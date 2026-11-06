"""
Tests for the helios-core 1.3.95 Core additions: primitive color textures, spectral palettes
and spectral textures (Context), single-channel PNG I/O (Global), and class-map segmentation
masks (pyhelios.annotation).

None of these need a GPU or a display. Images are written by the tests themselves: RGBA
textures with a small pure-Python PNG writer, and class maps with
Global.writePNGSingleChannel.
"""

import json
import os
import struct
import zlib

import numpy as np
import pytest

from pyhelios import Context, Global, SpectralTextureClass, annotation
from pyhelios.exceptions import HeliosError
from pyhelios.types import int2, vec2, vec3
from pyhelios.wrappers import UContextWrapper as context_wrapper
from pyhelios.wrappers import UGlobalWrapper as global_wrapper


requires_textures_1395 = pytest.mark.skipif(
    not context_wrapper._CONTEXT_TEXTURES_1395_AVAILABLE,
    reason="Color/spectral texture functions not in the native library (requires helios-core v1.3.95; "
           "rebuild with build_scripts/build_helios --clean)")
requires_png_1395 = pytest.mark.skipif(
    not global_wrapper._PNG_SINGLE_CHANNEL_FUNCTIONS_AVAILABLE,
    reason="readPNGSingleChannel/writePNGSingleChannel not in the native library (requires helios-core v1.3.95)")
requires_classmap_annotation_1395 = pytest.mark.skipif(
    not context_wrapper._ANNOTATION_1395_AVAILABLE,
    reason="annotation.writeClassMapSegmentationMasks not in the native library (requires helios-core v1.3.95)")


# A 6 x 4 texture: the outer columns are transparent, the middle four columns opaque.
TEX_W, TEX_H = 6, 4


def _opaque(x, y):
    return 1 <= x <= 4


def _write_rgba_png(path, width, height, pixel_fn):
    """Write an 8-bit RGBA PNG; pixel_fn(x, y) returns an (r, g, b, a) tuple of ints."""
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter type: none
        for x in range(width):
            raw.extend(pixel_fn(x, y))

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw)))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return str(path)


@pytest.fixture
def textures(tmp_path):
    """Shape texture (green), matching color texture (yellow), and mismatched textures."""
    shape = _write_rgba_png(tmp_path / "shape.png", TEX_W, TEX_H,
                            lambda x, y: (0, 200, 0, 255 if _opaque(x, y) else 0))
    color = _write_rgba_png(tmp_path / "color.png", TEX_W, TEX_H,
                            lambda x, y: (255, 255, 0, 255 if _opaque(x, y) else 0))
    other_outline = _write_rgba_png(tmp_path / "outline.png", TEX_W, TEX_H,
                                    lambda x, y: (255, 0, 0, 255 if 0 <= x <= 4 else 0))
    other_size = _write_rgba_png(tmp_path / "size.png", TEX_W * 2, TEX_H,
                                 lambda x, y: (255, 0, 0, 255))
    return {"shape": shape, "color": color, "outline": other_outline, "size": other_size}


def _classes_for_texture():
    """Class map for the shape texture: 0 where transparent, 1 on the left half and 2 on the right."""
    classes = np.zeros((TEX_H, TEX_W), dtype=np.uint16)
    for y in range(TEX_H):
        for x in range(TEX_W):
            if _opaque(x, y):
                classes[y, x] = 1 if x < TEX_W // 2 else 2
    return classes


TWO_CLASSES = [SpectralTextureClass("lamina_reflectivity", "lamina_transmissivity", "measured"),
               SpectralTextureClass("lesion_reflectivity", "", "assumed")]
THREE_CLASSES = [SpectralTextureClass("a_reflectivity", "a_transmissivity"),
                 SpectralTextureClass("b_reflectivity", "b_transmissivity"),
                 SpectralTextureClass("c_reflectivity", "c_transmissivity")]
ONE_CLASS = [SpectralTextureClass("a_reflectivity", "a_transmissivity")]


# ---------------------------------------------------------------------------
# Global.readPNGSingleChannel / writePNGSingleChannel
# ---------------------------------------------------------------------------

@pytest.mark.cross_platform
class TestPNGSingleChannelValidation:
    """Argument checks made in Python before any native call."""

    def test_wrong_value_count(self, tmp_path):
        with pytest.raises(ValueError, match="needs 6"):
            Global.writePNGSingleChannel(str(tmp_path / "x.png"), 3, 2, [1, 2, 3], 8)

    def test_value_out_of_uint16_range(self, tmp_path):
        with pytest.raises(ValueError, match="65535"):
            Global.writePNGSingleChannel(str(tmp_path / "x.png"), 1, 2, [0, 70000], 16)
        with pytest.raises(ValueError, match="65535"):
            Global.writePNGSingleChannel(str(tmp_path / "x.png"), 1, 2, [0, -1], 16)

    def test_non_integer_values(self, tmp_path):
        with pytest.raises(ValueError, match="integers"):
            Global.writePNGSingleChannel(str(tmp_path / "x.png"), 1, 2, [0.5, 1.0], 8)

    def test_bad_bit_depth(self, tmp_path):
        with pytest.raises(ValueError, match="bit_depth"):
            Global.writePNGSingleChannel(str(tmp_path / "x.png"), 1, 1, [0], 12)

    def test_bad_dimensions_and_filename(self, tmp_path):
        with pytest.raises(ValueError, match="width"):
            Global.writePNGSingleChannel(str(tmp_path / "x.png"), 0, 1, [], 8)
        with pytest.raises(ValueError, match="height"):
            Global.writePNGSingleChannel(str(tmp_path / "x.png"), 1, 2.0, [0, 0], 8)
        with pytest.raises(ValueError, match="filename"):
            Global.writePNGSingleChannel("", 1, 1, [0], 8)
        with pytest.raises(ValueError, match="filename"):
            Global.readPNGSingleChannel(42)


@pytest.mark.native_only
@requires_png_1395
class TestPNGSingleChannel:

    def test_8bit_round_trip(self, tmp_path):
        values = np.arange(12, dtype=np.uint16).reshape(3, 4) * 20
        path = str(tmp_path / "eight.png")
        Global.writePNGSingleChannel(path, 4, 3, values, 8)
        read = Global.readPNGSingleChannel(path)
        assert read.dtype == np.uint16
        assert read.shape == (3, 4)
        np.testing.assert_array_equal(read, values)

    def test_16bit_round_trip_keeps_values_above_255(self, tmp_path):
        values = [0, 1, 255, 256, 1000, 65535]
        path = str(tmp_path / "sixteen.png")
        Global.writePNGSingleChannel(path, 3, 2, values, bit_depth=16)
        read = Global.readPNGSingleChannel(path)
        assert read.shape == (2, 3)
        assert read.ravel().tolist() == values

    def test_value_too_large_for_8bit_is_rejected(self, tmp_path):
        with pytest.raises(HeliosError):
            Global.writePNGSingleChannel(str(tmp_path / "x.png"), 2, 1, [0, 256], 8)

    def test_rgba_image_is_rejected(self, textures):
        with pytest.raises(HeliosError):
            Global.readPNGSingleChannel(textures["shape"])

    def test_missing_file_is_rejected(self, tmp_path):
        with pytest.raises(HeliosError):
            Global.readPNGSingleChannel(str(tmp_path / "missing.png"))


# ---------------------------------------------------------------------------
# Color textures
# ---------------------------------------------------------------------------

@pytest.mark.native_only
@requires_textures_1395
class TestColorTexture:

    def test_changes_appearance_and_nothing_else(self, basic_context, textures):
        ctx = basic_context
        patch = ctx.addPatchTextured(vec3(0, 0, 0), vec2(1, 1), textures["shape"])
        bystander = ctx.addPatchTextured(vec3(0, 0, 0), vec2(1, 1), textures["shape"])
        shape_file = ctx.getPrimitiveTextureFile(patch)
        material = ctx.getPrimitiveMaterialLabel(patch)
        area = ctx.getPrimitiveArea(patch)

        assert ctx.getPrimitiveColorTextureFile(patch) == shape_file

        ctx.setPrimitiveColorTexture(patch, textures["color"])
        assert ctx.getPrimitiveColorTextureFile(patch) == textures["color"]
        assert ctx.getPrimitiveTextureFile(patch) == shape_file
        assert ctx.getPrimitiveMaterialLabel(patch) == material
        assert ctx.getPrimitiveArea(patch) == pytest.approx(area)
        assert ctx.getPrimitiveColorTextureFile(bystander) == shape_file

        ctx.setPrimitiveColorTexture(patch, "")
        assert ctx.getPrimitiveColorTextureFile(patch) == shape_file

    def test_list_of_uuids(self, basic_context, textures):
        ctx = basic_context
        uuids = [ctx.addPatchTextured(vec3(i, 0, 0), vec2(1, 1), textures["shape"]) for i in range(3)]
        ctx.setPrimitiveColorTexture(uuids, textures["color"])
        assert all(ctx.getPrimitiveColorTextureFile(u) == textures["color"] for u in uuids)

    def test_one_bad_primitive_leaves_the_others_unchanged(self, basic_context, textures):
        ctx = basic_context
        patch = ctx.addPatchTextured(vec3(0, 0, 0), vec2(1, 1), textures["shape"])
        untextured = ctx.addPatch()
        before = ctx.getPrimitiveColorTextureFile(patch)
        with pytest.raises(HeliosError):
            ctx.setPrimitiveColorTexture([patch, untextured], textures["color"])
        assert ctx.getPrimitiveColorTextureFile(patch) == before

    def test_mismatched_images_are_rejected(self, basic_context, textures):
        ctx = basic_context
        patch = ctx.addPatchTextured(vec3(0, 0, 0), vec2(1, 1), textures["shape"])
        for bad in (textures["outline"], textures["size"]):
            with pytest.raises(HeliosError):
                ctx.setPrimitiveColorTexture(patch, bad)
        with pytest.raises(HeliosError):
            ctx.setPrimitiveColorTexture(ctx.addPatch(), textures["color"])

    def test_validate_color_texture(self, basic_context, textures):
        ctx = basic_context
        ctx.validateColorTexture(textures["shape"], textures["color"])
        with pytest.raises(HeliosError, match="transparency"):
            ctx.validateColorTexture(textures["shape"], textures["outline"])
        with pytest.raises(HeliosError, match="resolution"):
            ctx.validateColorTexture(textures["shape"], textures["size"])

    def test_survives_write_and_load_xml(self, basic_context, textures, tmp_path):
        ctx = basic_context
        patch = ctx.addPatchTextured(vec3(0, 0, 0), vec2(1, 1), textures["shape"])
        ctx.setPrimitiveColorTexture(patch, textures["color"])
        xml = str(tmp_path / "color_texture.xml")
        ctx.writeXML(xml, quiet=True)

        with Context() as ctx2:
            loaded = ctx2.loadXML(xml, quiet=True)
            assert len(loaded) == 1
            assert ctx2.getPrimitiveColorTextureFile(loaded[0]) == textures["color"]


@pytest.mark.native_only
class TestColorTextureArgumentValidation:
    """Rejected in Python before any native call, so these run on any native build."""

    def test_wrong_uuid_type(self, basic_context):
        with pytest.raises(ValueError, match="UUID"):
            basic_context.setPrimitiveColorTexture("0", "color.png")
        with pytest.raises(ValueError, match="UUID"):
            basic_context.setPrimitiveColorTexture(uuids=1.5, color_texture_file="color.png")
        with pytest.raises(ValueError, match="UUID"):
            basic_context.setPrimitiveColorTexture([0, "1"], "color.png")

    def test_uuid_outside_unsigned_range(self, basic_context):
        # ctypes would silently wrap 2**32 to UUID 0.
        with pytest.raises(ValueError, match="UUID"):
            basic_context.setPrimitiveColorTexture(2 ** 32, "color.png")
        with pytest.raises(ValueError, match="UUID"):
            basic_context.setPrimitiveColorTexture([0, 2 ** 32], "color.png")

    def test_wrong_file_type(self, basic_context):
        with pytest.raises(ValueError, match="color_texture_file"):
            basic_context.setPrimitiveColorTexture(0, 5)
        with pytest.raises(ValueError, match="shape_texture_file"):
            basic_context.validateColorTexture(shape_texture_file=None, color_texture_file="c.png")
        with pytest.raises(ValueError, match="color_texture_file"):
            basic_context.validateColorTexture("s.png", "")


# ---------------------------------------------------------------------------
# Spectral palettes and spectral textures
# ---------------------------------------------------------------------------

@pytest.fixture
def class_map_untextured(tmp_path):
    """A 5 x 3 class map with classes 1 and 2 only, for a patch without a texture."""
    classes = np.array([[1, 1, 2, 2, 2],
                        [1, 1, 1, 2, 2],
                        [1, 2, 2, 2, 1]], dtype=np.uint16)
    path = str(tmp_path / "classes_untextured.png")
    Global.writePNGSingleChannel(path, 5, 3, classes, 8)
    return path, classes


@pytest.mark.native_only
@requires_textures_1395
@requires_png_1395
class TestSpectralPalette:

    def test_register_and_query(self, basic_context):
        ctx = basic_context
        assert not ctx.doesSpectralPaletteExist("leaf")
        ctx.addSpectralPalette("leaf", TWO_CLASSES)
        assert ctx.doesSpectralPaletteExist("leaf")
        assert ctx.getSpectralPalette("leaf") == TWO_CLASSES

    def test_same_classes_again_is_accepted_different_ones_rejected(self, basic_context):
        ctx = basic_context
        ctx.addSpectralPalette("leaf", TWO_CLASSES)
        ctx.addSpectralPalette("leaf", list(TWO_CLASSES))
        with pytest.raises(HeliosError):
            ctx.addSpectralPalette("leaf", THREE_CLASSES)
        assert ctx.getSpectralPalette("leaf") == TWO_CLASSES

    def test_invalid_palettes_are_rejected(self, basic_context):
        ctx = basic_context
        with pytest.raises(HeliosError):
            ctx.addSpectralPalette("", TWO_CLASSES)
        with pytest.raises(HeliosError):
            ctx.addSpectralPalette("empty", [])
        with pytest.raises(HeliosError):
            ctx.addSpectralPalette("no_reflectivity", [SpectralTextureClass("", "a_transmissivity")])
        assert not ctx.doesSpectralPaletteExist("empty")
        with pytest.raises(HeliosError):
            ctx.getSpectralPalette("missing")


@pytest.mark.native_only
@requires_textures_1395
@requires_png_1395
class TestSpectralTexture:

    def test_untextured_patch_round_trip(self, basic_context, class_map_untextured):
        ctx = basic_context
        path, classes = class_map_untextured
        ctx.addSpectralPalette("leaf", TWO_CLASSES)
        patch = ctx.addPatch()
        bystander = ctx.addPatch()
        material = ctx.getPrimitiveMaterialLabel(patch)
        area = ctx.getPrimitiveArea(patch)

        assert not ctx.primitiveHasSpectralTexture(patch)
        assert ctx.getPrimitiveSpectralTextureFile(patch) == ""
        assert ctx.getPrimitiveSpectralPalette(patch) == ""

        ctx.markGeometryClean()
        shape_revision = ctx.getShapeRevision()
        ctx.setPrimitiveSpectralTexture(patch, path, "leaf")

        assert ctx.primitiveHasSpectralTexture(patch)
        assert ctx.getPrimitiveSpectralTextureFile(patch) == path
        assert ctx.getPrimitiveSpectralPalette(patch) == "leaf"
        assert ctx.getPrimitiveMaterialLabel(patch) == material
        assert ctx.getPrimitiveArea(patch) == pytest.approx(area)
        assert not ctx.primitiveHasSpectralTexture(bystander)
        assert ctx.getShapeRevision() != shape_revision

        stored, resolution = ctx.getSpectralTextureClassMap(path)
        assert isinstance(resolution, int2)
        assert (resolution.x, resolution.y) == (5, 3)
        assert stored.dtype == np.uint16
        np.testing.assert_array_equal(stored, classes)

        ctx.clearPrimitiveSpectralTexture(patch)
        assert not ctx.primitiveHasSpectralTexture(patch)
        assert ctx.getPrimitiveSpectralTextureFile(patch) == ""
        assert ctx.getPrimitiveSpectralPalette(patch) == ""

    def test_textured_patch_with_transparent_texels(self, basic_context, textures, tmp_path):
        ctx = basic_context
        path = str(tmp_path / "classes_textured.png")
        Global.writePNGSingleChannel(path, TEX_W, TEX_H, _classes_for_texture(), 8)
        ctx.addSpectralPalette("leaf", TWO_CLASSES)
        patch = ctx.addPatchTextured(vec3(0, 0, 0), vec2(1, 1), textures["shape"])
        triangle = ctx.addTriangleTextured(vec3(0, 0, 0), vec3(1, 0, 0), vec3(1, 1, 0), textures["shape"],
                                           vec2(0, 0), vec2(1, 0), vec2(1, 1))
        ctx.setPrimitiveSpectralTexture([patch, triangle], path, "leaf")
        assert ctx.primitiveHasSpectralTexture(patch)
        assert ctx.primitiveHasSpectralTexture(triangle)

        # A class map that marks an opaque texel as class 0 does not match the shape
        bad = _classes_for_texture()
        bad[0, 2] = 0
        bad_path = str(tmp_path / "classes_bad.png")
        Global.writePNGSingleChannel(bad_path, TEX_W, TEX_H, bad, 8)
        other = ctx.addPatchTextured(vec3(0, 0, 0), vec2(1, 1), textures["shape"])
        with pytest.raises(HeliosError):
            ctx.setPrimitiveSpectralTexture(other, bad_path, "leaf")
        assert not ctx.primitiveHasSpectralTexture(other)

    def test_switching_palette_keeps_class_map_and_shape(self, basic_context, class_map_untextured):
        ctx = basic_context
        path, _ = class_map_untextured
        ctx.addSpectralPalette("young", TWO_CLASSES)
        ctx.addSpectralPalette("old", THREE_CLASSES)
        ctx.addSpectralPalette("too_small", ONE_CLASS)
        patch = ctx.addPatch()
        untextured = ctx.addPatch()
        ctx.setPrimitiveSpectralTexture(patch, path, "young")

        ctx.markGeometryClean()
        shape_revision = ctx.getShapeRevision()
        ctx.setPrimitiveSpectralPalette(patch, "old")
        assert ctx.getPrimitiveSpectralPalette(patch) == "old"
        assert ctx.getPrimitiveSpectralTextureFile(patch) == path
        assert ctx.getShapeRevision() == shape_revision

        with pytest.raises(HeliosError):
            ctx.setPrimitiveSpectralPalette(patch, "too_small")
        with pytest.raises(HeliosError):
            ctx.setPrimitiveSpectralPalette(patch, "missing")
        with pytest.raises(HeliosError):
            ctx.setPrimitiveSpectralPalette(untextured, "old")
        with pytest.raises(HeliosError):
            ctx.setPrimitiveSpectralPalette([patch, untextured], "young")
        assert ctx.getPrimitiveSpectralPalette(patch) == "old"

    def test_list_overloads(self, basic_context, class_map_untextured):
        ctx = basic_context
        path, _ = class_map_untextured
        ctx.addSpectralPalette("young", TWO_CLASSES)
        ctx.addSpectralPalette("old", THREE_CLASSES)
        patches = [ctx.addPatch(center=vec3(i, 0, 0)) for i in range(3)]
        ctx.setPrimitiveSpectralTexture(patches, path, "young")
        assert all(ctx.getPrimitiveSpectralPalette(p) == "young" for p in patches)
        ctx.setPrimitiveSpectralPalette(patches, "old")
        assert all(ctx.getPrimitiveSpectralPalette(p) == "old" for p in patches)

        # A list with a primitive that does not exist is rejected before anything is removed
        with pytest.raises(HeliosError):
            ctx.clearPrimitiveSpectralTexture([patches[0], 99999])
        assert ctx.primitiveHasSpectralTexture(patches[0])

        ctx.clearPrimitiveSpectralTexture(patches)
        assert not any(ctx.primitiveHasSpectralTexture(p) for p in patches)

    def test_rejected_assignments_change_nothing(self, basic_context, class_map_untextured, tmp_path):
        ctx = basic_context
        path, _ = class_map_untextured
        ctx.addSpectralPalette("too_small", ONE_CLASS)
        ctx.addSpectralPalette("leaf", TWO_CLASSES)
        patch = ctx.addPatch()
        with pytest.raises(HeliosError):
            ctx.setPrimitiveSpectralTexture(patch, path, "missing")
        with pytest.raises(HeliosError):
            ctx.setPrimitiveSpectralTexture(patch, path, "too_small")  # class 2 has no entry
        with pytest.raises(HeliosError):
            ctx.setPrimitiveSpectralTexture(patch, str(tmp_path / "missing.png"), "leaf")
        assert not ctx.primitiveHasSpectralTexture(patch)

        with pytest.raises(HeliosError):
            ctx.getSpectralTextureClassMap(str(tmp_path / "never_assigned.png"))

    def test_survives_write_and_load_xml(self, basic_context, class_map_untextured, tmp_path):
        ctx = basic_context
        path, classes = class_map_untextured
        ctx.addSpectralPalette("leaf", TWO_CLASSES)
        patch = ctx.addPatch()
        ctx.addPatch(center=vec3(2, 0, 0))
        ctx.setPrimitiveSpectralTexture(patch, path, "leaf")
        xml = str(tmp_path / "spectral_texture.xml")
        ctx.writeXML(xml, quiet=True)

        with Context() as ctx2:
            loaded = ctx2.loadXML(xml, quiet=True)
            assert len(loaded) == 2
            assert ctx2.doesSpectralPaletteExist("leaf")
            assert ctx2.getSpectralPalette("leaf") == TWO_CLASSES
            assert ctx2.primitiveHasSpectralTexture(loaded[0])
            assert ctx2.getPrimitiveSpectralPalette(loaded[0]) == "leaf"
            assert not ctx2.primitiveHasSpectralTexture(loaded[1])
            stored, resolution = ctx2.getSpectralTextureClassMap(ctx2.getPrimitiveSpectralTextureFile(loaded[0]))
            np.testing.assert_array_equal(stored, classes)


@pytest.mark.native_only
class TestSpectralTextureArgumentValidation:
    """Rejected in Python before any native call, so these run on any native build."""

    def test_palette_classes_must_be_spectral_texture_classes(self, basic_context):
        with pytest.raises(ValueError, match="SpectralTextureClass"):
            basic_context.addSpectralPalette("leaf", [("r", "t", "p")])
        with pytest.raises(ValueError, match="SpectralTextureClass"):
            basic_context.addSpectralPalette(label="leaf", classes=SpectralTextureClass("r"))
        with pytest.raises(ValueError, match="reflectivity_spectrum"):
            basic_context.addSpectralPalette("leaf", [SpectralTextureClass(None)])
        with pytest.raises(ValueError, match="label"):
            basic_context.addSpectralPalette(3, TWO_CLASSES)

    def test_wrong_uuid_types(self, basic_context):
        ctx = basic_context
        with pytest.raises(ValueError, match="UUID"):
            ctx.setPrimitiveSpectralTexture("0", "c.png", "leaf")
        with pytest.raises(ValueError, match="UUID"):
            ctx.setPrimitiveSpectralTexture(uuids=vec3(0, 0, 0), class_map_file="c.png", palette_label="leaf")
        with pytest.raises(ValueError, match="UUID"):
            ctx.setPrimitiveSpectralPalette(-1, "leaf")
        with pytest.raises(ValueError, match="UUID"):
            ctx.clearPrimitiveSpectralTexture(uuids=[0, None])
        with pytest.raises(ValueError, match="UUID"):
            ctx.primitiveHasSpectralTexture(True)
        with pytest.raises(ValueError):
            ctx.getPrimitiveSpectralPalette([0, 1])
        with pytest.raises(ValueError):
            ctx.getPrimitiveSpectralTextureFile("0")
        with pytest.raises(ValueError):
            ctx.getPrimitiveColorTextureFile(uuid=[0])

    def test_wrong_string_types(self, basic_context):
        ctx = basic_context
        with pytest.raises(ValueError, match="class_map_file"):
            ctx.setPrimitiveSpectralTexture(0, 1, "leaf")
        with pytest.raises(ValueError, match="palette_label"):
            ctx.setPrimitiveSpectralTexture(0, "c.png", palette_label=None)
        with pytest.raises(ValueError, match="palette_label"):
            ctx.setPrimitiveSpectralPalette(0, "")
        with pytest.raises(ValueError, match="class_map_file"):
            ctx.getSpectralTextureClassMap(class_map_file=int2(1, 1))


# ---------------------------------------------------------------------------
# annotation.writeClassMapSegmentationMasks
# ---------------------------------------------------------------------------

CM_W, CM_H = 8, 5


@pytest.fixture
def class_map_scene(basic_context, tmp_path):
    ctx = basic_context
    patch = ctx.addPatch()
    ctx.setPrimitiveDataFloat(patch, "chlorophyll", 40.0)
    pixel_uuids = np.zeros((CM_H, CM_W), dtype=np.uint32)
    pixel_uuids[0:4, 0:7] = patch + 1
    pixel_classes = np.zeros((CM_H, CM_W), dtype=np.uint32)
    pixel_classes[0:4, 0:3] = 1      # 12 pixels
    pixel_classes[0:2, 4:7] = 2      # 6 pixels
    pixel_classes[4, 7] = 3          # 1 pixel: too small to outline
    image = _write_rgba_png(tmp_path / "image.png", CM_W, CM_H, lambda x, y: (0, 0, 0, 255))
    return ctx, pixel_classes, pixel_uuids, image


@pytest.mark.native_only
@requires_classmap_annotation_1395
class TestWriteClassMapSegmentationMasks:

    def test_writes_one_category_per_named_class(self, class_map_scene, tmp_path):
        ctx, pixel_classes, pixel_uuids, image = class_map_scene
        json_file = str(tmp_path / "classes")
        annotation.writeClassMapSegmentationMasks(ctx, pixel_classes, pixel_uuids, int2(CM_W, CM_H),
                                                  {1: "lamina", 2: "lesion", 3: "speck"}, json_file, image,
                                                  data_attribute_labels=["chlorophyll"])
        with open(json_file + ".json") as f:
            coco = json.load(f)
        categories = {c["id"]: c["name"] for c in coco["categories"]}
        assert categories == {1: "lamina", 2: "lesion", 3: "speck"}
        by_category = {}
        for ann in coco["annotations"]:
            by_category.setdefault(ann["category_id"], []).append(ann)
        assert len(by_category[1]) == 1
        assert len(by_category[2]) == 1
        assert 3 not in by_category
        assert by_category[1][0]["bbox"] == [0, 0, 3, 4]
        assert by_category[2][0]["bbox"] == [4, 0, 3, 2]
        assert by_category[1][0]["attributes"]["chlorophyll"] == pytest.approx(40.0)

    def test_classes_not_listed_are_not_annotated(self, class_map_scene, tmp_path):
        ctx, pixel_classes, pixel_uuids, image = class_map_scene
        json_file = str(tmp_path / "only_lesions.json")
        annotation.writeClassMapSegmentationMasks(ctx, pixel_classes.ravel().tolist(), pixel_uuids,
                                                  int2(CM_W, CM_H), {2: "lesion"}, json_file, image)
        with open(json_file) as f:
            coco = json.load(f)
        assert {a["category_id"] for a in coco["annotations"]} == {2}

    def test_missing_image_is_rejected(self, class_map_scene, tmp_path):
        ctx, pixel_classes, pixel_uuids, _ = class_map_scene
        with pytest.raises(HeliosError):
            annotation.writeClassMapSegmentationMasks(ctx, pixel_classes, pixel_uuids, int2(CM_W, CM_H),
                                                      {1: "lamina"}, str(tmp_path / "x.json"),
                                                      str(tmp_path / "missing.png"))


@pytest.mark.native_only
class TestWriteClassMapSegmentationMasksValidation:
    """Rejected in Python before any native call, so these run on any native build."""

    def test_resolution_must_be_int2(self, class_map_scene, tmp_path):
        ctx, pixel_classes, pixel_uuids, image = class_map_scene
        with pytest.raises(ValueError, match="int2"):
            annotation.writeClassMapSegmentationMasks(ctx, pixel_classes, pixel_uuids, vec2(CM_W, CM_H),
                                                      {1: "lamina"}, str(tmp_path / "x.json"), image)
        with pytest.raises(ValueError, match="int2"):
            annotation.writeClassMapSegmentationMasks(ctx, pixel_classes, pixel_uuids, resolution=(CM_W, CM_H),
                                                      class_names={1: "lamina"},
                                                      json_filename=str(tmp_path / "x.json"), image_file=image)

    def test_context_must_be_a_context(self, class_map_scene, tmp_path):
        _, pixel_classes, pixel_uuids, image = class_map_scene
        with pytest.raises(ValueError, match="Context"):
            annotation.writeClassMapSegmentationMasks(None, pixel_classes, pixel_uuids, int2(CM_W, CM_H),
                                                      {1: "lamina"}, str(tmp_path / "x.json"), image)

    def test_class_map_size_and_type(self, class_map_scene, tmp_path):
        ctx, pixel_classes, pixel_uuids, image = class_map_scene
        with pytest.raises(ValueError, match="class map"):
            annotation.writeClassMapSegmentationMasks(ctx, pixel_classes[:2], pixel_uuids, int2(CM_W, CM_H),
                                                      {1: "lamina"}, str(tmp_path / "x.json"), image)
        with pytest.raises(TypeError, match="pixel_classes"):
            annotation.writeClassMapSegmentationMasks(ctx, pixel_classes.astype(float), pixel_uuids,
                                                      int2(CM_W, CM_H), {1: "lamina"}, str(tmp_path / "x.json"), image)

    def test_class_names(self, class_map_scene, tmp_path):
        ctx, pixel_classes, pixel_uuids, image = class_map_scene
        res = int2(CM_W, CM_H)
        with pytest.raises(ValueError, match="at least one"):
            annotation.writeClassMapSegmentationMasks(ctx, pixel_classes, pixel_uuids, res, {},
                                                      str(tmp_path / "x.json"), image)
        with pytest.raises(ValueError, match="1 or more"):
            annotation.writeClassMapSegmentationMasks(ctx, pixel_classes, pixel_uuids, res, {0: "none"},
                                                      str(tmp_path / "x.json"), image)
        with pytest.raises(TypeError, match="dict"):
            annotation.writeClassMapSegmentationMasks(ctx, pixel_classes, pixel_uuids, res, ["lamina"],
                                                      str(tmp_path / "x.json"), image)
        with pytest.raises(TypeError, match="names"):
            annotation.writeClassMapSegmentationMasks(ctx, pixel_classes, pixel_uuids, res, {1: 7},
                                                      str(tmp_path / "x.json"), image)
