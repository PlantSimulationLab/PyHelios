"""
Tests for EnergyBalance functionality in PyHelios.

This module tests the EnergyBalanceModel class and energy balance simulation capabilities.
Tests are designed to work in both native and mock modes.
"""

import pytest
import sys
import os
from typing import List

# Add pyhelios to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pyhelios import Context, EnergyBalanceModel, EnergyBalanceModelError, RadiationModel
from pyhelios.types import vec3, vec2
from pyhelios.plugins.registry import get_plugin_registry


def setup_radiation_for_energy_balance(context, band="SW"):
    """Helper function to set up radiation data for energy balance tests"""
    try:
        with RadiationModel(context) as radiation:
            radiation.addRadiationBand(band)
            radiation.addCollimatedRadiationSource()
            radiation.runBand(band)
    except Exception as e:
        # If radiation model fails, skip the test as energy balance requires radiation data
        pytest.skip(f"Radiation model setup failed (required for energy balance): {e}")


class TestEnergyBalanceMetadata:
    """Test energy balance plugin metadata and registration"""
    
    @pytest.mark.cross_platform
    def test_plugin_metadata_exists(self):
        """Test that energy balance plugin metadata is correctly defined"""
        from pyhelios.config.plugin_metadata import get_plugin_metadata
        
        metadata = get_plugin_metadata('energybalance')
        assert metadata is not None
        assert metadata.name == 'energybalance'
        assert metadata.description
        assert metadata.test_symbols
        assert isinstance(metadata.platforms, list)
        assert len(metadata.platforms) > 0
        assert metadata.gpu_required == True  # Energy balance requires CUDA
        assert "cuda" in metadata.system_dependencies



class TestEnergyBalanceAvailability:
    """Test energy balance plugin availability detection"""
    
    @pytest.mark.cross_platform
    def test_plugin_registry_awareness(self):
        """Test that plugin registry knows about energy balance"""
        registry = get_plugin_registry()
        
        # Plugin should be known (registry should be able to check it)
        capabilities = registry.get_plugin_capabilities()
        assert 'energybalance' in capabilities or not registry.is_plugin_available('energybalance')
    
    @pytest.mark.cross_platform 
    def test_graceful_unavailable_handling(self):
        """Test graceful handling when plugin unavailable"""
        registry = get_plugin_registry()
        
        with Context() as context:
            if not registry.is_plugin_available('energybalance'):
                # Should raise informative error
                with pytest.raises(EnergyBalanceModelError) as exc_info:
                    EnergyBalanceModel(context)
                
                error_msg = str(exc_info.value).lower()
                # Error should mention rebuilding and CUDA requirements
                assert any(keyword in error_msg for keyword in 
                          ['rebuild', 'build', 'enable', 'compile'])
                assert any(keyword in error_msg for keyword in
                          ['cuda', 'gpu', 'nvidia'])


class TestEnergyBalanceInterface:
    """Test energy balance interface without requiring native library"""
    
    @pytest.mark.cross_platform
    def test_energy_balance_class_structure(self):
        """Test that energy balance class has expected structure"""
        # Test class attributes and methods exist
        assert hasattr(EnergyBalanceModel, '__init__')
        assert hasattr(EnergyBalanceModel, '__enter__')
        assert hasattr(EnergyBalanceModel, '__exit__')
        assert hasattr(EnergyBalanceModel, 'run')
        assert hasattr(EnergyBalanceModel, 'addRadiationBand')
        assert hasattr(EnergyBalanceModel, 'enableAirEnergyBalance')
        assert hasattr(EnergyBalanceModel, 'evaluateAirEnergyBalance')
        assert hasattr(EnergyBalanceModel, 'optionalOutputPrimitiveData')
        assert hasattr(EnergyBalanceModel, 'printDefaultValueReport')
        assert hasattr(EnergyBalanceModel, 'enableMessages')
        assert hasattr(EnergyBalanceModel, 'disableMessages')
        assert hasattr(EnergyBalanceModel, 'is_available')
    
    @pytest.mark.cross_platform
    def test_error_types_available(self):
        """Test that error types are properly defined"""
        from pyhelios.exceptions import HeliosError
        assert issubclass(EnergyBalanceModelError, HeliosError)

    @pytest.mark.cross_platform
    def test_invalid_context_type(self):
        """Test energy balance model creation with invalid context"""
        with pytest.raises(TypeError):
            EnergyBalanceModel("invalid_context")


@pytest.mark.native_only
class TestEnergyBalanceFunctionality:
    """Test actual energy balance functionality with native library"""
    
    def test_energy_balance_creation(self):
        """Test energy balance model creation and destruction"""
        with Context() as context:
            # Test creating EnergyBalanceModel
            with EnergyBalanceModel(context) as energy_balance:
                assert energy_balance is not None
                assert isinstance(energy_balance, EnergyBalanceModel)
                # Native pointer should be valid
                native_ptr = energy_balance.getNativePtr()
                assert native_ptr is not None
    
    def test_message_control(self):
        """Test message enable/disable functionality"""
        with Context() as context:
            with EnergyBalanceModel(context) as energy_balance:
                # These should not raise exceptions
                energy_balance.disableMessages()
                energy_balance.enableMessages()
    
    def test_radiation_band_management(self):
        """Test radiation band management"""
        with Context() as context:
            with EnergyBalanceModel(context) as energy_balance:
                # Add single radiation band
                energy_balance.addRadiationBand("SW")
                
                # Add multiple radiation bands
                energy_balance.addRadiationBand(["PAR", "NIR", "LW"])
    
    def test_radiation_band_validation(self):
        """Test radiation band parameter validation"""
        with Context() as context:
            with EnergyBalanceModel(context) as energy_balance:
                # Test invalid single band
                with pytest.raises(ValueError, match="non-empty string"):
                    energy_balance.addRadiationBand("")
                
                with pytest.raises(ValueError, match="Band must be a string or list of strings"):
                    energy_balance.addRadiationBand(None)
                
                # Test invalid multiple bands
                with pytest.raises(ValueError, match="cannot be empty"):
                    energy_balance.addRadiationBand([])
                
                with pytest.raises(ValueError, match="non-empty strings"):
                    energy_balance.addRadiationBand(["SW", ""])
    
    def test_basic_energy_balance_run(self):
        """Test basic energy balance execution"""
        with Context() as context:
            # Add some geometry to work with
            patch_uuid = context.addPatch(center=vec3(0, 0, 1), size=vec2(1, 1))
            
            # Set up radiation data required for energy balance
            setup_radiation_for_energy_balance(context, "SW")
            
            with EnergyBalanceModel(context) as energy_balance:
                # Add radiation band
                energy_balance.addRadiationBand("SW")
                
                # Run steady state
                energy_balance.run()
                
                # Run with specific UUIDs
                energy_balance.run(uuids=[patch_uuid])
    
    def test_dynamic_energy_balance_run(self):
        """Test dynamic energy balance execution with timesteps"""
        with Context() as context:
            # Add geometry
            patch_uuid = context.addPatch(center=vec3(0, 0, 1), size=vec2(1, 1))
            
            # Set up radiation data required for energy balance
            setup_radiation_for_energy_balance(context, "SW")
            
            with EnergyBalanceModel(context) as energy_balance:
                # Add radiation band
                energy_balance.addRadiationBand("SW")
                
                # Run dynamic simulation
                energy_balance.run(dt=60.0)  # 60 second timestep
                
                # Run dynamic for specific UUIDs
                energy_balance.run(uuids=[patch_uuid], dt=30.0)
    
    def test_run_parameter_validation(self):
        """Test parameter validation for run method"""
        with Context() as context:
            patch_uuid = context.addPatch(center=vec3(0, 0, 1), size=vec2(1, 1))
            
            with EnergyBalanceModel(context) as energy_balance:
                energy_balance.addRadiationBand("SW")
                
                # Test invalid timestep - should catch ValueError from wrapper
                with pytest.raises(EnergyBalanceModelError, match="positive"):
                    energy_balance.run(dt=-1.0)
                
                with pytest.raises(EnergyBalanceModelError, match="positive"):
                    energy_balance.run(dt=0.0)
                
                # Test invalid UUIDs
                with pytest.raises(EnergyBalanceModelError, match="empty"):
                    energy_balance.run(uuids=[])
    
    def test_air_energy_balance(self):
        """Test air energy balance functionality"""
        with Context() as context:
            # Add canopy geometry
            for i in range(5):
                for j in range(5):
                    context.addPatch(center=vec3(i, j, 2.0), size=vec2(0.8, 0.8))
            
            # Set up radiation data required for energy balance
            setup_radiation_for_energy_balance(context, "SW")
            
            with EnergyBalanceModel(context) as energy_balance:
                energy_balance.addRadiationBand("SW")
                
                # Test automatic canopy height detection
                energy_balance.enableAirEnergyBalance()
                
                # Test with manual parameters
                energy_balance.enableAirEnergyBalance(canopy_height_m=3.0, reference_height_m=10.0)
                
                # Test air energy balance evaluation
                energy_balance.evaluateAirEnergyBalance(dt_sec=60.0, time_advance_sec=3600.0)
    
    def test_air_energy_balance_validation(self):
        """Test air energy balance parameter validation"""
        with Context() as context:
            context.addPatch(center=vec3(0, 0, 1), size=vec2(1, 1))
            
            with EnergyBalanceModel(context) as energy_balance:
                # Test invalid canopy height
                with pytest.raises(ValueError, match="positive"):
                    energy_balance.enableAirEnergyBalance(canopy_height_m=-1.0, reference_height_m=10.0)
                
                # Test invalid reference height
                with pytest.raises(ValueError, match="positive"):
                    energy_balance.enableAirEnergyBalance(canopy_height_m=5.0, reference_height_m=-1.0)
                
                # Test partial parameters (should fail) - should catch EnergyBalanceModelError
                with pytest.raises(EnergyBalanceModelError, match="together"):
                    energy_balance.enableAirEnergyBalance(canopy_height_m=5.0)
                
                # Test evaluation parameter validation
                energy_balance.enableAirEnergyBalance()
                
                with pytest.raises(ValueError, match="positive"):
                    energy_balance.evaluateAirEnergyBalance(dt_sec=-1.0, time_advance_sec=100.0)
                
                with pytest.raises(ValueError, match="greater than or equal"):
                    energy_balance.evaluateAirEnergyBalance(dt_sec=100.0, time_advance_sec=50.0)
    
    def test_air_energy_balance_for_uuids(self):
        """Test air energy balance for specific primitives"""
        with Context() as context:
            patch_uuids = []
            for i in range(3):
                uuid = context.addPatch(center=vec3(i, 0, 2.0), size=vec2(0.8, 0.8))
                patch_uuids.append(uuid)
            
            # Set up radiation data required for energy balance
            setup_radiation_for_energy_balance(context, "SW")
            
            with EnergyBalanceModel(context) as energy_balance:
                energy_balance.addRadiationBand("SW")
                energy_balance.enableAirEnergyBalance(canopy_height_m=3.0, reference_height_m=10.0)
                
                # Test air energy balance for specific UUIDs
                energy_balance.evaluateAirEnergyBalance(
                    dt_sec=30.0, time_advance_sec=300.0, UUIDs=patch_uuids[:2])
    
    def test_optional_output_data(self):
        """Test optional output data functionality"""
        with Context() as context:
            context.addPatch(center=vec3(0, 0, 1), size=vec2(1, 1))
            
            with EnergyBalanceModel(context) as energy_balance:
                # Test adding optional output data
                energy_balance.optionalOutputPrimitiveData("vapor_pressure_deficit")
                energy_balance.optionalOutputPrimitiveData("net_radiation")
                energy_balance.optionalOutputPrimitiveData("boundary_layer_conductance")
                
                # Test validation
                with pytest.raises(ValueError, match="non-empty string"):
                    energy_balance.optionalOutputPrimitiveData("")
                
                with pytest.raises(ValueError, match="non-empty string"):
                    energy_balance.optionalOutputPrimitiveData(None)
    
    def test_default_value_reporting(self):
        """Test default value reporting functionality"""
        with Context() as context:
            patch_uuids = []
            for i in range(3):
                uuid = context.addPatch(center=vec3(i, 0, 1.0), size=vec2(0.5, 0.5))
                patch_uuids.append(uuid)
            
            with EnergyBalanceModel(context) as energy_balance:
                # Test report for all primitives (should not crash)
                energy_balance.printDefaultValueReport()
                
                # Test report for specific UUIDs
                energy_balance.printDefaultValueReport(UUIDs=patch_uuids[:2])
    
    def test_context_integration(self):
        """Test integration with Context geometry operations"""
        with Context() as context:
            # Create various geometry types
            patch_uuid = context.addPatch(center=vec3(0, 0, 1), size=vec2(1, 1))
            triangle_uuid = context.addTriangle(vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0))
            
            # Set up radiation data required for energy balance
            setup_radiation_for_energy_balance(context, "SW")
            
            with EnergyBalanceModel(context) as energy_balance:
                energy_balance.addRadiationBand("SW")
                
                # Test that energy balance works with mixed geometry
                energy_balance.run()
                
                # Test with specific geometry types
                energy_balance.run(uuids=[patch_uuid])
                energy_balance.run(uuids=[triangle_uuid])
                energy_balance.run(uuids=[patch_uuid, triangle_uuid])


@pytest.mark.native_only
class TestEnergyBalanceIntegration:
    """Test energy balance integration with other PyHelios components"""
    
    def test_error_handling_integration(self):
        """Test that C++ exceptions become proper Python exceptions"""
        with Context() as context:
            with EnergyBalanceModel(context) as energy_balance:
                # Test operations that should cause specific errors
                # Most validation is done in Python layer, but test C++ error handling
                try:
                    # This should work without error
                    energy_balance.addRadiationBand("SW")
                    energy_balance.run()
                except EnergyBalanceModelError as e:
                    # If error occurs, verify it's properly translated
                    error_msg = str(e).lower()
                    # Should be informative error message
                    assert len(error_msg) > 10
    
    def test_multiple_energy_balance_models(self):
        """Test creating multiple energy balance models"""
        with Context() as context1, Context() as context2:
            context1.addPatch(center=vec3(0, 0, 1), size=vec2(1, 1))
            context2.addPatch(center=vec3(1, 1, 2), size=vec2(2, 2))
            
            # Set up radiation data for both contexts
            setup_radiation_for_energy_balance(context1, "SW")
            setup_radiation_for_energy_balance(context2, "LW")
            
            with EnergyBalanceModel(context1) as eb1, EnergyBalanceModel(context2) as eb2:
                eb1.addRadiationBand("SW")
                eb2.addRadiationBand("LW")
                
                # Both should work independently
                eb1.run()
                eb2.run()


@pytest.mark.mock_mode
class TestEnergyBalanceMockMode:
    """Tests specifically for mock mode behavior"""
    
    def test_mock_mode_graceful_degradation(self):
        """Test that EnergyBalanceModel provides clear error message when energy balance plugin is unavailable"""
        from pyhelios.plugins.registry import get_plugin_registry
        
        # Skip this test if energy balance plugin is actually available
        registry = get_plugin_registry()
        if registry.is_plugin_available('energybalance'):
            pytest.skip("Energy balance plugin is available - this test is for mock mode only")
        
        with Context() as context:
            # EnergyBalanceModel should raise EnergyBalanceModelError when energy balance plugin is not available
            with pytest.raises(EnergyBalanceModelError) as excinfo:
                EnergyBalanceModel(context)
            
            # Error message should be informative and actionable
            error_msg = str(excinfo.value)
            assert "'energybalance' plugin" in error_msg
            assert "not available" in error_msg
            
            # Should mention system requirements
            assert any(keyword in error_msg for keyword in ["GPU", "CUDA", "build"])
            
            # Should provide actionable solutions  
            assert "build_scripts/build_helios" in error_msg


@pytest.mark.slow
class TestEnergyBalancePerformance:
    """Performance tests for energy balance operations"""
    
    @pytest.mark.native_only
    def test_large_geometry_performance(self):
        """Test energy balance performance with large geometry sets"""
        import time
        
        with Context() as context:
            # Create larger geometry set
            patch_uuids = []
            for i in range(100):  # Create 100 patches
                for j in range(10):
                    uuid = context.addPatch(center=vec3(i*0.1, j*0.1, 1.0), size=vec2(0.05, 0.05))
                    patch_uuids.append(uuid)
            
            # Set up radiation data required for energy balance
            setup_radiation_for_energy_balance(context, "SW")
            
            with EnergyBalanceModel(context) as energy_balance:
                energy_balance.addRadiationBand("SW")
                
                # Time energy balance execution
                start_time = time.time()
                energy_balance.run()
                elapsed = time.time() - start_time
                
                # Should complete within reasonable time (adjust threshold as needed)
                assert elapsed < 30.0, f"Energy balance too slow for 1000 patches: {elapsed:.3f}s"
    
    @pytest.mark.native_only
    def test_dynamic_simulation_performance(self):
        """Test performance of dynamic energy balance simulations"""
        import time
        
        with Context() as context:
            # Create moderate geometry
            for i in range(25):  # 25x25 = 625 patches
                for j in range(25):
                    context.addPatch(center=vec3(i*0.2, j*0.2, 2.0), size=vec2(0.15, 0.15))
            
            # Set up radiation data required for energy balance
            setup_radiation_for_energy_balance(context, "SW")
            
            with EnergyBalanceModel(context) as energy_balance:
                energy_balance.addRadiationBand("SW")
                energy_balance.enableAirEnergyBalance()
                
                # Time dynamic simulation
                start_time = time.time()
                energy_balance.run(dt=60.0)  # Single timestep
                elapsed = time.time() - start_time
                
                # Should complete within reasonable time
                assert elapsed < 15.0, f"Dynamic energy balance too slow: {elapsed:.3f}s"


@pytest.mark.native_only
class TestEnergyBalanceEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_context(self):
        """Test energy balance with empty context"""
        with Context() as context:
            with EnergyBalanceModel(context) as energy_balance:
                energy_balance.addRadiationBand("SW")
                
                # Should handle empty geometry gracefully
                energy_balance.run()
    
    def test_single_primitive(self):
        """Test energy balance with single primitive"""
        with Context() as context:
            uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(0.1, 0.1))
            
            # Set up radiation data required for energy balance
            setup_radiation_for_energy_balance(context, "SW")
            
            with EnergyBalanceModel(context) as energy_balance:
                energy_balance.addRadiationBand("SW")
                energy_balance.run()
                energy_balance.run(uuids=[uuid])
    
    def test_very_small_timesteps(self):
        """Test energy balance with very small timesteps"""
        with Context() as context:
            context.addPatch(center=vec3(0, 0, 1), size=vec2(1, 1))
            
            # Set up radiation data required for energy balance
            setup_radiation_for_energy_balance(context, "SW")
            
            with EnergyBalanceModel(context) as energy_balance:
                energy_balance.addRadiationBand("SW")
                
                # Test very small timestep (should still work)
                energy_balance.run(dt=0.1)  # 0.1 second
                
                # Test very small air energy balance timestep
                energy_balance.enableAirEnergyBalance()
                energy_balance.evaluateAirEnergyBalance(dt_sec=0.5, time_advance_sec=1.0)
    
    def test_large_timesteps(self):
        """Test energy balance with large timesteps"""
        with Context() as context:
            context.addPatch(center=vec3(0, 0, 1), size=vec2(1, 1))
            
            # Set up radiation data required for energy balance
            setup_radiation_for_energy_balance(context, "SW")
            
            with EnergyBalanceModel(context) as energy_balance:
                energy_balance.addRadiationBand("SW")
                
                # Test large timestep
                energy_balance.run(dt=3600.0)  # 1 hour
                
                # Test large air energy balance timestep
                energy_balance.enableAirEnergyBalance()
                energy_balance.evaluateAirEnergyBalance(dt_sec=300.0, time_advance_sec=7200.0)  # 5min steps, 2 hour total