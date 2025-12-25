"""
Ctypes wrapper for EnergyBalanceModel C++ bindings.

This module provides low-level ctypes bindings to interface with 
the native Helios EnergyBalanceModel plugin via the C++ wrapper layer.
"""

import ctypes
from typing import List, Union

from ..plugins import helios_lib
from ..exceptions import check_helios_error

# Define the UEnergyBalanceModel struct
class UEnergyBalanceModel(ctypes.Structure):
    """Opaque structure for EnergyBalanceModel C++ class"""
    pass

# Import UContext from main wrapper to avoid type conflicts
from .UContextWrapper import UContext

# Error checking callback
def _check_error(result, func, args):
    """Automatic error checking for all energy balance functions"""
    check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage)
    return result

# Try to set up EnergyBalanceModel function prototypes
try:
    # EnergyBalanceModel creation and destruction
    helios_lib.createEnergyBalanceModel.argtypes = [ctypes.POINTER(UContext)]
    helios_lib.createEnergyBalanceModel.restype = ctypes.POINTER(UEnergyBalanceModel)
    helios_lib.createEnergyBalanceModel.errcheck = _check_error

    helios_lib.destroyEnergyBalanceModel.argtypes = [ctypes.POINTER(UEnergyBalanceModel)]
    helios_lib.destroyEnergyBalanceModel.restype = None
    # Note: destroyEnergyBalanceModel doesn't need errcheck as it doesn't fail

    # Message control
    helios_lib.enableEnergyBalanceMessages.argtypes = [ctypes.POINTER(UEnergyBalanceModel)]
    helios_lib.enableEnergyBalanceMessages.restype = None
    helios_lib.enableEnergyBalanceMessages.errcheck = _check_error

    helios_lib.disableEnergyBalanceMessages.argtypes = [ctypes.POINTER(UEnergyBalanceModel)]
    helios_lib.disableEnergyBalanceMessages.restype = None
    helios_lib.disableEnergyBalanceMessages.errcheck = _check_error

    # Core execution methods
    helios_lib.runEnergyBalance.argtypes = [ctypes.POINTER(UEnergyBalanceModel)]
    helios_lib.runEnergyBalance.restype = None
    helios_lib.runEnergyBalance.errcheck = _check_error

    helios_lib.runEnergyBalanceDynamic.argtypes = [ctypes.POINTER(UEnergyBalanceModel), ctypes.c_float]
    helios_lib.runEnergyBalanceDynamic.restype = None
    helios_lib.runEnergyBalanceDynamic.errcheck = _check_error

    helios_lib.runEnergyBalanceForUUIDs.argtypes = [
        ctypes.POINTER(UEnergyBalanceModel), 
        ctypes.POINTER(ctypes.c_uint), 
        ctypes.c_uint
    ]
    helios_lib.runEnergyBalanceForUUIDs.restype = None
    helios_lib.runEnergyBalanceForUUIDs.errcheck = _check_error

    helios_lib.runEnergyBalanceForUUIDsDynamic.argtypes = [
        ctypes.POINTER(UEnergyBalanceModel), 
        ctypes.POINTER(ctypes.c_uint), 
        ctypes.c_uint, 
        ctypes.c_float
    ]
    helios_lib.runEnergyBalanceForUUIDsDynamic.restype = None
    helios_lib.runEnergyBalanceForUUIDsDynamic.errcheck = _check_error

    # Radiation band management
    helios_lib.addEnergyBalanceRadiationBand.argtypes = [ctypes.POINTER(UEnergyBalanceModel), ctypes.c_char_p]
    helios_lib.addEnergyBalanceRadiationBand.restype = None
    helios_lib.addEnergyBalanceRadiationBand.errcheck = _check_error

    helios_lib.addEnergyBalanceRadiationBands.argtypes = [
        ctypes.POINTER(UEnergyBalanceModel), 
        ctypes.POINTER(ctypes.c_char_p), 
        ctypes.c_uint
    ]
    helios_lib.addEnergyBalanceRadiationBands.restype = None
    helios_lib.addEnergyBalanceRadiationBands.errcheck = _check_error

    # Air energy balance
    helios_lib.enableAirEnergyBalance.argtypes = [ctypes.POINTER(UEnergyBalanceModel)]
    helios_lib.enableAirEnergyBalance.restype = None
    helios_lib.enableAirEnergyBalance.errcheck = _check_error

    helios_lib.enableAirEnergyBalanceWithParameters.argtypes = [
        ctypes.POINTER(UEnergyBalanceModel), 
        ctypes.c_float, 
        ctypes.c_float
    ]
    helios_lib.enableAirEnergyBalanceWithParameters.restype = None
    helios_lib.enableAirEnergyBalanceWithParameters.errcheck = _check_error

    helios_lib.evaluateAirEnergyBalance.argtypes = [
        ctypes.POINTER(UEnergyBalanceModel), 
        ctypes.c_float, 
        ctypes.c_float
    ]
    helios_lib.evaluateAirEnergyBalance.restype = None
    helios_lib.evaluateAirEnergyBalance.errcheck = _check_error

    helios_lib.evaluateAirEnergyBalanceForUUIDs.argtypes = [
        ctypes.POINTER(UEnergyBalanceModel), 
        ctypes.POINTER(ctypes.c_uint), 
        ctypes.c_uint, 
        ctypes.c_float, 
        ctypes.c_float
    ]
    helios_lib.evaluateAirEnergyBalanceForUUIDs.restype = None
    helios_lib.evaluateAirEnergyBalanceForUUIDs.errcheck = _check_error

    # Optional output and reporting
    helios_lib.energyBalanceOptionalOutputPrimitiveData.argtypes = [ctypes.POINTER(UEnergyBalanceModel), ctypes.c_char_p]
    helios_lib.energyBalanceOptionalOutputPrimitiveData.restype = None
    helios_lib.energyBalanceOptionalOutputPrimitiveData.errcheck = _check_error

    helios_lib.printDefaultValueReport.argtypes = [ctypes.POINTER(UEnergyBalanceModel)]
    helios_lib.printDefaultValueReport.restype = None
    helios_lib.printDefaultValueReport.errcheck = _check_error

    helios_lib.printDefaultValueReportForUUIDs.argtypes = [
        ctypes.POINTER(UEnergyBalanceModel),
        ctypes.POINTER(ctypes.c_uint),
        ctypes.c_uint
    ]
    helios_lib.printDefaultValueReportForUUIDs.restype = None
    helios_lib.printDefaultValueReportForUUIDs.errcheck = _check_error

    # Mark that EnergyBalanceModel functions are available
    _ENERGY_BALANCE_FUNCTIONS_AVAILABLE = True

except AttributeError:
    # EnergyBalanceModel functions not available in current native library
    _ENERGY_BALANCE_FUNCTIONS_AVAILABLE = False

# GPU acceleration control (optional - only available when compiled with CUDA)
_GPU_ACCELERATION_AVAILABLE = False
try:
    helios_lib.enableGPUAcceleration.argtypes = [ctypes.POINTER(UEnergyBalanceModel)]
    helios_lib.enableGPUAcceleration.restype = None
    helios_lib.enableGPUAcceleration.errcheck = _check_error

    helios_lib.disableGPUAcceleration.argtypes = [ctypes.POINTER(UEnergyBalanceModel)]
    helios_lib.disableGPUAcceleration.restype = None
    helios_lib.disableGPUAcceleration.errcheck = _check_error

    helios_lib.isGPUAccelerationEnabled.argtypes = [ctypes.POINTER(UEnergyBalanceModel)]
    helios_lib.isGPUAccelerationEnabled.restype = ctypes.c_int
    helios_lib.isGPUAccelerationEnabled.errcheck = _check_error

    _GPU_ACCELERATION_AVAILABLE = True
except AttributeError:
    # GPU acceleration functions not available (library not compiled with CUDA)
    _GPU_ACCELERATION_AVAILABLE = False


# Python wrapper functions with validation and mock mode support

def createEnergyBalanceModel(context) -> ctypes.POINTER(UEnergyBalanceModel):
    """Create a new EnergyBalanceModel instance"""
    if not _ENERGY_BALANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "EnergyBalanceModel functions not available in current Helios library. "
            "Rebuild PyHelios with 'energybalance' enabled:\n"
            "  build_scripts/build_helios --plugins energybalance\n"
            "System requirements:\n"
            "  - NVIDIA GPU with CUDA support\n"
            "  - CUDA Toolkit installed"
        )
    
    return helios_lib.createEnergyBalanceModel(context)


def destroyEnergyBalanceModel(energy_model: ctypes.POINTER(UEnergyBalanceModel)) -> None:
    """Destroy EnergyBalanceModel instance"""
    if energy_model and _ENERGY_BALANCE_FUNCTIONS_AVAILABLE:
        helios_lib.destroyEnergyBalanceModel(energy_model)


def enableMessages(energy_model: ctypes.POINTER(UEnergyBalanceModel)) -> None:
    """Enable EnergyBalanceModel status messages"""
    if not _ENERGY_BALANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("EnergyBalanceModel functions not available. Rebuild with energybalance enabled.")
    if not energy_model:
        raise ValueError("EnergyBalanceModel instance is None.")
    
    helios_lib.enableEnergyBalanceMessages(energy_model)


def disableMessages(energy_model: ctypes.POINTER(UEnergyBalanceModel)) -> None:
    """Disable EnergyBalanceModel status messages"""
    if not _ENERGY_BALANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("EnergyBalanceModel functions not available. Rebuild with energybalance enabled.")
    if not energy_model:
        raise ValueError("EnergyBalanceModel instance is None.")
    
    helios_lib.disableEnergyBalanceMessages(energy_model)


def run(energy_model: ctypes.POINTER(UEnergyBalanceModel)) -> None:
    """Run energy balance model for all primitives (steady state)"""
    if not _ENERGY_BALANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("EnergyBalanceModel functions not available. Rebuild with energybalance enabled.")
    if not energy_model:
        raise ValueError("EnergyBalanceModel instance is None.")
    
    helios_lib.runEnergyBalance(energy_model)


def runDynamic(energy_model: ctypes.POINTER(UEnergyBalanceModel), dt: float) -> None:
    """Run energy balance model for all primitives (dynamic with timestep)"""
    if not _ENERGY_BALANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("EnergyBalanceModel functions not available. Rebuild with energybalance enabled.")
    if not energy_model:
        raise ValueError("EnergyBalanceModel instance is None.")
    if dt <= 0.0:
        raise ValueError("Time step must be positive.")
    
    helios_lib.runEnergyBalanceDynamic(energy_model, ctypes.c_float(dt))


def runForUUIDs(energy_model: ctypes.POINTER(UEnergyBalanceModel), uuids: List[int]) -> None:
    """Run energy balance model for specific primitives (steady state)"""
    if not _ENERGY_BALANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("EnergyBalanceModel functions not available. Rebuild with energybalance enabled.")
    if not energy_model:
        raise ValueError("EnergyBalanceModel instance is None.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")
    
    # Convert to ctypes array
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.runEnergyBalanceForUUIDs(energy_model, uuid_array, len(uuids))


def runForUUIDsDynamic(energy_model: ctypes.POINTER(UEnergyBalanceModel), uuids: List[int], dt: float) -> None:
    """Run energy balance model for specific primitives (dynamic with timestep)"""
    if not _ENERGY_BALANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("EnergyBalanceModel functions not available. Rebuild with energybalance enabled.")
    if not energy_model:
        raise ValueError("EnergyBalanceModel instance is None.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")
    if dt <= 0.0:
        raise ValueError("Time step must be positive.")
    
    # Convert to ctypes array
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.runEnergyBalanceForUUIDsDynamic(energy_model, uuid_array, len(uuids), ctypes.c_float(dt))


def addRadiationBand(energy_model: ctypes.POINTER(UEnergyBalanceModel), band: str) -> None:
    """Add a radiation band for absorbed flux calculations"""
    if not _ENERGY_BALANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("EnergyBalanceModel functions not available. Rebuild with energybalance enabled.")
    if not energy_model:
        raise ValueError("EnergyBalanceModel instance is None.")
    if not band:
        raise ValueError("Band name cannot be empty.")
    
    helios_lib.addEnergyBalanceRadiationBand(energy_model, band.encode('utf-8'))


def addRadiationBands(energy_model: ctypes.POINTER(UEnergyBalanceModel), bands: List[str]) -> None:
    """Add multiple radiation bands for absorbed flux calculations"""
    if not _ENERGY_BALANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("EnergyBalanceModel functions not available. Rebuild with energybalance enabled.")
    if not energy_model:
        raise ValueError("EnergyBalanceModel instance is None.")
    if not bands:
        raise ValueError("Bands list cannot be empty.")
    
    # Convert to ctypes array of char pointers
    encoded_bands = [band.encode('utf-8') for band in bands]
    band_array = (ctypes.c_char_p * len(encoded_bands))(*encoded_bands)
    helios_lib.addEnergyBalanceRadiationBands(energy_model, band_array, len(encoded_bands))


def enableAirEnergyBalance(energy_model: ctypes.POINTER(UEnergyBalanceModel)) -> None:
    """Enable air energy balance with automatic canopy height detection"""
    if not _ENERGY_BALANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("EnergyBalanceModel functions not available. Rebuild with energybalance enabled.")
    if not energy_model:
        raise ValueError("EnergyBalanceModel instance is None.")
    
    helios_lib.enableAirEnergyBalance(energy_model)


def enableAirEnergyBalanceWithParameters(energy_model: ctypes.POINTER(UEnergyBalanceModel), 
                                       canopy_height_m: float, reference_height_m: float) -> None:
    """Enable air energy balance with specified parameters"""
    if not _ENERGY_BALANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("EnergyBalanceModel functions not available. Rebuild with energybalance enabled.")
    if not energy_model:
        raise ValueError("EnergyBalanceModel instance is None.")
    if canopy_height_m <= 0.0:
        raise ValueError("Canopy height must be positive.")
    if reference_height_m <= 0.0:
        raise ValueError("Reference height must be positive.")
    
    helios_lib.enableAirEnergyBalanceWithParameters(energy_model, ctypes.c_float(canopy_height_m), ctypes.c_float(reference_height_m))


def evaluateAirEnergyBalance(energy_model: ctypes.POINTER(UEnergyBalanceModel), 
                           dt_sec: float, time_advance_sec: float) -> None:
    """Advance air energy balance over time for all primitives"""
    if not _ENERGY_BALANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("EnergyBalanceModel functions not available. Rebuild with energybalance enabled.")
    if not energy_model:
        raise ValueError("EnergyBalanceModel instance is None.")
    if dt_sec <= 0.0:
        raise ValueError("Time step must be positive.")
    if time_advance_sec < dt_sec:
        raise ValueError("Total time advance must be greater than or equal to time step.")
    
    helios_lib.evaluateAirEnergyBalance(energy_model, ctypes.c_float(dt_sec), ctypes.c_float(time_advance_sec))


def evaluateAirEnergyBalanceForUUIDs(energy_model: ctypes.POINTER(UEnergyBalanceModel), uuids: List[int],
                                   dt_sec: float, time_advance_sec: float) -> None:
    """Advance air energy balance over time for specific primitives"""
    if not _ENERGY_BALANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("EnergyBalanceModel functions not available. Rebuild with energybalance enabled.")
    if not energy_model:
        raise ValueError("EnergyBalanceModel instance is None.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")
    if dt_sec <= 0.0:
        raise ValueError("Time step must be positive.")
    if time_advance_sec < dt_sec:
        raise ValueError("Total time advance must be greater than or equal to time step.")
    
    # Convert to ctypes array
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.evaluateAirEnergyBalanceForUUIDs(energy_model, uuid_array, len(uuids), 
                                              ctypes.c_float(dt_sec), ctypes.c_float(time_advance_sec))


def optionalOutputPrimitiveData(energy_model: ctypes.POINTER(UEnergyBalanceModel), label: str) -> None:
    """Add optional output primitive data"""
    if not _ENERGY_BALANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("EnergyBalanceModel functions not available. Rebuild with energybalance enabled.")
    if not energy_model:
        raise ValueError("EnergyBalanceModel instance is None.")
    if not label:
        raise ValueError("Label cannot be empty.")
    
    helios_lib.energyBalanceOptionalOutputPrimitiveData(energy_model, label.encode('utf-8'))


def printDefaultValueReport(energy_model: ctypes.POINTER(UEnergyBalanceModel)) -> None:
    """Print default value report for all primitives"""
    if not _ENERGY_BALANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("EnergyBalanceModel functions not available. Rebuild with energybalance enabled.")
    if not energy_model:
        raise ValueError("EnergyBalanceModel instance is None.")
    
    helios_lib.printDefaultValueReport(energy_model)


def printDefaultValueReportForUUIDs(energy_model: ctypes.POINTER(UEnergyBalanceModel), uuids: List[int]) -> None:
    """Print default value report for specific primitives"""
    if not _ENERGY_BALANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("EnergyBalanceModel functions not available. Rebuild with energybalance enabled.")
    if not energy_model:
        raise ValueError("EnergyBalanceModel instance is None.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")
    
    # Convert to ctypes array
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.printDefaultValueReportForUUIDs(energy_model, uuid_array, len(uuids))


# GPU acceleration control functions

def enableGPUAcceleration(energy_model: ctypes.POINTER(UEnergyBalanceModel)) -> None:
    """Enable GPU acceleration for energy balance calculations"""
    if not _ENERGY_BALANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("EnergyBalanceModel functions not available. Rebuild with energybalance enabled.")
    if not _GPU_ACCELERATION_AVAILABLE:
        raise NotImplementedError(
            "GPU acceleration not available - library not compiled with CUDA support. "
            "Energy balance will use CPU mode with OpenMP parallelization."
        )
    if not energy_model:
        raise ValueError("EnergyBalanceModel instance is None.")

    helios_lib.enableGPUAcceleration(energy_model)


def disableGPUAcceleration(energy_model: ctypes.POINTER(UEnergyBalanceModel)) -> None:
    """Disable GPU acceleration and force CPU mode"""
    if not _ENERGY_BALANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("EnergyBalanceModel functions not available. Rebuild with energybalance enabled.")
    if not _GPU_ACCELERATION_AVAILABLE:
        # No-op if GPU acceleration not available - already in CPU mode
        return
    if not energy_model:
        raise ValueError("EnergyBalanceModel instance is None.")

    helios_lib.disableGPUAcceleration(energy_model)


def isGPUAccelerationEnabled(energy_model: ctypes.POINTER(UEnergyBalanceModel)) -> bool:
    """Check if GPU acceleration is currently enabled"""
    if not _ENERGY_BALANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("EnergyBalanceModel functions not available. Rebuild with energybalance enabled.")
    if not _GPU_ACCELERATION_AVAILABLE:
        return False  # GPU never enabled without CUDA
    if not energy_model:
        raise ValueError("EnergyBalanceModel instance is None.")

    result = helios_lib.isGPUAccelerationEnabled(energy_model)
    if result < 0:
        raise RuntimeError("Error checking GPU acceleration status")
    return result == 1


def isGPUAccelerationAvailable() -> bool:
    """Check if GPU acceleration functions are available in this build"""
    return _GPU_ACCELERATION_AVAILABLE


# Mock mode functions for development
if not _ENERGY_BALANCE_FUNCTIONS_AVAILABLE:
    def mock_createEnergyBalanceModel(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: EnergyBalanceModel not available. "
            "This would create an energy balance model instance with native library."
        )
    
    def mock_runEnergyBalance(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: EnergyBalanceModel methods not available. "
            "This would execute energy balance calculations with native library."
        )
    
    # Replace functions with mocks for development
    createEnergyBalanceModel = mock_createEnergyBalanceModel
    run = mock_runEnergyBalance
    runDynamic = mock_runEnergyBalance
    runForUUIDs = mock_runEnergyBalance
    runForUUIDsDynamic = mock_runEnergyBalance