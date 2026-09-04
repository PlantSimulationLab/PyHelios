"""
T5.5 -- Nearest-frontier + "distance advantage" heuristic. The task doc
calls this "five lines" -- deliberately kept that simple (raw newly-covered
primitive COUNT, not the fruit-area-weighted AVUB value T5.6's oracle uses;
straight-line Euclidean distance, not Phase 3's real execution-time cost).
The core loop really is five lines (see `_pick_next`); it may beat a more
sophisticated planner in the explore phase per the task doc's own framing.
"""

from .common import coverage_summary, sequence_motion_time_s, euclidean


def _pick_next(candidates, remaining, covered, current_eye):
    # --- the "five lines" ---
    best_idx, best_score = None, 0.0
    for j in remaining:
        gain = len(candidates[j]["visible_ids"] - covered)
        if gain <= 0:
            continue
        dist = euclidean(current_eye, candidates[j]["pose"][0])
        score = gain / dist if dist > 1e-6 else gain * 1e9
        if best_idx is None or score > best_score:
            best_idx, best_score = j, score
    return best_idx


def run_t55(reachable_candidates, fruit_records, fruit_prim_ids, prim_id_to_info, start_idx=0):
    n = len(reachable_candidates)
    current = start_idx
    remaining = set(range(n)) - {current}
    covered = set(reachable_candidates[current]["visible_ids"])
    order = [current]

    while True:
        current_eye = reachable_candidates[current]["pose"][0]
        nxt = _pick_next(reachable_candidates, remaining, covered, current_eye)
        if nxt is None:
            break
        covered |= reachable_candidates[nxt]["visible_ids"]
        order.append(nxt)
        remaining.discard(nxt)
        current = nxt

    poses = [reachable_candidates[i]["pose"] for i in order]
    summary = coverage_summary(covered, fruit_records, fruit_prim_ids, prim_id_to_info)
    motion_time_s = sequence_motion_time_s(poses)

    return {
        "baseline": "T5.5_nearest_frontier_distance_advantage",
        "label": "Nearest-frontier + distance-advantage heuristic (five lines)",
        "n_views_used": len(order),
        "motion_time_s": motion_time_s,
        **summary,
    }
