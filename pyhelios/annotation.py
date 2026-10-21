"""
Image annotation from a pixel-to-primitive map.

These functions turn a per-pixel record of which Context primitive is visible, together with
labels stored as primitive or object data, into bounding boxes (Ultralytics YOLO format) and
segmentation masks (COCO JSON format). They do not depend on how the image was produced, so any
renderer that can say which primitive is in each pixel writes the same annotations for the same
labeled Context. The radiation and visualizer plug-ins use the same routines for their own
annotation methods (:meth:`pyhelios.RadiationModel.writeImageBoundingBoxes`,
:meth:`pyhelios.Visualizer.writeImageBoundingBoxes`, and their segmentation-mask counterparts).

**The pixel-to-primitive map** is a sequence of ``width * height`` unsigned integers, row-major,
with row 0 at the TOP of the image. Each element is the UUID of the primitive visible in that
pixel **plus one**; 0 means no primitive is visible. A nested list, a flat list or a NumPy array
of either shape is accepted. :meth:`pyhelios.Visualizer.getPixelUUIDs` returns a map in exactly
this form.

**Labels** are primitive (or, with ``use_object_data=True``, object) data of type ``uint`` or
``int``. Every primitive carrying the same value of the same data label belongs to one object.
Primitives without the label are not annotated.

Example:
    >>> from pyhelios import Context, annotation
    >>> from pyhelios.types import int2
    >>> # pixel_uuids, width, height = visualizer.getPixelUUIDs()
    >>> boxes = annotation.labelBoundingBoxes(context, pixel_uuids, int2(width, height),
    ...                                       "leaf_id", 0)
    >>> annotation.writeLabelBoundingBoxes(context, pixel_uuids, int2(width, height),
    ...                                    "leaf_id", 0, image_file="scene.jpeg")
"""

import numbers
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple, Union

import numpy as np

from .Context import Context
from .wrappers import UContextWrapper as context_wrapper
from .wrappers.DataTypes import int2, vec2

__all__ = [
    "YOLOBox",
    "labelBoundingBoxes",
    "writeLabelBoundingBoxes",
    "labelMasks",
    "writeLabelSegmentationMasks",
]


@dataclass
class YOLOBox:
    """A bounding box in the normalized form of the YOLO annotation format.

    Attributes:
        class_id: Class index of the object.
        center: Center of the box, normalized to [0,1] by the image dimensions, origin at the top-left.
        size: Width and height of the box, normalized to [0,1] by the image dimensions.
    """
    class_id: int
    center: vec2
    size: vec2


def _check_context(context, func_name: str) -> None:
    if not isinstance(context, Context):
        raise ValueError(f"{func_name}: context must be a Context, got {type(context).__name__}")
    context._check_context_available()


def _check_resolution(resolution, func_name: str) -> Tuple[int, int]:
    if not isinstance(resolution, int2):
        raise ValueError(f"{func_name}: resolution must be an int2, got {type(resolution).__name__}")
    if resolution.x <= 0 or resolution.y <= 0:
        raise ValueError(f"{func_name}: resolution must be positive, got ({resolution.x}, {resolution.y})")
    return int(resolution.x), int(resolution.y)


def _check_pixel_map(pixel_uuids, width: int, height: int, func_name: str) -> np.ndarray:
    if isinstance(pixel_uuids, (str, bytes)) or not isinstance(pixel_uuids, (Sequence, np.ndarray)):
        raise TypeError(f"{func_name}: pixel_uuids must be a list or NumPy array of integers, "
                        f"got {type(pixel_uuids).__name__}")
    arr = np.asarray(pixel_uuids)
    if arr.size > 0 and arr.dtype.kind not in "iu":
        raise TypeError(f"{func_name}: pixel_uuids must hold integers (UUID + 1 per pixel, 0 for none), "
                        f"got dtype {arr.dtype}")
    if arr.size != width * height:
        raise ValueError(f"{func_name}: the pixel-to-primitive map has {arr.size} elements, which does not "
                         f"match the image resolution of {width} x {height} ({width * height} pixels)")
    if arr.size > 0 and (arr.min() < 0 or arr.max() > 0xFFFFFFFF):
        raise ValueError(f"{func_name}: pixel_uuids values must be in [0, 2^32 - 1] (UUID + 1 per pixel, 0 for none)")
    return arr.reshape(-1)


def _check_labels(data_labels, class_ids, func_name: str) -> Tuple[List[str], List[int]]:
    if isinstance(data_labels, str):
        if not isinstance(class_ids, numbers.Integral) or isinstance(class_ids, bool):
            raise TypeError(f"{func_name}: for a single data label, class_ids must be an integer, "
                            f"got {type(class_ids).__name__}")
        data_labels, class_ids = [data_labels], [class_ids]
    elif isinstance(data_labels, (list, tuple)):
        if not isinstance(class_ids, (list, tuple)):
            raise TypeError(f"{func_name}: for a list of data labels, class_ids must be a list of integers, "
                            f"got {type(class_ids).__name__}")
        if len(data_labels) != len(class_ids):
            raise ValueError(f"{func_name}: data_labels and class_ids must have the same length "
                             f"({len(data_labels)} != {len(class_ids)})")
        if len(data_labels) == 0:
            raise ValueError(f"{func_name}: at least one data label is required")
    else:
        raise TypeError(f"{func_name}: data_labels must be a string or a list of strings, "
                        f"got {type(data_labels).__name__}")
    for label in data_labels:
        if not isinstance(label, str) or not label.strip():
            raise TypeError(f"{func_name}: data labels must be non-empty strings, got {label!r}")
    for cid in class_ids:
        if not isinstance(cid, numbers.Integral) or isinstance(cid, bool) or cid < 0:
            raise ValueError(f"{func_name}: class IDs must be non-negative integers, got {cid!r}")
    return list(data_labels), [int(c) for c in class_ids]


def _check_filename(value, name: str, func_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{func_name}: {name} must be a non-empty string")
    return value


def labelBoundingBoxes(context: Context, pixel_uuids, resolution: int2,
                       data_labels: Union[str, List[str]], class_ids: Union[int, List[int]],
                       use_object_data: bool = False) -> List[YOLOBox]:
    """
    Compute a bounding box for each labeled object visible in a pixel-to-primitive map.

    One box is produced per distinct pair of class index and label value. A box encloses whole
    every pixel in which the object is visible: it runs from the left edge of the first pixel
    column to the right edge of the last, and from the top edge of the first pixel row to the
    bottom edge of the last, so an object visible in a single pixel has a box one pixel in size.

    Args:
        context: Context holding the primitives named by the map and their label data.
        pixel_uuids: Pixel-to-primitive map (UUID + 1 per pixel, 0 for none), row-major with
            row 0 at the top of the image.
        resolution: Image dimensions in pixels, as ``int2(width, height)``.
        data_labels: Name of a primitive or object data label, or a list of them.
        class_ids: Class index for the objects of each data label (an int for a single label, or a
            list in the same order as ``data_labels``).
        use_object_data: If True, labels are read from the data of each primitive's parent
            object; if False (default), from primitive data.

    Returns:
        List of :class:`YOLOBox`, ordered by class index and then label value.

    Raises:
        ValueError: If ``context`` is not a Context, ``resolution`` is not an int2, or the map
            does not have ``width * height`` elements.
        TypeError: If the labels, class IDs or map have the wrong type.
        NotImplementedError: If the native library predates helios-core v1.3.91.
    """
    func_name = "labelBoundingBoxes"
    _check_context(context, func_name)
    width, height = _check_resolution(resolution, func_name)
    pixels = _check_pixel_map(pixel_uuids, width, height, func_name)
    labels, ids = _check_labels(data_labels, class_ids, func_name)
    boxes = context_wrapper.annotationLabelBoundingBoxesWrapper(
        context.getNativePtr(), pixels, width, height, labels, ids, bool(use_object_data))
    return [YOLOBox(class_id=cid, center=vec2(cx, cy), size=vec2(w, h)) for cid, cx, cy, w, h in boxes]


def writeLabelBoundingBoxes(context: Context, pixel_uuids, resolution: int2,
                            data_labels: Union[str, List[str]], class_ids: Union[int, List[int]],
                            image_file: str, classes_txt_file: str = "classes.txt",
                            image_path: str = "./", use_object_data: bool = False) -> None:
    """
    Write YOLO bounding boxes and a class file for the labeled objects visible in a pixel-to-primitive map.

    The boxes (see :func:`labelBoundingBoxes`) are written to a file named after the image, with
    its extension replaced by ``.txt``, in the directory ``image_path``. The class file holds one
    ``class_id data_label`` pair per line.

    Args:
        context: Context holding the primitives named by the map and their label data.
        pixel_uuids: Pixel-to-primitive map (UUID + 1 per pixel, 0 for none), row-major with
            row 0 at the top of the image.
        resolution: Image dimensions in pixels, as ``int2(width, height)``.
        data_labels: Name of a primitive or object data label, or a list of them.
        class_ids: Class index for the objects of each data label.
        image_file: Name of the image these boxes annotate. Only its stem is used, to name the
            output file; the image itself need not exist.
        classes_txt_file: Name of the class file to write within ``image_path`` (default "classes.txt").
        image_path: Directory to write the output files to (default: current directory).
        use_object_data: If True, labels are read from object data; if False (default), from primitive data.

    Raises:
        ValueError: On invalid arguments (see :func:`labelBoundingBoxes`).
        HeliosRuntimeError: If ``image_path`` is not a writable directory or a file cannot be written.
        NotImplementedError: If the native library predates helios-core v1.3.91.
    """
    func_name = "writeLabelBoundingBoxes"
    _check_context(context, func_name)
    width, height = _check_resolution(resolution, func_name)
    pixels = _check_pixel_map(pixel_uuids, width, height, func_name)
    labels, ids = _check_labels(data_labels, class_ids, func_name)
    _check_filename(image_file, "image_file", func_name)
    _check_filename(classes_txt_file, "classes_txt_file", func_name)
    if not isinstance(image_path, str):
        raise TypeError(f"{func_name}: image_path must be a string")
    context_wrapper.annotationWriteLabelBoundingBoxesWrapper(
        context.getNativePtr(), pixels, width, height, labels, ids, image_file, classes_txt_file,
        image_path, bool(use_object_data))


def labelMasks(context: Context, pixel_uuids, resolution: int2, data_label: str,
               use_object_data: bool = False) -> Dict[int, np.ndarray]:
    """
    Build a binary mask for each distinct value of a data label visible in a pixel-to-primitive map.

    Args:
        context: Context holding the primitives named by the map and their label data.
        pixel_uuids: Pixel-to-primitive map (UUID + 1 per pixel, 0 for none), row-major with
            row 0 at the top of the image.
        resolution: Image dimensions in pixels, as ``int2(width, height)``.
        data_label: Name of the primitive or object data label, of type ``uint`` or ``int``.
        use_object_data: If True, the label is read from object data; if False (default), from primitive data.

    Returns:
        Dict mapping each label value to a boolean NumPy array of shape ``(height, width)``,
        indexed ``[row, column]`` with row 0 at the top of the image.

    Raises:
        ValueError: On invalid arguments (see :func:`labelBoundingBoxes`).
        NotImplementedError: If the native library predates helios-core v1.3.91.
    """
    func_name = "labelMasks"
    _check_context(context, func_name)
    width, height = _check_resolution(resolution, func_name)
    pixels = _check_pixel_map(pixel_uuids, width, height, func_name)
    if not isinstance(data_label, str) or not data_label.strip():
        raise TypeError(f"{func_name}: data_label must be a non-empty string")
    values, masks = context_wrapper.annotationLabelMasksWrapper(
        context.getNativePtr(), pixels, width, height, data_label, bool(use_object_data))
    return {value: masks[i] for i, value in enumerate(values)}


def writeLabelSegmentationMasks(context: Context, pixel_uuids, resolution: int2,
                                data_labels: Union[str, List[str]], class_ids: Union[int, List[int]],
                                json_filename: str, image_file: str,
                                data_attribute_labels: Optional[List[str]] = None,
                                append_file: bool = False, use_object_data: bool = False) -> None:
    """
    Write COCO JSON segmentation masks for the labeled objects visible in a pixel-to-primitive map.

    Each connected region of pixels sharing one value of a data label becomes one annotation, so
    an object split in two by an occluder yields two annotations. Pixels touching only at a corner
    are connected. The ``bbox`` of an annotation is (x, y, width, height) in pixels, enclosing
    whole every pixel of the region. A region of only one or two pixels is too small to outline
    and is not written. Each data label becomes a COCO category.

    Args:
        context: Context holding the primitives named by the map and their label data.
        pixel_uuids: Pixel-to-primitive map (UUID + 1 per pixel, 0 for none), row-major with
            row 0 at the top of the image.
        resolution: Image dimensions in pixels, as ``int2(width, height)``.
        data_labels: Name of a primitive or object data label, or a list of them.
        class_ids: COCO category ID for each data label.
        json_filename: Path of the COCO JSON file to write. ".json" is appended if missing.
        image_file: Path of the image these masks annotate, which must exist.
        data_attribute_labels: Optional primitive or object data labels of type int, uint, float
            or double whose mean over the pixels of each mask is written to that annotation's
            "attributes". A label that exists as both is read from primitive data; labels that do
            not exist are ignored.
        append_file: If True, annotations are added to an existing file at ``json_filename``;
            if False (default), a new file is written.
        use_object_data: If True, labels are read from object data; if False (default), from primitive data.

    Raises:
        ValueError: On invalid arguments (see :func:`labelBoundingBoxes`).
        HeliosRuntimeError: If ``image_file`` does not exist or the JSON file cannot be written.
        NotImplementedError: If the native library predates helios-core v1.3.91.
    """
    func_name = "writeLabelSegmentationMasks"
    _check_context(context, func_name)
    width, height = _check_resolution(resolution, func_name)
    pixels = _check_pixel_map(pixel_uuids, width, height, func_name)
    labels, ids = _check_labels(data_labels, class_ids, func_name)
    _check_filename(json_filename, "json_filename", func_name)
    _check_filename(image_file, "image_file", func_name)
    if data_attribute_labels is None:
        data_attribute_labels = []
    elif isinstance(data_attribute_labels, str) or not isinstance(data_attribute_labels, (list, tuple)):
        raise TypeError(f"{func_name}: data_attribute_labels must be a list of strings")
    if not all(isinstance(label, str) for label in data_attribute_labels):
        raise TypeError(f"{func_name}: data_attribute_labels must be a list of strings")
    context_wrapper.annotationWriteLabelSegmentationMasksWrapper(
        context.getNativePtr(), pixels, width, height, labels, ids, json_filename, image_file,
        list(data_attribute_labels), bool(append_file), bool(use_object_data))
