# Visualizer Plugin {#VisualizerDoc}

The Visualizer plugin provides OpenGL-based 3D visualization and rendering capabilities. This documentation is based on the actual implementation.

## Overview

The Visualizer class provides interactive 3D visualization of Helios scenes with real-time rendering, camera controls, and image export capabilities.

## Requirements

The visualizer plugin requires:
- OpenGL 3.3 or higher
- GLFW library for window management
- FreeType library for text rendering  
- Display/graphics drivers (X11 on Linux, native on Windows/macOS)

## Basic Usage

```python
from pyhelios import Context, Visualizer
from pyhelios.types import *

# Create context with geometry
context = Context()
patch_uuid = context.addPatch(
    center=vec3(0, 0, 0),
    size=vec2(2, 2),
    color=RGBcolor(0.3, 0.7, 0.2)
)

# Use Visualizer with context manager (recommended)
with Visualizer(width=1024, height=768) as visualizer:
    # Build scene geometry
    visualizer.buildContextGeometry(context)

    # Set up camera
    visualizer.setCameraPosition(
        position=vec3(5, 5, 5),
        lookAt=vec3(0, 0, 0)
    )

    # Configure scene
    visualizer.setBackgroundColor(RGBcolor(0.5, 0.7, 1.0))  # Sky blue
    visualizer.setLightingModel("phong")

    # Show interactive visualization
    visualizer.plotInteractive()
```

## Visualizer Creation

### Basic Initialization

```python
# Basic visualizer (verified constructor parameters)
visualizer = Visualizer(
    width=800, 
    height=600, 
    antialiasing_samples=1, 
    headless=False
)

# High-quality visualizer with antialiasing
visualizer = Visualizer(
    width=1920, 
    height=1080, 
    antialiasing_samples=8, 
    headless=False
)

# Headless mode for batch processing
visualizer = Visualizer(
    width=1024, 
    height=768, 
    antialiasing_samples=1, 
    headless=True
)
```

### Context Manager Usage

```python
# Recommended: use context manager for automatic cleanup
with Visualizer(1024, 768) as visualizer:
    # Visualization code here
    pass  # Automatic cleanup when done
```

## Geometry Loading

### Building Context Geometry

```python
# Load all geometry from context (verified method)
visualizer.buildContextGeometry(context)

# Load specific geometry UUIDs only
specific_uuids = [patch_uuid, triangle_uuid]
visualizer.buildContextGeometry(context, uuids=specific_uuids)
```

### Progressive Loading

```python
# Load geometry progressively for large scenes
all_uuids = context.getAllUUIDs()
batch_size = 1000

for i in range(0, len(all_uuids), batch_size):
    batch_uuids = all_uuids[i:i + batch_size]
    visualizer.buildContextGeometry(context, uuids=batch_uuids)
    print(f"Loaded batch {i//batch_size + 1}")
```

## Visualization Modes

### Interactive Visualization

```python
# Open interactive window (verified method)
visualizer.plotInteractive()

# Interactive controls available:
# - Mouse scroll: Zoom in/out
# - Left mouse + drag: Rotate camera
# - Right mouse + drag: Pan camera  
# - Arrow keys: Camera movement
# - +/- keys: Zoom in/out
```

### Non-Interactive Updates

```python
# Update visualization without interaction (verified method)
visualizer.plotUpdate()

# Useful for batch processing or animation sequences
for frame in range(100):
    
    # Update scene data here
    
    # Rebuild geometry if needed
    visualizer.buildContextGeometry(context)
    
    # Update visualization
    visualizer.plotUpdate()
    
    # Save frame
    visualizer.printWindow(f"frame_{frame:03d}.jpg")
```

## Camera Control

### Cartesian Camera Positioning

```python
# Set camera position using Cartesian coordinates (verified method)
visualizer.setCameraPosition(
    position=vec3(10, 10, 10),  # Camera position
    lookAt=vec3(0, 0, 0)        # Look-at point
)

# Top-down view
visualizer.setCameraPosition(
    position=vec3(0, 0, 20),
    lookAt=vec3(0, 0, 0)
)

# Side view
visualizer.setCameraPosition(
    position=vec3(20, 0, 5),
    lookAt=vec3(0, 0, 5)
)
```

### Spherical Camera Positioning

```python
# Set camera position using spherical coordinates (verified method)
visualizer.setCameraPositionSpherical(
    angle=SphericalCoord(15, 0.785, 1.57),  # [radius, elevation, azimuth] in radians
    lookAt=vec3(0, 0, 0)                    # Look-at point
)

# Orbit around scene
import math
for angle in range(0, 360, 10):
    azimuth = math.radians(angle)
    visualizer.setCameraPositionSpherical(
        angle=SphericalCoord(20, math.pi/4, azimuth),  # Fixed radius and elevation
        lookAt=vec3(0, 0, 0)
    )
    visualizer.plotUpdate()
    visualizer.printWindow(f"orbit_{angle:03d}.jpg")
```

### Camera Animation

```python
# Smooth camera animation
def animate_camera(visualizer, start_pos, end_pos, frames=30):
    for i in range(frames):
        # Linear interpolation
        t = i / (frames - 1)
        current_pos = vec3(
            start_pos.x + t * (end_pos.x - start_pos.x),
            start_pos.y + t * (end_pos.y - start_pos.y),
            start_pos.z + t * (end_pos.z - start_pos.z)
        )

        visualizer.setCameraPosition(current_pos, vec3(0, 0, 0))
        visualizer.plotUpdate()
        visualizer.printWindow(f"camera_anim_{i:03d}.jpg")

# Use the animation
start = vec3(20, 0, 10)
end = vec3(0, 20, 10)
animate_camera(visualizer, start, end)
```

## Scene Configuration

### Background and Lighting

```python
# Set background color (verified method)
visualizer.setBackgroundColor(RGBcolor(0.2, 0.3, 0.5))  # Dark blue
visualizer.setBackgroundColor(RGBcolor(1.0, 1.0, 1.0))  # White
visualizer.setBackgroundColor(RGBcolor(0.0, 0.0, 0.0))  # Black

# Set light direction (verified method)
visualizer.setLightDirection(vec3(0.5, 0.5, -1.0))  # Directional light

# Configure lighting model (verified method and constants)
visualizer.setLightingModel(0)              # No lighting
visualizer.setLightingModel(1)              # Phong shading  
visualizer.setLightingModel(2)              # Phong with shadows
visualizer.setLightingModel("none")         # String equivalent
visualizer.setLightingModel("phong")        # String equivalent
visualizer.setLightingModel("phong_shadowed")  # String equivalent
```

### Lighting Scenarios

```python
# Outdoor daylight
visualizer.setBackgroundColor(RGBcolor(0.5, 0.7, 1.0))     # Sky blue
visualizer.setLightDirection(vec3(0.3, 0.3, -0.9))         # Sun direction
visualizer.setLightingModel("phong_shadowed")               # Realistic shadows

# Indoor studio lighting
visualizer.setBackgroundColor(RGBcolor(0.1, 0.1, 0.1))     # Dark background
visualizer.setLightDirection(vec3(0.0, 0.0, -1.0))         # Top-down light
visualizer.setLightingModel("phong")                        # Clean lighting

# Technical/CAD view
visualizer.setBackgroundColor(RGBcolor(0.9, 0.9, 0.9))     # Light gray
visualizer.setLightDirection(vec3(0.577, 0.577, -0.577))   # Isometric
visualizer.setLightingModel("phong")                        # Even lighting
```

### Data Visualization

The visualizer can color primitives based on data values, enabling visualization of simulation results, measurements, or other quantitative data.

```python
from pyhelios import Context, Visualizer
from pyhelios.types import *

# Create context with geometry and data
context = Context()
patch1 = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
patch2 = context.addPatch(center=vec3(2, 0, 0), size=vec2(1, 1))
patch3 = context.addPatch(center=vec3(4, 0, 0), size=vec2(1, 1))

# Set data values on primitives
context.setPrimitiveDataFloat(patch1, "temperature", 20.5)  # Cool
context.setPrimitiveDataFloat(patch2, "temperature", 25.0)  # Moderate
context.setPrimitiveDataFloat(patch3, "temperature", 30.2)  # Warm

# Set additional data for different visualizations
context.setPrimitiveDataFloat(patch1, "radiation_flux_SW", 150.0)
context.setPrimitiveDataFloat(patch2, "radiation_flux_SW", 200.0)
context.setPrimitiveDataFloat(patch3, "radiation_flux_SW", 175.5)

with Visualizer(800, 600) as visualizer:
    visualizer.buildContextGeometry(context)
    
    # Color all primitives by temperature data
    visualizer.colorContextPrimitivesByData("temperature")
    visualizer.plotUpdate()
    
    # Color all primitives by radiation data
    visualizer.colorContextPrimitivesByData("radiation_flux_SW")
    visualizer.plotUpdate()
    
    # Color only specific primitives
    visualizer.colorContextPrimitivesByData("temperature", [patch1, patch3])
    visualizer.plotUpdate()
```

#### Advanced Data Visualization

```python
# Complete radiation visualization workflow
from pyhelios import Context, RadiationModel, Visualizer
from pyhelios.types import *

context = Context()

# Create a simple plant structure
for i in range(10):
    for j in range(10):
        leaf_uuid = context.addPatch(
            center=vec3(i * 0.5, j * 0.5, 2.0),
            size=vec2(0.4, 0.4),
            color=RGBcolor(0.3, 0.6, 0.2)
        )

# Run radiation simulation (if radiation plugin available)
try:
    with RadiationModel(context) as radiation:
        radiation.addRadiationBand("PAR")
        radiation.addCollimatedRadiationSource(vec3(0, 0, 10), 1000)
        radiation.run()
        
        # Radiation data is now set on primitives
        
    # Visualize radiation results
    with Visualizer(1024, 768) as visualizer:
        visualizer.buildContextGeometry(context)
        visualizer.setBackgroundColor([0.1, 0.1, 0.2])  # Dark background
        
        # Color by absorbed radiation
        visualizer.colorContextPrimitivesByData("radiation_flux_PAR")
        
        # Set camera for good viewing angle
        visualizer.setCameraPosition(
            position=vec3(8, 8, 8),
            lookAt=vec3(2.5, 2.5, 2)
        )
        
        # Use lighting that doesn't interfere with data visualization
        visualizer.setLightingModel("none")  # Show pure data colors
        
        visualizer.plotInteractive()
        
except Exception as e:
    print(f"Radiation simulation not available: {e}")
    # Fallback to manual data for demonstration
    all_uuids = context.getAllUUIDs("patch")
    for i, uuid in enumerate(all_uuids):
        # Set dummy radiation data
        flux_value = 50 + (i % 20) * 25  # Vary from 50 to 525
        context.setPrimitiveDataFloat(uuid, "simulated_flux", flux_value)
    
    with Visualizer(1024, 768) as visualizer:
        visualizer.buildContextGeometry(context)
        visualizer.colorContextPrimitivesByData("simulated_flux")
        visualizer.plotInteractive()
```

#### Data Visualization Best Practices

1. **Set data before visualization**: Always use `context.setPrimitiveDataFloat()` before calling `colorContextPrimitivesByData()`

2. **Use meaningful data names**: Choose descriptive names like `"temperature_celsius"` or `"radiation_flux_PAR"`

3. **Consider data ranges**: Large value ranges may require colormap configuration (future enhancement)

4. **Lighting considerations**: 
   - Use `setLightingModel("none")` to show pure data colors
   - Use `setLightingModel("phong")` to maintain surface appearance with data coloring

5. **Selective visualization**: Color specific primitives to highlight regions of interest:
   ```python
   # Color only high-value primitives
   high_flux_uuids = [uuid for uuid in all_uuids 
                     if context.getPrimitiveData(uuid, "flux")[0] > threshold]
   visualizer.colorContextPrimitivesByData("flux", high_flux_uuids)
   ```

## Image Export

### Basic Image Saving

```python
# Save current view to image (verified method)
visualizer.printWindow("scene_view.jpg")

# High-resolution image export
high_res_visualizer = Visualizer(3840, 2160, headless=True)
high_res_visualizer.buildContextGeometry(context)
high_res_visualizer.setCameraPosition([10, 10, 10], [0, 0, 0])
high_res_visualizer.plotUpdate()
high_res_visualizer.printWindow("high_res_scene.jpg")
```

### Batch Image Generation

```python
# Generate multiple views
views = {
    "front": ([0, 15, 5], [0, 0, 5]),
    "side": ([15, 0, 5], [0, 0, 5]),
    "top": ([0, 0, 20], [0, 0, 0]),
    "iso": ([10, 10, 10], [0, 0, 0])
}

for view_name, (position, look_at) in views.items():
    visualizer.setCameraPosition(vec3(*position), vec3(*look_at))
    visualizer.plotUpdate()
    visualizer.printWindow(f"scene_{view_name}.jpg")
```

## Window Management

### Window Control

```python
# Close visualization window (verified method)
visualizer.closeWindow()

# Safe to call even if no window is open
visualizer.closeWindow()  # No error
```

## Complete Workflow Examples

### Tree Visualization

```python
from pyhelios import Context, WeberPennTree, WPTType, Visualizer
from pyhelios.types import *

# Create scene
context = Context()

# Generate tree
wpt = WeberPennTree(context)
tree_id = wpt.buildTree(WPTType.APPLE)

# Add ground plane
ground_uuid = context.addPatch(
    center=vec3(0, 0, 0),
    size=vec2(10, 10),
    color=RGBcolor(0.4, 0.3, 0.2)
)

# Visualize
try:
    with Visualizer(1200, 800, antialiasing_samples=4) as visualizer:
        # Build all geometry
        visualizer.buildContextGeometry(context)
        
        # Set up nice view
        visualizer.setCameraPosition(vec3(8, 8, 6), vec3(0, 0, 3))
        visualizer.setBackgroundColor(RGBcolor(0.5, 0.7, 1.0))
        visualizer.setLightDirection(vec3(0.3, 0.3, -0.9))
        visualizer.setLightingModel("phong_shadowed")
        
        # Show interactive view
        visualizer.plotInteractive()
        
        # Save image
        visualizer.printWindow("apple_tree.jpg")
        
except VisualizerError as e:
    print(f"Visualization failed: {e}")
```

### Animation Sequence

```python
# Create animation of rotating tree
with WeberPennTree(context) as wpt:
    tree_id = wpt.buildTree(WPTType.LEMON)

try:
    with Visualizer(800, 600, headless=True) as visualizer:
        visualizer.buildContextGeometry(context)
        visualizer.setBackgroundColor(RGBcolor(0.8, 0.9, 1.0))
        visualizer.setLightingModel("phong")
        
        # Create 360-degree rotation
        for angle in range(0, 360, 5):
            import math
            radians = math.radians(angle)
            radius = 12
            x = radius * math.cos(radians)
            y = radius * math.sin(radians)
            
            visualizer.setCameraPosition(vec3(x, y, 6), vec3(0, 0, 3))
            visualizer.plotUpdate()
            visualizer.printWindow(f"animation/frame_{angle:03d}.jpg")
            
    print("Animation sequence complete")
    
except VisualizerError as e:
    print(f"Animation failed: {e}")
```

### Multi-Scene Comparison

```python
# Compare different tree types
tree_types = [WPTType.APPLE, WPTType.LEMON, WPTType.OLIVE]

for i, tree_type in enumerate(tree_types):
    # Create clean context for each tree
    context = Context()
    wpt = WeberPennTree(context)
    tree_id = wpt.buildTree(tree_type)
    
    try:
        with Visualizer(600, 600, headless=True) as visualizer:
            visualizer.buildContextGeometry(context)
            
            # Standardized view
            visualizer.setCameraPosition(vec3(6, 6, 6), vec3(0, 0, 3))
            visualizer.setBackgroundColor(RGBcolor(1.0, 1.0, 1.0))
            visualizer.setLightingModel("phong")
            
            visualizer.plotUpdate()
            visualizer.printWindow(f"tree_comparison_{tree_type.name.lower()}.jpg")
            
    except VisualizerError as e:
        print(f"Failed to visualize {tree_type.name}: {e}")
```

## Error Handling

```python
try:
    visualizer = Visualizer(1024, 768, antialiasing_samples=4)
    
except VisualizerError as e:
    print(f"Visualizer initialization failed: {e}")
    
    # Check platform-specific requirements
    import platform
    system = platform.system().lower()
    
    if 'linux' in system:
        print("Linux: Install X11 dev packages (libx11-dev, xorg-dev)")
        print("       sudo apt-get install libx11-dev xorg-dev libgl1-mesa-dev")
    elif 'darwin' in system:
        print("macOS: Install XQuartz (brew install --cask xquartz)")
    elif 'windows' in system:
        print("Windows: Update graphics drivers and Visual Studio runtime")

except ValueError as e:
    print(f"Invalid parameters: {e}")
    # Check width, height, antialiasing_samples values
```

## Performance Optimization

### Optimized Settings

```python
# Performance vs quality trade-offs
performance_configs = {
    "fast": {
        "width": 800,
        "height": 600,
        "antialiasing": 1,
        "lighting": "none"
    },
    "balanced": {
        "width": 1024,
        "height": 768,
        "antialiasing": 4,
        "lighting": "phong"
    },
    "high_quality": {
        "width": 1920,
        "height": 1080,
        "antialiasing": 8,
        "lighting": "phong_shadowed"
    }
}

# Apply configuration
config = performance_configs["balanced"]
visualizer = Visualizer(
    config["width"], 
    config["height"], 
    antialiasing_samples=config["antialiasing"]
)
visualizer.setLightingModel(config["lighting"])
```

### Memory Management

```python
# For large scenes, load geometry in batches
def visualize_large_scene(context, batch_size=1000):
    all_uuids = context.getAllUUIDs()
    total_primitives = len(all_uuids)
    
    with Visualizer(1024, 768) as visualizer:
        # Process in batches to manage memory
        for i in range(0, total_primitives, batch_size):
            batch_uuids = all_uuids[i:i + batch_size]
            visualizer.buildContextGeometry(context, uuids=batch_uuids)
            
            # Update visualization
            visualizer.plotUpdate()
            print(f"Processed {min(i + batch_size, total_primitives)}/{total_primitives} primitives")
```

## Build Requirements

```bash
# Build with visualizer plugin
build_scripts/build_helios --plugins visualizer

# Or use profiles that include visualization
build_scripts/build_helios                              # Default build includes visualizer
build_scripts/build_helios --plugins visualizer           # Visualizer-only build

# Check if visualizer is available
python -c "from pyhelios.plugins import get_plugin_registry; print(get_plugin_registry().is_plugin_available('visualizer'))"
```

## Platform-Specific Installation

### Linux (Ubuntu/Debian)
```bash
sudo apt-get install libx11-dev xorg-dev libgl1-mesa-dev libglu1-mesa-dev
```

### Linux (CentOS/RHEL)  
```bash
sudo yum install libX11-devel mesa-libGL-devel mesa-libGLU-devel
```

### macOS
```bash
brew install --cask xquartz
# OpenGL should be available by default
```

### Windows
- OpenGL drivers provided by graphics card drivers
- Visual Studio runtime may be required

This documentation covers the actual Visualizer implementation in PyHelios, verified against the wrapper code and high-level interface.