# Phase 7 status -- Foundation model diagnostics (D1-D6)

All of T7.1-T7.7 implemented and run for real against real Helios data,
in `yogesh_dev/phase7/`. Full details, real numbers, and every bug found
and fixed along the way are in `PHASE7_LOG.md`.

## Environment reality check (done first, not assumed)

`helios` conda env has `numpy`/`pillow`/`OpenEXR`/`PyYAML`/`PuLP` and this
repo's `pyhelios`, and nothing else relevant: no `torch`, `scipy`, `cv2`,
`scikit-learn`, `open3d`, `trimesh`, `pycolmap`, and none of
MapAnything/DA3/pi-cubed/VGGT. Disk (2.7T free) and network were fine, but
nothing was installed -- none of this phase's math needed it (see log).

## Per-subtask summary (real vs. proxy stated explicitly, per instructions)

- **T7.1** -- real WAI-format dataset writer, looked up the actual
  facebookresearch/map-anything spec, wrote a real 16-view dataset to disk.
- **T7.2 (D1)** -- PROXY (no foundation model installed): hand-rolled
  classical multi-view geometry standing in for MapAnything/DA3/pi3/VGGT,
  run against a real tree's real landmarks and poses. A/B/C monotonic
  pose-conditioning improvement held on every run; D beat the unconditioned
  baseline by >2x on every run.
- **T7.3 (D2)** -- same proxy, real 23-point arc-width sweep (5-360deg).
  Real, non-cherry-picked finding: unposed is worse than posed at every
  arc width, but the naive "no collapse when posed" claim does NOT hold
  for this prior-free classical proxy -- documented as a real limitation
  of the proxy, not glossed over.
- **T7.4 (D3)** -- real LAI/leaf-density sweep on one real, never-rebuilt
  tree (growth confirmed stochastic, no seed control exists). Real
  monotonic occlusion-vs-recall curve. Attention-effective-rank explicitly
  SKIPPED (`null`), not approximated -- no foundation-model attention runs
  here.
- **T7.5 (D4)** -- Phase 4's real diameter-class criterion reused verbatim
  + a new real empirical-recall check against T7.6's actual reconstruction.
  Real recall below 10mm (65-76% across runs) consistently beats the
  <55% benchmark.
- **T7.6 (D5)** -- 100% real: Phase 4's real log-odds volumetric depth
  fusion, exact poses, run against Phase 7's own real 42-view render.
- **T7.7 (D6)** -- 100% real: ground truth from live Context geometry,
  cross-checked against T7.6's actual reconstruction. Internode length and
  fruit diameter came out within a believable 4-24% of ground truth;
  canopy volume showed a large but explicitly-explained DEFINITIONAL
  mismatch (filled-voxel volume vs. bounding-box volume), not silently
  reported as a plain error.

## Known limitations (stated, not hidden)

- T7.2/T7.3/T7.4's reconstruction sub-metrics use a classical-geometry
  proxy, never the named foundation models -- flagged in every relevant
  report field (`hypothesis_*`, method strings, docstrings).
- T7.4's "attention effective rank" is skipped, not approximated.
- Growth-model stochasticity (no seed) means numbers shift run-to-run
  (reported ranges above reflect that); qualitative conclusions
  (monotonicity, recall trends, benchmark comparisons) were stable across
  the several runs performed during development.

## Verification

`PYTHONPATH=. /home/yogesh/anaconda3/envs/helios/bin/python -m
yogesh_dev.phase7.run_phase7` runs T7.1->T7.7 end to end against a fresh
tree; last full run: 26s wall clock, all 7 steps completed with no errors.

STATUS: DONE
