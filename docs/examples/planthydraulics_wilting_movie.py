"""
Plant Hydraulics -- Diurnal Wilting of a Tomato Plant

Runs a tomato plant through one day of weather and makes its posture follow the turgor
pressure the plant hydraulics model computes, so the model's output can be checked by eye:
the plant should stand up before dawn, wilt as transpiration peaks in the afternoon, and
recover in the evening.

Each timestep:
  1. radiation (PAR, NIR, LW) for the sun position and sky at that time of day;
  2. boundary-layer conductance, stomatal conductance and the leaf energy balance, which
     give each leaf's latent heat flux;
  3. plant hydraulics, which turns that transpiration and the soil water potential into
     the turgor pressure of every leaf;
  4. posture, from two simple relationships:
       a) plant-mean leaf turgor -> the Beta distribution of leaf inclination. Turgid, the
          plant has the distribution it was grown with; with no turgor the mean inclination
          rises to WILTED_MEAN_INCLINATION at the same concentration (mu + nu).
       b) each leaf's own turgor -> the flexibility of its petiole, from PETIOLE_FLEX_TURGID
          to PETIOLE_FLEX_WILTED (interpolated geometrically), which the plant architecture model bends under the
          weight of the leaflets.
     Both use the same wilting index, 0 at or above TURGOR_FULL_POSTURE and 1 at zero turgor.

The posture is computed from the turgor of the same timestep and is seen by the radiation
model of the next one, so wilted leaves intercept less sun than turgid ones.

The hydraulic and stomatal coefficients are plausible values chosen to make a mildly
water-stressed plant cross its turgor loss point in the afternoon; they are not a
calibration for tomato. Stomatal conductance (BMF model) does not respond to water
potential here, so transpiration is not reduced as the plant wilts.

Stomata are run dynamically, lagging their steady-state conductance by STOMATAL_TAU_OPEN and
STOMATAL_TAU_CLOSE. The hydraulics are steady-state: water potentials and turgor are in
equilibrium with the transpiration of each timestep, with no lag from stored water.

Output (under docs/examples/output/planthydraulics_wilting/, override with --outdir):
    wilting.mp4           left: plant as rendered; right: leaves colored by turgor pressure
                          (requires ffmpeg on PATH)
    frames/               the frames the movie is made from
    timeseries.csv        weather, fluxes, water potentials, turgor and posture per timestep
    timeseries.png        the same as plots (requires matplotlib)

Usage:
    python docs/examples/planthydraulics_wilting_movie.py
    python docs/examples/planthydraulics_wilting_movie.py --soil-psi -0.5 --step 15

Requires the plantarchitecture, planthydraulics, radiation, energybalance,
stomatalconductance, boundarylayerconductance, solarposition and visualizer plugins.
Radiation needs a GPU; rendering is headless.
"""

import argparse
import csv
import math
import os
import shutil
import subprocess
import sys

import numpy as np

from example_output import display_path, get_output_dir
from pyhelios import (Context, PlantArchitecture, PlantHydraulicsModel, PlantHydraulicsModelCoefficients,
                      RadiationModel, EnergyBalanceModel, StomatalConductanceModel, BoundaryLayerConductanceModel,
                      SolarPosition, Visualizer)
from pyhelios.StomatalConductance import BMFCoefficients
from pyhelios.types import vec2, vec3, RGBcolor

SEED = 11
PLANT_AGE = 45.0  # days

# Davis, California, on a clear day in July. Helios takes longitude and UTC offset positive west.
LATITUDE, LONGITUDE, UTC_OFFSET = 38.55, 121.74, 7.0
DATE = (2026, 7, 15)
PRESSURE = 101325.0  # Pa
TURBIDITY = 0.05
WIND_SPEED = 1.5  # m/s

# Time constants (s) with which stomata approach their steady-state conductance. Without them stomata
# shut the moment the light goes at sunset, transpiration collapses and the plant snaps upright.
STOMATAL_TAU_OPEN, STOMATAL_TAU_CLOSE = 900.0, 1500.0
STOMATAL_SUBSTEP = 60.0  # s; the stomatal update is explicit, so it is stepped well inside the time constants

# The rendered plant is lit from the sun's azimuth, but never from lower than this, so that the
# shadows stay readable at dawn and dusk.
MIN_LIGHT_ELEVATION = 30.0  # degrees

# Leaf pressure-volume curve: osmotic potential at full turgor (MPa), relative water content at
# turgor loss, and cell wall elasticity exponent. Turgor is -PI_O in a saturated leaf.
PI_O, RWC_TLP, ELASTICITY = -0.9, 0.85, 1.0
# Hydraulic conductances per unit leaf area (mol/m^2/s/MPa), held constant so that each steady-state
# solution depends only on that timestep's inputs.
K_LEAF, K_STEM, K_ROOT = 0.024, 0.06, 0.03

# Posture relationships.
TURGOR_FULL_POSTURE = 0.6  # MPa; at or above this turgor a leaf holds its turgid posture
WILTED_MEAN_INCLINATION = 65.0  # degrees from horizontal, at zero plant-mean turgor
PETIOLE_FLEX_TURGID = 0.05  # must stay positive: a petiole is not re-bent at exactly zero
PETIOLE_FLEX_WILTED = 2.5

TURGOR_COLORBAR_MAX = 0.6  # MPa


def weather(hour):
    """Air temperature (K) and relative humidity for a hot, dry summer day: 18 C / 75% before dawn, 34 C / 25% at 15:00."""
    phase = math.cos(2.0 * math.pi * (hour - 15.0) / 24.0)
    return 273.15 + 26.0 + 8.0 * phase, 0.50 - 0.25 * phase


def light_direction(sun):
    """Direction to light the rendered plant from: toward the sun, raised to MIN_LIGHT_ELEVATION if it is lower."""
    horizontal = math.hypot(sun.x, sun.y)
    if horizontal < 1e-6:
        return vec3(0, 0, 1)
    elevation = max(math.atan2(sun.z, horizontal), math.radians(MIN_LIGHT_ELEVATION))
    return vec3(math.cos(elevation) * sun.x / horizontal, math.cos(elevation) * sun.y / horizontal, math.sin(elevation))


def wilting_index(turgor):
    """0 for a turgid leaf, rising linearly to 1 as turgor falls from TURGOR_FULL_POSTURE to zero."""
    return np.clip(1.0 - np.asarray(turgor, dtype=float) / TURGOR_FULL_POSTURE, 0.0, 1.0)


def beta_parameters(mean_inclination_deg, concentration):
    """Beta (mu, nu) with the given mean inclination from horizontal, which is 90 * nu / (mu + nu)."""
    fraction = min(max(mean_inclination_deg / 90.0, 0.02), 0.98)
    return (1.0 - fraction) * concentration, fraction * concentration


def leaf_inclinations(plantarch, plant_id):
    """Inclination (degrees) and area of every leaf. The leaf angle distribution is one of leaf area, not leaf count."""
    inclinations = np.asarray(plantarch.getPlantLeafInclinations(plant_id), dtype=float)
    areas = np.asarray(plantarch.getPlantLeafAreas(plant_id), dtype=float)
    if inclinations.size != areas.size:
        raise RuntimeError(f"{areas.size} leaf areas but {inclinations.size} leaf inclinations were returned")
    return inclinations, areas


def mean_inclination(plantarch, plant_id):
    inclinations, areas = leaf_inclinations(plantarch, plant_id)
    return float((inclinations * areas).sum() / areas.sum())


def fit_beta(plantarch, plant_id):
    """Mean inclination (degrees) and concentration mu + nu of a plant's leaves, by area-weighted moments."""
    inclinations, areas = leaf_inclinations(plantarch, plant_id)
    x, weights = inclinations / 90.0, areas / areas.sum()
    mean = float((weights * x).sum())
    variance = float((weights * (x - mean) ** 2).sum())
    concentration = mean * (1.0 - mean) / variance - 1.0 if variance > 0 else 50.0
    return 90.0 * mean, min(max(concentration, 2.0), 50.0)


class Leaf:
    """One petiole and the leaflets it carries."""

    def __init__(self, shoot_id, node, petiole, object_ids):
        self.shoot_id, self.node, self.petiole, self.object_ids = shoot_id, node, petiole, object_ids


def collect_leaves(context, plantarch, plant_id):
    leaves = []
    for shoot_id in plantarch.getAllShootIDs(plant_id):
        for node in range(plantarch.getShoot(plant_id, shoot_id)["node_count"]):
            for petiole, object_ids in enumerate(plantarch.getPhytomerLeafObjectIDs(plant_id, shoot_id, node)):
                object_ids = [oid for oid in object_ids if context.doesObjectExist(oid)]
                if object_ids:
                    leaves.append(Leaf(shoot_id, node, petiole, object_ids))
    return leaves


def area_weighted_mean(context, uuids, label):
    values = context.getPrimitiveDataArray(uuids, label).astype(np.float64)
    areas = np.asarray(context.getPrimitiveArea(uuids), dtype=np.float64)
    return float((values * areas).sum() / areas.sum())


def apply_posture(context, plantarch, plant_id, leaves, turgid_mean_inclination, concentration):
    """Set petiole droop from each leaf's turgor and the leaf angle distribution from the plant mean."""
    flexibility = {}
    for leaf in leaves:
        turgor = area_weighted_mean(context, context.getObjectPrimitiveUUIDs(leaf.object_ids), "turgor_pressure")
        # Interpolated geometrically: droop rises roughly with the logarithm of flexibility, so this makes
        # the droop itself close to linear in the wilting index.
        flex = PETIOLE_FLEX_TURGID * (PETIOLE_FLEX_WILTED / PETIOLE_FLEX_TURGID) ** float(wilting_index(turgor))
        # A phytomer has one flexibility for all of its petioles; tomato has one petiole per phytomer.
        flexibility.setdefault((leaf.shoot_id, leaf.node), []).append(flex)
    for (shoot_id, node), values in flexibility.items():
        plantarch.setPetioleFlexibility(plant_id, shoot_id, node, float(np.mean(values)))
    for leaf in leaves:
        # setLeafAngleDistribution() below poses the leaves, which a plain bend would then refuse to move.
        plantarch.bendPetioleUnderLeafWeight(plant_id, leaf.shoot_id, leaf.node, leaf.petiole,
                                             include_posed_leaves=True)

    leaf_uuids = plantarch.getAllLeafUUIDs()
    wilt = float(wilting_index(area_weighted_mean(context, leaf_uuids, "turgor_pressure")))
    mean_inclination = turgid_mean_inclination + (WILTED_MEAN_INCLINATION - turgid_mean_inclination) * wilt
    mu, nu = beta_parameters(mean_inclination, concentration)
    plantarch.setLeafAngleDistribution(plant_id, mu, nu)
    return mu, nu, float(np.mean([np.mean(v) for v in flexibility.values()]))


def caption_frame(natural, colored, text, out_path):
    """Join the two renders side by side under a caption strip."""
    from PIL import Image, ImageDraw, ImageFont

    left, right = Image.open(natural).convert("RGB"), Image.open(colored).convert("RGB")
    banner = 40
    frame = Image.new("RGB", (left.width + right.width, left.height + banner), (30, 30, 34))
    frame.paste(left, (0, banner))
    frame.paste(right, (left.width, banner))
    font = None
    for candidate in ("/System/Library/Fonts/Supplemental/Arial.ttf",
                      "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf"):
        if os.path.exists(candidate):
            font = ImageFont.truetype(candidate, 20)
            break
    ImageDraw.Draw(frame).text((12, 9), text, fill=(255, 255, 255), font=font or ImageFont.load_default())
    # Even dimensions, as libx264 requires.
    frame = frame.crop((0, 0, frame.width - frame.width % 2, frame.height - frame.height % 2))
    frame.save(out_path, quality=92)


def plot_timeseries(rows, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    hour = [r["hour"] for r in rows]
    fig, axes = plt.subplots(4, 1, figsize=(7, 10), sharex=True)
    axes[0].plot(hour, [r["air_temperature_C"] for r in rows], label="air temperature (°C)")
    axes[0].plot(hour, [r["leaf_temperature_C"] for r in rows], label="mean leaf temperature (°C)")
    axes[0].plot(hour, [100 * r["air_humidity"] for r in rows], label="relative humidity (%)")
    axes[1].plot(hour, [r["PAR_absorbed_Wm2"] for r in rows], label="absorbed PAR (W/m²)")
    axes[1].plot(hour, [r["latent_flux_Wm2"] for r in rows], label="latent heat flux (W/m²)")
    for key, label in (("psi_soil_MPa", "soil"), ("psi_root_MPa", "root"), ("psi_stem_MPa", "stem"),
                       ("psi_leaf_MPa", "leaf (mean)")):
        axes[2].plot(hour, [r[key] for r in rows], label=f"{label} water potential (MPa)")
    axes[2].plot(hour, [r["turgor_mean_MPa"] for r in rows], "k", label="leaf turgor, mean (MPa)")
    axes[2].plot(hour, [r["turgor_min_MPa"] for r in rows], "k:", label="leaf turgor, minimum (MPa)")
    axes[3].plot(hour, [r["mean_inclination_deg"] for r in rows], label="mean leaf inclination (°)")
    axes[3].plot(hour, [r["leaf_height_m"] * 100 for r in rows], label="mean leaf height (cm)")
    axes[3].plot(hour, [r["petiole_flexibility"] * 10 for r in rows], label="mean petiole flexibility × 10")
    axes[3].set_xlabel("hour of day")
    for ax in axes:
        ax.legend(fontsize=8, loc="best")
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--soil-psi", type=float, default=-0.3, help="soil water potential, MPa (default: -0.3)")
    parser.add_argument("--start", type=float, default=5.0, help="first hour of the day simulated (default: 5)")
    parser.add_argument("--end", type=float, default=22.0, help="last hour of the day simulated (default: 22)")
    parser.add_argument("--step", type=float, default=10.0, help="timestep in minutes (default: 10)")
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--outdir", default=None,
                        help="output directory (default: docs/examples/output/planthydraulics_wilting)")
    args = parser.parse_args()

    outdir = str(get_output_dir("planthydraulics_wilting")) if args.outdir is None else os.path.abspath(args.outdir)
    frame_dir = os.path.join(outdir, "frames")
    os.makedirs(frame_dir, exist_ok=True)
    for stale in os.listdir(frame_dir):
        os.remove(os.path.join(frame_dir, stale))

    hours = np.arange(args.start, args.end + 1e-6, args.step / 60.0)
    rows = []

    with Context() as context:
        context.seedRandomGenerator(SEED)
        context.setDate(*DATE)

        ground = context.addPatch(center=vec3(0, 0, 0), size=vec2(3, 3), color=RGBcolor(0.36, 0.27, 0.18))
        context.setPrimitiveDataFloat(ground, "reflectivity_PAR", 0.12)
        context.setPrimitiveDataFloat(ground, "reflectivity_NIR", 0.30)

        with PlantArchitecture(context) as plantarch, \
                SolarPosition(context, UTC_OFFSET, LATITUDE, LONGITUDE) as solar, \
                RadiationModel(context) as radiation, \
                BoundaryLayerConductanceModel(context) as boundarylayer, \
                StomatalConductanceModel(context) as stomatal, \
                EnergyBalanceModel(context) as energybalance, \
                PlantHydraulicsModel(context) as hydraulics, \
                Visualizer(args.width, args.height, headless=True) as vis:

            # ---- plant ----
            plantarch.disableMessages()
            plantarch.loadPlantModelFromLibrary("tomato")
            plantarch.optionalOutputObjectData("plantID")  # groups the leaves into a plant for the hydraulics model
            plant_id = plantarch.buildPlantInstanceFromLibrary(base_position=vec3(0, 0, 0), age=PLANT_AGE)
            leaves = collect_leaves(context, plantarch, plant_id)
            turgid_mean_inclination, concentration = fit_beta(plantarch, plant_id)
            print(f"Tomato plant: {len(leaves)} leaves, {plantarch.getPlantLeafArea(plant_id) * 1e4:.0f} cm² leaf area, "
                  f"mean leaf inclination {turgid_mean_inclination:.1f}°")

            # ---- radiation ----
            radiation.disableMessages()
            sun = radiation.addCollimatedRadiationSource()
            for band in ("PAR", "NIR"):
                radiation.addRadiationBand(band)
                radiation.disableEmission(band)
                radiation.setDirectRayCount(band, 200)
                radiation.setDiffuseRayCount(band, 500)
                radiation.setScatteringDepth(band, 2)
            radiation.addRadiationBand("LW")
            radiation.setDiffuseRayCount("LW", 500)

            # ---- stomata, energy balance, hydraulics ----
            boundarylayer.disableMessages()
            stomatal.disableMessages()
            # Coefficients of the stomatal conductance documentation's example; not a tomato calibration.
            stomatal.setBMFCoefficients(BMFCoefficients(Em=258.25, i0=38.65, k=232916.82, b=609.67))
            stomatal.setDynamicTimeConstants(STOMATAL_TAU_OPEN, STOMATAL_TAU_CLOSE)
            stomatal_substeps = max(1, int(round(args.step * 60.0 / STOMATAL_SUBSTEP)))
            energybalance.disableMessages()
            for band in ("PAR", "NIR", "LW"):
                energybalance.addRadiationBand(band)

            coefficients = PlantHydraulicsModelCoefficients()
            coefficients.setLeafHydraulicConductance(K_LEAF)
            coefficients.setStemHydraulicConductance(K_STEM)
            coefficients.setRootHydraulicConductance(K_ROOT)
            coefficients.setLeafHydraulicCapacitance(PI_O, RWC_TLP, ELASTICITY)
            hydraulics.setModelCoefficients(coefficients)

            # ---- visualizer ----
            vis.setBackgroundColor(RGBcolor(0.93, 0.95, 0.97))
            vis.hideWatermark()
            vis.setColormap("PARULA")
            xb, yb, zb = context.getDomainBoundingBox(plantarch.getAllUUIDs())
            height = zb.y
            reach = max(abs(xb.x), abs(xb.y), abs(yb.x), abs(yb.y), 0.5 * height)
            vis.setCameraPosition(vec3(2.6 * reach, -2.6 * reach, 0.9 * height + 0.6 * reach), vec3(0, 0, 0.45 * height))

            context.setPrimitiveDataFloat(context.getAllUUIDs(), "temperature", weather(hours[0])[0])

            for i, hour in enumerate(hours):
                context.setTime(int(hour), int(round((hour - int(hour)) * 60)))
                air_temperature, air_humidity = weather(hour)

                # ---- weather onto the scene ----
                leaf_uuids = plantarch.getAllLeafUUIDs()
                all_uuids = context.getAllUUIDs()
                context.setPrimitiveDataFloat(all_uuids, "air_temperature", air_temperature)
                context.setPrimitiveDataFloat(all_uuids, "air_humidity", air_humidity)
                context.setPrimitiveDataFloat(all_uuids, "wind_speed", WIND_SPEED)
                plant_uuids = plantarch.getAllUUIDs()
                context.setPrimitiveDataFloat(plant_uuids, "reflectivity_PAR", 0.08)
                context.setPrimitiveDataFloat(plant_uuids, "transmissivity_PAR", 0.05)
                context.setPrimitiveDataFloat(plant_uuids, "reflectivity_NIR", 0.45)
                context.setPrimitiveDataFloat(plant_uuids, "transmissivity_NIR", 0.40)
                # Boundary layers develop over a leaflet, not over the triangles it is meshed with.
                context.setPrimitiveDataFloat(leaf_uuids, "object_length", 0.05)

                # ---- radiation ----
                sun_up = solar.getSunElevation() > math.radians(1.0)
                if sun_up:
                    diffuse_fraction = solar.getDiffuseFraction(PRESSURE, air_temperature, air_humidity, TURBIDITY)
                    par = solar.getSolarFluxPAR(PRESSURE, air_temperature, air_humidity, TURBIDITY)
                    nir = solar.getSolarFluxNIR(PRESSURE, air_temperature, air_humidity, TURBIDITY)
                    radiation.setSourcePosition(sun, solar.getSunDirectionVector())
                else:
                    diffuse_fraction, par, nir = 1.0, 0.0, 0.0
                radiation.setSourceFlux(sun, "PAR", par * (1.0 - diffuse_fraction))
                radiation.setSourceFlux(sun, "NIR", nir * (1.0 - diffuse_fraction))
                radiation.setDiffuseRadiationFlux("PAR", par * diffuse_fraction)
                radiation.setDiffuseRadiationFlux("NIR", nir * diffuse_fraction)
                radiation.setDiffuseRadiationFlux("LW", solar.getAmbientLongwaveFlux(air_temperature, air_humidity))
                radiation.updateGeometry()
                radiation.runBand(["PAR", "NIR", "LW"])

                # ---- transpiration ----
                # Stomatal conductance and leaf temperature depend on each other: leaf temperature is found for
                # the conductance carried over from the last timestep, the stomata are moved toward their steady
                # state for this one, and the energy balance is closed again. On the first timestep the leaves
                # have no conductance yet, and the stomatal model then starts them at steady state.
                boundarylayer.run(all_uuids)
                energybalance.run(all_uuids)
                for _ in range(stomatal_substeps):
                    stomatal.run(leaf_uuids, dt=args.step * 60.0 / stomatal_substeps)
                boundarylayer.run(all_uuids)
                energybalance.run(all_uuids)

                # ---- hydraulics ----
                hydraulics.setSoilWaterPotentialOfPlant(hydraulics.getPlantID(leaf_uuids), args.soil_psi)
                hydraulics.run(leaf_uuids)

                # ---- posture ----
                mu, nu, flexibility = apply_posture(context, plantarch, plant_id, leaves, turgid_mean_inclination,
                                                    concentration)

                turgor = context.getPrimitiveDataArray(leaf_uuids, "turgor_pressure")
                row = {
                    "hour": float(hour),
                    "air_temperature_C": air_temperature - 273.15,
                    "air_humidity": air_humidity,
                    "leaf_temperature_C": area_weighted_mean(context, leaf_uuids, "temperature") - 273.15,
                    "PAR_absorbed_Wm2": area_weighted_mean(context, leaf_uuids, "radiation_flux_PAR"),
                    "latent_flux_Wm2": area_weighted_mean(context, leaf_uuids, "latent_flux"),
                    "psi_soil_MPa": hydraulics.getSoilWaterPotential(leaf_uuids),
                    "psi_root_MPa": hydraulics.getRootWaterPotential(leaf_uuids),
                    "psi_stem_MPa": hydraulics.getStemWaterPotential(leaf_uuids),
                    "psi_leaf_MPa": area_weighted_mean(context, leaf_uuids, "water_potential"),
                    "turgor_mean_MPa": area_weighted_mean(context, leaf_uuids, "turgor_pressure"),
                    "turgor_min_MPa": float(turgor.min()),
                    "beta_mu": mu,
                    "beta_nu": nu,
                    "mean_inclination_deg": mean_inclination(plantarch, plant_id),
                    "petiole_flexibility": flexibility,
                    "leaf_height_m": float(np.mean([context.getObjectCenter(oid).z
                                                    for leaf in leaves for oid in leaf.object_ids])),
                }
                rows.append(row)

                # ---- render ----
                natural = os.path.join(frame_dir, f"natural_{i:04d}.jpeg")
                colored = os.path.join(frame_dir, f"turgor_{i:04d}.jpeg")
                vis.buildContextGeometry(context)
                vis.clearColor()
                vis.disableColorbar()
                vis.setLightingModel("phong_shadowed")
                vis.setLightDirection(light_direction(solar.getSunDirectionVector()))
                vis.plotUpdate()
                vis.printWindow(natural)
                vis.setLightingModel("phong")
                vis.colorContextPrimitivesByData("turgor_pressure", leaf_uuids)
                vis.setColorbarRange(0.0, TURGOR_COLORBAR_MAX)
                vis.setColorbarTitle("Turgor (MPa)")
                vis.enableColorbar()
                vis.plotUpdate()
                vis.printWindow(colored)
                for path in (natural, colored):
                    if not os.path.exists(path):
                        raise RuntimeError(f"Frame {i} was not written to {path}.")

                clock = f"{int(hour):02d}:{int(round((hour - int(hour)) * 60)):02d}"
                caption = (f"{clock}   air {row['air_temperature_C']:.0f} °C, RH {100 * air_humidity:.0f}%   "
                           f"leaf ψ {row['psi_leaf_MPa']:.2f} MPa   turgor {row['turgor_mean_MPa']:.2f} MPa   "
                           f"inclination {row['mean_inclination_deg']:.0f}°")
                caption_frame(natural, colored, caption, os.path.join(frame_dir, f"frame_{i:04d}.jpeg"))
                print(f"  {clock}  gs {area_weighted_mean(context, leaf_uuids, 'moisture_conductance'):5.3f}  E {row['latent_flux_Wm2']:6.1f} W/m²  psi_leaf {row['psi_leaf_MPa']:6.2f} MPa  "
                      f"turgor mean {row['turgor_mean_MPa']:5.2f} min {row['turgor_min_MPa']:5.2f} MPa  "
                      f"inclination {row['mean_inclination_deg']:5.1f}°  leaf height {100 * row['leaf_height_m']:5.1f} cm",
                      flush=True)

    csv_path = os.path.join(outdir, "timeseries.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nTime series written to: {display_path(csv_path)}")

    try:
        plot_path = os.path.join(outdir, "timeseries.png")
        plot_timeseries(rows, plot_path)
        print(f"Plots written to:       {display_path(plot_path)}")
    except ImportError:
        print("matplotlib not installed -- skipping timeseries.png")

    if not shutil.which("ffmpeg"):
        print(f"ffmpeg not found on PATH -- frames are in {display_path(frame_dir)} but no movie was encoded.")
        return 0
    movie = os.path.join(outdir, "wilting.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(args.fps),
                    "-i", os.path.join(frame_dir, "frame_%04d.jpeg"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", movie], check=True)
    print(f"Movie written to:       {display_path(movie)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
