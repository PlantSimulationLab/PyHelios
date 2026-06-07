"""
ULiDARWrapper - ctypes wrapper for LiDAR plugin

Provides low-level ctypes interface to LiDAR C++ plugin for point cloud processing,
synthetic scanning, triangulation, and leaf area calculations.
"""

import ctypes
from typing import List, Tuple, Optional
from .UContextWrapper import UContext
from ..plugins import helios_lib
from ..exceptions import check_helios_error


# Opaque structure for LiDARcloud
class ULiDARcloud(ctypes.Structure):
    """Opaque structure for LiDARcloud C++ class"""
    pass


# Error checking callback
def _check_error(result, func, args):
    """Automatic error checking for all LiDAR functions"""
    check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage)
    return result


# Function prototypes with availability detection
try:
    # Cloud lifecycle
    helios_lib.createLiDARcloud.argtypes = []
    helios_lib.createLiDARcloud.restype = ctypes.POINTER(ULiDARcloud)
    helios_lib.createLiDARcloud.errcheck = _check_error

    helios_lib.destroyLiDARcloud.argtypes = [ctypes.POINTER(ULiDARcloud)]
    helios_lib.destroyLiDARcloud.restype = None

    # Scan management
    helios_lib.addLiDARScan.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(ctypes.c_float),  # origin[3]
        ctypes.c_uint,  # Ntheta
        ctypes.c_float,  # thetaMin
        ctypes.c_float,  # thetaMax
        ctypes.c_uint,  # Nphi
        ctypes.c_float,  # phiMin
        ctypes.c_float,  # phiMax
        ctypes.c_float,  # exitDiameter
        ctypes.c_float,  # beamDivergence
        ctypes.c_float,  # rangeNoiseStdDev
        ctypes.c_float,  # angleNoiseStdDev
        ctypes.POINTER(ctypes.c_char_p),  # columnFormat
        ctypes.c_uint    # nCols
    ]
    helios_lib.addLiDARScan.restype = ctypes.c_uint
    helios_lib.addLiDARScan.errcheck = _check_error

    helios_lib.getLiDARScanCount.argtypes = [ctypes.POINTER(ULiDARcloud)]
    helios_lib.getLiDARScanCount.restype = ctypes.c_uint
    helios_lib.getLiDARScanCount.errcheck = _check_error

    helios_lib.getLiDARScanOrigin.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_float)
    ]
    helios_lib.getLiDARScanOrigin.restype = None
    helios_lib.getLiDARScanOrigin.errcheck = _check_error

    helios_lib.getLiDARScanSizeTheta.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARScanSizeTheta.restype = ctypes.c_uint
    helios_lib.getLiDARScanSizeTheta.errcheck = _check_error

    helios_lib.getLiDARScanSizePhi.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARScanSizePhi.restype = ctypes.c_uint
    helios_lib.getLiDARScanSizePhi.errcheck = _check_error

    helios_lib.getLiDARScanRangeNoiseStdDev.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARScanRangeNoiseStdDev.restype = ctypes.c_float
    helios_lib.getLiDARScanRangeNoiseStdDev.errcheck = _check_error

    helios_lib.getLiDARScanAngleNoiseStdDev.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARScanAngleNoiseStdDev.restype = ctypes.c_float
    helios_lib.getLiDARScanAngleNoiseStdDev.errcheck = _check_error

    # Hit point operations
    helios_lib.addLiDARHitPoint.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float)
    ]
    helios_lib.addLiDARHitPoint.restype = None
    helios_lib.addLiDARHitPoint.errcheck = _check_error

    helios_lib.addLiDARHitPointRGB.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float)
    ]
    helios_lib.addLiDARHitPointRGB.restype = None
    helios_lib.addLiDARHitPointRGB.errcheck = _check_error

    helios_lib.addLiDARHitPoints.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_float),  # xyzs[count*3]
        ctypes.POINTER(ctypes.c_float),  # directions[count*3]
        ctypes.c_uint,                   # count
        ctypes.POINTER(ctypes.c_float)   # colors[count*3] or NULL
    ]
    helios_lib.addLiDARHitPoints.restype = None
    helios_lib.addLiDARHitPoints.errcheck = _check_error

    helios_lib.getLiDARHitCount.argtypes = [ctypes.POINTER(ULiDARcloud)]
    helios_lib.getLiDARHitCount.restype = ctypes.c_uint
    helios_lib.getLiDARHitCount.errcheck = _check_error

    helios_lib.getLiDARHitXYZ.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_float)
    ]
    helios_lib.getLiDARHitXYZ.restype = None
    helios_lib.getLiDARHitXYZ.errcheck = _check_error

    helios_lib.getLiDARHitRaydir.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_float)
    ]
    helios_lib.getLiDARHitRaydir.restype = None
    helios_lib.getLiDARHitRaydir.errcheck = _check_error

    helios_lib.getLiDARHitColor.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_float)
    ]
    helios_lib.getLiDARHitColor.restype = None
    helios_lib.getLiDARHitColor.errcheck = _check_error

    helios_lib.getLiDARHitScanID.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARHitScanID.restype = ctypes.c_int
    helios_lib.getLiDARHitScanID.errcheck = _check_error

    helios_lib.doesLiDARHitDataExist.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.c_uint,
        ctypes.c_char_p
    ]
    helios_lib.doesLiDARHitDataExist.restype = ctypes.c_int
    helios_lib.doesLiDARHitDataExist.errcheck = _check_error

    helios_lib.getLiDARHitData.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.c_uint,
        ctypes.c_char_p
    ]
    helios_lib.getLiDARHitData.restype = ctypes.c_double
    helios_lib.getLiDARHitData.errcheck = _check_error

    helios_lib.getLiDARHitData_all.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_uint
    ]
    helios_lib.getLiDARHitData_all.restype = None
    helios_lib.getLiDARHitData_all.errcheck = _check_error

    helios_lib.getLiDARHitsXYZRGB_all.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_uint
    ]
    helios_lib.getLiDARHitsXYZRGB_all.restype = None
    helios_lib.getLiDARHitsXYZRGB_all.errcheck = _check_error

    helios_lib.deleteLiDARHitPoint.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.deleteLiDARHitPoint.restype = None
    helios_lib.deleteLiDARHitPoint.errcheck = _check_error

    # Transformations
    helios_lib.lidarCoordinateShift.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(ctypes.c_float)
    ]
    helios_lib.lidarCoordinateShift.restype = None
    helios_lib.lidarCoordinateShift.errcheck = _check_error

    helios_lib.lidarCoordinateRotation.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(ctypes.c_float)
    ]
    helios_lib.lidarCoordinateRotation.restype = None
    helios_lib.lidarCoordinateRotation.errcheck = _check_error

    # Triangulation
    helios_lib.lidarTriangulateHitPoints.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.c_float,
        ctypes.c_float
    ]
    helios_lib.lidarTriangulateHitPoints.restype = None
    helios_lib.lidarTriangulateHitPoints.errcheck = _check_error

    helios_lib.getLiDARTriangleCount.argtypes = [ctypes.POINTER(ULiDARcloud)]
    helios_lib.getLiDARTriangleCount.restype = ctypes.c_uint
    helios_lib.getLiDARTriangleCount.errcheck = _check_error

    # Filters
    helios_lib.lidarDistanceFilter.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_float]
    helios_lib.lidarDistanceFilter.restype = None
    helios_lib.lidarDistanceFilter.errcheck = _check_error

    helios_lib.lidarReflectanceFilter.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_float]
    helios_lib.lidarReflectanceFilter.restype = None
    helios_lib.lidarReflectanceFilter.errcheck = _check_error

    helios_lib.lidarFirstHitFilter.argtypes = [ctypes.POINTER(ULiDARcloud)]
    helios_lib.lidarFirstHitFilter.restype = None
    helios_lib.lidarFirstHitFilter.errcheck = _check_error

    helios_lib.lidarLastHitFilter.argtypes = [ctypes.POINTER(ULiDARcloud)]
    helios_lib.lidarLastHitFilter.restype = None
    helios_lib.lidarLastHitFilter.errcheck = _check_error

    # File I/O
    helios_lib.exportLiDARPointCloud.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_char_p]
    helios_lib.exportLiDARPointCloud.restype = None
    helios_lib.exportLiDARPointCloud.errcheck = _check_error

    helios_lib.exportLiDARScans.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_char_p]
    helios_lib.exportLiDARScans.restype = None
    helios_lib.exportLiDARScans.errcheck = _check_error

    helios_lib.loadLiDARXML.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_char_p]
    helios_lib.loadLiDARXML.restype = None
    helios_lib.loadLiDARXML.errcheck = _check_error

    # Message control
    helios_lib.lidarDisableMessages.argtypes = [ctypes.POINTER(ULiDARcloud)]
    helios_lib.lidarDisableMessages.restype = None
    helios_lib.lidarDisableMessages.errcheck = _check_error

    helios_lib.lidarEnableMessages.argtypes = [ctypes.POINTER(ULiDARcloud)]
    helios_lib.lidarEnableMessages.restype = None
    helios_lib.lidarEnableMessages.errcheck = _check_error

    # Grid cell management
    helios_lib.addLiDARGrid.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_float
    ]
    helios_lib.addLiDARGrid.restype = None
    helios_lib.addLiDARGrid.errcheck = _check_error

    helios_lib.addLiDARGridCell.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_float
    ]
    helios_lib.addLiDARGridCell.restype = None
    helios_lib.addLiDARGridCell.errcheck = _check_error

    helios_lib.getLiDARGridCellCount.argtypes = [ctypes.POINTER(ULiDARcloud)]
    helios_lib.getLiDARGridCellCount.restype = ctypes.c_uint
    helios_lib.getLiDARGridCellCount.errcheck = _check_error

    helios_lib.getLiDARCellCenter.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_float)
    ]
    helios_lib.getLiDARCellCenter.restype = None
    helios_lib.getLiDARCellCenter.errcheck = _check_error

    helios_lib.getLiDARCellSize.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_float)
    ]
    helios_lib.getLiDARCellSize.restype = None
    helios_lib.getLiDARCellSize.errcheck = _check_error

    helios_lib.getLiDARCellLeafArea.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARCellLeafArea.restype = ctypes.c_float
    helios_lib.getLiDARCellLeafArea.errcheck = _check_error

    helios_lib.getLiDARCellLeafAreaDensity.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARCellLeafAreaDensity.restype = ctypes.c_float
    helios_lib.getLiDARCellLeafAreaDensity.errcheck = _check_error

    helios_lib.calculateLiDARHitGridCell.argtypes = [ctypes.POINTER(ULiDARcloud)]
    helios_lib.calculateLiDARHitGridCell.restype = None
    helios_lib.calculateLiDARHitGridCell.errcheck = _check_error

    # Synthetic scanning
    helios_lib.syntheticLiDARScan.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(UContext)
    ]
    helios_lib.syntheticLiDARScan.restype = None
    helios_lib.syntheticLiDARScan.errcheck = _check_error

    helios_lib.syntheticLiDARScanAppend.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(UContext),
        ctypes.c_bool
    ]
    helios_lib.syntheticLiDARScanAppend.restype = None
    helios_lib.syntheticLiDARScanAppend.errcheck = _check_error

    helios_lib.syntheticLiDARScanWaveform.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(UContext),
        ctypes.c_int,
        ctypes.c_float
    ]
    helios_lib.syntheticLiDARScanWaveform.restype = None
    helios_lib.syntheticLiDARScanWaveform.errcheck = _check_error

    helios_lib.syntheticLiDARScanFull.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(UContext),
        ctypes.c_int,
        ctypes.c_float,
        ctypes.c_bool,
        ctypes.c_bool,
        ctypes.c_bool
    ]
    helios_lib.syntheticLiDARScanFull.restype = None
    helios_lib.syntheticLiDARScanFull.errcheck = _check_error

    # Leaf area calculations
    helios_lib.calculateLiDARLeafArea.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(UContext)
    ]
    helios_lib.calculateLiDARLeafArea.restype = None
    helios_lib.calculateLiDARLeafArea.errcheck = _check_error

    helios_lib.calculateLiDARLeafAreaMinHits.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(UContext),
        ctypes.c_int
    ]
    helios_lib.calculateLiDARLeafAreaMinHits.restype = None
    helios_lib.calculateLiDARLeafAreaMinHits.errcheck = _check_error

    helios_lib.calculateSyntheticLiDARLeafArea.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(UContext)
    ]
    helios_lib.calculateSyntheticLiDARLeafArea.restype = None
    helios_lib.calculateSyntheticLiDARLeafArea.errcheck = _check_error

    helios_lib.calculateSyntheticLiDARGtheta.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(UContext)
    ]
    helios_lib.calculateSyntheticLiDARGtheta.restype = None
    helios_lib.calculateSyntheticLiDARGtheta.errcheck = _check_error

    helios_lib.getLiDARCellGtheta.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARCellGtheta.restype = ctypes.c_float
    helios_lib.getLiDARCellGtheta.errcheck = _check_error

    helios_lib.setLiDARCellGtheta.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_float, ctypes.c_uint]
    helios_lib.setLiDARCellGtheta.restype = None
    helios_lib.setLiDARCellGtheta.errcheck = _check_error

    helios_lib.gapfillLiDARMisses.argtypes = [ctypes.POINTER(ULiDARcloud)]
    helios_lib.gapfillLiDARMisses.restype = None
    helios_lib.gapfillLiDARMisses.errcheck = _check_error

    helios_lib.exportLiDARGtheta.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_char_p]
    helios_lib.exportLiDARGtheta.restype = None
    helios_lib.exportLiDARGtheta.errcheck = _check_error

    # Additional export functions
    helios_lib.exportLiDARTriangleNormals.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_char_p]
    helios_lib.exportLiDARTriangleNormals.restype = None
    helios_lib.exportLiDARTriangleNormals.errcheck = _check_error

    helios_lib.exportLiDARTriangleAreas.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_char_p]
    helios_lib.exportLiDARTriangleAreas.restype = None
    helios_lib.exportLiDARTriangleAreas.errcheck = _check_error

    helios_lib.exportLiDARLeafAreas.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_char_p]
    helios_lib.exportLiDARLeafAreas.restype = None
    helios_lib.exportLiDARLeafAreas.errcheck = _check_error

    helios_lib.exportLiDARLeafAreaDensities.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_char_p]
    helios_lib.exportLiDARLeafAreaDensities.restype = None
    helios_lib.exportLiDARLeafAreaDensities.errcheck = _check_error

    helios_lib.exportLiDARGtheta.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_char_p]
    helios_lib.exportLiDARGtheta.restype = None
    helios_lib.exportLiDARGtheta.errcheck = _check_error

    # Context integration
    helios_lib.addLiDARTrianglesToContext.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(UContext)
    ]
    helios_lib.addLiDARTrianglesToContext.restype = None
    helios_lib.addLiDARTrianglesToContext.errcheck = _check_error

    helios_lib.initializeLiDARCollisionDetection.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(UContext)
    ]
    helios_lib.initializeLiDARCollisionDetection.restype = None
    helios_lib.initializeLiDARCollisionDetection.errcheck = _check_error

    helios_lib.enableLiDARCDGPUAcceleration.argtypes = [ctypes.POINTER(ULiDARcloud)]
    helios_lib.enableLiDARCDGPUAcceleration.restype = None
    helios_lib.enableLiDARCDGPUAcceleration.errcheck = _check_error

    helios_lib.disableLiDARCDGPUAcceleration.argtypes = [ctypes.POINTER(ULiDARcloud)]
    helios_lib.disableLiDARCDGPUAcceleration.restype = None
    helios_lib.disableLiDARCDGPUAcceleration.errcheck = _check_error

    _LIDAR_FUNCTIONS_AVAILABLE = True

except AttributeError:
    _LIDAR_FUNCTIONS_AVAILABLE = False


# Python wrapper functions
def createLiDARcloud() -> ctypes.POINTER(ULiDARcloud):
    """Create LiDARcloud instance"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "LiDAR functions not available. Rebuild PyHelios with lidar plugin:\n"
            "  build_scripts/build_helios --plugins lidar"
        )
    return helios_lib.createLiDARcloud()


def destroyLiDARcloud(cloud_ptr: ctypes.POINTER(ULiDARcloud)) -> None:
    """Destroy LiDARcloud instance"""
    if cloud_ptr and _LIDAR_FUNCTIONS_AVAILABLE:
        helios_lib.destroyLiDARcloud(cloud_ptr)


def addLiDARScan(cloud_ptr: ctypes.POINTER(ULiDARcloud),
                 origin: List[float], Ntheta: int, theta_range: Tuple[float, float],
                 Nphi: int, phi_range: Tuple[float, float],
                 exit_diameter: float, beam_divergence: float,
                 column_format: Optional[List[str]] = None,
                 range_noise_stddev: float = 0.0, angle_noise_stddev: float = 0.0) -> int:
    """Add a LiDAR scan to the point cloud"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")

    if len(origin) != 3:
        raise ValueError("Origin must be a 3-element array [x, y, z]")

    origin_array = (ctypes.c_float * 3)(*origin)

    if column_format:
        column_array = (ctypes.c_char_p * len(column_format))(
            *[c.encode('utf-8') for c in column_format]
        )
        n_cols = len(column_format)
    else:
        column_array = None
        n_cols = 0

    return helios_lib.addLiDARScan(
        cloud_ptr, origin_array, Ntheta, theta_range[0], theta_range[1],
        Nphi, phi_range[0], phi_range[1], exit_diameter, beam_divergence,
        float(range_noise_stddev), float(angle_noise_stddev),
        column_array, n_cols
    )


def getLiDARScanCount(cloud_ptr: ctypes.POINTER(ULiDARcloud)) -> int:
    """Get number of scans in the cloud"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARScanCount(cloud_ptr)


def getLiDARScanOrigin(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int) -> List[float]:
    """Get origin of a specific scan"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")

    origin = (ctypes.c_float * 3)()
    helios_lib.getLiDARScanOrigin(cloud_ptr, scanID, origin)
    return list(origin)


def getLiDARScanSizeTheta(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int) -> int:
    """Get number of zenith scan points"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARScanSizeTheta(cloud_ptr, scanID)


def getLiDARScanSizePhi(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int) -> int:
    """Get number of azimuthal scan points"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARScanSizePhi(cloud_ptr, scanID)


def getLiDARScanRangeNoiseStdDev(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int) -> float:
    """Get the range (along-beam) measurement noise standard deviation for a scan (meters)"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARScanRangeNoiseStdDev(cloud_ptr, scanID)


def getLiDARScanAngleNoiseStdDev(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int) -> float:
    """Get the angular (beam-pointing) jitter standard deviation for a scan (radians)"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARScanAngleNoiseStdDev(cloud_ptr, scanID)


def addLiDARHitPoint(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int,
                     xyz: List[float], direction: List[float]) -> None:
    """Add a hit point to the cloud"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")

    if len(xyz) != 3:
        raise ValueError("XYZ must be a 3-element array")
    if len(direction) < 2:
        raise ValueError("Direction must have at least 2 elements [radius, elevation]")

    xyz_array = (ctypes.c_float * 3)(*xyz)
    direction_array = (ctypes.c_float * 3)(direction[0], direction[1], direction[2] if len(direction) > 2 else 0)
    helios_lib.addLiDARHitPoint(cloud_ptr, scanID, xyz_array, direction_array)


def addLiDARHitPointRGB(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int,
                        xyz: List[float], direction: List[float], color: List[float]) -> None:
    """Add a hit point with color to the cloud"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")

    if len(xyz) != 3:
        raise ValueError("XYZ must be a 3-element array")
    if len(direction) < 2:
        raise ValueError("Direction must have at least 2 elements")
    if len(color) != 3:
        raise ValueError("Color must be a 3-element array [r, g, b]")

    xyz_array = (ctypes.c_float * 3)(*xyz)
    direction_array = (ctypes.c_float * 3)(direction[0], direction[1], direction[2] if len(direction) > 2 else 0)
    color_array = (ctypes.c_float * 3)(*color)
    helios_lib.addLiDARHitPointRGB(cloud_ptr, scanID, xyz_array, direction_array, color_array)


def addLiDARHitPoints(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int,
                      xyzs, directions, count: int, colors=None) -> None:
    """Add many hit points to the cloud in a single call (bulk ingestion).

    xyzs and directions must be contiguous float32 buffers (e.g. numpy arrays)
    of shape (count, 3). colors, if given, must be a contiguous float32 buffer
    of shape (count, 3); pass None to add without color. The buffers are passed
    straight through to C without per-point Python marshalling.
    """
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")

    xyzs_ptr = xyzs.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    directions_ptr = directions.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    colors_ptr = colors.ctypes.data_as(ctypes.POINTER(ctypes.c_float)) if colors is not None else None
    helios_lib.addLiDARHitPoints(cloud_ptr, scanID, xyzs_ptr, directions_ptr, count, colors_ptr)


def getLiDARHitCount(cloud_ptr: ctypes.POINTER(ULiDARcloud)) -> int:
    """Get total number of hit points"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARHitCount(cloud_ptr)


def getLiDARHitXYZ(cloud_ptr: ctypes.POINTER(ULiDARcloud), index: int) -> List[float]:
    """Get coordinates of a hit point"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")

    xyz = (ctypes.c_float * 3)()
    helios_lib.getLiDARHitXYZ(cloud_ptr, index, xyz)
    return list(xyz)


def getLiDARHitRaydir(cloud_ptr: ctypes.POINTER(ULiDARcloud), index: int) -> List[float]:
    """Get ray direction of a hit point"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")

    direction = (ctypes.c_float * 3)()
    helios_lib.getLiDARHitRaydir(cloud_ptr, index, direction)
    return list(direction)


def getLiDARHitColor(cloud_ptr: ctypes.POINTER(ULiDARcloud), index: int) -> List[float]:
    """Get color of a hit point"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")

    color = (ctypes.c_float * 3)()
    helios_lib.getLiDARHitColor(cloud_ptr, index, color)
    return list(color)


def getLiDARHitScanID(cloud_ptr: ctypes.POINTER(ULiDARcloud), index: int) -> int:
    """Get the scan ID a hit point belongs to"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARHitScanID(cloud_ptr, index)


def doesLiDARHitDataExist(cloud_ptr: ctypes.POINTER(ULiDARcloud), index: int, label: str) -> bool:
    """Check whether a named scalar data value exists for a hit point"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return bool(helios_lib.doesLiDARHitDataExist(cloud_ptr, index, label.encode('utf-8')))


def getLiDARHitData(cloud_ptr: ctypes.POINTER(ULiDARcloud), index: int, label: str) -> float:
    """Get a named scalar data value for a hit point"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARHitData(cloud_ptr, index, label.encode('utf-8'))


def getLiDARHitData_all(cloud_ptr: ctypes.POINTER(ULiDARcloud), label: str, n: int) -> List[float]:
    """Bulk-export a named scalar data value for all hit points in one call"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")

    out = (ctypes.c_float * n)()
    helios_lib.getLiDARHitData_all(cloud_ptr, label.encode('utf-8'), out, n)
    return list(out)


def getLiDARHitsXYZRGB_all(cloud_ptr: ctypes.POINTER(ULiDARcloud), n: int) -> Tuple[List[float], List[float]]:
    """Bulk-export XYZ coordinates and RGB colors for all hit points in one call.

    Returns a tuple (xyz_flat, rgb_flat) of flat 3*n-element lists.
    """
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")

    xyz = (ctypes.c_float * (3 * n))()
    rgb = (ctypes.c_float * (3 * n))()
    helios_lib.getLiDARHitsXYZRGB_all(cloud_ptr, xyz, rgb, n)
    return list(xyz), list(rgb)


def deleteLiDARHitPoint(cloud_ptr: ctypes.POINTER(ULiDARcloud), index: int) -> None:
    """Delete a hit point from the cloud"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.deleteLiDARHitPoint(cloud_ptr, index)


def lidarCoordinateShift(cloud_ptr: ctypes.POINTER(ULiDARcloud), shift: List[float]) -> None:
    """Translate all hit points by a shift vector"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")

    if len(shift) != 3:
        raise ValueError("Shift must be a 3-element array [x, y, z]")

    shift_array = (ctypes.c_float * 3)(*shift)
    helios_lib.lidarCoordinateShift(cloud_ptr, shift_array)


def lidarCoordinateRotation(cloud_ptr: ctypes.POINTER(ULiDARcloud), rotation: List[float]) -> None:
    """Rotate all hit points by spherical rotation angles"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")

    if len(rotation) < 2:
        raise ValueError("Rotation must have at least 2 elements [radius, elevation]")

    rotation_array = (ctypes.c_float * 3)(rotation[0], rotation[1], rotation[2] if len(rotation) > 2 else 0)
    helios_lib.lidarCoordinateRotation(cloud_ptr, rotation_array)


def lidarTriangulateHitPoints(cloud_ptr: ctypes.POINTER(ULiDARcloud),
                               Lmax: float, max_aspect_ratio: float) -> None:
    """Generate triangle mesh from hit points"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.lidarTriangulateHitPoints(cloud_ptr, Lmax, max_aspect_ratio)


def getLiDARTriangleCount(cloud_ptr: ctypes.POINTER(ULiDARcloud)) -> int:
    """Get number of triangles in the mesh"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARTriangleCount(cloud_ptr)


def lidarDistanceFilter(cloud_ptr: ctypes.POINTER(ULiDARcloud), maxdistance: float) -> None:
    """Filter hit points by maximum distance"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.lidarDistanceFilter(cloud_ptr, maxdistance)


def lidarReflectanceFilter(cloud_ptr: ctypes.POINTER(ULiDARcloud), minreflectance: float) -> None:
    """Filter hit points by minimum reflectance"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.lidarReflectanceFilter(cloud_ptr, minreflectance)


def lidarFirstHitFilter(cloud_ptr: ctypes.POINTER(ULiDARcloud)) -> None:
    """Keep only first return hit points"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.lidarFirstHitFilter(cloud_ptr)


def lidarLastHitFilter(cloud_ptr: ctypes.POINTER(ULiDARcloud)) -> None:
    """Keep only last return hit points"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.lidarLastHitFilter(cloud_ptr)


def exportLiDARPointCloud(cloud_ptr: ctypes.POINTER(ULiDARcloud), filename: str) -> None:
    """Export point cloud to ASCII file"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.exportLiDARPointCloud(cloud_ptr, filename.encode('utf-8'))


def exportLiDARScans(cloud_ptr: ctypes.POINTER(ULiDARcloud), filename: str) -> None:
    """Export all scans to an XML metadata file plus one ASCII data file per scan"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.exportLiDARScans(cloud_ptr, filename.encode('utf-8'))


def loadLiDARXML(cloud_ptr: ctypes.POINTER(ULiDARcloud), filename: str) -> None:
    """Load scan metadata from XML file"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.loadLiDARXML(cloud_ptr, filename.encode('utf-8'))


def lidarDisableMessages(cloud_ptr: ctypes.POINTER(ULiDARcloud)) -> None:
    """Disable console output messages"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.lidarDisableMessages(cloud_ptr)


def lidarEnableMessages(cloud_ptr: ctypes.POINTER(ULiDARcloud)) -> None:
    """Enable console output messages"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.lidarEnableMessages(cloud_ptr)


def addLiDARGrid(cloud_ptr: ctypes.POINTER(ULiDARcloud), center: List[float],
                 size: List[float], ndiv: List[int], rotation: float) -> None:
    """Add a rectangular grid of voxel cells"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")

    if len(center) != 3:
        raise ValueError("Center must be a 3-element array [x, y, z]")
    if len(size) != 3:
        raise ValueError("Size must be a 3-element array [x, y, z]")
    if len(ndiv) != 3:
        raise ValueError("Ndiv must be a 3-element array [nx, ny, nz]")

    center_array = (ctypes.c_float * 3)(*center)
    size_array = (ctypes.c_float * 3)(*size)
    ndiv_array = (ctypes.c_int * 3)(*ndiv)
    helios_lib.addLiDARGrid(cloud_ptr, center_array, size_array, ndiv_array, rotation)


def addLiDARGridCell(cloud_ptr: ctypes.POINTER(ULiDARcloud), center: List[float],
                     size: List[float], rotation: float) -> None:
    """Add a single grid cell"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")

    if len(center) != 3:
        raise ValueError("Center must be a 3-element array [x, y, z]")
    if len(size) != 3:
        raise ValueError("Size must be a 3-element array [x, y, z]")

    center_array = (ctypes.c_float * 3)(*center)
    size_array = (ctypes.c_float * 3)(*size)
    helios_lib.addLiDARGridCell(cloud_ptr, center_array, size_array, rotation)


def getLiDARGridCellCount(cloud_ptr: ctypes.POINTER(ULiDARcloud)) -> int:
    """Get number of grid cells"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARGridCellCount(cloud_ptr)


def getLiDARCellCenter(cloud_ptr: ctypes.POINTER(ULiDARcloud), index: int) -> List[float]:
    """Get center position of a grid cell"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")

    center = (ctypes.c_float * 3)()
    helios_lib.getLiDARCellCenter(cloud_ptr, index, center)
    return list(center)


def getLiDARCellSize(cloud_ptr: ctypes.POINTER(ULiDARcloud), index: int) -> List[float]:
    """Get size of a grid cell"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")

    size = (ctypes.c_float * 3)()
    helios_lib.getLiDARCellSize(cloud_ptr, index, size)
    return list(size)


def getLiDARCellLeafArea(cloud_ptr: ctypes.POINTER(ULiDARcloud), index: int) -> float:
    """Get leaf area of a grid cell"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARCellLeafArea(cloud_ptr, index)


def getLiDARCellLeafAreaDensity(cloud_ptr: ctypes.POINTER(ULiDARcloud), index: int) -> float:
    """Get leaf area density of a grid cell"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARCellLeafAreaDensity(cloud_ptr, index)


def calculateLiDARHitGridCell(cloud_ptr: ctypes.POINTER(ULiDARcloud)) -> None:
    """Calculate hit point grid cell assignments"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.calculateLiDARHitGridCell(cloud_ptr)


def syntheticLiDARScan(cloud_ptr: ctypes.POINTER(ULiDARcloud),
                       context_ptr: ctypes.POINTER(UContext)) -> None:
    """Perform synthetic discrete-return LiDAR scan"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.syntheticLiDARScan(cloud_ptr, context_ptr)


def syntheticLiDARScanAppend(cloud_ptr: ctypes.POINTER(ULiDARcloud),
                             context_ptr: ctypes.POINTER(UContext),
                             append: bool) -> None:
    """Perform synthetic scan with append control"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.syntheticLiDARScanAppend(cloud_ptr, context_ptr, append)


def syntheticLiDARScanWaveform(cloud_ptr: ctypes.POINTER(ULiDARcloud),
                               context_ptr: ctypes.POINTER(UContext),
                               rays_per_pulse: int,
                               pulse_distance_threshold: float) -> None:
    """Perform synthetic full-waveform LiDAR scan"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.syntheticLiDARScanWaveform(cloud_ptr, context_ptr, rays_per_pulse, pulse_distance_threshold)


def syntheticLiDARScanFull(cloud_ptr: ctypes.POINTER(ULiDARcloud),
                           context_ptr: ctypes.POINTER(UContext),
                           rays_per_pulse: int,
                           pulse_distance_threshold: float,
                           scan_grid_only: bool,
                           record_misses: bool,
                           append: bool) -> None:
    """Perform synthetic scan with full control"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.syntheticLiDARScanFull(cloud_ptr, context_ptr, rays_per_pulse,
                                      pulse_distance_threshold, scan_grid_only,
                                      record_misses, append)


def calculateLiDARLeafArea(cloud_ptr: ctypes.POINTER(ULiDARcloud),
                           context_ptr: ctypes.POINTER(UContext)) -> None:
    """Calculate leaf area for each grid cell"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.calculateLiDARLeafArea(cloud_ptr, context_ptr)


def calculateLiDARLeafAreaMinHits(cloud_ptr: ctypes.POINTER(ULiDARcloud),
                                  context_ptr: ctypes.POINTER(UContext),
                                  min_voxel_hits: int) -> None:
    """Calculate leaf area with minimum voxel hits threshold"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.calculateLiDARLeafAreaMinHits(cloud_ptr, context_ptr, min_voxel_hits)


def exportLiDARTriangleNormals(cloud_ptr: ctypes.POINTER(ULiDARcloud), filename: str) -> None:
    """Export triangle normal vectors"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.exportLiDARTriangleNormals(cloud_ptr, filename.encode('utf-8'))


def exportLiDARTriangleAreas(cloud_ptr: ctypes.POINTER(ULiDARcloud), filename: str) -> None:
    """Export triangle areas"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.exportLiDARTriangleAreas(cloud_ptr, filename.encode('utf-8'))


def exportLiDARLeafAreas(cloud_ptr: ctypes.POINTER(ULiDARcloud), filename: str) -> None:
    """Export leaf areas for each grid cell"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.exportLiDARLeafAreas(cloud_ptr, filename.encode('utf-8'))


def exportLiDARLeafAreaDensities(cloud_ptr: ctypes.POINTER(ULiDARcloud), filename: str) -> None:
    """Export leaf area densities for each grid cell"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.exportLiDARLeafAreaDensities(cloud_ptr, filename.encode('utf-8'))


def exportLiDARGtheta(cloud_ptr: ctypes.POINTER(ULiDARcloud), filename: str) -> None:
    """Export G(theta) values for each grid cell"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.exportLiDARGtheta(cloud_ptr, filename.encode('utf-8'))


def getLiDARCellGtheta(cloud_ptr: ctypes.POINTER(ULiDARcloud), index: int) -> float:
    """Get G(theta) value for a grid cell"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARCellGtheta(cloud_ptr, index)


def setLiDARCellGtheta(cloud_ptr: ctypes.POINTER(ULiDARcloud), Gtheta: float, index: int) -> None:
    """Set G(theta) value for a grid cell"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.setLiDARCellGtheta(cloud_ptr, Gtheta, index)


def gapfillLiDARMisses(cloud_ptr: ctypes.POINTER(ULiDARcloud)) -> None:
    """Gapfill sky/miss points"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.gapfillLiDARMisses(cloud_ptr)


def calculateSyntheticLiDARLeafArea(cloud_ptr: ctypes.POINTER(ULiDARcloud),
                                    context_ptr: ctypes.POINTER(UContext)) -> None:
    """Calculate synthetic leaf area for validation"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.calculateSyntheticLiDARLeafArea(cloud_ptr, context_ptr)


def calculateSyntheticLiDARGtheta(cloud_ptr: ctypes.POINTER(ULiDARcloud),
                                  context_ptr: ctypes.POINTER(UContext)) -> None:
    """Calculate synthetic G(theta) for validation"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.calculateSyntheticLiDARGtheta(cloud_ptr, context_ptr)


def addLiDARTrianglesToContext(cloud_ptr: ctypes.POINTER(ULiDARcloud),
                               context_ptr: ctypes.POINTER(UContext)) -> None:
    """Add triangulated mesh to Context as primitives"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.addLiDARTrianglesToContext(cloud_ptr, context_ptr)


def initializeLiDARCollisionDetection(cloud_ptr: ctypes.POINTER(ULiDARcloud),
                                     context_ptr: ctypes.POINTER(UContext)) -> None:
    """Initialize CollisionDetection for ray tracing"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.initializeLiDARCollisionDetection(cloud_ptr, context_ptr)


def enableLiDARCDGPUAcceleration(cloud_ptr: ctypes.POINTER(ULiDARcloud)) -> None:
    """Enable GPU acceleration for collision detection"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.enableLiDARCDGPUAcceleration(cloud_ptr)


def disableLiDARCDGPUAcceleration(cloud_ptr: ctypes.POINTER(ULiDARcloud)) -> None:
    """Disable GPU acceleration for collision detection"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.disableLiDARCDGPUAcceleration(cloud_ptr)


# Mock mode for development
if not _LIDAR_FUNCTIONS_AVAILABLE:
    def mock_createLiDARcloud(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: LiDAR not available. "
            "This would create a LiDAR cloud instance with native library."
        )

    def mock_lidar_operation(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: LiDAR operation not available. "
            "This would execute LiDAR operations with native library."
        )

    # Replace functions with mocks for development
    createLiDARcloud = mock_createLiDARcloud
    addLiDARScan = mock_lidar_operation
    addLiDARHitPoint = mock_lidar_operation
