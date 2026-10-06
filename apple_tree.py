import sys

from pyhelios import Context, PlantArchitecture, Visualizer
from pyhelios.types import RGBcolor, vec3


def build_apple_tree(plantarch, position=None, age_days=365.0, build_parameters=None):
    """Load the apple library model and build one tree instance.

    Args:
        plantarch: PlantArchitecture instance bound to a Context.
        position: Base of the trunk (default: origin).
        age_days: Plant age in days. Older = larger / more developed.
        build_parameters: Optional training overrides, e.g.
            {'trunk_height': 0.8, 'num_scaffolds': 4, 'scaffold_angle': 40}

    Returns:
        plant_id for the created tree.
    """
    if position is None:
        position = vec3(0, 0, 0)

    if build_parameters and build_parameters.get("trunk_height", 0.8) > 0.8:
        raise ValueError(
            "The built-in apple model requires trunk_height <= 0.80 m "
            "(20 nodes at 0.04 m per internode)."
        )

    plantarch.loadPlantModelFromLibrary("apple")
    plant_id = plantarch.buildPlantInstanceFromLibrary(
        base_position=position,
        age=age_days,
        build_parameters=build_parameters,
    )
    return plant_id


def visualize_trees(context, plantarch, plant_ids):
    """Open one interactive window showing all built trees together."""
    all_uuids = []
    for plant_id in plant_ids:
        uuids = plantarch.getAllPlantUUIDs(plant_id)
        if not uuids:
            raise RuntimeError(f"Plant {plant_id} has no geometry to visualize")
        all_uuids.extend(uuids)

    if not all_uuids:
        raise RuntimeError("No tree geometry to visualize")

    # Fit the camera to the combined scene bounding box
    x_bounds, y_bounds, z_bounds = context.getDomainBoundingBox(all_uuids)
    center = vec3(
        0.5 * (x_bounds.x + x_bounds.y),
        0.5 * (y_bounds.x + y_bounds.y),
        0.5 * (z_bounds.x + z_bounds.y),
    )
    extent = max(
        x_bounds.y - x_bounds.x,
        y_bounds.y - y_bounds.x,
        z_bounds.y - z_bounds.x,
        1.0,
    )

    with Visualizer(width=1000, height=800) as visualizer:
        visualizer.buildContextGeometry(context, uuids=all_uuids)
        visualizer.setCameraPosition(
            position=vec3(
                center.x + 1.8 * extent,
                center.y + 1.8 * extent,
                center.z + 0.6 * extent,
            ),
            lookAt=center,
        )
        visualizer.setBackgroundColor(RGBcolor(0.70, 0.85, 1.0))
        visualizer.setLightingModel("phong_shadowed")
        visualizer.plotInteractive()


if __name__ == "__main__":
    # Age is the main "size" control for library plants (days).
    # Try ~90 for a young tree, ~365 for a year-old tree.
    AGE_DAYS = [720.0] * 10

    POSITIONS = [
        vec3(0, 0, 0),
        vec3(1.5, 0, 0),
        vec3(3, 0, 0),
        vec3(9, 0, 0),
        vec3(12, 0, 0),
        vec3(15, 0, 0),
        vec3(18, 0, 0),
        vec3(21, 0, 0),
        vec3(24, 0, 0),
        vec3(27, 0, 0),
    ]

    # Optional apple training-system overrides (omit to use defaults):
    BUILD_PARAMS_LIST = [
        {"trunk_height": 0.72, "num_scaffolds": 4, "scaffold_angle": 33},
        {"trunk_height": 0.78, "num_scaffolds": 6, "scaffold_angle": 47},
        {"trunk_height": 0.79, "num_scaffolds": 5, "scaffold_angle": 39},
        {"trunk_height": 0.74, "num_scaffolds": 4, "scaffold_angle": 44},
        {"trunk_height": 0.70, "num_scaffolds": 6, "scaffold_angle": 31},
        {"trunk_height": 0.80, "num_scaffolds": 5, "scaffold_angle": 50},
        {"trunk_height": 0.76, "num_scaffolds": 4, "scaffold_angle": 36},
        {"trunk_height": 0.77, "num_scaffolds": 5, "scaffold_angle": 42},
        {"trunk_height": 0.71, "num_scaffolds": 6, "scaffold_angle": 35},
        {"trunk_height": 0.74, "num_scaffolds": 5, "scaffold_angle": 48},
    ]

    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            plantarch.loadPlantModelFromLibrary("apple")

            # Include fruit in collision detection and steer growth away from
            # overlaps (fruit is excluded by default) so apples on neighboring
            # trees/branches don't grow into each other.
            plantarch.setCollisionRelevantOrgans(
                include_internodes=True,
                include_leaves=True,
                include_fruit=True,
            )
            plantarch.enableSoftCollisionAvoidance(enable_fruit_collision=True)

            plant_ids = []

            for i in range(3):
                plant_id_i = build_apple_tree(
                    plantarch,
                    position=POSITIONS[i],
                    age_days=AGE_DAYS[i],
                    build_parameters=BUILD_PARAMS_LIST[i],
                )
                plant_ids.append(plant_id_i)

                object_ids = plantarch.getAllPlantObjectIDs(plant_id_i)
                uuids = plantarch.getAllPlantUUIDs(plant_id_i)
                x_bounds, y_bounds, z_bounds = context.getDomainBoundingBox(uuids)
                print(f"Apple tree plant_id={plant_id_i}")
                print(f"  objects:    {len(object_ids)}")
                print(f"  primitives: {len(uuids)}")
                print(f"  age:        {AGE_DAYS[i]} days")
                print(f"  extent:     x={x_bounds.y - x_bounds.x:.3f}m, y={y_bounds.y - y_bounds.x:.3f}m, z={z_bounds.y - z_bounds.x:.3f}m")

            if "--no-visualization" not in sys.argv:
                visualize_trees(context, plantarch, plant_ids)
