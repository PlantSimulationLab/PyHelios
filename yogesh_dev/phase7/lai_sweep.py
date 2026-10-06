"""
T7.4 (D3) -- LAI sweep on a fixed branch skeleton.

Task doc: "Helios lets you vary leaf area index continuously on a fixed
branch skeleton (this is exactly what the proposal's occlusion-regulation
module does). Sweep LAI from dormant to dense and measure (i) branch
geometry error and (ii) attention effective rank in the aggregator."

## What's real here, and what's explicitly skipped

- **Fixed branch skeleton, real**: the tree is built ONCE. Growth is
  stochastic (no seed control exposed by PlantArchitecture -- confirmed
  empirically: 3 consecutive builds with identical parameters produced
  57/94/66 shoot objects; see PHASE7_LOG.md) -- so a "fixed skeleton"
  sweep can only be real if leaf density is varied WITHIN one already-grown
  tree, never by rebuilding. This does exactly that: `context.deleteObject`
  removes real leaf compound objects (never shoot/petiole/peduncle), so
  every branch tube node position/radius is bit-identical across the
  entire sweep. Leaf area (`getPrimitiveArea` summed over real remaining
  leaf primitives) is used as the real, monotonic density proxy for LAI
  (no fixed "ground area" is well-defined for a single free-standing tree,
  so this reports real leaf area in m^2 and a documented ground-area-
  normalized approximation, not a from-a-table LAI value).
- **Branch-geometry error, real**: multi-view DLT triangulation
  (`mv_geometry.py`, same machinery as T7.2/T7.3) of each branch-segment
  midpoint from whichever real rendered views actually see it unoccluded
  at that leaf density, vs its real ground-truth position.
- **Occlusion, real**: a landmark counts as "visible" in a view only if
  BOTH (a) the real semantic label at its projected pixel is a branch
  class (shoot/petiole/peduncle) and (b) real rendered depth at that pixel
  matches the landmark's own analytic depth within tolerance -- i.e. an
  actual different, closer piece of geometry (a leaf) was ray-hit there,
  it's excluded, not faked as visible.
- **"Attention effective rank" -- SKIPPED, not approximated.** This
  submetric is intrinsic to a specific foundation model's internal
  aggregator (its cross-view attention weights). No such model runs in
  this environment (see PHASE7_LOG.md) -- there is no attention matrix to
  compute a rank over. Rather than invent a numerically-similar-looking
  but meaningless substitute, this is left out and reported as skipped in
  every result dict, so its absence is never silently blurred into "done."
- **"Occlusion-regulation module" -- confirmed absent.** Phase 2 already
  established this module does not exist anywhere in this codebase (see
  the task brief); nothing here depends on it.
"""

import json
import os

import numpy as np

from pyhelios import Context, PlantArchitecture, RadiationModel

from yogesh_dev.phase0.pose_convention import look_at_view_matrix, intrinsics_matrix
from yogesh_dev.phase0.radiation_setup import setup_bands_and_lights

from yogesh_dev.phase7 import mv_geometry as mv
from yogesh_dev.phase7.render_utils import (
    RESOLUTION, build_tree_scene, tree_lookat_and_radius, full_circle_poses,
    register_camera_pool, render_views, branch_skeleton_points, RGB_BANDS,
)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
N_VIEWS = 8
ELEVATION_DEG = 12.0
PIXEL_NOISE_SIGMA_PX = 0.5
MAX_BRANCH_POINTS = 100
TREE_AGE_DAYS = 720.0
# Descending, nested keep-fractions -- dense canopy (LAI max) down to bare
# skeleton (LAI 0), leaves only ever removed, never re-added, within one tree.
LAI_KEEP_FRACTIONS = [1.0, 0.85, 0.70, 0.55, 0.40, 0.25, 0.15, 0.08, 0.03, 0.0]
DEPTH_OCCLUSION_TOL_M = 0.02
BRANCH_SEMANTIC_CLASS_IDS = {3, 4, 5}  # shoot, petiole, peduncle


def run(seed=0):
    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            plant_id, position, all_uuids = build_tree_scene(context, plantarch, age_days=TREE_AGE_DAYS)
            branch_pts, segments, seg_counts = branch_skeleton_points(
                context, all_uuids, max_points=MAX_BRANCH_POINTS, seed=seed)
            gt_points = np.array([p["point"] for p in branch_pts])
            radii_m = np.array([p["diameter_mm"] for p in branch_pts]) / 2000.0

            leaf_uuids = context.filterPrimitivesByData(all_uuids, "object_label", "leaf")
            leaf_obj_ids = list(context.getUniquePrimitiveParentObjectIDs(leaf_uuids, include_zero=False))
            n_leaf_total = len(leaf_obj_ids)
            rng = np.random.default_rng(seed)
            ordered_leaf_ids = [leaf_obj_ids[i] for i in rng.permutation(n_leaf_total)]
            leaf_obj_to_uuids = {oid: context.getObjectPrimitiveUUIDs(oid) for oid in ordered_leaf_ids}

            x_bounds, y_bounds, _z = context.getDomainBoundingBox(all_uuids)
            footprint_area_m2 = (x_bounds.y - x_bounds.x) * (y_bounds.y - y_bounds.x)

            lookat, radius, height, width = tree_lookat_and_radius(context, all_uuids, position)
            poses, azs_deg = full_circle_poses(lookat, radius, N_VIEWS, elevation_deg=ELEVATION_DEG)

            with RadiationModel(context) as radiation:
                setup_bands_and_lights(radiation)
                labels, hfov_deg = register_camera_pool(radiation, N_VIEWS)
                radiation.updateGeometry()

                W, H = RESOLUTION
                K = intrinsics_matrix(W, H, hfov_deg)
                viewmats = [look_at_view_matrix(eye, lk) for eye, lk in poses]
                Ps = [K @ vm[:3, :] for vm in viewmats]

                remaining_leaf_ids = set(ordered_leaf_ids)
                prev_keep_count = n_leaf_total
                noise_rng = np.random.default_rng(seed + 1000)

                sweep_results = []
                for frac in LAI_KEEP_FRACTIONS:
                    target_keep = int(round(frac * n_leaf_total))
                    to_delete = ordered_leaf_ids[target_keep:prev_keep_count]
                    if to_delete:
                        context.deleteObject(to_delete)
                        for oid in to_delete:
                            remaining_leaf_ids.discard(oid)
                        radiation.updateGeometry()  # real geometry change -> must resync (unlike camera moves)
                    prev_keep_count = target_keep

                    leaf_area_m2 = sum(
                        context.getPrimitiveArea(u)
                        for oid in remaining_leaf_ids for u in leaf_obj_to_uuids[oid]
                    )

                    views = render_views(radiation, labels, poses, want_depth=True, want_semantic=True)
                    depth_imgs = [v["depth"] for v in views]
                    sem_imgs = [v["semantic"] for v in views]

                    n_visible_1plus = 0
                    n_visible_2plus = 0
                    recon_pts, recon_gt = [], []
                    visible_view_counts = []
                    for i, X in enumerate(gt_points):
                        visible_views = []
                        for j, vm in enumerate(viewmats):
                            uv, d = mv.project_point(K, vm, X)
                            if d <= 0.05 or uv is None:
                                continue
                            col, row = int(round(uv[0])), int(round(uv[1]))
                            if not (0 <= row < H and 0 <= col < W):
                                continue
                            sem = sem_imgs[j][row, col]
                            if np.isnan(sem) or int(round(sem)) not in BRANCH_SEMANTIC_CLASS_IDS:
                                continue
                            dd = float(depth_imgs[j][row, col])
                            if dd <= 0 or abs(dd - d) > (DEPTH_OCCLUSION_TOL_M + radii_m[i]):
                                continue
                            visible_views.append((j, uv))
                        visible_view_counts.append(len(visible_views))
                        if len(visible_views) >= 1:
                            n_visible_1plus += 1
                        if len(visible_views) >= 2:
                            n_visible_2plus += 1
                            Ps_v = [Ps[j] for j, _uv in visible_views]
                            pts_v = [uv + noise_rng.normal(0.0, PIXEL_NOISE_SIGMA_PX, size=2)
                                     for _j, uv in visible_views]
                            recon = mv.triangulate_linear(Ps_v, pts_v)
                            recon_pts.append(recon)
                            recon_gt.append(X)

                    rmse = mv.rmse_rigid(np.array(recon_pts), np.array(recon_gt)) if recon_pts else None
                    sweep_results.append({
                        "lai_keep_fraction": frac,
                        "n_leaves_remaining": len(remaining_leaf_ids),
                        "leaf_area_m2": leaf_area_m2,
                        "lai_proxy_leaf_area_over_footprint": leaf_area_m2 / footprint_area_m2,
                        "n_landmarks": len(gt_points),
                        "recall_visible_ge1_view": n_visible_1plus / len(gt_points),
                        "recall_reconstructable_ge2_views": n_visible_2plus / len(gt_points),
                        "mean_visible_views_per_landmark": float(np.mean(visible_view_counts)),
                        "branch_geometry_rmse_mm": rmse * 1000.0 if rmse is not None else None,
                        "attention_effective_rank": None,
                    })

    footprint_note = ("footprint_area_m2 = XY bounding-box area of the full tree at LAI-max "
                       "(a real but crude ground-area proxy for a single free-standing tree, "
                       "not a canopy-row LAI convention)")
    report = {
        "seed": seed, "n_views": N_VIEWS, "elevation_deg": ELEVATION_DEG,
        "pixel_noise_sigma_px": PIXEL_NOISE_SIGMA_PX, "hfov_deg": hfov_deg,
        "resolution": list(RESOLUTION), "n_leaf_objects_total": n_leaf_total,
        "n_branch_landmarks": len(gt_points), "branch_segment_counts": seg_counts,
        "footprint_area_m2": footprint_area_m2, "footprint_note": footprint_note,
        "sweep": sweep_results,
        "attention_effective_rank_note": (
            "SKIPPED (not approximated) for every sweep point: this submetric is intrinsic "
            "to a specific foundation model's internal cross-view attention weights, and no "
            "such model runs in this environment -- see PHASE7_LOG.md. Reporting a "
            "numerically-similar-looking substitute here would misrepresent what was "
            "measured, so `attention_effective_rank` is left `null` throughout instead."
        ),
    }

    dense = [r for r in sweep_results if r["lai_keep_fraction"] >= 0.85]
    sparse = [r for r in sweep_results if r["lai_keep_fraction"] <= 0.15]
    dense_recall = float(np.mean([r["recall_visible_ge1_view"] for r in dense]))
    sparse_recall = float(np.mean([r["recall_visible_ge1_view"] for r in sparse]))
    report["summary"] = {
        "dense_canopy_mean_recall_ge1_view": dense_recall,
        "sparse_canopy_mean_recall_ge1_view": sparse_recall,
        "recall_drop_dense_to_sparse": sparse_recall - dense_recall,
    }
    report["hypothesis_more_leaves_occlude_branches_supported"] = bool(sparse_recall > dense_recall)

    return report


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report = run()
    out_path = os.path.join(OUTPUT_DIR, "t74_lai_sweep.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=float)
    for r in report["sweep"]:
        print(f"keep={r['lai_keep_fraction']:.2f}  leaf_area={r['leaf_area_m2']:.3f}m2  "
              f"recall>=1={r['recall_visible_ge1_view']:.2f}  recall>=2={r['recall_reconstructable_ge2_views']:.2f}  "
              f"branch_rmse={r['branch_geometry_rmse_mm']}")
    print(json.dumps(report["summary"], indent=2))
    print("hypothesis_more_leaves_occlude_branches_supported:",
          report["hypothesis_more_leaves_occlude_branches_supported"])
    print("wrote", out_path)
    return report


if __name__ == "__main__":
    main()
