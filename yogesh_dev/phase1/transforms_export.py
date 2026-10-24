"""
T1.5 -- Camera intrinsics/extrinsics per view, written to a gsplat-compatible
`transforms.json`.

Reuses, rather than re-derives, the pose convention validated sub-pixel
accurate in Phase 0 T0.3 (`yogesh_dev/phase0/pose_convention.py`:
`look_at_view_matrix` / `intrinsics_matrix`) and the exact top-level field
names (`camera_model`, `width`, `height`, `fl_x`, `fl_y`, `cx`, `cy`,
`frames[].transform_matrix`) used by the existing `apple_tree_gaussian_splatting.py`
pipeline (see `git show apple-tree-cameras:apple_tree_gaussian_splatting.py`),
so the existing gsplat training code still runs unmodified against this
output. `transform_matrix` is camera-to-world (`inv(viewmat)`), matching that
script's convention exactly.

Extends the format (doesn't replace it) with: `hfov_deg`, a `pose_convention`
note, and per-frame `camera_label`, `plant_id`, `world_to_camera_matrix`, and
paths to the other T1.2-T1.4 ground-truth artifacts for that same view.
"""

import json

import numpy as np

from yogesh_dev.phase0.pose_convention import look_at_view_matrix, intrinsics_matrix

POSE_CONVENTION_NOTE = (
    "World-to-camera matrix is OpenCV convention (X-right, Y-down, Z-forward), "
    "world_up=(0,0,1), standard top-left-origin pixel indexing (row=v, col=u). "
    "Empirically validated sub-pixel accurate (<1px mean reprojection error) "
    "against the RadiationCamera in Phase 0 T0.3 using two independent poses "
    "(axis-aligned and off-axis) -- see PHASE0_LOG.md. transform_matrix (per "
    "frame) is camera-to-world = inv(world_to_camera_matrix)."
)


def build_transforms(hfov_deg, resolution, frames_info):
    """
    Args:
        hfov_deg: horizontal FOV in degrees (same for every camera in this rig).
        resolution: (width, height).
        frames_info: list of dicts, each with at least:
            eye (vec3), lookat (vec3), file_path (str, rgb image path,
            relative to the transforms.json location), camera_label (str),
            plant_id (int), split (str, optional, default "train"), plus any
            extra keys (depth_path, semantic_path, instance_path, ...) which
            are passed through verbatim onto the frame record.

    Returns the transforms dict (not yet written to disk).
    """
    width, height = resolution
    K = intrinsics_matrix(width, height, hfov_deg)

    frames = []
    for info in frames_info:
        viewmat = look_at_view_matrix(info["eye"], info["lookat"])
        c2w = np.linalg.inv(viewmat)
        frame = {
            "file_path": info["file_path"],
            "camera_label": info["camera_label"],
            "plant_id": info["plant_id"],
            "transform_matrix": c2w.tolist(),
            "world_to_camera_matrix": viewmat.tolist(),
            "split": info.get("split", "train"),
        }
        for key, value in info.items():
            if key not in frame and key not in ("eye", "lookat"):
                frame[key] = value
        frames.append(frame)

    return {
        "camera_model": "PINHOLE",
        "width": width,
        "height": height,
        "fl_x": float(K[0, 0]),
        "fl_y": float(K[1, 1]),
        "cx": float(K[0, 2]),
        "cy": float(K[1, 2]),
        "hfov_deg": hfov_deg,
        "pose_convention": POSE_CONVENTION_NOTE,
        "frames": frames,
    }


def write_transforms(transforms, output_path):
    with open(output_path, "w") as f:
        json.dump(transforms, f, indent=2)
