"""
Tests for the helios-core 1.3.92 PlantArchitecture changes that reach the Python API:
buildPlantCanopyFromLibrary() now honors its build_parameters (they were ignored natively, so every
plant in the canopy was built with the library defaults).
"""

import pytest

from pyhelios import Context, PlantArchitecture, PlantArchitectureError
from pyhelios.types import vec2, vec3, int2

from tests.test_plantarchitecture_phytomer import _require_plantarch


@pytest.mark.native_only
class TestCanopyBuildParameters:

    @pytest.mark.parametrize("num_scaffolds", [4, 6])
    def test_canopy_builds_the_requested_number_of_scaffolds(self, num_scaffolds):
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("pistachio")
            plant_ids = plantarch.buildPlantCanopyFromLibrary(
                canopy_center=vec3(0, 0, 0), plant_spacing=vec2(6.0, 6.0), plant_count=int2(2, 1),
                age=0.0, build_parameters={"num_scaffolds": num_scaffolds})
            assert len(plant_ids) == 2
            for plant_id in plant_ids:
                trunk = [s for s in plantarch.getAllShootIDs(plant_id)
                         if plantarch.getShoot(plant_id, s)["rank"] == 0]
                assert len(trunk) == 1
                assert len(plantarch.getShootChildIDs(plant_id, trunk[0])) == num_scaffolds

    def test_canopy_validates_build_parameters_natively(self):
        """An out-of-range value reaches the library model, which rejects it, instead of being dropped."""
        _require_plantarch()
        with Context() as context, PlantArchitecture(context) as plantarch:
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("grapevine_Wye")
            with pytest.raises(PlantArchitectureError, match="trunk_height"):
                plantarch.buildPlantCanopyFromLibrary(
                    canopy_center=vec3(0, 0, 0), plant_spacing=vec2(2.0, 3.0), plant_count=int2(1, 1),
                    age=0.0, build_parameters={"trunk_height": 0.165})
