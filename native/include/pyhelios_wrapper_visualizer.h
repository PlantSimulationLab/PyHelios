/**
 * @file pyhelios_wrapper_visualizer.h
 * @brief Visualizer functions for PyHelios C wrapper
 * 
 * This header provides visualization capabilities including 3D rendering,
 * camera control, lighting, and image output functions.
 */

#ifndef PYHELIOS_WRAPPER_VISUALIZER_H
#define PYHELIOS_WRAPPER_VISUALIZER_H

#include "pyhelios_wrapper_common.h"

// Forward declarations for Visualizer interface
class Visualizer;
namespace helios {
    class Context;
}

#ifdef __cplusplus
extern "C" {
#endif

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

/**
 * @brief Color context primitives by primitive data
 * @param visualizer Pointer to the Visualizer
 * @param data_name Name of primitive data to use for coloring
 */
PYHELIOS_API void colorContextPrimitivesByData(Visualizer* visualizer, const char* data_name);

/**
 * @brief Color specific context primitives by primitive data
 * @param visualizer Pointer to the Visualizer
 * @param data_name Name of primitive data to use for coloring
 * @param uuids Array of primitive UUIDs to color
 * @param count Number of UUIDs in the array
 */
PYHELIOS_API void colorContextPrimitivesByDataUUIDs(Visualizer* visualizer, const char* data_name, unsigned int* uuids, unsigned int count);

//=============================================================================
// Camera Control Functions
//=============================================================================

/**
 * @brief Set camera field of view angle
 * @param visualizer Pointer to the Visualizer
 * @param angle_FOV Field of view angle in degrees
 */
PYHELIOS_API void setCameraFieldOfView(Visualizer* visualizer, float angle_FOV);

/**
 * @brief Get camera position and look-at point
 * @param visualizer Pointer to the Visualizer
 * @param camera_position Array to store camera position [x, y, z]
 * @param look_at_point Array to store look-at point [x, y, z]
 */
PYHELIOS_API void getCameraPosition(Visualizer* visualizer, float* camera_position, float* look_at_point);

/**
 * @brief Get background color
 * @param visualizer Pointer to the Visualizer
 * @param color Array to store background color [r, g, b]
 */
PYHELIOS_API void getBackgroundColor(Visualizer* visualizer, float* color);

//=============================================================================
// Lighting Control Functions
//=============================================================================

/**
 * @brief Set light intensity scaling factor
 * @param visualizer Pointer to the Visualizer
 * @param intensity_factor Light intensity scaling factor
 */
PYHELIOS_API void setLightIntensityFactor(Visualizer* visualizer, float intensity_factor);

//=============================================================================
// Window and Display Functions
//=============================================================================

/**
 * @brief Get window size in pixels
 * @param visualizer Pointer to the Visualizer
 * @param width Pointer to store window width
 * @param height Pointer to store window height
 */
PYHELIOS_API void getWindowSize(Visualizer* visualizer, unsigned int* width, unsigned int* height);

/**
 * @brief Get framebuffer size in pixels
 * @param visualizer Pointer to the Visualizer
 * @param width Pointer to store framebuffer width
 * @param height Pointer to store framebuffer height
 */
PYHELIOS_API void getFramebufferSize(Visualizer* visualizer, unsigned int* width, unsigned int* height);

/**
 * @brief Print window with default filename
 * @param visualizer Pointer to the Visualizer
 */
PYHELIOS_API void printWindowDefault(Visualizer* visualizer);

/**
 * @brief Display image from pixel data
 * @param visualizer Pointer to the Visualizer
 * @param pixel_data Array of pixel data (RGBA format)
 * @param width_pixels Image width in pixels
 * @param height_pixels Image height in pixels
 */
PYHELIOS_API void displayImageFromPixels(Visualizer* visualizer, unsigned char* pixel_data, unsigned int width_pixels, unsigned int height_pixels);

/**
 * @brief Display image from file
 * @param visualizer Pointer to the Visualizer
 * @param file_name Path to image file
 */
PYHELIOS_API void displayImageFromFile(Visualizer* visualizer, const char* file_name);

//=============================================================================
// Window Data Access Functions
//=============================================================================

/**
 * @brief Get RGB pixel data from current window
 * @param visualizer Pointer to the Visualizer
 * @param buffer Buffer to store pixel data (must be pre-allocated)
 */
PYHELIOS_API void getWindowPixelsRGB(Visualizer* visualizer, unsigned int* buffer);

/**
 * @brief Get depth map from current window
 * @param visualizer Pointer to the Visualizer
 * @param depth_pixels Pointer to store depth data pointer
 * @param width_pixels Pointer to store width
 * @param height_pixels Pointer to store height
 * @param buffer_size Pointer to store buffer size
 */
PYHELIOS_API void getDepthMap(Visualizer* visualizer, float** depth_pixels, unsigned int* width_pixels, unsigned int* height_pixels, unsigned int* buffer_size);

/**
 * @brief Plot depth map visualization
 * @param visualizer Pointer to the Visualizer
 */
PYHELIOS_API void plotDepthMap(Visualizer* visualizer);

//=============================================================================
// Geometry Management Functions
//=============================================================================

/**
 * @brief Clear all geometry from visualizer
 * @param visualizer Pointer to the Visualizer
 */
PYHELIOS_API void clearGeometry(Visualizer* visualizer);

/**
 * @brief Clear context geometry from visualizer
 * @param visualizer Pointer to the Visualizer
 */
PYHELIOS_API void clearContextGeometry(Visualizer* visualizer);

/**
 * @brief Delete specific geometry by ID
 * @param visualizer Pointer to the Visualizer
 * @param geometry_id ID of geometry to delete
 */
PYHELIOS_API void deleteGeometry(Visualizer* visualizer, unsigned int geometry_id);

/**
 * @brief Update context primitive colors
 * @param visualizer Pointer to the Visualizer
 */
PYHELIOS_API void updateContextPrimitiveColors(Visualizer* visualizer);

//=============================================================================
// Coordinate Axes and Grid Functions
//=============================================================================

/**
 * @brief Add coordinate axes at origin with unit length
 * @param visualizer Pointer to the Visualizer
 */
PYHELIOS_API void addCoordinateAxes(Visualizer* visualizer);

/**
 * @brief Add coordinate axes with custom properties
 * @param visualizer Pointer to the Visualizer
 * @param origin Array of 3 floats [x, y, z] for axes origin
 * @param length Array of 3 floats [x, y, z] for axes length
 * @param sign_string String specifying axis direction ("both" or "positive")
 */
PYHELIOS_API void addCoordinateAxesCustom(Visualizer* visualizer, float* origin, float* length, const char* sign_string);

/**
 * @brief Remove coordinate axes
 * @param visualizer Pointer to the Visualizer
 */
PYHELIOS_API void disableCoordinateAxes(Visualizer* visualizer);

/**
 * @brief Add grid wireframe
 * @param visualizer Pointer to the Visualizer
 * @param center Array of 3 floats [x, y, z] for grid center
 * @param size Array of 3 floats [x, y, z] for grid size
 * @param subdivisions Array of 3 ints [x, y, z] for grid subdivisions
 */
PYHELIOS_API void addGridWireFrame(Visualizer* visualizer, float* center, float* size, int* subdivisions);

//=============================================================================
// Colorbar Control Functions
//=============================================================================

/**
 * @brief Enable colorbar
 * @param visualizer Pointer to the Visualizer
 */
PYHELIOS_API void enableColorbar(Visualizer* visualizer);

/**
 * @brief Disable colorbar
 * @param visualizer Pointer to the Visualizer
 */
PYHELIOS_API void disableColorbar(Visualizer* visualizer);

/**
 * @brief Set colorbar position
 * @param visualizer Pointer to the Visualizer
 * @param position Array of 3 floats [x, y, z] for colorbar position
 */
PYHELIOS_API void setColorbarPosition(Visualizer* visualizer, float* position);

/**
 * @brief Set colorbar size
 * @param visualizer Pointer to the Visualizer
 * @param size Array of 2 floats [width, height] for colorbar size
 */
PYHELIOS_API void setColorbarSize(Visualizer* visualizer, float* size);

/**
 * @brief Set colorbar range
 * @param visualizer Pointer to the Visualizer
 * @param min_val Minimum value
 * @param max_val Maximum value
 */
PYHELIOS_API void setColorbarRange(Visualizer* visualizer, float min_val, float max_val);

/**
 * @brief Set colorbar ticks
 * @param visualizer Pointer to the Visualizer
 * @param ticks Array of tick values
 * @param count Number of ticks
 */
PYHELIOS_API void setColorbarTicks(Visualizer* visualizer, float* ticks, unsigned int count);

/**
 * @brief Set colorbar title
 * @param visualizer Pointer to the Visualizer
 * @param title Colorbar title string
 */
PYHELIOS_API void setColorbarTitle(Visualizer* visualizer, const char* title);

/**
 * @brief Set colorbar font color
 * @param visualizer Pointer to the Visualizer
 * @param color Array of 3 floats [r, g, b] for font color
 */
PYHELIOS_API void setColorbarFontColor(Visualizer* visualizer, float* color);

/**
 * @brief Set colorbar font size
 * @param visualizer Pointer to the Visualizer
 * @param font_size Font size value
 */
PYHELIOS_API void setColorbarFontSize(Visualizer* visualizer, unsigned int font_size);

//=============================================================================
// Colormap Functions
//=============================================================================

/**
 * @brief Set predefined colormap
 * @param visualizer Pointer to the Visualizer
 * @param colormap_id Colormap ID (0=HOT, 1=COOL, 2=RAINBOW, 3=LAVA, 4=PARULA, 5=GRAY)
 */
PYHELIOS_API void setColormap(Visualizer* visualizer, unsigned int colormap_id);

/**
 * @brief Set custom colormap
 * @param visualizer Pointer to the Visualizer
 * @param colors Array of RGB colors (3 floats per color)
 * @param divisions Array of division points
 * @param count Number of colors/divisions
 */
PYHELIOS_API void setCustomColormap(Visualizer* visualizer, float* colors, float* divisions, unsigned int count);

//=============================================================================
// Object/Primitive Coloring Functions
//=============================================================================

/**
 * @brief Color context primitives by object data
 * @param visualizer Pointer to the Visualizer
 * @param data_name Name of object data to use for coloring
 */
PYHELIOS_API void colorContextPrimitivesByObjectData(Visualizer* visualizer, const char* data_name);

/**
 * @brief Color specific context primitives by object data
 * @param visualizer Pointer to the Visualizer
 * @param data_name Name of object data to use for coloring
 * @param obj_ids Array of object IDs to color
 * @param count Number of object IDs
 */
PYHELIOS_API void colorContextPrimitivesByObjectDataIDs(Visualizer* visualizer, const char* data_name, unsigned int* obj_ids, unsigned int count);

/**
 * @brief Color context primitives randomly
 * @param visualizer Pointer to the Visualizer
 * @param uuids Array of primitive UUIDs to color (NULL for all)
 * @param count Number of UUIDs (0 for all)
 */
PYHELIOS_API void colorContextPrimitivesRandomly(Visualizer* visualizer, unsigned int* uuids, unsigned int count);

/**
 * @brief Color context objects randomly
 * @param visualizer Pointer to the Visualizer
 * @param obj_ids Array of object IDs to color (NULL for all)
 * @param count Number of object IDs (0 for all)
 */
PYHELIOS_API void colorContextObjectsRandomly(Visualizer* visualizer, unsigned int* obj_ids, unsigned int count);

/**
 * @brief Clear primitive colors from previous coloring operations
 * @param visualizer Pointer to the Visualizer
 */
PYHELIOS_API void clearColor(Visualizer* visualizer);

//=============================================================================
// Watermark Control Functions
//=============================================================================

/**
 * @brief Hide watermark
 * @param visualizer Pointer to the Visualizer
 */
PYHELIOS_API void hideWatermark(Visualizer* visualizer);

/**
 * @brief Show watermark
 * @param visualizer Pointer to the Visualizer
 */
PYHELIOS_API void showWatermark(Visualizer* visualizer);

/**
 * @brief Update watermark geometry
 * @param visualizer Pointer to the Visualizer
 */
PYHELIOS_API void updateWatermark(Visualizer* visualizer);

//=============================================================================
// Performance and Utility Functions
//=============================================================================

/**
 * @brief Enable console messages
 * @param visualizer Pointer to the Visualizer
 */
PYHELIOS_API void enableMessages(Visualizer* visualizer);

/**
 * @brief Disable console messages
 * @param visualizer Pointer to the Visualizer
 */
PYHELIOS_API void disableMessages(Visualizer* visualizer);

/**
 * @brief Run one rendering loop
 * @param visualizer Pointer to the Visualizer
 * @param get_keystrokes Whether to process keystrokes
 */
PYHELIOS_API void plotOnce(Visualizer* visualizer, bool get_keystrokes);

/**
 * @brief Update visualization with window visibility control
 * @param visualizer Pointer to the Visualizer
 * @param hide_window Whether to hide the window
 */
PYHELIOS_API void plotUpdateWithVisibility(Visualizer* visualizer, bool hide_window);

//=============================================================================
// v1.3.53 Background Control Functions
//=============================================================================

/**
 * @brief Enable transparent background mode (v1.3.53+)
 * @param visualizer Pointer to the Visualizer
 */
PYHELIOS_API void setBackgroundTransparent(Visualizer* visualizer);

/**
 * @brief Set custom background image texture (v1.3.53+)
 * @param visualizer Pointer to the Visualizer
 * @param texture_file Path to texture file (JPEG or PNG)
 */
PYHELIOS_API void setBackgroundImage(Visualizer* visualizer, const char* texture_file);

/**
 * @brief Set sky sphere texture background with automatic scaling (v1.3.53+)
 * @param visualizer Pointer to the Visualizer
 * @param texture_file Path to texture file (NULL for default gradient)
 * @param divisions Number of sphere divisions for tessellation
 */
PYHELIOS_API void setBackgroundSkyTexture(Visualizer* visualizer, const char* texture_file, unsigned int divisions);

//=============================================================================
// v1.3.53 Navigation Gizmo Functions
//=============================================================================

/**
 * @brief Hide navigation gizmo (coordinate axes indicator) (v1.3.53+)
 * @param visualizer Pointer to the Visualizer
 */
PYHELIOS_API void hideNavigationGizmo(Visualizer* visualizer);

/**
 * @brief Show navigation gizmo (coordinate axes indicator) (v1.3.53+)
 * @param visualizer Pointer to the Visualizer
 */
PYHELIOS_API void showNavigationGizmo(Visualizer* visualizer);

//=============================================================================
// v1.3.53 Geometry Vertex Manipulation Functions
//=============================================================================

/**
 * @brief Get vertices of a geometry primitive (v1.3.53+)
 * @param visualizer Pointer to the Visualizer
 * @param geometry_id ID of the geometry primitive
 * @param vertices Pointer to store vertex data (array of floats: x1,y1,z1,x2,y2,z2,...)
 * @param vertex_count Pointer to store number of vertices
 */
PYHELIOS_API void getGeometryVertices(Visualizer* visualizer, size_t geometry_id, float** vertices, size_t* vertex_count);

/**
 * @brief Set vertices of a geometry primitive (v1.3.53+)
 * @param visualizer Pointer to the Visualizer
 * @param geometry_id ID of the geometry primitive
 * @param vertices Array of vertex data (floats: x1,y1,z1,x2,y2,z2,...)
 * @param vertex_count Number of vertices in the array
 */
PYHELIOS_API void setGeometryVertices(Visualizer* visualizer, size_t geometry_id, float* vertices, size_t vertex_count);

//=============================================================================
// v1.3.53 Enhanced Image Export
//=============================================================================

/**
 * @brief Save current visualization to image file with format specification (v1.3.53+)
 * @param visualizer Pointer to the Visualizer
 * @param filename Output filename for image
 * @param format Image format ("jpeg" or "png")
 */
PYHELIOS_API void printWindowWithFormat(Visualizer* visualizer, const char* filename, const char* format);

//=============================================================================
// v1.3.54 Point Culling and LOD Functions
//=============================================================================

/**
 * @brief Enable or disable point cloud culling optimization (v1.3.54+)
 * @param visualizer Pointer to the Visualizer
 * @param enabled True to enable culling, false to disable
 */
PYHELIOS_API void setPointCullingEnabled(Visualizer* visualizer, bool enabled);

/**
 * @brief Set the minimum number of points required to trigger culling (v1.3.54+)
 * @param visualizer Pointer to the Visualizer
 * @param threshold Point count threshold for enabling culling (default: 10000)
 */
PYHELIOS_API void setPointCullingThreshold(Visualizer* visualizer, size_t threshold);

/**
 * @brief Set the maximum rendering distance for points (v1.3.54+)
 * @param visualizer Pointer to the Visualizer
 * @param distance Maximum distance in world units (0 = auto-calculate based on scene size)
 */
PYHELIOS_API void setPointMaxRenderDistance(Visualizer* visualizer, float distance);

/**
 * @brief Set the level-of-detail factor for distance-based culling (v1.3.54+)
 * @param visualizer Pointer to the Visualizer
 * @param factor LOD factor (higher values = more aggressive culling, typical range: 1.0-50.0)
 */
PYHELIOS_API void setPointLODFactor(Visualizer* visualizer, float factor);

/**
 * @brief Get point cloud rendering performance metrics (v1.3.54+)
 * @param visualizer Pointer to the Visualizer
 * @param total_points Output parameter for total point count in scene
 * @param rendered_points Output parameter for number of points actually rendered after culling
 * @param culling_time_ms Output parameter for time spent on culling in milliseconds
 */
PYHELIOS_API void getPointRenderingMetrics(const Visualizer* visualizer,
                                            size_t* total_points,
                                            size_t* rendered_points,
                                            float* culling_time_ms);

#ifdef __cplusplus
}
#endif

#endif // PYHELIOS_WRAPPER_VISUALIZER_H