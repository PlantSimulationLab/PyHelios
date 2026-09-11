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


def _require_global_rng_functions(name: str) -> None:
    if not _GLOBAL_RNG_FUNCTIONS_AVAILABLE:
        raise RuntimeError(
            f"{name} is not available in the current native library. It requires "
            "helios-core v1.3.85 or newer; rebuild with "
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
