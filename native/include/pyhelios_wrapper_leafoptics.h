/**
 * @file pyhelios_wrapper_leafoptics.h
 * @brief LeafOptics functions for PyHelios C wrapper
 *
 * This header provides leaf optical properties modeling using the PROSPECT model,
 * including spectral reflectance/transmittance computation and species library access.
 */

#ifndef PYHELIOS_WRAPPER_LEAFOPTICS_H
#define PYHELIOS_WRAPPER_LEAFOPTICS_H

#include "pyhelios_wrapper_common.h"

// Forward declarations for LeafOptics interface
class LeafOptics;
namespace helios {
    class Context;
}

#ifdef __cplusplus
extern "C" {
#endif

//=============================================================================
// LeafOptics Lifecycle
//=============================================================================

/**
 * @brief Create a new LeafOptics instance
 * @param context Pointer to the Helios context
 * @return Pointer to the created LeafOptics, or nullptr on error
 * @note Constructor loads spectral data from plugins/leafoptics/spectral_data/prospect_spectral_library.xml
 */
PYHELIOS_API LeafOptics* createLeafOptics(helios::Context* context);

/**
 * @brief Destroy a LeafOptics instance
 * @param leafoptics Pointer to the LeafOptics to destroy
 */
PYHELIOS_API void destroyLeafOptics(LeafOptics* leafoptics);

//=============================================================================
// Model Execution
//=============================================================================

/**
 * @brief Run LeafOptics model and assign spectra to primitives
 * @param leafoptics Pointer to the LeafOptics instance
 * @param uuids Array of primitive UUIDs to assign spectra to
 * @param uuid_count Number of UUIDs in the array
 * @param properties Array of 11 floats: [numberlayers, brownpigments, chlorophyllcontent,
 *                   carotenoidcontent, anthocyancontent, watermass, drymass, protein, carbonconstituents,
 *                   V2Z, fqe]
 *                   V2Z (default 0.0) is the violaxanthin↔zeaxanthin de-epoxidation state used by the
 *                   radiation plugin's SIF pipeline (ignored by the pure PROSPECT calculation).
 *                   fqe (default 1.0) is the intrinsic fluorescence quantum-efficiency scalar applied
 *                   on top of the per-leaf Phi_F at SIF emission time (also ignored by PROSPECT).
 * @param label Label for the spectra (appended to "leaf_reflectivity_" and "leaf_transmissivity_")
 */
PYHELIOS_API void leafOpticsRun(LeafOptics* leafoptics, const unsigned int* uuids, unsigned int uuid_count,
                                 const float* properties, const char* label);

/**
 * @brief Run LeafOptics model without assigning to primitives
 * @param leafoptics Pointer to the LeafOptics instance
 * @param properties Array of 11 floats: [numberlayers, brownpigments, chlorophyllcontent,
 *                   carotenoidcontent, anthocyancontent, watermass, drymass, protein, carbonconstituents,
 *                   V2Z, fqe]
 *                   V2Z (default 0.0) is the violaxanthin↔zeaxanthin de-epoxidation state used by the
 *                   radiation plugin's SIF pipeline (ignored by the pure PROSPECT calculation).
 *                   fqe (default 1.0) is the intrinsic fluorescence quantum-efficiency scalar applied
 *                   on top of the per-leaf Phi_F at SIF emission time (also ignored by PROSPECT).
 * @param label Label for the spectra (appended to "leaf_reflectivity_" and "leaf_transmissivity_")
 */
PYHELIOS_API void leafOpticsRunNoUUIDs(LeafOptics* leafoptics, const float* properties, const char* label);

//=============================================================================
// Spectral Data Retrieval
//=============================================================================

/**
 * @brief Get leaf reflectance and transmittance spectra
 * @param leafoptics Pointer to the LeafOptics instance
 * @param properties Array of 11 floats: [numberlayers, brownpigments, chlorophyllcontent,
 *                   carotenoidcontent, anthocyancontent, watermass, drymass, protein, carbonconstituents,
 *                   V2Z, fqe]
 *                   V2Z (default 0.0) is the violaxanthin↔zeaxanthin de-epoxidation state used by the
 *                   radiation plugin's SIF pipeline (ignored by the pure PROSPECT calculation).
 *                   fqe (default 1.0) is the intrinsic fluorescence quantum-efficiency scalar applied
 *                   on top of the per-leaf Phi_F at SIF emission time (also ignored by PROSPECT).
 * @param reflectivities Output array for reflectivity values (must be at least 2101 floats)
 * @param transmissivities Output array for transmissivity values (must be at least 2101 floats)
 * @param wavelengths Output array for wavelength values in nm (must be at least 2101 floats)
 * @param size Output: number of spectral points (always 2101, covering 400-2500 nm)
 */
PYHELIOS_API void leafOpticsGetLeafSpectra(LeafOptics* leafoptics, const float* properties,
                                            float* reflectivities, float* transmissivities,
                                            float* wavelengths, unsigned int* size);

//=============================================================================
// Property Management
//=============================================================================

/**
 * @brief Set leaf optical properties for primitives
 * @param leafoptics Pointer to the LeafOptics instance
 * @param uuids Array of primitive UUIDs
 * @param uuid_count Number of UUIDs in the array
 * @param properties Array of 11 floats: [numberlayers, brownpigments, chlorophyllcontent,
 *                   carotenoidcontent, anthocyancontent, watermass, drymass, protein, carbonconstituents,
 *                   V2Z, fqe]
 *                   V2Z (default 0.0) is the violaxanthin↔zeaxanthin de-epoxidation state used by the
 *                   radiation plugin's SIF pipeline (ignored by the pure PROSPECT calculation).
 *                   fqe (default 1.0) is the intrinsic fluorescence quantum-efficiency scalar applied
 *                   on top of the per-leaf Phi_F at SIF emission time (also ignored by PROSPECT).
 */
PYHELIOS_API void leafOpticsSetProperties(LeafOptics* leafoptics, const unsigned int* uuids, unsigned int uuid_count,
                                           const float* properties);

/**
 * @brief Get PROSPECT parameters from reflectivity spectrum for primitives
 * @param leafoptics Pointer to the LeafOptics instance
 * @param uuids Array of primitive UUIDs to query
 * @param uuid_count Number of UUIDs in the array
 * @note Primitives without matching spectra are silently skipped
 */
PYHELIOS_API void leafOpticsGetPropertiesFromSpectrum(LeafOptics* leafoptics, const unsigned int* uuids, unsigned int uuid_count);

/**
 * @brief Get PROSPECT parameters from reflectivity spectrum for a single primitive
 * @param leafoptics Pointer to the LeafOptics instance
 * @param uuid Single primitive UUID to query
 * @note If no matching spectrum is found, the primitive is silently skipped
 */
PYHELIOS_API void leafOpticsGetPropertiesFromSpectrumSingle(LeafOptics* leafoptics, unsigned int uuid);

//=============================================================================
// Species Library
//=============================================================================

/**
 * @brief Get leaf optical properties from the built-in species library
 * @param leafoptics Pointer to the LeafOptics instance
 * @param species Name of the species (case-insensitive). Available species:
 *                "default", "garden_lettuce", "alfalfa", "corn", "sunflower",
 *                "english_walnut", "rice", "soybean", "wine_grape", "tomato",
 *                "common_bean", "cowpea"
 * @param properties Output array. Caller MUST allocate at least 11 floats; the function writes the
 *                   full layout: [numberlayers, brownpigments, chlorophyllcontent, carotenoidcontent,
 *                   anthocyancontent, watermass, drymass, protein, carbonconstituents, V2Z, fqe].
 *                   Allocating fewer than 11 floats is undefined behaviour (buffer overflow).
 *                   V2Z (default 0.0) and fqe (default 1.0) are inert for PROSPECT and used by the
 *                   radiation plugin's SIF pipeline.
 * @note If species is not found, default properties are used and a warning is issued
 */
PYHELIOS_API void leafOpticsGetPropertiesFromLibrary(LeafOptics* leafoptics, const char* species, float* properties);

//=============================================================================
// Message Control
//=============================================================================

/**
 * @brief Disable command-line output messages from LeafOptics
 * @param leafoptics Pointer to the LeafOptics instance
 */
PYHELIOS_API void leafOpticsDisableMessages(LeafOptics* leafoptics);

/**
 * @brief Enable command-line output messages from LeafOptics
 * @param leafoptics Pointer to the LeafOptics instance
 */
PYHELIOS_API void leafOpticsEnableMessages(LeafOptics* leafoptics);

/**
 * @brief Selectively output primitive data for specific biochemical properties
 * @param leafoptics Pointer to the LeafOptics instance
 * @param label Property label ("chlorophyll", "carotenoid", "anthocyanin", "brown", "water", "drymass", "protein", "cellulose")
 * @note By default, all biochemical properties are written. Use this to select only needed properties for better performance.
 */
PYHELIOS_API void leafOpticsOptionalOutputPrimitiveData(LeafOptics* leafoptics, const char* label);

#ifdef __cplusplus
}
#endif

#endif // PYHELIOS_WRAPPER_LEAFOPTICS_H
