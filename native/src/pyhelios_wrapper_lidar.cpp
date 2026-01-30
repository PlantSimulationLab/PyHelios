// PyHelios C Interface - LiDAR Functions
// Provides LiDAR point cloud processing, synthetic scanning, and triangulation

#include "../include/pyhelios_wrapper_common.h"
#include "../include/pyhelios_wrapper_context.h"
#include "Context.h"
#include <string>
#include <exception>
#include <vector>

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
                                            float exitDiameter, float beamDivergence) {
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

            // Create ScanMetadata with simplified constructor (no columnFormat for now)
            std::vector<std::string> columnFormat;  // Empty column format
            ScanMetadata metadata(scan_origin, Ntheta, thetaMin, thetaMax,
                                  Nphi, phiMin, phiMax, exitDiameter, beamDivergence, columnFormat);

            return cloud->addScan(metadata);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (addLiDARScan): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (addLiDARScan): Unknown error adding LiDAR scan");
            return 0;
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

    PYHELIOS_API void exportLiDARPointCloud(LiDARcloud* cloud, const char* filename) {
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

            cloud->exportPointCloud(filename);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (exportLiDARPointCloud): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (exportLiDARPointCloud): Unknown error");
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
