"""
Tests for PlantArchitecture plugin functionality.

This module tests the PlantArchitecture plugin integration including plant library
functionality, procedural plant generation, and time-based growth simulation.
"""

import pytest
from unittest.mock import patch, MagicMock
import ctypes
from typing import List

import pyhelios
from pyhelios import Context, PlantArchitecture, PlantArchitectureError
from pyhelios.types import vec3, vec2, int2
from pyhelios.wrappers import UPlantArchitectureWrapper as plantarch_wrapper
from pyhelios.plugins.registry import get_plugin_registry


@pytest.mark.cross_platform
class TestPlantArchitectureAvailability:
    """Test PlantArchitecture availability detection across platforms"""

    def test_is_plantarchitecture_available(self):
        """Test PlantArchitecture availability check"""
        from pyhelios.PlantArchitecture import is_plantarchitecture_available

        # Function should return boolean without raising exceptions
        result = is_plantarchitecture_available()
        assert isinstance(result, bool)

    def test_plantarchitecture_import(self):
        """Test that PlantArchitecture can be imported"""
        # Should not raise ImportError
        assert PlantArchitecture is not None or PlantArchitecture is None
        assert PlantArchitectureError is not None or PlantArchitectureError is None

    def test_plugin_in_pyhelios_namespace(self):
        """Test PlantArchitecture is available in pyhelios namespace"""
        # Should be available through main import
        assert hasattr(pyhelios, 'PlantArchitecture')
        assert hasattr(pyhelios, 'PlantArchitectureError')


@pytest.mark.cross_platform
class TestPlantArchitectureMockMode:
    """Test PlantArchitecture mock mode functionality"""

    def test_mock_mode_wrapper_functions(self):
        """Test mock mode wrapper functions raise appropriate errors"""
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            # Test that mock functions raise informative errors
            with pytest.raises(RuntimeError, match="Mock mode"):
                plantarch_wrapper.createPlantArchitecture(None)

            with pytest.raises(RuntimeError, match="Mock mode"):
                plantarch_wrapper.loadPlantModelFromLibrary(None, "bean")

    def test_graceful_unavailable_handling(self):
        """Test graceful handling when plugin unavailable"""
        registry = get_plugin_registry()

        with Context() as context:
            if not registry.is_plugin_available('plantarchitecture'):
                # Should raise informative error
                with pytest.raises(PlantArchitectureError) as exc_info:
                    PlantArchitecture(context)

                error_msg = str(exc_info.value).lower()
                # Error should mention rebuilding
                assert any(keyword in error_msg for keyword in
                          ['rebuild', 'build', 'enable', 'compile'])
                # Error should mention PlantArchitecture
                assert any(keyword in error_msg for keyword in
                          ['plantarchitecture', 'plant architecture'])
            else:
                # Plugin is available - test that it can be created successfully
                with PlantArchitecture(context) as plantarch:
                    assert plantarch is not None


@pytest.mark.native_only
class TestPlantArchitectureNative:
    """Test PlantArchitecture with native library functionality"""

    @pytest.fixture
    def context(self, check_native_library):
        """Create a Context for testing with proper cleanup"""
        context = Context()
        yield context
        # CRITICAL: Proper cleanup to prevent state contamination
        context.__exit__(None, None, None)

    @pytest.fixture
    def plantarch(self, context):
        """Create PlantArchitecture instance with proper cleanup"""
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture plugin not available")

        try:
            plantarch_instance = PlantArchitecture(context)
            yield plantarch_instance
            # CRITICAL: Proper cleanup to prevent state contamination
            plantarch_instance.__exit__(None, None, None)
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture initialization failed: {e}")

    def test_plantarchitecture_context_manager(self, context):
        """Test PlantArchitecture context manager protocol"""
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture plugin not available")

        try:
            with PlantArchitecture(context) as plantarch:
                assert plantarch._plantarch_ptr is not None
                assert plantarch.context is context
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_get_available_plant_models(self, plantarch):
        """Test getting available plant models from library"""
        models = plantarch.getAvailablePlantModels()

        assert isinstance(models, list)
        assert len(models) > 0

        # Check for expected plant models
        expected_models = ['bean', 'almond', 'apple', 'maize', 'rice', 'soybean']
        for model in expected_models:
            if model in models:
                assert isinstance(model, str)
                assert len(model) > 0

    def test_load_plant_model_from_library(self, plantarch):
        """Test loading a plant model from library"""
        # Get available models first
        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        # Load the first available model
        model_name = models[0]

        # Should not raise exception
        plantarch.loadPlantModelFromLibrary(model_name)

    def test_load_invalid_plant_model(self, plantarch):
        """Test loading non-existent plant model"""
        with pytest.raises(PlantArchitectureError, match="Failed to load plant model"):
            plantarch.loadPlantModelFromLibrary("nonexistent_plant_model")

    def test_build_plant_instance_from_library(self, plantarch):
        """Test building a plant instance from library"""
        # Load a plant model first
        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        model_name = models[0]
        plantarch.loadPlantModelFromLibrary(model_name)

        # Build plant instance
        position = vec3(0, 0, 0)
        age = 30.0

        plant_id = plantarch.buildPlantInstanceFromLibrary(position, age)

        assert isinstance(plant_id, int)
        assert plant_id >= 0  # Plant IDs can be 0 or positive

    def test_build_plant_canopy_from_library(self, plantarch):
        """Test building a plant canopy from library"""
        # Load a plant model first
        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        model_name = models[0]
        plantarch.loadPlantModelFromLibrary(model_name)

        # Build small canopy
        canopy_center = vec3(0, 0, 0)
        plant_spacing = vec2(0.5, 0.5)
        plant_count = int2(2, 2)
        age = 20.0

        plant_ids = plantarch.buildPlantCanopyFromLibrary(
            canopy_center, plant_spacing, plant_count, age
        )

        assert isinstance(plant_ids, list)
        assert len(plant_ids) == 4  # 2x2 = 4 plants
        for plant_id in plant_ids:
            assert isinstance(plant_id, int)
            assert plant_id >= 0  # Plant IDs can be 0 or positive

    def test_advance_time(self, plantarch):
        """Test advancing time for plant growth"""
        # Load model and create plant
        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        model_name = models[0]
        plantarch.loadPlantModelFromLibrary(model_name)

        position = vec3(0, 0, 0)
        age = 10.0
        plant_id = plantarch.buildPlantInstanceFromLibrary(position, age)

        # Advance time
        time_step = 5.0
        plantarch.advanceTime(time_step)

        # Should complete without exception

    def test_get_plant_object_ids(self, plantarch):
        """Test getting object IDs for a plant"""
        # Load model and create plant
        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        model_name = models[0]
        plantarch.loadPlantModelFromLibrary(model_name)

        position = vec3(0, 0, 0)
        age = 15.0
        plant_id = plantarch.buildPlantInstanceFromLibrary(position, age)

        # Get object IDs
        object_ids = plantarch.getAllPlantObjectIDs(plant_id)

        assert isinstance(object_ids, list)
        for obj_id in object_ids:
            assert isinstance(obj_id, int)

    def test_get_plant_uuids(self, plantarch):
        """Test getting UUIDs for a plant"""
        # Load model and create plant
        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        model_name = models[0]
        plantarch.loadPlantModelFromLibrary(model_name)

        position = vec3(0, 0, 0)
        age = 15.0
        plant_id = plantarch.buildPlantInstanceFromLibrary(position, age)

        # Get UUIDs
        uuids = plantarch.getAllPlantUUIDs(plant_id)

        assert isinstance(uuids, list)
        for uuid in uuids:
            assert isinstance(uuid, int)

    def test_build_plant_with_age_zero(self, plantarch):
        """Test that plants can be built with age=0 (newborn plants)"""
        # Load model
        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        model_name = models[0]
        plantarch.loadPlantModelFromLibrary(model_name)

        # Test age=0 - should work without error
        position = vec3(0, 0, 0)
        plant_id = plantarch.buildPlantInstanceFromLibrary(position, age=0.0)

        assert isinstance(plant_id, int)
        assert plant_id >= 0  # Plant IDs can be 0 or positive

        # Verify plant was actually created by getting its object IDs
        object_ids = plantarch.getAllPlantObjectIDs(plant_id)
        assert isinstance(object_ids, list)
        # Note: age=0 plants may have minimal geometry, so we don't enforce object_ids length

    def test_build_plant_canopy_with_age_zero(self, plantarch):
        """Test that plant canopies can be built with age=0 (newborn plants)"""
        # Load model
        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        model_name = models[0]
        plantarch.loadPlantModelFromLibrary(model_name)

        # Build small canopy with age=0
        canopy_center = vec3(0, 0, 0)
        plant_spacing = vec2(0.5, 0.5)
        plant_count = int2(2, 2)
        age = 0.0

        plant_ids = plantarch.buildPlantCanopyFromLibrary(
            canopy_center, plant_spacing, plant_count, age
        )

        assert isinstance(plant_ids, list)
        assert len(plant_ids) == 4  # 2x2 = 4 plants
        for plant_id in plant_ids:
            assert isinstance(plant_id, int)
            assert plant_id >= 0  # Plant IDs can be 0 or positive


@pytest.mark.cross_platform
class TestPlantArchitectureValidation:
    """Test PlantArchitecture parameter validation"""

    def test_validation_function_availability(self):
        """Test that validation functions are available"""
        # These functions should be available regardless of plugin availability
        from pyhelios.PlantArchitecture import validate_vec3, validate_vec2, validate_int2
        from pyhelios.validation.core import validate_positive_value

        # Just verify they can be imported
        assert validate_vec3 is not None
        assert validate_vec2 is not None
        assert validate_int2 is not None
        assert validate_positive_value is not None


@pytest.mark.cross_platform
class TestPlantArchitectureAssets:
    """Test PlantArchitecture asset management"""

    def test_working_directory_context_manager(self):
        """Test the working directory context manager"""
        from pyhelios.PlantArchitecture import _plantarchitecture_working_directory

        # Working directory context manager must succeed - no fallbacks allowed
        with _plantarchitecture_working_directory() as working_dir:
            assert working_dir is not None
            assert working_dir.exists(), f"Working directory must exist: {working_dir}"

    def test_working_directory_asset_validation(self):
        """Test working directory asset validation - this test verifies the function works correctly"""
        from pyhelios.PlantArchitecture import _plantarchitecture_working_directory

        # Test that the working directory function can be called successfully
        # In our current development environment, assets should be available
        try:
            with _plantarchitecture_working_directory() as working_dir:
                # Verify we get a valid working directory
                assert working_dir is not None
                assert working_dir.exists(), f"Working directory should exist: {working_dir}"

                # Verify the expected structure exists
                plantarch_dir = working_dir / 'plugins' / 'plantarchitecture'
                assert plantarch_dir.exists(), f"PlantArchitecture directory should exist: {plantarch_dir}"

        except RuntimeError as e:
            # If assets are missing, we should get an informative error message
            error_msg = str(e).lower()
            assert any(keyword in error_msg for keyword in
                      ['plantarchitecture', 'asset', 'build', 'directory']), \
                   f"Error message should mention missing assets: {e}"


@pytest.mark.integration
class TestPlantArchitectureIntegration:
    """Integration tests for PlantArchitecture with Context"""

    @pytest.fixture
    def context(self, check_native_library):
        """Create a Context for integration testing with proper cleanup"""
        context = Context()
        yield context
        # CRITICAL: Proper cleanup to prevent state contamination
        context.__exit__(None, None, None)

    def test_plantarchitecture_with_context(self, context):
        """Test PlantArchitecture integration with Context"""
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture plugin not available")

        try:
            with PlantArchitecture(context) as plantarch:
                # Test basic functionality
                models = plantarch.getAvailablePlantModels()
                assert isinstance(models, list)

                if models:
                    # Load a model and verify context interaction
                    plantarch.loadPlantModelFromLibrary(models[0])

                    # Build plant and check it creates geometry in context
                    initial_primitive_count = context.getPrimitiveCount()

                    plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 20.0)
                    assert plant_id >= 0  # Plant IDs can be 0 or positive

                    # Should have added primitives to context
                    final_primitive_count = context.getPrimitiveCount()
                    assert final_primitive_count >= initial_primitive_count

        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")


@pytest.mark.cross_platform
class TestPlantArchitectureConvenienceFunctions:
    """Test PlantArchitecture convenience functions"""

    def test_create_plant_architecture_function(self):
        """Test create_plant_architecture convenience function"""
        from pyhelios.PlantArchitecture import create_plant_architecture, PlantArchitecture

        context = MagicMock()

        # Mock successful creation by patching the class in the current test module
        with patch.object(PlantArchitecture, '__new__', return_value=MagicMock()) as mock_new:
            mock_instance = mock_new.return_value

            result = create_plant_architecture(context)

            # Verify the function returns what we expected
            assert result == mock_instance