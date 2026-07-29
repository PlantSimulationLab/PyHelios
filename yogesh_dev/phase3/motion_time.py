"""
T3.3 -- Execution-time model: trapezoidal velocity profile per axis.

No real hardware is available yet, so max velocity / acceleration below are
PLACEHOLDER, CLEARLY-LABELED numbers modeled loosely on typical linear-stage
(ballscrew/belt-driven gantry) and RC-servo-gimbal actuator datasheets for
small agricultural manipulators. Replace every number in LINEAR_AXIS_SPECS
and GIMBAL_AXIS_SPECS with real measurements before trusting any absolute
timing number produced here -- only the RELATIVE structure (gimbal orders of
magnitude cheaper than the linear stages) is meant to be trustworthy today.

That asymmetry is not cosmetic: it is exactly what the design doc's nested
planner idea depends on (cheap gimbal refinement inside an expensive linear
reposition). A full-range gimbal sweep is sub-second; a full-rail linear
traverse is tens of seconds -- see `demonstrate_asymmetry()`.

Trapezoidal velocity profile, standard result for point-to-point motion
under constant acceleration limits:
    d_accel = v_max^2 / (2*a_max)          -- distance to reach v_max
    if 2*d_accel <= d (reaches cruise speed):
        t = 2*(v_max/a_max) + (d - 2*d_accel)/v_max
    else (triangular profile, never reaches v_max):
        t = 2*sqrt(d/a_max)
"""

import math
from dataclasses import dataclass
from typing import Dict

from .kinematics import JointState


@dataclass(frozen=True)
class AxisSpec:
    name: str
    v_max: float  # m/s for linear axes, deg/s for pan/tilt
    a_max: float  # m/s^2 for linear axes, deg/s^2 for pan/tilt


# --- PLACEHOLDER hardware numbers -- see module docstring. Real values TBD. ---
LINEAR_AXIS_SPECS: Dict[str, AxisSpec] = {
    "x": AxisSpec("x_rail", v_max=0.30, a_max=0.50),      # long-travel gantry, heaviest carried mass
    "y": AxisSpec("y_extend", v_max=0.20, a_max=0.40),    # reach arm into/out of canopy
    "z": AxisSpec("z_lift", v_max=0.25, a_max=0.40),      # vertical lift stage
}

GIMBAL_AXIS_SPECS: Dict[str, AxisSpec] = {
    "pan": AxisSpec("pan", v_max=180.0, a_max=400.0),     # servo-driven, ~2 orders of magnitude cheaper
    "tilt": AxisSpec("tilt", v_max=180.0, a_max=400.0),
}


def trapezoidal_time(distance: float, spec: AxisSpec) -> float:
    """Time to traverse `distance` (same units as spec.v_max) under a
    trapezoidal (or, if too short to reach v_max, triangular) velocity
    profile with the given max velocity/acceleration."""
    d = abs(distance)
    if d == 0.0:
        return 0.0
    v_max, a_max = spec.v_max, spec.a_max
    d_accel = (v_max ** 2) / (2.0 * a_max)
    if 2.0 * d_accel <= d:
        return 2.0 * (v_max / a_max) + (d - 2.0 * d_accel) / v_max
    return 2.0 * math.sqrt(d / a_max)


def per_axis_times(q_from: JointState, q_to: JointState) -> Dict[str, float]:
    """Per-axis trapezoidal move time, before taking the max across axes."""
    return {
        "x": trapezoidal_time(q_to.x - q_from.x, LINEAR_AXIS_SPECS["x"]),
        "y": trapezoidal_time(q_to.y - q_from.y, LINEAR_AXIS_SPECS["y"]),
        "z": trapezoidal_time(q_to.z - q_from.z, LINEAR_AXIS_SPECS["z"]),
        "pan": trapezoidal_time(q_to.pan_deg - q_from.pan_deg, GIMBAL_AXIS_SPECS["pan"]),
        "tilt": trapezoidal_time(q_to.tilt_deg - q_from.tilt_deg, GIMBAL_AXIS_SPECS["tilt"]),
    }


def move_time(q_from: JointState, q_to: JointState) -> float:
    """Total execution time for a joint-to-joint move.

    Assumes all 5 axes move SIMULTANEOUSLY (synchronized start/stop is not
    modeled -- each axis just runs its own trapezoidal profile independently)
    and the move completes when the SLOWEST axis finishes, i.e.
    total_time = max(per-axis times). This is the standard simplification for
    multi-axis move-time estimation and is what makes the T3.4 roadmap edge
    weights meaningful without needing a full multi-axis motion coordinator.
    """
    return max(per_axis_times(q_from, q_to).values())


def demonstrate_asymmetry() -> Dict:
    """Concrete numbers showing the linear-vs-gimbal cost asymmetry that
    motivates the nested-planner idea: a full-range single-axis move on each
    stage, plus a full-range gimbal move, using ONLY the specs above (no
    joint-limit-specific numbers) -- see run_phase3_demo.py for the same
    comparison using the actual arm joint-limit ranges.
    """
    full_rail_m = 4.5      # matches default_arm_configs x range width (3.75 - (-0.75))
    full_reach_m = 1.05    # matches default y range width (-0.05 - (-1.10))
    full_lift_m = 0.45     # matches one z band's width
    full_pan_deg = 110.0   # matches default pan range width (55 - (-55))
    full_tilt_deg = 70.0   # matches default tilt range width (35 - (-35))

    return {
        "full_rail_traverse_s": trapezoidal_time(full_rail_m, LINEAR_AXIS_SPECS["x"]),
        "full_reach_traverse_s": trapezoidal_time(full_reach_m, LINEAR_AXIS_SPECS["y"]),
        "full_lift_traverse_s": trapezoidal_time(full_lift_m, LINEAR_AXIS_SPECS["z"]),
        "full_pan_sweep_s": trapezoidal_time(full_pan_deg, GIMBAL_AXIS_SPECS["pan"]),
        "full_tilt_sweep_s": trapezoidal_time(full_tilt_deg, GIMBAL_AXIS_SPECS["tilt"]),
    }
