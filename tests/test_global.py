"""
Tests for the process-wide random number generator bindings (helios-core v1.3.85+).

helios-core has two generators: one per Context (seeded by Context.seedRandomGenerator)
and one process-wide generator behind the free function helios::randu(), which plug-in
code uses where no Context is at hand. Global.seedRandomGenerator() seeds the second.
"""
import math

import pytest

from pyhelios import Global
from pyhelios.wrappers import UGlobalWrapper as global_wrapper


@pytest.mark.cross_platform
class TestGlobalRandomGeneratorValidation:
    """Argument validation happens in Python and needs no native library."""

    def test_seed_rejects_non_int(self):
        if not global_wrapper._GLOBAL_RNG_FUNCTIONS_AVAILABLE:
            pytest.skip("Global RNG functions not available (native library predates 1.3.85 or mock mode)")
        with pytest.raises(ValueError, match="seed must be an int"):
            Global.seedRandomGenerator(1.5)
        with pytest.raises(ValueError, match="seed must be an int"):
            Global.seedRandomGenerator(True)

    def test_seed_rejects_out_of_range(self):
        if not global_wrapper._GLOBAL_RNG_FUNCTIONS_AVAILABLE:
            pytest.skip("Global RNG functions not available (native library predates 1.3.85 or mock mode)")
        with pytest.raises(ValueError, match="unsigned 32-bit"):
            Global.seedRandomGenerator(-1)
        with pytest.raises(ValueError, match="unsigned 32-bit"):
            Global.seedRandomGenerator(2 ** 32)

    def test_randu_partial_range_rejected(self):
        # Rejected before any native call, so this holds in mock mode too.
        with pytest.raises(ValueError, match="both imin and imax"):
            Global.randu(imin=0)
        with pytest.raises(ValueError, match="both imin and imax"):
            Global.randu(imax=5)

    def test_unavailable_library_raises_clear_error(self):
        if global_wrapper._GLOBAL_RNG_FUNCTIONS_AVAILABLE:
            pytest.skip("Native library provides the 1.3.85 RNG functions")
        with pytest.raises(RuntimeError, match="helios-core v1.3.85"):
            Global.seedRandomGenerator(1)
        with pytest.raises(RuntimeError, match="helios-core v1.3.85"):
            Global.randu()


@pytest.mark.native_only
class TestGlobalRandomGenerator:
    """The bindings against the real library."""

    @pytest.fixture(autouse=True)
    def _require(self, check_native_library):
        if not global_wrapper._GLOBAL_RNG_FUNCTIONS_AVAILABLE:
            pytest.skip("Global RNG functions not available (native library predates helios-core 1.3.85)")

    def test_randu_in_unit_interval(self):
        draws = [Global.randu() for _ in range(200)]
        assert all(isinstance(d, float) for d in draws)
        assert all(0.0 <= d < 1.0 for d in draws)
        assert len(set(draws)) > 1

    def test_seed_makes_sequence_reproducible(self):
        Global.seedRandomGenerator(12345)
        first = [Global.randu() for _ in range(10)]
        Global.seedRandomGenerator(12345)
        second = [Global.randu() for _ in range(10)]
        assert first == second
        Global.seedRandomGenerator(54321)
        assert [Global.randu() for _ in range(10)] != first

    def test_seed_is_independent_of_context_generator(self):
        """Seeding the Context generator must not touch the process-wide one, and vice versa."""
        from pyhelios import Context
        Global.seedRandomGenerator(7)
        expected = [Global.randu() for _ in range(5)]
        with Context() as context:
            Global.seedRandomGenerator(7)
            context.seedRandomGenerator(99)
            context.randu()
            assert [Global.randu() for _ in range(5)] == expected

    def test_randu_int_is_inclusive_of_both_endpoints(self):
        """helios-core 1.3.85 made randu(int,int) uniform over the closed range."""
        Global.seedRandomGenerator(2026)
        draws = {Global.randu(0, 2) for _ in range(300)}
        assert draws == {0, 1, 2}
        assert all(isinstance(Global.randu(-3, 3), int) for _ in range(5))

    def test_randu_int_degenerate_range_returns_imin(self):
        assert Global.randu(4, 4) == 4
        assert Global.randu(9, 2) == 9


@pytest.mark.cross_platform
class TestLeafAngleDistributionCDFAvailability:
    """The 1.3.87 CDF bindings degrade to a clear error on an older library."""

    def test_unavailable_library_raises_clear_error(self):
        if global_wrapper._LEAF_ANGLE_CDF_FUNCTIONS_AVAILABLE:
            pytest.skip("Native library provides the 1.3.87 CDF functions")
        for call in (lambda: Global.evaluateBetaDistributionCDF(0.5, 1.0, 1.0),
                     lambda: Global.invertBetaDistributionCDF(0.5, 1.0, 1.0),
                     lambda: Global.evaluateEllipsoidalAzimuthCDF(0.5, 0.5, 0.0),
                     lambda: Global.invertEllipsoidalAzimuthCDF(0.5, 0.5, 0.0)):
            with pytest.raises(RuntimeError, match="helios-core v1.3.87"):
                call()

    def test_guard_matches_its_registration_block(self):
        """A wrapper checking the wrong flag would call a function with no argtypes set."""
        from unittest.mock import patch
        with patch.object(global_wrapper, '_LEAF_ANGLE_CDF_FUNCTIONS_AVAILABLE', False):
            with pytest.raises(RuntimeError, match="1.3.87"):
                global_wrapper.evaluateBetaDistributionCDF(0.5, 1.0, 1.0)
            with pytest.raises(RuntimeError, match="1.3.87"):
                global_wrapper.invertBetaDistributionCDF(0.5, 1.0, 1.0)
            with pytest.raises(RuntimeError, match="1.3.87"):
                global_wrapper.evaluateEllipsoidalAzimuthCDF(0.5, 0.5, 0.0)
            with pytest.raises(RuntimeError, match="1.3.87"):
                global_wrapper.invertEllipsoidalAzimuthCDF(0.5, 0.5, 0.0)


@pytest.mark.native_only
class TestLeafAngleDistributionCDF:
    """Beta inclination / ellipsoidal azimuth CDFs and their inverses (helios-core 1.3.87)."""

    def _skip_if_unavailable(self):
        if not global_wrapper._LEAF_ANGLE_CDF_FUNCTIONS_AVAILABLE:
            pytest.skip("Leaf angle CDF functions not available "
                        "(native library predates 1.3.87 or mock mode)")

    def test_beta_cdf_spans_zero_to_one_over_the_inclination_range(self):
        self._skip_if_unavailable()
        assert Global.evaluateBetaDistributionCDF(0.0, 1.0, 1.0) == pytest.approx(0.0)
        assert Global.evaluateBetaDistributionCDF(math.pi / 2, 1.0, 1.0) == pytest.approx(1.0)

    def test_beta_cdf_uniform_case_is_linear_in_angle(self):
        """mu = nu = 1 is the uniform distribution on [0, pi/2], so the CDF is theta/(pi/2)."""
        self._skip_if_unavailable()
        for frac in (0.25, 0.5, 0.75):
            theta = frac * (math.pi / 2)
            assert Global.evaluateBetaDistributionCDF(theta, 1.0, 1.0) == pytest.approx(
                frac, abs=1e-5)

    def test_beta_cdf_saturates_outside_the_range(self):
        """theta is clamped rather than extrapolated, so out-of-range values do not error."""
        self._skip_if_unavailable()
        assert Global.evaluateBetaDistributionCDF(-1.0, 2.0, 3.0) == pytest.approx(0.0)
        assert Global.evaluateBetaDistributionCDF(math.pi, 2.0, 3.0) == pytest.approx(1.0)

    def test_beta_cdf_is_monotonic(self):
        self._skip_if_unavailable()
        values = [Global.evaluateBetaDistributionCDF(i / 20 * (math.pi / 2), 2.0, 3.0)
                  for i in range(21)]
        assert values == sorted(values)

    def test_beta_cdf_inverse_round_trips(self):
        self._skip_if_unavailable()
        for probability in (0.05, 0.25, 0.5, 0.75, 0.95):
            theta = Global.invertBetaDistributionCDF(probability, 2.0, 3.0)
            assert 0.0 <= theta <= math.pi / 2
            assert Global.evaluateBetaDistributionCDF(theta, 2.0, 3.0) == pytest.approx(
                probability, abs=1e-4)

    def test_beta_cdf_inverse_endpoints(self):
        self._skip_if_unavailable()
        assert Global.invertBetaDistributionCDF(0.0, 2.0, 3.0) == pytest.approx(0.0)
        assert Global.invertBetaDistributionCDF(1.0, 2.0, 3.0) == pytest.approx(math.pi / 2)

    def test_beta_mean_follows_the_documented_parameterization(self):
        """Mean inclination is (pi/2)*nu/(mu+nu); the median must move the same way."""
        self._skip_if_unavailable()
        planophile = Global.invertBetaDistributionCDF(0.5, 5.0, 1.0)   # nu small -> near 0
        erectophile = Global.invertBetaDistributionCDF(0.5, 1.0, 5.0)  # nu large -> near pi/2
        assert planophile < erectophile, (
            f"nu is the numerator of the mean: {planophile} should be below {erectophile}")

    @pytest.mark.parametrize("mu,nu", [(0.0, 1.0), (-1.0, 1.0), (1.0, 0.0), (1.0, -2.0)])
    def test_beta_cdf_rejects_non_positive_parameters(self, mu, nu):
        self._skip_if_unavailable()
        with pytest.raises(Exception, match="(?i)positive"):
            Global.evaluateBetaDistributionCDF(0.5, mu, nu)
        with pytest.raises(Exception, match="(?i)positive"):
            Global.invertBetaDistributionCDF(0.5, mu, nu)

    @pytest.mark.parametrize("bad", [-0.01, 1.01])
    def test_beta_inverse_rejects_out_of_range_probability(self, bad):
        self._skip_if_unavailable()
        with pytest.raises(Exception, match="(?i)probability"):
            Global.invertBetaDistributionCDF(bad, 2.0, 3.0)

    def test_azimuth_cdf_inverse_round_trips(self):
        self._skip_if_unavailable()
        for probability in (0.1, 0.25, 0.5, 0.75, 0.9):
            phi = Global.invertEllipsoidalAzimuthCDF(probability, 0.5, 30.0)
            assert 0.0 <= phi < 2 * math.pi + 1e-6
            assert Global.evaluateEllipsoidalAzimuthCDF(phi, 0.5, 30.0) == pytest.approx(
                probability, abs=1e-4)

    def test_azimuth_cdf_zero_eccentricity_is_uniform(self):
        """A circle has no preferred direction, so the CDF is phi/(2*pi)."""
        self._skip_if_unavailable()
        for frac in (0.25, 0.5, 0.75):
            phi = frac * 2 * math.pi
            assert Global.evaluateEllipsoidalAzimuthCDF(phi, 0.0, 0.0) == pytest.approx(
                frac, abs=1e-4)

    @pytest.mark.parametrize("bad", [-0.01, 1.01])
    def test_azimuth_cdf_rejects_out_of_range_eccentricity(self, bad):
        self._skip_if_unavailable()
        with pytest.raises(Exception, match="(?i)eccentricity"):
            Global.evaluateEllipsoidalAzimuthCDF(1.0, bad, 0.0)
        with pytest.raises(Exception, match="(?i)eccentricity"):
            Global.invertEllipsoidalAzimuthCDF(0.5, bad, 0.0)

    @pytest.mark.parametrize("bad", [-0.01, 1.01])
    def test_azimuth_inverse_rejects_out_of_range_probability(self, bad):
        self._skip_if_unavailable()
        with pytest.raises(Exception, match="(?i)probability"):
            Global.invertEllipsoidalAzimuthCDF(bad, 0.5, 0.0)
