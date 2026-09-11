"""
T5.2 -- Static 3-camera rig, no arm motion (Phase 0's original above/
level/below rig position, one set per tree). This is THE REALISTIC
COMMERCIAL ALTERNATIVE: a fixed multi-camera installation with zero moving
parts, the thing an active-vision arm actually has to beat to be worth its
mechanical complexity.
"""

from .common import coverage_summary, union_of


def run_t52(static_rig, fruit_records, fruit_prim_ids, prim_id_to_info):
    """`static_rig`: list of 9 {'pose', 'visible_ids'} dicts (3 trees x 3
    rig heights), all real rendered views, per
    common.render_static_rig_and_single_fixed. No arm motion -> 0 motion
    time (the rig is simply always in position)."""
    union = union_of(r["visible_ids"] for r in static_rig)
    summary = coverage_summary(union, fruit_records, fruit_prim_ids, prim_id_to_info)
    return {
        "baseline": "T5.2_static_3camera_rig",
        "label": "Static 3-camera rig, no arm motion -- the realistic commercial alternative",
        "n_views_used": len(static_rig),
        "motion_time_s": 0.0,
        **summary,
    }
