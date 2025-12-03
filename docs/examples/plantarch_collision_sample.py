"""
PlantArchitecture Collision Detection Example

This example demonstrates the collision detection capabilities of the PlantArchitecture
plugin, including soft collision avoidance, hard obstacle avoidance, and performance
optimization techniques.

The collision detection system uses cone-based ray tracing to guide plant growth away
from obstacles while maintaining natural plant architecture. This example shows:
1. Basic soft collision avoidance between plants
2. Hard obstacle avoidance (solid boundaries)
3. Parameter tuning for different scenarios
4. Performance optimization with static obstacles
5. Organ-specific collision filtering
"""

from pyhelios import Context, PlantArchitecture
from pyhelios.types import vec3, vec2, int2, RGBcolor

def example_basic_soft_collision():
    """
    Example 1: Basic soft collision avoidance between plants

    This demonstrates the simplest collision detection setup where plants
    naturally avoid growing into each other and themselves.
    """
    print("\n=== Example 1: Basic Soft Collision Avoidance ===")

    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            # Load bean model
            plantarch.loadPlantModelFromLibrary("bean")

            # Enable soft collision avoidance with default parameters
            # This uses cone-based gap detection to guide growth
            plantarch.enableSoftCollisionAvoidance()

            # Build a small canopy of plants
            plant_ids = plantarch.buildPlantCanopyFromLibrary(
                canopy_center=vec3(0, 0, 0),
                plant_spacing=vec2(0.3, 0.3),  # Close spacing to encourage collisions
                plant_count=int2(3, 3),
                age=5.0  # Start young
            )

            print(f"Created {len(plant_ids)} plants with collision avoidance enabled")

            # Grow plants - collision detection will guide growth to minimize overlaps
            print("Growing plants with collision avoidance...")
            for day in range(40):
                plantarch.advanceTime(1.0)
                if (day + 1) % 10 == 0:
                    print(f"  Day {day + 1}: Plants growing with collision avoidance")

            print(f"Final plant count: {context.getPrimitiveCount()} primitives")

            # Save visualization
            context.writeOBJ("collision_basic.obj")
            print("Saved output to collision_basic.obj")


def example_tuned_collision_parameters():
    """
    Example 2: Tuning collision detection parameters

    Shows how to adjust the perception cone parameters to control collision
    detection behavior for different plant densities and growth patterns.
    """
    print("\n=== Example 2: Tuned Collision Parameters ===")

    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            plantarch.loadPlantModelFromLibrary("tomato")

            # Configure collision detection parameters for dense canopy
            plantarch.setSoftCollisionAvoidanceParameters(
                view_half_angle_deg=60.0,      # Narrower cone for focused detection
                look_ahead_distance=0.05,       # Shorter distance for close obstacles
                sample_count=512,               # More samples for better accuracy
                inertia_weight=0.3              # More responsive to obstacles
            )

            # Enable collision avoidance
            plantarch.enableSoftCollisionAvoidance()

            # Build dense canopy
            plant_ids = plantarch.buildPlantCanopyFromLibrary(
                canopy_center=vec3(0, 0, 0),
                plant_spacing=vec2(0.2, 0.2),  # Very dense spacing
                plant_count=int2(4, 4),
                age=10.0
            )

            print(f"Created {len(plant_ids)} plants in dense configuration")
            print("Collision parameters tuned for close spacing:")
            print("  - Narrower detection cone (60°)")
            print("  - Shorter look-ahead (0.05m)")
            print("  - Higher sample count (512 rays)")
            print("  - Lower inertia (0.3 for quick response)")

            # Grow plants
            print("Growing plants with optimized collision detection...")
            plantarch.advanceTime(20.0)

            print(f"Final geometry: {context.getPrimitiveCount()} primitives")
            context.writeOBJ("collision_tuned.obj")
            print("Saved output to collision_tuned.obj")


def example_hard_obstacle_avoidance():
    """
    Example 3: Hard obstacle avoidance with solid boundaries

    Demonstrates how to prevent plants from growing through solid objects
    like walls, ground, or buildings using hard collision avoidance.
    """
    print("\n=== Example 3: Hard Obstacle Avoidance ===")

    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            # Create ground plane (solid boundary)
            ground_uuid = context.addPatch(
                center=vec3(0, 0, 0),
                size=(5, 5),
                color=RGBcolor(0.6, 0.4, 0.2)  # Brown ground
            )

            # Create vertical wall obstacle
            wall_uuid = context.addPatch(
                center=vec3(1.0, 0, 0.5),
                size=(0.1, 2),
                color=RGBcolor(0.5, 0.5, 0.5)  # Gray wall
            )
            context.rotatePrimitive(wall_uuid, 90, "y")  # Make vertical

            print("Created obstacles: ground plane and vertical wall")

            # Load plant model
            plantarch.loadPlantModelFromLibrary("tomato")

            # Enable hard obstacle avoidance
            # Plants will strictly avoid these obstacles
            plantarch.enableSolidObstacleAvoidance(
                obstacle_UUIDs=[ground_uuid, wall_uuid],
                avoidance_distance=0.3,         # Stay 30cm away
                enable_fruit_adjustment=True,   # Adjust fruit near obstacles
                enable_obstacle_pruning=False   # Don't remove intersecting organs
            )

            print("Enabled solid obstacle avoidance:")
            print("  - Avoidance distance: 0.3m")
            print("  - Fruit adjustment: enabled")

            # Build plant near wall
            plant_id = plantarch.buildPlantInstanceFromLibrary(
                base_position=vec3(0.5, 0, 0),  # Close to wall
                age=5.0
            )

            print(f"Built plant {plant_id} near obstacles")

            # Grow plant - it will avoid obstacles
            print("Growing plant near obstacles...")
            for day in range(30):
                plantarch.advanceTime(1.0)
                if (day + 1) % 10 == 0:
                    print(f"  Day {day + 1}: Plant avoiding obstacles")

            context.writeOBJ("collision_obstacles.obj")
            print("Saved output to collision_obstacles.obj")


def example_static_obstacle_optimization():
    """
    Example 4: Performance optimization with static obstacles

    Shows how to mark non-moving geometry as static to improve collision
    detection performance through BVH (Bounding Volume Hierarchy) optimization.
    """
    print("\n=== Example 4: Static Obstacle Optimization ===")

    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            # Create static environment geometry
            print("Creating static environment geometry...")
            static_uuids = []

            # Ground
            ground = context.addPatch(vec3(0, 0, 0), size=(10, 10))
            static_uuids.append(ground)

            # Building walls (4 sides)
            for i, pos in enumerate([(-3, 0, 1), (3, 0, 1), (0, -3, 1), (0, 3, 1)]):
                wall = context.addPatch(vec3(*pos), size=(6 if i < 2 else 0.2, 0.2 if i < 2 else 6))
                static_uuids.append(wall)

            print(f"Created {len(static_uuids)} static obstacle primitives")

            # Load model
            plantarch.loadPlantModelFromLibrary("soybean")

            # IMPORTANT: Enable collision detection first
            plantarch.enableSoftCollisionAvoidance()

            # Mark static obstacles AFTER enabling collision detection
            # This builds an optimized BVH for fast ray intersection queries
            plantarch.setStaticObstacles(static_uuids)
            print("Marked obstacles as static for BVH optimization")

            # Build multiple plants
            plant_ids = plantarch.buildPlantCanopyFromLibrary(
                canopy_center=vec3(0, 0, 0),
                plant_spacing=vec2(0.5, 0.5),
                plant_count=int2(5, 5),
                age=10.0
            )

            print(f"Built {len(plant_ids)} plants with optimized collision detection")

            # Grow plants - collision detection uses optimized BVH
            print("Growing plants with static obstacle optimization...")
            plantarch.advanceTime(30.0)

            print("Performance tip: Static obstacles enable faster collision detection")
            print("  - BVH built once for static geometry")
            print("  - Reduces ray intersection queries")
            print("  - Ideal for ground, buildings, infrastructure")

            context.writeOBJ("collision_static.obj")
            print("Saved output to collision_static.obj")


def example_organ_filtering():
    """
    Example 5: Collision-relevant organ filtering

    Demonstrates how to selectively include different organ types in collision
    detection to balance accuracy and performance.
    """
    print("\n=== Example 5: Organ-Specific Collision Filtering ===")

    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            plantarch.loadPlantModelFromLibrary("bean")

            # Configure which organs participate in collision detection
            # Default: only leaves are checked (best performance)
            plantarch.setCollisionRelevantOrgans(
                include_internodes=True,   # Include stems
                include_leaves=True,       # Include leaf blades
                include_petioles=False,    # Exclude petioles (better performance)
                include_flowers=False,     # Exclude flowers
                include_fruit=False        # Exclude fruit
            )

            print("Collision detection configured for:")
            print("  - Internodes (stems): YES")
            print("  - Leaves: YES")
            print("  - Petioles: NO (performance optimization)")
            print("  - Flowers: NO")
            print("  - Fruit: NO")

            # Enable collision with organ filtering
            plantarch.enableSoftCollisionAvoidance()

            # Build plants
            plant_ids = plantarch.buildPlantCanopyFromLibrary(
                canopy_center=vec3(0, 0, 0),
                plant_spacing=vec2(0.4, 0.4),
                plant_count=int2(3, 3),
                age=15.0
            )

            # Grow and query collision-relevant geometry
            plantarch.advanceTime(25.0)

            # Get collision-relevant geometry for first plant
            collision_obj_ids = plantarch.getPlantCollisionRelevantObjectIDs(plant_ids[0])
            print(f"\nPlant {plant_ids[0]} has {len(collision_obj_ids)} collision-relevant objects")

            # Highlight collision geometry (optional visualization)
            for obj_id in collision_obj_ids[:5]:  # First 5 objects
                context.setObjectColor(obj_id, RGBcolor(1, 0, 0))  # Red highlight

            print("First 5 collision-relevant objects highlighted in red")

            context.writeOBJ("collision_organs.obj")
            print("Saved output to collision_organs.obj")


def example_combined_workflow():
    """
    Example 6: Complete collision detection workflow

    Demonstrates a realistic scenario combining all collision detection features:
    soft avoidance, hard obstacles, static optimization, and organ filtering.
    """
    print("\n=== Example 6: Complete Collision Detection Workflow ===")

    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            print("Setting up complete collision detection scenario...")

            # 1. Create environment
            print("\n1. Creating environment geometry")
            ground = context.addPatch(vec3(0, 0, 0), size=(8, 8))
            building = context.addPatch(vec3(2, 2, 1), size=(2, 2))
            fence_uuids = [
                context.addPatch(vec3(-3, y, 0.5), size=(0.1, 1))
                for y in range(-3, 4)
            ]

            static_uuids = [ground, building] + fence_uuids
            print(f"   Created {len(static_uuids)} environment primitives")

            # 2. Load plant model
            print("\n2. Loading plant model")
            plantarch.loadPlantModelFromLibrary("cowpea")

            # 3. Configure collision parameters
            print("\n3. Configuring collision detection")
            plantarch.setSoftCollisionAvoidanceParameters(
                view_half_angle_deg=80.0,
                look_ahead_distance=0.1,
                sample_count=256,
                inertia_weight=0.4
            )
            print("   Soft collision parameters: 80° cone, 0.1m look-ahead, 256 samples")

            # 4. Set organ filtering
            plantarch.setCollisionRelevantOrgans(
                include_internodes=True,
                include_leaves=True,
                include_petioles=False,
                include_flowers=False,
                include_fruit=False
            )
            print("   Organ filtering: internodes and leaves only")

            # 5. Enable collision detection
            print("\n4. Enabling collision detection")
            plantarch.enableSoftCollisionAvoidance()

            # 6. Optimize with static obstacles
            plantarch.setStaticObstacles(static_uuids)
            print("   Static obstacles marked for BVH optimization")

            # 7. Enable hard obstacle avoidance
            plantarch.enableSolidObstacleAvoidance(
                obstacle_UUIDs=[building] + fence_uuids,
                avoidance_distance=0.4,
                enable_fruit_adjustment=True
            )
            print("   Hard obstacle avoidance enabled (building + fence)")

            # 8. Build plant canopy
            print("\n5. Building plant canopy")
            plant_ids = plantarch.buildPlantCanopyFromLibrary(
                canopy_center=vec3(-1, -1, 0),
                plant_spacing=vec2(0.5, 0.5),
                plant_count=int2(4, 4),
                age=8.0
            )
            print(f"   Created {len(plant_ids)} plants")

            # 9. Grow plants with all collision features active
            print("\n6. Growing plants (collision detection active)")
            for day in range(0, 35, 5):
                plantarch.advanceTime(5.0)
                prim_count = context.getPrimitiveCount()
                print(f"   Day {day + 5}: {prim_count} primitives")

            # 10. Summary
            print("\n7. Summary")
            print(f"   Total primitives: {context.getPrimitiveCount()}")
            print(f"   Plants: {len(plant_ids)}")
            print("   Collision features used:")
            print("     ✓ Soft collision avoidance (plant-plant)")
            print("     ✓ Hard obstacle avoidance (building, fence)")
            print("     ✓ Static obstacle optimization (BVH)")
            print("     ✓ Organ filtering (performance)")

            context.writeOBJ("collision_complete.obj")
            print("\nSaved output to collision_complete.obj")


if __name__ == "__main__":
    print("=" * 70)
    print("PlantArchitecture Collision Detection Examples")
    print("=" * 70)

    # Run all examples
    example_basic_soft_collision()
    example_tuned_collision_parameters()
    example_hard_obstacle_avoidance()
    example_static_obstacle_optimization()
    example_organ_filtering()
    example_combined_workflow()

    print("\n" + "=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("1. Soft collision avoidance guides natural plant growth")
    print("2. Hard obstacles strictly prevent growth through boundaries")
    print("3. Static obstacles enable BVH optimization for performance")
    print("4. Organ filtering balances accuracy and computational cost")
    print("5. Parameters can be tuned for different plant densities")
    print("\nFor more information, see the PlantArchitecture documentation.")
