#!/usr/bin/env python3
"""
PlantArchitecture Plugin Sample

This example demonstrates the PyHelios PlantArchitecture plugin for procedural
plant modeling and plant library functionality. The PlantArchitecture plugin
provides access to 30 plant models with time-based growth simulation.

Requirements:
- PyHelios built with PlantArchitecture support:
  build_scripts/build_helios --plugins plantarchitecture

Plant Library Models:
- Trees: almond, apple, olive, walnut, easternredbud
- Crops: bean, cowpea, maize, rice, soybean, wheat, sorghum
- Vegetables: tomato, cherrytomato, capsicum, strawberry
- Others: grapevine_VSP, pistachio, bindweed, puncturevine

Features Demonstrated:
1. Plant model discovery and loading
2. Individual plant instance creation
3. Plant canopy generation
4. Time-based plant growth simulation
5. Plant geometry queries and analysis
"""

import os
import sys
from pathlib import Path

# Add PyHelios to path if running from examples directory
if __name__ == "__main__":
    script_dir = Path(__file__).parent.absolute()
    pyhelios_root = script_dir.parent.parent
    if pyhelios_root not in sys.path:
        sys.path.insert(0, str(pyhelios_root))

import pyhelios
from pyhelios import Context, PlantArchitecture, PlantArchitectureError
from pyhelios.types import vec3, vec2, int2, RGBcolor


def main():
    """Main demonstration function"""
    print("="*60)
    print("PyHelios PlantArchitecture Plugin Sample")
    print("="*60)

    # Check if PlantArchitecture is available
    print("1. Checking PlantArchitecture availability...")
    try:
        from pyhelios.PlantArchitecture import is_plantarchitecture_available
        if not is_plantarchitecture_available():
            print("❌ PlantArchitecture plugin not available")
            print("   Rebuild PyHelios with: build_scripts/build_helios --plugins plantarchitecture")
            return
        print("✅ PlantArchitecture plugin available")
    except ImportError:
        print("❌ PlantArchitecture module not found")
        print("   Rebuild PyHelios with: build_scripts/build_helios --plugins plantarchitecture")
        return

    # Create context and PlantArchitecture instance
    print("\n2. Initializing PlantArchitecture...")
    try:
        with Context() as context:
            with PlantArchitecture(context) as plantarch:
                print("✅ PlantArchitecture initialized successfully")

                # Discover available plant models
                discover_plant_models(plantarch)

                # Load and use a plant model
                plant_model = select_plant_model(plantarch)
                if plant_model:
                    # Demonstrate individual plant creation
                    demonstrate_individual_plant(plantarch, plant_model, context)

                    # Demonstrate canopy creation
                    demonstrate_plant_canopy(plantarch, plant_model, context)

                    # Demonstrate time-based growth
                    grown_plant_id = demonstrate_plant_growth(plantarch, plant_model, context)

                    # Analyze plant geometry
                    analyze_plant_geometry(plantarch, context, grown_plant_id)

                print("\n✅ PlantArchitecture demonstration completed successfully")

    except PlantArchitectureError as e:
        print(f"❌ PlantArchitecture error: {e}")
        return 1
    # Any other exception is a genuine bug: let it propagate with its traceback
    # rather than reporting success. Catching it here would make a broken example
    # exit 0 and look like it worked.

    return 0


def discover_plant_models(plantarch):
    """Discover and display available plant models"""
    print("\n3. Discovering available plant models...")
    try:
        models = plantarch.getAvailablePlantModels()
        print(f"✅ Found {len(models)} plant models:")

        # Group models by category for better display
        trees = [m for m in models if m in ['almond', 'apple', 'olive', 'walnut', 'easternredbud', 'pistachio']]
        crops = [m for m in models if m in ['bean', 'cowpea', 'maize', 'rice', 'soybean', 'wheat', 'sorghum']]
        vegetables = [m for m in models if m in ['tomato', 'cherrytomato', 'capsicum', 'strawberry', 'sugarbeet']]
        others = [m for m in models if m not in trees + crops + vegetables]

        if trees:
            print(f"   Trees ({len(trees)}): {', '.join(sorted(trees))}")
        if crops:
            print(f"   Crops ({len(crops)}): {', '.join(sorted(crops))}")
        if vegetables:
            print(f"   Vegetables ({len(vegetables)}): {', '.join(sorted(vegetables))}")
        if others:
            print(f"   Others ({len(others)}): {', '.join(sorted(others))}")

        return models

    except PlantArchitectureError as e:
        print(f"❌ Error discovering plant models: {e}")
        return []


def select_plant_model(plantarch):
    """Select a plant model for demonstration"""
    print("\n4. Selecting plant model for demonstration...")
    try:
        models = plantarch.getAvailablePlantModels()
        if not models:
            print("❌ No plant models available")
            return None

        # Prefer certain models for demonstration
        preferred_models = ['bean', 'maize', 'soybean', 'tomato', 'almond', 'apple']
        selected_model = None

        for model in preferred_models:
            if model in models:
                selected_model = model
                break

        if not selected_model:
            selected_model = models[0]

        print(f"🌱 Selected model: {selected_model}")
        return selected_model

    except PlantArchitectureError as e:
        print(f"❌ Error selecting plant model: {e}")
        return None


def demonstrate_individual_plant(plantarch, plant_model, context):
    """Demonstrate creating individual plant instances"""
    print(f"\n5. Creating individual {plant_model} plants...")
    try:
        # Load the plant model
        plantarch.loadPlantModelFromLibrary(plant_model)
        print(f"✅ Loaded {plant_model} model from library")

        # Create plants at different ages
        ages = [10, 20, 30, 45]
        positions = [
            vec3(-2, 0, 0),
            vec3(-1, 0, 0),
            vec3(1, 0, 0),
            vec3(2, 0, 0)
        ]

        plant_ids = []
        for i, (pos, age) in enumerate(zip(positions, ages)):
            plant_id = plantarch.buildPlantInstanceFromLibrary(pos, age)
            plant_ids.append(plant_id)
            print(f"   Plant {i+1}: ID {plant_id} at {[pos.x, pos.y, pos.z]} with age {age} days")

        print(f"✅ Created {len(plant_ids)} individual plants")
        return plant_ids

    except PlantArchitectureError as e:
        print(f"❌ Error creating individual plants: {e}")
        return []


def demonstrate_plant_canopy(plantarch, plant_model, context):
    """Demonstrate creating plant canopies"""
    print(f"\n6. Creating {plant_model} canopy...")
    try:
        # Create a small canopy
        canopy_center = vec3(0, 5, 0)  # Offset from individual plants
        plant_spacing = vec2(0.8, 0.8)  # 80cm spacing
        plant_count = int2(3, 3)  # 3x3 grid
        age = 25.0  # 25-day-old plants

        plant_ids = plantarch.buildPlantCanopyFromLibrary(
            canopy_center, plant_spacing, plant_count, age
        )

        print(f"✅ Created canopy with {len(plant_ids)} plants")
        print(f"   Center: [{canopy_center.x}, {canopy_center.y}, {canopy_center.z}]")
        print(f"   Spacing: {plant_spacing.x}m x {plant_spacing.y}m")
        print(f"   Grid: {plant_count.x} x {plant_count.y} plants")
        print(f"   Age: {age} days")

        return plant_ids

    except PlantArchitectureError as e:
        print(f"❌ Error creating plant canopy: {e}")
        return []


def demonstrate_plant_growth(plantarch, plant_model, context):
    """Demonstrate time-based plant growth"""
    print(f"\n7. Demonstrating {plant_model} growth simulation...")
    try:
        # Create a plant for growth demonstration
        position = vec3(5, 0, 0)  # Separate from other plants
        initial_age = 15.0

        plant_id = plantarch.buildPlantInstanceFromLibrary(position, initial_age)
        print(f"✅ Created plant ID {plant_id} at age {initial_age} days")

        # Count only this plant's primitives. context.getPrimitiveCount() covers
        # the whole scene, so it would also fold in growth of the other plants
        # created earlier in this example.
        previous_primitives = len(plantarch.getAllPlantUUIDs(plant_id))

        # Simulate growth over time
        growth_steps = [5, 10, 15, 20]  # Days to advance
        for i, time_step in enumerate(growth_steps):
            plantarch.advanceTime(time_step)
            current_age = initial_age + sum(growth_steps[:i+1])

            # Delta since the previous step, not since the start.
            current_primitives = len(plantarch.getAllPlantUUIDs(plant_id))
            primitive_change = current_primitives - previous_primitives
            previous_primitives = current_primitives

            print(f"   Step {i+1}: Advanced {time_step} days (age: {current_age} days)")
            print(f"            Plant primitives: {current_primitives} (Δ{primitive_change:+d} this step)")

        total_growth = sum(growth_steps)
        final_age = initial_age + total_growth
        print(f"✅ Growth simulation completed: {initial_age} → {final_age} days")

        return plant_id

    except PlantArchitectureError as e:
        print(f"❌ Error in growth simulation: {e}")
        return None


def analyze_plant_geometry(plantarch, context, plant_id):
    """Analyze plant geometry and structure"""
    print(f"\n8. Analyzing plant geometry...")
    try:
        # Get all plants in the scene
        total_primitives = context.getPrimitiveCount()
        print(f"✅ Total scene primitives: {total_primitives}")

        # Analyze the plant we actually grew. Plant IDs are assigned in
        # creation order starting at 0, so guessing an ID silently analyses a
        # different plant than intended.
        test_plant_id = plant_id

        try:
            # Get object IDs for the plant
            object_ids = plantarch.getAllPlantObjectIDs(test_plant_id)
            uuids = plantarch.getAllPlantUUIDs(test_plant_id)

            print(f"✅ Plant {test_plant_id} analysis:")
            print(f"   Object IDs: {len(object_ids)} objects")
            print(f"   UUIDs: {len(uuids)} primitives")

            if object_ids:
                print(f"   First few object IDs: {object_ids[:5]}")
            if uuids:
                print(f"   First few UUIDs: {uuids[:5]}")

        except PlantArchitectureError as e:
            print(f"   ⚠️  Could not analyze plant {test_plant_id}: {e}")

        # Scene summary
        print(f"\n📊 Scene Summary:")
        print(f"   Total primitives in context: {total_primitives}")
        print(f"   Plant models demonstrated: procedural generation with growth")

    except PlantArchitectureError as e:
        print(f"❌ Error analyzing geometry: {e}")


def print_usage_tips():
    """Print usage tips for PlantArchitecture"""
    print("\n" + "="*60)
    print("PlantArchitecture Usage Tips")
    print("="*60)
    print("1. Always use context managers for proper resource cleanup")
    print("2. Load plant models before building instances")
    print("3. Use appropriate ages for realistic plant development")
    print("4. Consider plant spacing when creating canopies")
    print("5. Growth simulation can be CPU intensive for large canopies")
    print("6. Assets must be available in the build directory")
    print("7. Check plugin availability before use")


if __name__ == "__main__":
    try:
        exit_code = main()
        print_usage_tips()
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(130)
    # Other exceptions propagate so the traceback is visible and the exit code
    # is non-zero.
    sys.exit(exit_code)