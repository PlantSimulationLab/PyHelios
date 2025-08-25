"""
Configuration management for PyHelios.

This module handles loading and processing configuration files for plugin
selection, build options, and system settings.
"""

import os
import platform
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

from .dependency_resolver import PluginDependencyResolver


@dataclass
class BuildConfig:
    """Build configuration settings."""
    build_type: str = "Release"
    cmake_args: List[str] = None
    parallel_jobs: int = 0
    verbose: bool = False
    
    def __post_init__(self):
        if self.cmake_args is None:
            self.cmake_args = []


@dataclass
class SystemConfig:
    """System configuration settings."""
    force_mock_mode: bool = False
    environment: Dict[str, str] = None
    
    def __post_init__(self):
        if self.environment is None:
            self.environment = {}


@dataclass 
class LoggingConfig:
    """Logging configuration settings."""
    level: str = "INFO"
    plugin_detection: bool = True
    build_logging: bool = True


@dataclass
class PluginConfig:
    """Plugin configuration settings."""
    selection_mode: str = "explicit"
    explicit_plugins: List[str] = None
    excluded_plugins: List[str] = None
    include_optional: bool = True
    platform_specific: Dict[str, Dict[str, List[str]]] = None
    
    def __post_init__(self):
        if self.explicit_plugins is None:
            self.explicit_plugins = []
        if self.excluded_plugins is None:
            self.excluded_plugins = []
        if self.platform_specific is None:
            self.platform_specific = {}


class ConfigurationError(Exception):
    """Raised when configuration is invalid or cannot be loaded."""
    pass


class ConfigManager:
    """Manages PyHelios configuration loading and processing."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file (optional)
        """
        self.config_file = config_file
        self.plugin_config = PluginConfig()
        self.build_config = BuildConfig()
        self.system_config = SystemConfig()
        self.logging_config = LoggingConfig()
        
        # Load configuration if file provided or default exists
        if config_file:
            self.load_config(config_file)
        else:
            self._try_load_default_config()
    
    def _try_load_default_config(self):
        """Try to load default configuration files."""
        default_paths = [
            "pyhelios_config.yaml",
            "pyhelios_config.yml", 
            ".pyhelios.yaml",
            ".pyhelios.yml",
            os.path.expanduser("~/.pyhelios.yaml"),
            os.path.expanduser("~/.pyhelios.yml")
        ]
        
        for path in default_paths:
            if os.path.exists(path):
                try:
                    self.load_config(path)
                    break
                except Exception:
                    continue  # Try next file
    
    def load_config(self, config_file: str):
        """
        Load configuration from YAML file.
        
        Args:
            config_file: Path to configuration file
            
        Raises:
            ConfigurationError: If configuration file cannot be loaded or is invalid
        """
        try:
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            if not isinstance(config_data, dict):
                raise ConfigurationError("Configuration file must contain a YAML dictionary")
            
            self._parse_config(config_data)
            self.config_file = config_file
            
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {config_file}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration: {e}")
    
    def _parse_config(self, config_data: Dict[str, Any]):
        """Parse configuration data into typed config objects."""
        
        # Parse plugin configuration
        if 'plugins' in config_data:
            plugin_data = config_data['plugins']
            self.plugin_config = PluginConfig(
                selection_mode=plugin_data.get('selection_mode', 'explicit'),
                explicit_plugins=plugin_data.get('explicit_plugins', []),
                excluded_plugins=plugin_data.get('excluded_plugins', []),
                include_optional=plugin_data.get('include_optional', True),
                platform_specific=plugin_data.get('platform_specific', {})
            )
        
        # Parse build configuration
        if 'build' in config_data:
            build_data = config_data['build']
            self.build_config = BuildConfig(
                build_type=build_data.get('build_type', 'Release'),
                cmake_args=build_data.get('cmake_args', []),
                parallel_jobs=build_data.get('parallel_jobs', 0),
                verbose=build_data.get('verbose', False)
            )
        
        # Parse system configuration
        if 'system' in config_data:
            system_data = config_data['system']
            self.system_config = SystemConfig(
                force_mock_mode=system_data.get('force_mock_mode', False),
                environment=system_data.get('environment', {})
            )
        
        # Parse logging configuration
        if 'logging' in config_data:
            logging_data = config_data['logging']
            self.logging_config = LoggingConfig(
                level=logging_data.get('level', 'INFO'),
                plugin_detection=logging_data.get('plugin_detection', True),
                build_logging=logging_data.get('build_logging', True)
            )
    
    def resolve_plugin_selection(self) -> List[str]:
        """
        Resolve the final plugin selection based on configuration.
        
        Returns:
            List of plugin names to build
            
        Raises:
            ConfigurationError: If plugin configuration is invalid
        """
        plugins = []
        
        if self.plugin_config.selection_mode == "explicit":
            # Use explicit plugin list
            plugins = list(self.plugin_config.explicit_plugins)
            
        elif self.plugin_config.selection_mode == "auto":
            # Auto-select based on system capabilities
            resolver = PluginDependencyResolver()
            gpu_available = resolver._check_cuda()
            
            if gpu_available:
                plugins = ["weberpenntree", "canopygenerator", "solarposition", "radiation", "visualizer", "energybalance"]
            else:
                plugins = ["weberpenntree", "canopygenerator", "solarposition", "visualizer", "energybalance"]
        else:
            raise ConfigurationError(
                f"Invalid selection_mode '{self.plugin_config.selection_mode}'. "
                "Must be 'explicit' or 'auto'"
            )
        
        # Apply platform-specific modifications
        current_platform = self._get_current_platform()
        if current_platform in self.plugin_config.platform_specific:
            platform_config = self.plugin_config.platform_specific[current_platform]
            
            # Add platform-specific plugins
            if 'additional_plugins' in platform_config:
                plugins.extend(platform_config['additional_plugins'])
            
            # Remove platform-specific exclusions
            if 'excluded_plugins' in platform_config:
                for plugin in platform_config['excluded_plugins']:
                    if plugin in plugins:
                        plugins.remove(plugin)
        
        # Apply global exclusions
        for plugin in self.plugin_config.excluded_plugins:
            if plugin in plugins:
                plugins.remove(plugin)
        
        # Remove duplicates and maintain order
        seen = set()
        unique_plugins = []
        for plugin in plugins:
            if plugin not in seen:
                seen.add(plugin)
                unique_plugins.append(plugin)
        
        return unique_plugins
    
    def _get_current_platform(self) -> str:
        """Get current platform name for configuration matching."""
        system = platform.system().lower()
        platform_map = {
            "windows": "windows",
            "linux": "linux",
            "darwin": "macos"
        }
        return platform_map.get(system, system)
    
    def get_cmake_args(self) -> List[str]:
        """Get complete CMake arguments including build type."""
        args = list(self.build_config.cmake_args)
        
        # Add build type if not already specified
        build_type_specified = any('-DCMAKE_BUILD_TYPE=' in arg for arg in args)
        if not build_type_specified:
            args.append(f'-DCMAKE_BUILD_TYPE={self.build_config.build_type}')
        
        return args
    
    def apply_environment_variables(self):
        """Apply environment variables from configuration."""
        for key, value in self.system_config.environment.items():
            os.environ[key] = str(value)
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate the current configuration.
        
        Returns:
            Dictionary with validation results
        """
        issues = []
        warnings = []
        
        # Validate plugin selection
        try:
            plugins = self.resolve_plugin_selection()
            
            # Check if any plugins were selected
            if not plugins:
                issues.append("No plugins selected - this may result in limited functionality")
            
            # Use dependency resolver to validate
            resolver = PluginDependencyResolver()
            validation = resolver.validate_configuration(plugins)
            
            if validation['invalid_plugins']:
                issues.extend([f"Invalid plugin: {p}" for p in validation['invalid_plugins']])
            
            if validation['platform_incompatible']:
                warnings.extend([f"Platform incompatible plugin: {p}" for p in validation['platform_incompatible']])
            
        except ConfigurationError as e:
            issues.append(str(e))
        
        # Validate build configuration
        valid_build_types = ['Release', 'Debug', 'RelWithDebInfo', 'MinSizeRel']
        if self.build_config.build_type not in valid_build_types:
            issues.append(f"Invalid build_type '{self.build_config.build_type}'. Must be one of: {valid_build_types}")
        
        # Validate logging configuration
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.logging_config.level not in valid_log_levels:
            issues.append(f"Invalid log level '{self.logging_config.level}'. Must be one of: {valid_log_levels}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'config_file': self.config_file
        }
    
    def save_config(self, output_file: str):
        """
        Save current configuration to a YAML file.
        
        Args:
            output_file: Path to output configuration file
        """
        config_data = {
            'plugins': {
                'selection_mode': self.plugin_config.selection_mode,
                'explicit_plugins': self.plugin_config.explicit_plugins,
                'excluded_plugins': self.plugin_config.excluded_plugins,
                'include_optional': self.plugin_config.include_optional,
                'platform_specific': self.plugin_config.platform_specific
            },
            'build': {
                'build_type': self.build_config.build_type,
                'cmake_args': self.build_config.cmake_args,
                'parallel_jobs': self.build_config.parallel_jobs,
                'verbose': self.build_config.verbose
            },
            'system': {
                'force_mock_mode': self.system_config.force_mock_mode,
                'environment': self.system_config.environment
            },
            'logging': {
                'level': self.logging_config.level,
                'plugin_detection': self.logging_config.plugin_detection,
                'build_logging': self.logging_config.build_logging
            }
        }
        
        with open(output_file, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)
    
    def print_summary(self):
        """Print a summary of the current configuration."""
        print("PyHelios Configuration Summary")
        print("=" * 30)
        
        print(f"Configuration file: {self.config_file or 'Default/Built-in'}")
        
        print(f"\nPlugin Configuration:")
        print(f"  Selection mode: {self.plugin_config.selection_mode}")
        if self.plugin_config.selection_mode == "explicit":
            print(f"  Explicit plugins: {self.plugin_config.explicit_plugins}")
        
        if self.plugin_config.excluded_plugins:
            print(f"  Excluded plugins: {self.plugin_config.excluded_plugins}")
        
        try:
            resolved_plugins = self.resolve_plugin_selection()
            print(f"  Resolved plugins ({len(resolved_plugins)}): {resolved_plugins}")
        except ConfigurationError as e:
            print(f"  ❌ Plugin resolution error: {e}")
        
        print(f"\nBuild Configuration:")
        print(f"  Build type: {self.build_config.build_type}")
        print(f"  Parallel jobs: {self.build_config.parallel_jobs or 'Auto'}")
        print(f"  Verbose: {self.build_config.verbose}")
        
        if self.build_config.cmake_args:
            print(f"  CMake args: {self.build_config.cmake_args}")
        
        print(f"\nSystem Configuration:")
        print(f"  Mock mode: {self.system_config.force_mock_mode}")
        if self.system_config.environment:
            print(f"  Environment variables: {list(self.system_config.environment.keys())}")
        
        print(f"\nLogging Configuration:")
        print(f"  Level: {self.logging_config.level}")
        print(f"  Plugin detection: {self.logging_config.plugin_detection}")
        print(f"  Build logging: {self.logging_config.build_logging}")


def load_config(config_file: Optional[str] = None) -> ConfigManager:
    """
    Load PyHelios configuration.
    
    Args:
        config_file: Optional path to configuration file
        
    Returns:
        ConfigManager instance with loaded configuration
    """
    return ConfigManager(config_file)