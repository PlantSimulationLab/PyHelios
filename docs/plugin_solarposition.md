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
    context.setDate(1, 5, 2015)  # May 1, 2015
    context.setTime(30, 12)      # 12:30

    # Create SolarPosition with location (UTC offset, latitude, longitude)
    with SolarPosition(7, 31.256, 119.947, context) as sun:
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

 The \ref pyhelios.SolarPosition.SolarPosition "SolarPosition" class can be initialized by simply passing a Helios context as an argument to the constructor. This gives the class access to the time and date currently set in the Context. The model must also know certain parameters about the simulated location, in particular the offset from UTC time, latitude, and longitude. A description of these parameters are given in the table below. These can be supplied using the second constructor listed in the table above. If only the Context is supplied to the constructor, the plugin uses Context location settings (if configured).

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
 \f$\Gamma = 2\pi(DOY-1)/365.25\f$,  (1)
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

### Spectral Solar Irradiance (SSolar-GOA Model) {#SpectralIrradianceTheory}

 For applications requiring high spectral resolution (e.g., photosynthesis, remote sensing), the plugin implements the SSolar-GOA spectral radiative transfer model from <a href="https://gmd.copernicus.org/articles/15/1689/2022/">Cachorro et al. (2022)</a>. This model computes bottom-of-atmosphere spectral irradiance from 300-2600 nm at 1 nm resolution.

 The SSolar-GOA model uses the Wehrli (1985) extraterrestrial solar spectrum corrected for Earth-Sun distance, then applies atmospheric transmittances for:

 - <b>Rayleigh scattering</b>: Molecular scattering using Bates (1984) optical depth formula
 - <b>Aerosol extinction</b>: Ångström turbidity law with Ambartsumian solution for scattering
 - <b>Water vapor absorption</b>: Empirical model for bands at 940, 1130, 1380, and 1870 nm
 - <b>Ozone absorption</b>: UV Hartley band (200-310 nm) and visible Chappuis band (400-700 nm)
 - <b>Oxygen absorption</b>: Primarily the A-band at 760 nm

 The model also accounts for surface-atmosphere multiple reflections based on surface albedo and atmospheric spherical albedo.

 <b>Parameter Derivation:</b> The implementation uses the same atmospheric inputs as the REST-2 model (pressure, temperature, humidity, turbidity). Additional parameters are derived automatically: precipitable water (Viswanadham 1981), ozone column (van Heuklon 1979), Ångström alpha (1.3), surface albedo (0.2), aerosol single scattering albedo (0.90), and asymmetry parameter (0.85).

 <b>Output Format:</b> Results are stored in Context global data as vectors of (wavelength, irradiance) pairs (\ref pyhelios.types.vec2 "vec2") with user-defined labels. Three spectral components are computed: global irradiance on horizontal surface, direct irradiance normal to sun direction, and diffuse irradiance on horizontal surface (all in W/m²/nm).

### Ambient Longwave Flux {#LWTheory}

 The longwave radiation flux emanating from the clear-sky is modeled following <a href="https://rmets.onlinelibrary.wiley.com/doi/full/10.1002/qj.49712253306">Prata (1996)</a>.

 The model surmounts to calculating the effective emissivity of the sky as a function of precipitable water in the atmosphere

 <center>
   \f$\epsilon_s = 1-(1+u)\mathrm{exp}\left(-\left(1.2+3u\right)^{0.5}\right)\f$,
 </center>

 where \f$u\f$ is the wator vapor path length (cm of precipitable water) which can be estimated following <a href="https://journals.ametsoc.org/doi/abs/10.1175/1520-0450(1981)020%3C0003%3ATRBTPW%3E2.0.CO%3B2">Viswanadham (1981)</a> for example.

 The downwelling longwave radiation flux on a horizontal surface is given by

 <center>
   \f$R_L=\epsilon_s\sigma T_a^4\f$,
 </center>

 where \f$\sigma=5.67\times10^{-8}\f$ W/m<sup>2</sup>-K<sup>4</sup>, and \f$T_a\f$ is the air temperature in Kelvin measured near the ground (say 2 m height).
 
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
    context.setDate(1, 5, 2015)  # May 1, 2015
    context.setTime(30, 12)      # 12:30

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
    context.setDate(1, 5, 2015)  # May 1, 2015
    context.setTime(30, 12)      # 12:30

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

 The turbidity parameter used in the SolarPosition plugin is <b>Ångström's aerosol turbidity coefficient (β)</b>, which represents the <b>aerosol optical depth (AOD) at 500 nm reference wavelength</b>. This parameter quantifies the amount of aerosols (dust, pollution, haze) in the atmosphere that scatter and absorb solar radiation.

 <b>Important:</b> This turbidity definition is NOT the same as "Linke turbidity" (T<sub>L</sub>), which is commonly used in some other solar radiation models. Linke turbidity typically ranges from 2-6, while Ångström turbidity (AOD) typically ranges from 0.02-0.4. The two are related but use different scales.

 The turbidity value is used in the Ångström turbidity formula:
 \f[
 \tau_{aerosol}(\lambda) = \beta \left(\frac{\lambda_{ref}}{\lambda}\right)^{\alpha}
 \f]
 where β is the turbidity parameter (AOD at 500 nm), λ is wavelength, λ<sub>ref</sub> = 500 nm, and α is the Ångström exponent (typically ~1.3).

 <b>Guidance for selecting turbidity values:</b>
 - 0.02: Very clear sky (remote/clean atmosphere) - <b>default value</b>
 - 0.03-0.05: Clear sky (typical for rural areas)
 - 0.1: Light haze or light pollution
 - 0.2-0.3: Hazy conditions (urban/polluted atmosphere)
 - >0.4: Very hazy or heavily polluted atmosphere

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
 <tr><td>humidity_rel</td><td>Air relative humidity (near the ground)</td><td>Must be 0-1</td><td>0.6 (60%)</td></tr>
 <tr><td>turbidity</td><td>Ångström's aerosol turbidity coefficient (β), which represents the aerosol optical depth (AOD) at 500 nm reference wavelength. <b>Note:</b> This is NOT Linke turbidity, which uses a different scale (typically 2-6). Typical values: 0.02 (very clear sky), 0.05 (clear sky), 0.1 (light haze), 0.2-0.3 (hazy), >0.4 (very hazy/polluted). Higher values indicate more aerosols in the atmosphere, which reduces direct solar flux and increases diffuse fraction.</td><td>Must be ≥ 0</td><td>0.02 (default clear sky)</td></tr>
 </table>

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
    context.setDate(1, 5, 2015)  # May 1, 2015
    context.setTime(30, 12)      # 12:30

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

 For applications requiring wavelength-resolved irradiance (e.g., photosynthesis models with wavelength-dependent quantum yield, remote sensing, hyperspectral image simulation), the \ref pyhelios.SolarPosition.SolarPosition::calculateGlobalSolarSpectrum "calculateGlobalSolarSpectrum()" method computes high-resolution spectral irradiance using the SSolar-GOA model.

 The spectral irradiance methods automatically derive atmospheric parameters (water vapor, ozone column) from standard atmospheric models. Results are stored in Context global data for use by other plugins (e.g., radiation plugin for ray tracing with spectral sources).

 **Note:** The Python API for spectral calculations differs from C++. Atmospheric conditions must be provided via \ref pyhelios.SolarPosition.SolarPosition::getSolarFlux "getSolarFlux()" and related methods. The spectral calculation methods derive additional parameters automatically.

 Example code for calculating spectral irradiance:

```python
from pyhelios import Context, SolarPosition

with Context() as context:
    # Set current time, date, and location
    context.setDate(16, 7, 2023)  # July 16, 2023
    context.setTime(12, 0)         # Solar noon

    # Initialize SolarPosition with location
    # Arguments: context, utc_offset, latitude, longitude
    with SolarPosition(context, 0, 36.93, 3.33) as sun:
        # Calculate global solar spectrum at 1 nm resolution (default)
        sun.calculateGlobalSolarSpectrum("clear_sky")

        # Or specify a coarser resolution (e.g., 10 nm)
        sun.calculateGlobalSolarSpectrum("clear_sky_10nm", 10.0)

        # Retrieve spectral data from Context using the same label
        global_spectrum = context.getGlobalData("clear_sky")

        # Use spectral data (wavelength in nm, irradiance in W/m²/nm)
        for point in global_spectrum:
            wavelength_nm = point.x
            irradiance = point.y  # W/m²/nm on horizontal surface
            # ... use wavelength-resolved irradiance

        # Similarly for direct and diffuse components:
        sun.calculateDirectSolarSpectrum("direct_beam")
        sun.calculateDiffuseSolarSpectrum("sky_diffuse")
```

 Three separate methods are available for the different spectral components:
 - \ref pyhelios.SolarPosition.SolarPosition::calculateGlobalSolarSpectrum "calculateGlobalSolarSpectrum()": Total irradiance on horizontal surface (direct + diffuse)
 - \ref pyhelios.SolarPosition.SolarPosition::calculateDirectSolarSpectrum "calculateDirectSolarSpectrum()": Direct beam irradiance normal to sun direction
 - \ref pyhelios.SolarPosition.SolarPosition::calculateDiffuseSolarSpectrum "calculateDiffuseSolarSpectrum()": Diffuse irradiance on horizontal surface

 Each method accepts an optional resolution parameter (default 1 nm) allowing wavelength downsampling. For example, resolution_nm=10.0 produces 231 wavelengths instead of the native 2301.

### Getting the Sky Longwave Flux {#LWFlux}

The downwelling longwave radiation flux from the sky can be calculated using the \ref pyhelios.SolarPosition.SolarPosition::getAmbientLongwaveFlux "getAmbientLongwaveFlux()" function. This function is based on the Prata (1996) model and returns the clear-sky downwelling longwave radiation flux on a horizontal surface in W/m<sup>2</sup>.

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
