/**
 * @file pyhelios_wrapper_common.h
 * @brief Common definitions and error handling for PyHelios C wrapper
 * 
 * This header provides common definitions, platform macros, error codes,
 * and error handling functions shared across all PyHelios wrapper modules.
 */

#ifndef PYHELIOS_WRAPPER_COMMON_H
#define PYHELIOS_WRAPPER_COMMON_H

// Windows DLL export/import declarations
#ifdef _WIN32
    #ifdef BUILDING_PYHELIOS_DLL
        #define PYHELIOS_API __declspec(dllexport)
    #else
        #define PYHELIOS_API __declspec(dllimport)
    #endif
#else
    #define PYHELIOS_API
#endif

#include <stddef.h>  // For size_t

#ifdef __cplusplus
#include <string>    // For std::string in setError function
#endif

// Error code enumeration for robust error handling
typedef enum {
    PYHELIOS_SUCCESS = 0,                         // No error
    PYHELIOS_ERROR_INVALID_PARAMETER = 1,         // Invalid parameter passed
    PYHELIOS_ERROR_UUID_NOT_FOUND = 2,            // UUID not found in context
    PYHELIOS_ERROR_FILE_IO = 3,                   // File I/O error
    PYHELIOS_ERROR_MEMORY_ALLOCATION = 4,         // Memory allocation failure
    PYHELIOS_ERROR_GPU_INITIALIZATION = 5,       // GPU initialization failed
    PYHELIOS_ERROR_PLUGIN_NOT_AVAILABLE = 6,     // Plugin not available
    PYHELIOS_ERROR_RUNTIME = 7,                  // Runtime error (general)
    PYHELIOS_ERROR_UNKNOWN = 99                  // Unknown error
} PyHeliosErrorCode;

#ifdef __cplusplus
extern "C" {
#endif

//=============================================================================
// Error Handling Functions
//=============================================================================

/**
 * @brief Get the last error code
 * @return Error code (0 = success, 1-99 = specific error types)
 */
PYHELIOS_API int getLastErrorCode();

/**
 * @brief Get the last error message
 * @return Pointer to error message string (null-terminated)
 */
PYHELIOS_API const char* getLastErrorMessage();

/**
 * @brief Clear the current error state
 */
PYHELIOS_API void clearError();

//=============================================================================
// GPU Environment Functions (core/global.h; helios-core v1.3.79+)
//=============================================================================

/**
 * @brief Check whether a GPU is required by the HELIOS_REQUIRE_GPU environment variable
 *
 * Returns 1 when HELIOS_REQUIRE_GPU is set to any value other than "0". This is the
 * counterpart to the HELIOS_NO_GPU veto: rather than changing what hardware probes
 * report, it changes what a test does when no GPU is found -- tests that would
 * normally skip must instead fail, so a runner dedicated to GPU coverage cannot
 * report success after silently skipping every GPU test.
 *
 * The environment is read on every call rather than cached, so a process can observe
 * a change made with setenv()/os.environ.
 *
 * @return 1 if a usable GPU is mandatory for this process, 0 otherwise
 */
PYHELIOS_API int gpuRequiredByEnvironment();

/**
 * @brief Fail if HELIOS_REQUIRE_GPU is set but no usable GPU was found
 *
 * Call at the point a test would otherwise skip for lack of a GPU. Does nothing
 * unless HELIOS_REQUIRE_GPU is set. Setting both HELIOS_REQUIRE_GPU and
 * HELIOS_NO_GPU is contradictory and is reported as an error rather than letting
 * one silently win.
 *
 * Note that this function does not itself probe for hardware: reaching it is taken
 * as proof that the caller already determined no GPU was usable. When
 * HELIOS_REQUIRE_GPU is set it therefore always reports an error.
 *
 * @param context_message Description of what was about to be skipped, included in
 *                        the error message. NULL is treated as an empty description.
 */
PYHELIOS_API void requireGPUOrFail(const char* context_message);

//=============================================================================
// Internal Helper Functions (for use by other wrapper modules)
//=============================================================================

#ifdef __cplusplus
/**
 * @brief Internal helper function to set error state
 * @param error_code Error code from PyHeliosErrorCode enum
 * @param message Error message string
 */
void setError(int error_code, const std::string& message);
}
#endif

#endif // PYHELIOS_WRAPPER_COMMON_H