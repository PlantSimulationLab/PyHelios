import ctypes
from typing import List

from ..plugins import helios_lib
from ..exceptions import check_helios_error

# Error checking callback
def _check_error(result, func, args):
    """
    Errcheck callback that automatically checks for Helios errors after each global function call.
    This ensures that C++ exceptions are properly converted to Python exceptions.
    """
    check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage, helios_lib.clearError)
    return result

# GPU environment functions from core/global.h (helios-core v1.3.79+). These live in
# the unconditionally-compiled common wrapper, not a plugin, so they are available in
# any native build. Probed in their own try block so an older library degrades to a
# clear error here rather than disabling unrelated bindings.
_GPU_ENV_FUNCTIONS_AVAILABLE = False
try:
    helios_lib.gpuRequiredByEnvironment.argtypes = []
    helios_lib.gpuRequiredByEnvironment.restype = ctypes.c_int
    helios_lib.gpuRequiredByEnvironment.errcheck = _check_error

    helios_lib.requireGPUOrFail.argtypes = [ctypes.c_char_p]
    helios_lib.requireGPUOrFail.restype = None
    helios_lib.requireGPUOrFail.errcheck = _check_error

    _GPU_ENV_FUNCTIONS_AVAILABLE = True
except AttributeError:
    _GPU_ENV_FUNCTIONS_AVAILABLE = False


# Process-wide random number generator from core/global.h (helios-core v1.3.85+).
# Probed separately so a library built against an older core keeps the GPU
# environment functions above working.
_GLOBAL_RNG_FUNCTIONS_AVAILABLE = False
try:
    helios_lib.seedGlobalRandomGenerator.argtypes = [ctypes.c_uint]
    helios_lib.seedGlobalRandomGenerator.restype = None
    helios_lib.seedGlobalRandomGenerator.errcheck = _check_error

    helios_lib.globalRandu.argtypes = []
    helios_lib.globalRandu.restype = ctypes.c_float
    helios_lib.globalRandu.errcheck = _check_error

    helios_lib.globalRanduInt.argtypes = [ctypes.c_int, ctypes.c_int]
    helios_lib.globalRanduInt.restype = ctypes.c_int
    helios_lib.globalRanduInt.errcheck = _check_error

    _GLOBAL_RNG_FUNCTIONS_AVAILABLE = True
except AttributeError:
    _GLOBAL_RNG_FUNCTIONS_AVAILABLE = False


# Leaf angle distribution CDFs from core/global.h (helios-core v1.3.87+), probed
# separately for the same reason as the block above.
_LEAF_ANGLE_CDF_FUNCTIONS_AVAILABLE = False
try:
    for _fn in ("evaluateBetaDistributionCDF", "invertBetaDistributionCDF",
                "evaluateEllipsoidalAzimuthCDF", "invertEllipsoidalAzimuthCDF"):
        _f = getattr(helios_lib, _fn)
        _f.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float]
        _f.restype = ctypes.c_float
        _f.errcheck = _check_error
    del _fn, _f

    _LEAF_ANGLE_CDF_FUNCTIONS_AVAILABLE = True
except AttributeError:
    _LEAF_ANGLE_CDF_FUNCTIONS_AVAILABLE = False


# Blackbody radiation functions from core/global.h (helios-core v1.3.90+), probed
# separately for the same reason as the blocks above.
_BLACKBODY_FUNCTIONS_AVAILABLE = False
try:
    helios_lib.blackbodyBandFraction.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.blackbodyBandFraction.restype = ctypes.c_float
    helios_lib.blackbodyBandFraction.errcheck = _check_error

    helios_lib.blackbodySpectralRadiance.argtypes = [ctypes.c_float, ctypes.c_float]
    helios_lib.blackbodySpectralRadiance.restype = ctypes.c_float
    helios_lib.blackbodySpectralRadiance.errcheck = _check_error

    _BLACKBODY_FUNCTIONS_AVAILABLE = True
except AttributeError:
    _BLACKBODY_FUNCTIONS_AVAILABLE = False


def _require_global_rng_functions(name: str) -> None:
    if not _GLOBAL_RNG_FUNCTIONS_AVAILABLE:
        raise RuntimeError(
            f"{name} is not available in the current native library. It requires "
            "helios-core v1.3.85 or newer; rebuild with "
            "'build_scripts/build_helios --clean'."
        )


def _require_leaf_angle_cdf_functions(name: str) -> None:
    if not _LEAF_ANGLE_CDF_FUNCTIONS_AVAILABLE:
        raise RuntimeError(
            f"{name} is not available in the current native library. It requires "
            "helios-core v1.3.87 or newer; rebuild with "
            "'build_scripts/build_helios --clean'."
        )


def _require_blackbody_functions(name: str) -> None:
    if not _BLACKBODY_FUNCTIONS_AVAILABLE:
        raise RuntimeError(
            f"{name} is not available in the current native library. It requires "
            "helios-core v1.3.90 or newer; rebuild with "
            "'build_scripts/build_helios --clean'."
        )


def _require_gpu_env_functions(name: str) -> None:
    if not _GPU_ENV_FUNCTIONS_AVAILABLE:
        raise RuntimeError(
            f"{name} is not available in the current native library. It requires "
            "helios-core v1.3.79 or newer; rebuild with "
            "'build_scripts/build_helios --clean'."
        )


def gpuRequiredByEnvironment() -> bool:
    """Check whether a GPU is required by the ``HELIOS_REQUIRE_GPU`` environment variable.

    True when ``HELIOS_REQUIRE_GPU`` is set to any value other than ``"0"``. This is the
    counterpart to the ``HELIOS_NO_GPU`` veto: rather than changing what hardware probes
    report, it changes what a test does when no GPU is found, so a CI runner dedicated to
    GPU coverage cannot report success after silently skipping every GPU test.

    The environment is read on every call rather than cached, so a change made via
    ``os.environ`` is observed immediately — except on Windows, where the statically
    linked MSVC runtime gives the DLL a private copy of the environment snapshotted
    at load time, so the variable must be set before the interpreter starts. See
    ``pyhelios.Global.gpuRequiredByEnvironment`` for the full explanation.

    Returns:
        True if a usable GPU is mandatory for this process
    """
    _require_gpu_env_functions("gpuRequiredByEnvironment")
    return helios_lib.gpuRequiredByEnvironment() != 0


def requireGPUOrFail(context_message: str) -> None:
    """Raise if ``HELIOS_REQUIRE_GPU`` is set but no usable GPU was found.

    Call at the point code would otherwise skip for lack of a GPU. Does nothing unless
    ``HELIOS_REQUIRE_GPU`` is set. Setting both ``HELIOS_REQUIRE_GPU`` and
    ``HELIOS_NO_GPU`` is contradictory and is reported as such.

    This function does not itself probe for hardware: reaching it is taken as proof the
    caller already determined no GPU was usable, so when ``HELIOS_REQUIRE_GPU`` is set it
    always raises.

    Args:
        context_message: Description of what was about to be skipped, included in the
            error message

    Raises:
        HeliosError: If a GPU is required by the environment but none was found
    """
    _require_gpu_env_functions("requireGPUOrFail")
    encoded = (context_message or "").encode('utf-8')
    helios_lib.requireGPUOrFail(encoded)



def seedGlobalRandomGenerator(seed: int) -> None:
    """Seed the process-wide generator behind the free function ``helios::randu()``.

    Distinct from ``Context.seedRandomGenerator()``, which seeds a per-Context
    generator. See ``pyhelios.Global.seedRandomGenerator`` for which native code
    draws from which.
    """
    _require_global_rng_functions("seedGlobalRandomGenerator")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError(f"seed must be an int, got {type(seed).__name__}")
    if seed < 0 or seed > 0xFFFFFFFF:
        raise ValueError(f"seed must fit in an unsigned 32-bit integer, got {seed}")
    helios_lib.seedGlobalRandomGenerator(ctypes.c_uint(seed))


def globalRandu() -> float:
    """Draw a uniform float in [0, 1) from the process-wide generator."""
    _require_global_rng_functions("globalRandu")
    return float(helios_lib.globalRandu())


def globalRanduInt(imin: int, imax: int) -> int:
    """Draw a uniform integer over the inclusive range [imin, imax] from the process-wide generator."""
    _require_global_rng_functions("globalRanduInt")
    for name, v in (("imin", imin), ("imax", imax)):
        if not isinstance(v, int) or isinstance(v, bool):
            raise ValueError(f"{name} must be an int, got {type(v).__name__}")
    return int(helios_lib.globalRanduInt(ctypes.c_int(imin), ctypes.c_int(imax)))


def evaluateBetaDistributionCDF(theta: float, mu: float, nu: float) -> float:
    """Cumulative probability of a Beta-distributed leaf inclination at or below ``theta``."""
    _require_leaf_angle_cdf_functions("evaluateBetaDistributionCDF")
    return float(helios_lib.evaluateBetaDistributionCDF(
        ctypes.c_float(theta), ctypes.c_float(mu), ctypes.c_float(nu)))


def invertBetaDistributionCDF(probability: float, mu: float, nu: float) -> float:
    """Leaf inclination (radians) at a given cumulative probability of the Beta distribution."""
    _require_leaf_angle_cdf_functions("invertBetaDistributionCDF")
    return float(helios_lib.invertBetaDistributionCDF(
        ctypes.c_float(probability), ctypes.c_float(mu), ctypes.c_float(nu)))


def evaluateEllipsoidalAzimuthCDF(phi: float, e: float, phi0_degrees: float) -> float:
    """Cumulative probability of an ellipsoidally distributed leaf azimuth at or below ``phi``."""
    _require_leaf_angle_cdf_functions("evaluateEllipsoidalAzimuthCDF")
    return float(helios_lib.evaluateEllipsoidalAzimuthCDF(
        ctypes.c_float(phi), ctypes.c_float(e), ctypes.c_float(phi0_degrees)))


def invertEllipsoidalAzimuthCDF(probability: float, e: float, phi0_degrees: float) -> float:
    """Leaf azimuth (radians) at a given cumulative probability of the ellipsoidal distribution."""
    _require_leaf_angle_cdf_functions("invertEllipsoidalAzimuthCDF")
    return float(helios_lib.invertEllipsoidalAzimuthCDF(
        ctypes.c_float(probability), ctypes.c_float(e), ctypes.c_float(phi0_degrees)))


def _require_real_number(name: str, value) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number, got {type(value).__name__}")


def blackbodyBandFraction(wavelength_min_nm: float, wavelength_max_nm: float, temperature_K: float) -> float:
    """Fraction of blackbody emissive power emitted between two wavelengths."""
    _require_blackbody_functions("blackbodyBandFraction")
    for name, v in (("wavelength_min_nm", wavelength_min_nm), ("wavelength_max_nm", wavelength_max_nm),
                    ("temperature_K", temperature_K)):
        _require_real_number(name, v)
    return float(helios_lib.blackbodyBandFraction(
        ctypes.c_float(wavelength_min_nm), ctypes.c_float(wavelength_max_nm), ctypes.c_float(temperature_K)))


def blackbodySpectralRadiance(wavelength_nm: float, temperature_K: float) -> float:
    """Spectral radiance of a blackbody (W/m^2/sr/nm)."""
    _require_blackbody_functions("blackbodySpectralRadiance")
    for name, v in (("wavelength_nm", wavelength_nm), ("temperature_K", temperature_K)):
        _require_real_number(name, v)
    return float(helios_lib.blackbodySpectralRadiance(ctypes.c_float(wavelength_nm), ctypes.c_float(temperature_K)))


# Single-channel PNG images from core/global.h (helios-core v1.3.95+), probed
# separately for the same reason as the blocks above.
_PNG_SINGLE_CHANNEL_FUNCTIONS_AVAILABLE = False
try:
    helios_lib.readPNGSingleChannel.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint),
                                                ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.readPNGSingleChannel.restype = ctypes.POINTER(ctypes.c_ushort)
    helios_lib.readPNGSingleChannel.errcheck = _check_error

    helios_lib.writePNGSingleChannel.argtypes = [ctypes.c_char_p, ctypes.c_uint, ctypes.c_uint,
                                                 ctypes.POINTER(ctypes.c_ushort), ctypes.c_uint, ctypes.c_uint]
    helios_lib.writePNGSingleChannel.restype = None
    helios_lib.writePNGSingleChannel.errcheck = _check_error

    _PNG_SINGLE_CHANNEL_FUNCTIONS_AVAILABLE = True
except AttributeError:
    _PNG_SINGLE_CHANNEL_FUNCTIONS_AVAILABLE = False


def _require_png_single_channel_functions(name: str) -> None:
    if not _PNG_SINGLE_CHANNEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError(
            f"{name} is not available in the current native library. It requires "
            "helios-core v1.3.95 or newer; rebuild with "
            "'build_scripts/build_helios --clean'."
        )


def readPNGSingleChannel(filename: str):
    """Read a grayscale PNG as integers. Returns (values, width, height), values a uint16 ndarray of shape (height, width)."""
    import numpy as np
    _require_png_single_channel_functions("readPNGSingleChannel")
    width = ctypes.c_uint()
    height = ctypes.c_uint()
    size = ctypes.c_uint()
    ptr = helios_lib.readPNGSingleChannel(filename.encode('utf-8'), ctypes.byref(width), ctypes.byref(height),
                                          ctypes.byref(size))
    w, h, n = width.value, height.value, size.value
    if n != w * h:
        raise RuntimeError(f"readPNGSingleChannel returned {n} values for a {w} x {h} image '{filename}'.")
    if n == 0 or not ptr:
        return np.zeros((h, w), dtype=np.uint16), w, h
    values = np.ctypeslib.as_array(ptr, shape=(n,)).astype(np.uint16, copy=True).reshape(h, w)
    return values, w, h


def writePNGSingleChannel(filename: str, width: int, height: int, pixel_values, bit_depth: int) -> None:
    """Write a grayscale PNG of integer values. ``pixel_values`` is a flat uint16 ndarray of width*height values."""
    import numpy as np
    _require_png_single_channel_functions("writePNGSingleChannel")
    arr = np.ascontiguousarray(pixel_values, dtype=np.uint16).ravel()
    helios_lib.writePNGSingleChannel(filename.encode('utf-8'), ctypes.c_uint(width), ctypes.c_uint(height),
                                     arr.ctypes.data_as(ctypes.POINTER(ctypes.c_ushort)), ctypes.c_uint(arr.size),
                                     ctypes.c_uint(bit_depth))


# Class map area fractions from core/global.h (helios-core v1.3.96+), probed
# separately for the same reason as the blocks above.
_CLASS_MAP_AREA_FUNCTIONS_AVAILABLE = False
try:
    helios_lib.classMapAreaFractions.argtypes = [
        ctypes.POINTER(ctypes.c_ushort), ctypes.c_uint, ctypes.c_int, ctypes.c_int,
        ctypes.POINTER(ctypes.c_float), ctypes.c_uint,
        ctypes.POINTER(ctypes.POINTER(ctypes.c_ushort)), ctypes.POINTER(ctypes.POINTER(ctypes.c_float)),
    ]
    helios_lib.classMapAreaFractions.restype = ctypes.c_uint
    helios_lib.classMapAreaFractions.errcheck = _check_error

    _CLASS_MAP_AREA_FUNCTIONS_AVAILABLE = True
except AttributeError:
    _CLASS_MAP_AREA_FUNCTIONS_AVAILABLE = False


def classMapAreaFractions(classes, width: int, height: int, uv) -> List[tuple]:
    """Area fraction of a (u,v) polygon in each class of a class map.

    ``classes`` is a flat uint16 ndarray of ``width * height`` values; ``uv`` a float32 ndarray of
    shape ``(N, 2)``. Returns ``[(class, fraction), ...]`` in increasing order of class.
    """
    import numpy as np
    if not _CLASS_MAP_AREA_FUNCTIONS_AVAILABLE:
        raise RuntimeError(
            "classMapAreaFractions is not available in the current native library. It requires "
            "helios-core v1.3.96 or newer; rebuild with 'build_scripts/build_helios --clean'."
        )
    cls = np.ascontiguousarray(classes, dtype=np.uint16).ravel()
    uv_arr = np.ascontiguousarray(uv, dtype=np.float32).reshape(-1, 2)
    out_classes = ctypes.POINTER(ctypes.c_ushort)()
    out_fractions = ctypes.POINTER(ctypes.c_float)()
    n = helios_lib.classMapAreaFractions(
        cls.ctypes.data_as(ctypes.POINTER(ctypes.c_ushort)), ctypes.c_uint(cls.size),
        ctypes.c_int(width), ctypes.c_int(height),
        uv_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_float)), ctypes.c_uint(uv_arr.shape[0]),
        ctypes.byref(out_classes), ctypes.byref(out_fractions))
    if n == 0 or not out_classes or not out_fractions:
        return []
    return [(int(out_classes[i]), float(out_fractions[i])) for i in range(n)]
