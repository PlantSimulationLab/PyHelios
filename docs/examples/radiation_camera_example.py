#!/usr/bin/env python3
"""
PyHelios RadiationModel Camera Example: Spectrally-Resolved Apple Imagery

Renders a physically-based synthetic photograph of an apple tree and exports
per-apple YOLO bounding boxes -- the kind of dataset used to train fruit
detection and yield-estimation models.

What makes the image physically meaningful:

- The camera is loaded from the camera library ("iPhone12ProMAX"), so the
  sensor resolution, field of view, and per-channel spectral response curves
  are the real measured ones instead of invented numbers.
- The sun uses the ASTM G173 reference solar spectrum.
- Every surface carries a measured reflectance/transmittance spectrum from the
  Helios spectral libraries (leaf, bark, fruit, soil).

With a spectral camera response, band radiative properties are integrated
against the sensor's sensitivity curve, so pixel color comes out of the physics
rather than being assigned by hand.

Three ordering requirements matter and are easy to get wrong:

1. Load the spectral library XML into the Context BEFORE assigning any
   *_spectrum primitive data. Helios resolves those strings against global
   data; an unresolved label silently falls back to a reflectivity of 0
   (i.e. black surfaces).
2. Call setScatteringDepth(band, >= 1) BEFORE runBand(). Camera ray tracing
   reads scattered flux, so a band left at scattering depth 0 renders as
   all-zero pixels.
3. Add cameras before running the bands.

Labeling note: bounding boxes are keyed on (class_id, primitive_data_value),
so each apple needs its OWN unique integer to get its own box. Giving every
fruit the same ID yields a single box around the whole canopy, which is the
most common mistake when generating detection datasets.

Requirements:
- PyHelios with the radiation and plantarchitecture plugins built
- A GPU: NVIDIA + OptiX is fastest; the Vulkan compute backend also works

Run:
    python docs/examples/radiation_camera_example.py

Output:
    docs/examples/output/radiation_camera/
"""

import math
import os
import sys
from pathlib import Path

from example_output import display_path, get_output_dir
from pyhelios import (
    Context, PlantArchitecture, RadiationModel, RadiationModelError,
    SolarPosition,
)
from pyhelios.assets import get_asset_manager
from pyhelios.types import vec2, vec3, RGBcolor


# Keep ray counts modest so the example finishes in a few minutes.
DIRECT_RAYS = 300
DIFFUSE_RAYS = 500
SCATTERING_DEPTH = 3

# RGB bands, defined WITHOUT explicit wavelength bounds.
#
# This is deliberate and it matters. When a camera spectral response is
# attached, Helios integrates surface reflectance against that response curve
# and uses the result for the camera pixels. If you also set explicit
# wavelength bounds, the SCATTERED flux is instead integrated over the band
# window, so the two paths disagree: scattering carries band-limited colour
# while the camera expects response-weighted colour. With scattering enabled,
# most of what the camera sees is scattered light, and low-chroma natural
# surfaces come out badly skewed -- brown soil renders pink (measured R/G of
# 2.6 instead of the correct 1.2).
#
# Leaving the bounds off keeps both paths on the camera response, which is
# what the Helios C++ sample (samples/tutorial12) does.
RGB_BANDS = ["red", "green", "blue"]

# Wavelength range spanned by the RGB bands. Both the direct and diffuse
# spectra are normalized over this range so their ratio stays physical.
VISIBLE_MIN = 400.0
VISIBLE_MAX = 700.0

# Visible-band irradiance for a clear sky (W/m^2), roughly 45% of the ~1000
# W/m^2 total shortwave, with the sky contributing ~15% of the direct beam.
DIRECT_IRRADIANCE = 450.0
DIFFUSE_IRRADIANCE = 70.0

# Measured spectra from helios-core/plugins/radiation/spectral_data/.
# The library has no apple-specific leaf or fruit spectrum, so these are the
# closest available analogues: a broadleaf tree species for foliage, and
# strawberry for the fruit (strongly red -- ~0.32 reflectance at 650 nm versus
# ~0.08 in the blue and green).
LEAF_REFLECTIVITY = "big_leaf_maple_leaf_reflectivity_0000"
LEAF_TRANSMISSIVITY = "big_leaf_maple_leaf_transmissivity_0000"
FRUIT_REFLECTIVITY = "strawberry_reflectivity_0000"
BARK_REFLECTIVITY = "bark_reflectivity_0000"
SOIL_REFLECTIVITY = "soil_reflectivity_0000"

SOLAR_SPECTRUM = "solar_spectrum_direct_ASTMG173"

SPECTRAL_LIBRARIES = [
    "leaf_surface_spectral_library.xml",
    "bark_surface_spectral_library.xml",
    "fruit_surface_spectral_library.xml",
    "soil_surface_spectral_library.xml",
    "solar_spectrum_ASTMG173.xml",
]

# Class IDs written into the YOLO classes file.
CLASS_APPLE = 0
CLASS_LEAF = 1


def _sun_direction(zenith_deg, azimuth_deg):
    """Unit vector pointing toward the sun.

    Azimuth is measured clockwise from north (+y), matching the Helios
    convention, and zenith is measured from vertical.
    """
    zenith = math.radians(zenith_deg)
    azimuth = math.radians(azimuth_deg)
    return vec3(
        math.sin(zenith) * math.sin(azimuth),
        math.sin(zenith) * math.cos(azimuth),
        math.cos(zenith),
    )


def load_spectral_libraries(context):
    """Load measured spectra into the Context as global data.

    The XML files ship with the radiation plugin build; find them via the
    asset manager so this works for both source and wheel installs.
    """
    build_path = get_asset_manager()._get_helios_build_path()
    if build_path is None:
        raise RuntimeError(
            "Could not locate the Helios build directory. "
            "Rebuild with: build_scripts/build_helios --clean"
        )

    spectral_dir = Path(build_path) / "plugins" / "radiation" / "spectral_data"
    if not spectral_dir.is_dir():
        raise RuntimeError(
            f"Radiation spectral data not found at {spectral_dir}. "
            "Rebuild with: build_scripts/build_helios --clean"
        )

    for filename in SPECTRAL_LIBRARIES:
        path = spectral_dir / filename
        if not path.is_file():
            raise RuntimeError(f"Missing spectral library file: {path}")
        context.loadXML(str(path), quiet=True)

    print(f"  Loaded {len(SPECTRAL_LIBRARIES)} spectral libraries from {spectral_dir}")


def build_apple_tree(context):
    """Grow an apple tree, assign measured spectra, and label each apple.

    Returns the number of apples that received a unique instance label.
    """
    plant = PlantArchitecture(context)
    plant.disableMessages()
    plant.loadPlantModelFromLibrary("apple")

    # Age in days. A mature tree carries fruit.
    plant_id = plant.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 1000.0)

    leaf_objects = plant.getPlantLeafObjectIDs(plant_id)
    fruit_objects = plant.getPlantFruitObjectIDs(plant_id)
    all_uuids = set(plant.getAllPlantUUIDs(plant_id))

    leaf_uuids = context.getObjectPrimitiveUUIDs(leaf_objects) if leaf_objects else []
    fruit_uuids = context.getObjectPrimitiveUUIDs(fruit_objects) if fruit_objects else []

    # Whatever is left over is woody structure (trunk, branches, petioles).
    wood_uuids = list(all_uuids - set(leaf_uuids) - set(fruit_uuids))

    # Optical properties. Leaves transmit; bark, fruit, and soil are opaque,
    # so they get reflectivity only (transmissivity defaults to 0).
    if leaf_uuids:
        context.setPrimitiveDataString(leaf_uuids, "reflectivity_spectrum", LEAF_REFLECTIVITY)
        context.setPrimitiveDataString(leaf_uuids, "transmissivity_spectrum", LEAF_TRANSMISSIVITY)
    if fruit_uuids:
        context.setPrimitiveDataString(fruit_uuids, "reflectivity_spectrum", FRUIT_REFLECTIVITY)
    if wood_uuids:
        context.setPrimitiveDataString(wood_uuids, "reflectivity_spectrum", BARK_REFLECTIVITY)

    # Per-apple instance labels. Bounding boxes are grouped by
    # (class_id, label_value), so each fruit object needs a DISTINCT integer
    # to produce its own box. Numbering starts at 1 because 0 is the
    # "unlabeled" default.
    for instance_id, object_id in enumerate(fruit_objects, start=1):
        uuids = context.getObjectPrimitiveUUIDs([object_id])
        context.setPrimitiveDataInt(uuids, "apple_id", instance_id)

    # Leaves are labeled as a single class instance -- useful as a contrasting
    # "canopy extent" box rather than per-leaf detection targets.
    if leaf_uuids:
        context.setPrimitiveDataInt(leaf_uuids, "canopy_id", 1)

    # Ground plane under the tree, large enough to fill the lower frame.
    ground_uuid = context.addPatch(
        center=vec3(0, 0, 0),
        size=vec2(40, 40),
        color=RGBcolor(0.35, 0.28, 0.22),
    )
    context.setPrimitiveDataString(ground_uuid, "reflectivity_spectrum", SOIL_REFLECTIVITY)

    print(f"  Apple tree: {len(fruit_objects)} apples, {len(leaf_objects)} leaves, "
          f"{len(wood_uuids)} woody primitives")
    print(f"  Scene total: {context.getPrimitiveCount()} primitives")
    return len(fruit_objects)


def main():
    print("PyHelios Radiation Camera Example: Apple Tree Imagery")
    print("=" * 60)

    output_dir = str(get_output_dir("radiation_camera"))
    print(f"Output directory: {display_path(output_dir)}")

    try:
        print("\n1. Loading spectral libraries...")
        context = Context()
        load_spectral_libraries(context)

        print("\n2. Growing apple tree and assigning spectra...")
        apple_count = build_apple_tree(context)

        print("\n3. Enabling atmospheric sky model...")
        # Without this the sky renders BLACK, not blue. Camera rays that escape
        # the scene return sky radiance only when the atmospheric model has been
        # enabled -- setting a diffuse flux alone lights the surfaces but leaves
        # the background at zero. An image that is half black sky also drags the
        # median luminance to 0, and since auto-exposure targets 18% gray on the
        # median, the gain explodes and every lit surface clips to white.
        with SolarPosition(context) as solar:
            solar.setAtmosphericConditions(
                pressure_Pa=101325.0,    # sea level
                temperature_K=293.15,    # 20 C
                humidity_rel=0.5,
                turbidity=0.05,          # clear sky
            )
            solar.enablePragueSkyModel()
            # Computes the spectral/angular sky radiance and stores it in the
            # Context; takes a few seconds.
            solar.updatePragueSkyModel(ground_albedo=0.25)
        print("  Prague sky model enabled (clear sky)")

        print("\n4. Configuring radiation simulation...")
        with RadiationModel(context) as radiation:
            # No wavelength bounds -- see the RGB_BANDS comment above. The
            # camera's spectral response defines what each band measures.
            for band in RGB_BANDS:
                radiation.addRadiationBand(band)
                radiation.setDirectRayCount(band, DIRECT_RAYS)
                radiation.setDiffuseRayCount(band, DIFFUSE_RAYS)
                # Must precede runBand() or camera pixels come out zero.
                radiation.setScatteringDepth(band, SCATTERING_DEPTH)
                # Emissivity defaults to 1. These are shortwave solar bands
                # with no meaningful thermal emission, so emission must be
                # disabled -- otherwise Helios rejects the scene because
                # emissivity + reflectivity + transmissivity exceeds 1.
                radiation.disableEmission(band)

            # Sun with the ASTM G173 reference solar spectrum.
            #
            # A COLLIMATED source is used rather than addSunSphereRadiationSource().
            # The sun-sphere source multiplies its flux by a hardcoded blackbody
            # scaling factor (sigma*5700^4/1288.437, roughly 4.7e4) that neither
            # setSourceSpectrumIntegral() nor setSourceFlux() can override, which
            # puts the direct beam ~1e5x above the diffuse sky and blows the
            # exposure out. Collimated is also the standard way to represent
            # direct-beam irradiance on a surface.
            sun_id = radiation.addCollimatedRadiationSource(_sun_direction(
                zenith_deg=30.0,    # mid-morning sun
                azimuth_deg=120.0,  # southeast
            ))
            radiation.setSourceSpectrum(sun_id, SOLAR_SPECTRUM)
            # Normalize over the VISIBLE range only. The ASTM spectrum extends
            # to 2500 nm, so integrating over its full extent and calling the
            # result a visible-band irradiance inflates the RGB bands by orders
            # of magnitude relative to the diffuse sky.
            radiation.setSourceSpectrumIntegral(
                sun_id, DIRECT_IRRADIANCE, VISIBLE_MIN, VISIBLE_MAX)

            # Diffuse sky uses the same reference spectrum over the same range,
            # so the sun/sky ratio stays physically sensible.
            for band in RGB_BANDS:
                radiation.setDiffuseSpectrum(band, SOLAR_SPECTRUM)
            radiation.setDiffuseSpectrumIntegral(
                DIFFUSE_IRRADIANCE, VISIBLE_MIN, VISIBLE_MAX)

            # Camera loaded from the library: real resolution, FOV, and
            # measured per-channel spectral response.
            #
            # Framing matters more than it looks. Auto-exposure meters on the
            # MEDIAN luminance of the whole frame and targets 18% gray, so a
            # frame dominated by empty sky or bare ground meters on the
            # background instead of the subject and pushes the canopy far up
            # the sRGB curve. Fill the frame with the tree.
            radiation.addRadiationCameraFromLibrary(
                camera_label="apple_cam",
                library_camera_label="iPhone12ProMAX",
                position=vec3(3.2, -3.2, 2.0),
                lookat=vec3(0, 0, 2.0),
                antialiasing_samples=20,
                band_labels=RGB_BANDS,
            )
            print(f"  {len(RGB_BANDS)} spectral bands, iPhone12ProMAX camera, "
                  f"{DIRECT_RAYS} direct / {DIFFUSE_RAYS} diffuse rays")

            print("\n5. Running radiation simulation (this takes a few minutes)...")
            radiation.updateGeometry()
            radiation.runBand(RGB_BANDS)
            print("  Simulation completed")

            print("\n6. Writing RGB image...")
            # The camera library entry uses "auto" exposure, so runBand() has
            # already applied auto-exposure (18% gray target) and white balance
            # to the stored pixel data. writeCameraImage then applies the sRGB
            # transfer curve, so no manual scaling is needed here.
            #
            # Do NOT use writeNormCameraImage for this: it re-divides every
            # band by the single brightest pixel in the scene -- directly-sunlit
            # soil -- which undoes the auto-exposure and washes the tree out to
            # a white silhouette.
            rgb_filename = radiation.writeCameraImage(
                camera="apple_cam",
                bands=RGB_BANDS,
                imagefile_base="apple_tree_rgb",
                image_path=output_dir,
            )
            print(f"  RGB image: {display_path(rgb_filename)}")

            print("\n7. Writing per-apple bounding boxes...")
            radiation.writeImageBoundingBoxes(
                camera_label="apple_cam",
                primitive_data_labels=["apple_id", "canopy_id"],
                object_class_ids=[CLASS_APPLE, CLASS_LEAF],
                image_file=rgb_filename,
                # Resolved relative to image_path, so pass a bare filename.
                classes_txt_file="apple_classes.txt",
                image_path=output_dir,
            )

            label_file = os.path.join(
                output_dir, Path(rgb_filename).stem + ".txt")
            box_count = 0
            if os.path.isfile(label_file):
                with open(label_file) as f:
                    boxes = [ln for ln in f if ln.strip()]
                box_count = len(boxes)
                apple_boxes = sum(
                    1 for ln in boxes if ln.split()[0] == str(CLASS_APPLE))
                print(f"  {box_count} YOLO boxes written "
                      f"({apple_boxes} apples visible of {apple_count} on the tree)")
            print(f"  Labels: {display_path(label_file)}")
            print(f"  Classes: {display_path(os.path.join(output_dir, 'apple_classes.txt'))}")

        print("\n" + "=" * 60)
        print("Done")
        print("=" * 60)
        print(f"\nGenerated in {display_path(output_dir)}:")
        print(f"  {os.path.basename(rgb_filename)} (spectrally-rendered RGB image)")
        print(f"  {os.path.basename(label_file)} (YOLO boxes, one row per apple)")
        print(f"  apple_classes.txt (class ID -> name mapping)")
        return 0

    except RadiationModelError as e:
        print(f"\nRadiationModel error: {e}")
        print("\nThe radiation plugin is likely unavailable. To resolve:")
        print("  1. Ensure a supported GPU is present")
        print("  2. Rebuild: build_scripts/build_helios --clean")
        print("  3. Check status: python -m pyhelios.plugins info radiation")
        return 1


if __name__ == "__main__":
    sys.exit(main())
