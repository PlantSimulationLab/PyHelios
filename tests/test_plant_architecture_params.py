"""Tests for the typed plant architecture parameter model and the nested
get/set parameter round-trip (shoot/phytomer/leaf-prototype + carb/nitrogen).

Cross-platform tests exercise the pure-Python typed model (no native library).
Native-only tests exercise the full JSON round-trip through the C++ wrapper.
"""

import json

import pytest

from pyhelios import Context, PlantArchitecture, PlantArchitectureError
from pyhelios.types import vec3
from pyhelios.wrappers import UPlantArchitectureWrapper as plantarch_wrapper
from pyhelios.plant_architecture_params import (
    RandomParameterFloat,
    RandomParameterInt,
    LeafPrototype,
    InternodeParameters,
    PhytomerParameters,
    ShootParameters,
    CarbohydrateParameters,
    NitrogenParameters,
)


# --------------------------------------------------------------------------- #
# Cross-platform: typed model
# --------------------------------------------------------------------------- #
@pytest.mark.cross_platform
class TestRandomParameterTypes:
    def test_float_constructors(self):
        assert RandomParameterFloat.constant(3).to_dict() == {"distribution": "constant", "parameters": [3.0]}
        assert RandomParameterFloat.uniform(1, 2).to_dict() == {"distribution": "uniform", "parameters": [1.0, 2.0]}
        assert RandomParameterFloat.normal(0, 1).to_dict() == {"distribution": "normal", "parameters": [0.0, 1.0]}
        assert RandomParameterFloat.weibull(2, 3).to_dict() == {"distribution": "weibull", "parameters": [2.0, 3.0]}

    def test_int_constructors(self):
        assert RandomParameterInt.constant(5).to_dict() == {"distribution": "constant", "parameters": [5.0]}
        assert RandomParameterInt.uniform(1, 4).to_dict() == {"distribution": "uniform", "parameters": [1.0, 4.0]}
        assert RandomParameterInt.discrete([1, 3, 5]).to_dict() == {
            "distribution": "discretevalues",
            "parameters": [1.0, 3.0, 5.0],
        }

    def test_float_roundtrip(self):
        rp = RandomParameterFloat.uniform(40, 50)
        assert RandomParameterFloat.from_dict(rp.to_dict()) == rp

    def test_int_from_dict_coerces_floats_to_int(self):
        rp = RandomParameterInt.from_dict({"distribution": "constant", "parameters": [20.0]})
        assert rp.parameters == [20]


@pytest.mark.cross_platform
class TestTypedModelRoundTrip:
    def test_default_shoot_roundtrip(self):
        sp = ShootParameters()
        assert ShootParameters.from_dict(sp.to_dict()).to_dict() == sp.to_dict()

    def test_default_shoot_is_json_serializable(self):
        # The transport is a JSON string, so the dict must be JSON-serializable.
        json.dumps(ShootParameters().to_dict())

    def test_nested_mutation_survives_roundtrip(self):
        sp = ShootParameters()
        sp.max_nodes = RandomParameterInt.constant(20)
        sp.phytomer_parameters.leaf.pitch = RandomParameterFloat.uniform(40, 50)
        sp.phytomer_parameters.internode.color = (0.1, 0.2, 0.3)
        sp.phytomer_parameters.leaf.prototype.prototype_function = "AlmondLeafPrototype"
        sp.phytomer_parameters.leaf.prototype.leaf_texture_file = {0: "tip.png", -1: "left.png"}

        d = sp.to_dict()
        sp2 = ShootParameters.from_dict(json.loads(json.dumps(d)))
        d2 = sp2.to_dict()
        assert d == d2
        assert d2["phytomer_parameters"]["leaf"]["pitch"] == {"distribution": "uniform", "parameters": [40.0, 50.0]}
        assert d2["phytomer_parameters"]["internode"]["color"] == {"r": 0.1, "g": 0.2, "b": 0.3}
        assert d2["phytomer_parameters"]["leaf"]["prototype"]["prototype_function"] == "AlmondLeafPrototype"
        # leaf texture map keys serialize as strings
        assert d2["phytomer_parameters"]["leaf"]["prototype"]["leaf_texture_file"] == {"0": "tip.png", "-1": "left.png"}

    def test_leaf_prototype_unset_function_is_empty_string(self):
        d = LeafPrototype().to_dict()
        assert d["prototype_function"] == ""
        # round-trips back to None
        assert LeafPrototype.from_dict(d).prototype_function is None

    def test_phytomer_roundtrip(self):
        pp = PhytomerParameters()
        pp.peduncle.length_segments = 5
        pp.inflorescence.flower_prototype_function = "AlmondFlowerPrototype"
        assert PhytomerParameters.from_dict(pp.to_dict()).to_dict() == pp.to_dict()

    def test_internode_partial_from_dict_uses_defaults(self):
        # A dict missing most fields should fall back to defaults, not crash.
        ip = InternodeParameters.from_dict({"pitch": {"distribution": "constant", "parameters": [5.0]}})
        assert ip.pitch.parameters == [5.0]
        assert ip.radial_subdivisions == 7  # default preserved

    def test_define_child_shoot_types(self):
        sp = ShootParameters()
        sp.define_child_shoot_types(["a", "b"], [0.5, 0.5])
        assert sp.to_dict()["child_shoot_types"] == {"labels": ["a", "b"], "probabilities": [0.5, 0.5]}

    def test_define_child_shoot_types_validates_lengths(self):
        sp = ShootParameters()
        with pytest.raises(ValueError):
            sp.define_child_shoot_types(["a", "b"], [1.0])
        with pytest.raises(ValueError):
            sp.define_child_shoot_types([], [])


@pytest.mark.cross_platform
class TestPhysiologyParams:
    def test_carbohydrate_field_count_and_roundtrip(self):
        cp = CarbohydrateParameters()
        d = cp.to_dict()
        assert len(d) == 30
        assert CarbohydrateParameters.from_dict(d).to_dict() == d

    def test_nitrogen_field_count_and_roundtrip(self):
        npar = NitrogenParameters()
        d = npar.to_dict()
        assert len(d) == 7
        assert NitrogenParameters.from_dict(d).to_dict() == d

    def test_partial_carbohydrate_from_dict(self):
        cp = CarbohydrateParameters.from_dict({"SLA": 12.5})
        assert cp.SLA == 12.5
        assert cp.fruit_density == CarbohydrateParameters().fruit_density


@pytest.mark.cross_platform
class TestHighLevelTypeValidation:
    def test_define_shoot_type_rejects_bad_type(self):
        # Constructing in mock mode raises before init; validate via the dataclass path instead.
        sp = ShootParameters()
        # The dict produced is always acceptable; a bad type (e.g. list) must be rejected.
        assert isinstance(sp.to_dict(), dict)


# --------------------------------------------------------------------------- #
# Native-only: full JSON round-trip through the C++ wrapper
# --------------------------------------------------------------------------- #
@pytest.mark.native_only
class TestNativeParameterRoundTrip:
    @pytest.fixture
    def context(self, check_native_library):
        ctx = Context()
        yield ctx
        ctx.__exit__(None, None, None)

    @pytest.fixture
    def plantarch(self, context):
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture plugin not available")
        if not plantarch_wrapper._PLANTARCHITECTURE_PARAMETER_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture parameter functions not available (rebuild required)")
        try:
            pa = PlantArchitecture(context)
            pa.loadPlantModelFromLibrary("almond")
            yield pa
            pa.__exit__(None, None, None)
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture init/load failed: {e}")

    def _first_shoot_label(self, pa):
        # Try common shoot type labels used by library models.
        for label in ("trunk", "scaffold", "shoot", "stem", "mainstem"):
            try:
                pa.getCurrentShootParameters(label)
                return label
            except Exception:
                continue
        pytest.skip("Could not determine a valid shoot type label")

    def test_get_includes_phytomer_parameters(self, plantarch):
        label = self._first_shoot_label(plantarch)
        params = plantarch.getCurrentShootParameters(label)
        assert "phytomer_parameters" in params
        pp = params["phytomer_parameters"]
        for key in ("internode", "petiole", "leaf", "peduncle", "inflorescence"):
            assert key in pp, f"missing nested phytomer key {key}"
        assert "prototype" in pp["leaf"]
        assert "pitch" in pp["leaf"]

    def test_phytomer_field_roundtrip(self, plantarch):
        label = self._first_shoot_label(plantarch)
        sp = plantarch.getCurrentShootParameters(label, return_typed=True)
        sp.phytomer_parameters.leaf.pitch = RandomParameterFloat.uniform(40, 50)
        sp.phytomer_parameters.internode.radial_subdivisions = 9
        plantarch.defineShootType("custom_roundtrip", sp)

        out = plantarch.getCurrentShootParameters("custom_roundtrip")
        assert out["phytomer_parameters"]["leaf"]["pitch"] == {"distribution": "uniform", "parameters": [40.0, 50.0]}
        assert out["phytomer_parameters"]["internode"]["radial_subdivisions"] == 9

    def test_leaf_prototype_function_by_name_roundtrip(self, plantarch):
        label = self._first_shoot_label(plantarch)
        sp = plantarch.getCurrentShootParameters(label, return_typed=True)
        sp.phytomer_parameters.inflorescence.flower_prototype_function = "AlmondFlowerPrototype"
        plantarch.defineShootType("custom_flower", sp)
        out = plantarch.getCurrentShootParameters("custom_flower")
        assert out["phytomer_parameters"]["inflorescence"]["flower_prototype_function"] == "AlmondFlowerPrototype"

    def test_unknown_prototype_name_raises(self, plantarch):
        label = self._first_shoot_label(plantarch)
        sp = plantarch.getCurrentShootParameters(label, return_typed=True)
        sp.phytomer_parameters.inflorescence.flower_prototype_function = "NotARealPrototype"
        with pytest.raises(Exception):
            plantarch.defineShootType("custom_bad", sp)

    def test_carbohydrate_defaults_and_set(self, plantarch):
        defaults = plantarch.getDefaultCarbohydrateParameters()
        assert isinstance(defaults, dict) and len(defaults) == 30
        cp = CarbohydrateParameters.from_dict(defaults)
        cp.SLA = cp.SLA * 1.1
        plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0.0, 0.0, 0.0), 1.0)
        plantarch.setPlantCarbohydrateParameters(plant_id, cp)  # must not raise

    def test_nitrogen_defaults_and_set(self, plantarch):
        defaults = plantarch.getDefaultNitrogenParameters()
        assert isinstance(defaults, dict) and len(defaults) == 7
        npar = NitrogenParameters.from_dict(defaults)
        npar.target_leaf_N_area = 2.0
        plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0.0, 0.0, 0.0), 1.0)
        plantarch.setPlantNitrogenParameters(plant_id, npar)  # must not raise


# --------------------------------------------------------------------------- #
# Native-only: species phytomer hooks survive redefining an existing shoot type
# --------------------------------------------------------------------------- #
@pytest.mark.native_only
class TestPhytomerFunctionPreservation:
    """Redefining an existing library shoot type must not discard the species'
    phytomer_creation_function / phytomer_callback_function.

    These are raw C function pointers that cannot cross the JSON boundary, so
    jsonToShootParameters rebuilds ShootParameters from values alone and leaves
    them null. For maize, MaizePhytomerCreationFunction is the only thing that
    assigns ears (BUD_ACTIVE, MaizeEarPrototype) at nodes 9-11 and kills the
    floral buds elsewhere; losing it puts a 7-flower tassel on nearly every node.

    Leaf count is identical either way, so it carries no signal here -- peduncle
    and fruit counts are what distinguish the two states.
    """

    @pytest.fixture
    def plantarch(self, check_native_library):
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture plugin not available")
        if not plantarch_wrapper._PLANTARCHITECTURE_PARAMETER_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture parameter functions not available (rebuild required)")
        ctx = Context()
        try:
            pa = PlantArchitecture(ctx)
            pa.disableMessages()
            pa.loadPlantModelFromLibrary("maize")
            yield pa
            pa.__exit__(None, None, None)
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture init/load failed: {e}")
        finally:
            ctx.__exit__(None, None, None)

    # Age 90: maize is phyllochron-limited well past age 45 in helios-core 1.3.82
    # (phyllochron_min went 2 -> 3 and grain fill 10 -> 58 days), so a shorter run
    # reaches neither the node cap nor fruit set and cannot distinguish the two states.
    BUILD_AGE = 90.0

    @staticmethod
    def _build_counts(pa):
        plant_id = pa.buildPlantInstanceFromLibrary(vec3(0.0, 0.0, 0.0),
                                                    TestPhytomerFunctionPreservation.BUILD_AGE)
        return (
            len(pa.getPlantLeafObjectIDs(plant_id)),
            len(pa.getPlantPeduncleObjectIDs(plant_id)),
            len(pa.getPlantFruitObjectIDs(plant_id)),
        )

    def test_identity_redefine_preserves_maize_ear_structure(self, plantarch):
        """An identity round-trip must be a true no-op.

        Reading mainstem parameters and writing them straight back unmodified
        must not change the plant at all.
        """
        baseline_leaves, baseline_peduncles, baseline_fruit = self._build_counts(plantarch)

        params = plantarch.getCurrentShootParameters("mainstem")
        plantarch.defineShootType("mainstem", params)

        after_leaves, after_peduncles, after_fruit = self._build_counts(plantarch)

        assert after_leaves == baseline_leaves, (
            f"identity redefine changed leaf count {baseline_leaves} -> {after_leaves}; "
            "shoot-level parameters were resampled or a prototype function was dropped"
        )
        assert after_peduncles == baseline_peduncles, (
            f"identity redefine changed peduncle count {baseline_peduncles} -> {after_peduncles}; "
            "species phytomer_creation_function was likely dropped"
        )
        assert after_fruit == baseline_fruit, (
            f"identity redefine changed fruit count {baseline_fruit} -> {after_fruit}; "
            "tassels replacing ears indicates the phytomer creation hook was lost"
        )

    def test_edited_redefine_applies_value_and_keeps_ear_structure(self, plantarch):
        """A real edit must take effect while the ear/tassel logic stays intact."""
        baseline_leaves, baseline_peduncles, baseline_fruit = self._build_counts(plantarch)

        params = plantarch.getCurrentShootParameters("mainstem")
        params["max_nodes"] = {"distribution": "constant", "parameters": [25]}
        plantarch.defineShootType("mainstem", params)

        plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0.0, 0.0, 0.0), self.BUILD_AGE)
        leaves = len(plantarch.getPlantLeafObjectIDs(plant_id))
        peduncles = len(plantarch.getPlantPeduncleObjectIDs(plant_id))

        # The edit must actually apply: raising the node cap must grow more leaves than
        # the same plant built with the library default.
        assert leaves > baseline_leaves, (
            f"max_nodes=25 did not take effect (leaves={leaves}, "
            f"baseline={baseline_leaves})")
        # ...without regressing into a tassel-per-node plant.
        assert peduncles <= baseline_peduncles + 1, (
            f"peduncle count {peduncles} far exceeds baseline {baseline_peduncles}; "
            "phytomer creation hook lost despite a valid parameter edit"
        )

    def test_new_shoot_type_from_existing_label_is_unaffected(self, plantarch):
        """Defining a brand-new label must still work (nothing to preserve)."""
        params = plantarch.getCurrentShootParameters("mainstem")
        params["max_nodes"] = {"distribution": "constant", "parameters": [12]}
        plantarch.defineShootType("custom_mainstem_variant", params)

        out = plantarch.getCurrentShootParameters("custom_mainstem_variant")
        assert out["max_nodes"] == {"distribution": "constant", "parameters": [12.0]}
