"""
Ctypes wrapper for PhotosynthesisModel C++ bindings.

This module provides low-level ctypes bindings to interface with 
the native Helios PhotosynthesisModel plugin via the C++ wrapper layer.
"""

import ctypes
from typing import List, Optional, Union

from ..plugins import helios_lib
from ..exceptions import check_helios_error

# Define the UPhotosynthesisModel struct
class UPhotosynthesisModel(ctypes.Structure):
    """Opaque structure for PhotosynthesisModel C++ class"""
    pass

# Import UContext from main wrapper to avoid type conflicts
from .UContextWrapper import UContext

# Error checking callback
def _check_error(result, func, args):
    """Automatic error checking for all photosynthesis functions"""
    check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage)
    return result

# Try to set up PhotosynthesisModel function prototypes
try:
    # PhotosynthesisModel creation and destruction
    helios_lib.createPhotosynthesisModel.argtypes = [ctypes.POINTER(UContext)]
    helios_lib.createPhotosynthesisModel.restype = ctypes.POINTER(UPhotosynthesisModel)
    helios_lib.createPhotosynthesisModel.errcheck = _check_error

    helios_lib.destroyPhotosynthesisModel.argtypes = [ctypes.POINTER(UPhotosynthesisModel)]
    helios_lib.destroyPhotosynthesisModel.restype = None
    # Note: destroyPhotosynthesisModel doesn't need errcheck as it doesn't fail

    # Model type configuration
    helios_lib.setPhotosynthesisModelTypeEmpirical.argtypes = [ctypes.POINTER(UPhotosynthesisModel)]
    helios_lib.setPhotosynthesisModelTypeEmpirical.restype = None
    helios_lib.setPhotosynthesisModelTypeEmpirical.errcheck = _check_error

    helios_lib.setPhotosynthesisModelTypeFarquhar.argtypes = [ctypes.POINTER(UPhotosynthesisModel)]
    helios_lib.setPhotosynthesisModelTypeFarquhar.restype = None
    helios_lib.setPhotosynthesisModelTypeFarquhar.errcheck = _check_error

    # Model execution
    helios_lib.runPhotosynthesisModel.argtypes = [ctypes.POINTER(UPhotosynthesisModel)]
    helios_lib.runPhotosynthesisModel.restype = None
    helios_lib.runPhotosynthesisModel.errcheck = _check_error

    helios_lib.runPhotosynthesisModelForUUIDs.argtypes = [
        ctypes.POINTER(UPhotosynthesisModel), 
        ctypes.POINTER(ctypes.c_uint), 
        ctypes.c_uint
    ]
    helios_lib.runPhotosynthesisModelForUUIDs.restype = None
    helios_lib.runPhotosynthesisModelForUUIDs.errcheck = _check_error

    # Species library integration
    helios_lib.setFarquharCoefficientsFromLibrary.argtypes = [ctypes.POINTER(UPhotosynthesisModel), ctypes.c_char_p]
    helios_lib.setFarquharCoefficientsFromLibrary.restype = None
    helios_lib.setFarquharCoefficientsFromLibrary.errcheck = _check_error

    helios_lib.setFarquharCoefficientsFromLibraryForUUIDs.argtypes = [
        ctypes.POINTER(UPhotosynthesisModel), 
        ctypes.c_char_p, 
        ctypes.POINTER(ctypes.c_uint), 
        ctypes.c_uint
    ]
    helios_lib.setFarquharCoefficientsFromLibraryForUUIDs.restype = None
    helios_lib.setFarquharCoefficientsFromLibraryForUUIDs.errcheck = _check_error

    helios_lib.getFarquharCoefficientsFromLibrary.argtypes = [
        ctypes.POINTER(UPhotosynthesisModel), 
        ctypes.c_char_p, 
        ctypes.POINTER(ctypes.c_float), 
        ctypes.c_uint
    ]
    helios_lib.getFarquharCoefficientsFromLibrary.restype = None
    helios_lib.getFarquharCoefficientsFromLibrary.errcheck = _check_error

    # Model parameter configuration - Empirical
    helios_lib.setEmpiricalModelCoefficients.argtypes = [
        ctypes.POINTER(UPhotosynthesisModel), 
        ctypes.POINTER(ctypes.c_float), 
        ctypes.c_uint
    ]
    helios_lib.setEmpiricalModelCoefficients.restype = None
    helios_lib.setEmpiricalModelCoefficients.errcheck = _check_error

    helios_lib.setEmpiricalModelCoefficientsForUUIDs.argtypes = [
        ctypes.POINTER(UPhotosynthesisModel), 
        ctypes.POINTER(ctypes.c_float), 
        ctypes.c_uint, 
        ctypes.POINTER(ctypes.c_uint), 
        ctypes.c_uint
    ]
    helios_lib.setEmpiricalModelCoefficientsForUUIDs.restype = None
    helios_lib.setEmpiricalModelCoefficientsForUUIDs.errcheck = _check_error

    # Model parameter configuration - Farquhar
    helios_lib.setFarquharModelCoefficients.argtypes = [
        ctypes.POINTER(UPhotosynthesisModel), 
        ctypes.POINTER(ctypes.c_float), 
        ctypes.c_uint
    ]
    helios_lib.setFarquharModelCoefficients.restype = None
    helios_lib.setFarquharModelCoefficients.errcheck = _check_error

    helios_lib.setFarquharModelCoefficientsForUUIDs.argtypes = [
        ctypes.POINTER(UPhotosynthesisModel), 
        ctypes.POINTER(ctypes.c_float), 
        ctypes.c_uint, 
        ctypes.POINTER(ctypes.c_uint), 
        ctypes.c_uint
    ]
    helios_lib.setFarquharModelCoefficientsForUUIDs.restype = None
    helios_lib.setFarquharModelCoefficientsForUUIDs.errcheck = _check_error

    # Individual Farquhar parameter setters
    helios_lib.setFarquharVcmax.argtypes = [
        ctypes.POINTER(UPhotosynthesisModel), 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.POINTER(ctypes.c_uint), 
        ctypes.c_uint
    ]
    helios_lib.setFarquharVcmax.restype = None
    helios_lib.setFarquharVcmax.errcheck = _check_error

    helios_lib.setFarquharJmax.argtypes = [
        ctypes.POINTER(UPhotosynthesisModel), 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.POINTER(ctypes.c_uint), 
        ctypes.c_uint
    ]
    helios_lib.setFarquharJmax.restype = None
    helios_lib.setFarquharJmax.errcheck = _check_error

    helios_lib.setFarquharRd.argtypes = [
        ctypes.POINTER(UPhotosynthesisModel), 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.POINTER(ctypes.c_uint), 
        ctypes.c_uint
    ]
    helios_lib.setFarquharRd.restype = None
    helios_lib.setFarquharRd.errcheck = _check_error

    helios_lib.setFarquharQuantumEfficiency.argtypes = [
        ctypes.POINTER(UPhotosynthesisModel), 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.POINTER(ctypes.c_uint), 
        ctypes.c_uint
    ]
    helios_lib.setFarquharQuantumEfficiency.restype = None
    helios_lib.setFarquharQuantumEfficiency.errcheck = _check_error

    helios_lib.setFarquharLightResponseCurvature.argtypes = [
        ctypes.POINTER(UPhotosynthesisModel), 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.c_float, 
        ctypes.POINTER(ctypes.c_uint), 
        ctypes.c_uint
    ]
    helios_lib.setFarquharLightResponseCurvature.restype = None
    helios_lib.setFarquharLightResponseCurvature.errcheck = _check_error

    # Parameter getters
    helios_lib.getEmpiricalModelCoefficients.argtypes = [
        ctypes.POINTER(UPhotosynthesisModel), 
        ctypes.c_uint, 
        ctypes.POINTER(ctypes.c_float), 
        ctypes.c_uint
    ]
    helios_lib.getEmpiricalModelCoefficients.restype = None
    helios_lib.getEmpiricalModelCoefficients.errcheck = _check_error

    helios_lib.getFarquharModelCoefficients.argtypes = [
        ctypes.POINTER(UPhotosynthesisModel), 
        ctypes.c_uint, 
        ctypes.POINTER(ctypes.c_float), 
        ctypes.c_uint
    ]
    helios_lib.getFarquharModelCoefficients.restype = None
    helios_lib.getFarquharModelCoefficients.errcheck = _check_error

    # Model configuration and utilities
    helios_lib.enablePhotosynthesisMessages.argtypes = [ctypes.POINTER(UPhotosynthesisModel)]
    helios_lib.enablePhotosynthesisMessages.restype = None
    helios_lib.enablePhotosynthesisMessages.errcheck = _check_error

    helios_lib.disablePhotosynthesisMessages.argtypes = [ctypes.POINTER(UPhotosynthesisModel)]
    helios_lib.disablePhotosynthesisMessages.restype = None
    helios_lib.disablePhotosynthesisMessages.errcheck = _check_error

    helios_lib.optionalOutputPhotosynthesisPrimitiveData.argtypes = [ctypes.POINTER(UPhotosynthesisModel), ctypes.c_char_p]
    helios_lib.optionalOutputPhotosynthesisPrimitiveData.restype = None
    helios_lib.optionalOutputPhotosynthesisPrimitiveData.errcheck = _check_error

    helios_lib.printPhotosynthesisDefaultValueReport.argtypes = [ctypes.POINTER(UPhotosynthesisModel)]
    helios_lib.printPhotosynthesisDefaultValueReport.restype = None
    helios_lib.printPhotosynthesisDefaultValueReport.errcheck = _check_error

    helios_lib.printPhotosynthesisDefaultValueReportForUUIDs.argtypes = [
        ctypes.POINTER(UPhotosynthesisModel),
        ctypes.POINTER(ctypes.c_uint),
        ctypes.c_uint
    ]
    helios_lib.printPhotosynthesisDefaultValueReportForUUIDs.restype = None
    helios_lib.printPhotosynthesisDefaultValueReportForUUIDs.errcheck = _check_error

    # Mark that PhotosynthesisModel functions are available
    _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE = True

except AttributeError:
    # PhotosynthesisModel functions not available in current native library
    _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE = False


# Number of floats in the C4 model coefficient flat-array layout (see
# pyhelios_wrapper_photosynthesis.h for the per-index meaning).
C4_COEFFICIENTS_COUNT = 43

# C4 model + Farquhar mesophyll-conductance bindings were added in helios-core v1.3.72.
# Probe separately so wheels built against older libraries keep the rest of the API working.
_C4_FUNCTIONS_AVAILABLE = False
try:
    helios_lib.setPhotosynthesisModelTypeC4.argtypes = [ctypes.POINTER(UPhotosynthesisModel)]
    helios_lib.setPhotosynthesisModelTypeC4.restype = None
    helios_lib.setPhotosynthesisModelTypeC4.errcheck = _check_error

    helios_lib.setFarquharMesophyllConductance.argtypes = [
        ctypes.POINTER(UPhotosynthesisModel),
        ctypes.c_float,
        ctypes.c_float,
        ctypes.c_float,
        ctypes.c_float,
        ctypes.POINTER(ctypes.c_uint),
        ctypes.c_uint,
    ]
    helios_lib.setFarquharMesophyllConductance.restype = None
    helios_lib.setFarquharMesophyllConductance.errcheck = _check_error

    helios_lib.setC4CoefficientsFromLibrary.argtypes = [ctypes.POINTER(UPhotosynthesisModel), ctypes.c_char_p]
    helios_lib.setC4CoefficientsFromLibrary.restype = None
    helios_lib.setC4CoefficientsFromLibrary.errcheck = _check_error

    helios_lib.setC4CoefficientsFromLibraryForUUIDs.argtypes = [
        ctypes.POINTER(UPhotosynthesisModel),
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_uint),
        ctypes.c_uint,
    ]
    helios_lib.setC4CoefficientsFromLibraryForUUIDs.restype = None
    helios_lib.setC4CoefficientsFromLibraryForUUIDs.errcheck = _check_error

    helios_lib.getC4CoefficientsFromLibrary.argtypes = [
        ctypes.POINTER(UPhotosynthesisModel),
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_uint,
    ]
    helios_lib.getC4CoefficientsFromLibrary.restype = None
    helios_lib.getC4CoefficientsFromLibrary.errcheck = _check_error

    helios_lib.setC4ModelCoefficients.argtypes = [
        ctypes.POINTER(UPhotosynthesisModel),
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_uint,
    ]
    helios_lib.setC4ModelCoefficients.restype = None
    helios_lib.setC4ModelCoefficients.errcheck = _check_error

    helios_lib.setC4ModelCoefficientsForUUIDs.argtypes = [
        ctypes.POINTER(UPhotosynthesisModel),
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_uint),
        ctypes.c_uint,
    ]
    helios_lib.setC4ModelCoefficientsForUUIDs.restype = None
    helios_lib.setC4ModelCoefficientsForUUIDs.errcheck = _check_error

    helios_lib.setC4ModelCoefficientsForMaterial.argtypes = [
        ctypes.POINTER(UPhotosynthesisModel),
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_uint,
    ]
    helios_lib.setC4ModelCoefficientsForMaterial.restype = None
    helios_lib.setC4ModelCoefficientsForMaterial.errcheck = _check_error

    helios_lib.setC4CoefficientsFromLibraryForMaterial.argtypes = [
        ctypes.POINTER(UPhotosynthesisModel),
        ctypes.c_char_p,
        ctypes.c_char_p,
    ]
    helios_lib.setC4CoefficientsFromLibraryForMaterial.restype = None
    helios_lib.setC4CoefficientsFromLibraryForMaterial.errcheck = _check_error

    helios_lib.getC4ModelCoefficients.argtypes = [
        ctypes.POINTER(UPhotosynthesisModel),
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_uint,
    ]
    helios_lib.getC4ModelCoefficients.restype = None
    helios_lib.getC4ModelCoefficients.errcheck = _check_error

    helios_lib.setPhotosynthesisCm.argtypes = [
        ctypes.POINTER(UPhotosynthesisModel),
        ctypes.c_float,
        ctypes.POINTER(ctypes.c_uint),
        ctypes.c_uint,
    ]
    helios_lib.setPhotosynthesisCm.restype = None
    helios_lib.setPhotosynthesisCm.errcheck = _check_error

    _C4_FUNCTIONS_AVAILABLE = True
except AttributeError:
    _C4_FUNCTIONS_AVAILABLE = False


def _require_c4_available():
    if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("PhotosynthesisModel functions not available. Rebuild with photosynthesis enabled.")
    if not _C4_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "C4 photosynthesis bindings require helios-core v1.3.72 or newer. "
            "Please rebuild PyHelios with `build_scripts/build_helios --clean`."
        )


# Python wrapper functions with validation and mock mode support

def createPhotosynthesisModel(context) -> ctypes.POINTER(UPhotosynthesisModel):
    """Create a new PhotosynthesisModel instance"""
    if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PhotosynthesisModel functions not available in current Helios library. "
            "Rebuild PyHelios with 'photosynthesis' enabled:\n"
            "  build_scripts/build_helios --plugins photosynthesis\n"
            "System requirements:\n"
            "  - Cross-platform compatible (no special dependencies)\n"
            "  - CPU-only computation (no GPU required)"
        )
    
    return helios_lib.createPhotosynthesisModel(context)


def destroyPhotosynthesisModel(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel)) -> None:
    """Destroy PhotosynthesisModel instance"""
    if photosynthesis_model and _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        helios_lib.destroyPhotosynthesisModel(photosynthesis_model)


# Model type configuration

def setModelTypeEmpirical(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel)) -> None:
    """Set photosynthesis model to use empirical model"""
    if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("PhotosynthesisModel functions not available. Rebuild with photosynthesis enabled.")
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    
    helios_lib.setPhotosynthesisModelTypeEmpirical(photosynthesis_model)


def setModelTypeFarquhar(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel)) -> None:
    """Set photosynthesis model to use Farquhar-von Caemmerer-Berry model"""
    if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("PhotosynthesisModel functions not available. Rebuild with photosynthesis enabled.")
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    
    helios_lib.setPhotosynthesisModelTypeFarquhar(photosynthesis_model)


# Model execution

def run(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel)) -> None:
    """Run photosynthesis model for all primitives"""
    if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("PhotosynthesisModel functions not available. Rebuild with photosynthesis enabled.")
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    
    helios_lib.runPhotosynthesisModel(photosynthesis_model)


def runForUUIDs(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel), uuids: List[int]) -> None:
    """Run photosynthesis model for specific primitives"""
    if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("PhotosynthesisModel functions not available. Rebuild with photosynthesis enabled.")
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")
    
    # Convert to ctypes array
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.runPhotosynthesisModelForUUIDs(photosynthesis_model, uuid_array, len(uuids))


# Species library integration

def setFarquharCoefficientsFromLibrary(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel), species: str) -> None:
    """Set Farquhar model coefficients from species library for all primitives"""
    if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("PhotosynthesisModel functions not available. Rebuild with photosynthesis enabled.")
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    if not species:
        raise ValueError("Species name cannot be empty.")
    
    helios_lib.setFarquharCoefficientsFromLibrary(photosynthesis_model, species.encode('utf-8'))


def setFarquharCoefficientsFromLibraryForUUIDs(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel), species: str, uuids: List[int]) -> None:
    """Set Farquhar model coefficients from species library for specific primitives"""
    if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("PhotosynthesisModel functions not available. Rebuild with photosynthesis enabled.")
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    if not species:
        raise ValueError("Species name cannot be empty.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")
    
    # Convert to ctypes array
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.setFarquharCoefficientsFromLibraryForUUIDs(photosynthesis_model, species.encode('utf-8'), uuid_array, len(uuids))


def getFarquharCoefficientsFromLibrary(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel), species: str) -> List[float]:
    """Get Farquhar model coefficients from species library"""
    if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("PhotosynthesisModel functions not available. Rebuild with photosynthesis enabled.")
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    if not species:
        raise ValueError("Species name cannot be empty.")
    
    # Create coefficients array
    coeff_size = 20
    coefficients = (ctypes.c_float * coeff_size)()
    
    helios_lib.getFarquharCoefficientsFromLibrary(photosynthesis_model, species.encode('utf-8'), coefficients, coeff_size)
    
    # Convert to Python list
    return list(coefficients)


# Model parameter configuration - Empirical

def setEmpiricalModelCoefficients(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel), coefficients: List[float]) -> None:
    """Set empirical model coefficients for all primitives"""
    if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("PhotosynthesisModel functions not available. Rebuild with photosynthesis enabled.")
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    if not coefficients:
        raise ValueError("Coefficients list cannot be empty.")
    if len(coefficients) < 10:
        raise ValueError("Empirical model coefficients must have at least 10 elements.")
    
    # Convert to ctypes array
    coeff_array = (ctypes.c_float * len(coefficients))(*coefficients)
    helios_lib.setEmpiricalModelCoefficients(photosynthesis_model, coeff_array, len(coefficients))


def setEmpiricalModelCoefficientsForUUIDs(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel), coefficients: List[float], uuids: List[int]) -> None:
    """Set empirical model coefficients for specific primitives"""
    if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("PhotosynthesisModel functions not available. Rebuild with photosynthesis enabled.")
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    if not coefficients:
        raise ValueError("Coefficients list cannot be empty.")
    if len(coefficients) < 10:
        raise ValueError("Empirical model coefficients must have at least 10 elements.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")
    
    # Convert to ctypes arrays
    coeff_array = (ctypes.c_float * len(coefficients))(*coefficients)
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.setEmpiricalModelCoefficientsForUUIDs(photosynthesis_model, coeff_array, len(coefficients), uuid_array, len(uuids))


# Model parameter configuration - Farquhar

def setFarquharModelCoefficients(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel), coefficients: List[float]) -> None:
    """Set Farquhar model coefficients for all primitives"""
    if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("PhotosynthesisModel functions not available. Rebuild with photosynthesis enabled.")
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    if not coefficients:
        raise ValueError("Coefficients list cannot be empty.")
    if len(coefficients) < 18:
        raise ValueError("Farquhar model coefficients must have at least 18 elements.")
    
    # Convert to ctypes array
    coeff_array = (ctypes.c_float * len(coefficients))(*coefficients)
    helios_lib.setFarquharModelCoefficients(photosynthesis_model, coeff_array, len(coefficients))


def setFarquharModelCoefficientsForUUIDs(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel), coefficients: List[float], uuids: List[int]) -> None:
    """Set Farquhar model coefficients for specific primitives"""
    if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("PhotosynthesisModel functions not available. Rebuild with photosynthesis enabled.")
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    if not coefficients:
        raise ValueError("Coefficients list cannot be empty.")
    if len(coefficients) < 18:
        raise ValueError("Farquhar model coefficients must have at least 18 elements.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")
    
    # Convert to ctypes arrays
    coeff_array = (ctypes.c_float * len(coefficients))(*coefficients)
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.setFarquharModelCoefficientsForUUIDs(photosynthesis_model, coeff_array, len(coefficients), uuid_array, len(uuids))


# Individual Farquhar parameter setters

def setFarquharVcmax(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel), vcmax_at_25c: float, 
                    dha: Optional[float] = None, topt: Optional[float] = None, dhd: Optional[float] = None, 
                    uuids: Optional[List[int]] = None) -> None:
    """Set Vcmax parameter with temperature response for specific primitives"""
    if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("PhotosynthesisModel functions not available. Rebuild with photosynthesis enabled.")
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    
    # Individual parameter setters require explicit UUIDs
    if uuids is None or len(uuids) == 0:
        raise ValueError("Individual parameter setters require explicit UUIDs. Use setFarquharModelCoefficients() for all primitives.")
    
    # Use -1 to indicate optional parameters not provided
    dha_val = -1.0 if dha is None else dha
    topt_val = -1.0 if topt is None else topt
    dhd_val = -1.0 if dhd is None else dhd
    
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    uuid_count = len(uuids)
    
    helios_lib.setFarquharVcmax(photosynthesis_model, vcmax_at_25c, dha_val, topt_val, dhd_val, uuid_array, uuid_count)
    
    # Check for errors after the C++ call
    check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage)


def setFarquharJmax(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel), jmax_at_25c: float, 
                    dha: Optional[float] = None, topt: Optional[float] = None, dhd: Optional[float] = None, 
                    uuids: Optional[List[int]] = None) -> None:
    """Set Jmax parameter with temperature response for specific primitives"""
    if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("PhotosynthesisModel functions not available. Rebuild with photosynthesis enabled.")
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    
    dha_val = -1.0 if dha is None else dha
    topt_val = -1.0 if topt is None else topt
    dhd_val = -1.0 if dhd is None else dhd
    
    if uuids is None:
        uuid_array = None
        uuid_count = 0
    else:
        uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
        uuid_count = len(uuids)
    
    helios_lib.setFarquharJmax(photosynthesis_model, jmax_at_25c, dha_val, topt_val, dhd_val, uuid_array, uuid_count)


def setFarquharRd(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel), rd_at_25c: float, 
                  dha: Optional[float] = None, topt: Optional[float] = None, dhd: Optional[float] = None, 
                  uuids: Optional[List[int]] = None) -> None:
    """Set dark respiration (Rd) parameter with temperature response for specific primitives"""
    if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("PhotosynthesisModel functions not available. Rebuild with photosynthesis enabled.")
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    
    dha_val = -1.0 if dha is None else dha
    topt_val = -1.0 if topt is None else topt
    dhd_val = -1.0 if dhd is None else dhd
    
    if uuids is None:
        uuid_array = None
        uuid_count = 0
    else:
        uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
        uuid_count = len(uuids)
    
    helios_lib.setFarquharRd(photosynthesis_model, rd_at_25c, dha_val, topt_val, dhd_val, uuid_array, uuid_count)


def setFarquharQuantumEfficiency(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel), alpha_at_25c: float, 
                                dha: Optional[float] = None, topt: Optional[float] = None, dhd: Optional[float] = None, 
                                uuids: Optional[List[int]] = None) -> None:
    """Set quantum efficiency (alpha) parameter with temperature response for specific primitives"""
    if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("PhotosynthesisModel functions not available. Rebuild with photosynthesis enabled.")
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    
    dha_val = -1.0 if dha is None else dha
    topt_val = -1.0 if topt is None else topt
    dhd_val = -1.0 if dhd is None else dhd
    
    if uuids is None:
        uuid_array = None
        uuid_count = 0
    else:
        uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
        uuid_count = len(uuids)
    
    helios_lib.setFarquharQuantumEfficiency(photosynthesis_model, alpha_at_25c, dha_val, topt_val, dhd_val, uuid_array, uuid_count)


def setFarquharLightResponseCurvature(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel), theta_at_25c: float, 
                                     dha: Optional[float] = None, topt: Optional[float] = None, dhd: Optional[float] = None, 
                                     uuids: Optional[List[int]] = None) -> None:
    """Set light response curvature (theta) parameter with temperature response for specific primitives"""
    if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("PhotosynthesisModel functions not available. Rebuild with photosynthesis enabled.")
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    
    dha_val = -1.0 if dha is None else dha
    topt_val = -1.0 if topt is None else topt
    dhd_val = -1.0 if dhd is None else dhd
    
    if uuids is None:
        uuid_array = None
        uuid_count = 0
    else:
        uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
        uuid_count = len(uuids)
    
    helios_lib.setFarquharLightResponseCurvature(photosynthesis_model, theta_at_25c, dha_val, topt_val, dhd_val, uuid_array, uuid_count)


# Parameter getters

def getEmpiricalModelCoefficients(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel), uuid: int) -> List[float]:
    """Get empirical model coefficients for a specific primitive"""
    if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("PhotosynthesisModel functions not available. Rebuild with photosynthesis enabled.")
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    if uuid < 0:
        raise ValueError("UUID must be non-negative.")
    
    # Create coefficients array
    coeff_size = 10
    coefficients = (ctypes.c_float * coeff_size)()
    
    helios_lib.getEmpiricalModelCoefficients(photosynthesis_model, uuid, coefficients, coeff_size)
    
    # Convert to Python list
    return list(coefficients)


def getFarquharModelCoefficients(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel), uuid: int) -> List[float]:
    """Get Farquhar model coefficients for a specific primitive"""
    if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("PhotosynthesisModel functions not available. Rebuild with photosynthesis enabled.")
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    if uuid < 0:
        raise ValueError("UUID must be non-negative.")
    
    # 22-float layout (helios-core 1.3.72+): 18 legacy + 4 mesophyll-conductance gm
    # temperature-response slots. Older builds that only fill 18 elements still work
    # because the C wrapper zero-fills the tail.
    coeff_size = 22
    coefficients = (ctypes.c_float * coeff_size)()

    helios_lib.getFarquharModelCoefficients(photosynthesis_model, uuid, coefficients, coeff_size)

    # Convert to Python list
    return list(coefficients)


# Model configuration and utilities

def enableMessages(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel)) -> None:
    """Enable PhotosynthesisModel status messages"""
    if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("PhotosynthesisModel functions not available. Rebuild with photosynthesis enabled.")
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    
    helios_lib.enablePhotosynthesisMessages(photosynthesis_model)


def disableMessages(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel)) -> None:
    """Disable PhotosynthesisModel status messages"""
    if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("PhotosynthesisModel functions not available. Rebuild with photosynthesis enabled.")
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    
    helios_lib.disablePhotosynthesisMessages(photosynthesis_model)


def optionalOutputPrimitiveData(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel), label: str) -> None:
    """Add optional output primitive data"""
    if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("PhotosynthesisModel functions not available. Rebuild with photosynthesis enabled.")
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    if not label:
        raise ValueError("Label cannot be empty.")
    
    helios_lib.optionalOutputPhotosynthesisPrimitiveData(photosynthesis_model, label.encode('utf-8'))


def printDefaultValueReport(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel)) -> None:
    """Print default value report for all primitives"""
    if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("PhotosynthesisModel functions not available. Rebuild with photosynthesis enabled.")
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    
    helios_lib.printPhotosynthesisDefaultValueReport(photosynthesis_model)


def printDefaultValueReportForUUIDs(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel), uuids: List[int]) -> None:
    """Print default value report for specific primitives"""
    if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("PhotosynthesisModel functions not available. Rebuild with photosynthesis enabled.")
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")
    
    # Convert to ctypes array
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.printPhotosynthesisDefaultValueReportForUUIDs(photosynthesis_model, uuid_array, len(uuids))


# C4 model + Farquhar mesophyll-conductance bindings (helios-core v1.3.72+)

def setModelTypeC4(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel)) -> None:
    """Set photosynthesis to use the von Caemmerer (2021) steady-state C4 model."""
    _require_c4_available()
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    helios_lib.setPhotosynthesisModelTypeC4(photosynthesis_model)


def setFarquharMesophyllConductance(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel),
                                    gm_at_25c: float, dha: float, topt: float, dhd: float,
                                    uuids: List[int]) -> None:
    """Set Farquhar mesophyll conductance gm with optional temperature response.

    Pass dha=-1 for a constant gm (no temperature response). With dha set, omit
    topt/dhd by passing -1 to fall through to the appropriate constructor overload.
    Default behaviour (no call) leaves gm = +infinity (Cc = Ci, legacy).
    """
    _require_c4_available()
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.setFarquharMesophyllConductance(
        photosynthesis_model,
        ctypes.c_float(gm_at_25c), ctypes.c_float(dha),
        ctypes.c_float(topt), ctypes.c_float(dhd),
        uuid_array, len(uuids),
    )


def setC4CoefficientsFromLibrary(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel),
                                 species: str, uuids: Optional[List[int]] = None) -> None:
    """Set C4 model coefficients from the species library.

    If ``uuids`` is None, applies to all primitives. Otherwise applies to the
    specified UUID set.
    """
    _require_c4_available()
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    if not species:
        raise ValueError("Species name cannot be empty.")

    species_bytes = species.encode('utf-8')
    if uuids is None:
        helios_lib.setC4CoefficientsFromLibrary(photosynthesis_model, species_bytes)
    else:
        if not uuids:
            raise ValueError("UUIDs list cannot be empty when provided.")
        uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
        helios_lib.setC4CoefficientsFromLibraryForUUIDs(
            photosynthesis_model, species_bytes, uuid_array, len(uuids),
        )


def setC4CoefficientsFromLibraryForMaterial(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel),
                                            species: str, material_label: str) -> None:
    """Apply a C4 species library entry to all primitives sharing a material label."""
    _require_c4_available()
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    if not species:
        raise ValueError("Species name cannot be empty.")
    if not material_label:
        raise ValueError("Material label cannot be empty.")
    helios_lib.setC4CoefficientsFromLibraryForMaterial(
        photosynthesis_model, species.encode('utf-8'), material_label.encode('utf-8'),
    )


def setC4ModelCoefficientsForMaterial(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel),
                                      material_label: str, coefficients: List[float]) -> None:
    """Apply a 43-float C4 coefficient array to all primitives sharing a material label."""
    _require_c4_available()
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    if not material_label:
        raise ValueError("Material label cannot be empty.")
    if len(coefficients) < C4_COEFFICIENTS_COUNT:
        raise ValueError(
            f"C4 coefficient array must have at least {C4_COEFFICIENTS_COUNT} elements, got {len(coefficients)}."
        )
    coeff_array = (ctypes.c_float * len(coefficients))(*coefficients)
    helios_lib.setC4ModelCoefficientsForMaterial(
        photosynthesis_model, material_label.encode('utf-8'),
        coeff_array, len(coefficients),
    )


def getC4CoefficientsFromLibrary(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel),
                                 species: str) -> List[float]:
    """Return the 43-float C4 coefficient array for ``species``."""
    _require_c4_available()
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    if not species:
        raise ValueError("Species name cannot be empty.")

    coeff_array = (ctypes.c_float * C4_COEFFICIENTS_COUNT)()
    helios_lib.getC4CoefficientsFromLibrary(
        photosynthesis_model, species.encode('utf-8'),
        coeff_array, C4_COEFFICIENTS_COUNT,
    )
    return list(coeff_array)


def setC4ModelCoefficients(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel),
                           coefficients: List[float],
                           uuids: Optional[List[int]] = None) -> None:
    """Apply a full C4 coefficient array to all (uuids=None) or selected primitives."""
    _require_c4_available()
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    if len(coefficients) < C4_COEFFICIENTS_COUNT:
        raise ValueError(
            f"C4 coefficient array must have at least {C4_COEFFICIENTS_COUNT} elements, got {len(coefficients)}."
        )
    coeff_array = (ctypes.c_float * len(coefficients))(*coefficients)

    if uuids is None:
        helios_lib.setC4ModelCoefficients(photosynthesis_model, coeff_array, len(coefficients))
    else:
        if not uuids:
            raise ValueError("UUIDs list cannot be empty when provided.")
        uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
        helios_lib.setC4ModelCoefficientsForUUIDs(
            photosynthesis_model, coeff_array, len(coefficients),
            uuid_array, len(uuids),
        )


def getC4ModelCoefficients(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel),
                           uuid: int) -> List[float]:
    """Return the 43-float C4 coefficient array for a single primitive."""
    _require_c4_available()
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    coeff_array = (ctypes.c_float * C4_COEFFICIENTS_COUNT)()
    helios_lib.getC4ModelCoefficients(
        photosynthesis_model, ctypes.c_uint(uuid),
        coeff_array, C4_COEFFICIENTS_COUNT,
    )
    return list(coeff_array)


def setCm(photosynthesis_model: ctypes.POINTER(UPhotosynthesisModel),
          cm: float, uuids: List[int]) -> None:
    """Manually prescribe mesophyll cytosolic CO2 (Cm) for the C4 model.

    Bypasses the Cm = Ci - A/gm fixed-point iteration and the stomatal balance
    on Ci. Primarily intended for testing/validation.
    """
    _require_c4_available()
    if not photosynthesis_model:
        raise ValueError("PhotosynthesisModel instance is None.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.setPhotosynthesisCm(
        photosynthesis_model, ctypes.c_float(cm), uuid_array, len(uuids),
    )


# Mock mode functions for development
if not _PHOTOSYNTHESIS_FUNCTIONS_AVAILABLE:
    def mock_createPhotosynthesisModel(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: PhotosynthesisModel not available. "
            "This would create a photosynthesis model instance with native library."
        )

    def mock_runPhotosynthesisModel(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: PhotosynthesisModel methods not available. "
            "This would execute photosynthesis calculations with native library."
        )

    # Replace functions with mocks for development
    createPhotosynthesisModel = mock_createPhotosynthesisModel
    run = mock_runPhotosynthesisModel
    runForUUIDs = mock_runPhotosynthesisModel
    setModelTypeEmpirical = mock_runPhotosynthesisModel
    setModelTypeFarquhar = mock_runPhotosynthesisModel