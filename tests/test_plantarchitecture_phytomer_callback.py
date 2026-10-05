"""
Tests for PlantArchitecture.setPhytomerCallbackFunction, the Python counterpart of
PhytomerParameters::phytomer_callback_function (called for every phytomer on every time step).
"""

import collections
import os
import subprocess
import sys
import textwrap
from unittest.mock import patch

import pytest

from pyhelios import Context, PlantArchitecture, PlantArchitectureError
from pyhelios.types import vec3
from pyhelios.wrappers import UPlantArchitectureWrapper as plantarch_wrapper

from tests.test_plantarchitecture_phytomer import _require_plantarch, _straight_tomato_type, _grow_base_stem

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.mark.cross_platform
class TestPhytomerCallbackValidation:

    def _pa(self):
        return PlantArchitecture.__new__(PlantArchitecture)

    @pytest.mark.parametrize("label", [None, 3, b"mainstem", ""])
    def test_rejects_bad_label(self, label):
        with pytest.raises(ValueError, match="(?i)shoot type label"):
            PlantArchitecture.setPhytomerCallbackFunction(self._pa(), label, None)

    @pytest.mark.parametrize("callback", [3, b"fn", object()])
    def test_rejects_non_callable(self, callback):
        with pytest.raises(ValueError, match="(?i)callable"):
            PlantArchitecture.setPhytomerCallbackFunction(self._pa(), "mainstem", callback)

    def test_guard_names_the_missing_symbol(self):
        with patch.object(plantarch_wrapper, '_PLANTARCHITECTURE_PHYTOMER_CALLBACK_AVAILABLE', False):
            with pytest.raises(RuntimeError, match="setPhytomerCallbackFunction"):
                plantarch_wrapper.setPhytomerCallbackFunction(None, "mainstem", None)

    def test_symbol_is_registered(self):
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture native functions not available")
        assert hasattr(plantarch_wrapper.helios_lib, "setPhytomerCallbackFunction")


def _probe(plantarch, callback, nodes=3):
    """A straight tomato-typed 'probe' base stem, built with callback installed as its per-timestep callback."""
    plantarch.disableMessages()
    plantarch.loadPlantModelFromLibrary("tomato")
    _straight_tomato_type(plantarch, "probe", max_nodes=8)
    plantarch.setPhytomerCallbackFunction("probe", callback)
    return _grow_base_stem(plantarch, "probe", nodes=nodes)


@pytest.mark.native_only
class TestPhytomerCallback:

    def test_fires_for_every_phytomer_on_every_step_with_its_identity_and_age(self):
        _require_plantarch()
        calls = []
        with Context() as context:
            with PlantArchitecture(context) as plantarch:
                plant_id, shoot_id = _probe(plantarch, lambda *a: calls.append(a), nodes=3)
                assert calls == []

                plantarch.advanceTime(1.0, plant_id=plant_id)
                assert sorted(c[2] for c in calls) == [0, 1, 2], "one call per phytomer per step"
                assert all(c[0] == plant_id and c[1] == shoot_id for c in calls)
                for p, s, n, age in calls:
                    assert age == pytest.approx(plantarch.getPhytomerAge(p, s, n))

                calls.clear()
                plantarch.advanceTime(3.0, plant_id=plant_id)
                per_node = collections.Counter(c[2] for c in calls)
                steps = per_node[0]
                assert steps >= 1 and per_node[1] == steps and per_node[2] == steps, per_node
                # Phytomers added during the call are visited only on the steps after their creation.
                assert all(count <= steps for count in per_node.values()), per_node
                last_age = {n: age for _, _, n, age in calls}
                for n, age in last_age.items():
                    assert age == pytest.approx(plantarch.getPhytomerAge(plant_id, shoot_id, n))

    def test_fires_for_phytomers_added_by_growth(self):
        _require_plantarch()
        seen = set()
        with Context() as context:
            context.seedRandomGenerator(3)
            with PlantArchitecture(context) as plantarch:
                plant_id, shoot_id = _probe(plantarch, lambda p, s, n, age: seen.add(n), nodes=1)
                plantarch.breakPlantDormancy(plant_id)
                plantarch.advanceTime(12.0, plant_id=plant_id)
                node_count = plantarch.getShoot(plant_id, shoot_id)["node_count"]
                assert node_count > 2, "the probe shoot did not grow"
                # The newest phytomer may be created on the final step, after that step's callbacks ran.
                assert set(range(node_count - 1)) <= seen <= set(range(node_count))

    def test_callback_can_modify_the_phytomer(self):
        _require_plantarch()
        with Context() as context:
            with PlantArchitecture(context) as plantarch:
                plant_id, shoot_id = _probe(
                    plantarch, lambda p, s, n, age: plantarch.setInternodeMaxLength(p, s, n, 0.001), nodes=2)
                plantarch.advanceTime(1.0, plant_id=plant_id)
                assert plantarch.getInternodeLength(plant_id, shoot_id, 1) == pytest.approx(0.001, rel=1e-3)

    def test_replacing_and_clearing_take_effect_for_existing_shoots(self):
        _require_plantarch()
        first, second = [], []
        with Context() as context:
            with PlantArchitecture(context) as plantarch:
                plant_id, _ = _probe(plantarch, lambda *a: first.append(a), nodes=2)
                plantarch.setPhytomerCallbackFunction("probe", lambda *a: second.append(a))
                plantarch.advanceTime(1.0, plant_id=plant_id)
                assert first == [] and len(second) == 2
                plantarch.setPhytomerCallbackFunction("probe", None)
                plantarch.advanceTime(1.0, plant_id=plant_id)
                assert len(second) == 2

    def test_installing_twice_then_clearing_does_not_recurse(self):
        """The trampoline must never record itself as the function to restore; if it did, clearing would recurse."""
        _require_plantarch()
        result = _run_in_subprocess("""
            from pyhelios import Context, PlantArchitecture
            from tests.test_plantarchitecture_phytomer_callback import _probe

            calls = []
            context = Context()
            plantarch = PlantArchitecture(context)
            plant_id, _ = _probe(plantarch, lambda *a: calls.append(a), nodes=2)
            plantarch.setPhytomerCallbackFunction("probe", lambda *a: calls.append(a))
            plantarch.setPhytomerCallbackFunction("probe", None)
            plantarch.advanceTime(1.0, plant_id=plant_id)
            print("CALLS", len(calls))
        """)
        assert result.returncode == 0, f"exit {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        assert "CALLS 0" in result.stdout

    def test_none_on_a_library_type_keeps_growth_working(self):
        """almond's proleptic shoots carry a library per-timestep function, which None restores."""
        _require_plantarch()
        calls = []
        with Context() as context:
            context.seedRandomGenerator(1)
            with PlantArchitecture(context) as plantarch:
                plantarch.disableMessages()
                plantarch.loadPlantModelFromLibrary("almond")
                labels = plantarch.listShootTypeLabels()
                for label in labels:
                    plantarch.setPhytomerCallbackFunction(label, lambda *a: calls.append(a))
                plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 200.0)
                assert calls, "the Python callback never ran on almond phytomers"
                for label in labels:
                    plantarch.setPhytomerCallbackFunction(label, None)
                calls.clear()
                plantarch.advanceTime(5.0, plant_id=plant_id)
                assert calls == []

    def test_phytomers_created_before_the_callback_do_not_call_it(self):
        """Each phytomer copies its type's parameters at creation, as with the creation function."""
        _require_plantarch()
        calls = []
        with Context() as context:
            with PlantArchitecture(context) as plantarch:
                plant_id, _ = _probe(plantarch, None, nodes=2)
                plantarch.setPhytomerCallbackFunction("probe", lambda *a: calls.append(a))
                plantarch.advanceTime(1.0, plant_id=plant_id)
                assert calls == []

    def test_does_not_fire_for_other_shoot_types(self):
        _require_plantarch()
        calls = []
        with Context() as context:
            with PlantArchitecture(context) as plantarch:
                plantarch.loadPlantModelFromLibrary("tomato")
                _straight_tomato_type(plantarch, "other")
                plantarch.setPhytomerCallbackFunction("other", lambda *a: calls.append(a))
                plant_id, _ = _probe(plantarch, None, nodes=2)
                plantarch.advanceTime(1.0, plant_id=plant_id)
                assert calls == []

    def test_unknown_shoot_type_raises(self):
        _require_plantarch()
        with Context() as context:
            with PlantArchitecture(context) as plantarch:
                plantarch.disableMessages()
                with pytest.raises(PlantArchitectureError, match="no_such_type"):
                    plantarch.setPhytomerCallbackFunction("no_such_type", lambda *a: None)


def _run_in_subprocess(source):
    env = dict(os.environ, PYTHONPATH=REPO_ROOT)
    return subprocess.run([sys.executable, "-c", textwrap.dedent(source)], capture_output=True,
                          text=True, timeout=300, cwd=REPO_ROOT, env=env)


@pytest.mark.native_only
class TestPhytomerCallbackErrors:

    def test_exception_surfaces_from_advanceTime_and_does_not_poison_the_next_call(self):
        _require_plantarch()
        result = _run_in_subprocess("""
            import sys
            sys.path.insert(0, 'tests')
            from pyhelios import Context, PlantArchitecture
            from tests.test_plantarchitecture_phytomer_callback import _probe

            class Boom(Exception):
                pass

            def explode(plant_id, shoot_id, node_index, age):
                raise Boom(f"callback failed at node {node_index}")

            context = Context()
            plantarch = PlantArchitecture(context)
            plant_id, shoot_id = _probe(plantarch, explode, nodes=2)
            try:
                plantarch.advanceTime(1.0, plant_id=plant_id)
            except Boom as e:
                print("RAISED", e)
            else:
                print("NOT RAISED")
                sys.exit(3)
            plantarch.setPhytomerCallbackFunction("probe", None)
            plantarch.advanceTime(1.0, plant_id=plant_id)
            print("RECOVERED")
        """)
        assert result.returncode == 0, f"exit {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        assert "RAISED callback failed at node 0" in result.stdout
        assert "RECOVERED" in result.stdout
