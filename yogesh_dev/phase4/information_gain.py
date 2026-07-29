"""
T4.5 -- GPU-batched information gain.

Task doc: "**[C++/CUDA, needs T0.6]** The single highest-leverage
engineering decision. Comparable systems spend 93% of the planning cycle
here, it is embarrassingly parallel, and no agricultural NBV paper has done
it because they are all on CPU OctoMap."

## Scope of THIS file, stated up front

This is explicitly OUT OF SCOPE to build for real: it needs a CUDA kernel
and T0.6 (`CollisionDetection`/GPU ray infra), neither of which exist in
this Python-only, `yogesh_dev`-confined phase. What IS in scope and
implemented for real below: a CORRECT, fully VECTORIZED (numpy, CPU)
REFERENCE implementation of the actual information-gain algorithm --
volumetric ray-based expected information gain over T4.1's real occupancy
map, batched across every candidate pose and every ray simultaneously (no
Python-level loop over poses or rays; only a `max_steps`-length loop over
march distance, which itself is vectorized across the (pose x ray) batch
dimension). This is real, testable, numerically checkable math -- just not
GPU-resident. See the design note at the bottom of this docstring (and
mirrored into PHASE4_LOG.md) for what would actually have to change to make
it GPU-batched.

## Algorithm: volumetric visibility-weighted entropy (Isler et al.-style)

For a candidate pose (eye, forward), sample R ray directions spanning the
camera's real FOV (from `sensor_model.intrinsics`). March each ray S fixed
steps up to a max range. At each (pose, ray, step) point, look up the real
T4.1 occupancy log-odds -> `p_occ = sigmoid(L)`. Per-voxel information is
the binary entropy `H(p_occ) = -p*log(p) - (1-p)*log(1-p)` (maximal exactly
at p=0.5, i.e. truly UNKNOWN voxels -- this is what makes "unknown" show up
without a hard threshold). Each step's contribution is discounted by the
transmittance `T(s) = prod_{s'<s} (1 - p_occ(s'))`, i.e. the probability the
ray was not already stopped by an occupied voxel before reaching step s
(standard volumetric-rendering-style visibility term). Total per-ray gain
= `sum_s T(s) * H(p_occ(s))`; per-pose gain = `sum` (or mean) over its rays.

An optional semantic prior term (real tie-in to T4.3): if a semantic
posterior map is supplied, each voxel's entropy is up-weighted by
`(1 + FRUIT_BOOST * P(fruit | voxel))`, biasing information gain toward
plausible fruit locations without zeroing out general exploration value
elsewhere. This is a real, if simple, semantically-informed NBV term, not
a placeholder.

## Vectorization (the part that stands in for "batched")

All of (pose, ray, step) is materialized as flat (N,3) point arrays for a
single grid-index + gather pass per march step (`S` numpy calls total, each
operating on the full `P*R`-sized batch at once) -- there is no Python loop
over individual poses or rays anywhere in the hot path. This is precisely
the structure a GPU-batched version would parallelize (see design note).

## Design note: what changes for a REAL GPU-batched version

(a) Batch dimension: candidate poses P (e.g. every reachable roadmap node,
    potentially thousands, evaluated per planning cycle) is the natural
    outer batch/grid dimension for a CUDA kernel -- one thread BLOCK per
    candidate pose (or per (pose, ray-tile) pair for very high ray counts),
    with individual threads over rays within a pose, is the natural
    mapping; this mirrors exactly this file's (P,R) leading array
    dimensions.
(b) Memory layout: Structure-of-Arrays, not Array-of-Structures -- pose
    eye/forward/right/up as flat float32 (P,3) arrays (as already done
    here), and critically the occupancy grid itself should live as a CUDA
    3D texture (or a dense pitched array bound as a texture), so per-step
    trilinear-interpolated log-odds lookups become a single hardware
    texture-fetch instruction per thread per step instead of this file's
    nearest-voxel `np.ravel_multi_index` + gather -- free interpolation AND
    free bounds handling (clamp-to-border) that this CPU version currently
    does by hand (`in_bounds` masking).
(c) Kernel structure: one thread per (pose, ray); a step loop INSIDE the
    kernel (not a separate global launch per step) accumulating running
    transmittance and gain in registers, writing one scalar (gain) out per
    thread at the end; a block-level or warp-level tree reduction sums
    per-ray gains to one gain-per-pose value, avoiding any global-memory
    round-trip per march step (this file round-trips through a numpy array
    per step, which is the CPU-appropriate analogue but would be the wrong
    thing to do on a GPU).
(d) What stays algorithmically identical: the entropy-of-log-odds formula,
    the transmittance recursion, and the optional semantic-prior weighting
    -- none of that is CPU/GPU-specific; only the loop structure, memory
    residency, and interpolation mode change. That is the point of keeping
    this file's math exactly what a GPU port would keep.
"""

import math

import numpy as np

import sensor_model as sm


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -30, 30)))


def binary_entropy(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return -(p * np.log(p) + (1 - p) * np.log(1 - p))


def sample_ray_directions(n_x=8, n_y=6, hfov_deg=None, vfov_deg=45.0, aspect=None):
    """Camera-local (r,u,f)-space ray direction offsets spanning the real
    FOV, as (n_x*n_y, 3) unit-ish vectors with f-component=1 (consistent
    with `sensor_model`'s x_ndc/y_ndc convention)."""
    if hfov_deg is None:
        hfov_deg = 2.0 * math.degrees(math.atan((aspect or 1.0) * math.tan(math.radians(vfov_deg) / 2.0)))
    xs = np.linspace(-math.tan(math.radians(hfov_deg) / 2.0), math.tan(math.radians(hfov_deg) / 2.0), n_x)
    ys = np.linspace(-math.tan(math.radians(vfov_deg) / 2.0), math.tan(math.radians(vfov_deg) / 2.0), n_y)
    xx, yy = np.meshgrid(xs, ys, indexing="xy")
    return np.stack([xx.ravel(), yy.ravel(), np.ones(xx.size)], axis=1)  # (R,3): (x_ndc, y_ndc, 1)


FRUIT_BOOST = 2.0


def batch_information_gain(grid, poses_eye_lookat, intr, semantic_posterior=None,
                            n_rays_x=8, n_rays_y=6, max_range=0.4, n_steps=20):
    """grid: occupancy_map.VoxelGrid (log_odds, bmin, voxel_size, dims).
    poses_eye_lookat: list of (eye, lookat) real world tuples (P poses).
    semantic_posterior: optional (dims+(6,)) array from semantic_map.py;
    if given, entropy at each voxel is boosted by fruit-class posterior.
    Returns per-pose total gain (P,) and per-pose mean gain-per-ray (P,).
    """
    P = len(poses_eye_lookat)
    ray_local = sample_ray_directions(n_rays_x, n_rays_y, vfov_deg=intr["vfov_deg"],
                                       aspect=intr["W"] / intr["H"])  # (R,3)
    R = ray_local.shape[0]

    eyes = np.zeros((P, 3))
    rights = np.zeros((P, 3))
    ups = np.zeros((P, 3))
    forwards = np.zeros((P, 3))
    for i, (eye, lookat) in enumerate(poses_eye_lookat):
        f, r, u = sm.camera_basis(eye, lookat)
        eyes[i], rights[i], ups[i], forwards[i] = eye, r, u, f

    # world-space ray direction per (pose, ray): (P,R,3)
    ray_dirs = (ray_local[None, :, 0:1] * rights[:, None, :] +
                ray_local[None, :, 1:2] * ups[:, None, :] +
                ray_local[None, :, 2:3] * forwards[:, None, :])
    ray_dirs = ray_dirs / np.linalg.norm(ray_dirs, axis=2, keepdims=True)

    step_dists = np.linspace(max_range / n_steps, max_range, n_steps)  # (S,)

    transmittance = np.ones((P, R), dtype=np.float64)
    gain_accum = np.zeros((P, R), dtype=np.float64)

    d = grid.dims
    n_classes = semantic_posterior.shape[-1] if semantic_posterior is not None else None

    for s in range(n_steps):
        pts = eyes[:, None, :] + step_dists[s] * ray_dirs  # (P,R,3)
        flat_pts = pts.reshape(-1, 3)
        idx = np.floor((flat_pts - grid.bmin) / grid.voxel_size).astype(np.int64)
        valid = np.all((idx >= 0) & (idx < np.array(d)), axis=1)
        p_occ = np.full(flat_pts.shape[0], 0.5)  # out-of-bounds treated as unknown
        if np.any(valid):
            flat_idx = np.ravel_multi_index((idx[valid, 0], idx[valid, 1], idx[valid, 2]), d)
            L = grid.log_odds.reshape(-1)[flat_idx]
            p_occ[valid] = sigmoid(L)
        ent = binary_entropy(p_occ)
        if semantic_posterior is not None and np.any(valid):
            post_flat = semantic_posterior.reshape(-1, n_classes)
            p_fruit = np.zeros(flat_pts.shape[0])
            p_fruit[valid] = post_flat[flat_idx, 1]  # class 1 = fruit
            ent = ent * (1.0 + FRUIT_BOOST * p_fruit)
        ent = ent.reshape(P, R)
        p_occ_grid = p_occ.reshape(P, R)

        gain_accum += transmittance * ent
        transmittance = transmittance * (1.0 - p_occ_grid)

    total_gain = gain_accum.sum(axis=1)
    mean_gain_per_ray = gain_accum.mean(axis=1)
    return total_gain, mean_gain_per_ray


if __name__ == "__main__":
    import json
    import os
    import time

    import kinematics as kin
    from occupancy_map import build_dual_resolution_map
    from semantic_map import build_semantic_map

    HERE = os.path.dirname(os.path.abspath(__file__))
    DATA = os.path.join(HERE, "data")

    coarse, fine_grids, occ_report = build_dual_resolution_map(DATA, pixel_stride=2)
    smap, sem_report = build_semantic_map(DATA)
    report = json.load(open(os.path.join(DATA, "gen_report.json")))
    intr = sm.intrinsics(tuple(report["resolution"]))

    arm_name = "arm_high"
    joints_arr = np.load(os.path.join(DATA, f"roadmap_{arm_name}_nodes.npy"))
    arms = {a.name: a for a in kin.single_tree_arm_configs()}
    arm = arms[arm_name]
    poses = []
    for row in joints_arr:
        q = kin.JointState(*row)
        pose = kin.forward_kinematics(q, arm)
        poses.append((pose.position, pose.lookat))
    print(f"Evaluating information gain over {len(poses)} real reachable roadmap nodes ({arm_name})")

    t0 = time.time()
    total_gain, mean_gain = batch_information_gain(coarse, poses, intr, semantic_posterior=smap.posterior())
    elapsed = time.time() - t0

    order = np.argsort(-total_gain)
    top5 = [{"node_index": int(i), "total_gain": float(total_gain[i]), "mean_gain_per_ray": float(mean_gain[i])}
            for i in order[:5]]
    bottom5 = [{"node_index": int(i), "total_gain": float(total_gain[i])} for i in order[-5:]]

    out = {
        "n_candidate_poses": len(poses), "n_rays_per_pose": 8 * 6, "n_march_steps": 20,
        "batched_eval_time_s": elapsed, "time_per_pose_ms": elapsed / len(poses) * 1000.0,
        "gain_mean": float(total_gain.mean()), "gain_std": float(total_gain.std()),
        "gain_min": float(total_gain.min()), "gain_max": float(total_gain.max()),
        "top5_highest_gain_nodes": top5, "bottom5_lowest_gain_nodes": bottom5,
    }
    print(json.dumps(out, indent=2))
    with open(os.path.join(HERE, "output_t45_information_gain.json"), "w") as fh:
        json.dump(out, fh, indent=2, default=str)
