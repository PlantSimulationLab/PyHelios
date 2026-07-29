"""
T4.2 (E1) -- Resolution vs thin-structure calibration.

Task doc: "Sweep voxel size against branch recall by diameter class (<5,
5-10, 10-20, >20mm) and against map update time. Apple leaf lamina is
0.15-0.3mm, twigs 2-10mm, trellis wire 2-3mm. Every published mapping
benchmark you will read was measured at 5cm. This sweep produces the
operating point everything else is built on."

## Ground truth: real primitive dimensions, not synthetic cylinders

`gen_dataset.py`'s `extract_branch_segments` (see PHASE4_LOG.md) produced
1336 REAL tube segments (61 shoot objects + 27 peduncle objects; petiole
excluded -- confirmed Cone-typed, not Tube, see Bug #2 in the log) from the
actual seeded apple tree, each with real node-to-node diameter
(`mid_diameter_mm`, from the real `getTubeObjectNodeRadii` values Helios's
own plant-architecture model assigned). This sweep uses those real per-segment
diameters as the ground truth for "what counts as a hit at each resolution"
-- exactly what the task doc asks for, not a fabricated set of test cylinders.

## Recall criterion (a geometric detectability model, stated explicitly as a choice)

Phase 4's rendered views label pixels by *semantic class* (shoot/petiole/
peduncle/...), not by individual segment identity -- there is no per-segment
"was THIS twig observed as occupied" signal available from the label maps
this dataset has. Measuring recall through the actual beam-model integration
pipeline per individual segment would require per-segment pixel labels this
render pass never produced. So this uses the geometric criterion the field
actually reasons about when choosing a voxel size: a diameter-D structure
produces at least one distinctly-occupied voxel along its length if D >= v
(one-voxel-width criterion), and is *robustly* resolved (multiple voxels
span the diameter, distinguishable from single-voxel sensor noise) if
D >= 2*v. Both are reported -- this is a real, defensible geometric standard
(the same Nyquist-like argument any voxel-size choice in mapping literature
uses), applied to real, not synthetic, segment diameters. It is NOT the same
as re-running the full sensor/log-odds pipeline per segment; that distinction
is kept explicit rather than blurred.

## Update-time sweep: a real, single-resolution GLOBAL grid, timed end to end

To measure the actual map-update cost as a function of resolution (the
second half of T4.2), this builds ONE global `occupancy_map.VoxelGrid`
(no dual-resolution split) covering the full scene AABB at each candidate
voxel size, and integrates all 42 real views through it via
`occupancy_map.integrate_view`, timing the whole pass -- this is what
motivates T4.1's dual-resolution design: a single fine (3mm) GLOBAL grid is
shown here to be far more expensive than a coarse (2cm) global grid plus
small local fine regions.
"""

import json
import os
import time

import numpy as np
import OpenEXR

import sensor_model as sm
from occupancy_map import make_grid, integrate_view

DIAMETER_CLASSES = [("<5mm", 0.0, 5.0), ("5-10mm", 5.0, 10.0), ("10-20mm", 10.0, 20.0), (">20mm", 20.0, 1e9)]
VOXEL_SWEEP_M = [0.05, 0.03, 0.02, 0.01, 0.005, 0.003, 0.002]


def classify_diameter(d_mm):
    for name, lo, hi in DIAMETER_CLASSES:
        if lo <= d_mm < hi:
            return name
    return DIAMETER_CLASSES[-1][0]


def recall_sweep(segments):
    by_class_total = {name: 0 for name, _lo, _hi in DIAMETER_CLASSES}
    for seg in segments:
        by_class_total[classify_diameter(seg["mid_diameter_mm"])] += 1

    results = []
    for v in VOXEL_SWEEP_M:
        v_mm = v * 1000.0
        by_class_hit = {name: 0 for name, _lo, _hi in DIAMETER_CLASSES}
        by_class_robust = {name: 0 for name, _lo, _hi in DIAMETER_CLASSES}
        for seg in segments:
            cls = classify_diameter(seg["mid_diameter_mm"])
            if seg["mid_diameter_mm"] >= v_mm:
                by_class_hit[cls] += 1
            if seg["mid_diameter_mm"] >= 2 * v_mm:
                by_class_robust[cls] += 1
        recall = {name: (by_class_hit[name] / by_class_total[name] if by_class_total[name] else None)
                  for name, _lo, _hi in DIAMETER_CLASSES}
        recall_robust = {name: (by_class_robust[name] / by_class_total[name] if by_class_total[name] else None)
                         for name, _lo, _hi in DIAMETER_CLASSES}
        results.append({"voxel_size_m": v, "n_hit_by_class": by_class_hit,
                         "n_robust_by_class": by_class_robust,
                         "recall_one_voxel": recall, "recall_two_voxel": recall_robust})
    return {"n_segments_total": len(segments), "n_by_class": by_class_total, "sweep": results}


def update_time_sweep(data_dir, voxel_sizes=None, pixel_stride=4, max_views=None):
    if voxel_sizes is None:
        voxel_sizes = VOXEL_SWEEP_M
    poses = json.load(open(os.path.join(data_dir, "poses.json")))
    fruit = json.load(open(os.path.join(data_dir, "fruit_ground_truth.json")))
    report = json.load(open(os.path.join(data_dir, "gen_report.json")))
    intr = sm.intrinsics(tuple(report["resolution"]))

    def read_depth(path):
        fh = OpenEXR.File(path)
        ch = fh.channels()
        key = "Z" if "Z" in ch else next(iter(ch.keys()))
        return np.array(ch[key].pixels, dtype=np.float32)

    all_centroids = np.array([r["centroid"] for r in fruit])
    scene_bmin = all_centroids.min(axis=0) - 0.15
    scene_bmax = all_centroids.max(axis=0) + 0.15
    views = poses if max_views is None else poses[:max_views]
    depths = [read_depth(os.path.join(data_dir, p["depth_path"])) for p in views]

    results = []
    for v in voxel_sizes:
        grid = make_grid(scene_bmin, scene_bmax, v)
        n_voxels = int(np.prod(grid.dims))
        t0 = time.time()
        for p, depth in zip(views, depths):
            integrate_view(grid, [], p["eye"], p["lookat"], depth, intr, pixel_stride=pixel_stride)
        elapsed = time.time() - t0
        counts = grid.counts()
        results.append({"voxel_size_m": v, "dims": grid.dims, "n_voxels": n_voxels,
                         "update_time_s": elapsed, "s_per_view": elapsed / len(views),
                         "counts": counts})
        print(f"  v={v:.4f}m dims={grid.dims} n_voxels={n_voxels:>10d} "
              f"update_time={elapsed:.3f}s ({elapsed/len(views)*1000:.2f}ms/view)")
    return {"n_views": len(views), "pixel_stride": pixel_stride, "sweep": results}


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    DATA = os.path.join(HERE, "data")

    segments = json.load(open(os.path.join(DATA, "branch_segments_gt.json")))
    print(f"Loaded {len(segments)} real tube segments (shoot+peduncle) from gen_dataset.py")
    recall_report = recall_sweep(segments)
    print(json.dumps(recall_report, indent=2))

    print("\nUpdate-time sweep (single global grid, all 42 real views, pixel_stride=4):")
    time_report = update_time_sweep(DATA, pixel_stride=4)

    out = {"recall": recall_report, "update_time": time_report}
    with open(os.path.join(HERE, "output_t42_voxel_sweep.json"), "w") as fh:
        json.dump(out, fh, indent=2, default=str)
