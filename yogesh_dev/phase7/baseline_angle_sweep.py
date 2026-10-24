"""
T7.3 (D2) -- baseline-angle sweep. Per the task doc, "likely your core
figure": arc width 5 deg -> 360 deg, with and without pose conditioning.
"Theory predicts sharp collapse at small disparity when uncalibrated, none
when posed."

Same PROXY caveat as T7.2 (see pose_conditioning_ablation.py's docstring
and PHASE7_LOG.md): no MapAnything/DA3/pi-cubed/VGGT available in this
env, so "posed" / "unposed" reconstruction quality is measured with the
same hand-rolled classical multi-view geometry (`mv_geometry.py`), not the
named foundation models.

## Experimental design

Real camera poses, generated from Phase 0's validated rig-sizing logic
(`render_utils.tree_lookat_and_radius`/`arc_camera_poses`) on a real
Helios-grown apple tree: N_VIEWS=8 cameras evenly spaced across an arc of
width `w`, for w in a 21-point sweep from 5 deg to 360 deg (dense enough
near the small-angle region, where the predicted collapse should live, to
actually resolve the curve's shape rather than a couple of samples).

Correspondences are the SAME simplification as T7.2: real 3D landmark
points (branch-segment midpoints + fruit centroids) projected through
each view's real, validated K/[R|t] with Gaussian pixel noise standing in
for feature detection/matching (no opencv/torch in this env -- see
PHASE7_LOG.md). No actual RGB/depth rendering is performed for the 21
sweep points -- the reconstruction math here (DLT triangulation,
essential-matrix pose recovery) consumes only these projected 2D points,
never pixel values, so rendering images would produce files nobody reads;
that would be real compute spent on an artifact this experiment doesn't
use. (T7.1's WAI writer is what produces real rendered artifacts, reused
directly by T7.6.)

Two conditions, matching T7.2's C and B:
  - POSED   : DLT triangulation using ALL N_VIEWS' REAL K/R/t (T7.2's
              condition C). No pose estimation error possible by
              construction -- if this collapses at small arc width, it is
              a triangulation-conditioning effect, not a gauge-freedom
              artifact of the OTHER estimation step.
  - UNPOSED : two-view essential matrix (K known, R/t estimated) between
              the WIDEST pair within each arc (view 0 and view N-1 -- the
              actual baseline `w` under test), Umeyama-aligned (T7.2's
              condition B). At small `w`, the two cameras are nearly
              coincident -> near-degenerate epipolar geometry -> pose
              estimation is expected to become numerically unstable, i.e.
              exactly the "sharp collapse" the theory predicts.
"""

import json
import math
import os

import numpy as np

from pyhelios import Context, PlantArchitecture

from yogesh_dev.phase0.pose_convention import look_at_view_matrix, intrinsics_matrix
from yogesh_dev.phase1.ground_truth import enable_fruit_object_data

from yogesh_dev.phase7 import mv_geometry as mv
from yogesh_dev.phase7.render_utils import (
    RESOLUTION, VFOV_DEG, build_tree_scene, tree_lookat_and_radius, arc_camera_poses,
    full_circle_poses, build_camera_properties, branch_skeleton_points, fruit_landmark_points,
)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
N_VIEWS = 8
ELEVATION_DEG = 15.0
PIXEL_NOISE_SIGMA_PX = 0.5
MAX_BRANCH_POINTS = 60
TREE_AGE_DAYS = 720.0
ARC_WIDTHS_DEG = [5, 8, 12, 16, 20, 25, 30, 40, 50, 60, 75, 90, 105, 120,
                  135, 150, 180, 210, 240, 270, 300, 330, 360]


def _poses_for_arc(lookat, radius, arc_width_deg):
    if arc_width_deg >= 359.999:
        return full_circle_poses(lookat, radius, N_VIEWS, elevation_deg=ELEVATION_DEG)
    return arc_camera_poses(lookat, radius, N_VIEWS, arc_width_deg, elevation_deg=ELEVATION_DEG)


def run(seed=0):
    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            enable_fruit_object_data(plantarch)
            plant_id, position, all_uuids = build_tree_scene(context, plantarch, age_days=TREE_AGE_DAYS)
            branch_pts, segments, seg_counts = branch_skeleton_points(
                context, all_uuids, max_points=MAX_BRANCH_POINTS, seed=seed)
            fruit_pts = fruit_landmark_points(context, plantarch, [plant_id])
            lookat, radius, height, width = tree_lookat_and_radius(context, all_uuids, position)

    landmarks = (
        [{"point": p["point"], "type": "branch"} for p in branch_pts]
        + [{"point": p["point"], "type": "fruit"} for p in fruit_pts]
    )
    gt_all = np.array([lm["point"] for lm in landmarks])

    _, hfov_deg = build_camera_properties(RESOLUTION, VFOV_DEG)
    W, H = RESOLUTION
    K = intrinsics_matrix(W, H, hfov_deg)
    rng = np.random.default_rng(seed)
    margin = 4.0

    sweep_results = []
    for arc_width_deg in ARC_WIDTHS_DEG:
        poses, azs_deg = _poses_for_arc(lookat, radius, arc_width_deg)
        viewmats = [look_at_view_matrix(eye, lk) for eye, lk in poses]
        Ps = [K @ vm[:3, :] for vm in viewmats]

        exact_uv = np.zeros((N_VIEWS, len(landmarks), 2))
        depths = np.zeros((N_VIEWS, len(landmarks)))
        for j, vm in enumerate(viewmats):
            for i, lm in enumerate(landmarks):
                uv, d = mv.project_point(K, vm, lm["point"])
                exact_uv[j, i] = uv if uv is not None else (-1e9, -1e9)
                depths[j, i] = d
        in_frame = np.all(
            (exact_uv[:, :, 0] >= margin) & (exact_uv[:, :, 0] < W - margin) &
            (exact_uv[:, :, 1] >= margin) & (exact_uv[:, :, 1] < H - margin) &
            (depths > 0.05),
            axis=0,
        )
        keep_idx = np.where(in_frame)[0]
        n_kept = len(keep_idx)
        gt_kept = gt_all[keep_idx]

        noisy_uv = exact_uv[:, keep_idx, :] + rng.normal(0.0, PIXEL_NOISE_SIGMA_PX, size=(N_VIEWS, n_kept, 2))

        # POSED: DLT triangulation, all N_VIEWS, real K/R/t.
        recon_posed = np.array([
            mv.triangulate_linear(Ps, [noisy_uv[j, i] for j in range(N_VIEWS)])
            for i in range(n_kept)
        ])
        rmse_posed = mv.rmse_rigid(recon_posed, gt_kept)

        # UNPOSED: two-view essential matrix, widest pair (0, N_VIEWS-1) = this arc's own baseline.
        pts1, pts2 = noisy_uv[0], noisy_uv[-1]
        try:
            E = mv.eight_point_essential(pts1, pts2, K)
            R_est, t_est, P2, cheirality = mv.select_pose_from_essential(E, K, K, pts1, pts2)
            P1 = K @ np.hstack([np.eye(3), np.zeros((3, 1))])
            recon_unposed = np.array([mv.triangulate_linear([P1, P2], [pts1[i], pts2[i]]) for i in range(n_kept)])
            align = mv.umeyama_alignment(recon_unposed, gt_kept, with_scale=True)
            rmse_unposed = align["rmse"]
            recovered_scale = align["s"]
        except np.linalg.LinAlgError:
            rmse_unposed = float("nan")
            recovered_scale = float("nan")
            cheirality = 0

        sweep_results.append({
            "arc_width_deg": arc_width_deg,
            "n_landmarks_used": n_kept,
            "rmse_posed_mm": rmse_posed * 1000.0,
            "rmse_unposed_mm": (rmse_unposed * 1000.0) if np.isfinite(rmse_unposed) else None,
            "unposed_recovered_scale": recovered_scale if np.isfinite(recovered_scale) else None,
            "unposed_cheirality_inliers": int(cheirality),
        })

    small_arc = [r for r in sweep_results if r["arc_width_deg"] <= 20]
    large_arc = [r for r in sweep_results if r["arc_width_deg"] >= 180]
    small_arc_unposed_mean = float(np.mean([r["rmse_unposed_mm"] for r in small_arc])) if small_arc else None
    large_arc_unposed_mean = float(np.mean([r["rmse_unposed_mm"] for r in large_arc])) if large_arc else None
    small_arc_posed_mean = float(np.mean([r["rmse_posed_mm"] for r in small_arc])) if small_arc else None
    large_arc_posed_mean = float(np.mean([r["rmse_posed_mm"] for r in large_arc])) if large_arc else None
    posed_collapse_ratio = small_arc_posed_mean / large_arc_posed_mean
    unposed_collapse_ratio = small_arc_unposed_mean / large_arc_unposed_mean
    unposed_over_posed_ratio_by_arc = [
        {"arc_width_deg": r["arc_width_deg"],
         "unposed_over_posed": (r["rmse_unposed_mm"] / r["rmse_posed_mm"]) if r["rmse_unposed_mm"] else None}
        for r in sweep_results
    ]

    report = {
        "seed": seed, "n_views": N_VIEWS, "elevation_deg": ELEVATION_DEG,
        "pixel_noise_sigma_px": PIXEL_NOISE_SIGMA_PX, "hfov_deg": hfov_deg,
        "resolution": list(RESOLUTION), "arc_widths_deg": ARC_WIDTHS_DEG,
        "branch_segment_counts": seg_counts, "n_landmarks_total": len(landmarks),
        "sweep": sweep_results,
        "summary": {
            "small_arc_le_20deg_posed_mean_rmse_mm": small_arc_posed_mean,
            "large_arc_ge_180deg_posed_mean_rmse_mm": large_arc_posed_mean,
            "small_arc_le_20deg_unposed_mean_rmse_mm": small_arc_unposed_mean,
            "large_arc_ge_180deg_unposed_mean_rmse_mm": large_arc_unposed_mean,
            "posed_small_over_large_ratio": posed_collapse_ratio,
            "unposed_small_over_large_ratio": unposed_collapse_ratio,
            "unposed_over_posed_ratio_by_arc": unposed_over_posed_ratio_by_arc,
        },
        # Honest finding, not a forced binary pass/fail (see docstring / PHASE7_LOG.md):
        # UNPOSED is worse than POSED at every arc width (unposed_over_posed_ratio_by_arc
        # is >1 throughout), consistent with the qualitative prediction that pose
        # conditioning helps. But the naive "collapse only when uncalibrated, NONE when
        # posed" claim does NOT hold cleanly for this classical-geometry proxy: POSED
        # (exact K/R/t, linear DLT triangulation) ALSO degrades substantially at small
        # arc width here (posed_small_over_large_ratio), because plain multi-view
        # triangulation has zero learned shape/appearance prior to fall back on when rays
        # are nearly parallel -- it is pure epipolar geometry, so it inherits the textbook
        # triangulation-uncertainty-vs-baseline relationship regardless of pose being
        # exact. A real foundation model (MapAnything/DA3/pi-cubed/VGGT) conditioned on
        # exact pose is hypothesized to avoid most of this collapse via learned priors
        # from training data -- this classical proxy structurally CANNOT test that part
        # of the hypothesis, and that gap is exactly why this is flagged as a proxy
        # throughout rather than presented as if it were the named foundation models.
        "unposed_beats_posed_hypothesis_supported": bool(unposed_collapse_ratio > posed_collapse_ratio),
        "naive_no_collapse_when_posed_supported": bool(posed_collapse_ratio < 2.0),
    }
    return report


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report = run()
    out_path = os.path.join(OUTPUT_DIR, "t73_baseline_angle_sweep.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=float)
    for r in report["sweep"]:
        print(f"arc={r['arc_width_deg']:>6.1f}deg  posed={r['rmse_posed_mm']:>9.3f}mm  "
              f"unposed={r['rmse_unposed_mm']}mm")
    print(json.dumps({k: v for k, v in report["summary"].items() if k != "unposed_over_posed_ratio_by_arc"},
                      indent=2))
    print("unposed_beats_posed_hypothesis_supported:", report["unposed_beats_posed_hypothesis_supported"])
    print("naive_no_collapse_when_posed_supported:", report["naive_no_collapse_when_posed_supported"])
    print("wrote", out_path)
    return report


if __name__ == "__main__":
    main()
