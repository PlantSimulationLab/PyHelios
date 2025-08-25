#!/usr/bin/env python3
"""
Stanford Bunny Energy Balance Example

This example demonstrates PyHelios energy balance modeling capabilities by replicating
the Stanford Bunny energy balance sample from the Helios C++ samples. It loads the Stanford
Bunny PLY file, sets up both radiation and energy balance models to compute surface
temperatures, and visualizes the temperature distribution using the native PyHelios visualizer.

HARDWARE REQUIREMENTS:
- NVIDIA GPU with CUDA compute capability (for radiation simulation and energy balance)
- CUDA Toolkit installed and configured
- OptiX ray tracing SDK installed (for radiation)
- OpenGL-compatible graphics system (for visualization)

SOFTWARE REQUIREMENTS:
- PyHelios with radiation, energybalance, and visualizer plugins enabled in native library
- Stanford Bunny PLY file (included in helios-core)

NOTE: This example demonstrates the full PyHelios workflow including native 3D visualization.
Both radiation and energy balance plugins require GPU acceleration for full functionality.

This is the PyHelios equivalent of helios-core/samples/energybalance_StanfordBunny/main.cpp
"""

import sys
import os
import numpy as np

# Add pyhelios to path if needed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pyhelios import Context, RadiationModel, EnergyBalanceModel, Visualizer
from pyhelios.types import *


def main():
    
    # Initialize context
    with Context() as context:
        
        # Load Stanford Bunny PLY file  
        ply_path = os.path.join(os.path.dirname(__file__), '..', '..', 'helios-core', 'PLY', 'StanfordBunny.ply')

        # Load bunny with scaling factor of 4 (matching C++ sample)
        bunny_uuids = context.loadPLY(ply_path, origin=vec3(0, 0, 0), height=4.0, upaxis="YUP")
            
        print(f"Loaded Stanford Bunny with {len(bunny_uuids)} triangles")
        
        # Create ground geometry (matching C++ sample exactly)
        D = 10  # Ground size
        size = int2(5, 5)  # Number of ground segments
        subsize = int2(50, 50)  # Subdivisions per segment
        dx = vec2(D / (size.x * subsize.x), D / (size.y * subsize.y))
        
        ground_uuids = []
        for j in range(size.y):
            for i in range(size.x):
                
                # Rotation pattern from C++ sample
                rot = ((j * size.x + i) % 3) * np.pi * 0.5
                
                for jj in range(subsize.y):
                    for ii in range(subsize.x):
                        center = vec3(
                            -0.5 * D + (i * subsize.x + ii) * dx.x, 
                            -0.5 * D + (j * subsize.y + jj) * dx.y, 
                            0
                        )
                        
                        if (j * size.x + i) % 2 == 0:
                            # Silver patches with low reflectivity
                            color = RGBcolor(0.75, 0.75, 0.75)  # RGB::silver equivalent
                            patch_uuid = context.addPatch(center=center, size=dx, color=color)
                            context.setPrimitiveDataFloat(patch_uuid, "reflectivity_SW", 0.0)
                        else:
                            # White patches with higher reflectivity  
                            color = RGBcolor(1.0, 1.0, 1.0)  # RGB::white equivalent
                            patch_uuid = context.addPatch(center=center, size=dx, color=color)
                            context.setPrimitiveDataFloat(patch_uuid, "reflectivity_SW", 0.6)

                        ground_uuids.append(patch_uuid)
        
        print(f"Added {len(ground_uuids)} ground patches")

        # Set up radiation model (matching C++ sample)
        sun_direction = vec3(0.4, -0.4, 0.6)
        
        with RadiationModel(context) as radiation_model:
            
            # Add collimated radiation source
            sun_source = radiation_model.addCollimatedRadiationSource(sun_direction)
            
            # Configure shortwave radiation band
            radiation_model.addRadiationBand("SW")
            radiation_model.disableEmission("SW")
            radiation_model.setDirectRayCount("SW", 100)
            radiation_model.setDiffuseRayCount("SW", 1000)
            radiation_model.setSourceFlux(sun_source, "SW", 600.0)
            radiation_model.setDiffuseRadiationFlux("SW", 100.0)
            radiation_model.setScatteringDepth("SW", 3)
            
            # Configure longwave radiation band
            radiation_model.addRadiationBand("LW")
            radiation_model.setDiffuseRayCount("LW", 1000)
            # LW flux: σT⁴ where σ = 5.67e-8, T = 300K
            lw_flux = 5.67e-8 * pow(300, 4)
            radiation_model.setDiffuseRadiationFlux("LW", lw_flux)
            
            # Update geometry and run radiation simulation
            radiation_model.updateGeometry()
            
            print("Running shortwave radiation simulation...")
            radiation_model.runBand("SW")
            
            print("Running longwave radiation simulation...")
            radiation_model.runBand("LW")

        # Set up energy balance model (matching C++ sample)
        with EnergyBalanceModel(context) as energy_balance:
            
            # Add radiation bands for energy balance calculations
            energy_balance.addRadiationBand("SW")
            energy_balance.addRadiationBand("LW")
            
            print("Running energy balance simulation...")
            # Run steady-state energy balance
            energy_balance.run()
            
            print("Energy balance simulation completed!")

        # Visualize temperature results using native PyHelios visualizer
        with Visualizer(width=1200, height=768) as visualizer:

            # Set background color for better contrast
            bg_color = RGBcolor(0.2, 0.2, 0.3)
            visualizer.setBackgroundColor(bg_color)

            # Disable lighting to show pure color mapping (matching C++ sample)
            visualizer.setLightingModel(visualizer.LIGHTING_NONE)
            
            # Set camera position
            camera_position = vec3(2.0, -10, 4.0)
            lookat_point = vec3(0, 0, 1.5)
            visualizer.setCameraPosition(camera_position, lookat_point)
            
            # Load geometry from context into visualizer
            visualizer.buildContextGeometry(context)
            
            # Color primitives by temperature data
            visualizer.colorContextPrimitivesByData("temperature")
            
            # Enable and configure colorbar
            #visualizer.setColorbarRange(300.0, 320.0)  # Temperature range in Kelvin
            #visualizer.setColorbarTitle("Temperature (K)")
            
            print("Launching interactive visualization...")
            print("Close the visualization window to exit.")
            
            # Start the visualization loop - this will open a window and run until user exits
            visualizer.plotInteractive()  # Blocking call - runs until user closes window
    
    print("Stanford Bunny energy balance example completed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())