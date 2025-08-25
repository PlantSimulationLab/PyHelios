#!/usr/bin/env python3
"""
PyHelios Visualizer Demo

This example demonstrates the core functionality of the PyHelios Visualizer
plugin for 3D visualization of plant models and simulation results.

The example shows:
1. Basic Context and geometry creation
2. Tree generation using WeberPennTree
3. Interactive 3D visualization
4. Camera and lighting control
5. Image export capabilities

Requirements:
- PyHelios built with visualizer plugin
- OpenGL-capable graphics system
"""

import sys
import os

# Add PyHelios to path if running from examples directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from pyhelios import Context, Visualizer, WeberPennTree, WPTType
    from pyhelios.types import *
    if hasattr(Visualizer, 'VisualizerError'):
        from pyhelios.Visualizer import VisualizerError
    else:
        VisualizerError = Exception
except ImportError as e:
    print(f"Error importing PyHelios: {e}")
    print("Make sure PyHelios is installed and built with visualizer plugin.")
    sys.exit(1)

def create_sample_tree(context):
    """Create a sample tree using WeberPennTree."""
    print("Creating sample tree...")
    
    try:
        with WeberPennTree(context) as wpt:
            # Set tree parameters for a nice-looking tree
            wpt.setBranchRecursionLevel(3)
            wpt.setTrunkSegmentResolution(12)
            wpt.setBranchSegmentResolution(8)
            wpt.setLeafSubdivisions(4, 4)
            
            # Build a lemon tree at a specific location
            tree_origin = vec3(0, 0, 0)
            tree_id = wpt.buildTree(WPTType.LEMON, origin=tree_origin)
            
            # Get tree UUIDs for potential future use
            trunk_uuids = wpt.getTrunkUUIDs(tree_id)
            branch_uuids = wpt.getBranchUUIDs(tree_id) 
            leaf_uuids = wpt.getLeafUUIDs(tree_id)
            
            print(f"Created tree with {len(trunk_uuids)} trunk, {len(branch_uuids)} branch, and {len(leaf_uuids)} leaf primitives")
            return tree_id, trunk_uuids + branch_uuids + leaf_uuids
            
    except Exception as e:
        print(f"Note: Tree creation failed (WeberPennTree plugin may not be available): {e}")
        return None, []


def demonstrate_basic_visualization():
    """Demonstrate basic visualization functionality."""
    print("\n=== Basic Visualization Demo ===")
    
    try:
        with Context() as context:
            # Create geometry
            patch_uuids = context.addPatch( center=make_vec3(0, 0, 0), size=make_vec2(10, 10) )
            tree_id, tree_uuids = create_sample_tree(context)
            
            # Create visualizer (smaller window for demo)
            with Visualizer(800, 600, headless=False) as visualizer:
                # Load all geometry into visualizer
                visualizer.buildContextGeometry(context)
                
                # Configure scene
                bg_color = RGBcolor(0.1, 0.1, 0.15)  # Dark blue background
                visualizer.setBackgroundColor(bg_color)
                light_dir = vec3(1, 1, 1)  # Directional lighting
                visualizer.setLightDirection(light_dir)
                visualizer.setLightingModel("phong_shadowed")    # Nice lighting with shadows
                
                # Set a good camera position to view the scene
                camera_pos = vec3(8, 8, 6)    # Camera position
                look_at = vec3(1.5, 1.5, 0.5) # Look at center of geometry
                visualizer.setCameraPosition(camera_pos, look_at)
                
                print("Opening interactive visualization window...")
                print("Controls:")
                print("  - Mouse scroll: Zoom in/out")
                print("  - Left mouse + drag: Rotate camera")
                print("  - Right mouse + drag: Pan camera")
                print("  - Arrow keys: Camera movement")
                print("  - Close window to continue")
                
                # Show interactive visualization
                visualizer.plotInteractive()
                
    except VisualizerError as e:
        print(f"Visualization error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    
    return True

def demonstrate_lighting_comparison():
    """Demonstrate different lighting models."""
    print("\n=== Lighting Model Comparison ===")
    
    try:
        with Context() as context:
            # Create a simple scene for lighting comparison
            center = vec3(0, 0, 0)
            size = vec2(2, 2)
            color = RGBcolor(0.7, 0.5, 0.3)
            context.addPatch(center=center, size=size, color=color)
            
            # Add a second patch at an angle for better lighting visualization
            center2 = vec3(1, 0, 1)
            rotation = SphericalCoord(1.0, 0.5, 0.3)  # Some rotation (radius, elevation, azimuth)
            context.addPatch(center=center2, size=size, rotation=rotation, color=color)
            
            with Visualizer(600, 400, headless=True) as visualizer:
                visualizer.buildContextGeometry(context)
                bg_color = RGBcolor(0.1, 0.1, 0.1)
                visualizer.setBackgroundColor(bg_color)
                light_dir = vec3(1, 1, -0.5)
                visualizer.setLightDirection(light_dir)
                
                # Camera position for good lighting view
                camera_pos = vec3(3, 3, 2)
                look_at = vec3(0.5, 0, 0.5)
                visualizer.setCameraPosition(camera_pos, look_at)
                
                # Test different lighting models
                lighting_modes = [
                    (Visualizer.LIGHTING_NONE, "lighting_none.jpg"),
                    (Visualizer.LIGHTING_PHONG, "lighting_phong.jpg"),
                    (Visualizer.LIGHTING_PHONG_SHADOWED, "lighting_shadowed.jpg"),
                ]
                
                print("Comparing lighting models...")
                for mode, filename in lighting_modes:
                    visualizer.setLightingModel(mode)
                    visualizer.plotUpdate()
                    
                    output_path = os.path.join(os.path.dirname(__file__), filename)
                    visualizer.printWindow(output_path)
                    
                    mode_names = {0: "None", 1: "Phong", 2: "Phong with Shadows"}
                    print(f"  Saved {mode_names[mode]}: {filename}")
                
    except VisualizerError as e:
        print(f"Lighting comparison error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    
    return True


def main():
    """Run the PyHelios Visualizer demo."""
    print("PyHelios Visualizer Demo")
    print("========================")
    
    # Check if we can create a visualizer
    try:
        # Quick test with small headless visualizer
        test_viz = Visualizer(100, 100, headless=True)
        test_viz.__exit__(None, None, None)  # Clean up
        print("✓ Visualizer plugin is available")
    except VisualizerError as e:
        print("✗ Visualizer plugin is not available")
        print(f"Error: {e}")
        print("\nTo enable visualization, build PyHelios with:")
        print("  build_scripts/build_helios --plugins visualizer")
        return 1
    
    success_count = 0
    total_demos = 3
    
    # Run demonstrations
    if demonstrate_basic_visualization():
        success_count += 1
        
    # if demonstrate_lighting_comparison():
    #     success_count += 1
    
    print(f"\n=== Demo Summary ===")
    print(f"Completed {success_count}/{total_demos} demonstrations successfully")
    
    if success_count == total_demos:
        print("✓ All demonstrations completed successfully!")
        print("\nGenerated image files:")
        image_files = [
            "view_perspective.jpg", "view_side.jpg", "view_front.jpg", "view_top.jpg",
            "lighting_none.jpg", "lighting_phong.jpg", "lighting_shadowed.jpg"
        ]
        for img in image_files:
            img_path = os.path.join(os.path.dirname(__file__), img)
            if os.path.exists(img_path):
                print(f"  - {img}")
        
        return 0
    else:
        print("⚠ Some demonstrations failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())