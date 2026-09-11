"""
Tests for the process-wide random number generator bindings (helios-core v1.3.85+).

helios-core has two generators: one per Context (seeded by Context.seedRandomGenerator)
and one process-wide generator behind the free function helios::randu(), which plug-in
code uses where no Context is at hand. Global.seedRandomGenerator() seeds the second.
"""
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
