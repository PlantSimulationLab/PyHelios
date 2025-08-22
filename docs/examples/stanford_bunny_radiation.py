#!/usr/bin/env python3
"""
Stanford Bunny Radiation Model Example

This example demonstrates PyHelios radiation modeling capabilities by replicating
the Stanford Bunny sample from the Helios C++ samples. It loads the Stanford Bunny
PLY file, sets up a radiation model with shortwave radiation, and visualizes the
radiation flux distribution using the native PyHelios visualizer plugin.

HARDWARE REQUIREMENTS:
- NVIDIA GPU with CUDA compute capability (for radiation simulation)
- CUDA Toolkit installed and configured
- OptiX ray tracing SDK installed
- OpenGL-compatible graphics system (for visualization)

SOFTWARE REQUIREMENTS:
- PyHelios with radiation and visualizer plugins enabled in native library
- Stanford Bunny PLY file (included in helios-core)

NOTE: This example demonstrates the full PyHelios workflow including native 3D visualization.
The radiation plugin requires GPU ray tracing hardware for full functionality.

This is the PyHelios equivalent of helios-core/samples/radiation_StanfordBunny/main.cpp
"""

import sys
import os
import numpy as np

# Add pyhelios to path if needed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pyhelios import Context, RadiationModel, Visualizer
from pyhelios.types import *


def main():
    
    # Initialize context
    with Context() as context:
        
        # Load Stanford Bunny PLY file  
        ply_path = os.path.join(os.path.dirname(__file__), '..', '..', 'helios-core', 'PLY', 'StanfordBunny.ply')

        # Load bunny with scaling factor of 4
        bunny_uuids = context.loadPLY(ply_path, origin=vec3(0, 0, 0), height=4.0, upaxis="YUP")
            
        print(f"Loaded Stanford Bunny with {len(bunny_uuids)} triangles")
        
        # Ground parameters (matching C++ sample)
        D = 10  # Ground size
        size = int2(5, 5)  # Number of ground segments
        subsize = int2(50, 50)  # Subdivisions per segment
        dx = vec2(D / (size.x * subsize.x), D / (size.y * subsize.y))
        
        ground_uuids = []
        for j in range(size.y):
            for i in range(size.x):
                
                for jj in range(subsize.y):
                    for ii in range(subsize.x):
                        center = vec3(-0.5 * D + (i * subsize.x + ii) * dx.x, -0.5 * D + (j * subsize.y + jj) * dx.y,0 )
                        
                        if (j * size.x + i) % 2 == 0:
                            # Silver patches with low reflectivity
                            color = RGBcolor(0.75, 0.75, 0.75)
                            patch_uuid = context.addPatch(center=center, size=dx, color=color)
                            context.setPrimitiveData(patch_uuid, "reflectivity_SW", 0.0)
                        else:
                            # White patches with higher reflectivity  
                            color = RGBcolor(1.0, 1.0, 1.0)
                            patch_uuid = context.addPatch(center=center, size=dx, color=color)
                            context.setPrimitiveData(patch_uuid, "reflectivity_SW", 0.6)

                        ground_uuids.append(patch_uuid)
        
        print(f"Added {len(ground_uuids)} ground patches")

        # Initialize radiation model

        with RadiationModel(context) as radiation_model:
            
            # Add shortwave radiation band
            radiation_model.addRadiationBand("SW")
            
            radiation_model.disableEmission("SW")
            radiation_model.setDirectRayCount("SW", 100)
            radiation_model.setDiffuseRayCount("SW", 300)

            sun_direction = vec3(0.4, -0.4, 0.6)
            sun_source = radiation_model.addCollimatedRadiationSource(sun_direction)

            radiation_model.setSourceFlux(sun_source, "SW", 800.0)
            radiation_model.setDiffuseRadiationFlux("SW", 200.0)
            radiation_model.setScatteringDepth("SW", 3)
            
            # Update geometry and run simulation
            radiation_model.updateGeometry()

            radiation_model.runBand("SW")

        # Apply Helios pseudocolor mapping to all primitives
        all_uuids = context.getAllUUIDs()
        context.colorPrimitiveByDataPseudocolor(
            uuids=all_uuids,
            primitive_data="radiation_flux_SW", 
            colormap="hot", 
            ncolors=256
        )
        
        # Visualize results using native PyHelios visualizer

        with Visualizer(width=1024, height=768) as visualizer:

            # Load geometry from context into visualizer
            visualizer.buildContextGeometry(context)

            # Position camera for Stanford Bunny view (bunny is ~4 units tall)
            camera_position = [6.0, -6.0, 4.0]  # Elevated view
            lookat_point = [0.0, 0.0, 1.5]  # Look at bunny center

            visualizer.setCameraPosition(camera_position, lookat_point)

            # Set background color to black for better contrast
            visualizer.setBackgroundColor([0.0, 0.0, 0.0])

            # Start the visualization loop - this will open a window and run until user exits
            visualizer.plotInteractive()  # Blocking call - runs until user closes window
    
    print("Stanford Bunny radiation example completed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())