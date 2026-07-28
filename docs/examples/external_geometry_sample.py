"""
PyHelios External Geometry Import Example

This example demonstrates the four main ways to import external geometry into PyHelios:
1. Loading PLY files
2. Loading OBJ files  
3. Loading Helios XML files
4. Importing from NumPy arrays (compatible with trimesh, Open3D, etc.)

It also shows how to retrieve primitive information and work with the data.
"""

from pathlib import Path

import numpy as np
from pyhelios import Context
from pyhelios.types import *

# Resolve asset paths relative to this script so the example can be run
# from any working directory.
MODELS_DIR = Path(__file__).parent / "models"

def main():
    # Create a PyHelios context
    context = Context()
    print("PyHelios External Geometry Import Demo")
    print("=" * 50)
    
    # ==================== METHOD 1: PLY FILE LOADING ====================
    print("\n1. PLY File Loading")

    # Simple PLY loading
    ply_uuids = context.loadPLY(str(MODELS_DIR / "suzanne.ply"), silent=True)
    print(f"   Simple PLY load: {len(ply_uuids)} primitives loaded")

    # PLY loading with transformations
    origin = vec3(2.0, 0.0, 1.0)
    color = RGBcolor(0.8, 0.2, 0.2)  # Red tint
    rotation = SphericalCoord(1.0, 0.0, np.pi/4)  # 45 degree rotation

    transformed_uuids = context.loadPLY(
        filename=str(MODELS_DIR / "suzanne.ply"),
        origin=origin,
        height=2.0,
        rotation=rotation,
        color=color,
        upaxis="YUP",
        silent=True
    )
    print(f"   Transformed PLY load: {len(transformed_uuids)} primitives loaded")
    
    # ==================== METHOD 2: OBJ FILE LOADING ====================
    print("\n2. OBJ File Loading")

    # Simple OBJ loading
    obj_uuids = context.loadOBJ(str(MODELS_DIR / "suzanne.obj"), silent=True)
    print(f"   Simple OBJ load: {len(obj_uuids)} primitives loaded")

    # OBJ loading with full transformations
    origin = vec3(-2.0, 0.0, 1.0)
    scale = vec3(0.5, 0.5, 0.5)  # Half scale
    rotation = SphericalCoord(1.0, 0.0, -np.pi/6)  # -30 degree rotation
    color = RGBcolor(0.2, 0.8, 0.2)  # Green tint

    transformed_obj_uuids = context.loadOBJ(
        filename=str(MODELS_DIR / "suzanne.obj"),
        origin=origin,
        scale=scale,
        rotation=rotation,
        color=color,
        upaxis="ZUP",
        silent=True
    )
    print(f"   Transformed OBJ load: {len(transformed_obj_uuids)} primitives loaded")

# ==================== METHOD 3: XML FILE LOADING ====================
    print("\n3. Helios XML File Loading")

    xml_uuids = context.loadXML(str(MODELS_DIR / "leaf_cube.xml"), quiet=True)
    print(f"   XML load: {len(xml_uuids)} primitives loaded")

    # ==================== METHOD 4: NUMPY ARRAY IMPORT ====================
    print("\n4. NumPy Array Import (trimesh/Open3D compatible)")
    
    # Create a simple triangular mesh (tetrahedron)
    vertices = np.array([
        [0.0, 0.0, 0.0],    # vertex 0
        [1.0, 0.0, 0.0],    # vertex 1
        [0.5, 1.0, 0.0],    # vertex 2
        [0.5, 0.5, 1.0]     # vertex 3
    ], dtype=np.float32)
    
    faces = np.array([
        [0, 1, 2],  # bottom face
        [0, 1, 3],  # front face
        [1, 2, 3],  # right face
        [0, 2, 3]   # left face
    ], dtype=np.int32)
    
    # Per-vertex colors (RGBA)
    colors = np.array([
        [1.0, 0.0, 0.0],  # red
        [0.0, 1.0, 0.0],  # green
        [0.0, 0.0, 1.0],  # blue
        [1.0, 1.0, 0.0]   # yellow
    ], dtype=np.float32)
    
    # Import triangles with per-vertex colors
    array_uuids = context.addTrianglesFromArrays(vertices, faces, colors)
    print(f"   NumPy array import: {len(array_uuids)} triangles added")
    print(f"   Triangle UUIDs: {array_uuids}")
    
    # ==================== TEXTURED TRIANGLE IMPORT ====================
    print("\n5. Textured Triangle Import")
    
    # Create a simple quad (2 triangles) with UV coordinates
    quad_vertices = np.array([
        [3.0, 0.0, 0.0],  # bottom-left
        [4.0, 0.0, 0.0],  # bottom-right
        [4.0, 1.0, 0.0],  # top-right
        [3.0, 1.0, 0.0]   # top-left
    ], dtype=np.float32)
    
    quad_faces = np.array([
        [0, 1, 2],  # first triangle
        [0, 2, 3]   # second triangle
    ], dtype=np.int32)
    
    # UV coordinates for texture mapping
    uv_coords = np.array([
        [0.0, 0.0],  # bottom-left UV
        [1.0, 0.0],  # bottom-right UV
        [1.0, 1.0],  # top-right UV
        [0.0, 1.0]   # top-left UV
    ], dtype=np.float32)

    # Single texture example (backward compatible)
    textured_uuids = context.addTrianglesFromArraysTextured(
        vertices=quad_vertices,
        faces=quad_faces,
        uv_coords=uv_coords,
        texture_files=str(MODELS_DIR / "Helios_logo.jpeg")  # Note: now uses texture_files parameter
    )
    print(f"   Single textured triangles: {len(textured_uuids)} triangles added")
    print(f"   Textured UUIDs: {textured_uuids}")
    
    # Multi-texture example (new functionality)
    print("\n   Multi-texture example:")
    
    # Create a simple 2x1 rectangle with 4 triangles using different textures
    multi_vertices = np.array([
        [0.0, 0.0, 2.0],   # bottom-left
        [1.0, 0.0, 2.0],   # bottom-middle
        [2.0, 0.0, 2.0],   # bottom-right
        [0.0, 1.0, 2.0],   # top-left
        [1.0, 1.0, 2.0],   # top-middle
        [2.0, 1.0, 2.0]    # top-right
    ], dtype=np.float32)
    
    multi_faces = np.array([
        [0, 1, 3],  # left bottom triangle
        [1, 4, 3],  # left top triangle
        [1, 2, 4],  # right bottom triangle
        [2, 5, 4]   # right top triangle
    ], dtype=np.uint32)
    
    multi_uv_coords = np.array([
        [0.0, 0.0], [0.5, 0.0], [1.0, 0.0],  # bottom row UVs
        [0.0, 1.0], [0.5, 1.0], [1.0, 1.0]   # top row UVs
    ], dtype=np.float32)
    
    # Material IDs: left triangles use texture 0, right triangles use texture 1
    material_ids = np.array([0, 0, 1, 1], dtype=np.uint32)
    
    try:
        # Attempt multi-texture with dummy texture files (will fail validation but shows API)
        multi_textured_uuids = context.addTrianglesFromArraysTextured(
            vertices=multi_vertices,
            faces=multi_faces,
            uv_coords=multi_uv_coords,
            texture_files=[str(MODELS_DIR / "Helios_logo.jpeg"), str(MODELS_DIR / "Helios_logo.jpeg")],  # Using same texture twice for demo
            material_ids=material_ids
        )
        print(f"   Multi-textured triangles: {len(multi_textured_uuids)} triangles added")
        print(f"   Multi-texture UUIDs: {multi_textured_uuids}")
    except Exception as e:
        print(f"   Multi-texture example skipped: {e}")
        print("   (This is expected if texture files don't exist or native library isn't built)")

# ==================== PRIMITIVE INFO RETRIEVAL ====================
    print("\n6. Primitive Information Retrieval")
    
    # Get information about the triangles we just created
    if array_uuids:
        first_triangle_uuid = array_uuids[0]
        
        # Get detailed primitive information
        prim_info = context.getPrimitiveInfo(first_triangle_uuid)
        print(f"   Triangle {first_triangle_uuid} info:")
        print(f"     Type: {prim_info.primitive_type}")
        print(f"     Area: {prim_info.area:.4f}")
        print(f"     Normal: ({prim_info.normal.x:.3f}, {prim_info.normal.y:.3f}, {prim_info.normal.z:.3f})")
        print(f"     Centroid: ({prim_info.centroid.x:.3f}, {prim_info.centroid.y:.3f}, {prim_info.centroid.z:.3f})")
        print(f"     Color: RGB({prim_info.color.r:.3f}, {prim_info.color.g:.3f}, {prim_info.color.b:.3f})")
        print(f"     Vertices:")
        for i, vertex in enumerate(prim_info.vertices):
            print(f"       v{i}: ({vertex.x:.3f}, {vertex.y:.3f}, {vertex.z:.3f})")
    
    # Get info for all primitives
    all_primitive_info = context.getAllPrimitiveInfo()
    print(f"\n   Total primitives in context: {len(all_primitive_info)}")
    
    # Summary by type
    type_counts = {}
    for info in all_primitive_info:
        ptype = info.primitive_type.name
        type_counts[ptype] = type_counts.get(ptype, 0) + 1
    
    print("   Primitive counts by type:")
    for ptype, count in type_counts.items():
        print(f"     {ptype}: {count}")
    
    # ==================== PRIMITIVE DATA EXAMPLE ====================
    print("\n7. Primitive Data (User-defined key-value pairs)")
    print("   Note: Primitive data methods require additional C++ wrapper implementation")
    print("   This demonstrates the intended API for user-defined metadata:")
    print("   - context.setPrimitiveData(uuid, 'temperature', 25.5)")
    print("   - context.setPrimitiveData(uuid, 'material_id', 42)")
    print("   - context.setPrimitiveData(uuid, 'source_file', 'imported_model.obj')")
    print("   - temp = context.getPrimitiveData(uuid, 'temperature')  # Auto-detects type")
    print("   - temp = context.getPrimitiveData(uuid, 'temperature', float)  # Explicit type (optional)")
    
    # ==================== INTEGRATION WITH POPULAR LIBRARIES ====================
    print("\n8. Integration with Popular Python 3D Libraries")
    print("   The array format used by PyHelios is compatible with:")
    print("   - trimesh: mesh = trimesh.Trimesh(vertices=vertices, faces=faces)")
    print("   - Open3D: mesh = o3d.geometry.TriangleMesh()")
    print("             mesh.vertices = o3d.utility.Vector3dVector(vertices)")
    print("             mesh.triangles = o3d.utility.Vector3iVector(faces)")
    print("   - numpy-stl: mesh = numpy_stl.mesh.Mesh(vertices.reshape(-1, 9))")
    
    print("\n" + "=" * 50)
    print("External geometry import demo completed!")
    print(f"Context contains {context.getPrimitiveCount()} total primitives")


if __name__ == "__main__":
    main()