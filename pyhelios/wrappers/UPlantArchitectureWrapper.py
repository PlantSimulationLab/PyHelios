"""
ctypes wrapper for PlantArchitecture plugin functionality.

This module provides ctypes bindings for the PlantArchitecture C++ plugin,
enabling procedural plant modeling and plant library functionality.
"""

import ctypes
from typing import List, Optional, Tuple

from ..plugins import helios_lib
from ..exceptions import check_helios_error

# Define the UPlantArchitecture struct
class UPlantArchitecture(ctypes.Structure):
    """Opaque structure for PlantArchitecture C++ class"""
    pass

# Import UContext from main wrapper to avoid type conflicts
from .UContextWrapper import UContext

# Function prototypes with availability detection
try:
    # PlantArchitecture management functions
    helios_lib.createPlantArchitecture.argtypes = [ctypes.POINTER(UContext)]
    helios_lib.createPlantArchitecture.restype = ctypes.POINTER(UPlantArchitecture)

    helios_lib.destroyPlantArchitecture.argtypes = [ctypes.POINTER(UPlantArchitecture)]
    helios_lib.destroyPlantArchitecture.restype = None

    # Plant library functions
    helios_lib.loadPlantModelFromLibrary.argtypes = [
        ctypes.POINTER(UPlantArchitecture),
        ctypes.c_char_p
    ]
    helios_lib.loadPlantModelFromLibrary.restype = ctypes.c_int

    helios_lib.buildPlantInstanceFromLibrary.argtypes = [
        ctypes.POINTER(UPlantArchitecture),
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_float
    ]
    helios_lib.buildPlantInstanceFromLibrary.restype = ctypes.c_uint

    helios_lib.buildPlantCanopyFromLibrary.argtypes = [
        ctypes.POINTER(UPlantArchitecture),
        ctypes.POINTER(ctypes.c_float),  # canopy_center
        ctypes.POINTER(ctypes.c_float),  # plant_spacing
        ctypes.POINTER(ctypes.c_int),    # plant_count
        ctypes.c_float,                  # age
        ctypes.POINTER(ctypes.POINTER(ctypes.c_uint)),  # plant_ids
        ctypes.POINTER(ctypes.c_int)     # num_plants
    ]
    helios_lib.buildPlantCanopyFromLibrary.restype = ctypes.c_int

    helios_lib.advanceTime.argtypes = [
        ctypes.POINTER(UPlantArchitecture),
        ctypes.c_float
    ]
    helios_lib.advanceTime.restype = ctypes.c_int

    # Plant query functions
    helios_lib.getAvailablePlantModels.argtypes = [
        ctypes.POINTER(UPlantArchitecture),
        ctypes.POINTER(ctypes.POINTER(ctypes.c_char_p)),
        ctypes.POINTER(ctypes.c_int)
    ]
    helios_lib.getAvailablePlantModels.restype = ctypes.c_int

    helios_lib.getAllPlantObjectIDs.argtypes = [
        ctypes.POINTER(UPlantArchitecture),
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_int)
    ]
    helios_lib.getAllPlantObjectIDs.restype = ctypes.POINTER(ctypes.c_uint)

    helios_lib.getAllPlantUUIDs.argtypes = [
        ctypes.POINTER(UPlantArchitecture),
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_int)
    ]
    helios_lib.getAllPlantUUIDs.restype = ctypes.POINTER(ctypes.c_uint)

    # Memory cleanup functions
    helios_lib.freeStringArray.argtypes = [ctypes.POINTER(ctypes.c_char_p), ctypes.c_int]
    helios_lib.freeStringArray.restype = None

    helios_lib.freeIntArray.argtypes = [ctypes.POINTER(ctypes.c_uint)]
    helios_lib.freeIntArray.restype = None

    _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE = True

except AttributeError:
    _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE = False

# Error checking callback
def _check_error(result, func, args):
    """Automatic error checking for all plugin functions"""
    check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage)
    return result

# Set up automatic error checking
if _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
    helios_lib.createPlantArchitecture.errcheck = _check_error
    helios_lib.loadPlantModelFromLibrary.errcheck = _check_error
    helios_lib.buildPlantInstanceFromLibrary.errcheck = _check_error
    helios_lib.buildPlantCanopyFromLibrary.errcheck = _check_error
    helios_lib.advanceTime.errcheck = _check_error
    helios_lib.getAvailablePlantModels.errcheck = _check_error
    helios_lib.getAllPlantObjectIDs.errcheck = _check_error
    helios_lib.getAllPlantUUIDs.errcheck = _check_error

# Wrapper functions
def createPlantArchitecture(context) -> ctypes.POINTER(UPlantArchitecture):
    """Create PlantArchitecture instance"""
    if not _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PlantArchitecture functions not available in current Helios library. "
            "Rebuild PyHelios with 'plantarchitecture' enabled:\n"
            "  build_scripts/build_helios --plugins plantarchitecture"
        )

    # Explicit type coercion to fix Windows ctypes type identity issue
    # Ensures context is properly cast to the expected ctypes.POINTER(UContext) type
    if context is not None:
        context_ptr = ctypes.cast(context, ctypes.POINTER(UContext))
        return helios_lib.createPlantArchitecture(context_ptr)
    else:
        raise ValueError("Context cannot be None")

def destroyPlantArchitecture(plantarch_ptr: ctypes.POINTER(UPlantArchitecture)) -> None:
    """Destroy PlantArchitecture instance"""
    if plantarch_ptr and _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
        helios_lib.destroyPlantArchitecture(plantarch_ptr)

def loadPlantModelFromLibrary(plantarch_ptr: ctypes.POINTER(UPlantArchitecture), plant_label: str) -> None:
    """Load plant model from library"""
    if not _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PlantArchitecture methods not available. Rebuild with plantarchitecture enabled."
        )

    if not plant_label:
        raise ValueError("Plant label cannot be empty")

    plant_label_bytes = plant_label.encode('utf-8')
    result = helios_lib.loadPlantModelFromLibrary(plantarch_ptr, plant_label_bytes)
    if result != 0:
        raise RuntimeError(f"Failed to load plant model '{plant_label}'")

def buildPlantInstanceFromLibrary(plantarch_ptr: ctypes.POINTER(UPlantArchitecture),
                                base_position: List[float], age: float) -> int:
    """Build plant instance from library"""
    if not _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PlantArchitecture methods not available. Rebuild with plantarchitecture enabled."
        )

    if len(base_position) != 3:
        raise ValueError("Base position must have exactly 3 coordinates")

    if age < 0:
        raise ValueError("Age cannot be negative")

    # Convert to ctypes array
    position_array = (ctypes.c_float * 3)(*base_position)

    # Call function - errcheck handles error checking automatically
    # Note: Plant IDs can be 0 or any positive integer - all are valid
    plant_id = helios_lib.buildPlantInstanceFromLibrary(plantarch_ptr, position_array, age)

    return plant_id

def buildPlantCanopyFromLibrary(plantarch_ptr: ctypes.POINTER(UPlantArchitecture),
                              canopy_center: List[float], plant_spacing: List[float],
                              plant_count: List[int], age: float) -> List[int]:
    """Build plant canopy from library"""
    if not _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PlantArchitecture methods not available. Rebuild with plantarchitecture enabled."
        )

    if len(canopy_center) != 3:
        raise ValueError("Canopy center must have exactly 3 coordinates")
    if len(plant_spacing) != 2:
        raise ValueError("Plant spacing must have exactly 2 values")
    if len(plant_count) != 2:
        raise ValueError("Plant count must have exactly 2 values")
    if age < 0:
        raise ValueError("Age cannot be negative")

    # Convert to ctypes arrays
    center_array = (ctypes.c_float * 3)(*canopy_center)
    spacing_array = (ctypes.c_float * 2)(*plant_spacing)
    count_array = (ctypes.c_int * 2)(*plant_count)

    # Output parameters
    plant_ids_ptr = ctypes.POINTER(ctypes.c_uint)()
    num_plants = ctypes.c_int()

    # Call function
    result = helios_lib.buildPlantCanopyFromLibrary(
        plantarch_ptr, center_array, spacing_array, count_array, age,
        ctypes.byref(plant_ids_ptr), ctypes.byref(num_plants)
    )

    if result != 0:
        raise RuntimeError("Failed to build plant canopy")

    # Convert to Python list
    if plant_ids_ptr and num_plants.value > 0:
        return [plant_ids_ptr[i] for i in range(num_plants.value)]
    else:
        return []

def advanceTime(plantarch_ptr: ctypes.POINTER(UPlantArchitecture), dt: float) -> None:
    """Advance time for plant growth"""
    if not _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PlantArchitecture methods not available. Rebuild with plantarchitecture enabled."
        )

    if dt < 0:
        raise ValueError("Time step cannot be negative")

    result = helios_lib.advanceTime(plantarch_ptr, dt)
    if result != 0:
        raise RuntimeError(f"Failed to advance time by {dt} days")

def getAvailablePlantModels(plantarch_ptr: ctypes.POINTER(UPlantArchitecture)) -> List[str]:
    """Get list of available plant models"""
    if not _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PlantArchitecture methods not available. Rebuild with plantarchitecture enabled."
        )

    # Output parameters
    model_names_ptr = ctypes.POINTER(ctypes.c_char_p)()
    count = ctypes.c_int()

    # Call function
    result = helios_lib.getAvailablePlantModels(
        plantarch_ptr, ctypes.byref(model_names_ptr), ctypes.byref(count)
    )

    if result != 0:
        raise RuntimeError("Failed to get available plant models")

    # Convert to Python list
    models = []
    if model_names_ptr and count.value > 0:
        for i in range(count.value):
            models.append(model_names_ptr[i].decode('utf-8'))

        # Clean up allocated memory
        helios_lib.freeStringArray(model_names_ptr, count.value)

    return models

def getAllPlantObjectIDs(plantarch_ptr: ctypes.POINTER(UPlantArchitecture), plant_id: int) -> List[int]:
    """Get all object IDs for a plant"""
    if not _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PlantArchitecture methods not available. Rebuild with plantarchitecture enabled."
        )

    if plant_id < 0:
        raise ValueError("Plant ID must be non-negative")

    # Get array from C++
    count = ctypes.c_int()
    ptr = helios_lib.getAllPlantObjectIDs(plantarch_ptr, plant_id, ctypes.byref(count))

    # Convert to Python list
    if ptr and count.value > 0:
        return [ptr[i] for i in range(count.value)]
    else:
        return []

def getAllPlantUUIDs(plantarch_ptr: ctypes.POINTER(UPlantArchitecture), plant_id: int) -> List[int]:
    """Get all UUIDs for a plant"""
    if not _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PlantArchitecture methods not available. Rebuild with plantarchitecture enabled."
        )

    if plant_id < 0:
        raise ValueError("Plant ID must be non-negative")

    # Get array from C++
    count = ctypes.c_int()
    ptr = helios_lib.getAllPlantUUIDs(plantarch_ptr, plant_id, ctypes.byref(count))

    # Convert to Python list
    if ptr and count.value > 0:
        return [ptr[i] for i in range(count.value)]
    else:
        return []

# Mock mode functions
if not _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
    def mock_createPlantArchitecture(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: PlantArchitecture not available. "
            "This would create a plant architecture instance with native library."
        )

    def mock_loadPlantModelFromLibrary(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: PlantArchitecture methods not available. "
            "This would load a plant model from library with native library."
        )

    def mock_buildPlantInstanceFromLibrary(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: PlantArchitecture methods not available. "
            "This would build a plant instance with native library."
        )

    def mock_advanceTime(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: PlantArchitecture methods not available. "
            "This would advance plant growth time with native library."
        )

    # Replace functions with mocks for development
    createPlantArchitecture = mock_createPlantArchitecture
    loadPlantModelFromLibrary = mock_loadPlantModelFromLibrary
    buildPlantInstanceFromLibrary = mock_buildPlantInstanceFromLibrary
    advanceTime = mock_advanceTime