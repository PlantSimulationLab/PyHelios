/**
 * @file pyhelios_wrapper_context.h
 * @brief Context and geometry functions for PyHelios C wrapper
 * 
 * This header provides Context creation, geometry management, primitive operations,
 * compound geometry functions, file loading, and primitive data functions.
 */

#ifndef PYHELIOS_WRAPPER_CONTEXT_H
#define PYHELIOS_WRAPPER_CONTEXT_H

#include "pyhelios_wrapper_common.h"

// Forward declarations for Context interface
namespace helios {
    class Context;
}

#ifdef __cplusplus
extern "C" {
#endif

//=============================================================================
// Context Functions
//=============================================================================

/**
 * @brief Create a new Helios Context
 * @return Pointer to the created Context
 */
PYHELIOS_API helios::Context* createContext();

/**
 * @brief Destroy a Helios Context
 * @param context Pointer to the Context to destroy
 */
PYHELIOS_API void destroyContext(helios::Context* context);

/**
 * @brief Mark geometry as clean
 * @param context Pointer to the Context
 */
PYHELIOS_API void markGeometryClean(helios::Context* context);

/**
 * @brief Mark geometry as dirty
 * @param context Pointer to the Context
 */
PYHELIOS_API void markGeometryDirty(helios::Context* context);

/**
 * @brief Check if geometry is dirty
 * @param context Pointer to the Context
 * @return true if geometry is dirty, false otherwise
 */
PYHELIOS_API bool isGeometryDirty(helios::Context* context);

/**
 * @brief Add a default patch to the context
 * @param context Pointer to the Context
 * @return UUID of the created patch
 */
PYHELIOS_API unsigned int addPatch(helios::Context* context);

/**
 * @brief Add a patch with center and size
 * @param context Pointer to the Context
 * @param center Array of 3 floats [x, y, z] for patch center
 * @param size Array of 2 floats [width, height] for patch size
 * @return UUID of the created patch
 */
PYHELIOS_API unsigned int addPatchWithCenterAndSize(helios::Context* context, float* center, float* size);

/**
 * @brief Add a patch with center, size, and rotation
 * @param context Pointer to the Context
 * @param center Array of 3 floats [x, y, z] for patch center
 * @param size Array of 2 floats [width, height] for patch size  
 * @param rotation Array of 3 floats [radius, elevation, azimuth] for patch rotation
 * @return UUID of the created patch
 */
PYHELIOS_API unsigned int addPatchWithCenterSizeAndRotation(helios::Context* context, float* center, float* size, float* rotation);

/**
 * @brief Add a patch with center, size, rotation, and RGB color
 * @param context Pointer to the Context
 * @param center Array of 3 floats [x, y, z] for patch center
 * @param size Array of 2 floats [width, height] for patch size
 * @param rotation Array of 3 floats [radius, elevation, azimuth] for patch rotation
 * @param color Array of 3 floats [r, g, b] for patch color
 * @return UUID of the created patch
 */
PYHELIOS_API unsigned int addPatchWithCenterSizeRotationAndColor(helios::Context* context, float* center, float* size, float* rotation, float* color);

/**
 * @brief Add a patch with center, size, rotation, and RGBA color
 * @param context Pointer to the Context
 * @param center Array of 3 floats [x, y, z] for patch center
 * @param size Array of 2 floats [width, height] for patch size
 * @param rotation Array of 3 floats [radius, elevation, azimuth] for patch rotation
 * @param color Array of 4 floats [r, g, b, a] for patch color
 * @return UUID of the created patch
 */
PYHELIOS_API unsigned int addPatchWithCenterSizeRotationAndColorRGBA(helios::Context* context, float* center, float* size, float* rotation, float* color);

/**
 * @brief Add a triangle primitive to the context
 * @param context Pointer to the Context
 * @param vertex0 Array of 3 floats [x, y, z] for first vertex
 * @param vertex1 Array of 3 floats [x, y, z] for second vertex
 * @param vertex2 Array of 3 floats [x, y, z] for third vertex
 * @return UUID of the created triangle
 */
PYHELIOS_API unsigned int addTriangle(helios::Context* context, float* vertex0, float* vertex1, float* vertex2);

/**
 * @brief Add a triangle primitive with RGB color
 * @param context Pointer to the Context
 * @param vertex0 Array of 3 floats [x, y, z] for first vertex
 * @param vertex1 Array of 3 floats [x, y, z] for second vertex
 * @param vertex2 Array of 3 floats [x, y, z] for third vertex
 * @param color Array of 3 floats [r, g, b] for triangle color
 * @return UUID of the created triangle
 */
PYHELIOS_API unsigned int addTriangleWithColor(helios::Context* context, float* vertex0, float* vertex1, float* vertex2, float* color);

/**
 * @brief Add a triangle primitive with RGBA color
 * @param context Pointer to the Context
 * @param vertex0 Array of 3 floats [x, y, z] for first vertex
 * @param vertex1 Array of 3 floats [x, y, z] for second vertex
 * @param vertex2 Array of 3 floats [x, y, z] for third vertex
 * @param color Array of 4 floats [r, g, b, a] for triangle color
 * @return UUID of the created triangle
 */
PYHELIOS_API unsigned int addTriangleWithColorRGBA(helios::Context* context, float* vertex0, float* vertex1, float* vertex2, float* color);

/**
 * @brief Add a triangle primitive with texture
 * @param context Pointer to the Context
 * @param vertex0 Array of 3 floats [x, y, z] for first vertex
 * @param vertex1 Array of 3 floats [x, y, z] for second vertex
 * @param vertex2 Array of 3 floats [x, y, z] for third vertex
 * @param texture_file Path to texture image file
 * @param uv0 Array of 2 floats [u, v] for first vertex texture coordinates
 * @param uv1 Array of 2 floats [u, v] for second vertex texture coordinates
 * @param uv2 Array of 2 floats [u, v] for third vertex texture coordinates
 * @return UUID of the created triangle
 */
PYHELIOS_API unsigned int addTriangleWithTexture(helios::Context* context, float* vertex0, float* vertex1, float* vertex2, const char* texture_file, float* uv0, float* uv1, float* uv2);

//=============================================================================
// Compound Geometry Functions
//=============================================================================

/**
 * @brief Add a tile (subdivided patch) to the context
 * @param context Pointer to the Context
 * @param center Array of 3 floats [x, y, z] for tile center
 * @param size Array of 2 floats [width, height] for tile size
 * @param rotation Array of 3 floats [radius, elevation, azimuth] for tile rotation
 * @param subdiv Array of 2 ints [x_subdivisions, y_subdivisions] for tile subdivisions
 * @param count Pointer to store the number of UUIDs returned
 * @return Pointer to array of UUIDs for the created patches
 */
PYHELIOS_API unsigned int* addTile(helios::Context* context, float* center, float* size, float* rotation, int* subdiv, unsigned int* count);

/**
 * @brief Add a tile (subdivided patch) with color to the context
 * @param context Pointer to the Context
 * @param center Array of 3 floats [x, y, z] for tile center
 * @param size Array of 2 floats [width, height] for tile size
 * @param rotation Array of 3 floats [radius, elevation, azimuth] for tile rotation
 * @param subdiv Array of 2 ints [x_subdivisions, y_subdivisions] for tile subdivisions
 * @param color Array of 3 floats [r, g, b] for tile color
 * @param count Pointer to store the number of UUIDs returned
 * @return Pointer to array of UUIDs for the created patches
 */
PYHELIOS_API unsigned int* addTileWithColor(helios::Context* context, float* center, float* size, float* rotation, int* subdiv, float* color, unsigned int* count);

/**
 * @brief Add a sphere to the context
 * @param context Pointer to the Context
 * @param ndivs Number of divisions for sphere tessellation
 * @param center Array of 3 floats [x, y, z] for sphere center
 * @param radius Sphere radius
 * @param count Pointer to store the number of UUIDs returned
 * @return Pointer to array of UUIDs for the created triangles
 */
PYHELIOS_API unsigned int* addSphere(helios::Context* context, unsigned int ndivs, float* center, float radius, unsigned int* count);

/**
 * @brief Add a sphere with color to the context
 * @param context Pointer to the Context
 * @param ndivs Number of divisions for sphere tessellation
 * @param center Array of 3 floats [x, y, z] for sphere center
 * @param radius Sphere radius
 * @param color Array of 3 floats [r, g, b] for sphere color
 * @param count Pointer to store the number of UUIDs returned
 * @return Pointer to array of UUIDs for the created triangles
 */
PYHELIOS_API unsigned int* addSphereWithColor(helios::Context* context, unsigned int ndivs, float* center, float radius, float* color, unsigned int* count);

/**
 * @brief Add a tube to the context
 * @param context Pointer to the Context
 * @param ndivs Number of radial divisions for tube
 * @param nodes Array of floats representing node positions [x1,y1,z1, x2,y2,z2, ...]
 * @param node_count Number of nodes
 * @param radii Array of floats representing radius at each node
 * @param count Pointer to store the number of UUIDs returned
 * @return Pointer to array of UUIDs for the created triangles
 */
PYHELIOS_API unsigned int* addTube(helios::Context* context, unsigned int ndivs, float* nodes, unsigned int node_count, float* radii, unsigned int* count);

/**
 * @brief Add a tube with colors to the context
 * @param context Pointer to the Context
 * @param ndivs Number of radial divisions for tube
 * @param nodes Array of floats representing node positions [x1,y1,z1, x2,y2,z2, ...]
 * @param node_count Number of nodes
 * @param radii Array of floats representing radius at each node
 * @param colors Array of floats representing RGB color at each node [r1,g1,b1, r2,g2,b2, ...]
 * @param count Pointer to store the number of UUIDs returned
 * @return Pointer to array of UUIDs for the created triangles
 */
PYHELIOS_API unsigned int* addTubeWithColor(helios::Context* context, unsigned int ndivs, float* nodes, unsigned int node_count, float* radii, float* colors, unsigned int* count);

/**
 * @brief Add a box to the context
 * @param context Pointer to the Context
 * @param center Array of 3 floats [x, y, z] for box center
 * @param size Array of 3 floats [width, height, depth] for box size
 * @param subdiv Array of 3 ints [x_subdivisions, y_subdivisions, z_subdivisions] for box subdivisions
 * @param count Pointer to store the number of UUIDs returned
 * @return Pointer to array of UUIDs for the created patches
 */
PYHELIOS_API unsigned int* addBox(helios::Context* context, float* center, float* size, int* subdiv, unsigned int* count);

/**
 * @brief Add a box with color to the context
 * @param context Pointer to the Context
 * @param center Array of 3 floats [x, y, z] for box center
 * @param size Array of 3 floats [width, height, depth] for box size
 * @param subdiv Array of 3 ints [x_subdivisions, y_subdivisions, z_subdivisions] for box subdivisions
 * @param color Array of 3 floats [r, g, b] for box color
 * @param count Pointer to store the number of UUIDs returned
 * @return Pointer to array of UUIDs for the created patches
 */
PYHELIOS_API unsigned int* addBoxWithColor(helios::Context* context, float* center, float* size, int* subdiv, float* color, unsigned int* count);

/**
 * @brief Get the type of a primitive
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @return Primitive type as integer
 */
PYHELIOS_API unsigned int getPrimitiveType(helios::Context* context, unsigned int uuid);

/**
 * @brief Get the area of a primitive
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @return Area of the primitive
 */
PYHELIOS_API float getPrimitiveArea(helios::Context* context, unsigned int uuid);

/**
 * @brief Get the normal vector of a primitive
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @return Pointer to array of 3 floats [x, y, z] for normal vector
 */
PYHELIOS_API float* getPrimitiveNormal(helios::Context* context, unsigned int uuid);

/**
 * @brief Get the vertices of a primitive
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param size Pointer to store the number of vertices
 * @return Pointer to array of vertex coordinates
 */
PYHELIOS_API float* getPrimitiveVertices(helios::Context* context, unsigned int uuid, unsigned int* size);

/**
 * @brief Get the color of a primitive (RGB)
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @return Pointer to array of 3 floats [r, g, b]
 */
PYHELIOS_API float* getPrimitiveColor(helios::Context* context, unsigned int uuid);

/**
 * @brief Get the RGB color of a primitive
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @return Pointer to array of 3 floats [r, g, b]
 */
PYHELIOS_API float* getPrimitiveColorRGB(helios::Context* context, unsigned int uuid);

/**
 * @brief Get the RGBA color of a primitive
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @return Pointer to array of 4 floats [r, g, b, a]
 */
PYHELIOS_API float* getPrimitiveColorRGBA(helios::Context* context, unsigned int uuid);

/**
 * @brief Get the total number of primitives in the context
 * @param context Pointer to the Context
 * @return Number of primitives
 */
PYHELIOS_API unsigned int getPrimitiveCount(helios::Context* context);

/**
 * @brief Get all primitive UUIDs in the context
 * @param context Pointer to the Context
 * @param size Pointer to store the number of UUIDs
 * @return Pointer to array of UUIDs
 */
PYHELIOS_API unsigned int* getAllUUIDs(helios::Context* context, unsigned int* size);

/**
 * @brief Get the total number of objects in the context
 * @param context Pointer to the Context
 * @return Number of objects
 */
PYHELIOS_API unsigned int getObjectCount(helios::Context* context);

/**
 * @brief Get all object IDs in the context
 * @param context Pointer to the Context
 * @param size Pointer to store the number of object IDs
 * @return Pointer to array of object IDs
 */
PYHELIOS_API unsigned int* getAllObjectIDs(helios::Context* context, unsigned int* size);

/**
 * @brief Get primitive UUIDs for a specific object
 * @param context Pointer to the Context
 * @param objectID Object ID
 * @param size Pointer to store the number of UUIDs
 * @return Pointer to array of UUIDs
 */
PYHELIOS_API unsigned int* getObjectPrimitiveUUIDs(helios::Context* context, unsigned int objectID, unsigned int* size);

/**
 * @brief Load PLY file with origin, height and upaxis parameters
 * @param context Pointer to the Context
 * @param filename Path to PLY file
 * @param origin_x Origin X coordinate
 * @param origin_y Origin Y coordinate  
 * @param origin_z Origin Z coordinate
 * @param height Scaling height
 * @param upaxis Up axis specification ("YUP" or "ZUP")
 * @param size Pointer to store the number of UUIDs
 * @return Pointer to array of UUIDs for loaded geometry
 */
PYHELIOS_API unsigned int* loadPLY(helios::Context* context, const char* filename, float* origin, float height, const char* upaxis, unsigned int* size);

/**
 * @brief Load geometry from PLY file (basic version)
 * @param context Context instance
 * @param filename Path to PLY file
 * @param silent Suppress output messages
 * @param size Pointer to store the number of UUIDs
 * @return Pointer to array of UUIDs for loaded geometry
 */
PYHELIOS_API unsigned int* loadPLYBasic(helios::Context* context, const char* filename, bool silent, unsigned int* size);

/**
 * @brief Load geometry from PLY file with origin, height, and rotation
 * @param context Context instance
 * @param filename Path to PLY file
 * @param origin Origin coordinates (3 floats)
 * @param height Height scaling factor
 * @param rotation Rotation parameters (3 floats)
 * @param upaxis Up axis direction
 * @param silent Suppress output messages
 * @param size Pointer to store the number of UUIDs
 * @return Pointer to array of UUIDs for loaded geometry
 */
PYHELIOS_API unsigned int* loadPLYWithOriginHeightRotation(helios::Context* context, const char* filename, float* origin, float height, float* rotation, const char* upaxis, bool silent, unsigned int* size);

/**
 * @brief Load geometry from PLY file with origin, height, and color
 * @param context Context instance
 * @param filename Path to PLY file
 * @param origin Origin coordinates (3 floats)
 * @param height Height scaling factor
 * @param color Default color (3 floats)
 * @param upaxis Up axis direction
 * @param silent Suppress output messages
 * @param size Pointer to store the number of UUIDs
 * @return Pointer to array of UUIDs for loaded geometry
 */
PYHELIOS_API unsigned int* loadPLYWithOriginHeightColor(helios::Context* context, const char* filename, float* origin, float height, float* color, const char* upaxis, bool silent, unsigned int* size);

/**
 * @brief Load geometry from PLY file with origin, height, rotation, and color
 * @param context Context instance
 * @param filename Path to PLY file
 * @param origin Origin coordinates (3 floats)
 * @param height Height scaling factor
 * @param rotation Rotation parameters (3 floats)
 * @param color Default color (3 floats)
 * @param upaxis Up axis direction
 * @param silent Suppress output messages
 * @param size Pointer to store the number of UUIDs
 * @return Pointer to array of UUIDs for loaded geometry
 */
PYHELIOS_API unsigned int* loadPLYWithOriginHeightRotationColor(helios::Context* context, const char* filename, float* origin, float height, float* rotation, float* color, const char* upaxis, bool silent, unsigned int* size);

/**
 * @brief Load geometry from OBJ file (basic version)
 * @param context Context instance
 * @param filename Path to OBJ file
 * @param silent Suppress output messages
 * @param size Pointer to store the number of UUIDs
 * @return Pointer to array of UUIDs for loaded geometry
 */
PYHELIOS_API unsigned int* loadOBJ(helios::Context* context, const char* filename, bool silent, unsigned int* size);

/**
 * @brief Load geometry from OBJ file with origin, height, rotation, and color
 * @param context Context instance
 * @param filename Path to OBJ file
 * @param origin Origin coordinates (3 floats)
 * @param height Height scaling factor
 * @param rotation Rotation parameters (3 floats)
 * @param color Default color (3 floats)
 * @param silent Suppress output messages
 * @param size Pointer to store the number of UUIDs
 * @return Pointer to array of UUIDs for loaded geometry
 */
PYHELIOS_API unsigned int* loadOBJWithOriginHeightRotationColor(helios::Context* context, const char* filename, float* origin, float height, float* rotation, float* color, bool silent, unsigned int* size);

/**
 * @brief Load geometry from OBJ file with origin, height, rotation, color, and upaxis
 * @param context Context instance
 * @param filename Path to OBJ file
 * @param origin Origin coordinates (3 floats)
 * @param height Height scaling factor
 * @param rotation Rotation parameters (3 floats)
 * @param color Default color (3 floats)
 * @param upaxis Up axis direction
 * @param silent Suppress output messages
 * @param size Pointer to store the number of UUIDs
 * @return Pointer to array of UUIDs for loaded geometry
 */
PYHELIOS_API unsigned int* loadOBJWithOriginHeightRotationColorUpaxis(helios::Context* context, const char* filename, float* origin, float height, float* rotation, float* color, const char* upaxis, bool silent, unsigned int* size);

/**
 * @brief Load geometry from OBJ file with origin, scale, rotation, color, and upaxis
 * @param context Context instance
 * @param filename Path to OBJ file
 * @param origin Origin coordinates (3 floats)
 * @param scale Scale factors (3 floats)
 * @param rotation Rotation parameters (3 floats)
 * @param color Default color (3 floats)
 * @param upaxis Up axis direction
 * @param silent Suppress output messages
 * @param size Pointer to store the number of UUIDs
 * @return Pointer to array of UUIDs for loaded geometry
 */
PYHELIOS_API unsigned int* loadOBJWithOriginScaleRotationColorUpaxis(helios::Context* context, const char* filename, float* origin, float* scale, float* rotation, float* color, const char* upaxis, bool silent, unsigned int* size);

/**
 * @brief Load geometry from XML file
 * @param context Context instance
 * @param filename Path to XML file
 * @param quiet Suppress output messages
 * @param size Pointer to store the number of UUIDs
 * @return Pointer to array of UUIDs for loaded geometry
 */
PYHELIOS_API unsigned int* loadXML(helios::Context* context, const char* filename, bool quiet, unsigned int* size);

/**
 * @brief Write geometry to PLY file (all primitives)
 * @param context Pointer to the Context
 * @param filename Output PLY filename
 */
PYHELIOS_API void writePLY(helios::Context* context, const char* filename);

/**
 * @brief Write geometry to PLY file (subset of primitives)
 * @param context Pointer to the Context
 * @param filename Output PLY filename
 * @param uuids Array of primitive UUIDs to export
 * @param count Number of UUIDs in the array
 */
PYHELIOS_API void writePLYWithUUIDs(helios::Context* context, const char* filename, unsigned int* uuids, unsigned int count);

/**
 * @brief Write geometry to OBJ file (all primitives)
 * @param context Pointer to the Context
 * @param filename Output OBJ filename
 * @param write_normals Whether to include vertex normals
 * @param silent Whether to suppress output messages
 */
PYHELIOS_API void writeOBJ(helios::Context* context, const char* filename, bool write_normals, bool silent);

/**
 * @brief Write geometry to OBJ file (subset of primitives)
 * @param context Pointer to the Context
 * @param filename Output OBJ filename
 * @param uuids Array of primitive UUIDs to export
 * @param count Number of UUIDs in the array
 * @param write_normals Whether to include vertex normals
 * @param silent Whether to suppress output messages
 */
PYHELIOS_API void writeOBJWithUUIDs(helios::Context* context, const char* filename, unsigned int* uuids, unsigned int count, bool write_normals, bool silent);

/**
 * @brief Write geometry to OBJ file with primitive data fields
 * @param context Pointer to the Context
 * @param filename Output OBJ filename
 * @param uuids Array of primitive UUIDs to export
 * @param count Number of UUIDs in the array
 * @param data_fields Array of primitive data field names to export
 * @param field_count Number of data fields
 * @param write_normals Whether to include vertex normals
 * @param silent Whether to suppress output messages
 */
PYHELIOS_API void writeOBJWithPrimitiveData(helios::Context* context, const char* filename, unsigned int* uuids, unsigned int count, const char** data_fields, unsigned int field_count, bool write_normals, bool silent);

//=============================================================================
// Primitive Data Functions
//=============================================================================

/**
 * @brief Set primitive data as float
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @param value Float value to set
 */
PYHELIOS_API void setPrimitiveDataFloat(helios::Context* context, unsigned int uuid, const char* label, float value);

/**
 * @brief Get primitive data as float
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @return Float value
 */
PYHELIOS_API float getPrimitiveDataFloat(helios::Context* context, unsigned int uuid, const char* label);

/**
 * @brief Set primitive data as vec3
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @param x X component
 * @param y Y component
 * @param z Z component
 */
PYHELIOS_API void setPrimitiveDataVec3(helios::Context* context, unsigned int uuid, const char* label, float x, float y, float z);

/**
 * @brief Get primitive data as vec3
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @param x Pointer to store X component
 * @param y Pointer to store Y component
 * @param z Pointer to store Z component
 */
PYHELIOS_API void getPrimitiveDataVec3(helios::Context* context, unsigned int uuid, const char* label, float* x, float* y, float* z);

/**
 * @brief Set primitive data as int
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @param value Integer value to set
 */
PYHELIOS_API void setPrimitiveDataInt(helios::Context* context, unsigned int uuid, const char* label, int value);

/**
 * @brief Get primitive data as int
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @return Integer value
 */
PYHELIOS_API int getPrimitiveDataInt(helios::Context* context, unsigned int uuid, const char* label);

/**
 * @brief Check if primitive data exists
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @return true if data exists, false otherwise
 */
PYHELIOS_API bool doesPrimitiveDataExist(helios::Context* context, unsigned int uuid, const char* label);

/**
 * @brief Set primitive data as string
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @param value String value to set
 */
PYHELIOS_API void setPrimitiveDataString(helios::Context* context, unsigned int uuid, const char* label, const char* value);

/**
 * @brief Get primitive data as string
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @param buffer Buffer to store the string
 * @param buffer_size Size of the buffer
 * @return Length of the string
 */
PYHELIOS_API int getPrimitiveDataString(helios::Context* context, unsigned int uuid, const char* label, char* buffer, int buffer_size);

/**
 * @brief Set primitive data as unsigned int
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @param value Unsigned int value to set
 */
PYHELIOS_API void setPrimitiveDataUInt(helios::Context* context, unsigned int uuid, const char* label, unsigned int value);

/**
 * @brief Get primitive data as unsigned int
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @param value Pointer to store the unsigned int value
 */
PYHELIOS_API unsigned int getPrimitiveDataUInt(helios::Context* context, unsigned int uuid, const char* label);

/**
 * @brief Set primitive data as double
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @param value Double value to set
 */
PYHELIOS_API void setPrimitiveDataDouble(helios::Context* context, unsigned int uuid, const char* label, double value);

/**
 * @brief Get primitive data as double
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @return Double value
 */
PYHELIOS_API double getPrimitiveDataDouble(helios::Context* context, unsigned int uuid, const char* label);

/**
 * @brief Get primitive data type
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @return Data type as integer
 */
PYHELIOS_API int getPrimitiveDataType(helios::Context* context, unsigned int uuid, const char* label);

/**
 * @brief Get primitive data size
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @return Data size as integer
 */
PYHELIOS_API int getPrimitiveDataSize(helios::Context* context, unsigned int uuid, const char* label);

/**
 * @brief Set primitive data as vec2
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @param x X component
 * @param y Y component
 */
PYHELIOS_API void setPrimitiveDataVec2(helios::Context* context, unsigned int uuid, const char* label, float x, float y);

/**
 * @brief Get primitive data as vec2
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @param x Pointer to store X component
 * @param y Pointer to store Y component
 */
PYHELIOS_API void getPrimitiveDataVec2(helios::Context* context, unsigned int uuid, const char* label, float* x, float* y);

/**
 * @brief Set primitive data as vec4
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @param x X component
 * @param y Y component
 * @param z Z component
 * @param w W component
 */
PYHELIOS_API void setPrimitiveDataVec4(helios::Context* context, unsigned int uuid, const char* label, float x, float y, float z, float w);

/**
 * @brief Get primitive data as vec4
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @param x Pointer to store X component
 * @param y Pointer to store Y component
 * @param z Pointer to store Z component
 * @param w Pointer to store W component
 */
PYHELIOS_API void getPrimitiveDataVec4(helios::Context* context, unsigned int uuid, const char* label, float* x, float* y, float* z, float* w);

/**
 * @brief Set primitive data as int2
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @param x X component
 * @param y Y component
 */
PYHELIOS_API void setPrimitiveDataInt2(helios::Context* context, unsigned int uuid, const char* label, int x, int y);

/**
 * @brief Get primitive data as int2
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @param x Pointer to store X component
 * @param y Pointer to store Y component
 */
PYHELIOS_API void getPrimitiveDataInt2(helios::Context* context, unsigned int uuid, const char* label, int* x, int* y);

/**
 * @brief Set primitive data as int3
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @param x X component
 * @param y Y component
 * @param z Z component
 */
PYHELIOS_API void setPrimitiveDataInt3(helios::Context* context, unsigned int uuid, const char* label, int x, int y, int z);

/**
 * @brief Get primitive data as int3
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @param x Pointer to store X component
 * @param y Pointer to store Y component
 * @param z Pointer to store Z component
 */
PYHELIOS_API void getPrimitiveDataInt3(helios::Context* context, unsigned int uuid, const char* label, int* x, int* y, int* z);

/**
 * @brief Set primitive data as int4
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @param x X component
 * @param y Y component
 * @param z Z component
 * @param w W component
 */
PYHELIOS_API void setPrimitiveDataInt4(helios::Context* context, unsigned int uuid, const char* label, int x, int y, int z, int w);

/**
 * @brief Get primitive data as int4
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @param x Pointer to store X component
 * @param y Pointer to store Y component
 * @param z Pointer to store Z component
 * @param w Pointer to store W component
 */
PYHELIOS_API void getPrimitiveDataInt4(helios::Context* context, unsigned int uuid, const char* label, int* x, int* y, int* z, int* w);

/**
 * @brief Generic primitive data getter that automatically detects type
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive
 * @param label Name/label of the data
 * @param result_buffer Buffer to store the result - must be large enough for the data type
 * @param max_buffer_size Maximum size of the result buffer
 * @return Data type as integer (HeliosDataType), or -1 on error
 */
PYHELIOS_API int getPrimitiveDataGeneric(helios::Context* context, unsigned int uuid, const char* label, void* result_buffer, int max_buffer_size);

/**
 * @brief Color primitives based on pseudocolor mapping of primitive data values
 * @param context Pointer to the Context
 * @param uuids Array of primitive UUIDs
 * @param num_uuids Number of UUIDs in the array
 * @param primitive_data Name of the primitive data to use for coloring
 * @param colormap Name of the colormap to use (e.g., "hot", "rainbow", "cool")
 * @param ncolors Number of colors in the colormap
 */
PYHELIOS_API void colorPrimitiveByDataPseudocolor(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* primitive_data, const char* colormap, unsigned int ncolors);

/**
 * @brief Color primitives based on pseudocolor mapping with specified data range
 * @param context Pointer to the Context
 * @param uuids Array of primitive UUIDs
 * @param num_uuids Number of UUIDs in the array
 * @param primitive_data Name of the primitive data to use for coloring
 * @param colormap Name of the colormap to use (e.g., "hot", "rainbow", "cool")
 * @param ncolors Number of colors in the colormap
 * @param data_min Minimum data value for color mapping
 * @param data_max Maximum data value for color mapping
 */
PYHELIOS_API void colorPrimitiveByDataPseudocolorWithRange(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* primitive_data, const char* colormap, unsigned int ncolors, float data_min, float data_max);

/**
 * @brief Set the simulation time using hour and minute
 * @param context Pointer to the Context
 * @param hour Hour (0-23)
 * @param minute Minute (0-59)
 */
PYHELIOS_API void setTime_HourMinute(helios::Context* context, int hour, int minute);

/**
 * @brief Set the simulation time using hour, minute, and second
 * @param context Pointer to the Context
 * @param hour Hour (0-23)
 * @param minute Minute (0-59)
 * @param second Second (0-59)
 */
PYHELIOS_API void setTime_HourMinuteSecond(helios::Context* context, int hour, int minute, int second);

/**
 * @brief Set the simulation date using day, month, and year
 * @param context Pointer to the Context
 * @param day Day (1-31)
 * @param month Month (1-12)
 * @param year Year (1900-3000)
 */
PYHELIOS_API void setDate_DayMonthYear(helios::Context* context, int day, int month, int year);

/**
 * @brief Set the simulation date using Julian day and year
 * @param context Pointer to the Context
 * @param julian_day Julian day (1-366)
 * @param year Year (1900-3000)
 */
PYHELIOS_API void setDate_JulianDay(helios::Context* context, int julian_day, int year);

/**
 * @brief Get the current simulation time
 * @param context Pointer to the Context
 * @param hour Output parameter for hour
 * @param minute Output parameter for minute
 * @param second Output parameter for second
 */
PYHELIOS_API void getTime(helios::Context* context, int* hour, int* minute, int* second);

/**
 * @brief Get the current simulation date
 * @param context Pointer to the Context
 * @param day Output parameter for day
 * @param month Output parameter for month
 * @param year Output parameter for year
 */
PYHELIOS_API void getDate(helios::Context* context, int* day, int* month, int* year);

#ifdef __cplusplus
}
#endif

#endif // PYHELIOS_WRAPPER_CONTEXT_H