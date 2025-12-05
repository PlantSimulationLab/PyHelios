# Boundary-Layer Conductance Model Plugin Documentation {#BoundaryLayerConductanceDoc}

[TOC]

<table>
<tr><th>Dependencies</th><td>None</td></tr>
<tr><th>Python Import</th><td>`from pyhelios import BoundaryLayerConductanceModel`</td></tr>
<tr><th>Main Class</th><td>\ref pyhelios.BoundaryLayerConductance.BoundaryLayerConductanceModel "BoundaryLayerConductanceModel"</td></tr>
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
from pyhelios import Context, BoundaryLayerConductanceModel
from pyhelios.types import vec3, vec2

with Context() as context:
    # Create leaf geometry
    leaf_uuid = context.addPatch(center=vec3(0, 0, 1), size=vec2(0.1, 0.1))

    # Set environmental conditions (optional - defaults used if not set)
    context.setPrimitiveData(leaf_uuid, "wind_speed", 2.0)  # m/s
    context.setPrimitiveData(leaf_uuid, "air_temperature", 298.0)  # K

    # Use boundary-layer conductance model
    with BoundaryLayerConductanceModel(context) as blc:
        # Set model for all primitives (default is Pohlhausen)
        blc.setBoundaryLayerModel("InclinedPlate")

        # Run calculation
        blc.run()

        # Get results
        gH = context.getPrimitiveData(leaf_uuid, "boundarylayer_conductance")
        print(f"Boundary-layer conductance: {gH[0]:.3f} mol air/m²-s")
```

## Known Issues {#BLCissues}

None.

## Introduction {#BLCIntro}

The boundary-layer conductance to heat describes the rate of energy transfer across the primitive boundary-layer for a given driving temperature difference. Currently, four different boundary-layer conductance models are available as part of this plug-in.

## BLConductanceModel Class Constructor {#BLCConstructor}

<table>
<tr><th>Constructors</th></tr>
<tr><td>\ref pyhelios.BoundaryLayerConductance.BoundaryLayerConductanceModel "BoundaryLayerConductanceModel"</td></tr>
</table>

The \ref pyhelios.BoundaryLayerConductance.BoundaryLayerConductanceModel "BoundaryLayerConductanceModel" class is initialized by passing the Helios context as an argument to the constructor.

## Input/Output Primitive Data {#BLCData}
 
### Input Primitive Data {#BLCInputData}

<table>
<tr><th>Primitive Data</th><th>Units</th><th>Data Type</th><th>Description</th><th>Available Plug-ins</th><th>Default Value</th></tr>
<tr><td>wind\_speed</td><td>m/s</td><td>\htmlonly<span style="font-family: Courier, monospace; color: green;">float</span>\endhtmlonly</td><td>Air wind speed just outside of primitive boundary-layer.</td><td>N/A</td><td>1 m/s</td></tr>
<tr><td>object\_length</td><td>m</td><td>\htmlonly<span style="font-family: Courier, monospace; color: green;">float</span>\endhtmlonly</td><td>Characteristic dimension of object formed by primitive.</td><td>N/A</td><td>Square root of primitive surface area</td></tr>
<tr><td>air\_temperature</td><td>Kelvin</td><td>\htmlonly<span style="font-family: Courier, monospace; color: green;">float</span>\endhtmlonly</td><td>Ambient air temperature outside of surface boundary layer.</td><td>N/A</td><td>290 K</td></tr>
<tr><td>surface\_temperature</td><td>Kelvin</td><td>\htmlonly<span style="font-family: Courier, monospace; color: green;">float</span>\endhtmlonly</td><td>Object surface temperature.</td><td>\ref pyhelios.EnergyBalance.EnergyBalanceModel "EnergyBalanceModel"</td><td>300 K</td></tr>
<tr><td>twosided\_flag</td><td>N/A</td><td>\htmlonly<span style="font-family: Courier, monospace; color: green;">uint</span>\endhtmlonly</td><td>Number of primitive faces with energy transfer (must be 1 or 2).</td><td>N/A</td><td>2</td></tr>
</table>

### Default Output Primitive Data {#BLOutputData}

<table>
<tr><th>Primitive Data</th><th>Units</th><th>Data Type</th><th>Description</th></tr>
<tr><td>boundarylayer\_conductance</td><td>mol air/m<sup>2</sup>-s</td><td>\htmlonly<span style="font-family: Courier, monospace; color: green;">float</span>\endhtmlonly</td><td>Primitive boundary-layer conductance calculated by this plug-in.</td></tr>
</table>

## Using the Boundary Layer Conductance Model Plug-in {#BLUse}

### Input Variables {#BLPrimData}

Inputs to the model are set by creating primitive variable data in the usual way. If a variable needed for a model input has not been create in the Context, the default value is assumed.

### Boundary-layer Conductance Models {#BLCModels}

There are four different built-in models for the boundary-layer conductance. The boundary-layer conductance model is set using the \ref pyhelios.BoundaryLayerConductance.BoundaryLayerConductanceModel::setBoundaryLayerModel "setBoundaryLayerModel()" function, which takes as arguments the UUID(s) of primitives for which the model is to be set, and a string referencing the chosen model. Possible models are summarized in the table below and described in further detail below. If the \ref pyhelios.BoundaryLayerConductance.BoundaryLayerConductanceModel::setBoundaryLayerModel "setBoundaryLayerModel()" is called for some UUIDs but not others, the plug-in will assume the default model (Pohlhausen) for any primitives for which no model was explicitly set.

It is also important to note that, by default, the length scale used to calculate the boundary-layer conductance is taken to be the square root of the primitive surface area. If the size of the object is different from the size of the primitive, then it is important to manually set the length scale to be the size of the object, as this is the relevant scale for boundary-layer development. This is usually necesary when using the boundary-layer conductance model for a sphere, for example.

The four available models are described in detail below:

<table>
<tr><th>Model</th><th>string argument</th></tr>
<tr><td>1. Pohlhausen Equation (default)</td><td>"Pohlhausen"</td></tr>
<tr><td>2. Inclined Plate</td><td>"InclinedPlate"</td></tr>
<tr><td>3. Laminar Sphere</td><td>"Sphere"</td></tr>
<tr><td>4. Ground Surface</td><td>"Ground"</td></tr>
</table>

#### 1. The Pohlhausen Equation (Laminar Flat Plate, Forced Convection) {#BLC1}

 The Pohlhausen equation is a classical similarity solution describing the boundary-layer conductance to heat for a flat plate parallel with the flow direction that is infinitely wide in the spanwise direction, and has finite length of \f$L\f$ in the streamwise direction. This model also assumes that the plate/primitive boundary-layer is laminar, and that convection is entirely forced (i.e., momentum forces dominate buoyancy forces). The boundary-layer conductance is calculated as

 \f$g_H = 0.135 n_s\sqrt{\frac{U}{L}}\f$,

 where \f$U\f$ is the wind speed just outside of the primitive boundary-layer, and \f$L\f$ is the characteristic length/dimension in the streamwise direction of the object that the primitive belongs to. For a leaf consisting of a single primitive, \f$L\f$ could be assumed to be the length of the primitive. If the primitive belongs to a Tile Compound Object, the plug-in will automatically use the dimension of the entire tile object and not that of a single patch/tile. Note that \f$g_H\f$ describes transfer from both sides of the plate/primitive, but transfer from each side of the plate/primitive is asymmetric because of buoyancy forces. \f$n_s\f$ is the number of primitive faces, which is determined by the value of primitive data "twosided_flag" (twosided\_flag=0 is single-sided and \f$n_s=1\f$, twosided\_flag=1 is two-sided and \f$n_s=2\f$).

#### 2. Laminar Inclined Plate, Mixed Free-Forced Convection {#BLC2}

 <a href="https://doi.org/10.1115/1.3247020">Chen et al. (1986)</a> provide a correlation for the boundary-layer conductance of a flat plate that is inclined with respect to the mean ambient flow direction. The correlation assumes that the plate is infinite in the spanwise direction, and has length \f$L\f$ in the other direction.

 The boundary-layer conductance for a plate inclined at \f$\theta_L\leq 75^\circ\f$ is given by

 \f$g_H(\theta_L)=\frac{\rho_a \nu}{Pr\,D_L}2F_1Re^{1/2}\left\{1\pm\left[\frac{2F_2\left(Gr\,\mathrm{cos}\,\theta_L/Re^2\right)^{1/4}}{3F_1}\right]^3\right\}^{1/3},\f$

and for \f$\theta_L>75^\circ\f$ as

\f$g_H(\theta_L)=\frac{\rho_a \nu}{Pr\,D_L}2F_1Re^{1/2}\left\{1\pm\left[\frac{F_3\left(Gr/Re^{5/2}\right)^{1/5}Gr^{C(\theta_L)}}{6\left[0.2+C(\theta_L)\right]F_1}\right]^3\right\}^{1/3},\f$

where \f$\rho_a\f$, \f$\nu\f$, and \f$Pr\f$ are respectively the molar density, kinematic viscosity, and Prandtl number of air, \f$L\f$ is the effective leaf dimension (<a href="https://doi.org/10.1115/1.3597463">Parkhurst 1968</a>), \f$Re\f$ is the Reynolds number based on \f$L\f$ and the local free-stream air velocity, and \f$Gr\f$ is the Grashof number which is defined here as

\f$Gr=\frac{g\beta\left(T_L-T_a\right)D_L^3}{\nu^2},\f$

where \f$g\f$ is the acceleration due to gravity, and \f$\beta\f$ is the volumetric thermal expansion coefficient which we approximate as the inverse of absolute ambient air temperature \f$1/T_a\f$ with \f$T_a\f$ in units of Kelvin. The plus and minus signs corresponds to buoyancy assisting flow and opposing flow cases, respectively. In the present model, the mean wind vector is always orthogonal to the gravity vector (transverse flow), and thus we always take the positive or buoyancy assisting flow case. The constants in the correlations are defined as

\f$F_1=0.399Pr^{1/3}\left[1+\left(0.0468/Pr\right)^{2/3}\right]^{-1/4},\f$

\f$F_2=0.75Pr^{1/2}\left[2.5\left(1+2Pr^{1/2}+2Pr\right)\right]^{-1/4},\f$

\f$F_3=Pr^{1/2}\left[0.25+1.6Pr^{1/2}\right]^{-1}\left(Pr/5\right)^{0.2+C(\theta_L)},\f$

\f$C(\theta_L)=0.070\left(\mathrm{cos}\,\theta_L\right)^{1/2}.\f$

Chen et al. (1986) mention that the equation for \f$\theta_L\leq 75^\circ\f$ is valid for \f$10^3\leq Re \leq 10^5\f$, and the equation for \f$\theta_L>75^\circ\f$ is valid for \f$10^3\leq GrPr \leq 10^9\f$.  We expect leaf Reynolds numbers somewhere between \f$5\times 10^3\f$ and \f$5\times 10^4\f$. Average \f$Gr Pr\f$ values are usually on the order of \f$10^6\f$. When \f$T_L \approx T_a\f$, it is possible for \f$Gr Pr\f$ to drop below \f$10^3\f$, however in these cases the net radiation is usually nearly zero and convective heat fluxes are low anyway.

#### 3. Laminar flow around a sphere {#BLC3}

 <a href="https://books.google.com/books?id=L5FnNlIaGfcC&dq=bird+lightfoot+Transport+Phenomena&lr=&source=gbs_navlinks_s">Bird et al. (1960)</a> provides correlation for forced convection heat transfer in laminar flow around a sphere

 \f$g_H = \frac{0.00164}{D} + 0.110\sqrt{\frac{U}{D}}\f$,

 where \f$D\f$ is the sphere diameter, and \f$U\f$ is the wind speed outside of the sphere boundary-layer.

#### 4. Flow over bare ground {#BLC4}

 <a href="https://doi.org/10.1016/S0168-1923(99)00005-2">Kustas and Norman (1999)</a> suggest a simple relationship for the convective heat conductance over flat, bare ground:

 \f$g_H = 0.166+0.5U,\f$

 where \f$U\f$ is the wind speed at a height above the soil surface where the effect of the soil surface roughness is minimal; typically 0.05 to 0.2 m.

### Setting the Boundary-layer Conductance Model To Be Used {#BLCSet}

```python
from pyhelios import Context, BoundaryLayerConductanceModel

# Declare the Context and add two primitives
with Context() as context:
    UUID0 = context.addPatch()
    UUID1 = context.addPatch()

    # Initialize the boundary-layer conductance Model
    with BoundaryLayerConductanceModel(context) as boundarylayerconductance:
        # This changes the boundary-layer conductance model for all (both) primitives
        boundarylayerconductance.setBoundaryLayerModel("InclinedPlate")

        # This changes the boundary-layer conductance model for the second primitive (while the first will keep the model set above)
        boundarylayerconductance.setBoundaryLayerModel("Ground", uuids=[UUID1])
```

### Running the Model {#BLCRun}

The model can be run to calculate the boundary-layer conductance for all primitives or a sub-set of primitives using the appropriate run function below.

<table>
<caption>Functions to perform boundary-layer conductance model calculations.</caption>
<tr><th>Model Run Function</th><th>Description</th></tr>
<tr><td>\ref pyhelios.BoundaryLayerConductance.BoundaryLayerConductanceModel::run "run()"</td><td>Run model calculations for all primitives in the Context.</td></tr>
<tr><td>\ref pyhelios.BoundaryLayerConductance.BoundaryLayerConductanceModel::run "run(uuids)"</td><td>Run model calculations for a select set of primitives in the Context, which are specified by a list of their UUIDs.</td></tr>
</table>
