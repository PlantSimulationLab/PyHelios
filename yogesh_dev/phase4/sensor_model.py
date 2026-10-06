"""
Shared camera projection / beam-sensor utilities for Phase 4.

The exact pixel <-> world-ray convention used by PyHelios's RadiationCamera
is not documented anywhere Python-visible, and `helios-core` C++ source is
not checked out in this worktree (submodule never initialized here) to read
directly. Rather than guess, the convention below was CALIBRATED EMPIRICALLY
against real rendered data (see PHASE4_LOG.md "Camera projection convention"
section for the full method and numbers: 8 real (view, fruit) pairs,
mean centroid-reconstruction error 3.7cm using this convention vs
>=7.3cm for the next-best sign/mode combination, with the residual 3-4cm
explained by sphere-surface-vs-center offset, not calibration error).
`self_test()` at the bottom reproduces that calibration check so it stays
runnable/falsifiable rather than a one-off finding.

Convention:
  - world up = (0,0,1); camera right r = normalize(forward x world_up);
    camera up u = r x forward.
  - pixel (row, col), resolution (W,H): x_ndc = (col - W/2)/fl_x,
    y_ndc = (H/2 - row)/fl_y  (row 0 = top of array = "up" in world).
  - fl_x = 0.5*W/tan(HFOV/2), fl_y = 0.5*H/tan(VFOV/2), VFOV=45deg fixed
    (matches `gen_dataset.py`'s `build_camera_properties`).
  - depth EXR value is PLANE depth (distance along forward axis), not
    Euclidean range: world point = eye + d*(x_ndc*r + y_ndc*u + forward).
  - sky/no-hit sentinel = exactly -1.0.
"""

import math
import os

import numpy as np

VFOV_DEG = 45.0
SKY_DEPTH_SENTINEL = -1.0
WORLD_UP = np.array([0.0, 0.0, 1.0])


def camera_basis(eye, lookat):
    eye = np.asarray(eye, dtype=float)
    lookat = np.asarray(lookat, dtype=float)
    f = lookat - eye
    f = f / np.linalg.norm(f)
    r = np.cross(f, WORLD_UP)
    r = r / np.linalg.norm(r)
    u = np.cross(r, f)
    return f, r, u


def intrinsics(resolution, vfov_deg=VFOV_DEG):
    W, H = resolution
    fl_y = 0.5 * H / math.tan(math.radians(vfov_deg) / 2.0)
    aspect = W / H
    hfov_deg = math.degrees(2.0 * math.atan(aspect * math.tan(math.radians(vfov_deg) / 2.0)))
    fl_x = 0.5 * W / math.tan(math.radians(hfov_deg) / 2.0)
    return {"fl_x": fl_x, "fl_y": fl_y, "cx": W / 2.0, "cy": H / 2.0,
            "W": W, "H": H, "hfov_deg": hfov_deg, "vfov_deg": vfov_deg}


def pixel_angular_size(intr):
    """Angular width of one pixel (radians), used as the beam's angular
    uncertainty for T4.1's beam sensor model footprint."""
    return 1.0 / intr["fl_x"], 1.0 / intr["fl_y"]


def unproject(rows, cols, depth_plane, eye, f, r, u, intr):
    """Vectorized pixel+plane-depth -> world-point unprojection.

    rows, cols, depth_plane: 1D arrays of equal length.
    Returns (N,3) world points.
    """
    rows = np.asarray(rows, dtype=float)
    cols = np.asarray(cols, dtype=float)
    depth_plane = np.asarray(depth_plane, dtype=float)
    x_ndc = (cols - intr["cx"]) / intr["fl_x"]
    y_ndc = (intr["cy"] - rows) / intr["fl_y"]
    ray = x_ndc[:, None] * r[None, :] + y_ndc[:, None] * u[None, :] + f[None, :]
    return np.asarray(eye, dtype=float)[None, :] + depth_plane[:, None] * ray


def unproject_grid(depth, eye, f, r, u, intr, valid_mask=None):
    """Unproject an entire (H,W) depth image at once. Returns (points, rows, cols)
    where points is (M,3) for the M valid (non-sky) pixels, rows/cols are
    their (int) pixel coordinates."""
    H, W = depth.shape
    if valid_mask is None:
        valid_mask = depth != SKY_DEPTH_SENTINEL
    rows, cols = np.nonzero(valid_mask)
    pts = unproject(rows, cols, depth[rows, cols], eye, f, r, u, intr)
    return pts, rows, cols


def project_point(point, eye, f, r, u, intr):
    """World point -> (row, col, plane_depth, in_front). Not clipped to the
    image bounds -- caller checks in_frustum via row/col range."""
    X = np.asarray(point, dtype=float) - np.asarray(eye, dtype=float)
    depth = float(np.dot(X, f))
    if depth <= 1e-9:
        return None, None, depth, False
    x_cam = float(np.dot(X, r))
    y_cam = float(np.dot(X, u))
    x_ndc = x_cam / depth
    y_ndc = y_cam / depth
    col = intr["cx"] + x_ndc * intr["fl_x"]
    row = intr["cy"] - y_ndc * intr["fl_y"]
    return row, col, depth, True


def in_frustum(row, col, intr):
    return row is not None and 0.0 <= row < intr["H"] and 0.0 <= col < intr["W"]


def self_test(data_dir):
    """Reproduce the empirical calibration check documented in
    PHASE4_LOG.md, using the real generated dataset. Returns the winning
    combo's mean/max reconstruction error (meters) as a sanity check that
    can be re-run any time the dataset is regenerated."""
    import json
    import OpenEXR

    poses = json.load(open(os.path.join(data_dir, "poses.json")))
    fruit = json.load(open(os.path.join(data_dir, "fruit_ground_truth.json")))
    report = json.load(open(os.path.join(data_dir, "gen_report.json")))
    intr = intrinsics(tuple(report["resolution"]))
    oid_to_centroid = {rec["object_id"]: np.array(rec["centroid"]) for rec in fruit}

    def read_depth(path):
        fh = OpenEXR.File(path)
        ch = fh.channels()
        key = "Z" if "Z" in ch else next(iter(ch.keys()))
        return np.array(ch[key].pixels, dtype=np.float32)

    cands = []
    for p in poses:
        inst = np.load(os.path.join(data_dir, p["instance_path"]))
        vals, counts = np.unique(inst, return_counts=True)
        for v, c in zip(vals, counts):
            if v > 0 and c > 300:
                cands.append((p, int(v), int(c)))
    cands.sort(key=lambda t: -t[2])
    cands = cands[:8]

    errs = []
    for p, oid, _cnt in cands:
        inst = np.load(os.path.join(data_dir, p["instance_path"]))
        depth = read_depth(os.path.join(data_dir, p["depth_path"]))
        mask = inst == oid
        rows, cols = np.nonzero(mask)
        d = depth[rows, cols]
        valid = d > 0
        rows, cols, d = rows[valid], cols[valid], d[valid]
        if len(d) < 20:
            continue
        eye = np.array(p["eye"])
        f, r, u = camera_basis(eye, p["lookat"])
        pts = unproject(rows, cols, d, eye, f, r, u, intr)
        err = float(np.linalg.norm(pts.mean(axis=0) - oid_to_centroid[oid]))
        errs.append(err)
    return {"n_pairs": len(errs), "mean_err_m": float(np.mean(errs)), "max_err_m": float(np.max(errs))}


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    result = self_test(os.path.join(HERE, "data"))
    print("Camera calibration self-test:", result)
    assert result["mean_err_m"] < 0.06, "calibration regression -- check sign/mode convention"
