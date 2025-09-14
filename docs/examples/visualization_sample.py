#!/usr/bin/env python3
"""
PyHelios Visualization Sample

This example demonstrates basic visualization capabilities using the PyHelios
native visualizer plugin. 

Requirements:
- PyHelios built with visualizer plugin
- OpenGL-capable graphics system
"""

import sys
import os

# Add PyHelios to path if running from examples directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from pyhelios import Context, Visualizer
    from pyhelios.types import *
    from pyhelios.Visualizer import VisualizerError
except ImportError as e:
    print(f"Error importing PyHelios: {e}")
    print("Make sure PyHelios is installed and built with visualizer plugin.")
    sys.exit(1)


def main():
    """Simple visualization example."""
    print("PyHelios Visualization Sample")
    print("============================")
    
    try:
        # Create a context with some geometry
        with Context() as context:
            # Add a few patches with different colors
            colors = [
                RGBcolor(1.0, 0.2, 0.2),  # Red
                RGBcolor(0.2, 1.0, 0.2),  # Green
                RGBcolor(0.2, 0.2, 1.0),  # Blue
                RGBcolor(1.0, 1.0, 0.2),  # Yellow
            ]

            positions = [
                vec3(0, 0, 0),
                vec3(2, 0, 0),
                vec3(0, 2, 0),
                vec3(1, 1, 1),
            ]
            
            print("Creating sample geometry...")
            for i, (pos, color) in enumerate(zip(positions, colors)):
                size = vec2(0.8, 0.8)
                uuid = context.addPatch(center=pos, size=size, color=color)
                print(f"  Created patch {i+1} at ({pos.x}, {pos.y}, {pos.z}) with color ({color.r}, {color.g}, {color.b})")
            
            # Create visualizer and display
            print("\nOpening visualization...")
            with Visualizer(800, 600) as visualizer:
                # Load geometry and configure scene
                visualizer.buildContextGeometry(context)
                bg_color = RGBcolor(0.1, 0.1, 0.15)
                visualizer.setBackgroundColor(bg_color)
                light_dir = vec3(1, 1, -1)
                visualizer.setLightDirection(light_dir)
                visualizer.setLightingModel("phong")
                
                # Set camera to get a good view
                camera_pos = vec3(4, 4, 3)
                look_at = vec3(1, 1, 0.5)
                visualizer.setCameraPosition(camera_pos, look_at)
                
                print("Interactive visualization opened.")
                print("Use mouse and keyboard to navigate:")
                print("  - Mouse scroll: Zoom")
                print("  - Left drag: Rotate")
                print("  - Right drag: Pan")
                print("  - Close window to exit")
                
                # Show interactive visualization
                visualizer.plotInteractive()
                
        print("\nVisualization complete!")
        
    except VisualizerError as e:
        print(f"Visualization error: {e}")
        print("\nTo enable visualization, build PyHelios with:")
        print("  build_scripts/build_helios --plugins visualizer")
        return 1
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
