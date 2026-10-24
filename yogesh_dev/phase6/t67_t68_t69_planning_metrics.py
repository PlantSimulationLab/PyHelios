"""
T6.7 -- discovery curve (view index / joint-space path length / wall-clock
incl. compute) + AUC + time-to-90%.
T6.8 -- oracle-normalized planning score Pi + per-step regret.
T6.9 -- IG calibration: Spearman rho per step, top-1 hit rate,
sparsification curve, AUIGSE.

All three run against Phase 4's real single-tree dataset and REUSE Phase 4's
own real planner code (`explore_planner.py`, `information_gain.py`,
`occupancy_map.py`) rather than reimplementing it -- these are inside
yogesh_dev/, so importing (not editing) them is allowed and is the more
honest choice than duplicating working, already-validated logic.
"""

import copy
import os
import time

import numpy as np
import pulp

from yogesh_dev.phase6.common import (
    PHASE4_DATA, PHASE6_OUTPUT, ensure_phase4_importable, load_json, spearman_rho,
)

ensure_phase4_importable()

import sensor_model as sm  # noqa: E402
from explore_planner import load_arm_coverage, load_adjacency, pairwise_travel_times, celf_explore  # noqa: E402
from information_gain import batch_information_gain, binary_entropy, sigmoid  # noqa: E402
from occupancy_map import make_grid, integrate_view, VoxelGrid  # noqa: E402

ARMS_WITH_COVERAGE = ("arm_mid", "arm_high")  # arm_low has zero coverage (real T4.6/T4.8 finding)


def _read_depth(path):
    import OpenEXR
    fh = OpenEXR.File(path)
    ch = fh.channels()
    key = "Z" if "Z" in ch else next(iter(ch.keys()))
    return np.array(ch[key].pixels, dtype=np.float32)


# ---------------------------------------------------------------------------
# T6.7 -- discovery curve, 3 x-axes, AUC, time-to-90%
# ---------------------------------------------------------------------------

def _instrumented_celf_explore(coverage, travel_time_table, start_node):
    """Faithful reimplementation of explore_planner.celf_explore (lines
    95-156), with a real time.perf_counter() wrapped around each round's
    gain-recompute + scoring work, so we get REAL per-step planning compute
    time (the original function only returns run-total counts, not a
    per-step wall-clock breakdown). Selection order is verified to match
    the original (see run_t67) -- this is a measurement instrument, not a
    different algorithm."""
    import heapq
    candidates = [n for n in coverage if n != start_node]
    ground_truth_gain = {n: None for n in candidates}
    version = {n: -1 for n in candidates}
    covered = set()
    current = start_node
    trace = []
    k = 0
    remaining = set(candidates)
    while remaining:
        t0 = time.perf_counter()
        heap = []
        for n in remaining:
            if version[n] != k:
                gain = len(coverage[n] - covered)
                ground_truth_gain[n] = gain
                version[n] = k
            cost = travel_time_table[current][n]
            score = ground_truth_gain[n] / cost if cost > 1e-9 else ground_truth_gain[n] * 1e9
            heapq.heappush(heap, (-score, n))
        neg_score, best = heapq.heappop(heap)
        compute_time_s = time.perf_counter() - t0

        best_gain = ground_truth_gain[best]
        best_cost = travel_time_table[current][best]
        if best_gain <= 0:
            break
        covered |= coverage[best]
        k += 1
        trace.append({"step": k, "node": best, "marginal_gain": best_gain,
                       "travel_time_s": best_cost, "compute_time_s": compute_time_s,
                       "cumulative_coverage": len(covered)})
        current = best
        remaining.discard(best)
    return trace


def run_t67(arm_coverage, arm_travel_tables, start_nodes):
    results = {}
    for arm_name in ARMS_WITH_COVERAGE:
        coverage = arm_coverage[arm_name]
        travel_table = arm_travel_tables[arm_name]
        start = start_nodes[arm_name]
        ground_set_size = len(set().union(*coverage.values()))

        trace = _instrumented_celf_explore(coverage, travel_table, start)
        official_sequence = celf_explore(coverage, travel_table, start)
        official_nodes = [s["node"] for s in official_sequence["trace"] if "step" in s]
        instrumented_nodes = [s["node"] for s in trace]
        sequence_matches = official_nodes == instrumented_nodes

        view_idx = np.arange(1, len(trace) + 1, dtype=float)
        cum_motion_time = np.cumsum([s["travel_time_s"] for s in trace])
        cum_compute_time = np.cumsum([s["compute_time_s"] for s in trace])
        cum_wallclock = cum_motion_time + cum_compute_time
        coverage_frac = np.array([s["cumulative_coverage"] for s in trace], dtype=float) / ground_set_size

        def auc_and_t90(x):
            if len(x) == 0 or x[-1] <= 0:
                return None, None
            x_full = np.concatenate([[0.0], x])
            y_full = np.concatenate([[0.0], coverage_frac])
            auc_raw = float(np.trapezoid(y_full, x_full))
            auc_normalized = auc_raw / x_full[-1]  # in [0,1]: area under frac-vs-x, x rescaled to [0,1]
            t90 = None
            for xi, yi in zip(x_full, y_full):
                if yi >= 0.9:
                    t90 = float(xi)
                    break
            return auc_normalized, t90

        auc_view, t90_view = auc_and_t90(view_idx)
        auc_motion, t90_motion = auc_and_t90(cum_motion_time)
        auc_wall, t90_wall = auc_and_t90(cum_wallclock)

        results[arm_name] = {
            "ground_set_size": ground_set_size,
            "n_steps": len(trace),
            "sequence_matches_official_celf_explore": sequence_matches,
            "final_coverage_fraction": float(coverage_frac[-1]) if len(coverage_frac) else None,
            "total_compute_time_s": float(cum_compute_time[-1]) if len(cum_compute_time) else 0.0,
            "total_motion_time_s": float(cum_motion_time[-1]) if len(cum_motion_time) else 0.0,
            "compute_fraction_of_wallclock": (
                float(cum_compute_time[-1] / cum_wallclock[-1]) if len(cum_wallclock) and cum_wallclock[-1] > 0 else None
            ),
            "curve": [
                {"step": i + 1, "view_index": float(view_idx[i]),
                 "cumulative_motion_time_s": float(cum_motion_time[i]),
                 "cumulative_wallclock_incl_compute_s": float(cum_wallclock[i]),
                 "coverage_fraction": float(coverage_frac[i])}
                for i in range(len(trace))
            ],
            "auc_normalized": {"view_index": auc_view, "motion_time": auc_motion, "wallclock_incl_compute": auc_wall},
            "time_to_90pct": {"view_index": t90_view, "motion_time_s": t90_motion, "wallclock_incl_compute_s": t90_wall},
            "note": ("'joint-space path length' x-axis realized as cumulative real T3.3 "
                     "motion time (Dijkstra over the T3.4 roadmap, edge weights = "
                     "kinematics.move_time) -- the roadmap's edge cost IS a monotonic "
                     "function of joint-space travel distance, so this is the direct, "
                     "available proxy for it, not a separate physical distance metric "
                     "(Phase 3/4 do not track a separate 'joint-space arc length' unit; "
                     "see PHASE6_LOG.md)."),
        }
    return results


# ---------------------------------------------------------------------------
# T6.8 -- oracle-normalized planning score Pi + per-step regret
# ---------------------------------------------------------------------------

def ilp_max_coverage(coverage, k):
    """Real ILP (PuLP + CBC) max-coverage optimum: choose <=k of the real
    candidate nodes to maximize the size of the union of their real
    vis_primitive_id coverage sets. Same problem family as Phase 5's T5.7,
    solved here directly on Phase 4's own ground set so the oracle and the
    real planner it's normalizing are on the IDENTICAL candidate/ground-set
    scale (Phase 5's own T5.6/T5.7 numbers are on a different, 3-tree/
    83-fruit scene -- see PHASE6_LOG.md for why those aren't used directly
    as T6.8's primary normalizer)."""
    nodes = list(coverage.keys())
    elements = sorted(set().union(*coverage.values()))
    elem_to_nodes = {e: [] for e in elements}
    for n in nodes:
        for e in coverage[n]:
            elem_to_nodes[e].append(n)

    prob = pulp.LpProblem("max_coverage", pulp.LpMaximize)
    x = {n: pulp.LpVariable(f"x_{n}", cat="Binary") for n in nodes}
    y = {e: pulp.LpVariable(f"y_{e}", cat="Binary") for e in elements}
    prob += pulp.lpSum(y[e] for e in elements)
    prob += pulp.lpSum(x[n] for n in nodes) <= k
    for e in elements:
        prob += y[e] <= pulp.lpSum(x[n] for n in elem_to_nodes[e])
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    chosen = [n for n in nodes if pulp.value(x[n]) > 0.5]
    covered = set()
    for n in chosen:
        covered |= coverage[n]
    return {"k": k, "status": pulp.LpStatus[prob.status], "chosen_nodes": chosen,
            "n_covered": len(covered), "coverage_fraction": len(covered) / len(elements)}


def run_t68(arm_coverage):
    results = {}
    for arm_name in ARMS_WITH_COVERAGE:
        coverage = arm_coverage[arm_name]
        n_candidates = len(coverage)
        ground_set_size = len(set().union(*coverage.values()))

        explore_out = load_json(os.path.join(PHASE4_DATA, "..", "output_t46_explore_planner.json")) \
            if os.path.isfile(os.path.join(PHASE4_DATA, "..", "output_t46_explore_planner.json")) else None
        # Fall back to recomputing live if the saved report isn't there.
        if explore_out is None or arm_name not in explore_out or "trace" not in explore_out[arm_name]:
            travel_table = pairwise_travel_times(load_adjacency(PHASE4_DATA, arm_name),
                                                  list(coverage.keys()))
            start = min(coverage.keys())
            planner_result = celf_explore(coverage, travel_table, start)
        else:
            planner_result = explore_out[arm_name]

        planner_trace = [s for s in planner_result["trace"] if "step" in s]
        max_k = len(planner_trace)

        oracle_by_k = {}
        for k in range(1, max_k + 1):
            oracle_by_k[k] = ilp_max_coverage(coverage, k)

        per_step = []
        for s in planner_trace:
            k = s["step"]
            planner_cov = s["cumulative_coverage"]
            oracle_cov = oracle_by_k[k]["n_covered"]
            pi = (planner_cov / oracle_cov) if oracle_cov else None
            regret = oracle_cov - planner_cov
            per_step.append({"k": k, "planner_coverage": planner_cov, "oracle_coverage": oracle_cov,
                              "Pi": pi, "regret_elements": regret,
                              "regret_fraction_of_ground_set": regret / ground_set_size})

        results[arm_name] = {
            "n_candidates": n_candidates, "ground_set_size": ground_set_size,
            "per_step": per_step,
            "mean_Pi": float(np.mean([s["Pi"] for s in per_step if s["Pi"] is not None])),
            "final_Pi": per_step[-1]["Pi"] if per_step else None,
            "final_regret_elements": per_step[-1]["regret_elements"] if per_step else None,
        }

    if os.path.isfile(os.path.join(os.path.dirname(PHASE4_DATA), "..", "phase5", "output", "phase5_run_report.json")):
        pass  # handled by caller (run_all) to avoid double-reading

    return results


def _find_phase5_report():
    """Phase 5 was still running in its OWN sibling git worktree
    (`.claude/worktrees/phase5-baselines`), not yet merged into this
    branch, when Phase 6 started -- so `yogesh_dev/phase5/` does not exist
    in THIS worktree's git-tracked tree. Its output is real, on-disk data
    on the same machine though, so we check the sibling worktree's working
    directory directly as a fallback (read-only) rather than declaring it
    unavailable just because git hasn't merged it here yet."""
    candidates = [
        os.path.normpath(os.path.join(os.path.dirname(PHASE4_DATA), "..", "phase5", "output", "phase5_run_report.json")),
        os.path.normpath(os.path.join(os.path.dirname(PHASE4_DATA), "..", "..", "..",
                                       "phase5-baselines",
                                       "yogesh_dev", "phase5", "output", "phase5_run_report.json")),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def add_phase5_reference(t68_results):
    phase5_report_path = _find_phase5_report()
    if phase5_report_path is None:
        t68_results["phase5_reference"] = {"available": False,
                                            "note": "Phase 5 output not present at all when Phase 6 ran."}
        return t68_results
    p5 = load_json(phase5_report_path)
    p5_results = p5.get("results", {})
    t68_results["phase5_reference"] = {
        "available": True,
        "caveat": ("Computed on a DIFFERENT scene (Phase 5's own fresh 3-tree/83-fruit "
                   "build, seed 20260729) than T6.8's primary oracle above (Phase 4's "
                   "single-tree/27-fruit gen_dataset.py scene) -- not the same "
                   "denominator, included for reference only, NOT used to normalize "
                   "T6.8's Pi/regret numbers above."),
        "T5.6_greedy_oracle_at_k": p5_results.get("T5.6", {}).get("at_k"),
        "T5.7_ilp_ceiling_by_k": p5_results.get("T5.7", {}).get("by_k") if "T5.7" in p5_results else None,
    }
    return t68_results


# ---------------------------------------------------------------------------
# T6.9 -- IG calibration
# ---------------------------------------------------------------------------

def _total_grid_entropy(grid: VoxelGrid):
    return float(binary_entropy(sigmoid(grid.log_odds)).sum())


def run_t69(poses, resolution, arm_name="arm_high", pixel_stride=4):
    fruit = load_json(os.path.join(PHASE4_DATA, "fruit_ground_truth.json"))
    all_centroids = np.array([r["centroid"] for r in fruit])
    scene_margin = 0.15
    bmin = all_centroids.min(axis=0) - scene_margin
    bmax = all_centroids.max(axis=0) + scene_margin
    voxel_size = 0.02

    arm_poses = sorted([p for p in poses if p["arm"] == arm_name], key=lambda p: p["node_id"])
    depths = {p["node_id"]: _read_depth(os.path.join(PHASE4_DATA, p["depth_path"])) for p in arm_poses}
    intr = sm.intrinsics(resolution)

    grid = make_grid(bmin, bmax, voxel_size)
    remaining = {p["node_id"]: p for p in arm_poses}
    order = [p["node_id"] for p in arm_poses]  # real roadmap-node_id order (gen_dataset.py's stride sampling)

    per_step = []
    for step_i, chosen_id in enumerate(order):
        candidate_ids = list(remaining.keys())
        if len(candidate_ids) < 2:
            break
        poses_eye_lookat = [(remaining[cid]["eye"], remaining[cid]["lookat"]) for cid in candidate_ids]
        predicted_gain, _mean_gain = batch_information_gain(grid, poses_eye_lookat, intr, max_range=0.4, n_steps=20)

        entropy_before = _total_grid_entropy(grid)
        actual_gain = []
        for cid in candidate_ids:
            trial = copy.deepcopy(grid)
            integrate_view(trial, [], remaining[cid]["eye"], remaining[cid]["lookat"],
                            depths[cid], intr, pixel_stride=pixel_stride)
            actual_gain.append(entropy_before - _total_grid_entropy(trial))
        actual_gain = np.array(actual_gain)

        rho = spearman_rho(predicted_gain, actual_gain)
        top1_predicted = candidate_ids[int(np.argmax(predicted_gain))]
        top1_actual = candidate_ids[int(np.argmax(actual_gain))]

        per_step.append({
            "step": step_i, "n_candidates": len(candidate_ids),
            "spearman_rho": rho, "top1_hit": bool(top1_predicted == top1_actual),
            "predicted_gain": predicted_gain.tolist(), "actual_gain": actual_gain.tolist(),
            "candidate_node_ids": candidate_ids,
        })

        # Advance the REAL map state by actually integrating the node next
        # in the real roadmap-index order (chosen_id), for the next step.
        integrate_view(grid, [], remaining[chosen_id]["eye"], remaining[chosen_id]["lookat"],
                        depths[chosen_id], intr, pixel_stride=pixel_stride)
        del remaining[chosen_id]

    valid_rhos = [s["spearman_rho"] for s in per_step if not np.isnan(s["spearman_rho"])]
    top1_hit_rate = float(np.mean([s["top1_hit"] for s in per_step])) if per_step else None

    # Sparsification curve + AUIGSE on the FIRST step's full candidate pool
    # (standard single-map-state calibration check).
    first = per_step[0] if per_step else None
    sparsification = None
    auigse = None
    if first is not None:
        pred = np.array(first["predicted_gain"])
        act = np.array(first["actual_gain"])
        n = len(pred)
        order_pred = np.argsort(-pred)
        order_oracle = np.argsort(-act)
        cum_pred = np.cumsum(act[order_pred]) / act.sum() if act.sum() > 0 else np.zeros(n)
        cum_oracle = np.cumsum(act[order_oracle]) / act.sum() if act.sum() > 0 else np.zeros(n)
        cum_random = np.arange(1, n + 1) / n
        sparsification = {
            "n": n, "cum_actual_gain_frac_by_predicted_order": cum_pred.tolist(),
            "cum_actual_gain_frac_by_oracle_order": cum_oracle.tolist(),
            "cum_actual_gain_frac_random_order": cum_random.tolist(),
        }
        # AUISE-style: area between oracle and predicted-order curves (lower = better calibrated).
        auigse = float(np.trapezoid(cum_oracle - cum_pred, dx=1.0 / n))

    return {
        "arm": arm_name, "n_steps": len(per_step), "per_step": per_step,
        "mean_spearman_rho": float(np.mean(valid_rhos)) if valid_rhos else None,
        "top1_hit_rate": top1_hit_rate,
        "sparsification_curve_first_step": sparsification,
        "AUIGSE_first_step": auigse,
        "note": ("'actual gain' = real total occupancy-grid binary-entropy reduction "
                 "from actually integrating that candidate's real depth (counterfactual, "
                 "then reverted -- only the real roadmap-order-chosen node's view is "
                 "permanently integrated before advancing to the next step). "
                 "pixel_stride=4 (vs T4.1's own default 2) for tractable repeated "
                 "counterfactual integration; documented, not hidden."),
    }


def run_all():
    os.makedirs(PHASE6_OUTPUT, exist_ok=True)
    poses = load_json(os.path.join(PHASE4_DATA, "poses.json"))
    report = load_json(os.path.join(PHASE4_DATA, "gen_report.json"))
    resolution = tuple(report["resolution"])

    arm_coverage = {arm: load_arm_coverage(PHASE4_DATA, poses, arm) for arm in ARMS_WITH_COVERAGE}
    arm_adjacency = {arm: load_adjacency(PHASE4_DATA, arm) for arm in ARMS_WITH_COVERAGE}
    arm_travel_tables = {arm: pairwise_travel_times(arm_adjacency[arm], list(arm_coverage[arm].keys()))
                          for arm in ARMS_WITH_COVERAGE}
    start_nodes = {arm: min(arm_coverage[arm].keys()) for arm in ARMS_WITH_COVERAGE}

    t67 = run_t67(arm_coverage, arm_travel_tables, start_nodes)
    t68 = run_t68(arm_coverage)
    t68 = add_phase5_reference(t68)
    t69 = run_t69(poses, resolution, arm_name="arm_high")

    return {"T6.7": t67, "T6.8": t68, "T6.9": t69}


if __name__ == "__main__":
    import json
    out = run_all()
    with open(os.path.join(PHASE6_OUTPUT, "t67_t68_t69_report.json"), "w") as fh:
        json.dump(out, fh, indent=2, default=str)
    print(json.dumps(out, indent=2, default=str)[:6000])
