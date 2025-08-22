# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Sub-Agents

- Make sure to familiarize yourself with the available sub-agents (@.claude/agents/) and use them efficiently:
  - context-gatherer: Expert code archaeologist and information synthesizer specializing in rapidly discovering, analyzing, and summarizing relevant context for development tasks.
  - research-specialist: Expert technical web researcher specializing in finding and evaluating open source codebases, scientific literature, and algorithmic implementation.
  - helios-cpp-expert: Specialist with deep knowledge of the Helios plant simulation software's native C++ codebase.
  - code-architect: Analyzes existing codebases holistically and create comprehensive implementation plans that consider architectural integrity, maintainability, and scalability.
  - debug-specialist: Expert software debugging specialist with deep C++ and cmake expertise.
  - code-reviewer: Code reviewer with deep knowledge of software engineering best practices, security principles, and maintainable code design.
  - test-coverage-maximizer: Writes tests that achieve maximum code coverage while ensuring robust functional testing that catches real bugs and edge cases.

## Virtual Environment

For development, create a virtual environment using your preferred method (venv, conda, etc.):

```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Unix/macOS
# or venv\Scripts\activate  # On Windows

# Using conda
conda create -n pyhelios python=3.9
conda activate pyhelios
```

## Project Overview

PyHelios provides cross-platform Python bindings for the Helios plant simulation software, offering a high-level interface for 3D plant modeling and simulation. The library uses ctypes with dynamic platform detection to interface with native C++ libraries and plugins.

**Cross-Platform Support**: 
- **Windows**: Full native support with pre-built DLLs
- **macOS/Linux**: Native support via build-from-source
- **Development Mode**: Mock mode for development on any platform without native libraries

## Development Commands

### Installation
```bash
pip install -e .
```

### Building Native Libraries

PyHelios now supports flexible plugin selection for customized builds based on your hardware and use case requirements.

#### Clean Helios-Style Project Structure

Following standard Helios C++ project conventions:
- **pyhelios_build/** - Source files (CMakeLists.txt, main.cpp, etc.)
- **pyhelios_build/build/** - All generated build artifacts including shared libraries for Python import

#### Plugin Selection Options

```bash
# Clean build from fresh state (recommended for troubleshooting)
build_scripts/build_helios --clean --plugins visualizer

# Basic builds
build_scripts/build_helios                           # Default build (non-GPU, non-vis plugins)
build_scripts/build_helios --nogpu                   # Exclude GPU plugins
build_scripts/build_helios --novis                   # Exclude visualization plugins

# Explicit plugin selection
build_scripts/build_helios --plugins weberpenntree,canopygenerator,visualizer

# Interactive selection
build_scripts/build_helios --interactive

# Exclude specific plugins
build_scripts/build_helios --exclude radiation

# Build with custom options
build_scripts/build_helios --cmake-args -DCMAKE_BUILD_TYPE=Debug --verbose

# Debug builds
build_scripts/build_helios --clean --plugins visualizer --buildmode debug
```

#### Plugin Discovery and Status

```bash
# Check plugin status and availability
python -m pyhelios.plugins status

# Discover optimal configuration for your system
python -m pyhelios.plugins discover

# Get information about specific plugins
python -m pyhelios.plugins info radiation

# Validate plugin configuration
python -m pyhelios.plugins validate --plugins radiation,visualizer

# List all available profiles
python -m pyhelios.plugins profiles
```

#### Configuration File Support

Create `pyhelios_config.yaml` to specify default plugin selection:

```yaml
plugins:
  profile: "standard"
  excluded_plugins:
    - radiation  # Exclude if no GPU available

build:
  build_type: "Release"
  verbose: false
```

### Running Examples
```bash
python docs/examples/context_sample.py
python docs/examples/wpt_sample.py
python docs/examples/visualization_sample.py
```

### Platform Status
```bash
# Check current platform and library status
python -c "from pyhelios.plugins import print_plugin_status; print_plugin_status()"
```

## Style
- Don't add comments that are specific to a given debugging session. For example: "We don't need this anymore, reverting back to old behavior", "Remove Phase 2 code for Phase 3", etc. These types of comments don't make sense outside of a given session.

## Architecture Overview

### Core Components

- **Context** (`pyhelios/Context.py`): Central simulation environment that manages 3D primitives (patches, triangles, voxels). Provides methods for adding geometry, querying properties, and managing object collections.

- **WeberPennTree** (`pyhelios/WeberPennTree.py`): Plant modeling plugin for generating procedural trees. Supports multiple tree types (ALMOND, APPLE, AVOCADO, LEMON, OLIVE, etc.) with configurable parameters for branch recursion, segment resolution, and leaf subdivisions.

- **DataTypes** (`pyhelios/wrappers/DataTypes.py`): Core geometric data structures using ctypes for C++ interop:
  - vec2/vec3/vec4: Vector types for positions, sizes, directions
  - RGBcolor/RGBAcolor: Color representations  
  - SphericalCoord: Spherical coordinate system
  - int2/int3/int4: Integer vector types

### Flexible Plugin System

PyHelios uses a sophisticated plugin-based architecture supporting **21 available plugins** with flexible selection and runtime detection:

#### Plugin Categories

**Core Plugins (Always Available):**
- **weberpenntree**: Procedural tree generation using Weber-Penn algorithms
- **canopygenerator**: Plant canopy generation for various species  
- **solarposition**: Solar position calculations and sun angle modeling

**GPU-Accelerated Plugins (Require CUDA):**
- **radiation**: OptiX-accelerated ray tracing and radiation modeling
- **aeriallidar**: Aerial LiDAR simulation with GPU acceleration
- **collisiondetection**: Collision detection with optional GPU acceleration

**Physics Modeling Plugins:**
- **energybalance**: Plant energy balance calculations and thermal modeling
- **photosynthesis**: Photosynthesis modeling and carbon assimilation
- **leafoptics**: Leaf optical properties modeling (PROSPECT model)
- **stomatalconductance**: Stomatal conductance modeling and gas exchange
- **boundarylayerconductance**: Boundary layer conductance for heat/mass transfer
- **planthydraulics**: Plant hydraulic modeling and water transport

**Analysis and Simulation Plugins:**
- **lidar**: LiDAR simulation and point cloud processing
- **plantarchitecture**: Advanced plant structure and architecture modeling
- **voxelintersection**: Voxel intersection operations and spatial analysis
- **syntheticannotation**: Synthetic data annotation for machine learning
- **parameteroptimization**: Parameter optimization algorithms for model calibration

**Visualization and Tools:**
- **visualizer**: OpenGL-based 3D visualization and rendering
- **projectbuilder**: GUI project builder with ImGui interface

#### Plugin Selection Profiles

The system includes predefined profiles for common use cases:

- **minimal**: Core functionality only (weberpenntree, canopygenerator, solarposition)
- **standard**: Standard features with visualization (adds visualizer, energybalance, photosynthesis)
- **gpu-accelerated**: High-performance GPU features (adds radiation for ray tracing)
- **research**: Comprehensive research suite (includes most plugins for academic use)
- **production**: Production-ready features (reliable, well-tested plugins)
- **visualization**: Focus on rendering and visualization capabilities
- **sensing**: Remote sensing and LiDAR simulation capabilities  
- **physics**: Comprehensive physics modeling and simulation
- **development**: Minimal set for PyHelios development and testing

### Cross-Platform Library Loading

PyHelios includes a sophisticated cross-platform library loader (`pyhelios/plugins/loader.py`):

**Platform Support:**
- **Windows**: Uses `ctypes.WinDLL` with `.dll` files
- **macOS**: Uses `ctypes.CDLL` with `.dylib` files  
- **Linux**: Uses `ctypes.CDLL` with `.so` files

**Dynamic Loading Features:**
- Automatic platform detection and appropriate ctypes loader selection
- Fallback to mock mode when native libraries are unavailable
- Comprehensive error handling and informative error messages
- Library validation to ensure core functions are available
- **Runtime plugin detection**: Automatically detects which plugins are compiled into the library
- **Plugin capability discovery**: Provides detailed information about available plugin features
- Dependency checking for optional components (e.g., OptiX for GPU acceleration)
- **Graceful degradation**: Clear error messages when plugins are unavailable with actionable solutions

**Mock Mode:**
- Provides full API compatibility without requiring native libraries
- Enables development and testing on any platform
- Raises informative `RuntimeError` with clear instructions when mock functions are called
- Seamlessly integrates with the testing framework

### High-Level Plugin-Aware Classes

PyHelios provides high-level classes with automatic plugin detection and graceful error handling:

- **Context** (`pyhelios/Context.py`): Enhanced with plugin status reporting and availability checking
- **WeberPennTree** (`pyhelios/WeberPennTree.py`): Automatically detects weberpenntree plugin availability  
- **RadiationModel** (`pyhelios/RadiationModel.py`): High-level interface for radiation modeling with comprehensive error handling and alternative suggestions

### Plugin Registry and Management

- **PluginRegistry** (`pyhelios/plugins/registry.py`): Centralized plugin management with decorators for graceful fallbacks
- **Plugin Detection** (`pyhelios/plugins/loader.py`): Runtime detection of available plugin capabilities
- **Configuration Management** (`pyhelios/config/config_manager.py`): YAML-based configuration with validation

### Wrapper Layer

The `pyhelios/wrappers/` directory contains ctypes wrappers that interface with native plugins:
- `UContextWrapper`: Context operations
- `UWeberPennTreeWrapper`: Tree generation  
- `URadiationModelWrapper`: Radiation modeling (with availability detection)
- `UGlobalWrapper`: Global configuration
- `ULoggerWrapper`: Logging functionality

## Key Usage Patterns

### Basic Geometry Creation
```python
from pyhelios import Context
from pyhelios.types import *  # Convenient import for all vector types

context = Context()
center = vec3(2, 3, 4)
size = vec2(1, 1)
color = RGBcolor(0.25, 0.25, 0.25)
patch_uuid = context.addPatch(center=center, size=size, color=color)
```

### Vector Type Import Options

PyHelios provides two ways to import vector types:

**Option 1: Direct imports (recommended)**
```python
from pyhelios.types import *  # All vector types: vec3, RGBcolor, etc.
position = vec3(1, 2, 3)
color = RGBcolor(0.5, 0.5, 0.5)
```

**Option 2: Explicit DataTypes module**
```python
from pyhelios import DataTypes
position = DataTypes.vec3(1, 2, 3)
color = DataTypes.RGBcolor(0.5, 0.5, 0.5)
```

The star import (`from pyhelios.types import *`) includes all vector types: `vec2`, `vec3`, `vec4`, `int2`, `int3`, `int4`, `RGBcolor`, `RGBAcolor`, `SphericalCoord`, and factory functions like `make_vec3`.

### Tree Generation
```python
from pyhelios import Context, WeberPennTree, WPTType

context = Context()
wpt = WeberPennTree(context)
tree_id = wpt.buildTree(WPTType.LEMON)
```

#### Radiation Modeling with Graceful Handling
```python
from pyhelios import Context, RadiationModel

context = Context()

# RadiationModel automatically checks plugin availability
with RadiationModel(context) as radiation:
    radiation.add_radiation_band("SW")
    radiation.add_collimated_radiation_source()
    radiation.run_band("SW")
    results = radiation.get_total_absorbed_flux()
```

#### Plugin System Discovery
```python
from pyhelios.plugins.registry import get_plugin_registry

registry = get_plugin_registry()

# Get plugin capabilities
capabilities = registry.get_plugin_capabilities()
for plugin, info in capabilities.items():
    print(f"{plugin}: {info['description']}")
    if info['gpu_required']:
        print("  Requires GPU support")

# Check for missing plugins
missing = registry.get_missing_plugins(['radiation', 'visualizer'])
if missing:
    print(f"Missing plugins: {missing}")
```

### Context Managers
Both Context and WeberPennTree support context manager protocol for proper resource cleanup.

## Helios Core Integration

PyHelios interfaces with the main Helios C++ library located in `helios-core/`. The core Helios library provides:

### Core Architecture (`helios-core/core/`)
- **Context.h/cpp**: Central 3D simulation environment with primitive management
- **Global.h/cpp**: Global configuration and utility functions  
- **Vector types**: Comprehensive 3D vector math operations

### Plugin System (`helios-core/plugins/`)
Key plugins that PyHelios may interface with:
- **weberpenntree/**: Procedural tree generation using Weber-Penn algorithms
- **canopygenerator/**: Plant canopy generation for various species  
- **radiation/**: OptiX-accelerated ray tracing for radiation modeling
- **plantarchitecture/**: Advanced plant structure modeling
- **visualizer/**: OpenGL-based 3D visualization
- **lidar/**: LiDAR simulation and point cloud processing
- **energybalance/**: Plant energy balance calculations
- **photosynthesis/**: Photosynthesis modeling

### Accessing Helios Documentation
- Complete documentation: `helios-core/doc/html/index.html` 
- Also available online: https://baileylab.ucdavis.edu/software/helios
- Plugin-specific documentation in each `plugins/*/doc/` directory

### C++/Python Interface Notes
- PyHelios uses ctypes to interface with Helios C++ DLLs
- The `pyhelios/wrappers/` directory contains ctypes wrapper functions
- Native pointers accessible via `get_native_ptr()` for direct Helios API calls
- Helios uses UUID-based object tracking system

## Testing Framework

PyHelios uses pytest for comprehensive testing with support for both unit and integration tests.

### Running Tests

```bash
# Install development dependencies  
pip install -e .[dev]

# Run all tests (works on all platforms - automatically handles mock mode)
pytest

# Run specific test categories
pytest -m unit             # Unit tests (work with mocks)
pytest -m integration      # Integration tests (require native libraries)
pytest -m cross_platform   # Tests that work on all platforms
pytest -m native_only      # Tests requiring native libraries only
pytest -m mock_mode        # Tests specifically for mock mode functionality  
pytest -m slow            # Long-running tests

# Run platform-specific tests
pytest -m windows_only     # Windows-specific tests
pytest -m macos_only       # macOS-specific tests  
pytest -m linux_only       # Linux-specific tests

# Run with coverage (if pytest-cov installed)
pytest --cov=pyhelios --cov-report=html

# Run specific test files
pytest tests/test_datatypes.py
pytest tests/test_cross_platform.py
pytest tests/test_context.py -v
```

### Test Structure

- **Unit Tests**: Test individual components without DLL dependencies (using mocks)
- **Integration Tests**: Test PyHelios + Helios C++ library interaction 
- **Cross-Platform Tests**: Tests that work on all platforms using mock mode when needed
- **Native-Only Tests**: Tests requiring actual native Helios libraries
- **Mock Mode Tests**: Tests specifically for mock mode functionality
- **Performance Tests**: Regression testing for performance-critical operations

### Test Markers

**Core Test Categories:**
- `@pytest.mark.unit`: Pure unit tests (work with mocks)
- `@pytest.mark.integration`: Integration tests with Helios core
- `@pytest.mark.cross_platform`: Tests that work on all platforms
- `@pytest.mark.native_only`: Tests requiring native Helios library
- `@pytest.mark.mock_mode`: Tests specifically for mock mode functionality


**Performance:**
- `@pytest.mark.slow`: Long-running tests

**Platform-Specific:**
- `@pytest.mark.windows_only`: Windows-specific tests
- `@pytest.mark.macos_only`: macOS-specific tests  
- `@pytest.mark.linux_only`: Linux-specific tests

### Key Test Files

- `test_datatypes.py`: DataTypes module (Vec2, Vec3, RGBcolor, etc.) with floating-point precision handling
- `test_context.py`: Context class and primitive management
- `test_weberpenntree.py`: WeberPennTree functionality and tree generation
- `test_cross_platform.py`: Cross-platform functionality, mock mode, and library loading
- `test_integration.py`: End-to-end workflows and complex scenarios
- `conftest.py`: Shared fixtures, platform detection, and test configuration
- `test_utils.py`: Testing utilities, validators, and helper classes

### Test Development Guidelines

**Cross-Platform Testing:**
- **Cross-platform tests** work on all platforms using mock mode when needed
- **Native tests** require platform-specific native libraries 
- Use `@pytest.mark.cross_platform` for tests that work everywhere
- Use `@pytest.mark.native_only` for tests requiring native functionality
- All tests gracefully handle missing libraries with informative skip messages

**Mock Mode Development:**
- Mock mode tests validate API compatibility without requiring native libraries
- Mock mode allows development and testing on any platform without building native libraries
- Tests automatically skip when native libraries are unavailable with informative messages

**Test Configuration:**
- `pytest.ini` configures test markers and excludes `helios-core/` from test collection
- `conftest.py` provides shared fixtures and platform detection utilities
- Floating-point comparisons use `pytest.approx()` for cross-platform reliability

**Test Execution:**
- All tests run successfully on any platform - failing tests are automatically fixed
- Tests provide clear output showing passed/skipped/failed counts  
- Zero warnings and errors in final test execution

**GitHub CI/CD Integration:**
- Comprehensive CI/CD workflows test PyHelios across all platforms
- Quick tests (`test-quick.yml`) for fast development feedback
- Matrix tests (`test-matrix.yml`) for comprehensive cross-platform validation
- Native library tests (`test-native.yml`) attempt to build and test with actual Helios libraries
- All workflows handle mock mode gracefully and provide meaningful test results

## Development Notes

**Cross-Platform Development:**
- **Full platform support**: PyHelios works seamlessly on Windows, macOS, and Linux
- **Mock mode**: Enables development and testing without native libraries on any platform  
- **Native libraries**: Build using `python build_scripts/build_helios.py` for full functionality
- **Platform detection**: Use `from pyhelios.plugins import get_plugin_info` to check current status and library availability

**Testing and Development Workflow:**
- **Comprehensive test suite**: 86 passing tests, 60 properly skipped, zero failures/errors/warnings
- **Cross-platform testing**: Run `pytest` on any platform - tests automatically adapt to available libraries
- **Mock mode development**: Develop and test PyHelios functionality without requiring native library compilation
- **Test categories**: Use `pytest -m cross_platform` for platform-independent tests, `pytest -m native_only` for native library tests

**Architecture and Integration:**
- **UUID-based tracking**: All geometric operations return UUIDs for object tracking
- **Context state management**: The Context manages geometry state with dirty/clean marking
- **Tree generation**: Allows customization of branch recursion levels, segment resolution, and leaf subdivisions
- **Native pointer access**: Available via `get_native_ptr()` methods for advanced operations
- **Helios core integration**: When debugging PyHelios issues, check corresponding C++ implementation in `helios-core/`

**Build and Configuration:**
- **Dynamic library loading**: Automatic platform detection and library loading with fallback to mock mode
- **Build system**: Use build scripts in `build_scripts/` to compile native libraries for your platform
- **Test configuration**: `pytest.ini` and `conftest.py` provide comprehensive test configuration
- **Error handling**: Informative error messages guide users when native libraries are unavailable

**Continuous Integration:**
- **GitHub Actions**: Comprehensive CI/CD workflows in `.github/workflows/`
- **Multi-platform testing**: Automated testing on Ubuntu, Windows, and macOS
- **Python version matrix**: Tests across Python 3.8-3.12
- **Mock mode validation**: All platforms test PyHelios functionality without native dependencies
- **Native library testing**: Best-effort compilation and testing with actual Helios libraries
- **Quick feedback**: Fast workflows for development branches provide rapid feedback

## Error Handling and Fallback Policy

**CRITICAL: PyHelios follows a fail-fast philosophy - never implement silent fallbacks that hide issues from users.** NEVER return fake values (0.0, empty lists, fake IDs), silently catch and ignore exceptions, or continue with misleading fallback functionality when core features fail. Instead, always raise explicit `RuntimeError` or `NotImplementedError` exceptions with clear, actionable error messages that explain what failed, why it failed, and how to fix it. The only acceptable fallbacks are explicit opt-in development modes, documented graceful degradation where users are informed, and safe no-ops like cleaning up `None` resources. **The Golden Rule: If something doesn't work, make it obvious** - users should never wonder why they got unexpected results, but should immediately see clear error messages with specific system requirements and actionable solutions.

## Plugin Integration Guidelines

### When Working on Plugin Integration

PyHelios has successfully integrated 3 major Helios C++ plugins (radiation, visualizer, WeberPennTree) through a sophisticated 8-phase integration process. When working on plugin integration tasks:

#### Use the Right Sub-Agent

- **For complete plugin integration projects**: Use `context-gatherer` to understand existing patterns, then `code-architect` for planning the integration
- **For C++ interface and build issues**: Use `helios-cpp-expert` for deep Helios core knowledge and CMake expertise  
- **For Python wrapper creation**: Use `code-reviewer` to ensure ctypes patterns follow best practices
- **For comprehensive testing**: Use `test-coverage-maximizer` to create robust cross-platform tests
- **For debugging integration issues**: Use `debug-specialist` for systematic troubleshooting

#### Critical Integration Requirements

**ALWAYS follow the 8-phase integration process:**

1. **Plugin Metadata Registration** - Add to `pyhelios/config/plugin_metadata.py` and relevant profiles
2. **Build System Integration** - CMake and flexible plugin selection system
3. **C++ Interface Implementation** - Add wrapper functions to `pyhelios_build/pyhelios_interface.cpp`
4. **ctypes Wrapper Creation** - Python-to-C++ interface in `pyhelios/wrappers/`
5. **High-Level Python API** - User-friendly classes with context managers and error handling
6. **Asset Management** - Copy runtime assets (shaders, textures, configs) to expected locations
7. **Testing Integration** - Cross-platform tests with proper pytest markers
8. **Documentation** - API docs and usage examples

#### Essential Integration Patterns

**Asset Management (Critical)**:
Many plugins require runtime assets that must be copied to specific locations where C++ code expects them. ALWAYS check for and implement asset copying in the build system.

**Exception Handling (Mandatory)**:
- All C++ interface functions MUST use try/catch blocks with proper error codes
- Use errcheck callbacks for automatic exception translation
- Never allow C++ exceptions to cross into Python

**Plugin Availability Detection**:
- Check function availability using try/except around ctypes prototypes
- Provide actionable error messages with rebuild instructions
- Implement mock mode for development when plugins unavailable

**Parameter Mapping Precision**:
- Check actual C++ constructor signatures - don't assume parameter order or meaning
- Map parameters semantically, not just positionally
- Test different parameter combinations

#### Documentation Requirements

For plugin integration tasks, ALWAYS:
- Reference the comprehensive [Plugin Integration Guide](docs/plugin_integration_guide.md) for step-by-step workflow
- Use the [C++ Plugin Integration Guide](docs/cpp_plugin_integration_guide.md) for technical C++ interface details
- Document all new plugin APIs with examples and error handling guidance
- Include troubleshooting sections for common integration issues

#### Testing Requirements

All plugin integrations MUST include:
- **Cross-platform tests** (`@pytest.mark.cross_platform`) that work with mock mode
- **Native-only tests** (`@pytest.mark.native_only`) that require actual plugin functionality
- **Plugin metadata tests** to verify registration and profiles
- **Error handling tests** to verify proper exception translation
- **Asset management tests** to verify runtime dependencies are available

#### Build System Requirements

When integrating plugins:
- Use the flexible plugin selection system - no manual CMake modifications needed for basic plugins
- Implement asset copying for runtime dependencies (shaders, textures, fonts, configs)
- Test build system with `--clean` builds and different plugin combinations
- Verify cross-platform symbol export and library loading
- Validate that built libraries can be loaded by ctypes on all platforms

#### Quality Standards

Maintain PyHelios's high standards:
- **Fail-fast error handling** - never silent fallbacks or fake return values
- **Cross-platform compatibility** - test on Windows, macOS, and Linux
- **Comprehensive documentation** - include examples, error scenarios, and troubleshooting
- **Robust testing** - cover both mock mode and native library scenarios
- **Performance considerations** - document any performance characteristics or limitations

#### Critical Lessons from Compound Geometry Integration

**Memory Management**: Always implement safe context cleanup to prevent segmentation faults:
```python
def __exit__(self, exc_type, exc_value, traceback):
    if self.context is not None:
        context_wrapper.destroyContext(self.context)
        self.context = None  # Prevent double deletion - CRITICAL
```

**ctypes Type Equality**: Never rely on `==` for ctypes structures - use field comparison:
```python
# WRONG: color != RGBcolor(1, 1, 1) may fail even when values are equal
# RIGHT: field-based comparison  
if color and not (color.r == 1.0 and color.g == 1.0 and color.b == 1.0):
```

**Parameter Array Mapping**: Check actual array sizes returned by ctypes structures:
```python
# SphericalCoord.to_list() returns 4 elements [radius, elevation, zenith, azimuth]
# But C++ interface expects 3 elements [radius, elevation, azimuth] 
rotation_list = [rotation.radius, rotation.elevation, rotation.azimuth]
```

**Vector Pre-allocation**: Always pre-allocate vectors in C++ for efficiency:
```cpp
std::vector<helios::vec3> nodes_vec;
nodes_vec.reserve(node_count);  // Pre-allocate - CRITICAL for performance
```

**Thread-Local Static Vectors**: Use thread_local for static return vectors:
```cpp
static thread_local std::vector<unsigned int> static_result;  // Not just static
```