"""
Tests for Visualizer functionality in PyHelios.

This module tests the Visualizer class and 3D visualization capabilities.
Tests are designed to work in both native and mock modes.

The test_color_primitives_integration_workflow test has been re-enabled after the
Helios C++ visualizer fixes for headless mode were merged into helios-core master branch.
"""

import pytest
import sys
import os
import platform
from typing import List

# Add pyhelios to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pyhelios import Context, Visualizer, DataTypes
from pyhelios.Visualizer import VisualizerError
from pyhelios.validation.exceptions import ValidationError
from pyhelios.wrappers.DataTypes import vec3, RGBcolor, SphericalCoord, vec2, int3


def is_headless_environment():
    """
    Check if we're running in a headless environment where visualization tests would fail.
    
    This function performs multiple checks to determine if the environment supports
    OpenGL rendering, which is required for the visualizer plugin tests.
    
    Returns:
        bool: True if headless (skip visualization tests), False if display is available
    """
    # Check for display availability
    display = os.environ.get('DISPLAY')
    if not display:
        return True  # No display available
    
    # Check if we're in an SSH session without X11 forwarding
    ssh_client = os.environ.get('SSH_CLIENT')
    ssh_tty = os.environ.get('SSH_TTY')
    if ssh_client or ssh_tty:
        # In SSH session - check if DISPLAY is properly set for X11 forwarding
        if not display or display == ':0':
            return True  # SSH without proper X11 forwarding
    
    # Additional check for CI environments
    ci_indicators = ['CI', 'CONTINUOUS_INTEGRATION', 'GITHUB_ACTIONS', 'TRAVIS', 'JENKINS']
    if any(os.environ.get(var) for var in ci_indicators):
        return True  # Running in CI environment
    
    # Try a simple OpenGL context test if we can import necessary libraries
    try:
        import subprocess
        import sys
        
        # On macOS, try to verify OpenGL/graphics capability through system_profiler
        if sys.platform == 'darwin':
            result = subprocess.run(['system_profiler', 'SPDisplaysDataType'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0 or 'Graphics/Displays' not in result.stdout:
                return True  # Can't verify graphics capability
        
        # On Linux, check if we can connect to X display
        elif sys.platform.startswith('linux'):
            result = subprocess.run(['xrandr', '--query'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return True  # Can't connect to X display
                
    except (ImportError, FileNotFoundError, subprocess.TimeoutExpired, Exception):
        # If we can't run the checks, be conservative
        return True
    
    return False  # Display should be available


def should_skip_interactive_visualizer_tests():
    """
    Check if interactive visualizer tests should be skipped.
    
    These tests may cause crashes even in environments with displays if the OpenGL
    context or graphics drivers have issues. Users can override with PYHELIOS_TEST_VISUALIZER_INTERACTIVE.
    
    Returns:
        bool: True if interactive tests should be skipped
    """
    # Allow users to force enable risky tests
    if os.environ.get('PYHELIOS_TEST_VISUALIZER_INTERACTIVE') == '1':
        return False
        
    # Skip if headless
    if is_headless_environment():
        return True
        
    # Be conservative about tests that call plotUpdate() or other interactive functions
    # These are known to cause crashes in some environments
    return True


@pytest.mark.cross_platform
class TestVisualizerCrossPlatform:
    """Cross-platform tests that work in both native and mock modes"""
    
    def test_visualizer_creation_parameters(self):
        """Test Visualizer parameter validation"""
        # Test invalid dimensions
        with pytest.raises(ValueError, match="Width and height must be positive"):
            Visualizer(0, 600)
        
        with pytest.raises(ValueError, match="Width and height must be positive"):
            Visualizer(800, -1)
        
        # Test invalid antialiasing
        with pytest.raises(ValueError, match="Antialiasing samples must be at least 1"):
            Visualizer(800, 600, antialiasing_samples=0)
    
    def test_visualizer_lighting_constants(self):
        """Test lighting model constants"""
        assert Visualizer.LIGHTING_NONE == 0
        assert Visualizer.LIGHTING_PHONG == 1
        assert Visualizer.LIGHTING_PHONG_SHADOWED == 2


@pytest.mark.native_only
@pytest.mark.skipif(is_headless_environment(), reason="Skipping visualizer tests in headless environment")
class TestVisualizerNative:
    """Test Visualizer class functionality with native library"""
    
    def test_visualizer_creation_basic(self):
        """Test basic Visualizer creation and destruction"""
        # Test creating Visualizer with default parameters
        with Visualizer(800, 600) as visualizer:
            assert visualizer is not None
            assert visualizer.width == 800
            assert visualizer.height == 600
            assert visualizer.antialiasing_samples == 1
            assert visualizer.headless == False
    
    def test_visualizer_creation_with_parameters(self):
        """Test Visualizer creation with custom parameters"""
        # Test with antialiasing and headless mode
        with Visualizer(1024, 768, antialiasing_samples=4, headless=True) as visualizer:
            assert visualizer.width == 1024
            assert visualizer.height == 768
            assert visualizer.antialiasing_samples == 4
            assert visualizer.headless == True
    
    def test_visualizer_context_geometry(self):
        """Test building Context geometry in visualizer"""
        with Context() as context:
            # Add some geometry to context
            center = DataTypes.vec3(0, 0, 0)
            size = DataTypes.vec2(1, 1)
            patch_uuid = context.addPatch(center=center, size=size)
            
            with Visualizer(400, 300, headless=True) as visualizer:
                # Build all geometry
                visualizer.buildContextGeometry(context)
                
                # Build specific geometry
                visualizer.buildContextGeometry(context, uuids=[patch_uuid])
    
    def test_visualizer_context_geometry_validation(self):
        """Test Context geometry building parameter validation"""
        with Context() as context:
            with Visualizer(400, 300, headless=True) as visualizer:
                # Test invalid context type (raises ValidationError which extends ValueError)
                # Use manual exception handling due to test isolation issues with pytest.raises
                validation_error_raised = False
                try:
                    visualizer.buildContextGeometry("invalid_context")
                except Exception as e:
                    validation_error_raised = True
                    # Check if it's the right type of exception
                    is_validation_error = (
                        isinstance(e, ValidationError) or
                        type(e).__name__ == 'ValidationError' or
                        'validation' in type(e).__module__.lower()
                    )
                    if not is_validation_error:
                        pytest.fail(f"Expected ValidationError but got {type(e).__name__}: {str(e)}")
                    
                    # Check the error message contains expected text
                    if "Parameter must be a Context instance" not in str(e):
                        pytest.fail(f"Error message doesn't contain expected text. Got: {str(e)}")
                
                if not validation_error_raised:
                    pytest.fail("Expected ValidationError to be raised but no exception was raised")
                
                # Test empty UUIDs list (raises ValueError inside try-catch, wrapped in VisualizerError)
                with pytest.raises(VisualizerError, match="UUIDs list cannot be empty"):
                    visualizer.buildContextGeometry(context, uuids=[])
    
    @pytest.mark.skipif(should_skip_interactive_visualizer_tests(), 
                        reason="Skipping interactive visualizer test (may cause crashes). Set PYHELIOS_TEST_VISUALIZER_INTERACTIVE=1 to enable.")
    def test_visualizer_rendering_headless(self):
        """Test basic rendering operations in headless mode"""
        with Context() as context:
            # Add geometry
            center = DataTypes.vec3(0, 0, 0)
            size = DataTypes.vec2(1, 1)
            context.addPatch(center=center, size=size)
            
            with Visualizer(400, 300, headless=True) as visualizer:
                visualizer.buildContextGeometry(context)
                
                # Test plot update (non-interactive)
                visualizer.plotUpdate()
                
                # Test window operations
                visualizer.closeWindow()
    
    @pytest.mark.skipif(should_skip_interactive_visualizer_tests(), 
                        reason="Skipping interactive visualizer test (may cause crashes). Set PYHELIOS_TEST_VISUALIZER_INTERACTIVE=1 to enable.")
    def test_visualizer_image_export(self):
        """Test image export functionality"""
        with Context() as context:
            # Add geometry
            center = DataTypes.vec3(0, 0, 0)
            size = DataTypes.vec2(1, 1)
            color = DataTypes.RGBcolor(0.5, 0.5, 0.5)
            context.addPatch(center=center, size=size, color=color)
            
            with Visualizer(400, 300, headless=True) as visualizer:
                visualizer.buildContextGeometry(context)
                visualizer.plotUpdate()
                
                # Test image export (this might require temp file handling)
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                    tmp_name = tmp.name
                
                try:
                    visualizer.printWindow(tmp_name)
                    # Check if file was created (size check would be better but file might be empty in mock)
                    assert os.path.exists(tmp_name)
                finally:
                    if os.path.exists(tmp_name):
                        os.unlink(tmp_name)
    
    def test_visualizer_camera_controls(self):
        """Test camera positioning functions"""
        with Visualizer(400, 300, headless=True) as visualizer:
            # Test Cartesian camera positioning
            position = vec3(5, 5, 5)
            lookAt = vec3(0, 0, 0)
            visualizer.setCameraPosition(position, lookAt)
            
            # Test spherical camera positioning
            # SphericalCoord(radius, elevation, azimuth) - angles in radians
            angle = SphericalCoord(10, 0.785, 0.785)  # 45 degrees in radians
            visualizer.setCameraPositionSpherical(angle, lookAt)
    
    def test_visualizer_camera_validation(self):
        """Test camera parameter validation"""
        with Visualizer(400, 300, headless=True) as visualizer:
            # Test invalid position types
            with pytest.raises(ValueError, match="Position must be a vec3"):
                visualizer.setCameraPosition([1, 2, 3], vec3(0, 0, 0))
            
            with pytest.raises(ValueError, match="LookAt must be a vec3"):
                visualizer.setCameraPosition(vec3(1, 2, 3), [0, 0, 0])
            
            # Test invalid spherical types
            with pytest.raises(ValueError, match="Angle must be a SphericalCoord"):
                visualizer.setCameraPositionSpherical([10, 45, 45], vec3(0, 0, 0))
    
    def test_visualizer_scene_configuration(self):
        """Test scene configuration functions"""
        with Visualizer(400, 300, headless=True) as visualizer:
            # Test background color
            color = RGBcolor(0.2, 0.3, 0.4)
            visualizer.setBackgroundColor(color)
            
            # Test light direction
            direction = vec3(1, 1, -1)
            visualizer.setLightDirection(direction)
            
            # Test lighting models
            visualizer.setLightingModel(Visualizer.LIGHTING_NONE)
            visualizer.setLightingModel(Visualizer.LIGHTING_PHONG)
            visualizer.setLightingModel(Visualizer.LIGHTING_PHONG_SHADOWED)
            
            # Test string lighting models
            visualizer.setLightingModel("none")
            visualizer.setLightingModel("phong")
            visualizer.setLightingModel("phong_shadowed")
    
    def test_visualizer_scene_validation(self):
        """Test scene configuration parameter validation"""
        with Visualizer(400, 300, headless=True) as visualizer:
            # Test invalid color type
            with pytest.raises(ValueError, match="Color must be an RGBcolor"):
                visualizer.setBackgroundColor([0.5, 0.5, 0.5])
            
            # Test invalid color range
            # Test that invalid colors are rejected at construction time
            with pytest.raises(ValueError, match="outside valid range"):
                invalid_color = RGBcolor(1.5, 0.5, 0.5)
            
            with pytest.raises(ValueError, match="outside valid range"):
                invalid_color2 = RGBcolor(0.5, -0.1, 0.5)
            
            # Test invalid direction type
            with pytest.raises(ValueError, match="Direction must be a vec3"):
                visualizer.setLightDirection([1, 1, -1])
            
            # Test zero direction vector
            zero_direction = vec3(0, 0, 0)
            with pytest.raises(ValueError, match="Light direction cannot be zero vector"):
                visualizer.setLightDirection(zero_direction)
            
            # Test invalid lighting model
            with pytest.raises(ValueError, match="Lighting model must be"):
                visualizer.setLightingModel(99)
            
            with pytest.raises(ValueError, match="Unknown lighting model string"):
                visualizer.setLightingModel("invalid_model")
    
    def test_visualizer_state_validation(self):
        """Test operations on destroyed visualizer"""
        visualizer = Visualizer(400, 300, headless=True)
        visualizer.__exit__(None, None, None)  # Manually destroy
        
        # Test that operations fail on destroyed visualizer
        with pytest.raises(VisualizerError, match="Visualizer has been destroyed"):
            with Context() as context:
                visualizer.buildContextGeometry(context)
        
        with pytest.raises(VisualizerError, match="Visualizer has been destroyed"):
            visualizer.plotUpdate()
        
        with pytest.raises(VisualizerError, match="Visualizer has been destroyed"):
            position = vec3(1, 2, 3)
            lookAt = vec3(0, 0, 0) 
            visualizer.setCameraPosition(position, lookAt)


@pytest.mark.mock_mode
class TestVisualizerMockMode:
    """Test Visualizer behavior in mock mode"""
    
    def test_visualizer_mock_mode_error_messages(self):
        """Test that mock mode provides helpful error messages"""
        import os
        import platform
        # Skip this test on macOS CI to avoid fatal crashes
        if os.environ.get('CI') and platform.system() == 'Darwin':
            pytest.skip("Skipping visualizer test on macOS CI due to graphics context issues")
            
        # This test assumes we're in an environment without visualizer plugin
        try:
            # Use headless mode to avoid display issues in CI
            with Visualizer(400, 300, headless=True) as visualizer:
                pytest.skip("Visualizer plugin is available, skipping mock mode test")
        except (VisualizerError, RuntimeError) as e:
            error_message = str(e)
            # Check that error message contains helpful information
            assert "visualizer" in error_message.lower()
            # Should contain helpful context about the issue
            assert any(term in error_message.lower() for term in ["plugin", "initialize", "graphics", "opengl", "system", "visualizer", "failed"])
        except Exception as e:
            # In CI environments, visualizer creation may fail with fatal errors
            # This is expected behavior when graphics context is not available
            pytest.skip(f"Visualizer creation failed in test environment: {e}")


@pytest.mark.cross_platform  
class TestVisualizerAPI:
    """Test Visualizer API compatibility across platforms"""
    
    def test_visualizer_types_and_defaults(self):
        """Test that types and defaults are consistent"""
        # Test that we can import and access constants
        assert hasattr(Visualizer, 'LIGHTING_NONE')
        assert hasattr(Visualizer, 'LIGHTING_PHONG')
        assert hasattr(Visualizer, 'LIGHTING_PHONG_SHADOWED')
    
    def test_visualizer_context_manager_protocol(self):
        """Test context manager protocol"""
        # Skip on macOS-13 due to Objective-C framework incompatibility with fork()
        # The new helios-core v1.3.50 visualizer initialization triggers NSResponder
        # initialization which cannot be safely used after fork() on macOS-13
        if (os.environ.get('CI') and platform.system() == 'Darwin' and
            platform.mac_ver()[0].startswith('13.')):
            pytest.skip("Skipping on macOS-13 CI: Visualizer initialization incompatible with fork() - "
                       "NSResponder framework conflicts with pytest-forked execution")

        # This should work even in mock mode for API validation
        try:
            visualizer = Visualizer(400, 300, headless=True)
            assert hasattr(visualizer, '__enter__')
            assert hasattr(visualizer, '__exit__')

            # Test that __enter__ returns self
            entered = visualizer.__enter__()
            assert entered is visualizer

            # Clean up
            visualizer.__exit__(None, None, None)
        except (VisualizerError, RuntimeError) as e:
            # Expected in mock mode or when graphics initialization fails in CI
            # Log the specific error for debugging
            import sys
            print(f"Visualizer initialization failed as expected in CI/mock mode: {e}", file=sys.stderr)
            pass
    
    def test_visualizer_method_signatures(self):
        """Test that all expected methods exist with correct signatures"""
        # Test method existence
        expected_methods = [
            'buildContextGeometry',
            'plotInteractive', 
            'plotUpdate',
            'printWindow',
            'closeWindow',
            'setCameraPosition',
            'setCameraPositionSpherical', 
            'setBackgroundColor',
            'setLightDirection',
            'setLightingModel',
            'colorContextPrimitivesByData'
        ]
        
        for method_name in expected_methods:
            assert hasattr(Visualizer, method_name), f"Missing method: {method_name}"
            method = getattr(Visualizer, method_name)
            assert callable(method), f"Method {method_name} is not callable"


@pytest.mark.cross_platform
class TestVisualizerDataColoring:
    """Test primitive coloring by data functionality"""
    
    def test_color_context_primitives_by_data_method_exists(self):
        """Test that colorContextPrimitivesByData method exists with correct signature"""
        assert hasattr(Visualizer, 'colorContextPrimitivesByData')
        method = getattr(Visualizer, 'colorContextPrimitivesByData')
        assert callable(method)
        
        # Test that method accepts correct parameters
        import inspect
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        assert 'self' in params
        assert 'data_name' in params
        assert 'uuids' in params
        
        # Check that uuids has Optional type hint and default value
        uuids_param = sig.parameters['uuids']
        assert uuids_param.default is None
    
    def test_color_primitives_api_compatibility(self):
        """Test API compatibility in mock mode"""
        # Skip on macOS-13 due to Objective-C framework incompatibility with fork()
        # The new helios-core v1.3.50 visualizer initialization triggers NSResponder
        # initialization which cannot be safely used after fork() on macOS-13
        if (os.environ.get('CI') and platform.system() == 'Darwin' and
            platform.mac_ver()[0].startswith('13.')):
            pytest.skip("Skipping on macOS-13 CI: Visualizer initialization incompatible with fork() - "
                       "NSResponder framework conflicts with pytest-forked execution")

        try:
            visualizer = Visualizer(400, 300, headless=True)

            # These should not raise AttributeError even in mock mode
            assert hasattr(visualizer, 'colorContextPrimitivesByData')

        except VisualizerError:
            # Expected in mock mode - plugin not available
            pass


@pytest.mark.native_only  
class TestVisualizerDataColoringNative:
    """Test primitive coloring by data with native library"""
    
    @pytest.fixture
    def visualizer_and_context(self):
        """Create visualizer and context with test data"""
        # Skip if headless environment
        if is_headless_environment():
            pytest.skip("Skipping visualization test in headless environment")
        
        context = Context()
        
        # Create some test geometry with data
        patch1 = context.addPatch(center=DataTypes.vec3(0, 0, 0), size=DataTypes.vec2(1, 1))
        patch2 = context.addPatch(center=DataTypes.vec3(2, 0, 0), size=DataTypes.vec2(1, 1))
        patch3 = context.addPatch(center=DataTypes.vec3(4, 0, 0), size=DataTypes.vec2(1, 1))
        
        # Set test data on primitives
        context.setPrimitiveDataFloat(patch1, "temperature", 20.5)
        context.setPrimitiveDataFloat(patch2, "temperature", 25.0)
        context.setPrimitiveDataFloat(patch3, "temperature", 30.2)
        
        context.setPrimitiveDataFloat(patch1, "radiation_flux", 150.0)
        context.setPrimitiveDataFloat(patch2, "radiation_flux", 200.0)
        context.setPrimitiveDataFloat(patch3, "radiation_flux", 175.5)
        
        try:
            visualizer = Visualizer(400, 300, headless=True)
            visualizer.buildContextGeometry(context)
            yield visualizer, context, [patch1, patch2, patch3]
        except (VisualizerError, RuntimeError) as e:
            pytest.skip(f"Visualizer plugin not available or graphics initialization failed: {e}")
        finally:
            # Cleanup
            if 'visualizer' in locals():
                try:
                    visualizer.closeWindow()
                except:
                    pass
    
    def test_color_all_primitives_by_data(self, visualizer_and_context):
        """Test coloring all primitives by data"""
        visualizer, context, uuids = visualizer_and_context
        
        # Test coloring all primitives by temperature data
        visualizer.colorContextPrimitivesByData("temperature")
        
        # Test coloring all primitives by radiation data
        visualizer.colorContextPrimitivesByData("radiation_flux")
        
        # Method should complete without error
    
    def test_color_specific_primitives_by_data(self, visualizer_and_context):
        """Test coloring specific primitives by data"""
        visualizer, context, uuids = visualizer_and_context
        
        # Test coloring subset of primitives
        visualizer.colorContextPrimitivesByData("temperature", uuids[:2])
        
        # Test coloring single primitive
        visualizer.colorContextPrimitivesByData("radiation_flux", [uuids[0]])
        
        # Test coloring all primitives explicitly
        visualizer.colorContextPrimitivesByData("temperature", uuids)
    
    def test_color_primitives_parameter_validation(self, visualizer_and_context):
        """Test parameter validation for colorContextPrimitivesByData"""
        visualizer, context, uuids = visualizer_and_context
        
        # Test empty data name
        with pytest.raises(ValueError, match="non-empty string"):
            visualizer.colorContextPrimitivesByData("")
        
        with pytest.raises(ValueError, match="non-empty string"):
            visualizer.colorContextPrimitivesByData(None)
        
        # Test invalid UUID list
        with pytest.raises(ValueError, match="non-empty list"):
            visualizer.colorContextPrimitivesByData("temperature", [])
        
        # Test invalid UUID types
        with pytest.raises(ValueError, match="non-negative integers"):
            visualizer.colorContextPrimitivesByData("temperature", ["invalid"])
        
        with pytest.raises(ValueError, match="non-negative integers"):
            visualizer.colorContextPrimitivesByData("temperature", [-1, -2, 1])
        
        # Test non-list UUID parameter
        with pytest.raises(ValueError, match="non-empty list"):
            visualizer.colorContextPrimitivesByData("temperature", "not_a_list")
    
    def test_color_primitives_with_nonexistent_data(self, visualizer_and_context):
        """Test behavior with non-existent data names"""
        visualizer, context, uuids = visualizer_and_context
        
        # This should not raise an exception at the Python level
        # The C++ code will handle missing data gracefully
        try:
            visualizer.colorContextPrimitivesByData("nonexistent_data")
        except VisualizerError:
            # This is acceptable - C++ may report error for missing data
            pass
    
    def test_color_primitives_uninitialized_visualizer(self):
        """Test error handling with uninitialized visualizer"""
        # Create visualizer but don't initialize it properly
        try:
            visualizer = Visualizer.__new__(Visualizer)
            visualizer.visualizer = None  # Simulate uninitialized state
            
            with pytest.raises(VisualizerError, match="not initialized"):
                visualizer.colorContextPrimitivesByData("temperature")
        except VisualizerError:
            # Expected if plugin not available
            pass
    
    def test_color_primitives_integration_workflow(self, visualizer_and_context):
        """Test complete workflow with primitive coloring

        This test validates the complete visualization workflow including primitive coloring
        and visualization updates in headless mode. The previous Helios C++ visualizer issues
        with plotUpdate() crashes in headless mode have been resolved.
        """
        visualizer, context, uuids = visualizer_and_context
        
        # Complete visualization workflow
        bg_color = RGBcolor(0.1, 0.1, 0.2)
        visualizer.setBackgroundColor(bg_color)
        visualizer.setLightingModel(visualizer.LIGHTING_PHONG)
        
        # Color by temperature
        visualizer.colorContextPrimitivesByData("temperature")

        # Update visualization (use plotUpdateWithVisibility for headless mode)
        visualizer.plotUpdateWithVisibility(hide_window=True)

        # Color by different data
        visualizer.colorContextPrimitivesByData("radiation_flux", uuids[:2])
        visualizer.plotUpdateWithVisibility(hide_window=True)
        
        # Test should complete without error


@pytest.mark.cross_platform
class TestVisualizerDataColoringMock:
    """Test primitive coloring by data in mock mode"""
    
    def test_color_primitives_mock_mode_error(self):
        """Test that mock mode provides informative error messages"""
        from pyhelios.plugins.registry import get_plugin_registry
        
        registry = get_plugin_registry()
        if registry.is_plugin_available('visualizer'):
            pytest.skip("Visualizer plugin available - not testing mock mode")
        
        # In mock mode, visualizer creation should fail
        with pytest.raises((VisualizerError, RuntimeError)) as exc_info:
            Visualizer(400, 300, headless=True)
        
        error_msg = str(exc_info.value).lower()
        # Error should mention rebuilding or graphics issues
        assert any(keyword in error_msg for keyword in 
                  ['rebuild', 'build', 'enable', 'visualizer', 'opengl', 'graphics', 'initialize', 'create'])


@pytest.mark.native_only
@pytest.mark.skipif(is_headless_environment(), reason="Skipping visualizer tests in headless environment")
class TestVisualizerNewMethodsNative:
    """Test newly implemented methods with native library"""
    
    def test_camera_field_of_view(self):
        """Test camera field of view methods"""
        with Visualizer(400, 300, headless=True) as visualizer:
            # Test field of view
            visualizer.setCameraFieldOfView(45.0)
            visualizer.setCameraFieldOfView(90.0)
            
            # Test field of view validation
            with pytest.raises(ValueError, match="between 0 and 180"):
                visualizer.setCameraFieldOfView(0.0)
            
            with pytest.raises(ValueError, match="between 0 and 180"):
                visualizer.setCameraFieldOfView(180.0)
            
            with pytest.raises(ValueError, match="must be numeric"):
                visualizer.setCameraFieldOfView("invalid")
    
    def test_camera_position_methods(self):
        """Test camera position retrieval methods"""
        with Visualizer(400, 300, headless=True) as visualizer:
            # Test getting camera position
            position, look_at = visualizer.getCameraPosition()
            assert isinstance(position, vec3)
            assert isinstance(look_at, vec3)
            
            # Test getting background color
            bg_color = visualizer.getBackgroundColor()
            assert isinstance(bg_color, RGBcolor)
    
    def test_window_size_methods(self):
        """Test window size retrieval methods"""
        with Visualizer(640, 480, headless=True) as visualizer:
            # Test window size
            width, height = visualizer.getWindowSize()
            assert isinstance(width, int)
            assert isinstance(height, int)
            assert width > 0
            assert height > 0
            
            # Test framebuffer size
            fb_width, fb_height = visualizer.getFramebufferSize()
            assert isinstance(fb_width, int)
            assert isinstance(fb_height, int)
            assert fb_width > 0
            assert fb_height > 0
    
    def test_colorbar_methods_basic(self):
        """Test basic colorbar control methods"""
        with Visualizer(400, 300, headless=True) as visualizer:
            # Test enabling/disabling colorbar
            visualizer.enableColorbar()
            visualizer.disableColorbar()
            
            # Test colorbar range
            visualizer.setColorbarRange(0.0, 100.0)
            
            with pytest.raises(ValueError, match="must be numeric"):
                visualizer.setColorbarRange("0", 100.0)
            
            with pytest.raises(ValueError, match="Minimum value must be less than maximum value"):
                visualizer.setColorbarRange(100.0, 50.0)
            
            # Test colorbar title
            visualizer.setColorbarTitle("Temperature (°C)")
            
            with pytest.raises(ValueError, match="must be a string"):
                visualizer.setColorbarTitle(123)
    
    def test_colormap_methods_basic(self):
        """Test basic colormap methods"""
        with Visualizer(400, 300, headless=True) as visualizer:
            # Test predefined colormaps
            visualizer.setColormap(Visualizer.COLORMAP_HOT)
            visualizer.setColormap(Visualizer.COLORMAP_COOL)
            visualizer.setColormap(Visualizer.COLORMAP_RAINBOW)
            
            # Test colormap validation
            with pytest.raises(ValueError, match="Colormap ID must be 0-5"):
                visualizer.setColormap(99)


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])