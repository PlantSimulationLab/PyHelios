/**
 * @file pyhelios_wrapper.h
 * @brief C wrapper functions for PyHelios to interface with Helios C++ library
 * 
 * This header provides C-style function declarations that can be called from
 * Python ctypes. Each function wraps the corresponding Helios C++ functionality.
 */

#ifndef PYHELIOS_WRAPPER_H
#define PYHELIOS_WRAPPER_H

// Windows DLL export/import declarations
#ifdef _WIN32
    #ifdef BUILDING_PYHELIOS_DLL
        #define PYHELIOS_API __declspec(dllexport)
    #else
        #define PYHELIOS_API __declspec(dllimport)
    #endif
#else
    #define PYHELIOS_API
#endif

#include <stddef.h>  // For size_t

// Error code enumeration for robust error handling
typedef enum {
    PYHELIOS_SUCCESS = 0,                         // No error
    PYHELIOS_ERROR_INVALID_PARAMETER = 1,         // Invalid parameter passed
    PYHELIOS_ERROR_UUID_NOT_FOUND = 2,            // UUID not found in context
    PYHELIOS_ERROR_FILE_IO = 3,                   // File I/O error
    PYHELIOS_ERROR_MEMORY_ALLOCATION = 4,         // Memory allocation failure
    PYHELIOS_ERROR_GPU_INITIALIZATION = 5,       // GPU initialization failed
    PYHELIOS_ERROR_PLUGIN_NOT_AVAILABLE = 6,     // Plugin not available
    PYHELIOS_ERROR_RUNTIME = 7,                  // Runtime error (general)
    PYHELIOS_ERROR_UNKNOWN = 99                  // Unknown error
} PyHeliosErrorCode;

#ifdef __cplusplus
extern "C" {
#endif

// Forward declarations for C interface
namespace helios {
    class Context;
}
class Visualizer;
class WeberPennTree;
class RadiationModel;

//=============================================================================
// Error Handling Functions
//=============================================================================

/**
 * @brief Get the last error code
 * @return Error code (0 = success, 1-99 = specific error types)
 */
PYHELIOS_API int getLastErrorCode();

/**
 * @brief Get the last error message
 * @return Pointer to error message string (null-terminated)
 */
PYHELIOS_API const char* getLastErrorMessage();

/**
 * @brief Clear the current error state
 */
PYHELIOS_API void clearError();

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

//=============================================================================
// Visualizer Functions
//=============================================================================

/**
 * @brief Create a Visualizer instance
 * @param width Window width in pixels
 * @param height Window height in pixels
 * @param headless Enable headless mode (no window display)
 * @return Pointer to the created Visualizer
 */
PYHELIOS_API Visualizer* createVisualizer(unsigned int width, unsigned int height, bool headless);

/**
 * @brief Create a Visualizer instance with antialiasing
 * @param width Window width in pixels
 * @param height Window height in pixels
 * @param antialiasing_samples Number of antialiasing samples
 * @param headless Enable headless mode (no window display)
 * @return Pointer to the created Visualizer
 */
PYHELIOS_API Visualizer* createVisualizerWithAntialiasing(unsigned int width, unsigned int height, unsigned int antialiasing_samples, bool headless);

/**
 * @brief Destroy a Visualizer instance
 * @param visualizer Pointer to the Visualizer to destroy
 */
PYHELIOS_API void destroyVisualizer(Visualizer* visualizer);

/**
 * @brief Build Context geometry in the visualizer
 * @param visualizer Pointer to the Visualizer
 * @param context Pointer to the Context
 */
PYHELIOS_API void buildContextGeometry(Visualizer* visualizer, helios::Context* context);

/**
 * @brief Build specific Context geometry UUIDs in the visualizer
 * @param visualizer Pointer to the Visualizer
 * @param context Pointer to the Context
 * @param uuids Array of primitive UUIDs to visualize
 * @param uuid_count Number of UUIDs in the array
 */
PYHELIOS_API void buildContextGeometryUUIDs(Visualizer* visualizer, helios::Context* context, unsigned int* uuids, unsigned int uuid_count);

/**
 * @brief Open interactive visualization window
 * @param visualizer Pointer to the Visualizer
 */
PYHELIOS_API void plotInteractive(Visualizer* visualizer);

/**
 * @brief Update visualization (non-interactive)
 * @param visualizer Pointer to the Visualizer
 */
PYHELIOS_API void plotUpdate(Visualizer* visualizer);

/**
 * @brief Save current visualization to image file
 * @param visualizer Pointer to the Visualizer
 * @param filename Output filename for image
 */
PYHELIOS_API void printWindow(Visualizer* visualizer, const char* filename);

/**
 * @brief Close visualization window
 * @param visualizer Pointer to the Visualizer
 */
PYHELIOS_API void closeWindow(Visualizer* visualizer);

/**
 * @brief Set camera position using Cartesian coordinates
 * @param visualizer Pointer to the Visualizer
 * @param position Array of 3 floats [x, y, z] for camera position
 * @param lookAt Array of 3 floats [x, y, z] for camera look-at point
 */
PYHELIOS_API void setCameraPosition(Visualizer* visualizer, float* position, float* lookAt);

/**
 * @brief Set camera position using spherical coordinates
 * @param visualizer Pointer to the Visualizer
 * @param angle Array of 3 floats [radius, zenith, azimuth] for camera position
 * @param lookAt Array of 3 floats [x, y, z] for camera look-at point
 */
PYHELIOS_API void setCameraPositionSpherical(Visualizer* visualizer, float* angle, float* lookAt);

/**
 * @brief Set background color
 * @param visualizer Pointer to the Visualizer
 * @param color Array of 3 floats [r, g, b] for background color
 */
PYHELIOS_API void setBackgroundColor(Visualizer* visualizer, float* color);

/**
 * @brief Set light direction
 * @param visualizer Pointer to the Visualizer
 * @param direction Array of 3 floats [x, y, z] for light direction vector
 */
PYHELIOS_API void setLightDirection(Visualizer* visualizer, float* direction);

/**
 * @brief Set lighting model
 * @param visualizer Pointer to the Visualizer
 * @param lighting_model Lighting model (0=NONE, 1=PHONG, 2=PHONG_SHADOWED)
 */
PYHELIOS_API void setLightingModel(Visualizer* visualizer, unsigned int lighting_model);

/**
 * @brief Validate texture file
 * @param texture_file Path to texture file
 * @return true if file is valid, false otherwise
 */
PYHELIOS_API bool validateTextureFile(const char* texture_file);

//=============================================================================
// WeberPennTree Functions
//=============================================================================

/**
 * @brief Create a WeberPennTree instance
 * @param context Pointer to the Helios Context
 * @return Pointer to the created WeberPennTree
 */
PYHELIOS_API WeberPennTree* createWeberPennTree(helios::Context* context);

/**
 * @brief Create a WeberPennTree instance with build directory
 * @param context Pointer to the Helios Context
 * @param buildDirectory Path to the build directory
 * @return Pointer to the created WeberPennTree
 */
PYHELIOS_API WeberPennTree* createWeberPennTreeWithBuildPluginRootDirectory(helios::Context* context, const char* buildDirectory);

/**
 * @brief Destroy a WeberPennTree instance
 * @param wpt Pointer to the WeberPennTree to destroy
 */
PYHELIOS_API void destroyWeberPennTree(WeberPennTree* wpt);

/**
 * @brief Build a tree with specified name and origin
 * @param wpt Pointer to the WeberPennTree
 * @param treename Name of the tree type to build
 * @param origin Array of 3 floats [x, y, z] for tree origin
 * @return Tree ID
 */
PYHELIOS_API unsigned int buildTree(WeberPennTree* wpt, const char* treename, float* origin);

/**
 * @brief Build a tree with specified name, origin, and scale
 * @param wpt Pointer to the WeberPennTree
 * @param treename Name of the tree type to build
 * @param origin Array of 3 floats [x, y, z] for tree origin
 * @param scale Scale factor for the tree
 * @return Tree ID
 */
PYHELIOS_API unsigned int buildTreeWithScale(WeberPennTree* wpt, const char* treename, float* origin, float scale);

/**
 * @brief Get UUIDs of trunk primitives for a tree
 * @param wpt Pointer to the WeberPennTree
 * @param treeID ID of the tree
 * @param size Pointer to store the number of UUIDs returned
 * @return Pointer to array of UUIDs
 */
PYHELIOS_API unsigned int* getWeberPennTreeTrunkUUIDs(WeberPennTree* wpt, unsigned int treeID, unsigned int* size);

/**
 * @brief Get UUIDs of branch primitives for a tree
 * @param wpt Pointer to the WeberPennTree
 * @param treeID ID of the tree
 * @param size Pointer to store the number of UUIDs returned
 * @return Pointer to array of UUIDs
 */
PYHELIOS_API unsigned int* getWeberPennTreeBranchUUIDs(WeberPennTree* wpt, unsigned int treeID, unsigned int* size);

/**
 * @brief Get UUIDs of leaf primitives for a tree
 * @param wpt Pointer to the WeberPennTree
 * @param treeID ID of the tree
 * @param size Pointer to store the number of UUIDs returned
 * @return Pointer to array of UUIDs
 */
PYHELIOS_API unsigned int* getWeberPennTreeLeafUUIDs(WeberPennTree* wpt, unsigned int treeID, unsigned int* size);

/**
 * @brief Get UUIDs of all primitives for a tree
 * @param wpt Pointer to the WeberPennTree
 * @param treeID ID of the tree
 * @param size Pointer to store the number of UUIDs returned
 * @return Pointer to array of UUIDs
 */
PYHELIOS_API unsigned int* getWeberPennTreeAllUUIDs(WeberPennTree* wpt, unsigned int treeID, unsigned int* size);

/**
 * @brief Set branch recursion level
 * @param wpt Pointer to the WeberPennTree
 * @param level Recursion level for branches
 */
PYHELIOS_API void setBranchRecursionLevel(WeberPennTree* wpt, unsigned int level);

/**
 * @brief Set trunk segment resolution
 * @param wpt Pointer to the WeberPennTree
 * @param trunk_segs Number of segments for trunk
 */
PYHELIOS_API void setTrunkSegmentResolution(WeberPennTree* wpt, unsigned int trunk_segs);

/**
 * @brief Set branch segment resolution
 * @param wpt Pointer to the WeberPennTree
 * @param branch_segs Number of segments for branches
 */
PYHELIOS_API void setBranchSegmentResolution(WeberPennTree* wpt, unsigned int branch_segs);

/**
 * @brief Set leaf subdivisions
 * @param wpt Pointer to the WeberPennTree
 * @param leaf_segs_x Number of subdivisions in x direction
 * @param leaf_segs_y Number of subdivisions in y direction
 */
PYHELIOS_API void setLeafSubdivisions(WeberPennTree* wpt, unsigned int leaf_segs_x, unsigned int leaf_segs_y);

//=============================================================================
// RadiationModel Functions
//=============================================================================

/**
 * @brief Create a new RadiationModel
 * @param context Pointer to the Helios context
 * @return Pointer to the created RadiationModel, or nullptr on error
 */
PYHELIOS_API RadiationModel* createRadiationModel(helios::Context* context);

/**
 * @brief Destroy a RadiationModel
 * @param radiation_model Pointer to the RadiationModel to destroy
 */
PYHELIOS_API void destroyRadiationModel(RadiationModel* radiation_model);

/**
 * @brief Disable RadiationModel status messages
 * @param radiation_model Pointer to the RadiationModel
 */
PYHELIOS_API void disableRadiationMessages(RadiationModel* radiation_model);

/**
 * @brief Enable RadiationModel status messages
 * @param radiation_model Pointer to the RadiationModel
 */
PYHELIOS_API void enableRadiationMessages(RadiationModel* radiation_model);

/**
 * @brief Add a radiation band
 * @param radiation_model Pointer to the RadiationModel
 * @param label Name/label for the radiation band
 */
PYHELIOS_API void addRadiationBand(RadiationModel* radiation_model, const char* label);

/**
 * @brief Add a radiation band with specified wavelength range
 * @param radiation_model Pointer to the RadiationModel
 * @param label Name/label for the radiation band
 * @param wavelength_min Minimum wavelength
 * @param wavelength_max Maximum wavelength
 */
PYHELIOS_API void addRadiationBandWithWavelengths(RadiationModel* radiation_model, const char* label, float wavelength_min, float wavelength_max);

/**
 * @brief Add a collimated radiation source with default direction
 * @param radiation_model Pointer to the RadiationModel
 * @return Source ID
 */
PYHELIOS_API unsigned int addCollimatedRadiationSourceDefault(RadiationModel* radiation_model);

/**
 * @brief Add a collimated radiation source with vec3 direction
 * @param radiation_model Pointer to the RadiationModel
 * @param x X component of direction vector
 * @param y Y component of direction vector
 * @param z Z component of direction vector
 * @return Source ID
 */
PYHELIOS_API unsigned int addCollimatedRadiationSourceVec3(RadiationModel* radiation_model, float x, float y, float z);

/**
 * @brief Add a collimated radiation source with spherical coordinates
 * @param radiation_model Pointer to the RadiationModel
 * @param elevation Elevation angle in spherical coordinates
 * @param azimuth Azimuth angle in spherical coordinates
 * @param radius Radius in spherical coordinates
 * @return Source ID
 */
PYHELIOS_API unsigned int addCollimatedRadiationSourceSpherical(RadiationModel* radiation_model, float elevation, float azimuth, float radius);

/**
 * @brief Run radiation simulation for a specific band
 * @param radiation_model Pointer to the RadiationModel
 * @param label Name/label of the radiation band to run
 */
PYHELIOS_API void runBand(RadiationModel* radiation_model, const char* label);

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

#ifdef __cplusplus
}
#endif

#endif // PYHELIOS_WRAPPER_H