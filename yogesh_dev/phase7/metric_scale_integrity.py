"""
T7.7 (D6) -- metric-scale integrity.

Task doc: "Canopy volume, leaf area, fruit diameter, internode length --
metrically correct, not just plausible." Cross-checked "against the real
reconstruction from T7.6/whatever anchor ran in T7.2."

## Ground truth (real, direct from the Helios Context -- no reconstruction)

Persisted by T7.6's own tree build (`t76_ground_truth_scale.json`,
`t76_branch_segments.json`) so this cross-check uses the EXACT SAME tree
instance T7.6 reconstructed (growth is stochastic -- a rebuild would
silently be a different tree, see PHASE7_LOG.md):
  - leaf_area_m2: real, `getPrimitiveArea` summed over every real leaf
    primitive.
  - canopy_bbox_volume_m3: real domain bounding box of the whole tree.
  - mean_internode_length_m: real, mean length of real `shoot` tube
    segments (node-to-node).
  - fruit diameters: real, equivalent-sphere diameter from real fruit
    surface area (same method as Phase 1 T1.2).

## Reconstructed side (from T7.6's actual fused voxel grid -- real, not
## fabricated numbers)

  - canopy_volume: occupied fine-voxel count x voxel_size^3. A real, if
    crude, occupied-space volume estimate from the actual reconstruction.
  - fruit_diameter: for each real fruit centroid, the spatial extent
    (max pairwise distance) of occupied fine voxels within a search
    radius of that centroid -- skipped for fruit with too few nearby
    occupied voxels to make the extent meaningful (reported explicitly).
  - internode_length: for each real shoot segment, snap each endpoint to
    its NEAREST actually-occupied fine voxel (if one exists within a
    small tolerance) and measure the reconstructed endpoint-to-endpoint
    distance -- segments with no occupied voxel near one endpoint are
    excluded (reported explicitly), not silently zero-filled.
  - leaf_area: NOT cross-checked. A sparse occupancy voxel grid has no
    per-primitive surface classification, so there is no principled way
    to recover a leaf AREA (a 2D quantity) from a 3D occupied-voxel set
    without assuming a leaf model this phase doesn't have. Reported as
    ground-truth-only, explicitly flagged as not cross-checked, rather
    than backed into a fabricated "reconstructed leaf area."

## Why this matters (ties back to T7.2)

T7.2 (D1) found that reconstruction is only in true metric scale when
extrinsics are known (conditions C/D); condition B (intrinsics only)
recovers correct SHAPE but an arbitrary, wrong absolute SCALE. T7.6's
depth fusion uses EXACT poses throughout (condition C/D territory), so
the prediction is that these physical quantities should come out close to
ground truth. Any large relative error here would be evidence that scale
integrity breaks down even with exact poses (e.g. from systematic
occupancy-grid discretization bias), which T7.2's HIGH-baseline-only
argument alone would not have caught.
"""

import json
import os

import numpy as np

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
FRUIT_SEARCH_RADIUS_FACTOR = 1.3
MIN_VOXELS_FOR_FRUIT_EXTENT = 4
INTERNODE_SNAP_TOL_VOXELS = 2
MAX_INTERNODE_SEGMENTS_CHECKED = 200


def _rel_err(recon, gt):
    if recon is None or gt is None or gt == 0:
        return None
    return (recon - gt) / gt


def run():
    with open(os.path.join(OUTPUT_DIR, "t76_ground_truth_scale.json")) as f:
        gt = json.load(f)
    with open(os.path.join(OUTPUT_DIR, "t76_branch_segments.json")) as f:
        segments = json.load(f)
    with open(os.path.join(OUTPUT_DIR, "t76_classical_baseline.json")) as f:
        t76_report = json.load(f)

    fine = np.load(os.path.join(OUTPUT_DIR, "t76_grid_fine.npz"))
    occupied, bmin, voxel_m = fine["occupied"], fine["bmin"], float(fine["voxel_size"])
    dims = np.array(occupied.shape)
    occ_idx = np.argwhere(occupied)
    occ_world = bmin[None, :] + (occ_idx + 0.5) * voxel_m

    # --- Canopy volume ---
    recon_canopy_volume_m3 = len(occ_idx) * (voxel_m ** 3)
    canopy_volume_rel_err = _rel_err(recon_canopy_volume_m3, gt["canopy_bbox_volume_m3"])

    # --- Fruit diameter ---
    # Search radius is tight (1.3x the KNOWN true diameter, using the known
    # fruit centroid as the search center -- fair since T7.6's fusion used
    # the same real fruit geometry, this isn't leaking reconstruction info)
    # specifically so nearby branch/leaf voxels from neighboring geometry
    # aren't swept in and mistaken for this fruit's own surface (same
    # false-positive-neighborhood trap as T7.5's empirical recall check --
    # see thin_structure_recall.py's docstring on tol_voxels). Diameter is
    # estimated as 2x the max distance of nearby occupied voxels FROM THE
    # KNOWN CENTER (not pairwise-among-neighbors, which is far more
    # sensitive to a single stray outlier voxel).
    fruit_results = []
    for fr in gt["fruit"]:
        center = np.array(fr["point"])
        gt_diam = fr["diameter_m"]
        search_r = FRUIT_SEARCH_RADIUS_FACTOR * (gt_diam / 2.0)  # factor x RADIUS, not diameter
        d = np.linalg.norm(occ_world - center[None, :], axis=1)
        nearby_d = d[d <= search_r]
        if len(nearby_d) < MIN_VOXELS_FOR_FRUIT_EXTENT:
            fruit_results.append({"gt_diameter_m": gt_diam, "recon_diameter_m": None,
                                   "n_nearby_voxels": int(len(nearby_d)), "skipped": True})
            continue
        recon_diam = float(2.0 * nearby_d.max())
        fruit_results.append({
            "gt_diameter_m": gt_diam, "recon_diameter_m": recon_diam,
            "n_nearby_voxels": int(len(nearby_d)), "skipped": False,
            "rel_err": _rel_err(recon_diam, gt_diam),
        })
    used_fruit = [r for r in fruit_results if not r["skipped"]]
    mean_fruit_rel_err = float(np.mean([abs(r["rel_err"]) for r in used_fruit])) if used_fruit else None

    # --- Internode length ---
    rng = np.random.default_rng(0)
    shoot_segs = [s for s in segments if s["label"] == "shoot"]
    if len(shoot_segs) > MAX_INTERNODE_SEGMENTS_CHECKED:
        idx = rng.choice(len(shoot_segs), MAX_INTERNODE_SEGMENTS_CHECKED, replace=False)
        shoot_segs = [shoot_segs[i] for i in idx]

    def snap_to_occupied(point):
        idx = np.floor((point - bmin) / voxel_m).astype(np.int64)
        lo = np.clip(idx - INTERNODE_SNAP_TOL_VOXELS, 0, dims - 1)
        hi = np.clip(idx + INTERNODE_SNAP_TOL_VOXELS + 1, 0, dims)
        if np.any(lo >= hi):
            return None
        window = occupied[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]
        local_idx = np.argwhere(window)
        if len(local_idx) == 0:
            return None
        world_candidates = bmin[None, :] + (lo[None, :] + local_idx + 0.5) * voxel_m
        d = np.linalg.norm(world_candidates - point[None, :], axis=1)
        return world_candidates[np.argmin(d)]

    internode_lengths_recon = []
    n_internode_checked = 0
    n_internode_snapped = 0
    for seg in shoot_segs:
        n_internode_checked += 1
        p0, p1 = np.array(seg["p0"]), np.array(seg["p1"])
        s0, s1 = snap_to_occupied(p0), snap_to_occupied(p1)
        if s0 is None or s1 is None:
            continue
        n_internode_snapped += 1
        internode_lengths_recon.append(float(np.linalg.norm(s1 - s0)))

    recon_mean_internode_m = float(np.mean(internode_lengths_recon)) if internode_lengths_recon else None
    internode_rel_err = _rel_err(recon_mean_internode_m, gt["mean_internode_length_m"])

    report = {
        "source_tree": "same tree instance as t76_classical_baseline.json (reused, not rebuilt)",
        "canopy_volume": {
            "ground_truth_bbox_m3": gt["canopy_bbox_volume_m3"],
            "reconstructed_occupied_voxel_volume_m3": recon_canopy_volume_m3,
            "relative_error": canopy_volume_rel_err,
            "note": "ground truth is a bounding-box volume (a real but crude convex proxy -- "
                    "no scipy.spatial.ConvexHull in this env, see PHASE7_LOG.md); reconstructed "
                    "is occupied-fine-voxel count x voxel^3, which measures FILLED volume, not "
                    "the canopy's convex envelope -- these are related but not identical "
                    "quantities, so relative_error here reflects that definitional gap as well "
                    "as reconstruction error, not reconstruction error alone.",
        },
        "leaf_area": {
            "ground_truth_m2": gt["leaf_area_m2"],
            "reconstructed_m2": None,
            "note": "NOT cross-checked -- see module docstring (no per-primitive surface "
                    "classification recoverable from a sparse occupancy voxel grid).",
        },
        "fruit_diameter": {
            "n_fruit_total": len(gt["fruit"]), "n_fruit_used": len(used_fruit),
            "n_fruit_skipped_too_few_voxels": len(fruit_results) - len(used_fruit),
            "mean_gt_diameter_m": gt["mean_fruit_diameter_m"],
            "mean_absolute_relative_error": mean_fruit_rel_err,
            "per_fruit": fruit_results,
        },
        "internode_length": {
            "n_segments_checked": n_internode_checked, "n_segments_snapped_both_ends": n_internode_snapped,
            "ground_truth_mean_m": gt["mean_internode_length_m"],
            "reconstructed_mean_m": recon_mean_internode_m,
            "relative_error": internode_rel_err,
        },
        "t72_cross_reference": (
            "T7.2 (D1) found metric scale is only correct under conditions C/D (known "
            "extrinsics); condition B (intrinsics only) recovered correct shape but an "
            "arbitrary global scale factor (see t72_pose_conditioning_ablation.json "
            "condition_B_plus_intrinsics.recovered_scale_factor). T7.6's fusion uses exact "
            "poses throughout (C/D territory), so small relative errors here are the expected "
            "regime; this check is what would have caught a discretization-driven scale bias "
            "that T7.2's baseline-only argument could not."
        ),
    }
    return report


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report = run()
    out_path = os.path.join(OUTPUT_DIR, "t77_metric_scale_integrity.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=float)
    print(json.dumps({
        "canopy_volume_rel_err": report["canopy_volume"]["relative_error"],
        "fruit_diameter_mean_abs_rel_err": report["fruit_diameter"]["mean_absolute_relative_error"],
        "internode_length_rel_err": report["internode_length"]["relative_error"],
    }, indent=2))
    print("wrote", out_path)
    return report


if __name__ == "__main__":
    main()
