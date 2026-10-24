"""
T6.10 -- Deadline-enforced closed-loop mode: the arm keeps moving during
planning (motion and planning-compute overlap), and the planner forfeits a
step rather than exceeding the mission budget. Reports the gap vs a
paused-clock baseline (today's implicit sense-plan-act behavior: the arm
sits still while the planner computes, so compute time serializes with
motion time instead of hiding inside it).

Uses REAL per-step data: travel_time_s from Phase 3's real T3.3
`kinematics.move_time` (via T6.7's real celf_explore trace, Dijkstra over
the T3.4 roadmap) and compute_time_s from T6.7's real, actually-measured
per-round planning wall-clock (not estimated). Budget = Phase 4 T4.7's own
real `T_TOTAL_S = 120.0` constant (`switching.py`), reused rather than
inventing a new number.

## Concurrency model, stated explicitly

- PAUSED-CLOCK (today's implicit behavior): the arm is stationary while the
  planner computes the next decision, so each step's wall-clock
  contribution is `compute_time_i + travel_time_i` (sequential).
- CLOSED-LOOP (T6.10 fix): planning for step i+1 happens WHILE the arm is
  still executing step i's motion (the classic sense-plan-act -> pipelined
  architecture change), so each step's wall-clock contribution is
  `max(compute_time_i, travel_time_i)` -- whichever is the bottleneck. This
  is a real, standard robotics pipelining assumption, stated here rather
  than silently assumed; it is NOT claiming the planner literally executes
  concurrently with the physical arm controller in this simulated
  environment (no such runtime exists in this repo) -- it is scoring what
  a real pipelined implementation WOULD achieve, using this run's real
  measured per-step costs as the numbers that assumption operates on.
- Deadline enforcement: elapsed wall-clock is checked BEFORE committing to
  a step; if committing would push elapsed past the budget, the planner
  FORFEITS that step (stops the mission there) rather than overrunning.
"""

import os
import time

from yogesh_dev.phase6.common import PHASE4_DATA, PHASE6_OUTPUT, ensure_phase4_importable, load_json

ensure_phase4_importable()

from explore_planner import load_arm_coverage  # noqa: E402
from yogesh_dev.phase6.t67_t68_t69_planning_metrics import ilp_max_coverage  # noqa: E402

T_TOTAL_S = 120.0  # switching.py's own real constant, reused (not re-invented)


def simulate(trace, budget_s, mode):
    """trace: list of {"travel_time_s", "compute_time_s", "cumulative_coverage"}
    in real planner-chosen order. Returns per-step elapsed-time-under-this-
    model + whether/where the deadline forces a forfeit."""
    elapsed = 0.0
    out = []
    forfeited_at = None
    for s in trace:
        if mode == "paused_clock":
            step_cost = s["compute_time_s"] + s["travel_time_s"]
        elif mode == "closed_loop":
            step_cost = max(s["compute_time_s"], s["travel_time_s"])
        else:
            raise ValueError(mode)

        if elapsed + step_cost > budget_s:
            forfeited_at = s["step"]
            break
        elapsed += step_cost
        out.append({"step": s["step"], "elapsed_s": elapsed, "cumulative_coverage": s["cumulative_coverage"]})

    return {"mode": mode, "budget_s": budget_s, "steps_completed": len(out),
            "forfeited_at_step": forfeited_at, "final_elapsed_s": elapsed,
            "final_coverage": out[-1]["cumulative_coverage"] if out else 0, "per_step": out}


def run_t610(t67_report, budget_s=T_TOTAL_S):
    results = {}
    for arm_name, arm_result in t67_report.items():
        trace = [{"step": c["step"], "travel_time_s": None, "compute_time_s": None,
                   "cumulative_coverage": c["coverage_fraction"]} for c in arm_result["curve"]]
        # Reconstruct per-step (not cumulative) travel/compute time from the
        # cumulative curve T6.7 already produced.
        prev_motion, prev_wall = 0.0, 0.0
        for i, c in enumerate(arm_result["curve"]):
            step_motion = c["cumulative_motion_time_s"] - prev_motion
            step_wall = c["cumulative_wallclock_incl_compute_s"] - prev_wall
            step_compute = step_wall - step_motion
            trace[i]["travel_time_s"] = step_motion
            trace[i]["compute_time_s"] = max(step_compute, 0.0)
            trace[i]["cumulative_coverage"] = c["coverage_fraction"]
            prev_motion = c["cumulative_motion_time_s"]
            prev_wall = c["cumulative_wallclock_incl_compute_s"]

        paused = simulate(trace, budget_s, "paused_clock")
        closed = simulate(trace, budget_s, "closed_loop")

        results[arm_name] = {
            "budget_s": budget_s,
            "paused_clock": paused,
            "closed_loop": closed,
            "coverage_gap_closed_loop_minus_paused": closed["final_coverage"] - paused["final_coverage"],
            "steps_gap_closed_loop_minus_paused": closed["steps_completed"] - paused["steps_completed"],
            "elapsed_time_gap_at_full_sequence_s": (
                sum(t["compute_time_s"] + t["travel_time_s"] for t in trace)
                - sum(max(t["compute_time_s"], t["travel_time_s"]) for t in trace)
            ),
        }
    return results


def run_t610_ilp_variant(arm_name="arm_high", budget_s=30.0):
    """A second, real-but-more-expensive-planner scenario: Phase 4/6's own
    CELF-lazy set-coverage compute is negligible (microseconds -- see
    `run_t610`'s CELF-based result), so the closed-loop-vs-paused-clock
    distinction is invisible at that scale. To actually exercise deadline
    enforcement with a non-trivial compute cost, this reruns the SAME
    real per-step travel times but substitutes T6.8's real PuLP+CBC
    max-coverage ILP solve (`ilp_max_coverage`, timed live, not estimated)
    as the per-step "planning compute" -- a real, sometimes-slow computation
    that actually exists in this codebase (unlike CELF's O(1) set-diff)."""
    poses = load_json(os.path.join(PHASE4_DATA, "poses.json"))
    coverage = load_arm_coverage(PHASE4_DATA, poses, arm_name)

    t67_report = load_json(os.path.join(PHASE6_OUTPUT, "t67_t68_t69_report.json"))["T6.7"][arm_name]
    curve = t67_report["curve"]

    trace = []
    prev_motion = 0.0
    for i, c in enumerate(curve):
        k = c["step"]
        t0 = time.perf_counter()
        ilp_max_coverage(coverage, k)
        compute_time_s = time.perf_counter() - t0
        travel_time_s = c["cumulative_motion_time_s"] - prev_motion
        prev_motion = c["cumulative_motion_time_s"]
        trace.append({"step": k, "travel_time_s": travel_time_s, "compute_time_s": compute_time_s,
                       "cumulative_coverage": c["coverage_fraction"]})

    paused = simulate(trace, budget_s, "paused_clock")
    closed = simulate(trace, budget_s, "closed_loop")
    return {
        "arm": arm_name, "budget_s": budget_s, "trace_with_real_ilp_compute_times": trace,
        "paused_clock": paused, "closed_loop": closed,
        "coverage_gap_closed_loop_minus_paused": closed["final_coverage"] - paused["final_coverage"],
        "steps_gap_closed_loop_minus_paused": closed["steps_completed"] - paused["steps_completed"],
    }


def run_all():
    os.makedirs(PHASE6_OUTPUT, exist_ok=True)
    t67_path = os.path.join(PHASE6_OUTPUT, "t67_t68_t69_report.json")
    if not os.path.isfile(t67_path):
        raise RuntimeError("Run t67_t68_t69_planning_metrics first (needs its real per-step trace).")
    t67_report = load_json(t67_path)["T6.7"]
    celf_based = run_t610(t67_report)
    ilp_based = run_t610_ilp_variant()
    return {"celf_based_compute_negligible": celf_based, "ilp_based_compute_nontrivial": ilp_based}


if __name__ == "__main__":
    import json
    out = run_all()
    with open(os.path.join(PHASE6_OUTPUT, "t610_deadline_closed_loop_report.json"), "w") as fh:
        json.dump(out, fh, indent=2, default=str)
    print(json.dumps(out, indent=2, default=str))
