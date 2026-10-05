"""
Ctypes wrapper for PlantHydraulicsModel C++ bindings.

This module provides low-level ctypes bindings to interface with
the native Helios PlantHydraulicsModel plugin via the C++ wrapper layer.
"""

import ctypes
from typing import List, Optional, Sequence

from ..plugins import helios_lib
from ..exceptions import check_helios_error

# Define the UPlantHydraulicsModel struct
class UPlantHydraulicsModel(ctypes.Structure):
    """Opaque structure for PlantHydraulicsModel C++ class"""
    pass

# Import UContext from main wrapper to avoid type conflicts
from .UContextWrapper import UContext

# Array sizes shared with native/include/pyhelios_wrapper_planthydraulics.h
CONDUCTANCE_SIZE = 4
CAPACITANCE_SIZE = 5
COEFFICIENT_SIZE = 25

# Error checking callback
def _check_error(result, func, args):
    """Automatic error checking for all plant hydraulics functions"""
    check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage, helios_lib.clearError)
    return result

_MODEL = ctypes.POINTER(UPlantHydraulicsModel)
_UUIDS = [ctypes.POINTER(ctypes.c_uint), ctypes.c_uint]
_FLOATS = ctypes.POINTER(ctypes.c_float)

# Try to set up PlantHydraulicsModel function prototypes
try:
    # PlantHydraulicsModel creation and destruction
    helios_lib.createPlantHydraulicsModel.argtypes = [ctypes.POINTER(UContext)]
    helios_lib.createPlantHydraulicsModel.restype = _MODEL
    helios_lib.createPlantHydraulicsModel.errcheck = _check_error

    helios_lib.destroyPlantHydraulicsModel.argtypes = [_MODEL]
    helios_lib.destroyPlantHydraulicsModel.restype = None
    # Note: destroyPlantHydraulicsModel doesn't need errcheck as it doesn't fail

    # Model coefficients
    helios_lib.setPlantHydraulicsModelCoefficients.argtypes = [_MODEL, _FLOATS, ctypes.c_uint, ctypes.c_char_p]
    helios_lib.setPlantHydraulicsModelCoefficients.restype = None
    helios_lib.setPlantHydraulicsModelCoefficients.errcheck = _check_error

    helios_lib.setPlantHydraulicsModelCoefficientsForUUIDs.argtypes = [_MODEL, _FLOATS, ctypes.c_uint, ctypes.c_char_p] + _UUIDS
    helios_lib.setPlantHydraulicsModelCoefficientsForUUIDs.restype = None
    helios_lib.setPlantHydraulicsModelCoefficientsForUUIDs.errcheck = _check_error

    helios_lib.setPlantHydraulicsModelCoefficientsFromLibrary.argtypes = [_MODEL, ctypes.c_char_p]
    helios_lib.setPlantHydraulicsModelCoefficientsFromLibrary.restype = None
    helios_lib.setPlantHydraulicsModelCoefficientsFromLibrary.errcheck = _check_error

    helios_lib.setPlantHydraulicsModelCoefficientsFromLibraryForUUIDs.argtypes = [_MODEL, ctypes.c_char_p] + _UUIDS
    helios_lib.setPlantHydraulicsModelCoefficientsFromLibraryForUUIDs.restype = None
    helios_lib.setPlantHydraulicsModelCoefficientsFromLibraryForUUIDs.errcheck = _check_error

    helios_lib.getPlantHydraulicsModelCoefficients.argtypes = [_MODEL, ctypes.c_uint, _FLOATS, ctypes.c_uint]
    helios_lib.getPlantHydraulicsModelCoefficients.restype = None
    helios_lib.getPlantHydraulicsModelCoefficients.errcheck = _check_error

    helios_lib.getPlantHydraulicsModelCoefficientsFromLibrary.argtypes = [_MODEL, ctypes.c_char_p, _FLOATS, ctypes.c_uint]
    helios_lib.getPlantHydraulicsModelCoefficientsFromLibrary.restype = None
    helios_lib.getPlantHydraulicsModelCoefficientsFromLibrary.errcheck = _check_error

    # Core execution methods
    helios_lib.runPlantHydraulicsModel.argtypes = [_MODEL, ctypes.c_int, ctypes.c_int]
    helios_lib.runPlantHydraulicsModel.restype = None
    helios_lib.runPlantHydraulicsModel.errcheck = _check_error

    helios_lib.runPlantHydraulicsModelForUUIDs.argtypes = [_MODEL] + _UUIDS + [ctypes.c_int, ctypes.c_int]
    helios_lib.runPlantHydraulicsModelForUUIDs.restype = None
    helios_lib.runPlantHydraulicsModelForUUIDs.errcheck = _check_error

    # Optional output primitive data
    helios_lib.setPlantHydraulicsOutputConductancePrimitiveData.argtypes = [_MODEL, ctypes.c_bool]
    helios_lib.setPlantHydraulicsOutputConductancePrimitiveData.restype = None
    helios_lib.setPlantHydraulicsOutputConductancePrimitiveData.errcheck = _check_error

    helios_lib.setPlantHydraulicsOutputCapacitancePrimitiveData.argtypes = [_MODEL, ctypes.c_bool]
    helios_lib.setPlantHydraulicsOutputCapacitancePrimitiveData.restype = None
    helios_lib.setPlantHydraulicsOutputCapacitancePrimitiveData.errcheck = _check_error

    # Plant grouping
    helios_lib.groupPlantHydraulicsPrimitivesIntoPlantObject.argtypes = [_MODEL] + _UUIDS
    helios_lib.groupPlantHydraulicsPrimitivesIntoPlantObject.restype = None
    helios_lib.groupPlantHydraulicsPrimitivesIntoPlantObject.errcheck = _check_error

    helios_lib.getPlantHydraulicsPlantID.argtypes = [_MODEL, ctypes.c_uint]
    helios_lib.getPlantHydraulicsPlantID.restype = ctypes.c_int
    helios_lib.getPlantHydraulicsPlantID.errcheck = _check_error

    helios_lib.getPlantHydraulicsPlantIDForUUIDs.argtypes = [_MODEL] + _UUIDS
    helios_lib.getPlantHydraulicsPlantIDForUUIDs.restype = ctypes.c_int
    helios_lib.getPlantHydraulicsPlantIDForUUIDs.errcheck = _check_error

    helios_lib.getPlantHydraulicsUniquePlantIDs.argtypes = [_MODEL] + _UUIDS + [ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getPlantHydraulicsUniquePlantIDs.restype = ctypes.POINTER(ctypes.c_int)
    helios_lib.getPlantHydraulicsUniquePlantIDs.errcheck = _check_error

    helios_lib.getPlantHydraulicsPrimitivesByPlantID.argtypes = [_MODEL, ctypes.c_int, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getPlantHydraulicsPrimitivesByPlantID.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.getPlantHydraulicsPrimitivesByPlantID.errcheck = _check_error

    helios_lib.getPlantHydraulicsPrimitivesWithoutPlantID.argtypes = [_MODEL] + _UUIDS + [ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getPlantHydraulicsPrimitivesWithoutPlantID.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.getPlantHydraulicsPrimitivesWithoutPlantID.errcheck = _check_error

    # Water potentials
    for _compartment in ("Stem", "Root", "Soil"):
        _func = getattr(helios_lib, f"getPlantHydraulics{_compartment}WaterPotential")
        _func.argtypes = [_MODEL, ctypes.c_uint]
        _func.restype = ctypes.c_float
        _func.errcheck = _check_error

        _func = getattr(helios_lib, f"getPlantHydraulics{_compartment}WaterPotentialForUUIDs")
        _func.argtypes = [_MODEL] + _UUIDS
        _func.restype = ctypes.c_float
        _func.errcheck = _check_error

        _func = getattr(helios_lib, f"getPlantHydraulics{_compartment}WaterPotentialOfPlant")
        _func.argtypes = [_MODEL, ctypes.c_uint]
        _func.restype = ctypes.c_float
        _func.errcheck = _check_error

    helios_lib.setPlantHydraulicsSoilWaterPotentialOfPlant.argtypes = [_MODEL, ctypes.c_uint, ctypes.c_float]
    helios_lib.setPlantHydraulicsSoilWaterPotentialOfPlant.restype = None
    helios_lib.setPlantHydraulicsSoilWaterPotentialOfPlant.errcheck = _check_error

    # Pressure-volume and vulnerability curve functions
    for _name in ("OsmoticPotential", "TurgorPressure", "WaterPotential", "Capacitance"):
        _func = getattr(helios_lib, f"computePlantHydraulics{_name}")
        _func.argtypes = [_FLOATS, ctypes.c_float]
        _func.restype = ctypes.c_float
        _func.errcheck = _check_error

    helios_lib.computePlantHydraulicsConductance.argtypes = [_FLOATS, ctypes.c_float, ctypes.c_float]
    helios_lib.computePlantHydraulicsConductance.restype = ctypes.c_float
    helios_lib.computePlantHydraulicsConductance.errcheck = _check_error

    # Mark that PlantHydraulicsModel functions are available
    _PLANTHYDRAULICS_FUNCTIONS_AVAILABLE = True

except AttributeError:
    # PlantHydraulicsModel functions not available in current native library
    _PLANTHYDRAULICS_FUNCTIONS_AVAILABLE = False


# Python wrapper functions with validation

def _require_available() -> None:
    if not _PLANTHYDRAULICS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "PlantHydraulicsModel functions not available in current Helios library. "
            "Rebuild PyHelios with 'planthydraulics' enabled:\n"
            "  build_scripts/build_helios\n"
            "System requirements:\n"
            "  - Platforms: Windows, Linux, macOS\n"
            "  - No GPU required\n"
            "  - No special dependencies"
        )


def _require_model(model) -> None:
    _require_available()
    if not model:
        raise ValueError("PlantHydraulicsModel instance is None.")


def _uuid_array(uuids: Sequence[int]):
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")
    return (ctypes.c_uint * len(uuids))(*uuids), ctypes.c_uint(len(uuids))


def _float_array(values: Sequence[float], size: int, name: str):
    if len(values) != size:
        raise ValueError(f"{name} array must have {size} elements, got {len(values)}.")
    return (ctypes.c_float * size)(*values)


def _encode_species(species: Optional[str]):
    return species.encode('utf-8') if species else None


def createPlantHydraulicsModel(context) -> ctypes.POINTER(UPlantHydraulicsModel):
    """Create a new PlantHydraulicsModel instance"""
    _require_available()

    # Explicit type coercion to fix Windows ctypes type identity issue
    # Ensures context is properly cast to the expected ctypes.POINTER(UContext) type
    if context is not None:
        context_ptr = ctypes.cast(context, ctypes.POINTER(UContext))
        return helios_lib.createPlantHydraulicsModel(context_ptr)
    else:
        raise ValueError("Context cannot be None")


def destroyPlantHydraulicsModel(model: ctypes.POINTER(UPlantHydraulicsModel)) -> None:
    """Destroy PlantHydraulicsModel instance"""
    if model and _PLANTHYDRAULICS_FUNCTIONS_AVAILABLE:
        helios_lib.destroyPlantHydraulicsModel(model)


def setModelCoefficients(model, coefficients: Sequence[float], leaf_capacitance_species: Optional[str] = None) -> None:
    """Set model coefficients for all primitives"""
    _require_model(model)
    coeff_array = _float_array(coefficients, COEFFICIENT_SIZE, "Coefficients")
    helios_lib.setPlantHydraulicsModelCoefficients(model, coeff_array, COEFFICIENT_SIZE, _encode_species(leaf_capacitance_species))


def setModelCoefficientsForUUIDs(model, coefficients: Sequence[float], uuids: Sequence[int],
                                 leaf_capacitance_species: Optional[str] = None) -> None:
    """Set model coefficients for specific primitives"""
    _require_model(model)
    coeff_array = _float_array(coefficients, COEFFICIENT_SIZE, "Coefficients")
    uuid_array, uuid_count = _uuid_array(uuids)
    helios_lib.setPlantHydraulicsModelCoefficientsForUUIDs(
        model, coeff_array, COEFFICIENT_SIZE, _encode_species(leaf_capacitance_species), uuid_array, uuid_count)


def setModelCoefficientsFromLibrary(model, species: str) -> None:
    """Set model coefficients from the species library for all primitives"""
    _require_model(model)
    if not species:
        raise ValueError("Species name cannot be empty.")
    helios_lib.setPlantHydraulicsModelCoefficientsFromLibrary(model, species.encode('utf-8'))


def setModelCoefficientsFromLibraryForUUIDs(model, species: str, uuids: Sequence[int]) -> None:
    """Set model coefficients from the species library for specific primitives"""
    _require_model(model)
    if not species:
        raise ValueError("Species name cannot be empty.")
    uuid_array, uuid_count = _uuid_array(uuids)
    helios_lib.setPlantHydraulicsModelCoefficientsFromLibraryForUUIDs(model, species.encode('utf-8'), uuid_array, uuid_count)


def getModelCoefficients(model, uuid: int) -> List[float]:
    """Get the coefficients held for one primitive, in the COEFFICIENT_SIZE layout"""
    _require_model(model)
    coeff_array = (ctypes.c_float * COEFFICIENT_SIZE)()
    helios_lib.getPlantHydraulicsModelCoefficients(model, uuid, coeff_array, COEFFICIENT_SIZE)
    return list(coeff_array)


def getModelCoefficientsFromLibrary(model, species: str) -> List[float]:
    """Get a species' library coefficients, in the COEFFICIENT_SIZE layout"""
    _require_model(model)
    if not species:
        raise ValueError("Species name cannot be empty.")
    coeff_array = (ctypes.c_float * COEFFICIENT_SIZE)()
    helios_lib.getPlantHydraulicsModelCoefficientsFromLibrary(model, species.encode('utf-8'), coeff_array, COEFFICIENT_SIZE)
    return list(coeff_array)


def run(model, timespan: int, timestep: int) -> None:
    """Run the model for all primitives in the Context"""
    _require_model(model)
    helios_lib.runPlantHydraulicsModel(model, ctypes.c_int(timespan), ctypes.c_int(timestep))


def runForUUIDs(model, uuids: Sequence[int], timespan: int, timestep: int) -> None:
    """Run the model for specific primitives"""
    _require_model(model)
    uuid_array, uuid_count = _uuid_array(uuids)
    helios_lib.runPlantHydraulicsModelForUUIDs(model, uuid_array, uuid_count, ctypes.c_int(timespan), ctypes.c_int(timestep))


def outputConductancePrimitiveData(model, toggle: bool) -> None:
    """Toggle writing of the optional 'hydraulic_conductance' primitive data"""
    _require_model(model)
    helios_lib.setPlantHydraulicsOutputConductancePrimitiveData(model, ctypes.c_bool(toggle))


def outputCapacitancePrimitiveData(model, toggle: bool) -> None:
    """Toggle writing of the optional 'hydraulic_capacitance' primitive data"""
    _require_model(model)
    helios_lib.setPlantHydraulicsOutputCapacitancePrimitiveData(model, ctypes.c_bool(toggle))


def groupPrimitivesIntoPlantObject(model, uuids: Sequence[int]) -> None:
    """Group primitives into a plant that shares stem, root and soil hydraulics"""
    _require_model(model)
    uuid_array, uuid_count = _uuid_array(uuids)
    helios_lib.groupPlantHydraulicsPrimitivesIntoPlantObject(model, uuid_array, uuid_count)


def getPlantID(model, uuid: int) -> int:
    """Get the plantID of a primitive"""
    _require_model(model)
    return helios_lib.getPlantHydraulicsPlantID(model, ctypes.c_uint(uuid))


def getPlantIDForUUIDs(model, uuids: Sequence[int]) -> int:
    """Get the plantID of a set of primitives. The native call compares only the first and last primitive."""
    _require_model(model)
    uuid_array, uuid_count = _uuid_array(uuids)
    return helios_lib.getPlantHydraulicsPlantIDForUUIDs(model, uuid_array, uuid_count)


def getUniquePlantIDs(model, uuids: Sequence[int]) -> List[int]:
    """Get the unique plantIDs of a set of primitives"""
    _require_model(model)
    uuid_array, uuid_count = _uuid_array(uuids)
    count = ctypes.c_uint(0)
    ptr = helios_lib.getPlantHydraulicsUniquePlantIDs(model, uuid_array, uuid_count, ctypes.byref(count))
    return list(ptr[:count.value]) if ptr and count.value > 0 else []


def getPrimitivesByPlantID(model, plant_id: int) -> List[int]:
    """Get the primitives belonging to a plantID"""
    _require_model(model)
    count = ctypes.c_uint(0)
    ptr = helios_lib.getPlantHydraulicsPrimitivesByPlantID(model, ctypes.c_int(plant_id), ctypes.byref(count))
    return list(ptr[:count.value]) if ptr and count.value > 0 else []


def getPrimitivesWithoutPlantID(model, uuids: Sequence[int]) -> List[int]:
    """Get the primitives that have no plantID"""
    _require_model(model)
    uuid_array, uuid_count = _uuid_array(uuids)
    count = ctypes.c_uint(0)
    ptr = helios_lib.getPlantHydraulicsPrimitivesWithoutPlantID(model, uuid_array, uuid_count, ctypes.byref(count))
    return list(ptr[:count.value]) if ptr and count.value > 0 else []


def getWaterPotential(model, compartment: str, uuid: int) -> float:
    """Get the 'Stem', 'Root' or 'Soil' water potential of the plant a primitive belongs to"""
    _require_model(model)
    return getattr(helios_lib, f"getPlantHydraulics{compartment}WaterPotential")(model, ctypes.c_uint(uuid))


def getWaterPotentialForUUIDs(model, compartment: str, uuids: Sequence[int]) -> float:
    """Get the 'Stem', 'Root' or 'Soil' water potential of the plant a set of primitives belongs to"""
    _require_model(model)
    uuid_array, uuid_count = _uuid_array(uuids)
    return getattr(helios_lib, f"getPlantHydraulics{compartment}WaterPotentialForUUIDs")(model, uuid_array, uuid_count)


def getWaterPotentialOfPlant(model, compartment: str, plant_id: int) -> float:
    """Get the 'Stem', 'Root' or 'Soil' water potential of a plant"""
    _require_model(model)
    return getattr(helios_lib, f"getPlantHydraulics{compartment}WaterPotentialOfPlant")(model, ctypes.c_uint(plant_id))


def setSoilWaterPotentialOfPlant(model, plant_id: int, soil_water_potential: float) -> None:
    """Set the soil water potential of a plant"""
    _require_model(model)
    helios_lib.setPlantHydraulicsSoilWaterPotentialOfPlant(model, ctypes.c_uint(plant_id), ctypes.c_float(soil_water_potential))


def computeOsmoticPotential(capacitance: Sequence[float], relative_water_content: float) -> float:
    """Osmotic potential (MPa) from the pressure-volume curve"""
    _require_available()
    return helios_lib.computePlantHydraulicsOsmoticPotential(
        _float_array(capacitance, CAPACITANCE_SIZE, "Capacitance"), ctypes.c_float(relative_water_content))


def computeTurgorPressure(capacitance: Sequence[float], relative_water_content: float) -> float:
    """Turgor pressure (MPa) from the pressure-volume curve"""
    _require_available()
    return helios_lib.computePlantHydraulicsTurgorPressure(
        _float_array(capacitance, CAPACITANCE_SIZE, "Capacitance"), ctypes.c_float(relative_water_content))


def computeWaterPotential(capacitance: Sequence[float], relative_water_content: float) -> float:
    """Water potential (MPa) from the pressure-volume curve"""
    _require_available()
    return helios_lib.computePlantHydraulicsWaterPotential(
        _float_array(capacitance, CAPACITANCE_SIZE, "Capacitance"), ctypes.c_float(relative_water_content))


def computeCapacitance(capacitance: Sequence[float], relative_water_content: float) -> float:
    """Hydraulic capacitance (mol/m²/MPa) from the pressure-volume curve"""
    _require_available()
    return helios_lib.computePlantHydraulicsCapacitance(
        _float_array(capacitance, CAPACITANCE_SIZE, "Capacitance"), ctypes.c_float(relative_water_content))


def computeConductance(conductance: Sequence[float], water_potential: float, temperature: float) -> float:
    """Hydraulic conductance (mol/m²/s/MPa) from the vulnerability curve"""
    _require_available()
    return helios_lib.computePlantHydraulicsConductance(
        _float_array(conductance, CONDUCTANCE_SIZE, "Conductance"), ctypes.c_float(water_potential), ctypes.c_float(temperature))

