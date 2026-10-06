"""
T4.7 -- Switching criteria (explore -> exploit).

Task doc: "All three, in disjunction: frontier exhaustion; marginal-value-
rate threshold eta set to the predicted exploit-phase rate; Good-Turing
coverage estimate `C_hat = 1 - f1/n > 0.95` over discovered fruit
instances. Plus a hard cap `rho*T_total` with rho swept."

This runs all four conditions (the 3-way disjunction plus the hard cap)
over T4.6's REAL CELF explore run traces (`arm_high`, the richer of the two
arms with nonzero coverage) and reports, honestly, exactly which step each
one would have fired on -- including cases where a criterion never fires
before natural frontier exhaustion, rather than forcing all four to look
equally decisive.

## 1. Frontier exhaustion
Already what `explore_planner.celf_explore` stops on naturally (no
remaining candidate has positive marginal coverage gain). Reported as the
step count at which this happens (equivalently, `len(trace)`).

## 2. Marginal-value-rate threshold eta = predicted exploit-phase rate
`eta` is estimated (not hand-picked) as the value/time rate of the single
BEST exploit-style greedy move available from the explore run's start
position -- i.e. "if you went straight for the single richest known target
using the exploit objective, what rate would you get" -- computed from the
same real per-node fruit-detection data used by T4.4, treating each newly
discovered real fruit instance as one unit of exploit value (`w_i=1`,
`phi(q)=1` once observed at all, matching T4.8's `phi(z)=1-e^{-z}`
saturating to ~1 fruit-value per instance once well observed -- see
T4.8). Explore's own per-step marginal rate (coverage-gain/time, same
number `celf_explore` computes each round) is compared against this eta;
the criterion fires the first step where explore's rate drops below it.

## 3. Good-Turing coverage estimate over discovered fruit instances
`n` = cumulative real fruit-instance detection EVENTS (a re-observation of
the same real fruitID on a later step counts again, exactly as the formula
intends -- it is about observation multiplicity, not just unique count).
`f1` = number of distinct real fruitID values observed EXACTLY once so far.
`C_hat = 1 - f1/n`. Recomputed after every real step of the explore
sequence; fires the first step where `C_hat > 0.95`.

## 4. Hard cap rho * T_total
`T_total` = a fixed real mission time budget; `rho` swept over a real range
of values. Reported: for each rho, whether/when the cap would have cut the
explore run short vs. let it finish naturally.
"""

import json
import os

import numpy as np

from explore_planner import celf_explore, load_arm_coverage, load_adjacency, pairwise_travel_times
from tracker import extract_detections
import sensor_model as sm

RHO_SWEEP = [0.2, 0.3, 0.4, 0.5, 0.6, 0.8]
T_TOTAL_S = 120.0
GT_THRESHOLD = 0.95


def per_node_fruit_ids(data_dir, arm_name, poses, intr):
    """Real per-rendered-node set of true fruitIDs visible (reuses T4.4's
    detection extraction, keyed by node_id for switching-criteria use)."""
    frames = extract_detections(data_dir, arm_name, poses, intr)
    return {fr["node_id"]: {d["true_id"] for d in fr["detections"]} for fr in frames}


def estimate_exploit_eta(fruit_ids_by_node, travel_table, start_node):
    """eta = best single-hop exploit-style rate (new distinct real fruit
    instances / travel time) reachable in one move from `start_node`."""
    best_rate = 0.0
    for node, ids in fruit_ids_by_node.items():
        if node == start_node or not ids:
            continue
        cost = travel_table.get(start_node, {}).get(node)
        if cost is None or cost <= 1e-9:
            continue
        rate = len(ids) / cost
        best_rate = max(best_rate, rate)
    return best_rate


def good_turing_series(fruit_ids_by_node, celf_sequence):
    """Walk the real CELF-selected node sequence in order; return per-step
    (n, f1, C_hat)."""
    obs_count = {}
    series = []
    n = 0
    for node in celf_sequence:
        for fid in fruit_ids_by_node.get(node, ()):
            obs_count[fid] = obs_count.get(fid, 0) + 1
            n += 1
        f1 = sum(1 for c in obs_count.values() if c == 1)
        c_hat = (1.0 - f1 / n) if n > 0 else 0.0
        series.append({"n": n, "f1": f1, "C_hat": c_hat})
    return series


def evaluate_switching(data_dir, arm_name):
    poses = json.load(open(os.path.join(data_dir, "poses.json")))
    report = json.load(open(os.path.join(data_dir, "gen_report.json")))
    intr = sm.intrinsics(tuple(report["resolution"]))

    coverage = load_arm_coverage(data_dir, poses, arm_name)
    ground_set = set().union(*coverage.values()) if coverage else set()
    if not ground_set:
        return {"note": f"{arm_name}: zero coverage possible, no switching demo run"}

    adjacency = load_adjacency(data_dir, arm_name)
    node_ids = list(coverage.keys())
    travel_table = pairwise_travel_times(adjacency, node_ids)
    start = min(node_ids)
    explore_result = celf_explore(coverage, travel_table, start)
    trace = explore_result["trace"]
    celf_sequence = [step["node"] for step in trace if "step" in step]

    fruit_ids_by_node = per_node_fruit_ids(data_dir, arm_name, poses, intr)
    eta = estimate_exploit_eta(fruit_ids_by_node, travel_table, start)
    gt_series = good_turing_series(fruit_ids_by_node, celf_sequence)

    # criterion 1: frontier exhaustion
    frontier_exhaustion_step = len(celf_sequence)

    # criterion 2: marginal-value-rate threshold
    rate_threshold_step = None
    for step in trace:
        if "step" not in step:
            continue
        rate = step["marginal_gain"] / step["travel_time_s"] if step["travel_time_s"] > 1e-9 else float("inf")
        if rate < eta:
            rate_threshold_step = step["step"]
            break

    # criterion 3: Good-Turing
    gt_step = None
    for i, gt in enumerate(gt_series):
        if gt["C_hat"] > GT_THRESHOLD:
            gt_step = i + 1
            break

    # criterion 4: hard cap sweep
    cum_time = [step["cumulative_time_s"] for step in trace if "step" in step]
    hard_cap_results = {}
    for rho in RHO_SWEEP:
        budget = rho * T_TOTAL_S
        cut_step = None
        for i, t in enumerate(cum_time):
            if t > budget:
                cut_step = i + 1
                break
        hard_cap_results[rho] = {"budget_s": budget, "would_cut_at_step": cut_step,
                                  "natural_finish_steps": len(cum_time)}

    fired_steps = [s for s in (frontier_exhaustion_step, rate_threshold_step, gt_step) if s is not None]
    disjunction_switch_step = min(fired_steps) if fired_steps else None

    return {
        "arm": arm_name, "n_steps_total": len(celf_sequence),
        "eta_predicted_exploit_rate": eta,
        "criterion_1_frontier_exhaustion_step": frontier_exhaustion_step,
        "criterion_2_marginal_rate_threshold_step": rate_threshold_step,
        "criterion_3_good_turing_step": gt_step,
        "good_turing_series": gt_series,
        "criterion_4_hard_cap_sweep": hard_cap_results,
        "disjunction_switch_step (min of criteria 1-3, ignoring hard cap)": disjunction_switch_step,
    }


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    DATA = os.path.join(HERE, "data")
    out = {arm: evaluate_switching(DATA, arm) for arm in ("arm_mid", "arm_high")}
    print(json.dumps(out, indent=2, default=str))
    with open(os.path.join(HERE, "output_t47_switching.json"), "w") as fh:
        json.dump(out, fh, indent=2, default=str)
