"""
STAGE 2 — FULL SIMULATION TEST: Solar Position + Radiation on a maize canopy.

===============================================================================
WHAT THIS IS
===============================================================================

A real end-to-end simulation, the kind a user of the GUI would run:

    1. build a maize canopy from Helios's built-in plant library
    2. give every leaf optical properties
    3. compute the sun from site + date + time
    4. BRIDGE: split solar flux into direct + diffuse and hand it to radiation
    5. ray trace PAR and NIR on the GPU
    6. read radiation_flux_PAR back off every leaf and check it makes sense

Stage 1 (testing_SolarToRadiation_Flow.py) showed WHERE the inputs come from.
This file actually runs them through the ray tracer.

Why this catches bugs the unit tests cannot: every unit test can pass while the
BRIDGE between the two plugins is wrong. Hand over the total instead of the
split, forget setSourcePosition, misspell a band label — none of those raise an
error. The run completes and the numbers are quietly wrong. Only a full
simulation with physical sanity checks exposes that.

===============================================================================
GPU SIZE — READ THIS BEFORE INCREASING ANYTHING
===============================================================================

Defaults here are deliberately SMALL, sized for a laptop RTX 3050 (4 GB).
Ray tracing memory scales with primitives x rays x bands, and OptiX does not
fail gracefully when it runs out — you get a driver reset or a hung process,
not a friendly error.

Change ONE thing at a time and re-run, using the SIZE profile below.
Watch `nvidia-smi` in another terminal if you want to see the headroom.

===============================================================================
HOW TO RUN
===============================================================================

    cd helios_gui/backend-api/pyhelios
    source ../Env/Scripts/activate          # Git Bash
    export PYHELIOS_USE_PIP=0
    python tests/Full_test_SR/testing_Maize_Simulation.py

Use FORWARD slashes even on Windows. In Git Bash a backslash escapes the next
character, so tests\Full_test_SR\... silently collapses to testsFull_test_SR...
and you get "No such file or directory".

Needs the radiation plugin compiled in. If it is missing the script says so and
stops rather than crashing.
"""

import math
import os
import sys

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")))
os.environ.setdefault("PYHELIOS_USE_PIP", "0")

from pyhelios import Context, SolarPosition  # noqa: E402
from pyhelios.wrappers.DataTypes import vec2, vec3, int2  # noqa: E402


# ===========================================================================
# SIZE PROFILE — the knobs that decide whether your GPU copes
# ===========================================================================
# Start at "small". Only move up if the run finishes comfortably.
#
#   plants        how many maize plants. Primitive count scales with this.
#   age_days      older plants have more leaves, so also more primitives.
#   direct_rays   rays per primitive toward the sun. Helios default 100.
#   diffuse_rays  rays per primitive toward the sky dome. Helios default 1000
#                 — that default is the single biggest memory cost, which is
#                 why "small" cuts it to 200.
#   scatter_*     how many bounces to follow. NIR needs more than PAR because
#                 maize leaves reflect and transmit ~45% each in NIR, so light
#                 keeps bouncing. PAR is mostly absorbed, so it dies quickly.
# ===========================================================================

SIZE = {
    "small": dict(plants=int2(2, 2), age_days=30.0, spacing=vec2(0.75, 0.75),
                  direct_rays=100, diffuse_rays=200,
                  scatter_par=2, scatter_nir=3),
    "medium": dict(plants=int2(3, 3), age_days=40.0, spacing=vec2(0.75, 0.75),
                   direct_rays=100, diffuse_rays=500,
                   scatter_par=2, scatter_nir=4),
    "large": dict(plants=int2(5, 5), age_days=50.0, spacing=vec2(0.75, 0.75),
                  direct_rays=200, diffuse_rays=1000,
                  scatter_par=3, scatter_nir=5),
}
PROFILE = "small"          # <-- change this, one step at a time

# Fixes the procedural plant generator so every run grows the SAME canopy.
# Change it to sample a different-but-repeatable maize plant. See the comment
# in main() for why an unseeded run makes this useless as a test.
RANDOM_SEED = 20260620

CROP = "maize"

# Same scenario as stage 1, so the two scripts can be compared line by line.
SITE = {"latitude": 38.5449, "longitude": 121.7405, "utc_offset": 7}
DATE = (2026, 6, 20)
TIME = (13, 0)
PRESSURE_PA, TEMPERATURE_K, HUMIDITY_FRAC, TURBIDITY_BETA = 101325.0, 300.0, 0.5, 0.05

# Leaf optical properties. Typical measured values for a green leaf.
# PAR: leaves absorb nearly everything, because that is the light they use.
# NIR: leaves are almost transparent mirrors, which is why NIR needs more
#      scattering bounces than PAR.
LEAF_OPTICS = {
    "PAR": dict(reflectivity=0.10, transmissivity=0.05),
    "NIR": dict(reflectivity=0.45, transmissivity=0.45),
}


def rule(title):
    print("\n" + "=" * 74)
    print(f"  {title}")
    print("=" * 74)


def check_plugins():
    """Refuse to run rather than crash confusingly if radiation is absent."""
    from pyhelios.plugins.registry import get_plugin_registry
    registry = get_plugin_registry()
    needed = ("solarposition", "radiation", "plantarchitecture")
    missing = [p for p in needed if not registry.is_plugin_available(p)]
    if missing:
        rule("CANNOT RUN")
        print(f"""
    Missing plugin(s): {', '.join(missing)}

    This is a build problem, not a bug in the test. Rebuild with:

        python build_scripts/build_helios.py --plugins radiation solarposition \\
               energybalance plantarchitecture visualizer weberpenntree \\
               photosynthesis stomatalconductance boundarylayerconductance \\
               leafoptics lidar
""")
        return False
    return True


# ===========================================================================
# STEP 1 — build the canopy
# ===========================================================================

def build_canopy(context, cfg):
    """Build a maize canopy from Helios's built-in plant library.

    You do not model the plant yourself. plantarchitecture ships 30+ crop
    models; two calls give you a real canopy with correct leaf geometry.
    """
    from pyhelios.PlantArchitecture import PlantArchitecture

    rule(f"STEP 1   BUILD THE {CROP.upper()} CANOPY   (profile: {PROFILE})")

    plantarch = PlantArchitecture(context)
    plantarch.loadPlantModelFromLibrary(CROP)

    plant_ids = plantarch.buildPlantCanopyFromLibrary(
        canopy_center=vec3(0.0, 0.0, 0.0),
        plant_spacing=cfg["spacing"],
        plant_count=cfg["plants"],
        age=cfg["age_days"],
    )

    # Every leaf UUID across every plant. These are the primitives we will give
    # optical properties to and later read flux back from.
    #
    # A leaf is an OBJECT (it may be several triangles); radiation works on
    # PRIMITIVES. getObjectPrimitiveUUIDs accepts the whole list at once, which
    # is one wrapper crossing instead of one per leaf.
    leaf_object_ids = []
    for plant_id in plant_ids:
        leaf_object_ids.extend(plantarch.getPlantLeafObjectIDs(plant_id))
    leaf_uuids = context.getObjectPrimitiveUUIDs(leaf_object_ids) if leaf_object_ids else []

    total_primitives = context.getPrimitiveCount()
    leaf_area = sum(context.getPrimitiveArea(u) for u in leaf_uuids)
    ground_area = (cfg["plants"].x * cfg["spacing"].x) * (cfg["plants"].y * cfg["spacing"].y)

    print(f"""
    Crop                {CROP}
    Plants              {cfg['plants'].x} x {cfg['plants'].y} = {len(plant_ids)}
    Spacing             {cfg['spacing'].x} x {cfg['spacing'].y} m
    Age                 {cfg['age_days']:.0f} days
    Ground area         {ground_area:.2f} m2

    Primitives total    {total_primitives}
    Leaf primitives     {len(leaf_uuids)}
    Total leaf area     {leaf_area:.3f} m2
    Leaf area index     {leaf_area / ground_area:.2f}   (m2 leaf per m2 ground)""")

    return plantarch, plant_ids, leaf_uuids, ground_area


# ===========================================================================
# STEP 2 — optical properties
# ===========================================================================

def set_leaf_optics(context, leaf_uuids):
    """Give every leaf a reflectivity and transmissivity per band.

    SILENT FAILURE WARNING: a primitive with no material defaults to
    reflectivity 0 and transmissivity 0 — a perfect black absorber. The run
    still succeeds and every number is wrong. Nothing warns you. That is why
    this step is explicit rather than left to a default.
    """
    rule("STEP 2   LEAF OPTICAL PROPERTIES")

    for band, props in LEAF_OPTICS.items():
        context.setPrimitiveDataFloat(
            leaf_uuids, f"reflectivity_{band}", props["reflectivity"])
        context.setPrimitiveDataFloat(
            leaf_uuids, f"transmissivity_{band}", props["transmissivity"])
        absorbed = 1.0 - props["reflectivity"] - props["transmissivity"]
        print(f"\n    {band}   reflectivity {props['reflectivity']:.2f}"
              f"   transmissivity {props['transmissivity']:.2f}"
              f"   -> absorbs {absorbed:.2f}")

    print("""
    Applied to every leaf primitive. Note how different the two bands are:
    a maize leaf absorbs 85% of PAR but only 10% of NIR. That single fact is
    why the two bands need different scattering depths.""")


# ===========================================================================
# STEP 3 — solar, and the bridge
# ===========================================================================

def solar_inputs(context):
    """Run Solar Position and return everything radiation needs.

    This is the same arithmetic stage 1 printed. Keeping it in one function
    makes it obvious that the bridge is a handful of lines of YOUR code, not
    something either plugin does for you.
    """
    rule("STEP 3   SOLAR POSITION, AND THE BRIDGE TO RADIATION")

    solar = SolarPosition(context, **SITE)
    try:
        solar.setAtmosphericConditions(
            PRESSURE_PA, TEMPERATURE_K, HUMIDITY_FRAC, TURBIDITY_BETA)

        zenith = solar.getSunZenith()
        sun_vector = solar.getSunDirectionVector()
        par_total = solar.getSolarFluxPAR()
        nir_total = solar.getSolarFluxNIR()
        fdiff = solar.getDiffuseFraction()

        # THE BRIDGE. Solar gives one total per band; radiation needs the beam
        # and the sky separately. Splitting them is your job.
        values = {
            "sun_vector": sun_vector,
            "zenith": zenith,
            "PAR": dict(direct=par_total * (1 - fdiff), diffuse=par_total * fdiff),
            "NIR": dict(direct=nir_total * (1 - fdiff), diffuse=nir_total * fdiff),
        }

        print(f"""
    Sun elevation       {math.degrees(solar.getSunElevation()):8.3f} deg
    Sun zenith          {math.degrees(zenith):8.3f} deg
    Sun vector          ({sun_vector.x:+.5f}, {sun_vector.y:+.5f}, {sun_vector.z:+.5f})
    Diffuse fraction    {fdiff:8.4f}

    BAND     TOTAL        DIRECT = total x (1-fdiff)   DIFFUSE = total x fdiff
    PAR   {par_total:8.2f}      {values['PAR']['direct']:8.2f}                    {values['PAR']['diffuse']:8.2f}   W/m2
    NIR   {nir_total:8.2f}      {values['NIR']['direct']:8.2f}                    {values['NIR']['diffuse']:8.2f}   W/m2

    These are BEAM-NORMAL values (measured facing the sun), which is what
    Helios wants. Do NOT multiply by cos(zenith).""")

        return values
    finally:
        solar.__exit__(None, None, None)


# ===========================================================================
# STEP 4 — radiation
# ===========================================================================

def run_radiation(context, cfg, solar_values):
    """Configure the radiation model, hand it the solar values, ray trace."""
    from pyhelios.RadiationModel import RadiationModel

    rule("STEP 4   RADIATION MODEL")

    radiation = RadiationModel(context)

    # A collimated source is a beam of parallel rays: the correct model for the
    # sun, which is effectively infinitely far away.
    sun = radiation.addCollimatedRadiationSource(solar_values["sun_vector"])

    for band in ("PAR", "NIR"):
        wavelengths = {"PAR": (400, 700), "NIR": (700, 2500)}[band]
        radiation.addRadiationBand(band, wavelengths[0], wavelengths[1])

        # The bridge values, handed over.
        radiation.setSourceFlux(sun, band, solar_values[band]["direct"])
        radiation.setDiffuseRadiationFlux(band, solar_values[band]["diffuse"])

        # EMISSION MUST BE OFF FOR SHORTWAVE BANDS.
        #
        # Helios enforces energy conservation as  emissivity + rho + tau = 1,
        # and emissivity defaults to 1.0. With a leaf at rho=0.45, tau=0.45 in
        # NIR that sums to 1.9 and runBand() aborts:
        #
        #   ERROR (RadiationModel): emissivity, transmissivity, and reflectivity
        #   must sum to 1 ... Band NIR, Primitive #14040: eps=1.000000,
        #   tau=0.450000, rho=0.450000
        #
        # The physics: emission means the surface RADIATES in this band. A leaf
        # at 300 K emits thermal longwave, not visible light or NIR, so emission
        # belongs only on the LW band. Turning it off here both fixes the sum
        # and is the physically correct model.
        radiation.disableEmission(band)

        radiation.setDirectRayCount(band, cfg["direct_rays"])
        radiation.setDiffuseRayCount(band, cfg["diffuse_rays"])

        # Scattering depth MUST be >= 1 or Helios silently resets every
        # primitive to black and the optical properties from step 2 are ignored.
        depth = cfg["scatter_par"] if band == "PAR" else cfg["scatter_nir"]
        radiation.setScatteringDepth(band, depth)

        print(f"\n    {band}   {wavelengths[0]}-{wavelengths[1]} nm"
              f"   direct {solar_values[band]['direct']:.2f}"
              f"   diffuse {solar_values[band]['diffuse']:.2f} W/m2"
              f"\n          rays {cfg['direct_rays']} direct / {cfg['diffuse_rays']} diffuse"
              f"   scatter depth {depth}")

    print("\n    Building acceleration structure and ray tracing...")
    radiation.updateGeometry()
    for band in ("PAR", "NIR"):
        radiation.runBand(band)
    print("    Done.")

    return radiation


# ===========================================================================
# STEP 5 — read the results back
# ===========================================================================

def report_flux(context, radiation, leaf_uuids, ground_area, solar_values, cfg):
    """Read radiation_flux_<band> off every leaf and describe the result.

    getAbsorbedFlux is the right reader: it returns values aligned to the UUID
    list you pass. getTotalAbsorbedFlux sums across bands (double-counting
    overlapping ones) and its ordering does NOT match context.getAllUUIDs(),
    which is a trap its own docstring warns about.

    WHICH NUMBERS ARE REPRODUCIBLE
    ------------------------------
    Seeding the Context pins the GEOMETRY, but ray tracing is Monte Carlo: rays
    are sampled randomly, so per-primitive values still wobble slightly between
    runs. Measured across two seeded runs:

        total absorbed   426.63 W  ->  426.63 W    identical
        brightest leaf   408.61    ->  409.04      ~0.1% drift

    Aggregates converge because 73,000 leaves average the sampling noise away;
    a single extreme value does not. So assert on TOTALS and MEANS, and treat
    min/max as diagnostics rather than test criteria. Raising diffuse_rays
    tightens the spread at the cost of memory and time.
    """
    rule("STEP 5   WHAT THE LEAVES ABSORBED")

    flux = {band: radiation.getAbsorbedFlux(band, leaf_uuids) for band in ("PAR", "NIR")}
    areas = [context.getPrimitiveArea(u) for u in leaf_uuids]

    stats = {}
    for band, values in flux.items():
        absorbed_watts = sum(f * a for f, a in zip(values, areas))
        stats[band] = {
            "min": min(values), "max": max(values),
            "mean": sum(values) / len(values),
            "watts": absorbed_watts,
        }
        print(f"""
    {band}   radiation_flux_{band}, per leaf primitive
      min             {stats[band]['min']:10.2f} W/m2   darkest leaf, deep in the canopy
      max             {stats[band]['max']:10.2f} W/m2   brightest leaf, top of canopy
      mean            {stats[band]['mean']:10.2f} W/m2
      total absorbed  {absorbed_watts:10.2f} W      = sum(flux x leaf area)""")

    # ---- vertical profile: does light actually decay with depth? ----
    # This is the signature result of a canopy radiation model. If it is flat,
    # the ray tracer is not seeing the geometry.
    heights = []
    for uuid in leaf_uuids:
        vertices = context.getPrimitiveVertices(uuid)
        heights.append(sum(v.z for v in vertices) / len(vertices))

    top, bottom = max(heights), min(heights)
    layers = 5
    print(f"\n    VERTICAL PROFILE   canopy from {bottom:.2f} m to {top:.2f} m, "
          f"in {layers} layers\n")
    print("      height range        leaves      mean PAR    relative")
    span = (top - bottom) or 1.0
    layer_means = []
    for i in reversed(range(layers)):
        low = bottom + span * i / layers
        high = bottom + span * (i + 1) / layers
        in_layer = [flux["PAR"][j] for j, h in enumerate(heights)
                    if low <= h <= high]
        if not in_layer:
            continue
        mean = sum(in_layer) / len(in_layer)
        layer_means.append(mean)
        bar = "#" * max(1, int(30 * mean / max(stats["PAR"]["max"], 1e-6)))
        print(f"      {low:5.2f} - {high:5.2f} m   {len(in_layer):6d}   {mean:9.2f}   {bar}")

    # ---- physical sanity checks ----
    rule("PHYSICAL CHECKS")

    # Energy supplied to the plot: the beam arrives on a horizontal footprint,
    # so HERE the cos(zenith) projection is correct — we are converting a
    # beam-normal flux into energy landing on flat ground.
    par_supplied = (solar_values["PAR"]["direct"] * math.cos(solar_values["zenith"])
                    + solar_values["PAR"]["diffuse"]) * ground_area

    checks = [
        (stats["PAR"]["watts"] <= par_supplied * 1.02,
         f"PAR absorbed {stats['PAR']['watts']:.1f} W <= supplied {par_supplied:.1f} W "
         f"(cannot absorb more than arrives)"),
        (stats["PAR"]["min"] >= 0,
         f"no negative flux (min {stats['PAR']['min']:.2f} W/m2)"),
        (stats["PAR"]["max"] > 0,
         "at least one leaf received light"),
        (stats["NIR"]["mean"] < stats["PAR"]["mean"] * 3,
         f"NIR mean {stats['NIR']['mean']:.1f} is not absurdly above PAR "
         f"{stats['PAR']['mean']:.1f}"),
        (len(layer_means) >= 2 and layer_means[0] > layer_means[-1],
         "top of canopy is brighter than the bottom (light is being intercepted)"),
        # A leaf CAN absorb more than direct + diffuse, because neighbouring
        # leaves scatter extra light onto it — RadiationModel.cpp:4638 adds the
        # scatter buffers on top of the incident flux. So the bound is not
        # (direct + diffuse); it is that plus a scattering allowance.
        #
        # This started as a strict "<= direct + diffuse" check and it FAILED on
        # a run where a top leaf absorbed slightly more. The check was wrong,
        # not the model. 1.5x is loose enough for real inter-leaf scattering and
        # still catches a genuine blunder like double-counting the flux.
        (stats["PAR"]["max"] <= (solar_values["PAR"]["direct"] +
                                 solar_values["PAR"]["diffuse"]) * 1.5,
         f"brightest leaf {stats['PAR']['max']:.1f} W/m2 is within 1.5x of "
         f"direct+diffuse {solar_values['PAR']['direct'] + solar_values['PAR']['diffuse']:.1f} "
         f"(headroom is for inter-leaf scattering)"),
    ]
    for ok, text in checks:
        print(f"    [{'PASS' if ok else 'FAIL'}]  {text}")

    failures = sum(1 for ok, _ in checks if not ok)
    print("\n" + "-" * 74)
    if failures:
        print(f"  {failures} physical check(s) FAILED — the coupling is not correct.")
    else:
        print("  Simulation ran and every physical check passed.")
    print("-" * 74)
    return failures


# ===========================================================================

def main():
    if not check_plugins():
        return 1

    cfg = SIZE[PROFILE]
    context = Context()

    # MAKE THE RUN REPRODUCIBLE.
    #
    # buildPlantCanopyFromLibrary is PROCEDURAL: leaf angles, internode lengths
    # and branching all draw from a random generator, so every call grows a
    # different maize plant. Without a fixed seed this script reported 396 W,
    # then 364 W, then 459 W of absorbed PAR on three consecutive runs — all
    # correct, all different.
    #
    # That is fatal for a test. You cannot tell a real regression from ordinary
    # plant-to-plant variation. Seeding pins the canopy so the same inputs
    # always produce the same geometry, and any change in the output is a
    # change in the CODE.
    #
    # To sample real variability on purpose, loop over several seeds and
    # compare distributions — do not just leave it unseeded.
    context.seedRandomGenerator(RANDOM_SEED)

    context.setDate(*DATE)
    context.setTime(*TIME)

    try:
        plantarch, plant_ids, leaf_uuids, ground_area = build_canopy(context, cfg)
        if not leaf_uuids:
            print("\n    No leaf primitives were produced — cannot continue.")
            return 1

        set_leaf_optics(context, leaf_uuids)
        solar_values = solar_inputs(context)
        radiation = run_radiation(context, cfg, solar_values)
        failures = report_flux(context, radiation, leaf_uuids, ground_area,
                               solar_values, cfg)

        print(f"""
  NEXT STEPS
    - Raise PROFILE from "{PROFILE}" one step and re-run, watching nvidia-smi.
    - Change TIME to (18, 0) and confirm the flux drops as the sun sets.
    - Change TIME to (0, 30) and confirm PAR goes to ~0 at night.
    - Set one band's scatter depth to 0 and re-run. Absorbed PAR goes UP about
      9%, not down: Helios overrides rho/tau to a perfect blackbody absorber
      (RadiationModel.cpp:2865-2868), so leaves absorb 100% instead of 85% and
      inter-leaf scattering vanishes. It does print a warning on stderr, which
      the GUI should surface.
""")
        return 1 if failures else 0
    finally:
        context.__exit__(None, None, None)


if __name__ == "__main__":
    sys.exit(main())
