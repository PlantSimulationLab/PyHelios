"""
High-level SoilTransport interface for PyHelios.

This module provides a user-friendly interface to the soil water transport plugin, which solves
the Richards equation for variably saturated water flow in soil, with optional coupling to plant
root systems.
"""

import logging
import math
import numbers
from dataclasses import dataclass, fields
from enum import IntEnum
from typing import List, Optional

from .plugins.registry import get_plugin_registry
from .wrappers import USoilTransportWrapper as soil_wrapper
from .wrappers.DataTypes import vec3
from .Context import Context, check_context_alive
from .exceptions import HeliosError

logger = logging.getLogger(__name__)


class SoilTransportModelError(HeliosError):
    """Exception raised for SoilTransport-specific errors."""
    pass


# ----------------------------------------------------------------------------------------------
# Enumerations (values match the C++ enums in SoilUtils.h)
# ----------------------------------------------------------------------------------------------

class SoilModel(IntEnum):
    """Soil constitutive model."""
    #: Mualem-van Genuchten model (default)
    VAN_GENUCHTEN = 0
    #: Gardner exponential model: K(h) = K_s exp(alpha h)
    GARDNER = 1
    #: Mualem-van Genuchten with an air-entry head h_e < 0 (Ippisch, Vogel & Bastian 2006)
    MODIFIED_VAN_GENUCHTEN = 2
    #: Linear model: S_e = 1 + alpha h (0 below h = -1/alpha) and K = K_s S_e
    LINEAR = 3


class KWeighting(IntEnum):
    """Interblock hydraulic conductivity weighting scheme (face conductivity between cells)."""
    #: The recommended default for every solver: arithmetic
    DEFAULT = -1
    #: Geometric mean, sqrt(K1*K2)
    GEOMETRIC = 0
    #: Arithmetic mean, (K1+K2)/2
    ARITHMETIC = 1
    #: Donor cell by total head
    UPSTREAM = 2
    #: Harmonic mean, 2*K1*K2/(K1+K2)
    HARMONIC = 3
    #: Harmonic mean of saturated K times the donor cell's relative permeability (k_r = K/K_s)
    UPSTREAM_KR = 4


class NonlinearMethod(IntEnum):
    """Nonlinear iteration strategy for the 3D solver's per-step solve."""
    #: Modified Picard only: robust, linear convergence
    PICARD = 0
    #: Jacobian-free Newton-Krylov (JFNK)
    NEWTON = 1
    #: Picard warm-up, then Newton
    PICARD_NEWTON = 2
    #: Nonlinear Gauss-Seidel + FAS multigrid (lagged K)
    NGS_FAS = 3
    #: Kirchhoff-transform M-scheme; homogeneous soils only, CPU only
    M_SCHEME = 4
    #: (default) Newton-Raphson with an assembled analytic Jacobian and line search
    NEWTON_ANALYTIC = 5


class SolverType(IntEnum):
    """Solver mode."""
    #: Independent 1D columns (fastest)
    SOLVER_1D = 0
    #: 1D columns with periodic horizontal coupling
    SOLVER_QUASI_3D = 1
    #: Full 3D Richards equation
    SOLVER_3D = 2


class SoilColorMode(IntEnum):
    """Soil-domain visualization coloring mode (see SoilTransportModel.addSoilVisualization)."""
    #: Color the soil block by volumetric water content theta [m³/m³]
    WATER_CONTENT = 0
    #: Color the soil block by pressure head h [m]
    PRESSURE_HEAD = 1
    #: Plain dirt texture (no field coloring)
    TEXTURE = 2


class SoilMeasurement(IntEnum):
    """Quantity recorded by a soil point sensor (see SoilTransportModel.addSensor)."""
    #: Volumetric water content theta [m³/m³]
    WATER_CONTENT = 0
    #: Pressure head h [m]
    PRESSURE_HEAD = 1


class SoilRegion(IntEnum):
    """How a fractional sub-region is used in SoilTransportModel.addSoilVisualization."""
    #: Render the sub-box (the rest of the domain is hidden)
    KEEP = 0
    #: Render the domain with the (corner-anchored) sub-box cut out
    REMOVE = 1


# ----------------------------------------------------------------------------------------------
# Argument validation
# ----------------------------------------------------------------------------------------------

_UINT_MAX = 2 ** 32 - 1
_FLOAT32_MAX = 3.4028234663852886e38


def _validate_float(value, name: str, method_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise ValueError(f"{method_name}() {name} must be a number, got {type(value).__name__}")
    if not math.isfinite(value):
        raise ValueError(f"{method_name}() {name} must be finite, got {value}")
    if abs(value) > _FLOAT32_MAX:
        raise ValueError(f"{method_name}() {name} is outside the range of a 32-bit float, got {value}")
    return float(value)


def _validate_int(value, name: str, method_name: str, minimum: Optional[int] = None,
                  maximum: Optional[int] = None) -> int:
    if isinstance(value, bool) or not isinstance(value, numbers.Integral):
        raise ValueError(f"{method_name}() {name} must be an integer, got {type(value).__name__}")
    if minimum is not None and value < minimum:
        raise ValueError(f"{method_name}() {name} must be >= {minimum}, got {value}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{method_name}() {name} must be <= {maximum}, got {value}")
    return int(value)


def _validate_uint(value, name: str, method_name: str) -> int:
    return _validate_int(value, name, method_name, 0, _UINT_MAX)


def _validate_bool(value, name: str, method_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{method_name}() {name} must be a bool, got {type(value).__name__}")
    return value


def _validate_str(value, name: str, method_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{method_name}() {name} must be a string, got {type(value).__name__}")
    return value


def _validate_vec3(value, name: str, method_name: str) -> List[float]:
    if not isinstance(value, vec3):
        raise ValueError(f"{method_name}() {name} must be a vec3, got {type(value).__name__}")
    return [_validate_float(c, f"{name}.{axis}", method_name) for c, axis in zip((value.x, value.y, value.z), "xyz")]


def _validate_enum(value, enum_class, name: str, method_name: str) -> int:
    if not isinstance(value, enum_class):
        raise ValueError(f"{method_name}() {name} must be a {enum_class.__name__}, got {type(value).__name__}")
    return int(value)


# ----------------------------------------------------------------------------------------------
# Parameter structs (field names and defaults match the C++ structs)
# ----------------------------------------------------------------------------------------------

@dataclass
class SoilProperties:
    """
    Soil hydraulic properties (van Genuchten-Mualem, modified van Genuchten, Gardner or linear model).

    The defaults are sand-like van Genuchten properties, as in the C++ default constructor. Use
    getSoilPropertiesFromTexture() for the USDA texture library, or the named constructors
    vanGenuchten(), modifiedVanGenuchten(), gardner() and linear().

    Attributes:
        theta_r: Residual volumetric water content [m³/m³]
        theta_s: Saturated volumetric water content [m³/m³]
        alpha: Pore-size parameter [1/m] (van Genuchten alpha, or Gardner exponential rate)
        n: van Genuchten n parameter [-] (unused for the Gardner model)
        K_s: Saturated hydraulic conductivity [m/s]
        model: Constitutive model selector (SoilModel)
        h_e: Air-entry pressure head [m] (< 0) of SoilModel.MODIFIED_VAN_GENUCHTEN (unused by the other models)
        kr_spline_start: Effective saturation above which the van Genuchten relative conductivity is
            replaced by a cubic spline that rises to 1 at saturation with zero slope (1 = off). Keeps
            dK/dh finite at saturation when n < 2; e.g. 0.9999. SoilModel.VAN_GENUCHTEN only.

    The native plugin checks that the values are physical when they are used: it requires
    0 <= theta_r < theta_s <= 1, alpha > 0, K_s > 0 and 0 < kr_spline_start <= 1, plus n > 1 for the
    van Genuchten models and h_e < 0 for SoilModel.MODIFIED_VAN_GENUCHTEN.
    """
    theta_r: float = 0.045
    theta_s: float = 0.43
    alpha: float = 14.5
    n: float = 2.68
    K_s: float = 8.25e-5
    model: SoilModel = SoilModel.VAN_GENUCHTEN
    h_e: float = 0.0
    kr_spline_start: float = 1.0

    @classmethod
    def vanGenuchten(cls, theta_r: float, theta_s: float, alpha: float, n: float, K_s: float) -> 'SoilProperties':
        """Named constructor for a van Genuchten soil."""
        return cls(theta_r, theta_s, alpha, n, K_s)

    @classmethod
    def modifiedVanGenuchten(cls, theta_r: float, theta_s: float, alpha: float, n: float, K_s: float,
                             h_e: float) -> 'SoilProperties':
        """Named constructor for a modified (air-entry) van Genuchten soil; h_e [m] is the air-entry head (< 0)."""
        return cls(theta_r, theta_s, alpha, n, K_s, model=SoilModel.MODIFIED_VAN_GENUCHTEN, h_e=h_e)

    @classmethod
    def linear(cls, theta_r: float, theta_s: float, alpha: float, K_s: float) -> 'SoilProperties':
        """Named constructor for a linear soil: S_e = 1 + alpha h, K = K_s S_e (n is unused)."""
        return cls(theta_r, theta_s, alpha, 2.0, K_s, model=SoilModel.LINEAR)

    @classmethod
    def gardner(cls, theta_r: float, theta_s: float, alpha: float, K_s: float) -> 'SoilProperties':
        """Named constructor for a Gardner exponential soil (n is unused)."""
        return cls(theta_r, theta_s, alpha, 2.0, K_s, model=SoilModel.GARDNER)

    def m(self) -> float:
        """van Genuchten m parameter, 1 - 1/n."""
        return 1.0 - 1.0 / self.n

    def validate(self, method_name: str = "SoilProperties") -> None:
        """Check that every field has the right type and is finite."""
        for name in ("theta_r", "theta_s", "alpha", "n", "K_s", "h_e", "kr_spline_start"):
            _validate_float(getattr(self, name), f"SoilProperties.{name}", method_name)
        _validate_enum(self.model, SoilModel, "SoilProperties.model", method_name)

    def _to_c(self) -> soil_wrapper.CSoilProperties:
        return soil_wrapper.CSoilProperties(self.theta_r, self.theta_s, self.alpha, self.n, self.K_s,
                                            int(self.model), self.h_e, self.kr_spline_start)

    @classmethod
    def _from_c(cls, c: soil_wrapper.CSoilProperties) -> 'SoilProperties':
        return cls(c.theta_r, c.theta_s, c.alpha, c.n, c.K_s, SoilModel(c.model), c.h_e, c.kr_spline_start)


@dataclass
class SolverParameters:
    """
    Solver configuration parameters. Field names and defaults match the C++ SolverParameters struct
    (its deprecated fields, which the solver no longer uses, are omitted).

    Attributes:
        max_picard_iterations: Maximum nonlinear iterations per timestep
        enable_gravity: Include gravity in the flux (False for horizontal flow or capillarity-only
            problems). Column solvers only; the 3D solver requires gravity.
        substep_on_failure: When a step fails, sub-step it (down to 1/1000 of the step) before
            reporting the failure. Set False when the caller shortens failed steps itself, so a step
            that has no solution fails at once.
        picard_tolerance: Nonlinear convergence tolerance [m]
        dt_min: Minimum timestep [s]
        dt_max: Maximum timestep [s]
        horizontal_coupling_interval: Quasi-3D: couple laterally every N vertical steps (1 = every
            step, the most accurate). setSolverParameters() replaces an interval set by
            enableHorizontalCoupling().
        C_regularization: Regularization value for the specific moisture capacity at saturation
        K_min: Additive hydraulic-conductivity floor [m/s] for the 3D solver (0 = off); a small value
            (e.g. 1e-9) eases sharp wetting fronts into dry soil
        picard_omega: Under-relaxation factor for Picard iteration (0 < omega <= 1; 0.5-0.7 for sharp
            wetting fronts or dry soil)
        K_weighting: Interblock conductivity weighting (KWeighting); DEFAULT is arithmetic
        anderson_depth: Anderson-acceleration depth for the 3D solver's Modified-Picard iteration
            (0 = off; 2-3 is typical)
        nonlinear_method: Nonlinear strategy (NonlinearMethod). The 3D solver offers every method;
            the column solvers use Newton for NEWTON_ANALYTIC and Modified Picard for any other value.
        num_threads: CPU threads for the 3D solver (0 = OMP_NUM_THREADS if set, else one per
            physical core)
        bdf2: 3D solver: second-order BDF2 time integration instead of backward Euler. BDF2 does not
            conserve water when sources or boundary fluxes change; use it only with fixed steps and
            smooth forcing.
        adaptive_dt: Enable adaptive timestepping
        dt_target_rel_change: Target per-step relative change in water content,
            |dtheta|/(theta_s-theta_r), used to size the adaptive step
        dt_safety: Safety factor applied to the adaptive step estimate (0 < safety <= 1)
        dt_growth_max: Maximum factor by which the step may grow in a single step
        dt_reduction_min: Minimum factor for a single-step reduction
        dt_failure_factor: Factor by which the step is decreased after a failed (non-converged) step
    """
    max_picard_iterations: int = 20
    enable_gravity: bool = True
    substep_on_failure: bool = True
    picard_tolerance: float = 1e-5
    dt_min: float = 0.01
    dt_max: float = 3600.0
    horizontal_coupling_interval: int = 1
    C_regularization: float = 1e-10
    K_min: float = 0.0
    picard_omega: float = 1.0
    K_weighting: KWeighting = KWeighting.DEFAULT
    anderson_depth: int = 0
    nonlinear_method: NonlinearMethod = NonlinearMethod.NEWTON_ANALYTIC
    num_threads: int = 0
    bdf2: bool = False
    adaptive_dt: bool = False
    dt_target_rel_change: float = 0.03
    dt_safety: float = 0.9
    dt_growth_max: float = 2.0
    dt_reduction_min: float = 0.25
    dt_failure_factor: float = 0.5

    _BOOL_FIELDS = ("enable_gravity", "substep_on_failure", "bdf2", "adaptive_dt")
    _UINT_FIELDS = ("max_picard_iterations", "horizontal_coupling_interval")
    _INT_FIELDS = ("anderson_depth", "num_threads")
    _ENUM_FIELDS = {"K_weighting": KWeighting, "nonlinear_method": NonlinearMethod}

    def validate(self, method_name: str = "SolverParameters") -> None:
        """Check that every field has the right type (and is finite and in integer range)."""
        for f in fields(self):
            value = getattr(self, f.name)
            label = f"SolverParameters.{f.name}"
            if f.name in self._BOOL_FIELDS:
                _validate_bool(value, label, method_name)
            elif f.name in self._UINT_FIELDS:
                _validate_uint(value, label, method_name)
            elif f.name in self._INT_FIELDS:
                _validate_int(value, label, method_name, -2 ** 31, 2 ** 31 - 1)
            elif f.name in self._ENUM_FIELDS:
                _validate_enum(value, self._ENUM_FIELDS[f.name], label, method_name)
            else:
                _validate_float(value, label, method_name)

    def _to_c(self) -> soil_wrapper.CSolverParameters:
        c = soil_wrapper.CSolverParameters()
        for f in fields(self):
            setattr(c, f.name, int(getattr(self, f.name)) if f.name in self._BOOL_FIELDS or f.name in self._ENUM_FIELDS
                    else getattr(self, f.name))
        return c


@dataclass
class RootDistributionParams:
    """
    Statistical (Vrugt-type) root distribution parameters for a plant. Defaults match the C++ struct.

    Attributes:
        plant_x: Plant x position in world coordinates [m]
        plant_y: Plant y position in world coordinates [m]
        plant_z: Plant z position in world coordinates [m] (not used: root depth is measured from
            the soil surface)
        z_max: Maximum rooting depth [m]
        r_max: Maximum radial extent [m]
        z_star: Depth of maximum root density [m]
        r_star: Radial location of maximum density [m]
        pz: Depth shape parameter [-]
        pr: Radial shape parameter [-]
        total_root_length: Total root length [m] (informational; uptake uses normalized fractions)
    """
    plant_x: float = 0.0
    plant_y: float = 0.0
    plant_z: float = 0.0
    z_max: float = 1.5
    r_max: float = 1.0
    z_star: float = 0.3
    r_star: float = 0.0
    pz: float = 1.0
    pr: float = 1.0
    total_root_length: float = 1000.0

    def validate(self, method_name: str = "RootDistributionParams") -> None:
        """Check that every field is a finite number."""
        for f in fields(self):
            _validate_float(getattr(self, f.name), f"RootDistributionParams.{f.name}", method_name)

    def _to_c(self) -> soil_wrapper.CRootDistributionParams:
        return soil_wrapper.CRootDistributionParams(*(getattr(self, f.name) for f in fields(self)))


@dataclass
class WeibullRootParameters:
    """
    Weibull root length distribution parameters for a plant (1D depth, or 3D depth x radius).

    Root length density follows a Weibull profile with depth (and, when radial is True, radius from
    the plant base): RLD(x) is proportional to (k/lambda)(x/lambda)^(k-1) exp(-(x/lambda)^k). The shape
    k controls the profile: k < 1 concentrates roots near the origin (surface / trunk), k = 1 is
    exponential decay, k > 1 gives a peak away from the origin. The distribution is normalized to
    fractions internally. Defaults match the C++ struct.

    Attributes:
        plant_x: Plant base x position in world coordinates [m] (radial origin; used when radial=True)
        plant_y: Plant base y position in world coordinates [m] (radial origin; used when radial=True)
        z_max: Maximum rooting depth [m]
        shape_z: Depth Weibull shape k_z [-]
        scale_z: Depth Weibull scale lambda_z [m]
        radial: True = 3D (depth x radius), False = 1D (depth only, horizontally uniform)
        r_max: Maximum radial extent [m] (used when radial=True)
        shape_r: Radial Weibull shape k_r [-] (used when radial=True)
        scale_r: Radial Weibull scale lambda_r [m] (used when radial=True)
        total_root_length: Total root length [m] (informational; uptake uses normalized fractions)
    """
    plant_x: float = 0.0
    plant_y: float = 0.0
    z_max: float = 1.5
    shape_z: float = 1.5
    scale_z: float = 0.3
    radial: bool = False
    r_max: float = 1.0
    shape_r: float = 1.0
    scale_r: float = 0.5
    total_root_length: float = 1000.0

    def validate(self, method_name: str = "WeibullRootParameters") -> None:
        """Check that every field has the right type and is finite."""
        for f in fields(self):
            label = f"WeibullRootParameters.{f.name}"
            if f.name == "radial":
                _validate_bool(self.radial, label, method_name)
            else:
                _validate_float(getattr(self, f.name), label, method_name)

    def _to_c(self) -> soil_wrapper.CWeibullRootParameters:
        return soil_wrapper.CWeibullRootParameters(
            *(int(getattr(self, f.name)) if f.name == "radial" else getattr(self, f.name) for f in fields(self)))


def _validate_struct(value, struct_class, name: str, method_name: str):
    if not isinstance(value, struct_class):
        raise ValueError(f"{method_name}() {name} must be a {struct_class.__name__}, got {type(value).__name__}")
    value.validate(method_name)
    return value


# ----------------------------------------------------------------------------------------------
# Soil property library (free functions)
# ----------------------------------------------------------------------------------------------

#: Default air-entry head [m] of the texture library for SoilModel.MODIFIED_VAN_GENUCHTEN (-2 cm)
DEFAULT_AIR_ENTRY_HEAD = -0.02


def _validate_texture_model(model, method_name: str) -> int:
    value = _validate_enum(model, SoilModel, "model", method_name)
    if model not in (SoilModel.VAN_GENUCHTEN, SoilModel.MODIFIED_VAN_GENUCHTEN):
        constructor = "gardner" if model == SoilModel.GARDNER else "linear"
        raise ValueError(
            f"{method_name}() the texture library holds van Genuchten parameters only, so model must be "
            f"SoilModel.VAN_GENUCHTEN or SoilModel.MODIFIED_VAN_GENUCHTEN, got SoilModel.{model.name}. "
            f"Build a {model.name} soil with SoilProperties.{constructor}().")
    return value


def _library_call(function_name: str, fn, *args):
    try:
        return fn(*args)
    except NotImplementedError:
        raise
    except Exception as e:
        raise SoilTransportModelError(f"{function_name} failed: {e}") from e


def getSoilPropertiesFromTexture(texture: str, model: Optional[SoilModel] = None,
                                 match_standard_curves: bool = True) -> SoilProperties:
    """
    Get soil hydraulic properties for a USDA texture class.

    With model omitted (or SoilModel.VAN_GENUCHTEN) this returns the Carsel & Parrish (1988) class
    averages. SoilModel.MODIFIED_VAN_GENUCHTEN converts them with toModifiedVanGenuchten() at
    h_e = -2 cm: by default the Carsel & Parrish curves truncated at h_e (identical below it,
    saturated above it). There is no texture library for SoilModel.GARDNER or SoilModel.LINEAR.

    Args:
        texture: Soil texture name (e.g. "sand", "loam", "clay"); see getAvailableSoilTextures()
        model: SoilModel.VAN_GENUCHTEN or SoilModel.MODIFIED_VAN_GENUCHTEN, or None for the van
            Genuchten class averages
        match_standard_curves: For the modified model: see toModifiedVanGenuchten()

    Returns:
        SoilProperties for the given texture and model

    Raises:
        ValueError: For SoilModel.GARDNER or SoilModel.LINEAR, which have no texture library
        SoilTransportModelError: For a texture that is not in the library
    """
    _validate_str(texture, "texture", "getSoilPropertiesFromTexture")
    _validate_bool(match_standard_curves, "match_standard_curves", "getSoilPropertiesFromTexture")
    if model is None:
        c = _library_call("getSoilPropertiesFromTexture", soil_wrapper.getSoilPropertiesFromTexture, texture)
    else:
        model_value = _validate_texture_model(model, "getSoilPropertiesFromTexture")
        c = _library_call("getSoilPropertiesFromTexture", soil_wrapper.getSoilPropertiesFromTextureModel,
                          texture, model_value, match_standard_curves)
    return SoilProperties._from_c(c)


def toModifiedVanGenuchten(vg: SoilProperties, h_e: float = DEFAULT_AIR_ENTRY_HEAD,
                           match_standard_curves: bool = True) -> SoilProperties:
    """
    Convert standard van Genuchten-Mualem parameters to the air-entry (modified) model.

    theta_r, alpha and n are kept. With match_standard_curves (the default) the modified model is the
    standard one truncated at h_e: theta_s and K_s become the standard theta and K at h_e, so theta(h)
    and K(h) equal the standard curves exactly for every h < h_e, and only the band h_e <= h < 0
    becomes saturated. Without it theta_s and K_s are kept as the saturated values (HYDRUS's
    "air-entry value of -2 cm" convention), which raises the unsaturated K and theta slightly.

    Args:
        vg: Standard van Genuchten soil
        h_e: Air-entry head [m] (< 0); default -0.02
        match_standard_curves: Truncate the standard curves at h_e (True) or keep theta_s and K_s (False)

    Returns:
        SoilProperties with model SoilModel.MODIFIED_VAN_GENUCHTEN
    """
    _validate_struct(vg, SoilProperties, "vg", "toModifiedVanGenuchten")
    h_e = _validate_float(h_e, "h_e", "toModifiedVanGenuchten")
    _validate_bool(match_standard_curves, "match_standard_curves", "toModifiedVanGenuchten")
    c = _library_call("toModifiedVanGenuchten", soil_wrapper.toModifiedVanGenuchten, vg._to_c(), h_e,
                      match_standard_curves)
    return SoilProperties._from_c(c)


def getAvailableSoilTextures() -> List[str]:
    """Get the list of soil texture names in the library."""
    return _library_call("getAvailableSoilTextures", soil_wrapper.getAvailableSoilTextures)


def isSoilTextureAvailable(texture: str) -> bool:
    """Check if a soil texture is available in the library."""
    _validate_str(texture, "texture", "isSoilTextureAvailable")
    return _library_call("isSoilTextureAvailable", soil_wrapper.isSoilTextureAvailable, texture)


# ----------------------------------------------------------------------------------------------
# SoilTransportModel
# ----------------------------------------------------------------------------------------------

class SoilTransportModel:
    """
    Soil water transport model for variably saturated flow.

    Solves the Richards equation for variably saturated water flow in soil, with optional coupling
    to plant root systems, in one of three modes (see setSolverType()): independent 1D columns
    (the default), quasi-3D columns with operator-split horizontal coupling, or the full 3D Richards
    equation. Hydraulic behavior follows the van Genuchten-Mualem model by default (the default soil
    is loam). The full 3D solver runs on an NVIDIA GPU when the build has CUDA and a usable device
    is present, and on the CPU (OpenMP) otherwise.

    The model works on its own finite-volume grid and needs no primitive data from the Context. It
    only adds geometry to the Context when addSoilVisualization() is called.

    Coupling with PlantHydraulicsModel: getSoilWaterPotential() returns a pressure head in metres;
    multiply by 9.80665e-3 MPa/m before passing it to
    PlantHydraulicsModel.setSoilWaterPotentialOfPlant(). Transpiration demand is set with
    setTranspiration().

    The domain, grid resolution and solver type must be set before the domain is set up, which
    happens in initializeDomain() or in the first call that needs it (e.g. setInitialCondition());
    changing them afterwards raises an error.

    System requirements:
        - Cross-platform support (Windows, Linux, macOS)
        - GPU optional (NVIDIA CUDA accelerates the full 3D solver)
        - Soil transport plugin compiled into PyHelios

    Example:
        >>> from pyhelios import Context, SoilTransportModel
        >>> from pyhelios.types import vec3
        >>> with Context() as context:
        ...     with SoilTransportModel(context) as soil:
        ...         soil.defineSoilDomain(vec3(0, 0, 0), vec3(1, 1, 1))
        ...         soil.setColumnResolution(50)
        ...         soil.setInitialCondition(-1.0)
        ...         soil.setTopBoundaryFlux(2e-6)
        ...         soil.setBottomBoundaryFreeDrainage()
        ...         soil.run(3600.0)
        ...         theta = soil.getWaterContent(vec3(0.5, 0.5, -0.1))
    """

    def __init__(self, context: Context):
        """
        Initialize SoilTransportModel with graceful plugin handling.

        Args:
            context: Helios Context instance

        Raises:
            TypeError: If context is not a Context instance
            SoilTransportModelError: If the soil transport plugin is not available
        """
        # Validate context type - use duck typing to handle import state issues during testing
        if not (hasattr(context, '__class__') and
                (isinstance(context, Context) or
                 context.__class__.__name__ == 'Context')):
            raise TypeError(f"SoilTransportModel requires a Context instance, got {type(context).__name__}")

        self.context = context
        self.soil_model = None
        # Grid dimensions (nx, ny, nz), mirroring the native defaults, so that a grid whose cell count
        # overflows the native 32-bit index can be rejected before it corrupts memory.
        self._grid = (1, 1, 20)

        registry = get_plugin_registry()
        if not registry.is_plugin_available('soiltransport'):
            raise SoilTransportModelError(
                "SoilTransportModel requires the 'soiltransport' plugin which is not available.\n\n"
                "The soil transport plugin solves the Richards equation for variably saturated soil "
                "water flow, with root water uptake, drip emitters and surface evaporation.\n\n"
                "To enable soil transport modeling, build PyHelios with all plugins:\n"
                "   build_scripts/build_helios\n\n"
                "System requirements:\n"
                "  - Platforms: Windows, Linux, macOS\n"
                "  - GPU: optional (NVIDIA CUDA accelerates the full 3D solver)\n"
                "  - No special dependencies"
            )

        try:
            self.soil_model = soil_wrapper.createSoilTransportModel(context.getNativePtr())
            if self.soil_model is None:
                raise SoilTransportModelError(
                    "Failed to create SoilTransportModel instance. "
                    "This may indicate a problem with the native library."
                )
            logger.info("SoilTransportModel created successfully")
        except Exception as e:
            raise SoilTransportModelError(f"Failed to initialize SoilTransportModel: {e}")

    def _check_context_alive(self):
        """Raise if the owning Context has been destroyed (see Context.check_context_alive)."""
        check_context_alive(getattr(self, "context", None), "SoilTransportModel")

    def _check_cell_count(self, grid, method_name: str) -> None:
        nx, ny, nz = grid
        if nx * ny * nz > _UINT_MAX:
            raise ValueError(
                f"{method_name}() the grid would have {nx} x {ny} x {nz} = {nx * ny * nz} cells, more than "
                f"the native solver can index ({_UINT_MAX})")

    def _call(self, method_name: str, fn, *args):
        """Call a wrapper function on this model, translating native errors."""
        self._check_context_alive()
        try:
            return fn(self.soil_model, *args)
        except NotImplementedError:
            raise
        except Exception as e:
            raise SoilTransportModelError(f"{method_name} failed: {e}") from e

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit with proper cleanup."""
        if self.soil_model is not None:
            try:
                soil_wrapper.destroySoilTransportModel(self.soil_model)
                logger.debug("SoilTransportModel destroyed successfully")
            except Exception as e:
                logger.warning(f"Error destroying SoilTransportModel: {e}")
            finally:
                self.soil_model = None

    def __del__(self):
        """Destructor to ensure C++ resources freed even without 'with' statement."""
        if hasattr(self, 'soil_model') and self.soil_model is not None:
            try:
                soil_wrapper.destroySoilTransportModel(self.soil_model)
                self.soil_model = None
            except Exception as e:
                import warnings
                warnings.warn(f"Error in SoilTransportModel.__del__: {e}")

    def getNativePtr(self):
        """Get the native pointer for advanced operations."""
        return self.soil_model

    # ------------------------------------------------------------------------------ domain setup

    def defineSoilDomain(self, origin: vec3, extent: vec3) -> None:
        """
        Define the soil domain as a box with a uniform grid.

        The domain, grid resolution and solver type must be set before the domain is set up, which
        happens in initializeDomain() or in the first call that needs it (e.g.
        setInitialCondition()); changing them afterwards raises an error.

        Args:
            origin: Domain origin (x, y, z) [m], where z is the top surface; the domain extends
                downward from it
            extent: Domain extent (dx, dy, dz), total size [m]; every component must be positive
        """
        o = _validate_vec3(origin, "origin", "defineSoilDomain")
        e = _validate_vec3(extent, "extent", "defineSoilDomain")
        self._call("defineSoilDomain", soil_wrapper.defineSoilDomain, o, e)

    def setGridResolution(self, nx: int, ny: int, nz: int) -> None:
        """
        Set the grid resolution.

        Args:
            nx: Number of columns in x direction
            ny: Number of columns in y direction
            nz: Number of vertical layers
        """
        nx = _validate_uint(nx, "nx", "setGridResolution")
        ny = _validate_uint(ny, "ny", "setGridResolution")
        nz = _validate_uint(nz, "nz", "setGridResolution")
        self._check_cell_count((nx, ny, nz), "setGridResolution")
        self._call("setGridResolution", soil_wrapper.setGridResolution, nx, ny, nz)
        self._grid = (nx, ny, nz)

    def setColumnResolution(self, nz: int) -> None:
        """
        Set single-column resolution (for 1D simulations).

        Args:
            nz: Number of vertical layers (the column solvers need at least 2)
        """
        nz = _validate_uint(nz, "nz", "setColumnResolution")
        grid = (self._grid[0], self._grid[1], nz)
        self._check_cell_count(grid, "setColumnResolution")
        self._call("setColumnResolution", soil_wrapper.setColumnResolution, nz)
        self._grid = grid

    def setColumnGrid(self, nx: int, ny: int) -> None:
        """
        Set column grid dimensions (for quasi-3D).

        Args:
            nx: Number of columns in x
            ny: Number of columns in y
        """
        nx = _validate_uint(nx, "nx", "setColumnGrid")
        ny = _validate_uint(ny, "ny", "setColumnGrid")
        grid = (nx, ny, self._grid[2])
        self._check_cell_count(grid, "setColumnGrid")
        self._call("setColumnGrid", soil_wrapper.setColumnGrid, nx, ny)
        self._grid = grid

    def initializeDomain(self) -> None:
        """Initialize the domain (call after setting resolution and extent)."""
        self._call("initializeDomain", soil_wrapper.initializeDomain)

    # ------------------------------------------------------------------------------ soil properties

    def setSoilProperties(self, *args, **kwargs) -> None:
        """
        Set soil hydraulic properties, uniformly or for one column.

        Two call forms, matching the C++ overloads:

        - ``setSoilProperties(props)`` sets uniform properties for the entire domain.
        - ``setSoilProperties(i, j, props)`` sets the properties of column (i, j).

        Arguments may also be passed by keyword (``i=``, ``j=``, ``props=``). This sets up the
          domain if it has not been set up yet, and keeps the column's initial and boundary
          conditions.

        Args:
            args: ``props`` (a SoilProperties), or ``i, j, props`` where i and j are the column
                indices in x and y
            kwargs: The same arguments by keyword: ``props``, or ``i``, ``j`` and ``props``

        Raises:
            SoilTransportModelError: For non-physical properties, or a column outside the grid
        """
        unknown = set(kwargs) - {"i", "j", "props"}
        if unknown:
            raise TypeError(f"setSoilProperties() got unexpected keyword arguments: {sorted(unknown)}")
        column_form = len(args) >= 2 or "i" in kwargs or "j" in kwargs
        names = ("i", "j", "props") if column_form else ("props",)
        if len(args) > len(names):
            raise TypeError(f"setSoilProperties() takes (props) or (i, j, props), got {len(args)} positional arguments")
        bound = dict(zip(names, args))
        for name, value in kwargs.items():
            if name in bound:
                raise TypeError(f"setSoilProperties() got multiple values for argument '{name}'")
            bound[name] = value
        missing = [name for name in names if name not in bound]
        if missing:
            raise TypeError(f"setSoilProperties() takes (props) or (i, j, props); missing {missing}")

        props = _validate_struct(bound["props"], SoilProperties, "props", "setSoilProperties")
        if column_form:
            i = _validate_uint(bound["i"], "i", "setSoilProperties")
            j = _validate_uint(bound["j"], "j", "setSoilProperties")
            self._call("setSoilProperties", soil_wrapper.setSoilPropertiesColumn, i, j, props._to_c())
        else:
            self._call("setSoilProperties", soil_wrapper.setSoilProperties, props._to_c())

    def setSoilPropertiesFromTexture(self, texture: str, model: Optional[SoilModel] = None,
                                     match_standard_curves: bool = True) -> None:
        """
        Set uniform soil properties from a texture name.

        Keeps the current initial and boundary conditions.

        Args:
            texture: Soil texture name (e.g. "sand", "loam", "clay"); see getAvailableSoilTextures()
            model: SoilModel.VAN_GENUCHTEN or SoilModel.MODIFIED_VAN_GENUCHTEN (see
                getSoilPropertiesFromTexture()), or None for the van Genuchten class averages
            match_standard_curves: For the modified model: see toModifiedVanGenuchten()

        Raises:
            ValueError: For SoilModel.GARDNER or SoilModel.LINEAR, which have no texture library
            SoilTransportModelError: For a texture that is not in the library (see isSoilTextureAvailable())
        """
        _validate_str(texture, "texture", "setSoilPropertiesFromTexture")
        _validate_bool(match_standard_curves, "match_standard_curves", "setSoilPropertiesFromTexture")
        if model is None:
            self._call("setSoilPropertiesFromTexture", soil_wrapper.setSoilPropertiesFromTexture, texture)
        else:
            model_value = _validate_texture_model(model, "setSoilPropertiesFromTexture")
            self._call("setSoilPropertiesFromTexture", soil_wrapper.setSoilPropertiesFromTextureModel,
                       texture, model_value, match_standard_curves)

    # ------------------------------------------------------------------------------ initial and boundary conditions

    def setInitialCondition(self, h_init: float) -> None:
        """
        Set a uniform initial pressure head.

        Args:
            h_init: Initial pressure head [m]
        """
        h_init = _validate_float(h_init, "h_init", "setInitialCondition")
        self._call("setInitialCondition", soil_wrapper.setInitialCondition, h_init)

    def setInitialConditionHydrostatic(self, water_table_depth: float) -> None:
        """
        Set a hydrostatic initial condition.

        Args:
            water_table_depth: Depth to the water table from the surface [m]
        """
        water_table_depth = _validate_float(water_table_depth, "water_table_depth", "setInitialConditionHydrostatic")
        self._call("setInitialConditionHydrostatic", soil_wrapper.setInitialConditionHydrostatic, water_table_depth)

    def setTopBoundaryFlux(self, flux: float) -> None:
        """
        Set the top boundary flux (Neumann boundary condition).

        Args:
            flux: Surface flux [m/s] (positive = infiltration into the soil)
        """
        flux = _validate_float(flux, "flux", "setTopBoundaryFlux")
        self._call("setTopBoundaryFlux", soil_wrapper.setTopBoundaryFlux, flux)

    def setSurfaceEvaporation(self, potential_rate: float, aerodynamic_resistance: float = 50.0) -> float:
        """
        Apply supply-limited surface evaporation from a potential (atmospheric-demand) rate.

        For each surface cell the actual evaporation is E_act = beta(theta_surf) * E_pot, where beta
        is a dry-surface-layer reduction factor: a wet surface evaporates near the potential rate, a
        drying surface less, falling to about 0 as it approaches residual water content. The actual
        evaporation is applied as a per-cell sink at the surface (and is included in the mass
        balance). Call once per step with the current potential rate. Each surface cell uses its own
        soil properties. Requires the full 3D solver.

        Args:
            potential_rate: Potential evaporation flux [m/s] (atmospheric demand)
            aerodynamic_resistance: Aerodynamic resistance [s/m] (default 50; lower = stronger evaporation)

        Returns:
            Total actual evaporation volume rate over the surface [m³/s]

        Raises:
            SoilTransportModelError: If the solver type is not SolverType.SOLVER_3D. The domain is set
                up before this check, so call setSolverType() first: once a column solver's domain is
                set up, it can no longer be switched to SOLVER_3D.
        """
        potential_rate = _validate_float(potential_rate, "potential_rate", "setSurfaceEvaporation")
        aerodynamic_resistance = _validate_float(aerodynamic_resistance, "aerodynamic_resistance", "setSurfaceEvaporation")
        return self._call("setSurfaceEvaporation", soil_wrapper.setSurfaceEvaporation, potential_rate,
                          aerodynamic_resistance)

    def setTopBoundaryPressure(self, h: float) -> None:
        """
        Set the top boundary pressure head (Dirichlet boundary condition).

        Args:
            h: Pressure head at the surface [m]
        """
        h = _validate_float(h, "h", "setTopBoundaryPressure")
        self._call("setTopBoundaryPressure", soil_wrapper.setTopBoundaryPressure, h)

    def setBottomBoundaryFreeDrainage(self) -> None:
        """Set the bottom boundary to free drainage (unit gradient)."""
        self._call("setBottomBoundaryFreeDrainage", soil_wrapper.setBottomBoundaryFreeDrainage)

    def setBottomBoundaryPressure(self, h: float) -> None:
        """
        Set the bottom boundary pressure head (Dirichlet boundary condition).

        Args:
            h: Pressure head at the bottom [m]
        """
        h = _validate_float(h, "h", "setBottomBoundaryPressure")
        self._call("setBottomBoundaryPressure", soil_wrapper.setBottomBoundaryPressure, h)

    def setBottomBoundaryFlux(self, flux: float) -> None:
        """
        Set the bottom boundary flux (Neumann boundary condition).

        Args:
            flux: Bottom flux [m/s] (positive = out of the domain)
        """
        flux = _validate_float(flux, "flux", "setBottomBoundaryFlux")
        self._call("setBottomBoundaryFlux", soil_wrapper.setBottomBoundaryFlux, flux)

    def addSurfaceEmitter(self, x: float, y: float, flow_rate: float, radius: float = 0.1) -> None:
        """
        Add a point water input (e.g. a drip emitter) at the soil surface.

        Injects water at a fixed volumetric flow rate as a source term; emitters persist across run()
        calls until clearSurfaceEmitters() is called. With the full 3D solver the discharge is spread
        over the surface cells within a circular wetting footprint of the given radius, so the
        per-cell source rate does not depend on the grid resolution. With the column solvers
        (SOLVER_1D, SOLVER_QUASI_3D) the discharge enters the surface layer of the column containing
        (x, y), and the radius is not used.

        Args:
            x: World x location of the emitter [m]
            y: World y location of the emitter [m]
            flow_rate: Emitter discharge [m³/s] (positive = into the soil)
            radius: Radius of the wetting footprint [m] (full 3D solver only; default 0.1)

        Raises:
            SoilTransportModelError: For a point outside the domain
        """
        x = _validate_float(x, "x", "addSurfaceEmitter")
        y = _validate_float(y, "y", "addSurfaceEmitter")
        flow_rate = _validate_float(flow_rate, "flow_rate", "addSurfaceEmitter")
        radius = _validate_float(radius, "radius", "addSurfaceEmitter")
        self._call("addSurfaceEmitter", soil_wrapper.addSurfaceEmitter, x, y, flow_rate, radius)

    def clearSurfaceEmitters(self) -> None:
        """Remove all surface emitters."""
        self._call("clearSurfaceEmitters", soil_wrapper.clearSurfaceEmitters)

    # ------------------------------------------------------------------------------ root coupling

    def enableRootUptake(self) -> None:
        """
        Enable root water uptake.

        setRootDistribution() and setRootDistributionWeibull() enable root uptake themselves, so
        calling this is not required.
        """
        self._call("enableRootUptake", soil_wrapper.enableRootUptake)

    def setRootDistribution(self, plant_id: int, params: RootDistributionParams) -> None:
        """
        Set a statistical root distribution for a plant.

        Args:
            plant_id: Plant identifier
            params: Root distribution parameters (RootDistributionParams)
        """
        plant_id = _validate_uint(plant_id, "plant_id", "setRootDistribution")
        params = _validate_struct(params, RootDistributionParams, "params", "setRootDistribution")
        self._call("setRootDistribution", soil_wrapper.setRootDistribution, plant_id, params._to_c())

    def setRootDistributionWeibull(self, plant_id: int, params: WeibullRootParameters) -> None:
        """
        Set a Weibull root length distribution for a plant (1D depth, or 3D depth x radius).

        Defines the root length distribution used to partition transpiration demand into per-cell
        root water uptake. Use radial=False for a 1D depth profile (horizontally uniform) or
        radial=True for a 3D depth x radius profile about the plant base. Call setTranspiration()
        afterward to drive the uptake.

        Args:
            plant_id: Plant identifier
            params: Weibull distribution parameters (WeibullRootParameters)
        """
        plant_id = _validate_uint(plant_id, "plant_id", "setRootDistributionWeibull")
        params = _validate_struct(params, WeibullRootParameters, "params", "setRootDistributionWeibull")
        self._call("setRootDistributionWeibull", soil_wrapper.setRootDistributionWeibull, plant_id, params._to_c())

    def setRootRadialConductivity(self, L_r: float) -> None:
        """
        Set the root radial conductivity.

        The value is stored, but the current root uptake model, which distributes each plant's
        transpiration demand over its root zone weighted by water stress, does not use it.

        Args:
            L_r: Root radial conductivity [m/(s·MPa)]
        """
        L_r = _validate_float(L_r, "L_r", "setRootRadialConductivity")
        self._call("setRootRadialConductivity", soil_wrapper.setRootRadialConductivity, L_r)

    def setRootWaterStressParameters(self, h_onset: float, h_wilting: float, omega_c: float) -> None:
        """
        Set the root water-stress (Feddes) and uptake-compensation (Jarvis) parameters.

        Each root cell's uptake is scaled by alpha(h): 1 for h >= h_onset, falling linearly to 0 at
        h_wilting, so roots stop extracting from soil that is too dry. Uptake is redistributed toward
        unstressed roots, so the full transpiration demand is met while the root-weighted mean alpha
        is at least omega_c; below that, uptake is reduced in proportion (see getRootUptakeFlux()).
        The native defaults are h_onset = -4 m, h_wilting = -150 m (about -1.5 MPa) and omega_c = 0.5.

        Args:
            h_onset: Pressure head where water stress begins [m]
            h_wilting: Pressure head where uptake stops [m]
            omega_c: Critical root-zone stress index, 0-1 (1 disables compensation)

        Raises:
            SoilTransportModelError: Unless h_wilting < h_onset <= 0 and 0 < omega_c <= 1
        """
        h_onset = _validate_float(h_onset, "h_onset", "setRootWaterStressParameters")
        h_wilting = _validate_float(h_wilting, "h_wilting", "setRootWaterStressParameters")
        omega_c = _validate_float(omega_c, "omega_c", "setRootWaterStressParameters")
        self._call("setRootWaterStressParameters", soil_wrapper.setRootWaterStressParameters, h_onset, h_wilting, omega_c)

    def setTranspiration(self, plant_id: int, transpiration: float) -> None:
        """
        Set the transpiration demand for a plant.

        The plant needs a root distribution (setRootDistribution() or setRootDistributionWeibull())
        first; otherwise an error is raised.

        Args:
            plant_id: Plant identifier
            transpiration: Transpiration flux per unit ground area of the soil domain [m/s] (a
                plant's volumetric transpiration rate [m³/s] divided by the domain's footprint area)
        """
        plant_id = _validate_uint(plant_id, "plant_id", "setTranspiration")
        transpiration = _validate_float(transpiration, "transpiration", "setTranspiration")
        self._call("setTranspiration", soil_wrapper.setTranspiration, plant_id, transpiration)

    # ------------------------------------------------------------------------------ solver configuration

    def setSolverType(self, type: SolverType) -> None:
        """
        Set the solver type.

        Switching to or from SOLVER_3D raises an error once the domain has been set up, and switching
        to SOLVER_3D raises one if SolverParameters.enable_gravity is False (column solvers only).

        Args:
            type: Solver type (SolverType.SOLVER_1D, SOLVER_QUASI_3D or SOLVER_3D); the default is SOLVER_1D
        """
        value = _validate_enum(type, SolverType, "type", "setSolverType")
        self._call("setSolverType", soil_wrapper.setSolverType, value)

    def enableHorizontalCoupling(self, interval: int = 10) -> None:
        """
        Enable horizontal coupling for quasi-3D.

        Switches the solver type to SolverType.SOLVER_QUASI_3D; coming from SOLVER_3D, this raises
        once the domain has been set up. A later setSolverParameters() replaces the interval with its
        horizontal_coupling_interval.

        Args:
            interval: Couple every N vertical timesteps (default 10; at least 1)
        """
        interval = _validate_uint(interval, "interval", "enableHorizontalCoupling")
        self._call("enableHorizontalCoupling", soil_wrapper.enableHorizontalCoupling, interval)

    def setSolverParameters(self, params: SolverParameters) -> None:
        """
        Set solver parameters.

        Checks the whole parameter set before storing any of it, so a rejected set leaves the model
        unchanged. Raises an error for horizontal_coupling_interval < 1, dt_min <= 0 or
        dt_max < dt_min, enable_gravity = False with SOLVER_3D, and NonlinearMethod.M_SCHEME (CPU
        only) after enableGPU(). With the automatic GPU choice, M_SCHEME simply runs on the CPU.

        Args:
            params: Solver parameters (SolverParameters)
        """
        params = _validate_struct(params, SolverParameters, "params", "setSolverParameters")
        self._call("setSolverParameters", soil_wrapper.setSolverParameters, params._to_c())

    def enableGPU(self) -> None:
        """
        Run the full 3D solver on the GPU.

        By default the choice is automatic: the 3D solver uses the GPU when one is available (see
        isGPUAvailable()) and the nonlinear method runs on it (NonlinearMethod.M_SCHEME is CPU only).
        Calling this requires the GPU, overriding the automatic choice.

        Raises:
            SoilTransportModelError: If this build has no CUDA support, no usable CUDA device is
                found, or the nonlinear method is M_SCHEME
        """
        self._call("enableGPU", soil_wrapper.enableGPU)

    def disableGPU(self) -> None:
        """Run the full 3D solver on the CPU (OpenMP) even when a GPU is available."""
        self._call("disableGPU", soil_wrapper.disableGPU)

    def isGPUEnabled(self) -> bool:
        """
        Whether the full 3D solver runs on the GPU.

        With the automatic choice, whether a usable GPU is available and the nonlinear method runs on it.
        """
        return self._call("isGPUEnabled", soil_wrapper.isGPUEnabled)

    @staticmethod
    def isGPUAvailable() -> bool:
        """
        Whether a usable CUDA device is available to the soil solver.

        False in builds without CUDA, when no CUDA device that can run this build's kernels is found,
        or when the environment variable HELIOS_NO_GPU is set (to anything but "0").
        """
        return _library_call("isGPUAvailable", soil_wrapper.isGPUAvailable)

    # ------------------------------------------------------------------------------ run

    def run(self, dt: float) -> None:
        """
        Run the simulation for one timestep.

        Raises an error if the solver cannot complete the step, typically because a boundary or
        root-uptake flux exceeds what the soil can deliver or absorb. The simulation clock and the
        cumulative root uptake then count only the time that was advanced, and the state is at the
        end of that time: none with the 3D solver and fixed stepping (the state is left as it was);
        the part completed before the failure with adaptive stepping; and, with the column solvers
        and fixed stepping (which advance dt in sub-steps of at most SolverParameters.dt_max), the
        sub-steps completed before the one that failed. An error raised part-way through a step for
        another reason (e.g. a quasi-3D cell reaching saturation, or a GPU failure) leaves the state
        and the clock as they were before the call.

        Args:
            dt: Timestep [s]
        """
        dt = _validate_float(dt, "dt", "run")
        self._call("run", soil_wrapper.run, dt)

    # ------------------------------------------------------------------------------ output for coupling

    def getSoilWaterPotential(self, plant_id: int) -> float:
        """
        Get the uptake-weighted soil water potential for a plant.

        Intended for PlantHydraulicsModel coupling.

        Args:
            plant_id: Plant identifier

        Returns:
            Weighted soil water potential as a pressure head [m]. PlantHydraulicsModel works in MPa:
            multiply by 9.80665e-3 MPa/m before passing it to
            PlantHydraulicsModel.setSoilWaterPotentialOfPlant().

        Raises:
            SoilTransportModelError: For a plant without a root distribution
        """
        plant_id = _validate_uint(plant_id, "plant_id", "getSoilWaterPotential")
        return self._call("getSoilWaterPotential", soil_wrapper.getSoilWaterPotential, plant_id)

    def getWaterContent(self, position: vec3) -> float:
        """
        Get the water content at a world position.

        Points on the domain boundary (e.g. the soil surface) read the boundary cell.

        Args:
            position: World coordinates [m]

        Returns:
            Volumetric water content [m³/m³]

        Raises:
            SoilTransportModelError: For a point outside the domain
        """
        p = _validate_vec3(position, "position", "getWaterContent")
        return self._call("getWaterContent", soil_wrapper.getWaterContent, p)

    def getPressureHead(self, position: vec3) -> float:
        """
        Get the pressure head at a world position.

        Points on the domain boundary (e.g. the soil surface) read the boundary cell.

        Args:
            position: World coordinates [m]

        Returns:
            Pressure head [m]

        Raises:
            SoilTransportModelError: For a point outside the domain
        """
        p = _validate_vec3(position, "position", "getPressureHead")
        return self._call("getPressureHead", soil_wrapper.getPressureHead, p)

    # ------------------------------------------------------------------------------ point sensors

    def addSensor(self, position: vec3, quantity: SoilMeasurement) -> int:
        """
        Add a point sensor that records water content or pressure head over time.

        Each call to recordSensors() appends the current measured value and the simulation time to
        the sensor's time series. A position on the domain boundary (e.g. the soil surface) reads the
        boundary cell.

        Args:
            position: World coordinates of the sensor [m]
            quantity: Quantity to measure (SoilMeasurement.WATER_CONTENT or PRESSURE_HEAD)

        Returns:
            Sensor id (index) used to retrieve its data

        Raises:
            SoilTransportModelError: For a position outside the domain
        """
        p = _validate_vec3(position, "position", "addSensor")
        q = _validate_enum(quantity, SoilMeasurement, "quantity", "addSensor")
        return self._call("addSensor", soil_wrapper.addSensor, p, q)

    def recordSensors(self) -> None:
        """Sample every sensor at the current soil state and append to its time series (e.g. after each run())."""
        self._call("recordSensors", soil_wrapper.recordSensors)

    def getSensorCount(self) -> int:
        """Number of sensors that have been added."""
        return self._call("getSensorCount", soil_wrapper.getSensorCount)

    def getSensorData(self, sensor_id: int) -> List[float]:
        """
        Recorded measurement time series for a sensor.

        Args:
            sensor_id: Sensor id returned by addSensor()

        Returns:
            Water content [m³/m³] or pressure head [m], one value per recordSensors() call
        """
        sensor_id = _validate_uint(sensor_id, "sensor_id", "getSensorData")
        return self._call("getSensorData", soil_wrapper.getSensorData, sensor_id)

    def getSensorTimes(self, sensor_id: int) -> List[float]:
        """
        Simulation times [s] corresponding to each entry of getSensorData().

        Args:
            sensor_id: Sensor id returned by addSensor()
        """
        sensor_id = _validate_uint(sensor_id, "sensor_id", "getSensorTimes")
        return self._call("getSensorTimes", soil_wrapper.getSensorTimes, sensor_id)

    def getSensorPosition(self, sensor_id: int) -> vec3:
        """
        World position of a sensor [m].

        Args:
            sensor_id: Sensor id returned by addSensor()
        """
        sensor_id = _validate_uint(sensor_id, "sensor_id", "getSensorPosition")
        return vec3(*self._call("getSensorPosition", soil_wrapper.getSensorPosition, sensor_id))

    def getSensorQuantity(self, sensor_id: int) -> SoilMeasurement:
        """
        Quantity a sensor measures.

        Args:
            sensor_id: Sensor id returned by addSensor()
        """
        sensor_id = _validate_uint(sensor_id, "sensor_id", "getSensorQuantity")
        return SoilMeasurement(self._call("getSensorQuantity", soil_wrapper.getSensorQuantity, sensor_id))

    def clearSensorData(self) -> None:
        """Clear the recorded time series of all sensors (keeps the sensors themselves)."""
        self._call("clearSensorData", soil_wrapper.clearSensorData)

    def writeSensorData(self, filename: str) -> None:
        """
        Write all sensor time series to a CSV file.

        One row per recorded sample: a "time_s" column followed by one column per sensor (labeled
        with its quantity and position). Assumes all sensors were recorded together (same number of
        samples).

        Args:
            filename: Output file path
        """
        _validate_str(filename, "filename", "writeSensorData")
        self._call("writeSensorData", soil_wrapper.writeSensorData, filename)

    # ------------------------------------------------------------------------------ diagnostics

    def getLastSubstepCount(self) -> int:
        """
        Sub-steps taken in the last run() call.

        With adaptive stepping, the adaptive sub-steps; with the 3D solver and fixed stepping, 1; with
        the column solvers and fixed stepping, the number of sub-steps of at most
        SolverParameters.dt_max.

        A large value together with a tiny getTimestep() means the solver is stiff (e.g. a sharp
        wetting front into dry soil) and the run is grinding.
        """
        return self._call("getLastSubstepCount", soil_wrapper.getLastSubstepCount)

    def resetSolverStats(self) -> None:
        """Reset the GPU nonlinear-solver instrumentation counters (see solverPicardOuter())."""
        self._call("resetSolverStats", soil_wrapper.resetSolverStats)

    def solverPicardOuter(self) -> int:
        """GPU nonlinear-solver instrumentation: Picard outer iterations (0 on the CPU and in column modes)."""
        return self._call("solverPicardOuter", soil_wrapper.solverPicardOuter)

    def solverNewtonOuter(self) -> int:
        """GPU nonlinear-solver instrumentation: Newton outer iterations (0 on the CPU and in column modes)."""
        return self._call("solverNewtonOuter", soil_wrapper.solverNewtonOuter)

    def solverPicardGmres(self) -> int:
        """GPU nonlinear-solver instrumentation: GMRES iterations in Picard (0 on the CPU and in column modes)."""
        return self._call("solverPicardGmres", soil_wrapper.solverPicardGmres)

    def solverNewtonGmres(self) -> int:
        """GPU nonlinear-solver instrumentation: GMRES iterations in Newton (0 on the CPU and in column modes)."""
        return self._call("solverNewtonGmres", soil_wrapper.solverNewtonGmres)

    def getTimestep(self) -> float:
        """
        Current adaptive timestep [s] the controller has settled on.

        Collapsing toward dt_min signals a stiff front; recovering toward dt_max means the front has
        relaxed. Returns the 3D or column-grid step depending on mode, and 0 before the first
        adaptive run.
        """
        return self._call("getTimestep", soil_wrapper.getTimestep)

    def getSolverIterationCount(self) -> int:
        """
        Cumulative nonlinear iterations of the 3D solver since the last resetSolverIterationCount().

        Counted only by adaptive steps (SolverParameters.adaptive_dt) and by the rescue of a failed
        fixed step, as iterations of whichever nonlinear method ran; a fixed-step run that needs no
        rescue adds nothing. 0 in column modes.
        """
        return self._call("getSolverIterationCount", soil_wrapper.getSolverIterationCount)

    def resetSolverIterationCount(self) -> None:
        """Reset the cumulative Picard-iteration counter (3D solver only)."""
        self._call("resetSolverIterationCount", soil_wrapper.resetSolverIterationCount)

    # ------------------------------------------------------------------------------ mass balance

    def getTotalWaterStorage(self) -> float:
        """Total water storage in the domain [m³]."""
        return self._call("getTotalWaterStorage", soil_wrapper.getTotalWaterStorage)

    def getCumulativeBoundaryInflux(self) -> float:
        """
        Net water volume that has entered through emitters and boundaries since the start of the run [m³].

        3D solver only. With backward Euler (the default) it equals the change in storage to the
        solver tolerance. With BDF2 (SolverParameters.bdf2) it does not: BDF2 gains or loses water
        whenever the inflow changes. See resetMassBalance().

        Raises:
            SoilTransportModelError: For the column solvers, which do not track it
        """
        return self._call("getCumulativeBoundaryInflux", soil_wrapper.getCumulativeBoundaryInflux)

    def getMassBalanceResidual(self) -> float:
        """
        Mass-balance residual of the time integrator since the run start [m³].

        3D solver only: its storage term minus the inflow, about 0 to the solver tolerance. With
        backward Euler (the default) the storage term is the change in stored water; with BDF2 it is
        BDF2's weighted combination of three time levels, so a residual of about 0 does not mean that
        the stored water matches the inflow (compare getTotalWaterStorage() with
        getCumulativeBoundaryInflux()).

        Raises:
            SoilTransportModelError: For the column solvers, which do not track it
        """
        return self._call("getMassBalanceResidual", soil_wrapper.getMassBalanceResidual)

    def resetMassBalance(self) -> None:
        """Reset the mass-balance accumulators (influx and conservation residual)."""
        self._call("resetMassBalance", soil_wrapper.resetMassBalance)

    def getCumulativeRootUptake(self, plant_id: int) -> float:
        """
        Cumulative root water uptake for a plant [m].

        Args:
            plant_id: Plant identifier

        Raises:
            SoilTransportModelError: For a plant without a root distribution
        """
        plant_id = _validate_uint(plant_id, "plant_id", "getCumulativeRootUptake")
        return self._call("getCumulativeRootUptake", soil_wrapper.getCumulativeRootUptake, plant_id)

    def getRootUptakeFlux(self, plant_id: int) -> float:
        """
        Root water uptake flux currently applied for a plant [m/s per unit ground area].

        Equal to the transpiration demand set with setTranspiration() unless the root zone is too dry
        to supply it (see setRootWaterStressParameters()); 0 before a transpiration demand is set.

        Args:
            plant_id: Plant identifier

        Raises:
            SoilTransportModelError: For a plant without a root distribution
        """
        plant_id = _validate_uint(plant_id, "plant_id", "getRootUptakeFlux")
        return self._call("getRootUptakeFlux", soil_wrapper.getRootUptakeFlux, plant_id)

    # ------------------------------------------------------------------------------ visualization

    def addSoilVisualization(self, mode: SoilColorMode, *fractions: vec3, keep_fraction: Optional[vec3] = None,
                             fraction_min: Optional[vec3] = None, fraction_max: Optional[vec3] = None,
                             region: Optional[SoilRegion] = None) -> List[int]:
        """
        Build a visualization of the soil domain into the model's Context.

        Creates a 3D block spanning the soil domain whose outer faces are colored by the chosen field
        (volumetric water content or pressure head) sampled from the current soil state, or shown with
        a plain dirt texture. Display it with the Visualizer plugin. The returned UUIDs let you exclude
        the geometry from a physics pass (e.g. radiation) if needed.

        Three call forms, matching the C++ overloads:

        - ``addSoilVisualization(mode)``: the whole domain.
        - ``addSoilVisualization(mode, keep_fraction)``: the domain cut to a fraction of each axis,
          measured from the origin corner (for z, the origin is the surface). Each component is in
          (0, 1]; cutting an axis below 1 exposes the interior cross-section at that plane.
        - ``addSoilVisualization(mode, fraction_min, fraction_max, region=SoilRegion.KEEP)``: a
          fractional sub-box with per-axis lower and upper corner fractions in [0, 1]. With
          SoilRegion.KEEP the sub-box is rendered (a zero-thickness axis collapses it to a
          cross-section slice). With SoilRegion.REMOVE the sub-box is cut out of the full domain (a
          cutaway); anchor it at a domain corner for a clean notch.

        In the field modes each face is subdivided into patches; every patch is colored from the
        field on a single range shared by the whole visualization, and carries the sampled value as
        float primitive data ("water_content" or "pressure_head", whichever the mode shows) plus its
        sample point as vec3 primitive data "soil_sample_pos". In TEXTURE mode each face is one
        textured patch with no field data. Every primitive carries int primitive data
        "soil_cut_face": 1 for cross-section faces exposed by a cut (off the domain boundary), 0
        otherwise.

        The fractions may be passed positionally or by keyword (``keep_fraction=``, or
        ``fraction_min=`` and ``fraction_max=``), but not both ways at once.

        Args:
            mode: Coloring mode (SoilColorMode.WATER_CONTENT, PRESSURE_HEAD or TEXTURE)
            fractions: Nothing, keep_fraction, or fraction_min and fraction_max (vec3)
            keep_fraction: Fraction of each axis to keep, anchored at the origin corner (vec3)
            fraction_min: Lower-corner fractions of the sub-box (vec3)
            fraction_max: Upper-corner fractions of the sub-box (vec3)
            region: SoilRegion.KEEP (default) or REMOVE; only with fraction_min and fraction_max

        Returns:
            UUIDs of the created primitives
        """
        mode_value = _validate_enum(mode, SoilColorMode, "mode", "addSoilVisualization")
        keyword_given = [v is not None for v in (keep_fraction, fraction_min, fraction_max)]
        if any(keyword_given):
            if fractions:
                raise TypeError("addSoilVisualization() takes the fractions positionally or by keyword, not both")
            if keep_fraction is not None:
                if fraction_min is not None or fraction_max is not None:
                    raise TypeError("addSoilVisualization() takes keep_fraction, or fraction_min and fraction_max, not both")
                fractions = (keep_fraction,)
            elif fraction_min is None or fraction_max is None:
                raise TypeError("addSoilVisualization() needs both fraction_min and fraction_max")
            else:
                fractions = (fraction_min, fraction_max)
        if region is not None and len(fractions) != 2:
            raise ValueError("addSoilVisualization() region can only be given with fraction_min and fraction_max")
        if len(fractions) == 0:
            return self._call("addSoilVisualization", soil_wrapper.addSoilVisualization, mode_value)
        if len(fractions) == 1:
            keep = _validate_vec3(fractions[0], "keep_fraction", "addSoilVisualization")
            return self._call("addSoilVisualization", soil_wrapper.addSoilVisualizationKeepFraction, mode_value, keep)
        if len(fractions) == 2:
            fmin = _validate_vec3(fractions[0], "fraction_min", "addSoilVisualization")
            fmax = _validate_vec3(fractions[1], "fraction_max", "addSoilVisualization")
            region_value = _validate_enum(SoilRegion.KEEP if region is None else region, SoilRegion, "region",
                                          "addSoilVisualization")
            return self._call("addSoilVisualization", soil_wrapper.addSoilVisualizationRegion, mode_value, fmin,
                              fmax, region_value)
        raise TypeError(f"addSoilVisualization() takes at most 2 fraction vectors, got {len(fractions)}")

    def updateSoilVisualization(self, UUIDs: List[int], mode: SoilColorMode) -> None:
        """
        Refresh the field data on an existing soil visualization in place (no rebuild).

        Re-samples the current soil field at the "soil_sample_pos" of each face patch created by a
        prior addSoilVisualization() call and rewrites its "pressure_head" or "water_content"
        primitive data. The geometry, and the colors set by addSoilVisualization(), are left
        untouched, which avoids deleting and recreating primitives on every frame of an animation;
        to show the new values, color the primitives by that data in the Visualizer
        (Visualizer.colorContextPrimitivesByData()). Primitives without "soil_sample_pos" (e.g.
        TEXTURE-mode faces) are skipped.

        Args:
            UUIDs: The primitive UUIDs returned by addSoilVisualization()
            mode: Field to sample (SoilColorMode.WATER_CONTENT or PRESSURE_HEAD; TEXTURE does nothing)
        """
        if isinstance(UUIDs, (str, bytes)) or not hasattr(UUIDs, '__iter__'):
            raise ValueError(f"updateSoilVisualization() UUIDs must be a list of integers, got {type(UUIDs).__name__}")
        uuid_list = [_validate_uint(u, "UUID", "updateSoilVisualization") for u in UUIDs]
        mode_value = _validate_enum(mode, SoilColorMode, "mode", "updateSoilVisualization")
        self._call("updateSoilVisualization", soil_wrapper.updateSoilVisualization, uuid_list, mode_value)

    # ------------------------------------------------------------------------------ messages

    def enableMessages(self) -> None:
        """Enable standard output messages."""
        self._call("enableMessages", soil_wrapper.enableMessages)

    def disableMessages(self) -> None:
        """Disable standard output messages."""
        self._call("disableMessages", soil_wrapper.disableMessages)

    def is_available(self) -> bool:
        """Check if SoilTransportModel is available in the current build."""
        return get_plugin_registry().is_plugin_available('soiltransport')
