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
