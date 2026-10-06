"""
T0.2 -- Define the 3-camera rig as RadiationCameras (replaces the
Visualizer-only `CAMERA_RIGS` dict in apple_tree_cameras.py for the Tier-C
physically-based path).

T0.4 -- Correct render loop structure: `updateGeometry()` once outside the
pose loop, one `runBand()` call per pose covering all bands together.

Camera parameter choices (see task doc T0.2 table):
    lens_diameter=0.0        -- pinhole; default 0.05 enables thin-lens DoF
                                 blur, which corrupts geometric experiments.
    HFOV                     -- CameraProperties takes HORIZONTAL FOV; the
                                 existing apple_tree_cameras.py CAMERA_FOV_DEG
                                 is VERTICAL. Converted via
                                 HFOV = 2*atan(aspect * tan(VFOV/2)).
    FOV_aspect_ratio=0.0      -- auto-computes vertical FOV from resolution.
    camera_resolution         -- (640, 480) default; see T0.5 for the cost
                                 curve that justifies this over the 1957x1286
                                 calibration resolution.
    antialiasing_samples      -- 1-4 for loop renders (not the tutorial
                                 default of 100, a 25-100x cost multiplier).

All 3 cameras stay registered simultaneously across the whole rig lifetime:
`runBand()` iterates every registered camera in one dispatch, so moving the
"rig" between trees is 3 `setCameraPosition`/`setCameraLookat` calls, not
3 `addRadiationCamera` calls.
"""

import math

from pyhelios.types import vec3
from pyhelios.RadiationModel import CameraProperties

from .pose_convention import hfov_from_vfov

# Same vertical-FOV convention and rig geometry as apple_tree_cameras.py's
# CAMERA_RIGS, so Tier B and Tier C are looking at the same 3 viewpoints.
CAMERA_FOV_DEG = 45.0    # VERTICAL fov, matches apple_tree_cameras.py
CAMERA_MARGIN = 1.3
CAMERA_DISTANCE_MIN = 1.0

CAMERA_RIGS = [
    {"name": "above", "height_frac": 1.15},
    {"name": "level", "height_frac": 0.5},
    {"name": "below", "height_frac": 0.05},
]

DEFAULT_RESOLUTION = (640, 480)
DEFAULT_ANTIALIASING_SAMPLES = 2  # in the 1-4 range recommended for loop renders
RGB_BAND_LABELS = ["red", "green", "blue"]


def camera_position_for_tree(context, plantarch, plant_id, base_position, rig, aspect_ratio):
    """Compute a camera position/lookAt in front of one tree for a given rig.

    Copy of apple_tree_cameras.py's function of the same name -- distance is
    sized from the tree's own bounding box (height/width), not a fixed
    offset, so cameras never crop a tree that grew larger than expected.
    """
    uuids = plantarch.getAllPlantUUIDs(plant_id)
    x_bounds, y_bounds, z_bounds = context.getDomainBoundingBox(uuids)
    tree_height = z_bounds.y - z_bounds.x
    tree_width = x_bounds.y - x_bounds.x

    half_fov_v = math.radians(CAMERA_FOV_DEG) / 2
    half_fov_h = math.atan(aspect_ratio * math.tan(half_fov_v))
    distance_for_height = (tree_height / 2) / math.tan(half_fov_v) * CAMERA_MARGIN
    distance_for_width = (tree_width / 2) / math.tan(half_fov_h) * CAMERA_MARGIN
    distance = max(distance_for_height, distance_for_width, CAMERA_DISTANCE_MIN)

    look_at = vec3(base_position.x, base_position.y, z_bounds.x + 0.5 * tree_height)
    position = vec3(
        base_position.x,
        base_position.y - distance,
        z_bounds.x + rig["height_frac"] * tree_height,
    )
    return position, look_at


def build_camera_properties(resolution=DEFAULT_RESOLUTION, vfov_deg=CAMERA_FOV_DEG):
    """Build the CameraProperties + derived HFOV shared by all 3 rig cameras.

    exposure="manual" (not the CameraProperties default "auto"): auto-exposure
    re-normalizes each frame independently, which makes getCameraPixelData
    values incomparable across poses/frames -- see PHASE0_LOG.md for the
    flux-sweep experiment that surfaced this (raising flux 100x under "auto"
    made background pixels move but foliage "hot" pixels move too, since the
    whole frame gets rescaled by an unknown per-frame gain). "manual" gives
    pixel values that scale linearly and predictably with the configured
    band flux, which is what T0.4/T0.5 assume.
    """
    width, height = resolution
    aspect = width / height
    hfov_deg = hfov_from_vfov(vfov_deg, aspect)
    cam_props = CameraProperties(
        camera_resolution=resolution,
        lens_diameter=0.0,       # pinhole -- see module docstring
        HFOV=hfov_deg,
        FOV_aspect_ratio=0.0,    # auto vertical FOV from resolution
        exposure="manual",
    )
    return cam_props, hfov_deg


def compute_tree_poses(context, plantarch, plant_ids, positions, resolution=DEFAULT_RESOLUTION):
    """For each (plant_id, position), compute the 3 rig poses (above/level/below).

    Returns a list (one entry per tree) of lists of (eye, lookat) tuples, in
    CAMERA_RIGS order -- i.e. tree_poses[i][k] is the pose for rig k on tree i.
    """
    width, height = resolution
    aspect = width / height
    tree_poses = []
    for plant_id, position in zip(plant_ids, positions):
        poses = []
        for rig in CAMERA_RIGS:
            eye, lookat = camera_position_for_tree(context, plantarch, plant_id, position, rig, aspect)
            poses.append((eye, lookat))
        tree_poses.append(poses)
    return tree_poses


def register_camera_rig(radiation, initial_poses, resolution=DEFAULT_RESOLUTION,
                         vfov_deg=CAMERA_FOV_DEG, antialiasing_samples=DEFAULT_ANTIALIASING_SAMPLES,
                         bands=None):
    """Register the 3 rig cameras once, at `initial_poses` (list of 3
    (eye, lookat) tuples, CAMERA_RIGS order). Returns (camera_labels, hfov_deg).

    Later moves between trees are done with setCameraPosition/setCameraLookat
    (see run_render_loop) -- never re-add the cameras.
    """
    if bands is None:
        bands = RGB_BAND_LABELS
    cam_props, hfov_deg = build_camera_properties(resolution, vfov_deg)

    camera_labels = [rig["name"] for rig in CAMERA_RIGS]
    for label, (eye, lookat) in zip(camera_labels, initial_poses):
        radiation.addRadiationCamera(label, list(bands), eye, lookat,
                                      camera_properties=cam_props,
                                      antialiasing_samples=antialiasing_samples)
    return camera_labels, hfov_deg


def run_render_loop(radiation, camera_labels, tree_poses, bands=None, collect_pixels=True):
    """T0.4 render loop: updateGeometry() ONCE, then one runBand() per pose
    covering all bands together -- never per-view geometry updates, never
    per-band runBand calls.

    Args:
        radiation: RadiationModel with cameras already registered via
            register_camera_rig().
        camera_labels: list of camera labels, CAMERA_RIGS order.
        tree_poses: list (per tree) of lists of (eye, lookat), CAMERA_RIGS order
            -- as returned by compute_tree_poses().
        bands: band labels to render together in one runBand() call.
        collect_pixels: if True, pull getCameraPixelData for every
            camera/band into the returned frame list (in-memory, no file I/O
            per T0.4). Set False to only time the render loop itself.

    Returns:
        List of per-tree frames: each frame is {camera_label: {band: pixels}}
        (empty dict per camera/band if collect_pixels=False).
    """
    if bands is None:
        bands = RGB_BAND_LABELS

    radiation.updateGeometry()  # ONCE, outside the pose loop (T0.4)

    frames = []
    for poses in tree_poses:
        for cam, (eye, lookat) in zip(camera_labels, poses):
            radiation.setCameraPosition(cam, eye)
            radiation.setCameraLookat(cam, lookat)

        radiation.runBand(list(bands))  # ONE call, all bands together (T0.4)

        if collect_pixels:
            frame = {
                cam: {b: radiation.getCameraPixelData(cam, b) for b in bands}
                for cam in camera_labels
            }
        else:
            frame = {}
        frames.append(frame)

    return frames
