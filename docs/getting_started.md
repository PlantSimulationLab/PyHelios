# Getting Started {#GettingStarted}

Welcome to PyHelios! This guide provides everything you need to get started with PyHelios, from installation to your first simulations.

## What is PyHelios?

PyHelios provides cross-platform Python bindings for the Helios 3D plant simulation library. It enables:

- **3D Plant Modeling**: Create realistic plant geometries using procedural generation
- **GPU-Accelerated Simulations**: High-performance radiation modeling with OptiX
- **Cross-Platform Support**: Works on Windows, macOS, and Linux
- **Plugin Architecture**: Extensible system with 21+ available plugins
- **Development Mode**: Mock mode for development without native libraries

## System Requirements

### Minimum Requirements
- Python 3.7+
- 4 GB RAM
- 1 GB disk space

### Recommended Requirements  
- Python 3.9+
- 8 GB RAM
- CUDA-compatible GPU (for radiation modeling)
- 5 GB disk space

## Installation {#Installation}

### Platform-Specific Installation

#### Windows

**Prerequisites:**
- Visual Studio 2019+ or Build Tools for Visual Studio
- Python 3.7+

```bash
# Clone repository
git clone --recursive https://github.com/PlantSimulationLab/PyHelios.git
cd PyHelios/

# Build native libraries (required)
./build_scripts/build_helios

# Install PyHelios
pip install -e .
```

#### macOS

**Prerequisites:**
- Xcode command line tools
- Python 3.7+

```bash
# Install Xcode command line tools
xcode-select --install

# Clone repository
git clone --recursive https://github.com/PlantSimulationLab/PyHelios.git
cd PyHelios/

# Install dependencies and build native libraries
source helios-core/utilities/dependencies.sh
./build_scripts/build_helios

# Install PyHelios
pip install -e .
```

#### Linux (Ubuntu/Debian)

**Prerequisites:**
- Build essentials
- CMake
- Python 3.7+

```bash
# Install prerequisites
sudo apt-get update
sudo apt-get install build-essential cmake python3-dev

# Clone repository
git clone --recursive https://github.com/PlantSimulationLab/PyHelios.git
cd PyHelios/

# Install dependencies and build native libraries
source helios-core/utilities/dependencies.sh
./build_scripts/build_helios

# Install PyHelios
pip install -e .
```

### Development Installation

For development work:

```bash
# Install with development dependencies
pip install -e .[dev]

# Verify installation with tests
pytest
```

### GPU Support

For GPU-accelerated radiation modeling:

```bash
# Install CUDA toolkit (varies by platform)
# Then build with all plugins (includes radiation with GPU support)
./build_scripts/build_helios

# Or build with only radiation plugin
./build_scripts/build_helios --plugins radiation
```

## Quick Start {#QuickStart}

### Your First PyHelios Script

Let's create a simple simulation with a patch and a tree:

```python
from pyhelios import Context, WeberPennTree
from pyhelios.types import *  # Import all vector types

# Create a simulation context
context = Context()

# Add a simple patch
center = vec3(0, 0, 0)
size = vec2(2, 2)
color = RGBcolor(0.3, 0.7, 0.3)  # Green

patch_uuid = context.addPatch(center=center, size=size, color=color)
print(f"Created patch with UUID: {patch_uuid}")

# Add a lemon tree
wpt = WeberPennTree(context)
tree_uuid = wpt.buildTree(WeberPennTree.WPTType.LEMON)
print(f"Created tree with UUID: {tree_uuid}")

# Check what we've created
print(f"Total primitives: {context.getPrimitiveCount()}")
print(f"All UUIDs: {context.getAllUUIDs()}")
```

### Basic Concepts

#### Context
The \ref pyhelios.Context.Context "Context" is your simulation environment. It manages all 3D geometry:

```python
from pyhelios import Context

context = Context()
# Context automatically detects available plugins
# and reports what's available for use
```

#### Data Types
PyHelios provides geometric data types for 3D operations:

```python
from pyhelios.types import *  # Import all vector types directly

# 3D vectors
position = vec3(1.0, 2.0, 3.0)
direction = vec3(0, 0, 1)  # Up vector

# 2D vectors for sizes
size = vec2(10.0, 5.0)  # width, height

# Colors
green = RGBcolor(0.2, 0.8, 0.2)
transparent_blue = RGBAcolor(0.2, 0.2, 0.8, 0.5)
```

**Vector Type Import Options:**

```python
# Option 1: Direct imports (recommended)
from pyhelios.types import *  # All types: vec3, RGBcolor, etc.
position = vec3(1, 2, 3)
color = RGBcolor(0.5, 0.5, 0.5)

# Alternative: Using the DataTypes module (less preferred)
from pyhelios import DataTypes
position = DataTypes.vec3(1, 2, 3)
color = DataTypes.RGBcolor(0.5, 0.5, 0.5)
```

### Tree Generation

Create procedural trees with the WeberPennTree plugin:

```python
from pyhelios import Context, WeberPennTree

context = Context()
wpt = WeberPennTree(context)

# Available tree types
tree_types = [
    WeberPennTree.WPTType.ALMOND,
    WeberPennTree.WPTType.APPLE, 
    WeberPennTree.WPTType.LEMON,
    WeberPennTree.WPTType.OLIVE,
    WeberPennTree.WPTType.AVOCADO
]

# Create different trees
for tree_type in tree_types:
    tree_id = wpt.buildTree(tree_type)
    print(f"Created {tree_type} tree: {tree_id}")
```

## Verification

Test your installation:

```python
from pyhelios import Context

# Create a basic context
context = Context()
print("PyHelios installed successfully!")

# Check available plugins
from pyhelios.plugins import print_plugin_status
print_plugin_status()
```

## Troubleshooting

### Common Issues

**Import Error**: 
- Verify Python version: `python --version`
- Check installation: `pip list | grep pyhelios`

**Missing Native Libraries**:
- Build libraries: `build_scripts/build_helios`
- Check plugin status: `python -m pyhelios.plugins status`

**Build Failures**:
- Windows: Ensure Visual Studio is installed
- macOS: Run `xcode-select --install`
- Linux: Install `build-essential cmake`

### Plugin Status

Check what plugins are available:

```bash
# Comprehensive plugin status
python -m pyhelios.plugins status

# System analysis and recommendations
python -m pyhelios.plugins discover

# Information about specific plugins
python -m pyhelios.plugins info radiation
```

## Next Steps

Once you have PyHelios installed and working:

1. **Explore Examples**: Check `docs/examples/` for more complex simulations
2. **Learn the API**: See the \ref UserGuide "User Guide" for comprehensive API documentation
3. **Plugin System**: Learn about available plugins in the \ref PluginSystem "Plugin System" guide
4. **Cross-Platform**: See \ref CrossPlatform "Cross-Platform Usage" for platform-specific tips

## Getting Help

- **Complete Documentation**: [https://plantsimulationlab.github.io/PyHelios/](https://plantsimulationlab.github.io/PyHelios/)
- **Examples**: Sample code in `docs/examples/`
- **Issues**: Report bugs on [GitHub](https://github.com/PlantSimulationLab/PyHelios/issues)
- **Helios Documentation**: [https://baileylab.ucdavis.edu/software/helios](https://baileylab.ucdavis.edu/software/helios)