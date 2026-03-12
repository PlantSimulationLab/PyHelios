# Radiation Model Plugin {#RadiationDoc}

The Radiation Model plugin provides GPU-accelerated ray tracing for radiation simulation using Vulkan or OptiX backends. Backend selection is automatic based on available hardware: Vulkan supports all GPU vendors (NVIDIA, AMD, Intel, Apple Silicon), while OptiX provides an optimized path for NVIDIA GPUs. This documentation is based on the actual implementation.

## Overview

The \ref pyhelios.RadiationModel.RadiationModel "RadiationModel class" provides advanced radiation modeling and ray tracing capabilities for realistic light interaction simulations in plant canopies and scenes.

## Requirements

The radiation plugin supports two GPU backends. At least one must be available:

### Vulkan Backend (All Platforms)

Supports NVIDIA, AMD, Intel, and Apple Silicon GPUs via Vulkan compute shaders with software BVH traversal. Vulkan headers and the glslang shader compiler are bundled with Helios, so no external Vulkan SDK installation is required on Windows.

| Requirement | macOS | Linux | Windows |
|-------------|-------|-------|---------|
| **GPU** | Any with Vulkan support | Any with Vulkan support | Any with Vulkan support |
| **Dependencies** | `brew install vulkan-loader molten-vk` | `sudo apt-get install libvulkan-dev` | None (all bundled) |

### OptiX Backend (NVIDIA Only)

Provides optimized ray tracing on NVIDIA GPUs using hardware RT cores. Two OptiX versions are supported:

| Backend | Driver Requirement | CUDA | Notes |
|---------|-------------------|------|-------|
| **OptiX 8.1** | NVIDIA driver >= 560 | CUDA 12.0+ | Default for modern drivers |
| **OptiX 6.5** | NVIDIA driver < 560 | CUDA 9.0+ | Legacy driver support |

### Backend Selection

Backend selection is **automatic at runtime** via GPU hardware probing. When the radiation model starts, it probes compiled-in backends in priority order (OptiX 8 -> OptiX 6 -> Vulkan) and selects the first one that is compatible with the current hardware. If no compatible GPU is found, a clear diagnostic error is raised.

You can query the active backend at runtime:

```python
with RadiationModel(context) as radiation:
    print(f"Active backend: {radiation.getBackendName()}")
    # e.g., "OptiX 8.1", "OptiX 6.5", "Vulkan Compute"
```

You can also probe GPU availability without creating a full radiation model:

```python
if RadiationModel.probeAnyGPUBackend():
    print("GPU backend available")
else:
    print("No compatible GPU backend found")
```

**For CUDA/OptiX setup**, see the comprehensive \ref CUDASetup "CUDA Setup Guide", which covers:
- Choosing the correct CUDA toolkit version: \ref ChoosingCUDA
- Platform-specific installation steps (Windows, Linux)
- GPU timeout settings for Windows: \ref PCGPUTimeout
- OptiX requirements: \ref OptiXSetup
- Troubleshooting common issues

## Basic Usage

```python
from pyhelios import Context, RadiationModel
from pyhelios.types import *

# Create context with geometry
context = Context()
patch_uuid = context.addPatch(
    center=vec3(0, 0, 0),
    size=vec2(2, 2),
    color=RGBcolor(0.3, 0.7, 0.2)
)

# Use RadiationModel with context manager (recommended)
with RadiationModel(context) as radiation:
    # Add radiation band
    radiation.addRadiationBand("PAR")
    
    # Add radiation source
    source_id = radiation.addCollimatedRadiationSource()
    radiation.setSourceFlux(source_id, "PAR", 1000.0)
    
    # Configure ray counts
    radiation.setDirectRayCount("PAR", 100)
    radiation.setDiffuseRayCount("PAR", 300)
    
    # Run simulation
    radiation.runBand("PAR")
    
    # Get results
    results = radiation.getTotalAbsorbedFlux()
    print(f"Total absorbed flux: {sum(results)} W")
```

## Radiation Bands

### Basic Band Management

```python
# Add radiation bands (verified methods)
radiation.addRadiationBand("PAR")
radiation.addRadiationBand("NIR")
radiation.addRadiationBand("SW")

# Add band with wavelength bounds
radiation.addRadiationBand("custom", wavelength_min=400.0, wavelength_max=700.0)

# Copy existing band
radiation.copyRadiationBand("PAR", "PAR_copy")
```

### Common Radiation Bands

```python
# Standard radiation bands for plant modeling
bands = {
    "PAR": "Photosynthetically Active Radiation (400-700 nm)",
    "NIR": "Near Infrared (700-1100 nm)", 
    "SW": "Shortwave (300-3000 nm)",
    "UV": "Ultraviolet (280-400 nm)",
    "VIS": "Visible (380-750 nm)"
}

for band, description in bands.items():
    radiation.addRadiationBand(band)
    print(f"Added {band}: {description}")
```

## Radiation Sources

### Collimated Sources

```python
# Default collimated source (verified methods)
source_id = radiation.addCollimatedRadiationSource()

# Source with specific direction vector (accepts tuple, vec3, or SphericalCoord)
source_id = radiation.addCollimatedRadiationSource(
    direction=(0.3, 0.3, -0.9)  # tuple: (x, y, z)
)

# Alternative formats for direction parameter
source_id = radiation.addCollimatedRadiationSource(
    direction=vec3(0.3, 0.3, -0.9)  # vec3 object
)

source_id = radiation.addCollimatedRadiationSource(
    direction=SphericalCoord(1.0, 45.0, 135.0)  # spherical coordinates
)

# Set source flux
radiation.setSourceFlux(source_id, "PAR", 1200.0)  # W/m²
```

### Spherical Sources

```python
# Spherical radiation source
source_id = radiation.addSphereRadiationSource(
    position=(0, 0, 10),  # x, y, z position
    radius=0.5            # Source radius
)

# Set flux for spherical source
radiation.setSourceFlux(source_id, "PAR", 800.0)
```

### Sun Sources

```python
# Realistic sun modeling
sun_id = radiation.addSunSphereRadiationSource(
    radius=0.5,           # Sun disc radius
    zenith=45.0,          # Sun zenith angle (degrees)
    azimuth=180.0,        # Sun azimuth angle (degrees)
    position_scaling=1.0, # Position scaling factor
    angular_width=0.53,   # Sun angular width (degrees)
    flux_scaling=1.0      # Flux scaling factor
)

# Set solar flux
radiation.setSourceFlux(sun_id, "PAR", 1200.0)
```

## Flux Configuration

### Source Flux Management

```python
# Single source flux
radiation.setSourceFlux(source_id, "PAR", 1000.0)

# Multiple sources with same flux
source_ids = [source1, source2, source3]
radiation.setSourceFlux(source_ids, "PAR", 800.0)

# Get current source flux
current_flux = radiation.getSourceFlux(source_id, "PAR")
print(f"Source flux: {current_flux} W/m²")

# Diffuse radiation flux
radiation.setDiffuseRadiationFlux("PAR", 200.0)
```

## Ray Configuration

### Ray Count Settings

```python
# Configure ray counts for accuracy vs. performance
radiation.setDirectRayCount("PAR", 1000)    # Direct rays
radiation.setDiffuseRayCount("PAR", 3000)   # Diffuse rays

# Higher ray counts for better accuracy
radiation.setDirectRayCount("PAR", 5000)
radiation.setDiffuseRayCount("PAR", 10000)
```

### Ray Count Guidelines

```python
# Performance vs accuracy trade-offs
ray_configs = {
    "fast": {"direct": 100, "diffuse": 300},
    "standard": {"direct": 1000, "diffuse": 3000}, 
    "high_quality": {"direct": 5000, "diffuse": 15000},
    "research": {"direct": 10000, "diffuse": 30000}
}

# Apply configuration
config = ray_configs["standard"]
radiation.setDirectRayCount("PAR", config["direct"])
radiation.setDiffuseRayCount("PAR", config["diffuse"])
```

## Advanced Configuration

### Scattering Control

```python
# Set scattering depth (number of bounces)
radiation.setScatteringDepth("PAR", 3)

# Set minimum scatter energy threshold
radiation.setMinScatterEnergy("PAR", 0.01)
```

### Emission Control

```python
# Enable/disable emission for thermal radiation
radiation.enableEmission("thermal")
radiation.disableEmission("PAR")  # PAR typically doesn't emit
```

## Simulation Execution

### Geometry Updates

```python
# Update all geometry before simulation
radiation.updateGeometry()

# Update specific geometry UUIDs
radiation.updateGeometry([patch_uuid, triangle_uuid])
```

### Running Simulations

**CRITICAL PERFORMANCE NOTE**: When simulating multiple radiation bands, **ALWAYS** run all bands in a single `runBand()` call rather than sequential single-band calls. This provides **significant computational efficiency gains** (often 2-5x faster) because:

- GPU ray tracing setup is performed once for all bands
- Scene geometry acceleration structures are reused across bands
- GPU kernel launches are batched together
- Memory transfers between CPU/GPU are minimized
- Ray traversal computations are shared between spectral bands

```python
# ✅ EFFICIENT - Single call for multiple bands (RECOMMENDED)
radiation.runBand(["PAR", "NIR", "SW"])

# ❌ INEFFICIENT - Sequential single-band calls (AVOID)
radiation.runBand("PAR")    # Full GPU setup overhead
radiation.runBand("NIR")    # Full GPU setup overhead again  
radiation.runBand("SW")     # Full GPU setup overhead again

# Single band execution (when only one band needed)
radiation.runBand("PAR")
```

### Performance Comparison

```python
import time

# Method 1: Sequential calls (SLOW)
start_time = time.time()
radiation.runBand("PAR")
radiation.runBand("NIR") 
radiation.runBand("SW")
sequential_time = time.time() - start_time

# Method 2: Multi-band call (FAST)
start_time = time.time()
radiation.runBand(["PAR", "NIR", "SW"])
multiband_time = time.time() - start_time

print(f"Sequential: {sequential_time:.2f}s")
print(f"Multi-band: {multiband_time:.2f}s") 
print(f"Speedup: {sequential_time/multiband_time:.1f}x faster")
```

## Results and Analysis

### Flux Results

```python
# Get total absorbed flux for all primitives
results = radiation.getTotalAbsorbedFlux()
total_absorption = sum(results)
print(f"Total absorbed flux: {total_absorption:.2f} W")

# Analyze results per primitive
all_uuids = context.getAllUUIDs()
for i, uuid in enumerate(all_uuids):
    if i < len(results):
        flux = results[i]
        area = context.getPrimitiveArea(uuid)
        flux_density = flux / area if area > 0 else 0
        print(f"Primitive {uuid}: {flux:.2f} W ({flux_density:.2f} W/m²)")
```

### Radiation Analysis

```python
# Calculate radiation statistics
radiation_data = radiation.getTotalAbsorbedFlux()

import statistics
mean_flux = statistics.mean(radiation_data)
max_flux = max(radiation_data)
min_flux = min(radiation_data)
std_flux = statistics.stdev(radiation_data)

print(f"Radiation statistics:")
print(f"  Mean: {mean_flux:.2f} W")
print(f"  Max: {max_flux:.2f} W") 
print(f"  Min: {min_flux:.2f} W")
print(f"  Std Dev: {std_flux:.2f} W")
```

## Advanced Band Management

### Query Band Existence

```python
# Check if band exists before using it
if radiation.doesBandExist("PAR"):
    print("PAR band exists")
    radiation.setDirectRayCount("PAR", 1000)
else:
    radiation.addRadiationBand("PAR")
```

### Copy Band with Wavelength Range

```python
# Copy band preserving original wavelength range
radiation.addRadiationBand("fullspectrum", 300, 3000)
radiation.copyRadiationBand("fullspectrum", "fullspectrum_copy")

# Copy band with new wavelength range
radiation.copyRadiationBand("fullspectrum", "PAR", 400, 700)
radiation.copyRadiationBand("fullspectrum", "NIR", 700, 1100)
```

## Geometric Radiation Sources

### Rectangle Sources (LED Panels, Grow Lights)

```python
from pyhelios.types import vec3, vec2

# Add rectangular radiation source (e.g., LED panel)
led_panel = radiation.addRectangleRadiationSource(
    position=vec3(0, 0, 5),      # Center position 5m above ground
    size=vec2(2.0, 1.0),          # 2m × 1m panel
    rotation=vec3(0, 0, 0)        # Rotation (Euler angles in radians)
)

# Configure the LED panel
radiation.addRadiationBand("LED")
radiation.setSourceFlux(led_panel, "LED", 500.0)  # 500 W/m²

# Set LED spectrum
led_spectrum = [
    (400, 0.0), (450, 0.3), (500, 0.8),
    (550, 0.5), (600, 0.2), (700, 0.0)
]
radiation.setSourceSpectrum(led_panel, led_spectrum)
```

### Disk Sources (Spotlights, Circular LEDs)

```python
# Add circular disk source (e.g., spotlight)
spotlight = radiation.addDiskRadiationSource(
    position=vec3(2, 2, 5),      # Position
    radius=0.5,                   # 0.5m radius
    rotation=vec3(0, 0, 0)        # Rotation
)

radiation.setSourceFlux(spotlight, "PAR", 800.0)
```

### Dynamic Source Positioning

```python
# Reposition sources for time-series simulations
for time_step in range(24):  # 24 hour simulation
    # Move sun position
    sun_position = calculate_sun_position(time_step)
    radiation.setSourcePosition(sun_id, sun_position)

    # Run simulation for this time step
    radiation.runBand("PAR")
    results = radiation.getTotalAbsorbedFlux()
    save_results(time_step, results)

# Delete sources when no longer needed
radiation.deleteRadiationSource(temporary_source_id)
```

## Spectral Data Management

### Setting Source Spectra

```python
# Define custom spectrum (wavelength in nm, relative intensity)
sunlight_spectrum = [
    (300, 0.1), (400, 0.5), (500, 1.0),
    (600, 0.9), (700, 0.7), (800, 0.5)
]

# Set spectrum for single source
radiation.setSourceSpectrum(sun_source, sunlight_spectrum)

# Set spectrum for multiple sources
led_sources = [led1, led2, led3]
radiation.setSourceSpectrum(led_sources, led_spectrum)

# Use predefined spectrum from global data
radiation.setSourceSpectrum(source_id, "D65_illuminant")
```

### Spectrum Integration and Analysis

```python
# Define leaf reflectance spectrum
leaf_reflectance = [
    (400, 0.08), (500, 0.10), (550, 0.45),
    (600, 0.15), (650, 0.12), (700, 0.50),
    (750, 0.55), (800, 0.52)
]

# Basic integration (total)
total = radiation.integrateSpectrum(leaf_reflectance)
print(f"Total reflectance: {total}")

# Integration over PAR range (400-700nm)
par_reflectance = radiation.integrateSpectrum(leaf_reflectance, 400, 700)
print(f"PAR reflectance: {par_reflectance}")

# Integration weighted by source spectrum
source_weighted = radiation.integrateSpectrum(
    leaf_reflectance, 400, 700, source_id=sun_id
)

# Integration with camera spectral response
camera_response = [(400, 0.2), (550, 1.0), (700, 0.3)]
camera_weighted = radiation.integrateSpectrum(
    leaf_reflectance, camera_spectrum=camera_response
)

# Integrate source spectrum directly
sun_par_flux = radiation.integrateSourceSpectrum(sun_id, 400, 700)
print(f"Sun PAR flux: {sun_par_flux} W/m²")
```

### Spectrum Normalization

```python
# Set spectrum integral (normalizes spectrum to target value)
radiation.setSourceSpectrumIntegral(source_id, 1000.0)  # Total = 1000 W/m²

# Set integral over specific wavelength range (PAR)
radiation.setSourceSpectrumIntegral(source_id, 500.0, 400, 700)  # PAR = 500 W/m²
```

### Spectrum Manipulation

```python
# Scale existing spectrum in-place
radiation.scaleSpectrum("leaf_reflectance", 1.2)  # Increase by 20%

# Create new scaled spectrum
radiation.scaleSpectrum("leaf_reflectance", "bright_leaf", 1.5)

# Random scaling for stochastic simulations
radiation.scaleSpectrumRandomly("base_leaf", "variant_leaf", 0.8, 1.2)

# Blend multiple spectra with weights
radiation.blendSpectra(
    new_label="mixed_leaf",
    spectrum_labels=["young_leaf", "mature_leaf", "old_leaf"],
    weights=[0.2, 0.5, 0.3]
)

# Random blending
radiation.blendSpectraRandomly(
    new_label="random_canopy",
    spectrum_labels=["leaf_type_a", "leaf_type_b", "leaf_type_c"]
)
```

## Diffuse Radiation

### Directionally-Biased Diffuse Radiation

```python
# Set diffuse radiation with extinction coefficient and peak direction
radiation.addRadiationBand("SW")
radiation.setDiffuseRadiationFlux("SW", 200.0)

# Sky radiation peaked at zenith
from pyhelios.types import vec3
radiation.setDiffuseRadiationExtinctionCoeff(
    label="SW",
    K=0.5,                    # Extinction coefficient
    peak_direction=vec3(0, 0, 1)  # Zenith direction
)

# Or use spherical coordinates
from pyhelios.types import SphericalCoord
radiation.setDiffuseRadiationExtinctionCoeff(
    label="SW",
    K=0.3,
    peak_direction=SphericalCoord(1.0, 45.0, 90.0)
)

# Query diffuse flux
diffuse_flux = radiation.getDiffuseFlux("SW")
print(f"Diffuse flux: {diffuse_flux} W/m²")
```

### Diffuse Spectrum Configuration

```python
# Set diffuse spectrum from global data
radiation.setDiffuseSpectrum("SW", "sky_spectrum")

# Set for multiple bands
radiation.setDiffuseSpectrum(["SW", "NIR"], "atmospheric_spectrum")

# Set diffuse spectrum integral (all bands)
radiation.setDiffuseSpectrumIntegral(1000.0)

# Set integral with wavelength range
radiation.setDiffuseSpectrumIntegral(500.0, 400, 700)

# Set integral for specific band
radiation.setDiffuseSpectrumIntegral(300.0, band_label="PAR")
radiation.setDiffuseSpectrumIntegral(200.0, 400, 700, band_label="PAR")
```

## Spectral Interpolation

### Primitive-Based Spectral Assignment

```python
# Automatically assign spectra based on primitive data values
leaf_patches = context.getAllUUIDs("patch")

# Assign leaf reflectance based on age
radiation.interpolateSpectrumFromPrimitiveData(
    primitive_uuids=leaf_patches,
    spectra_labels=["young_leaf_spectrum", "mature_leaf_spectrum", "old_leaf_spectrum"],
    values=[0.0, 50.0, 100.0],  # Days since emergence
    primitive_data_query_label="leaf_age",
    primitive_data_radprop_label="reflectance"
)

# Assign based on nitrogen content
radiation.interpolateSpectrumFromPrimitiveData(
    primitive_uuids=leaf_patches,
    spectra_labels=["low_n_leaf", "medium_n_leaf", "high_n_leaf"],
    values=[0.5, 2.0, 4.0],  # % nitrogen
    primitive_data_query_label="nitrogen_percent",
    primitive_data_radprop_label="reflectance"
)
```

### Object-Based Spectral Assignment

```python
# Assign spectra based on object-level data
tree_ids = [tree1_id, tree2_id, tree3_id]

radiation.interpolateSpectrumFromObjectData(
    object_ids=tree_ids,
    spectra_labels=["healthy_tree", "stressed_tree", "diseased_tree"],
    values=[1.0, 0.5, 0.0],  # Health index (0-1)
    object_data_query_label="health_index",
    primitive_data_radprop_label="reflectance"
)
```

## Camera Management

### Dynamic Camera Control

```python
from pyhelios.types import vec3, SphericalCoord

# Create camera
radiation.addRadiationCamera("cam1", ["red", "green", "blue"],
                           position=vec3(0, 0, 10),
                           lookat_or_direction=vec3(0, 0, 0))

# Reposition camera dynamically
radiation.setCameraPosition("cam1", vec3(5, 5, 15))
position = radiation.getCameraPosition("cam1")
print(f"Camera at: {position}")

# Update camera target
radiation.setCameraLookat("cam1", vec3(2, 2, 0))
lookat = radiation.getCameraLookat("cam1")
print(f"Camera looking at: {lookat}")

# Set camera orientation
radiation.setCameraOrientation("cam1", vec3(0, 0, 1))  # Look down
orientation = radiation.getCameraOrientation("cam1")
print(f"Camera orientation: {orientation}")

# Query all cameras
cameras = radiation.getAllCameraLabels()
print(f"Available cameras: {cameras}")
```

### Camera Spectral Response

```python
# Set custom camera spectral response
radiation.setCameraSpectralResponse("cam1", "red", "custom_red_response")

# Use standard camera models
radiation.setCameraSpectralResponseFromLibrary("cam1", "iPhone13")
radiation.setCameraSpectralResponseFromLibrary("cam2", "NikonD850")
radiation.setCameraSpectralResponseFromLibrary("cam3", "CanonEOS5D")

# Available camera models: iPhone13, NikonD850, CanonEOS5D, and more
```

### Programmatic Pixel Access

```python
# Get raw pixel data
pixels = radiation.getCameraPixelData("cam1", "red")
print(f"Image size: {len(pixels)} pixels")
print(f"Mean intensity: {sum(pixels)/len(pixels)}")

# Modify pixels programmatically
enhanced_pixels = [p * 1.3 for p in pixels]  # Brighten by 30%
radiation.setCameraPixelData("cam1", "red", enhanced_pixels)

# Apply custom image processing
import numpy as np
pixel_array = np.array(pixels)
filtered = apply_custom_filter(pixel_array)
radiation.setCameraPixelData("cam1", "red", filtered.tolist())
```

## Advanced Simulation Features

### Periodic Boundary Conditions

```python
# Enable periodic boundaries for large-scale simulations
radiation.enforcePeriodicBoundary("xy")   # Periodic in x and y
radiation.enforcePeriodicBoundary("xyz")  # Periodic in all dimensions
radiation.enforcePeriodicBoundary("x")    # Periodic in x only
```

### G-Function Calculation

```python
# Calculate geometry factor for canopy radiation modeling
from pyhelios.types import vec3

# Vertical view
g_vertical = radiation.calculateGtheta(vec3(0, 0, 1))
print(f"G-function (vertical): {g_vertical}")

# Oblique view
g_oblique = radiation.calculateGtheta(vec3(0.5, 0.5, 0.7))
print(f"G-function (oblique): {g_oblique}")

# Horizontal view
g_horizontal = radiation.calculateGtheta(vec3(1, 0, 0))
print(f"G-function (horizontal): {g_horizontal}")
```

### Sky Energy and Optional Outputs

```python
# Get total sky energy
sky_energy = radiation.getSkyEnergy()
print(f"Sky energy: {sky_energy} W")

# Enable optional primitive data outputs
radiation.optionalOutputPrimitiveData("temperature")
radiation.optionalOutputPrimitiveData("absorbed_PAR")
radiation.optionalOutputPrimitiveData("transmitted_flux")
```

## Spectral Modeling Workflows

### Realistic Sunlight Modeling

```python
# Create realistic solar spectrum
solar_spectrum = [
    (300, 0.05), (350, 0.15), (400, 0.35), (450, 0.65),
    (500, 0.90), (550, 1.00), (600, 0.95), (650, 0.85),
    (700, 0.75), (750, 0.70), (800, 0.65), (900, 0.55)
]

# Add sun source
sun_id = radiation.addSunSphereRadiationSource(
    radius=1.0, zenith=30.0, azimuth=180.0
)

# Set solar spectrum
radiation.setSourceSpectrum(sun_id, solar_spectrum)

# Normalize to total solar irradiance (1000 W/m²)
radiation.setSourceSpectrumIntegral(sun_id, 1000.0)

# Or normalize just PAR component to 500 W/m²
radiation.setSourceSpectrumIntegral(sun_id, 500.0, 400, 700)
```

### Multi-Spectral Leaf Modeling

```python
# Define leaf spectra at different developmental stages
young_leaf = [(400, 0.08), (550, 0.40), (700, 0.45), (800, 0.50)]
mature_leaf = [(400, 0.10), (550, 0.45), (700, 0.50), (800, 0.55)]
old_leaf = [(400, 0.06), (550, 0.30), (700, 0.35), (800, 0.40)]

# Create interpolated spectra for intermediate ages
for age in [10, 20, 30, 40]:
    radiation.scaleSpectrum(
        "young_leaf",
        f"leaf_age_{age}",
        scale_factor=1.0 + (age / 100.0)
    )

# Generate stochastic leaf variations
for i in range(100):
    radiation.scaleSpectrumRandomly(
        "mature_leaf",
        f"leaf_variant_{i}",
        min_scale=0.85,
        max_scale=1.15
    )
```

### Canopy Spectral Diversity

```python
# Get all leaf patches
leaf_patches = context.getAllUUIDs("patch")

# Assign spectra based on canopy height
radiation.interpolateSpectrumFromPrimitiveData(
    primitive_uuids=leaf_patches,
    spectra_labels=["upper_canopy", "middle_canopy", "lower_canopy"],
    values=[15.0, 8.0, 2.0],  # Height thresholds (meters)
    primitive_data_query_label="height",
    primitive_data_radprop_label="reflectance"
)

# Mix leaf types for realistic heterogeneity
radiation.blendSpectra(
    new_label="canopy_average",
    spectrum_labels=["sunlit_leaf", "shaded_leaf"],
    weights=[0.3, 0.7]  # 30% sunlit, 70% shaded
)
```

## Multi-View Camera Imaging

### Time-Series Camera Capture

```python
from pyhelios.types import vec3

# Set up camera
radiation.addRadiationCamera("timelapse", ["red", "green", "blue"],
                           position=vec3(0, 0, 20),
                           lookat_or_direction=vec3(0, 0, 0))

# Capture from multiple viewpoints
viewpoints = [
    vec3(10, 0, 15), vec3(0, 10, 15),
    vec3(-10, 0, 15), vec3(0, -10, 15)
]

for i, viewpoint in enumerate(viewpoints):
    # Move camera
    radiation.setCameraPosition("timelapse", viewpoint)

    # Update lookat to track target
    radiation.setCameraLookat("timelapse", vec3(0, 0, 5))

    # Capture image
    radiation.writeCameraImage(
        "timelapse", ["red", "green", "blue"],
        f"view_{i}", frame=i
    )
```

### Multi-Spectral Imaging with Standard Cameras

```python
# Create camera with iPhone 13 spectral response
radiation.addRadiationCamera("iphone_cam", ["red", "green", "blue"],
                           position=vec3(0, 0, 10),
                           lookat_or_direction=vec3(0, 0, 0))

radiation.setCameraSpectralResponseFromLibrary("iphone_cam", "iPhone13")

# Create camera with professional DSLR response
radiation.addRadiationCamera("dslr_cam", ["red", "green", "blue"],
                           position=vec3(5, 0, 10),
                           lookat_or_direction=vec3(0, 0, 0))

radiation.setCameraSpectralResponseFromLibrary("dslr_cam", "NikonD850")

# Run simulation and compare
radiation.runBand(["red", "green", "blue"])

iphone_img = radiation.writeCameraImage("iphone_cam", ["red", "green", "blue"], "iphone")
dslr_img = radiation.writeCameraImage("dslr_cam", ["red", "green", "blue"], "dslr")
```

## Advanced Workflows

### Growth Simulation with Spectral Changes

```python
# Simulate plant growth over 100 days
for day in range(100):
    # Update leaf age data
    leaf_patches = context.getAllUUIDs("patch")
    for patch_id in leaf_patches:
        current_age = context.getPrimitiveData(patch_id, "age")[0]
        context.setPrimitiveData(patch_id, "age", current_age + 1.0)

    # Interpolate spectra based on updated ages
    radiation.interpolateSpectrumFromPrimitiveData(
        primitive_uuids=leaf_patches,
        spectra_labels=["juvenile", "mature", "senescent"],
        values=[0.0, 50.0, 100.0],
        primitive_data_query_label="age",
        primitive_data_radprop_label="reflectance"
    )

    # Run radiation simulation
    radiation.runBand("PAR")

    # Analyze results
    flux = radiation.getTotalAbsorbedFlux()
    daily_radiation[day] = sum(flux)
```

### Multi-Source Lighting Scenarios

```python
# Create complex lighting setup
# Natural sunlight
sun = radiation.addSunSphereRadiationSource(1.0, 45.0, 180.0)
radiation.setSourceFlux(sun, "PAR", 600.0)

# Supplemental LED grow lights (rectangular panels)
led1 = radiation.addRectangleRadiationSource(
    position=vec3(-3, 0, 4), size=vec2(1, 2), rotation=vec3(0, 0, 0)
)
led2 = radiation.addRectangleRadiationSource(
    position=vec3(3, 0, 4), size=vec2(1, 2), rotation=vec3(0, 0, 0)
)

# LED spectrum (red-blue for photosynthesis)
led_spectrum = [
    (400, 0.0), (450, 0.8), (500, 0.2),
    (600, 0.1), (660, 1.0), (700, 0.0)
]

radiation.setSourceSpectrum([led1, led2], led_spectrum)
radiation.setSourceFlux([led1, led2], "PAR", 200.0)

# Run combined natural + artificial lighting
radiation.runBand("PAR")
```

### Quality Control with Source Position Tracking

```python
# Query and verify source positions
all_cameras = radiation.getAllCameraLabels()
print(f"Configured cameras: {all_cameras}")

# Get source positions for verification
for source_id in [sun, led1, led2]:
    pos = radiation.getSourcePosition(source_id)
    print(f"Source {source_id} at: {pos}")

# Verify band configuration
bands = ["PAR", "NIR", "SW"]
for band in bands:
    if radiation.doesBandExist(band):
        flux = radiation.getDiffuseFlux(band)
        print(f"{band}: {flux} W/m² diffuse")
```

## Complete Workflow Example

```python
from pyhelios import Context, WeberPennTree, WPTType, RadiationModel
from pyhelios.exceptions import RadiationModelError
from pyhelios.types import *

try:
    # Create scene
    context = Context()

    # Add ground plane
    ground_uuid = context.addPatch(
        center=vec3(0, 0, 0),
        size=vec2(10, 10),
        color=RGBcolor(0.3, 0.2, 0.1)
    )

    # Generate tree
    wpt = WeberPennTree(context)
    tree_id = wpt.buildTree(WPTType.LEMON)

    # Run radiation simulation
    with RadiationModel(context) as radiation:
        # Configure multiple radiation bands for comprehensive analysis
        radiation.addRadiationBand("PAR")  # Photosynthetically Active Radiation
        radiation.addRadiationBand("NIR")  # Near Infrared
        radiation.addRadiationBand("SW")   # Total Shortwave
        
        # Add sun
        sun_id = radiation.addSunSphereRadiationSource(
            radius=0.5,
            zenith=30.0,    # Morning sun
            azimuth=135.0   # Southeast
        )
        
        # Configure sources for all bands
        radiation.setSourceFlux(sun_id, "PAR", 600.0)  # W/m² PAR
        radiation.setSourceFlux(sun_id, "NIR", 500.0)  # W/m² NIR  
        radiation.setSourceFlux(sun_id, "SW", 1200.0)  # W/m² Total SW
        
        # Add diffuse sky radiation for all bands
        radiation.setDiffuseRadiationFlux("PAR", 100.0)
        radiation.setDiffuseRadiationFlux("NIR", 80.0)
        radiation.setDiffuseRadiationFlux("SW", 200.0)
        
        # Configure simulation quality for all bands
        for band in ["PAR", "NIR", "SW"]:
            radiation.setDirectRayCount(band, 2000)
            radiation.setDiffuseRayCount(band, 6000)
            radiation.setScatteringDepth(band, 2)
        
        # Run simulation - EFFICIENT multi-band execution
        radiation.updateGeometry()
        radiation.runBand(["PAR", "NIR", "SW"])  # Single call for all bands!
        
        # Analyze results
        results = radiation.getTotalAbsorbedFlux()
        
        # Get leaf-specific results
        leaf_uuids = wpt.getLeafUUIDs(tree_id)
        leaf_absorption = 0
        
        all_uuids = context.getAllUUIDs()
        for i, uuid in enumerate(all_uuids):
            if uuid in leaf_uuids and i < len(results):
                leaf_absorption += results[i]
        
        print(f"Total scene absorption: {sum(results):.2f} W")
        print(f"Leaf absorption: {leaf_absorption:.2f} W")
        print(f"Ground absorption: {results[all_uuids.index(ground_uuid)]:.2f} W")
        
        # Access band-specific data stored by radiation model
        for band in ["PAR", "NIR", "SW"]:
            print(f"Band {band} results available in primitive data: radiation_flux_{band}")

except RadiationModelError as e:
    print(f"Radiation modeling failed: {e}")
    print("Ensure GPU with Vulkan support is available (or NVIDIA GPU with CUDA/OptiX)")
    print("Check that radiation plugin is compiled: build_scripts/build_helios --plugins radiation")
except Exception as e:
    print(f"Simulation setup failed: {e}")
    print("Check geometry creation and tree generation parameters")
```

### Data Storage

```python
# Store radiation results as primitive data
results = radiation.getTotalAbsorbedFlux()
all_uuids = context.getAllUUIDs()

for i, uuid in enumerate(all_uuids):
    if i < len(results):
        # Store flux data
        context.setPrimitiveDataFloat(uuid, "radiation_flux_PAR", results[i])
        
        # Calculate flux density
        area = context.getPrimitiveArea(uuid)
        flux_density = results[i] / area if area > 0 else 0
        context.setPrimitiveDataFloat(uuid, "flux_density_PAR", flux_density)

# Use for visualization
context.colorPrimitiveByDataPseudocolor(
    all_uuids, "flux_density_PAR", "hot", 256
)
```

## Camera and Image Functions

> **Note**: Camera functions are available in Helios core v1.3.47+ and PyHelios v0.0.4+

The RadiationModel now includes advanced camera functionality for generating synthetic images, object detection training data, and auto-calibrated imagery.

### Camera Image Generation

```python
# Basic camera image writing (returns output filename)
filename = radiation.writeCameraImage(
    camera="overhead_camera",
    bands=["Red", "Green", "Blue"],
    imagefile_base="scene_rgb",
    image_path="./images",
    frame=-1  # All frames
)
print(f"Camera image saved to: {filename}")

# Normalized camera images  
filename = radiation.writeNormCameraImage(
    camera="side_camera",
    bands=["NIR", "Red"], 
    imagefile_base="false_color",
    image_path="./output"
)

# Camera image data in ASCII format
radiation.writeCameraImageData(
    camera="overhead_camera",
    band="RGB",
    imagefile_base="raw_data",
    image_path="./data"
)

# Camera image data in EXR format (lossless float precision, v1.3.66+)
radiation.writeCameraImageDataEXR(
    camera="overhead_camera",
    band="PAR",                    # Single band
    imagefile_base="raw_float_data",
    image_path="./data"
)

# Multi-band EXR (all bands as separate channels in one file)
radiation.writeCameraImageDataEXR(
    camera="overhead_camera",
    band=["Red", "Green", "Blue"],  # Multiple bands
    imagefile_base="rgb_float_data",
    image_path="./data"
)
```

### Depth Image Export

```python
# Depth image as ASCII text file
radiation.writeDepthImageData(
    camera_label="overhead_camera",
    imagefile_base="depth_data",
    image_path="./data"
)

# Depth image as EXR file (lossless float precision, v1.3.66+)
radiation.writeDepthImageDataEXR(
    camera_label="overhead_camera",
    imagefile_base="depth_float",
    image_path="./data"
)

# Normalized depth image (grayscale JPEG for visualization)
radiation.writeNormDepthImage(
    camera_label="overhead_camera",
    imagefile_base="depth_visual",
    max_depth=50.0,  # Maximum depth for normalization
    image_path="./data"
)
```

### Object Detection Training Data

Generate YOLO-format bounding boxes for machine learning training:

```python
# Single primitive data label
radiation.writeImageBoundingBoxes(
    camera_label="training_camera",
    primitive_data_labels="leaf_type",
    object_class_ids=1,  # Class ID for "leaf"
    image_file="training_001.jpg",
    classes_txt_file="plant_classes.txt",
    image_path="./annotations"
)

# Multiple primitive data labels for multi-class detection
radiation.writeImageBoundingBoxes(
    camera_label="training_camera", 
    primitive_data_labels=["leaves", "stems", "fruits"],
    object_class_ids=[0, 1, 2],  # Different class IDs
    image_file="training_002.jpg",
    classes_txt_file="classes.txt"
)

# Object-based bounding boxes (entire objects)
radiation.writeImageBoundingBoxes(
    camera_label="training_camera",
    object_data_labels=["tree_1", "tree_2", "shrub_1"], 
    object_class_ids=[10, 10, 20],  # Tree class=10, Shrub class=20
    image_file="training_003.jpg"
)
```

### Segmentation Masks for Instance Segmentation

Generate COCO-format JSON files for semantic/instance segmentation:

```python
# Single primitive segmentation
radiation.writeImageSegmentationMasks(
    camera_label="segmentation_camera",
    primitive_data_labels="plant_part",
    object_class_ids=1,
    json_filename="segmentation_001.json",
    image_file="seg_image_001.jpg",
    append_file=False
)

# Multiple primitive classes in one image
radiation.writeImageSegmentationMasks(
    camera_label="segmentation_camera",
    primitive_data_labels=["leaf", "bark", "soil"],
    object_class_ids=[1, 2, 3],
    json_filename="multi_class_seg.json", 
    image_file="scene_segmentation.jpg",
    append_file=True  # Add to existing annotations
)

# Object-level segmentation
radiation.writeImageSegmentationMasks(
    camera_label="segmentation_camera",
    object_data_labels=["individual_plant_1", "individual_plant_2"],
    object_class_ids=[100, 101],  # Unique instance IDs
    json_filename="instance_segmentation.json",
    image_file="plant_instances.jpg"
)
```

### Auto-Calibrated Camera Images

Automatic color correction for realistic imagery:

```python
# Basic auto-calibration with default settings
filename = radiation.autoCalibrateCameraImage(
    camera_label="rgb_camera",
    red_band_label="Red",
    green_band_label="Green", 
    blue_band_label="Blue",
    output_file_path="auto_calibrated_image.jpg"
)

# Advanced auto-calibration with quality report
filename = radiation.autoCalibrateCameraImage(
    camera_label="multispectral_camera",
    red_band_label="Band_670nm",
    green_band_label="Band_550nm",
    blue_band_label="Band_450nm", 
    output_file_path="calibrated_multispectral.jpg",
    print_quality_report=True,
    algorithm="MATRIX_3X3_AUTO",  # or "DIAGONAL_ONLY", "MATRIX_3X3_FORCE"
    ccm_export_file_path="color_correction_matrix.txt"
)
print(f"Calibrated image saved to: {filename}")
```

### Color Correction Algorithms

Choose the appropriate algorithm based on your needs:

```python
algorithms = {
    "DIAGONAL_ONLY": "Simple white balance correction (fastest)",
    "MATRIX_3X3_AUTO": "Full 3x3 matrix with stability fallback (recommended)",
    "MATRIX_3X3_FORCE": "Force 3x3 matrix even if potentially unstable"
}

# Test different algorithms
for algorithm, description in algorithms.items():
    filename = radiation.autoCalibrateCameraImage(
        camera_label="test_camera",
        red_band_label="R", green_band_label="G", blue_band_label="B",
        output_file_path=f"calibrated_{algorithm.lower()}.jpg",
        algorithm=algorithm
    )
    print(f"{algorithm}: {description} -> {filename}")
```

### Complete Camera Pipeline Example

```python
from pyhelios import Context, WeberPennTree, WPTType, RadiationModel
from pyhelios.exceptions import RadiationModelError
from pyhelios.types import *

# Create scene with labeled geometry
context = Context()

# Generate tree with data labels
wpt = WeberPennTree(context)
tree_id = wpt.buildTree(WPTType.APPLE)

# Label tree components for ML training
leaf_uuids = wpt.getLeafUUIDs(tree_id)
branch_uuids = wpt.getBranchUUIDs(tree_id)

for uuid in leaf_uuids:
    context.setPrimitiveDataString(uuid, "plant_part", "leaf")
    context.setPrimitiveDataString(uuid, "species", "apple")
    
for uuid in branch_uuids:
    context.setPrimitiveDataString(uuid, "plant_part", "branch") 
    context.setPrimitiveDataString(uuid, "species", "apple")

# Add ground with labels
ground = context.addPatch(center=vec3(0,0,0), size=vec2(10,10))
context.setPrimitiveDataString(ground, "plant_part", "soil")

# Run radiation simulation with cameras
try:
    with RadiationModel(context) as radiation:
        # Set up radiation bands
        radiation.addRadiationBand("Red")
        radiation.addRadiationBand("Green") 
        radiation.addRadiationBand("Blue")
        radiation.addRadiationBand("NIR")
        
        # Add sun source
        sun_id = radiation.addSunSphereRadiationSource(
            radius=0.5, zenith=45.0, azimuth=180.0)
        
        # Configure realistic solar spectrum
        radiation.setSourceFlux(sun_id, "Red", 250.0)
        radiation.setSourceFlux(sun_id, "Green", 350.0)
        radiation.setSourceFlux(sun_id, "Blue", 200.0)
        radiation.setSourceFlux(sun_id, "NIR", 400.0)
        
        # Run simulation
        radiation.updateGeometry()
        radiation.runBand(["Red", "Green", "Blue", "NIR"])
        
        # Generate camera images
        rgb_filename = radiation.writeCameraImage(
            camera="overhead_rgb",
            bands=["Red", "Green", "Blue"],
            imagefile_base="apple_tree_rgb"
        )
        
        nir_filename = radiation.writeCameraImage(
            camera="side_view", 
            bands=["NIR"],
            imagefile_base="apple_tree_nir"
        )
        
        # Generate training data for object detection
        radiation.writeImageBoundingBoxes(
            camera_label="overhead_rgb",
            primitive_data_labels=["leaf", "branch", "soil"],
            object_class_ids=[0, 1, 2],  # leaf=0, branch=1, soil=2
            image_file=rgb_filename,
            classes_txt_file="plant_classes.txt"
        )
        
        # Generate segmentation masks 
        radiation.writeImageSegmentationMasks(
            camera_label="overhead_rgb",
            primitive_data_labels=["leaf", "branch", "soil"],
            object_class_ids=[0, 1, 2],
            json_filename="apple_tree_segmentation.json",
            image_file=rgb_filename
        )
        
        # Create auto-calibrated realistic image
        calibrated_filename = radiation.autoCalibrateCameraImage(
            camera_label="overhead_rgb",
            red_band_label="Red",
            green_band_label="Green", 
            blue_band_label="Blue",
            output_file_path="apple_tree_calibrated.jpg",
            print_quality_report=True
        )
        
        print("Camera pipeline completed:")
        print(f"  RGB Image: {rgb_filename}")
        print(f"  NIR Image: {nir_filename}") 
        print(f"  Calibrated: {calibrated_filename}")
        print(f"  Training data: plant_classes.txt + YOLO format labels")
        print(f"  Segmentation: apple_tree_segmentation.json")
        
except RadiationModelError as e:
    print(f"Camera processing failed: {e}")
```

### Camera Function Error Handling

```python
try:
    # Camera functions with comprehensive error handling
    filename = radiation.writeCameraImage(
        camera="test_camera",
        bands=["R", "G", "B"],
        imagefile_base="test"
    )
    
except TypeError as e:
    print(f"Parameter error: {e}")
    # Handle invalid parameter types
    
except ValueError as e:
    print(f"Value error: {e}")  
    # Handle invalid parameter values (e.g., both primitive and object labels)
    
except RuntimeError as e:
    print(f"Camera operation failed: {e}")
    # Handle camera or image generation failures
```

## Error Handling

```python
from pyhelios import RadiationModel
from pyhelios.exceptions import HeliosGPUInitializationError

# Check GPU availability before creating RadiationModel
if not RadiationModel.probeAnyGPUBackend():
    print("No compatible GPU backend found")
    print("Supported backends: OptiX 8 (NVIDIA driver >= 560), OptiX 6 (NVIDIA driver < 560), Vulkan")

try:
    radiation = RadiationModel(context)
    print(f"Using backend: {radiation.getBackendName()}")

except Exception as e:
    print(f"RadiationModel initialization failed: {e}")

    # Runtime backend probing provides clear diagnostic messages
    if "Vulkan" in str(e):
        print("Vulkan backend error - check GPU drivers")
        print("  macOS: brew install vulkan-loader molten-vk")
        print("  Linux: sudo apt-get install libvulkan-dev")
        print("  Windows: No additional packages needed")
    elif "OptiX" in str(e):
        print("OptiX backend error - check CUDA/OptiX installation and NVIDIA drivers")
    elif "GPU" in str(e):
        print(f"GPU initialization failed: {e}")
```

## Build Requirements

```bash
# Build with radiation plugin
build_scripts/build_helios --plugins radiation

# Or use GPU profile
build_scripts/build_helios --plugins radiation

# Check if radiation is available
python -c "from pyhelios.plugins import get_plugin_registry; print(get_plugin_registry().is_plugin_available('radiation'))"
```

This documentation covers the actual RadiationModel implementation in PyHelios, verified against the wrapper code and high-level interface.