"""
Cross-platform library loader for PyHelios.

This module provides dynamic loading of Helios native libraries across
Windows, macOS, and Linux platforms with graceful fallback mechanisms.
"""

import os
import platform
import ctypes
from typing import Optional, Dict, Any, Callable, List
import logging

# Configure logging
logger = logging.getLogger(__name__)


class LibraryLoadError(Exception):
    """Raised when native library cannot be loaded."""
    pass


class MockLibrary:
    """Mock library that provides no-op implementations of all functions."""
    
    def __init__(self):
        self._functions = {}
        logger.info("Using mock library mode - no native Helios functionality available")
    
    def __getattr__(self, name: str) -> Callable:
        """Return a mock function for any requested function."""
        if name not in self._functions:
            def mock_function(*args, **kwargs):
                raise RuntimeError(
                    f"Cannot call '{name}' - PyHelios is running in mock mode. "
                    f"Native Helios library not available on this platform. "
                    f"Install platform-appropriate Helios binaries to enable full functionality."
                )
            
            mock_function.__name__ = f"mock_{name}"
            self._functions[name] = mock_function
        
        return self._functions[name]


class CrossPlatformLibraryLoader:
    """Cross-platform loader for Helios native libraries."""
    
    def __init__(self, plugin_dir: str):
        """
        Initialize the library loader.
        
        Args:
            plugin_dir: Directory containing native library files
        """
        self.plugin_dir = plugin_dir
        self.platform_name = platform.system()
        self.library = None
        self.is_mock = False
        
        # Platform-specific library configurations
        # Define these at runtime to avoid importing platform-specific modules
        self._library_config = self._get_library_config()
        
        logger.info(f"Initializing PyHelios library loader for platform: {self.platform_name}")
    
    def _get_library_config(self) -> Dict[str, Any]:
        """Get platform-specific library configuration."""
        config = {}
        
        if self.platform_name == 'Windows':
            # Only try to use WinDLL if we're actually on Windows
            try:
                config['Windows'] = {
                    'primary': 'CHelios.dll',
                    'loader': ctypes.WinDLL,
                    'alternatives': ['libhelios.dll', 'helios.dll'],
                    'dependencies': ['optix.6.5.0.dll']  # Optional GPU dependency
                }
            except AttributeError:
                # Fallback if WinDLL not available (shouldn't happen on Windows)
                config['Windows'] = {
                    'primary': 'CHelios.dll', 
                    'loader': ctypes.CDLL,
                    'alternatives': ['libhelios.dll', 'helios.dll'],
                    'dependencies': ['optix.6.5.0.dll']
                }
        
        config['Darwin'] = {  # macOS
            'primary': 'libCHelios.dylib',
            'loader': ctypes.CDLL,
            'alternatives': ['libhelios.dylib', 'CHelios.dylib'],
            'dependencies': []
        }
        
        config['Linux'] = {
            'primary': 'libCHelios.so',
            'loader': ctypes.CDLL,
            'alternatives': ['libhelios.so', 'CHelios.so'],
            'dependencies': []
        }
        
        return config
    
    @property
    def LIBRARY_CONFIG(self):
        """Access library configuration (for backward compatibility)."""
        return self._library_config
    
    def get_library_paths(self) -> Dict[str, str]:
        """Get all possible library paths for current platform."""
        if self.platform_name not in self.LIBRARY_CONFIG:
            return {}
        
        config = self.LIBRARY_CONFIG[self.platform_name]
        paths = {}
        
        # Primary library path
        paths['primary'] = os.path.join(self.plugin_dir, config['primary'])
        
        # Alternative library paths
        for i, alt in enumerate(config['alternatives']):
            paths[f'alt_{i}'] = os.path.join(self.plugin_dir, alt)
        
        # Dependency paths
        for i, dep in enumerate(config['dependencies']):
            paths[f'dep_{i}'] = os.path.join(self.plugin_dir, dep)
        
        return paths
    
    def check_dependencies(self) -> bool:
        """Check if optional dependencies are available."""
        if self.platform_name not in self.LIBRARY_CONFIG:
            return True
        
        config = self.LIBRARY_CONFIG[self.platform_name]
        missing_deps = []
        
        for dep in config['dependencies']:
            dep_path = os.path.join(self.plugin_dir, dep)
            if not os.path.exists(dep_path):
                missing_deps.append(dep)
        
        if missing_deps:
            logger.warning(f"Optional dependencies not found: {missing_deps}")
            logger.warning("Some features (e.g., GPU ray tracing) may not be available")
        
        return True  # Dependencies are optional for core functionality
    
    def _setup_library_path(self) -> None:
        """Automatically configure LD_LIBRARY_PATH for Linux/macOS to include plugin directory."""
        env_var = 'LD_LIBRARY_PATH' if self.platform_name == 'Linux' else 'DYLD_LIBRARY_PATH'
        current_path = os.environ.get(env_var, '')
        
        # Check if plugin directory is already in the path
        if self.plugin_dir not in current_path:
            if current_path:
                new_path = f"{self.plugin_dir}:{current_path}"
            else:
                new_path = self.plugin_dir
            
            os.environ[env_var] = new_path
            logger.debug(f"Automatically configured {env_var} to include: {self.plugin_dir}")
    
    def load_library(self, force_mock: bool = False) -> ctypes.CDLL:
        """
        Load the appropriate native library for the current platform.
        
        Args:
            force_mock: If True, use mock library regardless of availability
            
        Returns:
            Loaded library or mock library
            
        Raises:
            LibraryLoadError: If library loading fails and mock mode is disabled
        """
        # Check for explicit mock mode enabling
        mock_mode_enabled = (
            force_mock or 
            os.getenv('PYHELIOS_MOCK_MODE', '').lower() in ('1', 'true', 'yes', 'on') or
            os.getenv('PYHELIOS_DEV_MODE', '').lower() in ('1', 'true', 'yes', 'on')
        )
        
        if mock_mode_enabled:
            logger.info("Mock mode explicitly enabled")
            self.library = MockLibrary()
            self.is_mock = True
            return self.library
        
        # Check if platform is supported
        if self.platform_name not in self.LIBRARY_CONFIG:
            raise LibraryLoadError(
                f"Platform '{self.platform_name}' is not officially supported by PyHelios. "
                f"Supported platforms: {list(self.LIBRARY_CONFIG.keys())}. "
                f"To enable development mode without native libraries, set PYHELIOS_DEV_MODE=1"
            )
        
        config = self.LIBRARY_CONFIG[self.platform_name]
        paths = self.get_library_paths()
        
        # Automatically configure library path for Linux/macOS
        if self.platform_name in ['Linux', 'Darwin']:
            self._setup_library_path()
        
        # Check dependencies
        self.check_dependencies()
        
        # Try to load primary library
        primary_path = paths.get('primary')
        if primary_path and os.path.exists(primary_path):
            try:
                self.library = config['loader'](primary_path)
                logger.info(f"Successfully loaded primary library: {primary_path}")
                return self.library
            except Exception as e:
                logger.warning(f"Failed to load primary library {primary_path}: {e}")
        
        # Try alternative libraries
        for key, alt_path in paths.items():
            if key.startswith('alt_') and os.path.exists(alt_path):
                try:
                    self.library = config['loader'](alt_path)
                    logger.info(f"Successfully loaded alternative library: {alt_path}")
                    return self.library
                except Exception as e:
                    logger.warning(f"Failed to load alternative library {alt_path}: {e}")
        
        # No library could be loaded - raise error
        available_files = [f for f in os.listdir(self.plugin_dir) if f.endswith(('.dll', '.dylib', '.so'))] if os.path.exists(self.plugin_dir) else []
        
        error_msg = (
            f"Failed to load native Helios library for platform '{self.platform_name}'. "
            f"Expected files: {config['primary']} or {config['alternatives']}. "
        )
        
        if available_files:
            error_msg += f"Available library files: {available_files}. "
        else:
            error_msg += "No library files found in plugin directory. "
        
        error_msg += (
            f"To fix this issue:\n"
            f"1. Build native libraries: python build_scripts/build_helios.py\n"
            f"2. Or enable development mode: set PYHELIOS_DEV_MODE=1\n"
            f"Plugin directory: {self.plugin_dir}"
        )
        
        raise LibraryLoadError(error_msg)
    
    def get_library_info(self) -> Dict[str, Any]:
        """Get information about the loaded library."""
        info = {
            'platform': self.platform_name,
            'is_mock': self.is_mock,
            'plugin_dir': self.plugin_dir,
            'library_type': type(self.library).__name__ if self.library else None,
        }
        
        if not self.is_mock and self.library:
            # Try to get library path (if available)
            try:
                if hasattr(self.library, '_name'):
                    info['library_path'] = self.library._name
            except:
                pass
        
        # Check available library files
        info['available_files'] = []
        if os.path.exists(self.plugin_dir):
            for file in os.listdir(self.plugin_dir):
                if file.endswith(('.dll', '.dylib', '.so')):
                    info['available_files'].append(file)
        
        return info
    
    def validate_library(self) -> bool:
        """
        Validate that the loaded library has expected functions.
        
        Returns:
            True if library appears to be valid, False otherwise
        """
        if self.is_mock:
            return True  # Mock library is always "valid"
        
        if not self.library:
            return False
        
        # List of core functions that should be available
        core_functions = [
            'createContext',
            'destroyContext',
            'addPatchWithCenterAndSize',
            'getPrimitiveCount',
            'getPrimitiveType',
            'markGeometryClean',
            'markGeometryDirty',
            'isGeometryDirty'
        ]
        
        missing_functions = []
        for func_name in core_functions:
            try:
                func = getattr(self.library, func_name)
                if not callable(func):
                    missing_functions.append(func_name)
            except AttributeError:
                missing_functions.append(func_name)
        
        if missing_functions:
            logger.error(f"Library validation failed - missing functions: {missing_functions}")
            return False
        
        logger.info("Library validation passed - all core functions available")
        return True


# Global loader instance
_loader_instance: Optional[CrossPlatformLibraryLoader] = None


def get_loader(plugin_dir: str = None) -> CrossPlatformLibraryLoader:
    """Get the global library loader instance."""
    global _loader_instance
    
    if _loader_instance is None:
        if plugin_dir is None:
            # Find the correct library directory or fail explicitly
            plugin_dir = _find_library_directory()
        
        _loader_instance = CrossPlatformLibraryLoader(plugin_dir)
    
    return _loader_instance


def _find_library_directory() -> str:
    """
    Find the directory containing the built Helios library.
    
    Returns:
        Path to directory containing library files
        
    Raises:
        LibraryLoadError: If no library directory can be found
    """
    # Start from the current file location
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pyhelios_root = os.path.dirname(os.path.dirname(current_dir))  # Go up to PyHelios root
    
    platform_name = platform.system()
    if platform_name == 'Darwin':  # macOS
        library_names = ['libhelios.dylib', 'libCHelios.dylib', 'CHelios.dylib']
    elif platform_name == 'Windows':
        library_names = ['libhelios.dll', 'CHelios.dll', 'helios.dll']
    elif platform_name == 'Linux':
        library_names = ['libhelios.so', 'libCHelios.so', 'CHelios.so']
    else:
        raise LibraryLoadError(
            f"Platform '{platform_name}' is not supported by PyHelios. "
            f"Supported platforms: Windows, macOS, Linux"
        )
    
    # Try multiple locations in order of priority
    search_locations = [
        # 1. Packaged wheel location (for pip-installed PyHelios)
        current_dir,  # This is pyhelios/plugins/ when installed as wheel
        # 2. Development location (for local development)
        os.path.join(pyhelios_root, 'pyhelios_build', 'build', 'lib')
    ]
    
    for location in search_locations:
        if os.path.exists(location):
            for lib_name in library_names:
                lib_path = os.path.join(location, lib_name)
                if os.path.exists(lib_path):
                    logger.debug(f"Found library at: {lib_path}")
                    return location
    
    # Library not found in any location - provide clear error with actionable solution
    raise LibraryLoadError(
        f"Native Helios library not found in any expected location.\n"
        f"Searched locations: {search_locations}\n"
        f"Expected library files: {', '.join(library_names)}\n\n"
        f"To fix this issue:\n"
        f"1. Build native libraries: ./build_scripts/build_helios --plugins visualizer\n"
        f"2. Or enable development mode: set PYHELIOS_DEV_MODE=1\n\n"
        f"PyHelios follows a fail-fast philosophy - if you expected a native library "
        f"to be available but it's not, something is wrong and needs to be fixed."
    )


def load_helios_library(force_mock: bool = False) -> ctypes.CDLL:
    """
    Load the Helios native library for the current platform.
    
    Args:
        force_mock: Force mock mode even if native library is available
        
    Returns:
        Loaded library or mock library
    """
    # Check if dev mode is explicitly enabled via environment variable
    # If so, force mock mode regardless of force_mock parameter
    dev_mode_enabled = os.getenv('PYHELIOS_DEV_MODE', '').lower() in ('1', 'true', 'yes', 'on')
    if dev_mode_enabled:
        force_mock = True
    
    loader = get_loader()
    return loader.load_library(force_mock=force_mock)


def get_library_info() -> Dict[str, Any]:
    """Get information about the currently loaded library."""
    loader = get_loader()
    return loader.get_library_info()


def is_native_library_available() -> bool:
    """Check if a native library is available (not in mock mode)."""
    loader = get_loader()
    if loader.library is None:
        # Try to load library to check availability
        loader.load_library()
    return not loader.is_mock


def validate_library() -> bool:
    """Validate the currently loaded library."""
    loader = get_loader()
    if loader.library is None:
        loader.load_library()
    return loader.validate_library()


def detect_available_plugins() -> List[str]:
    """
    Detect which plugins are available in the currently loaded library.
    
    Returns:
        List of available plugin names
    """
    available_plugins = []
    
    # Basic plugins that should always be available if native library is loaded
    if is_native_library_available():
        # Check for basic plugins by trying to access their functions
        loader = get_loader()
        library = loader.library
        
        # Check for all plugins using the actual function names from wrappers
        plugin_checks = {
            'weberpenntree': ['createWeberPennTree', 'buildTree'],
            'canopygenerator': ['buildCanopy', 'generateCanopy'],
            'visualizer': ['createVisualizer', 'createVisualizerWithAntialiasing'],
            'radiation': ['createRadiationModel'],
            'energybalance': ['createEnergyBalanceModel'],
            'photosynthesis': ['createPhotosynthesisModel'],
            'leafoptics': ['createLeafOptics', 'destroyLeafOptics'],
            'stomatalconductance': ['createStomatalConductanceModel'],
            'boundarylayerconductance': ['createBoundaryLayerConductanceModel'],
            'planthydraulics': ['createPlantHydraulicsModel'],
            'lidar': ['createLiDARmodel', 'addLiDARSource'],
            'aeriallidar': ['createAerialLiDARmodel'],
            'plantarchitecture': ['createPlantArchitecture'],
            'voxelintersection': ['voxelIntersection'],
            'syntheticannotation': ['createSyntheticAnnotation'],
            'parameteroptimization': ['createParameterOptimization'],
            'projectbuilder': ['createProjectBuilder'],
            'collisiondetection': ['createCollisionDetection'],
            'solarposition': ['createSolarPosition', 'getSunElevation']
        }
        
        for plugin_name, function_names in plugin_checks.items():
            if any(hasattr(library, func_name) for func_name in function_names):
                available_plugins.append(plugin_name)
    
    return available_plugins


def is_plugin_available(plugin_name: str) -> bool:
    """
    Check if a specific plugin is available.
    
    Args:
        plugin_name: Name of the plugin to check
        
    Returns:
        True if plugin is available, False otherwise
    """
    available_plugins = detect_available_plugins()
    return plugin_name in available_plugins


def get_plugin_capabilities() -> Dict[str, Dict[str, Any]]:
    """
    Get capabilities information for all available plugins.
    
    Returns:
        Dictionary mapping plugin names to their capabilities
    """
    capabilities = {}
    available_plugins = detect_available_plugins()
    
    for plugin in available_plugins:
        capabilities[plugin] = {
            'name': plugin,
            'available': True,
            'description': f'{plugin.title()} plugin',
            'gpu_required': plugin in ['radiation'],  # Only radiation requires GPU
            'dependencies': []
        }
    
    return capabilities


