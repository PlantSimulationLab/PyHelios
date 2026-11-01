# Running PyHelios in Docker with GPU Support {#DockerGPU}

[TOC]

## Overview

The Linux wheel is self-contained -- `pip install pyhelios3d` needs no extra system
packages. GPU ray tracing is the part that needs setup: OptiX requires driver libraries
that the NVIDIA Container Toolkit injects **only when explicitly asked**, which it is not
by default.

That failure is silent. A container without those libraries imports fine, runs fine, and
uses a slower backend without reporting anything.

For host-level CUDA installation, see \ref CUDASetup "CUDA Setup Guide".

## Quick start

```bash
docker run -it --rm --gpus all \
  -e NVIDIA_DRIVER_CAPABILITIES=compute,utility,graphics \
  nvidia/cuda:12.6.3-runtime-ubuntu24.04 bash

# inside the container
apt-get update && apt-get install -y python3-pip
pip install pyhelios3d --break-system-packages
```

Then verify:

```python
from pyhelios import Context, RadiationModel
with RadiationModel(Context()) as radiation:
    print(radiation.getBackendName())   # "OptiX 8.1" on a working NVIDIA setup
```

## System libraries

The Linux wheel bundles the OpenGL and X11 libraries the visualizer plugin needs, so no
additional system packages are required -- even on minimal images such as `python:*-slim`
and `nvidia/cuda:*`.

## GPU access and driver capabilities

### Why the default configuration is not enough

`NVIDIA_DRIVER_CAPABILITIES` controls which host driver libraries the NVIDIA Container
Toolkit injects into the container. When unset it defaults to `utility,compute`:

| Capability | Provides |
|------------|----------|
| `utility`  | `nvidia-smi`, NVML |
| `compute`  | CUDA |
| `graphics` | OpenGL, EGL, Vulkan ICD, **and OptiX** |
| `display`  | X11 display support (also enables the graphics mounts) |
| `video`    | Video Codec SDK |
| `compat32` | 32-bit application support |

OptiX's driver library `libnvoptix.so.1` is part of the **graphics** mount set. With the
default capabilities you get a container where `nvidia-smi` works, CUDA works, and OptiX
is silently unavailable — so the radiation model falls back to Vulkan.

Set the capability explicitly:

```bash
docker run --gpus all -e NVIDIA_DRIVER_CAPABILITIES=compute,utility,graphics ...
```

`NVIDIA_DRIVER_CAPABILITIES=all` also works.

### Confirming injection worked

Before debugging PyHelios, confirm the driver libraries actually reached the container:

```bash
docker run --rm --gpus all -e NVIDIA_DRIVER_CAPABILITIES=compute,utility,graphics \
  nvidia/cuda:12.6.3-runtime-ubuntu24.04 \
  bash -c 'ldconfig -p | grep -E "libnvoptix|libcuda\.so"'
```

Both `libnvoptix.so.1` and `libcuda.so.1` should be listed. If they are absent, the
problem is with the container runtime configuration, not with PyHelios.

### Which backend is active

The radiation model probes backends in order — OptiX 8, then OptiX 6, then Vulkan — and
falls back silently. Ask it directly:

```python
from pyhelios import Context, RadiationModel
with RadiationModel(Context()) as radiation:
    print(radiation.getBackendName())
```

`"Vulkan Compute"` on an NVIDIA system means OptiX was not available. Vulkan is a
complete ray-tracing backend rather than a degraded mode — results are valid — but OptiX
is typically faster on NVIDIA hardware.

## Choosing a base image

PyHelios's native library does **not** link the CUDA runtime; it loads `libcuda.so.1` and
`libnvoptix.so.1` from the driver at runtime. A CUDA base image is therefore convenient
but not required — any Debian- or Ubuntu-based image works, provided the container
runtime injects the driver libraries.

If you do use `nvidia/cuda` images, the `runtime` flavor is sufficient. The `devel`
flavor adds compilers and headers that a pre-built wheel never uses.

> **Note**: NVIDIA deletes end-of-life CUDA image tags from Docker Hub, so a pinned tag
> will not remain available indefinitely. Mirror images you depend on long-term.

The `nvidia/cudagl` and `nvidia/opengl` images are no longer maintained (frozen at CUDA
11.x); install the graphics libraries into a current image instead.

### Example Dockerfile

```dockerfile
FROM nvidia/cuda:12.6.3-runtime-ubuntu24.04

ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility,graphics

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --break-system-packages pyhelios3d
```

Baking `NVIDIA_DRIVER_CAPABILITIES` into the image means users only need `--gpus all`.
Run it with:

```bash
docker run --rm --gpus all your-image python3 -c "import pyhelios; print(pyhelios.__version__)"
```

## Requirements on the host

GPU access in a container requires all of:

- An NVIDIA driver on the **host** (not inside the container)
- The [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
  installed and configured
- The Docker daemon restarted after configuration

Configuration is not automatic after installing the toolkit package:

```bash
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

`--gpus all` is Docker CLI syntax that dispatches to the NVIDIA runtime; it does not work
without the toolkit installed.

OptiX 8 additionally requires driver >= 560. OptiX 6.5 covers older drivers. If neither is
usable, the Vulkan backend is used.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `docker: Error response from daemon: could not select device driver "" with capabilities: [[gpu]]` | Container Toolkit not installed, `nvidia-ctk runtime configure` not run, or Docker not restarted | Run the configure and restart commands above |
| `nvidia-smi` works, but `getBackendName()` reports Vulkan | `NVIDIA_DRIVER_CAPABILITIES` lacks `graphics` | Add `graphics` to the capability list |
| `libnvoptix.so.1` absent from `ldconfig -p` despite `graphics` being set | Container Toolkit older than v1.15.0 (Apr 2024), which added injection of an OptiX support file | Upgrade the toolkit; check with `nvidia-ctk --version` |
| `Failed to initialize NVML: Unknown Error` | cgroup driver interaction | See NVIDIA's [troubleshooting guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/troubleshooting.html) |
| Vulkan backend selected on a machine with no NVIDIA GPU | Expected behavior | None needed; Vulkan is a supported backend |

### Vulkan specifics

If you are targeting the Vulkan backend rather than OptiX, note that the toolkit injects
the NVIDIA Vulkan ICD but not the Vulkan loader itself — install `libvulkan1` in the
image. The injected ICD is written to `/etc/vulkan/icd.d/`; the standard loader searches
both that and `/usr/share/vulkan/icd.d/`, but software that hardcodes the latter will not
find it.

If a Mesa software driver (`mesa-vulkan-drivers`, providing lavapipe) is also installed,
it can be enumerated alongside the NVIDIA device. Should Vulkan appear to run on the CPU,
check which devices are present with `vulkaninfo` from `vulkan-tools`.

## Rootless Docker, Podman, and WSL2

- **Rootless Docker** requires extra toolkit configuration; see NVIDIA's install guide.
  Note that the `no-cgroups` setting it requires is system-wide and affects rootful
  containers on the same host.
- **Podman**: NVIDIA recommends CDI. Under SELinux, add `--security-opt=label=disable`.
- **WSL2**: install the NVIDIA driver on the Windows host only — never inside the WSL
  distribution. The Container Toolkit is still required inside the distribution.
