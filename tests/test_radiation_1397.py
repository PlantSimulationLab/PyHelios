"""
Tests for the helios-core 1.3.97 RadiationModel periodic-boundary additions:
excluded primitives, a limited number of repeats, and "none"/"" removing the boundary.

The native tests run on any ray-tracing backend (including the Vulkan software BVH), so they
construct through radiation_model_or_skip() rather than being marked requires_gpu.
"""

import pytest

from pyhelios import Context, RadiationModel
from pyhelios.exceptions import HeliosError
from pyhelios.types import vec2, vec3, int2
from pyhelios.wrappers import URadiationModelWrapper as radiation_wrapper

from tests.test_radiation_model import radiation_model_or_skip


def _unbound_enforce(*args, **kwargs):
    """Call enforcePeriodicBoundary's body on a bare instance, bypassing the plugin check.

    Argument validation happens before any native call, so it can be exercised without a
    native library or a ray-tracing backend.
    """
    model = object.__new__(RadiationModel)
    return RadiationModel.enforcePeriodicBoundary.__wrapped__(model, *args, **kwargs)


@pytest.mark.cross_platform
class TestPeriodicBoundaryValidation:

    @pytest.mark.parametrize("boundary", ["xyz", "z", "XY", "periodic"])
    def test_unknown_boundary_raises(self, boundary):
        with pytest.raises(ValueError, match="Unknown periodic boundary"):
            _unbound_enforce(boundary)

    def test_boundary_must_be_string(self):
        with pytest.raises(ValueError, match="Boundary must be a string"):
            _unbound_enforce(None)

    def test_max_repeats_must_be_int2_positional_and_keyword(self):
        with pytest.raises(ValueError, match="max_repeats must be an int2"):
            _unbound_enforce("xy", [], (5, 5))
        with pytest.raises(ValueError, match="max_repeats must be an int2"):
            _unbound_enforce("xy", max_repeats=vec2(5, 5))

    def test_excluded_uuids_must_be_non_negative_integers(self):
        with pytest.raises(ValueError, match="excluded_uuids must be a list"):
            _unbound_enforce("xy", excluded_uuids=5)
        with pytest.raises(ValueError, match="excluded_uuids must be a list"):
            _unbound_enforce("xy", "12")
        with pytest.raises(ValueError, match="non-negative integer UUIDs"):
            _unbound_enforce("xy", excluded_uuids=[1, -2])
        with pytest.raises(ValueError, match="non-negative integer UUIDs"):
            _unbound_enforce("xy", excluded_uuids=[1.5])

    def test_options_require_1397_library(self, monkeypatch):
        monkeypatch.setattr(radiation_wrapper, "_RADIATION_1397_AVAILABLE", False)
        with pytest.raises(NotImplementedError, match="1.3.97"):
            radiation_wrapper.enforcePeriodicBoundaryWithOptions(object(), "xy", [1], (1, 1))


# Ground at z=0 under an opaque roof of the same footprint at z=1. With the roof repeating in an
# "xy" periodic boundary the ground sees no sky at all; without a periodic boundary it sees the sky
# through the open sides. Scattering and emission are off, so the ground's absorbed flux is the diffuse sky alone.
DIFFUSE_FLUX = 1000.0


def _ground_flux(configure, roof_size=1.0):
    with Context() as context:
        ground = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        roof = context.addPatch(center=vec3(0, 0, 1), size=vec2(roof_size, roof_size))
        with radiation_model_or_skip(context) as radiation:
            radiation.disableMessages()
            radiation.addRadiationBand("SW")
            radiation.disableEmission("SW")  # otherwise the roof underside emits sigma*T^4 onto the ground
            radiation.setDiffuseRayCount("SW", 20000)
            radiation.setDiffuseRadiationFlux("SW", DIFFUSE_FLUX)
            radiation.setScatteringDepth("SW", 0)
            configure(radiation, ground, roof)
            radiation.updateGeometry()
            radiation.runBand("SW")
            return float(radiation.getAbsorbedFlux("SW", [ground])[0])


@pytest.mark.native_only
class TestPeriodicBoundary1397Native:

    def test_baseline_geometry_is_discriminating(self):
        open_sky = _ground_flux(lambda r, g, roof: None)
        enclosed = _ground_flux(lambda r, g, roof: r.enforcePeriodicBoundary("xy"))
        assert open_sky > 0.2 * DIFFUSE_FLUX
        assert enclosed < 0.05 * open_sky

    @pytest.mark.parametrize("removal", ["none", ""])
    def test_none_removes_periodic_boundary(self, removal):
        def configure(r, g, roof):
            r.enforcePeriodicBoundary("xy")
            r.enforcePeriodicBoundary(removal)

        open_sky = _ground_flux(lambda r, g, roof: None)
        removed = _ground_flux(configure)
        assert removed == pytest.approx(open_sky, rel=0.1)

    def test_excluded_roof_appears_only_once(self):
        # The roof is a little smaller than the ground so that it lies strictly inside the period.
        open_sky = _ground_flux(lambda r, g, roof: None, roof_size=0.9)
        excluded = _ground_flux(lambda r, g, roof: r.enforcePeriodicBoundary("xy", excluded_uuids=[roof]), roof_size=0.9)
        # The repeated ground copies are flat and hide no sky, so with the roof standing only in
        # the central copy the ground sees what it does with no periodic boundary.
        assert excluded == pytest.approx(open_sky, rel=0.1)

    def test_excluded_uuids_positional(self):
        open_sky = _ground_flux(lambda r, g, roof: None, roof_size=0.9)
        excluded = _ground_flux(lambda r, g, roof: r.enforcePeriodicBoundary("xy", [roof]), roof_size=0.9)
        assert excluded == pytest.approx(open_sky, rel=0.1)

    def test_zero_repeats_is_no_periodic_boundary(self):
        open_sky = _ground_flux(lambda r, g, roof: None)
        zero = _ground_flux(lambda r, g, roof: r.enforcePeriodicBoundary("xy", max_repeats=int2(0, 0)))
        assert zero == pytest.approx(open_sky, rel=0.1)

    def test_limited_repeats_lie_between_open_and_unlimited(self):
        open_sky = _ground_flux(lambda r, g, roof: None)
        unlimited = _ground_flux(lambda r, g, roof: r.enforcePeriodicBoundary("xy"))
        limited = _ground_flux(lambda r, g, roof: r.enforcePeriodicBoundary("xy", [], int2(1, 1)))
        assert unlimited < limited < 0.9 * open_sky

    def test_native_rejects_bad_options(self):
        with Context() as context:
            ground = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
            with radiation_model_or_skip(context) as radiation:
                with pytest.raises(HeliosError, match="does not exist"):
                    radiation.enforcePeriodicBoundary("xy", excluded_uuids=[ground + 1000])
                with pytest.raises(HeliosError, match="must not be negative"):
                    radiation.enforcePeriodicBoundary("xy", max_repeats=int2(-1, 2))
                with pytest.raises(HeliosError, match="not periodic in y"):
                    radiation.enforcePeriodicBoundary("x", max_repeats=int2(2, 3))
                # A valid call after the failures is still accepted
                radiation.enforcePeriodicBoundary("x", [ground], int2(2, 0))
