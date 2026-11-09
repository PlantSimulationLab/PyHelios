"""
Tests for the helios-core 1.3.96 changes that reach the Python API.

Core: Context.getMaterialRevision / getModifiedUUIDs / replacePolymeshObjectPrimitives,
Global.classMapAreaFractions, and the pyhelios.collision closest-point queries.
Plug-ins: SolarPosition direct/diffuse flux getters, Visualizer camera up direction and
principal point, PlantHydraulics.getPrimitivesByPlantIDs, the C4 coefficient layout without
``absorptance``, the new photosynthesis and stomatal library entries, the LeafOptics drymass
default and unknown-species error, RadiationModel colour correction / tone curve camera
properties, applySpectralClassMaps, getCameraColorCorrectionMatrix and
getCameraPixelBrightnessTemperature, and the PlantArchitecture leaf roll, leaf shape,
fruit-branch collision avoidance, multi-plant elevation tracking, nitrogen pools, intercalary
leaflet scale and class-map ShootParameters fields.
"""

import math

import numpy as np
import pytest

from pyhelios import Context, Global, collision
from pyhelios.exceptions import HeliosError
from pyhelios.plugins.registry import get_plugin_registry
from pyhelios.types import RGBcolor, int2, vec2, vec3
from pyhelios.wrappers import UCollisionWrapper as collision_wrapper
from pyhelios.wrappers import UContextWrapper as context_wrapper
from pyhelios.wrappers import UGlobalWrapper as global_wrapper


def _available(plugin):
    return get_plugin_registry().is_plugin_available(plugin)


requires_ctx_1396 = pytest.mark.skipif(
    not context_wrapper._CONTEXT_1396_AVAILABLE,
    reason="Context 1.3.96 functions not in the native library (rebuild with build_scripts/build_helios --clean)")
requires_class_area_1396 = pytest.mark.skipif(
    not global_wrapper._CLASS_MAP_AREA_FUNCTIONS_AVAILABLE,
    reason="classMapAreaFractions not in the native library (requires helios-core v1.3.96)")
requires_collision_1396 = pytest.mark.skipif(
    not collision_wrapper._COLLISION_GEOMETRY_AVAILABLE,
    reason="collision queries not in the native library (requires helios-core v1.3.96 with plantarchitecture)")


# =========================================================================== #
# Pure-Python checks (mock mode safe)
# =========================================================================== #
@pytest.mark.cross_platform
class TestPurePythonDefaultsAndValidation:

    def test_leafoptics_drymass_default_matches_native(self):
        from pyhelios.LeafOptics import LeafOpticsProperties
        assert LeafOpticsProperties().drymass == pytest.approx(0.006)

    def test_camera_properties_new_fields_and_defaults(self):
        from pyhelios.RadiationModel import CameraProperties
        props = CameraProperties()
        assert props.exposure_target == pytest.approx(0.235)
        assert props.color_correction == "auto"
        assert props.tone_curve == "auto"
        off = CameraProperties(color_correction="off", tone_curve="off")
        assert (off.color_correction, off.tone_curve) == ("off", "off")
        with pytest.raises(ValueError, match="color_correction"):
            CameraProperties(color_correction="on")
        with pytest.raises(ValueError, match="tone_curve"):
            CameraProperties(tone_curve="sRGB")

    def test_camera_string_array_carries_new_fields_in_native_slots(self):
        from pyhelios.RadiationModel import CameraProperties
        from pyhelios.wrappers import URadiationModelWrapper as rw
        # Slots 7 and 8 must match CAMERA_STR_COLOR_CORRECTION / CAMERA_STR_TONE_CURVE in the C wrapper.
        assert rw._CAMERA_STRING_FIELDS[7] == "color_correction"
        assert rw._CAMERA_STRING_FIELDS[8] == "tone_curve"
        array, count = rw._build_camera_string_array(CameraProperties(color_correction="off", tone_curve="off"))
        assert count == 9
        assert array[7] == b"off" and array[8] == b"off"

    def test_c4_layout_is_42_and_legacy_43_is_rejected(self):
        from pyhelios.wrappers import UPhotosynthesisWrapper as pw
        assert pw.C4_COEFFICIENTS_COUNT == 42
        pw._check_c4_coefficient_count([0.0] * 42)
        with pytest.raises(ValueError, match="absorptance"):
            pw._check_c4_coefficient_count([0.0] * 43)
        with pytest.raises(ValueError, match="exactly 42"):
            pw._check_c4_coefficient_count([0.0] * 44)

    @pytest.mark.parametrize("name, expected", [
        ("Cowpea", "Cowpea"), ("cowpea", "Cowpea"), ("CommonBean", "CommonBean"),
        ("bean", "CommonBean"), ("common_bean", "CommonBean"),
    ])
    def test_new_farquhar_species_accepted(self, name, expected):
        from pyhelios.types.photosynthesis import validate_species_name
        assert validate_species_name(name) == expected

    def test_sorghum_listed_as_c4_species(self):
        from pyhelios.PhotosynthesisModel import AVAILABLE_C4_SPECIES
        assert "Sorghum_GEMINI2026" in AVAILABLE_C4_SPECIES

    def test_leaf_prototype_roll_and_class_map_round_trip(self):
        from pyhelios.plant_architecture_params import LeafPrototype, RandomParameterFloat
        proto = LeafPrototype(roll_fraction=RandomParameterFloat.constant(0.4),
                              leaf_class_map_file={0: "SorghumLeaf_classes.png"})
        d = proto.to_dict()
        assert d["roll_fraction"]["parameters"] == [pytest.approx(0.4)]
        assert d["leaf_class_map_file"] == {"0": "SorghumLeaf_classes.png"}
        back = LeafPrototype.from_dict(d)
        assert back.roll_fraction.parameters == [pytest.approx(0.4)]
        assert back.leaf_class_map_file == {0: "SorghumLeaf_classes.png"}
        assert LeafPrototype.from_dict({}).leaf_class_map_file == {}

    def test_internode_and_inflorescence_class_map_round_trip(self):
        from pyhelios.plant_architecture_params import InflorescenceParameters, InternodeParameters
        inode = InternodeParameters.from_dict(InternodeParameters(image_class_map_file="bark.png").to_dict())
        assert inode.image_class_map_file == "bark.png"
        infl = InflorescenceParameters.from_dict(InflorescenceParameters(fruit_class_map_file="fruit.png").to_dict())
        assert infl.fruit_class_map_file == "fruit.png"

    def test_leaf_shape_values_flat_round_trip(self):
        from pyhelios.plant_architecture_params import LeafShapeValues
        shape = LeafShapeValues(aspect_ratio=0.3, midrib_fold_fraction=0.1, longitudinal_curvature=-0.2,
                                longitudinal_curvature_exponent=3.0, lateral_curvature=0.05, petiole_roll=0.01,
                                wave_period=0.2, wave_amplitude=0.02, roll_fraction=0.5,
                                subdivisions_x=6, subdivisions_y=8, lattice_offset=(0.01, 0.0, -0.02))
        values, subdivisions = shape.to_flat()
        assert len(values) == 12 and subdivisions == [6, 8]
        back = LeafShapeValues.from_flat(values, subdivisions)
        assert back.roll_fraction == pytest.approx(0.5)
        assert back.lattice_offset == pytest.approx((0.01, 0.0, -0.02))
        assert back.subdivisions_y == 8

    def test_collision_rejects_non_vec3(self):
        with pytest.raises(ValueError, match="vec3"):
            collision.closestPointOnTriangle((0, 0, 0), vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0))
        with pytest.raises(ValueError, match="vec3"):
            collision.closestPointsOnSegments(vec3(0, 0, 0), vec3(1, 0, 0), RGBcolor(0, 0, 0), vec3(0, 1, 0))

    def test_class_map_area_fractions_argument_validation(self):
        classes = np.ones((3, 3), dtype=np.uint16)
        square = [vec2(0, 0), vec2(1, 0), vec2(1, 1), vec2(0, 1)]
        with pytest.raises(ValueError, match="int2"):
            Global.classMapAreaFractions(classes, (3, 3), square)
        with pytest.raises(ValueError, match="vec2"):
            Global.classMapAreaFractions(classes, int2(3, 3), [vec3(0, 0, 0)] * 3)
        with pytest.raises(ValueError, match="shape"):
            Global.classMapAreaFractions(classes, int2(4, 3), square)


# =========================================================================== #
# Core (native)
# =========================================================================== #
@pytest.mark.native_only
@requires_ctx_1396
class TestContext1396:

    def test_material_revision_advances_on_material_data(self):
        with Context() as context:
            context.addMaterial("leafmat")
            rev = context.getMaterialRevision()
            assert context.getMaterialRevision() == rev
            context.setMaterialDataFloat("leafmat", "specular_n", 1.5)
            assert context.getMaterialRevision() > rev

    def test_modified_uuids_give_each_caller_its_own_view(self):
        with Context() as context:
            a = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
            b = context.addPatch(center=vec3(2, 0, 0), size=vec2(1, 1))
            first, mark = context.getModifiedUUIDs()
            assert set(first) >= {a, b}
            none, mark = context.getModifiedUUIDs(mark)
            assert none == []
            context.setPrimitiveColor(b, RGBcolor(1, 0, 0))
            changed, mark2 = context.getModifiedUUIDs(mark)
            assert changed == [b]
            # A second caller starting fresh still sees everything; markGeometryClean does not reset marks.
            context.markGeometryClean()
            everything, _ = context.getModifiedUUIDs(0)
            assert set(everything) >= {a, b}
            nothing, _ = context.getModifiedUUIDs(mark2)
            assert nothing == []

    def test_modified_uuids_rejects_bad_mark(self):
        with Context() as context:
            with pytest.raises(ValueError, match="mark"):
                context.getModifiedUUIDs(-1)
            with pytest.raises(ValueError, match="mark"):
                context.getModifiedUUIDs(1.5)

    def test_replace_polymesh_primitives_keeps_object_and_copies_data(self):
        with Context() as context:
            t0 = context.addTriangle(vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0))
            t1 = context.addTriangle(vec3(1, 0, 0), vec3(1, 1, 0), vec3(0, 1, 0))
            obj = context.addPolymeshObject([t0, t1])
            context.setObjectDataFloat(obj, "nitrogen", 2.5)
            context.setPrimitiveDataFloat(t0, "tag", 7.0)

            new = context.addTriangle(vec3(0, 0, 0), vec3(0.5, 0, 0), vec3(0, 0.5, 0))
            context.replacePolymeshObjectPrimitives(obj, [t0], [new], [t0])

            assert context.doesObjectExist(obj)
            assert sorted(context.getObjectPrimitiveUUIDs(obj)) == sorted([t1, new])
            assert context.getObjectData(obj, "nitrogen") == pytest.approx(2.5)
            assert context.getPrimitiveData(new, "tag") == pytest.approx(7.0)
            assert not context.doesPrimitiveExist(t0)

    def test_replace_polymesh_primitives_validation(self):
        with Context() as context:
            with pytest.raises(ValueError, match="parallel"):
                context.replacePolymeshObjectPrimitives(0, [], [1, 2], [1])
            with pytest.raises(ValueError, match="old_UUIDs"):
                context.replacePolymeshObjectPrimitives(0, [-1], [], [])

    def test_replace_polymesh_primitives_native_error(self):
        with Context() as context:
            t0 = context.addTriangle(vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0))
            obj = context.addPolymeshObject([t0])
            with pytest.raises(HeliosError):
                # Removing the only member and adding nothing would leave the object empty.
                context.replacePolymeshObjectPrimitives(obj, [t0], [], [])


@pytest.mark.native_only
@requires_class_area_1396
class TestClassMapAreaFractions:

    def test_two_halves(self):
        classes = np.ones((3, 3), dtype=np.uint16)
        classes[:, 1:] = 2
        square = [vec2(0, 0), vec2(1, 0), vec2(1, 1), vec2(0, 1)]
        result = Global.classMapAreaFractions(classes, int2(3, 3), square)
        assert [c for c, _ in result] == [1, 2]
        assert [f for _, f in result] == pytest.approx([0.5, 0.5])

    def test_transparent_class_zero_left_out(self):
        classes = np.zeros((3, 3), dtype=np.uint16)
        square = [vec2(0, 0), vec2(1, 0), vec2(1, 1), vec2(0, 1)]
        assert Global.classMapAreaFractions(classes, int2(3, 3), square) == []

    def test_flat_classes_accepted(self):
        result = Global.classMapAreaFractions([3] * 4, int2(2, 2), [vec2(0, 0), vec2(1, 0), vec2(0, 1)])
        assert result == [(3, pytest.approx(1.0))]


@pytest.mark.native_only
@requires_collision_1396
class TestCollisionGeometry:

    def test_segments(self):
        d2, c1, c2 = collision.closestPointsOnSegments(vec3(0, 0, 0), vec3(1, 0, 0),
                                                       vec3(0.5, 1, 0), vec3(0.5, 2, 0))
        assert d2 == pytest.approx(1.0)
        assert (c1.x, c1.y, c1.z) == pytest.approx((0.5, 0, 0))
        assert (c2.x, c2.y, c2.z) == pytest.approx((0.5, 1, 0))

    def test_point_on_triangle(self):
        p = collision.closestPointOnTriangle(vec3(0.2, 0.2, 3), vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0))
        assert (p.x, p.y, p.z) == pytest.approx((0.2, 0.2, 0))
        corner = collision.closestPointOnTriangle(vec3(-1, -1, 0), vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0))
        assert (corner.x, corner.y, corner.z) == pytest.approx((0, 0, 0))

    def test_segment_triangle(self):
        # Crossing segment: zero distance, both points at the crossing.
        d2, s_pt, t_pt = collision.closestPointsSegmentTriangle(vec3(0.2, 0.2, -1), vec3(0.2, 0.2, 1),
                                                                vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0))
        assert d2 == pytest.approx(0.0, abs=1e-12)
        assert (t_pt.x, t_pt.y, t_pt.z) == pytest.approx((0.2, 0.2, 0))
        # Segment above the triangle.
        d2, s_pt, t_pt = collision.closestPointsSegmentTriangle(vec3(0.2, 0.2, 2), vec3(0.3, 0.2, 2),
                                                                vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0))
        assert d2 == pytest.approx(4.0)


# =========================================================================== #
# SolarPosition
# =========================================================================== #
@pytest.mark.native_only
class TestSolarPositionDirectDiffuse:

    def _solar(self, context):
        from pyhelios import SolarPosition
        from pyhelios.wrappers import USolarPositionWrapper as sw
        if not _available("solarposition"):
            pytest.skip("solarposition plugin not available")
        if not sw._DIRECT_DIFFUSE_FLUX_AVAILABLE:
            pytest.skip("direct/diffuse flux getters not in the native library (requires helios-core v1.3.96)")
        context.setDate(2023, 6, 21)
        context.setTime(12, 0)  # (hour, minute)
        solar = SolarPosition(context, 8, 38.55, 121.76)
        solar.setAtmosphericConditions(101325, 300, 0.5, 0.05)
        return solar

    def test_components_are_consistent_with_global_flux(self):
        with Context() as context:
            solar = self._solar(context)
            cosz = math.cos(solar.getSunZenith())
            direct, diffuse = solar.getDirectSolarFlux(), solar.getDiffuseSolarFlux()
            assert direct > 0 and diffuse > 0
            # Global horizontal = direct (normal to sun) * cos(zenith) + diffuse (horizontal).
            assert direct * cosz + diffuse == pytest.approx(solar.getSolarFlux() * cosz, rel=1e-3)
            f = solar.getDiffuseFraction()
            assert diffuse == pytest.approx(solar.getSolarFlux() * f * cosz, rel=1e-3)
            assert direct == pytest.approx(solar.getSolarFlux() * (1 - f), rel=1e-3)

    def test_band_components_sum(self):
        with Context() as context:
            solar = self._solar(context)
            assert solar.getDirectSolarFluxPAR() + solar.getDirectSolarFluxNIR() == pytest.approx(
                solar.getDirectSolarFlux(), rel=1e-4)
            assert solar.getDiffuseSolarFluxPAR() + solar.getDiffuseSolarFluxNIR() == pytest.approx(
                solar.getDiffuseSolarFlux(), rel=1e-4)
            # Clear-sky diffuse light is richer in PAR than the direct beam.
            assert (solar.getDiffuseSolarFluxPAR() / solar.getDiffuseSolarFlux()
                    > solar.getDirectSolarFluxPAR() / solar.getDirectSolarFlux())


# =========================================================================== #
# PlantHydraulics
# =========================================================================== #
@pytest.mark.native_only
class TestPlantHydraulicsByPlantIDs:

    def test_matches_per_plant_query(self):
        from pyhelios import PlantHydraulicsModel
        from pyhelios.wrappers import UPlantHydraulicsWrapper as hw
        if not _available("planthydraulics"):
            pytest.skip("planthydraulics plugin not available")
        if not hw._PRIMITIVES_BY_PLANT_IDS_AVAILABLE:
            pytest.skip("getPrimitivesByPlantIDs not in the native library (requires helios-core v1.3.96)")
        with Context() as context:
            leaves = [context.addPatch(center=vec3(i, 0, 1), size=vec2(0.1, 0.1)) for i in range(4)]
            for i, uuid in enumerate(leaves):
                context.setPrimitiveDataInt(uuid, "plantID", 1 if i < 2 else 2)
            with PlantHydraulicsModel(context) as hydraulics:
                result = hydraulics.getPrimitivesByPlantIDs([1, 2, 3])
                assert set(result) == {1, 2, 3}
                assert result[1] == hydraulics.getPrimitivesByPlantID(1) == sorted(leaves[:2])
                assert result[2] == sorted(leaves[2:])
                assert result[3] == []
                with pytest.raises(ValueError):
                    hydraulics.getPrimitivesByPlantIDs([1.5])


# =========================================================================== #
# Photosynthesis, stomatal conductance, leaf optics
# =========================================================================== #
@pytest.mark.native_only
class TestPhotosynthesisLibrary1396:

    def _photo(self, context):
        from pyhelios import PhotosynthesisModel
        if not _available("photosynthesis"):
            pytest.skip("photosynthesis plugin not available")
        return PhotosynthesisModel(context)

    def test_c4_library_array_has_42_slots_and_shifted_scalars(self):
        with Context() as context:
            photo = self._photo(context)
            setaria = photo.getC4CoefficientsFromLibrary("SetariaViridis_vC2021")
            assert len(setaria) == 42
            assert setaria[37] == pytest.approx(0.15)   # f_spectral
            assert setaria[38] == pytest.approx(0.7)    # theta_etr
            assert setaria[39] == pytest.approx(4.0)    # h_protons
            sorghum = photo.getC4CoefficientsFromLibrary("Sorghum")
            assert sorghum[38] == pytest.approx(0.03)   # theta_etr of the GEMINI sorghum fit

    def test_c4_coefficients_round_trip_and_legacy_rejected(self):
        with Context() as context:
            uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
            photo = self._photo(context)
            photo.setModelTypeC4()
            coeffs = photo.getC4CoefficientsFromLibrary("Sorghum_GEMINI2026")
            photo.setC4ModelCoefficients(coeffs, [uuid])
            assert photo.getC4ModelCoefficients(uuid)[37:] == pytest.approx(coeffs[37:])
            with pytest.raises(ValueError, match="absorptance"):
                photo.setC4ModelCoefficients(coeffs[:37] + [0.85] + coeffs[37:], [uuid])

    @pytest.mark.parametrize("species, vcmax25, jmax25", [
        ("Cowpea", 117.6, 379.9), ("CommonBean", 104.7, 259.4), ("Bean", 104.7, 259.4),
    ])
    def test_new_farquhar_entries(self, species, vcmax25, jmax25):
        # An unknown species silently falls back to default coefficients natively, so check the values.
        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
            photo = self._photo(context)
            coeffs = photo.getSpeciesCoefficients(species)
            assert coeffs[0] == pytest.approx(vcmax25, rel=1e-4)
            assert coeffs[1] == pytest.approx(jmax25, rel=1e-4)
            photo.setSpeciesCoefficients(species)

    def test_new_bmf_entries(self):
        from pyhelios import StomatalConductanceModel
        if not _available("stomatalconductance"):
            pytest.skip("stomatalconductance plugin not available")
        with Context() as context:
            with StomatalConductanceModel(context) as stomatal:
                for species in ("Cowpea", "CommonBean", "Bean", "Sorghum"):
                    coeffs = stomatal.getBMFCoefficientsFromLibrary(species)
                    assert coeffs.Em > 0


@pytest.mark.native_only
class TestLeafOptics1396:

    def test_unknown_species_raises_and_default_drymass(self):
        from pyhelios import LeafOptics
        from pyhelios.LeafOptics import LeafOpticsError
        if not _available("leafoptics"):
            pytest.skip("leafoptics plugin not available")
        with Context() as context:
            with LeafOptics(context) as leafoptics:
                leafoptics.disableMessages()
                with pytest.raises(LeafOpticsError):
                    leafoptics.getPropertiesFromLibrary("not_a_real_species")
                assert leafoptics.getPropertiesFromLibrary("default").drymass == pytest.approx(0.006)


# =========================================================================== #
# PlantArchitecture
# =========================================================================== #
def _require_pa_1396():
    from pyhelios.wrappers import UPlantArchitectureWrapper as pw
    if not _available("plantarchitecture"):
        pytest.skip("plantarchitecture plugin not available")
    if not pw._PLANTARCHITECTURE_1396_AVAILABLE:
        pytest.skip("PlantArchitecture 1.3.96 functions not in the native library; rebuild required")


def _first_leafy_phytomer(plantarch, plant_id, shoot_id=0):
    for node in range(plantarch.getShootNodeCount(plant_id, shoot_id)):
        petioles = plantarch.getPhytomerLeafObjectIDs(plant_id, shoot_id, node)
        if petioles and petioles[0]:
            return node, petioles[0]
    pytest.fail("no phytomer with leaves on the main shoot; assertions would be vacuous")


@pytest.mark.cross_platform
class TestPlantArchitecture1396Validation:

    @staticmethod
    def _pa():
        from pyhelios import PlantArchitecture
        plantarch = PlantArchitecture.__new__(PlantArchitecture)
        plantarch._plantarch_ptr = None
        plantarch.context = None
        return plantarch

    @pytest.mark.parametrize("roll", [-0.1, 1.5, float("nan")])
    def test_roll_fraction_range(self, roll):
        from pyhelios import PlantArchitecture
        with pytest.raises(ValueError):
            PlantArchitecture.setPlantLeafRoll(self._pa(), 0, roll)
        with pytest.raises(ValueError):
            PlantArchitecture.setPetioleLeafRoll(self._pa(), 0, 0, 0, 0, roll)

    @pytest.mark.parametrize("kwargs", [
        {"max_swing_deg": 0.0}, {"max_swing_deg": 200.0}, {"candidate_refresh_days": 0.0},
        {"clearance": -0.01}, {"settle_rate_deg_per_day": -1.0},
    ])
    def test_fruit_collision_parameter_ranges(self, kwargs):
        from pyhelios import PlantArchitecture
        with pytest.raises(ValueError):
            PlantArchitecture.setFruitBranchCollisionParameters(self._pa(), **kwargs)

    def test_reshape_leaf_requires_leaf_shape_values(self):
        from pyhelios import PlantArchitecture
        with pytest.raises(ValueError, match="LeafShapeValues"):
            PlantArchitecture.reshapeLeaf(self._pa(), 0, 0, 0, 0, 0, {"roll_fraction": 0.5})

    def test_elevation_tracking_rejects_empty_list(self):
        from pyhelios import PlantArchitecture
        with pytest.raises(ValueError):
            PlantArchitecture.enableLeafElevationAngleDistributionTracking(self._pa(), [], 2.0, 2.0, 90.0)


@pytest.mark.native_only
class TestPlantArchitecture1396Native:

    def test_plant_leaf_roll_keeps_leaf_objects_and_data(self):
        _require_pa_1396()
        from pyhelios import PlantArchitecture
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("sorghum")
            plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 25.0)
            leaves = plantarch.getPlantLeafObjectIDs(plant_id)
            assert leaves, "sorghum at age 25 has no leaves; assertions would be vacuous"
            context.setObjectDataFloat(leaves[0], "marker", 3.0)
            node, petiole_leaves = _first_leafy_phytomer(plantarch, plant_id)

            plantarch.setPlantLeafRoll(plant_id, 0.5)

            assert plantarch.getPlantLeafObjectIDs(plant_id) == leaves
            assert context.getObjectData(leaves[0], "marker") == pytest.approx(3.0)
            assert plantarch.getLeafShape(plant_id, 0, node, 0, 0).roll_fraction == pytest.approx(0.5)

            plantarch.setPetioleLeafRoll(plant_id, 0, node, 0, 0.0)
            assert plantarch.getLeafShape(plant_id, 0, node, 0, 0).roll_fraction == pytest.approx(0.0)

    def test_get_and_reshape_leaf_round_trip(self):
        _require_pa_1396()
        from pyhelios import PlantArchitecture, PlantArchitectureError
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("sorghum")
            plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 25.0)
            node, petiole_leaves = _first_leafy_phytomer(plantarch, plant_id)
            leaf_obj = petiole_leaves[0]
            area_before = context.getObjectArea(leaf_obj)

            shape = plantarch.getLeafShape(plant_id, 0, node, 0, 0)
            assert shape.aspect_ratio > 0 and shape.subdivisions_x >= 1
            shape.lateral_curvature = 0.0
            shape.roll_fraction = 0.3
            plantarch.reshapeLeaf(plant_id, 0, node, 0, 0, shape)

            after = plantarch.getLeafShape(plant_id, 0, node, 0, 0)
            assert after.roll_fraction == pytest.approx(0.3)
            assert context.doesObjectExist(leaf_obj)
            # Rolling bends the blade without stretching it.
            assert context.getObjectArea(leaf_obj) == pytest.approx(area_before, rel=0.15)

            with pytest.raises(PlantArchitectureError):
                plantarch.getLeafShape(plant_id, 0, node, 0, 999)

    def test_sorghum_class_map_and_roll_survive_shoot_parameter_round_trip(self):
        _require_pa_1396()
        from pyhelios import PlantArchitecture
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("sorghum")
            sp = plantarch.getCurrentShootParameters("mainstem", return_typed=True)
            proto = sp.phytomer_parameters.leaf.prototype
            assert proto.leaf_class_map_file, "sorghum leaf class map missing from ShootParameters"
            assert any("SorghumLeaf_classes" in f for f in proto.leaf_class_map_file.values())

            proto.roll_fraction.parameters = [0.25]
            plantarch.defineShootType("mainstem_rolled", sp)
            back = plantarch.getCurrentShootParameters("mainstem_rolled", return_typed=True)
            back_proto = back.phytomer_parameters.leaf.prototype
            assert back_proto.roll_fraction.parameters == [pytest.approx(0.25)]
            assert back_proto.leaf_class_map_file == proto.leaf_class_map_file

    def test_apple_bark_class_map_survives_shoot_parameter_round_trip(self):
        _require_pa_1396()
        from pyhelios import PlantArchitecture
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("apple")
            found = False
            for label in plantarch.listShootTypeLabels():
                sp = plantarch.getCurrentShootParameters(label, return_typed=True)
                bark = sp.phytomer_parameters.internode.image_class_map_file
                if not bark:
                    continue
                found = True
                plantarch.defineShootType(label + "_copy", sp)
                back = plantarch.getCurrentShootParameters(label + "_copy", return_typed=True)
                assert back.phytomer_parameters.internode.image_class_map_file == bark
            assert found, "no apple shoot type carries a bark class map"

    def test_set_petiole_leaflets_with_intercalary_scale(self):
        _require_pa_1396()
        from pyhelios import PlantArchitecture

        def petiole_leaf_area(intercalary):
            with Context() as context, PlantArchitecture(context) as plantarch:
                plantarch.disableMessages()
                plantarch.loadPlantModelFromLibrary("bean")
                plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 30.0)
                node, _ = _first_leafy_phytomer(plantarch, plant_id)
                plantarch.setPetioleLeaflets(plant_id, 0, node, 0, 5, 0.2, 0.8, 0.08,
                                             intercalary_leaflet_scale=intercalary)
                ids = plantarch.getPhytomerLeafObjectIDs(plant_id, 0, node)[0]
                assert len(ids) == 5
                return sum(context.getObjectArea(i) for i in ids)

        # The argument must reach native: a different intercalary scale changes the leaflets built.
        assert petiole_leaf_area(0.0) != pytest.approx(petiole_leaf_area(0.5), rel=0.02)

    def test_fruit_branch_collision_controls_run_through_growth(self):
        _require_pa_1396()
        from pyhelios import PlantArchitecture
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("bean")
            plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 45.0)
            plantarch.setFruitBranchCollisionParameters(60.0, 5.0, 0.002, 5.0)
            plantarch.enableFruitBranchCollisionAvoidance()
            plantarch.advanceTime(3.0, plant_id=plant_id)
            plantarch.disableFruitBranchCollisionAvoidance()
            plantarch.advanceTime(1.0, plant_id=plant_id)
            with pytest.raises(ValueError):
                plantarch.setFruitBranchCollisionParameters(max_swing_deg=181.0)

    def test_elevation_tracking_accepts_a_list(self):
        _require_pa_1396()
        from pyhelios import PlantArchitecture, PlantArchitectureError
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("bean")
            ids = [plantarch.buildPlantInstanceFromLibrary(vec3(i, 0, 0), 5.0) for i in range(2)]
            plantarch.enableLeafElevationAngleDistributionTracking(ids, 2.0, 2.0, 90.0)
            assert all(plantarch.isLeafAngleDistributionTrackingEnabled(i) for i in ids)
            with pytest.raises(PlantArchitectureError):
                plantarch.enableLeafElevationAngleDistributionTracking([ids[0], 9999], 2.0, 2.0, 90.0)

    def test_fruit_and_root_nitrogen_pools(self):
        _require_pa_1396()
        from pyhelios import PlantArchitecture, PlantArchitectureError
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("bean")
            plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 10.0)
            assert plantarch.getPlantFruitNitrogen(plant_id) == pytest.approx(0.0)
            assert plantarch.getPlantRootNitrogen(plant_id) == pytest.approx(0.0)
            for getter in (plantarch.getPlantFruitNitrogen, plantarch.getPlantRootNitrogen):
                with pytest.raises(PlantArchitectureError, match="does not exist"):
                    getter(9999)


# =========================================================================== #
# RadiationModel (needs a ray-tracing backend; probed out of process)
# =========================================================================== #
@pytest.mark.native_only
class TestRadiation1396:

    @staticmethod
    def _radiation(context):
        from pyhelios.wrappers import URadiationModelWrapper as rw
        from tests.test_radiation_model import radiation_model_or_skip
        if not rw._RADIATION_1396_AVAILABLE:
            pytest.skip("RadiationModel 1.3.96 functions not in the native library; rebuild required")
        return radiation_model_or_skip(context)

    def test_color_correction_matrix_rows_sum_to_one(self):
        from pyhelios.RadiationModel import RadiationModelError
        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
            radiation = self._radiation(context)
            try:
                for band in ("red", "green", "blue"):
                    radiation.addRadiationBand(band)
                radiation.addRadiationCamera("cam", ["red", "green", "blue"], vec3(0, 0, 3), vec3(0, 0, 0))
                with pytest.raises(RadiationModelError):
                    radiation.getCameraColorCorrectionMatrix("cam")  # no spectral responses yet
                for band in ("red", "green", "blue"):
                    radiation.setCameraSpectralResponse("cam", band, f"iPhone12ProMAX_{band}")
                ccm = radiation.getCameraColorCorrectionMatrix("cam")
                assert len(ccm) == 3 and all(len(row) == 3 for row in ccm)
                for row in ccm:
                    assert sum(row) == pytest.approx(1.0, abs=1e-4)
                # Diagonal-dominant: each channel maps mostly onto itself.
                assert all(ccm[i][i] > 0.5 for i in range(3))
            finally:
                radiation.__exit__(None, None, None)

    def test_brightness_temperature_of_blackbody_surface(self):
        from pyhelios.RadiationModel import CameraProperties
        with Context() as context:
            ground = context.addPatch(center=vec3(0, 0, 0), size=vec2(50, 50))
            context.setPrimitiveDataFloat(ground, "temperature", 300.0)
            radiation = self._radiation(context)
            try:
                radiation.addRadiationBand("TIR", 8000, 14000)
                radiation.enableEmission("TIR")
                radiation.setScatteringDepth("TIR", 0)
                radiation.setDiffuseRadiationFlux("TIR", 0.0)
                props = CameraProperties(camera_resolution=(8, 8), exposure="manual", lens_diameter=0.0,
                                         HFOV=10.0)
                radiation.addRadiationCamera("thermal", ["TIR"], vec3(0, 0, 5), vec3(0, 0, 0),
                                             camera_properties=props, antialiasing_samples=4)
                radiation.updateGeometry()
                radiation.runBand("TIR")
                temps = radiation.getCameraPixelBrightnessTemperature("thermal", "TIR")
                assert len(temps) == 64
                assert np.median(temps) == pytest.approx(300.0, abs=1.0)
            finally:
                radiation.__exit__(None, None, None)

    def test_apply_spectral_class_maps_textures_apple_bark(self):
        from pyhelios import PlantArchitecture
        _require_pa_1396()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("apple")
            plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 200.0)
            uuids = plantarch.getAllPlantUUIDs(plant_id)
            carriers = [u for u in uuids if context.doesPrimitiveDataExist(u, "spectral_class_map")]
            assert carriers, "apple carries no spectral_class_map primitive data; assertions would be vacuous"
            radiation = self._radiation(context)
            try:
                radiation.applySpectralClassMaps(uuids)
                textured = [u for u in carriers if context.primitiveHasSpectralTexture(u)]
                assert textured, "applySpectralClassMaps gave no bark primitive a spectral texture"
                with pytest.raises(ValueError):
                    radiation.applySpectralClassMaps([-1])
            finally:
                radiation.__exit__(None, None, None)


# =========================================================================== #
# Visualizer
# =========================================================================== #
@pytest.mark.cross_platform
class TestVisualizer1396Validation:

    @staticmethod
    def _vis():
        from pyhelios import Visualizer
        vis = Visualizer.__new__(Visualizer)
        vis.visualizer = object()  # validation runs before any native call
        return vis

    def test_up_direction_validation(self):
        with pytest.raises(ValueError, match="vec3"):
            self._vis().setCameraUpDirection((0, 0, 1))
        with pytest.raises(ValueError, match="zero"):
            self._vis().setCameraUpDirection(vec3(0, 0, 0))

    def test_principal_point_validation(self):
        with pytest.raises(ValueError, match="column"):
            self._vis().setCameraPrincipalPoint(float("inf"), 10)
        with pytest.raises(ValueError, match="row"):
            self._vis().setCameraPrincipalPoint(10, "5")


@pytest.mark.native_only
class TestVisualizer1396Native:

    def test_up_direction_rolls_the_image(self):
        from pyhelios import Visualizer
        from pyhelios.wrappers import UVisualizerWrapper as vw
        from tests.test_visualizer import is_headless_environment
        if not _available("visualizer") or is_headless_environment():
            pytest.skip("visualizer not available in this environment")
        if not vw._CAMERA_1396_FUNCTIONS_AVAILABLE:
            pytest.skip("camera up direction not in the native library; rebuild required")
        with Context() as context:
            # A patch offset in +x: with +y up it lands right of centre; rolled so +x is up it lands above.
            patch = context.addPatch(center=vec3(0.6, 0, 0), size=vec2(0.3, 0.3))
            with Visualizer(64, 64, antialiasing_samples=1, headless=True) as vis:
                vis.buildContextGeometry(context)
                vis.setCameraPosition(vec3(0, 0, 3), vec3(0, 0, 0))

                def centroid():
                    pixels, w, h = vis.getPixelUUIDs()
                    hits = [(i % w, i // w) for i, v in enumerate(pixels) if v == patch + 1]
                    assert hits, "patch not visible"
                    col = sum(x for x, _ in hits) / len(hits)
                    row = sum(y for _, y in hits) / len(hits)
                    return col / w, row / h  # fractions of the image, row 0 at the top

                vis.setCameraUpDirection(vec3(0, 1, 0))
                col, row = centroid()
                assert col > 0.6 and abs(row - 0.5) < 0.1
                vis.setCameraUpDirection(vec3(1, 0, 0))
                col, row = centroid()
                assert row < 0.4 and abs(col - 0.5) < 0.1
                vis.clearCameraUpDirection()
                vis.setCameraPrincipalPoint(32.0, 32.0)
