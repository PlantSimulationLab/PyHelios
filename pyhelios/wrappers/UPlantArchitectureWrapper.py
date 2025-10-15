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

    # Custom plant building functions
    helios_lib.addPlantInstance.argtypes = [
        ctypes.POINTER(UPlantArchitecture),
        ctypes.POINTER(ctypes.c_float),  # base_position
        ctypes.c_float                    # current_age
    ]
    helios_lib.addPlantInstance.restype = ctypes.c_uint

    helios_lib.deletePlantInstance.argtypes = [
        ctypes.POINTER(UPlantArchitecture),
        ctypes.c_uint                     # plantID
    ]
    helios_lib.deletePlantInstance.restype = ctypes.c_int

    helios_lib.addBaseStemShoot.argtypes = [
        ctypes.POINTER(UPlantArchitecture),
        ctypes.c_uint,                    # plantID
        ctypes.c_uint,                    # current_node_number
        ctypes.POINTER(ctypes.c_float),  # base_rotation
        ctypes.c_float,                   # internode_radius
        ctypes.c_float,                   # internode_length_max
        ctypes.c_float,                   # internode_length_scale_factor_fraction
        ctypes.c_float,                   # leaf_scale_factor_fraction
        ctypes.c_float,                   # radius_taper
        ctypes.c_char_p                   # shoot_type_label
    ]
    helios_lib.addBaseStemShoot.restype = ctypes.c_uint

    helios_lib.appendShoot.argtypes = [
        ctypes.POINTER(UPlantArchitecture),
        ctypes.c_uint,                    # plantID
        ctypes.c_int,                     # parent_shoot_ID
        ctypes.c_uint,                    # current_node_number
        ctypes.POINTER(ctypes.c_float),  # base_rotation
        ctypes.c_float,                   # internode_radius
        ctypes.c_float,                   # internode_length_max
        ctypes.c_float,                   # internode_length_scale_factor_fraction
        ctypes.c_float,                   # leaf_scale_factor_fraction
        ctypes.c_float,                   # radius_taper
        ctypes.c_char_p                   # shoot_type_label
    ]
    helios_lib.appendShoot.restype = ctypes.c_uint

    helios_lib.addChildShoot.argtypes = [
        ctypes.POINTER(UPlantArchitecture),
        ctypes.c_uint,                    # plantID
        ctypes.c_int,                     # parent_shoot_ID
        ctypes.c_uint,                    # parent_node_index
        ctypes.c_uint,                    # current_node_number
        ctypes.POINTER(ctypes.c_float),  # shoot_base_rotation
        ctypes.c_float,                   # internode_radius
        ctypes.c_float,                   # internode_length_max
        ctypes.c_float,                   # internode_length_scale_factor_fraction
        ctypes.c_float,                   # leaf_scale_factor_fraction
        ctypes.c_float,                   # radius_taper
        ctypes.c_char_p,                  # shoot_type_label
        ctypes.c_uint                     # petiole_index
    ]
    helios_lib.addChildShoot.restype = ctypes.c_uint

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

    # Collision detection functions
    helios_lib.enableSoftCollisionAvoidance.argtypes = [
        ctypes.POINTER(UPlantArchitecture),
        ctypes.POINTER(ctypes.c_uint),  # target_UUIDs
        ctypes.c_int,                   # uuid_count
        ctypes.POINTER(ctypes.c_uint),  # target_IDs
        ctypes.c_int,                   # id_count
        ctypes.c_bool,                  # enable_petiole
        ctypes.c_bool                   # enable_fruit
    ]
    helios_lib.enableSoftCollisionAvoidance.restype = ctypes.c_int

    helios_lib.disableCollisionDetection.argtypes = [ctypes.POINTER(UPlantArchitecture)]
    helios_lib.disableCollisionDetection.restype = None

    helios_lib.setSoftCollisionAvoidanceParameters.argtypes = [
        ctypes.POINTER(UPlantArchitecture),
        ctypes.c_float,  # view_half_angle_deg
        ctypes.c_float,  # look_ahead_distance
        ctypes.c_int,    # sample_count
        ctypes.c_float   # inertia_weight
    ]
    helios_lib.setSoftCollisionAvoidanceParameters.restype = None

    helios_lib.setCollisionRelevantOrgans.argtypes = [
        ctypes.POINTER(UPlantArchitecture),
        ctypes.c_bool,  # include_internodes
        ctypes.c_bool,  # include_leaves
        ctypes.c_bool,  # include_petioles
        ctypes.c_bool,  # include_flowers
        ctypes.c_bool   # include_fruit
    ]
    helios_lib.setCollisionRelevantOrgans.restype = None

    helios_lib.enableSolidObstacleAvoidance.argtypes = [
        ctypes.POINTER(UPlantArchitecture),
        ctypes.POINTER(ctypes.c_uint),  # obstacle_UUIDs
        ctypes.c_int,                   # uuid_count
        ctypes.c_float,                 # avoidance_distance
        ctypes.c_bool,                  # enable_fruit_adjustment
        ctypes.c_bool                   # enable_obstacle_pruning
    ]
    helios_lib.enableSolidObstacleAvoidance.restype = ctypes.c_int

    helios_lib.setStaticObstacles.argtypes = [
        ctypes.POINTER(UPlantArchitecture),
        ctypes.POINTER(ctypes.c_uint),  # target_UUIDs
        ctypes.c_int                    # uuid_count
    ]
    helios_lib.setStaticObstacles.restype = ctypes.c_int

    helios_lib.getPlantCollisionRelevantObjectIDs.argtypes = [
        ctypes.POINTER(UPlantArchitecture),
        ctypes.c_uint,              # plant_id
        ctypes.POINTER(ctypes.c_int) # count
    ]
    helios_lib.getPlantCollisionRelevantObjectIDs.restype = ctypes.POINTER(ctypes.c_uint)

    # File I/O functions
    helios_lib.writePlantMeshVertices.argtypes = [
        ctypes.POINTER(UPlantArchitecture),
        ctypes.c_uint,    # plantID
        ctypes.c_char_p   # filename
    ]
    helios_lib.writePlantMeshVertices.restype = ctypes.c_int

    helios_lib.writePlantStructureXML.argtypes = [
        ctypes.POINTER(UPlantArchitecture),
        ctypes.c_uint,    # plantID
        ctypes.c_char_p   # filename
    ]
    helios_lib.writePlantStructureXML.restype = ctypes.c_int

    helios_lib.writeQSMCylinderFile.argtypes = [
        ctypes.POINTER(UPlantArchitecture),
        ctypes.c_uint,    # plantID
        ctypes.c_char_p   # filename
    ]
    helios_lib.writeQSMCylinderFile.restype = ctypes.c_int

    helios_lib.readPlantStructureXML.argtypes = [
        ctypes.POINTER(UPlantArchitecture),
        ctypes.c_char_p,                            # filename
        ctypes.c_bool,                              # quiet
        ctypes.POINTER(ctypes.POINTER(ctypes.c_uint)),  # plant_ids
        ctypes.POINTER(ctypes.c_int)                # num_plants
    ]
    helios_lib.readPlantStructureXML.restype = ctypes.c_int

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
    # Custom plant building error checking
    helios_lib.addPlantInstance.errcheck = _check_error
    helios_lib.deletePlantInstance.errcheck = _check_error
    helios_lib.addBaseStemShoot.errcheck = _check_error
    helios_lib.appendShoot.errcheck = _check_error
    helios_lib.addChildShoot.errcheck = _check_error
    helios_lib.getAvailablePlantModels.errcheck = _check_error
    helios_lib.getAllPlantObjectIDs.errcheck = _check_error
    helios_lib.getAllPlantUUIDs.errcheck = _check_error
    # Collision detection error checking
    helios_lib.enableSoftCollisionAvoidance.errcheck = _check_error
    helios_lib.disableCollisionDetection.errcheck = _check_error
    helios_lib.setSoftCollisionAvoidanceParameters.errcheck = _check_error
    helios_lib.setCollisionRelevantOrgans.errcheck = _check_error
    helios_lib.enableSolidObstacleAvoidance.errcheck = _check_error
    helios_lib.setStaticObstacles.errcheck = _check_error
    helios_lib.getPlantCollisionRelevantObjectIDs.errcheck = _check_error
    # File I/O error checking
    helios_lib.writePlantMeshVertices.errcheck = _check_error
    helios_lib.writePlantStructureXML.errcheck = _check_error
    helios_lib.writeQSMCylinderFile.errcheck = _check_error
    helios_lib.readPlantStructureXML.errcheck = _check_error

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

# Custom plant building wrapper functions
def addPlantInstance(plantarch_ptr: ctypes.POINTER(UPlantArchitecture),
                    base_position: List[float], current_age: float) -> int:
    """Create an empty plant instance for custom building"""
    if not _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PlantArchitecture methods not available. Rebuild with plantarchitecture enabled."
        )

    if len(base_position) != 3:
        raise ValueError("Base position must have exactly 3 coordinates")

    if current_age < 0:
        raise ValueError("Age cannot be negative")

    # Convert to ctypes array
    position_array = (ctypes.c_float * 3)(*base_position)

    # Call function - errcheck handles error checking automatically
    plant_id = helios_lib.addPlantInstance(plantarch_ptr, position_array, current_age)

    return plant_id

def deletePlantInstance(plantarch_ptr: ctypes.POINTER(UPlantArchitecture), plant_id: int) -> None:
    """Delete a plant instance"""
    if not _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PlantArchitecture methods not available. Rebuild with plantarchitecture enabled."
        )

    if plant_id < 0:
        raise ValueError("Plant ID must be non-negative")

    result = helios_lib.deletePlantInstance(plantarch_ptr, plant_id)
    if result != 0:
        raise RuntimeError(f"Failed to delete plant instance {plant_id}")

def addBaseStemShoot(plantarch_ptr: ctypes.POINTER(UPlantArchitecture),
                    plant_id: int, current_node_number: int,
                    base_rotation: List[float], internode_radius: float,
                    internode_length_max: float,
                    internode_length_scale_factor_fraction: float,
                    leaf_scale_factor_fraction: float,
                    radius_taper: float, shoot_type_label: str) -> int:
    """Add a base stem shoot to plant instance"""
    if not _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PlantArchitecture methods not available. Rebuild with plantarchitecture enabled."
        )

    if plant_id < 0:
        raise ValueError("Plant ID must be non-negative")
    if current_node_number < 0:
        raise ValueError("Current node number must be non-negative")
    if len(base_rotation) != 3:
        raise ValueError("Base rotation must have exactly 3 values (pitch, yaw, roll)")
    if internode_radius <= 0:
        raise ValueError("Internode radius must be positive")
    if internode_length_max <= 0:
        raise ValueError("Internode length max must be positive")
    if not shoot_type_label:
        raise ValueError("Shoot type label cannot be empty")

    # Convert to ctypes
    rotation_array = (ctypes.c_float * 3)(*base_rotation)
    label_bytes = shoot_type_label.encode('utf-8')

    # Call function
    shoot_id = helios_lib.addBaseStemShoot(
        plantarch_ptr, plant_id, current_node_number, rotation_array,
        internode_radius, internode_length_max,
        internode_length_scale_factor_fraction, leaf_scale_factor_fraction,
        radius_taper, label_bytes
    )

    return shoot_id

def appendShoot(plantarch_ptr: ctypes.POINTER(UPlantArchitecture),
               plant_id: int, parent_shoot_id: int, current_node_number: int,
               base_rotation: List[float], internode_radius: float,
               internode_length_max: float,
               internode_length_scale_factor_fraction: float,
               leaf_scale_factor_fraction: float,
               radius_taper: float, shoot_type_label: str) -> int:
    """Append a shoot to an existing shoot"""
    if not _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PlantArchitecture methods not available. Rebuild with plantarchitecture enabled."
        )

    if plant_id < 0:
        raise ValueError("Plant ID must be non-negative")
    if parent_shoot_id < 0:
        raise ValueError("Parent shoot ID must be non-negative")
    if current_node_number < 0:
        raise ValueError("Current node number must be non-negative")
    if len(base_rotation) != 3:
        raise ValueError("Base rotation must have exactly 3 values (pitch, yaw, roll)")
    if internode_radius <= 0:
        raise ValueError("Internode radius must be positive")
    if internode_length_max <= 0:
        raise ValueError("Internode length max must be positive")
    if not shoot_type_label:
        raise ValueError("Shoot type label cannot be empty")

    # Convert to ctypes
    rotation_array = (ctypes.c_float * 3)(*base_rotation)
    label_bytes = shoot_type_label.encode('utf-8')

    # Call function
    shoot_id = helios_lib.appendShoot(
        plantarch_ptr, plant_id, parent_shoot_id, current_node_number,
        rotation_array, internode_radius, internode_length_max,
        internode_length_scale_factor_fraction, leaf_scale_factor_fraction,
        radius_taper, label_bytes
    )

    return shoot_id

def addChildShoot(plantarch_ptr: ctypes.POINTER(UPlantArchitecture),
                 plant_id: int, parent_shoot_id: int, parent_node_index: int,
                 current_node_number: int, shoot_base_rotation: List[float],
                 internode_radius: float, internode_length_max: float,
                 internode_length_scale_factor_fraction: float,
                 leaf_scale_factor_fraction: float,
                 radius_taper: float, shoot_type_label: str,
                 petiole_index: int = 0) -> int:
    """Add a child shoot at an axillary bud position"""
    if not _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PlantArchitecture methods not available. Rebuild with plantarchitecture enabled."
        )

    if plant_id < 0:
        raise ValueError("Plant ID must be non-negative")
    if parent_shoot_id < 0:
        raise ValueError("Parent shoot ID must be non-negative")
    if parent_node_index < 0:
        raise ValueError("Parent node index must be non-negative")
    if current_node_number < 0:
        raise ValueError("Current node number must be non-negative")
    if len(shoot_base_rotation) != 3:
        raise ValueError("Shoot base rotation must have exactly 3 values (pitch, yaw, roll)")
    if internode_radius <= 0:
        raise ValueError("Internode radius must be positive")
    if internode_length_max <= 0:
        raise ValueError("Internode length max must be positive")
    if not shoot_type_label:
        raise ValueError("Shoot type label cannot be empty")
    if petiole_index < 0:
        raise ValueError("Petiole index must be non-negative")

    # Convert to ctypes
    rotation_array = (ctypes.c_float * 3)(*shoot_base_rotation)
    label_bytes = shoot_type_label.encode('utf-8')

    # Call function
    shoot_id = helios_lib.addChildShoot(
        plantarch_ptr, plant_id, parent_shoot_id, parent_node_index,
        current_node_number, rotation_array, internode_radius,
        internode_length_max, internode_length_scale_factor_fraction,
        leaf_scale_factor_fraction, radius_taper, label_bytes, petiole_index
    )

    return shoot_id

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

# Collision detection functions
def enableSoftCollisionAvoidance(plantarch_ptr: ctypes.POINTER(UPlantArchitecture),
                                target_UUIDs: Optional[List[int]] = None,
                                target_IDs: Optional[List[int]] = None,
                                enable_petiole: bool = False,
                                enable_fruit: bool = False) -> None:
    """Enable soft collision avoidance for plant growth"""
    if not _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PlantArchitecture methods not available. Rebuild with plantarchitecture enabled."
        )

    # Convert lists to ctypes arrays
    uuid_array = None
    uuid_count = 0
    if target_UUIDs:
        uuid_count = len(target_UUIDs)
        if uuid_count > 0:
            uuid_array = (ctypes.c_uint * uuid_count)(*target_UUIDs)

    id_array = None
    id_count = 0
    if target_IDs:
        id_count = len(target_IDs)
        if id_count > 0:
            id_array = (ctypes.c_uint * id_count)(*target_IDs)

    result = helios_lib.enableSoftCollisionAvoidance(
        plantarch_ptr, uuid_array, uuid_count, id_array, id_count,
        ctypes.c_bool(enable_petiole), ctypes.c_bool(enable_fruit)
    )

    if result != 0:
        raise RuntimeError("Failed to enable soft collision avoidance")

def disableCollisionDetection(plantarch_ptr: ctypes.POINTER(UPlantArchitecture)) -> None:
    """Disable collision detection for plant growth"""
    if not _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PlantArchitecture methods not available. Rebuild with plantarchitecture enabled."
        )

    helios_lib.disableCollisionDetection(plantarch_ptr)

def setSoftCollisionAvoidanceParameters(plantarch_ptr: ctypes.POINTER(UPlantArchitecture),
                                       view_half_angle_deg: float,
                                       look_ahead_distance: float,
                                       sample_count: int,
                                       inertia_weight: float) -> None:
    """Set soft collision avoidance parameters"""
    if not _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PlantArchitecture methods not available. Rebuild with plantarchitecture enabled."
        )

    if view_half_angle_deg < 0 or view_half_angle_deg > 180:
        raise ValueError("View half angle must be between 0 and 180 degrees")
    if look_ahead_distance <= 0:
        raise ValueError("Look ahead distance must be positive")
    if sample_count <= 0:
        raise ValueError("Sample count must be positive")
    if inertia_weight < 0 or inertia_weight > 1:
        raise ValueError("Inertia weight must be between 0 and 1")

    helios_lib.setSoftCollisionAvoidanceParameters(
        plantarch_ptr,
        ctypes.c_float(view_half_angle_deg),
        ctypes.c_float(look_ahead_distance),
        ctypes.c_int(sample_count),
        ctypes.c_float(inertia_weight)
    )

def setCollisionRelevantOrgans(plantarch_ptr: ctypes.POINTER(UPlantArchitecture),
                              include_internodes: bool,
                              include_leaves: bool,
                              include_petioles: bool,
                              include_flowers: bool,
                              include_fruit: bool) -> None:
    """Set which plant organs participate in collision detection"""
    if not _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PlantArchitecture methods not available. Rebuild with plantarchitecture enabled."
        )

    helios_lib.setCollisionRelevantOrgans(
        plantarch_ptr,
        ctypes.c_bool(include_internodes),
        ctypes.c_bool(include_leaves),
        ctypes.c_bool(include_petioles),
        ctypes.c_bool(include_flowers),
        ctypes.c_bool(include_fruit)
    )

def enableSolidObstacleAvoidance(plantarch_ptr: ctypes.POINTER(UPlantArchitecture),
                                obstacle_UUIDs: List[int],
                                avoidance_distance: float = 0.5,
                                enable_fruit_adjustment: bool = False,
                                enable_obstacle_pruning: bool = False) -> None:
    """Enable solid obstacle avoidance"""
    if not _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PlantArchitecture methods not available. Rebuild with plantarchitecture enabled."
        )

    if not obstacle_UUIDs:
        raise ValueError("Obstacle UUIDs list cannot be empty")
    if avoidance_distance <= 0:
        raise ValueError("Avoidance distance must be positive")

    # Convert to ctypes array
    uuid_count = len(obstacle_UUIDs)
    uuid_array = (ctypes.c_uint * uuid_count)(*obstacle_UUIDs)

    result = helios_lib.enableSolidObstacleAvoidance(
        plantarch_ptr, uuid_array, uuid_count,
        ctypes.c_float(avoidance_distance),
        ctypes.c_bool(enable_fruit_adjustment),
        ctypes.c_bool(enable_obstacle_pruning)
    )

    if result != 0:
        raise RuntimeError("Failed to enable solid obstacle avoidance")

def setStaticObstacles(plantarch_ptr: ctypes.POINTER(UPlantArchitecture),
                      target_UUIDs: List[int]) -> None:
    """Mark geometry as static obstacles for BVH optimization"""
    if not _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PlantArchitecture methods not available. Rebuild with plantarchitecture enabled."
        )

    if not target_UUIDs:
        raise ValueError("Target UUIDs list cannot be empty")

    # Convert to ctypes array
    uuid_count = len(target_UUIDs)
    uuid_array = (ctypes.c_uint * uuid_count)(*target_UUIDs)

    result = helios_lib.setStaticObstacles(plantarch_ptr, uuid_array, uuid_count)

    if result != 0:
        raise RuntimeError("Failed to set static obstacles")

def getPlantCollisionRelevantObjectIDs(plantarch_ptr: ctypes.POINTER(UPlantArchitecture),
                                      plant_id: int) -> List[int]:
    """Get object IDs of collision-relevant geometry for a plant"""
    if not _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PlantArchitecture methods not available. Rebuild with plantarchitecture enabled."
        )

    if plant_id < 0:
        raise ValueError("Plant ID must be non-negative")

    # Get array from C++
    count = ctypes.c_int()
    ptr = helios_lib.getPlantCollisionRelevantObjectIDs(plantarch_ptr, plant_id, ctypes.byref(count))

    # Convert to Python list
    if ptr and count.value > 0:
        return [ptr[i] for i in range(count.value)]
    else:
        return []

# File I/O wrapper functions
def writePlantMeshVertices(plantarch_ptr: ctypes.POINTER(UPlantArchitecture),
                          plant_id: int, filename: str) -> None:
    """Write all plant mesh vertices to file"""
    if not _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PlantArchitecture methods not available. Rebuild with plantarchitecture enabled."
        )

    if plant_id < 0:
        raise ValueError("Plant ID must be non-negative")
    if not filename:
        raise ValueError("Filename cannot be empty")

    filename_bytes = filename.encode('utf-8')
    result = helios_lib.writePlantMeshVertices(plantarch_ptr, plant_id, filename_bytes)
    if result != 0:
        raise RuntimeError(f"Failed to write plant mesh vertices to {filename}")

def writePlantStructureXML(plantarch_ptr: ctypes.POINTER(UPlantArchitecture),
                          plant_id: int, filename: str) -> None:
    """Write plant structure to XML file"""
    if not _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PlantArchitecture methods not available. Rebuild with plantarchitecture enabled."
        )

    if plant_id < 0:
        raise ValueError("Plant ID must be non-negative")
    if not filename:
        raise ValueError("Filename cannot be empty")

    filename_bytes = filename.encode('utf-8')
    result = helios_lib.writePlantStructureXML(plantarch_ptr, plant_id, filename_bytes)
    if result != 0:
        raise RuntimeError(f"Failed to write plant structure XML to {filename}")

def writeQSMCylinderFile(plantarch_ptr: ctypes.POINTER(UPlantArchitecture),
                        plant_id: int, filename: str) -> None:
    """Write plant structure in TreeQSM cylinder format"""
    if not _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PlantArchitecture methods not available. Rebuild with plantarchitecture enabled."
        )

    if plant_id < 0:
        raise ValueError("Plant ID must be non-negative")
    if not filename:
        raise ValueError("Filename cannot be empty")

    filename_bytes = filename.encode('utf-8')
    result = helios_lib.writeQSMCylinderFile(plantarch_ptr, plant_id, filename_bytes)
    if result != 0:
        raise RuntimeError(f"Failed to write QSM cylinder file to {filename}")

def readPlantStructureXML(plantarch_ptr: ctypes.POINTER(UPlantArchitecture),
                         filename: str, quiet: bool = False) -> List[int]:
    """Read plant structure from XML file"""
    if not _PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PlantArchitecture methods not available. Rebuild with plantarchitecture enabled."
        )

    if not filename:
        raise ValueError("Filename cannot be empty")

    filename_bytes = filename.encode('utf-8')

    # Output parameters
    plant_ids_ptr = ctypes.POINTER(ctypes.c_uint)()
    num_plants = ctypes.c_int()

    # Call function
    result = helios_lib.readPlantStructureXML(
        plantarch_ptr, filename_bytes, ctypes.c_bool(quiet),
        ctypes.byref(plant_ids_ptr), ctypes.byref(num_plants)
    )

    if result != 0:
        raise RuntimeError(f"Failed to read plant structure XML from {filename}")

    # Convert to Python list
    if plant_ids_ptr and num_plants.value > 0:
        return [plant_ids_ptr[i] for i in range(num_plants.value)]
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