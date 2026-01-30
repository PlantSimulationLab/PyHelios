/**
 * @file pyhelios_wrapper_lidar.h
 * @brief LiDAR functions for PyHelios C wrapper
 *
 * This header provides LiDAR point cloud processing, synthetic scanning,
 * triangulation, and leaf area density calculations.
 */

#ifndef PYHELIOS_WRAPPER_LIDAR_H
#define PYHELIOS_WRAPPER_LIDAR_H

#include "pyhelios_wrapper_common.h"

// Forward declarations for LiDAR interface
class LiDARcloud;
namespace helios {
    class Context;
}

#ifdef __cplusplus
extern "C" {
#endif

//=============================================================================
// LiDAR Cloud Lifecycle
//=============================================================================

/**
 * @brief Create a new LiDARcloud instance
 * @return Pointer to the created LiDARcloud, or nullptr on error
 */
PYHELIOS_API LiDARcloud* createLiDARcloud();

/**
 * @brief Destroy a LiDARcloud instance
 * @param cloud Pointer to the LiDARcloud to destroy
 */
PYHELIOS_API void destroyLiDARcloud(LiDARcloud* cloud);

//=============================================================================
// Scan Management
//=============================================================================

/**
 * @brief Add a LiDAR scan to the point cloud
 * @param cloud Pointer to the LiDARcloud instance
 * @param origin Scanner position as [x, y, z]
 * @param Ntheta Number of scan points in zenith direction
 * @param thetaMin Minimum zenith angle (radians)
 * @param thetaMax Maximum zenith angle (radians)
 * @param Nphi Number of scan points in azimuthal direction
 * @param phiMin Minimum azimuthal angle (radians)
 * @param phiMax Maximum azimuthal angle (radians)
 * @param exitDiameter Laser beam exit diameter (meters)
 * @param beamDivergence Beam divergence angle (radians)
 * @return Scan ID for referencing this scan
 */
PYHELIOS_API unsigned int addLiDARScan(LiDARcloud* cloud, const float* origin,
                                       unsigned int Ntheta, float thetaMin, float thetaMax,
                                       unsigned int Nphi, float phiMin, float phiMax,
                                       float exitDiameter, float beamDivergence);

/**
 * @brief Get the number of scans in the cloud
 * @param cloud Pointer to the LiDARcloud instance
 * @return Number of scans
 */
PYHELIOS_API unsigned int getLiDARScanCount(LiDARcloud* cloud);

/**
 * @brief Get the origin of a specific scan
 * @param cloud Pointer to the LiDARcloud instance
 * @param scanID Scan ID
 * @param origin_out Output array for origin [x, y, z]
 */
PYHELIOS_API void getLiDARScanOrigin(LiDARcloud* cloud, unsigned int scanID, float* origin_out);

/**
 * @brief Get the number of zenith scan points for a scan
 * @param cloud Pointer to the LiDARcloud instance
 * @param scanID Scan ID
 * @return Number of theta scan points
 */
PYHELIOS_API unsigned int getLiDARScanSizeTheta(LiDARcloud* cloud, unsigned int scanID);

/**
 * @brief Get the number of azimuthal scan points for a scan
 * @param cloud Pointer to the LiDARcloud instance
 * @param scanID Scan ID
 * @return Number of phi scan points
 */
PYHELIOS_API unsigned int getLiDARScanSizePhi(LiDARcloud* cloud, unsigned int scanID);

//=============================================================================
// Hit Point Operations
//=============================================================================

/**
 * @brief Add a hit point to the cloud
 * @param cloud Pointer to the LiDARcloud instance
 * @param scanID Scan ID this hit belongs to
 * @param xyz Hit point coordinates [x, y, z]
 * @param direction Ray direction [radius, elevation, azimuth] (SphericalCoord)
 */
PYHELIOS_API void addLiDARHitPoint(LiDARcloud* cloud, unsigned int scanID,
                                   const float* xyz, const float* direction);

/**
 * @brief Add a hit point with color to the cloud
 * @param cloud Pointer to the LiDARcloud instance
 * @param scanID Scan ID this hit belongs to
 * @param xyz Hit point coordinates [x, y, z]
 * @param direction Ray direction [radius, elevation, azimuth] (SphericalCoord)
 * @param color RGB color [r, g, b]
 */
PYHELIOS_API void addLiDARHitPointRGB(LiDARcloud* cloud, unsigned int scanID,
                                       const float* xyz, const float* direction,
                                       const float* color);

/**
 * @brief Get total number of hit points in the cloud
 * @param cloud Pointer to the LiDARcloud instance
 * @return Total hit count
 */
PYHELIOS_API unsigned int getLiDARHitCount(LiDARcloud* cloud);

/**
 * @brief Get coordinates of a hit point
 * @param cloud Pointer to the LiDARcloud instance
 * @param index Hit point index
 * @param xyz_out Output array for coordinates [x, y, z]
 */
PYHELIOS_API void getLiDARHitXYZ(LiDARcloud* cloud, unsigned int index, float* xyz_out);

/**
 * @brief Get ray direction of a hit point
 * @param cloud Pointer to the LiDARcloud instance
 * @param index Hit point index
 * @param direction_out Output array [radius, elevation, azimuth]
 */
PYHELIOS_API void getLiDARHitRaydir(LiDARcloud* cloud, unsigned int index, float* direction_out);

/**
 * @brief Get color of a hit point
 * @param cloud Pointer to the LiDARcloud instance
 * @param index Hit point index
 * @param color_out Output array [r, g, b]
 */
PYHELIOS_API void getLiDARHitColor(LiDARcloud* cloud, unsigned int index, float* color_out);

/**
 * @brief Delete a hit point from the cloud
 * @param cloud Pointer to the LiDARcloud instance
 * @param index Hit point index
 */
PYHELIOS_API void deleteLiDARHitPoint(LiDARcloud* cloud, unsigned int index);

//=============================================================================
// Coordinate Transformations
//=============================================================================

/**
 * @brief Translate all hit points by a shift vector
 * @param cloud Pointer to the LiDARcloud instance
 * @param shift Translation vector [x, y, z]
 */
PYHELIOS_API void lidarCoordinateShift(LiDARcloud* cloud, const float* shift);

/**
 * @brief Rotate all hit points by spherical rotation angles
 * @param cloud Pointer to the LiDARcloud instance
 * @param rotation Rotation angles [radius, elevation, azimuth] (SphericalCoord)
 */
PYHELIOS_API void lidarCoordinateRotation(LiDARcloud* cloud, const float* rotation);

//=============================================================================
// Triangulation
//=============================================================================

/**
 * @brief Generate triangle mesh from hit points using Delaunay triangulation
 * @param cloud Pointer to the LiDARcloud instance
 * @param Lmax Maximum triangle edge length
 * @param max_aspect_ratio Maximum triangle aspect ratio
 */
PYHELIOS_API void lidarTriangulateHitPoints(LiDARcloud* cloud, float Lmax, float max_aspect_ratio);

/**
 * @brief Get number of triangles in the mesh
 * @param cloud Pointer to the LiDARcloud instance
 * @return Triangle count
 */
PYHELIOS_API unsigned int getLiDARTriangleCount(LiDARcloud* cloud);

//=============================================================================
// Filters
//=============================================================================

/**
 * @brief Filter hit points by maximum distance from scanner
 * @param cloud Pointer to the LiDARcloud instance
 * @param maxdistance Maximum distance threshold
 */
PYHELIOS_API void lidarDistanceFilter(LiDARcloud* cloud, float maxdistance);

/**
 * @brief Filter hit points by minimum reflectance value
 * @param cloud Pointer to the LiDARcloud instance
 * @param minreflectance Minimum reflectance threshold
 */
PYHELIOS_API void lidarReflectanceFilter(LiDARcloud* cloud, float minreflectance);

/**
 * @brief Keep only first return hit points
 * @param cloud Pointer to the LiDARcloud instance
 */
PYHELIOS_API void lidarFirstHitFilter(LiDARcloud* cloud);

/**
 * @brief Keep only last return hit points
 * @param cloud Pointer to the LiDARcloud instance
 */
PYHELIOS_API void lidarLastHitFilter(LiDARcloud* cloud);

//=============================================================================
// File I/O
//=============================================================================

/**
 * @brief Export point cloud to ASCII file
 * @param cloud Pointer to the LiDARcloud instance
 * @param filename Output file path
 */
PYHELIOS_API void exportLiDARPointCloud(LiDARcloud* cloud, const char* filename);

/**
 * @brief Load scan metadata from XML file
 * @param cloud Pointer to the LiDARcloud instance
 * @param filename XML file path
 */
PYHELIOS_API void loadLiDARXML(LiDARcloud* cloud, const char* filename);

//=============================================================================
// Grid Cell Management
//=============================================================================

/**
 * @brief Add a rectangular grid of voxel cells
 * @param cloud Pointer to the LiDARcloud instance
 * @param center Center position of grid [x, y, z]
 * @param size Grid dimensions [x, y, z]
 * @param ndiv Number of divisions [nx, ny, nz]
 * @param rotation Azimuthal rotation angle (radians)
 */
PYHELIOS_API void addLiDARGrid(LiDARcloud* cloud, const float* center, const float* size,
                               const int* ndiv, float rotation);

/**
 * @brief Add a single grid cell
 * @param cloud Pointer to the LiDARcloud instance
 * @param center Center position of cell [x, y, z]
 * @param size Cell dimensions [x, y, z]
 * @param rotation Azimuthal rotation angle (radians)
 */
PYHELIOS_API void addLiDARGridCell(LiDARcloud* cloud, const float* center, const float* size,
                                   float rotation);

/**
 * @brief Get the number of grid cells
 * @param cloud Pointer to the LiDARcloud instance
 * @return Number of grid cells
 */
PYHELIOS_API unsigned int getLiDARGridCellCount(LiDARcloud* cloud);

/**
 * @brief Get the center position of a grid cell
 * @param cloud Pointer to the LiDARcloud instance
 * @param index Grid cell index
 * @param center_out Output array for center [x, y, z]
 */
PYHELIOS_API void getLiDARCellCenter(LiDARcloud* cloud, unsigned int index, float* center_out);

/**
 * @brief Get the size of a grid cell
 * @param cloud Pointer to the LiDARcloud instance
 * @param index Grid cell index
 * @param size_out Output array for size [x, y, z]
 */
PYHELIOS_API void getLiDARCellSize(LiDARcloud* cloud, unsigned int index, float* size_out);

/**
 * @brief Get the leaf area of a grid cell
 * @param cloud Pointer to the LiDARcloud instance
 * @param index Grid cell index
 * @return Leaf area (m²)
 */
PYHELIOS_API float getLiDARCellLeafArea(LiDARcloud* cloud, unsigned int index);

/**
 * @brief Get the leaf area density of a grid cell
 * @param cloud Pointer to the LiDARcloud instance
 * @param index Grid cell index
 * @return Leaf area density (m²/m³)
 */
PYHELIOS_API float getLiDARCellLeafAreaDensity(LiDARcloud* cloud, unsigned int index);

/**
 * @brief Calculate hit point grid cell assignments
 * @param cloud Pointer to the LiDARcloud instance
 */
PYHELIOS_API void calculateLiDARHitGridCell(LiDARcloud* cloud);

//=============================================================================
// Synthetic Scanning
//=============================================================================

/**
 * @brief Perform synthetic discrete-return LiDAR scan
 * @param cloud Pointer to the LiDARcloud instance
 * @param context Pointer to the Helios context containing geometry
 */
PYHELIOS_API void syntheticLiDARScan(LiDARcloud* cloud, helios::Context* context);

/**
 * @brief Perform synthetic LiDAR scan with control over appending
 * @param cloud Pointer to the LiDARcloud instance
 * @param context Pointer to the Helios context containing geometry
 * @param append If true, append to existing hits; if false, clear existing hits
 */
PYHELIOS_API void syntheticLiDARScanAppend(LiDARcloud* cloud, helios::Context* context, bool append);

/**
 * @brief Perform synthetic full-waveform LiDAR scan
 * @param cloud Pointer to the LiDARcloud instance
 * @param context Pointer to the Helios context containing geometry
 * @param rays_per_pulse Number of rays to cast per pulse (typically 100)
 * @param pulse_distance_threshold Distance threshold for aggregating hits (meters)
 */
PYHELIOS_API void syntheticLiDARScanWaveform(LiDARcloud* cloud, helios::Context* context,
                                             int rays_per_pulse, float pulse_distance_threshold);

/**
 * @brief Perform synthetic full-waveform LiDAR scan with full control
 * @param cloud Pointer to the LiDARcloud instance
 * @param context Pointer to the Helios context containing geometry
 * @param rays_per_pulse Number of rays to cast per pulse
 * @param pulse_distance_threshold Distance threshold for aggregating hits (meters)
 * @param scan_grid_only If true, only scan within defined grid cells
 * @param record_misses If true, record miss/sky points
 * @param append If true, append to existing hits; if false, clear existing hits
 */
PYHELIOS_API void syntheticLiDARScanFull(LiDARcloud* cloud, helios::Context* context,
                                         int rays_per_pulse, float pulse_distance_threshold,
                                         bool scan_grid_only, bool record_misses, bool append);

//=============================================================================
// Advanced Grid Operations
//=============================================================================

/**
 * @brief Get G(theta) value for a grid cell
 * @param cloud Pointer to the LiDARcloud instance
 * @param index Grid cell index
 * @return G(theta) value for the cell
 */
PYHELIOS_API float getLiDARCellGtheta(LiDARcloud* cloud, unsigned int index);

/**
 * @brief Set G(theta) value for a grid cell
 * @param cloud Pointer to the LiDARcloud instance
 * @param Gtheta G(theta) value to set
 * @param index Grid cell index
 */
PYHELIOS_API void setLiDARCellGtheta(LiDARcloud* cloud, float Gtheta, unsigned int index);

//=============================================================================
// Gapfilling Operations
//=============================================================================

/**
 * @brief Gapfill sky/miss points where rays didn't hit geometry
 * @param cloud Pointer to the LiDARcloud instance
 */
PYHELIOS_API void gapfillLiDARMisses(LiDARcloud* cloud);

//=============================================================================
// Leaf Area Calculations
//=============================================================================

/**
 * @brief Calculate leaf area for each grid cell
 * @param cloud Pointer to the LiDARcloud instance
 * @param context Pointer to the Helios context
 */
PYHELIOS_API void calculateLiDARLeafArea(LiDARcloud* cloud, helios::Context* context);

/**
 * @brief Calculate leaf area with minimum voxel hits threshold
 * @param cloud Pointer to the LiDARcloud instance
 * @param context Pointer to the Helios context
 * @param min_voxel_hits Minimum number of hits required per voxel
 */
PYHELIOS_API void calculateLiDARLeafAreaMinHits(LiDARcloud* cloud, helios::Context* context,
                                                 int min_voxel_hits);

/**
 * @brief Calculate synthetic leaf area (for synthetic scan validation)
 * @param cloud Pointer to the LiDARcloud instance
 * @param context Pointer to the Helios context
 */
PYHELIOS_API void calculateSyntheticLiDARLeafArea(LiDARcloud* cloud, helios::Context* context);

/**
 * @brief Calculate synthetic G(theta) (for synthetic scan validation)
 * @param cloud Pointer to the LiDARcloud instance
 * @param context Pointer to the Helios context
 */
PYHELIOS_API void calculateSyntheticLiDARGtheta(LiDARcloud* cloud, helios::Context* context);

//=============================================================================
// Context Integration
//=============================================================================

/**
 * @brief Add triangulated mesh to Context as triangle primitives
 * @param cloud Pointer to the LiDARcloud instance
 * @param context Pointer to the Helios context
 */
PYHELIOS_API void addLiDARTrianglesToContext(LiDARcloud* cloud, helios::Context* context);

/**
 * @brief Initialize CollisionDetection plugin for ray tracing
 * @param cloud Pointer to the LiDARcloud instance
 * @param context Pointer to the Helios context
 */
PYHELIOS_API void initializeLiDARCollisionDetection(LiDARcloud* cloud, helios::Context* context);

/**
 * @brief Enable GPU acceleration for collision detection
 * @param cloud Pointer to the LiDARcloud instance
 */
PYHELIOS_API void enableLiDARCDGPUAcceleration(LiDARcloud* cloud);

/**
 * @brief Disable GPU acceleration for collision detection
 * @param cloud Pointer to the LiDARcloud instance
 */
PYHELIOS_API void disableLiDARCDGPUAcceleration(LiDARcloud* cloud);

//=============================================================================
// Additional Export Functions
//=============================================================================

/**
 * @brief Export triangle normal vectors
 * @param cloud Pointer to the LiDARcloud instance
 * @param filename Output file path
 */
PYHELIOS_API void exportLiDARTriangleNormals(LiDARcloud* cloud, const char* filename);

/**
 * @brief Export triangle areas
 * @param cloud Pointer to the LiDARcloud instance
 * @param filename Output file path
 */
PYHELIOS_API void exportLiDARTriangleAreas(LiDARcloud* cloud, const char* filename);

/**
 * @brief Export leaf areas for each grid cell
 * @param cloud Pointer to the LiDARcloud instance
 * @param filename Output file path
 */
PYHELIOS_API void exportLiDARLeafAreas(LiDARcloud* cloud, const char* filename);

/**
 * @brief Export leaf area densities for each grid cell
 * @param cloud Pointer to the LiDARcloud instance
 * @param filename Output file path
 */
PYHELIOS_API void exportLiDARLeafAreaDensities(LiDARcloud* cloud, const char* filename);

/**
 * @brief Export G(theta) values for each grid cell
 * @param cloud Pointer to the LiDARcloud instance
 * @param filename Output file path
 */
PYHELIOS_API void exportLiDARGtheta(LiDARcloud* cloud, const char* filename);

//=============================================================================
// Message Control
//=============================================================================

/**
 * @brief Disable console output messages
 * @param cloud Pointer to the LiDARcloud instance
 */
PYHELIOS_API void lidarDisableMessages(LiDARcloud* cloud);

/**
 * @brief Enable console output messages
 * @param cloud Pointer to the LiDARcloud instance
 */
PYHELIOS_API void lidarEnableMessages(LiDARcloud* cloud);

#ifdef __cplusplus
}
#endif

#endif // PYHELIOS_WRAPPER_LIDAR_H
