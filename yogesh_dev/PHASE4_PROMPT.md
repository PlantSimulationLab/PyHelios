# Task: Implement Phase 4 of the Helios setup plan (map and planner)

Unattended headless run (`--dangerously-skip-permissions`), nobody watching interactively.
Follow the constraints below exactly rather than asking. This is the largest phase so far —
budget your effort across all ten subtasks rather than over-polishing the first few.

## Context

Repo: `/home/yogesh/PyHelios`, branch `apple-tree-cameras`. Full plan:
`/home/yogesh/PyHelios/helios_setup_tasks.md` — **only implement Phase 4** (section
"## Phase 4 — Map and planner", tasks T4.1-T4.10).

**Prior phases already produced working code and real data, read before starting:**
- Branch `worktree-phase0-radiation`: `yogesh_dev/phase0/*.py` — camera rig, validated pose
  convention.
- Branch `worktree-phase1-groundtruth`: `yogesh_dev/phase1/*.py`, `yogesh_dev/phase1/output/`
  — `fruit_ground_truth.json`, real EXR depth per view, semantic/instance label maps,
  `transforms.json`.
- Branch `worktree-phase2-visibility` (worktree dir may be named `phase2-avub`): `yogesh_dev/phase2/*.py`
  — per-primitive `vis_i(v)`, AVUB/AVUB^inf, achievability classes, `PLACEHOLDER_reachable_poses`.
- Branch `worktree-phase3-kinematics`: `yogesh_dev/phase3/*.py` — FK/IK, execution-time model,
  k-NN roadmap (placeholder collision), arm geometry.

**Known real constraint (same one every prior phase hit):** `CollisionDetection`
(`castRaysSoA`, `findCollisions`, `buildBVH`) is **not exposed in PyHelios**. T4.1 and T4.5
in the task doc assume GPU ray-casting infrastructure that doesn't exist yet in this Python
API. Handle each on its own merits (see below) — don't just skip them.

**Note found by Phase 2**: apple-tree growth in `PlantArchitecture` is stochastic and
unseeded upstream — seed your own canopy build for reproducibility, and don't assume fruit
counts match exactly across phases' independent runs.

Use the `helios` conda env: `/home/yogesh/anaconda3/envs/helios/bin/python`.

## HARD CONSTRAINT

Every file you create or modify must live under `/home/yogesh/PyHelios/yogesh_dev/`. Do not
touch `apple_tree.py`, `apple_tree_cameras.py`, `helios-core/`, `pyhelios/`, or anything with
uncommitted changes already in git status. No `git commit`/`push`/`checkout`/`stash`, no
`sudo`, no installs outside the `helios` env.

## Deliverables (`yogesh_dev/phase4/`)

- **T4.1** — occupancy map, three-state (occupied/free/**unknown**), log-odds update, beam
  sensor model with range *and* angular uncertainty, dual resolution (coarser global + finer
  attention regions around fruit clusters). You have real depth (Phase 1's EXR files) and real
  poses (`transforms.json`) — use those as your beam sensor input instead of the missing
  ray-caster; this is a legitimate real implementation, not a workaround-in-disguise. Build
  your own lightweight log-odds voxel grid rather than pulling in nvblox/UFOMap/wavemap as
  external dependencies (that's a "decide build-vs-fork" call the task doc raises for a much
  later, larger-scale version of this — a real, working, self-contained implementation here is
  more valuable than a half-integrated external library). Document this scoping choice.
- **T4.2 (E1)** — sweep voxel size against branch/thin-structure recall by diameter class and
  against map update time, using real canopy geometry (primitive dimensions from the Context)
  as ground truth for what counts as a hit at each resolution. Real numbers, real sweep.
- **T4.3** — per-voxel semantic class posterior, fused from Phase 1's real
  `getPrimitiveDataLabelMap` output through the real known poses.
- **T4.4** — apple instance track database: build a real tracker across the pose sequence,
  and *also* build the oracle association using ground-truth `fruitID` (available for free in
  sim per Phase 1), then actually measure the tracker against the oracle (IDF1, ID switches).
  Don't skip the measurement step — a tracker without a reported IDF1 number isn't done.
- **T4.5** — GPU-batched information gain is explicitly `[C++/CUDA, needs T0.6]` and out of
  scope to implement for real in this Python-only, `yogesh_dev`-confined run. Instead: (a)
  implement a correct, vectorized (numpy, CPU) reference version of the information-gain
  computation over the T4.1 occupancy map so the *algorithm* is real and testable, clearly
  labeled as the CPU reference implementation, not the GPU-batched target; (b) write a short
  design note in `PHASE4_LOG.md` on what would actually change to make it GPU-batched
  (batch dimension, memory layout, what CUDA kernel structure would look like) so a human
  has a concrete starting point later. Do not claim GPU acceleration that isn't there.
- **T4.6** — explore planner: submodular max-coverage + CELF lazy evaluation, receding-horizon
  search over Phase 3's T3.4 roadmap (placeholder-collision roadmap is fine, same caveat
  propagates). Time-normalized utility using T3.3's real execution-time weights.
- **T4.7** — switching criteria, all three in disjunction: frontier exhaustion,
  marginal-value-rate threshold, Good-Turing coverage estimate over discovered fruit instances
  (`Ĉ = 1 - f1/n`), plus a hard `rho * T_total` cap. Implement and demonstrate each firing
  under a real (or realistically constructed) run trace.
- **T4.8** — exploit planner: budget-constrained submodular team orienteering,
  `F(A) = sum(w_i * phi(sum(q_i)))` with `phi(z) = 1 - exp(-z)`, cost-benefit greedy + CELF.
- **T4.9** — three-arm coordination: sequential greedy with randomized arm ordering. Actually
  verify submodularity of whatever objective you use (log-det vs. plain trace — the task doc
  is explicit that trace is NOT submodular and will make all arms converge on the same view;
  demonstrate this failure mode empirically with trace, then show log-det avoiding it).
- **T4.10** — gimbal-only local refinement: either gradient ascent on a differentiable
  semantic utility over pan/tilt, or a 3D-Move-to-See finite-difference gradient across the
  three physical cameras. Pick one, implement it for real against the actual camera rig.

Prefer real runnable demo scripts over class definitions with no execution. Where a task
depends on something upstream that's itself a documented placeholder (T3.4's roadmap
collision, T2.3's reachable-pose set), that's expected and fine — just don't let the
placeholder-ness silently disappear; keep tracing it through into your own docs.

## Logging and completion

Continuously append to `yogesh_dev/PHASE4_LOG.md` (what you did, real numbers, problems hit,
what's placeholder vs real, and the T4.5 GPU design note). When finished (or genuinely
blocked on a specific subtask), write `yogesh_dev/PHASE4_STATUS.md` whose **last line** is
exactly `STATUS: DONE` or `STATUS: BLOCKED: <reason>` — written last. If any individual
subtask (like T4.5's real GPU version) is intentionally out of scope rather than blocked,
say so explicitly per-subtask in the status file rather than blending it into one verdict.
