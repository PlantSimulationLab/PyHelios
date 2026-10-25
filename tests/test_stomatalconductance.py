"""
Tests for StomatalConductance integration
"""

import pytest
from pyhelios import Context
from pyhelios.plugins.registry import get_plugin_registry
# Import HeliosError from pyhelios main module to ensure consistency
from pyhelios import HeliosError
from pyhelios.types import vec3

class TestStomatalConductanceMetadata:
    """Test plugin metadata and registration"""
    
    @pytest.mark.cross_platform
    def test_plugin_metadata_exists(self):
        """Test that plugin metadata is correctly defined"""
        from pyhelios.config.plugin_metadata import get_plugin_metadata
        
        metadata = get_plugin_metadata('stomatalconductance')
        assert metadata is not None
        assert metadata.name == 'stomatalconductance'
        assert metadata.description
        assert metadata.test_symbols
        assert isinstance(metadata.platforms, list)
        assert len(metadata.platforms) > 0
        assert 'windows' in metadata.platforms
        assert 'linux' in metadata.platforms  
        assert 'macos' in metadata.platforms

    @pytest.mark.cross_platform
    def test_plugin_available(self):
        """Test that plugin is available when expected"""
        from pyhelios.config.plugin_metadata import PLUGIN_METADATA
        
        # Should be in plugin metadata
        assert 'stomatalconductance' in PLUGIN_METADATA
        
        # Should not require GPU
        metadata = PLUGIN_METADATA['stomatalconductance']
        assert not metadata.gpu_required
        
        # Should have no system dependencies
        assert metadata.system_dependencies == []

class TestStomatalConductanceAvailability:
    """Test plugin availability detection"""
    
    @pytest.mark.cross_platform
    def test_plugin_registry_awareness(self):
        """Test that plugin registry knows about StomatalConductance"""
        registry = get_plugin_registry()
        
        # Plugin should be known (even if not available)
        all_plugins = registry.get_available_plugins()
        # Note: stomatalconductance will be in all_plugins only if actually built and available
    
    @pytest.mark.cross_platform 
    def test_graceful_unavailable_handling(self):
        """Test graceful handling when plugin unavailable"""
        registry = get_plugin_registry()
        
        with Context() as context:
            if not registry.is_plugin_available('stomatalconductance'):
                # Should raise informative error
                try:
                    from pyhelios import StomatalConductanceModel
                    if StomatalConductanceModel is not None:
                        with pytest.raises(Exception) as exc_info:
                            StomatalConductanceModel(context)
                        
                        error_msg = str(exc_info.value).lower()
                        # Error should mention rebuilding or plugin unavailability
                        expected_keywords = ['rebuild', 'build', 'enable', 'compile', 'plugin', 'not available', 'unavailable']
                        found_keywords = [k for k in expected_keywords if k in error_msg]
                        assert len(found_keywords) > 0, f"Error message missing expected keywords. Got: '{str(exc_info.value)}'"
                except ImportError:
                    # StomatalConductanceModel not imported when plugin unavailable
                    pass
            else:
                # Plugin is available - nothing to test for graceful unavailable handling
                pass

class TestStomatalConductanceInterface:
    """Test plugin interface without requiring native library"""
    
    @pytest.mark.cross_platform
    def test_plugin_class_structure(self):
        """Test that plugin class has expected structure"""
        try:
            from pyhelios import (
                StomatalConductanceModel, 
                StomatalConductanceModelError,
                BWBCoefficients,
                BBLCoefficients, 
                MOPTCoefficients,
                BMFCoefficients,
                BBCoefficients
            )
            
            if StomatalConductanceModel is not None:
                # Test class attributes and methods exist
                assert hasattr(StomatalConductanceModel, '__init__')
                assert hasattr(StomatalConductanceModel, '__enter__')
                assert hasattr(StomatalConductanceModel, '__exit__')
                assert hasattr(StomatalConductanceModel, 'run')
                assert hasattr(StomatalConductanceModel, 'setBWBCoefficients')
                assert hasattr(StomatalConductanceModel, 'setBBLCoefficients')
                assert hasattr(StomatalConductanceModel, 'setMOPTCoefficients')
                assert hasattr(StomatalConductanceModel, 'setBMFCoefficients')
                assert hasattr(StomatalConductanceModel, 'setBBCoefficients')
                assert hasattr(StomatalConductanceModel, 'setBMFCoefficientsFromLibrary')
                assert hasattr(StomatalConductanceModel, 'setDynamicTimeConstants')
                assert hasattr(StomatalConductanceModel, 'optionalOutputPrimitiveData')
                assert hasattr(StomatalConductanceModel, 'printDefaultValueReport')
                assert hasattr(StomatalConductanceModel, 'is_available')
            
        except ImportError:
            # StomatalConductanceModel not available - this is acceptable
            pass
    
    @pytest.mark.cross_platform
    def test_coefficient_classes_structure(self):
        """Test that coefficient classes are properly defined"""
        try:
            from pyhelios import (
                BWBCoefficients,
                BBLCoefficients, 
                MOPTCoefficients,
                BMFCoefficients,
                BBCoefficients
            )
            
            if BWBCoefficients is not None:
                # Test BWB coefficients
                bwb = BWBCoefficients(gs0=0.1, a1=1.0)
                assert hasattr(bwb, 'gs0')
                assert hasattr(bwb, 'a1')
                assert bwb.gs0 == 0.1
                assert bwb.a1 == 1.0
                
                # Test BBL coefficients
                bbl = BBLCoefficients(gs0=0.1, a1=1.0, D0=1000.0)
                assert hasattr(bbl, 'gs0')
                assert hasattr(bbl, 'a1')
                assert hasattr(bbl, 'D0')
                
                # Test MOPT coefficients
                mopt = MOPTCoefficients(gs0=0.1, g1=2.0)
                assert hasattr(mopt, 'gs0')
                assert hasattr(mopt, 'g1')
                
                # Test BMF coefficients
                bmf = BMFCoefficients(Em=250.0, i0=40.0, k=200000.0, b=600.0)
                assert hasattr(bmf, 'Em')
                assert hasattr(bmf, 'i0')
                assert hasattr(bmf, 'k')
                assert hasattr(bmf, 'b')
                
                # Test BB coefficients
                bb = BBCoefficients(pi_0=1.0, pi_m=1.5, theta=200.0, sigma=0.5, chi=2.0)
                assert hasattr(bb, 'pi_0')
                assert hasattr(bb, 'pi_m')
                assert hasattr(bb, 'theta')
                assert hasattr(bb, 'sigma')
                assert hasattr(bb, 'chi')
                
        except ImportError:
            # Coefficient classes not available - this is acceptable
            pass
    
    @pytest.mark.cross_platform
    def test_error_types_available(self):
        """Test that error types are properly defined"""
        try:
            from pyhelios import StomatalConductanceModelError
            if StomatalConductanceModelError is not None:
                # Check that it's actually a class, not None or other
                assert isinstance(StomatalConductanceModelError, type), \
                    f"StomatalConductanceModelError should be a class, got: {type(StomatalConductanceModelError)}"
                
                # Import HeliosError in the same scope to ensure consistent class identity
                from pyhelios import HeliosError
                assert issubclass(StomatalConductanceModelError, HeliosError), \
                    f"StomatalConductanceModelError should inherit from HeliosError. "\
                    f"StomatalConductanceModelError: {StomatalConductanceModelError} (module: {StomatalConductanceModelError.__module__}), "\
                    f"HeliosError: {HeliosError} (module: {HeliosError.__module__}), "\
                    f"MRO: {StomatalConductanceModelError.__mro__}"
            else:
                # None is acceptable when plugin not available
                pass
        except ImportError:
            # Error types not available - this is acceptable
            pass

@pytest.mark.native_only
class TestStomatalConductanceFunctionality:
    """Test actual plugin functionality with native library"""
    
    def test_plugin_creation(self):
        """Test plugin can be created and destroyed"""
        from pyhelios import StomatalConductanceModel
        
        with Context() as context:
            with StomatalConductanceModel(context) as stomatal:
                assert stomatal is not None
                assert isinstance(stomatal, StomatalConductanceModel)
    
    def test_message_control(self):
        """Test message enable/disable functionality"""
        from pyhelios import StomatalConductanceModel
        
        with Context() as context:
            with StomatalConductanceModel(context) as stomatal:
                # Should not raise exceptions
                stomatal.enableMessages()
                stomatal.disableMessages()
    
    def test_basic_run_methods(self):
        """Test basic run functionality"""
        from pyhelios import StomatalConductanceModel
        
        with Context() as context:
            # Add some geometry for testing
            patch_uuid = context.addPatch(center=[0, 0, 1], size=[0.1, 0.1])
            
            with StomatalConductanceModel(context) as stomatal:
                # Test steady state for all primitives
                stomatal.run()
                
                # Test steady state for specific primitives
                stomatal.run(uuids=[patch_uuid])
                
                # Test dynamic with timestep for all primitives
                stomatal.run(dt=60.0)
                
                # Test dynamic with timestep for specific primitives
                stomatal.run(uuids=[patch_uuid], dt=30.0)

    def test_bwb_coefficients(self):
        """Test Ball-Woodrow-Berry model coefficients"""
        from pyhelios import StomatalConductanceModel, BWBCoefficients
        
        with Context() as context:
            patch_uuid = context.addPatch(center=[0, 0, 1], size=[0.1, 0.1])
            
            with StomatalConductanceModel(context) as stomatal:
                # Test BWB coefficients for all primitives
                bwb_coeffs = BWBCoefficients(gs0=0.0733, a1=9.422)
                stomatal.setBWBCoefficients(bwb_coeffs)
                
                # Test BWB coefficients for specific primitives
                stomatal.setBWBCoefficients(bwb_coeffs, uuids=[patch_uuid])
                
                # Run model to ensure coefficients are applied
                stomatal.run()
    
    def test_bbl_coefficients(self):
        """Test Ball-Berry-Leuning model coefficients"""
        from pyhelios import StomatalConductanceModel, BBLCoefficients
        
        with Context() as context:
            patch_uuid = context.addPatch(center=[0, 0, 1], size=[0.1, 0.1])
            
            with StomatalConductanceModel(context) as stomatal:
                # Test BBL coefficients
                bbl_coeffs = BBLCoefficients(gs0=0.0743, a1=4.265, D0=14570.0)
                stomatal.setBBLCoefficients(bbl_coeffs)
                stomatal.setBBLCoefficients(bbl_coeffs, uuids=[patch_uuid])
                stomatal.run()
    
    def test_mopt_coefficients(self):
        """Test Medlyn et al. optimality model coefficients"""
        from pyhelios import StomatalConductanceModel, MOPTCoefficients
        
        with Context() as context:
            patch_uuid = context.addPatch(center=[0, 0, 1], size=[0.1, 0.1])
            
            with StomatalConductanceModel(context) as stomatal:
                # Test MOPT coefficients
                mopt_coeffs = MOPTCoefficients(gs0=0.0825, g1=2.637)
                stomatal.setMOPTCoefficients(mopt_coeffs)
                stomatal.setMOPTCoefficients(mopt_coeffs, uuids=[patch_uuid])
                stomatal.run()
    
    def test_bmf_coefficients(self):
        """Test Buckley-Mott-Farquhar model coefficients"""
        from pyhelios import StomatalConductanceModel, BMFCoefficients
        
        with Context() as context:
            patch_uuid = context.addPatch(center=[0, 0, 1], size=[0.1, 0.1])
            
            with StomatalConductanceModel(context) as stomatal:
                # Test BMF coefficients
                bmf_coeffs = BMFCoefficients(Em=258.25, i0=38.65, k=232916.82, b=609.67)
                stomatal.setBMFCoefficients(bmf_coeffs)
                stomatal.setBMFCoefficients(bmf_coeffs, uuids=[patch_uuid])
                stomatal.run()
    
    def test_bb_coefficients(self):
        """Test Bailey model coefficients"""
        from pyhelios import StomatalConductanceModel, BBCoefficients
        
        with Context() as context:
            patch_uuid = context.addPatch(center=[0, 0, 1], size=[0.1, 0.1])
            
            with StomatalConductanceModel(context) as stomatal:
                # Test BB coefficients
                bb_coeffs = BBCoefficients(pi_0=1.0, pi_m=1.67, theta=211.22, sigma=0.4408, chi=2.076)
                stomatal.setBBCoefficients(bb_coeffs)
                stomatal.setBBCoefficients(bb_coeffs, uuids=[patch_uuid])
                stomatal.run()
    
    def test_species_library(self):
        """Test species library functionality"""
        from pyhelios import StomatalConductanceModel
        
        with Context() as context:
            patch_uuid = context.addPatch(center=[0, 0, 1], size=[0.1, 0.1])
            
            with StomatalConductanceModel(context) as stomatal:
                # Test common species
                common_species = ["Almond", "Apple", "Grape", "Walnut"]
                
                for species in common_species:
                    try:
                        # Set coefficients for all primitives
                        stomatal.setBMFCoefficientsFromLibrary(species)
                        
                        # Set coefficients for specific primitives
                        stomatal.setBMFCoefficientsFromLibrary(species, uuids=[patch_uuid])
                        
                        # Run model to ensure coefficients work
                        stomatal.run()
                    except Exception as e:
                        # Some species may not be available - this is acceptable
                        if "species not found" not in str(e).lower():
                            raise
    
    def test_dynamic_time_constants(self):
        """Test dynamic time constants"""
        from pyhelios import StomatalConductanceModel
        
        with Context() as context:
            patch_uuid = context.addPatch(center=[0, 0, 1], size=[0.1, 0.1])
            
            with StomatalConductanceModel(context) as stomatal:
                # Set time constants for all primitives
                stomatal.setDynamicTimeConstants(tau_open=120.0, tau_close=240.0)
                
                # Set time constants for specific primitives
                stomatal.setDynamicTimeConstants(tau_open=60.0, tau_close=180.0, uuids=[patch_uuid])
                
                # Run dynamic simulation
                stomatal.run(dt=30.0)
    
    def test_optional_output(self):
        """Test optional output functionality"""
        from pyhelios import StomatalConductanceModel
        
        with Context() as context:
            patch_uuid = context.addPatch(center=[0, 0, 1], size=[0.1, 0.1])
            
            with StomatalConductanceModel(context) as stomatal:
                # Add optional outputs
                common_outputs = ["gs", "Ci", "E"]
                
                for output in common_outputs:
                    stomatal.optionalOutputPrimitiveData(output)
                
                # Run model to generate output
                stomatal.run()
    
    def test_default_value_report(self):
        """Test default value reporting"""
        from pyhelios import StomatalConductanceModel
        
        with Context() as context:
            patch_uuid = context.addPatch(center=[0, 0, 1], size=[0.1, 0.1])
            
            with StomatalConductanceModel(context) as stomatal:
                # Print report for all primitives
                stomatal.printDefaultValueReport()
                
                # Print report for specific primitives
                stomatal.printDefaultValueReport(uuids=[patch_uuid])

    def test_parameter_validation(self):
        """Test parameter validation"""
        from pyhelios import StomatalConductanceModel, BWBCoefficients, StomatalConductanceModelError
        
        with Context() as context:
            patch_uuid = context.addPatch(center=[0, 0, 1], size=[0.1, 0.1])
            
            with StomatalConductanceModel(context) as stomatal:
                # Test invalid time step
                with pytest.raises(StomatalConductanceModelError, match="positive"):
                    stomatal.run(dt=-1.0)
                
                # Test empty UUIDs list
                with pytest.raises(StomatalConductanceModelError, match="empty"):
                    stomatal.run(uuids=[])
                
                # Test invalid BWB coefficients
                with pytest.raises(ValueError):
                    bad_coeffs = BWBCoefficients(gs0=-0.1, a1=1.0)  # negative gs0
                    stomatal.setBWBCoefficients(bad_coeffs)
                
                # Test invalid time constants
                with pytest.raises(ValueError, match="positive"):
                    stomatal.setDynamicTimeConstants(tau_open=-1.0, tau_close=100.0)
                
                # Test empty species name
                with pytest.raises(ValueError, match="empty"):
                    stomatal.setBMFCoefficientsFromLibrary("")
                
                # Test empty output label
                with pytest.raises(ValueError, match="empty"):
                    stomatal.optionalOutputPrimitiveData("")

@pytest.mark.native_only
class TestStomatalConductanceIntegration:
    """Test plugin integration with other PyHelios components"""
    
    def test_context_integration(self):
        """Test plugin works with Context geometry"""
        from pyhelios import StomatalConductanceModel, BMFCoefficients
        
        with Context() as context:
            # Add different types of geometry
            patch_uuid = context.addPatch(center=[0, 0, 1], size=[0.1, 0.1])
            triangle_uuid = context.addTriangle(vec3(0, 0, 0), vec3(0.1, 0, 0), vec3(0, 0.1, 0))
            
            with StomatalConductanceModel(context) as stomatal:
                # Set coefficients using species library
                stomatal.setBMFCoefficientsFromLibrary("Almond")
                
                # Test plugin can work with context geometry
                stomatal.run()
                
                # Test with specific geometry
                stomatal.run(uuids=[patch_uuid, triangle_uuid])
    
    def test_error_handling_integration(self):
        """Test that C++ exceptions become proper Python exceptions"""
        from pyhelios import StomatalConductanceModel, StomatalConductanceModelError
        
        with Context() as context:
            with StomatalConductanceModel(context) as stomatal:
                with pytest.raises(StomatalConductanceModelError, match="NonexistentSpecies"):
                    stomatal.setBMFCoefficientsFromLibrary("NonexistentSpecies")
    
    def test_multiple_models(self):
        """Test using multiple model types in sequence"""
        from pyhelios import (
            StomatalConductanceModel, 
            BWBCoefficients, 
            BBLCoefficients, 
            MOPTCoefficients,
            BMFCoefficients
        )
        
        with Context() as context:
            patch_uuid = context.addPatch(center=[0, 0, 1], size=[0.1, 0.1])
            
            with StomatalConductanceModel(context) as stomatal:
                # Test using different models in sequence
                
                # Start with BWB model
                bwb_coeffs = BWBCoefficients(gs0=0.05, a1=8.0)
                stomatal.setBWBCoefficients(bwb_coeffs, uuids=[patch_uuid])
                stomatal.run()
                
                # Switch to BBL model
                bbl_coeffs = BBLCoefficients(gs0=0.06, a1=5.0, D0=15000.0)
                stomatal.setBBLCoefficients(bbl_coeffs, uuids=[patch_uuid])
                stomatal.run()
                
                # Switch to MOPT model  
                mopt_coeffs = MOPTCoefficients(gs0=0.07, g1=3.0)
                stomatal.setMOPTCoefficients(mopt_coeffs, uuids=[patch_uuid])
                stomatal.run()
                
                # Switch to BMF model
                bmf_coeffs = BMFCoefficients(Em=250.0, i0=40.0, k=200000.0, b=600.0)
                stomatal.setBMFCoefficients(bmf_coeffs, uuids=[patch_uuid])
                stomatal.run()

def _bare_stomatal_model():
    """A StomatalConductanceModel that skips __init__, for exercising pure-Python validation
    that runs before any native call (works in mock mode)."""
    from pyhelios.StomatalConductance import StomatalConductanceModel
    model = object.__new__(StomatalConductanceModel)
    model.context = None
    model.stomatal_model = None
    return model


@pytest.mark.cross_platform
class TestStomatalCoefficientTargetValidation:
    """Validation of material_label / per-UUID coefficient assignment (no native library needed)"""

    def _all_setters(self):
        from pyhelios.StomatalConductance import (BWBCoefficients, BBLCoefficients, MOPTCoefficients,
                                                  BMFCoefficients, BBCoefficients)
        return [
            ("setBWBCoefficients", BWBCoefficients(gs0=0.07, a1=9.0)),
            ("setBBLCoefficients", BBLCoefficients(gs0=0.07, a1=4.0, D0=14570.0)),
            ("setMOPTCoefficients", MOPTCoefficients(gs0=0.08, g1=2.6)),
            ("setBMFCoefficients", BMFCoefficients(Em=258.25, i0=38.65, k=232916.82, b=609.67)),
            ("setBBCoefficients", BBCoefficients(pi_0=1.0, pi_m=1.67, theta=211.22, sigma=0.44, chi=2.08)),
        ]

    def test_uuids_and_material_label_mutually_exclusive(self):
        model = _bare_stomatal_model()
        for name, coeffs in self._all_setters():
            with pytest.raises(ValueError, match="not both"):
                getattr(model, name)(coeffs, uuids=[0], material_label="leaf")
            with pytest.raises(ValueError, match="not both"):
                getattr(model, name)(coeffs, [0], "leaf")
        with pytest.raises(ValueError, match="not both"):
            model.setBMFCoefficientsFromLibrary("Almond", uuids=[0], material_label="leaf")
        with pytest.raises(ValueError, match="not both"):
            model.setBMFCoefficientsFromLibrary("Almond", [0], "leaf")

    def test_wrong_coefficient_type_positional_and_keyword(self):
        from pyhelios.StomatalConductance import BWBCoefficients, BBLCoefficients
        model = _bare_stomatal_model()
        wrong = BBLCoefficients(gs0=0.07, a1=4.0, D0=14570.0)
        for name, _ in self._all_setters():
            if name == "setBBLCoefficients":
                bad = BWBCoefficients(gs0=0.07, a1=9.0)
            else:
                bad = wrong
            with pytest.raises(ValueError, match="Coefficients"):
                getattr(model, name)(bad, None, "leaf")
            with pytest.raises(ValueError, match="Coefficients"):
                getattr(model, name)(coeffs=bad, material_label="leaf")

    def test_wrong_material_label_type(self):
        model = _bare_stomatal_model()
        for name, coeffs in self._all_setters():
            with pytest.raises(ValueError, match="material_label"):
                getattr(model, name)(coeffs, None, 42)
            with pytest.raises(ValueError, match="material_label"):
                getattr(model, name)(coeffs, material_label="")
        with pytest.raises(ValueError, match="material_label"):
            model.setBMFCoefficientsFromLibrary("Almond", material_label=3)

    def test_string_passed_as_uuids_is_rejected_with_hint(self):
        model = _bare_stomatal_model()
        for name, coeffs in self._all_setters():
            with pytest.raises(ValueError, match="material_label="):
                getattr(model, name)(coeffs, "leaf")
            with pytest.raises(ValueError, match="uuids"):
                getattr(model, name)(coeffs, uuids=[1.5])

    def test_bmf_list_form_validation(self):
        from pyhelios.StomatalConductance import BMFCoefficients, BWBCoefficients
        model = _bare_stomatal_model()
        c = BMFCoefficients(Em=258.25, i0=38.65, k=232916.82, b=609.67)
        with pytest.raises(ValueError, match="requires uuids"):
            model.setBMFCoefficients([c, c])
        with pytest.raises(ValueError, match="does not match"):
            model.setBMFCoefficients([c, c], [1, 2, 3])
        with pytest.raises(ValueError, match="does not match"):
            model.setBMFCoefficients(coeffs=[c], uuids=[1, 2])
        with pytest.raises(ValueError, match="material_label"):
            model.setBMFCoefficients([c], material_label="leaf")
        with pytest.raises(ValueError, match="BMFCoefficients"):
            model.setBMFCoefficients([c, BWBCoefficients(gs0=0.1, a1=1.0)], [1, 2])
        with pytest.raises(ValueError, match="BMFCoefficients"):
            model.setBMFCoefficients([], [])
        with pytest.raises(ValueError, match="Em"):
            model.setBMFCoefficients([c, c._replace(Em=-1.0)], [1, 2])

    def test_bmf_zero_b_accepted_by_validation(self):
        """Library species such as Elderberry have b == 0, so b must not be rejected."""
        from pyhelios.StomatalConductance import StomatalConductanceModel, BMFCoefficients
        StomatalConductanceModel._validate_bmf(BMFCoefficients(Em=41.28, i0=305.3, k=102490.0, b=0.0))
        with pytest.raises(ValueError, match="b must be non-negative"):
            StomatalConductanceModel._validate_bmf(BMFCoefficients(Em=41.28, i0=305.3, k=102490.0, b=-1.0))

    def test_library_getter_species_validation(self):
        model = _bare_stomatal_model()
        with pytest.raises(ValueError, match="Species"):
            model.getBMFCoefficientsFromLibrary("")
        with pytest.raises(ValueError, match="Species"):
            model.getBMFCoefficientsFromLibrary(5)

    def test_wrapper_functions_mock_or_unavailable(self):
        """Without a model pointer the new wrapper functions fail loudly, never silently."""
        from pyhelios.wrappers import UStomatalConductanceWrapper as w
        calls = [
            lambda: w.setBWBCoefficientsForMaterial(None, "leaf", 0.1, 1.0),
            lambda: w.setBBLCoefficientsForMaterial(None, "leaf", 0.1, 1.0, 1.0),
            lambda: w.setMOPTCoefficientsForMaterial(None, "leaf", 0.1, 1.0),
            lambda: w.setBMFCoefficientsForMaterial(None, "leaf", 1.0, 1.0, 1.0, 1.0),
            lambda: w.setBBCoefficientsForMaterial(None, "leaf", 1.0, 1.0, 1.0, 1.0, 1.0),
            lambda: w.setBMFCoefficientsFromLibraryForMaterial(None, "Almond", "leaf"),
            lambda: w.setBMFCoefficientsPerUUID(None, [[1.0, 1.0, 1.0, 1.0]], [0]),
            lambda: w.getBMFCoefficientsFromLibrary(None, "Almond"),
        ]
        for call in calls:
            with pytest.raises((ValueError, NotImplementedError)):
                call()


def _bmf_gs(context, uuid):
    return context.getPrimitiveData(uuid, "moisture_conductance")


@pytest.mark.native_only
class TestStomatalMaterialAndPerUUIDCoefficients:
    """Material-label and per-UUID coefficient assignment against the native library"""

    def _leaves(self, context, n):
        uuids = [context.addPatch(center=vec3(i, 0, 1), size=[0.1, 0.1]) for i in range(n)]
        context.setPrimitiveDataFloat(uuids, "radiation_flux_PAR", 300.0)
        context.setPrimitiveDataFloat(uuids, "air_humidity", 0.4)
        return uuids

    def test_material_label_coefficients_change_gs_by_material(self):
        from pyhelios import StomatalConductanceModel, BMFCoefficients
        with Context() as context:
            a, b = self._leaves(context, 2)
            context.addMaterial("leaf_a")
            context.addMaterial("leaf_b")
            context.assignMaterialToPrimitive(a, "leaf_a")
            context.assignMaterialToPrimitive(b, "leaf_b")
            with StomatalConductanceModel(context) as stomatal:
                stomatal.setBMFCoefficientsFromLibrary("Almond")
                stomatal.run()
                baseline_a, baseline_b = _bmf_gs(context, a), _bmf_gs(context, b)
                assert baseline_a == pytest.approx(baseline_b)

                low = stomatal.getBMFCoefficientsFromLibrary("Almond")
                stomatal.setBMFCoefficients(low._replace(Em=low.Em * 0.25), material_label="leaf_a")
                stomatal.run()
                gs_a, gs_b = _bmf_gs(context, a), _bmf_gs(context, b)
                assert gs_b == pytest.approx(baseline_b)
                assert gs_a == pytest.approx(0.25 * baseline_a, rel=0.05)

    def test_material_label_takes_precedence_over_uuid(self):
        from pyhelios import StomatalConductanceModel, BMFCoefficients
        with Context() as context:
            (a,) = self._leaves(context, 1)
            context.addMaterial("leaf_a")
            context.assignMaterialToPrimitive(a, "leaf_a")
            with StomatalConductanceModel(context) as stomatal:
                stomatal.setBMFCoefficientsFromLibrary("Walnut", material_label="leaf_a")
                stomatal.run()
                gs_material = _bmf_gs(context, a)
                stomatal.setBMFCoefficientsFromLibrary("Almond", uuids=[a])
                stomatal.run()
                assert _bmf_gs(context, a) == pytest.approx(gs_material)

    def test_material_label_for_every_model_type_runs(self):
        from pyhelios import (StomatalConductanceModel, BWBCoefficients, BBLCoefficients,
                              MOPTCoefficients, BBCoefficients)
        with Context() as context:
            (a,) = self._leaves(context, 1)
            context.addMaterial("leaf_a")
            context.assignMaterialToPrimitive(a, "leaf_a")
            with StomatalConductanceModel(context) as stomatal:
                stomatal.setBWBCoefficients(BWBCoefficients(gs0=0.0733, a1=9.422), material_label="leaf_a")
                stomatal.run()
                stomatal.setBBLCoefficients(BBLCoefficients(gs0=0.0743, a1=4.265, D0=14570.0), material_label="leaf_a")
                stomatal.run()
                stomatal.setMOPTCoefficients(MOPTCoefficients(gs0=0.0825, g1=2.637), material_label="leaf_a")
                stomatal.run()
                stomatal.setBBCoefficients(BBCoefficients(pi_0=1.0, pi_m=1.67, theta=211.22, sigma=0.4408, chi=2.076),
                                           material_label="leaf_a")
                stomatal.run()
                assert _bmf_gs(context, a) > 0.0

    def test_unknown_material_label_raises(self):
        from pyhelios import StomatalConductanceModel, StomatalConductanceModelError, BWBCoefficients
        with Context() as context:
            self._leaves(context, 1)
            with StomatalConductanceModel(context) as stomatal:
                with pytest.raises(StomatalConductanceModelError, match="no_such_material"):
                    stomatal.setBWBCoefficients(BWBCoefficients(gs0=0.07, a1=9.0), material_label="no_such_material")
                with pytest.raises(StomatalConductanceModelError, match="no_such_material"):
                    stomatal.setBMFCoefficientsFromLibrary("Almond", material_label="no_such_material")

    def test_per_uuid_coefficient_list_gives_per_primitive_gs(self):
        from pyhelios import StomatalConductanceModel
        with Context() as context:
            uuids = self._leaves(context, 3)
            with StomatalConductanceModel(context) as stomatal:
                species = ["Almond", "Walnut", "Grape"]
                sets = [stomatal.getBMFCoefficientsFromLibrary(sp) for sp in species]
                stomatal.setBMFCoefficients(sets, uuids=uuids)
                stomatal.run()
                gs_list = [_bmf_gs(context, u) for u in uuids]

                for u, sp, gs in zip(uuids, species, gs_list):
                    stomatal.setBMFCoefficientsFromLibrary(sp, uuids=[u])
                stomatal.run()
                expected = [_bmf_gs(context, u) for u in uuids]
                assert gs_list == pytest.approx(expected)
                assert len({round(g, 6) for g in gs_list}) == 3

    def test_per_uuid_length_mismatch_rejected(self):
        from pyhelios import StomatalConductanceModel
        with Context() as context:
            uuids = self._leaves(context, 2)
            with StomatalConductanceModel(context) as stomatal:
                c = stomatal.getBMFCoefficientsFromLibrary("Almond")
                with pytest.raises(ValueError, match="does not match"):
                    stomatal.setBMFCoefficients([c], uuids=uuids)

    def test_library_getter_round_trips_through_uuid_setter(self):
        from pyhelios import StomatalConductanceModel, BMFCoefficients
        with Context() as context:
            (a,) = self._leaves(context, 1)
            with StomatalConductanceModel(context) as stomatal:
                coeffs = stomatal.getBMFCoefficientsFromLibrary("Almond")
                assert isinstance(coeffs, BMFCoefficients)
                assert coeffs.Em == pytest.approx(865.52, rel=1e-5)
                assert coeffs.i0 == pytest.approx(38.65, rel=1e-5)
                assert coeffs.k == pytest.approx(780320.1, rel=1e-5)
                assert coeffs.b == pytest.approx(2086.07, rel=1e-5)

                stomatal.setBMFCoefficientsFromLibrary("Almond")
                stomatal.run()
                gs_library = _bmf_gs(context, a)

                stomatal.setBMFCoefficientsFromLibrary("Walnut")
                stomatal.run()
                assert _bmf_gs(context, a) != pytest.approx(gs_library)

                stomatal.setBMFCoefficients(coeffs, uuids=[a])
                stomatal.run()
                assert _bmf_gs(context, a) == pytest.approx(gs_library)

    def test_library_getter_for_zero_b_species_is_settable(self):
        from pyhelios import StomatalConductanceModel
        with Context() as context:
            (a,) = self._leaves(context, 1)
            with StomatalConductanceModel(context) as stomatal:
                elder = stomatal.getBMFCoefficientsFromLibrary("Elderberry")
                assert elder.b == 0.0
                stomatal.setBMFCoefficients(elder, uuids=[a])
                stomatal.run()
                assert _bmf_gs(context, a) > 0.0

    @pytest.mark.parametrize("call", [
        lambda m, u: m.getBMFCoefficientsFromLibrary("Almnd"),
        lambda m, u: m.setBMFCoefficientsFromLibrary("Almnd"),
        lambda m, u: m.setBMFCoefficientsFromLibrary("Almnd", uuids=[u]),
        lambda m, u: m.setBMFCoefficientsFromLibrary("Almnd", material_label="leaf_mat"),
    ])
    def test_unknown_species_raises_and_lists_valid_names(self, call):
        """helios-core 1.3.93: an unknown species used to fall back silently to the Almond coefficients."""
        from pyhelios import StomatalConductanceModel, StomatalConductanceModelError
        with Context() as context:
            (a,) = self._leaves(context, 1)
            context.addMaterial("leaf_mat")
            with StomatalConductanceModel(context) as stomatal:
                with pytest.raises(StomatalConductanceModelError, match="Almnd.*Valid species are: Almond"):
                    call(stomatal, a)


@pytest.mark.slow
class TestStomatalConductancePerformance:
    """Performance tests for plugin operations"""
    
    @pytest.mark.native_only
    def test_computation_performance(self):
        """Test computation performance doesn't regress"""
        import time
        from pyhelios import StomatalConductanceModel
        
        with Context() as context:
            # Create multiple patches for performance testing
            patch_uuids = []
            for i in range(100):
                x = (i % 10) * 0.1
                y = (i // 10) * 0.1
                patch_uuid = context.addPatch(center=[x, y, 1], size=[0.05, 0.05])
                patch_uuids.append(patch_uuid)
            
            with StomatalConductanceModel(context) as stomatal:
                # Set coefficients using species library
                stomatal.setBMFCoefficientsFromLibrary("Almond")
                
                # Time computation
                start_time = time.time()
                stomatal.run()
                elapsed = time.time() - start_time
                
                # Should complete in reasonable time (adjust threshold as needed)
                assert elapsed < 5.0, f"Computation too slow: {elapsed:.3f}s"
    
    @pytest.mark.native_only
    def test_dynamic_performance(self):
        """Test dynamic simulation performance"""
        import time
        from pyhelios import StomatalConductanceModel
        
        with Context() as context:
            # Create some geometry
            patch_uuids = []
            for i in range(50):
                x = (i % 10) * 0.1
                y = (i // 10) * 0.1
                patch_uuid = context.addPatch(center=[x, y, 1], size=[0.05, 0.05])
                patch_uuids.append(patch_uuid)
            
            with StomatalConductanceModel(context) as stomatal:
                stomatal.setBMFCoefficientsFromLibrary("Apple")
                stomatal.setDynamicTimeConstants(tau_open=60.0, tau_close=120.0)
                
                # Time dynamic computation
                start_time = time.time()
                stomatal.run(dt=30.0)
                elapsed = time.time() - start_time
                
                # Should complete in reasonable time
                assert elapsed < 3.0, f"Dynamic computation too slow: {elapsed:.3f}s"