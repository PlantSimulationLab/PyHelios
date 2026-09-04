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
    check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage, helios_lib.clearError)
    return result


# Progress-callback function-pointer type fired during syntheticScan: void(float progress, const char* message)
LiDARProgressCallback = ctypes.CFUNCTYPE(None, ctypes.c_float, ctypes.c_char_p)


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
        ctypes.c_uint,   # nCols
        ctypes.c_float,  # scanTiltRoll
        ctypes.c_float,  # scanTiltPitch
        ctypes.c_float   # scanAzimuthOffset
    ]
    helios_lib.addLiDARScan.restype = ctypes.c_uint
    helios_lib.addLiDARScan.errcheck = _check_error

    helios_lib.addLiDARScanMoving.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.c_uint,   # Ntheta
        ctypes.c_float,  # thetaMin
        ctypes.c_float,  # thetaMax
        ctypes.c_uint,   # Nphi
        ctypes.c_float,  # phiMin
        ctypes.c_float,  # phiMax
        ctypes.c_float,  # exitDiameter
        ctypes.c_float,  # beamDivergence
        ctypes.c_float,  # rangeNoiseStdDev
        ctypes.c_float,  # angleNoiseStdDev
        ctypes.POINTER(ctypes.c_char_p),  # columnFormat
        ctypes.c_uint,   # nCols
        ctypes.POINTER(ctypes.c_double),  # traj_t[M]
        ctypes.POINTER(ctypes.c_float),   # traj_pos[3*M]
        ctypes.POINTER(ctypes.c_float),   # traj_rot[4*M or 3*M]
        ctypes.c_uint,   # M
        ctypes.c_int,    # rotIsQuaternion
        ctypes.POINTER(ctypes.c_float),   # lever_arm[3]
        ctypes.POINTER(ctypes.c_float),   # boresight_rpy[3]
        ctypes.c_float,  # pulse_rate_hz
        ctypes.c_double  # t0
    ]
    helios_lib.addLiDARScanMoving.restype = ctypes.c_uint
    helios_lib.addLiDARScanMoving.errcheck = _check_error

    helios_lib.addLiDARScanSpinning.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(ctypes.c_float),  # beamElevationAngles[nAngles]
        ctypes.c_uint,   # nAngles
        ctypes.c_float,  # azimuthStep_rad
        ctypes.c_float,  # pulse_rate_hz
        ctypes.c_float,  # exitDiameter
        ctypes.c_float,  # beamDivergence
        ctypes.c_float,  # rangeNoiseStdDev
        ctypes.c_float,  # angleNoiseStdDev
        ctypes.POINTER(ctypes.c_char_p),  # columnFormat
        ctypes.c_uint,   # nCols
        ctypes.POINTER(ctypes.c_double),  # traj_t[M]
        ctypes.POINTER(ctypes.c_float),   # traj_pos[3*M]
        ctypes.POINTER(ctypes.c_float),   # traj_rot[4*M or 3*M]
        ctypes.c_uint,   # M
        ctypes.c_int,    # rotIsQuaternion
        ctypes.POINTER(ctypes.c_float),   # lever_arm[3]
        ctypes.POINTER(ctypes.c_float),   # boresight_rpy[3]
        ctypes.c_double  # t0
    ]
    helios_lib.addLiDARScanSpinning.restype = ctypes.c_uint
    helios_lib.addLiDARScanSpinning.errcheck = _check_error

    helios_lib.addLiDARScanMovingRaster.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.c_uint,   # Ntheta
        ctypes.c_float,  # thetaMin
        ctypes.c_float,  # thetaMax
        ctypes.c_uint,   # Nphi
        ctypes.c_float,  # phiMin
        ctypes.c_float,  # phiMax
        ctypes.c_float,  # pulse_rate_hz
        ctypes.c_float,  # exitDiameter
        ctypes.c_float,  # beamDivergence
        ctypes.c_float,  # rangeNoiseStdDev
        ctypes.c_float,  # angleNoiseStdDev
        ctypes.POINTER(ctypes.c_char_p),  # columnFormat
        ctypes.c_uint,   # nCols
        ctypes.POINTER(ctypes.c_double),  # traj_t[M]
        ctypes.POINTER(ctypes.c_float),   # traj_pos[3*M]
        ctypes.POINTER(ctypes.c_float),   # traj_quat[4*M]
        ctypes.c_uint,   # M
        ctypes.POINTER(ctypes.c_float),   # lever_arm[3]
        ctypes.POINTER(ctypes.c_float),   # boresight_rpy[3]
        ctypes.c_double  # t0
    ]
    helios_lib.addLiDARScanMovingRaster.restype = ctypes.c_uint
    helios_lib.addLiDARScanMovingRaster.errcheck = _check_error

    helios_lib.addLiDARScanRisley.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(ctypes.c_double),  # prisms[4*nPrisms]
        ctypes.c_uint,    # nPrisms
        ctypes.c_double,  # refractive_index_air
        ctypes.c_float,   # pulse_rate_hz
        ctypes.c_float,   # exitDiameter
        ctypes.c_float,   # beamDivergence
        ctypes.c_float,   # rangeNoiseStdDev
        ctypes.c_float,   # angleNoiseStdDev
        ctypes.POINTER(ctypes.c_char_p),  # columnFormat
        ctypes.c_uint,    # nCols
        ctypes.POINTER(ctypes.c_double),  # traj_t[M]
        ctypes.POINTER(ctypes.c_float),   # traj_pos[3*M]
        ctypes.POINTER(ctypes.c_float),   # traj_rot[4*M or 3*M]
        ctypes.c_uint,    # M
        ctypes.c_int,     # rotIsQuaternion
        ctypes.POINTER(ctypes.c_float),   # lever_arm[3]
        ctypes.POINTER(ctypes.c_float),   # boresight_rpy[3]
        ctypes.c_double   # t0
    ]
    helios_lib.addLiDARScanRisley.restype = ctypes.c_uint
    helios_lib.addLiDARScanRisley.errcheck = _check_error

    # Scan acquisition-mode introspection
    helios_lib.getLiDARScanMode.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARScanMode.restype = ctypes.c_int
    helios_lib.getLiDARScanMode.errcheck = _check_error

    helios_lib.getLiDARScanStepsPerRev.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARScanStepsPerRev.restype = ctypes.c_uint
    helios_lib.getLiDARScanStepsPerRev.errcheck = _check_error

    helios_lib.getLiDARScanRotationRate.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARScanRotationRate.restype = ctypes.c_double
    helios_lib.getLiDARScanRotationRate.errcheck = _check_error

    helios_lib.getLiDARScanRevolutions.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARScanRevolutions.restype = ctypes.c_double
    helios_lib.getLiDARScanRevolutions.errcheck = _check_error

    helios_lib.getLiDARScanRisleyPrismCount.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARScanRisleyPrismCount.restype = ctypes.c_uint
    helios_lib.getLiDARScanRisleyPrismCount.errcheck = _check_error

    helios_lib.getLiDARScanRisleyPrisms.argtypes = [
        ctypes.POINTER(ULiDARcloud), ctypes.c_uint,
        ctypes.POINTER(ctypes.c_double),  # out[4*count]
        ctypes.c_uint,                    # count (in prisms)
    ]
    helios_lib.getLiDARScanRisleyPrisms.restype = None
    helios_lib.getLiDARScanRisleyPrisms.errcheck = _check_error

    helios_lib.getLiDARScanRisleyRefractiveIndexAir.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARScanRisleyRefractiveIndexAir.restype = ctypes.c_double
    helios_lib.getLiDARScanRisleyRefractiveIndexAir.errcheck = _check_error

    # Return-mode configuration
    helios_lib.getLiDARScanReturnMode.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARScanReturnMode.restype = ctypes.c_int
    helios_lib.getLiDARScanReturnMode.errcheck = _check_error

    helios_lib.setLiDARScanReturnMode.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint, ctypes.c_int]
    helios_lib.setLiDARScanReturnMode.restype = None
    helios_lib.setLiDARScanReturnMode.errcheck = _check_error

    helios_lib.getLiDARScanSingleReturnSelection.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARScanSingleReturnSelection.restype = ctypes.c_int
    helios_lib.getLiDARScanSingleReturnSelection.errcheck = _check_error

    helios_lib.setLiDARScanSingleReturnSelection.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint, ctypes.c_int]
    helios_lib.setLiDARScanSingleReturnSelection.restype = None
    helios_lib.setLiDARScanSingleReturnSelection.errcheck = _check_error

    helios_lib.getLiDARScanMaxReturns.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARScanMaxReturns.restype = ctypes.c_int
    helios_lib.getLiDARScanMaxReturns.errcheck = _check_error

    helios_lib.setLiDARScanMaxReturns.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint, ctypes.c_int]
    helios_lib.setLiDARScanMaxReturns.restype = None
    helios_lib.setLiDARScanMaxReturns.errcheck = _check_error

    helios_lib.getLiDARScanPulseWidth.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARScanPulseWidth.restype = ctypes.c_float
    helios_lib.getLiDARScanPulseWidth.errcheck = _check_error

    helios_lib.setLiDARScanPulseWidth.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint, ctypes.c_float]
    helios_lib.setLiDARScanPulseWidth.restype = None
    helios_lib.setLiDARScanPulseWidth.errcheck = _check_error

    helios_lib.getLiDARScanDetectionThreshold.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARScanDetectionThreshold.restype = ctypes.c_float
    helios_lib.getLiDARScanDetectionThreshold.errcheck = _check_error

    helios_lib.setLiDARScanDetectionThreshold.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint, ctypes.c_float]
    helios_lib.setLiDARScanDetectionThreshold.restype = None
    helios_lib.setLiDARScanDetectionThreshold.errcheck = _check_error

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

    helios_lib.getLiDARScanTiltRoll.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARScanTiltRoll.restype = ctypes.c_float
    helios_lib.getLiDARScanTiltRoll.errcheck = _check_error

    helios_lib.getLiDARScanTiltPitch.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARScanTiltPitch.restype = ctypes.c_float
    helios_lib.getLiDARScanTiltPitch.errcheck = _check_error

    helios_lib.getLiDARScanAzimuthOffset.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARScanAzimuthOffset.restype = ctypes.c_float
    helios_lib.getLiDARScanAzimuthOffset.errcheck = _check_error

    helios_lib.getLiDARScanPattern.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARScanPattern.restype = ctypes.c_int
    helios_lib.getLiDARScanPattern.errcheck = _check_error

    helios_lib.getLiDARScanBeamZenithAngleCount.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARScanBeamZenithAngleCount.restype = ctypes.c_uint
    helios_lib.getLiDARScanBeamZenithAngleCount.errcheck = _check_error

    helios_lib.getLiDARScanBeamZenithAngles.argtypes = [
        ctypes.POINTER(ULiDARcloud), ctypes.c_uint,
        ctypes.POINTER(ctypes.c_float), ctypes.c_uint,
    ]
    helios_lib.getLiDARScanBeamZenithAngles.restype = None
    helios_lib.getLiDARScanBeamZenithAngles.errcheck = _check_error

    # Miss detection
    helios_lib.isLiDARHitMiss.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.isLiDARHitMiss.restype = ctypes.c_int
    helios_lib.isLiDARHitMiss.errcheck = _check_error

    helios_lib.lidarHasMisses.argtypes = [ctypes.POINTER(ULiDARcloud)]
    helios_lib.lidarHasMisses.restype = ctypes.c_int
    helios_lib.lidarHasMisses.errcheck = _check_error

    helios_lib.getLiDARMissDistance.argtypes = []
    helios_lib.getLiDARMissDistance.restype = ctypes.c_float
    # No errcheck: pure constant accessor, never sets an error.

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

    helios_lib.addLiDARHitPointsWithData.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_float),   # xyzs[count*3]
        ctypes.POINTER(ctypes.c_float),   # directions[count*3]
        ctypes.c_uint,                    # count
        ctypes.POINTER(ctypes.c_float),   # colors[count*3] or NULL
        ctypes.POINTER(ctypes.c_char_p),  # dataLabels[nLabels]
        ctypes.c_uint,                    # nLabels
        ctypes.POINTER(ctypes.c_double)   # dataValues[count*nLabels] or NULL
    ]
    helios_lib.addLiDARHitPointsWithData.restype = None
    helios_lib.addLiDARHitPointsWithData.errcheck = _check_error

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

    helios_lib.getLiDARHitOrigin.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_float)
    ]
    helios_lib.getLiDARHitOrigin.restype = None
    helios_lib.getLiDARHitOrigin.errcheck = _check_error

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

    helios_lib.getLiDARHitDataColumn.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_uint,
        ctypes.c_double
    ]
    helios_lib.getLiDARHitDataColumn.restype = None
    helios_lib.getLiDARHitDataColumn.errcheck = _check_error

    helios_lib.getLiDARHitDataColumnIndex.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.c_char_p,
    ]
    helios_lib.getLiDARHitDataColumnIndex.restype = ctypes.c_int
    helios_lib.getLiDARHitDataColumnIndex.errcheck = _check_error

    helios_lib.getLiDARHitsXYZRGB_all.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_uint
    ]
    helios_lib.getLiDARHitsXYZRGB_all.restype = None
    helios_lib.getLiDARHitsXYZRGB_all.errcheck = _check_error

    helios_lib.getLiDARHitScanID_all.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_uint
    ]
    helios_lib.getLiDARHitScanID_all.restype = None
    helios_lib.getLiDARHitScanID_all.errcheck = _check_error

    helios_lib.isLiDARHitMiss_all.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_uint
    ]
    helios_lib.isLiDARHitMiss_all.restype = None
    helios_lib.isLiDARHitMiss_all.errcheck = _check_error

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

    helios_lib.getLiDARTriangulationStats.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(ctypes.c_uint),   # out[4]
    ]
    helios_lib.getLiDARTriangulationStats.restype = None
    helios_lib.getLiDARTriangulationStats.errcheck = _check_error

    helios_lib.getLiDARTriangleVertices_all.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(ctypes.c_float),  # out_xyz[triCount*9]
        ctypes.POINTER(ctypes.c_int),    # out_scan[triCount] or NULL
        ctypes.c_uint                    # triCount
    ]
    helios_lib.getLiDARTriangleVertices_all.restype = None
    helios_lib.getLiDARTriangleVertices_all.errcheck = _check_error

    helios_lib.lidarSetExternalTriangulation.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(ctypes.c_float),  # xyz[triCount*9]
        ctypes.POINTER(ctypes.c_int),    # scanIDs[triCount] (required)
        ctypes.c_uint                    # triCount
    ]
    helios_lib.lidarSetExternalTriangulation.restype = None
    helios_lib.lidarSetExternalTriangulation.errcheck = _check_error

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
    helios_lib.exportLiDARPointCloud.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_char_p, ctypes.c_bool]
    helios_lib.exportLiDARPointCloud.restype = None
    helios_lib.exportLiDARPointCloud.errcheck = _check_error

    helios_lib.exportLiDARLeafAreaUncertainty.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_char_p]
    helios_lib.exportLiDARLeafAreaUncertainty.restype = None
    helios_lib.exportLiDARLeafAreaUncertainty.errcheck = _check_error

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

    helios_lib.addLiDARGridTerrainFollowing.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_float,
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_uint
    ]
    helios_lib.addLiDARGridTerrainFollowing.restype = None
    helios_lib.addLiDARGridTerrainFollowing.errcheck = _check_error

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

    helios_lib.getLiDARCellRotation.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARCellRotation.restype = ctypes.c_float
    helios_lib.getLiDARCellRotation.errcheck = _check_error

    helios_lib.getLiDARCellLeafArea.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARCellLeafArea.restype = ctypes.c_float
    helios_lib.getLiDARCellLeafArea.errcheck = _check_error

    helios_lib.getLiDARCellLeafAreaDensity.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARCellLeafAreaDensity.restype = ctypes.c_float
    helios_lib.getLiDARCellLeafAreaDensity.errcheck = _check_error

    # Leaf-area sampling uncertainty (Pimont et al. 2018)
    helios_lib.getLiDARCellBeamCount.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARCellBeamCount.restype = ctypes.c_int
    helios_lib.getLiDARCellBeamCount.errcheck = _check_error

    helios_lib.getLiDARCellRelativeDensityIndex.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARCellRelativeDensityIndex.restype = ctypes.c_float
    helios_lib.getLiDARCellRelativeDensityIndex.errcheck = _check_error

    helios_lib.getLiDARCellMeanPathLength.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARCellMeanPathLength.restype = ctypes.c_float
    helios_lib.getLiDARCellMeanPathLength.errcheck = _check_error

    helios_lib.getLiDARCellLADVariance.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_uint]
    helios_lib.getLiDARCellLADVariance.restype = ctypes.c_float
    helios_lib.getLiDARCellLADVariance.errcheck = _check_error

    helios_lib.getLiDARCellLeafAreaConfidenceInterval.argtypes = [
        ctypes.POINTER(ULiDARcloud), ctypes.c_uint, ctypes.c_float,
        ctypes.POINTER(ctypes.c_float),  # out_bounds[2]
    ]
    helios_lib.getLiDARCellLeafAreaConfidenceInterval.restype = ctypes.c_int
    helios_lib.getLiDARCellLeafAreaConfidenceInterval.errcheck = _check_error

    helios_lib.getLiDARGroupLADConfidenceInterval.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(ctypes.c_uint),   # indices[nIndices]
        ctypes.c_uint, ctypes.c_float,
        ctypes.POINTER(ctypes.c_float),  # out_results[3]
    ]
    helios_lib.getLiDARGroupLADConfidenceInterval.restype = ctypes.c_int
    helios_lib.getLiDARGroupLADConfidenceInterval.errcheck = _check_error

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

    helios_lib.setLiDARCancelFlag.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(ctypes.c_int),  # cancellation flag (0/non-zero), or NULL
    ]
    helios_lib.setLiDARCancelFlag.restype = None
    helios_lib.setLiDARCancelFlag.errcheck = _check_error

    helios_lib.setLiDARSyntheticScanMemoryBudget.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.c_size_t,  # soft cap (bytes) on ray-tracing scratch buffers; must be > 0
    ]
    helios_lib.setLiDARSyntheticScanMemoryBudget.restype = None
    helios_lib.setLiDARSyntheticScanMemoryBudget.errcheck = _check_error

    helios_lib.getLiDARSyntheticScanMemoryBudget.argtypes = [ctypes.POINTER(ULiDARcloud)]
    helios_lib.getLiDARSyntheticScanMemoryBudget.restype = ctypes.c_size_t
    helios_lib.getLiDARSyntheticScanMemoryBudget.errcheck = _check_error

    helios_lib.setLiDARSyntheticScanProgressPointer.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(ctypes.c_int),  # per-scan progress counter, or NULL
    ]
    helios_lib.setLiDARSyntheticScanProgressPointer.restype = None
    helios_lib.setLiDARSyntheticScanProgressPointer.errcheck = _check_error

    helios_lib.setLiDARProgressCallback.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        LiDARProgressCallback,  # void(float, const char*), or NULL to clear
    ]
    helios_lib.setLiDARProgressCallback.restype = None
    helios_lib.setLiDARProgressCallback.errcheck = _check_error

    helios_lib.syntheticLiDARScanDiscrete.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(UContext),
        ctypes.c_bool,  # scan_grid_only
        ctypes.c_bool,  # record_misses
        ctypes.c_bool,  # append
    ]
    helios_lib.syntheticLiDARScanDiscrete.restype = None
    helios_lib.syntheticLiDARScanDiscrete.errcheck = _check_error

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

    helios_lib.syntheticLiDARScanReturnMode.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(UContext),
        ctypes.c_int,    # rays_per_pulse
        ctypes.c_float,  # pulse_distance_threshold
        ctypes.c_int,    # return_mode
        ctypes.c_bool,   # scan_grid_only
        ctypes.c_bool,   # record_misses
        ctypes.c_bool    # append
    ]
    helios_lib.syntheticLiDARScanReturnMode.restype = None
    helios_lib.syntheticLiDARScanReturnMode.errcheck = _check_error

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

    helios_lib.calculateLiDARLeafAreaUncertainty.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(UContext),
        ctypes.c_int,
        ctypes.c_float,
    ]
    helios_lib.calculateLiDARLeafAreaUncertainty.restype = None
    helios_lib.calculateLiDARLeafAreaUncertainty.errcheck = _check_error

    helios_lib.calculateLiDARLeafAreaGtheta.argtypes = [
        ctypes.POINTER(ULiDARcloud),
        ctypes.POINTER(UContext),
        ctypes.c_float,  # Gtheta
        ctypes.c_int,    # min_voxel_hits
        ctypes.c_float,  # element_width
    ]
    helios_lib.calculateLiDARLeafAreaGtheta.restype = None
    helios_lib.calculateLiDARLeafAreaGtheta.errcheck = _check_error

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

    helios_lib.isLiDARGPUAvailable.argtypes = [ctypes.POINTER(ULiDARcloud)]
    helios_lib.isLiDARGPUAvailable.restype = ctypes.c_int
    helios_lib.isLiDARGPUAvailable.errcheck = _check_error

    helios_lib.isLiDARGPUAccelerationEnabled.argtypes = [ctypes.POINTER(ULiDARcloud)]
    helios_lib.isLiDARGPUAccelerationEnabled.restype = ctypes.c_int
    helios_lib.isLiDARGPUAccelerationEnabled.errcheck = _check_error

    _LIDAR_FUNCTIONS_AVAILABLE = True

except AttributeError:
    _LIDAR_FUNCTIONS_AVAILABLE = False


# helios-core 1.3.84 additions, probed separately so a library built against an older core
# keeps the whole LiDAR API working rather than falling back to mock mode. (One missing
# symbol in the main block above mocks every LiDAR function.)
_LIDAR_1384_AVAILABLE = False
try:
    for _fn in ("gapfillLiDARMissesCount", "getLiDARVirtualMissCount", "getLiDARMaxHitPoints"):
        getattr(helios_lib, _fn).argtypes = [ctypes.POINTER(ULiDARcloud)]
        getattr(helios_lib, _fn).restype = ctypes.c_ulonglong
        getattr(helios_lib, _fn).errcheck = _check_error

    helios_lib.estimateLiDARHitPointMemory.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_ulonglong]
    helios_lib.estimateLiDARHitPointMemory.restype = ctypes.c_ulonglong
    helios_lib.estimateLiDARHitPointMemory.errcheck = _check_error

    helios_lib.gapfillLiDARMissesCountScan.argtypes = [
        ctypes.POINTER(ULiDARcloud), ctypes.c_uint, ctypes.c_bool, ctypes.c_bool,
    ]
    helios_lib.gapfillLiDARMissesCountScan.restype = ctypes.c_ulonglong
    helios_lib.gapfillLiDARMissesCountScan.errcheck = _check_error

    helios_lib.hasLiDARVirtualMisses.argtypes = [ctypes.POINTER(ULiDARcloud)]
    helios_lib.hasLiDARVirtualMisses.restype = ctypes.c_bool
    helios_lib.hasLiDARVirtualMisses.errcheck = _check_error

    helios_lib.materializeLiDARMisses.argtypes = [ctypes.POINTER(ULiDARcloud)]
    helios_lib.materializeLiDARMisses.restype = None
    helios_lib.materializeLiDARMisses.errcheck = _check_error

    helios_lib.getLiDARScanGridDirection.argtypes = [
        ctypes.POINTER(ULiDARcloud), ctypes.c_uint, ctypes.c_int, ctypes.c_int,
        ctypes.POINTER(ctypes.c_float),
    ]
    helios_lib.getLiDARScanGridDirection.restype = None
    helios_lib.getLiDARScanGridDirection.errcheck = _check_error

    helios_lib.getLiDARHitXYZColumn.argtypes = [
        ctypes.POINTER(ULiDARcloud), ctypes.POINTER(ctypes.c_float), ctypes.c_uint,
    ]
    helios_lib.getLiDARHitXYZColumn.restype = None
    helios_lib.getLiDARHitXYZColumn.errcheck = _check_error

    helios_lib.getLiDARHitScanIDColumn.argtypes = [
        ctypes.POINTER(ULiDARcloud), ctypes.POINTER(ctypes.c_int), ctypes.c_uint,
    ]
    helios_lib.getLiDARHitScanIDColumn.restype = None
    helios_lib.getLiDARHitScanIDColumn.errcheck = _check_error

    helios_lib.setLiDARMaxHitPoints.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_ulonglong]
    helios_lib.setLiDARMaxHitPoints.restype = None
    helios_lib.setLiDARMaxHitPoints.errcheck = _check_error

    helios_lib.getLiDARDefaultMaxHitPoints.argtypes = []
    helios_lib.getLiDARDefaultMaxHitPoints.restype = ctypes.c_ulonglong
    helios_lib.getLiDARDefaultMaxHitPoints.errcheck = _check_error

    helios_lib.reserveLiDARHitPoints.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_ulonglong]
    helios_lib.reserveLiDARHitPoints.restype = None
    helios_lib.reserveLiDARHitPoints.errcheck = _check_error

    helios_lib.setLiDARExactPathLengths.argtypes = [ctypes.POINTER(ULiDARcloud), ctypes.c_bool]
    helios_lib.setLiDARExactPathLengths.restype = None
    helios_lib.setLiDARExactPathLengths.errcheck = _check_error

    helios_lib.getLiDARExactPathLengths.argtypes = [ctypes.POINTER(ULiDARcloud)]
    helios_lib.getLiDARExactPathLengths.restype = ctypes.c_bool
    helios_lib.getLiDARExactPathLengths.errcheck = _check_error

    _LIDAR_1384_AVAILABLE = True
except AttributeError:
    _LIDAR_1384_AVAILABLE = False


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
                 range_noise_stddev: float = 0.0, angle_noise_stddev: float = 0.0,
                 scan_tilt_roll: float = 0.0, scan_tilt_pitch: float = 0.0,
                 scan_azimuth_offset: float = 0.0) -> int:
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
        column_array, n_cols,
        float(scan_tilt_roll), float(scan_tilt_pitch), float(scan_azimuth_offset)
    )


def addLiDARScanMoving(cloud_ptr: ctypes.POINTER(ULiDARcloud),
                       Ntheta: int, theta_range: Tuple[float, float],
                       Nphi: int, phi_range: Tuple[float, float],
                       exit_diameter: float, beam_divergence: float,
                       traj_t: List[float], traj_pos: List[List[float]],
                       traj_rot: List[List[float]], rot_is_quaternion: bool,
                       pulse_rate_hz: float,
                       lever_arm: Optional[List[float]] = None,
                       boresight_rpy: Optional[List[float]] = None,
                       column_format: Optional[List[str]] = None,
                       range_noise_stddev: float = 0.0, angle_noise_stddev: float = 0.0,
                       t0: float = 0.0) -> int:
    """Add a moving-platform (mobile/airborne) raster LiDAR scan driven by a 6-DOF pose trajectory.

    traj_rot entries are length-4 quaternions (qx,qy,qz,qw) if rot_is_quaternion is True,
    otherwise length-3 roll/pitch/yaw Euler angles (radians, intrinsic Z-Y-X).
    """
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")

    M = len(traj_t)
    if M == 0:
        raise ValueError("traj_t must contain at least one trajectory sample")
    if len(traj_pos) != M or len(traj_rot) != M:
        raise ValueError("traj_t, traj_pos, and traj_rot must all have the same length M")
    if pulse_rate_hz <= 0.0:
        raise ValueError("pulse_rate_hz must be greater than 0")

    rot_stride = 4 if rot_is_quaternion else 3
    if any(len(p) != 3 for p in traj_pos):
        raise ValueError("Each traj_pos entry must be a 3-element [x, y, z]")
    if any(len(r) != rot_stride for r in traj_rot):
        raise ValueError(
            f"Each traj_rot entry must have {rot_stride} elements "
            f"({'qx,qy,qz,qw' if rot_is_quaternion else 'roll,pitch,yaw'})"
        )

    t_array = (ctypes.c_double * M)(*[float(t) for t in traj_t])
    pos_flat = [float(c) for p in traj_pos for c in p]
    pos_array = (ctypes.c_float * (3 * M))(*pos_flat)
    rot_flat = [float(c) for r in traj_rot for c in r]
    rot_array = (ctypes.c_float * (rot_stride * M))(*rot_flat)

    lever = lever_arm if lever_arm is not None else [0.0, 0.0, 0.0]
    boresight = boresight_rpy if boresight_rpy is not None else [0.0, 0.0, 0.0]
    if len(lever) != 3 or len(boresight) != 3:
        raise ValueError("lever_arm and boresight_rpy must each be 3-element arrays")
    lever_array = (ctypes.c_float * 3)(*[float(c) for c in lever])
    boresight_array = (ctypes.c_float * 3)(*[float(c) for c in boresight])

    if column_format:
        column_array = (ctypes.c_char_p * len(column_format))(
            *[c.encode('utf-8') for c in column_format]
        )
        n_cols = len(column_format)
    else:
        column_array = None
        n_cols = 0

    return helios_lib.addLiDARScanMoving(
        cloud_ptr, Ntheta, theta_range[0], theta_range[1],
        Nphi, phi_range[0], phi_range[1], exit_diameter, beam_divergence,
        float(range_noise_stddev), float(angle_noise_stddev),
        column_array, n_cols,
        t_array, pos_array, rot_array, M, 1 if rot_is_quaternion else 0,
        lever_array, boresight_array, float(pulse_rate_hz), float(t0)
    )


def addLiDARScanSpinning(cloud_ptr: ctypes.POINTER(ULiDARcloud),
                         beam_elevation_angles: List[float],
                         azimuth_step_rad: float, pulse_rate_hz: float,
                         traj_t: List[float], traj_pos: List[List[float]],
                         traj_rot: List[List[float]], rot_is_quaternion: bool,
                         exit_diameter: float = 0.0, beam_divergence: float = 0.0,
                         lever_arm: Optional[List[float]] = None,
                         boresight_rpy: Optional[List[float]] = None,
                         column_format: Optional[List[str]] = None,
                         range_noise_stddev: float = 0.0, angle_noise_stddev: float = 0.0,
                         t0: float = 0.0) -> int:
    """Add a continuously-spinning multibeam scan from physical instrument parameters.

    beam_elevation_angles are per-channel ELEVATION angles above the horizon (radians), NOT zenith.
    traj_rot entries are length-4 quaternions (qx,qy,qz,qw) if rot_is_quaternion is True,
    otherwise length-3 roll/pitch/yaw Euler angles (radians, intrinsic Z-Y-X).
    """
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")

    n_angles = len(beam_elevation_angles)
    if n_angles == 0:
        raise ValueError("beam_elevation_angles must contain at least one per-channel angle")
    if azimuth_step_rad <= 0.0:
        raise ValueError("azimuth_step_rad must be greater than 0")
    if pulse_rate_hz <= 0.0:
        raise ValueError("pulse_rate_hz must be greater than 0")

    M = len(traj_t)
    if M == 0:
        raise ValueError("traj_t must contain at least one trajectory sample")
    if len(traj_pos) != M or len(traj_rot) != M:
        raise ValueError("traj_t, traj_pos, and traj_rot must all have the same length M")

    rot_stride = 4 if rot_is_quaternion else 3
    if any(len(p) != 3 for p in traj_pos):
        raise ValueError("Each traj_pos entry must be a 3-element [x, y, z]")
    if any(len(r) != rot_stride for r in traj_rot):
        raise ValueError(
            f"Each traj_rot entry must have {rot_stride} elements "
            f"({'qx,qy,qz,qw' if rot_is_quaternion else 'roll,pitch,yaw'})"
        )

    beam_array = (ctypes.c_float * n_angles)(*[float(a) for a in beam_elevation_angles])
    t_array = (ctypes.c_double * M)(*[float(t) for t in traj_t])
    pos_flat = [float(c) for p in traj_pos for c in p]
    pos_array = (ctypes.c_float * (3 * M))(*pos_flat)
    rot_flat = [float(c) for r in traj_rot for c in r]
    rot_array = (ctypes.c_float * (rot_stride * M))(*rot_flat)

    lever = lever_arm if lever_arm is not None else [0.0, 0.0, 0.0]
    boresight = boresight_rpy if boresight_rpy is not None else [0.0, 0.0, 0.0]
    if len(lever) != 3 or len(boresight) != 3:
        raise ValueError("lever_arm and boresight_rpy must each be 3-element arrays")
    lever_array = (ctypes.c_float * 3)(*[float(c) for c in lever])
    boresight_array = (ctypes.c_float * 3)(*[float(c) for c in boresight])

    if column_format:
        column_array = (ctypes.c_char_p * len(column_format))(
            *[c.encode('utf-8') for c in column_format]
        )
        n_cols = len(column_format)
    else:
        column_array = None
        n_cols = 0

    return helios_lib.addLiDARScanSpinning(
        cloud_ptr, beam_array, n_angles, float(azimuth_step_rad), float(pulse_rate_hz),
        float(exit_diameter), float(beam_divergence),
        float(range_noise_stddev), float(angle_noise_stddev),
        column_array, n_cols,
        t_array, pos_array, rot_array, M, 1 if rot_is_quaternion else 0,
        lever_array, boresight_array, float(t0)
    )


def addLiDARScanMovingRaster(cloud_ptr: ctypes.POINTER(ULiDARcloud),
                             Ntheta: int, theta_range: Tuple[float, float],
                             Nphi: int, phi_range: Tuple[float, float],
                             pulse_rate_hz: float,
                             traj_t: List[float], traj_pos: List[List[float]],
                             traj_quat: List[List[float]],
                             exit_diameter: float = 0.0, beam_divergence: float = 0.0,
                             lever_arm: Optional[List[float]] = None,
                             boresight_rpy: Optional[List[float]] = None,
                             column_format: Optional[List[str]] = None,
                             range_noise_stddev: float = 0.0, angle_noise_stddev: float = 0.0,
                             t0: float = 0.0) -> int:
    """Add a moving-platform raster scan: a fixed angular fan swept along a quaternion trajectory.

    traj_quat entries are length-4 quaternions (qx,qy,qz,qw), Hamilton body->world.
    """
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")

    M = len(traj_t)
    if M == 0:
        raise ValueError("traj_t must contain at least one trajectory sample")
    if len(traj_pos) != M or len(traj_quat) != M:
        raise ValueError("traj_t, traj_pos, and traj_quat must all have the same length M")
    if pulse_rate_hz <= 0.0:
        raise ValueError("pulse_rate_hz must be greater than 0")
    if any(len(p) != 3 for p in traj_pos):
        raise ValueError("Each traj_pos entry must be a 3-element [x, y, z]")
    if any(len(q) != 4 for q in traj_quat):
        raise ValueError("Each traj_quat entry must be a 4-element [qx, qy, qz, qw]")

    t_array = (ctypes.c_double * M)(*[float(t) for t in traj_t])
    pos_flat = [float(c) for p in traj_pos for c in p]
    pos_array = (ctypes.c_float * (3 * M))(*pos_flat)
    quat_flat = [float(c) for q in traj_quat for c in q]
    quat_array = (ctypes.c_float * (4 * M))(*quat_flat)

    lever = lever_arm if lever_arm is not None else [0.0, 0.0, 0.0]
    boresight = boresight_rpy if boresight_rpy is not None else [0.0, 0.0, 0.0]
    if len(lever) != 3 or len(boresight) != 3:
        raise ValueError("lever_arm and boresight_rpy must each be 3-element arrays")
    lever_array = (ctypes.c_float * 3)(*[float(c) for c in lever])
    boresight_array = (ctypes.c_float * 3)(*[float(c) for c in boresight])

    if column_format:
        column_array = (ctypes.c_char_p * len(column_format))(
            *[c.encode('utf-8') for c in column_format]
        )
        n_cols = len(column_format)
    else:
        column_array = None
        n_cols = 0

    return helios_lib.addLiDARScanMovingRaster(
        cloud_ptr, Ntheta, theta_range[0], theta_range[1],
        Nphi, phi_range[0], phi_range[1], float(pulse_rate_hz),
        float(exit_diameter), float(beam_divergence),
        float(range_noise_stddev), float(angle_noise_stddev),
        column_array, n_cols,
        t_array, pos_array, quat_array, M,
        lever_array, boresight_array, float(t0)
    )


def addLiDARScanRisley(cloud_ptr: ctypes.POINTER(ULiDARcloud),
                       prisms: List[List[float]], refractive_index_air: float,
                       pulse_rate_hz: float,
                       traj_t: List[float], traj_pos: List[List[float]],
                       traj_rot: List[List[float]], rot_is_quaternion: bool,
                       exit_diameter: float = 0.0, beam_divergence: float = 0.0,
                       lever_arm: Optional[List[float]] = None,
                       boresight_rpy: Optional[List[float]] = None,
                       column_format: Optional[List[str]] = None,
                       range_noise_stddev: float = 0.0, angle_noise_stddev: float = 0.0,
                       t0: float = 0.0) -> int:
    """Add a rotating-Risley-prism (Livox-style rosette) scan from physical instrument parameters.

    prisms is a list of 4-element [wedge_angle, refractive_index, rotor_rate, phase] entries in
    beam-traversal order (at least one). traj_rot entries are length-4 quaternions (qx,qy,qz,qw)
    if rot_is_quaternion is True, otherwise length-3 roll/pitch/yaw Euler angles (radians).
    """
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")

    n_prisms = len(prisms)
    if n_prisms == 0:
        raise ValueError("prisms must contain at least one Risley prism")
    if any(len(p) != 4 for p in prisms):
        raise ValueError("Each prism must be a 4-element [wedge_angle, refractive_index, rotor_rate, phase]")
    if pulse_rate_hz <= 0.0:
        raise ValueError("pulse_rate_hz must be greater than 0")

    M = len(traj_t)
    if M == 0:
        raise ValueError("traj_t must contain at least one trajectory sample")
    if len(traj_pos) != M or len(traj_rot) != M:
        raise ValueError("traj_t, traj_pos, and traj_rot must all have the same length M")

    rot_stride = 4 if rot_is_quaternion else 3
    if any(len(p) != 3 for p in traj_pos):
        raise ValueError("Each traj_pos entry must be a 3-element [x, y, z]")
    if any(len(r) != rot_stride for r in traj_rot):
        raise ValueError(
            f"Each traj_rot entry must have {rot_stride} elements "
            f"({'qx,qy,qz,qw' if rot_is_quaternion else 'roll,pitch,yaw'})"
        )

    prism_flat = [float(c) for p in prisms for c in p]
    prism_array = (ctypes.c_double * (4 * n_prisms))(*prism_flat)
    t_array = (ctypes.c_double * M)(*[float(t) for t in traj_t])
    pos_flat = [float(c) for p in traj_pos for c in p]
    pos_array = (ctypes.c_float * (3 * M))(*pos_flat)
    rot_flat = [float(c) for r in traj_rot for c in r]
    rot_array = (ctypes.c_float * (rot_stride * M))(*rot_flat)

    lever = lever_arm if lever_arm is not None else [0.0, 0.0, 0.0]
    boresight = boresight_rpy if boresight_rpy is not None else [0.0, 0.0, 0.0]
    if len(lever) != 3 or len(boresight) != 3:
        raise ValueError("lever_arm and boresight_rpy must each be 3-element arrays")
    lever_array = (ctypes.c_float * 3)(*[float(c) for c in lever])
    boresight_array = (ctypes.c_float * 3)(*[float(c) for c in boresight])

    if column_format:
        column_array = (ctypes.c_char_p * len(column_format))(
            *[c.encode('utf-8') for c in column_format]
        )
        n_cols = len(column_format)
    else:
        column_array = None
        n_cols = 0

    return helios_lib.addLiDARScanRisley(
        cloud_ptr, prism_array, n_prisms, float(refractive_index_air), float(pulse_rate_hz),
        float(exit_diameter), float(beam_divergence),
        float(range_noise_stddev), float(angle_noise_stddev),
        column_array, n_cols,
        t_array, pos_array, rot_array, M, 1 if rot_is_quaternion else 0,
        lever_array, boresight_array, float(t0)
    )


def getLiDARScanMode(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int) -> int:
    """Get the acquisition mode (0 = static raster, 1 = moving raster, 2 = spinning, 3 = Risley prism)."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARScanMode(cloud_ptr, scanID)


def getLiDARScanStepsPerRev(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int) -> int:
    """Get the number of azimuth firing steps per revolution (spinning scans; 0 otherwise)."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARScanStepsPerRev(cloud_ptr, scanID)


def getLiDARScanRotationRate(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int) -> float:
    """Get the sensor-head rotation rate in revolutions/second (spinning scans; 0 otherwise)."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARScanRotationRate(cloud_ptr, scanID)


def getLiDARScanRevolutions(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int) -> float:
    """Get the number of revolutions the sensor head made (spinning scans; 0 otherwise)."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARScanRevolutions(cloud_ptr, scanID)


def getLiDARScanRisleyPrisms(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int) -> List[List[float]]:
    """Get the rotating wedge prisms of a Risley-prism scan.

    Returns a list of [wedge_angle, refractive_index, rotor_rate, phase] entries in
    beam-traversal order (empty for scans that are not Risley-prism)."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    count = helios_lib.getLiDARScanRisleyPrismCount(cloud_ptr, scanID)
    if count == 0:
        return []
    out = (ctypes.c_double * (4 * count))()
    helios_lib.getLiDARScanRisleyPrisms(cloud_ptr, scanID, out, count)
    return [[float(out[4 * i]), float(out[4 * i + 1]), float(out[4 * i + 2]), float(out[4 * i + 3])]
            for i in range(count)]


def getLiDARScanRisleyRefractiveIndexAir(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int) -> float:
    """Get the refractive index of the medium surrounding the prisms of a Risley-prism scan (1.0 for non-Risley)."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARScanRisleyRefractiveIndexAir(cloud_ptr, scanID)


def getLiDARScanReturnMode(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int) -> int:
    """Get the return-reporting mode (0 = multi, 1 = single)."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARScanReturnMode(cloud_ptr, scanID)


def setLiDARScanReturnMode(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int, return_mode: int) -> None:
    """Set the return-reporting mode (0 = multi, 1 = single)."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.setLiDARScanReturnMode(cloud_ptr, scanID, return_mode)


def getLiDARScanSingleReturnSelection(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int) -> int:
    """Get the single/limited-return selection policy (0 = strongest, 1 = first, 2 = last, 3 = strongest+last)."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARScanSingleReturnSelection(cloud_ptr, scanID)


def setLiDARScanSingleReturnSelection(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int, selection: int) -> None:
    """Set the single/limited-return selection policy (0 = strongest, 1 = first, 2 = last, 3 = strongest+last)."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.setLiDARScanSingleReturnSelection(cloud_ptr, scanID, selection)


def getLiDARScanMaxReturns(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int) -> int:
    """Get the maximum returns per pulse used in single/limited-return mode."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARScanMaxReturns(cloud_ptr, scanID)


def setLiDARScanMaxReturns(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int, max_returns: int) -> None:
    """Set the maximum returns per pulse used in single/limited-return mode (must be >= 1)."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.setLiDARScanMaxReturns(cloud_ptr, scanID, max_returns)


def getLiDARScanPulseWidth(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int) -> float:
    """Get the pulse width / range resolution (meters) of a scan (0 = use syntheticScan argument)."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARScanPulseWidth(cloud_ptr, scanID)


def setLiDARScanPulseWidth(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int, pulse_width: float) -> None:
    """Set the pulse width / range resolution (meters) of a scan (0 = use syntheticScan argument)."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.setLiDARScanPulseWidth(cloud_ptr, scanID, float(pulse_width))


def getLiDARScanDetectionThreshold(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int) -> float:
    """Get the detection threshold (energy fraction, noise floor) of a scan."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARScanDetectionThreshold(cloud_ptr, scanID)


def setLiDARScanDetectionThreshold(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int, detection_threshold: float) -> None:
    """Set the detection threshold (energy fraction, noise floor) of a scan."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.setLiDARScanDetectionThreshold(cloud_ptr, scanID, float(detection_threshold))


def getLiDARScanTiltRoll(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int) -> float:
    """Get the global scanner tilt roll angle (radians) for a scan."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARScanTiltRoll(cloud_ptr, scanID)


def getLiDARScanTiltPitch(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int) -> float:
    """Get the global scanner tilt pitch angle (radians) for a scan."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARScanTiltPitch(cloud_ptr, scanID)


def getLiDARScanAzimuthOffset(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int) -> float:
    """Get the global scanner azimuth (heading) offset angle (radians) for a scan."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARScanAzimuthOffset(cloud_ptr, scanID)


def getLiDARScanPattern(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int) -> int:
    """Get the scan pattern (0 = raster, 1 = spinning multibeam)."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARScanPattern(cloud_ptr, scanID)


def getLiDARScanBeamZenithAngles(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int) -> List[float]:
    """Get the per-channel beam zenith angles (radians) for a multibeam scan (empty for raster)."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    count = helios_lib.getLiDARScanBeamZenithAngleCount(cloud_ptr, scanID)
    if count == 0:
        return []
    out = (ctypes.c_float * count)()
    helios_lib.getLiDARScanBeamZenithAngles(cloud_ptr, scanID, out, count)
    return [float(out[i]) for i in range(count)]


def isLiDARHitMiss(cloud_ptr: ctypes.POINTER(ULiDARcloud), index: int) -> bool:
    """Return True if the hit is a miss (a transmitted beam that returned nothing)."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return bool(helios_lib.isLiDARHitMiss(cloud_ptr, index))


def lidarHasMisses(cloud_ptr: ctypes.POINTER(ULiDARcloud)) -> bool:
    """Return True if the cloud contains at least one miss."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return bool(helios_lib.lidarHasMisses(cloud_ptr))


def getLiDARMissDistance() -> float:
    """Return the LIDAR_MISS_DISTANCE constant (meters)."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARMissDistance()


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


def addLiDARHitPointsWithData(cloud_ptr: ctypes.POINTER(ULiDARcloud), scanID: int,
                              xyzs, directions, count: int, colors=None,
                              labels=None, data_values=None) -> None:
    """Bulk-ingest hit points carrying a per-hit data map in one call.

    xyzs/directions (and colors, if given) must be contiguous float32 buffers of
    shape (count, 3); directions is (radius, elevation, azimuth). labels is a
    list of data-map key names; data_values must be a contiguous float64 buffer
    of shape (count, len(labels)). Pass labels=None/empty (and data_values=None)
    to ingest with an empty data map.
    """
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")

    xyzs_ptr = xyzs.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    directions_ptr = directions.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    colors_ptr = colors.ctypes.data_as(ctypes.POINTER(ctypes.c_float)) if colors is not None else None

    labels = list(labels or [])
    n_labels = len(labels)
    if n_labels:
        labels_arr = (ctypes.c_char_p * n_labels)(*[s.encode('utf-8') for s in labels])
        values_ptr = data_values.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
    else:
        labels_arr = None
        values_ptr = None

    helios_lib.addLiDARHitPointsWithData(cloud_ptr, scanID, xyzs_ptr, directions_ptr,
                                         count, colors_ptr, labels_arr, n_labels, values_ptr)


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


def getLiDARHitOrigin(cloud_ptr: ctypes.POINTER(ULiDARcloud), index: int) -> List[float]:
    """Get the (x,y,z) beam-emission origin of a hit point.

    For moving-platform scans this is the per-pulse origin; for static scans it falls back to
    the single scan origin of the hit's scan.
    """
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")

    xyz = (ctypes.c_float * 3)()
    helios_lib.getLiDARHitOrigin(cloud_ptr, index, xyz)
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


def getLiDARHitsXYZRGB_all_np(cloud_ptr: ctypes.POINTER(ULiDARcloud), n: int):
    """Bulk-export XYZ + RGB for all hits as numpy arrays (no per-element Python).

    Returns (xyz, rgb), each an (n, 3) float32 array. Much faster than the
    list-returning variant for million-point clouds — np.frombuffer copies the
    contiguous ctypes buffer in one shot.
    """
    import numpy as np
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    xyz = (ctypes.c_float * (3 * n))()
    rgb = (ctypes.c_float * (3 * n))()
    helios_lib.getLiDARHitsXYZRGB_all(cloud_ptr, xyz, rgb, n)
    xyz_np = np.frombuffer(xyz, dtype=np.float32, count=3 * n).copy().reshape(n, 3)
    rgb_np = np.frombuffer(rgb, dtype=np.float32, count=3 * n).copy().reshape(n, 3)
    return xyz_np, rgb_np


def getLiDARHitData_all_np(cloud_ptr: ctypes.POINTER(ULiDARcloud), label: str, n: int):
    """Bulk-export a named scalar field for all hits as an (n,) float32 numpy array
    (NaN where the label is absent for a hit)."""
    import numpy as np
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    out = (ctypes.c_float * n)()
    helios_lib.getLiDARHitData_all(cloud_ptr, label.encode('utf-8'), out, n)
    return np.frombuffer(out, dtype=np.float32, count=n).copy()


def getLiDARHitDataColumn(cloud_ptr: ctypes.POINTER(ULiDARcloud), label: str, n: int,
                          absent_value: float = -9999.0) -> List[float]:
    """Bulk-export a named scalar column via the native cache-linear columnar path.

    Faster than getLiDARHitData_all for whole-field reads (single cache-linear pass over the
    contiguous native column). Entries are absent_value where the label is absent for a hit.
    Returns a list of doubles of length min(n, hit count).
    """
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")

    out = (ctypes.c_double * n)()
    helios_lib.getLiDARHitDataColumn(cloud_ptr, label.encode('utf-8'), out, n, float(absent_value))
    return list(out)


def getLiDARHitDataColumnIndex(cloud_ptr: ctypes.POINTER(ULiDARcloud), label: str) -> int:
    """Get the internal column slot index for a hit-data label (-1 if never set on any hit)."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARHitDataColumnIndex(cloud_ptr, label.encode('utf-8'))


def getLiDARHitDataColumn_np(cloud_ptr: ctypes.POINTER(ULiDARcloud), label: str, n: int,
                             absent_value: float = -9999.0):
    """Bulk-export a named scalar column as an (n,) float64 numpy array via the columnar path
    (absent_value where the label is absent for a hit)."""
    import numpy as np
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    out = (ctypes.c_double * n)()
    helios_lib.getLiDARHitDataColumn(cloud_ptr, label.encode('utf-8'), out, n, float(absent_value))
    return np.frombuffer(out, dtype=np.float64, count=n).copy()


def getLiDARHitScanID_all(cloud_ptr: ctypes.POINTER(ULiDARcloud), n: int):
    """Bulk-export the scan ID of every hit as an (n,) int32 numpy array."""
    import numpy as np
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    out = (ctypes.c_int * n)()
    helios_lib.getLiDARHitScanID_all(cloud_ptr, out, n)
    return np.frombuffer(out, dtype=np.int32, count=n).copy()


def isLiDARHitMiss_all(cloud_ptr: ctypes.POINTER(ULiDARcloud), n: int):
    """Bulk-export the miss flag of every hit as an (n,) int32 numpy array (1=miss)."""
    import numpy as np
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    out = (ctypes.c_int * n)()
    helios_lib.isLiDARHitMiss_all(cloud_ptr, out, n)
    return np.frombuffer(out, dtype=np.int32, count=n).copy()


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


def getLiDARTriangulationStats(cloud_ptr: ctypes.POINTER(ULiDARcloud)) -> dict:
    """Filter diagnostics from the most recent triangulateHitPoints() call.

    Returns a dict with candidate/dropped counts. Each dropped triangle is
    attributed to one primary reason, so:
        candidates == kept + dropped_lmax + dropped_aspect + dropped_degenerate
    where `kept` equals getLiDARTriangleCount(). All zero if triangulation has
    not been run.
    """
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    out = (ctypes.c_uint * 4)()
    helios_lib.getLiDARTriangulationStats(cloud_ptr, out)
    return {
        "candidates": int(out[0]),
        "dropped_lmax": int(out[1]),
        "dropped_aspect": int(out[2]),
        "dropped_degenerate": int(out[3]),
    }


def getLiDARTriangleVertices_all(cloud_ptr: ctypes.POINTER(ULiDARcloud), tri_count: int):
    """Bulk-export every triangle's vertices (and source scan) in one call.

    Returns (xyz_flat, scan_ids) as numpy arrays: xyz_flat is (tri_count*9,)
    float32 laid out [v0x,v0y,v0z, v1x,v1y,v1z, v2x,v2y,v2z] per triangle, and
    scan_ids is (tri_count,) int32. Returns empty arrays when tri_count is 0.
    """
    import numpy as np
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    if tri_count <= 0:
        return np.empty((0,), dtype=np.float32), np.empty((0,), dtype=np.int32)

    xyz = np.empty((tri_count * 9,), dtype=np.float32)
    scan = np.empty((tri_count,), dtype=np.int32)
    helios_lib.getLiDARTriangleVertices_all(
        cloud_ptr,
        xyz.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        scan.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
        tri_count,
    )
    return xyz, scan


def lidarSetExternalTriangulation(cloud_ptr: ctypes.POINTER(ULiDARcloud),
                                  xyz_flat, scan_ids, tri_count: int) -> None:
    """Replace the internal triangulation with an externally-supplied mesh.

    xyz_flat is (tri_count*9,) float32 laid out [v0x,v0y,v0z, v1x,v1y,v1z,
    v2x,v2y,v2z] per triangle (the same layout getLiDARTriangleVertices_all
    exports). scan_ids is (tri_count,) int32, one required source scan per
    triangle. No-op when tri_count is 0.
    """
    import numpy as np
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    if tri_count <= 0:
        return

    xyz = np.ascontiguousarray(xyz_flat, dtype=np.float32)
    scan = np.ascontiguousarray(scan_ids, dtype=np.int32)
    if xyz.size != tri_count * 9:
        raise ValueError(f"xyz_flat has {xyz.size} floats, expected {tri_count * 9} (9 per triangle)")
    if scan.size != tri_count:
        raise ValueError(f"scan_ids has {scan.size} entries, expected {tri_count} (one per triangle)")

    helios_lib.lidarSetExternalTriangulation(
        cloud_ptr,
        xyz.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        scan.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
        tri_count,
    )


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


def exportLiDARPointCloud(cloud_ptr: ctypes.POINTER(ULiDARcloud), filename: str,
                          write_header: bool = True) -> None:
    """Export point cloud to ASCII file (optionally with a '#'-prefixed column header)"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.exportLiDARPointCloud(cloud_ptr, filename.encode('utf-8'), bool(write_header))


def exportLiDARLeafAreaUncertainty(cloud_ptr: ctypes.POINTER(ULiDARcloud), filename: str) -> None:
    """Export per-voxel leaf-area sampling uncertainty to a self-describing ASCII file"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.exportLiDARLeafAreaUncertainty(cloud_ptr, filename.encode('utf-8'))


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


def addLiDARGridTerrainFollowing(cloud_ptr: ctypes.POINTER(ULiDARcloud), center: List[float],
                                 size: List[float], ndiv: List[int], rotation: float,
                                 column_z_offsets: List[float]) -> None:
    """Add a rectangular grid of voxel cells with per-column vertical offsets"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")

    if len(center) != 3:
        raise ValueError("Center must be a 3-element array [x, y, z]")
    if len(size) != 3:
        raise ValueError("Size must be a 3-element array [x, y, z]")
    if len(ndiv) != 3:
        raise ValueError("Ndiv must be a 3-element array [nx, ny, nz]")

    expected = ndiv[0] * ndiv[1]
    if len(column_z_offsets) != expected:
        raise ValueError(
            f"column_z_offsets must have length ndiv[0]*ndiv[1] = {expected}, "
            f"got {len(column_z_offsets)}"
        )

    center_array = (ctypes.c_float * 3)(*center)
    size_array = (ctypes.c_float * 3)(*size)
    ndiv_array = (ctypes.c_int * 3)(*ndiv)
    offsets_array = (ctypes.c_float * len(column_z_offsets))(*column_z_offsets)
    helios_lib.addLiDARGridTerrainFollowing(cloud_ptr, center_array, size_array, ndiv_array,
                                            rotation, offsets_array, len(column_z_offsets))


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


def getLiDARCellRotation(cloud_ptr: ctypes.POINTER(ULiDARcloud), index: int) -> float:
    """Get azimuthal rotation of a grid cell about the z-axis, in degrees"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARCellRotation(cloud_ptr, index)


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


def setLiDARCancelFlag(cloud_ptr: ctypes.POINTER(ULiDARcloud), flag) -> None:
    """Register an external cancellation flag polled during syntheticScan.

    `flag` is a ctypes.c_int (pass by ref) that, when set non-zero from another
    thread, aborts the scan's ray loop mid-trace. Pass None to clear."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    ptr = ctypes.byref(flag) if flag is not None else None
    helios_lib.setLiDARCancelFlag(cloud_ptr, ptr)


def setLiDARSyntheticScanMemoryBudget(cloud_ptr: ctypes.POINTER(ULiDARcloud), bytes: int) -> None:
    """Set the soft memory budget (bytes) for syntheticScan's transient trace buffers.

    Bounds the live ray-tracing scratch buffers so large scans are chunked rather
    than traced in one OOM-prone batch. `bytes` must be > 0; if never set, Helios
    uses an automatic path-dependent default (4 GiB CPU / 8 GiB GPU)."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.setLiDARSyntheticScanMemoryBudget(cloud_ptr, ctypes.c_size_t(bytes))


def getLiDARSyntheticScanMemoryBudget(cloud_ptr: ctypes.POINTER(ULiDARcloud)) -> int:
    """Get the soft memory budget (bytes) for syntheticScan's transient buffers.

    Returns the explicitly configured budget, or 0 if using the automatic
    path-dependent default (4 GiB CPU / 8 GiB GPU)."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return int(helios_lib.getLiDARSyntheticScanMemoryBudget(cloud_ptr))


def setLiDARSyntheticScanProgressPointer(cloud_ptr: ctypes.POINTER(ULiDARcloud), ptr) -> None:
    """Register an external per-scan progress counter polled during syntheticScan.

    `ptr` is a ctypes.c_int (pass by ref) into which syntheticScan writes the 0-based
    index of the scan currently being ray-traced, set to getScanCount() when finished.
    Pass None to clear."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    p = ctypes.byref(ptr) if ptr is not None else None
    helios_lib.setLiDARSyntheticScanProgressPointer(cloud_ptr, p)


def setLiDARProgressCallback(cloud_ptr: ctypes.POINTER(ULiDARcloud), callback) -> None:
    """Register a progress callback fired with (progress_fraction, message) during syntheticScan.

    `callback` must be a LiDARProgressCallback ctypes instance (or None to clear). The
    caller is responsible for keeping the LiDARProgressCallback alive for as long as it is
    registered (ctypes does not hold a reference)."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    # A bare None is NOT accepted for a CFUNCTYPE argtype (ctypes wants a CFunctionType instance);
    # cast None to the callback type to pass a null function pointer that clears the callback.
    cb = callback if callback is not None else ctypes.cast(None, LiDARProgressCallback)
    helios_lib.setLiDARProgressCallback(cloud_ptr, cb)


def syntheticLiDARScanDiscrete(cloud_ptr: ctypes.POINTER(ULiDARcloud),
                               context_ptr: ctypes.POINTER(UContext),
                               scan_grid_only: bool, record_misses: bool, append: bool) -> None:
    """Perform discrete-return synthetic scan with miss-recording control"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.syntheticLiDARScanDiscrete(cloud_ptr, context_ptr, scan_grid_only, record_misses, append)


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


def syntheticLiDARScanReturnMode(cloud_ptr: ctypes.POINTER(ULiDARcloud),
                                 context_ptr: ctypes.POINTER(UContext),
                                 rays_per_pulse: int,
                                 pulse_distance_threshold: float,
                                 return_mode: int,
                                 scan_grid_only: bool = False,
                                 record_misses: bool = False,
                                 append: bool = True) -> None:
    """Perform an analytic-waveform synthetic scan with an explicit return mode.

    return_mode is 0 (multi) or 1 (single); it overrides each scan's stored returnMode for this
    call only. In single mode up to each scan's maxReturns returns per pulse are reported.
    """
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.syntheticLiDARScanReturnMode(cloud_ptr, context_ptr, rays_per_pulse,
                                            pulse_distance_threshold, return_mode,
                                            scan_grid_only, record_misses, append)


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


def calculateLiDARLeafAreaUncertainty(cloud_ptr: ctypes.POINTER(ULiDARcloud),
                                      context_ptr: ctypes.POINTER(UContext),
                                      min_voxel_hits: int, element_width: float) -> None:
    """Calculate leaf area plus per-voxel sampling uncertainty (Pimont et al. 2018)"""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.calculateLiDARLeafAreaUncertainty(
        cloud_ptr, context_ptr, min_voxel_hits, float(element_width))


def calculateLiDARLeafAreaGtheta(cloud_ptr: ctypes.POINTER(ULiDARcloud),
                                 context_ptr: ctypes.POINTER(UContext),
                                 Gtheta: float, min_voxel_hits: int, element_width: float) -> None:
    """Calculate leaf area using a caller-supplied G(theta), without requiring triangulation.

    Suitable for moving-platform scans (which cannot be triangulated). Gtheta must be in (0,1]
    (0.5 = spherical leaf-angle distribution).
    """
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    helios_lib.calculateLiDARLeafAreaGtheta(
        cloud_ptr, context_ptr, float(Gtheta), min_voxel_hits, float(element_width))


def getLiDARCellBeamCount(cloud_ptr: ctypes.POINTER(ULiDARcloud), index: int) -> int:
    """Get the beam count N entering a grid cell (-1 if calculateLeafArea not run)."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARCellBeamCount(cloud_ptr, index)


def getLiDARCellRelativeDensityIndex(cloud_ptr: ctypes.POINTER(ULiDARcloud), index: int) -> float:
    """Get the relative density index I_rdi for a grid cell."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARCellRelativeDensityIndex(cloud_ptr, index)


def getLiDARCellMeanPathLength(cloud_ptr: ctypes.POINTER(ULiDARcloud), index: int) -> float:
    """Get the mean beam path length (m) through a grid cell."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARCellMeanPathLength(cloud_ptr, index)


def getLiDARCellLADVariance(cloud_ptr: ctypes.POINTER(ULiDARcloud), index: int) -> float:
    """Get the per-voxel LAD sampling variance (-1 if unavailable)."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return helios_lib.getLiDARCellLADVariance(cloud_ptr, index)


def getLiDARCellLeafAreaConfidenceInterval(cloud_ptr: ctypes.POINTER(ULiDARcloud), index: int,
                                           confidence_level: float = 0.95):
    """Single-voxel leaf-area confidence interval.

    Returns (valid, lower, upper). ``valid`` is False when the interval is gated
    out by the Pimont validity envelope (the bounds are then not trustworthy).
    """
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    out = (ctypes.c_float * 2)()
    valid = helios_lib.getLiDARCellLeafAreaConfidenceInterval(
        cloud_ptr, index, float(confidence_level), out)
    return bool(valid), float(out[0]), float(out[1])


def getLiDARGroupLADConfidenceInterval(cloud_ptr: ctypes.POINTER(ULiDARcloud),
                                       indices: List[int], confidence_level: float = 0.95):
    """Group-scale LAD confidence interval over a set of cells (recommended path).

    Returns (valid, mean_lad, lower, upper).
    """
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    if not indices:
        raise ValueError("indices must contain at least one cell index")
    n = len(indices)
    idx_array = (ctypes.c_uint * n)(*[int(i) for i in indices])
    out = (ctypes.c_float * 3)()
    valid = helios_lib.getLiDARGroupLADConfidenceInterval(
        cloud_ptr, idx_array, n, float(confidence_level), out)
    return bool(valid), float(out[0]), float(out[1]), float(out[2])


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


def isLiDARGPUAvailable(cloud_ptr: ctypes.POINTER(ULiDARcloud)) -> bool:
    """Return True if a CUDA-capable GPU is available for collision-detection acceleration."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return bool(helios_lib.isLiDARGPUAvailable(cloud_ptr))


def isLiDARGPUAccelerationEnabled(cloud_ptr: ctypes.POINTER(ULiDARcloud)) -> bool:
    """Return True if GPU acceleration is currently enabled for collision detection."""
    if not _LIDAR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LiDAR functions not available")
    return bool(helios_lib.isLiDARGPUAccelerationEnabled(cloud_ptr))


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


# ---------------------------------------------------------------------------
# helios-core 1.3.84 additions
# ---------------------------------------------------------------------------

def _require_lidar_1384() -> None:
    """Raise if the native library predates the helios-core 1.3.84 LiDAR additions."""
    if not _LIDAR_FUNCTIONS_AVAILABLE or not _LIDAR_1384_AVAILABLE:
        raise RuntimeError(
            "This LiDAR function is not available in the current native library. "
            "It requires helios-core v1.3.84 or newer; rebuild with "
            "'build_scripts/build_helios --clean'."
        )


def gapfillLiDARMissesCount(cloud_ptr) -> int:
    """Gapfill every scan, returning only the number of points added."""
    _require_lidar_1384()
    return int(helios_lib.gapfillLiDARMissesCount(cloud_ptr))


def gapfillLiDARMissesCountScan(cloud_ptr, scanID: int, gapfill_grid_only: bool,
                                add_flags: bool) -> int:
    """Gapfill one scan, returning only the number of points added."""
    _require_lidar_1384()
    return int(helios_lib.gapfillLiDARMissesCountScan(
        cloud_ptr, ctypes.c_uint(int(scanID)),
        ctypes.c_bool(bool(gapfill_grid_only)), ctypes.c_bool(bool(add_flags))
    ))


def getLiDARVirtualMissCount(cloud_ptr) -> int:
    """Number of gap-filled misses currently held in virtualized form."""
    _require_lidar_1384()
    return int(helios_lib.getLiDARVirtualMissCount(cloud_ptr))


def hasLiDARVirtualMisses(cloud_ptr) -> bool:
    """Whether any gap-filled miss is currently held in virtualized form."""
    _require_lidar_1384()
    return bool(helios_lib.hasLiDARVirtualMisses(cloud_ptr))


def materializeLiDARMisses(cloud_ptr) -> None:
    """Convert every virtualized gap-filled miss into a stored hit point."""
    _require_lidar_1384()
    helios_lib.materializeLiDARMisses(cloud_ptr)


def getLiDARScanGridDirection(cloud_ptr, scanID: int, row: int, column: int):
    """Beam direction at a scan-grid cell as (radius, elevation, azimuth)."""
    _require_lidar_1384()
    out = (ctypes.c_float * 3)()
    helios_lib.getLiDARScanGridDirection(
        cloud_ptr, ctypes.c_uint(int(scanID)), ctypes.c_int(int(row)),
        ctypes.c_int(int(column)), out
    )
    return (float(out[0]), float(out[1]), float(out[2]))


def getLiDARHitXYZColumn(cloud_ptr, count: int):
    """Read every hit's position in index order in one pass."""
    _require_lidar_1384()
    if count <= 0:
        return []
    buf = (ctypes.c_float * (3 * count))()
    helios_lib.getLiDARHitXYZColumn(cloud_ptr, buf, ctypes.c_uint(int(count)))
    return [(float(buf[3*i]), float(buf[3*i+1]), float(buf[3*i+2])) for i in range(count)]


def getLiDARHitScanIDColumn(cloud_ptr, count: int):
    """Read every hit's scan ID in index order in one pass."""
    _require_lidar_1384()
    if count <= 0:
        return []
    buf = (ctypes.c_int * count)()
    helios_lib.getLiDARHitScanIDColumn(cloud_ptr, buf, ctypes.c_uint(int(count)))
    return [int(x) for x in buf]


def estimateLiDARHitPointMemory(cloud_ptr, hit_count: int) -> int:
    """Estimated resident bytes for a cloud of ``hit_count`` points."""
    _require_lidar_1384()
    return int(helios_lib.estimateLiDARHitPointMemory(cloud_ptr, ctypes.c_ulonglong(int(hit_count))))


def setLiDARMaxHitPoints(cloud_ptr, max_hits: int) -> None:
    """Set the cap on stored hit points (0 disables the check)."""
    _require_lidar_1384()
    helios_lib.setLiDARMaxHitPoints(cloud_ptr, ctypes.c_ulonglong(int(max_hits)))


def getLiDARMaxHitPoints(cloud_ptr) -> int:
    """Current cap on stored hit points."""
    _require_lidar_1384()
    return int(helios_lib.getLiDARMaxHitPoints(cloud_ptr))


def getLiDARDefaultMaxHitPoints() -> int:
    """Default cap on the number of stored hit points in a cloud."""
    _require_lidar_1384()
    return int(helios_lib.getLiDARDefaultMaxHitPoints())


def reserveLiDARHitPoints(cloud_ptr, hit_count: int) -> None:
    """Reserve capacity for hit points and every scalar-data column at once."""
    _require_lidar_1384()
    helios_lib.reserveLiDARHitPoints(cloud_ptr, ctypes.c_ulonglong(int(hit_count)))


def setLiDARExactPathLengths(cloud_ptr, exact: bool) -> None:
    """Keep every beam path length exactly, instead of binning them."""
    _require_lidar_1384()
    helios_lib.setLiDARExactPathLengths(cloud_ptr, ctypes.c_bool(bool(exact)))


def getLiDARExactPathLengths(cloud_ptr) -> bool:
    """Whether path lengths are accumulated exactly."""
    _require_lidar_1384()
    return bool(helios_lib.getLiDARExactPathLengths(cloud_ptr))
