# User Guide {#UserGuide}

Complete guide to PyHelios core functionality, API reference, and advanced usage patterns.

## Introduction {#Overview}

### What is Helios?

Helios is a powerful C++ library for 3D physical simulation of plant and environmental systems. It provides:

- **3D Geometry Management**: Sophisticated handling of complex plant architectures
- **Physical Modeling**: Advanced simulation of light, energy, and mass transport
- **Plugin Architecture**: Extensible system for specialized modeling capabilities
- **High Performance**: Optimized C++ core with optional GPU acceleration

### PyHelios Integration

PyHelios provides seamless Python access to Helios functionality while maintaining:
- **Performance**: Direct access to optimized C++ implementations
- **Flexibility**: Full access to underlying Helios functionality  
- **Ease of Use**: Pythonic interfaces and error handling
- **Cross-Platform**: Consistent behavior across Windows, macOS, and Linux

## Core Architecture

### Context - The Simulation Environment

The \ref pyhelios.Context.Context "Context" is the central hub of any Helios simulation:

- **Geometry Management**: Stores and organizes all 3D primitives
- **Coordinate Systems**: Manages spatial reference frames
- **Data Association**: Links data to geometric elements
- **State Tracking**: Maintains simulation state and history

### Primitives - Basic Geometric Elements

Helios uses several primitive types:

- **Patches**: Rectangular surface elements (most common)
- **Triangles**: Triangular surface elements for complex shapes
- **Tiles**: Specialized surface elements

### UUID-Based Object Tracking

All primitives are identified by Universally Unique Identifiers (UUIDs):

```python
from pyhelios import Context
from pyhelios.types import *

context = Context()

# Create primitives - returns UUID
patch_uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
triangle_uuid = context.addTriangle(
    vertex0=vec3(0, 0, 0),
    vertex1=vec3(1, 0, 0), 
    vertex2=vec3(0.5, 1, 0)
)

# Use UUIDs to query properties
area = context.getPrimitiveArea(patch_uuid)
vertices = context.getPrimitiveVertices(triangle_uuid)
```

## Data Types and Imports {#API}

### Standardized Vector Type Imports

PyHelios provides convenient access to vector types. **Use this standardized pattern throughout your code:**

```python
from pyhelios import Context
from pyhelios.types import *  # Import all vector types directly

# Create simulation environment
context = Context()

# Vector types (no prefix needed)
position = vec3(1.0, 2.0, 3.0)
size = vec2(10.0, 5.0)
direction = vec4(1.0, 2.0, 3.0, 1.0)

# Integer vectors
grid_size = int2(100, 50)
voxel_index = int3(10, 20, 5)
tensor_dims = int4(100, 50, 25, 10)

# Colors (0.0 to 1.0 range)
green = RGBcolor(0.2, 0.8, 0.2)
transparent_blue = RGBAcolor(0.2, 0.2, 0.8, 0.5)

# Spherical coordinates
spherical = SphericalCoord(
    radius=10.0,
    elevation=0.5,  # radians from horizontal
    azimuth=1.57    # radians from north
)
```

**Alternative (verbose) approach:**
```python
# Alternative: DataTypes module (less preferred)
from pyhelios import DataTypes
position = DataTypes.vec3(1.0, 2.0, 3.0)
color = DataTypes.RGBcolor(0.3, 0.7, 0.2)
```

### Available Types

The star import `from pyhelios.types import *` provides:
- **Vector types**: \ref pyhelios.wrappers.DataTypes.vec2 "vec2", \ref pyhelios.wrappers.DataTypes.vec3 "vec3", \ref pyhelios.wrappers.DataTypes.vec4 "vec4"
- **Integer vectors**: \ref pyhelios.wrappers.DataTypes.int2 "int2", \ref pyhelios.wrappers.DataTypes.int3 "int3", \ref pyhelios.wrappers.DataTypes.int4 "int4"
- **Colors**: \ref pyhelios.wrappers.DataTypes.RGBcolor "RGBcolor", \ref pyhelios.wrappers.DataTypes.RGBAcolor "RGBAcolor"
- **Coordinates**: \ref pyhelios.wrappers.DataTypes.SphericalCoord "SphericalCoord"
- **Factory functions**: `make_vec3`, `make_RGBcolor`, etc.

## Context Class Reference

The \ref pyhelios.Context.Context "Context class" is the central simulation environment. All methods documented here are verified from the actual implementation.

### Basic Usage

```python
from pyhelios import Context
from pyhelios.types import *

# Create a new simulation context
context = Context()

# Context manager usage (recommended for automatic cleanup)
with Context() as context:
    # Your simulation code here
    patch_uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
    # Automatic cleanup on exit
```

### Geometry Creation Methods

#### Patches (Rectangular Surfaces)

```python
# Basic patch with defaults
patch_uuid = context.addPatch()

# Patch with center and size
patch_uuid = context.addPatch(
    center=vec3(0, 0, 0),
    size=vec2(1.0, 2.0)
)

# Patch with all parameters
patch_uuid = context.addPatch(
    center=vec3(0, 0, 0),
    size=vec2(1.0, 2.0), 
    rotation=SphericalCoord(radius=1, elevation=0, azimuth=0),
    color=RGBcolor(0.3, 0.7, 0.2)
)
```

#### Triangles

```python
# Triangle with three vertices
triangle_uuid = context.addTriangle(
    vertex0=vec3(0, 0, 0),
    vertex1=vec3(1, 0, 0),
    vertex2=vec3(0.5, 1, 0)
)

# Triangle with color
triangle_uuid = context.addTriangle(
    vertex0=vec3(0, 0, 0),
    vertex1=vec3(1, 0, 0),
    vertex2=vec3(0.5, 1, 0),
    color=RGBcolor(0.8, 0.2, 0.2)
)
```

#### Compound Geometry

**Tiles (Subdivided Patches)**

```python
# Create a tile subdivided into multiple patches
tile_uuids = context.addTile(
    center=vec3(0, 0, 0),
    size=vec2(2, 2),
    rotation=SphericalCoord(1, 0, 0),
    subdivisions=int2(4, 4)  # 4x4 subdivision
)
print(f"Created {len(tile_uuids)} patches in tile")
```

**Spheres (Tessellated)**

```python
# Create a tessellated sphere
sphere_uuids = context.addSphere(
    Ndivisions=10,  # Number of subdivisions
    center=vec3(0, 0, 2),
    radius=1.0,
    color=RGBcolor(0.2, 0.5, 0.8)
)
print(f"Created sphere with {len(sphere_uuids)} triangular faces")
```

**Tubes (Cylindrical Geometry)**

```python
# Create a tube from node positions
nodes = [vec3(0, 0, 0), vec3(0, 0, 1), vec3(0, 0, 2)]
radii = [0.1, 0.15, 0.05]  # Variable radius along tube

tube_uuids = context.addTube(
    Ndivisions=8,  # Circumferential divisions
    nodes=nodes,
    radii=radii,
    color=RGBcolor(0.4, 0.2, 0.1)
)
print(f"Created tube with {len(tube_uuids)} primitives")
```

**Boxes (3D Rectangular)**

```python
# Create a 3D box
box_uuids = context.addBox(
    center=vec3(1, 1, 1),
    size=vec3(0.5, 0.5, 0.5),
    rotation=SphericalCoord(1, 0, 0.785),  # 45 degree rotation
    color=RGBcolor(0.6, 0.3, 0.8)
)
print(f"Created box with {len(box_uuids)} faces")
```

#### Array-Based Methods

**Textured Triangles**

```python
# Single textured triangle
textured_uuid = context.addTriangleTextured(
    vertex0=vec3(0, 0, 0),
    vertex1=vec3(1, 0, 0),
    vertex2=vec3(0.5, 1, 0),
    textureFilename="textures/leaf.jpg",
    uv0=vec2(0, 0),
    uv1=vec2(1, 0),
    uv2=vec2(0.5, 1)
)
```

**Batch Triangle Creation from Arrays**

```python
import numpy as np

# Create multiple triangles from NumPy arrays
vertices = np.array([
    [0, 0, 0], [1, 0, 0], [0.5, 1, 0],  # Triangle 1
    [1, 0, 0], [2, 0, 0], [1.5, 1, 0]   # Triangle 2
], dtype=np.float32)

# Add triangles from arrays
triangle_uuids = context.addTrianglesFromArrays(
    vertices=vertices,
    indices=np.array([0, 1, 2, 3, 4, 5], dtype=np.uint32),
    color=RGBcolor(0.5, 0.7, 0.3)
)
print(f"Created {len(triangle_uuids)} triangles from arrays")
```

**Batch Textured Triangle Creation**

```python
# Create multiple textured triangles from arrays
texture_coords = np.array([
    [0, 0], [1, 0], [0.5, 1],  # UV coords for triangle 1
    [0, 0], [1, 0], [0.5, 1]   # UV coords for triangle 2
], dtype=np.float32)

textured_uuids = context.addTrianglesFromArraysTextured(
    vertices=vertices,
    indices=np.array([0, 1, 2, 3, 4, 5], dtype=np.uint32),
    textureCoords=texture_coords,
    textureFilename="textures/bark.jpg"
)
print(f"Created {len(textured_uuids)} textured triangles")
```

### Geometry Query Methods

#### Basic Properties

```python
# Geometric properties
area = context.getPrimitiveArea(uuid)
normal = context.getPrimitiveNormal(uuid)  # Returns vec3
vertices = context.getPrimitiveVertices(uuid)  # Returns list of vec3

# Primitive information
prim_type = context.getPrimitiveType(uuid)  # Returns PrimitiveType enum
color = context.getPrimitiveColor(uuid)     # Returns RGBcolor

# Context-wide queries
total_primitives = context.getPrimitiveCount()
all_uuids = context.getAllUUIDs()  # Returns list of all primitive UUIDs
```

#### Data Association

```python
# Set primitive data (use type-specific methods)
context.setPrimitiveDataFloat(uuid, "temperature", 25.0)
context.setPrimitiveDataString(uuid, "material", "leaf")

# Get primitive data
temperature = context.getPrimitiveData(uuid, "temperature", float)
material = context.getPrimitiveData(uuid, "material", str)

# Check if data exists
has_data = context.doesPrimitiveDataExist(uuid, "temperature")

# Efficient data retrieval as NumPy arrays
import numpy as np

# Get data for all primitives as NumPy array (most efficient method)
all_uuids = context.getAllUUIDs()
temperature_array = context.getPrimitiveDataArray(all_uuids, "temperature")
print(f"Temperature array shape: {temperature_array.shape}")
print(f"Mean temperature: {np.mean(temperature_array)}")

# Get data for specific primitives
selected_uuids = all_uuids[:100]  # First 100 primitives
temperature_subset = context.getPrimitiveDataArray(selected_uuids, "temperature")

# Works with any data type
area_array = context.getPrimitiveDataArray(all_uuids, "area")
```

#### Primitive Collections

```python
# Get all primitive UUIDs
all_uuids = context.getAllUUIDs()
print(f"Total primitives: {len(all_uuids)}")

# Use specific query methods as needed for geometric properties
for uuid in all_uuids:
    area = context.getPrimitiveArea(uuid)
    prim_type = context.getPrimitiveType(uuid)
```

## File I/O Operations {#IO}

### Supported File Formats

#### Geometry Files
- **PLY**: Stanford Triangle Format (preferred for 3D meshes)
- **OBJ**: Wavefront OBJ format
- **XML**: Helios XML format for complex scenes

#### Data Files
- **CSV**: Comma-separated values for tabular data
- **TXT**: Plain text data files
- **JSON**: Configuration and metadata

### Loading Geometry

#### PLY Files

```python
from pyhelios import Context
from pyhelios.types import *

context = Context()

# Basic PLY loading
uuids = context.loadPLY("models/plant.ply")
print(f"Loaded {len(uuids)} primitives from PLY file")

# PLY with transformations
origin = vec3(5, 0, 0)
rotation = SphericalCoord(1.0, 0, 1.57)  # 90 degrees
color = RGBcolor(0.3, 0.7, 0.3)

uuids = context.loadPLY(
    "leaf.ply",
    origin=origin,
    rotation=rotation,
    color=color
)
```

#### OBJ Files

```python
# Basic OBJ loading
uuids = context.loadOBJ("models/tree.obj")

# OBJ with material support
uuids = context.loadOBJ(
    "textured_plant.obj",
    silent=True  # Suppress loading messages
)
```

#### XML Files

```python
# Load Helios XML scene
uuids = context.loadXML("scenes/plant_scene.xml")

# XML with global transformations
uuids = context.loadXML(
    "complex_scene.xml",
    origin=vec3(10, 0, 0),
    rotation=SphericalCoord(1.0, 0.1, 0)
)
```



## Error Handling and Best Practices

### Exception Handling

```python
from pyhelios import Context, HeliosPluginNotAvailableError
from pyhelios.types import *

# Always use try-catch for robust applications
try:
    context = Context()
    
    # Geometry operations
    patch_uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
    
    # Data operations
    context.setPrimitiveDataFloat(patch_uuid, "temperature", 25.0)
    temp = context.getPrimitiveData(patch_uuid, "temperature", float)
    
except HeliosPluginNotAvailableError as e:
    print(f"Plugin not available: {e}")
except Exception as e:
    print(f"Simulation error: {e}")
```

### Memory Management

```python
# Use context managers for automatic cleanup
with Context() as context:
    # Large simulation operations
    uuids = context.loadPLY("large_model.ply")
    # Automatic cleanup when exiting context
    pass

# Manual cleanup if needed
context = Context()
try:
    # Simulation work
    pass
finally:
    # Context cleanup handled automatically
    pass
```

### Performance Optimization

```python
from pyhelios import Context
from pyhelios.types import *

context = Context()

# Batch operations for better performance
patch_centers = [vec3(i, j, 0) for i in range(10) for j in range(10)]
patch_uuids = []

for center in patch_centers:
    uuid = context.addPatch(center=center, size=vec2(0.1, 0.1))
    patch_uuids.append(uuid)

# Batch data setting
for uuid in patch_uuids:
    context.setPrimitiveDataFloat(uuid, "temperature", 20.0 + random.uniform(-5, 5))

# Get primitive information efficiently
print(f"Total primitives: {context.getPrimitiveCount()}")
```

## Integration with Helios Ecosystem

PyHelios seamlessly integrates with the broader Helios ecosystem:

- **Native Helios**: Access to full C++ API through ctypes
- **Helios Plugins**: Support for all 21+ available plugins
- **Helios Data Formats**: Compatible file I/O operations
- **Helios Documentation**: Consistent with native documentation

### Plugin System Integration

```python
from pyhelios import Context

context = Context()

# Check plugin availability using the plugin system
from pyhelios.plugins import get_plugin_registry, print_plugin_status

# Get detailed plugin status
print_plugin_status()

# Check specific plugin availability (example)
registry = get_plugin_registry()
if registry.is_plugin_available('radiation'):
    print("GPU radiation modeling available")
if registry.is_plugin_available('visualizer'):
    print("3D visualization available")
if registry.is_plugin_available('weberpenntree'):
    print("Procedural tree generation available")
```

### Native Pointer Access

For advanced users needing direct C++ API access:

```python
# Get native pointer for direct Helios C++ calls
native_context_ptr = context.getNativePtr()

# Use with caution - bypasses Python safety checks
# Only for advanced integration scenarios
```

## Physical Units and Conventions

### Coordinate System
- **X-axis**: East (positive) / West (negative)
- **Y-axis**: North (positive) / South (negative)  
- **Z-axis**: Up (positive) / Down (negative)

### Units
- **Length**: Meters (m)
- **Area**: Square meters (m²)
- **Angles**: Radians
- **Temperature**: Celsius (°C)
- **Radiation**: W/m² or mol/m²/s depending on context

### Color Values
- **RGB**: 0.0 to 1.0 range (not 0-255)
- **Alpha**: 0.0 (transparent) to 1.0 (opaque)

## Complete Example

```python
from pyhelios import Context, WeberPennTree, RadiationModel
from pyhelios.types import *

# Create simulation with error handling
try:
    with Context() as context:
        print("Creating plant geometry...")
        
        # Add ground patch
        ground = context.addPatch(
            center=vec3(0, 0, 0),
            size=vec2(10, 10),
            color=RGBcolor(0.4, 0.3, 0.2)
        )
        
        # Add procedural tree if available
        try:
            from pyhelios import WeberPennTree
            wpt = WeberPennTree(context)
            tree_uuid = wpt.buildTree(WeberPennTree.WPTType.LEMON)
            print(f"Created tree: {tree_uuid}")
        except Exception as e:
            print(f"WeberPennTree not available: {e}")
        
        # Load additional geometry
        try:
            leaf_uuids = context.loadPLY("models/leaf.ply")
            print(f"Loaded {len(leaf_uuids)} leaf primitives")
        except:
            print("Leaf model not found, continuing without it")
        
        # Set initial conditions
        all_uuids = context.getAllUUIDs()
        for uuid in all_uuids:
            context.setPrimitiveDataFloat(uuid, "temperature", 20.0)
        
        # Run radiation simulation if available
        try:
            with RadiationModel(context) as radiation:
                radiation.addRadiationBand("SW")
                radiation.setDirectRayCount("SW", 100)
                radiation.runBand("SW")
                print("Radiation simulation completed")
        except Exception as e:
            print(f"Radiation modeling not available: {e}")
        
        # Results available through getAllUUIDs() and getPrimitiveData()
        print(f"Results available for {len(all_uuids)} primitives")
        
        print(f"Simulation completed with {context.getPrimitiveCount()} primitives")

except Exception as e:
    print(f"Simulation failed: {e}")
```

For complete documentation of the underlying Helios library, visit: [https://baileylab.ucdavis.edu/software/helios](https://baileylab.ucdavis.edu/software/helios)