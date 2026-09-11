# Task: Implement Phase 6 of the Helios setup plan (metrics harness)

Unattended headless run (`--dangerously-skip-permissions`), nobody watching interactively.
Follow the constraints below exactly rather than asking.

## Context

Repo: `/home/yogesh/PyHelios`, branch `apple-tree-cameras`. Full plan:
`/home/yogesh/PyHelios/helios_setup_tasks.md` — **only implement Phase 6** (section
"## Phase 6 — Metrics harness", tasks T6.1-T6.11).

**Prior phases already produced working code and real data, all merged into this branch under
`yogesh_dev/`** (no need to check out other worktree branches): `phase0/` (camera rig),
`phase1/` (ground truth, depth, labels), `phase2/` (`visibility.py`/`avub.py`), `phase3/`
(kinematics/roadmap), `phase4/` (occupancy map, planners), `phase5/` (baselines, may still be
mid-run in a separate worktree — don't depend on it).

**T6.1-T6.3 describe real, already-confirmed bugs in the existing (non-`yogesh_dev`) gsplat
pipeline at `/home/yogesh/PyHelios/apple_tree_gaussian_splatting.py`:**
- **T6.1**: line 348, `"split": "test" if (i % test_every == 0) else "train"`, combined with
  `camera_poses` being generated as a flattened `num_cols` x `num_rows` grid — when
  `test_every == num_cols` (check `CAPTURE_CONFIGS` around line 71 and wherever `test_every`
  is set from it), `i % num_cols == 0` always lands on the same grid column, so every config's
  test set is column 0 only, not a representative sample.
- **T6.2/T6.3**: masked PSNR and occlusion-aware mask supervision — look at
  `load_dataset_tensors` (line ~375) and wherever PSNR/loss is computed in this file for the
  current (flawed) behavior to fix.

## HARD CONSTRAINT

Every file you create or modify must live under `/home/yogesh/PyHelios/yogesh_dev/`. **Do not
edit `apple_tree_gaussian_splatting.py` or any other file outside `yogesh_dev/` directly**,
even though T6.1-T6.3 are real bugs in that file. Instead: implement the corrected logic as
importable functions in `yogesh_dev/phase6/`, demonstrate the fix is correct against real data
(e.g. show the old `i % num_cols` logic actually does collapse to column 0, and your seeded
random permutation doesn't), and write a precise patch description (exact line numbers, before/
after) in `PHASE6_LOG.md` for a human to apply to the real file later. This matches how every
prior phase has handled anything outside `yogesh_dev/`. No `git commit`/`push`/`checkout`/
`stash`, no `sudo`, no installs outside the `helios` env
(`/home/yogesh/anaconda3/envs/helios/bin/python`).

## Deliverables (`yogesh_dev/phase6/`)

- **T6.1** — seeded random permutation train/test split, replacing the `i % test_every`
  scheme. Demonstrate: show the old scheme's test set is single-column (reproduce the bug for
  real on actual `camera_poses` grids from the existing configs), show your fix distributes
  across all columns.
- **T6.2** — masked PSNR restricted to GT-fruit ∪ rendered-alpha, not raw full-frame PSNR.
  Show the actual score inflation on real data (e.g. compare a real all-background dummy
  render's PSNR under both metrics — should be high under naive PSNR, low/excluded under
  correct masking).
- **T6.3** — occlusion-aware mask supervision: render fruit-only for unoccluded silhouette,
  subtract fruit-visible mask from full scene for occluded-fruit pixels, and produce a
  training mask that **excludes** those pixels from loss rather than supervising them as
  background. Use Phase 1/2's real label maps and Phase 2's `visibility.py` as the
  occlusion source.
- **T6.4** — occlusion-conditioned detection recall, stratified by GT occlusion decile (using
  Phase 2's real per-fruit AVUB/vis_i as the occlusion measure).
- **T6.5** — semantically stratified F-score at class-specific tau (fruit 5mm, branch 10mm,
  wire 5mm, leaf 10mm) — no ICP alignment needed, poses are exactly known from Phase 1's
  `transforms.json`.
- **T6.6** — three-state occupancy confusion matrix against Phase 4's occupancy map output,
  report `M(free|occ)` restricted to wire/branch classes as the safety-critical miss rate.
- **T6.7** — discovery curve (view index / joint-space path length from Phase 3's execution-
  time model / wall-clock) + AUC + time-to-90%, using Phase 4/5's real coverage sequences.
- **T6.8** — oracle-normalized planning score Pi and per-step regret, using Phase 5's T5.6
  greedy oracle and T5.7 ILP ceiling as the normalizers (if Phase 5 isn't finished yet, use
  whatever of its outputs exist, or Phase 2's AVUB as a fallback normalizer — document which).
- **T6.9** — IG calibration: Spearman rho per step, top-1 hit rate, sparsification curve,
  AUIGSE, against Phase 4's real information-gain values.
- **T6.10** — deadline-enforced closed-loop mode: arm keeps moving during planning, planner
  forfeits if over budget, using Phase 3's real execution-time model for the clock. Report the
  gap vs. a paused-clock baseline.
- **T6.11** — per-module latency table (mean/p95/p99/max) at a stated resolution, plus a
  hardware-independent work unit (ray casts, candidate evaluations) — actually time the real
  modules from Phases 0-5 you have access to, don't estimate.

Run everything against real data from Phases 0-5. Where a metric depends on something that
doesn't exist yet in this codebase (e.g. Phase 5 unfinished, or T2.6's missing
occlusion-regulation module), say so plainly and use the best available real substitute,
documented as such — same policy every prior phase followed.

## Logging and completion

Continuously append to `yogesh_dev/PHASE6_LOG.md` (what you did, real numbers, the T6.1-T6.3
patch description for the real file, problems hit). When finished (or genuinely blocked),
write `yogesh_dev/PHASE6_STATUS.md` whose **last line** is exactly `STATUS: DONE` or
`STATUS: BLOCKED: <reason>` — written last, after everything else.
