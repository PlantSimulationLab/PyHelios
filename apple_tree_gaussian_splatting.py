import functools
import json
import math
import os

import numpy as np
import torch
import torch.nn.functional as F
from gsplat import DefaultStrategy, MCMCStrategy, export_splats, rasterization
from PIL import Image
from scipy.spatial import cKDTree
from torch import nn

from apple_tree import build_apple_tree
from notify_slack import notify_slack
from pyhelios import Context, PlantArchitecture, Visualizer
from pyhelios.types import RGBcolor, vec3

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
SH0_C0 = 0.28209479177387814  # degree-0 spherical harmonic basis constant

# Reference calibration from a real camera. PyHelios's Visualizer only exposes a
# symmetric pinhole camera (single vertical FOV, centered principal point, no
# fx != fy, no distortion), so this can't be reproduced exactly. We instead
# derive the render resolution from (cx, cy) and the vertical FOV from fy, and
# drop distortion + off-center principal point -- the gsplat training K matrix
# below is a centered pinhole matching what PyHelios actually rendered, not
# these raw values.
CAMERA_FX = 737.052978515625
CAMERA_FY = 736.5230102539062
CAMERA_CX = 978.52197265625
CAMERA_CY = 643.114013671875
CAMERA_DISTORTION = (1.1389000415802002, 1.6283799409866333,
                      0.0002682750055100769, 2.426269929856062e-05, 0.17436400055885315)  # k1,k2,p1,p2,k3 (unused, see note above)

BACKGROUND_RGB = (0.70, 0.85, 1.0)
FOV_DEG = math.degrees(2 * math.atan(round(2 * CAMERA_CY) / (2 * CAMERA_FY)))

# PyHelios's headless Visualizer has a native heap-corruption bug (crashes with
# "malloc(): corrupted top size") triggered by repeated renders once a dimension
# gets much above ~1800px -- confirmed independent of primitive count, of reusing
# vs. recreating the Visualizer, and of whether torch/gsplat are even imported.
# The full resolution implied by the camera calibration (1957x1286) crashes
# reliably within the first few views, so we render at the same aspect ratio
# scaled down to a size that's been validated stable across dozens of sequential
# renders. FOV_DEG above is an angle derived from fy/cy and stays correct
# regardless of this scaling.
MAX_RENDER_DIMENSION = 1000
_render_scale = min(1.0, MAX_RENDER_DIMENSION / max(round(2 * CAMERA_CX), round(2 * CAMERA_CY)))
IMAGE_WIDTH = round(2 * CAMERA_CX * _render_scale)
IMAGE_HEIGHT = round(2 * CAMERA_CY * _render_scale)
NUM_GRID_COLS = 8  # horizontal camera positions within the frontal plane
NUM_GRID_ROWS = 3  # vertical camera positions within the frontal plane
GRID_SPAN_FRACTION = 0.6  # how far the grid spans across the tree's own extent/height
TEST_EVERY = 8
DISTANCE_MARGIN = 1.05  # tight headroom so each tree nearly fills the frame

OUTPUT_DIR = "renders/gaussian_splatting"
DATASET_DIR = os.path.join(OUTPUT_DIR, "dataset")
EVAL_DIR = os.path.join(OUTPUT_DIR, "eval")

TRAIN_ITERS = 5000
INIT_POINT_BUDGET = 60000

CLASS_NAMES = ("fruit", "leaf", "tree")  # "tree" = everything else: branches, trunk, petioles, flower parts
CLASS_MASK_COLORS = {"fruit": (255, 0, 0), "leaf": (0, 255, 0), "tree": (0, 0, 255)}
MASK_BACKGROUND_RGB = (0, 0, 0)
MASK_COLOR_MATCH_THRESHOLD = 60  # pixels farther than this from every class color fall back to background

TARGET_CLASS = "fruit"  # apples only, using the semantic mask as a prior

# Design decision: rather than committing to one gsplat densification scheme,
# train once per strategy the library ships and export a separate .ply for
# each, so the two can be compared on the same seed points/dataset:
#   - "default": DefaultStrategy -- clone/split/prune (original 3DGS paper).
#   - "mcmc":    MCMCStrategy -- relocation + noise injection (3DGS-MCMC paper).
SPLAT_STRATEGIES = ("default", "mcmc")
MCMC_CAP_MAX = 200_000  # relocation target cap, sized for a fruit-only point budget
MCMC_OPACITY_REG = 0.01  # L1 opacity regularization weight, per the 3DGS-MCMC paper
MCMC_SCALE_REG = 0.01  # L1 scale regularization weight, per the 3DGS-MCMC paper


# ---------------------------------------------------------------------------
# Tree construction (reuses apple_tree.py) + point-cloud seeding
# ---------------------------------------------------------------------------

def build_orchard(plantarch, positions, age_days):
    """Build one apple tree per position, with fruit-aware collision avoidance."""
    plantarch.loadPlantModelFromLibrary("apple")
    plantarch.setCollisionRelevantOrgans(
        include_internodes=True, include_leaves=True, include_fruit=True
    )
    plantarch.enableSoftCollisionAvoidance(enable_fruit_collision=True)
    return [
        build_apple_tree(plantarch, position=position, age_days=age_days)
        for position in positions
    ]


@functools.lru_cache(maxsize=None)
def _texture_average_color(path):
    """Mean RGB of a texture's opaque pixels, used when a primitive has no flat color."""
    img = Image.open(path).convert("RGBA")
    arr = np.asarray(img, dtype=np.float32) / 255.0
    rgb = arr[..., :3]
    mask = arr[..., 3] > 0.5
    if not mask.any():
        mask = np.ones(arr.shape[:2], dtype=bool)
    return tuple(rgb[mask].mean(axis=0))


def sample_point_cloud(context, uuids, target_points=INIT_POINT_BUDGET,
                        samples_per_unit_area=500.0, max_samples=6):
    """Seed Gaussian positions/colors directly from tree surface geometry."""
    flat_verts, offsets = context.getPrimitiveVertices(uuids)
    colors = context.getPrimitiveColor(uuids)
    areas = context.getPrimitiveArea(uuids)

    positions, point_colors = [], []
    for i, uuid in enumerate(uuids):
        verts = flat_verts[offsets[i]:offsets[i + 1]].reshape(-1, 3)
        if verts.shape[0] < 3:
            continue

        color = colors[i]
        if color.max() < 0.03:
            texture_file = context.getPrimitiveTextureFile(uuid)
            if texture_file:
                color = np.array(_texture_average_color(texture_file), dtype=np.float32)

        n_samples = int(np.clip(round(areas[i] * samples_per_unit_area), 1, max_samples))
        for _ in range(n_samples):
            if verts.shape[0] >= 4:
                u, w = np.random.rand(2)
                p = ((1 - u) * (1 - w) * verts[0] + u * (1 - w) * verts[1]
                     + u * w * verts[2] + (1 - u) * w * verts[3])
            else:
                r1, r2 = np.random.rand(2)
                if r1 + r2 > 1:
                    r1, r2 = 1 - r1, 1 - r2
                p = verts[0] + r1 * (verts[1] - verts[0]) + r2 * (verts[2] - verts[0])
            positions.append(p)
            point_colors.append(color)

    positions = np.asarray(positions, dtype=np.float32)
    point_colors = np.clip(np.asarray(point_colors, dtype=np.float32), 0.02, 0.98)
    if len(positions) > target_points:
        idx = np.random.choice(len(positions), target_points, replace=False)
        positions, point_colors = positions[idx], point_colors[idx]
    return positions, point_colors


def classify_primitives(context, uuids):
    """Split primitive UUIDs into fruit/leaf/tree using Helios's per-primitive
    "object_label" data (set internally by PlantArchitecture when it builds
    each organ). "tree" is everything left over: branches, trunk, petioles,
    peduncles, flower parts -- there's no single "tree" label in Helios, so
    it's the complement of fruit and leaf. This is a pure read (filter), so
    it's safe to call at any point -- unlike render_semantic_masks below,
    which mutates primitive colors."""
    uuids = list(uuids)
    fruit = context.filterPrimitivesByData(uuids, "object_label", "fruit")
    leaf = context.filterPrimitivesByData(uuids, "object_label", "leaf")
    tree = list(set(uuids) - set(fruit) - set(leaf))
    return {"fruit": fruit, "leaf": leaf, "tree": tree}


def render_semantic_masks(context, class_uuids, camera_poses, out_dir, width=IMAGE_WIDTH, height=IMAGE_HEIGHT,
                           fov_deg=FOV_DEG):
    """Render one flat-colored, unlit pass per camera pose (the same poses as
    the RGB dataset, for pixel-perfect alignment) and decode it into a
    single-channel class-index PNG: 0=background, 1=fruit, 2=leaf, 3=tree.

    Uses overridePrimitiveTextureColor + lighting_model="none" so every
    primitive renders as its exact flat class color with no texture/shading,
    then nearest-color matching recovers the class per pixel. This mutates
    each primitive's stored flat color for the rest of the Context's
    lifetime (only the texture-color override is restored afterward) -- call
    this AFTER sample_point_cloud(), which reads primitive colors and would
    otherwise pick up these synthetic mask colors instead of the tree's
    actual colors.
    """
    os.makedirs(out_dir, exist_ok=True)
    all_uuids = [u for uuids in class_uuids.values() for u in uuids]

    for class_name in CLASS_NAMES:
        color = tuple(c / 255 for c in CLASS_MASK_COLORS[class_name])
        context.setPrimitiveColor(class_uuids[class_name], RGBcolor(*color))
    context.overridePrimitiveTextureColor(all_uuids)

    reference_colors = np.array(
        [MASK_BACKGROUND_RGB] + [CLASS_MASK_COLORS[c] for c in CLASS_NAMES], dtype=np.float32
    )

    mask_paths = []
    with Visualizer(width=width, height=height, headless=True) as visualizer:
        visualizer.buildContextGeometry(context, uuids=all_uuids)
        visualizer.setBackgroundColor(RGBcolor(*(c / 255 for c in MASK_BACKGROUND_RGB)))
        visualizer.setLightingModel("none")
        visualizer.setCameraFieldOfView(fov_deg)

        for i, (eye, lookAt) in enumerate(camera_poses):
            visualizer.setCameraPosition(position=eye, lookAt=lookAt)
            visualizer.plotUpdate()
            viz_path = os.path.join(out_dir, f"maskviz_{i:04d}.png")
            visualizer.printWindow(viz_path)

            raw = np.asarray(Image.open(viz_path).convert("RGB"), dtype=np.float32)
            dists = np.linalg.norm(raw[:, :, None, :] - reference_colors[None, None, :, :], axis=-1)
            class_idx = np.argmin(dists, axis=-1)
            class_idx[np.min(dists, axis=-1) > MASK_COLOR_MATCH_THRESHOLD] = 0

            mask_path = os.path.join(out_dir, f"mask_{i:04d}.png")
            Image.fromarray(class_idx.astype(np.uint8), mode="L").save(mask_path)
            mask_paths.append(mask_path)
            print(f"  mask {i + 1}/{len(camera_poses)}: {mask_path}")

    context.usePrimitiveTextureColor(all_uuids)
    return mask_paths


# ---------------------------------------------------------------------------
# Camera plane rig (extends the fixed 3-shot rig in apple_tree_cameras.py into
# dozens of views with known poses, one grid per tree, since Gaussian
# Splatting needs many views rather than a few fixed angles)
# ---------------------------------------------------------------------------

def plane_camera_poses(center, tree_height, tree_x_extent, tree_y_extent, num_cols=NUM_GRID_COLS,
                        num_rows=NUM_GRID_ROWS, fov_deg=FOV_DEG, aspect_ratio=IMAGE_WIDTH / IMAGE_HEIGHT,
                        margin=DISTANCE_MARGIN, span_fraction=GRID_SPAN_FRACTION):
    """Camera poses for ONE tree: rather than orbiting around it, the camera
    stays on a single frontal plane at a fixed distance from that tree's own
    center (facing along -Y) and translates across a grid of horizontal/
    vertical offsets within that plane. lookAt is pinned to the tree center
    throughout, so each shot is a slightly different parallax view of the
    same face rather than a new angle around the tree.

    Distance is sized off THIS tree's own height/extent (not the whole
    orchard), so each tree fills its frame the same way regardless of where
    it sits in the row. It must also clear the tree's extent along the
    approach direction (tree_y_extent), or a wide canopy would poke through
    the near clipping plane."""
    half_fov_v = math.radians(fov_deg) / 2
    half_fov_h = math.atan(aspect_ratio * math.tan(half_fov_v))
    distance_for_height = (tree_height / 2) / math.tan(half_fov_v) * margin
    distance_for_width = (tree_x_extent / 2) / math.tan(half_fov_h) * margin
    distance_for_clearance = (tree_y_extent / 2) * margin
    distance = max(distance_for_height, distance_for_width, distance_for_clearance)

    half_span_x = (tree_x_extent / 2) * span_fraction
    half_span_z = (tree_height / 2) * span_fraction

    poses = []
    for z_off in np.linspace(-half_span_z, half_span_z, num_rows):
        for x_off in np.linspace(-half_span_x, half_span_x, num_cols):
            eye = vec3(center.x + x_off, center.y - distance, center.z + z_off)
            poses.append((eye, center))
    return poses


def look_at_view_matrix(eye, lookAt, world_up=(0.0, 0.0, 1.0)):
    """World-to-camera matrix in OpenCV convention (X-right, Y-down, Z-forward),
    matching the eye/lookAt/world-up=+Z convention the Visualizer renders with."""
    eye_np = np.array([eye.x, eye.y, eye.z], dtype=np.float32)
    center_np = np.array([lookAt.x, lookAt.y, lookAt.z], dtype=np.float32)
    up_np = np.array(world_up, dtype=np.float32)

    forward = center_np - eye_np
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, up_np)
    if np.linalg.norm(right) < 1e-6:
        up_np = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        right = np.cross(forward, up_np)
    right /= np.linalg.norm(right)
    down = np.cross(forward, right)

    rotation_c2w = np.stack([right, down, forward], axis=1)
    viewmat = np.eye(4, dtype=np.float32)
    viewmat[:3, :3] = rotation_c2w.T
    viewmat[:3, 3] = -rotation_c2w.T @ eye_np
    return viewmat


def intrinsics_matrix(width, height, fov_deg):
    focal = height / (2.0 * math.tan(math.radians(fov_deg) / 2.0))
    return np.array([[focal, 0, width / 2.0], [0, focal, height / 2.0], [0, 0, 1]], dtype=np.float32)


# ---------------------------------------------------------------------------
# Multi-view dataset rendering + export
# ---------------------------------------------------------------------------

def render_dataset(context, all_uuids, camera_poses, out_dir, width=IMAGE_WIDTH, height=IMAGE_HEIGHT,
                    fov_deg=FOV_DEG, background_rgb=BACKGROUND_RGB, test_every=TEST_EVERY):
    os.makedirs(out_dir, exist_ok=True)
    K = intrinsics_matrix(width, height, fov_deg)

    frames = []
    with Visualizer(width=width, height=height, headless=True) as visualizer:
        visualizer.buildContextGeometry(context, uuids=all_uuids)
        visualizer.setBackgroundColor(RGBcolor(*background_rgb))
        visualizer.setLightingModel("phong_shadowed")
        visualizer.setCameraFieldOfView(fov_deg)

        for i, (eye, lookAt) in enumerate(camera_poses):
            visualizer.setCameraPosition(position=eye, lookAt=lookAt)
            visualizer.plotUpdate()
            filename = os.path.join(out_dir, f"view_{i:04d}.png")
            visualizer.printWindow(filename)
            frames.append({
                "file_path": filename,
                "viewmat": look_at_view_matrix(eye, lookAt),
                "split": "test" if (i % test_every == 0) else "train",
            })
            print(f"  rendered {i + 1}/{len(camera_poses)}: {filename}")

    transforms = {
        "camera_model": "PINHOLE",
        "width": width,
        "height": height,
        "fl_x": float(K[0, 0]),
        "fl_y": float(K[1, 1]),
        "cx": float(K[0, 2]),
        "cy": float(K[1, 2]),
        "frames": [
            {
                "file_path": os.path.relpath(f["file_path"], out_dir),
                "transform_matrix": np.linalg.inv(f["viewmat"]).tolist(),
                "split": f["split"],
            }
            for f in frames
        ],
    }
    with open(os.path.join(out_dir, "transforms.json"), "w") as fh:
        json.dump(transforms, fh, indent=2)

    return frames, K


def load_dataset_tensors(frames, K, device=DEVICE, mask_paths=None, target_class_index=None,
                          background_rgb=BACKGROUND_RGB):
    """Load rendered frames as training tensors. If mask_paths and
    target_class_index are given (see CLASS_NAMES / TARGET_CLASS), pixels
    outside that class are replaced with the background color before
    training -- the semantic mask acts as a prior so the model only ever
    gets photometric supervision for the target class (e.g. "fruit"), and
    everywhere else is treated as empty background."""
    K_t = torch.from_numpy(K).to(device)
    dataset = {"train": [], "test": []}
    for i, frame in enumerate(frames):
        image = np.asarray(Image.open(frame["file_path"]).convert("RGB"), dtype=np.float32) / 255.0
        if mask_paths is not None and target_class_index is not None:
            class_mask = np.asarray(Image.open(mask_paths[i]).convert("L"))
            keep = class_mask == target_class_index
            image = np.where(keep[..., None], image, np.array(background_rgb, dtype=np.float32))
        dataset[frame["split"]].append({
            "image": torch.from_numpy(image).to(device),
            "viewmat": torch.from_numpy(frame["viewmat"]).to(device),
        })
    return dataset, K_t


# ---------------------------------------------------------------------------
# Gaussian Splatting: init, training, eval, export
# ---------------------------------------------------------------------------

def inverse_sigmoid(x):
    return math.log(x / (1 - x))


def init_gaussians(positions, colors, scene_radius, device=DEVICE):
    tree = cKDTree(positions)
    dists, _ = tree.query(positions, k=4)
    nn_dist = np.clip(dists[:, 1:].mean(axis=1), scene_radius * 1e-4, scene_radius * 0.1)

    n = positions.shape[0]
    scales_init = np.repeat(nn_dist[:, None], 3, axis=1)
    quats_init = np.zeros((n, 4), dtype=np.float32)
    quats_init[:, 0] = 1.0
    sh0_init = (colors - 0.5) / SH0_C0

    return {
        "means": nn.Parameter(torch.tensor(positions, dtype=torch.float32, device=device)),
        "scales": nn.Parameter(torch.log(torch.tensor(scales_init, dtype=torch.float32, device=device))),
        "quats": nn.Parameter(torch.tensor(quats_init, dtype=torch.float32, device=device)),
        "opacities": nn.Parameter(torch.full((n,), inverse_sigmoid(0.1), dtype=torch.float32, device=device)),
        "sh0": nn.Parameter(torch.tensor(sh0_init, dtype=torch.float32, device=device).unsqueeze(1)),
        "shN": nn.Parameter(torch.zeros((n, 0, 3), dtype=torch.float32, device=device)),
    }


def _gaussian_window(window_size, sigma, device):
    coords = torch.arange(window_size, dtype=torch.float32, device=device) - window_size // 2
    g = torch.exp(-(coords ** 2) / (2 * sigma ** 2))
    g /= g.sum()
    return g.outer(g)


def ssim(img1, img2, window_size=11):
    """Single-scale SSIM between two (H,W,3) images in [0,1]."""
    channels = img1.shape[-1]
    window = _gaussian_window(window_size, 1.5, img1.device).expand(channels, 1, window_size, window_size)
    x = img1.permute(2, 0, 1).unsqueeze(0)
    y = img2.permute(2, 0, 1).unsqueeze(0)
    pad = window_size // 2

    mu_x = F.conv2d(x, window, padding=pad, groups=channels)
    mu_y = F.conv2d(y, window, padding=pad, groups=channels)
    mu_x2, mu_y2, mu_xy = mu_x * mu_x, mu_y * mu_y, mu_x * mu_y

    sigma_x2 = F.conv2d(x * x, window, padding=pad, groups=channels) - mu_x2
    sigma_y2 = F.conv2d(y * y, window, padding=pad, groups=channels) - mu_y2
    sigma_xy = F.conv2d(x * y, window, padding=pad, groups=channels) - mu_xy

    c1, c2 = 0.01 ** 2, 0.03 ** 2
    ssim_map = ((2 * mu_xy + c1) * (2 * sigma_xy + c2)) / ((mu_x2 + mu_y2 + c1) * (sigma_x2 + sigma_y2 + c2))
    return ssim_map.mean()


def render_view(params, viewmat, K, width, height, background):
    colors = torch.cat([params["sh0"], params["shN"]], dim=1)
    render, alpha, info = rasterization(
        means=params["means"],
        quats=params["quats"],
        scales=torch.exp(params["scales"]),
        opacities=torch.sigmoid(params["opacities"]),
        colors=colors,
        viewmats=viewmat.unsqueeze(0),
        Ks=K.unsqueeze(0),
        width=width,
        height=height,
        sh_degree=0,
        backgrounds=background,
        packed=False,
    )
    return render[0], alpha[0], info


def _build_strategy(strategy_name, iters):
    """The two densification schemes gsplat ships take different constructor
    args and different initialize_state()/step_*_backward() signatures (see
    module docstring on SPLAT_STRATEGIES), so construction is centralized here
    rather than branching inline in the training loop."""
    if strategy_name == "default":
        return DefaultStrategy(refine_stop_iter=int(iters * 0.75), refine_every=100)
    if strategy_name == "mcmc":
        return MCMCStrategy(cap_max=MCMC_CAP_MAX, refine_stop_iter=int(iters * 0.75), refine_every=100)
    raise ValueError(f"Unknown strategy_name: {strategy_name!r} (expected one of {SPLAT_STRATEGIES})")


def train_gaussians(params, dataset, K, width, height, background_rgb, strategy_name="default",
                     iters=TRAIN_ITERS, scene_radius=1.0, device=DEVICE):
    lrs = {
        "means": 1.6e-4 * scene_radius,
        "scales": 5e-3,
        "quats": 1e-3,
        "opacities": 5e-2,
        "sh0": 2.5e-3,
        "shN": 2.5e-3 / 20,
    }
    optimizers = {name: torch.optim.Adam([params[name]], lr=lrs[name], eps=1e-15) for name in params}
    means_scheduler = torch.optim.lr_scheduler.ExponentialLR(
        optimizers["means"], gamma=(1.6e-6 / 1.6e-4) ** (1.0 / iters)
    )

    strategy = _build_strategy(strategy_name, iters)
    strategy.check_sanity(params, optimizers)
    # DefaultStrategy scales its split heuristics off scene_radius; MCMCStrategy
    # has no such notion (relocation is opacity-driven, not scale-driven).
    state = strategy.initialize_state(scene_scale=scene_radius) if strategy_name == "default" \
        else strategy.initialize_state()

    background = torch.tensor(background_rgb, dtype=torch.float32, device=device).unsqueeze(0)
    train_views = dataset["train"]

    for step in range(1, iters + 1):
        view = train_views[np.random.randint(len(train_views))]
        rendered, _, info = render_view(params, view["viewmat"], K, width, height, background)
        target = view["image"]

        l1 = (rendered - target).abs().mean()
        loss = 0.8 * l1 + 0.2 * (1.0 - ssim(rendered, target))
        if strategy_name == "mcmc":
            # 3DGS-MCMC paper regularizes opacity/scale directly since there's
            # no explicit split/prune step to keep them in check otherwise.
            loss = (loss + MCMC_OPACITY_REG * torch.sigmoid(params["opacities"]).abs().mean()
                     + MCMC_SCALE_REG * torch.exp(params["scales"]).abs().mean())

        if strategy_name == "default":
            strategy.step_pre_backward(params, optimizers, state, step, info)
        loss.backward()
        if strategy_name == "mcmc":
            strategy.step_post_backward(params, optimizers, state, step, info, lr=means_scheduler.get_last_lr()[0])
        else:
            strategy.step_post_backward(params, optimizers, state, step, info)

        for opt in optimizers.values():
            opt.step()
            opt.zero_grad(set_to_none=True)
        means_scheduler.step()

        if step % 200 == 0 or step == 1:
            print(f"  [{strategy_name}] iter {step}/{iters}  loss={loss.item():.4f}  l1={l1.item():.4f}  "
                  f"gaussians={params['means'].shape[0]}")

    return params


def evaluate(params, dataset, K, width, height, background_rgb, out_dir, device=DEVICE):
    os.makedirs(out_dir, exist_ok=True)
    background = torch.tensor(background_rgb, dtype=torch.float32, device=device).unsqueeze(0)
    psnrs = []
    with torch.no_grad():
        for i, view in enumerate(dataset["test"]):
            rendered, _, _ = render_view(params, view["viewmat"], K, width, height, background)
            rendered = rendered.clamp(0, 1)
            target = view["image"]

            mse = ((rendered - target) ** 2).mean().item()
            psnr = 10 * math.log10(1.0 / max(mse, 1e-10))
            psnrs.append(psnr)

            comparison = (torch.cat([target, rendered], dim=1).clamp(0, 1).cpu().numpy() * 255).astype(np.uint8)
            Image.fromarray(comparison).save(os.path.join(out_dir, f"eval_{i:03d}_psnr{psnr:.1f}.png"))

    mean_psnr = float(np.mean(psnrs)) if psnrs else float("nan")
    print(f"Held-out PSNR: mean={mean_psnr:.2f} dB over {len(psnrs)} views")
    return mean_psnr


def export_ply(params, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    export_splats(
        means=params["means"].detach(),
        scales=params["scales"].detach(),
        quats=F.normalize(params["quats"], dim=-1).detach(),
        opacities=params["opacities"].detach(),
        sh0=params["sh0"].detach(),
        shN=params["shN"].detach(),
        format="ply",
        save_to=out_path,
    )


def main():
    AGE_DAYS = 720.0
    POSITIONS = [vec3(0, 0, 0), vec3(1.5, 0, 0), vec3(3, 0, 0)]

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            plant_ids = build_orchard(plantarch, POSITIONS, AGE_DAYS)
            tree_uuids_list = [plantarch.getAllPlantUUIDs(plant_id) for plant_id in plant_ids]
            all_uuids = [u for uuids in tree_uuids_list for u in uuids]
            print(f"Built {len(plant_ids)} apple trees, {len(all_uuids)} primitives total")

            camera_poses = []
            for tree_uuids in tree_uuids_list:
                tree_center, _ = context.getDomainBoundingSphere(tree_uuids)
                x_bounds, y_bounds, z_bounds = context.getDomainBoundingBox(tree_uuids)
                tree_height = z_bounds.y - z_bounds.x
                tree_x_extent = x_bounds.y - x_bounds.x
                tree_y_extent = y_bounds.y - y_bounds.x
                print(f"  tree center=({tree_center.x:.2f}, {tree_center.y:.2f}, {tree_center.z:.2f}) "
                      f"height={tree_height:.2f}m x_extent={tree_x_extent:.2f}m y_extent={tree_y_extent:.2f}m")
                camera_poses.extend(plane_camera_poses(tree_center, tree_height, tree_x_extent, tree_y_extent))

            print(f"Rendering {len(camera_poses)} multi-view images...")
            frames, K = render_dataset(context, all_uuids, camera_poses, DATASET_DIR)

            print("Classifying primitives by organ type...")
            class_uuids = classify_primitives(context, all_uuids)
            for name in CLASS_NAMES:
                print(f"  {name}: {len(class_uuids[name])} primitives")

            print(f"Sampling seed point cloud from tree geometry (class={TARGET_CLASS})...")
            positions, colors = sample_point_cloud(context, class_uuids[TARGET_CLASS])
            print(f"  {len(positions)} seed points")
            # scale-init radius from the actual points being fit, not the whole
            # scene -- a class filter (e.g. fruit only) covers a much smaller
            # volume than the full tree, so the full bounding sphere would be
            # a poor scale for the Gaussian init/LR heuristics below.
            point_cloud_radius = float(np.linalg.norm(positions - positions.mean(axis=0), axis=1).max())

            # Mutates primitive colors, so it must run after sample_point_cloud
            # (see render_semantic_masks docstring) -- reuses the same camera
            # poses as the RGB dataset for pixel-perfect alignment.
            print(f"Rendering {len(camera_poses)} semantic mask images...")
            mask_paths = render_semantic_masks(context, class_uuids, camera_poses, DATASET_DIR)

    target_class_index = CLASS_NAMES.index(TARGET_CLASS) + 1
    dataset, K_t = load_dataset_tensors(frames, K, mask_paths=mask_paths, target_class_index=target_class_index)
    print(f"Train views: {len(dataset['train'])}  Test views: {len(dataset['test'])}")

    # Same seed points/dataset, trained once per strategy the library ships
    # (see SPLAT_STRATEGIES) so the two can be compared side by side.
    results = []
    for strategy_name in SPLAT_STRATEGIES:
        print(f"--- Strategy: {strategy_name} ---")
        params = init_gaussians(positions, colors, point_cloud_radius)
        print(f"Training {params['means'].shape[0]} Gaussians for {TRAIN_ITERS} iterations on {DEVICE}...")
        params = train_gaussians(params, dataset, K_t, IMAGE_WIDTH, IMAGE_HEIGHT, BACKGROUND_RGB,
                                  strategy_name=strategy_name, iters=TRAIN_ITERS, scene_radius=point_cloud_radius)

        mean_psnr = evaluate(params, dataset, K_t, IMAGE_WIDTH, IMAGE_HEIGHT, BACKGROUND_RGB,
                              os.path.join(EVAL_DIR, strategy_name))

        output_ply_path = os.path.join(OUTPUT_DIR, f"apple_splats_{TARGET_CLASS}_{strategy_name}.ply")
        export_ply(params, output_ply_path)
        print(f"Saved trained splats to {output_ply_path}")

        results.append({
            "strategy": strategy_name,
            "num_gaussians": params["means"].shape[0],
            "mean_psnr": mean_psnr,
            "output_ply_path": output_ply_path,
        })

    return results


if __name__ == "__main__":
    try:
        results = main()
        summary = "; ".join(
            f"{r['strategy']}: {r['num_gaussians']} Gaussians, PSNR={r['mean_psnr']:.2f}dB -> {r['output_ply_path']}"
            for r in results
        )
        notify_slack(f":white_check_mark: apple_tree_gaussian_splatting.py finished (class=fruit) — {summary}")
    except Exception as e:
        notify_slack(f":x: apple_tree_gaussian_splatting.py failed: {type(e).__name__}: {e}")
        raise
