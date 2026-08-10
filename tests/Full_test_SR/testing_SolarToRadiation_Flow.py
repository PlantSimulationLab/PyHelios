"""
STAGE 1 of the maize simulation test — WHERE RADIATION'S INPUTS COME FROM.


User inputs
     ↓
SolarPosition
     ↓
PAR / NIR / direction / longwave
     ↓
Split direct + diffuse
     ↓
CHECK VALUES
     ↓
Print what Radiation SHOULD receive

===============================================================================
WHAT THIS FILE ANSWERS
===============================================================================

Before running a full simulation it is worth being able to point at every number
the radiation model receives and say exactly where it came from.

This script does only that. It runs the SOLAR half, then prints the complete
chain from the values you type to the values radiation would be handed:

    YOU TYPE            SOLAR COMPUTES           YOU HAND TO RADIATION
    ----------------    ---------------------    ---------------------------
    latitude            sun direction vector     setSourcePosition(...)
    longitude           elevation / zenith
    UTC offset          azimuth
    date, time
                        PAR  (beam-normal)       setSourceFlux(sun,"PAR",...)
    pressure            NIR  (beam-normal)       setDiffuseRadiationFlux("PAR")
    temperature         diffuse fraction         setSourceFlux(sun,"NIR",...)
    humidity                                     setDiffuseRadiationFlux("NIR")
    turbidity           sky longwave             setDiffuseRadiationFlux("LW")

===============================================================================
THE KEY IDEA: THE TWO PLUGINS NEVER TALK TO EACH OTHER
===============================================================================

Solar Position does not know Radiation exists. Radiation does not know Solar
Position exists. YOUR CODE is the bridge between them.

That bridge is about five lines long, and it is where integration bugs live.
Every unit test can pass while the bridge is wrong:

    - hand over the total instead of splitting direct from diffuse
    - forget setSourcePosition, so the sun never moves off its default
    - use band label "par" when the band was created as "PAR"
    - multiply by cos(zenith) when Helios does not want you to

None of those raise an error. The run completes and the numbers are wrong.

===============================================================================
HOW TO RUN
===============================================================================

    cd helios_gui/backend-api/pyhelios
    source ../Env/Scripts/activate          # Git Bash
    export PYHELIOS_USE_PIP=0
    python tests/Full_test_SR/testing_SolarToRadiation_Flow.py

Use FORWARD slashes even on Windows. In Git Bash a backslash escapes the next
character, so tests\\Full_test_SR\\... silently collapses to testsFull_test_SR...
and you get "No such file or directory". Also note: use `python <file>`, not
`python -m <file>` — the -m flag runs a MODULE (a dotted import path with no
.py), not a file path.

This stage needs ONLY the solarposition plugin, so it runs without a GPU. To
actually ray trace the numbers it prints, run the stage 2 script alongside it:

    python tests/Full_test_SR/testing_Maize_Simulation.py
"""

import math
import os
import sys

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")))
os.environ.setdefault("PYHELIOS_USE_PIP", "0")

from pyhelios import Context, SolarPosition  # noqa: E402


# ===========================================================================
# THE SCENARIO
# ===========================================================================
# A maize field at Davis, California, at 1pm on the summer solstice. Chosen
# because the sun is high and the flux is large, which makes every downstream
# number easy to read.
#
# REMEMBER the two inverted sign conventions:
#   longitude   POSITIVE = WEST.  Google Maps says Davis is -121.74; Helios
#               wants +121.74.
#   utc_offset  POSITIVE = WEST.  California is UTC-7 in summer, so +7 here.
# ===========================================================================

SITE = {
    "latitude": 38.5449,     # 38.5 N
    "longitude": 121.7405,   # 121.7 W  -> positive in Helios
    "utc_offset": 7,         # UTC-7    -> positive in Helios
}
DATE = (2026, 6, 20)
TIME = (13, 0)

# Atmosphere. Units are the easiest thing in this whole file to get wrong:
#   pressure     PASCALS      101325     not 1013 hPa
#   temperature  KELVIN       300        not 27 C
#   humidity     FRACTION     0.5        not 50 %
#   turbidity    ANGSTROM b   0.05       not 3.0 Linke
PRESSURE_PA = 101325.0
TEMPERATURE_K = 300.0
HUMIDITY_FRAC = 0.5
TURBIDITY_BETA = 0.05



def rule(title):
    print("\n" + "=" * 74)
    print(f"  {title}")
    print("=" * 74)


def main():
    # -------------------------------------------------------------------
    # STAGE 1 — the inputs a user types into the panel
    # -------------------------------------------------------------------
    rule("STAGE 1   WHAT THE USER TYPES")

    year, month, day = DATE
    hour, minute = TIME
    print(f"""
    SITE
      Latitude          {SITE['latitude']:>12.4f}  deg     {abs(SITE['latitude']):.4f} N
      Longitude         {SITE['longitude']:>12.4f}  deg     {abs(SITE['longitude']):.4f} W   (POSITIVE-WEST)
      UTC offset        {SITE['utc_offset']:>12}  h       UTC-{SITE['utc_offset']}       (POSITIVE-WEST)

    DATE AND TIME
      Date              {year:>12d}-{month:02d}-{day:02d}
      Time              {hour:>12d}:{minute:02d}          local clock time

    ATMOSPHERE
      Pressure          {PRESSURE_PA:>12.0f}  Pa      (NOT hPa)
      Temperature       {TEMPERATURE_K:>12.1f}  K       = {TEMPERATURE_K - 273.15:.1f} C
      Humidity          {HUMIDITY_FRAC:>12.2f}  frac    = {HUMIDITY_FRAC * 100:.0f} %   (NOT percent)
      Turbidity beta    {TURBIDITY_BETA:>12.2f}          Angstrom (NOT Linke)""")

    # -------------------------------------------------------------------
    # STAGE 2 — what Solar Position computes from those inputs
    # -------------------------------------------------------------------
    context = Context()
    context.setDate(*DATE)
    context.setTime(*TIME)
    solar = SolarPosition(context, **SITE)

    try:
        solar.setAtmosphericConditions(
            PRESSURE_PA, TEMPERATURE_K, HUMIDITY_FRAC, TURBIDITY_BETA)

        # Geometry — depends only on site, date and time.
        elevation = solar.getSunElevation()      # radians, despite the docstring
        zenith = solar.getSunZenith()
        azimuth = solar.getSunAzimuth()
        sun_vector = solar.getSunDirectionVector()

        # Flux — depends on geometry AND atmosphere.
        par_total = solar.getSolarFluxPAR()          # beam-normal W/m2
        nir_total = solar.getSolarFluxNIR()          # beam-normal W/m2
        fdiff = solar.getDiffuseFraction()           # 0..1, shared by PAR & NIR
        longwave = solar.getAmbientLongwaveFlux()    # W/m2 from the sky

        rule("STAGE 2   WHAT SOLAR POSITION COMPUTES")
        print(f"""
    SUN GEOMETRY                        from site + date + time only
      getSunElevation()   {math.degrees(elevation):>10.3f} deg    ({elevation:.5f} rad)
      getSunZenith()      {math.degrees(zenith):>10.3f} deg    ({zenith:.5f} rad)
      getSunAzimuth()     {math.degrees(azimuth):>10.3f} deg    ({azimuth:.5f} rad)
      getSunDirectionVector()
                          x = {sun_vector.x:+.5f}   y = {sun_vector.y:+.5f}   z = {sun_vector.z:+.5f}

    SOLAR FLUX                          Gueymard (2008) REST2 model
      getSolarFluxPAR()   {par_total:>10.2f} W/m2   beam-normal, 400-700 nm
      getSolarFluxNIR()   {nir_total:>10.2f} W/m2   beam-normal, 700-2500 nm
      getDiffuseFraction(){fdiff:>10.4f}          {fdiff * 100:.1f}% of it is diffuse

    SKY LONGWAVE                        Prata (1996) model
      getAmbientLongwaveFlux()
                          {longwave:>10.2f} W/m2   from T_air and humidity only

    NOTE  "beam-normal" means measured on a surface facing the sun square-on,
          NOT on a horizontal surface. Helios wants beam-normal, so you do NOT
          multiply by cos(zenith). Helios's own tutorial 14 confirms this.
          For reference, horizontal would be {par_total * math.cos(zenith):.2f} W/m2 for PAR.""")

        # -------------------------------------------------------------------
        # STAGE 3 — the bridge. This is the code under test.
        # -------------------------------------------------------------------
        par_direct = par_total * (1.0 - fdiff)
        par_diffuse = par_total * fdiff
        nir_direct = nir_total * (1.0 - fdiff)
        nir_diffuse = nir_total * fdiff

        rule("STAGE 3   THE BRIDGE  -  your code, and where bugs live")
        print(f"""
    Solar gives ONE total per band. Radiation needs TWO numbers per band:
    one for the beam from the sun's disc, one for the scattered sky.
    Splitting them is your job, using the diffuse fraction.

      PAR direct   = {par_total:7.2f} x (1 - {fdiff:.4f})  = {par_direct:8.2f} W/m2
      PAR diffuse  = {par_total:7.2f} x      {fdiff:.4f}   = {par_diffuse:8.2f} W/m2
                                                    ---------
                                              total {par_direct + par_diffuse:8.2f} W/m2  (matches)

      NIR direct   = {nir_total:7.2f} x (1 - {fdiff:.4f})  = {nir_direct:8.2f} W/m2
      NIR diffuse  = {nir_total:7.2f} x      {fdiff:.4f}   = {nir_diffuse:8.2f} W/m2
                                                    ---------
                                              total {nir_direct + nir_diffuse:8.2f} W/m2  (matches)

      LW  direct   =    none            the sun emits nothing at 5-100 um
      LW  diffuse  = {longwave:8.2f} W/m2   the whole sky is the source""")

        # -------------------------------------------------------------------
        # STAGE 4 — exactly what radiation receives
        # -------------------------------------------------------------------
        rule("STAGE 4   WHAT RADIATION RECEIVES")
        print(f"""
    These are the literal calls stage 2 of the test will make. Every number
    traces back to a solar getter above.

      sun = radiation.addCollimatedRadiationSource(
                vec3({sun_vector.x:.5f}, {sun_vector.y:.5f}, {sun_vector.z:.5f}))   <- getSunDirectionVector()

      radiation.addRadiationBand("PAR")
      radiation.setSourceFlux(sun, "PAR", {par_direct:8.2f})      <- PAR x (1 - fdiff)
      radiation.setDiffuseRadiationFlux("PAR", {par_diffuse:8.2f})      <- PAR x fdiff

      radiation.addRadiationBand("NIR")
      radiation.setSourceFlux(sun, "NIR", {nir_direct:8.2f})      <- NIR x (1 - fdiff)
      radiation.setDiffuseRadiationFlux("NIR", {nir_diffuse:8.2f})      <- NIR x fdiff

      radiation.addRadiationBand("LW")
      radiation.setDiffuseRadiationFlux("LW",  {longwave:8.2f})      <- Prata sky longwave

    AFTER runBand() Helios writes one field per band onto EVERY leaf:
      radiation_flux_PAR      W/m2 absorbed by that primitive
      radiation_flux_NIR
      radiation_flux_LW""")

        # -------------------------------------------------------------------
        # Sanity checks on the bridge itself
        # -------------------------------------------------------------------
        rule("CHECKS ON THE BRIDGE")
        checks = [
            (abs((par_direct + par_diffuse) - par_total) < 1e-3,
             "PAR direct + diffuse adds back to the PAR total (no energy invented or lost)"),
            (abs((nir_direct + nir_diffuse) - nir_total) < 1e-3,
             "NIR direct + diffuse adds back to the NIR total"),
            (0.0 <= fdiff <= 1.0,
             f"diffuse fraction {fdiff:.4f} is within 0..1"),
            (abs(math.sqrt(sun_vector.x ** 2 + sun_vector.y ** 2 + sun_vector.z ** 2) - 1.0) < 1e-4,
             "sun direction vector has length 1"),
            (sun_vector.z > 0,
             f"sun is above the horizon (vector z = {sun_vector.z:+.5f}), so there IS a beam"),
            (par_direct > par_diffuse,
             "on a clear day the direct beam beats the diffuse sky"),
            (longwave > 250.0,
             f"sky longwave {longwave:.1f} W/m2 is physically plausible for a warm day"),
        ]
        for ok, text in checks:
            print(f"    [{'PASS' if ok else 'FAIL'}]  {text}")

        failed = sum(1 for ok, _ in checks if not ok)
        print("\n" + "-" * 74)
        if failed:
            print(f"  {failed} check(s) failed - do not proceed to stage 2 until these pass.")
        else:
            print("  Every bridge check passed. These values are ready for the radiation model.")
        print("-" * 74)

    finally:
        solar.__exit__(None, None, None)
        context.__exit__(None, None, None)

    # -------------------------------------------------------------------
    # Is the radiation half even runnable on this machine?
    # -------------------------------------------------------------------
    rule("STAGE 2 READINESS   can radiation actually run here?")
    try:
        from pyhelios.plugins.registry import get_plugin_registry
        registry = get_plugin_registry()
        available = {p: registry.is_plugin_available(p) for p in
                     ("solarposition", "radiation", "plantarchitecture", "energybalance")}
    except Exception as exc:
        print(f"\n    Could not query the plugin registry: {exc}")
        return

    print()
    for name, ok in available.items():
        print(f"    {'[ok  ]' if ok else '[MISS]'}  {name}")

    if not available.get("radiation"):
        print("""
    The radiation plugin is NOT in this build, so stage 2 cannot run.
    This is not a bug in the test - libhelios.dll was not compiled with it.

    Rebuild, then COPY THE RESULT INTO PLACE - the build writes to
    pyhelios_build/build/ but the loader reads pyhelios_build/build/lib/,
    so a successful build alone changes nothing:

        python build_scripts/build_helios.py --plugins radiation solarposition \\
               energybalance plantarchitecture visualizer weberpenntree \\
               photosynthesis stomatalconductance boundarylayerconductance leafoptics
        cp pyhelios_build/build/libhelios.dll pyhelios_build/build/lib/

    Close any running Python that imported pyhelios first, or the linker
    cannot replace the locked DLL and the build silently leaves the old one.

    Compiling the CUDA kernels takes roughly 10-30 minutes.""")
    else:
        print("""
    Radiation is available, so the numbers above can actually be ray traced:

        python tests/Full_test_SR/testing_Maize_Simulation.py

    That builds a maize canopy, hands it exactly the values printed in stage 4,
    and reports what each leaf absorbed.""")


if __name__ == "__main__":
    main()
