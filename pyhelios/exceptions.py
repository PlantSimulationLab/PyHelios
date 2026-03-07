"""
Exception classes for PyHelios library.

This module provides a hierarchy of exceptions that map to various error conditions
in the Helios C++ core and PyHelios wrapper layer.
"""


class HeliosError(Exception):
    """Base exception class for all PyHelios-related errors."""
    pass


class HeliosRuntimeError(HeliosError):
    """
    Runtime errors from Helios operations.
    
    Raised when the Helios core encounters a runtime error condition,
    such as invalid geometry parameters or numerical precision issues.
    """
    pass


class HeliosInvalidArgumentError(HeliosError):
    """
    Invalid argument errors.
    
    Raised when function parameters are invalid, such as null pointers,
    out-of-range values, or incompatible data types.
    """
    pass


class HeliosUUIDNotFoundError(HeliosError):
    """
    UUID not found errors.
    
    Raised when attempting to access a primitive or object that doesn't
    exist in the Context using an invalid UUID.
    """
    pass


class HeliosFileIOError(HeliosError):
    """
    File I/O related errors.
    
    Raised when file operations fail, such as loading PLY files,
    reading textures, or accessing plugin data files.
    """
    pass


class HeliosMemoryAllocationError(HeliosError):
    """
    Memory allocation errors.
    
    Raised when memory allocation fails, typically during large
    geometry operations or texture loading.
    """
    pass


class HeliosGPUInitializationError(HeliosError):
    """
    GPU initialization errors.
    
    Raised when GPU-related operations fail, such as Vulkan/OptiX backend
    initialization for radiation modeling or GPU setup.
    """
    pass


class HeliosPluginNotAvailableError(HeliosError):
    """
    Plugin not available errors.
    
    Raised when attempting to use a plugin that is not compiled or
    available in the current PyHelios installation.
    """
    pass


class HeliosUnknownError(HeliosError):
    """
    Unknown errors.
    
    Raised when an unexpected C++ exception occurs that doesn't
    map to a specific error category.
    """
    pass


# Error code to exception mapping
ERROR_CODE_TO_EXCEPTION = {
    1: HeliosInvalidArgumentError,       # PYHELIOS_ERROR_INVALID_PARAMETER
    2: HeliosUUIDNotFoundError,          # PYHELIOS_ERROR_UUID_NOT_FOUND
    3: HeliosFileIOError,                # PYHELIOS_ERROR_FILE_IO
    4: HeliosMemoryAllocationError,      # PYHELIOS_ERROR_MEMORY_ALLOCATION
    5: HeliosGPUInitializationError,     # PYHELIOS_ERROR_GPU_INITIALIZATION
    6: HeliosPluginNotAvailableError,    # PYHELIOS_ERROR_PLUGIN_NOT_AVAILABLE
    7: HeliosRuntimeError,               # PYHELIOS_ERROR_RUNTIME
    99: HeliosUnknownError,              # PYHELIOS_ERROR_UNKNOWN
}


def create_exception_from_error_code(error_code, error_message):
    """
    Create an appropriate exception instance from an error code and message.
    
    Args:
        error_code (int): Error code from the C++ wrapper
        error_message (str): Error message from the C++ wrapper
        
    Returns:
        HeliosError: Appropriate exception instance
    """
    exception_class = ERROR_CODE_TO_EXCEPTION.get(error_code, HeliosUnknownError)
    return exception_class(f"Helios error {error_code}: {error_message}")


def check_helios_error(get_error_func, get_message_func):
    """
    Check for Helios errors and raise appropriate Python exceptions.
    
    This function is designed to be used as an errcheck callback for ctypes
    function calls.
    
    Args:
        get_error_func: Function to get the last error code
        get_message_func: Function to get the last error message
        
    Raises:
        HeliosError: If an error is detected
    """
    error_code = get_error_func()
    if error_code != 0:  # 0 is PYHELIOS_SUCCESS
        error_message = get_message_func().decode('utf-8') if get_message_func() else "Unknown error"
        raise create_exception_from_error_code(error_code, error_message)