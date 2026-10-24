"""
T1.4 -- Export depth via `writeDepthImageDataEXR`, real lossless-float EXR
files on disk.

Per the task doc: there is no in-memory depth getter for the radiation
camera in PyHelios (only the three file writers: text, EXR,
normalized-JPEG), and `Visualizer.getDepthMap()` is a separate,
upstream-broken path (returns only {0.0, 255.0} -- see Phase 0's
`PHASE0_LOG.md` T0.7 finding). This module uses the EXR writer
specifically because it is the one Python-reachable path that preserves
full float precision, and reads it back with the `OpenEXR` package
(installed into the `helios` conda env via pip for this task -- neither
`OpenEXR` nor `imageio`'s EXR support were present beforehand; see
PHASE1_LOG.md).
"""

import os

import numpy as np
import OpenEXR


def export_depth_exr(radiation, camera_label, output_dir, view_name):
    """Write one camera's current depth buffer to `{output_dir}/{camera_label}_{view_name}.exr`.

    Must be called after `updateGeometry()` + `runBand()` for the pose this
    camera is currently at (same requirement as the label-map writers).
    Returns the EXR filepath actually written.
    """
    os.makedirs(output_dir, exist_ok=True)
    radiation.writeDepthImageDataEXR(camera_label, view_name, image_path=output_dir + os.sep)
    return os.path.join(output_dir, f"{camera_label}_{view_name}.exr")


def read_depth_exr(filepath):
    """Read a depth EXR file back into a (H,W) float32 NumPy array."""
    f = OpenEXR.File(filepath)
    channels = f.channels()
    # helios::writeEXR (helios-core) writes a single-channel image; the
    # channel name isn't guaranteed across OpenEXR-writer versions, so pick
    # 'Z' if present (depth convention) else whatever the sole channel is.
    if "Z" in channels:
        key = "Z"
    else:
        key = next(iter(channels.keys()))
    return np.array(channels[key].pixels, dtype=np.float32)


SKY_DEPTH_SENTINEL = -1.0
# Empirically confirmed (not documented anywhere in the task doc or
# PyHelios docstrings): pixels where the primary camera ray hits no
# geometry ("sky") get depth EXACTLY -1.0, not some large far-plane value.
# Verified pixel-for-pixel identical to the semantic label map's NaN
# (background) mask on a real render -- see PHASE1_LOG.md T1.4 section.


def depth_stats(depth, valid_mask=None):
    """Summary stats for logging -- min/max/mean over real (non-sky) depth
    pixels. `valid_mask` should be the semantic/instance label map's
    ~isnan() mask (same ray-hit-topology pass, guaranteed pixel-aligned);
    if omitted, falls back to excluding the known -1.0 sky sentinel."""
    if valid_mask is None:
        valid_mask = depth != SKY_DEPTH_SENTINEL
    valid = depth[valid_mask]
    if valid.size == 0:
        return {"min": None, "max": None, "mean": None, "n_pixels": int(depth.size), "n_valid": 0}
    return {
        "min": float(valid.min()),
        "max": float(valid.max()),
        "mean": float(valid.mean()),
        "n_pixels": int(depth.size),
        "n_valid": int(valid.size),
        "sky_fraction": float(1.0 - valid.size / depth.size),
    }
