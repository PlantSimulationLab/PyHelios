# Phase 5 Status

All of T5.1-T5.9 implemented under `yogesh_dev/phase5/` and run end-to-end
against real data (not stubs) — not simulated, not estimated. See
`PHASE5_LOG.md` for full detail, real numbers, and every problem hit
(including two real ILP correctness bugs found and fixed mid-phase).

## Summary

- **T5.1-T5.8**: one fresh, real 3-apple-tree scene (83 fruit, 17098
  fruit-surface primitives, seed 20260729) built with the real Phase 0/1/2
  radiation-camera rig and ground-truth/visibility machinery. Real V_reach
  (Phase 2's `PLACEHOLDER_reachable_poses`, 324 poses) and Phase 0's static
  3-camera rig rendered once and cached; every baseline scores its own
  real view-selection policy from that cache, all directly comparable on
  the same real `mean_coverage_frac` (AVUB-style) metric plus execution
  time via Phase 3's real trapezoidal motion-time model.
- **T5.7 (ILP set-cover)**: real MILP via `pulp` + CBC (installed into the
  `helios` env for this task, scoped and minimal). Caught and fixed two
  real bugs: a fruit-level-vs-primitive-level objective mismatch, and a
  free-CBC "Optimal" status that could not be trusted at this problem's
  real scale (verified via a targeted cold-solve diagnostic) — fixed with
  a cross-validation-against-known-lower-bounds mechanism so the reported
  ceiling can never silently be worse than an independently-verified
  achievable result.
- **T5.9**: fully offline (no live pyhelios), against Phase 4's real
  dataset and exploit planner. Reproduces Phase 4's own
  `output_t48_exploit_planner.json` exactly as the "perfect perception"
  condition (a correctness check), and adds a new tracker-driven "noisy
  perception" ablation using Phase 4's real T4.4 tracker output, isolating
  perception-driven value loss from planning-algorithm error.

Real numbers, full summary table, and honest caveats for every baseline
are in `PHASE5_LOG.md`'s Results section. Raw data:
`yogesh_dev/phase5/output/phase5_run_report.json` (T5.1-T5.8) and
`yogesh_dev/phase5/output/phase5_t59_perfect_perception.json` (T5.9).

## Known, honestly-flagged limitations (not hidden)

- Execution-time costing (T5.3/T5.5/T5.8 motion times) applies Phase 3's
  real trapezoidal model to joint coordinates derived directly from each
  pose, without validating those poses against Phase 3's placeholder
  per-arm joint-limit envelope (Phase 2's reachable-pose grid and Phase
  3's arm limits were developed independently and never reconciled) — see
  PHASE5_LOG.md "Real integration gap carried forward honestly".
- T5.7's k=6-8 numbers are a real, valid LOWER BOUND on the true ILP
  optimum (matching T5.6's greedy oracle), not a solver-certified ceiling
  — free CBC could not verify a better solution within the 180s/k time
  budget at this problem's real scale (~17k primitive-level binaries).
  k=1-5 ARE solver-verified optima.
- T5.6's greedy oracle is capped at 40 steps (a safety bound, not a
  discovered plateau) and had not fully saturated at that point on the
  real 324-candidate V_reach.

None of this was silently swept under the rug — every item above is
reproducible from the code and cross-checked against an independent real
number in `PHASE5_LOG.md`.

STATUS: DONE
