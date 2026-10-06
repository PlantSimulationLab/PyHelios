"""
W2 -- Action spaces and trajectory samplers.

## Camera state and the view action

A camera state is 4-D: `(x, y, z, yaw)`. Pitch is fixed per episode (recorded in
the episode metadata, not part of the action) and roll is always zero, because
`addRadiationCamera` takes only position + lookat and exposes no up-vector /
roll control (a known PyHelios limitation, listed in COMPLETE_SETUP.md's upstream
patch list). So a 4-D state is exactly what the simulator can actually express --
adding a pitch action would mean recording an action the rig cannot execute.

The view action is the state delta to the NEXT frame:

    a_view[t] = (x[t+1]-x[t], y[t+1]-y[t], z[t+1]-z[t], wrap(yaw[t+1]-yaw[t]))

`wrap` maps to (-pi, pi], so replaying actions from the start state reproduces
the trajectory exactly (verified to < 1e-6 in `run_w2.py`, which is this task's
acceptance criterion). The last frame of an episode has a zero action.

## Why the lane is narrow (measured, not assumed)

W0 measured the real orchard bounding box at age 720 d, seed 10000:
    x in [-7.78, 7.86], y in [-3.09, 3.12], z in [0.00, 2.79]
Tree bases sit at y = -1.75 and y = +1.75, so the canopy half-width is
~1.34 m and the two rows leave a free inter-row lane of only about
2*(1.75-1.34) = 0.82 m. `LANE_HALF_WIDTH` below is derived from that, not
guessed, and `run_w2.py` re-measures it per orchard rather than hard-coding it.

## Trajectory families

- `row_traversal` -- drive along the lane (+x or -x), yaw held near across-row
  with a small forward lean and a slow sinusoidal scan. This is the realistic
  robot path.
- `orbit` -- circle one tree at a fixed radius, yaw always pointing at the tree.
  Orbits necessarily leave the lane; for interior trees they also pass through
  neighbouring canopy volume. Helios cameras have no collision, so this is
  physically unrealisable but geometrically well-defined; `orbit_intrusion()`
  measures what fraction of an orbit's poses fall inside a canopy cylinder so
  the number is reported rather than hidden.
- `random_walk` -- bounded jitter inside the lane, for coverage of the action
  space. Reflecting boundaries, so every sample is in-bounds by construction.

## Growth actions

`a_grow` is a scalar `dt` in days handed to `plantarch.advanceTime(dt)`. See
`GROWTH_SCHEDULE` and the W0/W0b findings for why the usable window is narrow.
"""

import math

import numpy as np

# Derived from W0's measured bounding box (see module docstring).
CANOPY_HALF_WIDTH_M = 1.34
LANE_HALF_WIDTH = 0.35          # conservative: 0.82/2 = 0.41 free, keep 0.35
CAMERA_Z_MIN = 0.45
CAMERA_Z_MAX = 2.20
DEFAULT_PITCH_DEG = -5.0        # slight downward tilt, like a mast-mounted camera
FOCAL_LEN = 1.0                 # distance from eye to lookat point (arbitrary > 0)

TRAJECTORY_FAMILIES = ("row_traversal", "orbit", "random_walk")

# Growth schedule. W0/W0b measured the apple model's fruit window; anything
# outside it contains zero fruit, which would make the fruit-visibility decoder
# head untrainable. Set by run_w0b.py's measured curve, not by assumption.
GROWTH_SCHEDULE = {
    "fruiting_window_days": (560.0, 780.0),
    "note": "measured in W0b; see output/w0/w0b_age_curve.json",
}


def wrap_angle(a):
    """Map angle(s) to (-pi, pi]."""
    return (np.asarray(a, dtype=np.float64) + np.pi) % (2 * np.pi) - np.pi


# ---------------------------------------------------------------------------
# state <-> pose
# ---------------------------------------------------------------------------
def state_to_pose(state, pitch_deg=DEFAULT_PITCH_DEG, focal_len=FOCAL_LEN):
    """(x,y,z,yaw) -> (eye, lookat) tuples of floats."""
    x, y, z, yaw = [float(v) for v in state]
    p = math.radians(pitch_deg)
    d = (math.cos(p) * math.cos(yaw), math.cos(p) * math.sin(yaw), math.sin(p))
    eye = (x, y, z)
    lookat = (x + focal_len * d[0], y + focal_len * d[1], z + focal_len * d[2])
    return eye, lookat


def states_to_poses(states, pitch_deg=DEFAULT_PITCH_DEG, focal_len=FOCAL_LEN):
    return [state_to_pose(s, pitch_deg, focal_len) for s in states]


# ---------------------------------------------------------------------------
# action encoding / decoding
# ---------------------------------------------------------------------------
def states_to_actions(states):
    """(T,4) states -> (T,4) actions; action[t] is the delta to state[t+1].
    The final action is all-zero (no next state)."""
    s = np.asarray(states, dtype=np.float64)
    a = np.zeros_like(s)
    if len(s) > 1:
        a[:-1, :3] = s[1:, :3] - s[:-1, :3]
        a[:-1, 3] = wrap_angle(s[1:, 3] - s[:-1, 3])
    return a.astype(np.float32)


def actions_to_states(start_state, actions):
    """Inverse of `states_to_actions`: replay actions from a start state.

    Yaw is accumulated then wrapped, so it matches the original wrapped yaw. The
    acceptance test in run_w2.py compares this against the recorded states and
    requires max error < 1e-6.
    """
    a = np.asarray(actions, dtype=np.float64)
    s = np.zeros_like(a)
    s[0] = np.asarray(start_state, dtype=np.float64)
    for t in range(1, len(a)):
        s[t, :3] = s[t - 1, :3] + a[t - 1, :3]
        s[t, 3] = wrap_angle(s[t - 1, 3] + a[t - 1, 3])
    return s


def state_error(a, b):
    """Max abs error between two state arrays, yaw compared modulo 2pi."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    pos = np.abs(a[:, :3] - b[:, :3]).max()
    yaw = np.abs(wrap_angle(a[:, 3] - b[:, 3])).max()
    return float(max(pos, yaw))


# ---------------------------------------------------------------------------
# bounds
# ---------------------------------------------------------------------------
def lane_bounds(ext, lane_half=LANE_HALF_WIDTH, x_margin=0.5):
    """Free-space box for lane trajectories, from the orchard's planting grid."""
    return {
        "x": (ext["x_min"] - x_margin, ext["x_max"] + x_margin),
        "y": (ext["lane_y"] - lane_half, ext["lane_y"] + lane_half),
        "z": (CAMERA_Z_MIN, CAMERA_Z_MAX),
    }


def in_lane(states, bounds):
    """Boolean array: is each state inside the lane box?"""
    s = np.asarray(states, dtype=np.float64)
    ok = np.ones(len(s), dtype=bool)
    for i, k in enumerate("xyz"):
        lo, hi = bounds[k]
        ok &= (s[:, i] >= lo - 1e-9) & (s[:, i] <= hi + 1e-9)
    return ok


def orbit_intrusion(states, ext, canopy_radius=CANOPY_HALF_WIDTH_M):
    """Fraction of orbit poses that fall inside SOME tree's canopy cylinder.

    Reported honestly rather than prevented: Helios radiation cameras have no
    collision, so an orbit around an interior tree unavoidably passes through
    neighbouring canopy. This number quantifies how physically unrealisable a
    given orbit is.
    """
    s = np.asarray(states, dtype=np.float64)[:, :2]
    centers = np.array([[tx, ry] for ry in ext["row_y"] for tx in ext["tree_x"]])
    d = np.linalg.norm(s[:, None, :] - centers[None, :, :], axis=2)
    return float((d.min(axis=1) < canopy_radius).mean())


# ---------------------------------------------------------------------------
# trajectory samplers
# ---------------------------------------------------------------------------
def sample_row_traversal(n_steps, ext, rng, lane_half=LANE_HALF_WIDTH):
    """Drive down the lane. Randomised: direction, start offset, speed, target
    row, lateral offset, height, and the amplitude/phase of a slow yaw scan."""
    b = lane_bounds(ext, lane_half)
    direction = 1.0 if rng.random() < 0.5 else -1.0
    span = b["x"][1] - b["x"][0]
    # cover 60-100% of the row, at a constant speed
    frac = rng.uniform(0.6, 1.0)
    length = span * frac
    x0 = rng.uniform(b["x"][0], b["x"][1] - length) if direction > 0 else \
        rng.uniform(b["x"][0] + length, b["x"][1])
    xs = x0 + direction * np.linspace(0.0, length, n_steps)

    y0 = rng.uniform(*b["y"])
    y_amp = rng.uniform(0.0, min(0.12, lane_half))
    ys = np.clip(y0 + y_amp * np.sin(np.linspace(0, rng.uniform(1, 3) * np.pi, n_steps)),
                 b["y"][0], b["y"][1])

    z0 = rng.uniform(0.7, 1.8)
    z_amp = rng.uniform(0.0, 0.25)
    zs = np.clip(z0 + z_amp * np.sin(np.linspace(0, rng.uniform(0.5, 2) * np.pi, n_steps)),
                 b["z"][0], b["z"][1])

    # Look at one row (+/- pi/2 in world yaw), with a forward lean and a slow scan.
    row_sign = 1.0 if rng.random() < 0.5 else -1.0
    base_yaw = row_sign * np.pi / 2.0
    lean = rng.uniform(-0.5, 0.5) * direction
    scan_amp = rng.uniform(0.0, 0.5)
    yaws = wrap_angle(base_yaw + lean
                      + scan_amp * np.sin(np.linspace(0, rng.uniform(1, 4) * np.pi, n_steps)))

    return np.stack([xs, ys, zs, yaws], axis=1).astype(np.float64)


def sample_orbit(n_steps, ext, rng):
    """Circle one tree. Yaw always points at the tree centre."""
    tx = float(rng.choice(ext["tree_x"]))
    ty = float(rng.choice(ext["row_y"]))
    radius = float(rng.uniform(1.6, 2.6))
    sweep = float(rng.uniform(np.pi * 0.5, 2 * np.pi))
    theta0 = float(rng.uniform(0, 2 * np.pi))
    sgn = 1.0 if rng.random() < 0.5 else -1.0
    thetas = theta0 + sgn * np.linspace(0.0, sweep, n_steps)
    xs = tx + radius * np.cos(thetas)
    ys = ty + radius * np.sin(thetas)
    z0 = float(rng.uniform(0.8, 1.9))
    zs = np.clip(z0 + rng.uniform(0.0, 0.3) * np.sin(np.linspace(0, np.pi, n_steps)),
                 CAMERA_Z_MIN, CAMERA_Z_MAX)
    yaws = wrap_angle(np.arctan2(ty - ys, tx - xs))
    return np.stack([xs, ys, zs, yaws], axis=1).astype(np.float64)


def sample_random_walk(n_steps, ext, rng, lane_half=LANE_HALF_WIDTH):
    """Bounded random walk inside the lane, reflecting at the boundaries so
    every sample is in-bounds by construction (no rejection, no clipping bias
    at the walls beyond the reflection itself)."""
    b = lane_bounds(ext, lane_half)
    step = np.array([rng.uniform(0.06, 0.20), rng.uniform(0.01, 0.05),
                     rng.uniform(0.01, 0.05), rng.uniform(0.02, 0.12)])
    s = np.array([rng.uniform(*b["x"]), rng.uniform(*b["y"]), rng.uniform(*b["z"]),
                  rng.uniform(-np.pi, np.pi)])
    out = np.zeros((n_steps, 4))
    out[0] = s
    for t in range(1, n_steps):
        d = rng.normal(0.0, 1.0, 4) * step
        nxt = out[t - 1] + d
        for i, k in enumerate("xyz"):
            lo, hi = b[k]
            v = nxt[i]
            # reflect (possibly multiple times for a large step)
            for _ in range(4):
                if v < lo:
                    v = 2 * lo - v
                elif v > hi:
                    v = 2 * hi - v
                else:
                    break
            nxt[i] = min(max(v, lo), hi)
        nxt[3] = wrap_angle(nxt[3])
        out[t] = nxt
    return out


SAMPLERS = {
    "row_traversal": sample_row_traversal,
    "orbit": sample_orbit,
    "random_walk": sample_random_walk,
}


def sample_trajectory(family, n_steps, ext, seed):
    """Seeded trajectory sample. Returns (states (T,4), actions (T,4), meta)."""
    if family not in SAMPLERS:
        raise ValueError(f"unknown family {family!r}, expected one of {TRAJECTORY_FAMILIES}")
    rng = np.random.default_rng(int(seed))
    states = SAMPLERS[family](int(n_steps), ext, rng)
    actions = states_to_actions(states)
    meta = {"family": family, "n_steps": int(n_steps), "traj_seed": int(seed)}
    return states, actions, meta


def action_stats(actions):
    a = np.asarray(actions, dtype=np.float64)
    live = a[:-1] if len(a) > 1 else a
    return {
        "n": int(len(a)),
        "abs_mean": live.__abs__().mean(axis=0).tolist(),
        "abs_max": live.__abs__().max(axis=0).tolist(),
        "std": live.std(axis=0).tolist(),
    }
