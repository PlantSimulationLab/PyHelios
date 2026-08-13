"""
Example demonstrating custom plant building with PlantArchitecture.

This example shows how to use the low-level custom building API to create
plants with full control over shoot structure and morphology.

IMPORTANT: Custom building requires loading a plant model first to define
shoot types. The shoot type labels used in custom building must match the
types defined in the loaded plant model.
"""

from pyhelios import Context, PlantArchitecture
from pyhelios.types import vec3, AxisRotation

# Create context and plant architecture
with Context() as context:
    with PlantArchitecture(context) as plantarch:
        print("=== Custom Plant Building Example ===\n")

        # STEP 1: Load a plant model to define shoot types
        # This is REQUIRED before using custom building methods
        print("Step 1: Loading plant model to define shoot types...")
        plantarch.loadPlantModelFromLibrary("bean")
        print("  ✓ Plant model loaded")
        print()

        # STEP 2: Create an empty plant instance
        print("Step 2: Creating empty plant instance...")
        plant_id = plantarch.addPlantInstance(
            base_position=vec3(0, 0, 0),
            current_age=0.0
        )
        print(f"  ✓ Created plant ID: {plant_id}")
        print()

        # STEP 3: Add base stem shoot (main trunk)
        print("Step 3: Adding base stem shoot...")
        base_shoot_id = plantarch.addBaseStemShoot(
            plant_id=plant_id,
            current_node_number=5,  # Start with 5 nodes
            base_rotation=AxisRotation(0, 0, 0),  # Upright
            internode_radius=0.01,  # 1cm radius
            internode_length_max=0.08,  # 8cm max length
            internode_length_scale_factor_fraction=1.0,
            leaf_scale_factor_fraction=1.0,
            radius_taper=0.9,  # Slight taper
            shoot_type_label="trifoliate"  # Must match a shoot type defined by the loaded model
        )
        print(f"  ✓ Created base shoot ID: {base_shoot_id}")
        print()

        # STEP 4: Add lateral branches
        print("Step 4: Adding lateral branches...")
        branch_ids = []
        for node_index in [2, 3, 4]:  # Add branches at nodes 2, 3, 4
            branch_id = plantarch.addChildShoot(
                plant_id=plant_id,
                parent_shoot_id=base_shoot_id,
                parent_node_index=node_index,
                current_node_number=3,  # Each branch has 3 nodes
                shoot_base_rotation=AxisRotation(45, 90 * node_index, 0),  # 45° out, rotated
                internode_radius=0.005,  # Thinner than main stem
                internode_length_max=0.05,  # Shorter internodes
                internode_length_scale_factor_fraction=1.0,
                leaf_scale_factor_fraction=0.9,
                radius_taper=0.85,
                shoot_type_label="trifoliate"
            )
            branch_ids.append(branch_id)
            print(f"  ✓ Created branch at node {node_index}, shoot ID: {branch_id}")
        print()

        # STEP 5: Query plant geometry
        print("Step 5: Querying plant geometry...")
        plant_uuids = plantarch.getAllPlantUUIDs(plant_id)
        plant_obj_ids = plantarch.getAllPlantObjectIDs(plant_id)
        print(f"  ✓ Plant has {len(plant_uuids)} primitives")
        print(f"  ✓ Plant has {len(plant_obj_ids)} objects")
        print()

        # STEP 6: Advance time to grow the plant
        #
        # KNOWN LIMITATION: growth of a custom-built plant is currently broken in
        # the native library. The first advanceTime() call destroys nearly every
        # leaf and petiole object (POLYMESH/CONE), leaving only the internode TUBE
        # objects - measured here, the plant shrinks from 116 objects / 7910
        # primitives to 4 objects / 392 primitives instead of growing. Plants
        # created with buildPlantInstanceFromLibrary() are unaffected.
        #
        # Growth is therefore not demonstrated here. Uncomment below to observe the
        # bug, but do not rely on the resulting geometry.
        #
        # plantarch.advanceTime(10.0)
        # plant_uuids_after = plantarch.getAllPlantUUIDs(plant_id)
        # print(f"  After growth: {len(plant_uuids_after)} primitives")
        print("Step 6: Growth skipped - see KNOWN LIMITATION note above.")
        print()

        print("=== Custom Plant Building Complete ===")
        print("\nKey Points:")
        print("  • Always load a plant model first to define shoot types")
        print("  • Shoot type labels must match those in the loaded model")
        print("  • Custom building provides full control over plant architecture")
        print("  • advanceTime() on a custom-built plant currently destroys leaf")
        print("    and petiole geometry - use buildPlantInstanceFromLibrary() if")
        print("    you need to grow the plant")
