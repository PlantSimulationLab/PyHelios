# PlantArchitecture Documentation {#PlantArchitectureDoc}

## Overview

PlantArchitecture provides advanced plant structure and architecture modeling with a comprehensive library of 25+ procedural plant models. This plugin enables time-based plant growth simulation, procedural plant generation, and plant community modeling for scientific applications including agriculture, forestry, and ecological research.

The plugin includes pre-built models for major agricultural crops (bean, cowpea, maize, rice, soybean, wheat), fruit trees (almond, apple, olive, walnut), and other plant species with biologically-accurate growth parameters and morphological characteristics.

## System Requirements

- **Platforms**: Windows, Linux, macOS
- **Dependencies**: Extensive asset library (textures, OBJ models, configuration files)
- **GPU**: Not required
- **Memory**: Moderate memory usage scales with plant complexity and canopy size
- **Assets**: Large asset collection (~100MB) with textures, 3D models, and species parameters

## Installation

### Build with PlantArchitecture

PlantArchitecture is included in default PyHelios builds. To build explicitly:

```bash
# Using interactive selection
build_scripts/build_helios --interactive

# Explicit selection
build_scripts/build_helios --plugins plantarchitecture

# Clean build
build_scripts/build_helios --clean --plugins plantarchitecture

# Check if available
python -c "from pyhelios.plugins import print_plugin_status; print_plugin_status()"
```

### Verify Installation

```python
from pyhelios import PlantArchitecture
from pyhelios.PlantArchitecture import is_plantarchitecture_available

# Check availability
if is_plantarchitecture_available():
    print("PlantArchitecture is available")
else:
    print("PlantArchitecture not available - rebuild required")
```

## Quick Start

```python
from pyhelios import Context, PlantArchitecture
from pyhelios.types import *

# Create context and plugin
with Context() as context:
    with PlantArchitecture(context) as plantarch:
        # Get available plant models
        models = plantarch.getAvailablePlantModels()
        print(f"Available models: {models}")

        # Load a plant model
        plantarch.loadPlantModelFromLibrary("bean")

        # Create a single plant
        position = vec3(0, 0, 0)
        age = 30.0  # days
        plant_id = plantarch.buildPlantInstanceFromLibrary(position, age)
        print(f"Created plant ID: {plant_id}")

        # Advance plant growth
        plantarch.advanceTime(10.0)  # Grow for 10 more days
```

## Available Plant Models

PlantArchitecture includes 25+ scientifically-validated plant models:

**Field Crops:**
- `"bean"` - Common bean with climbing growth habit
- `"cowpea"` - Cowpea with determinate growth pattern
- `"maize"` - Corn with C4 photosynthetic characteristics
- `"rice"` - Rice with tillering growth pattern
- `"sorghum"` - Sorghum grain crop
- `"soybean"` - Soybean with determinate/indeterminate varieties
- `"wheat"` - Wheat with tiller development

**Trees:**
- `"almond"` - Almond tree with seasonal growth patterns
- `"apple"` - Apple tree with standard varieties
- `"easternredbud"` - Ornamental tree
- `"olive"` - Olive tree with Mediterranean characteristics
- `"pistachio"` - Pistachio with alternating bearing patterns
- `"walnut"` - Walnut tree with complex branching

**Vegetables:**
- `"butterlettuce"` - Lettuce with rosette growth form
- `"capsicum"` - Bell pepper with bush growth habit
- `"cherrytomato"` - Cherry tomato variant
- `"strawberry"` - Strawberry with runner propagation
- `"sugarbeet"` - Sugar beet root crop
- `"tomato"` - Tomato with determinate/indeterminate growth

**Weeds:**
- `"bindweed"` - Invasive vine species
- `"cheeseweed"` - Common weed species
- `"groundcherryweed"` - Weed species related to tomato and tomatillo
- `"puncturevine"` - Prostrate weed species

**Vines:**
- `"grapevine_VSP"` - Grapevine with vertical shoot positioned trellis
- `"grapevine_Wye"` - Grapevine with Wye trellis (quadrilateral)

## Examples

### Basic Plant Creation

```python
from pyhelios import Context, PlantArchitecture
from pyhelios.types import *

with Context() as context:
    with PlantArchitecture(context) as plantarch:
        # Load bean model
        plantarch.loadPlantModelFromLibrary("bean")

        # Create plant at origin with 20-day age
        position = vec3(0, 0, 0)
        age = 20.0
        plant_id = plantarch.buildPlantInstanceFromLibrary(position, age)

        print(f"Created bean plant {plant_id} at age {age} days")
```

### Plant Canopy Generation

```python
from pyhelios import Context, PlantArchitecture
from pyhelios.types import *

with Context() as context:
    with PlantArchitecture(context) as plantarch:
        # Load crop model
        plantarch.loadPlantModelFromLibrary("maize")

        # Create 5x5 canopy
        canopy_center = vec3(0, 0, 0)
        plant_spacing = vec2(0.75, 0.75)  # 75cm spacing
        plant_count = int2(5, 5)          # 5x5 grid
        age = 45.0                        # 45-day-old plants

        plant_ids = plantarch.buildPlantCanopyFromLibrary(
            canopy_center, plant_spacing, plant_count, age
        )

        print(f"Created canopy with {len(plant_ids)} maize plants")
        print(f"Plant IDs: {plant_ids}")
```

### Time-Based Growth Simulation

```python
from pyhelios import Context, PlantArchitecture
from pyhelios.types import *

with Context() as context:
    with PlantArchitecture(context) as plantarch:
        # Load and create young plant
        plantarch.loadPlantModelFromLibrary("soybean")
        plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 15.0)

        # Simulate growth over time
        growth_days = [5, 10, 5, 8]  # Growth increments

        for days in growth_days:
            print(f"Advancing {days} days...")
            plantarch.advanceTime(days)

            # Get plant components after growth
            object_ids = plantarch.getAllPlantObjectIDs(plant_id)
            uuids = plantarch.getAllPlantUUIDs(plant_id)

            print(f"  Plant now has {len(object_ids)} objects, {len(uuids)} primitives")
```

### Multi-Species Simulation

```python
from pyhelios import Context, PlantArchitecture
from pyhelios.types import *

with Context() as context:
    with PlantArchitecture(context) as plantarch:
        # Create mixed species simulation
        species_positions = [
            ("bean", vec3(-1, 0, 0), 25.0),
            ("maize", vec3(0, 0, 0), 30.0),
            ("soybean", vec3(1, 0, 0), 20.0)
        ]

        plant_ids = []
        for species, position, age in species_positions:
            plantarch.loadPlantModelFromLibrary(species)
            plant_id = plantarch.buildPlantInstanceFromLibrary(position, age)
            plant_ids.append((species, plant_id))
            print(f"Created {species} plant (ID: {plant_id}) at age {age} days")

        # Simulate synchronized growth
        plantarch.advanceTime(21.0)  # Three weeks of growth

        # Analyze final state
        for species, plant_id in plant_ids:
            primitives = plantarch.getAllPlantUUIDs(plant_id)
            print(f"{species} plant {plant_id}: {len(primitives)} primitives")
```

### Error Handling

```python
from pyhelios import Context, PlantArchitecture, PlantArchitectureError
from pyhelios.types import *

with Context() as context:
    try:
        with PlantArchitecture(context) as plantarch:
            # Attempt to load invalid model
            try:
                plantarch.loadPlantModelFromLibrary("nonexistent_plant")
            except PlantArchitectureError as e:
                print(f"Model loading error: {e}")

            # Load valid model
            plantarch.loadPlantModelFromLibrary("bean")

            # Test parameter validation
            try:
                # Invalid age (negative)
                plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), -5.0)
            except ValueError as e:
                print(f"Parameter validation error: {e}")

            # Valid plant creation
            plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 30.0)
            print(f"Successfully created plant {plant_id}")

    except PlantArchitectureError as e:
        print(f"Plugin error: {e}")
        # Error messages include rebuild instructions
```

### Species-Specific Characteristics

Different plant models have unique biological characteristics:

- **Annual crops** (bean, maize, wheat): Complete lifecycle in one growing season
- **Perennial trees** (almond, olive, walnut): Multi-year growth patterns with seasonal cycles
- **Determinant growth** (some beans, tomatoes): Defined growth endpoint
- **Indeterminant growth** (some tomatoes, vines): Continuous growth under favorable conditions