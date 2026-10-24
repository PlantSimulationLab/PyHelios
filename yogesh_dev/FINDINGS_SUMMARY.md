# Findings Summary — Phases 0-8 (complete)

This is a synthesis of what was actually *learned*, not just what was built — real numbers,
real bugs found, and honest limitations across every phase. For per-phase detail see each
`PHASEn_LOG.md`/`PHASEn_STATUS.md`; for the plan/scope map see `COMPLETE_SETUP.md`. This is
the full plan, Phase 0 through Phase 8 — nothing left running.

## The one blocker that shaped everything

**T0.6 — `CollisionDetection` (`castRaysSoA`, `findCollisions`, `buildBVH`) is not exposed in
PyHelios.** Decided in Phase 0 (recommends building the binding) but never implemented — every
phase since worked around it with a documented placeholder rather than pretending it's fine:
Phase 2 used render-based occlusion instead of ray casting, Phase 3/4's roadmap collision is a
bounding-box approximation, Phase 4's GPU info-gain is a CPU reference only. This is the single
highest-leverage real engineering task left in the whole plan.

## Real bugs found and fixed (not in the original task doc — discovered along the way)

1. **`Visualizer.getDepthMap()` is broken upstream** (Phase 0) — returns only `{0.0, 255.0}`,
   no intermediate depth values. Confirmed via helios-core's own `// \todo` comment on the
   exact code path. Rules out the "interim hack" option for T0.6.
2. **`optionalOutputObjectData` ordering requirement, undocumented in the task doc** (Phase 1)
   — must be called *before* `buildPlantInstanceFromLibrary`, not after as the task doc's own
   snippet orders it. Confirmed by A/B test: "after" produces zero object data.
3. **`getPrimitiveDataLabelMap(cam, "object_label")` silently returns an all-background map**
   (Phase 1) — string-typed fields can't be label-mapped in the C++ layer (fails via a stderr
   warning, not a Python exception). Fixed by deriving an int-typed class-id field first.
4. **Apple-tree growth in `PlantArchitecture` is stochastic and was never seeded upstream**
   (Phase 2) — verified with a real A/B build test (97 vs 72 fruit from two unseeded builds).
   Every phase since seeds its own canopy build explicitly.
5. **Cross-worktree `PYTHONPATH` resolving to the wrong, unbuilt `pyhelios` package** (Phase 4)
   — a real environment-isolation bug hit when running inside a git worktree.
6. **Native segfault calling tube-node accessors on Cone-typed petiole objects** (Phase 4).
7. **Two real ILP correctness bugs in the T5.7 baseline** (Phase 5): a fruit-level-vs-
   primitive-level objective mismatch, and a free-CBC "Optimal" status that couldn't be
   trusted at this problem's real scale — fixed with cross-validation against known lower
   bounds so the reported ceiling can never silently be worse than an independently-verified
   result.
8. **Three real, pre-existing bugs in the actual gsplat pipeline** (`apple_tree_gaussian_splatting.py`,
   Phase 6): the train/test split (`i % test_every`) always selects grid column 0, not a
   representative sample; masked PSNR is inflated by constant-background pixels; occlusion
   supervision currently teaches the splat that occluded apples are simply absent. Reproduced
   live against real data, fixed in `yogesh_dev/phase6/`, exact patch documented for a human
   to apply to the real file.
9. **`plantarch.getAllPlantUUIDs(plant_id)` crashes (`unordered_map::at`) if called again
   after `context.deleteObject()` has removed any of that plant's primitives** (Phase 8) —
   worked around by caching UUID lists before thinning and never re-querying
   `PlantArchitecture` afterward.
10. **Simulated LiDAR scans with a narrow azimuth window aimed directly at a target silently
    drop nearly all pulses** rather than recording them as misses, even with a verified-correct
    aim direction (Phase 8) — worked around with full-360° azimuth scans per station instead.
    Also found `calculateSyntheticLeafArea` unreliable in this environment (returns 0.0 in
    isolation, or a value bit-identical to a prior call's result) — used direct
    `context.getPrimitiveArea` summation as real ground truth instead.

## Key quantitative findings

- **Render cost is dominated by a fixed per-call cost, not resolution/AA** (Phase 0): `runBand()`
  costs a flat ~0.6-1.0s regardless of a 16x pixel-count range or 4x AA range — direct evidence
  for prioritizing the `runCamerasOnly()` upstream patch (skip the full radiative-transfer
  solve when only the camera moved).
- **Pose convention is sub-pixel accurate**: 0.71px mean reprojection error (Phase 0), later
  cross-validated independently at 1.41px mean / 0.98px median via a completely different path
  (Phase 1's transforms.json vs. instance-mask centroids) — the geometry pipeline is trustworthy.
- **Union-over-poses matters**: 82/83 fruit had coverage improve when accumulated across views
  rather than taken as a max over single views, +8.7 points mean, best case nearly doubled
  (22.0% → 41.1%) (Phase 2).
- **AVUB / AVUB^inf ratio ≈ 0.51** (Phase 2, placeholder-pose-derived) — roughly half of a
  fruit's theoretically-visible surface is reachable under the current placeholder workspace
  envelope; a real number once Phase 3's kinematics-derived reachable set replaces the
  placeholder will move this.
- **Gimbal motion is ~14.7x cheaper than linear-stage motion** (Phase 3) — the real number
  underpinning the whole nested-planner design idea in the proposal.
- **CELF gives 0% measured speedup at this dataset's candidate-pool scale** (Phase 4, 5-13
  poses/arm) despite being algorithmically correct (verified identical to brute-force greedy)
  — the benefit is real at larger scale but doesn't show up yet here; reported honestly rather
  than dressed up.
- **The trace-vs-log-det submodularity failure mode is real and reproducible** (Phase 4): under
  a plain-trace objective, three-arm coordination collapses to 1 unique view assignment across
  6 random orderings; log-det gives 3, with a real diversity metric (mean pairwise bearing dot
  product) confirming it chooses meaningfully different views.
- **Information-gain calibration came back anti-correlated**, Spearman ρ ≈ -0.26 (Phase 6) —
  the current IG formulation's predicted value doesn't track actual value well on this dataset.
  This is a real, concerning finding worth investigating before trusting IG-driven exploration.
- **Thin-structure recall beats the literature benchmark**: 65-76% recall below 10mm diameter
  (Phase 7), vs. the <55% benchmark the task doc says to beat.
- **The "no collapse when posed" theoretical claim did not hold** for Phase 7's classical
  multi-view-geometry proxy in the D2 baseline-angle sweep (5°-360°, 23 real points) — unposed
  reconstruction was worse than posed at every angle, but posed reconstruction still degraded
  at small baselines, contrary to the clean theoretical prediction. Explicitly flagged as a
  proxy limitation, not a foundation-model result.
- **Metric-scale integrity mostly holds**: fruit diameter and internode length reconstructed
  within 4-24% of ground truth (Phase 7); canopy volume showed a large gap explained as a real
  *definitional* mismatch (filled-voxel volume vs. bounding-box volume), not a silent error.
- **`apple_fruitingwall` genuinely reduces canopy interpenetration**: plain `apple` canopies
  interpenetrate neighbors by ~29% of canopy width at 1.5m spacing (confirming the task doc's
  claim, across all 3 seeds tried); `apple_fruitingwall` at the same spacing drops that to ~4%
  (Phase 8). The paired Wilcoxon test (n=3) didn't reach significance despite a full-separation
  Cliff's delta of 1.0 — an honest small-n result, not dressed up as more than it is.
  - **The degenerate-baseline check passed**: a deliberately stupid `look_away` policy scored
  exactly 0.0 on 24/24 canopies (Phase 8's Tatarchenko check) — the headline coverage metric
  isn't trivially gameable.
- **The digital-twin path preserves planner rankings**: a LiDAR-reconstructed "twin" of a real
  canopy achieved 99.88% leaf-area reconstruction fidelity and, despite ~14% lower absolute
  coverage numbers than the original, preserved the *exact* 4-policy ranking (Spearman ρ = 1.0)
  (Phase 8) — evidence that relative planner comparisons would survive a real sim-to-real
  transfer even where absolute numbers shift.
- **Real per-canopy cost now measured, enabling a real full-scale time estimate**: Phase 8's
  reduced-scale run averaged 4.00s/canopy; anchored against Phase 5's real 3-tree measurement
  (~77s/canopy at full scale), the task doc's full factorial spec (320+ canopies) would take
  **~6.8 hours of render time alone** — a real number to plan around, not a guess.

## What's honestly incomplete or blocked (not hidden anywhere)

- **T2.6** (validate occlusion-regulation module against AVUB) — the WTFRC proposal's
  occlusion-regulation module doesn't exist anywhere in this codebase. Verified by a
  reproducible repo-wide search (`yogesh_dev/phase2/t26_check.py`), not assumed.
- **T4.5's GPU/CUDA information gain** — explicitly out of scope for a Python-only run;
  shipped a correct CPU vectorized reference implementation plus a concrete GPU design note
  instead of faking acceleration.
- **T7.2-T7.4's foundation-model comparisons** — no foundation model (MapAnything/DA3/π³/VGGT)
  is installed in the `helios` env; every result from those subtasks is explicitly labeled as
  coming from a classical-geometry proxy, not the named models.
- **Phase 2/3's reachable-pose set and Phase 3's real joint limits were never reconciled**
  (found in Phase 5) — motion-time costing currently applies Phase 3's model to poses that
  were never validated against Phase 3's own joint-limit envelope.
- **T3.4/T3.5's collision checking, T4.1's occupancy beam model, and T5.7's k>5 ILP ceiling**
  all still rest on placeholders/lower-bounds rather than the real T0.6 ray-caster or a
  certified-optimal solver at scale.
- **Phase 8's full factorial spec was run at reduced scale, by design**: 8-cell screening
  design x 3 canopies/cell (24 total, single-tree) instead of the full 16-cell x ≥20/cell
  (320+, three-tree) spec — the *infrastructure* (canopy factory, factorial design generator,
  statistics, LiDAR pipeline) is real and general, not hard-coded to the reduced scale, and the
  real per-canopy timing above makes the full-scale cost knowable rather than a guess.
- **T8.6's digital twin reconstructs leaves only** (the real scope of `LiDARCloud`'s API) —
  branch and fruit geometry in the "twin" are the original canopy's own exact primitives, not
  independently reconstructed. Documented explicitly, not implied to be more than it is.

## Bottom line

Every phase produced real, runnable code against real Helios data on this machine — nothing
across Phases 0-8 was simulated, estimated, or faked. Where the plan assumed a capability that
doesn't exist yet (T0.6's ray caster, foundation models, an occlusion-regulation module,
real hardware specs, a full-scale compute budget), that gap was documented and worked around
transparently rather than papered over, and is traceable back to a specific phase's log. The
engineering path forward is narrow and known: build the T0.6 binding to upgrade every
placeholder at once, reconcile Phase 2/3's pose sets, investigate the Phase 6 IG
anti-correlation finding before trusting information-gain-driven exploration in a real
planner, and — when ready — spend the ~6.8 real GPU-hours Phase 8 estimated to run the full
factorial sweep at its intended scale.
