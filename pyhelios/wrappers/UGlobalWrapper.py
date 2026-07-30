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


# TODO: Implement global functions for build plugin root directory management
# The Global.py module expects setBuildPluginRootDirectory and getBuildPluginRootDirectory
# functions, but these are not currently implemented in the C++ interface.
#
# Once the C++ functions are implemented, add them here with proper error checking:
#
# try:
#     helios_lib.setBuildPluginRootDirectory.argtypes = [ctypes.c_char_p]
#     helios_lib.setBuildPluginRootDirectory.restype = None
#     helios_lib.setBuildPluginRootDirectory.errcheck = _check_error
#
#     helios_lib.getBuildPluginRootDirectory.argtypes = []
#     helios_lib.getBuildPluginRootDirectory.restype = ctypes.c_char_p
#     helios_lib.getBuildPluginRootDirectory.errcheck = _check_error
#
#     _GLOBAL_FUNCTIONS_AVAILABLE = True
# except AttributeError:
#     _GLOBAL_FUNCTIONS_AVAILABLE = False
#
# def setBuildPluginRootDirectory(directory: str):
#     if not _GLOBAL_FUNCTIONS_AVAILABLE:
#         raise NotImplementedError("Global functions not available in current Helios library.")
#     directory_bytes = directory.encode('utf-8')
#     helios_lib.setBuildPluginRootDirectory(directory_bytes)
#
# def getBuildPluginRootDirectory() -> str:
#     if not _GLOBAL_FUNCTIONS_AVAILABLE:
#         raise NotImplementedError("Global functions not available in current Helios library.")
#     result = helios_lib.getBuildPluginRootDirectory()
#     return result.decode('utf-8') if result else ""
