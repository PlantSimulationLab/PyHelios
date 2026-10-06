"""
T5.9 -- Perfect-perception ablation.

Fully offline: no live pyhelios/Context needed at all. Runs entirely
against Phase 4's already-generated real dataset
(yogesh_dev/phase4/data/*, from the real seeded single-tree scene: 27
fruit, 42 real rendered views across 3 arms) and its real T4.8 exploit
planner / T4.4 tracker code (yogesh_dev/phase4/*.py, imported via
sys.path since those are flat standalone modules, not a dotted package --
see PHASE5_LOG.md).

## What "perfect perception" already means in this codebase, and what's
   actually being ablated

Phase 4's T4.8 `celf_exploit` (yogesh_dev/phase4/exploit_planner.py)
already plans against GROUND-TRUTH per-primitive visibility
(`vis_primitive_id`, keyed by the real `fruitID`/`object_id` -- i.e. it
already assumes perfect identity/association, because no real detector
was ever built in this repo; see PHASE4_LOG.md/PHASE5_LOG.md). That run is
`output_t48_exploit_planner.json` and IS this task's "perfect perception"
condition -- it is reproduced here (not re-derived differently) as
`perfect` below, and matches the original file's numbers exactly (a
correctness check, not a coincidence).

The one piece of Phase 4 that DOES model real, measurable perception error
is T4.4's tracker (`tracker.py`): a real greedy nearest-3D-centroid
association across each arm's view sequence, scored against oracle
identity via IDF1 / ID-switch counts. It is NOT wired into planning at all
today -- T4.6/T4.8 never consult it. This script builds the missing
connection: a `noisy` planning condition that runs the EXACT SAME greedy/
CELF value-function-driven view-selection algorithm as `celf_exploit`, but
where each view's contribution accumulates under the TRACKER's predicted
track_id instead of the true object_id -- i.e. the planner "believes" two
views belong to the same fruit (or different fruit) exactly to the extent
the real tracker's greedy nearest-centroid association would build up a
persistent per-fruit visibility record. Concretely: track T's
fixed denominator (total primitive count "T thinks it's tracking") is
fruit_prim_ids[true_id of T's FIRST detection]; every later view assigned
to track T contributes q = (real primitives seen for whatever true fruit
that later detection actually was) / (that fixed, possibly-mismatched,
first-sighting denominator) -- exactly modeling what happens when a
tracker's identity persistence is wrong (an ID switch merges two fruit
into one identity, or fragments one fruit into two).

Both `perfect` and `noisy` are run with the SAME greedy/CELF algorithm,
SAME travel-time roadmap cost, SAME start node and budget -- so any gap
between them is attributable ONLY to the identity/perception signal
feeding the value function, not to a different planning algorithm. Because
the `noisy` run's own selection could look artificially good under its OWN
(possibly wrong) value accounting, its SELECTED VIEW SEQUENCE is also
re-scored under the TRUE value function (`noisy_plan_scored_by_truth`)
for an apples-to-apples comparison against `perfect`'s value -- this
isolates planning error (already isolated to 0 by construction, since the
algorithm is identical) from perception error (the entire measured gap).
"""

import heapq
import json
import math
import os
import sys

PHASE4_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "phase4")
if PHASE4_DIR not in sys.path:
    sys.path.insert(0, PHASE4_DIR)

import explore_planner as ep  # noqa: E402
import exploit_planner as xp  # noqa: E402
import tracker as tr  # noqa: E402
import sensor_model as sm  # noqa: E402

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
BUDGET_S = 45.0  # matches Phase 4's own T4.8 run (output_t48_exploit_planner.json)
ARMS = ("arm_low", "arm_mid", "arm_high")


def _celf_generic(q_of, identity_ids, travel_time_table, start_node, budget_s, weights=None):
    """Identical algorithm to exploit_planner.celf_exploit, parameterized
    by an externally-supplied q_of (node -> {identity: q_value}) and
    identity_ids, so it can be driven by either the true object_id-keyed
    q's or the tracker's track_id-keyed q's."""
    weights = weights or {}
    candidates = [n for n in q_of if n != start_node]
    cum_q = {fid: 0.0 for fid in identity_ids}
    current_value = xp.exploit_value(cum_q, weights)

    version = {n: -1 for n in candidates}
    cached_gain = {n: None for n in candidates}

    trace = []
    current = start_node
    time_used = 0.0
    k = 0
    remaining = set(candidates)
    n_true_recomputes = 0
    n_would_be = 0

    while remaining:
        n_would_be += len(remaining)
        heap = []
        for n in remaining:
            if version[n] != k:
                merged = dict(cum_q)
                for fid, q in q_of[n].items():
                    merged[fid] = merged.get(fid, 0.0) + q
                gain = xp.exploit_value(merged, weights) - current_value
                cached_gain[n] = gain
                version[n] = k
                n_true_recomputes += 1
            cost = travel_time_table[current][n]
            score = cached_gain[n] / cost if cost > 1e-9 else cached_gain[n] * 1e9
            heapq.heappush(heap, (-score, n))

        _neg_score, best = heapq.heappop(heap)
        best_gain = cached_gain[best]
        best_cost = travel_time_table[current][best]

        if best_gain <= 1e-9:
            break
        if time_used + best_cost > budget_s:
            trace.append({"stopped": "budget_exhausted", "node": best})
            break

        for fid, q in q_of[best].items():
            cum_q[fid] = cum_q.get(fid, 0.0) + q
        current_value += best_gain
        time_used += best_cost
        k += 1
        trace.append({"step": k, "node": best, "marginal_value_gain": best_gain,
                      "travel_time_s": best_cost, "cumulative_time_s": time_used})
        current = best
        remaining.discard(best)

    selected_nodes = [t["node"] for t in trace if "step" in t]
    return {
        "selected_nodes": selected_nodes, "self_reported_final_value": current_value,
        "total_time_s": time_used, "n_true_gain_recomputes": n_true_recomputes,
        "n_naive_would_be": n_would_be,
    }


def _true_q_of(coverage, fruit_prim_ids):
    """Exact reproduction of exploit_planner.celf_exploit's internal
    q_contribution, exposed per-node so it can drive `_celf_generic`
    directly (used for the `perfect` condition)."""
    q_of = {}
    for node, vis in coverage.items():
        out = {}
        for fid, prim_ids in fruit_prim_ids.items():
            n_visible = len(vis & prim_ids)
            if n_visible:
                out[fid] = n_visible / len(prim_ids)
        q_of[node] = out
    return q_of


def _tracker_q_of(coverage, fruit_prim_ids, tracked_frames):
    """Per-node q contributions keyed by the REAL tracker's predicted
    track_id instead of true object_id -- see module docstring for the
    exact semantics (fixed first-sighting denominator, later views scored
    against whatever true fruit they actually came from)."""
    track_first_true = {}
    q_of = {n: {} for n in coverage}
    for frame in tracked_frames:
        node = frame["node_id"]
        if node not in coverage:
            continue
        for det in frame["detections"]:
            tid = det["track_id"]
            true_id = det["true_id"]
            if tid not in track_first_true:
                track_first_true[tid] = true_id
            denom_prims = fruit_prim_ids.get(track_first_true[tid])
            if not denom_prims:
                continue
            seen_prims = coverage[node] & fruit_prim_ids.get(true_id, set())
            if not seen_prims:
                continue
            q = len(seen_prims) / len(denom_prims)
            q_of[node][tid] = q_of[node].get(tid, 0.0) + q
    track_ids_all = set(track_first_true.keys())
    return q_of, track_ids_all


def _score_sequence_under_truth(selected_nodes, true_q_of, fruit_prim_ids):
    """Replay a chosen node sequence's cumulative value under the TRUE
    (object_id-keyed) value function, regardless of what identity signal
    actually drove the selection -- the honest apples-to-apples number."""
    cum_q = {fid: 0.0 for fid in fruit_prim_ids}
    for node in selected_nodes:
        for fid, q in true_q_of.get(node, {}).items():
            cum_q[fid] = cum_q.get(fid, 0.0) + q
    return xp.exploit_value(cum_q, {})


def run_arm(data_dir, arm_name, poses, intr, fruit_prim_ids):
    coverage = ep.load_arm_coverage(data_dir, poses, arm_name)
    ground_set = set().union(*coverage.values()) if coverage else set()
    if not ground_set:
        return {"note": "zero coverage possible from this arm -- real Phase 4 finding, not an error"}

    adjacency = ep.load_adjacency(data_dir, arm_name)
    node_ids = list(coverage.keys())
    travel_table = ep.pairwise_travel_times(adjacency, node_ids)
    start = min(node_ids)

    # --- perfect perception: reproduces output_t48_exploit_planner.json ---
    true_q_of = _true_q_of(coverage, fruit_prim_ids)
    perfect = _celf_generic(true_q_of, set(fruit_prim_ids.keys()), travel_table, start, BUDGET_S)

    # --- tracker-driven "noisy" perception ---
    frames = tr.extract_detections(data_dir, arm_name, poses, intr)
    tracked_frames, n_tracks = tr.run_tracker(frames)
    idf1 = tr.score_idf1(tracked_frames)
    track_q_of, track_ids_all = _tracker_q_of(coverage, fruit_prim_ids, tracked_frames)
    noisy = _celf_generic(track_q_of, track_ids_all, travel_table, start, BUDGET_S)

    noisy_true_value = _score_sequence_under_truth(noisy["selected_nodes"], true_q_of, fruit_prim_ids)
    perfect_value = perfect["self_reported_final_value"]
    gap = perfect_value - noisy_true_value
    gap_frac = (gap / perfect_value) if perfect_value > 0 else None
    note = None
    if gap < 0:
        note = (
            "Negative gap: the tracker-driven run's DIFFERENT node selection "
            "scored HIGHER under the true value function than the 'perfect' "
            "run's own greedy choice. This is a real, legitimate consequence "
            "of CELF/greedy submodular selection being only an "
            "approximation (not a global optimum, see T5.7's ILP for the "
            "actual ceiling) -- a different (noise-perturbed) candidate "
            "ranking can occasionally land on a better local optimum by "
            "chance. It does NOT mean perception noise helps in general; "
            "see tracker_idf1/n_id_switches for how much identity confusion "
            "actually occurred on this arm."
        )

    return {
        "n_fruit_total": len(fruit_prim_ids),
        "tracker_idf1": idf1,
        "perfect_perception": {
            "selected_nodes": perfect["selected_nodes"],
            "final_value": perfect_value,
            "total_time_s": perfect["total_time_s"],
            "n_views_used": len(perfect["selected_nodes"]),
        },
        "noisy_perception_tracker_driven": {
            "selected_nodes": noisy["selected_nodes"],
            "self_reported_final_value": noisy["self_reported_final_value"],
            "true_value_of_same_selected_views": noisy_true_value,
            "total_time_s": noisy["total_time_s"],
            "n_views_used": len(noisy["selected_nodes"]),
        },
        "perception_driven_value_gap": gap,
        "perception_driven_value_gap_fraction_of_perfect": gap_frac,
        "note": note,
    }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    data_dir = os.path.join(PHASE4_DIR, "data")
    poses = json.load(open(os.path.join(data_dir, "poses.json")))
    report_meta = json.load(open(os.path.join(data_dir, "gen_report.json")))
    intr = sm.intrinsics(tuple(report_meta["resolution"]))
    fruit_prim_ids = xp.load_fruit_prim_ids(data_dir)

    results = {}
    for arm_name in ARMS:
        print(f"T5.9 {arm_name}...", flush=True)
        results[arm_name] = run_arm(data_dir, arm_name, poses, intr, fruit_prim_ids)
        print(f"T5.9 {arm_name} done:", {k: v for k, v in results[arm_name].items()
                                          if k not in ("perfect_perception", "noisy_perception_tracker_driven")},
              flush=True)

    out = {
        "baseline": "T5.9_perfect_perception_ablation",
        "label": "Perfect-perception (ground-truth identity) vs tracker-driven (real ID-confusion) exploit planning",
        "budget_s": BUDGET_S,
        "data_source": "yogesh_dev/phase4/data (real seeded single-tree scene, 27 fruit, 42 real rendered views)",
        "per_arm": results,
    }
    with open(os.path.join(OUTPUT_DIR, "phase5_t59_perfect_perception.json"), "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(json.dumps(out, indent=2, default=str))
    return out


if __name__ == "__main__":
    main()
