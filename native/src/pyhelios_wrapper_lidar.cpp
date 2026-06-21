// PyHelios C Interface - LiDAR Functions
// Provides LiDAR point cloud processing, synthetic scanning, and triangulation

#include "../include/pyhelios_wrapper_common.h"
#include "../include/pyhelios_wrapper_context.h"
#include "Context.h"
#include <string>
#include <exception>
#include <vector>
#include <cmath>

#ifdef LIDAR_PLUGIN_AVAILABLE
#include "../include/pyhelios_wrapper_lidar.h"
#include "LiDAR.h"

extern "C" {

    //=============================================================================
    // LiDAR Cloud Lifecycle
    //=============================================================================

    PYHELIOS_API LiDARcloud* createLiDARcloud() {
        try {
            clearError();
            return new LiDARcloud();
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (createLiDARcloud): ") + e.what());
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (createLiDARcloud): Unknown error creating LiDARcloud.");
            return nullptr;
        }
    }

    PYHELIOS_API void destroyLiDARcloud(LiDARcloud* cloud) {
        if (cloud) {
            delete cloud;
        }
    }

    //=============================================================================
    // Scan Management
    //=============================================================================

    PYHELIOS_API unsigned int addLiDARScan(LiDARcloud* cloud, const float* origin,
                                            unsigned int Ntheta, float thetaMin, float thetaMax,
                                            unsigned int Nphi, float phiMin, float phiMax,
                                            float exitDiameter, float beamDivergence,
                                            float rangeNoiseStdDev, float angleNoiseStdDev,
                                            const char** columnFormat, unsigned int nCols,
                                            float scanTiltRoll, float scanTiltPitch, float scanAzimuthOffset) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0;
            }
            if (!origin) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Origin array is null");
                return 0;
            }
            if (Ntheta == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Ntheta must be greater than 0");
                return 0;
            }
            if (Nphi == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Nphi must be greater than 0");
                return 0;
            }

            // Create scan origin
            helios::vec3 scan_origin(origin[0], origin[1], origin[2]);

            // Build column format from caller-supplied labels (empty preserves default behavior).
            // Non-standard labels here drive primitive-data sampling onto hits during syntheticScan.
            std::vector<std::string> column_format;
            if (columnFormat != nullptr && nCols > 0) {
                column_format.reserve(nCols);
                for (unsigned int i = 0; i < nCols; i++) {
                    if (columnFormat[i] != nullptr) {
                        column_format.emplace_back(columnFormat[i]);
                    }
                }
            }
            // rangeNoiseStdDev and angleNoiseStdDev are 0 by default (range noise and beam-pointing
            // jitter disabled); these only affect synthetic-scan generation. scanTiltRoll/scanTiltPitch
            // (radians) model a residual scanner spin-axis tilt away from plumb; 0 0 = perfectly level.
            ScanMetadata metadata(scan_origin, Ntheta, thetaMin, thetaMax,
                                  Nphi, phiMin, phiMax, exitDiameter, beamDivergence,
                                  rangeNoiseStdDev, angleNoiseStdDev, column_format,
                                  scanTiltRoll, scanTiltPitch, scanAzimuthOffset);

            return cloud->addScan(metadata);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (addLiDARScan): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (addLiDARScan): Unknown error adding LiDAR scan");
            return 0;
        }
    }

    PYHELIOS_API unsigned int addLiDARScanMoving(LiDARcloud* cloud,
                                                 unsigned int Ntheta, float thetaMin, float thetaMax,
                                                 unsigned int Nphi, float phiMin, float phiMax,
                                                 float exitDiameter, float beamDivergence,
                                                 float rangeNoiseStdDev, float angleNoiseStdDev,
                                                 const char** columnFormat, unsigned int nCols,
                                                 const double* traj_t, const float* traj_pos,
                                                 const float* traj_rot, unsigned int M, int rotIsQuaternion,
                                                 const float* lever_arm, const float* boresight_rpy,
                                                 float pulse_rate_hz, double t0) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0;
            }
            if (Ntheta == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Ntheta must be greater than 0");
                return 0;
            }
            if (Nphi == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Nphi must be greater than 0");
                return 0;
            }
            if (!traj_t || !traj_pos || !traj_rot || M == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Trajectory arrays must contain at least one sample");
                return 0;
            }
            if (pulse_rate_hz <= 0.f) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "pulse_rate_hz must be greater than 0");
                return 0;
            }

            std::vector<std::string> column_format;
            if (columnFormat != nullptr && nCols > 0) {
                column_format.reserve(nCols);
                for (unsigned int i = 0; i < nCols; i++) {
                    if (columnFormat[i] != nullptr) {
                        column_format.emplace_back(columnFormat[i]);
                    }
                }
            }

            // Origin is ignored for moving scans (the trajectory supplies position); static tilt fields
            // must be zero in this mode (attitude comes entirely from the trajectory + boresight).
            ScanMetadata metadata(helios::make_vec3(0, 0, 0), Ntheta, thetaMin, thetaMax,
                                  Nphi, phiMin, phiMax, exitDiameter, beamDivergence,
                                  rangeNoiseStdDev, angleNoiseStdDev, column_format,
                                  0.f, 0.f, 0.f);

            std::vector<double> t_vec;
            t_vec.reserve(M);
            for (unsigned int i = 0; i < M; i++) {
                t_vec.push_back(traj_t[i]);
            }

            std::vector<helios::vec3> pos_vec;
            pos_vec.reserve(M);
            for (unsigned int i = 0; i < M; i++) {
                pos_vec.push_back(helios::make_vec3(traj_pos[3 * i], traj_pos[3 * i + 1], traj_pos[3 * i + 2]));
            }

            helios::vec3 lever = lever_arm ? helios::make_vec3(lever_arm[0], lever_arm[1], lever_arm[2]) : helios::make_vec3(0, 0, 0);
            helios::vec3 boresight = boresight_rpy ? helios::make_vec3(boresight_rpy[0], boresight_rpy[1], boresight_rpy[2]) : helios::make_vec3(0, 0, 0);

            if (rotIsQuaternion) {
                std::vector<helios::vec4> quat_vec;
                quat_vec.reserve(M);
                for (unsigned int i = 0; i < M; i++) {
                    quat_vec.push_back(helios::make_vec4(traj_rot[4 * i], traj_rot[4 * i + 1], traj_rot[4 * i + 2], traj_rot[4 * i + 3]));
                }
                return cloud->addScanMoving(metadata, t_vec, pos_vec, quat_vec, lever, boresight, pulse_rate_hz, t0);
            } else {
                std::vector<helios::vec3> rpy_vec;
                rpy_vec.reserve(M);
                for (unsigned int i = 0; i < M; i++) {
                    rpy_vec.push_back(helios::make_vec3(traj_rot[3 * i], traj_rot[3 * i + 1], traj_rot[3 * i + 2]));
                }
                return cloud->addScanMoving(metadata, t_vec, pos_vec, rpy_vec, lever, boresight, pulse_rate_hz, t0);
            }

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (addLiDARScanMoving): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (addLiDARScanMoving): Unknown error adding moving-platform scan");
            return 0;
        }
    }

    PYHELIOS_API unsigned int addLiDARScanSpinning(LiDARcloud* cloud,
                                                   const float* beamElevationAngles, unsigned int nAngles,
                                                   float azimuthStep_rad, float pulse_rate_hz,
                                                   float exitDiameter, float beamDivergence,
                                                   float rangeNoiseStdDev, float angleNoiseStdDev,
                                                   const char** columnFormat, unsigned int nCols,
                                                   const double* traj_t, const float* traj_pos,
                                                   const float* traj_rot, unsigned int M, int rotIsQuaternion,
                                                   const float* lever_arm, const float* boresight_rpy,
                                                   double t0) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0;
            }
            if (!beamElevationAngles || nAngles == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "beamElevationAngles must contain at least one per-channel angle");
                return 0;
            }
            if (azimuthStep_rad <= 0.f) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "azimuthStep_rad must be greater than 0");
                return 0;
            }
            if (pulse_rate_hz <= 0.f) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "pulse_rate_hz must be greater than 0");
                return 0;
            }
            if (!traj_t || !traj_pos || !traj_rot || M == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Trajectory arrays must contain at least one sample");
                return 0;
            }

            // beamElevationAngles are ELEVATION angles above the horizon (radians), matching the native
            // addScanSpinning convention (zenith = pi/2 - elevation is applied internally).
            std::vector<float> beam_elev;
            beam_elev.reserve(nAngles);
            for (unsigned int i = 0; i < nAngles; i++) {
                beam_elev.push_back(beamElevationAngles[i]);
            }

            std::vector<std::string> column_format;
            if (columnFormat != nullptr && nCols > 0) {
                column_format.reserve(nCols);
                for (unsigned int i = 0; i < nCols; i++) {
                    if (columnFormat[i] != nullptr) {
                        column_format.emplace_back(columnFormat[i]);
                    }
                }
            }
            // addScanSpinning requires a non-empty column format (defaults to {"x","y","z"} in C++); preserve
            // that default when the caller passes nothing.
            if (column_format.empty()) {
                column_format = {"x", "y", "z"};
            }

            std::vector<double> t_vec;
            t_vec.reserve(M);
            for (unsigned int i = 0; i < M; i++) {
                t_vec.push_back(traj_t[i]);
            }

            std::vector<helios::vec3> pos_vec;
            pos_vec.reserve(M);
            for (unsigned int i = 0; i < M; i++) {
                pos_vec.push_back(helios::make_vec3(traj_pos[3 * i], traj_pos[3 * i + 1], traj_pos[3 * i + 2]));
            }

            helios::vec3 lever = lever_arm ? helios::make_vec3(lever_arm[0], lever_arm[1], lever_arm[2]) : helios::make_vec3(0, 0, 0);
            helios::vec3 boresight = boresight_rpy ? helios::make_vec3(boresight_rpy[0], boresight_rpy[1], boresight_rpy[2]) : helios::make_vec3(0, 0, 0);

            if (rotIsQuaternion) {
                std::vector<helios::vec4> quat_vec;
                quat_vec.reserve(M);
                for (unsigned int i = 0; i < M; i++) {
                    quat_vec.push_back(helios::make_vec4(traj_rot[4 * i], traj_rot[4 * i + 1], traj_rot[4 * i + 2], traj_rot[4 * i + 3]));
                }
                return cloud->addScanSpinning(beam_elev, azimuthStep_rad, pulse_rate_hz, t_vec, pos_vec, quat_vec,
                                              lever, boresight, exitDiameter, beamDivergence, rangeNoiseStdDev,
                                              angleNoiseStdDev, column_format, t0);
            } else {
                std::vector<helios::vec3> rpy_vec;
                rpy_vec.reserve(M);
                for (unsigned int i = 0; i < M; i++) {
                    rpy_vec.push_back(helios::make_vec3(traj_rot[3 * i], traj_rot[3 * i + 1], traj_rot[3 * i + 2]));
                }
                return cloud->addScanSpinning(beam_elev, azimuthStep_rad, pulse_rate_hz, t_vec, pos_vec, rpy_vec,
                                              lever, boresight, exitDiameter, beamDivergence, rangeNoiseStdDev,
                                              angleNoiseStdDev, column_format, t0);
            }

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (addLiDARScanSpinning): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (addLiDARScanSpinning): Unknown error adding spinning scan");
            return 0;
        }
    }

    PYHELIOS_API unsigned int addLiDARScanMovingRaster(LiDARcloud* cloud,
                                                       unsigned int Ntheta, float thetaMin, float thetaMax,
                                                       unsigned int Nphi, float phiMin, float phiMax,
                                                       float pulse_rate_hz,
                                                       float exitDiameter, float beamDivergence,
                                                       float rangeNoiseStdDev, float angleNoiseStdDev,
                                                       const char** columnFormat, unsigned int nCols,
                                                       const double* traj_t, const float* traj_pos,
                                                       const float* traj_quat, unsigned int M,
                                                       const float* lever_arm, const float* boresight_rpy,
                                                       double t0) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0;
            }
            if (Ntheta == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Ntheta must be greater than 0");
                return 0;
            }
            if (Nphi == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Nphi must be greater than 0");
                return 0;
            }
            if (pulse_rate_hz <= 0.f) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "pulse_rate_hz must be greater than 0");
                return 0;
            }
            if (!traj_t || !traj_pos || !traj_quat || M == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Trajectory arrays must contain at least one sample");
                return 0;
            }

            std::vector<std::string> column_format;
            if (columnFormat != nullptr && nCols > 0) {
                column_format.reserve(nCols);
                for (unsigned int i = 0; i < nCols; i++) {
                    if (columnFormat[i] != nullptr) {
                        column_format.emplace_back(columnFormat[i]);
                    }
                }
            }
            if (column_format.empty()) {
                column_format = {"x", "y", "z"};
            }

            std::vector<double> t_vec;
            t_vec.reserve(M);
            for (unsigned int i = 0; i < M; i++) {
                t_vec.push_back(traj_t[i]);
            }

            std::vector<helios::vec3> pos_vec;
            pos_vec.reserve(M);
            for (unsigned int i = 0; i < M; i++) {
                pos_vec.push_back(helios::make_vec3(traj_pos[3 * i], traj_pos[3 * i + 1], traj_pos[3 * i + 2]));
            }

            std::vector<helios::vec4> quat_vec;
            quat_vec.reserve(M);
            for (unsigned int i = 0; i < M; i++) {
                quat_vec.push_back(helios::make_vec4(traj_quat[4 * i], traj_quat[4 * i + 1], traj_quat[4 * i + 2], traj_quat[4 * i + 3]));
            }

            helios::vec3 lever = lever_arm ? helios::make_vec3(lever_arm[0], lever_arm[1], lever_arm[2]) : helios::make_vec3(0, 0, 0);
            helios::vec3 boresight = boresight_rpy ? helios::make_vec3(boresight_rpy[0], boresight_rpy[1], boresight_rpy[2]) : helios::make_vec3(0, 0, 0);

            return cloud->addScanMovingRaster(Ntheta, thetaMin, thetaMax, Nphi, phiMin, phiMax, pulse_rate_hz,
                                              t_vec, pos_vec, quat_vec, lever, boresight, exitDiameter,
                                              beamDivergence, rangeNoiseStdDev, angleNoiseStdDev, column_format, t0);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (addLiDARScanMovingRaster): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (addLiDARScanMovingRaster): Unknown error adding moving-raster scan");
            return 0;
        }
    }

    //=============================================================================
    // Scan Acquisition-Mode Introspection
    //=============================================================================

    PYHELIOS_API int getLiDARScanMode(LiDARcloud* cloud, unsigned int scanID) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return -1;
            }
            // 0 = SCAN_MODE_STATIC_RASTER, 1 = SCAN_MODE_MOVING_RASTER, 2 = SCAN_MODE_SPINNING.
            return static_cast<int>(cloud->getScanMode(scanID));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARScanMode): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARScanMode): Unknown error");
            return -1;
        }
    }

    PYHELIOS_API unsigned int getLiDARScanStepsPerRev(LiDARcloud* cloud, unsigned int scanID) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0;
            }
            return cloud->getScanStepsPerRev(scanID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARScanStepsPerRev): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARScanStepsPerRev): Unknown error");
            return 0;
        }
    }

    PYHELIOS_API double getLiDARScanRotationRate(LiDARcloud* cloud, unsigned int scanID) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0.0;
            }
            return cloud->getScanRotationRate(scanID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARScanRotationRate): ") + e.what());
            return 0.0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARScanRotationRate): Unknown error");
            return 0.0;
        }
    }

    PYHELIOS_API double getLiDARScanRevolutions(LiDARcloud* cloud, unsigned int scanID) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0.0;
            }
            return cloud->getScanRevolutions(scanID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARScanRevolutions): ") + e.what());
            return 0.0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARScanRevolutions): Unknown error");
            return 0.0;
        }
    }

    //=============================================================================
    // Return-Mode Configuration
    //=============================================================================

    PYHELIOS_API int getLiDARScanReturnMode(LiDARcloud* cloud, unsigned int scanID) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return -1;
            }
            // 0 = RETURN_MODE_MULTI, 1 = RETURN_MODE_SINGLE.
            return static_cast<int>(cloud->getScanReturnMode(scanID));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARScanReturnMode): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARScanReturnMode): Unknown error");
            return -1;
        }
    }

    PYHELIOS_API void setLiDARScanReturnMode(LiDARcloud* cloud, unsigned int scanID, int returnMode) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (returnMode != 0 && returnMode != 1) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "returnMode must be 0 (multi) or 1 (single)");
                return;
            }
            cloud->setScanReturnMode(scanID, static_cast<ReturnMode>(returnMode));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setLiDARScanReturnMode): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setLiDARScanReturnMode): Unknown error");
        }
    }

    PYHELIOS_API int getLiDARScanSingleReturnSelection(LiDARcloud* cloud, unsigned int scanID) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return -1;
            }
            // 0 = STRONGEST, 1 = FIRST, 2 = LAST.
            return static_cast<int>(cloud->getScanSingleReturnSelection(scanID));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARScanSingleReturnSelection): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARScanSingleReturnSelection): Unknown error");
            return -1;
        }
    }

    PYHELIOS_API void setLiDARScanSingleReturnSelection(LiDARcloud* cloud, unsigned int scanID, int selection) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (selection < 0 || selection > 3) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "selection must be 0 (strongest), 1 (first), 2 (last), or 3 (strongest+last)");
                return;
            }
            cloud->setScanSingleReturnSelection(scanID, static_cast<SingleReturnSelection>(selection));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setLiDARScanSingleReturnSelection): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setLiDARScanSingleReturnSelection): Unknown error");
        }
    }

    PYHELIOS_API int getLiDARScanMaxReturns(LiDARcloud* cloud, unsigned int scanID) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0;
            }
            return cloud->getScanMaxReturns(scanID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARScanMaxReturns): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARScanMaxReturns): Unknown error");
            return 0;
        }
    }

    PYHELIOS_API void setLiDARScanMaxReturns(LiDARcloud* cloud, unsigned int scanID, int maxReturns) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (maxReturns < 1) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "maxReturns must be >= 1");
                return;
            }
            cloud->setScanMaxReturns(scanID, maxReturns);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setLiDARScanMaxReturns): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setLiDARScanMaxReturns): Unknown error");
        }
    }

    PYHELIOS_API float getLiDARScanPulseWidth(LiDARcloud* cloud, unsigned int scanID) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0.0f;
            }
            return cloud->getScanPulseWidth(scanID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARScanPulseWidth): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARScanPulseWidth): Unknown error");
            return 0.0f;
        }
    }

    PYHELIOS_API void setLiDARScanPulseWidth(LiDARcloud* cloud, unsigned int scanID, float pulseWidth) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            cloud->setScanPulseWidth(scanID, pulseWidth);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setLiDARScanPulseWidth): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setLiDARScanPulseWidth): Unknown error");
        }
    }

    PYHELIOS_API float getLiDARScanDetectionThreshold(LiDARcloud* cloud, unsigned int scanID) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0.0f;
            }
            return cloud->getScanDetectionThreshold(scanID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARScanDetectionThreshold): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARScanDetectionThreshold): Unknown error");
            return 0.0f;
        }
    }

    PYHELIOS_API void setLiDARScanDetectionThreshold(LiDARcloud* cloud, unsigned int scanID, float detectionThreshold) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            cloud->setScanDetectionThreshold(scanID, detectionThreshold);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setLiDARScanDetectionThreshold): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setLiDARScanDetectionThreshold): Unknown error");
        }
    }

    PYHELIOS_API unsigned int getLiDARScanCount(LiDARcloud* cloud) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0;
            }
            return cloud->getScanCount();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARScanCount): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARScanCount): Unknown error");
            return 0;
        }
    }

    PYHELIOS_API void getLiDARScanOrigin(LiDARcloud* cloud, unsigned int scanID, float* origin_out) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!origin_out) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output origin array is null");
                return;
            }

            helios::vec3 origin = cloud->getScanOrigin(scanID);
            origin_out[0] = origin.x;
            origin_out[1] = origin.y;
            origin_out[2] = origin.z;

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARScanOrigin): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARScanOrigin): Unknown error");
        }
    }

    PYHELIOS_API unsigned int getLiDARScanSizeTheta(LiDARcloud* cloud, unsigned int scanID) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0;
            }
            return cloud->getScanSizeTheta(scanID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARScanSizeTheta): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARScanSizeTheta): Unknown error");
            return 0;
        }
    }

    PYHELIOS_API float getLiDARScanRangeNoiseStdDev(LiDARcloud* cloud, unsigned int scanID) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0.0f;
            }
            return cloud->getScanRangeNoiseStdDev(scanID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARScanRangeNoiseStdDev): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARScanRangeNoiseStdDev): Unknown error");
            return 0.0f;
        }
    }

    PYHELIOS_API float getLiDARScanAngleNoiseStdDev(LiDARcloud* cloud, unsigned int scanID) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0.0f;
            }
            return cloud->getScanAngleNoiseStdDev(scanID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARScanAngleNoiseStdDev): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARScanAngleNoiseStdDev): Unknown error");
            return 0.0f;
        }
    }

    PYHELIOS_API float getLiDARScanTiltRoll(LiDARcloud* cloud, unsigned int scanID) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0.0f;
            }
            return cloud->getScanTiltRoll(scanID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARScanTiltRoll): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARScanTiltRoll): Unknown error");
            return 0.0f;
        }
    }

    PYHELIOS_API float getLiDARScanTiltPitch(LiDARcloud* cloud, unsigned int scanID) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0.0f;
            }
            return cloud->getScanTiltPitch(scanID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARScanTiltPitch): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARScanTiltPitch): Unknown error");
            return 0.0f;
        }
    }

    PYHELIOS_API float getLiDARScanAzimuthOffset(LiDARcloud* cloud, unsigned int scanID) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0.0f;
            }
            return cloud->getScanAzimuthOffset(scanID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARScanAzimuthOffset): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARScanAzimuthOffset): Unknown error");
            return 0.0f;
        }
    }

    PYHELIOS_API int getLiDARScanPattern(LiDARcloud* cloud, unsigned int scanID) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return -1;
            }
            // Returns 0 for SCAN_PATTERN_RASTER, 1 for SCAN_PATTERN_SPINNING_MULTIBEAM.
            return static_cast<int>(cloud->getScanPattern(scanID));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARScanPattern): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARScanPattern): Unknown error");
            return -1;
        }
    }

    PYHELIOS_API unsigned int getLiDARScanBeamZenithAngleCount(LiDARcloud* cloud, unsigned int scanID) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0;
            }
            return static_cast<unsigned int>(cloud->getScanBeamZenithAngles(scanID).size());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARScanBeamZenithAngleCount): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARScanBeamZenithAngleCount): Unknown error");
            return 0;
        }
    }

    PYHELIOS_API void getLiDARScanBeamZenithAngles(LiDARcloud* cloud, unsigned int scanID,
                                                   float* out, unsigned int count) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!out) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "output array is null");
                return;
            }
            std::vector<float> angles = cloud->getScanBeamZenithAngles(scanID);
            unsigned int n = std::min(count, static_cast<unsigned int>(angles.size()));
            for (unsigned int i = 0; i < n; i++) {
                out[i] = angles[i];
            }
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARScanBeamZenithAngles): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARScanBeamZenithAngles): Unknown error");
        }
    }

    PYHELIOS_API unsigned int getLiDARScanSizePhi(LiDARcloud* cloud, unsigned int scanID) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0;
            }
            return cloud->getScanSizePhi(scanID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARScanSizePhi): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARScanSizePhi): Unknown error");
            return 0;
        }
    }

    //=============================================================================
    // Hit Point Operations
    //=============================================================================

    PYHELIOS_API void addLiDARHitPoint(LiDARcloud* cloud, unsigned int scanID,
                                        const float* xyz, const float* direction) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!xyz) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "XYZ array is null");
                return;
            }
            if (!direction) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Direction array is null");
                return;
            }

            helios::vec3 position(xyz[0], xyz[1], xyz[2]);
            // Direction is SphericalCoord: [radius, elevation, azimuth]
            helios::SphericalCoord ray_direction = helios::make_SphericalCoord(direction[0], direction[1]);

            cloud->addHitPoint(scanID, position, ray_direction);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (addLiDARHitPoint): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (addLiDARHitPoint): Unknown error");
        }
    }

    PYHELIOS_API void addLiDARHitPointRGB(LiDARcloud* cloud, unsigned int scanID,
                                           const float* xyz, const float* direction,
                                           const float* color) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!xyz) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "XYZ array is null");
                return;
            }
            if (!direction) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Direction array is null");
                return;
            }
            if (!color) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Color array is null");
                return;
            }

            helios::vec3 position(xyz[0], xyz[1], xyz[2]);
            helios::SphericalCoord ray_direction = helios::make_SphericalCoord(direction[0], direction[1]);
            helios::RGBcolor rgb(color[0], color[1], color[2]);

            cloud->addHitPoint(scanID, position, ray_direction, rgb);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (addLiDARHitPointRGB): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (addLiDARHitPointRGB): Unknown error");
        }
    }

    PYHELIOS_API void addLiDARHitPoints(LiDARcloud* cloud, unsigned int scanID,
                                         const float* xyzs, const float* directions,
                                         unsigned int count, const float* colors) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!xyzs) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "XYZ array is null");
                return;
            }
            if (!directions) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Direction array is null");
                return;
            }

            for (unsigned int i = 0; i < count; i++) {
                helios::vec3 position(xyzs[3 * i], xyzs[3 * i + 1], xyzs[3 * i + 2]);
                // Direction is SphericalCoord: [radius, elevation, azimuth]
                helios::SphericalCoord ray_direction = helios::make_SphericalCoord(directions[3 * i], directions[3 * i + 1]);

                if (colors == nullptr) {
                    cloud->addHitPoint(scanID, position, ray_direction);
                } else {
                    helios::RGBcolor rgb(colors[3 * i], colors[3 * i + 1], colors[3 * i + 2]);
                    cloud->addHitPoint(scanID, position, ray_direction, rgb);
                }
            }

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (addLiDARHitPoints): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (addLiDARHitPoints): Unknown error");
        }
    }

    PYHELIOS_API void addLiDARHitPointsWithData(LiDARcloud* cloud, unsigned int scanID,
                                                const float* xyzs, const float* directions,
                                                unsigned int count, const float* colors,
                                                const char** dataLabels, unsigned int nLabels,
                                                const double* dataValues) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!xyzs) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "XYZ array is null");
                return;
            }
            if (!directions) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Direction array is null");
                return;
            }
            if (nLabels > 0 && (dataLabels == nullptr || dataValues == nullptr)) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER,
                         "Data labels/values are null with nLabels > 0");
                return;
            }

            // Cache the label strings once rather than re-wrapping per hit.
            std::vector<std::string> labels;
            labels.reserve(nLabels);
            for (unsigned int j = 0; j < nLabels; j++) {
                labels.emplace_back(dataLabels[j] != nullptr ? dataLabels[j] : "");
            }

            for (unsigned int i = 0; i < count; i++) {
                helios::vec3 position(xyzs[3 * i], xyzs[3 * i + 1], xyzs[3 * i + 2]);
                // Full SphericalCoord (radius, elevation, azimuth) — radius is the
                // beam path length Beer's law needs, so keep it (the no-data
                // addLiDARHitPoints drops it via the 2-arg make_SphericalCoord).
                helios::SphericalCoord ray_direction = helios::make_SphericalCoord(
                    directions[3 * i], directions[3 * i + 1], directions[3 * i + 2]);

                std::map<std::string, double> data;
                for (unsigned int j = 0; j < nLabels; j++) {
                    data[labels[j]] = dataValues[(size_t)i * nLabels + j];
                }

                if (colors == nullptr) {
                    cloud->addHitPoint(scanID, position, ray_direction, data);
                } else {
                    helios::RGBcolor rgb(colors[3 * i], colors[3 * i + 1], colors[3 * i + 2]);
                    cloud->addHitPoint(scanID, position, ray_direction, rgb, data);
                }
            }

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (addLiDARHitPointsWithData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (addLiDARHitPointsWithData): Unknown error");
        }
    }

    PYHELIOS_API unsigned int getLiDARHitCount(LiDARcloud* cloud) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0;
            }
            return cloud->getHitCount();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARHitCount): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARHitCount): Unknown error");
            return 0;
        }
    }

    PYHELIOS_API void getLiDARHitXYZ(LiDARcloud* cloud, unsigned int index, float* xyz_out) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!xyz_out) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output XYZ array is null");
                return;
            }

            helios::vec3 position = cloud->getHitXYZ(index);
            xyz_out[0] = position.x;
            xyz_out[1] = position.y;
            xyz_out[2] = position.z;

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARHitXYZ): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARHitXYZ): Unknown error");
        }
    }

    PYHELIOS_API void getLiDARHitOrigin(LiDARcloud* cloud, unsigned int index, float* xyz_out) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!xyz_out) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output XYZ array is null");
                return;
            }

            helios::vec3 origin = cloud->getHitOrigin(index);
            xyz_out[0] = origin.x;
            xyz_out[1] = origin.y;
            xyz_out[2] = origin.z;

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARHitOrigin): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARHitOrigin): Unknown error");
        }
    }

    PYHELIOS_API void getLiDARHitRaydir(LiDARcloud* cloud, unsigned int index, float* direction_out) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!direction_out) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output direction array is null");
                return;
            }

            helios::SphericalCoord direction = cloud->getHitRaydir(index);
            direction_out[0] = direction.radius;
            direction_out[1] = direction.elevation;
            direction_out[2] = direction.azimuth;

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARHitRaydir): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARHitRaydir): Unknown error");
        }
    }

    PYHELIOS_API void getLiDARHitColor(LiDARcloud* cloud, unsigned int index, float* color_out) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!color_out) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output color array is null");
                return;
            }

            helios::RGBcolor color = cloud->getHitColor(index);
            color_out[0] = color.r;
            color_out[1] = color.g;
            color_out[2] = color.b;

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARHitColor): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARHitColor): Unknown error");
        }
    }

    PYHELIOS_API int getLiDARHitScanID(LiDARcloud* cloud, unsigned int index) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return -1;
            }
            if (index >= cloud->getHitCount()) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Hit point index out of bounds");
                return -1;
            }
            return cloud->getHitScanID(index);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARHitScanID): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARHitScanID): Unknown error");
            return -1;
        }
    }

    PYHELIOS_API int doesLiDARHitDataExist(LiDARcloud* cloud, unsigned int index, const char* label) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Hit data label is null");
                return 0;
            }
            // doesHitDataExist is safe: returns false on out-of-bounds index.
            return cloud->doesHitDataExist(index, label) ? 1 : 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (doesLiDARHitDataExist): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (doesLiDARHitDataExist): Unknown error");
            return 0;
        }
    }

    PYHELIOS_API double getLiDARHitData(LiDARcloud* cloud, unsigned int index, const char* label) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return std::nan("");
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Hit data label is null");
                return std::nan("");
            }
            // Guard with doesHitDataExist first: getHitData throws on missing label/OOB index,
            // and a C++ exception must never cross the FFI boundary.
            if (!cloud->doesHitDataExist(index, label)) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER,
                         std::string("Hit data ``") + label + "'' does not exist for the given hit index");
                return std::nan("");
            }
            return cloud->getHitData(index, label);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARHitData): ") + e.what());
            return std::nan("");
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARHitData): Unknown error");
            return std::nan("");
        }
    }

    PYHELIOS_API void getLiDARHitData_all(LiDARcloud* cloud, const char* label, float* out, unsigned int n) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Hit data label is null");
                return;
            }
            if (!out) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output array is null");
                return;
            }
            unsigned int count = cloud->getHitCount();
            unsigned int limit = (n < count) ? n : count;
            for (unsigned int i = 0; i < limit; i++) {
                out[i] = cloud->doesHitDataExist(i, label) ? float(cloud->getHitData(i, label)) : std::nanf("");
            }
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARHitData_all): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARHitData_all): Unknown error");
        }
    }

    PYHELIOS_API void getLiDARHitDataColumn(LiDARcloud* cloud, const char* label, double* out,
                                            unsigned int n, double absent_value) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Hit data label is null");
                return;
            }
            if (!out) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output array is null");
                return;
            }
            // Native columnar bulk read: a single cache-linear pass. getHitDataColumn fills `column` with one
            // value per hit (absent_value where the label is absent), or all-absent if the column was never
            // registered. Copy into the caller's buffer clamped to min(n, hit count).
            std::vector<double> column;
            cloud->getHitDataColumn(label, column, absent_value);
            unsigned int limit = (n < column.size()) ? n : static_cast<unsigned int>(column.size());
            for (unsigned int i = 0; i < limit; i++) {
                out[i] = column[i];
            }
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARHitDataColumn): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARHitDataColumn): Unknown error");
        }
    }

    PYHELIOS_API void getLiDARHitsXYZRGB_all(LiDARcloud* cloud, float* xyz_out, float* rgb_out, unsigned int n) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!xyz_out) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output XYZ array is null");
                return;
            }
            if (!rgb_out) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output RGB array is null");
                return;
            }
            unsigned int count = cloud->getHitCount();
            unsigned int limit = (n < count) ? n : count;
            for (unsigned int i = 0; i < limit; i++) {
                helios::vec3 position = cloud->getHitXYZ(i);
                xyz_out[3 * i + 0] = position.x;
                xyz_out[3 * i + 1] = position.y;
                xyz_out[3 * i + 2] = position.z;
                helios::RGBcolor color = cloud->getHitColor(i);
                rgb_out[3 * i + 0] = color.r;
                rgb_out[3 * i + 1] = color.g;
                rgb_out[3 * i + 2] = color.b;
            }
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARHitsXYZRGB_all): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARHitsXYZRGB_all): Unknown error");
        }
    }

    PYHELIOS_API void getLiDARHitScanID_all(LiDARcloud* cloud, int* out, unsigned int n) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!out) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output array is null");
                return;
            }
            unsigned int count = cloud->getHitCount();
            unsigned int limit = (n < count) ? n : count;
            for (unsigned int i = 0; i < limit; i++) {
                out[i] = cloud->getHitScanID(i);
            }
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARHitScanID_all): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARHitScanID_all): Unknown error");
        }
    }

    PYHELIOS_API void isLiDARHitMiss_all(LiDARcloud* cloud, int* out, unsigned int n) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!out) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output array is null");
                return;
            }
            unsigned int count = cloud->getHitCount();
            unsigned int limit = (n < count) ? n : count;
            for (unsigned int i = 0; i < limit; i++) {
                out[i] = cloud->isHitMiss(i) ? 1 : 0;
            }
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (isLiDARHitMiss_all): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (isLiDARHitMiss_all): Unknown error");
        }
    }

    PYHELIOS_API void deleteLiDARHitPoint(LiDARcloud* cloud, unsigned int index) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            cloud->deleteHitPoint(index);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (deleteLiDARHitPoint): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (deleteLiDARHitPoint): Unknown error");
        }
    }

    //=============================================================================
    // Coordinate Transformations
    //=============================================================================

    PYHELIOS_API void lidarCoordinateShift(LiDARcloud* cloud, const float* shift) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!shift) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Shift array is null");
                return;
            }

            helios::vec3 shift_vec(shift[0], shift[1], shift[2]);
            cloud->coordinateShift(shift_vec);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (lidarCoordinateShift): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (lidarCoordinateShift): Unknown error");
        }
    }

    PYHELIOS_API void lidarCoordinateRotation(LiDARcloud* cloud, const float* rotation) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!rotation) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Rotation array is null");
                return;
            }

            helios::SphericalCoord rotation_angles = helios::make_SphericalCoord(rotation[0], rotation[1]);
            cloud->coordinateRotation(rotation_angles);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (lidarCoordinateRotation): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (lidarCoordinateRotation): Unknown error");
        }
    }

    //=============================================================================
    // Triangulation
    //=============================================================================

    PYHELIOS_API void lidarTriangulateHitPoints(LiDARcloud* cloud, float Lmax, float max_aspect_ratio) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (Lmax <= 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Lmax must be greater than 0");
                return;
            }
            if (max_aspect_ratio <= 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "max_aspect_ratio must be greater than 0");
                return;
            }

            cloud->triangulateHitPoints(Lmax, max_aspect_ratio);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (lidarTriangulateHitPoints): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (lidarTriangulateHitPoints): Unknown error");
        }
    }

    PYHELIOS_API unsigned int getLiDARTriangleCount(LiDARcloud* cloud) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0;
            }
            return cloud->getTriangleCount();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARTriangleCount): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARTriangleCount): Unknown error");
            return 0;
        }
    }

    PYHELIOS_API void getLiDARTriangulationStats(LiDARcloud* cloud, unsigned int* out) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!out) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "output pointer is null");
                return;
            }
            out[0] = static_cast<unsigned int>(cloud->getTriangulationCandidateCount());
            out[1] = static_cast<unsigned int>(cloud->getTriangulationDroppedByLmax());
            out[2] = static_cast<unsigned int>(cloud->getTriangulationDroppedByAspect());
            out[3] = static_cast<unsigned int>(cloud->getTriangulationDroppedByDegenerate());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARTriangulationStats): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARTriangulationStats): Unknown error");
        }
    }

    PYHELIOS_API void getLiDARTriangleVertices_all(LiDARcloud* cloud, float* out_xyz,
                                                   int* out_scan, unsigned int triCount) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!out_xyz) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output XYZ array is null");
                return;
            }
            unsigned int n = cloud->getTriangleCount();
            unsigned int limit = (triCount < n) ? triCount : n;
            for (unsigned int i = 0; i < limit; i++) {
                Triangulation t = cloud->getTriangle(i);
                float* p = out_xyz + (size_t)9 * i;
                p[0] = t.vertex0.x; p[1] = t.vertex0.y; p[2] = t.vertex0.z;
                p[3] = t.vertex1.x; p[4] = t.vertex1.y; p[5] = t.vertex1.z;
                p[6] = t.vertex2.x; p[7] = t.vertex2.y; p[8] = t.vertex2.z;
                if (out_scan) {
                    out_scan[i] = t.scanID;
                }
            }
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARTriangleVertices_all): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARTriangleVertices_all): Unknown error");
        }
    }

    PYHELIOS_API void lidarSetExternalTriangulation(LiDARcloud* cloud, const float* xyz,
                                                    const int* scanIDs, unsigned int triCount) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (triCount > 0 && !xyz) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Triangle vertex array is null");
                return;
            }
            if (triCount > 0 && !scanIDs) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "scanIDs array is null (per-scan provenance is required)");
                return;
            }

            std::vector<helios::vec3> verts;
            verts.reserve((size_t)3 * triCount);
            for (unsigned int i = 0; i < triCount; i++) {
                const float* p = xyz + (size_t)9 * i;
                verts.push_back(helios::make_vec3(p[0], p[1], p[2]));
                verts.push_back(helios::make_vec3(p[3], p[4], p[5]));
                verts.push_back(helios::make_vec3(p[6], p[7], p[8]));
            }

            std::vector<int> scans(scanIDs, scanIDs + triCount);

            cloud->setExternalTriangulation(verts, scans);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (lidarSetExternalTriangulation): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (lidarSetExternalTriangulation): Unknown error");
        }
    }

    //=============================================================================
    // Filters
    //=============================================================================

    PYHELIOS_API void lidarDistanceFilter(LiDARcloud* cloud, float maxdistance) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (maxdistance <= 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "maxdistance must be greater than 0");
                return;
            }

            cloud->distanceFilter(maxdistance);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (lidarDistanceFilter): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (lidarDistanceFilter): Unknown error");
        }
    }

    PYHELIOS_API void lidarReflectanceFilter(LiDARcloud* cloud, float minreflectance) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }

            cloud->reflectanceFilter(minreflectance);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (lidarReflectanceFilter): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (lidarReflectanceFilter): Unknown error");
        }
    }

    PYHELIOS_API void lidarFirstHitFilter(LiDARcloud* cloud) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }

            cloud->firstHitFilter();

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (lidarFirstHitFilter): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (lidarFirstHitFilter): Unknown error");
        }
    }

    PYHELIOS_API void lidarLastHitFilter(LiDARcloud* cloud) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }

            cloud->lastHitFilter();

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (lidarLastHitFilter): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (lidarLastHitFilter): Unknown error");
        }
    }

    //=============================================================================
    // File I/O
    //=============================================================================

    PYHELIOS_API void exportLiDARPointCloud(LiDARcloud* cloud, const char* filename, bool write_header) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null");
                return;
            }

            // write_header=true prepends a '#'-prefixed column-name header line (CloudCompare convention);
            // the loader skips '#'-prefixed lines so headered files round-trip through loadXML().
            cloud->exportPointCloud(filename, write_header);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (exportLiDARPointCloud): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (exportLiDARPointCloud): Unknown error");
        }
    }

    PYHELIOS_API void exportLiDARLeafAreaUncertainty(LiDARcloud* cloud, const char* filename) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null");
                return;
            }
            cloud->exportLeafAreaUncertainty(filename);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (exportLiDARLeafAreaUncertainty): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (exportLiDARLeafAreaUncertainty): Unknown error");
        }
    }

    PYHELIOS_API void exportLiDARScans(LiDARcloud* cloud, const char* filename) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null");
                return;
            }

            cloud->exportScans(filename);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (exportLiDARScans): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (exportLiDARScans): Unknown error");
        }
    }

    PYHELIOS_API void loadLiDARXML(LiDARcloud* cloud, const char* filename) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null");
                return;
            }

            cloud->loadXML(filename);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (loadLiDARXML): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (loadLiDARXML): Unknown error");
        }
    }

    //=============================================================================
    // Grid Cell Management
    //=============================================================================

    PYHELIOS_API void addLiDARGrid(LiDARcloud* cloud, const float* center, const float* size,
                                    const int* ndiv, float rotation) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!center || !size || !ndiv) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Input arrays are null");
                return;
            }

            helios::vec3 grid_center(center[0], center[1], center[2]);
            helios::vec3 grid_size(size[0], size[1], size[2]);
            helios::int3 grid_ndiv = helios::make_int3(ndiv[0], ndiv[1], ndiv[2]);

            cloud->addGrid(grid_center, grid_size, grid_ndiv, rotation);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (addLiDARGrid): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (addLiDARGrid): Unknown error");
        }
    }

    PYHELIOS_API void addLiDARGridCell(LiDARcloud* cloud, const float* center, const float* size,
                                        float rotation) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!center || !size) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Input arrays are null");
                return;
            }

            helios::vec3 cell_center(center[0], center[1], center[2]);
            helios::vec3 cell_size(size[0], size[1], size[2]);

            cloud->addGridCell(cell_center, cell_size, rotation);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (addLiDARGridCell): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (addLiDARGridCell): Unknown error");
        }
    }

    PYHELIOS_API unsigned int getLiDARGridCellCount(LiDARcloud* cloud) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0;
            }
            return cloud->getGridCellCount();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARGridCellCount): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARGridCellCount): Unknown error");
            return 0;
        }
    }

    PYHELIOS_API void getLiDARCellCenter(LiDARcloud* cloud, unsigned int index, float* center_out) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!center_out) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output center array is null");
                return;
            }

            helios::vec3 center = cloud->getCellCenter(index);
            center_out[0] = center.x;
            center_out[1] = center.y;
            center_out[2] = center.z;

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARCellCenter): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARCellCenter): Unknown error");
        }
    }

    PYHELIOS_API void getLiDARCellSize(LiDARcloud* cloud, unsigned int index, float* size_out) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!size_out) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output size array is null");
                return;
            }

            helios::vec3 size = cloud->getCellSize(index);
            size_out[0] = size.x;
            size_out[1] = size.y;
            size_out[2] = size.z;

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARCellSize): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARCellSize): Unknown error");
        }
    }

    PYHELIOS_API float getLiDARCellLeafArea(LiDARcloud* cloud, unsigned int index) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0.0f;
            }
            return cloud->getCellLeafArea(index);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARCellLeafArea): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARCellLeafArea): Unknown error");
            return 0.0f;
        }
    }

    PYHELIOS_API float getLiDARCellLeafAreaDensity(LiDARcloud* cloud, unsigned int index) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0.0f;
            }
            return cloud->getCellLeafAreaDensity(index);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARCellLeafAreaDensity): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARCellLeafAreaDensity): Unknown error");
            return 0.0f;
        }
    }

    PYHELIOS_API int getLiDARCellBeamCount(LiDARcloud* cloud, unsigned int index) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return -1;
            }
            // -1 if calculateLeafArea() has not been run for this cell.
            return cloud->getCellBeamCount(index);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARCellBeamCount): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARCellBeamCount): Unknown error");
            return -1;
        }
    }

    PYHELIOS_API float getLiDARCellRelativeDensityIndex(LiDARcloud* cloud, unsigned int index) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0.0f;
            }
            return cloud->getCellRelativeDensityIndex(index);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARCellRelativeDensityIndex): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARCellRelativeDensityIndex): Unknown error");
            return 0.0f;
        }
    }

    PYHELIOS_API float getLiDARCellMeanPathLength(LiDARcloud* cloud, unsigned int index) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0.0f;
            }
            return cloud->getCellMeanPathLength(index);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARCellMeanPathLength): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARCellMeanPathLength): Unknown error");
            return 0.0f;
        }
    }

    PYHELIOS_API float getLiDARCellLADVariance(LiDARcloud* cloud, unsigned int index) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return -1.0f;
            }
            // -1 if calculateLeafArea() has not been run for this cell.
            return cloud->getCellLADVariance(index);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARCellLADVariance): ") + e.what());
            return -1.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARCellLADVariance): Unknown error");
            return -1.0f;
        }
    }

    PYHELIOS_API int getLiDARCellLeafAreaConfidenceInterval(LiDARcloud* cloud, unsigned int index,
                                                            float confidence_level, float* out_bounds) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0;
            }
            if (!out_bounds) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "output bounds array is null");
                return 0;
            }
            float lower = 0.0f, upper = 0.0f;
            // Returns false (0) when the interval is gated out by the Pimont validity envelope.
            bool valid = cloud->getCellLeafAreaConfidenceInterval(index, confidence_level, lower, upper);
            out_bounds[0] = lower;
            out_bounds[1] = upper;
            return valid ? 1 : 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARCellLeafAreaConfidenceInterval): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARCellLeafAreaConfidenceInterval): Unknown error");
            return 0;
        }
    }

    PYHELIOS_API int getLiDARGroupLADConfidenceInterval(LiDARcloud* cloud, const unsigned int* indices,
                                                        unsigned int nIndices, float confidence_level,
                                                        float* out_results) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0;
            }
            if (!indices || nIndices == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "indices must contain at least one cell index");
                return 0;
            }
            if (!out_results) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "output results array is null");
                return 0;
            }
            std::vector<uint> idx_vec(indices, indices + nIndices);
            float mean_lad = 0.0f, lower = 0.0f, upper = 0.0f;
            bool valid = cloud->getGroupLADConfidenceInterval(idx_vec, confidence_level, mean_lad, lower, upper);
            out_results[0] = mean_lad;
            out_results[1] = lower;
            out_results[2] = upper;
            return valid ? 1 : 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARGroupLADConfidenceInterval): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARGroupLADConfidenceInterval): Unknown error");
            return 0;
        }
    }

    PYHELIOS_API void calculateLiDARHitGridCell(LiDARcloud* cloud) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            cloud->calculateHitGridCell();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (calculateLiDARHitGridCell): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (calculateLiDARHitGridCell): Unknown error");
        }
    }

    //=============================================================================
    // Synthetic Scanning
    //=============================================================================

    PYHELIOS_API void syntheticLiDARScan(LiDARcloud* cloud, helios::Context* context) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }

            cloud->syntheticScan(context);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (syntheticLiDARScan): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (syntheticLiDARScan): Unknown error");
        }
    }

    PYHELIOS_API void syntheticLiDARScanAppend(LiDARcloud* cloud, helios::Context* context, bool append) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }

            cloud->syntheticScan(context, append);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (syntheticLiDARScanAppend): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (syntheticLiDARScanAppend): Unknown error");
        }
    }

    PYHELIOS_API void setLiDARCancelFlag(LiDARcloud* cloud, volatile int* flag) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            cloud->setCancelFlag(flag);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setLiDARCancelFlag): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setLiDARCancelFlag): Unknown error");
        }
    }

    PYHELIOS_API void syntheticLiDARScanDiscrete(LiDARcloud* cloud, helios::Context* context,
                                                 bool scan_grid_only, bool record_misses, bool append) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            // Discrete-return scan with explicit miss recording. record_misses=true records the
            // transmitted beams (misses) required by calculateLeafArea()'s inversion.
            cloud->syntheticScan(context, scan_grid_only, record_misses, append);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (syntheticLiDARScanDiscrete): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (syntheticLiDARScanDiscrete): Unknown error");
        }
    }

    PYHELIOS_API void syntheticLiDARScanWaveform(LiDARcloud* cloud, helios::Context* context,
                                                  int rays_per_pulse, float pulse_distance_threshold) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (rays_per_pulse <= 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "rays_per_pulse must be greater than 0");
                return;
            }
            if (pulse_distance_threshold <= 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "pulse_distance_threshold must be greater than 0");
                return;
            }

            cloud->syntheticScan(context, rays_per_pulse, pulse_distance_threshold);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (syntheticLiDARScanWaveform): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (syntheticLiDARScanWaveform): Unknown error");
        }
    }

    PYHELIOS_API void syntheticLiDARScanFull(LiDARcloud* cloud, helios::Context* context,
                                              int rays_per_pulse, float pulse_distance_threshold,
                                              bool scan_grid_only, bool record_misses, bool append) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (rays_per_pulse <= 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "rays_per_pulse must be greater than 0");
                return;
            }
            if (pulse_distance_threshold <= 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "pulse_distance_threshold must be greater than 0");
                return;
            }

            cloud->syntheticScan(context, rays_per_pulse, pulse_distance_threshold,
                               scan_grid_only, record_misses, append);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (syntheticLiDARScanFull): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (syntheticLiDARScanFull): Unknown error");
        }
    }

    PYHELIOS_API void syntheticLiDARScanReturnMode(LiDARcloud* cloud, helios::Context* context,
                                                   int rays_per_pulse, float pulse_distance_threshold,
                                                   int return_mode, bool scan_grid_only,
                                                   bool record_misses, bool append) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (rays_per_pulse <= 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "rays_per_pulse must be greater than 0");
                return;
            }
            if (pulse_distance_threshold <= 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "pulse_distance_threshold must be greater than 0");
                return;
            }
            if (return_mode != 0 && return_mode != 1) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "return_mode must be 0 (multi) or 1 (single)");
                return;
            }
            // The explicit return-mode overload overrides each scan's stored returnMode for this call only.
            cloud->syntheticScan(context, rays_per_pulse, pulse_distance_threshold,
                                 static_cast<ReturnMode>(return_mode), scan_grid_only, record_misses, append);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (syntheticLiDARScanReturnMode): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (syntheticLiDARScanReturnMode): Unknown error");
        }
    }

    //=============================================================================
    // Advanced Grid Operations
    //=============================================================================

    PYHELIOS_API float getLiDARCellGtheta(LiDARcloud* cloud, unsigned int index) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0.0f;
            }
            return cloud->getCellGtheta(index);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getLiDARCellGtheta): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getLiDARCellGtheta): Unknown error");
            return 0.0f;
        }
    }

    PYHELIOS_API void setLiDARCellGtheta(LiDARcloud* cloud, float Gtheta, unsigned int index) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            cloud->setCellGtheta(Gtheta, index);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setLiDARCellGtheta): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setLiDARCellGtheta): Unknown error");
        }
    }

    //=============================================================================
    // Gapfilling Operations
    //=============================================================================

    PYHELIOS_API void gapfillLiDARMisses(LiDARcloud* cloud) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            cloud->gapfillMisses();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (gapfillLiDARMisses): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (gapfillLiDARMisses): Unknown error");
        }
    }

    PYHELIOS_API int isLiDARHitMiss(LiDARcloud* cloud, unsigned int index) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0;
            }
            // A "miss" is a fired pulse that returned nothing (transmitted beam); these form the
            // denominator of the per-voxel transmission probability used by calculateLeafArea().
            return cloud->isHitMiss(index) ? 1 : 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (isLiDARHitMiss): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (isLiDARHitMiss): Unknown error");
            return 0;
        }
    }

    PYHELIOS_API int lidarHasMisses(LiDARcloud* cloud) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return 0;
            }
            return cloud->hasMisses() ? 1 : 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (lidarHasMisses): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (lidarHasMisses): Unknown error");
            return 0;
        }
    }

    PYHELIOS_API float getLiDARMissDistance() {
        // The distance at which a miss point is placed along its beam (LiDARcloud::LIDAR_MISS_DISTANCE).
        return LiDARcloud::LIDAR_MISS_DISTANCE;
    }

    //=============================================================================
    // Leaf Area Calculations
    //=============================================================================

    PYHELIOS_API void calculateLiDARLeafArea(LiDARcloud* cloud, helios::Context* context) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            cloud->calculateLeafArea(context);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (calculateLiDARLeafArea): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (calculateLiDARLeafArea): Unknown error");
        }
    }

    PYHELIOS_API void calculateLiDARLeafAreaMinHits(LiDARcloud* cloud, helios::Context* context,
                                                      int min_voxel_hits) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            cloud->calculateLeafArea(context, min_voxel_hits);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (calculateLiDARLeafAreaMinHits): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (calculateLiDARLeafAreaMinHits): Unknown error");
        }
    }

    PYHELIOS_API void calculateLiDARLeafAreaUncertainty(LiDARcloud* cloud, helios::Context* context,
                                                        int min_voxel_hits, float element_width) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            // element_width (m) is the characteristic vegetation element size used for the
            // element-position-variability term of the per-voxel LAD sampling variance
            // (Pimont et al. 2018). element_width <= 0 leaves a sampling-only variance.
            cloud->calculateLeafArea(context, min_voxel_hits, element_width);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (calculateLiDARLeafAreaUncertainty): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (calculateLiDARLeafAreaUncertainty): Unknown error");
        }
    }

    PYHELIOS_API void calculateLiDARLeafAreaGtheta(LiDARcloud* cloud, helios::Context* context,
                                                   float Gtheta, int min_voxel_hits, float element_width) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            // Beam-based inversion with a caller-supplied G(theta); does not require triangulation, so it
            // works for moving-platform scans whose pulses cannot be Delaunay-triangulated. Gtheta must be
            // in (0,1] (0.5 = spherical leaf-angle distribution).
            cloud->calculateLeafArea(context, Gtheta, min_voxel_hits, element_width);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (calculateLiDARLeafAreaGtheta): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (calculateLiDARLeafAreaGtheta): Unknown error");
        }
    }

    PYHELIOS_API void calculateSyntheticLiDARLeafArea(LiDARcloud* cloud, helios::Context* context) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            cloud->calculateSyntheticLeafArea(context);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (calculateSyntheticLiDARLeafArea): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (calculateSyntheticLiDARLeafArea): Unknown error");
        }
    }

    PYHELIOS_API void calculateSyntheticLiDARGtheta(LiDARcloud* cloud, helios::Context* context) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            cloud->calculateSyntheticGtheta(context);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (calculateSyntheticLiDARGtheta): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (calculateSyntheticLiDARGtheta): Unknown error");
        }
    }

    //=============================================================================
    // Context Integration
    //=============================================================================

    PYHELIOS_API void addLiDARTrianglesToContext(LiDARcloud* cloud, helios::Context* context) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            cloud->addTrianglesToContext(context);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (addLiDARTrianglesToContext): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (addLiDARTrianglesToContext): Unknown error");
        }
    }

    PYHELIOS_API void initializeLiDARCollisionDetection(LiDARcloud* cloud, helios::Context* context) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            cloud->initializeCollisionDetection(context);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (initializeLiDARCollisionDetection): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (initializeLiDARCollisionDetection): Unknown error");
        }
    }

    PYHELIOS_API void enableLiDARCDGPUAcceleration(LiDARcloud* cloud) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            cloud->enableGPUAcceleration();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (enableLiDARCDGPUAcceleration): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (enableLiDARCDGPUAcceleration): Unknown error");
        }
    }

    PYHELIOS_API void disableLiDARCDGPUAcceleration(LiDARcloud* cloud) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            cloud->disableGPUAcceleration();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (disableLiDARCDGPUAcceleration): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (disableLiDARCDGPUAcceleration): Unknown error");
        }
    }

    //=============================================================================
    // Additional Export Functions
    //=============================================================================

    PYHELIOS_API void exportLiDARTriangleNormals(LiDARcloud* cloud, const char* filename) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null");
                return;
            }
            cloud->exportTriangleNormals(filename);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (exportLiDARTriangleNormals): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (exportLiDARTriangleNormals): Unknown error");
        }
    }

    PYHELIOS_API void exportLiDARTriangleAreas(LiDARcloud* cloud, const char* filename) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null");
                return;
            }
            cloud->exportTriangleAreas(filename);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (exportLiDARTriangleAreas): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (exportLiDARTriangleAreas): Unknown error");
        }
    }

    PYHELIOS_API void exportLiDARLeafAreas(LiDARcloud* cloud, const char* filename) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null");
                return;
            }
            cloud->exportLeafAreas(filename);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (exportLiDARLeafAreas): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (exportLiDARLeafAreas): Unknown error");
        }
    }

    PYHELIOS_API void exportLiDARLeafAreaDensities(LiDARcloud* cloud, const char* filename) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null");
                return;
            }
            cloud->exportLeafAreaDensities(filename);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (exportLiDARLeafAreaDensities): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (exportLiDARLeafAreaDensities): Unknown error");
        }
    }

    PYHELIOS_API void exportLiDARGtheta(LiDARcloud* cloud, const char* filename) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null");
                return;
            }
            cloud->exportGtheta(filename);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (exportLiDARGtheta): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (exportLiDARGtheta): Unknown error");
        }
    }

    //=============================================================================
    // Message Control
    //=============================================================================

    PYHELIOS_API void lidarDisableMessages(LiDARcloud* cloud) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }

            cloud->disableMessages();

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (lidarDisableMessages): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (lidarDisableMessages): Unknown error");
        }
    }

    PYHELIOS_API void lidarEnableMessages(LiDARcloud* cloud) {
        try {
            clearError();
            if (!cloud) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LiDAR cloud pointer is null");
                return;
            }

            cloud->enableMessages();

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (lidarEnableMessages): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (lidarEnableMessages): Unknown error");
        }
    }

} // extern "C"

#endif // LIDAR_PLUGIN_AVAILABLE
