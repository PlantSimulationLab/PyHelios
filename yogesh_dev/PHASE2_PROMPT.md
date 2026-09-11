# Task: Implement Phase 2 of the Helios setup plan (visibility ground truth / AVUB)

Unattended headless run (`--dangerously-skip-permissions`), nobody watching interactively.
Follow the constraints below exactly rather than asking.

## Context

Repo: `/home/yogesh/PyHelios`, branch `apple-tree-cameras`. Full plan:
`/home/yogesh/PyHelios/helios_setup_tasks.md` — **only implement Phase 2** (section
"## Phase 2 — Visibility ground truth (AVUB / NVE)", tasks T2.1-T2.6).

**Prior/parallel phases, read before starting:**
- Branch `worktree-phase0-radiation`: `yogesh_dev/phase0/*.py` — camera rig, validated pose
  convention, radiation setup.
- Branch `worktree-phase1-groundtruth`: `yogesh_dev/phase1/*.py` and
  `yogesh_dev/phase1/output/` — `fruit_ground_truth.json` (73 real fruit objects w/ bbox,
  area, primitive UUIDs), per-view semantic/instance label maps (`getPrimitiveDataLabelMap`,
  `getObjectDataLabelMap` on `fruitID`), transforms.json. **This is your main input data.**
- Branch `worktree-phase3-kinematics` **may still be mid-run** (a separate background job is
  building it concurrently right now) — do NOT depend on its final output being ready or
  correct. Where the task doc says a task "needs Phase 3" (T2.3), build against a clearly
  documented **placeholder/synthetic reachable-pose set** instead (see T2.3 below) so this
  phase produces real, testable results now; document exactly what should be swapped in once
  Phase 3's real roadmap exists.

**Known real constraint:** `CollisionDetection` (`castRaysSoA`, `findCollisions`, etc.) is
**not exposed in PyHelios**. The task doc frames T2.1 as needing this for occlusion
determination, but you don't actually need it: Phase 1 already produced real per-pixel
instance label maps (`getObjectDataLabelMap(cam, "fruitID")`) from real renders. Use those:
for a given pose, render (or reuse an existing Phase 1 render if the pose matches), read which
`fruitID` instances/primitives appear in the visible pixels, and sum **real primitive area**
(`context.getPrimitiveArea`) only over primitives confirmed visible that way. This gives a
legitimate area-weighted visibility fraction without analytic ray casting — coarser than true
per-primitive ray tracing (won't resolve sub-primitive partial occlusion), but real and
documented as such. Do not fabricate ray-casting results that don't exist.

Use the `helios` conda env: `/home/yogesh/anaconda3/envs/helios/bin/python`.

## HARD CONSTRAINT

Every file you create or modify must live under `/home/yogesh/PyHelios/yogesh_dev/`. Do not
touch `apple_tree.py`, `apple_tree_cameras.py`, `helios-core/`, `pyhelios/`, or anything with
uncommitted changes already in git status. No `git commit`/`push`/`checkout`/`stash`, no
`sudo`, no installs outside the `helios` env.

## Deliverables (`yogesh_dev/phase2/`)

- **T2.1** — per-fruit visible-fraction `vis_i(v)` for a given pose: area-weighted indicator
  of (unoccluded ∧ front-facing ∧ in-frustum), using the render-based approach above. Weight
  by real primitive area, not pixel count (pixel count only *selects which primitives count as
  visible*, area of those primitives is the actual weight). Cross-check against raw
  `getObjectDataLabelMap` pixel counts per the task doc's own suggested validation — they
  should correlate; report the actual correlation, don't assume it.
- **T2.2** — accumulated visibility over a trial: `v_i_max(t)` as the **union** over primitives
  seen by *any* camera at *any* time in a sequence of poses — not a max over individual views.
  Demonstrate on a real multi-pose sequence (e.g. the existing 3-rig x 3-tree views from
  Phase 0/1) that union-coverage exceeds any single view's coverage.
- **T2.3** — reachable view set 𝒱_reach: since Phase 3's real kinematics/roadmap may not be
  ready, build a **documented placeholder**: a dense grid/sample of camera poses in front of
  each tree within a plausible workspace envelope (reuse Phase 0's camera-rig style
  position/lookat generation as a starting point), clearly labeled
  `PLACEHOLDER_reachable_poses` or similar in code and docs, with a clear docstring on exactly
  what a real T3.4 roadmap output should look like to be substitutable here (same interface).
- **T2.4** — compute AVUB and AVUB^∞ using T2.1 + T2.3: `AVUB_i` = fraction of fruit i's
  surface visible from any pose in the (placeholder) reachable set; `AVUB^∞` using an
  unconstrained free-flying camera sweep (denser/broader placeholder sampling). Report the
  `AVUB / AVUB^∞` ratio. Caveat clearly in the log that these numbers will change once real
  Phase 3 reachability replaces the placeholder.
- **T2.5** — fruit achievability classes: tag each fruit *observable* (`AVUB_i > 0`), *sizeable*
  (`AVUB_i > gamma_size`, pick and document a reasonable gamma), *graspable* (approach cone
  clear — can approximate with a simple geometric cone-vs-neighboring-primitive check if a real
  approach-planner doesn't exist yet, document the approximation).
- **T2.6** — validate the proposal's occlusion-regulation module against AVUB: first check
  whether such a module actually exists anywhere in this repo (search for it). If it doesn't
  exist, **do not fabricate one** — document clearly in the log that T2.6 is blocked on a
  module that doesn't exist yet in this codebase, and skip it (this is a legitimate partial
  outcome, report it honestly in the status file rather than forcing a fake "done").

Run everything against real data (Phase 1's actual 73 fruit objects / real label maps), not
synthetic fruit. If a Phase-3-dependent task produces placeholder-based numbers, say so
explicitly in both the code (docstrings/constants) and `PHASE2_LOG.md` — never present
placeholder-derived numbers as if they were the real thing.

## Logging and completion

Continuously append to `yogesh_dev/PHASE2_LOG.md` (what you did, real numbers, problems hit,
which parts are placeholder-based and why). When finished (or genuinely blocked), write
`yogesh_dev/PHASE2_STATUS.md` whose **last line** is exactly `STATUS: DONE` or
`STATUS: BLOCKED: <reason>` — written last, after everything else. If T2.6 was skipped because
the occlusion-regulation module doesn't exist, the status file should say DONE for T2.1-T2.5
and explicitly call out T2.6 as skipped-with-reason, not blend it into a vague overall status.
