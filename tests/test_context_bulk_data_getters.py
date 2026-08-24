"""Tests for bulk primitive/object data getters.

Before these existed, Context.getPrimitiveDataArray() took a single native call
only for float; every other type looped in Python, costing one ctypes crossing
per primitive plus a second N-call existence sweep. Every type now reads in one
native call -- the fixed-width types through the PERELEM_GET_* macros, strings
through the offset-array form. These pin both the correctness of the bulk paths
and the fact that they are actually taken.
"""

import inspect

import numpy as np
import pytest

from pyhelios import Context
from pyhelios.types import vec2, vec3, vec4, int2, int3, int4
from pyhelios.wrappers import UContextWrapper as context_wrapper


@pytest.mark.native_only
class TestBulkPrimitiveDataGetters:
    """Bulk reads must agree with the per-element path for every data type."""

    @pytest.fixture
    def ctx_with_patches(self):
        with Context() as ctx:
            for i in range(12):
                ctx.addPatch(center=vec3(0, 0, i), size=vec2(1, 1))
            yield ctx, ctx.getAllUUIDs()

    def test_scalar_types_match_elementwise(self, ctx_with_patches):
        ctx, uuids = ctx_with_patches
        cases = [
            ("bulk_int", [i - 5 for i in range(len(uuids))], int, np.int32,
             ctx.setPrimitiveDataInt),
            ("bulk_uint", [i + 1 for i in range(len(uuids))], "uint", np.uint32,
             ctx.setPrimitiveDataUInt),
            ("bulk_double", [i * 0.25 for i in range(len(uuids))], "double",
             np.float64, ctx.setPrimitiveDataDouble),
        ]
        for label, values, typ, dtype, setter in cases:
            for uuid, value in zip(uuids, values):
                setter(uuid, label, value)

            bulk = ctx.getPrimitiveDataArray(uuids, label)
            elementwise = np.asarray(
                [ctx.getPrimitiveData(u, label, typ) for u in uuids], dtype=dtype
            )

            assert bulk.dtype == dtype, f"{label}: got {bulk.dtype}"
            assert bulk.shape == (len(uuids),)
            assert np.array_equal(bulk, elementwise), f"{label} diverged"

    def test_vector_types_match_elementwise(self, ctx_with_patches):
        ctx, uuids = ctx_with_patches
        cases = [
            ("bulk_vec2", lambda i: vec2(i, i + 0.5), 2, np.float32,
             ctx.setPrimitiveDataVec2),
            ("bulk_vec3", lambda i: vec3(i, i + 0.5, i + 1.5), 3, np.float32,
             ctx.setPrimitiveDataVec3),
            ("bulk_vec4", lambda i: vec4(i, i + 0.5, i + 1.5, i + 2.5), 4,
             np.float32, ctx.setPrimitiveDataVec4),
            ("bulk_int2", lambda i: int2(i, i + 1), 2, np.int32,
             ctx.setPrimitiveDataInt2),
            ("bulk_int3", lambda i: int3(i, i + 1, i + 2), 3, np.int32,
             ctx.setPrimitiveDataInt3),
            ("bulk_int4", lambda i: int4(i, i + 1, i + 2, i + 3), 4, np.int32,
             ctx.setPrimitiveDataInt4),
        ]
        for label, make, components, dtype, setter in cases:
            for i, uuid in enumerate(uuids):
                setter(uuid, label, make(i))

            bulk = ctx.getPrimitiveDataArray(uuids, label)
            assert bulk.shape == (len(uuids), components), f"{label}: {bulk.shape}"
            assert bulk.dtype == dtype, f"{label}: got {bulk.dtype}"

            for i, uuid in enumerate(uuids):
                expected = make(i)
                fields = [getattr(expected, axis)
                          for axis in ("x", "y", "z", "w")[:components]]
                assert np.allclose(bulk[i], fields), f"{label} row {i} diverged"

    def test_float_path_still_works(self, ctx_with_patches):
        """The pre-existing float bulk reader must be unaffected."""
        ctx, uuids = ctx_with_patches
        for i, uuid in enumerate(uuids):
            ctx.setPrimitiveDataFloat(uuid, "bulk_float", i * 1.5)

        bulk = ctx.getPrimitiveDataArray(uuids, "bulk_float")
        assert bulk.dtype == np.float32
        assert np.allclose(bulk, [i * 1.5 for i in range(len(uuids))])

    def test_uuid_order_is_preserved(self, ctx_with_patches):
        """Values must come back aligned to the UUID order given, not sorted."""
        ctx, uuids = ctx_with_patches
        for i, uuid in enumerate(uuids):
            ctx.setPrimitiveDataInt(uuid, "ordered", i)

        reversed_uuids = list(reversed(uuids))
        bulk = ctx.getPrimitiveDataArray(reversed_uuids, "ordered")
        assert np.array_equal(bulk, np.arange(len(uuids) - 1, -1, -1))

    def test_missing_label_names_the_failing_primitive(self, ctx_with_patches):
        """Fail-fast policy: the error must identify which primitive failed."""
        ctx, uuids = ctx_with_patches
        with pytest.raises(Exception) as exc:
            ctx.getPrimitiveDataArray(uuids, "no_such_label_here")
        assert "no_such_label_here" in str(exc.value)

    def test_buffer_is_copied_not_aliased(self, ctx_with_patches):
        """Successive reads must not alias the shared thread_local buffer."""
        ctx, uuids = ctx_with_patches
        for i, uuid in enumerate(uuids):
            ctx.setPrimitiveDataInt(uuid, "first", i)
            ctx.setPrimitiveDataInt(uuid, "second", i * 100)

        a = ctx.getPrimitiveDataArray(uuids, "first")
        b = ctx.getPrimitiveDataArray(uuids, "second")
        assert np.array_equal(a, np.arange(len(uuids), dtype=a.dtype)), (
            "first read was overwritten by the second; the native buffer is "
            "reused per call and must be copied"
        )
        assert not np.array_equal(a, b)


@pytest.mark.native_only
class TestBulkObjectDataGetters:
    """Object data had no bulk reader at any type."""

    def test_object_scalar_and_vector_reads(self):
        with Context() as ctx:
            objids = [
                ctx.addSphereObject(radius=0.5, center=vec3(0, 0, i), ndivs=4)
                for i in range(6)
            ]
            for i, oid in enumerate(objids):
                ctx.setObjectDataFloat(oid, "obj_float", i * 2.0)
                ctx.setObjectDataVec3(oid, "obj_vec3", vec3(i, i + 1, i + 2))

            floats = context_wrapper.getObjectDataArrayBulk(
                ctx.getNativePtr(), objids, "obj_float", 2)
            assert floats.shape == (len(objids),)
            assert np.allclose(floats, [i * 2.0 for i in range(len(objids))])

            vecs = context_wrapper.getObjectDataArrayBulk(
                ctx.getNativePtr(), objids, "obj_vec3", 5)
            assert vecs.shape == (len(objids), 3)
            for i in range(len(objids)):
                assert np.allclose(vecs[i], [i, i + 1, i + 2])


@pytest.mark.cross_platform
class TestBulkPathIsTaken:
    """Pin the mechanism: the non-float branches must not loop per UUID."""

    def test_no_per_uuid_loop_for_bulk_types(self):
        source = inspect.getsource(Context.getPrimitiveDataArray)
        # String (type 10) legitimately still loops -- it has no bulk getter.
        head, _, tail = source.partition("HELIOS_TYPE_STRING")
        assert "for i, uuid in enumerate(uuids)" not in head, (
            "getPrimitiveDataArray still reads one primitive at a time for a "
            "type that now has a bulk getter; route it through "
            "getPrimitiveDataArrayBulk."
        )

    def test_existence_presweep_only_on_error_path(self):
        """The 2N-crossing pre-sweep must not run before a successful read.

        It is still used inside `except HeliosError` handlers to turn a native
        failure into a message naming the offending primitive, which is the
        fail-fast contract. What must not survive is an unconditional sweep
        before the bulk call.
        """
        import textwrap
        source = textwrap.dedent(inspect.getsource(Context.getPrimitiveDataArray))
        lines = source.splitlines()
        sweep_lines = [i for i, ln in enumerate(lines)
                       if "_check_primitive_data_exists(uuids, label)" in ln
                       and "def " not in ln]
        assert sweep_lines, "expected the sweep to remain on the error path"
        for i in sweep_lines:
            preceding = "\n".join(lines[max(0, i - 6):i])
            assert "except HeliosError" in preceding, (
                f"line {i+1} calls the existence sweep outside an error handler; "
                "it must not run before a successful bulk read"
            )


@pytest.mark.native_only
class TestObjectDataArrayPublicAPI:
    """The object bulk getters must be reachable from Context, not just the wrapper.

    The native getters and ctypes plumbing shipped without any public method
    routing to them, so no user-facing call could benefit from them.
    """

    def test_context_exposes_getObjectDataArray(self):
        assert hasattr(Context, "getObjectDataArray"), (
            "bulk object-data getters exist natively but no Context method "
            "reaches them, so nothing in the public API benefits from them"
        )

    def test_object_data_array_matches_elementwise(self):
        with Context() as ctx:
            objids = [
                ctx.addSphereObject(radius=0.5, center=vec3(0, 0, i), ndivs=4)
                for i in range(6)
            ]
            for i, oid in enumerate(objids):
                ctx.setObjectDataFloat(oid, "of", i * 2.0)
                ctx.setObjectDataInt(oid, "oi", i - 3)
                ctx.setObjectDataVec3(oid, "ov", vec3(i, i + 1, i + 2))

            floats = ctx.getObjectDataArray(objids, "of")
            assert floats.shape == (len(objids),)
            assert np.allclose(floats, [i * 2.0 for i in range(len(objids))])

            ints = ctx.getObjectDataArray(objids, "oi")
            assert np.array_equal(
                ints, np.asarray([i - 3 for i in range(len(objids))], dtype=ints.dtype))

            vecs = ctx.getObjectDataArray(objids, "ov")
            assert vecs.shape == (len(objids), 3)
            for i in range(len(objids)):
                assert np.allclose(vecs[i], [i, i + 1, i + 2])

    def test_object_data_array_preserves_order(self):
        with Context() as ctx:
            objids = [
                ctx.addSphereObject(radius=0.5, center=vec3(0, 0, i), ndivs=4)
                for i in range(5)
            ]
            for i, oid in enumerate(objids):
                ctx.setObjectDataInt(oid, "seq", i)
            reversed_ids = list(reversed(objids))
            got = ctx.getObjectDataArray(reversed_ids, "seq")
            assert np.array_equal(got, np.arange(len(objids) - 1, -1, -1))

    def test_object_data_array_missing_label_raises(self):
        with Context() as ctx:
            objids = [ctx.addSphereObject(radius=0.5, center=vec3(0, 0, 0), ndivs=4)]
            with pytest.raises(Exception) as exc:
                ctx.getObjectDataArray(objids, "absent_obj_label")
            assert "absent_obj_label" in str(exc.value)


@pytest.mark.native_only
class TestVectorDataRoundTrip:
    """Reading vec/int data and writing it back must work.

    getPrimitiveDataArray returns an (N, components) ndarray for the vec/int
    types, so read-modify-write is the natural idiom. The per-element setter
    rejected ndarray rows, which broke that round trip for exactly the types
    the bulk getters added -- while the scalar path kept working.
    """

    @pytest.fixture
    def ctx(self):
        with Context() as c:
            for i in range(8):
                c.addPatch(center=vec3(0, 0, i), size=vec2(1, 1))
            yield c, c.getAllUUIDs()

    def test_vec3_round_trip_persists_modified_values(self, ctx):
        c, uuids = ctx
        c.setPrimitiveDataVec3(uuids, "n", vec3(1.0, 2.0, 3.0))

        arr = c.getPrimitiveDataArray(uuids, "n")
        arr[:, 2] *= -1.0
        c.setPrimitiveDataVec3(uuids, "n", arr)

        # Assert the MODIFIED values came back, not merely that no error raised:
        # a test that only checks for no exception passes for the wrong reason.
        back = c.getPrimitiveDataArray(uuids, "n")
        assert np.allclose(back[:, 0], 1.0)
        assert np.allclose(back[:, 1], 2.0)
        assert np.allclose(back[:, 2], -3.0), f"z not written back: {back[:, 2]}"

    def test_int3_round_trip_persists_modified_values(self, ctx):
        c, uuids = ctx
        c.setPrimitiveDataInt3(uuids, "i3", int3(4, 5, 6))

        arr = c.getPrimitiveDataArray(uuids, "i3")
        arr[:, 0] += 10
        c.setPrimitiveDataInt3(uuids, "i3", arr)

        back = c.getPrimitiveDataArray(uuids, "i3")
        assert np.array_equal(back[:, 0], np.full(len(uuids), 14))
        assert np.array_equal(back[:, 1], np.full(len(uuids), 5))
        assert np.array_equal(back[:, 2], np.full(len(uuids), 6))

    def test_existing_sequence_inputs_still_accepted(self, ctx):
        """Lists, tuples and vecN objects must keep working unchanged."""
        c, uuids = ctx
        c.setPrimitiveDataVec3(uuids, "mixed", [vec3(1, 1, 1)] * len(uuids))
        assert np.allclose(c.getPrimitiveDataArray(uuids, "mixed"), 1.0)

        c.setPrimitiveDataVec3(uuids, "mixed", [(2.0, 2.0, 2.0)] * len(uuids))
        assert np.allclose(c.getPrimitiveDataArray(uuids, "mixed"), 2.0)

        c.setPrimitiveDataVec3(uuids, "mixed", [[3.0, 3.0, 3.0]] * len(uuids))
        assert np.allclose(c.getPrimitiveDataArray(uuids, "mixed"), 3.0)

    def test_wrong_component_count_still_rejected(self, ctx):
        """An ndarray with the wrong width must still raise, not silently pad."""
        c, uuids = ctx
        bad = np.ones((len(uuids), 2), dtype=np.float32)
        with pytest.raises((ValueError, TypeError)):
            c.setPrimitiveDataVec3(uuids, "bad", bad)


@pytest.mark.native_only
class TestBulkStringDataGetter:
    """String data must read in one native call, like every other type.

    String was the last type without a bulk getter: it needs the offset-array
    pattern because entries are variable length, so it kept a per-UUID loop plus
    the 2N existence pre-sweep the other types dropped.
    """

    @pytest.fixture
    def ctx(self):
        with Context() as c:
            for i in range(10):
                c.addPatch(center=vec3(0, 0, i), size=vec2(1, 1))
            yield c, c.getAllUUIDs()

    def test_string_values_match_elementwise(self, ctx):
        c, uuids = ctx
        for i, u in enumerate(uuids):
            c.setPrimitiveDataString(u, "sp", f"species_{i}")

        bulk = c.getPrimitiveDataArray(uuids, "sp")
        elementwise = [c.getPrimitiveData(u, "sp", str) for u in uuids]
        assert list(bulk) == elementwise
        assert list(bulk) == [f"species_{i}" for i in range(len(uuids))]

    def test_variable_length_and_empty_strings(self, ctx):
        """Offsets must handle differing lengths, including empty entries."""
        c, uuids = ctx
        values = ["", "a", "medium", "a" * 200, "", "xy", "z" * 50,
                  "tail", "", "last"]
        for u, v in zip(uuids, values):
            c.setPrimitiveDataString(u, "var", v)

        bulk = c.getPrimitiveDataArray(uuids, "var")
        assert list(bulk) == values, f"got {list(bulk)}"

    def test_non_ascii_strings_round_trip(self, ctx):
        """UTF-8 must survive the byte-offset splitting."""
        c, uuids = ctx
        values = [f"leaf_éè_{i}" for i in range(len(uuids))]
        for u, v in zip(uuids, values):
            c.setPrimitiveDataString(u, "utf", v)
        bulk = c.getPrimitiveDataArray(uuids, "utf")
        assert list(bulk) == values

    def test_string_order_is_preserved(self, ctx):
        c, uuids = ctx
        for i, u in enumerate(uuids):
            c.setPrimitiveDataString(u, "ord", str(i))
        rev = list(reversed(uuids))
        bulk = c.getPrimitiveDataArray(rev, "ord")
        assert list(bulk) == [str(i) for i in range(len(uuids) - 1, -1, -1)]

    def test_missing_string_label_raises(self, ctx):
        c, uuids = ctx
        with pytest.raises(Exception) as exc:
            c.getPrimitiveDataArray(uuids, "no_such_string_label")
        assert "no_such_string_label" in str(exc.value)

    def test_string_uses_one_native_call(self):
        """Mechanism: the string branch must not loop per UUID any more."""
        source = inspect.getsource(Context.getPrimitiveDataArray)
        _, _, tail = source.partition("HELIOS_TYPE_STRING")
        assert "for i, uuid in enumerate(uuids)" not in tail, (
            "the string branch still reads one primitive at a time; route it "
            "through the bulk string getter"
        )
