"""
T2.4 -- Achievable Visibility Upper Bound (AVUB) and AVUB^inf.

    AVUB_i    = fraction of fruit i's surface visible from ANY pose in the
                (placeholder, see reachable_poses.py) reachable set V_reach
    AVUB_i^inf = same, but over the unconstrained free-flying pose set

Both are computed as `fruit_visible_fraction` of the UNION of visible
primitive ids across every pose in the respective set -- i.e. exactly
`visibility.union_visible_ids(...)[-1]` fed through
`visibility.fruit_visible_fraction`, reusing T2.1/T2.2 machinery rather than
a separate implementation.

*** CAVEAT, repeated from reachable_poses.py: V_reach here is a documented
*** PLACEHOLDER grid, not Phase 3's real kinematics-constrained roadmap.
*** AVUB_i / AVUB_i^inf / their ratio will change once Phase 3's real
*** reachable set replaces the placeholder grid -- do not treat these
*** numbers as final hardware-capability figures.
"""

from .visibility import union_visible_ids, fruit_visible_fraction


def compute_avub(per_pose_visible_ids, fruit_records, fruit_prim_ids, prim_id_to_info):
    """Given a list of per-pose visible-id sets (one set per pose in some
    pose collection, e.g. all reachable poses for one tree, or all
    free-flying poses for one tree), return {object_id: AVUB_i} for every
    fruit record in `fruit_records` belonging to that tree.
    """
    union = union_visible_ids(per_pose_visible_ids)[-1] if per_pose_visible_ids else set()
    avub = {}
    for rec in fruit_records:
        oid = rec["object_id"]
        frac, _area = fruit_visible_fraction(
            union, fruit_prim_ids, prim_id_to_info, oid, rec["surface_area_m2"])
        avub[oid] = frac
    return avub


def avub_ratio(avub, avub_inf):
    """AVUB / AVUB^inf per fruit -- the workspace-imposed metric (design doc
    §7.1). Undefined (None) where AVUB^inf itself is 0 (fruit invisible even
    to an unconstrained free-flying camera -- e.g. buried inside the trunk).
    """
    ratio = {}
    for oid, inf_val in avub_inf.items():
        b = avub.get(oid, 0.0)
        ratio[oid] = (b / inf_val) if inf_val > 0 else None
    return ratio


def summarize_avub(avub, avub_inf):
    """Aggregate stats for the log: mean AVUB, mean AVUB^inf, mean of the
    per-fruit ratio (only over fruit with AVUB^inf > 0), and the ratio of
    the means (a second, coarser way to report the same workspace-imposed
    quantity, per design doc §7.1's "AVUB / AVUB^inf" language).
    """
    ratios = avub_ratio(avub, avub_inf)
    defined_ratios = [r for r in ratios.values() if r is not None]
    n = len(avub)
    mean_avub = sum(avub.values()) / n if n else 0.0
    mean_avub_inf = sum(avub_inf.values()) / n if n else 0.0
    return {
        "n_fruit": n,
        "mean_AVUB": mean_avub,
        "mean_AVUB_inf": mean_avub_inf,
        "ratio_of_means_AVUB_over_AVUB_inf": (mean_avub / mean_avub_inf) if mean_avub_inf > 0 else None,
        "mean_per_fruit_ratio_AVUB_over_AVUB_inf": (
            sum(defined_ratios) / len(defined_ratios) if defined_ratios else None
        ),
        "n_fruit_with_AVUB_inf_zero": sum(1 for v in avub_inf.values() if v == 0.0),
    }
