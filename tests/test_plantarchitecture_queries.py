"""
Tests for the PlantArchitecture plant-level queries: getPlantName, determinePhenologyStage,
getShootNodeCount, getPlantStemHeight, get/setPlantBasePosition, getPlantInternodeObjectIDs and
the leaf inclination/azimuth angle distributions.
"""

import ctypes
from unittest.mock import patch

import pytest

from pyhelios import Context, PlantArchitecture, PlantArchitectureError
from pyhelios.types import vec3, RGBcolor, AxisRotation
from pyhelios.wrappers import UPlantArchitectureWrapper as plantarch_wrapper
from pyhelios.plugins.registry import get_plugin_registry

PHENOLOGY_STAGES = {"dormant", "vegetative", "reproductive", "senescent"}

QUERY_SYMBOLS = (
    "determinePhenologyStage", "getPlantName", "getShootNodeCount", "getPlantStemHeight",
    "getPlantBasePosition", "getPlantBasePositions", "setPlantBasePosition",
    "getPlantInternodeObjectIDs", "getPlantLeafInclinationAngleDistribution",
    "getPlantLeafAzimuthAngleDistribution",
)


def _require_plantarch():
    if not get_plugin_registry().is_plugin_available('plantarchitecture'):
        pytest.skip("PlantArchitecture plugin not available")


@pytest.mark.cross_platform
class TestPlantQueryValidation:
    """Argument validation (no native library needed)."""

    def _pa(self):
        return PlantArchitecture.__new__(PlantArchitecture)

    @pytest.mark.parametrize("method", ["getPlantName", "determinePhenologyStage", "getPlantStemHeight",
                                        "getPlantInternodeObjectIDs"])
    @pytest.mark.parametrize("bad", [-1, True, 1.5, "0", None])
    def test_single_plant_queries_reject_bad_plant_id(self, method, bad):
        with pytest.raises(ValueError, match="(?i)plant id"):
            getattr(PlantArchitecture, method)(self._pa(), bad)

    @pytest.mark.parametrize("ids", [(-1, 0), (0, -1), (True, 0), (0, 1.5), ("0", 0)])
    def test_getShootNodeCount_rejects_bad_identifiers(self, ids):
        with pytest.raises(ValueError):
            PlantArchitecture.getShootNodeCount(self._pa(), *ids)

    @pytest.mark.parametrize("bad", [-1, True, 1.5, "0", None, [], [0, -1]])
    def test_getPlantBasePosition_rejects_bad_plant_ids(self, bad):
        with pytest.raises(ValueError):
            PlantArchitecture.getPlantBasePosition(self._pa(), bad)

    @pytest.mark.parametrize("bad", [(1, 2, 3), [1, 2, 3], RGBcolor(1, 0, 0), None])
    def test_setPlantBasePosition_requires_vec3_positionally(self, bad):
        with pytest.raises(ValueError, match="(?i)vec3"):
            PlantArchitecture.setPlantBasePosition(self._pa(), 0, bad)

    @pytest.mark.parametrize("bad", [(1, 2, 3), RGBcolor(1, 0, 0)])
    def test_setPlantBasePosition_requires_vec3_by_keyword(self, bad):
        with pytest.raises(ValueError, match="(?i)vec3"):
            PlantArchitecture.setPlantBasePosition(self._pa(), plant_id=0, base_position=bad)

    def test_setPlantBasePosition_rejects_bad_plant_id(self):
        with pytest.raises(ValueError, match="(?i)plant id"):
            PlantArchitecture.setPlantBasePosition(self._pa(), -1, vec3(0, 0, 0))

    @pytest.mark.parametrize("bad", ["", 3, b"stem"])
    def test_getPlantInternodeObjectIDs_rejects_bad_shoot_type_label(self, bad):
        with pytest.raises(ValueError, match="(?i)shoot type label"):
            PlantArchitecture.getPlantInternodeObjectIDs(self._pa(), 0, bad)

    @pytest.mark.parametrize("method", ["getPlantLeafInclinationAngleDistribution",
                                        "getPlantLeafAzimuthAngleDistribution"])
    @pytest.mark.parametrize("bad_bins", [0, -3, 2.5, True, "9", None])
    def test_distributions_reject_bad_bin_count(self, method, bad_bins):
        with pytest.raises(ValueError, match="num_bins"):
            getattr(PlantArchitecture, method)(self._pa(), 0, bad_bins)

    @pytest.mark.parametrize("method", ["getPlantLeafInclinationAngleDistribution",
                                        "getPlantLeafAzimuthAngleDistribution"])
    @pytest.mark.parametrize("bad", [1, "yes", None])
    def test_distributions_reject_non_bool_normalize(self, method, bad):
        with pytest.raises(ValueError, match="normalize"):
            getattr(PlantArchitecture, method)(self._pa(), 0, 9, bad)

    @pytest.mark.parametrize("method", ["getPlantLeafInclinationAngleDistribution",
                                        "getPlantLeafAzimuthAngleDistribution"])
    @pytest.mark.parametrize("bad", [-1, [], [0, -2], "0", True])
    def test_distributions_reject_bad_plant_ids(self, method, bad):
        with pytest.raises(ValueError):
            getattr(PlantArchitecture, method)(self._pa(), bad, 9)

    def test_wrappers_guard_with_the_plant_query_flag(self):
        """A wrapper checking the wrong flag would call a function with no argtypes set."""
        calls = [
            lambda: plantarch_wrapper.determinePhenologyStage(None, 0),
            lambda: plantarch_wrapper.getPlantName(None, 0),
            lambda: plantarch_wrapper.getShootNodeCount(None, 0, 0),
            lambda: plantarch_wrapper.getPlantStemHeight(None, 0),
            lambda: plantarch_wrapper.getPlantBasePosition(None, 0),
            lambda: plantarch_wrapper.getPlantBasePositions(None, [0]),
            lambda: plantarch_wrapper.setPlantBasePosition(None, 0, (0, 0, 0)),
            lambda: plantarch_wrapper.getPlantInternodeObjectIDs(None, 0),
            lambda: plantarch_wrapper.getPlantLeafInclinationAngleDistribution(None, [0], 9),
            lambda: plantarch_wrapper.getPlantLeafAzimuthAngleDistribution(None, [0], 9),
        ]
        with patch.object(plantarch_wrapper, '_PLANTARCHITECTURE_PLANT_QUERIES_AVAILABLE', False):
            for call in calls:
                with pytest.raises(RuntimeError, match="(?i)rebuild"):
                    call()

    def test_expected_symbols_are_registered(self):
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture native functions not available")
        for name in QUERY_SYMBOLS:
            assert hasattr(plantarch_wrapper.helios_lib, name), f"native library is missing {name}"
        assert plantarch_wrapper._PLANTARCHITECTURE_PLANT_QUERIES_AVAILABLE


@pytest.fixture
def bean():
    """A context, plant architecture and a 20-day library bean plant (before flower initiation)."""
    _require_plantarch()
    with Context() as context:
        context.seedRandomGenerator(11)
        with PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("bean")
            plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 20.0)
            yield context, plantarch, plant_id


@pytest.mark.native_only
class TestPlantIdentityAndPhenology:

    def test_name_matches_library_label(self, bean):
        _, plantarch, plant_id = bean
        assert plantarch.getPlantName(plant_id) == "bean"

    def test_name_follows_the_model_each_plant_was_built_from(self, bean):
        _, plantarch, bean_id = bean
        plantarch.loadPlantModelFromLibrary("tomato")
        tomato_id = plantarch.buildPlantInstanceFromLibrary(vec3(1, 0, 0), 10.0)
        assert plantarch.getPlantName(tomato_id) == "tomato"
        assert plantarch.getPlantName(bean_id) == "bean"

    def test_phenology_stage_changes_as_the_plant_ages(self, bean):
        _, plantarch, plant_id = bean
        young = plantarch.determinePhenologyStage(plant_id)
        assert young in PHENOLOGY_STAGES
        assert young == "vegetative"

        # Library bean initiates flowers at 40 days and has open flowers by about 60.
        plantarch.advanceTime(45.0, plant_id=plant_id)
        old = plantarch.determinePhenologyStage(plant_id)
        assert old in PHENOLOGY_STAGES
        assert old == "reproductive", (
            f"flowers {len(plantarch.getPlantFlowerObjectIDs(plant_id))}, "
            f"fruit {len(plantarch.getPlantFruitObjectIDs(plant_id))}")

    def test_dormant_plant_reports_dormant(self, bean):
        _, plantarch, plant_id = bean
        plantarch.makePlantDormant(plant_id)
        assert plantarch.determinePhenologyStage(plant_id) == "dormant"

    @pytest.mark.parametrize("method", ["getPlantName", "determinePhenologyStage", "getPlantStemHeight",
                                        "getPlantInternodeObjectIDs", "getPlantBasePosition"])
    def test_missing_plant_raises(self, bean, method):
        _, plantarch, plant_id = bean
        with pytest.raises(PlantArchitectureError, match="(?i)does not exist"):
            getattr(plantarch, method)(plant_id + 999)


@pytest.mark.native_only
class TestStemAndNodeQueries:

    def test_stem_height_is_positive_and_at_most_plant_height(self, bean):
        _, plantarch, plant_id = bean
        stem = plantarch.getPlantStemHeight(plant_id)
        assert stem > 0.0
        assert stem <= plantarch.getPlantHeight(plant_id) + 1e-6

    def test_stem_height_of_plant_without_shoots_raises(self, bean):
        _, plantarch, _ = bean
        empty = plantarch.addPlantInstance(vec3(0, 0, 0), 0.0)
        with pytest.raises(PlantArchitectureError, match="(?i)no shoots"):
            plantarch.getPlantStemHeight(empty)

    def test_node_count_is_positive_for_every_shoot(self, bean):
        _, plantarch, plant_id = bean
        shoot_ids = plantarch.getAllShootIDs(plant_id)
        assert shoot_ids
        counts = [plantarch.getShootNodeCount(plant_id, s) for s in shoot_ids]
        assert counts[0] > 0
        assert all(isinstance(c, int) and c >= 0 for c in counts)
        assert counts == [plantarch.getShoot(plant_id, s)["node_count"] for s in shoot_ids]

    def test_node_count_grows_with_time(self, bean):
        _, plantarch, plant_id = bean
        before = sum(plantarch.getShootNodeCount(plant_id, s) for s in plantarch.getAllShootIDs(plant_id))
        plantarch.advanceTime(15.0, plant_id=plant_id)
        after = sum(plantarch.getShootNodeCount(plant_id, s) for s in plantarch.getAllShootIDs(plant_id))
        assert after > before

    def test_out_of_range_shoot_raises(self, bean):
        _, plantarch, plant_id = bean
        bad_shoot = len(plantarch.getAllShootIDs(plant_id)) + 5
        with pytest.raises(PlantArchitectureError, match="(?i)out of range"):
            plantarch.getShootNodeCount(plant_id, bad_shoot)


@pytest.mark.native_only
class TestInternodeObjectIDs:

    def test_internode_ids_are_valid_objects_disjoint_from_leaves(self, bean):
        context, plantarch, plant_id = bean
        internodes = plantarch.getPlantInternodeObjectIDs(plant_id)
        leaves = plantarch.getPlantLeafObjectIDs(plant_id)
        assert internodes and leaves
        assert len(set(internodes)) == len(internodes)
        assert all(context.doesObjectExist(o) for o in internodes)
        assert set(internodes).isdisjoint(leaves)
        assert set(internodes) <= set(plantarch.getAllPlantObjectIDs(plant_id))

    def test_shoot_type_filter_returns_a_subset(self, bean):
        _, plantarch, plant_id = bean
        everything = set(plantarch.getPlantInternodeObjectIDs(plant_id))
        unifoliate = plantarch.getPlantInternodeObjectIDs(plant_id, "unifoliate")
        trifoliate = plantarch.getPlantInternodeObjectIDs(plant_id, shoot_type_label="trifoliate")
        assert unifoliate and trifoliate
        assert set(unifoliate) <= everything and set(trifoliate) <= everything
        assert set(unifoliate).isdisjoint(trifoliate)

    def test_unknown_shoot_type_raises(self, bean):
        _, plantarch, plant_id = bean
        with pytest.raises(PlantArchitectureError, match="(?i)no shoots with shoot type label"):
            plantarch.getPlantInternodeObjectIDs(plant_id, "no_such_shoot_type")


@pytest.mark.native_only
class TestLeafAngleDistributions:

    @pytest.mark.parametrize("method", ["getPlantLeafInclinationAngleDistribution",
                                        "getPlantLeafAzimuthAngleDistribution"])
    @pytest.mark.parametrize("num_bins", [1, 9, 36])
    def test_normalized_distribution_has_num_bins_and_sums_to_one(self, bean, method, num_bins):
        _, plantarch, plant_id = bean
        dist = getattr(plantarch, method)(plant_id, num_bins)
        assert len(dist) == num_bins
        assert all(v >= 0.0 for v in dist)
        assert sum(dist) == pytest.approx(1.0, abs=1e-4)

    @pytest.mark.parametrize("method", ["getPlantLeafInclinationAngleDistribution",
                                        "getPlantLeafAzimuthAngleDistribution"])
    def test_unnormalized_distribution_sums_to_leaf_area(self, bean, method):
        _, plantarch, plant_id = bean
        dist = getattr(plantarch, method)(plant_id, 12, normalize=False)
        assert len(dist) == 12
        assert sum(dist) == pytest.approx(plantarch.getPlantLeafArea(plant_id), rel=1e-3)

    def test_inclination_distribution_matches_leaf_angle_posing(self, bean):
        """Flattening the leaves moves area into the lowest inclination bins."""
        _, plantarch, plant_id = bean
        plantarch.setLeafAngleDistribution(plant_id, 8.0, 1.0)
        flat = plantarch.getPlantLeafInclinationAngleDistribution(plant_id, 3)
        plantarch.setLeafAngleDistribution(plant_id, 1.0, 8.0)
        steep = plantarch.getPlantLeafInclinationAngleDistribution(plant_id, 3)
        assert flat[0] > steep[0]
        assert steep[2] > flat[2]

    @pytest.mark.parametrize("method", ["getPlantLeafInclinationAngleDistribution",
                                        "getPlantLeafAzimuthAngleDistribution"])
    def test_multiple_plants_are_pooled(self, bean, method):
        _, plantarch, first = bean
        second = plantarch.buildPlantInstanceFromLibrary(vec3(1, 0, 0), 25.0)
        a = getattr(plantarch, method)(first, 8, normalize=False)
        b = getattr(plantarch, method)(second, 8, normalize=False)
        pooled = getattr(plantarch, method)([first, second], 8, normalize=False)
        assert pooled == pytest.approx([x + y for x, y in zip(a, b)], rel=1e-4, abs=1e-9)
        normalized = getattr(plantarch, method)((first, second), 8)
        assert sum(normalized) == pytest.approx(1.0, abs=1e-4)

    def test_native_shim_rejects_zero_bins(self, bean):
        """The shim guards Nbins == 0 itself, rather than relying on Python-side validation."""
        _, plantarch, plant_id = bean
        ids = (ctypes.c_uint * 1)(plant_id)
        count = ctypes.c_int()
        with pytest.raises(Exception, match="(?i)number of bins"):
            plantarch_wrapper.helios_lib.getPlantLeafInclinationAngleDistribution(
                plantarch._plantarch_ptr, ids, 1, 0, 1, ctypes.byref(count))


@pytest.mark.native_only
class TestPlantBasePosition:

    def test_library_plant_reports_its_build_position(self, bean):
        _, plantarch, _ = bean
        plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(2.0, -1.5, 0.25), 15.0)
        p = plantarch.getPlantBasePosition(plant_id)
        assert isinstance(p, vec3)
        assert (p.x, p.y, p.z) == pytest.approx((2.0, -1.5, 0.25))

    def test_list_of_ids_returns_list_in_order(self, bean):
        _, plantarch, first = bean
        second = plantarch.buildPlantInstanceFromLibrary(vec3(3, 4, 0), 15.0)
        positions = plantarch.getPlantBasePosition([second, first])
        assert len(positions) == 2 and all(isinstance(p, vec3) for p in positions)
        assert (positions[0].x, positions[0].y, positions[0].z) == pytest.approx((3, 4, 0))
        assert (positions[1].x, positions[1].y, positions[1].z) == pytest.approx((0, 0, 0))

    def test_set_base_position_places_the_stem_built_afterwards(self, bean):
        context, plantarch, _ = bean
        target = vec3(1.0, 2.0, 0.5)
        plant_id = plantarch.addPlantInstance(vec3(0, 0, 0), 0.0)
        plantarch.setPlantBasePosition(plant_id, target)
        plantarch.addBaseStemShoot(plant_id, 1, AxisRotation(0, 0, 0), 0.01, 0.1, 1.0, 1.0, 0.9, "unifoliate")

        p = plantarch.getPlantBasePosition(plant_id)
        assert (p.x, p.y, p.z) == pytest.approx((1.0, 2.0, 0.5))

        stem = plantarch.getPlantInternodeObjectIDs(plant_id)
        assert stem
        lo, hi = context.getObjectBoundingBox(stem)
        assert lo.x - 0.05 <= target.x <= hi.x + 0.05
        assert lo.y - 0.05 <= target.y <= hi.y + 0.05
        assert lo.z == pytest.approx(target.z, abs=0.02)

    def test_set_base_position_on_built_plant_moves_the_plant(self, bean):
        """The plant's geometry is translated with its base position (helios-core 1.3.93)."""
        context, plantarch, plant_id = bean
        objects = plantarch.getAllPlantObjectIDs(plant_id)
        base_before = plantarch.getPlantBasePosition(plant_id)
        lo_before, hi_before = context.getObjectBoundingBox(objects)
        plantarch.setPlantBasePosition(plant_id, vec3(5, 5, 0))
        p = plantarch.getPlantBasePosition(plant_id)
        assert (p.x, p.y, p.z) == pytest.approx((5, 5, 0))
        shift = (5 - base_before.x, 5 - base_before.y, 0 - base_before.z)
        lo_after, hi_after = context.getObjectBoundingBox(objects)
        assert (lo_after.x - lo_before.x, lo_after.y - lo_before.y, lo_after.z - lo_before.z) == pytest.approx(shift, abs=1e-4)
        assert (hi_after.x - hi_before.x, hi_after.y - hi_before.y, hi_after.z - hi_before.z) == pytest.approx(shift, abs=1e-4)

    def test_set_base_position_on_missing_plant_raises(self, bean):
        _, plantarch, plant_id = bean
        with pytest.raises(PlantArchitectureError, match="(?i)does not exist"):
            plantarch.setPlantBasePosition(plant_id + 999, vec3(0, 0, 0))
