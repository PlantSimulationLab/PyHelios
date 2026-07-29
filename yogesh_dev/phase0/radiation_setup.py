"""
T0.1 -- Radiation band + light source setup.

DECISION (required by the task spec): this rig uses **plausible RGB**, not
radiometrically calibrated real-spectra radiometry.

Why
---
The end use of this rig (per helios_setup_tasks.md) is: (a) gsplat/NBV
perception experiments, and (b) ground-truth per-pixel semantic/instance
labels + depth. Neither needs absolute-calibrated radiance -- they need
images that look plausible enough for a perception model (or a human) to
be usable, and RGB bands whose relative intensities roughly track visible
red/green/blue so foliage/fruit/sky render with sane colors.

Real-spectra radiometry (`setSourceSpectrum` with an actual solar spectrum,
`setCameraSpectralResponseFromLibrary` with a real sensor response curve,
radiometrically-calibrated leaf/fruit reflectance spectra) would be required
if we were ever going to claim a radiometric quantity (e.g. "this fruit
receives X W/m^2 of PAR", or comparing against a real camera's raw sensor
output for domain-transfer). That is explicitly out of scope for Phase 0.
If a later phase needs that (e.g. T7.6's classical-baseline comparison, or
any sim-to-real transfer claim), revisit this file and switch to
`setSourceSpectrum` / `setCameraSpectralResponseFromLibrary` rather than the
flat per-band flux values used here.

Band choice
-----------
Three bands approximating the visible RGB primaries, using wavelength
bounds in nanometers (matches the task doc's example and the values that
were smoke-tested against the running plugin):
    red:   600-700 nm
    green: 500-600 nm
    blue:  400-500 nm

Flux choice
-----------
Flat, hand-picked flux per band (no real solar spectrum lookup) tuned only
so the rendered images are neither blown out nor near-black at midday sun
angles. Diffuse flux is set to a fixed fraction of direct flux, which is a
crude sky-radiance model -- fine for plausible RGB, not for radiometric
work.

KNOWN ARTIFACT (measured, not fixed -- see PHASE0_LOG.md "Photometric
saturation artifact" for the full flux-sweep evidence): on the 3-apple-tree
scene, ~15-20% of foliage/branch/fruit pixels return an identical fixed
value (~292.4, in whatever internal radiance units getCameraPixelData
returns) across all 3 bands, REGARDLESS of how low the configured flux is
set (confirmed down to flux scaled 1000x smaller than the default here).
This means it is not ordinary over-exposure -- lowering flux does not fix
it, and can make the relative contrast worse (background scales down
linearly with flux while the fixed-value cluster does not). The affected
pixels line up exactly with the tree canopy silhouette (confirmed by
comparing a hot-pixel mask to the rendered shape), and it reproduces on a
SINGLE isolated tree (9.4% of pixels, no neighboring-tree overlap possible)
just as it does on the 3-tree scene (~15-20%), so this is a property of one
apple plant's own procedurally-generated leaf/branch geometry (most likely
self-overlapping tessellated leaf surfaces from the growth model), not a
cross-tree spacing or lighting configuration mistake.
Per-pixel ground-truth (`getPrimitiveDataLabelMap` / `getObjectDataLabelMap`,
validated sub-pixel in T0.3) is unaffected, since those come from a separate
ray-hit-topology pass, not the radiance computation. Anything that consumes
raw RGB pixel values (a future gsplat pass, a perception model) should treat
this as a real, open issue rather than something Phase 0 already solved.
"""

RGB_BANDS = {
    "red": (600.0, 700.0),
    "green": (500.0, 600.0),
    "blue": (400.0, 500.0),
}

# Plausible-RGB flux values (arbitrary units, hand-tuned for a sane-looking
# render -- NOT calibrated W/m^2 solar irradiance).
#
# Tuned small on purpose: writeCameraImage() applies an sRGB transfer
# function directly to the RAW getCameraPixelData value (RadiationCamera.cpp
# lin_to_srgb(): input clamped to [0,1], >=1.0 -> pure white) BEFORE applying
# its own flux_to_pixel_conversion scale factor. So the flux here has to be
# small enough that ordinary reflected radiance lands under ~1.0, not tuned
# via flux_to_pixel_conversion (that parameter only rescales the already
# gamma-compressed [0,1] image afterwards, it doesn't fix an over-bright
# linear input). At flux=480/520/380 background diffuse pixels alone were
# ~14-20 (see PHASE0_LOG.md flux-sweep) -- 15-20x too bright to avoid
# clipping to solid white.
DEFAULT_BAND_FLUX = {
    "red": 9.6,
    "green": 10.4,
    "blue": 7.6,
}

DEFAULT_DIFFUSE_FRACTION = 0.12  # diffuse flux = this * direct flux, per band
DEFAULT_SCATTERING_DEPTH = 1     # T0.1 guidance: start at 1, raise only if leaves look wrong


def setup_bands_and_lights(radiation, zenith=30.0, azimuth=120.0,
                            band_flux=None, diffuse_fraction=DEFAULT_DIFFUSE_FRACTION,
                            scattering_depth=DEFAULT_SCATTERING_DEPTH,
                            sun_radius=0.5, angular_width=0.53):
    """Add the RGB bands + one sun source to a RadiationModel, per T0.1.

    Args:
        radiation: RadiationModel instance (bands/sources are added to it).
        zenith, azimuth: Sun position in degrees.
        band_flux: Optional override dict {band: flux}; defaults to
            DEFAULT_BAND_FLUX (plausible RGB, not calibrated).
        diffuse_fraction: Diffuse flux as a fraction of direct flux per band.
        scattering_depth: Passed to setScatteringDepth for every band.
        sun_radius, angular_width: Passed to addSunSphereRadiationSource.

    Returns:
        sun_source_id
    """
    if band_flux is None:
        band_flux = DEFAULT_BAND_FLUX

    for band, (lo, hi) in RGB_BANDS.items():
        radiation.addRadiationBand(band, lo, hi)

    sun = radiation.addSunSphereRadiationSource(
        radius=sun_radius, zenith=zenith, azimuth=azimuth, angular_width=angular_width
    )

    for band in RGB_BANDS:
        flux = band_flux[band]
        radiation.setSourceFlux(sun, band, flux)
        radiation.setDiffuseRadiationFlux(band, flux * diffuse_fraction)
        radiation.setScatteringDepth(band, scattering_depth)

    return sun
