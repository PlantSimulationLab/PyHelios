"""
Reference copy of `worktree-phase3-kinematics:yogesh_dev/phase3/kinematics.py`
(T3.1 forward kinematics / T3.2 inverse kinematics for the 5-DOF camera-arm
chain), copied into `yogesh_dev/phase4/` per the same pattern Phase 1 used for
`phase0/canopy.py` and Phase 3 used for `phase1/fruit_ground_truth.json` --
each phase's worktree is a separate git branch/checkout, so anything Phase 4
needs from Phase 3 has to be vendored here rather than cross-imported.

Only addition over the Phase 3 original: `single_tree_arm_configs()`, sized
for Phase 4's single-tree dataset (`gen_dataset.py` builds one seeded apple
tree at the origin, not the 3-tree row Phase 3's `default_arm_configs()`
assumes) -- same non-overlapping-z-band structure, narrower x/y envelope.
`default_arm_configs()` itself is kept verbatim for anything that wants the
original 3-tree-row numbers.

Everything else (JointLimits, ArmConfig, JointState, CameraPose,
forward_kinematics, inverse_kinematics, joint_within_limits, verify_roundtrip)
is unchanged from Phase 3 -- see that module's docstring for the full
derivation and the pan/tilt/pose-convention rationale.
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
    """Verbatim from Phase 3 -- placeholder 3-arm workcell spanning the
    original 3-tree row (trees at x=0, 1.5, 3). See phase3/kinematics.py for
    the full rationale. Not used by Phase 4's single-tree dataset; kept for
    reference / anything that wants the original numbers."""
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
        limits = JointLimits(x=x_limits, y=y_limits, z=z_band, pan_deg=pan_limits, tilt_deg=tilt_limits)
        arms.append(ArmConfig(name=name, limits=limits))
    return arms


def single_tree_arm_configs(z_bands=None) -> List[ArmConfig]:
    """Phase-4-specific: 3 arms sharing an x/y envelope sized for ONE tree at
    the origin (Phase 4's `gen_dataset.py` scene), same non-overlapping
    vertical bands idea as Phase 3's `default_arm_configs`. Narrower x range
    (+/-0.6 m rail either side of the single tree, vs +/-0.75 m margin beyond
    a 3-tree, 4.5 m row) since there is only one canopy to work in front of.

    z_bands default matches Phase 1's real fruit z-range for a single tree
    (see PHASE4_LOG.md for the actual observed range) split into 3
    non-overlapping bands with explicit clearance gaps, same structural
    arm-arm collision guarantee as Phase 3 (T3.5).
    """
    if z_bands is None:
        z_bands = [
            ("arm_low", (0.30, 0.75)),
            ("arm_mid", (0.80, 1.25)),
            ("arm_high", (1.30, 1.75)),
        ]
    x_limits = (-0.6, 0.6)
    y_limits = (-1.10, -0.35)
    pan_limits = (-55.0, 55.0)
    tilt_limits = (-35.0, 35.0)
    arms = []
    for name, z_band in z_bands:
        limits = JointLimits(x=x_limits, y=y_limits, z=z_band, pan_deg=pan_limits, tilt_deg=tilt_limits)
        arms.append(ArmConfig(name=name, limits=limits))
    return arms


def joint_within_limits(q: JointState, limits: JointLimits, eps: float = 1e-9) -> Tuple[bool, List[str]]:
    violations = []
    checks = [
        ("x", q.x, limits.x), ("y", q.y, limits.y), ("z", q.z, limits.z),
        ("pan", q.pan_deg, limits.pan_deg), ("tilt", q.tilt_deg, limits.tilt_deg),
    ]
    for name, value, (lo, hi) in checks:
        if not (lo - eps <= value <= hi + eps):
            violations.append(name)
    return (len(violations) == 0, violations)


def forward_kinematics(q: JointState, arm: ArmConfig) -> CameraPose:
    pan = math.radians(q.pan_deg)
    tilt = math.radians(q.tilt_deg)
    cos_tilt = math.cos(tilt)
    fx = math.sin(pan) * cos_tilt
    fy = math.cos(pan) * cos_tilt
    fz = math.sin(tilt)
    position = (q.x, q.y, q.z)
    lookat = (q.x + fx * arm.look_distance, q.y + fy * arm.look_distance, q.z + fz * arm.look_distance)
    return CameraPose(position=position, lookat=lookat, forward=(fx, fy, fz))


def inverse_kinematics(pose: CameraPose, arm: ArmConfig) -> Tuple[JointState, bool, List[str]]:
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


def _linspace(lo: float, hi: float, n: int) -> List[float]:
    if n <= 1:
        return [0.5 * (lo + hi)]
    step = (hi - lo) / (n - 1)
    return [lo + i * step for i in range(n)]


def _dist(a, b) -> float:
    return math.sqrt(sum((ai - bi) ** 2 for ai, bi in zip(a, b)))


def verify_roundtrip(arm: ArmConfig, n_per_axis: int = 4, seed: int = 0) -> Dict:
    import itertools
    import random

    rng = random.Random(seed)
    lim = arm.limits
    xs = _linspace(lim.x[0], lim.x[1], n_per_axis)
    ys = _linspace(lim.y[0], lim.y[1], n_per_axis)
    zs = _linspace(lim.z[0], lim.z[1], n_per_axis)
    pans = _linspace(lim.pan_deg[0], lim.pan_deg[1], n_per_axis)
    tilts = _linspace(lim.tilt_deg[0], lim.tilt_deg[1], n_per_axis)

    max_pos_err = max_lookat_err = max_forward_err = max_joint_err = 0.0
    n_checked = 0
    n_limit_violations = 0

    for x, y, z, pan, tilt in itertools.product(xs, ys, zs, pans, tilts):
        jitter = rng.uniform(-1e-3, 1e-3)
        q0 = JointState(x=x, y=y, z=z,
                         pan_deg=min(max(pan + jitter, lim.pan_deg[0]), lim.pan_deg[1]),
                         tilt_deg=min(max(tilt + jitter, lim.tilt_deg[0]), lim.tilt_deg[1]))
        pose0 = forward_kinematics(q0, arm)
        q1, ok, _v = inverse_kinematics(pose0, arm)
        if not ok:
            n_limit_violations += 1
        pose1 = forward_kinematics(q1, arm)

        max_pos_err = max(max_pos_err, _dist(pose0.position, pose1.position))
        max_lookat_err = max(max_lookat_err, _dist(pose0.lookat, pose1.lookat))
        max_forward_err = max(max_forward_err, _dist(pose0.forward, pose1.forward))
        max_joint_err = max(max_joint_err, max(abs(q0.x - q1.x), abs(q0.y - q1.y), abs(q0.z - q1.z),
                                                abs(q0.pan_deg - q1.pan_deg), abs(q0.tilt_deg - q1.tilt_deg)))
        n_checked += 1

    tol = 1e-6
    passed = (max_pos_err < tol and max_lookat_err < tol and max_forward_err < tol and max_joint_err < tol)
    return {
        "arm": arm.name, "n_checked": n_checked, "n_limit_violations": n_limit_violations,
        "max_position_error_m": max_pos_err, "max_lookat_error_m": max_lookat_err,
        "max_forward_error": max_forward_err, "max_joint_error": max_joint_err,
        "tolerance": tol, "passed": passed,
    }
