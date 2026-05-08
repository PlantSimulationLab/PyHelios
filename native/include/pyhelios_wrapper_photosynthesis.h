/**
 * @file pyhelios_wrapper_photosynthesis.h
 * @brief PhotosynthesisModel functions for PyHelios C wrapper
 * 
 * This header provides photosynthesis modeling capabilities including
 * empirical and Farquhar-von Caemmerer-Berry models, species library
 * integration, and comprehensive parameter management.
 */

#ifndef PYHELIOS_WRAPPER_PHOTOSYNTHESIS_H
#define PYHELIOS_WRAPPER_PHOTOSYNTHESIS_H

#include "pyhelios_wrapper_common.h"

// Forward declarations for PhotosynthesisModel interface
class PhotosynthesisModel;
namespace helios {
    class Context;
}

#ifdef __cplusplus
extern "C" {
#endif

//=============================================================================
// PhotosynthesisModel Functions
//=============================================================================

/**
 * @brief Create a new PhotosynthesisModel
 * @param context Pointer to the Helios context
 * @return Pointer to the created PhotosynthesisModel, or nullptr on error
 */
PYHELIOS_API PhotosynthesisModel* createPhotosynthesisModel(helios::Context* context);

/**
 * @brief Destroy a PhotosynthesisModel
 * @param photosynthesis_model Pointer to the PhotosynthesisModel to destroy
 */
PYHELIOS_API void destroyPhotosynthesisModel(PhotosynthesisModel* photosynthesis_model);

//=============================================================================
// Model Type Configuration
//=============================================================================

/**
 * @brief Set photosynthesis model to use empirical model
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 */
PYHELIOS_API void setPhotosynthesisModelTypeEmpirical(PhotosynthesisModel* photosynthesis_model);

/**
 * @brief Set photosynthesis model to use Farquhar-von Caemmerer-Berry model
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 */
PYHELIOS_API void setPhotosynthesisModelTypeFarquhar(PhotosynthesisModel* photosynthesis_model);

/**
 * @brief Set photosynthesis model to use the von Caemmerer (2021) steady-state C4 model
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 */
PYHELIOS_API void setPhotosynthesisModelTypeC4(PhotosynthesisModel* photosynthesis_model);

//=============================================================================
// Model Execution
//=============================================================================

/**
 * @brief Run photosynthesis model for all primitives
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 */
PYHELIOS_API void runPhotosynthesisModel(PhotosynthesisModel* photosynthesis_model);

/**
 * @brief Run photosynthesis model for specific primitives
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param uuids Array of primitive UUIDs
 * @param uuid_count Number of UUIDs in the array
 */
PYHELIOS_API void runPhotosynthesisModelForUUIDs(PhotosynthesisModel* photosynthesis_model, const unsigned int* uuids, unsigned int uuid_count);

//=============================================================================
// Species Library Integration
//=============================================================================

/**
 * @brief Set Farquhar model coefficients from species library for all primitives
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param species Name of the species (case insensitive, supports aliases)
 */
PYHELIOS_API void setFarquharCoefficientsFromLibrary(PhotosynthesisModel* photosynthesis_model, const char* species);

/**
 * @brief Set Farquhar model coefficients from species library for specific primitives
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param species Name of the species (case insensitive, supports aliases)
 * @param uuids Array of primitive UUIDs
 * @param uuid_count Number of UUIDs in the array
 */
PYHELIOS_API void setFarquharCoefficientsFromLibraryForUUIDs(PhotosynthesisModel* photosynthesis_model, const char* species, const unsigned int* uuids, unsigned int uuid_count);

/**
 * @brief Get Farquhar model coefficients from species library
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param species Name of the species (case insensitive, supports aliases)
 * @param coefficients Output array for coefficients [Vcmax, Jmax, alpha, Rd, O, TPU_flag, ...temp_params]
 * @param coeff_size Size of coefficients array (must be at least 20)
 */
PYHELIOS_API void getFarquharCoefficientsFromLibrary(PhotosynthesisModel* photosynthesis_model, const char* species, float* coefficients, unsigned int coeff_size);

//=============================================================================
// Model Parameter Configuration
//=============================================================================

/**
 * @brief Set empirical model coefficients for all primitives
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param coefficients Array of empirical coefficients [Tref, Ci_ref, Asat, theta, Tmin, Topt, q, R, ER, kC]
 * @param coeff_count Number of coefficients (must be 10)
 */
PYHELIOS_API void setEmpiricalModelCoefficients(PhotosynthesisModel* photosynthesis_model, const float* coefficients, unsigned int coeff_count);

/**
 * @brief Set empirical model coefficients for specific primitives
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param coefficients Array of empirical coefficients [Tref, Ci_ref, Asat, theta, Tmin, Topt, q, R, ER, kC]
 * @param coeff_count Number of coefficients (must be 10)
 * @param uuids Array of primitive UUIDs
 * @param uuid_count Number of UUIDs in the array
 */
PYHELIOS_API void setEmpiricalModelCoefficientsForUUIDs(PhotosynthesisModel* photosynthesis_model, const float* coefficients, unsigned int coeff_count, const unsigned int* uuids, unsigned int uuid_count);

/**
 * @brief Set Farquhar model coefficients for all primitives
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param coefficients Array of Farquhar coefficients [Vcmax, Jmax, alpha, Rd, O, TPU_flag, ...temp_params]
 * @param coeff_count Number of coefficients (must be at least 20)
 */
PYHELIOS_API void setFarquharModelCoefficients(PhotosynthesisModel* photosynthesis_model, const float* coefficients, unsigned int coeff_count);

/**
 * @brief Set Farquhar model coefficients for specific primitives
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param coefficients Array of Farquhar coefficients [Vcmax, Jmax, alpha, Rd, O, TPU_flag, ...temp_params]
 * @param coeff_count Number of coefficients (must be at least 20)
 * @param uuids Array of primitive UUIDs
 * @param uuid_count Number of UUIDs in the array
 */
PYHELIOS_API void setFarquharModelCoefficientsForUUIDs(PhotosynthesisModel* photosynthesis_model, const float* coefficients, unsigned int coeff_count, const unsigned int* uuids, unsigned int uuid_count);

//=============================================================================
// Individual Farquhar Parameter Setters with Temperature Response
//=============================================================================

/**
 * @brief Set Vcmax parameter with temperature response for specific primitives
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param vcmax_at_25c Value at 25°C
 * @param dha Rate of increase parameter (optional, -1 for default)
 * @param topt Optimum temperature in °C (optional, -1 for default)
 * @param dhd Rate of decrease parameter (optional, -1 for default)
 * @param uuids Array of primitive UUIDs (nullptr for all primitives)
 * @param uuid_count Number of UUIDs in the array (0 for all primitives)
 */
PYHELIOS_API void setFarquharVcmax(PhotosynthesisModel* photosynthesis_model, float vcmax_at_25c, float dha, float topt, float dhd, const unsigned int* uuids, unsigned int uuid_count);

/**
 * @brief Set Jmax parameter with temperature response for specific primitives
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param jmax_at_25c Value at 25°C
 * @param dha Rate of increase parameter (optional, -1 for default)
 * @param topt Optimum temperature in °C (optional, -1 for default)
 * @param dhd Rate of decrease parameter (optional, -1 for default)
 * @param uuids Array of primitive UUIDs (nullptr for all primitives)
 * @param uuid_count Number of UUIDs in the array (0 for all primitives)
 */
PYHELIOS_API void setFarquharJmax(PhotosynthesisModel* photosynthesis_model, float jmax_at_25c, float dha, float topt, float dhd, const unsigned int* uuids, unsigned int uuid_count);

/**
 * @brief Set dark respiration (Rd) parameter with temperature response for specific primitives
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param rd_at_25c Value at 25°C
 * @param dha Rate of increase parameter (optional, -1 for default)
 * @param topt Optimum temperature in °C (optional, -1 for default)
 * @param dhd Rate of decrease parameter (optional, -1 for default)
 * @param uuids Array of primitive UUIDs (nullptr for all primitives)
 * @param uuid_count Number of UUIDs in the array (0 for all primitives)
 */
PYHELIOS_API void setFarquharRd(PhotosynthesisModel* photosynthesis_model, float rd_at_25c, float dha, float topt, float dhd, const unsigned int* uuids, unsigned int uuid_count);

/**
 * @brief Set quantum efficiency (alpha) parameter with temperature response for specific primitives
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param alpha_at_25c Value at 25°C
 * @param dha Rate of increase parameter (optional, -1 for default)
 * @param topt Optimum temperature in °C (optional, -1 for default)
 * @param dhd Rate of decrease parameter (optional, -1 for default)
 * @param uuids Array of primitive UUIDs (nullptr for all primitives)
 * @param uuid_count Number of UUIDs in the array (0 for all primitives)
 */
PYHELIOS_API void setFarquharQuantumEfficiency(PhotosynthesisModel* photosynthesis_model, float alpha_at_25c, float dha, float topt, float dhd, const unsigned int* uuids, unsigned int uuid_count);

/**
 * @brief Set light response curvature (theta) parameter with temperature response for specific primitives
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param theta_at_25c Value at 25°C
 * @param dha Rate of increase parameter (optional, -1 for default)
 * @param topt Optimum temperature in °C (optional, -1 for default)
 * @param dhd Rate of decrease parameter (optional, -1 for default)
 * @param uuids Array of primitive UUIDs (nullptr for all primitives)
 * @param uuid_count Number of UUIDs in the array (0 for all primitives)
 */
PYHELIOS_API void setFarquharLightResponseCurvature(PhotosynthesisModel* photosynthesis_model, float theta_at_25c, float dha, float topt, float dhd, const unsigned int* uuids, unsigned int uuid_count);

/**
 * @brief Set Farquhar mesophyll conductance gm with temperature response for specific primitives
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param gm_at_25c Value of gm at 25°C (mol CO2 / m^2 / s / bar)
 * @param dha Activation energy dHa (kJ/mol; -1 for no temperature response, equivalent to constant gm)
 * @param topt Optimum temperature in °C (optional; -1 for monotonic Arrhenius)
 * @param dhd Deactivation energy dHd (kJ/mol; -1 for default = 10*dHa or 600)
 * @param uuids Array of primitive UUIDs (must be non-null and non-empty)
 * @param uuid_count Number of UUIDs in the array
 * @note When gm is finite, the C3 Farquhar solver derives Cc = Ci - A/gm via an
 *       Ethier & Livingston quadratic. The default gm = +infinity reproduces the
 *       legacy Cc = Ci behaviour bit-for-bit.
 */
PYHELIOS_API void setFarquharMesophyllConductance(PhotosynthesisModel* photosynthesis_model, float gm_at_25c, float dha, float topt, float dhd, const unsigned int* uuids, unsigned int uuid_count);

//=============================================================================
// C4 Model (von Caemmerer 2021) Coefficient Configuration
//=============================================================================

//
// C4 coefficient flat-array layout (43 floats):
//
//   [ 0..3]   Vpmax temperature response: value_at_25C, dHa, Topt(C), dHd
//   [ 4..7]   Vcmax temperature response: value_at_25C, dHa, Topt(C), dHd
//   [ 8..11]  Jmax  temperature response: value_at_25C, dHa, Topt(C), dHd
//   [12..15]  Rd    temperature response: value_at_25C, dHa, Topt(C), dHd
//   [16..19]  gm    temperature response: value_at_25C, dHa, Topt(C), dHd
//   [20..24]  Rubisco/PEPC kinetic constants at 25C: Kc_25, Ko_25, Kp_25, gamma_star_25, Om_25
//   [25..29]  Activation energies (kJ/mol): dH_Kc, dH_Ko, dH_Kp, dH_gamma_star, dH_Om
//   [30..42]  User-tunable scalars: alpha_psII_fraction, x_etr_partition, Vpr, Rm_frac, fcyc,
//             gbs, ao, absorptance, f_spectral, theta_etr, h_protons, H_J, H_Jcyc
//
// Topt is exposed in Celsius (helios stores it internally as Kelvin). When packing,
// values >= 1000 (the "no optimum" sentinel 10000-273.15) are written as -1; on input
// negative slots fall through to the appropriate constructor overload (constant /
// Arrhenius / peaked / peaked+dHd) following the same convention as the Farquhar
// individual setters.

/**
 * @brief Set C4 model coefficients from species library for all primitives
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param species Name of the species (e.g. "SetariaViridis_vC2021", "GenericC4_vC2000", "Maize_Massad2007")
 */
PYHELIOS_API void setC4CoefficientsFromLibrary(PhotosynthesisModel* photosynthesis_model, const char* species);

/**
 * @brief Set C4 model coefficients from species library for specific primitives
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param species Name of the species
 * @param uuids Array of primitive UUIDs
 * @param uuid_count Number of UUIDs in the array
 */
PYHELIOS_API void setC4CoefficientsFromLibraryForUUIDs(PhotosynthesisModel* photosynthesis_model, const char* species, const unsigned int* uuids, unsigned int uuid_count);

/**
 * @brief Get C4 model coefficients for a species from the C4 library
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param species Name of the species
 * @param coefficients Output array (must be at least 43 floats)
 * @param coeff_size Size of coefficients array
 */
PYHELIOS_API void getC4CoefficientsFromLibrary(PhotosynthesisModel* photosynthesis_model, const char* species, float* coefficients, unsigned int coeff_size);

/**
 * @brief Set C4 model coefficients for all primitives
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param coefficients Array of 43 floats (see layout comment above)
 * @param coeff_count Number of coefficients (must be 43)
 */
PYHELIOS_API void setC4ModelCoefficients(PhotosynthesisModel* photosynthesis_model, const float* coefficients, unsigned int coeff_count);

/**
 * @brief Set C4 model coefficients for specific primitives
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param coefficients Array of 43 floats (see layout comment above)
 * @param coeff_count Number of coefficients (must be 43)
 * @param uuids Array of primitive UUIDs
 * @param uuid_count Number of UUIDs in the array
 */
PYHELIOS_API void setC4ModelCoefficientsForUUIDs(PhotosynthesisModel* photosynthesis_model, const float* coefficients, unsigned int coeff_count, const unsigned int* uuids, unsigned int uuid_count);

/**
 * @brief Set C4 model coefficients for all primitives that share a material label.
 *
 * Wraps the helios-core 1.3.72 ``setModelCoefficients(material_label, C4ModelCoefficients)``
 * overload. Coefficients are cached by material on first lookup and reused for every
 * primitive that references the material at run() time.
 *
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param material_label Material identifier (must already exist on at least one primitive)
 * @param coefficients Array of 43 floats (see layout comment above)
 * @param coeff_count Number of coefficients (must be 43)
 */
PYHELIOS_API void setC4ModelCoefficientsForMaterial(PhotosynthesisModel* photosynthesis_model, const char* material_label, const float* coefficients, unsigned int coeff_count);

/**
 * @brief Apply a C4 species library entry to all primitives that share a material label.
 *
 * Wraps the helios-core 1.3.72 ``setC4CoefficientsFromLibrary(species, material_label)``
 * overload.
 *
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param species Name of the species (e.g. "SetariaViridis_vC2021")
 * @param material_label Material identifier
 */
PYHELIOS_API void setC4CoefficientsFromLibraryForMaterial(PhotosynthesisModel* photosynthesis_model, const char* species, const char* material_label);

/**
 * @brief Get C4 model coefficients for a specific primitive
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param uuid Primitive UUID
 * @param coefficients Output array (must be at least 43 floats)
 * @param coeff_size Size of coefficients array
 */
PYHELIOS_API void getC4ModelCoefficients(PhotosynthesisModel* photosynthesis_model, unsigned int uuid, float* coefficients, unsigned int coeff_size);

/**
 * @brief Manually set the mesophyll cytosolic CO2 partial pressure (Cm) for primitives (C4 only)
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param cm Mesophyll cytosolic CO2 partial pressure in ubar
 * @param uuids Array of primitive UUIDs (must be non-null and non-empty)
 * @param uuid_count Number of UUIDs in the array
 * @note Bypasses the Cm = Ci - A/gm fixed-point iteration; primarily for testing
 *       and validation against published reference data.
 */
PYHELIOS_API void setPhotosynthesisCm(PhotosynthesisModel* photosynthesis_model, float cm, const unsigned int* uuids, unsigned int uuid_count);

//=============================================================================
// Parameter Getters
//=============================================================================

/**
 * @brief Get empirical model coefficients for a specific primitive
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param uuid Primitive UUID
 * @param coefficients Output array for coefficients [Tref, Ci_ref, Asat, theta, Tmin, Topt, q, R, ER, kC]
 * @param coeff_size Size of coefficients array (must be at least 10)
 */
PYHELIOS_API void getEmpiricalModelCoefficients(PhotosynthesisModel* photosynthesis_model, unsigned int uuid, float* coefficients, unsigned int coeff_size);

/**
 * @brief Get Farquhar model coefficients for a specific primitive
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param uuid Primitive UUID
 * @param coefficients Output array for coefficients [Vcmax, Jmax, alpha, Rd, O, TPU_flag, ...temp_params]
 * @param coeff_size Size of coefficients array (must be at least 20)
 */
PYHELIOS_API void getFarquharModelCoefficients(PhotosynthesisModel* photosynthesis_model, unsigned int uuid, float* coefficients, unsigned int coeff_size);

//=============================================================================
// Model Configuration and Utilities
//=============================================================================

/**
 * @brief Enable PhotosynthesisModel status messages
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 */
PYHELIOS_API void enablePhotosynthesisMessages(PhotosynthesisModel* photosynthesis_model);

/**
 * @brief Disable PhotosynthesisModel status messages
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 */
PYHELIOS_API void disablePhotosynthesisMessages(PhotosynthesisModel* photosynthesis_model);

/**
 * @brief Add optional output primitive data
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param label Name of the primitive data to add (e.g., "Ci", "limitation_state", "Gamma_CO2")
 */
PYHELIOS_API void optionalOutputPhotosynthesisPrimitiveData(PhotosynthesisModel* photosynthesis_model, const char* label);

/**
 * @brief Print default value report for all primitives
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 */
PYHELIOS_API void printPhotosynthesisDefaultValueReport(PhotosynthesisModel* photosynthesis_model);

/**
 * @brief Print default value report for specific primitives
 * @param photosynthesis_model Pointer to the PhotosynthesisModel
 * @param uuids Array of primitive UUIDs
 * @param uuid_count Number of UUIDs in the array
 */
PYHELIOS_API void printPhotosynthesisDefaultValueReportForUUIDs(PhotosynthesisModel* photosynthesis_model, const unsigned int* uuids, unsigned int uuid_count);

#ifdef __cplusplus
}
#endif

#endif // PYHELIOS_WRAPPER_PHOTOSYNTHESIS_H