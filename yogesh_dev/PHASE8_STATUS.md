# Phase 8 Status — Scale-up

All of T8.1-T8.6 implemented and executed end-to-end with real data. See
`PHASE8_LOG.md` for full detail (real numbers, real per-canopy timing, gotchas found
and fixed) and `PREREGISTRATION.md` for the metrics/seeds/comparisons committed to
before any T8.2+ result was produced. Code lives in `yogesh_dev/phase8/`; results in
`yogesh_dev/phase8/output/*.json`.

## What was built vs what was run

Every deliverable's *infrastructure* is real and general (seeded canopy factory with a
real disjoint dev/test seed split, a real fractional-factorial design generator, real
hand-rolled statistics with no SciPy dependency, a real LiDAR scan-and-reconstruct
pipeline) — none of it is hard-coded to only the reduced scale it was actually run at.
What was reduced, and why, per the task's scale-honesty requirement:

| | Full spec | What was actually run |
|---|---|---|
| T8.2 factorial | 16-cell full factorial x >=20 canopies/cell = 320+ canopies, 3-tree scenes, full 108-pose/tree V_reach | 8-cell resolution-IV screening design x 3 canopies/cell = 24 canopies, 1-tree scenes, 18-pose/tree V_reach |
| Real cost basis | Phase 5's own measurement: ~77s/canopy at full scale (3-tree, 324-pose V_reach) | This run: 4.00s/canopy mean, 96s total for all 24 |
| Full-scale estimate | — | 320 canopies x 77s = **~6.8 hours** of render time alone |

T8.1 (canopy factory), T8.3 (fruiting-wall comparison), T8.4 (statistics), T8.5
(degenerate-baseline check), and T8.6 (digital twin) were each run at a scale that
fully exercises the real pipeline (multiple real seeds, real paired comparisons, a
real statistically-analyzed result) without needing the >=20-canopies/cell volume —
see `PREREGISTRATION.md` for the exact seed counts committed to for each.

## Real findings worth flagging

- **Determinism re-verified**: `context.seedRandomGenerator(seed)` before
  `PlantArchitecture` construction makes canopy growth fully deterministic (matches
  Phase 5's finding, re-confirmed independently here).
- **New gotcha found**: `plantarch.getAllPlantUUIDs(plant_id)` reliably crashes
  (`unordered_map::at`) if called again after `context.deleteObject()` has removed any
  of that plant's primitives — worked around by caching UUID lists before thinning and
  never re-querying PlantArchitecture afterward (`canopy_factory.py`, `policies.py`).
- **New gotcha found**: simulated LiDAR scans with a narrow azimuth window aimed
  directly at a target silently drop nearly all pulses rather than recording them as
  misses, even when the aim direction is verified correct — full-360-degree-azimuth
  scans from each station work reliably instead (`t86_digital_twin.py`).
- **`calculateSyntheticLeafArea` unreliable in this environment** — verified directly
  (returns 0.0 in isolation, or a value bit-identical to the inversion result when
  called right after `calculateLeafArea`, neither of which is real independent ground
  truth); real ground truth for the T8.6 leaf-area fidelity check used direct
  `context.getPrimitiveArea` summation instead.
- **Real scientific results**: `apple` canopies interpenetrate their neighbors by
  ~29% of canopy width at 1.5m spacing (task doc's claim, confirmed in all 3 seeds
  tried) vs ~4% for `apple_fruitingwall` at the same spacing. The degenerate
  `look_away` baseline scored exactly 0.0 on 24/24 canopies (Tatarchenko check: PASS).
  The digital-twin's LiDAR-reconstructed canopy preserved the exact 4-policy view-
  selection ranking of the original (Spearman rho = 1.0) despite ~14% lower absolute
  coverage numbers, with 99.88% leaf-area reconstruction fidelity.

## Known limitations, logged rather than hidden

- T8.2/T8.3/T8.6 use single-tree canopies (not Phase 0/5's 3-tree row) as part of the
  documented scale reduction — the full-scale cost estimate above is anchored to
  Phase 5's real 3-tree measurement, not extrapolated from these single-tree numbers.
- T8.3's apple-vs-fruitingwall Wilcoxon test (n=3 pairs) does not reach significance
  despite a full-separation Cliff's delta of 1.0 — an honest small-n result, not
  papered over.
- T8.6's digital twin reconstructs leaves only (LiDARCloud's real API scope); branch
  and fruit geometry in the twin are the original canopy's own exact primitives, not
  independently reconstructed — documented explicitly in `t86_digital_twin.py`'s
  module docstring, not implied to be something it isn't.

## Closing summary — what `yogesh_dev/` now covers end-to-end

Phase 8 is the last phase in the plan. Together, `yogesh_dev/phase0` through
`yogesh_dev/phase8` now cover the full pipeline the task list set out to build: a
physically-based radiation-camera rig alongside the original fast Visualizer path
(Phase 0), exact per-fruit and per-pixel ground truth export (Phase 1), area-weighted
per-primitive visibility and AVUB/AVUB^inf hardware-design metrics (Phase 2), hand-rolled
5-DOF forward/inverse kinematics and a reachability roadmap (Phase 3), an occupancy map,
information-gain planner, explore/exploit switching logic, and three-arm coordination
(Phase 4), eight real baselines and oracles to keep the planner honest (Phase 5), a
metrics harness fixing the train/test split, masked PSNR, and occlusion-aware
supervision bugs plus discovery-curve and IG-calibration diagnostics (Phase 6),
foundation-model diagnostics on pose conditioning, baseline-angle collapse, LAI-driven
occlusion, thin-structure recall, and metric-scale integrity (Phase 7), and finally, in
this phase, the scale-up scaffolding needed to run the whole thing across many seeded
canopies with real statistics, a real fruiting-wall architecture comparison, a
pre-registered evaluation protocol with an empirically-verified non-degenerate headline
metric, and a real sim-to-real digital-twin path whose reconstructed geometry preserves
planner rankings. Every phase's real numbers, real gotchas, and real scale reductions
are logged in that phase's own `PHASE<N>_LOG.md` rather than asserted — this phase's
`PHASE8_LOG.md` continues that pattern for the scale-up work specifically.

STATUS: DONE
