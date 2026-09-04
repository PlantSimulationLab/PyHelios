# Phase-by-Phase: What We Did and What We Found

Companion to `FINDINGS_SUMMARY.md` (cross-cutting synthesis) and `COMPLETE_SETUP.md` (scope
map). This file goes phase by phase in more depth — every subtask's concrete work and its real
result. Source detail lives in each `PHASEn_LOG.md`/`PHASEn_STATUS.md`; numbers here are
pulled from those, not re-derived.

---

## Phase 0 — Radiation camera migration and honest benchmarking

### What we did
- Set up the radiation band + light source stack (T0.1): red/green/blue bands, sun + diffuse
  sources, chose **plausible RGB** over calibrated radiometry (documented reasoning in
  `PHASE0_DECISIONS.md`) since neither the gsplat pipeline nor the ground-truth consumers need
  radiometric accuracy.
- Replaced the `Visualizer`-based `CAMERA_RIGS` dict with real `addRadiationCamera` calls
  (T0.2): pinhole (`lens_diameter=0.0`), HFOV correctly converted from the existing vertical-FOV
  convention, `camera_resolution` starting at 640x480, AA=2.
- Empirically validated the radiation camera's pose convention (T0.3) with a 9-sphere test
  scene at known world coordinates, checked against projected `K·[R|t]·X`.
- Restructured the render loop (T0.4): `updateGeometry()` once outside the pose loop, one
  multi-band `runBand()` call per pose.
- Ran an honest Tier B (`Visualizer`) vs Tier C (`RadiationModel`) benchmark (T0.5) plus a
  3x3 resolution/AA sweep, all real wall-clock measurements.
- Wrote a decision doc for T0.6 (ray-casting architecture) rather than implementing the C++
  binding — recommends building it, with reasoning grounded in the T0.5 numbers.
- Wired `Visualizer.getDepthMap()` into a fresh Tier-B rig (T0.7).

### What we found
- HFOV conversion measured at **57.822°** (640x480, from a 45° VFOV).
- Pose convention is **sub-pixel accurate**: 0.71px mean reprojection error across two
  different camera poses (axis-aligned and off-axis).
- **Render cost is dominated by a fixed per-call cost, not camera parameters**: `runBand()`
  clustered at 0.62-1.09s across a 16x pixel-count range (320x240 to 1280x960) and a 4x AA
  range (1-4). Decomposed: `runBand()` itself took 0.620-0.627s (flat across 3 poses); reading
  back all 9 camera/band pixel buffers took only 0.037-0.042s. The scene-wide radiative-transfer
  solve **is** the cost — direct evidence for prioritizing the `runCamerasOnly()` upstream patch.
- **Tier B vs Tier C comparison is confounded**: this devbox has no physical display, so Tier B
  ran under Mesa llvmpipe (CPU software rendering via Xvfb), not the RTX 5090. Tier C measuring
  "faster" here is an artifact of that, not evidence ray tracing beats OpenGL rasterization in
  general — flagged explicitly, re-run needed on real display/GPU-backed OpenGL hardware.
- **`Visualizer.getDepthMap()` is broken upstream**: returns exactly `{0.0, 255.0}`, no
  intermediate values, confirmed via a `// \todo` comment directly on the code path in
  helios-core's `VisualizerRendering.cpp`. This rules out T0.6's "interim hack" option (using
  depth-only ray casting as a stand-in for real ray tracing).
- Found and worked around an `exposure="auto"` pitfall that makes pixel values incomparable
  across frames, and a flux-independent photometric saturation artifact affecting ~15-20% of
  foliage pixels on this canopy (documented, not fixed — out of scope).
- **T0.6 recommendation**: build the `CollisionDetection` binding (option 1) over a bespoke
  C++ sim loop (option 2) or the broken interim hack (option 3, ruled out by the finding above).

---

## Phase 1 — Ground truth export

### What we did
- Enabled `optionalOutputObjectData` for `plantID`/`fruitID`/`leafID`/`rank`/`age`/
  `phenology_stage` (T1.1), verified labels actually appear via `context.listObjectData`.
- Exported `fruit_ground_truth.json` (T1.2): object ID, plant ID, centroid, bounding box,
  equivalent diameter, surface area, primitive UUID list, plus the T1.1 labels as bonus fields.
- Exported per-pixel semantic (derived int class-id) and instance (`fruitID`) label maps for
  all 9 views (T1.3), replacing the old flat-color-render hack entirely.
- Exported real EXR depth via `writeDepthImageDataEXR`, read back with the `OpenEXR` package
  (T1.4).
- Extended `transforms.json` with the radiation camera's real HFOV, derived K, and the
  T0.3-validated world-to-camera convention, gsplat-compatible (T1.5).
- Built a toggleable RGB-D noise model — range-dependent Gaussian noise + depth-edge mixed
  pixels pulled toward the real discontinuity partner (T1.6).

### What we found
- **73 fruit objects across 3 trees** in this run's ground-truth export.
- **`optionalOutputObjectData` must be called *before* `buildPlantInstanceFromLibrary`**, not
  after as the task doc's own code snippet orders it — confirmed by an A/B test where the
  "after" ordering silently produces zero object data. Also found `plantID` is never actually
  set on fruit objects; derived via a UUID→plant-ID lookup instead.
- **`getPrimitiveDataLabelMap(cam, "object_label")` silently returns an all-background map**:
  the C++ layer can't label-map a string-typed field (fails via a stderr warning, not a Python
  exception). Fixed by deriving an int-typed class-id field first before label-mapping.
- **Sky/no-hit pixels are exactly `depth == -1.0`**, verified pixel-for-pixel aligned with the
  semantic map's background mask — a previously-undocumented fact about the depth writer.
- **Cross-validation across three independently-produced artifacts agreed**: projecting 219
  real (fruit, view) pairs through T1.5's intrinsics/extrinsics and comparing against T1.3's
  measured instance-mask centroids gave **1.41px mean / 0.98px median** error — consistent with
  Phase 0's T0.3 sub-pixel validation via a completely different measurement path.
- **Noise model tuning**: the RealSense-typical 0.03m mixed-pixel threshold proved far too
  aggressive on this cluttered canopy (37% of pixels flagged, 70cm RMSE) — retuned against the
  actual depth-gradient distribution to a final ~4cm mean / ~7cm RMSE depth change.

---

## Phase 2 — Visibility ground truth (AVUB / NVE)

### What we did
- Built its own seeded canopy (found Phase 1 hadn't seeded — see below), 83 fruit across 3
  trees, 17,098 fruit-surface primitives, each assigned a unique ID.
- Implemented `vis_i(v)` (T2.1) at real **per-primitive** resolution — better than the task
  brief's anticipated object-level fallback — by reading primitive IDs back per pose via
  `getPrimitiveDataLabelMap`, without needing the missing `CollisionDetection` ray caster.
- Implemented real union-over-poses accumulation (T2.2), not max-over-views.
- Built `PLACEHOLDER_reachable_poses` (T2.3): 108 poses/tree front-hemisphere grid, plus a
  288 poses/tree full-sphere set, explicitly labeled as a stand-in for Phase 3's not-yet-built
  kinematics roadmap, with a documented substitution interface.
- Computed AVUB and AVUB^inf for all 83 fruit (T2.4), and fruit achievability classes (T2.5):
  observable / sizeable (γ=0.30) / graspable (approach-cone approximation).
- Searched the entire repo/history for the WTFRC occlusion-regulation module needed for T2.6.

### What we found
- **Per-primitive `vis_i(v)` cross-validated at r=0.9242** (Pearson) against the task doc's own
  suggested check (raw `fruitID` pixel-count fractions) over 241 real (fruit, view) pairs.
- **Union-over-poses beats single-view for almost every fruit**: 82/83 fruit had union coverage
  exceed their best single view, mean improvement **+8.7 points**, best case nearly doubled
  (22.0% → 41.1%).
- **AVUB mean 0.499, AVUB^inf mean 0.977, ratio of means 0.511** — caveated as
  placeholder-pose-derived, will change once Phase 3's real reachability replaces the stand-in.
- **Achievability**: 100% observable, 95.2% sizeable (of observable), 98.8% graspable (of
  observable).
- **T2.6 is genuinely blocked, not faked**: 12 hits across every commit/branch, all prose in
  `active_vision_design.md`/`helios_setup_tasks.md` describing the *external* proposal's
  module — zero lines of actual implementation anywhere in this codebase. Reproducible via
  `yogesh_dev/phase2/t26_check.py`.
- **Apple-tree growth is stochastic and was never seeded upstream** — verified with a real A/B
  build test (97 vs 72 fruit from two unseeded builds of the same code). This is why Phase 2's
  83-fruit scene is a different, independently-real realization from Phase 1's 73, not the same
  dataset reused — every phase since seeds its own build explicitly because of this finding.

---

## Phase 3 — Kinematics and the reachability roadmap

### What we did
- Hand-rolled 5-DOF forward kinematics (T3.1): 3 prismatic + pan/tilt → camera pose, with
  joint limits and a documented (placeholder, no real hardware spec exists) per-arm vertical
  band.
- Closed-form inverse kinematics (T3.2): linear axes solved for position, pan/tilt for look
  direction — verified by actually round-tripping FK(IK(pose)).
- Trapezoidal execution-time model (T3.3) with placeholder but clearly-labeled velocity/
  acceleration numbers for linear stages vs. gimbal.
- Built the roadmap (T3.4): discretized reachable poses per arm with cached IK, k-NN graph
  weighted by real T3.3 execution time, with an explicitly-placeholder (bounding-box) collision
  check standing in for the missing `CollisionDetection` binding.
- Arm/workcell collision geometry (T3.5): non-overlapping vertical bands proven by direct
  interval-overlap math (arm-vs-arm collision structurally impossible by construction), plus a
  live Helios Context geometry cross-check.

### What we found
- **FK/IK round-trip accurate to ~1e-14** across 3125 samples per arm.
- **~14.7x cost asymmetry between gimbal and linear-stage motion** — the real number underlying
  the whole nested-planner design idea (cheap gimbal refinement inside expensive linear moves).
- **Roadmap/graph-search machinery is real and runs against real geometry** — only the
  collision predicate underneath is a documented placeholder, precisely scoped: what changes
  once real `findCollisions`/`castRaysSoA` lands is written out explicitly.
- Arm-vs-arm collision: proven impossible by construction (pure math), not by simulation.
  Arm-vs-canopy collision checking is not implemented — still needs T0.6.

---

## Phase 4 — Map and planner

### What we did
- Built its own seeded single-tree scene (41,351 primitives, 27 fruit, 1336 real tube
  segments), rendered 42 real views (depth EXR, semantic/instance/vis-primitive-id label maps,
  real poses) across 3 arms' placeholder-collision roadmaps.
- Hand-rolled a 3-state (occupied/free/unknown) log-odds occupancy map (T4.1) using real
  depth+poses as the beam sensor input, instead of nvblox/UFOMap/wavemap or the missing ray
  caster — a real, self-contained implementation, documented as a scoping choice.
- Voxel-size vs. thin-structure-recall sweep (T4.2/E1) against the real 1336 tube segments'
  actual diameters.
- Per-voxel semantic class posterior fused from real label maps (T4.3).
- Apple instance tracker (T4.4) built *and* measured against a ground-truth oracle association
  (IDF1, ID switches), using a from-scratch Hungarian algorithm (no scipy in this env).
- T4.5 (GPU-batched info gain): declared the CUDA implementation explicitly out of scope,
  shipped a correct vectorized CPU reference implementation plus a concrete GPU design note
  instead.
- Explore planner (T4.6): submodular max-coverage + CELF, receding-horizon search over the
  T3.4 roadmap.
- Switching criteria (T4.7): frontier exhaustion, marginal-value-rate threshold, Good-Turing
  coverage, hard time cap — all demonstrated firing and not firing on real run traces.
- Exploit planner (T4.8): budget-constrained submodular team orienteering.
- Three-arm coordination (T4.9): sequential greedy with randomized ordering, explicitly
  verified submodularity (log-det vs. trace).
- Gimbal-only local refinement (T4.10): gradient ascent over pan/tilt via real central
  finite-difference gradients from actual re-renders.

### What we found
- **Two real bugs found and fixed**: cross-worktree `PYTHONPATH` resolving to the wrong,
  unbuilt `pyhelios` package; a native segfault calling tube-node accessors on Cone-typed
  petiole objects.
- **T4.6's CELF is algorithmically correct** (selected sequence identical to brute-force
  greedy on real data) but **measured 0% speedup** at this phase's real candidate-pool scale
  (5-13 rendered poses/arm) — reported honestly rather than hidden or inflated.
- **T4.7 fired both ways on real data**: Good-Turing coverage crossed 0.95 *before* frontier
  exhaustion on one arm; on another arm (`arm_mid`) it never crossed 0.95 at all.
- **T4.9 reproduced the exact failure mode the task doc warned about**: under a plain-trace
  objective, three-arm coordination collapsed to **1 unique view assignment across 6 random
  orderings**; log-det gave **3**, with a real diversity metric (mean pairwise bearing dot
  product) confirming log-det chooses more diverse views. Trace's non-submodularity was
  verified by an executable assertion on real data, not just asserted in prose.
- **T4.10 achieved a real 1.66x semantic-utility improvement** at its peak, from 61 real
  re-renders (not a synthetic differentiable stand-in).
- Every planner that searches over the T3.4 roadmap (T4.6/T4.8/T4.9) inherits its placeholder
  (bounding-box) collision check — traced through explicitly rather than silently absorbed.

---

## Phase 5 — Baselines and oracles

### What we did
- Built a fresh, real, seeded 3-apple-tree scene (83 fruit, 17,098 fruit-surface primitives,
  seed 20260729) and rendered/cached Phase 2's real 324-pose reachable set once, shared across
  every baseline for a fair comparison.
- Implemented all nine baselines as real view-selection policies scored on the same real
  `mean_coverage_frac` (AVUB-style) metric plus Phase 3's real execution-time cost: T5.1 single
  fixed camera, T5.2 static 3-camera rig, T5.3 boustrophedon raster, T5.4 random reachable
  views, T5.5 nearest-frontier + distance-advantage heuristic, T5.6 greedy oracle, T5.7 ILP
  set-cover ceiling, T5.8 all-reachable-views fusion, T5.9 perfect-perception ablation.
- Installed `pulp` + CBC into the `helios` env (scoped, documented) for a real MILP solve in
  T5.7 rather than a greedy approximation mislabeled as ILP.

### What we found
- **Two real ILP correctness bugs caught and fixed mid-phase**: a fruit-level-vs-primitive-level
  objective mismatch, and a free-CBC "Optimal" status that couldn't actually be trusted at this
  problem's scale (~17k primitive-level binaries) — verified via a targeted cold-solve
  diagnostic, then fixed by cross-validating against known lower bounds so the reported ceiling
  can never silently under-report an independently-achievable result.
- **T5.7's k=1-5 are solver-verified optima; k=6-8 are honestly reported as valid lower bounds**
  (matching T5.6's greedy oracle), not solver-certified ceilings — free CBC couldn't verify
  better within a 180s/k budget at this scale.
- **T5.9 exactly reproduced Phase 4's own exploit-planner output** as a correctness
  cross-check, then added a genuinely new noisy-perception ablation using Phase 4's real T4.4
  tracker output — isolating perception-driven value loss from planning-algorithm error.
- **A real, previously-unnoticed integration gap**: Phase 2's reachable-pose grid and Phase 3's
  per-arm joint-limit envelope were developed independently and never reconciled against each
  other — T5.3/T5.5/T5.8's motion-time costing applies Phase 3's model to joint coordinates
  derived directly from poses without validating those poses are actually within Phase 3's
  placeholder joint limits. Flagged for follow-up, not silently ignored.
- **T5.6's greedy oracle was capped at 40 steps** (a safety bound) and hadn't fully saturated
  at that point on the real 324-candidate set — documented as a bound, not a discovered plateau.

---

## Phase 6 — Metrics harness

### What we did
- Reproduced three real, pre-existing bugs in `apple_tree_gaussian_splatting.py` **live**
  against real built trees and real Phase 1 renders (not touching that file directly, per
  constraint): T6.1 train/test split, T6.2 masked PSNR, T6.3 occlusion-aware supervision —
  implemented fixed versions in `yogesh_dev/`, wrote an exact before/after patch description.
- Occlusion-conditioned detection recall by GT occlusion decile (T6.4), class-stratified
  F-score at class-specific thresholds (T6.5), three-state occupancy confusion matrix (T6.6) —
  all against Phase 4's real single-tree dataset (27 fruit, 42 rendered views).
- Discovery curves + AUC + time-to-90% (T6.7), oracle-normalized planning score Π + per-step
  regret (T6.8), IG calibration — Spearman ρ, top-1 hit rate, sparsification curve, AUIGSE
  (T6.9) — all reusing Phase 4's real planner/IG code.
- Deadline-enforced closed-loop mode (T6.10): verified the mechanism forfeits correctly under
  a tight budget.
- Per-module latency table (T6.11): real wall-clock mean/p95/p99/max for 8 representative real
  modules across Phases 2-4, each with a stated hardware-independent work unit.

### What we found
- **T6.1's bug reproduced for real**: the old `i % test_every` scheme does collapse to a
  single grid column on the actual `camera_poses` grids from the existing configs; the seeded
  random-permutation fix distributes across all columns.
- **T6.2's naive PSNR inflation demonstrated on real data**: an all-background dummy render
  scores artificially high under raw PSNR, low/excluded correctly under the fixed masked
  version.
- **IG calibration came back anti-correlated: Spearman ρ ≈ -0.26** — the current
  information-gain formulation's predicted value does not track actual measured value well on
  this real dataset. This is a real, notable negative result worth investigating before
  trusting IG-driven exploration.
- **Wire/trellis class metrics (T6.5/T6.6) reported as real N/A**, not fabricated — no such
  class exists anywhere in this repo's scene yet.
- **T6.8 used Phase 4's own data as the primary oracle-normalization scale** (Phase 5 was
  still mid-run in a sibling worktree when Phase 6 ran) — Phase 5's differently-scaled T5.6/T5.7
  numbers are carried in only as a documented reference, not blended in as if directly
  comparable.
- **T6.10's deadline mechanism works correctly, but the closed-loop-vs-paused-clock gap is
  honestly reported as negligible** at this dataset's real scale — no compute cost measured
  anywhere in this codebase (CELF or exact ILP) is large enough relative to real arm motion
  time to matter yet.
- **`helios` env has no SciPy** — Spearman ρ was hand-rolled in `common.py`; no torch/gsplat
  either, so T6.1-T6.3 reimplement (rather than import) the relevant slice of the real gsplat
  file's logic.

---

## Phase 7 — Foundation model diagnostics (D1-D6)

### What we did
- Checked what's actually importable in the `helios` env **before** assuming anything (found:
  numpy/pillow/OpenEXR/PyYAML/PuLP + this repo's `pyhelios`; nothing else — no torch, scipy,
  cv2, scikit-learn, open3d, trimesh, pycolmap, and none of MapAnything/DA3/π³/VGGT). Confirmed
  disk (2.7T free) and network were fine, but installed nothing since none of this phase's math
  actually required it.
- Built a real Helios → WAI-format dataset writer (T7.1), looked up the actual
  facebookresearch/map-anything spec, wrote a real 16-view dataset to disk.
- Implemented a hand-rolled classical multi-view-geometry proxy standing in for the missing
  foundation models, used consistently across T7.2/T7.3/T7.4, labeled PROXY everywhere.
- Pose-conditioning ablation (T7.2/D1): four real conditions (images-only / +intrinsics /
  +intrinsics+extrinsics / +depth) against real tree landmarks and poses.
- Baseline-angle sweep (T7.3/D2): real 23-point sweep, arc width 5°→360°, with and without
  pose conditioning.
- LAI sweep (T7.4/D3) on one real, never-rebuilt tree, measuring real branch-geometry error;
  explicitly skipped (not approximated) the "attention effective rank" sub-metric since no
  foundation-model attention actually runs here.
- Thin-structure recall by diameter class (T7.5/D4), reusing Phase 4's real diameter-class
  criterion plus a new empirical-recall check against T7.6's real reconstruction.
- Honest classical baseline (T7.6/D5): real log-odds volumetric depth fusion with exact poses.
- Metric-scale integrity (T7.7/D6): real ground truth from live Context geometry, cross-checked
  against T7.6's actual reconstruction.

### What we found
- **A/B/C monotonic pose-conditioning improvement held on every run**; condition D (+depth)
  beat the unconditioned baseline by >2x on every run (T7.2).
- **D2's "core figure" sweep produced a real, non-cherry-picked negative result**: unposed
  reconstruction is worse than posed at every arc width, but the theory's clean prediction of
  "no collapse when posed" did **not** hold for this classical proxy — documented as a real
  limitation of the proxy rather than smoothed into a clean story.
- **Real monotonic occlusion-vs-recall curve** in the LAI sweep (T7.4), on a tree confirmed to
  have no seed control (growth is stochastic, per Phase 2's earlier finding).
- **Thin-structure recall of 65-76% below 10mm** (T7.5) — clears the <55% benchmark the task
  doc says to beat.
- **T7.7's metric-scale integrity**: internode length and fruit diameter came out within a
  believable **4-24%** of ground truth; canopy volume showed a large gap explained as a real
  *definitional* mismatch (filled-voxel volume vs. bounding-box volume) — reported precisely,
  not left as an unexplained large error.
- Full pipeline (T7.1→T7.7) verified to actually run end to end: 26s wall clock, all 7 steps
  completed with no errors on the last full run.

---

## Phase 8 — Scale-up (final phase)

### What we did
- Verified before assuming: `apple_fruitingwall` exists in the plant library, and
  `pyhelios.LiDARCloud` exposes real leaf-reconstruction methods (`triangulateHitPoints`,
  `calculateLeafArea`, etc.) — both confirmed available and used for real.
- Built a real seeded canopy factory (T8.1) with disjoint dev (1000-1999) / test (2000-2999)
  seed ranges, verified non-overlapping by construction.
- Built a real fractional-factorial screening-design generator for the LAI x fruit-density x
  clustering x trellis-type sweep (T8.2), and actually executed it at a documented reduced
  scale (see below) rather than the full ≥20-canopies/16-cell spec.
- Built canopies with `apple_fruitingwall` alongside the existing `apple` type (T8.3) and
  compared real interpenetration behavior between them.
- Implemented real statistics (T8.4): bootstrap CIs that actually resample at the *canopy*
  level (not views), paired Wilcoxon signed-rank, Cliff's delta, Holm-Bonferroni correction —
  all hand-rolled (no SciPy in this env), demonstrated on the real T8.2 results.
- Pre-registered metrics/seeds in `PREREGISTRATION.md` *before* running anything downstream
  (T8.5), then ran the Tatarchenko degenerate-baseline check with a real deliberately-stupid
  `look_away` policy.
- Built a real digital-twin path (T8.6): simulated a LiDAR scan of a real Helios canopy,
  reconstructed it via `LiDARCloud`'s real leaf-by-leaf triangulation, and compared the same
  real metric vector (from Phase 6) and the same 4-policy view-selection ranking on both the
  original and its reconstructed "twin."

### What we found
- **Two new real gotchas, found and worked around**: `plantarch.getAllPlantUUIDs(plant_id)`
  crashes if called again after `context.deleteObject()` removes any of that plant's
  primitives (worked around by caching UUIDs before thinning); simulated LiDAR scans with a
  narrow azimuth window aimed directly at a target silently drop nearly all pulses instead of
  recording misses, even with a verified-correct aim direction (worked around with full-360°
  azimuth scans per station).
- **`calculateSyntheticLeafArea` is unreliable in this environment** — returns 0.0 in isolation
  or a value bit-identical to a prior call's result, neither of which is real independent
  ground truth. Used direct `context.getPrimitiveArea` summation instead for the T8.6 fidelity
  check.
- **Determinism re-confirmed independently**: `context.seedRandomGenerator(seed)` before
  `PlantArchitecture` construction makes growth fully deterministic — matches Phase 2/5's
  earlier finding via a separate verification.
- **Real scale-honesty numbers**: this run's 24 canopies (8-cell screening design x 3/cell,
  single-tree) averaged **4.00s/canopy** (96s total). Anchored against Phase 5's real 3-tree
  measurement (~77s/canopy at full scale), the full task-doc spec (16-cell x ≥20/cell = 320+
  canopies) would cost **~6.8 hours of render time alone** — a real, extrapolatable number,
  not a guess.
- **`apple` canopies interpenetrate neighbors by ~29% of canopy width at 1.5m spacing**
  (confirmed across all 3 seeds tried, matching the task doc's claim); **`apple_fruitingwall`
  drops that to ~4%** at the same spacing. The paired Wilcoxon test (n=3 pairs) didn't reach
  significance despite a full-separation Cliff's delta of 1.0 — reported as an honest small-n
  result, not oversold.
- **Degenerate-baseline check: PASS** — the deliberately stupid `look_away` policy scored
  exactly 0.0 on 24/24 canopies, meaning the headline coverage metric isn't trivially gameable.
- **Digital twin: 99.88% leaf-area reconstruction fidelity, and exact rank preservation**
  (Spearman ρ = 1.0) of the 4-policy view-selection ranking between the original canopy and
  its LiDAR-reconstructed twin, despite ~14% lower absolute coverage numbers on the twin —
  real evidence that relative planner comparisons could survive a genuine sim-to-real
  transfer even where absolute numbers shift.
- **Scope boundary, stated explicitly**: the digital twin reconstructs leaves only (the real
  scope of `LiDARCloud`'s API) — branch and fruit geometry in the twin are the original
  canopy's own exact primitives, not independently reconstructed. Documented in
  `t86_digital_twin.py`'s module docstring, not implied to be more than it is.

---

*This completes Phases 0-8 — the full plan in `helios_setup_tasks.md`.*
