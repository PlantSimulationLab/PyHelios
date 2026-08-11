"""
HAPPY FLOW — drive the Solar and Radiation panels exactly as the real UI would.

===============================================================================
WHAT THIS IS
===============================================================================

The two panel designs, turned into a working test harness. Every field from the
Solar Position panel and the Radiation panel is here as a setting you can edit
or toggle, exactly as a user would in the GUI. Then you press R and the whole
pipeline runs for real:

    canopy  ->  solar  ->  the bridge  ->  ray trace  ->  flux per leaf

Three things it gives you that the other test scripts do not:

  1. TOGGLES. Flux mode flat/spectral, source type, periodic boundary, Prague
     sky, cloud calibration, per-band on/off. Change one, re-run, see what moves.

  2. PROVENANCE. Every number in the run report says where it came from and
     where it went:
         PAR direct   412.34 W/m2
           FROM  solar.getSolarFluxPAR() x (1 - getDiffuseFraction())
           TO    radiation.setSourceFlux(sunID, "PAR", ...)

  3. FAILURE REASONS. When a check fails it does not just say FAIL. It explains
     what the number means, why the bound exists, and which setting to change.

===============================================================================
HOW TO RUN
===============================================================================

    cd helios_gui/backend-api/pyhelios
    python tests/Full_test_SR/testing_HappyFlow_UI.py

FORWARD slashes, and no -m. In Git Bash a backslash escapes the next character,
and -m expects a module name rather than a file path.

===============================================================================
THE UNIT CONVERSIONS THIS DEMONSTRATES
===============================================================================

The panel shows human units. Helios wants SI. The harness holds the UI value
and converts on the way in, printing both — because getting this wrong is
silent, not fatal:

    UI shows            Helios wants          Wrong value is accepted?
    1013.2 hPa          101325 Pa             YES - inflates PAR ~27%
    26.9 C              300.0 K               no  - would throw
    50 %                0.5 fraction          no  - throws, humidity must be 0..1
    turbidity 0.05      Angstrom beta         YES - a Linke 3.0 blacks out the sun
"""

import math
import os
import sys

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")))
os.environ.setdefault("PYHELIOS_USE_PIP", "0")

from pyhelios import Context, SolarPosition  # noqa: E402
from pyhelios.wrappers.DataTypes import vec2, vec3, int2, Date, Time  # noqa: E402


# ===========================================================================
# PANEL STATE — one entry per field in the two artifacts
# ===========================================================================
# Values are in UI units. Conversion to Helios units happens in run(), so the
# conversion is visible rather than buried.
# ===========================================================================

UI = {
    # ---- Solar panel : Site -------------------------------------------
    "latitude": 38.5449,          # deg, + = north      (same as Google Maps)
    "longitude": 121.7405,        # deg, + = WEST       (INVERTED vs Google Maps)
    "utc_offset": 7.0,            # h,   + = WEST       (INVERTED vs IANA)
    "altitude_m": 16.0,           # SHOWN IN THE PANEL BUT NOT USED - see run()
    # ---- Solar panel : Date and time ----------------------------------
    "date": (2026, 6, 20),
    "time": (13, 0),
    # ---- Solar panel : Atmosphere (UI units) --------------------------
    "pressure_hPa": 1013.25,      # panel shows hPa, Helios wants Pa
    "temperature_C": 26.85,       # panel shows C,   Helios wants K
    "humidity_pct": 50.0,         # panel shows %,   Helios wants a fraction
    "turbidity_beta": 0.05,       # Angstrom beta, NOT Linke
    # ---- Solar panel : Advanced ---------------------------------------
    "prague_sky": False,          # toggle
    "ground_albedo": 0.33,
    "cloud_calibration": False,   # toggle - uses measured_ghi below, no file needed
    "measured_ghi": 700.0,        # W/m2 on a HORIZONTAL surface, as a pyranometer reads

    "spectral_irradiance": False, # toggle - SSolar-GOA curves into global data
    "turbidity_calibration": False,  # toggle - fit beta to measured irradiance
    # ---- Radiation panel : Driven by / Source -------------------------
    "driven_by": "solar",         # solar | manual
    "source_type": "collimated",  # collimated | sunsphere
    # MEASURED mode: you supply band TOTALS (what a pyranometer reports); the
    # diffuse fraction still comes from Solar Position.
    "measured_par_total": 400.0,
    "measured_nir_total": 450.0,
    # MANUAL mode: you supply the two numbers radiation actually consumes, per
    # band, exactly as the artifact's band groups show them. Nothing is derived.
    #   direct  -> radiation.setSourceFlux(sunID, band, value)
    #   diffuse -> radiation.setDiffuseRadiationFlux(band, value)
    "manual_PAR_direct": 400.0,
    "manual_PAR_diffuse": 40.0,
    "manual_NIR_direct": 450.0,
    "manual_NIR_diffuse": 45.0,
    "manual_LW_diffuse": 380.0,
    # ---- Radiation panel : Flux mode ----------------------------------
    "flux_mode": "flat",          # flat | spectral
    "source_spectrum": "solar_spectrum_direct_ASTMG173",
    "sky_spectrum": "solar_spectrum_diffuse_ASTMG173",
    # ---- Radiation panel : Bands --------------------------------------
    "band_PAR": True,
    "band_NIR": True,
    "band_LW": False,             # needs emission + temperatures; off by default
    # Wavelength window per band, nm. In FLAT mode these are only labels; in
    # SPECTRAL mode they decide what gets integrated, so a band with no range
    # silently receives zero flux.
    "lambda_PAR": (400, 700),
    "lambda_NIR": (700, 2500),
    "lambda_LW": (5000, 100000),
    "direct_rays": 100,
    "diffuse_rays": 200,
    "scatter_PAR": 2,
    "scatter_NIR": 3,
    "min_scatter_energy": 0.1,
    # ---- Radiation panel : Diffuse sky shape --------------------------
    "anisotropy_K": 0.0,          # 0 = uniform sky
    # ---- Radiation panel : Optical properties (from Materials) --------
    "twosided_flag": 1,           # 1 = absorb on both faces, 0 = front only
    "emissivity_LW": 0.98,        # only used when band LW is on
    # ---- Radiation panel : Scene --------------------------------------
    "periodic_boundary": "off",   # off | x | y | xy
    "optional_outputs": True,     # write reflectivity/transmissivity per primitive
    # ---- Radiation panel : Results ------------------------------------
    "compute_gtheta": True,       # G(theta) projection coefficient
    "compute_total_absorbed": True,
    # ---- Scene / canopy ------------------------------------------------
    "crop": "maize",
    "plants_x": 2,
    "plants_y": 2,
    "spacing": 0.75,
    "age_days": 30.0,
    "random_seed": 20260620,
}

ADVANCED = False   # toggled with 'a'; hides the rarely-used rows when False

# Leaf optics per band. Shortwave: emission off, so rho + tau may be anything
# <= 1. Longwave: emission ON, and Helios enforces eps + rho + tau == 1.
LEAF_OPTICS = {
    "PAR": dict(rho=0.10, tau=0.05),
    "NIR": dict(rho=0.45, tau=0.45),
    "LW": dict(rho=0.02, tau=0.00, emissivity=0.98),   # sums to exactly 1.0
}


# ===========================================================================
# DISPLAY
# ===========================================================================

def rule(title, char="="):
    print("\n" + char * 78)
    print(f"  {title}")
    print(char * 78)


# ---------------------------------------------------------------------------
# CONDITIONAL FIELDS
# ---------------------------------------------------------------------------
# A real panel reveals a field the moment the mode needing it is selected:
# choose "manual" and the direct/diffuse boxes appear, switch to "spectral" and
# the spectrum pickers appear. Without this, a field tagged "advanced" stays
# hidden even after you pick the mode that requires it - which is the dead end
# behind "I shifted to manual and there is nowhere to type the flux".
#
# Relevance overrides the advanced flag in BOTH directions: a field its mode
# needs is always shown, and a field its mode ignores is always hidden, because
# editing it would change nothing.
RELEVANT_WHEN = {
    # MEASURED: band totals typed in, diffuse fraction still from Solar.
    "measured_par_total": lambda: UI["driven_by"] == "measured" and UI["band_PAR"],
    "measured_nir_total": lambda: UI["driven_by"] == "measured" and UI["band_NIR"],
    # MANUAL: the two numbers radiation actually consumes, per band.
    "manual_PAR_direct": lambda: UI["driven_by"] == "manual" and UI["band_PAR"],
    "manual_PAR_diffuse": lambda: UI["driven_by"] == "manual" and UI["band_PAR"],
    "manual_NIR_direct": lambda: UI["driven_by"] == "manual" and UI["band_NIR"],
    "manual_NIR_diffuse": lambda: UI["driven_by"] == "manual" and UI["band_NIR"],
    "manual_LW_diffuse": lambda: UI["driven_by"] == "manual" and UI["band_LW"],
    # Mode- and band-dependent fields elsewhere in the panel.
    "source_spectrum": lambda: UI["flux_mode"] == "spectral",
    "sky_spectrum": lambda: UI["flux_mode"] == "spectral",
    "measured_ghi": lambda: UI["cloud_calibration"],
    "ground_albedo": lambda: UI["prague_sky"],
    "emissivity_LW": lambda: UI["band_LW"],
    "lambda_PAR": lambda: UI["band_PAR"],
    "lambda_NIR": lambda: UI["band_NIR"],
    "lambda_LW": lambda: UI["band_LW"],
    "scatter_PAR": lambda: UI["band_PAR"],
    "scatter_NIR": lambda: UI["band_NIR"],
}


def _format_row(key, label, note):
    """Render one field as a panel line."""
    value = UI[key]
    if isinstance(value, bool):
        shown = "[ON ]" if value else "[off]"
    elif isinstance(value, tuple):
        shown = ", ".join(str(v) for v in value)
    else:
        shown = str(value)
    return f"  {label:<26} {shown:<34} {note}"


def row(key, label, note="", advanced=False):
    """One panel row. Returns the printable line, or None if hidden."""
    if key in RELEVANT_WHEN:
        return _format_row(key, label, note) if RELEVANT_WHEN[key]() else None
    if advanced and not ADVANCED:
        return None
    return _format_row(key, label, note)


# Menu layout: (key, label, note, advanced). None key = section header.
PANEL = [
    (None, "SOLAR POSITION PANEL", "", False),
    ("latitude", "Latitude", "deg, + = north", False),
    ("longitude", "Longitude", "deg, + = WEST (inverted!)", False),
    ("utc_offset", "UTC offset", "h, + = WEST (inverted!)", False),
    ("altitude_m", "Altitude", "m - NOT USED BY HELIOS", False),
    ("date", "Date", "year-month-day", False),
    ("time", "Time", "hour:minute, local", False),
    ("pressure_hPa", "Pressure", "hPa -> converted to Pa", False),
    ("temperature_C", "Temperature", "C -> converted to K", False),
    ("humidity_pct", "Humidity", "% -> converted to fraction", False),
    ("turbidity_beta", "Turbidity beta", "Angstrom, NOT Linke", False),
    ("prague_sky", "Prague sky model", "ADV - needs a dataset file", True),
    ("ground_albedo", "Ground albedo", "ADV - Prague input", True),
    ("cloud_calibration", "Cloud calibration", "ADV - uses constant below", True),
    ("measured_ghi", "Measured GHI", "ADV - W/m2 horizontal", True),
    ("spectral_irradiance", "Spectral irradiance", "ADV - SSolar-GOA curves", True),
    ("turbidity_calibration", "Turbidity calibration", "ADV - fit beta to measured", True),

    (None, "RADIATION PANEL", "", False),
    ("driven_by", "Driven by", "solar | manual", False),
    ("source_type", "Source type", "collimated | sunsphere", False),
    ("flux_mode", "Flux mode", "flat | spectral", False),
    ("band_PAR", "Band PAR", "400-700 nm", False),
    ("band_NIR", "Band NIR", "700-2500 nm", False),
    ("band_LW", "Band LW", "5-100 um, emission ON", False),
    ("lambda_PAR", "PAR wavelengths", "nm, min,max", True),
    ("lambda_NIR", "NIR wavelengths", "nm, min,max", True),
    ("lambda_LW", "LW wavelengths", "nm, min,max", True),
    ("direct_rays", "Direct rays", "per primitive", False),
    ("diffuse_rays", "Diffuse rays", "biggest GPU cost", False),
    ("scatter_PAR", "Scatter depth PAR", "0 = rho/tau ignored", False),
    ("scatter_NIR", "Scatter depth NIR", "NIR needs more bounces", False),
    ("anisotropy_K", "Anisotropy K", "0 = uniform sky", True),
    ("twosided_flag", "Two-sided flag", "1 = both faces, 0 = front", True),
    ("emissivity_LW", "Emissivity LW", "eps+rho+tau must = 1", True),
    ("periodic_boundary", "Periodic boundary", "off | x | y | xy", True),
    ("optional_outputs", "Optional outputs", "write rho/tau per primitive", True),
    ("compute_gtheta", "Compute G(theta)", "projection coefficient", True),
    ("compute_total_absorbed", "Total absorbed", "sum across all bands", True),
    ("min_scatter_energy", "Min scatter energy", "cutoff", True),
    ("source_spectrum", "Source spectrum", "spectral mode only", True),
    ("sky_spectrum", "Sky spectrum", "spectral mode only", True),
    ("measured_par_total", "PAR total measured", "W/m2 beam-normal", True),
    ("measured_nir_total", "NIR total measured", "W/m2 beam-normal", True),
    ("manual_PAR_direct", "PAR direct flux", "-> setSourceFlux", True),
    ("manual_PAR_diffuse", "PAR diffuse flux", "-> setDiffuseRadiationFlux", True),
    ("manual_NIR_direct", "NIR direct flux", "-> setSourceFlux", True),
    ("manual_NIR_diffuse", "NIR diffuse flux", "-> setDiffuseRadiationFlux", True),
    ("manual_LW_diffuse", "LW diffuse flux", "-> setDiffuseRadiationFlux", True),

    (None, "SCENE", "", False),
    ("crop", "Crop", "maize, soybean, tomato...", False),
    ("plants_x", "Plants X", "canopy size", False),
    ("plants_y", "Plants Y", "canopy size", False),
    ("spacing", "Plant spacing", "m", False),
    ("age_days", "Plant age", "days", False),
    ("random_seed", "Random seed", "pins the canopy", True),
]


def show_panel():
    index = {}
    n = 0
    for key, label, note, adv in PANEL:
        if key is None:
            rule(label, "-")
            continue
        line = row(key, label, note, adv)
        if line is None:
            continue
        n += 1
        index[str(n)] = key
        print(f"{n:>4}.{line}")
    return index


# ===========================================================================
# EDITING
# ===========================================================================

TOGGLES = {"prague_sky", "cloud_calibration", "spectral_irradiance",
           "turbidity_calibration", "band_PAR", "band_NIR", "band_LW",
           "optional_outputs", "compute_gtheta", "compute_total_absorbed"}
CHOICES = {
    # Three modes, matching the artifact's segmented control:
    #   solar    everything from Solar Position
    #   measured you supply the FLUX, Solar still supplies the sun DIRECTION
    #   manual   you supply both
    "driven_by": ["solar", "measured", "manual"],
    "source_type": ["collimated", "sunsphere"],
    "flux_mode": ["flat", "spectral"],
    "periodic_boundary": ["off", "x", "y", "xy"],
    "crop": ["maize", "soybean", "tomato", "strawberry", "wheat", "rice",
             "sorghum", "cowpea", "bean", "butterlettuce"],
}


def edit(key):
    """Edit one field, respecting its type. Toggles flip, choices cycle."""
    current = UI[key]

    if key in TOGGLES:
        UI[key] = not current
        print(f"    {key} -> {'ON' if UI[key] else 'off'}")
        return

    if key in CHOICES:
        options = CHOICES[key]
        print(f"    options: {' | '.join(options)}")
        raw = input(f"    new value [{current}]: ").strip()
        if raw == "":
            return
        if raw not in options:
            print(f"    '{raw}' is not one of them; unchanged.")
            return
        UI[key] = raw
        return

    if isinstance(current, tuple):
        raw = input(f"    new value as comma list [{','.join(map(str, current))}]: ").strip()
        if raw == "":
            return
        try:
            UI[key] = tuple(int(p) for p in raw.split(","))
        except ValueError:
            print("    not a list of whole numbers; unchanged.")
        return

    raw = input(f"    new value [{current}]: ").strip()
    if raw == "":
        return
    try:
        UI[key] = type(current)(raw) if not isinstance(current, str) else raw
    except ValueError:
        print(f"    '{raw}' is not a {type(current).__name__}; unchanged.")


# ===========================================================================
# THE RUN
# ===========================================================================

import contextlib  # noqa: E402


@contextlib.contextmanager
def assets_cwd():
    """Run inside pyhelios_build/build, where the plugin assets were staged.

    The SSolar-GOA spectrum functions open their data with a RELATIVE path:
        plugins/solarposition/ssolar_goa/wehrli.dat
    so they only work when that path resolves from the current directory. The
    build stages the assets under pyhelios_build/build, so we chdir there for
    the duration of the call and restore afterwards.

    Your backend will need the same trick, or an absolute-path fix upstream.
    """
    here = os.getcwd()
    staged = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "pyhelios_build", "build"))
    if os.path.isdir(staged):
        os.chdir(staged)
    try:
        yield
    finally:
        os.chdir(here)


# ===========================================================================
# DIAGNOSTICS  -  which optional features work on THIS machine, and why not
# ===========================================================================

def diagnostics():
    """Probe every optional feature and report OK / FAIL with the reason.

    This exists because "advanced" options fail for environmental reasons -
    a missing data file, an absent timeseries, a plugin left out of the build -
    not because of anything wrong with your inputs. Knowing which ones are
    usable before you design UI around them saves building a toggle that can
    never be switched on.
    """
    rule("FEATURE DIAGNOSTICS   what works on this machine")
    results = []

    def probe(group, name, fn, fix=""):
        try:
            value = fn()
            results.append((group, name, True, str(value)[:52] if value is not None else "", ""))
        except Exception as exc:
            msg = str(exc).split(":")[-1].strip()
            results.append((group, name, False, msg[:80], fix))

    # ---- plugins present at all --------------------------------------
    from pyhelios.plugins.registry import get_plugin_registry
    registry = get_plugin_registry()
    for plugin in ("solarposition", "radiation", "plantarchitecture",
                   "energybalance", "visualizer"):
        ok = registry.is_plugin_available(plugin)
        results.append(("PLUGIN", plugin, ok, "" if ok else "not compiled into libhelios.dll",
                        "" if ok else "rebuild with --plugins including it, then copy "
                                      "pyhelios_build/build/libhelios.dll into build/lib/"))

    # ---- solar core --------------------------------------------------
    context = Context()
    context.setDate(*UI["date"])
    context.setTime(*UI["time"])
    solar = SolarPosition(context, utc_offset=UI["utc_offset"],
                          latitude=UI["latitude"], longitude=UI["longitude"])
    solar.setAtmosphericConditions(UI["pressure_hPa"] * 100.0,
                                   UI["temperature_C"] + 273.15,
                                   UI["humidity_pct"] / 100.0,
                                   UI["turbidity_beta"])

    probe("SOLAR", "sun angles", lambda: f"{math.degrees(solar.getSunElevation()):.2f} deg elev")
    probe("SOLAR", "sun direction vector", lambda: "unit vec3"
          if abs(math.sqrt(sum(c ** 2 for c in (solar.getSunDirectionVector().x,
                                                solar.getSunDirectionVector().y,
                                                solar.getSunDirectionVector().z))) - 1) < 1e-4
          else "NOT unit length")
    probe("SOLAR", "sunrise / sunset",
          lambda: f"{solar.getSunriseTime().hour:02d}:{solar.getSunriseTime().minute:02d}"
                  f" - {solar.getSunsetTime().hour:02d}:{solar.getSunsetTime().minute:02d}")
    probe("SOLAR", "Gueymard flux PAR/NIR",
          lambda: f"{solar.getSolarFluxPAR():.1f} / {solar.getSolarFluxNIR():.1f} W/m2")
    probe("SOLAR", "diffuse fraction", lambda: f"{solar.getDiffuseFraction():.4f}")
    probe("SOLAR", "Prata sky longwave", lambda: f"{solar.getAmbientLongwaveFlux():.1f} W/m2")

    # ---- solar advanced ----------------------------------------------
    probe("SOLAR ADV", "Prague sky model", lambda: solar.enablePragueSkyModel() or "enabled",
          "The PragueSkyModelReduced.dat dataset is not shipped with this build. "
          "Either obtain it and place it under plugins/solarposition/lib/prague_sky_model/, "
          "or hide this toggle in the GUI.")

    def _spectra():
        with assets_cwd():
            solar.calculateDirectSolarSpectrum("diag_direct", 5.0)
            solar.calculateDiffuseSolarSpectrum("diag_diffuse", 5.0)
            solar.calculateGlobalSolarSpectrum("diag_global", 5.0)
        return "3 curves written to global data"
    probe("SOLAR ADV", "spectral irradiance (SSolar-GOA)", _spectra,
          "These open wehrli.dat with a RELATIVE path, so they only work when the "
          "working directory is pyhelios_build/build. This harness handles it with "
          "assets_cwd(); your backend must do the same or resolve the path absolutely.")

    probe("SOLAR ADV", "cloud calibration",
          lambda: solar.enableCloudCalibration("ghi") or "enabled",
          "Needs measured irradiance loaded as a Context timeseries first. Grey this "
          "toggle out in the GUI until weather data with a GHI column is loaded.")
    probe("SOLAR ADV", "turbidity calibration",
          lambda: solar.calibrateTurbidityFromTimeseries("ghi") or "calibrated",
          "Same dependency as cloud calibration - it needs a measured irradiance "
          "timeseries to fit beta against.")

    # ---- radiation ----------------------------------------------------
    try:
        from pyhelios.RadiationModel import RadiationModel
        radiation = RadiationModel(context)
        band = "diag"
        radiation.addRadiationBand(band, 400, 700)
        src = radiation.addCollimatedRadiationSource(solar.getSunDirectionVector())

        probe("RADIATION", "collimated source", lambda: f"source id {src}")
        probe("RADIATION", "sun sphere source",
              lambda: f"source id {radiation.addSunSphereRadiationSource(0.5, solar.getSunZenith(), solar.getSunAzimuth())}",
              "")
        probe("RADIATION", "disable emission", lambda: radiation.disableEmission(band) or "ok")
        probe("RADIATION", "scattering depth", lambda: radiation.setScatteringDepth(band, 2) or "ok")
        probe("RADIATION", "anisotropic sky (K)",
              lambda: radiation.setDiffuseRadiationExtinctionCoeff(
                  band, 0.1, solar.getSunDirectionVector()) or "ok")
        probe("RADIATION", "periodic boundary xy",
              lambda: radiation.enforcePeriodicBoundary("xy") or "ok",
              "Only 'x', 'y' and 'xy' are accepted; anything else warns and is ignored. "
              "There is no way to switch it back off once set on a model instance.")
        probe("RADIATION ADV", "source spectrum (ASTM)",
              lambda: radiation.setSourceSpectrum(src, "solar_spectrum_direct_ASTMG173") or "ok",
              "")
        probe("RADIATION ADV", "diffuse spectrum (ASTM)",
              lambda: radiation.setDiffuseSpectrum(band, "solar_spectrum_diffuse_ASTMG173") or "ok",
              "")
        probe("RADIATION ADV", "getSkyEnergy",
              lambda: f"{radiation.getSkyEnergy():.3f}  (0 means never populated)",
              "")
    except Exception as exc:
        results.append(("RADIATION", "model construction", False, str(exc)[:80],
                        "The radiation plugin is missing from the build."))

    context.__exit__(None, None, None)

    # ---- report -------------------------------------------------------
    current = None
    failures = 0
    for group, name, ok, detail, fix in results:
        if group != current:
            current = group
            print(f"\n  {group}")
        mark = "OK  " if ok else "FAIL"
        print(f"    [{mark}]  {name:<34} {detail}")
        if not ok:
            failures += 1
            if fix:
                for line in _wrap(fix, 62):
                    print(f"             {line}")

    print("\n" + "-" * 78)
    print(f"  {len(results) - failures} of {len(results)} features usable. "
          f"{failures} unavailable - reasons above.")
    print("  Features marked FAIL are environment problems, not input errors:")
    print("  a missing data file, an absent timeseries, or a plugin left out of the build.")
    print("-" * 78)


class Trace:
    """Collects provenance lines and check results for the report."""

    def __init__(self):
        self.values = []   # (name, value, unit, came_from, went_to)
        self.checks = []   # (ok, statement, why_it_matters)
        self.notes = []    # advisory messages, e.g. a toggle that could not apply

    def value(self, name, value, unit, came_from, went_to=""):
        self.values.append((name, value, unit, came_from, went_to))

    def check(self, ok, statement, why):
        self.checks.append((ok, statement, why))

    def note(self, text):
        self.notes.append(text)


def run():
    trace = Trace()
    active_bands = [b for b in ("PAR", "NIR", "LW") if UI[f"band_{b}"]]

    if not active_bands:
        print("\n  No bands are enabled. Turn on at least one and run again.")
        return

    # ---- unit conversion, made visible -------------------------------
    pressure_Pa = UI["pressure_hPa"] * 100.0
    temperature_K = UI["temperature_C"] + 273.15
    humidity_frac = UI["humidity_pct"] / 100.0

    rule("UNIT CONVERSION   panel units -> Helios units")
    print(f"""
    Pressure      {UI['pressure_hPa']:>10.2f} hPa   x100      ->  {pressure_Pa:>10.1f} Pa
    Temperature   {UI['temperature_C']:>10.2f} C     +273.15   ->  {temperature_K:>10.2f} K
    Humidity      {UI['humidity_pct']:>10.1f} %     /100      ->  {humidity_frac:>10.3f} fraction
    Turbidity     {UI['turbidity_beta']:>10.3f}       none      ->  {UI['turbidity_beta']:>10.3f} Angstrom beta

    The panel must do these three conversions. Helios validates humidity
    (0..1) and would throw on 50, but it accepts 1013 Pa without complaint,
    which is why pressure is the dangerous one.""")

    context = Context()
    context.seedRandomGenerator(UI["random_seed"])
    context.setDate(*UI["date"])
    context.setTime(*UI["time"])

    try:
        # ---- canopy --------------------------------------------------
        rule("STEP 1   BUILD THE CANOPY")
        from pyhelios.PlantArchitecture import PlantArchitecture
        plantarch = PlantArchitecture(context)
        plantarch.loadPlantModelFromLibrary(UI["crop"])
        plant_ids = plantarch.buildPlantCanopyFromLibrary(
            canopy_center=vec3(0.0, 0.0, 0.0),
            plant_spacing=vec2(UI["spacing"], UI["spacing"]),
            plant_count=int2(UI["plants_x"], UI["plants_y"]),
            age=UI["age_days"],
        )
        leaf_objects = []
        for pid in plant_ids:
            leaf_objects.extend(plantarch.getPlantLeafObjectIDs(pid))
        leaf_uuids = context.getObjectPrimitiveUUIDs(leaf_objects)
        areas = [context.getPrimitiveArea(u) for u in leaf_uuids]
        leaf_area = sum(areas)
        ground_area = (UI["plants_x"] * UI["spacing"]) * (UI["plants_y"] * UI["spacing"])

        print(f"""
    Crop / plants     {UI['crop']}, {UI['plants_x']}x{UI['plants_y']} = {len(plant_ids)}
    Leaf primitives   {len(leaf_uuids)}
    Leaf area         {leaf_area:.3f} m2   over {ground_area:.2f} m2 ground
    Leaf area index   {leaf_area / ground_area:.2f}
    Seed              {UI['random_seed']}   (same seed -> same canopy)""")

        # ---- optics --------------------------------------------------
        # twosided_flag decides whether a primitive absorbs on both faces.
        # Default 1 = both. A leaf absorbing from both sides is right; a ground
        # plane absorbing from underneath is not, which is why the flag exists.
        # It must be an UNSIGNED INT, not a float - the wrong type is ignored.
        context.setPrimitiveDataUInt(leaf_uuids, "twosided_flag", int(UI["twosided_flag"]))
        trace.value("twosided_flag", UI["twosided_flag"], "",
                    "UI twosided_flag (uint, NOT float)",
                    'context.setPrimitiveDataUInt(uuids, "twosided_flag", ...)')

        for band in active_bands:
            optics = LEAF_OPTICS[band]
            context.setPrimitiveDataFloat(leaf_uuids, f"reflectivity_{band}", optics["rho"])
            context.setPrimitiveDataFloat(leaf_uuids, f"transmissivity_{band}", optics["tau"])
            if band == "LW":
                context.setPrimitiveDataFloat(leaf_uuids, "emissivity_LW", UI["emissivity_LW"])
            trace.value(f"{band} leaf rho / tau",
                        f"{optics['rho']:.2f} / {optics['tau']:.2f}", "",
                        "LEAF_OPTICS in this file",
                        f'context.setPrimitiveData(uuid, "reflectivity_{band}", ...)')

        # ---- solar ---------------------------------------------------
        rule("STEP 2   SOLAR POSITION")
        solar = SolarPosition(context, utc_offset=UI["utc_offset"],
                              latitude=UI["latitude"], longitude=UI["longitude"])
        solar.setAtmosphericConditions(pressure_Pa, temperature_K,
                                       humidity_frac, UI["turbidity_beta"])

        # advanced toggles, each reporting honestly if it cannot apply
        if UI["prague_sky"]:
            try:
                solar.enablePragueSkyModel()
                solar.updatePragueSkyModel(UI["ground_albedo"])
                trace.note("Prague sky model ENABLED.")
            except Exception as exc:
                trace.note(f"Prague sky model requested but could NOT be enabled.\n"
                           f"        {str(exc).split(':')[-1].strip()[:110]}\n"
                           f"        The dataset file is not shipped with this build. The "
                           f"toggle should be disabled in the GUI unless the file is present.")
        if UI["cloud_calibration"]:
            # NO WEATHER FILE NEEDED. Cloud calibration only requires a Context
            # timeseries to exist, so we synthesise a single constant point at
            # the current date/time. That is enough to exercise the whole code
            # path and watch it change the numbers.
            try:
                clear_par = solar.getSolarFluxPAR()
                clear_nir = solar.getSolarFluxNIR()
                clear_fd = solar.getDiffuseFraction()
                # cos(zenith) computed locally: the shared cos_zenith is set
                # further down, after this advanced-toggle block runs.
                clear_horiz = solar.getSolarFlux() * math.cos(solar.getSunZenith())

                context.addTimeseriesData(
                    "ghi", UI["measured_ghi"],
                    Date(UI["date"][0], UI["date"][1], UI["date"][2]),
                    Time(UI["time"][0], UI["time"][1], 0))
                solar.enableCloudCalibration("ghi")

                cal_par = solar.getSolarFluxPAR()
                cal_nir = solar.getSolarFluxNIR()
                cal_fd = solar.getDiffuseFraction()

                trace.note(
                    f"Cloud calibration ON, using a synthetic constant instead of a file.\n"
                    f"        measured GHI {UI['measured_ghi']:.0f} W/m2 horizontal vs "
                    f"clear-sky {clear_horiz:.0f} W/m2\n"
                    f"        PAR   {clear_par:7.2f} -> {cal_par:7.2f} W/m2\n"
                    f"        NIR   {clear_nir:7.2f} -> {cal_nir:7.2f} W/m2\n"
                    f"        fdiff {clear_fd:7.4f} -> {cal_fd:7.4f}")

                if abs(cal_par - cal_nir) < 0.01:
                    trace.note(
                        "BUG IN HELIOS - PAR and NIR came back IDENTICAL after calibration.\n"
                        "        applyCloudCalibration computes\n"
                        "            R = R_calc * R_meas / (R_calc * cos(zenith))\n"
                        "        in which R_calc cancels out, leaving R = R_meas / cos(zenith)\n"
                        "        for EVERY band. The PAR/NIR split is destroyed and both bands\n"
                        "        return the broadband value, so total shortwave is roughly\n"
                        "        doubled downstream.\n"
                        "        SolarPosition.cpp:566-569. Do not ship cloud calibration with\n"
                        "        band-split radiation until this is fixed upstream.")
            except Exception as exc:
                trace.note(f"Cloud calibration could NOT be enabled.\n"
                           f"        {str(exc).split(':')[-1].strip()[:110]}")
        if UI["turbidity_calibration"]:
            try:
                solar.calibrateTurbidityFromTimeseries("ghi")
                trace.note("Turbidity beta re-fitted against timeseries 'ghi'.")
            except Exception as exc:
                trace.note(f"Turbidity calibration requested but could NOT run.\n"
                           f"        {str(exc).split(':')[-1].strip()[:110]}\n"
                           f"        Same dependency as cloud calibration: it fits beta to a "
                           f"measured irradiance series, so one must be loaded first.")
        if UI["spectral_irradiance"]:
            try:
                with assets_cwd():
                    solar.calculateDirectSolarSpectrum("sun_direct_spectrum", 5.0)
                    solar.calculateDiffuseSolarSpectrum("sun_diffuse_spectrum", 5.0)
                    solar.calculateGlobalSolarSpectrum("sun_global_spectrum", 5.0)
                trace.note("SSolar-GOA spectra written to global data as "
                           "sun_direct_spectrum / sun_diffuse_spectrum / sun_global_spectrum. "
                           "Set 'Source spectrum' to one of these to drive spectral mode from "
                           "THIS site's atmosphere instead of the fixed ASTM reference.")
            except Exception as exc:
                trace.note(f"Spectral irradiance requested but could NOT run.\n"
                           f"        {str(exc).split(':')[-1].strip()[:110]}\n"
                           f"        These read wehrli.dat via a RELATIVE path, so they only "
                           f"work with the working directory set to pyhelios_build/build.")

        zenith = solar.getSunZenith()
        sun_vector = solar.getSunDirectionVector()
        trace.value("Sun elevation", f"{math.degrees(solar.getSunElevation()):.3f}", "deg",
                    "solar.getSunElevation()  [returns RADIANS]", "display only")
        trace.value("Sun zenith", f"{math.degrees(zenith):.3f}", "deg",
                    "solar.getSunZenith()", "used for the horizontal projection")
        trace.value("Sun vector", f"({sun_vector.x:+.4f},{sun_vector.y:+.4f},{sun_vector.z:+.4f})", "",
                    "solar.getSunDirectionVector()",
                    "radiation.addCollimatedRadiationSource(...)")

        # THREE-WAY DRIVEN-BY, matching the artifact's segmented control.
        #
        #   solar     direction AND flux from Solar Position
        #   measured  flux typed by the user (from a pyranometer), but the sun
        #             DIRECTION still computed by Solar Position. This is the
        #             common real-world case and it is easy to forget it exists.
        #   manual    both typed; Solar Position contributes nothing.
        if UI["driven_by"] == "solar":
            par_total = solar.getSolarFluxPAR()
            nir_total = solar.getSolarFluxNIR()
            fdiff = solar.getDiffuseFraction()
            src_par, src_nir, src_fd = ("solar.getSolarFluxPAR()",
                                        "solar.getSolarFluxNIR()",
                                        "solar.getDiffuseFraction()")
        elif UI["driven_by"] == "measured":
            par_total, nir_total = UI["measured_par_total"], UI["measured_nir_total"]
            fdiff = solar.getDiffuseFraction()
            src_par = src_nir = "measured band total typed by the user"
            src_fd = "solar.getDiffuseFraction()  (still from Solar Position)"
            trace.note("driven_by = measured: the band TOTAL is yours, but the sun DIRECTION "
                       "and the diffuse FRACTION still come from Solar Position, so the "
                       "direct/diffuse split is still computed. Use this with a pyranometer.")
        else:
            # MANUAL: nothing is derived. You type the two numbers radiation
            # actually consumes, per band, so there is no split step at all and
            # no diffuse fraction anywhere in the chain.
            par_total = nir_total = None
            fdiff = None
            src_par = src_nir = src_fd = "not used - manual mode types direct/diffuse directly"
            trace.note("driven_by = manual: no split happens. The direct and diffuse boxes go "
                       "straight to setSourceFlux and setDiffuseRadiationFlux, so Solar "
                       "Position contributes only the sun DIRECTION. Nothing here is derived, "
                       "which also means nothing checks that your two numbers are consistent.")

        # Values the artifact shows in its 'Incoming from Solar' readout but
        # which the pipeline does not otherwise surface.
        cos_zenith = math.cos(zenith)
        sunrise, sunset = solar.getSunriseTime(), solar.getSunsetTime()
        trace.value("cos(zenith)", f"{cos_zenith:.4f}", "",
                    "math.cos(solar.getSunZenith())",
                    "projects beam-normal onto flat ground (checks only)")
        trace.value("Global shortwave", f"{solar.getSolarFlux():.2f}", "W/m2 beam-normal",
                    "solar.getSolarFlux()  [PAR + NIR combined]",
                    "not sent to radiation - shown for cross-checking PAR+NIR")
        trace.value("Sunrise / sunset",
                    f"{sunrise.hour:02d}:{sunrise.minute:02d} - {sunset.hour:02d}:{sunset.minute:02d}",
                    "local",
                    "solar.getSunriseTime() / getSunsetTime()", "display only")

        # The artifact has an Altitude field. Helios does not accept one.
        trace.note(f"Altitude {UI['altitude_m']} m is in the panel but NOT passed to Helios - "
                   f"SolarPosition's constructor takes only (context, utc_offset, latitude, "
                   f"longitude). Altitude affects air mass in reality, and here it is folded "
                   f"into the PRESSURE you supply instead. Either drop the field from the GUI "
                   f"or use it to auto-compute pressure.")

        longwave = solar.getAmbientLongwaveFlux()

        if UI["driven_by"] == "manual":
            # Typed straight through. No total, no fraction, no split.
            flux = {
                "PAR": dict(direct=UI["manual_PAR_direct"], diffuse=UI["manual_PAR_diffuse"]),
                "NIR": dict(direct=UI["manual_NIR_direct"], diffuse=UI["manual_NIR_diffuse"]),
                "LW": dict(direct=0.0, diffuse=UI["manual_LW_diffuse"]),
            }
            for band in ("PAR", "NIR", "LW"):
                if band != "LW":
                    trace.value(f"{band} direct", f"{flux[band]['direct']:.2f}", "W/m2",
                                f"UI manual_{band}_direct   <- typed, nothing derived",
                                f'radiation.setSourceFlux(sunID, "{band}", ...)')
                trace.value(f"{band} diffuse", f"{flux[band]['diffuse']:.2f}", "W/m2",
                            f"UI manual_{band}_diffuse  <- typed, nothing derived",
                            f'radiation.setDiffuseRadiationFlux("{band}", ...)')
            trace.value("Sky longwave", f"{longwave:.2f}", "W/m2",
                        "solar.getAmbientLongwaveFlux()  [computed but NOT used in manual mode]",
                        "ignored - the LW diffuse box overrides it")
        else:
            flux = {
                "PAR": dict(direct=par_total * (1 - fdiff), diffuse=par_total * fdiff),
                "NIR": dict(direct=nir_total * (1 - fdiff), diffuse=nir_total * fdiff),
                "LW": dict(direct=0.0, diffuse=longwave),
            }
            trace.value("PAR total", f"{par_total:.2f}", "W/m2 beam-normal", src_par, "split below")
            trace.value("NIR total", f"{nir_total:.2f}", "W/m2 beam-normal", src_nir, "split below")
            trace.value("Diffuse fraction", f"{fdiff:.4f}", "", src_fd, "splits both bands")
            trace.value("Sky longwave", f"{longwave:.2f}", "W/m2",
                        "solar.getAmbientLongwaveFlux()  [Prata 1996]",
                        'radiation.setDiffuseRadiationFlux("LW", ...)')
            for band in ("PAR", "NIR"):
                trace.value(f"{band} direct", f"{flux[band]['direct']:.2f}", "W/m2",
                            f"{band} total x (1 - fdiff)   <- YOUR CODE, not Helios",
                            f'radiation.setSourceFlux(sunID, "{band}", ...)')
                trace.value(f"{band} diffuse", f"{flux[band]['diffuse']:.2f}", "W/m2",
                            f"{band} total x fdiff         <- YOUR CODE, not Helios",
                            f'radiation.setDiffuseRadiationFlux("{band}", ...)')

        # ---- radiation ------------------------------------------------
        rule("STEP 3   RADIATION MODEL")
        from pyhelios.RadiationModel import RadiationModel
        radiation = RadiationModel(context)

        if UI["source_type"] == "collimated":
            sun_id = radiation.addCollimatedRadiationSource(sun_vector)
            source_note = "addCollimatedRadiationSource(sun_vector)  parallel beam, sun at infinity"
        else:
            sun_id = radiation.addSunSphereRadiationSource(
                0.5, zenith, solar.getSunAzimuth())
            source_note = ("addSunSphereRadiationSource(radius, zenith, azimuth)  "
                           "finite disc, gives soft shadow edges")
        trace.value("Source", source_note, "", "UI source_type toggle", "")

        # SPECTRAL SETUP HAPPENS ONCE, OUTSIDE THE BAND LOOP.
        #
        # setSourceSpectrumIntegral rescales the ENTIRE stored curve, even the
        # 4-argument form that takes a wavelength window. So calling it per band
        # means the second call silently overwrites the first:
        #
        #     setSourceSpectrumIntegral(sun, PAR_direct)   # scales whole curve
        #     setSourceSpectrumIntegral(sun, NIR_direct)   # scales it AGAIN
        #
        # That is why it is called once here, with the shortwave TOTAL. The
        # per-band split then falls out of integrating the curve over each
        # band's wavelength window.
        #
        # NOTE A REAL MODELLING DIFFERENCE: in flat mode the PAR/NIR split comes
        # from Gueymard's separate PAR and NIR values. In spectral mode it comes
        # from the SHAPE of the ASTM curve. The two will not agree exactly, and
        # that is expected, not a bug.
        if UI["flux_mode"] == "spectral":
            shortwave_direct = sum(flux[b]["direct"] for b in active_bands if b != "LW")
            radiation.setSourceSpectrum(sun_id, UI["source_spectrum"])
            radiation.setSourceSpectrumIntegral(sun_id, shortwave_direct)
            trace.value("Spectral source", UI["source_spectrum"], "",
                        "UI source_spectrum (a curve from solar_spectrum_ASTMG173.xml)",
                        "radiation.setSourceSpectrum(sunID, label)")
            trace.value("Spectral integral", f"{shortwave_direct:.2f}", "W/m2 total shortwave",
                        "sum of PAR direct + NIR direct   <- ONE call, not per band",
                        "radiation.setSourceSpectrumIntegral(sunID, total)")

        for band in active_bands:
            lo, hi = UI[f"lambda_{band}"]
            radiation.addRadiationBand(band, lo, hi)
            trace.value(f"{band} wavelengths", f"{lo} - {hi}", "nm",
                        f"UI lambda_{band}",
                        f'radiation.addRadiationBand("{band}", {lo}, {hi})')

            if UI["flux_mode"] == "flat":
                radiation.setSourceFlux(sun_id, band, flux[band]["direct"])
                radiation.setDiffuseRadiationFlux(band, flux[band]["diffuse"])
            else:
                # The source spectrum is already set and scaled. Per band we
                # only need the sky curve and its magnitude; the direct flux is
                # derived by integrating the source curve over [lo, hi].
                radiation.setDiffuseSpectrum(band, UI["sky_spectrum"])
                radiation.setDiffuseRadiationFlux(band, flux[band]["diffuse"])

            # Emission belongs only on longwave: a 300 K leaf radiates thermal
            # infrared, not visible or NIR light. Leaving it on for shortwave
            # breaks Helios's eps + rho + tau == 1 rule and aborts runBand().
            if band == "LW":
                radiation.enableEmission(band)
            else:
                radiation.disableEmission(band)

            radiation.setDirectRayCount(band, UI["direct_rays"])
            radiation.setDiffuseRayCount(band, UI["diffuse_rays"])
            radiation.setMinScatterEnergy(band, UI["min_scatter_energy"])
            depth = {"PAR": UI["scatter_PAR"], "NIR": UI["scatter_NIR"], "LW": 1}[band]
            radiation.setScatteringDepth(band, depth)

            if UI["anisotropy_K"] > 0:
                radiation.setDiffuseRadiationExtinctionCoeff(
                    band, UI["anisotropy_K"], sun_vector)

            trace.value(f"{band} rays / depth",
                        f"{UI['direct_rays']} direct, {UI['diffuse_rays']} diffuse, depth {depth}",
                        "", "UI ray settings",
                        f'setDirectRayCount / setDiffuseRayCount / setScatteringDepth("{band}")')

        if UI["periodic_boundary"] != "off":
            radiation.enforcePeriodicBoundary(UI["periodic_boundary"])
            trace.note(f"Periodic boundary '{UI['periodic_boundary']}' enabled - the plot "
                       f"now behaves as an infinite field, removing edge effects. NOTE there "
                       f"is no way to switch this back off on the same model instance.")

        # Optional outputs: ask Helios to write the resolved rho/tau back as
        # primitive data, so you can inspect what it ACTUALLY used rather than
        # what you thought you set. This is how you catch the scattering-depth-0
        # override, where your values are silently replaced by a blackbody.
        if UI["optional_outputs"]:
            for band in active_bands:
                radiation.optionalOutputPrimitiveData(f"reflectivity_{band}")
                radiation.optionalOutputPrimitiveData(f"transmissivity_{band}")
            trace.value("Optional outputs", "reflectivity_* / transmissivity_*", "",
                        "UI optional_outputs toggle",
                        "radiation.optionalOutputPrimitiveData(label)")

        print(f"\n    Ray tracing {', '.join(active_bands)} ...")
        radiation.updateGeometry()
        for band in active_bands:
            radiation.runBand(band)
        print("    Done.")

        # ---- results --------------------------------------------------
        rule("STEP 4   RESULTS")
        stats = {}
        for band in active_bands:
            values = radiation.getAbsorbedFlux(band, leaf_uuids)
            watts = sum(f * a for f, a in zip(values, areas))
            stats[band] = dict(min=min(values), max=max(values),
                               mean=sum(values) / len(values), watts=watts)
            print(f"""
    {band}   radiation_flux_{band}   (ABSORBED flux, per Radiation.dox)
      min / mean / max   {stats[band]['min']:8.2f} / {stats[band]['mean']:8.2f} / {stats[band]['max']:8.2f} W/m2
      total absorbed     {watts:8.2f} W
        FROM  radiation.getAbsorbedFlux("{band}", leaf_uuids)
        WHICH READS  primitive data "radiation_flux_{band}" written by runBand()""")

        # ---- the remaining Results rows from the artifact ---------------
        if UI["compute_total_absorbed"]:
            # Summed from the PER-BAND values, deliberately.
            #
            # getTotalAbsorbedFlux() exists and looks like the obvious call, but
            # its own docstring warns that its ordering does NOT correspond to
            # context.getAllUUIDs(), so there is no safe way to line it up with
            # a leaf UUID list. Indexing it by UUID gave 492.49 W here against a
            # true per-band sum of 525.18 W - a 6% error from misalignment, with
            # nothing to indicate anything was wrong.
            #
            # It also sums EVERY band, so if you ever add a SW band alongside
            # PAR and NIR the overlapping wavelengths are counted twice.
            summed = sum(s["watts"] for s in stats.values())
            per_band = "  +  ".join(f"{b} {stats[b]['watts']:.2f}" for b in stats)
            print(f"""
    TOTAL ABSORBED   summed across the active bands
      {per_band}   =   {summed:.2f} W
        FROM  sum of radiation.getAbsorbedFlux(band, leaf_uuids) per band
        NOT FROM getTotalAbsorbedFlux(), whose ordering cannot be aligned to a
        UUID list and which double-counts overlapping bands. Prefer the
        per-band reader and add them up yourself.""")

        if UI["compute_gtheta"]:
            try:
                g_sun = radiation.calculateGtheta(sun_vector)
                g_up = radiation.calculateGtheta(vec3(0.0, 0.0, 1.0))
                print(f"""
    G(theta)   projection coefficient, NOT a view factor
      toward the sun    {g_sun:.4f}
      straight down     {g_up:.4f}
        FROM  radiation.calculateGtheta(direction)
        MEANS  the mean fraction of leaf area projected onto a plane facing
        that direction. 0.5 is the classic spherical-leaf value; higher means
        leaves face that direction more squarely.""")
            except Exception as exc:
                trace.note(f"calculateGtheta failed: {str(exc)[:90]}")

        # ---- checks ---------------------------------------------------
        if "PAR" in stats:
            supplied = (flux["PAR"]["direct"] * math.cos(zenith)
                        + flux["PAR"]["diffuse"]) * ground_area
            trace.check(
                stats["PAR"]["watts"] <= supplied * 1.02,
                f"PAR absorbed {stats['PAR']['watts']:.1f} W <= supplied {supplied:.1f} W",
                "Energy conservation. Supplied is the beam projected onto flat ground "
                "(direct x cos(zenith)) plus the diffuse sky, times the plot area. "
                "Absorbing more than arrives means the flux was double-counted, most "
                "likely by handing radiation the band TOTAL instead of the direct/diffuse "
                "split.")
            trace.check(
                stats["PAR"]["max"] <= (flux["PAR"]["direct"] + flux["PAR"]["diffuse"]) * 1.5,
                f"brightest leaf {stats['PAR']['max']:.1f} W/m2 within 1.5x of "
                f"direct+diffuse {flux['PAR']['direct'] + flux['PAR']['diffuse']:.1f}",
                "A leaf CAN exceed direct+diffuse because neighbours scatter light onto "
                "it, so the bound allows 50% headroom. Blowing past it suggests the "
                "source flux was set twice, or a spectral integral was applied on top of "
                "an already-scaled flux.")
            trace.check(
                stats["PAR"]["mean"] > 1.0,
                f"mean PAR {stats['PAR']['mean']:.1f} W/m2 is non-trivial",
                "Near-zero absorbed flux with the sun above the horizon means light is "
                "not reaching the leaves at all. Usual causes: the source flux was never "
                "set for this band, or the sun vector points away from the canopy.")

        # Settings-level check. This one reads the CONFIGURATION rather than the
        # results, because scattering depth 0 does not show up as an obviously
        # wrong number - see the WHY below.
        for band in [b for b in active_bands if b != "LW"]:
            depth = {"PAR": UI["scatter_PAR"], "NIR": UI["scatter_NIR"]}[band]
            has_optics = LEAF_OPTICS[band]["rho"] > 0 or LEAF_OPTICS[band]["tau"] > 0
            trace.check(
                not (depth == 0 and has_optics),
                f"{band}: scatter depth {depth} is compatible with rho="
                f"{LEAF_OPTICS[band]['rho']} tau={LEAF_OPTICS[band]['tau']}",
                "With scattering depth 0 Helios overrides your optical properties to "
                "eps=1, rho=0, tau=0 - a perfect blackbody absorber "
                "(RadiationModel.cpp:2865-2868). It does NOT darken the scene: leaves "
                "absorb 100% instead of 85%, so absorbed PAR goes UP by roughly 9% and "
                "inter-leaf scattering disappears entirely. The result looks plausible, "
                "which is what makes it dangerous. Helios does print a warning on stderr "
                "('Surface radiative properties ... will be ignored'), so surface that "
                "warning in the GUI rather than relying on the numbers looking wrong. "
                "FIX: set scatter depth to at least 1 for any band with non-zero rho/tau.")
        if "NIR" in stats and "PAR" in stats:
            trace.check(
                stats["NIR"]["mean"] < stats["PAR"]["mean"],
                f"NIR mean {stats['NIR']['mean']:.1f} < PAR mean {stats['PAR']['mean']:.1f}",
                "A leaf absorbs ~85% of PAR but only ~10% of NIR, so absorbed NIR must be "
                "the smaller number even though incoming NIR is larger. Reversed means "
                "the rho/tau values were swapped between bands.")
        trace.check(
            sun_vector.z > 0,
            f"sun above the horizon (vector z = {sun_vector.z:+.4f})",
            "Below the horizon there is no direct beam at all. If you did not intend "
            "night, the usual cause is a flipped longitude or UTC offset sign - both are "
            "POSITIVE-WEST in Helios, inverted from every other tool.")
        if par_total is not None:
            # Only meaningful when a split actually happened. In manual mode you
            # type direct and diffuse independently, so there is no total to add
            # back to and nothing to conserve.
            trace.check(
                abs((flux["PAR"]["direct"] + flux["PAR"]["diffuse"]) - par_total) < 1e-3,
                "PAR direct + diffuse adds back to the PAR total",
                "The split must conserve energy. This is pure arithmetic in this file, so a "
                "failure means the diffuse fraction is outside 0..1.")
        else:
            # Manual mode has no derived quantity to check, so the only sanity
            # available is that the typed numbers are physical.
            trace.check(
                all(flux[b]["direct"] >= 0 and flux[b]["diffuse"] >= 0
                    for b in flux),
                "all typed flux values are non-negative",
                "Manual mode derives nothing, so nothing cross-checks your numbers. This is "
                "the only guard there is: negative flux is unphysical. If your results look "
                "wrong in manual mode, the inputs are the first place to look.")

        # ---- report ---------------------------------------------------
        rule("PROVENANCE   every value, where it came from, where it went")
        for name, value, unit, came, went in trace.values:
            print(f"\n  {name:<22} {value} {unit}")
            print(f"    FROM  {came}")
            if went:
                print(f"    TO    {went}")

        if trace.notes:
            rule("NOTES")
            for n in trace.notes:
                print(f"    - {n}")

        rule("CHECKS")
        failed = 0
        for ok, statement, why in trace.checks:
            print(f"\n  [{'PASS' if ok else 'FAIL'}]  {statement}")
            if not ok:
                failed += 1
                print("         WHY THIS MATTERS:")
                for line in _wrap(why, 66):
                    print(f"           {line}")

        print("\n" + "-" * 78)
        if failed:
            print(f"  {failed} of {len(trace.checks)} checks FAILED. Read the WHY above, "
                  "change the setting it names, and run again.")
        else:
            print(f"  HAPPY FLOW COMPLETE - all {len(trace.checks)} checks passed.")
        print("-" * 78)

    except Exception as exc:
        rule("RUN FAILED")
        print(f"\n  {type(exc).__name__}: {exc}\n")
        print(_diagnose(str(exc)))
    finally:
        context.__exit__(None, None, None)


def _wrap(text, width):
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        out.append(line)
    return out


def _diagnose(message):
    """Turn a raw Helios error into an instruction naming the setting to change."""
    rules = [
        ("must sum to 1",
         "Emission is on for a band whose leaves also reflect and transmit.\n"
         "  Helios enforces emissivity + rho + tau == 1 and emissivity defaults to 1.0.\n"
         "  FIX: only the LW band may have emission on. Turn band_LW off, or check\n"
         "  LEAF_OPTICS['LW'] still sums to exactly 1."),
        ("does not exist",
         "A band label or timeseries name was referenced before it was created.\n"
         "  FIX: check the band toggles - a flux was set for a band that is off."),
        ("Prague",
         "The Prague sky dataset is not shipped with this build.\n"
         "  FIX: turn the 'Prague sky model' toggle off (press a, then its number)."),
        ("Timeseries variable",
         "Cloud calibration needs measured irradiance loaded as a timeseries first.\n"
         "  FIX: turn 'Cloud calibration' off, or load weather data before running."),
        ("out of memory",
         "The GPU ran out of VRAM.\n"
         "  FIX: lower 'Diffuse rays' first - it is the biggest cost - then reduce\n"
         "  Plants X / Plants Y."),
        ("humidity",
         "Humidity must be a FRACTION 0..1, not a percentage.\n"
         "  FIX: the panel holds percent and divides by 100; check humidity_pct <= 100."),
    ]
    for needle, advice in rules:
        if needle.lower() in message.lower():
            return f"  LIKELY CAUSE:\n  {advice}"
    return ("  No specific diagnosis. Re-run with one setting changed at a time to\n"
            "  isolate which one triggers it.")


# ===========================================================================

def main():
    global ADVANCED
    print("\n" + "=" * 78)
    print("  HAPPY FLOW  -  Solar Position + Radiation, driven like the real UI")
    print("=" * 78)

    while True:
        index = show_panel()
        print(f"\n    [number] edit    [r] RUN    [d] DIAGNOSE features"
              f"    [a] advanced {'ON' if ADVANCED else 'off'}    [q] quit")
        choice = input("\n  > ").strip().lower()

        if choice in ("q", "quit", "exit"):
            print("\n  Done.\n")
            return
        if choice == "a":
            ADVANCED = not ADVANCED
            continue
        if choice == "d":
            try:
                diagnostics()
            except Exception as exc:
                print(f"\n  Diagnostics itself failed: {type(exc).__name__}: {exc}")
            input("\n  Press Enter to return to the panel...")
            continue
        if choice == "r":
            run()
            input("\n  Press Enter to return to the panel...")
            continue
        if choice in index:
            edit(index[choice])
            continue
        print(f"    '{choice}' is not an option.")


if __name__ == "__main__":
    main()
