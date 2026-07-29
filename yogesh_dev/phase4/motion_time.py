"""
Verbatim reference copy of `worktree-phase3-kinematics:yogesh_dev/phase3/motion_time.py`
(T3.3 trapezoidal-velocity-profile execution-time model), vendored here for
the same cross-worktree reason documented in `kinematics.py`. See the
original for the full derivation and the placeholder-hardware-numbers caveat
-- nothing here is new; Phase 4's `explore_planner.py` / `exploit_planner.py`
/ `coordination.py` consume `move_time` as the real (if placeholder-hardware)
execution-time weight for roadmap edges, per T4.6/T4.8's "time-normalized
utility using T3.3's real execution-time weights" requirement.
"""

import math
from dataclasses import dataclass
from typing import Dict

try:
    from .kinematics import JointState
except ImportError:  # standalone script use (e.g. gen_dataset.py), no package context
    from kinematics import JointState


@dataclass(frozen=True)
class AxisSpec:
    name: str
    v_max: float
    a_max: float


LINEAR_AXIS_SPECS: Dict[str, AxisSpec] = {
    "x": AxisSpec("x_rail", v_max=0.30, a_max=0.50),
    "y": AxisSpec("y_extend", v_max=0.20, a_max=0.40),
    "z": AxisSpec("z_lift", v_max=0.25, a_max=0.40),
}

GIMBAL_AXIS_SPECS: Dict[str, AxisSpec] = {
    "pan": AxisSpec("pan", v_max=180.0, a_max=400.0),
    "tilt": AxisSpec("tilt", v_max=180.0, a_max=400.0),
}


def trapezoidal_time(distance: float, spec: AxisSpec) -> float:
    d = abs(distance)
    if d == 0.0:
        return 0.0
    v_max, a_max = spec.v_max, spec.a_max
    d_accel = (v_max ** 2) / (2.0 * a_max)
    if 2.0 * d_accel <= d:
        return 2.0 * (v_max / a_max) + (d - 2.0 * d_accel) / v_max
    return 2.0 * math.sqrt(d / a_max)


def per_axis_times(q_from: JointState, q_to: JointState) -> Dict[str, float]:
    return {
        "x": trapezoidal_time(q_to.x - q_from.x, LINEAR_AXIS_SPECS["x"]),
        "y": trapezoidal_time(q_to.y - q_from.y, LINEAR_AXIS_SPECS["y"]),
        "z": trapezoidal_time(q_to.z - q_from.z, LINEAR_AXIS_SPECS["z"]),
        "pan": trapezoidal_time(q_to.pan_deg - q_from.pan_deg, GIMBAL_AXIS_SPECS["pan"]),
        "tilt": trapezoidal_time(q_to.tilt_deg - q_from.tilt_deg, GIMBAL_AXIS_SPECS["tilt"]),
    }


def move_time(q_from: JointState, q_to: JointState) -> float:
    return max(per_axis_times(q_from, q_to).values())


def demonstrate_asymmetry() -> Dict:
    full_rail_m = 1.2
    full_reach_m = 0.75
    full_lift_m = 0.45
    full_pan_deg = 110.0
    full_tilt_deg = 70.0
    return {
        "full_rail_traverse_s": trapezoidal_time(full_rail_m, LINEAR_AXIS_SPECS["x"]),
        "full_reach_traverse_s": trapezoidal_time(full_reach_m, LINEAR_AXIS_SPECS["y"]),
        "full_lift_traverse_s": trapezoidal_time(full_lift_m, LINEAR_AXIS_SPECS["z"]),
        "full_pan_sweep_s": trapezoidal_time(full_pan_deg, GIMBAL_AXIS_SPECS["pan"]),
        "full_tilt_sweep_s": trapezoidal_time(full_tilt_deg, GIMBAL_AXIS_SPECS["tilt"]),
    }
