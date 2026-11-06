"""
Tests for the helios-core 1.3.95 PlantArchitecture additions that reach the Python API: leaf texture
series and aging stages (LeafPrototype.leaf_texture_series / leaf_texture_stage_ages, the
"leaf_texture_stage" object data, set/getPlantMinimumLeafTextureStage(), generateLeafTextureStages()),
and the rice and maize build parameters.
"""

import os

import pytest

from pyhelios import Context, LeafTextureStageOptions, PlantArchitecture, PlantArchitectureError
from pyhelios.plant_architecture_params import LeafPrototype
from pyhelios.types import RGBcolor, vec3
from pyhelios.wrappers import UPlantArchitectureWrapper as plantarch_wrapper

from tests.test_plantarchitecture_phytomer import _require_plantarch


def _require_1395():
    _require_plantarch()
    if not plantarch_wrapper._PLANTARCHITECTURE_1395_AVAILABLE:
        pytest.skip("native library predates helios-core 1.3.95; rebuild required")


def _pa_without_native():
    plantarch = PlantArchitecture.__new__(PlantArchitecture)
    plantarch._plantarch_ptr = None
    plantarch.context = None
    return plantarch


# --------------------------------------------------------------------------- #
# Pure Python
# --------------------------------------------------------------------------- #
@pytest.mark.cross_platform
class TestLeafTextureSeriesDataclass:

    def test_series_and_ages_round_trip_through_dict(self):
        proto = LeafPrototype(leaf_texture_series={0: [["a0.png", "a1.png"], ["b0.png", "b1.png"]]},
                              leaf_texture_stage_ages=[0.0, 30.0])
        d = proto.to_dict()
        assert d["leaf_texture_series"] == {"0": [["a0.png", "a1.png"], ["b0.png", "b1.png"]]}
        assert d["leaf_texture_stage_ages"] == [0.0, 30.0]
        back = LeafPrototype.from_dict(d)
        assert back.leaf_texture_series == {0: [["a0.png", "a1.png"], ["b0.png", "b1.png"]]}
        assert back.leaf_texture_stage_ages == [0.0, 30.0]

    def test_defaults_are_empty_and_missing_keys_tolerated(self):
        assert LeafPrototype().to_dict()["leaf_texture_series"] == {}
        back = LeafPrototype.from_dict({})
        assert back.leaf_texture_series == {} and back.leaf_texture_stage_ages == []


@pytest.mark.cross_platform
class TestLeafTextureStageOptions:

    def test_defaults_mirror_native(self):
        d = LeafTextureStageOptions().to_dict()
        assert d["senescence_colors"] == [pytest.approx([0.76, 0.66, 0.18]), pytest.approx([0.36, 0.22, 0.10])]
        assert d["senesced_textures"] == [] and d["onset_map"] == ""
        assert d["patchiness"] == pytest.approx(0.3)
        assert d["transition_width"] == pytest.approx(0.25)
        assert d["noise_seed"] == 0

    @pytest.mark.parametrize("kwargs, match", [
        ({"senescence_colors": [vec3(1, 0, 0)]}, "RGBcolor"),
        ({"senescence_colors": [], "senesced_textures": []}, "nothing for the leaf"),
        ({"patchiness": 1.5}, "patchiness"),
        ({"transition_width": 0.0}, "transition_width"),
        ({"noise_seed": -1}, "noise_seed"),
        ({"senesced_textures": "a.png"}, "senesced_textures"),
    ])
    def test_validate_rejects_bad_fields(self, kwargs, match):
        with pytest.raises(ValueError, match=match):
            LeafTextureStageOptions(**kwargs).validate()

    @pytest.mark.parametrize("args, match", [
        (("AlmondLeaf.png", "out", 1), "at least 2"),
        (("AlmondLeaf.png", "out", 2.0), "must be an int"),
        (("", "out", 3), "leaf_texture"),
        (("AlmondLeaf.png", "", 3), "output_directory"),
    ])
    def test_generate_rejects_bad_arguments(self, args, match):
        with pytest.raises(ValueError, match=match):
            PlantArchitecture.generateLeafTextureStages(*args)

    def test_generate_rejects_wrong_options_type(self):
        with pytest.raises(ValueError, match="LeafTextureStageOptions"):
            PlantArchitecture.generateLeafTextureStages("AlmondLeaf.png", "out", 3, {"noise_seed": 1})
        with pytest.raises(ValueError, match="RGBcolor"):
            PlantArchitecture.generateLeafTextureStages(
                "AlmondLeaf.png", "out", 3, LeafTextureStageOptions(senescence_colors=[(1, 0, 0)]))


@pytest.mark.cross_platform
class TestMinimumLeafTextureStageValidation:

    @pytest.mark.parametrize("plant_id, stage", [(-1, 0), (0, -1), (0, 1.5), (True, 0), (0, 2 ** 32)])
    def test_set_rejects_bad_arguments(self, plant_id, stage):
        with pytest.raises(ValueError):
            _pa_without_native().setPlantMinimumLeafTextureStage(plant_id, stage)

    def test_get_rejects_negative_plant_id(self):
        with pytest.raises(ValueError, match="between 0 and"):
            _pa_without_native().getPlantMinimumLeafTextureStage(-1)

    @pytest.mark.parametrize("call", [
        lambda: plantarch_wrapper.setPlantMinimumLeafTextureStage(None, 0, 1),
        lambda: plantarch_wrapper.getPlantMinimumLeafTextureStage(None, 0),
        lambda: plantarch_wrapper.generateLeafTextureStages("AlmondLeaf.png", "out", 3, "{}"),
    ])
    def test_wrappers_require_a_1395_library(self, call, monkeypatch):
        monkeypatch.setattr(plantarch_wrapper, "_PLANTARCHITECTURE_1395_AVAILABLE", False)
        with pytest.raises(RuntimeError, match="1.3.95"):
            call()


# --------------------------------------------------------------------------- #
# Native
# --------------------------------------------------------------------------- #
@pytest.mark.native_only
class TestGenerateLeafTextureStagesNative:

    def test_writes_one_image_per_stage(self, tmp_path):
        _require_1395()
        files = PlantArchitecture.generateLeafTextureStages("TomatoLeaf_blade.png", tmp_path / "stages", 4)
        assert len(files) == 4
        assert all(os.path.isfile(f) for f in files)
        assert os.path.basename(files[0]) == "TomatoLeaf_blade.png"
        for f in files[1:]:
            assert os.path.dirname(os.path.realpath(f)) == os.path.realpath(tmp_path / "stages")
            assert f.endswith(".png")  # the leaf texture has transparency
        assert len(set(files)) == 4

    def test_relative_output_directory_is_the_callers(self, tmp_path, monkeypatch):
        _require_1395()
        monkeypatch.chdir(tmp_path)
        options = LeafTextureStageOptions(senescence_colors=[RGBcolor(0.8, 0.1, 0.1)], noise_seed=3)
        files = PlantArchitecture.generateLeafTextureStages("TomatoLeaf_blade.png", "relative_out", 2, options)
        assert len(files) == 2
        assert (tmp_path / "relative_out" / os.path.basename(files[1])).is_file()

    def test_missing_texture_raises(self, tmp_path):
        _require_1395()
        with pytest.raises(PlantArchitectureError, match="Could not resolve"):
            PlantArchitecture.generateLeafTextureStages("NoSuchLeaf_xyz.png", tmp_path, 3)

    def test_native_range_check_reaches_python(self, tmp_path):
        _require_1395()
        with pytest.raises(PlantArchitectureError, match="resolution"):
            PlantArchitecture.generateLeafTextureStages(
                "TomatoLeaf_blade.png", tmp_path, 3,
                LeafTextureStageOptions(senesced_textures=["AlmondLeaf.png"]))


@pytest.mark.native_only
class TestLeafTextureSeriesNative:

    def test_rice_library_series_round_trips(self):
        """The 1.3.95 rice model ships a two-variant, three-stage series; it must survive get/define/get."""
        _require_1395()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("rice")
            sp = plantarch.getCurrentShootParameters("mainstem", return_typed=True)
            proto = sp.phytomer_parameters.leaf.prototype
            assert len(proto.leaf_texture_series[0]) == 2
            assert all(len(variant) == 3 for variant in proto.leaf_texture_series[0])
            assert proto.leaf_texture_stage_ages == pytest.approx([0.0, 55.0, 72.0])

            proto.leaf_texture_series = {0: [["RiceLeaf_B_0.png", "RiceLeaf_B_1.png"]]}
            proto.leaf_texture_stage_ages = [0.0, 30.0]
            plantarch.defineShootType("rice_custom", sp)
            back = plantarch.getCurrentShootParameters("rice_custom", return_typed=True).phytomer_parameters.leaf.prototype
            assert back.leaf_texture_series == {0: [["RiceLeaf_B_0.png", "RiceLeaf_B_1.png"]]}
            assert back.leaf_texture_stage_ages == pytest.approx([0.0, 30.0])

    def test_leaf_texture_stage_object_data_and_minimum_stage(self, tmp_path):
        _require_1395()
        stages = PlantArchitecture.generateLeafTextureStages("TomatoLeaf_blade.png", tmp_path, 3)
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("rice")
            redefined = 0
            for label in plantarch.listShootTypeLabels():
                sp = plantarch.getCurrentShootParameters(label, return_typed=True)
                proto = sp.phytomer_parameters.leaf.prototype
                if not proto.leaf_texture_series:
                    continue
                proto.leaf_texture_series = {0: [stages]}
                proto.leaf_texture_stage_ages = [0.0, 1.0, 2.0]
                plantarch.defineShootType(label, sp)
                redefined += 1
            assert redefined, "rice has no shoot type with a leaf texture series"

            plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 12.0)
            leaves = plantarch.getPlantLeafObjectIDs(plant_id)
            assert leaves, "rice at age 12 has no leaves; assertions would be vacuous"
            assert not any(context.doesObjectDataExist(leaf, "leaf_texture_stage") for leaf in leaves)

            # Enabling the output writes it to leaves that already exist.
            plantarch.optionalOutputObjectData("leaf_texture_stage")
            values = [context.getObjectData(leaf, "leaf_texture_stage") for leaf in leaves]
            assert set(values) <= {0, 1, 2}
            assert max(values) == 2, f"no leaf of a 12-day rice plant reached stage 2: {sorted(set(values))}"

            assert plantarch.getPlantMinimumLeafTextureStage(plant_id) == 0
            plantarch.setPlantMinimumLeafTextureStage(plant_id, 2)
            assert plantarch.getPlantMinimumLeafTextureStage(plant_id) == 2
            assert {context.getObjectData(leaf, "leaf_texture_stage") for leaf in leaves} == {2}

    def test_minimum_stage_for_missing_plant_raises(self):
        _require_1395()
        with Context() as context, PlantArchitecture(context) as plantarch:
            with pytest.raises(PlantArchitectureError, match="does not exist"):
                plantarch.setPlantMinimumLeafTextureStage(9999, 1)
            with pytest.raises(PlantArchitectureError, match="does not exist"):
                plantarch.getPlantMinimumLeafTextureStage(9999)


@pytest.mark.native_only
class TestRiceAndMaizeBuildParameters:

    def test_rice_reports_and_accepts_build_parameters(self):
        _require_1395()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            names = set(plantarch.getPlantModelBuildParameterNames("rice"))
            assert {"tiller_count", "panicle_type", "panicle_length", "ripeness"} <= names
            plantarch.loadPlantModelFromLibrary("rice")
            plant_id = plantarch.buildPlantInstanceFromLibrary(
                vec3(0, 0, 0), 10.0, build_parameters={"tiller_count": 2, "panicle_type": 0.2})
            assert plantarch.getPlantBuildParameters(plant_id) == pytest.approx(
                {"tiller_count": 2.0, "panicle_type": 0.2})
            with pytest.raises(PlantArchitectureError, match="tiller_count"):
                plantarch.buildPlantInstanceFromLibrary(vec3(1, 0, 0), 10.0, build_parameters={"tiller_count": 1.5})

    def test_maize_reports_and_accepts_build_parameters(self):
        _require_1395()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            names = set(plantarch.getPlantModelBuildParameterNames("maize"))
            assert {"tassel_type", "tassel_length", "tassel_branch_count", "anther_fraction"} <= names
            assert "tiller_count" not in names
            plantarch.loadPlantModelFromLibrary("maize")
            plant_id = plantarch.buildPlantInstanceFromLibrary(
                vec3(0, 0, 0), 10.0, build_parameters={"tassel_type": 0.0})
            assert plantarch.getPlantBuildParameters(plant_id) == pytest.approx({"tassel_type": 0.0})
            with pytest.raises(ValueError, match="Unknown build parameter"):
                plantarch.buildPlantInstanceFromLibrary(vec3(1, 0, 0), 10.0, build_parameters={"trunk_height": 1.0})
