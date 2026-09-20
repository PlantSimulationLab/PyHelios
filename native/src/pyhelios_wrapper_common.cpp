// PyHelios C Interface - Common Functions
// Provides shared error handling and utilities for all PyHelios wrapper modules

#include "../include/pyhelios_wrapper_common.h"
#include "global.h"
#include <string>
#include <exception>
#include <cstdio>

// Global error state for thread-safe error handling - matches PyHelios error codes
static thread_local std::string last_error_message;
static thread_local int last_error_code = PYHELIOS_SUCCESS;

// Helper function to set error state with PyHelios error codes
void setError(int error_code, const std::string& message) {
    last_error_code = error_code;
    last_error_message = message;
}

extern "C" {

    //=============================================================================
    // Error Handling Functions
    //=============================================================================
    
    PYHELIOS_API int getLastErrorCode() {
        return last_error_code;
    }

    PYHELIOS_API const char* getLastErrorMessage() {
        return last_error_message.c_str();
    }
    
    PYHELIOS_API void clearError() {
        last_error_code = PYHELIOS_SUCCESS;
        last_error_message.clear();
    }

    //=============================================================================
    // GPU Environment Functions (core/global.h; helios-core v1.3.79+)
    //=============================================================================

    PYHELIOS_API int gpuRequiredByEnvironment() {
        clearError();
        try {
            return helios::gpuRequiredByEnvironment() ? 1 : 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (gpuRequiredByEnvironment): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (gpuRequiredByEnvironment): Unknown error.");
            return 0;
        }
    }

    PYHELIOS_API void requireGPUOrFail(const char* context_message) {
        clearError();
        try {
            // A null description is not an error; the native function only interpolates
            // it into the message, so an empty string is the faithful equivalent.
            helios::requireGPUOrFail(context_message ? std::string(context_message) : std::string());
        } catch (const std::runtime_error& e) {
            // The expected path whenever HELIOS_REQUIRE_GPU is set: the native function
            // signals "should have had a GPU" by throwing. Preserve its message verbatim,
            // which already names the contradiction case (both REQUIRE and NO_GPU set).
            setError(PYHELIOS_ERROR_GPU_INITIALIZATION, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (requireGPUOrFail): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (requireGPUOrFail): Unknown error.");
        }
    }

    PYHELIOS_API void seedGlobalRandomGenerator(unsigned int seed) {
        clearError();
        try {
            helios::seedRandomGenerator(seed);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (seedGlobalRandomGenerator): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (seedGlobalRandomGenerator): Unknown error.");
        }
    }

    PYHELIOS_API float globalRandu() {
        clearError();
        try {
            return helios::randu();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (globalRandu): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (globalRandu): Unknown error.");
            return 0.0f;
        }
    }

    PYHELIOS_API int globalRanduInt(int imin, int imax) {
        clearError();
        try {
            return helios::randu(imin, imax);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (globalRanduInt): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (globalRanduInt): Unknown error.");
            return 0;
        }
    }

    //=============================================================================
    // Leaf Angle Distribution CDFs (core/global.h; helios-core v1.3.87+)
    //=============================================================================

    PYHELIOS_API float evaluateBetaDistributionCDF(float theta, float mu, float nu) {
        clearError();
        try {
            return helios::evaluate_Beta_distribution_CDF(theta, mu, nu);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, std::string("ERROR (evaluateBetaDistributionCDF): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (evaluateBetaDistributionCDF): Unknown error.");
            return 0.0f;
        }
    }

    PYHELIOS_API float invertBetaDistributionCDF(float probability, float mu, float nu) {
        clearError();
        try {
            return helios::invert_Beta_distribution_CDF(probability, mu, nu);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, std::string("ERROR (invertBetaDistributionCDF): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (invertBetaDistributionCDF): Unknown error.");
            return 0.0f;
        }
    }

    PYHELIOS_API float evaluateEllipsoidalAzimuthCDF(float phi, float e, float phi0_degrees) {
        clearError();
        try {
            return helios::evaluate_ellipsoidal_azimuth_CDF(phi, e, phi0_degrees);
        } catch (const std::exception& ex) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, std::string("ERROR (evaluateEllipsoidalAzimuthCDF): ") + ex.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (evaluateEllipsoidalAzimuthCDF): Unknown error.");
            return 0.0f;
        }
    }

    PYHELIOS_API float invertEllipsoidalAzimuthCDF(float probability, float e, float phi0_degrees) {
        clearError();
        try {
            return helios::invert_ellipsoidal_azimuth_CDF(probability, e, phi0_degrees);
        } catch (const std::exception& ex) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, std::string("ERROR (invertEllipsoidalAzimuthCDF): ") + ex.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (invertEllipsoidalAzimuthCDF): Unknown error.");
            return 0.0f;
        }
    }

} //extern "C"