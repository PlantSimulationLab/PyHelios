"""
Value-correctness tests for the SolarPosition plugin.

===============================================================================
WHY THIS FILE EXISTS
===============================================================================

There is already a test file next to this one: test_solarposition.py. It has
about 35 tests, and they check that the methods RUN. Here is a real example
from it:

    elevation = solar.getSunElevation()
    assert -90 <= elevation <= 90
    assert elevation > 0

That test passes whether the function returns 23.1 degrees or 0.40 radians,
because both numbers sit inside the range -90..90. So it proves the method did
not crash. It does not prove the answer is CORRECT.

This file checks correctness. Every test below is written so that a wrong unit,
a wrong sign, or a wrong formula makes it fail.

===============================================================================
HOW THIS FILE IS ORGANISED
===============================================================================

Five sections, each a different KIND of test. You will use all five kinds again
when you test the radiation model, so the sections matter more than the
individual tests:

  1. REFERENCE VALUES    Compare against an answer somebody already verified.
  2. INVARIANTS          Relationships true for every input, so no table needed.
  3. CONTRACT            The documentation promises X; check the code does X.
  4. VALIDATION          Bad input must be REJECTED, and we assert it is.
  5. CHARACTERISATION    Record what the code gets wrong today, on purpose.

===============================================================================
HOW TO RUN IT
===============================================================================

    cd helios_gui/backend-api/pyhelios
    ../Env/Scripts/python.exe -m pytest tests/test_solarposition_values.py -v -o addopts=""

The `-o addopts=""` part is only needed because pytest.ini passes --forked and
the pytest-forked package is not installed in Env. Install it with
`pip install pytest-forked` and you can drop that flag.

Expected result: 15 passed, 2 xfailed. The 2 xfailed are a real bug, explained
in section 3.
===============================================================================
PYTEST IN FIVE MINUTES
===============================================================================

pytest finds tests by NAME, not by registration. It looks for:
    - files     named  test_*.py
    - classes   named  Test*        (grouping only; no inheritance needed)
    - functions named  test_*

A test PASSES if it finishes without raising. It FAILS if any `assert` is
false. There is no "return True" — a silent finish means success.

The tools used in this file, each explained again at its first appearance:

    assert x == y            plain Python; pytest rewrites it so a failure
                             prints the actual values, not just "False"
    pytest.approx(v, abs=t)  compare floats with a tolerance; never use == on
                             floats, because 0.1 + 0.2 != 0.3 in binary
    pytest.raises(Error)     assert that a block DOES throw
    @pytest.fixture          shared setup + cleanup for several tests
    @pytest.mark.native_only a label from pytest.ini; lets CI skip tests that
                             need the compiled Helios library
    @pytest.mark.xfail       "this is expected to fail" — see section 3
"""

import math

import pytest

from pyhelios import Context, SolarPosition, SolarPositionError


# =============================================================================
# REFERENCE DATA
# =============================================================================
# These numbers are NOT invented. Inventing an expected value produces a test
# that only proves the code agrees with your guess.
#
# They come from Helios's own C++ test suite:
#     plugins/solarposition/tests/selfTest.cpp
#
# That suite was written by the Helios authors and is run on every Helios
# build, so its numbers are independently verified. Copying them into Python
# checks that the PyHelios wrapper reaches the same answer the C++ does.
# =============================================================================

# From selfTest.cpp, TEST_CASE("SolarPosition sun position Boulder").
# NOTE the longitude sign: Helios uses POSITIVE-WEST, the opposite of Google
# Maps and every GIS tool. Boulder is 105.2 degrees WEST, so Helios wants
# +105.2369. Passing -105.2369 puts the sun on the wrong side of the sky and
# NOTHING warns you — which is exactly why the Boulder test below matters.
BOULDER = dict(utc_offset=7, latitude=40.1250, longitude=105.2369)
BOULDER_DATE = (2000, 1, 1)
BOULDER_TIME = (10, 30)
BOULDER_ELEVATION_DEG = 29.49   # selfTest allows +/- 10 deg
BOULDER_AZIMUTH_DEG = 154.18    # selfTest allows +/- 5 deg

# From selfTest.cpp, TEST_CASE("SolarPosition ambient longwave model").
LONGWAVE = dict(utc_offset=6, latitude=36.5289, longitude=97.4439)
LONGWAVE_DATE = (2003, 5, 5)
LONGWAVE_TIME = (9, 10)
# Units matter enormously here and are easy to get wrong:
#   pressure    Pascals, NOT hectopascals  (101325, not 1013)
#   temperature Kelvin,  NOT Celsius       (290, not 17)
#   humidity    FRACTION, NOT percent      (0.5, not 50)
#   turbidity   Angstrom beta, NOT Linke   (0.02, not 3.0)
# Section 5 shows what happens when you get two of these wrong.
LONGWAVE_CONDITIONS = (101325.0, 290.0, 0.5, 0.02)
LONGWAVE_EXPECTED_WM2 = 310.03192


def _solar(date, time, site):
    """Build a Context at a fixed date/time, plus a SolarPosition for a site.

    Every test needs the same three steps: make a Context, set the date and
    time on it, then attach a SolarPosition. Doing that inline in each test
    means eight copies of the same four lines, and when one copy drifts you get
    a failure that points at the setup instead of at the thing being tested.

    The leading underscore is a Python convention meaning "internal helper".
    It also stops pytest collecting it — pytest only collects names starting
    with `test_`, so a helper named `solar` would be fine too, but the
    underscore makes the intent obvious to a reader.

    Returns (context, solar). The CALLER must close both; see the try/finally
    in the first test for why.
    """
    context = Context()
    context.setDate(*date)   # *date unpacks (2000, 1, 1) into three arguments
    context.setTime(*time)
    return context, SolarPosition(context, **site)  # **site unpacks the dict


# =============================================================================
# SECTION 1 — REFERENCE VALUES
# =============================================================================
# The strongest kind of test: a known input with an independently known answer.
#
# Strength:  catches almost any error anywhere in the chain.
# Weakness:  you need a trustworthy source for the expected number, and the
#            test only covers the one input you picked.
# =============================================================================

@pytest.mark.native_only
class TestAgainstHeliosReferenceValues:
    """Compare against numbers Helios's own C++ suite asserts.

    `@pytest.mark.native_only` is a LABEL, declared in pytest.ini. It does
    nothing on its own. It lets CI run `pytest -m "not native_only"` on a
    machine with no compiled Helios library and skip these automatically.

    The class is pure grouping. It does not inherit from anything, has no
    setUp, and exists only so `pytest -v` prints related tests together.
    """

    def test_boulder_sun_angles_match_cpp_selftest(self):
        """Sun angles for Boulder must match selfTest.cpp within its tolerance.

        This is the single most valuable test in the file. One assertion
        exercises the whole chain at once:

            date handling -> UTC offset sign -> longitude sign convention
            -> Iqbal's solar geometry equations -> the C-to-Python wrapper

        If ANY link is wrong the angle moves and this fails. That is what makes
        it worth more than five narrow tests.

        Why the tolerance is 10 degrees and not 0.01: selfTest.cpp itself
        allows +/- 10. Solar position models disagree slightly, and the point
        of the test is to catch a sun on the wrong side of the sky, not to
        pin down the last decimal. A tolerance that is too tight produces a
        test that fails for harmless reasons and gets deleted.
        """
        context, solar = _solar(BOULDER_DATE, BOULDER_TIME, BOULDER)
        try:
            # math.degrees converts radians -> degrees. We must do this because
            # the library returns radians despite documenting degrees; that bug
            # is the subject of section 3. Here we simply convert so this test
            # measures the ANGLE rather than the unit mistake.
            elevation_deg = math.degrees(solar.getSunElevation())
            azimuth_deg = math.degrees(solar.getSunAzimuth())

            # The string after the comma is the failure message. pytest already
            # prints both values, but a message that says what the numbers MEAN
            # turns a puzzle into an instruction.
            assert abs(elevation_deg - BOULDER_ELEVATION_DEG) <= 10.0, (
                f"elevation {elevation_deg:.2f} deg is more than 10 deg from the "
                f"selfTest reference {BOULDER_ELEVATION_DEG} deg"
            )
            assert abs(azimuth_deg - BOULDER_AZIMUTH_DEG) <= 5.0, (
                f"azimuth {azimuth_deg:.2f} deg is more than 5 deg from the "
                f"selfTest reference {BOULDER_AZIMUTH_DEG} deg"
            )
        finally:
            # `finally` runs whether the test passed, failed, or errored.
            # Without it, a failing assert would skip the cleanup and leak the
            # native C++ objects, which can crash LATER tests — producing a
            # confusing failure far away from the real cause.
            solar.__exit__(None, None, None)
            context.__exit__(None, None, None)

    def test_ambient_longwave_matches_cpp_selftest(self):
        """Prata (1996) sky longwave must reproduce the C++ value exactly.

        Longwave involves no ray tracing and no randomness — it is one closed
        formula over air temperature and humidity. So unlike the angles above,
        we can demand near-exact agreement.

        `rel=1e-6` means "within one part in a million", a RELATIVE tolerance.
        Use rel for large numbers (310.03192) and abs for numbers near zero,
        where a relative tolerance becomes meaninglessly tight.
        """
        context, solar = _solar(LONGWAVE_DATE, LONGWAVE_TIME, LONGWAVE)
        try:
            # The modern API: set the atmosphere once, then call getters with
            # no arguments. The old four-argument getters still exist but are
            # marked [[deprecated]] in SolarPosition.h.
            solar.setAtmosphericConditions(*LONGWAVE_CONDITIONS)
            longwave = solar.getAmbientLongwaveFlux()

            assert longwave == pytest.approx(LONGWAVE_EXPECTED_WM2, rel=1e-6)
        finally:
            solar.__exit__(None, None, None)
            context.__exit__(None, None, None)


# =============================================================================
# SECTION 2 — INVARIANTS
# =============================================================================
# A property that must hold for EVERY input, not just the one you tested.
#
# Strength:  needs no reference table, and stays valid forever. These survive
#            refactors that break reference tests.
# Weakness:  passing does not prove the value is right, only self-consistent.
#            A model that returns the same wrong angle twice still satisfies
#            "the vector agrees with the angles".
#
# Use both kinds together. Section 1 anchors the values; section 2 covers all
# the inputs section 1 could not.
# =============================================================================

@pytest.mark.native_only
class TestPhysicalInvariants:
    """Properties true by definition, so a break is always a bug."""

    def test_elevation_and_zenith_are_complementary(self):
        """elevation + zenith is a right angle, by definition.

        Elevation is measured UP from the horizon; zenith is measured DOWN
        from straight overhead. They describe the same direction from opposite
        ends, so together they always make 90 degrees.

        Asserted in RADIANS (pi/2) because that is what the library actually
        returns. Section 3 asserts the same thing in degrees to document the
        mismatch with the docstrings.

        `abs=1e-5` is an ABSOLUTE tolerance: the two sides may differ by up to
        0.00001. Floating-point arithmetic is never exact, so `== math.pi / 2`
        would fail on rounding alone.
        """
        context, solar = _solar((2023, 6, 21), (12, 0), dict(
            utc_offset=0, latitude=0.0, longitude=0.0))
        try:
            total = solar.getSunElevation() + solar.getSunZenith()
            assert total == pytest.approx(math.pi / 2, abs=1e-5)
        finally:
            solar.__exit__(None, None, None)
            context.__exit__(None, None, None)

    def test_direction_vector_is_unit_length(self):
        """A direction carries no magnitude, so its length must be 1.

        getSunDirectionVector returns "which way is the sun", not "how far" or
        "how bright". By convention such a vector is normalised to length 1.
        If a refactor accidentally scaled it, everything downstream that
        multiplies by it would silently change.
        """
        context, solar = _solar((2023, 6, 21), (12, 0), dict(
            utc_offset=0, latitude=0.0, longitude=0.0))
        try:
            v = solar.getSunDirectionVector()
            magnitude = math.sqrt(v.x ** 2 + v.y ** 2 + v.z ** 2)
            assert magnitude == pytest.approx(1.0, abs=1e-4)
        finally:
            solar.__exit__(None, None, None)
            context.__exit__(None, None, None)

    def test_direction_vector_agrees_with_elevation(self):
        """The vector and the angles must describe the SAME sun.

        Helios exposes the sun position two ways: as angles (elevation,
        azimuth) and as a 3D vector. Two code paths, one truth. If somebody
        fixes a bug in one and forgets the other, they silently disagree and
        no other test would notice.

        z is the vertical component of a unit vector, and elevation is the
        angle above the horizontal, so trigonometry demands z == sin(elevation).
        """
        context, solar = _solar((2023, 6, 21), (12, 0), dict(
            utc_offset=0, latitude=0.0, longitude=0.0))
        try:
            v = solar.getSunDirectionVector()
            assert v.z == pytest.approx(math.sin(solar.getSunElevation()), abs=1e-5)
        finally:
            solar.__exit__(None, None, None)
            context.__exit__(None, None, None)

    def test_sun_is_below_horizon_at_midnight(self):
        """Elevation must be negative at 00:30. Catches sign errors.

        This is the cheapest possible test and one of the most useful. The two
        sign conventions in this plugin — positive-WEST longitude and
        positive-WEST UTC offset — are both inverted relative to every other
        tool. Getting either backwards typically puts the sun UP at midnight.

        A range check (`-90 <= elevation <= 90`) would happily accept that.
        This one would not.
        """
        context, solar = _solar((2023, 6, 21), (0, 30), dict(
            utc_offset=0, latitude=40.0, longitude=0.0))
        try:
            assert solar.getSunElevation() < 0
        finally:
            solar.__exit__(None, None, None)
            context.__exit__(None, None, None)

    def test_elevation_rises_through_the_morning(self):
        """Elevation must increase from 08:00 to 10:00 to 12:00.

        This tests a TREND rather than a value, which means it needs no
        reference table and works at any site on any date before solar noon.

        Note the loop builds a fresh Context per hour rather than mutating one.
        Reusing a Context would also work, but a fresh one guarantees each
        sample is independent — if the plugin ever cached a stale angle, the
        reuse version would hide it.
        """
        elevations = []
        for hour in (8, 10, 12):
            context, solar = _solar((2023, 6, 21), (hour, 0), BOULDER)
            try:
                elevations.append(solar.getSunElevation())
            finally:
                solar.__exit__(None, None, None)
                context.__exit__(None, None, None)

        # Python chains comparisons, so this reads as it looks: strictly rising.
        assert elevations[0] < elevations[1] < elevations[2], (
            f"elevation did not rise through the morning: {elevations}"
        )

    def test_sunrise_is_before_sunset(self):
        """Sunrise must precede sunset, and neither may be the 00:00 sentinel.

        getSunriseTime scans minute by minute looking for the horizon crossing.
        If it never finds one — polar winter, or a bug — it returns 00:00. That
        is indistinguishable from a real midnight answer unless you check for
        it explicitly, which is what the last two assertions do.

        Comparing (hour, minute) TUPLES works because Python compares tuples
        element by element: (7, 28) < (16, 39) because 7 < 16.
        """
        context = Context()
        context.setDate(2023, 1, 1)   # no setTime — sunrise does not need one
        solar = SolarPosition(context, **BOULDER)
        try:
            sunrise = solar.getSunriseTime()
            sunset = solar.getSunsetTime()

            assert (sunrise.hour, sunrise.minute) < (sunset.hour, sunset.minute)
            assert (sunrise.hour, sunrise.minute) != (0, 0)
            assert (sunset.hour, sunset.minute) != (0, 0)
        finally:
            solar.__exit__(None, None, None)
            context.__exit__(None, None, None)

    def test_par_and_nir_are_positive_in_daylight(self):
        """Flux must be positive during the day, and the fraction within 0..1.

        A weak test on purpose. It is a smoke check that the Gueymard model
        produced something physical at all. The reference test in section 1
        does the precise work; this one covers the flux getters that section 1
        does not touch.
        """
        context, solar = _solar(LONGWAVE_DATE, LONGWAVE_TIME, LONGWAVE)
        try:
            solar.setAtmosphericConditions(*LONGWAVE_CONDITIONS)
            assert solar.getSolarFluxPAR() > 0
            assert solar.getSolarFluxNIR() > 0
            # A fraction outside 0..1 is meaningless by definition.
            assert 0.0 <= solar.getDiffuseFraction() <= 1.0
        finally:
            solar.__exit__(None, None, None)
            context.__exit__(None, None, None)


# =============================================================================
# SECTION 3 — THE DOCUMENTED CONTRACT (currently broken)
# =============================================================================
# A "contract" test checks that the code does what the DOCUMENTATION promises.
# Both tests here fail, because the documentation is wrong. That is a finding,
# not a mistake in the test.
# =============================================================================

@pytest.mark.native_only
class TestDocumentedUnitContract:
    """SolarPosition.py promises degrees; the library returns radians.

    The evidence:

      - SolarPosition.py getSunElevation docstring:
            "Sun elevation angle in degrees (0 deg = horizon, 90 deg = zenith)"
      - pyhelios_wrapper_solarposition.cpp line 86, the comment above it:
            "// Solar angle calculations - basic angles in degrees"
      - pyhelios_wrapper_solarposition.cpp line 96, what it actually does:
            return sp->getSunElevation();      <- no conversion
      - Helios core works in radians. The C++ selfTest converts explicitly:
            sp.getSunElevation() * 180.f / M_PI

    Measured on this machine for the Boulder case:
        elevation           = 0.4039   (0.4039 rad = 23.1 deg)
        elevation + zenith  = 1.5708   (= pi/2, so radians, not 90)

    WHY THIS MATTERS FOR THE GUI: a panel that displays getSunElevation()
    directly will show "0.4" where the user expects "23.1".

    -------------------------------------------------------------------------
    WHAT xfail MEANS
    -------------------------------------------------------------------------
    @pytest.mark.xfail marks a test as "expected to fail". pytest runs it, sees
    it fail, and reports XFAIL instead of FAILED. The suite stays green while
    the bug stays on the record.

    `strict=True` is the important half. Without it, a test that starts PASSING
    is reported as XPASS and quietly ignored — so when somebody fixes the bug,
    nobody notices and the stale marker lives forever. With strict=True, an
    unexpected pass is a FAILURE, forcing whoever fixed it to come here and
    remove the marker.

    The alternative is to delete these two tests and just let the bug exist
    undocumented. Do not do that. A recorded bug is worth far more than a
    tidy file.
    """

    @pytest.mark.xfail(
        strict=True,
        reason="pyhelios_wrapper_solarposition.cpp returns radians; docstrings say degrees",
    )
    def test_elevation_is_returned_in_degrees_as_documented(self):
        """If the docstring were true, this would read ~29.5, not ~0.40."""
        context, solar = _solar(BOULDER_DATE, BOULDER_TIME, BOULDER)
        try:
            # Note: NO math.degrees() call here. That is the whole point —
            # we take the library at its documented word and see what happens.
            assert solar.getSunElevation() == pytest.approx(
                BOULDER_ELEVATION_DEG, abs=10.0)
        finally:
            solar.__exit__(None, None, None)
            context.__exit__(None, None, None)

    @pytest.mark.xfail(
        strict=True,
        reason="same radians/degrees mismatch, on the elevation+zenith sum",
    )
    def test_elevation_plus_zenith_is_ninety_degrees_as_documented(self):
        """The same bug from a second angle, independent of any reference value.

        Worth having both: this one would still catch the unit error even if
        the Boulder reference numbers were ever revised.
        """
        context, solar = _solar((2023, 6, 21), (12, 0), dict(
            utc_offset=0, latitude=0.0, longitude=0.0))
        try:
            total = solar.getSunElevation() + solar.getSunZenith()
            assert total == pytest.approx(90.0, abs=0.01)
        finally:
            solar.__exit__(None, None, None)
            context.__exit__(None, None, None)


# =============================================================================
# SECTION 4 — INPUT VALIDATION
# =============================================================================
# So far every test asked "is the right answer produced?". These ask the
# opposite: "is a WRONG INPUT refused?".
#
# A model that silently accepts nonsense is more dangerous than one that
# crashes, because the run completes and the numbers look plausible.
# =============================================================================

@pytest.mark.native_only
class TestAtmosphericValidation:
    """setAtmosphericConditions rejects some bad input. Pin down which."""

    @pytest.fixture
    def solar(self):
        """A shared, automatically cleaned-up SolarPosition.

        A FIXTURE is pytest's setup/teardown mechanism. Any test in this class
        that takes an argument named `solar` gets the object yielded below —
        pytest matches by NAME, which is why the parameter must be spelled
        exactly like the function.

        Everything before `yield` is setup, everything after is teardown, and
        the teardown runs even if the test fails. That replaces the try/finally
        blocks used earlier in this file. Both are correct; a fixture is
        cleaner once three or more tests need the same object.

        By default a fixture runs once PER TEST, so each test gets a fresh
        object and cannot be polluted by an earlier one.
        """
        context = Context()
        context.setDate(2023, 6, 21)
        context.setTime(12, 0)
        sp = SolarPosition(context, utc_offset=0, latitude=0.0, longitude=0.0)
        yield sp                              # <- the test body runs here
        sp.__exit__(None, None, None)         # <- teardown, always runs
        context.__exit__(None, None, None)

    def test_humidity_as_percentage_is_rejected(self, solar):
        """Humidity is a FRACTION. Passing 50 means 5000% and must be refused.

        This is the single most likely mistake a GUI will make, because every
        user interface in the world shows humidity as a percentage. Somebody
        will forward 50 straight from the input box.

        `with pytest.raises(ValueError):` inverts the usual logic — the test
        PASSES if the block raises ValueError, and FAILS if it completes
        normally or raises a different exception type.
        """
        with pytest.raises(ValueError):
            solar.setAtmosphericConditions(101325.0, 300.0, 50.0, 0.05)

    def test_negative_humidity_is_rejected(self, solar):
        """The other end of the same range check."""
        with pytest.raises(ValueError):
            solar.setAtmosphericConditions(101325.0, 300.0, -0.1, 0.05)

    def test_zero_pressure_is_rejected(self, solar):
        """Zero pressure means no atmosphere.

        Note this raises SolarPositionError, not ValueError — the check lives
        in the C++ layer and surfaces as the plugin's own exception type, while
        humidity is checked in Python first. Asserting the exact type documents
        WHERE each check happens, which matters when you decide what your API
        should return to the frontend.
        """
        with pytest.raises(SolarPositionError):
            solar.setAtmosphericConditions(0.0, 300.0, 0.5, 0.05)

    def test_negative_turbidity_is_rejected(self, solar):
        """Negative haze is meaningless. This is the ONLY turbidity check that
        exists — see section 5 for the one that does not."""
        with pytest.raises(ValueError):
            solar.setAtmosphericConditions(101325.0, 300.0, 0.5, -1.0)


# =============================================================================
# SECTION 5 — CHARACTERISATION TESTS
# =============================================================================
# The unusual kind, and the one most worth understanding.
#
# A characterisation test asserts what the code CURRENTLY DOES, including
# behaviour that is wrong. It is not saying "this is correct". It is saying
# "this is how it behaves today, and I want to be told if that ever changes".
#
# Two uses here:
#   1. It proves the silent failure is real, with a number. That is the
#      evidence for adding a range check to the GUI.
#   2. If Helios ever adds proper validation upstream, these tests fail, and
#      the failure message tells you to go re-examine the GUI's own checks
#      rather than leaving duplicated validation forever.
#
# Read the assertion messages below: they are written for the person who sees
# the failure in six months, not for you today.
# =============================================================================

@pytest.mark.native_only
class TestSilentlyAcceptedBadInput:
    """Record what Helios does NOT catch, so the GUI knows what it must."""

    @pytest.fixture
    def solar(self):
        context = Context()
        context.setDate(2003, 5, 5)
        context.setTime(9, 10)
        sp = SolarPosition(context, **LONGWAVE)
        yield sp
        sp.__exit__(None, None, None)
        context.__exit__(None, None, None)

    def test_pressure_in_hectopascals_is_accepted_and_wrong(self, solar):
        """1013 hPa instead of 101325 Pa: no error, and much too much PAR.

        Weather stations, forecasts and most APIs report pressure in
        hectopascals. Helios wants Pascals. The only validation is
        "pressure > 0", so 1013 sails through.

        The test measures the CORRECT value first, then the wrong one, and
        compares them. Comparing against a hard-coded number would break every
        time the model was tuned; comparing against the model's own correct
        answer is stable.

        Measured: 425 W/m2 correct, 541 W/m2 with hPa — about 27% too high.
        The threshold below is 1.2x, comfortably under 1.27 so ordinary model
        tuning will not trip it, but far above any rounding noise.
        """
        solar.setAtmosphericConditions(*LONGWAVE_CONDITIONS)
        correct_par = solar.getSolarFluxPAR()

        solar.setAtmosphericConditions(1013.0, 290.0, 0.5, 0.02)
        wrong_par = solar.getSolarFluxPAR()

        assert wrong_par > correct_par * 1.2, (
            "hPa/Pa confusion no longer inflates PAR — recheck the GUI's "
            "pressure range validation, it may now be redundant"
        )

    def test_linke_turbidity_is_accepted_and_blacks_out_the_sun(self, solar):
        """3.0 is a legal Linke turbidity but an absurd Angstrom beta.

        There are two common turbidity scales and Helios accepts only one:

            Angstrom beta   0.02 (very clear) .. 0.1 (hazy)   <- what Helios wants
            Linke turbidity 2 (clear) .. 6 (very hazy)        <- a different scale

        The numbers overlap in neither range nor meaning, but both are "small
        positive floats", so the `turbidity >= 0` check cannot tell them apart.

        Measured: 425 W/m2 with beta=0.02, and 0.86 W/m2 with 3.0. The sun
        effectively goes out — yet the run completes and reports success.
        """
        solar.setAtmosphericConditions(*LONGWAVE_CONDITIONS)
        correct_par = solar.getSolarFluxPAR()

        solar.setAtmosphericConditions(101325.0, 290.0, 0.5, 3.0)
        wrong_par = solar.getSolarFluxPAR()

        assert wrong_par < correct_par * 0.01, (
            "Linke turbidity no longer collapses PAR — recheck the GUI's "
            "turbidity range validation"
        )
