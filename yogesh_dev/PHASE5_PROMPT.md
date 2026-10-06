# Task: Implement Phase 5 of the Helios setup plan (baselines and oracles)

Unattended headless run (`--dangerously-skip-permissions`), nobody watching interactively.
Follow the constraints below exactly rather than asking.

## Context

Repo: `/home/yogesh/PyHelios`, branch `apple-tree-cameras`. Full plan:
`/home/yogesh/PyHelios/helios_setup_tasks.md` — **only implement Phase 5** (section
"## Phase 5 — Baselines and oracles", tasks T5.1-T5.9). All nine are pure Python, no known
blockers (unlike every phase before this one) — this phase exists to give the eventual real
planner something honest to be compared against, so **every baseline must run against real
data and produce real, reportable numbers**, not stubs.

**Prior phases already produced working code and real data — read before starting.** All are
now merged into `apple-tree-cameras` under `yogesh_dev/` (already pushed, no need to check
out other worktree branches this time):
- `yogesh_dev/phase0/` — camera rig, validated pose convention.
- `yogesh_dev/phase1/` — ground truth export, real EXR depth, label maps, `transforms.json`.
- `yogesh_dev/phase2/` — `visibility.py` (per-primitive `vis_i(v)`), `avub.py`,
  `reachable_poses.py` (`PLACEHOLDER_reachable_poses` — this IS your 𝒱_reach / denominator
  of Π for T5.4/T5.6/T5.7/T5.8, use it directly rather than re-deriving reachability).
- `yogesh_dev/phase3/` — `kinematics.py` (FK/IK), `roadmap.py` (k-NN roadmap, placeholder
  collision), `motion_time.py` (execution-time weights).
- `yogesh_dev/phase4/` — `occupancy_map.py`, `explore_planner.py`, `exploit_planner.py`,
  `information_gain.py`, `tracker.py`. T5.9's "the planner" and T5.6's "ground truth" both
  refer to this phase's real fruit-visibility/tracking machinery, not something to rebuild.

Use the `helios` conda env: `/home/yogesh/anaconda3/envs/helios/bin/python`.

## HARD CONSTRAINT

Every file you create or modify must live under `/home/yogesh/PyHelios/yogesh_dev/`. Do not
touch `apple_tree.py`, `apple_tree_cameras.py`, `helios-core/`, `pyhelios/`, or anything with
uncommitted changes already in git status. No `git commit`/`push`/`checkout`/`stash`, no
`sudo`, no installs outside the `helios` env.

## Deliverables (`yogesh_dev/phase5/`)

Implement each baseline as a real, runnable policy that produces a real view/pose sequence
and a real coverage/AVUB score against Phase 2's ground truth, so they're directly comparable:

- **T5.1** — single fixed camera, one view. The absolute floor.
- **T5.2** — static 3-camera rig, no arm motion (Phase 0's original rig position). "The
  realistic commercial alternative" — label it as such in the report.
- **T5.3** — boustrophedon (back-and-forth) raster over the 3 linear axes, gimbal fixed or
  simply forward-facing. The engineering-practical competitor the task doc says is "absent
  from the entire NBV literature" — worth getting right, not just checked off.
- **T5.4** — random reachable views, sampled from Phase 2's `PLACEHOLDER_reachable_poses`.
  This is the denominator of the planning score Π mentioned in the design doc — run enough
  random trials to report a stable mean +/- std, not a single lucky/unlucky draw.
- **T5.5** — nearest-frontier + Ericson "distance advantage" heuristic. Task doc says this is
  "five lines" — keep it that simple, but actually run it, don't just describe it.
- **T5.6** — greedy oracle: at each step, evaluate every candidate in 𝒱_reach against ground
  truth (Phase 2's real AVUB/vis_i), pick the actual best. This is the numerator of Π — it
  needs to be a real greedy search over real candidates, not an approximation.
- **T5.7** — offline ILP set-cover optimum for k <= 8 views. Use a real ILP solver if one is
  available in the `helios` env (check first — e.g. `pulp`, `scipy.optimize.milp`); if none is
  available, install `pulp` via pip into the `helios` env specifically for this (that's an
  acceptable, minimal, scoped install). This is "the true ceiling" — must be an actual optimum,
  not a greedy approximation mislabeled as ILP.
- **T5.8** — all-reachable-views fusion: union coverage using literally every pose in
  `PLACEHOLDER_reachable_poses` (the sensor + workspace ceiling). Compare directly against
  T5.7's smaller-k ceiling to show the gap between "unlimited views" and "k-view optimum."
- **T5.9** — perfect-perception ablation: feed ground-truth fruit detections (from Phase 1/2,
  not a real detector) into Phase 4's exploit planner, and compare against Phase 4's original
  run to isolate how much of any performance gap is planning error vs. perception error.

For every baseline, report: coverage/AVUB achieved, number of views used, and (where
meaningful) execution-time cost using Phase 3's real motion-time model — so they're comparable
on more than one axis, matching the design doc's framing (§7's Π, Phase 6's discovery-curve
metrics).

## Logging and completion

Continuously append to `yogesh_dev/PHASE5_LOG.md` (what you did, real numbers for every
baseline in one place — a summary table is ideal — problems hit). When finished (or genuinely
blocked on a specific baseline), write `yogesh_dev/PHASE5_STATUS.md` whose **last line** is
exactly `STATUS: DONE` or `STATUS: BLOCKED: <reason>` — written last, after everything else.
