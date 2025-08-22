<br><br>

[![Test Linux](https://github.com/PlantSimulationLab/PyHelios/actions/workflows/pytest-linux.yml/badge.svg?branch=master)](https://github.com/PlantSimulationLab/PyHelios/actions/workflows/pytest-linux.yml) [![Test Windows](https://github.com/PlantSimulationLab/PyHelios/actions/workflows/pytest-windows.yml/badge.svg?branch=master)](https://github.com/PlantSimulationLab/PyHelios/actions/workflows/pytest-windows.yml) [![Test MacOS](https://github.com/PlantSimulationLab/PyHelios/actions/workflows/pytest-macos.yml/badge.svg?branch=master)](https://github.com/PlantSimulationLab/PyHelios/actions/workflows/pytest-macos.yml) [![Docs](https://github.com/PlantSimulationLab/PyHelios/actions/workflows/docs.yml/badge.svg?branch=master)](https://github.com/PlantSimulationLab/PyHelios/actions/workflows/docs.yml)

<div align="center">
  <img src="docs/images/PyHelios_logo_whiteborder.png"  alt="" width="300" />
</div>

# PyHelios

Cross-platform Python bindings for [Helios](https://github.com/PlantSimulationLab/Helios) 3D plant simulation library.

PyHelios provides a Python interface to the powerful Helios C++ library for 3D physical simulation of plant and environmental systems. It enables plant modeling, geometry manipulation, and biophysical simulations including GPU-accelerated radiation transfer, photosynthesis, and plant architecture modeling.

For complete documentation of PyHelios, please visit: https://plantsimulationlab.github.io/PyHelios/

**Important**
This project is in the early stages of development. The Python API only has a limited subset of the Helios C++ functionality. 
The code is likely to change quickly, with backward compatability not being maintained. It is recommended when you update your code to read the changelog in `docs/CHANGELOG.md`.

For complete documentation of the Helios C++ library, please visit https://baileylab.ucdavis.edu/software/helios

## Platform Support

PyHelios now works across multiple platforms:

- ✅ **Windows** (x64) - Full native support
- ✅ **macOS** (Intel/Apple Silicon) - Native support with build-from-source
- ✅ **Linux** (x64) - Native support with build-from-source  
- ✅ **Development Mode** - Explicit mock mode for development without native libraries

## Installation

### Full Installation with Native Helios Libraries

#### Windows
```bash
# Prerequisites: Visual Studio 2019+ or Build Tools

# Clone the Helios git repository
git clone --recursive git@github.com:PlantSimulationLab/PyHelios.git
cd PyHelios/

# Build native Helios C++ library
./build_scripts/build_helios

# Install Python dependencies
pip install -e .
```

#### macOS
```bash
# Clone the Helios git repository
git clone --recursive git@github.com:PlantSimulationLab/PyHelios.git
cd PyHelios/

# Install Helios C++ dependencies
source helios-core/utilities/dependencies.sh

# Build native Helios C++ library
./build_scripts/build_helios

# Install Python dependencies
pip install -e .
```

#### Linux (Ubuntu/Debian)
```bash
# Clone the Helios git repository
git clone --recursive git@github.com:PlantSimulationLab/PyHelios.git
cd PyHelios/

# Install Helios C++ dependencies
source helios-core/utilities/dependencies.sh

# Build native Helios C++ library  
./build_scripts/build_helios

# Install Python dependencies
pip install -e .
```

## Usage

- Creating a basic Context and adding a Patch

```python
from pyhelios import Context
from pyhelios.types import *

context = Context()

center = vec3(2, 3, 4)
size = vec2(1, 1)
color = RGBcolor(0.25, 0.25, 0.25)

patch_uuid = context.addPatch(center=center, size=size, color=color)
```

- Creating a Lemon tree and an Olive tree using WeberPennTree plugin

```python
from pyhelios import Context, WeberPennTree

context = Context()
wpt = WeberPennTree(context)

tree_id_lemon = wpt.buildTree(wpt_type=WeberPennTree.WPTType.LEMON)
tree_id_olive = wpt.buildTree(wpt_type=WeberPennTree.WPTType.OLIVE)
```

- GPU-accelerated radiation simulation with graceful plugin handling

```python
from pyhelios import Context, RadiationModel

context = Context()

# Add geometry to the context here (PLY files, patches, trees, etc.)

with RadiationModel(context) as radiation:
    radiation.addRadiationBand(band_label="SW")
    radiation.setDirectRayCount(band_label="SW", ray_count=100)
    radiation.setDiffuseRayCount(band_label="SW", ray_count=1000)
        
    # Run GPU simulation
    radiation.runBand(band_label="SW")
    results = radiation.getTotalAbsorbedFlux()
        
    # Apply native pseudocolor mapping for visualization
    all_uuids = context.getAllUUIDs()
    context.colorPrimitiveByDataPseudocolor(all_uuids, "radiation_flux_SW", "hot", 256)
```

### Command-Line Plugin Tools

```bash
# Comprehensive plugin status
python -m pyhelios.plugins status

# System analysis and recommendations
python -m pyhelios.plugins discover

# Information about specific plugins
python -m pyhelios.plugins info radiation

# Validate plugin combinations
python -m pyhelios.plugins validate --plugins radiation,visualizer
```

## Development and Testing

```bash
# Run tests (works on all platforms)
pytest

# Run only cross-platform tests
pytest -m cross_platform

# Run only tests that need native libraries
pytest -m native_only

# Run with coverage
pytest --cov=pyhelios
```

## Building Native Libraries

PyHelios now supports **flexible plugin selection** for customized builds based on your hardware and requirements. Choose from **21 available plugins** using predefined profiles or explicit selection.

### Advanced Plugin Selection

```bash
# Custom plugin selection
build_scripts/build_helios --plugins weberpenntree,visualizer

# Interactive selection (guided setup)
build_scripts/build_helios --interactive

# Exclude problematic plugins
build_scripts/build_helios --exclude radiation
```

### Configuration File Support

Create `pyhelios_config.yaml` for persistent plugin preferences:

```yaml
plugins:
  selection_mode: "profile"
  profile: "standard"
  excluded_plugins:
    - radiation  # Exclude if no GPU available
```

### Available Plugin Profiles

- **minimal**: Core functionality (weberpenntree, canopygenerator, solarposition)
- **standard**: Standard features with visualization (adds energybalance, photosynthesis, visualizer)  
- **gpu-accelerated**: High-performance GPU features (adds radiation for ray tracing)
- **research**: Comprehensive research suite (most plugins for academic use)
- **production**: Production-ready features (reliable, well-tested plugins)
- **visualization**: Focus on rendering and visualization
- **sensing**: Remote sensing and LiDAR simulation
- **physics**: Comprehensive physics modeling
- **development**: Minimal set for PyHelios development

## Troubleshooting

### Import Errors
- Verify installation: `pip list | grep pyhelios`
- Check Python version: Requires Python 3.7+
- Try reinstalling: `pip install -e . --force-reinstall`

## Advanced Features

### GPU Radiation Simulation
- OptiX-accelerated ray tracing for realistic radiation modeling
- Direct and diffuse radiation calculations
- Multi-bounce scattering simulation
- Native pseudocolor mapping for visualization
- Example: `docs/examples/stanford_bunny_radiation.py`

### C++ Plugin Development
For developers looking to integrate additional C++ plugins, see `docs/cpp_plugin_integration_guide.md` for comprehensive guidance on:
- Native library building and linking
- Python wrapper implementation
- Cross-platform considerations
- Testing and documentation standards

For additional support, see the [Helios documentation](https://baileylab.ucdavis.edu/software/helios) or [GitHub issues](https://github.com/PlantSimulationLab/PyHelios/issues).




