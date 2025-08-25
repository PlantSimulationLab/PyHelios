# Cross-Platform Usage {#CrossPlatform}

PyHelios is designed to work seamlessly across Windows, macOS, and Linux. This guide covers platform-specific considerations and features.

## Platform Support Matrix

| Feature | Windows | macOS | Linux | Notes |
|---------|---------|-------|-------|-------|
| Core PyHelios | ✅ | ✅ | ✅ | Full support |
| WeberPennTree | ✅ | ✅ | ✅ | Procedural trees |
| Visualizer | ✅ | ✅ | ✅ | OpenGL rendering |
| Radiation (GPU) | ✅ | ⚠️ | ✅ | Requires CUDA |
| Pre-built Libraries | ❌ | ❌ | ❌ | Build from source required |
| Development Mode | ✅ | ✅ | ✅ | Mock mode |

## Windows

**Advantages:**
- Excellent Visual Studio integration
- Comprehensive plugin support when built
- Strong GPU computing support

**Setup:**
```bash
git clone --recursive https://github.com/PlantSimulationLab/PyHelios.git
cd PyHelios/
# Build native libraries (required)
build_scripts/build_helios
pip install -e .
```

**Build Requirements:**
```bash
# Requires Visual Studio 2019+ or Build Tools
# Install Visual Studio Build Tools or full IDE
```

**GPU Support:**
- Install CUDA Toolkit 11.0+
- NVIDIA GPU with compute capability 3.5+

## macOS

**Advantages:**
- Native Apple Silicon and Intel support
- Excellent development experience
- Full OpenGL/Metal support

**Setup:**
```bash
# Install Xcode command line tools
xcode-select --install

git clone --recursive https://github.com/PlantSimulationLab/PyHelios.git
cd PyHelios/
build_scripts/build_helios
pip install -e .
```

**Platform Considerations:**
- **Apple Silicon**: Full native support
- **Intel Macs**: Full compatibility
- **GPU Acceleration**: Limited CUDA support (eGPU setups)
- **Homebrew**: May be used for dependencies

**Common Issues:**
```bash
# If you get permission errors:
sudo xcode-select --install

# If CMake is missing:
brew install cmake

# Environment setup:
source pyhelios/setup_env.sh
```

## Linux

**Advantages:**
- Excellent server deployment
- Strong GPU computing support
- Flexible package management

**Setup (Ubuntu/Debian):**
```bash
# Install prerequisites
sudo apt-get update
sudo apt-get install build-essential cmake python3-dev

git clone --recursive https://github.com/PlantSimulationLab/PyHelios.git
cd PyHelios/
build_scripts/build_helios
pip install -e .
```

**Setup (CentOS/RHEL):**
```bash
# Install prerequisites
sudo yum groupinstall "Development Tools"
sudo yum install cmake python3-devel

# Continue with standard build process
```

**GPU Support:**
```bash
# Install CUDA (example for Ubuntu)
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/7fa2af80.pub
sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /"
sudo apt-get update
sudo apt-get install cuda
```

## Platform-Specific Features

### Library Loading

PyHelios automatically detects and loads the correct libraries:

```python
from pyhelios.plugins import get_library_info

# Check current platform and library status  
info = get_library_info()
print(f"Platform: {info['platform']}")
print(f"Library path: {info['library_path']}")
print(f"Available plugins: {info['plugins']}")
```

### File Paths

```python
from pathlib import Path
import os

# Cross-platform path handling
data_dir = Path.home() / "PyHelios" / "data"
data_dir.mkdir(parents=True, exist_ok=True)

# Platform-specific paths
if os.name == 'nt':  # Windows
    config_dir = Path(os.environ['APPDATA']) / "PyHelios"
else:  # macOS/Linux
    config_dir = Path.home() / ".config" / "pyhelios"
```

### Environment Variables

```python
import os

# Set library path (Linux/macOS)
if os.name != 'nt':
    lib_path = "/path/to/pyhelios/plugins"
    current_path = os.environ.get('LD_LIBRARY_PATH', '')
    os.environ['LD_LIBRARY_PATH'] = f"{lib_path}:{current_path}"

# Development mode (all platforms)
os.environ['PYHELIOS_DEV_MODE'] = '1'  # Enable mock mode
```

## Performance Considerations

### Memory Usage
- **Windows**: Typically lowest memory overhead
- **macOS**: Moderate memory usage, excellent for development
- **Linux**: Most efficient for large-scale simulations

### GPU Performance
- **Windows**: Best CUDA support and performance
- **Linux**: Excellent for server/cluster deployments  
- **macOS**: Limited GPU compute capabilities

## Development Workflow

### Cross-Platform Development

```python
import platform
from pyhelios import Context

def create_optimized_context():
    """Create context optimized for current platform."""
    system = platform.system()
    
    if system == "Windows":
        # Windows-specific optimizations
        context = Context()
        # Use all available plugins
    elif system == "Darwin":  # macOS
        # macOS-specific optimizations
        context = Context()
        # May skip GPU-intensive plugins
    else:  # Linux
        # Linux-specific optimizations
        context = Context()
        # Optimize for server deployment
    
    return context
```

### Testing Across Platforms

```bash
# Run platform-specific tests
pytest -m windows_only   # Windows-only tests
pytest -m macos_only     # macOS-only tests  
pytest -m linux_only     # Linux-only tests
pytest -m cross_platform # All platforms
```

## Deployment Considerations

### Windows Deployment
- Include Visual C++ Redistributable
- Package native DLLs with application
- Consider installer packages

### macOS Deployment
- Code signing for distribution
- Create .app bundles
- Consider Homebrew for dependencies

### Linux Deployment
- Package as .deb/.rpm or use containers
- Handle library dependencies
- Consider snap/flatpak packages

## Troubleshooting

### Common Cross-Platform Issues

**Library Loading Errors:**
```bash
# Check library dependencies
# Windows:
dumpbin /dependents libhelios.dll

# macOS:
otool -L libhelios.dylib

# Linux:
ldd libhelios.so
```

**Path Issues:**
```python
# Use pathlib for cross-platform paths
from pathlib import Path

# Wrong:
path = "data/models/tree.obj"

# Right:
path = Path("data") / "models" / "tree.obj"
```

**Environment Setup:**
```bash
# Windows (PowerShell):
$env:PYTHONPATH = "C:\path\to\PyHelios"

# macOS/Linux:
export PYTHONPATH="/path/to/PyHelios"
export LD_LIBRARY_PATH="/path/to/PyHelios/plugins:$LD_LIBRARY_PATH"
```

## Platform-Specific Examples

See the `docs/examples/` directory for platform-specific examples:
- `windows_specific.py` - Windows-only features
- `macos_integration.py` - macOS-specific integrations
- `linux_server.py` - Linux server deployment
- `cross_platform_app.py` - Universal application