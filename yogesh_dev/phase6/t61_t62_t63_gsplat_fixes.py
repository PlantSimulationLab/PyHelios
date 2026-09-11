"""
T6.1-T6.3 -- real, on-the-record demonstrations of three confirmed bugs in
the existing (non-yogesh_dev) gaussian-splatting pipeline at
`apple_tree_gaussian_splatting.py` (repo root), plus corrected, importable
implementations of the fixed logic.

HARD CONSTRAINT (see task brief / PHASE6_LOG.md): we are not allowed to
edit `apple_tree_gaussian_splatting.py` directly, and we can't even import
it as a whole module here because it unconditionally imports `torch` and
`gsplat` at module level and neither is installed in the `helios` conda
env used for this phase (confirmed: `ModuleNotFoundError: No module named
'torch'`). So the two small pieces of its logic relevant to T6.1
(`plane_camera_poses`, camera-pose grid geometry) are faithfully
reimplemented below, cited by exact line number, rather than imported.
Everything else (real tree, real renders, real label maps) uses the
genuine yogesh_dev/phase0-2 machinery and a live PyHelios scene.

See PHASE6_LOG.md for the exact before/after patch to apply to the real
file.
"""

import math
import os

import numpy as np
from PIL import Image

from pyhelios import Context, PlantArchitecture, Visualizer
from pyhelios.types import vec3, RGBcolor

from apple_tree import build_apple_tree

THIS_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(THIS_DIR, "output")

AGE_DAYS = 720.0  # same age the real pipeline uses (apple_tree_gaussian_splatting.py:581)

# Real constants copied from apple_tree_gaussian_splatting.py (module-level
# constants, not functions -- reading these is not "editing" the file).
BACKGROUND_RGB = (0.70, 0.85, 1.0)              # line 34
CAPTURE_CONFIGS = (                              # lines 71-73
    {"name": "sparse", "num_planes": 1, "num_cols": 4, "num_rows": 2},
    {"name": "default", "num_planes": 1, "num_cols": 8, "num_rows": 3},
    {"name": "multi_face", "num_planes": 4, "num_cols": 8, "num_rows": 3},
)
TEST_EVERY = 8                                   # line 53
GRID_SPAN_FRACTION = 0.6                         # line 66
DISTANCE_MARGIN = 1.05                           # line 57
SEED = 20260729  # PyHelios-wide convention this repo's phases use for reproducibility


# ---------------------------------------------------------------------------
# T6.1 -- seeded random permutation train/test split
# ---------------------------------------------------------------------------

def plane_camera_poses(center, tree_height, tree_x_extent, tree_y_extent, num_planes, num_cols, num_rows,
                        fov_deg, aspect_ratio, margin=DISTANCE_MARGIN, span_fraction=GRID_SPAN_FRACTION):
    """Faithful reimplementation of apple_tree_gaussian_splatting.py's
    `plane_camera_poses` (lines 246-293), reproduced here (not imported --
    see module docstring) so T6.1's demonstration runs against the REAL
    pose-grid geometry and ordering, not an abstract stand-in. Any person
    diffing this against the original will find it functionally identical."""
    half_fov_v = math.radians(fov_deg) / 2
    half_fov_h = math.atan(aspect_ratio * math.tan(half_fov_v))
    half_x, half_y = tree_x_extent / 2, tree_y_extent / 2
    distance_for_height = (tree_height / 2) / math.tan(half_fov_v) * margin

    half_span_z = (tree_height / 2) * span_fraction
    base_az = -math.pi / 2

    poses = []
    for p in range(num_planes):
        az = base_az + 2 * math.pi * p / num_planes
        forward = (math.cos(az), math.sin(az))
        tangent = (-math.sin(az), math.cos(az))

        half_width_at_az = abs(math.sin(az)) * half_x + abs(math.cos(az)) * half_y
        depth_at_az = abs(math.cos(az)) * half_x + abs(math.sin(az)) * half_y
        distance_for_width = half_width_at_az / math.tan(half_fov_h) * margin
        distance_for_clearance = depth_at_az * margin
        distance = max(distance_for_height, distance_for_width, distance_for_clearance)
        half_span_t = half_width_at_az * span_fraction

        for z_off in np.linspace(-half_span_z, half_span_z, num_rows):
            for t_off in np.linspace(-half_span_t, half_span_t, num_cols):
                eye = vec3(
                    center.x + distance * forward[0] + t_off * tangent[0],
                    center.y + distance * forward[1] + t_off * tangent[1],
                    center.z + z_off,
                )
                poses.append((eye, center, t_off, z_off))  # (eye, lookat, t_off, z_off) -- t_off/z_off kept for the demo below
    return poses


def old_split(n, test_every=TEST_EVERY):
    """The CURRENT (buggy) scheme: apple_tree_gaussian_splatting.py:348."""
    return ["test" if (i % test_every == 0) else "train" for i in range(n)]


def seeded_permutation_split(n, test_every=TEST_EVERY, seed=SEED):
    """T6.1 FIX: seeded random permutation, matching the OLD scheme's test
    set SIZE (round(n/test_every), so downstream train/test ratios and
    reported view counts don't shift) but not its column bias. This is the
    function to substitute for the `"split": ...` line in `render_dataset`.
    """
    n_test = max(1, round(n / test_every))
    rng = np.random.RandomState(seed)
    test_idx = set(rng.permutation(n)[:n_test].tolist())
    return ["test" if i in test_idx else "train" for i in range(n)]


def demo_t61(tree_center, tree_height, tree_x_extent, tree_y_extent, fov_deg=57.82, aspect_ratio=640 / 480):
    """Reproduce the T6.1 bug for real on the actual CAPTURE_CONFIGS grids,
    using a real tree's bounding geometry, and show the fix distributes
    across all columns instead of column 0 only."""
    report = {}
    for cfg in CAPTURE_CONFIGS:
        poses = plane_camera_poses(
            tree_center, tree_height, tree_x_extent, tree_y_extent,
            num_planes=cfg["num_planes"], num_cols=cfg["num_cols"], num_rows=cfg["num_rows"],
            fov_deg=fov_deg, aspect_ratio=aspect_ratio,
        )
        n = len(poses)
        cols = [i % cfg["num_cols"] for i in range(n)]  # loop order is row-major, cols innermost -> col = i % num_cols
        t_offs = [p[2] for p in poses]

        old = old_split(n)
        new = seeded_permutation_split(n)

        old_test_idx = [i for i, s in enumerate(old) if s == "test"]
        new_test_idx = [i for i, s in enumerate(new) if s == "test"]

        report[cfg["name"]] = {
            "num_planes": cfg["num_planes"], "num_cols": cfg["num_cols"], "num_rows": cfg["num_rows"],
            "n_views": n, "test_every": TEST_EVERY,
            "old_scheme": {
                "n_test": len(old_test_idx),
                "distinct_test_columns": sorted(set(cols[i] for i in old_test_idx)),
                "distinct_test_t_off_m": sorted(set(round(t_offs[i], 4) for i in old_test_idx)),
            },
            "new_scheme_seeded_permutation": {
                "n_test": len(new_test_idx),
                "distinct_test_columns": sorted(set(cols[i] for i in new_test_idx)),
                "n_distinct_test_t_off_m": len(set(round(t_offs[i], 4) for i in new_test_idx)),
            },
        }
    return report


# ---------------------------------------------------------------------------
# T6.2 -- masked PSNR restricted to GT-fruit UNION rendered-alpha
# ---------------------------------------------------------------------------

def psnr(a, b, eps=1e-10):
    """Same formula as apple_tree_gaussian_splatting.py's evaluate() (line 555):
    10*log10(1/mse), mse clamped away from 0."""
    mse = float(np.mean((a - b) ** 2))
    return 10 * math.log10(1.0 / max(mse, eps))


def naive_psnr_full_frame(target_rgb, rendered_rgb):
    """The CURRENT (buggy) metric: apple_tree_gaussian_splatting.py's evaluate(),
    lines 550-556 -- MSE over every pixel in the frame, no masking at all."""
    return psnr(target_rgb, rendered_rgb)


def masked_psnr(target_rgb, rendered_rgb, gt_fruit_mask, rendered_alpha, alpha_thresh=0.5):
    """T6.2 FIX: PSNR restricted to (GT-fruit mask) UNION (rendered-alpha >
    threshold) -- i.e. every pixel where either ground truth OR the model's
    own render THINKS there's fruit. Excludes true-negative background
    pixels (which is what makes a "render nothing" model score honestly
    badly), while still penalizing false positives the model hallucinates
    outside the GT fruit mask (that's what the rendered-alpha term adds)."""
    mask = gt_fruit_mask | (rendered_alpha > alpha_thresh)
    if not mask.any():
        return float("nan"), 0
    return psnr(target_rgb[mask], rendered_rgb[mask]), int(mask.sum())


def demo_t62(phase1_output_dir):
    """Real-data demonstration: use one of Phase 1's actual rendered RGB
    views + its real semantic label map (GT-fruit mask) as the "ground
    truth" the pipeline would train against, and a "dummy" render that
    reproduces the scene's own real background color everywhere and NEVER
    renders any fruit (the exact degenerate failure mode T6.2 describes --
    "a model rendering nothing scores well"). Compare naive full-frame PSNR
    against the corrected masked PSNR on this real image."""
    results = {}
    views = [
        ("above_tree0_above", "tree0_above"),
        ("level_tree1_level", "tree1_level"),
        ("below_tree2_below", "tree2_below"),
    ]
    for rgb_name, label_name in views:
        rgb_path = os.path.join(phase1_output_dir, "rgb", f"{rgb_name}.jpeg")
        sem_path = os.path.join(phase1_output_dir, "labels", f"{label_name}_semantic.npy")
        target = np.asarray(Image.open(rgb_path).convert("RGB"), dtype=np.float32) / 255.0
        semantic = np.load(sem_path)

        gt_fruit_mask = (semantic == 1)  # SEMANTIC_CLASSES: 1 == "fruit" (yogesh_dev/phase1/label_maps.py)
        background_mask = np.isnan(semantic)  # nearest-hit no-hit == background (phase1/label_maps.py)

        real_background_color = target[background_mask].mean(axis=0) if background_mask.any() \
            else np.array(BACKGROUND_RGB, dtype=np.float32)
        dummy_render = np.broadcast_to(real_background_color, target.shape).astype(np.float32)
        dummy_alpha = np.zeros(target.shape[:2], dtype=np.float32)  # "renders nothing" -> alpha 0 everywhere

        naive = naive_psnr_full_frame(target, dummy_render)
        masked, n_mask_px = masked_psnr(target, dummy_render, gt_fruit_mask, dummy_alpha)

        results[rgb_name] = {
            "resolution": list(target.shape[:2]),
            "n_fruit_pixels": int(gt_fruit_mask.sum()),
            "fruit_fraction": float(gt_fruit_mask.mean()),
            "background_fraction": float(background_mask.mean()),
            "naive_full_frame_psnr_db": naive,
            "masked_psnr_db": masked,
            "n_masked_pixels": n_mask_px,
            "psnr_inflation_db": naive - masked,
        }
    return results


# ---------------------------------------------------------------------------
# T6.3 -- occlusion-aware mask supervision
# ---------------------------------------------------------------------------

MASK_MATCH_COLOR = (255, 0, 0)
MASK_BG_COLOR = (0, 0, 0)
MASK_MATCH_THRESHOLD = 60


def _flat_color_render(context, uuids, fruit_uuids, eye, lookat, fov_deg, width, height):
    """Single flat-colored, unlit render (same technique as
    apple_tree_gaussian_splatting.py's render_semantic_masks, lines 186-237,
    reimplemented here for the same import-ability reason as above): fruit
    primitives -> red, everything else -> background. Building geometry
    from ONLY `uuids` means anything not in that set physically cannot
    occlude -- that's what makes the fruit-only pass an unoccluded
    silhouette."""
    context.setPrimitiveColor(fruit_uuids, RGBcolor(1.0, 0.0, 0.0))
    others = list(set(uuids) - set(fruit_uuids))
    if others:
        context.setPrimitiveColor(others, RGBcolor(0.0, 0.0, 1.0))
    context.overridePrimitiveTextureColor(uuids)

    tmp_path = os.path.join(OUTPUT_DIR, "_t63_tmp_render.png")
    with Visualizer(width=width, height=height, headless=True) as visualizer:
        visualizer.buildContextGeometry(context, uuids=uuids)
        visualizer.setBackgroundColor(RGBcolor(*(c / 255 for c in MASK_BG_COLOR)))
        visualizer.setLightingModel("none")
        visualizer.setCameraFieldOfView(fov_deg)
        visualizer.setCameraPosition(position=eye, lookAt=lookat)
        visualizer.plotUpdate()
        visualizer.printWindow(tmp_path)

    context.usePrimitiveTextureColor(uuids)
    raw = np.asarray(Image.open(tmp_path).convert("RGB"), dtype=np.float32)
    dist_to_fruit = np.linalg.norm(raw - np.array(MASK_MATCH_COLOR, dtype=np.float32), axis=-1)
    return dist_to_fruit < MASK_MATCH_THRESHOLD  # boolean fruit-pixel mask


def build_occlusion_aware_training_mask(fruit_visible_mask, fruit_alone_silhouette_mask):
    """T6.3 FIX. Inputs:
      fruit_visible_mask: pixels where the FULL scene's nearest-hit is fruit
        (what the current pipeline already computes and calls the "fruit
        mask" -- see load_dataset_tensors, apple_tree_gaussian_splatting.py:387-390).
      fruit_alone_silhouette_mask: pixels where fruit would be visible if it
        were the ONLY geometry in the scene (no occluders) -- the T6.3
        "render the fruit class alone" pass.

    Returns (color_target_is_fruit, occluded_fruit_mask, loss_mask):
      - color_target_is_fruit: same boolean as fruit_visible_mask (pixels
        supervised toward the real fruit-only render color).
      - occluded_fruit_mask: silhouette AND NOT visible -- fruit that exists
        here but is hidden behind something else.
      - loss_mask: True everywhere the loss should be computed. Occluded-
        fruit pixels are EXCLUDED (False) instead of being supervised as
        background, which is exactly what T6.3 asks for and what the
        current pipeline gets wrong (it silently teaches the splat that
        occluded apples are absent, since load_dataset_tensors replaces
        every non-fruit-visible pixel, occluded or not, with background_rgb
        and evaluate()/train_gaussians apply the photometric loss over the
        WHOLE frame with no per-pixel loss mask at all).
    """
    occluded_fruit_mask = fruit_alone_silhouette_mask & ~fruit_visible_mask
    loss_mask = ~occluded_fruit_mask
    return fruit_visible_mask, occluded_fruit_mask, loss_mask


def demo_t63(context, all_uuids, fruit_uuids, eye, lookat, fov_deg, width=480, height=360):
    full_scene_fruit_mask = _flat_color_render(context, all_uuids, fruit_uuids, eye, lookat, fov_deg, width, height)
    fruit_alone_mask = _flat_color_render(context, fruit_uuids, fruit_uuids, eye, lookat, fov_deg, width, height)

    color_target_is_fruit, occluded_fruit_mask, loss_mask = build_occlusion_aware_training_mask(
        full_scene_fruit_mask, fruit_alone_mask)

    # What the CURRENT pipeline does: every pixel outside full_scene_fruit_mask
    # (occluded or genuinely background) gets supervised AS background --
    # i.e. its implicit loss_mask is all-True, with occluded-fruit pixels
    # silently folded into the "background" target.
    old_effective_loss_mask_all_true = np.ones_like(full_scene_fruit_mask, dtype=bool)

    return {
        "resolution": [height, width],
        "n_fruit_visible_unoccluded_px": int(full_scene_fruit_mask.sum()),
        "n_fruit_alone_silhouette_px": int(fruit_alone_mask.sum()),
        "n_occluded_fruit_px": int(occluded_fruit_mask.sum()),
        "occluded_fraction_of_silhouette": (
            float(occluded_fruit_mask.sum() / fruit_alone_mask.sum()) if fruit_alone_mask.sum() else 0.0
        ),
        "old_scheme_n_pixels_wrongly_supervised_as_background": int(occluded_fruit_mask.sum()),
        "old_scheme_loss_mask_excludes_any_pixels": bool((~old_effective_loss_mask_all_true).any()),
        "new_scheme_n_pixels_excluded_from_loss": int((~loss_mask).sum()),
    }


# ---------------------------------------------------------------------------
# Orchestration: build ONE real tree, run all three demos against it.
# ---------------------------------------------------------------------------

def run_all():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with Context() as context:
        context.seedRandomGenerator(SEED)
        with PlantArchitecture(context) as plantarch:
            plantarch.loadPlantModelFromLibrary("apple")
            plant_id = build_apple_tree(plantarch, position=vec3(0, 0, 0), age_days=AGE_DAYS)
            all_uuids = plantarch.getAllPlantUUIDs(plant_id)
            fruit_uuids = context.filterPrimitivesByData(list(all_uuids), "object_label", "fruit")

            tree_center, _ = context.getDomainBoundingSphere(all_uuids)
            x_bounds, y_bounds, z_bounds = context.getDomainBoundingBox(all_uuids)
            tree_height = z_bounds.y - z_bounds.x
            tree_x_extent = x_bounds.y - x_bounds.x
            tree_y_extent = y_bounds.y - y_bounds.x

            t61_report = demo_t61(tree_center, tree_height, tree_x_extent, tree_y_extent)

            phase1_output_dir = os.path.join(THIS_DIR, "..", "phase1", "output")
            t62_report = demo_t62(phase1_output_dir)

            # A camera pose with real fruit-behind-leaf occlusion: front-ish,
            # mid-height, close enough that canopy self-occlusion is common.
            demo_eye = vec3(tree_center.x, tree_center.y - 1.6, tree_center.z + 0.2)
            demo_lookat = tree_center
            t63_report = demo_t63(context, list(all_uuids), list(fruit_uuids), demo_eye, demo_lookat, fov_deg=57.82)

    return {
        "tree_geometry": {
            "center": [tree_center.x, tree_center.y, tree_center.z],
            "height_m": tree_height, "x_extent_m": tree_x_extent, "y_extent_m": tree_y_extent,
            "n_primitives": len(all_uuids), "n_fruit_primitives": len(fruit_uuids),
        },
        "T6.1_split_fix": t61_report,
        "T6.2_masked_psnr": t62_report,
        "T6.3_occlusion_aware_mask": t63_report,
    }


if __name__ == "__main__":
    import json
    report = run_all()
    out_path = os.path.join(OUTPUT_DIR, "t61_t62_t63_report.json")
    with open(out_path, "w") as fh:
        json.dump(report, fh, indent=2)
    print(json.dumps(report, indent=2))
