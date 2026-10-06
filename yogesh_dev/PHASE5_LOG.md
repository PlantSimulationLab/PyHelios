# Phase 5 Log — Baselines and oracles

Scope: `helios_setup_tasks.md` Phase 5 (T5.1-T5.9) only. Everything under
`yogesh_dev/phase5/`. Branch: `worktree-phase5-baselines` (this worktree
was reset onto local `apple-tree-cameras` at `5ca80ea`, which already
contains merged Phase 0-4 deliverables — see "Worktree setup" below).

## Worktree setup

`EnterWorktree` defaulted to branching from `origin/master` (the upstream
`PlantSimulationLab/PyHelios` default branch), which does NOT contain
`yogesh_dev/` at all. Verified with `git status`/`git log` that the fresh
worktree had no uncommitted work, then `git reset --hard apple-tree-cameras`
(the local branch, which already has Phase 0-4 merged at `5ca80ea`) to pull
in the real prior-phase code and data. Two gitignored build artifacts also
had to be symlinked in from the main checkout (same pattern every prior
phase worktree used):

- `pyhelios_build/build/{lib,plugins}` -> main checkout's build output
- `helios-core` -> main checkout's submodule checkout

Verified these are read-only build outputs / a submodule checkout, not
tracked sources, and nothing under them is written to by this worktree.

Neither `pulp` nor `scipy` was present in the `helios` conda env (checked
first, per the task brief). Installed `pulp` via pip into the `helios` env
specifically for T5.7's ILP solver (the scoped, minimal install the task
brief explicitly permits) — verified working with CBC as the backend
before using it for real.

## Design: one fresh scene, rendered once, every baseline scores from cache

T5.1-T5.8 all need to be directly comparable, so `yogesh_dev/phase5/common.py`
builds ONE fresh 3-apple-tree scene (same real Phase 0/1/2 radiation-camera
rig, ground-truth export, and per-primitive `vis_primitive_id` visibility
machinery those phases already validated — reused via import, not
reimplemented), renders + caches every candidate pose's real per-primitive
visibility exactly ONCE (the real V_reach: Phase 2's own
`PLACEHOLDER_reachable_poses` grid, 108 poses/tree x 3 trees = 324, per the
task brief's explicit instruction to use it directly rather than
re-deriving reachability; plus Phase 0's static 3-camera rig, 9 poses), and
every T5.x baseline then scores its own view-selection POLICY purely from
that cached data — no baseline re-renders. This is what makes the eight
baselines' numbers apples-to-apples: same scene, same fruit, same
primitive ids, same render settings.

Seed `20260729` (same one Phase 2 used) — this scene realization came out
to **83 fruit, 17098 fruit-surface primitives** across the 3 trees,
IDENTICAL to Phase 2's own run's counts. That's worth noting: Phase 2's log
observed fruit count varying run-to-run (73 in Phase 1 vs 83 in Phase 2)
and attributed it to "stochastic growth, unseeded upstream" — but this
Phase 5 run, using the exact same seed AND the exact same code path
(`build_three_tree_scene`), reproduced Phase 2's 83-fruit count exactly.
So `context.seedRandomGenerator(SEED)` called before `PlantArchitecture`
construction does appear to make growth fully deterministic across
independent processes after all; Phase 1 (73 fruit) simply never called it.

### Real integration gap carried forward honestly, not hidden

Phase 3's `motion_time.move_time` (trapezoidal per-axis execution time) is
reused for every baseline's execution-time-cost number, but WITHOUT binding
poses to one of Phase 3's three placeholder `ArmConfig`s. Phase 2's
reachable-pose grid (rail/height/depth relative to each tree's own bbox)
and Phase 3's arm z-bands/pan/tilt limits (`default_arm_configs()`, sized
against the whole 3-tree row's absolute world coordinates) were developed
independently and were never reconciled — forcing every V_reach pose
through Phase 3's IK+limit check would silently reject most of the grid.
`common.pose_to_joint_state` instead derives `(x, y, z, pan, tilt)`
directly from each pose's `(eye, lookat)` via the same closed-form math
`kinematics.inverse_kinematics` uses, arm-agnostically, and
`move_time`/the trapezoidal per-axis model itself (which doesn't consult
joint limits at all) is applied unchanged. Execution-time numbers below are
real applications of Phase 3's real model; they are not validated against
Phase 3's placeholder joint-limit envelope. Flagging this explicitly rather
than silently picking an arm per pose.

## Per-baseline notes

**T5.1 (single fixed camera):** the "level" rig pose (Phase 0's
`camera_position_for_tree`) on the middle tree (x=1.5) — the natural single
static camera for a row of 3 trees. Absolute floor as expected.

**T5.2 (static 3-camera rig):** Phase 0's original above/level/below rig,
one set per tree, 9 real rendered poses, zero motion time by construction
(rig is simply always in position). Labeled explicitly in its own output
as "the realistic commercial alternative" per the task brief.

**T5.3 (boustrophedon):** a genuine 3D lawnmower serpentine over the SAME
V_reach grid (not a separately-invented raster) — alternates rail direction
each height row and height direction each depth level, matching
`placeholder_reachable_poses`' own (height-major, depth, rail) generation
order. Trees are visited in sequence (tree 0 raster to completion, then
tree 1, then tree 2) rather than interleaved — a real single-rail
lawnmower could equally interleave trees; visiting one tree's raster to
completion before sliding to the next is the simpler, still-realistic
choice made here.

**T5.4 (random reachable):** k in {1,2,4,8}, 200 trials/k, mean +/- std
reported (not a single lucky/unlucky draw, per the task brief).

**T5.5 (nearest-frontier + distance advantage):** deliberately the
"five lines" the task brief calls for — raw newly-covered PRIMITIVE COUNT
(not the fruit-area-weighted AVUB value T5.6's oracle uses) divided by
straight-line Euclidean distance (not Phase 3's real execution-time cost)
— a cheaper, simpler heuristic than T5.6's oracle by construction, greedily
chasing whichever unvisited candidate has the best raw-coverage-per-unit-
distance until no candidate offers new coverage.

**T5.6 (greedy oracle):** brute-force full re-evaluation of every
remaining V_reach candidate every round (no CELF laziness — this IS the
oracle other planners' CELF implementations approximate), scored on the
real area-weighted AVUB-style metric. Capped at 40 steps as a safety bound;
see results below for whether it actually saturated (marginal gain <= eps)
within that cap on the real 324-candidate V_reach.

**T5.7 (ILP set-cover optimum):** real MILP via `pulp` + CBC. Ground
elements are individual fruit-SURFACE PRIMITIVES (not whole fruit objects),
each weighted by `area_p / total_area_of_its_own_fruit`, so the ILP's
linear objective is EXACTLY `sum_i frac_i` — i.e. maximizing it is
identical to maximizing `mean_coverage_frac` (the same real metric every
other baseline is scored on), not a solver-internal proxy. Solved for
k in {1..8}.

This baseline took two real bugs, found and fixed during this phase, not
a design done right the first time:

1. *Fruit-level vs primitive-level ground elements.* An earlier version
   used fruit-level binary z_i ("is fruit i covered at all"), weighted by
   whole-fruit area — a perfectly valid set-cover ILP, but optimizing a
   DIFFERENT question than the one being reported. On synthetic
   smoke-test data it produced a k=2 "ceiling" (0.219) scoring BELOW the
   T5.6 greedy oracle's own k=2 result (0.229) — a contradiction for
   something billed as "the true ceiling". Moving to primitive-level
   elements fixed this (verified ILP >= greedy at every k on synthetic
   data immediately after).

2. *CBC's own "Optimal" status cannot be trusted at this problem's real
   scale.* On the real 324-candidate/17098-primitive problem, the FIRST
   full live run (with a 120s-per-k cap) reported CBC status "Not Solved"
   at k=6 (0 views selected) and, after a warm-start-based retry fix,
   reported "Optimal" at k=6/7/8 with values (0.353, 0.366, 0.379) that
   scored BELOW T5.6's real, independently-computed greedy oracle at the
   same k (0.358, 0.378, 0.392) — again mathematically impossible for a
   genuine optimum (greedy's result is always a valid feasible lower
   bound). A targeted diagnostic (rebuilding the real scene, re-rendering
   V_reach, solving k=6 COLD with no warm start and a 600s time limit —
   5x the original) reproduced the identical false "Optimal" claim,
   proving this wasn't a warm-start artifact but a genuine pitfall of free
   CBC + pulp's status parsing on a MIP this size within any practical
   time budget. **Fix:** every ILP solve (single attempt, 180s cap, no
   warm start) is now cross-validated against two independent real lower
   bounds — T5.6's own greedy-oracle selection at the same k, and the
   previous (k-1)'s accepted selection (monotonicity: `sum_v y_v <= k`
   trivially accepts a smaller selection, so coverage can never decrease
   in k). Whichever of {ILP's solution, greedy's solution, previous k's
   solution} scores highest under the real ground-truth metric is what
   gets reported, honestly labeled via `selection_source` per k — so a
   mislabeled "Optimal" can never silently ship a worse-than-known-
   achievable number. On the final real run: k=1-5 accepted the ILP's own
   (verified-better-than-greedy) solution directly; k=6-8 fell back to
   T5.6's greedy-oracle selection (ILP could not find/verify anything
   better within the 180s/k budget at this scale) — see Results for exact
   per-k provenance. This means k=6-8's reported numbers are a REAL,
   valid lower bound on the true optimum (not necessarily equal to it) —
   stated honestly rather than claimed as a proven ceiling.

**T5.8 (all-reachable fusion):** union over literally all 324 V_reach
poses — this is Phase 2's own AVUB computation, re-derived on this run's
fresh scene (not reused numerically from Phase 2's own run, since fruit
identity/primitive ids are process-local) so it's on the same footing as
every other T5.x number here.

**T5.9 (perfect-perception ablation):** fully offline, no live pyhelios —
runs entirely against Phase 4's already-generated dataset
(`yogesh_dev/phase4/data/`, 27 fruit, 42 real rendered views, 3 arms) and
Phase 4's own `exploit_planner.py`/`tracker.py` code (imported via
`sys.path`, since those are flat standalone modules). Key finding on
inspection: Phase 4's T4.8 exploit planner ALREADY plans against
ground-truth per-primitive visibility keyed by true `fruitID` (no real
detector was ever built in this repo) — so it already IS the "perfect
perception" condition, and reproducing it here via a from-scratch
`_celf_generic` (parameterized version of `celf_exploit`'s algorithm) is
also a correctness check: it must exactly match `output_t48_exploit_planner.json`'s
numbers, and it does (see Results). The actual ablation built here is a
NEW "noisy perception" condition: the same identical greedy/CELF
algorithm, same travel-time roadmap costs, same start/budget, but driven
by the real T4.4 tracker's predicted `track_id` (subject to real
ID-switch/gating error, scored by IDF1) instead of true `fruitID` — so any
value gap between the two is attributable ONLY to identity/perception
confusion, not to a different planning algorithm. `arm_low` reproduces
Phase 4's own "zero coverage possible" finding (no fruit ever visible from
that arm's z-band in this dataset) — not a Phase 5 regression.

## Timing / process notes

Real live pyhelios pass: 324+9 pose renders (batched 3/call via
`runBand()`), each `runBand()` call dominated by the fixed scene-wide solve
cost Phase 0 already measured (~0.6-1.0s) — full V_reach render took 73.5s,
static rig + single-fixed took 2.1s. T5.7's ILP (up to 8 k-values, ~17098
primitive-level binary variables + 324 view binaries each, 180s cap/k) was
the slowest step. Full T5.1-T5.8 pipeline: **1353s (~22.6 min)** wall clock
end to end (scene build + render + all 8 baselines), across 3 live-pyhelios
attempts total (2 discarded after catching real T5.7 bugs — see above).

## Results

Real scene this run: **83 fruit, 17098 fruit-surface primitives, 3 trees**
(seed 20260729). `mean_coverage_frac` = area-weighted fraction of fruit
surface visible (union over the baseline's own chosen views), averaged
over all 83 fruit — the same real metric (`common.coverage_summary`,
built on Phase 2's `vis_i(v)`/AVUB machinery) every baseline below is
scored on, so these are directly comparable.

| Baseline | Views used | Coverage (mean_coverage_frac) | Fruit observed at all | Motion time (s) |
|---|---|---|---|---|
| T5.1 Single fixed camera (floor) | 1 | 0.1147 | 82/83 (98.8%) | 0.0 |
| T5.2 Static 3-camera rig (commercial alt.) | 9 | 0.3240 | 83/83 (100%) | 0.0 |
| T5.3 Boustrophedon raster (full V_reach) | 324 | 0.5964 | 83/83 (100%) | 540.3 |
| T5.4 Random reachable, k=8 (mean±std, 200 trials) | 8 | 0.2964 ± 0.0243 | 99.8% ± 1.2% | 60.3 ± 7.8 |
| T5.5 Nearest-frontier + distance advantage | 240 | 0.5964 | 83/83 (100%) | 556.7 |
| T5.6 Greedy oracle, k=8 (of 40-step run, not saturated) | 8 (of 40) | 0.3923 (0.5384 @ 40) | 100% | — |
| T5.7 ILP set-cover ceiling, k=8 | 8 | 0.3923 (real lower bound, see caveat) | 100% | — |
| T5.8 All-reachable fusion (all of V_reach) | 324 | 0.5964 | 83/83 (100%) | 749.8 (grid order) |

**T5.6 / T5.7 full k=1..8 curve** (greedy oracle vs. ILP ceiling — identical
at every k in this run, since the ILP could only beat/verify greedy at
k=1-5 and fell back to greedy's own real result at k=6-8 within the 180s/k
budget; see the T5.7 note above for why that's an honest lower bound, not
a proven ceiling, at k=6-8):

| k | Greedy oracle (T5.6) | ILP (T5.7) | T5.7 source |
|---|---|---|---|
| 1 | 0.1463 | 0.1463 | ilp |
| 2 | 0.2151 | 0.2151 | ilp |
| 3 | 0.2752 | **0.2764** | ilp |
| 4 | 0.3102 | **0.3109** | ilp |
| 5 | 0.3353 | **0.3371** | ilp |
| 6 | 0.3585 | 0.3585 | greedy_oracle_at_k (ILP: "Not Solved") |
| 7 | 0.3780 | 0.3780 | greedy_oracle_at_k (ILP found 0.3512, below greedy) |
| 8 | 0.3923 | 0.3923 | greedy_oracle_at_k (ILP found 0.3674, below greedy) |

Sanity checks that passed on the final run (see `run_t57`/report JSON):
monotonically non-decreasing in k, and ILP >= greedy at every k, by
construction of the cross-validation fallback.

Note T5.3/T5.5/T5.8 all converge to the identical 0.5964 — expected: all
three eventually union over the same achievable-from-V_reach primitive
set (T5.3 and T5.8 visit literally all 324 poses; T5.5 stops at 240 once
no remaining candidate offers any new coverage, having already reached the
same saturation point). T5.6's own 40-step (not fully saturated) run
reaches 0.5384, still below that ceiling — it would keep climbing toward
~0.596 with more steps, capped here at 40 as a safety bound, not a
discovered plateau (`"saturated": false`).

**T5.9 (offline, Phase 4 dataset, 27 fruit / 3 arms, budget=45s):**

| Arm | Perfect perception (T4.8 reproduction) | Tracker-driven ("noisy") true value | Gap | Tracker IDF1 / ID switches |
|---|---|---|---|---|
| arm_low | N/A — zero coverage possible (real Phase 4 finding) | — | — | — |
| arm_mid | 2.5490 (4 views, 44.2s) | 2.5490 (identical selection) | 0.0 | 0.9375 / 1 switch |
| arm_high | 8.2435 (6 views, 32.0s) | 9.1267 (different 6-view selection) | **-0.883** (noisy scored HIGHER) | 0.9067 / 5 switches |

`perfect_perception`'s numbers exactly reproduce Phase 4's own
`output_t48_exploit_planner.json` (2.5489702566440626 / 44.20738067567971s
for arm_mid; 8.243543962553415 / 32.01606277353565s for arm_high) — a
correctness check on the from-scratch `_celf_generic` reimplementation,
not a coincidence. arm_high's negative gap is a real, legitimate
consequence of greedy/CELF submodular selection being only a
(1-1/e)-approximation, not a global optimum (see T5.7 above for what the
actual ceiling looks like) — a different, noise-perturbed candidate
ranking can occasionally land on a better local optimum by chance; it does
NOT mean perception noise helps in general (see the `note` field in
`output/phase5_t59_perfect_perception.json` for the full honest caveat).

All raw numbers: `yogesh_dev/phase5/output/phase5_run_report.json` (T5.1-
T5.8) and `yogesh_dev/phase5/output/phase5_t59_perfect_perception.json`
(T5.9).
