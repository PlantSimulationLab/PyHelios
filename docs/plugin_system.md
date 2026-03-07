# Plugin System {#PluginSystem}

PyHelios uses a sophisticated plugin architecture with **21 available plugins** that can be selectively built and deployed based on your hardware and requirements.

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

## Plugin Selection Profiles

Use predefined profiles for common use cases:

```bash
# Default build (core functionality with visualization)
build_scripts/build_helios

# Specific plugin selection
build_scripts/build_helios --plugins weberpenntree,canopygenerator,visualizer

# Build with all plugins (includes GPU features if CUDA available)
build_scripts/build_helios

# Or build specific plugins
build_scripts/build_helios --plugins radiation

# Interactive selection (guided setup)
build_scripts/build_helios --interactive

# Exclude specific categories
build_scripts/build_helios --nogpu --novis
```

### Profile Contents

| Profile | Plugins Included | Use Case |
|---------|------------------|----------|
| **minimal** | weberpenntree, canopygenerator, solarposition | Basic functionality |
| **standard** | minimal + energybalance, photosynthesis, visualizer | General usage |
| **gpu-accelerated** | standard + radiation | High-performance computing |
| **research** | Most plugins | Academic research |
| **production** | Reliable subset | Production deployments |

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
from pyhelios.plugins import get_plugin_registry, print_plugin_status

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
from pyhelios.exceptions import HeliosPluginNotAvailableError

context = Context()

try:
    # RadiationModel automatically checks plugin availability
    with RadiationModel(context) as radiation:
        radiation.add_radiation_band("SW")
        radiation.run_band("SW")
        results = radiation.get_total_absorbed_flux()
except HeliosPluginNotAvailableError as e:
    print(f"Radiation modeling not available: {e}")
    # Error message includes specific instructions for enabling radiation
    # Fall back to alternative approaches
```

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
  selection_mode: "profile"
  profile: "standard"
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

# List all available profiles
python -m pyhelios.plugins profiles
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

```python
# Plugin wrapper example
from pyhelios.wrappers.base import BaseWrapper
from pyhelios.plugins.decorators import require_plugin

class MyPluginWrapper(BaseWrapper):
    @require_plugin('myplugin')
    def my_function(self, param):
        """Function that requires the myplugin plugin."""
        return self._call_native('my_function', param)

# High-level interface
class MyPlugin:
    def __init__(self, context):
        self.context = context
        self.wrapper = MyPluginWrapper()
    
    @require_plugin('myplugin')
    def do_something(self):
        """High-level interface to plugin functionality."""
        return self.wrapper.my_function()
```

## Plugin Dependencies

### System Dependencies

Plugins may require system libraries:

- **radiation**: Vulkan SDK (all platforms) or CUDA Toolkit + OptiX SDK (NVIDIA)
- **visualizer**: OpenGL, GLFW
- **lidar**: Point cloud libraries
- **photosynthesis**: Mathematical libraries

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
# Plugin cleanup
context.cleanup_plugins()  # Clean up plugin resources

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
# Check system dependencies
python -m pyhelios.plugins validate --system-check
```

### Plugin Error Messages

PyHelios provides detailed error messages with actionable solutions:

```
HeliosPluginNotAvailableError: The 'radiation' plugin is not available.

To enable GPU-accelerated radiation modeling:
1. Install Vulkan SDK (cross-platform: NVIDIA, AMD, Intel, Apple Silicon)
   OR CUDA Toolkit 11.0+ with OptiX (NVIDIA GPUs only)
2. Rebuild PyHelios: build_scripts/build_helios --plugins radiation
3. Ensure GPU with Vulkan 1.1+ support or NVIDIA GPU with compute capability 3.5+

Alternative: Use CPU-based radiation approximations with the 'energybalance' plugin.
```