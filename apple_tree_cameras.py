import os
import sys

from apple_tree import build_apple_tree
from pyhelios import Context, PlantArchitecture, Visualizer
from pyhelios.types import RGBcolor, vec3

# Gaussian-splat capture rig: all 3 cameras sit at the same horizontal
# distance in front of the tree (same x, same y offset) and differ only in
# elevation (z) -- one above the tree looking down, one level with the
# tree's center, one low near the ground looking up. The same rig is
# reused for every tree, just re-centered on that tree's position/height.
CAMERA_DISTANCE = 2.5  # front offset from the tree, in meters, same for all rigs

CAMERA_RIGS = [
    {"name": "above", "height_frac": 1.15},
    {"name": "level", "height_frac": 0.5},
    {"name": "below", "height_frac": 0.05},
]

OUTPUT_DIR = "renders"


def camera_position_for_tree(context, plantarch, plant_id, base_position, rig):
    """Compute a camera position/lookAt in front of one tree for a given rig."""
    uuids = plantarch.getAllPlantUUIDs(plant_id)
    x_bounds, y_bounds, z_bounds = context.getDomainBoundingBox(uuids)
    tree_height = z_bounds.y - z_bounds.x

    look_at = vec3(base_position.x, base_position.y, z_bounds.x + 0.5 * tree_height)
    position = vec3(
        base_position.x,
        base_position.y - CAMERA_DISTANCE,
        z_bounds.x + rig["height_frac"] * tree_height,
    )
    return position, look_at


if __name__ == "__main__":
    AGE_DAYS = 365.0
    POSITIONS = [vec3(0, 0, 0), vec3(3, 0, 0), vec3(6, 0, 0)]

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            plant_ids = []
            for i, position in enumerate(POSITIONS):
                plant_id = build_apple_tree(plantarch, position=position, age_days=AGE_DAYS)
                plant_ids.append(plant_id)
                print(f"Built apple tree plant_id={plant_id} at {position}")

            all_uuids = []
            for plant_id in plant_ids:
                all_uuids.extend(plantarch.getAllPlantUUIDs(plant_id))

            with Visualizer(width=1000, height=800, headless=True) as visualizer:
                visualizer.buildContextGeometry(context, uuids=all_uuids)
                visualizer.setBackgroundColor(RGBcolor(0.70, 0.85, 1.0))
                visualizer.setLightingModel("phong_shadowed")

                for plant_id, position in zip(plant_ids, POSITIONS):
                    for rig in CAMERA_RIGS:
                        camera_pos, look_at = camera_position_for_tree(
                            context, plantarch, plant_id, position, rig
                        )
                        visualizer.setCameraPosition(position=camera_pos, lookAt=look_at)
                        visualizer.plotUpdate()

                        filename = os.path.join(
                            OUTPUT_DIR, f"tree{plant_id}_{rig['name']}.png"
                        )
                        visualizer.printWindow(filename)
                        print(f"  Saved {filename}")

    print(f"\nDone. Images written to {OUTPUT_DIR}/")
