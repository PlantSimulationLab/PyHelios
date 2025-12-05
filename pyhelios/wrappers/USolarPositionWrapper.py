"""
ctypes interface for SolarPosition plugin functionality.

This module provides the low-level ctypes interface to the SolarPosition plugin,
handling solar angle calculations, radiation modeling, and time-dependent solar functions.
"""

import ctypes
from typing import List, Optional, Tuple
from ..plugins import helios_lib
from ..exceptions import check_helios_error


# Define SolarPosition structure
class USolarPosition(ctypes.Structure):
    """Opaque structure for SolarPosition C++ class"""
    pass


# Try to set up SolarPosition function prototypes with availability detection
try:
    # SolarPosition creation/destruction
    helios_lib.createSolarPosition.argtypes = [ctypes.c_void_p]
    helios_lib.createSolarPosition.restype = ctypes.POINTER(USolarPosition)
    
    helios_lib.createSolarPositionWithCoordinates.argtypes = [ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.createSolarPositionWithCoordinates.restype = ctypes.POINTER(USolarPosition)
    
    helios_lib.destroySolarPosition.argtypes = [ctypes.POINTER(USolarPosition)]
    helios_lib.destroySolarPosition.restype = None
    
    # Solar angle calculations - basic angles in degrees
    helios_lib.getSunElevation.argtypes = [ctypes.POINTER(USolarPosition)]
    helios_lib.getSunElevation.restype = ctypes.c_float
    
    helios_lib.getSunZenith.argtypes = [ctypes.POINTER(USolarPosition)]
    helios_lib.getSunZenith.restype = ctypes.c_float
    
    helios_lib.getSunAzimuth.argtypes = [ctypes.POINTER(USolarPosition)]
    helios_lib.getSunAzimuth.restype = ctypes.c_float
    
    # Solar direction vectors
    helios_lib.getSunDirectionVector.argtypes = [ctypes.POINTER(USolarPosition)]
    helios_lib.getSunDirectionVector.restype = ctypes.POINTER(ctypes.c_float)
    
    helios_lib.getSunDirectionSpherical.argtypes = [ctypes.POINTER(USolarPosition)]
    helios_lib.getSunDirectionSpherical.restype = ctypes.POINTER(ctypes.c_float)
    
    # Solar flux calculations - all take atmospheric parameters
    helios_lib.getSolarFlux.argtypes = [ctypes.POINTER(USolarPosition), ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.getSolarFlux.restype = ctypes.c_float
    
    helios_lib.getSolarFluxPAR.argtypes = [ctypes.POINTER(USolarPosition), ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.getSolarFluxPAR.restype = ctypes.c_float
    
    helios_lib.getSolarFluxNIR.argtypes = [ctypes.POINTER(USolarPosition), ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.getSolarFluxNIR.restype = ctypes.c_float
    
    helios_lib.getDiffuseFraction.argtypes = [ctypes.POINTER(USolarPosition), ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.getDiffuseFraction.restype = ctypes.c_float
    
    # Time calculations - returns Time structure components
    helios_lib.getSunriseTime.argtypes = [ctypes.POINTER(USolarPosition), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    helios_lib.getSunriseTime.restype = None
    
    helios_lib.getSunsetTime.argtypes = [ctypes.POINTER(USolarPosition), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    helios_lib.getSunsetTime.restype = None
    
    # Calibration functions
    helios_lib.calibrateTurbidityFromTimeseries.argtypes = [ctypes.POINTER(USolarPosition), ctypes.c_char_p]
    helios_lib.calibrateTurbidityFromTimeseries.restype = ctypes.c_float
    
    helios_lib.enableCloudCalibration.argtypes = [ctypes.POINTER(USolarPosition), ctypes.c_char_p]
    helios_lib.enableCloudCalibration.restype = None
    
    helios_lib.disableCloudCalibration.argtypes = [ctypes.POINTER(USolarPosition)]
    helios_lib.disableCloudCalibration.restype = None

    # Atmospheric condition management (modern API)
    helios_lib.setAtmosphericConditions.argtypes = [ctypes.POINTER(USolarPosition), ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.setAtmosphericConditions.restype = None

    helios_lib.getAtmosphericConditions.argtypes = [ctypes.POINTER(USolarPosition), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.getAtmosphericConditions.restype = None

    # Modern parameter-free flux methods (use atmospheric conditions from Context)
    helios_lib.getSolarFluxFromState.argtypes = [ctypes.POINTER(USolarPosition)]
    helios_lib.getSolarFluxFromState.restype = ctypes.c_float

    helios_lib.getSolarFluxPARFromState.argtypes = [ctypes.POINTER(USolarPosition)]
    helios_lib.getSolarFluxPARFromState.restype = ctypes.c_float

    helios_lib.getSolarFluxNIRFromState.argtypes = [ctypes.POINTER(USolarPosition)]
    helios_lib.getSolarFluxNIRFromState.restype = ctypes.c_float

    helios_lib.getDiffuseFractionFromState.argtypes = [ctypes.POINTER(USolarPosition)]
    helios_lib.getDiffuseFractionFromState.restype = ctypes.c_float

    helios_lib.getAmbientLongwaveFluxFromState.argtypes = [ctypes.POINTER(USolarPosition)]
    helios_lib.getAmbientLongwaveFluxFromState.restype = ctypes.c_float

    # SSolar-GOA Spectral Solar Model Methods
    helios_lib.calculateDirectSolarSpectrum.argtypes = [ctypes.POINTER(USolarPosition), ctypes.c_char_p, ctypes.c_float]
    helios_lib.calculateDirectSolarSpectrum.restype = None

    helios_lib.calculateDiffuseSolarSpectrum.argtypes = [ctypes.POINTER(USolarPosition), ctypes.c_char_p, ctypes.c_float]
    helios_lib.calculateDiffuseSolarSpectrum.restype = None

    helios_lib.calculateGlobalSolarSpectrum.argtypes = [ctypes.POINTER(USolarPosition), ctypes.c_char_p, ctypes.c_float]
    helios_lib.calculateGlobalSolarSpectrum.restype = None

    # Prague Sky Model Methods (v1.3.59)
    helios_lib.enablePragueSkyModel.argtypes = [ctypes.POINTER(USolarPosition)]
    helios_lib.enablePragueSkyModel.restype = None

    helios_lib.isPragueSkyModelEnabled.argtypes = [ctypes.POINTER(USolarPosition)]
    helios_lib.isPragueSkyModelEnabled.restype = ctypes.c_bool

    helios_lib.updatePragueSkyModel.argtypes = [ctypes.POINTER(USolarPosition), ctypes.c_float]
    helios_lib.updatePragueSkyModel.restype = None

    helios_lib.pragueSkyModelNeedsUpdate.argtypes = [ctypes.POINTER(USolarPosition), ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.pragueSkyModelNeedsUpdate.restype = ctypes.c_bool

    # Note: Additional utility functions can be added here as needed

    _SOLARPOSITION_FUNCTIONS_AVAILABLE = True
    
except AttributeError:
    _SOLARPOSITION_FUNCTIONS_AVAILABLE = False


# Error checking callback
def _check_error(result, func, args):
    """Automatic error checking for all SolarPosition functions"""
    check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage)
    return result


# Set up automatic error checking
if _SOLARPOSITION_FUNCTIONS_AVAILABLE:
    helios_lib.createSolarPosition.errcheck = _check_error
    helios_lib.createSolarPositionWithCoordinates.errcheck = _check_error
    helios_lib.getSunElevation.errcheck = _check_error
    helios_lib.getSunZenith.errcheck = _check_error
    helios_lib.getSunAzimuth.errcheck = _check_error
    helios_lib.getSunDirectionVector.errcheck = _check_error
    helios_lib.getSunDirectionSpherical.errcheck = _check_error
    helios_lib.getSolarFlux.errcheck = _check_error
    helios_lib.getSolarFluxPAR.errcheck = _check_error
    helios_lib.getSolarFluxNIR.errcheck = _check_error
    helios_lib.getDiffuseFraction.errcheck = _check_error
    helios_lib.getSunriseTime.errcheck = _check_error
    helios_lib.getSunsetTime.errcheck = _check_error
    helios_lib.calibrateTurbidityFromTimeseries.errcheck = _check_error
    helios_lib.enableCloudCalibration.errcheck = _check_error
    helios_lib.disableCloudCalibration.errcheck = _check_error
    helios_lib.calculateDirectSolarSpectrum.errcheck = _check_error
    helios_lib.calculateDiffuseSolarSpectrum.errcheck = _check_error
    helios_lib.calculateGlobalSolarSpectrum.errcheck = _check_error
    # Prague Sky Model error checking (v1.3.59)
    helios_lib.enablePragueSkyModel.errcheck = _check_error
    helios_lib.isPragueSkyModelEnabled.errcheck = _check_error
    helios_lib.updatePragueSkyModel.errcheck = _check_error
    helios_lib.pragueSkyModelNeedsUpdate.errcheck = _check_error
    # Modern API error checking
    helios_lib.setAtmosphericConditions.errcheck = _check_error
    helios_lib.getAtmosphericConditions.errcheck = _check_error
    helios_lib.getSolarFluxFromState.errcheck = _check_error
    helios_lib.getSolarFluxPARFromState.errcheck = _check_error
    helios_lib.getSolarFluxNIRFromState.errcheck = _check_error
    helios_lib.getDiffuseFractionFromState.errcheck = _check_error
    helios_lib.getAmbientLongwaveFluxFromState.errcheck = _check_error


# Wrapper functions
def createSolarPosition(context) -> ctypes.POINTER(USolarPosition):
    """Create SolarPosition instance using Context location"""
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "SolarPosition functions not available in current Helios library. "
            "Rebuild PyHelios with 'solarposition' enabled:\n"
            "  build_scripts/build_helios --plugins solarposition"
        )
    
    return helios_lib.createSolarPosition(context)


def createSolarPositionWithCoordinates(context, utc_hours: float, latitude_deg: float, longitude_deg: float) -> ctypes.POINTER(USolarPosition):
    """Create SolarPosition instance with explicit coordinates"""
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "SolarPosition functions not available in current Helios library. "
            "Rebuild PyHelios with 'solarposition' enabled:\n"
            "  build_scripts/build_helios --plugins solarposition"
        )
    
    return helios_lib.createSolarPositionWithCoordinates(context, utc_hours, latitude_deg, longitude_deg)


def destroySolarPosition(solar_pos: ctypes.POINTER(USolarPosition)) -> None:
    """Destroy SolarPosition instance"""
    if solar_pos and _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        helios_lib.destroySolarPosition(solar_pos)


# Solar angle calculations
def getSunElevation(solar_pos: ctypes.POINTER(USolarPosition)) -> float:
    """Get sun elevation angle in degrees"""
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")
    
    return helios_lib.getSunElevation(solar_pos)


def getSunZenith(solar_pos: ctypes.POINTER(USolarPosition)) -> float:
    """Get sun zenith angle in degrees"""
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")
    
    return helios_lib.getSunZenith(solar_pos)


def getSunAzimuth(solar_pos: ctypes.POINTER(USolarPosition)) -> float:
    """Get sun azimuth angle in degrees"""
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")
    
    return helios_lib.getSunAzimuth(solar_pos)


# Solar direction vectors
def getSunDirectionVector(solar_pos: ctypes.POINTER(USolarPosition)) -> List[float]:
    """Get sun direction as 3D vector [x, y, z]"""
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")
    
    ptr = helios_lib.getSunDirectionVector(solar_pos)
    if ptr:
        return list(ptr[:3])  # Return first 3 elements as list
    else:
        return [0.0, 0.0, 0.0]


def getSunDirectionSpherical(solar_pos: ctypes.POINTER(USolarPosition)) -> List[float]:
    """Get sun direction as spherical coordinates [radius, elevation, azimuth]"""
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")
    
    ptr = helios_lib.getSunDirectionSpherical(solar_pos)
    if ptr:
        return list(ptr[:3])  # Return first 3 elements as list (radius, elevation, azimuth)
    else:
        return [1.0, 0.0, 0.0]


# Solar flux calculations
def getSolarFlux(solar_pos: ctypes.POINTER(USolarPosition), pressure_Pa: float, temperature_K: float, humidity_rel: float, turbidity: float) -> float:
    """Get total solar flux with atmospheric parameters"""
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")
    
    return helios_lib.getSolarFlux(solar_pos, pressure_Pa, temperature_K, humidity_rel, turbidity)


def getSolarFluxPAR(solar_pos: ctypes.POINTER(USolarPosition), pressure_Pa: float, temperature_K: float, humidity_rel: float, turbidity: float) -> float:
    """Get PAR solar flux with atmospheric parameters"""
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")
    
    return helios_lib.getSolarFluxPAR(solar_pos, pressure_Pa, temperature_K, humidity_rel, turbidity)


def getSolarFluxNIR(solar_pos: ctypes.POINTER(USolarPosition), pressure_Pa: float, temperature_K: float, humidity_rel: float, turbidity: float) -> float:
    """Get NIR solar flux with atmospheric parameters"""
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")
    
    return helios_lib.getSolarFluxNIR(solar_pos, pressure_Pa, temperature_K, humidity_rel, turbidity)


def getDiffuseFraction(solar_pos: ctypes.POINTER(USolarPosition), pressure_Pa: float, temperature_K: float, humidity_rel: float, turbidity: float) -> float:
    """Get diffuse fraction of solar radiation with atmospheric parameters"""
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")
    
    return helios_lib.getDiffuseFraction(solar_pos, pressure_Pa, temperature_K, humidity_rel, turbidity)


# Time calculations
def getSunriseTime(solar_pos: ctypes.POINTER(USolarPosition)) -> Tuple[int, int, int]:
    """Get sunrise time as (hour, minute, second)"""
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")
    
    hour = ctypes.c_int()
    minute = ctypes.c_int()
    second = ctypes.c_int()
    
    helios_lib.getSunriseTime(solar_pos, ctypes.byref(hour), ctypes.byref(minute), ctypes.byref(second))
    
    return (hour.value, minute.value, second.value)


def getSunsetTime(solar_pos: ctypes.POINTER(USolarPosition)) -> Tuple[int, int, int]:
    """Get sunset time as (hour, minute, second)"""
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")
    
    hour = ctypes.c_int()
    minute = ctypes.c_int()
    second = ctypes.c_int()
    
    helios_lib.getSunsetTime(solar_pos, ctypes.byref(hour), ctypes.byref(minute), ctypes.byref(second))
    
    return (hour.value, minute.value, second.value)


# Calibration functions
def calibrateTurbidityFromTimeseries(solar_pos: ctypes.POINTER(USolarPosition), timeseries_label: str) -> None:
    """Calibrate turbidity from timeseries data"""
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")
    
    label_encoded = timeseries_label.encode('utf-8')
    helios_lib.calibrateTurbidityFromTimeseries(solar_pos, label_encoded)


def enableCloudCalibration(solar_pos: ctypes.POINTER(USolarPosition), timeseries_label: str) -> None:
    """Enable cloud calibration using timeseries data"""
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")
    
    label_encoded = timeseries_label.encode('utf-8')
    helios_lib.enableCloudCalibration(solar_pos, label_encoded)


def disableCloudCalibration(solar_pos: ctypes.POINTER(USolarPosition)) -> None:
    """Disable cloud calibration"""
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")

    helios_lib.disableCloudCalibration(solar_pos)


# Atmospheric condition management (modern API)
def setAtmosphericConditions(solar_pos: ctypes.POINTER(USolarPosition), pressure_Pa: float, temperature_K: float, humidity_rel: float, turbidity: float) -> None:
    """Set atmospheric conditions in Context global data"""
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")

    helios_lib.setAtmosphericConditions(solar_pos, pressure_Pa, temperature_K, humidity_rel, turbidity)


def getAtmosphericConditions(solar_pos: ctypes.POINTER(USolarPosition)) -> Tuple[float, float, float, float]:
    """Get atmospheric conditions from Context global data"""
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")

    pressure = ctypes.c_float()
    temperature = ctypes.c_float()
    humidity = ctypes.c_float()
    turbidity = ctypes.c_float()

    helios_lib.getAtmosphericConditions(solar_pos, ctypes.byref(pressure), ctypes.byref(temperature), ctypes.byref(humidity), ctypes.byref(turbidity))

    return (pressure.value, temperature.value, humidity.value, turbidity.value)


# Modern parameter-free flux methods (use atmospheric conditions from Context)
def getSolarFluxFromState(solar_pos: ctypes.POINTER(USolarPosition)) -> float:
    """Get total solar flux using atmospheric conditions from Context"""
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")

    return helios_lib.getSolarFluxFromState(solar_pos)


def getSolarFluxPARFromState(solar_pos: ctypes.POINTER(USolarPosition)) -> float:
    """Get PAR solar flux using atmospheric conditions from Context"""
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")

    return helios_lib.getSolarFluxPARFromState(solar_pos)


def getSolarFluxNIRFromState(solar_pos: ctypes.POINTER(USolarPosition)) -> float:
    """Get NIR solar flux using atmospheric conditions from Context"""
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")

    return helios_lib.getSolarFluxNIRFromState(solar_pos)


def getDiffuseFractionFromState(solar_pos: ctypes.POINTER(USolarPosition)) -> float:
    """Get diffuse fraction using atmospheric conditions from Context"""
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")

    return helios_lib.getDiffuseFractionFromState(solar_pos)


def getAmbientLongwaveFluxFromState(solar_pos: ctypes.POINTER(USolarPosition)) -> float:
    """Get ambient longwave flux using atmospheric conditions from Context"""
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")

    return helios_lib.getAmbientLongwaveFluxFromState(solar_pos)


# SSolar-GOA Spectral Solar Model Methods
def calculateDirectSolarSpectrum(solar_pos: ctypes.POINTER(USolarPosition), label: str, resolution_nm: float = 1.0) -> None:
    """
    Calculate direct beam solar spectrum using SSolar-GOA model and store in Context global data.

    Args:
        solar_pos: SolarPosition instance pointer
        label: Label for storing spectral data in Context global data
        resolution_nm: Wavelength resolution in nm (default: 1.0, valid range: 1.0-2300.0)

    Note:
        - Computes spectral irradiance normal to sun direction from 300-2600 nm
        - Stores result as std::vector<helios::vec2> (wavelength_nm, W/m²/nm) in Context global data
        - Uses SSolar-GOA model (Cachorro et al. 2022)
    """
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")

    label_encoded = label.encode('utf-8')
    helios_lib.calculateDirectSolarSpectrum(solar_pos, label_encoded, resolution_nm)


def calculateDiffuseSolarSpectrum(solar_pos: ctypes.POINTER(USolarPosition), label: str, resolution_nm: float = 1.0) -> None:
    """
    Calculate diffuse solar spectrum using SSolar-GOA model and store in Context global data.

    Args:
        solar_pos: SolarPosition instance pointer
        label: Label for storing spectral data in Context global data
        resolution_nm: Wavelength resolution in nm (default: 1.0, valid range: 1.0-2300.0)

    Note:
        - Computes diffuse spectral irradiance on horizontal surface from 300-2600 nm
        - Stores result as std::vector<helios::vec2> (wavelength_nm, W/m²/nm) in Context global data
        - Uses SSolar-GOA model (Cachorro et al. 2022)
    """
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")

    label_encoded = label.encode('utf-8')
    helios_lib.calculateDiffuseSolarSpectrum(solar_pos, label_encoded, resolution_nm)


def calculateGlobalSolarSpectrum(solar_pos: ctypes.POINTER(USolarPosition), label: str, resolution_nm: float = 1.0) -> None:
    """
    Calculate global (total) solar spectrum using SSolar-GOA model and store in Context global data.

    Args:
        solar_pos: SolarPosition instance pointer
        label: Label for storing spectral data in Context global data
        resolution_nm: Wavelength resolution in nm (default: 1.0, valid range: 1.0-2300.0)

    Note:
        - Computes global spectral irradiance on horizontal surface from 300-2600 nm
        - Stores result as std::vector<helios::vec2> (wavelength_nm, W/m²/nm) in Context global data
        - Uses SSolar-GOA model (Cachorro et al. 2022)
    """
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")

    label_encoded = label.encode('utf-8')
    helios_lib.calculateGlobalSolarSpectrum(solar_pos, label_encoded, resolution_nm)


# Prague Sky Model Methods (v1.3.59)
def enablePragueSkyModel(solar_pos: ctypes.POINTER(USolarPosition)) -> None:
    """
    Enable Prague sky model for atmospheric sky radiance computation.

    The Prague model provides physically-based sky radiance distributions accounting for
    Rayleigh and Mie scattering across the 360-1480 nm spectral range.

    Args:
        solar_pos: SolarPosition instance pointer

    Note:
        After enabling, call updatePragueSkyModel() to compute and store spectral-angular
        parameters in Context global data. Requires 27 MB data file:
        plugins/solarposition/lib/prague_sky_model/PragueSkyModelReduced.dat
    """
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")

    helios_lib.enablePragueSkyModel(solar_pos)


def isPragueSkyModelEnabled(solar_pos: ctypes.POINTER(USolarPosition)) -> bool:
    """
    Check if Prague sky model is enabled.

    Args:
        solar_pos: SolarPosition instance pointer

    Returns:
        True if Prague model has been enabled, False otherwise
    """
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")

    return helios_lib.isPragueSkyModelEnabled(solar_pos)


def updatePragueSkyModel(solar_pos: ctypes.POINTER(USolarPosition), ground_albedo: float = 0.33) -> None:
    """
    Update Prague sky model and store spectral-angular parameters in Context.

    This is a computationally intensive operation (~1100 model queries with OpenMP parallelization).
    Use pragueSkyModelNeedsUpdate() for lazy evaluation to avoid unnecessary updates.

    Args:
        solar_pos: SolarPosition instance pointer
        ground_albedo: Ground albedo value (default: 0.33)

    Stores in Context global data:
        - "prague_sky_spectral_params": vec<float> size 1350 (225 wavelengths × 6 parameters)
        - "prague_sky_sun_direction": vec3 sun direction
        - "prague_sky_visibility_km": float visibility
        - "prague_sky_ground_albedo": float ground albedo
        - "prague_sky_valid": int validity flag (1=valid, 0=invalid)

    Note:
        Reads turbidity from Context atmospheric conditions for sky calculations.
    """
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")

    helios_lib.updatePragueSkyModel(solar_pos, ground_albedo)


def pragueSkyModelNeedsUpdate(solar_pos: ctypes.POINTER(USolarPosition),
                               ground_albedo: float = 0.33,
                               sun_tolerance: float = 0.01,
                               turbidity_tolerance: float = 0.02,
                               albedo_tolerance: float = 0.05) -> bool:
    """
    Check if Prague sky model update is needed based on changed conditions.

    Enables lazy evaluation to avoid expensive Prague updates when conditions haven't
    changed significantly.

    Args:
        solar_pos: SolarPosition instance pointer
        ground_albedo: Current ground albedo (default: 0.33)
        sun_tolerance: Threshold for sun direction changes (default: 0.01 ≈ 0.57°)
        turbidity_tolerance: Relative threshold for turbidity (default: 0.02 = 2%)
        albedo_tolerance: Threshold for albedo changes (default: 0.05 = 5%)

    Returns:
        True if updatePragueSkyModel() should be called, False if cached data is still valid

    Note:
        Reads turbidity from Context atmospheric conditions for comparison.
    """
    if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("SolarPosition methods not available. Rebuild with solarposition enabled.")

    return helios_lib.pragueSkyModelNeedsUpdate(solar_pos, ground_albedo, sun_tolerance,
                                                 turbidity_tolerance, albedo_tolerance)


# Note: Additional utility functions can be added here as needed


# Mock mode functions for development when plugin unavailable
if not _SOLARPOSITION_FUNCTIONS_AVAILABLE:
    def mock_createSolarPosition(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: SolarPosition not available. "
            "This would create a solar position instance with native library."
        )
    
    def mock_getSunElevation(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: SolarPosition method not available. "
            "This would calculate sun elevation angle with native library."
        )
    
    def mock_getSolarFlux(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: SolarPosition method not available. "
            "This would calculate solar flux with native library."
        )
    
    # Replace functions with mocks for development
    createSolarPosition = mock_createSolarPosition
    getSunElevation = mock_getSunElevation
    getSolarFlux = mock_getSolarFlux