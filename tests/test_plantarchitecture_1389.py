"""
Tests for the helios-core 1.3.89 PlantArchitecture additions: leaf blade area, shadow-grid light
exposure, PhytomerParameters::resample(), the LeafPrototype petiolule length, the shoot tortuosity
persistence length, and the almond_independence library model.
"""

import copy
from unittest.mock import patch

import pytest

from pyhelios import Context, PlantArchitecture, PlantArchitectureError
from pyhelios.PlantArchitecture import _validate_build_parameters
from pyhelios.types import vec3, RGBcolor
from pyhelios.wrappers import UPlantArchitectureWrapper as plantarch_wrapper
from pyhelios.plugins.registry import get_plugin_registry
from pyhelios.plant_architecture_params import (
    LeafPrototype,
    PhytomerParameters,
    RandomParameterFloat,
    ShootParameters,
)


def _require_plantarch():
    if not get_plugin_registry().is_plugin_available('plantarchitecture'):
        pytest.skip("PlantArchitecture plugin not available")


@pytest.mark.cross_platform
class TestPlantArch1389Validation:
    """Argument validation and typed-parameter fields (no native library needed)."""

    def _pa(self):
        return PlantArchitecture.__new__(PlantArchitecture)

    def test_1389_guard(self):
        with patch.object(plantarch_wrapper, '_PLANTARCHITECTURE_1389_AVAILABLE', False):
            with pytest.raises(RuntimeError, match="1.3.89"):
                plantarch_wrapper.getLeafBladeArea(None, 0)
            with pytest.raises(RuntimeError, match="1.3.89"):
                plantarch_wrapper.getShadowLightExposureAtPoint(None, 0, (0, 0, 0))
            with pytest.raises(RuntimeError, match="1.3.89"):
                plantarch_wrapper.resamplePhytomerParameters(None, {})

    @pytest.mark.parametrize("bad", [-1, True, 1.5, "3"])
    def test_getLeafBladeArea_rejects_bad_object_id(self, bad):
        with pytest.raises(ValueError, match="(?i)leaf object id"):
            PlantArchitecture.getLeafBladeArea(self._pa(), bad)

    def test_getShadowLightExposureAtPoint_rejects_non_vec3(self):
        with pytest.raises(ValueError, match="vec3"):
            PlantArchitecture.getShadowLightExposureAtPoint(self._pa(), 0, RGBcolor(1, 0, 0))
        with pytest.raises(ValueError, match="vec3"):
            PlantArchitecture.getShadowLightExposureAtPoint(self._pa(), plant_id=0, position=[0, 0, 1])

    def test_getShadowLightExposureAtPoint_rejects_bad_plant_id(self):
        with pytest.raises(ValueError, match="(?i)plant id"):
            PlantArchitecture.getShadowLightExposureAtPoint(self._pa(), -1, vec3(0, 0, 1))

    def test_resamplePhytomerParameters_rejects_wrong_type(self):
        with pytest.raises(ValueError, match="PhytomerParameters"):
            PlantArchitecture.resamplePhytomerParameters(self._pa(), ShootParameters())

    def test_petiolule_length_field_round_trips(self):
        assert LeafPrototype().petiolule_length == {0: 0.05}
        proto = LeafPrototype(build_petiolule=True, petiolule_length={0: 0.02, -1: 0.03, 1: 0.03})
        d = proto.to_dict()
        assert d["petiolule_length"] == {"0": 0.02, "-1": 0.03, "1": 0.03}
        assert LeafPrototype.from_dict(d).petiolule_length == {0: 0.02, -1: 0.03, 1: 0.03}

    def test_tortuosity_persistence_length_field_round_trips(self):
        sp = ShootParameters()
        assert sp.tortuosity_persistence_length == RandomParameterFloat.constant(0.5)
        sp.tortuosity_persistence_length = RandomParameterFloat.uniform(0.2, 0.4)
        d = sp.to_dict()
        assert d["tortuosity_persistence_length"] == {"distribution": "uniform", "parameters": [0.2, 0.4]}
        assert ShootParameters.from_dict(d).tortuosity_persistence_length == RandomParameterFloat.uniform(0.2, 0.4)

    def test_almond_independence_accepts_scaffold_build_parameters(self):
        _validate_build_parameters({"trunk_height": 0.8, "num_scaffolds": 4, "scaffold_angle": 50},
                                   "almond_independence")

    @pytest.mark.parametrize("model", ["almond_aldrich", "almond_wood_colony"])
    def test_models_that_read_no_build_parameters_reject_them(self, model):
        """These builders never call getParameterValue(), so a trunk_height would be silently ignored."""
        with pytest.raises(ValueError, match="accepts no build parameters"):
            _validate_build_parameters({"trunk_height": 0.8}, model)


@pytest.mark.native_only
class TestPlantArch1389Native:

    def test_expected_1389_symbols_are_registered(self):
        _require_plantarch()
        for name in ("getLeafBladeArea", "getShadowLightExposureAtPoint", "resamplePhytomerParametersJSON"):
            assert hasattr(plantarch_wrapper.helios_lib, name), f"native library is missing {name}"

    def test_almond_independence_is_a_library_model(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            assert "almond_independence" in plantarch.getAvailablePlantModels()

    def test_leaf_blade_area_excludes_petiolules(self):
        """Bean leaflets carry petiolules: blade area sums to the plant leaf area and is below the object area."""
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("bean")
            plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 25.0)
            leaf_ids = plantarch.getPlantLeafObjectIDs(plant_id)
            assert leaf_ids
            blade = [plantarch.getLeafBladeArea(obj) for obj in leaf_ids]
            assert all(a > 0 for a in blade)
            assert sum(blade) == pytest.approx(plantarch.getPlantLeafArea(plant_id), rel=1e-4)
            object_area = [context.getObjectArea(obj) for obj in leaf_ids]
            assert all(a <= o * (1 + 1e-6) for a, o in zip(blade, object_area))
            assert any(a < o * (1 - 1e-4) for a, o in zip(blade, object_area)), \
                "no bean leaf carried a petiolule, so blade and object area never differed"

    def test_leaf_blade_area_missing_object_raises(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            with pytest.raises(PlantArchitectureError, match="(?i)does not exist"):
                plantarch.getLeafBladeArea(987654)

    def test_shadow_light_exposure_is_bounded(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("bean")
            plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 25.0)
            for z in (0.0, 0.1, 0.3, 5.0):
                exposure = plantarch.getShadowLightExposureAtPoint(plant_id, vec3(0, 0, z))
                assert 0.0 <= exposure <= 1.0

    def test_shadow_light_exposure_missing_plant_raises(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            with pytest.raises(PlantArchitectureError, match="(?i)does not exist"):
                plantarch.getShadowLightExposureAtPoint(12345, vec3(0, 0, 0))

    def test_petiolule_length_reads_library_value_and_round_trips(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("bean")
            sp = plantarch.getCurrentShootParameters("trifoliate", return_typed=True)
            proto = sp.phytomer_parameters.leaf.prototype
            assert proto.build_petiolule
            assert proto.petiolule_length == {0: pytest.approx(0.02)}

            proto.petiolule_length = {0: 0.04, -1: 0.03, 1: 0.03}
            plantarch.defineShootType("trifoliate", sp)
            back = plantarch.getCurrentShootParameters("trifoliate", return_typed=True)
            assert back.phytomer_parameters.leaf.prototype.petiolule_length == {
                0: pytest.approx(0.04), -1: pytest.approx(0.03), 1: pytest.approx(0.03)}

    def test_tortuosity_persistence_length_round_trips(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("bean")
            params = plantarch.getCurrentShootParameters("trifoliate")
            assert params["tortuosity_persistence_length"]["distribution"] == "constant"
            params["tortuosity_persistence_length"] = {"distribution": "constant", "parameters": [1.25]}
            plantarch.defineShootType("trifoliate", params)
            back = plantarch.getCurrentShootParameters("trifoliate")
            assert back["tortuosity_persistence_length"]["parameters"] == [pytest.approx(1.25)]

    def test_resample_freezes_distributed_fields_and_keeps_constants(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            pp = PhytomerParameters()
            pp.leaf.pitch = RandomParameterFloat.uniform(40.0, 50.0)
            pp.petiole.length = RandomParameterFloat.normal(0.1, 0.01)
            pp.internode.pitch = RandomParameterFloat.constant(12.0)

            drawn = plantarch.resamplePhytomerParameters(pp)

            assert isinstance(drawn, PhytomerParameters)
            assert drawn.leaf.pitch.distribution == "constant"
            assert 40.0 <= drawn.leaf.pitch.parameters[0] <= 50.0
            assert drawn.petiole.length.distribution == "constant"
            assert drawn.internode.pitch == RandomParameterFloat.constant(12.0)
            # The input is not modified.
            assert pp.leaf.pitch == RandomParameterFloat.uniform(40.0, 50.0)

    def test_resample_follows_the_context_seed(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("bean")
            pp = copy.deepcopy(plantarch.getCurrentShootParameters("trifoliate")["phytomer_parameters"])
            pp["leaf"]["pitch"] = {"distribution": "uniform", "parameters": [0.0, 90.0]}

            context.seedRandomGenerator(7)
            first = plantarch.resamplePhytomerParameters(pp)
            second = plantarch.resamplePhytomerParameters(pp)
            context.seedRandomGenerator(7)
            repeat = plantarch.resamplePhytomerParameters(pp)

            assert isinstance(first, dict)
            assert first["leaf"]["pitch"] == repeat["leaf"]["pitch"]
            assert first["leaf"]["pitch"] != second["leaf"]["pitch"]
