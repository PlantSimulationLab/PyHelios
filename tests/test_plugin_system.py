"""
Comprehensive tests for the PyHelios plugin system.

This module tests plugin metadata, dependency resolution,
configuration management, and runtime plugin detection.
"""

import pytest
import os
import sys
import tempfile
import platform
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import the plugin system components to test
from pyhelios.config.plugin_metadata import (
    PLUGIN_METADATA, get_plugin_metadata, get_all_plugin_names,
    get_platform_compatible_plugins, get_gpu_dependent_plugins
)
from pyhelios.config.dependency_resolver import (
    PluginDependencyResolver, ResolutionStatus
)
from pyhelios.config.config_manager import ConfigManager, ConfigurationError


class TestPluginMetadata:
    """Test plugin metadata functionality."""
    
    def test_plugin_metadata_structure(self):
        """Test that all plugins have required metadata fields."""
        assert len(PLUGIN_METADATA) > 0, "No plugin metadata found"
        
        for plugin_name, metadata in PLUGIN_METADATA.items():
            # Check required fields
            assert hasattr(metadata, 'name')
            assert hasattr(metadata, 'description')
            assert hasattr(metadata, 'system_dependencies')
            assert hasattr(metadata, 'plugin_dependencies')
            assert hasattr(metadata, 'platforms')
            assert hasattr(metadata, 'gpu_required')
            assert hasattr(metadata, 'optional')
            assert hasattr(metadata, 'test_symbols')
            
            # Check field types
            assert isinstance(metadata.description, str)
            assert isinstance(metadata.system_dependencies, list)
            assert isinstance(metadata.plugin_dependencies, list)
            assert isinstance(metadata.platforms, list)
            assert isinstance(metadata.gpu_required, bool)
            assert isinstance(metadata.optional, bool)
            assert isinstance(metadata.test_symbols, list)
            
            # Check that platforms are valid
            valid_platforms = {'windows', 'linux', 'macos'}
            for platform_name in metadata.platforms:
                assert platform_name in valid_platforms, f"Invalid platform: {platform_name}"
    
    def test_get_plugin_metadata(self):
        """Test getting metadata for specific plugins."""
        # Test existing plugin
        radiation_metadata = get_plugin_metadata('radiation')
        assert radiation_metadata is not None
        assert radiation_metadata.name == 'radiation'
        assert radiation_metadata.gpu_required == True
        
        # Test non-existent plugin
        assert get_plugin_metadata('nonexistent') is None
    
    def test_get_all_plugin_names(self):
        """Test getting all plugin names."""
        plugin_names = get_all_plugin_names()
        assert isinstance(plugin_names, list)
        assert len(plugin_names) > 0
        assert 'radiation' in plugin_names
        assert 'weberpenntree' in plugin_names
    
    
    def test_get_platform_compatible_plugins(self):
        """Test getting platform-compatible plugins."""
        compatible = get_platform_compatible_plugins()
        assert isinstance(compatible, list)
        assert len(compatible) > 0
        
        # Should include plugins compatible with current platform
        current_system = platform.system().lower()
        platform_map = {'windows': 'windows', 'linux': 'linux', 'darwin': 'macos'}
        current_platform = platform_map.get(current_system, current_system)
        
        for plugin in compatible:
            metadata = PLUGIN_METADATA[plugin]
            assert current_platform in metadata.platforms
    
    def test_get_gpu_dependent_plugins(self):
        """Test getting GPU-dependent plugins."""
        gpu_plugins = get_gpu_dependent_plugins()
        assert isinstance(gpu_plugins, list)
        assert 'radiation' in gpu_plugins
        
        # All returned plugins should have gpu_required=True
        for plugin in gpu_plugins:
            metadata = PLUGIN_METADATA[plugin]
            assert metadata.gpu_required == True




class TestDependencyResolver:
    """Test plugin dependency resolution."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.resolver = PluginDependencyResolver()
    
    def test_resolve_dependencies_simple(self):
        """Test simple dependency resolution."""
        resolver = PluginDependencyResolver()

        # Test with basic plugins (using integrated plugins)
        result = resolver.resolve_dependencies(['weberpenntree', 'solarposition'])

        assert result.status in [ResolutionStatus.SUCCESS, ResolutionStatus.WARNING]
        assert isinstance(result.final_plugins, list)
        assert 'weberpenntree' in result.final_plugins
        assert 'solarposition' in result.final_plugins
    
    def test_resolve_dependencies_with_gpu(self):
        """Test dependency resolution with GPU plugins."""
        resolver = PluginDependencyResolver()
        
        # Test with radiation plugin (GPU-dependent)
        result = resolver.resolve_dependencies(['radiation'])
        
        assert isinstance(result.final_plugins, list)
        
        # Radiation requires either Vulkan or CUDA GPU backend
        # If any GPU backend is available, radiation should be included
        has_gpu_backend = (result.system_check_results.get('vulkan', False) or
                          result.system_check_results.get('cuda', False))
        if has_gpu_backend:
            assert 'radiation' in result.final_plugins
        else:
            assert 'radiation' not in result.final_plugins
            assert len(result.warnings) > 0
    
    def test_validate_configuration(self):
        """Test configuration validation."""
        resolver = PluginDependencyResolver()
        
        # Test valid configuration (using integrated plugins)
        validation = resolver.validate_configuration(['weberpenntree', 'solarposition'])
        
        assert isinstance(validation, dict)
        assert 'valid_plugins' in validation
        assert 'invalid_plugins' in validation
        assert 'platform_compatible' in validation
        assert 'system_dependencies' in validation
        
        # Test invalid plugin
        validation = resolver.validate_configuration(['nonexistent'])
        assert 'nonexistent' in validation['invalid_plugins']
    
    def test_dependency_graph(self):
        """Test dependency graph generation."""
        resolver = PluginDependencyResolver()
        
        plugins = ['weberpenntree', 'radiation']
        graph = resolver.get_dependency_graph(plugins)
        
        assert isinstance(graph, dict)
        assert 'weberpenntree' in graph
        assert isinstance(graph['weberpenntree'], list)


class TestConfigManager:
    """Test configuration management."""
    
    def test_default_config(self):
        """Test default configuration creation."""
        config = ConfigManager()
        
        # Check default values
        assert config.plugin_config.selection_mode == "explicit"
        assert config.build_config.build_type == "Release"
        assert config.logging_config.level == "INFO"
    
    def test_yaml_config_loading(self):
        """Test loading configuration from YAML file."""
        yaml_content = """
plugins:
  selection_mode: "explicit"
  explicit_plugins:
    - weberpenntree
    - solarposition
  excluded_plugins:
    - radiation

build:
  build_type: "Debug"
  verbose: true

logging:
  level: "DEBUG"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            temp_filename = f.name
            
        try:
            config = ConfigManager(temp_filename)
            
            # Check parsed values
            assert config.plugin_config.selection_mode == "explicit"
            assert config.plugin_config.explicit_plugins == ["weberpenntree", "solarposition"]
            assert config.plugin_config.excluded_plugins == ["radiation"]
            assert config.build_config.build_type == "Debug"
            assert config.build_config.verbose == True
            assert config.logging_config.level == "DEBUG"
            
        finally:
            try:
                os.unlink(temp_filename)
            except (OSError, PermissionError):
                pass  # Ignore cleanup errors on Windows
    
    def test_plugin_resolution(self):
        """Test plugin resolution from configuration."""
        config = ConfigManager()
        
        # Test explicit plugin resolution (using integrated plugins)
        config.plugin_config.selection_mode = "explicit"
        config.plugin_config.explicit_plugins = ["weberpenntree", "solarposition"]

        plugins = config.resolve_plugin_selection()
        assert isinstance(plugins, list)
        assert len(plugins) > 0

        # Test explicit resolution (clear platform-specific config to avoid interference)
        config.plugin_config.selection_mode = "explicit"
        config.plugin_config.explicit_plugins = ["weberpenntree", "solarposition"]
        config.plugin_config.platform_specific = {}  # Clear platform-specific config

        plugins = config.resolve_plugin_selection()
        assert plugins == ["weberpenntree", "solarposition"]
    
    def test_config_validation(self):
        """Test configuration validation."""
        config = ConfigManager()
        
        # Test valid configuration
        validation = config.validate_configuration()
        assert isinstance(validation, dict)
        assert 'valid' in validation
        assert 'issues' in validation
        assert 'warnings' in validation
        
        # Test invalid configuration
        config.plugin_config.selection_mode = "invalid_mode"
        validation = config.validate_configuration()
        assert validation['valid'] == False
        assert len(validation['issues']) > 0
    
    def test_config_save_load(self):
        """Test saving and loading configuration."""
        original_config = ConfigManager()
        original_config.plugin_config.explicit_plugins = ["radiation", "visualizer"]
        original_config.build_config.build_type = "Debug"
        original_config.logging_config.level = "WARNING"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_filename = f.name
            
        try:
            # Save configuration
            original_config.save_config(temp_filename)
            
            # Load configuration
            loaded_config = ConfigManager(temp_filename)
            
            # Verify values match
            assert loaded_config.plugin_config.explicit_plugins == ["radiation", "visualizer"]
            assert loaded_config.build_config.build_type == "Debug"
            assert loaded_config.logging_config.level == "WARNING"
            
        finally:
            try:
                os.unlink(temp_filename)
            except (OSError, PermissionError):
                pass  # Ignore cleanup errors on Windows


class TestPluginRegistry:
    """Test plugin registry functionality."""
    
    @pytest.fixture
    def mock_plugin_functions(self):
        """Mock plugin detection functions for testing."""
        with patch('pyhelios.plugins.registry.detect_available_plugins') as mock_detect, \
             patch('pyhelios.plugins.registry.get_plugin_capabilities') as mock_capabilities:
            
            mock_detect.return_value = ['weberpenntree', 'solarposition']
            mock_capabilities.return_value = {
                'weberpenntree': {
                    'name': 'weberpenntree',
                    'description': 'Tree generation',
                    'available': True,
                    'gpu_required': False,
                    'dependencies': []
                },
                'solarposition': {
                    'name': 'solarposition',
                    'description': 'Solar position calculations',
                    'available': True,
                    'gpu_required': False,
                    'dependencies': []
                }
            }
            yield mock_detect, mock_capabilities
    
    def test_registry_initialization(self, mock_plugin_functions):
        """Test plugin registry initialization."""
        from pyhelios.plugins.registry import PluginRegistry
        
        registry = PluginRegistry()
        registry.initialize()
        
        assert registry._initialized == True
        available = registry.get_available_plugins()
        assert isinstance(available, list)
        assert 'weberpenntree' in available
    
    def test_plugin_availability_check(self, mock_plugin_functions):
        """Test plugin availability checking."""
        from pyhelios.plugins.registry import PluginRegistry
        
        registry = PluginRegistry()
        registry.initialize()
        
        # Test available plugin
        assert registry.is_plugin_available('weberpenntree') == True
        
        # Test unavailable plugin  
        assert registry.is_plugin_available('nonexistent') == False
    
    def test_plugin_requirements(self, mock_plugin_functions):
        """Test plugin requirement checking."""
        from pyhelios.plugins.registry import PluginRegistry, PluginNotAvailableError
        
        registry = PluginRegistry()
        registry.initialize()
        
        # Test requiring available plugin - should not raise
        registry.require_plugin('weberpenntree')
        
        # Test requiring unavailable plugin - should raise
        with pytest.raises(PluginNotAvailableError):
            registry.require_plugin('nonexistent')


class TestIntegration:
    """Integration tests for the complete plugin system."""
    
    def test_end_to_end_workflow(self):
        """Test complete plugin selection and validation workflow."""
        # Create configuration
        config = ConfigManager()
        config.plugin_config.selection_mode = "explicit"
        config.plugin_config.explicit_plugins = ["weberpenntree"]
        
        # Resolve plugins
        plugins = config.resolve_plugin_selection()
        assert isinstance(plugins, list)
        assert len(plugins) > 0
        
        # Validate with dependency resolver
        resolver = PluginDependencyResolver()
        result = resolver.resolve_dependencies(plugins)
        
        assert result.status in [ResolutionStatus.SUCCESS, ResolutionStatus.WARNING]
        assert isinstance(result.final_plugins, list)
    
    def test_cross_platform_compatibility(self):
        """Test that the system works across different platforms."""
        # Test basic plugin compatibility on current platform
        try:
            compatible_plugins = get_platform_compatible_plugins()
            assert isinstance(compatible_plugins, list)
            assert len(compatible_plugins) > 0
            
            # Test that common integrated plugins are available
            common_plugins = ["weberpenntree", "solarposition", "visualizer"]
            for plugin in common_plugins:
                if plugin in compatible_plugins:
                    assert plugin in PLUGIN_METADATA
        except Exception as e:
            pytest.fail(f"Platform compatibility check failed: {e}")
    
    def test_mock_mode_compatibility(self):
        """Test that mock mode works correctly."""
        # Test that plugin metadata works without native libraries
        plugin_names = get_all_plugin_names()
        assert len(plugin_names) > 0
        
        # Test dependency resolution in mock environment
        resolver = PluginDependencyResolver()
        result = resolver.resolve_dependencies(['weberpenntree'])
        
        # Should work even without native libraries
        assert isinstance(result.final_plugins, list)


@pytest.mark.slow
class TestPerformance:
    """Performance tests for plugin system."""
    
    def test_metadata_loading_performance(self):
        """Test that metadata loading is fast."""
        import time
        
        start_time = time.time()
        for _ in range(100):
            get_all_plugin_names()
            get_platform_compatible_plugins()
        end_time = time.time()
        
        # Should complete 100 iterations in under 1 second
        assert (end_time - start_time) < 1.0
    
    def test_dependency_resolution_performance(self):
        """Test that dependency resolution is reasonably fast."""
        import time
        
        resolver = PluginDependencyResolver()
        all_plugins = get_all_plugin_names()
        
        start_time = time.time()
        result = resolver.resolve_dependencies(all_plugins)
        end_time = time.time()
        
        # Should resolve all plugins in under 5 seconds
        assert (end_time - start_time) < 5.0
        assert isinstance(result.final_plugins, list)


@pytest.mark.cross_platform
class TestPluginCLI:
    """Tests for the `python -m pyhelios.plugins` command-line interface."""

    def _run_cli(self, *args, extra_env=None):
        """Run the plugin CLI in a subprocess and return (returncode, output)."""
        import subprocess
        repo_root = Path(__file__).parent.parent
        env = {**os.environ, 'PYTHONPATH': str(repo_root)}
        if extra_env:
            env.update(extra_env)
        proc = subprocess.run(
            [sys.executable, '-m', 'pyhelios.plugins', *args],
            capture_output=True, text=True, cwd=str(repo_root),
            env=env, errors='replace',
        )
        return proc.returncode, proc.stdout + proc.stderr

    def test_info_reports_runtime_availability(self):
        """`plugins info <name>` must report availability, not an internal error.

        Regression: cmd_info called the no-argument get_plugin_info() from
        pyhelios.plugins with a plugin name, raising TypeError. The broad
        except in main() turned that into "Error: get_plugin_info() takes 0
        positional arguments but 1 was given" under a "Runtime Status" heading,
        which reads like the plugin is broken rather than the CLI.
        """
        returncode, output = self._run_cli('info', 'radiation')

        assert 'takes 0 positional arguments' not in output, (
            f"cmd_info called get_plugin_info() with an argument:\n{output}"
        )
        assert returncode == 0, f"`plugins info radiation` failed:\n{output}"
        # It must actually state availability.
        assert 'Available:' in output, f"No availability reported:\n{output}"

    def test_info_rejects_unknown_plugin(self):
        """An unknown plugin name is reported clearly and exits non-zero."""
        returncode, output = self._run_cli('info', 'not_a_real_plugin')

        assert returncode == 1
        assert 'Unknown plugin' in output

    @pytest.mark.parametrize('command', [
        ('status',),
        ('discover',),
        ('info', 'radiation'),
        ('info', 'not_a_real_plugin'),
    ])
    def test_cli_survives_legacy_console_encoding(self, command):
        """The CLI must not crash on consoles that cannot encode its symbols.

        Regression: the status glyphs are non-ASCII, and a Windows console
        running a legacy codepage encodes stdout as cp1252, whose codec has no
        mapping for them. Every affected command died with UnicodeEncodeError
        instead of printing its report, and the broad except in main() then
        died the same way trying to print an error marker. cp1252 is forced
        here so the failure reproduces on any platform.
        """
        expected_returncode = 1 if command[-1] == 'not_a_real_plugin' else 0
        returncode, output = self._run_cli(
            *command, extra_env={'PYTHONIOENCODING': 'cp1252'}
        )

        assert 'UnicodeEncodeError' not in output, (
            f"`plugins {' '.join(command)}` crashed on a cp1252 console:\n{output}"
        )
        assert returncode == expected_returncode, (
            f"`plugins {' '.join(command)}` exited {returncode} on a cp1252 "
            f"console:\n{output}"
        )


@pytest.mark.cross_platform
class TestLibraryLoadErrorIsNotSwallowed:
    """A library that exists but will not load must not be reported as "no plugins available".

    The loader distinguishes "no library file" from "library present but unloadable" and builds
    a message naming the missing system library. The registry used to catch every exception and
    fall back to an empty plugin set, which turned a missing libGL into "plugin not available"
    and pointed users at `build_helios --plugins <name>` -- a rebuild that cannot fix a missing
    system dependency, and that produces a single-plugin library breaking everything else.
    """

    def test_library_load_error_propagates(self):
        from pyhelios.plugins.registry import PluginRegistry
        from pyhelios.plugins.loader import LibraryLoadError

        message = (
            "Failed to load native Helios library for platform 'Linux'.\n"
            "The library file was found but could not be loaded:\n"
            "  /x/libhelios.so\n    libGL.so.1: cannot open shared object file\n"
            "This indicates missing system libraries: libGL.so.1\n"
        )

        registry = PluginRegistry()
        with patch('pyhelios.plugins.registry.detect_available_plugins',
                   side_effect=LibraryLoadError(message)):
            with pytest.raises(LibraryLoadError, match="libGL"):
                registry.initialize()

    def test_unrelated_errors_still_degrade_gracefully(self):
        """Only load failures propagate; other faults keep the old empty-set behaviour."""
        from pyhelios.plugins.registry import PluginRegistry

        registry = PluginRegistry()
        with patch('pyhelios.plugins.registry.detect_available_plugins',
                   side_effect=ValueError("something unrelated")):
            registry.initialize()

        assert registry.get_available_plugins() == []


@pytest.mark.cross_platform
class TestWheelRuntimeAssets:
    """Assets a plugin loads at runtime must be staged into the wheel.

    Building a plugin into the wheel does not ship its data files: prepare_wheel.py copies only
    directories named in its per-plugin allowlist. A missing entry builds and tests clean, then
    raises at the first call that resolves the asset.
    """

    @staticmethod
    def _prepare_wheel_source():
        """Source of copy_assets_for_packaging, or skip if the repo build scripts are absent.

        These assertions introspect build_scripts/prepare_wheel.py, which ships in the repo but
        not in the wheel. The wheel test jobs run from an isolated directory holding only the
        copied test suite, so there is nothing to introspect there.
        """
        import inspect

        repo_root = Path(__file__).resolve().parents[1]
        if not (repo_root / 'build_scripts' / 'prepare_wheel.py').exists():
            pytest.skip("wheel asset staging tests need the repo "
                        "(build_scripts/prepare_wheel.py not found)")

        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        from build_scripts import prepare_wheel

        return inspect.getsource(prepare_wheel.copy_assets_for_packaging)

    def test_radiation_camera_library_is_staged(self):
        """setCameraSpectralResponseFromLibrary() resolves camera_library/camera_library.xml."""
        source = self._prepare_wheel_source()
        assert "'camera_library'" in source or '"camera_library"' in source, (
            "radiation's camera_library directory is not staged into the wheel, so "
            "setCameraSpectralResponseFromLibrary() raises at runtime in an installed wheel"
        )

    def test_staged_asset_dirs_exist_in_helios_core(self):
        """Every directory named in the allowlist must exist, or it silently stages nothing."""
        import re

        source = self._prepare_wheel_source()

        repo_root = Path(__file__).resolve().parents[1]
        plugins_src = repo_root / 'helios-core' / 'plugins'
        if not plugins_src.exists():
            pytest.skip("helios-core plugins directory not available")
        match = re.search(r'plugin_asset_dirs = \{(.*?)\n    \}', source, re.DOTALL)
        assert match, "could not locate plugin_asset_dirs in prepare_wheel.py"

        missing = []
        for plugin, subdir in re.findall(r"'([\w]+)':\s*\[([^\]]*)\]", match.group(1)):
            for entry in re.findall(r"'([^']+)'", subdir):
                if not (plugins_src / plugin / entry).exists():
                    missing.append(f"{plugin}/{entry}")

        assert not missing, f"allowlisted asset directories do not exist: {missing}"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])