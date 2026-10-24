"""
T7.1 -- Helios -> WAI dataset writer.

WAI ("World As Images", MapAnything's training data format --
facebookresearch/map-anything, `data_processing/README.md`) real spec,
looked up rather than guessed (see PHASE7_LOG.md for the source):

    <dataset_name>/<scene_name>/
        scene_meta.json
        images/<frame_name>.png
        depth/<frame_name>.exr        (optional modality)
        masks/<frame_name>.png        (optional modality)

    scene_meta.json root fields: scene_name, dataset_name, version,
    last_modified, shared_intrinsics, camera_model, camera_convention
    ("opencv"), fl_x, fl_y, cx, cy, w, h, scene_modalities,
    frame_modalities.

    Each frames[] entry: frame_name, file_path, transform_matrix (4x4
    flattened, camera-to-world, OpenCV convention), <modality>_path per
    optional modality present for that frame.

This project's `camera_convention` is ALREADY OpenCV (X-right, Y-down,
Z-forward, world_up=+Z) -- empirically validated sub-pixel accurate in
Phase 0 T0.3 (`pose_convention.py`) -- so `transform_matrix` here is
exactly that validated `look_at_view_matrix`'s inverse, matching WAI's
`camera_convention: "opencv"` requirement with no re-derivation needed.

One writer, every later experiment: `write_wai_scene` is called directly
by T7.3/T7.4/T7.5/T7.6/T7.7's render passes to persist their own view
sets in this same format (not just a one-off demo dataset) -- "one loader
serves every later experiment" per the task doc.
"""

import datetime
import json
import os

import numpy as np

from yogesh_dev.phase0.pose_convention import intrinsics_matrix, look_at_view_matrix

FORMAT_VERSION = "0.1"


def write_wai_scene(radiation, labels, poses, hfov_deg, resolution, output_dir,
                     dataset_name, scene_name, write_rgb=True, write_depth=True,
                     write_semantic_mask=True, frame_names=None, extra_frame_fields=None):
    """Persist one already-rendered (after runBand()) set of camera views as
    one WAI scene. Returns the scene_meta dict (also written to disk).

    `extra_frame_fields`: optional list (same length/order as `labels`) of
    dicts merged into each frame's metadata verbatim (e.g. azimuth_deg,
    split, plant_id) -- lets sweep experiments tag WAI frames with their
    own experiment parameters without WAI itself needing to know about them.
    """
    scene_dir = os.path.join(output_dir, dataset_name, scene_name)
    images_dir = os.path.join(scene_dir, "images")
    depth_dir = os.path.join(scene_dir, "depth")
    masks_dir = os.path.join(scene_dir, "masks")
    os.makedirs(images_dir, exist_ok=True)
    if write_depth:
        os.makedirs(depth_dir, exist_ok=True)
    if write_semantic_mask:
        os.makedirs(masks_dir, exist_ok=True)

    W, H = resolution
    K = intrinsics_matrix(W, H, hfov_deg)

    if frame_names is None:
        frame_names = [f"frame_{i:05d}" for i in range(len(labels))]

    frames = []
    for i, (label, (eye, lookat)) in enumerate(zip(labels, poses)):
        frame_name = frame_names[i]
        viewmat = look_at_view_matrix(eye, lookat)
        c2w = np.linalg.inv(viewmat)

        frame = {
            "frame_name": frame_name,
            "camera_label": label,
            "transform_matrix": c2w.flatten().tolist(),
            "world_to_camera_matrix": viewmat.flatten().tolist(),
            "eye": [eye.x, eye.y, eye.z],
            "lookat": [lookat.x, lookat.y, lookat.z],
        }

        if write_rgb:
            from yogesh_dev.phase0.radiation_cameras import RGB_BAND_LABELS
            rgb_path = radiation.writeCameraImage(
                camera=label, bands=list(RGB_BAND_LABELS), imagefile_base=frame_name,
                image_path=images_dir + os.sep, flux_to_pixel_conversion=1.0,
            )
            frame["file_path"] = os.path.relpath(rgb_path, scene_dir)

        if write_depth:
            radiation.writeDepthImageDataEXR(label, frame_name, image_path=depth_dir + os.sep)
            written_depth_path = os.path.join(depth_dir, f"{label}_{frame_name}.exr")
            canonical_depth_path = os.path.join(depth_dir, f"{frame_name}.exr")
            if os.path.exists(written_depth_path) and written_depth_path != canonical_depth_path:
                os.replace(written_depth_path, canonical_depth_path)
            frame["depth_path"] = os.path.relpath(canonical_depth_path, scene_dir)

        if write_semantic_mask:
            from yogesh_dev.phase1.label_maps import SEMANTIC_CLASS_ID_FIELD
            semantic = radiation.getPrimitiveDataLabelMap(label, SEMANTIC_CLASS_ID_FIELD)
            mask_path = os.path.join(masks_dir, f"{frame_name}.npy")
            np.save(mask_path, semantic)
            frame["mask_path"] = os.path.relpath(mask_path, scene_dir)

        if extra_frame_fields is not None:
            frame.update(extra_frame_fields[i])

        frames.append(frame)

    scene_modalities = {}
    frame_modalities = {}
    if write_rgb:
        frame_modalities["image"] = {"frame_key": "file_path", "format": "image"}
    if write_depth:
        frame_modalities["depth"] = {"frame_key": "depth_path", "format": "depth_exr_plane"}
    if write_semantic_mask:
        frame_modalities["semantic_mask"] = {"frame_key": "mask_path", "format": "npy_int_labelmap"}

    scene_meta = {
        "scene_name": scene_name,
        "dataset_name": dataset_name,
        "version": FORMAT_VERSION,
        "last_modified": datetime.datetime.utcnow().isoformat() + "Z",
        "shared_intrinsics": True,
        "camera_model": "PINHOLE",
        "camera_convention": "opencv",
        "fl_x": float(K[0, 0]), "fl_y": float(K[1, 1]),
        "cx": float(K[0, 2]), "cy": float(K[1, 2]),
        "w": W, "h": H,
        "hfov_deg": hfov_deg,
        "pose_convention_note": (
            "world_to_camera_matrix / transform_matrix use the OpenCV convention "
            "(X-right, Y-down, Z-forward), world_up=(0,0,1), empirically validated "
            "sub-pixel accurate against the Helios RadiationCamera in Phase 0 T0.3."
        ),
        "depth_convention_note": "depth EXR is PLANE depth (distance along camera forward "
                                  "axis), not Euclidean range; sky/no-hit sentinel is -1.0.",
        "source": "Helios (helios-core RadiationModel) synthetic render, not a real capture.",
        "scene_modalities": scene_modalities,
        "frame_modalities": frame_modalities,
        "_applied_transformations": {},
        "frames": frames,
    }

    with open(os.path.join(scene_dir, "scene_meta.json"), "w") as f:
        json.dump(scene_meta, f, indent=2)

    return scene_meta
