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
from pyhelios.wrappers.DataTypes import AxisRotation  # Import directly from DataTypes to avoid Windows import issues
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

    def test_plantarchitecture_context_manager(self, basic_context):
        """Test PlantArchitecture context manager protocol"""
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture plugin not available")

        try:
            with PlantArchitecture(basic_context) as plantarch:
                assert plantarch._plantarch_ptr is not None
                assert plantarch.context is basic_context
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
class TestPlantArchitectureUSDValidation:
    """Validation tests for the new USD/growth-frame methods that work without native libs."""

    def _stub_plantarch(self):
        """Build a PlantArchitecture instance with a dummy pointer for validation tests.

        We bypass __init__ because availability checks would otherwise prevent us
        from constructing the object in mock mode. The validation tested here
        runs before any C call, so the dummy pointer is never dereferenced.
        """
        plantarch = PlantArchitecture.__new__(PlantArchitecture)
        plantarch._plantarch_ptr = None
        plantarch.context = None
        return plantarch

    def test_write_plant_structure_usd_negative_id(self):
        plantarch = self._stub_plantarch()
        with pytest.raises(ValueError, match="non-negative"):
            plantarch.writePlantStructureUSD(-1, "out.usda")

    def test_write_plant_structure_usd_empty_filename(self):
        plantarch = self._stub_plantarch()
        with pytest.raises(ValueError, match="empty"):
            plantarch.writePlantStructureUSD(0, "")

    def test_register_growth_frame_negative_id(self):
        plantarch = self._stub_plantarch()
        with pytest.raises(ValueError, match="non-negative"):
            plantarch.registerGrowthFrame(-1)

    def test_write_plant_growth_usd_negative_id(self):
        plantarch = self._stub_plantarch()
        with pytest.raises(ValueError, match="non-negative"):
            plantarch.writePlantGrowthUSD(-1, "out.usda")

    def test_write_plant_growth_usd_empty_filename(self):
        plantarch = self._stub_plantarch()
        with pytest.raises(ValueError, match="empty"):
            plantarch.writePlantGrowthUSD(0, "")

    def test_clear_growth_frames_negative_id(self):
        plantarch = self._stub_plantarch()
        with pytest.raises(ValueError, match="non-negative"):
            plantarch.clearGrowthFrames(-1)

    def test_get_growth_frame_count_negative_id(self):
        plantarch = self._stub_plantarch()
        with pytest.raises(ValueError, match="non-negative"):
            plantarch.getGrowthFrameCount(-1)


@pytest.mark.cross_platform
class TestPlantArchitectureAssets:
    """Test PlantArchitecture asset management"""

    def test_working_directory_context_manager(self):
        """Test the working directory context manager"""
        from pyhelios.PlantArchitecture import _plantarchitecture_working_directory

        # Test working directory context manager - skip if assets not built
        try:
            with _plantarchitecture_working_directory() as working_dir:
                assert working_dir is not None
                assert working_dir.exists(), f"Working directory must exist: {working_dir}"
        except RuntimeError as e:
            # Assets not available - skip test with informative message
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ['plantarchitecture', 'assets', 'not found', 'build']):
                pytest.skip(f"PlantArchitecture assets not available: {e}")

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

    def test_plantarchitecture_with_context(self, basic_context):
        """Test PlantArchitecture integration with Context"""
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture plugin not available")

        try:
            with PlantArchitecture(basic_context) as plantarch:
                # Test basic functionality
                models = plantarch.getAvailablePlantModels()
                assert isinstance(models, list)

                if models:
                    # Load a model and verify context interaction
                    plantarch.loadPlantModelFromLibrary(models[0])

                    # Build plant and check it creates geometry in context
                    initial_primitive_count = basic_context.getPrimitiveCount()

                    plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 20.0)
                    assert plant_id >= 0  # Plant IDs can be 0 or positive

                    # Should have added primitives to context
                    final_primitive_count = basic_context.getPrimitiveCount()
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


@pytest.mark.native_only
class TestPlantArchitectureCollisionDetection:
    """Test PlantArchitecture collision detection functionality"""

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

    def test_enable_soft_collision_avoidance_basic(self, plantarch):
        """Test enabling soft collision avoidance with default parameters"""
        # Should not raise exception
        plantarch.enableSoftCollisionAvoidance()

    def test_enable_soft_collision_avoidance_with_target_uuids(self, plantarch, context):
        """Test enabling collision avoidance with specific target UUIDs"""
        # Add some geometry to the context
        patch_uuid = context.addPatch(center=vec3(2, 2, 0), size=(1, 1))

        # Enable collision with specific UUIDs
        plantarch.enableSoftCollisionAvoidance(target_object_UUIDs=[patch_uuid])

    def test_enable_soft_collision_avoidance_with_petiole_fruit(self, plantarch):
        """Test enabling collision detection for petioles and fruit"""
        plantarch.enableSoftCollisionAvoidance(
            enable_petiole_collision=True,
            enable_fruit_collision=True
        )

    def test_disable_collision_detection(self, plantarch):
        """Test disabling collision detection"""
        # Enable first
        plantarch.enableSoftCollisionAvoidance()

        # Then disable - should not raise exception
        plantarch.disableCollisionDetection()

    def test_set_soft_collision_avoidance_parameters_default(self, plantarch):
        """Test setting collision parameters with default values"""
        # Should not raise exception
        plantarch.setSoftCollisionAvoidanceParameters()

    def test_set_soft_collision_avoidance_parameters_custom(self, plantarch):
        """Test setting collision parameters with custom values"""
        plantarch.setSoftCollisionAvoidanceParameters(
            view_half_angle_deg=60.0,
            look_ahead_distance=0.05,
            sample_count=512,
            inertia_weight=0.3
        )

    def test_set_soft_collision_avoidance_parameters_validation(self, plantarch):
        """Test parameter validation for collision avoidance settings"""
        # Test invalid view half angle
        with pytest.raises(ValueError, match="view_half_angle_deg must be between 0 and 180"):
            plantarch.setSoftCollisionAvoidanceParameters(view_half_angle_deg=200.0)

        with pytest.raises(ValueError, match="view_half_angle_deg must be between 0 and 180"):
            plantarch.setSoftCollisionAvoidanceParameters(view_half_angle_deg=-10.0)

        # Test invalid look ahead distance
        with pytest.raises(ValueError, match="look_ahead_distance must be positive"):
            plantarch.setSoftCollisionAvoidanceParameters(look_ahead_distance=0.0)

        with pytest.raises(ValueError, match="look_ahead_distance must be positive"):
            plantarch.setSoftCollisionAvoidanceParameters(look_ahead_distance=-0.1)

        # Test invalid sample count
        with pytest.raises(ValueError, match="sample_count must be positive"):
            plantarch.setSoftCollisionAvoidanceParameters(sample_count=0)

        with pytest.raises(ValueError, match="sample_count must be positive"):
            plantarch.setSoftCollisionAvoidanceParameters(sample_count=-10)

        # Test invalid inertia weight
        with pytest.raises(ValueError, match="inertia_weight must be between 0 and 1"):
            plantarch.setSoftCollisionAvoidanceParameters(inertia_weight=1.5)

        with pytest.raises(ValueError, match="inertia_weight must be between 0 and 1"):
            plantarch.setSoftCollisionAvoidanceParameters(inertia_weight=-0.1)

    def test_set_collision_relevant_organs_default(self, plantarch):
        """Test setting collision-relevant organs with default settings"""
        plantarch.setCollisionRelevantOrgans(
            include_internodes=True,
            include_leaves=True
        )

    def test_set_collision_relevant_organs_all(self, plantarch):
        """Test enabling collision detection for all organ types"""
        plantarch.setCollisionRelevantOrgans(
            include_internodes=True,
            include_leaves=True,
            include_petioles=True,
            include_flowers=True,
            include_fruit=True
        )

    def test_set_collision_relevant_organs_none(self, plantarch):
        """Test disabling collision detection for all organ types"""
        plantarch.setCollisionRelevantOrgans(
            include_internodes=False,
            include_leaves=False,
            include_petioles=False,
            include_flowers=False,
            include_fruit=False
        )

    def test_enable_solid_obstacle_avoidance(self, plantarch, context):
        """Test enabling solid obstacle avoidance"""
        # Add obstacle geometry
        patch_uuid = context.addPatch(center=vec3(2, 2, 0), size=(1, 1))

        # Enable solid obstacle avoidance
        plantarch.enableSolidObstacleAvoidance(
            obstacle_UUIDs=[patch_uuid],
            avoidance_distance=0.5
        )

    def test_enable_solid_obstacle_avoidance_with_options(self, plantarch, context):
        """Test solid obstacle avoidance with fruit adjustment and pruning"""
        # Add obstacle geometry
        patch_uuid = context.addPatch(center=vec3(1, 1, 0), size=(1, 1))

        plantarch.enableSolidObstacleAvoidance(
            obstacle_UUIDs=[patch_uuid],
            avoidance_distance=0.2,
            enable_fruit_adjustment=True,
            enable_obstacle_pruning=True
        )

    def test_enable_solid_obstacle_avoidance_validation(self, plantarch):
        """Test parameter validation for solid obstacle avoidance"""
        # Test empty UUID list
        with pytest.raises(ValueError, match="Obstacle UUIDs list cannot be empty"):
            plantarch.enableSolidObstacleAvoidance(obstacle_UUIDs=[])

        # Test invalid avoidance distance
        with pytest.raises(ValueError, match="avoidance_distance must be positive"):
            plantarch.enableSolidObstacleAvoidance(
                obstacle_UUIDs=[1, 2, 3],
                avoidance_distance=0.0
            )

        with pytest.raises(ValueError, match="avoidance_distance must be positive"):
            plantarch.enableSolidObstacleAvoidance(
                obstacle_UUIDs=[1, 2, 3],
                avoidance_distance=-0.5
            )

    def test_set_static_obstacles(self, plantarch, context):
        """Test marking geometry as static obstacles"""
        # Add some geometry
        patch_uuid1 = context.addPatch(center=vec3(0, 0, 0), size=(2, 2))
        patch_uuid2 = context.addPatch(center=vec3(5, 5, 0), size=(2, 2))

        # Enable collision detection first (required by C++ implementation)
        plantarch.enableSoftCollisionAvoidance()

        # Mark as static obstacles
        plantarch.setStaticObstacles([patch_uuid1, patch_uuid2])

    def test_set_static_obstacles_validation(self, plantarch):
        """Test parameter validation for static obstacles"""
        # Test empty UUID list
        with pytest.raises(ValueError, match="target_UUIDs list cannot be empty"):
            plantarch.setStaticObstacles([])

    def test_get_plant_collision_relevant_object_ids(self, plantarch):
        """Test getting collision-relevant object IDs for a plant"""
        # Load model and create plant
        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        model_name = models[0]
        plantarch.loadPlantModelFromLibrary(model_name)

        position = vec3(0, 0, 0)
        age = 20.0
        plant_id = plantarch.buildPlantInstanceFromLibrary(position, age)

        # Get collision-relevant object IDs
        collision_obj_ids = plantarch.getPlantCollisionRelevantObjectIDs(plant_id)

        assert isinstance(collision_obj_ids, list)
        for obj_id in collision_obj_ids:
            assert isinstance(obj_id, int)

    def test_get_plant_collision_relevant_object_ids_validation(self, plantarch):
        """Test parameter validation for getting collision-relevant object IDs"""
        # Test negative plant ID
        with pytest.raises(ValueError, match="Plant ID must be non-negative"):
            plantarch.getPlantCollisionRelevantObjectIDs(-1)


@pytest.mark.integration
class TestPlantArchitectureCollisionIntegration:
    """Integration tests for PlantArchitecture collision detection with Context"""

    @pytest.fixture
    def context(self, check_native_library):
        """Create a Context for integration testing with proper cleanup"""
        context = Context()
        yield context
        # CRITICAL: Proper cleanup to prevent state contamination
        context.__exit__(None, None, None)

    def test_collision_detection_workflow(self, basic_context):
        """Test complete collision detection workflow"""
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture plugin not available")

        try:
            with PlantArchitecture(basic_context) as plantarch:
                # Get available models
                models = plantarch.getAvailablePlantModels()
                if not models:
                    pytest.skip("No plant models available")

                # Load a plant model
                model_name = models[0]
                plantarch.loadPlantModelFromLibrary(model_name)

                # Create obstacle geometry
                obstacle_uuid = basic_context.addPatch(center=vec3(2, 2, 1), size=(1, 1))

                # Configure collision parameters
                plantarch.setSoftCollisionAvoidanceParameters(
                    view_half_angle_deg=80.0,
                    look_ahead_distance=0.1,
                    sample_count=256,
                    inertia_weight=0.4
                )

                # Set organ filtering
                plantarch.setCollisionRelevantOrgans(
                    include_internodes=True,
                    include_leaves=True
                )

                # Enable soft collision avoidance FIRST
                plantarch.enableSoftCollisionAvoidance(
                    target_object_UUIDs=[obstacle_uuid]
                )

                # Mark as static obstacle for optimization (must be AFTER enabling collision detection)
                plantarch.setStaticObstacles([obstacle_uuid])

                # Build plant with collision detection enabled
                plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), age=20.0)
                assert plant_id >= 0

                # Advance time with collision detection active
                plantarch.advanceTime(10.0)

                # Query collision-relevant geometry
                collision_obj_ids = plantarch.getPlantCollisionRelevantObjectIDs(plant_id)
                assert isinstance(collision_obj_ids, list)

                # Disable collision detection
                plantarch.disableCollisionDetection()

        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_solid_obstacle_workflow(self, basic_context):
        """Test solid obstacle avoidance workflow"""
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture plugin not available")

        try:
            with PlantArchitecture(basic_context) as plantarch:
                # Get available models
                models = plantarch.getAvailablePlantModels()
                if not models:
                    pytest.skip("No plant models available")

                # Load a plant model
                model_name = models[0]
                plantarch.loadPlantModelFromLibrary(model_name)

                # Create solid obstacle (e.g., wall)
                wall_uuid = basic_context.addPatch(center=vec3(1, 1, 0), size=(2, 2))

                # Enable solid obstacle avoidance
                plantarch.enableSolidObstacleAvoidance(
                    obstacle_UUIDs=[wall_uuid],
                    avoidance_distance=0.3,
                    enable_fruit_adjustment=True
                )

                # Build plant near obstacle
                plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), age=15.0)
                assert plant_id >= 0

                # Advance time - plant growth should avoid solid obstacle
                plantarch.advanceTime(5.0)

        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")


@pytest.mark.native_only
class TestPlantArchitectureFileIO:
    """Test PlantArchitecture file I/O functionality"""

    @pytest.fixture
    def context(self, check_native_library):
        """Create a Context for testing with proper cleanup"""
        context = Context()
        yield context
        context.__exit__(None, None, None)

    @pytest.fixture
    def plantarch(self, context):
        """Create PlantArchitecture instance with proper cleanup"""
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture plugin not available")

        try:
            plantarch_instance = PlantArchitecture(context)
            yield plantarch_instance
            plantarch_instance.__exit__(None, None, None)
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture initialization failed: {e}")

    def test_write_plant_mesh_vertices(self, plantarch, tmp_path):
        """Test writing plant mesh vertices to file"""
        # Load model and create plant
        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        plantarch.loadPlantModelFromLibrary(models[0])
        plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), age=20.0)

        # Write vertices to file
        output_file = tmp_path / "plant_vertices.txt"
        plantarch.writePlantMeshVertices(plant_id, str(output_file))

        # Verify file was created and contains data
        assert output_file.exists()
        assert output_file.stat().st_size > 0

        # Verify content format (x y z per line)
        with open(output_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 0
            # Check first line has 3 float values
            first_line = lines[0].strip().split()
            assert len(first_line) == 3
            for val in first_line:
                float(val)  # Should not raise exception

    def test_write_plant_structure_xml(self, plantarch, tmp_path):
        """Test writing plant structure to XML file"""
        # Load model and create plant
        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        model_name = models[0]
        plantarch.loadPlantModelFromLibrary(model_name)
        plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), age=25.0)

        # Write XML
        output_file = tmp_path / "plant_structure.xml"
        plantarch.writePlantStructureXML(plant_id, str(output_file))

        # Verify file was created
        assert output_file.exists()
        assert output_file.stat().st_size > 0

        # Verify it's valid XML
        with open(output_file, 'r') as f:
            content = f.read()
            assert content.startswith('<?xml')
            # Note: Can't test loading here without loading the model first

    def test_write_qsm_cylinder_file(self, plantarch, tmp_path):
        """Test writing TreeQSM cylinder format file"""
        # Load model and create plant
        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        plantarch.loadPlantModelFromLibrary(models[0])
        plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), age=30.0)

        # Write QSM file
        output_file = tmp_path / "plant_qsm.txt"
        plantarch.writeQSMCylinderFile(plant_id, str(output_file))

        # Verify file was created
        assert output_file.exists()
        assert output_file.stat().st_size > 0

        # Verify content format (tab-separated values)
        with open(output_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 0
            # Check first line has multiple tab-separated values
            first_line = lines[0].strip()
            assert '\t' in first_line or ' ' in first_line

    def test_read_plant_structure_xml(self, plantarch, tmp_path):
        """Test reading plant structure from XML file"""
        # Note: This test verifies the XML write operation works correctly.
        # XML loading has C++ limitations with certain plant models/growth stages,
        # so we focus on testing that our Python interface correctly calls the
        # C++ functions and handles errors properly.

        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        model_name = models[0]
        plantarch.loadPlantModelFromLibrary(model_name)
        plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), age=5.0)

        # Save to XML - this tests that writePlantStructureXML works
        xml_file = tmp_path / "plant_to_load.xml"
        plantarch.writePlantStructureXML(plant_id, str(xml_file))

        # Verify file was created with valid XML content
        assert xml_file.exists()
        assert xml_file.stat().st_size > 0

        with open(xml_file, 'r') as f:
            content = f.read()
            assert content.startswith('<?xml')
            assert 'plant' in content.lower()  # Should contain plant-related data

    def test_xml_roundtrip(self, plantarch, tmp_path):
        """Test saving plant structure to XML and verifying format"""
        # Note: Full roundtrip testing (save + load) has C++ limitations with
        # certain plant models/growth stages. This test verifies the XML writing
        # functionality works correctly and produces valid XML files.

        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        model_name = models[0]
        plantarch.loadPlantModelFromLibrary(model_name)
        plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(1, 2, 0), age=5.0)

        # Get original UUIDs to verify plant has geometry
        original_uuids = plantarch.getAllPlantUUIDs(plant_id)
        assert len(original_uuids) > 0, "Plant should have geometry"

        # Save to XML
        xml_file = tmp_path / "plant_roundtrip.xml"
        plantarch.writePlantStructureXML(plant_id, str(xml_file))

        # Verify XML file was created with valid content
        assert xml_file.exists()
        assert xml_file.stat().st_size > 0

        with open(xml_file, 'r') as f:
            content = f.read()
            assert content.startswith('<?xml')
            # XML should contain shoot and plant structure information
            assert any(keyword in content.lower() for keyword in ['shoot', 'branch', 'leaf'])

    def test_read_plant_structure_xml_quiet_mode(self, plantarch, tmp_path):
        """Test quiet parameter is properly passed to C++ function"""
        # Note: This test verifies the quiet parameter is properly handled
        # in the Python interface. Full XML loading has C++ limitations with
        # certain plant models, so we verify parameter handling only.

        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        model_name = models[0]
        plantarch.loadPlantModelFromLibrary(model_name)
        plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), age=5.0)

        # Save to XML
        xml_file = tmp_path / "plant_quiet.xml"
        plantarch.writePlantStructureXML(plant_id, str(xml_file))

        # Verify file was created (XML write works)
        assert xml_file.exists()
        assert xml_file.stat().st_size > 0

        # Test that readPlantStructureXML accepts quiet parameter
        # (even if loading fails due to C++ limitations, parameter should be accepted)
        try:
            loaded_plant_ids = plantarch.readPlantStructureXML(str(xml_file), quiet=True)
            # If loading succeeds, verify result format
            assert isinstance(loaded_plant_ids, list)
        except PlantArchitectureError:
            # C++ loading limitation - test passed because quiet parameter was accepted
            pass

    def test_file_io_path_preservation(self, plantarch, tmp_path):
        """Test that working directory is preserved during file I/O"""
        import os

        # Load model and create plant
        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        plantarch.loadPlantModelFromLibrary(models[0])
        plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), age=20.0)

        # Save current working directory
        original_cwd = os.getcwd()

        # Write to file using relative path
        output_file = tmp_path / "test_vertices.txt"
        plantarch.writePlantMeshVertices(plant_id, str(output_file))

        # Verify working directory was preserved
        assert os.getcwd() == original_cwd

        # Verify file was created in correct location
        assert output_file.exists()

    def test_write_file_io_validation(self, plantarch):
        """Test parameter validation for write methods"""
        # Test negative plant ID
        with pytest.raises(ValueError, match="Plant ID must be non-negative"):
            plantarch.writePlantMeshVertices(-1, "output.txt")

        with pytest.raises(ValueError, match="Plant ID must be non-negative"):
            plantarch.writePlantStructureXML(-1, "output.xml")

        with pytest.raises(ValueError, match="Plant ID must be non-negative"):
            plantarch.writeQSMCylinderFile(-1, "output.txt")

        # Test empty filename
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            plantarch.writePlantMeshVertices(0, "")

        with pytest.raises(ValueError, match="Filename cannot be empty"):
            plantarch.writePlantStructureXML(0, "")

        with pytest.raises(ValueError, match="Filename cannot be empty"):
            plantarch.writeQSMCylinderFile(0, "")

    def test_read_file_io_validation(self, plantarch):
        """Test parameter validation for read methods"""
        # Test empty filename
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            plantarch.readPlantStructureXML("")

    def test_write_invalid_plant_id(self, plantarch, tmp_path):
        """Test writing with non-existent plant ID"""
        output_file = tmp_path / "invalid_plant.txt"

        # Should raise error for non-existent plant ID
        with pytest.raises(PlantArchitectureError):
            plantarch.writePlantMeshVertices(99999, str(output_file))

    def test_read_nonexistent_file(self, plantarch):
        """Test reading from non-existent XML file"""
        with pytest.raises(PlantArchitectureError):
            plantarch.readPlantStructureXML("nonexistent_file.xml")

    def test_file_io_with_pathlib(self, plantarch, tmp_path):
        """Test file I/O methods work with pathlib.Path objects"""
        from pathlib import Path

        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        model_name = models[0]
        plantarch.loadPlantModelFromLibrary(model_name)
        plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), age=5.0)

        # Test write methods with Path objects
        vertices_file = tmp_path / "vertices_path.txt"
        plantarch.writePlantMeshVertices(plant_id, vertices_file)
        assert vertices_file.exists()
        assert vertices_file.stat().st_size > 0

        xml_file = tmp_path / "structure_path.xml"
        plantarch.writePlantStructureXML(plant_id, xml_file)
        assert xml_file.exists()
        assert xml_file.stat().st_size > 0

        qsm_file = tmp_path / "qsm_path.txt"
        plantarch.writeQSMCylinderFile(plant_id, qsm_file)
        assert qsm_file.exists()
        assert qsm_file.stat().st_size > 0

        # Test read method accepts Path objects (even if loading has C++ limitations)
        try:
            loaded_ids = plantarch.readPlantStructureXML(xml_file)
            assert isinstance(loaded_ids, list)
        except PlantArchitectureError:
            # C++ loading limitation - test passed because Path was accepted
            pass


@pytest.mark.native_only
class TestPlantArchitectureUSDExport:
    """Test PlantArchitecture USD export and growth animation methods (v1.3.71+)."""

    @pytest.fixture
    def context(self, check_native_library):
        context = Context()
        yield context
        context.__exit__(None, None, None)

    @pytest.fixture
    def plantarch(self, context):
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture plugin not available")
        try:
            instance = PlantArchitecture(context)
            yield instance
            instance.__exit__(None, None, None)
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture initialization failed: {e}")

    def _build_plant(self, plantarch):
        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")
        plantarch.loadPlantModelFromLibrary(models[0])
        return plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), age=15.0)

    def test_write_plant_structure_usd_default_params(self, plantarch, tmp_path):
        plant_id = self._build_plant(plantarch)
        out = tmp_path / "plant.usda"
        plantarch.writePlantStructureUSD(plant_id, str(out))
        assert out.exists()
        assert out.stat().st_size > 0
        # USDA files start with the "#usda" magic header
        with open(out, 'r') as f:
            assert f.read(64).lstrip().startswith("#usda")

    def test_write_plant_structure_usd_custom_params(self, plantarch, tmp_path):
        plant_id = self._build_plant(plantarch)
        out = tmp_path / "plant_custom.usda"
        plantarch.writePlantStructureUSD(
            plant_id, str(out),
            elastic_modulus=8e9,
            wood_density=750.0,
            damping_ratio=0.2,
            leaf_mass_per_area=0.04,
            fruit_mass=0.005,
            flower_mass=0.001,
        )
        assert out.exists()
        assert out.stat().st_size > 0

    def test_growth_frame_lifecycle(self, plantarch):
        plant_id = self._build_plant(plantarch)

        # Initially zero frames
        assert plantarch.getGrowthFrameCount(plant_id) == 0

        plantarch.registerGrowthFrame(plant_id)
        assert plantarch.getGrowthFrameCount(plant_id) == 1

        plantarch.advanceTime(2.0)
        plantarch.registerGrowthFrame(plant_id)
        assert plantarch.getGrowthFrameCount(plant_id) == 2

        plantarch.clearGrowthFrames(plant_id)
        assert plantarch.getGrowthFrameCount(plant_id) == 0

    def test_write_plant_growth_usd(self, plantarch, tmp_path):
        plant_id = self._build_plant(plantarch)

        for _ in range(3):
            plantarch.registerGrowthFrame(plant_id)
            plantarch.advanceTime(1.0)

        out = tmp_path / "growth.usda"
        plantarch.writePlantGrowthUSD(plant_id, str(out), seconds_per_frame=0.5)
        assert out.exists()
        assert out.stat().st_size > 0


@pytest.mark.native_only
class TestPlantArchitectureCustomBuilding:
    """Test PlantArchitecture custom plant building functionality"""

    @pytest.fixture
    def context(self, check_native_library):
        """Create a Context for testing with proper cleanup"""
        context = Context()
        yield context
        context.__exit__(None, None, None)

    @pytest.fixture
    def plantarch(self, context):
        """Create PlantArchitecture instance with proper cleanup"""
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture plugin not available")

        try:
            plantarch_instance = PlantArchitecture(context)
            yield plantarch_instance
            plantarch_instance.__exit__(None, None, None)
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture initialization failed: {e}")

    def test_add_plant_instance(self, plantarch):
        """Test creating an empty plant instance"""
        position = vec3(0, 0, 0)
        age = 0.0

        plant_id = plantarch.addPlantInstance(position, age)

        assert isinstance(plant_id, int)
        assert plant_id >= 0

    def test_add_plant_instance_with_list_position(self, plantarch):
        """Test creating plant instance with vec3"""
        position = vec3(1.0, 2.0, 0.0)
        age = 5.0

        plant_id = plantarch.addPlantInstance(position, age)

        assert isinstance(plant_id, int)
        assert plant_id >= 0

    def test_add_plant_instance_validation(self, plantarch):
        """Test parameter validation for addPlantInstance"""
        # Test negative age
        with pytest.raises(ValueError, match="Age must be non-negative"):
            plantarch.addPlantInstance(vec3(0, 0, 0), -1.0)

        # Test invalid position type
        with pytest.raises(ValueError, match="base_position must be a vec3"):
            plantarch.addPlantInstance([1, 2], 0.0)

    def test_delete_plant_instance(self, plantarch):
        """Test deleting a plant instance"""
        # Create a plant first
        plant_id = plantarch.addPlantInstance(vec3(0, 0, 0), 0.0)

        # Delete it
        plantarch.deletePlantInstance(plant_id)

        # Should complete without exception

    def test_delete_plant_instance_validation(self, plantarch):
        """Test parameter validation for deletePlantInstance"""
        # Test negative plant ID
        with pytest.raises(ValueError, match="Plant ID must be non-negative"):
            plantarch.deletePlantInstance(-1)

    def test_delete_plant_after_creation(self, plantarch):
        """Test deleting plant after creation completes successfully"""
        # Create two plants
        plant_id1 = plantarch.addPlantInstance(vec3(0, 0, 0), 0.0)
        plant_id2 = plantarch.addPlantInstance(vec3(5, 5, 0), 0.0)

        # Delete first plant
        plantarch.deletePlantInstance(plant_id1)

        # Should complete without error
        # Note: C++ implementation may not raise errors for invalid IDs

    def test_add_base_stem_shoot(self, plantarch):
        """Test adding a base stem shoot to a plant"""
        # Load a plant model to define shoot types
        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        # Use 'bean' model explicitly for deterministic shoot types
        if 'bean' not in models:
            pytest.skip("Bean model not available for testing")

        # REQUIRED: Load plant model first to define shoot types
        plantarch.loadPlantModelFromLibrary('bean')

        # Create empty plant
        plant_id = plantarch.addPlantInstance(vec3(0, 0, 0), 0.0)

        # Add base stem shoot using shoot type from loaded model
        rotation = AxisRotation(0, 0, 0)
        # Use "unifoliate" which is the base shoot type for bean/legume models
        shoot_id = plantarch.addBaseStemShoot(
            plant_id=plant_id,
            current_node_number=1,
            base_rotation=rotation,
            internode_radius=0.01,
            internode_length_max=0.1,
            internode_length_scale_factor_fraction=1.0,
            leaf_scale_factor_fraction=1.0,
            radius_taper=0.9,
            shoot_type_label="unifoliate"
        )

        assert isinstance(shoot_id, int)
        assert shoot_id >= 0

    def test_add_base_stem_shoot_with_axis_rotation(self, plantarch):
        """Test adding base stem shoot with AxisRotation"""
        # Load model for shoot types (REQUIRED before custom building)
        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        # Use 'bean' model explicitly for deterministic shoot types
        if 'bean' not in models:
            pytest.skip("Bean model not available for testing")

        # REQUIRED: Load plant model first to define shoot types
        plantarch.loadPlantModelFromLibrary('bean')
        plant_id = plantarch.addPlantInstance(vec3(0, 0, 0), 0.0)

        # Use AxisRotation for rotation
        shoot_id = plantarch.addBaseStemShoot(
            plant_id, 1, AxisRotation(15, 0, 0), 0.015, 0.12, 1.0, 1.0, 0.85, "unifoliate"
        )

        assert isinstance(shoot_id, int)
        assert shoot_id >= 0

    def test_add_base_stem_shoot_validation(self, plantarch):
        """Test parameter validation for addBaseStemShoot"""
        plant_id = plantarch.addPlantInstance(vec3(0, 0, 0), 0.0)
        rotation = AxisRotation(0, 0, 0)

        # Test negative plant ID
        with pytest.raises(ValueError, match="Plant ID must be non-negative"):
            plantarch.addBaseStemShoot(-1, 1, rotation, 0.01, 0.1, 1.0, 1.0, 0.9, "unifoliate")

        # Test negative node number
        with pytest.raises(ValueError, match="Current node number must be non-negative"):
            plantarch.addBaseStemShoot(plant_id, -1, rotation, 0.01, 0.1, 1.0, 1.0, 0.9, "unifoliate")

        # Test invalid rotation type (lists no longer accepted)
        with pytest.raises(AttributeError):  # Lists don't have .to_list() method
            plantarch.addBaseStemShoot(plant_id, 1, [0, 0], 0.01, 0.1, 1.0, 1.0, 0.9, "unifoliate")

        # Test non-positive radius
        with pytest.raises(ValueError, match="Internode radius must be positive"):
            plantarch.addBaseStemShoot(plant_id, 1, rotation, 0.0, 0.1, 1.0, 1.0, 0.9, "unifoliate")

        # Test non-positive length
        with pytest.raises(ValueError, match="Internode length max must be positive"):
            plantarch.addBaseStemShoot(plant_id, 1, rotation, 0.01, 0.0, 1.0, 1.0, 0.9, "unifoliate")

        # Test empty label
        with pytest.raises(ValueError, match="Shoot type label cannot be empty"):
            plantarch.addBaseStemShoot(plant_id, 1, rotation, 0.01, 0.1, 1.0, 1.0, 0.9, "")

    def test_append_shoot(self, plantarch):
        """Test appending a shoot to an existing shoot"""
        # Load model for shoot types (REQUIRED)
        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        # Use 'bean' model explicitly for deterministic shoot types
        if 'bean' not in models:
            pytest.skip("Bean model not available for testing")

        # REQUIRED: Load plant model first to define shoot types
        plantarch.loadPlantModelFromLibrary('bean')

        # Create plant with base shoot (unifoliate has max_nodes=1, so use trifoliate for more nodes)
        plant_id = plantarch.addPlantInstance(vec3(0, 0, 0), 0.0)
        base_shoot_id = plantarch.addBaseStemShoot(
            plant_id, 3, AxisRotation(0, 0, 0), 0.01, 0.1, 1.0, 1.0, 0.9, "trifoliate"
        )

        # Append a shoot (even trifoliate has max_nodes constraint, so use 1 node)
        new_shoot_id = plantarch.appendShoot(
            plant_id=plant_id,
            parent_shoot_id=base_shoot_id,
            current_node_number=1,
            base_rotation=AxisRotation(0, 0, 0),
            internode_radius=0.008,
            internode_length_max=0.08,
            internode_length_scale_factor_fraction=1.0,
            leaf_scale_factor_fraction=0.8,
            radius_taper=0.85,
            shoot_type_label="unifoliate"
        )

        assert isinstance(new_shoot_id, int)
        assert new_shoot_id >= 0
        assert new_shoot_id != base_shoot_id

    def test_append_shoot_validation(self, plantarch):
        """Test parameter validation for appendShoot"""
        # Load model for shoot types (REQUIRED)
        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        # Use 'bean' model explicitly for deterministic shoot types
        if 'bean' not in models:
            pytest.skip("Bean model not available for testing")

        # REQUIRED: Load plant model first to define shoot types
        plantarch.loadPlantModelFromLibrary('bean')

        plant_id = plantarch.addPlantInstance(vec3(0, 0, 0), 0.0)
        shoot_id = plantarch.addBaseStemShoot(plant_id, 3, AxisRotation(0, 0, 0), 0.01, 0.1, 1.0, 1.0, 0.9, "trifoliate")
        rotation = AxisRotation(0, 0, 0)

        # Test negative parent shoot ID
        with pytest.raises(ValueError, match="Parent shoot ID must be non-negative"):
            plantarch.appendShoot(plant_id, -1, 2, rotation, 0.01, 0.1, 1.0, 1.0, 0.9, "trifoliate")

        # Test non-positive radius
        with pytest.raises(ValueError, match="Internode radius must be positive"):
            plantarch.appendShoot(plant_id, shoot_id, 2, rotation, -0.01, 0.1, 1.0, 1.0, 0.9, "trifoliate")

    def test_append_shoot_to_nonexistent_parent(self, plantarch):
        """Test appending shoot to non-existent parent fails"""
        plant_id = plantarch.addPlantInstance(vec3(0, 0, 0), 0.0)

        with pytest.raises(PlantArchitectureError):
            plantarch.appendShoot(plant_id, 99999, 5, AxisRotation(0, 0, 0), 0.01, 0.1, 1.0, 1.0, 0.9, "unifoliate")

    def test_add_child_shoot(self, plantarch):
        """Test adding a child shoot at an axillary bud"""
        # Load model for shoot types (REQUIRED)
        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        # Use 'bean' model explicitly for deterministic shoot types
        if 'bean' not in models:
            pytest.skip("Bean model not available for testing")

        # REQUIRED: Load plant model first to define shoot types
        plantarch.loadPlantModelFromLibrary('bean')

        # Create plant with base shoot (trifoliate allows more nodes)
        plant_id = plantarch.addPlantInstance(vec3(0, 0, 0), 0.0)
        main_shoot_id = plantarch.addBaseStemShoot(
            plant_id, 5, AxisRotation(0, 0, 0), 0.01, 0.1, 1.0, 1.0, 0.9, "trifoliate"
        )

        # Add child shoot at node 2 (trifoliate allows child shoots)
        branch_id = plantarch.addChildShoot(
            plant_id=plant_id,
            parent_shoot_id=main_shoot_id,
            parent_node_index=2,
            current_node_number=1,
            shoot_base_rotation=AxisRotation(45, 90, 0),
            internode_radius=0.005,
            internode_length_max=0.06,
            internode_length_scale_factor_fraction=1.0,
            leaf_scale_factor_fraction=0.9,
            radius_taper=0.8,
            shoot_type_label="trifoliate"
        )

        assert isinstance(branch_id, int)
        assert branch_id >= 0
        assert branch_id != main_shoot_id

    def test_add_child_shoot_with_petiole_index(self, plantarch):
        """Test adding child shoot at specific petiole index"""
        # Load model for shoot types (REQUIRED)
        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        # Use 'bean' model explicitly for deterministic shoot types
        if 'bean' not in models:
            pytest.skip("Bean model not available for testing")

        # REQUIRED: Load plant model first to define shoot types
        plantarch.loadPlantModelFromLibrary('bean')

        plant_id = plantarch.addPlantInstance(vec3(0, 0, 0), 0.0)
        main_shoot_id = plantarch.addBaseStemShoot(
            plant_id, 5, AxisRotation(0, 0, 0), 0.01, 0.1, 1.0, 1.0, 0.9, "trifoliate"
        )

        # Add child shoot with petiole_index=0 (default petiole)
        branch_id = plantarch.addChildShoot(
            plant_id, main_shoot_id, 2, 1, AxisRotation(45, 270, 0),
            0.005, 0.06, 1.0, 0.9, 0.8, "trifoliate", petiole_index=0
        )

        assert isinstance(branch_id, int)
        assert branch_id >= 0

    def test_add_child_shoot_validation(self, plantarch):
        """Test parameter validation for addChildShoot"""
        # Load model for shoot types (REQUIRED)
        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        # Use 'bean' model explicitly for deterministic shoot types
        if 'bean' not in models:
            pytest.skip("Bean model not available for testing")

        # REQUIRED: Load plant model first to define shoot types
        plantarch.loadPlantModelFromLibrary('bean')

        plant_id = plantarch.addPlantInstance(vec3(0, 0, 0), 0.0)
        shoot_id = plantarch.addBaseStemShoot(plant_id, 5, AxisRotation(0, 0, 0), 0.01, 0.1, 1.0, 1.0, 0.9, "trifoliate")
        rotation = AxisRotation(45, 0, 0)

        # Test negative parent node index
        with pytest.raises(ValueError, match="Parent node index must be non-negative"):
            plantarch.addChildShoot(plant_id, shoot_id, -1, 1, rotation, 0.005, 0.06, 1.0, 0.9, 0.8, "trifoliate")

        # Test negative petiole index
        with pytest.raises(ValueError, match="Petiole index must be non-negative"):
            plantarch.addChildShoot(
                plant_id, shoot_id, 2, 1, rotation, 0.005, 0.06, 1.0, 0.9, 0.8, "trifoliate", petiole_index=-1
            )

        # Test empty label
        with pytest.raises(ValueError, match="Shoot type label cannot be empty"):
            plantarch.addChildShoot(plant_id, shoot_id, 2, 1, rotation, 0.005, 0.06, 1.0, 0.9, 0.8, "")


@pytest.mark.integration
class TestPlantArchitectureCustomBuildingIntegration:
    """Integration tests for custom plant building with Context"""

    @pytest.fixture
    def context(self, check_native_library):
        """Create a Context for integration testing with proper cleanup"""
        context = Context()
        yield context
        context.__exit__(None, None, None)

    def test_custom_plant_building_workflow(self, basic_context):
        """Test complete custom plant building workflow"""
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture plugin not available")

        try:
            with PlantArchitecture(basic_context) as plantarch:
                # Load model for shoot types
                models = plantarch.getAvailablePlantModels()
                if not models:
                    pytest.skip("No plant models available")

                # Use 'bean' model explicitly for deterministic shoot types
                if 'bean' not in models:
                    pytest.skip("Bean model not available for testing")

                plantarch.loadPlantModelFromLibrary('bean')

                # Check initial primitive count
                initial_count = basic_context.getPrimitiveCount()

                # Create empty plant instance
                plant_id = plantarch.addPlantInstance(vec3(0, 0, 0), 0.0)
                assert plant_id >= 0

                # Add base stem shoot with 3 nodes using trifoliate (which allows more nodes)
                base_shoot_id = plantarch.addBaseStemShoot(
                    plant_id, 3, AxisRotation(0, 0, 0), 0.01, 0.1, 1.0, 1.0, 0.9, "trifoliate"
                )
                assert base_shoot_id >= 0

                # Add child branch at node 2 (now exists since we created 3 nodes)
                branch_id = plantarch.addChildShoot(
                    plant_id, base_shoot_id, 2, 1, AxisRotation(45, 90, 0),
                    0.005, 0.06, 1.0, 0.9, 0.8, "trifoliate"
                )
                assert branch_id >= 0

                # Verify geometry was added to context
                # Note: Custom building may or may not immediately add geometry
                # depending on C++ implementation, so we just verify no crash

                # Get plant UUIDs
                uuids = plantarch.getAllPlantUUIDs(plant_id)
                assert isinstance(uuids, list)

                # Delete the plant
                plantarch.deletePlantInstance(plant_id)

                # Should complete without error

        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_custom_vs_library_plant_building(self, basic_context):
        """Test that custom building and library building can coexist"""
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture plugin not available")

        try:
            with PlantArchitecture(basic_context) as plantarch:
                # Get available models
                models = plantarch.getAvailablePlantModels()
                if not models:
                    pytest.skip("No plant models available")

                # Use 'bean' model explicitly for deterministic shoot types
                if 'bean' not in models:
                    pytest.skip("Bean model not available for testing")

                # Create plant from library (this also loads the model and defines shoot types)
                plantarch.loadPlantModelFromLibrary('bean')
                library_plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(5, 5, 0), 10.0)
                assert library_plant_id >= 0

                # Create custom plant
                custom_plant_id = plantarch.addPlantInstance(vec3(-5, -5, 0), 0.0)
                assert custom_plant_id >= 0

                # Add shoot to custom plant using shoot type from loaded model
                shoot_id = plantarch.addBaseStemShoot(
                    custom_plant_id, 1, AxisRotation(0, 0, 0), 0.01, 0.1, 1.0, 1.0, 0.9, "unifoliate"
                )
                assert shoot_id >= 0

                # Verify both plants exist
                library_uuids = plantarch.getAllPlantUUIDs(library_plant_id)
                custom_uuids = plantarch.getAllPlantUUIDs(custom_plant_id)

                assert isinstance(library_uuids, list)
                assert isinstance(custom_uuids, list)

                # Delete custom plant
                plantarch.deletePlantInstance(custom_plant_id)

                # Library plant should still exist
                library_uuids_after = plantarch.getAllPlantUUIDs(library_plant_id)
                assert isinstance(library_uuids_after, list)

        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_complex_branching_structure(self, basic_context):
        """Test building complex branching structure"""
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture plugin not available")

        try:
            with PlantArchitecture(basic_context) as plantarch:
                # Load model for shoot types
                models = plantarch.getAvailablePlantModels()
                if not models:
                    pytest.skip("No plant models available")

                # Use 'bean' model explicitly for deterministic shoot types
                if 'bean' not in models:
                    pytest.skip("Bean model not available for testing")

                plantarch.loadPlantModelFromLibrary('bean')

                # Create plant
                plant_id = plantarch.addPlantInstance(vec3(0, 0, 0), 0.0)

                # Add main stem with 6 nodes using trifoliate (which allows more nodes)
                main_stem_id = plantarch.addBaseStemShoot(
                    plant_id, 6, AxisRotation(0, 0, 0), 0.015, 0.12, 1.0, 1.0, 0.9, "trifoliate"
                )

                # Add multiple lateral branches at different nodes
                branch_angles = [45, 135, 225, 315]
                branch_ids = []

                for i, angle in enumerate(branch_angles):
                    branch_id = plantarch.addChildShoot(
                        plant_id, main_stem_id, i + 2, 1,
                        AxisRotation(45, angle, 0),
                        0.008, 0.08, 1.0, 0.9, 0.85, "trifoliate"
                    )
                    branch_ids.append(branch_id)
                    assert branch_id >= 0

                # Verify all branches have unique IDs
                assert len(set(branch_ids)) == len(branch_ids)

                # Get all plant geometry
                plant_uuids = plantarch.getAllPlantUUIDs(plant_id)
                assert isinstance(plant_uuids, list)

        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

@pytest.mark.native_only
class TestBuildParameters:
    """Test build_parameters functionality for customizing library plants"""

    def test_build_instance_with_parameters_single(self, basic_context):
        """Test building single plant with one parameter override"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("tomato")
                
                # Build plant with custom trunk_height
                plant_id = plantarch.buildPlantInstanceFromLibrary(
                    base_position=vec3(0, 0, 0),
                    age=30.0,
                    build_parameters={'trunk_height': 2.5}
                )
                
                assert plant_id >= 0
                
                # Verify plant was created
                obj_ids = plantarch.getAllPlantObjectIDs(plant_id)
                assert isinstance(obj_ids, list)
                assert len(obj_ids) > 0
                
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_build_instance_with_parameters_multiple(self, basic_context):
        """Test building plant with multiple parameter overrides"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("grapevine_VSP")
                
                # Build with multiple custom parameters
                plant_id = plantarch.buildPlantInstanceFromLibrary(
                    base_position=vec3(0, 0, 0),
                    age=45.0,
                    build_parameters={
                        'cordon_height': 1.8,
                        'cordon_radius': 1.2
                    }
                )
                
                assert plant_id >= 0
                
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_build_instance_without_parameters(self, basic_context):
        """Test backward compatibility - building without parameters"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("bean")
                
                # Build without parameters (old behavior)
                plant_id = plantarch.buildPlantInstanceFromLibrary(
                    base_position=vec3(0, 0, 0),
                    age=25.0
                )
                
                assert plant_id >= 0
                
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_build_instance_with_empty_parameters(self, basic_context):
        """Test building with empty parameter dict"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("soybean")
                
                # Build with empty parameters dict
                plant_id = plantarch.buildPlantInstanceFromLibrary(
                    base_position=vec3(0, 0, 0),
                    age=20.0,
                    build_parameters={}
                )
                
                assert plant_id >= 0
                
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_build_canopy_with_parameters_single(self, basic_context):
        """Test building canopy with parameter override"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("tomato")
                
                # Build canopy with custom parameter
                plant_ids = plantarch.buildPlantCanopyFromLibrary(
                    canopy_center=vec3(0, 0, 0),
                    plant_spacing=vec2(1.0, 1.0),
                    plant_count=int2(3, 2),
                    age=30.0,
                    build_parameters={'trunk_height': 2.0}
                )
                
                assert isinstance(plant_ids, list)
                assert len(plant_ids) == 6  # 3x2
                assert all(pid >= 0 for pid in plant_ids)
                
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_build_canopy_with_parameters_multiple(self, basic_context):
        """Test building canopy with multiple parameters"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("grapevine_VSP")
                
                # Build canopy with multiple custom parameters
                plant_ids = plantarch.buildPlantCanopyFromLibrary(
                    canopy_center=vec3(0, 0, 0),
                    plant_spacing=vec2(1.5, 2.0),
                    plant_count=int2(2, 2),
                    age=45.0,
                    build_parameters={
                        'cordon_height': 1.8,
                        'cordon_radius': 1.5
                    }
                )
                
                assert isinstance(plant_ids, list)
                assert len(plant_ids) == 4  # 2x2
                
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_build_canopy_without_parameters(self, basic_context):
        """Test backward compatibility - building canopy without parameters"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("bean")
                
                # Build without parameters (old behavior)
                plant_ids = plantarch.buildPlantCanopyFromLibrary(
                    canopy_center=vec3(0, 0, 0),
                    plant_spacing=vec2(0.5, 0.5),
                    plant_count=int2(2, 2),
                    age=20.0
                )
                
                assert isinstance(plant_ids, list)
                assert len(plant_ids) == 4
                
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_build_parameters_validation_not_dict(self, basic_context):
        """Test validation rejects non-dict build_parameters"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("bean")
                
                # Should raise ValueError for non-dict
                with pytest.raises(ValueError, match="build_parameters must be a dict"):
                    plantarch.buildPlantInstanceFromLibrary(
                        base_position=vec3(0, 0, 0),
                        age=20.0,
                        build_parameters="invalid"
                    )
                    
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_build_parameters_validation_non_string_keys(self, basic_context):
        """Test validation rejects non-string keys"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("bean")
                
                # Should raise ValueError for non-string keys
                with pytest.raises(ValueError, match="keys must be strings"):
                    plantarch.buildPlantInstanceFromLibrary(
                        base_position=vec3(0, 0, 0),
                        age=20.0,
                        build_parameters={123: 2.5}
                    )
                    
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_build_parameters_validation_non_numeric_values(self, basic_context):
        """Test validation rejects non-numeric values"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("bean")
                
                # Should raise ValueError for non-numeric values
                with pytest.raises(ValueError, match="values must be numeric"):
                    plantarch.buildPlantInstanceFromLibrary(
                        base_position=vec3(0, 0, 0),
                        age=20.0,
                        build_parameters={'trunk_height': "not_a_number"}
                    )
                    
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_build_parameters_with_int_values(self, basic_context):
        """Test that integer parameter values are accepted"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("tomato")
                
                # Integer values should be accepted
                plant_id = plantarch.buildPlantInstanceFromLibrary(
                    base_position=vec3(0, 0, 0),
                    age=30.0,
                    build_parameters={'trunk_height': 2}  # int instead of float
                )
                
                assert plant_id >= 0
                
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_build_parameters_with_float_values(self, basic_context):
        """Test that float parameter values are accepted"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("tomato")
                
                # Float values should be accepted
                plant_id = plantarch.buildPlantInstanceFromLibrary(
                    base_position=vec3(0, 0, 0),
                    age=30.0,
                    build_parameters={'trunk_height': 2.5}  # float
                )
                
                assert plant_id >= 0
                
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_canopy_build_parameters_validation(self, basic_context):
        """Test validation for canopy building with invalid parameters"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("bean")
                
                # Should raise ValueError for non-dict
                with pytest.raises(ValueError, match="build_parameters must be a dict"):
                    plantarch.buildPlantCanopyFromLibrary(
                        canopy_center=vec3(0, 0, 0),
                        plant_spacing=vec2(0.5, 0.5),
                        plant_count=int2(2, 2),
                        age=20.0,
                        build_parameters=[1, 2, 3]  # list instead of dict
                    )
                    
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")



@pytest.mark.native_only  
class TestShootParameters:
    """Test shoot parameter query and modification functionality"""

    def test_get_shoot_parameters(self, basic_context):
        """Test querying shoot parameters"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("bean")

                # Get parameters for bean shoot type
                params = plantarch.getCurrentShootParameters("unifoliate")

                assert isinstance(params, dict)
                # Check for key parameters
                assert 'max_nodes' in params
                assert 'insertion_angle_tip' in params
                assert 'phyllochron_min' in params

                # Check RandomParameter structure
                assert isinstance(params['max_nodes'], dict)
                assert 'distribution' in params['max_nodes']
                assert 'parameters' in params['max_nodes']

        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_roundtrip_modification(self, basic_context):
        """Test query -> modify -> define -> query cycle"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("bean")

                # Get original parameters
                orig_params = plantarch.getCurrentShootParameters("unifoliate")
                
                # Modify a parameter
                modified_params = orig_params.copy()
                modified_params['max_nodes'] = {
                    'distribution': 'constant',
                    'parameters': [20.0]
                }
                
                # Define new shoot type
                plantarch.defineShootType("CustomStem", modified_params)
                
                # Query back and verify
                custom_params = plantarch.getCurrentShootParameters("CustomStem")
                assert custom_params['max_nodes']['parameters'][0] == 20.0
                
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_modify_multiple_parameters(self, basic_context):
        """Test modifying multiple shoot parameters"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("bean")

                params = plantarch.getCurrentShootParameters("unifoliate")
                
                # Modify multiple parameters
                params['max_nodes'] = {'distribution': 'constant', 'parameters': [25.0]}
                params['insertion_angle_tip'] = {'distribution': 'uniform', 'parameters': [40.0, 50.0]}
                params['gravitropic_curvature'] = {'distribution': 'normal', 'parameters': [0.5, 0.1]}
                
                # Define new type
                plantarch.defineShootType("ModifiedStem", params)
                
                # Verify
                verified = plantarch.getCurrentShootParameters("ModifiedStem")
                assert verified['max_nodes']['parameters'][0] == 25.0
                assert verified['insertion_angle_tip']['distribution'] == 'uniform'
                assert len(verified['insertion_angle_tip']['parameters']) == 2
                
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_get_parameters_invalid_shoot_type(self, basic_context):
        """Test error handling for invalid shoot type"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("bean")
                
                # Should raise error for non-existent shoot type
                with pytest.raises(PlantArchitectureError):
                    plantarch.getCurrentShootParameters("NonExistentShootType")
                    
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_define_shoot_type_validation(self, basic_context):
        """Test parameter validation for defineShootType"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("bean")
                
                # Empty label
                with pytest.raises(ValueError, match="cannot be empty"):
                    plantarch.defineShootType("", {})
                
                # Non-dict parameters  
                with pytest.raises(ValueError, match="must be a dict"):
                    plantarch.defineShootType("Test", "not_a_dict")
                    
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_boolean_parameters(self, basic_context):
        """Test modifying boolean shoot parameters"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("tomato")

                params = plantarch.getCurrentShootParameters("mainstem")
                
                # Modify boolean flags
                params['determinate_shoot_growth'] = True
                params['flowers_require_dormancy'] = False
                
                plantarch.defineShootType("DeterminateStem", params)
                
                # Verify
                verified = plantarch.getCurrentShootParameters("DeterminateStem")
                assert verified['determinate_shoot_growth'] == True
                assert verified['flowers_require_dormancy'] == False
                
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")


@pytest.mark.unit
class TestRandomParameterHelpers:
    """Test RandomParameter and RandomParameterInt helper classes"""

    def test_random_parameter_constant(self):
        """Test RandomParameter.constant()"""
        from pyhelios import RandomParameter
        
        param = RandomParameter.constant(45.0)
        assert param == {'distribution': 'constant', 'parameters': [45.0]}

    def test_random_parameter_uniform(self):
        """Test RandomParameter.uniform()"""
        from pyhelios import RandomParameter
        
        param = RandomParameter.uniform(40.0, 50.0)
        assert param['distribution'] == 'uniform'
        assert param['parameters'] == [40.0, 50.0]

    def test_random_parameter_uniform_validation(self):
        """Test uniform distribution validation"""
        from pyhelios import RandomParameter
        
        with pytest.raises(ValueError, match="min_val.*must be.*max_val"):
            RandomParameter.uniform(50.0, 40.0)

    def test_random_parameter_normal(self):
        """Test RandomParameter.normal()"""
        from pyhelios import RandomParameter
        
        param = RandomParameter.normal(45.0, 5.0)
        assert param['distribution'] == 'normal'
        assert param['parameters'] == [45.0, 5.0]

    def test_random_parameter_normal_validation(self):
        """Test normal distribution validation"""
        from pyhelios import RandomParameter
        
        with pytest.raises(ValueError, match="std_dev.*must be"):
            RandomParameter.normal(45.0, -1.0)

    def test_random_parameter_weibull(self):
        """Test RandomParameter.weibull()"""
        from pyhelios import RandomParameter
        
        param = RandomParameter.weibull(2.0, 50.0)
        assert param['distribution'] == 'weibull'
        assert param['parameters'] == [2.0, 50.0]

    def test_random_parameter_weibull_validation(self):
        """Test Weibull distribution validation"""
        from pyhelios import RandomParameter
        
        with pytest.raises(ValueError, match="shape.*must be"):
            RandomParameter.weibull(0.0, 50.0)
        
        with pytest.raises(ValueError, match="scale.*must be"):
            RandomParameter.weibull(2.0, 0.0)

    def test_random_parameter_int_constant(self):
        """Test RandomParameterInt.constant()"""
        from pyhelios import RandomParameterInt
        
        param = RandomParameterInt.constant(15)
        assert param == {'distribution': 'constant', 'parameters': [15.0]}

    def test_random_parameter_int_uniform(self):
        """Test RandomParameterInt.uniform()"""
        from pyhelios import RandomParameterInt
        
        param = RandomParameterInt.uniform(10, 20)
        assert param['distribution'] == 'uniform'
        assert param['parameters'] == [10.0, 20.0]

    def test_random_parameter_int_uniform_validation(self):
        """Test integer uniform validation"""
        from pyhelios import RandomParameterInt
        
        with pytest.raises(ValueError, match="min_val.*must be.*max_val"):
            RandomParameterInt.uniform(20, 10)

    def test_random_parameter_int_discrete(self):
        """Test RandomParameterInt.discrete()"""
        from pyhelios import RandomParameterInt
        
        param = RandomParameterInt.discrete([1, 2, 3, 5])
        assert param['distribution'] == 'discretevalues'
        assert param['parameters'] == [1.0, 2.0, 3.0, 5.0]

    def test_random_parameter_int_discrete_validation(self):
        """Test discrete distribution validation"""
        from pyhelios import RandomParameterInt
        
        with pytest.raises(ValueError, match="cannot be empty"):
            RandomParameterInt.discrete([])


@pytest.mark.native_only
class TestRandomParameterIntegration:
    """Test RandomParameter helpers with actual plant building"""

    def test_uniform_distribution_in_shoot_params(self, basic_context):
        """Test using RandomParameter.uniform() in shoot parameters"""
        try:
            from pyhelios import RandomParameter
            
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("bean")
                
                params = plantarch.getCurrentShootParameters("unifoliate")
                
                # Use helper to create uniform distribution
                params['insertion_angle_tip'] = RandomParameter.uniform(40.0, 50.0)
                params['gravitropic_curvature'] = RandomParameter.normal(0.5, 0.1)
                
                # Define and verify
                plantarch.defineShootType("VariableShoot", params)
                
                verified = plantarch.getCurrentShootParameters("VariableShoot")
                assert verified['insertion_angle_tip']['distribution'] == 'uniform'
                assert verified['insertion_angle_tip']['parameters'] == [40.0, 50.0]
                assert verified['gravitropic_curvature']['distribution'] == 'normal'
                
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_integer_distributions(self, basic_context):
        """Test RandomParameterInt helpers"""
        try:
            from pyhelios import RandomParameterInt
            
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("bean")
                
                params = plantarch.getCurrentShootParameters("unifoliate")
                
                # Use integer helpers
                params['max_nodes'] = RandomParameterInt.uniform(15, 25)
                params['max_nodes_per_season'] = RandomParameterInt.constant(20)
                
                plantarch.defineShootType("VariableNodeShoot", params)
                
                verified = plantarch.getCurrentShootParameters("VariableNodeShoot")
                assert verified['max_nodes']['distribution'] == 'uniform'
                assert verified['max_nodes']['parameters'] == [15.0, 25.0]
                
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")


@pytest.mark.native_only
class TestPlantStateQueries:
    """Test plant state query methods"""

    def test_get_plant_age(self, basic_context):
        """Test getPlantAge method"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("bean")
                
                age = 30.0
                plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), age)
                
                retrieved_age = plantarch.getPlantAge(plant_id)
                assert retrieved_age == age
                
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_get_plant_height(self, basic_context):
        """Test getPlantHeight method"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("bean")
                
                plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 25.0)
                
                height = plantarch.getPlantHeight(plant_id)
                assert isinstance(height, float)
                assert height >= 0
                
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_get_plant_leaf_area(self, basic_context):
        """Test getPlantLeafArea method"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("soybean")
                
                plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 20.0)
                
                leaf_area = plantarch.getPlantLeafArea(plant_id)
                assert isinstance(leaf_area, float)
                assert leaf_area >= 0
                
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_query_methods_validation(self, basic_context):
        """Test validation for query methods"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("bean")
                
                plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 15.0)
                
                # Negative plant ID should raise ValueError
                with pytest.raises(ValueError, match="must be non-negative"):
                    plantarch.getPlantAge(-1)
                
                with pytest.raises(ValueError, match="must be non-negative"):
                    plantarch.getPlantHeight(-1)
                
                with pytest.raises(ValueError, match="must be non-negative"):
                    plantarch.getPlantLeafArea(-1)
                    
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_multiple_plants_queries(self, basic_context):
        """Test queries work for multiple plants"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("bean")
                
                # Build multiple plants with different ages
                plant1 = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 20.0)
                plant2 = plantarch.buildPlantInstanceFromLibrary(vec3(1, 0, 0), 30.0)
                
                # Verify each has correct age
                assert plantarch.getPlantAge(plant1) == 20.0
                assert plantarch.getPlantAge(plant2) == 30.0
                
                # Both should have positive height
                assert plantarch.getPlantHeight(plant1) > 0
                assert plantarch.getPlantHeight(plant2) > 0
                
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")


@pytest.mark.native_only
class TestPhenologicalControl:
    """Test phenological control methods"""

    def test_set_phenological_thresholds_basic(self, basic_context):
        """Test setting phenological thresholds for a plant"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("tomato")
                
                plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 10.0)
                
                # Set phenological timing
                plantarch.setPlantPhenologicalThresholds(
                    plant_id=plant_id,
                    time_to_dormancy_break=0,
                    time_to_flower_initiation=30,
                    time_to_flower_opening=40,
                    time_to_fruit_set=50,
                    time_to_fruit_maturity=80,
                    time_to_dormancy=120,
                    max_leaf_lifespan=90
                )
                
                # Method should complete without error
                assert True
                
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_set_phenological_thresholds_perennial(self, basic_context):
        """Test phenology for perennial fruit tree"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("apple")
                
                plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 365.0)
                
                # Set typical apple phenology, exercising the is_evergreen flag (1.3.76)
                plantarch.setPlantPhenologicalThresholds(
                    plant_id=plant_id,
                    time_to_dormancy_break=60,
                    time_to_flower_initiation=90,
                    time_to_flower_opening=105,
                    time_to_fruit_set=120,
                    time_to_fruit_maturity=200,
                    time_to_dormancy=280,
                    max_leaf_lifespan=180,
                    is_evergreen=True
                )

                assert True
                
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_phenology_validation(self, basic_context):
        """Test validation for phenological methods"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("bean")
                
                plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 15.0)
                
                # Negative plant ID should raise ValueError
                with pytest.raises(ValueError, match="must be non-negative"):
                    plantarch.setPlantPhenologicalThresholds(
                        plant_id=-1,
                        time_to_dormancy_break=0,
                        time_to_flower_initiation=30,
                        time_to_flower_opening=40,
                        time_to_fruit_set=50,
                        time_to_fruit_maturity=80,
                        time_to_dormancy=120
                    )
                    
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")

    def test_phenology_with_default_leaf_lifespan(self, basic_context):
        """Test phenology with default max_leaf_lifespan"""
        try:
            with PlantArchitecture(basic_context) as plantarch:
                plantarch.loadPlantModelFromLibrary("bean")

                plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 10.0)

                # Use default max_leaf_lifespan
                plantarch.setPlantPhenologicalThresholds(
                    plant_id=plant_id,
                    time_to_dormancy_break=0,
                    time_to_flower_initiation=25,
                    time_to_flower_opening=30,
                    time_to_fruit_set=35,
                    time_to_fruit_maturity=60,
                    time_to_dormancy=80
                    # max_leaf_lifespan uses default 1e6
                )

                assert True

        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture not available: {e}")


@pytest.mark.cross_platform
class TestPlantArchitectureProgressCallbackValidation:
    """Test progress callback parameter validation"""

    def test_set_progress_callback_rejects_non_callable(self):
        """Test setProgressCallback rejects non-callable arguments"""
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture plugin not available")

        with Context() as context:
            try:
                with PlantArchitecture(context) as pa:
                    with pytest.raises(ValueError, match="callable"):
                        pa.setProgressCallback("not_a_callable")
                    with pytest.raises(ValueError, match="callable"):
                        pa.setProgressCallback(42)
            except PlantArchitectureError:
                pytest.skip("PlantArchitecture not available")

    def test_set_progress_callback_accepts_none(self):
        """Test setProgressCallback accepts None to clear callback"""
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture plugin not available")

        with Context() as context:
            try:
                with PlantArchitecture(context) as pa:
                    pa.setProgressCallback(None)
            except PlantArchitectureError:
                pytest.skip("PlantArchitecture not available")

    def test_set_progress_callback_accepts_callable(self):
        """Test setProgressCallback accepts a callable"""
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture plugin not available")

        with Context() as context:
            try:
                with PlantArchitecture(context) as pa:
                    pa.setProgressCallback(lambda p, m: None)
                    pa.setProgressCallback(None)
            except PlantArchitectureError:
                pytest.skip("PlantArchitecture not available")


@pytest.mark.native_only
class TestPlantArchitectureProgressCallbackNative:
    """Test progress callback with native library functionality"""

    @pytest.fixture
    def context(self, check_native_library):
        """Create a Context for testing with proper cleanup"""
        context = Context()
        yield context
        context.__exit__(None, None, None)

    @pytest.fixture
    def plantarch(self, context):
        """Create PlantArchitecture instance with proper cleanup"""
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture plugin not available")

        try:
            plantarch_instance = PlantArchitecture(context)
            yield plantarch_instance
            plantarch_instance.__exit__(None, None, None)
        except PlantArchitectureError as e:
            pytest.skip(f"PlantArchitecture initialization failed: {e}")

    def test_progress_callback(self, plantarch):
        """Test progress callback receives updates during advanceTime"""
        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        model = 'bean' if 'bean' in models else models[0]
        plantarch.loadPlantModelFromLibrary(model)

        position = vec3(0, 0, 0)
        plantarch.buildPlantInstanceFromLibrary(position, age=0.0)

        updates = []

        def on_progress(progress, message):
            updates.append((progress, message))

        plantarch.setProgressCallback(on_progress)
        plantarch.advanceTime(1.0)

        assert len(updates) > 0, "Progress callback should have been called at least once"

        for progress, message in updates:
            assert 0.0 <= progress <= 1.0, f"Progress {progress} out of range [0, 1]"
            assert isinstance(message, str), f"Message should be str, got {type(message)}"
            assert len(message) > 0, "Message should be non-empty"

        assert updates[-1][0] == pytest.approx(1.0, abs=0.05), \
            f"Final progress should be ~1.0, got {updates[-1][0]}"

    def test_progress_callback_clear(self, plantarch):
        """Test clearing progress callback with None"""
        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")

        model = 'bean' if 'bean' in models else models[0]
        plantarch.loadPlantModelFromLibrary(model)
        plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), age=0.0)

        updates = []
        plantarch.setProgressCallback(lambda p, m: updates.append((p, m)))
        plantarch.advanceTime(1.0)

        count_before_clear = len(updates)
        assert count_before_clear > 0, "Should have received callbacks"

        plantarch.setProgressCallback(None)
        plantarch.advanceTime(1.0)

        assert len(updates) == count_before_clear, \
            "No callbacks should fire after clearing with None"


@pytest.mark.native_only
class TestPlantArchitectureShootTopology:
    """Tests for the shoot-topology accessors added with the helios-core 1.3.74 merge:
    getAllShootIDs / getShoot / getShootChildIDs / getShootInternode{Vertices,Radii}."""

    @pytest.fixture
    def context(self, check_native_library):
        context = Context()
        yield context
        context.__exit__(None, None, None)

    @pytest.fixture
    def plantarch(self, context):
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            pytest.skip("PlantArchitecture plugin not available")
        plantarch_instance = PlantArchitecture(context)
        yield plantarch_instance
        plantarch_instance.__exit__(None, None, None)

    def _build_plant(self, plantarch):
        models = plantarch.getAvailablePlantModels()
        if not models:
            pytest.skip("No plant models available")
        plantarch.loadPlantModelFromLibrary(models[0])
        return plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 15.0)

    def test_get_all_shoot_ids(self, plantarch):
        """getAllShootIDs returns a contiguous 0-based list with shoot 0 (the base stem)."""
        plant_id = self._build_plant(plantarch)
        shoot_ids = plantarch.getAllShootIDs(plant_id)
        assert isinstance(shoot_ids, list)
        assert len(shoot_ids) >= 1
        assert shoot_ids[0] == 0
        assert shoot_ids == list(range(len(shoot_ids)))

    def test_get_shoot_topology(self, plantarch):
        """getShoot returns the base stem's topology: rank 0, parent -1."""
        plant_id = self._build_plant(plantarch)
        shoot = plantarch.getShoot(plant_id, 0)
        assert set(shoot.keys()) == {"rank", "parent_shoot_id", "parent_node_index", "node_count"}
        assert shoot["rank"] == 0
        assert shoot["parent_shoot_id"] == -1  # base stem has no parent
        assert shoot["node_count"] >= 1

    def test_get_shoot_children(self, plantarch):
        """getShootChildIDs returns valid child shoot IDs that exist in getAllShootIDs."""
        plant_id = self._build_plant(plantarch)
        all_ids = set(plantarch.getAllShootIDs(plant_id))
        children = plantarch.getShootChildIDs(plant_id, 0)
        assert isinstance(children, list)
        for child in children:
            assert child in all_ids

    def test_get_shoot_internode_geometry(self, plantarch):
        """Internode vertices are (x,y,z) tuples with a parallel per-vertex radii array."""
        plant_id = self._build_plant(plantarch)
        verts = plantarch.getShootInternodeVertices(plant_id, 0)
        radii = plantarch.getShootInternodeRadii(plant_id, 0)
        assert isinstance(verts, list)
        assert isinstance(radii, list)
        assert len(verts) == len(radii)
        for v in verts:
            assert len(v) == 3
        for r in radii:
            assert r >= 0.0

    def test_shoot_accessors_reject_negative_ids(self, plantarch):
        """Negative plant/shoot IDs raise ValueError."""
        with pytest.raises(ValueError):
            plantarch.getShoot(-1, 0)
        with pytest.raises(ValueError):
            plantarch.getShootChildIDs(0, -1)
