/**
 * @file pyhelios_wrapper_context.h
 * @brief Context and geometry functions for PyHelios C wrapper
 * 
 * This header provides Context creation, geometry management, primitive operations,
 * compound geometry functions, file loading, and primitive data functions.
 */

#ifndef PYHELIOS_WRAPPER_CONTEXT_H
#define PYHELIOS_WRAPPER_CONTEXT_H

#include <stdint.h>  // For uint64_t

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
 * @brief Add a patch with center, size, rotation, and texture file
 * @param context Pointer to the Context
 * @param center Array of 3 floats [x, y, z] for patch center
 * @param size Array of 2 floats [width, height] for patch size
 * @param rotation Array of 3 floats [radius, elevation, azimuth] for patch rotation
 * @param texture_file Path to texture image file (JPEG or PNG)
 * @return UUID of the created patch
 */
PYHELIOS_API unsigned int addPatchWithTexture(helios::Context* context, float* center, float* size, float* rotation, const char* texture_file);

/**
 * @brief Add a patch with center, size, rotation, texture file, and UV coordinates
 * @param context Pointer to the Context
 * @param center Array of 3 floats [x, y, z] for patch center
 * @param size Array of 2 floats [width, height] for patch size
 * @param rotation Array of 3 floats [radius, elevation, azimuth] for patch rotation
 * @param texture_file Path to texture image file (JPEG or PNG)
 * @param uv_center Array of 2 floats [u, v] for UV center of texture map
 * @param uv_size Array of 2 floats [u, v] for UV size of texture map
 * @return UUID of the created patch
 */
PYHELIOS_API unsigned int addPatchWithTextureAndUV(helios::Context* context, float* center, float* size, float* rotation, const char* texture_file, float* uv_center, float* uv_size);

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
 * @brief Add a disk to the context
 * @param context Pointer to the Context
 * @param ndivs Number of radial divisions for disk tessellation
 * @param center Array of 3 floats [x, y, z] for disk center
 * @param size Array of 2 floats [semi_major, semi_minor] for disk radii
 * @param count Pointer to store the number of UUIDs returned
 * @return Pointer to array of UUIDs for the created triangles
 */
PYHELIOS_API unsigned int* addDisk(helios::Context* context, unsigned int ndivs, float* center, float* size, unsigned int* count);

/**
 * @brief Add a disk with rotation to the context
 * @param context Pointer to the Context
 * @param ndivs Number of radial divisions for disk tessellation
 * @param center Array of 3 floats [x, y, z] for disk center
 * @param size Array of 2 floats [semi_major, semi_minor] for disk radii
 * @param rotation Array of 3 floats [radius, elevation, azimuth] for disk orientation
 * @param count Pointer to store the number of UUIDs returned
 * @return Pointer to array of UUIDs for the created triangles
 */
PYHELIOS_API unsigned int* addDiskWithRotation(helios::Context* context, unsigned int ndivs, float* center, float* size, float* rotation, unsigned int* count);

/**
 * @brief Add a disk with color to the context
 * @param context Pointer to the Context
 * @param ndivs Number of radial divisions for disk tessellation
 * @param center Array of 3 floats [x, y, z] for disk center
 * @param size Array of 2 floats [semi_major, semi_minor] for disk radii
 * @param rotation Array of 3 floats [radius, elevation, azimuth] for disk orientation
 * @param color Array of 3 floats [r, g, b] for disk color
 * @param count Pointer to store the number of UUIDs returned
 * @return Pointer to array of UUIDs for the created triangles
 */
PYHELIOS_API unsigned int* addDiskWithColor(helios::Context* context, unsigned int ndivs, float* center, float* size, float* rotation, float* color, unsigned int* count);

/**
 * @brief Add a disk with RGBA color to the context
 * @param context Pointer to the Context
 * @param ndivs Number of radial divisions for disk tessellation
 * @param center Array of 3 floats [x, y, z] for disk center
 * @param size Array of 2 floats [semi_major, semi_minor] for disk radii
 * @param rotation Array of 3 floats [radius, elevation, azimuth] for disk orientation
 * @param color Array of 4 floats [r, g, b, a] for disk color with transparency
 * @param count Pointer to store the number of UUIDs returned
 * @return Pointer to array of UUIDs for the created triangles
 */
PYHELIOS_API unsigned int* addDiskWithRGBAColor(helios::Context* context, unsigned int ndivs, float* center, float* size, float* rotation, float* color, unsigned int* count);

/**
 * @brief Add a disk with polar/radial subdivisions to the context
 * @param context Pointer to the Context
 * @param ndivs Array of 2 ints [radial_divisions, azimuthal_divisions] for disk tessellation
 * @param center Array of 3 floats [x, y, z] for disk center
 * @param size Array of 2 floats [semi_major, semi_minor] for disk radii
 * @param rotation Array of 3 floats [radius, elevation, azimuth] for disk orientation
 * @param color Array of 3 floats [r, g, b] for disk color
 * @param count Pointer to store the number of UUIDs returned
 * @return Pointer to array of UUIDs for the created triangles
 */
PYHELIOS_API unsigned int* addDiskPolarSubdivisions(helios::Context* context, int* ndivs, float* center, float* size, float* rotation, float* color, unsigned int* count);

/**
 * @brief Add a disk with polar/radial subdivisions and RGBA color to the context
 * @param context Pointer to the Context
 * @param ndivs Array of 2 ints [radial_divisions, azimuthal_divisions] for disk tessellation
 * @param center Array of 3 floats [x, y, z] for disk center
 * @param size Array of 2 floats [semi_major, semi_minor] for disk radii
 * @param rotation Array of 3 floats [radius, elevation, azimuth] for disk orientation
 * @param color Array of 4 floats [r, g, b, a] for disk color with transparency
 * @param count Pointer to store the number of UUIDs returned
 * @return Pointer to array of UUIDs for the created triangles
 */
PYHELIOS_API unsigned int* addDiskPolarSubdivisionsRGBA(helios::Context* context, int* ndivs, float* center, float* size, float* rotation, float* color, unsigned int* count);

/**
 * @brief Add a cone to the context
 * @param context Pointer to the Context
 * @param ndivs Number of radial divisions for cone tessellation
 * @param node0 Array of 3 floats [x, y, z] for cone base center
 * @param node1 Array of 3 floats [x, y, z] for cone apex center
 * @param radius0 Radius at base (node0)
 * @param radius1 Radius at apex (node1)
 * @param count Pointer to store the number of UUIDs returned
 * @return Pointer to array of UUIDs for the created triangles
 */
PYHELIOS_API unsigned int* addCone(helios::Context* context, unsigned int ndivs, float* node0, float* node1, float radius0, float radius1, unsigned int* count);

/**
 * @brief Add a cone with color to the context
 * @param context Pointer to the Context
 * @param ndivs Number of radial divisions for cone tessellation
 * @param node0 Array of 3 floats [x, y, z] for cone base center
 * @param node1 Array of 3 floats [x, y, z] for cone apex center
 * @param radius0 Radius at base (node0)
 * @param radius1 Radius at apex (node1)
 * @param color Array of 3 floats [r, g, b] for cone color
 * @param count Pointer to store the number of UUIDs returned
 * @return Pointer to array of UUIDs for the created triangles
 */
PYHELIOS_API unsigned int* addConeWithColor(helios::Context* context, unsigned int ndivs, float* node0, float* node1, float radius0, float radius1, float* color, unsigned int* count);

/**
 * @brief Copy a single primitive
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive to copy
 * @return UUID of the copied primitive
 */
PYHELIOS_API unsigned int copyPrimitive(helios::Context* context, unsigned int uuid);

/**
 * @brief Copy multiple primitives
 * @param context Pointer to the Context
 * @param uuids Pointer to array of UUIDs to copy
 * @param count Number of UUIDs in the array
 * @param result_count Output parameter for number of copied primitives
 * @return Pointer to array of UUIDs for the copied primitives
 */
PYHELIOS_API unsigned int* copyPrimitives(helios::Context* context, unsigned int* uuids, unsigned int count, unsigned int* result_count);

/**
 * @brief Copy all primitive data from one primitive to another
 * @param context Pointer to the Context
 * @param sourceUUID UUID of the source primitive
 * @param destinationUUID UUID of the destination primitive
 */
PYHELIOS_API void copyPrimitiveData(helios::Context* context, unsigned int sourceUUID, unsigned int destinationUUID);

/**
 * @brief Copy a single object
 * @param context Pointer to the Context
 * @param objID Object ID to copy
 * @return Object ID of the copied object
 */
PYHELIOS_API unsigned int copyObject(helios::Context* context, unsigned int objID);

/**
 * @brief Copy multiple objects
 * @param context Pointer to the Context
 * @param objIDs Pointer to array of object IDs to copy
 * @param count Number of object IDs in the array
 * @param result_count Output parameter for number of copied objects
 * @return Pointer to array of object IDs for the copied objects
 */
PYHELIOS_API unsigned int* copyObjects(helios::Context* context, unsigned int* objIDs, unsigned int count, unsigned int* result_count);

/**
 * @brief Copy all object data from one object to another
 * @param context Pointer to the Context
 * @param source_objID Object ID of the source object
 * @param destination_objID Object ID of the destination object
 */
PYHELIOS_API void copyObjectData(helios::Context* context, unsigned int source_objID, unsigned int destination_objID);

/**
 * @brief Translate a single primitive
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive to translate
 * @param shift Array of 3 floats [x, y, z] representing the translation vector
 */
PYHELIOS_API void translatePrimitive(helios::Context* context, unsigned int uuid, float* shift);

/**
 * @brief Translate multiple primitives
 * @param context Pointer to the Context
 * @param uuids Pointer to array of UUIDs to translate
 * @param count Number of UUIDs in the array
 * @param shift Array of 3 floats [x, y, z] representing the translation vector
 */
PYHELIOS_API void translatePrimitives(helios::Context* context, unsigned int* uuids, unsigned int count, float* shift);

/**
 * @brief Translate a single object
 * @param context Pointer to the Context
 * @param objID Object ID to translate
 * @param shift Array of 3 floats [x, y, z] representing the translation vector
 */
PYHELIOS_API void translateObject(helios::Context* context, unsigned int objID, float* shift);

/**
 * @brief Translate multiple objects
 * @param context Pointer to the Context
 * @param objIDs Pointer to array of object IDs to translate
 * @param count Number of object IDs in the array
 * @param shift Array of 3 floats [x, y, z] representing the translation vector
 */
PYHELIOS_API void translateObjects(helios::Context* context, unsigned int* objIDs, unsigned int count, float* shift);

// ==================== Rotation Operations ====================

/**
 * @brief Rotate a primitive around an axis specified by string ("x", "y", or "z")
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive to rotate
 * @param rotation_radians Rotation angle in radians
 * @param axis Axis string ("x", "y", or "z")
 */
PYHELIOS_API void rotatePrimitive_axisString(helios::Context* context, unsigned int uuid, float rotation_radians, const char* axis);

/**
 * @brief Rotate multiple primitives around an axis specified by string
 * @param context Pointer to the Context
 * @param uuids Pointer to array of UUIDs to rotate
 * @param count Number of UUIDs in the array
 * @param rotation_radians Rotation angle in radians
 * @param axis Axis string ("x", "y", or "z")
 */
PYHELIOS_API void rotatePrimitives_axisString(helios::Context* context, unsigned int* uuids, unsigned int count, float rotation_radians, const char* axis);

/**
 * @brief Rotate a primitive around an axis specified by vector
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive to rotate
 * @param rotation_radians Rotation angle in radians
 * @param axis Array of 3 floats [x, y, z] representing the axis vector
 */
PYHELIOS_API void rotatePrimitive_axisVector(helios::Context* context, unsigned int uuid, float rotation_radians, float* axis);

/**
 * @brief Rotate multiple primitives around an axis specified by vector
 * @param context Pointer to the Context
 * @param uuids Pointer to array of UUIDs to rotate
 * @param count Number of UUIDs in the array
 * @param rotation_radians Rotation angle in radians
 * @param axis Array of 3 floats [x, y, z] representing the axis vector
 */
PYHELIOS_API void rotatePrimitives_axisVector(helios::Context* context, unsigned int* uuids, unsigned int count, float rotation_radians, float* axis);

/**
 * @brief Rotate a primitive around an axis through a specified origin point
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive to rotate
 * @param rotation_radians Rotation angle in radians
 * @param origin Array of 3 floats [x, y, z] representing the origin point
 * @param axis Array of 3 floats [x, y, z] representing the axis vector
 */
PYHELIOS_API void rotatePrimitive_originAxisVector(helios::Context* context, unsigned int uuid, float rotation_radians, float* origin, float* axis);

/**
 * @brief Rotate multiple primitives around an axis through a specified origin point
 * @param context Pointer to the Context
 * @param uuids Pointer to array of UUIDs to rotate
 * @param count Number of UUIDs in the array
 * @param rotation_radians Rotation angle in radians
 * @param origin Array of 3 floats [x, y, z] representing the origin point
 * @param axis Array of 3 floats [x, y, z] representing the axis vector
 */
PYHELIOS_API void rotatePrimitives_originAxisVector(helios::Context* context, unsigned int* uuids, unsigned int count, float rotation_radians, float* origin, float* axis);

/**
 * @brief Rotate an object around an axis specified by string ("x", "y", or "z")
 * @param context Pointer to the Context
 * @param objID Object ID to rotate
 * @param rotation_radians Rotation angle in radians
 * @param axis Axis string ("x", "y", or "z")
 */
PYHELIOS_API void rotateObject_axisString(helios::Context* context, unsigned int objID, float rotation_radians, const char* axis);

/**
 * @brief Rotate multiple objects around an axis specified by string
 * @param context Pointer to the Context
 * @param objIDs Pointer to array of object IDs to rotate
 * @param count Number of object IDs in the array
 * @param rotation_radians Rotation angle in radians
 * @param axis Axis string ("x", "y", or "z")
 */
PYHELIOS_API void rotateObjects_axisString(helios::Context* context, unsigned int* objIDs, unsigned int count, float rotation_radians, const char* axis);

/**
 * @brief Rotate an object around an axis specified by vector
 * @param context Pointer to the Context
 * @param objID Object ID to rotate
 * @param rotation_radians Rotation angle in radians
 * @param axis Array of 3 floats [x, y, z] representing the axis vector
 */
PYHELIOS_API void rotateObject_axisVector(helios::Context* context, unsigned int objID, float rotation_radians, float* axis);

/**
 * @brief Rotate multiple objects around an axis specified by vector
 * @param context Pointer to the Context
 * @param objIDs Pointer to array of object IDs to rotate
 * @param count Number of object IDs in the array
 * @param rotation_radians Rotation angle in radians
 * @param axis Array of 3 floats [x, y, z] representing the axis vector
 */
PYHELIOS_API void rotateObjects_axisVector(helios::Context* context, unsigned int* objIDs, unsigned int count, float rotation_radians, float* axis);

/**
 * @brief Rotate an object around an axis through a specified origin point
 * @param context Pointer to the Context
 * @param objID Object ID to rotate
 * @param rotation_radians Rotation angle in radians
 * @param origin Array of 3 floats [x, y, z] representing the origin point
 * @param axis Array of 3 floats [x, y, z] representing the axis vector
 */
PYHELIOS_API void rotateObject_originAxisVector(helios::Context* context, unsigned int objID, float rotation_radians, float* origin, float* axis);

/**
 * @brief Rotate multiple objects around an axis through a specified origin point
 * @param context Pointer to the Context
 * @param objIDs Pointer to array of object IDs to rotate
 * @param count Number of object IDs in the array
 * @param rotation_radians Rotation angle in radians
 * @param origin Array of 3 floats [x, y, z] representing the origin point
 * @param axis Array of 3 floats [x, y, z] representing the axis vector
 */
PYHELIOS_API void rotateObjects_originAxisVector(helios::Context* context, unsigned int* objIDs, unsigned int count, float rotation_radians, float* origin, float* axis);

/**
 * @brief Rotate an object about the global origin around an axis specified by vector
 * @param context Pointer to the Context
 * @param objID Object ID to rotate
 * @param rotation_radians Rotation angle in radians
 * @param axis Array of 3 floats [x, y, z] representing the axis vector
 */
PYHELIOS_API void rotateObjectAboutOrigin_axisVector(helios::Context* context, unsigned int objID, float rotation_radians, float* axis);

/**
 * @brief Rotate multiple objects about the global origin around an axis specified by vector
 * @param context Pointer to the Context
 * @param objIDs Pointer to array of object IDs to rotate
 * @param count Number of object IDs in the array
 * @param rotation_radians Rotation angle in radians
 * @param axis Array of 3 floats [x, y, z] representing the axis vector
 */
PYHELIOS_API void rotateObjectsAboutOrigin_axisVector(helios::Context* context, unsigned int* objIDs, unsigned int count, float rotation_radians, float* axis);

// ==================== Scaling Operations ====================

/**
 * @brief Scale a primitive
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive to scale
 * @param scale Array of 3 floats [x, y, z] representing the scale factors
 */
PYHELIOS_API void scalePrimitive(helios::Context* context, unsigned int uuid, float* scale);

/**
 * @brief Scale multiple primitives
 * @param context Pointer to the Context
 * @param uuids Pointer to array of UUIDs to scale
 * @param count Number of UUIDs in the array
 * @param scale Array of 3 floats [x, y, z] representing the scale factors
 */
PYHELIOS_API void scalePrimitives(helios::Context* context, unsigned int* uuids, unsigned int count, float* scale);

/**
 * @brief Scale a primitive about a specified point
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive to scale
 * @param scale Array of 3 floats [x, y, z] representing the scale factors
 * @param point Array of 3 floats [x, y, z] representing the point to scale about
 */
PYHELIOS_API void scalePrimitiveAboutPoint(helios::Context* context, unsigned int uuid, float* scale, float* point);

/**
 * @brief Scale multiple primitives about a specified point
 * @param context Pointer to the Context
 * @param uuids Pointer to array of UUIDs to scale
 * @param count Number of UUIDs in the array
 * @param scale Array of 3 floats [x, y, z] representing the scale factors
 * @param point Array of 3 floats [x, y, z] representing the point to scale about
 */
PYHELIOS_API void scalePrimitivesAboutPoint(helios::Context* context, unsigned int* uuids, unsigned int count, float* scale, float* point);

/**
 * @brief Scale an object
 * @param context Pointer to the Context
 * @param objID Object ID to scale
 * @param scale Array of 3 floats [x, y, z] representing the scale factors
 */
PYHELIOS_API void scaleObject(helios::Context* context, unsigned int objID, float* scale);

/**
 * @brief Scale multiple objects
 * @param context Pointer to the Context
 * @param objIDs Pointer to array of object IDs to scale
 * @param count Number of object IDs in the array
 * @param scale Array of 3 floats [x, y, z] representing the scale factors
 */
PYHELIOS_API void scaleObjects(helios::Context* context, unsigned int* objIDs, unsigned int count, float* scale);

/**
 * @brief Scale an object about its center
 * @param context Pointer to the Context
 * @param objID Object ID to scale
 * @param scale Array of 3 floats [x, y, z] representing the scale factors
 */
PYHELIOS_API void scaleObjectAboutCenter(helios::Context* context, unsigned int objID, float* scale);

/**
 * @brief Scale multiple objects about their centers
 * @param context Pointer to the Context
 * @param objIDs Pointer to array of object IDs to scale
 * @param count Number of object IDs in the array
 * @param scale Array of 3 floats [x, y, z] representing the scale factors
 */
PYHELIOS_API void scaleObjectsAboutCenter(helios::Context* context, unsigned int* objIDs, unsigned int count, float* scale);

/**
 * @brief Scale an object about a specified point
 * @param context Pointer to the Context
 * @param objID Object ID to scale
 * @param scale Array of 3 floats [x, y, z] representing the scale factors
 * @param point Array of 3 floats [x, y, z] representing the point to scale about
 */
PYHELIOS_API void scaleObjectAboutPoint(helios::Context* context, unsigned int objID, float* scale, float* point);

/**
 * @brief Scale multiple objects about a specified point
 * @param context Pointer to the Context
 * @param objIDs Pointer to array of object IDs to scale
 * @param count Number of object IDs in the array
 * @param scale Array of 3 floats [x, y, z] representing the scale factors
 * @param point Array of 3 floats [x, y, z] representing the point to scale about
 */
PYHELIOS_API void scaleObjectsAboutPoint(helios::Context* context, unsigned int* objIDs, unsigned int count, float* scale, float* point);

/**
 * @brief Scale an object about the global origin
 * @param context Pointer to the Context
 * @param objID Object ID to scale
 * @param scale Array of 3 floats [x, y, z] representing the scale factors
 */
PYHELIOS_API void scaleObjectAboutOrigin(helios::Context* context, unsigned int objID, float* scale);

/**
 * @brief Scale multiple objects about the global origin
 * @param context Pointer to the Context
 * @param objIDs Pointer to array of object IDs to scale
 * @param count Number of object IDs in the array
 * @param scale Array of 3 floats [x, y, z] representing the scale factors
 */
PYHELIOS_API void scaleObjectsAboutOrigin(helios::Context* context, unsigned int* objIDs, unsigned int count, float* scale);

/**
 * @brief Scale the length of a Cone object by scaling the distance between the two nodes
 * @param context Pointer to the Context
 * @param objID Object ID of the Cone to scale
 * @param scale_factor Factor by which to scale the cone length
 */
PYHELIOS_API void scaleConeObjectLength(helios::Context* context, unsigned int objID, float scale_factor);

/**
 * @brief Scale the girth of a Cone object by scaling the radii at both nodes
 * @param context Pointer to the Context
 * @param objID Object ID of the Cone to scale
 * @param scale_factor Factor by which to scale the cone girth
 */
PYHELIOS_API void scaleConeObjectGirth(helios::Context* context, unsigned int objID, float scale_factor);

// ============================================================================
// Object-Returning Compound Geometry Methods
// ============================================================================

/**
 * @brief Add a spherical compound object (basic)
 * @param context Pointer to the Context
 * @param ndivs Number of tessellations
 * @param center Array of 3 floats [x, y, z] for sphere center
 * @param radius Radius of sphere
 * @return Object ID of new sphere object
 */
PYHELIOS_API unsigned int addSphereObject_basic(helios::Context* context, unsigned int ndivs, float* center, float radius);

/**
 * @brief Add a spherical compound object with color
 * @param context Pointer to the Context
 * @param ndivs Number of tessellations
 * @param center Array of 3 floats [x, y, z] for sphere center
 * @param radius Radius of sphere
 * @param color Array of 3 floats [r, g, b] for color
 * @return Object ID of new sphere object
 */
PYHELIOS_API unsigned int addSphereObject_color(helios::Context* context, unsigned int ndivs, float* center, float radius, float* color);

/**
 * @brief Add a spherical compound object with texture
 * @param context Pointer to the Context
 * @param ndivs Number of tessellations
 * @param center Array of 3 floats [x, y, z] for sphere center
 * @param radius Radius of sphere
 * @param texturefile Path to texture image file
 * @return Object ID of new sphere object
 */
PYHELIOS_API unsigned int addSphereObject_texture(helios::Context* context, unsigned int ndivs, float* center, float radius, const char* texturefile);

/**
 * @brief Add an ellipsoidal compound object (basic)
 * @param context Pointer to the Context
 * @param ndivs Number of tessellations
 * @param center Array of 3 floats [x, y, z] for ellipsoid center
 * @param radius Array of 3 floats [rx, ry, rz] for ellipsoid radii
 * @return Object ID of new sphere object
 */
PYHELIOS_API unsigned int addSphereObject_ellipsoid(helios::Context* context, unsigned int ndivs, float* center, float* radius);

/**
 * @brief Add an ellipsoidal compound object with color
 * @param context Pointer to the Context
 * @param ndivs Number of tessellations
 * @param center Array of 3 floats [x, y, z] for ellipsoid center
 * @param radius Array of 3 floats [rx, ry, rz] for ellipsoid radii
 * @param color Array of 3 floats [r, g, b] for color
 * @return Object ID of new sphere object
 */
PYHELIOS_API unsigned int addSphereObject_ellipsoid_color(helios::Context* context, unsigned int ndivs, float* center, float* radius, float* color);

/**
 * @brief Add an ellipsoidal compound object with texture
 * @param context Pointer to the Context
 * @param ndivs Number of tessellations
 * @param center Array of 3 floats [x, y, z] for ellipsoid center
 * @param radius Array of 3 floats [rx, ry, rz] for ellipsoid radii
 * @param texturefile Path to texture image file
 * @return Object ID of new sphere object
 */
PYHELIOS_API unsigned int addSphereObject_ellipsoid_texture(helios::Context* context, unsigned int ndivs, float* center, float* radius, const char* texturefile);

/**
 * @brief Add a tiled patch object (basic)
 * @param context Pointer to the Context
 * @param center Array of 3 floats [x, y, z] for tile center
 * @param size Array of 2 floats [x, y] for tile size
 * @param rotation Array of 3 floats [radius, elevation, azimuth] for rotation
 * @param subdiv Array of 2 ints [x, y] for subdivisions
 * @return Object ID of new tile object
 */
PYHELIOS_API unsigned int addTileObject_basic(helios::Context* context, float* center, float* size, float* rotation, int* subdiv);

/**
 * @brief Add a tiled patch object with color
 * @param context Pointer to the Context
 * @param center Array of 3 floats [x, y, z] for tile center
 * @param size Array of 2 floats [x, y] for tile size
 * @param rotation Array of 3 floats [radius, elevation, azimuth] for rotation
 * @param subdiv Array of 2 ints [x, y] for subdivisions
 * @param color Array of 3 floats [r, g, b] for color
 * @return Object ID of new tile object
 */
PYHELIOS_API unsigned int addTileObject_color(helios::Context* context, float* center, float* size, float* rotation, int* subdiv, float* color);

/**
 * @brief Add a tiled patch object with texture
 * @param context Pointer to the Context
 * @param center Array of 3 floats [x, y, z] for tile center
 * @param size Array of 2 floats [x, y] for tile size
 * @param rotation Array of 3 floats [radius, elevation, azimuth] for rotation
 * @param subdiv Array of 2 ints [x, y] for subdivisions
 * @param texturefile Path to texture image file
 * @return Object ID of new tile object
 */
PYHELIOS_API unsigned int addTileObject_texture(helios::Context* context, float* center, float* size, float* rotation, int* subdiv, const char* texturefile);

/**
 * @brief Add a tiled patch object with texture and repeat
 * @param context Pointer to the Context
 * @param center Array of 3 floats [x, y, z] for tile center
 * @param size Array of 2 floats [x, y] for tile size
 * @param rotation Array of 3 floats [radius, elevation, azimuth] for rotation
 * @param subdiv Array of 2 ints [x, y] for subdivisions
 * @param texturefile Path to texture image file
 * @param texture_repeat Array of 2 ints [x, y] for texture repetitions
 * @return Object ID of new tile object
 */
PYHELIOS_API unsigned int addTileObject_texture_repeat(helios::Context* context, float* center, float* size, float* rotation, int* subdiv, const char* texturefile, int* texture_repeat);

// addBoxObject
PYHELIOS_API unsigned int addBoxObject_basic(helios::Context* context, float* center, float* size, int* subdiv);
PYHELIOS_API unsigned int addBoxObject_color(helios::Context* context, float* center, float* size, int* subdiv, float* color);
PYHELIOS_API unsigned int addBoxObject_texture(helios::Context* context, float* center, float* size, int* subdiv, const char* texturefile);
PYHELIOS_API unsigned int addBoxObject_color_reverse(helios::Context* context, float* center, float* size, int* subdiv, float* color, bool reverse_normals);
PYHELIOS_API unsigned int addBoxObject_texture_reverse(helios::Context* context, float* center, float* size, int* subdiv, const char* texturefile, bool reverse_normals);

// addConeObject
PYHELIOS_API unsigned int addConeObject_basic(helios::Context* context, unsigned int ndivs, float* node0, float* node1, float radius0, float radius1);
PYHELIOS_API unsigned int addConeObject_color(helios::Context* context, unsigned int ndivs, float* node0, float* node1, float radius0, float radius1, float* color);
PYHELIOS_API unsigned int addConeObject_texture(helios::Context* context, unsigned int ndivs, float* node0, float* node1, float radius0, float radius1, const char* texturefile);

// addDiskObject
PYHELIOS_API unsigned int addDiskObject_basic(helios::Context* context, unsigned int ndivs, float* center, float* size);
PYHELIOS_API unsigned int addDiskObject_rotation(helios::Context* context, unsigned int ndivs, float* center, float* size, float* rotation);
PYHELIOS_API unsigned int addDiskObject_color(helios::Context* context, unsigned int ndivs, float* center, float* size, float* rotation, float* color);
PYHELIOS_API unsigned int addDiskObject_rgba(helios::Context* context, unsigned int ndivs, float* center, float* size, float* rotation, float* color);
PYHELIOS_API unsigned int addDiskObject_texture(helios::Context* context, unsigned int ndivs, float* center, float* size, float* rotation, const char* texturefile);
PYHELIOS_API unsigned int addDiskObject_polar_color(helios::Context* context, int* ndivs, float* center, float* size, float* rotation, float* color);
PYHELIOS_API unsigned int addDiskObject_polar_rgba(helios::Context* context, int* ndivs, float* center, float* size, float* rotation, float* color);
PYHELIOS_API unsigned int addDiskObject_polar_texture(helios::Context* context, int* ndivs, float* center, float* size, float* rotation, const char* texturefile);

// addTubeObject
PYHELIOS_API unsigned int addTubeObject_basic(helios::Context* context, unsigned int radial_subdivisions, float* nodes, unsigned int node_count, float* radii, unsigned int radius_count);
PYHELIOS_API unsigned int addTubeObject_color(helios::Context* context, unsigned int radial_subdivisions, float* nodes, unsigned int node_count, float* radii, unsigned int radius_count, float* colors, unsigned int color_count);
PYHELIOS_API unsigned int addTubeObject_texture(helios::Context* context, unsigned int radial_subdivisions, float* nodes, unsigned int node_count, float* radii, unsigned int radius_count, const char* texturefile);
PYHELIOS_API unsigned int addTubeObject_texture_uv(helios::Context* context, unsigned int radial_subdivisions, float* nodes, unsigned int node_count, float* radii, unsigned int radius_count, const char* texturefile, float* textureuv_ufrac, unsigned int uv_count);

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
 * @brief Check if a primitive exists for a given UUID
 * @param context Pointer to the Context
 * @param uuid Primitive UUID to check
 * @return true if the primitive exists, false otherwise
 */
PYHELIOS_API bool doesPrimitiveExist(helios::Context* context, unsigned int uuid);

/**
 * @brief Check if all primitives exist for a list of UUIDs
 * @param context Pointer to the Context
 * @param uuids Array of primitive UUIDs to check
 * @param count Number of UUIDs in the array
 * @return true if ALL primitives exist, false otherwise (including for empty arrays)
 */
PYHELIOS_API bool doesPrimitiveExistBatch(helios::Context* context, unsigned int* uuids, unsigned int count);

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

/**
 * @brief Write primitive data to an ASCII text file (all primitives)
 * @param context Pointer to the Context
 * @param filename Output filename
 * @param column_labels Array of primitive data labels to include as columns
 * @param label_count Number of column labels
 * @param print_header Whether to print column headers as first line
 * @note Use "UUID" as a column label to include primitive UUIDs
 */
PYHELIOS_API void writePrimitiveData(helios::Context* context, const char* filename, const char** column_labels, unsigned int label_count, bool print_header);

/**
 * @brief Write primitive data to an ASCII text file (selected primitives)
 * @param context Pointer to the Context
 * @param filename Output filename
 * @param column_labels Array of primitive data labels to include as columns
 * @param label_count Number of column labels
 * @param uuids Array of primitive UUIDs to include
 * @param uuid_count Number of UUIDs
 * @param print_header Whether to print column headers as first line
 * @note Use "UUID" as a column label to include primitive UUIDs
 */
PYHELIOS_API void writePrimitiveDataWithUUIDs(helios::Context* context, const char* filename, const char** column_labels, unsigned int label_count, unsigned int* uuids, unsigned int uuid_count, bool print_header);

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

//=============================================================================
// Batch Primitive Data Functions - Broadcast Pattern (same value to all UUIDs)
//=============================================================================

/**
 * @brief Set primitive data as int for multiple primitives (broadcast)
 * @param context Pointer to the Context
 * @param uuids Array of primitive UUIDs
 * @param num_uuids Number of UUIDs in the array
 * @param label Name/label of the data
 * @param value Integer value to set on all primitives
 */
PYHELIOS_API void setBroadcastPrimitiveDataInt(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* label, int value);

/**
 * @brief Set primitive data as unsigned int for multiple primitives (broadcast)
 * @param context Pointer to the Context
 * @param uuids Array of primitive UUIDs
 * @param num_uuids Number of UUIDs in the array
 * @param label Name/label of the data
 * @param value Unsigned integer value to set on all primitives
 */
PYHELIOS_API void setBroadcastPrimitiveDataUInt(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* label, unsigned int value);

/**
 * @brief Set primitive data as float for multiple primitives (broadcast)
 * @param context Pointer to the Context
 * @param uuids Array of primitive UUIDs
 * @param num_uuids Number of UUIDs in the array
 * @param label Name/label of the data
 * @param value Float value to set on all primitives
 */
PYHELIOS_API void setBroadcastPrimitiveDataFloat(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* label, float value);

/**
 * @brief Set primitive data as double for multiple primitives (broadcast)
 * @param context Pointer to the Context
 * @param uuids Array of primitive UUIDs
 * @param num_uuids Number of UUIDs in the array
 * @param label Name/label of the data
 * @param value Double value to set on all primitives
 */
PYHELIOS_API void setBroadcastPrimitiveDataDouble(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* label, double value);

/**
 * @brief Set primitive data as string for multiple primitives (broadcast)
 * @param context Pointer to the Context
 * @param uuids Array of primitive UUIDs
 * @param num_uuids Number of UUIDs in the array
 * @param label Name/label of the data
 * @param value String value to set on all primitives
 */
PYHELIOS_API void setBroadcastPrimitiveDataString(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* label, const char* value);

/**
 * @brief Set primitive data as vec2 for multiple primitives (broadcast)
 * @param context Pointer to the Context
 * @param uuids Array of primitive UUIDs
 * @param num_uuids Number of UUIDs in the array
 * @param label Name/label of the data
 * @param x X component
 * @param y Y component
 */
PYHELIOS_API void setBroadcastPrimitiveDataVec2(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* label, float x, float y);

/**
 * @brief Set primitive data as vec3 for multiple primitives (broadcast)
 * @param context Pointer to the Context
 * @param uuids Array of primitive UUIDs
 * @param num_uuids Number of UUIDs in the array
 * @param label Name/label of the data
 * @param x X component
 * @param y Y component
 * @param z Z component
 */
PYHELIOS_API void setBroadcastPrimitiveDataVec3(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* label, float x, float y, float z);

/**
 * @brief Set primitive data as vec4 for multiple primitives (broadcast)
 * @param context Pointer to the Context
 * @param uuids Array of primitive UUIDs
 * @param num_uuids Number of UUIDs in the array
 * @param label Name/label of the data
 * @param x X component
 * @param y Y component
 * @param z Z component
 * @param w W component
 */
PYHELIOS_API void setBroadcastPrimitiveDataVec4(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* label, float x, float y, float z, float w);

/**
 * @brief Set primitive data as int2 for multiple primitives (broadcast)
 * @param context Pointer to the Context
 * @param uuids Array of primitive UUIDs
 * @param num_uuids Number of UUIDs in the array
 * @param label Name/label of the data
 * @param x X component
 * @param y Y component
 */
PYHELIOS_API void setBroadcastPrimitiveDataInt2(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* label, int x, int y);

/**
 * @brief Set primitive data as int3 for multiple primitives (broadcast)
 * @param context Pointer to the Context
 * @param uuids Array of primitive UUIDs
 * @param num_uuids Number of UUIDs in the array
 * @param label Name/label of the data
 * @param x X component
 * @param y Y component
 * @param z Z component
 */
PYHELIOS_API void setBroadcastPrimitiveDataInt3(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* label, int x, int y, int z);

/**
 * @brief Set primitive data as int4 for multiple primitives (broadcast)
 * @param context Pointer to the Context
 * @param uuids Array of primitive UUIDs
 * @param num_uuids Number of UUIDs in the array
 * @param label Name/label of the data
 * @param x X component
 * @param y Y component
 * @param z Z component
 * @param w W component
 */
PYHELIOS_API void setBroadcastPrimitiveDataInt4(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* label, int x, int y, int z, int w);

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

//=============================================================================
// Timeseries Functions
//=============================================================================

/**
 * @brief Add a data point to a timeseries variable
 * @param context Pointer to the Context
 * @param label Name of the timeseries variable
 * @param value Value of the data point
 * @param day Day of month (1-31)
 * @param month Month of year (1-12)
 * @param year Year (YYYY format)
 * @param hour Hour of day (0-23)
 * @param minute Minute of hour (0-59)
 * @param second Second of minute (0-59)
 */
PYHELIOS_API void addTimeseriesData(helios::Context* context, const char* label, float value,
                                     int day, int month, int year, int hour, int minute, int second);

/**
 * @brief Update the value of an existing timeseries data point
 * @param context Pointer to the Context
 * @param label Name of the timeseries variable
 * @param day Day of month (1-31) of the existing point
 * @param month Month (1-12) of the existing point
 * @param year Year of the existing point
 * @param hour Hour of day (0-23) of the existing point
 * @param minute Minute of hour (0-59) of the existing point
 * @param second Second of minute (0-59) of the existing point
 * @param new_value Replacement value to assign at the specified timestamp
 *
 * Throws a runtime error if the variable does not exist or if no point with the
 * specified (date, time) is found. Use addTimeseriesData() to append a new point.
 */
PYHELIOS_API void updateTimeseriesData(helios::Context* context, const char* label,
                                        int day, int month, int year, int hour, int minute, int second,
                                        float new_value);

/**
 * @brief Set the Context date and time from a timeseries data point index
 * @param context Pointer to the Context
 * @param label Name of the timeseries variable
 * @param index Index of the timeseries data point (0 = earliest)
 */
PYHELIOS_API void setCurrentTimeseriesPoint(helios::Context* context, const char* label, unsigned int index);

/**
 * @brief Query a timeseries value at a specific date and time (with interpolation)
 * @param context Pointer to the Context
 * @param label Name of the timeseries variable
 * @param day Day of month
 * @param month Month of year
 * @param year Year
 * @param hour Hour of day
 * @param minute Minute of hour
 * @param second Second of minute
 * @return Interpolated value at the specified date/time
 */
PYHELIOS_API float queryTimeseriesData_DateTime(helios::Context* context, const char* label,
                                                 int day, int month, int year, int hour, int minute, int second);

/**
 * @brief Query a timeseries value at the current Context date/time
 * @param context Pointer to the Context
 * @param label Name of the timeseries variable
 * @return Value at the current Context date/time
 */
PYHELIOS_API float queryTimeseriesData_Current(helios::Context* context, const char* label);

/**
 * @brief Query a timeseries value by index
 * @param context Pointer to the Context
 * @param label Name of the timeseries variable
 * @param index Index of the data point (0 = earliest)
 * @return Value at the specified index
 */
PYHELIOS_API float queryTimeseriesData_Index(helios::Context* context, const char* label, unsigned int index);

/**
 * @brief Get the Time associated with a timeseries data point
 * @param context Pointer to the Context
 * @param label Name of the timeseries variable
 * @param index Index of the data point (0 = earliest)
 * @param hour Output parameter for hour
 * @param minute Output parameter for minute
 * @param second Output parameter for second
 */
PYHELIOS_API void queryTimeseriesTime(helios::Context* context, const char* label, unsigned int index,
                                       int* hour, int* minute, int* second);

/**
 * @brief Get the Date associated with a timeseries data point
 * @param context Pointer to the Context
 * @param label Name of the timeseries variable
 * @param index Index of the data point (0 = earliest)
 * @param day Output parameter for day
 * @param month Output parameter for month
 * @param year Output parameter for year
 */
PYHELIOS_API void queryTimeseriesDate(helios::Context* context, const char* label, unsigned int index,
                                       int* day, int* month, int* year);

/**
 * @brief Get the number of data points in a timeseries variable
 * @param context Pointer to the Context
 * @param label Name of the timeseries variable
 * @return Number of data points
 */
PYHELIOS_API unsigned int getTimeseriesLength(helios::Context* context, const char* label);

/**
 * @brief Check whether a timeseries variable exists
 * @param context Pointer to the Context
 * @param label Name of the timeseries variable
 * @return true if the variable exists, false otherwise
 */
PYHELIOS_API bool doesTimeseriesVariableExist(helios::Context* context, const char* label);

/**
 * @brief List all existing timeseries variables
 * @param context Pointer to the Context
 * @param count Output parameter for the number of variables
 * @return Array of C-string pointers (valid until next call)
 */
PYHELIOS_API const char** listTimeseriesVariables(helios::Context* context, unsigned int* count);

/**
 * @brief Load tabular timeseries data from a text file
 * @param context Pointer to the Context
 * @param data_file Path to the text file
 * @param column_labels Array of column label strings
 * @param label_count Number of column labels
 * @param delimiter Column delimiter string
 * @param date_string_format Date format string (e.g., "YYYYMMDD", "ISO8601")
 * @param headerlines Number of header lines to skip
 */
PYHELIOS_API void loadTabularTimeseriesData(helios::Context* context, const char* data_file,
                                             const char** column_labels, unsigned int label_count,
                                             const char* delimiter, const char* date_string_format,
                                             unsigned int headerlines);

/**
 * @brief Clear all timeseries data from the context
 * @param context Pointer to the Context
 */
PYHELIOS_API void clearTimeseriesData(helios::Context* context);

/**
 * @brief Delete a single timeseries variable and all of its data points
 * @param context Pointer to the Context
 * @param label Name of the timeseries variable to delete
 * @note If the variable does not exist, the underlying Helios API issues a non-fatal
 *       warning and the call is otherwise a no-op.
 */
PYHELIOS_API void deleteTimeseriesVariable(helios::Context* context, const char* label);

//=============================================================================
// Primitive and Object Deletion Functions
//=============================================================================

/**
 * @brief Delete a single primitive from the context
 * @param context Pointer to the Context
 * @param uuid UUID of the primitive to delete
 * @note If the primitive belongs to a compound object, it is removed from that object.
 *       If the object becomes empty, it is automatically deleted.
 */
PYHELIOS_API void deletePrimitive(helios::Context* context, unsigned int uuid);

/**
 * @brief Delete multiple primitives from the context
 * @param context Pointer to the Context
 * @param uuids Array of primitive UUIDs to delete
 * @param count Number of UUIDs in the array
 * @note If any primitive belongs to a compound object, it is removed from that object.
 *       If any object becomes empty, it is automatically deleted.
 */
PYHELIOS_API void deletePrimitives(helios::Context* context, unsigned int* uuids, unsigned int count);

/**
 * @brief Delete a single compound object from the context
 * @param context Pointer to the Context
 * @param objID Object ID to delete
 * @note Deleting an object also deletes ALL its child primitives.
 */
PYHELIOS_API void deleteObject(helios::Context* context, unsigned int objID);

/**
 * @brief Delete multiple compound objects from the context
 * @param context Pointer to the Context
 * @param objIDs Array of object IDs to delete
 * @param count Number of object IDs in the array
 * @note Deleting objects also deletes ALL their child primitives.
 */
PYHELIOS_API void deleteObjects(helios::Context* context, unsigned int* objIDs, unsigned int count);

//=========================================================================
// Materials System (v1.3.58+)
//=========================================================================

// Core Material Management

/** @brief Add a new material with the given label */
PYHELIOS_API void addMaterial(void* context, const char* material_label);

/** @brief Check if a material with the given label exists */
PYHELIOS_API bool doesMaterialExist(void* context, const char* material_label);

/** @brief Get list of all material labels */
PYHELIOS_API const char** listMaterials(void* context, size_t* count);

/** @brief Delete a material by label */
PYHELIOS_API void deleteMaterial(void* context, const char* material_label);

// Material Properties

/** @brief Get the color of a material */
PYHELIOS_API void getMaterialColor(void* context, const char* material_label, float* color);

/** @brief Set the color of a material */
PYHELIOS_API void setMaterialColor(void* context, const char* material_label, float r, float g, float b, float a);

/** @brief Get the texture file path of a material */
PYHELIOS_API const char* getMaterialTexture(void* context, const char* material_label);

/** @brief Set the texture of a material */
PYHELIOS_API void setMaterialTexture(void* context, const char* material_label, const char* texture_file);

/** @brief Check if material texture color is overridden */
PYHELIOS_API bool isMaterialTextureColorOverridden(void* context, const char* material_label);

/** @brief Set whether material should override texture color */
PYHELIOS_API void setMaterialTextureColorOverride(void* context, const char* material_label, bool override);

/** @brief Get the twosided flag of a material */
PYHELIOS_API unsigned int getMaterialTwosidedFlag(void* context, const char* material_label);

/** @brief Set the twosided flag of a material */
PYHELIOS_API void setMaterialTwosidedFlag(void* context, const char* material_label, unsigned int twosided_flag);

// Primitive-Material Assignment

/** @brief Assign a material to a primitive */
PYHELIOS_API void assignMaterialToPrimitive(void* context, unsigned int UUID, const char* material_label);

/** @brief Assign a material to multiple primitives */
PYHELIOS_API void assignMaterialToPrimitives(void* context, const unsigned int* UUIDs, size_t count, const char* material_label);

/** @brief Assign a material to all primitives in an object */
PYHELIOS_API void assignMaterialToObject(void* context, unsigned int ObjID, const char* material_label);

/** @brief Assign a material to all primitives in multiple objects */
PYHELIOS_API void assignMaterialToObjects(void* context, const unsigned int* ObjIDs, size_t count, const char* material_label);

/** @brief Get the material label assigned to a primitive */
PYHELIOS_API const char* getPrimitiveMaterialLabel(void* context, unsigned int UUID);

/** @brief Get the twosided flag for a primitive (checks material first, then primitive data) */
PYHELIOS_API unsigned int getPrimitiveTwosidedFlag(void* context, unsigned int UUID, unsigned int default_value);

/** @brief Get all primitives that use a given material */
PYHELIOS_API const unsigned int* getPrimitivesUsingMaterial(void* context, const char* material_label, size_t* count);

//=============================================================================
// Texture Functions
//=============================================================================

/** @brief Get the texture file path of a primitive */
PYHELIOS_API const char* getPrimitiveTextureFile(void* context, unsigned int uuid);

/** @brief Set the texture file path of a primitive */
PYHELIOS_API void setPrimitiveTextureFile(void* context, unsigned int uuid, const char* texture_file);

/** @brief Get the texture size of a primitive (width, height) */
PYHELIOS_API void getPrimitiveTextureSize(void* context, unsigned int uuid, int* width, int* height);

/** @brief Get the texture UV coordinates of a primitive */
PYHELIOS_API float* getPrimitiveTextureUV(void* context, unsigned int uuid, unsigned int* size);

/** @brief Check if primitive texture has a transparency channel */
PYHELIOS_API bool primitiveTextureHasTransparencyChannel(void* context, unsigned int uuid);

/** @brief Get the solid fraction of a primitive */
PYHELIOS_API float getPrimitiveSolidFraction(void* context, unsigned int uuid);

/** @brief Override texture color with constant RGB color for a primitive */
PYHELIOS_API void overridePrimitiveTextureColor(void* context, unsigned int uuid);

/** @brief Use texture map color instead of constant RGB color for a primitive */
PYHELIOS_API void usePrimitiveTextureColor(void* context, unsigned int uuid);

/** @brief Check if primitive texture color is overridden */
PYHELIOS_API bool isPrimitiveTextureColorOverridden(void* context, unsigned int uuid);

//=============================================================================
// Fixed-Size Batch Getters
//=============================================================================

/** @brief Get normals for multiple primitives. Returns flattened float array (N*3). */
PYHELIOS_API float* getBatchPrimitiveNormals(void* context, unsigned int* uuids, unsigned int count, unsigned int* result_size);

/** @brief Get colors for multiple primitives. Returns flattened float array (N*3). */
PYHELIOS_API float* getBatchPrimitiveColors(void* context, unsigned int* uuids, unsigned int count, unsigned int* result_size);

/** @brief Get areas for multiple primitives. Returns float array (N). */
PYHELIOS_API float* getBatchPrimitiveAreas(void* context, unsigned int* uuids, unsigned int count, unsigned int* result_size);

/** @brief Get types for multiple primitives. Returns uint array (N). */
PYHELIOS_API unsigned int* getBatchPrimitiveTypes(void* context, unsigned int* uuids, unsigned int count, unsigned int* result_size);

/** @brief Get solid fractions for multiple primitives. Returns float array (N). */
PYHELIOS_API float* getBatchPrimitiveSolidFractions(void* context, unsigned int* uuids, unsigned int count, unsigned int* result_size);

//=============================================================================
// Variable-Size Batch Getters
//=============================================================================

/** @brief Get vertices for multiple primitives. offsets_out must be caller-allocated with count+1 elements. */
PYHELIOS_API float* getBatchPrimitiveVertices(void* context, unsigned int* uuids, unsigned int count, unsigned int* offsets_out, unsigned int* total_floats);

/** @brief Get texture UVs for multiple primitives. offsets_out must be caller-allocated with count+1 elements. */
PYHELIOS_API float* getBatchPrimitiveTextureUV(void* context, unsigned int* uuids, unsigned int count, unsigned int* offsets_out, unsigned int* total_floats);

/** @brief Get texture files for multiple primitives as concatenated string. offsets_out must be caller-allocated with count+1 elements. */
PYHELIOS_API const char* getBatchPrimitiveTextureFiles(void* context, unsigned int* uuids, unsigned int count, unsigned int* offsets_out, unsigned int* total_chars);

/** @brief Get material labels for multiple primitives as concatenated string. offsets_out must be caller-allocated with count+1 elements. */
PYHELIOS_API const char* getBatchPrimitiveMaterialLabels(void* context, unsigned int* uuids, unsigned int count, unsigned int* offsets_out, unsigned int* total_chars);

/** @brief Resolve material texture suppression for batch export. Modifies colors_inout in-place, returns concatenated resolved texture file strings. */
PYHELIOS_API const char* resolveMaterialTextures(
    void* context, unsigned int* uuids, unsigned int count,
    float* colors_inout, unsigned int* tex_offsets_out, unsigned int* total_chars_out);

/**
 * @brief Pack GPU-ready geometry buffers for a set of primitives in a single pass.
 *
 * Produces a binary blob containing contiguous typed arrays that can be loaded
 * directly into Three.js BufferGeometry attributes with zero JS-side conversion.
 *
 * Wire format (all little-endian):
 *   Header (16 bytes):
 *     uint8  version (2)
 *     uint8  flags (reserved)
 *     uint16 group_count
 *     uint32 total_vertices
 *     uint32 total_triangles
 *     uint32 total_primitives
 *   Per-group descriptor (repeated group_count times):
 *     uint32 vertex_start, vertex_count, triangle_start, triangle_count
 *     uint16 texture_path_length
 *     uint8  flags (bit 0: mask_mode, bit 1: has_uvs, bit 2: has_colors)
 *     [texture_path_length bytes] UTF-8 texture path
 *   Contiguous typed arrays:
 *     float32[total_vertices * 3]   positions
 *     float32[total_vertices * 3]   colors
 *     float32[total_vertices * 2]   uvs
 *     uint32[total_triangles * 3]   indices
 *     uint32[total_triangles]       faceToUuid
 *
 * @param context Context pointer
 * @param uuids Array of primitive UUIDs to pack
 * @param count Number of UUIDs
 * @param out_size Output: total byte size of the returned buffer
 * @return Pointer to the packed buffer (thread_local, valid until next call)
 */
PYHELIOS_API unsigned char* packGPUBuffers(
    void* context, unsigned int* uuids, unsigned int count,
    unsigned int* out_size);

// ==================== Visibility Functions ====================

PYHELIOS_API void hidePrimitive(helios::Context* context, unsigned int uuid);
PYHELIOS_API void hidePrimitives(helios::Context* context, unsigned int* uuids, unsigned int count);
PYHELIOS_API void showPrimitive(helios::Context* context, unsigned int uuid);
PYHELIOS_API void showPrimitives(helios::Context* context, unsigned int* uuids, unsigned int count);
PYHELIOS_API bool isPrimitiveHidden(helios::Context* context, unsigned int uuid);

PYHELIOS_API void hideObject(helios::Context* context, unsigned int objID);
PYHELIOS_API void hideObjects(helios::Context* context, unsigned int* objIDs, unsigned int count);
PYHELIOS_API void showObject(helios::Context* context, unsigned int objID);
PYHELIOS_API void showObjects(helios::Context* context, unsigned int* objIDs, unsigned int count);
PYHELIOS_API bool isObjectHidden(helios::Context* context, unsigned int objID);

// ==================== Object Data Functions ====================

// Setters (single object)
PYHELIOS_API void setObjectDataInt(helios::Context* context, unsigned int objID, const char* label, int value);
PYHELIOS_API void setObjectDataUInt(helios::Context* context, unsigned int objID, const char* label, unsigned int value);
PYHELIOS_API void setObjectDataFloat(helios::Context* context, unsigned int objID, const char* label, float value);
PYHELIOS_API void setObjectDataDouble(helios::Context* context, unsigned int objID, const char* label, double value);
PYHELIOS_API void setObjectDataString(helios::Context* context, unsigned int objID, const char* label, const char* value);
PYHELIOS_API void setObjectDataVec2(helios::Context* context, unsigned int objID, const char* label, float x, float y);
PYHELIOS_API void setObjectDataVec3(helios::Context* context, unsigned int objID, const char* label, float x, float y, float z);
PYHELIOS_API void setObjectDataVec4(helios::Context* context, unsigned int objID, const char* label, float x, float y, float z, float w);
PYHELIOS_API void setObjectDataInt2(helios::Context* context, unsigned int objID, const char* label, int x, int y);
PYHELIOS_API void setObjectDataInt3(helios::Context* context, unsigned int objID, const char* label, int x, int y, int z);
PYHELIOS_API void setObjectDataInt4(helios::Context* context, unsigned int objID, const char* label, int x, int y, int z, int w);

// Broadcast setters (multiple objects, same value)
PYHELIOS_API void setBroadcastObjectDataInt(helios::Context* context, unsigned int* objIDs, size_t count, const char* label, int value);
PYHELIOS_API void setBroadcastObjectDataUInt(helios::Context* context, unsigned int* objIDs, size_t count, const char* label, unsigned int value);
PYHELIOS_API void setBroadcastObjectDataFloat(helios::Context* context, unsigned int* objIDs, size_t count, const char* label, float value);
PYHELIOS_API void setBroadcastObjectDataDouble(helios::Context* context, unsigned int* objIDs, size_t count, const char* label, double value);
PYHELIOS_API void setBroadcastObjectDataString(helios::Context* context, unsigned int* objIDs, size_t count, const char* label, const char* value);
PYHELIOS_API void setBroadcastObjectDataVec2(helios::Context* context, unsigned int* objIDs, size_t count, const char* label, float x, float y);
PYHELIOS_API void setBroadcastObjectDataVec3(helios::Context* context, unsigned int* objIDs, size_t count, const char* label, float x, float y, float z);
PYHELIOS_API void setBroadcastObjectDataVec4(helios::Context* context, unsigned int* objIDs, size_t count, const char* label, float x, float y, float z, float w);
PYHELIOS_API void setBroadcastObjectDataInt2(helios::Context* context, unsigned int* objIDs, size_t count, const char* label, int x, int y);
PYHELIOS_API void setBroadcastObjectDataInt3(helios::Context* context, unsigned int* objIDs, size_t count, const char* label, int x, int y, int z);
PYHELIOS_API void setBroadcastObjectDataInt4(helios::Context* context, unsigned int* objIDs, size_t count, const char* label, int x, int y, int z, int w);

// Getters
PYHELIOS_API int getObjectDataInt(helios::Context* context, unsigned int objID, const char* label);
PYHELIOS_API unsigned int getObjectDataUInt(helios::Context* context, unsigned int objID, const char* label);
PYHELIOS_API float getObjectDataFloat(helios::Context* context, unsigned int objID, const char* label);
PYHELIOS_API double getObjectDataDouble(helios::Context* context, unsigned int objID, const char* label);
PYHELIOS_API int getObjectDataString(helios::Context* context, unsigned int objID, const char* label, char* buffer, int buffer_size);
PYHELIOS_API void getObjectDataVec2(helios::Context* context, unsigned int objID, const char* label, float* x, float* y);
PYHELIOS_API void getObjectDataVec3(helios::Context* context, unsigned int objID, const char* label, float* x, float* y, float* z);
PYHELIOS_API void getObjectDataVec4(helios::Context* context, unsigned int objID, const char* label, float* x, float* y, float* z, float* w);
PYHELIOS_API void getObjectDataInt2(helios::Context* context, unsigned int objID, const char* label, int* x, int* y);
PYHELIOS_API void getObjectDataInt3(helios::Context* context, unsigned int objID, const char* label, int* x, int* y, int* z);
PYHELIOS_API void getObjectDataInt4(helios::Context* context, unsigned int objID, const char* label, int* x, int* y, int* z, int* w);

// Utilities
PYHELIOS_API int getObjectDataType(helios::Context* context, unsigned int objID, const char* label);
PYHELIOS_API int getObjectDataSize(helios::Context* context, unsigned int objID, const char* label);
PYHELIOS_API bool doesObjectDataExist(helios::Context* context, unsigned int objID, const char* label);
PYHELIOS_API void clearObjectData(helios::Context* context, unsigned int objID, const char* label);
PYHELIOS_API void clearObjectDataBatch(helios::Context* context, unsigned int* objIDs, unsigned int count, const char* label);
PYHELIOS_API const char** listObjectData(helios::Context* context, unsigned int objID, unsigned int* count);
PYHELIOS_API const char** listAllObjectDataLabels(helios::Context* context, unsigned int* count);
PYHELIOS_API void duplicateObjectData(helios::Context* context, unsigned int objID, const char* old_label, const char* new_label);
PYHELIOS_API void renameObjectData(helios::Context* context, unsigned int objID, const char* old_label, const char* new_label);

// Filters
PYHELIOS_API unsigned int* filterObjectsByDataFloat(helios::Context* context, unsigned int* objIDs, unsigned int count, const char* label, float value, const char* comparator, unsigned int* result_count);
PYHELIOS_API unsigned int* filterObjectsByDataDouble(helios::Context* context, unsigned int* objIDs, unsigned int count, const char* label, double value, const char* comparator, unsigned int* result_count);
PYHELIOS_API unsigned int* filterObjectsByDataInt(helios::Context* context, unsigned int* objIDs, unsigned int count, const char* label, int value, const char* comparator, unsigned int* result_count);
PYHELIOS_API unsigned int* filterObjectsByDataUInt(helios::Context* context, unsigned int* objIDs, unsigned int count, const char* label, unsigned int value, const char* comparator, unsigned int* result_count);
PYHELIOS_API unsigned int* filterObjectsByDataString(helios::Context* context, unsigned int* objIDs, unsigned int count, const char* label, const char* value, unsigned int* result_count);

// ==================== Global Data Functions ====================

// Setters
PYHELIOS_API void setGlobalDataInt(helios::Context* context, const char* label, int value);
PYHELIOS_API void setGlobalDataUInt(helios::Context* context, const char* label, unsigned int value);
PYHELIOS_API void setGlobalDataFloat(helios::Context* context, const char* label, float value);
PYHELIOS_API void setGlobalDataDouble(helios::Context* context, const char* label, double value);
PYHELIOS_API void setGlobalDataString(helios::Context* context, const char* label, const char* value);
PYHELIOS_API void setGlobalDataVec2(helios::Context* context, const char* label, float x, float y);
PYHELIOS_API void setGlobalDataVec3(helios::Context* context, const char* label, float x, float y, float z);
PYHELIOS_API void setGlobalDataVec4(helios::Context* context, const char* label, float x, float y, float z, float w);
PYHELIOS_API void setGlobalDataInt2(helios::Context* context, const char* label, int x, int y);
PYHELIOS_API void setGlobalDataInt3(helios::Context* context, const char* label, int x, int y, int z);
PYHELIOS_API void setGlobalDataInt4(helios::Context* context, const char* label, int x, int y, int z, int w);

// Getters
PYHELIOS_API int getGlobalDataInt(helios::Context* context, const char* label);
PYHELIOS_API unsigned int getGlobalDataUInt(helios::Context* context, const char* label);
PYHELIOS_API float getGlobalDataFloat(helios::Context* context, const char* label);
PYHELIOS_API double getGlobalDataDouble(helios::Context* context, const char* label);
PYHELIOS_API int getGlobalDataString(helios::Context* context, const char* label, char* buffer, int buffer_size);
PYHELIOS_API void getGlobalDataVec2(helios::Context* context, const char* label, float* x, float* y);
PYHELIOS_API void getGlobalDataVec3(helios::Context* context, const char* label, float* x, float* y, float* z);
PYHELIOS_API void getGlobalDataVec4(helios::Context* context, const char* label, float* x, float* y, float* z, float* w);
PYHELIOS_API void getGlobalDataInt2(helios::Context* context, const char* label, int* x, int* y);
PYHELIOS_API void getGlobalDataInt3(helios::Context* context, const char* label, int* x, int* y, int* z);
PYHELIOS_API void getGlobalDataInt4(helios::Context* context, const char* label, int* x, int* y, int* z, int* w);

// Utilities
PYHELIOS_API int getGlobalDataType(helios::Context* context, const char* label);
PYHELIOS_API int getGlobalDataSize(helios::Context* context, const char* label);
PYHELIOS_API bool doesGlobalDataExist(helios::Context* context, const char* label);
PYHELIOS_API void clearGlobalData(helios::Context* context, const char* label);
PYHELIOS_API void renameGlobalData(helios::Context* context, const char* old_label, const char* new_label);
PYHELIOS_API void duplicateGlobalData(helios::Context* context, const char* old_label, const char* new_label);
PYHELIOS_API const char** listGlobalData(helios::Context* context, unsigned int* count);

// Increment
PYHELIOS_API void incrementGlobalDataInt(helios::Context* context, const char* label, int increment);
PYHELIOS_API void incrementGlobalDataUInt(helios::Context* context, const char* label, unsigned int increment);
PYHELIOS_API void incrementGlobalDataFloat(helios::Context* context, const char* label, float increment);
PYHELIOS_API void incrementGlobalDataDouble(helios::Context* context, const char* label, double increment);

// ==================== Primitive Data Statistics & Filtering ====================

// Statistics (float and double return scalars; vec types use output pointers)
PYHELIOS_API float calculatePrimitiveDataMeanFloat(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label);
PYHELIOS_API double calculatePrimitiveDataMeanDouble(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label);
PYHELIOS_API void calculatePrimitiveDataMeanVec2(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label, float* x, float* y);
PYHELIOS_API void calculatePrimitiveDataMeanVec3(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label, float* x, float* y, float* z);
PYHELIOS_API void calculatePrimitiveDataMeanVec4(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label, float* x, float* y, float* z, float* w);

PYHELIOS_API float calculatePrimitiveDataAreaWeightedMeanFloat(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label);
PYHELIOS_API double calculatePrimitiveDataAreaWeightedMeanDouble(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label);

PYHELIOS_API float calculatePrimitiveDataSumFloat(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label);
PYHELIOS_API double calculatePrimitiveDataSumDouble(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label);

PYHELIOS_API float calculatePrimitiveDataAreaWeightedSumFloat(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label);
PYHELIOS_API double calculatePrimitiveDataAreaWeightedSumDouble(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label);

// Scale & Increment
PYHELIOS_API void scalePrimitiveDataWithUUIDs(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label, float factor);
PYHELIOS_API void scalePrimitiveDataAll(helios::Context* context, const char* label, float factor);
PYHELIOS_API void incrementPrimitiveDataInt(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label, int increment);
PYHELIOS_API void incrementPrimitiveDataFloat(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label, float increment);

// Aggregate
PYHELIOS_API void aggregatePrimitiveDataSum(helios::Context* context, unsigned int* uuids, unsigned int count, const char** labels, unsigned int label_count, const char* result_label);
PYHELIOS_API void aggregatePrimitiveDataProduct(helios::Context* context, unsigned int* uuids, unsigned int count, const char** labels, unsigned int label_count, const char* result_label);

// Surface area
PYHELIOS_API float sumPrimitiveSurfaceArea(helios::Context* context, unsigned int* uuids, unsigned int count);

// Filter
PYHELIOS_API unsigned int* filterPrimitivesByDataFloat(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label, float value, const char* comparator, unsigned int* result_count);
PYHELIOS_API unsigned int* filterPrimitivesByDataInt(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label, int value, const char* comparator, unsigned int* result_count);
PYHELIOS_API unsigned int* filterPrimitivesByDataString(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label, const char* value, unsigned int* result_count);

// ==================== Object Geometry Queries ====================
PYHELIOS_API unsigned int getObjectType(helios::Context* context, unsigned int objID);
PYHELIOS_API float* getObjectCenter(helios::Context* context, unsigned int objID);
PYHELIOS_API void getObjectBoundingBox(helios::Context* context, unsigned int objID, float* min_corner, float* max_corner);
PYHELIOS_API void getObjectBoundingBox_batch(helios::Context* context, unsigned int* objIDs, unsigned int count, float* min_corner, float* max_corner);
PYHELIOS_API unsigned int* getObjectPrimitiveUUIDs_batch(helios::Context* context, unsigned int* objIDs, unsigned int count, unsigned int* size);
PYHELIOS_API unsigned int* getObjectPrimitiveUUIDs_nested(helios::Context* context, unsigned int* flat_objIDs, unsigned int* inner_counts, unsigned int outer_count, unsigned int* size);

// Tile
PYHELIOS_API float getTileObjectAreaRatio(helios::Context* context, unsigned int objID);
PYHELIOS_API float* getTileObjectAreaRatio_batch(helios::Context* context, unsigned int* objIDs, unsigned int count, unsigned int* size);
PYHELIOS_API float* getTileObjectCenter(helios::Context* context, unsigned int objID);
PYHELIOS_API float* getTileObjectSize(helios::Context* context, unsigned int objID);
PYHELIOS_API int* getTileObjectSubdivisionCount(helios::Context* context, unsigned int objID);
PYHELIOS_API float* getTileObjectNormal(helios::Context* context, unsigned int objID);
PYHELIOS_API float* getTileObjectTextureUV(helios::Context* context, unsigned int objID, unsigned int* size);
PYHELIOS_API float* getTileObjectVertices(helios::Context* context, unsigned int objID, unsigned int* size);

// Sphere
PYHELIOS_API float* getSphereObjectCenter(helios::Context* context, unsigned int objID);
PYHELIOS_API float* getSphereObjectRadius(helios::Context* context, unsigned int objID);
PYHELIOS_API unsigned int getSphereObjectSubdivisionCount(helios::Context* context, unsigned int objID);
PYHELIOS_API float getSphereObjectVolume(helios::Context* context, unsigned int objID);

// Box
PYHELIOS_API float* getBoxObjectCenter(helios::Context* context, unsigned int objID);
PYHELIOS_API float* getBoxObjectSize(helios::Context* context, unsigned int objID);
PYHELIOS_API int* getBoxObjectSubdivisionCount(helios::Context* context, unsigned int objID);
PYHELIOS_API float getBoxObjectVolume(helios::Context* context, unsigned int objID);

// Disk
PYHELIOS_API float* getDiskObjectCenter(helios::Context* context, unsigned int objID);
PYHELIOS_API float* getDiskObjectSize(helios::Context* context, unsigned int objID);
PYHELIOS_API unsigned int getDiskObjectSubdivisionCount(helios::Context* context, unsigned int objID);

// Tube
PYHELIOS_API unsigned int getTubeObjectSubdivisionCount(helios::Context* context, unsigned int objID);
PYHELIOS_API unsigned int getTubeObjectNodeCount(helios::Context* context, unsigned int objID);
PYHELIOS_API float* getTubeObjectNodes(helios::Context* context, unsigned int objID, unsigned int* size);
PYHELIOS_API float* getTubeObjectNodeRadii(helios::Context* context, unsigned int objID, unsigned int* size);
PYHELIOS_API float* getTubeObjectNodeColors(helios::Context* context, unsigned int objID, unsigned int* size);
PYHELIOS_API float getTubeObjectVolume(helios::Context* context, unsigned int objID);
PYHELIOS_API float getTubeObjectSegmentVolume(helios::Context* context, unsigned int objID, unsigned int segment_index);

// Cone
PYHELIOS_API unsigned int getConeObjectSubdivisionCount(helios::Context* context, unsigned int objID);
PYHELIOS_API float* getConeObjectNodes(helios::Context* context, unsigned int objID, unsigned int* size);
PYHELIOS_API float* getConeObjectNodeRadii(helios::Context* context, unsigned int objID, unsigned int* size);
PYHELIOS_API float* getConeObjectNode(helios::Context* context, unsigned int objID, int number);
PYHELIOS_API float getConeObjectNodeRadius(helios::Context* context, unsigned int objID, int number);
PYHELIOS_API float* getConeObjectAxisUnitVector(helios::Context* context, unsigned int objID);
PYHELIOS_API float getConeObjectLength(helios::Context* context, unsigned int objID);
PYHELIOS_API float getConeObjectVolume(helios::Context* context, unsigned int objID);

// ==================== Primitive Geometry Queries ====================
PYHELIOS_API float* getPatchCenter(helios::Context* context, unsigned int uuid);
PYHELIOS_API float* getPatchSize(helios::Context* context, unsigned int uuid);
PYHELIOS_API float* getTriangleVertex(helios::Context* context, unsigned int uuid, unsigned int number);
PYHELIOS_API float* getVoxelCenter(helios::Context* context, unsigned int uuid);
PYHELIOS_API float* getVoxelSize(helios::Context* context, unsigned int uuid);
PYHELIOS_API unsigned int getPatchCount(helios::Context* context, bool include_hidden);
PYHELIOS_API unsigned int getTriangleCount(helios::Context* context, bool include_hidden);
PYHELIOS_API void getPrimitiveBoundingBox(helios::Context* context, unsigned int uuid, float* min_corner, float* max_corner);
PYHELIOS_API void getPrimitiveBoundingBox_batch(helios::Context* context, unsigned int* uuids, unsigned int count, float* min_corner, float* max_corner);

// ==================== Primitive Color Mutation ====================
PYHELIOS_API void setPrimitiveColor(helios::Context* context, unsigned int uuid, float* color);
PYHELIOS_API void setPrimitiveColor_batch(helios::Context* context, unsigned int* uuids, unsigned int count, float* color);
PYHELIOS_API void setPrimitiveColorRGBA(helios::Context* context, unsigned int uuid, float* color);
PYHELIOS_API void setPrimitiveColorRGBA_batch(helios::Context* context, unsigned int* uuids, unsigned int count, float* color);

// ==================== Primitive Data Introspection / Cleanup ====================
PYHELIOS_API void clearPrimitiveDataByLabel(helios::Context* context, unsigned int uuid, const char* label);
PYHELIOS_API void clearPrimitiveDataByLabel_batch(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label);
PYHELIOS_API const char** listPrimitiveData(helios::Context* context, unsigned int uuid, unsigned int* count);

// ==================== Domain Cropping ====================
PYHELIOS_API void cropDomainX(helios::Context* context, float* xbounds);
PYHELIOS_API void cropDomainY(helios::Context* context, float* ybounds);
PYHELIOS_API void cropDomainZ(helios::Context* context, float* zbounds);
PYHELIOS_API void cropDomainXYZ(helios::Context* context, float* xbounds, float* ybounds, float* zbounds);
PYHELIOS_API unsigned int* cropDomainByUUIDs(helios::Context* context, unsigned int* uuids, unsigned int count, float* xbounds, float* ybounds, float* zbounds, unsigned int* out_size);

//=============================================================================
// Scalar Getters / Setters & List-of-String Getters
//=============================================================================

// ---- Bool getters ----
PYHELIOS_API bool doesObjectExist(helios::Context* context, unsigned int objID);
PYHELIOS_API bool doesObjectContainPrimitive(helios::Context* context, unsigned int objID, unsigned int uuid);
PYHELIOS_API bool doesMaterialDataExist(helios::Context* context, const char* material_label, const char* data_label);
PYHELIOS_API bool objectHasTexture(helios::Context* context, unsigned int objID);
PYHELIOS_API bool isPrimitiveDirty(helios::Context* context, unsigned int uuid);
PYHELIOS_API bool isObjectDataValueCachingEnabled(helios::Context* context, const char* label);
PYHELIOS_API bool isPrimitiveDataValueCachingEnabled(helios::Context* context, const char* label);
PYHELIOS_API bool areObjectPrimitivesComplete(helios::Context* context, unsigned int objID);

// ---- Numeric scalar getters ----
PYHELIOS_API int getJulianDate(helios::Context* context);
PYHELIOS_API unsigned int getMaterialCount(helios::Context* context);
PYHELIOS_API float getObjectArea(helios::Context* context, unsigned int objID);
PYHELIOS_API unsigned int getObjectPrimitiveCount(helios::Context* context, unsigned int objID);
PYHELIOS_API float getPolymeshObjectVolume(helios::Context* context, unsigned int objID);
PYHELIOS_API unsigned int getMaterialIDFromLabel(helios::Context* context, const char* material_label);
PYHELIOS_API unsigned int getPrimitiveMaterialID(helios::Context* context, unsigned int uuid);
PYHELIOS_API uint64_t getGlobalDataVersion(helios::Context* context, const char* label);
PYHELIOS_API unsigned int getPrimitiveParentObjectID(helios::Context* context, unsigned int uuid);

// ---- String returns (buffer pattern) ----
PYHELIOS_API int getObjectTextureFile(helios::Context* context, unsigned int objID, char* buffer, int buffer_size);

// ---- List-of-string returns (index pair to avoid double thread_local) ----
PYHELIOS_API unsigned int listAllPrimitiveDataLabelsCount(helios::Context* context);
PYHELIOS_API int listAllPrimitiveDataLabel(helios::Context* context, unsigned int index, char* buffer, int buffer_size);
PYHELIOS_API unsigned int getLoadedXMLFileCount(helios::Context* context);
PYHELIOS_API int getLoadedXMLFile(helios::Context* context, unsigned int index, char* buffer, int buffer_size);

// ---- Simple actions ----
PYHELIOS_API void printObjectInfo(helios::Context* context, unsigned int objID);
PYHELIOS_API void printPrimitiveInfo(helios::Context* context, unsigned int uuid);
PYHELIOS_API void enablePrimitiveDataValueCaching(helios::Context* context, const char* label);
PYHELIOS_API void disablePrimitiveDataValueCaching(helios::Context* context, const char* label);
PYHELIOS_API void enableObjectDataValueCaching(helios::Context* context, const char* label);
PYHELIOS_API void disableObjectDataValueCaching(helios::Context* context, const char* label);
PYHELIOS_API void setObjectDataFromPrimitiveDataMean(helios::Context* context, unsigned int objID, const char* label);
PYHELIOS_API void renameMaterial(helios::Context* context, const char* old_label, const char* new_label);
PYHELIOS_API void renamePrimitiveData(helios::Context* context, unsigned int uuid, const char* old_label, const char* new_label);
PYHELIOS_API void clearMaterialData(helios::Context* context, const char* material_label, const char* data_label);

//=============================================================================
// Vector-return getters & geometry mutators
//=============================================================================

// ---- Vector<uint> returns (thread_local buffer pattern) ----
PYHELIOS_API unsigned int* getDeletedUUIDs(helios::Context* context, unsigned int* count);
PYHELIOS_API unsigned int* getDirtyUUIDs(helios::Context* context, bool include_deleted, unsigned int* count);
PYHELIOS_API unsigned int* getUniquePrimitiveParentObjectIDs(helios::Context* context, unsigned int* uuids, unsigned int count, bool include_zero, unsigned int* out_count);

// ---- Object normal / origin queries & setters ----
PYHELIOS_API float* getObjectAverageNormal(helios::Context* context, unsigned int objID);
PYHELIOS_API void setObjectAverageNormal(helios::Context* context, unsigned int objID, float* origin, float* new_normal);
PYHELIOS_API void setObjectOrigin(helios::Context* context, unsigned int objID, float* origin);

// ---- Primitive azimuth / elevation setters ----
PYHELIOS_API void setPrimitiveAzimuth(helios::Context* context, unsigned int uuid, float* origin, float new_azimuth);
PYHELIOS_API void setPrimitiveElevation(helios::Context* context, unsigned int uuid, float* origin, float new_elevation);

// ---- Geometry mutators ----
PYHELIOS_API void setTriangleVertices(helios::Context* context, unsigned int uuid, float* vertex0, float* vertex1, float* vertex2);
PYHELIOS_API void setPrimitiveNormal(helios::Context* context, unsigned int uuid, float* origin, float* new_normal);
PYHELIOS_API void setPrimitiveNormalBatch(helios::Context* context, unsigned int* uuids, unsigned int count, float* origin, float* new_normal);
PYHELIOS_API void setPrimitiveParentObjectID(helios::Context* context, unsigned int uuid, unsigned int objID);
PYHELIOS_API void setPrimitiveParentObjectIDBatch(helios::Context* context, unsigned int* uuids, unsigned int count, unsigned int objID);

//=============================================================================
// Material data API + unique data values
//=============================================================================

// ---- setMaterialData<T> (11 type specializations, scalar) ----
PYHELIOS_API void setMaterialDataInt(helios::Context* context, const char* material_label, const char* data_label, int value);
PYHELIOS_API void setMaterialDataUInt(helios::Context* context, const char* material_label, const char* data_label, unsigned int value);
PYHELIOS_API void setMaterialDataFloat(helios::Context* context, const char* material_label, const char* data_label, float value);
PYHELIOS_API void setMaterialDataDouble(helios::Context* context, const char* material_label, const char* data_label, double value);
PYHELIOS_API void setMaterialDataString(helios::Context* context, const char* material_label, const char* data_label, const char* value);
PYHELIOS_API void setMaterialDataVec2(helios::Context* context, const char* material_label, const char* data_label, float x, float y);
PYHELIOS_API void setMaterialDataVec3(helios::Context* context, const char* material_label, const char* data_label, float x, float y, float z);
PYHELIOS_API void setMaterialDataVec4(helios::Context* context, const char* material_label, const char* data_label, float x, float y, float z, float w);
PYHELIOS_API void setMaterialDataInt2(helios::Context* context, const char* material_label, const char* data_label, int x, int y);
PYHELIOS_API void setMaterialDataInt3(helios::Context* context, const char* material_label, const char* data_label, int x, int y, int z);
PYHELIOS_API void setMaterialDataInt4(helios::Context* context, const char* material_label, const char* data_label, int x, int y, int z, int w);

// ---- getMaterialData<T> (11 type specializations, scalar) ----
PYHELIOS_API int getMaterialDataInt(helios::Context* context, const char* material_label, const char* data_label);
PYHELIOS_API unsigned int getMaterialDataUInt(helios::Context* context, const char* material_label, const char* data_label);
PYHELIOS_API float getMaterialDataFloat(helios::Context* context, const char* material_label, const char* data_label);
PYHELIOS_API double getMaterialDataDouble(helios::Context* context, const char* material_label, const char* data_label);
PYHELIOS_API int getMaterialDataString(helios::Context* context, const char* material_label, const char* data_label, char* buffer, int buffer_size);
PYHELIOS_API void getMaterialDataVec2(helios::Context* context, const char* material_label, const char* data_label, float* x, float* y);
PYHELIOS_API void getMaterialDataVec3(helios::Context* context, const char* material_label, const char* data_label, float* x, float* y, float* z);
PYHELIOS_API void getMaterialDataVec4(helios::Context* context, const char* material_label, const char* data_label, float* x, float* y, float* z, float* w);
PYHELIOS_API void getMaterialDataInt2(helios::Context* context, const char* material_label, const char* data_label, int* x, int* y);
PYHELIOS_API void getMaterialDataInt3(helios::Context* context, const char* material_label, const char* data_label, int* x, int* y, int* z);
PYHELIOS_API void getMaterialDataInt4(helios::Context* context, const char* material_label, const char* data_label, int* x, int* y, int* z, int* w);

// ---- Material data type query ----
PYHELIOS_API int getMaterialDataType(helios::Context* context, const char* material_label, const char* data_label);

// ---- Unique data values (3 type specializations each) ----
PYHELIOS_API int* getUniquePrimitiveDataValuesInt(helios::Context* context, const char* label, unsigned int* count);
PYHELIOS_API unsigned int* getUniquePrimitiveDataValuesUInt(helios::Context* context, const char* label, unsigned int* count);
PYHELIOS_API unsigned int getUniquePrimitiveDataValuesStringCount(helios::Context* context, const char* label);
PYHELIOS_API int getUniquePrimitiveDataValuesString(helios::Context* context, const char* label, unsigned int index, char* buffer, int buffer_size);
PYHELIOS_API int* getUniqueObjectDataValuesInt(helios::Context* context, const char* label, unsigned int* count);
PYHELIOS_API unsigned int* getUniqueObjectDataValuesUInt(helios::Context* context, const char* label, unsigned int* count);
PYHELIOS_API unsigned int getUniqueObjectDataValuesStringCount(helios::Context* context, const char* label);
PYHELIOS_API int getUniqueObjectDataValuesString(helios::Context* context, const char* label, unsigned int index, char* buffer, int buffer_size);

//=============================================================================
// 4x4 transformation matrices + domain bounds
//=============================================================================

// ---- 4x4 transformation matrices (row-major, T[i*4+j]) ----
PYHELIOS_API void getObjectTransformationMatrix(helios::Context* context, unsigned int objID, float* T_out);
PYHELIOS_API void setObjectTransformationMatrix(helios::Context* context, unsigned int objID, float* T_in);
PYHELIOS_API void setObjectTransformationMatrixBatch(helios::Context* context, unsigned int* objIDs, unsigned int count, float* T_in);
PYHELIOS_API void getPrimitiveTransformationMatrix(helios::Context* context, unsigned int uuid, float* T_out);
PYHELIOS_API void setPrimitiveTransformationMatrix(helios::Context* context, unsigned int uuid, float* T_in);
PYHELIOS_API void setPrimitiveTransformationMatrixBatch(helios::Context* context, unsigned int* uuids, unsigned int count, float* T_in);

// ---- Domain bounding box / sphere ----
// bounds_out is a flat array: [xmin, xmax, ymin, ymax, zmin, zmax].
PYHELIOS_API void getDomainBoundingBox(helios::Context* context, float* bounds_out);
PYHELIOS_API void getDomainBoundingBoxFiltered(helios::Context* context, unsigned int* uuids, unsigned int count, float* bounds_out);
// center_out is a 3-float array; radius is a scalar out.
PYHELIOS_API void getDomainBoundingSphere(helios::Context* context, float* center_out, float* radius_out);
PYHELIOS_API void getDomainBoundingSphereFiltered(helios::Context* context, unsigned int* uuids, unsigned int count, float* center_out, float* radius_out);

//=============================================================================
// Tube/polymesh + object color/dirty/tile mutators
//=============================================================================

// ---- Tube object mutators ----
// node_xyz_flat is a flat float array of size count*3 (x,y,z, x,y,z, ...).
PYHELIOS_API void setTubeNodes(helios::Context* context, unsigned int objID, float* node_xyz_flat, unsigned int count);
PYHELIOS_API void setTubeRadii(helios::Context* context, unsigned int objID, float* node_radii, unsigned int count);
PYHELIOS_API void scaleTubeGirth(helios::Context* context, unsigned int objID, float scale_factor);
PYHELIOS_API void scaleTubeLength(helios::Context* context, unsigned int objID, float scale_factor);
PYHELIOS_API void pruneTubeNodes(helios::Context* context, unsigned int objID, unsigned int node_index);
PYHELIOS_API void appendTubeSegmentColor(helios::Context* context, unsigned int objID, float* node_position, float node_radius, float* color_rgb);
PYHELIOS_API void appendTubeSegmentTexture(helios::Context* context, unsigned int objID, float* node_position, float node_radius, const char* texturefile, float* textureuv_ufrac);

// ---- Polymesh object creation ----
PYHELIOS_API unsigned int addPolymeshObject(helios::Context* context, unsigned int* uuids, unsigned int count);

// ---- Object color / texture override (RGB single + batch, RGBA single + batch) ----
PYHELIOS_API void setObjectColorRGB(helios::Context* context, unsigned int objID, float* color_rgb);
PYHELIOS_API void setObjectColorRGBBatch(helios::Context* context, unsigned int* objIDs, unsigned int count, float* color_rgb);
PYHELIOS_API void setObjectColorRGBA(helios::Context* context, unsigned int objID, float* color_rgba);
PYHELIOS_API void setObjectColorRGBABatch(helios::Context* context, unsigned int* objIDs, unsigned int count, float* color_rgba);

PYHELIOS_API void overrideObjectTextureColor(helios::Context* context, unsigned int objID);
PYHELIOS_API void overrideObjectTextureColorBatch(helios::Context* context, unsigned int* objIDs, unsigned int count);
PYHELIOS_API void useObjectTextureColor(helios::Context* context, unsigned int objID);
PYHELIOS_API void useObjectTextureColorBatch(helios::Context* context, unsigned int* objIDs, unsigned int count);

// ---- Mark primitive dirty/clean ----
PYHELIOS_API void markPrimitiveDirty(helios::Context* context, unsigned int uuid);
PYHELIOS_API void markPrimitiveDirtyBatch(helios::Context* context, unsigned int* uuids, unsigned int count);
PYHELIOS_API void markPrimitiveClean(helios::Context* context, unsigned int uuid);
PYHELIOS_API void markPrimitiveCleanBatch(helios::Context* context, unsigned int* uuids, unsigned int count);

// ---- Tile subdivision (int2 vs area-ratio overloads, distinct names) ----
PYHELIOS_API void setTileObjectSubdivisionCount(helios::Context* context, unsigned int* objIDs, unsigned int count, int subdiv_x, int subdiv_y);
PYHELIOS_API void setTileObjectSubdivisionByAreaRatio(helios::Context* context, unsigned int* objIDs, unsigned int count, float area_ratio);

//=============================================================================
// Cleanup, XML write, RNG, Location
//=============================================================================

// ---- Cleanup helpers (return new list of survivors via thread_local) ----
PYHELIOS_API unsigned int* cleanDeletedUUIDs(helios::Context* context, unsigned int* uuids_in, unsigned int count_in, unsigned int* count_out);
PYHELIOS_API unsigned int* cleanDeletedObjectIDs(helios::Context* context, unsigned int* objIDs_in, unsigned int count_in, unsigned int* count_out);

// ---- XML write ----
PYHELIOS_API void writeXML(helios::Context* context, const char* filename, bool quiet);
PYHELIOS_API void writeXMLFiltered(helios::Context* context, const char* filename, unsigned int* uuids, unsigned int count, bool quiet);
PYHELIOS_API void writeXML_byobject(helios::Context* context, const char* filename, unsigned int* objIDs, unsigned int count, bool quiet);

// ---- RNG ----
PYHELIOS_API float randu_basic(helios::Context* context);
PYHELIOS_API float randu_range(helios::Context* context, float min, float max);
PYHELIOS_API int randu_int_range(helios::Context* context, int min, int max);
PYHELIOS_API float randn_basic(helios::Context* context);
PYHELIOS_API float randn_params(helios::Context* context, float mean, float stddev);

// ---- Location ----
PYHELIOS_API void setLocation(helios::Context* context, float latitude_deg, float longitude_deg, float utc_offset);
PYHELIOS_API void getLocation(helios::Context* context, float* latitude_deg_out, float* longitude_deg_out, float* utc_offset_out);

//=============================================================================
// Colormap helpers + texture transparency
//=============================================================================

// generateColormap(name, Ncolors) - returns flat RGB triples (3*Ncolors floats).
PYHELIOS_API float* generateColormapNamed(helios::Context* context, const char* colormap_name, unsigned int n_colors, unsigned int* count_out);

// generateTexturesFromColormap returns a list of file paths via count+index pattern.
PYHELIOS_API unsigned int generateTexturesFromColormapCount(helios::Context* context, const char* texture_file, float* colormap_rgb_flat, unsigned int n_colors);
PYHELIOS_API int generateTexturesFromColormapPath(helios::Context* context, unsigned int index, char* buffer, int buffer_size);

// getPrimitiveTextureTransparencyData fills a flat unsigned-char buffer of width*height bytes.
// Returns 1 if transparency data is available, 0 if the primitive has no transparency channel.
PYHELIOS_API int getPrimitiveTextureTransparencyDataInfo(helios::Context* context, unsigned int uuid, unsigned int* width_out, unsigned int* height_out);
PYHELIOS_API unsigned char* getPrimitiveTextureTransparencyDataBuffer(helios::Context* context, unsigned int uuid);

#ifdef __cplusplus
}
#endif

#endif // PYHELIOS_WRAPPER_CONTEXT_H