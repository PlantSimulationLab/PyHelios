<br><br>

[![Build Wheels](https://github.com/PlantSimulationLab/PyHelios/actions/workflows/build-wheels.yml/badge.svg?event=push)](https://github.com/PlantSimulationLab/PyHelios/actions/workflows/build-wheels.yml) [![Test Linux](https://github.com/PlantSimulationLab/PyHelios/actions/workflows/pytest-linux.yml/badge.svg?branch=master)](https://github.com/PlantSimulationLab/PyHelios/actions/workflows/pytest-linux.yml) [![Test Windows](https://github.com/PlantSimulationLab/PyHelios/actions/workflows/pytest-windows.yml/badge.svg?branch=master)](https://github.com/PlantSimulationLab/PyHelios/actions/workflows/pytest-windows.yml) [![Test MacOS](https://github.com/PlantSimulationLab/PyHelios/actions/workflows/pytest-macos.yml/badge.svg?branch=master)](https://github.com/PlantSimulationLab/PyHelios/actions/workflows/pytest-macos.yml)
[![PyPI version](https://img.shields.io/pypi/v/pyhelios3d.svg)](https://pypi.org/project/pyhelios3d/)

<div align="center">
  <img src="https://raw.githubusercontent.com/PlantSimulationLab/PyHelios/master/docs/images/PyHelios_logo_whiteborder.png"  alt="" width="300" />
</div>

# Getting Started {#GettingStarted}

Cross-platform Python bindings for [Helios](https://github.com/PlantSimulationLab/Helios) 3D plant simulation library.

PyHelios provides a Python interface to the powerful Helios C++ library for 3D physical simulation of plant and environmental systems. It enables plant modeling, geometry manipulation, and biophysical simulations including GPU-accelerated radiation transfer, photosynthesis, and plant architecture modeling.

📖 **[Complete Documentation](https://plantsimulationlab.github.io/PyHelios/)**

⚠️Note that this is a work in progress. Not all Helios functionality has been implemented in PyHelios ⚠️

⚠️Help make PyHelios better by reporting issues: https://github.com/PlantSimulationLab/PyHelios/issues ⚠️

See the Helios C++ documentation for a more in-depth description of Helios: https://baileylab.ucdavis.edu/software/helios

## Quick Start

### Installation

**Easy Install (Recommended):**
```bash
pip install pyhelios3d
```

This installs pre-built PyHelios with platform-appropriate plugins:
- **macOS (Apple Silicon)**: All plugins including energybalance in CPU mode (radiation requires CUDA)
- **macOS (Intel)**: Pre-built wheels not available - please [build from source](#build-from-source)
- **Windows/Linux**: All plugins with optional GPU acceleration (automatic CPU fallback)

PyHelios automatically selects the best execution mode:
- **Plugins with GPU-only modes** (radiation): Require CUDA-capable GPU
- **Plugins with CPU/GPU modes** (energybalance): Work on all platforms, GPU acceleration optional
- **CPU-only plugins**: Work on all platforms without special hardware

> **Note for Intel Mac Users**: Due to GitHub Actions infrastructure limitations, pre-built wheels are only available for Apple Silicon Macs. Intel Mac users must build PyHelios from source following the [macOS build instructions](#macos) below.

### Build from Source {#build-from-source}

If you need to customize plugins or build from source:

#### Windows {#windows}

**Prerequisites:**
- Visual Studio 2019+ or Build Tools for Visual Studio
- Python 3.7+

```bash
# Clone repository
git clone --recursive https://github.com/PlantSimulationLab/PyHelios.git
cd PyHelios/

# Build native libraries (optional - pre-built binaries included)
./build_scripts/build_helios

# Install PyHelios dependencies
pip install -e .
```

#### macOS {#macos}

**Prerequisites:**
- Xcode command line tools
- Python 3.7+

```bash
# Install Xcode command line tools
xcode-select --install

# Clone repository
git clone --recursive https://github.com/PlantSimulationLab/PyHelios.git
cd PyHelios/

# Install c++ dependencies and build native libraries
source helios-core/utilities/dependencies.sh
./build_scripts/build_helios

# Install PyHelios dependencies
pip install -e .
```

#### Linux (Ubuntu/Debian) {#linux}

**Prerequisites:**
- Build essentials
- CMake
- Python 3.7+

```bash
# Clone repository
git clone --recursive https://github.com/PlantSimulationLab/PyHelios.git
cd PyHelios/

# Install c++ dependencies and build native libraries
source helios-core/utilities/dependencies.sh
./build_scripts/build_helios

# Install PyHelios dependencies
pip install -e .
```

### GPU Features Setup (Optional)

PyHelios plugins have three types of GPU support:

**GPU-Required Plugins** (need CUDA):
- **Radiation Model**: OptiX-powered ray tracing for light simulation
- **Aerial LiDAR**: GPU-accelerated LiDAR simulation

**GPU-Optional Plugins** (work with or without CUDA):
- **Energy Balance** *(v1.3.61+)*: Automatic mode selection - GPU (CUDA) → OpenMP (parallel CPU) → Serial CPU
  - CPU mode recommended for most workloads without GPU

**CPU-Only Plugins** (no GPU needed):
- All other plugins (PlantArchitecture, Photosynthesis, SolarPosition, etc.)

**For GPU Acceleration** (optional), ensure you have:
- NVIDIA GPU with CUDA support
- NVIDIA drivers installed
- CUDA Toolkit (version 11.8 or 12.x)

**Verification:**
```bash
nvidia-smi  # Should show GPU information
nvcc --version  # Should show CUDA compiler version
```

**Testing GPU Features:**
```python
from pyhelios import Context, RadiationModel, EnergyBalanceModel

context = Context()

# Test GPU-required plugin (radiation)
try:
    radiation = RadiationModel(context)
    print("GPU radiation modeling available!")
except RuntimeError as e:
    print(f"Radiation requires GPU: {e}")

# Test GPU-optional plugin (energybalance)
with EnergyBalanceModel(context) as energy:
    if energy.isGPUAccelerationEnabled():
        print("EnergyBalance using GPU acceleration")
    else:
        print("EnergyBalance using CPU mode (OpenMP or serial)")
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

| Section                                                                                  | Description |
|------------------------------------------------------------------------------------------|-------------|
| **[Getting Started](https://plantsimulationlab.github.io/PyHelios/Introduction.html)** | Installation, setup, and first steps |
| **[User Guide](https://plantsimulationlab.github.io/PyHelios/API.html)**           | Core concepts, API reference, and examples |
| **[Cross-Platform](https://plantsimulationlab.github.io/PyHelios/CrossPlatform.html)**   | Platform-specific usage and deployment |
| **[Plugin System](https://plantsimulationlab.github.io/PyHelios/PluginSystem.html)**     | Available plugins and configuration |

## Key Features

- **Cross-platform**: Windows, macOS, and Linux support
- **Plant modeling**: 20+ plant species models in the plant architecture plug-in
- **GPU acceleration**: OptiX-powered radiation simulation
- **3D visualization**: OpenGL-based real-time rendering

## Updating PyHelios

### PyPI Installation

If you installed via pip, simply upgrade to the latest version:

```bash
pip install --upgrade pyhelios3d
```

### Source Installation

If you built PyHelios from source, update with the latest changes:

```bash
# Update main repository and submodules recursively
git pull --recurse-submodules

# Alternative: Update main repo first, then submodules
git pull
git submodule update --init --recursive

# Rebuild native libraries after updates (recommended)
./build_scripts/build_helios --clean

# Reinstall PyHelios
pip install -e .
```

**Important**: Always use `--recurse-submodules` or manually update submodules when pulling updates, as PyHelios depends on the `helios-core` submodule for C++ functionality.

## Quick Commands

```bash
# Test installation (uses subprocess isolation for robust testing)
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