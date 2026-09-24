"""
Tests for the helios-core 1.3.88 PlantArchitecture additions: the phytomer creation
callback, per-phytomer growth targets and readouts, live shoot phyllotaxy, per-model leaf
inclination distributions, and the reworked nitrogen parameters.
"""

import copy
import math
import os
import subprocess
import sys
import textwrap
from unittest.mock import patch

import pytest

from pyhelios import Context, PlantArchitecture, PlantArchitectureError
from pyhelios.types import vec3
from pyhelios.wrappers.DataTypes import AxisRotation
from pyhelios.wrappers import UPlantArchitectureWrapper as plantarch_wrapper
from pyhelios.plugins.registry import get_plugin_registry
from pyhelios.plant_architecture_params import NitrogenParameters

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _require_plantarch():
    if not get_plugin_registry().is_plugin_available('plantarchitecture'):
        pytest.skip("PlantArchitecture plugin not available")


def _constant(value):
    return {"distribution": "constant", "parameters": [float(value)]}


def _straight_tomato_type(plantarch, label, phyllotactic_angle=137.5, leaves_per_petiole=None,
                          max_nodes=None):
    """Define a tomato-derived shoot type with a straight vertical stem and constant phyllotaxy."""
    params = copy.deepcopy(plantarch.getCurrentShootParameters("mainstem"))
    params["tortuosity"] = _constant(0)
    params["gravitropic_curvature"] = _constant(0)
    params["child_shoot_types"] = {"labels": [], "probabilities": []}
    internode = params["phytomer_parameters"]["internode"]
    internode["pitch"] = _constant(0)
    internode["phyllotactic_angle"] = _constant(phyllotactic_angle)
    internode["max_floral_buds_per_petiole"] = _constant(0)
    internode["max_vegetative_buds_per_petiole"] = _constant(0)
    if leaves_per_petiole is not None:
        params["phytomer_parameters"]["leaf"]["leaves_per_petiole"] = _constant(leaves_per_petiole)
    if max_nodes is not None:
        params["max_nodes"] = _constant(max_nodes)
    plantarch.defineShootType(label, params)


def _grow_base_stem(plantarch, label, nodes=1, age=0.0, internode_fraction=0.1, leaf_fraction=0.1):
    plant_id = plantarch.addPlantInstance(vec3(0, 0, 0), age)
    shoot_id = plantarch.addBaseStemShoot(
        plant_id=plant_id, current_node_number=nodes, base_rotation=AxisRotation(0, 0, 0),
        internode_radius=0.002, internode_length_max=0.04,
        internode_length_scale_factor_fraction=internode_fraction,
        leaf_scale_factor_fraction=leaf_fraction, radius_taper=1.0, shoot_type_label=label)
    return plant_id, shoot_id


def _leaf_area(context, object_ids):
    return sum(context.getObjectArea(oid) for oid in object_ids)


def _polyline_length(points):
    return sum(math.dist(points[i].to_list(), points[i + 1].to_list()) for i in range(len(points) - 1))


def _horizontal_azimuth_deg(v):
    return math.degrees(math.atan2(v.y, v.x))


def _angle_delta_deg(a, b):
    """Signed difference b - a folded to [0, 360)."""
    return (b - a) % 360.0


# =============================================================================
# Pure-Python validation
# =============================================================================

PER_PHYTOMER_METHODS = [
    ("setInternodeMaxLength", (0.05,)),
    ("scaleInternodeMaxLength", (0.5,)),
    ("scaleLeafPrototypeScale", (0.5,)),
    ("getPhytomerAge", ()),
    ("getInternodeLength", ()),
    ("getInternodeRadius", ()),
    ("getInternodeNodePositions", ()),
    ("getInternodeAxisVector", (1.0,)),
    ("getPetioleAxisVector", (0.0, 0)),
    ("getPetioleVertices", (0,)),
    ("getPetioleRadii", (0,)),
    ("getPhytomerLeafObjectIDs", ()),
    ("getLeafBasePosition", (0, 0)),
]


@pytest.mark.cross_platform
class TestPhytomerBindingValidation:
    """Argument validation for the helios-core 1.3.88 additions (no native library needed)."""

    def _pa(self):
        return PlantArchitecture.__new__(PlantArchitecture)

    @pytest.mark.parametrize("method,extra", PER_PHYTOMER_METHODS)
    @pytest.mark.parametrize("ids", [(-1, 0, 0), (0, -1, 0), (0, 0, -1), (True, 0, 0), (0, 0, 1.5), ("0", 0, 0)])
    def test_rejects_bad_identifiers_positionally(self, method, extra, ids):
        with pytest.raises(ValueError):
            getattr(PlantArchitecture, method)(self._pa(), *ids, *extra)

    @pytest.mark.parametrize("method,extra", PER_PHYTOMER_METHODS)
    def test_rejects_bad_node_index_by_keyword(self, method, extra):
        with pytest.raises(ValueError, match="(?i)node index"):
            getattr(PlantArchitecture, method)(self._pa(), 0, 0, -3, *extra)

    @pytest.mark.parametrize("bad", [0.0, -0.1, float("nan"), float("inf"), "0.1", True, None])
    def test_setInternodeMaxLength_rejects_bad_length(self, bad):
        with pytest.raises(ValueError, match="(?i)length"):
            PlantArchitecture.setInternodeMaxLength(self._pa(), 0, 0, 0, bad)

    @pytest.mark.parametrize("method", ["scaleInternodeMaxLength", "scaleLeafPrototypeScale"])
    @pytest.mark.parametrize("bad", [0.0, -1.0, "2", True, None])
    def test_scales_reject_non_positive_factor(self, method, bad):
        with pytest.raises(ValueError, match="(?i)scale factor"):
            getattr(PlantArchitecture, method)(self._pa(), 0, 0, 0, bad)

    def test_scaleLeafPrototypeScale_rejects_bad_petiole_index(self):
        with pytest.raises(ValueError, match="(?i)petiole index"):
            PlantArchitecture.scaleLeafPrototypeScale(self._pa(), 0, 0, 0, 0.5, petiole_index=-1)

    @pytest.mark.parametrize("method,args", [
        ("getInternodeAxisVector", (-0.1,)),
        ("getInternodeAxisVector", (1.1,)),
        ("getInternodeAxisVector", ("0.5",)),
        ("getPetioleAxisVector", (1.5, 0)),
        ("getPetioleAxisVector", (float("nan"), 0)),
    ])
    def test_axis_vectors_reject_bad_stem_fraction(self, method, args):
        with pytest.raises(ValueError, match="(?i)stem fraction"):
            getattr(PlantArchitecture, method)(self._pa(), 0, 0, 0, *args)

    @pytest.mark.parametrize("method,args", [
        ("getPetioleAxisVector", (0.0, -1)),
        ("getPetioleVertices", (-1,)),
        ("getPetioleRadii", (True,)),
        ("getLeafBasePosition", (-1, 0)),
    ])
    def test_rejects_bad_petiole_index(self, method, args):
        with pytest.raises(ValueError, match="(?i)petiole index"):
            getattr(PlantArchitecture, method)(self._pa(), 0, 0, 0, *args)

    def test_getLeafBasePosition_rejects_bad_leaf_index(self):
        with pytest.raises(ValueError, match="(?i)leaf index"):
            PlantArchitecture.getLeafBasePosition(self._pa(), 0, 0, 0, 0, -2)

    @pytest.mark.parametrize("mean,sd,match", [
        ("137", 0.0, "(?i)mean"),
        (float("nan"), 0.0, "(?i)mean"),
        (137.5, -1.0, "(?i)standard deviation"),
        (137.5, float("inf"), "(?i)standard deviation"),
        (137.5, "0", "(?i)standard deviation"),
    ])
    def test_setShootPhyllotacticAngle_rejects_bad_values(self, mean, sd, match):
        with pytest.raises(ValueError, match=match):
            PlantArchitecture.setShootPhyllotacticAngle(self._pa(), 0, 0, mean, sd)

    def test_setShootPhyllotacticAngle_rejects_bad_ids(self):
        with pytest.raises(ValueError):
            PlantArchitecture.setShootPhyllotacticAngle(self._pa(), -1, 0, 137.5)
        with pytest.raises(ValueError):
            PlantArchitecture.setShootPhyllotacticAngle(self._pa(), 0, "0", 137.5)

    @pytest.mark.parametrize("label", [None, 3, b"mainstem", ""])
    def test_setPhytomerCreationFunction_rejects_bad_label(self, label):
        with pytest.raises(ValueError, match="(?i)shoot type label"):
            PlantArchitecture.setPhytomerCreationFunction(self._pa(), label, None)

    @pytest.mark.parametrize("callback", [3, "fn", object()])
    def test_setPhytomerCreationFunction_rejects_non_callable(self, callback):
        with pytest.raises(ValueError, match="(?i)callable"):
            PlantArchitecture.setPhytomerCreationFunction(self._pa(), "mainstem", callback)

    @pytest.mark.parametrize("method,args", [
        ("getPlantModelLeafInclinationDistribution", (3,)),
        ("doesPlantModelDeclareLeafInclinationDistribution", (None,)),
        ("setPlantModelLeafInclinationDistribution", ("", 1.0, 1.0)),
    ])
    def test_inclination_distribution_rejects_bad_model_name(self, method, args):
        with pytest.raises(ValueError, match="(?i)model name"):
            getattr(PlantArchitecture, method)(self._pa(), *args)

    @pytest.mark.parametrize("mu,nu", [(-1.0, 1.0), (1.0, 0.0), ("1", 1.0), (float("nan"), 1.0)])
    def test_setPlantModelLeafInclinationDistribution_rejects_bad_parameters(self, mu, nu):
        with pytest.raises(ValueError, match="(?i)beta"):
            PlantArchitecture.setPlantModelLeafInclinationDistribution(self._pa(), "cowpea", mu, nu)

    def test_getPlantAvailableNitrogen_rejects_bad_plant_id(self):
        with pytest.raises(ValueError, match="(?i)plant id"):
            PlantArchitecture.getPlantAvailableNitrogen(self._pa(), -1)

    def test_1388_guard(self):
        with patch.object(plantarch_wrapper, '_PLANTARCHITECTURE_1388_AVAILABLE', False):
            with pytest.raises(RuntimeError, match="1.3.88"):
                plantarch_wrapper.getPhytomerAge(None, 0, 0, 0)
            with pytest.raises(RuntimeError, match="1.3.88"):
                plantarch_wrapper.setShootPhyllotacticAngle(None, 0, 0, 137.5, 0.0)
            with pytest.raises(RuntimeError, match="1.3.88"):
                plantarch_wrapper.setPhytomerCreationFunction(None, "mainstem", None)
            with pytest.raises(RuntimeError, match="1.3.88"):
                plantarch_wrapper.getPlantAvailableNitrogen(None, 0)

    def test_expected_1388_symbols_are_registered(self):
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture native functions not available")
        for name in ("setPhytomerCreationFunction", "setInternodeMaxLength", "scaleInternodeMaxLength",
                     "scaleLeafPrototypeScale", "scaleLeafPrototypeScaleAt", "setShootPhyllotacticAngle",
                     "getPhytomerAge", "getInternodeLength", "getInternodeRadius",
                     "getInternodeNodePositions", "getInternodeAxisVector", "getPetioleAxisVector",
                     "getPetioleVertices", "getPetioleRadii", "getPhytomerLeafObjectIDs",
                     "getLeafBasePosition", "getPlantModelLeafInclinationDistribution",
                     "setPlantModelLeafInclinationDistribution",
                     "doesPlantModelDeclareLeafInclinationDistribution", "getPlantAvailableNitrogen"):
            assert hasattr(plantarch_wrapper.helios_lib, name), f"native library is missing {name}"


@pytest.mark.cross_platform
class TestNitrogenParameterFields:
    """NitrogenParameters mirrors the helios-core 1.3.88 struct."""

    def test_new_fields_present_with_native_defaults(self):
        d = NitrogenParameters().to_dict()
        assert d["leaf_remobilization_rate"] == pytest.approx(0.03)
        assert d["leaf_senescence_duration_fraction"] == pytest.approx(0.25)
        assert d["stress_senescence_advance_fraction"] == pytest.approx(0.30)

    def test_removed_field_is_gone(self):
        assert "remobilization_age_threshold" not in NitrogenParameters().to_dict()
        assert not hasattr(NitrogenParameters(), "remobilization_age_threshold")

    def test_setPlantNitrogenParameters_rejects_an_unknown_key(self):
        """A dict written for helios-core 1.3.87 must not have its removed field silently dropped."""
        pa = PlantArchitecture.__new__(PlantArchitecture)
        with pytest.raises(ValueError, match="remobilization_age_threshold"):
            PlantArchitecture.setPlantNitrogenParameters(pa, 0, {"remobilization_age_threshold": 0.7})


# =============================================================================
# Native: phytomer creation callback
# =============================================================================

@pytest.mark.native_only
class TestPhytomerCreationCallback:

    def test_fires_once_per_new_phytomer_with_its_identity(self):
        _require_plantarch()
        calls = []

        def record(plant_id, shoot_id, node_index, shoot_node_index, parent_shoot_node_index,
                   shoot_max_nodes, plant_age):
            calls.append((plant_id, shoot_id, node_index, shoot_node_index, shoot_max_nodes, plant_age))

        with Context() as context:
            context.seedRandomGenerator(3)
            with PlantArchitecture(context) as plantarch:
                plantarch.disableMessages()
                plantarch.loadPlantModelFromLibrary("tomato")
                _straight_tomato_type(plantarch, "probe", max_nodes=6)
                plantarch.setPhytomerCreationFunction("probe", record)
                plant_id, shoot_id = _grow_base_stem(plantarch, "probe", nodes=1)
                assert len(calls) == 1, "the initial phytomer must invoke the callback"
                plantarch.breakPlantDormancy(plant_id)
                plantarch.advanceTime(12.0, plant_id=plant_id)

                node_count = plantarch.getShoot(plant_id, shoot_id)["node_count"]
                assert node_count > 1, "the probe shoot did not grow"
                assert len(calls) == node_count
                assert [c[2] for c in calls] == list(range(node_count))
                assert all(c[0] == plant_id and c[1] == shoot_id for c in calls)
                assert all(c[4] == 6 for c in calls)
                ages = [c[5] for c in calls]
                assert ages == sorted(ages) and ages[-1] > 0.0

    def test_scaling_from_the_callback_shrinks_new_leaves(self):
        _require_plantarch()

        def grown_leaf_area(callback):
            with Context() as context:
                context.seedRandomGenerator(11)
                with PlantArchitecture(context) as plantarch:
                    plantarch.disableMessages()
                    plantarch.loadPlantModelFromLibrary("tomato")
                    _straight_tomato_type(plantarch, "probe", max_nodes=4)
                    plantarch.setPhytomerCreationFunction(
                        "probe", lambda p, s, n, *rest: callback(plantarch, p, s, n))
                    plant_id, _ = _grow_base_stem(plantarch, "probe", nodes=3, leaf_fraction=1.0)
                    return _leaf_area(context, plantarch.getPlantLeafObjectIDs(plant_id))

        def halve(plantarch, p, s, n):
            plantarch.scaleLeafPrototypeScale(p, s, n, 0.5)

        # The control installs a do-nothing callback so both runs draw the same random leaves.
        control = grown_leaf_area(lambda *args: None)
        scaled = grown_leaf_area(halve)
        assert control > 0.0
        assert scaled == pytest.approx(0.25 * control, rel=0.02)

    def test_none_clears_a_python_callback(self):
        _require_plantarch()
        calls = []
        with Context() as context:
            with PlantArchitecture(context) as plantarch:
                plantarch.disableMessages()
                plantarch.loadPlantModelFromLibrary("tomato")
                _straight_tomato_type(plantarch, "probe")
                plantarch.setPhytomerCreationFunction("probe", lambda *a: calls.append(a))
                plantarch.setPhytomerCreationFunction("probe", None)
                _grow_base_stem(plantarch, "probe", nodes=3)
                assert calls == []

    @staticmethod
    def _first_internode_length(label_setup):
        """Length of a fully-elongated first internode on a tomato-typed base stem built at age 0."""
        with Context() as context:
            with PlantArchitecture(context) as plantarch:
                plantarch.disableMessages()
                plantarch.loadPlantModelFromLibrary("tomato")
                label = label_setup(plantarch)
                plant_id, shoot_id = _grow_base_stem(plantarch, label, nodes=2, internode_fraction=1.0)
                return plantarch.getInternodeLength(plant_id, shoot_id, 0)

    def test_none_clears_the_library_tomato_function(self):
        """At plant age 0 TomatoPhytomerCreationFunction scales every new internode to 0.7 of its target."""
        _require_plantarch()

        def cleared(plantarch):
            plantarch.setPhytomerCreationFunction("mainstem", None)
            return "mainstem"

        assert self._first_internode_length(lambda pa: "mainstem") == pytest.approx(0.7 * 0.04, rel=1e-3)
        assert self._first_internode_length(cleared) == pytest.approx(0.04, rel=1e-3)

    def test_redefining_an_existing_label_keeps_the_callback(self):
        _require_plantarch()
        calls = []
        with Context() as context:
            with PlantArchitecture(context) as plantarch:
                plantarch.disableMessages()
                plantarch.loadPlantModelFromLibrary("tomato")
                _straight_tomato_type(plantarch, "probe")
                plantarch.setPhytomerCreationFunction("probe", lambda *a: calls.append(a))
                plantarch.defineShootType("probe", plantarch.getCurrentShootParameters("probe"))
                _grow_base_stem(plantarch, "probe", nodes=2)
                assert len(calls) == 2

    def test_a_new_label_from_a_dict_starts_without_one(self):
        """JSON carries no function pointers, so neither a Python callback nor the library function carries over."""
        _require_plantarch()
        calls = []
        with Context() as context:
            with PlantArchitecture(context) as plantarch:
                plantarch.disableMessages()
                plantarch.loadPlantModelFromLibrary("tomato")
                plantarch.setPhytomerCreationFunction("mainstem", lambda *a: calls.append(a))
                plantarch.defineShootType("derived", plantarch.getCurrentShootParameters("mainstem"))
                _grow_base_stem(plantarch, "derived", nodes=2)
                assert calls == []

    def test_a_new_label_does_not_inherit_the_library_function(self):
        _require_plantarch()

        def derived(plantarch):
            plantarch.defineShootType("derived", plantarch.getCurrentShootParameters("mainstem"))
            return "derived"

        def redefined(plantarch):
            plantarch.defineShootType("mainstem", plantarch.getCurrentShootParameters("mainstem"))
            return "mainstem"

        assert self._first_internode_length(derived) == pytest.approx(0.04, rel=1e-3)
        assert self._first_internode_length(redefined) == pytest.approx(0.7 * 0.04, rel=1e-3), (
            "redefining an existing label keeps the library function")

    def test_callback_survives_the_instance_that_set_it_being_destroyed(self):
        _require_plantarch()
        first, second = [], []
        with Context() as context:
            with PlantArchitecture(context) as plantarch:
                plantarch.disableMessages()
                plantarch.loadPlantModelFromLibrary("tomato")
                _straight_tomato_type(plantarch, "probe")
                plantarch.setPhytomerCreationFunction("probe", lambda *a: first.append(a))
            with PlantArchitecture(context) as plantarch:
                plantarch.disableMessages()
                plantarch.loadPlantModelFromLibrary("tomato")
                _straight_tomato_type(plantarch, "probe")
                plantarch.setPhytomerCreationFunction("probe", lambda *a: second.append(a))
                _grow_base_stem(plantarch, "probe", nodes=2)
        assert first == [] and len(second) == 2


def _run_in_subprocess(source):
    env = dict(os.environ, PYTHONPATH=REPO_ROOT)
    return subprocess.run([sys.executable, "-c", textwrap.dedent(source)], capture_output=True,
                          text=True, timeout=300, cwd=REPO_ROOT, env=env)


_CALLBACK_RAISES_PRELUDE = """
    import sys
    sys.path.insert(0, 'tests')
    from pyhelios import Context, PlantArchitecture
    from test_plantarchitecture_phytomer import _straight_tomato_type, _grow_base_stem

    class Boom(Exception):
        pass

    def explode(plant_id, shoot_id, node_index, *rest):
        if node_index >= FAIL_AT:
            raise Boom(f"callback failed at node {node_index}")

    context = Context()
    plantarch = PlantArchitecture(context)
    plantarch.disableMessages()
    plantarch.loadPlantModelFromLibrary("tomato")
    _straight_tomato_type(plantarch, "probe", max_nodes=8)
    plantarch.setPhytomerCreationFunction("probe", explode)
"""


@pytest.mark.native_only
class TestPhytomerCreationCallbackErrors:
    """A Python exception in the callback must surface from the call that grew the phytomer."""

    def test_exception_surfaces_from_advanceTime(self):
        _require_plantarch()
        result = _run_in_subprocess("FAIL_AT = 1\n" + textwrap.dedent(_CALLBACK_RAISES_PRELUDE) + textwrap.dedent("""
            plant_id, _ = _grow_base_stem(plantarch, "probe", nodes=1)
            plantarch.breakPlantDormancy(plant_id)
            try:
                plantarch.advanceTime(10.0, plant_id=plant_id)
            except Boom as e:
                print("RAISED", e)
                sys.exit(0)
            print("NOT RAISED")
            sys.exit(3)
        """))
        assert result.returncode == 0, f"exit {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        assert "RAISED callback failed at node 1" in result.stdout

    def test_exception_surfaces_from_addBaseStemShoot(self):
        _require_plantarch()
        result = _run_in_subprocess("FAIL_AT = 0\n" + textwrap.dedent(_CALLBACK_RAISES_PRELUDE) + textwrap.dedent("""
            try:
                _grow_base_stem(plantarch, "probe", nodes=2)
            except Boom as e:
                print("RAISED", e)
                sys.exit(0)
            print("NOT RAISED")
            sys.exit(3)
        """))
        assert result.returncode == 0, f"exit {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        assert "RAISED callback failed at node 0" in result.stdout

    def test_the_next_call_is_not_poisoned_by_a_handled_callback_error(self):
        _require_plantarch()
        result = _run_in_subprocess("FAIL_AT = 0\n" + textwrap.dedent(_CALLBACK_RAISES_PRELUDE) + textwrap.dedent("""
            try:
                _grow_base_stem(plantarch, "probe", nodes=1)
            except Boom:
                pass
            plantarch.setPhytomerCreationFunction("probe", None)
            plant_id, shoot_id = _grow_base_stem(plantarch, "probe", nodes=2)
            print("NODES", plantarch.getShoot(plant_id, shoot_id)["node_count"])
        """))
        assert result.returncode == 0, f"exit {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        assert "NODES 2" in result.stdout


# =============================================================================
# Native: per-phytomer growth targets, phyllotaxy and readouts
# =============================================================================

@pytest.fixture
def tomato():
    """A context and plant architecture with a 4-node straight tomato stem, fully elongated."""
    _require_plantarch()
    with Context() as context:
        context.seedRandomGenerator(7)
        with PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("tomato")
            plantarch.setPhytomerCreationFunction("mainstem", None)
            _straight_tomato_type(plantarch, "probe", max_nodes=12)
            plant_id, shoot_id = _grow_base_stem(plantarch, "probe", nodes=4, internode_fraction=1.0,
                                                 leaf_fraction=1.0)
            yield context, plantarch, plant_id, shoot_id


@pytest.mark.native_only
class TestPerPhytomerGrowthTargets:

    def test_setInternodeMaxLength_shortens_an_elongated_internode(self, tomato):
        _, plantarch, p, s = tomato
        before = plantarch.getInternodeLength(p, s, 1)
        plantarch.setInternodeMaxLength(p, s, 1, 0.5 * before)
        assert plantarch.getInternodeLength(p, s, 1) == pytest.approx(0.5 * before, rel=1e-3)
        assert plantarch.getInternodeLength(p, s, 2) == pytest.approx(before, rel=1e-3)

    def test_setInternodeMaxLength_raises_the_target_for_growth(self, tomato):
        _, plantarch, p, s = tomato
        before = plantarch.getInternodeLength(p, s, 0)
        plantarch.setInternodeMaxLength(p, s, 0, 2.0 * before)
        assert plantarch.getInternodeLength(p, s, 0) == pytest.approx(before, rel=1e-3), (
            "raising the target must not move the present length")
        plantarch.breakPlantDormancy(p)
        plantarch.advanceTime(15.0, plant_id=p)
        assert plantarch.getInternodeLength(p, s, 0) > 1.2 * before

    def test_scaleInternodeMaxLength_halves_an_elongated_internode(self, tomato):
        _, plantarch, p, s = tomato
        before = plantarch.getInternodeLength(p, s, 2)
        plantarch.scaleInternodeMaxLength(p, s, 2, 0.5)
        assert plantarch.getInternodeLength(p, s, 2) == pytest.approx(0.5 * before, rel=1e-3)

    def test_scaleLeafPrototypeScale_rescales_the_blades_now(self, tomato):
        context, plantarch, p, s = tomato
        ids = [oid for petiole in plantarch.getPhytomerLeafObjectIDs(p, s, 1) for oid in petiole]
        other = [oid for petiole in plantarch.getPhytomerLeafObjectIDs(p, s, 2) for oid in petiole]
        area, other_area = _leaf_area(context, ids), _leaf_area(context, other)
        plantarch.scaleLeafPrototypeScale(p, s, 1, 0.5)
        assert _leaf_area(context, ids) == pytest.approx(0.25 * area, rel=1e-3)
        assert _leaf_area(context, other) == pytest.approx(other_area, rel=1e-6)

    def test_scaleLeafPrototypeScale_single_petiole(self, tomato):
        context, plantarch, p, s = tomato
        ids = plantarch.getPhytomerLeafObjectIDs(p, s, 1)[0]
        area = _leaf_area(context, ids)
        plantarch.scaleLeafPrototypeScale(p, s, 1, 2.0, petiole_index=0)
        assert _leaf_area(context, ids) == pytest.approx(4.0 * area, rel=1e-3)

    def test_scaleLeafSizeMax_leaves_the_blades_where_they_are(self, tomato):
        """The contrast with scaleLeafPrototypeScale: only the target moves."""
        context, plantarch, p, s = tomato
        ids = [oid for petiole in plantarch.getPhytomerLeafObjectIDs(p, s, 1) for oid in petiole]
        area = _leaf_area(context, ids)
        plantarch.scaleLeafSizeMax(p, s, 1, 2.0)
        assert _leaf_area(context, ids) == pytest.approx(area, rel=1e-6)

    def test_out_of_range_indices_raise_value_error_naming_the_range(self, tomato):
        _, plantarch, p, s = tomato
        with pytest.raises(ValueError, match=r"(?i)node index 99.*4 phytomers"):
            plantarch.setInternodeMaxLength(p, s, 99, 0.05)
        with pytest.raises(ValueError, match=r"(?i)petiole index 5.*1 petiole"):
            plantarch.scaleLeafPrototypeScale(p, s, 0, 0.5, petiole_index=5)

    def test_missing_plant_raises_plantarchitecture_error(self, tomato):
        _, plantarch, _, s = tomato
        with pytest.raises(PlantArchitectureError):
            plantarch.scaleInternodeMaxLength(9999, s, 0, 0.5)


@pytest.mark.native_only
class TestShootPhyllotacticAngle:

    @staticmethod
    def _azimuths(plantarch, p, s):
        n = plantarch.getShoot(p, s)["node_count"]
        return [_horizontal_azimuth_deg(plantarch.getPetioleAxisVector(p, s, i, 0.0, 0)) for i in range(n)]

    def test_sets_the_next_phytomer_angle_only_on_that_shoot(self):
        _require_plantarch()
        with Context() as context:
            context.seedRandomGenerator(2)
            with PlantArchitecture(context) as plantarch:
                plantarch.disableMessages()
                plantarch.loadPlantModelFromLibrary("tomato")
                _straight_tomato_type(plantarch, "probe", phyllotactic_angle=137.5, max_nodes=12)
                a, sa = _grow_base_stem(plantarch, "probe", nodes=2, internode_fraction=1.0, leaf_fraction=1.0)
                b, sb = _grow_base_stem(plantarch, "probe", nodes=2, internode_fraction=1.0, leaf_fraction=1.0)
                built_a = self._azimuths(plantarch, a, sa)

                plantarch.setShootPhyllotacticAngle(a, sa, 90.0)
                for plant in (a, b):
                    plantarch.breakPlantDormancy(plant)
                plantarch.advanceTime(10.0)

                az_a, az_b = self._azimuths(plantarch, a, sa), self._azimuths(plantarch, b, sb)
                assert len(az_a) > 3 and len(az_b) > 3
                for before, after in zip(built_a, az_a):
                    assert _angle_delta_deg(before, after) == pytest.approx(0.0, abs=1.0) or \
                        _angle_delta_deg(before, after) == pytest.approx(360.0, abs=1.0)
                for i in range(2, len(az_a)):
                    assert _angle_delta_deg(az_a[i - 1], az_a[i]) == pytest.approx(90.0, abs=1.0)
                for i in range(1, len(az_b)):
                    assert _angle_delta_deg(az_b[i - 1], az_b[i]) == pytest.approx(137.5, abs=1.0)
                assert _angle_delta_deg(az_a[0], az_a[1]) == pytest.approx(137.5, abs=1.0)

    def test_standard_deviation_spreads_the_angles(self):
        _require_plantarch()
        with Context() as context:
            context.seedRandomGenerator(4)
            with PlantArchitecture(context) as plantarch:
                plantarch.disableMessages()
                plantarch.loadPlantModelFromLibrary("tomato")
                _straight_tomato_type(plantarch, "probe", max_nodes=20)
                p, s = _grow_base_stem(plantarch, "probe", nodes=1, internode_fraction=1.0, leaf_fraction=1.0)
                plantarch.setShootPhyllotacticAngle(p, s, 120.0, 15.0)
                plantarch.breakPlantDormancy(p)
                plantarch.advanceTime(25.0)
                az = self._azimuths(plantarch, p, s)
                deltas = [_angle_delta_deg(az[i - 1], az[i]) for i in range(1, len(az))]
                assert len(deltas) >= 4
                assert max(deltas) - min(deltas) > 5.0

    def test_missing_shoot_raises(self, tomato):
        _, plantarch, p, _ = tomato
        with pytest.raises(PlantArchitectureError):
            plantarch.setShootPhyllotacticAngle(p, 42, 90.0)


@pytest.mark.native_only
class TestPerPhytomerReadouts:

    def test_age_increases_with_time(self, tomato):
        _, plantarch, p, s = tomato
        before = plantarch.getPhytomerAge(p, s, 0)
        plantarch.breakPlantDormancy(p)
        plantarch.advanceTime(3.0, plant_id=p)
        assert plantarch.getPhytomerAge(p, s, 0) == pytest.approx(before + 3.0, abs=1e-3)

    def test_internode_length_is_the_node_polyline_length(self, tomato):
        _, plantarch, p, s = tomato
        for node in range(4):
            nodes = plantarch.getInternodeNodePositions(p, s, node)
            assert len(nodes) >= 2 and all(isinstance(v, vec3) for v in nodes)
            assert plantarch.getInternodeLength(p, s, node) == pytest.approx(_polyline_length(nodes), rel=1e-4)

    def test_internode_nodes_chain_up_the_shoot(self, tomato):
        _, plantarch, p, s = tomato
        top_of_first = plantarch.getInternodeNodePositions(p, s, 0)[-1]
        base_of_second = plantarch.getInternodeNodePositions(p, s, 1)[0]
        assert math.dist(top_of_first.to_list(), base_of_second.to_list()) < 1e-5

    def test_internode_radius_and_axis(self, tomato):
        _, plantarch, p, s = tomato
        assert plantarch.getInternodeRadius(p, s, 0) > 0.0
        axis = plantarch.getInternodeAxisVector(p, s, 0, 1.0)
        assert math.hypot(axis.x, axis.y, axis.z) == pytest.approx(1.0, abs=1e-4)
        assert axis.z > 0.99, "the probe stem is straight and vertical"

    def test_petiole_vertices_radii_and_length_agree(self, tomato):
        _, plantarch, p, s = tomato
        vertices = plantarch.getPetioleVertices(p, s, 1, 0)
        radii = plantarch.getPetioleRadii(p, s, 1, 0)
        assert len(vertices) >= 2 and len(vertices) == len(radii)
        assert all(r > 0.0 for r in radii)
        assert plantarch.getPetioleLength(p, s, 1, 0) == pytest.approx(_polyline_length(vertices), rel=1e-3)
        axis = plantarch.getPetioleAxisVector(p, s, 1, 0.0, 0)
        assert math.hypot(axis.x, axis.y, axis.z) == pytest.approx(1.0, abs=1e-4)

    def test_leaf_object_ids_partition_the_plant_leaves(self, tomato):
        _, plantarch, p, s = tomato
        per_node = [plantarch.getPhytomerLeafObjectIDs(p, s, n) for n in range(4)]
        flat = [oid for node in per_node for petiole in node for oid in petiole]
        assert sorted(flat) == sorted(plantarch.getPlantLeafObjectIDs(p))
        assert all(len(node) == 1 and len(node[0]) == 7 for node in per_node), "tomato: 1 petiole, 7 leaflets"

    def test_leaf_base_lies_on_its_petiole(self, tomato):
        _, plantarch, p, s = tomato
        vertices = plantarch.getPetioleVertices(p, s, 1, 0)
        for leaf in range(7):
            base = plantarch.getLeafBasePosition(p, s, 1, 0, leaf)
            nearest = min(math.dist(base.to_list(), v.to_list()) for v in vertices)
            assert nearest < 0.25 * _polyline_length(vertices)

    def test_out_of_range_readouts_raise_value_error(self, tomato):
        _, plantarch, p, s = tomato
        with pytest.raises(ValueError, match=r"(?i)node index 4.*4 phytomers"):
            plantarch.getPhytomerAge(p, s, 4)
        with pytest.raises(ValueError, match=r"(?i)petiole index 1.*1 petiole"):
            plantarch.getPetioleVertices(p, s, 0, 1)
        with pytest.raises(ValueError, match=r"(?i)petiole index 1.*1 petiole"):
            plantarch.getPetioleRadii(p, s, 0, 1)
        with pytest.raises(ValueError, match=r"(?i)petiole index 3"):
            plantarch.getPetioleAxisVector(p, s, 0, 0.5, 3)
        with pytest.raises(ValueError, match=r"(?i)leaf index 7.*7 leaves"):
            plantarch.getLeafBasePosition(p, s, 0, 0, 7)


# =============================================================================
# Native: plugin behaviours the tomato port depends on
# =============================================================================

@pytest.mark.native_only
class TestTomatoPortPluginBehaviour:

    def test_one_and_nine_leaflet_types_from_one_dict_grow_on_one_plant(self):
        """Blade caching must key on the leaflet count as well as the prototype identifier.

        A cotyledon type (one leaflet) and a main-stem type (nine leaflets) derived from the
        same library dict share a prototype identifier; before helios-core 1.3.87 this made
        the plugin throw std::out_of_range from advanceTime.
        """
        _require_plantarch()
        with Context() as context:
            context.seedRandomGenerator(1)
            with PlantArchitecture(context) as plantarch:
                plantarch.disableMessages()
                plantarch.loadPlantModelFromLibrary("tomato")
                base = plantarch.getCurrentShootParameters("mainstem")

                grown = copy.deepcopy(base)
                grown["phytomer_parameters"]["leaf"]["leaves_per_petiole"] = _constant(9)
                grown["child_shoot_types"] = {"labels": ["grown_probe"], "probabilities": [1.0]}
                plantarch.defineShootType("grown_probe", grown)

                cotyledon = copy.deepcopy(base)
                cotyledon["phytomer_parameters"]["leaf"]["leaves_per_petiole"] = _constant(1)
                cotyledon["phytomer_parameters"]["petiole"]["petioles_per_internode"] = 2
                cotyledon["max_nodes"] = _constant(1)
                cotyledon["child_shoot_types"] = {"labels": ["grown_probe"], "probabilities": [1.0]}
                plantarch.defineShootType("cotyledon_probe", cotyledon)

                plant_id = plantarch.addPlantInstance(vec3(0, 0, 0), 0.0)
                cot = plantarch.addBaseStemShoot(plant_id, 1, AxisRotation(0, 0, 0), 0.001, 0.01, 1.0, 1.0, 0.0,
                                                 "cotyledon_probe")
                main = plantarch.appendShoot(plant_id, cot, 1, AxisRotation(0, 0, 0.5 * math.pi), 0.001, 0.02,
                                             0.01, 0.01, 0.0, "grown_probe")
                plantarch.breakPlantDormancy(plant_id)
                plantarch.advanceTime(20.0, plant_id=plant_id)

                assert [len(p) for p in plantarch.getPhytomerLeafObjectIDs(plant_id, cot, 0)] == [1, 1]
                n = plantarch.getShoot(plant_id, main)["node_count"]
                assert n > 1
                assert all(len(petiole) == 9 for node in range(n)
                           for petiole in plantarch.getPhytomerLeafObjectIDs(plant_id, main, node))


# =============================================================================
# Native: helios-core 1.3.88 PlantArchitecture additions
# =============================================================================

@pytest.mark.native_only
class TestPlantModelLeafInclinationDistribution:

    def test_cowpea_declares_its_distribution(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            assert plantarch.doesPlantModelDeclareLeafInclinationDistribution("cowpea")
            mu, nu = plantarch.getPlantModelLeafInclinationDistribution("cowpea")
            assert (mu, nu) == (pytest.approx(1.398, abs=1e-4), pytest.approx(1.574, abs=1e-4))

    def test_set_and_clear(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            assert not plantarch.doesPlantModelDeclareLeafInclinationDistribution("bean")
            assert plantarch.getPlantModelLeafInclinationDistribution("bean") == (0.0, 0.0)
            plantarch.setPlantModelLeafInclinationDistribution("bean", 2.0, 1.5)
            assert plantarch.doesPlantModelDeclareLeafInclinationDistribution("bean")
            assert plantarch.getPlantModelLeafInclinationDistribution("bean") == (
                pytest.approx(2.0), pytest.approx(1.5))
            plantarch.setPlantModelLeafInclinationDistribution("cowpea", 0.0, 0.0)
            assert not plantarch.doesPlantModelDeclareLeafInclinationDistribution("cowpea")

    def test_unknown_model_raises(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            with pytest.raises(PlantArchitectureError, match="(?i)does not exist"):
                plantarch.getPlantModelLeafInclinationDistribution("not_a_plant")


@pytest.mark.native_only
class TestPlantAvailableNitrogen:

    def test_fresh_plant_has_an_empty_pool(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("bean")
            plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 10.0)
            assert plantarch.getPlantAvailableNitrogen(plant_id) == 0.0

    def test_missing_plant_raises(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            with pytest.raises(PlantArchitectureError, match="(?i)does not exist"):
                plantarch.getPlantAvailableNitrogen(12345)

    def test_new_nitrogen_fields_round_trip_through_native(self):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            defaults = plantarch.getDefaultNitrogenParameters()
            assert defaults["leaf_remobilization_rate"] == pytest.approx(0.03)
            assert defaults["leaf_senescence_duration_fraction"] == pytest.approx(0.25)
            assert defaults["stress_senescence_advance_fraction"] == pytest.approx(0.30)
            assert "remobilization_age_threshold" not in defaults
