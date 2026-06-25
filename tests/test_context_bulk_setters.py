"""Tests for per-element bulk setters added to Context.

Covers:
- Per-element setPrimitiveData<T> (distinct value per UUID) for all type categories.
- Per-element setObjectData<T> (distinct value per ObjID).
- Bulk overridePrimitiveTextureColor / usePrimitiveTextureColor (list of UUIDs).
- incrementPrimitiveData for uint and double fields via the data_type argument.

These exercise the C interface functions set<Scope>Data<T>Array,
overridePrimitiveTextureColorBatch / usePrimitiveTextureColorBatch, and
incrementPrimitiveDataUInt / incrementPrimitiveDataDouble.
"""

import pytest
import numpy as np

from pyhelios import DataTypes
from pyhelios.types import *  # vec2, vec3, vec4, int2, int3, int4


@pytest.mark.native_only
class TestPerElementPrimitiveData:
    """setPrimitiveData with a distinct value per primitive."""

    def _patches(self, ctx, n):
        return [ctx.addPatch(center=vec3(i, 0, 0)) for i in range(n)]

    def test_perelement_int(self, basic_context):
        uuids = self._patches(basic_context, 4)
        values = [10, 20, 30, 40]
        basic_context.setPrimitiveDataInt(uuids, "idx", values)
        for uuid, v in zip(uuids, values):
            assert basic_context.getPrimitiveData(uuid, "idx", int) == v

    def test_perelement_uint(self, basic_context):
        uuids = self._patches(basic_context, 3)
        values = [1, 2, 3]
        basic_context.setPrimitiveDataUInt(uuids, "u", values)
        for uuid, v in zip(uuids, values):
            assert basic_context.getPrimitiveData(uuid, "u", "uint") == v

    def test_perelement_float(self, basic_context):
        uuids = self._patches(basic_context, 5)
        values = [1.5, 2.5, 3.5, 4.5, 5.5]
        basic_context.setPrimitiveDataFloat(uuids, "temp", values)
        result = basic_context.getPrimitiveDataArray(uuids, "temp")
        np.testing.assert_array_almost_equal(result, values, decimal=4)

    def test_perelement_float_numpy(self, basic_context):
        uuids = self._patches(basic_context, 4)
        values = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
        basic_context.setPrimitiveDataFloat(uuids, "v", values)
        result = basic_context.getPrimitiveDataArray(uuids, "v")
        np.testing.assert_array_almost_equal(result, values, decimal=5)

    def test_perelement_double(self, basic_context):
        uuids = self._patches(basic_context, 3)
        values = [1.0 / 3.0, 2.0 / 3.0, 1.0 / 7.0]
        basic_context.setPrimitiveDataDouble(uuids, "d", values)
        for uuid, v in zip(uuids, values):
            assert basic_context.getPrimitiveData(uuid, "d", "double") == pytest.approx(v)

    def test_perelement_string(self, basic_context):
        uuids = self._patches(basic_context, 3)
        values = ["leaf", "branch", "trunk"]
        basic_context.setPrimitiveDataString(uuids, "part", values)
        for uuid, v in zip(uuids, values):
            assert basic_context.getPrimitiveData(uuid, "part", str) == v

    def test_perelement_vec3_objects(self, basic_context):
        uuids = self._patches(basic_context, 3)
        values = [vec3(1, 2, 3), vec3(4, 5, 6), vec3(7, 8, 9)]
        basic_context.setPrimitiveDataVec3(uuids, "wind", values)
        for uuid, v in zip(uuids, values):
            result = basic_context.getPrimitiveData(uuid, "wind")
            assert result[0] == pytest.approx(v.x)
            assert result[1] == pytest.approx(v.y)
            assert result[2] == pytest.approx(v.z)

    def test_perelement_vec2_sequences(self, basic_context):
        uuids = self._patches(basic_context, 2)
        values = [[1.0, 2.0], [3.0, 4.0]]
        basic_context.setPrimitiveDataVec2(uuids, "uv", values)
        for uuid, v in zip(uuids, values):
            result = basic_context.getPrimitiveData(uuid, "uv")
            assert result[0] == pytest.approx(v[0])
            assert result[1] == pytest.approx(v[1])

    def test_perelement_int2_objects(self, basic_context):
        uuids = self._patches(basic_context, 3)
        values = [int2(1, 2), int2(3, 4), int2(5, 6)]
        basic_context.setPrimitiveDataInt2(uuids, "ij", values)
        for uuid, v in zip(uuids, values):
            result = basic_context.getPrimitiveData(uuid, "ij")
            assert result[0] == v.x
            assert result[1] == v.y

    def test_length_mismatch_raises(self, basic_context):
        uuids = self._patches(basic_context, 3)
        with pytest.raises(ValueError, match="match"):
            basic_context.setPrimitiveDataFloat(uuids, "v", [1.0, 2.0])

    def test_scalar_still_broadcasts(self, basic_context):
        """A scalar value on a UUID list still broadcasts (backward compatible)."""
        uuids = self._patches(basic_context, 4)
        basic_context.setPrimitiveDataFloat(uuids, "same", 7.0)
        result = basic_context.getPrimitiveDataArray(uuids, "same")
        np.testing.assert_array_almost_equal(result, [7.0] * 4, decimal=4)


@pytest.mark.native_only
class TestPerElementObjectData:
    """setObjectData with a distinct value per object."""

    def _boxes(self, ctx, n):
        return [ctx.addBoxObject(center=DataTypes.vec3(i * 3, 0, 0),
                                 size=DataTypes.vec3(1, 1, 1),
                                 subdiv=DataTypes.int3(1, 1, 1)) for i in range(n)]

    def test_perelement_object_float(self, basic_context):
        obj_ids = self._boxes(basic_context, 3)
        values = [10.0, 20.0, 30.0]
        basic_context.setObjectDataFloat(obj_ids, "score", values)
        for oid, v in zip(obj_ids, values):
            assert basic_context.getObjectDataFloat(oid, "score") == pytest.approx(v)

    def test_perelement_object_int(self, basic_context):
        obj_ids = self._boxes(basic_context, 3)
        values = [1, 2, 3]
        basic_context.setObjectDataInt(obj_ids, "rank", values)
        for oid, v in zip(obj_ids, values):
            assert basic_context.getObjectDataInt(oid, "rank") == v

    def test_perelement_object_string(self, basic_context):
        obj_ids = self._boxes(basic_context, 3)
        values = ["a", "b", "c"]
        basic_context.setObjectDataString(obj_ids, "tag", values)
        for oid, v in zip(obj_ids, values):
            assert basic_context.getObjectDataString(oid, "tag") == v

    def test_object_scalar_still_broadcasts(self, basic_context):
        obj_ids = self._boxes(basic_context, 3)
        basic_context.setObjectDataFloat(obj_ids, "shared", 5.0)
        for oid in obj_ids:
            assert basic_context.getObjectDataFloat(oid, "shared") == pytest.approx(5.0)


@pytest.mark.native_only
class TestBulkTextureColorOverride:
    """Bulk override / use texture color for many primitives at once."""

    def _patches(self, ctx, n):
        return [ctx.addPatch(center=vec3(i, 0, 0)) for i in range(n)]

    def test_override_batch(self, basic_context):
        uuids = self._patches(basic_context, 5)
        basic_context.overridePrimitiveTextureColor(uuids)
        for uuid in uuids:
            assert basic_context.isPrimitiveTextureColorOverridden(uuid) is True

    def test_use_batch_restores(self, basic_context):
        uuids = self._patches(basic_context, 5)
        basic_context.overridePrimitiveTextureColor(uuids)
        basic_context.usePrimitiveTextureColor(uuids)
        for uuid in uuids:
            assert basic_context.isPrimitiveTextureColorOverridden(uuid) is False

    def test_single_uuid_still_works(self, basic_context):
        uuid = basic_context.addPatch()
        basic_context.overridePrimitiveTextureColor(uuid)
        assert basic_context.isPrimitiveTextureColorOverridden(uuid) is True


@pytest.mark.native_only
class TestIncrementUIntDouble:
    """incrementPrimitiveData targeting uint and double fields."""

    def _patches(self, ctx, n):
        return [ctx.addPatch(center=vec3(i, 0, 0)) for i in range(n)]

    def test_increment_uint(self, basic_context):
        uuids = self._patches(basic_context, 3)
        basic_context.setPrimitiveDataUInt(uuids, "count", 10)
        basic_context.incrementPrimitiveData(uuids, "count", 5, data_type="uint")
        for uuid in uuids:
            assert basic_context.getPrimitiveData(uuid, "count", "uint") == 15

    def test_increment_double(self, basic_context):
        uuids = self._patches(basic_context, 3)
        basic_context.setPrimitiveDataDouble(uuids, "precise", 1.0)
        basic_context.incrementPrimitiveData(uuids, "precise", 0.5, data_type="double")
        for uuid in uuids:
            assert basic_context.getPrimitiveData(uuid, "precise", "double") == pytest.approx(1.5)

    def test_increment_invalid_data_type(self, basic_context):
        uuids = self._patches(basic_context, 1)
        basic_context.setPrimitiveDataInt(uuids, "x", 1)
        with pytest.raises(ValueError, match="Unsupported data_type"):
            basic_context.incrementPrimitiveData(uuids, "x", 1, data_type="bogus")
