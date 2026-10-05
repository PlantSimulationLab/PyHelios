"""
High-level PlantHydraulics interface for PyHelios.

This module provides a user-friendly interface to the plant hydraulics modeling
capabilities with graceful plugin handling and informative error messages.
"""

import logging
import math
import numbers
from dataclasses import dataclass
from typing import List, Optional, Sequence, Union

from .plugins.registry import get_plugin_registry
from .wrappers import UPlantHydraulicsWrapper as hydraulics_wrapper
from .Context import Context, check_context_alive
from .exceptions import HeliosError

logger = logging.getLogger(__name__)


class PlantHydraulicsModelError(HeliosError):
    """Exception raised for PlantHydraulics-specific errors."""
    pass


# Species names accepted by the native leaf capacitance library. For any other name the native code
# only prints a warning and substitutes other values, so names are checked here.
AVAILABLE_SPECIES = (
    "Walnut", "walnut",
    "PistachioFemale", "pistachiofemale", "pistachio_female", "Pistachio_Female", "Pistachio_female",
    "pistachio", "Pistachio",
    "Elderberry", "elderberry", "blue_elderberry",
    "Western_Redbud", "western_redbud", "Redbud", "redbud",
)


def _validate_species(species, method_name: str) -> str:
    if not isinstance(species, str):
        raise ValueError(f"{method_name}() species must be a string, got {type(species).__name__}")
    if species not in AVAILABLE_SPECIES:
        raise ValueError(
            f"{method_name}() unknown species '{species}'. "
            f"Available species: {', '.join(AVAILABLE_SPECIES)}"
        )
    return species


def _validate_float(value, name: str, method_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise ValueError(f"{method_name}() {name} must be a number, got {type(value).__name__}")
    if not math.isfinite(value):
        raise ValueError(f"{method_name}() {name} must be finite, got {value}")
    return float(value)


def _validate_int(value, name: str, method_name: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, numbers.Integral):
        raise ValueError(f"{method_name}() {name} must be an integer, got {type(value).__name__}")
    if value < minimum:
        raise ValueError(f"{method_name}() {name} must be >= {minimum}, got {value}")
    return int(value)


def _validate_bool(value, name: str, method_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{method_name}() {name} must be a bool, got {type(value).__name__}")
    return value


def _validate_uuids(UUIDs, method_name: str) -> List[int]:
    if isinstance(UUIDs, (str, bytes)) or not hasattr(UUIDs, '__iter__'):
        raise ValueError(f"{method_name}() UUIDs must be a list of integers, got {type(UUIDs).__name__}")
    uuid_list = [_validate_int(uuid, 'UUID', method_name, 0) for uuid in UUIDs]
    if not uuid_list:
        raise ValueError(f"{method_name}() UUIDs cannot be empty")
    return uuid_list


@dataclass
class HydraulicConductance:
    """
    Hydraulic conductance of a leaf, stem or root as a function of water potential.

    Conductance follows K = saturated_conductance / (1 + |psi / potential_at_half_saturated|^sensitivity).
    It is constant at saturated_conductance when potential_at_half_saturated or sensitivity is zero.

    Attributes:
        saturated_conductance: Conductance at a water potential of zero (mol/m²/s/MPa). Must be > 0.
        potential_at_half_saturated: Water potential at which conductance is half its saturated value (MPa).
        sensitivity: Steepness of the decline in conductance around potential_at_half_saturated (unitless).
        temperature_dependence: If True, conductance is scaled by (T/298.15)^7.
    """
    saturated_conductance: float = 0.5
    potential_at_half_saturated: float = 0.0
    sensitivity: float = 0.0
    temperature_dependence: bool = False

    def validate(self, method_name: str = "HydraulicConductance") -> None:
        """Raise ValueError if any parameter is outside its valid range."""
        saturated = _validate_float(self.saturated_conductance, 'saturated_conductance', method_name)
        if saturated <= 0.0:
            raise ValueError(f"{method_name}() saturated_conductance must be > 0, got {saturated}")
        _validate_float(self.potential_at_half_saturated, 'potential_at_half_saturated', method_name)
        sensitivity = _validate_float(self.sensitivity, 'sensitivity', method_name)
        if sensitivity < 0.0:
            raise ValueError(f"{method_name}() sensitivity must be >= 0, got {sensitivity}")
        _validate_bool(self.temperature_dependence, 'temperature_dependence', method_name)

    def to_list(self) -> List[float]:
        """Flat layout expected by the native interface."""
        return [float(self.saturated_conductance), float(self.potential_at_half_saturated),
                float(self.sensitivity), 1.0 if self.temperature_dependence else 0.0]


@dataclass
class HydraulicCapacitance:
    """
    Hydraulic capacitance of a leaf, stem or root, from pressure-volume curve parameters.

    A fixed_constant_capacitance greater than zero gives a constant capacitance. Use
    HydraulicCapacitance.constant() to build one; its pressure-volume curve parameters are the defaults.

    For a leaf, the model always computes relative water content, turgor pressure and osmotic
    potential from the pressure-volume curve parameters, so a constant leaf capacitance means those
    outputs come from the default curve. For a stem or root, capacitance is used only by
    non-steady-state runs, which require a constant; their pressure-volume curve parameters are
    never used.

    Attributes:
        osmotic_potential_at_full_turgor: Osmotic potential at full turgor (MPa). Must be < 0.
        relative_water_content_at_turgor_loss: Relative water content at the turgor loss point (unitless), in (0, 1).
        cell_wall_elasticity_exponent: Exponent of the turgor pressure versus relative water content relationship (unitless).
        saturated_specific_water_content: Specific water content at a relative water content of 1 (mol/m²).
        fixed_constant_capacitance: Constant capacitance (mol/m²/MPa), or -1 to use the pressure-volume curve.
    """
    osmotic_potential_at_full_turgor: float = -2.0
    relative_water_content_at_turgor_loss: float = 0.8
    cell_wall_elasticity_exponent: float = 1.0
    saturated_specific_water_content: float = 1.0
    fixed_constant_capacitance: float = -1.0

    @classmethod
    def constant(cls, capacitance: float) -> 'HydraulicCapacitance':
        """
        Create a constant hydraulic capacitance.

        Args:
            capacitance: Constant capacitance (mol/m²/MPa). Must be > 0.
        """
        value = _validate_float(capacitance, 'capacitance', 'HydraulicCapacitance.constant')
        if value <= 0.0:
            raise ValueError(f"HydraulicCapacitance.constant() capacitance must be > 0, got {value}")
        return cls(fixed_constant_capacitance=value)

    def is_constant(self) -> bool:
        """True if this is a constant capacitance rather than a pressure-volume curve."""
        return self.fixed_constant_capacitance > 0.0

    def validate(self, method_name: str = "HydraulicCapacitance") -> None:
        """Raise ValueError if any parameter is outside its valid range."""
        fixed = _validate_float(self.fixed_constant_capacitance, 'fixed_constant_capacitance', method_name)
        if fixed <= 0.0 and fixed != -1.0:
            raise ValueError(
                f"{method_name}() fixed_constant_capacitance must be > 0, or -1 to use the "
                f"pressure-volume curve parameters, got {fixed}"
            )
        osmotic = _validate_float(self.osmotic_potential_at_full_turgor, 'osmotic_potential_at_full_turgor', method_name)
        if osmotic >= 0.0:
            raise ValueError(f"{method_name}() osmotic_potential_at_full_turgor must be < 0, got {osmotic}")
        turgor_loss = _validate_float(self.relative_water_content_at_turgor_loss,
                                      'relative_water_content_at_turgor_loss', method_name)
        if not 0.0 < turgor_loss < 1.0:
            raise ValueError(
                f"{method_name}() relative_water_content_at_turgor_loss must be between 0 and 1 (exclusive), "
                f"got {turgor_loss}"
            )
        elasticity = _validate_float(self.cell_wall_elasticity_exponent, 'cell_wall_elasticity_exponent', method_name)
        if elasticity <= 0.0:
            raise ValueError(f"{method_name}() cell_wall_elasticity_exponent must be > 0, got {elasticity}")
        saturated = _validate_float(self.saturated_specific_water_content, 'saturated_specific_water_content', method_name)
        if saturated <= 0.0:
            raise ValueError(f"{method_name}() saturated_specific_water_content must be > 0, got {saturated}")

    def to_list(self) -> List[float]:
        """Flat layout expected by the native interface."""
        return [float(self.osmotic_potential_at_full_turgor), float(self.relative_water_content_at_turgor_loss),
                float(self.cell_wall_elasticity_exponent), float(self.saturated_specific_water_content),
                float(self.fixed_constant_capacitance)]


def _make_conductance(method_name, saturated_conductance, potential_at_half_saturated, sensitivity,
                      temperature_dependence) -> HydraulicConductance:
    if potential_at_half_saturated is None:
        if sensitivity is not None:
            raise ValueError(f"{method_name}() sensitivity requires potential_at_half_saturated")
        conductance = HydraulicConductance(saturated_conductance, 0.0, 0.0, temperature_dependence)
    else:
        conductance = HydraulicConductance(saturated_conductance, potential_at_half_saturated,
                                           5.0 if sensitivity is None else sensitivity, temperature_dependence)
    conductance.validate(method_name)
    return conductance


def _make_capacitance(method_name, first, relative_water_content_at_turgor_loss, cell_wall_elasticity_exponent,
                      saturated_specific_water_content=None) -> HydraulicCapacitance:
    if relative_water_content_at_turgor_loss is None:
        if cell_wall_elasticity_exponent is not None or saturated_specific_water_content is not None:
            raise ValueError(
                f"{method_name}() a constant capacitance takes a single value; give "
                f"relative_water_content_at_turgor_loss to use pressure-volume curve parameters"
            )
        value = _validate_float(first, 'capacitance', method_name)
        if value <= 0.0:
            raise ValueError(f"{method_name}() capacitance must be > 0, got {value}")
        return HydraulicCapacitance(fixed_constant_capacitance=value)

    capacitance = HydraulicCapacitance(
        osmotic_potential_at_full_turgor=first,
        relative_water_content_at_turgor_loss=relative_water_content_at_turgor_loss,
        cell_wall_elasticity_exponent=1.0 if cell_wall_elasticity_exponent is None else cell_wall_elasticity_exponent,
        saturated_specific_water_content=1.0 if saturated_specific_water_content is None else saturated_specific_water_content,
    )
    capacitance.validate(method_name)
    return capacitance


class PlantHydraulicsModelCoefficients:
    """
    Hydraulic conductance and capacitance parameters of the leaf, stem and root compartments.

    A new instance holds the model defaults: a constant conductance of 0.5 mol/m²/s/MPa for each
    compartment, and pressure-volume curve parameters of -2 MPa osmotic potential at full turgor,
    0.8 relative water content at turgor loss and an elasticity exponent of 1.

    Attributes:
        LeafHydraulicConductance, StemHydraulicConductance, RootHydraulicConductance: HydraulicConductance
        LeafHydraulicCapacitance: HydraulicCapacitance, or None when the leaf capacitance comes from the
            species library (see leaf_capacitance_species)
        StemHydraulicCapacitance, RootHydraulicCapacitance: HydraulicCapacitance
        leaf_capacitance_species: Species name whose library leaf capacitance is used, or None

    Example:
        >>> coeffs = PlantHydraulicsModelCoefficients()
        >>> coeffs.setLeafHydraulicConductance(0.05, -1.5, 2.0)
        >>> coeffs.setStemHydraulicConductance(0.5)
        >>> coeffs.setLeafHydraulicCapacitanceFromLibrary("pistachio")
    """

    def __init__(self):
        self.LeafHydraulicConductance = HydraulicConductance()
        self.StemHydraulicConductance = HydraulicConductance()
        self.RootHydraulicConductance = HydraulicConductance()
        self.LeafHydraulicCapacitance: Optional[HydraulicCapacitance] = HydraulicCapacitance()
        self.StemHydraulicCapacitance = HydraulicCapacitance()
        self.RootHydraulicCapacitance = HydraulicCapacitance()
        self.leaf_capacitance_species: Optional[str] = None

    def __repr__(self):
        leaf_capacitance = (f"library '{self.leaf_capacitance_species}'" if self.leaf_capacitance_species
                            else repr(self.LeafHydraulicCapacitance))
        return (f"PlantHydraulicsModelCoefficients(LeafHydraulicConductance={self.LeafHydraulicConductance!r}, "
                f"StemHydraulicConductance={self.StemHydraulicConductance!r}, "
                f"RootHydraulicConductance={self.RootHydraulicConductance!r}, "
                f"LeafHydraulicCapacitance={leaf_capacitance}, "
                f"StemHydraulicCapacitance={self.StemHydraulicCapacitance!r}, "
                f"RootHydraulicCapacitance={self.RootHydraulicCapacitance!r})")

    # Hydraulic conductance

    def setLeafHydraulicConductance(self, saturated_conductance: float,
                                    potential_at_half_saturated: Optional[float] = None,
                                    sensitivity: Optional[float] = None,
                                    temperature_dependence: bool = False) -> None:
        """
        Set leaf hydraulic conductance, constant or as a function of leaf water potential.

        Args:
            saturated_conductance: Conductance at a water potential of zero (mol/m²/s/MPa). Typical range 0.001 to 1.
                With no other arguments this is a constant conductance.
            potential_at_half_saturated: Water potential at which conductance is half its saturated value (MPa).
            sensitivity: Steepness of the decline in conductance with water potential (unitless).
                Defaults to 5 when potential_at_half_saturated is given.
            temperature_dependence: If True, conductance is scaled by (T/298.15)^7.
        """
        self.LeafHydraulicConductance = _make_conductance(
            'setLeafHydraulicConductance', saturated_conductance, potential_at_half_saturated, sensitivity,
            temperature_dependence)

    def setLeafHydraulicConductanceTemperatureDependence(self, temperature_dependence: bool) -> None:
        """Toggle the temperature dependence of leaf hydraulic conductance, K(T) = K*(T/298.15)^7."""
        self.LeafHydraulicConductance.temperature_dependence = _validate_bool(
            temperature_dependence, 'temperature_dependence', 'setLeafHydraulicConductanceTemperatureDependence')

    def setStemHydraulicConductance(self, saturated_conductance: float,
                                    potential_at_half_saturated: Optional[float] = None,
                                    sensitivity: Optional[float] = None,
                                    temperature_dependence: bool = False) -> None:
        """
        Set stem hydraulic conductance, constant or as a function of stem water potential.

        Args:
            saturated_conductance: Conductance at a water potential of zero (mol/m²/s/MPa). Typical range 0.001 to 1.
                With no other arguments this is a constant conductance.
            potential_at_half_saturated: Water potential at which conductance is half its saturated value (MPa).
            sensitivity: Steepness of the decline in conductance with water potential (unitless).
                Defaults to 5 when potential_at_half_saturated is given.
            temperature_dependence: If True, conductance is scaled by (T/298.15)^7.
        """
        self.StemHydraulicConductance = _make_conductance(
            'setStemHydraulicConductance', saturated_conductance, potential_at_half_saturated, sensitivity,
            temperature_dependence)

    def setStemHydraulicConductanceTemperatureDependence(self, temperature_dependence: bool) -> None:
        """Toggle the temperature dependence of stem hydraulic conductance, K(T) = K*(T/298.15)^7."""
        self.StemHydraulicConductance.temperature_dependence = _validate_bool(
            temperature_dependence, 'temperature_dependence', 'setStemHydraulicConductanceTemperatureDependence')

    def setRootHydraulicConductance(self, saturated_conductance: float,
                                    potential_at_half_saturated: Optional[float] = None,
                                    sensitivity: Optional[float] = None,
                                    temperature_dependence: bool = False) -> None:
        """
        Set root hydraulic conductance, constant or as a function of root water potential.

        Args:
            saturated_conductance: Conductance at a water potential of zero (mol/m²/s/MPa). Typical range 0.001 to 1.
                With no other arguments this is a constant conductance.
            potential_at_half_saturated: Water potential at which conductance is half its saturated value (MPa).
            sensitivity: Steepness of the decline in conductance with water potential (unitless).
                Defaults to 5 when potential_at_half_saturated is given.
            temperature_dependence: If True, conductance is scaled by (T/298.15)^7.
        """
        self.RootHydraulicConductance = _make_conductance(
            'setRootHydraulicConductance', saturated_conductance, potential_at_half_saturated, sensitivity,
            temperature_dependence)

    def setRootHydraulicConductanceTemperatureDependence(self, temperature_dependence: bool) -> None:
        """Toggle the temperature dependence of root hydraulic conductance, K(T) = K*(T/298.15)^7."""
        self.RootHydraulicConductance.temperature_dependence = _validate_bool(
            temperature_dependence, 'temperature_dependence', 'setRootHydraulicConductanceTemperatureDependence')

    # Hydraulic capacitance

    def setLeafHydraulicCapacitance(self, osmotic_potential_at_full_turgor: float,
                                    relative_water_content_at_turgor_loss: Optional[float] = None,
                                    cell_wall_elasticity_exponent: Optional[float] = None,
                                    saturated_specific_water_content: Optional[float] = None) -> None:
        """
        Set leaf hydraulic capacitance, constant or from pressure-volume curve parameters.

        Called with a single argument, that value is a constant capacitance (mol/m²/MPa, typical range
        0.005 to 0.5). Otherwise the arguments are pressure-volume curve parameters.

        The model computes leaf relative water content, turgor pressure and osmotic potential from
        the pressure-volume curve parameters. A constant capacitance resets those parameters to
        their defaults (-2 MPa, 0.8, 1) and otherwise only changes the optional
        "hydraulic_capacitance" output.

        Args:
            osmotic_potential_at_full_turgor: Osmotic potential at full turgor (MPa), or the constant
                capacitance (mol/m²/MPa) when it is the only argument.
            relative_water_content_at_turgor_loss: Relative water content at the turgor loss point (unitless).
                Typical range 0.7 to 0.95.
            cell_wall_elasticity_exponent: Exponent of the turgor pressure versus relative water content
                relationship (unitless). Typical range 1 to 2. Defaults to 1.
            saturated_specific_water_content: Saturated specific water content (mol/m²). Defaults to 1.
        """
        self.LeafHydraulicCapacitance = _make_capacitance(
            'setLeafHydraulicCapacitance', osmotic_potential_at_full_turgor, relative_water_content_at_turgor_loss,
            cell_wall_elasticity_exponent, saturated_specific_water_content)
        self.leaf_capacitance_species = None

    def setLeafHydraulicCapacitanceFromLibrary(self, species: str) -> None:
        """
        Set leaf hydraulic capacitance from the species library of pressure-volume curve parameters.

        The library values are held by the native plugin and applied when the coefficients are passed
        to PlantHydraulicsModel.setModelCoefficients(). LeafHydraulicCapacitance stays None unless it
        is later replaced by setLeafHydraulicCapacitance().

        Args:
            species: Species name. See pyhelios.PlantHydraulics.AVAILABLE_SPECIES.

        Raises:
            ValueError: If the species is not in the library
        """
        self.leaf_capacitance_species = _validate_species(species, 'setLeafHydraulicCapacitanceFromLibrary')
        self.LeafHydraulicCapacitance = None

    def setStemHydraulicCapacitance(self, osmotic_potential_at_full_turgor: float,
                                    relative_water_content_at_turgor_loss: Optional[float] = None,
                                    cell_wall_elasticity_exponent: Optional[float] = None) -> None:
        """
        Set stem hydraulic capacitance, constant or from pressure-volume curve parameters.

        Called with a single argument, that value is a constant capacitance (typical range 0.005 to 2).
        Stem capacitance is used only by non-steady-state runs, which require it to be constant;
        pressure-volume curve parameters are accepted but never used by the model.

        Args:
            osmotic_potential_at_full_turgor: Osmotic potential at full turgor (MPa), or the constant
                capacitance when it is the only argument.
            relative_water_content_at_turgor_loss: Relative water content at the turgor loss point (unitless).
            cell_wall_elasticity_exponent: Exponent of the turgor pressure versus relative water content
                relationship (unitless). Defaults to 1.
        """
        self.StemHydraulicCapacitance = _make_capacitance(
            'setStemHydraulicCapacitance', osmotic_potential_at_full_turgor, relative_water_content_at_turgor_loss,
            cell_wall_elasticity_exponent)

    def setRootHydraulicCapacitance(self, osmotic_potential_at_full_turgor: float,
                                    relative_water_content_at_turgor_loss: Optional[float] = None,
                                    cell_wall_elasticity_exponent: Optional[float] = None) -> None:
        """
        Set root hydraulic capacitance, constant or from pressure-volume curve parameters.

        Called with a single argument, that value is a constant capacitance (typical range 0.005 to 2).
        Root capacitance is used only by non-steady-state runs, which require it to be constant;
        pressure-volume curve parameters are accepted but never used by the model.

        Args:
            osmotic_potential_at_full_turgor: Osmotic potential at full turgor (MPa), or the constant
                capacitance when it is the only argument.
            relative_water_content_at_turgor_loss: Relative water content at the turgor loss point (unitless).
            cell_wall_elasticity_exponent: Exponent of the turgor pressure versus relative water content
                relationship (unitless). Defaults to 1.
        """
        self.RootHydraulicCapacitance = _make_capacitance(
            'setRootHydraulicCapacitance', osmotic_potential_at_full_turgor, relative_water_content_at_turgor_loss,
            cell_wall_elasticity_exponent)

    def validate(self, method_name: str = "PlantHydraulicsModelCoefficients") -> None:
        """Raise ValueError if any compartment's parameters are missing, mistyped or out of range."""
        for label in ('Leaf', 'Stem', 'Root'):
            conductance = getattr(self, f'{label}HydraulicConductance')
            if not isinstance(conductance, HydraulicConductance):
                raise ValueError(
                    f"{method_name}() {label}HydraulicConductance must be a HydraulicConductance, "
                    f"got {type(conductance).__name__}"
                )
            conductance.validate(method_name)

        if self.leaf_capacitance_species is not None:
            _validate_species(self.leaf_capacitance_species, method_name)
        for label in ('Leaf', 'Stem', 'Root'):
            capacitance = getattr(self, f'{label}HydraulicCapacitance')
            if label == 'Leaf' and self.leaf_capacitance_species is not None and capacitance is None:
                continue
            if not isinstance(capacitance, HydraulicCapacitance):
                raise ValueError(
                    f"{method_name}() {label}HydraulicCapacitance must be a HydraulicCapacitance, "
                    f"got {type(capacitance).__name__}"
                )
            capacitance.validate(method_name)
            if label != 'Leaf' and capacitance.saturated_specific_water_content != 1.0:
                raise ValueError(
                    f"{method_name}() {label}HydraulicCapacitance.saturated_specific_water_content cannot be set; "
                    f"the model uses it only for leaves"
                )

    def to_list(self) -> List[float]:
        """Flat layout expected by the native interface (see pyhelios_wrapper_planthydraulics.h)."""
        leaf_capacitance = self.LeafHydraulicCapacitance or HydraulicCapacitance()
        values = (self.LeafHydraulicConductance.to_list() + self.StemHydraulicConductance.to_list()
                  + self.RootHydraulicConductance.to_list() + leaf_capacitance.to_list())
        for capacitance in (self.StemHydraulicCapacitance, self.RootHydraulicCapacitance):
            values += [float(capacitance.osmotic_potential_at_full_turgor),
                       float(capacitance.relative_water_content_at_turgor_loss),
                       float(capacitance.cell_wall_elasticity_exponent),
                       float(capacitance.fixed_constant_capacitance)]
        return values

    @classmethod
    def from_list(cls, values: Sequence[float]) -> 'PlantHydraulicsModelCoefficients':
        """Build coefficients from the flat layout written by to_list()."""
        if len(values) != hydraulics_wrapper.COEFFICIENT_SIZE:
            raise ValueError(
                f"PlantHydraulicsModelCoefficients.from_list() expects {hydraulics_wrapper.COEFFICIENT_SIZE} "
                f"values, got {len(values)}"
            )
        v = [float(value) for value in values]
        coeffs = cls()
        for index, label in enumerate(('Leaf', 'Stem', 'Root')):
            block = v[4 * index:4 * index + 4]
            setattr(coeffs, f'{label}HydraulicConductance',
                    HydraulicConductance(block[0], block[1], block[2], block[3] != 0.0))
        coeffs.LeafHydraulicCapacitance = HydraulicCapacitance(v[12], v[13], v[14], v[15], v[16])
        coeffs.StemHydraulicCapacitance = HydraulicCapacitance(v[17], v[18], v[19], 1.0, v[20])
        coeffs.RootHydraulicCapacitance = HydraulicCapacitance(v[21], v[22], v[23], 1.0, v[24])
        return coeffs


class PlantHydraulicsModel:
    """
    High-level interface for plant hydraulics modeling.

    The model computes the water potential of the root, stem and leaf compartments of a plant from
    the transpiration of its leaves and a soil water potential set by the user. Stems and roots are
    each one compartment per plant; leaf water potential, turgor pressure, osmotic potential and
    relative water content are computed for each leaf primitive.

    Leaves are grouped into plants by a "plantID", read from the object data of a primitive's parent
    object or from the primitive's own data. run() groups the primitives it is given that have no
    plantID into a new plant (see run()).

    Input primitive data (float):
        - "latent_flux" (W/m²): transpiration, e.g. from EnergyBalanceModel. A leaf without it
          transpires nothing, and the plant's transpiration is the area-weighted mean over the
          primitives that do have it (zero if none do).
        - "temperature" (K, default 300): surface temperature, used for a temperature-dependent
          leaf conductance
        - "air_temperature" (K, default 298.15): stem temperature; the root is taken to be 5 K
          cooler. Used for a temperature-dependent stem or root conductance, and read from one
          primitive only, the one with the lowest UUID in the plant.
        - "water_potential" (MPa, default -0.001): leaf water potential at which a water-potential
          dependent leaf conductance is evaluated. It is also an output, so repeated runs start
          from the previous result.
        - "relative_water_content" (default 1.0): initial leaf relative water content, read by
          non-steady-state runs only

    Water-potential dependent conductances are evaluated once per run at the water potentials from
    before the run (for the stem and root, those stored from the model's previous run of the plant,
    or -0.001 MPa), so a steady-state run is not iterated to a self-consistent solution.

    Output primitive data:
        - "water_potential" (MPa), "turgor_pressure" (MPa), "osmotic_potential" (MPa),
          "relative_water_content" (unitless)

    Steady-state runs (timespan=0) are the supported mode; non-steady-state runs are under
    construction in the native plugin.

    System requirements:
        - Cross-platform support (Windows, Linux, macOS)
        - No GPU required
        - No special dependencies
        - Plant hydraulics plugin compiled into PyHelios

    Example:
        >>> with Context() as context:
        ...     # with: from pyhelios import Context; from pyhelios.types import vec2, vec3
        ...     leaf = context.addPatch(center=vec3(0, 0, 1), size=vec2(0.1, 0.1))
        ...     context.setPrimitiveDataFloat(leaf, "latent_flux", 100.0)
        ...
        ...     with PlantHydraulicsModel(context) as hydraulics:
        ...         coeffs = PlantHydraulicsModelCoefficients()
        ...         coeffs.setLeafHydraulicCapacitanceFromLibrary("pistachio")
        ...         hydraulics.setModelCoefficients(coeffs)
        ...
        ...         hydraulics.run([leaf])
        ...         psi_stem = hydraulics.getStemWaterPotential(leaf)
    """

    def __init__(self, context: Context):
        """
        Initialize PlantHydraulicsModel with graceful plugin handling.

        Args:
            context: Helios Context instance

        Raises:
            TypeError: If context is not a Context instance
            PlantHydraulicsModelError: If the plant hydraulics plugin is not available
        """
        # Validate context type - use duck typing to handle import state issues during testing
        if not (hasattr(context, '__class__') and
                (isinstance(context, Context) or
                 context.__class__.__name__ == 'Context')):
            raise TypeError(f"PlantHydraulicsModel requires a Context instance, got {type(context).__name__}")

        self.context = context
        self.hydraulics_model = None
        # UUIDs holding their own coefficients, which getModelCoefficients() can read back
        self._per_primitive_uuids = set()

        # Check plugin availability using registry
        registry = get_plugin_registry()

        if not registry.is_plugin_available('planthydraulics'):
            raise PlantHydraulicsModelError(
                "PlantHydraulicsModel requires the 'planthydraulics' plugin which is not available.\n\n"
                "The plant hydraulics plugin computes root, stem and leaf water potentials, turgor "
                "pressure, osmotic potential and relative water content from leaf transpiration.\n\n"
                "To enable plant hydraulics modeling, build PyHelios with all plugins:\n"
                "   build_scripts/build_helios\n\n"
                "System requirements:\n"
                "  - Platforms: Windows, Linux, macOS\n"
                "  - No GPU required\n"
                "  - No special dependencies"
            )

        # Plugin is available - create plant hydraulics model
        try:
            self.hydraulics_model = hydraulics_wrapper.createPlantHydraulicsModel(context.getNativePtr())
            if self.hydraulics_model is None:
                raise PlantHydraulicsModelError(
                    "Failed to create PlantHydraulicsModel instance. "
                    "This may indicate a problem with the native library."
                )
            logger.info("PlantHydraulicsModel created successfully")

        except Exception as e:
            raise PlantHydraulicsModelError(f"Failed to initialize PlantHydraulicsModel: {e}")

    def _check_context_alive(self):
        """Raise if the owning Context has been destroyed (see Context.check_context_alive)."""
        check_context_alive(getattr(self, "context", None), "PlantHydraulicsModel")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit with proper cleanup."""
        if self.hydraulics_model is not None:
            try:
                hydraulics_wrapper.destroyPlantHydraulicsModel(self.hydraulics_model)
                logger.debug("PlantHydraulicsModel destroyed successfully")
            except Exception as e:
                logger.warning(f"Error destroying PlantHydraulicsModel: {e}")
            finally:
                self.hydraulics_model = None

    def __del__(self):
        """Destructor to ensure C++ resources freed even without 'with' statement."""
        if hasattr(self, 'hydraulics_model') and self.hydraulics_model is not None:
            try:
                hydraulics_wrapper.destroyPlantHydraulicsModel(self.hydraulics_model)
                self.hydraulics_model = None
            except Exception as e:
                import warnings
                warnings.warn(f"Error in PlantHydraulicsModel.__del__: {e}")

    def getNativePtr(self):
        """Get the native pointer for advanced operations."""
        return self.hydraulics_model

    # Model coefficients

    def setModelCoefficients(self, modelcoefficients: PlantHydraulicsModelCoefficients,
                             UUIDs: Optional[List[int]] = None) -> None:
        """
        Set the model coefficients for all primitives, or for a subset of primitives.

        Setting coefficients for all primitives clears any coefficients previously set for
        specific primitives.

        Coefficients set for specific primitives apply to their leaf conductance and capacitance
        only. Stem and root water potentials are always computed from the coefficients set for
        all primitives.

        Args:
            modelcoefficients: Hydraulic conductance and capacitance parameters
            UUIDs: Optional list of primitive UUIDs. If None, applies to all primitives.

        Raises:
            ValueError: If modelcoefficients is not a PlantHydraulicsModelCoefficients, a parameter is
                out of range, or UUIDs is empty
            PlantHydraulicsModelError: If operation fails

        Example:
            >>> coeffs = PlantHydraulicsModelCoefficients()
            >>> coeffs.setLeafHydraulicConductance(0.05, -1.5, 2.0)
            >>> hydraulics.setModelCoefficients(coeffs)
        """
        if not isinstance(modelcoefficients, PlantHydraulicsModelCoefficients):
            raise ValueError(
                "setModelCoefficients() modelcoefficients must be a PlantHydraulicsModelCoefficients, "
                f"got {type(modelcoefficients).__name__}"
            )
        modelcoefficients.validate('setModelCoefficients')
        uuid_list = None if UUIDs is None else _validate_uuids(UUIDs, 'setModelCoefficients')

        self._check_context_alive()
        try:
            if uuid_list is None:
                hydraulics_wrapper.setModelCoefficients(
                    self.hydraulics_model, modelcoefficients.to_list(), modelcoefficients.leaf_capacitance_species)
                self._per_primitive_uuids.clear()
            else:
                hydraulics_wrapper.setModelCoefficientsForUUIDs(
                    self.hydraulics_model, modelcoefficients.to_list(), uuid_list,
                    modelcoefficients.leaf_capacitance_species)
                self._per_primitive_uuids.update(uuid_list)
        except Exception as e:
            raise PlantHydraulicsModelError(f"Failed to set model coefficients: {e}")

    def setModelCoefficientsFromLibrary(self, species: str, UUIDs: Optional[Union[int, List[int]]] = None) -> None:
        """
        Set the model coefficients from the species library.

        The library provides leaf pressure-volume curve parameters; all other coefficients take
        their default values.

        Args:
            species: Species name. See pyhelios.PlantHydraulics.AVAILABLE_SPECIES.
            UUIDs: Optional primitive UUID or list of UUIDs. If None, applies to all primitives.

        Raises:
            ValueError: If the species is not in the library or UUIDs is empty
            PlantHydraulicsModelError: If operation fails

        Example:
            >>> hydraulics.setModelCoefficientsFromLibrary("Walnut")
        """
        _validate_species(species, 'setModelCoefficientsFromLibrary')
        if UUIDs is None:
            uuid_list = None
        elif isinstance(UUIDs, numbers.Integral) and not isinstance(UUIDs, bool):
            uuid_list = [_validate_int(UUIDs, 'UUID', 'setModelCoefficientsFromLibrary', 0)]
        else:
            uuid_list = _validate_uuids(UUIDs, 'setModelCoefficientsFromLibrary')

        self._check_context_alive()
        try:
            if uuid_list is None:
                hydraulics_wrapper.setModelCoefficientsFromLibrary(self.hydraulics_model, species)
                self._per_primitive_uuids.clear()
            else:
                hydraulics_wrapper.setModelCoefficientsFromLibraryForUUIDs(self.hydraulics_model, species, uuid_list)
                self._per_primitive_uuids.update(uuid_list)
        except Exception as e:
            raise PlantHydraulicsModelError(f"Failed to set model coefficients from library: {e}")

    def getModelCoefficients(self, UUID: int) -> PlantHydraulicsModelCoefficients:
        """
        Get the coefficients set for a specific primitive.

        Only coefficients given for specific primitives can be read: those set with
        setModelCoefficients() or setModelCoefficientsFromLibrary() and a UUIDs argument. A primitive
        without its own coefficients uses the model-wide ones, which the native model does not
        expose.

        Leaf capacitance taken from the species library is returned as its pressure-volume curve
        parameters, with leaf_capacitance_species set to None.

        Args:
            UUID: Primitive UUID

        Returns:
            A new PlantHydraulicsModelCoefficients holding the primitive's coefficients

        Raises:
            ValueError: If UUID is not a non-negative integer
            PlantHydraulicsModelError: If no coefficients were set for this primitive, or the
                operation fails

        Example:
            >>> hydraulics.setModelCoefficients(coeffs, UUIDs=[leaf_uuid])
            >>> hydraulics.getModelCoefficients(leaf_uuid).LeafHydraulicConductance.saturated_conductance
        """
        uuid = _validate_int(UUID, 'UUID', 'getModelCoefficients', 0)

        self._check_context_alive()
        if uuid not in self._per_primitive_uuids:
            raise PlantHydraulicsModelError(
                f"getModelCoefficients() primitive {uuid} has no coefficients of its own; it uses the "
                f"model-wide coefficients, which cannot be read back from the native model. Pass UUIDs to "
                f"setModelCoefficients() or setModelCoefficientsFromLibrary() to give it its own."
            )
        try:
            values = hydraulics_wrapper.getModelCoefficients(self.hydraulics_model, uuid)
        except Exception as e:
            raise PlantHydraulicsModelError(f"Failed to get model coefficients of primitive {uuid}: {e}")
        return PlantHydraulicsModelCoefficients.from_list(values)

    def getModelCoefficientsFromLibrary(self, species: str) -> PlantHydraulicsModelCoefficients:
        """
        Get the model coefficients of a species from the library.

        The library provides leaf pressure-volume curve parameters; all other coefficients are at
        their default values. The leaf capacitance is returned as its parameter values, with
        leaf_capacitance_species set to None.

        Args:
            species: Species name. See pyhelios.PlantHydraulics.AVAILABLE_SPECIES.

        Returns:
            A new PlantHydraulicsModelCoefficients

        Raises:
            ValueError: If the species is not in the library
            PlantHydraulicsModelError: If operation fails

        Example:
            >>> coeffs = hydraulics.getModelCoefficientsFromLibrary("Walnut")
            >>> coeffs.LeafHydraulicCapacitance.osmotic_potential_at_full_turgor
            -1.6386...
        """
        _validate_species(species, 'getModelCoefficientsFromLibrary')

        self._check_context_alive()
        try:
            values = hydraulics_wrapper.getModelCoefficientsFromLibrary(self.hydraulics_model, species)
        except Exception as e:
            raise PlantHydraulicsModelError(f"Failed to get model coefficients from library: {e}")
        return PlantHydraulicsModelCoefficients.from_list(values)

    # Execution

    def run(self, UUIDs: Optional[List[int]] = None, timespan: int = 0, timestep: int = 100) -> None:
        """
        Run the plant hydraulics model.

        Primitives sharing a plantID are treated as the leaves of one plant, with one stem, root and
        soil water potential. The model runs for every plant that the given primitives belong to,
        and writes output data to all primitives in the Context with that plantID, not only to the
        primitives given.

        Given primitives with no plantID are grouped into one new plant: those that do not belong
        to an object are added to a new polymesh object, and all of them are given the primitive
        data "plantID", set to that object's ID. Primitives that already belong to an object stay
        in it.

        Args:
            UUIDs: Optional list of primitive UUIDs selecting the plants to run. If None, runs for
                all primitives in the Context; primitives with no plantID, including any that are
                not leaves, are then grouped into a single plant.
            timespan: Duration of the simulation (s). 0 gives the steady-state solution.
            timestep: Timestep of a non-steady-state simulation (s).

        Raises:
            ValueError: If UUIDs is empty, timespan is negative, or timestep is not positive
            PlantHydraulicsModelError: If calculation fails, including when every primitive without a
                plantID already belongs to an object, so that no polymesh object can be created

        Note:
            Non-steady-state runs (timespan > 0) are under construction in the native plugin, and
            require constant stem and root capacitances.

        Example:
            >>> hydraulics.run(leaf_uuids)          # steady state, the plants these leaves belong to
        """
        uuid_list = None if UUIDs is None else _validate_uuids(UUIDs, 'run')
        timespan = _validate_int(timespan, 'timespan', 'run', 0)
        timestep = _validate_int(timestep, 'timestep', 'run', 1)

        self._check_context_alive()
        try:
            if uuid_list is None:
                hydraulics_wrapper.run(self.hydraulics_model, timespan, timestep)
            else:
                hydraulics_wrapper.runForUUIDs(self.hydraulics_model, uuid_list, timespan, timestep)
        except Exception as e:
            raise PlantHydraulicsModelError(f"Failed to run plant hydraulics model: {e}")

    def outputConductancePrimitiveData(self, toggle: bool) -> None:
        """
        Toggle writing of the optional primitive data "hydraulic_conductance" (mol/m²/s/MPa).

        The data is written by non-steady-state runs only.

        Args:
            toggle: True to write the data
        """
        _validate_bool(toggle, 'toggle', 'outputConductancePrimitiveData')
        self._check_context_alive()
        try:
            hydraulics_wrapper.outputConductancePrimitiveData(self.hydraulics_model, toggle)
        except Exception as e:
            raise PlantHydraulicsModelError(f"Failed to set conductance output: {e}")

    def outputCapacitancePrimitiveData(self, toggle: bool) -> None:
        """
        Toggle writing of the optional primitive data "hydraulic_capacitance" (mol/m²/MPa).

        The data is written by non-steady-state runs only.

        Args:
            toggle: True to write the data
        """
        _validate_bool(toggle, 'toggle', 'outputCapacitancePrimitiveData')
        self._check_context_alive()
        try:
            hydraulics_wrapper.outputCapacitancePrimitiveData(self.hydraulics_model, toggle)
        except Exception as e:
            raise PlantHydraulicsModelError(f"Failed to set capacitance output: {e}")

    # Plant grouping

    def groupPrimitivesIntoPlantObject(self, UUIDs: List[int]) -> int:
        """
        Group leaf primitives into a plant that shares stem, root and soil hydraulics.

        Those of the primitives that do not belong to an object are added to a new polymesh object.
        All of them are given the primitive data "plantID", set to that object's ID; primitives
        that already belong to an object stay in it.

        Args:
            UUIDs: Leaf primitive UUIDs

        Returns:
            The plantID assigned to the primitives

        Raises:
            ValueError: If UUIDs is empty, or any of the primitives already has a plantID
            PlantHydraulicsModelError: If all of the primitives already belong to an object, so that
                no polymesh object can be created
        """
        uuid_list = _validate_uuids(UUIDs, 'groupPrimitivesIntoPlantObject')
        self._check_context_alive()
        try:
            ungrouped = hydraulics_wrapper.getPrimitivesWithoutPlantID(self.hydraulics_model, uuid_list)
        except Exception as e:
            raise PlantHydraulicsModelError(f"Failed to group primitives into plant object: {e}")
        already_grouped = sorted(set(uuid_list) - set(ungrouped))
        if already_grouped:
            raise ValueError(
                "groupPrimitivesIntoPlantObject() primitives already have a plantID: "
                f"{already_grouped[:10]}{'...' if len(already_grouped) > 10 else ''}"
            )
        try:
            hydraulics_wrapper.groupPrimitivesIntoPlantObject(self.hydraulics_model, uuid_list)
            return hydraulics_wrapper.getPlantIDForUUIDs(self.hydraulics_model, uuid_list)
        except Exception as e:
            raise PlantHydraulicsModelError(f"Failed to group primitives into plant object: {e}")

    def getPlantID(self, UUIDs: Union[int, List[int]]) -> int:
        """
        Get the plantID of a primitive, or the plantID shared by a list of primitives.

        Args:
            UUIDs: Primitive UUID or list of UUIDs

        Returns:
            The plantID

        Raises:
            ValueError: If UUIDs is empty
            PlantHydraulicsModelError: If a primitive has no plantID, or the primitives do not share one
        """
        single, uuid_list = self._single_or_list(UUIDs, 'getPlantID')
        self._check_context_alive()
        try:
            if single:
                return hydraulics_wrapper.getPlantID(self.hydraulics_model, uuid_list[0])
            self._require_shared_plant(uuid_list)
            return hydraulics_wrapper.getPlantIDForUUIDs(self.hydraulics_model, uuid_list)
        except Exception as e:
            raise PlantHydraulicsModelError(f"Failed to get plantID: {e}")

    def _require_shared_plant(self, uuid_list: List[int]) -> None:
        # The native list overloads compare only the first and last primitive.
        plant_ids = hydraulics_wrapper.getUniquePlantIDs(self.hydraulics_model, uuid_list)
        if len(plant_ids) > 1:
            raise ValueError(f"UUIDs do not share the same plantID; found plantIDs {sorted(plant_ids)}")

    def getUniquePlantIDs(self, UUIDs: List[int]) -> List[int]:
        """
        Get the unique plantIDs of a list of primitives.

        Args:
            UUIDs: Primitive UUIDs

        Returns:
            List of unique plantIDs

        Raises:
            ValueError: If UUIDs is empty
            PlantHydraulicsModelError: If a primitive has no plantID
        """
        uuid_list = _validate_uuids(UUIDs, 'getUniquePlantIDs')
        self._check_context_alive()
        try:
            return hydraulics_wrapper.getUniquePlantIDs(self.hydraulics_model, uuid_list)
        except Exception as e:
            raise PlantHydraulicsModelError(f"Failed to get unique plantIDs: {e}")

    def getPrimitivesByPlantID(self, plantID: int) -> List[int]:
        """
        Get the primitives belonging to a plant.

        Args:
            plantID: Plant identifier

        Returns:
            List of primitive UUIDs; empty if no primitive has this plantID
        """
        if isinstance(plantID, bool) or not isinstance(plantID, numbers.Integral):
            raise ValueError(f"getPrimitivesByPlantID() plantID must be an integer, got {type(plantID).__name__}")
        self._check_context_alive()
        try:
            return hydraulics_wrapper.getPrimitivesByPlantID(self.hydraulics_model, int(plantID))
        except Exception as e:
            raise PlantHydraulicsModelError(f"Failed to get primitives by plantID: {e}")

    def getPrimitivesWithoutPlantID(self, UUIDs: List[int]) -> List[int]:
        """
        Get the primitives that have no plantID, in either parent object data or primitive data.

        Args:
            UUIDs: Primitive UUIDs to check

        Returns:
            List of primitive UUIDs without a plantID

        Raises:
            ValueError: If UUIDs is empty
        """
        uuid_list = _validate_uuids(UUIDs, 'getPrimitivesWithoutPlantID')
        self._check_context_alive()
        try:
            return hydraulics_wrapper.getPrimitivesWithoutPlantID(self.hydraulics_model, uuid_list)
        except Exception as e:
            raise PlantHydraulicsModelError(f"Failed to get primitives without plantID: {e}")

    # Water potentials

    @staticmethod
    def _single_or_list(UUIDs, method_name: str):
        if isinstance(UUIDs, numbers.Integral) and not isinstance(UUIDs, bool):
            return True, [_validate_int(UUIDs, 'UUID', method_name, 0)]
        return False, _validate_uuids(UUIDs, method_name)

    def _get_water_potential(self, compartment: str, UUIDs, method_name: str) -> float:
        single, uuid_list = self._single_or_list(UUIDs, method_name)
        self._check_context_alive()
        try:
            if single:
                return hydraulics_wrapper.getWaterPotential(self.hydraulics_model, compartment, uuid_list[0])
            self._require_shared_plant(uuid_list)
            return hydraulics_wrapper.getWaterPotentialForUUIDs(self.hydraulics_model, compartment, uuid_list)
        except Exception as e:
            raise PlantHydraulicsModelError(f"Failed to get {compartment.lower()} water potential: {e}")

    def _get_water_potential_of_plant(self, compartment: str, plantID, method_name: str) -> float:
        plant_id = _validate_int(plantID, 'plantID', method_name, 0)
        self._check_context_alive()
        try:
            return hydraulics_wrapper.getWaterPotentialOfPlant(self.hydraulics_model, compartment, plant_id)
        except Exception as e:
            raise PlantHydraulicsModelError(f"Failed to get {compartment.lower()} water potential of plant: {e}")

    def getStemWaterPotential(self, UUIDs: Union[int, List[int]]) -> float:
        """
        Get the stem water potential (MPa) of the plant that a leaf primitive, or a list of leaf
        primitives of one plant, belongs to.

        Raises:
            PlantHydraulicsModelError: If the model has not been run for the plant
        """
        return self._get_water_potential('Stem', UUIDs, 'getStemWaterPotential')

    def getStemWaterPotentialOfPlant(self, plantID: int) -> float:
        """
        Get the stem water potential (MPa) of a plant.

        Raises:
            PlantHydraulicsModelError: If the model has not been run for the plant
        """
        return self._get_water_potential_of_plant('Stem', plantID, 'getStemWaterPotentialOfPlant')

    def getRootWaterPotential(self, UUIDs: Union[int, List[int]]) -> float:
        """
        Get the root water potential (MPa) of the plant that a leaf primitive, or a list of leaf
        primitives of one plant, belongs to.

        Raises:
            PlantHydraulicsModelError: If the model has not been run for the plant
        """
        return self._get_water_potential('Root', UUIDs, 'getRootWaterPotential')

    def getRootWaterPotentialOfPlant(self, plantID: int) -> float:
        """
        Get the root water potential (MPa) of a plant.

        Raises:
            PlantHydraulicsModelError: If the model has not been run for the plant
        """
        return self._get_water_potential_of_plant('Root', plantID, 'getRootWaterPotentialOfPlant')

    def getSoilWaterPotential(self, UUIDs: Union[int, List[int]]) -> float:
        """
        Get the soil water potential (MPa) of the plant that a leaf primitive, or a list of leaf
        primitives of one plant, belongs to.

        Raises:
            PlantHydraulicsModelError: If no soil water potential has been set and the model has not been
                run for the plant
        """
        return self._get_water_potential('Soil', UUIDs, 'getSoilWaterPotential')

    def getSoilWaterPotentialOfPlant(self, plantID: int) -> float:
        """
        Get the soil water potential (MPa) of a plant.

        Raises:
            PlantHydraulicsModelError: If no soil water potential has been set and the model has not been
                run for the plant
        """
        return self._get_water_potential_of_plant('Soil', plantID, 'getSoilWaterPotentialOfPlant')

    def setSoilWaterPotentialOfPlant(self, plantID: int, soil_water_potential: float) -> None:
        """
        Set the soil water potential of a plant.

        Plants with no soil water potential set use -0.001 MPa.

        Args:
            plantID: Plant identifier
            soil_water_potential: Soil water potential (MPa)

        Example:
            >>> plantID = hydraulics.getPlantID(leaf_uuids)
            >>> hydraulics.setSoilWaterPotentialOfPlant(plantID, -0.05)
        """
        plant_id = _validate_int(plantID, 'plantID', 'setSoilWaterPotentialOfPlant', 0)
        potential = _validate_float(soil_water_potential, 'soil_water_potential', 'setSoilWaterPotentialOfPlant')
        self._check_context_alive()
        try:
            hydraulics_wrapper.setSoilWaterPotentialOfPlant(self.hydraulics_model, plant_id, potential)
        except Exception as e:
            raise PlantHydraulicsModelError(f"Failed to set soil water potential: {e}")

    # Pressure-volume and vulnerability curves

    @staticmethod
    def _validate_curve_args(coeffs, relative_water_content, method_name: str) -> float:
        if not isinstance(coeffs, HydraulicCapacitance):
            raise ValueError(f"{method_name}() coeffs must be a HydraulicCapacitance, got {type(coeffs).__name__}")
        coeffs.validate(method_name)
        water_content = _validate_float(relative_water_content, 'relative_water_content', method_name)
        if not 0.0 < water_content <= 1.0:
            raise ValueError(f"{method_name}() relative_water_content must be in (0, 1], got {water_content}")
        return water_content

    @staticmethod
    def computeOsmoticPotential(coeffs: HydraulicCapacitance, relative_water_content: float) -> float:
        """
        Compute osmotic potential (MPa) at a relative water content from pressure-volume curve parameters.

        Args:
            coeffs: Pressure-volume curve parameters
            relative_water_content: Relative water content (unitless), in (0, 1]
        """
        water_content = PlantHydraulicsModel._validate_curve_args(coeffs, relative_water_content, 'computeOsmoticPotential')
        return hydraulics_wrapper.computeOsmoticPotential(coeffs.to_list(), water_content)

    @staticmethod
    def computeTurgorPressure(coeffs: HydraulicCapacitance, relative_water_content: float) -> float:
        """
        Compute turgor pressure (MPa) at a relative water content from pressure-volume curve parameters.

        Args:
            coeffs: Pressure-volume curve parameters
            relative_water_content: Relative water content (unitless), in (0, 1]
        """
        water_content = PlantHydraulicsModel._validate_curve_args(coeffs, relative_water_content, 'computeTurgorPressure')
        return hydraulics_wrapper.computeTurgorPressure(coeffs.to_list(), water_content)

    @staticmethod
    def computeWaterPotential(coeffs: HydraulicCapacitance, relative_water_content: float) -> float:
        """
        Compute water potential (MPa) at a relative water content, the sum of turgor pressure and
        osmotic potential from pressure-volume curve parameters.

        Args:
            coeffs: Pressure-volume curve parameters
            relative_water_content: Relative water content (unitless), in (0, 1]
        """
        water_content = PlantHydraulicsModel._validate_curve_args(coeffs, relative_water_content, 'computeWaterPotential')
        return hydraulics_wrapper.computeWaterPotential(coeffs.to_list(), water_content)

    @staticmethod
    def computeCapacitance(coeffs: HydraulicCapacitance, relative_water_content: float) -> float:
        """
        Compute hydraulic capacitance (mol/m²/MPa) at a relative water content.

        Returns the constant capacitance if coeffs holds one, otherwise the saturated specific water
        content divided by the slope of the pressure-volume curve.

        Args:
            coeffs: Hydraulic capacitance parameters
            relative_water_content: Relative water content (unitless), in (0.001, 1]
        """
        water_content = PlantHydraulicsModel._validate_curve_args(coeffs, relative_water_content, 'computeCapacitance')
        if not coeffs.is_constant() and water_content <= 0.001:
            raise ValueError(f"computeCapacitance() relative_water_content must be > 0.001, got {water_content}")
        return hydraulics_wrapper.computeCapacitance(coeffs.to_list(), water_content)

    @staticmethod
    def computeConductance(coeffs: HydraulicConductance, water_potential: float, temperature: float = 298.15) -> float:
        """
        Compute hydraulic conductance (mol/m²/s/MPa) at a water potential and temperature.

        Args:
            coeffs: Hydraulic conductance parameters
            water_potential: Water potential (MPa)
            temperature: Temperature (K); used only if coeffs has temperature dependence enabled
        """
        if not isinstance(coeffs, HydraulicConductance):
            raise ValueError(f"computeConductance() coeffs must be a HydraulicConductance, got {type(coeffs).__name__}")
        coeffs.validate('computeConductance')
        potential = _validate_float(water_potential, 'water_potential', 'computeConductance')
        temperature_K = _validate_float(temperature, 'temperature', 'computeConductance')
        if temperature_K <= 0.0:
            raise ValueError(f"computeConductance() temperature must be > 0 K, got {temperature_K}")
        return hydraulics_wrapper.computeConductance(coeffs.to_list(), potential, temperature_K)

    def is_available(self) -> bool:
        """
        Check if PlantHydraulicsModel is available in current build.

        Returns:
            True if plugin is available, False otherwise
        """
        registry = get_plugin_registry()
        return registry.is_plugin_available('planthydraulics')


# Convenience function
def create_plant_hydraulics_model(context: Context) -> PlantHydraulicsModel:
    """
    Create PlantHydraulicsModel instance with context.

    Args:
        context: Helios Context

    Returns:
        PlantHydraulicsModel instance
    """
    return PlantHydraulicsModel(context)
