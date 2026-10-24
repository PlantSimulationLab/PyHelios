# Task: Implement Phase 3 of the Helios setup plan (kinematics + reachability roadmap)

Unattended headless run (`--dangerously-skip-permissions`), nobody watching interactively.
Follow the constraints below exactly rather than asking.

## Context

Repo: `/home/yogesh/PyHelios`, branch `apple-tree-cameras`. Full plan:
`/home/yogesh/PyHelios/helios_setup_tasks.md` — **only implement Phase 3** (section
"## Phase 3 — Kinematics and the reachability roadmap", tasks T3.1-T3.5).

Helios/PyHelios has **zero** kinematics support (no FK/IK/Jacobians) — this is genuinely
yours to write from scratch, not something to look up in the library.

**Prior phases already produced working code, read it before starting:**
- Branch `worktree-phase0-radiation` (or `git show worktree-phase0-radiation:yogesh_dev/phase0/<file>`):
  `canopy.py`, `radiation_setup.py`, `radiation_cameras.py` — camera rig + validated pose convention.
- Branch `worktree-phase1-groundtruth`: `phase1/*.py` — ground truth export, `output/fruit_ground_truth.json`
  (73 real fruit objects w/ bounding boxes across 3 trees — useful as realistic geometry bounds for
  reachability/workspace design).

**Known real constraint from Phase 0/2 planning:** `CollisionDetection` (`castRaysSoA`,
`findCollisions`, `findCollisionsWithinDistance`, `buildBVH`) is **not exposed in PyHelios** —
explicitly excluded per `pyhelios/config/plugin_metadata.py`. T3.4 and T3.5 in the task doc
assume this exists. It doesn't yet (Phase 0 recommended building it as T0.6, not yet done).
**Do not fabricate or fake collision results as if this capability exists.**

Use the `helios` conda env: `/home/yogesh/anaconda3/envs/helios/bin/python`.

## HARD CONSTRAINT

Every file you create or modify must live under `/home/yogesh/PyHelios/yogesh_dev/`. Do not
touch `apple_tree.py`, `apple_tree_cameras.py`, `helios-core/`, `pyhelios/`, or anything with
uncommitted changes already in git status. No `git commit`/`push`/`checkout`/`stash`, no
`sudo`, no installs outside the `helios` env.

## Deliverables (`yogesh_dev/phase3/`)

- **T3.1** — 5-DOF forward kinematics: 3 prismatic (left-right, up-down, in-out) + pan + tilt
  → camera pose (position + look direction). Hand-rolled, no external kinematics library.
  Include joint limits and a documented per-arm vertical band (pick reasonable numbers for a
  3-arm workcell spanning a tree row, document the assumption clearly since there's no real
  hardware spec available — this is a placeholder to revisit against actual hardware later).
- **T3.2** — closed-form inverse kinematics: solve linear axes for camera position, pan/tilt
  for look direction, given the FK from T3.1. No iterative solver. Verify FK(IK(pose)) round-trips
  to the original pose within numerical tolerance — actually run this check, don't just assert it
  works.
- **T3.3** — execution-time model: trapezoidal velocity profile per axis. Since no real hardware
  numbers are available, pick documented, clearly-labeled placeholder max velocity/acceleration
  values for the 3 linear stages and the gimbal (with the cost asymmetry between them — gimbal
  should be much faster/cheaper than linear stages, that asymmetry is structurally important per
  the task doc, not just cosmetic). Flag this clearly as needing real hardware numbers eventually.
- **T3.4** — build the roadmap: discretize the reachable 5-DOF space per arm (with IK cached),
  build a k-NN graph in joint space weighted by real execution time from T3.3, so planning
  becomes graph search. **Collision rejection is blocked by the missing `CollisionDetection`
  binding** — implement the roadmap-building pipeline with a clearly-named, clearly-documented
  placeholder collision check (e.g., a simple bounding-box/geometric approximation using
  `Context.getDomainBoundingBox` against the canopy extent from `fruit_ground_truth.json`,
  explicitly NOT real per-primitive ray-traced collision), so the graph-search machinery is
  real and testable, but do not claim it does true collision-checked reachability. Document
  precisely what swapping in real `findCollisions`/`castRaysSoA` later would change.
- **T3.5** — arm/workcell collision geometry: add arm link representations (boxes/tubes) as
  Helios geometry in the Context, and enforce non-overlapping vertical bands per arm so
  arm-arm collision is structurally impossible by construction (this part doesn't need the
  missing binding — it's a geometric constraint on the T3.1 workspace design, verify it with a
  direct interval-overlap check, not `findCollisions`). Document that arm-vs-canopy collision
  checking itself still needs T0.6.

Run FK/IK/roadmap-building for real against realistic geometry bounds (from Phase 1's
`fruit_ground_truth.json` / Phase 0's canopy). Prefer an actual runnable demo script over just
class definitions.

## Logging and completion

Continuously append to `yogesh_dev/PHASE3_LOG.md` (what you did, real numbers, problems hit,
and — important — a clear list of exactly what remains blocked on T0.6 and why). When finished
(or genuinely blocked), write `yogesh_dev/PHASE3_STATUS.md` whose **last line** is exactly
`STATUS: DONE` or `STATUS: BLOCKED: <reason>` — written last, after everything else.
