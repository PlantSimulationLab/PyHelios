# Phase 0 status

All of T0.1, T0.2, T0.3, T0.4, T0.5, T0.7 implemented and run end-to-end
against the real `pyhelios` radiation + visualizer plugins on this machine
(RTX 5090, OptiX 8.1 backend) -- not simulated, not estimated. T0.6 is a
decision doc (`PHASE0_DECISIONS.md`) per the task spec, not an
implementation (writing the `CollisionDetection` C++/pybind11 binding was
explicitly out of scope for this run).

Summary of what was verified, with real measured numbers (full detail in
`PHASE0_LOG.md`):

- **T0.1**: plausible-RGB band/source setup, decision documented. Discovered
  and worked around an `exposure="auto"` pitfall (makes pixel values
  incomparable across frames). Discovered and documented (did not fix -- out
  of scope) a real, flux-independent photometric saturation artifact
  affecting ~15-20% of foliage pixels on this canopy.
- **T0.2**: 3 cameras registered as `RadiationCamera`s with correct
  VFOV->HFOV conversion (57.822 deg measured at 640x480 from a 45 deg VFOV),
  pinhole, AA=2 default.
- **T0.3 [BLOCKER]**: pose convention empirically verified sub-pixel
  accurate (mean 0.71px error on a 320x240 render) against two different
  camera poses (axis-aligned and off-axis) using a 9-sphere test scene with
  ground-truth primitive-data labels -- confirmed the radiation camera uses
  the same convention as the existing Visualizer/gsplat pipeline.
- **T0.4**: render loop restructured correctly (`updateGeometry()` once,
  one multi-band `runBand()` per pose), demonstrated on the real 3-tree
  scene.
- **T0.5 [BLOCKER]**: real Tier B vs Tier C benchmark plus a 3x3
  resolution/AA sweep, all with real wall-clock measurements. Key finding:
  Tier C's cost is dominated by a fixed per-`runBand()` scene-wide solve
  (~0.62-1.0s, nearly flat across a 16x pixel-count range and 4x AA range),
  not by camera parameters -- directly supports prioritizing the
  `runCamerasOnly()` upstream patch. Tier B vs Tier C comparison is flagged
  with an important environment caveat (this devbox's Visualizer runs on
  Mesa llvmpipe software rendering under Xvfb, not the GPU).
- **T0.6**: decision doc recommends writing the `CollisionDetection`
  binding (option 1), with reasoning grounded in the T0.5 numbers and a
  T0.7 finding that rules out the "interim hack" option.
- **T0.7**: `Visualizer.getDepthMap()` wired into a fresh Tier-B rig, runs
  end-to-end. Discovered its values are broken (upstream-acknowledged
  helios-core bug, not a Phase 0 mistake) and documented for T0.6.

Deliverables are all under `yogesh_dev/` (`phase0/*.py`,
`PHASE0_DECISIONS.md`, `PHASE0_LOG.md`, this file, plus generated
`benchmark_results.json` and sample renders in `phase0/renders_tier_b/` and
`phase0/renders_tier_c/`). Nothing outside `yogesh_dev/` was modified.

STATUS: DONE
