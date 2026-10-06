# Phase 1 status

All of T1.1-T1.6 implemented and run end-to-end against the real `pyhelios`
radiation plugin on the real 3-apple-tree scene (RTX 5090, OptiX 8.1
backend) -- not simulated, not estimated. Built directly on Phase 0's
validated radiation-camera rig, render loop, and pose convention (copied
into this worktree's `yogesh_dev/phase0/` unmodified, since this worktree
also branched from `origin/master` rather than `apple-tree-cameras` -- see
`PHASE1_LOG.md` for why).

Summary, with real measured numbers (full detail in `PHASE1_LOG.md`):

- **T1.1**: `optionalOutputObjectData` enabled and verified with a real
  `context.listObjectData()` call on a real fruit object from the actual
  3-tree scene -- all 4 checkable labels (`fruitID`, `rank`, `age`,
  `phenology_stage`) present. Found and corrected two real gotchas not in
  the task doc: (1) the call must happen *before*
  `buildPlantInstanceFromLibrary`, not after as the task doc's own snippet
  orders it -- confirmed by an A/B test where the "after" ordering produces
  zero object data; (2) `plantID` is never set on fruit objects at all, so
  it's derived via a uuid->plant_id lookup instead.
- **T1.2**: `fruit_ground_truth.json` exported -- 73 fruit objects across 3
  trees in this run (object id, plant id, centroid, bbox, equivalent
  diameter, surface area, primitive UUID list, plus bonus `fruitID`/`rank`/
  `age`/`phenology_stage` fields already available from T1.1).
- **T1.3**: per-pixel semantic (`semantic_class_id`, derived from the
  string `object_label` field) and instance (`fruitID`) label maps for all
  9 views. Found and worked around a real issue: the task doc's own
  `getPrimitiveDataLabelMap(cam, "object_label")` snippet silently returns
  an all-background map (C++ can't label-map a string field; it fails via a
  `stderr` warning, not a Python exception) -- fixed by deriving an
  int-typed class-id field first.
- **T1.4**: real EXR depth files via `writeDepthImageDataEXR`, read back
  with the `OpenEXR` package (installed into the `helios` env for this
  task). Found and documented a real, previously-undocumented fact: sky/
  no-hit pixels are exactly `depth == -1.0`, verified pixel-for-pixel
  aligned with the semantic map's background mask.
- **T1.5**: `transforms.json` with the RadiationCamera's actual HFOV
  (57.822 deg, matches Phase 0's number), derived `K`, and the T0.3-validated
  world-to-camera convention, in the same gsplat-compatible field layout the
  existing `apple_tree_gaussian_splatting.py` pipeline already reads.
  Cross-checked T1.2+T1.3+T1.5 against each other (not requested, done as
  an extra integration check): projecting 219 real (fruit, view) pairs
  through T1.5's intrinsics/extrinsics and comparing against T1.3's measured
  instance-mask centroids gives 1.41 px mean / 0.98 px median error --
  consistent with T0.3's sub-pixel validation, confirming all three
  artifacts agree with each other on a real render.
- **T1.6**: toggleable RGB-D noise model (range-dependent Gaussian noise +
  depth-edge mixed pixels pulled toward the real discontinuity partner).
  Threshold was tuned against the *actual* depth-gradient distribution of
  this cluttered canopy scene after a first attempt (RealSense-typical
  0.03 m threshold) proved far too aggressive here (37% of pixels flagged,
  RMSE 70 cm) -- final result: ~4 cm mean / ~7 cm RMSE depth change,
  quantified and reproducible (seeded) via `compare_before_after`.

Deliverables are all under `yogesh_dev/` (`phase0/*.py` copies,
`phase1/*.py`, `phase1/output/*`, `PHASE1_LOG.md`, this file). Nothing
outside `yogesh_dev/` was modified. No upstream bugs were silently worked
around without comment -- both real issues found (the string-typed
`object_label` label-map failure and the `optionalOutputObjectData`
ordering requirement) are documented in `PHASE1_LOG.md` alongside the fix
actually used.

STATUS: DONE
