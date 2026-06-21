"""Typed model for Helios plant architecture parameters.

This module provides discoverable, validated dataclasses mirroring the nested
C++ ``ShootParameters`` / ``PhytomerParameters`` / ``LeafPrototype`` structures
(plus the flat ``CarbohydrateParameters`` / ``NitrogenParameters``). The objects
serialize to/from the plain ``dict`` JSON transport used by the PlantArchitecture
wrapper, so they can be used interchangeably with the raw-dict API.

Canonical usage builds a typed object from the values currently defined in the
native library, mutates it, and applies it back -- this avoids any drift between
Python-side defaults and the C++ defaults::

    from pyhelios import Context, PlantArchitecture
    from pyhelios.plant_architecture_params import ShootParameters, RandomParameterFloat

    with Context() as ctx:
        pa = PlantArchitecture(ctx)
        pa.loadPlantModelFromLibrary("almond")
        sp = ShootParameters.from_dict(pa.getCurrentShootParameters("trunk"))
        sp.phytomer_parameters.leaf.pitch = RandomParameterFloat.uniform(40, 50)
        pa.defineShootType("trunk2", sp)

Notes
-----
* Every numeric leaf/shoot/phytomer field is a :class:`RandomParameterFloat` or
  :class:`RandomParameterInt` carrying a distribution and its parameters.
* Prototype functions (leaf/flower/fruit) are referenced by *name* -- a string
  naming a built-in Helios prototype (e.g. ``"AlmondFlowerPrototype"``). An empty
  string / ``None`` means "unset". The C++ ``shared_ptr<Phytomer>`` creation and
  callback functions are not exposable from Python and are not represented here.
* Child shoot types serialize on input only (the native struct has no public
  getter); see :attr:`ShootParameters.child_shoot_types`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

__all__ = [
    "RandomParameterFloat",
    "RandomParameterInt",
    "LeafPrototype",
    "InternodeParameters",
    "PetioleParameters",
    "LeafParameters",
    "PeduncleParameters",
    "InflorescenceParameters",
    "PhytomerParameters",
    "ShootParameters",
    "CarbohydrateParameters",
    "NitrogenParameters",
]


# --------------------------------------------------------------------------- #
# Random parameters
# --------------------------------------------------------------------------- #
@dataclass
class RandomParameterFloat:
    """A float-valued parameter with a sampling distribution.

    Use the classmethod constructors (:meth:`constant`, :meth:`uniform`,
    :meth:`normal`, :meth:`weibull`) rather than constructing directly.
    """

    distribution: str = "constant"
    parameters: List[float] = field(default_factory=lambda: [0.0])

    @classmethod
    def constant(cls, value: float) -> "RandomParameterFloat":
        return cls("constant", [float(value)])

    @classmethod
    def uniform(cls, min_val: float, max_val: float) -> "RandomParameterFloat":
        return cls("uniform", [float(min_val), float(max_val)])

    @classmethod
    def normal(cls, mean: float, std_dev: float) -> "RandomParameterFloat":
        return cls("normal", [float(mean), float(std_dev)])

    @classmethod
    def weibull(cls, shape: float, scale: float) -> "RandomParameterFloat":
        return cls("weibull", [float(shape), float(scale)])

    def to_dict(self) -> Dict[str, Any]:
        return {"distribution": self.distribution, "parameters": [float(p) for p in self.parameters]}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RandomParameterFloat":
        return cls(str(d["distribution"]), [float(p) for p in d["parameters"]])


@dataclass
class RandomParameterInt:
    """An int-valued parameter with a sampling distribution."""

    distribution: str = "constant"
    parameters: List[int] = field(default_factory=lambda: [0])

    @classmethod
    def constant(cls, value: int) -> "RandomParameterInt":
        return cls("constant", [int(value)])

    @classmethod
    def uniform(cls, min_val: int, max_val: int) -> "RandomParameterInt":
        return cls("uniform", [int(min_val), int(max_val)])

    @classmethod
    def discrete(cls, values: List[int]) -> "RandomParameterInt":
        return cls("discretevalues", [int(v) for v in values])

    def to_dict(self) -> Dict[str, Any]:
        # The native JSON transport encodes int distribution parameters as floats.
        return {"distribution": self.distribution, "parameters": [float(p) for p in self.parameters]}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RandomParameterInt":
        return cls(str(d["distribution"]), [int(round(float(p))) for p in d["parameters"]])


# --------------------------------------------------------------------------- #
# Helpers for color / vec3 (encoded as plain tuples on the Python side)
# --------------------------------------------------------------------------- #
Color = Tuple[float, float, float]
Vec3 = Tuple[float, float, float]


def _rpf(d: Dict[str, Any], key: str, default: RandomParameterFloat) -> RandomParameterFloat:
    return RandomParameterFloat.from_dict(d[key]) if key in d else default


def _rpi(d: Dict[str, Any], key: str, default: RandomParameterInt) -> RandomParameterInt:
    return RandomParameterInt.from_dict(d[key]) if key in d else default


def _color_to_dict(c: Color) -> Dict[str, float]:
    return {"r": float(c[0]), "g": float(c[1]), "b": float(c[2])}


def _color_from_dict(d: Dict[str, Any], default: Color) -> Color:
    return (float(d.get("r", default[0])), float(d.get("g", default[1])), float(d.get("b", default[2])))


def _vec3_to_dict(v: Vec3) -> Dict[str, float]:
    return {"x": float(v[0]), "y": float(v[1]), "z": float(v[2])}


def _vec3_from_dict(d: Dict[str, Any], default: Vec3) -> Vec3:
    return (float(d.get("x", default[0])), float(d.get("y", default[1])), float(d.get("z", default[2])))


# --------------------------------------------------------------------------- #
# Leaf prototype
# --------------------------------------------------------------------------- #
@dataclass
class LeafPrototype:
    leaf_aspect_ratio: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(1.0))
    midrib_fold_fraction: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    longitudinal_curvature: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    lateral_curvature: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    petiole_roll: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    wave_period: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    wave_amplitude: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    leaf_buckle_length: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    leaf_buckle_angle: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    leaf_offset: Vec3 = (0.0, 0.0, 0.0)
    subdivisions: int = 1
    unique_prototypes: int = 1
    build_petiolule: bool = False
    OBJ_model_file: str = ""
    leaf_texture_file: Dict[int, str] = field(default_factory=dict)
    prototype_function: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "leaf_aspect_ratio": self.leaf_aspect_ratio.to_dict(),
            "midrib_fold_fraction": self.midrib_fold_fraction.to_dict(),
            "longitudinal_curvature": self.longitudinal_curvature.to_dict(),
            "lateral_curvature": self.lateral_curvature.to_dict(),
            "petiole_roll": self.petiole_roll.to_dict(),
            "wave_period": self.wave_period.to_dict(),
            "wave_amplitude": self.wave_amplitude.to_dict(),
            "leaf_buckle_length": self.leaf_buckle_length.to_dict(),
            "leaf_buckle_angle": self.leaf_buckle_angle.to_dict(),
            "leaf_offset": _vec3_to_dict(self.leaf_offset),
            "subdivisions": int(self.subdivisions),
            "unique_prototypes": int(self.unique_prototypes),
            "build_petiolule": bool(self.build_petiolule),
            "OBJ_model_file": self.OBJ_model_file,
            "leaf_texture_file": {str(k): v for k, v in self.leaf_texture_file.items()},
            "prototype_function": self.prototype_function or "",
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LeafPrototype":
        base = cls()
        tex = d.get("leaf_texture_file", {})
        return cls(
            leaf_aspect_ratio=_rpf(d, "leaf_aspect_ratio", base.leaf_aspect_ratio),
            midrib_fold_fraction=_rpf(d, "midrib_fold_fraction", base.midrib_fold_fraction),
            longitudinal_curvature=_rpf(d, "longitudinal_curvature", base.longitudinal_curvature),
            lateral_curvature=_rpf(d, "lateral_curvature", base.lateral_curvature),
            petiole_roll=_rpf(d, "petiole_roll", base.petiole_roll),
            wave_period=_rpf(d, "wave_period", base.wave_period),
            wave_amplitude=_rpf(d, "wave_amplitude", base.wave_amplitude),
            leaf_buckle_length=_rpf(d, "leaf_buckle_length", base.leaf_buckle_length),
            leaf_buckle_angle=_rpf(d, "leaf_buckle_angle", base.leaf_buckle_angle),
            leaf_offset=_vec3_from_dict(d["leaf_offset"], base.leaf_offset) if "leaf_offset" in d else base.leaf_offset,
            subdivisions=int(d.get("subdivisions", base.subdivisions)),
            unique_prototypes=int(d.get("unique_prototypes", base.unique_prototypes)),
            build_petiolule=bool(d.get("build_petiolule", base.build_petiolule)),
            OBJ_model_file=str(d.get("OBJ_model_file", base.OBJ_model_file)),
            leaf_texture_file={int(k): str(v) for k, v in tex.items()},
            prototype_function=(d.get("prototype_function") or None),
        )


# --------------------------------------------------------------------------- #
# Phytomer sub-structures
# --------------------------------------------------------------------------- #
@dataclass
class InternodeParameters:
    pitch: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(20.0))
    phyllotactic_angle: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(137.5))
    radius_initial: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.001))
    max_vegetative_buds_per_petiole: RandomParameterInt = field(default_factory=lambda: RandomParameterInt.constant(0))
    max_floral_buds_per_petiole: RandomParameterInt = field(default_factory=lambda: RandomParameterInt.constant(0))
    color: Color = (0.0, 0.0, 0.0)
    image_texture: str = ""
    length_segments: int = 1
    radial_subdivisions: int = 7

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pitch": self.pitch.to_dict(),
            "phyllotactic_angle": self.phyllotactic_angle.to_dict(),
            "radius_initial": self.radius_initial.to_dict(),
            "max_vegetative_buds_per_petiole": self.max_vegetative_buds_per_petiole.to_dict(),
            "max_floral_buds_per_petiole": self.max_floral_buds_per_petiole.to_dict(),
            "color": _color_to_dict(self.color),
            "image_texture": self.image_texture,
            "length_segments": int(self.length_segments),
            "radial_subdivisions": int(self.radial_subdivisions),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "InternodeParameters":
        base = cls()
        return cls(
            pitch=_rpf(d, "pitch", base.pitch),
            phyllotactic_angle=_rpf(d, "phyllotactic_angle", base.phyllotactic_angle),
            radius_initial=_rpf(d, "radius_initial", base.radius_initial),
            max_vegetative_buds_per_petiole=_rpi(d, "max_vegetative_buds_per_petiole", base.max_vegetative_buds_per_petiole),
            max_floral_buds_per_petiole=_rpi(d, "max_floral_buds_per_petiole", base.max_floral_buds_per_petiole),
            color=_color_from_dict(d["color"], base.color) if "color" in d else base.color,
            image_texture=str(d.get("image_texture", base.image_texture)),
            length_segments=int(d.get("length_segments", base.length_segments)),
            radial_subdivisions=int(d.get("radial_subdivisions", base.radial_subdivisions)),
        )


@dataclass
class PetioleParameters:
    petioles_per_internode: int = 1
    pitch: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(90.0))
    radius: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.001))
    length: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.05))
    curvature: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    taper: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    color: Color = (0.0, 0.0, 0.0)
    length_segments: int = 1
    radial_subdivisions: int = 7

    def to_dict(self) -> Dict[str, Any]:
        return {
            "petioles_per_internode": int(self.petioles_per_internode),
            "pitch": self.pitch.to_dict(),
            "radius": self.radius.to_dict(),
            "length": self.length.to_dict(),
            "curvature": self.curvature.to_dict(),
            "taper": self.taper.to_dict(),
            "color": _color_to_dict(self.color),
            "length_segments": int(self.length_segments),
            "radial_subdivisions": int(self.radial_subdivisions),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PetioleParameters":
        base = cls()
        return cls(
            petioles_per_internode=int(d.get("petioles_per_internode", base.petioles_per_internode)),
            pitch=_rpf(d, "pitch", base.pitch),
            radius=_rpf(d, "radius", base.radius),
            length=_rpf(d, "length", base.length),
            curvature=_rpf(d, "curvature", base.curvature),
            taper=_rpf(d, "taper", base.taper),
            color=_color_from_dict(d["color"], base.color) if "color" in d else base.color,
            length_segments=int(d.get("length_segments", base.length_segments)),
            radial_subdivisions=int(d.get("radial_subdivisions", base.radial_subdivisions)),
        )


@dataclass
class LeafParameters:
    leaves_per_petiole: RandomParameterInt = field(default_factory=lambda: RandomParameterInt.constant(1))
    pitch: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    yaw: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    roll: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    leaflet_offset: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    leaflet_scale: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(1.0))
    prototype_scale: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.05))
    prototype: LeafPrototype = field(default_factory=LeafPrototype)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "leaves_per_petiole": self.leaves_per_petiole.to_dict(),
            "pitch": self.pitch.to_dict(),
            "yaw": self.yaw.to_dict(),
            "roll": self.roll.to_dict(),
            "leaflet_offset": self.leaflet_offset.to_dict(),
            "leaflet_scale": self.leaflet_scale.to_dict(),
            "prototype_scale": self.prototype_scale.to_dict(),
            "prototype": self.prototype.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LeafParameters":
        base = cls()
        return cls(
            leaves_per_petiole=_rpi(d, "leaves_per_petiole", base.leaves_per_petiole),
            pitch=_rpf(d, "pitch", base.pitch),
            yaw=_rpf(d, "yaw", base.yaw),
            roll=_rpf(d, "roll", base.roll),
            leaflet_offset=_rpf(d, "leaflet_offset", base.leaflet_offset),
            leaflet_scale=_rpf(d, "leaflet_scale", base.leaflet_scale),
            prototype_scale=_rpf(d, "prototype_scale", base.prototype_scale),
            prototype=LeafPrototype.from_dict(d["prototype"]) if "prototype" in d else base.prototype,
        )


@dataclass
class PeduncleParameters:
    length: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.05))
    radius: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.001))
    pitch: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    roll: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    curvature: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    color: Color = (0.0, 0.0, 0.0)
    length_segments: int = 3
    radial_subdivisions: int = 7

    def to_dict(self) -> Dict[str, Any]:
        return {
            "length": self.length.to_dict(),
            "radius": self.radius.to_dict(),
            "pitch": self.pitch.to_dict(),
            "roll": self.roll.to_dict(),
            "curvature": self.curvature.to_dict(),
            "color": _color_to_dict(self.color),
            "length_segments": int(self.length_segments),
            "radial_subdivisions": int(self.radial_subdivisions),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PeduncleParameters":
        base = cls()
        return cls(
            length=_rpf(d, "length", base.length),
            radius=_rpf(d, "radius", base.radius),
            pitch=_rpf(d, "pitch", base.pitch),
            roll=_rpf(d, "roll", base.roll),
            curvature=_rpf(d, "curvature", base.curvature),
            color=_color_from_dict(d["color"], base.color) if "color" in d else base.color,
            length_segments=int(d.get("length_segments", base.length_segments)),
            radial_subdivisions=int(d.get("radial_subdivisions", base.radial_subdivisions)),
        )


@dataclass
class InflorescenceParameters:
    flowers_per_peduncle: RandomParameterInt = field(default_factory=lambda: RandomParameterInt.constant(1))
    flower_offset: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    pitch: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    roll: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    flower_prototype_scale: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0075))
    fruit_prototype_scale: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0075))
    fruit_gravity_factor_fraction: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    unique_prototypes: int = 1
    flower_prototype_function: Optional[str] = None
    fruit_prototype_function: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "flowers_per_peduncle": self.flowers_per_peduncle.to_dict(),
            "flower_offset": self.flower_offset.to_dict(),
            "pitch": self.pitch.to_dict(),
            "roll": self.roll.to_dict(),
            "flower_prototype_scale": self.flower_prototype_scale.to_dict(),
            "fruit_prototype_scale": self.fruit_prototype_scale.to_dict(),
            "fruit_gravity_factor_fraction": self.fruit_gravity_factor_fraction.to_dict(),
            "unique_prototypes": int(self.unique_prototypes),
            "flower_prototype_function": self.flower_prototype_function or "",
            "fruit_prototype_function": self.fruit_prototype_function or "",
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "InflorescenceParameters":
        base = cls()
        return cls(
            flowers_per_peduncle=_rpi(d, "flowers_per_peduncle", base.flowers_per_peduncle),
            flower_offset=_rpf(d, "flower_offset", base.flower_offset),
            pitch=_rpf(d, "pitch", base.pitch),
            roll=_rpf(d, "roll", base.roll),
            flower_prototype_scale=_rpf(d, "flower_prototype_scale", base.flower_prototype_scale),
            fruit_prototype_scale=_rpf(d, "fruit_prototype_scale", base.fruit_prototype_scale),
            fruit_gravity_factor_fraction=_rpf(d, "fruit_gravity_factor_fraction", base.fruit_gravity_factor_fraction),
            unique_prototypes=int(d.get("unique_prototypes", base.unique_prototypes)),
            flower_prototype_function=(d.get("flower_prototype_function") or None),
            fruit_prototype_function=(d.get("fruit_prototype_function") or None),
        )


@dataclass
class PhytomerParameters:
    internode: InternodeParameters = field(default_factory=InternodeParameters)
    petiole: PetioleParameters = field(default_factory=PetioleParameters)
    leaf: LeafParameters = field(default_factory=LeafParameters)
    peduncle: PeduncleParameters = field(default_factory=PeduncleParameters)
    inflorescence: InflorescenceParameters = field(default_factory=InflorescenceParameters)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "internode": self.internode.to_dict(),
            "petiole": self.petiole.to_dict(),
            "leaf": self.leaf.to_dict(),
            "peduncle": self.peduncle.to_dict(),
            "inflorescence": self.inflorescence.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PhytomerParameters":
        base = cls()
        return cls(
            internode=InternodeParameters.from_dict(d["internode"]) if "internode" in d else base.internode,
            petiole=PetioleParameters.from_dict(d["petiole"]) if "petiole" in d else base.petiole,
            leaf=LeafParameters.from_dict(d["leaf"]) if "leaf" in d else base.leaf,
            peduncle=PeduncleParameters.from_dict(d["peduncle"]) if "peduncle" in d else base.peduncle,
            inflorescence=InflorescenceParameters.from_dict(d["inflorescence"]) if "inflorescence" in d else base.inflorescence,
        )


# --------------------------------------------------------------------------- #
# Shoot parameters
# --------------------------------------------------------------------------- #
# Top-level ShootParameters fields, with their RandomParameter kind. Keeping this
# as a table avoids 20+ near-identical lines in both to_dict and from_dict.
_SHOOT_RPF_FIELDS = (
    ("girth_area_factor", 0.0),
    ("insertion_angle_tip", 20.0),
    ("insertion_angle_decay_rate", 0.0),
    ("internode_length_max", 0.02),
    ("internode_length_min", 0.002),
    ("internode_length_decay_rate", 0.0),
    ("base_roll", 0.0),
    ("base_yaw", 0.0),
    ("gravitropic_curvature", 0.0),
    ("tortuosity", 0.0),
    ("phyllochron_min", 2.0),
    ("elongation_rate_max", 0.2),
    ("vegetative_bud_break_probability_min", 0.0),
    ("vegetative_bud_break_probability_max", 1.0),
    ("vegetative_bud_break_probability_decay_rate", -0.5),
    ("flower_bud_break_probability", 0.0),
    ("fruit_set_probability", 0.0),
    ("vegetative_bud_break_time", 5.0),
)
_SHOOT_RPI_FIELDS = (
    ("max_nodes", 10),
    ("max_nodes_per_season", 9999),
    ("max_terminal_floral_buds", 0),
)
_SHOOT_BOOL_FIELDS = (
    ("flowers_require_dormancy", False),
    ("growth_requires_dormancy", False),
    ("determinate_shoot_growth", True),
)


@dataclass
class ShootParameters:
    phytomer_parameters: PhytomerParameters = field(default_factory=PhytomerParameters)

    # Geometric / growth RandomParameter_float fields
    girth_area_factor: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    insertion_angle_tip: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(20.0))
    insertion_angle_decay_rate: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    internode_length_max: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.02))
    internode_length_min: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.002))
    internode_length_decay_rate: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    base_roll: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    base_yaw: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    gravitropic_curvature: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    tortuosity: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    phyllochron_min: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(2.0))
    elongation_rate_max: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.2))
    vegetative_bud_break_probability_min: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    vegetative_bud_break_probability_max: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(1.0))
    vegetative_bud_break_probability_decay_rate: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(-0.5))
    flower_bud_break_probability: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    fruit_set_probability: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(0.0))
    vegetative_bud_break_time: RandomParameterFloat = field(default_factory=lambda: RandomParameterFloat.constant(5.0))

    # RandomParameter_int fields
    max_nodes: RandomParameterInt = field(default_factory=lambda: RandomParameterInt.constant(10))
    max_nodes_per_season: RandomParameterInt = field(default_factory=lambda: RandomParameterInt.constant(9999))
    max_terminal_floral_buds: RandomParameterInt = field(default_factory=lambda: RandomParameterInt.constant(0))

    # Boolean flags
    flowers_require_dormancy: bool = False
    growth_requires_dormancy: bool = False
    determinate_shoot_growth: bool = True

    # Optional child shoot type definition: {"labels": [...], "probabilities": [...]}.
    # Note: the native struct exposes no getter, so this round-trips on input only --
    # getCurrentShootParameters() will not populate it.
    child_shoot_types: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"phytomer_parameters": self.phytomer_parameters.to_dict()}
        for name, _ in _SHOOT_RPF_FIELDS:
            d[name] = getattr(self, name).to_dict()
        for name, _ in _SHOOT_RPI_FIELDS:
            d[name] = getattr(self, name).to_dict()
        for name, _ in _SHOOT_BOOL_FIELDS:
            d[name] = bool(getattr(self, name))
        if self.child_shoot_types is not None:
            d["child_shoot_types"] = self.child_shoot_types
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ShootParameters":
        kwargs: Dict[str, Any] = {}
        if "phytomer_parameters" in d:
            kwargs["phytomer_parameters"] = PhytomerParameters.from_dict(d["phytomer_parameters"])
        for name, default in _SHOOT_RPF_FIELDS:
            if name in d:
                kwargs[name] = RandomParameterFloat.from_dict(d[name])
        for name, default in _SHOOT_RPI_FIELDS:
            if name in d:
                kwargs[name] = RandomParameterInt.from_dict(d[name])
        for name, default in _SHOOT_BOOL_FIELDS:
            if name in d:
                kwargs[name] = bool(d[name])
        if "child_shoot_types" in d:
            kwargs["child_shoot_types"] = d["child_shoot_types"]
        return cls(**kwargs)

    def define_child_shoot_types(self, labels: List[str], probabilities: List[float]) -> None:
        """Set child shoot types; probabilities must sum to 1 (validated natively)."""
        if len(labels) != len(probabilities):
            raise ValueError("labels and probabilities must be the same length")
        if not labels:
            raise ValueError("labels and probabilities cannot be empty")
        self.child_shoot_types = {"labels": list(labels), "probabilities": [float(p) for p in probabilities]}


# --------------------------------------------------------------------------- #
# Flat physiology parameter structs
# --------------------------------------------------------------------------- #
def _flat_to_dict(obj: Any, names: Tuple[str, ...]) -> Dict[str, float]:
    return {n: float(getattr(obj, n)) for n in names}


def _flat_from_dict(cls: Any, d: Dict[str, Any], names: Tuple[str, ...]) -> Any:
    base = cls()
    kwargs = {n: float(d[n]) for n in names if n in d}
    for n in names:
        kwargs.setdefault(n, getattr(base, n))
    return cls(**kwargs)


_CARB_FIELDS = (
    "stem_density", "stem_carbon_percentage", "stem_carbohydrate_percentage",
    "stem_structural_carbon_percentage", "maturity_age", "initial_density_ratio",
    "shoot_root_ratio", "leaf_total_carbon_percentage", "SLA",
    "leaf_carbohydrate_percentage", "leaf_carbon_percentage", "total_flower_cost",
    "fruit_density", "fruit_carbon_percentage", "r_m_w_20", "r_m_r_20",
    "living_wood_fraction", "growth_respiration_fraction", "carbohydrate_abortion_threshold",
    "carbohydrate_pruning_threshold", "bud_death_threshold_days", "branch_death_threshold_days",
    "carbohydrate_phyllochron_threshold", "carbohydrate_vegetative_break_threshold",
    "carbohydrate_growth_threshold", "starch_sequestration_ratio",
    "carbohydrate_transfer_threshold_down", "carbohydrate_transfer_threshold_up",
    "carbon_conductance_down", "carbon_conductance_up",
)


@dataclass
class CarbohydrateParameters:
    """Flat carbohydrate-model parameters. Defaults mirror the Helios C++ defaults;
    prefer ``CarbohydrateParameters.from_dict(pa.getDefaultCarbohydrateParameters())``."""

    stem_density: float = 675000.0
    stem_carbon_percentage: float = 0.457
    stem_carbohydrate_percentage: float = 1 - (1 / 1.14)
    stem_structural_carbon_percentage: float = 0.457 - (1 - (1 / 1.14))
    maturity_age: float = 120.0
    initial_density_ratio: float = 0.25
    shoot_root_ratio: float = 3.0
    leaf_total_carbon_percentage: float = 0.453
    SLA: float = 9.2 / 10000 / 0.453 * 12.01
    leaf_carbohydrate_percentage: float = 1 - (1 / 1.13)
    leaf_carbon_percentage: float = 0.453
    total_flower_cost: float = 8.33e-4
    fruit_density: float = 525000.0
    fruit_carbon_percentage: float = 0.475
    r_m_w_20: float = 5.25164e-05
    r_m_r_20: float = 5.25164e-03
    living_wood_fraction: float = 0.5
    growth_respiration_fraction: float = 0.211
    carbohydrate_abortion_threshold: float = 0.1
    carbohydrate_pruning_threshold: float = 0.025
    bud_death_threshold_days: float = 2.0
    branch_death_threshold_days: float = 5.0
    carbohydrate_phyllochron_threshold: float = 0.05
    carbohydrate_vegetative_break_threshold: float = 0.05
    carbohydrate_growth_threshold: float = 0.2
    starch_sequestration_ratio: float = 0.025
    carbohydrate_transfer_threshold_down: float = 0.025
    carbohydrate_transfer_threshold_up: float = 0.04
    carbon_conductance_down: float = 0.95
    carbon_conductance_up: float = 0.95 * 0.5

    def to_dict(self) -> Dict[str, float]:
        return _flat_to_dict(self, _CARB_FIELDS)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CarbohydrateParameters":
        return _flat_from_dict(cls, d, _CARB_FIELDS)


_NITROGEN_FIELDS = (
    "target_leaf_N_area", "minimum_leaf_N_area", "root_allocation_fraction",
    "max_N_accumulation_rate", "leaf_remobilization_efficiency",
    "remobilization_age_threshold", "fruit_N_area",
)


@dataclass
class NitrogenParameters:
    """Flat nitrogen-model parameters. Prefer
    ``NitrogenParameters.from_dict(pa.getDefaultNitrogenParameters())``."""

    target_leaf_N_area: float = 1.5
    minimum_leaf_N_area: float = 0.5
    root_allocation_fraction: float = 0.15
    max_N_accumulation_rate: float = 0.1
    leaf_remobilization_efficiency: float = 0.70
    remobilization_age_threshold: float = 0.70
    fruit_N_area: float = 1.0

    def to_dict(self) -> Dict[str, float]:
        return _flat_to_dict(self, _NITROGEN_FIELDS)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "NitrogenParameters":
        return _flat_from_dict(cls, d, _NITROGEN_FIELDS)
