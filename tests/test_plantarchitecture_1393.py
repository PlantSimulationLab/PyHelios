"""
Tests for the helios-core 1.3.93 PlantArchitecture changes that reach the Python API: build parameter
discovery and retention (getPlantModelBuildParameterNames(), getPlantBuildParameters()), the grapevine
cluster and sorghum tiller/panicle build parameters, season-peak light exposure, setPlantBasePosition()
moving a built plant, and the petiole-less leaves of the library grasses.
"""

import pytest

from pyhelios import Context, PlantArchitecture, PlantArchitectureError
from pyhelios.types import vec3
from pyhelios.wrappers import UPlantArchitectureWrapper as plantarch_wrapper

from tests.test_plantarchitecture_phytomer import _require_plantarch


@pytest.mark.cross_platform
class TestPlantArch1393Validation:

    def _pa(self):
        plantarch = PlantArchitecture.__new__(PlantArchitecture)
        plantarch._plantarch_ptr = None
        plantarch.context = None
        return plantarch

    @pytest.mark.parametrize("bad", ["", "   ", None, 3])
    def test_model_name_must_be_a_non_empty_string(self, bad):
        with pytest.raises(ValueError, match="non-empty string"):
            self._pa().getPlantModelBuildParameterNames(bad)

    def test_season_peak_exposure_requires_a_vec3(self):
        with pytest.raises(ValueError, match="vec3"):
            self._pa().getSeasonPeakLightExposureAtPoint(0, (0.0, 0.0, 1.0))

    @pytest.mark.parametrize("call", [
        lambda: plantarch_wrapper.getSeasonPeakLightExposureAtPoint(None, 0, (0, 0, 0)),
        lambda: plantarch_wrapper.getPlantModelBuildParameterNames(None, "sorghum"),
        lambda: plantarch_wrapper.getPlantBuildParameters(None, 0),
    ])
    def test_wrappers_require_a_1393_library(self, call, monkeypatch):
        """An older native library raises instead of calling a symbol with no argtypes set."""
        monkeypatch.setattr(plantarch_wrapper, "_PLANTARCHITECTURE_1393_AVAILABLE", False)
        with pytest.raises(RuntimeError, match="1.3.93"):
            call()


@pytest.mark.native_only
class TestBuildParameterDiscovery:

    def test_grapevine_models_accept_cluster_parameters(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            for model in ("grapevine_VSP", "grapevine_Wye"):
                names = plantarch.getPlantModelBuildParameterNames(model)
                assert {"trunk_height", "vine_spacing", "berry_diameter", "cluster_berry_count"} <= set(names)

    def test_sorghum_accepts_tiller_and_panicle_parameters(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            names = plantarch.getPlantModelBuildParameterNames("sorghum")
            assert {"tiller_count", "panicle_type", "grain_count", "grain_color_r", "glume_color_b"} <= set(names)
            assert len(names) == len(set(names))

    def test_model_without_parameters_returns_empty_list(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            assert plantarch.getPlantModelBuildParameterNames("bean") == []

    def test_every_library_model_can_be_queried_without_loading(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            for model in plantarch.getAvailablePlantModels():
                assert isinstance(plantarch.getPlantModelBuildParameterNames(model), list)

    def test_unknown_model_raises(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            with pytest.raises(PlantArchitectureError, match="not_a_model"):
                plantarch.getPlantModelBuildParameterNames("not_a_model")


@pytest.mark.native_only
class TestOrganBuildParameters:
    """Organ build parameters (grape clusters, sorghum tillers and panicles) are accepted and kept."""

    def test_sorghum_tillers_and_panicle_type_are_accepted_and_kept(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("sorghum")
            params = {"tiller_count": 2, "panicle_type": 1.0, "grain_count": 800}
            plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 10.0, build_parameters=params)
            assert plantarch.getPlantBuildParameters(plant_id) == pytest.approx(
                {k: float(v) for k, v in params.items()})

    def test_grapevine_cluster_parameters_are_accepted(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("grapevine_VSP")
            plant_id = plantarch.buildPlantInstanceFromLibrary(
                vec3(0, 0, 0), 0.0, build_parameters={"berry_diameter": 0.018, "cluster_berry_count": 120})
            assert plantarch.getPlantBuildParameters(plant_id) == pytest.approx(
                {"berry_diameter": 0.018, "cluster_berry_count": 120.0})

    def test_sorghum_tillers_add_shoots(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("sorghum")
            plain = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 60.0)
            tillered = plantarch.buildPlantInstanceFromLibrary(
                vec3(1, 0, 0), 60.0, build_parameters={"tiller_count": 3})
            assert len(plantarch.getAllShootIDs(tillered)) > len(plantarch.getAllShootIDs(plain))

    def test_fractional_count_parameter_raises(self):
        """Counting parameters must be whole numbers; 3.9 scaffolds used to be truncated to 3."""
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("almond")
            with pytest.raises(PlantArchitectureError, match="num_scaffolds"):
                plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 0.0, build_parameters={"num_scaffolds": 3.9})

    def test_nan_parameter_raises(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("grapevine_VSP")
            with pytest.raises(PlantArchitectureError, match="trunk_height"):
                plantarch.buildPlantInstanceFromLibrary(
                    vec3(0, 0, 0), 0.0, build_parameters={"trunk_height": float("nan")})

    def test_misspelled_organ_parameter_is_rejected(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("sorghum")
            with pytest.raises(ValueError, match="tiler_count"):
                plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 0.0, build_parameters={"tiler_count": 1})


@pytest.mark.native_only
class TestPlantBuildParameters:

    def test_plant_built_without_parameters_has_none(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("bean")
            plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 5.0)
            assert plantarch.getPlantBuildParameters(plant_id) == {}

    def test_canopy_plants_keep_their_parameters(self):
        _require_plantarch()
        from pyhelios.types import vec2, int2
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("pistachio")
            plant_ids = plantarch.buildPlantCanopyFromLibrary(
                canopy_center=vec3(0, 0, 0), plant_spacing=vec2(6.0, 6.0), plant_count=int2(2, 1),
                age=0.0, build_parameters={"num_scaffolds": 4})
            for plant_id in plant_ids:
                assert plantarch.getPlantBuildParameters(plant_id) == {"num_scaffolds": 4.0}

    def test_parameters_round_trip_through_xml(self, tmp_path):
        _require_plantarch()
        path = tmp_path / "sorghum.xml"
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("sorghum")
            plant_id = plantarch.buildPlantInstanceFromLibrary(
                vec3(0, 0, 0), 10.0, build_parameters={"tiller_count": 2, "panicle_type": 0.0})
            plantarch.writePlantStructureXML(plant_id, path)
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("sorghum")
            (reloaded,) = plantarch.readPlantStructureXML(path, quiet=True)
            assert plantarch.getPlantBuildParameters(reloaded) == {"tiller_count": 2.0, "panicle_type": 0.0}

    def test_nonexistent_plant_raises(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            with pytest.raises(PlantArchitectureError, match="does not exist"):
                plantarch.getPlantBuildParameters(99)


@pytest.mark.native_only
class TestSeasonPeakLightExposure:

    def test_reports_past_summer_shade_through_dormancy(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("apple")
            plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 0.0)
            assert plantarch.getSeasonPeakLightExposureAtPoint(plant_id, vec3(0, 0, 1)) == 1.0

            # Grow into the first summer and find the most shaded point of the canopy.
            plantarch.advanceTime(240.0, plant_id=plant_id)
            assert plantarch.getPlantLeafObjectIDs(plant_id)
            points = [vec3(x, y, z) for x in (-0.2, 0.0, 0.2) for y in (-0.2, 0.0, 0.2)
                      for z in (0.6, 0.8, 1.0, 1.2, 1.4)]
            summer = {i: plantarch.getShadowLightExposureAtPoint(plant_id, p) for i, p in enumerate(points)}
            shaded = min(summer, key=summer.get)
            assert summer[shaded] < 1.0

            # Through leaf fall into dormancy: the current canopy casts no shade, the season peak still does.
            plantarch.advanceTime(150.0, plant_id=plant_id)
            assert plantarch.determinePhenologyStage(plant_id) == "dormant"
            assert plantarch.getShadowLightExposureAtPoint(plant_id, points[shaded]) == 1.0
            peak = plantarch.getSeasonPeakLightExposureAtPoint(plant_id, points[shaded])
            # The grid is captured at the plant's leaf-area peak, which need not be the day sampled above.
            assert 0.0 <= peak < 1.0
            assert peak == pytest.approx(summer[shaded], abs=0.05)

    def test_nonexistent_plant_raises(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            with pytest.raises(PlantArchitectureError, match="does not exist"):
                plantarch.getSeasonPeakLightExposureAtPoint(99, vec3(0, 0, 0))


@pytest.mark.native_only
class TestPlantBasePosition1393:

    def test_set_base_position_moves_a_built_plant(self):
        """Before 1.3.93 only the reported position changed and the geometry stayed put."""
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("bean")
            plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 20.0)
            uuid = plantarch.getAllPlantUUIDs(plant_id)[0]
            before = context.getPrimitiveVertices(uuid)[0]

            plantarch.setPlantBasePosition(plant_id, vec3(1.0, 2.0, 0.5))

            after = context.getPrimitiveVertices(uuid)[0]
            assert (after.x - before.x, after.y - before.y, after.z - before.z) == pytest.approx((1.0, 2.0, 0.5), abs=1e-5)
            base = plantarch.getPlantBasePosition(plant_id)
            assert (base.x, base.y, base.z) == pytest.approx((1.0, 2.0, 0.5))

            # Growth continues from the moved position.
            plantarch.advanceTime(5.0, plant_id=plant_id)
            for u in plantarch.getAllPlantUUIDs(plant_id):
                for v in context.getPrimitiveVertices(u):
                    assert v.x > 0.5 and v.y > 1.5

    def test_base_position_of_plant_without_shoots(self):
        """Raised before 1.3.93; now returns the position the first shoot will be placed at."""
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plant_id = plantarch.addPlantInstance(vec3(1.0, 2.0, 3.0), 0.0)
            base = plantarch.getPlantBasePosition(plant_id)
            assert (base.x, base.y, base.z) == pytest.approx((1.0, 2.0, 3.0))


@pytest.mark.native_only
class TestSessileGrassLeaves:

    @pytest.mark.parametrize("model", ["maize", "rice", "sorghum", "wheat"])
    def test_library_grasses_have_no_petiole(self, model):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary(model)
            shoot = plantarch.getCurrentShootParameters(plantarch.listShootTypeLabels()[0], return_typed=True)
            petiole_length = shoot.phytomer_parameters.petiole.length
            assert petiole_length.distribution == "constant" and petiole_length.parameters == [0.0]
            plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 30.0)
            assert plantarch.getPlantLeafObjectIDs(plant_id)
