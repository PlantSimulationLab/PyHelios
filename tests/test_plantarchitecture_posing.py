"""
Tests for posing a finished plant: PlantArchitecture.setLeafAngleDistribution() and the
per-phytomer petiole flexibility accessors.
"""

from unittest.mock import patch

import numpy as np
import pytest

from pyhelios import Context, PlantArchitecture, PlantArchitectureError
from pyhelios.types import vec3
from pyhelios.wrappers import UPlantArchitectureWrapper as plantarch_wrapper
from pyhelios.plugins.registry import get_plugin_registry


def _require_plantarch():
    if not get_plugin_registry().is_plugin_available('plantarchitecture'):
        pytest.skip("PlantArchitecture plugin not available")


@pytest.mark.cross_platform
class TestPosingValidation:
    """Argument validation (no native library needed)."""

    def _pa(self):
        return PlantArchitecture.__new__(PlantArchitecture)

    @pytest.mark.parametrize("bad", [-1, True, 1.5, "0", None])
    def test_setLeafAngleDistribution_rejects_bad_plant_id(self, bad):
        with pytest.raises(ValueError):
            PlantArchitecture.setLeafAngleDistribution(self._pa(), bad, 2.0, 1.5)

    def test_setLeafAngleDistribution_rejects_empty_list(self):
        with pytest.raises(ValueError, match="(?i)must not be empty"):
            PlantArchitecture.setLeafAngleDistribution(self._pa(), [], 2.0, 1.5)

    @pytest.mark.parametrize("mu,nu", [(0.0, 1.5), (2.0, 0.0), (-1.0, 1.5), (2.0, -1.0),
                                       (float("nan"), 1.5), (2.0, float("inf")), ("2", 1.5), (True, 1.5)])
    def test_setLeafAngleDistribution_rejects_bad_beta_parameters(self, mu, nu):
        with pytest.raises(ValueError, match="(?i)beta_(mu|nu)_inclination"):
            PlantArchitecture.setLeafAngleDistribution(self._pa(), 0, mu, nu)

    @pytest.mark.parametrize("bad", [-0.1, 1.1, float("nan")])
    def test_setLeafAngleDistribution_rejects_bad_eccentricity(self, bad):
        with pytest.raises(ValueError, match="(?i)eccentricity"):
            PlantArchitecture.setLeafAngleDistribution(self._pa(), 0, 2.0, 1.5, eccentricity=bad)

    @pytest.mark.parametrize("ids", [(-1, 0, 0), (0, -1, 0), (0, 0, -1), (True, 0, 0), (0, 0, 1.5)])
    def test_petiole_flexibility_rejects_bad_identifiers(self, ids):
        with pytest.raises(ValueError):
            PlantArchitecture.getPetioleFlexibility(self._pa(), *ids)
        with pytest.raises(ValueError):
            PlantArchitecture.setPetioleFlexibility(self._pa(), *ids, 1.0)

    @pytest.mark.parametrize("bad", [-0.1, float("nan"), float("inf"), "1.0", True, None])
    def test_setPetioleFlexibility_rejects_bad_flexibility(self, bad):
        with pytest.raises(ValueError, match="(?i)flexibility"):
            PlantArchitecture.setPetioleFlexibility(self._pa(), 0, 0, 0, bad)

    @pytest.mark.parametrize("bad", [1, "yes", None])
    def test_bendPetioleUnderLeafWeight_rejects_non_bool_include_posed_leaves(self, bad):
        with pytest.raises(ValueError, match="(?i)include_posed_leaves"):
            PlantArchitecture.bendPetioleUnderLeafWeight(self._pa(), 0, 0, 0, 0, include_posed_leaves=bad)

    def test_wrappers_guard_with_the_posing_flag(self):
        """A wrapper checking the wrong flag would call a function with no argtypes set."""
        with patch.object(plantarch_wrapper, '_PLANTARCHITECTURE_POSING_AVAILABLE', False):
            with pytest.raises(RuntimeError, match="(?i)rebuild"):
                plantarch_wrapper.setPlantLeafAngleDistribution(None, [0], 2.0, 1.5)
            with pytest.raises(RuntimeError, match="(?i)rebuild"):
                plantarch_wrapper.bendPetioleWithPosedLeavesUnderLeafWeight(None, 0, 0, 0, 0)
            with pytest.raises(RuntimeError, match="(?i)rebuild"):
                plantarch_wrapper.getPetioleFlexibility(None, 0, 0, 0)
            with pytest.raises(RuntimeError, match="(?i)rebuild"):
                plantarch_wrapper.setPetioleFlexibility(None, 0, 0, 0, 1.0)

    def test_expected_symbols_are_registered(self):
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture native functions not available")
        for name in ("setPlantLeafAngleDistribution", "bendPetioleWithPosedLeavesUnderLeafWeight",
                     "getPetioleFlexibility", "setPetioleFlexibility"):
            assert hasattr(plantarch_wrapper.helios_lib, name), f"native library is missing {name}"
        assert plantarch_wrapper._PLANTARCHITECTURE_POSING_AVAILABLE


@pytest.fixture
def tomato():
    """A context, plant architecture and library tomato plant with fully expanded lower leaves."""
    _require_plantarch()
    with Context() as context:
        context.seedRandomGenerator(7)
        with PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("tomato")
            plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 30.0)
            yield context, plantarch, plant_id


def _leafy_node(plantarch, plant_id):
    """Index of a main-stem phytomer that carries leaves."""
    for node in range(plantarch.getShoot(plant_id, 0)["node_count"]):
        petioles = plantarch.getPhytomerLeafObjectIDs(plant_id, 0, node)
        if petioles and petioles[0]:
            return node
    pytest.fail("the tomato plant has no leaves on its main stem")


def _mean_leaf_height(context, plantarch, plant_id, node):
    ids = [oid for petiole in plantarch.getPhytomerLeafObjectIDs(plant_id, 0, node) for oid in petiole]
    return float(np.mean([context.getObjectCenter(oid).z for oid in ids]))


@pytest.mark.native_only
class TestSetLeafAngleDistribution:

    def test_mean_inclination_follows_the_beta_parameters(self, tomato):
        """Mean inclination from horizontal is 90 * nu / (mu + nu) degrees."""
        _, plantarch, plant_id = tomato
        count = len(plantarch.getPlantLeafInclinations(plant_id))

        plantarch.setLeafAngleDistribution(plant_id, 4.0, 1.0)
        flat = plantarch.getPlantLeafInclinations(plant_id)
        plantarch.setLeafAngleDistribution(plant_id, 1.0, 4.0)
        steep = plantarch.getPlantLeafInclinations(plant_id)

        assert len(flat) == len(steep) == count
        assert np.mean(flat) < 30.0 < 60.0 < np.mean(steep), (
            f"mean inclination {np.mean(flat):.1f} deg (expected ~18) and {np.mean(steep):.1f} deg (expected ~72)")

    def test_azimuth_is_kept_unless_eccentricity_is_given(self, tomato):
        context, plantarch, plant_id = tomato

        def azimuths():
            out = []
            for oid in plantarch.getPlantLeafObjectIDs(plant_id):
                n = np.sum([np.array(context.getPrimitiveNormal(u).to_list()) * context.getPrimitiveArea(u)
                            for u in context.getObjectPrimitiveUUIDs(oid)], axis=0)
                if n[2] < 0:
                    n = -n
                out.append(np.arctan2(n[1], n[0]))
            return np.array(out)

        def circular_shift(a, b):
            return np.abs(np.angle(np.exp(1j * (a - b))))

        # Start from steep leaves so that the azimuth of every normal is well defined.
        plantarch.setLeafAngleDistribution(plant_id, 1.0, 4.0)
        start = azimuths()
        plantarch.setLeafAngleDistribution(plant_id, 1.5, 3.0)
        kept = circular_shift(azimuths(), start)
        plantarch.setLeafAngleDistribution(plant_id, 1.5, 3.0, eccentricity=0.95, ellipse_rotation_degrees=0.0)
        moved = circular_shift(azimuths(), start)

        assert np.median(kept) < np.radians(5.0), f"median azimuth shift {np.degrees(np.median(kept)):.1f} deg"
        assert np.median(moved) > 3.0 * max(np.median(kept), np.radians(1.0))

    def test_accepts_a_list_of_plants(self, tomato):
        _, plantarch, plant_id = tomato
        other = plantarch.buildPlantInstanceFromLibrary(vec3(1, 0, 0), 30.0)
        plantarch.setLeafAngleDistribution([plant_id, other], 1.0, 4.0)
        pooled = plantarch.getPlantLeafInclinations(plant_id) + plantarch.getPlantLeafInclinations(other)
        assert np.mean(pooled) > 60.0

    def test_missing_plant_raises(self, tomato):
        _, plantarch, _ = tomato
        with pytest.raises(PlantArchitectureError, match="(?i)does not exist"):
            plantarch.setLeafAngleDistribution(9999, 2.0, 1.5)


@pytest.mark.native_only
class TestPetioleFlexibility:

    def test_library_tomato_petioles_are_rigid(self, tomato):
        _, plantarch, plant_id = tomato
        assert plantarch.getPetioleFlexibility(plant_id, 0, _leafy_node(plantarch, plant_id)) == 0.0

    def test_set_then_get_round_trips(self, tomato):
        _, plantarch, plant_id = tomato
        node = _leafy_node(plantarch, plant_id)
        plantarch.setPetioleFlexibility(plant_id, 0, node, 1.75)
        assert plantarch.getPetioleFlexibility(plant_id, 0, node) == pytest.approx(1.75)

    def test_raised_flexibility_droops_the_leaves_and_is_reversible(self, tomato):
        context, plantarch, plant_id = tomato
        node = _leafy_node(plantarch, plant_id)
        rest = _mean_leaf_height(context, plantarch, plant_id, node)
        length = plantarch.getPetioleLength(plant_id, 0, node, 0)

        plantarch.setPetioleFlexibility(plant_id, 0, node, 3.0)
        assert _mean_leaf_height(context, plantarch, plant_id, node) == pytest.approx(rest, abs=1e-6), (
            "setting the flexibility must not move geometry by itself")
        plantarch.bendPetioleUnderLeafWeight(plant_id, 0, node, 0)
        drooped = _mean_leaf_height(context, plantarch, plant_id, node)
        assert drooped < rest - 0.005, f"leaves did not droop: {rest:.4f} -> {drooped:.4f} m"
        # Bending is inextensible.
        assert plantarch.getPetioleLength(plant_id, 0, node, 0) == pytest.approx(length, rel=1e-4)

        plantarch.setPetioleFlexibility(plant_id, 0, node, 1e-4)
        plantarch.bendPetioleUnderLeafWeight(plant_id, 0, node, 0)
        assert _mean_leaf_height(context, plantarch, plant_id, node) == pytest.approx(rest, abs=1e-3)

    def test_posed_leaves_block_bending_unless_included(self, tomato):
        """setLeafAngleDistribution() poses every leaf, after which a plain bend is a no-op."""
        context, plantarch, plant_id = tomato
        node = _leafy_node(plantarch, plant_id)
        plantarch.setLeafAngleDistribution(plant_id, 2.0, 2.0)
        posed = _mean_leaf_height(context, plantarch, plant_id, node)

        plantarch.setPetioleFlexibility(plant_id, 0, node, 3.0)
        plantarch.bendPetioleUnderLeafWeight(plant_id, 0, node, 0)
        assert _mean_leaf_height(context, plantarch, plant_id, node) == pytest.approx(posed, abs=1e-6)

        plantarch.bendPetioleUnderLeafWeight(plant_id, 0, node, 0, include_posed_leaves=True)
        assert _mean_leaf_height(context, plantarch, plant_id, node) < posed - 0.005

        # The leaves are still posed afterward, so a plain bend goes back to doing nothing.
        plantarch.setPetioleFlexibility(plant_id, 0, node, 1e-4)
        drooped = _mean_leaf_height(context, plantarch, plant_id, node)
        plantarch.bendPetioleUnderLeafWeight(plant_id, 0, node, 0)
        assert _mean_leaf_height(context, plantarch, plant_id, node) == pytest.approx(drooped, abs=1e-6)

    def test_out_of_range_node_raises(self, tomato):
        _, plantarch, plant_id = tomato
        with pytest.raises(PlantArchitectureError, match="(?i)out of range"):
            plantarch.getPetioleFlexibility(plant_id, 0, 9999)
        with pytest.raises(PlantArchitectureError, match="(?i)out of range"):
            plantarch.setPetioleFlexibility(plant_id, 0, 9999, 1.0)
