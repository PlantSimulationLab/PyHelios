# Phase 3 Status

All of T3.1–T3.5 implemented under `yogesh_dev/phase3/`, run for real against
the actual Phase 1 fruit ground-truth geometry (73 fruit objects, 3 trees),
not synthetic/fabricated numbers. See `PHASE3_LOG.md` for full detail.

## Deliverables

- `yogesh_dev/phase3/kinematics.py` — T3.1 (5-DOF FK, hand-rolled, no
  external kinematics library) + T3.2 (closed-form IK). Round-trip
  FK(IK(pose)) verified to ~1e-14 across all 3 arms, 3125 samples/arm.
- `yogesh_dev/phase3/motion_time.py` — T3.3 trapezoidal velocity profile,
  placeholder linear-stage vs. gimbal specs, ~14.7x cost asymmetry
  demonstrated with real numbers.
- `yogesh_dev/phase3/roadmap.py` — T3.4 discretized joint-space roadmap,
  placeholder (bounding-box) collision rejection, k-NN graph weighted by
  real T3.3 execution time, Dijkstra shortest-path demo.
- `yogesh_dev/phase3/arm_geometry.py` — T3.5 vertical-band non-overlap proof
  (pure interval math) + live Helios Context geometry cross-check via
  `getDomainBoundingBox`.
- `yogesh_dev/phase3/run_phase3_demo.py` — runs all of the above end to end;
  actually executed, not just defined (see PHASE3_LOG.md for full output).
- `yogesh_dev/phase3/reference_data/fruit_ground_truth.json` — copy of
  Phase 1's real ground-truth export, used as the realistic geometry input.

## Known placeholders (explicitly documented in-code and in the log, not hidden)

- All joint limits, vertical bands, and T3.3 velocity/acceleration numbers
  are placeholders pending real hardware measurements (no hardware spec
  exists yet) — flagged in `kinematics.py`/`motion_time.py` docstrings.
- T3.4's collision rejection is a coarse per-plant fruit-bounding-box point
  test, explicitly NOT real per-primitive ray-traced collision. Precisely
  documented in `roadmap.py`'s module docstring and in PHASE3_LOG.md what
  changes once T0.6 lands.
- T3.5 checks arm-vs-arm collision (structurally impossible by construction)
  but NOT arm-vs-canopy collision, which needs T0.6.

## Blocked on T0.6 (not done in any phase so far)

`CollisionDetection` (`castRaysSoA`/`findCollisions`/`buildBVH`) is not
exposed in PyHelios. This blocks: real per-primitive collision rejection in
the T3.4 roadmap, arm-vs-canopy collision checking in T3.5, and continuous
(as opposed to discrete-node) path collision checking. See PHASE3_LOG.md's
"What remains blocked on T0.6" section for the complete, itemized list.
None of this was faked — the roadmap-building and graph-search machinery
itself is real and runs against real geometry; only the collision predicate
underneath it is a documented placeholder.

STATUS: DONE
