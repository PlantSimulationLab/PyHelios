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
11. [Phase 9: Code Review and Quality Assurance](#phase-9-code-review-and-quality-assurance)
12. [Critical Requirements](#critical-requirements)
13. [Troubleshooting](#troubleshooting)
14. [Examples from Existing Plugins](#examples-from-existing-plugins)

## Overview

PyHelios uses a sophisticated plugin architecture that enables seamless integration of Helios C++ plugins through Python bindings. The integration process involves **9 distinct phases**, each with specific requirements and best practices.

### Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                    PyHelios Plugin Architecture             │
├─────────────────────────────────────────────────────────────┤
│  Python High-Level API (YourPlugin.py)                      │
│  ├── Context managers and error handling                    │
│  └── User-friendly methods with type hints                  │
├─────────────────────────────────────────────────────────────┤
│  ctypes Wrappers (UYourPluginWrapper.py)                    │
│  ├── Function prototypes and availability detection         │
│  └── Python-to-C type conversion                            │
├─────────────────────────────────────────────────────────────┤
│  C++ Interface (pyhelios_interface.cpp)                     │
│  ├── C-compatible wrapper functions                         │
│  └── Exception handling and parameter validation            │
├─────────────────────────────────────────────────────────────┤
│  Native Plugin (helios-core/plugins/yourplugin/)            │
│  ├── C++ plugin implementation                              │
│  └── Runtime assets (shaders, textures, configs)            │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

Before starting plugin integration, ensure you have:

1. **Helios C++ plugin** working in helios-core
2. **Development environment** with CMake, appropriate compiler
3. **Plugin documentation** from helios-core
4. **Understanding of plugin dependencies** (CUDA, OpenGL, etc.)
5. **Test data** or examples for validation

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
        test_symbols=["createYourPlugin", "yourPluginMethod1", "yourPluginMethod2"]  # CRITICAL: Must match C++ function names EXACTLY
    ),
}
```

### 1.2 Validation

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

The PyHelios build system automatically handles plugin integration through the flexible plugin selection system. However, you must manually add the plugin's include directory to enable header file compilation.

**ESSENTIAL**: Add your plugin's include directory to `pyhelios_build/CMakeLists.txt` in both the `pyhelios_interface` and `pyhelios_shared` target sections following the existing pattern for other plugins (visualizer, weberpenntree, radiation).

**Automatic Integration**: Your plugin will be built when:
- User explicitly selects it: `--plugins yourplugin`
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

### 2.3 Add to Default Build

**Important**: For mature plugins that should be included in default builds, add your plugin to the `INTEGRATED_PLUGINS` constant at the top of `build_scripts/build_helios.py`.

**CRITICAL**: PyHelios uses a single canonical list to prevent maintenance issues. There is only ONE place to add new integrated plugins:

```python
# In build_scripts/build_helios.py (lines ~40-50)
INTEGRATED_PLUGINS = [
    "visualizer",
    "weberpenntree",
    "radiation",
    "energybalance",
    "solarposition",
    "stomatalconductance",
    "photosynthesis",
    "plantarchitecture",
    "yourplugin"  # Add new plugin here
]
```

**DO NOT** modify any other hardcoded lists in the file - they have all been replaced with references to `INTEGRATED_PLUGINS`.

### 2.4 Test Build Integration

Test that your plugin builds correctly:

```bash
# Clean build with your plugin
build_scripts/build_helios --clean --plugins yourplugin

# Test with interactive mode
build_scripts/build_helios --interactive

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

# CRITICAL: Import UContext from UContextWrapper for ctypes compatibility
from .UContextWrapper import UContext
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
    
    # CRITICAL: Add errcheck to ALL functions that can fail
    # Missing errcheck callbacks result in silent failures and cryptic ctypes errors

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

### 4.2 Critical Error Handling Requirements

**ESSENTIAL**: Every ctypes function prototype must have an errcheck callback to automatically translate C++ exceptions to Python exceptions. Missing errcheck callbacks lead to:

- **Silent failures** where errors are ignored
- **Cryptic ctypes errors** like "Don't know how to convert parameter N"
- **Poor debugging experience** requiring manual try-catch everywhere

#### Complete errcheck Setup Pattern

```python
# Step 1: Set up all function prototypes
try:
    helios_lib.yourFunction1.argtypes = [...]
    helios_lib.yourFunction1.restype = ...
    
    helios_lib.yourFunction2.argtypes = [...]
    helios_lib.yourFunction2.restype = ...
    
    # Mark functions as available
    _YOURPLUGIN_FUNCTIONS_AVAILABLE = True
    
except AttributeError:
    _YOURPLUGIN_FUNCTIONS_AVAILABLE = False

# Step 2: Add errcheck to ALL functions (critical!)
if _YOURPLUGIN_FUNCTIONS_AVAILABLE:
    helios_lib.yourFunction1.errcheck = _check_error
    helios_lib.yourFunction2.errcheck = _check_error
    # Add errcheck for EVERY function - no exceptions!
```

#### Common errcheck Mistakes

**❌ Wrong - Missing errcheck:**
```python
helios_lib.loadPLYWithTransforms.argtypes = [...]
helios_lib.loadPLYWithTransforms.restype = ...
# Missing: .errcheck = _check_error
# Result: Silent failures, cryptic ctypes errors
```

**✅ Correct - Complete errcheck setup:**
```python
helios_lib.loadPLYWithTransforms.argtypes = [...]
helios_lib.loadPLYWithTransforms.restype = ...
helios_lib.loadPLYWithTransforms.errcheck = _check_error  # Essential!
```

#### Error Behavior Without errcheck

When errcheck is missing, users experience:

1. **Silent parameter conversion failures** that show as cryptic messages
2. **No automatic exception translation** from C++ to Python
3. **Poor debugging experience** requiring manual error checking
4. **Inconsistent error handling** across PyHelios functions

#### Function Prototype Setup Failure Modes

**CRITICAL**: Individual function availability can vary within a plugin. Use granular try/except blocks to avoid losing available functions due to missing ones.

**❌ Wrong - Single try/except block:**
```python
# This fails if ANY function is missing, losing ALL functions
try:
    helios_lib.function1.argtypes = [...]
    helios_lib.function2.argtypes = [...]  # If this fails...
    helios_lib.function3.argtypes = [...]  # ...these are lost too
    _PLUGIN_AVAILABLE = True
except AttributeError:
    _PLUGIN_AVAILABLE = False  # All functions marked unavailable
```

**✅ Correct - Individual try/except blocks:**
```python
# Each function is set up independently
_AVAILABLE_FUNCTIONS = []

try:
    helios_lib.function1.argtypes = [...]
    helios_lib.function1.errcheck = _check_error
    _AVAILABLE_FUNCTIONS.append('function1')
except AttributeError:
    pass

try:
    helios_lib.function2.argtypes = [...]
    helios_lib.function2.errcheck = _check_error
    _AVAILABLE_FUNCTIONS.append('function2')
except AttributeError:
    pass

# Mark as available if we found any functions
_PLUGIN_AVAILABLE = len(_AVAILABLE_FUNCTIONS) > 0
```

#### Verification Commands

Test that error handling works correctly:

```bash
# Test automatic error translation
python -c "
from pyhelios import Context
context = Context()
try:
    # This should raise HeliosRuntimeError automatically
    context.getPrimitiveInfo(999999)
except Exception as e:
    print(f'SUCCESS: {type(e).__name__}: {e}')
"

# Test file loading error handling  
python -c "
from pyhelios import Context
context = Context()
try:
    # This should raise FileNotFoundError or HeliosFileIOError
    context.loadPLY('nonexistent.ply')
except Exception as e:
    print(f'SUCCESS: {type(e).__name__}: {e}')
"

# Test function prototype setup
python -c "
from pyhelios.wrappers.UContextWrapper import helios_lib
func = helios_lib.loadPLYWithOriginHeightRotationColor
if func.argtypes is None:
    print('ERROR: Function prototype not set up')
else:
    print('SUCCESS: Function prototype configured')
"
```

### 4.3 Import in Wrappers Module

**File**: `pyhelios/wrappers/__init__.py`

Add import for your wrapper:

```python
# Existing imports...
from . import UYourPluginWrapper
```

## Phase 5: High-Level Python API

### 5.1 Naming Convention Requirements

**CRITICAL**: Python API method names must exactly match the corresponding C++ method names to maintain consistency across PyHelios. Follow these naming conventions:

**Method Names**: Use **upperCamelCase** to match C++ exactly:
- ✅ Correct: `addRadiationBand()` (matches C++ `addRadiationBand()`)
- ❌ Wrong: `add_radiation_band()` (Python snake_case)

**Parameter Names**: Use **C++ parameter naming** where possible:
- ✅ Correct: `UUIDs` (matches C++ `std::vector<uint> &UUIDs`)
- ❌ Wrong: `uuids` (Python snake_case)
- ✅ Correct: `dt` (matches C++ `float dt`)

**Examples from Existing PyHelios Classes**:
- `Context.addPatch()` matches C++ `Context::addPatch()`
- `RadiationModel.addRadiationBand()` matches C++ `RadiationModel::addRadiationBand()`
- `WeberPennTree.buildTree()` matches C++ `WeberPennTree::buildTree()`

### 5.2 Create High-Level Class

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

# CRITICAL: Import validation functions and ensure they RETURN validated objects
try:
    from .validation.datatypes import validate_vec3, validate_vec2, validate_int2
except ImportError:
    # Fallback validation functions that MUST return validated objects
    def validate_vec3(value, name, func):
        if hasattr(value, 'x') and hasattr(value, 'y') and hasattr(value, 'z'):
            return value  # CRITICAL: Must return the validated object
        if isinstance(value, (list, tuple)) and len(value) == 3:
            from .wrappers.DataTypes import vec3
            return vec3(*value)  # CRITICAL: Must return the converted object
        raise ValueError(f"{name} must be vec3 or 3-element list/tuple")

    def validate_vec2(value, name, func):
        if hasattr(value, 'x') and hasattr(value, 'y'):
            return value  # CRITICAL: Must return the validated object
        if isinstance(value, (list, tuple)) and len(value) == 2:
            from .wrappers.DataTypes import vec2
            return vec2(*value)  # CRITICAL: Must return the converted object
        raise ValueError(f"{name} must be vec2 or 2-element list/tuple")

    def validate_int2(value, name, func):
        if hasattr(value, 'x') and hasattr(value, 'y'):
            return value  # CRITICAL: Must return the validated object
        if isinstance(value, (list, tuple)) and len(value) == 2:
            from .wrappers.DataTypes import int2
            return int2(*value)  # CRITICAL: Must return the converted object
        raise ValueError(f"{name} must be int2 or 2-element list/tuple")

from .validation.core import validate_positive_value

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
    
    def computeSomething(self, parameters: List[float]) -> int:
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
            >>> plugin.computeSomething([1.0, 2.0, 3.0])
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
    
    def getDataArray(self, UUID: int) -> List[float]:
        """
        Get array data for specified primitive.
        
        Args:
            UUID: Primitive UUID
            
        Returns:
            Array of data values
            
        Raises:
            ValueError: If UUID is invalid
            YourPluginError: If data retrieval fails
        """
        if UUID < 0:
            raise ValueError("UUID must be non-negative")
        
        try:
            return plugin_wrapper.yourPluginGetArray(self._plugin_ptr, UUID)
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

### 6.3 Asset Management Strategy: Stage 1 vs Stage 2

**CRITICAL LESSON FROM PLANTARCHITECTURE INTEGRATION**: PyHelios uses two distinct asset management strategies depending on the distribution method.

#### Stage 1: CMake + Working Directory Pattern (Current Standard)

**For development builds and most current plugins**, use the CMake asset copying + working directory context manager pattern:

**CMake Level (already implemented for most plugins)**:
- CMake automatically copies assets to `build/plugins/yourplugin/` during build
- Assets include `copy_obj_assets`, `copy_texture_assets`, etc. targets
- No manual Python asset copying required

**Python Level (required for all plugins with assets)**:
```python
from contextlib import contextmanager
from .assets import get_asset_manager

@contextmanager
def _yourplugin_working_directory():
    """
    Context manager that temporarily changes working directory to where YourPlugin assets are located.

    YourPlugin C++ code uses hardcoded relative paths like "plugins/yourplugin/assets/"
    expecting assets relative to working directory. This manager temporarily changes to the build
    directory where assets are actually located.
    """
    # Find the build directory containing YourPlugin assets
    asset_manager = get_asset_manager()
    working_dir = asset_manager._get_helios_build_path()

    if working_dir and working_dir.exists():
        yourplugin_assets = working_dir / 'plugins' / 'yourplugin'
    else:
        # Fallback to development paths
        current_dir = Path(__file__).parent
        repo_root = current_dir.parent
        build_lib_dir = repo_root / 'pyhelios_build' / 'build' / 'lib'
        working_dir = build_lib_dir.parent
        yourplugin_assets = working_dir / 'plugins' / 'yourplugin'

        if not build_lib_dir.exists():
            raise RuntimeError(
                f"PyHelios build directory not found at {build_lib_dir}. "
                f"YourPlugin requires native libraries to be built. "
                f"Run: build_scripts/build_helios --plugins yourplugin"
            )

    if not yourplugin_assets.exists():
        raise RuntimeError(
            f"YourPlugin assets not found at {yourplugin_assets}. "
            f"Build system failed to copy YourPlugin assets. "
            f"Run: build_scripts/build_helios --clean --plugins yourplugin"
        )

    # Change to the build directory temporarily
    original_dir = os.getcwd()
    try:
        os.chdir(working_dir)
        logger.debug(f"Changed working directory to {working_dir} for YourPlugin asset access")
        yield working_dir
    finally:
        os.chdir(original_dir)
        logger.debug(f"Restored working directory to {original_dir}")

# Use in plugin operations
class YourPlugin:
    def __init__(self, context: Context):
        # Create plugin instance with asset-aware working directory
        with _yourplugin_working_directory():
            self._plugin_ptr = plugin_wrapper.createYourPlugin(context.getNativePtr())

    def some_method(self):
        # Use working directory for operations requiring assets
        with _yourplugin_working_directory():
            return plugin_wrapper.yourPluginMethod(self._plugin_ptr, ...)
```

#### Stage 2: Python Asset Copying (Future Wheel Distribution)

**For future wheel-based distribution**, Python will copy assets to package directories:

```python
def _copy_yourplugin_assets(self) -> None:
    """
    Copy YourPlugin runtime assets to expected locations for wheel distribution.

    NOTE: This is Stage 2 asset management for future wheel distribution.
    Most plugins currently use Stage 1 (CMake + working directory) pattern.
    """
    # Implementation for when needed...
```

**CRITICAL WHEEL BUILD REQUIREMENT FOR STAGE 1 PLUGINS**: Even Stage 1 plugins require wheel packaging configuration to work in distributed wheels.

**File**: `build_scripts/prepare_wheel.py`

Add your plugin to the `plugin_asset_dirs` mapping:

```python
# Line ~215 in build_scripts/prepare_wheel.py
plugin_asset_dirs = {
    'weberpenntree': ['leaves', 'wood', 'xml'],
    'visualizer': ['textures', 'shaders'],
    'yourplugin': ['textures', 'obj', 'xml'],  # Add this line
    # Include only essential runtime asset directories
}
```

**Asset Directory Selection Guidelines**:
- **Include**: Runtime assets required by C++ code (textures, models, configs)
- **Exclude**: Source files (`.blend`, development tools, documentation)
- **Verify**: Check helios-core/plugins/yourplugin/assets/ for directory structure

**Why This Is Required**: The working directory context manager looks for assets via the asset manager, which searches multiple paths including `pyhelios/assets/build/plugins/yourplugin/`. During wheel builds, assets must be copied to this location by `prepare_wheel.py` or the plugin will fail with "assets not found" errors.

**INTEGRATION RULE**: New plugins should follow the **Stage 1 pattern** (CMake + working directory context manager) like WeberPennTree, Visualizer, and PlantArchitecture, **AND** must be added to `plugin_asset_dirs` in `prepare_wheel.py` for wheel distribution.

### 6.4 Plugin-Specific Asset Considerations

Some plugins may require special asset handling:

```python
# In build_scripts/build_helios.py, most plugins have commented-out asset copying
# NOTE: Asset copying for yourplugin plugin disabled - Stage 1 asset management
# uses CMake targets (copy_obj_assets, copy_texture_assets) with working directory context manager
# self._copy_yourplugin_assets()

# Only uncomment and implement if Stage 2 distribution specifically required
```

## Phase 7: Testing Integration

### 7.1 Create Test File

**CRITICAL NAMING REQUIREMENT**: The test file name must exactly match the plugin name for proper pytest hook integration. The PyHelios test system uses filename pattern matching to automatically detect required plugins and skip tests when plugins are unavailable.

**File**: `tests/test_yourplugin.py` (where "yourplugin" exactly matches the plugin name in `plugin_metadata.py`)

**❌ Wrong**: `test_your_plugin.py` (underscore doesn't match plugin name "yourplugin")  
**✅ Correct**: `test_yourplugin.py` (exactly matches plugin name "yourplugin")

This naming convention enables automatic test skipping on machines without the required plugin, preventing test failures due to missing dependencies.

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
    def test_plugin_available(self):
        """Test that plugin is available when expected"""
        from pyhelios.config.plugin_metadata import PLUGIN_METADATA
        
        # Should be in plugin metadata
        assert 'yourplugin' in PLUGIN_METADATA

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
        assert hasattr(YourPlugin, 'computeSomething')
        assert hasattr(YourPlugin, 'getDataArray')
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
                result = plugin.computeSomething([1.0, 2.0, 3.0])
                assert isinstance(result, int)
                assert result >= 0  # Adjust based on expected output
    
    def test_parameter_validation(self):
        """Test parameter validation"""
        with Context() as context:
            with YourPlugin(context) as plugin:
                # Test empty parameters
                with pytest.raises(ValueError, match="cannot be empty"):
                    plugin.computeSomething([])
                
                # Test invalid parameter count
                with pytest.raises(ValueError, match="at least"):
                    plugin.computeSomething([1.0])
                
                # Test invalid parameter type (if applicable)
                with pytest.raises(ValueError, match="numeric"):
                    plugin.computeSomething([1.0, "invalid", 3.0])
    
    def test_data_array_retrieval(self):
        """Test array data retrieval"""
        with Context() as context:
            # Create some geometry to test with
            patch_uuid = context.addPatch(center=[0, 0, 1], size=[1, 1])
            
            with YourPlugin(context) as plugin:
                # Test valid UUID
                data = plugin.getDataArray(patch_uuid)
                assert isinstance(data, list)
                # Adjust assertions based on expected data
                
                # Test invalid UUID
                with pytest.raises((ValueError, YourPluginError)):
                    plugin.getDataArray(-1)

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
                result = plugin.computeSomething([1.0, 2.0, 3.0])
                assert result is not None
    
    def test_error_handling_integration(self):
        """Test that C++ exceptions become proper Python exceptions"""
        with Context() as context:
            with YourPlugin(context) as plugin:
                # Test operations that should cause specific errors
                # Adjust based on plugin behavior
                try:
                    plugin.getDataArray(99999)  # Non-existent UUID
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
                result = plugin.computeSomething([1.0, 2.0, 3.0])
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

### 7.3 Critical Test Fixture Requirements

**LESSON FROM PLANTARCHITECTURE INTEGRATION**: Test fixtures MUST include proper cleanup patterns to prevent state contamination between tests. PyHelios uses pytest-forked for subprocess isolation, but proper fixture cleanup is still required for resource management.

#### Proper Fixture Patterns

**✅ CORRECT - Use conftest.py patterns with cleanup:**
```python
@pytest.fixture
def basic_context(check_native_library):
    """Fixture providing basic context with proper cleanup"""
    context = Context()
    yield context
    # CRITICAL: Proper cleanup
    context.__exit__(None, None, None)

@pytest.fixture
def yourplugin_instance(basic_context):
    """Fixture providing plugin instance with proper cleanup"""
    if not basic_context.is_plugin_available('yourplugin'):
        pytest.skip("YourPlugin not available")

    plugin = YourPlugin(basic_context)
    yield plugin
    # CRITICAL: Proper cleanup
    plugin.__exit__(None, None, None)
```

**❌ WRONG - Missing cleanup causes resource leaks:**
```python
@pytest.fixture
def context(self):
    return Context()  # NO CLEANUP - causes resource leaks

@pytest.fixture
def plugin(self):
    context = Context()
    return YourPlugin(context)  # NO CLEANUP - causes resource leaks
```

#### Cleanup Verification

Always verify that your test fixtures follow the established patterns in `conftest.py`:

```bash
# Check that test fixtures include proper cleanup
grep -A 10 -B 5 "__exit__" tests/test_yourplugin.py

# Should show context manager exits or proper cleanup calls
```

### 7.4 Run Tests

```bash
# Run all plugin tests (automatically uses pytest-forked for isolation)
pytest tests/test_yourplugin.py -v

# Run only cross-platform tests
pytest tests/test_yourplugin.py -m cross_platform

# Run only native tests (if library available)
pytest tests/test_yourplugin.py -m native_only

# Run with coverage
pytest tests/test_yourplugin.py --cov=pyhelios.YourPlugin

# Verify pytest-forked is working (should show "plugins: forked-X.X.X")
pytest tests/test_yourplugin.py --tb=short
```

## Phase 8: Documentation

### 8.1 API Documentation

**File**: `docs/plugin_yourplugin.md`

```markdown
# YourPlugin Documentation {#YourPluginDoc}

## Overview

YourPlugin provides [detailed description of plugin capabilities and use cases].

## System Requirements

- **Platforms**: Windows, Linux, macOS
- **Dependencies**: [List any special requirements]
- **GPU**: [Required/Not required]
- **Memory**: [Any special memory requirements]

## Installation

### Build with YourPlugin

```bash
# Using explicit selection
build_scripts/build_helios --interactive

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

**IMPORTANT NOTE**: Do NOT include an "API Reference" section in plugin documentation. Doxygen automatically generates comprehensive API documentation from the Python docstrings in your plugin class. Focus on overview, installation, examples, and troubleshooting instead.

## Examples

### Basic Usage

```python
from pyhelios import Context, YourPlugin

with Context() as context:
    # Add some geometry
    patch_uuid = context.addPatch(center=[0, 0, 1], size=[1, 1])
    
    with YourPlugin(context) as plugin:
        # Compute something
        result = plugin.computeSomething([1.0, 2.0, 3.0])
        print(f"Computation result: {result}")
        
        # Get data for the patch
        data = plugin.getDataArray(patch_uuid)
        print(f"Patch data: {data}")
```

### Error Handling

```python
from pyhelios import Context, YourPlugin, YourPluginError

with Context() as context:
    try:
        with YourPlugin(context) as plugin:
            result = plugin.computeSomething([1.0, 2.0, 3.0])
            
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
            data = plugin.getDataArray(uuid)
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

### 8.2 Update Documentation Configuration

**IMPORTANT**: Update the Doxygen configuration to include your plugin documentation and exclude implementation details:

**File**: `docs/Doxyfile.python`

**First, add your documentation file to the `INPUT` list:**

```
INPUT = docs/plugin_integration_guide.md \
        docs/plugin_energybalance.md \
        docs/plugin_radiation.md \
        docs/plugin_visualizer.md \
        docs/plugin_weberpenntree.md \
        docs/plugin_yourplugin.md \    # Add this line
        # ... rest of INPUT files
```

**Then, add your wrapper to the `EXCLUDE` list:**

```
EXCLUDE = pyhelios/plugins/__pycache__ \
          pyhelios/__pycache__ \
          pyhelios/wrappers/UContextWrapper.py \
          pyhelios/wrappers/UGlobalWrapper.py \
          pyhelios/wrappers/ULoggerWrapper.py \
          pyhelios/wrappers/URadiationModelWrapper.py \
          pyhelios/wrappers/UVisualizerWrapper.py \
          pyhelios/wrappers/UWeberPennTreeWrapper.py \
          pyhelios/wrappers/UYourPluginWrapper.py \    # Add this line
          pyhelios/config \
          pyhelios/assets \
          # ... rest of exclusions
```

This ensures your plugin documentation appears in the generated docs while hiding low-level implementation details from end-users.

**Finally, add your plugin to the navigation layout:**

**File**: `docs/DoxygenLayout.xml`

Add your plugin to the navigation structure in alphabetical order:

```xml
<!-- Plugin Documentation Section -->
<tab type="usergroup" visible="yes" url="@ref Plugins" title="Plugins" intro="">
  <!-- Currently Implemented Plugins (Alphabetized) -->
  <tab type="user" visible="yes" url="@ref EnergyBalanceDoc" title="Energy Balance"/>
  <tab type="user" visible="yes" url="@ref YourPluginDoc" title="Your Plugin"/>    <!-- Add this line -->
  <tab type="user" visible="yes" url="@ref RadiationDoc" title="Radiation Model"/>
  <!-- ... other plugins ... -->
</tab>
```

### 8.3 Update Main Documentation

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

### 8.4 Add Files to Version Control

**IMPORTANT**: Don't forget to add all the new plugin files to git:

```bash
# Add all new plugin files to git
git add native/include/pyhelios_wrapper_yourplugin.h
git add pyhelios/wrappers/UYourPluginWrapper.py
git add pyhelios/YourPlugin.py
git add tests/test_yourplugin.py
git add docs/plugin_yourplugin.md

# Also add any modified files
git add pyhelios/config/plugin_metadata.py
git add pyhelios/__init__.py
git add pyhelios/wrappers/__init__.py
git add native/src/pyhelios_wrapper.cpp
git add docs/Doxyfile.python

# Check what files are staged
git status

# Commit the plugin integration
git commit -m "Add YourPlugin integration

- Add C++ wrapper interface and implementation
- Add ctypes wrapper with error handling
- Add high-level Python API with context manager
- Add comprehensive test suite (cross-platform + native)
- Add complete documentation
- Update plugin metadata

🤖 Generated with Claude Code"
```

**Common files to check:**
- All new `.h` header files in `native/include/`
- All new `.py` wrapper files in `pyhelios/wrappers/`
- Main plugin API file `pyhelios/YourPlugin.py`
- Test file `tests/test_yourplugin.py`
- Documentation file `docs/plugin_yourplugin.md`
- Modified configuration files in `pyhelios/config/`
- Updated `__init__.py` files

## Parameter Validation Requirements

**CRITICAL: All plugin methods MUST implement parameter validation using PyHelios validation decorators.**

### Implementation Steps

**1. Import and Apply Decorators**
```python
from .validation.plugin_decorators import validate_your_plugin_params

@validate_your_plugin_params
def your_method(self, param1: type, param2: type) -> return_type:
    # Method implementation
```

**2. Create Plugin Validation Functions**
Add to `pyhelios/validation/plugins.py`:
```python
def validate_your_parameter(value, param_name, method_name):
    if not meets_requirements(value):
        raise ValidationError(f"{method_name}() '{param_name}' {error_details}")
    return value
```

**3. Create Method Decorators** 
Add to `pyhelios/validation/plugin_decorators.py`:
```python
def validate_your_method_params(func):
    def wrapper(self, param1=None, **kwargs):
        if param1 is not None:
            param1 = validate_your_parameter(param1, 'param1', func.__name__)
        return func(self, param1, **kwargs)
    return wrapper
```

### Validation Standards

- **Coverage**: Validate ALL public method parameters
- **Type coercion**: Support list/tuple → vec3/vec2 for compatibility  
- **Duck typing**: Use `hasattr(value, 'x')` for vector recognition
- **Error messages**: Be specific with expected vs actual values
- **Exception**: Use ValidationError (extends ValueError)
- **Numeric validation**: Check for NaN/infinity with `math.isfinite()`

### Common Patterns

```python
# Import common validators
from .validation.core import validate_positive_value, validate_finite_numeric
from .validation.datatypes import validate_vec3, validate_rgb_color
from .validation.plugins import validate_uuid_list

# Usage in decorators
validate_positive_value(scale, 'scale', 'buildTree')
origin = validate_vec3(origin, 'origin', 'addPatch') 
color = validate_rgb_color(color, 'color', 'setPrimitiveColor')
uuids = validate_uuid_list(uuids, 'UUIDs', 'processUUIDs')
```

### Testing Requirements

Create tests for both validation logic and plugin functionality:
```python
@pytest.mark.cross_platform  # Works with mocks
def test_plugin_validation():
    # Test parameter validation

@pytest.mark.native_only     # Requires native libraries  
def test_plugin_functionality():
    # Test actual plugin behavior
```

### Integration Checklist

- [ ] All public methods have validation decorators
- [ ] Plugin validation functions in `plugins.py`
- [ ] Method decorators in `plugin_decorators.py`  
- [ ] Test coverage for validation and functionality
- [ ] Clear error messages with actionable guidance
- [ ] Backward compatibility through type coercion

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
- **CRITICAL**: Use errcheck callbacks for automatic error checking on ALL ctypes functions
- Never allow C++ exceptions to cross into Python

**Common Failure**: Missing errcheck callbacks on ctypes functions result in:
- Silent failures and cryptic "Don't know how to convert parameter N" errors
- Poor debugging experience requiring manual try-catch everywhere
- Inconsistent error handling across PyHelios

**Solution**: Always add `helios_lib.yourFunction.errcheck = _check_error` for every function prototype.

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

#### Tests Not Being Skipped Properly

**Symptom**: Tests for unavailable plugins fail instead of being skipped with `@pytest.mark.native_only`.

**Root Cause**: Test file naming doesn't match plugin name, preventing pytest hook from detecting required plugin.

**Solution**: 
```bash
# Check if test file name matches plugin name exactly
ls tests/test_*yourplugin*

# Should show: tests/test_yourplugin.py (exact match)
# NOT: tests/test_your_plugin.py (underscore variant)

# Rename if incorrect
mv tests/test_your_plugin.py tests/test_yourplugin.py
```

#### Pytest Test Isolation Issues (State Contamination)

**CRITICAL PROBLEM**: A persistent issue where tests pass individually but fail when run as part of the full test suite, affecting multiple plugins (energybalance, radiation, stomatalconductance, plantarchitecture).

**Symptoms**:
- Tests pass when run with `pytest tests/test_yourplugin.py -v`
- Same tests fail when run with `pytest` (full suite)
- Import-related failures with class identity mismatches
- Error messages like `AssertionError: False = issubclass(...)` or ctypes pointer type mismatches
- Error messages like `expected LP_UContext instance instead of LP_UContext`
- Resource accumulation and memory leaks between tests
- Segmentation faults during test cleanup

**Root Causes Identified**:

1. **ctypes Structure Type Identity Problem** - Well-documented limitation where identical Structure classes are treated as different types when redefined during pytest module reloading.

2. **Improper Test Fixture Cleanup** - **CRITICAL DISCOVERY FROM PLANTARCHITECTURE INTEGRATION**: Incorrect fixture patterns cause resource leaks and state contamination even with pytest-forked protection.

**COMPREHENSIVE SOLUTION IMPLEMENTED** (v0.1.0+):

#### 1. pytest-forked for Subprocess Isolation

**Complete test isolation** by running each test in a separate subprocess:

```bash
# Installation (automatically included in development dependencies)
pip install pytest-forked>=1.6.0

# Automatic usage via pytest.ini configuration
pytest  # Now uses --forked by default
```

#### 2. MANDATORY Fixture Cleanup Patterns

**LESSON FROM PLANTARCHITECTURE**: Even with subprocess isolation, fixtures must follow proper cleanup patterns to prevent resource leaks within individual test processes.

**✅ CORRECT Fixture Patterns**:
```python
# Context fixtures - MUST use yield + cleanup
@pytest.fixture
def context(self, check_native_library):
    """Context fixture with proper cleanup"""
    context = Context()
    yield context
    # CRITICAL: Explicit cleanup prevents resource leaks
    context.__exit__(None, None, None)

# Plugin fixtures - MUST avoid nested context managers
@pytest.fixture
def yourplugin_instance(self, context):
    """Plugin fixture with proper cleanup"""
    if not plugin_available('yourplugin'):
        pytest.skip("Plugin not available")

    plugin = YourPlugin(context)
    yield plugin
    # CRITICAL: Explicit cleanup prevents resource leaks
    plugin.__exit__(None, None, None)
```

**❌ WRONG Patterns That Cause Contamination**:
```python
# ❌ WRONG - Return without cleanup causes resource leaks
@pytest.fixture
def context(self):
    return Context()  # NO CLEANUP!

# ❌ WRONG - Nested context manager in fixture
@pytest.fixture
def plugin(self, context):
    try:
        with YourPlugin(context) as plugin:  # Nested context manager
            yield plugin
    except PluginError:
        pytest.skip("Plugin failed")

# ❌ WRONG - Double context manager usage
@pytest.fixture
def context(self):
    with Context() as context:  # Context manager in fixture
        yield context
```

#### 3. State Contamination Prevention Checklist

**MANDATORY for all new plugin integrations**:

- [ ] **Context fixtures use yield + __exit__ cleanup pattern**
- [ ] **Plugin fixtures avoid nested context managers**
- [ ] **All fixtures follow conftest.py established patterns**
- [ ] **Test isolation verified with both individual and suite runs**
- [ ] **Resource cleanup verified with fixture pattern checking**

#### 4. Verification Commands

**Test fixture cleanup patterns**:
```bash
# Verify fixtures include proper cleanup
grep -A 10 -B 5 "__exit__" tests/test_yourplugin.py

# Should show context manager exits or proper cleanup calls
# If no results, fixtures need cleanup implementation
```

**Test state contamination elimination**:
```bash
# Individual test (should pass)
pytest tests/test_yourplugin.py -v

# Full suite (should also pass with no contamination)
pytest --tb=short

# Verify pytest-forked active (should show "plugins: forked-X.X.X")
pytest tests/test_yourplugin.py --tb=short
```

This comprehensive solution:
- ✅ Completely eliminates ctypes type contamination between tests
- ✅ Prevents resource leaks and memory accumulation within tests
- ✅ Provides clean module state for each test execution
- ✅ Works across all platforms (Windows, macOS, Linux)
- ✅ Maintains test performance (minimal subprocess overhead)
- ✅ Requires proper fixture patterns for all plugins
- ✅ Prevents ALL forms of test state contamination

**Alternative Solutions** (Legacy - for reference):

**1. Enhanced Test Fixture Architecture** (`conftest.py` - legacy approach):
```python
@pytest.fixture(scope="module", autouse=True)
def reset_plugin_state():
    """Reset plugin registry state between test modules to prevent contamination."""
    # Reset at the start of each test module
    _reset_plugin_registry_if_available()
    yield
    # Reset at the end of each test module
    _reset_plugin_registry_if_available()

def _reset_plugin_registry_if_available():
    """Reset plugin registry to prevent test contamination."""
    try:
        from pyhelios.plugins.registry import reset_plugin_registry
        reset_plugin_registry()
    except ImportError:
        pass
```

**2. Import Path Standardization** (REQUIRED for new plugins):
```python
# ✅ CORRECT - Import from main pyhelios module
from pyhelios import HeliosError, YourPluginError

# ❌ WRONG - Direct import from exceptions module causes contamination
from pyhelios.exceptions import HeliosError
```

**3. Robust Parameter Validation** (for Context-related issues):
```python
# Use duck typing to handle class identity issues during test runs
if not (hasattr(context, '__class__') and 
        (isinstance(context, Context) or 
         context.__class__.__name__ == 'Context')):
    raise TypeError(f"Requires a Context instance, got {type(context).__name__}")
```

**4. Enhanced Error Class Registration** (add to `pyhelios/__init__.py`):
```python
# Ensure ALL plugin error classes are available from main module
try:
    from .YourPlugin import YourPlugin, YourPluginError
except (AttributeError, ImportError):
    YourPlugin = None
    YourPluginError = None
```

**PREVENTION CHECKLIST** for new plugin integrations:
- [ ] Import ALL error classes from main `pyhelios` module, not submodules
- [ ] Add plugin error classes to main module imports in `__init__.py`
- [ ] Use duck typing for Context validation (see pattern above)
- [ ] Test both individual plugin tests AND full test suite
- [ ] Verify no failing tests when plugin unavailable (proper skipping)

**Debugging Commands**:
```bash
# Test individual plugin tests (forked execution automatic)
pytest tests/test_yourplugin.py -v

# Test with other plugin tests to check for contamination (no longer needed with forked execution)
pytest tests/test_yourplugin.py tests/test_energybalance.py tests/test_radiation_model.py -v

# Run full test suite (forked execution prevents contamination)
pytest --tb=short

# Force non-forked execution for debugging (if needed)
pytest tests/test_yourplugin.py --forked=False -v

# Check pytest-forked is working
pytest tests/test_stomatalconductance.py -v --tb=short
# Should show "plugins: forked-X.X.X" in test session header

# Check for import consistency issues (rarely needed with forked execution)
python -c "
from pyhelios import YourPluginError, HeliosError
print('YourPluginError module:', YourPluginError.__module__)
print('HeliosError module:', HeliosError.__module__)
print('Inheritance check:', issubclass(YourPluginError, HeliosError))
"
```

**Resolution Verification**:
With pytest-forked implementation, expect:
- ✅ All tests pass individually: `pytest tests/test_yourplugin.py -v`
- ✅ All tests pass in full suite: `pytest --tb=short`  
- ✅ Zero test failures due to ctypes or state contamination
- ✅ Clean subprocess isolation prevents all forms of test interference
- ✅ Proper test skipping when plugins unavailable
- ✅ Test session shows "plugins: forked-X.X.X" indicating forked execution is active

**Debug Plugin Detection**:
```python
# Test the plugin detection logic
from tests.conftest import _get_required_plugins_for_test

class MockItem:
    def __init__(self, path): 
        self.fspath = type('MockPath', (), {'__str__': lambda self: path})()
        self.name = "test_something"

item = MockItem('tests/test_yourplugin.py')
required_plugins = _get_required_plugins_for_test(item)
print("Detected required plugins:", required_plugins)  # Should include 'yourplugin'
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

## Phase 9: Code Review and Quality Assurance

**CRITICAL FINAL STEP**: After completing all integration phases, conduct a comprehensive code review to ensure production readiness and maintain PyHelios's high quality standards.

### 9.1 Code Review Requirements

**Use the `code-reviewer` sub-agent** to analyze the complete plugin integration holistically:

```bash
# Request comprehensive code review from Claude Code
# Focus on the following critical aspects:
```

**1. Integration Completeness Assessment**
- [ ] **All 8 integration phases completed**: Verify every step from metadata registration through documentation has been properly implemented
- [ ] **No missing components**: Check that all required files exist and are properly configured
- [ ] **Build system integration**: Confirm plugin builds successfully with all dependency combinations
- [ ] **Asset management**: Verify all runtime assets are identified and properly copied

**2. Implementation Production Readiness**
- [ ] **100% functional completeness**: Every public method and property works correctly with no stub implementations
- [ ] **No silent fallbacks**: All error conditions raise appropriate exceptions with actionable messages
- [ ] **No TODO comments**: No placeholder code or unfinished implementations remain
- [ ] **No development artifacts**: Remove debugging code, test-only features, or temporary workarounds
- [ ] **Parameter validation**: All public methods have comprehensive parameter validation using PyHelios decorators
- [ ] **Memory management**: Proper resource cleanup with context managers and safe pointer handling

**3. Testing Quality and Rigor**
- [ ] **Comprehensive test coverage**: Tests cover all public methods, error conditions, and edge cases
- [ ] **No skipped tests**: All tests either pass or are properly marked with platform/dependency requirements
- [ ] **No mock fallbacks in native tests**: Tests marked `@pytest.mark.native_only` use actual plugin functionality
- [ ] **Cross-platform compatibility**: Tests run successfully on all supported platforms with appropriate markers
- [ ] **Integration testing**: Tests verify interaction with other PyHelios components (Context, other plugins)
- [ ] **Performance validation**: Critical operations meet performance expectations
- [ ] **Error handling testing**: Exception paths are thoroughly tested with appropriate error types and messages

**4. Documentation Accuracy Verification**
- [ ] **Line-by-line accuracy**: Every code example compiles and runs correctly
- [ ] **Parameter documentation**: All method parameters documented with correct names, types, and meanings
- [ ] **API consistency**: Method names match C++ API exactly (upperCamelCase convention)
- [ ] **Example validation**: All usage examples have been tested and work as documented
- [ ] **Installation instructions**: Build and installation steps are current and complete
- [ ] **Troubleshooting accuracy**: Error scenarios and solutions reflect actual behavior
- [ ] **System requirements**: Dependencies, platforms, and hardware requirements are accurate

### 9.2 Review Process

**Step 1: Initiate Code Review**
```bash
# Use Claude Code's code-reviewer sub-agent for comprehensive analysis
# Request analysis of the complete plugin integration
```

**Step 2: Integration Phase Checklist**
The code reviewer should verify completion of all integration phases:

```
✅ Phase 1: Plugin Metadata Registration
   - Plugin registered in plugin_metadata.py
   - Metadata includes all required fields
   - Plugin discoverable via discovery commands

✅ Phase 2: Build System Integration  
   - CMakeLists.txt updated with plugin include directories
   - Plugin builds with --plugins flag
   - Asset copying implemented if needed
   - Added to default builds if appropriate

✅ Phase 3: C++ Interface Implementation
   - All C++ wrapper functions implemented in pyhelios_interface.cpp
   - Proper exception handling with try/catch blocks
   - Parameter validation and type conversion
   - Library rebuilt with new functions available

✅ Phase 4: ctypes Wrapper Creation
   - Complete wrapper file created (UYourPluginWrapper.py)
   - All functions have errcheck callbacks (CRITICAL)
   - Mock mode implementation for development
   - Availability detection working correctly

✅ Phase 5: High-Level Python API
   - User-friendly class with context manager support
   - Method names match C++ API (upperCamelCase)
   - Comprehensive error handling and validation
   - Added to main module imports

✅ Phase 6: Asset Management
   - All runtime assets identified and documented
   - Asset copying implemented in build system
   - **Plugin added to plugin_asset_dirs in prepare_wheel.py for wheel distribution**
   - Assets available at expected locations
   - Working directory handling if needed

✅ Phase 7: Testing Integration
   - Test file named to match plugin exactly
   - Cross-platform and native-only test coverage
   - Integration tests with other components
   - Performance and edge case testing

✅ Phase 8: Documentation
   - Plugin documentation file created
   - Doxygen configuration updated
   - API examples tested and accurate
   - Troubleshooting guide complete
```

**Step 3: Quality Standards Verification**
The code reviewer must confirm the plugin meets PyHelios quality standards:

- **Fail-fast error handling**: No silent fallbacks or misleading return values
- **Cross-platform compatibility**: Works on Windows, macOS, and Linux
- **Consistent API patterns**: Follows established PyHelios conventions  
- **Resource management**: Proper cleanup prevents memory leaks
- **User experience**: Clear error messages with actionable solutions

**Step 4: Final Integration Test**
After code review approval, run the complete verification sequence:

```bash
# Clean build from scratch
build_scripts/build_helios --clean --plugins yourplugin

# Complete test suite (MANDATORY)
pytest

# Verify zero failures
# Success criteria: All tests pass, appropriate tests skipped, zero errors
```

### 9.3 Review Deliverables

The code reviewer should provide:

1. **Integration Completion Report**: Confirmation all 8 phases completed correctly
2. **Code Quality Assessment**: Production readiness evaluation
3. **Test Coverage Analysis**: Verification of comprehensive, rigorous testing
4. **Documentation Accuracy Report**: Line-by-line verification of all documentation
5. **Issue Identification**: Any problems requiring resolution before merge
6. **Approval Status**: Clear go/no-go decision for production deployment

### 9.4 Common Review Findings

Based on previous integrations, watch for these frequent issues:

**Implementation Issues**:
- Missing errcheck callbacks causing cryptic ctypes errors
- Incomplete parameter validation allowing invalid inputs
- Memory management issues causing segmentation faults
- Asset paths hardcoded instead of using proper working directories

**Testing Issues**:
- Tests that skip instead of actually testing functionality
- Mock tests that don't validate real behavior
- Missing edge case coverage
- Test isolation problems causing contamination between test modules

**Documentation Issues**:
- Code examples using wrong parameter names or types
- Outdated API method names not matching current C++ interface
- Installation instructions missing platform-specific requirements
- Error message examples that don't match actual behavior

### 9.5 Final Verification Protocol

**MANDATORY**: Before declaring integration complete, verify:

```bash
# 1. Clean build succeeds
build_scripts/build_helios --clean --plugins yourplugin

# 2. Plugin availability detection works
python -c "from pyhelios.plugins import print_plugin_status; print_plugin_status()"

# 3. Import works correctly
python -c "from pyhelios import YourPlugin; print('Import successful')"

# 4. Basic functionality test
python -c "
from pyhelios import Context, YourPlugin
with Context() as context:
    with YourPlugin(context) as plugin:
        print('Plugin creation successful')
"

# 5. Complete test suite passes
pytest

# 6. Documentation builds without errors  
cd docs && doxygen Doxyfile.python
```

**Success Criteria**: All commands complete without errors, warnings, or failures.

---

This guide provides comprehensive coverage of PyHelios plugin integration. Following these phases and requirements, **including the mandatory Phase 9 code review**, will ensure successful integration of new Helios plugins while maintaining PyHelios's high standards for cross-platform compatibility, error handling, and user experience.