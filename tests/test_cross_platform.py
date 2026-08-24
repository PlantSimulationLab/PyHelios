"""
Cross-platform tests for PyHelios.

These tests verify that PyHelios works across different platforms and
handles mock mode appropriately when native libraries aren't available.
"""

import pytest
import platform
import sys
import ctypes
from unittest.mock import patch, Mock
from pyhelios.plugins import loader, get_plugin_info, print_plugin_status
from tests.test_utils import PlatformHelper


@pytest.mark.cross_platform
class TestPlatformDetection:
    """Test platform detection and library loading logic."""
    
    def test_platform_detection(self, platform_info):
        """Test that platform is correctly detected."""
        assert platform_info['name'] in ['Windows', 'Darwin', 'Linux']
        
        # Exactly one platform should be true
        platform_flags = [
            platform_info['is_windows'],
            platform_info['is_macos'],
            platform_info['is_linux']
        ]
        assert sum(platform_flags) == 1
    
    def test_library_loader_initialization(self):
        """Test that library loader can be initialized."""
        test_loader = loader.CrossPlatformLibraryLoader("/tmp/test")
        assert test_loader.platform_name == platform.system()
        assert test_loader.plugin_dir == "/tmp/test"
    
    def test_library_config_exists_for_platform(self):
        """Test that library configuration exists for current platform."""
        platform_name = platform.system()
        test_loader = loader.CrossPlatformLibraryLoader("/tmp/test")
        if platform_name in test_loader.LIBRARY_CONFIG:
            config = test_loader.LIBRARY_CONFIG[platform_name]
            assert 'primary' in config
            assert 'loader' in config
            assert 'alternatives' in config
            assert 'dependencies' in config
        else:
            # Should fall back to mock mode for unsupported platforms
            pytest.skip(f"Platform {platform_name} not in official configuration")
    
    def test_get_library_paths(self):
        """Test library path generation."""
        test_loader = loader.CrossPlatformLibraryLoader("/test/path")
        paths = test_loader.get_library_paths()
        
        if test_loader.platform_name in test_loader.LIBRARY_CONFIG:
            assert 'primary' in paths
            assert paths['primary'].startswith("/test/path")
        else:
            assert paths == {}
    
    def test_plugin_info_accessible(self):
        """Test that plugin information is accessible."""
        info = get_plugin_info()
        
        assert 'platform' in info
        assert 'native_available' in info
        assert 'is_mock' in info
        assert info['platform'] == platform.system()
    
    def test_print_plugin_status_no_error(self, capsys):
        """Test that plugin status can be printed without error."""
        print_plugin_status()
        captured = capsys.readouterr()
        assert "PyHelios Plugin Status:" in captured.out


@pytest.mark.mock_mode 
class TestMockModeOperation:
    """Test operation in mock mode (no native libraries)."""
    
    def test_mock_library_creation(self):
        """Test mock library creation and basic operation."""
        mock_lib = loader.MockLibrary()
        
        # Should be able to access any function name
        func = mock_lib.some_function
        assert callable(func)
        
        # But calling it should raise an informative error
        with pytest.raises(RuntimeError, match="mock mode"):
            func()
    
    def test_forced_mock_mode(self):
        """Test forcing mock mode even when native library might be available."""
        # This test uses an isolated mock library without affecting global state
        mock_library = loader.MockLibrary()
        assert isinstance(mock_library, loader.MockLibrary)
        
        # Any function access should work but calls should fail
        with pytest.raises(RuntimeError, match="mock mode"):
            mock_library.createContext()
    
    def test_mock_mode_error_messages(self):
        """Test that mock mode provides helpful error messages."""
        mock_lib = loader.MockLibrary()
        
        try:
            mock_lib.createContext()
        except RuntimeError as e:
            error_msg = str(e)
            assert "mock mode" in error_msg
            assert "createContext" in error_msg
            assert "Native Helios library not available" in error_msg


@pytest.mark.unit
class TestLibraryLoaderFunctionality:
    """Test core library loader functionality."""
    
    def test_loader_singleton(self):
        """Test that loader behaves as singleton."""
        loader1 = loader.get_loader()
        loader2 = loader.get_loader()
        assert loader1 is loader2
    
    def test_library_info_structure(self):
        """Test library info has expected structure."""
        info = loader.get_library_info()
        
        required_keys = ['platform', 'is_mock', 'plugin_dir', 'available_files']
        for key in required_keys:
            assert key in info
    
    def test_library_validation_mock(self):
        """Test library validation with mock library."""
        test_loader = loader.CrossPlatformLibraryLoader("/nonexistent/path")
        test_loader.library = loader.MockLibrary()
        test_loader.is_mock = True
        
        # Mock library should always validate as "valid"
        assert test_loader.validate_library() is True
    
    def test_check_dependencies_missing_dir(self):
        """Test dependency checking with missing directory."""
        test_loader = loader.CrossPlatformLibraryLoader("/nonexistent/path")
        
        # Should not crash, should return True (dependencies are optional)
        result = test_loader.check_dependencies()
        assert result is True
    
    def test_unsupported_platform_handling(self):
        """Test handling of unsupported platforms."""
        # Mock unsupported platform - should raise LibraryLoadError
        with patch('platform.system', return_value='UnsupportedOS'):
            test_loader = loader.CrossPlatformLibraryLoader("/test/path")
            
            # Should raise exception for unsupported platform
            with pytest.raises(loader.LibraryLoadError) as exc_info:
                test_loader.load_library()
            
            assert "not officially supported" in str(exc_info.value)
            assert "PYHELIOS_DEV_MODE=1" in str(exc_info.value)

    def test_dev_mode_works_without_a_native_library(self, monkeypatch):
        """PYHELIOS_DEV_MODE=1 must yield a mock library when no library exists.

        The error raised when no library is found tells the user to set
        PYHELIOS_DEV_MODE=1, so that variable has to actually rescue the situation.
        It could not: load_helios_library() called get_loader() before acting on the
        dev-mode flag, and get_loader() resolves a library directory eagerly via
        _find_library_directory(), which raises when there is nothing to find. The
        advice in the message was therefore impossible to follow.
        """
        monkeypatch.setattr(loader, "_loader_instance", None)
        monkeypatch.setattr(
            loader, "_find_library_directory",
            Mock(side_effect=loader.LibraryLoadError("Native Helios library not found")),
        )
        monkeypatch.setenv("PYHELIOS_DEV_MODE", "1")

        library = loader.load_helios_library()

        assert isinstance(library, loader.MockLibrary)
        assert loader.get_loader().is_mock is True

    def test_force_mock_works_without_a_native_library(self, monkeypatch):
        """The explicit force_mock argument must not need a library directory either."""
        monkeypatch.setattr(loader, "_loader_instance", None)
        monkeypatch.setattr(
            loader, "_find_library_directory",
            Mock(side_effect=loader.LibraryLoadError("Native Helios library not found")),
        )
        monkeypatch.delenv("PYHELIOS_DEV_MODE", raising=False)
        monkeypatch.delenv("PYHELIOS_MOCK_MODE", raising=False)

        library = loader.load_helios_library(force_mock=True)

        assert isinstance(library, loader.MockLibrary)

    def test_missing_library_still_raises_without_dev_mode(self, monkeypatch):
        """Without dev mode, a missing library must still fail fast rather than mock."""
        monkeypatch.setattr(loader, "_loader_instance", None)
        monkeypatch.setattr(
            loader, "_find_library_directory",
            Mock(side_effect=loader.LibraryLoadError("Native Helios library not found")),
        )
        monkeypatch.delenv("PYHELIOS_DEV_MODE", raising=False)
        monkeypatch.delenv("PYHELIOS_MOCK_MODE", raising=False)

        with pytest.raises(loader.LibraryLoadError):
            loader.load_helios_library()


@pytest.mark.cross_platform
class TestCrossPlatformDataTypes:
    """Test that DataTypes work across all platforms."""
    
    def test_vec3_creation(self):
        """Test Vec3 creation works on all platforms."""
        from pyhelios import DataTypes
        
        v = DataTypes.vec3(1.0, 2.0, 3.0)
        assert v.x == 1.0
        assert v.y == 2.0
        assert v.z == 3.0
    
    def test_color_creation(self):
        """Test RGBcolor creation works on all platforms."""
        from pyhelios import DataTypes
        
        c = DataTypes.RGBcolor(0.5, 0.7, 0.2)
        assert c.r == pytest.approx(0.5)
        assert c.g == pytest.approx(0.7)
        assert c.b == pytest.approx(0.2)
    
    def test_all_data_types_importable(self):
        """Test that all DataTypes can be imported on any platform."""
        from pyhelios import DataTypes
        
        # Test that all expected types exist
        types_to_test = [
            'vec2', 'vec3', 'vec4',
            'int2', 'int3', 'int4',
            'RGBcolor', 'RGBAcolor',
            'SphericalCoord'
        ]
        
        for type_name in types_to_test:
            assert hasattr(DataTypes, type_name)
            type_class = getattr(DataTypes, type_name)
            assert callable(type_class)


@pytest.mark.integration
class TestPlatformSpecificIntegration:
    """Integration tests that depend on platform-specific libraries."""
    
    @PlatformHelper.skip_if_no_native_library()
    def test_context_creation_with_native_library(self):
        """Test Context creation when native library is available."""
        from pyhelios import Context
        
        with Context() as ctx:
            assert ctx is not None
            # Should be able to perform basic operations
            count = ctx.getPrimitiveCount()
            assert count == 0
    
    @PlatformHelper.skip_if_no_native_library()
    def test_tree_creation_with_native_library(self):
        """Test WeberPennTree creation when native library is available."""
        from pyhelios import Context
        from pyhelios.plugins.registry import get_plugin_registry
        
        # Skip if weberpenntree plugin is not available
        registry = get_plugin_registry()
        if not registry.is_plugin_available('weberpenntree'):
            pytest.skip("WeberPennTree plugin not available in current build")
        
        from pyhelios import WeberPennTree, WPTType
        
        with Context() as ctx:
            with WeberPennTree(ctx) as wpt:
                assert wpt is not None
                # Should be able to build a tree
                tree_id = wpt.buildTree(WPTType.LEMON)
                assert isinstance(tree_id, int)


@pytest.mark.native_only
class TestNativeLibrarySpecific:
    """Tests that specifically require native library functionality."""
    
    def test_library_validation_native(self):
        """Test library validation with native library."""
        if not loader.is_native_library_available():
            pytest.skip("Native library not available")
        
        result = loader.validate_library()
        assert result is True
    
    def test_native_library_functions_available(self):
        """Test that expected functions are available in native library."""
        if not loader.is_native_library_available():
            pytest.skip("Native library not available")
        
        helios_lib = loader.load_helios_library()
        
        # Test core functions exist
        core_functions = [
            'createContext',
            'destroyContext',
            'addPatch'
        ]
        
        for func_name in core_functions:
            assert hasattr(helios_lib, func_name)
            func = getattr(helios_lib, func_name)
            assert callable(func)


@pytest.mark.cross_platform
class TestErrorHandling:
    """Test error handling across platforms."""
    
    def test_import_failure_handling(self):
        """Test handling of import failures."""
        # This should not raise an exception even if libraries are missing
        try:
            from pyhelios import Context
            # If we can import Context, it should either work or fail gracefully
            assert Context is not None
        except ImportError:
            pytest.fail("PyHelios should be importable even without native libraries")
    
    def test_graceful_degradation(self):
        """Test graceful degradation when native features unavailable."""
        from pyhelios.plugins import get_plugin_info
        
        info = get_plugin_info()
        
        # Should always have basic info regardless of library availability
        assert 'platform' in info
        assert 'is_mock' in info
        
        if info['is_mock']:
            # In mock mode, should still be functional for basic operations
            assert info['native_available'] is False
        else:
            # With native library, should have full functionality
            assert info['native_available'] is True


class TestPlatformCompatibility:
    """Test compatibility across different Python versions and platforms."""
    
    def test_python_version_compatibility(self):
        """Test that PyHelios works with current Python version."""
        version_info = sys.version_info
        
        # Should work with Python 3.7+
        assert version_info.major == 3
        assert version_info.minor >= 7
    
    def test_ctypes_availability(self):
        """Test that ctypes is available (required for all functionality)."""
        import ctypes
        assert ctypes is not None
        
        # Test basic ctypes functionality
        assert hasattr(ctypes, 'CDLL')
        assert hasattr(ctypes, 'WinDLL') or not PlatformHelper.is_windows()
    
    @pytest.mark.parametrize("platform_name", ['Windows', 'Darwin', 'Linux'])
    def test_loader_config_completeness(self, platform_name):
        """Test that loader configuration is complete for each platform."""
        # Create a loader instance to get the config
        test_loader = loader.CrossPlatformLibraryLoader("/tmp/test")
        config = test_loader.LIBRARY_CONFIG.get(platform_name)
        if config:
            required_keys = ['primary', 'loader', 'alternatives', 'dependencies']
            for key in required_keys:
                assert key in config
                
            # Verify loader is appropriate ctypes class
            if platform_name == 'Windows':
                # Only check this if we're actually on Windows or if WinDLL is available
                try:
                    assert config['loader'] == ctypes.WinDLL
                except AttributeError:
                    # WinDLL not available, should fall back to CDLL
                    assert config['loader'] == ctypes.CDLL
            else:
                assert config['loader'] == ctypes.CDLL