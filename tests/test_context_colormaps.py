"""
Tests for the Context colormap helpers and the helios-core 1.3.89 colormap introspection
(getColormapNames / getColormapControlPoints), plus the 1.3.89 calendar fixes as seen through
setDate()/getJulianDate().
"""

from unittest.mock import patch

import pytest

from pyhelios import Context
from pyhelios.types import RGBcolor
from pyhelios.wrappers import UContextWrapper as context_wrapper


EXPECTED_NAMES = {"hot", "cool", "lava", "rainbow", "parula", "gray", "green", "lines", "algae"}


@pytest.mark.cross_platform
class TestColormapIntrospectionValidation:

    def test_1389_guard(self):
        with patch.object(context_wrapper, '_CONTEXT_COLORMAP_1389_AVAILABLE', False):
            with pytest.raises(NotImplementedError, match="1.3.89"):
                context_wrapper.getColormapNamesWrapper()
            with pytest.raises(NotImplementedError, match="1.3.89"):
                context_wrapper.getColormapControlPointsWrapper("hot")

    def test_control_points_rejects_non_string(self):
        with pytest.raises(ValueError, match="string"):
            Context.getColormapControlPoints(3)


@pytest.mark.native_only
class TestColormapIntrospectionNative:

    def test_names_are_static_and_complete(self):
        # Static: callable on the class, with no Context constructed.
        assert set(Context.getColormapNames()) == EXPECTED_NAMES

    @pytest.mark.parametrize("name", sorted(EXPECTED_NAMES))
    def test_control_points_span_zero_to_one(self, name):
        colors, positions = Context.getColormapControlPoints(name)
        assert len(colors) == len(positions) >= 2
        assert all(isinstance(c, RGBcolor) for c in colors)
        assert positions[0] == pytest.approx(0.0)
        assert positions[-1] == pytest.approx(1.0)
        assert all(a < b for a, b in zip(positions, positions[1:]))
        for c in colors:
            assert 0.0 <= c.r <= 1.0 and 0.0 <= c.g <= 1.0 and 0.0 <= c.b <= 1.0

    def test_unknown_name_lists_valid_names(self):
        with pytest.raises(Exception, match="algae"):
            Context.getColormapControlPoints("viridis")

    def test_generated_colormap_endpoints_match_control_points(self):
        colors, _ = Context.getColormapControlPoints("algae")
        with Context() as context:
            ramp = context.generateColormap("algae", 16)
        assert len(ramp) == 16
        for got, want in ((ramp[0], colors[0]), (ramp[-1], colors[-1])):
            assert (got.r, got.g, got.b) == pytest.approx((want.r, want.g, want.b), abs=1e-5)

    @pytest.mark.parametrize("name", ["algae", "lines"])
    def test_new_colormaps_accepted_by_generateColormap(self, name):
        with Context() as context:
            assert len(context.generateColormap(name, 7)) == 7

    @pytest.mark.parametrize("n", [0, 1])
    def test_generateColormap_requires_two_colors(self, n):
        with Context() as context:
            with pytest.raises(Exception, match="(?i)at least 2"):
                context.generateColormap("hot", n)

    def test_pseudocolor_constant_data_uses_first_color(self):
        from pyhelios.types import vec3, vec2
        with Context() as context:
            uuids = [context.addPatch(center=vec3(i, 0, 0), size=vec2(1, 1)) for i in range(3)]
            for u in uuids:
                context.setPrimitiveDataFloat(u, "value", 2.5)
            context.colorPrimitiveByDataPseudocolor(uuids, "value", "algae", 10)
            first = Context.getColormapControlPoints("algae")[0][0]
            for u in uuids:
                c = context.getPrimitiveColor(u)
                assert (c.r, c.g, c.b) == pytest.approx((first.r, first.g, first.b), abs=1e-5)


@pytest.mark.native_only
class TestCalendarJulianDay:
    """helios-core 1.3.89 fixed Calendar2Julian() for August of leap years and the Gregorian century rule."""

    @pytest.mark.parametrize("year,month,day,julian", [
        (2024, 8, 1, 214),    # was 215 before 1.3.89
        (2024, 8, 31, 244),
        (2024, 7, 31, 213),
        (2023, 8, 1, 213),
        (2100, 3, 1, 60),     # 2100 is not a leap year; was 61
        (2000, 3, 1, 61),     # 2000 is
    ])
    def test_julian_day(self, year, month, day, julian):
        with Context() as context:
            context.setDate(year, month, day)
            assert context.getJulianDate() == julian
