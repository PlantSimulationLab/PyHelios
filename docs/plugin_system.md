# Plugins {#PluginSystem}

Plug-ins build on the Helios core engine and operate on the geometry and data held in the Context. Links to the documentation for each plug-in currently wrapped in PyHelios are given below. Each plug-in documentation page lists its dependencies, the PyHelios import, the main class, and usage examples.

## Available Plug-ins

- \ref BoundaryLayerConductanceDoc "Boundary-Layer Conductance: boundary-layer conductance model calculations based on several possible models."
- \ref EnergyBalanceDoc "Energy Balance Model: surface energy balance solution."
- \ref LeafOpticsDoc "Leaf Optics: implementation of the PROSPECT leaf optical model of leaf reflectance and transmittance spectra."
- \ref LiDARDoc "Terrestrial LiDAR: processing terrestrial LiDAR point-cloud data into leaf area, leaf angle distributions, and reconstructed plant geometry."
- \ref PhotosynthesisDoc "Photosynthesis Model: photosynthetic assimilation model."
- \ref PlantArchitectureDoc "Plant Architecture: flexible procedural plant generation with dynamic growth and phenology."
- \ref RadiationDoc "Radiation Model: GPU-accelerated ray-tracing radiation transport model (all platforms via Vulkan; NVIDIA systems via OptiX)."
- \ref SolarPositionDoc "Solar Position: model for the position of the sun in the sky, as well as solar radiation flux and longwave flux from the sky."
- \ref StomatalConductanceDoc "Stomatal Conductance Model: model for the conductance of water vapor through stomatal pores."
- \ref VisualizerDoc "Visualizer: OpenGL-based visualization of model geometry and data."
- \ref WeberPennTreeDoc "Weber-Penn Tree: procedural tree architecture generation."

Additional Helios plug-ins (e.g. Aerial LiDAR, Canopy Generator, Parameter Optimization, Plant Hydraulics, Project Builder) are available in the native C++ library but do not yet have dedicated PyHelios documentation pages. See the [native Helios documentation](https://baileylab.ucdavis.edu/software/helios) for those.

For details on how PyHelios builds, selects, and detects plug-ins at runtime, see \ref PluginBuildSystem "Building and Selecting Plug-ins".
