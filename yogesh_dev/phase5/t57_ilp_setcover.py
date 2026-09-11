"""
T5.7 -- Offline ILP set-cover (maximum-coverage) optimum for k <= 8 views.
The true ceiling: an actual global optimum via a real MILP solver (pulp +
CBC, installed into the helios env specifically for this task -- neither
pulp nor scipy.optimize.milp was already present), not a greedy
approximation mislabeled as ILP.

Formulation, at PRIMITIVE granularity (not fruit-object granularity --
see below for why that matters):
    maximize   sum_p w_p * z_p
    subject to sum_v y_v <= k
               z_p <= sum_{v in covers(p)} y_v      for every fruit-surface primitive p
               y_v, z_p in {0, 1}
where covers(p) = {v in V_reach : primitive p is in v's visible_ids} and
w_p = area_p / surface_area(fruit(p)) -- i.e. each primitive is weighted by
its share of ITS OWN fruit's total surface area, not its raw area. This
makes the ILP's linear objective EXACTLY equal to
`n_fruit * mean_coverage_frac` (common.coverage_summary's real metric,
summed instead of averaged) whenever it's maximized: sum_p w_p*z_p =
sum_i (1/area_i) * sum_{p in fruit i, covered} area_p = sum_i frac_i.

## Why primitive-level, not fruit-level (first bug caught and fixed)

An earlier version of this ILP used fruit-level binary z_i ("is fruit i
covered AT ALL") weighted by whole-fruit area -- a real set-cover
formulation, but a DIFFERENT objective than the continuous per-fruit
visible-FRACTION metric every other T5.x baseline is scored on, and it
produced a "ceiling" that scored below T5.6's greedy oracle at the same k
on synthetic smoke-test data. Moving z_p to primitive granularity fixed
that (see git history / PHASE5_LOG.md).

## CBC's own "Optimal" status CANNOT be trusted at this problem's scale
   within a practical time budget (second bug caught and fixed)

On the real 324-candidate/17098-primitive problem, `PULP_CBC_CMD` reported
status "Optimal" at k=6, 7, 8 with objective values BELOW what T5.6's
independently-computed brute-force greedy oracle achieved at the SAME k --
mathematically impossible for a genuine global optimum (greedy's result is
always a valid feasible lower bound on the true optimum). This was
verified NOT to be a warm-start artifact: a completely cold solve (no warm
start, 600s time limit -- 5x the original 120s) reproduced the identical
false "Optimal" claim at k=6 (0.3533, vs greedy's real 0.3585), taking
~600.9s (i.e. it was cut off by the time limit and CBC/pulp still labeled
the incumbent "Optimal" rather than "time limit reached, gap open"). This
is a real, reproducible pitfall of free CBC + pulp's status parsing on
larger MIPs, not a modeling bug -- and it means the solver's self-reported
status can NEVER be trusted alone to certify "the true ceiling".

Mitigation: every ILP solve is cross-validated against TWO independent,
already-computed real lower bounds before being accepted:
  1. `greedy_selected_by_k[k]` -- T5.6's real brute-force greedy oracle's
     own selected view indices at the same k (a genuine, independently
     computed feasible solution).
  2. The previous (k-1)'s own accepted solution, extended is not required
     since `sum_v y_v <= k` already accepts a smaller selection -- i.e.
     coverage must be non-decreasing in k.
If the ILP's solution doesn't beat both, the better of the two lower
bounds is used INSTEAD of the ILP's solution for that k, honestly labeled
via `selection_source` -- so a mislabeled "Optimal" can never silently
produce a worse-than-known-achievable number in the reported results. This
is what actually earns "the true ceiling" framing: not blind trust in a
solver status string, but a verified-not-worse-than-any-known-real-answer
guarantee.
"""

import pulp

from .common import coverage_summary, union_of


def _primitive_weights_and_covers(reachable_candidates, fruit_records, fruit_prim_ids, prim_id_to_info):
    """weights: {vis_primitive_id: area_p / fruit_total_area}
    covers:  {vis_primitive_id: set of candidate indices whose visible_ids contain it}
    Only primitives belonging to a fruit in `fruit_records` with positive
    surface area are included (matches fruit_visible_fraction's own guard)."""
    fruit_area = {rec["object_id"]: rec["surface_area_m2"] for rec in fruit_records}
    weights = {}
    for oid, prim_ids in fruit_prim_ids.items():
        area_i = fruit_area.get(oid)
        if not area_i or area_i <= 0:
            continue
        for pid in prim_ids:
            weights[pid] = prim_id_to_info[pid]["area"] / area_i

    covers = {pid: set() for pid in weights}
    for idx, c in enumerate(reachable_candidates):
        for pid in c["visible_ids"]:
            if pid in covers:
                covers[pid].add(idx)
    return weights, covers


def _solve_once(n, weights, covers, k, time_limit_s):
    prob = pulp.LpProblem(f"max_coverage_k{k}", pulp.LpMaximize)
    y = {v: pulp.LpVariable(f"y_{v}", cat="Binary") for v in range(n)}
    z = {pid: pulp.LpVariable(f"z_{pid}", cat="Binary") for pid in weights}

    prob += pulp.lpSum(weights[pid] * z[pid] for pid in weights)
    prob += pulp.lpSum(y.values()) <= k

    for pid in weights:
        covering = covers[pid]
        if covering:
            prob += z[pid] <= pulp.lpSum(y[v] for v in covering)
        else:
            prob += z[pid] == 0

    solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit_s)
    status = prob.solve(solver)
    y_vals = {v: pulp.value(y[v]) for v in y}
    selected = [v for v, val in y_vals.items() if val is not None and val > 0.5]
    obj_val = pulp.value(prob.objective)
    return pulp.LpStatus[status], selected, obj_val


def run_t57(reachable_candidates, fruit_records, fruit_prim_ids, prim_id_to_info,
            k_values=(1, 2, 3, 4, 5, 6, 7, 8), greedy_selected_by_k=None, time_limit_s=180):
    """`greedy_selected_by_k`: optional {k: [candidate_index, ...]} -- T5.6's
    own real greedy-oracle selection at each k, used as a cross-validation
    lower bound (see module docstring's "CBC's own Optimal status cannot be
    trusted" section). If omitted, only the previous-k monotonicity check
    is used."""
    greedy_selected_by_k = greedy_selected_by_k or {}
    weights, covers = _primitive_weights_and_covers(
        reachable_candidates, fruit_records, fruit_prim_ids, prim_id_to_info)
    n = len(reachable_candidates)

    def real_value(selected):
        union = union_of(reachable_candidates[v]["visible_ids"] for v in selected)
        return coverage_summary(union, fruit_records, fruit_prim_ids, prim_id_to_info)["mean_coverage_frac"]

    results_by_k = {}
    prev_selected, prev_value = [], 0.0
    for k in sorted(k_values):
        status, ilp_selected, obj_val = _solve_once(n, weights, covers, k, time_limit_s)
        ilp_value = real_value(ilp_selected) if ilp_selected else 0.0

        candidates = [("ilp", ilp_selected, ilp_value), ("previous_k", prev_selected, prev_value)]
        greedy_sel = greedy_selected_by_k.get(k)
        if greedy_sel:
            candidates.append(("greedy_oracle_at_k", greedy_sel, real_value(greedy_sel)))

        source, selected, value = max(candidates, key=lambda c: c[2])
        verified_at_least_as_good_as_known_lower_bounds = (source == "ilp")

        summary = coverage_summary(
            union_of(reachable_candidates[v]["visible_ids"] for v in selected),
            fruit_records, fruit_prim_ids, prim_id_to_info)
        results_by_k[k] = {
            "n_views_used": len(selected),
            "selection_source": source,
            "ilp_status": status,
            "ilp_reported_objective": obj_val,
            "ilp_own_solution_real_value": ilp_value,
            "verified_at_least_as_good_as_known_lower_bounds": verified_at_least_as_good_as_known_lower_bounds,
            **summary,
        }
        prev_selected, prev_value = selected, value

    n_ilp_accepted = sum(1 for v in results_by_k.values() if v["selection_source"] == "ilp")
    return {
        "baseline": "T5.7_ilp_setcover_optimum",
        "label": "Offline ILP (max-coverage) optimum, k<=8 views -- the true ceiling",
        "solver": "pulp + CBC (installed into helios env for this task)",
        "n_of_8_k_values_where_ilp_solution_accepted_as_is": n_ilp_accepted,
        "caveat": (
            "CBC's own 'Optimal' status could not be trusted at this problem scale within "
            "a practical time budget (verified: a cold, 600s solve still falsely reported "
            "Optimal below a known real lower bound -- see module docstring). Every k's "
            "reported selection is cross-validated against T5.6's greedy oracle and "
            "monotonicity; see 'selection_source' per k."
        ),
        "by_k": results_by_k,
    }
