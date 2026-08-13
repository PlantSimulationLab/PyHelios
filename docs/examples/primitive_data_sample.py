"""
PyHelios Primitive Data Example

Demonstrates the primitive data API for attaching user-defined key-value data to
geometric primitives.

Setters are type-specific -- there is no generic `setPrimitiveData()`. Pick the
setter matching the value you are storing:

    setPrimitiveDataInt     setPrimitiveDataUInt    setPrimitiveDataFloat
    setPrimitiveDataDouble  setPrimitiveDataString  setPrimitiveDataVec2
    setPrimitiveDataVec3    setPrimitiveDataVec4    setPrimitiveDataInt2
    setPrimitiveDataInt3    setPrimitiveDataInt4

The getter, by contrast, is generic: `getPrimitiveData(uuid, label)` detects the
stored type automatically.

There is no boolean setter. Store flags as ints (0/1) with setPrimitiveDataInt.

Every setter also accepts a list of UUIDs as its first argument, which assigns the
same value to every listed primitive.

Run:
    python docs/examples/primitive_data_sample.py
"""

import sys

from pyhelios import Context
from pyhelios.types import vec2, vec3, vec4, int2, int3, int4, RGBcolor


# Type codes returned by getPrimitiveDataType().
HELIOS_TYPE_NAMES = {
    0: "HELIOS_TYPE_INT",
    1: "HELIOS_TYPE_UINT",
    2: "HELIOS_TYPE_FLOAT",
    3: "HELIOS_TYPE_DOUBLE",
    4: "HELIOS_TYPE_VEC2",
    5: "HELIOS_TYPE_VEC3",
    6: "HELIOS_TYPE_VEC4",
    7: "HELIOS_TYPE_INT2",
    8: "HELIOS_TYPE_INT3",
    9: "HELIOS_TYPE_INT4",
    10: "HELIOS_TYPE_STRING",
}


def basic_types(context, patch_uuid):
    """Store and retrieve the common scalar and vector types."""
    print("\n--- Setting Primitive Data ---")

    context.setPrimitiveDataInt(patch_uuid, "plant_age", 25)
    print("Set plant_age (int): 25")

    context.setPrimitiveDataFloat(patch_uuid, "leaf_area", 12.5)
    print("Set leaf_area (float): 12.5")

    context.setPrimitiveDataString(patch_uuid, "species", "Quercus alba")
    print("Set species (str): 'Quercus alba'")

    context.setPrimitiveDataVec3(patch_uuid, "wind_direction", vec3(1.0, 0.5, 0.2))
    print("Set wind_direction (vec3): (1.0, 0.5, 0.2)")

    context.setPrimitiveDataVec3(patch_uuid, "soil_nutrients", vec3(2.1, 1.8, 3.2))
    print("Set soil_nutrients (vec3): (2.1, 1.8, 3.2)")

    print("\n--- Checking Data Existence ---")
    for label in ["plant_age", "leaf_area", "species", "wind_direction", "nonexistent"]:
        exists = context.doesPrimitiveDataExist(patch_uuid, label)
        print(f"Data '{label}' exists: {exists}")

    print("\n--- Getting Primitive Data (type auto-detected) ---")
    for label in ["plant_age", "leaf_area", "species", "wind_direction", "soil_nutrients"]:
        value = context.getPrimitiveData(patch_uuid, label)
        print(f"Retrieved {label} (as {type(value).__name__}): {value}")

    # Vector types come back as plain Python lists, not vec2/vec3/vec4 objects,
    # so index them ([0], [1], ...) rather than using .x / .y / .z.
    wind = context.getPrimitiveData(patch_uuid, "wind_direction")
    print(f"Wind x-component via index: {wind[0]}")


def extended_types(context, patch_uuid):
    """Store and retrieve the remaining supported types."""
    print("\n--- Extended Data Types ---")

    # No boolean setter exists; use an int flag instead.
    context.setPrimitiveDataInt(patch_uuid, "is_flowering", 1)
    context.setPrimitiveDataInt(patch_uuid, "has_disease", 0)
    print("Set is_flowering / has_disease (int flags): 1 / 0")

    # UInt handles values beyond the signed 32-bit range.
    context.setPrimitiveDataUInt(patch_uuid, "global_id", 3000000000)
    print("Set global_id (uint): 3000000000")

    context.setPrimitiveDataDouble(patch_uuid, "precise_measurement", 3.14159265358979)
    print("Set precise_measurement (double): 3.14159265358979")

    context.setPrimitiveDataVec2(patch_uuid, "uv_coordinates", vec2(0.5, 0.7))
    context.setPrimitiveDataVec4(patch_uuid, "rgba_color", vec4(0.8, 0.6, 0.4, 0.9))
    context.setPrimitiveDataInt2(patch_uuid, "screen_position", int2(640, 480))
    context.setPrimitiveDataInt3(patch_uuid, "voxel_index", int3(12, 8, 15))
    context.setPrimitiveDataInt4(patch_uuid, "rgba_int", int4(255, 128, 64, 230))
    print("Set uv_coordinates (vec2), rgba_color (vec4), screen_position (int2),")
    print("    voxel_index (int3), rgba_int (int4)")

    print("\n--- Retrieving Extended Types ---")
    for label in ["is_flowering", "global_id", "precise_measurement",
                  "uv_coordinates", "rgba_color", "screen_position",
                  "voxel_index", "rgba_int"]:
        value = context.getPrimitiveData(patch_uuid, label)
        print(f"Retrieved {label} (as {type(value).__name__}): {value}")


def type_introspection(context, patch_uuid):
    """Report the stored type and element count for each label."""
    print("\n--- Data Type Introspection ---")

    labels = ["plant_age", "leaf_area", "species", "wind_direction",
              "is_flowering", "global_id", "precise_measurement",
              "uv_coordinates", "rgba_color", "screen_position",
              "voxel_index", "rgba_int"]

    for label in labels:
        data_type = context.getPrimitiveDataType(patch_uuid, label)
        type_name = HELIOS_TYPE_NAMES.get(data_type, f"UNKNOWN_{data_type}")
        size = context.getPrimitiveDataSize(patch_uuid, label)
        print(f"Data '{label}': type={type_name}, size={size}")


def multiple_primitives(context, patch_uuid):
    """Compare data across primitives and set data in bulk."""
    print("\n--- Working with Multiple Primitives ---")

    sphere_uuids = context.addSphere(center=vec3(3, 0, 0), radius=1.0, ndivs=8)
    sphere_uuid = sphere_uuids[0]
    print(f"Created sphere with {len(sphere_uuids)} primitives")

    context.setPrimitiveDataInt(sphere_uuid, "plant_age", 15)
    context.setPrimitiveDataString(sphere_uuid, "species", "Pinus sylvestris")

    print(f"Patch species:  '{context.getPrimitiveData(patch_uuid, 'species')}'")
    print(f"Sphere species: '{context.getPrimitiveData(sphere_uuid, 'species')}'")

    # Passing a list of UUIDs assigns the same value to every primitive.
    context.setPrimitiveDataFloat(sphere_uuids, "temperature", 22.5)
    temperatures = context.getPrimitiveDataArray(sphere_uuids, "temperature")
    print(f"Bulk-set temperature on {len(sphere_uuids)} primitives; "
          f"array shape {temperatures.shape}, all equal: "
          f"{bool((temperatures == 22.5).all())}")


def error_handling(context, patch_uuid):
    """Show that invalid access raises rather than returning a placeholder."""
    print("\n--- Error Handling ---")

    try:
        context.getPrimitiveData(patch_uuid, "nonexistent")
        print("ERROR: reading missing data should have raised")
    except Exception as e:
        print(f"Reading missing data raised {type(e).__name__} (expected)")

    try:
        context.setPrimitiveDataInt(patch_uuid, "bad_data", {"dict": "not_supported"})
        print("ERROR: an unsupported value type should have raised")
    except Exception as e:
        print(f"Unsupported value type raised {type(e).__name__} (expected)")


def advanced_usage():
    """Per-primitive data across a small canopy."""
    print("\n=== Advanced Primitive Data Usage ===")

    context = Context()

    patch_uuids = []
    for i in range(3):
        for j in range(3):
            uuid = context.addPatch(
                center=vec3(i * 0.5, j * 0.5, 0),
                size=vec2(0.4, 0.4),
                color=RGBcolor(0.2, 0.6, 0.2),
            )
            patch_uuids.append(uuid)
    print(f"Created {len(patch_uuids)} patches for canopy simulation")

    # Give each patch its own values.
    for index, uuid in enumerate(patch_uuids):
        context.setPrimitiveDataFloat(uuid, "light_intercepted", 100.0 + index * 12.5)
        context.setPrimitiveDataFloat(uuid, "temperature", 20.0 + index * 0.75)
        context.setPrimitiveDataInt(uuid, "patch_index", index)

    light = context.getPrimitiveDataArray(patch_uuids, "light_intercepted")
    temperature = context.getPrimitiveDataArray(patch_uuids, "temperature")

    print(f"  Total light intercepted: {light.sum():.1f}")
    print(f"  Average temperature: {temperature.mean():.1f} C")
    print(f"  Number of patches: {len(patch_uuids)}")


def main():
    print("=== PyHelios Primitive Data Example ===")

    context = Context()
    patch_uuid = context.addPatch(
        center=vec3(0, 0, 0),
        size=vec2(2, 2),
        color=RGBcolor(0.5, 0.8, 0.3),
    )
    print(f"Created patch with UUID: {patch_uuid}")

    basic_types(context, patch_uuid)
    extended_types(context, patch_uuid)
    type_introspection(context, patch_uuid)
    multiple_primitives(context, patch_uuid)
    error_handling(context, patch_uuid)

    print("\n=== Primitive Data Example Complete ===")

    advanced_usage()
    return 0


if __name__ == "__main__":
    sys.exit(main())
