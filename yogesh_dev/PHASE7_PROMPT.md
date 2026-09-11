# Task: Implement Phase 7 of the Helios setup plan (foundation model diagnostics, D1-D6)

Unattended headless run (`--dangerously-skip-permissions`), nobody watching interactively.
Follow the constraints below exactly rather than asking.

## Context

Repo: `/home/yogesh/PyHelios`, branch `apple-tree-cameras`. Full plan:
`/home/yogesh/PyHelios/helios_setup_tasks.md` — **only implement Phase 7** (section
"## Phase 7 — Foundation model diagnostics (D1-D6)", tasks T7.1-T7.7).

Per the task doc, this phase **only needs Phase 0 + Phase 1**, both already done and merged
into this branch under `yogesh_dev/phase0/` and `yogesh_dev/phase1/` (camera rig, pose
convention, ground truth, real EXR depth, label maps, `transforms.json`). Framed in the task
doc as "the cheapest self-contained paper in the plan."

**Real-world constraint you must check for yourself, don't assume**: T7.2/T7.3 reference
external foundation models (MapAnything, DA3, pi-cubed, VGGT) as anchors, and T7.6 references
classical MVS/TSDF/PromptDA baselines. These are **not installed in the `helios` conda env**
(`/home/yogesh/anaconda3/envs/helios/bin/python`) — check what's actually importable before
assuming anything is available. Do not `pip install` large model packages/download pretrained
weights without checking network/disk feasibility first; if a specific external model genuinely
isn't practical to run in this environment, implement the **diagnostic methodology for real**
(the actual ablation/sweep logic, using Phase 0/1's real rendering as the data source) against
whatever anchor model *is* actually available or reasonably installable in the `helios` env, and
document clearly which real anchor you used and why, rather than faking results from a model
that was never actually run.

Use the `helios` conda env for all Python: `/home/yogesh/anaconda3/envs/helios/bin/python`.

## HARD CONSTRAINT

Every file you create or modify must live under `/home/yogesh/PyHelios/yogesh_dev/`. Do not
touch `apple_tree.py`, `apple_tree_cameras.py`, `apple_tree_gaussian_splatting.py`,
`helios-core/`, `pyhelios/`, or anything with uncommitted changes already in git status. No
`git commit`/`push`/`checkout`/`stash`, no `sudo`. Installs into the `helios` env are allowed
only if genuinely necessary, scoped, and documented (same policy Phase 5 used for `pulp`) —
prefer lightweight/classical baselines over multi-GB pretrained checkpoints if disk/bandwidth
is a real constraint; check available disk space first and document what you found.

## Deliverables (`yogesh_dev/phase7/`)

- **T7.1** — Helios -> WAI dataset writer (MapAnything's format). Write real Phase 0/1 renders
  (RGB, depth, poses, intrinsics) into that format for real. Look up or infer the WAI format
  structure; if the exact spec can't be found, implement a reasonable, clearly-documented
  version of it (images + per-frame pose/intrinsics + depth, in a directory/manifest layout)
  rather than blocking on an exact external spec match.
- **T7.2 (D1)** — pose-conditioning ablation: four conditions (images only / +intrinsics /
  +intrinsics+extrinsics / +depth) on whatever real anchor model is actually available/
  installable (see constraint above). If no full foundation model can run, implement a
  reasonable, real proxy measurement (e.g. a classical structure-from-motion or PnP-based
  reconstruction quality metric under each conditioning level) that still tests the real
  underlying hypothesis (does giving the model more pose info improve reconstruction), and
  document explicitly that this is a proxy, not the named foundation models.
- **T7.3 (D2)** — baseline-angle sweep: arc width 5 degrees to 360 degrees, real camera poses
  rendered from Phase 0's rig at varying angular spacing, with and without pose conditioning.
  This is called out as "likely your core figure" — make sure it's a real sweep with enough
  points to show a curve, not 2-3 samples.
- **T7.4 (D3)** — LAI (leaf area index) sweep on a fixed branch skeleton, measuring
  branch-geometry error and attention effective rank. Note: needs "the proposal's
  occlusion-regulation module" which Phase 2 already confirmed does not exist anywhere in
  this codebase — implement the LAI sweep and branch-geometry-error measurement for real
  (varying leaf density directly via the canopy/plant architecture parameters), and document
  clearly that the "attention effective rank" sub-metric is skipped/approximated if it depends
  on a foundation model's internal attention that isn't actually running here.
- **T7.5 (D4)** — thin-structure recall by diameter class, reusing Phase 4's real
  diameter-class methodology (`phase4/voxel_sweep.py`) against this phase's own data. Benchmark
  to beat: <55% recall below 10mm — report your real number against that.
- **T7.6 (D5)** — honest classical baseline: classical MVS or depth-completion with exact
  poses (numpy/scipy-based multi-view stereo or simple depth fusion is fine — doesn't need
  heavyweight external packages) run for real against Phase 0/1's real multi-view data.
- **T7.7 (D6)** — metric-scale integrity: canopy volume, leaf area, fruit diameter, internode
  length, computed from real Helios Context geometry and cross-checked against the real
  reconstruction from T7.6/whatever anchor ran in T7.2, to see if scale is preserved correctly
  end to end.

## Logging and completion

Continuously append to `yogesh_dev/PHASE7_LOG.md` (what you checked was actually available in
the `helios` env before assuming, what you ran for real vs. proxied, real numbers, problems
hit). When finished (or genuinely blocked), write `yogesh_dev/PHASE7_STATUS.md` whose **last
line** is exactly `STATUS: DONE` or `STATUS: BLOCKED: <reason>` — written last, after
everything else. Be explicit per-subtask about which used a real named foundation model vs. a
documented proxy — don't let that distinction blur.
