# Radiation Model Plugin {#RadiationDoc}

The Radiation Model plugin provides GPU-accelerated ray tracing for radiation simulation using OptiX. This documentation is based on the actual implementation.

## Overview

The \ref pyhelios.RadiationModel.RadiationModel "RadiationModel class" provides advanced radiation modeling and ray tracing capabilities for realistic light interaction simulations in plant canopies and scenes.

## Requirements

The radiation plugin requires:
- NVIDIA GPU with CUDA support
- CUDA Toolkit installed
- OptiX runtime (bundled with PyHelios)

## Basic Usage

```python
from pyhelios import Context, RadiationModel, RadiationModelError
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

# Source with specific direction vector
source_id = radiation.addCollimatedRadiationSource(
    direction=(0.3, 0.3, -0.9)  # Sun angle
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
radiation.setSourceFluxMultiple(source_ids, "PAR", 800.0)

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

```python
# Run single band
radiation.runBand("PAR")

# Run multiple bands
radiation.runBand(["PAR", "NIR", "SW"])
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

## Complete Workflow Example

```python
from pyhelios import Context, WeberPennTree, WPTType, RadiationModel
from pyhelios.types import *

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
try:
    with RadiationModel(context) as radiation:
        # Configure radiation
        radiation.addRadiationBand("PAR")
        
        # Add sun
        sun_id = radiation.addSunSphereRadiationSource(
            radius=0.5,
            zenith=30.0,    # Morning sun
            azimuth=135.0   # Southeast
        )
        radiation.setSourceFlux(sun_id, "PAR", 1200.0)
        
        # Add diffuse sky radiation
        radiation.setDiffuseRadiationFlux("PAR", 200.0)
        
        # Configure simulation quality
        radiation.setDirectRayCount("PAR", 2000)
        radiation.setDiffuseRayCount("PAR", 6000)
        radiation.setScatteringDepth("PAR", 2)
        
        # Run simulation
        radiation.updateGeometry()
        radiation.runBand("PAR")
        
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
        
except RadiationModelError as e:
    print(f"Radiation simulation failed: {e}")
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

## Error Handling

```python
from pyhelios.exceptions import HeliosGPUInitializationError

try:
    radiation = RadiationModel(context)
    
except RadiationModelError as e:
    print(f"RadiationModel initialization failed: {e}")
    
    # Check if GPU is available
    if "NVIDIA GPU" in str(e):
        print("Ensure NVIDIA GPU with CUDA support is available")
    elif "OptiX" in str(e):
        print("OptiX runtime error - check graphics drivers")
        
except HeliosGPUInitializationError as e:
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