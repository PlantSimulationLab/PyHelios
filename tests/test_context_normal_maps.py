"""Tests for the helios-core 1.3.97 Context additions: normal and bump maps, decoded
NormalMapTexels, the normal-map free functions of core/global.h, and getDeletedUUIDs(mark)."""

import math
import struct
import zlib

import numpy as np
import pytest

from pyhelios import Context, Global, NormalMapKind, NormalMapTexels
from pyhelios.exceptions import HeliosError
from pyhelios.types import vec2, vec3, RGBcolor


# ---------------------------------------------------------------------------
# Minimal PNG writer (no Pillow dependency)
# ---------------------------------------------------------------------------

def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def _write_png(path, pixels: np.ndarray):
    """Write an (H, W, 3) uint8 RGB, or an (H, W) uint16 grayscale, array as a PNG."""
    if pixels.ndim == 3:
        height, width, _ = pixels.shape
        bit_depth, color_type = 8, 2
        rows = [b"\x00" + pixels[r].astype(np.uint8).tobytes() for r in range(height)]
    else:
        height, width = pixels.shape
        bit_depth, color_type = 16, 0
        rows = [b"\x00" + pixels[r].astype(">u2").tobytes() for r in range(height)]
    header = struct.pack(">IIBBBBB", width, height, bit_depth, color_type, 0, 0, 0)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(_png_chunk(b"IHDR", header))
        f.write(_png_chunk(b"IDAT", zlib.compress(b"".join(rows))))
        f.write(_png_chunk(b"IEND", b""))
    return str(path)


@pytest.fixture
def maps(tmp_path):
    """A tilted tangent-space normal map, another normal map, and a 16-bit bump ramp."""
    normal = np.zeros((4, 4, 3), dtype=np.uint8)
    normal[:] = (218, 128, 218)  # tilted toward +x
    other = np.zeros((4, 4, 3), dtype=np.uint8)
    other[:] = (128, 218, 218)  # tilted toward +y
    ramp = np.tile((1000 * np.arange(8)).astype(np.uint16), (6, 1))  # rises to the right
    return {
        "normal": _write_png(tmp_path / "normal.png", normal),
        "other": _write_png(tmp_path / "other.png", other),
        "bump": _write_png(tmp_path / "bump.png", ramp),
    }


def _expected_tilt_x():
    c = np.array([218, 128, 218]) / 255.0 * 2 - 1
    return c / np.linalg.norm(c)


# ---------------------------------------------------------------------------
# Cross-platform: enum and exports
# ---------------------------------------------------------------------------

@pytest.mark.cross_platform
class TestNormalMapTypes:
    def test_normal_map_kind_values_match_native_enum(self):
        assert NormalMapKind.NORMAL_MAP_NONE == 0
        assert NormalMapKind.NORMAL_MAP_TANGENT_SPACE == 1
        assert NormalMapKind.NORMAL_MAP_BUMP == 2

    def test_exported_from_types(self):
        from pyhelios.types import NormalMapKind as K
        assert K is NormalMapKind

    def test_texels_need_a_handle(self):
        with pytest.raises(RuntimeError, match="native handle"):
            NormalMapTexels(None)


# ---------------------------------------------------------------------------
# Native: materials
# ---------------------------------------------------------------------------

@pytest.mark.native_only
class TestMaterialNormalMaps:
    def test_setters_getters_and_clearing(self, maps):
        with Context() as ctx:
            ctx.addMaterial("bark")
            assert ctx.getMaterialNormalMapKind("bark") == NormalMapKind.NORMAL_MAP_NONE
            assert ctx.getMaterialNormalMapFile("bark") == ""
            assert ctx.getMaterialNormalMapStrength("bark") == pytest.approx(1.0)

            ctx.setMaterialNormalMap("bark", maps["normal"], 1.5, True)
            assert ctx.getMaterialNormalMapKind("bark") == NormalMapKind.NORMAL_MAP_TANGENT_SPACE
            assert ctx.getMaterialNormalMapFile("bark") == maps["normal"]
            assert ctx.getMaterialNormalMapStrength("bark") == pytest.approx(1.5)
            assert ctx.isMaterialNormalMapGreenFlipped("bark") is True

            # One map per material: a bump map is refused until the normal map is cleared
            with pytest.raises(HeliosError):
                ctx.setMaterialBumpMap("bark", maps["bump"], 5.0)

            ctx.setMaterialNormalMapStrength("bark", 0.5)
            assert ctx.getMaterialNormalMapStrength("bark") == pytest.approx(0.5)

            ctx.clearMaterialNormalMap("bark")
            assert ctx.getMaterialNormalMapKind("bark") == NormalMapKind.NORMAL_MAP_NONE
            with pytest.raises(HeliosError):
                ctx.setMaterialNormalMapStrength("bark", 2.0)

            ctx.setMaterialBumpMap("bark", maps["bump"], 5.0)
            assert ctx.getMaterialNormalMapKind("bark") == NormalMapKind.NORMAL_MAP_BUMP
            assert ctx.isMaterialNormalMapGreenFlipped("bark") is False

    def test_bad_images_and_strengths_are_refused(self, maps):
        with Context() as ctx:
            ctx.addMaterial("bark")
            with pytest.raises(HeliosError):
                ctx.setMaterialNormalMap("bark", maps["bump"])  # grayscale given as a normal map
            with pytest.raises(HeliosError):
                ctx.setMaterialNormalMap("bark", "does_not_exist_normal.png")
            with pytest.raises(HeliosError):
                ctx.setMaterialNormalMap("bark", maps["normal"], strength=0.0)
            with pytest.raises(HeliosError):
                ctx.setMaterialNormalMap("no_such_material", maps["normal"])
            assert ctx.getMaterialNormalMapKind("bark") == NormalMapKind.NORMAL_MAP_NONE

    def test_argument_types_are_validated(self, maps):
        with Context() as ctx:
            ctx.addMaterial("bark")
            with pytest.raises(ValueError):
                ctx.setMaterialNormalMap(5, maps["normal"])
            with pytest.raises(ValueError):
                ctx.setMaterialNormalMap("bark", maps["normal"], "1.0")
            with pytest.raises(ValueError):
                ctx.setMaterialNormalMap("bark", maps["normal"], 1.0, 1)
            with pytest.raises(ValueError):
                ctx.setMaterialNormalMap("bark", maps["normal"], flip_green="yes")
            with pytest.raises(ValueError):
                ctx.setMaterialBumpMap("bark", maps["bump"], strength=True)

    def test_material_texels_are_cached_and_shared(self, maps):
        with Context() as ctx:
            ctx.addMaterial("a")
            ctx.addMaterial("none")
            ctx.setMaterialNormalMap("a", maps["normal"])
            texels = ctx.getMaterialNormalMapTexels(ctx.getMaterialIDFromLabel("a"))
            assert isinstance(texels, NormalMapTexels)
            assert texels.kind == NormalMapKind.NORMAL_MAP_TANGENT_SPACE
            assert texels.resolution == (4, 4)
            assert texels.strength == pytest.approx(1.0)
            assert texels.flip_green is False
            assert ctx.getMaterialNormalMapTexels(ctx.getMaterialIDFromLabel("none")) is None

            ctx.clearNormalMapCache()
            # Earlier holders keep their copy after the cache is released
            assert texels.resolution == (4, 4)
            n = texels.getNormal(1, 1)
            assert n.x == pytest.approx(_expected_tilt_x()[0], rel=1e-3)

    def test_texels_outlive_context(self, maps):
        ctx = Context()
        texels = ctx.getNormalMapTexels(maps["normal"], NormalMapKind.NORMAL_MAP_TANGENT_SPACE)
        ctx.__exit__(None, None, None)
        assert texels.getNormal(0, 0).z > 0


# ---------------------------------------------------------------------------
# Native: primitives
# ---------------------------------------------------------------------------

@pytest.mark.native_only
class TestPrimitiveNormalMaps:
    def test_primitive_map_is_copy_on_write(self, maps):
        with Context() as ctx:
            p0 = ctx.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1), color=RGBcolor(0.2, 0.6, 0.2))
            p1 = ctx.addPatch(center=vec3(2, 0, 0), size=vec2(1, 1), color=RGBcolor(0.2, 0.6, 0.2))
            original = ctx.getPrimitiveMaterialLabel(p0)

            ctx.setPrimitiveNormalMap(p0, maps["normal"])
            assert ctx.getPrimitiveNormalMapKind(p0) == NormalMapKind.NORMAL_MAP_TANGENT_SPACE
            assert ctx.getPrimitiveNormalMapFile(p0) == maps["normal"]
            assert ctx.getPrimitiveNormalMapKind(p1) == NormalMapKind.NORMAL_MAP_NONE
            assert ctx.getPrimitiveMaterialLabel(p0) != original

            ctx.clearPrimitiveNormalMap(p0)
            assert ctx.getPrimitiveNormalMapKind(p0) == NormalMapKind.NORMAL_MAP_NONE
            assert ctx.getPrimitiveMaterialLabel(p0) == original

    def test_list_forms_and_bump_map(self, maps):
        with Context() as ctx:
            ctx.addMaterial("leaf")
            p0 = ctx.addPatch()
            p1 = ctx.addPatch()
            ctx.assignMaterialToPrimitive([p0, p1], "leaf")
            ctx.setPrimitiveBumpMap([p0], maps["bump"], 3.0)
            assert ctx.getPrimitiveNormalMapKind(p0) == NormalMapKind.NORMAL_MAP_BUMP
            assert ctx.getPrimitiveNormalMapStrength(p0) == pytest.approx(3.0)
            assert ctx.getPrimitiveNormalMapKind(p1) == NormalMapKind.NORMAL_MAP_NONE
            assert ctx.getMaterialNormalMapKind("leaf") == NormalMapKind.NORMAL_MAP_NONE

            ctx.setPrimitiveNormalMap([p0, p1], maps["other"], strength=2.0, flip_green=True)
            for p in (p0, p1):
                assert ctx.getPrimitiveNormalMapFile(p) == maps["other"]
                assert ctx.getPrimitiveNormalMapStrength(p) == pytest.approx(2.0)
            ctx.clearPrimitiveNormalMap([p0, p1])
            assert ctx.getPrimitiveNormalMapKind(p1) == NormalMapKind.NORMAL_MAP_NONE

    def test_list_is_checked_before_any_change(self, maps):
        with Context() as ctx:
            patch = ctx.addPatch()
            bare = ctx.addTriangle(vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0))
            with pytest.raises(HeliosError):
                ctx.setPrimitiveNormalMap(bare, maps["normal"])
            with pytest.raises(HeliosError):
                ctx.setPrimitiveNormalMap([patch, bare], maps["normal"])
            assert ctx.getPrimitiveNormalMapKind(patch) == NormalMapKind.NORMAL_MAP_NONE
            with pytest.raises(HeliosError):
                ctx.getPrimitiveNormalMapUV(bare)

    def test_normal_map_uv(self, maps):
        with Context() as ctx:
            patch = ctx.addPatch()
            uv = ctx.getPrimitiveNormalMapUV(patch)
            assert [(round(c.x, 6), round(c.y, 6)) for c in uv] == [(0, 0), (1, 0), (1, 1), (0, 1)]
            tri = ctx.addTriangleTextured(vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0), maps["other"],
                                          vec2(0, 0), vec2(1, 0), vec2(0, 1))
            ctx.setPrimitiveNormalMap(tri, maps["normal"])
            tri_uv = ctx.getPrimitiveNormalMapUV(tri)
            assert len(tri_uv) == 3
            assert (tri_uv[1].x, tri_uv[1].y) == pytest.approx((1.0, 0.0))

    def test_uuid_argument_validation(self, maps):
        with Context() as ctx:
            p = ctx.addPatch()
            with pytest.raises(ValueError):
                ctx.setPrimitiveNormalMap("1", maps["normal"])
            with pytest.raises(ValueError):
                ctx.setPrimitiveNormalMap([p, -1], maps["normal"])
            with pytest.raises(ValueError):
                ctx.getPrimitiveNormalMapKind([p])
            with pytest.raises(ValueError):
                ctx.setPrimitiveBumpMap(p, maps["bump"], None)

    def test_material_map_survives_xml_round_trip(self, maps, tmp_path):
        xml = str(tmp_path / "scene.xml")
        with Context() as ctx:
            ctx.addMaterial("leaf")
            p = ctx.addPatch()
            ctx.assignMaterialToPrimitive(p, "leaf")
            ctx.setMaterialNormalMap("leaf", maps["normal"], 0.75, True)
            ctx.writeXML(xml, quiet=True)
        with Context() as ctx:
            uuids = ctx.loadXML(xml, quiet=True)
            assert ctx.getPrimitiveNormalMapKind(uuids[0]) == NormalMapKind.NORMAL_MAP_TANGENT_SPACE
            assert ctx.getPrimitiveNormalMapStrength(uuids[0]) == pytest.approx(0.75)


# ---------------------------------------------------------------------------
# Native: NormalMapTexels and the free functions
# ---------------------------------------------------------------------------

@pytest.mark.native_only
class TestNormalMapTexelsAndFreeFunctions:
    def test_decode_tangent_space(self, maps):
        texels = Global.decodeNormalMapImage(maps["normal"], NormalMapKind.NORMAL_MAP_TANGENT_SPACE)
        assert texels.resolution == (4, 4)
        assert texels.getMemoryBytes() == 4 * 4 * 2 * 2
        expected = _expected_tilt_x()
        n = texels.getNormal(2, 1)
        assert (n.x, n.y, n.z) == pytest.approx(tuple(expected), rel=1e-3, abs=1e-3)
        assert texels.xy.shape == (4, 4, 2)
        assert texels.xy.dtype == np.int16
        assert texels.xy[1, 2, 0] / 32767.0 == pytest.approx(n.x, rel=1e-3)

    def test_flip_and_strength(self, maps):
        plain = Global.decodeNormalMapImage(maps["other"], NormalMapKind.NORMAL_MAP_TANGENT_SPACE).getNormal(0, 0)
        flipped = Global.decodeNormalMapImage(maps["other"], NormalMapKind.NORMAL_MAP_TANGENT_SPACE, 1.0, True).getNormal(0, 0)
        strong = Global.decodeNormalMapImage(maps["other"], NormalMapKind.NORMAL_MAP_TANGENT_SPACE, 2.0).getNormal(0, 0)
        assert plain.y > 0.5
        assert flipped.y == pytest.approx(-plain.y, rel=1e-4)
        e = np.array([2 * plain.x, 2 * plain.y, plain.z])
        e /= np.linalg.norm(e)
        assert strong.y == pytest.approx(e[1], rel=1e-4)

    def test_decode_bump_ramp(self, maps):
        strength = 50.0
        a = 1000.0 / 65535.0
        texels = Global.decodeNormalMapImage(maps["bump"], NormalMapKind.NORMAL_MAP_BUMP, strength)
        e = np.array([-strength * a, 0.0, 1.0])
        e /= np.linalg.norm(e)
        n = texels.getNormal(3, 2)
        assert n.x == pytest.approx(e[0], rel=1e-3)
        assert abs(n.y) < 1e-4

    def test_decode_rejects_bad_arguments(self, maps):
        with pytest.raises(HeliosError):
            Global.decodeNormalMapImage(maps["normal"], NormalMapKind.NORMAL_MAP_TANGENT_SPACE, 0.0)
        with pytest.raises(HeliosError):
            Global.decodeNormalMapImage(maps["normal"], NormalMapKind.NORMAL_MAP_BUMP, 1.0, True)
        with pytest.raises(HeliosError):
            Global.decodeNormalMapImage(maps["normal"], NormalMapKind.NORMAL_MAP_NONE)
        with pytest.raises(HeliosError):
            Global.decodeNormalMapImage(maps["bump"], NormalMapKind.NORMAL_MAP_TANGENT_SPACE)
        with pytest.raises(ValueError):
            Global.decodeNormalMapImage(maps["normal"], "tangent")

    def test_get_normal_out_of_range_raises_instead_of_reading_past_the_image(self, maps):
        texels = Global.decodeNormalMapImage(maps["normal"], NormalMapKind.NORMAL_MAP_TANGENT_SPACE)
        for col, row in ((4, 0), (0, 4), (-1, 0)):
            with pytest.raises(HeliosError, match="outside"):
                texels.getNormal(col, row)
        with pytest.raises(ValueError):
            texels.getNormal(1.0, 0)

    def test_sampling(self, maps):
        texels = Global.decodeNormalMapImage(maps["normal"], NormalMapKind.NORMAL_MAP_TANGENT_SPACE)
        expected = _expected_tilt_x()
        n = texels.sampleNearest(vec2(0.3, 0.7))
        assert (n.x, n.y, n.z) == pytest.approx(tuple(expected), abs=1e-3)
        batch = texels.sampleBilinear(np.array([[0.0, 0.0], [0.5, 0.5], [1.0, 1.0]]))
        assert batch.shape == (3, 3)
        np.testing.assert_allclose(batch, np.tile(expected, (3, 1)), atol=1e-3)
        with pytest.raises(ValueError):
            texels.sampleNearest(np.zeros((2, 3)))

    def test_context_cache_matches_free_decode(self, maps):
        with Context() as ctx:
            cached = ctx.getNormalMapTexels(maps["bump"], NormalMapKind.NORMAL_MAP_BUMP, 10.0)
        direct = Global.decodeNormalMapImage(maps["bump"], NormalMapKind.NORMAL_MAP_BUMP, 10.0)
        np.testing.assert_array_equal(cached.xy, direct.xy)

    def test_classify_bump_image(self, maps, tmp_path):
        gentle = np.zeros((4, 4, 3), dtype=np.uint8)
        gentle[:] = (150, 128, 245)  # mean normal mostly along +z
        gentle_file = _write_png(tmp_path / "gentle.png", gentle)
        assert Global.classifyBumpImage(maps["bump"]) == NormalMapKind.NORMAL_MAP_BUMP
        assert Global.classifyBumpImage(gentle_file) == NormalMapKind.NORMAL_MAP_TANGENT_SPACE
        # A strongly tilted map is neither a height map nor a plausible normal map
        with pytest.raises(HeliosError, match="neither"):
            Global.classifyBumpImage(maps["normal"])

    def test_tangent_frame_and_apply(self):
        frame = Global.computeTangentFrame(vec3(0, 0, 0), vec3(2, 0, 0), vec3(0, 3, 0),
                                           vec2(0, 0), vec2(1, 0), vec2(0, 1))
        assert frame is not None
        dPdu, dPdv = frame
        assert (dPdu.x, dPdu.y, dPdu.z) == pytest.approx((2, 0, 0))
        assert (dPdv.x, dPdv.y, dPdv.z) == pytest.approx((0, 3, 0))

        t = 1 / math.sqrt(2)
        n = Global.applyTangentSpaceNormal(vec3(t, 0, t), dPdu, dPdv, vec3(0, 0, 1))
        assert (n.x, n.y, n.z) == pytest.approx((t, 0, t), abs=1e-6)

        # Collinear (u,v) give no frame
        assert Global.computeTangentFrame(vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0),
                                          vec2(0, 0), vec2(1, 1), vec2(2, 2)) is None
        with pytest.raises(ValueError):
            Global.computeTangentFrame(vec2(0, 0), vec3(1, 0, 0), vec3(0, 1, 0), vec2(0, 0), vec2(1, 0), vec2(0, 1))
        with pytest.raises(ValueError):
            Global.applyTangentSpaceNormal(vec3(0, 0, 1), dPdu, dPdv, RGBcolor(0, 0, 1))


# ---------------------------------------------------------------------------
# Native: getDeletedUUIDs(mark)
# ---------------------------------------------------------------------------

@pytest.mark.native_only
class TestDeletedUUIDsSinceMark:
    def test_mark_survives_markGeometryClean(self):
        with Context() as ctx:
            a, b, c = ctx.addPatch(), ctx.addPatch(), ctx.addPatch()
            _, mark = ctx.getModifiedUUIDs()
            ctx.deletePrimitive(b)
            ctx.markGeometryClean()
            assert ctx.getDeletedUUIDs() == []  # the shared list was emptied
            assert ctx.getDeletedUUIDs(mark) == [b]  # the caller's own view was not
            ctx.deletePrimitive([c, a])
            assert ctx.getDeletedUUIDs(mark) == [b, c, a]
            assert set(ctx.getDeletedUUIDs(0)) == {a, b, c}

    def test_does_not_advance_mark_and_pairs_with_getModifiedUUIDs(self):
        with Context() as ctx:
            a, b = ctx.addPatch(), ctx.addPatch()
            _, mark = ctx.getModifiedUUIDs()
            ctx.deletePrimitive(a)
            previous = mark
            modified, mark = ctx.getModifiedUUIDs(mark)
            assert a not in modified
            assert ctx.getDeletedUUIDs(previous) == [a]
            assert ctx.getDeletedUUIDs(previous) == [a]
            assert ctx.getDeletedUUIDs(mark) == []

    def test_mark_validation(self):
        with Context() as ctx:
            for bad in (-1, 1.5, "0", True, 2 ** 64):
                with pytest.raises(ValueError):
                    ctx.getDeletedUUIDs(bad)
