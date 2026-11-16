"""
Tests for the helios-core 1.3.98 additions that reach the Python API.

Core: Context.getPrimitiveDataRevision / getSpectralTextureRevision.
Plug-ins: PlantHydraulicsModel.outputPlantConductancePrimitiveData, the photosynthesis
"electron_transport_rate" / "dark_respiration" outputs, the Buckley et al. (2026) stomatal
conductance model and its species library, and the PlantArchitecture joint-pose API
(getPlantJoints ... bakePlantPose, setShootNodePositions) and getPlantArticulation.
"""

import math

import numpy as np
import pytest

from pyhelios import Context, Global, SpectralTextureClass
from pyhelios.plugins.registry import get_plugin_registry
from pyhelios.types import vec3
from pyhelios.wrappers import UContextWrapper as context_wrapper


def _available(plugin):
    return get_plugin_registry().is_plugin_available(plugin)


requires_ctx_1398 = pytest.mark.skipif(
    not context_wrapper._CONTEXT_1398_AVAILABLE,
    reason="Context 1.3.98 functions not in the native library (rebuild with build_scripts/build_helios --clean)")


# =========================================================================== #
# Pure-Python checks (mock mode safe)
# =========================================================================== #
@pytest.mark.cross_platform
class TestPurePython1398:

    def test_buckley2026_defaults_match_native_constructor(self):
        from pyhelios.StomatalConductance import Buckley2026Coefficients
        c = Buckley2026Coefficients()
        assert (c.s, c.K_plant_at_25C, c.b_o, c.psi_c) == pytest.approx((0.08766, 0.007411, 1.11, -4.103))

    def test_buckley2026_validation_rejects_bad_coefficients(self):
        from pyhelios.StomatalConductance import Buckley2026Coefficients, StomatalConductanceModel
        validate = StomatalConductanceModel._validate_buckley2026
        validate(Buckley2026Coefficients())
        with pytest.raises(ValueError, match="Buckley2026Coefficients instance"):
            validate((0.1, 0.01, 1.0, -2.0))
        with pytest.raises(ValueError, match="s must be positive"):
            validate(Buckley2026Coefficients(s=0.0))
        with pytest.raises(ValueError, match="K_plant_at_25C must be positive"):
            validate(Buckley2026Coefficients(K_plant_at_25C=-1.0))
        with pytest.raises(ValueError, match="psi_c must be a finite number"):
            validate(Buckley2026Coefficients(psi_c=float("nan")))

    def test_buckley2026_wrapper_rejects_wrong_array_length(self):
        from pyhelios.wrappers import UStomatalConductanceWrapper as sw
        with pytest.raises(ValueError, match="exactly 4 values"):
            sw._buckley2026_array([1.0, 2.0, 3.0])

    def test_joint_id_round_trip_and_hashable(self):
        from pyhelios.PlantArchitecture import PlantJointID, PlantJointType
        j = PlantJointID(PlantJointType.PEDUNCLE, 3, 4, 1, 2)
        assert j._to_list() == [4, 3, 4, 1, 2]
        assert PlantJointID._from_list([4, 3, 4, 1, 2]) == j
        assert {j: 1}[PlantJointID(PlantJointType.PEDUNCLE, 3, 4, 1, 2)] == 1
        # Values match the native PlantJointType enum.
        assert [t.value for t in PlantJointType] == [0, 1, 2, 3, 4]

    def test_joint_pose_rejects_non_finite(self):
        from pyhelios.PlantArchitecture import PlantJointPose
        assert PlantJointPose()._to_list() == [0.0, 0.0, 0.0, 1.0]
        with pytest.raises(ValueError, match="yaw_degrees"):
            PlantJointPose(yaw_degrees=float("inf"))._to_list()
        with pytest.raises(ValueError, match="pitch_degrees"):
            PlantJointPose(pitch_degrees="10")._to_list()

    def test_pose_methods_validate_argument_types_before_native_call(self):
        from pyhelios import PlantArchitecture
        from pyhelios.PlantArchitecture import PlantJointID, PlantJointPose
        pa = PlantArchitecture.__new__(PlantArchitecture)
        pa._plantarch_ptr = None
        pa.context = None
        with pytest.raises(ValueError, match="PlantJointID"):
            PlantArchitecture.setPlantJointPose(pa, 0, (2, 0, 0, 0, 0), PlantJointPose())
        with pytest.raises(ValueError, match="PlantJointPose"):
            PlantArchitecture.setPlantJointPose(pa, 0, PlantJointID(), (0, 0, 0, 1))
        with pytest.raises(ValueError, match="positive finite"):
            PlantArchitecture.setPlantJointLength(pa, 0, PlantJointID(), 0.0)
        with pytest.raises(ValueError, match=r"node_positions\[1\] must be a vec3"):
            PlantArchitecture.setShootNodePositions(pa, 0, 0, [vec3(0, 0, 0), (0, 0, 1)])
        with pytest.raises(ValueError, match="pairs"):
            PlantArchitecture.setPlantJointPoses(pa, 0, [PlantJointID()])
        with pytest.raises(ValueError, match="armature_stability_ratio"):
            PlantArchitecture.getPlantArticulation(pa, 0, armature_stability_ratio=0.0)
        with pytest.raises(ValueError, match="wood_density"):
            PlantArchitecture.getPlantArticulation(pa, 0, wood_density=float("nan"))
        with pytest.raises(ValueError, match="shootID must be a non-negative int"):
            PlantArchitecture.setPlantJointPose(pa, 0, PlantJointID(shootID=-1), PlantJointPose())

    def test_pose_wrapper_rejects_wrong_array_sizes(self):
        from pyhelios.wrappers import UPlantArchitectureWrapper as pw
        with pytest.raises(ValueError, match="5 values"):
            pw._joint_array([0, 0, 0])
        with pytest.raises(ValueError, match="4 values"):
            pw._pose_array([0.0, 0.0])


# =========================================================================== #
# Context revisions
# =========================================================================== #
@pytest.mark.native_only
@requires_ctx_1398
class TestContextRevisions1398:

    def test_primitive_data_revision_is_per_label(self):
        with Context() as ctx:
            uuid = ctx.addPatch()
            assert ctx.getPrimitiveDataRevision("temperature") == 0
            ctx.setPrimitiveDataFloat(uuid, "temperature", 25.0)
            rev = ctx.getPrimitiveDataRevision("temperature")
            assert rev > 0
            ctx.setPrimitiveDataFloat(uuid, "other_label", 1.0)
            assert ctx.getPrimitiveDataRevision("temperature") == rev
            ctx.setPrimitiveDataFloat(uuid, "temperature", 25.0)   # same value still advances it
            assert ctx.getPrimitiveDataRevision("temperature") > rev

    def test_primitive_data_revision_rejects_non_str(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="Label must be a str"):
                ctx.getPrimitiveDataRevision(5)

    def test_spectral_texture_revision_advances_on_set_and_clear(self, tmp_path):
        classes = np.array([[1, 1, 2], [1, 2, 2]], dtype=np.uint16)
        path = str(tmp_path / "classes.png")
        Global.writePNGSingleChannel(path, 3, 2, classes, 8)
        with Context() as ctx:
            ctx.addSpectralPalette("leaf", [SpectralTextureClass("a_reflectivity", "a_transmissivity"),
                                            SpectralTextureClass("b_reflectivity", "b_transmissivity")])
            patch = ctx.addPatch()
            rev0 = ctx.getSpectralTextureRevision()
            ctx.setPrimitiveDataFloat(patch, "x", 1.0)
            assert ctx.getSpectralTextureRevision() == rev0
            ctx.setPrimitiveSpectralTexture(patch, path, "leaf")
            rev1 = ctx.getSpectralTextureRevision()
            assert rev1 > rev0
            ctx.clearPrimitiveSpectralTexture(patch)
            assert ctx.getSpectralTextureRevision() > rev1


# =========================================================================== #
# Plant hydraulics, photosynthesis and the Buckley et al. (2026) stomatal model
# =========================================================================== #
def _require_plugin(name):
    if not _available(name):
        pytest.skip(f"{name} plugin not available")


@pytest.mark.native_only
class TestPlantConductanceOutput1398:

    def _run(self, write_output, set_soil):
        _require_plugin("planthydraulics")
        from pyhelios import PlantHydraulicsModel
        from tests.test_planthydraulics import add_plant, pistachio_coefficients
        from pyhelios.wrappers import UPlantHydraulicsWrapper as hw
        if not hw._PLANT_CONDUCTANCE_OUTPUT_AVAILABLE:
            pytest.skip("native library predates helios-core 1.3.98")
        with Context() as ctx, PlantHydraulicsModel(ctx) as model:
            leaves = add_plant(ctx, plant_id=1)
            model.setModelCoefficients(pistachio_coefficients())
            if set_soil:
                model.setSoilWaterPotentialOfPlant(1, -0.3)
            if write_output:
                model.outputPlantConductancePrimitiveData(True)
            model.run(leaves)
            has_k = ctx.doesPrimitiveDataExist(leaves[0], "plant_hydraulic_conductance")
            has_soil = ctx.doesPrimitiveDataExist(leaves[0], "soil_water_potential")
            k = ctx.getPrimitiveDataFloat(leaves[0], "plant_hydraulic_conductance") if has_k else None
            soil = ctx.getPrimitiveDataFloat(leaves[0], "soil_water_potential") if has_soil else None
        return has_k, k, has_soil, soil

    def test_not_written_unless_requested(self):
        has_k, _, has_soil, _ = self._run(write_output=False, set_soil=True)
        assert not has_k and not has_soil

    def test_written_in_steady_state_when_requested(self):
        has_k, k, has_soil, soil = self._run(write_output=True, set_soil=True)
        assert has_k and k > 0 and math.isfinite(k)
        assert has_soil and soil == pytest.approx(-0.3)

    def test_soil_water_potential_only_for_plants_set_by_user(self):
        has_k, _, has_soil, _ = self._run(write_output=True, set_soil=False)
        assert has_k
        assert not has_soil

    def test_non_bool_toggle_rejected(self):
        _require_plugin("planthydraulics")
        from pyhelios import PlantHydraulicsModel
        with Context() as ctx, PlantHydraulicsModel(ctx) as model:
            with pytest.raises(ValueError):
                model.outputPlantConductancePrimitiveData(1)


def _require_buckley():
    _require_plugin("stomatalconductance")
    from pyhelios.wrappers import UStomatalConductanceWrapper as sw
    if not sw._BUCKLEY2026_FUNCTIONS_AVAILABLE:
        pytest.skip("native library predates helios-core 1.3.98")


@pytest.mark.native_only
class TestBuckley2026Stomatal:

    def test_library_values_match_native_table(self):
        _require_buckley()
        from pyhelios import StomatalConductanceModel
        with Context() as ctx, StomatalConductanceModel(ctx) as sc:
            almond = sc.getBuckley2026CoefficientsFromLibrary("Almond")
            assert (almond.s, almond.K_plant_at_25C, almond.b_o, almond.psi_c) == \
                pytest.approx((0.01595, 0.03266, 1.416, -2.329))
            assert sc.getBuckley2026CoefficientsFromLibrary("pistachio").psi_c == pytest.approx(-4.103)
            for species in ("Elderberry", "Cowpea", "EasternRedbud", "Grape", "Olive", "PistachioFemale"):
                assert sc.getBuckley2026CoefficientsFromLibrary(species).s > 0

    def test_unknown_species_raises_with_valid_names(self):
        _require_buckley()
        from pyhelios import StomatalConductanceModel
        from pyhelios.StomatalConductance import StomatalConductanceModelError
        with Context() as ctx, StomatalConductanceModel(ctx) as sc:
            with pytest.raises(StomatalConductanceModelError, match="EasternRedbud"):
                sc.getBuckley2026CoefficientsFromLibrary("Walnut")
            with pytest.raises(StomatalConductanceModelError):
                sc.setBuckley2026CoefficientsFromLibrary("Walnut")

    @staticmethod
    def _leaf_inputs(ctx, uuids, include_photo=True):
        for name, value in (("radiation_flux_PAR", 300.0), ("temperature", 298.0), ("air_temperature", 298.0),
                            ("air_humidity", 0.5), ("boundarylayer_conductance", 1.0),
                            ("soil_water_potential", -0.3)):
            ctx.setPrimitiveDataFloat(uuids, name, value)
        if include_photo:
            ctx.setPrimitiveDataFloat(uuids, "net_photosynthesis", 10.0)
            ctx.setPrimitiveDataFloat(uuids, "electron_transport_rate", 120.0)
            ctx.setPrimitiveDataFloat(uuids, "dark_respiration", 1.0)

    def test_selecting_model_sets_global_flag_and_run_writes_conductance(self):
        _require_buckley()
        from pyhelios import StomatalConductanceModel
        from pyhelios.StomatalConductance import Buckley2026Coefficients
        with Context() as ctx, StomatalConductanceModel(ctx) as sc:
            sc.disableMessages()
            leaves = [ctx.addPatch() for _ in range(3)]
            self._leaf_inputs(ctx, leaves)
            assert not ctx.doesGlobalDataExist("buckley2026_stomatal_model_enabled")
            sc.setBuckley2026Coefficients(Buckley2026Coefficients(s=0.03, K_plant_at_25C=0.008, b_o=1.2, psi_c=-1.8))
            assert ctx.getGlobalDataInt("buckley2026_stomatal_model_enabled") == 1
            sc.run(leaves)
            gs = [ctx.getPrimitiveDataFloat(u, "moisture_conductance") for u in leaves]
            assert all(math.isfinite(g) and g > 0 for g in gs)

    def test_closed_stomata_when_soil_below_psi_c(self):
        _require_buckley()
        from pyhelios import StomatalConductanceModel
        from pyhelios.StomatalConductance import Buckley2026Coefficients
        with Context() as ctx, StomatalConductanceModel(ctx) as sc:
            sc.disableMessages()
            leaf = ctx.addPatch()
            self._leaf_inputs(ctx, [leaf])
            sc.setBuckley2026Coefficients(Buckley2026Coefficients(psi_c=-0.1), uuids=[leaf])
            sc.run([leaf])
            assert ctx.getPrimitiveDataFloat(leaf, "moisture_conductance") == pytest.approx(0.0, abs=1e-6)

    def test_missing_photosynthesis_inputs_is_an_error(self):
        _require_buckley()
        from pyhelios import StomatalConductanceModel
        from pyhelios.StomatalConductance import StomatalConductanceModelError
        with Context() as ctx, StomatalConductanceModel(ctx) as sc:
            sc.disableMessages()
            leaf = ctx.addPatch()
            self._leaf_inputs(ctx, [leaf], include_photo=False)
            sc.setBuckley2026CoefficientsFromLibrary("Grape")
            with pytest.raises(StomatalConductanceModelError):
                sc.run([leaf])

    def test_material_target(self):
        _require_buckley()
        from pyhelios import StomatalConductanceModel
        with Context() as ctx, StomatalConductanceModel(ctx) as sc:
            sc.disableMessages()
            ctx.addMaterial("grape_leaf")
            leaf = ctx.addPatch()
            ctx.assignMaterialToPrimitive(leaf, "grape_leaf")
            self._leaf_inputs(ctx, [leaf])
            sc.setBuckley2026CoefficientsFromLibrary("Grape", material_label="grape_leaf")
            sc.run([leaf])
            assert ctx.getPrimitiveDataFloat(leaf, "moisture_conductance") > 0

    def test_photosynthesis_writes_inputs_once_buckley_selected(self):
        _require_buckley()
        _require_plugin("photosynthesis")
        from pyhelios import PhotosynthesisModel, StomatalConductanceModel
        with Context() as ctx, PhotosynthesisModel(ctx) as photo, StomatalConductanceModel(ctx) as sc:
            photo.disableMessages()
            sc.disableMessages()
            leaf = ctx.addPatch()
            self._leaf_inputs(ctx, [leaf], include_photo=False)
            ctx.setPrimitiveDataFloat(leaf, "moisture_conductance", 0.2)
            photo.setFarquharCoefficientsFromLibrary("Almond")
            photo.runForPrimitives([leaf])
            assert not ctx.doesPrimitiveDataExist(leaf, "electron_transport_rate")
            sc.setBuckley2026CoefficientsFromLibrary("Almond")
            photo.runForPrimitives([leaf])
            assert ctx.getPrimitiveDataFloat(leaf, "electron_transport_rate") > 0
            assert ctx.getPrimitiveDataFloat(leaf, "dark_respiration") > 0
            sc.run([leaf])
            assert ctx.getPrimitiveDataFloat(leaf, "moisture_conductance") > 0

    def test_photosynthesis_optional_outputs_on_request(self):
        _require_plugin("photosynthesis")
        from pyhelios import PhotosynthesisModel
        with Context() as ctx, PhotosynthesisModel(ctx) as photo:
            photo.disableMessages()
            leaf = ctx.addPatch()
            self._leaf_inputs(ctx, [leaf], include_photo=False)
            ctx.setPrimitiveDataFloat(leaf, "moisture_conductance", 0.2)
            photo.setFarquharCoefficientsFromLibrary("Almond")
            photo.exportResults("electron_transport_rate")
            photo.exportResults("dark_respiration")
            photo.runForPrimitives([leaf])
            J = ctx.getPrimitiveDataFloat(leaf, "electron_transport_rate")
            Rd = ctx.getPrimitiveDataFloat(leaf, "dark_respiration")
            assert 0 < J < 1000 and 0 < Rd < 20


# =========================================================================== #
# PlantArchitecture joint poses and articulation
# =========================================================================== #
def _require_pose_api():
    _require_plugin("plantarchitecture")
    from pyhelios.wrappers import UPlantArchitectureWrapper as pw
    if not pw._PLANTARCHITECTURE_1398_AVAILABLE:
        pytest.skip("native library predates helios-core 1.3.98")


@pytest.fixture
def bean_plant():
    _require_pose_api()
    from pyhelios import PlantArchitecture
    with Context() as ctx, PlantArchitecture(ctx) as pa:
        pa.disableMessages()
        pa.loadPlantModelFromLibrary("bean")
        plant_id = pa.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 25.0)
        yield ctx, pa, plant_id


def _flat_vertices(ctx, uuids):
    return np.concatenate([np.array([[v.x, v.y, v.z] for v in ctx.getPrimitiveVertices(u)]).ravel()
                           for u in uuids])


@pytest.mark.native_only
class TestPlantJointPoses:

    def _petiole_joint(self, pa, plant_id):
        from pyhelios.PlantArchitecture import PlantJointType
        joints = pa.getPlantJoints(plant_id)
        petioles = [j for j in joints if j.type == PlantJointType.PETIOLE]
        assert petioles, "bean at age 25 has no petiole joints; assertions would be vacuous"
        return petioles[0]

    def test_joints_listed_base_outward(self, bean_plant):
        from pyhelios.PlantArchitecture import PlantJointType
        _, pa, plant_id = bean_plant
        joints = pa.getPlantJoints(plant_id)
        assert joints[0].type == PlantJointType.ROOT
        types = {j.type for j in joints}
        assert PlantJointType.INTERNODE in types and PlantJointType.PETIOLE in types
        assert len(set(joints)) == len(joints)

    def test_joint_frame_has_unit_axes(self, bean_plant):
        _, pa, plant_id = bean_plant
        frame = pa.getPlantJointFrame(plant_id, self._petiole_joint(pa, plant_id))
        for axis in (frame.parent_axis, frame.organ_axis):
            assert math.sqrt(axis.x ** 2 + axis.y ** 2 + axis.z ** 2) == pytest.approx(1.0, abs=1e-4)
        assert frame.length > 0

    def test_pose_moves_geometry_and_reset_restores_it(self, bean_plant):
        from pyhelios.PlantArchitecture import PlantJointPose
        ctx, pa, plant_id = bean_plant
        uuids = pa.getAllPlantUUIDs(plant_id)
        before = _flat_vertices(ctx, uuids)
        joint = self._petiole_joint(pa, plant_id)
        assert not pa.isPlantPosed(plant_id)

        pa.setPlantJointPose(plant_id, joint, PlantJointPose(pitch_degrees=25.0, yaw_degrees=10.0))
        assert pa.isPlantPosed(plant_id)
        assert pa.getAllPlantUUIDs(plant_id) == uuids, "posing must not rebuild organs"
        posed = _flat_vertices(ctx, uuids)
        assert np.max(np.abs(posed - before)) > 1e-3
        pose = pa.getPlantJointPose(plant_id, joint)
        assert (pose.pitch_degrees, pose.yaw_degrees, pose.roll_degrees, pose.length_scale) == \
            pytest.approx((25.0, 10.0, 0.0, 1.0))

        pa.resetPlantPose(plant_id)
        assert not pa.isPlantPosed(plant_id)
        np.testing.assert_allclose(_flat_vertices(ctx, uuids), before, atol=1e-5)

    def test_poses_are_offsets_not_increments(self, bean_plant):
        from pyhelios.PlantArchitecture import PlantJointPose
        ctx, pa, plant_id = bean_plant
        uuids = pa.getAllPlantUUIDs(plant_id)
        joint = self._petiole_joint(pa, plant_id)
        pa.setPlantJointPose(plant_id, joint, PlantJointPose(pitch_degrees=20.0))
        once = _flat_vertices(ctx, uuids)
        pa.setPlantJointPose(plant_id, joint, PlantJointPose(pitch_degrees=20.0))
        np.testing.assert_allclose(_flat_vertices(ctx, uuids), once, atol=1e-5)

    def test_set_joint_poses_batch_and_length(self, bean_plant):
        from pyhelios.PlantArchitecture import PlantJointPose, PlantJointType
        _, pa, plant_id = bean_plant
        internodes = [j for j in pa.getPlantJoints(plant_id) if j.type == PlantJointType.INTERNODE][:3]
        pa.setPlantJointPoses(plant_id, {j: PlantJointPose(yaw_degrees=5.0 * (i + 1)) for i, j in enumerate(internodes)})
        assert [pa.getPlantJointPose(plant_id, j).yaw_degrees for j in internodes] == pytest.approx([5.0, 10.0, 15.0])

        target = internodes[1]
        grown = pa.getPlantJointFrame(plant_id, target).length
        pa.setPlantJointLength(plant_id, target, 1.5 * grown)
        assert pa.getPlantJointFrame(plant_id, target).length == pytest.approx(1.5 * grown, rel=1e-3)
        pose = pa.getPlantJointPose(plant_id, target)
        assert pose.length_scale == pytest.approx(1.5, rel=1e-3)
        assert pose.yaw_degrees == pytest.approx(10.0), "setPlantJointLength must keep the joint's angles"

    def test_bake_makes_pose_permanent(self, bean_plant):
        from pyhelios.PlantArchitecture import PlantJointPose
        ctx, pa, plant_id = bean_plant
        uuids = pa.getAllPlantUUIDs(plant_id)
        joint = self._petiole_joint(pa, plant_id)
        pa.setPlantJointPose(plant_id, joint, PlantJointPose(pitch_degrees=30.0))
        posed = _flat_vertices(ctx, uuids)
        pa.bakePlantPose(plant_id)
        assert not pa.isPlantPosed(plant_id)
        assert pa.getPlantJointPose(plant_id, joint).pitch_degrees == pytest.approx(0.0)
        np.testing.assert_allclose(_flat_vertices(ctx, uuids), posed, atol=1e-5)

    def test_posed_plant_cannot_be_written_to_xml(self, bean_plant, tmp_path):
        from pyhelios import PlantArchitectureError
        from pyhelios.PlantArchitecture import PlantJointPose
        _, pa, plant_id = bean_plant
        pa.setPlantJointPose(plant_id, self._petiole_joint(pa, plant_id), PlantJointPose(pitch_degrees=15.0))
        with pytest.raises(PlantArchitectureError):
            pa.writePlantStructureXML(plant_id, tmp_path / "posed.xml")

    def test_advance_time_bakes_pose(self, bean_plant):
        from pyhelios.PlantArchitecture import PlantJointPose
        _, pa, plant_id = bean_plant
        joint = self._petiole_joint(pa, plant_id)
        pa.setPlantJointPose(plant_id, joint, PlantJointPose(pitch_degrees=20.0))
        assert pa.isPlantPosed(plant_id)
        pa.advanceTime(1.0, plant_id=plant_id)
        assert not pa.isPlantPosed(plant_id)
        assert pa.getPlantJointPose(plant_id, joint).pitch_degrees == pytest.approx(0.0)

    def test_list_pairs_accepted_by_set_joint_poses(self, bean_plant):
        from pyhelios.PlantArchitecture import PlantJointPose
        _, pa, plant_id = bean_plant
        joint = self._petiole_joint(pa, plant_id)
        pa.setPlantJointPoses(plant_id, [[joint, PlantJointPose(roll_degrees=12.0)]])
        assert pa.getPlantJointPose(plant_id, joint).roll_degrees == pytest.approx(12.0)

    def test_unknown_joint_raises(self, bean_plant):
        from pyhelios import PlantArchitectureError
        from pyhelios.PlantArchitecture import PlantJointID, PlantJointPose, PlantJointType
        _, pa, plant_id = bean_plant
        with pytest.raises(PlantArchitectureError):
            pa.setPlantJointPose(plant_id, PlantJointID(PlantJointType.INTERNODE, 999, 0, 0, 0),
                                 PlantJointPose(pitch_degrees=5.0))

    @staticmethod
    def _longest_shoot(pa, plant_id):
        from pyhelios.PlantArchitecture import PlantJointType
        by_shoot = {}
        for j in pa.getPlantJoints(plant_id):
            if j.type == PlantJointType.INTERNODE:
                by_shoot.setdefault(j.shootID, []).append(j)
        shoot_id, internodes = max(by_shoot.items(), key=lambda item: len(item[1]))
        assert len(internodes) >= 3, "no shoot with 3+ internodes; assertions would be vacuous"
        return shoot_id, internodes

    def test_set_shoot_node_positions_bends_shoot(self, bean_plant):
        _, pa, plant_id = bean_plant
        shoot_id, internodes = self._longest_shoot(pa, plant_id)
        frames = [pa.getPlantJointFrame(plant_id, j) for j in internodes]
        base = frames[0].pivot
        positions = [base]
        # Lay the stem along +x at its grown internode lengths.
        x = base.x
        for f in frames:
            x += f.length
            positions.append(vec3(x, base.y, base.z))
        pa.setShootNodePositions(plant_id, shoot_id, positions)
        assert pa.isPlantPosed(plant_id)
        last = pa.getPlantJointFrame(plant_id, internodes[-1])
        assert last.organ_axis.x == pytest.approx(1.0, abs=1e-3)
        tip = vec3(last.pivot.x + last.organ_axis.x * last.length, last.pivot.y + last.organ_axis.y * last.length,
                   last.pivot.z + last.organ_axis.z * last.length)
        assert (tip.x, tip.y, tip.z) == pytest.approx((positions[-1].x, positions[-1].y, positions[-1].z), abs=1e-3)

    def test_set_shoot_node_positions_wrong_count_raises(self, bean_plant):
        from pyhelios import PlantArchitectureError
        _, pa, plant_id = bean_plant
        shoot_id, internodes = self._longest_shoot(pa, plant_id)
        base = pa.getPlantJointFrame(plant_id, internodes[0]).pivot
        too_few = [base] + [vec3(base.x + 0.05 * (i + 1), base.y, base.z) for i in range(len(internodes) - 1)]
        with pytest.raises(PlantArchitectureError, match="positions were given"):
            pa.setShootNodePositions(plant_id, shoot_id, too_few)


@pytest.mark.native_only
class TestPlantArticulation:

    def test_articulation_links_and_joints_are_consistent(self, bean_plant):
        from pyhelios.PlantArchitecture import PlantArticulationLinkType
        _, pa, plant_id = bean_plant
        art = pa.getPlantArticulation(plant_id)
        assert art.links and art.joints
        assert art.links[0].parent_index == -1
        for i, link in enumerate(art.links):
            assert link.parent_index < i, "every parent link must precede its children"
            assert link.mass > 0 and link.name
            assert math.isclose(sum(q * q for q in link.orientation), 1.0, abs_tol=1e-3)
        assert len({link.name for link in art.links}) == len(art.links)
        types = {link.type for link in art.links}
        assert PlantArticulationLinkType.INTERNODE in types and PlantArticulationLinkType.LEAF in types
        for joint in art.joints:
            assert 0 <= joint.parent_index < len(art.links) and 0 <= joint.child_index < len(art.links)
            assert art.links[joint.child_index].parent_index == joint.parent_index
            assert joint.stiffness >= 0 and joint.damping >= 0

    def test_link_joints_name_real_skeleton_joints(self, bean_plant):
        _, pa, plant_id = bean_plant
        joints = set(pa.getPlantJoints(plant_id))
        art = pa.getPlantArticulation(plant_id)
        assert all(link.joint in joints for link in art.links)

    def test_parameters_reach_native(self, bean_plant):
        _, pa, plant_id = bean_plant
        light = pa.getPlantArticulation(plant_id, wood_density=400.0)
        heavy = pa.getPlantArticulation(plant_id, wood_density=800.0)
        stem_light = [l.mass for l in light.links if l.radius > 0]
        stem_heavy = [l.mass for l in heavy.links if l.radius > 0]
        assert stem_heavy == pytest.approx([2.0 * m for m in stem_light], rel=1e-4)

    def test_unknown_plant_raises(self, bean_plant):
        from pyhelios import PlantArchitectureError
        _, pa, _ = bean_plant
        with pytest.raises(PlantArchitectureError):
            pa.getPlantArticulation(9999)
