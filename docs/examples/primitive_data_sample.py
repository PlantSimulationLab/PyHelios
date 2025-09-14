"""
PyHelios Primitive Data Example

This example demonstrates the primitive data API for storing and retrieving
user-defined data associated with geometric primitives. The primitive data
system allows you to attach arbitrary key-value pairs to any primitive.

Supported data types (Phase 1):
- int: Integer values
- float: Floating-point values  
- str: String values
- vec3: 3D vector values
- list/tuple: 3-element sequences treated as vec3

Extended data types (Phase 2):
- bool: Boolean values (True/False)
- uint: Unsigned integer values (for large positive numbers)
- double: Double-precision floating-point values
- vec2: 2D vector values
- vec4: 4D vector values
- int2: 2D integer vector values
- int3: 3D integer vector values
- int4: 4D integer vector values
- list/tuple: 2/3/4-element sequences with automatic type detection
"""

from pyhelios import Context
from pyhelios.types import *

def main():
    print("=== PyHelios Primitive Data Example ===")
    
    # Create a context
    context = Context()
    
    # Add some geometry to work with
    center = vec3(0, 0, 0)
    size = vec2(2, 2)
    color = RGBcolor(0.5, 0.8, 0.3)
    
    # Create a patch
    patch_uuid = context.addPatch(center=center, size=size, color=color)
    print(f"Created patch with UUID: {patch_uuid}")
    
    try:
        # === SETTING PRIMITIVE DATA ===
        print("\n--- Setting Primitive Data ---")
        
        # Set integer data
        context.setPrimitiveData(patch_uuid, "plant_age", 25)
        print("Set plant_age (int): 25")
        
        # Set float data
        context.setPrimitiveData(patch_uuid, "leaf_area", 12.5)
        print("Set leaf_area (float): 12.5")
        
        # Set string data
        context.setPrimitiveData(patch_uuid, "species", "Quercus alba")
        print("Set species (str): 'Quercus alba'")
        
        # Set vec3 data
        wind_direction = vec3(1.0, 0.5, 0.2)
        context.setPrimitiveData(patch_uuid, "wind_direction", wind_direction)
        print(f"Set wind_direction (vec3): {wind_direction}")
        
        # Set vec3 data using vec3 type
        soil_nutrients = vec3(2.1, 1.8, 3.2)
        context.setPrimitiveData(patch_uuid, "soil_nutrients", soil_nutrients)
        print(f"Set soil_nutrients (vec3): {soil_nutrients}")
        
        # === CHECKING DATA EXISTENCE ===
        print("\n--- Checking Data Existence ---")
        
        labels_to_check = ["plant_age", "leaf_area", "species", "wind_direction", "nonexistent"]
        
        for label in labels_to_check:
            exists = context.doesPrimitiveDataExist(patch_uuid, label)
            print(f"Data '{label}' exists: {exists}")
        
        # === GETTING PRIMITIVE DATA (Auto-Detection) ===
        print("\n--- Getting Primitive Data (Auto-Detection) ---")
        
        # Get integer data - type automatically detected
        age = context.getPrimitiveData(patch_uuid, "plant_age")
        print(f"Retrieved plant_age (auto-detected as {type(age).__name__}): {age}")
        
        # Get float data - type automatically detected
        area = context.getPrimitiveData(patch_uuid, "leaf_area")
        print(f"Retrieved leaf_area (auto-detected as {type(area).__name__}): {area}")
        
        # Get string data - type automatically detected
        species = context.getPrimitiveData(patch_uuid, "species")
        print(f"Retrieved species (auto-detected as {type(species).__name__}): '{species}'")
        
        # Get vec3 data - type automatically detected
        wind = context.getPrimitiveData(patch_uuid, "wind_direction")
        print(f"Retrieved wind_direction (auto-detected as {type(wind).__name__}): {wind}")
        
        # Get vec3 data - type automatically detected
        nutrients_list = context.getPrimitiveData(patch_uuid, "soil_nutrients")
        print(f"Retrieved soil_nutrients (auto-detected as {type(nutrients_list).__name__}): {nutrients_list}")
        
        # === GETTING PRIMITIVE DATA (Explicit Types - for backward compatibility) ===
        print("\n--- Getting Primitive Data (Explicit Types - Optional) ---")
        
        # You can still specify types explicitly for backward compatibility
        age_explicit = context.getPrimitiveData(patch_uuid, "plant_age", int)
        area_explicit = context.getPrimitiveData(patch_uuid, "leaf_area", float)
        species_explicit = context.getPrimitiveData(patch_uuid, "species", str)
        wind_explicit = context.getPrimitiveData(patch_uuid, "wind_direction", vec3)
        nutrients_explicit = context.getPrimitiveData(patch_uuid, "soil_nutrients", list)
        
        print(f"Explicit types still work - age: {age_explicit}, area: {area_explicit}")
        print(f"Explicit types still work - species: '{species_explicit}', wind: {wind_explicit}")
        print(f"Explicit types still work - nutrients: {nutrients_explicit}")
        
        # === EXTENDED TYPES (PHASE 2) ===
        print("\n--- Extended Data Types (Phase 2) ---")
        
        # Boolean data
        context.setPrimitiveData(patch_uuid, "is_flowering", True)
        context.setPrimitiveData(patch_uuid, "has_disease", False)
        print("Set is_flowering (bool): True")
        print("Set has_disease (bool): False")
        
        # Unsigned integer (large positive values)
        large_id = 3000000000  # Exceeds signed int32 range
        context.setPrimitiveData(patch_uuid, "global_id", large_id)
        print(f"Set global_id (uint): {large_id}")
        
        # vec2 data
        uv_coords = vec2(0.5, 0.7)
        context.setPrimitiveData(patch_uuid, "uv_coordinates", uv_coords)
        print(f"Set uv_coordinates (vec2): {uv_coords}")
        
        # vec4 data
        rgba_color = vec4(0.8, 0.6, 0.4, 0.9)
        context.setPrimitiveData(patch_uuid, "rgba_color", rgba_color)
        print(f"Set rgba_color (vec4): {rgba_color}")
        
        # int2 data (screen coordinates)
        screen_pos = int2(640, 480)
        context.setPrimitiveData(patch_uuid, "screen_position", screen_pos)
        print(f"Set screen_position (int2): {screen_pos}")
        
        # int3 data (voxel indices)
        voxel_index = int3(12, 8, 15)
        context.setPrimitiveData(patch_uuid, "voxel_index", voxel_index)
        print(f"Set voxel_index (int3): {voxel_index}")
        
        # int4 data (RGBA as integers)
        rgba_int = int4(255, 128, 64, 230)
        context.setPrimitiveData(patch_uuid, "rgba_int", rgba_int)
        print(f"Set rgba_int (int4): {rgba_int}")
        
        # Vector type examples
        context.setPrimitiveData(patch_uuid, "size_2d", vec2(10.5, 15.2))
        context.setPrimitiveData(patch_uuid, "grid_pos", int2(5, 7))
        context.setPrimitiveData(patch_uuid, "transform", vec4(1.0, 0.0, 0.0, 1.0))
        context.setPrimitiveData(patch_uuid, "indices", int4(100, 200, 300, 400))
        print("Set size_2d (vec2): (10.5, 15.2)")
        print("Set grid_pos (int2): (5, 7)")
        print("Set transform (vec4): (1.0, 0.0, 0.0, 1.0)")
        print("Set indices (int4): (100, 200, 300, 400)")
        
        # Retrieving extended types (auto-detection)
        print("\n--- Retrieving Extended Types (Auto-Detection) ---")
        
        flowering = context.getPrimitiveData(patch_uuid, "is_flowering")
        disease = context.getPrimitiveData(patch_uuid, "has_disease")
        print(f"Retrieved is_flowering (auto-detected as {type(flowering).__name__}): {flowering}")
        print(f"Retrieved has_disease (auto-detected as {type(disease).__name__}): {disease}")
        
        global_id = context.getPrimitiveData(patch_uuid, "global_id")
        print(f"Retrieved global_id (auto-detected as {type(global_id).__name__}): {global_id}")
        
        uv = context.getPrimitiveData(patch_uuid, "uv_coordinates")
        print(f"Retrieved uv_coordinates (auto-detected as {type(uv).__name__}): {uv}")
        
        rgba = context.getPrimitiveData(patch_uuid, "rgba_color")
        print(f"Retrieved rgba_color (auto-detected as {type(rgba).__name__}): {rgba}")
        
        screen = context.getPrimitiveData(patch_uuid, "screen_position")
        print(f"Retrieved screen_position (auto-detected as {type(screen).__name__}): {screen}")
        
        voxel = context.getPrimitiveData(patch_uuid, "voxel_index")
        print(f"Retrieved voxel_index (auto-detected as {type(voxel).__name__}): {voxel}")
        
        rgba_ints = context.getPrimitiveData(patch_uuid, "rgba_int")
        print(f"Retrieved rgba_int (auto-detected as {type(rgba_ints).__name__}): {rgba_ints}")
        
        # Retrieve auto-detected types
        size_list = context.getPrimitiveData(patch_uuid, "size_2d")
        grid_list = context.getPrimitiveData(patch_uuid, "grid_pos")
        print(f"Retrieved size_2d (auto-detected as {type(size_list).__name__}): {size_list}")
        print(f"Retrieved grid_pos (auto-detected as {type(grid_list).__name__}): {grid_list}")
        
        # Note: explicit list types still work for special cases
        size_list_explicit = context.getPrimitiveData(patch_uuid, "size_2d", "list_vec2")
        grid_list_explicit = context.getPrimitiveData(patch_uuid, "grid_pos", "list_int2")
        print(f"Explicit list types still work - size_2d: {size_list_explicit}")
        print(f"Explicit list types still work - grid_pos: {grid_list_explicit}")
        
        # === DATA TYPE INTROSPECTION ===
        print("\n--- Data Type Introspection ---")
        
        data_labels = ["plant_age", "leaf_area", "species", "wind_direction", 
                      "is_flowering", "global_id", "uv_coordinates", "rgba_color",
                      "screen_position", "voxel_index", "rgba_int"]
        
        # HeliosDataType constants
        type_names = {
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
            11: "HELIOS_TYPE_BOOL",
            12: "HELIOS_TYPE_UNKNOWN"
        }
        
        for label in data_labels:
            data_type = context.getPrimitiveDataType(patch_uuid, label)
            type_name = type_names.get(data_type, f"UNKNOWN_{data_type}")
            size = context.getPrimitiveDataSize(patch_uuid, label)
            print(f"Data '{label}': type={type_name}, size={size}")
        
        # === WORKING WITH MULTIPLE PRIMITIVES ===
        print("\n--- Working with Multiple Primitives ---")
        
        # Create more geometry
        sphere_center = vec3(3, 0, 0)
        sphere_uuid = context.addSphere(center=sphere_center, radius=1.0, ndivs=8)[0]  # Get first triangle UUID
        print(f"Created sphere with first triangle UUID: {sphere_uuid}")
        
        # Add data to sphere
        context.setPrimitiveData(sphere_uuid, "plant_age", 15)  # Different age
        context.setPrimitiveData(sphere_uuid, "species", "Pinus sylvestris")  # Different species
        
        # Compare data between primitives (using auto-detection)
        patch_species = context.getPrimitiveData(patch_uuid, "species")
        sphere_species = context.getPrimitiveData(sphere_uuid, "species")
        
        print(f"Patch species: '{patch_species}' (auto-detected as {type(patch_species).__name__})")
        print(f"Sphere species: '{sphere_species}' (auto-detected as {type(sphere_species).__name__})")
        
        # === ERROR HANDLING EXAMPLES ===
        print("\n--- Error Handling Examples ---")
        
        # Try to get non-existent data
        try:
            context.getPrimitiveData(patch_uuid, "nonexistent")
        except Exception as e:
            print(f"Expected error for non-existent data: {type(e).__name__}")
        
        # Try to set unsupported data type
        try:
            context.setPrimitiveData(patch_uuid, "bad_data", {"dict": "not_supported"})
        except ValueError as e:
            print(f"Expected error for unsupported type: {e}")
        
        print("\n=== Primitive Data Example Complete ===")
        
    except NotImplementedError as e:
        print(f"\nNote: {e}")
        print("This functionality requires the updated C++ wrapper functions.")
        print("The API is ready, but native implementation is pending.")
        
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("This may indicate an issue with the primitive data implementation.")


def demonstrate_advanced_usage():
    """
    Demonstrate advanced usage patterns for primitive data.
    """
    print("\n=== Advanced Primitive Data Usage ===")
    
    context = Context()
    
    try:
        # Create a small canopy
        patch_uuids = []
        for i in range(3):
            for j in range(3):
                center = vec3(i * 2, j * 2, 0)
                size = vec2(1.5, 1.5)
                uuid = context.addPatch(center=center, size=size)
                patch_uuids.append(uuid)
        
        print(f"Created {len(patch_uuids)} patches for canopy simulation")
        
        # Set environmental data for each patch
        for i, uuid in enumerate(patch_uuids):
            # Simulate environmental gradients
            light_level = 100.0 - i * 5.0  # Decreasing light
            temperature = 25.0 + i * 0.5   # Increasing temperature
            height = i * 0.1                # Varying heights
            
            # Store environmental data
            context.setPrimitiveData(uuid, "light_level", light_level)
            context.setPrimitiveData(uuid, "temperature", temperature) 
            context.setPrimitiveData(uuid, "height", height)
            context.setPrimitiveData(uuid, "patch_id", i)
            
            # Store position as vec3
            x, y = i % 3 * 2, i // 3 * 2
            position = [float(x), float(y), height]
            context.setPrimitiveData(uuid, "position", position)
        
        # Analyze the canopy data
        print("\n--- Canopy Analysis ---")
        total_light = 0.0
        avg_temperature = 0.0
        
        for uuid in patch_uuids:
            light = context.getPrimitiveData(uuid, "light_level")
            temp = context.getPrimitiveData(uuid, "temperature")
            patch_id = context.getPrimitiveData(uuid, "patch_id")
            position = context.getPrimitiveData(uuid, "position")
            
            total_light += light
            avg_temperature += temp
            
            print(f"Patch {patch_id}: Light={light:.1f}, Temp={temp:.1f}°C, Pos={position} (types: {type(light).__name__}, {type(temp).__name__}, {type(patch_id).__name__}, {type(position).__name__})")
        
        avg_temperature /= len(patch_uuids)
        print(f"\nCanopy Summary:")
        print(f"  Total light intercepted: {total_light:.1f}")
        print(f"  Average temperature: {avg_temperature:.1f}°C")
        print(f"  Number of patches: {len(patch_uuids)}")
        
    except NotImplementedError:
        print("Advanced usage requires native primitive data implementation")
    except Exception as e:
        print(f"Error in advanced usage: {e}")


if __name__ == "__main__":
    main()
    demonstrate_advanced_usage()