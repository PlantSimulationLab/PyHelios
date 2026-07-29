# Complete Setup — Progress Overview

Source plan: [`helios_setup_tasks.md`](../helios_setup_tasks.md) (repo root). This file is an
index into what's actually been built under `yogesh_dev/` — each phase's own `PHASEn_LOG.md`
and `PHASEn_STATUS.md` has the full detail; this is the short version.

Every phase below ran as an unattended background Claude Code agent, isolated to its own git
worktree, confined to only writing under `yogesh_dev/`, then merged and pushed to
`fork/apple-tree-cameras`.

## Standing blocker (affects every phase)

**T0.6 — `CollisionDetection` is not exposed in PyHelios** (`castRaysSoA`, `findCollisions`,
`buildBVH`). Phase 0 recommended building this C++/pybind11 binding but it was never
implemented (out of scope for a Python-only, `yogesh_dev`-confined run). Every later phase
worked around it with a documented placeholder (bounding-box collision, render-based
occlusion instead of ray casting, etc.) rather than pretending it doesn't matter. This is the
single most valuable next real engineering task if progress stalls.

## Phase 0 — Radiation camera migration and benchmarking — DONE
`phase0/` · [log](PHASE0_LOG.md) · [decisions](PHASE0_DECISIONS.md) · [status](PHASE0_STATUS.md)

Radiation-camera rig (pinhole, correct HFOV conversion), pose convention validated sub-pixel
accurate (0.71px), honest Tier B (Visualizer) vs Tier C (RadiationModel) benchmark. Key
finding: `runBand()` cost is dominated by a flat ~0.6-1.0s scene-wide solve, not by
resolution/AA — direct evidence for prioritizing the `runCamerasOnly()` upstream patch.

## Phase 1 — Ground truth export — DONE
`phase1/` · [log](PHASE1_LOG.md) · [status](PHASE1_STATUS.md)

`fruit_ground_truth.json` (73 fruit/3 trees), per-pixel semantic + instance label maps, real
EXR depth, gsplat-compatible `transforms.json` (cross-checked against T1.2/T1.3, 1.41px mean
reprojection error), seeded RGB-D noise model.

## Phase 2 — Visibility ground truth (AVUB) — DONE (T2.6 blocked, not faked)
`phase2/` · [log](PHASE2_LOG.md) · [status](PHASE2_STATUS.md)

Per-primitive `vis_i(v)` (17,098 fruit-surface primitives, r=0.924 cross-validation), real
union-over-poses coverage (+8.7pt mean over single-view), AVUB mean 0.499 / AVUB^inf mean
0.977 on a placeholder reachable-pose set, achievability classes. T2.6 genuinely skipped — the
WTFRC occlusion-regulation module it needs to validate against doesn't exist anywhere in this
codebase (repo-wide search came up empty).

## Phase 3 — Kinematics and reachability roadmap — DONE
`phase3/` · [log](PHASE3_LOG.md) · [status](PHASE3_STATUS.md)

Hand-rolled 5-DOF FK + closed-form IK (round-trip to ~1e-14), trapezoidal execution-time model
(~14.7x gimbal/linear cost asymmetry), k-NN roadmap with placeholder (bounding-box) collision,
arm-vs-arm collision proven structurally impossible by construction.

## Phase 4 — Map and planner — DONE (T4.5 GPU/CUDA explicitly out of scope)
`phase4/` · [log](PHASE4_LOG.md) · [status](PHASE4_STATUS.md)

Log-odds occupancy map (real depth+poses as the sensor input), voxel-size/thin-structure
sweep, semantic layer, fruit tracker measured against oracle (from-scratch Hungarian
algorithm), CPU-reference information gain + GPU design note, explore planner (CELF verified
against brute force), exploit planner, 3-arm coordination (reproduced the trace-vs-log-det
submodularity failure mode from the task doc), gimbal gradient-ascent refinement (61 real
re-renders, 1.66x utility gain).

## Phase 5 — Baselines and oracles — IN PROGRESS
`phase5/` (job `1af98e12`, still running as of this writing)

T5.1-T5.9: fixed camera, static rig, boustrophedon raster, random views, nearest-frontier
heuristic, greedy oracle, ILP set-cover ceiling, all-views fusion, perfect-perception
ablation. All pure Python, no known blockers — first phase without one.

## Not yet started

Phase 6 (metrics harness), Phase 7 (foundation-model diagnostics), Phase 8 (scale-up) — see
`helios_setup_tasks.md` for scope. Phase 7 only needs Phases 0-1 and can run in parallel with
anything above.
