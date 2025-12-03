# LeafOptics Documentation {#LeafOpticsDoc}

## Overview

The LeafOptics plugin provides a Python interface to the PROSPECT leaf optical model for computing spectral reflectance and transmittance of plant leaves based on their biochemical properties.

**Key Features:**
- Computes spectral reflectance and transmittance from 400-2500 nm at 1 nm resolution (2101 data points)
- Supports both PROSPECT-D and PROSPECT-PRO model modes
- Built-in species library with 12 pre-fitted plant species from LOPEX93 dataset
- Integrates with Helios Context for geometry-based spectral assignment

## System Requirements

- **Platforms**: Windows, Linux, macOS
- **GPU**: Not required
- **Dependencies**: None (spectral data included)
- **Runtime Assets**: ~475KB XML spectral library file

## Installation

### Build with LeafOptics

```bash
# Build with LeafOptics plugin
build_scripts/build_helios --plugins leafoptics

# Build with related radiation plugins
build_scripts/build_helios --plugins leafoptics,radiation

# Interactive selection
build_scripts/build_helios --interactive

# Check if available
python -c "from pyhelios import LeafOptics; print('Available:', LeafOptics.isAvailable())"
```

## Quick Start

```python
from pyhelios import Context, LeafOptics, LeafOpticsProperties

# Create context and LeafOptics instance
with Context() as context:
    with LeafOptics(context) as leafoptics:
        # Get properties for a known species
        props = leafoptics.getPropertiesFromLibrary("sunflower")
        print(f"Sunflower chlorophyll: {props.chlorophyllcontent} ug/cm^2")

        # Compute spectral reflectance and transmittance
        wavelengths, reflectance, transmittance = leafoptics.getLeafSpectra(props)
        print(f"Spectral range: {wavelengths[0]}-{wavelengths[-1]} nm ({len(wavelengths)} points)")

        # Apply to geometry
        leaf_uuid = context.addPatch(center=[0, 0, 1], size=[0.1, 0.1])
        leafoptics.run([leaf_uuid], props, "sunflower_leaf")
```

## LeafOpticsProperties

The `LeafOpticsProperties` dataclass holds PROSPECT model parameters:

| Property | Default | Units | Description |
|----------|---------|-------|-------------|
| `numberlayers` | 1.5 | - | Number of mesophyll layers |
| `brownpigments` | 0.0 | - | Brown pigment content |
| `chlorophyllcontent` | 30.0 | ug/cm² | Chlorophyll a+b content |
| `carotenoidcontent` | 7.0 | ug/cm² | Carotenoid content |
| `anthocyancontent` | 1.0 | ug/cm² | Anthocyanin content |
| `watermass` | 0.015 | g/cm² | Equivalent water thickness |
| `drymass` | 0.09 | g/cm² | Dry matter content |
| `protein` | 0.0 | g/cm² | Protein content (PROSPECT-PRO) |
| `carbonconstituents` | 0.0 | g/cm² | Carbon constituents (PROSPECT-PRO) |

**Model Mode Selection:**
- If `protein > 0` OR `carbonconstituents > 0`: Uses PROSPECT-PRO mode
- Otherwise: Uses PROSPECT-D mode (default)

## Species Library

The plugin includes pre-fitted PROSPECT-D parameters for 12 plant species from the LOPEX93 dataset:

| Species Name | Common Name |
|--------------|-------------|
| `default` | Generic default values |
| `garden_lettuce` | Lettuce (Lactuca sativa) |
| `alfalfa` | Alfalfa (Medicago sativa) |
| `corn` | Corn/Maize (Zea mays) |
| `sunflower` | Sunflower (Helianthus annuus) |
| `english_walnut` | Walnut (Juglans regia) |
| `rice` | Rice (Oryza sativa) |
| `soybean` | Soybean (Glycine max) |
| `wine_grape` | Grape (Vitis vinifera) |
| `tomato` | Tomato (Lycopersicum esculentum) |
| `common_bean` | Bean (Phaseolus vulgaris) |
| `cowpea` | Cowpea (Vigna unguiculata) |

Species names are case-insensitive.

## Examples

### Using Species Library

```python
from pyhelios import Context, LeafOptics

with Context() as context:
    with LeafOptics(context) as leafoptics:
        # Get all available species
        species_list = LeafOptics.getAvailableSpecies()
        print(f"Available species: {species_list}")

        # Get properties for corn
        corn_props = leafoptics.getPropertiesFromLibrary("corn")
        print(f"Corn chlorophyll: {corn_props.chlorophyllcontent} ug/cm^2")
        print(f"Corn water mass: {corn_props.watermass} g/cm^2")
```

### Custom Leaf Properties

```python
from pyhelios import Context, LeafOptics, LeafOpticsProperties

with Context() as context:
    with LeafOptics(context) as leafoptics:
        # Create custom properties (e.g., stressed leaf)
        stressed_leaf = LeafOpticsProperties(
            numberlayers=2.0,
            chlorophyllcontent=15.0,  # Lower chlorophyll (stress)
            carotenoidcontent=12.0,   # Higher carotenoids
            anthocyancontent=8.0,     # Higher anthocyanin (stress indicator)
            watermass=0.008,          # Lower water (drought stress)
            drymass=0.10
        )

        # Compute spectra
        wavelengths, refl, trans = leafoptics.getLeafSpectra(stressed_leaf)

        # Find reflectance at key wavelengths
        idx_red = int(680 - 400)   # Red absorption by chlorophyll
        idx_nir = int(800 - 400)   # NIR plateau
        print(f"Red reflectance: {refl[idx_red]:.3f}")
        print(f"NIR reflectance: {refl[idx_nir]:.3f}")
```

### Assigning Spectra to Geometry

```python
from pyhelios import Context, LeafOptics

with Context() as context:
    # Create leaf geometry
    sunflower_leaves = [
        context.addPatch(center=[0, 0, 1 + i * 0.2], size=[0.15, 0.15])
        for i in range(5)
    ]

    with LeafOptics(context) as leafoptics:
        # Get sunflower properties
        props = leafoptics.getPropertiesFromLibrary("sunflower")

        # Assign spectra to all leaves
        leafoptics.run(sunflower_leaves, props, "sunflower")

        # This creates global data:
        # - "leaf_reflectivity_sunflower"
        # - "leaf_transmissivity_sunflower"
```

### Comparing Species Spectra

```python
from pyhelios import Context, LeafOptics
import matplotlib.pyplot as plt  # Optional for visualization

with Context() as context:
    with LeafOptics(context) as leafoptics:
        species_to_compare = ["corn", "soybean", "sunflower"]
        spectra = {}

        for species in species_to_compare:
            props = leafoptics.getPropertiesFromLibrary(species)
            wavelengths, refl, trans = leafoptics.getLeafSpectra(props)
            spectra[species] = (wavelengths, refl, trans)

        # Compare reflectance at 550 nm (green peak)
        idx_550 = int(550 - 400)
        for species, (wl, refl, trans) in spectra.items():
            print(f"{species}: R={refl[idx_550]:.3f}, T={trans[idx_550]:.3f}")
```

## Spectral Characteristics

The PROSPECT model produces realistic leaf spectra with these characteristic features:

- **Blue absorption** (400-500 nm): High absorption by chlorophyll and carotenoids
- **Green peak** (~550 nm): Reduced absorption creates "green" appearance
- **Red absorption** (600-700 nm): Strong chlorophyll absorption
- **Red edge** (680-750 nm): Rapid increase in reflectance at chlorophyll absorption edge
- **NIR plateau** (750-1300 nm): High reflectance/transmittance, low absorption
- **Water absorption bands**: Absorption features at 970, 1200, 1450, 1940 nm

## Troubleshooting

### Plugin Not Available

If you see "LeafOptics not available" errors:

1. Check plugin status:
   ```bash
   python -c "from pyhelios import LeafOptics; print('Available:', LeafOptics.isAvailable())"
   ```

2. Rebuild with plugin:
   ```bash
   build_scripts/build_helios --clean --plugins leafoptics
   ```

### Spectral Data Not Found

If you see errors about missing spectral data:

1. Verify assets were copied during build:
   ```bash
   ls -la pyhelios_build/build/plugins/leafoptics/spectral_data/
   ```

2. Rebuild with clean flag:
   ```bash
   build_scripts/build_helios --clean --plugins leafoptics
   ```

### Invalid Spectral Values

If computed spectra have unexpected values:

1. Check input property ranges - use values from species library as reference
2. Verify properties are physically realistic (positive values, reasonable ranges)
3. Check model mode - PROSPECT-PRO requires protein or carbonconstituents > 0

## Scientific Background

The LeafOptics plugin implements the PROSPECT model family:

- **PROSPECT-D** (Féret et al., 2017): Uses dry matter content for absorption
- **PROSPECT-PRO** (Féret et al., 2021): Separates protein and carbon constituents

The model computes bidirectional leaf reflectance and transmittance using:
1. Specific absorption coefficients for each biochemical constituent
2. Radiative transfer through layered leaf mesophyll structure
3. Fresnel reflectance at air-leaf interfaces

## References

- Jacquemoud, S., & Baret, F. (1990). PROSPECT: A model of leaf optical properties spectra. Remote sensing of environment, 34(2), 75-91.
- Féret, J. B., et al. (2017). PROSPECT-D: Towards modeling leaf optical properties through a complete lifecycle. Remote Sensing of Environment, 193, 204-215.
- Hosgood, B., et al. (1994). LOPEX93: Leaf Optical Properties EXperiment. EUR 16095 EN. JRC Report.
