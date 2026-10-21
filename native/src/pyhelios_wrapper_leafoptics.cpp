// PyHelios C Interface - LeafOptics Functions
// Provides PROSPECT leaf optical model capabilities for spectral reflectance/transmittance

#include "../include/pyhelios_wrapper_common.h"
#include "../include/pyhelios_wrapper_context.h"
#include "Context.h"
#include <string>
#include <exception>
#include <vector>

#ifdef LEAFOPTICS_PLUGIN_AVAILABLE
#include "../include/pyhelios_wrapper_leafoptics.h"
#include "LeafOptics.h"

extern "C" {

    //=============================================================================
    // LeafOptics Lifecycle
    //=============================================================================

    PYHELIOS_API LeafOptics* createLeafOptics(helios::Context* context) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return nullptr;
            }

            return new LeafOptics(context);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (createLeafOptics): ") + e.what());
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (createLeafOptics): Unknown error creating LeafOptics.");
            return nullptr;
        }
    }

    PYHELIOS_API void destroyLeafOptics(LeafOptics* leafoptics) {
        if (leafoptics) {
            delete leafoptics;
        }
    }

    //=============================================================================
    // Model Execution
    //=============================================================================

    PYHELIOS_API void leafOpticsRun(LeafOptics* leafoptics, const unsigned int* uuids, unsigned int uuid_count,
                                     const float* properties, const char* label) {
        try {
            clearError();
            if (!leafoptics) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LeafOptics pointer is null");
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
            if (!properties) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Properties array is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }

            // Convert UUIDs to vector
            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);

            // Create LeafOpticsProperties from array
            // Order: [numberlayers, brownpigments, chlorophyllcontent, carotenoidcontent,
            //         anthocyancontent, watermass, drymass, protein, carbonconstituents]
            LeafOpticsProperties leafprops;
            leafprops.numberlayers = properties[0];
            leafprops.brownpigments = properties[1];
            leafprops.chlorophyllcontent = properties[2];
            leafprops.carotenoidcontent = properties[3];
            leafprops.anthocyancontent = properties[4];
            leafprops.watermass = properties[5];
            leafprops.drymass = properties[6];
            leafprops.protein = properties[7];
            leafprops.carbonconstituents = properties[8];
            leafprops.V2Z = properties[9];
            leafprops.fqe = properties[10];

            leafoptics->run(uuid_vector, leafprops, std::string(label));

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (LeafOptics::run): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (LeafOptics::run): Unknown error running LeafOptics model.");
        }
    }

    PYHELIOS_API void leafOpticsRunNoUUIDs(LeafOptics* leafoptics, const float* properties, const char* label) {
        try {
            clearError();
            if (!leafoptics) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LeafOptics pointer is null");
                return;
            }
            if (!properties) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Properties array is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }

            // Create LeafOpticsProperties from array
            LeafOpticsProperties leafprops;
            leafprops.numberlayers = properties[0];
            leafprops.brownpigments = properties[1];
            leafprops.chlorophyllcontent = properties[2];
            leafprops.carotenoidcontent = properties[3];
            leafprops.anthocyancontent = properties[4];
            leafprops.watermass = properties[5];
            leafprops.drymass = properties[6];
            leafprops.protein = properties[7];
            leafprops.carbonconstituents = properties[8];
            leafprops.V2Z = properties[9];
            leafprops.fqe = properties[10];

            leafoptics->run(leafprops, std::string(label));

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (LeafOptics::run): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (LeafOptics::run): Unknown error running LeafOptics model without UUIDs.");
        }
    }

    //=============================================================================
    // Spectral Data Retrieval
    //=============================================================================

    PYHELIOS_API void leafOpticsGetLeafSpectra(LeafOptics* leafoptics, const float* properties,
                                                float* reflectivities, float* transmissivities,
                                                float* wavelengths, unsigned int* size) {
        try {
            clearError();
            if (!leafoptics) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LeafOptics pointer is null");
                if (size) *size = 0;
                return;
            }
            if (!properties) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Properties array is null");
                if (size) *size = 0;
                return;
            }
            if (!reflectivities || !transmissivities || !wavelengths) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output arrays cannot be null");
                if (size) *size = 0;
                return;
            }
            if (!size) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Size pointer is null");
                return;
            }

            // Create LeafOpticsProperties from array
            LeafOpticsProperties leafprops;
            leafprops.numberlayers = properties[0];
            leafprops.brownpigments = properties[1];
            leafprops.chlorophyllcontent = properties[2];
            leafprops.carotenoidcontent = properties[3];
            leafprops.anthocyancontent = properties[4];
            leafprops.watermass = properties[5];
            leafprops.drymass = properties[6];
            leafprops.protein = properties[7];
            leafprops.carbonconstituents = properties[8];
            leafprops.V2Z = properties[9];
            leafprops.fqe = properties[10];

            // Get spectra from LeafOptics
            std::vector<helios::vec2> refl_vec, trans_vec;
            leafoptics->getLeafSpectra(leafprops, refl_vec, trans_vec);

            // Copy data to output arrays
            // vec2 format: (wavelength, value)
            *size = static_cast<unsigned int>(refl_vec.size());

            for (unsigned int i = 0; i < *size; ++i) {
                wavelengths[i] = refl_vec[i].x;       // Wavelength in nm
                reflectivities[i] = refl_vec[i].y;   // Reflectivity value
                transmissivities[i] = trans_vec[i].y; // Transmissivity value
            }

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (LeafOptics::getLeafSpectra): ") + e.what());
            if (size) *size = 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (LeafOptics::getLeafSpectra): Unknown error getting leaf spectra.");
            if (size) *size = 0;
        }
    }

    //=============================================================================
    // Property Management
    //=============================================================================

    PYHELIOS_API void leafOpticsSetProperties(LeafOptics* leafoptics, const unsigned int* uuids, unsigned int uuid_count,
                                               const float* properties) {
        try {
            clearError();
            if (!leafoptics) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LeafOptics pointer is null");
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
            if (!properties) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Properties array is null");
                return;
            }

            // Convert UUIDs to vector
            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);

            // Create LeafOpticsProperties from array
            LeafOpticsProperties leafprops;
            leafprops.numberlayers = properties[0];
            leafprops.brownpigments = properties[1];
            leafprops.chlorophyllcontent = properties[2];
            leafprops.carotenoidcontent = properties[3];
            leafprops.anthocyancontent = properties[4];
            leafprops.watermass = properties[5];
            leafprops.drymass = properties[6];
            leafprops.protein = properties[7];
            leafprops.carbonconstituents = properties[8];
            leafprops.V2Z = properties[9];
            leafprops.fqe = properties[10];

            leafoptics->setProperties(uuid_vector, leafprops);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (LeafOptics::setProperties): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (LeafOptics::setProperties): Unknown error setting properties.");
        }
    }

    PYHELIOS_API void leafOpticsGetPropertiesFromSpectrum(LeafOptics* leafoptics, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!leafoptics) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LeafOptics pointer is null");
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

            // Convert UUIDs to vector
            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);

            leafoptics->getPropertiesFromSpectrum(uuid_vector);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (LeafOptics::getPropertiesFromSpectrum): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (LeafOptics::getPropertiesFromSpectrum): Unknown error getting properties from spectrum.");
        }
    }

    PYHELIOS_API void leafOpticsGetPropertiesFromSpectrumSingle(LeafOptics* leafoptics, unsigned int uuid) {
        try {
            clearError();
            if (!leafoptics) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LeafOptics pointer is null");
                return;
            }

            leafoptics->getPropertiesFromSpectrum(uuid);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (LeafOptics::getPropertiesFromSpectrum): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (LeafOptics::getPropertiesFromSpectrum): Unknown error getting properties from spectrum for single UUID.");
        }
    }

    //=============================================================================
    // Species Library
    //=============================================================================

    PYHELIOS_API void leafOpticsGetPropertiesFromLibrary(LeafOptics* leafoptics, const char* species, float* properties) {
        try {
            clearError();
            if (!leafoptics) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LeafOptics pointer is null");
                return;
            }
            if (!species) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Species name is null");
                return;
            }
            if (!properties) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Properties array is null");
                return;
            }

            // Get properties from library
            LeafOpticsProperties leafprops;
            leafoptics->getPropertiesFromLibrary(std::string(species), leafprops);

            // Pack into output array
            // Order: [numberlayers, brownpigments, chlorophyllcontent, carotenoidcontent,
            //         anthocyancontent, watermass, drymass, protein, carbonconstituents,
            //         V2Z, fqe]
            properties[0] = leafprops.numberlayers;
            properties[1] = leafprops.brownpigments;
            properties[2] = leafprops.chlorophyllcontent;
            properties[3] = leafprops.carotenoidcontent;
            properties[4] = leafprops.anthocyancontent;
            properties[5] = leafprops.watermass;
            properties[6] = leafprops.drymass;
            properties[7] = leafprops.protein;
            properties[8] = leafprops.carbonconstituents;
            properties[9] = leafprops.V2Z;
            properties[10] = leafprops.fqe;

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (LeafOptics::getPropertiesFromLibrary): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (LeafOptics::getPropertiesFromLibrary): Unknown error getting properties from library.");
        }
    }

    //=============================================================================
    // Message Control
    //=============================================================================

    PYHELIOS_API void leafOpticsDisableMessages(LeafOptics* leafoptics) {
        try {
            clearError();
            if (!leafoptics) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LeafOptics pointer is null");
                return;
            }

            leafoptics->disableMessages();

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (LeafOptics::disableMessages): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (LeafOptics::disableMessages): Unknown error disabling messages.");
        }
    }

    PYHELIOS_API void leafOpticsEnableMessages(LeafOptics* leafoptics) {
        try {
            clearError();
            if (!leafoptics) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LeafOptics pointer is null");
                return;
            }

            leafoptics->enableMessages();

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (LeafOptics::enableMessages): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (LeafOptics::enableMessages): Unknown error enabling messages.");
        }
    }

    PYHELIOS_API void leafOpticsOptionalOutputPrimitiveData(LeafOptics* leafoptics, const char* label) {
        try {
            clearError();
            if (!leafoptics) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LeafOptics pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }

            leafoptics->optionalOutputPrimitiveData(label);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (LeafOptics::optionalOutputPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (LeafOptics::optionalOutputPrimitiveData): Unknown error setting optional output.");
        }
    }

    //=============================================================================
    // Nitrogen-Based Automatic Mode
    //=============================================================================

    PYHELIOS_API void leafOpticsRunNitrogen(LeafOptics* leafoptics, const unsigned int* uuids, unsigned int uuid_count,
                                             const float* params, unsigned int num_bins) {
        try {
            clearError();
            if (!leafoptics) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LeafOptics pointer is null");
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
            if (!params) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Nitrogen parameters array is null");
                return;
            }

            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);

            // Order: [f_photosynthetic, N_to_Cab_coefficient, Car_to_Cab_ratio, numberlayers,
            //         anthocyancontent, brownpigments, watermass, drymass, protein, carbonconstituents,
            //         V2Z, fqe, reassignment_threshold, min_reassignment_change]
            LeafOpticsProperties_Nauto nauto;
            nauto.f_photosynthetic = params[0];
            nauto.N_to_Cab_coefficient = params[1];
            nauto.Car_to_Cab_ratio = params[2];
            nauto.numberlayers = params[3];
            nauto.anthocyancontent = params[4];
            nauto.brownpigments = params[5];
            nauto.watermass = params[6];
            nauto.drymass = params[7];
            nauto.protein = params[8];
            nauto.carbonconstituents = params[9];
            nauto.V2Z = params[10];
            nauto.fqe = params[11];
            nauto.reassignment_threshold = params[12];
            nauto.min_reassignment_change = params[13];
            nauto.num_bins = num_bins;

            leafoptics->run(uuid_vector, nauto);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (LeafOptics::run nitrogen mode): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (LeafOptics::run nitrogen mode): Unknown error running nitrogen-based leaf optics.");
        }
    }

    PYHELIOS_API void leafOpticsUpdateNitrogenBasedSpectra(LeafOptics* leafoptics) {
        try {
            clearError();
            if (!leafoptics) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "LeafOptics pointer is null");
                return;
            }

            leafoptics->updateNitrogenBasedSpectra();

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (LeafOptics::updateNitrogenBasedSpectra): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (LeafOptics::updateNitrogenBasedSpectra): Unknown error updating nitrogen-based spectra.");
        }
    }

} // extern "C"

#endif // LEAFOPTICS_PLUGIN_AVAILABLE
