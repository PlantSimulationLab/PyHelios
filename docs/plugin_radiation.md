# Radiation Model Plugin {#RadiationDoc}

The Radiation Model plugin provides GPU-accelerated ray tracing for radiation simulation using Vulkan or OptiX backends. Backend selection is automatic based on available hardware: Vulkan supports all GPU vendors (NVIDIA, AMD, Intel, Apple Silicon), while OptiX provides an optimized path for NVIDIA GPUs.

## Overview

The \ref pyhelios.RadiationModel.RadiationModel "RadiationModel class" provides advanced radiation modeling and ray tracing capabilities for realistic light interaction simulations in plant canopies and scenes.

## Requirements

The radiation plugin supports two GPU backends. At least one must be available:

### Vulkan Backend (All Platforms)

Supports NVIDIA, AMD, Intel, and Apple Silicon GPUs via Vulkan compute shaders with software BVH traversal. Vulkan headers and the glslang shader compiler are bundled with Helios, so no external Vulkan SDK installation is required on Windows.

| Requirement | macOS | Linux | Windows |
|-------------|-------|-------|---------|
| **GPU** | Any with Vulkan support | Any with Vulkan support | Any with Vulkan support |
| **Dependencies** | `brew install vulkan-loader molten-vk` | `sudo apt-get install libvulkan-dev` | None (all bundled) |

### OptiX Backend (NVIDIA Only)

Provides optimized ray tracing on NVIDIA GPUs using hardware RT cores. Two OptiX versions are supported:

| Backend | Driver Requirement | CUDA | Notes |
|---------|-------------------|------|-------|
| **OptiX 8.1** | NVIDIA driver >= 560 | CUDA 12.0+ | Default for modern drivers |
| **OptiX 6.5** | NVIDIA driver < 560 | CUDA 9.0+ | Legacy driver support |

### Backend Selection

Backend selection is **automatic at runtime** via GPU hardware probing. When the radiation model starts, it probes compiled-in backends in priority order (OptiX 8 -> OptiX 6 -> Vulkan) and selects the first one that is compatible with the current hardware. If no compatible GPU is found, a clear diagnostic error is raised.

You can query the active backend at runtime:

```python
with RadiationModel(context) as radiation:
    print(f"Active backend: {radiation.getBackendName()}")
    # e.g., "OptiX 8.1", "OptiX 6.5", "Vulkan Compute"
```

You can also probe GPU availability without creating a full radiation model:

```python
if RadiationModel.probeAnyGPUBackend():
    print("GPU backend available")
else:
    print("No compatible GPU backend found")
```

**Running in Docker?** See \ref DockerGPU "Running PyHelios in Docker with GPU Support". Containers need `NVIDIA_DRIVER_CAPABILITIES` to include `graphics` before the OptiX backend is available; without it the model silently falls back to Vulkan.

**For CUDA/OptiX setup**, see the comprehensive \ref CUDASetup "CUDA Setup Guide", which covers:
- Choosing the correct CUDA toolkit version: \ref ChoosingCUDA
- Platform-specific installation steps (Windows, Linux)
- GPU timeout settings for Windows: \ref PCGPUTimeout
- OptiX requirements: \ref OptiXSetup
- Troubleshooting common issues

## Basic Usage

```python
from pyhelios import Context, RadiationModel
from pyhelios.types import *

# Create context with geometry
context = Context()
patch_uuid = context.addPatch(
    center=vec3(0, 0, 0),
    size=vec2(2, 2),
    color=RGBcolor(0.3, 0.7, 0.2)
)

# Use RadiationModel with context manager (recommended)
with RadiationModel(context) as radiation:
    # Add radiation band
    radiation.addRadiationBand("PAR")
    
    # Add radiation source
    source_id = radiation.addCollimatedRadiationSource()
    radiation.setSourceFlux(source_id, "PAR", 1000.0)
    
    # Configure ray counts
    radiation.setDirectRayCount("PAR", 100)
    radiation.setDiffuseRayCount("PAR", 300)
    
    # Run simulation. runBand() pushes Context geometry into the radiation model
    # itself, and rebuilds it if primitives were added or deleted since the last
    # build, so an explicit updateGeometry() call is not needed here.
    radiation.runBand("PAR")
    
    # Get results. Values are flux DENSITY in W/m^2, one per primitive, and
    # element i belongs to uuids[i].
    uuids = context.getAllUUIDs()
    results = radiation.getAbsorbedFlux("PAR")
    print(f"Absorbed flux density: {results[0]:.2f} W/m^2")
    
    # To get absorbed POWER in W, weight each primitive by its area.
    # Do NOT use results.sum() - summing W/m^2 across primitives is not meaningful.
    # Both calls return arrays, so this is one vectorized multiply.
    power = float((results * context.getPrimitiveArea(uuids)).sum(dtype="float64"))
    print(f"Total absorbed power: {power:.2f} W")
```

> **Units:** `getAbsorbedFlux()` returns absorbed flux **density** in W/m² for each
> primitive (the `radiation_flux_<band>` primitive data) — not power in watts.
> Because it is a density, it does **not** change when you change a primitive's
> size: a 1×1 m and a 2×2 m patch under the same collimated source both report
> 1000 W/m². Multiply by `context.getPrimitiveArea(uuid)` to convert to watts
> before summing across primitives.

> ⚠️ **Use `getAbsorbedFlux(band)`, not `getTotalAbsorbedFlux()`, for per-primitive
> results.** `getTotalAbsorbedFlux()` has two traps:
>
> 1. **Its ordering is not `context.getAllUUIDs()`.** The values are ordered by the
>    radiation model's internal primitive ordering. Pairing the two by index silently assigns each
>    primitive's flux to a different primitive.
> 2. **It sums over every band.** With PAR, NIR and SW registered, the result is
>    PAR + NIR + SW per primitive, which double-counts because SW already spans the
>    other two.
>
> `getAbsorbedFlux(band)` is keyed by UUID and returns one band, so neither applies.

## Radiation Bands

### Basic Band Management

```python
# Add radiation bands
radiation.addRadiationBand("PAR")
radiation.addRadiationBand("NIR")
radiation.addRadiationBand("SW")

# Add band with wavelength bounds
radiation.addRadiationBand("custom", wavelength_min=400.0, wavelength_max=700.0)

# Copy existing band
radiation.copyRadiationBand("PAR", "PAR_copy")
```

Wavelength bounds are in nanometers. The lower bound must not be negative (a band may start at 0 nm) and the upper bound must exceed it by at least 1 nm. Bounds change how a band is treated:

- Surface `reflectivity_spectrum` and `transmissivity_spectrum` primitive data set a primitive's band reflectivity and transmissivity only in a band that has bounds (see [Spectral Surface Properties](#RadSpectralSurfaceProperties)).
- An emission-enabled band with bounds emits only the in-band part of the Planck spectrum (see [Emission Control](#RadEmissionControl)).

### Common Radiation Bands

```python
# Standard radiation bands for plant modeling
bands = {
    "PAR": "Photosynthetically Active Radiation (400-700 nm)",
    "NIR": "Near Infrared (700-1100 nm)", 
    "SW": "Shortwave (300-3000 nm)",
    "UV": "Ultraviolet (280-400 nm)",
    "VIS": "Visible (380-750 nm)"
}

for band, description in bands.items():
    radiation.addRadiationBand(band)
    print(f"Added {band}: {description}")
```

## Radiation Sources

### Collimated Sources

```python
# Default collimated source
source_id = radiation.addCollimatedRadiationSource()

# Source with specific direction vector (accepts tuple, vec3, or SphericalCoord)
source_id = radiation.addCollimatedRadiationSource(
    direction=(0.3, 0.3, -0.9)  # tuple: (x, y, z)
)

# Alternative formats for direction parameter
source_id = radiation.addCollimatedRadiationSource(
    direction=vec3(0.3, 0.3, -0.9)  # vec3 object
)

import math

# SphericalCoord takes (radius, elevation_radians, azimuth_radians) - note RADIANS,
# so convert if you are working in degrees.
source_id = radiation.addCollimatedRadiationSource(
    direction=SphericalCoord(1.0, math.radians(45.0), math.radians(135.0))
)

# Set source flux
radiation.setSourceFlux(source_id, "PAR", 1200.0)  # W/m²
```

### Spherical Sources

```python
# Spherical radiation source
source_id = radiation.addSphereRadiationSource(
    position=(0, 0, 10),  # x, y, z position
    radius=0.5            # Source radius
)

# Set flux for spherical source
radiation.setSourceFlux(source_id, "PAR", 800.0)
```

### Sun Sources

```python
# Realistic sun modeling
sun_id = radiation.addSunSphereRadiationSource(
    radius=0.5,           # Sun disc radius
    zenith=45.0,          # Sun zenith angle (degrees)
    azimuth=180.0,        # Sun azimuth angle (degrees)
    position_scaling=1.0, # Position scaling factor
    angular_width=0.53,   # Sun angular width (degrees)
    flux_scaling=1.0      # Flux scaling factor
)

# Set solar flux
radiation.setSourceFlux(sun_id, "PAR", 1200.0)
```

### Visualizing Sources and Cameras

Radiation sources and cameras have no geometry of their own. `enableLightModelVisualization()`
adds a 3D model of each sphere, sun-sphere, disk and rectangle source to the Context (collimated
sources have no position and get none), and `enableCameraModelVisualization()` adds one at each
camera, pointed along its view. Sources and cameras added later get a model too, and moving a
source with `setSourcePosition()` moves its model.

The models are ordinary Context primitives, so they show in the Visualizer and in OBJ exports. They
carry `invisibility_flag = 1` (see Invisible Primitives below), so they do not
affect the simulation. The sun-sphere model is sized and placed from the domain's bounding sphere,
so enable visualization after adding the scene geometry. The disable methods remove the models.
Calling an enable method again rebuilds the models rather than adding a second set, and calling a
disable method twice, or after some model primitives were deleted, is harmless.

```python
radiation.addSphereRadiationSource(vec3(0, 0, 2), 0.25)
radiation.addRectangleRadiationSource(vec3(1, 0, 2), vec2(0.5, 0.5), vec3(0, 0, 0))
radiation.enableLightModelVisualization()
radiation.enableCameraModelVisualization()

context.writeOBJ("scene_with_sources.obj")

radiation.disableLightModelVisualization()
radiation.disableCameraModelVisualization()
```

## Flux Configuration

### Source Flux Management

```python
# Single source flux
radiation.setSourceFlux(source_id, "PAR", 1000.0)

# Multiple sources with same flux
source_ids = [source1, source2, source3]
radiation.setSourceFlux(source_ids, "PAR", 800.0)

# Get current source flux
current_flux = radiation.getSourceFlux(source_id, "PAR")
print(f"Source flux: {current_flux} W/m²")

# Diffuse radiation flux
radiation.setDiffuseRadiationFlux("PAR", 200.0)
```

## Ray Configuration

### Ray Count Settings {#RadRayCountSettings}

```python
# Configure ray counts for accuracy vs. performance
radiation.setDirectRayCount("PAR", 1000)    # Direct rays
radiation.setDiffuseRayCount("PAR", 3000)   # Diffuse rays

# Higher ray counts for better accuracy
radiation.setDirectRayCount("PAR", 5000)
radiation.setDiffuseRayCount("PAR", 10000)
```

The defaults are 100 direct rays and 1000 diffuse rays per primitive. The diffuse ray count is also used for the scattering iterations.

> **Note:** Bands run together in one `runBand()` call share a single ray launch, which uses the largest direct and diffuse ray counts set for any of those bands. If "PAR" is set to 100 direct rays and "NIR" to 1000, `runBand(["PAR", "NIR"])` traces both with 1000. To give each band its own ray count, run the bands in separate `runBand()` calls.

### Ray Count Guidelines

```python
# Performance vs accuracy trade-offs
ray_configs = {
    "fast": {"direct": 100, "diffuse": 300},
    "standard": {"direct": 1000, "diffuse": 3000}, 
    "high_quality": {"direct": 5000, "diffuse": 15000},
    "research": {"direct": 10000, "diffuse": 30000}
}

# Apply configuration
config = ray_configs["standard"]
radiation.setDirectRayCount("PAR", config["direct"])
radiation.setDiffuseRayCount("PAR", config["diffuse"])
```

## Advanced Configuration

### Scattering Control

```python
# Set the maximum number of scattering iterations
radiation.setScatteringDepth("PAR", 3)

# Optionally stop early once no primitive has more than this flux (W/m²) left to scatter.
# The default of 0 never stops early.
radiation.setMinScatterEnergy("PAR", 0.01)
```

The energy still waiting to be scattered after the last iteration is not dropped: the remaining
iterations are summed as a geometric series. A scattering depth of 3 to 5 is therefore usually
enough, even in strongly scattering bands such as near-infrared. Since helios-core 1.3.96 the
same series is applied to radiation camera images, so they converge at the same depths as the
absorbed flux. (Before, an image saw only the iterations that were traced: a near-infrared image
of a canopy was about 11% too dark at the default depth of 3 and 4% at a depth of 5.)

Between a layer of leaves (or a cover) and the ground below it, the fraction scattered again
alternates from one iteration to the next. Since helios-core 1.3.96 the series is summed over
pairs of iterations when that happens, which makes such layered scenes accurate from a depth of 3.
Earlier versions extrapolated from the last iteration alone, so the absorbed flux of a leaf over
soil in a strongly scattering band was overestimated after an even depth and underestimated after
an odd one (by up to +400% at a depth of 2 and -15% at the default depth of 3). Results for
canopies, where the alternation is weak, are essentially unchanged. The same release fixed
`runBand()` stopping with "The energy to be scattered ... did not decrease" in scenes with a large
primitive under a few small reflective ones, such as a ground patch below young leaves.

A band with a scattering depth of 0 has no scattering: its primitives absorb all the radiation
they intercept. Radiation cameras image such a band too (helios-core 1.3.96+; previously, when no
band in a `runBand()` call had a depth of at least 1, cameras were not rendered and recorded 0).
As in the radiation solution, surfaces in such a band are black: the camera sees their blackbody
emission and the sky and sources behind them, but no reflected or transmitted radiation. This
suits, for example, a thermal camera imaging surfaces at known temperatures.

Later scattering iterations launch fewer diffuse rays per primitive, in proportion to the energy
left to scatter (minimum 16). This makes strongly scattering bands faster, at the cost of somewhat
noisier scattered flux on deeply shaded primitives and in camera images. Call
`radiation.disableScatteringRayReduction()` to launch the full diffuse ray count in every
iteration, and `enableScatteringRayReduction()` to restore the default.

> **Note:** Before helios-core 1.3.92 the energy left after the last iteration was absorbed where
> it sat, which overstated near-infrared leaf absorption by about 20% at a scattering depth of 3,
> and `setMinScatterEnergy()` had no effect.

### Diffuse Sky Hemisphere

The diffuse (ambient) sky set by `setDiffuseRadiationFlux()` fills only the upper hemisphere.
Rays that leave all geometry heading below the horizon -- past the edge of a finite ground, or
from the underside of an isolated object -- receive no diffuse radiation.

```python
# Remove domain edge effects (recommended)
radiation.enforcePeriodicBoundary("xy")

# Or fill the full sphere with sky radiation, so rays leaving below the horizon
# receive the same diffuse radiation as rays leaving upward (all bands)
radiation.enableBelowHorizonDiffuseRadiation()
radiation.disableBelowHorizonDiffuseRadiation()   # back to the default
```

Radiation cameras always show sky below the horizon (helios-core 1.3.96+). A camera ray that
leaves all geometry below the horizon, for example past the far edge of a finite ground, sees the
sky radiance at the horizon in the same azimuth, so a finite domain no longer renders a black strip
between its edge and the horizon and the sky is continuous across it. This applies to camera rays
only: the diffuse radiation that lights the scene still comes from the upper hemisphere, so the
sky seen through such a gap did not illuminate the scene. With
`enableBelowHorizonDiffuseRadiation()` the camera instead sees the sky's full-sphere angular
pattern below the horizon, as the diffuse rays do.

> **Note:** Before helios-core 1.3.92 the sky filled the full sphere, so an isolated two-sided
> horizontal patch absorbed twice the diffuse flux. Diffuse fluxes near the edges of finite
> domains and on isolated objects are lower than in earlier versions.

### Invisible Primitives

Setting the `uint` primitive data `invisibility_flag` to 1 makes a primitive invisible to the
radiation model: it is not intersected by any ray, does not appear in camera images, and neither
absorbs nor emits radiation. It takes precedence over `twosided_flag`, including one set through
a material. Call `updateGeometry()` after setting it on existing primitives.

```python
context.setPrimitiveDataUInt(uuid, "invisibility_flag", 1)
radiation.updateGeometry()
```

### Spectral Textures {#RadSpectralTexture}

A patch or triangle with a spectral texture (`Context.setPrimitiveSpectralTexture()`, with the
class spectra named by a palette registered with `Context.addSpectralPalette()`; spectral textures
are also read and written by `Context.loadXML()` / `writeXML()`) takes its reflectivity and
transmissivity from the class of its class map at each point, instead of from its
`reflectivity_spectrum` and `transmissivity_spectrum` primitive data, which it ignores. Each
class's spectra are weighted over a band exactly as a primitive's are, and are looked up in the
Context's global data or the plug-in's spectral libraries; a spectrum that cannot be found raises
an error.

- **Absorption** follows the class map: every ray leaving the primitive uses the class at the point
  it leaves from, so a leaf whose sunlit half is green and shaded half is brown absorbs as such. The
  radiation the primitive reflects and transmits is still one flux per face, spread evenly over it.
- **Cameras** see each pixel in the outgoing radiation of the class its ray hits. The radiation
  reaching each face is that of the primitive as a whole, so the pattern within a primitive comes
  from its classes, not from shadows across it. With camera flux smoothing
  (`enableCameraFluxSmoothing()`) the light is interpolated smoothly across facets while the
  classes stay sharp.
- **Per-pixel classes** are recorded as global data `camera_<camera>_pixel_spectral_class` and can
  be written as COCO masks with `writeImageSegmentationMasksBySpectralClass()` (see
  [Segmentation Masks](#segmentation-masks-for-instance-segmentation)).
- The optional output primitive data `reflectivity` and `transmissivity`
  (`optionalOutputPrimitiveData()`) report the area-weighted means of the primitive's classes.
- Each class must conserve energy on its own: reflectivity plus transmissivity above 1 in any class
  the primitive covers raises an error, even if the mean does not. A class spectrum that does not
  overlap a band with wavelength bounds raises an error when the band is run; in a band without
  bounds a class's spectra are weighted by the spectral responses of the cameras that image the
  band, as a primitive's are (see [Spectral Surface Properties](#RadSpectralSurfaceProperties)),
  or take the default reflectivity and transmissivity of 0 if no camera with a response images it.
- In a band with thermal emission a primitive has one emissivity, so rays use the primitive's own
  values there. Its classes must then agree in that band, or the primitive can be given constant
  `reflectivity_<band>` / `transmissivity_<band>` data for it, which override the palette in such a
  band only. A SIF band is treated like a band without emission.

The following raise an error when combined with a spectral texture:

- Primitive data `reflectivity_<band>` or `transmissivity_<band>` in a band without thermal
  emission (including a fluorescence band).
- Translucent covers.
- Classes whose reflectivity or transmissivity differ in a band with thermal emission, unless the
  primitive has constant values for that band.

**Surface layers.** Since helios-core 1.3.97 a primitive with a spectral texture can have a
specular surface layer (`specular_roughness` / `specular_n`); before that the combination raised an
error. All of its classes lie under the same layer, the primitive's (or its material's), and each
class's spectra give its reflectivity and transmissivity as totals at normal incidence. The layer's
reflection, highlight and angular split are the primitive's, the same for every class. A class must
therefore reflect at least what the layer alone reflects at normal incidence, a(1), in every band
and as weighted by each camera's spectral response, or `runBand()` raises an error naming the class
and its palette.

#### Surfaces with a Class Map {#RadSurfaceClassMap}

A class map of a surface that is not a leaf, such as bark or a fruit skin, is defined by an XML
file of the same name beside it, which names the surface's spectra and scales them for each class:

```xml
<helios>
  <surface_class_map reflectivity_spectrum="bark_reflectivity_0000" transmissivity_spectrum=""
                     provenance="AppleBark.jpg via utilities/leaf_class_maps/fit_classes --surface">
    <class id="1" reflectance_scale="0.11"/>
    <class id="2" reflectance_scale="0.46"/>
    ...
  </surface_class_map>
</helios>
```

The spectra are taken from the spectral library or from the Context's global data, and each
class's spectra are the surface's spectra times its `reflectance_scale` (held to at most 1, and to
at most 1 together). \ref pyhelios.RadiationModel.RadiationModel.applySpectralClassMaps
"applySpectralClassMaps(uuids=None)" (helios-core 1.3.96+) builds the palette
`surface_<class map>` from such definitions for every primitive given to it that carries the
primitive data `spectral_class_map` (the class map's path), and assigns the spectral texture. With
no argument it considers every primitive in the Context.

A surface with a specular surface layer, such as a waxy fruit skin, can instead have classes that
scale only the body under the layer (helios-core 1.3.97+): with `scales="body"` on
`<surface_class_map>`, a class of `reflectance_scale` s has the reflectivity a(1) + s (ρ − a(1)) and
the transmissivity s τ, where ρ and τ are the surface's spectra and a(1) is what the layer of the
primitives reflects at normal incidence. `applySpectralClassMaps()` reads each primitive's layer
(`specular_roughness` and `specular_n`, from its material or primitive data), so **set the layer
first**; primitives with different layers get separate palettes,
`surface_<class map>_n<refractive index>_r<roughness>`. It raises an error if such a map is applied
to a primitive without a layer or with a per-band refractive index (`specular_n_<band>`), or if the
surface's reflectivity falls below a(1) at any wavelength; `runBand()` raises one if a primitive's
layer was changed afterwards (call `applySpectralClassMaps()` again).

PlantArchitecture records the class map on the bark and fruit of library models that have one,
such as `apple` and `apple_fruitingwall` (see `InternodeParameters.image_class_map_file` and
`InflorescenceParameters.fruit_class_map_file` in the
[PlantArchitecture documentation](plugin_plantarchitecture.md)), so one call after building the
plants is all that is needed. Call it before `updateGeometry()`, as a spectral texture assigned
afterwards is not seen until the geometry is updated again:

```python
from pyhelios import Context, PlantArchitecture, RadiationModel
from pyhelios.types import vec3

with Context() as context, PlantArchitecture(context) as plantarch:
    plantarch.loadPlantModelFromLibrary("apple")
    plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 1200)

    with RadiationModel(context) as radiation:
        radiation.applySpectralClassMaps()   # bark (and any class-mapped fruit); leaves are left to LeafOptics
        radiation.updateGeometry()
```

Primitives carrying a class map defined relative to a leaf, as PlantArchitecture records on
leaves through `LeafPrototype.leaf_class_map_file`, are left alone: their classes are derived from
the leaf's properties by \ref pyhelios.LeafOptics.LeafOptics.run "LeafOptics.run()" (see the
[LeafOptics documentation](plugin_leafoptics.md)). A whole plant can therefore be passed at once.

The fruit of the `apple` models also carries, as primitive data set by its prototype, a red-apple
skin spectrum (`apple_fruit_reflectivity_0000`) under a waxy specular surface layer
(`specular_roughness` 0.15, `specular_n` 1.45), and since helios-core 1.3.97 its class map
(`AppleFruit_classes.png`, the skin's blush) scales the body under that layer (`scales="body"`).
Override them by setting the same primitive data after the plant is built and before calling
`applySpectralClassMaps()`.

Class maps and their definitions can be made from a texture with
`utilities/leaf_class_maps/fit_classes` in helios-core (its `--surface` mode, for anything that is
not a leaf). A class scales the whole spectrum, so its colour in linear light is the spectrum's;
the fitter holds every class below a visible reflectance of 0.6 by default, because the brightest
parts of a photograph of a natural surface are gloss and lit curvature rather than reflectance,
and a class scaled past that renders washed out.

### Normal and Bump Maps {#RadNormalMaps}

Since helios-core 1.3.97 the radiation model applies normal and bump maps (set with
`Context.setMaterialNormalMap()`, `setMaterialBumpMap()`, or per primitive with
`setPrimitiveNormalMap()` / `setPrimitiveBumpMap()`) on all backends (OptiX 8, OptiX 6.5, Vulkan). A
primitive with a map has a shading normal that varies across its surface while its geometry stays
flat. The model uses the shading normal for everything that depends on the angle of the light at
the surface, and the facet's own normal for everything that depends on its extent, so energy is
conserved:

- **Direct radiation.** A relief intercepts exactly the beam its footprint does, so the direct
  radiation a primitive receives is unchanged by its map, and a Lambertian primitive absorbs the same
  with or without one. A specular surface layer splits what arrives at the angle of the shading
  normal.
- **Diffuse, scattered and emitted radiation.** Rays still leave in a cosine lobe about the facet
  normal, so a Lambertian primitive absorbs the same diffuse radiation with or without a map; a
  surface layer splits each ray's radiation at its angle to the shading normal.
- **Cameras.** The direct radiation of the sources is shaded at every hit point with the shading
  normal (softened toward the shadow terminator), as are a layer's viewing angle and highlight. Sky
  and scattered radiation is shaded by the mean direction it arrived from at each face, interpolated
  across facets with camera flux smoothing. This works with and without camera flux smoothing and
  spectral textures.

The bottom face of a primitive uses the negated shading normal, as the other side of a thin sheet
does. A primitive needs (u,v) coordinates for its map (a patch, or a textured triangle). Maps cost
2 bytes per texel and 6 bytes per primitive on the GPU, plus 24 bytes per launched band for each
mapped primitive while there are cameras; when no primitive has a map nothing is stored and results
are those of a model without the feature.

- A map changed after `updateGeometry()` raises an error at the next `runBand()`; call
  `updateGeometry()` again.
- **Translucent covers (`glass_n_<band>`) cannot have normal maps**: `runBand()` raises an error.

### Reproducibility

The ray tracer draws its random numbers from the Context's random generator, so seeding the
Context with `context.seedRandomGenerator(seed)` makes `runBand()` fluxes and camera images
reproducible on a given backend (helios-core 1.3.92+). Results are not identical across
backends.

### Emission Control {#RadEmissionControl}

```python
# Enable/disable emission for thermal radiation
radiation.enableEmission("thermal")
radiation.disableEmission("PAR")  # PAR typically doesn't emit
```

Each primitive emits with emissivity `emissivity_<band>` (default 1) at its `temperature` primitive data (default 300 K). How much it emits depends on whether the band has wavelength bounds:

- A band added without bounds, such as `addRadiationBand("LW")`, is treated as broadband longwave and emits the full εσT⁴. This is the usual setup for the longwave band of an energy balance.
- A band added with bounds, such as `addRadiationBand("thermal", 8000, 14000)`, emits only the part of the Planck spectrum inside them, εσT⁴ times the blackbody band fraction. A thermal camera band with bounds therefore records in-band radiance: at 300 K the 8-14 µm band holds about 38% of σT⁴. \ref pyhelios.RadiationModel.RadiationModel.getCameraPixelBrightnessTemperature "getCameraPixelBrightnessTemperature()" converts a thermal camera's pixels back to brightness temperatures by inverting this relation for each pixel (see [Thermal Cameras](#RadThermalCamera)).

The band fraction and the Planck spectral radiance are available as `Global.blackbodyBandFraction(wavelength_min_nm, wavelength_max_nm, temperature_K)` and `Global.blackbodySpectralRadiance(wavelength_nm, temperature_K)` (from `pyhelios import Global`), for example to convert an in-band flux back to a temperature or to check the emission of a surface.

Any diffuse (sky) flux given to a bounded emission band with `setDiffuseRadiationFlux()` should also be the in-band value rather than the broadband longwave flux; \ref pyhelios.SolarPosition.SolarPosition.getThermalSkyFlux "SolarPosition.getThermalSkyFlux()" computes it for bands within 5.5-15.3 µm.

> **Note:** Before helios-core 1.3.90 every emission band emitted the full broadband σT⁴ regardless of its bounds. Results for bounded emission bands are lower than in earlier versions (by about 2.7x for 8-14 µm at 300 K), and a visible band with bounds and emission left enabled no longer emits several hundred W/m².

`runBand()` records, for each band, its emission state as global data named `emission_enabled_<band>` (`uint`, 1 when emission is enabled for that band and 0 otherwise), its scattering depth as `scattering_depth_<band>` (`uint`), and, for a band with wavelength bounds, the bounds as `wavelength_bounds_<band>` (`vec2`, nm). The energy balance model uses these so that the thermal radiation it emits matches the emission of its bands here. They record each band as configured at the most recent `runBand()` call, so a band whose emission, scattering depth, or bounds are changed afterwards should be run again before the energy balance. The emitting bands given to the energy balance model must account for the blackbody spectrum once — either a single band without bounds, or adjacent bounded bands that together span the thermal spectrum — so a bounded thermal camera band should not be added to the energy balance model alongside the longwave band. You can read the values back through the Context:

```python
radiation.runBand(["PAR", "thermal"])

context.getGlobalData("emission_enabled_thermal")  # 1
context.getGlobalData("emission_enabled_PAR")      # 0
```

The values exist only for bands that have actually been run, since `runBand()` is what writes them.

## Simulation Execution

### Geometry Updates

As of helios-core v1.3.79 the no-argument form is **optional**: `runBand()` builds the
geometry itself before tracing, and rebuilds it whenever primitives have been added to
or deleted from the Context since the last build. As of v1.3.92 it also rebuilds when
primitives have been moved, rotated, scaled, reshaped or re-textured. Setting primitive
data does not trigger a rebuild, so call `updateGeometry()` yourself after changing
`twosided_flag` or `invisibility_flag` on existing primitives.

```python
# Optional - runBand() would do this itself. Call it explicitly only to control
# when the cost of the build is paid.
radiation.updateGeometry()

# Restrict the model to a subset of Context primitives.
radiation.updateGeometry([patch_uuid, triangle_uuid])
```

The two forms are **not** interchangeable. A subset passed to `updateGeometry(uuids)` is
never rebuilt automatically, because an automatic rebuild would discard the subset you
asked for. After modifying Context geometry you must call `updateGeometry(uuids)` again
yourself:

```python
radiation.updateGeometry([patch_uuid])   # model now holds this one primitive
context.addPatch(center=vec3(1, 0, 0))   # new geometry the model will NOT pick up
radiation.runBand("PAR")                 # still traces only patch_uuid

radiation.updateGeometry([patch_uuid, new_uuid])  # required to widen the subset
```

Calling `updateGeometry()` with no argument clears the subset and returns the model to
tracking the full Context.

`updateGeometry()` raises for a scene containing voxels, which no ray-tracing backend
supports, and for a triangle whose texture has a transparency channel but which has no
texture (u,v) coordinates, such as one textured with `setPrimitiveTextureFile()`.

### Running Simulations

**CRITICAL PERFORMANCE NOTE**: When simulating multiple radiation bands, **ALWAYS** run all bands in a single `runBand()` call rather than sequential single-band calls. This provides **significant computational efficiency gains** (often 2-5x faster) because:

- GPU ray tracing setup is performed once for all bands
- Scene geometry acceleration structures are reused across bands
- GPU kernel launches are batched together
- Memory transfers between CPU/GPU are minimized
- Ray traversal computations are shared between spectral bands

```python
# ✅ EFFICIENT - Single call for multiple bands (RECOMMENDED)
radiation.runBand(["PAR", "NIR", "SW"])

# ❌ INEFFICIENT - Sequential single-band calls (AVOID)
radiation.runBand("PAR")    # Full GPU setup overhead
radiation.runBand("NIR")    # Full GPU setup overhead again  
radiation.runBand("SW")     # Full GPU setup overhead again

# Single band execution (when only one band needed)
radiation.runBand("PAR")
```

Bands run together are traced with the largest direct and diffuse ray counts set for any of them (see [Ray Count Settings](#RadRayCountSettings)), so run bands separately when they need different ray counts.

### Performance Comparison

```python
import time

# Method 1: Sequential calls (SLOW)
start_time = time.time()
radiation.runBand("PAR")
radiation.runBand("NIR") 
radiation.runBand("SW")
sequential_time = time.time() - start_time

# Method 2: Multi-band call (FAST)
start_time = time.time()
radiation.runBand(["PAR", "NIR", "SW"])
multiband_time = time.time() - start_time

print(f"Sequential: {sequential_time:.2f}s")
print(f"Multi-band: {multiband_time:.2f}s") 
print(f"Speedup: {sequential_time/multiband_time:.1f}x faster")
```

## Results and Analysis

### Flux Results

`getAbsorbedFlux(band)` returns one band's absorbed flux density in W/m², with
element `i` belonging to `uuids[i]`.

```python
# Get absorbed flux density (W/m^2) for all primitives, for one band
all_uuids = context.getAllUUIDs()
results = radiation.getAbsorbedFlux("PAR")

# Convert to absorbed power (W) by weighting each primitive by its area.
# Pass the whole UUID list to getPrimitiveArea(): one native call, rather than
# one per primitive. Accumulate in float64 - areas are float32, and a plain
# sum() over them drifts on canopy-sized scenes.
import numpy as np
areas = context.getPrimitiveArea(all_uuids)                 # ndarray, shape (N,)
power = np.asarray(results, dtype=np.float64) * areas       # W, per primitive
print(f"Total absorbed power: {power.sum(dtype=np.float64):.2f} W")

# Analyze results per primitive
for uuid, flux_density, p in zip(all_uuids, results, power):
    print(f"Primitive {uuid}: {flux_density:.2f} W/m² ({p:.2f} W)")

# Several bands at once -> dict of band label to per-primitive list
bands = radiation.getAbsorbedFlux(["PAR", "NIR", "SW"])
print(f"PAR on first primitive: {bands['PAR'][0]:.2f} W/m²")

# Restrict to a subset of primitives; results follow the order you pass
leaf_flux = radiation.getAbsorbedFlux("PAR", uuids=leaf_uuids)
```

### Radiation Analysis

```python
# Calculate radiation statistics over the per-primitive flux densities (W/m^2)
radiation_data = radiation.getAbsorbedFlux("PAR")

# getAbsorbedFlux returns a float32 array, so use numpy rather than statistics:
# each of these is one vectorized pass instead of a Python-level loop.
mean_flux = radiation_data.mean(dtype="float64")
max_flux = radiation_data.max()
min_flux = radiation_data.min()
std_flux = radiation_data.std(dtype="float64")

print(f"Radiation statistics (flux density):")
print(f"  Mean: {mean_flux:.2f} W/m²")
print(f"  Max: {max_flux:.2f} W/m²")
print(f"  Min: {min_flux:.2f} W/m²")
print(f"  Std Dev: {std_flux:.2f} W/m²")
```

Note that these statistics are unweighted: each primitive contributes equally
regardless of its size. For an area-weighted scene average, divide total absorbed
power by total area.

## Advanced Band Management

### Query Band Existence

```python
# Check if band exists before using it
if radiation.doesBandExist("PAR"):
    print("PAR band exists")
    radiation.setDirectRayCount("PAR", 1000)
else:
    radiation.addRadiationBand("PAR")
```

### Copy Band with Wavelength Range

```python
# Copy band preserving original wavelength range
radiation.addRadiationBand("fullspectrum", 300, 3000)
radiation.copyRadiationBand("fullspectrum", "fullspectrum_copy")

# Copy band with new wavelength range
radiation.copyRadiationBand("fullspectrum", "PAR", 400, 700)
radiation.copyRadiationBand("fullspectrum", "NIR", 700, 1100)
```

## Geometric Radiation Sources

### Rectangle Sources (LED Panels, Grow Lights)

```python
from pyhelios.types import vec3, vec2

# Add rectangular radiation source (e.g., LED panel)
led_panel = radiation.addRectangleRadiationSource(
    position=vec3(0, 0, 5),      # Center position 5m above ground
    size=vec2(2.0, 1.0),          # 2m × 1m panel
    rotation=vec3(0, 0, 0)        # Rotation (Euler angles in radians)
)

# Configure the LED panel
radiation.addRadiationBand("LED")
radiation.setSourceFlux(led_panel, "LED", 500.0)  # 500 W/m²

# Set LED spectrum
led_spectrum = [
    (400, 0.0), (450, 0.3), (500, 0.8),
    (550, 0.5), (600, 0.2), (700, 0.0)
]
radiation.setSourceSpectrum(led_panel, led_spectrum)
```

### Disk Sources (Spotlights, Circular LEDs)

```python
# Add circular disk source (e.g., spotlight)
spotlight = radiation.addDiskRadiationSource(
    position=vec3(2, 2, 5),      # Position
    radius=0.5,                   # 0.5m radius
    rotation=vec3(0, 0, 0)        # Rotation
)

radiation.setSourceFlux(spotlight, "PAR", 800.0)
```

### Dynamic Source Positioning

```python
# Reposition sources for time-series simulations
for time_step in range(24):  # 24 hour simulation
    # Move sun position
    sun_position = calculate_sun_position(time_step)
    radiation.setSourcePosition(sun_id, sun_position)

    # Run simulation for this time step
    radiation.runBand("PAR")
    results = radiation.getAbsorbedFlux("PAR")
    save_results(time_step, results)

# Delete sources when no longer needed
radiation.deleteRadiationSource(temporary_source_id)
```

## Spectral Data Management

### Setting Source Spectra

```python
# Define custom spectrum (wavelength in nm, relative intensity)
sunlight_spectrum = [
    (300, 0.1), (400, 0.5), (500, 1.0),
    (600, 0.9), (700, 0.7), (800, 0.5)
]

# Set spectrum for single source
radiation.setSourceSpectrum(sun_source, sunlight_spectrum)

# Set spectrum for multiple sources
led_sources = [led1, led2, led3]
radiation.setSourceSpectrum(led_sources, led_spectrum)

# Use predefined spectrum from global data or the spectral library
radiation.setSourceSpectrum(source_id, "CIE_D65")
```

The spectral library includes the CIE 1931 2-degree colour-matching functions (`CIE1931_2deg_xbar`,
`CIE1931_2deg_ybar`, `CIE1931_2deg_zbar`) and CIE standard illuminant D65 (`CIE_D65`), from
`spectral_data/cie_colorimetry.xml` (helios-core 1.3.96+), so `"CIE_D65"` can be used directly as a
source spectrum.

### Spectrum Integration and Analysis

```python
# Define leaf reflectance spectrum
leaf_reflectance = [
    (400, 0.08), (500, 0.10), (550, 0.45),
    (600, 0.15), (650, 0.12), (700, 0.50),
    (750, 0.55), (800, 0.52)
]

# Basic integration (total)
total = radiation.integrateSpectrum(leaf_reflectance)
print(f"Total reflectance: {total}")

# Integration over PAR range (400-700nm)
par_reflectance = radiation.integrateSpectrum(leaf_reflectance, 400, 700)
print(f"PAR reflectance: {par_reflectance}")

# Source-weighted average over a range: int(S*f) / int(S)
source_weighted = radiation.integrateSpectrum(
    leaf_reflectance, 400, 700, source_id=sun_id
)

# Camera-response-weighted average: int(f*C) / int(C)
camera_response = [(400, 0.2), (550, 1.0), (700, 0.3)]
camera_weighted = radiation.integrateSpectrum(
    leaf_reflectance, camera_spectrum=camera_response
)

# Source- and camera-weighted, normalized by the source: int(S*f*C) / int(S)
source_camera_weighted = radiation.integrateSpectrum(
    leaf_reflectance, source_id=sun_id, camera_spectrum=camera_response
)

# Integrate source spectrum directly
sun_par_flux = radiation.integrateSourceSpectrum(sun_id, 400, 700)
print(f"Sun PAR flux: {sun_par_flux} W/m²")
```

When integrating over a wavelength range, the spectrum is linearly interpolated to the bounds, so a bound that falls between tabulated points contributes only the part of its segment inside the range (helios-core 1.3.89+; earlier versions integrated the whole segment containing each bound).

The source- and camera-weighted forms return weighted averages rather than plain integrals, and treat every spectrum as zero outside the wavelengths at which it is tabulated. A source tabulated from 500 to 600 nm therefore weights only that part of a 400-700 nm range (helios-core 1.3.90+; earlier versions held the source's edge values across the rest of the range). The source must have a spectrum, and the call raises if there is nothing to weight by: a source spectrum with no energy between the bounds or where the camera response is tabulated, or a camera response that is zero everywhere. Earlier versions returned NaN.

### Spectral Surface Properties {#RadSpectralSurfaceProperties}

Setting the primitive data `reflectivity_spectrum` or `transmissivity_spectrum` to the label of a spectrum in Context global data makes the model compute that primitive's reflectivity or transmissivity in each band that has wavelength bounds, by averaging the spectrum over the band weighted by the incident radiation's spectrum.

```python
radiation.addRadiationBand("PAR", 400, 700)
context.setPrimitiveDataString(leaf_uuids, "reflectivity_spectrum", "leaf_reflectivity")
context.setPrimitiveDataString(leaf_uuids, "transmissivity_spectrum", "leaf_transmissivity")
```

- **A band value overrides the spectrum.** If `reflectivity_<band>` or `transmissivity_<band>` is also set on the primitive, that value is used in that band instead of the spectrum, including a value of 0. Before helios-core 1.3.90 a value of 0 was ignored and the spectrum used, so a scene that carries a band value of 0 alongside a spectrum (for example, one loaded from XML) now uses 0.
- **Spectra are zero outside their tabulated range.** This holds for source spectra and for reflectivity and transmissivity spectra alike. A reflectivity or transmissivity spectrum that does not overlap a band at all has no defined value in it, and `runBand()` raises when that band is run; set a constant `reflectivity_<band>` or `transmissivity_<band>` for that band instead.
- **Bands without wavelength bounds use the camera responses.** A band added without bounds has no range to integrate over, so a spectrum there is weighted by the spectral response of the cameras that image the band instead: the band reflectivity and transmissivity are the camera-weighted values divided by the camera-weighted value of a white surface, averaged over the cameras with a response in the band. This is how satellite or multispectral bands defined only by a camera's spectral response are set up. Without such a camera a spectrum has no value in a band without bounds, and the default of 0 is used. (Before helios-core 1.3.96 the transmissivity stayed 0 in such a band, so leaves were opaque there and camera images of canopies over soil were too dark.)
- **A source needs energy where it has flux.** If a source has a flux in a band (for example from `setSourceFlux()`) but its spectrum has no energy in that band, or a diffuse flux has a diffuse spectrum with no energy in the band, `runBand()` raises when the band is run with surfaces that have spectral properties. Earlier versions silently used a reflectivity and transmissivity of 0, so surfaces absorbed all of that radiation.
- **Several sources.** Radiation coming directly from a source uses properties weighted by that source's spectrum. Diffuse, scattered and emitted radiation use properties weighted by the band's combined incident spectrum: each source's spectrum and the diffuse spectrum, in proportion to their band fluxes. Before helios-core 1.3.90 they were weighted by the spectrum of source 0 alone, so results with several differently coloured sources in one band depended on the order the sources were added.

The model supports at most 255 radiation sources.

### Spectrum Normalization

```python
# Set spectrum integral (normalizes spectrum to target value)
radiation.setSourceSpectrumIntegral(source_id, 1000.0)  # Total = 1000 W/m²

# Set integral over specific wavelength range (PAR)
radiation.setSourceSpectrumIntegral(source_id, 500.0, 400, 700)  # PAR = 500 W/m²
```

### Spectrum Manipulation

```python
# Scale existing spectrum in-place
radiation.scaleSpectrum("leaf_reflectance", 1.2)  # Increase by 20%

# Create new scaled spectrum
radiation.scaleSpectrum("leaf_reflectance", "bright_leaf", 1.5)

# Random scaling for stochastic simulations
radiation.scaleSpectrumRandomly("base_leaf", "variant_leaf", 0.8, 1.2)

# Blend multiple spectra with weights
radiation.blendSpectra(
    new_label="mixed_leaf",
    spectrum_labels=["young_leaf", "mature_leaf", "old_leaf"],
    weights=[0.2, 0.5, 0.3]
)

# Random blending
radiation.blendSpectraRandomly(
    new_label="random_canopy",
    spectrum_labels=["leaf_type_a", "leaf_type_b", "leaf_type_c"]
)
```

## Diffuse Radiation

### Directionally-Biased Diffuse Radiation

```python
# Set diffuse radiation with extinction coefficient and peak direction
radiation.addRadiationBand("SW")
radiation.setDiffuseRadiationFlux("SW", 200.0)

# Sky radiation peaked at zenith
from pyhelios.types import vec3
radiation.setDiffuseRadiationExtinctionCoeff(
    label="SW",
    K=0.5,                    # Extinction coefficient
    peak_direction=vec3(0, 0, 1)  # Zenith direction
)

# Or use spherical coordinates. SphericalCoord takes elevation and azimuth in
# RADIANS, so convert from degrees when needed.
import math
from pyhelios.types import SphericalCoord
radiation.setDiffuseRadiationExtinctionCoeff(
    label="SW",
    K=0.3,
    peak_direction=SphericalCoord(1.0, math.radians(45.0), math.radians(90.0))
)

# Query diffuse flux
diffuse_flux = radiation.getDiffuseFlux("SW")
print(f"Diffuse flux: {diffuse_flux} W/m²")
```

> **`getDiffuseFlux()` is an input, not a result.** It returns the band's
> *configured* diffuse source flux — a single scalar, the value you set with
> `setDiffuseRadiationFlux()` (or derived from the diffuse spectrum) — not
> per-primitive absorbed diffuse radiation. There is no separate accessor for the
> absorbed diffuse component: `getAbsorbedFlux(band)` already reports each
> primitive's total absorbed flux for that band, direct plus diffuse plus
> scattered.

### Diffuse Spectrum Configuration

```python
# Set diffuse spectrum from global data
radiation.setDiffuseSpectrum("SW", "sky_spectrum")

# Set for multiple bands
radiation.setDiffuseSpectrum(["SW", "NIR"], "atmospheric_spectrum")

# Set diffuse spectrum integral (all bands)
radiation.setDiffuseSpectrumIntegral(1000.0)

# Set integral with wavelength range
radiation.setDiffuseSpectrumIntegral(500.0, 400, 700)

# Set integral for specific band
radiation.setDiffuseSpectrumIntegral(300.0, band_label="PAR")
radiation.setDiffuseSpectrumIntegral(200.0, 400, 700, band_label="PAR")
```

## Spectral Interpolation

### Primitive-Based Spectral Assignment

```python
# Automatically assign spectra based on primitive data values
leaf_patches = context.getAllUUIDs("patch")

# Assign leaf reflectance based on age
radiation.interpolateSpectrumFromPrimitiveData(
    primitive_uuids=leaf_patches,
    spectra_labels=["young_leaf_spectrum", "mature_leaf_spectrum", "old_leaf_spectrum"],
    values=[0.0, 50.0, 100.0],  # Days since emergence
    primitive_data_query_label="leaf_age",
    primitive_data_radprop_label="reflectance"
)

# Assign based on nitrogen content
radiation.interpolateSpectrumFromPrimitiveData(
    primitive_uuids=leaf_patches,
    spectra_labels=["low_n_leaf", "medium_n_leaf", "high_n_leaf"],
    values=[0.5, 2.0, 4.0],  # % nitrogen
    primitive_data_query_label="nitrogen_percent",
    primitive_data_radprop_label="reflectance"
)
```

### Object-Based Spectral Assignment

```python
# Assign spectra based on object-level data
tree_ids = [tree1_id, tree2_id, tree3_id]

radiation.interpolateSpectrumFromObjectData(
    object_ids=tree_ids,
    spectra_labels=["healthy_tree", "stressed_tree", "diseased_tree"],
    values=[1.0, 0.5, 0.0],  # Health index (0-1)
    object_data_query_label="health_index",
    primitive_data_radprop_label="reflectance"
)
```

## Camera Management

### Dynamic Camera Control

```python
from pyhelios.types import vec3, SphericalCoord

# Create camera
radiation.addRadiationCamera("cam1", ["red", "green", "blue"],
                           position=vec3(0, 0, 10),
                           lookat_or_direction=vec3(0, 0, 0))

# Reposition camera dynamically
radiation.setCameraPosition("cam1", vec3(5, 5, 15))
position = radiation.getCameraPosition("cam1")
print(f"Camera at: {position}")

# Update camera target
radiation.setCameraLookat("cam1", vec3(2, 2, 0))
lookat = radiation.getCameraLookat("cam1")
print(f"Camera looking at: {lookat}")

# Set camera orientation
radiation.setCameraOrientation("cam1", vec3(0, 0, 1))  # Look down
orientation = radiation.getCameraOrientation("cam1")
print(f"Camera orientation: {orientation}")

# Query all cameras
cameras = radiation.getAllCameraLabels()
print(f"Available cameras: {cameras}")
```

### Solar-Induced Fluorescence (SIF) Camera (helios-core v1.3.72+)

PyHelios v0.1.21+ exposes the Fluspect-B-driven SIF camera type. Each user-defined emission band must already exist via `addRadiationBand()`; those bands are flagged internally as SIF-emitting and use the Fluspect-B leaf-fluorescence kernel for emission instead of Stefan-Boltzmann. Helios auto-creates internal radiation bands covering 400–750 nm at the requested `excitation_bin_width_nm` and reuses them across cameras with matching bin widths. Per-band emission is computed as the Fluspect-B excitation→emission kernel scaled by the van der Tol (2014) rate-coefficient quantum yield Φ_F, and injected into the standard `runBand()` emission loop so that escape probability and canopy reabsorption emerge naturally from the 3D ray tracer. Per-leaf biochemistry is authored via the LeafOptics plug-in — see [LeafOptics → Radiation SIF integration](plugin_leafoptics.md#LOSIFIntegration).

```python
from pyhelios import RadiationModel, SIFCameraProperties
from pyhelios.types import vec3

with RadiationModel(context) as radiation:
    radiation.addRadiationBand("F687", 685.0, 690.0)   # SIF red peak
    radiation.addRadiationBand("F760", 758.0, 762.0)   # SIF far-red peak

    sif_props = SIFCameraProperties(
        camera_resolution=(512, 512),
        excitation_bin_width_nm=10.0,        # 10 nm excitation bins (default)
        excitation_scattering_depth=0,        # 0 = no inter-leaf scatter
    )

    radiation.addSIFCamera(
        "sif_cam",
        emission_band_labels=["F687", "F760"],
        position=vec3(0, 0, 5),
        lookat_or_direction=vec3(0, 0, 0),
        camera_properties=sif_props,
        antialiasing_samples=64,
    )

    assert radiation.isSIFCamera("sif_cam")
```

Each emission band is locked to a single excitation bin width — re-flagging the same band from a second camera with a different bin width is an error. The Fluspect-B kernel acts on the excitation flux *incident* on each leaf (leaf absorption is already contained in the kernel). At the default `excitation_scattering_depth=0`, only excitation arriving directly from the sources is counted, so leaves inside a canopy miss the excitation scattered to them by other leaves (most in the far-red end of the excitation range, where leaf reflectance and transmittance are both large). Set `excitation_scattering_depth >= 1` to include inter-leaf scattering, at the cost of additional excitation-band ray traces.

Each leaf face emits the Fluspect-B *backward* spectrum of the excitation it receives plus the *forward* spectrum of the excitation received by the opposite face, so for a leaf lit from above the top face emits the backward spectrum. The two differ most in the red band near 685 nm, where backward emission is about twice as strong for a typical leaf because red fluorescence is reabsorbed crossing the leaf.

The fluorescence quantum yield Φ_F follows van der Tol et al. (2014), Eq. 19, with its unstressed parameter set (the SCOPE default). It is driven by the per-leaf `electron_transport_ratio` primitive data — the relative light saturation Ja/Je, which is 1 in the dark and falls as light saturates photosynthesis — and by leaf `temperature` (the radiation model's default of 300 K when absent; a non-positive temperature is an error). `electron_transport_ratio` is written by the Farquhar and C4 photosynthesis models when requested as an optional output (see [Photosynthesis optional outputs](plugin_photosynthesis.md#PhotoOptionalOutputData)); the empirical model cannot drive SIF. Primitives without `fluspect_spectrum` do not fluoresce, but a primitive that has `fluspect_spectrum` and no `electron_transport_ratio` when a SIF band is run makes `runBand()` raise an error. Run the PAR band before photosynthesis, or every leaf sees zero light and gets the dark-adapted yield (Ja/Je = 1) regardless of its actual illumination.

> **Note:** helios-core 1.3.89 corrected the SIF emission scaling and fluorescence yield, so absolute SIF values are much lower than those produced by earlier versions.

> Per-leaf excitation-flux storage scales as `O(N_leaves * N_excitation_bands)` where
> `N_excitation_bands = ceil(350 / excitation_bin_width_nm)`. For very large
> canopies prefer a coarser bin width (e.g., 20 nm) to keep memory bounded.

### Camera Spectral Response

```python
# Set custom camera spectral response
radiation.setCameraSpectralResponse("cam1", "red", "custom_red_response")

# Use standard camera models
radiation.setCameraSpectralResponseFromLibrary("cam1", "iPhone13")
radiation.setCameraSpectralResponseFromLibrary("cam2", "NikonD850")
radiation.setCameraSpectralResponseFromLibrary("cam3", "CanonEOS5D")

# Available camera models: iPhone13, NikonD850, CanonEOS5D, and more
```

When every band of a camera has a spectral response, the model identifies the camera's red, green and blue bands from those responses (see [Camera Red, Green and Blue Bands](#RadCameraRGBBands)), and an RGB camera is colour corrected from them automatically (see [Camera Colour Correction](#RadCameraColorCorrection)). helios-core 1.3.96 also fixed the library's `SpectralDevicesMSC_spectral_response` red, green and NIR980 responses, whose out-of-order wavelengths made any camera using them fail to load.

### Programmatic Pixel Access

```python
# Get raw pixel data
pixels = radiation.getCameraPixelData("cam1", "red")
print(f"Image size: {len(pixels)} pixels")
print(f"Mean intensity: {sum(pixels)/len(pixels)}")

# Modify pixels programmatically
enhanced_pixels = [p * 1.3 for p in pixels]  # Brighten by 30%
radiation.setCameraPixelData("cam1", "red", enhanced_pixels)

# Apply custom image processing
import numpy as np
pixel_array = np.array(pixels)
filtered = apply_custom_filter(pixel_array)
radiation.setCameraPixelData("cam1", "red", filtered.tolist())
```

## Advanced Simulation Features

### Periodic Boundary Conditions

```python
# Enable periodic boundaries for large-scale simulations. Call before updateGeometry().
# Valid boundaries are "x", "y", "xy", and "none" (or "") - there is no periodic z mode.
# Any other string raises ValueError. Each call replaces the previous boundary.
radiation.enforcePeriodicBoundary("xy")   # Periodic in x and y
radiation.enforcePeriodicBoundary("x")    # Periodic in x only
radiation.enforcePeriodicBoundary("y")    # Periodic in y only
radiation.enforcePeriodicBoundary("none") # Remove the periodic boundary (helios-core 1.3.97+)
```

**Primitives that do not repeat** (helios-core 1.3.97+). `excluded_uuids` lists primitives that
exist only once, in the central copy of the domain - for example a sensor mast or a plant of another
species standing in an infinite canopy:

```python
mast_uuids = context.getObjectPrimitiveUUIDs(mast_objID)
radiation.enforcePeriodicBoundary("xy", excluded_uuids=mast_uuids)  # canopy repeats, mast does not
```

The period is then the width of the bounding box of the primitives that do repeat (e.g. the
ground), and every excluded primitive must lie laterally within it; `updateGeometry()` raises an
error otherwise. An excluded UUID that does not exist raises immediately. The list is read when the
geometry is updated: primitives added later are not excluded, and excluded primitives deleted later
are dropped. With excluded primitives the model also solves the radiation field *without* them,
which the periodic copies and cameras use, so the sky an excluded object hides and the light it
scatters appear once rather than around every copy. The reported `radiation_flux_<band>` values are
those of the scene as it is, in the central copy. This makes `runBand()` about 5-15% slower. In
camera images every primitive's direct radiation (except a translucent cover's) is then evaluated
per pixel sample with a shadow ray, so the object's cast shadow falls only where the object puts
it. An excluded primitive cannot be a translucent cover (`runBand()` raises).

**A limited number of copies** (helios-core 1.3.97+). `max_repeats` is an `int2` giving the number
of copies on each side of the central domain in x and y. Values must not be negative and must be 0
for a direction that is not periodic; a limit of 0 gives the same result as no periodic boundary in
that direction. A ray that leaves the field continues as one that leaves the scene (sky, source or
camera background). Every copy shows the radiation of the central domain, so the darker edges of a
real finite field are not resolved:

```python
from pyhelios.types import int2
radiation.enforcePeriodicBoundary("xy", max_repeats=int2(5, 5))   # an 11 x 11 field of copies
radiation.enforcePeriodicBoundary("x", excluded_uuids=mast_uuids, max_repeats=int2(3, 0))
```

\note Changed in helios-core 1.3.97: an unknown boundary string now raises an error instead of
printing a warning, each call replaces the previous boundary instead of adding to it, and a primitive
in a periodic domain is now hit by rays from itself in its periodic copies (it previously received
sky through its own copies and was not shaded by them).

### G-Function Calculation

```python
# Calculate geometry factor for canopy radiation modeling
from pyhelios.types import vec3

# Vertical view
g_vertical = radiation.calculateGtheta(vec3(0, 0, 1))
print(f"G-function (vertical): {g_vertical}")

# Oblique view
g_oblique = radiation.calculateGtheta(vec3(0.5, 0.5, 0.7))
print(f"G-function (oblique): {g_oblique}")

# Horizontal view
g_horizontal = radiation.calculateGtheta(vec3(1, 0, 0))
print(f"G-function (horizontal): {g_horizontal}")
```

\note `calculateGtheta()` calls `updateGeometry()` automatically (emitting a warning) if the scene geometry has not yet been pushed to the radiation model, so an explicit prior `updateGeometry()` is not required. If the G-function is undefined — no geometry, or zero total leaf area in the scene — it raises an explicit `RuntimeError` rather than returning NaN.

\note The one case it will *not* auto-build is a model holding a primitive subset from `updateGeometry(uuids)` that has not been traced yet: building the full Context there would silently discard the subset, so it raises instead and tells you to call `updateGeometry(uuids)` again (or `updateGeometry()` if you want the whole Context). After a `runBand()` the geometry is already built, so the G-function is simply reported over the subset you selected.

### Optional Outputs

```python
# Enable optional primitive data outputs.
# Only "reflectivity" and "transmissivity" are recognized; any other label
# prints a warning and enables nothing.
radiation.optionalOutputPrimitiveData("reflectivity")
radiation.optionalOutputPrimitiveData("transmissivity")
```

\note `getSkyEnergy()` is deprecated: no ray-tracing backend computes the energy lost to the sky, so it always returned 0. As of helios-core 1.3.92 it emits a `DeprecationWarning` and raises, and it will be removed in helios-core v2.0.

## Spectral Modeling Workflows

### Realistic Sunlight Modeling

```python
# Create realistic solar spectrum
solar_spectrum = [
    (300, 0.05), (350, 0.15), (400, 0.35), (450, 0.65),
    (500, 0.90), (550, 1.00), (600, 0.95), (650, 0.85),
    (700, 0.75), (750, 0.70), (800, 0.65), (900, 0.55)
]

# Add sun source
sun_id = radiation.addSunSphereRadiationSource(
    radius=1.0, zenith=30.0, azimuth=180.0
)

# Set solar spectrum
radiation.setSourceSpectrum(sun_id, solar_spectrum)

# Normalize to total solar irradiance (1000 W/m²)
radiation.setSourceSpectrumIntegral(sun_id, 1000.0)

# Or normalize just PAR component to 500 W/m²
radiation.setSourceSpectrumIntegral(sun_id, 500.0, 400, 700)
```

### Multi-Spectral Leaf Modeling

```python
# Define leaf spectra at different developmental stages
young_leaf = [(400, 0.08), (550, 0.40), (700, 0.45), (800, 0.50)]
mature_leaf = [(400, 0.10), (550, 0.45), (700, 0.50), (800, 0.55)]
old_leaf = [(400, 0.06), (550, 0.30), (700, 0.35), (800, 0.40)]

# Create interpolated spectra for intermediate ages
for age in [10, 20, 30, 40]:
    radiation.scaleSpectrum(
        "young_leaf",
        f"leaf_age_{age}",
        scale_factor=1.0 + (age / 100.0)
    )

# Generate stochastic leaf variations
for i in range(100):
    radiation.scaleSpectrumRandomly(
        "mature_leaf",
        f"leaf_variant_{i}",
        min_scale=0.85,
        max_scale=1.15
    )
```

### Canopy Spectral Diversity

```python
# Get all leaf patches
leaf_patches = context.getAllUUIDs("patch")

# Assign spectra based on canopy height
radiation.interpolateSpectrumFromPrimitiveData(
    primitive_uuids=leaf_patches,
    spectra_labels=["upper_canopy", "middle_canopy", "lower_canopy"],
    values=[15.0, 8.0, 2.0],  # Height thresholds (meters)
    primitive_data_query_label="height",
    primitive_data_radprop_label="reflectance"
)

# Mix leaf types for realistic heterogeneity
radiation.blendSpectra(
    new_label="canopy_average",
    spectrum_labels=["sunlit_leaf", "shaded_leaf"],
    weights=[0.3, 0.7]  # 30% sunlit, 70% shaded
)
```

## Multi-View Camera Imaging

<a name="CameraRenderOrder"></a>
### Camera rendering order

`writeCameraImage()`, `writeNormCameraImage()` and `writeCameraImageData()` do not
render anything. They only write out pixel data that a previous `runBand()` call
produced. Three ordering rules follow from this:

1. **Add the camera before calling `runBand()`.** `runBand()` renders only the
   cameras that exist when it runs. A camera added afterwards has no pixel data
   until the next `runBand()`.
2. **Render every band you intend to write.** `runBand()` fills in pixel data
   only for the bands passed to it, so `runBand(["red", "green", "blue"])`
   followed by `writeCameraImage(..., bands=["NIR"])` fails even though the NIR
   band exists.
3. **Re-run `runBand()` after moving a camera or changing the scene.** Pixel data
   reflects the scene as of the last render.

White balance, colour correction and exposure act on a camera's whole image, so
`runBand()` applies them once every band of the camera has been rendered since the
image was last processed (helios-core 1.3.96+). A camera rendered one band per
`runBand()` call is processed when its last band is rendered, and a camera whose bands
are not rendered in a call is left as it is. If only some of the bands of an already
processed image are rendered again, the image is incomplete until the rest are rendered
too: reading it in the meantime (e.g. `getCameraPixelData()` or `writeCameraImage()`)
raises an error, since it would mix processed and unprocessed bands. (Earlier versions
re-applied exposure to every camera on every `runBand()` call, so an `"ISOXXX"`-exposed
camera's gain compounded with each call.)

```python
# Correct order
radiation.addRadiationCamera("cam", ["red", "green", "blue"], ...)  # 1. add camera
radiation.runBand(["red", "green", "blue"])                         # 2. render
radiation.writeCameraImage("cam", ["red", "green", "blue"], "out")  # 3. write
```

(`runBand()` pushes the geometry itself, so no `updateGeometry()` step is needed.)

Getting this wrong raises a `RadiationModelError` naming the camera and band that
were never rendered. PyHelios checks the precondition itself before calling into
the native library and reports which `runBand()` call is missing.

### Time-Series Camera Capture

```python
from pyhelios.types import vec3

# Set up camera
radiation.addRadiationCamera("timelapse", ["red", "green", "blue"],
                           position=vec3(0, 0, 20),
                           lookat_or_direction=vec3(0, 0, 0))

# Capture from multiple viewpoints
viewpoints = [
    vec3(10, 0, 15), vec3(0, 10, 15),
    vec3(-10, 0, 15), vec3(0, -10, 15)
]

for i, viewpoint in enumerate(viewpoints):
    # Move camera
    radiation.setCameraPosition("timelapse", viewpoint)

    # Update lookat to track target
    radiation.setCameraLookat("timelapse", vec3(0, 0, 5))

    # Re-render from the new viewpoint. This is required: writeCameraImage()
    # only reads pixel data produced by runBand(), so moving the camera without
    # re-running would write the previous viewpoint's image.
    radiation.runBand(["red", "green", "blue"])

    # Capture image
    radiation.writeCameraImage(
        "timelapse", ["red", "green", "blue"],
        f"view_{i}", frame=i
    )
```

\note `writeCameraImage()` renders nothing itself -- it only writes out pixel data that `runBand()` has already produced. See [Camera rendering order](#CameraRenderOrder) for the ordering rules this implies.

### Multi-Spectral Imaging with Standard Cameras

```python
# Create camera with iPhone 13 spectral response
radiation.addRadiationCamera("iphone_cam", ["red", "green", "blue"],
                           position=vec3(0, 0, 10),
                           lookat_or_direction=vec3(0, 0, 0))

radiation.setCameraSpectralResponseFromLibrary("iphone_cam", "iPhone13")

# Create camera with professional DSLR response
radiation.addRadiationCamera("dslr_cam", ["red", "green", "blue"],
                           position=vec3(5, 0, 10),
                           lookat_or_direction=vec3(0, 0, 0))

radiation.setCameraSpectralResponseFromLibrary("dslr_cam", "NikonD850")

# Run simulation and compare
radiation.runBand(["red", "green", "blue"])

iphone_img = radiation.writeCameraImage("iphone_cam", ["red", "green", "blue"], "iphone")
dslr_img = radiation.writeCameraImage("dslr_cam", ["red", "green", "blue"], "dslr")
```

## Advanced Workflows

### Growth Simulation with Spectral Changes

```python
# Simulate plant growth over 100 days
for day in range(100):
    # Update leaf age data
    leaf_patches = context.getAllUUIDs()
    # One native call each way, rather than two per primitive
    ages = context.getPrimitiveDataArray(leaf_patches, "age")
    context.setPrimitiveDataFloat(leaf_patches, "age", ages + 1.0)

    # Interpolate spectra based on updated ages
    radiation.interpolateSpectrumFromPrimitiveData(
        primitive_uuids=leaf_patches,
        spectra_labels=["juvenile", "mature", "senescent"],
        values=[0.0, 50.0, 100.0],
        primitive_data_query_label="age",
        primitive_data_radprop_label="reflectance"
    )

    # Run radiation simulation
    radiation.runBand("PAR")

    # Analyze results - convert flux density (W/m^2) to absorbed power (W)
    flux = radiation.getAbsorbedFlux("PAR")
    # Both calls return arrays: one vectorized multiply, and float64
    # accumulation so summing float32 areas does not drift.
    daily_radiation[day] = float((flux * context.getPrimitiveArea(leaf_patches)).sum(dtype="float64"))
```

### Multi-Source Lighting Scenarios

```python
# Create complex lighting setup
# Natural sunlight
sun = radiation.addSunSphereRadiationSource(1.0, 45.0, 180.0)
radiation.setSourceFlux(sun, "PAR", 600.0)

# Supplemental LED grow lights (rectangular panels)
led1 = radiation.addRectangleRadiationSource(
    position=vec3(-3, 0, 4), size=vec2(1, 2), rotation=vec3(0, 0, 0)
)
led2 = radiation.addRectangleRadiationSource(
    position=vec3(3, 0, 4), size=vec2(1, 2), rotation=vec3(0, 0, 0)
)

# LED spectrum (red-blue for photosynthesis)
led_spectrum = [
    (400, 0.0), (450, 0.8), (500, 0.2),
    (600, 0.1), (660, 1.0), (700, 0.0)
]

radiation.setSourceSpectrum([led1, led2], led_spectrum)
radiation.setSourceFlux([led1, led2], "PAR", 200.0)

# Run combined natural + artificial lighting
radiation.runBand("PAR")
```

### Quality Control with Source Position Tracking

```python
# Query and verify source positions
all_cameras = radiation.getAllCameraLabels()
print(f"Configured cameras: {all_cameras}")

# Get source positions for verification
for source_id in [sun, led1, led2]:
    pos = radiation.getSourcePosition(source_id)
    print(f"Source {source_id} at: {pos}")

# Verify band configuration
bands = ["PAR", "NIR", "SW"]
for band in bands:
    if radiation.doesBandExist(band):
        flux = radiation.getDiffuseFlux(band)
        print(f"{band}: {flux} W/m² diffuse")
```

## Complete Workflow Example

```python
from pyhelios import Context, WeberPennTree, WPTType, RadiationModel
from pyhelios import RadiationModelError
from pyhelios.types import *

try:
    # Create scene
    context = Context()

    # Add ground plane
    ground_uuid = context.addPatch(
        center=vec3(0, 0, 0),
        size=vec2(10, 10),
        color=RGBcolor(0.3, 0.2, 0.1)
    )

    # Generate tree
    wpt = WeberPennTree(context)
    tree_id = wpt.buildTree(WPTType.LEMON)

    # Run radiation simulation
    with RadiationModel(context) as radiation:
        # Configure multiple radiation bands for comprehensive analysis
        radiation.addRadiationBand("PAR")  # Photosynthetically Active Radiation
        radiation.addRadiationBand("NIR")  # Near Infrared
        radiation.addRadiationBand("SW")   # Total Shortwave
        
        # Add sun
        sun_id = radiation.addSunSphereRadiationSource(
            radius=0.5,
            zenith=30.0,    # Morning sun
            azimuth=135.0   # Southeast
        )
        
        # Configure sources for all bands
        radiation.setSourceFlux(sun_id, "PAR", 600.0)  # W/m² PAR
        radiation.setSourceFlux(sun_id, "NIR", 500.0)  # W/m² NIR  
        radiation.setSourceFlux(sun_id, "SW", 1200.0)  # W/m² Total SW
        
        # Add diffuse sky radiation for all bands
        radiation.setDiffuseRadiationFlux("PAR", 100.0)
        radiation.setDiffuseRadiationFlux("NIR", 80.0)
        radiation.setDiffuseRadiationFlux("SW", 200.0)
        
        # Configure simulation quality for all bands
        for band in ["PAR", "NIR", "SW"]:
            radiation.setDirectRayCount(band, 2000)
            radiation.setDiffuseRayCount(band, 6000)
            radiation.setScatteringDepth(band, 2)
        
        # Run simulation - EFFICIENT multi-band execution
        radiation.updateGeometry()
        radiation.runBand(["PAR", "NIR", "SW"])  # Single call for all bands!
        
        # Analyze results, one band at a time. Do NOT use getTotalAbsorbedFlux()
        # here: it would return PAR + NIR + SW added together, and its ordering
        # does not line up with all_uuids.
        all_uuids = context.getAllUUIDs()
        results = radiation.getAbsorbedFlux("PAR")   # W/m^2, PAR only
        
        # Get leaf-specific results. results[] is flux density (W/m^2), so each
        # primitive must be area-weighted before the values can be summed.
        # getPrimitiveArea() accepts the whole list, which costs one native call
        # instead of one per primitive - do NOT call it per UUID in a loop.
        import numpy as np
        areas = context.getPrimitiveArea(all_uuids)          # ndarray, shape (N,)
        power = np.asarray(results, dtype=np.float64) * areas  # W, per primitive
        
        # Accumulate in float64: areas come back as float32, and a plain sum() over
        # them drifts on canopy-sized scenes.
        leaf_uuids = set(wpt.getLeafUUIDs(tree_id))
        is_leaf = np.array([u in leaf_uuids for u in all_uuids])
        leaf_absorption = float(power[is_leaf].sum(dtype=np.float64))
        
        total_absorption = float(power.sum(dtype=np.float64))
        ground_absorption = float(power[all_uuids.index(ground_uuid)])
        
        print(f"Total scene PAR absorption: {total_absorption:.2f} W")
        print(f"Leaf PAR absorption: {leaf_absorption:.2f} W")
        print(f"Ground PAR absorption: {ground_absorption:.2f} W")
        
        # Access band-specific data stored by the radiation model. runBand() writes
        # each band's absorbed flux density to primitive data "radiation_flux_<band>";
        # getAbsorbedFlux() reads exactly that, keyed by UUID.
        per_band = radiation.getAbsorbedFlux(["PAR", "NIR", "SW"])
        for band, flux in per_band.items():
            mean_flux = flux.mean(dtype="float64")
            print(f"Band {band}: mean absorbed flux density {mean_flux:.2f} W/m²")
        
        # Equivalent, reading the primitive data directly in one native call:
        #   context.getPrimitiveDataArray(all_uuids, "radiation_flux_PAR")
        # A per-UUID comprehension over getPrimitiveDataFloat() returns the same
        # values but costs one native call per primitive -- avoid it on large scenes.

except RadiationModelError as e:
    print(f"Radiation modeling failed: {e}")
    print("Ensure GPU with Vulkan support is available (or NVIDIA GPU with CUDA/OptiX)")
    print("Check that radiation plugin is compiled: build_scripts/build_helios --plugins radiation")
except Exception as e:
    print(f"Simulation setup failed: {e}")
    print("Check geometry creation and tree generation parameters")
```

### Data Storage

`runBand()` already stores each band's absorbed flux density as primitive data
under `radiation_flux_<band>`, so there is nothing to store for that quantity —
just read it back with `getAbsorbedFlux(band)`. You only need to write primitive
data for quantities you derive yourself:

```python
# Read back what runBand() stored (W/m^2, PAR only, aligned to all_uuids)
import numpy as np
all_uuids = context.getAllUUIDs()
results = radiation.getAbsorbedFlux("PAR")

# Absorbed power in W is derived, so it does need storing. Both getPrimitiveArea()
# and setPrimitiveDataFloat() accept the whole UUID list - one native call each,
# rather than two per primitive.
areas = context.getPrimitiveArea(all_uuids)
power = np.asarray(results, dtype=np.float64) * areas
context.setPrimitiveDataFloat(all_uuids, "absorbed_power_PAR", power.tolist())

# Use for visualization - "radiation_flux_PAR" is already there from runBand()
context.colorPrimitiveByDataPseudocolor(
    all_uuids, "radiation_flux_PAR", "hot", 256
)
```

> **Reading primitive data in bulk:** either `context.getPrimitiveDataArray(uuids,
> label)` (returns a NumPy array) or a list comprehension over
> `context.getPrimitiveDataFloat()` works, and both are linear in the primitive
> count.

## Camera and Image Functions

> **Note**: Camera functions are available in Helios core v1.3.47+ and PyHelios v0.0.4+

The RadiationModel includes camera functionality for generating synthetic images, object detection training data, and auto-calibrated imagery.

### Camera Image Generation

```python
# Basic camera image writing (returns output filename)
filename = radiation.writeCameraImage(
    camera="overhead_camera",
    bands=["Red", "Green", "Blue"],
    imagefile_base="scene_rgb",
    image_path="./images",
    frame=-1  # All frames
)
print(f"Camera image saved to: {filename}")

# Normalized camera images  
filename = radiation.writeNormCameraImage(
    camera="side_camera",
    bands=["NIR", "Red"], 
    imagefile_base="false_color",
    image_path="./output"
)

# Camera image data in ASCII format
radiation.writeCameraImageData(
    camera="overhead_camera",
    band="RGB",
    imagefile_base="raw_data",
    image_path="./data"
)

# Camera image data in EXR format (lossless float precision, v1.3.66+)
radiation.writeCameraImageDataEXR(
    camera="overhead_camera",
    band="PAR",                    # Single band
    imagefile_base="raw_float_data",
    image_path="./data"
)

# Multi-band EXR (all bands as separate channels in one file)
radiation.writeCameraImageDataEXR(
    camera="overhead_camera",
    band=["Red", "Green", "Blue"],  # Multiple bands
    imagefile_base="rgb_float_data",
    image_path="./data"
)
```

### Depth Image Export

```python
# Depth image as ASCII text file
radiation.writeDepthImageData(
    camera_label="overhead_camera",
    imagefile_base="depth_data",
    image_path="./data"
)

# Depth image as EXR file (lossless float precision, v1.3.66+)
radiation.writeDepthImageDataEXR(
    camera_label="overhead_camera",
    imagefile_base="depth_float",
    image_path="./data"
)

# Normalized depth image (grayscale JPEG for visualization)
radiation.writeNormDepthImage(
    camera_label="overhead_camera",
    imagefile_base="depth_visual",
    max_depth=50.0,  # Maximum depth for normalization
    image_path="./data"
)
```

### Object Detection Training Data

Generate YOLO-format bounding boxes for machine learning training:

```python
# Single primitive data label
radiation.writeImageBoundingBoxes(
    camera_label="training_camera",
    primitive_data_labels="leaf_type",
    object_class_ids=1,  # Class ID for "leaf"
    image_file="training_001.jpg",
    classes_txt_file="plant_classes.txt",
    image_path="./annotations"
)

# Multiple primitive data labels for multi-class detection
radiation.writeImageBoundingBoxes(
    camera_label="training_camera", 
    primitive_data_labels=["leaves", "stems", "fruits"],
    object_class_ids=[0, 1, 2],  # Different class IDs
    image_file="training_002.jpg",
    classes_txt_file="classes.txt"
)

# Object-based bounding boxes (entire objects)
radiation.writeImageBoundingBoxes(
    camera_label="training_camera",
    object_data_labels=["tree_1", "tree_2", "shrub_1"], 
    object_class_ids=[10, 10, 20],  # Tree class=10, Shrub class=20
    image_file="training_003.jpg"
)
```

### Segmentation Masks for Instance Segmentation

Generate COCO-format JSON files for semantic/instance segmentation:

```python
# Single primitive segmentation
radiation.writeImageSegmentationMasks(
    camera_label="segmentation_camera",
    primitive_data_labels="plant_part",
    object_class_ids=1,
    json_filename="segmentation_001.json",
    image_file="seg_image_001.jpg",
    append_file=False
)

# Multiple primitive classes in one image
radiation.writeImageSegmentationMasks(
    camera_label="segmentation_camera",
    primitive_data_labels=["leaf", "bark", "soil"],
    object_class_ids=[1, 2, 3],
    json_filename="multi_class_seg.json", 
    image_file="scene_segmentation.jpg",
    append_file=True  # Add to existing annotations
)

# Object-level segmentation
radiation.writeImageSegmentationMasks(
    camera_label="segmentation_camera",
    object_data_labels=["individual_plant_1", "individual_plant_2"],
    object_class_ids=[100, 101],  # Unique instance IDs
    json_filename="instance_segmentation.json",
    image_file="plant_instances.jpg"
)
```

Note that one label value can produce more than one annotation: an object partly hidden behind
something closer to the camera is visible as several separate regions, each annotated in its own
right.

#### Masks by Spectral-Texture Class

Masks can also follow the classes of [spectral textures](#RadSpectralTexture), which vary within a
primitive. Whenever `runBand()` renders a camera and some primitive has a spectral texture, it
records the class each pixel sees as the global data `camera_<camera>_pixel_spectral_class` (one
`uint` per pixel, 0 where the pixel sees no primitive with a spectral texture, mirrored
left-to-right relative to the written image, as `camera_<camera>_pixel_UUID` is).
`writeImageSegmentationMasksBySpectralClass()` writes one annotation for each connected region of
pixels of one class, with the class value as the COCO category ID. A class spanning several
primitives, such as the lesions of a leaf, gives one mask per region it forms in the image, however
many primitives it covers. Classes mean the same thing in every palette of a class map, so the
masks do not depend on which palette is in use.

```python
radiation.runBand(["red", "green", "blue"])
image_file = radiation.writeCameraImage("visible", ["red", "green", "blue"], "leaf", "./")

# Class 1 of the leaves' class map is healthy lamina and class 2 is lesion
radiation.writeImageSegmentationMasksBySpectralClass(
    camera_label="visible",
    class_names={1: "lamina", 2: "lesion"},   # class value (>= 1) -> category name
    json_filename="lesion_masks.json",
    image_file=image_file,
    data_attribute_labels=[],                 # optional: data averaged within each mask
    append_file=False,
)
```

Only the classes listed in `class_names` are annotated. It raises if the camera does not exist, if
`class_names` is empty or contains class 0, if the image file does not exist, or if the classes
were not recorded (the camera has not been rendered by `runBand()`, or no primitive in the model's
geometry has a spectral texture).

### Per-Pixel Data Label Maps

Export a camera's per-pixel primitive- or object-data values as a dense, row-major map — useful for ground-truth regression targets (e.g. per-pixel temperature, leaf age, or any numeric primitive/object data field). Float, double, uint, and int data types are supported; background pixels (no primitive struck) receive a configurable `padvalue` (default NaN).

```python
# Write the map to a row-major ASCII text file
radiation.writePrimitiveDataLabelMap(
    camera="overhead_camera",
    primitive_data_label="temperature",
    imagefile_base="temp_map",
    image_path="./data",
    padvalue=float("nan"),   # value for background (no-hit) pixels
)
radiation.writeObjectDataLabelMap(
    camera="overhead_camera",
    object_data_label="plant_id",
    imagefile_base="plantid_map",
    image_path="./data",
)

# Or get the map directly as a 2D (height, width) NumPy array (no file left on disk)
temp = radiation.getPrimitiveDataLabelMap("overhead_camera", "temperature")  # shape (H, W)
plant_id = radiation.getObjectDataLabelMap("overhead_camera", "plant_id")
```

### Updating Camera Parameters

`updateCameraParameters()` changes an existing camera's intrinsics in place, preserving its position, lookat direction, and spectral band configuration.

> **Changing `camera_resolution` discards the camera's rendered image data.** The per-pixel buffers are sized to the resolution the camera was rendered at, so helios-core v1.3.79+ clears them rather than reinterpreting them at the new size. Re-render with `runBand()` before writing an image, or `writeCameraImage()` will report the camera as unrendered. Changing any other parameter leaves image data intact.

```python
radiation.runBand(["red", "green", "blue"])
radiation.writeCameraImage("cam", ["red", "green", "blue"], "before")

# Changing HFOV only - image data survives.
radiation.updateCameraParameters("cam", CameraProperties(camera_resolution=(512, 512), HFOV=45))

# Changing resolution - image data is discarded.
radiation.updateCameraParameters("cam", CameraProperties(camera_resolution=(1024, 1024), HFOV=45))
radiation.runBand(["red", "green", "blue"])          # required before writing again
radiation.writeCameraImage("cam", ["red", "green", "blue"], "after")
```

### Simulating Satellite Imagery {#RadCameraAtmosphere}

A camera normally records the radiance leaving the scene. A sensor above the atmosphere, such as a satellite, instead records that radiance attenuated by the atmosphere, plus light scattered into its view by the atmosphere itself (path radiance) and by the surrounding ground (the adjacency effect). `enableCameraAtmosphere()` converts a camera's images to the radiance at such a sensor, using spectra computed by \ref pyhelios.SolarPosition.SolarPosition.calculateSensorAtmosphereSpectra "SolarPosition.calculateSensorAtmosphereSpectra()" (see the [Solar Position documentation](plugin_solarposition.md) for the model and its accuracy). After each camera ray trace, every pixel in a band becomes L_path + T↑ · L_pixel + L_adj, with the path and adjacency radiances integrated over the band with the camera's spectral response and the upward direct transmittance T↑ averaged over the band.

Illuminate the scene with the direct and diffuse irradiance spectra computed together with the atmosphere spectra, so that the light reaching the scene and the light leaving it pass through the same atmosphere:

```python
from pyhelios import Context, RadiationModel, SolarPosition, CameraProperties
from pyhelios.types import vec2, vec3

camera_position = vec3(0, 0, 50)
camera_lookat = vec3(0, 0, 0)

ground = context.addPatch(center=vec3(0, 0, 0), size=vec2(20, 20))
context.setPrimitiveDataFloat(ground, "reflectivity_red", 0.1)

with SolarPosition(context, utc_offset=8, latitude=38.5, longitude=121.7) as solar:
    solar.setAtmosphericConditions(101325, 298, 0.5, 0.1)
    solar.setGroundAlbedo(0.15)
    # Direction from the camera's look-at point toward its position
    solar.calculateSensorAtmosphereSpectra("satellite_atmosphere", vec3(0, 0, 1))
    sun_direction = solar.getSunDirectionVector()

with RadiationModel(context) as radiation:
    radiation.addRadiationBand("red", 620, 670)
    radiation.disableEmission("red")
    radiation.setScatteringDepth("red", 1)  # cameras record scattered radiation
    sun = radiation.addCollimatedRadiationSource(sun_direction)
    radiation.setSourceSpectrum(sun, "satellite_atmosphere_direct_irradiance")
    radiation.setDiffuseSpectrum("red", "satellite_atmosphere_diffuse_irradiance")

    properties = CameraProperties(
        HFOV=5.0,              # narrow field of view
        exposure="manual",     # keep pixel values in radiance units
        white_balance="off",
    )
    radiation.addRadiationCamera("satellite", ["red"], camera_position, camera_lookat, properties, 1)
    radiation.enableCameraAtmosphere("satellite", "satellite_atmosphere")

    radiation.runBand("red")
    radiance = radiation.getCameraPixelData("satellite", "red")
```

The camera does not need to be at orbital altitude: the atmosphere is applied analytically, so only the viewing direction matters. A camera a short distance above the scene with a narrow field of view avoids numerical precision problems, and its image can be averaged to the footprint of the satellite pixels being simulated.

The atmosphere spectra are read when `runBand()` is called, so these requirements are checked there, and violating any of them raises an error:

- The atmosphere spectra must have been computed for the direction from the camera's look-at point toward its position, to within 1 degree.
- Every pixel must see the scene. Sky pixels have no surface for the atmosphere to act on.
- A reflective band must have wavelength bounds or a camera spectral response, and must lie within the wavelength range of the atmosphere spectra (300-2600 nm at the default 1 nm resolution).
- A thermal band must have wavelength bounds within 5502-15326 nm, its spectral response must not be zero over the band, and each pixel's brightness temperature must lie within 150-400 K.

Emission (thermal) bands are converted with the thermal atmosphere computed by \ref pyhelios.SolarPosition.SolarPosition.calculateSensorThermalAtmosphere "SolarPosition.calculateSensorThermalAtmosphere()" under the same label. Because a bounded emission band emits only the in-band part of the Planck spectrum, the pixels are in-band radiances. Each pixel's radiance is converted to a brightness temperature (as `getCameraPixelBrightnessTemperature()` does for a camera without an atmosphere); the Planck spectrum at that temperature is multiplied by the atmospheric transmittance wavelength by wavelength and integrated over the band with the camera's spectral response, and the upwelling atmospheric radiance is added. Any band within 5.5-15.3 µm can be used (for example GOES ABI bands 8-16, MODIS bands 27-36, Landsat 8/9 TIRS bands 10 and 11, and 7.5-13.5 µm microbolometer cameras), but not the 3.5-5 µm bands, where reflected sunlight is significant.

```python
solar.calculateSensorThermalAtmosphere("satellite_atmosphere", vec3(0, 0, 1))

radiation.addRadiationBand("TIR", 10600, 11190)   # Landsat 8 TIRS band 10
radiation.setDiffuseRadiationFlux("TIR", solar.getThermalSkyFlux(10600, 11190))
context.setPrimitiveDataFloat(ground_uuids, "emissivity_TIR", 0.96)
```

The emissivity of many surfaces varies with wavelength in the thermal infrared, so each thermal band needs its own `emissivity_<band>`. The sky radiance the scene reflects is whatever diffuse flux the band is given, which must be the in-band value.

Any exposure other than `"manual"` and any white balance other than `"off"` rescales the images after the atmosphere is applied, so use `exposure="manual"` and `white_balance="off"` when radiance values are needed. (A thermal camera with `"auto"` exposure is the exception: its pixels stay radiances, see [Thermal Cameras](#RadThermalCamera).) For a thermal band, `getCameraPixelBrightnessTemperature(camera_label, band_label)` then gives the brightness temperature above the atmosphere of each pixel, weighted by the camera's spectral response, as satellite thermal products report it.

| Method | Description |
|---|---|
| [enableCameraAtmosphere(camera_label, atmosphere_label)](pyhelios.RadiationModel.RadiationModel.enableCameraAtmosphere) | Convert a camera's images to the radiance at a sensor above the atmosphere |
| [disableCameraAtmosphere(camera_label)](pyhelios.RadiationModel.RadiationModel.disableCameraAtmosphere) | Record the radiance leaving the scene again (the default) |

### Camera Flux Smoothing

By default each pixel reports the outgoing flux of the primitive behind it, so a coarsely tessellated curved surface renders as a set of flat panels. `enableCameraFluxSmoothing()` reconstructs the image as the radiation leaving the smooth surface that the tessellation stands for, in two parts:

- **The direct radiation of the sources** is evaluated for every pixel sample at the point the camera ray hits: a shadow ray toward a point on each source, drawn as the radiation solve draws it, decides whether the source reaches the point, and what reaches it carries the cosine of a *shading normal* interpolated across the facet from normals at the vertices it shares with its neighbours (the mean of the facet normals meeting there, each weighted by its angle at the vertex). The brightness follows the curvature of the surface, a shadow cast by another object falls where the geometry puts it within a facet, and the light fades smoothly across the terminator. The penumbra of the sun's disk and of a finite source is resolved by the camera's antialiasing samples.
- **The rest of the outgoing radiation** (sky light, light scattered by other surfaces, and emission) is averaged onto the shared vertices, weighted by facet area, and interpolated back across each facet. The top and bottom faces are averaged separately, so a thin leaf does not render as the average of its lit and shaded sides.

Primitives with a specular surface layer (`specular_roughness`) are smoothed too: their highlight of the direct radiation and the split between the body's and the layer's components with viewing angle are evaluated with the shading normal, and the layer's own outgoing component is interpolated from the vertices. The transmittance of a translucent cover that a camera looks through is still taken from the cover's facet normal. No stored vertex normals are needed: the normals are computed from the facets, so a mesh without authored normals is smoothed just as one with them is.

> **Note:** Changed in helios-core 1.3.97. Cameras now decide per pixel sample, with a shadow ray, whether each source reaches a smoothed surface; previously a cast shadow filled each facet it crossed evenly at the facet's lit fraction and stepped at facet edges, and the terminator on coarse tubes was up to 8% too dark. This adds one shadow ray per pixel sample and source on smoothed geometry. Vertex normals are now weighted by the angle each facet makes at the vertex rather than by area, which fixes straight sunlit `Tube` and `Cone` objects brightening or darkening along their length by up to about a third.

> **Note:** Changed in helios-core 1.3.96. Previously all of the outgoing flux was averaged onto the vertices, so smoothed images of coarsely tessellated sunlit surfaces were darker than the surface they represent by about cos(π/N) for N divisions (about 13% for six), spheres kept a visible step at each latitude ring, a cast shadow was spread onto neighbouring facets, and glossy primitives still showed a step at every facet edge.

This applies to `Tube`, `Sphere`, `Cone`, `Polymesh`, `Tile` and `AdaptiveTile` objects. Tubes and cones are smoothed around the circumference and along their length, across the rings where consecutive segments meet; spheres around the azimuth and across the rings bounding each zenith band. A tile is flat, so its direct radiation is that of each sub-patch, and smoothing blurs real per-sub-patch variation in the rest of the radiation, which is worth weighing against the reduction in Monte-Carlo noise. A `Box` or `Disk` object, and any primitive belonging to no object, is left alone: its faces are genuinely flat, so the per-facet value is already correct everywhere on them. A polymesh must carry the face table that `loadOBJ()` and `loadPLY()` retain; one assembled from loose primitives by `addPolymeshObject()` has no topology and is left alone.

> **Smoothing changes what the camera reports.** A pixel no longer carries the outgoing flux of the primitive behind it, but a reconstruction from that primitive's value, its neighbours' and the shading normal, so pixel values no longer correspond exactly to the `radiation_flux_*` primitive data. Nothing else is affected: the radiation solve, the `radiation_flux_*` values themselves, and the pixel-label and depth images are all unchanged. Smoothing is off by default for this reason and should be enabled deliberately.

The crease angle is the angle between adjacent facet normals above which a shared edge is treated as a hard crease, so neither the flux nor the shading normal is averaged across it. It applies to polymesh objects only, whose facets may meet at a genuine edge the tessellation resolved; the curved object types are smooth by construction and are never creased. It must be between 0 and 180 degrees.

```python
with RadiationModel(context) as radiation:
    radiation.enableCameraFluxSmoothing(crease_angle_degrees=45.0)
    print(radiation.isCameraFluxSmoothingEnabled())        # True
    print(radiation.getCameraFluxSmoothingCreaseAngle())   # 45.0

    radiation.updateGeometry()
    radiation.runBand(["red", "green", "blue"])
    radiation.writeCameraImage("cam", ["red", "green", "blue"], "smoothed")

    radiation.disableCameraFluxSmoothing()                 # back to per-facet flux
```

Toggling smoothing after geometry has been built re-uploads the geometry and rebuilds the acceleration structure, which is not cheap — prefer calling it before `updateGeometry()`.

| Method | Description |
|---|---|
| [enableCameraFluxSmoothing(crease_angle_degrees)](pyhelios.RadiationModel.RadiationModel.enableCameraFluxSmoothing) | Interpolate flux across each facet; crease angle defaults to 30 degrees |
| [disableCameraFluxSmoothing()](pyhelios.RadiationModel.RadiationModel.disableCameraFluxSmoothing) | Hold flux constant across each facet (the default) |
| [isCameraFluxSmoothingEnabled()](pyhelios.RadiationModel.RadiationModel.isCameraFluxSmoothingEnabled) | Whether smoothing is enabled |
| [getCameraFluxSmoothingCreaseAngle()](pyhelios.RadiationModel.RadiationModel.getCameraFluxSmoothingCreaseAngle) | Crease angle in degrees |

### Camera Metadata

`enableCameraMetadata(camera_labels)` makes `writeCameraImage()` write a JSON metadata file beside
each image. Its `location_properties.longitude` and `acquisition_properties.UTC_offset` are filled
from the Context's location and recorded **positive East** (ISO 6709 / ISO 8601, and the image's
EXIF tags), the opposite sign to the Context's west-positive `Location`; e.g. Davis, CA is written
with longitude −121.76 and UTC offset −8.00.

\note Changed in helios-core 1.3.97. Earlier versions copied the Context's west-positive longitude
and UTC offset unchanged, so every image was recorded in the wrong hemisphere and with a UTC offset
of the opposite sign to its EXIF OffsetTime; the UTC offset is now written with two decimals.

### Camera Image Processing Pipeline {#RadCameraPipeline}

After `runBand()` renders every band of a camera, an RGB camera's image passes through these steps, each controlled by a `CameraProperties` field:

| Step | Applied by | `CameraProperties` field | Default |
|---|---|---|---|
| White balance | `runBand()` | `white_balance` (`"auto"`/`"off"`) | `"auto"` |
| Colour correction to linear sRGB | `runBand()` | `color_correction` (`"auto"`/`"off"`) | `"auto"` |
| Exposure | `runBand()` | `exposure` (`"auto"`/`"manual"`/`"ISOXXX"`), `exposure_target` | `"auto"`, 0.235 |
| Tone curve | `writeCameraImage()` | `tone_curve` (`"auto"`/`"off"`) | `"auto"` |
| sRGB encoding | `writeCameraImage()` | - | always, for RGB images |

The camera's pixel data (`getCameraPixelData()`) is the linear image after the first three steps; the tone curve and sRGB encoding are applied only to written images. The raw camera data written by `writeCameraImageDataEXR()` is left as rendered by all of them.

> **Note:** helios-core 1.3.96 changed the defaults of this pipeline: RGB cameras with spectral responses (including every RGB camera in the camera library) are now colour corrected, written images get a tone curve, and auto exposure meters a centre-weighted mean with a target of 0.235. Rendered RGB images therefore look different from earlier versions. To reproduce the earlier appearance as closely as possible, set `color_correction="off"` and `tone_curve="off"`.

### Camera Red, Green and Blue Bands {#RadCameraRGBBands}

White balance, colour correction, auto exposure and the tone curve act on a camera's red, green and blue bands, so the model has to know which of the camera's bands those are. A thermal or multispectral camera from the camera library, and a camera with fewer than three bands, has none. For any other camera they are identified as follows (helios-core 1.3.96+):

- If **every band has a spectral response** (`setCameraSpectralResponse()`, or a camera from the camera library), each band's colour is taken from its response, whatever the band is called and in whatever order the bands are listed. The response-weighted mean wavelength decides: below 400 nm is ultraviolet, 400-505 nm blue, 505-570 nm green, 570-700 nm red, and above 700 nm near-infrared. If two bands have the same colour, such as the two green bands of some multispectral cameras, the one named for that colour is taken.
- **Otherwise**, the bands named `"red"`, `"green"` and `"blue"` (or `"R"`, `"G"` and `"B"`, in any case) are taken, and failing that, the bands of a three-band camera in the order they were listed.

So a multispectral camera with bands `["blue", "green", "red", "red_edge", "nir"]` has its RGB bands found and its red-edge and near-infrared bands left untouched; a camera listed `["B", "G", "R"]` is still an RGB camera; and a colour-infrared camera with bands `["nir", "red", "green"]` is not one, because none of its bands is blue. A camera that looks like an RGB camera but is not one (it has exactly three bands, bands named red, green and blue, or is an RGB camera from the library) prints a warning listing the mean wavelength and colour of each band; its images are not white balanced or colour corrected, and are exposed band by band as a multispectral camera's are. Setting `color_correction="off"` silences the warning. If the bands named red, green and blue have red, green and blue responses but in the wrong bands (for example with the red and blue responses swapped), an error is raised.

> **Note:** Before helios-core 1.3.96, white balance always took the first three bands, and auto exposure took any band whose name contained "red", "green" or "blue", so a `"red_edge"` or `"infrared"` band could be metered as red.

### Camera Colour Correction {#RadCameraColorCorrection}

A camera's own red, green and blue are not the red, green and blue of a display. Its three spectral responses overlap, so each channel also records light the eye would attribute to the others, and an image shown as recorded looks washed out and greyish. Real cameras convert their RGB to a display colour space with a 3x3 colour correction matrix, and since helios-core 1.3.96 radiation cameras do the same: with `CameraProperties.color_correction="auto"` (the default), a camera whose red, green and blue bands all have spectral responses converts its images to linear sRGB after white balance and before exposure.

The matrix is derived from the camera's spectral responses, so it needs no calibration images and applies equally to a user-defined camera. It is the matrix, with rows summing to 1 so that white stays white, that best maps what the camera records from the reflectance spectra shipped with the radiation plug-in (the colour boards and the leaf, soil, bark and fruit libraries), lit by CIE illuminant D65, to their colorimetric colour for the CIE 1931 standard observer. For the cameras of the camera library, corrected colours lie within about 1-2 CIEDE2000 units (median) of their colorimetric values, against about 5-6 units without the correction. The correction assumes daylight-like illumination; under strongly coloured artificial light (e.g. tungsten) the colour error roughly doubles.

\ref pyhelios.RadiationModel.RadiationModel.getCameraColorCorrectionMatrix "getCameraColorCorrectionMatrix(camera_label)" returns the matrix as three rows of three; it is also recorded in the camera's image metadata (`color_correction_matrix`, see `enableCameraMetadata()`).

```python
from pyhelios import RadiationModel, CameraProperties
from pyhelios.types import vec3

radiation.addRadiationCameraFromLibrary("cam", "Nikon_D700", position=vec3(0, -5, 1), lookat=vec3(0, 0, 0.5))
radiation.runBand(["red", "green", "blue"])

ccm = radiation.getCameraColorCorrectionMatrix("cam")   # [[r0, r1, r2], [g0, g1, g2], [b0, b1, b2]]
```

The correction changes only the camera's images (`getCameraPixelData()` and written JPEG images); the raw data written by `writeCameraImageDataEXR()` is left as rendered. Cameras without spectral responses and cameras that are not RGB (e.g. thermal or multispectral) are never corrected. A camera whose responses do not distinguish colours, such as one with the same response in every band, has no matrix: its images are left uncorrected with a warning, and `getCameraColorCorrectionMatrix()` raises `RadiationModelError`.

Set `color_correction="off"` to keep a camera's own RGB, for example to apply a matrix of your own with `applyCameraColorCorrectionMatrix()`, which since helios-core 1.3.96 raises an error for a camera whose current image was already colour corrected automatically, rather than correcting the colours twice:

```python
props = CameraProperties(color_correction="off")
radiation.addRadiationCamera("cam_own_ccm", ["red", "green", "blue"], position, lookat, props)
radiation.setCameraSpectralResponseFromLibrary("cam_own_ccm", "NikonD700")
radiation.runBand(["red", "green", "blue"])
radiation.applyCameraColorCorrectionMatrix("cam_own_ccm", "red", "green", "blue", "my_ccm.xml")
```

### Camera Exposure

`CameraProperties` carries an `exposure` field that is passed through to the native camera by `addRadiationCamera()` and `updateCameraParameters()`. Supported modes are `"auto"` (automatic exposure, the default), `"manual"` (no automatic exposure scaling, pixel values stay in radiance units), and `"ISOXXX"` (ISO-based, e.g. `"ISO100"`, scaled by the ISO, shutter speed and aperture). Use `"manual"` when you need radiometrically comparable pixel values across frames or cameras.

```python
from pyhelios import RadiationModel, CameraProperties

props = CameraProperties()
props.exposure = "manual"   # disable per-frame auto-exposure scaling
radiation.addRadiationCamera("fixed_exposure_cam", ["red", "green", "blue"], position, lookat, props)
```

With `"auto"` exposure, an RGB camera meters its image the way a camera's meter does: after white balance and colour correction, it scales the image so that its **centre-weighted mean luminance** equals `CameraProperties.exposure_target`, as a fraction of full scale (default **0.235**). Each pixel's luminance is weighted by exp(-(dx² + dy²)), where dx and dy are the pixel's offsets from the image centre in units of 0.35 of the image width and height, so the middle of the image counts most. The rule and target were calibrated against the in-camera JPEGs of 413 camera models: a centre-weighted mean predicted the cameras' exposure with a spread of 0.57 stops, against 0.83 for the median. The target was fitted together with the [tone curve](#RadCameraToneCurve), so the two belong together. A scene darker or brighter than a typical photograph, such as a canopy viewed from above, may still call for a different target. `exposure_target` is ignored for `"manual"` and `"ISOXXX"` exposure and by cameras that are not RGB cameras, and a non-positive value is rejected. Note that sky pixels are metered too, so the sky affects the exposure of the rest of the image.

```python
props = CameraProperties(exposure="auto", exposure_target=0.15)   # darker target for a nadir canopy view
radiation.addRadiationCamera("nadir_cam", ["red", "green", "blue"], position, lookat, props)
```

> **Note:** `exposure_target` was added in helios-core 1.3.85. Until 1.3.96, auto exposure metered the **median** luminance with a default target of **0.18**, and was applied before white balance. Auto-exposed images change brightness with 1.3.96, and projects that set `exposure_target` for the old median rule need a new value.

Cameras that are not RGB cameras (e.g. multispectral or colour-infrared) normalize each band so that its 95th percentile of signal pixels is 0.7. [Thermal cameras](#RadThermalCamera) are not exposed.

### Camera Tone Curve {#RadCameraToneCurve}

Real cameras do not encode their images with the sRGB curve alone: before encoding, they apply a tone curve that darkens shadows and rolls off highlights, which gives their JPEGs their contrast. Without it, rendered images look flat and hazy. Since helios-core 1.3.96, with `CameraProperties.tone_curve="auto"` (the default), `writeCameraImage()` applies the typical in-camera tone curve to each channel of an RGB camera's image before sRGB encoding.

The curve was measured from the JPEGs of 413 camera models; the curves of Canon, Sony, Nikon, Panasonic, Fujifilm, Olympus and Pentax cameras agree within 2-5 levels out of 255, so one curve serves all of them. Compared with sRGB encoding alone, it gives shadows at a quarter of mid-grey 39 rather than 60 out of 255, leaves mid-grey almost unchanged (114 rather than 118), and compresses highlights instead of clipping them. Phone cameras were not included: they apply local tone mapping, which a single curve does not reproduce.

Only written images are tone mapped. The camera's pixel data (`getCameraPixelData()`) and the raw data written by `writeCameraImageDataEXR()` stay linear, and grayscale images and cameras that are not RGB cameras are never tone mapped. The camera's image metadata records the curve applied as `tone_curve` (`"typical camera"` or `"none"`). Set `tone_curve="off"` to encode images with the sRGB curve alone:

```python
props = CameraProperties(tone_curve="off")   # sRGB encoding only
```

### Thermal Cameras {#RadThermalCamera}

A thermal camera is a library camera of type "thermal", or (since helios-core 1.3.96) a camera added with `addRadiationCamera()` whose bands all have emission enabled and wavelength bounds starting at 3000 nm or above (e.g. 8000-14000 nm). With the default `"auto"` exposure its pixel data stay radiances, and it is not white balanced, colour corrected, tone mapped or sRGB encoded as an RGB camera is. (Previously such a camera's pixels were rescaled so that their 95th percentile was 0.7, so they no longer held radiances.) Emission is enabled by default and often left enabled in visible bands, so bands without wavelength bounds do not count: a camera imaging a band without bounds such as `"LW"`, or an emission band alongside other bands, is normalized like any other non-RGB camera unless its exposure is `"manual"`.

\ref pyhelios.RadiationModel.RadiationModel.getCameraPixelBrightnessTemperature "getCameraPixelBrightnessTemperature(camera_label, band_label)" (helios-core 1.3.96+) converts a thermal camera's pixels in an emission band to brightness temperatures (K), in the order of `getCameraPixelData()`: the temperature of a blackbody whose in-band radiance equals the pixel's. It is the surface temperature only for a surface of emissivity 1, and it includes the radiation the surface reflects (e.g. from the sky). A pixel of zero radiance gives 0 K. With a sensor atmosphere (`enableCameraAtmosphere()`, see [Simulating Satellite Imagery](#RadCameraAtmosphere)) the result is the brightness temperature above the atmosphere, weighted by the camera's spectral response. The pixels must be radiances: the camera's exposure must be `"manual"`, or `"auto"` for a thermal camera; any other camera with `"auto"` exposure, or one with `"ISOXXX"` exposure, is refused with `RadiationModelError`.

```python
from pyhelios import RadiationModel
from pyhelios.types import vec3

with RadiationModel(context) as radiation:
    radiation.addRadiationBand("TIR", 8000, 14000)
    radiation.setScatteringDepth("TIR", 0)       # surfaces at known temperatures; cameras image depth 0 too
    radiation.setDiffuseRadiationFlux("TIR", 0.0)
    radiation.addRadiationCamera("thermal_cam", ["TIR"], vec3(0, 0, 5), vec3(0, 0, 0))   # thermal: stays radiance
    radiation.runBand("TIR")

    T_b = radiation.getCameraPixelBrightnessTemperature("thermal_cam", "TIR")   # K, one per pixel
```

### Camera Image Corrections

Two methods post-process a rendered RGB camera image before it is written. Both change the camera's stored pixel data in place, so applying one twice applies it twice, and neither clamps values.

- `applyCameraColorCorrectionMatrix(camera_label, red, green, blue, ccm_file_path)` multiplies each pixel's `(r, g, b)` by a 3x3 matrix, or by a 3x3 matrix plus an offset column (`matrix_type="4x3"`), read from an XML file such as the one `autoCalibrateCameraImage(..., ccm_export_file_path=...)` exports. A missing file raises `FileNotFoundError`. Since helios-core 1.3.96 it raises an error for a camera whose current image was already colour corrected automatically; create such a camera with `CameraProperties(color_correction="off")` (see [Camera Colour Correction](#RadCameraColorCorrection)).
- `applyCameraImageCorrections(camera_label, red, green, blue, saturation_adjustment=1.0, brightness_adjustment=1.0, contrast_adjustment=1.0)` applies lens flare (if enabled for the camera), then brightness and contrast in linear space (`0.5 + (v * brightness - 0.5) * contrast`), then saturation about each pixel's luminance (0 gives grayscale). A factor of 1.0 skips its step. The factors are recorded in camera metadata when `enableCameraMetadata()` is on.

White balance, automatic colour correction and exposure are not part of these calls: they are applied during `runBand()` according to the camera's `white_balance`, `color_correction` and `exposure` `CameraProperties`. The tone curve and sRGB encoding are applied by `writeCameraImage()` when it writes a 3-band image (see [Camera Image Processing Pipeline](#RadCameraPipeline)). The full order is therefore:

```python
# "cam" was created with CameraProperties(color_correction="off") so that it can take its own matrix
radiation.runBand(["red", "green", "blue"])          # render; white balance and exposure applied here
radiation.applyCameraColorCorrectionMatrix("cam", "red", "green", "blue", "cam_ccm.xml")   # optional
radiation.applyCameraImageCorrections("cam", "red", "green", "blue",
                                      saturation_adjustment=1.5,
                                      brightness_adjustment=1.2,
                                      contrast_adjustment=1.1)
radiation.writeCameraImage("cam", ["red", "green", "blue"], "corrected")   # tone curve and sRGB encoding applied here
```

A CCM file has one `<row>` per line:

```xml
<helios>
  <ColorCorrectionMatrix camera_label="cam" matrix_type="3x3">
    <row>1.10 -0.05 0.02</row>
    <row>-0.03 1.08 0.01</row>
    <row>0.01 -0.04 1.12</row>
  </ColorCorrectionMatrix>
</helios>
```

### Auto-Calibrated Camera Images

Automatic color correction for realistic imagery:

```python
# Basic auto-calibration with default settings
filename = radiation.autoCalibrateCameraImage(
    camera_label="rgb_camera",
    red_band_label="Red",
    green_band_label="Green", 
    blue_band_label="Blue",
    output_file_path="auto_calibrated_image.jpg"
)

# Advanced auto-calibration with quality report
filename = radiation.autoCalibrateCameraImage(
    camera_label="multispectral_camera",
    red_band_label="Band_670nm",
    green_band_label="Band_550nm",
    blue_band_label="Band_450nm", 
    output_file_path="calibrated_multispectral.jpg",
    print_quality_report=True,
    algorithm="MATRIX_3X3_AUTO",  # or "DIAGONAL_ONLY", "MATRIX_3X3_FORCE"
    ccm_export_file_path="color_correction_matrix.txt"
)
print(f"Calibrated image saved to: {filename}")
```

`autoCalibrateCameraImage()` fits a colour correction matrix from the colour board patches in the camera's view: the matrix that best maps, in the weighted least-squares sense, the camera's mean linear RGB over each patch to the patch's reference colour, the colorimetric linear sRGB (CIE illuminant D65, CIE 1931 2-degree observer) of the reflectance spectrum the patch was rendered with. Neutral patches count double, and patches seen by 10 pixels or fewer are left out. The corrected image is written sRGB encoded (without the tone curve of `writeCameraImage()`), and the exported matrix maps linear camera RGB to linear sRGB, as `applyCameraColorCorrectionMatrix()` expects. If the camera's image was colour corrected automatically (`color_correction="auto"`), that correction is undone on a copy of the data before fitting, so the result is the same as for the same camera with `color_correction="off"`. With `"MATRIX_3X3_AUTO"`, a diagonal correction is fitted instead, with a warning, if the patches in view do not determine a stable 3x3 matrix. It raises an error if no patch is in view, or with `"MATRIX_3X3_FORCE"` if fewer than 6 patches of distinct colours are.

> **Note:** helios-core 1.3.96 fixed `autoCalibrateCameraImage()`, whose matrices were previously unusable: the third column of every fitted 3x3 matrix had the wrong signs (so `"MATRIX_3X3_AUTO"` always fell back to a diagonal correction), the fit mapped linear camera RGB onto gamma-encoded reference colours, the corrected image was written without sRGB encoding, and the Calibrite and SpyderCHECKR reference colours were assigned to the wrong patches. It also raised no error when no usable patches were in view, silently returning an identity or clamped matrix. Matrices exported by earlier versions should be regenerated.

### Color Correction Algorithms

Choose the appropriate algorithm based on your needs:

```python
algorithms = {
    "DIAGONAL_ONLY": "Simple white balance correction (fastest)",
    "MATRIX_3X3_AUTO": "Full 3x3 matrix with stability fallback (recommended)",
    "MATRIX_3X3_FORCE": "Force 3x3 matrix even if potentially unstable"
}

# Test different algorithms
for algorithm, description in algorithms.items():
    filename = radiation.autoCalibrateCameraImage(
        camera_label="test_camera",
        red_band_label="R", green_band_label="G", blue_band_label="B",
        output_file_path=f"calibrated_{algorithm.lower()}.jpg",
        algorithm=algorithm
    )
    print(f"{algorithm}: {description} -> {filename}")
```

### Complete Camera Pipeline Example

```python
from pyhelios import Context, WeberPennTree, WPTType, RadiationModel
from pyhelios import RadiationModelError
from pyhelios.types import *

# Create scene with labeled geometry
context = Context()

# Generate tree with data labels
wpt = WeberPennTree(context)
tree_id = wpt.buildTree(WPTType.APPLE)

# Label tree components for ML training
leaf_uuids = wpt.getLeafUUIDs(tree_id)
branch_uuids = wpt.getBranchUUIDs(tree_id)

for uuid in leaf_uuids:
    context.setPrimitiveDataString(uuid, "plant_part", "leaf")
    context.setPrimitiveDataString(uuid, "species", "apple")
    
for uuid in branch_uuids:
    context.setPrimitiveDataString(uuid, "plant_part", "branch") 
    context.setPrimitiveDataString(uuid, "species", "apple")

# Add ground with labels
ground = context.addPatch(center=vec3(0,0,0), size=vec2(10,10))
context.setPrimitiveDataString(ground, "plant_part", "soil")

# Run radiation simulation with cameras
try:
    with RadiationModel(context) as radiation:
        # Set up radiation bands
        radiation.addRadiationBand("Red")
        radiation.addRadiationBand("Green") 
        radiation.addRadiationBand("Blue")
        radiation.addRadiationBand("NIR")
        
        # Add sun source
        sun_id = radiation.addSunSphereRadiationSource(
            radius=0.5, zenith=45.0, azimuth=180.0)
        
        # Configure realistic solar spectrum
        radiation.setSourceFlux(sun_id, "Red", 250.0)
        radiation.setSourceFlux(sun_id, "Green", 350.0)
        radiation.setSourceFlux(sun_id, "Blue", 200.0)
        radiation.setSourceFlux(sun_id, "NIR", 400.0)
        
        # Add cameras BEFORE running: runBand() renders only the cameras that
        # already exist, and only the bands passed to it.
        radiation.addRadiationCamera(
            "overhead_rgb", ["Red", "Green", "Blue"],
            position=vec3(0, 0, 20),
            lookat_or_direction=vec3(0, 0, 0))
        radiation.addRadiationCamera(
            "side_view", ["NIR"],
            position=vec3(15, 0, 5),
            lookat_or_direction=vec3(0, 0, 5))

        # Run simulation
        radiation.updateGeometry()
        radiation.runBand(["Red", "Green", "Blue", "NIR"])
        
        # Generate camera images
        rgb_filename = radiation.writeCameraImage(
            camera="overhead_rgb",
            bands=["Red", "Green", "Blue"],
            imagefile_base="apple_tree_rgb"
        )
        
        nir_filename = radiation.writeCameraImage(
            camera="side_view", 
            bands=["NIR"],
            imagefile_base="apple_tree_nir"
        )
        
        # Generate training data for object detection
        radiation.writeImageBoundingBoxes(
            camera_label="overhead_rgb",
            primitive_data_labels=["leaf", "branch", "soil"],
            object_class_ids=[0, 1, 2],  # leaf=0, branch=1, soil=2
            image_file=rgb_filename,
            classes_txt_file="plant_classes.txt"
        )
        
        # Generate segmentation masks 
        radiation.writeImageSegmentationMasks(
            camera_label="overhead_rgb",
            primitive_data_labels=["leaf", "branch", "soil"],
            object_class_ids=[0, 1, 2],
            json_filename="apple_tree_segmentation.json",
            image_file=rgb_filename
        )
        
        # Create auto-calibrated realistic image
        calibrated_filename = radiation.autoCalibrateCameraImage(
            camera_label="overhead_rgb",
            red_band_label="Red",
            green_band_label="Green", 
            blue_band_label="Blue",
            output_file_path="apple_tree_calibrated.jpg",
            print_quality_report=True
        )
        
        print("Camera pipeline completed:")
        print(f"  RGB Image: {rgb_filename}")
        print(f"  NIR Image: {nir_filename}") 
        print(f"  Calibrated: {calibrated_filename}")
        print(f"  Training data: plant_classes.txt + YOLO format labels")
        print(f"  Segmentation: apple_tree_segmentation.json")
        
except RadiationModelError as e:
    print(f"Camera processing failed: {e}")
```

### Camera Function Error Handling

```python
try:
    # Camera functions with comprehensive error handling
    filename = radiation.writeCameraImage(
        camera="test_camera",
        bands=["R", "G", "B"],
        imagefile_base="test"
    )
    
except TypeError as e:
    print(f"Parameter error: {e}")
    # Handle invalid parameter types
    
except ValueError as e:
    print(f"Value error: {e}")  
    # Handle invalid parameter values (e.g., both primitive and object labels)
    
except RuntimeError as e:
    print(f"Camera operation failed: {e}")
    # Handle camera or image generation failures
```

## Error Handling

```python
from pyhelios import RadiationModel
from pyhelios.exceptions import HeliosGPUInitializationError

# Check GPU availability before creating RadiationModel
if not RadiationModel.probeAnyGPUBackend():
    print("No compatible GPU backend found")
    print("Supported backends: OptiX 8 (NVIDIA driver >= 560), OptiX 6 (NVIDIA driver < 560), Vulkan")

try:
    radiation = RadiationModel(context)
    print(f"Using backend: {radiation.getBackendName()}")

except Exception as e:
    print(f"RadiationModel initialization failed: {e}")

    # Runtime backend probing provides clear diagnostic messages
    if "Vulkan" in str(e):
        print("Vulkan backend error - check GPU drivers")
        print("  macOS: brew install vulkan-loader molten-vk")
        print("  Linux: sudo apt-get install libvulkan-dev")
        print("  Windows: No additional packages needed")
    elif "OptiX" in str(e):
        print("OptiX backend error - check CUDA/OptiX installation and NVIDIA drivers")
    elif "GPU" in str(e):
        print(f"GPU initialization failed: {e}")
```

## Build Requirements

```bash
# Build with radiation plugin
build_scripts/build_helios --plugins radiation

# Or use GPU profile
build_scripts/build_helios --plugins radiation

# Check if radiation is available
python -c "from pyhelios.plugins import get_plugin_registry; print(get_plugin_registry().is_plugin_available('radiation'))"
```