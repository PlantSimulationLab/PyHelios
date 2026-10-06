"""
T8.2 -- the 3 view-selection policies scored on every factorial-cell canopy:
`fixed_rig`, `reachable_union` (pre-registered comparison pair, PREREGISTRATION.md),
and `look_away` (T8.5's degenerate baseline). All 3 reuse Phase 0/2/5's real
radiation-camera rendering and per-primitive visibility machinery unchanged -- nothing
here re-implements rendering or occlusion, it only selects which poses to render and how
to combine their visibility sets.

## Why camera-pose geometry is computed from cached UUIDs, not Phase 0/2's own
   plant_id-based helpers, directly

`camera_position_for_tree` (phase0/radiation_cameras.py) and `placeholder_reachable_poses`
(phase2/reachable_poses.py) both call `plantarch.getAllPlantUUIDs(plant_id)` internally to
get a tree's bounding box. That call reliably raises `unordered_map::at` once ANY
leaf/fruit object on that plant has been removed via `context.deleteObject` -- a real
gotcha this phase found (see canopy_factory.py's docstring and PHASE8_LOG.md), because
Phase 8 is the first phase to thin canopies and then ask PlantArchitecture about them
again. So this module re-derives the same bounding-box/standoff-distance/grid math those
two functions use, but takes an explicit UUID list (Canopy's cached post-thinning list)
instead of re-querying PlantArchitecture. The math itself (standoff distance, rig height
fractions, rail/height/depth grid) is unchanged from Phase 0/2 -- `_standoff_distance` and
`_linspace` are imported directly from phase2/reachable_poses.py, not reimplemented.
"""

import math
import time

from pyhelios import RadiationModel
from pyhelios.types import vec3

from yogesh_dev.phase0.radiation_setup import setup_bands_and_lights
from yogesh_dev.phase0.radiation_cameras import (
    build_camera_properties, RGB_BAND_LABELS, CAMERA_RIGS, CAMERA_FOV_DEG,
)
from yogesh_dev.phase2.visibility import (
    assign_vis_primitive_ids, render_poses_batched, union_visible_ids,
)
from yogesh_dev.phase2.reachable_poses import _standoff_distance, _linspace
from yogesh_dev.phase5.common import coverage_summary

RESOLUTION = (320, 240)
VFOV_DEG = 45.0
CAMERA_LABELS = ["camA", "camB", "camC"]

# Reduced from Phase 5's 108 poses/tree (n_rail=6,n_height=6,n_depth=3) -- see
# PHASE8_LOG.md for the real per-pose render cost this reduction is based on.
REDUCED_REACHABLE_GRID = dict(n_rail=3, n_height=3, n_depth=2)


def _tree_bounds(context, uuids):
    x_bounds, y_bounds, z_bounds = context.getDomainBoundingBox(uuids)
    tree_height = z_bounds.y - z_bounds.x
    tree_width = x_bounds.y - x_bounds.x
    return tree_height, tree_width, z_bounds.x


def rig_pose_from_uuids(context, uuids, base_position, height_frac, aspect_ratio, vfov_deg=CAMERA_FOV_DEG):
    """Same math as phase0/radiation_cameras.py's `camera_position_for_tree`, but
    takes a UUID list directly (see module docstring)."""
    tree_height, tree_width, z_min = _tree_bounds(context, uuids)
    half_fov_v = math.radians(vfov_deg) / 2
    half_fov_h = math.atan(aspect_ratio * math.tan(half_fov_v))
    distance = max(
        (tree_height / 2) / math.tan(half_fov_v) * 1.3,
        (tree_width / 2) / math.tan(half_fov_h) * 1.3,
        1.0,
    )
    look_at = vec3(base_position.x, base_position.y, z_min + 0.5 * tree_height)
    position = vec3(base_position.x, base_position.y - distance, z_min + height_frac * tree_height)
    return position, look_at


def reachable_poses_from_uuids(context, uuids, base_position, vfov_deg=VFOV_DEG,
                                aspect_ratio=320 / 240, n_rail=3, n_height=3, n_depth=2,
                                rail_halfwidth_m=0.5, depth_frac_range=(0.75, 1.25)):
    """Same math as phase2/reachable_poses.py's `placeholder_reachable_poses`, but
    takes a UUID list directly (see module docstring)."""
    tree_height, tree_width, z_min = _tree_bounds(context, uuids)
    distance = _standoff_distance(tree_height, tree_width, vfov_deg, aspect_ratio)

    rail_offsets = _linspace(-rail_halfwidth_m, rail_halfwidth_m, n_rail)
    height_fracs = _linspace(0.05, 1.15, n_height)
    depth_fracs = _linspace(depth_frac_range[0], depth_frac_range[1], n_depth)

    poses = []
    for hf in height_fracs:
        eye_z = z_min + hf * tree_height
        for df in depth_fracs:
            dist = distance * df
            for rx in rail_offsets:
                eye = vec3(base_position.x + rx, base_position.y - dist, eye_z)
                lookat = vec3(base_position.x, base_position.y, eye_z)
                poses.append((eye, lookat))
    return poses


def look_away_pose(context, uuids, base_position, aspect_ratio):
    """T8.5's degenerate baseline pose: same standoff distance/height as the fixed
    rig's 'level' position, boresight rotated 180 degrees in azimuth (facing directly
    AWAY from the canopy) -- see PREREGISTRATION.md."""
    eye, lookat = rig_pose_from_uuids(context, uuids, base_position, 0.5, aspect_ratio)
    # Reflect the look direction through the eye point: lookat' = eye - (lookat - eye)
    away = vec3(eye.x - (lookat.x - eye.x), eye.y - (lookat.y - eye.y), eye.z - (lookat.z - eye.z))
    return eye, away


def score_canopy(canopy, reachable_grid=None):
    """Render `fixed_rig`, `reachable_union`, and `look_away` on one already-built
    Canopy (yogesh_dev/phase8/canopy_factory.py) and return each policy's real
    `mean_coverage_frac` / `fraction_fruit_observed` (Phase 2/5's headline metric, see
    PREREGISTRATION.md) plus render timing.

    Caller owns `canopy` (built via canopy_factory.build_canopy) and must call
    `canopy.close()` -- this function only opens/closes its own RadiationModel.
    """
    if reachable_grid is None:
        reachable_grid = REDUCED_REACHABLE_GRID

    context = canopy.context
    all_uuids = canopy.all_uuids()
    prim_id_to_info, fruit_prim_ids = assign_vis_primitive_ids(context, all_uuids, canopy.fruit_records)

    aspect = RESOLUTION[0] / RESOLUTION[1]
    per_tree_uuids = [canopy.tree_uuids(i) for i in range(len(canopy.plant_ids))]

    with RadiationModel(context) as radiation:
        setup_bands_and_lights(radiation)
        cam_props, hfov_deg = build_camera_properties(RESOLUTION, VFOV_DEG)

        # Register camera slots at a throwaway initial pose (first tree's 'level' rig
        # position) -- real poses are set per-render via setCameraPosition/lookat,
        # never by re-adding cameras (T0.4 pattern).
        init_eye, init_lookat = rig_pose_from_uuids(context, per_tree_uuids[0], canopy.positions[0], 0.5, aspect)
        for label in CAMERA_LABELS:
            radiation.addRadiationCamera(label, RGB_BAND_LABELS, init_eye, init_lookat,
                                          camera_properties=cam_props, antialiasing_samples=1)
        radiation.updateGeometry()  # ONCE (T0.4)

        # --- fixed_rig: 3 rig poses PER TREE, no motion ---
        fixed_rig_poses = []
        for uuids, pos in zip(per_tree_uuids, canopy.positions):
            for rig in CAMERA_RIGS:
                fixed_rig_poses.append(rig_pose_from_uuids(context, uuids, pos, rig["height_frac"], aspect))

        # --- reachable_union: small V_reach grid PER TREE ---
        reachable_poses = []
        for uuids, pos in zip(per_tree_uuids, canopy.positions):
            poses = reachable_poses_from_uuids(context, uuids, pos, vfov_deg=VFOV_DEG,
                                                aspect_ratio=aspect, **reachable_grid)
            reachable_poses.extend(poses)

        # --- look_away: 1 pose, first tree only ---
        look_away = look_away_pose(context, per_tree_uuids[0], canopy.positions[0], aspect)

        all_poses = fixed_rig_poses + reachable_poses + [look_away]
        t0 = time.time()
        results = render_poses_batched(radiation, CAMERA_LABELS, all_poses, RGB_BAND_LABELS)
        render_s = time.time() - t0

    n_fixed = len(fixed_rig_poses)
    n_reach = len(reachable_poses)
    fixed_rig_vis = [vis for vis, _ in results[:n_fixed]]
    reachable_vis = [vis for vis, _ in results[n_fixed:n_fixed + n_reach]]
    look_away_vis = results[n_fixed + n_reach][0]

    fixed_rig_union = union_visible_ids(fixed_rig_vis)[-1] if fixed_rig_vis else set()
    reachable_union = union_visible_ids(reachable_vis)[-1] if reachable_vis else set()
    # single_fixed (T5.1-style, "absolute floor"): the first tree's own 'level' rig
    # pose alone -- CAMERA_RIGS order is [above, level, below], so index 1. Free
    # (already rendered as part of fixed_rig_poses), no extra render cost.
    level_idx = [r["name"] for r in CAMERA_RIGS].index("level")
    single_fixed_vis = fixed_rig_vis[level_idx] if fixed_rig_vis else set()

    fruit_records = canopy.fruit_records
    policies = {
        "single_fixed": coverage_summary(single_fixed_vis, fruit_records, fruit_prim_ids, prim_id_to_info),
        "fixed_rig": coverage_summary(fixed_rig_union, fruit_records, fruit_prim_ids, prim_id_to_info),
        "reachable_union": coverage_summary(reachable_union, fruit_records, fruit_prim_ids, prim_id_to_info),
        "look_away": coverage_summary(look_away_vis, fruit_records, fruit_prim_ids, prim_id_to_info),
    }
    return {
        "policies": policies,
        "n_fixed_rig_poses": n_fixed,
        "n_reachable_poses": n_reach,
        "render_s": render_s,
    }
