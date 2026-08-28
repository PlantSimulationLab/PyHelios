# CUDA Setup Guide for PyHelios {#CUDASetup}

[TOC]

## Overview

Several PyHelios plugins support NVIDIA CUDA for GPU-accelerated computations. This guide provides comprehensive instructions for installing and configuring CUDA for PyHelios.

> **Note**: The radiation plugin now also supports a Vulkan compute backend, enabling GPU ray tracing on AMD, Intel, and Apple Silicon GPUs without CUDA. See the \ref RadiationDoc "Radiation Model documentation" for details.

> **Running in a container?** This guide covers host installation. For Docker-specific
> setup -- driver capabilities, required system libraries, and the settings needed to reach
> the OptiX backend -- see \ref DockerGPU "Running PyHelios in Docker with GPU Support".

## GPU-Accelerated Plugins

The following plugins use GPU acceleration:

| Plugin | Description | CUDA Required |
|--------|-------------|---------------|
| \ref pyhelios.RadiationModel.RadiationModel "RadiationModel" | GPU-accelerated ray tracing via Vulkan or OptiX | No (Vulkan alternative available) |
| \ref pyhelios.EnergyBalance.EnergyBalanceModel "EnergyBalanceModel" | Plant energy balance and thermal modeling | Optional (CPU fallback) |
| aeriallidar | Aerial LiDAR simulation with GPU acceleration | Yes |
| lidar | LiDAR simulation and point cloud processing | Yes |

## System Requirements

### Hardware Requirements

- **GPU**: NVIDIA GPU with CUDA Compute Capability 3.5 or higher
- **Memory**: Minimum 2GB GPU memory (4GB+ recommended for large simulations)
- **Driver**: NVIDIA GPU driver 450.80.02 or newer (Linux) / 452.39 or newer (Windows)

### Platform Support

- **Windows**: Full CUDA support (Windows 10/11)
- **Linux**: Full CUDA support (Ubuntu 18.04+, CentOS 7+, other distributions)
- **macOS**: **NOT SUPPORTED** - Apple discontinued NVIDIA GPU support after macOS 10.13

## CUDA Toolkit Installation

### Recommended CUDA Versions

PyHelios is tested and compatible with:
- **CUDA 11.8** (Recommended - broadest compatibility)
- **CUDA 12.0, 12.1, 12.2, 12.3** (Newer features, may require driver updates)

**Minimum Version**: CUDA 9.0 (some plugins may require newer versions)

### Windows Installation

1. **Download CUDA Toolkit**:
   - Visit [NVIDIA CUDA Downloads](https://developer.nvidia.com/cuda-downloads)
   - Select: Windows → x86_64 → Your Windows version → exe (network or local)
   - Download the installer (network installer is smaller, ~3MB vs. ~3GB local)

2. **Run Installer**:
   ```
   cuda_12.x.x_windows.exe
   ```
   - Accept the license agreement
   - Choose "Custom" installation
   - Recommended components:
     - CUDA Toolkit
     - CUDA Samples (optional, useful for testing)
     - CUDA Documentation (optional)
     - CUDA Demo Suite (optional)
     - GeForce Experience (optional)

3. **Verify Installation**:
   ```bash
   # Open Command Prompt or PowerShell
   nvidia-smi  # Should show GPU information
   nvcc --version  # Should show CUDA compiler version
   ```

4. **Set Environment Variables** (usually done automatically):
   - `CUDA_PATH`: `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x`
   - `PATH`: Should include `%CUDA_PATH%\bin` and `%CUDA_PATH%\libnvvp`

### Linux Installation

**Ubuntu/Debian:**

```bash
# 1. Download CUDA Toolkit
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update

# 2. Install CUDA
sudo apt-get install cuda-toolkit-12-3  # Or your preferred version

# 3. Add to PATH (add to ~/.bashrc)
export PATH=/usr/local/cuda-12.3/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda-12.3/lib64:$LD_LIBRARY_PATH

# 4. Reload environment
source ~/.bashrc

# 5. Verify installation
nvidia-smi
nvcc --version
```

**CentOS/RHEL:**

```bash
# 1. Download and install CUDA repo
sudo yum install https://developer.download.nvidia.com/compute/cuda/repos/rhel8/x86_64/cuda-keyring-1.1-1-1.noarch.rpm

# 2. Install CUDA
sudo yum install cuda-toolkit-12-3

# 3. Add to PATH (add to ~/.bashrc)
export PATH=/usr/local/cuda-12.3/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda-12.3/lib64:$LD_LIBRARY_PATH

# 4. Reload environment
source ~/.bashrc

# 5. Verify installation
nvidia-smi
nvcc --version
```

**Alternative: Direct Installer**

For more control or if repository installation fails:

```bash
# 1. Download runfile installer from NVIDIA website
wget https://developer.download.nvidia.com/compute/cuda/12.3.0/local_installers/cuda_12.3.0_545.23.06_linux.run

# 2. Run installer
sudo sh cuda_12.3.0_545.23.06_linux.run

# Follow prompts - deselect driver if already installed
```

## Verification

### Check CUDA Installation

```bash
# Check GPU status and driver version
nvidia-smi

# Check CUDA compiler
nvcc --version

# Check CUDA library path (Linux)
ldconfig -p | grep cuda
```

**Expected nvidia-smi output:**
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 545.23.06    Driver Version: 545.23.06    CUDA Version: 12.3    |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
```

### Test PyHelios GPU Plugins

```python
from pyhelios import Context, EnergyBalanceModel

# Test energy balance plugin
try:
    with Context() as context:
        with EnergyBalanceModel(context) as energy_balance:
            print("✓ EnergyBalance plugin available - CUDA working!")
except RuntimeError as e:
    print(f"✗ CUDA not available: {e}")
```

## Windows-Specific: GPU Timeout Settings {#PCGPUTimeout}

Windows has a Timeout Detection and Recovery (TDR) feature that terminates GPU operations taking longer than 2 seconds by default. For long-running PyHelios simulations, you need to increase this timeout.

### Increase GPU Timeout (Windows Registry)

**WARNING**: Modifying the registry can affect system stability. Back up your registry before proceeding.

1. **Open Registry Editor**:
   - Press `Win + R`, type `regedit`, press Enter
   - Navigate to: `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\GraphicsDrivers`

2. **Create/Modify TDR Keys**:
   - Right-click → New → DWORD (32-bit) Value
   - Create these keys with specified values:

   | Key Name | Value | Description |
   |----------|-------|-------------|
   | `TdrLevel` | `0` | Disables TDR (use with caution) |
   | `TdrDelay` | `60` | Timeout in seconds (default is 2) |
   | `TdrDdiDelay` | `60` | Driver timeout in seconds |

3. **Restart Computer** for changes to take effect

### Alternative: TDR Registry File

Create a file `disable_tdr.reg`:

```registry
Windows Registry Editor Version 5.00

[HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\GraphicsDrivers]
"TdrLevel"=dword:00000000
"TdrDelay"=dword:0000003c
"TdrDdiDelay"=dword:0000003c
```

Double-click to import, then restart.

### Verify TDR Settings

```bash
# PowerShell
reg query "HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers" /v TdrLevel
reg query "HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers" /v TdrDelay
```

**References**:
- [NVIDIA TDR Documentation](https://docs.nvidia.com/gameworks/content/developertools/desktop/timeout_detection_recovery.htm)
- [Microsoft TDR Registry Keys](https://learn.microsoft.com/en-us/windows-hardware/drivers/display/tdr-registry-keys)

## Choosing the Right CUDA Version {#ChoosingCUDA}

### Compatibility Matrix

| CUDA Version | GPU Compute Capability | GCC Version (Linux) | Visual Studio (Windows) |
|--------------|------------------------|---------------------|-------------------------|
| CUDA 11.8    | 3.5 - 9.0              | 5.3 - 11.x          | 2017, 2019, 2022        |
| CUDA 12.0    | 5.0 - 9.0              | 6.0 - 12.x          | 2019, 2022              |
| CUDA 12.3    | 5.0 - 9.0              | 6.0 - 12.x          | 2019, 2022              |

### Check Your GPU Compute Capability

```bash
# Using nvidia-smi
nvidia-smi --query-gpu=compute_cap --format=csv

# Or using CUDA sample (if installed)
/usr/local/cuda/samples/1_Utilities/deviceQuery/deviceQuery
```

**Common GPUs and Compute Capabilities**:
- GeForce RTX 40xx series: 8.9
- GeForce RTX 30xx series: 8.6
- GeForce RTX 20xx series: 7.5
- GeForce GTX 16xx series: 7.5
- GeForce GTX 10xx series: 6.1
- Older GPUs: Check [NVIDIA GPU Compute Capability](https://developer.nvidia.com/cuda-gpus)

### Recommendation

- **For maximum compatibility**: Use CUDA 11.8
- **For latest features**: Use CUDA 12.3
- **For older GPUs** (compute < 5.0): Use CUDA 10.2 or earlier

## OptiX Requirements (Radiation Plugin Only) {#OptiXSetup}

The \ref pyhelios.RadiationModel.RadiationModel "RadiationModel" plugin requires NVIDIA OptiX for GPU-accelerated ray tracing.

### For Pip-Installed PyHelios (Most Users)

**You do NOT need to install OptiX yourself** - it is already bundled:

- **Windows**: OptiX runtime is bundled with PyHelios wheels
- **Linux (native)**: OptiX runtime is bundled with PyHelios wheels
- **WSL (Windows Subsystem for Linux)**: See special instructions below

### For WSL (Windows Subsystem for Linux) Users

If you're using WSL2 with GPU passthrough:

1. **Verify GPU Access**:
   ```bash
   nvidia-smi  # Should show your GPU
   ```

2. **Install CUDA for WSL**:
   - Follow [NVIDIA's WSL-CUDA guide](https://docs.nvidia.com/cuda/wsl-user-guide/index.html)
   - Use the WSL-specific CUDA installer (NOT the Linux installer)

3. **OptiX on WSL**:
   - OptiX may require manual installation in WSL environments
   - Download from [NVIDIA OptiX Downloads](https://developer.nvidia.com/optix/downloads)
   - Follow WSL-specific GPU library installation procedures

### For Building PyHelios from Source

**You do NOT need to download OptiX SDK** - headers are bundled in the repository:

- OptiX SDK headers are included in `helios-core/plugins/radiation/lib/OptiX/`
- Simply build with the radiation plugin enabled:
  ```bash
  build_scripts/build_helios --clean --plugins radiation
  ```

## Troubleshooting

### Common Issues

#### Issue: "nvidia-smi: command not found" or "NVIDIA driver not found"

**Solution**: Install or update NVIDIA GPU drivers
```bash
# Ubuntu/Debian
sudo ubuntu-drivers autoinstall
sudo reboot

# Or download from NVIDIA: https://www.nvidia.com/download/index.aspx
```

#### Issue: "nvcc: command not found"

**Solution**: CUDA not in PATH
```bash
# Linux - add to ~/.bashrc
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

# Windows - add to System Environment Variables PATH:
C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x\bin
```

#### Issue: "CUDA error: out of memory"

**Solutions**:
- Reduce simulation size (fewer primitives)
- Close other GPU-using applications
- Use smaller timesteps for dynamic simulations
- Upgrade GPU memory

#### Issue: "CUDA driver version is insufficient for CUDA runtime version"

**Solution**: Update NVIDIA GPU drivers to match CUDA version requirements
- Check required driver version at [CUDA Toolkit Release Notes](https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/)

#### Issue: PyHelios builds without CUDA support

**Solution**: Verify CUDA is detected during build
```bash
# Clean rebuild
build_scripts/build_helios --clean --verbose

# Check CMake output for:
# -- Found CUDA: /usr/local/cuda-12.3
# -- CUDA version: 12.3
```

If CUDA not detected:
- Ensure `nvcc` is in PATH
- Set `CUDA_PATH` environment variable
- Install CUDA development packages (headers)

### Performance Issues

#### Slow GPU Performance

- **Check GPU usage**: `nvidia-smi -l 1` (updates every second)
- **Verify GPU clocks**: `nvidia-smi -q -d CLOCK`
- **Thermal throttling**: Check temperatures, improve cooling
- **Power limit**: Increase if needed: `sudo nvidia-smi -pl 300` (sets 300W limit)

### Getting Help

If issues persist:

1. **Check PyHelios plugin status**:
   ```bash
   python -c "from pyhelios.plugins import print_plugin_status; print_plugin_status()"
   ```

2. **Collect system information**:
   ```bash
   nvidia-smi
   nvcc --version
   python --version
   python -c "import pyhelios; print(pyhelios.__version__)"
   ```

3. **Report issues** with this information at [PyHelios GitHub Issues](https://github.com/baileylab/pyhelios/issues)

## Additional Resources

### Official Documentation

- [NVIDIA CUDA Installation Guide (Linux)](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/)
- [NVIDIA CUDA Installation Guide (Windows)](https://docs.nvidia.com/cuda/cuda-installation-guide-microsoft-windows/)
- [CUDA Toolkit Downloads](https://developer.nvidia.com/cuda-downloads)
- [CUDA Compatibility Guide](https://docs.nvidia.com/deploy/cuda-compatibility/)
- [OptiX Programming Guide](https://raytracing-docs.nvidia.com/optix7/guide/index.html)

### PyHelios Documentation

- \ref PluginBuildSystem "Building and Selecting Plug-ins"
- \ref pyhelios.RadiationModel.RadiationModel "RadiationModel Documentation"
- \ref EnergyBalanceDoc "EnergyBalance Documentation"

### Community Support

- [PyHelios GitHub](https://github.com/baileylab/pyhelios)
- [Helios Main Website](https://baileylab.ucdavis.edu/software/helios)
- [NVIDIA Developer Forums](https://forums.developer.nvidia.com/)
