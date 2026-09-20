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
// Global Random Number Generator (helios-core v1.3.85+)
//=============================================================================

/**
 * @brief Seed the generator behind the free function helios::randu()
 *
 * This is the process-wide generator used by plug-in code that draws random
 * numbers outside a Context (LiDAR leaf-group and triangle index draws, grape
 * berry placement in PlantArchitecture, ...). It is distinct from the per-Context
 * generator seeded by seedRandomGenerator(helios::Context*, unsigned int). By
 * default it is seeded from std::random_device, so each run differs; seeding it
 * makes a run reproducible.
 *
 * The generator is shared by all threads and access to it is synchronized, so a
 * seed set from any thread applies to every subsequent draw. Seeding fixes the
 * sequence of values drawn, not which thread draws which value, so it does not
 * by itself make a parallel loop reproducible.
 *
 * @param seed Value used to seed the generator
 */
PYHELIOS_API void seedGlobalRandomGenerator(unsigned int seed);

/**
 * @brief Draw from the process-wide generator: uniform float over [0,1)
 * @return Uniform random float in [0,1); 0 on error (check getLastErrorCode())
 */
PYHELIOS_API float globalRandu();

/**
 * @brief Draw from the process-wide generator: uniform integer over the inclusive range [imin,imax]
 *
 * Every value in the range, endpoints included, is equally likely. If imin >= imax,
 * imin is returned.
 *
 * @param imin Lower bound (inclusive)
 * @param imax Upper bound (inclusive)
 * @return Uniform random integer in [imin,imax]; 0 on error (check getLastErrorCode())
 */
PYHELIOS_API int globalRanduInt(int imin, int imax);

//=============================================================================
// Leaf Angle Distribution CDFs (core/global.h; helios-core v1.3.87+)
//=============================================================================

/**
 * @brief Cumulative distribution function of the Beta leaf-inclination distribution
 *
 * Gives the probability that a leaf inclination drawn from the Beta distribution is
 * no greater than theta. Shares its parameterization with the sampler, in which nu is
 * the first shape parameter of the underlying Beta variate and mu the second, so the
 * mean inclination is (pi/2)*nu/(mu+nu).
 *
 * theta is measured from vertical and saturates outside [0, pi/2]: a negative angle
 * returns 0 and an angle at or above pi/2 returns 1.
 *
 * @param theta Leaf inclination angle (radians)
 * @param mu First parameter of the beta distribution; must be positive
 * @param nu Second parameter of the beta distribution; must be positive
 * @return Cumulative probability in [0,1]; 0 on error (check getLastErrorCode())
 */
PYHELIOS_API float evaluateBetaDistributionCDF(float theta, float mu, float nu);

/**
 * @brief Inverse of evaluateBetaDistributionCDF(): the inclination at a given probability
 *
 * @param probability Cumulative probability; must be in [0,1]
 * @param mu First parameter of the beta distribution; must be positive
 * @param nu Second parameter of the beta distribution; must be positive
 * @return Leaf inclination angle (radians) in [0, pi/2]; 0 on error (check getLastErrorCode())
 */
PYHELIOS_API float invertBetaDistributionCDF(float probability, float mu, float nu);

/**
 * @brief Cumulative distribution function of the ellipsoidal leaf-azimuth distribution
 *
 * The probability is measured from the ellipse rotation phi0_degrees, and phi is wrapped
 * into [0, 2*pi).
 *
 * @param phi Azimuth angle (radians)
 * @param e Eccentricity of the ellipsoidal distribution; must be in [0,1]
 * @param phi0_degrees Azimuthal rotation of the ellipse (degrees)
 * @return Cumulative probability in [0,1]; 0 on error (check getLastErrorCode())
 */
PYHELIOS_API float evaluateEllipsoidalAzimuthCDF(float phi, float e, float phi0_degrees);

/**
 * @brief Inverse of evaluateEllipsoidalAzimuthCDF(): the azimuth at a given probability
 *
 * @param probability Cumulative probability; must be in [0,1]
 * @param e Eccentricity of the ellipsoidal distribution; must be in [0,1]
 * @param phi0_degrees Azimuthal rotation of the ellipse (degrees)
 * @return Azimuth angle (radians) in [0, 2*pi); 0 on error (check getLastErrorCode())
 */
PYHELIOS_API float invertEllipsoidalAzimuthCDF(float probability, float e, float phi0_degrees);

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