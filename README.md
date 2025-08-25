<br><br>

[![Test Linux](https://github.com/PlantSimulationLab/PyHelios/actions/workflows/pytest-linux.yml/badge.svg?branch=master)](https://github.com/PlantSimulationLab/PyHelios/actions/workflows/pytest-linux.yml) [![Test Windows](https://github.com/PlantSimulationLab/PyHelios/actions/workflows/pytest-windows.yml/badge.svg?branch=master)](https://github.com/PlantSimulationLab/PyHelios/actions/workflows/pytest-windows.yml) [![Test MacOS](https://github.com/PlantSimulationLab/PyHelios/actions/workflows/pytest-macos.yml/badge.svg?branch=master)](https://github.com/PlantSimulationLab/PyHelios/actions/workflows/pytest-macos.yml)

<div align="center">
  <img src="https://raw.githubusercontent.com/PlantSimulationLab/PyHelios/master/docs/images/PyHelios_logo_whiteborder.png"  alt="" width="300" />
</div>

# PyHelios

Cross-platform Python bindings for [Helios](https://github.com/PlantSimulationLab/Helios) 3D plant simulation library.

PyHelios provides a Python interface to the powerful Helios C++ library for 3D physical simulation of plant and environmental systems. It enables plant modeling, geometry manipulation, and biophysical simulations including GPU-accelerated radiation transfer, photosynthesis, and plant architecture modeling.

📖 **[Complete Documentation](https://plantsimulationlab.github.io/PyHelios/)**

⚠️Note that this is a work in progress. Not all Helios functionality has been implemented in PyHelios ⚠️

See the Helios C++ documentation for a more in-depth description of Helios: https://baileylab.ucdavis.edu/software/helios

## Quick Start

### Installation

#### Windows

**Prerequisites:**
- Visual Studio 2019+ or Build Tools for Visual Studio
- Python 3.7+

```bash
# Clone repository
git clone --recursive https://github.com/PlantSimulationLab/PyHelios.git
cd PyHelios/

# Build native libraries (optional - pre-built binaries included)
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
# Clone repository
git clone --recursive https://github.com/PlantSimulationLab/PyHelios.git
cd PyHelios/

# Install dependencies and build native libraries
source helios-core/utilities/dependencies.sh
./build_scripts/build_helios

# Install PyHelios
pip install -e .
```

### First Example

```python
from pyhelios import Context
from pyhelios.types import *

# Create simulation context
context = Context()

# Add a patch primitive
center = vec3(2, 3, 4)
size = vec2(1, 1)
color = RGBcolor(0.25, 0.25, 0.25)
patch_uuid = context.addPatch(center=center, size=size, color=color)

print(f"Created patch: {patch_uuid}")
```

## Documentation

| Section | Description |
|---------|-------------|
| **[Getting Started](https://plantsimulationlab.github.io/PyHelios/getting_started.html)** | Installation, setup, and first steps |
| **[User Guide](https://plantsimulationlab.github.io/PyHelios/user_guide.html)** | Core concepts, API reference, and examples |
| **[Cross-Platform](https://plantsimulationlab.github.io/PyHelios/cross_platform.html)** | Platform-specific usage and deployment |
| **[Plugin System](https://plantsimulationlab.github.io/PyHelios/plugin_system.html)** | Available plugins and configuration |

## Key Features

- **Cross-platform**: Windows, macOS, and Linux support
- **Plant modeling**: WeberPennTree procedural generation 
- **GPU acceleration**: OptiX-powered radiation simulation
- **3D visualization**: OpenGL-based real-time rendering
- **Flexible plugins**: Currently 4 plug-ins implemented
- **Development mode**: Mock mode for development without native libraries

## Quick Commands

```bash
# Test installation
pytest

# Check plugin status  
python -m pyhelios.plugins status

# Interactive plugin selection
./build_scripts/build_helios --interactive
```

## Support

- **Documentation**: https://plantsimulationlab.github.io/PyHelios/
- **Issues**: [GitHub Issues](https://github.com/PlantSimulationLab/PyHelios/issues)
- **Helios C++ Docs**: https://baileylab.ucdavis.edu/software/helios

---

**Note**: This project is in active development. The API may change quickly - see `docs/CHANGELOG.md` for updates.