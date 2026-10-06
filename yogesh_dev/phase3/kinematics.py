"""
T3.1/T3.2 -- 5-DOF forward and inverse kinematics for the per-arm camera rig.

Helios/PyHelios has zero kinematics support (no FK/IK, no joint limits, no
Jacobians) -- everything here is hand-rolled pure Python, deliberately with
no dependency on pyhelios, so it can be imported and round-trip-tested with
nothing but the standard library + numpy present. The only thing Helios ever
needs out of this module is a (position, lookat) pair to feed
`RadiationModel.addRadiationCamera` / `setCameraPosition` / `setCameraLookat`.

Chain (5 DOF, in joint-state order): x, y, z, pan, tilt
    x     -- prismatic, "left-right" along the tree row (world +X)
    y     -- prismatic, "in-out", reach from the rail toward the canopy (world +Y)
    z     -- prismatic, "up-down" (world +Z)
    pan   -- rotation about world +Z (azimuth)
    tilt  -- rotation elevating the look direction out of the horizontal plane

Position/orientation are fully decoupled: the camera's optical center sits
exactly at (x, y, z) -- pan/tilt rotate the *look direction* about that fixed
point, they do not move it (i.e. zero gimbal offset). This is what makes the
closed-form IK in T3.2 possible ("solve linear axes for position, then
pan/tilt for look direction" -- see task doc). A real gimbal will have a
nonzero offset between its rotation center and the camera's nodal point;
modeling that would turn IK into a small nonlinear solve. Flagged here as a
simplification to revisit once real hardware geometry is available.

Look-direction convention (pan=0, tilt=0 -> +Y, world up = +Z, no roll):
    forward = (sin(pan)*cos(tilt), cos(pan)*cos(tilt), sin(tilt))
This matches the world_up=(0,0,1) OpenCV-style convention empirically
validated for the RadiationCamera in
`worktree-phase0-radiation:yogesh_dev/phase0/pose_convention.py` (T0.3): the
camera has no up-vector parameter and EXIF roll is hardcoded to 0, so this
5-DOF chain must never introduce roll -- it doesn't, by construction, since
neither pan nor tilt rotates about the view axis itself.

Joint limits / vertical bands (T3.1) are PLACEHOLDERS -- there is no real
hardware spec available yet. They are sized against the actual 3-tree canopy
this repo builds (`yogesh_dev/phase0/canopy.py`: trees at x=0, 1.5, 3 m) and
the real fruit bounding boxes exported in Phase 1
(`yogesh_dev/phase3/reference_data/fruit_ground_truth.json`: fruit z in
[0.70, 1.82] m across all 3 trees). Revisit every number in
`default_arm_configs()` against actual hardware before trusting it for
anything beyond this demo.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class JointLimits:
    x: Tuple[float, float]
    y: Tuple[float, float]
    z: Tuple[float, float]
    pan_deg: Tuple[float, float]
    tilt_deg: Tuple[float, float]


@dataclass(frozen=True)
class ArmConfig:
    """One arm's joint limits + a synthetic look-distance used only to place
    a concrete `lookat` point (RadiationCamera only cares about the direction
    from eye to lookat, not the distance -- see phase0/pose_convention.py)."""
    name: str
    limits: JointLimits
    look_distance: float = 1.0


@dataclass(frozen=True)
class JointState:
    x: float
    y: float
    z: float
    pan_deg: float
    tilt_deg: float

    def as_tuple(self) -> Tuple[float, float, float, float, float]:
        return (self.x, self.y, self.z, self.pan_deg, self.tilt_deg)


@dataclass(frozen=True)
class CameraPose:
    position: Tuple[float, float, float]
    lookat: Tuple[float, float, float]
    forward: Tuple[float, float, float]


def default_arm_configs() -> List[ArmConfig]:
    """Placeholder 3-arm workcell spanning the tree row.

    Shared by all 3 arms:
        x in [-0.75, 3.75] m  -- full rail traversal across all 3 trees
                                  (trees at x=0, 1.5, 3) plus 0.75 m margin
                                  on each end for the outer trees' canopy
                                  radius (~0.6 m, from Phase 1 fruit bboxes).
        y in [-1.10, -0.05] m -- reach envelope from the rail (behind the
                                  canopy at y ~ -1.1) toward the canopy front
                                  face (fruit y as low as -0.43 m); the arm
                                  never crosses to y > -0.05 so it can't
                                  physically pass through the trunk region.
        pan  in [-55, 55] deg -- enough to sweep toward neighboring trees
                                  from one rail (cart) position.
        tilt in [-35, 35] deg -- covers fruit above/below the arm's own
                                  height band without approaching gimbal lock.

    Per-arm, NON-OVERLAPPING vertical (z) bands -- this is what makes
    arm-arm collision structurally impossible by construction (T3.5), since
    each arm's z coordinate can never leave its own band regardless of
    x/y/pan/tilt. Fruit z spans [0.70, 1.82] m (Phase 1 ground truth); the 3
    bands below cover [0.50, 1.95] m with explicit 0.05 m clearance gaps
    between adjacent bands so floating-point band edges never touch:
        arm_low  z in [0.50, 0.95]
        arm_mid  z in [1.00, 1.45]
        arm_high z in [1.50, 1.95]

    ALL NUMBERS HERE ARE PLACEHOLDERS pending real hardware measurements.
    """
    x_limits = (-0.75, 3.75)
    y_limits = (-1.10, -0.05)
    pan_limits = (-55.0, 55.0)
    tilt_limits = (-35.0, 35.0)
    z_bands = [
        ("arm_low", (0.50, 0.95)),
        ("arm_mid", (1.00, 1.45)),
        ("arm_high", (1.50, 1.95)),
    ]
    arms = []
    for name, z_band in z_bands:
        limits = JointLimits(
            x=x_limits, y=y_limits, z=z_band,
            pan_deg=pan_limits, tilt_deg=tilt_limits,
        )
        arms.append(ArmConfig(name=name, limits=limits))
    return arms


def joint_within_limits(q: JointState, limits: JointLimits, eps: float = 1e-9) -> Tuple[bool, List[str]]:
    """Return (ok, list_of_violated_axis_names).

    `eps` absorbs floating-point round-off from the asin/atan2 in
    `inverse_kinematics` (e.g. a joint exactly at its limit can round-trip to
    `hi + 1e-14`) -- it is NOT slack in the real joint limits, just tolerance
    for comparing floats against them. Confirmed necessary empirically: see
    `verify_roundtrip` on exact-boundary grid samples in PHASE3_LOG.md.
    """
    violations = []
    checks = [
        ("x", q.x, limits.x),
        ("y", q.y, limits.y),
        ("z", q.z, limits.z),
        ("pan", q.pan_deg, limits.pan_deg),
        ("tilt", q.tilt_deg, limits.tilt_deg),
    ]
    for name, value, (lo, hi) in checks:
        if not (lo - eps <= value <= hi + eps):
            violations.append(name)
    return (len(violations) == 0, violations)


def forward_kinematics(q: JointState, arm: ArmConfig) -> CameraPose:
    """T3.1 -- 5-DOF forward kinematics: joints -> camera (position, lookat).

    Does NOT enforce joint limits (callers that need enforcement should call
    `joint_within_limits` themselves -- the roadmap builder in roadmap.py
    does this at discretization time, since limits there define the sampling
    grid rather than a runtime guard).
    """
    pan = math.radians(q.pan_deg)
    tilt = math.radians(q.tilt_deg)
    cos_tilt = math.cos(tilt)
    fx = math.sin(pan) * cos_tilt
    fy = math.cos(pan) * cos_tilt
    fz = math.sin(tilt)

    position = (q.x, q.y, q.z)
    lookat = (
        q.x + fx * arm.look_distance,
        q.y + fy * arm.look_distance,
        q.z + fz * arm.look_distance,
    )
    return CameraPose(position=position, lookat=lookat, forward=(fx, fy, fz))


def inverse_kinematics(pose: CameraPose, arm: ArmConfig) -> Tuple[JointState, bool, List[str]]:
    """T3.2 -- closed-form IK: camera (position, lookat) -> joints.

    Position is trivial (x, y, z = the camera position directly, since
    position and orientation are decoupled -- see module docstring).
    Orientation solves in closed form because the chain has exactly two
    rotational DOF matching the two free angles of a unit direction vector:

        tilt = asin(dz)                      (dz = forward.z)
        pan  = atan2(dx, dy)                  (valid since cos(tilt) > 0
                                                for any tilt in (-90, 90) deg,
                                                which our joint limits (T3.1)
                                                stay well inside of -- no
                                                gimbal-lock branch needed)

    No iterative solver of any kind. Returns (joints, within_limits, violated_axes);
    callers decide whether an out-of-limits result should be an error or just
    filtered out (the roadmap builder filters).
    """
    px, py, pz = pose.position
    lx, ly, lz = pose.lookat
    dx, dy, dz = lx - px, ly - py, lz - pz
    norm = math.sqrt(dx * dx + dy * dy + dz * dz)
    if norm < 1e-12:
        raise ValueError("pose.lookat coincides with pose.position -- look direction undefined")
    dx, dy, dz = dx / norm, dy / norm, dz / norm

    dz_clamped = max(-1.0, min(1.0, dz))
    tilt = math.asin(dz_clamped)
    pan = math.atan2(dx, dy)

    q = JointState(x=px, y=py, z=pz, pan_deg=math.degrees(pan), tilt_deg=math.degrees(tilt))
    ok, violations = joint_within_limits(q, arm.limits)
    return q, ok, violations


def verify_roundtrip(arm: ArmConfig, n_per_axis: int = 4, seed: int = 0) -> Dict:
    """T3.2 -- ACTUALLY RUN the FK(IK(pose)) round-trip check (not just an
    assertion in a docstring). Samples a grid of joint states within `arm`'s
    limits, runs FK -> IK -> FK, and reports the max discrepancy between the
    original and round-tripped (position, lookat, forward) plus the max
    joint-value discrepancy.

    Returns a dict with max errors and pass/fail so callers can log/assert.
    """
    import itertools
    import random

    rng = random.Random(seed)
    lim = arm.limits
    xs = _linspace(lim.x[0], lim.x[1], n_per_axis)
    ys = _linspace(lim.y[0], lim.y[1], n_per_axis)
    zs = _linspace(lim.z[0], lim.z[1], n_per_axis)
    pans = _linspace(lim.pan_deg[0], lim.pan_deg[1], n_per_axis)
    tilts = _linspace(lim.tilt_deg[0], lim.tilt_deg[1], n_per_axis)

    max_pos_err = 0.0
    max_lookat_err = 0.0
    max_forward_err = 0.0
    max_joint_err = 0.0
    n_checked = 0
    n_limit_violations = 0

    for x, y, z, pan, tilt in itertools.product(xs, ys, zs, pans, tilts):
        # small random jitter within limits so grid corners/edges aren't the
        # only thing tested (still clamp to stay within limits)
        jitter = rng.uniform(-1e-3, 1e-3)
        q0 = JointState(
            x=x, y=y, z=z,
            pan_deg=min(max(pan + jitter, lim.pan_deg[0]), lim.pan_deg[1]),
            tilt_deg=min(max(tilt + jitter, lim.tilt_deg[0]), lim.tilt_deg[1]),
        )
        pose0 = forward_kinematics(q0, arm)
        q1, ok, _violations = inverse_kinematics(pose0, arm)
        if not ok:
            n_limit_violations += 1
        pose1 = forward_kinematics(q1, arm)

        pos_err = _dist(pose0.position, pose1.position)
        lookat_err = _dist(pose0.lookat, pose1.lookat)
        fwd_err = _dist(pose0.forward, pose1.forward)
        joint_err = max(
            abs(q0.x - q1.x), abs(q0.y - q1.y), abs(q0.z - q1.z),
            abs(q0.pan_deg - q1.pan_deg), abs(q0.tilt_deg - q1.tilt_deg),
        )

        max_pos_err = max(max_pos_err, pos_err)
        max_lookat_err = max(max_lookat_err, lookat_err)
        max_forward_err = max(max_forward_err, fwd_err)
        max_joint_err = max(max_joint_err, joint_err)
        n_checked += 1

    tol = 1e-6
    passed = (max_pos_err < tol and max_lookat_err < tol
              and max_forward_err < tol and max_joint_err < tol)

    return {
        "arm": arm.name,
        "n_checked": n_checked,
        "n_limit_violations": n_limit_violations,
        "max_position_error_m": max_pos_err,
        "max_lookat_error_m": max_lookat_err,
        "max_forward_error": max_forward_err,
        "max_joint_error": max_joint_err,
        "tolerance": tol,
        "passed": passed,
    }


def _linspace(lo: float, hi: float, n: int) -> List[float]:
    if n <= 1:
        return [0.5 * (lo + hi)]
    step = (hi - lo) / (n - 1)
    return [lo + i * step for i in range(n)]


def _dist(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> float:
    return math.sqrt(sum((ai - bi) ** 2 for ai, bi in zip(a, b)))
