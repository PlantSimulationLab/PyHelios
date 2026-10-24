"""
T5.3 -- Boustrophedon (back-and-forth) raster over the 3 linear axes,
gimbal forward-facing (no separate gimbal search -- each grid pose already
looks level into the canopy, per Phase 2's reachable-pose grid). The task
doc calls this "the engineering-practical competitor, absent from the
entire NBV literature" -- worth getting right, not just checked off.

Reuses Phase 2's PLACEHOLDER_reachable_poses grid (same candidate poses
T5.4/T5.6/T5.7/T5.8 draw from) rather than a separately-invented raster, so
this baseline visits EXACTLY the real V_reach grid, just in a genuine 3D
serpentine (lawnmower) traversal order instead of an arbitrary one:
    for depth (alternating direction each depth level):
        for height (alternating direction each height row):
            for rail (the fast axis)
Trees are visited in sequence (tree 0 fully, then tree 1, then tree 2) --
a single rail spanning the row could equally interleave trees, but visiting
one tree's raster to completion before sliding to the next is what an
actual boustrophedon lawnmower pattern over a row of orchard trees looks
like, and it keeps this baseline's raster order independently verifiable
against the grid's own generation order (see common.py / reachable_poses.py).
"""

from .common import coverage_summary, sequence_motion_time_s, REACHABLE_GRID
from yogesh_dev.phase2.visibility import union_visible_ids


def _boustrophedon_local_order(n_rail, n_height, n_depth):
    """Index order (hi, di, ri) -> flat index, matching
    placeholder_reachable_poses' own generation order (height-major, then
    depth, then rail: `for hf: for df: for rx: append`)."""
    order = []
    for di in range(n_depth):
        height_range = range(n_height) if di % 2 == 0 else range(n_height - 1, -1, -1)
        for hi in height_range:
            rail_range = range(n_rail) if hi % 2 == 0 else range(n_rail - 1, -1, -1)
            for ri in rail_range:
                flat_index = hi * (n_depth * n_rail) + di * n_rail + ri
                order.append(flat_index)
    return order


def run_t53(reachable_candidates, plant_ids, fruit_records, fruit_prim_ids, prim_id_to_info):
    """`reachable_candidates`: flat global V_reach list (common.render_and_cache_reachable),
    in tree-major order, each tree's block internally in placeholder_reachable_poses'
    own (height, depth, rail) generation order."""
    n_rail, n_height, n_depth = REACHABLE_GRID["n_rail"], REACHABLE_GRID["n_height"], REACHABLE_GRID["n_depth"]
    per_tree_n = n_rail * n_height * n_depth
    local_order = _boustrophedon_local_order(n_rail, n_height, n_depth)

    ordered = []
    for t, plant_id in enumerate(plant_ids):
        block = reachable_candidates[t * per_tree_n:(t + 1) * per_tree_n]
        assert len(block) == per_tree_n, "reachable_candidates block size mismatch with REACHABLE_GRID"
        for flat_index in local_order:
            ordered.append(block[flat_index])

    poses = [c["pose"] for c in ordered]
    visible_sequence = [c["visible_ids"] for c in ordered]
    cumulative = union_visible_ids(visible_sequence)
    final_union = cumulative[-1] if cumulative else set()

    summary = coverage_summary(final_union, fruit_records, fruit_prim_ids, prim_id_to_info)
    motion_time_s = sequence_motion_time_s(poses)

    # Discovery-curve sample (view index -> mean coverage frac so far),
    # sampled every 10 views + the final view (Phase 6 discovery-curve framing).
    stride = max(1, len(cumulative) // 20)
    curve = []
    for i in range(stride - 1, len(cumulative), stride):
        frac = coverage_summary(cumulative[i], fruit_records, fruit_prim_ids, prim_id_to_info)["mean_coverage_frac"]
        curve.append({"n_views": i + 1, "mean_coverage_frac": frac})
    if curve and curve[-1]["n_views"] != len(cumulative):
        curve.append({"n_views": len(cumulative), "mean_coverage_frac": summary["mean_coverage_frac"]})

    return {
        "baseline": "T5.3_boustrophedon_raster",
        "label": "Boustrophedon raster over the 3 linear axes -- engineering-practical competitor",
        "n_views_used": len(poses),
        "motion_time_s": motion_time_s,
        "discovery_curve": curve,
        **summary,
    }
