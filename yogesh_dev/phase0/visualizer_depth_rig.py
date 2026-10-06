"""
T0.7 -- Keep the Visualizer path as Tier B, with depth wired in.

Fresh copy/adaptation of apple_tree_cameras.py (repo root) inside
yogesh_dev/, per the Phase 0 constraint of not touching the original. Adds
`Visualizer.getDepthMap() -> (List[float], w, h)`, which already existed in
PyHelios but was unused by the original rig -- free depth at frame rate for
debugging and fast rollouts, per the task doc.

KNOWN UPSTREAM BUG (measured, not fixable from PyHelios -- would need a
helios-core patch, out of scope for this task): `getDepthMap()` currently
returns near-binary garbage, not real per-pixel depth. Measured on the
3-tree scene: `np.unique(depth)` is exactly `{0.0, 255.0}` with ~every pixel
at one of those two values, no intermediate depths at all. Root cause is
in helios-core itself, not a Phase 0 setup mistake: helios-core's
`VisualizerRendering.cpp` (`Visualizer::getDepthMap`, the vector-returning
overload) ends with the comment `// \todo This is not working. Basically
the same code works in the plotDepthMap() method, but for some reason
doesn't seem to yield the correct float values.` -- i.e. this is an
upstream-acknowledged bug, not something wrong with how it's called here.
This matters for T0.6: PHASE0_DECISIONS.md's option 3 ("use
Visualizer.getDepthMap() as a poor-man's depth-only ray cast") is NOT
currently viable given this bug -- it would need the helios-core fix first.
The pixel-count/timing benchmark in T0.5 still uses `getDepthMap()` for
Tier B (it's a fair timing measurement of the call itself, real workloads
will call it), but do not trust its VALUES until helios-core fixes this.
"""

import math
import os

from pyhelios import Context, PlantArchitecture, Visualizer
from pyhelios.types import RGBcolor, vec3

from .canopy import build_three_tree_scene

CAMERA_FOV_DEG = 45.0    # matches Visualizer's default vertical FOV (not overridden below)
CAMERA_MARGIN = 1.3
CAMERA_DISTANCE_MIN = 1.0

CAMERA_RIGS = [
    {"name": "above", "height_frac": 1.15},
    {"name": "level", "height_frac": 0.5},
    {"name": "below", "height_frac": 0.05},
]

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "renders_tier_b")


def camera_position_for_tree(context, plantarch, plant_id, base_position, rig, aspect_ratio):
    """Identical to apple_tree_cameras.py's function of the same name."""
    uuids = plantarch.getAllPlantUUIDs(plant_id)
    x_bounds, y_bounds, z_bounds = context.getDomainBoundingBox(uuids)
    tree_height = z_bounds.y - z_bounds.x
    tree_width = x_bounds.y - x_bounds.x

    half_fov_v = math.radians(CAMERA_FOV_DEG) / 2
    half_fov_h = math.atan(aspect_ratio * math.tan(half_fov_v))
    distance_for_height = (tree_height / 2) / math.tan(half_fov_v) * CAMERA_MARGIN
    distance_for_width = (tree_width / 2) / math.tan(half_fov_h) * CAMERA_MARGIN
    distance = max(distance_for_height, distance_for_width, CAMERA_DISTANCE_MIN)

    look_at = vec3(base_position.x, base_position.y, z_bounds.x + 0.5 * tree_height)
    position = vec3(
        base_position.x,
        base_position.y - distance,
        z_bounds.x + rig["height_frac"] * tree_height,
    )
    return position, look_at


def run_tier_b_rig(context, plantarch, plant_ids, positions, width=640, height=480,
                    save_images=False, output_dir=OUTPUT_DIR):
    """Render the 3-camera rig through the Visualizer (Tier B), capturing both
    the RGB frame (optional, for eyeballing) and the depth map (via
    getDepthMap(), the T0.7 addition) for every tree/rig combination.

    Returns a list of dicts: {plant_id, rig_name, depth, depth_w, depth_h}.
    `depth` is the raw flat depth buffer as returned by getDepthMap()
    (no file I/O, matches the in-memory-only requirement used elsewhere in
    Phase 0).
    """
    if save_images:
        os.makedirs(output_dir, exist_ok=True)

    all_uuids = []
    for plant_id in plant_ids:
        all_uuids.extend(plantarch.getAllPlantUUIDs(plant_id))

    results = []
    with Visualizer(width=width, height=height, headless=True) as visualizer:
        visualizer.buildContextGeometry(context, uuids=all_uuids)
        visualizer.setBackgroundColor(RGBcolor(0.70, 0.85, 1.0))
        visualizer.setLightingModel("phong_shadowed")

        for plant_id, position in zip(plant_ids, positions):
            for rig in CAMERA_RIGS:
                camera_pos, look_at = camera_position_for_tree(
                    context, plantarch, plant_id, position, rig, width / height
                )
                visualizer.setCameraPosition(position=camera_pos, lookAt=look_at)
                visualizer.plotUpdate()

                depth, depth_w, depth_h = visualizer.getDepthMap()

                if save_images:
                    filename = os.path.join(output_dir, f"tree{plant_id}_{rig['name']}.png")
                    visualizer.printWindow(filename)

                results.append({
                    "plant_id": plant_id,
                    "rig_name": rig["name"],
                    "depth": depth,
                    "depth_w": depth_w,
                    "depth_h": depth_h,
                })

    return results


if __name__ == "__main__":
    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            plant_ids, positions = build_three_tree_scene(context, plantarch)
            for plant_id in plant_ids:
                print(f"Built apple tree plant_id={plant_id}, "
                      f"{len(plantarch.getAllPlantUUIDs(plant_id))} primitives")

            results = run_tier_b_rig(context, plantarch, plant_ids, positions, save_images=True)

    for r in results:
        depth = r["depth"]
        finite = [d for d in depth if d == d and abs(d) < 1e6]  # drop NaN/inf sentinels
        print(f"tree{r['plant_id']}_{r['rig_name']}: depth {r['depth_w']}x{r['depth_h']}, "
              f"{len(finite)}/{len(depth)} finite, "
              f"range=[{min(finite):.3f}, {max(finite):.3f}]" if finite else "no finite depth")
