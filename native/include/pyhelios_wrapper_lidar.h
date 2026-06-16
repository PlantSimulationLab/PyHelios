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
 * @param rangeNoiseStdDev Standard deviation of Gaussian range (along-beam) measurement noise in
 *                         meters (0 disables noise). Only affects synthetic-scan generation.
 * @param angleNoiseStdDev Standard deviation of Gaussian angular (beam-pointing) jitter in radians
 *                         (0 disables jitter). Only affects synthetic-scan generation.
 * @param columnFormat Array of column-format label strings (may be nullptr). Non-standard labels
 *                     drive primitive-data sampling onto hits during syntheticScan.
 * @param nCols Number of entries in columnFormat (0 keeps the default empty format)
 * @param scanTiltRoll Global scanner tilt roll angle in radians (0 = perfectly level). Models residual
 *                     spin-axis tilt away from plumb; only affects synthetic-scan generation.
 * @param scanTiltPitch Global scanner tilt pitch angle in radians (0 = perfectly level).
 * @param scanAzimuthOffset Global scanner azimuth (heading) offset in radians, a right-hand rotation
 *                          about the world +z axis applied on top of the azimuth sweep (0 = no offset).
 * @return Scan ID for referencing this scan
 */
PYHELIOS_API unsigned int addLiDARScan(LiDARcloud* cloud, const float* origin,
                                       unsigned int Ntheta, float thetaMin, float thetaMax,
                                       unsigned int Nphi, float phiMin, float phiMax,
                                       float exitDiameter, float beamDivergence,
                                       float rangeNoiseStdDev, float angleNoiseStdDev,
                                       const char** columnFormat, unsigned int nCols,
                                       float scanTiltRoll, float scanTiltPitch, float scanAzimuthOffset);

/**
 * @brief Add a spinning multibeam LiDAR scan (e.g. Velodyne/Ouster/Hesai rotating multi-channel sensor)
 *
 * Each laser channel is fired at a fixed zenith angle (from beamZenithAngles) as the head rotates
 * through uniform azimuth steps. The scan is stored as an (nAngles x Nphi) table so all downstream
 * processing is shared with raster scans.
 * @param cloud Pointer to the LiDARcloud instance
 * @param origin Scanner position as [x, y, z]
 * @param beamZenithAngles Per-channel zenith angles in radians (0 = upward, pi/2 = horizontal, pi = downward)
 * @param nAngles Number of channels (sets Ntheta); must be >= 1
 * @param Nphi Number of azimuth steps (columns) per rotation
 * @param phiMin Minimum azimuthal angle (radians)
 * @param phiMax Maximum azimuthal angle (radians)
 * @param exitDiameter Laser beam exit diameter (meters)
 * @param beamDivergence Beam divergence angle (radians)
 * @param rangeNoiseStdDev Standard deviation of Gaussian range noise in meters (0 disables)
 * @param angleNoiseStdDev Standard deviation of Gaussian angular jitter in radians (0 disables)
 * @param columnFormat Array of column-format label strings (may be nullptr)
 * @param nCols Number of entries in columnFormat
 * @param scanTiltRoll Global scanner tilt roll angle in radians (0 = level)
 * @param scanTiltPitch Global scanner tilt pitch angle in radians (0 = level)
 * @param scanAzimuthOffset Global scanner azimuth (heading) offset in radians, a right-hand rotation
 *                          about the world +z axis applied on top of the azimuth sweep (0 = no offset).
 * @return Scan ID for referencing this scan
 */
PYHELIOS_API unsigned int addLiDARScanMultibeam(LiDARcloud* cloud, const float* origin,
                                                const float* beamZenithAngles, unsigned int nAngles,
                                                unsigned int Nphi, float phiMin, float phiMax,
                                                float exitDiameter, float beamDivergence,
                                                float rangeNoiseStdDev, float angleNoiseStdDev,
                                                const char** columnFormat, unsigned int nCols,
                                                float scanTiltRoll, float scanTiltPitch, float scanAzimuthOffset);

/**
 * @brief Add a moving-platform (mobile/airborne) raster LiDAR scan driven by a 6-DOF pose trajectory
 *
 * The scanner pose changes during the sweep. For each pulse the synthetic-scan generator computes its
 * acquisition time t = t0 + ordinal/pulse_rate_hz, interpolates the platform pose at that time, and emits
 * a per-pulse origin and direction (origin = pos + R(q)*lever_arm). Every resulting hit/miss stores its own
 * origin ("origin_x"/"origin_y"/"origin_z"), timestamp ("timestamp"), and firing index ("pulse_id").
 * The static tilt roll/pitch/azimuth fields are NOT applied in this mode and are forced to zero; attitude
 * comes entirely from the trajectory and the boresight misalignment.
 * @param cloud Pointer to the LiDARcloud instance
 * @param Ntheta Number of scan points in zenith direction (raster grid rows)
 * @param thetaMin Minimum zenith angle (radians)
 * @param thetaMax Maximum zenith angle (radians)
 * @param Nphi Number of scan points in azimuthal direction (raster grid columns)
 * @param phiMin Minimum azimuthal angle (radians)
 * @param phiMax Maximum azimuthal angle (radians)
 * @param exitDiameter Laser beam exit diameter (meters)
 * @param beamDivergence Beam divergence angle (radians)
 * @param rangeNoiseStdDev Standard deviation of Gaussian range noise in meters (0 disables)
 * @param angleNoiseStdDev Standard deviation of Gaussian angular jitter in radians (0 disables)
 * @param columnFormat Array of column-format label strings (may be nullptr)
 * @param nCols Number of entries in columnFormat
 * @param traj_t Monotonically increasing trajectory sample times in seconds (length M)
 * @param traj_pos Platform positions in world coordinates, 3*M floats [x0,y0,z0, x1,y1,z1, ...]
 * @param traj_rot Platform orientations. If rotIsQuaternion != 0: 4*M floats (qx,qy,qz,qw), Hamilton
 *                 body->world. Otherwise: 3*M floats (roll,pitch,yaw) radians, intrinsic Z-Y-X.
 * @param M Number of trajectory samples (must be >= 1; the three traj_* arrays share this length)
 * @param rotIsQuaternion 1 = traj_rot holds quaternions (4*M); 0 = traj_rot holds roll/pitch/yaw Euler (3*M)
 * @param lever_arm Sensor optical center in the platform body frame as [x,y,z] meters (may be nullptr = 0)
 * @param boresight_rpy Fixed sensor rotational misalignment as [roll,pitch,yaw] radians (may be nullptr = 0)
 * @param pulse_rate_hz Pulse repetition rate in Hz (must be > 0)
 * @param t0 Time of the first pulse in seconds (relative time)
 * @return Scan ID for referencing this scan
 */
PYHELIOS_API unsigned int addLiDARScanMoving(LiDARcloud* cloud,
                                             unsigned int Ntheta, float thetaMin, float thetaMax,
                                             unsigned int Nphi, float phiMin, float phiMax,
                                             float exitDiameter, float beamDivergence,
                                             float rangeNoiseStdDev, float angleNoiseStdDev,
                                             const char** columnFormat, unsigned int nCols,
                                             const double* traj_t, const float* traj_pos,
                                             const float* traj_rot, unsigned int M, int rotIsQuaternion,
                                             const float* lever_arm, const float* boresight_rpy,
                                             float pulse_rate_hz, double t0);

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

/**
 * @brief Get the standard deviation of Gaussian range (along-beam) measurement noise for a scan
 * @param cloud Pointer to the LiDARcloud instance
 * @param scanID Scan ID
 * @return Range noise standard deviation in meters (0 if disabled), or 0 on error
 */
PYHELIOS_API float getLiDARScanRangeNoiseStdDev(LiDARcloud* cloud, unsigned int scanID);

/**
 * @brief Get the standard deviation of Gaussian angular (beam-pointing) jitter for a scan
 * @param cloud Pointer to the LiDARcloud instance
 * @param scanID Scan ID
 * @return Angular jitter standard deviation in radians (0 if disabled), or 0 on error
 */
PYHELIOS_API float getLiDARScanAngleNoiseStdDev(LiDARcloud* cloud, unsigned int scanID);

/**
 * @brief Get the global scanner tilt roll angle for a scan
 * @param cloud Pointer to the LiDARcloud instance
 * @param scanID Scan ID
 * @return Tilt roll angle in radians (0 if level), or 0 on error
 */
PYHELIOS_API float getLiDARScanTiltRoll(LiDARcloud* cloud, unsigned int scanID);

/**
 * @brief Get the global scanner tilt pitch angle for a scan
 * @param cloud Pointer to the LiDARcloud instance
 * @param scanID Scan ID
 * @return Tilt pitch angle in radians (0 if level), or 0 on error
 */
PYHELIOS_API float getLiDARScanTiltPitch(LiDARcloud* cloud, unsigned int scanID);

/**
 * @brief Get the global scanner azimuth (heading) offset for a scan
 * @param cloud Pointer to the LiDARcloud instance
 * @param scanID Scan ID
 * @return Azimuth offset (right-hand rotation about the world +z axis) in radians (0 if none), or 0 on error
 */
PYHELIOS_API float getLiDARScanAzimuthOffset(LiDARcloud* cloud, unsigned int scanID);

/**
 * @brief Get the scan pattern for a scan
 * @param cloud Pointer to the LiDARcloud instance
 * @param scanID Scan ID
 * @return 0 = SCAN_PATTERN_RASTER, 1 = SCAN_PATTERN_SPINNING_MULTIBEAM, or -1 on error
 */
PYHELIOS_API int getLiDARScanPattern(LiDARcloud* cloud, unsigned int scanID);

/**
 * @brief Get the number of per-channel beam zenith angles for a scan
 * @param cloud Pointer to the LiDARcloud instance
 * @param scanID Scan ID
 * @return Number of channel angles (0 for a raster scan), or 0 on error
 */
PYHELIOS_API unsigned int getLiDARScanBeamZenithAngleCount(LiDARcloud* cloud, unsigned int scanID);

/**
 * @brief Get the per-channel beam zenith angles for a multibeam scan
 * @param cloud Pointer to the LiDARcloud instance
 * @param scanID Scan ID
 * @param out Caller-allocated array (radians); fills min(count, available) entries
 * @param count Capacity of out
 */
PYHELIOS_API void getLiDARScanBeamZenithAngles(LiDARcloud* cloud, unsigned int scanID,
                                               float* out, unsigned int count);

//=============================================================================
// Miss Detection
//=============================================================================

/**
 * @brief Determine whether a hit is a "miss" (a transmitted beam that returned nothing)
 * @param cloud Pointer to the LiDARcloud instance
 * @param index Hit index
 * @return 1 if the hit is a miss, 0 otherwise (or on error)
 */
PYHELIOS_API int isLiDARHitMiss(LiDARcloud* cloud, unsigned int index);

/**
 * @brief Determine whether the cloud contains any misses
 * @param cloud Pointer to the LiDARcloud instance
 * @return 1 if at least one hit is a miss, 0 otherwise (or on error)
 */
PYHELIOS_API int lidarHasMisses(LiDARcloud* cloud);

/**
 * @brief Get the LIDAR_MISS_DISTANCE constant (distance at which a miss point is placed along its beam)
 * @return LiDARcloud::LIDAR_MISS_DISTANCE in meters
 */
PYHELIOS_API float getLiDARMissDistance();

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
 * @brief Add many hit points to the cloud in a single call (bulk ingestion)
 * @param cloud Pointer to the LiDARcloud instance
 * @param scanID Scan ID these hits belong to
 * @param xyzs Hit point coordinates, count×3 row-major cartesian [x, y, z]
 * @param directions Ray directions, count×3 [radius, elevation, azimuth]
 *                   (azimuth is currently ignored, matching single-point behavior)
 * @param count Number of hit points to add
 * @param colors RGB colors, count×3 [r, g, b], or NULL to add without color
 */
PYHELIOS_API void addLiDARHitPoints(LiDARcloud* cloud, unsigned int scanID,
                                     const float* xyzs, const float* directions,
                                     unsigned int count, const float* colors);

/**
 * @brief Add many hit points carrying a per-hit data map in a single call.
 *
 * Like addLiDARHitPoints, but also populates each HitPoint's data map from
 * named scalar columns — the in-memory equivalent of what loadASCIIFile does
 * for non-standard columns. This is the path multi-return LAD needs: the
 * timestamp/target_index/target_count values land in the map so
 * isMultiReturnData()/gapfillMisses() can group beams by pulse.
 *
 * @param cloud Pointer to the LiDARcloud instance
 * @param scanID Scan ID these hits belong to (the scan must already exist)
 * @param xyzs Hit point coordinates, count×3 row-major cartesian [x, y, z]
 * @param directions Ray directions, count×3 [radius, elevation, azimuth].
 *                   Pass cart2sphere(xyz-origin) to match the ASCII loader;
 *                   the full SphericalCoord (incl. radius) is used.
 * @param count Number of hit points to add
 * @param colors RGB colors, count×3 [r, g, b], or NULL to add without color
 * @param dataLabels nLabels C-strings naming the data-map keys, or NULL
 * @param nLabels Number of data-map columns (0 for no data map)
 * @param dataValues count×nLabels row-major double values, or NULL
 */
PYHELIOS_API void addLiDARHitPointsWithData(LiDARcloud* cloud, unsigned int scanID,
                                            const float* xyzs, const float* directions,
                                            unsigned int count, const float* colors,
                                            const char** dataLabels, unsigned int nLabels,
                                            const double* dataValues);

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
 * @brief Get the (x,y,z) origin from which the beam producing this hit point was emitted
 *
 * For moving-platform scans each hit stores its own per-pulse emission origin; this returns that origin.
 * For static scans (no per-hit origin) it falls back to the single scan origin of the hit's scan.
 * @param cloud Pointer to the LiDARcloud instance
 * @param index Hit point index
 * @param xyz_out Output array for the beam origin [x, y, z]
 */
PYHELIOS_API void getLiDARHitOrigin(LiDARcloud* cloud, unsigned int index, float* xyz_out);

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
 * @brief Get the scan ID a hit point belongs to
 * @param cloud Pointer to the LiDARcloud instance
 * @param index Hit point index
 * @return Scan ID, or -1 on error / out-of-bounds index
 */
PYHELIOS_API int getLiDARHitScanID(LiDARcloud* cloud, unsigned int index);

/**
 * @brief Check whether a named scalar data value exists for a hit point
 * @param cloud Pointer to the LiDARcloud instance
 * @param index Hit point index
 * @param label Data label to query
 * @return 1 if the data exists, 0 otherwise (including out-of-bounds index)
 */
PYHELIOS_API int doesLiDARHitDataExist(LiDARcloud* cloud, unsigned int index, const char* label);

/**
 * @brief Get a named scalar data value for a hit point
 * @param cloud Pointer to the LiDARcloud instance
 * @param index Hit point index
 * @param label Data label to retrieve
 * @return The stored value, or NaN on error / missing label / out-of-bounds index
 */
PYHELIOS_API double getLiDARHitData(LiDARcloud* cloud, unsigned int index, const char* label);

/**
 * @brief Bulk-export a named scalar data value for all hit points in one call
 * @param cloud Pointer to the LiDARcloud instance
 * @param label Data label to retrieve
 * @param out Caller-allocated output array of length n; entries are NaN where the label is absent.
 *            Only the first min(n, hit count) entries are written; if n exceeds the hit count the
 *            trailing entries are left untouched.
 * @param n Capacity of the output array (export is clamped to min(n, hit count))
 */
PYHELIOS_API void getLiDARHitData_all(LiDARcloud* cloud, const char* label, float* out, unsigned int n);

/**
 * @brief Bulk-export XYZ coordinates and RGB colors for all hit points in one call
 * @param cloud Pointer to the LiDARcloud instance
 * @param xyz_out Caller-allocated output array of length 3*n (x,y,z per hit)
 * @param rgb_out Caller-allocated output array of length 3*n (r,g,b per hit)
 * @param n Capacity in hits (export is clamped to min(n, hit count))
 */
PYHELIOS_API void getLiDARHitsXYZRGB_all(LiDARcloud* cloud, float* xyz_out, float* rgb_out, unsigned int n);

/**
 * @brief Bulk-export the scan ID of every hit point in one call
 * @param cloud Pointer to the LiDARcloud instance
 * @param out Caller-allocated int array of length n (scan ID per hit)
 * @param n Capacity in hits (export is clamped to min(n, hit count))
 */
PYHELIOS_API void getLiDARHitScanID_all(LiDARcloud* cloud, int* out, unsigned int n);

/**
 * @brief Bulk-export the miss flag of every hit point in one call
 * @param cloud Pointer to the LiDARcloud instance
 * @param out Caller-allocated int array of length n (1 if the hit is a miss, 0 otherwise)
 * @param n Capacity in hits (export is clamped to min(n, hit count))
 */
PYHELIOS_API void isLiDARHitMiss_all(LiDARcloud* cloud, int* out, unsigned int n);

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

/**
 * @brief Get triangulation filter diagnostics from the most recent
 *        triangulateHitPoints() call.
 *
 * Fills out[0..3] with: candidate count (pre-filter), dropped-by-Lmax,
 * dropped-by-aspect, dropped-by-degenerate. Each dropped triangle is attributed
 * to one primary reason, so out[0] == getLiDARTriangleCount() + out[1] + out[2]
 * + out[3]. All zero if triangulation has not been run.
 * @param cloud Pointer to the LiDARcloud instance
 * @param out   Caller-allocated array of at least 4 unsigned ints
 */
PYHELIOS_API void getLiDARTriangulationStats(LiDARcloud* cloud, unsigned int* out);

/**
 * @brief Bulk-export every triangle's three vertices (and source scan) in one call.
 *
 * Reads getTriangle(i).vertex0/1/2 directly off the LiDARcloud, bypassing the
 * Context round-trip and the per-UUID getPrimitiveVertices loop. out_xyz is
 * filled row-major as [v0x,v0y,v0z, v1x,v1y,v1z, v2x,v2y,v2z] per triangle
 * (triCount×9 floats). out_scan, if non-NULL, receives each triangle's scanID.
 *
 * @param cloud Pointer to the LiDARcloud instance
 * @param out_xyz Output buffer of triCount×9 floats
 * @param out_scan Output buffer of triCount ints, or NULL to skip provenance
 * @param triCount Number of triangles the buffers are sized for
 */
PYHELIOS_API void getLiDARTriangleVertices_all(LiDARcloud* cloud, float* out_xyz,
                                               int* out_scan, unsigned int triCount);

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
 * @param write_header If true, prepend a '#'-prefixed column-name header line (CloudCompare
 *                     convention); the loader skips '#'-prefixed lines so headered files round-trip.
 */
PYHELIOS_API void exportLiDARPointCloud(LiDARcloud* cloud, const char* filename, bool write_header);

/**
 * @brief Export per-voxel leaf-area sampling uncertainty to a self-describing ASCII file
 * @param cloud Pointer to the LiDARcloud instance
 * @param filename Output file path
 */
PYHELIOS_API void exportLiDARLeafAreaUncertainty(LiDARcloud* cloud, const char* filename);

/**
 * @brief Export all scans to an XML metadata file plus one ASCII data file per scan
 * @param cloud Pointer to the LiDARcloud instance
 * @param filename Path of the XML metadata file to write (e.g. "output/scans.xml"). One ASCII data
 *                 file is auto-generated per scan, named by stripping the XML extension and appending
 *                 "_<scanID>.xyz" (e.g. "output/scans_0.xyz"). Re-loadable with loadLiDARXML().
 */
PYHELIOS_API void exportLiDARScans(LiDARcloud* cloud, const char* filename);

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

//=============================================================================
// Leaf-Area Sampling Uncertainty (Pimont et al. 2018)
//=============================================================================

/**
 * @brief Get the beam count N entering a grid cell (from the most recent calculateLeafArea())
 * @return Beam count, or -1 if calculateLeafArea() has not been run for this cell, or on error
 */
PYHELIOS_API int getLiDARCellBeamCount(LiDARcloud* cloud, unsigned int index);

/**
 * @brief Get the relative density index I_rdi for a grid cell
 * @return Relative density index, or 0 on error
 */
PYHELIOS_API float getLiDARCellRelativeDensityIndex(LiDARcloud* cloud, unsigned int index);

/**
 * @brief Get the mean beam path length through a grid cell
 * @return Mean path length (m), or 0 on error
 */
PYHELIOS_API float getLiDARCellMeanPathLength(LiDARcloud* cloud, unsigned int index);

/**
 * @brief Get the per-voxel LAD sampling variance for a grid cell
 * @return LAD variance, or -1 if unavailable / on error
 */
PYHELIOS_API float getLiDARCellLADVariance(LiDARcloud* cloud, unsigned int index);

/**
 * @brief Get the leaf-area confidence interval for a single grid cell
 * @param cloud Pointer to the LiDARcloud instance
 * @param index Grid cell index
 * @param confidence_level Two-sided confidence level (e.g. 0.95)
 * @param out_bounds Caller-allocated array[2] receiving [lower, upper]
 * @return 1 if the interval is valid (passes the Pimont validity envelope), 0 otherwise / on error
 */
PYHELIOS_API int getLiDARCellLeafAreaConfidenceInterval(LiDARcloud* cloud, unsigned int index,
                                                        float confidence_level, float* out_bounds);

/**
 * @brief Get the group-scale LAD confidence interval over a set of grid cells (recommended path)
 * @param cloud Pointer to the LiDARcloud instance
 * @param indices Array of grid cell indices
 * @param nIndices Number of indices
 * @param confidence_level Two-sided confidence level (e.g. 0.95)
 * @param out_results Caller-allocated array[3] receiving [mean_lad, lower, upper]
 * @return 1 if the interval is valid, 0 otherwise / on error
 */
PYHELIOS_API int getLiDARGroupLADConfidenceInterval(LiDARcloud* cloud, const unsigned int* indices,
                                                    unsigned int nIndices, float confidence_level,
                                                    float* out_results);

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
 * @brief Perform discrete-return synthetic scan with miss recording control
 * @param cloud Pointer to the LiDARcloud instance
 * @param context Pointer to the Helios context containing geometry
 * @param scan_grid_only If true, only scan within defined grid cells
 * @param record_misses If true, record miss/sky points (transmitted beams). Required by
 *                      calculateLeafArea(), which counts misses as transmitted beams.
 * @param append If true, append to existing hits; if false, clear existing hits
 */
PYHELIOS_API void syntheticLiDARScanDiscrete(LiDARcloud* cloud, helios::Context* context,
                                             bool scan_grid_only, bool record_misses, bool append);

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
 * @brief Calculate leaf area with per-voxel sampling uncertainty (Pimont et al. 2018)
 * @param cloud Pointer to the LiDARcloud instance
 * @param context Pointer to the Helios context
 * @param min_voxel_hits Minimum number of hits required per voxel
 * @param element_width Characteristic vegetation element width (m) for the element-position-variability
 *                      term; element_width <= 0 leaves a sampling-only variance. Per-voxel uncertainty is
 *                      then available via getLiDARCellLADVariance / getLiDARCell*ConfidenceInterval.
 */
PYHELIOS_API void calculateLiDARLeafAreaUncertainty(LiDARcloud* cloud, helios::Context* context,
                                                    int min_voxel_hits, float element_width);

/**
 * @brief Calculate leaf area using a caller-supplied G(theta), without requiring triangulation
 *
 * Beam-based leaf-area inversion for scans that cannot be triangulated (in particular moving-platform
 * scans). Takes G(theta) directly instead of estimating it from triangulation, so triangulateHitPoints()
 * is NOT required. Uses the per-pulse beam origin recorded on each hit, so it is correct for moving scans.
 * @param cloud Pointer to the LiDARcloud instance
 * @param context Pointer to the Helios context
 * @param Gtheta Mean leaf-projection coefficient G(theta), applied to every voxel; must be in (0,1]
 *               (0.5 = spherical/random leaf-angle distribution)
 * @param min_voxel_hits Minimum number of hits required per voxel
 * @param element_width Characteristic vegetation element width (m); <= 0 reports sampling-only uncertainty
 */
PYHELIOS_API void calculateLiDARLeafAreaGtheta(LiDARcloud* cloud, helios::Context* context,
                                               float Gtheta, int min_voxel_hits, float element_width);

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
