"""
T5.8 -- All-reachable-views fusion: union coverage using literally every
pose in the real V_reach (Phase 2's PLACEHOLDER_reachable_poses, all 3
trees). The sensor + workspace ceiling -- this IS Phase 2's own AVUB
computation (avub.compute_avub), just re-derived here on THIS run's fresh
scene so it's directly comparable to every other T5.x number computed on
the same scene. Compare directly against T5.7's smaller-k ILP ceiling to
show the gap between "unlimited views" and "k-view optimum".
"""

from .common import coverage_summary, union_of, sequence_motion_time_s


def run_t58(reachable_candidates, fruit_records, fruit_prim_ids, prim_id_to_info):
    union = union_of(c["visible_ids"] for c in reachable_candidates)
    summary = coverage_summary(union, fruit_records, fruit_prim_ids, prim_id_to_info)
    # Motion time if visited in raster (grid generation) order -- not a
    # minimization, just context for "what unlimited views actually costs".
    poses_in_grid_order = [c["pose"] for c in reachable_candidates]
    motion_time_s = sequence_motion_time_s(poses_in_grid_order)

    return {
        "baseline": "T5.8_all_reachable_fusion",
        "label": "All-reachable-views fusion -- sensor + workspace ceiling (all of V_reach)",
        "n_views_used": len(reachable_candidates),
        "motion_time_s_if_visited_in_grid_order": motion_time_s,
        **summary,
    }
