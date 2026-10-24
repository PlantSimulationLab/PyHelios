"""
Shared scene setup + render/cache/scoring helpers for Phase 5 (T5.1-T5.8).

Builds ONE fresh 3-apple-tree scene (same real Phase 0/1/2 radiation-camera
rig, ground-truth export, and per-primitive visibility machinery those
phases already validated), renders + caches every candidate pose's real
per-primitive visibility ONCE, then every baseline in t5*.py scores its own
view sequence purely from that cached data. This is what makes all eight
baselines' numbers directly comparable: same scene, same fruit, same
primitive ids, same render settings -- only the view-selection POLICY
differs between baselines.

Per the task brief, V_reach for T5.4/T5.6/T5.7/T5.8 is Phase 2's
PLACEHOLDER_reachable_poses, used directly (not re-derived from Phase 3's
kinematics roadmap). Phase 3's real T3.3 execution-time model IS reused,
but arm-agnostically: a pose's (x, y, z, pan, tilt) joint coordinates are
derived directly from its (eye, lookat) via the same closed-form math
`kinematics.inverse_kinematics` uses, WITHOUT binding the pose to one of
Phase 3's three placeholder ArmConfigs (whose z-bands/pan/tilt limits were
sized against a different independently-chosen envelope than Phase 2's
reachable-pose grid -- forcing every reachable-grid pose through those
limits would silently drop most of V_reach). This is a real, documented
integration gap between Phase 2 and Phase 3's independently-developed
placeholders, not swept under the rug -- see PHASE5_LOG.md.
"""

import math
import os
import time

from pyhelios import Context, PlantArchitecture, RadiationModel
from pyhelios.types import vec3

from yogesh_dev.phase0.canopy import build_three_tree_scene
from yogesh_dev.phase0.radiation_setup import setup_bands_and_lights
from yogesh_dev.phase0.radiation_cameras import (
    build_camera_properties, camera_position_for_tree, compute_tree_poses,
    RGB_BAND_LABELS, CAMERA_RIGS,
)
from yogesh_dev.phase1.ground_truth import enable_fruit_object_data, export_fruit_ground_truth

from yogesh_dev.phase2.visibility import (
    assign_vis_primitive_ids, render_poses_batched, union_visible_ids, fruit_visible_fraction,
)
from yogesh_dev.phase2.reachable_poses import placeholder_reachable_poses

from yogesh_dev.phase3.kinematics import JointState
from yogesh_dev.phase3.motion_time import move_time

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

RESOLUTION = (320, 240)
ANTIALIASING_SAMPLES = 1
VFOV_DEG = 45.0
CAMERA_LABELS = ["camA", "camB", "camC"]
SEED = 20260729  # same seed Phase 2 used, for a directly-comparable fresh run

# Same V_reach density Phase 2 settled on (108 poses/tree, ~10 min sweep budget).
REACHABLE_GRID = dict(n_rail=6, n_height=6, n_depth=3)


def build_scene(seed=SEED):
    """Build the live pyhelios scene + everything every T5.x baseline needs.
    Returns a dict of live handles; caller is responsible for closing the
    Context/PlantArchitecture/RadiationModel context managers it opens
    (see run_phase5.py for the exact `with` nesting)."""
    context = Context()
    context.__enter__()
    context.seedRandomGenerator(seed)

    plantarch = PlantArchitecture(context)
    plantarch.__enter__()
    enable_fruit_object_data(plantarch)

    t0 = time.time()
    plant_ids, positions = build_three_tree_scene(context, plantarch)
    build_time_s = time.time() - t0

    all_uuids = []
    for pid in plant_ids:
        all_uuids.extend(plantarch.getAllPlantUUIDs(pid))

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    fruit_gt_path = os.path.join(OUTPUT_DIR, "phase5_fruit_ground_truth.json")
    fruit_records, gt_report = export_fruit_ground_truth(context, plantarch, plant_ids, fruit_gt_path)

    fruit_records_by_plant = {}
    for rec in fruit_records:
        fruit_records_by_plant.setdefault(rec["plant_id"], []).append(rec)

    prim_id_to_info, fruit_prim_ids = assign_vis_primitive_ids(context, all_uuids, fruit_records)

    return {
        "context": context, "plantarch": plantarch, "seed": seed,
        "plant_ids": plant_ids, "positions": positions,
        "fruit_records": fruit_records, "fruit_records_by_plant": fruit_records_by_plant,
        "gt_report": gt_report, "build_time_s": build_time_s,
        "prim_id_to_info": prim_id_to_info, "fruit_prim_ids": fruit_prim_ids,
        "n_fruit_surface_primitives": len(prim_id_to_info),
    }


def open_radiation(scene):
    context = scene["context"]
    radiation = RadiationModel(context)
    radiation.__enter__()
    setup_bands_and_lights(radiation)
    cam_props, hfov_deg = build_camera_properties(RESOLUTION, VFOV_DEG)
    aspect = RESOLUTION[0] / RESOLUTION[1]
    init_eye, init_lookat = camera_position_for_tree(
        scene["context"], scene["plantarch"], scene["plant_ids"][0], scene["positions"][0],
        {"height_frac": 0.5}, aspect)
    for label in CAMERA_LABELS:
        radiation.addRadiationCamera(label, RGB_BAND_LABELS, init_eye, init_lookat,
                                      camera_properties=cam_props,
                                      antialiasing_samples=ANTIALIASING_SAMPLES)
    radiation.updateGeometry()  # ONCE -- T0.4
    return radiation, hfov_deg


def render_and_cache_reachable(radiation, scene):
    """Render Phase 2's PLACEHOLDER_reachable_poses grid for every tree,
    ONCE, and return a flat global candidate list (across all 3 trees) of
    {'tree_id', 'pose': (eye, lookat), 'visible_ids': set(...)} -- this flat
    list IS V_reach for T5.4/T5.6/T5.7/T5.8."""
    context, plantarch = scene["context"], scene["plantarch"]
    candidates = []
    per_tree_timing = {}
    aspect = RESOLUTION[0] / RESOLUTION[1]
    for plant_id, base_position in zip(scene["plant_ids"], scene["positions"]):
        poses = placeholder_reachable_poses(
            context, plantarch, plant_id, base_position,
            vfov_deg=VFOV_DEG, aspect_ratio=aspect, **REACHABLE_GRID)
        t0 = time.time()
        results = render_poses_batched(radiation, CAMERA_LABELS, poses, RGB_BAND_LABELS)
        dt = time.time() - t0
        per_tree_timing[plant_id] = {"n_poses": len(poses), "render_s": dt}
        for pose, (visible_ids, _pixel_counts) in zip(poses, results):
            candidates.append({"tree_id": plant_id, "pose": pose, "visible_ids": visible_ids})
    return candidates, per_tree_timing


def render_static_rig_and_single_fixed(radiation, scene):
    """T5.2's static 3-camera rig (Phase 0's original above/level/below
    positions, one set per tree -- 9 poses total, NO arm motion between
    them) and T5.1's single fixed camera (the 'level' rig pose on the
    middle tree, the natural single-camera choice for a row of 3 trees)."""
    tree_poses = compute_tree_poses(scene["context"], scene["plantarch"],
                                     scene["plant_ids"], scene["positions"], resolution=RESOLUTION)
    flat_poses = [pose for poses in tree_poses for pose in poses]  # 9 poses, CAMERA_RIGS order per tree
    results = render_poses_batched(radiation, CAMERA_LABELS, flat_poses, RGB_BAND_LABELS)
    static_rig = [{"pose": pose, "visible_ids": vis} for pose, (vis, _pc) in zip(flat_poses, results)]

    mid = len(scene["plant_ids"]) // 2
    level_idx = [rig["name"] for rig in CAMERA_RIGS].index("level")
    single_fixed = static_rig[mid * len(CAMERA_RIGS) + level_idx]
    return static_rig, single_fixed


def coverage_summary(final_visible_ids, fruit_records, fruit_prim_ids, prim_id_to_info):
    """Mean area-weighted visible fraction across ALL fruit (all 3 trees)
    achieved by the union `final_visible_ids` of whatever view sequence a
    baseline actually used. Same metric Phase 2 calls AVUB when the input
    is the full V_reach; here it's evaluated on a baseline's own (usually
    much smaller) chosen view set."""
    fracs = []
    for rec in fruit_records:
        frac, _area = fruit_visible_fraction(
            final_visible_ids, fruit_prim_ids, prim_id_to_info,
            rec["object_id"], rec["surface_area_m2"])
        fracs.append(frac)
    n = len(fracs)
    n_observed = sum(1 for f in fracs if f > 0)
    return {
        "n_fruit": n,
        "mean_coverage_frac": (sum(fracs) / n) if n else 0.0,
        "n_fruit_observed_at_all": n_observed,
        "fraction_fruit_observed": (n_observed / n) if n else 0.0,
    }


def union_of(visible_id_sets):
    union = set()
    for s in visible_id_sets:
        union |= s
    return union


def pose_to_joint_state(pose):
    """Direct (x, y, z, pan_deg, tilt_deg) from a raw (eye, lookat) pose,
    using the exact same closed-form direction math as Phase 3's
    `kinematics.inverse_kinematics`, but WITHOUT binding to one of Phase 3's
    three placeholder ArmConfigs (see module docstring: Phase 2's reachable
    grid and Phase 3's arm-limit placeholders were sized independently)."""
    eye, lookat = pose
    px, py, pz = eye.x, eye.y, eye.z
    lx, ly, lz = lookat.x, lookat.y, lookat.z
    dx, dy, dz = lx - px, ly - py, lz - pz
    norm = math.sqrt(dx * dx + dy * dy + dz * dz)
    if norm < 1e-12:
        return JointState(x=px, y=py, z=pz, pan_deg=0.0, tilt_deg=0.0)
    dx, dy, dz = dx / norm, dy / norm, dz / norm
    tilt = math.asin(max(-1.0, min(1.0, dz)))
    pan = math.atan2(dx, dy)
    return JointState(x=px, y=py, z=pz, pan_deg=math.degrees(pan), tilt_deg=math.degrees(tilt))


def sequence_motion_time_s(poses):
    """Total real T3.3 execution time (seconds) to visit `poses` in the
    given order, via Phase 3's real trapezoidal-profile `move_time` between
    each consecutive pair's derived joint coordinates."""
    if len(poses) < 2:
        return 0.0
    total = 0.0
    prev = pose_to_joint_state(poses[0])
    for p in poses[1:]:
        cur = pose_to_joint_state(p)
        total += move_time(prev, cur)
        prev = cur
    return total


def euclidean(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2)
