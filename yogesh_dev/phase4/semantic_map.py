"""
T4.3 -- Semantic layer: per-voxel class posterior fused from
`getPrimitiveDataLabelMap` through known poses.

Task doc: "Per-voxel class posterior fused from `getPrimitiveDataLabelMap`
through known poses." `gen_dataset.py` already produces exactly this input
for real: `semantic_class_id` is a real per-primitive-data field
(fruit=1, leaf=2, shoot=3, petiole=4, peduncle=5, 0=unlabeled/other), read
back per-pixel via `radiation.getPrimitiveDataLabelMap(cam,
"semantic_class_id")` -- the same real ray-traced nearest-hit mechanism
Phase 2's `visibility.py` used for `vis_primitive_id` (see that module's
docstring for why this is real per-primitive ray-traced data, not an
approximation).

Verified empirically (not assumed): the semantic label map's "no hit"
sentinel is NaN (float64 array), and it is pixel-for-pixel identical to the
depth map's `-1.0` sentinel mask (confirmed on a real view,
`arm_mid_33`: 69799/76800 pixels NaN in both, `np.array_equal` true) --
same ray-hit-topology pass, so the two masks are guaranteed aligned; no
separate validity check is needed once you already have the depth mask.

## Posterior representation

Per voxel: a length-6 count vector (classes 0..5) accumulated across every
real pixel (from every one of the 42 real views) whose unprojected world
point falls in that voxel. Posterior = Dirichlet-multinomial with a flat
Laplace prior (alpha=1 per class): `posterior = (counts+alpha) /
(counts.sum()+alpha*n_classes)`. This shares the exact same voxel grid
geometry as T4.1's coarse occupancy grid (same `bmin`/`voxel_size`/`dims`)
so the two layers are spatially aligned and can be queried together (e.g.
T4.6/T4.8's planners can ask "occupied AND posterior(fruit) high" for the
same voxel).
"""

import json
import os

import numpy as np
import OpenEXR

import sensor_model as sm
from occupancy_map import make_grid

N_CLASSES = 6  # 0=unlabeled/other, 1=fruit, 2=leaf, 3=shoot, 4=petiole, 5=peduncle
CLASS_NAMES = {0: "other", 1: "fruit", 2: "leaf", 3: "shoot", 4: "petiole", 5: "peduncle"}


class SemanticVoxelMap:
    def __init__(self, grid_geom):
        self.bmin = grid_geom.bmin
        self.voxel_size = grid_geom.voxel_size
        self.dims = grid_geom.dims
        self.counts = np.zeros(self.dims + (N_CLASSES,), dtype=np.int32)

    def world_to_index(self, points):
        return np.floor((points - self.bmin) / self.voxel_size).astype(np.int64)

    def in_bounds(self, idx):
        d = np.array(self.dims)
        return np.all((idx >= 0) & (idx < d), axis=1)

    def add_observations(self, points, class_ids):
        idx = self.world_to_index(points)
        valid = self.in_bounds(idx)
        idx = idx[valid]
        class_ids = class_ids[valid].astype(np.int64)
        class_ids = np.clip(class_ids, 0, N_CLASSES - 1)
        if len(idx) == 0:
            return
        flat_voxel = np.ravel_multi_index((idx[:, 0], idx[:, 1], idx[:, 2]), self.dims)
        flat_combo = flat_voxel * N_CLASSES + class_ids
        counts_flat = self.counts.reshape(-1)
        np.add.at(counts_flat, flat_combo, 1)

    def posterior(self, alpha=1.0):
        c = self.counts.astype(np.float64) + alpha
        return c / c.sum(axis=-1, keepdims=True)

    def observed_mask(self):
        return self.counts.sum(axis=-1) > 0

    def majority_class(self):
        return np.argmax(self.counts, axis=-1)

    def entropy(self, alpha=1.0):
        p = self.posterior(alpha)
        return -np.sum(p * np.log(p + 1e-12), axis=-1)


def read_depth(path):
    fh = OpenEXR.File(path)
    ch = fh.channels()
    key = "Z" if "Z" in ch else next(iter(ch.keys()))
    return np.array(ch[key].pixels, dtype=np.float32)


def integrate_semantic_view(smap, eye, lookat, depth, semantic, intr, pixel_stride=2):
    f, r, u = sm.camera_basis(eye, lookat)
    valid = (depth != sm.SKY_DEPTH_SENTINEL) & ~np.isnan(semantic)
    H, W = depth.shape
    rows = np.arange(0, H, pixel_stride)
    cols = np.arange(0, W, pixel_stride)
    rr, cc = np.meshgrid(rows, cols, indexing="ij")
    rr = rr.reshape(-1)
    cc = cc.reshape(-1)
    m = valid[rr, cc]
    rr, cc = rr[m], cc[m]
    if len(rr) == 0:
        return 0
    d = depth[rr, cc]
    cls = semantic[rr, cc].astype(np.int64)
    pts = sm.unproject(rr, cc, d, eye, f, r, u, intr)
    smap.add_observations(pts, cls)
    return len(rr)


def build_semantic_map(data_dir, coarse_voxel_m=0.02, scene_margin=0.15, pixel_stride=2, max_views=None):
    poses = json.load(open(os.path.join(data_dir, "poses.json")))
    fruit = json.load(open(os.path.join(data_dir, "fruit_ground_truth.json")))
    report = json.load(open(os.path.join(data_dir, "gen_report.json")))
    intr = sm.intrinsics(tuple(report["resolution"]))

    all_centroids = np.array([r["centroid"] for r in fruit])
    scene_bmin = all_centroids.min(axis=0) - scene_margin
    scene_bmax = all_centroids.max(axis=0) + scene_margin
    grid_geom = make_grid(scene_bmin, scene_bmax, coarse_voxel_m)
    smap = SemanticVoxelMap(grid_geom)

    views = poses if max_views is None else poses[:max_views]
    n_obs = 0
    import time
    t0 = time.time()
    for p in views:
        depth = read_depth(os.path.join(data_dir, p["depth_path"]))
        semantic = np.load(os.path.join(data_dir, p["semantic_path"]))
        n_obs += integrate_semantic_view(smap, p["eye"], p["lookat"], depth, semantic, intr, pixel_stride)
    elapsed = time.time() - t0

    observed = smap.observed_mask()
    majority = smap.majority_class()
    ent = smap.entropy()
    class_voxel_counts = {CLASS_NAMES[c]: int(np.sum(observed & (majority == c))) for c in range(N_CLASSES)}

    report_out = {
        "n_views": len(views), "n_pixel_observations": n_obs, "update_time_s": elapsed,
        "grid_dims": grid_geom.dims, "n_observed_voxels": int(np.sum(observed)),
        "majority_class_voxel_counts": class_voxel_counts,
        "mean_entropy_observed": float(np.mean(ent[observed])) if np.any(observed) else None,
        "mean_entropy_unobserved": float(np.mean(ent[~observed])),
        "max_entropy_possible": float(np.log(N_CLASSES)),
    }
    return smap, report_out


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    DATA = os.path.join(HERE, "data")
    smap, report = build_semantic_map(DATA)
    print(json.dumps(report, indent=2, default=str))
    with open(os.path.join(HERE, "output_t43_semantic_report.json"), "w") as fh:
        json.dump(report, fh, indent=2, default=str)
