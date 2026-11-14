"""
Tests for the helios-core 1.3.97 PlantArchitecture changes that reach the Python API:
appendShootFromNodePositions(), the leaf stalk arguments of setPetioleLeafGeometry(),
canReshapeLeafInPlace(), negative midrib_fold_fraction, the "cucumber" library model, the olive
trunk_height build parameter and the revised apple / apple_fruitingwall trunk_height ranges.
"""

import contextlib
import math
import sys
from unittest.mock import patch

import pytest

from pyhelios import Context, PlantArchitecture, PlantArchitectureError
from pyhelios.types import vec3
from pyhelios.wrappers import UPlantArchitectureWrapper as plantarch_wrapper
from pyhelios.wrappers.DataTypes import AxisRotation

from tests.test_plantarchitecture_phytomer import _require_plantarch


# The pyhelios.PlantArchitecture module, not the class: pyhelios re-exports the class under the
# module's name, so a patch("pyhelios.PlantArchitecture.<name>") string target resolves to the
# class on Python 3.10, whose mock walks the path with getattr.
_PLANTARCHITECTURE_MODULE = sys.modules[PlantArchitecture.__module__]


def _require_1397():
    _require_plantarch()
    if not plantarch_wrapper._PLANTARCHITECTURE_1397_AVAILABLE:
        pytest.skip("native library predates helios-core 1.3.97; rebuild required")


def _pa_without_native():
    plantarch = PlantArchitecture.__new__(PlantArchitecture)
    plantarch._plantarch_ptr = None
    plantarch.context = None
    return plantarch


def _first_leafy_phytomer(plantarch, plant_id, shoot_id=0):
    for node in range(plantarch.getShootNodeCount(plant_id, shoot_id)):
        petioles = plantarch.getPhytomerLeafObjectIDs(plant_id, shoot_id, node)
        if petioles and petioles[0]:
            return node, petioles[0]
    pytest.fail("no phytomer with leaves on the main shoot; assertions would be vacuous")


# --------------------------------------------------------------------------- #
# Pure Python
# --------------------------------------------------------------------------- #
@pytest.mark.cross_platform
class TestPlantArch1397Validation:

    def test_negative_midrib_fold_fraction_reaches_the_native_call(self):
        """-1..1 is accepted since helios-core 1.3.97; the Python check used to reject negatives."""
        pa = _pa_without_native()
        pa._check_context_alive = lambda: None
        with patch.object(plantarch_wrapper, "setPetioleLeafShape") as native, \
                patch.object(_PLANTARCHITECTURE_MODULE, "_plantarchitecture_working_directory", contextlib.nullcontext):
            PlantArchitecture.setPetioleLeafShape(pa, 0, 0, 0, 0, 0.5, 0.0, 0.0, -0.5)
            PlantArchitecture.setPetioleLeafShape(pa, 0, 0, 0, 0, 0.5, 0.0, 0.0, -1.0)
        assert native.call_count == 2
        assert native.call_args_list[0].args[-1] == pytest.approx(-0.5)

    def test_midrib_fold_fraction_outside_minus_one_to_one_is_rejected(self):
        pa = _pa_without_native()
        for value in (-1.01, 1.01):
            with pytest.raises(ValueError, match="between -1 and 1"):
                PlantArchitecture.setPetioleLeafShape(pa, 0, 0, 0, 0, 0.5, 0.0, 0.0, value)

    def test_append_shoot_validates_arguments(self):
        pa = _pa_without_native()
        path = [vec3(0, 0, 0), vec3(0, 0, 0.1)]
        with pytest.raises(ValueError, match="Parent shoot ID"):
            PlantArchitecture.appendShootFromNodePositions(pa, 0, -1, path, [0.01, 0.01], "stem")
        with pytest.raises(ValueError, match="vec3"):
            PlantArchitecture.appendShootFromNodePositions(pa, 0, 0, [(0, 0, 0), (0, 0, 0.1)], [0.01, 0.01], "stem")
        with pytest.raises(ValueError, match="positive"):
            PlantArchitecture.appendShootFromNodePositions(pa, 0, 0, path, [0.01, 0.0], "stem")
        with pytest.raises(ValueError, match="empty"):
            PlantArchitecture.appendShootFromNodePositions(pa, 0, 0, path, [0.01, 0.01], " ")
        with pytest.raises(ValueError, match="empty"):
            PlantArchitecture.appendShootFromNodePositions(pa, 0, 0, path, [0.01, 0.01], "stem",
                                                           growth_shoot_type_label="")

    def test_leaf_stalk_arguments_are_validated(self):
        pa = _pa_without_native()
        bases = [vec3(0, 0, 0), vec3(0.01, 0, 0)]
        rotations = [AxisRotation(0, 0, 0)] * 2
        sizes = [0.05, 0.05]
        with pytest.raises(ValueError, match="one entry per leaf"):
            PlantArchitecture.setPetioleLeafGeometry(pa, 0, 0, 0, 0, bases, rotations, sizes,
                                                     leaf_stalk_lengths=[0.01])
        with pytest.raises(ValueError, match="positive"):
            PlantArchitecture.setPetioleLeafGeometry(pa, 0, 0, 0, 0, bases, rotations, sizes,
                                                     leaf_stalk_lengths=[0.01, 0.0])
        with pytest.raises(ValueError, match="vec3"):
            PlantArchitecture.setPetioleLeafGeometry(pa, 0, 0, 0, 0, bases, rotations, sizes,
                                                     leaf_stalk_bases=[vec3(0, 0, 0), (0, 0, 0)])
        with pytest.raises(ValueError, match="one entry per leaf"):
            PlantArchitecture.setPetioleLeafGeometry(pa, 0, 0, 0, 0, bases, rotations, sizes,
                                                     leaf_stalk_bases=[vec3(0, 0, 0)])

    def test_can_reshape_requires_leaf_shape_values(self):
        with pytest.raises(ValueError, match="LeafShapeValues"):
            PlantArchitecture.canReshapeLeafInPlace(_pa_without_native(), 0, 0, 0, 0, 0, {"roll_fraction": 0.5})

    @pytest.mark.parametrize("call", [
        lambda: plantarch_wrapper.appendShootFromNodePositions(None, 0, 0, [[0, 0, 0], [0, 0, 1]], [1, 1], "s"),
        lambda: plantarch_wrapper.canReshapeLeafInPlace(None, 0, 0, 0, 0, 0, [0.0] * 12, [1, 1]),
        lambda: plantarch_wrapper.setPetioleLeafGeometry(None, 0, 0, 0, 0, [[0, 0, 0]], [[0, 0, 0]], [0.1],
                                                         leaf_stalk_lengths=[0.01]),
        lambda: plantarch_wrapper.setPetioleLeafGeometry(None, 0, 0, 0, 0, [[0, 0, 0]], [[0, 0, 0]], [0.1],
                                                         leaf_stalk_bases=[[0, 0, 0]]),
    ])
    def test_wrappers_require_a_1397_library(self, call, monkeypatch):
        """An older native library raises instead of calling a symbol with no argtypes set,
        or silently dropping the stalk arguments it does not know."""
        monkeypatch.setattr(plantarch_wrapper, "_PLANTARCHITECTURE_FUNCTIONS_AVAILABLE", True)
        monkeypatch.setattr(plantarch_wrapper, "_PLANTARCHITECTURE_1385_AVAILABLE", True)
        monkeypatch.setattr(plantarch_wrapper, "_PLANTARCHITECTURE_1397_AVAILABLE", False)
        with pytest.raises(NotImplementedError, match="1.3.97"):
            call()


# --------------------------------------------------------------------------- #
# Native
# --------------------------------------------------------------------------- #
@pytest.mark.native_only
class TestPlantArch1397Library:

    def test_1397_symbols_are_registered(self):
        """A symbol-name typo would otherwise make every 1.3.97 test skip instead of fail."""
        _require_plantarch()
        assert plantarch_wrapper._PLANTARCHITECTURE_1397_AVAILABLE is True, (
            "helios-core 1.3.97 PlantArchitecture symbols missing; rebuild with "
            "'build_scripts/build_helios --clean'")

    def test_cucumber_is_a_library_model_and_builds(self):
        _require_1397()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            assert "cucumber" in plantarch.getAvailablePlantModels()
            assert plantarch.getPlantModelBuildParameterNames("cucumber") == []
            plantarch.loadPlantModelFromLibrary("cucumber")
            assert "main" in plantarch.listShootTypeLabels()
            plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 20.0)
            assert plantarch.getPlantName(plant_id) == "cucumber"
            assert plantarch.getPlantLeafObjectIDs(plant_id), "cucumber at age 20 built no leaves"
            assert plantarch.getShootNodeCount(plant_id, 0) > 5

    def test_olive_accepts_trunk_height(self):
        _require_1397()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            assert plantarch.getPlantModelBuildParameterNames("olive") == ["trunk_height"]
            plantarch.loadPlantModelFromLibrary("olive")

            def trunk_top(height):
                plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 0.0,
                                                                   build_parameters={"trunk_height": height})
                return max(v[2] for v in plantarch.getShootInternodeVertices(plant_id, 0))

            low, high = trunk_top(0.3), trunk_top(1.2)
            assert low == pytest.approx(0.3, abs=0.06)
            assert high == pytest.approx(1.2, abs=0.06)

            with pytest.raises(PlantArchitectureError, match="trunk_height"):
                plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 0.0, build_parameters={"trunk_height": 1.6})

    def test_apple_builds_a_tall_trunk(self):
        """apple with trunk_height above 0.8 m failed inside addBaseStemShoot() before 1.3.97."""
        _require_1397()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("apple")
            plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 0.0,
                                                               build_parameters={"trunk_height": 2.0})
            # Native's own test allows 15%: the trunk is whole internodes and leans slightly.
            assert plantarch.getPlantStemHeight(plant_id) == pytest.approx(2.0, rel=0.15)

    def test_apple_fruitingwall_trunk_height_upper_limit_is_one_meter(self):
        _require_1397()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("apple_fruitingwall")
            with pytest.raises(PlantArchitectureError, match="trunk_height"):
                plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 0.0, build_parameters={"trunk_height": 1.5})


@pytest.mark.native_only
class TestPlantArch1397Reconstruction:
    """appendShootFromNodePositions and measured leaflet stalks, on bean (whose leaflets carry stalks)."""

    PATH = [vec3(0.0, 0.0, 0.0), vec3(0.0, 0.0, 0.1), vec3(0.02, 0.0, 0.198), vec3(0.05, 0.01, 0.293)]
    RADII = [0.006, 0.005, 0.004, 0.003]
    # Bean's creation hook scales new internodes by min(1, 0.2 + 0.8*age/10); age 10 makes it 1.
    AGE = 10.0

    @pytest.fixture
    def bean(self):
        _require_1397()
        with Context() as context, PlantArchitecture(context) as pa:
            pa.disableMessages()
            pa.loadPlantModelFromLibrary("bean")
            yield context, pa

    def _stem(self, plantarch):
        plant_id = plantarch.addPlantInstance(vec3(0, 0, 0), self.AGE)
        stem = plantarch.addShootFromNodePositions(plant_id, -1, 0, self.PATH, self.RADII, "trifoliate")
        return plant_id, stem

    def test_appended_shoot_continues_the_parent_axis(self, bean):
        context, plantarch = bean
        plant_id, stem = self._stem(plantarch)
        tip = self.PATH[-1]
        path = [tip, vec3(tip.x + 0.02, tip.y, tip.z + 0.1), vec3(tip.x + 0.03, tip.y, tip.z + 0.2)]
        shoot = plantarch.appendShootFromNodePositions(plant_id, stem, path, [0.003, 0.0025, 0.002], "trifoliate")
        assert shoot != stem
        assert plantarch.isShootGeometryPrescribed(plant_id, shoot) is True
        verts = plantarch.getShootInternodeVertices(plant_id, shoot)
        # Seated on the parent's tip, on its axis -- not a parent radius beside it as a lateral is.
        assert math.dist(verts[0], (tip.x, tip.y, tip.z)) < 1e-3
        assert math.dist(verts[0], verts[-1]) == pytest.approx(
            math.dist((path[0].x, path[0].y, path[0].z), (path[-1].x, path[-1].y, path[-1].z)), rel=1e-3)

    def test_appended_shoot_accepts_a_growth_type(self, bean):
        context, plantarch = bean
        plant_id, stem = self._stem(plantarch)
        tip = self.PATH[-1]
        path = [tip, vec3(tip.x, tip.y, tip.z + 0.1)]
        shoot = plantarch.appendShootFromNodePositions(plant_id, stem, path, [0.003, 0.002], "trifoliate",
                                                       growth_shoot_type_label="unifoliate")
        assert plantarch.isShootGeometryPrescribed(plant_id, shoot) is True

    def test_appended_shoot_far_from_the_tip_is_rejected(self, bean):
        context, plantarch = bean
        plant_id, stem = self._stem(plantarch)
        with pytest.raises(PlantArchitectureError):
            plantarch.appendShootFromNodePositions(plant_id, stem, [vec3(1, 1, 1), vec3(1, 1, 1.1)],
                                                   [0.003, 0.002], "trifoliate")

    def _leaves_per_petiole(self, plantarch):
        pp = plantarch.getCurrentShootParameters("trifoliate")["phytomer_parameters"]
        v = pp["leaf"]["leaves_per_petiole"]
        return int(v["parameters"][0]) if isinstance(v, dict) else int(v)

    def _placed_leaves(self, plantarch, n):
        bases = [vec3(0.3 + 0.03 * i, 0.2, 0.15) for i in range(n)]
        return bases, [AxisRotation(0.2, 0.0, 0.0)] * n, [0.08] * n

    def test_leaf_stalk_lengths_set_the_stalk(self, bean):
        """A longer stalk adds object area beyond the blade, whose size is fixed."""
        context, plantarch = bean
        plant_id, stem = self._stem(plantarch)
        n = self._leaves_per_petiole(plantarch)
        bases, rotations, sizes = self._placed_leaves(plantarch, n)

        def stalk_area(length):
            plantarch.setPetioleLeafGeometry(plant_id, stem, 0, 0, bases, rotations, sizes,
                                             leaf_stalk_lengths=[length] * n)
            leaves = plantarch.getPhytomerLeafObjectIDs(plant_id, stem, 0)[0]
            return sum(context.getObjectArea(o) - plantarch.getLeafBladeArea(o) for o in leaves)

        short, long_ = stalk_area(0.004), stalk_area(0.02)
        assert short > 0.0
        assert long_ > short

    def test_refused_stalk_base_leaves_no_stray_blade(self, bean):
        """A stalk base a metre from its leaf makes a stalk longer than the blade, which is refused,
        and the leaf built for it is deleted rather than left in the Context."""
        context, plantarch = bean
        plant_id, stem = self._stem(plantarch)
        n = self._leaves_per_petiole(plantarch)
        bases, rotations, sizes = self._placed_leaves(plantarch, n)
        plantarch.setPetioleLeafGeometry(plant_id, stem, 0, 0, bases, rotations, sizes)
        objects_before = context.getObjectCount()

        far = [vec3(b.x + 1.0, b.y, b.z) for b in bases]
        with pytest.raises(PlantArchitectureError):
            plantarch.setPetioleLeafGeometry(plant_id, stem, 0, 0, bases, rotations, sizes, leaf_stalk_bases=far)
        assert context.getObjectCount() <= objects_before


@pytest.mark.native_only
class TestPlantArch1397LeafShape:

    def test_can_reshape_in_place_agrees_with_reshape_leaf(self):
        _require_1397()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("sorghum")
            plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 25.0)
            node, petiole_leaves = _first_leafy_phytomer(plantarch, plant_id)
            leaf = petiole_leaves[0]

            own = plantarch.getLeafShape(plant_id, 0, node, 0, 0)
            assert plantarch.canReshapeLeafInPlace(plant_id, 0, node, 0, 0, own) is True
            before = context.getObjectPrimitiveUUIDs(leaf)
            plantarch.reshapeLeaf(plant_id, 0, node, 0, 0, own)
            assert context.getObjectPrimitiveUUIDs(leaf) == before

            finer = plantarch.getLeafShape(plant_id, 0, node, 0, 0)
            finer.subdivisions_y = own.subdivisions_y * 4 + 2
            assert plantarch.canReshapeLeafInPlace(plant_id, 0, node, 0, 0, finer) is False
            plantarch.reshapeLeaf(plant_id, 0, node, 0, 0, finer)
            assert context.getObjectPrimitiveUUIDs(leaf) != before

            with pytest.raises(PlantArchitectureError):
                plantarch.canReshapeLeafInPlace(plant_id, 0, node, 0, 999, own)

    def test_negative_midrib_fold_is_accepted_natively(self):
        _require_1397()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("tomato")
            plant_id = plantarch.addPlantInstance(vec3(0, 0, 0), 10.0)
            stem = plantarch.addShootFromNodePositions(
                plant_id, -1, 0, [vec3(0, 0, 0), vec3(0, 0, 0.05), vec3(0, 0, 0.1)],
                [0.004, 0.0035, 0.003], "mainstem")
            plantarch.setPetioleLeafShape(plant_id, stem, 0, 0, 0.5, 0.0, 0.0, -0.6)
            assert plantarch.getLeafShape(plant_id, stem, 0, 0, 0).midrib_fold_fraction == pytest.approx(-0.6)


@pytest.mark.native_only
class TestLibraryFunctionNames1397:
    """Library functions referenced by name must be registered, or a shoot-parameter round trip drops them."""

    def test_cucumber_shoot_parameters_name_their_library_functions(self):
        from pyhelios import Context, PlantArchitecture
        with Context() as context:
            with PlantArchitecture(context) as plantarch:
                plantarch.loadPlantModelFromLibrary("cucumber")
                params = plantarch.getCurrentShootParameters("main")
                inflorescence = params["phytomer_parameters"]["inflorescence"]
                assert inflorescence["fruit_prototype_function"] == "CucumberFruitPrototype"
                assert inflorescence["flower_prototype_function"] == "CucumberFlowerPrototype"
                assert plantarch.getPhytomerCreationFunctionName("main") == "CucumberMainPhytomerCreationFunction"
                assert plantarch.getPhytomerCallbackFunctionName("main") == "CucumberMainPhytomerCallbackFunction"
                # Redefining the type from its own parameters keeps the fruit and flower
                plantarch.defineShootType("main_copy", params)
                copied = plantarch.getCurrentShootParameters("main_copy")["phytomer_parameters"]["inflorescence"]
                assert copied["fruit_prototype_function"] == "CucumberFruitPrototype"
                assert copied["flower_prototype_function"] == "CucumberFlowerPrototype"

    def test_apple_fruitingwall_functions_are_registered(self):
        from pyhelios import PlantArchitecture
        assert "AppleFruitingWallPhytomerCreationFunction" in PlantArchitecture.getLibraryPhytomerCreationFunctionNames()
        assert "AppleFruitingWallPhytomerCallbackFunction" in PlantArchitecture.getLibraryPhytomerCallbackFunctionNames()
