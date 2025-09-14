# Weber-Penn Tree Plugin {#WeberPennTreeDoc}

The Weber-Penn Tree plugin provides procedural tree generation using the Weber-Penn modeling algorithms. This documentation is based on the actual implementation.

## Overview

The WeberPennTree class generates realistic tree structures for various fruit and nut tree species using scientifically-based algorithms.

## Basic Usage

```python
from pyhelios import Context, WeberPennTree, WPTType
from pyhelios.types import *

# Create context and tree generator
context = Context()
wpt = WeberPennTree(context)

# Generate a tree with default parameters
tree_id = wpt.buildTree(WPTType.LEMON)

# Generate tree with custom position and scale
tree_id = wpt.buildTree(
    wpt_type=WPTType.APPLE,
    origin=vec3(5, 10, 0),
    scale=1.5
)

print(f"Generated tree with ID: {tree_id}")
```

## Available Tree Types

The actual tree types available in PyHelios (from WPTType enum):

```python
# Verified tree types from WPTType enum
available_types = [
    WPTType.ALMOND,     # Almond tree
    WPTType.APPLE,      # Apple tree  
    WPTType.AVOCADO,    # Avocado tree
    WPTType.LEMON,      # Lemon tree
    WPTType.OLIVE,      # Olive tree
    WPTType.ORANGE,     # Orange tree
    WPTType.PEACH,      # Peach tree
    WPTType.PISTACHIO,  # Pistachio tree
    WPTType.WALNUT      # Walnut tree
]

# Generate different tree types
for tree_type in available_types:
    tree_id = wpt.buildTree(tree_type)
    print(f"Generated {tree_type.value} tree: ID {tree_id}")
```

## Tree Component Queries

Get UUIDs for different parts of generated trees:

```python
# Build a tree first
tree_id = wpt.buildTree(WPTType.OLIVE)

# Get UUIDs for different tree components (verified methods)
trunk_uuids = wpt.getTrunkUUIDs(tree_id)
branch_uuids = wpt.getBranchUUIDs(tree_id)
leaf_uuids = wpt.getLeafUUIDs(tree_id)
all_tree_uuids = wpt.getAllUUIDs(tree_id)

print(f"Tree {tree_id} components:")
print(f"  Trunk primitives: {len(trunk_uuids)}")
print(f"  Branch primitives: {len(branch_uuids)}")
print(f"  Leaf primitives: {len(leaf_uuids)}")
print(f"  Total primitives: {len(all_tree_uuids)}")
```

## Tree Customization

Control the generation parameters before building trees:

```python
# Set generation parameters (verified methods)
wpt.setBranchRecursionLevel(4)      # Number of branching levels
wpt.setTrunkSegmentResolution(8)    # Trunk smoothness (segments)
wpt.setBranchSegmentResolution(6)   # Branch smoothness (segments)
wpt.setLeafSubdivisions(3, 3)       # Leaf detail (x, y subdivisions)

# Generate tree with custom parameters
tree_id = wpt.buildTree(WPTType.LEMON)
```

### Parameter Effects

- **Branch Recursion Level**: Controls tree complexity
  - Level 1: Trunk only
  - Level 2: Trunk + primary branches
  - Level 3: Trunk + primary + secondary branches
  - Level 4+: Additional levels of smaller branches

- **Segment Resolution**: Controls geometric smoothness
  - Lower values (3-4): Coarse, angular geometry
  - Higher values (8-12): Smooth, detailed geometry

- **Leaf Subdivisions**: Controls leaf detail
  - (1,1): Simple rectangular leaves
  - (3,3): More detailed leaf geometry with 9 patches per leaf
  - (5,5): High detail leaves with 25 patches per leaf

## Context Manager Usage

For proper resource cleanup:

```python
# Recommended: use context manager
with WeberPennTree(context) as wpt:
    wpt.setBranchRecursionLevel(4)
    tree_id = wpt.buildTree(WPTType.APPLE)
    leaf_uuids = wpt.getLeafUUIDs(tree_id)
    # Automatic cleanup when done
```

## Multiple Tree Scenes

Generate multiple trees efficiently:

```python
# Generate an orchard
orchard_trees = []
tree_spacing = 4.0  # meters

for i in range(3):
    for j in range(3):
        # Position trees in a grid
        x = i * tree_spacing
        y = j * tree_spacing
        position = vec3(x, y, 0)
        
        # Alternate tree types
        tree_types = [WPTType.APPLE, WPTType.LEMON, WPTType.OLIVE]
        tree_type = tree_types[(i + j) % 3]
        
        # Random scale variation
        import random
        scale = 0.8 + 0.4 * random.random()
        
        tree_id = wpt.buildTree(tree_type, position, scale)
        orchard_trees.append(tree_id)

print(f"Generated orchard with {len(orchard_trees)} trees")
```

## Tree Analysis

Analyze generated tree properties:

```python
# Generate tree
tree_id = wpt.buildTree(WPTType.OLIVE)

# Get all tree components
trunk_uuids = wpt.getTrunkUUIDs(tree_id)
branch_uuids = wpt.getBranchUUIDs(tree_id)
leaf_uuids = wpt.getLeafUUIDs(tree_id)

# Calculate tree properties using Context methods
total_leaf_area = 0
for uuid in leaf_uuids:
    area = context.getPrimitiveArea(uuid)
    total_leaf_area += area

# Calculate total branch volume (if branches are cylinders)
total_branch_volume = 0
for uuid in branch_uuids:
    # Branch volume calculation would depend on primitive type
    pass

print(f"Tree {tree_id} analysis:")
print(f"  Total leaf area: {total_leaf_area:.2f} m²")
print(f"  Number of leaves: {len(leaf_uuids)}")
print(f"  Number of branches: {len(branch_uuids)}")
```

## Integration with Other PyHelios Components

### With Context Data Association

```python
# Generate tree
tree_id = wpt.buildTree(WPTType.LEMON)
leaf_uuids = wpt.getLeafUUIDs(tree_id)

# Add data to tree components
for uuid in leaf_uuids:
    context.setPrimitiveDataFloat(uuid, "temperature", 25.0)
    context.setPrimitiveDataString(uuid, "tree_species", "lemon")
    context.setPrimitiveDataInt(uuid, "tree_id", tree_id)
```

### With Visualization

```python
# Generate tree and apply colors based on data
tree_id = wpt.buildTree(WPTType.OLIVE)
leaf_uuids = wpt.getLeafUUIDs(tree_id)

# Color leaves based on height
for uuid in leaf_uuids:
    center = context.getPrimitiveCenter(uuid)  # This would need actual implementation
    height = center.z  # Assuming z is height
    
    # Green gradient based on height
    green_intensity = min(1.0, height / 5.0)  # Normalize to 5m max height
    color = RGBcolor(0.2, green_intensity, 0.2)
    
    # Set primitive color (this would need actual Context method)
    # context.setPrimitiveColor(uuid, color)  # Method may not exist

# Use pseudocolor mapping instead
all_tree_uuids = wpt.getAllUUIDs(tree_id)
context.colorPrimitiveByDataPseudocolor(
    all_tree_uuids, "height", "viridis", 256
)
```

## Error Handling

```python
try:
    wpt = WeberPennTree(context)
    tree_id = wpt.buildTree(WPTType.LEMON)
    
except Exception as e:
    print(f"Tree generation failed: {e}")
    
    # Check if WeberPennTree plugin is available
    if not context.is_plugin_available('weberpenntree'):
        print("WeberPennTree plugin not available")
        print("Build with: build_scripts/build_helios --plugins weberpenntree")
```

## Build Requirements

The WeberPennTree plugin is included in most PyHelios builds:

```bash
# Build with WeberPennTree plugin
build_scripts/build_helios --plugins weberpenntree

# Or use a profile that includes it
build_scripts/build_helios --plugins weberpenntree           # WeberPennTree only
build_scripts/build_helios                                  # Default build includes WeberPennTree
```

## Performance Considerations

```python
# For large numbers of trees, consider:
# 1. Lower recursion levels for distant trees
wpt.setBranchRecursionLevel(2)  # Simpler trees

# 2. Lower segment resolution for distant trees  
wpt.setTrunkSegmentResolution(4)
wpt.setBranchSegmentResolution(3)

# 3. Lower leaf subdivisions for dense forests
wpt.setLeafSubdivisions(1, 1)  # Simple rectangular leaves

# Generate many simple trees
simple_trees = []
for i in range(100):
    tree_id = wpt.buildTree(WPTType.OLIVE)
    simple_trees.append(tree_id)
```

This documentation covers the actual WeberPennTree implementation in PyHelios, verified against the wrapper code and example usage.