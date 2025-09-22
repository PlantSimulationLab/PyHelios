#!/usr/bin/env python3
"""
PlantArchitecture Visualizer Example

This example demonstrates how to create plants using the PlantArchitecture plugin
and visualize them using the Visualizer plugin. It creates a small mixed-species
garden with different plant types at various growth stages.

Requirements:
- PlantArchitecture plugin (for plant generation)
- Visualizer plugin (for 3D visualization)

Usage:
    python docs/examples/plantarchitecture_visualizer_example.py
"""

from pyhelios import Context, PlantArchitecture, Visualizer
from pyhelios.types import *

def main():
    """Create a mixed-species plant garden and visualize it."""

    print("PlantArchitecture + Visualizer Example")
    print("=" * 50)

    with Context() as context:

        context.addTile(vec3(0,0,0), vec2(10,10), SphericalCoord(1,0,0), int2(5,5), RGBcolor(0.5,0.5,0.5))

        with PlantArchitecture(context) as plantarch:
            print("[OK] PlantArchitecture plugin available")

            # Get available plant models
            models = plantarch.getAvailablePlantModels()
            print(f"Available plant models: {len(models)}")
            print(f"Examples: {', '.join(models[:5])}{'...' if len(models) > 5 else ''}")

            # Create a diverse garden layout
            print("\nCreating plant garden...")

            # Define plant positions and species for a small garden
            garden_plants = [
                # Agricultural crops in a row
                ("bean", vec3(-1, -1, 0), 25.0),
                ("maize", vec3(0, -1, 0), 35.0),
                ("soybean", vec3(1, -1, 0), 30.0),

                # Vegetables in middle row
                ("tomato", vec3(-1, 1, 0), 40.0),
                ("groundcherryweed", vec3(-0, 1, 0), 28.0),
                ("strawberry", vec3(1, 1, 0), 20.0),
            ]

            created_plants = []

            for species, position, age in garden_plants:
                # Load the plant model
                plantarch.loadPlantModelFromLibrary(species)

                # Create plant instance
                plant_id = plantarch.buildPlantInstanceFromLibrary(position, age)
                created_plants.append((species, plant_id, age))

                print(f"  + {species.capitalize():12} at {position} (age: {age:2.0f} days) -> ID: {plant_id}")

            # Simulate some growth
            print("\nAdvancing plant growth by 7 days...")
            plantarch.advanceTime(35.0)

            # Display plant statistics
            total_primitives = context.getPrimitiveCount()
            print(f"\nGarden Statistics:")
            print(f"  Plants created: {len(created_plants)}")
            print(f"  Total primitives: {total_primitives}")

            # Get detailed plant information
            for species, plant_id, initial_age in created_plants:
                object_ids = plantarch.getAllPlantObjectIDs(plant_id)
                uuids = plantarch.getAllPlantUUIDs(plant_id)
                print(f"  {species.capitalize():12}: {len(object_ids):3d} objects, {len(uuids):4d} primitives")

        with Visualizer(800, 500) as vis:

            # Set up visualization
            vis.buildContextGeometry(context)

            vis.setLightingModel("phong_shadowed")

            print("Starting visualization...")
            print("Close the visualizer window when done viewing.")
            vis.plotInteractive()

if __name__ == "__main__":
    main()