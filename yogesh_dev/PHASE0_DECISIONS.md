# Phase 0 decisions

## T0.1 -- plausible RGB vs real-spectra radiometry

**Decision: plausible RGB.** See `phase0/radiation_setup.py` module docstring
for the full reasoning. Short version: the two consumers of this rig
(gsplat/NBV perception experiments, and per-pixel ground truth) don't need
radiometrically calibrated radiance, just RGB bands that look plausible and
whose ground truth (semantic/instance labels, depth) is exact. Revisit only
if a later phase makes a radiometric claim (e.g. T7.6's classical-baseline
comparison, or any sim-to-real transfer argument).

## T0.6 -- the Tier-A ray-casting story

**Recommendation: Option 1, write the `CollisionDetection` binding
(`castRaysSoA` / `castRaysGPU` / `findCollisions*` / `buildBVH` /
`setStaticGeometry`).** Not attempted in this task (explicitly out of scope
-- it's a C++/pybind11 change to `helios-core`/`pyhelios` bindings, and this
run was constrained to `yogesh_dev/` only with no `helios-core` edits). This
is a recommendation for a human to greenlight, backed by what was actually
measured in T0.1-T0.5:

### Why not Option 3 (interim hack: `Visualizer.getDepthMap()`)

This was the cheapest option on paper, but it is currently **not viable**:
measured in T0.7 (see `phase0/visualizer_depth_rig.py` and
`PHASE0_LOG.md`), `getDepthMap()` returns near-binary garbage on this build
(`np.unique(depth)` is exactly `{0.0, 255.0}`, no intermediate values) and
this is an **upstream-acknowledged bug**, not a Phase 0 setup mistake --
helios-core's `VisualizerRendering.cpp` has the comment `// \todo This is
not working. Basically the same code works in the plotDepthMap() method,
but for some reason doesn't seem to yield the correct float values.`
directly on the code path PyHelios's `getDepthMap()` calls. Building Phase 2
fruit-outward visibility on top of this would be building on broken data.
It would need the helios-core fix first, at which point it's still missing
per-primitive UUID and arbitrary-origin rays (the task doc's own
limitation), so it's a dead end for Phase 2 either way.

### Why not Option 2 (sim loop in C++, driven from Python at experiment level)

This avoids writing a Python binding but doesn't avoid writing C++, and it
pushes the planner/loop logic (which is genuinely easier to iterate on in
Python -- Phase 3/4's kinematics and planning code is explicitly Python-only
in the task doc) into the same language as the thing that's hard to modify
quickly. It also doesn't produce a reusable, testable Python API the way a
binding does -- every experiment variant needs a C++ rebuild. Given
Phase 2's `vis_i(v)` and Phase 4's GPU-batched information gain both need
this ray-casting capability repeatedly, from Python, with different
sampling patterns per experiment, a binding that exposes the existing
`castRaysSoA`/`castRaysGPU` primitives is more reusable than a bespoke C++
loop per experiment.

### Why Option 1

- Directly unblocks Phase 2 (`vis_i(v)` needs arbitrary-origin rays from
  fruit surfaces with per-primitive UUID hit results) and Phase 4
  (GPU-batched information gain, called out in the task doc as "the single
  highest-leverage engineering decision").
- `CollisionDetection`'s ray tracer already exists in helios-core and is
  explicitly excluded only from the Python API
  (`pyhelios/config/plugin_metadata.py`) -- this is a binding gap, not a
  missing capability, so the C++ work is "expose an existing thing" rather
  than "build a new ray tracer."
- Measured evidence from T0.5 supports investing here rather than in
  Tier B/C tuning: the render-loop cost in this rig is dominated by a fixed
  per-`runBand()` scene-wide radiative-transfer solve (~0.62-1.0s,
  essentially flat across 320x240 to 1280x960 and AA 1-4 -- see
  `PHASE0_LOG.md`'s sweep table), not by anything camera-related. A
  Tier-A ray-caster sidesteps the radiative-transfer solve entirely for
  pure visibility/occupancy queries, which is exactly the kind of
  high-frequency query Phase 2/4 need and that Tier B/C are structurally
  too expensive for (Tier B is further confounded by this devbox's
  software-only OpenGL renderer -- see the Tier B caveat in
  `PHASE0_LOG.md` -- but Tier C's flat cost-vs-resolution curve is a
  real, environment-independent finding).

### Practical note for whoever picks this up

Also expose `runCamerasOnly()`
(`RayTracingBackend.h:153`, listed in "Upstream patches worth
contributing" #1) at the same time if touching this part of the codebase --
our T0.5 numbers are direct evidence for that patch too: if
`runBand()`'s cost is the scene solve and not the camera step, then a
camera-only re-render after just moving the camera (no geometry change)
should be dramatically cheaper than a full `runBand()`, which is exactly
the 1 Hz -> 10 Hz jump the task doc predicts.
