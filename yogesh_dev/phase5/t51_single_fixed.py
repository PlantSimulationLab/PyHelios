"""
T5.1 -- Single fixed camera, one view. The absolute floor: whatever this
one camera happens to see, with no repositioning at all.
"""

from .common import coverage_summary


def run_t51(single_fixed, fruit_records, fruit_prim_ids, prim_id_to_info):
    """`single_fixed`: {'pose': (eye, lookat), 'visible_ids': set(...)} --
    the one real rendered view (see common.render_static_rig_and_single_fixed)."""
    summary = coverage_summary(single_fixed["visible_ids"], fruit_records, fruit_prim_ids, prim_id_to_info)
    return {
        "baseline": "T5.1_single_fixed_camera",
        "label": "Single fixed camera, one view (absolute floor)",
        "n_views_used": 1,
        "motion_time_s": 0.0,
        **summary,
    }
