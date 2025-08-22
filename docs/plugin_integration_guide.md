# PyHelios Plugin Integration Guide

This comprehensive guide provides step-by-step instructions for integrating new Helios C++ plugins into PyHelios. It covers everything from plugin registration through testing and documentation, based on lessons learned from successfully integrating the radiation, visualizer, and WeberPennTree plugins.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Phase 1: Plugin Metadata Registration](#phase-1-plugin-metadata-registration)
4. [Phase 2: Build System Integration](#phase-2-build-system-integration)
5. [Phase 3: C++ Interface Implementation](#phase-3-c-interface-implementation)
6. [Phase 4: ctypes Wrapper Creation](#phase-4-ctypes-wrapper-creation)
7. [Phase 5: High-Level Python API](#phase-5-high-level-python-api)
8. [Phase 6: Asset Management](#phase-6-asset-management)
9. [Phase 7: Testing Integration](#phase-7-testing-integration)
10. [Phase 8: Documentation](#phase-8-documentation)
11. [Critical Requirements](#critical-requirements)
12. [Troubleshooting](#troubleshooting)
13. [Examples from Existing Plugins](#examples-from-existing-plugins)

## Overview

PyHelios uses a sophisticated plugin architecture that enables seamless integration of Helios C++ plugins through Python bindings. The integration process involves **8 distinct phases**, each with specific requirements and best practices.

### Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                    PyHelios Plugin Architecture             │
├─────────────────────────────────────────────────────────────┤
│  Python High-Level API (YourPlugin.py)                     │
│  ├── Context managers and error handling                   │
│  └── User-friendly methods with type hints                 │
├─────────────────────────────────────────────────────────────┤
│  ctypes Wrappers (UYourPluginWrapper.py)                   │
│  ├── Function prototypes and availability detection        │
│  └── Python-to-C type conversion                           │
├─────────────────────────────────────────────────────────────┤
│  C++ Interface (pyhelios_interface.cpp)                    │
│  ├── C-compatible wrapper functions                        │
│  └── Exception handling and parameter validation           │
├─────────────────────────────────────────────────────────────┤
│  Native Plugin (helios-core/plugins/yourplugin/)          │
│  ├── C++ plugin implementation                             │
│  └── Runtime assets (shaders, textures, configs)          │
└─────────────────────────────────────────────────────────────┘
```

### Integration Complexity

Plugin integration complexity varies by type:

- **Simple plugins** (data processing): ~4-6 hours
- **Moderate plugins** (physics modeling): ~1-2 days  
- **Complex plugins** (GPU-accelerated, visualization): ~3-5 days

## Prerequisites

Before starting plugin integration, ensure you have:

1. **Helios C++ plugin** working in helios-core
2. **Development environment** with CMake, appropriate compiler
3. **Plugin documentation** from helios-core
4. **Understanding of plugin dependencies** (CUDA, OpenGL, etc.)
5. **Test data** or examples for validation

### Required Tools

```bash
# Development dependencies
pip install -e .[dev]

# Build tools
cmake --version  # 3.18+
# Platform-specific compiler (MSVC, clang, gcc)

# Optional: GPU dependencies
nvidia-smi  # For CUDA plugins
```

## Phase 1: Plugin Metadata Registration

### 1.1 Define Plugin Metadata

Add your plugin to the metadata registry:

**File**: `pyhelios/config/plugin_metadata.py`

```python
PLUGIN_METADATA = {
    # ... existing plugins ...
    
    "yourplugin": PluginMetadata(
        name="yourplugin",
        description="Brief description of plugin functionality",
        system_dependencies=["required_system_libs"],  # e.g., ["cuda", "opengl"]
        plugin_dependencies=["other_helios_plugins"],  # e.g., ["weberpenntree"]
        platforms=["windows", "linux", "macos"],       # Supported platforms
        gpu_required=False,                            # True if requires GPU
        optional=True,                                 # False for core plugins
        profile_tags=["category", "subcategory"],      # e.g., ["physics", "modeling"]
        test_symbols=["function1", "function2"]        # Functions to test availability
    ),
}
```

### 1.2 Add to Plugin Profiles

**File**: `pyhelios/config/plugin_profiles.py`

Add your plugin to relevant profiles:

```python
PLUGIN_PROFILES = {
    # ... existing profiles ...
    
    "your_category": PluginProfile(
        name="your_category",
        description="Profile description",
        plugins=["yourplugin", "related_plugin"],
        platforms=["windows", "linux", "macos"]
    ),
    
    # Add to existing profiles where appropriate
    "research": PluginProfile(
        plugins=[
            # ... existing plugins ...
            "yourplugin"  # Add to research profile
        ]
    )
}
```

### 1.3 Validation

Test metadata registration:

```bash
# Check plugin discovery
python -m pyhelios.plugins discover

# Validate plugin metadata
python -c "
from pyhelios.config.plugin_metadata import get_plugin_metadata
metadata = get_plugin_metadata('yourplugin')
print(f'Plugin: {metadata.name}')
print(f'Dependencies: {metadata.system_dependencies}')
"
```

## Phase 2: Build System Integration

### 2.1 CMake Integration

The PyHelios build system automatically handles plugin integration through the flexible plugin selection system. No manual CMake modifications are typically required.

**Automatic Integration**: Your plugin will be built when:
- User explicitly selects it: `--plugins yourplugin`
- Included in a profile that contains it
- Required as a dependency by another plugin

### 2.2 Special Build Requirements

For plugins with special dependencies, add CMake configuration:

**File**: `pyhelios_build/cmake/PluginSelection.cmake`

```cmake
# Special handling for complex plugins
if("yourplugin" IN_LIST PLUGINS)
    # Find required dependencies
    find_package(YourDependency REQUIRED)
    
    # Add compile definitions
    target_compile_definitions(pyhelios_interface PUBLIC YOURPLUGIN_AVAILABLE)
    
    # Link dependencies
    target_link_libraries(pyhelios_interface YourDependency::YourDependency)
    
    # Handle assets
    file(COPY "${HELIOS_CORE_DIR}/plugins/yourplugin/assets"
         DESTINATION "${CMAKE_BINARY_DIR}/plugins/yourplugin/")
endif()
```

### 2.3 Test Build Integration

Test that your plugin builds correctly:

```bash
# Clean build with your plugin
build_scripts/build_helios --clean --plugins yourplugin

# Test with profile
build_scripts/build_helios --profile research

# Interactive selection (verify plugin appears)
build_scripts/build_helios --interactive
```

## Phase 3: C++ Interface Implementation

### 3.1 Add Interface Functions

**CRITICAL**: Before implementing Python wrappers, add C-compatible functions to the PyHelios interface.

**File**: `pyhelios_build/pyhelios_interface.cpp`

Add functions after existing implementations:

```cpp
#ifdef YOURPLUGIN_AVAILABLE
#include "YourPlugin.h"  // Include plugin header

// Plugin creation/destruction
EXPORT void* createYourPlugin(helios::Context* context) {
    try {
        clearError();
        if (!context) {
            setError(1, "Context pointer is null");
            return nullptr;
        }
        
        // Create plugin instance - adjust based on plugin constructor
        return new YourPluginClass(context);
        
    } catch (const std::runtime_error& e) {
        setError(7, e.what());
        return nullptr;
    } catch (const std::exception& e) {
        setError(7, std::string("ERROR (createYourPlugin): ") + e.what());
        return nullptr;
    } catch (...) {
        setError(99, "ERROR (createYourPlugin): Unknown error");
        return nullptr;
    }
}

EXPORT void destroyYourPlugin(void* plugin_ptr) {
    if (plugin_ptr) {
        delete static_cast<YourPluginClass*>(plugin_ptr);
    }
}

// Plugin methods - follow this pattern for each method
EXPORT int yourPluginMethod(void* plugin_ptr, float* params, uint32_t param_count) {
    try {
        clearError();
        
        // Validate parameters
        if (!plugin_ptr) {
            setError(1, "Plugin pointer is null");
            return -1;
        }
        if (!params) {
            setError(1, "Parameters array is null");
            return -1;
        }
        
        // Cast plugin pointer
        YourPluginClass* plugin = static_cast<YourPluginClass*>(plugin_ptr);
        
        // Convert parameters - adjust based on C++ API
        std::vector<float> cpp_params(params, params + param_count);
        
        // Call C++ method
        int result = plugin->yourMethod(cpp_params);
        
        return result;
        
    } catch (const std::runtime_error& e) {
        setError(7, e.what());
        return -1;
    } catch (const std::exception& e) {
        setError(7, std::string("ERROR (yourPluginMethod): ") + e.what());
        return -1;
    } catch (...) {
        setError(99, "ERROR (yourPluginMethod): Unknown error");
        return -1;
    }
}

// For methods returning arrays
EXPORT float* yourPluginGetArray(void* plugin_ptr, uint32_t uuid, uint32_t* size) {
    try {
        clearError();
        
        if (!plugin_ptr || !size) {
            setError(1, "Invalid parameters");
            if (size) *size = 0;
            return nullptr;
        }
        
        YourPluginClass* plugin = static_cast<YourPluginClass*>(plugin_ptr);
        
        // Get data from plugin
        std::vector<float> result = plugin->getArrayData(uuid);
        
        // Convert to static array for return
        static std::vector<float> static_result;
        static_result = result;
        *size = static_result.size();
        return static_result.data();
        
    } catch (const std::runtime_error& e) {
        setError(2, e.what());  // UUID_NOT_FOUND for typical cases
        if (size) *size = 0;
        return nullptr;
    } catch (const std::exception& e) {
        setError(7, e.what());
        if (size) *size = 0;
        return nullptr;
    } catch (...) {
        setError(99, "ERROR (yourPluginGetArray): Unknown error");
        if (size) *size = 0;
        return nullptr;
    }
}

#endif // YOURPLUGIN_AVAILABLE
```

### 3.2 Parameter Conversion Patterns

**Common Parameter Conversions**:

```cpp
// Vec3 from float array
helios::vec3 position(float_array[0], float_array[1], float_array[2]);

// Vec2 from float array  
helios::vec2 size(float_array[0], float_array[1]);

// SphericalCoord from float array
helios::SphericalCoord rotation = helios::make_SphericalCoord(float_array[0], float_array[1]);

// Color from float array
helios::RGBcolor color(float_array[0], float_array[1], float_array[2]);
helios::RGBAcolor color_rgba(float_array[0], float_array[1], float_array[2], float_array[3]);

// String handling (always validate)
if (c_string) {
    std::string cpp_string(c_string);
    plugin->methodWithString(cpp_string);
}

// UUID arrays
std::vector<uint32_t> uuids(uuid_array, uuid_array + count);
```

### 3.3 Rebuild Requirement

**CRITICAL**: After adding interface functions, rebuild PyHelios:

```bash
build_scripts/build_helios --clean --plugins yourplugin --verbose
```

This enables:
- New functions available to ctypes
- Exception handling infrastructure
- Plugin availability detection

## Phase 4: ctypes Wrapper Creation

### 4.1 Create Wrapper File

**File**: `pyhelios/wrappers/UYourPluginWrapper.py`

```python
import ctypes
from typing import List, Optional, Union
from ..plugins import helios_lib
from ..exceptions import check_helios_error

# Define plugin structure
class UYourPlugin(ctypes.Structure):
    """Opaque structure for YourPlugin C++ class"""
    pass

# Function prototypes with availability detection
try:
    # Plugin creation/destruction
    helios_lib.createYourPlugin.argtypes = [ctypes.POINTER(UContext)]
    helios_lib.createYourPlugin.restype = ctypes.POINTER(UYourPlugin)
    
    helios_lib.destroyYourPlugin.argtypes = [ctypes.POINTER(UYourPlugin)]
    helios_lib.destroyYourPlugin.restype = None
    
    # Plugin methods
    helios_lib.yourPluginMethod.argtypes = [
        ctypes.POINTER(UYourPlugin), 
        ctypes.POINTER(ctypes.c_float), 
        ctypes.c_uint32
    ]
    helios_lib.yourPluginMethod.restype = ctypes.c_int
    
    helios_lib.yourPluginGetArray.argtypes = [
        ctypes.POINTER(UYourPlugin),
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_uint32)
    ]
    helios_lib.yourPluginGetArray.restype = ctypes.POINTER(ctypes.c_float)
    
    _YOURPLUGIN_FUNCTIONS_AVAILABLE = True
    
except AttributeError:
    _YOURPLUGIN_FUNCTIONS_AVAILABLE = False

# Error checking callback
def _check_error(result, func, args):
    """Automatic error checking for all plugin functions"""
    check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage)
    return result

# Set up automatic error checking
if _YOURPLUGIN_FUNCTIONS_AVAILABLE:
    helios_lib.createYourPlugin.errcheck = _check_error
    helios_lib.yourPluginMethod.errcheck = _check_error
    helios_lib.yourPluginGetArray.errcheck = _check_error

# Wrapper functions
def createYourPlugin(context) -> ctypes.POINTER(UYourPlugin):
    """Create YourPlugin instance"""
    if not _YOURPLUGIN_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "YourPlugin functions not available in current Helios library. "
            "Rebuild PyHelios with 'yourplugin' enabled:\n"
            "  build_scripts/build_helios --plugins yourplugin"
        )
    
    return helios_lib.createYourPlugin(context)

def destroyYourPlugin(plugin_ptr: ctypes.POINTER(UYourPlugin)) -> None:
    """Destroy YourPlugin instance"""
    if plugin_ptr and _YOURPLUGIN_FUNCTIONS_AVAILABLE:
        helios_lib.destroyYourPlugin(plugin_ptr)

def yourPluginMethod(plugin_ptr: ctypes.POINTER(UYourPlugin), 
                    params: List[float]) -> int:
    """Execute plugin method with parameters"""
    if not _YOURPLUGIN_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "YourPlugin methods not available. Rebuild with yourplugin enabled."
        )
    
    # Validate inputs
    if not params:
        raise ValueError("Parameters list cannot be empty")
    
    # Convert to ctypes array
    param_array = (ctypes.c_float * len(params))(*params)
    
    # Call function - errcheck handles error checking automatically
    result = helios_lib.yourPluginMethod(plugin_ptr, param_array, len(params))
    
    return result

def yourPluginGetArray(plugin_ptr: ctypes.POINTER(UYourPlugin), 
                      uuid: int) -> List[float]:
    """Get array data from plugin"""
    if not _YOURPLUGIN_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "YourPlugin methods not available. Rebuild with yourplugin enabled."
        )
    
    # Validate inputs
    if uuid < 0:
        raise ValueError("UUID must be non-negative")
    
    # Get array from C++
    size = ctypes.c_uint32()
    ptr = helios_lib.yourPluginGetArray(plugin_ptr, uuid, ctypes.byref(size))
    
    # Convert to Python list
    if ptr and size.value > 0:
        return list(ptr[:size.value])
    else:
        return []

# Mock mode functions
if not _YOURPLUGIN_FUNCTIONS_AVAILABLE:
    def mock_createYourPlugin(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: YourPlugin not available. "
            "This would create a plugin instance with native library."
        )
    
    def mock_yourPluginMethod(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: YourPlugin method not available. "
            "This would execute plugin computation with native library."
        )
    
    # Replace functions with mocks for development
    createYourPlugin = mock_createYourPlugin
    yourPluginMethod = mock_yourPluginMethod
```

### 4.2 Import in Wrappers Module

**File**: `pyhelios/wrappers/__init__.py`

Add import for your wrapper:

```python
# Existing imports...
from . import UYourPluginWrapper
```

## Phase 5: High-Level Python API

### 5.1 Create High-Level Class

**File**: `pyhelios/YourPlugin.py`

```python
"""
YourPlugin - High-level interface for YourPlugin functionality

This module provides a Python interface to the YourPlugin Helios plugin,
offering [description of plugin capabilities].
"""

from typing import List, Optional, Union, Any
from . import wrappers.UYourPluginWrapper as plugin_wrapper
from .Context import Context
from .plugins.registry import get_plugin_registry
from .exceptions import HeliosError

class YourPluginError(HeliosError):
    """Exception raised for YourPlugin-specific errors"""
    pass

class YourPlugin:
    """
    High-level interface for YourPlugin functionality.
    
    YourPlugin provides [detailed description of capabilities].
    
    This class requires the native Helios library built with YourPlugin support.
    Use context managers for proper resource cleanup.
    
    Example:
        >>> with Context() as context:
        ...     with YourPlugin(context) as plugin:
        ...         result = plugin.compute_something([1.0, 2.0, 3.0])
        ...         print(f"Result: {result}")
    """
    
    def __init__(self, context: Context):
        """
        Initialize YourPlugin with a Helios context.
        
        Args:
            context: Active Helios Context instance
            
        Raises:
            YourPluginError: If plugin not available in current build
            RuntimeError: If plugin initialization fails
        """
        # Check plugin availability
        registry = get_plugin_registry()
        if not registry.is_plugin_available('yourplugin'):
            raise YourPluginError(
                "YourPlugin not available in current Helios library. "
                "Rebuild PyHelios with YourPlugin support:\n"
                "  build_scripts/build_helios --plugins yourplugin\n"
                "\n"
                "System requirements:\n"
                f"  - Platforms: {', '.join(['Windows', 'Linux', 'macOS'])}\n"
                "  - Dependencies: [list any special requirements]\n"
                "  - GPU: [Required/Not required]"
            )
        
        self.context = context
        self._plugin_ptr = plugin_wrapper.createYourPlugin(context.getNativePtr())
        
        if not self._plugin_ptr:
            raise YourPluginError("Failed to initialize YourPlugin")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources"""
        if hasattr(self, '_plugin_ptr') and self._plugin_ptr:
            plugin_wrapper.destroyYourPlugin(self._plugin_ptr)
            self._plugin_ptr = None
    
    def compute_something(self, parameters: List[float]) -> int:
        """
        Perform plugin computation with given parameters.
        
        Args:
            parameters: List of computation parameters
                       [describe what each parameter means, units, ranges]
            
        Returns:
            Computation result [describe return value]
            
        Raises:
            ValueError: If parameters are invalid
            YourPluginError: If computation fails
            
        Example:
            >>> plugin.compute_something([1.0, 2.0, 3.0])
            42
        """
        # Validate inputs
        if not parameters:
            raise ValueError("Parameters list cannot be empty")
        
        if len(parameters) < 3:
            raise ValueError("At least 3 parameters required")
        
        # Additional validation as needed
        for i, param in enumerate(parameters):
            if not isinstance(param, (int, float)):
                raise ValueError(f"Parameter {i} must be numeric")
        
        try:
            # Call wrapper function
            result = plugin_wrapper.yourPluginMethod(self._plugin_ptr, parameters)
            return result
            
        except Exception as e:
            raise YourPluginError(f"Plugin computation failed: {e}")
    
    def get_data_array(self, uuid: int) -> List[float]:
        """
        Get array data for specified primitive.
        
        Args:
            uuid: Primitive UUID
            
        Returns:
            Array of data values
            
        Raises:
            ValueError: If UUID is invalid
            YourPluginError: If data retrieval fails
        """
        if uuid < 0:
            raise ValueError("UUID must be non-negative")
        
        try:
            return plugin_wrapper.yourPluginGetArray(self._plugin_ptr, uuid)
        except Exception as e:
            raise YourPluginError(f"Failed to get array data: {e}")
    
    def is_available(self) -> bool:
        """
        Check if YourPlugin is available in current build.
        
        Returns:
            True if plugin is available, False otherwise
        """
        registry = get_plugin_registry()
        return registry.is_plugin_available('yourplugin')

# Convenience function
def create_your_plugin(context: Context) -> YourPlugin:
    """
    Create YourPlugin instance with context.
    
    Args:
        context: Helios Context
        
    Returns:
        YourPlugin instance
    """
    return YourPlugin(context)
```

### 5.2 Add to Main Module

**File**: `pyhelios/__init__.py`

Add your plugin to the main imports:

```python
# Existing imports...
from .YourPlugin import YourPlugin, YourPluginError

# Add to __all__
__all__ = [
    # ... existing exports ...
    'YourPlugin',
    'YourPluginError'
]
```

## Phase 6: Asset Management

### 6.1 Identify Runtime Assets

Many plugins require runtime assets that must be copied to specific locations:

**Common Asset Types**:
- **Shaders**: `.vert`, `.frag`, `.glsl` files
- **Textures**: `.png`, `.jpg`, `.tga` files  
- **Fonts**: `.ttf`, `.otf` files
- **Configuration**: `.xml`, `.json`, `.yaml` files
- **Data files**: `.csv`, `.dat`, model files

### 6.2 Asset Discovery

Check plugin source for asset requirements:

```bash
# Search for asset loading in plugin C++ code
cd helios-core/plugins/yourplugin
grep -r "load\|read\|open" src/
grep -r "\.png\|\.jpg\|\.xml\|\.glsl" src/
```

### 6.3 Implement Asset Copying

**File**: `build_scripts/build_helios.py`

Add asset copying method:

```python
def _copy_yourplugin_assets(self) -> None:
    """
    Copy YourPlugin runtime assets to expected locations.
    
    The C++ YourPlugin code expects assets at specific locations relative
    to the working directory. This method copies all required assets.
    """
    # Source and destination paths
    build_plugin_dir = self.build_dir / 'plugins' / 'yourplugin'
    target_base_dir = self.output_dir.parent / 'plugins' / 'yourplugin'
    
    if not build_plugin_dir.exists():
        print(f"ℹ️  YourPlugin assets directory not found: {build_plugin_dir}")
        return
    
    total_files_copied = 0
    
    # Copy shader files
    build_shader_dir = build_plugin_dir / 'shaders'
    if build_shader_dir.exists():
        target_shader_dir = target_base_dir / 'shaders'
        target_shader_dir.mkdir(parents=True, exist_ok=True)
        
        for shader_file in build_shader_dir.rglob('*'):
            if shader_file.is_file():
                rel_path = shader_file.relative_to(build_shader_dir)
                dest_file = target_shader_dir / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(shader_file, dest_file)
                total_files_copied += 1
                print(f"Copied shader: {rel_path}")
    
    # Copy configuration files
    build_config_dir = build_plugin_dir / 'config'
    if build_config_dir.exists():
        target_config_dir = target_base_dir / 'config'
        target_config_dir.mkdir(parents=True, exist_ok=True)
        
        for config_file in build_config_dir.rglob('*'):
            if config_file.is_file():
                rel_path = config_file.relative_to(build_config_dir)
                dest_file = target_config_dir / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(config_file, dest_file)
                total_files_copied += 1
                print(f"Copied config: {rel_path}")
    
    # Copy data files
    for data_pattern in ['*.xml', '*.json', '*.dat']:
        for data_file in build_plugin_dir.rglob(data_pattern):
            if data_file.is_file():
                rel_path = data_file.relative_to(build_plugin_dir)
                dest_file = target_base_dir / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(data_file, dest_file)
                total_files_copied += 1
                print(f"Copied data: {rel_path}")
    
    if total_files_copied > 0:
        print(f"📦 Successfully copied {total_files_copied} YourPlugin assets to {target_base_dir}")
```

### 6.4 Integrate Asset Copying

Add to the main copy method in `build_scripts/build_helios.py`:

```python
def copy_to_output(self, library_path: Path) -> None:
    # ... existing code ...
    
    # Copy plugin-specific assets
    if 'yourplugin' in self.plugins:
        self._copy_yourplugin_assets()
    
    # ... rest of method ...
```

## Phase 7: Testing Integration

### 7.1 Create Test File

**File**: `tests/test_yourplugin.py`

```python
"""
Tests for YourPlugin integration
"""

import pytest
from pyhelios import Context, YourPlugin, YourPluginError
from pyhelios.plugins.registry import get_plugin_registry
from pyhelios.exceptions import HeliosError

class TestYourPluginMetadata:
    """Test plugin metadata and registration"""
    
    @pytest.mark.cross_platform
    def test_plugin_metadata_exists(self):
        """Test that plugin metadata is correctly defined"""
        from pyhelios.config.plugin_metadata import get_plugin_metadata
        
        metadata = get_plugin_metadata('yourplugin')
        assert metadata is not None
        assert metadata.name == 'yourplugin'
        assert metadata.description
        assert metadata.test_symbols
        assert isinstance(metadata.platforms, list)
        assert len(metadata.platforms) > 0

    @pytest.mark.cross_platform
    def test_plugin_in_profiles(self):
        """Test that plugin appears in appropriate profiles"""
        from pyhelios.config.plugin_profiles import get_profile_plugins
        
        # Should be in research profile
        research_plugins = get_profile_plugins('research')
        assert 'yourplugin' in research_plugins

class TestYourPluginAvailability:
    """Test plugin availability detection"""
    
    @pytest.mark.cross_platform
    def test_plugin_registry_awareness(self):
        """Test that plugin registry knows about YourPlugin"""
        registry = get_plugin_registry()
        
        # Plugin should be known (even if not available)
        all_plugins = registry.get_all_plugins()
        assert 'yourplugin' in all_plugins
    
    @pytest.mark.cross_platform 
    def test_graceful_unavailable_handling(self):
        """Test graceful handling when plugin unavailable"""
        registry = get_plugin_registry()
        
        with Context() as context:
            if not registry.is_plugin_available('yourplugin'):
                # Should raise informative error
                with pytest.raises(YourPluginError) as exc_info:
                    YourPlugin(context)
                
                error_msg = str(exc_info.value).lower()
                # Error should mention rebuilding
                assert any(keyword in error_msg for keyword in 
                          ['rebuild', 'build', 'enable', 'compile'])

class TestYourPluginInterface:
    """Test plugin interface without requiring native library"""
    
    @pytest.mark.cross_platform
    def test_plugin_class_structure(self):
        """Test that plugin class has expected structure"""
        # Test class attributes and methods exist
        assert hasattr(YourPlugin, '__init__')
        assert hasattr(YourPlugin, '__enter__')
        assert hasattr(YourPlugin, '__exit__')
        assert hasattr(YourPlugin, 'compute_something')
        assert hasattr(YourPlugin, 'get_data_array')
        assert hasattr(YourPlugin, 'is_available')
    
    @pytest.mark.cross_platform
    def test_error_types_available(self):
        """Test that error types are properly defined"""
        assert issubclass(YourPluginError, HeliosError)

@pytest.mark.native_only
class TestYourPluginFunctionality:
    """Test actual plugin functionality with native library"""
    
    def test_plugin_creation(self):
        """Test plugin can be created and destroyed"""
        with Context() as context:
            with YourPlugin(context) as plugin:
                assert plugin is not None
                assert isinstance(plugin, YourPlugin)
    
    def test_basic_computation(self):
        """Test basic plugin computation"""
        with Context() as context:
            with YourPlugin(context) as plugin:
                # Test with valid parameters
                result = plugin.compute_something([1.0, 2.0, 3.0])
                assert isinstance(result, int)
                assert result >= 0  # Adjust based on expected output
    
    def test_parameter_validation(self):
        """Test parameter validation"""
        with Context() as context:
            with YourPlugin(context) as plugin:
                # Test empty parameters
                with pytest.raises(ValueError, match="cannot be empty"):
                    plugin.compute_something([])
                
                # Test invalid parameter count
                with pytest.raises(ValueError, match="at least"):
                    plugin.compute_something([1.0])
                
                # Test invalid parameter type (if applicable)
                with pytest.raises(ValueError, match="numeric"):
                    plugin.compute_something([1.0, "invalid", 3.0])
    
    def test_data_array_retrieval(self):
        """Test array data retrieval"""
        with Context() as context:
            # Create some geometry to test with
            patch_uuid = context.addPatch(center=[0, 0, 1], size=[1, 1])
            
            with YourPlugin(context) as plugin:
                # Test valid UUID
                data = plugin.get_data_array(patch_uuid)
                assert isinstance(data, list)
                # Adjust assertions based on expected data
                
                # Test invalid UUID
                with pytest.raises((ValueError, YourPluginError)):
                    plugin.get_data_array(-1)

@pytest.mark.native_only
class TestYourPluginIntegration:
    """Test plugin integration with other PyHelios components"""
    
    def test_context_integration(self):
        """Test plugin works with Context geometry"""
        with Context() as context:
            # Add some geometry
            patch_uuid = context.addPatch(center=[0, 0, 1], size=[1, 1])
            triangle_uuid = context.addTriangle([0, 0, 0], [1, 0, 0], [0, 1, 0])
            
            with YourPlugin(context) as plugin:
                # Test plugin can work with context geometry
                result = plugin.compute_something([1.0, 2.0, 3.0])
                assert result is not None
    
    def test_error_handling_integration(self):
        """Test that C++ exceptions become proper Python exceptions"""
        with Context() as context:
            with YourPlugin(context) as plugin:
                # Test operations that should cause specific errors
                # Adjust based on plugin behavior
                try:
                    plugin.get_data_array(99999)  # Non-existent UUID
                    assert False, "Should have raised an exception"
                except HeliosError as e:
                    # Verify error message is helpful
                    error_msg = str(e).lower()
                    assert any(keyword in error_msg for keyword in 
                              ['not found', 'invalid', 'uuid'])

@pytest.mark.slow
class TestYourPluginPerformance:
    """Performance tests for plugin operations"""
    
    @pytest.mark.native_only
    def test_computation_performance(self):
        """Test computation performance doesn't regress"""
        import time
        
        with Context() as context:
            with YourPlugin(context) as plugin:
                # Time computation
                start_time = time.time()
                result = plugin.compute_something([1.0, 2.0, 3.0])
                elapsed = time.time() - start_time
                
                # Adjust threshold based on expected performance
                assert elapsed < 1.0, f"Computation too slow: {elapsed:.3f}s"
                assert result is not None
```

### 7.2 Test Configuration

Add test markers to `pytest.ini` if needed:

```ini
# pytest.ini (if new markers needed)
markers =
    yourplugin: tests requiring YourPlugin
```

### 7.3 Run Tests

```bash
# Run all plugin tests
pytest tests/test_yourplugin.py -v

# Run only cross-platform tests
pytest tests/test_yourplugin.py -m cross_platform

# Run only native tests (if library available)
pytest tests/test_yourplugin.py -m native_only

# Run with coverage
pytest tests/test_yourplugin.py --cov=pyhelios.YourPlugin
```

## Phase 8: Documentation

### 8.1 API Documentation

**File**: `docs/plugin_yourplugin.md`

```markdown
# YourPlugin Documentation

## Overview

YourPlugin provides [detailed description of plugin capabilities and use cases].

## System Requirements

- **Platforms**: Windows, Linux, macOS
- **Dependencies**: [List any special requirements]
- **GPU**: [Required/Not required]
- **Memory**: [Any special memory requirements]

## Installation

YourPlugin is included in the following build profiles:
- `research`: Full research capabilities
- `your_category`: [Description of custom profile]

### Build with YourPlugin

```bash
# Using profile
build_scripts/build_helios --profile research

# Explicit selection
build_scripts/build_helios --plugins yourplugin

# Check if available
python -c "from pyhelios.plugins import print_plugin_status; print_plugin_status()"
```

## Quick Start

```python
from pyhelios import Context, YourPlugin

# Create context and plugin
with Context() as context:
    with YourPlugin(context) as plugin:
        # Perform computation
        result = plugin.compute_something([1.0, 2.0, 3.0])
        print(f"Result: {result}")
        
        # Get data arrays
        data = plugin.get_data_array(some_uuid)
        print(f"Data: {data}")
```

## API Reference

### YourPlugin Class

#### Constructor

```python
YourPlugin(context: Context)
```

Initialize YourPlugin with a Helios context.

**Parameters:**
- `context`: Active Helios Context instance

**Raises:**
- `YourPluginError`: If plugin not available
- `RuntimeError`: If initialization fails

#### Methods

##### compute_something

```python
compute_something(parameters: List[float]) -> int
```

Perform plugin computation with given parameters.

**Parameters:**
- `parameters`: List of computation parameters
  - `parameters[0]`: [Description, units, range]
  - `parameters[1]`: [Description, units, range]
  - `parameters[2]`: [Description, units, range]

**Returns:**
- `int`: Computation result [description]

**Raises:**
- `ValueError`: If parameters are invalid
- `YourPluginError`: If computation fails

**Example:**
```python
result = plugin.compute_something([1.0, 2.0, 3.0])
```

##### get_data_array

```python
get_data_array(uuid: int) -> List[float]
```

Get array data for specified primitive.

**Parameters:**
- `uuid`: Primitive UUID

**Returns:**
- `List[float]`: Array of data values

**Raises:**
- `ValueError`: If UUID is invalid
- `YourPluginError`: If data retrieval fails

## Examples

### Basic Usage

```python
from pyhelios import Context, YourPlugin

with Context() as context:
    # Add some geometry
    patch_uuid = context.addPatch(center=[0, 0, 1], size=[1, 1])
    
    with YourPlugin(context) as plugin:
        # Compute something
        result = plugin.compute_something([1.0, 2.0, 3.0])
        print(f"Computation result: {result}")
        
        # Get data for the patch
        data = plugin.get_data_array(patch_uuid)
        print(f"Patch data: {data}")
```

### Error Handling

```python
from pyhelios import Context, YourPlugin, YourPluginError

with Context() as context:
    try:
        with YourPlugin(context) as plugin:
            result = plugin.compute_something([1.0, 2.0, 3.0])
            
    except YourPluginError as e:
        print(f"Plugin error: {e}")
        # Error messages include rebuild instructions
        
    except ValueError as e:
        print(f"Parameter error: {e}")
```

### Integration with Other Plugins

```python
from pyhelios import Context, WeberPennTree, YourPlugin, WPTType

with Context() as context:
    # Generate tree geometry
    with WeberPennTree(context) as wpt:
        tree_id = wpt.build_tree(WPTType.LEMON)
    
    # Process with YourPlugin
    with YourPlugin(context) as plugin:
        # Get all patch UUIDs from tree
        patch_uuids = context.getAllUUIDs("patch")
        
        # Process each patch
        for uuid in patch_uuids:
            data = plugin.get_data_array(uuid)
            print(f"Patch {uuid}: {data}")
```

## Troubleshooting

### Plugin Not Available

If you see "YourPlugin not available" errors:

1. Check plugin status:
   ```bash
   python -c "from pyhelios.plugins import print_plugin_status; print_plugin_status()"
   ```

2. Rebuild with plugin:
   ```bash
   build_scripts/build_helios --clean --plugins yourplugin
   ```

3. Verify dependencies are installed

### Build Errors

Common build issues:

- **Missing dependencies**: Install required system libraries
- **Platform compatibility**: Check supported platforms
- **CMake errors**: Verify CMake version and configuration

### Runtime Errors

- **Parameter validation errors**: Check parameter types and ranges
- **UUID errors**: Verify UUIDs exist in context
- **Memory errors**: Use context managers for proper cleanup

## Performance Notes

- YourPlugin computations are [performance characteristics]
- For large datasets, consider [optimization strategies]
- Memory usage scales with [scaling factors]

## Limitations

- [List any known limitations]
- [Platform-specific issues]
- [Integration constraints]
```

### 8.2 Update Main Documentation

Add your plugin to the main documentation:

**File**: `docs/overview.md` (or similar)

Add section about your plugin in the appropriate category.

### 8.3 Generate Documentation

```bash
# Generate Doxygen documentation
cd docs
doxygen Doxyfile.python

# View generated documentation
open docs/generated/html/index.html
```

## Critical Requirements

### 8.1 Asset Management is Critical

**Lesson from Visualizer Integration**: Many plugins require runtime assets that must be copied to specific locations. The C++ code often expects assets at hardcoded relative paths.

**Requirements**:
- Identify all runtime assets in plugin source
- Implement asset copying in build system
- Test asset loading in different working directories
- Document asset requirements for users

### 8.2 Parameter Mapping Precision

**Lesson from Visualizer Integration**: C++ function signatures must be precisely mapped to Python parameters, especially constructor overloads.

**Requirements**:
- Check actual C++ constructor signatures
- Map parameters semantically, not just positionally  
- Test different parameter combinations
- Document parameter meanings and defaults

### 8.3 Cross-Platform Symbol Export

**Requirements**:
- Use `EXPORT` macro in C++ interface functions
- Test library loading on all target platforms
- Verify symbols are exported (use `nm`, `objdump`, or similar tools)
- Handle platform-specific linking differences

### 8.4 Exception Handling is Mandatory

**Requirements**:
- All C++ interface functions must use try/catch blocks
- Set appropriate error codes based on exception type
- Use errcheck callbacks for automatic error checking
- Never allow C++ exceptions to cross into Python

### 8.5 Plugin Availability Detection

**Requirements**:
- Check function availability using try/except around ctypes prototypes
- Provide actionable error messages when unavailable
- Implement mock mode for development
- Test unavailable plugin scenarios

### 8.6 Memory Management and Context Cleanup

**Lesson from Compound Geometry Integration**: Memory management issues can cause segmentation faults during context cleanup, especially when static vectors hold references to deleted memory.

**Critical Requirements**:
- **Context Destructor Safety**: Always set pointer to `None` after deletion to prevent double-deletion:
  ```python
  def __exit__(self, exc_type, exc_value, traceback):
      if self.context is not None:
          context_wrapper.destroyContext(self.context)
          self.context = None  # Prevent double deletion
  ```

- **Static Vector Thread Safety**: Use `thread_local` for static vectors in C++ to prevent race conditions:
  ```cpp
  // Convert vector to thread-local static array for return
  static thread_local std::vector<unsigned int> static_result;
  static_result = std::move(uuids);
  *count = static_result.size();
  return static_result.data();
  ```

- **Vector Pre-allocation**: Always pre-allocate vectors for efficiency:
  ```cpp
  // Pre-allocate nodes vector with known size
  std::vector<helios::vec3> nodes_vec;
  nodes_vec.reserve(node_count);
  for (unsigned int i = 0; i < node_count; i++) {
      nodes_vec.emplace_back(nodes[i*3], nodes[i*3+1], nodes[i*3+2]);
  }
  ```

### 8.7 Parameter Validation and Type Handling

**Lesson from Compound Geometry Integration**: Parameter validation must happen at multiple layers, and type equality can be unreliable.

**Critical Requirements**:
- **Python Type Equality Issues**: Never rely on `==` for ctypes structures - use field comparison:
  ```python
  # WRONG: color != RGBcolor(1, 1, 1) may fail even when equal
  # RIGHT: field-based comparison
  if color and not (color.r == 1.0 and color.g == 1.0 and color.b == 1.0):
      # Use colored version
  ```

- **SphericalCoord Array Mapping**: `SphericalCoord.to_list()` returns 4 elements but C++ interface expects 3:
  ```python
  # Extract only radius, elevation, azimuth for C++ interface
  rotation_list = [rotation.radius, rotation.elevation, rotation.azimuth]
  ```

- **Multi-layer Validation**: Implement validation at Python, ctypes, and C++ levels for robustness

### 8.8 Compound Geometry Pattern

**Lesson from Compound Geometry Integration**: Methods returning arrays of UUIDs require special handling patterns different from single-primitive methods.

**Requirements**:
- **Return Type Consistency**: Compound geometry methods return `List[int]` of UUIDs, not single integers
- **Efficient Array Conversion**: Use static thread_local vectors for C++ to Python array conversion
- **Parameter Validation**: Validate subdivisions, sizes, and counts at Python level before C++ calls
- **Error Code Consistency**: Use consistent error codes (`PYHELIOS_ERROR_INVALID_PARAMETER`) across all functions
- **Method Naming**: Use clear patterns like `addTile()` vs `addTileWithColor()` for different signatures

## Troubleshooting

### Build Issues

#### Plugin Not Found During Build

```bash
# Check plugin exists in helios-core
ls helios-core/plugins/yourplugin/

# Check metadata registration
python -c "
from pyhelios.config.plugin_metadata import get_plugin_metadata
print(get_plugin_metadata('yourplugin'))
"

# Verify plugin selection
build_scripts/build_helios --plugins yourplugin --verbose
```

#### CMake Configuration Errors

```bash
# Check CMake can find plugin
cd pyhelios_build/build
cmake .. -DPLUGINS="yourplugin" --debug-output

# Check for missing dependencies
cmake .. -DPLUGINS="yourplugin" 2>&1 | grep -i "not found"
```

#### Library Linking Errors

```bash
# Check library symbols (macOS/Linux)
nm -D libhelios.dylib | grep -i yourplugin
objdump -t libhelios.so | grep -i yourplugin

# Windows
dumpbin /exports libhelios.dll | findstr yourplugin
```

### Runtime Issues

#### AttributeError in ctypes Prototypes

```python
# Debug function availability
from pyhelios.plugins import helios_lib

try:
    func = getattr(helios_lib, 'yourPluginFunction')
    print("Function available:", func)
except AttributeError:
    print("Function not found in library")
    
# List all available functions
print([name for name in dir(helios_lib) if 'yourplugin' in name.lower()])
```

#### Segmentation Faults

**Lesson from Compound Geometry Integration**: Segfaults often occur during cleanup, not during function execution.

**Common Causes and Solutions**:

1. **Context Double Deletion** (Most Common):
   ```python
   # SYMPTOM: Segfault in destroyContext during test teardown
   # CAUSE: Context being destroyed multiple times
   # FIX: Set pointer to None after deletion
   def __exit__(self, exc_type, exc_value, traceback):
       if self.context is not None:
           context_wrapper.destroyContext(self.context)
           self.context = None  # Critical fix
   ```

2. **Static Vector Memory Issues**:
   ```cpp
   // SYMPTOM: Random segfaults with compound geometry
   // CAUSE: Static vectors shared between threads
   // FIX: Use thread_local storage
   static thread_local std::vector<unsigned int> static_result;  // Not just static
   ```

3. **Parameter Array Bounds**:
   ```python
   # SYMPTOM: Segfault when calling functions with arrays
   # CAUSE: Wrong array size expectations
   # CHECK: SphericalCoord.to_list() returns 4 elements, C++ expects 3
   rotation_list = [rotation.radius, rotation.elevation, rotation.azimuth]  # Only 3
   ```

4. **ctypes Type Mismatches**:
   ```python
   # Check parameter types and counts
   # Common causes:
   # - Wrong ctypes parameter types
   # - Null pointer dereference  
   # - Array bounds errors
   # - Wrong parameter count
   ```

**Debugging Steps**:
1. **Check if segfault happens during cleanup**: Run single test vs. test suite
2. **Verify Context pointer management**: Add logging to `__exit__` methods  
3. **Test with different thread counts**: `pytest -n 1` vs `pytest -n auto`
4. **Use memory debugging tools**: `valgrind` on Linux, AddressSanitizer
5. **Add debugging to C++ interface**: Use GDB or Visual Studio debugger

#### Asset Loading Failures

```bash
# Check asset locations
find . -name "*.vert" -o -name "*.frag" -o -name "*.xml"

# Check working directory
python -c "
import os
print('Working directory:', os.getcwd())
print('Expected assets at: plugins/yourplugin/')
"

# Test asset loading manually
python -c "
import os
if os.path.exists('plugins/yourplugin/config.xml'):
    print('Assets found')
else:
    print('Assets missing - check build asset copying')
"
```

### Integration Issues

#### Plugin Not Appearing in Registry

```python
# Check plugin registration
from pyhelios.plugins.registry import get_plugin_registry

registry = get_plugin_registry()
all_plugins = registry.get_all_plugins()
print("All plugins:", all_plugins)

available = registry.get_available_plugins()
print("Available plugins:", available)

# Check metadata
from pyhelios.config.plugin_metadata import PLUGIN_METADATA
print("Registered metadata:", list(PLUGIN_METADATA.keys()))
```

#### Import Errors

```python
# Check wrapper imports
try:
    from pyhelios.wrappers import UYourPluginWrapper
    print("Wrapper imported successfully")
except ImportError as e:
    print("Wrapper import failed:", e)

# Check high-level import
try:
    from pyhelios import YourPlugin
    print("High-level class imported successfully")
except ImportError as e:
    print("High-level import failed:", e)
```

## Examples from Existing Plugins

### WeberPennTree Example

Simple plugin with asset management:

```python
# Asset-aware initialization
with _weberpenntree_working_directory():
    self.wpt = wpt_wrapper.createWeberPennTreeWithBuildPluginRootDirectory(
        context.getNativePtr(), str(build_dir)
    )
```

### RadiationModel Example

Complex plugin with availability checking:

```python
# Plugin availability checking
registry = get_plugin_registry()
if not registry.is_plugin_available('radiation'):
    raise RadiationModelError(comprehensive_error_message)

# Context manager for GPU resources
def __exit__(self, exc_type, exc_value, traceback):
    if self.radiation_model:
        radiation_wrapper.destroyRadiationModel(self.radiation_model)
```

### Visualizer Example

Plugin with extensive asset requirements:

```python
# Asset-aware working directory
with _visualizer_working_directory():
    self.visualizer = visualizer_wrapper.create_visualizer(width, height, headless)

# Platform-specific error messages
if not registry.is_plugin_available('visualizer'):
    raise VisualizerError(platform_specific_error_msg)
```

---

This guide provides comprehensive coverage of PyHelios plugin integration. Following these phases and requirements will ensure successful integration of new Helios plugins while maintaining PyHelios's high standards for cross-platform compatibility, error handling, and user experience.