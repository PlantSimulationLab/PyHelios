"""
Self-contained copy of the apple-tree canopy builder used by the rest of
`yogesh_dev/phase0/`.

This is a copy of `build_apple_tree()` from `apple_tree.py` (repo root),
adapted so Phase 0 work doesn't touch anything outside `yogesh_dev/`. Keep
in sync by hand if the original changes in a way that matters for Phase 0.
"""

from pyhelios.types import vec3


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


def build_three_tree_scene(context, plantarch, age_days=720.0):
    """Build the standard 3-tree scene used throughout Phase 0 benchmarking
    (matches the layout in apple_tree_cameras.py: trees at x=0, 1.5, 3)."""
    positions = [vec3(0, 0, 0), vec3(1.5, 0, 0), vec3(3, 0, 0)]
    plant_ids = []
    for position in positions:
        plant_id = build_apple_tree(plantarch, position=position, age_days=age_days)
        plant_ids.append(plant_id)
    return plant_ids, positions
