"""
Comprehensive tests for the PyHelios plugin system.

This module tests plugin metadata, dependency resolution,
configuration management, and runtime plugin detection.
"""

import pytest
import os
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
        
        # Test with basic plugins
        result = resolver.resolve_dependencies(['weberpenntree', 'canopygenerator'])
        
        assert result.status in [ResolutionStatus.SUCCESS, ResolutionStatus.WARNING]
        assert isinstance(result.final_plugins, list)
        assert 'weberpenntree' in result.final_plugins
        assert 'canopygenerator' in result.final_plugins
    
    def test_resolve_dependencies_with_gpu(self):
        """Test dependency resolution with GPU plugins."""
        resolver = PluginDependencyResolver()
        
        # Test with radiation plugin (GPU-dependent)
        result = resolver.resolve_dependencies(['radiation'])
        
        assert isinstance(result.final_plugins, list)
        
        # If CUDA is available, radiation should be included
        # If not, it should be removed with warnings
        if result.system_check_results.get('cuda', False):
            assert 'radiation' in result.final_plugins
        else:
            assert 'radiation' not in result.final_plugins
            assert len(result.warnings) > 0
    
    def test_validate_configuration(self):
        """Test configuration validation."""
        resolver = PluginDependencyResolver()
        
        # Test valid configuration
        validation = resolver.validate_configuration(['weberpenntree', 'canopygenerator'])
        
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
    - canopygenerator
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
            assert config.plugin_config.explicit_plugins == ["weberpenntree", "canopygenerator"]
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
        
        # Test explicit plugin resolution
        config.plugin_config.selection_mode = "explicit"
        config.plugin_config.explicit_plugins = ["weberpenntree", "canopygenerator"]
        
        plugins = config.resolve_plugin_selection()
        assert isinstance(plugins, list)
        assert len(plugins) > 0
        
        # Test explicit resolution (clear platform-specific config to avoid interference)
        config.plugin_config.selection_mode = "explicit"
        config.plugin_config.explicit_plugins = ["weberpenntree", "canopygenerator"]
        config.plugin_config.platform_specific = {}  # Clear platform-specific config
        
        plugins = config.resolve_plugin_selection()
        assert plugins == ["weberpenntree", "canopygenerator"]
    
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
            
            mock_detect.return_value = ['weberpenntree', 'canopygenerator']
            mock_capabilities.return_value = {
                'weberpenntree': {
                    'name': 'weberpenntree',
                    'description': 'Tree generation',
                    'available': True,
                    'gpu_required': False,
                    'dependencies': []
                },
                'canopygenerator': {
                    'name': 'canopygenerator',
                    'description': 'Canopy generation',
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
            
            # Test that common plugins are available
            common_plugins = ["weberpenntree", "canopygenerator", "solarposition"]
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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])