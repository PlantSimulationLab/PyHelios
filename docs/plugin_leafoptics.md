# Leaf Optics Plugin Documentation {#LeafOpticsDoc}

[TOC]

<table>
<tr><th>Dependencies</th><td>None</td></tr>
<tr><th>Python Import</th><td>`from pyhelios import LeafOptics`</td></tr>
<tr><th>Main Class</th><td>\ref pyhelios.LeafOptics.LeafOptics "LeafOptics"</td></tr>
</table>

## System Requirements

<table>
  <tr>
    <th>Dependencies</th>
    <td>None</td>
  </tr>
  <tr>
    <th>Platforms</th>
    <td>Windows, Linux, macOS</td>
  </tr>
  <tr>
    <th>GPU</th>
    <td>Not required</td>
  </tr>
</table>

## Quick Start

```python
from pyhelios import Context, LeafOptics
from pyhelios.types import vec3, vec2

with Context() as context:
    # Create leaf geometry
    uuid = context.addPatch(center=vec3(0, 0, 1), size=vec2(0.1, 0.1))

    # Use LeafOptics plugin
    with LeafOptics(context) as leafoptics:
        # Get properties from species library
        props = leafoptics.getPropertiesFromLibrary("sunflower")

        # Compute spectra and assign to geometry
        leafoptics.run([uuid], props, "sunflower")

        # Retrieve computed spectra
        wavelengths, reflectance, transmittance = leafoptics.getLeafSpectra(props)
        print(f"Spectral range: {wavelengths[0]}-{wavelengths[-1]} nm ({len(wavelengths)} points)")
```

## Introduction {#LOIntro}

This plug-in computes leaf spectral reflectance and transmittance using the
PROSPECT family of models.  The implementation follows the <a href="https://doi.org/10.1016/j.rse.2017.08.004">PROSPECT--PRO</a>
formulation with eight absorbing constituents and a structural parameter
\f$N\f$ that represents the number of elementary layers in the leaf.  Output
spectra cover the range 400--2500&nbsp;nm in 1&nbsp;nm steps.

For each wavelength \f$\lambda\f$ the absorption coefficient of a single layer
is calculated as
\f[ k(\lambda)=\frac{C_{ab}a_{ab}(\lambda)+C_{ar}a_{ar}(\lambda)+C_{an}a_{an}(\lambda)+C_{br}a_{br}(\lambda)
+C_{w}a_{w}(\lambda)+C_{m}a_{m}(\lambda)+C_{p}a_{p}(\lambda)+C_{c}a_{c}(\lambda)}{N}, \f]
where the \f$C\f$ variables are the constituent masses per area and the
\f$a(\lambda)\f$ terms are the specific absorption coefficients loaded from the
internal spectral library.  Fresnel equations are used to compute surface
reflectance and a radiative transfer solution gives the total leaf
reflectance and transmittance.

## LeafOptics Class Constructor {#LOConstructor}

<table>
<tr><th>Constructors</th></tr>
<tr><td>\ref pyhelios.LeafOptics.LeafOptics "LeafOptics"</td></tr>
</table>

The constructor simply stores a pointer to the Helios context and loads the
spectral library data required by the model.

## LeafOpticsProperties Structure {#LOProps}

The \ref pyhelios.LeafOptics.LeafOpticsProperties "LeafOpticsProperties" structure stores the biochemical inputs to the
model.

<table>
 <tr><th>Member</th><th>Units</th><th>Description</th><th>Default Value</th></tr>
 <tr><td>numberlayers</td><td>unitless</td><td>Leaf structure parameter \f$N\f$</td><td>1.5</td></tr>
 <tr><td>brownpigments</td><td>unitless</td><td>Mass of brown pigments</td><td>0</td></tr>
 <tr><td>chlorophyllcontent</td><td>\f$\mu\f$g&nbsp;cm\f$^{-2}\f$</td><td>Total chlorophyll</td><td>30</td></tr>
 <tr><td>carotenoidcontent</td><td>\f$\mu\f$g&nbsp;cm\f$^{-2}\f$</td><td>Total carotenoids</td><td>7</td></tr>
 <tr><td>anthocyancontent</td><td>\f$\mu\f$g&nbsp;cm\f$^{-2}\f$</td><td>Anthocyanins</td><td>1</td></tr>
 <tr><td>watermass</td><td>g&nbsp;cm\f$^{-2}\f$</td><td>Equivalent water thickness</td><td>0.015</td></tr>
 <tr><td>drymass</td><td>g&nbsp;cm\f$^{-2}\f$</td><td>Dry matter mass</td><td>0.09</td></tr>
 <tr><td>protein</td><td>g&nbsp;cm\f$^{-2}\f$</td><td>Protein mass</td><td>0</td></tr>
 <tr><td>carbonconstituents</td><td>g&nbsp;cm\f$^{-2}\f$</td><td>Cellulose and other carbon compounds</td><td>0</td></tr>
 <tr><td>V2Z</td><td>unitless, [0,1]</td><td>Violaxanthin↔zeaxanthin de-epoxidation state. Used by the radiation plugin's solar-induced fluorescence (SIF) pipeline; ignored by PROSPECT.</td><td>0</td></tr>
 <tr><td>fqe</td><td>unitless</td><td>Intrinsic fluorescence quantum-efficiency scalar applied on top of the per-leaf Phi_F at SIF emission time. Ignored by PROSPECT.</td><td>1</td></tr>
</table>

> **SIF parameters (helios-core v1.3.72+):** `V2Z` and `fqe` are inert for the pure
> reflectance/transmittance calculation. They are written to `fluspect_biochem_<label>`
> global data on every `run()` so the radiation plugin's SIF camera can look them up
> per primitive when building Fluspect-B emission kernels.

## Integration with the Radiation SIF Pipeline {#LOSIFIntegration}

The radiation plugin includes a Fluspect-B / van der Tol pipeline for simulating solar-induced chlorophyll fluorescence (SIF) — see [SIF camera](plugin_radiation.md#sif-camera) in the radiation docs. LeafOptics is the canonical way to author the per-leaf biochemistry that pipeline needs.

### What LeafOptics Writes for SIF {#LOSIFData}

Every `run(uuids, props, label)` call emits one extra global-data entry and one extra primitive-data label, in addition to the reflectance and transmittance outputs:

| Output | Type | Description |
|---|---|---|
| Global data `fluspect_biochem_<label>` | `std::vector<float>` (11 elements) | Fluspect-B biochemistry vector in fixed field order: `[Cab, Cca, Cw, Cdm, Cs, Cant, Cp, Cbc, N, V2Z, fqe]`. |
| Primitive data `fluspect_spectrum` | `string` | Stamped on every UUID — value is `"fluspect_biochem_<label>"`. The radiation plugin reads this per primitive to identify fluorescing leaves; primitives without it are silently treated as non-fluorescing (stems, soil, etc.). |

The biochemistry vector is keyed by label, so leaves sharing a spectrum label share a single Fluspect-B kernel in the radiation plugin's per-label kernel cache. This is automatic — no extra API to enable.

### Field Mapping (LeafOpticsProperties → Fluspect-B) {#LOSIFFields}

| `LeafOpticsProperties` Member | Fluspect-B Field | Notes |
|---|---|---|
| `chlorophyllcontent` | C<sub>ab</sub> | Drives the dominant red-edge absorption that emits at 685 nm. |
| `carotenoidcontent` | C<sub>ca</sub> | Combined with V2Z controls absorption in the 400–550 nm excitation range. |
| `watermass` | C<sub>w</sub> | Equivalent water thickness (cm). |
| `drymass` | C<sub>dm</sub> | PROSPECT-D dry matter (g/cm²). Set to 0 in PROSPECT-PRO mode. |
| `brownpigments` | C<sub>s</sub> | Senescence/brown-pigment content. |
| `anthocyancontent` | C<sub>ant</sub> | |
| `protein` | C<sub>p</sub> | PROSPECT-PRO only. |
| `carbonconstituents` | C<sub>bc</sub> | PROSPECT-PRO only. |
| `numberlayers` | N | Mesophyll layer parameter. |
| `V2Z` | V2Z | SIF-only field; ignored by PROSPECT. |
| `fqe` | f<sub>qe</sub> | SIF-only field; ignored by PROSPECT. |

### Minimal SIF Wiring Example {#LOSIFExample}

```python
from pyhelios import Context, LeafOptics
from pyhelios.LeafOptics import LeafOpticsProperties
from pyhelios.types import vec3, vec2

with Context() as context:
    leaf_uuids = [context.addPatch(center=vec3(0, 0, 1), size=vec2(0.1, 0.1))]
    with LeafOptics(context) as leafoptics:
        props = LeafOpticsProperties()
        props.chlorophyllcontent = 40.0   # Cab, ug/cm^2
        props.carotenoidcontent  = 10.0   # Cca, ug/cm^2
        props.numberlayers       = 1.5
        props.watermass          = 0.009  # cm
        props.drymass            = 0.012  # g/cm^2
        props.V2Z                = 0.0    # dark-adapted; SIF-only
        props.fqe                = 1.0    # no calibration scalar; SIF-only
        leafoptics.run(leaf_uuids, props, "myleaf")

# Now the radiation plugin's SIF pipeline can find every leaf in leaf_uuids via the
# "fluspect_spectrum" primitive data and look up its biochemistry from the
# "fluspect_biochem_myleaf" global data — no further wiring required.
```

> **Note:** the reverse path `getPropertiesFromSpectrum()` does not currently populate `V2Z` or `fqe` as primitive data — those fields are SIF-only and are read by the radiation plugin directly from the `fluspect_biochem_*` global-data vector.

## Using the LeafOptics Plug-in {#LOUse}

The model can be run to produce global spectra and, optionally, assign those
spectra and optical properties to a set of primitives.

```python
from pyhelios import Context, LeafOptics
from pyhelios.LeafOptics import LeafOpticsProperties
from pyhelios.types import vec3, vec2

with Context() as context:
    with LeafOptics(context) as leafoptics:
        # Set custom properties
        props = LeafOpticsProperties()
        props.chlorophyllcontent = 40.0
        props.watermass = 0.02

        # Create leaf geometry
        leafIDs = [context.addPatch(center=vec3(0, 0, 1), size=vec2(0.1, 0.1))]

        # Run the model
        leafoptics.run(leafIDs, props, "example")
```

This command creates global data labeled
"leaf_reflectivity_example" and "leaf_transmissivity_example" containing the
computed spectra.  The spectra labels are also stored as primitive data for the
specified UUIDs together with the biochemical property values.

## Using the Built-in Species Library {#LOLibrary}

The LeafOptics class includes a built-in species library that provides pre-configured optical properties for common plant species. This simplifies model usage by eliminating the need to manually specify biochemical parameters.

### Basic Usage {#LOLibraryBasic}

Use the \ref pyhelios.LeafOptics.LeafOptics::getPropertiesFromLibrary "getPropertiesFromLibrary()" method to return a \ref pyhelios.LeafOptics.LeafOpticsProperties "LeafOpticsProperties" structure with species-specific values:

```python
from pyhelios import Context, LeafOptics
from pyhelios.types import vec3, vec2

with Context() as context:
    with LeafOptics(context) as leafoptics:
        # Get properties from library
        props = leafoptics.getPropertiesFromLibrary("default")

        # Create leaf geometry
        leafIDs = [context.addPatch(center=vec3(0, 0, 1), size=vec2(0.1, 0.1))]

        # Run the model
        leafoptics.run(leafIDs, props, "example")
```

The method returns a \ref pyhelios.LeafOptics.LeafOpticsProperties "LeafOpticsProperties" structure with the nine PROSPECT biochemistry parameters populated (numberlayers, chlorophyllcontent, carotenoidcontent, anthocyancontent, brownpigments, watermass, drymass, protein, carbonconstituents). The optional Fluspect-B SIF fields (`V2Z`, `fqe`) keep their dataclass defaults (0.0 and 1.0); set them on the returned object if you intend to use the radiation plugin's SIF camera.

### Available Species {#LOLibrarySpecies}

The library contains PROSPECT-D parameters fitted to LOPEX93 spectral library samples using the `fit_prospect_visrobust.py` script with robust optimization. All species use PROSPECT-D mode (drymass > 0, protein = 0, carbonconstituents = 0).

<table>
 <tr><th>Species Label</th><th>Scientific Name</th><th>N</th><th>Cab<br>(µg/cm²)</th><th>Car<br>(µg/cm²)</th><th>Ant<br>(µg/cm²)</th><th>Cbrown</th><th>Cw<br>(g/cm²)</th><th>Cm<br>(g/cm²)</th><th>R²</th><th>Source</th></tr>
 <tr><td>"default"</td><td>-</td><td>1.50</td><td>30.0</td><td>7.00</td><td>1.00</td><td>0.000</td><td>0.0150</td><td>0.0900</td><td>-</td><td>Original Helios defaults</td></tr>
 <tr><td>"garden_lettuce"</td><td><i>Lactuca sativa</i> L.</td><td>2.01</td><td>30.3</td><td>6.99</td><td>1.36</td><td>0.107</td><td>0.0282</td><td>0.0053</td><td>0.993</td><td>LOPEX93 sample 0021</td></tr>
 <tr><td>"alfalfa"</td><td><i>Medicago sativa</i> L.</td><td>2.01</td><td>43.6</td><td>10.3</td><td>1.34</td><td>0.000</td><td>0.0190</td><td>0.0047</td><td>0.994</td><td>LOPEX93 sample 0036</td></tr>
 <tr><td>"corn"</td><td><i>Zea mays</i> L.</td><td>1.59</td><td>22.9</td><td>3.97</td><td>0.00</td><td>0.727</td><td>0.0150</td><td>0.0044</td><td>0.975</td><td>LOPEX93 sample 0041</td></tr>
 <tr><td>"sunflower"</td><td><i>Helianthus annuus</i> L.</td><td>1.76</td><td>54.1</td><td>12.9</td><td>1.75</td><td>0.011</td><td>0.0186</td><td>0.0064</td><td>0.995</td><td>LOPEX93 sample 0081</td></tr>
 <tr><td>"english_walnut"</td><td><i>Juglans regia</i> L.</td><td>1.56</td><td>55.9</td><td>12.5</td><td>1.74</td><td>0.000</td><td>0.0128</td><td>0.0058</td><td>0.994</td><td>LOPEX93 sample 0091</td></tr>
 <tr><td>"rice"</td><td><i>Oryza sativa</i> L.</td><td>1.67</td><td>37.2</td><td>10.0</td><td>0.00</td><td>0.028</td><td>0.0101</td><td>0.0048</td><td>0.998</td><td>LOPEX93 sample 0106</td></tr>
 <tr><td>"soybean"</td><td><i>Glycine max</i> L.</td><td>1.54</td><td>46.4</td><td>12.1</td><td>0.65</td><td>0.000</td><td>0.0101</td><td>0.0029</td><td>0.997</td><td>LOPEX93 sample 0116</td></tr>
 <tr><td>"wine_grape"</td><td><i>Vitis vinifera</i> L.</td><td>1.43</td><td>50.9</td><td>12.5</td><td>1.44</td><td>0.080</td><td>0.0109</td><td>0.0060</td><td>0.997</td><td>LOPEX93 sample 0276</td></tr>
 <tr><td>"tomato"</td><td><i>Lycopersicum esculentum</i></td><td>1.40</td><td>48.3</td><td>11.6</td><td>1.45</td><td>0.000</td><td>0.0156</td><td>0.0026</td><td>0.997</td><td>LOPEX93 sample 0316</td></tr>
</table>

**Notes:**
- Species names are case-insensitive (e.g., "corn" and "CORN" are equivalent).
- R² values computed as 1 - (RMSE² / variance), indicating goodness-of-fit to measured spectra.
- All parameters were fitted without affine calibration using visible-robust optimization.
- LOPEX93 dataset: Hosgood B. et al. (1994), Leaf Optical Properties Experiment 93 (LOPEX93), EUR 16095 EN.

### Error Handling {#LOLibraryError}

If an unknown species name is provided, the method:
1. Issues a warning message (if messages are enabled)
2. Populates the properties structure with default values
3. Does not throw an error

This ensures that code continues to run even if a species name is misspelled or not yet in the library.

### Extending the Species Library {#LOLibraryExtend}

To add new species to the library, edit the species library data in the Helios C++ source code at `plugins/leafoptics/src/LeafOptics.cpp`. The library supports both PROSPECT-D mode (using drymass) and PROSPECT-PRO mode (using protein and carbonconstituents). Contact the PyHelios developers to request new species additions.

## Retrieving PROSPECT Parameters from Spectra {#LORetrieve}

The LeafOptics class maintains an internal mapping between spectrum labels and the PROSPECT parameters used to generate them. This allows users to retrieve the original model parameters from primitives that have been assigned LeafOptics-generated spectra.

### Basic Usage {#LORetrieveBasic}

The \ref pyhelios.LeafOptics.LeafOptics::getPropertiesFromSpectrum "getPropertiesFromSpectrum()" method queries primitives for their "reflectivity_spectrum" primitive data and, if it matches a spectrum generated by the LeafOptics instance, assigns the corresponding PROSPECT parameters as primitive data:

```python
from pyhelios import Context, LeafOptics
from pyhelios.LeafOptics import LeafOpticsProperties
from pyhelios.types import vec3, vec2

with Context() as context:
    with LeafOptics(context) as leafoptics:
        # Generate spectra for different leaf types
        healthy_leaf = LeafOpticsProperties()
        healthy_leaf.chlorophyllcontent = 45.0
        healthy_leaf.carotenoidcontent = 12.0

        stressed_leaf = LeafOpticsProperties()
        stressed_leaf.chlorophyllcontent = 20.0
        stressed_leaf.brownpigments = 0.3

        # Create primitives
        healthy_IDs = [context.addPatch(center=vec3(0, 0, 1), size=vec2(0.1, 0.1))]
        stressed_IDs = [context.addPatch(center=vec3(0, 0, 2), size=vec2(0.1, 0.1))]

        # Run model for each leaf type
        leafoptics.run(healthy_IDs, healthy_leaf, "healthy")
        leafoptics.run(stressed_IDs, stressed_leaf, "stressed")

        # Later, retrieve parameters from primitives based on their assigned spectra
        all_leaves = healthy_IDs + stressed_IDs
        leafoptics.getPropertiesFromSpectrum(all_leaves)

        # Each primitive now has parameter data matching its assigned spectrum
        chl = context.getPrimitiveData(healthy_IDs[0], "chlorophyll")
        # chl[0] = 45.0 (from healthy_leaf parameters)

        chl = context.getPrimitiveData(stressed_IDs[0], "chlorophyll")
        # chl[0] = 20.0 (from stressed_leaf parameters)
```

### Method Behavior {#LORetrieveBehavior}

For each UUID passed to \ref pyhelios.LeafOptics.LeafOptics::getPropertiesFromSpectrum "getPropertiesFromSpectrum()":

1. The method queries the primitive data "reflectivity_spectrum"
2. If the spectrum label starts with "leaf_reflectivity_", it extracts the user-provided label
3. If that label matches a spectrum generated by this LeafOptics instance, the corresponding parameters are assigned as primitive data
4. Primitives without matching spectra are silently skipped (no error is thrown)

### Assigned Primitive Data Labels {#LORetrieveLabels}

The method assigns primitive data using the same labels as \ref pyhelios.LeafOptics.LeafOptics::setProperties "setProperties()":

<table>
 <tr><th>Primitive Data Label</th><th>Parameter</th><th>Condition</th></tr>
 <tr><td>"chlorophyll"</td><td>chlorophyllcontent</td><td>Always</td></tr>
 <tr><td>"carotenoid"</td><td>carotenoidcontent</td><td>Always</td></tr>
 <tr><td>"anthocyanin"</td><td>anthocyancontent</td><td>Always</td></tr>
 <tr><td>"brown"</td><td>brownpigments</td><td>If brownpigments > 0</td></tr>
 <tr><td>"water"</td><td>watermass</td><td>Always</td></tr>
 <tr><td>"drymass"</td><td>drymass</td><td>If drymass > 0 (PROSPECT-D mode)</td></tr>
 <tr><td>"protein"</td><td>protein</td><td>If drymass = 0 (PROSPECT-PRO mode)</td></tr>
 <tr><td>"cellulose"</td><td>carbonconstituents</td><td>If drymass = 0 (PROSPECT-PRO mode)</td></tr>
</table>

### Important Notes {#LORetrieveNotes}

- The parameter mapping is stored per LeafOptics instance. If you create a new LeafOptics object, it will not have access to spectra generated by a previous instance.
- Only spectra generated using the \ref pyhelios.LeafOptics.LeafOptics::run "run()" methods are tracked. Manually created global data with "leaf_reflectivity_" prefixes will not match.
- The method always overwrites existing primitive data for the parameters listed above.
- Both overloads are available: pass a list of UUIDs for multiple primitives or a single UUID for one primitive.

## Optional Output Primitive Data {#LOOptionalOutput}

By default, the LeafOptics plug-in writes all leaf constituent concentrations to primitive data. To selectively output only specific properties for improved performance, call \ref pyhelios.LeafOptics.LeafOptics::optionalOutputPrimitiveData "optionalOutputPrimitiveData()" with the desired labels before calling run().

```python
from pyhelios import Context, LeafOptics
from pyhelios.LeafOptics import LeafOpticsProperties
from pyhelios.types import vec3, vec2

with Context() as context:
    with LeafOptics(context) as leafoptics:
        # Enable selective output for better performance
        leafoptics.optionalOutputPrimitiveData("chlorophyll")
        leafoptics.optionalOutputPrimitiveData("carotenoid")

        # Run model
        props = LeafOpticsProperties()
        leafIDs = [context.addPatch(center=vec3(0, 0, 1), size=vec2(0.1, 0.1))]
        leafoptics.run(leafIDs, props, "example")
```

<table>
 <tr>
    <th>Primitive Data Label</th>
    <th>Units</th>
    <th>Data Type</th>
    <th>Description</th>
 </tr>
 <tr>
    <td>chlorophyll</td>
    <td>\f$\mu\f$g cm\f$^{-2}\f$</td>
    <td><span style="font-family: Courier, monospace; color: green;">float</span></td>
    <td>Total chlorophyll content</td>
 </tr>
 <tr>
    <td>carotenoid</td>
    <td>\f$\mu\f$g cm\f$^{-2}\f$</td>
    <td><span style="font-family: Courier, monospace; color: green;">float</span></td>
    <td>Total carotenoid content</td>
 </tr>
 <tr>
    <td>anthocyanin</td>
    <td>\f$\mu\f$g cm\f$^{-2}\f$</td>
    <td><span style="font-family: Courier, monospace; color: green;">float</span></td>
    <td>Anthocyanin content</td>
 </tr>
 <tr>
    <td>brown</td>
    <td>unitless</td>
    <td><span style="font-family: Courier, monospace; color: green;">float</span></td>
    <td>Brown pigment content (only written if value > 0)</td>
 </tr>
 <tr>
    <td>water</td>
    <td>g cm\f$^{-2}\f$</td>
    <td><span style="font-family: Courier, monospace; color: green;">float</span></td>
    <td>Equivalent water thickness</td>
 </tr>
 <tr>
    <td>drymass</td>
    <td>g cm\f$^{-2}\f$</td>
    <td><span style="font-family: Courier, monospace; color: green;">float</span></td>
    <td>Dry matter mass (PROSPECT-D mode only, when drymass > 0)</td>
 </tr>
 <tr>
    <td>protein</td>
    <td>g cm\f$^{-2}\f$</td>
    <td><span style="font-family: Courier, monospace; color: green;">float</span></td>
    <td>Protein mass (PROSPECT-PRO mode only, when drymass = 0)</td>
 </tr>
 <tr>
    <td>cellulose</td>
    <td>g cm\f$^{-2}\f$</td>
    <td><span style="font-family: Courier, monospace; color: green;">float</span></td>
    <td>Cellulose and carbon compounds (PROSPECT-PRO mode only, when drymass = 0)</td>
 </tr>
</table>

*/