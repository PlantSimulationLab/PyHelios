# Phase 0 log

Unattended run implementing `helios_setup_tasks.md`'s Phase 0 (T0.1-T0.7,
T0.6 as a decision doc only). Everything below is chronological; numbers are
real measurements from this run, not estimates.

Machine: NVIDIA RTX 5090, driver 580.173.02, CUDA 13.0. RadiationModel
initializes with the OptiX 8.1 backend. `helios` conda env,
`/home/yogesh/anaconda3/envs/helios/bin/python`.

## Environment setup problems and workarounds

1. **Harness-enforced worktree isolation vs. pyhelios needing a build.**
   This background session's harness rejects file writes in the shared
   checkout until isolated into a git worktree (`EnterWorktree`). But a
   fresh worktree doesn't have the compiled native library --
   `pyhelios_build/build/` is gitignored (build output, not tracked) and the
   `helios-core` submodule isn't checked out into new worktrees either. Fix:
   symlinked both from the worktree back to the main checkout's already-built
   copies (`pyhelios_build/build -> /home/yogesh/PyHelios/pyhelios_build/build`,
   `helios-core -> /home/yogesh/PyHelios/helios-core`). Read-only references,
   nothing in the main checkout was modified, and neither path is
   git-tracked content (build output / submodule gitlink), so this doesn't
   touch tracked repo state. Verified with a smoke test after linking.

2. **`Visualizer` needs a display even in `headless=True` mode.** This
   devbox has no X server (`$DISPLAY` unset). `Visualizer(..., headless=True)`
   still failed with "Failed to create Visualizer" until run under
   `xvfb-run -a`. Reproduced on the *unmodified* main checkout too (not a
   worktree-specific problem) -- confirmed via a standalone Visualizer smoke
   test outside `yogesh_dev/` (not committed anywhere, just a
   confirmation that this is an environment fact, not something Phase 0
   broke). All Tier B / benchmark commands in this log were run under
   `xvfb-run -a python -m yogesh_dev.phase0.<module>`.

## T0.1 -- radiation band + light source setup

Decision: **plausible RGB**, not real-spectra radiometry. Full reasoning in
`phase0/radiation_setup.py`'s module docstring. Three bands (red 600-700nm,
green 500-600nm, blue 400-500nm), one sun sphere source, diffuse flux = 12%
of direct flux per band, scattering depth 1 (per task doc's "start at 1"
guidance).

### Discovered problem: `exposure="auto"` makes pixel values incomparable across frames

Initial testing used `CameraProperties` defaults (`exposure="auto"`).
Flux-sweep experiment (fixed scene, only the configured band flux changed,
range 0.001x-1x of a baseline `{red:480, green:520, blue:380}`):

| flux scale | measured background pixel value (raw) |
|---|---|
| 1.0 | 18.33 |
| 0.3 | 5.50 |
| 0.1 | 1.83 |

Wait -- that's `exposure="manual"`. Under `exposure="auto"` the SAME sweep
gave background pixel value **fixed at ~0.17-0.19 regardless of flux
scale**, while a foliage "hot" pixel cluster's raw value scaled as
`C/flux_scale` for a constant `C` -- i.e. auto-exposure was applying a
per-frame gain that exactly cancelled the flux change for one reference
region, while amplifying an unrelated fixed-magnitude artifact elsewhere.
This makes frame-to-frame raw pixel comparisons meaningless. Fix: use
`exposure="manual"` (`radiation_cameras.build_camera_properties`) --
confirmed this makes raw values scale linearly and predictably with
configured flux (see manual-exposure table above: 18.33 -> 5.50 -> 1.83 is
exactly proportional to 1.0 -> 0.3 -> 0.1).

### Discovered problem: fixed-value photometric saturation artifact (open issue, not fixed)

Even under `exposure="manual"`, ~15-20% of foliage/branch/fruit pixels in
the 3-tree scene return an **identical value (~292.4) across all 3 bands**,
independent of the configured flux:

| flux scale | flux_red | measured hot-cluster max (all bands) |
|---|---|---|
| 1.0 | 480 | 292.3997 |
| 0.1 | 48 | 292.3997 |
| 0.01 | 4.8 | 292.3997 |
| 0.001 | 0.48 | 292.3997 |

Confirmed this is not cross-tree canopy interpenetration: an isolated
single tree (no neighbors) shows the same artifact (9.4% of pixels at
exactly the same value, vs. ~15-20% for the 3-tree scene). Confirmed the
hot-pixel mask spatially matches the tree canopy silhouette (not a
localized sun-disk glint). Band-label capitalization ("red" vs "Red") makes
no difference. Given the value is completely flux-independent (a 1000x flux
change doesn't move it at all), this looks like a numerical
saturation/clamp somewhere in the scattering solve for this canopy's
geometry, most likely triggered by self-overlapping/degenerate leaf
tessellation from the procedural growth model -- not something fixable
from PyHelios (would need helios-core investigation, out of scope here).
Documented in `radiation_setup.py`'s "KNOWN ARTIFACT" note. Does **not**
affect per-pixel ground truth (`getPrimitiveDataLabelMap` /
`getObjectDataLabelMap`), which comes from a separate ray-hit-topology pass
validated sub-pixel accurate in T0.3.

### sRGB gamma clips raw radiance >= 1.0 to solid white before `flux_to_pixel_conversion` is applied

Found while trying to get a non-blown-out preview image.
`RadiationModel::writeCameraImage` (helios-core
`plugins/radiation/src/RadiationCamera.cpp:565-574`) applies
`lin_to_srgb(max(0,v))` to the RAW per-band pixel value first
(`lin_to_srgb` clamps `x>=1.0` to `1.0`, i.e. solid white --
`RadiationModel.h:436-443`), and only THEN multiplies by
`flux_to_pixel_conversion`. So `flux_to_pixel_conversion` cannot rescue an
over-bright linear input -- it only trims the brightness of an
already-correctly-exposed image. Final `DEFAULT_BAND_FLUX` in
`radiation_setup.py` (`red=9.6, green=10.4, blue=7.6`, i.e. the 480/520/380
baseline x0.02) was chosen so ordinary background/diffuse radiance lands
under 1.0. Demo renders (`phase0/renders_tier_c/*.jpeg`, from
`run_tier_c_demo.py`) show a correctly-exposed olive-green background with
recognizable tree silhouettes -- but the foliage itself still renders
mostly solid white because of the saturation artifact above (which,
per the table above, clips regardless of flux level chosen).

## T0.2 -- 3 cameras as RadiationCamera

`phase0/radiation_cameras.py`. HFOV conversion implemented and used:
`HFOV = 2*atan(aspect * tan(VFOV/2))`, `VFOV=45deg` (matches
`apple_tree_cameras.py`'s `CAMERA_FOV_DEG`). At 640x480 (aspect 4:3) this
gives `HFOV=57.822 deg` (measured, printed by `run_tier_c_demo.py`).
`lens_diameter=0.0` (pinhole), `FOV_aspect_ratio=0.0` (auto vertical),
`antialiasing_samples=2` default (in the 1-4 range). All 3 cameras
(`above`/`level`/`below`) are registered once and repositioned via
`setCameraPosition`/`setCameraLookat` between trees -- never re-added.

## T0.3 [BLOCKER] -- pose convention, empirically verified

`phase0/pose_convention.py`. Method: 9 spheres at known world coordinates
spanning the frame, tagged with a unique `sphere_id` primitive-data value;
rendered; measured each sphere's pixel centroid via
`getPrimitiveDataLabelMap(cam, "sphere_id")`; compared against
`K @ [R|t] @ X` using the SAME convention `apple_tree_gaussian_splatting.py`'s
`look_at_view_matrix()` uses (OpenCV X-right/Y-down/Z-forward,
`world_up=(0,0,1)`), reverse-engineered against the Visualizer -- **not
assumed to carry over to the radiation camera, tested instead.**

Result, axis-aligned pose (`eye=(0,-5,1)`, `lookat=(0,0,1)`):

| candidate pixel-axis convention | mean err (px) | max err (px) |
|---|---|---|
| **row=v, col=u (standard top-left origin)** | **0.707** | **0.813** |
| row=H-1-v, col=u (vertical flip) | 62.377 | 101.384 |
| row=v, col=W-1-u (horizontal flip) | 93.309 | 151.576 |
| row=H-1-v, col=W-1-u (both flipped) | 126.988 | 181.526 |

Result, off-axis pose (`eye=(3.2,-4.1,2.6)`, `lookat=(0.3,0.2,0.9)`, not
aligned with any single world axis, to rule out a coincidental match):
best convention again "row=v, col=u", mean err 0.713px, max 0.914px, 9/9
spheres visible.

**Conclusion: the radiation camera uses the exact same convention as the
Visualizer/gsplat pipeline** -- `world_up=(0,0,1)`, OpenCV-style camera
frame, standard top-left-origin pixel indexing, sub-pixel accurate (<1px
mean error on a 320x240 image) in both an axis-aligned and an off-axis
pose. No flips, no basis change needed anywhere downstream. Roll is indeed
never introduced by this convention (only position + lookat feed the
camera), consistent with the task doc's note that roll isn't
representable.

## T0.4 -- render loop structure

`phase0/radiation_cameras.py:run_render_loop` and the inline loop in
`run_tier_c_demo.py`: `updateGeometry()` called once outside the pose loop,
one `runBand(["red","green","blue"])` call per pose (not per band). Ran
against the real 3-tree scene end-to-end (`run_tier_c_demo.py`): 3 tree
poses x 3 cameras rendered + written to JPEG in 1.96-2.34s total across
several runs (~0.65-0.78s/pose, includes JPEG encode + disk write, not
just compute -- see T0.5 for a compute-only number).

## T0.5 [BLOCKER] -- honest benchmark

`phase0/benchmark.py`. All numbers below are from one full run
(`benchmark_results.json` has the raw data). Scene: 3 apple trees, age 720
days, positions x=0/1.5/3 (matches `apple_tree_cameras.py`).

### Primitive counts

`{tree0: 36105, tree1: 36409, tree2: 47699, total: 120213}` for this run.
**Note:** primitive count is NOT deterministic run-to-run with identical
build parameters -- observed 33k-56k per tree across different runs of this
session (e.g. one run gave `{41833, 34173, 45363}`, another
`{56224, 37006, 45363}`). The apple library's procedural growth model has
some unseeded internal randomness. Treat "primitive count per tree" as a
distribution (roughly 33k-56k per tree observed here), not a fixed number.

### Tier B vs Tier C, 640x480

| Tier | metric | value |
|---|---|---|
| B (Visualizer plotUpdate+getDepthMap) | mean per view | **0.726s** (1.38 Hz) |
| B | min/max per view | 0.701s / 0.817s |
| C (runBand, AA=1, scatter depth=1, 3 cams/pose) | mean per pose (excl. warmup) | **0.627s** (1.59 Hz) |
| C | warmup pose (first runBand after updateGeometry) | 0.628s (not meaningfully different from steady-state here) |

**Environment caveat, important:** this devbox has no physical display, so
Tier B ran under `xvfb-run`. `glxinfo | grep renderer` confirms
`OpenGL renderer string: llvmpipe` -- Mesa's CPU software rasterizer, NOT
the RTX 5090. Decomposed Tier B: `plotUpdate()` alone measured 0.30-0.41s,
`getDepthMap()` alone 0.32-0.37s, roughly an even split, for ~120k
primitives at 640x480. **Tier C measuring faster than Tier B here is an
artifact of this headless software-rendering setup, not evidence that
ray-traced radiative transfer beats OpenGL rasterization in general.** On
real display/GPU-backed-OpenGL hardware, Tier B would very likely be much
faster than this. Re-run on real hardware before making an architecture
call on this axis. (The Visualizer/Tier B path itself is real and correct
-- this is a benchmarking-environment limitation, not a bug in the rig.)

### Resolution x AA sweep, Tier C (mean s/pose excl. warmup, n=2 poses per config -- small sample, treat trend not exact values)

| resolution | AA=1 | AA=2 | AA=4 |
|---|---|---|---|
| 320x240 | 0.818s | 0.722s | 0.661s |
| 640x480 | 0.842s | 0.726s | 0.969s |
| 1280x960 | 1.090s | 1.018s | 1.075s |

**Key finding: per-pose cost is dominated by a fixed cost, not by
resolution or AA.** All 9 configurations cluster in 0.66-1.09s despite a
16x pixel-count range (320x240 -> 1280x960) and a 4x AA range. This
directly contradicts the naive expectation that lower resolution/AA -> much
faster loop. Decomposed a separate run (`runBand()` call alone vs. pixel
readback alone, 640x480/AA=1): `runBand()` took 0.620-0.627s across all 3
poses (astonishingly flat), while reading back all 9 camera/band pixel
buffers took only 0.037-0.042s total. **The scene-wide direct+diffuse+
scattering radiative-transfer solve inside `runBand()` -- which happens
once per call regardless of camera resolution/AA/count -- is the entire
cost.** This is exactly the problem the task doc's "Upstream patches worth
contributing #1" (`runCamerasOnly()`) targets, and our numbers are direct
supporting evidence for prioritizing that patch (see `PHASE0_DECISIONS.md`).

### T0.6 note

See `PHASE0_DECISIONS.md` (separate file per the task spec) for the T0.6
ray-casting-story decision, informed by everything above.

## T0.7 -- Visualizer.getDepthMap() wired into Tier B

`phase0/visualizer_depth_rig.py`. Functionally wired in and runs end-to-end
(3 trees x 3 rigs, depth pulled per view, no file I/O). **But the VALUES
are broken:** `getDepthMap()` returned exactly `{0.0, 255.0}` with no
intermediate depths on every view tested -- confirmed this is an
upstream-acknowledged helios-core bug (`VisualizerRendering.cpp`'s
`Visualizer::getDepthMap(std::vector<float>&, ...)` ends with `// \todo
This is not working. Basically the same code works in the plotDepthMap()
method, but for some reason doesn't seem to yield the correct float
values.`), not a Phase 0 integration mistake. This directly affects the
T0.6 decision -- see `PHASE0_DECISIONS.md` for why this rules out T0.6's
"interim hack" option as currently viable.

## Files produced (all under `yogesh_dev/`)

- `phase0/canopy.py` -- self-contained copy of `build_apple_tree` (T0.1-T0.5 dependency)
- `phase0/radiation_setup.py` -- T0.1
- `phase0/radiation_cameras.py` -- T0.2, T0.4
- `phase0/pose_convention.py` -- T0.3
- `phase0/run_tier_c_demo.py` -- T0.1+T0.2+T0.4 integration demo, writes `renders_tier_c/*.jpeg`
- `phase0/visualizer_depth_rig.py` -- T0.7, writes `renders_tier_b/*.png`
- `phase0/benchmark.py` -- T0.5, writes `benchmark_results.json`
- `PHASE0_DECISIONS.md` -- T0.6 decision doc
- `PHASE0_LOG.md` -- this file
- `PHASE0_STATUS.md` -- final status

## How to re-run everything

```
cd /home/yogesh/PyHelios   # or wherever this yogesh_dev/ lands
PYTHONPATH=. /home/yogesh/anaconda3/envs/helios/bin/python -m yogesh_dev.phase0.pose_convention
PYTHONPATH=. /home/yogesh/anaconda3/envs/helios/bin/python -m yogesh_dev.phase0.run_tier_c_demo
PYTHONPATH=. xvfb-run -a /home/yogesh/anaconda3/envs/helios/bin/python -m yogesh_dev.phase0.visualizer_depth_rig
PYTHONPATH=. xvfb-run -a /home/yogesh/anaconda3/envs/helios/bin/python -m yogesh_dev.phase0.benchmark
```

(`xvfb-run -a` is only required for the two that touch `Visualizer`; the
pure-RadiationModel scripts don't need a display.)
