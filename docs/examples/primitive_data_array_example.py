#!/usr/bin/env python3
"""
Example demonstrating the getPrimitiveDataArray() method in PyHelios.

This example shows how to efficiently retrieve primitive data from multiple
primitives as NumPy arrays, which is useful for analysis and visualization.
"""

import numpy as np
from pyhelios import Context
from pyhelios.types import *


def main():
    print("PyHelios getPrimitiveDataArray() Example")
    print("=" * 45)
    
    # Create a context
    with Context() as context:
        # Create a grid of patches and assign data
        patch_uuids = []
        print("\n1. Creating patches and setting primitive data...")
        
        for i in range(5):
            for j in range(3):
                # Create patch at grid position
                uuid = context.addPatch(center=vec3(i * 2.0, j * 2.0, 0.0), size=vec2(1.5, 1.5))
                
                # Set various types of primitive data
                context.setPrimitiveDataFloat(uuid, "temperature", 20.0 + i * 2.5 + j * 1.2)
                context.setPrimitiveDataInt(uuid, "leaf_count", 50 + i * 10 + j * 5)
                context.setPrimitiveDataString(uuid, "species", f"species_{i}_{j}")
                context.setPrimitiveDataFloat(uuid, "height", 1.0 + i * 0.3 + j * 0.2)
                
                patch_uuids.append(uuid)
        
        print(f"Created {len(patch_uuids)} patches with primitive data")
        
        # Demonstrate getPrimitiveDataArray() with different data types
        print("\n2. Retrieving data arrays...")
        
        # Get temperature data (float)
        temperatures = context.getPrimitiveDataArray(patch_uuids, "temperature")
        print(f"Temperatures: dtype={temperatures.dtype}, shape={temperatures.shape}")
        print(f"  Min: {temperatures.min():.1f}, Max: {temperatures.max():.1f}, Mean: {temperatures.mean():.1f}")
        
        # Get leaf count data (int)
        leaf_counts = context.getPrimitiveDataArray(patch_uuids, "leaf_count")
        print(f"Leaf counts: dtype={leaf_counts.dtype}, shape={leaf_counts.shape}")
        print(f"  Min: {leaf_counts.min()}, Max: {leaf_counts.max()}, Total: {leaf_counts.sum()}")
        
        # Get species data (string)
        species_names = context.getPrimitiveDataArray(patch_uuids, "species")
        print(f"Species: dtype={species_names.dtype}, shape={species_names.shape}")
        print(f"  Unique species: {len(np.unique(species_names))}")
        print(f"  First few: {list(species_names[:3])}")
        
        # Get height data (float)
        heights = context.getPrimitiveDataArray(patch_uuids, "height")
        print(f"Heights: dtype={heights.dtype}, shape={heights.shape}")
        print(f"  Range: {heights.min():.2f} - {heights.max():.2f}")
        
        # Demonstrate data analysis using NumPy
        print("\n3. Data analysis with NumPy...")
        
        # Find patches with high temperature
        hot_mask = temperatures > 25.0
        hot_patches = [patch_uuids[i] for i in range(len(patch_uuids)) if hot_mask[i]]
        print(f"Patches with temperature > 25°C: {len(hot_patches)}")
        
        # Find correlation between height and leaf count
        correlation = np.corrcoef(heights, leaf_counts.astype(float))[0, 1]
        print(f"Correlation between height and leaf count: {correlation:.3f}")
        
        # Group analysis by species
        unique_species = np.unique(species_names)
        print(f"\nAnalysis by species:")
        for species in unique_species[:3]:  # Show first 3 species
            mask = species_names == species
            avg_temp = temperatures[mask].mean()
            avg_leaves = leaf_counts[mask].mean()
            print(f"  {species}: avg temp={avg_temp:.1f}°C, avg leaves={avg_leaves:.0f}")
        
        # Demonstrate error handling
        print("\n4. Error handling demonstration...")
        
        try:
            # Try to get data that doesn't exist
            nonexistent_data = context.getPrimitiveDataArray(patch_uuids, "nonexistent_label")
        except ValueError as e:
            print(f"Expected error for non-existent data: {e}")
        
        try:
            # Try with empty UUID list
            empty_data = context.getPrimitiveDataArray([], "temperature")
        except ValueError as e:
            print(f"Expected error for empty UUID list: {e}")
        
        # Demonstrate mixed primitive types
        print("\n5. Mixed primitive types...")
        
        # Add some triangles
        triangle_uuids = []
        for i in range(3):
            uuid = context.addTriangle(
                vec3(i * 3.0, -2.0, 0.0),
                vec3(i * 3.0 + 1.0, -2.0, 0.0),
                vec3(i * 3.0 + 0.5, -1.0, 0.0)
            )
            context.setPrimitiveDataFloat(uuid, "surface_roughness", 0.1 + i * 0.05)
            triangle_uuids.append(uuid)
        
        # Get data from triangles
        roughness = context.getPrimitiveDataArray(triangle_uuids, "surface_roughness")
        print(f"Triangle surface roughness: {roughness}")
        
        # Combine patch and triangle data (same label)
        all_uuids = patch_uuids + triangle_uuids
        for uuid in triangle_uuids:
            context.setPrimitiveDataFloat(uuid, "temperature", 15.0)  # Cooler triangles
        
        all_temperatures = context.getPrimitiveDataArray(all_uuids, "temperature")
        print(f"Combined temperatures (patches + triangles): shape={all_temperatures.shape}")
        print(f"  Patch temps: {all_temperatures[:len(patch_uuids)].mean():.1f}°C")
        print(f"  Triangle temps: {all_temperatures[len(patch_uuids):].mean():.1f}°C")
        
        print("\n6. Performance comparison...")
        
        # Compare single vs array retrieval for larger dataset
        import time
        
        # Individual calls
        start_time = time.time()
        individual_temps = []
        for uuid in patch_uuids:
            individual_temps.append(context.getPrimitiveDataFloat(uuid, "temperature"))
        individual_time = time.time() - start_time
        
        # Array call
        start_time = time.time()
        array_temps = context.getPrimitiveDataArray(patch_uuids, "temperature")
        array_time = time.time() - start_time
        
        print(f"Individual calls: {individual_time*1000:.1f} ms")
        print(f"Array call: {array_time*1000:.1f} ms")
        print(f"Array is {individual_time/array_time:.1f}x faster")
        
        # Verify results are identical
        np.testing.assert_array_almost_equal(individual_temps, array_temps)
        print("Results are identical ✓")


if __name__ == "__main__":
    main()