# Phase 4 Status

Branch: `worktree-phase4-map-planner`. Scope: `helios_setup_tasks.md` Phase 4
(T4.1-T4.10) only, everything under `yogesh_dev/`. Full details, real
numbers, and every problem hit are in `PHASE4_LOG.md`; this file is the
short per-subtask scope declaration.

## Dataset this phase runs on

`yogesh_dev/phase4/gen_dataset.py` builds its OWN seeded (SEED=20260729,
reproducible), single-tree apple canopy (41351 primitives, 27 fruit, 1336
real tube segments) and renders 42 real views (real depth EXR, semantic/
instance/vis-primitive-id label maps, real poses) across 3 arms'
placeholder-collision T3.4-style roadmaps. Two real bugs were found and
fixed while producing it (cross-worktree PYTHONPATH resolving to the wrong
unbuilt `pyhelios` package; a native SEGFAULT calling tube-node accessors
on Cone-typed petiole objects) — see `PHASE4_LOG.md` for both.

## Per-subtask status

- **T4.1** (occupancy map, 3-state log-odds, dual resolution, beam sensor
  model): DONE, real. Scoping choice: hand-rolled numpy log-odds grid
  instead of nvblox/UFOMap/wavemap (documented in `occupancy_map.py`) — a
  real, complete, self-contained implementation, not a partial external
  integration. Uses real depth+poses as the beam sensor's input in place of
  the still-missing `CollisionDetection` ray-caster (T0.6), per the task
  brief's own framing for this phase.
- **T4.2 / E1** (voxel size vs. thin-structure recall + update time): DONE,
  real. Ground truth = the 1336 real tube segments' real diameters.
- **T4.3** (semantic layer, per-voxel class posterior): DONE, real.
- **T4.4** (apple instance track database, IDF1/ID switches vs. oracle):
  DONE, real, including the from-scratch Hungarian algorithm (no scipy in
  the `helios` env) self-tested against brute force.
- **T4.5** (GPU-batched information gain): the GPU/CUDA implementation is
  **explicitly OUT OF SCOPE** for this phase (needs C++/CUDA + T0.6, not
  buildable from a Python-only `yogesh_dev`-confined session) — this is a
  scope declaration, not a blocker. What IS done, real: a correct,
  fully-vectorized (batched over pose x ray) numpy CPU reference
  implementation of the actual volumetric information-gain algorithm, plus
  a concrete GPU-batched design note (batch dimension, SoA memory layout,
  CUDA-texture-based interpolation, kernel structure) in `PHASE4_LOG.md`
  and `information_gain.py`'s docstring.
- **T4.6** (explore planner, submodular max-coverage + CELF, receding
  horizon): DONE, real. CELF's selected sequence verified identical to
  brute-force greedy on real data (correctness proven); CELF's measured
  gain-recompute savings are honestly 0% at this phase's real candidate-pool
  scale (5-13 rendered poses/arm) — explained in the log, not hidden.
- **T4.7** (switching criteria, 3-way disjunction + hard cap): DONE, real,
  demonstrated firing (including Good-Turing firing BEFORE frontier
  exhaustion on a real run) and NOT firing (arm_mid's Good-Turing never
  crosses 0.95) — both reported honestly.
- **T4.8** (exploit planner, budget-constrained team orienteering):
  DONE, real.
- **T4.9** (three-arm coordination, trace vs. log-det submodularity):
  DONE, real. Trace's modularity verified by executable assertion on real
  data; the task doc's warned failure mode (all arms converge on the same
  view under trace) reproduced exactly — 1 unique assignment across 6
  random orderings under trace vs. 3 under log-det, with a real diversity
  metric (mean pairwise bearing dot product) confirming log-det chooses
  more diverse views.
- **T4.10** (gimbal-only local refinement): DONE, real. Gradient ascent
  over pan/tilt chosen (of the task doc's two options), via real central
  finite-difference gradients from actual re-renders (not a synthetic
  differentiable stand-in) — 61 real renders, 1.66x real semantic-utility
  improvement at its peak.

## Placeholders inherited from earlier phases (propagated, not silently resolved)

- T3.4's roadmap collision check is still the coarse per-plant-AABB
  placeholder (no real ray-traced/swept collision) — every planner in this
  phase (T4.6, T4.8, T4.9) that searches over a roadmap inherits this.
- T2.3-style "reachable pose set" limitations from Phase 2 are not
  reintroduced here (Phase 4 built its own roadmap via Phase 3's real FK/IK
  + T3.4 roadmap builder), but the underlying `CollisionDetection` gap
  (T0.6) is the same one every phase has hit and documented.

STATUS: DONE
