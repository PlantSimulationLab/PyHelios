"""
Example demonstrating collision avoidance and growth steering with PlantArchitecture.

Covers the collision API end to end:
  1. Basic soft collision avoidance
  2. Parameter tuning for different scenarios
  3. Hard obstacle avoidance with solid boundaries
  4. Performance optimization with static obstacles
  5. Organ-specific collision filtering
  6. Attraction points, which steer growth toward targets
  7. A complete realistic workflow

ORDERING MATTERS: collision hooks run while each phytomer is constructed, so a plant
must be BUILT before collision is enabled, and growth that should be steered has to
happen AFTER. Enabling collision first makes otherwise identical runs diverge from
day zero.

For a visual A/B demonstration that collision avoidance actually holds foliage clear
of a barrier, see plantarch_collision_movie.py.
"""

from pyhelios import Context, PlantArchitecture
from pyhelios.types import vec3, vec2


def basic_soft_collision(plantarch):
    """Soft avoidance steers shoot axes away from nearby geometry."""
    print("1. Basic soft collision avoidance")

    plantarch.loadPlantModelFromLibrary("bean")
    plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 5.0)

    # Enable AFTER building, then grow so the steering has something to act on.
    plantarch.enableSoftCollisionAvoidance()
    plantarch.advanceTime(15.0)

    print(f"   plant {plant_id}: {len(plantarch.getAllPlantUUIDs(plant_id))} primitives")
    plantarch.disableCollisionDetection()
    print()


def tune_collision_parameters(plantarch):
    """The four steering parameters trade fidelity against cost."""
    print("2. Parameter tuning")

    plantarch.enableSoftCollisionAvoidance()

    # view_half_angle_deg, look_ahead_distance, sample_count, inertia_weight.
    # A wider cone and more samples steer more reliably and cost more per phytomer.
    plantarch.setSoftCollisionAvoidanceParameters(80.0, 0.1, 256, 0.4)
    print("   default-equivalent: 80 deg cone, 0.1 m look-ahead, 256 samples")

    plantarch.setSoftCollisionAvoidanceParameters(45.0, 0.05, 64, 0.6)
    print("   cheaper:            45 deg cone, 0.05 m look-ahead, 64 samples")

    plantarch.disableCollisionDetection()
    print()


def hard_obstacle_avoidance(context, plantarch):
    """Solid obstacles can additionally prune organs that end up inside them."""
    print("3. Hard obstacle avoidance")

    wall = context.addPatch(center=vec3(0.3, 0, 0.3), size=vec2(1.0, 1.0))
    plantarch.loadPlantModelFromLibrary("bean")
    plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 5.0)

    plantarch.enableSolidObstacleAvoidance(
        [wall],
        avoidance_distance=0.1,
        enable_fruit_adjustment=False,
        enable_obstacle_pruning=True,
    )
    plantarch.advanceTime(15.0)

    print(f"   plant {plant_id}: {len(plantarch.getAllPlantUUIDs(plant_id))} primitives")
    plantarch.disableCollisionDetection()
    print()


def static_obstacles_for_performance(context, plantarch):
    """Geometry that never moves can be declared static so the BVH is built once."""
    print("4. Static obstacles")

    ground = context.addPatch(center=vec3(0, 0, 0), size=vec2(5.0, 5.0))

    plantarch.enableSoftCollisionAvoidance()
    # setStaticObstacles() must follow enableSoftCollisionAvoidance().
    plantarch.setStaticObstacles([ground])
    print("   ground patch registered as a static obstacle")

    plantarch.disableCollisionDetection()
    print()


def organ_specific_filtering(plantarch):
    """Restricting collision to the organs that matter cuts the per-step cost."""
    print("5. Organ-specific filtering")

    plantarch.enableSoftCollisionAvoidance()

    # internodes, leaves, petioles, flowers, fruit
    plantarch.setCollisionRelevantOrgans(False, True, False, False, False)
    print("   leaves only -- the cheapest useful setting for canopy work")

    plantarch.setCollisionRelevantOrgans(True, True, True, False, True)
    print("   internodes, leaves, petioles and fruit")

    plantarch.disableCollisionDetection()
    print()


def attraction_points():
    """Attraction points are the counterpart to collision: what to grow TOWARD.

    Runs in its own Context so the steering is visible on a fresh plant rather than
    mixed in with the collision state configured above.
    """
    print("6. Attraction points")

    with Context() as context, PlantArchitecture(context) as plantarch:
        plantarch.disableMessages()
        plantarch.loadPlantModelFromLibrary("bindweed")
        plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 1.0)

        # A vertical line of targets standing in for a trellis wire.
        wire = [vec3(0.5, 0.0, 0.02 * z) for z in range(1, 25)]
        plantarch.enableAttractionPoints(
            wire,
            plant_id=plant_id,
            view_half_angle_deg=89.0,
            look_ahead_distance=2.0,
            attraction_weight=1.0,
        )
        plantarch.advanceTime(40.0)

        bases = plantarch.getPlantLeafBases(plant_id)
        if bases:
            mean_x = sum(b.x for b in bases) / len(bases)
            print(f"   mean leaf x = {mean_x:.3f} (targets sit at x = 0.5)")

        plantarch.disableAttractionPoints(plant_id=plant_id)
    print()


def complete_workflow(context, plantarch):
    """The whole sequence in the order it has to happen."""
    print("7. Complete workflow")

    # 1. Obstacle geometry first, so it exists to be avoided.
    wall = context.addPatch(center=vec3(0.4, 0, 0.4), size=vec2(1.2, 1.2))

    # 2. Load the model and BUILD the plant.
    plantarch.loadPlantModelFromLibrary("bean")
    plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 5.0)

    # 3. Only now enable collision, and configure it.
    plantarch.enableSoftCollisionAvoidance()
    plantarch.setSoftCollisionAvoidanceParameters(80.0, 0.1, 256, 0.4)
    plantarch.setCollisionRelevantOrgans(True, True, False, False, False)
    plantarch.setStaticObstacles([wall])

    # 4. Grow. Everything above steers this.
    plantarch.advanceTime(20.0)

    leaves = plantarch.getPlantLeafObjectIDs(plant_id)
    print(f"   plant {plant_id}: {len(plantarch.getAllPlantUUIDs(plant_id))} primitives, "
          f"{len(leaves)} leaf objects")

    plantarch.disableCollisionDetection()
    print()


def main():
    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()

            print("=== PlantArchitecture Collision Detection Examples ===\n")

            basic_soft_collision(plantarch)
            tune_collision_parameters(plantarch)
            hard_obstacle_avoidance(context, plantarch)
            static_obstacles_for_performance(context, plantarch)
            organ_specific_filtering(plantarch)
            attraction_points()
            complete_workflow(context, plantarch)

            print("Done.")


if __name__ == "__main__":
    main()
