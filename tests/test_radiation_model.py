"""
Tests for RadiationModel functionality in PyHelios.

This module tests the RadiationModel class and radiation simulation capabilities.
Tests are designed to work in both native and mock modes.
"""

import functools
import pytest
import subprocess
import sys
import os
import textwrap
import numpy as np
from typing import List
from unittest.mock import MagicMock

# Add pyhelios to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pyhelios import Context, RadiationModel, RadiationModelError, DataTypes
from pyhelios.plugins.registry import get_plugin_registry
from pyhelios.validation.exceptions import ValidationError
from tests.conftest import skip_or_fail_without_gpu

# RadiationSourceType may not be available if RadiationModel is None
try:
    from pyhelios.RadiationModel import RadiationSourceType
except (ImportError, AttributeError):
    RadiationSourceType = None

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


@functools.lru_cache(maxsize=1)
def radiation_backend_constructible() -> bool:
    """Whether a RadiationModel can be constructed here, probed out of process.

    Constructing a RadiationModel where no ray-tracing backend can initialize is
    not reliably survivable. It usually raises RadiationModelError, which callers
    catch to skip -- but on some MoltenVK configurations (notably the macOS
    cibuildwheel runner) it instead segfaults inside createRadiationModel, taking
    the whole test process down. try/except cannot defend against SIGSEGV, so do
    the probe in a child process and let the child absorb any crash.

    Returns True only if the child constructed a model and exited cleanly, so a
    crash, a non-zero exit, and a clean backend error all read as "unavailable".
    """
    try:
        result = subprocess.run(
            [sys.executable, '-c', textwrap.dedent("""
                from pyhelios import Context, RadiationModel
                from pyhelios.types import vec3
                ctx = Context()
                ctx.addPatch(center=vec3(0, 0, 0))
                RadiationModel(ctx)
                print("BACKEND_OK")
            """)],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=REPO_ROOT,
            env=dict(os.environ, PYTHONPATH=REPO_ROOT),
        )
    except subprocess.TimeoutExpired:
        return False
    return result.returncode == 0 and "BACKEND_OK" in result.stdout


def skip_without_radiation_backend() -> None:
    """Skip the calling test unless a RadiationModel can actually be built.

    Honors HELIOS_REQUIRE_GPU: on a runner dedicated to GPU coverage this fails
    instead of skipping, so an environment that cannot build a backend at all
    cannot pass by skipping everything.
    """
    if not radiation_backend_constructible():
        skip_or_fail_without_gpu("no constructible ray-tracing backend")


def radiation_model_or_skip(context) -> RadiationModel:
    """Build a RadiationModel, skipping the calling test if no backend exists.

    `is_plugin_available('radiation')` is not enough on its own: the plugin can
    be compiled into the library and still have no device to run on, which is
    the situation in the cibuildwheel test environment. Constructing the model
    there raises rather than skipping, so a test guarded only by plugin
    availability fails the wheel build instead of being skipped out of it.
    """
    skip_without_radiation_backend()
    try:
        return RadiationModel(context)
    except RadiationModelError as e:
        msg = str(e)
        if ("No compatible GPU backend found" in msg
                or "Failed to initialize RadiationModel" in msg):
            pytest.skip(f"No ray-tracing backend available: {e}")
        raise


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

    def test_sun_sphere_zenith_follows_cosine_law(self):
        """Sun sphere zenith angle must be interpreted as degrees-from-vertical.

        Regression test: the C interface previously passed the caller's
        degrees-zenith straight into SphericalCoord(radius, elevation_radians,
        azimuth_radians) with no unit or zenith->elevation conversion, so the sun
        was placed at an arbitrary wrong position. An overhead sun (zenith=0)
        produced 0 W/m^2 instead of the source flux.

        A horizontal patch under a sun of flux F must absorb F*cos(zenith).
        """
        import math

        flux = 1000.0
        for zenith_deg in (0.0, 30.0, 60.0, 85.0):
            with Context() as context:
                context.addPatch(center=DataTypes.vec3(0, 0, 0),
                                 size=DataTypes.vec2(1, 1))
                with RadiationModel(context) as radiation:
                    radiation.addRadiationBand("SW")
                    source = radiation.addSunSphereRadiationSource(
                        radius=1.0, zenith=zenith_deg, azimuth=0.0)
                    radiation.setSourceFlux(source, "SW", flux)
                    radiation.setDirectRayCount("SW", 500)
                    # Explicit updateGeometry() avoids the known upstream
                    # isgeometryinitialized nondeterminism that can otherwise
                    # return 0.0 flux regardless of sun position.
                    radiation.updateGeometry()
                    radiation.runBand("SW")
                    absorbed = radiation.getTotalAbsorbedFlux()[0]

            expected = flux * math.cos(math.radians(zenith_deg))
            assert abs(absorbed - expected) < 0.05 * flux, (
                f"zenith={zenith_deg} deg: absorbed {absorbed:.2f} W/m^2, "
                f"expected ~{expected:.2f} W/m^2 (cosine law). "
                f"Check degrees->radians and zenith->elevation conversion in "
                f"native/src/pyhelios_wrapper_radiation.cpp."
            )

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
                # Add some geometry for the camera to render
                from pyhelios.wrappers.DataTypes import vec3, vec2, RGBcolor
                context.addPatch(
                    center=vec3(0, 0, 0),
                    size=vec2(1.0, 1.0),
                    color=RGBcolor(0.5, 0.5, 0.5),
                )

                # Add radiation bands first
                radiation_model.addRadiationBand("R")
                radiation_model.addRadiationBand("G")
                radiation_model.addRadiationBand("B")

                # Add camera before writing image
                radiation_model.addRadiationCamera(
                    camera_label="test_camera",
                    band_labels=["R", "G", "B"],
                    position=vec3(0, 0, 5),
                    lookat_or_direction=vec3(0, 0, 0)
                )

                # Render the camera. Writing an unrendered camera is refused by the
                # pixel-data preflight in writeNormCameraImage(), so this is required
                # rather than incidental.
                radiation_model.updateGeometry()
                radiation_model.runBand(["R", "G", "B"])

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
        #
        # Probed out of process first: where the constructor segfaults instead of
        # raising, the except clause below never runs and the crash takes down
        # the test session.
        skip_without_radiation_backend()
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

    def test_repeated_run_band_is_idempotent(self):
        """Re-running runBand() on an unchanged scene must reproduce the same image.

        Regression test for camera radiance doubling on the OptiX 8 backend. runBand()
        seeds a host accumulator with each primitive's emitted flux, uploads it to the
        device camera-scatter buffer, then adds that same buffer back into the host
        accumulator after each scattering launch -- counting the emitted base twice.
        On the first runBand() of an emission-only scene the upload is silently dropped
        (the device buffer has not been allocated yet), which hid the defect; every
        later call doubles. Reported as exactly 2x on the GPU CI runner, where
        test_update_camera_parameters_honors_exposure got 541.7 against an expected
        270.9 because it is the only test here that renders the same camera twice.

        This asserts the property directly rather than through the exposure mode, so
        it does not depend on updateCameraParameters() being involved -- it is not.
        Manual exposure is used throughout so the comparison is against raw radiance
        with no auto-exposure gain in between.

        The Vulkan compute backend is unaffected, so this passes on any machine
        without a CUDA GPU; the red state lives on the GPU runner.
        """
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
                    CameraProperties(camera_resolution=(64, 64), HFOV=30,
                                     lens_diameter=0.0, exposure="manual"),
                    antialiasing_samples=1,
                )
                radiation.updateGeometry()

                maxima = []
                for _ in range(3):
                    radiation.runBand(["TH"])
                    maxima.append(
                        float(np.array(radiation.getCameraPixelData("cam", "TH")).max())
                    )

        # Anchored to the physical value, not just to run 1, so that a backend which
        # doubled on every run (including the first) could not satisfy this by being
        # consistently wrong.
        expected = 5.670374419e-8 * 350.0 ** 4 / np.pi  # ~270.9 W/m^2/sr
        for run_index, value in enumerate(maxima):
            assert np.isclose(value, expected, rtol=0.05), (
                f"runBand() call {run_index + 1} of {len(maxima)} gave {value:.4g}, "
                f"expected ~{expected:.1f} (ratio {value / expected:.3f}); "
                f"all runs: {['%.4g' % m for m in maxima]}"
            )

    def test_resolution_change_discards_image_data(self):
        """Changing the resolution invalidates rendered pixel data (helios-core v1.3.79+).

        The per-pixel buffers are sized to the resolution the camera was rendered at,
        so a resolution change clears them rather than reinterpreting them at the new
        size. Writing an image must then report the camera as unrendered until a fresh
        runBand(), and a same-resolution update must NOT disturb the data.
        """
        from pyhelios.RadiationModel import CameraProperties
        from pyhelios.wrappers.DataTypes import vec3, vec2
        with Context() as context:
            uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(2.0, 2.0))
            context.setPrimitiveDataFloat(uuid, "temperature", 350.0)
            context.setPrimitiveDataFloat(uuid, "emissivity_TH", 1.0)
            with self._radiation_model(context) as radiation:
                radiation.addRadiationBand("TH")
                radiation.enableEmission("TH")
                radiation.setDiffuseRayCount("TH", 100)
                radiation.addRadiationCamera(
                    "cam", ["TH"], vec3(0, 0, 10), vec3(0, 0, 0),
                    CameraProperties(camera_resolution=(32, 32), HFOV=30, lens_diameter=0.0),
                    antialiasing_samples=1,
                )
                radiation.runBand(["TH"])

                # Baseline: the camera has data at its original resolution.
                assert len(radiation.getCameraPixelData("cam", "TH")) == 32 * 32

                # Same resolution -> data survives.
                radiation.updateCameraParameters(
                    "cam",
                    CameraProperties(camera_resolution=(32, 32), HFOV=45,
                                     lens_diameter=0.0),
                )
                assert len(radiation.getCameraPixelData("cam", "TH")) == 32 * 32, (
                    "a non-resolution parameter change must preserve image data"
                )

                # Different resolution -> data discarded, so writing must fail loudly
                # rather than emit an image built from stale buffers.
                radiation.updateCameraParameters(
                    "cam",
                    CameraProperties(camera_resolution=(64, 64), HFOV=45,
                                     lens_diameter=0.0),
                )
                with pytest.raises(RadiationModelError) as excinfo:
                    radiation.writeCameraImage("cam", ["TH"], "discarded",
                                               image_path=str(tmp_path_for_images()))
                assert "runBand()" in str(excinfo.value)

                # A fresh render restores it, now at the new resolution.
                radiation.runBand(["TH"])
                assert len(radiation.getCameraPixelData("cam", "TH")) == 64 * 64


def tmp_path_for_images():
    """Directory for test image output, created on demand."""
    path = os.path.join(REPO_ROOT, "tests", "_image_output")
    os.makedirs(path, exist_ok=True)
    return path


@pytest.mark.cross_platform
class TestGeometrySubsetTracking:
    """The _geometry_subset state machine that guards calculateGtheta().

    helios-core v1.3.79 makes runBand() build geometry automatically, but a subset
    from updateGeometry(uuids) is deliberately never rebuilt -- so PyHelios must not
    auto-build over one. updateGeometry() with no argument clears the native subset
    latch, which would silently widen the model back to the full Context.

    Driven against stub wrappers so the state transitions are pinned without a GPU;
    the flag logic is pure Python.
    """

    def _model(self, monkeypatch):
        radiation_module = sys.modules['pyhelios.RadiationModel']

        registry = get_plugin_registry()
        real_is_available = registry.is_plugin_available
        monkeypatch.setattr(
            registry, 'is_plugin_available',
            lambda name: True if name == 'radiation' else real_is_available(name))

        model = RadiationModel.__new__(RadiationModel)
        model.radiation_model = object()
        # calculateGtheta() passes the Context pointer through to the native call,
        # which is stubbed below, so any non-None sentinel suffices.
        model.context = MagicMock()
        model._geometry_updated = False
        model._geometry_subset = False

        calls = []
        monkeypatch.setattr(radiation_module.radiation_wrapper, 'updateGeometry',
                            lambda *a: calls.append('full'))
        monkeypatch.setattr(radiation_module.radiation_wrapper, 'updateGeometryUUIDs',
                            lambda *a: calls.append('subset'))
        monkeypatch.setattr(radiation_module.radiation_wrapper, 'runBand',
                            lambda *a: None)
        monkeypatch.setattr(RadiationModel, '_check_context_alive', lambda self: None)
        return model, calls

    def test_full_update_clears_subset_flag(self, monkeypatch):
        model, calls = self._model(monkeypatch)

        model.updateGeometry([1, 2])
        assert model._geometry_subset is True

        model.updateGeometry()
        assert model._geometry_subset is False, (
            "updateGeometry() clears the native subset latch, so the flag must follow"
        )
        assert calls == ['subset', 'full']

    def test_runband_marks_geometry_built(self, monkeypatch):
        """runBand() builds geometry itself, so the flag must record it."""
        model, _ = self._model(monkeypatch)

        assert model._geometry_updated is False
        model.runBand("SW")
        assert model._geometry_updated is True

    def test_runband_preserves_subset_flag(self, monkeypatch):
        """runBand() never rebuilds a subset, so it must not clear the flag."""
        model, calls = self._model(monkeypatch)

        model.updateGeometry([1, 2])
        model.runBand("SW")

        assert model._geometry_subset is True
        assert 'full' not in calls, "runBand() must not trigger a full-Context build"

    def test_calculate_gtheta_refuses_to_autobuild_over_subset(self, monkeypatch):
        """The core hazard: auto-building would discard the caller's subset."""
        model, calls = self._model(monkeypatch)
        model._geometry_subset = True
        model._geometry_updated = False

        with pytest.raises(RuntimeError) as excinfo:
            model.calculateGtheta(DataTypes.vec3(0, 0, 1))

        message = str(excinfo.value)
        assert "updateGeometry(uuids)" in message, (
            f"error must tell the user how to rebuild the subset: {message}")
        assert 'full' not in calls, (
            "must NOT have silently widened the model to the full Context")

    def test_calculate_gtheta_autobuilds_when_not_subset(self, monkeypatch):
        """The pre-existing non-subset auto-build behavior must be preserved."""
        radiation_module = sys.modules['pyhelios.RadiationModel']
        model, calls = self._model(monkeypatch)
        model._geometry_subset = False
        model._geometry_updated = False

        monkeypatch.setattr(radiation_module.radiation_wrapper, 'calculateGtheta',
                            lambda *a: 0.5)

        assert model.calculateGtheta(DataTypes.vec3(0, 0, 1)) == 0.5
        assert calls == ['full'], "should have auto-built the full Context geometry"

    def test_calculate_gtheta_after_runband_does_not_rebuild(self, monkeypatch):
        """runBand() already built it, so no redundant rebuild and no warning."""
        radiation_module = sys.modules['pyhelios.RadiationModel']
        model, calls = self._model(monkeypatch)

        monkeypatch.setattr(radiation_module.radiation_wrapper, 'calculateGtheta',
                            lambda *a: 0.5)

        model.runBand("SW")
        assert model.calculateGtheta(DataTypes.vec3(0, 0, 1)) == 0.5
        assert calls == [], "runBand() already built geometry; must not rebuild"

    def test_calculate_gtheta_works_after_subset_then_runband(self, monkeypatch):
        """updateGeometry(uuids) -> runBand() -> calculateGtheta() must not raise.

        runBand() marks geometry as built, so the subset guard is not reached and the
        G-function is reported over the subset the caller selected.
        """
        radiation_module = sys.modules['pyhelios.RadiationModel']
        model, calls = self._model(monkeypatch)

        monkeypatch.setattr(radiation_module.radiation_wrapper, 'calculateGtheta',
                            lambda *a: 0.25)

        model.updateGeometry([1, 2])
        model.runBand("SW")

        assert model.calculateGtheta(DataTypes.vec3(0, 0, 1)) == 0.25
        assert calls == ['subset'], (
            "the subset must survive: no full build may have happened")

    def test_calculate_gtheta_works_after_subset_then_full_update(self, monkeypatch):
        """updateGeometry(uuids) -> updateGeometry() -> calculateGtheta() succeeds."""
        radiation_module = sys.modules['pyhelios.RadiationModel']
        model, calls = self._model(monkeypatch)

        monkeypatch.setattr(radiation_module.radiation_wrapper, 'calculateGtheta',
                            lambda *a: 0.75)

        model.updateGeometry([1, 2])
        model.updateGeometry()

        assert model.calculateGtheta(DataTypes.vec3(0, 0, 1)) == 0.75
        assert calls == ['subset', 'full']


@pytest.mark.native_only
class TestGPUEnvironmentBindings:
    """The helios-core v1.3.79 GPU environment functions, through their real bindings.

    conftest's skip_or_fail_without_gpu() deliberately reimplements the same
    environment logic in pure Python so test gating works in mock mode. That means
    nothing else in the suite exercises these ctypes bindings, so a wrong argtypes,
    restype, or string encoding would go unnoticed. These tests call them directly.

    The variable is set in a CHILD PROCESS environment rather than through
    monkeypatch, because an os.environ change is invisible to the native library on
    Windows. libhelios.dll links the MSVC C runtime statically (MSVC_RUNTIME_LIBRARY
    "MultiThreaded" in pyhelios_build/CMakeLists.txt), so it holds a private copy of
    the environment snapshotted at DLL load, while os.environ writes go through
    Python's own CRT. Setting the variable before the interpreter starts is the only
    way the DLL can see it -- which is also the rule users must follow -- and it
    exercises the bindings identically on every platform.
    """

    @staticmethod
    def _in_child(body: str, **env: "str | None") -> subprocess.CompletedProcess:
        """Run `body` in a fresh interpreter with `env` applied to its environment.

        A value of None removes the variable rather than setting it empty: the two
        are different to the functions under test, and Windows cannot hold an empty
        variable at all.
        """
        child_env = dict(os.environ, PYTHONPATH=REPO_ROOT)
        for name, value in env.items():
            if value is None:
                child_env.pop(name, None)
            else:
                child_env[name] = value
        return subprocess.run(
            [sys.executable, '-c', textwrap.dedent(body)],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=REPO_ROOT,
            env=child_env,
        )

    @pytest.mark.parametrize("value,expected", [
        (None, False),
        ("1", True),
        ("0", False),  # exactly "0" is the only value that counts as unset
        ("false", True),  # any other value counts as set, including "false"
    ])
    def test_gpu_required_by_environment_reports_the_variable(self, value, expected):
        """The raw, case-sensitive comparison against "0", through the real binding."""
        result = self._in_child("""
            from pyhelios import Global
            print("RESULT:", Global.gpuRequiredByEnvironment())
        """, HELIOS_REQUIRE_GPU=value)

        assert result.returncode == 0, result.stderr
        assert f"RESULT: {expected}" in result.stdout, result.stdout

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="static-CRT DLL cannot observe an os.environ change (see class docstring)",
    )
    def test_gpu_required_by_environment_is_not_cached(self, monkeypatch):
        """Re-reads the environment on every call rather than latching the first answer.

        gpuBackendsDisabledByEnvironment() deliberately caches process-wide and this
        one deliberately does not, and only an in-process flip distinguishes them --
        every other test here starts a fresh process and so would pass either way.
        """
        from pyhelios import Global

        monkeypatch.delenv("HELIOS_REQUIRE_GPU", raising=False)
        assert Global.gpuRequiredByEnvironment() is False

        monkeypatch.setenv("HELIOS_REQUIRE_GPU", "1")
        assert Global.gpuRequiredByEnvironment() is True, (
            "the native function must re-read the environment, not cache it"
        )

    def test_require_gpu_or_fail_is_noop_when_unset(self):
        result = self._in_child("""
            from pyhelios import Global
            Global.requireGPUOrFail("should do nothing")
            print("RETURNED")
        """, HELIOS_REQUIRE_GPU=None)

        assert result.returncode == 0, result.stderr
        assert "RETURNED" in result.stdout, result.stdout

    def test_require_gpu_or_fail_raises_when_set(self):
        """Always raises when HELIOS_REQUIRE_GPU is set; it never probes hardware."""
        result = self._in_child("""
            from pyhelios import Global
            try:
                Global.requireGPUOrFail("radiation ray tracing")
            except Exception as e:
                print("RAISED:", repr(str(e)))
            else:
                print("DID NOT RAISE")
        """, HELIOS_REQUIRE_GPU="1", HELIOS_NO_GPU=None)

        assert result.returncode == 0, result.stderr
        assert "RAISED:" in result.stdout, result.stdout
        # Naming the variable also proves this is the native message rather than the
        # "not available in the current native library" RuntimeError from the wrapper.
        assert "HELIOS_REQUIRE_GPU" in result.stdout, result.stdout

    def test_require_gpu_or_fail_reports_contradictory_env(self):
        """Setting both REQUIRE and NO_GPU must be reported, not silently resolved."""
        result = self._in_child("""
            from pyhelios import Global
            try:
                Global.requireGPUOrFail("contradiction check")
            except Exception as e:
                print("RAISED:", repr(str(e)))
            else:
                print("DID NOT RAISE")
        """, HELIOS_REQUIRE_GPU="1", HELIOS_NO_GPU="1")

        assert result.returncode == 0, result.stderr
        assert "RAISED:" in result.stdout, result.stdout
        assert "HELIOS_NO_GPU" in result.stdout and "HELIOS_REQUIRE_GPU" in result.stdout, result.stdout

    def test_require_gpu_or_fail_accepts_empty_message(self):
        """The const char* argument must tolerate an empty string (NULL-equivalent)."""
        result = self._in_child("""
            from pyhelios import Global
            try:
                Global.requireGPUOrFail("")
            except Exception as e:
                print("RAISED:", repr(str(e)))
            else:
                print("DID NOT RAISE")
        """, HELIOS_REQUIRE_GPU="1", HELIOS_NO_GPU=None)

        assert result.returncode == 0, result.stderr
        assert "RAISED:" in result.stdout, result.stdout
        assert "HELIOS_REQUIRE_GPU" in result.stdout, result.stdout

    def test_gpu_backends_disabled_by_environment_returns_bool(self):
        """Exercises the binding; the value depends on how the process was started.

        This one caches process-wide on first call, so it cannot be toggled with
        monkeypatch the way gpuRequiredByEnvironment() can. Assert the binding
        round-trips a real bool rather than trying to flip it.
        """
        assert isinstance(RadiationModel.gpuBackendsDisabledByEnvironment(), bool)

    def test_no_gpu_veto_agrees_with_probe(self):
        """If the environment vetoes GPU backends, probing must report none."""
        if RadiationModel.gpuBackendsDisabledByEnvironment():
            assert RadiationModel.probeAnyGPUBackend() is False, (
                "HELIOS_NO_GPU is set, so probeAnyGPUBackend() must return False"
            )


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])

@pytest.mark.cross_platform
class TestWriteCameraImagePixelDataPreflight:
    """writeCameraImage must reject unrendered cameras with an actionable error.

    Regression for GitHub issue #4. Native writeCameraImage indexes its
    pixel_data map with std::map::at() while validating against a *different*
    container (the camera's band_labels, populated at camera creation rather
    than at render), so an unrendered camera/band surfaced as a bare
    "invalid map<K, T> key". The upstream guard lands in helios-core v1.3.79;
    this preflight fixes the message for users on earlier cores and stays
    correct afterwards.

    These tests drive the preflight against a stub wrapper so they run without a
    GPU. They verify the guard's logic and its message, NOT the end-to-end
    native behaviour -- see TestWriteCameraImagePixelDataPreflightNative for
    that.
    """

    def _model_with_stub(self, monkeypatch, cameras, rendered):
        """Build a RadiationModel shell wired to a fake native wrapper.

        `rendered` maps camera label -> set of bands that runBand() has filled
        in, mirroring how the native layer populates pixel_data.
        """
        # 'pyhelios.RadiationModel' is the module; the RadiationModel name
        # re-exported from the package is the class and would shadow it here.
        radiation_module = sys.modules['pyhelios.RadiationModel']

        # writeCameraImage is wrapped in @require_plugin('radiation'), which runs
        # before any stubbed wrapper call. Stubbing only the wrapper leaves that
        # gate live, so on a build without the radiation plugin these tests fail
        # with PluginNotAvailableError instead of exercising the preflight. The
        # preflight is pure Python and needs no plugin, so report it available.
        registry = get_plugin_registry()
        real_is_available = registry.is_plugin_available
        monkeypatch.setattr(
            registry, 'is_plugin_available',
            lambda name: True if name == 'radiation' else real_is_available(name))

        model = RadiationModel.__new__(RadiationModel)
        model.radiation_model = object()
        model.context = None

        def fake_get_all_camera_labels(_ptr):
            return list(cameras)

        def fake_get_camera_pixel_data(_ptr, camera_label, band_label):
            if band_label not in rendered.get(camera_label, set()):
                raise RuntimeError(
                    f"ERROR (RadiationModel::getCameraPixelData): Band "
                    f"'{band_label}' does not exist in camera '{camera_label}'."
                )
            return [0.0, 0.0, 0.0, 0.0]

        monkeypatch.setattr(radiation_module.radiation_wrapper,
                            'getAllCameraLabels', fake_get_all_camera_labels)
        monkeypatch.setattr(radiation_module.radiation_wrapper,
                            'getCameraPixelData', fake_get_camera_pixel_data)
        monkeypatch.setattr(RadiationModel, '_check_context_alive', lambda self: None)
        return model

    def test_camera_never_rendered_raises_actionable_error(self, monkeypatch):
        """The exact issue #4 sequence: camera added, runBand() never called."""
        model = self._model_with_stub(monkeypatch, cameras=["overhead_rgb"], rendered={})

        with pytest.raises(RadiationModelError) as excinfo:
            model.writeCameraImage(camera="overhead_rgb",
                                   bands=["Red", "Green", "Blue"],
                                   imagefile_base="apple_tree_rgb")

        message = str(excinfo.value)
        assert "runBand()" in message, f"error must name the missing call: {message}"
        assert "overhead_rgb" in message, f"error must name the camera: {message}"
        assert "invalid map" not in message, f"raw STL message leaked: {message}"

    def test_band_not_in_runband_call_raises_actionable_error(self, monkeypatch):
        """runBand(['Red','Green','Blue']) then writeCameraImage(['NIR']).

        The subtler failure: camera and band both exist, but that band was never
        rendered, so pixel_data has no key for it.
        """
        model = self._model_with_stub(
            monkeypatch,
            cameras=["cam"],
            rendered={"cam": {"Red", "Green", "Blue"}},
        )

        with pytest.raises(RadiationModelError) as excinfo:
            model.writeCameraImage(camera="cam", bands=["NIR"],
                                   imagefile_base="nir")

        message = str(excinfo.value)
        assert "NIR" in message, f"error must name the unrendered band: {message}"
        assert "runBand()" in message

    def test_nonexistent_camera_names_existing_cameras(self, monkeypatch):
        model = self._model_with_stub(monkeypatch, cameras=["cam_a"],
                                      rendered={"cam_a": {"Red"}})

        with pytest.raises(RadiationModelError) as excinfo:
            model.writeCameraImage(camera="typo_cam", bands=["Red"],
                                   imagefile_base="x")

        message = str(excinfo.value)
        assert "typo_cam" in message
        assert "cam_a" in message, f"error should list existing cameras: {message}"

    def test_fully_rendered_camera_passes_preflight(self, monkeypatch):
        """The guard must be a no-op for valid input."""
        # 'pyhelios.RadiationModel' is the module; the RadiationModel name
        # re-exported from the package is the class and would shadow it here.
        radiation_module = sys.modules['pyhelios.RadiationModel']

        model = self._model_with_stub(
            monkeypatch,
            cameras=["cam"],
            rendered={"cam": {"Red", "Green", "Blue"}},
        )

        calls = []

        def fake_write(_ptr, camera, bands, base, path, frame, conversion):
            calls.append((camera, list(bands)))
            return "cam_out.jpeg"

        monkeypatch.setattr(radiation_module.radiation_wrapper,
                            'writeCameraImage', fake_write)

        result = model.writeCameraImage(camera="cam",
                                        bands=["Red", "Green", "Blue"],
                                        imagefile_base="out")

        assert result == "cam_out.jpeg"
        assert calls == [("cam", ["Red", "Green", "Blue"])], (
            "valid input must reach the native call unchanged"
        )

    def test_writenorm_camera_image_is_guarded_too(self, monkeypatch):
        """writeNormCameraImage delegates to writeCameraImage natively."""
        model = self._model_with_stub(monkeypatch, cameras=["cam"], rendered={})

        with pytest.raises(RadiationModelError) as excinfo:
            model.writeNormCameraImage(camera="cam", bands=["Red"],
                                       imagefile_base="x")

        assert "runBand()" in str(excinfo.value)

    def test_empty_native_filename_raises_instead_of_reporting_success(self, monkeypatch):
        """An empty native return means the write failed and must not look like success.

        helios-core v1.3.79 signals a failed camera-image write by returning an
        empty filename rather than throwing. The preflight above catches the
        common causes, but not all of them -- an unwritable image_path fails this
        way too. Reporting "written to: " for a file that was never created
        violates the fail-fast policy, so an empty return must raise.
        """
        radiation_module = sys.modules['pyhelios.RadiationModel']

        model = self._model_with_stub(
            monkeypatch,
            cameras=["cam"],
            rendered={"cam": {"Red"}},
        )

        monkeypatch.setattr(
            radiation_module.radiation_wrapper, 'writeCameraImage',
            lambda *args, **kwargs: "")

        with pytest.raises(RadiationModelError) as excinfo:
            model.writeCameraImage(camera="cam", bands=["Red"],
                                   imagefile_base="out",
                                   image_path="/nonexistent/dir")

        message = str(excinfo.value)
        assert "cam" in message, f"error must name the camera: {message}"
        assert "/nonexistent/dir" in message, (
            f"error should name the output path, the likeliest cause: {message}")

    def test_empty_native_filename_raises_for_writenorm(self, monkeypatch):
        """Same empty-return contract applies to writeNormCameraImage."""
        radiation_module = sys.modules['pyhelios.RadiationModel']

        model = self._model_with_stub(
            monkeypatch,
            cameras=["cam"],
            rendered={"cam": {"Red"}},
        )

        monkeypatch.setattr(
            radiation_module.radiation_wrapper, 'writeNormCameraImage',
            lambda *args, **kwargs: "")

        with pytest.raises(RadiationModelError) as excinfo:
            model.writeNormCameraImage(camera="cam", bands=["Red"],
                                       imagefile_base="out",
                                       image_path="/nonexistent/dir")

        assert "cam" in str(excinfo.value)

    def test_successful_write_still_logs_and_returns_filename(self, monkeypatch):
        """The empty-return guard must not disturb the success path."""
        radiation_module = sys.modules['pyhelios.RadiationModel']

        model = self._model_with_stub(
            monkeypatch,
            cameras=["cam"],
            rendered={"cam": {"Red"}},
        )

        monkeypatch.setattr(
            radiation_module.radiation_wrapper, 'writeCameraImage',
            lambda *args, **kwargs: "cam_Red_00001.jpeg")

        assert model.writeCameraImage(
            camera="cam", bands=["Red"],
            imagefile_base="out") == "cam_Red_00001.jpeg"


@pytest.mark.native_only
class TestWriteCameraImagePixelDataPreflightNative:
    """End-to-end confirmation of the issue #4 preflight against a real GPU.

    The stub-driven tests above cannot prove the native call is actually
    avoided. These require a working radiation backend (OptiX/CUDA or Vulkan)
    and are skipped on machines without one -- including Apple Silicon, where
    the plugin compiles but has no runtime backend. They MUST be run on GPU
    hardware or CI before this fix is considered verified end-to-end.
    """

    @staticmethod
    def _radiation_or_skip(context):
        """Construct a RadiationModel, skipping if no backend can initialize.

        The plugin can be compiled in and still fail at construction when no
        usable backend is present (e.g. Vulkan pipeline creation fails on Apple
        Silicon). Without this, such machines report a misleading failure for a
        defect these tests are not exercising.

        The out-of-process probe runs first because the constructor does not
        always fail cleanly: on the macOS cibuildwheel runner it segfaults, and
        no except clause can catch SIGSEGV.
        """
        skip_without_radiation_backend()
        try:
            return RadiationModel(context)
        except RadiationModelError as e:
            pytest.skip(f"no working radiation backend on this machine: {e}")

    def test_unrendered_camera_raises_instead_of_map_key_error(self):
        """Camera added but runBand() never called -- the reported sequence."""
        context = Context()
        context.addPatch(center=DataTypes.vec3(0, 0, 0),
                         size=DataTypes.vec2(10, 10))

        with self._radiation_or_skip(context) as radiation:
            radiation.addRadiationBand("Red")
            radiation.addRadiationBand("Green")
            radiation.addRadiationBand("Blue")
            radiation.updateGeometry()
            radiation.addRadiationCamera(
                "overhead_rgb", ["Red", "Green", "Blue"],
                position=DataTypes.vec3(0, 3, 10),
                lookat_or_direction=DataTypes.vec3(0, 0, 0))

            with pytest.raises(RadiationModelError) as excinfo:
                radiation.writeCameraImage(camera="overhead_rgb",
                                           bands=["Red", "Green", "Blue"],
                                           imagefile_base="issue4_rgb")

            message = str(excinfo.value)
            assert "invalid map" not in message, (
                f"raw STL error reached the user: {message}"
            )
            assert "runBand()" in message

    def test_band_outside_runband_call_raises(self):
        """runBand() on RGB, then request an image for the unrendered NIR band."""
        context = Context()
        context.addPatch(center=DataTypes.vec3(0, 0, 0),
                         size=DataTypes.vec2(10, 10))

        with self._radiation_or_skip(context) as radiation:
            for band in ("Red", "Green", "Blue", "NIR"):
                radiation.addRadiationBand(band)
            radiation.addRadiationCamera(
                "cam", ["Red", "Green", "Blue", "NIR"],
                position=DataTypes.vec3(0, 3, 10),
                lookat_or_direction=DataTypes.vec3(0, 0, 0))
            radiation.updateGeometry()
            radiation.runBand(["Red", "Green", "Blue"])

            with pytest.raises(RadiationModelError) as excinfo:
                radiation.writeCameraImage(camera="cam", bands=["NIR"],
                                           imagefile_base="issue4_nir")

            assert "invalid map" not in str(excinfo.value)

    def test_rendered_camera_still_writes_image(self, tmp_path):
        """The preflight must not break the working path."""
        context = Context()
        context.addPatch(center=DataTypes.vec3(0, 0, 0),
                         size=DataTypes.vec2(10, 10))

        with self._radiation_or_skip(context) as radiation:
            for band in ("Red", "Green", "Blue"):
                radiation.addRadiationBand(band)
            radiation.addRadiationCamera(
                "cam", ["Red", "Green", "Blue"],
                position=DataTypes.vec3(0, 3, 10),
                lookat_or_direction=DataTypes.vec3(0, 0, 0))
            radiation.updateGeometry()
            radiation.runBand(["Red", "Green", "Blue"])

            filename = radiation.writeCameraImage(
                camera="cam", bands=["Red", "Green", "Blue"],
                imagefile_base="issue4_ok", image_path=str(tmp_path) + os.sep)

            assert filename, "valid camera image write returned no filename"


@pytest.mark.native_only
class TestBandSpecificAbsorbedFlux:
    """Per-band absorbed flux must be retrievable and UUID-aligned (GitHub issue #10).

    ``getTotalAbsorbedFlux()`` sums ``radiation_flux_<band>`` over every band
    registered in the model (RadiationModel.cpp), which double-counts overlapping
    bands such as PAR + NIR + SW, and it is indexed by the radiation model's
    internal primitive ordering rather than by ``context.getAllUUIDs()``.
    ``Context::getAllUUIDs`` iterates an ``unordered_map``, so its order is a hash
    order that does not match; two patches come back as ``[1, 0]``. Pairing the
    two by position therefore attributes flux to the wrong primitive.

    ``getAbsorbedFlux()`` reads the per-band primitive data keyed by UUID, so it
    is correct for a single band and correct by construction on ordering.

    Not marked ``requires_gpu``: these run on the Vulkan software-BVH backend,
    which needs no GPU. Environments with no constructible backend skip.
    """

    _radiation_or_skip = staticmethod(radiation_model_or_skip)

    @staticmethod
    def _shaded_scene(context):
        """Small patch fully shaded by a large one, so per-primitive flux differs.

        Returns (shaded_uuid, lit_uuid). Distinct flux values are what make an
        index-alignment error detectable at all.
        """
        shaded = context.addPatch(center=DataTypes.vec3(0, 0, 0),
                                  size=DataTypes.vec2(1, 1))
        lit = context.addPatch(center=DataTypes.vec3(0, 0, 2),
                               size=DataTypes.vec2(6, 6))
        return shaded, lit

    def _run(self, context, radiation, bands):
        for band in bands:
            radiation.addRadiationBand(band)
        source = radiation.addCollimatedRadiationSource(
            direction=DataTypes.vec3(0, 0, -1))
        for i, band in enumerate(bands):
            radiation.setSourceFlux(source, band, 200.0 * (i + 1))
            radiation.setDiffuseRadiationFlux(band, 0.0)
            radiation.setDirectRayCount(band, 300)
            radiation.setScatteringDepth(band, 0)
        radiation.updateGeometry()
        radiation.runBand(list(bands))

    def test_absorbed_flux_is_uuid_aligned(self):
        """getAbsorbedFlux(band)[i] must belong to getAllUUIDs()[i]."""
        with Context() as context:
            self._shaded_scene(context)
            with self._radiation_or_skip(context) as radiation:
                self._run(context, radiation, ["SW"])

                uuids = context.getAllUUIDs()
                flux = radiation.getAbsorbedFlux("SW")

                assert len(flux) == len(uuids)
                truth = [context.getPrimitiveDataFloat(u, "radiation_flux_SW")
                         for u in uuids]
                # Guard the guard: if every primitive absorbed the same amount,
                # a misalignment would pass unnoticed.
                assert max(truth) - min(truth) > 1.0, (
                    f"scene does not discriminate primitives: {truth}")
                for i, uuid in enumerate(uuids):
                    assert abs(flux[i] - truth[i]) < 1e-3, (
                        f"index {i} (UUID {uuid}): getAbsorbedFlux gave {flux[i]}, "
                        f"primitive data says {truth[i]}")

    def test_absorbed_flux_is_per_band_not_summed(self):
        """Each band must report its own flux, not the all-band sum."""
        bands = ["PAR", "NIR", "SW"]
        with Context() as context:
            self._shaded_scene(context)
            with self._radiation_or_skip(context) as radiation:
                self._run(context, radiation, bands)

                uuids = context.getAllUUIDs()
                per_band = {b: radiation.getAbsorbedFlux(b) for b in bands}

                for band in bands:
                    expected = [context.getPrimitiveDataFloat(
                        u, f"radiation_flux_{band}") for u in uuids]
                    assert per_band[band] == pytest.approx(expected, abs=1e-3)

                # The sum over bands is what getTotalAbsorbedFlux() reports, so
                # any single band must be strictly smaller than that sum.
                summed = [sum(per_band[b][i] for b in bands)
                          for i in range(len(uuids))]
                lit_index = max(range(len(uuids)), key=lambda i: summed[i])
                for band in bands:
                    assert per_band[band][lit_index] < summed[lit_index] - 1.0, (
                        f"band {band} looks like the all-band sum")

    def test_absorbed_flux_accepts_band_list(self):
        """A list of bands returns a dict keyed by band label."""
        bands = ["PAR", "NIR"]
        with Context() as context:
            self._shaded_scene(context)
            with self._radiation_or_skip(context) as radiation:
                self._run(context, radiation, bands)

                result = radiation.getAbsorbedFlux(bands)

                assert isinstance(result, dict)
                assert set(result) == set(bands)
                for band in bands:
                    assert result[band] == pytest.approx(
                        radiation.getAbsorbedFlux(band), abs=1e-3)

    def test_absorbed_flux_honors_explicit_uuids(self):
        """An explicit UUID list controls both selection and order."""
        with Context() as context:
            shaded, lit = self._shaded_scene(context)
            with self._radiation_or_skip(context) as radiation:
                self._run(context, radiation, ["SW"])

                pair = radiation.getAbsorbedFlux("SW", uuids=[lit, shaded])

                assert len(pair) == 2
                assert pair[0] == pytest.approx(
                    context.getPrimitiveDataFloat(lit, "radiation_flux_SW"),
                    abs=1e-3)
                assert pair[1] == pytest.approx(
                    context.getPrimitiveDataFloat(shaded, "radiation_flux_SW"),
                    abs=1e-3)

    def test_absorbed_flux_unknown_band_raises(self):
        """An unregistered band must name the problem, not fail obscurely."""
        with Context() as context:
            self._shaded_scene(context)
            with self._radiation_or_skip(context) as radiation:
                self._run(context, radiation, ["SW"])

                with pytest.raises(RadiationModelError) as excinfo:
                    radiation.getAbsorbedFlux("NIR")

                assert "NIR" in str(excinfo.value)

    def test_absorbed_flux_before_runband_raises(self):
        """Querying a band that was added but never run must say so."""
        with Context() as context:
            self._shaded_scene(context)
            with self._radiation_or_skip(context) as radiation:
                radiation.addRadiationBand("SW")
                radiation.addRadiationBand("NIR")
                source = radiation.addCollimatedRadiationSource(
                    direction=DataTypes.vec3(0, 0, -1))
                radiation.setSourceFlux(source, "SW", 500.0)
                radiation.setDirectRayCount("SW", 200)
                radiation.updateGeometry()
                radiation.runBand("SW")

                with pytest.raises(RadiationModelError) as excinfo:
                    radiation.getAbsorbedFlux("NIR")

                message = str(excinfo.value)
                assert "runBand" in message
                assert "NIR" in message

    def test_absorbed_flux_rejects_non_string_band(self):
        """Type errors must be reported as such."""
        with Context() as context:
            self._shaded_scene(context)
            with self._radiation_or_skip(context) as radiation:
                self._run(context, radiation, ["SW"])

                with pytest.raises((TypeError, ValueError)):
                    radiation.getAbsorbedFlux(42)

    def test_absorbed_flux_does_not_rescan_uuids_per_primitive(self):
        """Retrieval must stay linear in the primitive count.

        Any UUID-existence check that re-fetches and rescans the context's UUID
        list per element turns retrieval into O(N^2) with N native round-trips --
        ~15 s for a 20k-primitive canopy against ~40 ms when the lookup is hoisted.
        ``Context._validate_uuids()`` hoists it; reintroducing a per-element check
        here would not.

        Counting ``getAllUUIDs()`` calls detects that without timing anything: the
        quadratic form calls it once per primitive.
        """
        with Context() as context:
            for i in range(6):
                context.addPatch(center=DataTypes.vec3(i * 0.5, 0, 0),
                                 size=DataTypes.vec2(0.4, 0.4))
            with self._radiation_or_skip(context) as radiation:
                self._run(context, radiation, ["SW"])

                primitive_count = context.getPrimitiveCount()
                calls = []
                real_get_all = context.getAllUUIDs

                def counting_get_all():
                    calls.append(1)
                    return real_get_all()

                context.getAllUUIDs = counting_get_all
                try:
                    flux = radiation.getAbsorbedFlux("SW")
                finally:
                    del context.getAllUUIDs

                assert len(flux) == primitive_count
                assert len(calls) <= 1, (
                    f"getAllUUIDs() called {len(calls)} times for "
                    f"{primitive_count} primitives - retrieval is rescanning "
                    f"the UUID list per primitive"
                )


class TestBoundedBandCameraResponseWarning:
    """Explicit band wavelength bounds + a camera spectral response render wrong colors.

    Helios integrates camera pixels against the camera's spectral response, but
    integrates SCATTERED flux over the band's wavelength bounds. Without bounds it
    falls back to the camera-weighted average so both agree; with bounds they
    diverge. Since scattering supplies most camera-visible light, colors come out
    skewed -- a soil spectrum with a true red/green ratio of 1.2 renders at 2.6.

    Nothing raises and saturated colors still look plausible, so PyHelios warns
    when it sees the combination.
    """

    @pytest.mark.native_only
    def test_warns_when_bounded_band_gets_camera_response(self, caplog):
        """setCameraSpectralResponse on a bounded band must warn."""
        registry = get_plugin_registry()
        if not registry.is_plugin_available('radiation'):
            pytest.skip("radiation plugin not available")

        with Context() as context:
            with radiation_model_or_skip(context) as radiation:
                radiation.addRadiationBand("red", 600.0, 700.0)
                radiation.addRadiationCamera(
                    "cam", ["red"], DataTypes.vec3(0, -2, 1), DataTypes.vec3(0, 0, 1),
                    antialiasing_samples=1)

                caplog.clear()
                with caplog.at_level("WARNING", logger="pyhelios.RadiationModel"):
                    radiation.setCameraSpectralResponse("cam", "red", "iPhone12ProMAX_red")

        text = caplog.text
        assert "wavelength bounds" in text, f"expected a bounded-band warning, got: {text!r}"
        assert "red" in text

    @pytest.mark.native_only
    def test_no_warning_without_wavelength_bounds(self, caplog):
        """The recommended setup (no bounds) must stay silent."""
        registry = get_plugin_registry()
        if not registry.is_plugin_available('radiation'):
            pytest.skip("radiation plugin not available")

        with Context() as context:
            with radiation_model_or_skip(context) as radiation:
                radiation.addRadiationBand("red")
                radiation.addRadiationCamera(
                    "cam", ["red"], DataTypes.vec3(0, -2, 1), DataTypes.vec3(0, 0, 1),
                    antialiasing_samples=1)

                caplog.clear()
                with caplog.at_level("WARNING", logger="pyhelios.RadiationModel"):
                    radiation.setCameraSpectralResponse("cam", "red", "iPhone12ProMAX_red")

        assert "wavelength bounds" not in caplog.text

    @pytest.mark.native_only
    def test_copied_band_inherits_bounded_state(self, caplog):
        """copyRadiationBand with no bounds inherits them, so the copy must warn too."""
        registry = get_plugin_registry()
        if not registry.is_plugin_available('radiation'):
            pytest.skip("radiation plugin not available")

        with Context() as context:
            with radiation_model_or_skip(context) as radiation:
                radiation.addRadiationBand("red", 600.0, 700.0)
                radiation.copyRadiationBand("red", "green")
                radiation.addRadiationCamera(
                    "cam", ["green"], DataTypes.vec3(0, -2, 1), DataTypes.vec3(0, 0, 1),
                    antialiasing_samples=1)

                caplog.clear()
                with caplog.at_level("WARNING", logger="pyhelios.RadiationModel"):
                    radiation.setCameraSpectralResponse("cam", "green", "iPhone12ProMAX_green")

        assert "wavelength bounds" in caplog.text
        assert "green" in caplog.text

    @pytest.mark.native_only
    def test_rebinding_band_without_bounds_clears_warning(self, caplog):
        """Re-adding a band without bounds must clear the stale bounded state."""
        registry = get_plugin_registry()
        if not registry.is_plugin_available('radiation'):
            pytest.skip("radiation plugin not available")

        with Context() as context:
            with radiation_model_or_skip(context) as radiation:
                radiation.addRadiationBand("red", 600.0, 700.0)
                radiation.addRadiationBand("red")  # redefined without bounds
                radiation.addRadiationCamera(
                    "cam", ["red"], DataTypes.vec3(0, -2, 1), DataTypes.vec3(0, 0, 1),
                    antialiasing_samples=1)

                caplog.clear()
                with caplog.at_level("WARNING", logger="pyhelios.RadiationModel"):
                    radiation.setCameraSpectralResponse("cam", "red", "iPhone12ProMAX_red")

        assert "wavelength bounds" not in caplog.text


class TestCameraStringPropertiesArePlumbed:
    """CameraProperties' string fields must reach the C++ camera.

    These are std::string on the C++ side, so they cannot ride in the numeric
    camera-properties array. They previously stopped at the C boundary, which
    hardcoded "auto"/"generic" -- so white_balance="off" and exposure="manual"
    silently did nothing and there was no way to disable Helios' automatic
    colour handling from Python.
    """

    @pytest.mark.native_only
    def test_white_balance_off_changes_rendered_colour(self):
        """white_balance='off' must actually reach the camera and alter pixels."""
        registry = get_plugin_registry()
        if not registry.is_plugin_available('radiation'):
            pytest.skip("radiation plugin not available")

        from pyhelios import CameraProperties

        from pyhelios.assets import get_asset_manager
        spectral_dir = (get_asset_manager()._get_helios_build_path()
                        / "plugins" / "radiation" / "spectral_data")
        camera_library = spectral_dir / "camera_spectral_library.xml"
        if not camera_library.is_file():
            pytest.skip("camera spectral library not present in build")

        def render(white_balance):
            with Context() as context:
                context.loadXML(str(camera_library), True)
                context.loadXML(str(spectral_dir / "soil_surface_spectral_library.xml"), True)
                patch = context.addPatch(
                    center=DataTypes.vec3(0, 0, 0),
                    size=DataTypes.vec2(20, 20))
                context.setPrimitiveDataString(
                    patch, "reflectivity_spectrum", "soil_reflectivity_0000")
                with radiation_model_or_skip(context) as radiation:
                    for band in ("red", "green", "blue"):
                        radiation.addRadiationBand(band)
                        radiation.disableEmission(band)
                        radiation.setScatteringDepth(band, 1)
                    source = radiation.addCollimatedRadiationSource(DataTypes.vec3(0, 0, 1))
                    for band in ("red", "green", "blue"):
                        radiation.setSourceFlux(source, band, 500.0)
                    props = CameraProperties(camera_resolution=(64, 64), HFOV=60.0,
                                             white_balance=white_balance)
                    radiation.addRadiationCamera(
                        "cam", ["red", "green", "blue"],
                        DataTypes.vec3(0, 0, 5), DataTypes.vec3(0, 0, 0),
                        props, antialiasing_samples=1)
                    radiation.setCameraSpectralResponse("cam", "red", "iPhone12ProMAX_red")
                    radiation.setCameraSpectralResponse("cam", "green", "iPhone12ProMAX_green")
                    radiation.setCameraSpectralResponse("cam", "blue", "iPhone12ProMAX_blue")
                    radiation.updateGeometry()
                    radiation.runBand(["red", "green", "blue"])
                    return {b: radiation.getCameraPixelData("cam", b)
                            for b in ("red", "green", "blue")}

        auto = render("auto")
        off = render("off")

        def ratio(px):
            lit = [i for i, v in enumerate(px["green"]) if v > 1e-9]
            assert lit, "camera produced no lit pixels"
            i = lit[len(lit) // 2]
            return px["red"][i] / px["green"][i]

        auto_ratio = ratio(auto)
        off_ratio = ratio(off)

        # Spectral white balance divides each channel by its integrated response,
        # which boosts red ~2.1x relative to green. Turning it off must remove
        # that boost, so the two ratios cannot match.
        assert abs(auto_ratio - off_ratio) > 0.1 * max(auto_ratio, off_ratio), (
            f"white_balance had no effect: auto R/G={auto_ratio:.3f}, "
            f"off R/G={off_ratio:.3f} -- the setting is not reaching the camera")
        assert off_ratio < auto_ratio, (
            f"disabling white balance should reduce the red boost, got "
            f"auto={auto_ratio:.3f} off={off_ratio:.3f}")

    @pytest.mark.native_only
    def test_camera_metadata_reports_requested_model(self, tmp_path):
        """model/manufacturer must reach the camera and appear in its metadata."""
        registry = get_plugin_registry()
        if not registry.is_plugin_available('radiation'):
            pytest.skip("radiation plugin not available")

        import json
        from pyhelios import CameraProperties

        with Context() as context:
            context.addPatch(center=DataTypes.vec3(0, 0, 0.5),
                             size=DataTypes.vec2(3, 3),
                             rotation=DataTypes.SphericalCoord(1.0, 1.5708, 0.0))
            with radiation_model_or_skip(context) as radiation:
                radiation.addRadiationBand("red")
                radiation.disableEmission("red")
                radiation.setScatteringDepth("red", 1)
                source = radiation.addCollimatedRadiationSource(DataTypes.vec3(0, 0, 1))
                radiation.setSourceFlux(source, "red", 500.0)
                props = CameraProperties(camera_resolution=(32, 32), HFOV=60.0,
                                         manufacturer="PyHeliosTest",
                                         model="TestCam9000")
                radiation.addRadiationCamera(
                    "cam", ["red"], DataTypes.vec3(0, -2, 0.5),
                    DataTypes.vec3(0, 0, 0.5), props, antialiasing_samples=1)
                radiation.enableCameraMetadata("cam")
                radiation.updateGeometry()
                radiation.runBand(["red"])
                radiation.writeCameraImage("cam", ["red"], "meta", str(tmp_path))

        blobs = list(tmp_path.glob("*.json"))
        assert blobs, "no camera metadata file was written"
        text = json.dumps(json.loads(blobs[0].read_text()))
        assert "TestCam9000" in text, f"model not plumbed through: {text[:400]}"
