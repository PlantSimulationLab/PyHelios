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

    //=============================================================================
    // Blackbody Radiation (core/global.h; helios-core v1.3.90+)
    //=============================================================================

    PYHELIOS_API float blackbodyBandFraction(float wavelength_min_nm, float wavelength_max_nm, float temperature_K) {
        clearError();
        try {
            return helios::blackbodyBandFraction(wavelength_min_nm, wavelength_max_nm, temperature_K);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, std::string("ERROR (blackbodyBandFraction): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (blackbodyBandFraction): Unknown error.");
            return 0.0f;
        }
    }

    PYHELIOS_API float blackbodySpectralRadiance(float wavelength_nm, float temperature_K) {
        clearError();
        try {
            return helios::blackbodySpectralRadiance(wavelength_nm, temperature_K);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, std::string("ERROR (blackbodySpectralRadiance): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (blackbodySpectralRadiance): Unknown error.");
            return 0.0f;
        }
    }

    //=============================================================================
    // Single-channel PNG images (core/global.h; helios-core v1.3.95+)
    //=============================================================================

    static thread_local std::vector<unsigned short> s_png_single_channel_buffer;

    PYHELIOS_API const unsigned short* readPNGSingleChannel(const char* filename, unsigned int* width, unsigned int* height, unsigned int* size) {
        clearError();
        try {
            if (!width || !height || !size) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (readPNGSingleChannel): Output pointer is null"); return nullptr; }
            *width = 0;
            *height = 0;
            *size = 0;
            if (!filename) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (readPNGSingleChannel): File name pointer is null"); return nullptr; }
            uint w = 0;
            uint h = 0;
            std::vector<uint16_t> values;
            helios::readPNGSingleChannel(std::string(filename), w, h, values);
            s_png_single_channel_buffer.assign(values.begin(), values.end());
            *width = w;
            *height = h;
            *size = static_cast<unsigned int>(s_png_single_channel_buffer.size());
            return s_png_single_channel_buffer.empty() ? nullptr : s_png_single_channel_buffer.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_FILE_IO, std::string("ERROR (readPNGSingleChannel): ") + e.what());
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (readPNGSingleChannel): Unknown error.");
            return nullptr;
        }
    }

    PYHELIOS_API void writePNGSingleChannel(const char* filename, unsigned int width, unsigned int height, const unsigned short* pixel_values, unsigned int count, unsigned int bit_depth) {
        clearError();
        try {
            if (!filename) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (writePNGSingleChannel): File name pointer is null"); return; }
            if (count > 0 && !pixel_values) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (writePNGSingleChannel): Pixel value pointer is null"); return; }
            std::vector<uint16_t> values(pixel_values, pixel_values + count);
            helios::writePNGSingleChannel(std::string(filename), width, height, values, bit_depth);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_FILE_IO, std::string("ERROR (writePNGSingleChannel): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (writePNGSingleChannel): Unknown error.");
        }
    }

    static thread_local std::vector<unsigned short> s_class_area_classes;
    static thread_local std::vector<float> s_class_area_fractions;

    PYHELIOS_API unsigned int classMapAreaFractions(const unsigned short* classes, unsigned int class_count, int width, int height, const float* uv, unsigned int uv_count, const unsigned short** out_classes, const float** out_fractions) {
        clearError();
        try {
            if (!out_classes || !out_fractions) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (classMapAreaFractions): Output pointer is null"); return 0; }
            *out_classes = nullptr;
            *out_fractions = nullptr;
            if (class_count > 0 && !classes) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (classMapAreaFractions): Class pointer is null"); return 0; }
            if (uv_count > 0 && !uv) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (classMapAreaFractions): (u,v) pointer is null"); return 0; }
            std::vector<uint16_t> classes_vec(classes, classes + class_count);
            std::vector<helios::vec2> uv_vec;
            uv_vec.reserve(uv_count);
            for (unsigned int i = 0; i < uv_count; ++i) {
                uv_vec.push_back(helios::make_vec2(uv[2 * i], uv[2 * i + 1]));
            }
            std::vector<std::pair<uint16_t, float>> result = helios::classMapAreaFractions(classes_vec, helios::make_int2(width, height), uv_vec);
            s_class_area_classes.clear();
            s_class_area_fractions.clear();
            s_class_area_classes.reserve(result.size());
            s_class_area_fractions.reserve(result.size());
            for (const auto& entry : result) {
                s_class_area_classes.push_back(entry.first);
                s_class_area_fractions.push_back(entry.second);
            }
            *out_classes = s_class_area_classes.empty() ? nullptr : s_class_area_classes.data();
            *out_fractions = s_class_area_fractions.empty() ? nullptr : s_class_area_fractions.data();
            return static_cast<unsigned int>(result.size());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (classMapAreaFractions): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (classMapAreaFractions): Unknown error.");
            return 0;
        }
    }

} //extern "C"
