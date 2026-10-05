# Solar Position Plugin Documentation {#SolarPositionDoc}

[TOC]

<table>
<tr><th>Dependencies</th><td>None</td></tr>
<tr><th>Python Import</th><td>`from pyhelios import SolarPosition`</td></tr>
<tr><th>Main Class</th><td>\ref pyhelios.SolarPosition.SolarPosition "SolarPosition"</td></tr>
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
from pyhelios import Context, SolarPosition
from pyhelios.types import *

with Context() as context:
    # Set date and time
    context.setDate(2015, 5, 1)  # May 1, 2015
    context.setTime(12, 30)      # 12:30

    # Create SolarPosition. The Context is always the FIRST argument, followed
    # by UTC offset, latitude, and longitude.
    with SolarPosition(context, 7, 31.256, 119.947) as sun:
        # Get sun direction
        direction = sun.getSunDirectionVector()
        elevation = sun.getSunElevation()
        azimuth = sun.getSunAzimuth()

        print(f"Sun direction: {direction}")
        print(f"Elevation: {elevation} radians")
        print(f"Azimuth: {azimuth} radians")

        # Calculate solar flux with atmospheric conditions
        sun.setAtmosphericConditions(101000, 300, 0.6, 0.05)
        flux = sun.getSolarFlux()
        diffuse_fraction = sun.getDiffuseFraction()

        print(f"Solar flux: {flux} W/m²")
        print(f"Diffuse fraction: {diffuse_fraction}")
```

## Introduction {#SolarIntro}

This plugin calculates the position of the sun, and also implements other models for solar fluxes as well as longwave fluxes from the sky. Model theory and equations are given in the sections below.

## Class Constructor {#SolarConstructor}

 <table>
 <tr><th>Constructors</th></tr>
 <tr><td>\ref pyhelios.SolarPosition.SolarPosition "SolarPosition(context)"</td></tr>
 <tr><td>\ref pyhelios.SolarPosition.SolarPosition "SolarPosition(context, utc_offset, latitude, longitude)"</td></tr>
 </table>

 The \ref pyhelios.SolarPosition.SolarPosition "SolarPosition" class can be initialized by simply passing a Helios context as an argument to the constructor. This gives the class access to the time and date currently set in the Context. The model must also know certain parameters about the simulated location, in particular the offset from UTC time, latitude, and longitude. A description of these parameters are given in the table below. These can be supplied using the second constructor listed in the table above. If only the Context is supplied to the constructor, the plugin uses the Context's currently configured location.

 The Context's location can be set ahead of time with `context.setLocation(latitude, longitude, utc_offset)` or with the immutable `Location` dataclass from `pyhelios.types`. See [Geographic Location](user_guide.html#Location) in the user guide for details. With this approach, location is configured once and shared across plugins:

 ```python
 from pyhelios import Context, SolarPosition

 context = Context()
 context.setLocation(38.55, 121.76, 8.0)   # latitude, longitude, UTC offset
 solar = SolarPosition(context)            # picks up the Context location
 ```

 <table>
 <caption>SolarPosition constructor inputs</caption>
 <tr><th>Input Parameter</th><th>Description</th><th>Convention</th><th>Default Behavior</th></tr>
 <tr><td>UTC</td><td>Difference in hours between Coordinated Universal Time (UTC) for a particular location.  See the figure below to determine a particular UTC offset.</td><td>UTC offset value is positive moving West.</td><td>+8:00</td></tr>
 <tr><td>latitude</td><td>Geographic coordinate that specifies the north–south position of a point on the Earth's surface in degrees.</td><td>Latitude is positive in the northern hemisphere.</td><td>+38.55</td></tr>
 <tr><td>longitude</td><td>Geographic coordinate that specifies the east-west position of a point on the Earth's surface in degrees.</td><td>Longitude is positive in the western hemisphere.</td><td>+121.76</td></tr>
 </table>

 \image html "images/1200px-Standard_World_Time_Zones.png"

## Model Theory {#SolarTheory}

### Position of the Sun {#SolarPosTheory}

 The solar position model was implemented following the description in <a href="https://www.sciencedirect.com/science/article/pii/B9780123737502500069">Chapter 1 of Iqbal (1983)</a>.

 The day angle \f$\Gamma\f$ given as the polar angle of the earth relative to the sun (\f$\Gamma=0\f$ on Jan. 1) is calculated as

 <center>
 \f$\Gamma = 2\pi(DOY-1)/365\f$,  (1)
 </center>

 where DOY is the <a href="https://en.wikipedia.org/wiki/Julian_day">Julian Day</a> of the year.

 The solar declination angle is then calculated as

 <center>
 \f$\delta = 0.006918 - 0.399912\,\mathrm{cos}(\Gamma) + 0.070257\,\mathrm{sin}(\Gamma)- 0.006758\,\mathrm{cos}(2\Gamma) + 0.000907\,\mathrm{sin}(2\Gamma) - 0.002697\,\mathrm{cos}(3\Gamma) + 0.00148\,\mathrm{sin}(3\Gamma)\f$.         (2)
 </center>

 The <a href="https://en.wikipedia.org/wiki/Equation_of_time">equation of time</a> is calculated as
 
 <center>
 \f$EoT = 229.18(0.000075 + 0.001868\,\mathrm{cos}(\Gamma) - 0.032077\,\mathrm{sin}(\Gamma) - 0.014615\,\mathrm{cos}(2\Gamma) - 0.04089\,\mathrm{sin}(2\Gamma))\f$,         (3)
 </center>

 The hour angle is given by
 
 <center>
 \f$h=15(LST-12)\f$,         (4)
 </center>

 with

 <center>
   \f$LST=hour+minute/60+TC/60\f$,          (5)
 </center>

 and

 <center>
   \f$TC=4(15UTC-longitude)+EoT\f$,         (6)
 </center>

 Finally, the solar elevation angle is given by

 <center>
 \f$\theta_s=\mathrm{sin}^{-1}( \mathrm{sin}(latitude)\mathrm{sin}(\delta) + \mathrm{cos}(latitude)\mathrm{cos}(\delta)\mathrm{cos}(h) )\f$,         (7)
 </center>

 and the solar azimuthal angle is given by

 <center>
 \f$\phi_s=\mathrm{cos}^{-1}( (\mathrm{sin}(\delta) - \mathrm{sin}(\theta_s)\mathrm{sin}(latitude))/(\mathrm{cos}(\theta)\mathrm{cos}(latitude)))\f$.         (8)
 </center>

 Note that \f$\mathrm{cos}^{-1}\f$ gives angles between 0 and \f$\pi\f$, so to get a \f$\phi_s\f$ between 0 and \f$2\pi\f$, we take \f$\phi_s=2\pi-\phi_s\f$ if \f$LST>12\f$.

### Direct and Diffuse Solar Flux (REST-2 Model) {#SolarFluxTheory}

 Clear-sky solar fluxes are calculated using the 'REST-2' (Reference Evaluation of Solar Transmittance, 2 bands) model of <a href="https://www.sciencedirect.com/science/article/pii/S0038092X07000990">Gueymard (2008)</a>. REST-2 is a high-performance broadband radiative transfer model derived from parameterizations of the SMARTS spectral code, and is widely recognized as one of the most accurate clear-sky models available.

 The model uses a two-band spectral scheme that separately treats the visible band (290-700 nm) and near-infrared band (700-4000 nm). In the visible band, attenuation is dominated by Rayleigh scattering and aerosol extinction, while the NIR band is primarily affected by water vapor absorption. For each band, the model calculates independent broadband transmittances for:

 - <b>Rayleigh scattering</b>: Molecular scattering by air molecules
 - <b>Uniformly mixed gases</b>: Absorption by CO<sub>2</sub> and O<sub>2</sub>
 - <b>Ozone</b>: UV and visible absorption bands
 - <b>Water vapor</b>: Major absorption in the NIR
 - <b>Aerosols</b>: Scattering and absorption characterized by Ångström turbidity coefficients

 Direct beam irradiance is computed from the product of these transmittances, while diffuse irradiance uses a two-layer scattering scheme that accounts for aerosol forward scattering and backscattering from the atmosphere-ground system. The model partitions the total radiative flux into direct and diffuse components suitable for agricultural, solar energy, and climate applications.

### Spectral Solar Irradiance (Model Based on SSolar-GOA) {#SpectralIrradianceTheory}

 For applications requiring high spectral resolution (e.g., photosynthesis, remote sensing), \ref pyhelios.SolarPosition.SolarPosition::calculateDirectSolarSpectrum "calculateDirectSolarSpectrum()", \ref pyhelios.SolarPosition.SolarPosition::calculateDiffuseSolarSpectrum "calculateDiffuseSolarSpectrum()" and \ref pyhelios.SolarPosition.SolarPosition::calculateGlobalSolarSpectrum "calculateGlobalSolarSpectrum()" compute the direct normal, diffuse horizontal and global horizontal spectral irradiance at the ground from 300 to 2600 nm at 1 nm resolution. The model follows the structure of SSolar-GOA (<a href="https://doi.org/10.5194/gmd-15-1689-2022">Cachorro et al. 2022</a>): the atmosphere is a single homogeneous layer of molecules and aerosol whose scattering transmittance is given by an analytical two-stream solution, gas absorption multiplies it, and multiple reflection between the ground and the atmosphere is included through the atmosphere's spherical albedo.

 - <b>Extraterrestrial spectrum</b>: the 1985 Wehrli standard spectrum, averaged over 1 nm bins and scaled for the Earth-Sun distance
 - <b>Air mass</b>: the relative optical air mass of Kasten and Young (1989)
 - <b>Rayleigh scattering and aerosol extinction</b>: a single mixed layer, with the aerosol optical depth from the Ångström law (exponent 1.3) and the single-scattering albedo (0.893) and asymmetry parameter (0.634) of the 6S continental aerosol at 550 nm
 - <b>Gas absorption</b>: transmittance tables computed with the 6S radiative transfer code for water vapor, ozone and the uniformly mixed gases (oxygen, carbon dioxide, methane, nitrous oxide and carbon monoxide)
 - <b>Ground-atmosphere multiple reflection</b>: from the ground albedo (see \ref pyhelios.SolarPosition.SolarPosition::setGroundAlbedo "setGroundAlbedo()") and the atmospheric spherical albedo

 <b>Parameter Derivation:</b> The model uses the same atmospheric inputs as the REST-2 model (pressure, temperature, humidity, turbidity). The precipitable water is derived from the air temperature and relative humidity, which must therefore be greater than zero. The total column ozone comes from \ref pyhelios.SolarPosition.SolarPosition::getOzoneColumn "getOzoneColumn()" (see \ref OzoneColumn) and the ground albedo from \ref pyhelios.SolarPosition.SolarPosition::setGroundAlbedo "setGroundAlbedo()" (default 0.2).

 <b>Output Format:</b> Results are stored in Context global data as vectors of (wavelength, irradiance) pairs with user-defined labels. Three spectral components are computed: global irradiance on horizontal surface, direct irradiance normal to sun direction, and diffuse irradiance on horizontal surface (all in W/m²/nm).

 The gas transmittance tables cover a water vapor path (precipitable water times air mass) up to 320 g/cm², an ozone path (ozone column times air mass) up to 25 atm-cm, and an air mass times the ratio of surface pressure to 1013.25 hPa up to 37.99. A longer path raises an error; with the sun close to the horizon this happens for precipitable water above about 8.4 cm, an ozone column above about 660 DU, or a surface pressure above about 1015 hPa. A sun at or below the horizon also raises an error.

### Atmosphere Between the Scene and a Satellite Sensor {#SensorAtmosphereTheory}

 To simulate imagery from a sensor above the atmosphere (e.g., a satellite), the radiance leaving the scene must be converted to the radiance reaching the sensor. The atmosphere attenuates the scene radiance and adds light of its own. Following the formulation of the 6S radiative transfer code (<a href="https://doi.org/10.1109/36.581987">Vermote et al. 1997</a>), the radiance at the sensor is

 <center>
   \f$L_{sensor} = L_{path} + T_{dir}^{\uparrow} L_{surface} + T_{dif}^{\uparrow} \rho_g E_g / \pi\f$,
 </center>

 where \f$L_{path}\f$ is the path radiance scattered into the sensor by the atmosphere without reaching the ground, \f$T_{dir}^{\uparrow}\f$ and \f$T_{dif}^{\uparrow}\f$ are the direct and diffuse transmittances from the ground to the sensor, and the last term (the adjacency effect) is light reflected by the surrounding ground of albedo \f$\rho_g\f$, lit by the global irradiance \f$E_g\f$, and scattered into the sensor's line of sight.

 The scattering quantities are taken from a look-up table computed with the vector version of 6S for its continental aerosol model. The table spans surface pressures from 701.2 to 1013 hPa, aerosol optical depths at 550 nm from 0 to 1.2, solar zenith angles up to 70 degrees, view zenith angles up to 60 degrees and all relative azimuths. Gas transmittance, also from 6S, is tabulated separately at 1 nm spacing. In a comparison with direct 6S calculations, top-of-atmosphere reflectances differed by 0.0009 on average and by at most 0.011.

 Limitations: a single (continental) aerosol type; the sensor is above the atmosphere; the adjacency effect assumes surroundings of uniform albedo; and clear sky.

### Thermal Infrared Atmosphere Between the Scene and a Satellite Sensor {#SensorThermalAtmosphereTheory}

 In a thermal infrared band the atmosphere absorbs part of the radiance leaving the scene and emits radiance of its own, so the spectral radiance at a sensor above the atmosphere is \f$L_{sensor} = \tau L_{surface} + L^{\uparrow}\f$, where \f$\tau\f$ is the atmospheric transmittance along the view path and \f$L^{\uparrow}\f$ the radiance emitted by the atmosphere along it. The atmosphere also emits the sky radiance that the scene reflects; it is described by \f$L^{\downarrow}\f$, the downwelling irradiance at the ground divided by \f$\pi\f$, so that a Lambertian surface of emissivity \f$\varepsilon\f$ reflects \f$(1-\varepsilon)L^{\downarrow}\f$.

 The three quantities are interpolated from a look-up table computed with the libRadtran radiative transfer code (REPTRAN absorption parameterization) for a clear sky without aerosol, as averages over 5 cm⁻¹ wavenumber bins stored at the bin centers, 5502-15326 nm. The temperature and humidity profiles are not known from the surface conditions alone, so the table assumes climatological ones, interpolated between standard atmospheres according to the surface air temperature.

 The table's axes are the column water vapor (0.1-7.5 g/cm²), the surface air temperature (at sea level, 246.2-321.7 K; the range is lower at higher elevations, e.g. 242.4-304.6 K at 701.2 hPa), the surface pressure (701.2-1013 hPa, extrapolated linearly up to 1050 hPa), the view zenith angle (0-60 degrees) and the ozone column (150-450 DU). The table agrees with the line-by-line model LBLRTM to within 1 K in brightness temperature for the satellite bands tested.

### Ambient Longwave Flux {#LWTheory}

 The broadband longwave radiation flux emitted by a clear sky (\ref pyhelios.SolarPosition.SolarPosition::getAmbientLongwaveFlux "getAmbientLongwaveFlux()") is modeled following <a href="https://rmets.onlinelibrary.wiley.com/doi/full/10.1002/qj.49712253306">Prata (1996)</a>.

 The model surmounts to calculating the effective emissivity of the sky as a function of precipitable water in the atmosphere

 <center>
   \f$\epsilon_s = 1-(1+u)\mathrm{exp}\left(-\left(1.2+3u\right)^{0.5}\right)\f$,
 </center>

 where \f$u\f$ is the precipitable water in cm. It is estimated from the air temperature \f$T_a\f$ (K) and relative humidity \f$h\f$ set with `setAtmosphericConditions()` as \f$u = 0.465\,e_0/T_a\f$, with the vapor pressure \f$e_0 = 611\,h\,\mathrm{exp}\left(17.502\,(T_a-273)/(T_a-273+240.9)\right)\f$ in Pa. (The precipitable water used by the spectral solar models and the thermal atmosphere look-up table is instead derived from the dew point.)

 The downwelling longwave radiation flux on a horizontal surface is given by

 <center>
   \f$R_L=\epsilon_s\sigma T_a^4\f$,
 </center>

 where \f$\sigma=5.67\times10^{-8}\f$ W/m<sup>2</sup>-K<sup>4</sup>, and \f$T_a\f$ is the air temperature in Kelvin measured near the ground (say 2 m height).

 This flux covers all longwave wavelengths. It is not the right diffuse flux for an emission band with wavelength bounds, which should receive only the sky radiation within the band: \ref pyhelios.SolarPosition.SolarPosition::getThermalSkyFlux "getThermalSkyFlux()" computes that from the thermal atmosphere look-up table (see \ref SensorThermalAtmosphereTheory), for bands within 5502-15326 nm. The table cannot replace the broadband flux, since much of the sky's longwave emission lies outside that range (e.g., the water vapor rotation band beyond 15 µm).
 
## Using the SolarPosition Plug-in {#SolarLib}

### Getting the Direction of the Sun {#SolarPos}

 The direction of the sun can be queried in one of several ways: a Cartesian unit vector pointing in the direction of the sun, a spherical coordinate describing the direction of the sun, the elevation angle of the sun, the zenithal angle of the sun, and the azimuthal angle of the sun.  The functions to query these quantities are given in the table below. Each of these functions calculates the solar direction based on the current time and date set in the Context (see \ref pyhelios.Context.Context::setTime "setTime()" "setTime()" and \ref pyhelios.Context.Context::setDate "setDate()" "setDate()"), and the UTC, latitude, and longitude specified in the \ref pyhelios.SolarPosition.SolarPosition "SolarPosition" constructor.

 <table>
 <tr><th>Direction Quantity</th><th>Function</th></tr>
 <tr><td>Unit vector pointing toward the sun.</td><td>\ref pyhelios.SolarPosition.SolarPosition::getSunDirectionVector "getSunDirectionVector()"</td></tr>
 <tr><td>Spherical coordinate vector pointing toward the sun.</td><td>\ref pyhelios.SolarPosition.SolarPosition::getSunDirectionSpherical "getSunDirectionSpherical()"</td></tr>
 <tr><td>Elevation angle of the sun (radians).</td><td>\ref pyhelios.SolarPosition.SolarPosition::getSunElevation "getSunElevation()"</td></tr>
 <tr><td>Zenithal angle of the sun (radians).</td><td>\ref pyhelios.SolarPosition.SolarPosition::getSunZenith "getSunZenith()"</td></tr>
 <tr><td>Azimuthal angle of the sun (radians).</td><td>\ref pyhelios.SolarPosition.SolarPosition::getSunAzimuth "getSunAzimuth()"</td></tr>
 </table>

 Below is an example of how to use the \ref pyhelios.SolarPosition.SolarPosition "SolarPosition" plugin to calculate the sun angle.

 ```python
from pyhelios import Context, SolarPosition
from pyhelios.types import *

with Context() as context:
    # Set the current time and date
    context.setDate(2015, 5, 1)  # May 1, 2015
    context.setTime(12, 30)      # 12:30

    # Initialize the SolarPosition class with coordinates
    # Arguments: context, utc_offset, latitude, longitude
    with SolarPosition(context, 7, 31.256, 119.947) as sun:
        # Get the sun position
        direction = sun.getSunDirectionVector()  # unit vector

        elevation = sun.getSunElevation()  # elevation angle (radians)
        azimuth = sun.getSunAzimuth()      # azimuthal angle (radians)

        print(f"Direction: {direction}")
        print(f"Elevation: {elevation} radians")
        print(f"Azimuth: {azimuth} radians")
 ```

### Specifying Atmospheric Conditions {#AtmosphericConditions}

The SolarPosition plugin requires atmospheric parameters to calculate solar flux and related quantities. The Python API uses `setAtmosphericConditions()` to set atmospheric parameters once, then calls parameter-free flux methods. This approach is clean, reduces code repetition, and aligns with the C++ plugin API.

```python
from pyhelios import Context, SolarPosition
import math

with Context() as context:
    # Set the current time and date
    context.setDate(2015, 5, 1)  # May 1, 2015
    context.setTime(12, 30)      # 12:30

    # Initialize the SolarPosition class
    with SolarPosition(context, 7, 31.256, 119.947) as sun:
        # Set atmospheric conditions once
        sun.setAtmosphericConditions(
            pressure_Pa=101000,      # Atmospheric pressure (Pa)
            temperature_K=300,       # Temperature (K)
            humidity_rel=0.6,        # Relative humidity (0-1)
            turbidity=0.05           # Turbidity coefficient
        )

        # Call parameter-free methods (no repetition!)
        R = sun.getSolarFlux()
        zenith = sun.getSunZenith()
        R_horiz = R * math.cos(zenith)

        f_diff = sun.getDiffuseFraction()
        R_dir = R * (1.0 - f_diff)

        print(f"Total flux: {R:.2f} W/m²")
        print(f"Horizontal flux: {R_horiz:.2f} W/m²")
        print(f"Diffuse fraction: {f_diff:.3f}")
        print(f"Direct flux: {R_dir:.2f} W/m²")
```

#### Understanding the Turbidity Parameter {#TurbidityDefinition}

 The turbidity parameter used in the SolarPosition plugin is <b>Ångström's aerosol turbidity coefficient (β)</b>, the <b>aerosol optical depth at 1 µm</b>. It quantifies the amount of aerosols (dust, pollution, haze) in the atmosphere that scatter and absorb solar radiation.

 <b>Important:</b> This turbidity definition is NOT the same as "Linke turbidity" (T<sub>L</sub>), which is commonly used in some other solar radiation models and uses a different scale.

 The aerosol optical depth at wavelength λ follows the Ångström turbidity formula:
 \f[
 \tau_{aerosol}(\lambda) = \beta \lambda^{-\alpha}
 \f]
 where λ is in µm and α is the Ångström exponent, taken as 1.3 by the REST-2 and spectral models and the sensor atmosphere model. The aerosol optical depth at 550 nm is therefore about 2.18β, and that at 500 nm about 2.46β; an aerosol optical depth measured at 500 nm (e.g., by a sun photometer) corresponds to β ≈ 0.41 times that value. Passing an aerosol optical depth at 500 nm directly as the turbidity over-states the aerosol load by about 2.5 times. The default turbidity is 0.02.

 The Prague sky model (\ref pyhelios.SolarPosition.SolarPosition::updatePragueSkyModel "updatePragueSkyModel()") is parameterized by ground-level visibility rather than aerosol optical depth. The aerosol optical depth at 550 nm is converted to visibility by log-log interpolation through the model's continental polluted, average and clean atmospheres, whose visibilities are 27.6, 59.4 and 131.8 km. The visibility is limited to the model's range of 20-131.8 km, so air cleaner than an aerosol optical depth at 550 nm of 0.064 (turbidity about 0.029, which includes the default of 0.02) is represented by the cleanest Prague atmosphere, and air hazier than about 0.45 (turbidity about 0.21) by the haziest. The visibility used is stored in Context global data as <code>prague_sky_visibility_km</code>.

 Higher turbidity values result in:
 - Reduced direct solar radiation
 - Increased fraction of diffuse radiation
 - Whitening of the sky (reduced blue color)
 - Enhanced circumsolar brightening (bright region around the sun)

 <table>
 <caption>Atmospheric condition parameters</caption>
 <tr><th>Parameter</th><th>Description</th><th>Validation</th><th>Example Value</th></tr>
 <tr><td>pressure_Pa</td><td>Atmospheric pressure in Pascals (near the ground)</td><td>Must be > 0</td><td>101,325 Pa (1 atm)</td></tr>
 <tr><td>temperature_K</td><td>Air temperature in Kelvin (near the ground)</td><td>Must be > 0</td><td>300 K (27°C)</td></tr>
 <tr><td>humidity_rel</td><td>Air relative humidity (near the ground)</td><td>Must be 0-1; must be greater than 0 for the spectral irradiance, sensor atmosphere and thermal atmosphere methods</td><td>0.5 (50%)</td></tr>
 <tr><td>turbidity</td><td>Ångström's aerosol turbidity coefficient (β), the aerosol optical depth at 1 µm (see \ref TurbidityDefinition). <b>Note:</b> This is NOT Linke turbidity, which uses a different scale. Higher values indicate more aerosols in the atmosphere, which reduces direct solar flux and increases diffuse fraction.</td><td>Must be ≥ 0</td><td>0.02 (default)</td></tr>
 </table>

#### Total Column Ozone {#OzoneColumn}

 The REST-2 and spectral irradiance models and the sensor atmosphere models need the total column ozone, which absorbs in the ultraviolet and in the Chappuis band in the visible. It can be set, in Dobson units, with \ref pyhelios.SolarPosition.SolarPosition::setOzoneColumn "setOzoneColumn()" (stored in Context global data as <code>atmosphere_ozone_DU</code>). Otherwise it is taken from a monthly zonal-mean climatology: the monthly mean total ozone of the NASA SBUV Merged Ozone Data Set in 36 latitude bands 5 degrees wide, averaged over 2005-2024. The value at the current date and latitude is interpolated linearly in latitude between the centers of the bands and in the day of the year between the middles of the months. It can be retrieved with \ref pyhelios.SolarPosition.SolarPosition::getOzoneColumn "getOzoneColumn()".

 The climatology ranges from about 180 DU (the Antarctic ozone hole, 75-80 degrees south in October) to about 420 DU (the Arctic in spring). It has no data where the sun is too low for the satellite measurements, in high-latitude winter months, nor poleward of 80 degrees; for those dates and latitudes, any method that needs the ozone column (including \ref pyhelios.SolarPosition.SolarPosition::getSolarFlux "getSolarFlux()") raises an error, and the ozone column must be set with `setOzoneColumn()`. Next to a latitude band or month without data, the value of the band or month containing the latitude or date is used rather than interpolating toward the missing one.

```python
sun.setOzoneColumn(310.0)        # e.g., from a local measurement
ozone_DU = sun.getOzoneColumn()  # 310.0
```

### Getting the Solar Flux {#SolarFlux}

 The solar flux can be calculated using the REST-2 model of <a href="https://www.sciencedirect.com/science/article/pii/S0038092X07000990?casa_token=BAJYGez71awAAAAA:CfmA4oT9MLiHGvpD6oUkkDu4EJ1S9uRabZq4-wM07jtcmviZ12jvhD8VVcAkjLWoGNMtg8hDaqo">Gueymard (2008)</a> using the \ref pyhelios.SolarPosition.SolarPosition::getSolarFlux "getSolarFlux()" function. IT IS CRITICAL TO NOTE THAT THE CALCULATED FLUX IS FOR A SURFACE PERPENDICULAR TO THE SUN DIRECTION. To get the flux on a horizontal surface, multiply by the cosine of the solar zenith angle.

 Methods are available to get the incoming solar radiation flux perpendicular to the direction of the sun 1) for the entire solar spectrum (\ref pyhelios.SolarPosition.SolarPosition::getSolarFlux "getSolarFlux()"), 2) for the PAR band (\ref pyhelios.SolarPosition.SolarPosition::getSolarFluxPAR "getSolarFluxPAR()"), and 3) for the NIR band (\ref pyhelios.SolarPosition.SolarPosition::getSolarFluxNIR "getSolarFluxNIR()").

 The very similar function \ref pyhelios.SolarPosition.SolarPosition::getDiffuseFraction "getDiffuseFraction()" calculates the fraction of the total flux that is diffuse. The fraction that is direct is simply one minus the diffuse fraction.

 Example code for using these solar flux functions is given below.

```python
from pyhelios import Context, SolarPosition
import math

with Context() as context:
    # Set the current time and date
    context.setDate(2015, 5, 1)  # May 1, 2015
    context.setTime(12, 30)      # 12:30

    # Initialize the SolarPosition class
    with SolarPosition(context, 7, 31.256, 119.947) as sun:
        # Define atmospheric conditions
        pressure_Pa = 101000      # pressure
        temperature_K = 300       # temperature
        humidity_rel = 0.6        # humidity
        turbidity = 0.05          # turbidity

        # Get the sun position
        zenith = sun.getSunZenith()  # zenithal angle (radians)

        # Calculate solar flux with atmospheric parameters
        R = sun.getSolarFlux(pressure_Pa, temperature_K, humidity_rel, turbidity)
        R_horiz = R * math.cos(zenith)  # flux on horizontal surface

        f_diff = sun.getDiffuseFraction(pressure_Pa, temperature_K, humidity_rel, turbidity)

        R_dir = R * (1.0 - f_diff)  # direct component of flux (W/m²)
```

#### Calibrating the turbidity using weather station (radiometer) data {#SolarFluxTurb}

 The predicted solar flux may not perfectly match local predicted solar fluxes due to uncertainty in the local turbidity value. There is a built-in routine to calibrate the turbidity based on measured radiative fluxes.

 For the calibration, you must load radiation flux data into a timeseries within the Context. There must be at least one clear-sky day in the timeseries data, and the radiative fluxes must be for the entire solar spectrum in units of W/m<sup>2</sup>. You can then use the \ref pyhelios.SolarPosition.SolarPosition::calibrateTurbidityFromTimeseries "calibrateTurbidityFromTimeseries()" method. This method takes one argument, which is a string corresponding to the timeseries variable name containing the radiation flux data.

#### Incorporating the effects of clouds {#SolarFluxClouds}

 The REST2 model for solar fluxes was developed for clear-sky conditions and cannot directly be used when clouds are present. If incident solar radiation data is available (e.g., from a weather station), this can be used to calibrate the model to account for the possible presence of clouds. A simple model is described below for doing so.

 Consider \f$R_{meas,h}\f$ to be the measured all-wave incoming solar radiation flux on a horizontal plane (clear or cloudy conditions), and \f$R_{clear}\f$ to be the predicted all-wave incoming solar radiation flux predicted by the REST2 model for clear-sky conditions perpendicular to the direction of the sun. This flux can be projected onto the horizontal plane according to

 \f[
    R_{clear,h} = R_{clear}\mathrm{cos}\,\theta_s.
 \f]

 The diffuse fraction can be approximated as

 \f[
    f_{diff} = 1-\frac{R_{meas,h} - R_{clear,h}}{R_{clear,h}},
 \f]

 where it is enforced that \f$0\leq f_{diff} \leq 1\f$. The resulting flux that is output from the model is (flux perpendicular to the sun)

 \f[
   R_{model} = R_{clear}\frac{R_{meas,h}}{R_{clear,h}}.
 \f]

 In order to enable flux calibration for cloudy conditions, you must 1) Load timeseries data containing the measured all-wave solar radiation flux. This data must cover the entire period of the simulation. 2) Call \ref pyhelios.SolarPosition.SolarPosition::enableCloudCalibration "enableCloudCalibration()", which requires a string corresponding to the timeseries data label.

 Below is a Python example showing cloud calibration using Context timeseries:

```python
from pyhelios import Context, SolarPosition

with Context() as context:
    # Load weather data directly into Context timeseries
    context.loadTabularTimeseriesData(
        "/path/to/weatherdatafile.txt",
        column_labels=["date", "hour", "Tair_C", "humidity_rel", "Patm_Pa", "R_tot_Wm2"],
        delimiter=",",
        headerlines=1
    )

    with SolarPosition(context, 7, 31.256, 119.947) as sun:
        # Enable cloud calibration using measured radiation timeseries
        sun.enableCloudCalibration("R_tot_Wm2")

        # Calibrate turbidity from measured radiation data
        turbidity = sun.calibrateTurbidityFromTimeseries("R_tot_Wm2")

        # Loop through timeseries data points
        n = context.getTimeseriesLength("Tair_C")
        for i in range(n):
            # Set context date/time to this timeseries point
            context.setCurrentTimeseriesPoint("Tair_C", i)

            # Query atmospheric data at this timestep
            Tair_K = context.queryTimeseriesData("Tair_C", index=i) + 273.15
            humidity_rel = context.queryTimeseriesData("humidity_rel", index=i)
            Patm_Pa = context.queryTimeseriesData("Patm_Pa", index=i)

            # Set atmospheric conditions for this timestep
            sun.setAtmosphericConditions(Patm_Pa, Tair_K, humidity_rel, turbidity)

            # Calculate solar flux
            R = sun.getSolarFlux()
            f_diff = sun.getDiffuseFraction()

            R_dir = R * (1.0 - f_diff)  # direct component
            R_diff = R * f_diff          # diffuse component
```

 An example of the above model applied to actual direct-diffuse partitioned radiation data using a shadowband radiometer is shown below. It should be emphasized that the above model is a relatively simple approximation that produces reasonable fluxes, but more accurate predictions are possible and require much more complicated models.

## Getting Spectral Solar Irradiance {#SpectralFlux}

 For applications requiring wavelength-resolved irradiance (e.g., photosynthesis models with wavelength-dependent quantum yield, remote sensing, hyperspectral image simulation), the \ref pyhelios.SolarPosition.SolarPosition::calculateGlobalSolarSpectrum "calculateGlobalSolarSpectrum()", \ref pyhelios.SolarPosition.SolarPosition::calculateDirectSolarSpectrum "calculateDirectSolarSpectrum()" and \ref pyhelios.SolarPosition.SolarPosition::calculateDiffuseSolarSpectrum "calculateDiffuseSolarSpectrum()" methods compute high-resolution spectral irradiance with the model described in \ref SpectralIrradianceTheory.

 The spectral irradiance methods use the atmospheric conditions set with \ref pyhelios.SolarPosition.SolarPosition::setAtmosphericConditions "setAtmosphericConditions()" (the relative humidity must be greater than zero), the ozone column (see \ref OzoneColumn) and the ground albedo. Results are stored in Context global data for use by other plugins (e.g., the radiation plugin for ray tracing with spectral sources), which refer to a spectrum by its label.

 The spectral model also depends on the albedo of the ground surrounding the scene. Light reflected by the ground is partly scattered back down by the atmosphere, which raises the global and diffuse irradiance, most strongly at blue and ultraviolet wavelengths where atmospheric scattering is strongest; without cloud calibration the direct beam is unaffected. The ground albedo defaults to 0.2 and can be set with \ref pyhelios.SolarPosition.SolarPosition::setGroundAlbedo "setGroundAlbedo()" (stored in Context global data as <code>atmosphere_ground_albedo</code>):

```python
sun.setGroundAlbedo(0.8)  # e.g., fresh snow
```

 Example code for calculating spectral irradiance:

```python
from pyhelios import Context, SolarPosition

with Context() as context:
    # Set current time, date, and location
    context.setDate(2023, 7, 16)  # July 16, 2023
    context.setTime(12, 0)         # Solar noon

    # Initialize SolarPosition with location
    # Arguments: context, utc_offset, latitude, longitude
    with SolarPosition(context, 0, 36.93, 3.33) as sun:
        # Calculate global solar spectrum at 1 nm resolution (default)
        sun.calculateGlobalSolarSpectrum("clear_sky")

        # Or specify a coarser resolution (e.g., 10 nm)
        sun.calculateGlobalSolarSpectrum("clear_sky_10nm", 10.0)

        # The spectrum is stored in Context global data under the same label
        # as (wavelength in nm, irradiance in W/m²/nm) pairs
        n_wavelengths = context.getGlobalDataSize("clear_sky")  # 2301

        # Similarly for direct and diffuse components:
        sun.calculateDirectSolarSpectrum("direct_beam")
        sun.calculateDiffuseSolarSpectrum("sky_diffuse")
```

 Three separate methods are available for the different spectral components:
 - \ref pyhelios.SolarPosition.SolarPosition::calculateGlobalSolarSpectrum "calculateGlobalSolarSpectrum()": Total irradiance on horizontal surface (direct + diffuse)
 - \ref pyhelios.SolarPosition.SolarPosition::calculateDirectSolarSpectrum "calculateDirectSolarSpectrum()": Direct beam irradiance normal to sun direction
 - \ref pyhelios.SolarPosition.SolarPosition::calculateDiffuseSolarSpectrum "calculateDiffuseSolarSpectrum()": Diffuse irradiance on horizontal surface

 Each method accepts an optional resolution parameter (default 1 nm) allowing wavelength downsampling. For example, resolution_nm=10.0 produces 231 wavelengths instead of the native 2301.

### Simulating Satellite Imagery {#SensorAtmosphere}

 \ref pyhelios.SolarPosition.SolarPosition::calculateSensorAtmosphereSpectra "calculateSensorAtmosphereSpectra()" computes the spectra needed to convert radiance leaving the scene into radiance at a sensor above the atmosphere (see \ref SensorAtmosphereTheory). Given the direction from the scene toward the sensor, it stores in Context global data the path radiance, the adjacency radiance, the upward direct and diffuse transmittances and the atmospheric spherical albedo, together with the direct, diffuse and global solar irradiance at the ground computed with the same atmosphere. To keep the illumination of the scene consistent with the atmosphere between it and the sensor, use these irradiance spectra, rather than those of `calculateDirectSolarSpectrum()` and `calculateDiffuseSolarSpectrum()`, for the scene's radiation sources.

```python
from pyhelios import Context, SolarPosition
from pyhelios.types import vec3

with Context() as context:
    context.setDate(2023, 7, 16)
    context.setTime(12, 0)

    with SolarPosition(context, 0, 36.93, 3.33) as sun:
        sun.setAtmosphericConditions(101325, 298, 0.5, 0.1)  # pressure, temperature, humidity, turbidity
        sun.setGroundAlbedo(0.15)  # albedo of the ground surrounding the scene

        # Sensor at nadir
        sun.calculateSensorAtmosphereSpectra("satellite", vec3(0, 0, 1))

        # Stored spectra: (wavelength in nm, value) pairs
        assert context.doesGlobalDataExist("satellite_path_radiance")  # W/m²/sr/nm
```

 <table>
 <caption>Global data stored by calculateSensorAtmosphereSpectra(), each named with the label followed by a suffix</caption>
 <tr><th>Suffix</th><th>Description</th><th>Units</th></tr>
 <tr><td>_path_radiance</td><td>Radiance scattered by the atmosphere into the sensor without reaching the ground</td><td>W/m²/sr/nm</td></tr>
 <tr><td>_adjacency_radiance</td><td>Radiance reflected by the surrounding ground and scattered by the atmosphere into the sensor</td><td>W/m²/sr/nm</td></tr>
 <tr><td>_upward_direct_transmittance</td><td>Transmittance of the surface-leaving radiance straight to the sensor, including gas absorption</td><td>-</td></tr>
 <tr><td>_upward_diffuse_transmittance</td><td>Transmittance of surface-leaving radiance scattered into the sensor direction, including gas absorption</td><td>-</td></tr>
 <tr><td>_spherical_albedo</td><td>Spherical albedo of the atmosphere</td><td>-</td></tr>
 <tr><td>_direct_irradiance</td><td>Direct solar irradiance at the ground, normal to the sun direction</td><td>W/m²/nm</td></tr>
 <tr><td>_diffuse_irradiance</td><td>Diffuse solar irradiance at the ground on a horizontal surface</td><td>W/m²/nm</td></tr>
 <tr><td>_global_irradiance</td><td>Global solar irradiance at the ground on a horizontal surface</td><td>W/m²/nm</td></tr>
 <tr><td>_direction_to_sensor</td><td>Unit vector toward the sensor (a single vec3)</td><td>-</td></tr>
 </table>

 The turbidity set with `setAtmosphericConditions()` (the Ångström coefficient β, see \ref TurbidityDefinition) is converted to an aerosol optical depth at 550 nm using an Ångström exponent of 1.3. Conditions outside the range of the look-up table (solar zenith above 70 degrees, view zenith above 60 degrees, aerosol optical depth at 550 nm above 1.2, surface pressure below 701.2 hPa or above 1050 hPa, or a water vapor path, the column water vapor times \f$1/\mu_s + 1/\mu_v\f$, above 320 g/cm²) and a sun below the horizon raise an error; pressures between 1013 and 1050 hPa are extrapolated linearly. The model assumes clear sky, so it cannot be used together with cloud calibration.

### Simulating Satellite Thermal Imagery {#SensorThermalAtmosphere}

 \ref pyhelios.SolarPosition.SolarPosition::calculateSensorThermalAtmosphere "calculateSensorThermalAtmosphere()" computes the thermal infrared transmittance and upwelling and downwelling atmospheric radiance for a sensor viewing the scene from the given direction (see \ref SensorThermalAtmosphereTheory). They are stored in Context global data as spectra of 234 points from 5502 to 15326 nm, with the suffixes "_thermal_transmittance", "_thermal_upwelling_radiance" and "_thermal_downwelling_radiance" (radiances in W/m²/sr/nm). The atmospheric profile is built from the air temperature, humidity and pressure set with `setAtmosphericConditions()` and the ozone column (\ref OzoneColumn); the column water vapor derived from the temperature and humidity is stored with the suffix "_thermal_water_vapor_cm", and the unit vector toward the sensor with the suffix "_direction_to_sensor". The model does not depend on the sun's position, so night-time imagery can be simulated.

```python
sun.setAtmosphericConditions(101325, 298, 0.5, 0.1)
sun.calculateSensorThermalAtmosphere("satellite", vec3(0, 0, 1))  # sensor at nadir

water_vapor = context.getGlobalData("satellite_thermal_water_vapor_cm")  # g/cm²
```

 The column water vapor must lie within 0.1-7.5 g/cm², the pressure within 701.2-1050 hPa, the ozone column within 150-450 DU, and the view zenith angle must not exceed 60 degrees. The supported air temperatures depend on the pressure: 246.2-321.7 K at 1013 hPa. Conditions outside these ranges raise an error.

 The sky longwave radiance that the scene reflects in a thermal band should come from the same atmosphere. \ref pyhelios.SolarPosition.SolarPosition::getThermalSkyFlux "getThermalSkyFlux()" gives the clear-sky longwave irradiance on a horizontal surface within a band, the band-specific counterpart of the broadband \ref pyhelios.SolarPosition.SolarPosition::getAmbientLongwaveFlux "getAmbientLongwaveFlux()"; it is the diffuse flux to give an emission band with the same wavelength bounds:

```python
radiation.addRadiationBand("TIR", 10600, 11190)  # e.g., Landsat 8 TIRS band 10
radiation.setDiffuseRadiationFlux("TIR", sun.getThermalSkyFlux(10600, 11190))
```

### Getting the Sky Longwave Flux {#LWFlux}

The downwelling longwave radiation flux from the sky can be calculated using the \ref pyhelios.SolarPosition.SolarPosition::getAmbientLongwaveFlux "getAmbientLongwaveFlux()" function. This function is based on the Prata (1996) model and returns the clear-sky downwelling longwave radiation flux on a horizontal surface in W/m<sup>2</sup>, integrated over all longwave wavelengths (see \ref LWTheory). It is the diffuse flux to give an emission band without wavelength bounds. For an emission band with wavelength bounds, use \ref pyhelios.SolarPosition.SolarPosition::getThermalSkyFlux "getThermalSkyFlux()" instead, which gives the clear-sky irradiance within the band (see \ref SensorThermalAtmosphere).

```python
from pyhelios import Context, SolarPosition

with Context() as context:
    with SolarPosition(context) as sun:
        # Set atmospheric conditions (includes temperature and humidity)
        sun.setAtmosphericConditions(101325, 288.15, 0.6, 0.05)

        # Get longwave flux (uses temperature and humidity from atmospheric conditions)
        lw_flux = sun.getAmbientLongwaveFlux()
        print(f"Longwave flux: {lw_flux:.2f} W/m²")
```
