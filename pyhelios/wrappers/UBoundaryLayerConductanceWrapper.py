"""
Ctypes wrapper for BoundaryLayerConductanceModel C++ bindings.

This module provides low-level ctypes bindings to interface with
the native Helios BoundaryLayerConductanceModel plugin via the C++ wrapper layer.
"""

import ctypes
from typing import List, Union

from ..plugins import helios_lib
from ..exceptions import check_helios_error

# Define the UBoundaryLayerConductanceModel struct
class UBoundaryLayerConductanceModel(ctypes.Structure):
    """Opaque structure for BLConductanceModel C++ class"""
    pass

# Import UContext from main wrapper to avoid type conflicts
from .UContextWrapper import UContext

# Error checking callback
def _check_error(result, func, args):
    """Automatic error checking for all boundary layer conductance functions"""
    check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage, helios_lib.clearError)
    return result

# Try to set up BoundaryLayerConductanceModel function prototypes
try:
    # BoundaryLayerConductanceModel creation and destruction
    helios_lib.createBoundaryLayerConductanceModel.argtypes = [ctypes.POINTER(UContext)]
    helios_lib.createBoundaryLayerConductanceModel.restype = ctypes.POINTER(UBoundaryLayerConductanceModel)
    helios_lib.createBoundaryLayerConductanceModel.errcheck = _check_error

    helios_lib.destroyBoundaryLayerConductanceModel.argtypes = [ctypes.POINTER(UBoundaryLayerConductanceModel)]
    helios_lib.destroyBoundaryLayerConductanceModel.restype = None
    # Note: destroyBoundaryLayerConductanceModel doesn't need errcheck as it doesn't fail

    # Message control
    helios_lib.enableBoundaryLayerMessages.argtypes = [ctypes.POINTER(UBoundaryLayerConductanceModel)]
    helios_lib.enableBoundaryLayerMessages.restype = None
    helios_lib.enableBoundaryLayerMessages.errcheck = _check_error

    helios_lib.disableBoundaryLayerMessages.argtypes = [ctypes.POINTER(UBoundaryLayerConductanceModel)]
    helios_lib.disableBoundaryLayerMessages.restype = None
    helios_lib.disableBoundaryLayerMessages.errcheck = _check_error

    # Model configuration methods
    helios_lib.setBoundaryLayerModel.argtypes = [ctypes.POINTER(UBoundaryLayerConductanceModel), ctypes.c_char_p]
    helios_lib.setBoundaryLayerModel.restype = None
    helios_lib.setBoundaryLayerModel.errcheck = _check_error

    helios_lib.setBoundaryLayerModelForUUID.argtypes = [ctypes.POINTER(UBoundaryLayerConductanceModel), ctypes.c_uint, ctypes.c_char_p]
    helios_lib.setBoundaryLayerModelForUUID.restype = None
    helios_lib.setBoundaryLayerModelForUUID.errcheck = _check_error

    helios_lib.setBoundaryLayerModelForUUIDs.argtypes = [
        ctypes.POINTER(UBoundaryLayerConductanceModel),
        ctypes.POINTER(ctypes.c_uint),
        ctypes.c_uint,
        ctypes.c_char_p
    ]
    helios_lib.setBoundaryLayerModelForUUIDs.restype = None
    helios_lib.setBoundaryLayerModelForUUIDs.errcheck = _check_error

    # Core execution methods
    helios_lib.runBoundaryLayerModel.argtypes = [ctypes.POINTER(UBoundaryLayerConductanceModel)]
    helios_lib.runBoundaryLayerModel.restype = None
    helios_lib.runBoundaryLayerModel.errcheck = _check_error

    helios_lib.runBoundaryLayerModelForUUIDs.argtypes = [
        ctypes.POINTER(UBoundaryLayerConductanceModel),
        ctypes.POINTER(ctypes.c_uint),
        ctypes.c_uint
    ]
    helios_lib.runBoundaryLayerModelForUUIDs.restype = None
    helios_lib.runBoundaryLayerModelForUUIDs.errcheck = _check_error

    _BOUNDARYLAYER_FUNCTIONS_AVAILABLE = True

except AttributeError:
    _BOUNDARYLAYER_FUNCTIONS_AVAILABLE = False


# Wrapper functions
def createBoundaryLayerConductanceModel(context: ctypes.POINTER(UContext)) -> ctypes.POINTER(UBoundaryLayerConductanceModel):
    """Create BoundaryLayerConductanceModel instance"""
    if not _BOUNDARYLAYER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "BoundaryLayerConductanceModel functions not available in current Helios library. "
            "Rebuild PyHelios with 'boundarylayerconductance' enabled:\n"
            "  build_scripts/build_helios --plugins boundarylayerconductance"
        )

    if not context:
        raise ValueError("Context instance is None.")

    return helios_lib.createBoundaryLayerConductanceModel(context)


def destroyBoundaryLayerConductanceModel(model: ctypes.POINTER(UBoundaryLayerConductanceModel)) -> None:
    """Destroy BoundaryLayerConductanceModel instance"""
    if model and _BOUNDARYLAYER_FUNCTIONS_AVAILABLE:
        helios_lib.destroyBoundaryLayerConductanceModel(model)


def enableMessages(model: ctypes.POINTER(UBoundaryLayerConductanceModel)) -> None:
    """Enable standard output messages from boundary layer conductance model"""
    if not _BOUNDARYLAYER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("BoundaryLayerConductanceModel functions not available. Rebuild with boundarylayerconductance enabled.")
    if not model:
        raise ValueError("BoundaryLayerConductanceModel instance is None.")

    helios_lib.enableBoundaryLayerMessages(model)


def disableMessages(model: ctypes.POINTER(UBoundaryLayerConductanceModel)) -> None:
    """Disable standard output messages from boundary layer conductance model"""
    if not _BOUNDARYLAYER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("BoundaryLayerConductanceModel functions not available. Rebuild with boundarylayerconductance enabled.")
    if not model:
        raise ValueError("BoundaryLayerConductanceModel instance is None.")

    helios_lib.disableBoundaryLayerMessages(model)


def setBoundaryLayerModel(model: ctypes.POINTER(UBoundaryLayerConductanceModel), model_name: str) -> None:
    """Set boundary layer conductance model for all primitives"""
    if not _BOUNDARYLAYER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("BoundaryLayerConductanceModel functions not available. Rebuild with boundarylayerconductance enabled.")
    if not model:
        raise ValueError("BoundaryLayerConductanceModel instance is None.")
    if not model_name:
        raise ValueError("Model name cannot be empty.")

    # Convert to bytes for c_char_p
    model_name_bytes = model_name.encode('utf-8')
    helios_lib.setBoundaryLayerModel(model, model_name_bytes)


def setBoundaryLayerModelForUUID(model: ctypes.POINTER(UBoundaryLayerConductanceModel), uuid: int, model_name: str) -> None:
    """Set boundary layer conductance model for a specific primitive"""
    if not _BOUNDARYLAYER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("BoundaryLayerConductanceModel functions not available. Rebuild with boundarylayerconductance enabled.")
    if not model:
        raise ValueError("BoundaryLayerConductanceModel instance is None.")
    if uuid < 0:
        raise ValueError("UUID must be non-negative.")
    if not model_name:
        raise ValueError("Model name cannot be empty.")

    # Convert to bytes for c_char_p
    model_name_bytes = model_name.encode('utf-8')
    helios_lib.setBoundaryLayerModelForUUID(model, ctypes.c_uint(uuid), model_name_bytes)


def setBoundaryLayerModelForUUIDs(model: ctypes.POINTER(UBoundaryLayerConductanceModel), uuids: List[int], model_name: str) -> None:
    """Set boundary layer conductance model for specific primitives"""
    if not _BOUNDARYLAYER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("BoundaryLayerConductanceModel functions not available. Rebuild with boundarylayerconductance enabled.")
    if not model:
        raise ValueError("BoundaryLayerConductanceModel instance is None.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")
    if not model_name:
        raise ValueError("Model name cannot be empty.")

    # Convert to ctypes array
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    # Convert to bytes for c_char_p
    model_name_bytes = model_name.encode('utf-8')
    helios_lib.setBoundaryLayerModelForUUIDs(model, uuid_array, len(uuids), model_name_bytes)


def runBoundaryLayerModel(model: ctypes.POINTER(UBoundaryLayerConductanceModel)) -> None:
    """Run boundary layer conductance calculations for all primitives"""
    if not _BOUNDARYLAYER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("BoundaryLayerConductanceModel functions not available. Rebuild with boundarylayerconductance enabled.")
    if not model:
        raise ValueError("BoundaryLayerConductanceModel instance is None.")

    helios_lib.runBoundaryLayerModel(model)


def runBoundaryLayerModelForUUIDs(model: ctypes.POINTER(UBoundaryLayerConductanceModel), uuids: List[int]) -> None:
    """Run boundary layer conductance calculations for specific primitives"""
    if not _BOUNDARYLAYER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("BoundaryLayerConductanceModel functions not available. Rebuild with boundarylayerconductance enabled.")
    if not model:
        raise ValueError("BoundaryLayerConductanceModel instance is None.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")

    # Convert to ctypes array
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.runBoundaryLayerModelForUUIDs(model, uuid_array, len(uuids))


# Mock mode functions
if not _BOUNDARYLAYER_FUNCTIONS_AVAILABLE:
    def mock_create(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: BoundaryLayerConductanceModel not available. "
            "This would create a plugin instance with native library."
        )

    def mock_method(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: BoundaryLayerConductanceModel method not available. "
            "This would execute plugin computation with native library."
        )

    # Replace functions with mocks for development
    createBoundaryLayerConductanceModel = mock_create
    setBoundaryLayerModel = mock_method
    runBoundaryLayerModel = mock_method
