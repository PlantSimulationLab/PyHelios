"""
Tests for the helios-core 1.3.90 PlantArchitecture changes: the peduncle yaw parameter, structural
edits from phytomer creation functions and callbacks (deferred pruneBranch(), rejected operations),
and the library-model changes that reach the Python API (grapevine_Wye build parameters, pistachio
scaffolds, new shoot types).
"""

import os
import subprocess
import sys
import textwrap

import pytest

from pyhelios import Context, PlantArchitecture, PlantArchitectureError
from pyhelios.PlantArchitecture import _validate_build_parameters
from pyhelios.types import vec3
from pyhelios.wrappers import UPlantArchitectureWrapper as plantarch_wrapper
from pyhelios.wrappers.DataTypes import AxisRotation
from pyhelios.plant_architecture_params import (
    PeduncleParameters,
    PhytomerParameters,
    RandomParameterFloat,
    ShootParameters,
)

from tests.test_plantarchitecture_phytomer import _require_plantarch, _straight_tomato_type, _grow_base_stem

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WYE_PARAMETERS = {"trunk_height": 1.2, "cordon_spacing": 0.8, "vine_spacing": 2.2, "catch_wire_height": 2.0}


def _run_in_subprocess(source):
    env = dict(os.environ, PYTHONPATH=REPO_ROOT)
    return subprocess.run([sys.executable, "-c", textwrap.dedent(source)], capture_output=True,
                          text=True, timeout=300, cwd=REPO_ROOT, env=env)


def _probe(plantarch, callback=None, creation=None, nodes=5, max_nodes=8):
    """A straight tomato-typed 'probe' base stem with the given functions installed. Returns (plant_id, shoot_id)."""
    plantarch.disableMessages()
    plantarch.loadPlantModelFromLibrary("tomato")
    _straight_tomato_type(plantarch, "probe", max_nodes=max_nodes)
    if callback is not None:
        plantarch.setPhytomerCallbackFunction("probe", callback)
    if creation is not None:
        plantarch.setPhytomerCreationFunction("probe", creation)
    return _grow_base_stem(plantarch, "probe", nodes=nodes)


@pytest.mark.cross_platform
class TestPlantArch1390Validation:

    def _pa(self):
        plantarch = PlantArchitecture.__new__(PlantArchitecture)
        plantarch._plantarch_ptr = None
        plantarch.context = None
        return plantarch

    def test_grapevine_wye_build_parameters_are_accepted(self):
        """The model is registered as 'grapevine_Wye'; its parameters were keyed under 'grapevine_wye'."""
        _validate_build_parameters(dict(WYE_PARAMETERS), "grapevine_Wye")

    def test_grapevine_wye_rejects_tree_parameters(self):
        with pytest.raises(ValueError, match="num_scaffolds"):
            _validate_build_parameters({"num_scaffolds": 4}, "grapevine_Wye")

    def test_peduncle_yaw_defaults_to_zero_and_round_trips(self):
        assert PeduncleParameters().yaw == RandomParameterFloat.constant(0.0)
        assert PeduncleParameters().to_dict()["yaw"] == {"distribution": "constant", "parameters": [0.0]}

        pp = PhytomerParameters()
        pp.peduncle.yaw = RandomParameterFloat.uniform(170.0, 190.0)
        back = PhytomerParameters.from_dict(pp.to_dict())
        assert back.peduncle.yaw == RandomParameterFloat.uniform(170.0, 190.0)
        assert back.peduncle.roll == RandomParameterFloat.constant(0.0)

    def test_peduncle_from_dict_without_yaw_uses_default(self):
        peduncle = PeduncleParameters.from_dict({"roll": {"distribution": "constant", "parameters": [90.0]}})
        assert peduncle.yaw == RandomParameterFloat.constant(0.0)
        assert peduncle.roll.parameters == [90.0]

    @pytest.mark.parametrize("call", [
        lambda pa: pa.advanceTime(1.0),
        lambda pa: pa.advanceTime(1.0, plant_id=0),
        lambda pa: pa.deletePlantInstance(0),
        lambda pa: pa.loadPlantModelFromLibrary("bean"),
    ])
    def test_skipped_operations_raise_inside_a_callback(self, call):
        plantarch = self._pa()
        plantarch._phytomer_callback_depth = 1
        with pytest.raises(PlantArchitectureError, match="inside a phytomer creation or callback function"):
            call(plantarch)

    def test_rejected_load_does_not_change_the_recorded_model(self):
        plantarch = self._pa()
        plantarch._current_plant_model = "tomato"
        plantarch._phytomer_callback_depth = 1
        with pytest.raises(PlantArchitectureError):
            plantarch.loadPlantModelFromLibrary("bean")
        assert plantarch._current_plant_model == "tomato"

    def test_trampolines_track_callback_depth(self):
        plantarch = self._pa()
        plantarch._pending_callback_error = None
        seen = []

        callback = plantarch._makePhytomerCallbackTrampoline(
            lambda *a: seen.append(plantarch._phytomer_callback_depth))
        assert callback(0, 0, 0, 0.0) == 0
        creation = plantarch._makePhytomerCreationTrampoline(
            lambda *a: seen.append(plantarch._phytomer_callback_depth))
        assert creation(0, 0, 0, 0, 0, 1, 0.0) == 0
        assert seen == [1, 1]
        assert plantarch._phytomer_callback_depth == 0

    def test_callback_depth_is_restored_when_the_callback_raises(self):
        plantarch = self._pa()
        plantarch._pending_callback_error = None

        def failing(*args):
            raise KeyError("boom")

        callback = plantarch._makePhytomerCallbackTrampoline(failing)
        assert callback(0, 0, 0, 0.0) == 1
        assert plantarch._phytomer_callback_depth == 0
        assert isinstance(plantarch._pending_callback_error, KeyError)


@pytest.mark.native_only
class TestPeduncleYaw:

    def test_grapevine_clusters_hang_opposite_the_leaf(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            for model in ("grapevine_VSP", "grapevine_Wye"):
                plantarch.loadPlantModelFromLibrary(model)
                sp = plantarch.getCurrentShootParameters("grapevine_shoot", return_typed=True)
                assert sp.phytomer_parameters.peduncle.yaw == RandomParameterFloat.constant(180.0), model

    def test_yaw_round_trips_through_a_shoot_type(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("tomato")
            sp = plantarch.getCurrentShootParameters("mainstem", return_typed=True)
            assert sp.phytomer_parameters.peduncle.yaw == RandomParameterFloat.constant(0.0)

            sp.phytomer_parameters.peduncle.yaw = RandomParameterFloat.uniform(80.0, 100.0)
            plantarch.defineShootType("yawed", sp)
            back = plantarch.getCurrentShootParameters("yawed")
            assert back["phytomer_parameters"]["peduncle"]["yaw"] == {
                "distribution": "uniform", "parameters": [80.0, 100.0]}

    def test_resample_draws_yaw(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            pp = PhytomerParameters()
            pp.peduncle.yaw = RandomParameterFloat.uniform(80.0, 100.0)
            drawn = plantarch.resamplePhytomerParameters(pp)
            assert drawn.peduncle.yaw.distribution == "constant"
            assert 80.0 <= drawn.peduncle.yaw.parameters[0] <= 100.0


@pytest.mark.native_only
class TestLibraryModels1390:

    @pytest.mark.parametrize("model, label", [
        ("pistachio", "scaffold"),
        ("almond", "spur"),
        ("grapevine_VSP", "grapevine_lateral"),
        ("grapevine_Wye", "grapevine_lateral"),
    ])
    def test_new_shoot_types_are_listed(self, model, label):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary(model)
            assert label in plantarch.listShootTypeLabels()
            assert isinstance(plantarch.getCurrentShootParameters(label, return_typed=True), ShootParameters)

    def test_grapevine_wye_builds_with_trellis_parameters(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("grapevine_Wye")
            plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 0.0, build_parameters=dict(WYE_PARAMETERS))
            assert plantarch.getAllShootIDs(plant_id)
            assert context.getPrimitiveCount() > 0

    def test_grapevine_wye_trunk_height_is_the_cordon_wire_height(self):
        """0.165 m was the default trunk length before 1.3.90; the range is now 0.5-2 m."""
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("grapevine_Wye")
            with pytest.raises(PlantArchitectureError, match="trunk_height"):
                plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 0.0, build_parameters={"trunk_height": 0.165})

    @pytest.mark.parametrize("num_scaffolds", [4, 6])
    def test_pistachio_builds_the_requested_number_of_scaffolds(self, num_scaffolds):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("pistachio")
            plant_id = plantarch.buildPlantInstanceFromLibrary(
                vec3(0, 0, 0), 0.0, build_parameters={"num_scaffolds": num_scaffolds})
            trunk = [s for s in plantarch.getAllShootIDs(plant_id) if plantarch.getShoot(plant_id, s)["rank"] == 0]
            assert len(trunk) == 1
            assert len(plantarch.getShootChildIDs(plant_id, trunk[0])) == num_scaffolds


@pytest.mark.native_only
class TestStructuralEditsFromCallbacks:

    def test_prune_from_a_callback_is_deferred_to_the_end_of_the_step(self):
        """Before helios-core 1.3.90 this removed phytomers from the shoot being iterated."""
        _require_plantarch()
        result = _run_in_subprocess("""
            from pyhelios import Context, PlantArchitecture
            from tests.test_plantarchitecture_1390 import _probe

            context = Context()
            plantarch = PlantArchitecture(context)
            during, visited = [], []

            def prune_once(p, s, n, age):
                if not during:
                    plantarch.pruneBranch(p, s, 3)
                    during.append(plantarch.getShoot(p, s)["node_count"])
                    plantarch.pruneBranch(p, s, 4)  # already taken off by the cut below it
                visited.append(n)

            plant_id, shoot_id = _probe(plantarch, callback=prune_once, nodes=5)
            plantarch.advanceTime(1.0, plant_id=plant_id)
            print("DURING", during[0])
            print("VISITED", sorted(set(visited)))
            print("AFTER", plantarch.getShoot(plant_id, shoot_id)["node_count"])
        """)
        assert result.returncode == 0, f"exit {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        assert "DURING 5" in result.stdout, result.stdout
        assert "VISITED [0, 1, 2, 3, 4]" in result.stdout, result.stdout
        assert "AFTER 3" in result.stdout, result.stdout

    def test_prune_from_a_creation_function_is_applied_before_the_build_call_returns(self):
        _require_plantarch()
        result = _run_in_subprocess("""
            from pyhelios import Context, PlantArchitecture
            from tests.test_plantarchitecture_1390 import _probe

            context = Context()
            plantarch = PlantArchitecture(context)
            during = []

            def prune_at_fourth(p, s, n, *rest):
                if n == 3:
                    plantarch.pruneBranch(p, s, 2)
                    during.append(plantarch.getShoot(p, s)["node_count"])

            plant_id, shoot_id = _probe(plantarch, creation=prune_at_fourth, nodes=5)
            print("UNCUT_DURING", len(during) == 1 and during[0] > 2)
            print("AFTER", plantarch.getShoot(plant_id, shoot_id)["node_count"])
        """)
        assert result.returncode == 0, f"exit {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        assert "UNCUT_DURING True" in result.stdout, result.stdout
        assert "AFTER 2" in result.stdout, result.stdout

    def test_invalid_prune_raises_at_the_call_site(self):
        _require_plantarch()
        caught = []

        def bad_prune(p, s, n, age):
            try:
                plantarch.pruneBranch(p, s, 99)
            except PlantArchitectureError as e:
                caught.append(e)

        with Context() as context, PlantArchitecture(context) as plantarch:
            plant_id, shoot_id = _probe(plantarch, callback=bad_prune, nodes=3)
            plantarch.advanceTime(1.0, plant_id=plant_id)
            assert len(caught) == 3
            assert plantarch.getShoot(plant_id, shoot_id)["node_count"] == 3

    def test_cuts_queued_before_a_failing_callback_are_discarded(self):
        _require_plantarch()

        def prune_then_fail(p, s, n, age):
            plantarch.pruneBranch(p, s, 1)
            raise KeyError("stop")

        with Context() as context, PlantArchitecture(context) as plantarch:
            plant_id, shoot_id = _probe(plantarch, callback=prune_then_fail, nodes=3)
            with pytest.raises(KeyError, match="stop"):
                plantarch.advanceTime(1.0, plant_id=plant_id)
            assert plantarch.getShoot(plant_id, shoot_id)["node_count"] == 3

    @pytest.mark.parametrize("operation", ["advanceTime", "deletePlantInstance", "loadPlantModelFromLibrary"])
    def test_skipped_operations_raise_and_leave_the_plant_alone(self, operation):
        _require_plantarch()

        def edit(p, s, n, age):
            if operation == "advanceTime":
                plantarch.advanceTime(1.0)
            elif operation == "deletePlantInstance":
                plantarch.deletePlantInstance(p)
            else:
                plantarch.loadPlantModelFromLibrary("bean")

        with Context() as context, PlantArchitecture(context) as plantarch:
            plant_id, shoot_id = _probe(plantarch, callback=edit, nodes=3)
            with pytest.raises(PlantArchitectureError, match=f"{operation}\\(\\) cannot be called from inside"):
                plantarch.advanceTime(1.0, plant_id=plant_id)
            assert plant_id in plantarch.getAllPlantIDs()
            assert plantarch.getShoot(plant_id, shoot_id)["node_count"] == 3
            assert "probe" in plantarch.listShootTypeLabels()

            # The same operations work once the callback has returned.
            plantarch.setPhytomerCallbackFunction("probe", None)
            plantarch.advanceTime(1.0, plant_id=plant_id)
            plantarch.deletePlantInstance(plant_id)
            assert plant_id not in plantarch.getAllPlantIDs()

    @pytest.mark.parametrize("operation", ["addBaseStemShoot", "buildPlantInstanceFromLibrary"])
    def test_adding_structure_from_a_callback_raises(self, operation):
        _require_plantarch()

        def edit(p, s, n, age):
            if operation == "addBaseStemShoot":
                plantarch.addBaseStemShoot(
                    plant_id=p, current_node_number=1, base_rotation=AxisRotation(0, 0, 0),
                    internode_radius=0.002, internode_length_max=0.04,
                    internode_length_scale_factor_fraction=0.1, leaf_scale_factor_fraction=0.1,
                    radius_taper=1.0, shoot_type_label="probe")
            else:
                plantarch.buildPlantInstanceFromLibrary(vec3(1, 0, 0), 0.0)

        with Context() as context, PlantArchitecture(context) as plantarch:
            plant_id, shoot_id = _probe(plantarch, callback=edit, nodes=3)
            with pytest.raises(PlantArchitectureError, match="(?i)inside a phytomer callback"):
                plantarch.advanceTime(1.0, plant_id=plant_id)
            assert plantarch.getAllShootIDs(plant_id) == [shoot_id]


@pytest.mark.cross_platform
class TestLibraryPhytomerFunctionsValidation:
    """Argument checks and the availability guard for library phytomer functions set by name."""

    def _pa(self):
        return PlantArchitecture.__new__(PlantArchitecture)

    @pytest.mark.parametrize("setter", ["setPhytomerCreationFunction", "setPhytomerCallbackFunction"])
    def test_empty_name_is_rejected(self, setter):
        with pytest.raises(ValueError, match="cannot be empty"):
            getattr(PlantArchitecture, setter)(self._pa(), "proleptic", "")

    @pytest.mark.parametrize("setter", ["setPhytomerCreationFunction", "setPhytomerCallbackFunction"])
    @pytest.mark.parametrize("callback", [3, b"AlmondPhytomerCallbackFunction", ["AlmondPhytomerCallbackFunction"]])
    def test_neither_callable_nor_name_is_rejected(self, setter, callback):
        with pytest.raises(ValueError, match="library function name"):
            getattr(PlantArchitecture, setter)(self._pa(), "proleptic", callback)

    @pytest.mark.parametrize("getter", ["getPhytomerCreationFunctionName", "getPhytomerCallbackFunctionName"])
    @pytest.mark.parametrize("label", [None, 3, ""])
    def test_getter_rejects_bad_label(self, getter, label):
        with pytest.raises(ValueError, match="(?i)shoot type label"):
            getattr(PlantArchitecture, getter)(self._pa(), label)

    def test_guard_matches_its_registration_block(self):
        from unittest.mock import patch
        with patch.object(plantarch_wrapper, '_PLANTARCHITECTURE_LIBRARY_PHYTOMER_FUNCTIONS_AVAILABLE', False):
            for call in (lambda: plantarch_wrapper.setPhytomerCreationFunctionByName(None, "a", "b"),
                         lambda: plantarch_wrapper.setPhytomerCallbackFunctionByName(None, "a", "b"),
                         lambda: plantarch_wrapper.getPhytomerCreationFunctionName(None, "a"),
                         lambda: plantarch_wrapper.getPhytomerCallbackFunctionName(None, "a"),
                         plantarch_wrapper.getLibraryPhytomerCreationFunctionNames,
                         plantarch_wrapper.getLibraryPhytomerCallbackFunctionNames):
                with pytest.raises(RuntimeError, match="by name"):
                    call()

    def test_symbols_are_registered(self):
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture native functions not available")
        assert plantarch_wrapper._PLANTARCHITECTURE_LIBRARY_PHYTOMER_FUNCTIONS_AVAILABLE


@pytest.mark.native_only
class TestLibraryPhytomerFunctions:
    """The Assets.h phytomer creation and callback functions, installed and read back by name."""

    @pytest.fixture
    def plantarch(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as instance:
            instance.disableMessages()
            yield instance

    def test_callback_names_include_the_1390_functions(self):
        _require_plantarch()
        names = PlantArchitecture.getLibraryPhytomerCallbackFunctionNames()
        assert "AlmondSpurPhytomerCallbackFunction" in names
        assert "GrapevinePhytomerCallbackFunction" in names
        assert names == sorted(names) and len(set(names)) == len(names)

    def test_creation_and_callback_names_do_not_overlap(self):
        _require_plantarch()
        creation = PlantArchitecture.getLibraryPhytomerCreationFunctionNames()
        assert "AlmondPhytomerCreationFunction" in creation
        assert all(name.endswith("PhytomerCreationFunction") for name in creation)
        assert not set(creation) & set(PlantArchitecture.getLibraryPhytomerCallbackFunctionNames())

    @pytest.mark.parametrize("model, label, creation, callback", [
        ("almond", "proleptic", "AlmondPhytomerCreationFunction", "AlmondSpurPhytomerCallbackFunction"),
        ("almond", "trunk", None, None),
        ("grapevine_VSP", "grapevine_shoot", "GrapevinePhytomerCreationFunction", "GrapevinePhytomerCallbackFunction"),
        ("tomato", "mainstem", "TomatoPhytomerCreationFunction", None),
    ])
    def test_library_models_report_their_functions(self, plantarch, model, label, creation, callback):
        plantarch.loadPlantModelFromLibrary(model)
        assert plantarch.getPhytomerCreationFunctionName(label) == creation
        assert plantarch.getPhytomerCallbackFunctionName(label) == callback

    def test_a_new_label_starts_without_functions_and_takes_them_by_name(self, plantarch):
        plantarch.loadPlantModelFromLibrary("almond")
        plantarch.defineShootType("my_shoot", plantarch.getCurrentShootParameters("proleptic"))
        assert plantarch.getPhytomerCreationFunctionName("my_shoot") is None
        assert plantarch.getPhytomerCallbackFunctionName("my_shoot") is None

        plantarch.setPhytomerCreationFunction("my_shoot", plantarch.getPhytomerCreationFunctionName("proleptic"))
        plantarch.setPhytomerCallbackFunction("my_shoot", "AlmondSpurPhytomerCallbackFunction")

        assert plantarch.getPhytomerCreationFunctionName("my_shoot") == "AlmondPhytomerCreationFunction"
        assert plantarch.getPhytomerCallbackFunctionName("my_shoot") == "AlmondSpurPhytomerCallbackFunction"
        # Redefining the label keeps them, and the type the names were read from is untouched.
        plantarch.defineShootType("my_shoot", plantarch.getCurrentShootParameters("my_shoot"))
        assert plantarch.getPhytomerCallbackFunctionName("my_shoot") == "AlmondSpurPhytomerCallbackFunction"
        assert plantarch.getPhytomerCallbackFunctionName("proleptic") == "AlmondSpurPhytomerCallbackFunction"

    def test_a_library_function_set_by_name_runs(self, plantarch):
        """TomatoPhytomerCreationFunction shrinks the leaves of a young plant to about a third of their unscaled area."""
        def leaf_area(creation):
            plantarch.loadPlantModelFromLibrary("tomato")
            _straight_tomato_type(plantarch, "probe", max_nodes=8)
            if creation is not None:
                plantarch.setPhytomerCreationFunction("probe", creation)
            plant_id, _ = _grow_base_stem(plantarch, "probe", nodes=4)
            area = plantarch.getPlantLeafArea(plant_id)
            plantarch.deletePlantInstance(plant_id)
            return area

        bare = leaf_area(None)
        with_library = leaf_area("TomatoPhytomerCreationFunction")
        assert bare > 0.0
        assert 0.0 < with_library < 0.6 * bare

    def test_a_python_callback_reports_no_name_and_is_replaced_by_one(self, plantarch):
        calls = []
        plantarch.loadPlantModelFromLibrary("tomato")
        _straight_tomato_type(plantarch, "probe", max_nodes=8)
        plantarch.setPhytomerCreationFunction("probe", lambda *args: calls.append(args))
        assert plantarch.getPhytomerCreationFunctionName("probe") is None

        plantarch.setPhytomerCreationFunction("probe", "TomatoPhytomerCreationFunction")
        assert plantarch.getPhytomerCreationFunctionName("probe") == "TomatoPhytomerCreationFunction"
        assert "probe" not in plantarch._phytomer_creation_callbacks
        _grow_base_stem(plantarch, "probe", nodes=3)
        assert calls == []

        # None restores what a later Python callback replaced, which is now the library function.
        plantarch.setPhytomerCreationFunction("probe", lambda *args: calls.append(args))
        plantarch.setPhytomerCreationFunction("probe", None)
        assert plantarch.getPhytomerCreationFunctionName("probe") == "TomatoPhytomerCreationFunction"

    def test_shoots_built_under_a_python_callback_switch_to_the_library_function(self, plantarch):
        calls = []
        plant_id, shoot_id = _probe(plantarch, callback=lambda *args: calls.append(args), nodes=3)
        plantarch.advanceTime(1.0, plant_id=plant_id)
        assert calls
        calls.clear()

        plantarch.setPhytomerCallbackFunction("probe", "CherryTomatoPhytomerCallbackFunction")
        plantarch.advanceTime(1.0, plant_id=plant_id)
        assert calls == []
        assert plantarch.getPhytomerCallbackFunctionName("probe") == "CherryTomatoPhytomerCallbackFunction"

    @pytest.mark.parametrize("setter, wrong_kind", [
        ("setPhytomerCreationFunction", "AlmondPhytomerCallbackFunction"),
        ("setPhytomerCallbackFunction", "AlmondPhytomerCreationFunction"),
        ("setPhytomerCallbackFunction", "NoSuchFunction"),
    ])
    def test_unknown_or_wrong_kind_name_raises(self, plantarch, setter, wrong_kind):
        plantarch.loadPlantModelFromLibrary("almond")
        with pytest.raises(PlantArchitectureError, match="Unknown library phytomer"):
            getattr(plantarch, setter)("proleptic", wrong_kind)
        assert plantarch.getPhytomerCallbackFunctionName("proleptic") == "AlmondSpurPhytomerCallbackFunction"

    def test_unknown_shoot_type_raises(self, plantarch):
        plantarch.loadPlantModelFromLibrary("almond")
        with pytest.raises(PlantArchitectureError):
            plantarch.setPhytomerCallbackFunction("no_such_type", "AlmondSpurPhytomerCallbackFunction")
        with pytest.raises(PlantArchitectureError):
            plantarch.getPhytomerCallbackFunctionName("no_such_type")
