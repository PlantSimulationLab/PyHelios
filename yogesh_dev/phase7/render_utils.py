"""
Shared scene-build / camera-pose / render helpers for all of Phase 7's
experiments (T7.2-T7.7). Reuses Phase 0's validated rig-construction
utilities and Phase 0/1's validated pose convention rather than
re-deriving either.

Design note on why this isn't just Phase 0's `radiation_cameras.py`
`CAMERA_RIGS`: that module hard-codes exactly 3 fixed rig positions
(above/level/below) per tree. Every Phase 7 experiment needs cameras at
*arbitrary, swept* azimuth positions around one tree (D2's arc-width
sweep, D1's pose-conditioning views, D3/D4/D5/D6's multi-view sets) --
so this module adds an `arc_camera_poses` generator on top of the same
validated `look_at_view_matrix`/`intrinsics_matrix`/HFOV-from-VFOV math,
and a camera-pool registration pattern (register once, reposition many
times) to keep repeated sweeps cheap (`updateGeometry()` is genuinely
called only once per Context, per T0.4's finding).
"""

import math
import os

import numpy as np
import OpenEXR

from pyhelios import Context, PlantArchitecture, RadiationModel
from pyhelios.RadiationModel import CameraProperties
from pyhelios.types import vec3

from yogesh_dev.phase0.canopy import build_apple_tree
from yogesh_dev.phase0.pose_convention import hfov_from_vfov, intrinsics_matrix, look_at_view_matrix
from yogesh_dev.phase0.radiation_setup import setup_bands_and_lights
from yogesh_dev.phase1.label_maps import assign_semantic_class_ids, SEMANTIC_CLASSES, SEMANTIC_CLASS_ID_FIELD
from yogesh_dev.phase4.gen_dataset import extract_branch_segments

RESOLUTION = (480, 360)
VFOV_DEG = 45.0
AA_SAMPLES = 2
RGB_BANDS = ["red", "green", "blue"]

SCRATCH_DIR = os.path.join(os.path.dirname(__file__), "output", "_scratch")

SKY_DEPTH_SENTINEL = -1.0


def build_tree_scene(context, plantarch, age_days=365.0, position=None, build_parameters=None):
    """Build one apple tree (T1.1-style: object data enabled by the caller
    BEFORE this, if needed) and return (plant_id, position, all_uuids)."""
    if position is None:
        position = vec3(0.0, 0.0, 0.0)
    plant_id = build_apple_tree(plantarch, position=position, age_days=age_days,
                                 build_parameters=build_parameters)
    all_uuids = plantarch.getAllPlantUUIDs(plant_id)
    assign_semantic_class_ids(context, all_uuids)
    return plant_id, position, all_uuids


def tree_lookat_and_radius(context, uuids, position, margin=1.6, min_radius=1.0):
    """Bounding-box-derived look-at point (trunk mid-height) and a camera
    orbit radius sized so the whole tree stays in frame at VFOV_DEG,
    copying Phase 0's `camera_position_for_tree` sizing logic (same
    height/width-vs-FOV distance calculation, just parameterized for an
    arbitrary azimuth instead of the 3 fixed rig slots)."""
    x_bounds, y_bounds, z_bounds = context.getDomainBoundingBox(uuids)
    height = z_bounds.y - z_bounds.x
    width = max(x_bounds.y - x_bounds.x, y_bounds.y - y_bounds.x)
    half_fov_v = math.radians(VFOV_DEG) / 2.0
    dist_h = (height / 2.0) / math.tan(half_fov_v) * margin
    dist_w = (width / 2.0) / math.tan(half_fov_v) * margin
    radius = max(dist_h, dist_w, min_radius)
    lookat = vec3(position.x, position.y, z_bounds.x + 0.5 * height)
    return lookat, radius, height, width


def arc_camera_poses(lookat, radius, n_views, arc_width_deg, center_azimuth_deg=0.0, elevation_deg=10.0):
    """`n_views` camera (eye, lookat) poses evenly spaced across an arc of
    `arc_width_deg` degrees of azimuth, centered at `center_azimuth_deg`,
    on a circle of `radius` around `lookat` at a fixed elevation angle.

    Azimuth convention: 0 deg = camera on -Y looking toward +Y (matches
    Phase 0's rig convention, camera_position_for_tree), positive azimuth
    rotates toward +X. `n_views == 1` places a single camera at the arc
    center. `arc_width_deg == 360` with evenly spaced points would
    double-count the seam (0 and 360 are the same point) -- callers doing
    a full circle should request `n_views` points over `endpoint=False`
    spacing; see `full_circle_poses`.
    """
    if n_views == 1:
        azs_deg = np.array([center_azimuth_deg], dtype=float)
    else:
        half = arc_width_deg / 2.0
        azs_deg = np.linspace(center_azimuth_deg - half, center_azimuth_deg + half, n_views)
    elev = math.radians(elevation_deg)
    poses = []
    for az_deg in azs_deg:
        az = math.radians(az_deg)
        dx = radius * math.cos(elev) * math.sin(az)
        dy = -radius * math.cos(elev) * math.cos(az)
        dz = radius * math.sin(elev)
        eye = vec3(lookat.x + dx, lookat.y + dy, lookat.z + dz)
        poses.append((eye, lookat))
    return poses, list(azs_deg)


def full_circle_poses(lookat, radius, n_views, elevation_deg=10.0):
    """n_views evenly spaced around the FULL 360 deg circle, without
    double-counting the seam (endpoint excluded)."""
    azs_deg = np.linspace(0.0, 360.0, n_views, endpoint=False)
    elev = math.radians(elevation_deg)
    poses = []
    for az_deg in azs_deg:
        az = math.radians(az_deg)
        dx = radius * math.cos(elev) * math.sin(az)
        dy = -radius * math.cos(elev) * math.cos(az)
        dz = radius * math.sin(elev)
        eye = vec3(lookat.x + dx, lookat.y + dy, lookat.z + dz)
        poses.append((eye, lookat))
    return poses, list(azs_deg)


def build_camera_properties(resolution=RESOLUTION, vfov_deg=VFOV_DEG):
    width, height = resolution
    aspect = width / height
    hfov_deg = hfov_from_vfov(vfov_deg, aspect)
    cam_props = CameraProperties(
        camera_resolution=resolution,
        lens_diameter=0.0,
        HFOV=hfov_deg,
        FOV_aspect_ratio=0.0,
        exposure="manual",
    )
    return cam_props, hfov_deg


def register_camera_pool(radiation, n_cameras, resolution=RESOLUTION, vfov_deg=VFOV_DEG,
                          aa_samples=AA_SAMPLES, initial_eye=None, initial_lookat=None):
    """Register `n_cameras` cameras once, all at a placeholder pose.
    Returns (labels, hfov_deg). Reposition with setCameraPosition/
    setCameraLookat and call updateGeometry() only ONCE for the whole
    Context lifetime (T0.4) -- camera moves alone don't need it."""
    if initial_eye is None:
        initial_eye = vec3(0.0, -3.0, 1.0)
    if initial_lookat is None:
        initial_lookat = vec3(0.0, 0.0, 1.0)
    cam_props, hfov_deg = build_camera_properties(resolution, vfov_deg)
    labels = [f"cam{i}" for i in range(n_cameras)]
    for label in labels:
        radiation.addRadiationCamera(label, list(RGB_BANDS), initial_eye, initial_lookat,
                                      camera_properties=cam_props, antialiasing_samples=aa_samples)
    return labels, hfov_deg


def _read_depth_exr(filepath):
    f = OpenEXR.File(filepath)
    channels = f.channels()
    key = "Z" if "Z" in channels else next(iter(channels.keys()))
    return np.array(channels[key].pixels, dtype=np.float32)


def render_views(radiation, labels_used, poses, resolution=RESOLUTION,
                  want_rgb=False, want_depth=True, want_semantic=True, want_instance=False,
                  rgb_dir=None, view_names=None):
    """Move `labels_used` cameras to `poses`, render ONE runBand() call
    covering all of them, and pull back per-view arrays. Depth is
    necessarily a disk round-trip (writeDepthImageDataEXR is the only
    Python-reachable full-float-precision path, per Phase 1 T1.4) --
    uses a fixed per-camera scratch file under
    `yogesh_dev/phase7/output/_scratch/`, overwritten every call so
    sweeps don't accumulate thousands of files.

    Returns a list of dicts (same order as labels_used/poses), each with
    whatever of {eye, lookat, rgb, depth, semantic} was requested.
    """
    assert len(labels_used) == len(poses)
    for label, (eye, lookat) in zip(labels_used, poses):
        radiation.setCameraPosition(label, eye)
        radiation.setCameraLookat(label, lookat)

    radiation.runBand(list(RGB_BANDS))

    os.makedirs(SCRATCH_DIR, exist_ok=True)
    results = []
    for i, (label, (eye, lookat)) in enumerate(zip(labels_used, poses)):
        entry = {"eye": eye, "lookat": lookat, "camera_label": label}
        if want_rgb:
            out_dir = rgb_dir if rgb_dir is not None else SCRATCH_DIR
            name = view_names[i] if view_names else f"{label}_{i}"
            fname = radiation.writeCameraImage(
                camera=label, bands=list(RGB_BANDS), imagefile_base=name,
                image_path=out_dir + os.sep, flux_to_pixel_conversion=1.0,
            )
            entry["rgb_path"] = fname
        if want_depth:
            scratch_view = f"scratch{i}"
            radiation.writeDepthImageDataEXR(label, scratch_view, image_path=SCRATCH_DIR + os.sep)
            depth_path = os.path.join(SCRATCH_DIR, f"{label}_{scratch_view}.exr")
            entry["depth"] = _read_depth_exr(depth_path)
            os.remove(depth_path)
        if want_semantic:
            entry["semantic"] = radiation.getPrimitiveDataLabelMap(label, SEMANTIC_CLASS_ID_FIELD)
        if want_instance:
            entry["instance"] = radiation.getObjectDataLabelMap(label, "fruitID")
        results.append(entry)
    return results


def camera_matrices(hfov_deg, resolution, eye, lookat):
    """(K, world_to_camera 4x4) for one pose, reusing Phase 0's validated
    pose convention exactly."""
    width, height = resolution
    K = intrinsics_matrix(width, height, hfov_deg)
    viewmat = look_at_view_matrix(eye, lookat)
    return K, viewmat


def branch_skeleton_points(context, all_uuids, max_points=None, seed=0):
    """Real branch-skeleton 3D landmark points: every tube-segment
    midpoint from Phase 4's `extract_branch_segments` (shoot/peduncle
    tube nodes -- the fixed skeleton T7.4 sweeps LAI against). Returns a
    list of dicts: {point (3,), diameter_mm, label, object_id}.
    """
    segments, counts = extract_branch_segments(context, all_uuids)
    points = []
    for seg in segments:
        p0 = np.array(seg["p0"])
        p1 = np.array(seg["p1"])
        mid = 0.5 * (p0 + p1)
        points.append({
            "point": mid,
            "diameter_mm": seg["mid_diameter_mm"],
            "label": seg["label"],
            "object_id": seg["object_id"],
        })
    if max_points is not None and len(points) > max_points:
        rng = np.random.default_rng(seed)
        idx = rng.choice(len(points), size=max_points, replace=False)
        points = [points[i] for i in idx]
    return points, segments, counts


def fruit_landmark_points(context, plantarch, plant_ids):
    """Real fruit centroids (world 3D), reusing Phase 1's
    `export_fruit_ground_truth`-style query but without writing a file --
    just the (object_id, centroid, diameter) triples."""
    from yogesh_dev.phase1.ground_truth import build_uuid_to_plant_map, equivalent_diameter_from_surface_area
    uuid_to_plant = build_uuid_to_plant_map(plantarch, plant_ids)
    all_uuids = list(uuid_to_plant.keys())
    fruit_uuids = context.filterPrimitivesByData(all_uuids, "object_label", "fruit")
    fruit_uuid_set = set(fruit_uuids)
    fruit_objs = context.getUniquePrimitiveParentObjectIDs(fruit_uuids, include_zero=False)
    records = []
    for oid in fruit_objs:
        obj_uuids = context.getObjectPrimitiveUUIDs(oid)
        obj_fruit_uuids = [u for u in obj_uuids if u in fruit_uuid_set]
        if not obj_fruit_uuids:
            continue
        center = context.getObjectCenter(oid)
        surface_area = sum(context.getPrimitiveArea(u) for u in obj_fruit_uuids)
        diameter = equivalent_diameter_from_surface_area(surface_area)
        records.append({
            "object_id": oid,
            "point": np.array([center.x, center.y, center.z]),
            "diameter_m": diameter,
        })
    return records
