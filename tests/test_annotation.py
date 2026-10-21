"""
Tests for pyhelios.annotation (helios::annotation, helios-core 1.3.91) and the Context
geometry/shape revision counters (helios-core 1.3.92).

The annotation functions take a pixel-to-primitive map rather than a renderer, so the native
tests build the map by hand: no GPU, display or visualizer is needed.
"""

import json
import os

import numpy as np
import pytest

from pyhelios import Context, annotation
from pyhelios.types import int2, vec2, vec3


WIDTH, HEIGHT = 10, 8

# Pixel regions (top-left origin, inclusive bounds): (col_min, col_max, row_min, row_max)
REGION_A = (1, 3, 2, 4)   # 3 x 3 = 9 pixels
REGION_B = (6, 8, 0, 6)   # 3 x 7 = 21 pixels
REGION_C = (0, 0, 7, 7)   # 1 pixel, carries no "leaf_id"


def _fill(pixel_map, region, uuid):
    c0, c1, r0, r1 = region
    pixel_map[r0:r1 + 1, c0:c1 + 1] = uuid + 1


@pytest.fixture
def labeled_scene(basic_context):
    """Three patches; A and B carry leaf_id 1 and 2, C carries only fruit_id 5."""
    ctx = basic_context
    a = ctx.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
    b = ctx.addPatch(center=vec3(2, 0, 0), size=vec2(1, 1))
    c = ctx.addPatch(center=vec3(4, 0, 0), size=vec2(1, 1))
    ctx.setPrimitiveDataUInt(a, "leaf_id", 1)
    ctx.setPrimitiveDataUInt(b, "leaf_id", 2)
    ctx.setPrimitiveDataUInt(c, "fruit_id", 5)
    ctx.setPrimitiveDataFloat(a, "temperature", 20.0)
    ctx.setPrimitiveDataFloat(b, "temperature", 30.0)

    pixel_map = np.zeros((HEIGHT, WIDTH), dtype=np.uint32)
    _fill(pixel_map, REGION_A, a)
    _fill(pixel_map, REGION_B, b)
    _fill(pixel_map, REGION_C, c)
    return ctx, pixel_map


@pytest.mark.native_only
class TestLabelBoundingBoxes:

    def test_boxes_enclose_whole_pixels(self, labeled_scene):
        ctx, pixel_map = labeled_scene
        boxes = annotation.labelBoundingBoxes(ctx, pixel_map, int2(WIDTH, HEIGHT), "leaf_id", 0)

        assert len(boxes) == 2
        assert all(isinstance(b, annotation.YOLOBox) for b in boxes)
        a, b = boxes  # ordered by class index, then label value (1 before 2)
        assert a.class_id == 0 and b.class_id == 0
        # A spans columns 1-3, rows 2-4 -> edges at x 1..4, y 2..5
        assert a.center.x == pytest.approx(2.5 / WIDTH)
        assert a.center.y == pytest.approx(3.5 / HEIGHT)
        assert a.size.x == pytest.approx(3 / WIDTH)
        assert a.size.y == pytest.approx(3 / HEIGHT)
        # B spans columns 6-8, rows 0-6 -> edges at x 6..9, y 0..7
        assert b.center.x == pytest.approx(7.5 / WIDTH)
        assert b.center.y == pytest.approx(3.5 / HEIGHT)
        assert b.size.x == pytest.approx(3 / WIDTH)
        assert b.size.y == pytest.approx(7 / HEIGHT)

    def test_flat_list_map_matches_2d_array(self, labeled_scene):
        ctx, pixel_map = labeled_scene
        from_array = annotation.labelBoundingBoxes(ctx, pixel_map, int2(WIDTH, HEIGHT), "leaf_id", 0)
        from_list = annotation.labelBoundingBoxes(ctx, pixel_map.ravel().tolist(), int2(WIDTH, HEIGHT),
                                                  "leaf_id", 0)
        assert [(b.class_id, b.center.x, b.center.y) for b in from_array] == \
               [(b.class_id, b.center.x, b.center.y) for b in from_list]

    def test_single_pixel_object_gets_one_pixel_box(self, labeled_scene):
        ctx, pixel_map = labeled_scene
        boxes = annotation.labelBoundingBoxes(ctx, pixel_map, int2(WIDTH, HEIGHT), "fruit_id", 3)
        assert len(boxes) == 1
        assert boxes[0].class_id == 3
        assert boxes[0].size.x == pytest.approx(1 / WIDTH)
        assert boxes[0].size.y == pytest.approx(1 / HEIGHT)
        assert boxes[0].center.x == pytest.approx(0.5 / WIDTH)
        assert boxes[0].center.y == pytest.approx(7.5 / HEIGHT)

    def test_multiple_labels(self, labeled_scene):
        ctx, pixel_map = labeled_scene
        boxes = annotation.labelBoundingBoxes(ctx, pixel_map, int2(WIDTH, HEIGHT),
                                              ["leaf_id", "fruit_id"], [0, 1])
        assert sorted(b.class_id for b in boxes) == [0, 0, 1]

    def test_unlabeled_pixels_and_empty_map(self, labeled_scene):
        ctx, _ = labeled_scene
        empty = np.zeros((HEIGHT, WIDTH), dtype=np.uint32)
        assert annotation.labelBoundingBoxes(ctx, empty, int2(WIDTH, HEIGHT), "leaf_id", 0) == []

    def test_object_data(self, basic_context):
        ctx = basic_context
        obj1 = ctx.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1), subdiv=int2(2, 1))
        obj2 = ctx.addTileObject(center=vec3(3, 0, 0), size=vec2(1, 1), subdiv=int2(2, 1))
        ctx.setObjectDataUInt(obj1, "plant_id", 7)
        ctx.setObjectDataUInt(obj2, "plant_id", 8)
        p1 = ctx.getObjectPrimitiveUUIDs(obj1)
        p2 = ctx.getObjectPrimitiveUUIDs(obj2)

        pixel_map = np.zeros((HEIGHT, WIDTH), dtype=np.uint32)
        pixel_map[0:4, 0:2] = p1[0] + 1
        pixel_map[0:4, 2:4] = p1[1] + 1
        pixel_map[4:8, 5:10] = p2[0] + 1

        boxes = annotation.labelBoundingBoxes(ctx, pixel_map, int2(WIDTH, HEIGHT), "plant_id", 0,
                                              use_object_data=True)
        assert len(boxes) == 2
        assert boxes[0].size.x == pytest.approx(4 / WIDTH)  # both primitives of obj1 form one box
        assert boxes[0].size.y == pytest.approx(4 / HEIGHT)
        assert boxes[1].size.x == pytest.approx(5 / WIDTH)

        # The same label read as primitive data finds nothing
        assert annotation.labelBoundingBoxes(ctx, pixel_map, int2(WIDTH, HEIGHT), "plant_id", 0) == []

    def test_mismatched_map_length_raises(self, labeled_scene):
        ctx, pixel_map = labeled_scene
        with pytest.raises(ValueError, match="does not match the image resolution"):
            annotation.labelBoundingBoxes(ctx, pixel_map, int2(WIDTH + 1, HEIGHT), "leaf_id", 0)

    def test_write_bounding_boxes(self, labeled_scene, tmp_path):
        ctx, pixel_map = labeled_scene
        annotation.writeLabelBoundingBoxes(ctx, pixel_map, int2(WIDTH, HEIGHT), ["leaf_id", "fruit_id"],
                                           [0, 1], image_file="scene.jpeg", image_path=str(tmp_path) + "/")

        lines = (tmp_path / "scene.txt").read_text().strip().splitlines()
        assert len(lines) == 3
        fields = [line.split() for line in lines]
        first = [float(v) for v in fields[0]]
        assert int(first[0]) == 0
        assert first[1:] == pytest.approx([2.5 / WIDTH, 3.5 / HEIGHT, 3 / WIDTH, 3 / HEIGHT], abs=1e-6)

        classes = (tmp_path / "classes.txt").read_text().strip().splitlines()
        assert classes == ["0 leaf_id", "1 fruit_id"]

    def test_write_bounding_boxes_missing_directory_raises(self, labeled_scene, tmp_path):
        from pyhelios.exceptions import HeliosRuntimeError
        ctx, pixel_map = labeled_scene
        with pytest.raises(HeliosRuntimeError):  # only one missing directory level is created
            annotation.writeLabelBoundingBoxes(ctx, pixel_map, int2(WIDTH, HEIGHT), "leaf_id", 0,
                                               image_file="scene.jpeg",
                                               image_path=str(tmp_path / "does_not_exist" / "deeper") + "/")


@pytest.mark.native_only
class TestLabelMasks:

    def test_masks(self, labeled_scene):
        ctx, pixel_map = labeled_scene
        masks = annotation.labelMasks(ctx, pixel_map, int2(WIDTH, HEIGHT), "leaf_id")

        assert set(masks) == {1, 2}
        for mask in masks.values():
            assert isinstance(mask, np.ndarray)
            assert mask.dtype == bool
            assert mask.shape == (HEIGHT, WIDTH)
        assert int(masks[1].sum()) == 9
        assert int(masks[2].sum()) == 21
        # Indexed [row, column] with row 0 at the top
        assert masks[1][2, 1] and masks[1][4, 3] and not masks[1][1, 1]
        assert masks[2][0, 6] and masks[2][6, 8] and not masks[2][7, 8]

    def test_no_labels_gives_empty_dict(self, labeled_scene):
        ctx, pixel_map = labeled_scene
        assert annotation.labelMasks(ctx, pixel_map, int2(WIDTH, HEIGHT), "no_such_label") == {}


@pytest.mark.native_only
class TestWriteLabelSegmentationMasks:

    def test_write_masks_with_attributes(self, labeled_scene, tmp_path):
        ctx, pixel_map = labeled_scene
        image = tmp_path / "scene.jpeg"
        image.write_bytes(b"placeholder")  # only its existence and name are used
        json_file = tmp_path / "masks"

        annotation.writeLabelSegmentationMasks(ctx, pixel_map, int2(WIDTH, HEIGHT), "leaf_id", 4,
                                               json_filename=str(json_file), image_file=str(image),
                                               data_attribute_labels=["temperature"])

        data = json.loads((tmp_path / "masks.json").read_text())
        assert [c["id"] for c in data["categories"]] == [4]
        assert len(data["images"]) == 1
        anns = sorted(data["annotations"], key=lambda a: a["area"])
        assert len(anns) == 2
        assert anns[0]["bbox"] == [1, 2, 3, 3] and anns[0]["area"] == 9
        assert anns[1]["bbox"] == [6, 0, 3, 7] and anns[1]["area"] == 21
        assert anns[0]["attributes"]["temperature"] == pytest.approx(20.0)
        assert anns[1]["attributes"]["temperature"] == pytest.approx(30.0)

    def test_append(self, labeled_scene, tmp_path):
        ctx, pixel_map = labeled_scene
        image = tmp_path / "scene.jpeg"
        image.write_bytes(b"placeholder")
        json_file = str(tmp_path / "masks.json")

        annotation.writeLabelSegmentationMasks(ctx, pixel_map, int2(WIDTH, HEIGHT), "leaf_id", 0,
                                               json_filename=json_file, image_file=str(image))
        annotation.writeLabelSegmentationMasks(ctx, pixel_map, int2(WIDTH, HEIGHT), "leaf_id", 0,
                                               json_filename=json_file, image_file=str(image),
                                               append_file=True)
        with open(json_file) as f:
            data = json.load(f)
        assert len(data["annotations"]) == 4
        assert len({a["id"] for a in data["annotations"]}) == 4

    def test_missing_image_raises(self, labeled_scene, tmp_path):
        from pyhelios.exceptions import HeliosRuntimeError
        ctx, pixel_map = labeled_scene
        with pytest.raises(HeliosRuntimeError, match="does not exist"):
            annotation.writeLabelSegmentationMasks(ctx, pixel_map, int2(WIDTH, HEIGHT), "leaf_id", 0,
                                                   json_filename=str(tmp_path / "m.json"),
                                                   image_file=str(tmp_path / "missing.jpeg"))


@pytest.mark.cross_platform
class TestAnnotationArgumentValidation:
    """Validation runs before any native call, so a mocked Context is enough."""

    def test_non_context_rejected(self):
        with pytest.raises(ValueError, match="must be a Context"):
            annotation.labelBoundingBoxes(object(), [0] * 4, int2(2, 2), "leaf_id", 0)

    def test_resolution_must_be_int2(self, mock_context):
        for bad in [(2, 2), vec2(2, 2), [2, 2]]:
            with pytest.raises(ValueError, match="int2"):
                annotation.labelBoundingBoxes(mock_context, [0] * 4, bad, "leaf_id", 0)
            with pytest.raises(ValueError, match="int2"):
                annotation.labelMasks(mock_context, [0] * 4, resolution=bad, data_label="leaf_id")

    def test_map_length_checked(self, mock_context):
        with pytest.raises(ValueError, match="does not match the image resolution"):
            annotation.labelMasks(mock_context, [0] * 5, int2(2, 2), "leaf_id")

    def test_map_must_be_integers(self, mock_context):
        with pytest.raises(TypeError, match="integers"):
            annotation.labelBoundingBoxes(mock_context, [0.5] * 4, int2(2, 2), "leaf_id", 0)
        with pytest.raises(ValueError, match="2\\^32"):
            annotation.labelBoundingBoxes(mock_context, [-1, 0, 0, 0], int2(2, 2), "leaf_id", 0)

    def test_labels_and_class_ids(self, mock_context):
        with pytest.raises(ValueError, match="same length"):
            annotation.labelBoundingBoxes(mock_context, [0] * 4, int2(2, 2), ["a", "b"], [0])
        with pytest.raises(TypeError, match="must be an integer"):
            annotation.labelBoundingBoxes(mock_context, [0] * 4, int2(2, 2), "a", [0])
        with pytest.raises(ValueError, match="non-negative"):
            annotation.labelBoundingBoxes(mock_context, [0] * 4, int2(2, 2), ["a"], [-1])

    def test_segmentation_attribute_labels_must_be_list(self, mock_context):
        with pytest.raises(TypeError, match="data_attribute_labels"):
            annotation.writeLabelSegmentationMasks(mock_context, [0] * 4, int2(2, 2), "a", 0,
                                                   json_filename="m.json", image_file="x.jpeg",
                                                   data_attribute_labels="temperature")


@pytest.mark.native_only
class TestGeometryRevision:

    def test_repeated_reads_are_equal(self, basic_context):
        basic_context.addPatch()
        assert basic_context.getGeometryRevision() == basic_context.getGeometryRevision()
        assert basic_context.getShapeRevision() == basic_context.getShapeRevision()

    def test_data_write_advances_geometry_but_not_shape(self, basic_context):
        uuid = basic_context.addPatch()
        geometry = basic_context.getGeometryRevision()
        shape = basic_context.getShapeRevision()

        basic_context.setPrimitiveDataFloat(uuid, "temperature", 25.0)

        assert basic_context.getGeometryRevision() != geometry
        assert basic_context.getShapeRevision() == shape

    def test_translate_advances_both(self, basic_context):
        uuid = basic_context.addPatch()
        geometry = basic_context.getGeometryRevision()
        shape = basic_context.getShapeRevision()

        basic_context.translatePrimitive(uuid, vec3(1, 0, 0))

        assert basic_context.getGeometryRevision() != geometry
        assert basic_context.getShapeRevision() != shape

    def test_delete_advances_both(self, basic_context):
        uuid = basic_context.addPatch()
        geometry = basic_context.getGeometryRevision()
        shape = basic_context.getShapeRevision()

        basic_context.deletePrimitive(uuid)

        assert basic_context.getGeometryRevision() != geometry
        assert basic_context.getShapeRevision() != shape

    def test_mark_geometry_clean_does_not_reset(self, basic_context):
        uuid = basic_context.addPatch()
        basic_context.translatePrimitive(uuid, vec3(1, 0, 0))
        geometry = basic_context.getGeometryRevision()
        shape = basic_context.getShapeRevision()

        basic_context.markGeometryClean()

        assert basic_context.getGeometryRevision() == geometry
        assert basic_context.getShapeRevision() == shape
