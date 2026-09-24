"""
Grow a calibrated tomato free-running from seed and measure every leaf, in plain Python.

This is a port of the simulate stage of a C++ tomato calibration program (PlantCloudFit):
the species setup, the rank-dependent phytomer creation function, the cotyledon node the
seedling is seated on, the node-by-node phyllotaxy, and the half-day time loop. It writes
the same per-leaf table the C++ program writes (``leaves.csv``), so the two can be compared
column by column, and it is a starting point for driving such a model from Python.

The bindings it depends on:
  - ``PlantArchitecture.setPhytomerCreationFunction`` -- a Python function run for every new
    phytomer, here scaling leaves and petioles by node rank;
  - ``setShootPhyllotacticAngle`` -- rewriting one shoot's next phyllotactic angle before
    each time step;
  - ``setInternodeMaxLength`` -- sizing the first internodes (hypocotyl, cotyledon node);
  - the per-phytomer readouts (``getInternodeNodePositions``, ``getPetioleAxisVector``,
    ``getPhytomerLeafObjectIDs``, ``getLeafBasePosition``, ...) used to measure the plant.

IMPORTANT: shoot types are defined here from parameter dicts, while the C++ program copies
C++ structs. Both consume draws from the Context random generator, but not the same number,
so the same seed does not grow the same plant draw for draw. With plant-to-plant variation
switched off, structure (which leaves exist on which day, and their leaflet counts) matches
the C++ program; organ sizes agree in distribution across seeds, not plant by plant.

Parameters are read from a whitespace-separated ``key value`` file (``#`` starts a comment),
the format of the C++ program's ``theta_fitted.txt``. The leaf texture is the C++ program's
blade crop, ``TomatoLeaf_blade.png``.

Run:
    python docs/examples/plantarch_tomato_calibrated_sample.py --theta theta.txt \\
        --texture path/to/TomatoLeaf_blade.png --out out_dir [--seed 1] [--replicates 1]

Compare with the C++ program's output directory (per track and day):
    python docs/examples/plantarch_tomato_calibrated_sample.py --compare cpp_out/leaves.csv out_dir/leaves.csv
or, for runs of several replicates, by medians over replicates:
    python docs/examples/plantarch_tomato_calibrated_sample.py --compare cpp_out/leaves.csv out_dir/leaves.csv --ensemble
"""

import argparse
import copy
import csv
import math
import os
import sys
from collections import defaultdict

import numpy as np

from pyhelios import Context, PlantArchitecture
from pyhelios.types import vec3
from pyhelios.wrappers.DataTypes import AxisRotation

SAMPLE_DAYS = [1, 3, 5, 7, 9, 11, 13, 15, 17, 20, 21]
DETECTION_TERMINAL_LENGTH = 0.0078  # m; a leaf is recorded once its terminal leaflet is this long
LEAF_COLUMNS = ["day", "scan", "track", "rank", "first_day", "on_main_stem", "synthesized_axis",
                "attachment_arclength_mm", "attachment_height_mm", "axis_length_mm", "leaflets", "area_cm2",
                "terminal_area_cm2", "terminal_length_mm", "insertion_azimuth_deg", "insertion_pitch_deg",
                "attach_x_mm", "attach_y_mm", "attach_z_mm"]
# Columns that do not depend on the plant's random base yaw.
COMPARED_COLUMNS = ["leaflets", "area_cm2", "terminal_area_cm2", "terminal_length_mm", "axis_length_mm",
                    "attachment_arclength_mm", "attachment_height_mm", "insertion_pitch_deg"]

f32 = np.float32


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

def read_theta(path):
    """Read ``key value`` lines into a dict, dropping ``#`` comments."""
    theta = {}
    with open(path) as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if line:
                key, value = line.split()
                theta[key] = float(value)
    return theta


def constant(value):
    return {"distribution": "constant", "parameters": [float(value)]}


def normal(mean, sd):
    return {"distribution": "normal", "parameters": [float(mean), float(sd)]}


def uniform(low, high):
    return {"distribution": "uniform", "parameters": [float(low), float(high)]}


def children(label):
    return {"labels": [label], "probabilities": [1.0]}


def distribution_mean(parameter, context):
    """The value a C++ ``RandomParameter::val()`` would return for an unsampled parameter, drawn from the Context."""
    kind, p = parameter["distribution"], parameter["parameters"]
    if kind == "constant":
        return p[0]
    if kind == "uniform":
        return context.randu(float(p[0]), float(p[1]))
    if kind == "normal":
        return context.randn(float(p[0]), float(p[1]))
    raise ValueError(f"Unsupported distribution '{kind}'")


# ---------------------------------------------------------------------------
# Species
# ---------------------------------------------------------------------------

class RankScaling:
    """The phytomer creation function: organs laid down on the first nodes stay smaller."""

    def __init__(self, plantarch, leaf_scale_node0, leaf_scale_nodes, internode_scale_late, internode_scale_age_days):
        self.plantarch = plantarch
        self.leaf_scale_node0 = f32(leaf_scale_node0)
        self.leaf_scale_nodes = f32(leaf_scale_nodes)
        self.internode_scale_late = f32(internode_scale_late)
        self.internode_scale_age_days = f32(internode_scale_age_days)

    def __call__(self, plant_id, shoot_id, node_index, shoot_node_index, parent_shoot_node_index, shoot_max_nodes,
                 plant_age):
        # Indexed by the plugin's shoot_node_index, which the main stem numbers from 1 (see the C++ model).
        index_from_first_leaf = f32(shoot_node_index - 1) if shoot_node_index >= 1 else f32(0)
        scale = self.leaf_scale_node0 + (f32(1) - self.leaf_scale_node0) * index_from_first_leaf / max(
            f32(0.1), self.leaf_scale_nodes)
        scale = float(min(max(scale, f32(0.1)), f32(1)))
        self.plantarch.scaleLeafPrototypeScale(plant_id, shoot_id, node_index, scale)
        self.plantarch.scalePetioleMaxLength(plant_id, shoot_id, node_index, scale)
        if self.internode_scale_late != f32(1):
            ramp = min(f32(1), f32(plant_age) / max(f32(0.1), self.internode_scale_age_days))
            internode_scale = min(max(f32(1) + (self.internode_scale_late - f32(1)) * ramp, f32(0.05)), f32(3))
            self.plantarch.scaleInternodeMaxLength(plant_id, shoot_id, node_index, float(internode_scale))


def setup_tomato_species(context, plantarch, growth, texture_file):
    """Define the grown, cotyledon and build shoot types from the library tomato; mirrors setupTomatoSpecies()."""
    plantarch.loadPlantModelFromLibrary("tomato")
    species = {"growth_type_label": "mainstem", "build_type_label": "measured_tomato", "cotyledon_type_label": ""}

    build = copy.deepcopy(plantarch.getCurrentShootParameters("mainstem"))
    library_internode_length_max = build["internode_length_max"]["parameters"][0]
    build["gravitropic_curvature"] = constant(0)
    build["tortuosity"] = constant(0)
    build["girth_area_factor"] = constant(0)
    build["max_nodes"] = constant(64)
    build["internode_length_max"] = constant(0.02)
    build["internode_length_min"] = constant(0.001)
    build["phytomer_parameters"]["internode"]["length_segments"] = 1
    build["phytomer_parameters"]["internode"]["pitch"] = constant(0)
    prototype = build["phytomer_parameters"]["leaf"]["prototype"]
    prototype["longitudinal_curvature"] = constant(-0.1)
    prototype["lateral_curvature"] = constant(-0.1)
    prototype["leaf_texture_file"] = {"0": texture_file}
    prototype["leaf_aspect_ratio"] = constant(0.523)
    prototype["midrib_fold_fraction"] = constant(0.1)
    prototype["wave_period"] = constant(0.35)
    prototype["wave_amplitude"] = constant(0.08)
    prototype["unique_prototypes"] = 1
    prototype["build_petiolule"] = True
    build["phytomer_parameters"]["leaf"]["leaves_per_petiole"] = constant(7)

    library = plantarch.getCurrentShootParameters("mainstem")
    build["phytomer_parameters"]["internode"]["pitch"] = copy.deepcopy(library["phytomer_parameters"]["internode"]["pitch"])
    grown = copy.deepcopy(library)
    grown["phytomer_parameters"]["leaf"]["prototype"] = copy.deepcopy(build["phytomer_parameters"]["leaf"]["prototype"])
    species["growth_internode_length_max"] = library_internode_length_max
    species["growth_internode_length_max_sd"] = 0.0

    ramp = {"leaf_scale_node0": 1.0, "leaf_scale_nodes": 2.0, "internode_scale_late": 1.0,
            "internode_scale_age_days": 10.0}
    phyllotactic_mean = phyllotactic_sd = -1.0
    petiole_pitch_mean = petiole_pitch_sd = -1.0
    leaf_pitch_mean, leaf_pitch_sd = 1e9, -1.0
    aspect_mean = aspect_sd = -1.0
    curvature_mean, curvature_sd = 1e9, -1.0
    unique_prototypes = -1
    flexibility = {"flexibility": -1.0, "flexibility_aging": -1.0, "flexibility_aging_max": -1.0, "flexibility_taper": -1.0}
    petiole_flexibility = {"flexibility": -1.0, "flexibility_aging": -1.0}
    cotyledon = {"prototype_scale": 0.0, "petiole_length": 0.002, "petiole_pitch": 60.0, "petioles": 2.0}

    both_fields = {
        "phyllochron_min": lambda p, v: p.__setitem__("phyllochron_min", constant(v)),
        "internode_length_max": lambda p, v: p.__setitem__("internode_length_max", constant(v)),
        "elongation_rate_max": lambda p, v: p.__setitem__("elongation_rate_max", constant(v)),
        "petiole_length": lambda p, v: p["phytomer_parameters"]["petiole"].__setitem__("length", constant(v)),
        "leaves_per_petiole": lambda p, v: p["phytomer_parameters"]["leaf"].__setitem__("leaves_per_petiole", constant(round(v))),
        "prototype_scale": lambda p, v: p["phytomer_parameters"]["leaf"].__setitem__("prototype_scale", constant(v)),
        "leaflet_scale": lambda p, v: p["phytomer_parameters"]["leaf"].__setitem__("leaflet_scale", constant(v)),
        "intercalary_leaflet_scale": lambda p, v: p["phytomer_parameters"]["leaf"].__setitem__("intercalary_leaflet_scale", constant(v)),
        "petiole_curvature": lambda p, v: p["phytomer_parameters"]["petiole"].__setitem__("curvature", constant(v)),
        "petiole_pitch": lambda p, v: p["phytomer_parameters"]["petiole"].__setitem__("pitch", constant(v)),
        "leaf_pitch": lambda p, v: p["phytomer_parameters"]["leaf"].__setitem__("pitch", constant(v)),
        "max_nodes": lambda p, v: p.__setitem__("max_nodes", constant(round(v))),
        "gravitropic_curvature": lambda p, v: p.__setitem__("gravitropic_curvature", constant(v)),
        "tortuosity": lambda p, v: p.__setitem__("tortuosity", constant(v)),
        "leaflet_offset": lambda p, v: p["phytomer_parameters"]["leaf"].__setitem__("leaflet_offset", constant(v)),
        "leaf_expansion_rate_max": lambda p, v: p.__setitem__("leaf_expansion_rate_max", constant(v)),
    }
    simulation_keys = {"base_tilt_deg", "base_tilt_sd", "cotyledon_internode_length", "phyllotactic_angle_node1",
                       "phyllotactic_angle_node2"}

    for key in sorted(growth):  # the C++ program iterates a std::map
        value = growth[key]
        if key == "petiole_pitch_sd":
            petiole_pitch_sd = value
        elif key == "leaf_pitch_sd":
            leaf_pitch_sd = value
        elif key == "leaf_aspect_ratio":
            aspect_mean = value
        elif key == "leaf_aspect_ratio_sd":
            aspect_sd = value
        elif key == "leaf_curvature":
            curvature_mean = value
        elif key == "leaf_curvature_sd":
            curvature_sd = value
        elif key == "unique_prototypes":
            unique_prototypes = int(round(value))
        elif key.startswith("leaf_flexibility"):
            flexibility[key[len("leaf_"):]] = value
        elif key.startswith("petiole_flexibility"):
            petiole_flexibility[key[len("petiole_"):]] = value
        elif key in both_fields:
            for parameters in (build, grown):
                both_fields[key](parameters, value)
            if key == "petiole_pitch":
                petiole_pitch_mean = value
            elif key == "leaf_pitch":
                leaf_pitch_mean = value
            elif key == "internode_length_max":
                species["growth_internode_length_max"] = value
        elif key == "phyllotactic_angle_mean":
            phyllotactic_mean = value
        elif key == "phyllotactic_angle_sd":
            phyllotactic_sd = value
        elif key == "internode_length_max_sd":
            species["growth_internode_length_max_sd"] = value
        elif key == "phyllochron_sd":
            grown["phyllochron_min"] = normal(grown["phyllochron_min"]["parameters"][0], value)
        elif key in ramp:
            ramp[key] = value
        elif key == "petiole_length_segments":
            grown["phytomer_parameters"]["petiole"]["length_segments"] = int(round(value))
        elif key.startswith("cotyledon_") and key != "cotyledon_internode_length":
            cotyledon[key[len("cotyledon_"):]] = value
        elif key == "girth_area_factor":
            grown["girth_area_factor"] = constant(value)
        elif key == "internode_radius_initial":
            grown["phytomer_parameters"]["internode"]["radius_initial"] = constant(value)
        elif key == "petiole_radius":
            grown["phytomer_parameters"]["petiole"]["radius"] = constant(value)
        elif key not in simulation_keys:
            raise ValueError(f"Unrecognized growth parameter '{key}'")

    if phyllotactic_mean >= 0:
        spread = max(phyllotactic_sd, 0.0)
        for parameters in (build, grown):
            parameters["phytomer_parameters"]["internode"]["phyllotactic_angle"] = (
                normal(phyllotactic_mean, spread) if spread > 0 else constant(phyllotactic_mean))
    elif phyllotactic_sd >= 0:
        raise ValueError("'phyllotactic_angle_sd' was given without 'phyllotactic_angle_mean'")

    grown_phytomer = grown["phytomer_parameters"]
    if petiole_pitch_sd > 0:
        mean = petiole_pitch_mean if petiole_pitch_mean >= 0 else distribution_mean(grown_phytomer["petiole"]["pitch"], context)
        half_width = math.sqrt(3.0) * petiole_pitch_sd
        grown_phytomer["petiole"]["pitch"] = uniform(max(5.0, mean - half_width), min(90.0, mean + half_width))
    if leaf_pitch_sd > 0:
        mean = leaf_pitch_mean if leaf_pitch_mean < 1e8 else distribution_mean(grown_phytomer["leaf"]["pitch"], context)
        grown_phytomer["leaf"]["pitch"] = normal(mean, leaf_pitch_sd)
    grown_prototype = grown_phytomer["leaf"]["prototype"]
    if aspect_mean > 0:
        grown_prototype["leaf_aspect_ratio"] = normal(aspect_mean, aspect_sd) if aspect_sd > 0 else constant(aspect_mean)
    if curvature_mean < 1e8:
        shape = normal(curvature_mean, curvature_sd) if curvature_sd > 0 else constant(curvature_mean)
        grown_prototype["longitudinal_curvature"] = copy.deepcopy(shape)
        grown_prototype["lateral_curvature"] = copy.deepcopy(shape)
    for field, value in flexibility.items():
        if value >= 0:
            grown_prototype[field] = constant(value)
    for field, value in petiole_flexibility.items():
        if value >= 0:
            grown_phytomer["petiole"][field] = constant(value)
    if unique_prototypes > 0:
        grown_prototype["unique_prototypes"] = unique_prototypes

    build["internode_length_max"] = constant(species["growth_internode_length_max"])
    species["growth_type_label"] = "grown_tomato"
    grown["child_shoot_types"] = children("grown_tomato")
    plantarch.defineShootType("grown_tomato", grown)
    # A new label defined from a dict has no creation function, so the library's age-based one is already gone.
    if ramp["leaf_scale_node0"] != 1.0 or ramp["internode_scale_late"] != 1.0:
        species["creation_function"] = RankScaling(plantarch, **ramp)
        plantarch.setPhytomerCreationFunction("grown_tomato", species["creation_function"])

    if cotyledon["prototype_scale"] > 0:
        cot = copy.deepcopy(grown)
        phytomer = cot["phytomer_parameters"]
        phytomer["internode"]["pitch"] = constant(0)
        phytomer["internode"]["max_floral_buds_per_petiole"] = constant(0)
        phytomer["internode"]["max_vegetative_buds_per_petiole"] = constant(1)
        phytomer["petiole"]["petioles_per_internode"] = int(round(cotyledon["petioles"]))
        phytomer["petiole"]["length"] = constant(cotyledon["petiole_length"])
        phytomer["petiole"]["pitch"] = constant(cotyledon["petiole_pitch"])
        phytomer["petiole"]["flexibility"] = constant(0)
        phytomer["leaf"]["leaves_per_petiole"] = constant(1)
        phytomer["leaf"]["leaflet_offset"] = constant(0)
        phytomer["leaf"]["prototype_scale"] = constant(cotyledon["prototype_scale"])
        cot["max_nodes"] = constant(1)
        cot["vegetative_bud_break_probability_min"] = constant(1)
        cot["flower_bud_break_probability"] = constant(0)
        cot["child_shoot_types"] = children("grown_tomato")
        species["cotyledon_type_label"] = "cotyledon_tomato"
        plantarch.defineShootType("cotyledon_tomato", cot)

    build["child_shoot_types"] = children(species["growth_type_label"])
    plantarch.defineShootType("measured_tomato", build)
    return species


# ---------------------------------------------------------------------------
# Seeding and growing
# ---------------------------------------------------------------------------

def seed_plant(plantarch, plant_id, species, internode_length_max, hypocotyl_length, cotyledon_internode_length,
               base_rotation):
    """Place the cotyledon node and the main stem on it; returns the main stem's shoot ID."""
    if not species["cotyledon_type_label"]:
        main_stem = plantarch.addBaseStemShoot(plant_id, 1, base_rotation, 0.001, internode_length_max, 0.01, 0.01,
                                               0.0, species["growth_type_label"])
        if hypocotyl_length > 0:
            plantarch.setInternodeMaxLength(plant_id, 0, 0, hypocotyl_length)
        return main_stem
    cotyledon_shoot = plantarch.addBaseStemShoot(plant_id, 1, base_rotation, 0.001, max(1e-4, hypocotyl_length), 1.0,
                                                 1.0, 0.0, species["cotyledon_type_label"])
    main_stem = plantarch.appendShoot(plant_id, cotyledon_shoot, 1, AxisRotation(0, 0, 0.5 * math.pi), 0.001,
                                      internode_length_max, 0.01, 0.01, 0.0, species["growth_type_label"])
    if plantarch.getShoot(plant_id, main_stem)["node_count"] > 0 and cotyledon_internode_length > 0:
        plantarch.setInternodeMaxLength(plant_id, main_stem, 0, cotyledon_internode_length)
    return main_stem


def simulate(theta, texture_file, seed=1, days=SAMPLE_DAYS, replicate=0):
    """Grow one plant; yields (day, scan, rows) after each sampled day, where rows follow LEAF_COLUMNS."""
    growth = {k: v for k, v in theta.items()
              if k not in ("hypocotyl_length", "emergence_offset_days", "emergence_offset_days_sd")}
    hypocotyl_length = theta.get("hypocotyl_length", 0.0)
    emergence_offset = theta.get("emergence_offset_days", 0.0)
    for key in ("internode_length_max_sd", "emergence_offset_days_sd", "base_tilt_sd"):
        if theta.get(key, 0.0) > 0:
            raise ValueError(f"This port grows plants without plant-to-plant variation; set {key} to 0")
    steady_angle = theta.get("phyllotactic_angle_mean", 137.5)
    spread = theta.get("phyllotactic_angle_sd", 0.0)
    sequence = [theta.get("phyllotactic_angle_node1", steady_angle), theta.get("phyllotactic_angle_node2", steady_angle)]
    tilt = math.radians(max(0.0, theta.get("base_tilt_deg", 0.0)))

    context = Context()
    context.seedRandomGenerator(seed + replicate)
    plantarch = PlantArchitecture(context)
    plantarch.disableMessages()
    species = setup_tomato_species(context, plantarch, growth, texture_file)

    plant_id = plantarch.addPlantInstance(vec3(0, 0, 0), 0.0)
    main_stem = seed_plant(plantarch, plant_id, species, species["growth_internode_length_max"], hypocotyl_length,
                           theta.get("cotyledon_internode_length", 0.0), AxisRotation(tilt, 0.0, 0.0))
    plantarch.breakPlantDormancy(plant_id)

    # float32 day arithmetic, as in the C++ program, so the step sizes match.
    germination_day = f32(1) - f32(emergence_offset)
    simulated_day = germination_day
    plant_code = f"S{replicate + 1:02d}"
    for day in sorted(days):
        if f32(day) < germination_day:
            continue
        while f32(day) - simulated_day > f32(1e-4):
            step = min(f32(0.5), f32(day) - simulated_day)
            next_node = plantarch.getShoot(plant_id, main_stem)["node_count"]
            angle = sequence[next_node - 1] if 1 <= next_node <= len(sequence) else steady_angle
            plantarch.setShootPhyllotacticAngle(plant_id, main_stem, angle, spread)
            plantarch.advanceTime(float(step), plant_id=plant_id)
            simulated_day = f32(simulated_day + step)
        scan = f"{plant_code}_d{day:02d}"
        yield day, scan, record_plant(context, plantarch, plant_id, day, scan, main_stem)


# ---------------------------------------------------------------------------
# Measuring
# ---------------------------------------------------------------------------

def _unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 0 else np.zeros(3)


def blade_uuids(context, obj_id):
    uuids = context.getObjectPrimitiveUUIDs(obj_id)
    blade = [u for u in uuids
             if context.doesPrimitiveDataExist(u, "object_label") and context.getPrimitiveData(u, "object_label", str) == "leaf"]
    return blade if blade else uuids


def blade_area(context, obj_id):
    return float(sum(context.getPrimitiveArea(u) for u in blade_uuids(context, obj_id)))


def blade_orientation(context, obj_id):
    """Midrib (object x axis projected into the blade plane) and upward area-weighted normal."""
    transform = context.getObjectTransformationMatrix(obj_id)
    midrib = np.array([transform[0, 0], transform[1, 0], transform[2, 0]], dtype=float)
    normal_sum = np.zeros(3)
    for u in blade_uuids(context, obj_id):
        n = np.array(context.getPrimitiveNormal(u).to_list(), dtype=float)
        if n[2] < 0:
            n = -n
        normal_sum += context.getPrimitiveArea(u) * n
    if np.linalg.norm(midrib) < 1e-9 or np.linalg.norm(normal_sum) < 1e-12:
        raise RuntimeError(f"Leaf object {obj_id} has degenerate geometry")
    normal = _unit(normal_sum)
    midrib = midrib - np.dot(midrib, normal) * normal
    if np.linalg.norm(midrib) < 1e-9:
        raise RuntimeError(f"Leaf object {obj_id} has its length axis along its normal")
    return _unit(midrib), normal


def blade_extent(context, obj_id, midrib, normal):
    across = _unit(np.cross(normal, midrib))
    vertices = np.array([v.to_list() for u in blade_uuids(context, obj_id) for v in context.getPrimitiveVertices(u)])
    along = vertices @ midrib
    sideways = vertices @ across
    return float(along.max() - along.min()), float(sideways.max() - sideways.min())


def insertion_angles(stem_axis, petiole_direction):
    stem_axis, petiole_direction = _unit(stem_axis), _unit(petiole_direction)
    if not stem_axis.any() or not petiole_direction.any():
        return float("nan"), float("nan")
    reference = _unit(np.array([1.0, 0, 0]) - stem_axis * stem_axis[0])
    if not reference.any():
        reference = _unit(np.array([0, 1.0, 0]) - stem_axis * stem_axis[1])
    reference_perp = np.cross(stem_axis, reference)
    azimuth = math.degrees(math.atan2(np.dot(petiole_direction, reference_perp), np.dot(petiole_direction, reference)))
    if azimuth < 0:
        azimuth += 360.0
    pitch = math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(petiole_direction, stem_axis))))))
    return azimuth, pitch


def record_plant(context, plantarch, plant_id, day, scan, main_stem):
    """One row per detected leaf, in the C++ program's leaves.csv schema; mirrors recordPlant()."""
    rows = []
    for _, shoot_ids in sorted(plantarch.getShootIDsByRank(plant_id).items()):
        for shoot_id in shoot_ids:
            on_main_stem = shoot_id in (0, main_stem)
            offset = 0.0
            if shoot_id == main_stem and main_stem != 0:
                offset = sum(plantarch.getInternodeLength(plant_id, 0, n)
                             for n in range(plantarch.getShoot(plant_id, 0)["node_count"]))
            stem_arclength = 0.0
            for node in range(plantarch.getShoot(plant_id, shoot_id)["node_count"]):
                stem_arclength += plantarch.getInternodeLength(plant_id, shoot_id, node)
                arclength_from_base = offset + stem_arclength
                nodes = [np.array(v.to_list()) for v in plantarch.getInternodeNodePositions(plant_id, shoot_id, node)]
                if not nodes:
                    continue
                attachment = nodes[-1]
                leaf_ids = plantarch.getPhytomerLeafObjectIDs(plant_id, shoot_id, node)
                for petiole, leaflets in enumerate(leaf_ids):
                    if not leaflets:
                        continue
                    terminal_index = (len(leaflets) - 1) // 2
                    total_area = sum(blade_area(context, o) for o in leaflets if context.doesObjectExist(o))
                    if total_area <= 0:
                        continue
                    terminal = leaflets[terminal_index]
                    if not context.doesObjectExist(terminal):
                        continue
                    midrib, normal = blade_orientation(context, terminal)
                    terminal_length, _ = blade_extent(context, terminal, midrib, normal)
                    if terminal_length < DETECTION_TERMINAL_LENGTH:
                        continue
                    chord = nodes[-1] - nodes[0]
                    stem_axis = chord if np.linalg.norm(chord) > 0 else np.array(
                        plantarch.getInternodeAxisVector(plant_id, shoot_id, node, 1.0).to_list())
                    petiole_axis = np.array(plantarch.getPetioleAxisVector(plant_id, shoot_id, node, 0.0, petiole).to_list())
                    azimuth, pitch = insertion_angles(stem_axis, petiole_axis)
                    track = shoot_id * 100 + node * 2 + petiole
                    first_day = day - int(math.floor(plantarch.getPhytomerAge(plant_id, shoot_id, node) + 0.5))  # std::lround
                    terminal_area = blade_area(context, terminal)
                    rows.append([day, scan, track, track, first_day, int(on_main_stem), 0,
                                 f"{1000 * arclength_from_base:.2f}", f"{1000 * attachment[2]:.2f}",
                                 f"{1000 * plantarch.getPetioleLength(plant_id, shoot_id, node):.2f}", len(leaflets),
                                 f"{1e4 * total_area:.3f}", f"{1e4 * terminal_area:.3f}", f"{1000 * terminal_length:.2f}",
                                 f"{azimuth:.1f}", f"{pitch:.1f}", f"{1000 * attachment[0]:.2f}",
                                 f"{1000 * attachment[1]:.2f}", f"{1000 * attachment[2]:.2f}"])
    return rows


# ---------------------------------------------------------------------------
# Comparing
# ---------------------------------------------------------------------------

def read_leaves(path):
    """leaves.csv as {(scan_replicate, day, track): row dict}."""
    with open(path) as f:
        return {(r["scan"].split("_")[0], int(r["day"]), int(r["track"])): r for r in csv.DictReader(f)}


def compare(reference_path, candidate_path, out=sys.stdout):
    """Per-track, per-day comparison of the yaw-independent columns. Returns True if every value is equal."""
    reference, candidate = read_leaves(reference_path), read_leaves(candidate_path)
    missing = sorted(set(reference) - set(candidate))
    extra = sorted(set(candidate) - set(reference))
    common = sorted(set(reference) & set(candidate))
    print(f"leaves: {len(reference)} reference, {len(candidate)} candidate, {len(common)} in both", file=out)
    if missing:
        print(f"  only in reference: {missing}", file=out)
    if extra:
        print(f"  only in candidate: {extra}", file=out)
    exact = not missing and not extra
    for column in COMPARED_COLUMNS:
        diffs = [abs(float(candidate[k][column]) - float(reference[k][column])) for k in common]
        unequal = sum(candidate[k][column] != reference[k][column] for k in common)
        exact &= unequal == 0
        print(f"  {column:26s} unequal {unequal:3d}/{len(common)}  max |diff| {max(diffs, default=0):.4g}  "
              f"median |diff| {float(np.median(diffs)) if diffs else 0:.4g}", file=out)
    return exact


ENSEMBLE_COLUMNS = ["area_cm2", "axis_length_mm", "attachment_height_mm"]


def compare_ensemble(reference_path, candidate_path, out=sys.stdout):
    """Compare two multi-replicate leaves.csv files by per-(day, track) medians over replicates.

    A median counts as agreeing when the two differ by no more than the larger of the two sides'
    seed-to-seed standard deviations. Returns True if leaf presence and leaflet counts agree on
    every (day, track) and every median agrees.
    """
    def group(path):
        values = defaultdict(lambda: defaultdict(list))
        with open(path) as f:
            for r in csv.DictReader(f):
                key = (int(r["day"]), int(r["track"]))
                values[key]["present"].append(r["scan"].split("_")[0])
                values[key]["leaflets"].append(int(r["leaflets"]))
                for column in ENSEMBLE_COLUMNS:
                    values[key][column].append(float(r[column]))
        return values

    reference, candidate = group(reference_path), group(candidate_path)
    keys = sorted(set(reference) | set(candidate))
    ok = True
    presence_mismatch = [(k, len(reference[k]["present"]), len(candidate[k]["present"])) for k in keys
                         if len(reference[k]["present"]) != len(candidate[k]["present"])]
    leaflet_mismatch = [k for k in keys if reference[k]["leaflets"] and candidate[k]["leaflets"]
                        and sorted(set(reference[k]["leaflets"])) != sorted(set(candidate[k]["leaflets"]))]
    print(f"(day, track) groups: {len(keys)}; replicate counts differ on {len(presence_mismatch)}, "
          f"leaflet counts differ on {len(leaflet_mismatch)}", file=out)
    for k, n_ref, n_cand in presence_mismatch:
        print(f"  day {k[0]} track {k[1]}: {n_ref} reference replicates vs {n_cand} candidate", file=out)
    ok &= not presence_mismatch and not leaflet_mismatch
    for column in ENSEMBLE_COLUMNS:
        within, total, worst = 0, 0, 0.0
        for k in keys:
            a, b = reference[k][column], candidate[k][column]
            if len(a) < 2 or len(b) < 2:
                continue
            spread = max(float(np.std(a, ddof=1)), float(np.std(b, ddof=1)), 1e-9)
            z = abs(float(np.median(a)) - float(np.median(b))) / spread
            within += z <= 1.0
            total += 1
            worst = max(worst, z)
        ok &= within == total
        print(f"  {column:22s} medians within one seed-to-seed sd: {within}/{total}  "
              f"(worst |diff|/sd {worst:.2f})", file=out)
    return ok


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--theta", help="key/value parameter file")
    parser.add_argument("--texture", help="leaf blade texture (TomatoLeaf_blade.png)")
    parser.add_argument("--out", help="output directory for leaves.csv")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--replicates", type=int, default=1)
    parser.add_argument("--compare", nargs=2, metavar=("REFERENCE", "CANDIDATE"), help="compare two leaves.csv files")
    parser.add_argument("--ensemble", action="store_true",
                        help="with --compare: compare per-(day, track) medians over replicates instead of values")
    args = parser.parse_args()

    if args.compare:
        sys.exit(0 if (compare_ensemble if args.ensemble else compare)(*args.compare) else 1)
    if not (args.theta and args.texture and args.out):
        parser.error("--theta, --texture and --out are required unless --compare is given")
    if not os.path.isfile(args.texture):
        parser.error(f"leaf texture '{args.texture}' does not exist")

    theta = read_theta(args.theta)
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "leaves.csv"), "w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(LEAF_COLUMNS)
        for replicate in range(args.replicates):
            for day, scan, rows in simulate(theta, os.path.abspath(args.texture), args.seed, replicate=replicate):
                writer.writerows(rows)
            print(f"  S{replicate + 1:02d}: grown to day {max(SAMPLE_DAYS)}")
    print(f"  wrote {os.path.join(args.out, 'leaves.csv')}")


if __name__ == "__main__":
    main()
