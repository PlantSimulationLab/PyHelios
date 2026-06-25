import ctypes
from typing import List

from ..plugins import helios_lib
from ..exceptions import check_helios_error

# Error checking callback
def _check_error(result, func, args):
    """
    Errcheck callback that automatically checks for Helios errors after each logger function call.
    This ensures that C++ exceptions are properly converted to Python exceptions.
    """
    check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage, helios_lib.clearError)
    return result

# Check if logger functions are available (they may not be in all builds)
_has_logger = hasattr(helios_lib, 'createLogger')

if _has_logger:
    helios_lib.createLogger.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.createLogger.restype = None
    helios_lib.createLogger.errcheck = _check_error

    helios_lib.destroyLogger.argtypes = []
    helios_lib.destroyLogger.restype = None
    # Note: destroyLogger doesn't need errcheck as it typically doesn't fail

    helios_lib.writeLog.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.writeLog.restype = None
    helios_lib.writeLog.errcheck = _check_error

def createLogger(logFileName: str, logFileLocation: str) -> None:
    if _has_logger:
        logFileName_bytes = logFileName.encode("utf-8")
        logFileLocation_bytes = logFileLocation.encode("utf-8")
        helios_lib.createLogger(logFileName_bytes, logFileLocation_bytes)
    else:
        print(f"Warning: Logger not available in this build. Would create logger: {logFileName} at {logFileLocation}")

def destroyLogger() -> None:
    if _has_logger:
        helios_lib.destroyLogger()
    else:
        print("Warning: Logger not available in this build. Would destroy logger.")

def writeLog(label: str, message: str) -> None:
    if _has_logger:
        label_bytes = label.encode("utf-8")
        message_bytes = message.encode("utf-8")
        helios_lib.writeLog(label_bytes, message_bytes)
    else:
        print(f"Log [{label}]: {message}")