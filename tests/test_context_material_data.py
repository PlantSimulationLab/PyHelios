"""Tests for the PyHelios material-data API.

Covers the per-type set/get methods, the unified setMaterialData/getMaterialData
dispatch, getMaterialDataType, and getUniquePrimitive/ObjectDataValues.
"""

import pytest
from pyhelios import Context
from pyhelios.exceptions import HeliosRuntimeError
from pyhelios.types import vec2, vec3, vec4, int2, int3, int4


@pytest.fixture
def basic_context(check_native_library):
    """Fresh native Context per test."""
    ctx = Context()
    yield ctx
    ctx.__exit__(None, None, None)


@pytest.fixture
def material_label():
    return "pr3_test_material"


@pytest.fixture
def material_ctx(basic_context, material_label):
    """Context with a single test material registered."""
    basic_context.addMaterial(material_label)
    return basic_context


# =============================================================================
# Per-type setMaterialData / getMaterialData round-trips
# =============================================================================

@pytest.mark.native_only
class TestMaterialDataPerTypeRoundTrip:
    def test_int(self, material_ctx, material_label):
        material_ctx.setMaterialDataInt(material_label, "k", 42)
        assert material_ctx.getMaterialDataInt(material_label, "k") == 42

    def test_uint(self, material_ctx, material_label):
        material_ctx.setMaterialDataUInt(material_label, "k", 4_000_000_000)
        assert material_ctx.getMaterialDataUInt(material_label, "k") == 4_000_000_000

    def test_float(self, material_ctx, material_label):
        material_ctx.setMaterialDataFloat(material_label, "k", 3.14)
        assert material_ctx.getMaterialDataFloat(material_label, "k") == pytest.approx(3.14, rel=1e-5)

    def test_double(self, material_ctx, material_label):
        material_ctx.setMaterialDataDouble(material_label, "k", 2.718281828)
        assert material_ctx.getMaterialDataDouble(material_label, "k") == pytest.approx(2.718281828, rel=1e-12)

    def test_string(self, material_ctx, material_label):
        material_ctx.setMaterialDataString(material_label, "k", "hello world")
        assert material_ctx.getMaterialDataString(material_label, "k") == "hello world"

    def test_string_long(self, material_ctx, material_label):
        # Cross the 256-byte initial buffer boundary in _read_string_buffer.
        long_value = "x" * 1000
        material_ctx.setMaterialDataString(material_label, "k", long_value)
        assert material_ctx.getMaterialDataString(material_label, "k") == long_value

    def test_vec2(self, material_ctx, material_label):
        material_ctx.setMaterialDataVec2(material_label, "k", vec2(1.5, -2.5))
        v = material_ctx.getMaterialDataVec2(material_label, "k")
        assert isinstance(v, vec2)
        assert v.x == pytest.approx(1.5)
        assert v.y == pytest.approx(-2.5)

    def test_vec3(self, material_ctx, material_label):
        material_ctx.setMaterialDataVec3(material_label, "k", vec3(1, 2, 3))
        v = material_ctx.getMaterialDataVec3(material_label, "k")
        assert isinstance(v, vec3)
        assert v.x == pytest.approx(1.0)
        assert v.y == pytest.approx(2.0)
        assert v.z == pytest.approx(3.0)

    def test_vec4(self, material_ctx, material_label):
        material_ctx.setMaterialDataVec4(material_label, "k", vec4(0.1, 0.2, 0.3, 0.4))
        v = material_ctx.getMaterialDataVec4(material_label, "k")
        assert isinstance(v, vec4)
        assert (v.x, v.y, v.z, v.w) == pytest.approx((0.1, 0.2, 0.3, 0.4))

    def test_int2(self, material_ctx, material_label):
        material_ctx.setMaterialDataInt2(material_label, "k", int2(7, -8))
        v = material_ctx.getMaterialDataInt2(material_label, "k")
        assert isinstance(v, int2)
        assert v.x == 7
        assert v.y == -8

    def test_int3(self, material_ctx, material_label):
        material_ctx.setMaterialDataInt3(material_label, "k", int3(1, 2, 3))
        v = material_ctx.getMaterialDataInt3(material_label, "k")
        assert (v.x, v.y, v.z) == (1, 2, 3)

    def test_int4(self, material_ctx, material_label):
        material_ctx.setMaterialDataInt4(material_label, "k", int4(1, 2, 3, 4))
        v = material_ctx.getMaterialDataInt4(material_label, "k")
        assert (v.x, v.y, v.z, v.w) == (1, 2, 3, 4)


# =============================================================================
# Unified setMaterialData / getMaterialData dispatch
# =============================================================================

@pytest.mark.native_only
class TestMaterialDataUnifiedDispatch:
    def test_int_via_unified(self, material_ctx, material_label):
        material_ctx.setMaterialData(material_label, "k", 42)
        assert material_ctx.getMaterialData(material_label, "k") == 42

    def test_float_via_unified(self, material_ctx, material_label):
        material_ctx.setMaterialData(material_label, "k", 3.14)
        assert material_ctx.getMaterialData(material_label, "k") == pytest.approx(3.14, rel=1e-5)

    def test_string_via_unified(self, material_ctx, material_label):
        material_ctx.setMaterialData(material_label, "k", "auto")
        assert material_ctx.getMaterialData(material_label, "k") == "auto"

    def test_vec3_via_unified(self, material_ctx, material_label):
        material_ctx.setMaterialData(material_label, "k", vec3(1, 2, 3))
        v = material_ctx.getMaterialData(material_label, "k")
        assert isinstance(v, vec3)
        assert (v.x, v.y, v.z) == pytest.approx((1, 2, 3))

    def test_int4_via_unified(self, material_ctx, material_label):
        material_ctx.setMaterialData(material_label, "k", int4(1, 2, 3, 4))
        v = material_ctx.getMaterialData(material_label, "k")
        assert isinstance(v, int4)
        assert (v.x, v.y, v.z, v.w) == (1, 2, 3, 4)

    def test_explicit_type_arg(self, material_ctx, material_label):
        material_ctx.setMaterialDataFloat(material_label, "k", 1.5)
        assert material_ctx.getMaterialData(material_label, "k", float) == pytest.approx(1.5)

    def test_explicit_uint_dtype(self, material_ctx, material_label):
        material_ctx.setMaterialDataUInt(material_label, "k", 100)
        assert material_ctx.getMaterialData(material_label, "k", "uint") == 100

    def test_explicit_double_dtype(self, material_ctx, material_label):
        material_ctx.setMaterialDataDouble(material_label, "k", 1.234567890123)
        v = material_ctx.getMaterialData(material_label, "k", "double")
        assert v == pytest.approx(1.234567890123, rel=1e-12)

    def test_unsupported_value_raises(self, material_ctx, material_label):
        with pytest.raises(ValueError, match="Unsupported value type"):
            material_ctx.setMaterialData(material_label, "k", [1, 2, 3])

    def test_unsupported_dtype_raises(self, material_ctx, material_label):
        material_ctx.setMaterialDataFloat(material_label, "k", 1.0)
        with pytest.raises(ValueError, match="Unsupported material data type"):
            material_ctx.getMaterialData(material_label, "k", complex)


# =============================================================================
# getMaterialDataType + doesMaterialDataExist
# =============================================================================

@pytest.mark.native_only
class TestMaterialDataType:
    def test_type_codes_match_helios_enum(self, material_ctx, material_label):
        # 0=INT, 1=UINT, 2=FLOAT, 3=DOUBLE, 4=VEC2, 5=VEC3, 6=VEC4, 7=INT2,
        # 8=INT3, 9=INT4, 10=STRING.
        cases = [
            ("setMaterialDataInt", 1, 0),
            ("setMaterialDataUInt", 1, 1),
            ("setMaterialDataFloat", 1.5, 2),
            ("setMaterialDataDouble", 1.5, 3),
            ("setMaterialDataString", "x", 10),
        ]
        for setter, value, expected_code in cases:
            label = f"k_{setter}"
            getattr(material_ctx, setter)(material_label, label, value)
            assert material_ctx.getMaterialDataType(material_label, label) == expected_code, \
                f"{setter} → expected type code {expected_code}"

    def test_vec_type_codes(self, material_ctx, material_label):
        material_ctx.setMaterialDataVec2(material_label, "v2", vec2(1, 2))
        material_ctx.setMaterialDataVec3(material_label, "v3", vec3(1, 2, 3))
        material_ctx.setMaterialDataVec4(material_label, "v4", vec4(1, 2, 3, 4))
        material_ctx.setMaterialDataInt2(material_label, "i2", int2(1, 2))
        material_ctx.setMaterialDataInt3(material_label, "i3", int3(1, 2, 3))
        material_ctx.setMaterialDataInt4(material_label, "i4", int4(1, 2, 3, 4))
        assert material_ctx.getMaterialDataType(material_label, "v2") == 4
        assert material_ctx.getMaterialDataType(material_label, "v3") == 5
        assert material_ctx.getMaterialDataType(material_label, "v4") == 6
        assert material_ctx.getMaterialDataType(material_label, "i2") == 7
        assert material_ctx.getMaterialDataType(material_label, "i3") == 8
        assert material_ctx.getMaterialDataType(material_label, "i4") == 9

    def test_does_material_data_exist(self, material_ctx, material_label):
        assert material_ctx.doesMaterialDataExist(material_label, "k") is False
        material_ctx.setMaterialDataFloat(material_label, "k", 1.0)
        assert material_ctx.doesMaterialDataExist(material_label, "k") is True

    def test_clear_material_data(self, material_ctx, material_label):
        material_ctx.setMaterialDataFloat(material_label, "k", 1.0)
        assert material_ctx.doesMaterialDataExist(material_label, "k") is True
        material_ctx.clearMaterialData(material_label, "k")
        assert material_ctx.doesMaterialDataExist(material_label, "k") is False


# =============================================================================
# Validation
# =============================================================================

@pytest.mark.native_only
class TestMaterialDataValidation:
    def test_setMaterialDataVec3_rejects_non_vec3(self, material_ctx, material_label):
        with pytest.raises(ValueError, match="value must be a vec3"):
            material_ctx.setMaterialDataVec3(material_label, "k", (1, 2, 3))

    def test_setMaterialDataInt2_rejects_non_int2(self, material_ctx, material_label):
        with pytest.raises(ValueError, match="value must be an int2"):
            material_ctx.setMaterialDataInt2(material_label, "k", (1, 2))

    def test_get_unknown_data_raises(self, material_ctx, material_label):
        with pytest.raises(HeliosRuntimeError):
            material_ctx.getMaterialDataFloat(material_label, "nonexistent_key")

    def test_get_unknown_material_raises(self, basic_context):
        with pytest.raises(HeliosRuntimeError):
            basic_context.getMaterialDataFloat("nonexistent_material", "k")


# =============================================================================
# Unique data values (require value caching enabled)
# =============================================================================

@pytest.mark.native_only
class TestUniquePrimitiveDataValues:
    def test_unique_int_values(self, basic_context):
        # Caching must be enabled BEFORE the data is written so the registry
        # is populated as values are set.
        basic_context.enablePrimitiveDataValueCaching("category")
        u1 = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        u2 = basic_context.addPatch(center=vec3(1, 0, 0), size=vec2(1, 1))
        u3 = basic_context.addPatch(center=vec3(2, 0, 0), size=vec2(1, 1))
        basic_context.setPrimitiveDataInt(u1, "category", 7)
        basic_context.setPrimitiveDataInt(u2, "category", 7)
        basic_context.setPrimitiveDataInt(u3, "category", 42)
        unique = basic_context.getUniquePrimitiveDataValues("category", int)
        assert sorted(unique) == [7, 42]

    def test_unique_string_values(self, basic_context):
        basic_context.enablePrimitiveDataValueCaching("species")
        uuids = [basic_context.addPatch(center=vec3(i, 0, 0), size=vec2(0.1, 0.1))
                 for i in range(4)]
        for u, sp in zip(uuids, ["oak", "pine", "oak", "maple"]):
            basic_context.setPrimitiveDataString(u, "species", sp)
        unique = basic_context.getUniquePrimitiveDataValues("species", str)
        assert sorted(unique) == ["maple", "oak", "pine"]

    def test_unique_uint_values(self, basic_context):
        basic_context.enablePrimitiveDataValueCaching("group_id")
        uuids = [basic_context.addPatch(center=vec3(i, 0, 0), size=vec2(0.1, 0.1))
                 for i in range(3)]
        for u, gid in zip(uuids, [10, 20, 10]):
            basic_context.setPrimitiveDataUInt(u, "group_id", gid)
        unique = basic_context.getUniquePrimitiveDataValues("group_id", "uint")
        assert sorted(unique) == [10, 20]

    def test_unique_without_caching_raises(self, basic_context):
        # No enablePrimitiveDataValueCaching call → C++ raises.
        u = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        basic_context.setPrimitiveDataInt(u, "uncached_label", 1)
        with pytest.raises(HeliosRuntimeError):
            basic_context.getUniquePrimitiveDataValues("uncached_label", int)

    def test_unsupported_dtype_raises(self, basic_context):
        with pytest.raises(ValueError, match="Unsupported dtype"):
            basic_context.getUniquePrimitiveDataValues("anything", float)


@pytest.mark.native_only
class TestUniqueObjectDataValues:
    def test_unique_int_values_on_objects(self, basic_context):
        basic_context.enableObjectDataValueCaching("class_id")
        from pyhelios.types import SphericalCoord
        ids = [basic_context.addTileObject(center=vec3(i, 0, 0), size=vec2(0.5, 0.5),
                                           rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
               for i in range(3)]
        basic_context.setObjectDataInt(ids[0], "class_id", 1)
        basic_context.setObjectDataInt(ids[1], "class_id", 2)
        basic_context.setObjectDataInt(ids[2], "class_id", 1)
        unique = basic_context.getUniqueObjectDataValues("class_id", int)
        assert sorted(unique) == [1, 2]

    def test_unsupported_dtype_raises(self, basic_context):
        with pytest.raises(ValueError, match="Unsupported dtype"):
            basic_context.getUniqueObjectDataValues("anything", float)
