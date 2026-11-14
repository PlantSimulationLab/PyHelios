"""
Tests for adding and modifying many triangles in one native call.

Covers:
- addTrianglesFromArraysTextured returning UUIDs in face order when material IDs interleave.
- addTrianglesFromArraysTextured failing fast instead of falling back to a per-triangle loop.
- addTriangleSoup: an (N, 3, 3) triangle soup with optional UVs and per-triangle texture
  indices, which must produce exactly what N separate addTriangle/addTriangleTextured calls do.
- setTriangleVerticesBatch: rewriting N triangles' vertices in place.
- setTriangleVertices / setTriangleVerticesBatch rejecting non-triangle and missing UUIDs
  instead of crashing.
"""

import os
import struct
import subprocess
import sys
import textwrap
import zlib

import numpy as np
import pytest

from pyhelios import Context
from pyhelios.types import vec2, vec3
from pyhelios.wrappers import UContextWrapper as context_wrapper


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
def two_textures(tmp_path):
    """An alpha-masked 'leaf' texture (left half transparent) and a fully opaque texture."""
    leaf = _write_rgba_png(tmp_path / "leaf.png", 8, 8,
                           lambda x, y: (0, 180, 0, 255 if x >= 4 else 0))
    bark = _write_rgba_png(tmp_path / "bark.png", 8, 8,
                           lambda x, y: (120, 80, 40, 255))
    return [os.path.abspath(leaf), os.path.abspath(bark)]


def _strip_mesh(n_faces):
    """An indexed strip of n_faces triangles with distinct vertices and UVs."""
    n_verts = n_faces + 2
    xs = np.arange(n_verts, dtype=np.float64)
    vertices = np.stack([xs, (np.arange(n_verts) % 2).astype(np.float64), 0.1 * xs], axis=1)
    uv = np.stack([xs / (n_verts - 1), (np.arange(n_verts) % 2).astype(np.float64)], axis=1)
    faces = np.array([[i, i + 1, i + 2] for i in range(n_faces)], dtype=np.int64)
    return vertices, faces, uv


def _soup(n, seed=0):
    """N random non-degenerate triangles as an (N, 3, 3) array with (N, 3, 2) UVs."""
    rng = np.random.default_rng(seed)
    base = rng.uniform(-5, 5, size=(n, 1, 3))
    corners = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float64)
    jitter = rng.uniform(-0.2, 0.2, size=(n, 3, 3))
    vertices = (base + corners + jitter).astype(np.float32)
    uv = rng.uniform(0, 1, size=(n, 3, 2)).astype(np.float32)
    return vertices, uv


def _vertices_of(ctx, uuid):
    return np.array([[v.x, v.y, v.z] for v in ctx.getPrimitiveVertices(uuid)], dtype=np.float32)


def _uv_of(ctx, uuid):
    return np.array([[p.x, p.y] for p in ctx.getPrimitiveTextureUV(uuid)], dtype=np.float32)


requires_bulk = pytest.mark.skipif(
    not getattr(context_wrapper, "_TRIANGLE_BULK_FUNCTIONS_AVAILABLE", False),
    reason="Bulk triangle functions not in the native library (rebuild with build_scripts/build_helios)")


@pytest.mark.native_only
class TestMultiTexturedFaceOrder:
    """addTrianglesFromArraysTextured must return UUIDs in face order."""

    def test_interleaved_material_ids_return_uuids_in_face_order(self, basic_context, two_textures):
        vertices, faces, uv = _strip_mesh(6)
        material_ids = np.array([0, 1, 0, 1, 0, 1], dtype=np.uint32)

        uuids = basic_context.addTrianglesFromArraysTextured(
            vertices, faces, uv, two_textures, material_ids)

        assert len(uuids) == len(faces)
        for i, uuid in enumerate(uuids):
            expected = vertices[faces[i]].astype(np.float32)
            np.testing.assert_allclose(_vertices_of(basic_context, uuid), expected, atol=1e-5,
                                       err_msg=f"UUID {i} does not hold face {i}'s vertices")
            assert basic_context.getPrimitiveTextureFile(uuid) == two_textures[material_ids[i]]

    def test_missing_native_function_raises_instead_of_falling_back(
            self, basic_context, two_textures, monkeypatch):
        vertices, faces, uv = _strip_mesh(2)
        available = [f for f in context_wrapper._AVAILABLE_TRIANGLE_FUNCTIONS
                     if f != 'addTrianglesFromArraysMultiTextured']
        monkeypatch.setattr(context_wrapper, "_AVAILABLE_TRIANGLE_FUNCTIONS", available)
        before = basic_context.getPrimitiveCount()

        with pytest.raises(NotImplementedError, match="addTrianglesFromArraysMultiTextured"):
            basic_context.addTrianglesFromArraysTextured(vertices, faces, uv, two_textures)
        assert basic_context.getPrimitiveCount() == before


_NON_TRIANGLE_SCRIPT = textwrap.dedent("""
    import sys
    from pyhelios import Context
    from pyhelios.types import vec2, vec3
    ctx = Context()
    patch = ctx.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
    try:
        ctx.setTriangleVertices(patch, vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0))
    except Exception as e:
        print("RAISED:", type(e).__name__, e)
        sys.exit(0)
    print("NO ERROR")
    sys.exit(3)
""")


@pytest.mark.native_only
class TestSetTriangleVerticesRejectsNonTriangles:
    """A non-triangle UUID must raise, not dereference a null Triangle pointer."""

    def test_single_call_on_patch_raises_instead_of_crashing(self):
        result = subprocess.run([sys.executable, "-c", _NON_TRIANGLE_SCRIPT],
                                capture_output=True, text=True, timeout=120)
        assert result.returncode == 0, (
            f"setTriangleVertices on a patch exited with {result.returncode} "
            f"(negative = killed by signal)\nstdout: {result.stdout}\nstderr: {result.stderr[-2000:]}")
        assert "RAISED:" in result.stdout
        assert "not a triangle" in result.stdout


@pytest.mark.native_only
@requires_bulk
class TestAddTriangleSoup:
    """addTriangleSoup must equal N separate per-triangle adds."""

    def test_matches_per_triangle_adds_on_textured_mesh(self, two_textures):
        n = 60
        vertices, uv = _soup(n)
        # Mix the alpha-masked texture, the opaque texture and untextured triangles.
        texture_index = np.array([(i % 3) - 1 for i in range(n)], dtype=np.int32)  # -1, 0, 1, ...

        with Context() as bulk_ctx, Context() as ref_ctx:
            bulk = bulk_ctx.addTriangleSoup(vertices, uv=uv, texture_index=texture_index,
                                            texture_files=two_textures)
            ref = []
            for i in range(n):
                v = [vec3(*map(float, vertices[i, k])) for k in range(3)]
                if texture_index[i] < 0:
                    ref.append(ref_ctx.addTriangle(*v))
                else:
                    t = [vec2(*map(float, uv[i, k])) for k in range(3)]
                    ref.append(ref_ctx.addTriangleTextured(v[0], v[1], v[2],
                                                           two_textures[texture_index[i]], *t))

            assert isinstance(bulk, list) and len(bulk) == n
            assert bulk == ref, "UUIDs differ from the per-triangle sequence"
            for i, (b, r) in enumerate(zip(bulk, ref)):
                assert bulk_ctx.getPrimitiveType(b) == ref_ctx.getPrimitiveType(r)
                np.testing.assert_array_equal(_vertices_of(bulk_ctx, b), _vertices_of(ref_ctx, r))
                # Helios stores a triangle as a transformation matrix, so reading back the
                # input can differ by an ULP; bulk vs per-call above must match exactly.
                np.testing.assert_allclose(_vertices_of(bulk_ctx, b), vertices[i], rtol=0, atol=1e-6)
                assert bulk_ctx.getPrimitiveTextureFile(b) == ref_ctx.getPrimitiveTextureFile(r)
                assert bulk_ctx.getPrimitiveSolidFraction(b) == ref_ctx.getPrimitiveSolidFraction(r)
                assert bulk_ctx.getPrimitiveMaterialLabel(b) == ref_ctx.getPrimitiveMaterialLabel(r)
                assert bulk_ctx.getPrimitiveMaterialID(b) == ref_ctx.getPrimitiveMaterialID(r)
                if texture_index[i] >= 0:
                    np.testing.assert_array_equal(_uv_of(bulk_ctx, b), _uv_of(ref_ctx, r))
                    assert bulk_ctx.getPrimitiveTextureFile(b) == two_textures[texture_index[i]]
                else:
                    assert bulk_ctx.getPrimitiveTextureFile(b) == ""

            # The alpha mask must actually have been applied (otherwise solid fraction is
            # trivially 1 everywhere and the comparison above proves little).
            leaf_fractions = [bulk_ctx.getPrimitiveSolidFraction(b)
                              for b, t in zip(bulk, texture_index) if t == 0]
            assert any(f < 1.0 for f in leaf_fractions)

    def test_untextured_only(self, basic_context):
        vertices, _ = _soup(10)
        uuids = basic_context.addTriangleSoup(vertices)
        assert len(uuids) == 10
        for i, u in enumerate(uuids):
            np.testing.assert_allclose(_vertices_of(basic_context, u), vertices[i], rtol=0, atol=1e-6)
            assert basic_context.getPrimitiveTextureFile(u) == ""

    def test_float64_input_accepted(self, basic_context):
        vertices, _ = _soup(4)
        uuids = basic_context.addTriangleSoup(vertices.astype(np.float64))
        np.testing.assert_allclose(_vertices_of(basic_context, uuids[2]), vertices[2], rtol=0, atol=1e-6)

    def test_empty_returns_empty_list(self, basic_context):
        assert basic_context.addTriangleSoup(np.empty((0, 3, 3), dtype=np.float32)) == []

    @pytest.mark.parametrize("make_kwargs, exc, match", [
        (lambda v, uv, tex: dict(vertices=v.reshape(-1, 9)), ValueError, r"\(N, 3, 3\)"),
        (lambda v, uv, tex: dict(vertices=v.astype(np.int32)), ValueError, "floating"),
        (lambda v, uv, tex: dict(vertices=v.tolist()), ValueError, "ndarray"),
        (lambda v, uv, tex: dict(vertices=v, uv=uv[:, :, :1], texture_index=np.zeros(len(v), np.int32),
                                 texture_files=tex), ValueError, r"\(N, 3, 2\)"),
        (lambda v, uv, tex: dict(vertices=v, uv=uv[:-1], texture_index=np.zeros(len(v), np.int32),
                                 texture_files=tex), ValueError, r"\(N, 3, 2\)"),
        (lambda v, uv, tex: dict(vertices=v, uv=uv.astype(np.int64), texture_index=np.zeros(len(v), np.int32),
                                 texture_files=tex), ValueError, "floating"),
        (lambda v, uv, tex: dict(vertices=v, uv=uv, texture_index=np.full(len(v), 2, np.int32),
                                 texture_files=tex), ValueError, "out of range"),
        (lambda v, uv, tex: dict(vertices=v, uv=uv, texture_index=np.full(len(v), -2, np.int32),
                                 texture_files=tex), ValueError, "out of range"),
        (lambda v, uv, tex: dict(vertices=v, uv=uv, texture_index=np.zeros(len(v), np.float32),
                                 texture_files=tex), ValueError, "integer"),
        (lambda v, uv, tex: dict(vertices=v, uv=uv, texture_index=np.zeros(len(v) - 1, np.int32),
                                 texture_files=tex), ValueError, r"\(N,\)"),
        (lambda v, uv, tex: dict(vertices=v, texture_index=np.zeros(len(v), np.int32),
                                 texture_files=tex), ValueError, "uv"),
        (lambda v, uv, tex: dict(vertices=v, uv=uv, texture_index=np.zeros(len(v), np.int32)),
         ValueError, "texture_files"),
        (lambda v, uv, tex: dict(vertices=v, uv=uv, texture_index=np.zeros(len(v), np.int32),
                                 texture_files=["/nonexistent/leaf.png"]), FileNotFoundError, "leaf.png"),
        (lambda v, uv, tex: dict(vertices=v, uv=uv, texture_index=np.zeros(len(v), np.int32),
                                 texture_files=tex[0]), ValueError, "list"),
    ])
    def test_invalid_input_raises_and_adds_nothing(self, basic_context, two_textures,
                                                   make_kwargs, exc, match):
        vertices, uv = _soup(5)
        existing = basic_context.addTriangle(vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0))
        before = basic_context.getPrimitiveCount()
        with pytest.raises(exc, match=match):
            basic_context.addTriangleSoup(**make_kwargs(vertices, uv, two_textures))
        assert basic_context.getPrimitiveCount() == before
        assert list(basic_context.getAllUUIDs()) == [existing]

    def test_unreadable_texture_rolls_back(self, basic_context, tmp_path, two_textures):
        """A texture that exists but fails to load in Helios leaves no triangles behind."""
        bad = tmp_path / "corrupt.png"
        bad.write_bytes(b"not a png")
        vertices, uv = _soup(6)
        texture_index = np.array([0, 0, 0, 1, 1, 1], dtype=np.int32)
        before = basic_context.getPrimitiveCount()
        with pytest.raises(Exception):
            basic_context.addTriangleSoup(vertices, uv=uv, texture_index=texture_index,
                                          texture_files=[two_textures[0], str(bad)])
        assert basic_context.getPrimitiveCount() == before


@pytest.mark.native_only
@requires_bulk
class TestSetTriangleVerticesBatch:
    """setTriangleVerticesBatch must equal N single setTriangleVertices calls."""

    def test_matches_per_primitive_calls(self, two_textures):
        n = 40
        vertices, uv = _soup(n, seed=1)
        new_vertices, _ = _soup(n, seed=2)
        texture_index = np.array([(i % 2) - 1 for i in range(n)], dtype=np.int32)

        with Context() as bulk_ctx, Context() as ref_ctx:
            bulk = bulk_ctx.addTriangleSoup(vertices, uv=uv, texture_index=texture_index,
                                            texture_files=two_textures)
            ref = ref_ctx.addTriangleSoup(vertices, uv=uv, texture_index=texture_index,
                                          texture_files=two_textures)

            bulk_ctx.setTriangleVerticesBatch(bulk, new_vertices)
            for i, u in enumerate(ref):
                ref_ctx.setTriangleVertices(u, *[vec3(*map(float, new_vertices[i, k])) for k in range(3)])

            assert sorted(bulk_ctx.getAllUUIDs()) == sorted(bulk)
            for i, (b, r) in enumerate(zip(bulk, ref)):
                np.testing.assert_allclose(_vertices_of(bulk_ctx, b), new_vertices[i], rtol=0, atol=1e-6)
                np.testing.assert_array_equal(_vertices_of(bulk_ctx, b), _vertices_of(ref_ctx, r))
                nb, nr = bulk_ctx.getPrimitiveNormal(b), ref_ctx.getPrimitiveNormal(r)
                assert (nb.x, nb.y, nb.z) == (nr.x, nr.y, nr.z)
                assert bulk_ctx.getPrimitiveArea(b) == ref_ctx.getPrimitiveArea(r)
                assert bulk_ctx.getPrimitiveSolidFraction(b) == ref_ctx.getPrimitiveSolidFraction(r)

    def test_accepts_numpy_uuid_array(self, basic_context):
        vertices, _ = _soup(3)
        uuids = basic_context.addTriangleSoup(vertices)
        new_vertices, _ = _soup(3, seed=5)
        basic_context.setTriangleVerticesBatch(np.array(uuids, dtype=np.uint32), new_vertices)
        np.testing.assert_allclose(_vertices_of(basic_context, uuids[1]), new_vertices[1], rtol=0, atol=1e-6)

    def test_empty_is_noop(self, basic_context):
        basic_context.setTriangleVerticesBatch([], np.empty((0, 3, 3), dtype=np.float32))

    @pytest.mark.parametrize("case", ["missing_uuid", "patch_uuid", "count_mismatch",
                                      "bad_shape", "int_dtype", "negative_uuid"])
    def test_invalid_input_raises_and_modifies_nothing(self, basic_context, case):
        vertices, _ = _soup(4)
        uuids = basic_context.addTriangleSoup(vertices)
        patch = basic_context.addPatch(center=vec3(9, 9, 9), size=vec2(1, 1))
        new_vertices, _ = _soup(4, seed=7)

        if case == "missing_uuid":
            args, exc, match = (uuids[:3] + [999999], new_vertices), Exception, "999999"
        elif case == "patch_uuid":
            args, exc, match = (uuids[:3] + [patch], new_vertices), Exception, "not a triangle"
        elif case == "count_mismatch":
            args, exc, match = (uuids, new_vertices[:3]), ValueError, r"\(4, 3, 3\)"
        elif case == "bad_shape":
            args, exc, match = (uuids, new_vertices.reshape(4, 9)), ValueError, r"\(4, 3, 3\)"
        elif case == "int_dtype":
            args, exc, match = (uuids, new_vertices.astype(np.int32)), ValueError, "floating"
        else:
            args, exc, match = ([-1] + uuids[1:], new_vertices), ValueError, "non-negative"

        with pytest.raises(exc, match=match):
            basic_context.setTriangleVerticesBatch(*args)
        for i, u in enumerate(uuids):
            np.testing.assert_allclose(_vertices_of(basic_context, u), vertices[i], rtol=0, atol=1e-6)


@pytest.mark.native_only
class TestAddTrianglesFromArraysNative:
    """addTrianglesFromArrays (untextured) results are unchanged by moving its loop native."""

    def test_vertices_and_colors(self, basic_context):
        vertices, faces, _ = _strip_mesh(5)
        face_colors = np.linspace(0, 1, 15).reshape(5, 3)
        uuids = basic_context.addTrianglesFromArrays(vertices, faces, face_colors)
        assert len(uuids) == 5
        for i, u in enumerate(uuids):
            np.testing.assert_allclose(_vertices_of(basic_context, u),
                                       vertices[faces[i]].astype(np.float32), atol=1e-6)
            c = basic_context.getPrimitiveColor(u)
            np.testing.assert_allclose([c.r, c.g, c.b], face_colors[i], atol=1e-6)

    def test_per_vertex_colors_are_averaged(self, basic_context):
        vertices, faces, _ = _strip_mesh(3)
        vertex_colors = np.linspace(0, 1, 15).reshape(5, 3)
        uuids = basic_context.addTrianglesFromArrays(vertices, faces, vertex_colors)
        for i, u in enumerate(uuids):
            c = basic_context.getPrimitiveColor(u)
            np.testing.assert_allclose([c.r, c.g, c.b], vertex_colors[faces[i]].mean(axis=0), atol=1e-6)
