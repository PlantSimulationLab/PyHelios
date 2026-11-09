"""
Ctypes wrapper for SoilTransportModel C++ bindings.

This module provides low-level ctypes bindings to interface with
the native Helios SoilTransportModel plugin via the C++ wrapper layer.
"""

import ctypes
from typing import List, Sequence, Tuple

from ..plugins import helios_lib
from ..exceptions import check_helios_error


class USoilTransportModel(ctypes.Structure):
    """Opaque structure for SoilTransportModel C++ class"""
    pass


# Import UContext from main wrapper to avoid type conflicts
from .UContextWrapper import UContext


# ctypes mirrors of the structs in native/include/pyhelios_wrapper_soiltransport.h.
# Field order must match the C declarations exactly.

class CSoilProperties(ctypes.Structure):
    _fields_ = [
        ("theta_r", ctypes.c_float),
        ("theta_s", ctypes.c_float),
        ("alpha", ctypes.c_float),
        ("n", ctypes.c_float),
        ("K_s", ctypes.c_float),
        ("model", ctypes.c_int),
        ("h_e", ctypes.c_float),
        ("kr_spline_start", ctypes.c_float),
    ]


class CSolverParameters(ctypes.Structure):
    _fields_ = [
        ("max_picard_iterations", ctypes.c_uint),
        ("enable_gravity", ctypes.c_int),
        ("substep_on_failure", ctypes.c_int),
        ("picard_tolerance", ctypes.c_float),
        ("dt_min", ctypes.c_float),
        ("dt_max", ctypes.c_float),
        ("horizontal_coupling_interval", ctypes.c_uint),
        ("C_regularization", ctypes.c_float),
        ("K_min", ctypes.c_float),
        ("picard_omega", ctypes.c_float),
        ("K_weighting", ctypes.c_int),
        ("anderson_depth", ctypes.c_int),
        ("nonlinear_method", ctypes.c_int),
        ("num_threads", ctypes.c_int),
        ("bdf2", ctypes.c_int),
        ("adaptive_dt", ctypes.c_int),
        ("dt_target_rel_change", ctypes.c_float),
        ("dt_safety", ctypes.c_float),
        ("dt_growth_max", ctypes.c_float),
        ("dt_reduction_min", ctypes.c_float),
        ("dt_failure_factor", ctypes.c_float),
    ]


class CRootDistributionParams(ctypes.Structure):
    _fields_ = [(name, ctypes.c_float) for name in
                ("plant_x", "plant_y", "plant_z", "z_max", "r_max", "z_star", "r_star", "pz", "pr", "total_root_length")]


class CWeibullRootParameters(ctypes.Structure):
    _fields_ = [
        ("plant_x", ctypes.c_float),
        ("plant_y", ctypes.c_float),
        ("z_max", ctypes.c_float),
        ("shape_z", ctypes.c_float),
        ("scale_z", ctypes.c_float),
        ("radial", ctypes.c_int),
        ("r_max", ctypes.c_float),
        ("shape_r", ctypes.c_float),
        ("scale_r", ctypes.c_float),
        ("total_root_length", ctypes.c_float),
    ]


def _check_error(result, func, args):
    """Automatic error checking for all soil transport functions"""
    check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage, helios_lib.clearError)
    return result


_M = ctypes.POINTER(USoilTransportModel)
_F = ctypes.c_float
_U = ctypes.c_uint
_I = ctypes.c_int
_U64 = ctypes.c_ulonglong
_VEC3 = ctypes.POINTER(ctypes.c_float)
_COUNT = ctypes.POINTER(ctypes.c_uint)
_STR = ctypes.c_char_p

# name: (argtypes, restype)
_PROTOTYPES = {
    "createSoilTransportModel": ([ctypes.POINTER(UContext)], _M),
    # domain setup
    "soilTransportDefineSoilDomain": ([_M, _VEC3, _VEC3], None),
    "soilTransportSetGridResolution": ([_M, _U, _U, _U], None),
    "soilTransportSetColumnResolution": ([_M, _U], None),
    "soilTransportSetColumnGrid": ([_M, _U, _U], None),
    "soilTransportInitializeDomain": ([_M], None),
    # soil properties
    "soilTransportSetSoilProperties": ([_M, ctypes.POINTER(CSoilProperties)], None),
    "soilTransportSetSoilPropertiesColumn": ([_M, _U, _U, ctypes.POINTER(CSoilProperties)], None),
    "soilTransportSetSoilPropertiesFromTexture": ([_M, _STR], None),
    "soilTransportSetSoilPropertiesFromTextureModel": ([_M, _STR, _I, _I], None),
    # initial and boundary conditions
    "soilTransportSetInitialCondition": ([_M, _F], None),
    "soilTransportSetInitialConditionHydrostatic": ([_M, _F], None),
    "soilTransportSetTopBoundaryFlux": ([_M, _F], None),
    "soilTransportSetSurfaceEvaporation": ([_M, _F, _F], _F),
    "soilTransportSetTopBoundaryPressure": ([_M, _F], None),
    "soilTransportSetBottomBoundaryFreeDrainage": ([_M], None),
    "soilTransportSetBottomBoundaryPressure": ([_M, _F], None),
    "soilTransportSetBottomBoundaryFlux": ([_M, _F], None),
    "soilTransportAddSurfaceEmitter": ([_M, _F, _F, _F, _F], None),
    "soilTransportClearSurfaceEmitters": ([_M], None),
    # root coupling
    "soilTransportEnableRootUptake": ([_M], None),
    "soilTransportSetRootDistribution": ([_M, _U, ctypes.POINTER(CRootDistributionParams)], None),
    "soilTransportSetRootDistributionWeibull": ([_M, _U, ctypes.POINTER(CWeibullRootParameters)], None),
    "soilTransportSetRootRadialConductivity": ([_M, _F], None),
    "soilTransportSetRootWaterStressParameters": ([_M, _F, _F, _F], None),
    "soilTransportSetTranspiration": ([_M, _U, _F], None),
    # solver configuration
    "soilTransportSetSolverType": ([_M, _I], None),
    "soilTransportEnableHorizontalCoupling": ([_M, _U], None),
    "soilTransportSetSolverParameters": ([_M, ctypes.POINTER(CSolverParameters)], None),
    "soilTransportEnableGPU": ([_M], None),
    "soilTransportDisableGPU": ([_M], None),
    "soilTransportIsGPUEnabled": ([_M], _I),
    "soilTransportIsGPUAvailable": ([], _I),
    # run
    "runSoilTransportModel": ([_M, _F], None),
    # output for coupling
    "soilTransportGetSoilWaterPotential": ([_M, _U], _F),
    "soilTransportGetWaterContent": ([_M, _VEC3], _F),
    "soilTransportGetPressureHead": ([_M, _VEC3], _F),
    # point sensors
    "soilTransportAddSensor": ([_M, _VEC3, _I], _U),
    "soilTransportRecordSensors": ([_M], None),
    "soilTransportGetSensorCount": ([_M], _U),
    "soilTransportGetSensorData": ([_M, _U, _COUNT], ctypes.POINTER(ctypes.c_float)),
    "soilTransportGetSensorTimes": ([_M, _U, _COUNT], ctypes.POINTER(ctypes.c_float)),
    "soilTransportGetSensorPosition": ([_M, _U, _VEC3], None),
    "soilTransportGetSensorQuantity": ([_M, _U], _I),
    "soilTransportClearSensorData": ([_M], None),
    "soilTransportWriteSensorData": ([_M, _STR], None),
    # diagnostics and mass balance
    "soilTransportGetLastSubstepCount": ([_M], _U),
    "soilTransportResetSolverStats": ([_M], None),
    "soilTransportSolverPicardOuter": ([_M], _U64),
    "soilTransportSolverNewtonOuter": ([_M], _U64),
    "soilTransportSolverPicardGmres": ([_M], _U64),
    "soilTransportSolverNewtonGmres": ([_M], _U64),
    "soilTransportGetTimestep": ([_M], _F),
    "soilTransportGetSolverIterationCount": ([_M], _U64),
    "soilTransportResetSolverIterationCount": ([_M], None),
    "soilTransportGetTotalWaterStorage": ([_M], ctypes.c_double),
    "soilTransportGetCumulativeBoundaryInflux": ([_M], ctypes.c_double),
    "soilTransportGetMassBalanceResidual": ([_M], ctypes.c_double),
    "soilTransportResetMassBalance": ([_M], None),
    "soilTransportGetCumulativeRootUptake": ([_M, _U], _F),
    "soilTransportGetRootUptakeFlux": ([_M, _U], _F),
    # visualization
    "soilTransportAddSoilVisualization": ([_M, _I, _COUNT], ctypes.POINTER(ctypes.c_uint)),
    "soilTransportAddSoilVisualizationKeepFraction": ([_M, _I, _VEC3, _COUNT], ctypes.POINTER(ctypes.c_uint)),
    "soilTransportAddSoilVisualizationRegion": ([_M, _I, _VEC3, _VEC3, _I, _COUNT], ctypes.POINTER(ctypes.c_uint)),
    "soilTransportUpdateSoilVisualization": ([_M, ctypes.POINTER(ctypes.c_uint), _U, _I], None),
    # messages
    "soilTransportEnableMessages": ([_M], None),
    "soilTransportDisableMessages": ([_M], None),
    # soil property library
    "soilTransportGetSoilPropertiesFromTexture": ([_STR, ctypes.POINTER(CSoilProperties)], None),
    "soilTransportGetSoilPropertiesFromTextureModel": ([_STR, _I, _I, ctypes.POINTER(CSoilProperties)], None),
    "soilTransportToModifiedVanGenuchten": ([ctypes.POINTER(CSoilProperties), _F, _I, ctypes.POINTER(CSoilProperties)], None),
    "soilTransportGetAvailableSoilTextures": ([], _STR),
    "soilTransportIsSoilTextureAvailable": ([_STR], _I),
}

try:
    for _name, (_argtypes, _restype) in _PROTOTYPES.items():
        _fn = getattr(helios_lib, _name)
        _fn.argtypes = _argtypes
        _fn.restype = _restype
        _fn.errcheck = _check_error

    helios_lib.destroySoilTransportModel.argtypes = [_M]
    helios_lib.destroySoilTransportModel.restype = None
    # destroySoilTransportModel doesn't need errcheck as it doesn't fail

    _SOILTRANSPORT_FUNCTIONS_AVAILABLE = True
except AttributeError:
    # SoilTransportModel functions not available in current native library
    _SOILTRANSPORT_FUNCTIONS_AVAILABLE = False


def _require_available() -> None:
    if not _SOILTRANSPORT_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "SoilTransportModel functions not available in current Helios library. "
            "Rebuild PyHelios with 'soiltransport' enabled:\n"
            "  build_scripts/build_helios\n"
            "System requirements:\n"
            "  - Platforms: Windows, Linux, macOS\n"
            "  - GPU: optional (NVIDIA CUDA accelerates the full 3D solver)\n"
            "  - No special dependencies"
        )


def _require_model(model) -> None:
    _require_available()
    if not model:
        raise ValueError("SoilTransportModel instance is None.")


def _vec3(values: Sequence[float]):
    return (ctypes.c_float * 3)(*values)


def _encode(text: str) -> bytes:
    return text.encode('utf-8')


def _float_list(ptr, count: ctypes.c_uint) -> List[float]:
    return list(ptr[:count.value]) if ptr and count.value > 0 else []


def _uint_list(ptr, count: ctypes.c_uint) -> List[int]:
    return list(ptr[:count.value]) if ptr and count.value > 0 else []


# ---------------------------------------------------------------- model management

def createSoilTransportModel(context) -> ctypes.POINTER(USoilTransportModel):
    """Create a new SoilTransportModel instance"""
    _require_available()
    if context is None:
        raise ValueError("Context cannot be None")
    # Explicit cast fixes the Windows ctypes type identity issue
    context_ptr = ctypes.cast(context, ctypes.POINTER(UContext))
    return helios_lib.createSoilTransportModel(context_ptr)


def destroySoilTransportModel(model) -> None:
    """Destroy SoilTransportModel instance"""
    if model and _SOILTRANSPORT_FUNCTIONS_AVAILABLE:
        helios_lib.destroySoilTransportModel(model)


# ---------------------------------------------------------------- domain setup

def defineSoilDomain(model, origin: Sequence[float], extent: Sequence[float]) -> None:
    _require_model(model)
    helios_lib.soilTransportDefineSoilDomain(model, _vec3(origin), _vec3(extent))


def setGridResolution(model, nx: int, ny: int, nz: int) -> None:
    _require_model(model)
    helios_lib.soilTransportSetGridResolution(model, nx, ny, nz)


def setColumnResolution(model, nz: int) -> None:
    _require_model(model)
    helios_lib.soilTransportSetColumnResolution(model, nz)


def setColumnGrid(model, nx: int, ny: int) -> None:
    _require_model(model)
    helios_lib.soilTransportSetColumnGrid(model, nx, ny)


def initializeDomain(model) -> None:
    _require_model(model)
    helios_lib.soilTransportInitializeDomain(model)


# ---------------------------------------------------------------- soil properties

def setSoilProperties(model, props: CSoilProperties) -> None:
    _require_model(model)
    helios_lib.soilTransportSetSoilProperties(model, ctypes.byref(props))


def setSoilPropertiesColumn(model, i: int, j: int, props: CSoilProperties) -> None:
    _require_model(model)
    helios_lib.soilTransportSetSoilPropertiesColumn(model, i, j, ctypes.byref(props))


def setSoilPropertiesFromTexture(model, texture: str) -> None:
    _require_model(model)
    helios_lib.soilTransportSetSoilPropertiesFromTexture(model, _encode(texture))


def setSoilPropertiesFromTextureModel(model, texture: str, soil_model: int, match_standard_curves: bool) -> None:
    _require_model(model)
    helios_lib.soilTransportSetSoilPropertiesFromTextureModel(model, _encode(texture), soil_model, int(match_standard_curves))


# ---------------------------------------------------------------- initial and boundary conditions

def setInitialCondition(model, h_init: float) -> None:
    _require_model(model)
    helios_lib.soilTransportSetInitialCondition(model, h_init)


def setInitialConditionHydrostatic(model, water_table_depth: float) -> None:
    _require_model(model)
    helios_lib.soilTransportSetInitialConditionHydrostatic(model, water_table_depth)


def setTopBoundaryFlux(model, flux: float) -> None:
    _require_model(model)
    helios_lib.soilTransportSetTopBoundaryFlux(model, flux)


def setSurfaceEvaporation(model, potential_rate: float, aerodynamic_resistance: float) -> float:
    _require_model(model)
    return helios_lib.soilTransportSetSurfaceEvaporation(model, potential_rate, aerodynamic_resistance)


def setTopBoundaryPressure(model, h: float) -> None:
    _require_model(model)
    helios_lib.soilTransportSetTopBoundaryPressure(model, h)


def setBottomBoundaryFreeDrainage(model) -> None:
    _require_model(model)
    helios_lib.soilTransportSetBottomBoundaryFreeDrainage(model)


def setBottomBoundaryPressure(model, h: float) -> None:
    _require_model(model)
    helios_lib.soilTransportSetBottomBoundaryPressure(model, h)


def setBottomBoundaryFlux(model, flux: float) -> None:
    _require_model(model)
    helios_lib.soilTransportSetBottomBoundaryFlux(model, flux)


def addSurfaceEmitter(model, x: float, y: float, flow_rate: float, radius: float) -> None:
    _require_model(model)
    helios_lib.soilTransportAddSurfaceEmitter(model, x, y, flow_rate, radius)


def clearSurfaceEmitters(model) -> None:
    _require_model(model)
    helios_lib.soilTransportClearSurfaceEmitters(model)


# ---------------------------------------------------------------- root coupling

def enableRootUptake(model) -> None:
    _require_model(model)
    helios_lib.soilTransportEnableRootUptake(model)


def setRootDistribution(model, plant_id: int, params: CRootDistributionParams) -> None:
    _require_model(model)
    helios_lib.soilTransportSetRootDistribution(model, plant_id, ctypes.byref(params))


def setRootDistributionWeibull(model, plant_id: int, params: CWeibullRootParameters) -> None:
    _require_model(model)
    helios_lib.soilTransportSetRootDistributionWeibull(model, plant_id, ctypes.byref(params))


def setRootRadialConductivity(model, L_r: float) -> None:
    _require_model(model)
    helios_lib.soilTransportSetRootRadialConductivity(model, L_r)


def setRootWaterStressParameters(model, h_onset: float, h_wilting: float, omega_c: float) -> None:
    _require_model(model)
    helios_lib.soilTransportSetRootWaterStressParameters(model, h_onset, h_wilting, omega_c)


def setTranspiration(model, plant_id: int, transpiration: float) -> None:
    _require_model(model)
    helios_lib.soilTransportSetTranspiration(model, plant_id, transpiration)


# ---------------------------------------------------------------- solver configuration

def setSolverType(model, solver_type: int) -> None:
    _require_model(model)
    helios_lib.soilTransportSetSolverType(model, solver_type)


def enableHorizontalCoupling(model, interval: int) -> None:
    _require_model(model)
    helios_lib.soilTransportEnableHorizontalCoupling(model, interval)


def setSolverParameters(model, params: CSolverParameters) -> None:
    _require_model(model)
    helios_lib.soilTransportSetSolverParameters(model, ctypes.byref(params))


def enableGPU(model) -> None:
    _require_model(model)
    helios_lib.soilTransportEnableGPU(model)


def disableGPU(model) -> None:
    _require_model(model)
    helios_lib.soilTransportDisableGPU(model)


def isGPUEnabled(model) -> bool:
    _require_model(model)
    return bool(helios_lib.soilTransportIsGPUEnabled(model))


def isGPUAvailable() -> bool:
    _require_available()
    return bool(helios_lib.soilTransportIsGPUAvailable())


# ---------------------------------------------------------------- run

def run(model, dt: float) -> None:
    _require_model(model)
    helios_lib.runSoilTransportModel(model, dt)


# ---------------------------------------------------------------- output for coupling

def getSoilWaterPotential(model, plant_id: int) -> float:
    _require_model(model)
    return helios_lib.soilTransportGetSoilWaterPotential(model, plant_id)


def getWaterContent(model, position: Sequence[float]) -> float:
    _require_model(model)
    return helios_lib.soilTransportGetWaterContent(model, _vec3(position))


def getPressureHead(model, position: Sequence[float]) -> float:
    _require_model(model)
    return helios_lib.soilTransportGetPressureHead(model, _vec3(position))


# ---------------------------------------------------------------- point sensors

def addSensor(model, position: Sequence[float], quantity: int) -> int:
    _require_model(model)
    return helios_lib.soilTransportAddSensor(model, _vec3(position), quantity)


def recordSensors(model) -> None:
    _require_model(model)
    helios_lib.soilTransportRecordSensors(model)


def getSensorCount(model) -> int:
    _require_model(model)
    return helios_lib.soilTransportGetSensorCount(model)


def getSensorData(model, sensor_id: int) -> List[float]:
    _require_model(model)
    count = ctypes.c_uint(0)
    ptr = helios_lib.soilTransportGetSensorData(model, sensor_id, ctypes.byref(count))
    return _float_list(ptr, count)


def getSensorTimes(model, sensor_id: int) -> List[float]:
    _require_model(model)
    count = ctypes.c_uint(0)
    ptr = helios_lib.soilTransportGetSensorTimes(model, sensor_id, ctypes.byref(count))
    return _float_list(ptr, count)


def getSensorPosition(model, sensor_id: int) -> Tuple[float, float, float]:
    _require_model(model)
    out = (ctypes.c_float * 3)()
    helios_lib.soilTransportGetSensorPosition(model, sensor_id, out)
    return out[0], out[1], out[2]


def getSensorQuantity(model, sensor_id: int) -> int:
    _require_model(model)
    return helios_lib.soilTransportGetSensorQuantity(model, sensor_id)


def clearSensorData(model) -> None:
    _require_model(model)
    helios_lib.soilTransportClearSensorData(model)


def writeSensorData(model, filename: str) -> None:
    _require_model(model)
    helios_lib.soilTransportWriteSensorData(model, _encode(filename))


# ---------------------------------------------------------------- diagnostics and mass balance

def getLastSubstepCount(model) -> int:
    _require_model(model)
    return helios_lib.soilTransportGetLastSubstepCount(model)


def resetSolverStats(model) -> None:
    _require_model(model)
    helios_lib.soilTransportResetSolverStats(model)


def solverPicardOuter(model) -> int:
    _require_model(model)
    return helios_lib.soilTransportSolverPicardOuter(model)


def solverNewtonOuter(model) -> int:
    _require_model(model)
    return helios_lib.soilTransportSolverNewtonOuter(model)


def solverPicardGmres(model) -> int:
    _require_model(model)
    return helios_lib.soilTransportSolverPicardGmres(model)


def solverNewtonGmres(model) -> int:
    _require_model(model)
    return helios_lib.soilTransportSolverNewtonGmres(model)


def getTimestep(model) -> float:
    _require_model(model)
    return helios_lib.soilTransportGetTimestep(model)


def getSolverIterationCount(model) -> int:
    _require_model(model)
    return helios_lib.soilTransportGetSolverIterationCount(model)


def resetSolverIterationCount(model) -> None:
    _require_model(model)
    helios_lib.soilTransportResetSolverIterationCount(model)


def getTotalWaterStorage(model) -> float:
    _require_model(model)
    return helios_lib.soilTransportGetTotalWaterStorage(model)


def getCumulativeBoundaryInflux(model) -> float:
    _require_model(model)
    return helios_lib.soilTransportGetCumulativeBoundaryInflux(model)


def getMassBalanceResidual(model) -> float:
    _require_model(model)
    return helios_lib.soilTransportGetMassBalanceResidual(model)


def resetMassBalance(model) -> None:
    _require_model(model)
    helios_lib.soilTransportResetMassBalance(model)


def getCumulativeRootUptake(model, plant_id: int) -> float:
    _require_model(model)
    return helios_lib.soilTransportGetCumulativeRootUptake(model, plant_id)


def getRootUptakeFlux(model, plant_id: int) -> float:
    _require_model(model)
    return helios_lib.soilTransportGetRootUptakeFlux(model, plant_id)


# ---------------------------------------------------------------- visualization

def addSoilVisualization(model, mode: int) -> List[int]:
    _require_model(model)
    count = ctypes.c_uint(0)
    ptr = helios_lib.soilTransportAddSoilVisualization(model, mode, ctypes.byref(count))
    return _uint_list(ptr, count)


def addSoilVisualizationKeepFraction(model, mode: int, keep_fraction: Sequence[float]) -> List[int]:
    _require_model(model)
    count = ctypes.c_uint(0)
    ptr = helios_lib.soilTransportAddSoilVisualizationKeepFraction(model, mode, _vec3(keep_fraction), ctypes.byref(count))
    return _uint_list(ptr, count)


def addSoilVisualizationRegion(model, mode: int, fraction_min: Sequence[float], fraction_max: Sequence[float], region: int) -> List[int]:
    _require_model(model)
    count = ctypes.c_uint(0)
    ptr = helios_lib.soilTransportAddSoilVisualizationRegion(model, mode, _vec3(fraction_min), _vec3(fraction_max), region, ctypes.byref(count))
    return _uint_list(ptr, count)


def updateSoilVisualization(model, uuids: Sequence[int], mode: int) -> None:
    _require_model(model)
    array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.soilTransportUpdateSoilVisualization(model, array, len(uuids), mode)


# ---------------------------------------------------------------- messages

def enableMessages(model) -> None:
    _require_model(model)
    helios_lib.soilTransportEnableMessages(model)


def disableMessages(model) -> None:
    _require_model(model)
    helios_lib.soilTransportDisableMessages(model)


# ---------------------------------------------------------------- soil property library

def getSoilPropertiesFromTexture(texture: str) -> CSoilProperties:
    _require_available()
    out = CSoilProperties()
    helios_lib.soilTransportGetSoilPropertiesFromTexture(_encode(texture), ctypes.byref(out))
    return out


def getSoilPropertiesFromTextureModel(texture: str, soil_model: int, match_standard_curves: bool) -> CSoilProperties:
    _require_available()
    out = CSoilProperties()
    helios_lib.soilTransportGetSoilPropertiesFromTextureModel(_encode(texture), soil_model, int(match_standard_curves), ctypes.byref(out))
    return out


def toModifiedVanGenuchten(vg: CSoilProperties, h_e: float, match_standard_curves: bool) -> CSoilProperties:
    _require_available()
    out = CSoilProperties()
    helios_lib.soilTransportToModifiedVanGenuchten(ctypes.byref(vg), h_e, int(match_standard_curves), ctypes.byref(out))
    return out


def getAvailableSoilTextures() -> List[str]:
    _require_available()
    joined = helios_lib.soilTransportGetAvailableSoilTextures()
    if not joined:
        return []
    return joined.decode('utf-8').split('\n')


def isSoilTextureAvailable(texture: str) -> bool:
    _require_available()
    return bool(helios_lib.soilTransportIsSoilTextureAvailable(_encode(texture)))
