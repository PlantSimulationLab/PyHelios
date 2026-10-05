"""
Tests for PlantHydraulicsModel integration
"""

import os

import pytest
from pyhelios import (
    Context,
    HeliosError,
    PlantHydraulicsModel,
    PlantHydraulicsModelError,
    PlantHydraulicsModelCoefficients,
    HydraulicConductance,
    HydraulicCapacitance,
)
from pyhelios.PlantHydraulics import AVAILABLE_SPECIES
from pyhelios.plugins.registry import get_plugin_registry
from pyhelios.types import vec2, vec3, int2, SphericalCoord

# Steady-state stem water potential (MPa) of a plant transpiring 100 W/m² with default conductances
# and a soil water potential of -0.05 MPa; the value checked by the native self-tests.
EXPECTED_STEM_POTENTIAL = -0.0590909


def add_plant(context, plant_id, center=None, size=None, subdiv=None, latent_flux=100.0):
    """Add a tile of leaves whose parent object carries a plantID. Returns the leaf UUIDs."""
    obj = context.addTileObject(center=center or vec3(0, 0, 0), size=size or vec2(1, 1),
                                rotation=SphericalCoord(1, 0, 0), subdiv=subdiv or int2(5, 5))
    leaves = context.getObjectPrimitiveUUIDs(obj)
    context.setObjectDataInt(obj, "plantID", plant_id)
    context.setPrimitiveDataFloat(leaves, "latent_flux", latent_flux)
    return leaves


def pistachio_coefficients():
    coeffs = PlantHydraulicsModelCoefficients()
    coeffs.setLeafHydraulicCapacitanceFromLibrary("pistachio")
    return coeffs


@pytest.mark.cross_platform
class TestPlantHydraulicsMetadata:
    """Test plugin metadata and registration"""

    def test_plugin_metadata_exists(self):
        from pyhelios.config.plugin_metadata import get_plugin_metadata

        metadata = get_plugin_metadata('planthydraulics')
        assert metadata is not None
        assert metadata.name == 'planthydraulics'
        assert metadata.description
        assert 'createPlantHydraulicsModel' in metadata.test_symbols
        assert metadata.gpu_required is False
        assert set(metadata.platforms) == {'windows', 'linux', 'macos'}

    def test_plugin_in_registry(self):
        from pyhelios.config.plugin_metadata import PLUGIN_METADATA
        assert 'planthydraulics' in PLUGIN_METADATA

    def test_plugin_in_integrated_list(self):
        """Plugin is part of the default build."""
        build_script = os.path.join(
            os.path.dirname(__file__), '..', 'build_scripts', 'build_helios.py')
        if not os.path.exists(build_script):
            # Wheel test environments copy only tests/ into an isolated directory,
            # so the build script this asserts on is not present.
            pytest.skip("Build script not available in wheel testing environment "
                        "(build_scripts/build_helios.py not found)")
        with open(build_script) as handle:
            source = handle.read()
        integrated = source.split('INTEGRATED_PLUGINS = [')[1].split(']')[0]
        assert 'planthydraulics' in integrated


@pytest.mark.cross_platform
class TestPlantHydraulicsInterface:
    """Test the Python interface without requiring the native library"""

    def test_class_structure(self):
        for name in ('__init__', '__enter__', '__exit__', '__del__', 'getNativePtr',
                     'setModelCoefficients', 'setModelCoefficientsFromLibrary', 'run',
                     'outputConductancePrimitiveData', 'outputCapacitancePrimitiveData',
                     'groupPrimitivesIntoPlantObject', 'getPlantID', 'getUniquePlantIDs',
                     'getPrimitivesByPlantID', 'getPrimitivesWithoutPlantID',
                     'getStemWaterPotential', 'getStemWaterPotentialOfPlant',
                     'getRootWaterPotential', 'getRootWaterPotentialOfPlant',
                     'getSoilWaterPotential', 'getSoilWaterPotentialOfPlant',
                     'setSoilWaterPotentialOfPlant', 'computeOsmoticPotential',
                     'computeTurgorPressure', 'computeWaterPotential', 'computeConductance',
                     'computeCapacitance', 'is_available'):
            assert hasattr(PlantHydraulicsModel, name), name

    def test_error_type(self):
        assert issubclass(PlantHydraulicsModelError, HeliosError)

    def test_requires_context(self):
        with pytest.raises(TypeError, match="Context"):
            PlantHydraulicsModel("not a context")

    def test_unavailable_plugin_raises_actionable_error(self):
        if get_plugin_registry().is_plugin_available('planthydraulics'):
            pytest.skip("planthydraulics is available - cannot test unavailable scenario")
        with Context() as context:
            with pytest.raises(PlantHydraulicsModelError, match="build_helios"):
                PlantHydraulicsModel(context)

    def test_coefficient_defaults_match_native(self):
        coeffs = PlantHydraulicsModelCoefficients()
        for conductance in (coeffs.LeafHydraulicConductance, coeffs.StemHydraulicConductance,
                            coeffs.RootHydraulicConductance):
            assert conductance == HydraulicConductance(0.5, 0.0, 0.0, False)
        for capacitance in (coeffs.LeafHydraulicCapacitance, coeffs.StemHydraulicCapacitance,
                            coeffs.RootHydraulicCapacitance):
            assert capacitance == HydraulicCapacitance(-2.0, 0.8, 1.0, 1.0, -1.0)
        assert coeffs.leaf_capacitance_species is None
        coeffs.validate()

    def test_conductance_setter_forms(self):
        coeffs = PlantHydraulicsModelCoefficients()

        coeffs.setLeafHydraulicConductance(0.3)
        assert coeffs.LeafHydraulicConductance == HydraulicConductance(0.3, 0.0, 0.0, False)

        # Two-argument form takes the native default sensitivity of 5
        coeffs.setStemHydraulicConductance(0.3, -1.5)
        assert coeffs.StemHydraulicConductance == HydraulicConductance(0.3, -1.5, 5.0, False)

        coeffs.setRootHydraulicConductance(0.3, -1.5, 2.0, True)
        assert coeffs.RootHydraulicConductance == HydraulicConductance(0.3, -1.5, 2.0, True)

    def test_temperature_dependence_setters_touch_only_their_compartment(self):
        coeffs = PlantHydraulicsModelCoefficients()
        coeffs.setStemHydraulicConductanceTemperatureDependence(True)
        assert coeffs.StemHydraulicConductance.temperature_dependence is True
        assert coeffs.LeafHydraulicConductance.temperature_dependence is False
        assert coeffs.RootHydraulicConductance.temperature_dependence is False

    def test_capacitance_setter_forms(self):
        coeffs = PlantHydraulicsModelCoefficients()

        coeffs.setStemHydraulicCapacitance(0.5)
        assert coeffs.StemHydraulicCapacitance.is_constant()
        assert coeffs.StemHydraulicCapacitance.fixed_constant_capacitance == 0.5

        coeffs.setRootHydraulicCapacitance(-1.5, 0.75, 2.0)
        assert not coeffs.RootHydraulicCapacitance.is_constant()
        assert coeffs.RootHydraulicCapacitance == HydraulicCapacitance(-1.5, 0.75, 2.0, 1.0, -1.0)

        coeffs.setLeafHydraulicCapacitance(-1.5, 0.75, 2.0, 10.0)
        assert coeffs.LeafHydraulicCapacitance.saturated_specific_water_content == 10.0

    def test_library_leaf_capacitance_replaces_and_is_replaced(self):
        coeffs = PlantHydraulicsModelCoefficients()
        coeffs.setLeafHydraulicCapacitanceFromLibrary("Walnut")
        assert coeffs.leaf_capacitance_species == "Walnut"
        assert coeffs.LeafHydraulicCapacitance is None
        coeffs.validate()

        coeffs.setLeafHydraulicCapacitance(-1.5, 0.75)
        assert coeffs.leaf_capacitance_species is None
        assert coeffs.LeafHydraulicCapacitance is not None

    def test_coefficient_array_layout(self):
        coeffs = PlantHydraulicsModelCoefficients()
        coeffs.setLeafHydraulicConductance(0.1, -1.0, 2.0, True)
        coeffs.setStemHydraulicConductance(0.2)
        coeffs.setRootHydraulicConductance(0.3, -3.0)
        coeffs.setLeafHydraulicCapacitance(-1.5, 0.75, 2.0, 10.0)
        coeffs.setStemHydraulicCapacitance(0.4)
        coeffs.setRootHydraulicCapacitance(-2.5, 0.9, 1.5)
        assert coeffs.to_list() == pytest.approx([
            0.1, -1.0, 2.0, 1.0,
            0.2, 0.0, 0.0, 0.0,
            0.3, -3.0, 5.0, 0.0,
            -1.5, 0.75, 2.0, 10.0, -1.0,
            -2.0, 0.8, 1.0, 0.4,
            -2.5, 0.9, 1.5, -1.0,
        ])

    def test_from_list_inverts_to_list(self):
        coeffs = PlantHydraulicsModelCoefficients()
        coeffs.setLeafHydraulicConductance(0.1, -1.0, 2.0, True)
        coeffs.setRootHydraulicConductance(0.3, -3.0)
        coeffs.setLeafHydraulicCapacitance(-1.5, 0.75, 2.0, 10.0)
        coeffs.setStemHydraulicCapacitance(0.4)
        coeffs.setRootHydraulicCapacitance(-2.5, 0.9, 1.5)

        rebuilt = PlantHydraulicsModelCoefficients.from_list(coeffs.to_list())
        assert rebuilt.to_list() == coeffs.to_list()
        assert rebuilt.LeafHydraulicConductance == coeffs.LeafHydraulicConductance
        assert rebuilt.StemHydraulicConductance.temperature_dependence is False
        assert rebuilt.StemHydraulicCapacitance == coeffs.StemHydraulicCapacitance
        assert rebuilt.leaf_capacitance_species is None
        rebuilt.validate()

    @pytest.mark.parametrize("size", [0, 24, 26])
    def test_from_list_rejects_wrong_length(self, size):
        with pytest.raises(ValueError, match="25"):
            PlantHydraulicsModelCoefficients.from_list([0.0] * size)

    @pytest.mark.parametrize("species", ["Almond", "WALNUT", "", "pistachio "])
    def test_unknown_species_rejected(self, species):
        with pytest.raises(ValueError, match="unknown species"):
            PlantHydraulicsModelCoefficients().setLeafHydraulicCapacitanceFromLibrary(species)

    def test_non_string_species_rejected(self):
        with pytest.raises(ValueError, match="must be a string"):
            PlantHydraulicsModelCoefficients().setLeafHydraulicCapacitanceFromLibrary(3)

    @pytest.mark.parametrize("value", [0.0, -0.5, float('nan'), float('inf'), "0.5", True])
    def test_invalid_conductance_rejected(self, value):
        coeffs = PlantHydraulicsModelCoefficients()
        for setter in (coeffs.setLeafHydraulicConductance, coeffs.setStemHydraulicConductance,
                       coeffs.setRootHydraulicConductance):
            with pytest.raises(ValueError):
                setter(value)

    def test_invalid_conductance_arguments_rejected(self):
        coeffs = PlantHydraulicsModelCoefficients()
        with pytest.raises(ValueError, match="sensitivity must be >= 0"):
            coeffs.setLeafHydraulicConductance(0.5, -1.5, -1.0)
        with pytest.raises(ValueError, match="requires potential_at_half_saturated"):
            coeffs.setLeafHydraulicConductance(0.5, sensitivity=2.0)
        with pytest.raises(ValueError, match="must be a bool"):
            coeffs.setLeafHydraulicConductance(0.5, -1.5, 2.0, 1)
        with pytest.raises(ValueError, match="must be a bool"):
            coeffs.setLeafHydraulicConductanceTemperatureDependence("yes")

    def test_invalid_capacitance_rejected(self):
        coeffs = PlantHydraulicsModelCoefficients()
        with pytest.raises(ValueError, match="capacitance must be > 0"):
            coeffs.setLeafHydraulicCapacitance(0.0)
        with pytest.raises(ValueError, match="capacitance must be > 0"):
            coeffs.setStemHydraulicCapacitance(-2.0)
        with pytest.raises(ValueError, match="osmotic_potential_at_full_turgor must be < 0"):
            coeffs.setLeafHydraulicCapacitance(2.0, 0.8)
        with pytest.raises(ValueError, match="relative_water_content_at_turgor_loss"):
            coeffs.setLeafHydraulicCapacitance(-2.0, 1.0)
        with pytest.raises(ValueError, match="cell_wall_elasticity_exponent"):
            coeffs.setRootHydraulicCapacitance(-2.0, 0.8, 0.0)
        with pytest.raises(ValueError, match="saturated_specific_water_content"):
            coeffs.setLeafHydraulicCapacitance(-2.0, 0.8, 1.0, 0.0)
        with pytest.raises(ValueError, match="capacitance must be > 0"):
            HydraulicCapacitance.constant(0.0)

    def test_validate_catches_directly_assigned_values(self):
        coeffs = PlantHydraulicsModelCoefficients()
        coeffs.StemHydraulicConductance.saturated_conductance = 0.0
        with pytest.raises(ValueError, match="saturated_conductance must be > 0"):
            coeffs.validate()

        coeffs = PlantHydraulicsModelCoefficients()
        coeffs.RootHydraulicCapacitance = None
        with pytest.raises(ValueError, match="RootHydraulicCapacitance must be a HydraulicCapacitance"):
            coeffs.validate()

        coeffs = PlantHydraulicsModelCoefficients()
        coeffs.StemHydraulicCapacitance.saturated_specific_water_content = 5.0
        with pytest.raises(ValueError, match="only for leaves"):
            coeffs.validate()

        coeffs = PlantHydraulicsModelCoefficients()
        coeffs.leaf_capacitance_species = "Almond"
        with pytest.raises(ValueError, match="unknown species"):
            coeffs.validate()

    def test_curve_functions_validate_before_reaching_native(self):
        capacitance = HydraulicCapacitance()
        with pytest.raises(ValueError, match="must be a HydraulicCapacitance"):
            PlantHydraulicsModel.computeWaterPotential(HydraulicConductance(), 0.9)
        with pytest.raises(ValueError, match=r"relative_water_content must be in \(0, 1\]"):
            PlantHydraulicsModel.computeWaterPotential(capacitance, 0.0)
        with pytest.raises(ValueError, match=r"relative_water_content must be in \(0, 1\]"):
            PlantHydraulicsModel.computeOsmoticPotential(capacitance, 1.5)
        with pytest.raises(ValueError, match="must be a HydraulicConductance"):
            PlantHydraulicsModel.computeConductance(capacitance, -1.0)
        with pytest.raises(ValueError, match="temperature must be > 0"):
            PlantHydraulicsModel.computeConductance(HydraulicConductance(), -1.0, 0.0)


@pytest.fixture
def context(check_native_library):
    context = Context()
    yield context
    context.__exit__(None, None, None)


@pytest.fixture
def hydraulics(context):
    model = PlantHydraulicsModel(context)
    yield model
    model.__exit__(None, None, None)


@pytest.mark.native_only
class TestPlantHydraulicsFunctionality:
    """Test plugin functionality with the native library"""

    def test_create_and_destroy(self, context):
        with PlantHydraulicsModel(context) as model:
            assert model.getNativePtr() is not None
            assert model.is_available()
        assert model.getNativePtr() is None

    def test_cleanup_without_with_statement(self, context):
        import gc
        import warnings
        model = PlantHydraulicsModel(context)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            del model
            gc.collect()

    def test_steady_state_matches_native_reference(self, context, hydraulics):
        leaves = add_plant(context, plant_id=1)
        hydraulics.setModelCoefficients(pistachio_coefficients())

        plant_id = hydraulics.getPlantID(leaves)
        assert plant_id == 1
        hydraulics.setSoilWaterPotentialOfPlant(plant_id, -0.05)
        hydraulics.run(leaves)

        for leaf in leaves:
            assert hydraulics.getStemWaterPotential(leaf) == pytest.approx(EXPECTED_STEM_POTENTIAL, rel=1e-5)
        assert hydraulics.getStemWaterPotential(leaves) == pytest.approx(EXPECTED_STEM_POTENTIAL, rel=1e-5)
        assert hydraulics.getStemWaterPotentialOfPlant(1) == pytest.approx(EXPECTED_STEM_POTENTIAL, rel=1e-5)

        # psi_root = psi_soil - E/K_root and psi_stem = psi_root - E/K_stem, with E = 100/44000 mol/m²/s
        transpiration = 100.0 / 44000.0
        assert hydraulics.getSoilWaterPotential(leaves[0]) == pytest.approx(-0.05, rel=1e-5)
        assert hydraulics.getRootWaterPotential(leaves[0]) == pytest.approx(-0.05 - transpiration / 0.5, rel=1e-5)
        assert hydraulics.getRootWaterPotentialOfPlant(1) == pytest.approx(-0.05 - transpiration / 0.5, rel=1e-5)
        assert hydraulics.getRootWaterPotential(leaves) == pytest.approx(-0.05 - transpiration / 0.5, rel=1e-5)
        assert hydraulics.getSoilWaterPotential(leaves) == pytest.approx(-0.05, rel=1e-5)

    def test_leaf_outputs(self, context, hydraulics):
        leaves = add_plant(context, plant_id=1)
        hydraulics.setModelCoefficients(pistachio_coefficients())
        hydraulics.setSoilWaterPotentialOfPlant(1, -0.05)
        hydraulics.run(leaves)

        transpiration = 100.0 / 44000.0
        expected_leaf_potential = EXPECTED_STEM_POTENTIAL - transpiration / 0.5
        for leaf in leaves:
            water_potential = context.getPrimitiveData(leaf, "water_potential", float)
            turgor = context.getPrimitiveData(leaf, "turgor_pressure", float)
            osmotic = context.getPrimitiveData(leaf, "osmotic_potential", float)
            water_content = context.getPrimitiveData(leaf, "relative_water_content", float)

            assert water_potential == pytest.approx(expected_leaf_potential, rel=1e-4)
            assert water_potential == pytest.approx(turgor + osmotic, abs=1e-5)
            assert turgor > 0.0
            assert osmotic < 0.0
            assert 0.9 < water_content <= 1.0

        # Optional outputs are written by non-steady-state runs only
        assert not context.doesPrimitiveDataExist(leaves[0], "hydraulic_conductance")
        assert not context.doesPrimitiveDataExist(leaves[0], "hydraulic_capacitance")

    def test_run_all_primitives(self, context, hydraulics):
        leaves = add_plant(context, plant_id=1)
        hydraulics.setModelCoefficients(pistachio_coefficients())
        hydraulics.setSoilWaterPotentialOfPlant(1, -0.05)
        hydraulics.run()
        assert hydraulics.getStemWaterPotential(leaves[0]) == pytest.approx(EXPECTED_STEM_POTENTIAL, rel=1e-5)

    def test_potentials_independent_of_leaf_area(self, context, hydraulics):
        small = add_plant(context, plant_id=1)
        large = add_plant(context, plant_id=2, center=vec3(10, 0, 0), size=vec2(2, 2))
        assert context.sumPrimitiveSurfaceArea(large) == pytest.approx(4.0 * context.sumPrimitiveSurfaceArea(small), rel=1e-5)

        hydraulics.setModelCoefficients(pistachio_coefficients())
        hydraulics.setSoilWaterPotentialOfPlant(1, -0.05)
        hydraulics.setSoilWaterPotentialOfPlant(2, -0.05)
        hydraulics.run(small + large)

        assert sorted(hydraulics.getUniquePlantIDs(small + large)) == [1, 2]
        assert hydraulics.getStemWaterPotentialOfPlant(1) == pytest.approx(EXPECTED_STEM_POTENTIAL, rel=1e-5)
        assert hydraulics.getStemWaterPotentialOfPlant(2) == pytest.approx(EXPECTED_STEM_POTENTIAL, rel=1e-5)
        assert hydraulics.getRootWaterPotentialOfPlant(2) == pytest.approx(
            hydraulics.getRootWaterPotentialOfPlant(1), rel=1e-5)

    def test_soil_water_potential_shifts_the_whole_plant(self, context, hydraulics):
        leaves = add_plant(context, plant_id=1)
        hydraulics.setModelCoefficients(pistachio_coefficients())

        hydraulics.setSoilWaterPotentialOfPlant(1, -0.05)
        hydraulics.run(leaves)
        wet = hydraulics.getStemWaterPotentialOfPlant(1)

        hydraulics.setSoilWaterPotentialOfPlant(1, -1.05)
        assert hydraulics.getSoilWaterPotentialOfPlant(1) == pytest.approx(-1.05)
        hydraulics.run(leaves)
        assert hydraulics.getStemWaterPotentialOfPlant(1) == pytest.approx(wet - 1.0, rel=1e-5)

    def test_custom_conductances(self, context, hydraulics):
        leaves = add_plant(context, plant_id=1)
        coeffs = PlantHydraulicsModelCoefficients()
        coeffs.setRootHydraulicConductance(0.25)
        coeffs.setStemHydraulicConductance(0.1)
        coeffs.setLeafHydraulicConductance(0.05)
        hydraulics.setModelCoefficients(coeffs)
        hydraulics.setSoilWaterPotentialOfPlant(1, -0.2)
        hydraulics.run(leaves)

        transpiration = 100.0 / 44000.0
        root = -0.2 - transpiration / 0.25
        stem = root - transpiration / 0.1
        assert hydraulics.getRootWaterPotentialOfPlant(1) == pytest.approx(root, rel=1e-5)
        assert hydraulics.getStemWaterPotentialOfPlant(1) == pytest.approx(stem, rel=1e-5)
        assert context.getPrimitiveData(leaves[0], "water_potential", float) == pytest.approx(
            stem - transpiration / 0.05, rel=1e-4)

    def test_stem_and_root_coefficients_are_not_swapped(self, context, hydraulics):
        """Temperature dependence on the stem only must change the stem drop and not the root drop."""
        leaves = add_plant(context, plant_id=1)
        context.setPrimitiveDataFloat(leaves, "air_temperature", 310.0)
        coeffs = PlantHydraulicsModelCoefficients()
        coeffs.setStemHydraulicConductanceTemperatureDependence(True)
        hydraulics.setModelCoefficients(coeffs)
        hydraulics.setSoilWaterPotentialOfPlant(1, -0.05)
        hydraulics.run(leaves)

        transpiration = 100.0 / 44000.0
        root = -0.05 - transpiration / 0.5
        stem = root - transpiration / (0.5 * (310.0 / 298.15) ** 7)
        assert hydraulics.getRootWaterPotentialOfPlant(1) == pytest.approx(root, rel=1e-5)
        assert hydraulics.getStemWaterPotentialOfPlant(1) == pytest.approx(stem, rel=1e-5)

    def test_per_primitive_coefficients(self, context, hydraulics):
        leaves = add_plant(context, plant_id=1, subdiv=int2(2, 2))

        high = PlantHydraulicsModelCoefficients()
        high.setLeafHydraulicCapacitanceFromLibrary("Walnut")
        high.setLeafHydraulicConductance(1.0)
        low = PlantHydraulicsModelCoefficients()
        low.setLeafHydraulicCapacitanceFromLibrary("Walnut")
        low.setLeafHydraulicConductance(0.1)

        hydraulics.setModelCoefficients(high, leaves[:2])
        hydraulics.setModelCoefficients(low, UUIDs=leaves[2:])
        hydraulics.setSoilWaterPotentialOfPlant(1, -0.05)
        hydraulics.run(leaves)

        transpiration = 100.0 / 44000.0
        stem = hydraulics.getStemWaterPotentialOfPlant(1)
        assert context.getPrimitiveData(leaves[0], "water_potential", float) == pytest.approx(
            stem - transpiration / 1.0, rel=1e-4)
        assert context.getPrimitiveData(leaves[3], "water_potential", float) == pytest.approx(
            stem - transpiration / 0.1, rel=1e-4)

    def test_library_species_matches_explicit_parameters(self, context, hydraulics):
        """The species name reaches the native library: pistachio is (-3.096, 0.7652, 2)."""
        leaves = add_plant(context, plant_id=1, latent_flux=4000.0)
        hydraulics.setSoilWaterPotentialOfPlant(1, -0.05)

        def turgor_with(coeffs):
            hydraulics.setModelCoefficients(coeffs)
            hydraulics.run(leaves)
            return context.getPrimitiveData(leaves[0], "turgor_pressure", float)

        explicit = PlantHydraulicsModelCoefficients()
        explicit.setLeafHydraulicCapacitance(-3.096, 0.7652, 2.0)

        library_turgor = turgor_with(pistachio_coefficients())
        assert library_turgor == pytest.approx(turgor_with(explicit), rel=1e-5)
        assert library_turgor != pytest.approx(turgor_with(PlantHydraulicsModelCoefficients()), rel=1e-2)

    def test_set_coefficients_from_library(self, context, hydraulics):
        leaves = add_plant(context, plant_id=1, latent_flux=4000.0)
        hydraulics.setSoilWaterPotentialOfPlant(1, -0.05)

        hydraulics.setModelCoefficientsFromLibrary("pistachio")
        hydraulics.run(leaves)
        pistachio = context.getPrimitiveData(leaves[0], "turgor_pressure", float)

        hydraulics.setModelCoefficients(pistachio_coefficients())
        hydraulics.run(leaves)
        assert context.getPrimitiveData(leaves[0], "turgor_pressure", float) == pytest.approx(pistachio, rel=1e-5)

        # A per-primitive library entry overrides the global coefficients for that leaf only
        hydraulics.setModelCoefficientsFromLibrary("Walnut", leaves[0])
        hydraulics.setModelCoefficientsFromLibrary("Walnut", [leaves[1]])
        hydraulics.run(leaves)
        walnut = context.getPrimitiveData(leaves[0], "turgor_pressure", float)
        assert walnut != pytest.approx(pistachio, rel=1e-2)
        assert context.getPrimitiveData(leaves[1], "turgor_pressure", float) == pytest.approx(walnut, rel=1e-5)
        assert context.getPrimitiveData(leaves[2], "turgor_pressure", float) == pytest.approx(pistachio, rel=1e-5)

    def test_get_coefficients_round_trip(self, context, hydraulics):
        leaves = add_plant(context, plant_id=1, subdiv=int2(2, 2))

        coeffs = PlantHydraulicsModelCoefficients()
        coeffs.setLeafHydraulicConductance(0.1, -1.0, 2.0, True)
        coeffs.setStemHydraulicConductance(0.2)
        coeffs.setRootHydraulicConductance(0.3, -3.0)
        coeffs.setLeafHydraulicCapacitance(-1.5, 0.75, 2.0, 10.0)
        coeffs.setStemHydraulicCapacitance(0.4)
        coeffs.setRootHydraulicCapacitance(-2.5, 0.9, 1.5)
        other = PlantHydraulicsModelCoefficients()
        other.setLeafHydraulicCapacitance(0.25)

        hydraulics.setModelCoefficients(coeffs, [leaves[0]])
        hydraulics.setModelCoefficients(other, [leaves[1]])

        read = hydraulics.getModelCoefficients(leaves[0])
        assert isinstance(read, PlantHydraulicsModelCoefficients)
        assert read.to_list() == pytest.approx(coeffs.to_list(), rel=1e-6)
        assert read.LeafHydraulicConductance.temperature_dependence is True
        assert read.StemHydraulicCapacitance.is_constant()
        assert not read.RootHydraulicCapacitance.is_constant()
        read.validate()

        read_other = hydraulics.getModelCoefficients(leaves[1])
        assert read_other.to_list() == pytest.approx(other.to_list(), rel=1e-6)
        assert read_other.LeafHydraulicCapacitance.is_constant()

    def test_get_coefficients_returns_library_leaf_capacitance_as_values(self, context, hydraulics):
        leaves = add_plant(context, plant_id=1)
        coeffs = pistachio_coefficients()
        coeffs.setLeafHydraulicConductance(0.05)
        hydraulics.setModelCoefficients(coeffs, [leaves[0]])

        read = hydraulics.getModelCoefficients(leaves[0])
        assert read.leaf_capacitance_species is None
        leaf = read.LeafHydraulicCapacitance
        assert (leaf.osmotic_potential_at_full_turgor, leaf.relative_water_content_at_turgor_loss,
                leaf.cell_wall_elasticity_exponent) == pytest.approx((-3.096, 0.7652, 2.0), rel=1e-6)
        assert read.LeafHydraulicConductance.saturated_conductance == pytest.approx(0.05)

    @pytest.mark.parametrize("species, expected", [
        ("Walnut", (-1.6386, 0.7683, 2.0)),
        ("pistachio", (-3.096, 0.7652, 2.0)),
        ("Elderberry", (-2.011, 0.8135, 2.0)),
        ("redbud", (-2.1963, 0.8872, 1.5)),
    ])
    def test_get_coefficients_from_library(self, hydraulics, species, expected):
        coeffs = hydraulics.getModelCoefficientsFromLibrary(species)
        leaf = coeffs.LeafHydraulicCapacitance
        assert (leaf.osmotic_potential_at_full_turgor, leaf.relative_water_content_at_turgor_loss,
                leaf.cell_wall_elasticity_exponent) == pytest.approx(expected, rel=1e-6)
        assert coeffs.leaf_capacitance_species is None

        defaults = PlantHydraulicsModelCoefficients().to_list()
        assert coeffs.to_list()[:12] == pytest.approx(defaults[:12])
        assert coeffs.to_list()[15:] == pytest.approx(defaults[15:])

    def test_library_coefficients_can_be_modified_and_set(self, context, hydraulics):
        leaves = add_plant(context, plant_id=1, latent_flux=4000.0)
        hydraulics.setSoilWaterPotentialOfPlant(1, -0.05)

        hydraulics.setModelCoefficientsFromLibrary("pistachio")
        hydraulics.run(leaves)
        expected = context.getPrimitiveData(leaves[0], "turgor_pressure", float)

        hydraulics.setModelCoefficients(hydraulics.getModelCoefficientsFromLibrary("pistachio"))
        hydraulics.run(leaves)
        assert context.getPrimitiveData(leaves[0], "turgor_pressure", float) == pytest.approx(expected, rel=1e-5)

    @pytest.mark.parametrize("species", AVAILABLE_SPECIES)
    def test_every_listed_species_is_accepted(self, context, hydraulics, species):
        leaves = add_plant(context, plant_id=1, subdiv=int2(1, 1))
        hydraulics.setModelCoefficientsFromLibrary(species)
        hydraulics.run(leaves)
        assert context.getPrimitiveData(leaves[0], "turgor_pressure", float) > 0.0

    def test_ungrouped_primitives_are_grouped_by_run(self, context, hydraulics):
        leaves = [context.addPatch(center=vec3(i, 0, 0), size=vec2(0.1, 0.1)) for i in range(3)]
        context.setPrimitiveDataFloat(leaves, "latent_flux", 100.0)

        assert hydraulics.getPrimitivesWithoutPlantID(leaves) == leaves
        hydraulics.run(leaves)
        assert hydraulics.getPrimitivesWithoutPlantID(leaves) == []

        plant_id = hydraulics.getPlantID(leaves)
        assert hydraulics.getUniquePlantIDs(leaves) == [plant_id]
        assert sorted(hydraulics.getPrimitivesByPlantID(plant_id)) == sorted(leaves)
        assert all(context.getPrimitiveParentObjectID(leaf) != 0 for leaf in leaves)

    def test_group_primitives_into_plant_object(self, context, hydraulics):
        first = [context.addPatch(center=vec3(i, 0, 0), size=vec2(0.1, 0.1)) for i in range(2)]
        second = [context.addPatch(center=vec3(i, 5, 0), size=vec2(0.1, 0.1)) for i in range(2)]

        first_id = hydraulics.groupPrimitivesIntoPlantObject(first)
        second_id = hydraulics.groupPrimitivesIntoPlantObject(second)
        assert first_id != second_id
        assert hydraulics.getPlantID(first[0]) == first_id
        assert hydraulics.getPlantID(second) == second_id
        assert sorted(hydraulics.getPrimitivesByPlantID(first_id)) == sorted(first)
        assert hydraulics.getPrimitivesByPlantID(987654) == []

    def test_plant_id_from_primitive_data(self, context, hydraulics):
        leaf1 = context.addPatch(center=vec3(0, 0, 0), size=vec2(0.1, 0.1))
        leaf2 = context.addPatch(center=vec3(1, 0, 0), size=vec2(0.1, 0.1))
        context.setPrimitiveDataInt(leaf1, "plantID", 7)
        context.setPrimitiveDataInt(leaf2, "plantID", 9)

        assert hydraulics.getPlantID(leaf1) == 7
        assert hydraulics.getPlantID(leaf2) == 9
        assert sorted(hydraulics.getUniquePlantIDs([leaf1, leaf2])) == [7, 9]
        assert hydraulics.getPrimitivesByPlantID(9) == [leaf2]

    def test_transient_run(self, context, hydraulics):
        def leaf_potential(saturated_water_content):
            leaves = add_plant(context, plant_id=leaf_potential.next_id, subdiv=int2(3, 3), latent_flux=200.0,
                               center=vec3(10 * leaf_potential.next_id, 0, 0))
            context.setPrimitiveDataFloat(leaves, "relative_water_content", 0.95)
            context.setPrimitiveDataFloat(leaves, "water_potential", -0.5)

            coeffs = PlantHydraulicsModelCoefficients()
            coeffs.setLeafHydraulicCapacitance(-1.6386, 0.7683, 2.0, saturated_water_content)
            coeffs.setStemHydraulicCapacitance(0.1)
            coeffs.setRootHydraulicCapacitance(0.1)
            hydraulics.setModelCoefficients(coeffs)
            hydraulics.setSoilWaterPotentialOfPlant(leaf_potential.next_id, -0.05)
            hydraulics.outputConductancePrimitiveData(True)
            hydraulics.outputCapacitancePrimitiveData(True)
            hydraulics.run(leaves, timespan=100, timestep=10)
            leaf_potential.next_id += 1

            assert context.getPrimitiveData(leaves[0], "hydraulic_conductance", float) == pytest.approx(0.5)
            assert context.getPrimitiveData(leaves[0], "hydraulic_capacitance", float) > 0.0
            return context.getPrimitiveData(leaves[0], "water_potential", float)

        leaf_potential.next_id = 1
        # A larger leaf water reservoir buffers the change in leaf water potential
        assert leaf_potential(1.0) != pytest.approx(leaf_potential(10.0), rel=1e-3)

    def test_curve_functions(self):
        walnut = HydraulicCapacitance(-1.6386, 0.7683, 2.0)
        w = 0.9
        turgor = 1.6386 * ((w - 0.7683) / (1.0 - 0.7683)) ** 2
        osmotic = -1.6386 / w

        assert PlantHydraulicsModel.computeTurgorPressure(walnut, w) == pytest.approx(turgor, rel=1e-5)
        assert PlantHydraulicsModel.computeOsmoticPotential(walnut, w) == pytest.approx(osmotic, rel=1e-5)
        assert PlantHydraulicsModel.computeWaterPotential(walnut, w) == pytest.approx(turgor + osmotic, rel=1e-5)
        # Below the turgor loss point there is no turgor
        assert PlantHydraulicsModel.computeTurgorPressure(walnut, 0.5) == 0.0
        # At full hydration turgor balances osmotic potential
        assert PlantHydraulicsModel.computeWaterPotential(walnut, 1.0) == pytest.approx(0.0, abs=1e-6)

        slope = 2.0 * 1.6386 * (w - 0.7683) / (1.0 - 0.7683) ** 2 + 1.6386 / w ** 2
        assert PlantHydraulicsModel.computeCapacitance(walnut, w) == pytest.approx(1.0 / slope, rel=5e-3)
        assert PlantHydraulicsModel.computeCapacitance(HydraulicCapacitance.constant(0.3), w) == pytest.approx(0.3)

    def test_conductance_function(self):
        vulnerable = HydraulicConductance(0.5, -2.0, 3.0)
        assert PlantHydraulicsModel.computeConductance(vulnerable, -1.5) == pytest.approx(
            0.5 / (1.0 + 0.75 ** 3), rel=1e-5)
        assert PlantHydraulicsModel.computeConductance(vulnerable, -2.0) == pytest.approx(0.25, rel=1e-5)
        assert PlantHydraulicsModel.computeConductance(HydraulicConductance(0.5), -5.0, 310.0) == pytest.approx(0.5)

        warm = HydraulicConductance(0.5, temperature_dependence=True)
        assert PlantHydraulicsModel.computeConductance(warm, -1.0, 310.0) == pytest.approx(
            0.5 * (310.0 / 298.15) ** 7, rel=1e-5)


@pytest.mark.native_only
class TestPlantHydraulicsErrorHandling:
    """Test that invalid use raises instead of returning misleading values"""

    def test_set_coefficients_rejects_wrong_types(self, hydraulics):
        with pytest.raises(ValueError, match="must be a PlantHydraulicsModelCoefficients"):
            hydraulics.setModelCoefficients(HydraulicConductance())
        with pytest.raises(ValueError, match="must be a PlantHydraulicsModelCoefficients"):
            hydraulics.setModelCoefficients(modelcoefficients=[0.5] * 25)
        with pytest.raises(ValueError, match="UUIDs cannot be empty"):
            hydraulics.setModelCoefficients(PlantHydraulicsModelCoefficients(), [])
        with pytest.raises(ValueError, match="UUIDs must be a list"):
            hydraulics.setModelCoefficients(PlantHydraulicsModelCoefficients(), 5)

    def test_set_coefficients_validates_values(self, hydraulics):
        coeffs = PlantHydraulicsModelCoefficients()
        coeffs.LeafHydraulicConductance.saturated_conductance = 0.0
        with pytest.raises(ValueError, match="saturated_conductance must be > 0"):
            hydraulics.setModelCoefficients(coeffs)

    def test_unknown_species_rejected(self, hydraulics):
        with pytest.raises(ValueError, match="unknown species"):
            hydraulics.setModelCoefficientsFromLibrary("Almond")
        with pytest.raises(ValueError, match="must be a string"):
            hydraulics.setModelCoefficientsFromLibrary(species=None)

    def test_run_argument_validation(self, context, hydraulics):
        leaves = add_plant(context, plant_id=1)
        with pytest.raises(ValueError, match="UUIDs cannot be empty"):
            hydraulics.run([])
        with pytest.raises(ValueError, match="timespan must be >= 0"):
            hydraulics.run(leaves, timespan=-1)
        with pytest.raises(ValueError, match="timestep must be >= 1"):
            hydraulics.run(leaves, timespan=100, timestep=0)
        with pytest.raises(ValueError, match="timespan must be an integer"):
            hydraulics.run(leaves, timespan=10.5)
        with pytest.raises(ValueError, match="UUID must be an integer"):
            hydraulics.run([1.5])
        with pytest.raises(ValueError, match="UUIDs must be a list"):
            hydraulics.run("12")

    def test_toggle_validation(self, hydraulics):
        with pytest.raises(ValueError, match="must be a bool"):
            hydraulics.outputConductancePrimitiveData(1)
        with pytest.raises(ValueError, match="must be a bool"):
            hydraulics.outputCapacitancePrimitiveData("on")

    def test_water_potential_before_run_raises(self, context, hydraulics):
        leaves = add_plant(context, plant_id=1)
        with pytest.raises(PlantHydraulicsModelError, match="run\\(\\)"):
            hydraulics.getStemWaterPotential(leaves[0])
        with pytest.raises(PlantHydraulicsModelError, match="run\\(\\)"):
            hydraulics.getRootWaterPotentialOfPlant(1)
        with pytest.raises(PlantHydraulicsModelError, match="setSoilWaterPotentialOfPlant"):
            hydraulics.getSoilWaterPotentialOfPlant(42)

    def test_primitive_without_plant_id_raises(self, context, hydraulics):
        leaf = context.addPatch(center=vec3(0, 0, 0), size=vec2(0.1, 0.1))
        with pytest.raises(PlantHydraulicsModelError, match="plantID"):
            hydraulics.getPlantID(leaf)
        with pytest.raises(PlantHydraulicsModelError, match="plantID"):
            hydraulics.getUniquePlantIDs([leaf])

    def test_primitives_of_different_plants_raise(self, context, hydraulics):
        first = add_plant(context, plant_id=1)
        second = add_plant(context, plant_id=2, center=vec3(10, 0, 0))
        with pytest.raises(PlantHydraulicsModelError, match="do not share the same plantID"):
            hydraulics.getPlantID(first + second)

    def test_mixed_plants_in_the_middle_of_a_list_raise(self, context, hydraulics):
        """The native list overloads compare only the first and last primitive."""
        first = add_plant(context, plant_id=1)
        second = add_plant(context, plant_id=2, center=vec3(10, 0, 0))
        hydraulics.run(first + second)
        mixed = [first[0], second[0], first[1]]
        with pytest.raises(PlantHydraulicsModelError, match="do not share the same plantID"):
            hydraulics.getPlantID(mixed)
        with pytest.raises(PlantHydraulicsModelError, match="do not share the same plantID"):
            hydraulics.getStemWaterPotential(mixed)

    def test_per_primitive_coefficients_do_not_change_stem_or_root(self, context, hydraulics):
        leaves = add_plant(context, plant_id=1)
        per_leaf = PlantHydraulicsModelCoefficients()
        per_leaf.setStemHydraulicConductance(0.05)
        per_leaf.setRootHydraulicConductance(0.05)
        hydraulics.setModelCoefficients(per_leaf, leaves)
        hydraulics.setSoilWaterPotentialOfPlant(1, -0.05)
        hydraulics.run(leaves)
        assert hydraulics.getStemWaterPotentialOfPlant(1) == pytest.approx(EXPECTED_STEM_POTENTIAL, rel=1e-5)

    def test_plant_without_latent_flux_does_not_transpire(self, context, hydraulics):
        bare = context.addTileObject(center=vec3(10, 0, 0), size=vec2(1, 1),
                                     rotation=SphericalCoord(1, 0, 0), subdiv=int2(2, 2))
        context.setObjectDataInt(bare, "plantID", 2)
        bare_leaves = context.getObjectPrimitiveUUIDs(bare)
        hydraulics.setSoilWaterPotentialOfPlant(2, -0.05)
        hydraulics.run(bare_leaves)
        assert hydraulics.getStemWaterPotentialOfPlant(2) == pytest.approx(-0.05, rel=1e-5)

    def test_capacitance_rejects_water_content_below_stencil(self):
        with pytest.raises(ValueError, match="must be > 0.001"):
            PlantHydraulicsModel.computeCapacitance(HydraulicCapacitance(), 0.0005)

    def test_regrouping_a_plant_raises(self, context, hydraulics):
        leaves = add_plant(context, plant_id=1)
        with pytest.raises(ValueError, match="already have a plantID"):
            hydraulics.groupPrimitivesIntoPlantObject(leaves)

    def test_regrouping_primitive_data_plants_raises(self, context, hydraulics):
        """The native check sees only object data, and would overwrite a primitive-data plantID."""
        leaves = [context.addPatch(center=vec3(i, 0, 0), size=vec2(0.1, 0.1)) for i in range(4)]
        first_id = hydraulics.groupPrimitivesIntoPlantObject(leaves[:2])
        with pytest.raises(ValueError, match="already have a plantID"):
            hydraulics.groupPrimitivesIntoPlantObject(leaves)
        assert hydraulics.getPlantID(leaves[:2]) == first_id
        assert hydraulics.getPrimitivesWithoutPlantID(leaves) == leaves[2:]

    def test_ungrouped_primitives_already_in_an_object_raise(self, context, hydraulics):
        tile = context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                     rotation=SphericalCoord(1, 0, 0), subdiv=int2(2, 2))
        leaves = context.getObjectPrimitiveUUIDs(tile)
        with pytest.raises(PlantHydraulicsModelError, match="already belong to another object"):
            hydraulics.run(leaves)
        with pytest.raises(PlantHydraulicsModelError, match="already belong to another object"):
            hydraulics.groupPrimitivesIntoPlantObject(leaves)

    def test_root_is_five_kelvin_cooler_than_air_temperature(self, context, hydraulics):
        leaves = add_plant(context, plant_id=1)
        context.setPrimitiveDataFloat(leaves, "air_temperature", 310.0)
        coeffs = PlantHydraulicsModelCoefficients()
        coeffs.setRootHydraulicConductanceTemperatureDependence(True)
        hydraulics.setModelCoefficients(coeffs)
        hydraulics.setSoilWaterPotentialOfPlant(1, -0.05)
        hydraulics.run(leaves)
        transpiration = 100.0 / 44000.0
        assert hydraulics.getRootWaterPotentialOfPlant(1) == pytest.approx(
            -0.05 - transpiration / (0.5 * (305.0 / 298.15) ** 7), rel=1e-5)

    def test_constant_leaf_capacitance_uses_default_curve(self, context, hydraulics):
        leaves = add_plant(context, plant_id=1, latent_flux=4000.0)
        hydraulics.setSoilWaterPotentialOfPlant(1, -0.05)

        def turgor_with(coeffs):
            hydraulics.setModelCoefficients(coeffs)
            hydraulics.run(leaves)
            return context.getPrimitiveData(leaves[0], "turgor_pressure", float)

        constant = PlantHydraulicsModelCoefficients()
        constant.setLeafHydraulicCapacitance(0.3)
        assert turgor_with(constant) == pytest.approx(turgor_with(PlantHydraulicsModelCoefficients()), rel=1e-6)

    def test_transient_run_requires_constant_stem_and_root_capacitance(self, context, hydraulics):
        leaves = add_plant(context, plant_id=1)
        hydraulics.setModelCoefficients(PlantHydraulicsModelCoefficients())
        with pytest.raises(PlantHydraulicsModelError, match="fixed_constant_capacitance"):
            hydraulics.run(leaves, timespan=100, timestep=10)

    def test_get_coefficients_without_per_primitive_entry_raises(self, context, hydraulics):
        """Reading a leaf that uses the model-wide coefficients must not give it default ones."""
        leaves = add_plant(context, plant_id=1, latent_flux=4000.0)
        hydraulics.setSoilWaterPotentialOfPlant(1, -0.05)
        hydraulics.setModelCoefficients(pistachio_coefficients())
        hydraulics.run(leaves)
        before = context.getPrimitiveData(leaves[0], "turgor_pressure", float)

        with pytest.raises(PlantHydraulicsModelError, match="no coefficients of its own"):
            hydraulics.getModelCoefficients(leaves[0])

        hydraulics.run(leaves)
        assert context.getPrimitiveData(leaves[0], "turgor_pressure", float) == pytest.approx(before, rel=1e-6)

    def test_model_wide_coefficients_clear_readable_entries(self, context, hydraulics):
        leaves = add_plant(context, plant_id=1)
        hydraulics.setModelCoefficientsFromLibrary("Walnut", leaves[0])
        hydraulics.getModelCoefficients(leaves[0])
        hydraulics.setModelCoefficients(PlantHydraulicsModelCoefficients())
        with pytest.raises(PlantHydraulicsModelError, match="no coefficients of its own"):
            hydraulics.getModelCoefficients(leaves[0])

    @pytest.mark.parametrize("value", [-1, 1.5, "0", None, True])
    def test_get_coefficients_rejects_bad_uuid(self, hydraulics, value):
        with pytest.raises(ValueError, match="UUID"):
            hydraulics.getModelCoefficients(value)

    @pytest.mark.parametrize("species", ["Almond", "", None])
    def test_get_coefficients_from_library_rejects_unknown_species(self, hydraulics, species):
        with pytest.raises(ValueError):
            hydraulics.getModelCoefficientsFromLibrary(species)

    def test_invalid_plant_id_arguments(self, hydraulics):
        with pytest.raises(ValueError, match="plantID must be >= 0"):
            hydraulics.setSoilWaterPotentialOfPlant(-1, -0.05)
        with pytest.raises(ValueError, match="soil_water_potential must be finite"):
            hydraulics.setSoilWaterPotentialOfPlant(1, float('nan'))
        with pytest.raises(ValueError, match="plantID must be an integer"):
            hydraulics.getStemWaterPotentialOfPlant(1.5)
        with pytest.raises(ValueError, match="plantID must be an integer"):
            hydraulics.getPrimitivesByPlantID("1")

    def test_use_after_exit_raises(self, context):
        model = PlantHydraulicsModel(context)
        model.__exit__(None, None, None)
        with pytest.raises(PlantHydraulicsModelError):
            model.run()


@pytest.mark.native_only
class TestPlantHydraulicsIntegration:
    """Test integration with other PyHelios plugins"""

    def test_plant_architecture_workflow(self, context, hydraulics):
        if not get_plugin_registry().is_plugin_available('plantarchitecture'):
            pytest.skip("plantarchitecture plugin not available")
        from pyhelios import PlantArchitecture

        with PlantArchitecture(context) as plantarchitecture:
            plantarchitecture.disableMessages()
            plantarchitecture.loadPlantModelFromLibrary("bean")
            plantarchitecture.optionalOutputObjectData("plantID")
            plantarchitecture.buildPlantInstanceFromLibrary(base_position=vec3(0, 0, 0), age=20)
            leaves = plantarchitecture.getAllLeafUUIDs()
            assert leaves

            context.setPrimitiveDataFloat(leaves, "latent_flux", 100.0)
            assert hydraulics.getPrimitivesWithoutPlantID(leaves) == []
            plant_id = hydraulics.getPlantID(leaves)

            hydraulics.setModelCoefficients(pistachio_coefficients())
            hydraulics.setSoilWaterPotentialOfPlant(plant_id, -0.05)
            hydraulics.run(leaves)

            assert hydraulics.getStemWaterPotential(leaves) == pytest.approx(EXPECTED_STEM_POTENTIAL, rel=1e-4)
            transpiration = 100.0 / 44000.0
            assert context.getPrimitiveData(leaves[0], "water_potential", float) == pytest.approx(
                EXPECTED_STEM_POTENTIAL - transpiration / 0.5, rel=1e-4)
