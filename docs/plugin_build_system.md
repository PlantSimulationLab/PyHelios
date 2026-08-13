# Building and Selecting Plug-ins {#PluginBuildSystem}

PyHelios uses a flexible plugin architecture with **21 available plugins** that can be selectively built and deployed based on your hardware and requirements. This page describes how to build, select, and detect plug-ins at runtime. For documentation of individual plug-ins, see \ref PluginSystem "Plugins".

## Plugin Categories

### Core Plugins (Always Available)
- **weberpenntree**: Procedural tree generation using Weber-Penn algorithms
- **canopygenerator**: Plant canopy generation for various species  
- **solarposition**: Solar position calculations and sun angle modeling

### GPU-Accelerated Plugins
- **radiation**: GPU-accelerated ray tracing and radiation modeling via Vulkan or OptiX backends
- **aeriallidar**: Aerial LiDAR simulation with GPU acceleration (CUDA)
- **collisiondetection**: Collision detection with optional GPU acceleration

### Physics Modeling Plugins
- **energybalance**: Plant energy balance calculations and thermal modeling
- **photosynthesis**: Photosynthesis modeling and carbon assimilation
- **leafoptics**: Leaf optical properties modeling (PROSPECT model)
- **stomatalconductance**: Stomatal conductance modeling and gas exchange
- **boundarylayerconductance**: Boundary layer conductance for heat/mass transfer
- **planthydraulics**: Plant hydraulic modeling and water transport

### Analysis and Simulation Plugins
- **lidar**: LiDAR simulation and point cloud processing
- **plantarchitecture**: Advanced plant structure and architecture modeling
- **voxelintersection**: Voxel intersection operations and spatial analysis
- **syntheticannotation**: Synthetic data annotation for machine learning
- **parameteroptimization**: Parameter optimization algorithms for model calibration

### Visualization and Tools
- **visualizer**: OpenGL-based 3D visualization and rendering
- **projectbuilder**: GUI project builder with ImGui interface

## Plugin Selection

A bare `build_scripts/build_helios` builds **every** available plugin. This is the
default, it is what the wheels ship, and it is what local testing should use.

```bash
# Default build: all available plugins (use this)
build_scripts/build_helios

# Clean rebuild, all plugins
build_scripts/build_helios --clean

# Explicit plugin selection
build_scripts/build_helios --plugins weberpenntree,canopygenerator,visualizer

# Exclude a single plugin
build_scripts/build_helios --exclude radiation

# Exclude whole categories
build_scripts/build_helios --nogpu --novis

# Interactive selection (guided setup)
build_scripts/build_helios --interactive
```

Only restrict the plugin set when you specifically need to isolate a plugin — for
example to reproduce a plugin-specific build failure. A plugin left out of the
build reports itself as unavailable at runtime, and the resulting
`PluginNotAvailable` errors are easy to misread as code bugs.

To make a selection persistent, set `explicit_plugins`, `excluded_plugins` or
`build_type` in `pyhelios_config.yaml` rather than passing flags each time. Use
`--config <file>` to point at a different configuration file, and
`--validate-config` to check one without building.

To see what is available on the current system:

```bash
build_scripts/build_helios --list-plugins      # PyHelios-integrated plugins
build_scripts/build_helios --list-all-plugins  # all helios-core plugins
build_scripts/build_helios --discover          # recommended config for this system
```

## Runtime Plugin Detection

PyHelios automatically detects available plugins at runtime:

```python
from pyhelios import Context

# Context reports available plugins during initialization
context = Context()
# Output: "PyHelios Context created with 8 available plugins: weberpenntree, canopygenerator, visualizer..."

# Check available plugins
available_plugins = context.get_available_plugins()
print(f"Available plugins: {available_plugins}")

# Check plugin availability
from pyhelios.plugins import print_plugin_status
from pyhelios.plugins.registry import get_plugin_registry

registry = get_plugin_registry()
if registry.is_plugin_available('radiation'):
    print("GPU radiation modeling available")
else:
    print("Radiation plugin not available - rebuild with GPU support (Vulkan or CUDA)")

# Get detailed plugin status
print_plugin_status()
```

## Plugin-Aware Usage

### Graceful Degradation

```python
from pyhelios import Context, RadiationModel
from pyhelios.types import vec2, vec3
from pyhelios.exceptions import HeliosPluginNotAvailableError

context = Context()
context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))

try:
    # RadiationModel automatically checks plugin availability
    with RadiationModel(context) as radiation:
        radiation.addRadiationBand("SW")
        radiation.addCollimatedRadiationSource()
        radiation.runBand("SW")
        results = radiation.getAbsorbedFlux("SW")
except HeliosPluginNotAvailableError as e:
    print(f"Radiation modeling not available: {e}")
    # Error message includes specific instructions for enabling radiation
    # Fall back to alternative approaches
```

The Context must contain geometry before querying results — `getAbsorbedFlux()`
raises `ValueError` on an empty Context rather than returning an empty list.

### Plugin Registry

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

## Custom Plugin Selection

### Explicit Plugin Selection

```bash
# Build with specific plugins
build_scripts/build_helios --plugins weberpenntree,canopygenerator,visualizer,energybalance

# Interactive selection (guided setup)
build_scripts/build_helios --interactive

# Exclude problematic plugins
build_scripts/build_helios --exclude radiation
```

### Configuration File Support

Create `pyhelios_config.yaml` for persistent preferences:

```yaml
plugins:
  selection_mode: "explicit"
  explicit_plugins:
    - weberpenntree
    - visualizer
  excluded_plugins:
    - radiation  # Exclude if no GPU available

build:
  build_type: "Release"
  verbose: false
```

### Discovery and Validation

```bash
# Discover optimal configuration for your system
python -m pyhelios.plugins discover

# Check plugin status and availability
python -m pyhelios.plugins status

# Get information about specific plugins
python -m pyhelios.plugins info radiation

# Validate plugin combinations
python -m pyhelios.plugins validate --plugins radiation,visualizer
```

## Plugin Development

### Adding New Plugins

For developers looking to add new plugins:

1. **C++ Plugin Development**: See [C++ Plugin Integration Guide](cpp_plugin_integration_guide.html)
2. **Python Wrapper**: Create ctypes wrapper in `pyhelios/wrappers/`
3. **High-Level Interface**: Add user-friendly class in `pyhelios/`
4. **Plugin Metadata**: Update `pyhelios/config/plugin_metadata.py`
5. **Testing**: Add tests with appropriate markers

### Plugin Architecture

Guard plugin-dependent methods with the `require_plugin` decorator from
`pyhelios.plugins.registry`. It raises `PluginNotAvailableError` with a rebuild
hint when the plugin is missing, instead of failing later inside ctypes:

```python
from pyhelios.plugins.registry import require_plugin, PluginNotAvailableError

class MyPlugin:
    def __init__(self, context):
        self.context = context

    @require_plugin('myplugin')
    def do_something(self):
        """High-level interface to plugin functionality."""
        ...
```

For an optional feature that should degrade rather than raise, use
`graceful_plugin_fallback` from the same module.

## Plugin Dependencies

### System Dependencies

Plugins may require system libraries:

- **radiation**: Vulkan loader (macOS/Linux; bundled on Windows) or CUDA Toolkit + OptiX (NVIDIA)
- **visualizer**: OpenGL (GLFW, GLEW and freetype are vendored and built from source)

Most plugins — including **lidar** and **photosynthesis** — declare no external
system dependencies and build from source with no extra setup. The authoritative
per-plugin list is `system_dependencies` in `pyhelios/config/plugin_metadata.py`,
which `python -m pyhelios.plugins info <name>` prints.

### Dependency Resolution

```python
from pyhelios.config.dependency_resolver import PluginDependencyResolver

resolver = PluginDependencyResolver()

# Resolve plugin dependencies
result = resolver.resolve_dependencies(['radiation', 'visualizer'])
if result.errors:
    for error in result.errors:
        print(f"Error: {error}")
else:
    print(f"Final plugins: {result.final_plugins}")
```

## Performance Considerations

### Plugin Loading

- Plugins are loaded dynamically at runtime
- Only active plugins consume memory
- GPU plugins initialize hardware on first use

### Memory Management

```python
# Context managers for automatic cleanup
with Context() as context:
    # Plugins automatically cleaned up on exit
    pass
```

## Troubleshooting

### Common Plugin Issues

**Plugin Not Found:**
```python
# Check if plugin is built
from pyhelios.plugins import print_plugin_status
print_plugin_status()

# Rebuild with plugin included
# build_scripts/build_helios --plugins plugin_name
```

**GPU Plugin Failures:**
```bash
# Check Vulkan availability
vulkaninfo

# Or check CUDA installation (NVIDIA GPUs)
nvidia-smi
```

**Dependency Issues:**
```bash
# Validate a plugin combination and report unmet dependencies
python -m pyhelios.plugins validate --plugins radiation,visualizer
```

### Plugin Error Messages

PyHelios provides detailed error messages with actionable solutions:

```
HeliosPluginNotAvailableError: The 'radiation' plugin is not available.

To enable GPU-accelerated radiation modeling:
1. Install Vulkan loader (macOS/Linux) or CUDA 12.0+ (NVIDIA driver >= 560)
   Windows: No external Vulkan dependencies needed (headers + glslang bundled)
2. Rebuild PyHelios: build_scripts/build_helios --plugins radiation
3. Backend auto-detected at runtime: OptiX 8 -> OptiX 6 -> Vulkan

Alternative: Use CPU-based radiation approximations with the 'energybalance' plugin.
```
