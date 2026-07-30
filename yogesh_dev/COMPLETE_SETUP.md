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

### Phase 5 — Baselines and oracles — DONE
`phase5/` · [log](PHASE5_LOG.md) · [status](PHASE5_STATUS.md)

All nine baselines, real data: T5.1 fixed camera, T5.2 static 3-camera rig, T5.3 boustrophedon
raster, T5.4 random reachable views, T5.5 nearest-frontier heuristic, T5.6 greedy oracle
(324-candidate real V_reach), T5.7 ILP set-cover ceiling (k<=8, real MILP via pulp+CBC, caught
2 real solver-correctness bugs), T5.8 all-views fusion, T5.9 perfect-perception ablation
(exactly reproduced Phase 4's exploit-planner output as a correctness check).

### Phase 6 — Metrics harness — DONE
`phase6/` · [log](PHASE6_LOG.md) · [status](PHASE6_STATUS.md)

Reproduced and fixed 3 real pre-existing bugs in `apple_tree_gaussian_splatting.py` (train/test
split, masked PSNR, occlusion-aware supervision) without touching that file directly, plus
occlusion-conditioned recall, class-stratified F-score, occupancy confusion matrix, discovery
curves, oracle-normalized Π, IG calibration (found anti-correlated, ρ≈-0.26 — flagged for
follow-up), deadline-enforced closed loop, per-module latency table.

### Phase 7 — Foundation model diagnostics (D1–D6) — DONE
`phase7/` · [log](PHASE7_LOG.md) · [status](PHASE7_STATUS.md)

`helios` env has no foundation models installed (checked, not assumed) — used a documented
classical multi-view-geometry proxy for D1-D3 instead of faking results. D2's angle sweep
found the "no collapse when posed" theory doesn't hold for this proxy. D4 thin-structure
recall (65-76% below 10mm) beats the <55% benchmark. D6 metric-scale integrity mostly within
4-24% of ground truth.

### Phase 8 — Scale-up — DONE (final phase)
`phase8/` · [log](PHASE8_LOG.md) · [status](PHASE8_STATUS.md) · [preregistration](phase8/PREREGISTRATION.md)

Real seeded canopy factory, fractional-factorial screening design (run at documented reduced
scale — 24 canopies vs. the full 320+ spec, with a real ~6.8-hour full-scale cost estimate
extrapolated from measured timing), `apple` vs `apple_fruitingwall` interpenetration
comparison (29% vs 4% at 1.5m spacing), full statistics suite, pre-registered metrics with a
passing Tatarchenko degenerate-baseline check, and a LiDAR digital-twin path achieving 99.88%
leaf-area fidelity with exact (ρ=1.0) planner-ranking preservation.

---

## Full plan status: all 9 phases (0-8) complete

Every phase in `helios_setup_tasks.md` has real, runnable deliverables under `yogesh_dev/`.
See `FINDINGS_SUMMARY.md` for the cross-cutting synthesis of what was learned, and
`PHASE_BY_PHASE_FINDINGS.md` for a detailed "what we did / what we found" per phase.

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

All 9 phases are done. What's left is upgrading placeholders to the real thing, and spending
real compute at real scale:

- **T0.6** (the real `CollisionDetection` binding) is the single highest-leverage task left —
  it would upgrade every placeholder across Phases 2-4 (occlusion via rendering instead of ray
  casting, bounding-box collision instead of real collision, CPU-only information gain) from
  "documented approximation" to "real" in one pass. C++/pybind11 work, not Python.
- **Phase 8's full-scale factorial sweep** is now a known, bounded cost (~6.8 real GPU-hours
  per the measured extrapolation) rather than an open-ended one — worth running once appetite
  exists for that compute spend.
- **The Phase 6 IG anti-correlation finding (Spearman ρ≈-0.26)** is worth investigating before
  trusting information-gain-driven exploration in a real planner — it suggests the current IG
  formulation doesn't track real value well on this dataset.
- **The Phase 5 finding that Phase 2's reachable-pose grid and Phase 3's joint limits were
  never reconciled** should be fixed before any of Phase 4/5's motion-time numbers are treated
  as trustworthy at the pose level.
- Reconstruct a real tree via the LiDAR digital-twin path (T8.6 built the machinery; it was
  run against a simulated scan of a Helios canopy, not an actual physical tree) if genuine
  sim-to-real validation becomes a priority.
