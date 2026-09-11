"""
T0.5 [BLOCKER] -- Honest benchmark: Tier B (Visualizer) vs Tier C (RadiationModel),
plus a resolution/AA sweep for Tier C. All numbers below are REAL measurements
from this machine (RTX 5090, OptiX 8.1 backend) on the standard 3-apple-tree
scene -- see PHASE0_LOG.md for the actual run's numbers (this file only
contains the code; run it to reproduce).

Requires a display for the Tier B (Visualizer) path even in "headless" mode
-- this environment has no X server, so run under xvfb-run:

    xvfb-run -a /home/yogesh/anaconda3/envs/helios/bin/python -m yogesh_dev.phase0.benchmark

Tier C (RadiationModel) does not need a display (it's pure OptiX/CUDA), but
running the whole script under xvfb-run is harmless for it.

Methodology notes (read before trusting the numbers):
- Every timed call is synchronous from Python's perspective: getCameraPixelData
  / getDepthMap block until the GPU work finishes and data is copied back, so
  wall-clock time.time() deltas around them include the actual compute, not
  just kernel-launch overhead.
- Tier C is timed with a warm-up pose first (excluded from the average) --
  the first runBand() call after updateGeometry() pays for BVH/acceleration-
  structure construction, which a real closed loop would only pay once per
  geometry change, not once per pose.
- Tier B numbers are the plotUpdate()+getDepthMap() pair per view, which is
  what T0.7 wires into the rig; getDepthMap() is being timed even though its
  VALUES are currently broken upstream (see visualizer_depth_rig.py) --
  timing the call is still a fair measurement of what a real Tier-B rollout
  would pay per view.

ENVIRONMENT CAVEAT (important -- read before trusting the Tier B number):
this devbox has no physical display, so the Visualizer runs under
`xvfb-run`. `glxinfo | grep renderer` on this Xvfb confirms
`OpenGL renderer string: llvmpipe` -- Mesa's CPU SOFTWARE rasterizer, NOT
the RTX 5090. Tier B is therefore paying full software-rasterization cost
for ~120k primitives at 640x480 (measured ~0.30-0.41s for plotUpdate() alone,
~0.32-0.37s for getDepthMap() alone -- see PHASE0_LOG.md), while Tier C
correctly dispatches to the GPU via OptiX. The measured "Tier C is faster
than Tier B" result below is real for THIS machine as configured, but it is
an artifact of the headless GL setup, not evidence that ray-traced radiative
transfer beats OpenGL rasterization in general. On a machine with a real
display (or a GPU-backed headless EGL/GLX context), Tier B would very likely
be much faster than what's measured here. Re-run this benchmark on real
display hardware before using the Tier B number for any architecture
decision.
"""

import json
import os
import time

import numpy as np

from pyhelios import Context, PlantArchitecture, RadiationModel, Visualizer
from pyhelios.types import RGBcolor

from .canopy import build_three_tree_scene
from .radiation_setup import setup_bands_and_lights
from .radiation_cameras import (
    compute_tree_poses, register_camera_rig, run_render_loop,
    RGB_BAND_LABELS,
)
from .visualizer_depth_rig import camera_position_for_tree, CAMERA_RIGS

RESULTS_PATH = os.path.join(os.path.dirname(__file__), "benchmark_results.json")


def count_primitives(plantarch, plant_ids):
    counts = {pid: len(plantarch.getAllPlantUUIDs(pid)) for pid in plant_ids}
    counts["total"] = sum(counts.values())
    return counts


def benchmark_tier_b(context, plantarch, plant_ids, positions, width=640, height=480, n_repeats=1):
    """Tier B: Visualizer.plotUpdate() + getDepthMap(), timed per view.
    Requires a display (run under xvfb-run) -- see module docstring.
    """
    all_uuids = []
    for plant_id in plant_ids:
        all_uuids.extend(plantarch.getAllPlantUUIDs(plant_id))

    per_view_times = []
    with Visualizer(width=width, height=height, headless=True) as visualizer:
        visualizer.buildContextGeometry(context, uuids=all_uuids)
        visualizer.setBackgroundColor(RGBcolor(0.70, 0.85, 1.0))
        visualizer.setLightingModel("phong_shadowed")

        for _ in range(n_repeats):
            for plant_id, position in zip(plant_ids, positions):
                for rig in CAMERA_RIGS:
                    camera_pos, look_at = camera_position_for_tree(
                        context, plantarch, plant_id, position, rig, width / height)
                    visualizer.setCameraPosition(position=camera_pos, lookAt=look_at)

                    t0 = time.perf_counter()
                    visualizer.plotUpdate()
                    _depth, _w, _h = visualizer.getDepthMap()
                    t1 = time.perf_counter()

                    per_view_times.append(t1 - t0)

    per_view_times = np.array(per_view_times)
    return {
        "n_views": len(per_view_times),
        "total_s": float(per_view_times.sum()),
        "mean_s": float(per_view_times.mean()),
        "min_s": float(per_view_times.min()),
        "max_s": float(per_view_times.max()),
        "hz": float(1.0 / per_view_times.mean()),
        "resolution": (width, height),
    }


def benchmark_tier_c(context, plantarch, plant_ids, positions, width=640, height=480,
                      antialiasing_samples=1, scattering_depth=1, n_warmup_poses=1):
    """Tier C: runBand(["red","green","blue"]) per pose (= per tree, all 3
    cameras together), 640x480/AA=1/scattering_depth=1 by default per T0.5's
    spec. Returns timing that EXCLUDES the first `n_warmup_poses` poses (BVH
    build cost, paid once per geometry change in a real loop, not per pose).
    """
    tree_poses = compute_tree_poses(context, plantarch, plant_ids, positions,
                                     resolution=(width, height))

    with RadiationModel(context) as radiation:
        setup_bands_and_lights(radiation, scattering_depth=scattering_depth)
        camera_labels, hfov_deg = register_camera_rig(
            radiation, tree_poses[0], resolution=(width, height),
            antialiasing_samples=antialiasing_samples)

        radiation.updateGeometry()  # ONCE, outside the pose loop (T0.4)

        pose_times = []
        for poses in tree_poses:
            t0 = time.perf_counter()
            for cam, (eye, lookat) in zip(camera_labels, poses):
                radiation.setCameraPosition(cam, eye)
                radiation.setCameraLookat(cam, lookat)
            radiation.runBand(RGB_BAND_LABELS)  # ONE call, all bands (T0.4)
            for cam in camera_labels:
                for band in RGB_BAND_LABELS:
                    radiation.getCameraPixelData(cam, band)  # force readback, matches Tier B timing semantics
            t1 = time.perf_counter()
            pose_times.append(t1 - t0)

    pose_times = np.array(pose_times)
    warm = pose_times[n_warmup_poses:] if len(pose_times) > n_warmup_poses else pose_times
    return {
        "n_poses_total": len(pose_times),
        "n_poses_excl_warmup": len(warm),
        "warmup_pose_s": float(pose_times[0]) if len(pose_times) else None,
        "total_s_excl_warmup": float(warm.sum()),
        "mean_s_per_pose_excl_warmup": float(warm.mean()) if len(warm) else None,
        "min_s": float(warm.min()) if len(warm) else None,
        "max_s": float(warm.max()) if len(warm) else None,
        "hz_excl_warmup": float(1.0 / warm.mean()) if len(warm) else None,
        "resolution": (width, height),
        "antialiasing_samples": antialiasing_samples,
        "scattering_depth": scattering_depth,
        "n_cameras": len(camera_labels),
    }


def run_resolution_aa_sweep(resolutions, aa_values):
    """Fresh Context/RadiationModel per configuration (avoids the source/band
    accumulation bug found during T0.1 -- see PHASE0_LOG.md)."""
    sweep_results = []
    for width, height in resolutions:
        for aa in aa_values:
            with Context() as context:
                with PlantArchitecture(context) as plantarch:
                    plant_ids, positions = build_three_tree_scene(context, plantarch)
                    result = benchmark_tier_c(context, plantarch, plant_ids, positions,
                                               width=width, height=height,
                                               antialiasing_samples=aa)
            result["config"] = f"{width}x{height}_AA{aa}"
            sweep_results.append(result)
            print(f"  {result['config']}: {result['mean_s_per_pose_excl_warmup']*1000:.1f} ms/pose "
                  f"({result['hz_excl_warmup']:.2f} Hz), warmup pose={result['warmup_pose_s']*1000:.1f} ms")
    return sweep_results


def main():
    results = {}

    print("=" * 70)
    print("Primitive counts")
    print("=" * 70)
    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            plant_ids, positions = build_three_tree_scene(context, plantarch)
            prim_counts = count_primitives(plantarch, plant_ids)
    print(prim_counts)
    results["primitive_counts"] = prim_counts

    print()
    print("=" * 70)
    print("Tier B: Visualizer.plotUpdate() + getDepthMap(), 640x480, 9 views (3 trees x 3 rigs)")
    print("=" * 70)
    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            plant_ids, positions = build_three_tree_scene(context, plantarch)
            tier_b = benchmark_tier_b(context, plantarch, plant_ids, positions)
    print(tier_b)
    results["tier_b"] = tier_b

    print()
    print("=" * 70)
    print("Tier C: runBand([r,g,b]) per pose, 640x480, AA=1, scattering_depth=1, 3 cams/pose")
    print("=" * 70)
    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            plant_ids, positions = build_three_tree_scene(context, plantarch)
            tier_c = benchmark_tier_c(context, plantarch, plant_ids, positions)
    print(tier_c)
    results["tier_c"] = tier_c

    print()
    print("=" * 70)
    print("Resolution x AA sweep (Tier C)")
    print("=" * 70)
    resolutions = [(320, 240), (640, 480), (1280, 960)]
    aa_values = [1, 2, 4]
    sweep = run_resolution_aa_sweep(resolutions, aa_values)
    results["sweep"] = sweep

    with open(RESULTS_PATH, "w") as fh:
        json.dump(results, fh, indent=2)
    print(f"\nWrote {RESULTS_PATH}")

    return results


if __name__ == "__main__":
    main()
