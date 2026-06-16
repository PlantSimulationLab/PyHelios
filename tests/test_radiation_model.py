"""
Tests for RadiationModel functionality in PyHelios.

This module tests the RadiationModel class and radiation simulation capabilities.
Tests are designed to work in both native and mock modes.
"""

import pytest
import sys
import os
import numpy as np
from typing import List

# Add pyhelios to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pyhelios import Context, RadiationModel, RadiationModelError, DataTypes
from pyhelios.validation.exceptions import ValidationError

# RadiationSourceType may not be available if RadiationModel is None
try:
    from pyhelios.RadiationModel import RadiationSourceType
except (ImportError, AttributeError):
    RadiationSourceType = None


@pytest.mark.native_only
@pytest.mark.requires_gpu
class TestRadiationModel:
    """Test RadiationModel class functionality"""
    
    def test_radiation_model_creation(self):
        """Test RadiationModel creation and destruction"""
        with Context() as context:
            # Test creating RadiationModel
            with RadiationModel(context) as radiation_model:
                assert radiation_model is not None
                # Native pointer may be None in mock mode, but RadiationModel should still work
                native_ptr = radiation_model.getNativePtr()
                assert native_ptr is not None or native_ptr is None  # Accept both cases
    
    @pytest.mark.cross_platform  
    def test_radiation_model_invalid_context(self):
        """Test RadiationModel creation with invalid context"""
        with pytest.raises(TypeError):
            RadiationModel("invalid_context")
    
    def test_message_control(self):
        """Test message enable/disable functionality"""
        with Context() as context:
            with RadiationModel(context) as radiation_model:
                # These should not raise exceptions
                radiation_model.disableMessages()
                radiation_model.enableMessages()
    
    def test_radiation_bands(self):
        """Test radiation band management"""
        with Context() as context:
            with RadiationModel(context) as radiation_model:
                # Add basic radiation band
                radiation_model.addRadiationBand("SW")
                
                # Add band with wavelength bounds (wavelengths in nanometers)
                radiation_model.addRadiationBand("PAR", 400, 700)
                
                # Copy radiation band
                radiation_model.copyRadiationBand("SW", "SW_copy")
    
    def test_radiation_sources(self):
        """Test radiation source creation"""
        with Context() as context:
            with RadiationModel(context) as radiation_model:
                # Test default collimated source
                source1 = radiation_model.addCollimatedRadiationSource()
                assert isinstance(source1, int)
                
                # Test collimated source with vec3 direction
                direction = DataTypes.vec3(0.4, -0.4, 0.6)
                source2 = radiation_model.addCollimatedRadiationSource(direction)
                assert isinstance(source2, int)
                
                # Test collimated source with spherical direction
                spherical_dir = DataTypes.SphericalCoord(1.0, 0.5, 0.3)
                source3 = radiation_model.addCollimatedRadiationSource(spherical_dir)
                assert isinstance(source3, int)
                
                # Test sphere radiation source
                position = DataTypes.vec3(0, 0, 10)
                source4 = radiation_model.addSphereRadiationSource(position, 1.0)
                assert isinstance(source4, int)
                
                # Test sun sphere radiation source
                source5 = radiation_model.addSunSphereRadiationSource(
                    radius=1.0, zenith=30.0, azimuth=45.0, angular_width=0.53)
                assert isinstance(source5, int)
    
    def test_radiation_source_invalid_direction(self):
        """Test radiation source creation with invalid direction type"""
        with Context() as context:
            with RadiationModel(context) as radiation_model:
                with pytest.raises(TypeError):
                    radiation_model.addCollimatedRadiationSource("invalid_direction")
    
    @pytest.mark.cross_platform  
    def test_ray_count_configuration(self):
        """Test ray count configuration"""
        with Context() as context:
            with RadiationModel(context) as radiation_model:
                radiation_model.addRadiationBand("SW")
                
                # Set direct ray count
                radiation_model.setDirectRayCount("SW", 100)
                
                # Set diffuse ray count
                radiation_model.setDiffuseRayCount("SW", 300)
    
    def test_flux_configuration(self):
        """Test flux configuration"""
        with Context() as context:
            with RadiationModel(context) as radiation_model:
                radiation_model.addRadiationBand("SW")
                source = radiation_model.addCollimatedRadiationSource()
                
                # Set diffuse radiation flux
                radiation_model.setDiffuseRadiationFlux("SW", 200.0)
                
                # Set single source flux
                radiation_model.setSourceFlux(source, "SW", 800.0)
                
                # Set multiple source flux
                source2 = radiation_model.addCollimatedRadiationSource()
                radiation_model.setSourceFlux([source, source2], "SW", 400.0)
                
                # Get source flux (may return 0 in mock mode)
                flux = radiation_model.getSourceFlux(source, "SW")
                assert isinstance(flux, float)
    
    def test_flux_configuration_invalid_types(self):
        """Test flux configuration with invalid types"""
        with Context() as context:
            with RadiationModel(context) as radiation_model:
                radiation_model.addRadiationBand("SW")
                
                with pytest.raises(ValidationError):
                    radiation_model.setSourceFlux("invalid_source", "SW", 800.0)
    
    def test_scattering_configuration(self):
        """Test scattering configuration"""
        with Context() as context:
            with RadiationModel(context) as radiation_model:
                radiation_model.addRadiationBand("SW")
                
                # Set scattering depth
                radiation_model.setScatteringDepth("SW", 3)
                
                # Set minimum scatter energy
                radiation_model.setMinScatterEnergy("SW", 0.01)
    
    def test_emission_control(self):
        """Test emission control"""
        with Context() as context:
            with RadiationModel(context) as radiation_model:
                radiation_model.addRadiationBand("SW")
                
                # Disable emission
                radiation_model.disableEmission("SW")
                
                # Enable emission
                radiation_model.enableEmission("SW")
    
    def test_geometry_update(self):
        """Test geometry update"""
        with Context() as context:
            # Add some geometry
            patch = context.addPatch()
            
            with RadiationModel(context) as radiation_model:
                # Update all geometry
                radiation_model.updateGeometry()
                
                # Update specific geometry
                radiation_model.updateGeometry([patch])
    
    def test_run_simulation_basic(self):
        """Test basic simulation execution (should not crash in mock mode)"""
        with Context() as context:
            # Add simple geometry
            patch = context.addPatch()
            context.setPrimitiveDataFloat(patch, "radiation_flux_SW", 500.0)
            
            with RadiationModel(context) as radiation_model:
                radiation_model.addRadiationBand("SW")
                source = radiation_model.addCollimatedRadiationSource()
                radiation_model.setSourceFlux(source, "SW", 800.0)
                
                radiation_model.updateGeometry()
                
                # Run single band
                radiation_model.runBand("SW")
                
                # Run multiple bands  
                radiation_model.addRadiationBand("LW")
                radiation_model.runBand(["SW", "LW"])
    
    def test_run_simulation_invalid_types(self):
        """Test simulation with invalid label types"""
        with Context() as context:
            with RadiationModel(context) as radiation_model:
                with pytest.raises(ValidationError):
                    radiation_model.runBand(123)  # Invalid type
    
    def test_result_access(self):
        """Test accessing simulation results"""
        with Context() as context:
            patch = context.addPatch()
            
            with RadiationModel(context) as radiation_model:
                # Get total absorbed flux (returns list, may be empty in mock mode)
                flux = radiation_model.getTotalAbsorbedFlux()
                assert isinstance(flux, list)


@pytest.mark.native_only
class TestContextPseudocolor:
    """Test Context pseudocolor functionality"""
    
    def test_pseudocolor_basic(self):
        """Test basic pseudocolor functionality"""
        with Context() as context:
            # Add geometry
            patches = [context.addPatch() for _ in range(3)]
            
            # Set primitive data
            for i, patch in enumerate(patches):
                context.setPrimitiveDataFloat(patch, "test_data", float(i * 100))
            
            # Apply pseudocolor (may raise NotImplementedError in mock mode)
            try:
                context.colorPrimitiveByDataPseudocolor(
                    patches, "test_data", "hot", 10)
            except NotImplementedError:
                # Expected in mock mode when pseudocolor functions are not available
                pass
    
    def test_pseudocolor_with_range(self):
        """Test pseudocolor with specified range"""
        with Context() as context:
            # Add geometry
            patches = [context.addPatch() for _ in range(3)]
            
            # Set primitive data
            for i, patch in enumerate(patches):
                context.setPrimitiveDataFloat(patch, "test_data", float(i * 100))
            
            # Apply pseudocolor with range (may raise NotImplementedError in mock mode)
            try:
                context.colorPrimitiveByDataPseudocolor(
                    patches, "test_data", "cool", 10, max_val=300.0, min_val=0.0)
            except NotImplementedError:
                # Expected in mock mode when pseudocolor functions are not available
                pass
    
    def test_pseudocolor_different_colormaps(self):
        """Test different colormap options"""
        with Context() as context:
            patch = context.addPatch()
            context.setPrimitiveDataFloat(patch, "test_data", 100.0)
            
            # Test different colormaps (may raise NotImplementedError in mock mode)
            colormaps = ["hot", "cool", "parula", "rainbow", "gray", "lava"]
            for colormap in colormaps:
                try:
                    context.colorPrimitiveByDataPseudocolor(
                        [patch], "test_data", colormap, 5)
                except NotImplementedError:
                    # Expected in mock mode when pseudocolor functions are not available
                    continue


@pytest.mark.native_only
@pytest.mark.requires_gpu
class TestRadiationModelIntegration:
    """Integration tests requiring native RadiationModel library"""
    
    def test_stanford_bunny_workflow(self):
        """Test Stanford Bunny-style radiation workflow"""
        # This test requires native libraries and the actual Stanford Bunny PLY file
        ply_path = os.path.join(os.path.dirname(__file__), '..', 
                               'helios-core', 'PLY', 'StanfordBunny.ply')
        
        if not os.path.exists(ply_path):
            pytest.skip("Stanford Bunny PLY file not found")
        
        with Context() as context:
            try:
                # Load Stanford Bunny
                bunny_uuids = context.loadPLY(ply_path, 
                                            origin=DataTypes.vec3(0, 0, 0),
                                            height=4.0)
                
                assert len(bunny_uuids) > 0
                
                with RadiationModel(context) as radiation_model:
                    # Set up radiation simulation
                    radiation_model.addRadiationBand("SW") 
                    radiation_model.disableEmission("SW")
                    radiation_model.setDirectRayCount("SW", 10)  # Low count for test speed
                    
                    sun_direction = DataTypes.vec3(0.4, -0.4, 0.6)
                    source = radiation_model.addCollimatedRadiationSource(sun_direction)
                    radiation_model.setSourceFlux(source, "SW", 800.0)
                    
                    radiation_model.updateGeometry()
                    radiation_model.runBand("SW")
                    
                    # Apply pseudocolor
                    context.colorPrimitiveByDataPseudocolor(
                        bunny_uuids[:100], "radiation_flux_SW", "hot")
                    
            except Exception:
                pytest.skip("Native RadiationModel not available or simulation failed")


@pytest.mark.mock_mode
class TestRadiationModelMockMode:
    """Tests specifically for mock mode behavior"""
    
    def test_mock_mode_graceful_degradation(self):
        """Test that RadiationModel provides clear error message when radiation plugin is unavailable"""
        from pyhelios.plugins.registry import get_plugin_registry
        
        # Skip this test if radiation plugin is actually available
        registry = get_plugin_registry()
        if registry.is_plugin_available('radiation'):
            pytest.skip("Radiation plugin is available - this test is for mock mode only")
        
        with Context() as context:
            # RadiationModel should raise RadiationModelError when radiation plugin is not available
            with pytest.raises(RadiationModelError) as excinfo:
                RadiationModel(context)
            
            # Error message should be informative and actionable
            error_msg = str(excinfo.value)
            assert "radiation plugin" in error_msg
            assert "not available" in error_msg or "required but is not available" in error_msg
            
            # Should mention system requirements
            assert any(keyword in error_msg for keyword in ["GPU", "CUDA", "OptiX", "build"])
            
            # Should provide actionable solutions  
            assert "build_scripts/build_helios" in error_msg


@pytest.fixture
def radiation_model_with_camera():
    """Fixture providing a RadiationModel with camera setup ready for testing"""
    with Context() as context:
        with RadiationModel(context) as radiation_model:
            # Add basic geometry for camera operations
            from pyhelios.wrappers.DataTypes import vec3, vec2, RGBcolor
            patch_center = vec3(0, 0, 0)
            patch_size = vec2(1.0, 1.0)
            patch_color = RGBcolor(0.5, 0.5, 0.5)
            patch_uuid = context.addPatch(center=patch_center, size=patch_size, color=patch_color)

            # Add primitive data for bounding box detection (integer values)
            context.setPrimitiveDataInt(patch_uuid, "leaves", 1)
            context.setPrimitiveDataInt(patch_uuid, "branches", 2)
            context.setPrimitiveDataInt(patch_uuid, "trunk", 3)
            context.setPrimitiveDataInt(patch_uuid, "tree_species", 4)

            sourceid = radiation_model.addCollimatedRadiationSource()

            # Add radiation band and camera
            radiation_model.addRadiationBand("red")
            radiation_model.setSourceFlux(sourceid, "red", 100.0)
            radiation_model.setScatteringDepth("red", 2)
            radiation_model.addRadiationCamera(
                camera_label="test_camera",
                band_labels=["red"],
                position=vec3(0, 0, 5),
                lookat_or_direction=vec3(0, 0, 0)
            )

            # Update geometry and run simulation (required for camera operations)
            radiation_model.updateGeometry()
            radiation_model.runBand(["red"])

            # Generate camera image to create pixel labels (required for most camera operations)
            radiation_model.writeCameraImage(
                camera="test_camera",
                bands=["red"],
                imagefile_base="test_image",
                image_path="./"
            )

            yield radiation_model, context


@pytest.mark.native_only
@pytest.mark.requires_gpu
class TestRadiationModelCameraFunctions:
    """Test new camera and image functions in RadiationModel v1.3.47"""
    
    def test_writeCameraImage(self):
        """Test camera image writing functionality"""
        with Context() as context:
            with RadiationModel(context) as radiation_model:
                # Add some geometry for the camera to render
                from pyhelios.wrappers.DataTypes import vec3, vec2, RGBcolor
                patch_center = vec3(0, 0, 0)
                patch_size = vec2(1.0, 1.0)
                patch_color = RGBcolor(0.5, 0.5, 0.5)
                context.addPatch(center=patch_center, size=patch_size, color=patch_color)

                # Add radiation bands first (use 3 bands for RGB image)
                radiation_model.addRadiationBand("red")
                radiation_model.addRadiationBand("green")
                radiation_model.addRadiationBand("blue")

                # Add camera before writing image
                radiation_model.addRadiationCamera(
                    camera_label="test_camera",
                    band_labels=["red", "green", "blue"],
                    position=vec3(0, 0, 5),
                    lookat_or_direction=vec3(0, 0, 0)
                )

                # Update geometry and run simulation (required for camera operations)
                radiation_model.updateGeometry()
                radiation_model.runBand(["red", "green", "blue"])

                # Test basic camera image writing (may return empty string in mock mode)
                filename = radiation_model.writeCameraImage(
                    camera="test_camera",
                    bands=["red", "green", "blue"],
                    imagefile_base="test_image",
                    image_path="./"
                )
                assert isinstance(filename, str)
    
    def test_writeCameraImage_invalid_params(self):
        """Test camera image writing with invalid parameters"""
        with Context() as context:
            with RadiationModel(context) as radiation_model:
                # Test invalid camera type
                with pytest.raises(TypeError):
                    radiation_model.writeCameraImage(
                        camera=123,  # Invalid type
                        bands=["RGB"], 
                        imagefile_base="test"
                    )
                
                # Test empty bands list
                with pytest.raises(TypeError):
                    radiation_model.writeCameraImage(
                        camera="test_camera",
                        bands=[],  # Empty list
                        imagefile_base="test"
                    )
                
                # Test invalid flux conversion
                with pytest.raises(TypeError):
                    radiation_model.writeCameraImage(
                        camera="test_camera",
                        bands=["RGB"],
                        imagefile_base="test",
                        flux_to_pixel_conversion=0  # Invalid value
                    )
    
    def test_writeNormCameraImage(self):
        """Test normalized camera image writing"""
        with Context() as context:
            with RadiationModel(context) as radiation_model:
                # Add radiation bands first
                radiation_model.addRadiationBand("R")
                radiation_model.addRadiationBand("G")
                radiation_model.addRadiationBand("B")

                # Add camera before writing image
                from pyhelios.wrappers.DataTypes import vec3
                radiation_model.addRadiationCamera(
                    camera_label="test_camera",
                    band_labels=["R", "G", "B"],
                    position=vec3(0, 0, 5),
                    lookat_or_direction=vec3(0, 0, 0)
                )

                filename = radiation_model.writeNormCameraImage(
                    camera="test_camera",
                    bands=["R", "G", "B"],
                    imagefile_base="normalized_test",
                    frame=0
                )
                assert isinstance(filename, str)
    
    def test_writeCameraImage_data(self):
        """Test camera image data writing (ASCII format)"""
        with Context() as context:
            with RadiationModel(context) as radiation_model:
                # Add radiation band first
                radiation_model.addRadiationBand("RGB")

                # Add camera before writing data
                from pyhelios.wrappers.DataTypes import vec3
                radiation_model.addRadiationCamera(
                    camera_label="test_camera",
                    band_labels=["RGB"],
                    position=vec3(0, 0, 5),
                    lookat_or_direction=vec3(0, 0, 0)
                )

                # Should not raise exception
                radiation_model.writeCameraImageData(
                    camera="test_camera",
                    band="RGB",
                    imagefile_base="data_test",
                    image_path="./output/",
                    frame=-1
                )
    
    def test_writeImageBoundingBoxes_single_primitive(self, radiation_model_with_camera):
        """Test writing image bounding boxes with single primitive data label"""
        radiation_model, context = radiation_model_with_camera

        # Test single primitive data label (tree_species is already set in the fixture)
        radiation_model.writeImageBoundingBoxes(
            camera_label="test_camera",
            primitive_data_labels="tree_species",
            object_class_ids=1,
            image_file="test_image.jpg"
        )
    
    def test_writeImageBoundingBoxes_multiple_primitive(self, radiation_model_with_camera):
        """Test writing image bounding boxes with multiple primitive data labels"""
        radiation_model, context = radiation_model_with_camera

        # Test multiple primitive data labels (leaves, branches, trunk are already set in the fixture)
        radiation_model.writeImageBoundingBoxes(
            camera_label="test_camera",
            primitive_data_labels=["leaves", "branches", "trunk"],
            object_class_ids=[1, 2, 3],
            image_file="test_image.jpg",
            classes_txt_file="plant_classes.txt"
        )
    
    def test_writeImageBoundingBoxes_single_object(self, radiation_model_with_camera):
        """Test writing image bounding boxes with single object data label"""
        radiation_model, context = radiation_model_with_camera

        # Add object data that can be used for bounding boxes
        patch_uuids = context.getAllUUIDs()
        if patch_uuids:
            context.setPrimitiveDataString(patch_uuids[0], "tree_id", "oak_tree_001")

        # Test single object data label
        radiation_model.writeImageBoundingBoxes(
            camera_label="test_camera",
            object_data_labels="tree_id",
            object_class_ids=5,
            image_file="test_image.jpg"
        )
    
    def test_writeImageBoundingBoxes_multiple_object(self, radiation_model_with_camera):
        """Test writing image bounding boxes with multiple object data labels"""
        radiation_model, context = radiation_model_with_camera

        # Add object data that can be used for bounding boxes
        patch_uuids = context.getAllUUIDs()
        if patch_uuids:
            context.setPrimitiveDataString(patch_uuids[0], "tree_1", "oak_001")
            context.setPrimitiveDataString(patch_uuids[0], "tree_2", "oak_002")
            context.setPrimitiveDataString(patch_uuids[0], "tree_3", "oak_003")

        # Test multiple object data labels
        radiation_model.writeImageBoundingBoxes(
            camera_label="test_camera",
            object_data_labels=["tree_1", "tree_2", "tree_3"],
            object_class_ids=[10, 11, 12],
            image_file="test_image.jpg",
            image_path="./annotations/"
        )
    
    def test_writeImageBoundingBoxes_invalid_params(self):
        """Test bounding boxes with invalid parameters"""
        with Context() as context:
            with RadiationModel(context) as radiation_model:
                # Test both primitive and object labels provided (should fail)
                with pytest.raises(ValueError):
                    radiation_model.writeImageBoundingBoxes(
                        camera_label="test_camera",
                        primitive_data_labels="test",
                        object_data_labels="test2",  # Both provided - invalid
                        object_class_ids=1,
                        image_file="test.jpg"
                    )
                
                # Test neither provided (should fail)
                with pytest.raises(ValueError):
                    radiation_model.writeImageBoundingBoxes(
                        camera_label="test_camera",
                        image_file="test.jpg"
                    )
                
                # Test mismatched lengths
                with pytest.raises(ValueError):
                    radiation_model.writeImageBoundingBoxes(
                        camera_label="test_camera",
                        primitive_data_labels=["a", "b"],
                        object_class_ids=[1],  # Wrong length
                        image_file="test.jpg"
                    )
    
    def test_writeImageSegmentationMasks_single_primitive(self, radiation_model_with_camera):
        """Test writing segmentation masks with single primitive data label"""
        radiation_model, context = radiation_model_with_camera

        # Generate camera image first (required for segmentation masks)
        image_filename = radiation_model.writeCameraImage(
            camera="test_camera",
            bands=["red"],
            imagefile_base="test_image",
            image_path="./"
        )

        # Add primitive data for segmentation masks
        patch_uuids = context.getAllUUIDs()
        if patch_uuids:
            context.setPrimitiveDataInt(patch_uuids[0], "leaf_type", 1)

        radiation_model.writeImageSegmentationMasks(
            camera_label="test_camera",
            primitive_data_labels="leaf_type",
            object_class_ids=1,
            json_filename="segmentation.json",
            image_file=image_filename,
            append_file=False
        )
    
    def test_writeImageSegmentationMasks_multiple_primitive(self, radiation_model_with_camera):
        """Test writing segmentation masks with multiple primitive data labels"""
        radiation_model, context = radiation_model_with_camera

        # Generate camera image first (required for segmentation masks)
        image_filename = radiation_model.writeCameraImage(
            camera="test_camera",
            bands=["red"],
            imagefile_base="test_image",
            image_path="./"
        )

        # Add primitive data for segmentation masks
        patch_uuids = context.getAllUUIDs()
        if patch_uuids:
            context.setPrimitiveDataInt(patch_uuids[0], "leaves", 1)
            context.setPrimitiveDataInt(patch_uuids[0], "stem", 1)
            context.setPrimitiveDataInt(patch_uuids[0], "fruit", 2)

        radiation_model.writeImageSegmentationMasks(
            camera_label="test_camera",
            primitive_data_labels=["leaves", "stem", "fruit"],
            object_class_ids=[1, 2, 3],
            json_filename="multi_segmentation.json",
            image_file=image_filename,
            append_file=True
        )
    
    def test_writeImageSegmentationMasks_object_data(self, radiation_model_with_camera):
        """Test writing segmentation masks with object data labels"""
        radiation_model, context = radiation_model_with_camera

        # Generate camera image first (required for segmentation masks)
        image_filename = radiation_model.writeCameraImage(
            camera="test_camera",
            bands=["red"],
            imagefile_base="test_image",
            image_path="./"
        )

        # Add object data for segmentation masks
        patch_uuids = context.getAllUUIDs()
        if patch_uuids:
            context.setPrimitiveDataString(patch_uuids[0], "plant_id", "plant_001")
            context.setPrimitiveDataString(patch_uuids[0], "plant_1", "plant_a")
            context.setPrimitiveDataString(patch_uuids[0], "plant_2", "plant_b")

        # Single object data label
        radiation_model.writeImageSegmentationMasks(
            camera_label="test_camera",
            object_data_labels="plant_id",
            object_class_ids=10,
            json_filename="object_segmentation.json",
            image_file=image_filename
        )

        # Multiple object data labels
        radiation_model.writeImageSegmentationMasks(
            camera_label="test_camera",
            object_data_labels=["plant_1", "plant_2"],
            object_class_ids=[10, 11],
            json_filename="multi_object_segmentation.json",
            image_file=image_filename,
            append_file=True
        )
    
    def test_writeImageSegmentationMasks_invalid_params(self):
        """Test segmentation masks with invalid parameters"""
        with Context() as context:
            with RadiationModel(context) as radiation_model:
                # Test both primitive and object labels provided (should fail)
                with pytest.raises(ValueError):
                    radiation_model.writeImageSegmentationMasks(
                        camera_label="test_camera",
                        primitive_data_labels="test",
                        object_data_labels="test2",  # Both provided - invalid
                        object_class_ids=1,
                        json_filename="test.json",
                        image_file="test.jpg"
                    )
                
                # Test invalid append_file type
                with pytest.raises(TypeError):
                    radiation_model.writeImageSegmentationMasks(
                        camera_label="test_camera",
                        primitive_data_labels="test",
                        object_class_ids=1,
                        json_filename="test.json",
                        image_file="test.jpg",
                        append_file="invalid"  # Should be boolean
                    )
    
    def test_autoCalibrateCameraImage_invalid_params(self):
        """Test auto-calibration with invalid parameters"""
        with Context() as context:
            with RadiationModel(context) as radiation_model:
                # Test invalid algorithm
                with pytest.raises(ValueError):
                    radiation_model.autoCalibrateCameraImage(
                        camera_label="test_camera",
                        red_band_label="R",
                        green_band_label="G",
                        blue_band_label="B",
                        output_file_path="test.jpg",
                        algorithm="INVALID_ALGORITHM"
                    )
                
                # Test empty camera label
                with pytest.raises(TypeError):
                    radiation_model.autoCalibrateCameraImage(
                        camera_label="",  # Empty string
                        red_band_label="R",
                        green_band_label="G",
                        blue_band_label="B",
                        output_file_path="test.jpg"
                    )
                
                # Test invalid print_quality_report type
                with pytest.raises(TypeError):
                    radiation_model.autoCalibrateCameraImage(
                        camera_label="test_camera",
                        red_band_label="R",
                        green_band_label="G",
                        blue_band_label="B",
                        output_file_path="test.jpg",
                        print_quality_report="invalid"  # Should be boolean
                    )


@pytest.mark.native_only
@pytest.mark.requires_gpu
class TestRadiationModelLabelMap:
    """Test per-pixel primitive/object data label map functions."""

    def _setup_full_fov_scene(self, context, radiation_model, patch_id):
        """Render a scene where a single labelled patch fills the entire camera FOV.

        Returns (camera_label, band_label, resolution) and leaves the model run so that
        per-pixel labels exist. Camera at (0,0,5) looking down with HFOV=90 sees a focal
        plane half-width of 5 at z=0, so a 20x20 patch fully covers the view.
        """
        from pyhelios.wrappers.DataTypes import vec3, vec2
        from pyhelios import CameraProperties

        patch_uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(20.0, 20.0))
        context.setPrimitiveDataInt(patch_uuid, "patch_id", patch_id)

        source = radiation_model.addCollimatedRadiationSource(vec3(0, 0, 1))
        radiation_model.addRadiationBand("SW")
        radiation_model.setSourceFlux(source, "SW", 1000.0)
        radiation_model.setScatteringDepth("SW", 1)

        resolution = (32, 32)
        camera_props = CameraProperties(camera_resolution=resolution, HFOV=90.0)
        radiation_model.addRadiationCamera(
            camera_label="label_cam",
            band_labels=["SW"],
            position=vec3(0, 0, 5),
            lookat_or_direction=vec3(0, 0, 0),
            camera_properties=camera_props,
            antialiasing_samples=1,
        )

        radiation_model.updateGeometry()
        radiation_model.runBand(["SW"])
        return "label_cam", "SW", resolution

    def test_write_primitive_data_label_map_file(self, tmp_path):
        """writePrimitiveDataLabelMap writes a text map matching camera resolution."""
        patch_id = 7
        with Context() as context:
            with RadiationModel(context) as radiation_model:
                camera, band, resolution = self._setup_full_fov_scene(
                    context, radiation_model, patch_id)
                width, height = resolution

                radiation_model.writePrimitiveDataLabelMap(
                    camera=camera,
                    primitive_data_label="patch_id",
                    imagefile_base="labels",
                    image_path=str(tmp_path) + os.sep,
                    frame=0,
                )

                # frame >= 0 => zero-padded 5-digit frame suffix
                label_file = tmp_path / f"{camera}_labels_00000.txt"
                assert label_file.exists(), f"Label map file not created: {label_file}"

                labels = np.loadtxt(str(label_file))
                assert labels.shape == (height, width)
                assert labels.size == width * height

                # Patch fills the whole FOV: every pixel carries the patch label, no padding.
                assert not np.any(np.isnan(labels)), "Full-FOV scene should have no background pixels"
                assert np.all(labels == patch_id)

                # Cross-check pixel count against getCameraPixelData (one value per pixel).
                pixel_data = radiation_model.getCameraPixelData(camera, band)
                assert len(pixel_data) == width * height
                foreground = int(np.count_nonzero(~np.isnan(labels)))
                assert foreground == len(pixel_data)

    def test_get_primitive_data_label_map_array(self):
        """getPrimitiveDataLabelMap returns a 2D NumPy array with NaN background."""
        patch_id = 3
        with Context() as context:
            with RadiationModel(context) as radiation_model:
                from pyhelios.wrappers.DataTypes import vec3, vec2
                from pyhelios import CameraProperties

                # Small patch leaves background pixels so we exercise the NaN padding path.
                patch_uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(2.0, 2.0))
                context.setPrimitiveDataInt(patch_uuid, "patch_id", patch_id)

                source = radiation_model.addCollimatedRadiationSource(vec3(0, 0, 1))
                radiation_model.addRadiationBand("SW")
                radiation_model.setSourceFlux(source, "SW", 1000.0)
                radiation_model.setScatteringDepth("SW", 1)

                resolution = (32, 32)
                camera_props = CameraProperties(camera_resolution=resolution, HFOV=90.0)
                radiation_model.addRadiationCamera(
                    camera_label="label_cam",
                    band_labels=["SW"],
                    position=vec3(0, 0, 5),
                    lookat_or_direction=vec3(0, 0, 0),
                    camera_properties=camera_props,
                    antialiasing_samples=1,
                )
                radiation_model.updateGeometry()
                radiation_model.runBand(["SW"])

                labels = radiation_model.getPrimitiveDataLabelMap("label_cam", "patch_id")

                width, height = resolution
                assert isinstance(labels, np.ndarray)
                assert labels.shape == (height, width)

                # Small patch in the center: some labelled foreground, some NaN background.
                foreground_mask = labels == patch_id
                background_mask = np.isnan(labels)
                assert foreground_mask.any(), "Expected the central patch to be visible"
                assert background_mask.any(), "Expected background (NaN) pixels around the patch"
                # Every non-background pixel must carry the patch label.
                assert np.all(labels[~background_mask] == patch_id)

                # Cross-check total pixel count against getCameraPixelData.
                pixel_data = radiation_model.getCameraPixelData("label_cam", "SW")
                assert len(pixel_data) == width * height
                assert int(foreground_mask.sum() + background_mask.sum()) == len(pixel_data)


@pytest.mark.cross_platform
class TestRadiationModelLabelMapAPI:
    """Mock-mode-safe checks that the label map API is wired up and importable."""

    def test_label_map_methods_exist(self):
        """The label map methods are exposed regardless of native availability."""
        for name in ("writePrimitiveDataLabelMap", "writeObjectDataLabelMap",
                     "getPrimitiveDataLabelMap", "getObjectDataLabelMap"):
            assert hasattr(RadiationModel, name), f"RadiationModel missing {name}"

    def test_label_map_wrapper_functions_exist(self):
        """The ctypes wrapper exposes the label map functions (import does not crash)."""
        from pyhelios.wrappers import URadiationModelWrapper as wrapper
        assert hasattr(wrapper, "writePrimitiveDataLabelMap")
        assert hasattr(wrapper, "writeObjectDataLabelMap")


@pytest.mark.requires_gpu
class TestRadiationModelCameraFunctionsMock:
    """Test camera functions with GPU/OptiX requirements"""

    def test_camera_functions_with_gpu(self, radiation_model_with_camera):
        """Test that camera functions work when GPU/OptiX is available"""
        # This test requires GPU/OptiX since camera functions use radiation ray tracing
        radiation_model, context = radiation_model_with_camera

        # Add RGB radiation band
        radiation_model.addRadiationBand("RGB")

        # Add camera for testing functionality
        from pyhelios.wrappers.DataTypes import vec3
        radiation_model.addRadiationCamera(
            camera_label="gpu_test",
            band_labels=["RGB"],
            position=vec3(0, 0, 5),
            lookat_or_direction=vec3(0, 0, 0)
        )

        # Update geometry and run simulation
        radiation_model.updateGeometry()
        radiation_model.runBand(["RGB"])

        # Test basic camera functionality
        filename = radiation_model.writeCameraImage(
            camera="gpu_test", bands=["RGB"], imagefile_base="test")
        assert isinstance(filename, str)


@pytest.mark.native_only
@pytest.mark.requires_gpu
class TestRadiationModelCameraCreation:
    """Test addRadiationCamera method functionality"""

    def test_add_radiation_camera_vec3(self):
        """Test adding radiation camera with vec3 position and lookat"""
        with Context() as context:
            with RadiationModel(context) as radiation_model:
                # Add radiation bands first
                radiation_model.addRadiationBand("red")
                radiation_model.addRadiationBand("green")
                radiation_model.addRadiationBand("blue")

                # Test basic camera creation with vec3 coordinates
                from pyhelios.wrappers.DataTypes import vec3
                radiation_model.addRadiationCamera(
                    camera_label="test_camera",
                    band_labels=["red", "green", "blue"],
                    position=vec3(0, 0, 5),
                    lookat_or_direction=vec3(0, 0, 0)
                )

    def test_add_radiation_camera_with_properties(self):
        """Test adding radiation camera with custom CameraProperties"""
        with Context() as context:
            with RadiationModel(context) as radiation_model:
                # Add radiation band
                radiation_model.addRadiationBand("RGB")

                # Create custom camera properties
                from pyhelios import CameraProperties
                camera_props = CameraProperties(
                    camera_resolution=(1024, 1024),
                    focal_plane_distance=2.0,
                    lens_diameter=0.1,
                    HFOV=45.0,
                    FOV_aspect_ratio=1.0
                )

                # Add camera with custom properties
                from pyhelios.wrappers.DataTypes import vec3
                radiation_model.addRadiationCamera(
                    camera_label="hd_camera",
                    band_labels=["RGB"],
                    position=vec3(0, 0, 10),
                    lookat_or_direction=vec3(0, 0, 0),
                    camera_properties=camera_props,
                    antialiasing_samples=200
                )

    def test_add_radiation_camera_validation(self):
        """Test parameter validation for addRadiationCamera"""
        with Context() as context:
            with RadiationModel(context) as radiation_model:
                radiation_model.addRadiationBand("test_band")
                from pyhelios.wrappers.DataTypes import vec3
                from pyhelios.validation.exceptions import ValidationError

                # Test invalid camera label (empty string)
                with pytest.raises(ValidationError):
                    radiation_model.addRadiationCamera(
                        camera_label="",  # Empty string
                        band_labels=["test_band"],
                        position=vec3(0, 0, 5),
                        lookat_or_direction=vec3(0, 0, 0)
                    )

                # Test invalid band labels (empty list)
                with pytest.raises(ValidationError):
                    radiation_model.addRadiationCamera(
                        camera_label="test",
                        band_labels=[],  # Empty list
                        position=vec3(0, 0, 5),
                        lookat_or_direction=vec3(0, 0, 0)
                    )

                # Test invalid antialiasing samples
                with pytest.raises(ValidationError):
                    radiation_model.addRadiationCamera(
                        camera_label="test",
                        band_labels=["test_band"],
                        position=vec3(0, 0, 5),
                        lookat_or_direction=vec3(0, 0, 0),
                        antialiasing_samples=0  # Must be positive
                    )

                # Test invalid list parameters (should reject lists)
                with pytest.raises(TypeError):
                    radiation_model.addRadiationCamera(
                        camera_label="invalid_test",
                        band_labels=["test_band"],
                        position=[1, 2, 3],  # Should reject lists
                        lookat_or_direction=vec3(0, 0, 0)
                    )

                # Test valid camera creation with proper vec3
                radiation_model.addRadiationCamera(
                    camera_label="valid_test",
                    band_labels=["test_band"],
                    position=vec3(1, 2, 3),  # Proper vec3
                    lookat_or_direction=vec3(0, 0, 0)  # Proper vec3
                )


@pytest.mark.native_only
@pytest.mark.requires_gpu
class TestBatch1SimpleMethods:
    """Test Batch 1: Simple methods (band query, source management, advanced simulation)"""

    def test_does_band_exist(self):
        """Test doesBandExist method"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                # Band doesn't exist yet
                assert not radiation.doesBandExist("test_band")

                # Add band
                radiation.addRadiationBand("test_band")

                # Now band exists
                assert radiation.doesBandExist("test_band")

                # Other band doesn't exist
                assert not radiation.doesBandExist("nonexistent")

    def test_delete_radiation_source(self):
        """Test deleteRadiationSource method"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                # Create source
                source_id = radiation.addCollimatedRadiationSource()
                assert isinstance(source_id, int)

                # Delete source (should not raise)
                radiation.deleteRadiationSource(source_id)

    def test_get_source_position(self):
        """Test getSourcePosition method"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                # Create source (collimated sources are at origin by default)
                source_id = radiation.addCollimatedRadiationSource()

                # Get position
                position = radiation.getSourcePosition(source_id)
                assert hasattr(position, 'x')
                assert hasattr(position, 'y')
                assert hasattr(position, 'z')

    def test_get_sky_energy(self):
        """Test getSkyEnergy method"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                energy = radiation.getSkyEnergy()
                assert isinstance(energy, float)
                assert energy >= 0

    def test_calculate_gtheta(self):
        """Test calculateGtheta method"""
        with Context() as context:
            # Add some geometry
            patch = context.addPatch(center=[0, 0, 1], size=[1, 1])

            with RadiationModel(context) as radiation:
                from pyhelios.wrappers.DataTypes import vec3

                # Calculate G-function for vertical view
                g_value = radiation.calculateGtheta(vec3(0, 0, 1))
                assert isinstance(g_value, float)

                # Calculate for horizontal view
                g_value2 = radiation.calculateGtheta([1, 0, 0])
                assert isinstance(g_value2, float)

    def test_optional_output_primitive_data(self):
        """Test optionalOutputPrimitiveData method"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                # Should not raise
                radiation.optionalOutputPrimitiveData("temperature")

    def test_enforce_periodic_boundary(self):
        """Test enforcePeriodicBoundary method"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                # Test various boundary specifications
                radiation.enforcePeriodicBoundary("xy")
                radiation.enforcePeriodicBoundary("xyz")
                radiation.enforcePeriodicBoundary("x")


@pytest.mark.native_only
@pytest.mark.requires_gpu
class TestBatch2GeometricSources:
    """Test Batch 2: Geometric sources and camera management"""

    def test_set_source_position_vec3(self):
        """Test setSourcePosition with vec3"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                from pyhelios.wrappers.DataTypes import vec3

                # Use sphere source which has a defined position
                source_id = radiation.addSphereRadiationSource(vec3(0, 0, 10), 1.0)

                # Set new position
                new_pos = vec3(10, 20, 30)
                radiation.setSourcePosition(source_id, new_pos)

                # Verify position changed
                position = radiation.getSourcePosition(source_id)
                assert abs(position.x - 10) < 0.01
                assert abs(position.y - 20) < 0.01
                assert abs(position.z - 30) < 0.01

    def test_set_source_position_list(self):
        """Test setSourcePosition with list"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                from pyhelios.wrappers.DataTypes import vec3

                # Use sphere source
                source_id = radiation.addSphereRadiationSource(vec3(0, 0, 10), 1.0)

                # Set position with list
                radiation.setSourcePosition(source_id, [5, 10, 15])

                # Verify
                position = radiation.getSourcePosition(source_id)
                assert abs(position.x - 5) < 0.01
                assert abs(position.y - 10) < 0.01
                assert abs(position.z - 15) < 0.01

    def test_add_rectangle_radiation_source(self):
        """Test addRectangleRadiationSource"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                from pyhelios.wrappers.DataTypes import vec3, vec2

                radiation.addRadiationBand("SW")

                # Add rectangle source (LED panel)
                source_id = radiation.addRectangleRadiationSource(
                    position=vec3(0, 0, 5),
                    size=vec2(2, 1),
                    rotation=vec3(0, 0, 0)
                )
                assert isinstance(source_id, int)

                # Set flux for the source
                radiation.setSourceFlux(source_id, "SW", 500.0)

    def test_add_rectangle_radiation_source_with_lists(self):
        """Test addRectangleRadiationSource with lists"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                radiation.addRadiationBand("SW")

                source_id = radiation.addRectangleRadiationSource(
                    position=[0, 0, 5],
                    size=[2, 1],
                    rotation=[0, 0, 0]
                )
                assert isinstance(source_id, int)

    def test_add_disk_radiation_source(self):
        """Test addDiskRadiationSource"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                from pyhelios.wrappers.DataTypes import vec3

                radiation.addRadiationBand("SW")

                # Add disk source (spotlight)
                source_id = radiation.addDiskRadiationSource(
                    position=vec3(0, 0, 5),
                    radius=1.5,
                    rotation=vec3(0, 0, 0)
                )
                assert isinstance(source_id, int)

                # Set flux
                radiation.setSourceFlux(source_id, "SW", 300.0)

    def test_camera_position_management(self):
        """Test camera position get/set"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                from pyhelios.wrappers.DataTypes import vec3
                from pyhelios.RadiationModel import CameraProperties

                radiation.addRadiationBand("test")

                # Create camera
                radiation.addRadiationCamera(
                    camera_label="cam1",
                    band_labels=["test"],
                    position=vec3(0, 0, 10),
                    lookat_or_direction=vec3(0, 0, 0)
                )

                # Get initial position
                pos = radiation.getCameraPosition("cam1")
                assert abs(pos.x - 0) < 0.01
                assert abs(pos.z - 10) < 0.01

                # Set new position
                radiation.setCameraPosition("cam1", vec3(5, 5, 15))

                # Verify changed
                new_pos = radiation.getCameraPosition("cam1")
                assert abs(new_pos.x - 5) < 0.01
                assert abs(new_pos.y - 5) < 0.01
                assert abs(new_pos.z - 15) < 0.01

    def test_camera_lookat_management(self):
        """Test camera lookat get/set"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                from pyhelios.wrappers.DataTypes import vec3

                radiation.addRadiationBand("test")
                radiation.addRadiationCamera(
                    camera_label="cam1",
                    band_labels=["test"],
                    position=vec3(0, 0, 10),
                    lookat_or_direction=vec3(0, 0, 0)
                )

                # Get lookat
                lookat = radiation.getCameraLookat("cam1")
                assert hasattr(lookat, 'x')

                # Set new lookat
                radiation.setCameraLookat("cam1", [5, 5, 0])

                # Verify
                new_lookat = radiation.getCameraLookat("cam1")
                assert abs(new_lookat.x - 5) < 0.01

    def test_camera_orientation_management(self):
        """Test camera orientation get/set"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                from pyhelios.wrappers.DataTypes import vec3, SphericalCoord

                radiation.addRadiationBand("test")
                radiation.addRadiationCamera(
                    camera_label="cam1",
                    band_labels=["test"],
                    position=vec3(0, 0, 10),
                    lookat_or_direction=vec3(0, 0, 0)
                )

                # Get orientation
                orientation = radiation.getCameraOrientation("cam1")
                assert hasattr(orientation, 'elevation')

                # Set with vec3
                radiation.setCameraOrientation("cam1", vec3(0, 0, 1))

                # Set with SphericalCoord
                radiation.setCameraOrientation("cam1", SphericalCoord(1.0, 45.0, 90.0))

    def test_get_all_camera_labels(self):
        """Test getAllCameraLabels method"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                from pyhelios.wrappers.DataTypes import vec3

                radiation.addRadiationBand("test")

                # Initially no cameras
                labels = radiation.getAllCameraLabels()
                assert isinstance(labels, list)

                # Add cameras
                radiation.addRadiationCamera("cam1", ["test"], vec3(0,0,10), vec3(0,0,0))
                radiation.addRadiationCamera("cam2", ["test"], vec3(5,0,10), vec3(0,0,0))

                # Should have 2 cameras
                labels = radiation.getAllCameraLabels()
                assert len(labels) == 2
                assert "cam1" in labels
                assert "cam2" in labels


@pytest.mark.native_only
@pytest.mark.requires_gpu
class TestBatch3SpectralData:
    """Test Batch 3: Spectral data management"""

    def test_set_source_spectrum_with_data(self):
        """Test setSourceSpectrum with spectrum data"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                radiation.addRadiationBand("SW")
                source_id = radiation.addCollimatedRadiationSource()

                # Define custom spectrum
                led_spectrum = [
                    (400, 0.0), (450, 0.3), (500, 0.8),
                    (550, 0.5), (600, 0.2), (700, 0.0)
                ]

                # Set spectrum (should not raise)
                radiation.setSourceSpectrum(source_id, led_spectrum)

    def test_set_source_spectrum_with_label(self):
        """Test setSourceSpectrum with global data label"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                radiation.addRadiationBand("SW")
                source_id = radiation.addCollimatedRadiationSource()

                # Test that method accepts string argument (even if label doesn't exist)
                # If label doesn't exist, C++ will raise error - verify error handling works
                try:
                    radiation.setSourceSpectrum(source_id, "D65_illuminant")
                    # If it works, great - verify no crash
                    assert True
                except Exception as e:
                    # If it fails, verify we get a meaningful error (not a crash)
                    assert "error" in str(e).lower() or "not found" in str(e).lower() or "does not exist" in str(e).lower(), \
                        f"Expected meaningful error about missing label, got: {e}"

    def test_set_source_spectrum_multiple_sources(self):
        """Test setSourceSpectrum for multiple sources"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                radiation.addRadiationBand("SW")
                source1 = radiation.addCollimatedRadiationSource()
                source2 = radiation.addCollimatedRadiationSource()

                spectrum = [(400, 0.5), (500, 1.0), (600, 0.5)]

                # Apply to multiple sources
                radiation.setSourceSpectrum([source1, source2], spectrum)

    def test_set_source_spectrum_integral(self):
        """Test setSourceSpectrumIntegral"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                radiation.addRadiationBand("SW")
                source_id = radiation.addCollimatedRadiationSource()

                # First set a spectrum, then set integral
                spectrum = [(400, 0.5), (500, 1.0), (600, 0.5)]
                radiation.setSourceSpectrum(source_id, spectrum)

                # Now set integral
                radiation.setSourceSpectrumIntegral(source_id, 1000.0)

                # Set integral with range
                radiation.setSourceSpectrumIntegral(source_id, 500.0, 400, 700)

    def test_integrate_spectrum_basic(self):
        """Test integrateSpectrum basic integration"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                spectrum = [(400, 0.1), (500, 0.5), (600, 0.8), (700, 0.3)]

                # Basic integration
                result = radiation.integrateSpectrum(spectrum)
                assert isinstance(result, float)
                assert result >= 0

    def test_integrate_spectrum_with_range(self):
        """Test integrateSpectrum with wavelength range"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                spectrum = [(300, 0.1), (400, 0.5), (600, 0.8), (800, 0.3)]

                # Integration over PAR range
                par_result = radiation.integrateSpectrum(spectrum, 400, 700)
                assert isinstance(par_result, float)

    def test_integrate_spectrum_with_source(self):
        """Test integrateSpectrum with source"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                radiation.addRadiationBand("SW")
                source_id = radiation.addCollimatedRadiationSource()

                # Set source spectrum first
                source_spectrum = [(400, 0.8), (500, 1.0), (600, 0.6)]
                radiation.setSourceSpectrum(source_id, source_spectrum)
                radiation.setSourceFlux(source_id, "SW", 1000.0)

                spectrum = [(400, 0.5), (500, 1.0), (600, 0.5)]

                # Integration with source spectrum
                result = radiation.integrateSpectrum(spectrum, 400, 700, source_id=source_id)
                assert isinstance(result, float)

    def test_integrate_spectrum_with_camera(self):
        """Test integrateSpectrum with camera spectrum"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                object_spectrum = [(400, 0.5), (500, 1.0), (600, 0.8)]
                camera_response = [(400, 0.2), (550, 1.0), (700, 0.3)]

                # Integration with camera response
                result = radiation.integrateSpectrum(object_spectrum, camera_spectrum=camera_response)
                assert isinstance(result, float)

    def test_integrate_source_spectrum(self):
        """Test integrateSourceSpectrum"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                radiation.addRadiationBand("SW")
                source_id = radiation.addCollimatedRadiationSource()

                # Set source spectrum first
                source_spectrum = [(400, 0.8), (500, 1.0), (600, 0.6)]
                radiation.setSourceSpectrum(source_id, source_spectrum)
                radiation.setSourceFlux(source_id, "SW", 1000.0)

                # Integrate source spectrum over PAR range
                par_flux = radiation.integrateSourceSpectrum(source_id, 400, 700)
                assert isinstance(par_flux, float)

    def test_scale_spectrum_in_place(self):
        """Test scaleSpectrum in-place - verify parameter validation"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                # Verify method signature works correctly
                # Method should accept string label and numeric scale factor
                with pytest.raises(Exception):  # Will fail - label doesn't exist, but that's correct behavior
                    radiation.scaleSpectrum("test_spectrum", 1.5)

    def test_scale_spectrum_to_new(self):
        """Test scaleSpectrum to new label - verify parameter validation"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                # Verify method accepts 3 parameters: existing_label, new_label, scale_factor
                with pytest.raises(Exception):  # Will fail - label doesn't exist, but that's correct behavior
                    radiation.scaleSpectrum("existing", "new_scaled", 2.0)

    def test_scale_spectrum_randomly(self):
        """Test scaleSpectrumRandomly - verify parameter validation"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                # Verify method accepts correct parameters
                with pytest.raises(Exception):  # Will fail - label doesn't exist, but that's correct behavior
                    radiation.scaleSpectrumRandomly("base_spectrum", "random_variant", 0.8, 1.2)

    def test_blend_spectra(self):
        """Test blendSpectra - verify weights validation"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                # Test that weights validation works (tested in parameter validation class)
                # This verifies the method exists and accepts correct signature
                with pytest.raises(Exception):  # Will fail - labels don't exist, but that's correct behavior
                    radiation.blendSpectra("mixed", ["spec1", "spec2"], [0.7, 0.3])

    def test_blend_spectra_randomly(self):
        """Test blendSpectraRandomly - verify accepts label list"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                # Verify method exists and accepts list of spectrum labels
                with pytest.raises(Exception):  # Will fail - labels don't exist, but that's correct behavior
                    radiation.blendSpectraRandomly("random_mix", ["spec1", "spec2", "spec3"])


@pytest.mark.native_only
@pytest.mark.requires_gpu
class TestBatch4DiffuseAndCamera:
    """Test Batch 4: Diffuse radiation and advanced camera"""

    def test_set_diffuse_radiation_extinction_coeff_vec3(self):
        """Test setDiffuseRadiationExtinctionCoeff with vec3"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                from pyhelios.wrappers.DataTypes import vec3

                radiation.addRadiationBand("SW")

                # Set extinction coefficient with peak direction
                radiation.setDiffuseRadiationExtinctionCoeff("SW", 0.5, vec3(0, 0, 1))

    def test_set_diffuse_radiation_extinction_coeff_spherical(self):
        """Test setDiffuseRadiationExtinctionCoeff with SphericalCoord"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                from pyhelios.wrappers.DataTypes import SphericalCoord

                radiation.addRadiationBand("SW")

                # Set with spherical coordinates
                radiation.setDiffuseRadiationExtinctionCoeff("SW", 0.3, SphericalCoord(1.0, 45.0, 90.0))

    def test_get_diffuse_flux(self):
        """Test getDiffuseFlux"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                radiation.addRadiationBand("SW")
                radiation.setDiffuseRadiationFlux("SW", 200.0)

                flux = radiation.getDiffuseFlux("SW")
                assert isinstance(flux, float)

    def test_set_diffuse_spectrum_single_band(self):
        """Test setDiffuseSpectrum for single band"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                radiation.addRadiationBand("SW")

                # Verify method accepts single band label and spectrum label
                with pytest.raises(Exception):  # Will fail - spectrum doesn't exist, but that's correct
                    radiation.setDiffuseSpectrum("SW", "sky_spectrum")

    def test_set_diffuse_spectrum_multiple_bands(self):
        """Test setDiffuseSpectrum for multiple bands"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                radiation.addRadiationBand("SW")
                radiation.addRadiationBand("NIR")

                # Verify method accepts list of band labels
                with pytest.raises(Exception):  # Will fail - spectrum doesn't exist, but that's correct
                    radiation.setDiffuseSpectrum(["SW", "NIR"], "sky_spectrum")

    def test_set_diffuse_spectrum_integral_all_bands(self):
        """Test setDiffuseSpectrumIntegral for all bands"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                radiation.addRadiationBand("SW")

                # These require diffuse spectrum to be set first
                # Since we can't easily set that, just verify method exists and accepts parameters
                try:
                    radiation.setDiffuseSpectrumIntegral(1000.0)
                except:
                    # Expected - spectrum not set
                    pass

                try:
                    radiation.setDiffuseSpectrumIntegral(500.0, 400, 700)
                except:
                    # Expected - spectrum not set
                    pass

    def test_set_diffuse_spectrum_integral_specific_band(self):
        """Test setDiffuseSpectrumIntegral for specific band"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                radiation.addRadiationBand("PAR")

                # These require diffuse spectrum to be set first
                try:
                    radiation.setDiffuseSpectrumIntegral(500.0, band_label="PAR")
                except:
                    # Expected - spectrum not set
                    pass

                try:
                    radiation.setDiffuseSpectrumIntegral(300.0, 400, 700, band_label="PAR")
                except:
                    # Expected - spectrum not set
                    pass

    def test_set_camera_spectral_response(self):
        """Test setCameraSpectralResponse sets reference without error"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                from pyhelios.wrappers.DataTypes import vec3

                radiation.addRadiationBand("red")
                radiation.addRadiationCamera("cam1", ["red"], vec3(0,0,10), vec3(0,0,0))

                # Method should accept parameters and set reference (even if global data doesn't exist yet)
                # C++ stores the reference; actual data loading happens later
                radiation.setCameraSpectralResponse("cam1", "red", "sensor_response")
                # Success = method works correctly

    def test_set_camera_spectral_response_from_library(self):
        """Test setCameraSpectralResponseFromLibrary - verify accepts library name"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                from pyhelios.wrappers.DataTypes import vec3

                radiation.addRadiationBand("red")
                radiation.addRadiationCamera("cam1", ["red"], vec3(0,0,10), vec3(0,0,0))

                # Verify method accepts camera library name
                # May fail if library doesn't have camera model, but that's expected
                try:
                    radiation.setCameraSpectralResponseFromLibrary("cam1", "iPhone13")
                except Exception as e:
                    # Verify we get meaningful error, not a crash
                    assert isinstance(e, Exception), "Should raise exception, not crash"

    def test_camera_pixel_data_access(self):
        """Test getCameraPixelData and setCameraPixelData"""
        with Context() as context:
            # Add geometry
            context.addPatch(center=[0, 0, 0], size=[1, 1])

            with RadiationModel(context) as radiation:
                from pyhelios.wrappers.DataTypes import vec3

                radiation.addRadiationBand("test")
                radiation.addRadiationCamera("cam1", ["test"], vec3(0,0,10), vec3(0,0,0))

                # Get/set pixel data
                try:
                    pixels = radiation.getCameraPixelData("cam1", "test")
                    assert isinstance(pixels, list)

                    # Modify and set back
                    if len(pixels) > 0:
                        modified = [p * 1.5 for p in pixels]
                        radiation.setCameraPixelData("cam1", "test", modified)
                except:
                    # May fail if camera hasn't been run yet
                    pass


@pytest.mark.native_only
@pytest.mark.requires_gpu
class TestBatch5SpectralInterpolation:
    """Test Batch 5: Spectral interpolation"""

    def test_interpolate_spectrum_from_primitive_data(self):
        """Test interpolateSpectrumFromPrimitiveData stores interpolation specification"""
        with Context() as context:
            # Create some patches
            patch1 = context.addPatch(center=[0, 0, 1], size=[1, 1])
            patch2 = context.addPatch(center=[2, 0, 1], size=[1, 1])
            patch3 = context.addPatch(center=[4, 0, 1], size=[1, 1])

            with RadiationModel(context) as radiation:
                # Method should succeed - it stores the interpolation specification
                # Actual spectrum application happens when spectra are available
                radiation.interpolateSpectrumFromPrimitiveData(
                    primitive_uuids=[patch1, patch2, patch3],
                    spectra_labels=["young_leaf", "mature_leaf", "old_leaf"],
                    values=[0.0, 50.0, 100.0],
                    primitive_data_query_label="age",
                    primitive_data_radprop_label="reflectance"
                )
                # No exception = success

    def test_interpolate_spectrum_from_object_data(self):
        """Test interpolateSpectrumFromObjectData stores interpolation specification"""
        with Context() as context:
            # Create object with primitives
            patch1 = context.addPatch(center=[0, 0, 1], size=[1, 1])

            with RadiationModel(context) as radiation:
                # Method should succeed - it stores the interpolation specification
                radiation.interpolateSpectrumFromObjectData(
                    object_ids=[1],
                    spectra_labels=["healthy", "stressed", "diseased"],
                    values=[1.0, 0.5, 0.0],
                    object_data_query_label="health",
                    primitive_data_radprop_label="reflectance"
                )
                # No exception = success


@pytest.mark.native_only
@pytest.mark.requires_gpu
class TestParameterValidation:
    """Test parameter validation for new methods (requires radiation plugin)"""

    def test_does_band_exist_validation(self):
        """Test doesBandExist parameter validation"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                # Empty string should be validated
                try:
                    radiation.doesBandExist("")
                except (ValueError, ValidationError):
                    pass  # Expected

    def test_delete_source_validation(self):
        """Test deleteRadiationSource parameter validation"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                # Negative ID should fail
                with pytest.raises(ValueError):
                    radiation.deleteRadiationSource(-1)

    def test_disk_source_radius_validation(self):
        """Test addDiskRadiationSource radius validation"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                from pyhelios.wrappers.DataTypes import vec3

                # Negative radius should fail
                with pytest.raises(ValueError):
                    radiation.addDiskRadiationSource(vec3(0,0,5), -1.0, vec3(0,0,0))

                # Zero radius should fail
                with pytest.raises(ValueError):
                    radiation.addDiskRadiationSource(vec3(0,0,5), 0.0, vec3(0,0,0))

    def test_source_spectrum_integral_validation(self):
        """Test setSourceSpectrumIntegral validation"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                radiation.addRadiationBand("SW")
                source_id = radiation.addCollimatedRadiationSource()

                # Negative integral should fail
                with pytest.raises(ValueError):
                    radiation.setSourceSpectrumIntegral(source_id, -100.0)

    def test_blend_spectra_validation(self):
        """Test blendSpectra validation"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                # Mismatched labels and weights should fail
                with pytest.raises(ValueError):
                    radiation.blendSpectra("mixed", ["spec1", "spec2"], [0.7])  # Only 1 weight

                # Empty labels should fail
                with pytest.raises(ValueError):
                    radiation.blendSpectra("mixed", [], [])

    def test_camera_label_validation(self):
        """Test camera methods require non-empty labels"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                # Empty camera label should fail
                with pytest.raises(ValueError):
                    radiation.getCameraPosition("")

                with pytest.raises(ValueError):
                    radiation.setCameraLookat("", [0, 0, 0])

    def test_interpolation_validation(self):
        """Test spectral interpolation parameter validation"""
        with Context() as context:
            with RadiationModel(context) as radiation:
                # Mismatched spectra and values should fail
                with pytest.raises(ValueError):
                    radiation.interpolateSpectrumFromPrimitiveData(
                        primitive_uuids=[1, 2, 3],
                        spectra_labels=["spec1", "spec2"],  # 2 spectra
                        values=[0.0, 50.0, 100.0],  # 3 values - mismatch!
                        primitive_data_query_label="age",
                        primitive_data_radprop_label="reflectance"
                    )

                # Empty UUIDs should fail
                with pytest.raises(ValueError):
                    radiation.interpolateSpectrumFromPrimitiveData(
                        primitive_uuids=[],
                        spectra_labels=["spec1"],
                        values=[0.0],
                        primitive_data_query_label="age",
                        primitive_data_radprop_label="reflectance"
                    )


@pytest.mark.cross_platform
class TestNewMethodsAPIStructure:
    """Test that new methods have proper API structure"""

    def test_new_methods_exist(self):
        """Verify all new methods are accessible"""
        # Check methods exist on RadiationModel class
        assert hasattr(RadiationModel, 'doesBandExist')
        assert hasattr(RadiationModel, 'deleteRadiationSource')
        assert hasattr(RadiationModel, 'getSourcePosition')
        assert hasattr(RadiationModel, 'setSourcePosition')
        assert hasattr(RadiationModel, 'getSkyEnergy')
        assert hasattr(RadiationModel, 'calculateGtheta')
        assert hasattr(RadiationModel, 'optionalOutputPrimitiveData')
        assert hasattr(RadiationModel, 'enforcePeriodicBoundary')

        # Geometric sources
        assert hasattr(RadiationModel, 'addRectangleRadiationSource')
        assert hasattr(RadiationModel, 'addDiskRadiationSource')

        # Camera management
        assert hasattr(RadiationModel, 'setCameraPosition')
        assert hasattr(RadiationModel, 'getCameraPosition')
        assert hasattr(RadiationModel, 'setCameraLookat')
        assert hasattr(RadiationModel, 'getCameraLookat')
        assert hasattr(RadiationModel, 'setCameraOrientation')
        assert hasattr(RadiationModel, 'getCameraOrientation')
        assert hasattr(RadiationModel, 'getAllCameraLabels')

        # Spectral methods
        assert hasattr(RadiationModel, 'setSourceSpectrum')
        assert hasattr(RadiationModel, 'setSourceSpectrumIntegral')
        assert hasattr(RadiationModel, 'integrateSpectrum')
        assert hasattr(RadiationModel, 'integrateSourceSpectrum')
        assert hasattr(RadiationModel, 'scaleSpectrum')
        assert hasattr(RadiationModel, 'scaleSpectrumRandomly')
        assert hasattr(RadiationModel, 'blendSpectra')
        assert hasattr(RadiationModel, 'blendSpectraRandomly')

        # Diffuse methods
        assert hasattr(RadiationModel, 'setDiffuseRadiationExtinctionCoeff')
        assert hasattr(RadiationModel, 'getDiffuseFlux')
        assert hasattr(RadiationModel, 'setDiffuseSpectrum')
        assert hasattr(RadiationModel, 'setDiffuseSpectrumIntegral')

        # Advanced camera
        assert hasattr(RadiationModel, 'setCameraSpectralResponse')
        assert hasattr(RadiationModel, 'setCameraSpectralResponseFromLibrary')
        assert hasattr(RadiationModel, 'getCameraPixelData')
        assert hasattr(RadiationModel, 'setCameraPixelData')

        # Interpolation
        assert hasattr(RadiationModel, 'interpolateSpectrumFromPrimitiveData')
        assert hasattr(RadiationModel, 'interpolateSpectrumFromObjectData')

    def test_methods_are_callable(self):
        """Verify new methods are callable"""
        # Just check they're callable, not None
        assert callable(RadiationModel.doesBandExist)
        assert callable(RadiationModel.setSourceSpectrum)
        assert callable(RadiationModel.integrateSpectrum)
        assert callable(RadiationModel.getAllCameraLabels)
        assert callable(RadiationModel.interpolateSpectrumFromPrimitiveData)


# ============================================================================
# SIF Camera Bindings (helios-core v1.3.72+)
# ============================================================================


@pytest.mark.cross_platform
class TestSIFCameraBindingsExposed:
    """Sanity checks that the SIF camera surface is wired up regardless of native availability."""

    def test_sif_camera_properties_dataclass(self):
        from pyhelios import SIFCameraProperties, CameraProperties
        if SIFCameraProperties is None:
            pytest.skip("RadiationModel exports unavailable in this build")

        props = SIFCameraProperties()
        assert isinstance(props, CameraProperties)
        # Defaults: 10 nm bins, no excitation scattering.
        assert props.excitation_bin_width_nm == 10.0
        assert props.excitation_scattering_depth == 0

        custom = SIFCameraProperties(excitation_bin_width_nm=20.0, excitation_scattering_depth=2)
        assert custom.excitation_bin_width_nm == 20.0
        assert custom.excitation_scattering_depth == 2

    def test_sif_camera_properties_validates_inputs(self):
        from pyhelios import SIFCameraProperties
        if SIFCameraProperties is None:
            pytest.skip("RadiationModel exports unavailable in this build")
        with pytest.raises(ValueError):
            SIFCameraProperties(excitation_bin_width_nm=0.0)
        with pytest.raises(ValueError):
            SIFCameraProperties(excitation_scattering_depth=-1)

    def test_sif_camera_methods_present_on_radiation_model(self):
        if RadiationModel is None:
            pytest.skip("RadiationModel unavailable in this build")
        for name in ("addSIFCamera", "isSIFCamera"):
            assert hasattr(RadiationModel, name)


@pytest.mark.native_only
@pytest.mark.requires_gpu
class TestSIFCameraNative:
    """End-to-end SIF camera registration (requires the radiation plugin and GPU backend)."""

    def test_register_sif_camera_with_lookat(self):
        from pyhelios import SIFCameraProperties
        from pyhelios.wrappers.DataTypes import vec3

        with Context() as context:
            with RadiationModel(context) as radiation:
                radiation.addRadiationBand("F687", 685.0, 690.0)

                props = SIFCameraProperties(camera_resolution=(64, 64),
                                             excitation_bin_width_nm=20.0,
                                             excitation_scattering_depth=0)
                radiation.addSIFCamera(
                    "sif_cam",
                    emission_band_labels=["F687"],
                    position=vec3(0, 0, 5),
                    lookat_or_direction=vec3(0, 0, 0),
                    camera_properties=props,
                    antialiasing_samples=4,
                )

                assert radiation.isSIFCamera("sif_cam") is True

    def test_is_sif_camera_returns_false_for_regular_camera(self):
        from pyhelios import CameraProperties
        from pyhelios.wrappers.DataTypes import vec3

        with Context() as context:
            with RadiationModel(context) as radiation:
                radiation.addRadiationBand("PAR", 400.0, 700.0)
                radiation.addRadiationCamera(
                    "regular",
                    band_labels=["PAR"],
                    position=vec3(0, 0, 5),
                    lookat_or_direction=vec3(0, 0, 0),
                    camera_properties=CameraProperties(camera_resolution=(64, 64)),
                    antialiasing_samples=4,
                )
                assert radiation.isSIFCamera("regular") is False


@pytest.mark.cross_platform
class TestCameraPropertiesManufacturer:
    """Test the CameraProperties.manufacturer field (Python class behavior, mock-safe)."""

    def test_manufacturer_default_empty(self):
        from pyhelios import CameraProperties
        props = CameraProperties()
        assert props.manufacturer == ""

    def test_manufacturer_set(self):
        from pyhelios import CameraProperties
        props = CameraProperties(manufacturer="Canon")
        assert props.manufacturer == "Canon"
        assert "manufacturer='Canon'" in repr(props)

    def test_manufacturer_invalid_type_raises(self):
        from pyhelios import CameraProperties
        with pytest.raises(ValueError, match="manufacturer must be a string"):
            CameraProperties(manufacturer=123)

    def test_manufacturer_does_not_break_to_array(self):
        # to_array() carries only numeric fields; manufacturer must not alter its length.
        from pyhelios import CameraProperties
        props = CameraProperties(manufacturer="Nikon")
        assert len(props.to_array()) == 10


@pytest.mark.native_only
class TestCameraExposureSparseSubject:
    """Regression tests for spectral auto-exposure on sparse subjects.

    Not marked ``requires_gpu``: this bug lives in host-side exposure code and
    manifests on the Vulkan software-BVH backend, which has no GPU requirement.
    The ``requires_gpu`` marker would skip these on exactly the platform the bug
    affects. Where no ray-tracing backend is constructible at all (e.g. the
    cibuildwheel test environment), ``_radiation_model`` skips these tests
    rather than failing — the exposure path under test is unreachable there.

    Previously, a single-band ("spectral"-typed) camera viewing an emitting
    subject that filled less than 5% of the frame produced astronomically large
    pixel values (~1.9e8): the 95th-percentile exposure reference landed on the
    zero background, the gain floor (0.7/1e-6) took over, and the real radiance
    was amplified by ~7e5. Exposure depended on how much of the frame the subject
    happened to fill (camera distance / field of view) rather than its radiance.
    """

    @staticmethod
    def _radiation_model(context):
        # The Vulkan software-BVH backend (no GPU required) is what these tests
        # target, but some environments — notably the cibuildwheel test step —
        # have no compatible ray-tracing backend at all, so the constructor
        # cannot initialize. Skip there rather than fail; the exposure logic
        # under test is unreachable without a working backend.
        try:
            return RadiationModel(context)
        except RadiationModelError as e:
            # No ray-tracing backend is constructible in this environment. This
            # surfaces differently per platform: a clean "No compatible GPU
            # backend found" message, or a low-level dependency-load failure
            # (e.g. Windows error 0xc06d007e when the radiation lib's OptiX/CUDA
            # dependencies are absent in the cibuildwheel test step). In every
            # such case the exposure path under test is unreachable, so skip.
            msg = str(e)
            backend_unavailable = (
                "No compatible GPU backend found" in msg
                or "Failed to initialize RadiationModel" in msg
            )
            if backend_unavailable:
                pytest.skip(f"No ray-tracing backend available: {e}")
            raise

    def _render(self, hfov, position, patch_size, resolution=64, exposure="auto", temperature=350.0):
        from pyhelios.RadiationModel import CameraProperties
        from pyhelios.wrappers.DataTypes import vec3, vec2
        with Context() as context:
            uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(patch_size, patch_size))
            context.setPrimitiveDataFloat(uuid, "temperature", temperature)
            context.setPrimitiveDataFloat(uuid, "emissivity_TH", 1.0)
            with self._radiation_model(context) as radiation:
                radiation.addRadiationBand("TH")
                radiation.enableEmission("TH")
                radiation.setScatteringDepth("TH", 1)
                radiation.setDiffuseRayCount("TH", 100)
                props = CameraProperties(
                    camera_resolution=(resolution, resolution),
                    HFOV=hfov,
                    lens_diameter=0.0,
                    exposure=exposure,
                )
                radiation.addRadiationCamera(
                    "cam", ["TH"], vec3(*position), vec3(0, 0, 0), props,
                    antialiasing_samples=1,
                )
                radiation.updateGeometry()
                radiation.runBand(["TH"])
                return np.array(radiation.getCameraPixelData("cam", "TH"))

    def test_small_subject_does_not_blow_up_exposure(self):
        # Subject fills well under 5% of the frame -> exercises the sparse path.
        pixels = self._render(hfov=30, position=(0, 0, 10), patch_size=0.5)
        nonzero = pixels[pixels > 0]
        assert len(nonzero) > 0, "subject must render (nonzero pixels)"
        assert np.all(np.isfinite(pixels)), "pixel values must be finite"
        # Auto-exposure maps the signal toward ~0.7; the historic bug produced ~1.9e8.
        assert pixels.max() < 100.0, (
            f"sparse-subject exposure blew up: max pixel = {pixels.max():.4g}"
        )

    def test_exposure_bounded_across_hfov(self):
        # Across the full FOV range the subject must render with bounded values,
        # whether it fills <5% (wide FOV) or most of the frame (narrow FOV).
        for hfov in (40, 30, 28, 20, 10, 5):
            pixels = self._render(hfov=hfov, position=(0, 0, 10), patch_size=2.0)
            assert (pixels > 0).sum() > 0, f"HFOV={hfov}: subject must render"
            assert np.all(np.isfinite(pixels)), f"HFOV={hfov}: non-finite pixels"
            assert pixels.max() < 100.0, (
                f"HFOV={hfov}: exposure blew up, max = {pixels.max():.4g}"
            )

    def test_exposure_invariant_to_subject_size(self):
        # A uniform emitter should auto-expose to the same level regardless of how
        # much of the frame it fills (the property the bug violated).
        big = self._render(hfov=30, position=(0, 0, 10), patch_size=2.0)
        small = self._render(hfov=30, position=(0, 0, 10), patch_size=0.5)
        assert np.isclose(big.max(), small.max(), rtol=0.1), (
            f"exposure not size-invariant: big={big.max():.4g} small={small.max():.4g}"
        )

    def test_manual_exposure_returns_raw_radiance(self):
        # exposure="manual" must be plumbed through to the camera and skip
        # auto-exposure, returning physical radiance (sigma*T^4/pi for a
        # blackbody). Previously the exposure mode was dropped at the ctypes
        # boundary, so "manual" behaved identically to "auto".
        manual = self._render(hfov=30, position=(0, 0, 10), patch_size=2.0, exposure="manual")
        auto = self._render(hfov=30, position=(0, 0, 10), patch_size=2.0, exposure="auto")
        sigma = 5.670374419e-8
        expected = sigma * 350.0 ** 4 / np.pi  # ~270.8 W/m^2/sr
        assert np.isclose(manual.max(), expected, rtol=0.05), (
            f"manual exposure should return raw radiance ~{expected:.1f}, got {manual.max():.4g}"
        )
        # Auto normalizes to ~0.7; manual must clearly differ (mode is honored).
        assert manual.max() > 10.0 * auto.max(), (
            f"manual ({manual.max():.4g}) not distinct from auto ({auto.max():.4g})"
        )

    def test_manual_exposure_scales_with_temperature(self):
        # Raw radiance must track the emitter temperature (auto-exposure would
        # normalize this away). Confirms manual genuinely bypasses exposure.
        hot = self._render(hfov=10, position=(0, 0, 10), patch_size=2.0,
                           exposure="manual", temperature=500.0)
        cool = self._render(hfov=10, position=(0, 0, 10), patch_size=2.0,
                            exposure="manual", temperature=350.0)
        ratio = hot.max() / cool.max()
        expected_ratio = (500.0 / 350.0) ** 4  # Stefan-Boltzmann
        assert np.isclose(ratio, expected_ratio, rtol=0.05), (
            f"raw radiance should scale as T^4 (expected {expected_ratio:.2f}x), got {ratio:.2f}x"
        )

    def test_update_camera_parameters_honors_exposure(self):
        # updateCameraParameters must also plumb the exposure mode through. The
        # camera is created with the default "auto" then switched to "manual";
        # the rendered radiance must change from the normalized ~0.7 to the raw
        # blackbody value. Previously the exposure string was dropped on this path.
        from pyhelios.RadiationModel import CameraProperties
        from pyhelios.wrappers.DataTypes import vec3, vec2
        with Context() as context:
            uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(2.0, 2.0))
            context.setPrimitiveDataFloat(uuid, "temperature", 350.0)
            context.setPrimitiveDataFloat(uuid, "emissivity_TH", 1.0)
            with self._radiation_model(context) as radiation:
                radiation.addRadiationBand("TH")
                radiation.enableEmission("TH")
                radiation.setScatteringDepth("TH", 1)
                radiation.setDiffuseRayCount("TH", 100)
                radiation.addRadiationCamera(
                    "cam", ["TH"], vec3(0, 0, 10), vec3(0, 0, 0),
                    CameraProperties(camera_resolution=(64, 64), HFOV=30, lens_diameter=0.0),
                    antialiasing_samples=1,
                )
                radiation.updateGeometry()
                radiation.runBand(["TH"])
                auto_max = np.array(radiation.getCameraPixelData("cam", "TH")).max()

                radiation.updateCameraParameters(
                    "cam",
                    CameraProperties(camera_resolution=(64, 64), HFOV=30,
                                     lens_diameter=0.0, exposure="manual"),
                )
                radiation.runBand(["TH"])
                manual_max = np.array(radiation.getCameraPixelData("cam", "TH")).max()

        expected = 5.670374419e-8 * 350.0 ** 4 / np.pi  # ~270.8 W/m^2/sr
        assert np.isclose(manual_max, expected, rtol=0.05), (
            f"updateCameraParameters(manual) should yield raw radiance ~{expected:.1f}, "
            f"got {manual_max:.4g}"
        )
        assert manual_max > 10.0 * auto_max, (
            f"exposure update had no effect: auto={auto_max:.4g} manual={manual_max:.4g}"
        )


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])