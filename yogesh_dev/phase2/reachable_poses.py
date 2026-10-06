"""
T2.3 -- PLACEHOLDER reachable view set V_reach (and an unconstrained
free-flying set used for AVUB^inf), built without Phase 3.

Real Phase 3 (T3.1-T3.4, `worktree-phase3-kinematics`) is supposed to supply
V_reach as: densely sample the 5-DOF joint space (3 prismatic axes + pan/tilt
gimbal) -> forward-kinematics to camera pose -> reject self-collision and
canopy collision -> cache per canopy. That branch may still be mid-run and
its output is explicitly NOT to be depended on here (see task brief). Every
function in this module is a documented PLACEHOLDER standing in for it.

    ***********************************************************************
    * PLACEHOLDER_reachable_poses -- NOT real kinematics/reachability.    *
    * Replace with Phase 3's real roadmap output before trusting any AVUB *
    * number produced from it as a real hardware-capability metric.       *
    ***********************************************************************

## Interface a real T3.4 roadmap must satisfy to be substitutable here

Everything downstream (visibility.py, avub.py, achievability.py) consumes
only a plain `List[(eye: vec3, lookat: vec3)]` per tree/canopy -- it does not
care how that list was produced. A real T3.4 roadmap should expose a
function with this signature:

    def reachable_poses(tree_bbox, base_position) -> List[Tuple[vec3, vec3]]

(one call per canopy, matching "cache per canopy" in the design doc), where
each pose is a *feasible, collision-checked, kinematically reachable* camera
pose -- ideally accompanied by the roadmap's graph structure (nodes + k-NN
edges weighted by T3.3 execution time) for planning, but AVUB only needs the
pose list itself. Swap `placeholder_reachable_poses` for that function (same
call site, same return shape) once it exists; nothing else in phase2/ needs
to change.

## What this placeholder actually does instead

`placeholder_reachable_poses`: a dense axis-aligned grid over the same three
prismatic axes a real rail-mounted arm would have --
  - rail (x): camera slides side-to-side along a fixed-distance rail in
    front of the tree row (mirrors a linear cart axis)
  - height (z): camera slides up/down (mirrors a vertical prismatic axis),
    same 0.05-1.15 * tree_height envelope as Phase 0/1's 3-camera rig
    (yogesh_dev/phase0/radiation_cameras.py CAMERA_RIGS), just sampled
    densely instead of at 3 fixed fractions
  - depth (y): camera moves in/out from the canopy (mirrors an in-out
    prismatic axis), sampled around the same margin-based standoff distance
    Phase 0 computes from the tree's own bounding box
all three axes look roughly LEVEL into the canopy from the FRONT hemisphere
only (pan/tilt aimed generally at the canopy at the camera's own height) --
this asymmetry (front-hemisphere-only, one side of the row) is what should
make AVUB < AVUB^inf even in placeholder form, for a structurally real
reason (a rail-mounted arm cannot fly around to the back of the tree),
not an arbitrary sampling-density difference.

No self-collision or canopy-collision rejection, no joint limits, no
execution-time weighting -- all of that needs Phase 3 and is explicitly out
of scope here.

`placeholder_free_flying_poses` (for AVUB^inf): full-sphere sampling around
the tree at several azimuths (0-360 degrees, i.e. including the back of the
tree a rail-mounted arm can never reach), several elevations (including
below and well above canopy height), and multiple radii -- always looking
directly at the tree's center. This is the "unconstrained free-flying
camera" the design doc's AVUB^inf calls for; it is denser AND structurally
broader (full sphere vs front hemisphere) than the reachable set, which is
what makes AVUB / AVUB^inf a meaningful (if placeholder-derived) ratio
rather than a foregone conclusion.
"""

import math

from pyhelios.types import vec3


def _tree_geometry(context, plantarch, plant_id, base_position):
    uuids = plantarch.getAllPlantUUIDs(plant_id)
    x_bounds, y_bounds, z_bounds = context.getDomainBoundingBox(uuids)
    tree_height = z_bounds.y - z_bounds.x
    tree_width = x_bounds.y - x_bounds.x
    z_min = z_bounds.x
    return tree_height, tree_width, z_min


def _standoff_distance(tree_height, tree_width, vfov_deg, aspect_ratio, margin=1.3, dist_min=1.0):
    half_fov_v = math.radians(vfov_deg) / 2
    half_fov_h = math.atan(aspect_ratio * math.tan(half_fov_v))
    distance_for_height = (tree_height / 2) / math.tan(half_fov_v) * margin
    distance_for_width = (tree_width / 2) / math.tan(half_fov_h) * margin
    return max(distance_for_height, distance_for_width, dist_min)


def placeholder_reachable_poses(context, plantarch, plant_id, base_position,
                                 vfov_deg=45.0, aspect_ratio=640 / 480,
                                 n_rail=5, n_height=5, n_depth=2,
                                 rail_halfwidth_m=0.5, depth_frac_range=(0.75, 1.25)):
    """PLACEHOLDER_reachable_poses -- see module docstring. Dense grid over
    (rail x, height z, depth y) in front of one tree, always looking level
    into the canopy from the front hemisphere only.

    Returns a list of (eye: vec3, lookat: vec3), length n_rail*n_height*n_depth.
    """
    tree_height, tree_width, z_min = _tree_geometry(context, plantarch, plant_id, base_position)
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
                # Look level (same height as eye), generally toward the canopy
                # column (x=base_position.x, y=base_position.y) -- not always
                # re-centering on a fixed point, so the grid actually samples
                # different look directions like a real gimbal sweep would.
                lookat = vec3(base_position.x, base_position.y, eye_z)
                poses.append((eye, lookat))
    return poses


def placeholder_free_flying_poses(context, plantarch, plant_id, base_position,
                                   vfov_deg=45.0, aspect_ratio=640 / 480,
                                   n_azimuth=10, n_elevation=6, n_radius=2,
                                   elevation_range_deg=(-60.0, 80.0),
                                   depth_frac_range=(0.75, 1.25)):
    """PLACEHOLDER free-flying pose set for AVUB^inf -- see module docstring.
    Full-sphere sampling around the tree's own center (not just the front
    hemisphere), always looking at the tree center.

    Returns a list of (eye: vec3, lookat: vec3), length
    n_azimuth*n_elevation*n_radius.
    """
    tree_height, tree_width, z_min = _tree_geometry(context, plantarch, plant_id, base_position)
    distance = _standoff_distance(tree_height, tree_width, vfov_deg, aspect_ratio)
    center = vec3(base_position.x, base_position.y, z_min + 0.5 * tree_height)

    azimuths = _linspace(0.0, 360.0, n_azimuth, endpoint=False)
    elevations = _linspace(elevation_range_deg[0], elevation_range_deg[1], n_elevation)
    depth_fracs = _linspace(depth_frac_range[0], depth_frac_range[1], n_radius)

    poses = []
    for el_deg in elevations:
        el = math.radians(el_deg)
        for df in depth_fracs:
            r = distance * df
            for az_deg in azimuths:
                az = math.radians(az_deg)
                dx = r * math.cos(el) * math.sin(az)
                dy = -r * math.cos(el) * math.cos(az)  # az=0 -> same "front" side as the reachable set
                dz = r * math.sin(el)
                eye = vec3(center.x + dx, center.y + dy, center.z + dz)
                poses.append((eye, center))
    return poses


def _linspace(lo, hi, n, endpoint=True):
    if n <= 1:
        return [lo]
    span = (hi - lo) / (n - 1 if endpoint else n)
    return [lo + i * span for i in range(n)]
