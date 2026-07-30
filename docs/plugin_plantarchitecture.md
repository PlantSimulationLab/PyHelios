# PlantArchitecture Documentation {#PlantArchitectureDoc}

## Overview

PlantArchitecture provides advanced plant structure and architecture modeling with a comprehensive library of 28 procedural plant models. This plugin enables time-based plant growth simulation, procedural plant generation, and plant community modeling for scientific applications including agriculture, forestry, and ecological research.

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

PlantArchitecture includes 28 scientifically-validated plant models:

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
- `"apple_fruitingwall"` - Apple fruiting wall (specialized high-density training system)
- `"easternredbud"` - Ornamental tree
- `"olive"` - Olive tree with Mediterranean characteristics
- `"pistachio"` - Pistachio with alternating bearing patterns
- `"walnut"` - Walnut tree with complex branching

**Vegetables:**
- `"asparagus"` - Asparagus perennial vegetable crop
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

**Vines and Ornamentals:**
- `"bougainvillea"` - Ornamental flowering vine with vibrant bracts
- `"grapevine_VSP"` - Grapevine with vertical shoot positioned trellis
- `"grapevine_Wye"` - Grapevine with Wye trellis (quadrilateral)

## Shoot, Phenology, and Resource Parameters

Beyond loading a named library model, PyHelios exposes the underlying parameter
structures so shoot growth, phenology, and the carbohydrate/nitrogen resource
models can be inspected and customized.

### Typed parameter model

`pyhelios.plant_architecture_params` provides a typed, discoverable mirror of the
native nested `ShootParameters` / `PhytomerParameters` / `LeafPrototype` structures
(plus the flat `CarbohydrateParameters` and `NitrogenParameters`). Random
distributions are expressed with `RandomParameterFloat` / `RandomParameterInt`
(`.constant(...)`, `.uniform(...)`, etc.), and every object round-trips with
`from_dict()` / `to_dict()`.

```python
from pyhelios import Context, PlantArchitecture
from pyhelios.plant_architecture_params import ShootParameters, RandomParameterFloat
from pyhelios.types import vec3

with Context() as context, PlantArchitecture(context) as plant:
    plant.loadPlantModelFromLibrary("almond")

    # Inspect the current shoot parameters as a typed object
    sp = plant.getCurrentShootParameters("trunk", return_typed=True)
    print(sp.max_nodes)
    print(sp.phytomer_parameters.leaf.pitch.to_dict())

    # Modify and re-register a shoot type (accepts a ShootParameters or a nested dict)
    sp.phytomer_parameters.internode.length_segments = 3
    plant.defineShootType("trunk", sp)
```

`getCurrentShootParameters()` returns a plain nested `dict` by default; pass
`return_typed=True` to get a `ShootParameters` object. The returned structure
surfaces the full `phytomer_parameters` sub-structure (internode, petiole, leaf,
peduncle, inflorescence, and the leaf prototype). `defineShootType()` accepts
either a nested `dict` or a `ShootParameters`.

### Phenological thresholds

`setPlantPhenologicalThresholds()` controls the timing of the developmental
stages. Pass `is_evergreen=True` for species that retain leaves through dormancy
rather than shedding them at senescence:

```python
plant.setPlantPhenologicalThresholds(
    plant_id,
    time_to_dormancy_break=60,
    time_to_flower_initiation=90,
    time_to_flower_opening=105,
    time_to_fruit_set=120,
    time_to_fruit_maturity=200,
    time_to_dormancy=280,
    max_leaf_lifespan=180,   # deciduous: ~6 month leaf life
    is_evergreen=False,
)
```

### Carbohydrate and nitrogen model parameters

`getDefaultCarbohydrateParameters()` and `getDefaultNitrogenParameters()` return
the C++ default-constructed template (a flat `dict`, or a typed object with
`return_typed=True`) to modify and apply to a plant instance via
`setPlantCarbohydrateParameters()` / `setPlantNitrogenParameters()`. The native
API has no per-plant getter for these, so the get methods return the default
template rather than the values currently in effect on a specific plant.

```python
from pyhelios.plant_architecture_params import CarbohydrateParameters

carb = plant.getDefaultCarbohydrateParameters(return_typed=True)
carb.SLA = 0.025
plant.setPlantCarbohydrateParameters(plant_id, carb)
```

See `docs/examples/plantarch_phytomer_parameters_sample.py` for a complete,
runnable example.

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

### Querying Organs

`getPlantLeafObjectIDs()` returns the object ID of every leaf on a plant, and `getPlantLeafBases()` returns each leaf's attachment base position (where it joins its petiole, not the leaf centroid).

```python
from pyhelios import Context, PlantArchitecture
from pyhelios.types import vec3

with Context() as context:
    with PlantArchitecture(context) as plantarch:
        plantarch.loadPlantModelFromLibrary("soybean")
        plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 20.0)

        leaf_ids = plantarch.getPlantLeafObjectIDs(plant_id)   # list of object IDs
        bases = plantarch.getPlantLeafBases(plant_id)          # list of vec3

        print(f"{len(leaf_ids)} leaves; first attaches at {bases[0]}")

        # Leaf object IDs are a subset of the plant's object IDs, so they can be
        # used with any Context object query.
        for leaf_id in leaf_ids[:5]:
            print(context.getObjectPrimitiveUUIDs(leaf_id))
```

> **Do not pair the two results positionally.** `getPlantLeafObjectIDs()` and `getPlantLeafBases()` are built by independent traversals of the shoot tree, so element *i* of one is not guaranteed to describe the same leaf as element *i* of the other. helios-core keeps an internal `getPlantLeafObjectIDsAndBases()` that gathers both in a single traversal for exactly this reason, but it is protected and not reachable from PyHelios. If you need the correspondence, derive the position from the object ID instead — e.g. via `context.getObjectPrimitiveUUIDs(leaf_id)` and the primitive vertices.

Four further getters cover the remaining organ types, all with the same signature and return type:

| Method | Organ |
|---|---|
| `getPlantLeafObjectIDs(plant_id)` | Leaves |
| `getPlantPetioleObjectIDs(plant_id)` | Petioles (stalks attaching leaves to the stem) |
| `getPlantPeduncleObjectIDs(plant_id)` | Peduncles (stalks bearing flowers and fruit) |
| `getPlantFlowerObjectIDs(plant_id)` | Flowers / inflorescences |
| `getPlantFruitObjectIDs(plant_id)` | Fruit |

Each returns object IDs that are a subset of `getAllPlantObjectIDs()`, and the five sets are mutually disjoint — no object is both a leaf and a fruit — so they can be used to partition a plant by organ type.

```python
import numpy as np

fruit_ids = plantarch.getPlantFruitObjectIDs(plant_id)

for fruit_id in fruit_ids:
    uuids = context.getObjectPrimitiveUUIDs(fruit_id)
    # Areas come back as float32; accumulate in float64 to avoid drift.
    area = context.getPrimitiveArea(uuids).sum(dtype=np.float64)
    print(f"fruit {fruit_id}: {area:.4f} m²")

# Partition a plant by organ type
for name in ("Leaf", "Petiole", "Peduncle", "Flower", "Fruit"):
    ids = getattr(plantarch, f"getPlant{name}ObjectIDs")(plant_id)
    print(f"{name}: {len(ids)}")
```

> **An empty list is a normal result, not a failure.** The reproductive organs — peduncles, flowers and fruit — exist only once a plant reaches the corresponding growth stage, so a plant built at a young age returns `[]` for them. Flowers additionally disappear as they set fruit, so a mature plant can legitimately report many fruit and no flowers. If you expect an organ and get none, advance the plant further with `advanceTime()` rather than treating the empty list as an error.

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

## Collision Detection

PlantArchitecture integrates advanced collision detection capabilities to enable realistic plant growth that responds to obstacles and other plants. The collision detection system uses cone-based ray tracing to guide plant growth away from obstacles while maintaining natural plant architecture.

### Overview

The collision detection system provides two primary modes:

1. **Soft Collision Avoidance**: Guides plant growth to naturally minimize collisions with itself and other plants while tending to fill open space (space colonization)
2. **Hard Obstacle Avoidance**: Strictly prevents plant growth through solid boundaries like ground, walls, or buildings

Both modes use a "perception cone" at the shoot apex to detect obstacles and guide growth direction. Ray-tracing calculations determine objects within the cone's field of view, allowing the plant to react appropriately.

### Perception Cone Parameters

The perception cone is the fundamental mechanism for collision detection. Key parameters control its behavior:

- **View Half-Angle** (degrees, 0-180): Field of view of the detection cone. Default: 80°
  - Wider angles detect more obstacles but increase computational cost
  - Narrower angles focus detection but may miss nearby obstacles

- **Look-Ahead Distance** (meters): How far ahead the plant "looks" for obstacles. Default: 0.1m
  - Longer distances detect distant obstacles earlier
  - Shorter distances are suitable for dense canopies

- **Sample Count** (rays): Number of rays launched within the cone. Default: 256
  - More samples provide better accuracy but reduce performance
  - Fewer samples improve speed but may miss small obstacles

- **Inertia Weight** (0-1): How strongly growth maintains previous direction. Default: 0.4
  - Lower values (e.g., 0.2) make growth more responsive to obstacles
  - Higher values (e.g., 0.6) make growth smoother and more gradual

### Soft Collision Avoidance

Soft collision avoidance guides plant growth to minimize collisions while maintaining natural architecture. Growth direction is adjusted toward the largest gap detected within the perception cone.

**Basic Usage:**

```python
from pyhelios import Context, PlantArchitecture
from pyhelios.types import *

with Context() as context:
    with PlantArchitecture(context) as plantarch:
        plantarch.loadPlantModelFromLibrary("bean")

        # Enable soft collision avoidance with default parameters
        plantarch.enableSoftCollisionAvoidance()

        # Build canopy - plants will avoid each other during growth
        plant_ids = plantarch.buildPlantCanopyFromLibrary(
            canopy_center=vec3(0, 0, 0),
            plant_spacing=vec2(0.3, 0.3),
            plant_count=int2(3, 3),
            age=10.0
        )

        # Grow plants with collision avoidance active
        plantarch.advanceTime(30.0)
```

**Customized Parameters:**

```python
# Configure for dense canopy with close spacing
plantarch.setSoftCollisionAvoidanceParameters(
    view_half_angle_deg=60.0,    # Narrower cone for focused detection
    look_ahead_distance=0.05,     # Shorter distance for close obstacles
    sample_count=512,             # More samples for better accuracy
    inertia_weight=0.3            # More responsive to obstacles
)

plantarch.enableSoftCollisionAvoidance()
```

**Target-Specific Collision Detection:**

```python
# Create obstacles (e.g., support structures)
pole_uuids = [context.addPatch(vec3(0, 0, 0.5), size=(0.1, 1))]

# Enable collision avoidance only for specific obstacles
plantarch.enableSoftCollisionAvoidance(
    target_object_UUIDs=pole_uuids,
    enable_petiole_collision=True,  # Include petioles in detection
    enable_fruit_collision=False     # Exclude fruit (performance)
)
```

### Hard Obstacle Avoidance

Hard obstacle avoidance strictly prevents plant growth through solid boundaries. When an obstacle is detected within the avoidance distance, growth is redirected perpendicular to the obstacle surface.

**Basic Usage:**

```python
from pyhelios import Context, PlantArchitecture
from pyhelios.types import *

with Context() as context:
    with PlantArchitecture(context) as plantarch:
        # Create ground plane
        ground_uuid = context.addPatch(
            center=vec3(0, 0, 0),
            size=(5, 5),
            color=RGBcolor(0.6, 0.4, 0.2)
        )

        # Create vertical wall
        wall_uuid = context.addPatch(
            center=vec3(1.5, 0, 0.5),
            size=(0.1, 3)
        )

        plantarch.loadPlantModelFromLibrary("tomato")

        # Enable solid obstacle avoidance
        plantarch.enableSolidObstacleAvoidance(
            obstacle_UUIDs=[ground_uuid, wall_uuid],
            avoidance_distance=0.3  # Stay 30cm away from obstacles
        )

        # Build plant near obstacles
        plant_id = plantarch.buildPlantInstanceFromLibrary(
            base_position=vec3(0.5, 0, 0),
            age=10.0
        )

        # Grow - plant will strictly avoid obstacles
        plantarch.advanceTime(25.0)
```

**With Fruit Adjustment:**

```python
# Create obstacles
ground = context.addPatch(vec3(0, 0, 0), size=(5, 5))
wall = context.addPatch(vec3(1.5, 0, 0.5), size=(0.1, 3))

# Enable fruit adjustment for large fruit near obstacles
plantarch.enableSolidObstacleAvoidance(
    obstacle_UUIDs=[ground, wall],
    avoidance_distance=0.4,
    enable_fruit_adjustment=True,    # Rotate fruit away from obstacles
    enable_obstacle_pruning=False    # Don't remove intersecting organs
)
```

### Performance Optimization

Collision detection can be computationally expensive. Several optimization techniques improve performance:

#### Static Obstacle Marking

Mark non-moving geometry as static to enable BVH (Bounding Volume Hierarchy) optimization:

```python
from pyhelios import Context, PlantArchitecture
from pyhelios.types import *

with Context() as context:
    with PlantArchitecture(context) as plantarch:
        # Create static environment
        ground = context.addPatch(vec3(0, 0, 0), size=(10, 10))
        building = context.addPatch(vec3(3, 3, 1), size=(2, 2))

        static_uuids = [ground, building]

        plantarch.loadPlantModelFromLibrary("soybean")

        # IMPORTANT: Enable collision detection FIRST
        plantarch.enableSoftCollisionAvoidance()

        # THEN mark static obstacles (builds optimized BVH)
        plantarch.setStaticObstacles(static_uuids)

        # Build plants with optimized collision detection
        plant_ids = plantarch.buildPlantCanopyFromLibrary(
            canopy_center=vec3(0, 0, 0),
            plant_spacing=vec2(0.5, 0.5),
            plant_count=int2(5, 5),
            age=15.0
        )

        plantarch.advanceTime(30.0)
```

**Key Points:**
- Static obstacles should not move during simulation
- BVH is built once and reused for all ray queries
- Significantly improves performance in complex scenes
- Must call `setStaticObstacles()` AFTER `enableSoftCollisionAvoidance()`

#### Organ Filtering

Selectively include organ types in collision detection to balance accuracy and performance:

```python
# Configure which organs participate in collision detection
plantarch.setCollisionRelevantOrgans(
    include_internodes=True,   # Include stems
    include_leaves=True,       # Include leaf blades
    include_petioles=False,    # Exclude petioles (performance)
    include_flowers=False,     # Exclude flowers
    include_fruit=False        # Exclude fruit
)

plantarch.enableSoftCollisionAvoidance()
```

**Default Configuration:**
- Only leaves are included by default (best performance)
- Internodes, petioles, flowers, and fruit are excluded

**Recommendations:**
- For most crops: leaves only (default)
- For woody plants: leaves + internodes
- For dense canopies: leaves + internodes + petioles
- Always benchmark performance impact when adding organ types

### Querying Collision-Relevant Geometry

Retrieve which objects are participating in collision detection for visualization or debugging:

```python
# Get collision-relevant object IDs for a specific plant
collision_obj_ids = plantarch.getPlantCollisionRelevantObjectIDs(plant_id)

print(f"Plant {plant_id} has {len(collision_obj_ids)} collision-relevant objects")

# Highlight collision geometry in visualization
for obj_id in collision_obj_ids:
    context.setObjectColor(obj_id, RGBcolor(1, 0, 0))  # Red highlight
```

### Disabling Collision Detection

Turn off collision detection when not needed:

```python
# Disable collision detection
plantarch.disableCollisionDetection()

# Plant growth will no longer check for collisions
plantarch.advanceTime(10.0)
```

### Complete Workflow Example

Realistic scenario combining all collision detection features:

```python
from pyhelios import Context, PlantArchitecture
from pyhelios.types import *

with Context() as context:
    with PlantArchitecture(context) as plantarch:
        # 1. Create environment
        ground = context.addPatch(vec3(0, 0, 0), size=(8, 8))
        building = context.addPatch(vec3(2, 2, 1), size=(2, 2))
        fence_uuids = [
            context.addPatch(vec3(-3, y, 0.5), size=(0.1, 1))
            for y in range(-3, 4)
        ]

        static_uuids = [ground, building] + fence_uuids

        # 2. Load plant model
        plantarch.loadPlantModelFromLibrary("cowpea")

        # 3. Configure collision parameters
        plantarch.setSoftCollisionAvoidanceParameters(
            view_half_angle_deg=80.0,
            look_ahead_distance=0.1,
            sample_count=256,
            inertia_weight=0.4
        )

        # 4. Set organ filtering
        plantarch.setCollisionRelevantOrgans(
            include_internodes=True,
            include_leaves=True,
            include_petioles=False,
            include_flowers=False,
            include_fruit=False
        )

        # 5. Enable soft collision avoidance
        plantarch.enableSoftCollisionAvoidance()

        # 6. Mark static obstacles for optimization
        plantarch.setStaticObstacles(static_uuids)

        # 7. Enable hard obstacle avoidance
        plantarch.enableSolidObstacleAvoidance(
            obstacle_UUIDs=[building] + fence_uuids,
            avoidance_distance=0.4,
            enable_fruit_adjustment=True
        )

        # 8. Build plant canopy
        plant_ids = plantarch.buildPlantCanopyFromLibrary(
            canopy_center=vec3(-1, -1, 0),
            plant_spacing=vec2(0.5, 0.5),
            plant_count=int2(4, 4),
            age=8.0
        )

        # 9. Grow plants with all collision features active
        plantarch.advanceTime(35.0)

        # 10. Save results
        context.writeOBJ("collision_example.obj")
```

### Performance Considerations

Collision detection computational cost scales with:
- **Scene complexity**: Number of primitives in the scene
- **Perception cone size**: Larger cones require more ray queries
- **Sample count**: More rays = more intersection tests
- **Plant density**: More plants = more collision checks
- **Organ inclusion**: More organ types = larger BVH

**Performance Tips:**

1. **Use static obstacles** for non-moving geometry (ground, buildings)
2. **Filter organs** - include only necessary organ types (default: leaves only)
3. **Tune cone parameters** - smaller cones and fewer samples for dense canopies
4. **Enable selectively** - only activate collision detection when needed
5. **Batch growth** - use larger time steps (e.g., 5-10 days) rather than daily increments

**Example Performance Settings:**

```python
# High accuracy (slower, for publication-quality results)
plantarch.setSoftCollisionAvoidanceParameters(
    view_half_angle_deg=90.0,
    look_ahead_distance=0.15,
    sample_count=512,
    inertia_weight=0.4
)

# Balanced (recommended for most applications)
plantarch.setSoftCollisionAvoidanceParameters(
    view_half_angle_deg=80.0,
    look_ahead_distance=0.1,
    sample_count=256,
    inertia_weight=0.4
)

# Fast (for rapid prototyping or large-scale simulations)
plantarch.setSoftCollisionAvoidanceParameters(
    view_half_angle_deg=60.0,
    look_ahead_distance=0.08,
    sample_count=128,
    inertia_weight=0.5
)
```

### Common Patterns

**Pattern 1: Dense Canopy with Self-Avoidance**

```python
# Plants avoid themselves and neighbors
plantarch.setSoftCollisionAvoidanceParameters(
    view_half_angle_deg=70.0,
    look_ahead_distance=0.08,
    sample_count=256,
    inertia_weight=0.3
)
plantarch.setCollisionRelevantOrgans(
    include_internodes=True,
    include_leaves=True,
    include_petioles=False,
    include_flowers=False,
    include_fruit=False
)
plantarch.enableSoftCollisionAvoidance()
```

**Pattern 2: Greenhouse with Infrastructure**

```python
# Create greenhouse structure
posts = []
for x in [-2, 2]:
    for y in [-2, 2]:
        posts.append(context.addPatch(vec3(x, y, 1), size=(0.1, 2)))

# Configure collision detection
plantarch.enableSoftCollisionAvoidance()
plantarch.setStaticObstacles(posts)  # Optimize for static posts
plantarch.enableSolidObstacleAvoidance(
    obstacle_UUIDs=posts,
    avoidance_distance=0.3
)
```

**Pattern 3: Field with Ground Clipping**

```python
# Prevent growth below ground
ground = context.addPatch(vec3(0, 0, 0), size=(20, 20))

plantarch.enableSolidObstacleAvoidance(
    obstacle_UUIDs=[ground],
    avoidance_distance=0.05,  # Very close to ground
    enable_fruit_adjustment=True  # Adjust fruit on ground
)
```

### Troubleshooting

**Problem: Plants still collide despite collision detection**

- Check that `enableSoftCollisionAvoidance()` was called before `advanceTime()`
- Increase `sample_count` for better detection accuracy
- Reduce `inertia_weight` for more responsive avoidance
- Verify collision-relevant organs are correctly configured

**Problem: Poor performance with collision detection**

- Mark static geometry with `setStaticObstacles()`
- Reduce `sample_count` (try 128 or 64)
- Reduce `view_half_angle_deg` (try 60° or 50°)
- Filter organs to leaves only
- Use larger time steps in `advanceTime()`

**Problem: `setStaticObstacles()` fails**

- Ensure `enableSoftCollisionAvoidance()` is called FIRST
- Static obstacles require collision detection to be active
- C++ library enforces this requirement

**Problem: Unnatural plant growth patterns**

- Increase `inertia_weight` for smoother growth (try 0.5-0.6)
- Reduce `look_ahead_distance` to react to closer obstacles only
- Check that obstacle geometry is correctly positioned

### Example Scripts

Complete working examples are available in `docs/examples/`:

- **`plantarch_collision_sample.py`**: Comprehensive collision detection examples including:
  - Basic soft collision avoidance
  - Parameter tuning for different scenarios
  - Hard obstacle avoidance with solid boundaries
  - Performance optimization with static obstacles
  - Organ-specific collision filtering
  - Complete realistic workflow

Run the examples:

```bash
python docs/examples/plantarch_collision_sample.py
```

## File I/O and Persistence

PlantArchitecture provides comprehensive file I/O capabilities to save and load plant structures, export geometry for external processing, and integrate with biomechanical analysis tools. These features enable plant structure persistence, library creation, and interoperability with other software.

### Overview

The following file I/O methods are available:

1. **`writePlantStructureXML()`**: Save complete plant structure to XML for later loading
2. **`readPlantStructureXML()`**: Load saved plant structures from XML files
3. **`writePlantMeshVertices()`**: Export all mesh vertices for external processing
4. **`writeQSMCylinderFile()`**: Export to TreeQSM format for biomechanical analysis
5. **`writePlantStructureUSD()`**: Export plant structure as a USD articulated rigid body for NVIDIA IsaacSim physics simulation
6. **`registerGrowthFrame()`** / **`writePlantGrowthUSD()`** / **`clearGrowthFrames()`** / **`getGrowthFrameCount()`**: Capture and export per-step growth snapshots as a time-sampled USD animation file (importable into Blender)

All methods work with both string paths and `pathlib.Path` objects, and correctly handle relative/absolute paths.

### Save and Load Plant Structures (XML)

XML format preserves complete plant architecture including shoot structure, organ properties, and growth state. This enables:
- Saving plant growth stages for later analysis
- Creating reusable plant libraries
- Sharing plant structures between simulations
- Checkpointing long-running simulations

**Basic Usage:**

```python
from pyhelios import Context, PlantArchitecture
from pyhelios.types import *

# Save plant to XML
with Context() as context:
    with PlantArchitecture(context) as plantarch:
        plantarch.loadPlantModelFromLibrary("bean")
        plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), age=30.0)

        # Grow plant
        plantarch.advanceTime(15.0)

        # Save to XML
        plantarch.writePlantStructureXML(plant_id, "bean_day45.xml")
        print("Plant saved successfully")

# Load plant from XML (in new context)
with Context() as context:
    with PlantArchitecture(context) as plantarch:
        # Must load model before reading XML
        plantarch.loadPlantModelFromLibrary("bean")

        # Load saved plant(s)
        plant_ids = plantarch.readPlantStructureXML("bean_day45.xml")
        print(f"Loaded {len(plant_ids)} plant(s)")
```

**Known limitation**: calling `advanceTime()` on a plant restored from XML currently fails in the
native library with `ERROR (Tube::setTubeRadii): Number of radii in input vector must match number
of tube nodes.` Reloaded plants can be queried and rendered, but not grown further. Plants built
in-process with `buildPlantInstanceFromLibrary()` are unaffected.

**Important Notes:**
- Plant model must be loaded (`loadPlantModelFromLibrary()`) before calling `readPlantStructureXML()`
- XML files can contain multiple plants (returns list of plant IDs)
- Use `quiet=True` parameter to suppress console output during loading
- XML format is Helios-native and preserves all plant structure details

**Quiet Mode:**

```python
# Load without console output
plant_ids = plantarch.readPlantStructureXML("bean_day45.xml", quiet=True)
```

### Export Mesh Vertices

Export all vertex coordinates from plant geometry for external processing such as:
- Convex hull calculation
- Bounding volume computation
- Custom geometric analysis
- Integration with external modeling tools

**Basic Usage:**

```python
from pyhelios import Context, PlantArchitecture
from pyhelios.types import *

with Context() as context:
    with PlantArchitecture(context) as plantarch:
        # Create plant
        plantarch.loadPlantModelFromLibrary("tomato")
        plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), age=25.0)

        # Export vertices
        plantarch.writePlantMeshVertices(plant_id, "tomato_vertices.txt")
        print("Vertices exported successfully")

# Read and analyze exported vertices
with open("tomato_vertices.txt", 'r') as f:
    for i, line in enumerate(f.readlines()[:5]):
        x, y, z = line.strip().split()
        print(f"Vertex {i+1}: ({x}, {y}, {z})")
```

**Output Format:**
- Plain text file with one vertex per line
- Three space-separated floating-point values per line: `x y z`
- All vertices from all primitive meshes in the plant
- Coordinates in global coordinate system

**Example Applications:**

```python
import numpy as np

# Load vertices for analysis
vertices = np.loadtxt("tomato_vertices.txt")

# Calculate bounding box
min_coords = vertices.min(axis=0)
max_coords = vertices.max(axis=0)
print(f"Bounding box: {min_coords} to {max_coords}")

# Calculate plant volume (approximate with convex hull)
from scipy.spatial import ConvexHull
hull = ConvexHull(vertices)
volume = hull.volume
print(f"Convex hull volume: {volume:.3f} m³")
```

### Export TreeQSM Cylinder Format

Export plant structure in TreeQSM (Quantitative Structure Model) format for biomechanical analysis and structural modeling. TreeQSM is widely used in forestry and biomechanics research.

**Basic Usage:**

```python
from pyhelios import Context, PlantArchitecture
from pyhelios.types import *

with Context() as context:
    with PlantArchitecture(context) as plantarch:
        # Create tree
        plantarch.loadPlantModelFromLibrary("almond")
        plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), age=50.0)

        # Export to TreeQSM format
        plantarch.writeQSMCylinderFile(plant_id, "almond_qsm.txt")
        print("TreeQSM file exported successfully")
```

**TreeQSM Format Details:**

The exported file contains tab-separated values with the following information for each cylinder:
- Cylinder dimensions (radius, length)
- Spatial position and orientation
- Branch topology (parent, extension, branch IDs)
- Branch hierarchy (order, position in branch)
- Quality metrics (distance, coverage)

**Reference:** Raumonen et al. (2013) "Fast Automatic Precision Tree Models from Terrestrial Laser Scanner Data" *Remote Sensing* 5(2):491-520

**Use Cases:**
- Biomechanical modeling and structural analysis
- Wind resistance calculations
- Carbon storage estimation
- Tree architecture studies
- Integration with TreeQSM analysis tools

### Export USD Articulated Rigid Body (IsaacSim Physics)

Export the plant structure as a PhysX articulation in USDA (ASCII USD) format for NVIDIA IsaacSim physics simulation. Each tube segment becomes a capsule-shaped rigid link connected by spherical joints whose local frames encode the rest-pose orientation. Spring/damper drives are derived from beam bending stiffness (`K = E*I/L`). Leaves, fruits, and flowers are represented as mass bodies attached by spring links.

**Basic Usage:**

```python
from pyhelios import Context, PlantArchitecture
from pyhelios.types import *

with Context() as context:
    with PlantArchitecture(context) as plantarch:
        plantarch.loadPlantModelFromLibrary("almond")
        plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), age=50.0)

        # Default physics parameters
        plantarch.writePlantStructureUSD(plant_id, "almond.usda")

        # Custom physics parameters
        plantarch.writePlantStructureUSD(
            plant_id, "almond_custom.usda",
            elastic_modulus=8e9,         # Young's modulus (Pa)
            wood_density=750.0,          # kg/m^3
            damping_ratio=0.15,
            leaf_mass_per_area=0.04,     # kg/m^2
            fruit_mass=0.005,            # kg
        )
```

### Growth Animation Export (USD for Blender)

Capture per-step plant geometry snapshots during a growth simulation and export them as a time-sampled USDA animation that imports directly into Blender. Organs that appear during growth are toggled visible at the appropriate frame.

**Basic Usage:**

```python
from pyhelios import Context, PlantArchitecture
from pyhelios.types import *

with Context() as context:
    with PlantArchitecture(context) as plantarch:
        plantarch.loadPlantModelFromLibrary("bean")
        plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), age=5.0)

        # Capture a frame after each growth step
        for _ in range(10):
            plantarch.advanceTime(2.0)
            plantarch.registerGrowthFrame(plant_id)

        print(f"Captured {plantarch.getGrowthFrameCount(plant_id)} frames")

        # Export as a 1-second-per-frame animation
        plantarch.writePlantGrowthUSD(plant_id, "bean_growth.usda", seconds_per_frame=1.0)

        # Reset frame storage when done
        plantarch.clearGrowthFrames(plant_id)
```

This export is visual-only — no physics prims, joints, or collision shapes are written. For physics simulation, use `writePlantStructureUSD()` instead.

### Path Handling

All file I/O methods accept both string paths and `pathlib.Path` objects, and correctly handle relative/absolute paths while preserving the user's working directory.

**Using pathlib.Path:**

```python
from pathlib import Path
from pyhelios import Context, PlantArchitecture
from pyhelios.types import *

with Context() as context:
    with PlantArchitecture(context) as plantarch:
        plantarch.loadPlantModelFromLibrary("bean")
        plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), age=20.0)

        # Create output directory
        output_dir = Path("plant_data")
        output_dir.mkdir(exist_ok=True)

        # All methods work with Path objects
        vertices_file = output_dir / "vertices.txt"
        plantarch.writePlantMeshVertices(plant_id, vertices_file)

        xml_file = output_dir / "plant.xml"
        plantarch.writePlantStructureXML(plant_id, xml_file)

        qsm_file = output_dir / "qsm.txt"
        plantarch.writeQSMCylinderFile(plant_id, qsm_file)

        print(f"All files saved to {output_dir.absolute()}")
```

**Path Features:**
- Works with both relative and absolute paths
- User's working directory is preserved across all operations
- Automatic path resolution before C++ operations
- Compatible with `pathlib.Path` and string paths

### Creating Plant Libraries

Save plants at different growth stages to build reusable libraries:

```python
from pathlib import Path
from pyhelios import Context, PlantArchitecture
from pyhelios.types import *

# Create library directory
library_dir = Path("soybean_library")
library_dir.mkdir(exist_ok=True)

with Context() as context:
    with PlantArchitecture(context) as plantarch:
        plantarch.loadPlantModelFromLibrary("soybean")

        # Save plants at multiple growth stages
        growth_stages = [10, 20, 30, 40, 50]  # days

        for age in growth_stages:
            # Create plant at this age
            plant_id = plantarch.buildPlantInstanceFromLibrary(
                base_position=vec3(0, 0, 0),
                age=float(age)
            )

            # Save to library
            filename = library_dir / f"soybean_day{age}.xml"
            plantarch.writePlantStructureXML(plant_id, str(filename))

            # Get statistics
            uuids = plantarch.getAllPlantUUIDs(plant_id)
            print(f"Day {age}: {len(uuids)} primitives -> {filename.name}")

print(f"\nCreated library with {len(growth_stages)} growth stages")
print(f"Library location: {library_dir.absolute()}")
```

**Using the Library:**

```python
# Load specific growth stage from library
with Context() as context:
    with PlantArchitecture(context) as plantarch:
        plantarch.loadPlantModelFromLibrary("soybean")

        # Load day 30 plant
        library_file = Path("soybean_library/soybean_day30.xml")
        plant_ids = plantarch.readPlantStructureXML(str(library_file))
        print(f"Loaded plant {plant_ids[0]} from library")

        # Continue growing from library state
        plantarch.advanceTime(10.0)
```

### Multi-Plant Canopy Persistence

Save and load entire canopies for complex scene persistence:

```python
from pathlib import Path
from pyhelios import Context, PlantArchitecture
from pyhelios.types import *

# Save canopy
with Context() as context:
    with PlantArchitecture(context) as plantarch:
        plantarch.loadPlantModelFromLibrary("bean")

        # Create 3x3 canopy
        plant_ids = plantarch.buildPlantCanopyFromLibrary(
            canopy_center=vec3(0, 0, 0),
            plant_spacing=vec2(0.5, 0.5),
            plant_count=int2(3, 3),
            age=25.0
        )

        # Grow canopy
        plantarch.advanceTime(15.0)

        # Save each plant
        canopy_dir = Path("bean_canopy")
        canopy_dir.mkdir(exist_ok=True)

        for i, plant_id in enumerate(plant_ids):
            filename = canopy_dir / f"plant_{i}.xml"
            plantarch.writePlantStructureXML(plant_id, str(filename))

        print(f"Saved {len(plant_ids)} plants to {canopy_dir}")

# Load canopy
with Context() as context:
    with PlantArchitecture(context) as plantarch:
        plantarch.loadPlantModelFromLibrary("bean")

        loaded_plants = []
        for i in range(9):  # 3x3 = 9 plants
            filename = Path(f"bean_canopy/plant_{i}.xml")
            plant_ids = plantarch.readPlantStructureXML(str(filename), quiet=True)
            loaded_plants.extend(plant_ids)

        print(f"Loaded {len(loaded_plants)} plants from canopy")

        # Continue simulation
        plantarch.advanceTime(10.0)
```

### Integration Workflow Examples

**Workflow 1: Growth Time Series**

```python
from pyhelios import Context, PlantArchitecture
from pyhelios.types import *

with Context() as context:
    with PlantArchitecture(context) as plantarch:
        plantarch.loadPlantModelFromLibrary("maize")
        plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), age=10.0)

        # Save snapshots at regular intervals
        time_series = [0, 5, 10, 15, 20]  # days from now

        for days in time_series:
            if days > 0:
                plantarch.advanceTime(float(days))

            # Save structure
            plantarch.writePlantStructureXML(plant_id, f"maize_t{days}.xml")

            # Export geometry
            plantarch.writePlantMeshVertices(plant_id, f"maize_t{days}_vertices.txt")

            print(f"Saved snapshot at t={days} days")
```

**Workflow 2: External Analysis Pipeline**

```python
from pyhelios import Context, PlantArchitecture
from pyhelios.types import *
import numpy as np

with Context() as context:
    with PlantArchitecture(context) as plantarch:
        plantarch.loadPlantModelFromLibrary("walnut")
        plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), age=100.0)

        # Export for different analysis types

        # 1. TreeQSM format for biomechanics
        plantarch.writeQSMCylinderFile(plant_id, "walnut_biomech.txt")

        # 2. Vertices for convex hull analysis
        plantarch.writePlantMeshVertices(plant_id, "walnut_verts.txt")

        # 3. XML for archival
        plantarch.writePlantStructureXML(plant_id, "walnut_archive.xml")

        print("Exported to multiple formats for external analysis")

# External processing
vertices = np.loadtxt("walnut_verts.txt")
print(f"Loaded {len(vertices)} vertices for analysis")

# Your analysis code here...
```

### Error Handling

File I/O operations include comprehensive error handling:

```python
from pyhelios import Context, PlantArchitecture, PlantArchitectureError
from pyhelios.types import *

with Context() as context:
    with PlantArchitecture(context) as plantarch:
        plantarch.loadPlantModelFromLibrary("bean")
        plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), age=20.0)

        try:
            # Attempt write operation
            plantarch.writePlantStructureXML(plant_id, "output/plant.xml")
        except PlantArchitectureError as e:
            print(f"Write failed: {e}")
            # Handle error (e.g., create directory)

        try:
            # Attempt read operation
            plant_ids = plantarch.readPlantStructureXML("nonexistent.xml")
        except PlantArchitectureError as e:
            print(f"Read failed: {e}")
            # Handle error

        # Parameter validation
        try:
            plantarch.writePlantStructureXML(-1, "plant.xml")
        except ValueError as e:
            print(f"Invalid parameter: {e}")
```

**Common Errors:**
- `ValueError`: Invalid parameters (negative plant ID, empty filename)
- `PlantArchitectureError`: File operation failed (permissions, missing file, invalid XML)
- Model not loaded before `readPlantStructureXML()` (must call `loadPlantModelFromLibrary()` first)

### Example Scripts

Complete working examples are available in `docs/examples/`:

- **`plantarch_file_io_sample.py`**: Comprehensive file I/O examples including:
  - Saving and loading plant structures
  - Exporting mesh vertices for external processing
  - TreeQSM format export for biomechanics
  - Creating plant libraries with growth stages
  - Multi-plant canopy persistence
  - Flexible path handling with pathlib

Run the examples:

```bash
python docs/examples/plantarch_file_io_sample.py
```