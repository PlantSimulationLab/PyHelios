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

#ifdef __cplusplus
}
#endif

#endif // PYHELIOS_WRAPPER_VISUALIZER_H