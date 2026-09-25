"""
T1.3 -- Per-pixel semantic and instance ground-truth maps per camera view,
replacing the flat-color-render + nearest-color-match hack entirely.

Instance map: `radiation.getObjectDataLabelMap(cam, "fruitID")` works directly
-- `fruitID` is an int object-data field (see ground_truth.py), which is
exactly one of the types `writeObjectDataLabelMap` supports natively.

Semantic map: the task doc's snippet (`getPrimitiveDataLabelMap(cam,
"object_label")`) does NOT work as written -- verified against the
helios-core source, not assumed. `object_label` is a STRING primitive-data
field (set unconditionally by the plant-architecture model: "fruit", "leaf",
"shoot", "petiole", "peduncle", ...). `RadiationModel::writePrimitiveDataLabelMap`
(RadiationCamera.cpp) only handles HELIOS_TYPE_{FLOAT,UINT,INT,DOUBLE} --
its final `else` branch silently writes `padvalue` for every pixel and
prints a C++-side stderr warning ("No primitive data ... found"), it does
NOT raise a Python exception. Passing a string-typed label straight through
would produce a silently-all-NaN "ground truth" map. Fix used here: derive a
NEW int-typed `semantic_class_id` primitive-data field from `object_label`
via `filterPrimitivesByData` + `setPrimitiveDataInt`, once, then label-map
*that* field instead.
"""

import os

import numpy as np

# object_label string -> integer semantic class id. 0 is reserved for any
# primitive whose object_label isn't one of these known plant-architecture
# labels (e.g. ground plane, if one is ever added) -- NOT the same as
# background/no-hit, which getPrimitiveDataLabelMap reports as NaN.
SEMANTIC_CLASSES = {
    "fruit": 1,
    "leaf": 2,
    "shoot": 3,
    "petiole": 4,
    "peduncle": 5,
}
SEMANTIC_OTHER_CLASS_ID = 0
SEMANTIC_CLASS_ID_FIELD = "semantic_class_id"

# Fixed RGB palette for PNG previews, indexed by class id (0..5 above).
SEMANTIC_PALETTE = {
    0: (120, 120, 120),   # other / unlabeled geometry
    1: (220, 20, 60),     # fruit -- crimson
    2: (34, 139, 34),     # leaf -- forest green
    3: (139, 90, 43),     # shoot/branch -- brown
    4: (222, 184, 135),   # petiole -- tan
    5: (255, 165, 0),     # peduncle -- orange
}
BACKGROUND_RGB = (10, 10, 20)


def assign_semantic_class_ids(context, all_uuids):
    """Derive `semantic_class_id` (int) from the existing `object_label`
    (string) primitive data. Must be called once before any getPrimitiveDataLabelMap
    call for `semantic_class_id`, any time after the trees are built (doesn't
    require updateGeometry/runBand -- it's plain Context primitive data).

    Returns a dict of {label: n_primitives_matched} for logging.
    """
    context.setPrimitiveDataInt(list(all_uuids), SEMANTIC_CLASS_ID_FIELD, SEMANTIC_OTHER_CLASS_ID)
    counts = {}
    for label, class_id in SEMANTIC_CLASSES.items():
        matched = context.filterPrimitivesByData(all_uuids, "object_label", label)
        if matched:
            context.setPrimitiveDataInt(matched, SEMANTIC_CLASS_ID_FIELD, class_id)
        counts[label] = len(matched)
    return counts


def _colorize_semantic(label_map):
    h, w = label_map.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    nan_mask = np.isnan(label_map)
    rgb[nan_mask] = BACKGROUND_RGB
    for class_id, color in SEMANTIC_PALETTE.items():
        mask = (~nan_mask) & (np.round(label_map) == class_id)
        rgb[mask] = color
    return rgb


def _colorize_instance(label_map):
    """Deterministic per-instance-id color via a hash, background left dark."""
    h, w = label_map.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    nan_mask = np.isnan(label_map)
    rgb[nan_mask] = BACKGROUND_RGB
    ids = np.unique(label_map[~nan_mask]).astype(np.int64)
    for inst_id in ids:
        # Cheap deterministic hash -> color, stable across runs/views.
        h_ = (inst_id * 2654435761) & 0xFFFFFFFF
        color = ((h_ >> 16) & 0xFF, (h_ >> 8) & 0xFF, h_ & 0xFF)
        mask = (~nan_mask) & (np.round(label_map) == inst_id)
        rgb[mask] = color
    return rgb


def export_label_maps(radiation, camera_label, output_dir, view_name, write_preview_png=True):
    """T1.3: pull the semantic (`semantic_class_id`) and instance (`fruitID`)
    label maps for one already-rendered camera view (i.e. after updateGeometry
    + runBand for the pose this camera is currently at), save as .npy (the
    canonical ground truth) and optionally a colorized PNG preview.

    Returns a dict with array shapes and simple stats for logging.
    """
    os.makedirs(output_dir, exist_ok=True)

    semantic = radiation.getPrimitiveDataLabelMap(camera_label, SEMANTIC_CLASS_ID_FIELD)
    instance = radiation.getObjectDataLabelMap(camera_label, "fruitID")

    sem_path = os.path.join(output_dir, f"{view_name}_semantic.npy")
    inst_path = os.path.join(output_dir, f"{view_name}_instance.npy")
    np.save(sem_path, semantic)
    np.save(inst_path, instance)

    report = {
        "view": view_name,
        "shape": list(semantic.shape),
        "semantic_classes_present": sorted(
            int(c) for c in np.unique(semantic[~np.isnan(semantic)])
        ) if not np.all(np.isnan(semantic)) else [],
        "n_fruit_instances_visible": int(
            len(np.unique(instance[~np.isnan(instance)]))
        ) if not np.all(np.isnan(instance)) else 0,
        "background_fraction": float(np.mean(np.isnan(semantic))),
    }

    if write_preview_png:
        import imageio.v3 as iio
        iio.imwrite(os.path.join(output_dir, f"{view_name}_semantic.png"), _colorize_semantic(semantic))
        iio.imwrite(os.path.join(output_dir, f"{view_name}_instance.png"), _colorize_instance(instance))

    return report
