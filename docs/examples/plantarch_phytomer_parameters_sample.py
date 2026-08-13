"""Customize nested plant architecture (phytomer) parameters.

Demonstrates the typed parameter model: load a library species, pull its shoot
parameters as a typed object, mutate nested phytomer/leaf-prototype fields, define
a new shoot type, and build a plant that uses it. Also shows setting the flat
carbohydrate model parameters.

IMPORTANT - which build path honors a custom shoot type:

    Custom shoot types only take effect when you assemble the plant yourself with
    addPlantInstance() + addBaseStemShoot(), passing your shoot type label.

    buildPlantInstanceFromLibrary() calls a hard-coded builder for the species,
    which uses that species' own shoot types. Defining a new shoot type has no
    effect on it -- even redefining an existing label such as "trunk" is ignored.

Run:
    python docs/examples/plantarch_phytomer_parameters_sample.py
"""

from pyhelios import Context, PlantArchitecture
from pyhelios.types import vec3, AxisRotation
from pyhelios.plant_architecture_params import (
    RandomParameterFloat,
    RandomParameterInt,
)


def build_with_leaf_scale(prototype_scale: float) -> float:
    """Build a bean plant whose leaves use the given prototype scale.

    Returns the resulting total leaf area in m^2.
    """
    with Context() as context:
        pa = PlantArchitecture(context)

        # Loading a library model registers that species' shoot types, which we
        # use as the template to modify. Bean defines "unifoliate" and
        # "trifoliate" (each species has its own labels; there is no generic
        # "stem" type).
        pa.loadPlantModelFromLibrary("bean")

        # Pull the full nested parameter set as a typed object.
        sp = pa.getCurrentShootParameters("trifoliate", return_typed=True)

        # --- Mutate nested phytomer / leaf-prototype parameters ---
        sp.max_nodes = RandomParameterInt.constant(15)
        # leaf.pitch is in DEGREES (Helios converts internally with deg2rad).
        sp.phytomer_parameters.leaf.pitch = RandomParameterFloat.uniform(40, 60)
        sp.phytomer_parameters.leaf.prototype_scale = RandomParameterFloat.constant(
            prototype_scale
        )
        sp.phytomer_parameters.internode.radial_subdivisions = 9
        sp.phytomer_parameters.leaf.prototype.subdivisions = 5

        # Register the modified parameters under a new label.
        pa.defineShootType("custom_stem", sp)

        # Build the plant manually so the custom shoot type is actually used.
        plant_id = pa.addPlantInstance(vec3(0, 0, 0), 0.0)
        pa.addBaseStemShoot(
            plant_id=plant_id,
            current_node_number=5,
            base_rotation=AxisRotation(0, 0, 0),
            internode_radius=0.005,
            internode_length_max=0.05,
            internode_length_scale_factor_fraction=1.0,
            leaf_scale_factor_fraction=1.0,
            radius_taper=0.9,
            shoot_type_label="custom_stem",
        )

        return pa.getPlantLeafArea(plant_id)


def show_parameter_roundtrip() -> None:
    """Confirm a modified parameter survives the trip through the C++ layer."""
    with Context() as context:
        pa = PlantArchitecture(context)
        pa.loadPlantModelFromLibrary("almond")

        sp = pa.getCurrentShootParameters("trunk", return_typed=True)
        print("  almond trunk leaf.pitch (default):",
              sp.phytomer_parameters.leaf.pitch.to_dict())

        sp.phytomer_parameters.leaf.pitch = RandomParameterFloat.uniform(40, 60)
        pa.defineShootType("custom_trunk", sp)

        out = pa.getCurrentShootParameters("custom_trunk")
        print("  custom_trunk leaf.pitch (read back):",
              out["phytomer_parameters"]["leaf"]["pitch"])


def show_carbohydrate_parameters() -> None:
    """Apply the flat carbohydrate parameter struct to a plant instance."""
    with Context() as context:
        pa = PlantArchitecture(context)
        pa.loadPlantModelFromLibrary("almond")

        # The native API has no per-plant getter, so this returns the C++
        # default-constructed template to modify and apply.
        carb = pa.getDefaultCarbohydrateParameters(return_typed=True)
        print(f"  SLA default: {carb.SLA:.6f}")
        carb.SLA *= 1.1
        print(f"  SLA tweaked: {carb.SLA:.6f}")

        # age is in DAYS. An almond needs roughly half a year of simulated growth
        # before it carries appreciable leaf area; at age=1 it is bare wood.
        plant_id = pa.buildPlantInstanceFromLibrary(vec3(0, 0, 0), age=180.0)
        pa.setPlantCarbohydrateParameters(plant_id, carb)
        print(f"  applied to plant {plant_id}; "
              f"leaf area = {pa.getPlantLeafArea(plant_id):.5f} m^2")


def main() -> None:
    print("1. Nested parameter round-trip")
    show_parameter_roundtrip()
    print()

    print("2. Custom shoot type actually changing the geometry")
    # Leaf area scales with the square of the prototype scale, which shows the
    # custom shoot type is really driving the build.
    for scale in (0.02, 0.05, 0.10):
        area = build_with_leaf_scale(scale)
        print(f"  prototype_scale = {scale:.2f}  ->  leaf area = {area:.6f} m^2")
    print()

    print("3. Carbohydrate model parameters")
    show_carbohydrate_parameters()


if __name__ == "__main__":
    main()
