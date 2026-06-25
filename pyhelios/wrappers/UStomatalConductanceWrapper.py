"""
Ctypes wrapper for StomatalConductanceModel C++ bindings.

This module provides low-level ctypes bindings to interface with 
the native Helios StomatalConductanceModel plugin via the C++ wrapper layer.
"""

import ctypes
from typing import List, Union

from ..plugins import helios_lib
from ..exceptions import check_helios_error

# Define the UStomatalConductanceModel struct
class UStomatalConductanceModel(ctypes.Structure):
    """Opaque structure for StomatalConductanceModel C++ class"""
    pass

# Import UContext from main wrapper to avoid type conflicts
from .UContextWrapper import UContext

# Error checking callback
def _check_error(result, func, args):
    """Automatic error checking for all stomatal conductance functions"""
    check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage, helios_lib.clearError)
    return result

# Try to set up StomatalConductanceModel function prototypes
try:
    # StomatalConductanceModel creation and destruction
    helios_lib.createStomatalConductanceModel.argtypes = [ctypes.POINTER(UContext)]
    helios_lib.createStomatalConductanceModel.restype = ctypes.POINTER(UStomatalConductanceModel)
    helios_lib.createStomatalConductanceModel.errcheck = _check_error

    helios_lib.destroyStomatalConductanceModel.argtypes = [ctypes.POINTER(UStomatalConductanceModel)]
    helios_lib.destroyStomatalConductanceModel.restype = None
    # Note: destroyStomatalConductanceModel doesn't need errcheck as it doesn't fail

    # Message control
    helios_lib.enableStomatalConductanceMessages.argtypes = [ctypes.POINTER(UStomatalConductanceModel)]
    helios_lib.enableStomatalConductanceMessages.restype = None
    helios_lib.enableStomatalConductanceMessages.errcheck = _check_error

    helios_lib.disableStomatalConductanceMessages.argtypes = [ctypes.POINTER(UStomatalConductanceModel)]
    helios_lib.disableStomatalConductanceMessages.restype = None
    helios_lib.disableStomatalConductanceMessages.errcheck = _check_error

    # Core execution methods
    helios_lib.runStomatalConductanceModel.argtypes = [ctypes.POINTER(UStomatalConductanceModel)]
    helios_lib.runStomatalConductanceModel.restype = None
    helios_lib.runStomatalConductanceModel.errcheck = _check_error

    helios_lib.runStomatalConductanceModelDynamic.argtypes = [ctypes.POINTER(UStomatalConductanceModel), ctypes.c_float]
    helios_lib.runStomatalConductanceModelDynamic.restype = None
    helios_lib.runStomatalConductanceModelDynamic.errcheck = _check_error

    helios_lib.runStomatalConductanceModelForUUIDs.argtypes = [
        ctypes.POINTER(UStomatalConductanceModel), 
        ctypes.POINTER(ctypes.c_uint), 
        ctypes.c_uint
    ]
    helios_lib.runStomatalConductanceModelForUUIDs.restype = None
    helios_lib.runStomatalConductanceModelForUUIDs.errcheck = _check_error

    helios_lib.runStomatalConductanceModelForUUIDsDynamic.argtypes = [
        ctypes.POINTER(UStomatalConductanceModel), 
        ctypes.POINTER(ctypes.c_uint), 
        ctypes.c_uint, 
        ctypes.c_float
    ]
    helios_lib.runStomatalConductanceModelForUUIDsDynamic.restype = None
    helios_lib.runStomatalConductanceModelForUUIDsDynamic.errcheck = _check_error

    # BWB Model Coefficient Functions
    helios_lib.setStomatalConductanceBWBCoefficients.argtypes = [ctypes.POINTER(UStomatalConductanceModel), ctypes.c_float, ctypes.c_float]
    helios_lib.setStomatalConductanceBWBCoefficients.restype = None
    helios_lib.setStomatalConductanceBWBCoefficients.errcheck = _check_error

    helios_lib.setStomatalConductanceBWBCoefficientsForUUIDs.argtypes = [
        ctypes.POINTER(UStomatalConductanceModel), 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.POINTER(ctypes.c_uint), 
        ctypes.c_uint
    ]
    helios_lib.setStomatalConductanceBWBCoefficientsForUUIDs.restype = None
    helios_lib.setStomatalConductanceBWBCoefficientsForUUIDs.errcheck = _check_error

    # BBL Model Coefficient Functions
    helios_lib.setStomatalConductanceBBLCoefficients.argtypes = [ctypes.POINTER(UStomatalConductanceModel), ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.setStomatalConductanceBBLCoefficients.restype = None
    helios_lib.setStomatalConductanceBBLCoefficients.errcheck = _check_error

    helios_lib.setStomatalConductanceBBLCoefficientsForUUIDs.argtypes = [
        ctypes.POINTER(UStomatalConductanceModel), 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.POINTER(ctypes.c_uint), 
        ctypes.c_uint
    ]
    helios_lib.setStomatalConductanceBBLCoefficientsForUUIDs.restype = None
    helios_lib.setStomatalConductanceBBLCoefficientsForUUIDs.errcheck = _check_error

    # MOPT Model Coefficient Functions
    helios_lib.setStomatalConductanceMOPTCoefficients.argtypes = [ctypes.POINTER(UStomatalConductanceModel), ctypes.c_float, ctypes.c_float]
    helios_lib.setStomatalConductanceMOPTCoefficients.restype = None
    helios_lib.setStomatalConductanceMOPTCoefficients.errcheck = _check_error

    helios_lib.setStomatalConductanceMOPTCoefficientsForUUIDs.argtypes = [
        ctypes.POINTER(UStomatalConductanceModel), 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.POINTER(ctypes.c_uint), 
        ctypes.c_uint
    ]
    helios_lib.setStomatalConductanceMOPTCoefficientsForUUIDs.restype = None
    helios_lib.setStomatalConductanceMOPTCoefficientsForUUIDs.errcheck = _check_error

    # BMF Model Coefficient Functions
    helios_lib.setStomatalConductanceBMFCoefficients.argtypes = [ctypes.POINTER(UStomatalConductanceModel), ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.setStomatalConductanceBMFCoefficients.restype = None
    helios_lib.setStomatalConductanceBMFCoefficients.errcheck = _check_error

    helios_lib.setStomatalConductanceBMFCoefficientsForUUIDs.argtypes = [
        ctypes.POINTER(UStomatalConductanceModel), 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.POINTER(ctypes.c_uint), 
        ctypes.c_uint
    ]
    helios_lib.setStomatalConductanceBMFCoefficientsForUUIDs.restype = None
    helios_lib.setStomatalConductanceBMFCoefficientsForUUIDs.errcheck = _check_error

    # BB Model Coefficient Functions
    helios_lib.setStomatalConductanceBBCoefficients.argtypes = [
        ctypes.POINTER(UStomatalConductanceModel), 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.c_float
    ]
    helios_lib.setStomatalConductanceBBCoefficients.restype = None
    helios_lib.setStomatalConductanceBBCoefficients.errcheck = _check_error

    helios_lib.setStomatalConductanceBBCoefficientsForUUIDs.argtypes = [
        ctypes.POINTER(UStomatalConductanceModel), 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.POINTER(ctypes.c_uint), 
        ctypes.c_uint
    ]
    helios_lib.setStomatalConductanceBBCoefficientsForUUIDs.restype = None
    helios_lib.setStomatalConductanceBBCoefficientsForUUIDs.errcheck = _check_error

    # Species Library Functions
    helios_lib.setStomatalConductanceBMFCoefficientsFromLibrary.argtypes = [ctypes.POINTER(UStomatalConductanceModel), ctypes.c_char_p]
    helios_lib.setStomatalConductanceBMFCoefficientsFromLibrary.restype = None
    helios_lib.setStomatalConductanceBMFCoefficientsFromLibrary.errcheck = _check_error

    helios_lib.setStomatalConductanceBMFCoefficientsFromLibraryForUUIDs.argtypes = [
        ctypes.POINTER(UStomatalConductanceModel), 
        ctypes.c_char_p, 
        ctypes.POINTER(ctypes.c_uint), 
        ctypes.c_uint
    ]
    helios_lib.setStomatalConductanceBMFCoefficientsFromLibraryForUUIDs.restype = None
    helios_lib.setStomatalConductanceBMFCoefficientsFromLibraryForUUIDs.errcheck = _check_error

    # Dynamic Time Constants
    helios_lib.setStomatalConductanceDynamicTimeConstants.argtypes = [ctypes.POINTER(UStomatalConductanceModel), ctypes.c_float, ctypes.c_float]
    helios_lib.setStomatalConductanceDynamicTimeConstants.restype = None
    helios_lib.setStomatalConductanceDynamicTimeConstants.errcheck = _check_error

    helios_lib.setStomatalConductanceDynamicTimeConstantsForUUIDs.argtypes = [
        ctypes.POINTER(UStomatalConductanceModel), 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.POINTER(ctypes.c_uint), 
        ctypes.c_uint
    ]
    helios_lib.setStomatalConductanceDynamicTimeConstantsForUUIDs.restype = None
    helios_lib.setStomatalConductanceDynamicTimeConstantsForUUIDs.errcheck = _check_error

    # Utility Functions
    helios_lib.addStomatalConductanceOptionalOutput.argtypes = [ctypes.POINTER(UStomatalConductanceModel), ctypes.c_char_p]
    helios_lib.addStomatalConductanceOptionalOutput.restype = None
    helios_lib.addStomatalConductanceOptionalOutput.errcheck = _check_error

    helios_lib.printStomatalConductanceDefaultValueReport.argtypes = [ctypes.POINTER(UStomatalConductanceModel)]
    helios_lib.printStomatalConductanceDefaultValueReport.restype = None
    helios_lib.printStomatalConductanceDefaultValueReport.errcheck = _check_error

    helios_lib.printStomatalConductanceDefaultValueReportForUUIDs.argtypes = [
        ctypes.POINTER(UStomatalConductanceModel), 
        ctypes.POINTER(ctypes.c_uint), 
        ctypes.c_uint
    ]
    helios_lib.printStomatalConductanceDefaultValueReportForUUIDs.restype = None
    helios_lib.printStomatalConductanceDefaultValueReportForUUIDs.errcheck = _check_error

    # Mark that StomatalConductanceModel functions are available
    _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE = True

except AttributeError:
    # StomatalConductanceModel functions not available in current native library
    _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE = False


# Python wrapper functions with validation and mock mode support

def createStomatalConductanceModel(context) -> ctypes.POINTER(UStomatalConductanceModel):
    """Create a new StomatalConductanceModel instance"""
    if not _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "StomatalConductanceModel functions not available in current Helios library. "
            "Rebuild PyHelios with 'stomatalconductance' enabled:\n"
            "  build_scripts/build_helios --plugins stomatalconductance\n"
            "System requirements:\n"
            "  - Platforms: Windows, Linux, macOS\n"
            "  - No GPU required\n"
            "  - No special dependencies"
        )

    # Explicit type coercion to fix Windows ctypes type identity issue
    # Ensures context is properly cast to the expected ctypes.POINTER(UContext) type
    if context is not None:
        context_ptr = ctypes.cast(context, ctypes.POINTER(UContext))
        return helios_lib.createStomatalConductanceModel(context_ptr)
    else:
        raise ValueError("Context cannot be None")


def destroyStomatalConductanceModel(model: ctypes.POINTER(UStomatalConductanceModel)) -> None:
    """Destroy StomatalConductanceModel instance"""
    if model and _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
        helios_lib.destroyStomatalConductanceModel(model)


def enableMessages(model: ctypes.POINTER(UStomatalConductanceModel)) -> None:
    """Enable StomatalConductanceModel status messages"""
    if not _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("StomatalConductanceModel functions not available. Rebuild with stomatalconductance enabled.")
    if not model:
        raise ValueError("StomatalConductanceModel instance is None.")
    
    helios_lib.enableStomatalConductanceMessages(model)


def disableMessages(model: ctypes.POINTER(UStomatalConductanceModel)) -> None:
    """Disable StomatalConductanceModel status messages"""
    if not _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("StomatalConductanceModel functions not available. Rebuild with stomatalconductance enabled.")
    if not model:
        raise ValueError("StomatalConductanceModel instance is None.")
    
    helios_lib.disableStomatalConductanceMessages(model)


def run(model: ctypes.POINTER(UStomatalConductanceModel)) -> None:
    """Run stomatal conductance model for all primitives (steady state)"""
    if not _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("StomatalConductanceModel functions not available. Rebuild with stomatalconductance enabled.")
    if not model:
        raise ValueError("StomatalConductanceModel instance is None.")
    
    helios_lib.runStomatalConductanceModel(model)


def runDynamic(model: ctypes.POINTER(UStomatalConductanceModel), dt: float) -> None:
    """Run stomatal conductance model for all primitives (dynamic with timestep)"""
    if not _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("StomatalConductanceModel functions not available. Rebuild with stomatalconductance enabled.")
    if not model:
        raise ValueError("StomatalConductanceModel instance is None.")
    if dt <= 0.0:
        raise ValueError("Time step must be positive.")
    
    helios_lib.runStomatalConductanceModelDynamic(model, ctypes.c_float(dt))


def runForUUIDs(model: ctypes.POINTER(UStomatalConductanceModel), uuids: List[int]) -> None:
    """Run stomatal conductance model for specific primitives (steady state)"""
    if not _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("StomatalConductanceModel functions not available. Rebuild with stomatalconductance enabled.")
    if not model:
        raise ValueError("StomatalConductanceModel instance is None.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")
    
    # Convert to ctypes array
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.runStomatalConductanceModelForUUIDs(model, uuid_array, len(uuids))


def runForUUIDsDynamic(model: ctypes.POINTER(UStomatalConductanceModel), uuids: List[int], dt: float) -> None:
    """Run stomatal conductance model for specific primitives (dynamic with timestep)"""
    if not _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("StomatalConductanceModel functions not available. Rebuild with stomatalconductance enabled.")
    if not model:
        raise ValueError("StomatalConductanceModel instance is None.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")
    if dt <= 0.0:
        raise ValueError("Time step must be positive.")
    
    # Convert to ctypes array
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.runStomatalConductanceModelForUUIDsDynamic(model, uuid_array, len(uuids), ctypes.c_float(dt))


# BWB Model Functions
def setBWBCoefficients(model: ctypes.POINTER(UStomatalConductanceModel), gs0: float, a1: float) -> None:
    """Set Ball-Woodrow-Berry model coefficients for all primitives"""
    if not _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("StomatalConductanceModel functions not available. Rebuild with stomatalconductance enabled.")
    if not model:
        raise ValueError("StomatalConductanceModel instance is None.")
    
    helios_lib.setStomatalConductanceBWBCoefficients(model, ctypes.c_float(gs0), ctypes.c_float(a1))


def setBWBCoefficientsForUUIDs(model: ctypes.POINTER(UStomatalConductanceModel), gs0: float, a1: float, uuids: List[int]) -> None:
    """Set Ball-Woodrow-Berry model coefficients for specific primitives"""
    if not _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("StomatalConductanceModel functions not available. Rebuild with stomatalconductance enabled.")
    if not model:
        raise ValueError("StomatalConductanceModel instance is None.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")
    
    # Convert to ctypes array
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.setStomatalConductanceBWBCoefficientsForUUIDs(model, ctypes.c_float(gs0), ctypes.c_float(a1), uuid_array, len(uuids))


# BBL Model Functions
def setBBLCoefficients(model: ctypes.POINTER(UStomatalConductanceModel), gs0: float, a1: float, D0: float) -> None:
    """Set Ball-Berry-Leuning model coefficients for all primitives"""
    if not _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("StomatalConductanceModel functions not available. Rebuild with stomatalconductance enabled.")
    if not model:
        raise ValueError("StomatalConductanceModel instance is None.")
    
    helios_lib.setStomatalConductanceBBLCoefficients(model, ctypes.c_float(gs0), ctypes.c_float(a1), ctypes.c_float(D0))


def setBBLCoefficientsForUUIDs(model: ctypes.POINTER(UStomatalConductanceModel), gs0: float, a1: float, D0: float, uuids: List[int]) -> None:
    """Set Ball-Berry-Leuning model coefficients for specific primitives"""
    if not _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("StomatalConductanceModel functions not available. Rebuild with stomatalconductance enabled.")
    if not model:
        raise ValueError("StomatalConductanceModel instance is None.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")
    
    # Convert to ctypes array
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.setStomatalConductanceBBLCoefficientsForUUIDs(model, ctypes.c_float(gs0), ctypes.c_float(a1), ctypes.c_float(D0), uuid_array, len(uuids))


# MOPT Model Functions
def setMOPTCoefficients(model: ctypes.POINTER(UStomatalConductanceModel), gs0: float, g1: float) -> None:
    """Set Medlyn et al. optimality model coefficients for all primitives"""
    if not _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("StomatalConductanceModel functions not available. Rebuild with stomatalconductance enabled.")
    if not model:
        raise ValueError("StomatalConductanceModel instance is None.")
    
    helios_lib.setStomatalConductanceMOPTCoefficients(model, ctypes.c_float(gs0), ctypes.c_float(g1))


def setMOPTCoefficientsForUUIDs(model: ctypes.POINTER(UStomatalConductanceModel), gs0: float, g1: float, uuids: List[int]) -> None:
    """Set Medlyn et al. optimality model coefficients for specific primitives"""
    if not _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("StomatalConductanceModel functions not available. Rebuild with stomatalconductance enabled.")
    if not model:
        raise ValueError("StomatalConductanceModel instance is None.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")
    
    # Convert to ctypes array
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.setStomatalConductanceMOPTCoefficientsForUUIDs(model, ctypes.c_float(gs0), ctypes.c_float(g1), uuid_array, len(uuids))


# BMF Model Functions
def setBMFCoefficients(model: ctypes.POINTER(UStomatalConductanceModel), Em: float, i0: float, k: float, b: float) -> None:
    """Set Buckley-Mott-Farquhar model coefficients for all primitives"""
    if not _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("StomatalConductanceModel functions not available. Rebuild with stomatalconductance enabled.")
    if not model:
        raise ValueError("StomatalConductanceModel instance is None.")
    
    helios_lib.setStomatalConductanceBMFCoefficients(model, ctypes.c_float(Em), ctypes.c_float(i0), ctypes.c_float(k), ctypes.c_float(b))


def setBMFCoefficientsForUUIDs(model: ctypes.POINTER(UStomatalConductanceModel), Em: float, i0: float, k: float, b: float, uuids: List[int]) -> None:
    """Set Buckley-Mott-Farquhar model coefficients for specific primitives"""
    if not _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("StomatalConductanceModel functions not available. Rebuild with stomatalconductance enabled.")
    if not model:
        raise ValueError("StomatalConductanceModel instance is None.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")
    
    # Convert to ctypes array
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.setStomatalConductanceBMFCoefficientsForUUIDs(model, ctypes.c_float(Em), ctypes.c_float(i0), ctypes.c_float(k), ctypes.c_float(b), uuid_array, len(uuids))


# BB Model Functions
def setBBCoefficients(model: ctypes.POINTER(UStomatalConductanceModel), pi_0: float, pi_m: float, theta: float, sigma: float, chi: float) -> None:
    """Set Bailey model coefficients for all primitives"""
    if not _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("StomatalConductanceModel functions not available. Rebuild with stomatalconductance enabled.")
    if not model:
        raise ValueError("StomatalConductanceModel instance is None.")
    
    helios_lib.setStomatalConductanceBBCoefficients(model, ctypes.c_float(pi_0), ctypes.c_float(pi_m), ctypes.c_float(theta), ctypes.c_float(sigma), ctypes.c_float(chi))


def setBBCoefficientsForUUIDs(model: ctypes.POINTER(UStomatalConductanceModel), pi_0: float, pi_m: float, theta: float, sigma: float, chi: float, uuids: List[int]) -> None:
    """Set Bailey model coefficients for specific primitives"""
    if not _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("StomatalConductanceModel functions not available. Rebuild with stomatalconductance enabled.")
    if not model:
        raise ValueError("StomatalConductanceModel instance is None.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")
    
    # Convert to ctypes array
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.setStomatalConductanceBBCoefficientsForUUIDs(model, ctypes.c_float(pi_0), ctypes.c_float(pi_m), ctypes.c_float(theta), ctypes.c_float(sigma), ctypes.c_float(chi), uuid_array, len(uuids))


# Species Library Functions
def setBMFCoefficientsFromLibrary(model: ctypes.POINTER(UStomatalConductanceModel), species: str) -> None:
    """Set BMF model coefficients using species library for all primitives"""
    if not _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("StomatalConductanceModel functions not available. Rebuild with stomatalconductance enabled.")
    if not model:
        raise ValueError("StomatalConductanceModel instance is None.")
    if not species:
        raise ValueError("Species name cannot be empty.")
    
    helios_lib.setStomatalConductanceBMFCoefficientsFromLibrary(model, species.encode('utf-8'))


def setBMFCoefficientsFromLibraryForUUIDs(model: ctypes.POINTER(UStomatalConductanceModel), species: str, uuids: List[int]) -> None:
    """Set BMF model coefficients using species library for specific primitives"""
    if not _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("StomatalConductanceModel functions not available. Rebuild with stomatalconductance enabled.")
    if not model:
        raise ValueError("StomatalConductanceModel instance is None.")
    if not species:
        raise ValueError("Species name cannot be empty.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")
    
    # Convert to ctypes array
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.setStomatalConductanceBMFCoefficientsFromLibraryForUUIDs(model, species.encode('utf-8'), uuid_array, len(uuids))


# Dynamic Time Constants
def setDynamicTimeConstants(model: ctypes.POINTER(UStomatalConductanceModel), tau_open: float, tau_close: float) -> None:
    """Set dynamic time constants for all primitives"""
    if not _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("StomatalConductanceModel functions not available. Rebuild with stomatalconductance enabled.")
    if not model:
        raise ValueError("StomatalConductanceModel instance is None.")
    if tau_open <= 0.0:
        raise ValueError("Opening time constant must be positive.")
    if tau_close <= 0.0:
        raise ValueError("Closing time constant must be positive.")
    
    helios_lib.setStomatalConductanceDynamicTimeConstants(model, ctypes.c_float(tau_open), ctypes.c_float(tau_close))


def setDynamicTimeConstantsForUUIDs(model: ctypes.POINTER(UStomatalConductanceModel), tau_open: float, tau_close: float, uuids: List[int]) -> None:
    """Set dynamic time constants for specific primitives"""
    if not _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("StomatalConductanceModel functions not available. Rebuild with stomatalconductance enabled.")
    if not model:
        raise ValueError("StomatalConductanceModel instance is None.")
    if tau_open <= 0.0:
        raise ValueError("Opening time constant must be positive.")
    if tau_close <= 0.0:
        raise ValueError("Closing time constant must be positive.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")
    
    # Convert to ctypes array
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.setStomatalConductanceDynamicTimeConstantsForUUIDs(model, ctypes.c_float(tau_open), ctypes.c_float(tau_close), uuid_array, len(uuids))


# Utility Functions
def optionalOutputPrimitiveData(model: ctypes.POINTER(UStomatalConductanceModel), label: str) -> None:
    """Add optional output primitive data"""
    if not _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("StomatalConductanceModel functions not available. Rebuild with stomatalconductance enabled.")
    if not model:
        raise ValueError("StomatalConductanceModel instance is None.")
    if not label:
        raise ValueError("Label cannot be empty.")
    
    helios_lib.addStomatalConductanceOptionalOutput(model, label.encode('utf-8'))


def printDefaultValueReport(model: ctypes.POINTER(UStomatalConductanceModel)) -> None:
    """Print default value report for all primitives"""
    if not _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("StomatalConductanceModel functions not available. Rebuild with stomatalconductance enabled.")
    if not model:
        raise ValueError("StomatalConductanceModel instance is None.")
    
    helios_lib.printStomatalConductanceDefaultValueReport(model)


def printDefaultValueReportForUUIDs(model: ctypes.POINTER(UStomatalConductanceModel), uuids: List[int]) -> None:
    """Print default value report for specific primitives"""
    if not _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("StomatalConductanceModel functions not available. Rebuild with stomatalconductance enabled.")
    if not model:
        raise ValueError("StomatalConductanceModel instance is None.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")
    
    # Convert to ctypes array
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.printStomatalConductanceDefaultValueReportForUUIDs(model, uuid_array, len(uuids))


# Mock mode functions for development
if not _STOMATAL_CONDUCTANCE_FUNCTIONS_AVAILABLE:
    def mock_createStomatalConductanceModel(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: StomatalConductanceModel not available. "
            "This would create a stomatal conductance model instance with native library."
        )
    
    def mock_runStomatalConductanceModel(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: StomatalConductanceModel methods not available. "
            "This would execute stomatal conductance calculations with native library."
        )
    
    # Replace functions with mocks for development
    createStomatalConductanceModel = mock_createStomatalConductanceModel
    run = mock_runStomatalConductanceModel
    runDynamic = mock_runStomatalConductanceModel
    runForUUIDs = mock_runStomatalConductanceModel
    runForUUIDsDynamic = mock_runStomatalConductanceModel