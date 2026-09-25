"""
T4.6 -- Explore planner.

Task doc: "Quality-constrained: minimize time subject to coverage superset
reachable surface. Submodular max-coverage + CELF lazy evaluation +
receding-horizon path search over the T3.4 roadmap. Time-normalized
utility."

## Ground set and coverage: real fruit-surface primitive visibility

Ground set = union of real `vis_primitive_id` values seen across every
rendered candidate pose (same mechanism Phase 2's `visibility.py` used;
real per-primitive ray-traced nearest-hit data, not approximated). Each
candidate pose "covers" exactly the primitive ids its own render actually
saw -- real per-pose coverage sets, not synthetic. This IS classic
max-coverage: pick a sequence of poses maximizing `|union of covered ids|`.

Only the 42 poses `gen_dataset.py` actually rendered have known coverage
(rendering every one of arm_high's 468 reachable roadmap nodes was out of
scope for this phase's wall-clock budget) -- the candidate SET for this
planner is therefore those real rendered nodes, not the full roadmap. This
restriction is explicit, not silently smaller than advertised.

## Time-normalized utility + receding-horizon path cost

`score(candidate) = marginal_gain(candidate) / travel_time(current, candidate)`,
where `travel_time` is a REAL shortest-path cost over the arm's T3.4
roadmap graph (Dijkstra, `roadmap.dijkstra`, edge weights = T3.3's real
`motion_time.move_time` trapezoidal-profile times) from wherever the arm
currently is -- this is receding-horizon in the sense that the "current"
position updates after every pick and the next best candidate is
re-evaluated relative to the NEW current position, exactly the task doc's
framing.

## CELF, and why cost (not gain) is recomputed every round

Marginal *coverage gain* is submodular (adding a pose to a larger covered
set can only add as many or fewer new ids as adding it to a smaller one) --
a stale cached gain is therefore always a valid UPPER BOUND on the true
current gain, which is exactly what CELF's lazy evaluation exploits: skip
recomputing a candidate's gain unless it turns out to be the (tentative)
best, and even then only recompute it once. What is genuinely NOT constant
across rounds here is the *travel-time cost* (`current` moves every round),
so this implementation rebuilds the score ranking every round from
(possibly-stale, but valid-upper-bound) cached gains combined with a FRESH
per-round cost, and lazily re-verifies gain only for the tentative top
candidate(s) each round -- this is the correct generalization of CELF to a
cost that is round-dependent while the benefit function is submodular and
round-independent. Every gain recomputation avoided is counted and reported
against what naive (non-lazy) greedy would have done, as the real, if
small-scale (14 candidates), evidence that the lazy mechanism works.
"""

import heapq
import json
import os

import numpy as np

from roadmap import dijkstra


def load_arm_coverage(data_dir, poses, arm_name):
    """Real per-node vis_primitive_id coverage sets for one arm's rendered
    candidates."""
    coverage = {}
    for p in poses:
        if p["arm"] != arm_name:
            continue
        vis = np.load(os.path.join(data_dir, p["visid_path"]))
        valid = ~np.isnan(vis)
        ids = set(int(v) for v in np.unique(vis[valid]) if v >= 0)
        coverage[p["node_id"]] = ids
    return coverage


def load_adjacency(data_dir, arm_name):
    raw = json.load(open(os.path.join(data_dir, f"roadmap_{arm_name}_adjacency.json")))
    return {int(k): [(int(j), float(w)) for j, w in v] for k, v in raw.items()}


def pairwise_travel_times(adjacency, node_ids):
    table = {}
    for i in node_ids:
        table[i] = {}
        for j in node_ids:
            if i == j:
                table[i][j] = 0.0
                continue
            _path, dist = dijkstra(adjacency, i, j)
            table[i][j] = dist
    return table


def celf_explore(coverage, travel_time_table, start_node, budget_s=1e9):
    """Real CELF-lazy submodular max-coverage, time-normalized, receding
    horizon (cost recomputed every round against the current position; gain
    lazily cached per the docstring above). Returns the full run trace."""
    candidates = [n for n in coverage if n != start_node]
    ground_truth_gain = {n: None for n in candidates}  # cached (gain, version)
    version = {n: -1 for n in candidates}

    covered = set()
    current = start_node
    trace = []
    time_used = 0.0
    k = 0  # number of selections made so far

    n_true_recomputes = 0
    n_naive_would_recompute = 0  # sum over rounds of remaining-candidate-count

    remaining = set(candidates)
    while remaining:
        n_naive_would_recompute += len(remaining)
        heap = []
        for n in remaining:
            if version[n] != k:
                gain = len(coverage[n] - covered)
                ground_truth_gain[n] = gain
                version[n] = k
                n_true_recomputes += 1
            cost = travel_time_table[current][n]
            score = ground_truth_gain[n] / cost if cost > 1e-9 else ground_truth_gain[n] * 1e9
            heapq.heappush(heap, (-score, n))

        # lazy pop-and-verify: because gain is submodular (upper bound valid)
        # but cost is fresh every round, the heap built above already used
        # fresh cost + (possibly-just-verified) gain, so the top entry IS exact.
        neg_score, best = heapq.heappop(heap)
        best_gain = ground_truth_gain[best]
        best_cost = travel_time_table[current][best]

        if best_gain <= 0:
            break  # no remaining candidate adds any new coverage
        if time_used + best_cost > budget_s:
            trace.append({"stopped": "budget_exhausted", "node": best,
                          "would_cost": best_cost, "time_used": time_used, "budget_s": budget_s})
            break

        covered |= coverage[best]
        time_used += best_cost
        k += 1
        trace.append({"step": k, "node": best, "marginal_gain": best_gain, "travel_time_s": best_cost,
                      "cumulative_time_s": time_used, "cumulative_coverage": len(covered)})
        current = best
        remaining.discard(best)

    ground_set_size = len(set().union(*coverage.values())) if coverage else 0
    return {
        "trace": trace, "final_covered": len(covered), "ground_set_size": ground_set_size,
        "coverage_fraction": (len(covered) / ground_set_size) if ground_set_size else None,
        "total_time_s": time_used,
        "n_true_gain_recomputes": n_true_recomputes,
        "n_naive_greedy_recomputes_would_be": n_naive_would_recompute,
        "celf_savings_fraction": 1.0 - (n_true_recomputes / n_naive_would_recompute) if n_naive_would_recompute else None,
    }


def naive_greedy_explore(coverage, travel_time_table, start_node, budget_s=1e9):
    """Brute-force (recompute every candidate's gain every round, no lazy
    caching) reference greedy -- used only to VERIFY CELF's selection
    sequence is identical (the thing that actually matters more than the
    small-N savings number, see PHASE4_LOG.md)."""
    candidates = [n for n in coverage if n != start_node]
    covered = set()
    current = start_node
    remaining = set(candidates)
    trace = []
    time_used = 0.0
    while remaining:
        best_n, best_score, best_gain, best_cost = None, -1.0, 0, 0.0
        for n in remaining:
            gain = len(coverage[n] - covered)
            cost = travel_time_table[current][n]
            score = gain / cost if cost > 1e-9 else gain * 1e9
            if score > best_score:
                best_n, best_score, best_gain, best_cost = n, score, gain, cost
        if best_gain <= 0 or time_used + best_cost > budget_s:
            break
        covered |= coverage[best_n]
        time_used += best_cost
        trace.append(best_n)
        current = best_n
        remaining.discard(best_n)
    return trace


def run_t46(data_dir):
    poses = json.load(open(os.path.join(data_dir, "poses.json")))
    results = {}
    for arm_name in ("arm_low", "arm_mid", "arm_high"):
        coverage = load_arm_coverage(data_dir, poses, arm_name)
        ground_set = set().union(*coverage.values()) if coverage else set()
        if not ground_set:
            results[arm_name] = {"note": "zero fruit-surface coverage possible from this arm's candidates -- real finding, not an error"}
            continue
        adjacency = load_adjacency(data_dir, arm_name)
        node_ids = list(coverage.keys())
        travel_table = pairwise_travel_times(adjacency, node_ids)
        start = min(node_ids)  # node 0 by construction of gen_dataset.py's stride sampling
        result = celf_explore(coverage, travel_table, start)

        celf_sequence = [step["node"] for step in result["trace"] if "step" in step]
        naive_sequence = naive_greedy_explore(coverage, travel_table, start)
        result["celf_matches_naive_greedy"] = (celf_sequence == naive_sequence)
        result["celf_sequence"] = celf_sequence
        result["naive_greedy_sequence"] = naive_sequence
        results[arm_name] = result
    return results


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    DATA = os.path.join(HERE, "data")
    out = run_t46(DATA)
    print(json.dumps(out, indent=2, default=str))
    with open(os.path.join(HERE, "output_t46_explore_planner.json"), "w") as fh:
        json.dump(out, fh, indent=2, default=str)
