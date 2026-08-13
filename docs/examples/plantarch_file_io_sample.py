"""
PlantArchitecture File I/O Example

This example demonstrates the file input/output capabilities of the PlantArchitecture
plugin, including:
1. Saving and loading plant structures (XML format)
2. Exporting mesh vertices for external processing
3. Exporting TreeQSM cylinder format for biomechanical analysis
4. Common workflows for plant structure persistence

The file I/O methods enable:
- Saving plant growth states for later analysis
- Exporting plant geometry for external tools
- Creating plant libraries and reusable structures
- Integrating with biomechanical modeling software

All files written by this example go to docs/examples/output/plantarch_file_io/.
"""

from pathlib import Path
from example_output import display_path, get_output_dir
from pyhelios import Context, PlantArchitecture
from pyhelios.types import vec3, vec2, int2

OUTPUT_DIR = get_output_dir("plantarch_file_io")


def example_save_and_load_xml():
    """
    Example 1: Save and load plant structures using XML format

    Demonstrates the basic workflow of saving a plant's complete structure
    to an XML file and loading it back for continued use.
    """
    print("\n=== Example 1: Save and Load Plant Structures ===")

    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            # Load bean model and create plant
            print("Creating bean plant (age 30 days)...")
            plantarch.loadPlantModelFromLibrary("bean")
            plant_id = plantarch.buildPlantInstanceFromLibrary(
                base_position=vec3(0, 0, 0),
                age=30.0
            )

            # Grow the plant
            print("Growing plant for 15 additional days...")
            plantarch.advanceTime(15.0)

            # Get plant statistics before saving
            original_uuids = plantarch.getAllPlantUUIDs(plant_id)
            print(f"Plant has {len(original_uuids)} primitives")

            # Save plant structure to XML
            output_file = OUTPUT_DIR / "bean_day45.xml"
            print(f"Saving plant structure to {display_path(output_file)}...")
            plantarch.writePlantStructureXML(plant_id, str(output_file))
            print(f"✓ Plant saved successfully")

    # Create new context to demonstrate loading
    print("\nLoading saved plant in new context...")
    with Context() as context2:
        with PlantArchitecture(context2) as plantarch2:
            # The plant model must be loaded before reading the XML so that the
            # shoot types referenced by the file are defined in this context.
            plantarch2.loadPlantModelFromLibrary("bean")

            # Load the saved plant
            loaded_plant_ids = plantarch2.readPlantStructureXML(str(output_file))
            print(f"✓ Loaded {len(loaded_plant_ids)} plant(s)")

            # Verify loaded plant
            for loaded_id in loaded_plant_ids:
                loaded_uuids = plantarch2.getAllPlantUUIDs(loaded_id)
                print(f"  Loaded plant {loaded_id} has {len(loaded_uuids)} primitives")

            # NOTE: Calling advanceTime() on a plant restored from XML currently
            # fails in the native library with
            #   "ERROR (Tube::setTubeRadii): Number of radii in input vector must
            #    match number of tube nodes."
            # Growth of a reloaded plant is therefore not demonstrated here.
            # Plants built in-process with buildPlantInstanceFromLibrary() can be
            # grown normally -- see example_grow_and_save() below.


def example_export_mesh_vertices():
    """
    Example 2: Export plant mesh vertices for external processing

    Shows how to export all vertex coordinates from a plant for use in
    external tools such as convex hull analysis, bounding volume computation,
    or custom geometric processing.
    """
    print("\n=== Example 2: Export Mesh Vertices ===")

    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            # Create tomato plant
            print("Creating tomato plant...")
            plantarch.loadPlantModelFromLibrary("tomato")
            plant_id = plantarch.buildPlantInstanceFromLibrary(
                base_position=vec3(0, 0, 0),
                age=25.0
            )

            # Export vertices
            output_file = OUTPUT_DIR / "tomato_vertices.txt"
            print(f"Exporting mesh vertices to {display_path(output_file)}...")
            plantarch.writePlantMeshVertices(plant_id, str(output_file))

            # Read and analyze the exported vertices
            with open(output_file, 'r') as f:
                lines = f.readlines()
                print(f"✓ Exported {len(lines)} vertices")

                # Calculate bounding box from first few vertices
                if len(lines) >= 10:
                    print("Sample vertices (first 5):")
                    for i, line in enumerate(lines[:5]):
                        coords = line.strip().split()
                        print(f"  Vertex {i+1}: x={coords[0]}, y={coords[1]}, z={coords[2]}")

            # These vertices can now be used for:
            # - Computing convex hull
            # - Calculating bounding volumes
            # - Custom geometric analysis
            # - Integration with external modeling tools
            print("\nVertices ready for external processing:")
            print("  - Convex hull calculation")
            print("  - Bounding volume computation")
            print("  - Geometric analysis")


def example_export_qsm_format():
    """
    Example 3: Export TreeQSM cylinder format for biomechanical analysis

    Demonstrates exporting plant structure in TreeQSM format, which is
    widely used for quantitative structure modeling and biomechanical analysis.
    """
    print("\n=== Example 3: Export TreeQSM Cylinder Format ===")

    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            # Create almond tree
            print("Creating almond tree...")
            plantarch.loadPlantModelFromLibrary("almond")
            plant_id = plantarch.buildPlantInstanceFromLibrary(
                base_position=vec3(0, 0, 0),
                age=50.0  # Mature tree
            )

            # Export to TreeQSM format
            output_file = OUTPUT_DIR / "almond_qsm.txt"
            print(f"Exporting to TreeQSM format: {display_path(output_file)}...")
            plantarch.writeQSMCylinderFile(plant_id, str(output_file))

            # Analyze the QSM export
            with open(output_file, 'r') as f:
                lines = f.readlines()
                # The QSM file starts with a column-header line, so the cylinder
                # count is one less than the line count.
                cylinder_lines = lines[1:]
                print(f"✓ Exported {len(cylinder_lines)} cylinders")

                # Parse first cylinder to show data structure
                if len(cylinder_lines) > 0:
                    print("\nTreeQSM format includes:")
                    print("  - Cylinder dimensions (radius, length)")
                    print("  - Spatial position and orientation")
                    print("  - Branch topology (parent, extension, branch IDs)")
                    print("  - Branch hierarchy (order, position)")
                    print("  - Quality metrics (distance, coverage)")

                    print(f"\nFirst cylinder data:")
                    first_line = lines[0].strip()
                    print(f"  {first_line}")

            print("\nQSM file ready for biomechanical analysis tools")
            print("Reference: Raumonen et al. (2013) Remote Sensing 5(2):491-520")


def example_plant_library_workflow():
    """
    Example 4: Create a plant library with growth stages

    Shows how to build a library of plants at different growth stages
    for reuse in simulations, analysis, or visualization.
    """
    print("\n=== Example 4: Plant Library Workflow ===")

    # Create output directory
    library_dir = OUTPUT_DIR / "plant_library"
    library_dir.mkdir(exist_ok=True)
    print(f"Creating plant library in {display_path(library_dir)}/")

    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            # Load soybean model
            print("\nCreating soybean plants at different growth stages...")
            plantarch.loadPlantModelFromLibrary("soybean")

            # Save plants at multiple growth stages
            growth_stages = [10, 20, 30, 40, 50]  # Days

            for age in growth_stages:
                # Create plant at this age
                plant_id = plantarch.buildPlantInstanceFromLibrary(
                    base_position=vec3(0, 0, 0),
                    age=float(age)
                )

                # Save to library
                filename = library_dir / f"soybean_day{age}.xml"
                plantarch.writePlantStructureXML(plant_id, str(filename))

                # Get plant statistics
                uuids = plantarch.getAllPlantUUIDs(plant_id)
                print(f"  Day {age}: {len(uuids)} primitives -> {filename.name}")

                # Delete plant to prepare for next
                # (In PyHelios, we'd recreate the context or use deletePlant if available)

    print(f"\n✓ Created library with {len(growth_stages)} growth stages")
    print(f"Library location: {display_path(library_dir)}")

    # Demonstrate loading from library
    print("\nLoading day 30 plant from library...")
    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            # The plant model must be loaded before reading the XML so that the
            # shoot types referenced by the file are defined in this context.
            plantarch.loadPlantModelFromLibrary("soybean")

            library_file = library_dir / "soybean_day30.xml"
            loaded_ids = plantarch.readPlantStructureXML(str(library_file))
            print(f"✓ Loaded plant {loaded_ids[0]} from library")

            # NOTE: advanceTime() on a plant restored from XML currently fails in
            # the native library (Tube::setTubeRadii node/radii mismatch), so
            # growth from the library state is not demonstrated here.
            loaded_uuids = plantarch.getAllPlantUUIDs(loaded_ids[0])
            print(f"Loaded plant has {len(loaded_uuids)} primitives")


def example_multi_plant_canopy_persistence():
    """
    Example 5: Save and load complete canopies

    Demonstrates saving and loading entire plant canopies for complex
    scene persistence and analysis workflows.
    """
    print("\n=== Example 5: Multi-Plant Canopy Persistence ===")

    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            # Create a canopy of bean plants
            print("Creating 3x3 bean canopy...")
            plantarch.loadPlantModelFromLibrary("bean")

            plant_ids = plantarch.buildPlantCanopyFromLibrary(
                canopy_center=vec3(0, 0, 0),
                plant_spacing=vec2(0.5, 0.5),
                plant_count=int2(3, 3),
                age=25.0
            )

            print(f"Created {len(plant_ids)} plants")

            # Grow canopy
            print("Growing canopy for 15 days...")
            plantarch.advanceTime(15.0)

            # Save each plant in the canopy
            canopy_dir = OUTPUT_DIR / "bean_canopy"
            canopy_dir.mkdir(exist_ok=True)

            print(f"Saving canopy to {display_path(canopy_dir)}/...")
            for i, plant_id in enumerate(plant_ids):
                filename = canopy_dir / f"plant_{i}.xml"
                plantarch.writePlantStructureXML(plant_id, str(filename))

            print(f"✓ Saved {len(plant_ids)} plants")

            # Save canopy metadata
            metadata_file = canopy_dir / "canopy_info.txt"
            with open(metadata_file, 'w') as f:
                f.write(f"Canopy: 3x3 bean plants\n")
                f.write(f"Spacing: 0.5m x 0.5m\n")
                f.write(f"Age: 40 days\n")
                f.write(f"Plants: {len(plant_ids)}\n")

            print(f"✓ Saved metadata to {metadata_file.name}")

    # Load and analyze the saved canopy
    print("\nLoading saved canopy...")
    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            # The plant model must be loaded before reading the XML so that the
            # shoot types referenced by the files are defined in this context.
            plantarch.loadPlantModelFromLibrary("bean")

            loaded_plants = []

            for i in range(9):  # 3x3 = 9 plants
                filename = canopy_dir / f"plant_{i}.xml"
                plant_ids = plantarch.readPlantStructureXML(str(filename), quiet=True)
                loaded_plants.extend(plant_ids)

            print(f"✓ Loaded {len(loaded_plants)} plants from canopy")

            # Analyze loaded canopy
            total_primitives = 0
            for plant_id in loaded_plants:
                uuids = plantarch.getAllPlantUUIDs(plant_id)
                total_primitives += len(uuids)

            print(f"Total canopy primitives: {total_primitives}")
            print(f"Average per plant: {total_primitives / len(loaded_plants):.0f}")


def example_path_handling():
    """
    Example 6: Flexible path handling

    Shows that file I/O methods work with both string paths and pathlib.Path
    objects, and handle relative/absolute paths correctly.
    """
    print("\n=== Example 6: Flexible Path Handling ===")

    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            # Create a test plant
            plantarch.loadPlantModelFromLibrary("bean")
            plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), age=20.0)

            # Test with pathlib.Path
            output_dir = OUTPUT_DIR / "path_handling"
            output_dir.mkdir(exist_ok=True)

            print("Testing pathlib.Path objects...")
            xml_path = output_dir / "test_plant.xml"
            plantarch.writePlantStructureXML(plant_id, xml_path)
            print(f"✓ Saved to Path object: {display_path(xml_path)}")

            vertices_path = output_dir / "test_vertices.txt"
            plantarch.writePlantMeshVertices(plant_id, vertices_path)
            print(f"✓ Saved to Path object: {display_path(vertices_path)}")

            # Test with a plain string path
            print("\nTesting string paths...")
            qsm_path = str(output_dir / "test_qsm.txt")
            plantarch.writeQSMCylinderFile(plant_id, qsm_path)
            print(f"✓ Saved to string path: {display_path(qsm_path)}")

            # Load using Path object
            loaded_ids = plantarch.readPlantStructureXML(xml_path)
            print(f"✓ Loaded from Path object: {len(loaded_ids)} plant(s)")

            print("\nPath handling features:")
            print("  ✓ Works with pathlib.Path objects")
            print("  ✓ Works with string paths")
            print("  ✓ Relative paths resolve against the working directory")


if __name__ == "__main__":
    print("=" * 70)
    print("PlantArchitecture File I/O Examples")
    print("=" * 70)

    # Run all examples
    example_save_and_load_xml()
    example_export_mesh_vertices()
    example_export_qsm_format()
    example_plant_library_workflow()
    example_multi_plant_canopy_persistence()
    example_path_handling()

    print("\n" + "=" * 70)
    print("All examples completed successfully!")
    print(f"Output written to: {display_path(OUTPUT_DIR)}")
    print("=" * 70)

    print("\nKey Takeaways:")
    print("1. XML format preserves complete plant structure for reloading")
    print("2. Mesh vertices enable integration with external analysis tools")
    print("3. TreeQSM format supports biomechanical modeling workflows")
    print("4. Plant libraries enable efficient reuse of growth stages")
    print("5. File I/O works seamlessly with pathlib and string paths")
    print("\nFor more information, see the PlantArchitecture documentation.")
