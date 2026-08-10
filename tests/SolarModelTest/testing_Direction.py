"""
MANUAL TEST — Sun direction methods of the SolarPosition plugin.

===============================================================================
WHAT THIS DOES
===============================================================================

You type the same inputs the Solar Position panel collects:

        Latitude, Longitude, UTC offset, Date, Time

It then calls EVERY SolarPosition method that answers "where is the sun", prints
what each one returned, and says whether that method looks correct:

        getSunElevation()            getSunDirectionVector()
        getSunZenith()               getSunDirectionSpherical()
        getSunAzimuth()              getSunriseTime()
                                     getSunsetTime()

So one run tells you which methods work and which do not.

Flux methods (PAR, NIR, diffuse fraction, longwave) are NOT here — they need
atmosphere inputs as well, so they belong in their own file.

===============================================================================
HOW TO RUN
===============================================================================

    cd helios_gui\\backend-api\\pyhelios
    ..\\Env\\Scripts\\Activate.ps1
    $env:PYHELIOS_USE_PIP = "0"
    python tests\\SolarModelTest\\testing_Direction.py

The filename starts with "testing_" and not "test_" on purpose: pytest only
collects test_*.py, so this script full of input() prompts will never hang an
automated run.

===============================================================================
THE INPUTS — WHAT TO TYPE
===============================================================================

  LATITUDE     -90..+90,  POSITIVE = NORTH.  Same as Google Maps.

  LONGITUDE    -180..+180, POSITIVE = WEST.  BACKWARDS from Google Maps.
               Google Maps says Davis CA is -121.74. Helios wants +121.74.
               Google Maps says New Delhi is +77.21. Helios wants -77.21.

  UTC OFFSET   -14..+14,  POSITIVE = WEST.   ALSO BACKWARDS.
               California is UTC-8, so type +8.
               India is UTC+5:30, so type -5.5. Fractions are allowed.

  DATE / TIME  Local clock time at the site. The plugin converts internally.

===============================================================================
CASES WORTH TRYING
===============================================================================

  Boulder reference   lat 40.125  lon 105.2369  utc 7   2000-01-01  10:30
      The check below compares against 29.49 deg elevation and 154.18 deg
      azimuth, which come from Helios's own C++ test suite. If this one passes,
      the whole chain is sound.

  Night               any site, time 00:30
      Elevation must be NEGATIVE. If it is positive a sign convention is wrong.

  Wrong longitude     Davis with lon -121.74 instead of +121.74
      Watch the azimuth move by roughly 30 degrees. Nothing warns you. This is
      what your users will do if they paste from Google Maps.

  Overhead sun        lat 0  lon 0  utc 0  2023-03-21  12:00
      Equator at equinox noon: elevation should be close to 90.

  Polar winter        lat 78.2  lon -15.6  utc -1  2023-12-21  12:00
      Sun never rises, so elevation stays negative all day.
"""

import math
import os
import sys

# Let `import pyhelios` work no matter which folder you run this from.
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")))

# Stop PyHelios rebuilding the native C++ library on import.
os.environ.setdefault("PYHELIOS_USE_PIP", "0")

from pyhelios import Context, SolarPosition  # noqa: E402


# Reference answer from plugins/solarposition/tests/selfTest.cpp.
# Only used when you enter this exact case, so the script can tell you whether
# the numbers match an independently verified result.
BOULDER_REF = {
    "latitude": 40.1250, "longitude": 105.2369, "utc_offset": 7.0,
    "date": (2000, 1, 1), "time": (10, 30),
    "elevation_deg": 29.49, "azimuth_deg": 154.18,
}


# ===========================================================================
# INPUT
# ===========================================================================

def ask(prompt, default, low, high, whole=False):
    """Ask for a number in [low, high]; Enter accepts the default.

    Re-prompts instead of crashing, which is also a small demo of the range
    checking your GUI has to do — Helios does not validate these itself.
    """
    while True:
        raw = input(f"    {prompt} [{default}]: ").strip()
        if raw == "":
            return int(default) if whole else float(default)
        try:
            value = int(raw) if whole else float(raw)
        except ValueError:
            print(f"      '{raw}' is not a number.")
            continue
        if not (low <= value <= high):
            print(f"      Must be between {low} and {high}.")
            continue
        return value


def collect_inputs():
    """Collect exactly the fields the Solar Position panel collects."""
    print("\n  SITE       (longitude and UTC offset are POSITIVE-WEST)")
    latitude = ask("Latitude    -90..90,  + = north", 38.5449, -90, 90)
    longitude = ask("Longitude  -180..180, + = WEST ", 121.7405, -180, 180)
    utc_offset = ask("UTC offset  -14..14,  + = WEST ", 7, -14, 14)

    print("\n  DATE AND TIME   (local clock time at the site)")
    year = ask("Year ", 2026, 1900, 2100, whole=True)
    month = ask("Month  1-12", 6, 1, 12, whole=True)
    day = ask("Day    1-31", 20, 1, 31, whole=True)
    hour = ask("Hour   0-23", 13, 0, 23, whole=True)
    minute = ask("Minute 0-59", 0, 0, 59, whole=True)

    return {
        "latitude": latitude, "longitude": longitude, "utc_offset": utc_offset,
        "date": (year, month, day), "time": (hour, minute),
    }


# ===========================================================================
# CALLING THE METHODS
# ===========================================================================

def run_methods(inp):
    """Call every direction method and record what each returned.

    Each method is wrapped in its own try/except. If one raises, the others
    still run — that is the point of a method-by-method test. A single
    try around the whole block would hide every method after the first failure.

    Returns a list of (method_name, ok, display_value, raw_value).
    """
    context = Context()
    context.setDate(*inp["date"])
    context.setTime(*inp["time"])
    solar = SolarPosition(
        context,
        utc_offset=inp["utc_offset"],
        latitude=inp["latitude"],
        longitude=inp["longitude"],
    )

    rows = []
    raw = {}

    def call(name, fn, fmt):
        """Run one method, catch its own failure, format its result."""
        try:
            value = fn()
        except Exception as exc:
            rows.append((name, False, f"RAISED {type(exc).__name__}: {exc}", None))
            return None
        rows.append((name, True, fmt(value), value))
        raw[name] = value
        return value

    try:
        # NOTE these return RADIANS even though SolarPosition.py documents
        # degrees. See TestDocumentedUnitContract in
        # tests/test_solarposition_values.py for the proof. We convert for
        # display so the numbers are the ones a person expects.
        call("getSunElevation", solar.getSunElevation,
             lambda v: f"{math.degrees(v):8.3f} deg   ({v:.5f} rad)")
        call("getSunZenith", solar.getSunZenith,
             lambda v: f"{math.degrees(v):8.3f} deg   ({v:.5f} rad)")
        call("getSunAzimuth", solar.getSunAzimuth,
             lambda v: f"{math.degrees(v):8.3f} deg   ({v:.5f} rad)")
        call("getSunDirectionVector", solar.getSunDirectionVector,
             lambda v: f"x={v.x:+.5f}  y={v.y:+.5f}  z={v.z:+.5f}")
        call("getSunDirectionSpherical", solar.getSunDirectionSpherical,
             lambda v: f"radius={v.radius:.5f}  elevation={v.elevation:.5f}  "
                       f"azimuth={v.azimuth:.5f}")
        call("getSunriseTime", solar.getSunriseTime,
             lambda t: f"{t.hour:02d}:{t.minute:02d}")
        call("getSunsetTime", solar.getSunsetTime,
             lambda t: f"{t.hour:02d}:{t.minute:02d}")
    finally:
        # Native C++ objects must be released or the process leaks and can
        # crash later in a long session.
        solar.__exit__(None, None, None)
        context.__exit__(None, None, None)

    return rows, raw


# ===========================================================================
# CHECKING THE RESULTS
# ===========================================================================

def check_results(inp, raw):
    """Decide whether the returned values are actually CORRECT.

    Running without an exception only proves a method did not crash. These
    checks prove the numbers mean something. Each one has a twin assertion in
    tests/test_solarposition_values.py — seeing them pass by hand first is what
    makes the automated versions make sense.
    """
    checks = []

    elevation = raw.get("getSunElevation")
    zenith = raw.get("getSunZenith")
    azimuth = raw.get("getSunAzimuth")
    vector = raw.get("getSunDirectionVector")
    sunrise = raw.get("getSunriseTime")
    sunset = raw.get("getSunsetTime")

    # 1. Elevation and zenith describe the same direction from opposite ends,
    #    so together they must make a right angle. Always true.
    if elevation is not None and zenith is not None:
        total = math.degrees(elevation + zenith)
        checks.append((abs(total - 90.0) < 0.01,
                       f"elevation + zenith = {total:.3f} deg   (must be 90)"))

    # 2. A direction carries no magnitude, so the vector length must be 1.
    if vector is not None:
        length = math.sqrt(vector.x ** 2 + vector.y ** 2 + vector.z ** 2)
        checks.append((abs(length - 1.0) < 1e-4,
                       f"direction vector length = {length:.6f}   (must be 1)"))

    # 3. Helios exposes the sun position twice — as angles and as a vector.
    #    They must agree, or one code path has drifted from the other.
    if vector is not None and elevation is not None:
        expected_z = math.sin(elevation)
        checks.append((abs(vector.z - expected_z) < 1e-5,
                       f"vector.z = {vector.z:.6f} vs sin(elevation) = "
                       f"{expected_z:.6f}   (must match)"))

    # 4. Azimuth is a compass bearing, so it belongs in 0..360 degrees.
    if azimuth is not None:
        azimuth_deg = math.degrees(azimuth)
        checks.append((-0.01 <= azimuth_deg <= 360.01,
                       f"azimuth = {azimuth_deg:.3f} deg   (must be 0..360)"))

    # 5. Night hours must put the sun below the horizon. This is the cheap
    #    guard against a flipped longitude or UTC offset sign.
    hour = inp["time"][0]
    if elevation is not None and (hour <= 3 or hour >= 22):
        checks.append((elevation < 0,
                       f"time is {hour:02d}:xx, so elevation must be NEGATIVE"))

    # 6. Sunrise must precede sunset, and 00:00 is the "never found" sentinel
    #    rather than a real answer.
    if sunrise is not None and sunset is not None:
        rise = (sunrise.hour, sunrise.minute)
        set_ = (sunset.hour, sunset.minute)
        checks.append((rise < set_,
                       f"sunrise {rise[0]:02d}:{rise[1]:02d} before "
                       f"sunset {set_[0]:02d}:{set_[1]:02d}"))
        checks.append((rise != (0, 0) and set_ != (0, 0),
                       "neither time is the 00:00 'not computed' sentinel"))

    # 7. If you entered the Boulder reference case, compare against the
    #    independently verified answer from the C++ test suite.
    same_site = (
        abs(inp["latitude"] - BOULDER_REF["latitude"]) < 0.01 and
        abs(inp["longitude"] - BOULDER_REF["longitude"]) < 0.01 and
        abs(inp["utc_offset"] - BOULDER_REF["utc_offset"]) < 0.01 and
        inp["date"] == BOULDER_REF["date"] and inp["time"] == BOULDER_REF["time"]
    )
    if same_site and elevation is not None and azimuth is not None:
        d_elev = abs(math.degrees(elevation) - BOULDER_REF["elevation_deg"])
        d_azim = abs(math.degrees(azimuth) - BOULDER_REF["azimuth_deg"])
        checks.append((d_elev <= 10.0,
                       f"BOULDER REFERENCE: elevation off by {d_elev:.2f} deg "
                       f"from selfTest.cpp's {BOULDER_REF['elevation_deg']}  "
                       f"(allowed 10)"))
        checks.append((d_azim <= 5.0,
                       f"BOULDER REFERENCE: azimuth off by {d_azim:.2f} deg "
                       f"from selfTest.cpp's {BOULDER_REF['azimuth_deg']}  "
                       f"(allowed 5)"))

    return checks


# ===========================================================================
# DISPLAY
# ===========================================================================

def show(inp, rows, checks, raw):
    year, month, day = inp["date"]
    hour, minute = inp["time"]
    lon_dir = "W" if inp["longitude"] >= 0 else "E"
    utc_sign = "-" if inp["utc_offset"] >= 0 else "+"

    print("\n" + "=" * 72)
    print("  INPUTS YOU ENTERED")
    print("=" * 72)
    print(f"    Latitude     {inp['latitude']:>11.4f}    "
          f"{abs(inp['latitude']):.4f} {'N' if inp['latitude'] >= 0 else 'S'}")
    print(f"    Longitude    {inp['longitude']:>11.4f}    "
          f"{abs(inp['longitude']):.4f} {lon_dir}")
    print(f"    UTC offset   {inp['utc_offset']:>11}    "
          f"UTC{utc_sign}{abs(inp['utc_offset'])}")
    print(f"    Date         {year:04d}-{month:02d}-{day:02d}")
    print(f"    Time         {hour:02d}:{minute:02d}  local")

    print("\n" + "=" * 72)
    print("  WHAT EACH METHOD RETURNED")
    print("=" * 72)
    for name, ok, display, _ in rows:
        status = "ok  " if ok else "FAIL"
        print(f"    [{status}] {name:26s} {display}")

    print("\n" + "=" * 72)
    print("  ARE THOSE VALUES CORRECT?")
    print("=" * 72)
    for ok, text in checks:
        print(f"    [{'PASS' if ok else 'FAIL'}]  {text}")

    # Plain-language reading so the numbers mean something at a glance.
    elevation = raw.get("getSunElevation")
    azimuth = raw.get("getSunAzimuth")
    if elevation is not None:
        elevation_deg = math.degrees(elevation)
        print("\n  IN PLAIN WORDS")
        if elevation_deg < 0:
            print(f"    Sun is BELOW the horizon by {abs(elevation_deg):.1f} deg "
                  "- night, or polar winter.")
        else:
            compass = "?"
            if azimuth is not None:
                compass = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][
                    int((math.degrees(azimuth) % 360) / 45 + 0.5) % 8]
            print(f"    Sun is UP, {elevation_deg:.1f} deg above the horizon, "
                  f"toward the {compass}.")

    failed = [t for ok, t in checks if not ok] + \
             [n for n, ok, _, _ in rows if not ok]
    print("\n" + "-" * 72)
    if failed:
        print(f"  RESULT: {len(failed)} problem(s). The methods are NOT all correct "
              "for this input.")
    else:
        print("  RESULT: every method ran and every check passed.")
    print("-" * 72)


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    print("\n" + "=" * 72)
    print("  SOLAR POSITION - DIRECTION METHOD TEST")
    print("=" * 72)
    print("\n  Enter the site and time. Press Enter to accept each [default].")
    print("  Read the top of this file for cases worth trying.")

    while True:
        inp = collect_inputs()
        try:
            rows, raw = run_methods(inp)
        except Exception as exc:
            # Construction itself failed, so no method ever ran.
            print(f"\n  COULD NOT CREATE SolarPosition: {type(exc).__name__}: {exc}")
        else:
            checks = check_results(inp, raw)
            show(inp, rows, checks, raw)

        again = input("\n  Test another? (y/n) [y]: ").strip().lower()
        if again in ("n", "no", "q", "quit"):
            print("\n  Done.\n")
            return


if __name__ == "__main__":
    # Runs only when executed directly, so an accidental import cannot hang on
    # an input() prompt.
    main()
