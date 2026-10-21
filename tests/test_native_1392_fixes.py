"""
Regression tests for native fixes and behavior changes in helios-core 1.3.92 that are
reachable through existing PyHelios APIs.

Each test fails against the 1.3.90 native library and passes against 1.3.92.
"""

import pytest

from pyhelios import Context, DataTypes
from pyhelios.exceptions import HeliosError

from tests.test_radiation_model import radiation_model_or_skip


def _obj_face_centroid_x(obj_path):
    """x-coordinate of the centroid of each face, in the order the faces appear in the file."""
    vertices = []
    centroids = []
    for line in obj_path.read_text().splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "v":
            vertices.append(float(parts[1]))
        elif parts[0] == "f":
            idx = [int(p.split("/")[0]) - 1 for p in parts[1:]]
            centroids.append(sum(vertices[i] for i in idx) / len(idx))
    return centroids


@pytest.mark.native_only
class TestContextOutput1392:

    def test_writeOBJ_dat_rows_follow_faces_when_grouped_by_object_label(self, tmp_path):
        """Row i of each .dat file holds the value of face i, also when faces are grouped by object_label."""
        with Context() as context:
            # Patches at x = 0, 10, 20; labels A, B, A interleave so object grouping reorders the faces.
            values = {0.0: 1.0, 10.0: 2.0, 20.0: 3.0}
            labels = {0.0: "A", 10.0: "B", 20.0: "A"}
            uuids = []
            for x in (0.0, 10.0, 20.0):
                uuid = context.addPatch(center=DataTypes.vec3(x, 0, 0), size=DataTypes.vec2(1, 1))
                context.setPrimitiveDataFloat(uuid, "value", values[x])
                context.setPrimitiveDataString(uuid, "object_label", labels[x])
                uuids.append(uuid)

            obj_file = tmp_path / "scene.obj"
            context.writeOBJ(str(obj_file), uuids, ["value"], silent=True)

        centroids = _obj_face_centroid_x(obj_file)
        rows = [float(v) for v in (tmp_path / "scene_value.dat").read_text().split()]
        assert len(rows) == len(centroids) == 6
        for cx, row in zip(centroids, rows):
            nearest = min(values, key=lambda x: abs(x - cx))
            assert row == pytest.approx(values[nearest]), \
                f"face centred at x={cx:.2f} has .dat value {row}, expected {values[nearest]}"

    def test_writeOBJ_missing_dat_field_raises_before_writing(self, tmp_path):
        with Context() as context:
            labeled = context.addPatch(center=DataTypes.vec3(0, 0, 0), size=DataTypes.vec2(1, 1))
            unlabeled = context.addPatch(center=DataTypes.vec3(2, 0, 0), size=DataTypes.vec2(1, 1))
            context.setPrimitiveDataFloat(labeled, "value", 1.0)

            obj_file = tmp_path / "scene.obj"
            with pytest.raises(HeliosError, match="does not exist for primitive"):
                context.writeOBJ(str(obj_file), [labeled, unlabeled], ["value"], silent=True)
        assert not obj_file.exists()
        assert not (tmp_path / "scene_value.dat").exists()

    def test_writePrimitiveData_unopenable_file_raises(self, tmp_path):
        with Context() as context:
            uuid = context.addPatch(center=DataTypes.vec3(0, 0, 0), size=DataTypes.vec2(1, 1))
            context.setPrimitiveDataFloat(uuid, "value", 1.0)
            # A directory cannot be opened as an output file.
            target = tmp_path / "is_a_directory"
            target.mkdir()
            with pytest.raises(HeliosError):
                context.writePrimitiveData(str(target), ["value"])


@pytest.mark.native_only
class TestEnergyBalance1392:

    def test_run_rejects_duplicate_uuid(self):
        from pyhelios import EnergyBalanceModel, EnergyBalanceModelError
        with Context() as context:
            uuid = context.addPatch(center=DataTypes.vec3(0, 0, 0), size=DataTypes.vec2(1, 1))
            context.setPrimitiveDataFloat(uuid, "radiation_flux_SW", 0.0)
            with EnergyBalanceModel(context) as energy_balance:
                energy_balance.addRadiationBand("SW")
                with pytest.raises(EnergyBalanceModelError, match="appears more than once"):
                    energy_balance.run([uuid, uuid])


@pytest.mark.native_only
class TestRadiation1392Fixes:
    """Run on the Vulkan software BVH; not requires_gpu."""

    @staticmethod
    def _direct_band(radiation):
        radiation.disableMessages()
        radiation.addRadiationBand("SW")
        radiation.disableEmission("SW")
        radiation.setScatteringDepth("SW", 0)
        radiation.setDirectRayCount("SW", 100)
        source = radiation.addCollimatedRadiationSource(DataTypes.vec3(0, 0, 1))
        radiation.setSourceFlux(source, "SW", 1000.0)

    def test_invisibility_flag_hides_primitive(self):
        with Context() as context:
            receiver = context.addPatch(center=DataTypes.vec3(0, 0, 0), size=DataTypes.vec2(1, 1))
            shade = context.addPatch(center=DataTypes.vec3(0, 0, 1), size=DataTypes.vec2(2, 2))
            context.setPrimitiveDataUInt(shade, "invisibility_flag", 1)
            with radiation_model_or_skip(context) as radiation:
                self._direct_band(radiation)
                radiation.updateGeometry()
                radiation.runBand("SW")
                flux = radiation.getAbsorbedFlux("SW", [receiver, shade])
        assert flux[0] == pytest.approx(1000.0, rel=0.01)
        assert flux[1] == pytest.approx(0.0, abs=1e-6)

    def test_runBand_rebuilds_after_primitive_moved(self):
        with Context() as context:
            receiver = context.addPatch(center=DataTypes.vec3(0, 0, 0), size=DataTypes.vec2(1, 1))
            shade = context.addPatch(center=DataTypes.vec3(0, 0, 1), size=DataTypes.vec2(2, 2))
            with radiation_model_or_skip(context) as radiation:
                self._direct_band(radiation)
                radiation.updateGeometry()
                radiation.runBand("SW")
                assert radiation.getAbsorbedFlux("SW", [receiver])[0] == pytest.approx(0.0, abs=1e-6)

                # Move the shade out of the beam; no updateGeometry() call.
                context.translatePrimitive(shade, DataTypes.vec3(50, 0, 0))
                radiation.runBand("SW")
                assert radiation.getAbsorbedFlux("SW", [receiver])[0] == pytest.approx(1000.0, rel=0.01)

    @staticmethod
    def _seeded_diffuse_flux(seed):
        with Context() as context:
            context.seedRandomGenerator(seed)
            receiver = context.addPatch(center=DataTypes.vec3(0, 0, 0), size=DataTypes.vec2(1, 1))
            context.addPatch(center=DataTypes.vec3(0.6, 0, 0.4), size=DataTypes.vec2(1, 1),
                             rotation=DataTypes.SphericalCoord(1, 0.5 * 3.14159265, 0))
            with radiation_model_or_skip(context) as radiation:
                radiation.disableMessages()
                radiation.addRadiationBand("SW")
                radiation.disableEmission("SW")
                radiation.setScatteringDepth("SW", 0)
                radiation.setDiffuseRayCount("SW", 16)
                radiation.setDiffuseRadiationFlux("SW", 1000.0)
                radiation.updateGeometry()
                radiation.runBand("SW")
                return float(radiation.getAbsorbedFlux("SW", [receiver])[0])

    def test_seeded_context_makes_runBand_reproducible(self):
        assert self._seeded_diffuse_flux(7) == self._seeded_diffuse_flux(7)
