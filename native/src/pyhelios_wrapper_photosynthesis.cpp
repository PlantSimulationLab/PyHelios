// PyHelios C Interface - PhotosynthesisModel Functions
// Provides photosynthesis modeling capabilities including empirical and Farquhar models

#include "../include/pyhelios_wrapper_common.h"
#include "../include/pyhelios_wrapper_context.h"
#include "Context.h"
#include <string>
#include <exception>
#include <vector>

#ifdef PHOTOSYNTHESIS_PLUGIN_AVAILABLE
#include "../include/pyhelios_wrapper_photosynthesis.h"
#include "PhotosynthesisModel.h"

// =============================================================================
// C4 helpers (must have C++ linkage — kept outside the extern "C" block below).
// =============================================================================

namespace pyhelios_photosynthesis_internal {

constexpr unsigned int C4_COEFF_COUNT = 43;
// Sentinel: PhotosyntheticTemperatureResponseParameters initializes Topt = 10000 K when no
// optimum is set. After K → C conversion this is ~9726.85 — far above any realistic Topt.
// Helios's own validation (validateOptimalTemperature in PhotosynthesisModel.h) rejects
// Topt > 100 °C as biologically unrealistic, so any value at or above 200 °C must be the
// "no optimum" sentinel rather than user-supplied data. We expose it as -1 in the flat
// coefficient array.
constexpr float C4_NO_OPTIMUM_TOPT_C = 200.f;

// Apply 4 floats (val_at_25C, dHa, Topt_C, dHd) to a temperature-response member.
// Selects the appropriate ctor by sentinels (-1) following the existing Farquhar convention.
template <typename SetterT>
inline void applyTempResponse(SetterT &&setter, float val, float dHa, float Topt_C, float dHd) {
    if (dHa < 0) {
        setter(val);
    } else if (Topt_C < 0) {
        setter(val, dHa);
    } else if (dHd < 0) {
        setter(val, dHa, Topt_C);
    } else {
        setter(val, dHa, Topt_C, dHd);
    }
}

// Pack a PhotosyntheticTemperatureResponseParameters into 4 floats at out[0..3].
// Topt is converted from Kelvin (internal) to Celsius and replaced with -1 if it indicates "no optimum".
inline void packTempResponse(const PhotosyntheticTemperatureResponseParameters &p, float *out) {
    out[0] = p.value_at_25C;
    out[1] = p.dHa;
    float topt_c = p.Topt - 273.15f;
    out[2] = (topt_c >= C4_NO_OPTIMUM_TOPT_C) ? -1.f : topt_c;
    out[3] = p.dHd;
}

// Unpack a 43-float coefficient array into a C4ModelCoefficients struct.
inline C4ModelCoefficients unpackC4Coefficients(const float *coefficients) {
    C4ModelCoefficients c;

    applyTempResponse([&](auto... a) { c.setVpmax(a...); }, coefficients[0], coefficients[1], coefficients[2], coefficients[3]);
    applyTempResponse([&](auto... a) { c.setVcmax(a...); }, coefficients[4], coefficients[5], coefficients[6], coefficients[7]);
    applyTempResponse([&](auto... a) { c.setJmax(a...); }, coefficients[8], coefficients[9], coefficients[10], coefficients[11]);
    applyTempResponse([&](auto... a) { c.setRd(a...); }, coefficients[12], coefficients[13], coefficients[14], coefficients[15]);
    applyTempResponse([&](auto... a) { c.setMesophyllConductance_gm(a...); }, coefficients[16], coefficients[17], coefficients[18], coefficients[19]);

    c.Kc_25 = coefficients[20];
    c.Ko_25 = coefficients[21];
    c.Kp_25 = coefficients[22];
    c.gamma_star_25 = coefficients[23];
    c.Om_25 = coefficients[24];

    c.dH_Kc = coefficients[25];
    c.dH_Ko = coefficients[26];
    c.dH_Kp = coefficients[27];
    c.dH_gamma_star = coefficients[28];
    c.dH_Om = coefficients[29];

    c.alpha_psII_fraction = coefficients[30];
    c.x_etr_partition = coefficients[31];
    c.Vpr = coefficients[32];
    c.Rm_frac = coefficients[33];
    c.fcyc = coefficients[34];
    c.gbs = coefficients[35];
    c.ao = coefficients[36];
    c.absorptance = coefficients[37];
    c.f_spectral = coefficients[38];
    c.theta_etr = coefficients[39];
    c.h_protons = coefficients[40];
    c.H_J = coefficients[41];
    c.H_Jcyc = coefficients[42];

    return c;
}

// Pack a C4ModelCoefficients struct into a 43-float coefficient array.
inline void packC4Coefficients(const C4ModelCoefficients &c, float *out) {
    packTempResponse(c.getVpmaxTempResponse(), &out[0]);
    packTempResponse(c.getVcmaxTempResponse(), &out[4]);
    packTempResponse(c.getJmaxTempResponse(), &out[8]);
    packTempResponse(c.getRdTempResponse(), &out[12]);
    packTempResponse(c.getMesophyllConductance_gmTempResponse(), &out[16]);

    out[20] = c.Kc_25;
    out[21] = c.Ko_25;
    out[22] = c.Kp_25;
    out[23] = c.gamma_star_25;
    out[24] = c.Om_25;

    out[25] = c.dH_Kc;
    out[26] = c.dH_Ko;
    out[27] = c.dH_Kp;
    out[28] = c.dH_gamma_star;
    out[29] = c.dH_Om;

    out[30] = c.alpha_psII_fraction;
    out[31] = c.x_etr_partition;
    out[32] = c.Vpr;
    out[33] = c.Rm_frac;
    out[34] = c.fcyc;
    out[35] = c.gbs;
    out[36] = c.ao;
    out[37] = c.absorptance;
    out[38] = c.f_spectral;
    out[39] = c.theta_etr;
    out[40] = c.h_protons;
    out[41] = c.H_J;
    out[42] = c.H_Jcyc;
}

} // namespace pyhelios_photosynthesis_internal

extern "C" {

using pyhelios_photosynthesis_internal::C4_COEFF_COUNT;
using pyhelios_photosynthesis_internal::packC4Coefficients;
using pyhelios_photosynthesis_internal::unpackC4Coefficients;

    //=============================================================================
    // PhotosynthesisModel Lifecycle
    //=============================================================================
    
    PYHELIOS_API PhotosynthesisModel* createPhotosynthesisModel(helios::Context* context) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return nullptr;
            }
            
            return new PhotosynthesisModel(context);
            
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (createPhotosynthesisModel): ") + e.what());
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (createPhotosynthesisModel): Unknown error creating PhotosynthesisModel.");
            return nullptr;
        }
    }
    
    PYHELIOS_API void destroyPhotosynthesisModel(PhotosynthesisModel* photosynthesis_model) {
        if (photosynthesis_model) {
            delete photosynthesis_model;
        }
    }
    
    //=============================================================================
    // Model Type Configuration
    //=============================================================================
    
    PYHELIOS_API void setPhotosynthesisModelTypeEmpirical(PhotosynthesisModel* photosynthesis_model) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            
            photosynthesis_model->setModelType_Empirical();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::setModelType_Empirical): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::setModelType_Empirical): Unknown error setting empirical model type.");
        }
    }
    
    PYHELIOS_API void setPhotosynthesisModelTypeFarquhar(PhotosynthesisModel* photosynthesis_model) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }

            photosynthesis_model->setModelType_Farquhar();

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::setModelType_Farquhar): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::setModelType_Farquhar): Unknown error setting Farquhar model type.");
        }
    }

    PYHELIOS_API void setPhotosynthesisModelTypeC4(PhotosynthesisModel* photosynthesis_model) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }

            photosynthesis_model->setModelType_C4();

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::setModelType_C4): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::setModelType_C4): Unknown error setting C4 model type.");
        }
    }
    
    //=============================================================================
    // Model Execution
    //=============================================================================
    
    PYHELIOS_API void runPhotosynthesisModel(PhotosynthesisModel* photosynthesis_model) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            
            photosynthesis_model->run();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::run): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::run): Unknown error running photosynthesis model.");
        }
    }
    
    PYHELIOS_API void runPhotosynthesisModelForUUIDs(PhotosynthesisModel* photosynthesis_model, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null");
                return;
            }
            if (uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUID count must be greater than 0");
                return;
            }
            
            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            photosynthesis_model->run(uuid_vector);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::run): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::run): Unknown error running photosynthesis model for UUIDs.");
        }
    }
    
    //=============================================================================
    // Species Library Integration
    //=============================================================================
    
    PYHELIOS_API void setFarquharCoefficientsFromLibrary(PhotosynthesisModel* photosynthesis_model, const char* species) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            if (!species) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Species name is null");
                return;
            }
            
            photosynthesis_model->setFarquharCoefficientsFromLibrary(species);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::setFarquharCoefficientsFromLibrary): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::setFarquharCoefficientsFromLibrary): Unknown error setting coefficients from library.");
        }
    }
    
    PYHELIOS_API void setFarquharCoefficientsFromLibraryForUUIDs(PhotosynthesisModel* photosynthesis_model, const char* species, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            if (!species) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Species name is null");
                return;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null");
                return;
            }
            if (uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUID count must be greater than 0");
                return;
            }
            
            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            photosynthesis_model->setFarquharCoefficientsFromLibrary(species, uuid_vector);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::setFarquharCoefficientsFromLibrary): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::setFarquharCoefficientsFromLibrary): Unknown error setting coefficients from library for UUIDs.");
        }
    }
    
    PYHELIOS_API void getFarquharCoefficientsFromLibrary(PhotosynthesisModel* photosynthesis_model, const char* species, float* coefficients, unsigned int coeff_size) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            if (!species) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Species name is null");
                return;
            }
            if (!coefficients) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Coefficients array is null");
                return;
            }
            if (coeff_size < 18) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Coefficients array size must be at least 18");
                return;
            }
            
            // Get coefficients from library
            FarquharModelCoefficients farquhar_coeffs = photosynthesis_model->getFarquharCoefficientsFromLibrary(species);
            
            // Pack into float array: [Vcmax, Jmax, alpha, Rd, O, TPU_flag, ...temp_params]
            coefficients[0] = farquhar_coeffs.Vcmax;
            coefficients[1] = farquhar_coeffs.Jmax;
            coefficients[2] = farquhar_coeffs.alpha;
            coefficients[3] = farquhar_coeffs.Rd;
            coefficients[4] = farquhar_coeffs.O;
            coefficients[5] = static_cast<float>(farquhar_coeffs.TPU_flag);
            
            // Temperature parameters (simplified - just the main ones)
            coefficients[6] = farquhar_coeffs.c_Vcmax;
            coefficients[7] = farquhar_coeffs.dH_Vcmax;
            coefficients[8] = farquhar_coeffs.c_Jmax;
            coefficients[9] = farquhar_coeffs.dH_Jmax;
            coefficients[10] = farquhar_coeffs.c_Rd;
            coefficients[11] = farquhar_coeffs.dH_Rd;
            coefficients[12] = farquhar_coeffs.c_Kc;
            coefficients[13] = farquhar_coeffs.dH_Kc;
            coefficients[14] = farquhar_coeffs.c_Ko;
            coefficients[15] = farquhar_coeffs.dH_Ko;
            coefficients[16] = farquhar_coeffs.c_Gamma;
            coefficients[17] = farquhar_coeffs.dH_Gamma;
            
            // Fill remaining with zeros if array is larger
            for (unsigned int i = 18; i < coeff_size; ++i) {
                coefficients[i] = 0.0f;
            }
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::getFarquharCoefficientsFromLibrary): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::getFarquharCoefficientsFromLibrary): Unknown error getting coefficients from library.");
        }
    }
    
    //=============================================================================
    // Model Parameter Configuration - Empirical Model
    //=============================================================================
    
    PYHELIOS_API void setEmpiricalModelCoefficients(PhotosynthesisModel* photosynthesis_model, const float* coefficients, unsigned int coeff_count) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            if (!coefficients) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Coefficients array is null");
                return;
            }
            if (coeff_count < 10) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Empirical model coefficients array must have at least 10 elements");
                return;
            }
            
            // Create empirical coefficients from array [Tref, Ci_ref, Asat, theta, Tmin, Topt, q, R, ER, kC]
            EmpiricalModelCoefficients empirical_coeffs;
            empirical_coeffs.Tref = coefficients[0];
            empirical_coeffs.Ci_ref = coefficients[1];
            empirical_coeffs.Asat = coefficients[2];
            empirical_coeffs.theta = coefficients[3];
            empirical_coeffs.Tmin = coefficients[4];
            empirical_coeffs.Topt = coefficients[5];
            empirical_coeffs.q = coefficients[6];
            empirical_coeffs.R = coefficients[7];
            empirical_coeffs.ER = coefficients[8];
            empirical_coeffs.kC = coefficients[9];
            
            photosynthesis_model->setModelCoefficients(empirical_coeffs);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::setModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::setModelCoefficients): Unknown error setting empirical model coefficients.");
        }
    }
    
    PYHELIOS_API void setEmpiricalModelCoefficientsForUUIDs(PhotosynthesisModel* photosynthesis_model, const float* coefficients, unsigned int coeff_count, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            if (!coefficients) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Coefficients array is null");
                return;
            }
            if (coeff_count < 10) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Empirical model coefficients array must have at least 10 elements");
                return;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null");
                return;
            }
            if (uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUID count must be greater than 0");
                return;
            }
            
            // Create empirical coefficients from array
            EmpiricalModelCoefficients empirical_coeffs;
            empirical_coeffs.Tref = coefficients[0];
            empirical_coeffs.Ci_ref = coefficients[1];
            empirical_coeffs.Asat = coefficients[2];
            empirical_coeffs.theta = coefficients[3];
            empirical_coeffs.Tmin = coefficients[4];
            empirical_coeffs.Topt = coefficients[5];
            empirical_coeffs.q = coefficients[6];
            empirical_coeffs.R = coefficients[7];
            empirical_coeffs.ER = coefficients[8];
            empirical_coeffs.kC = coefficients[9];
            
            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            photosynthesis_model->setModelCoefficients(empirical_coeffs, uuid_vector);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::setModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::setModelCoefficients): Unknown error setting empirical model coefficients for UUIDs.");
        }
    }
    
    //=============================================================================
    // Model Parameter Configuration - Farquhar Model
    //=============================================================================
    
    PYHELIOS_API void setFarquharModelCoefficients(PhotosynthesisModel* photosynthesis_model, const float* coefficients, unsigned int coeff_count) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            if (!coefficients) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Coefficients array is null");
                return;
            }
            if (coeff_count < 18) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Farquhar model coefficients array must have at least 18 elements");
                return;
            }
            
            // Create Farquhar coefficients from array [Vcmax, Jmax, alpha, Rd, O, TPU_flag, ...temp_params]
            FarquharModelCoefficients farquhar_coeffs;
            farquhar_coeffs.Vcmax = coefficients[0];
            farquhar_coeffs.Jmax = coefficients[1];
            farquhar_coeffs.alpha = coefficients[2];
            farquhar_coeffs.Rd = coefficients[3];
            farquhar_coeffs.O = coefficients[4];
            farquhar_coeffs.TPU_flag = static_cast<int>(coefficients[5]);
            
            // Basic temperature parameters (using simplified interface)
            if (coeff_count >= 18) {
                farquhar_coeffs.c_Vcmax = coefficients[6];
                farquhar_coeffs.dH_Vcmax = coefficients[7];
                farquhar_coeffs.c_Jmax = coefficients[8];
                farquhar_coeffs.dH_Jmax = coefficients[9];
                farquhar_coeffs.c_Rd = coefficients[10];
                farquhar_coeffs.dH_Rd = coefficients[11];
                farquhar_coeffs.c_Kc = coefficients[12];
                farquhar_coeffs.dH_Kc = coefficients[13];
                farquhar_coeffs.c_Ko = coefficients[14];
                farquhar_coeffs.dH_Ko = coefficients[15];
                farquhar_coeffs.c_Gamma = coefficients[16];
                farquhar_coeffs.dH_Gamma = coefficients[17];
            }

            // Mesophyll conductance gm temperature response (helios-core 1.3.72+).
            // Slots 18..21 only consumed when present so legacy 18-float callers keep working.
            if (coeff_count >= 22) {
                pyhelios_photosynthesis_internal::applyTempResponse(
                    [&](auto... a) { farquhar_coeffs.setMesophyllConductance_gm(a...); },
                    coefficients[18], coefficients[19], coefficients[20], coefficients[21]);
            }

            photosynthesis_model->setModelCoefficients(farquhar_coeffs);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::setModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::setModelCoefficients): Unknown error setting Farquhar model coefficients.");
        }
    }

    PYHELIOS_API void setFarquharModelCoefficientsForUUIDs(PhotosynthesisModel* photosynthesis_model, const float* coefficients, unsigned int coeff_count, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            if (!coefficients) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Coefficients array is null");
                return;
            }
            if (coeff_count < 18) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Farquhar model coefficients array must have at least 18 elements");
                return;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null");
                return;
            }
            if (uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUID count must be greater than 0");
                return;
            }
            
            // Create Farquhar coefficients from array
            FarquharModelCoefficients farquhar_coeffs;
            farquhar_coeffs.Vcmax = coefficients[0];
            farquhar_coeffs.Jmax = coefficients[1];
            farquhar_coeffs.alpha = coefficients[2];
            farquhar_coeffs.Rd = coefficients[3];
            farquhar_coeffs.O = coefficients[4];
            farquhar_coeffs.TPU_flag = static_cast<int>(coefficients[5]);
            
            // Basic temperature parameters
            if (coeff_count >= 18) {
                farquhar_coeffs.c_Vcmax = coefficients[6];
                farquhar_coeffs.dH_Vcmax = coefficients[7];
                farquhar_coeffs.c_Jmax = coefficients[8];
                farquhar_coeffs.dH_Jmax = coefficients[9];
                farquhar_coeffs.c_Rd = coefficients[10];
                farquhar_coeffs.dH_Rd = coefficients[11];
                farquhar_coeffs.c_Kc = coefficients[12];
                farquhar_coeffs.dH_Kc = coefficients[13];
                farquhar_coeffs.c_Ko = coefficients[14];
                farquhar_coeffs.dH_Ko = coefficients[15];
                farquhar_coeffs.c_Gamma = coefficients[16];
                farquhar_coeffs.dH_Gamma = coefficients[17];
            }

            // Mesophyll conductance gm temperature response (helios-core 1.3.72+).
            if (coeff_count >= 22) {
                pyhelios_photosynthesis_internal::applyTempResponse(
                    [&](auto... a) { farquhar_coeffs.setMesophyllConductance_gm(a...); },
                    coefficients[18], coefficients[19], coefficients[20], coefficients[21]);
            }

            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            photosynthesis_model->setModelCoefficients(farquhar_coeffs, uuid_vector);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::setModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::setModelCoefficients): Unknown error setting Farquhar model coefficients for UUIDs.");
        }
    }
    
    //=============================================================================
    // Individual Farquhar Parameter Setters with Temperature Response
    //=============================================================================
    
    PYHELIOS_API void setFarquharVcmax(PhotosynthesisModel* photosynthesis_model, float vcmax_at_25c, float dha, float topt, float dhd, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            
            // Individual parameter setters require explicit UUIDs
            if (uuids == nullptr || uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Individual parameter setters require explicit UUIDs. Use setFarquharModelCoefficients() for all primitives.");
                return;
            }
            
            std::vector<uint> target_uuids(uuids, uuids + uuid_count);
            
            // For each UUID, get existing coefficients, modify only Vcmax, then set back
            for (uint uuid : target_uuids) {
                try {
                    // Get existing coefficients for this UUID
                    FarquharModelCoefficients existing_coeffs = photosynthesis_model->getFarquharModelCoefficients(uuid);
                    
                    // Modify only the Vcmax parameter using the appropriate overload
                    if (dha < 0) {
                        existing_coeffs.setVcmax(vcmax_at_25c);
                    } else if (topt < 0) {
                        existing_coeffs.setVcmax(vcmax_at_25c, dha);
                    } else if (dhd < 0) {
                        existing_coeffs.setVcmax(vcmax_at_25c, dha, topt);
                    } else {
                        existing_coeffs.setVcmax(vcmax_at_25c, dha, topt, dhd);
                    }
                    
                    // Set the modified coefficients back for this UUID
                    std::vector<uint> single_uuid = {uuid};
                    photosynthesis_model->setModelCoefficients(existing_coeffs, single_uuid);
                    
                } catch (const std::exception& e) {
                    // If this UUID doesn't have photosynthesis data yet, skip it silently
                    // This allows the function to work on mixed primitive sets
                    continue;
                }
            }
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::setVcmax): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::setVcmax): Unknown error setting Vcmax parameter.");
        }
    }
    
    PYHELIOS_API void setFarquharJmax(PhotosynthesisModel* photosynthesis_model, float jmax_at_25c, float dha, float topt, float dhd, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            
            // Individual parameter setters require explicit UUIDs
            if (uuids == nullptr || uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Individual parameter setters require explicit UUIDs. Use setFarquharModelCoefficients() for all primitives.");
                return;
            }
            
            std::vector<uint> target_uuids(uuids, uuids + uuid_count);
            
            // For each UUID, get existing coefficients, modify only Jmax, then set back
            for (uint uuid : target_uuids) {
                try {
                    // Get existing coefficients for this UUID
                    FarquharModelCoefficients existing_coeffs = photosynthesis_model->getFarquharModelCoefficients(uuid);
                    
                    // Modify only the Jmax parameter using the appropriate overload
                    if (dha < 0) {
                        existing_coeffs.setJmax(jmax_at_25c);
                    } else if (topt < 0) {
                        existing_coeffs.setJmax(jmax_at_25c, dha);
                    } else if (dhd < 0) {
                        existing_coeffs.setJmax(jmax_at_25c, dha, topt);
                    } else {
                        existing_coeffs.setJmax(jmax_at_25c, dha, topt, dhd);
                    }
                    
                    // Set the modified coefficients back for this UUID
                    std::vector<uint> single_uuid = {uuid};
                    photosynthesis_model->setModelCoefficients(existing_coeffs, single_uuid);
                    
                } catch (const std::exception& e) {
                    // If this UUID doesn't have photosynthesis data yet, skip it silently
                    continue;
                }
            }
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::setJmax): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::setJmax): Unknown error setting Jmax parameter.");
        }
    }
    
    PYHELIOS_API void setFarquharRd(PhotosynthesisModel* photosynthesis_model, float rd_at_25c, float dha, float topt, float dhd, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            
            // Individual parameter setters require explicit UUIDs
            if (uuids == nullptr || uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Individual parameter setters require explicit UUIDs. Use setFarquharModelCoefficients() for all primitives.");
                return;
            }
            
            std::vector<uint> target_uuids(uuids, uuids + uuid_count);
            
            // For each UUID, get existing coefficients, modify only Rd, then set back
            for (uint uuid : target_uuids) {
                try {
                    // Get existing coefficients for this UUID
                    FarquharModelCoefficients existing_coeffs = photosynthesis_model->getFarquharModelCoefficients(uuid);
                    
                    // Modify only the Rd parameter using the appropriate overload
                    if (dha < 0) {
                        existing_coeffs.setRd(rd_at_25c);
                    } else if (topt < 0) {
                        existing_coeffs.setRd(rd_at_25c, dha);
                    } else if (dhd < 0) {
                        existing_coeffs.setRd(rd_at_25c, dha, topt);
                    } else {
                        existing_coeffs.setRd(rd_at_25c, dha, topt, dhd);
                    }
                    
                    // Set the modified coefficients back for this UUID
                    std::vector<uint> single_uuid = {uuid};
                    photosynthesis_model->setModelCoefficients(existing_coeffs, single_uuid);
                    
                } catch (const std::exception& e) {
                    // If this UUID doesn't have photosynthesis data yet, skip it silently
                    continue;
                }
            }
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::setRd): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::setRd): Unknown error setting Rd parameter.");
        }
    }
    
    PYHELIOS_API void setFarquharQuantumEfficiency(PhotosynthesisModel* photosynthesis_model, float alpha_at_25c, float dha, float topt, float dhd, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            
            // Individual parameter setters require explicit UUIDs
            if (uuids == nullptr || uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Individual parameter setters require explicit UUIDs. Use setFarquharModelCoefficients() for all primitives.");
                return;
            }
            
            std::vector<uint> target_uuids(uuids, uuids + uuid_count);
            
            // For each UUID, get existing coefficients, modify only alpha, then set back
            for (uint uuid : target_uuids) {
                try {
                    // Get existing coefficients for this UUID
                    FarquharModelCoefficients existing_coeffs = photosynthesis_model->getFarquharModelCoefficients(uuid);
                    
                    // Modify only the quantum efficiency parameter using the appropriate overload
                    if (dha < 0) {
                        existing_coeffs.setQuantumEfficiency_alpha(alpha_at_25c);
                    } else if (topt < 0) {
                        existing_coeffs.setQuantumEfficiency_alpha(alpha_at_25c, dha);
                    } else if (dhd < 0) {
                        existing_coeffs.setQuantumEfficiency_alpha(alpha_at_25c, dha, topt);
                    } else {
                        existing_coeffs.setQuantumEfficiency_alpha(alpha_at_25c, dha, topt, dhd);
                    }
                    
                    // Set the modified coefficients back for this UUID
                    std::vector<uint> single_uuid = {uuid};
                    photosynthesis_model->setModelCoefficients(existing_coeffs, single_uuid);
                    
                } catch (const std::exception& e) {
                    // If this UUID doesn't have photosynthesis data yet, skip it silently
                    continue;
                }
            }
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::setQuantumEfficiency_alpha): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::setQuantumEfficiency_alpha): Unknown error setting quantum efficiency parameter.");
        }
    }
    
    PYHELIOS_API void setFarquharLightResponseCurvature(PhotosynthesisModel* photosynthesis_model, float theta_at_25c, float dha, float topt, float dhd, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            
            // Individual parameter setters require explicit UUIDs
            if (uuids == nullptr || uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Individual parameter setters require explicit UUIDs. Use setFarquharModelCoefficients() for all primitives.");
                return;
            }
            
            std::vector<uint> target_uuids(uuids, uuids + uuid_count);
            
            // For each UUID, get existing coefficients, modify only theta, then set back
            for (uint uuid : target_uuids) {
                try {
                    // Get existing coefficients for this UUID
                    FarquharModelCoefficients existing_coeffs = photosynthesis_model->getFarquharModelCoefficients(uuid);
                    
                    // Modify only the light response curvature parameter using the appropriate overload
                    if (dha < 0) {
                        existing_coeffs.setLightResponseCurvature_theta(theta_at_25c);
                    } else if (topt < 0) {
                        existing_coeffs.setLightResponseCurvature_theta(theta_at_25c, dha);
                    } else if (dhd < 0) {
                        existing_coeffs.setLightResponseCurvature_theta(theta_at_25c, dha, topt);
                    } else {
                        existing_coeffs.setLightResponseCurvature_theta(theta_at_25c, dha, topt, dhd);
                    }
                    
                    // Set the modified coefficients back for this UUID
                    std::vector<uint> single_uuid = {uuid};
                    photosynthesis_model->setModelCoefficients(existing_coeffs, single_uuid);
                    
                } catch (const std::exception& e) {
                    // If this UUID doesn't have photosynthesis data yet, skip it silently
                    continue;
                }
            }
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::setLightResponseCurvature_theta): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::setLightResponseCurvature_theta): Unknown error setting light response curvature parameter.");
        }
    }
    
    //=============================================================================
    // Parameter Getters
    //=============================================================================
    
    PYHELIOS_API void getEmpiricalModelCoefficients(PhotosynthesisModel* photosynthesis_model, unsigned int uuid, float* coefficients, unsigned int coeff_size) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            if (!coefficients) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Coefficients array is null");
                return;
            }
            if (coeff_size < 10) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Coefficients array size must be at least 10");
                return;
            }
            
            EmpiricalModelCoefficients empirical_coeffs = photosynthesis_model->getEmpiricalModelCoefficients(uuid);
            
            // Pack into float array [Tref, Ci_ref, Asat, theta, Tmin, Topt, q, R, ER, kC]
            coefficients[0] = empirical_coeffs.Tref;
            coefficients[1] = empirical_coeffs.Ci_ref;
            coefficients[2] = empirical_coeffs.Asat;
            coefficients[3] = empirical_coeffs.theta;
            coefficients[4] = empirical_coeffs.Tmin;
            coefficients[5] = empirical_coeffs.Topt;
            coefficients[6] = empirical_coeffs.q;
            coefficients[7] = empirical_coeffs.R;
            coefficients[8] = empirical_coeffs.ER;
            coefficients[9] = empirical_coeffs.kC;
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::getEmpiricalModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::getEmpiricalModelCoefficients): Unknown error getting empirical model coefficients.");
        }
    }
    
    PYHELIOS_API void getFarquharModelCoefficients(PhotosynthesisModel* photosynthesis_model, unsigned int uuid, float* coefficients, unsigned int coeff_size) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            if (!coefficients) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Coefficients array is null");
                return;
            }
            if (coeff_size < 18) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Coefficients array size must be at least 18");
                return;
            }

            FarquharModelCoefficients farquhar_coeffs = photosynthesis_model->getFarquharModelCoefficients(uuid);

            // Pack into float array [Vcmax, Jmax, alpha, Rd, O, TPU_flag, ...temp_params]
            coefficients[0] = farquhar_coeffs.Vcmax;
            coefficients[1] = farquhar_coeffs.Jmax;
            coefficients[2] = farquhar_coeffs.alpha;
            coefficients[3] = farquhar_coeffs.Rd;
            coefficients[4] = farquhar_coeffs.O;
            coefficients[5] = static_cast<float>(farquhar_coeffs.TPU_flag);

            // Temperature parameters
            coefficients[6] = farquhar_coeffs.c_Vcmax;
            coefficients[7] = farquhar_coeffs.dH_Vcmax;
            coefficients[8] = farquhar_coeffs.c_Jmax;
            coefficients[9] = farquhar_coeffs.dH_Jmax;
            coefficients[10] = farquhar_coeffs.c_Rd;
            coefficients[11] = farquhar_coeffs.dH_Rd;
            coefficients[12] = farquhar_coeffs.c_Kc;
            coefficients[13] = farquhar_coeffs.dH_Kc;
            coefficients[14] = farquhar_coeffs.c_Ko;
            coefficients[15] = farquhar_coeffs.dH_Ko;
            coefficients[16] = farquhar_coeffs.c_Gamma;
            coefficients[17] = farquhar_coeffs.dH_Gamma;

            // Mesophyll conductance gm temperature response (helios-core 1.3.72+).
            // Slots 18..21 only populated if the buffer is large enough; older 18-float
            // callers continue to work without seeing gm.
            if (coeff_size >= 22) {
                pyhelios_photosynthesis_internal::packTempResponse(
                    farquhar_coeffs.getMesophyllConductance_gmTempResponse(),
                    &coefficients[18]);
            }

            // Fill remaining with zeros if array is even larger
            for (unsigned int i = (coeff_size >= 22 ? 22u : 18u); i < coeff_size; ++i) {
                coefficients[i] = 0.0f;
            }

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::getFarquharModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::getFarquharModelCoefficients): Unknown error getting Farquhar model coefficients.");
        }
    }
    
    //=============================================================================
    // Model Configuration and Utilities
    //=============================================================================
    
    PYHELIOS_API void enablePhotosynthesisMessages(PhotosynthesisModel* photosynthesis_model) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            
            photosynthesis_model->enableMessages();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::enableMessages): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::enableMessages): Unknown error enabling messages.");
        }
    }
    
    PYHELIOS_API void disablePhotosynthesisMessages(PhotosynthesisModel* photosynthesis_model) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            
            photosynthesis_model->disableMessages();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::disableMessages): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::disableMessages): Unknown error disabling messages.");
        }
    }
    
    PYHELIOS_API void optionalOutputPhotosynthesisPrimitiveData(PhotosynthesisModel* photosynthesis_model, const char* label) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            
            photosynthesis_model->optionalOutputPrimitiveData(label);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::optionalOutputPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::optionalOutputPrimitiveData): Unknown error setting optional output.");
        }
    }
    
    PYHELIOS_API void printPhotosynthesisDefaultValueReport(PhotosynthesisModel* photosynthesis_model) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            
            photosynthesis_model->printDefaultValueReport();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::printDefaultValueReport): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::printDefaultValueReport): Unknown error printing default value report.");
        }
    }
    
    PYHELIOS_API void printPhotosynthesisDefaultValueReportForUUIDs(PhotosynthesisModel* photosynthesis_model, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null");
                return;
            }
            if (uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUID count must be greater than 0");
                return;
            }

            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            photosynthesis_model->printDefaultValueReport(uuid_vector);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::printDefaultValueReport): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::printDefaultValueReport): Unknown error printing default value report for UUIDs.");
        }
    }

    //=============================================================================
    // Farquhar Mesophyll Conductance (gm)
    //=============================================================================

    PYHELIOS_API void setFarquharMesophyllConductance(PhotosynthesisModel* photosynthesis_model, float gm_at_25c, float dha, float topt, float dhd, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }

            if (uuids == nullptr || uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Individual parameter setters require explicit UUIDs. Use setFarquharModelCoefficients() for all primitives.");
                return;
            }

            std::vector<uint> target_uuids(uuids, uuids + uuid_count);

            for (uint uuid : target_uuids) {
                try {
                    FarquharModelCoefficients existing_coeffs = photosynthesis_model->getFarquharModelCoefficients(uuid);

                    if (dha < 0) {
                        existing_coeffs.setMesophyllConductance_gm(gm_at_25c);
                    } else if (topt < 0) {
                        existing_coeffs.setMesophyllConductance_gm(gm_at_25c, dha);
                    } else if (dhd < 0) {
                        existing_coeffs.setMesophyllConductance_gm(gm_at_25c, dha, topt);
                    } else {
                        existing_coeffs.setMesophyllConductance_gm(gm_at_25c, dha, topt, dhd);
                    }

                    std::vector<uint> single_uuid = {uuid};
                    photosynthesis_model->setModelCoefficients(existing_coeffs, single_uuid);

                } catch (const std::exception&) {
                    // Skip UUIDs without photosynthesis data (matches setFarquharVcmax convention).
                    continue;
                }
            }

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::setMesophyllConductance_gm): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::setMesophyllConductance_gm): Unknown error setting mesophyll conductance.");
        }
    }

    //=============================================================================
    // C4 Model (von Caemmerer 2021) Coefficient Configuration
    //=============================================================================

    PYHELIOS_API void setC4CoefficientsFromLibrary(PhotosynthesisModel* photosynthesis_model, const char* species) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            if (!species) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Species name is null");
                return;
            }

            photosynthesis_model->setC4CoefficientsFromLibrary(species);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::setC4CoefficientsFromLibrary): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::setC4CoefficientsFromLibrary): Unknown error setting C4 coefficients from library.");
        }
    }

    PYHELIOS_API void setC4CoefficientsFromLibraryForUUIDs(PhotosynthesisModel* photosynthesis_model, const char* species, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            if (!species) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Species name is null");
                return;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null");
                return;
            }
            if (uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUID count must be greater than 0");
                return;
            }

            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            photosynthesis_model->setC4CoefficientsFromLibrary(species, uuid_vector);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::setC4CoefficientsFromLibrary): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::setC4CoefficientsFromLibrary): Unknown error setting C4 coefficients from library for UUIDs.");
        }
    }

    PYHELIOS_API void getC4CoefficientsFromLibrary(PhotosynthesisModel* photosynthesis_model, const char* species, float* coefficients, unsigned int coeff_size) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            if (!species) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Species name is null");
                return;
            }
            if (!coefficients) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Coefficients array is null");
                return;
            }
            if (coeff_size < C4_COEFF_COUNT) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "C4 coefficients array must have at least 43 elements");
                return;
            }

            C4ModelCoefficients c = photosynthesis_model->getC4CoefficientsFromLibrary(species);
            packC4Coefficients(c, coefficients);

            for (unsigned int i = C4_COEFF_COUNT; i < coeff_size; ++i) {
                coefficients[i] = 0.f;
            }

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::getC4CoefficientsFromLibrary): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::getC4CoefficientsFromLibrary): Unknown error getting C4 coefficients from library.");
        }
    }

    PYHELIOS_API void setC4ModelCoefficients(PhotosynthesisModel* photosynthesis_model, const float* coefficients, unsigned int coeff_count) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            if (!coefficients) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Coefficients array is null");
                return;
            }
            if (coeff_count < C4_COEFF_COUNT) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "C4 model coefficients array must have at least 43 elements");
                return;
            }

            C4ModelCoefficients c = unpackC4Coefficients(coefficients);
            photosynthesis_model->setModelCoefficients(c);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::setModelCoefficients (C4)): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::setModelCoefficients (C4)): Unknown error setting C4 model coefficients.");
        }
    }

    PYHELIOS_API void setC4ModelCoefficientsForMaterial(PhotosynthesisModel* photosynthesis_model, const char* material_label, const float* coefficients, unsigned int coeff_count) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            if (!material_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Material label is null");
                return;
            }
            if (!coefficients) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Coefficients array is null");
                return;
            }
            if (coeff_count < pyhelios_photosynthesis_internal::C4_COEFF_COUNT) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "C4 model coefficients array must have at least 43 elements");
                return;
            }

            C4ModelCoefficients c = pyhelios_photosynthesis_internal::unpackC4Coefficients(coefficients);
            photosynthesis_model->setModelCoefficients(std::string(material_label), c);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::setModelCoefficients (C4 by material)): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::setModelCoefficients (C4 by material)): Unknown error.");
        }
    }

    PYHELIOS_API void setC4CoefficientsFromLibraryForMaterial(PhotosynthesisModel* photosynthesis_model, const char* species, const char* material_label) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            if (!species) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Species name is null");
                return;
            }
            if (!material_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Material label is null");
                return;
            }

            photosynthesis_model->setC4CoefficientsFromLibrary(std::string(species), std::string(material_label));

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::setC4CoefficientsFromLibrary (by material)): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::setC4CoefficientsFromLibrary (by material)): Unknown error.");
        }
    }

    PYHELIOS_API void setC4ModelCoefficientsForUUIDs(PhotosynthesisModel* photosynthesis_model, const float* coefficients, unsigned int coeff_count, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            if (!coefficients) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Coefficients array is null");
                return;
            }
            if (coeff_count < C4_COEFF_COUNT) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "C4 model coefficients array must have at least 43 elements");
                return;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null");
                return;
            }
            if (uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUID count must be greater than 0");
                return;
            }

            C4ModelCoefficients c = unpackC4Coefficients(coefficients);
            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            photosynthesis_model->setModelCoefficients(c, uuid_vector);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::setModelCoefficients (C4)): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::setModelCoefficients (C4)): Unknown error setting C4 model coefficients for UUIDs.");
        }
    }

    PYHELIOS_API void getC4ModelCoefficients(PhotosynthesisModel* photosynthesis_model, unsigned int uuid, float* coefficients, unsigned int coeff_size) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            if (!coefficients) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Coefficients array is null");
                return;
            }
            if (coeff_size < C4_COEFF_COUNT) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "C4 coefficients array must have at least 43 elements");
                return;
            }

            C4ModelCoefficients c = photosynthesis_model->getC4ModelCoefficients(uuid);
            packC4Coefficients(c, coefficients);

            for (unsigned int i = C4_COEFF_COUNT; i < coeff_size; ++i) {
                coefficients[i] = 0.f;
            }

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::getC4ModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::getC4ModelCoefficients): Unknown error getting C4 model coefficients.");
        }
    }

    PYHELIOS_API void setPhotosynthesisCm(PhotosynthesisModel* photosynthesis_model, float cm, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!photosynthesis_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PhotosynthesisModel pointer is null");
                return;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null");
                return;
            }
            if (uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUID count must be greater than 0");
                return;
            }

            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            photosynthesis_model->setCm(cm, uuid_vector);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhotosynthesisModel::setCm): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhotosynthesisModel::setCm): Unknown error setting Cm.");
        }
    }

} // extern "C"

#endif // PHOTOSYNTHESIS_PLUGIN_AVAILABLE