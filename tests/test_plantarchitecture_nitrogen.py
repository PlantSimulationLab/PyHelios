"""
Tests for the PlantArchitecture nitrogen model controls: enabling the model, initializing pools and
applying nitrogen, and the leaf and plant nitrogen object data advanceTime() then writes.
"""

import math
from unittest.mock import patch

import pytest

from pyhelios import Context, PlantArchitecture, PlantArchitectureError
from pyhelios.types import vec3
from pyhelios.wrappers import UPlantArchitectureWrapper as plantarch_wrapper
from pyhelios.plugins.registry import get_plugin_registry


def _require_plantarch():
    if not get_plugin_registry().is_plugin_available('plantarchitecture'):
        pytest.skip("PlantArchitecture plugin not available")
    if not plantarch_wrapper._PLANTARCHITECTURE_NITROGEN_MODEL_AVAILABLE:
        pytest.skip("native library predates the nitrogen model controls")


def _unbound():
    """A PlantArchitecture with no native object: argument validation must refuse before using it."""
    return PlantArchitecture.__new__(PlantArchitecture)


@pytest.mark.cross_platform
class TestNitrogenArgumentValidation:

    @pytest.mark.parametrize("amount", ["1.0", None, True, [1.0]])
    def test_addPlantNitrogen_rejects_a_non_number(self, amount):
        with pytest.raises(ValueError, match="amount_gN must be a number"):
            PlantArchitecture.addPlantNitrogen(_unbound(), 0, amount)

    @pytest.mark.parametrize("amount", [-0.1, math.nan, math.inf])
    def test_addPlantNitrogen_rejects_a_negative_or_non_finite_amount(self, amount):
        with pytest.raises(ValueError, match="finite number >= 0"):
            PlantArchitecture.addPlantNitrogen(_unbound(), 0, amount)

    def test_addPlantNitrogen_rejects_bad_plant_ids(self):
        with pytest.raises(ValueError, match="(?i)plant id"):
            PlantArchitecture.addPlantNitrogen(_unbound(), -1, 1.0)
        with pytest.raises(ValueError, match="(?i)plant id"):
            PlantArchitecture.addPlantNitrogen(_unbound(), [0, -2], 1.0)
        with pytest.raises(ValueError, match="(?i)must not be empty"):
            PlantArchitecture.addPlantNitrogen(_unbound(), [], 1.0)
        with pytest.raises(ValueError, match="(?i)plant id"):
            PlantArchitecture.addPlantNitrogen(_unbound(), True, 1.0)

    def test_addPlantNitrogen_validates_keyword_arguments(self):
        with pytest.raises(ValueError, match="amount_gN"):
            PlantArchitecture.addPlantNitrogen(_unbound(), plant_id=0, amount_gN="2")

    @pytest.mark.parametrize("value", [-1.0, math.nan, "1.5"])
    def test_initializers_reject_a_bad_leaf_N(self, value):
        with pytest.raises(ValueError, match="initial_leaf_N_area"):
            PlantArchitecture.initializeNitrogenPools(_unbound(), value)
        with pytest.raises(ValueError, match="initial_leaf_N_area"):
            PlantArchitecture.initializePlantNitrogenPools(_unbound(), 0, value)

    def test_initializePlantNitrogenPools_rejects_a_bad_plant_id(self):
        with pytest.raises(ValueError, match="(?i)plant id"):
            PlantArchitecture.initializePlantNitrogenPools(_unbound(), -3, 1.5)

    def test_guard_names_the_missing_bindings(self):
        with patch.object(plantarch_wrapper, '_PLANTARCHITECTURE_NITROGEN_MODEL_AVAILABLE', False):
            for call in (lambda: plantarch_wrapper.enableNitrogenModel(None),
                         lambda: plantarch_wrapper.isNitrogenModelEnabled(None),
                         lambda: plantarch_wrapper.initializeNitrogenPools(None, 1.5),
                         lambda: plantarch_wrapper.addPlantNitrogen(None, 0, 1.0),
                         lambda: plantarch_wrapper.addPlantsNitrogen(None, [0], 1.0)):
                with pytest.raises(RuntimeError, match="nitrogen model controls"):
                    call()

    def test_expected_symbols_are_registered(self):
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture native functions not available")
        for name in ("enableNitrogenModel", "disableNitrogenModel", "isNitrogenModelEnabled",
                     "initializeNitrogenPools", "initializePlantNitrogenPools", "addPlantNitrogen",
                     "addPlantsNitrogen"):
            assert hasattr(plantarch_wrapper.helios_lib, name), f"native library is missing {name}"


@pytest.mark.native_only
class TestNitrogenModelNative:

    def _bean(self, plantarch, age=10.0, x=0.0):
        plantarch.loadPlantModelFromLibrary("bean")
        return plantarch.buildPlantInstanceFromLibrary(vec3(x, 0, 0), age)

    def test_enable_and_disable_round_trip(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            assert plantarch.isNitrogenModelEnabled() is False
            plantarch.enableNitrogenModel()
            assert plantarch.isNitrogenModelEnabled() is True
            plantarch.disableNitrogenModel()
            assert plantarch.isNitrogenModelEnabled() is False

    def test_added_nitrogen_is_split_by_the_root_allocation_fraction(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plant = self._bean(plantarch)
            plantarch.enableNitrogenModel()
            plantarch.initializePlantNitrogenPools(plant, 1.5)
            root_fraction = plantarch.getDefaultNitrogenParameters()["root_allocation_fraction"]
            plantarch.addPlantNitrogen(plant, 2.0)
            assert plantarch.getPlantAvailableNitrogen(plant) == pytest.approx(2.0 * (1 - root_fraction), rel=1e-6)

    def test_a_list_adds_the_amount_to_each_plant(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plants = [self._bean(plantarch, x=float(i)) for i in range(3)]
            plantarch.enableNitrogenModel()
            plantarch.initializeNitrogenPools(1.5)
            plantarch.addPlantNitrogen(plants, 1.0)
            pools = [plantarch.getPlantAvailableNitrogen(p) for p in plants]
            assert pools[0] > 0 and pools == pytest.approx([pools[0]] * 3)

    def test_a_missing_plant_raises(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.enableNitrogenModel()
            with pytest.raises(PlantArchitectureError, match="(?i)does not exist"):
                plantarch.addPlantNitrogen(12345, 1.0)
            with pytest.raises(PlantArchitectureError, match="(?i)does not exist"):
                plantarch.initializePlantNitrogenPools(12345, 1.5)

    def test_advanceTime_writes_leaf_and_plant_nitrogen_only_when_enabled(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plant = self._bean(plantarch)
            plantarch.advanceTime(1.0)
            leaves = plantarch.getPlantLeafObjectIDs(plant)
            assert leaves
            assert not context.doesObjectDataExist(leaves[0], "leaf_nitrogen_gN_m2")

            plantarch.enableNitrogenModel()
            plantarch.initializePlantNitrogenPools(plant, 1.2)
            plantarch.advanceTime(1.0)
            leaves = plantarch.getPlantLeafObjectIDs(plant)
            values = [context.getObjectDataFloat(o, "leaf_nitrogen_gN_m2") for o in leaves
                      if context.doesObjectDataExist(o, "leaf_nitrogen_gN_m2")]
            assert values, "no leaf carries leaf_nitrogen_gN_m2 after advanceTime()"
            assert all(0.0 <= v <= 1.2 + 1e-6 for v in values)
            stress = context.getObjectDataFloat(leaves[0], "nitrogen_stress_factor")
            assert 0.0 <= stress <= 1.0

    def test_a_starved_plant_ends_more_stressed_than_a_fed_one(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            fed, starved = self._bean(plantarch, x=0.0), self._bean(plantarch, x=2.0)
            plantarch.enableNitrogenModel()
            plantarch.initializeNitrogenPools(1.5)
            plantarch.addPlantNitrogen(fed, 5.0)
            plantarch.advanceTime(20.0)

            def stress(plant):
                leaf = plantarch.getPlantLeafObjectIDs(plant)[0]
                return context.getObjectDataFloat(leaf, "nitrogen_stress_factor")

            assert stress(fed) > stress(starved) + 0.05
