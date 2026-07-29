# Complete Setup — Full Plan Overview

Source plan: [`helios_setup_tasks.md`](../helios_setup_tasks.md) (repo root) — this file covers
**the entire plan, Phase 0 through Phase 8**, not just what's finished so far. Each completed
phase below links to its own `PHASEn_LOG.md`/`PHASEn_STATUS.md` under `yogesh_dev/` for full
detail; this file is the map of the whole territory, done and not-done alike.

Every phase so far ran as an unattended background Claude Code agent, isolated to its own git
worktree, confined to only writing under `yogesh_dev/`, then merged and pushed to
`fork/apple-tree-cameras`.

## Standing blocker (affects most later phases)

**T0.6 — `CollisionDetection` is not exposed in PyHelios** (`castRaysSoA`, `findCollisions`,
`buildBVH`). Phase 0 recommended building this C++/pybind11 binding but it was never
implemented (out of scope for a Python-only, `yogesh_dev`-confined run). Every phase since has
worked around it with a documented placeholder (bounding-box collision, render-based occlusion
instead of ray casting, etc.) rather than pretending it doesn't matter. **This is the single
most valuable real engineering task left** — it directly unblocks real (non-placeholder)
collision checking in Phase 3/4 and the GPU-batched information gain in T4.5.

---

## Done

### Phase 0 — Radiation camera migration and benchmarking — DONE
`phase0/` · [log](PHASE0_LOG.md) · [decisions](PHASE0_DECISIONS.md) · [status](PHASE0_STATUS.md)

Radiation-camera rig (pinhole, correct HFOV conversion), pose convention validated sub-pixel
accurate (0.71px), honest Tier B (Visualizer) vs Tier C (RadiationModel) benchmark. Key
finding: `runBand()` cost is dominated by a flat ~0.6-1.0s scene-wide solve, not by
resolution/AA — direct evidence for prioritizing the `runCamerasOnly()` upstream patch (below).

### Phase 1 — Ground truth export — DONE
`phase1/` · [log](PHASE1_LOG.md) · [status](PHASE1_STATUS.md)

`fruit_ground_truth.json` (73 fruit/3 trees), per-pixel semantic + instance label maps, real
EXR depth, gsplat-compatible `transforms.json` (cross-checked against T1.2/T1.3, 1.41px mean
reprojection error), seeded RGB-D noise model.

### Phase 2 — Visibility ground truth (AVUB) — DONE (T2.6 blocked, not faked)
`phase2/` · [log](PHASE2_LOG.md) · [status](PHASE2_STATUS.md)

Per-primitive `vis_i(v)` (17,098 fruit-surface primitives, r=0.924 cross-validation), real
union-over-poses coverage (+8.7pt mean over single-view), AVUB mean 0.499 / AVUB^inf mean
0.977 on a placeholder reachable-pose set, achievability classes. T2.6 genuinely skipped — the
WTFRC occlusion-regulation module it needs to validate against doesn't exist anywhere in this
codebase (repo-wide search came up empty).

### Phase 3 — Kinematics and reachability roadmap — DONE
`phase3/` · [log](PHASE3_LOG.md) · [status](PHASE3_STATUS.md)

Hand-rolled 5-DOF FK + closed-form IK (round-trip to ~1e-14), trapezoidal execution-time model
(~14.7x gimbal/linear cost asymmetry), k-NN roadmap with placeholder (bounding-box) collision,
arm-vs-arm collision proven structurally impossible by construction.

### Phase 4 — Map and planner — DONE (T4.5 GPU/CUDA explicitly out of scope)
`phase4/` · [log](PHASE4_LOG.md) · [status](PHASE4_STATUS.md)

Log-odds occupancy map (real depth+poses as the sensor input), voxel-size/thin-structure
sweep, semantic layer, fruit tracker measured against oracle (from-scratch Hungarian
algorithm), CPU-reference information gain + GPU design note, explore planner (CELF verified
against brute force), exploit planner, 3-arm coordination (reproduced the trace-vs-log-det
submodularity failure mode from the task doc), gimbal gradient-ascent refinement (61 real
re-renders, 1.66x utility gain).

## In progress

### Phase 5 — Baselines and oracles — RUNNING
`phase5/` (job `1af98e12`)

All nine baselines are pure Python with no known blockers (first phase without one): T5.1
fixed camera, T5.2 static 3-camera rig, T5.3 boustrophedon raster, T5.4 random reachable
views, T5.5 nearest-frontier heuristic, T5.6 greedy oracle, T5.7 ILP set-cover ceiling (k<=8),
T5.8 all-views fusion, T5.9 perfect-perception ablation feeding GT detections into Phase 4's
exploit planner. Exists so the real planner has something honest to be measured against.

---

## Not yet started

### Phase 6 — Metrics harness
Fixing real, already-identified flaws in the existing gsplat evaluation pipeline plus new
planning/mapping metrics:
- T6.1 train/test split bug (`i % 8 == 0` always selects column 0 — needs a seeded random permutation)
- T6.2 masked PSNR bug (background-dominated score inflation — restrict to GT-fruit ∪ rendered-alpha)
- T6.3 occlusion-aware mask supervision (stop teaching the splat occluded apples are absent)
- T6.4 occlusion-conditioned detection recall by GT occlusion decile
- T6.5 class-specific F-score (fruit 5mm / branch 10mm / wire 5mm / leaf 10mm), no ICP needed (exact frame known)
- T6.6 three-state occupancy confusion matrix, `M(free|occ)` on wires/branches as the safety-critical metric
- T6.7 discovery curve (3 x-axes: view index, joint-space path length, wall-clock) + AUC + time-to-90%
- T6.8 oracle-normalized planning score Π + per-step regret
- T6.9 IG calibration (Spearman ρ, top-1 hit rate, sparsification curve, AUIGSE)
- T6.10 deadline-enforced closed-loop mode (arm moves during planning, forfeits over budget)
- T6.11 per-module latency table (mean/p95/p99/max) + hardware-independent work unit

### Phase 7 — Foundation model diagnostics (D1–D6)
Only needs Phases 0-1 (already done) — **can run any time, in parallel with anything else,
including right now.** Framed in the task doc as "the cheapest self-contained paper in the
plan":
- T7.1 Helios → WAI dataset writer (MapAnything format)
- T7.2 D1 pose-conditioning ablation (images-only / +intrinsics / +intrinsics+extrinsics / +depth)
- T7.3 D2 baseline-angle sweep (5°→360° arc width) — "likely your core figure"
- T7.4 D3 LAI sweep on a fixed branch skeleton (needs the occlusion-regulation module — same one T2.6 found missing)
- T7.5 D4 thin-structure recall by diameter class (benchmark to beat: <55% below 10mm)
- T7.6 D5 honest classical baseline (MVS/TSDF/PromptDA with exact poses)
- T7.7 D6 metric-scale integrity (canopy volume, leaf area, fruit diameter, internode length)

### Phase 8 — Scale-up
- T8.1 seeded, disjoint dev/test canopy sets for paired comparisons
- T8.2 factorial sweep (LAI × fruit density × clustering × trellis type)
- T8.3 switch to `apple_fruitingwall` alongside `apple`
- T8.4 statistics (≥20 canopies/cell, bootstrap CIs resampling canopies not views, paired Wilcoxon, Cliff's δ, Holm-Bonferroni)
- T8.5 pre-registered metrics/seeds + Tatarchenko degenerate-baseline check
- T8.6 digital-twin sim-to-real validation via the LiDAR plugin's leaf-by-leaf reconstruction

---

## Upstream patches worth contributing (helios-core, not PyHelios)

Not part of any phase's Python deliverables, but real, valuable, and each removes a constraint
every phase above has hit:

1. **`runCamerasOnly()`** — highest value. Skip the full scene radiative-transfer solve when
   only the camera moved (fast path already exists internally, `RayTracingBackend.h:153`, just
   not public). Phase 0's benchmark is direct evidence this is plausibly a 1Hz→10Hz jump.
2. **In-memory depth + pixel-UUID getters** — the C++ already produces these; PyHelios's
   `getGlobalData` just can't return float arrays yet.
3. **Binary label maps** — `getPrimitiveDataLabelMap`/`getObjectDataLabelMap` round-trip
   through a text file; fine for datasets (used throughout Phase 1-5), too slow for a closed loop.
4. **`CollisionDetection` bindings** — this is T0.6, the standing blocker above.
5. **Camera up-vector/roll** — not blocking for the current 5-DOF design, but worth documenting.

## Suggested order of attack from here

Phases 0-4 are done; Phase 5 is running. Two independent paths open up next:

- **Phase 6** (metrics harness) can start immediately — it only touches the existing gsplat
  pipeline and Phase 0-5 outputs, no new blockers.
- **Phase 7** (foundation-model diagnostics) has been runnable in parallel since Phase 1
  finished and still hasn't been started — per the task doc, this de-risks the largest open
  question in the plan and is worth picking up soon rather than leaving until last.
- **Phase 8** (scale-up) should wait until 6-7 land, since it's a multiplier on canopy count
  and expensive to run before the metrics/diagnostics it depends on are trustworthy.
- **T0.6** (the real `CollisionDetection` binding) remains the one task that would upgrade
  every placeholder across Phases 2-4 from "documented approximation" to "real" — worth a
  dedicated pass whenever there's appetite for the C++/pybind11 work.
