"""
Tests for PlantArchitecture.setFruitPrototypeFunction and setFlowerPrototypeFunction, the Python counterparts of
InflorescenceParameters::fruit_prototype_function and flower_prototype_function.
"""

import copy
from unittest.mock import patch

import pytest

from pyhelios import Context, PlantArchitecture, PlantArchitectureError
from pyhelios.types import vec3
from pyhelios.wrappers import UPlantArchitectureWrapper as plantarch_wrapper

from tests.test_plantarchitecture_phytomer import _grow_base_stem, _require_plantarch


@pytest.mark.cross_platform
class TestPythonPrototypeValidation:

    def _pa(self):
        return PlantArchitecture.__new__(PlantArchitecture)

    @pytest.mark.parametrize("setter", ["setFruitPrototypeFunction", "setFlowerPrototypeFunction"])
    @pytest.mark.parametrize("label", [None, 3, b"mainstem", ""])
    def test_rejects_bad_label(self, setter, label):
        with pytest.raises(ValueError, match="(?i)shoot type label"):
            getattr(PlantArchitecture, setter)(self._pa(), label, None)

    @pytest.mark.parametrize("setter", ["setFruitPrototypeFunction", "setFlowerPrototypeFunction"])
    @pytest.mark.parametrize("function", [3, b"fn", "TomatoFruitPrototype", object()])
    def test_rejects_non_callable(self, setter, function):
        with pytest.raises(ValueError, match="(?i)callable"):
            getattr(PlantArchitecture, setter)(self._pa(), "mainstem", function)

    def test_guard_names_the_rebuild(self):
        with patch.object(plantarch_wrapper, '_PLANTARCHITECTURE_PYTHON_PROTOTYPES_AVAILABLE', False):
            with pytest.raises(RuntimeError, match="(?i)prototype functions are not available"):
                plantarch_wrapper.setFruitPrototypeFunction(None, None, "mainstem", None)

    def test_symbols_are_registered(self):
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture native functions not available")
        assert hasattr(plantarch_wrapper.helios_lib, "setFruitPrototypeFunction")
        assert hasattr(plantarch_wrapper.helios_lib, "setFlowerPrototypeFunction")


def _box(context, length=1.0, width=0.3):
    """A small closed box along +x from the origin, as primitive UUIDs: the shape of a unit fruit prototype."""
    return context.addBox(center=vec3(length / 2, 0, 0), size=vec3(length, width, width))


class _Recorder:
    """A prototype function that builds a box and records every call."""

    def __init__(self, length=1.0):
        self.calls = []
        self.length = length

    def __call__(self, context, *args):
        self.calls.append(args)
        return _box(context, self.length)


def _constant(value):
    return {"distribution": "constant", "parameters": [float(value)]}


def _fruiting_tomato(plantarch, unique_prototypes=3):
    """The library tomato, every floral bud flowering and setting fruit, with a fixed number of unique prototypes.

    The library sets only some of its buds, so without this a seed can grow no flower at all and a test of a
    prototype function would pass without ever calling it. Seeded at 5 and grown to 60 days it carries 18 flowers;
    to 90 days, 30 flowers and 48 fruit.
    """
    plantarch.disableMessages()
    plantarch.loadPlantModelFromLibrary("tomato")
    params = copy.deepcopy(plantarch.getCurrentShootParameters("mainstem"))
    params["flower_bud_break_probability"] = _constant(1)
    params["fruit_set_probability"] = _constant(1)
    params["phytomer_parameters"]["inflorescence"]["unique_prototypes"] = unique_prototypes
    plantarch.defineShootType("mainstem", params)
    return params


def _grow(plantarch, age=90.0):
    return plantarch.buildPlantInstanceFromLibrary(base_position=vec3(0, 0, 0), age=age)


@pytest.mark.native_only
class TestPythonFruitPrototype:

    def test_builds_each_unique_prototype_and_every_fruit_is_a_copy(self):
        _require_plantarch()
        fruit = _Recorder()
        with Context() as context:
            context.seedRandomGenerator(5)
            with PlantArchitecture(context) as plantarch:
                _fruiting_tomato(plantarch, unique_prototypes=3)
                plantarch.setFruitPrototypeFunction("mainstem", fruit)
                plant_id = _grow(plantarch)
                fruit_ids = plantarch.getPlantFruitObjectIDs(plant_id)
                assert fruit_ids, "the tomato carried no fruit, so the prototype function was never exercised"
                assert len(fruit.calls) == 3, "one call per unique prototype"
                for subdivisions, parameters in fruit.calls:
                    assert isinstance(subdivisions, int)
                    assert isinstance(parameters, dict)
                # Every fruit is a box: 6 patches.
                for oid in fruit_ids:
                    assert len(context.getObjectPrimitiveUUIDs(oid)) == 6

    def test_parameters_name_the_slot_and_carry_it_to_a_new_type(self):
        _require_plantarch()
        fruit = _Recorder()
        with Context() as context:
            context.seedRandomGenerator(5)
            with PlantArchitecture(context) as plantarch:
                _fruiting_tomato(plantarch)
                plantarch.setFruitPrototypeFunction("mainstem", fruit)
                params = plantarch.getCurrentShootParameters("mainstem")
                name = params["phytomer_parameters"]["inflorescence"]["fruit_prototype_function"]
                assert name.startswith("PythonFruitPrototype_"), name
                # Round trips through a definition, and a new type defined from it shares the function.
                plantarch.defineShootType("mainstem", params)
                plantarch.defineShootType("copy", copy.deepcopy(params))
                for label in ("mainstem", "copy"):
                    got = plantarch.getCurrentShootParameters(label)["phytomer_parameters"]["inflorescence"]
                    assert got["fruit_prototype_function"] == name

    def test_replacing_binds_a_new_slot_and_none_restores_the_library_function(self):
        _require_plantarch()
        with Context() as context:
            context.seedRandomGenerator(5)
            with PlantArchitecture(context) as plantarch:
                _fruiting_tomato(plantarch)

                def name():
                    return plantarch.getCurrentShootParameters("mainstem")["phytomer_parameters"][
                        "inflorescence"]["fruit_prototype_function"]

                assert name() == "TomatoFruitPrototype"
                plantarch.setFruitPrototypeFunction("mainstem", _Recorder())
                first = name()
                plantarch.setFruitPrototypeFunction("mainstem", _Recorder())
                second = name()
                assert first != second and second.startswith("PythonFruitPrototype_")
                plantarch.setFruitPrototypeFunction("mainstem", None)
                assert name() == "TomatoFruitPrototype"

    def test_an_exception_propagates_with_its_type(self):
        _require_plantarch()

        def broken(context, subdivisions, parameters):
            raise ZeroDivisionError("no fruit today")

        with Context() as context:
            context.seedRandomGenerator(5)
            with PlantArchitecture(context) as plantarch:
                _fruiting_tomato(plantarch)
                plantarch.setFruitPrototypeFunction("mainstem", broken)
                with pytest.raises(ZeroDivisionError, match="no fruit today"):
                    _grow(plantarch)

    @pytest.mark.parametrize("returned", [None, [], 7, [1.5], "uuids", [True]])
    def test_a_wrong_return_value_is_refused(self, returned):
        _require_plantarch()
        with Context() as context:
            context.seedRandomGenerator(5)
            with PlantArchitecture(context) as plantarch:
                _fruiting_tomato(plantarch)
                plantarch.setFruitPrototypeFunction("mainstem", lambda c, s, p: returned)
                with pytest.raises(TypeError, match="(?i)list of primitive UUIDs"):
                    _grow(plantarch)

    def test_parameters_carried_to_another_context_are_refused_when_called(self):
        _require_plantarch()
        with Context() as context:
            context.seedRandomGenerator(5)
            with PlantArchitecture(context) as plantarch:
                _fruiting_tomato(plantarch)
                plantarch.setFruitPrototypeFunction("mainstem", _Recorder())
                params = plantarch.getCurrentShootParameters("mainstem")
                with Context() as other_context:
                    other_context.seedRandomGenerator(5)
                    with PlantArchitecture(other_context) as other:
                        other.disableMessages()
                        # A NEW label takes the function the parameters name; redefining an existing one keeps its own.
                        other.defineShootType("carried", params)
                        with pytest.raises(PlantArchitectureError, match="different Context"):
                            plant_id, _ = _grow_base_stem(other, "carried", nodes=1)
                            other.setPlantPhenologicalThresholds(plant_id, 0, 40, 5, 5, 30, 1000)
                            other.breakPlantDormancy(plant_id)
                            other.advanceTime(90)

    def test_redefining_an_existing_type_keeps_its_python_function(self):
        _require_plantarch()
        with Context() as context:
            context.seedRandomGenerator(5)
            with PlantArchitecture(context) as plantarch:
                _fruiting_tomato(plantarch)
                plantarch.setFruitPrototypeFunction("mainstem", _Recorder())
                params = plantarch.getCurrentShootParameters("mainstem")
                name = params["phytomer_parameters"]["inflorescence"]["fruit_prototype_function"]
                params["phytomer_parameters"]["inflorescence"]["fruit_prototype_function"] = "TomatoFruitPrototype"
                plantarch.defineShootType("mainstem", params)
                got = plantarch.getCurrentShootParameters("mainstem")["phytomer_parameters"]["inflorescence"]
                assert got["fruit_prototype_function"] == name

    def test_slots_run_out_and_are_freed_with_their_plantarchitecture(self):
        _require_plantarch()
        with Context() as context:
            context.seedRandomGenerator(5)
            with PlantArchitecture(context) as plantarch:
                _fruiting_tomato(plantarch)
                for _ in range(32):
                    plantarch.setFruitPrototypeFunction("mainstem", _Recorder())
                with pytest.raises(PlantArchitectureError, match="slots are in use"):
                    plantarch.setFruitPrototypeFunction("mainstem", _Recorder())
            with PlantArchitecture(context) as plantarch:
                _fruiting_tomato(plantarch)
                plantarch.setFruitPrototypeFunction("mainstem", _Recorder())


@pytest.mark.native_only
class TestPythonFlowerPrototype:

    def test_builds_closed_and_open_prototypes(self):
        _require_plantarch()
        flower = _Recorder(length=0.5)
        with Context() as context:
            context.seedRandomGenerator(5)
            with PlantArchitecture(context) as plantarch:
                _fruiting_tomato(plantarch, unique_prototypes=2)
                plantarch.setFlowerPrototypeFunction("mainstem", flower)
                name = plantarch.getCurrentShootParameters("mainstem")["phytomer_parameters"][
                    "inflorescence"]["flower_prototype_function"]
                assert name.startswith("PythonFlowerPrototype_"), name
                plant_id = _grow(plantarch, age=60.0)
                assert plantarch.getPlantFlowerObjectIDs(plant_id) or plantarch.getPlantFruitObjectIDs(plant_id)
                opened = sorted(is_open for _, is_open, _ in flower.calls)
                assert opened == [False, False, True, True], "two closed and two open prototypes"
