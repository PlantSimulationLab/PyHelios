"""
T5.6 -- Greedy oracle. At each step, evaluate EVERY remaining candidate in
the real V_reach against ground truth (Phase 2's real per-primitive
vis_i(v)/AVUB machinery, via common.coverage_summary), and pick the
actual best -- brute-force full re-evaluation every round, no CELF laziness
(this IS the oracle T5.5/explore-planner CELF implementations are supposed
to approximate). This is the numerator of the design doc's planning score
Pi.

Reports the full step trace plus results at k=1..8 (to pair directly
against T5.7's ILP optimum at the same k's) and the natural saturation
point (marginal gain <= epsilon).
"""

from .common import coverage_summary, union_of


def run_t56(reachable_candidates, fruit_records, fruit_prim_ids, prim_id_to_info,
            k_checkpoints=(1, 2, 3, 4, 5, 6, 7, 8), max_steps=40, eps=1e-9):
    n = len(reachable_candidates)
    remaining = list(range(n))
    covered = set()
    order = []
    trace = []
    at_k = {}

    current_frac = 0.0
    for step in range(1, max_steps + 1):
        best_idx, best_new_union, best_frac = None, None, current_frac
        for j in remaining:
            candidate_union = covered | reachable_candidates[j]["visible_ids"]
            frac = coverage_summary(candidate_union, fruit_records, fruit_prim_ids, prim_id_to_info)["mean_coverage_frac"]
            if frac > best_frac:
                best_idx, best_new_union, best_frac = j, candidate_union, frac

        if best_idx is None or (best_frac - current_frac) <= eps:
            break

        gain = best_frac - current_frac
        covered = best_new_union
        current_frac = best_frac
        order.append(best_idx)
        remaining.remove(best_idx)
        trace.append({"step": step, "candidate_index": best_idx, "marginal_gain": gain,
                      "cumulative_mean_coverage_frac": current_frac})

        if step in k_checkpoints:
            summary = coverage_summary(covered, fruit_records, fruit_prim_ids, prim_id_to_info)
            at_k[step] = {"n_views_used": step, **summary}

    final_summary = coverage_summary(covered, fruit_records, fruit_prim_ids, prim_id_to_info)

    return {
        "baseline": "T5.6_greedy_oracle",
        "label": "Greedy oracle -- brute-force full evaluation of every V_reach candidate each round (numerator of Pi)",
        "n_views_used": len(order),
        "trace": trace,
        "at_k": at_k,
        "saturated": len(order) < max_steps,
        **final_summary,
    }
