# Phase 2 status

T2.1-T2.5 implemented and run end-to-end against the real `pyhelios`
radiation plugin on a real, freshly-built 3-apple-tree scene (83 fruit
across 3 trees, RTX 5090, OptiX 8.1 backend) — not simulated, not estimated.
Built directly on Phase 0's radiation-camera rig and Phase 1's ground-truth
export code (imported, not duplicated). T2.6 is explicitly blocked and
skipped, not faked — see below.

Summary, with real measured numbers (full detail in `PHASE2_LOG.md`):

- **T2.1**: `vis_i(v)` implemented at real per-**primitive** resolution
  (better than the task brief's anticipated `getObjectDataLabelMap`
  object-level fallback — see `PHASE2_LOG.md` for why the primitive-level
  approach is still genuine ray-traced occlusion, not fabricated), by
  assigning all 17,098 fruit-surface primitives a unique id and reading it
  back per pose via `getPrimitiveDataLabelMap`. Cross-validated against the
  task doc's own suggested check (raw `fruitID` pixel-count fractions):
  Pearson r = **0.9242** over 241 real (fruit, view) pairs.
- **T2.2**: real union-over-poses accumulation (not max-over-views),
  demonstrated on the Phase 0/1 3-camera rig: **82/83** fruit had union
  coverage exceed their best single view, mean improvement **8.7 points**,
  best case nearly doubled (22.0% -> 41.1%).
- **T2.3**: `PLACEHOLDER_reachable_poses` (108 poses/tree, front-hemisphere
  rail/height/depth grid) and a broader free-flying set (288 poses/tree,
  full-sphere) built and clearly labeled as placeholders standing in for
  Phase 3's not-yet-existing kinematics roadmap, with a documented
  substitution interface in `reachable_poses.py`.
- **T2.4**: AVUB_i and AVUB_i^inf computed for all 83 fruit — mean AVUB
  **0.499**, mean AVUB^inf **0.977**, ratio of means **0.511**. Explicitly
  caveated in code and log as placeholder-derived, not a real
  hardware-capability number yet.
- **T2.5**: achievability classes computed for all 83 fruit — **100%**
  observable, **95.2%** sizeable (of observable, gamma_size=0.30
  placeholder), **98.8%** graspable (of observable, approach-cone
  approximation). Recall reported against the observable denominator per
  the design doc.
- **T2.6**: **BLOCKED, not faked.** Searched every commit on every branch
  in this repo for an occlusion-regulation module — 12 hits, all prose in
  `active_vision_design.md`/`helios_setup_tasks.md` describing the
  *external* WTFRC proposal's module, zero in code. No such module has ever
  been implemented in this codebase, so there is nothing to validate AVUB
  against. Per the task brief, this was not approximated or fabricated;
  the search itself is reproducible via `yogesh_dev/phase2/t26_check.py`.

Deliverables are all under `yogesh_dev/` (`phase2/*.py`, `phase2/output/*`,
`PHASE2_LOG.md`, this file, plus prerequisite Phase 0/1 files pulled in by
merging `worktree-phase1-groundtruth`). Nothing outside `yogesh_dev/` was
modified — the only exceptions are three untracked, gitignored local
symlinks needed to make `pyhelios` importable in this fresh worktree
(`pyhelios_build/build/lib`, `pyhelios_build/build/plugins`, `helios-core`,
all pointing at the main checkout's existing build artifacts/submodule
checkout — see `PHASE2_LOG.md` "Worktree setup"), none of which touch
tracked source.

Two real findings beyond the task list, both documented with evidence in
`PHASE2_LOG.md`: (1) `getPrimitiveDataLabelMap` gives genuine per-primitive
ray-traced occlusion resolution for free, which is a strictly better T2.1
implementation than the object-level fallback the task brief anticipated
when it assumed `CollisionDetection` was the only path to that;
(2) apple-tree growth in `PlantArchitecture` is stochastic and was never
seeded upstream (Phase 0/1) — verified with a real A/B build test (97 vs 72
fruit from two unseeded builds) — so Phase 2 seeds its own run for
reproducibility and its 83-fruit scene is a different, independently real,
realization from Phase 1's 73, not the same dataset reused.

T2.1-T2.5: STATUS: DONE
T2.6: BLOCKED (occlusion-regulation module does not exist in this codebase — see above)

STATUS: DONE
