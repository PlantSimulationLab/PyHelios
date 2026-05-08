// PyHelios C Interface - Radiation Functions  
// Provides GPU-accelerated ray tracing and radiation modeling functions (Vulkan/OptiX backends)

#include "../include/pyhelios_wrapper_common.h"
#include "../include/pyhelios_wrapper_context.h"
#include "Context.h"
#include <string>
#include <exception>

#ifdef RADIATION_PLUGIN_AVAILABLE
#include "../include/pyhelios_wrapper_radiation.h"
#include "RadiationModel.h"

// ColorCorrectionAlgorithm enum for auto-calibration (matching RadiationModel.h)
enum class ColorCorrectionAlgorithm {
    DIAGONAL_ONLY = 0,        //!< Simple diagonal scaling (white balance only)
    MATRIX_3X3_AUTO = 1,      //!< 3x3 matrix with automatic fallback to diagonal if unstable
    MATRIX_3X3_FORCE = 2      //!< Force 3x3 matrix calculation even if potentially unstable
};

// =============================================================================
// SIF helpers (must have C++ linkage — kept outside the extern "C" block below).
// =============================================================================

namespace pyhelios_radiation_internal {

// Populate a SIFCameraProperties struct from a 10-float camera-properties array
// (same layout as addRadiationCameraVec3) plus the two SIF-specific fields.
inline SIFCameraProperties buildSIFCameraProperties(const float* camera_properties,
                                                    float excitation_bin_width_nm,
                                                    unsigned int excitation_scattering_depth) {
    SIFCameraProperties props;
    props.camera_resolution = helios::make_int2((int)camera_properties[0], (int)camera_properties[1]);
    props.focal_plane_distance = camera_properties[2];
    props.lens_diameter = camera_properties[3];
    props.HFOV = camera_properties[4];
    props.FOV_aspect_ratio = camera_properties[5];

    props.lens_focal_length = camera_properties[6];
    props.sensor_width_mm = camera_properties[7];
    props.shutter_speed = camera_properties[8];
    props.camera_zoom = camera_properties[9];

    props.model = "generic";
    props.lens_make = "";
    props.lens_model = "";
    props.lens_specification = "";
    props.exposure = "auto";
    props.white_balance = "auto";

    props.excitation_bin_width_nm = excitation_bin_width_nm;
    props.excitation_scattering_depth = excitation_scattering_depth;
    return props;
}

} // namespace pyhelios_radiation_internal

extern "C" {

using pyhelios_radiation_internal::buildSIFCameraProperties;
    // RadiationModel C interface functions
    
    PYHELIOS_API RadiationModel* createRadiationModel(helios::Context* context) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return nullptr;
            }
            return new RadiationModel(context);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::constructor): ") + e.what());
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::constructor): Unknown error creating RadiationModel.");
            return nullptr;
        }
    }
    
    PYHELIOS_API void destroyRadiationModel(RadiationModel* radiation_model) {
        try {
            clearError();
            if (radiation_model != nullptr) {
                delete radiation_model;
            }
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::destructor): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::destructor): Unknown error destroying RadiationModel.");
        }
    }
    
    PYHELIOS_API void disableRadiationMessages(RadiationModel* radiation_model) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            radiation_model->disableMessages();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::disableMessages): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::disableMessages): Unknown error disabling messages.");
        }
    }
    
    PYHELIOS_API void enableRadiationMessages(RadiationModel* radiation_model) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            radiation_model->enableMessages();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::enableMessages): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::enableMessages): Unknown error enabling messages.");
        }
    }
    
    PYHELIOS_API void addRadiationBand(RadiationModel* radiation_model, const char* label) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            radiation_model->addRadiationBand(std::string(label));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::addRadiationBand): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::addRadiationBand): Unknown error adding radiation band.");
        }
    }
    
    PYHELIOS_API void addRadiationBandWithWavelengths(RadiationModel* radiation_model, const char* label, float wavelength_min, float wavelength_max) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            radiation_model->addRadiationBand(std::string(label), wavelength_min, wavelength_max);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::addRadiationBandWithWavelengths): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::addRadiationBandWithWavelengths): Unknown error adding radiation band with wavelengths.");
        }
    }
    
    PYHELIOS_API void copyRadiationBand(RadiationModel* radiation_model, const char* old_label, const char* new_label) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!old_label || !new_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            radiation_model->copyRadiationBand(std::string(old_label), std::string(new_label));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::copyRadiationBand): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::copyRadiationBand): Unknown error copying radiation band.");
        }
    }

    PYHELIOS_API void copyRadiationBandWithWavelengths(RadiationModel* radiation_model, const char* old_label, const char* new_label,
                                                        float wavelength_min, float wavelength_max) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!old_label || !new_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            radiation_model->copyRadiationBand(std::string(old_label), std::string(new_label), wavelength_min, wavelength_max);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::copyRadiationBand): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::copyRadiationBand): Unknown error copying radiation band with wavelengths.");
        }
    }

    PYHELIOS_API unsigned int addCollimatedRadiationSourceDefault(RadiationModel* radiation_model) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return 0;
            }
            return radiation_model->addCollimatedRadiationSource();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::addCollimatedRadiationSource): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::addCollimatedRadiationSource): Unknown error adding collimated radiation source.");
            return 0;
        }
    }
    
    PYHELIOS_API unsigned int addCollimatedRadiationSourceVec3(RadiationModel* radiation_model, float x, float y, float z) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return 0;
            }
            helios::vec3 direction(x, y, z);
            return radiation_model->addCollimatedRadiationSource(direction);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::addCollimatedRadiationSource): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::addCollimatedRadiationSource): Unknown error adding collimated radiation source with vec3.");
            return 0;
        }
    }
    
    PYHELIOS_API unsigned int addCollimatedRadiationSourceSpherical(RadiationModel* radiation_model, float radius, float elevation, float azimuth) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return 0;
            }
            helios::SphericalCoord direction(radius, elevation, azimuth);
            return radiation_model->addCollimatedRadiationSource(direction);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::addCollimatedRadiationSource): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::addCollimatedRadiationSource): Unknown error adding collimated radiation source with spherical coordinates.");
            return 0;
        }
    }
    
    PYHELIOS_API unsigned int addSphereRadiationSource(RadiationModel* radiation_model, float x, float y, float z, float radius) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return 0;
            }
            helios::vec3 position(x, y, z);
            return radiation_model->addSphereRadiationSource(position, radius);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::addSphereRadiationSource): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::addSphereRadiationSource): Unknown error adding sphere radiation source.");
            return 0;
        }
    }
    
    PYHELIOS_API unsigned int addSunSphereRadiationSource(RadiationModel* radiation_model, float radius, float zenith, float azimuth, float position_scaling, float angular_width, float flux_scaling) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return 0;
            }
            helios::SphericalCoord sun_direction(radius, zenith, azimuth);
            return radiation_model->addSunSphereRadiationSource(sun_direction);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::addSunSphereRadiationSource): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::addSunSphereRadiationSource): Unknown error adding sun sphere radiation source.");
            return 0;
        }
    }
    
    PYHELIOS_API void setDirectRayCount(RadiationModel* radiation_model, const char* label, size_t count) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            radiation_model->setDirectRayCount(std::string(label), count);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setDirectRayCount): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setDirectRayCount): Unknown error setting direct ray count.");
        }
    }
    
    PYHELIOS_API void setDiffuseRayCount(RadiationModel* radiation_model, const char* label, size_t count) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            radiation_model->setDiffuseRayCount(std::string(label), count);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setDiffuseRayCount): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setDiffuseRayCount): Unknown error setting diffuse ray count.");
        }
    }
    
    PYHELIOS_API void setDiffuseRadiationFlux(RadiationModel* radiation_model, const char* label, float flux) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            radiation_model->setDiffuseRadiationFlux(std::string(label), flux);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setDiffuseRadiationFlux): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setDiffuseRadiationFlux): Unknown error setting diffuse radiation flux.");
        }
    }
    
    PYHELIOS_API void setSourceFlux(RadiationModel* radiation_model, unsigned int source_id, const char* label, float flux) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            radiation_model->setSourceFlux(source_id, std::string(label), flux);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setSourceFlux): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setSourceFlux): Unknown error setting source flux.");
        }
    }
    
    PYHELIOS_API void setSourceFluxMultiple(RadiationModel* radiation_model, unsigned int* source_ids, size_t count, const char* label, float flux) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!source_ids || !label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameters are null");
                return;
            }
            std::vector<unsigned int> id_vector(source_ids, source_ids + count);
            radiation_model->setSourceFlux(id_vector, std::string(label), flux);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setSourceFlux): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setSourceFlux): Unknown error setting multiple source flux.");
        }
    }
    
    PYHELIOS_API float getSourceFlux(RadiationModel* radiation_model, unsigned int source_id, const char* label) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return 0.0f;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return 0.0f;
            }
            return radiation_model->getSourceFlux(source_id, std::string(label));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::getSourceFlux): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::getSourceFlux): Unknown error getting source flux.");
            return 0.0f;
        }
    }
    
    PYHELIOS_API void setScatteringDepth(RadiationModel* radiation_model, const char* label, unsigned int depth) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            radiation_model->setScatteringDepth(std::string(label), depth);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setScatteringDepth): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setScatteringDepth): Unknown error setting scattering depth.");
        }
    }
    
    PYHELIOS_API void setMinScatterEnergy(RadiationModel* radiation_model, const char* label, float energy) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            radiation_model->setMinScatterEnergy(std::string(label), energy);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setMinScatterEnergy): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setMinScatterEnergy): Unknown error setting min scatter energy.");
        }
    }
    
    PYHELIOS_API void disableEmission(RadiationModel* radiation_model, const char* label) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            radiation_model->disableEmission(std::string(label));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::disableEmission): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::disableEmission): Unknown error disabling emission.");
        }
    }
    
    PYHELIOS_API void enableEmission(RadiationModel* radiation_model, const char* label) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            radiation_model->enableEmission(std::string(label));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::enableEmission): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::enableEmission): Unknown error enabling emission.");
        }
    }
    
    PYHELIOS_API void updateRadiationGeometry(RadiationModel* radiation_model) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            radiation_model->updateGeometry();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::updateGeometry): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::updateGeometry): Unknown error updating geometry.");
        }
    }
    
    PYHELIOS_API void updateRadiationGeometryUUIDs(RadiationModel* radiation_model, unsigned int* uuids, size_t count) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null");
                return;
            }
            std::vector<unsigned int> uuid_vector(uuids, uuids + count);
            radiation_model->updateGeometry(uuid_vector);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::updateGeometry): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::updateGeometry): Unknown error updating specific geometry.");
        }
    }
    
    PYHELIOS_API void runRadiationBand(RadiationModel* radiation_model, const char* label) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            radiation_model->runBand(std::string(label));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::runBand): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::runBand): Unknown error running radiation band.");
        }
    }
    
    PYHELIOS_API void runRadiationBandMultiple(RadiationModel* radiation_model, const char** labels, size_t count) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!labels) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Labels array is null");
                return;
            }
            std::vector<std::string> label_vector;
            for (size_t i = 0; i < count; i++) {
                if (labels[i]) {
                    label_vector.push_back(std::string(labels[i]));
                }
            }
            radiation_model->runBand(label_vector);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::runBand): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::runBand): Unknown error running multiple radiation bands.");
        }
    }
    
    PYHELIOS_API float* getTotalAbsorbedFlux(RadiationModel* radiation_model, size_t* size) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                if (size) *size = 0;
                return nullptr;
            }
            if (!size) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Size pointer is null");
                return nullptr;
            }
            
            std::vector<float> flux_data = radiation_model->getTotalAbsorbedFlux();

            // Allocate static buffer for flux data
            static thread_local std::vector<float> flux_buffer;
            flux_buffer = flux_data;
            *size = flux_buffer.size();
            return flux_buffer.data();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::getTotalAbsorbedFlux): ") + e.what());
            if (size) *size = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::getTotalAbsorbedFlux): Unknown error getting absorbed flux.");
            if (size) *size = 0;
            return nullptr;
        }
    }

    //=========================================================================
    // Diffuse Radiation Functions
    //=========================================================================

    PYHELIOS_API void setDiffuseRadiationExtinctionCoeffVec3(RadiationModel* radiation_model, const char* label,
                                                             float K, float peak_dir_x, float peak_dir_y, float peak_dir_z) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }

            helios::vec3 peak_direction(peak_dir_x, peak_dir_y, peak_dir_z);
            radiation_model->setDiffuseRadiationExtinctionCoeff(std::string(label), K, peak_direction);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setDiffuseRadiationExtinctionCoeff): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setDiffuseRadiationExtinctionCoeff): Unknown error setting extinction coefficient.");
        }
    }

    PYHELIOS_API void setDiffuseRadiationExtinctionCoeffSpherical(RadiationModel* radiation_model, const char* label,
                                                                  float K, float radius, float elevation, float azimuth) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }

            helios::SphericalCoord peak_direction = helios::make_SphericalCoord(radius, elevation, azimuth);
            radiation_model->setDiffuseRadiationExtinctionCoeff(std::string(label), K, peak_direction);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setDiffuseRadiationExtinctionCoeff): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setDiffuseRadiationExtinctionCoeff): Unknown error setting extinction coefficient.");
        }
    }

    PYHELIOS_API float getDiffuseFlux(RadiationModel* radiation_model, const char* band_label) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return 0.0f;
            }
            if (!band_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Band label is null");
                return 0.0f;
            }

            return radiation_model->getDiffuseFlux(std::string(band_label));

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::getDiffuseFlux): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::getDiffuseFlux): Unknown error getting diffuse flux.");
            return 0.0f;
        }
    }

    PYHELIOS_API void setDiffuseSpectrum(RadiationModel* radiation_model, const char* band_label,
                                         const char* spectrum_label) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!spectrum_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Spectrum label is null");
                return;
            }

            // Note: band_label parameter is kept for API compatibility but ignored.
            // The C++ API applies the spectrum to ALL bands, not specific bands.
            radiation_model->setDiffuseSpectrum(std::string(spectrum_label));

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setDiffuseSpectrum): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setDiffuseSpectrum): Unknown error setting diffuse spectrum.");
        }
    }

    PYHELIOS_API void setDiffuseSpectrumMultiple(RadiationModel* radiation_model,
                                                 const char** band_labels, size_t band_count,
                                                 const char* spectrum_label) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!spectrum_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Spectrum label is null");
                return;
            }

            // Note: band_labels parameter is kept for API compatibility but ignored.
            // The C++ API applies the spectrum to ALL bands, not specific bands.
            radiation_model->setDiffuseSpectrum(std::string(spectrum_label));

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setDiffuseSpectrum): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setDiffuseSpectrum): Unknown error setting diffuse spectrum.");
        }
    }

    PYHELIOS_API void setDiffuseSpectrumIntegralAll(RadiationModel* radiation_model, float spectrum_integral) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }

            radiation_model->setDiffuseSpectrumIntegral(spectrum_integral);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setDiffuseSpectrumIntegral): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setDiffuseSpectrumIntegral): Unknown error setting diffuse spectrum integral.");
        }
    }

    PYHELIOS_API void setDiffuseSpectrumIntegralAllRange(RadiationModel* radiation_model, float spectrum_integral,
                                                         float wavelength_min, float wavelength_max) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }

            radiation_model->setDiffuseSpectrumIntegral(spectrum_integral, wavelength_min, wavelength_max);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setDiffuseSpectrumIntegral): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setDiffuseSpectrumIntegral): Unknown error setting diffuse spectrum integral with range.");
        }
    }

    PYHELIOS_API void setDiffuseSpectrumIntegralBand(RadiationModel* radiation_model, const char* band_label,
                                                     float spectrum_integral) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!band_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Band label is null");
                return;
            }

            radiation_model->setDiffuseSpectrumIntegral(std::string(band_label), spectrum_integral);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setDiffuseSpectrumIntegral): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setDiffuseSpectrumIntegral): Unknown error setting diffuse spectrum integral for band.");
        }
    }

    PYHELIOS_API void setDiffuseSpectrumIntegralBandRange(RadiationModel* radiation_model, const char* band_label,
                                                          float spectrum_integral,
                                                          float wavelength_min, float wavelength_max) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!band_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Band label is null");
                return;
            }

            radiation_model->setDiffuseSpectrumIntegral(std::string(band_label), spectrum_integral,
                                                       wavelength_min, wavelength_max);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setDiffuseSpectrumIntegral): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setDiffuseSpectrumIntegral): Unknown error setting diffuse spectrum integral for band with range.");
        }
    }

    //=========================================================================
    // Band Query Functions
    //=========================================================================

    PYHELIOS_API int doesBandExist(RadiationModel* radiation_model, const char* label) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return -1;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return -1;
            }

            bool exists = radiation_model->doesBandExist(std::string(label));
            return exists ? 1 : 0;

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::doesBandExist): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::doesBandExist): Unknown error checking band existence.");
            return -1;
        }
    }

    //=========================================================================
    // Source Management Functions
    //=========================================================================

    PYHELIOS_API void deleteRadiationSource(RadiationModel* radiation_model, unsigned int source_id) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }

            radiation_model->deleteRadiationSource(source_id);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::deleteRadiationSource): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::deleteRadiationSource): Unknown error deleting radiation source.");
        }
    }

    PYHELIOS_API void getSourcePosition(RadiationModel* radiation_model, unsigned int source_id, float* position) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!position) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Position array pointer is null");
                return;
            }

            helios::vec3 pos = radiation_model->getSourcePosition(source_id);
            position[0] = pos.x;
            position[1] = pos.y;
            position[2] = pos.z;

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::getSourcePosition): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::getSourcePosition): Unknown error getting source position.");
        }
    }

    PYHELIOS_API void setSourcePositionVec3(RadiationModel* radiation_model, unsigned int source_id,
                                           float x, float y, float z) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }

            helios::vec3 position(x, y, z);
            radiation_model->setSourcePosition(source_id, position);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setSourcePosition): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setSourcePosition): Unknown error setting source position.");
        }
    }

    PYHELIOS_API void setSourcePositionSpherical(RadiationModel* radiation_model, unsigned int source_id,
                                                 float radius, float elevation, float azimuth) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }

            helios::SphericalCoord position = helios::make_SphericalCoord(radius, elevation, azimuth);
            radiation_model->setSourcePosition(source_id, position);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setSourcePosition): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setSourcePosition): Unknown error setting source position.");
        }
    }

    PYHELIOS_API unsigned int addRectangleRadiationSource(RadiationModel* radiation_model,
                                                         float position_x, float position_y, float position_z,
                                                         float size_x, float size_y,
                                                         float rotation_x, float rotation_y, float rotation_z) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return 0;
            }

            helios::vec3 position(position_x, position_y, position_z);
            helios::vec2 size(size_x, size_y);
            helios::vec3 rotation(rotation_x, rotation_y, rotation_z);
            return radiation_model->addRectangleRadiationSource(position, size, rotation);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::addRectangleRadiationSource): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::addRectangleRadiationSource): Unknown error adding rectangle source.");
            return 0;
        }
    }

    PYHELIOS_API unsigned int addDiskRadiationSource(RadiationModel* radiation_model,
                                                    float position_x, float position_y, float position_z,
                                                    float radius,
                                                    float rotation_x, float rotation_y, float rotation_z) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return 0;
            }

            helios::vec3 position(position_x, position_y, position_z);
            helios::vec3 rotation(rotation_x, rotation_y, rotation_z);
            return radiation_model->addDiskRadiationSource(position, radius, rotation);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::addDiskRadiationSource): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::addDiskRadiationSource): Unknown error adding disk source.");
            return 0;
        }
    }

    //=========================================================================
    // Source Spectrum Management Functions
    //=========================================================================

    PYHELIOS_API void setSourceSpectrum(RadiationModel* radiation_model, unsigned int source_id,
                                        const float* spectrum_data, size_t spectrum_size) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!spectrum_data) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Spectrum data pointer is null");
                return;
            }
            if (spectrum_size == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Spectrum size must be greater than zero");
                return;
            }

            // Convert flat array [w1,v1,w2,v2,...] to vector<vec2>
            std::vector<helios::vec2> spectrum_vec;
            spectrum_vec.reserve(spectrum_size);
            for (size_t i = 0; i < spectrum_size; i++) {
                spectrum_vec.emplace_back(spectrum_data[i*2], spectrum_data[i*2+1]);
            }

            radiation_model->setSourceSpectrum(source_id, spectrum_vec);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setSourceSpectrum): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setSourceSpectrum): Unknown error setting source spectrum.");
        }
    }

    PYHELIOS_API void setSourceSpectrumMultiple(RadiationModel* radiation_model,
                                                const unsigned int* source_ids, size_t source_count,
                                                const float* spectrum_data, size_t spectrum_size) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!source_ids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Source IDs pointer is null");
                return;
            }
            if (!spectrum_data) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Spectrum data pointer is null");
                return;
            }

            // Convert arrays to vectors
            std::vector<uint> source_vec(source_ids, source_ids + source_count);

            std::vector<helios::vec2> spectrum_vec;
            spectrum_vec.reserve(spectrum_size);
            for (size_t i = 0; i < spectrum_size; i++) {
                spectrum_vec.emplace_back(spectrum_data[i*2], spectrum_data[i*2+1]);
            }

            radiation_model->setSourceSpectrum(source_vec, spectrum_vec);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setSourceSpectrum): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setSourceSpectrum): Unknown error setting source spectrum for multiple sources.");
        }
    }

    PYHELIOS_API void setSourceSpectrumLabel(RadiationModel* radiation_model, unsigned int source_id,
                                             const char* spectrum_label) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!spectrum_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Spectrum label is null");
                return;
            }

            radiation_model->setSourceSpectrum(source_id, std::string(spectrum_label));

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setSourceSpectrum): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setSourceSpectrum): Unknown error setting source spectrum from label.");
        }
    }

    PYHELIOS_API void setSourceSpectrumLabelMultiple(RadiationModel* radiation_model,
                                                     const unsigned int* source_ids, size_t source_count,
                                                     const char* spectrum_label) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!source_ids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Source IDs pointer is null");
                return;
            }
            if (!spectrum_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Spectrum label is null");
                return;
            }

            std::vector<uint> source_vec(source_ids, source_ids + source_count);
            radiation_model->setSourceSpectrum(source_vec, std::string(spectrum_label));

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setSourceSpectrum): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setSourceSpectrum): Unknown error setting source spectrum from label for multiple sources.");
        }
    }

    PYHELIOS_API void setSourceSpectrumIntegral(RadiationModel* radiation_model, unsigned int source_id,
                                                float source_integral) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }

            radiation_model->setSourceSpectrumIntegral(source_id, source_integral);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setSourceSpectrumIntegral): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setSourceSpectrumIntegral): Unknown error setting source spectrum integral.");
        }
    }

    PYHELIOS_API void setSourceSpectrumIntegralRange(RadiationModel* radiation_model, unsigned int source_id,
                                                     float source_integral, float wavelength_min, float wavelength_max) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }

            radiation_model->setSourceSpectrumIntegral(source_id, source_integral, wavelength_min, wavelength_max);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setSourceSpectrumIntegral): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setSourceSpectrumIntegral): Unknown error setting source spectrum integral with range.");
        }
    }

    //=========================================================================
    // Spectrum Integration Functions
    //=========================================================================

    PYHELIOS_API float integrateSpectrum(RadiationModel* radiation_model,
                                         const float* object_spectrum, size_t spectrum_size) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return 0.0f;
            }
            if (!object_spectrum) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Spectrum data pointer is null");
                return 0.0f;
            }

            // Convert flat array to vector<vec2>
            std::vector<helios::vec2> spectrum_vec;
            spectrum_vec.reserve(spectrum_size);
            for (size_t i = 0; i < spectrum_size; i++) {
                spectrum_vec.emplace_back(object_spectrum[i*2], object_spectrum[i*2+1]);
            }

            return radiation_model->integrateSpectrum(spectrum_vec);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::integrateSpectrum): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::integrateSpectrum): Unknown error integrating spectrum.");
            return 0.0f;
        }
    }

    PYHELIOS_API float integrateSpectrumRange(RadiationModel* radiation_model,
                                              const float* object_spectrum, size_t spectrum_size,
                                              float wavelength_min, float wavelength_max) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return 0.0f;
            }
            if (!object_spectrum) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Spectrum data pointer is null");
                return 0.0f;
            }

            // Convert flat array to vector<vec2>
            std::vector<helios::vec2> spectrum_vec;
            spectrum_vec.reserve(spectrum_size);
            for (size_t i = 0; i < spectrum_size; i++) {
                spectrum_vec.emplace_back(object_spectrum[i*2], object_spectrum[i*2+1]);
            }

            return radiation_model->integrateSpectrum(spectrum_vec, wavelength_min, wavelength_max);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::integrateSpectrum): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::integrateSpectrum): Unknown error integrating spectrum with range.");
            return 0.0f;
        }
    }

    PYHELIOS_API float integrateSpectrumWithSource(RadiationModel* radiation_model, unsigned int source_id,
                                                   const float* object_spectrum, size_t spectrum_size,
                                                   float wavelength_min, float wavelength_max) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return 0.0f;
            }
            if (!object_spectrum) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Spectrum data pointer is null");
                return 0.0f;
            }

            // Convert flat array to vector<vec2>
            std::vector<helios::vec2> spectrum_vec;
            spectrum_vec.reserve(spectrum_size);
            for (size_t i = 0; i < spectrum_size; i++) {
                spectrum_vec.emplace_back(object_spectrum[i*2], object_spectrum[i*2+1]);
            }

            return radiation_model->integrateSpectrum(source_id, spectrum_vec, wavelength_min, wavelength_max);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::integrateSpectrum): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::integrateSpectrum): Unknown error integrating spectrum with source.");
            return 0.0f;
        }
    }

    PYHELIOS_API float integrateSpectrumWithCamera(RadiationModel* radiation_model,
                                                   const float* object_spectrum, size_t object_spectrum_size,
                                                   const float* camera_spectrum, size_t camera_spectrum_size) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return 0.0f;
            }
            if (!object_spectrum || !camera_spectrum) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Spectrum data pointer is null");
                return 0.0f;
            }

            // Convert flat arrays to vector<vec2>
            std::vector<helios::vec2> object_vec;
            object_vec.reserve(object_spectrum_size);
            for (size_t i = 0; i < object_spectrum_size; i++) {
                object_vec.emplace_back(object_spectrum[i*2], object_spectrum[i*2+1]);
            }

            std::vector<helios::vec2> camera_vec;
            camera_vec.reserve(camera_spectrum_size);
            for (size_t i = 0; i < camera_spectrum_size; i++) {
                camera_vec.emplace_back(camera_spectrum[i*2], camera_spectrum[i*2+1]);
            }

            return radiation_model->integrateSpectrum(object_vec, camera_vec);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::integrateSpectrum): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::integrateSpectrum): Unknown error integrating spectrum with camera.");
            return 0.0f;
        }
    }

    PYHELIOS_API float integrateSpectrumWithSourceAndCamera(RadiationModel* radiation_model, unsigned int source_id,
                                                            const float* object_spectrum, size_t object_spectrum_size,
                                                            const float* camera_spectrum, size_t camera_spectrum_size) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return 0.0f;
            }
            if (!object_spectrum || !camera_spectrum) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Spectrum data pointer is null");
                return 0.0f;
            }

            // Convert flat arrays to vector<vec2>
            std::vector<helios::vec2> object_vec;
            object_vec.reserve(object_spectrum_size);
            for (size_t i = 0; i < object_spectrum_size; i++) {
                object_vec.emplace_back(object_spectrum[i*2], object_spectrum[i*2+1]);
            }

            std::vector<helios::vec2> camera_vec;
            camera_vec.reserve(camera_spectrum_size);
            for (size_t i = 0; i < camera_spectrum_size; i++) {
                camera_vec.emplace_back(camera_spectrum[i*2], camera_spectrum[i*2+1]);
            }

            return radiation_model->integrateSpectrum(source_id, object_vec, camera_vec);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::integrateSpectrum): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::integrateSpectrum): Unknown error integrating spectrum with source and camera.");
            return 0.0f;
        }
    }

    PYHELIOS_API float integrateSourceSpectrum(RadiationModel* radiation_model, unsigned int source_id,
                                               float wavelength_min, float wavelength_max) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return 0.0f;
            }

            return radiation_model->integrateSourceSpectrum(source_id, wavelength_min, wavelength_max);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::integrateSourceSpectrum): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::integrateSourceSpectrum): Unknown error integrating source spectrum.");
            return 0.0f;
        }
    }

    //=========================================================================
    // Spectral Interpolation Functions
    //=========================================================================

    PYHELIOS_API void interpolateSpectrumFromPrimitiveData(RadiationModel* radiation_model,
                                                           const unsigned int* primitive_uuids, size_t uuid_count,
                                                           const char** spectra_labels, size_t spectra_count,
                                                           const float* values, size_t value_count,
                                                           const char* primitive_data_query_label,
                                                           const char* primitive_data_radprop_label) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!primitive_uuids || !spectra_labels || !values) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required array parameter is null");
                return;
            }
            if (!primitive_data_query_label || !primitive_data_radprop_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required label parameter is null");
                return;
            }
            if (spectra_count != value_count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Spectra count must match values count");
                return;
            }

            // Convert arrays to vectors
            std::vector<uint> uuid_vec(primitive_uuids, primitive_uuids + uuid_count);

            std::vector<std::string> spectra_vec;
            spectra_vec.reserve(spectra_count);
            for (size_t i = 0; i < spectra_count; i++) {
                if (spectra_labels[i]) {
                    spectra_vec.push_back(std::string(spectra_labels[i]));
                }
            }

            std::vector<float> values_vec(values, values + value_count);

            radiation_model->interpolateSpectrumFromPrimitiveData(uuid_vec, spectra_vec, values_vec,
                                                                 std::string(primitive_data_query_label),
                                                                 std::string(primitive_data_radprop_label));

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::interpolateSpectrumFromPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::interpolateSpectrumFromPrimitiveData): Unknown error interpolating spectrum.");
        }
    }

    PYHELIOS_API void interpolateSpectrumFromObjectData(RadiationModel* radiation_model,
                                                        const unsigned int* object_ids, size_t object_count,
                                                        const char** spectra_labels, size_t spectra_count,
                                                        const float* values, size_t value_count,
                                                        const char* object_data_query_label,
                                                        const char* primitive_data_radprop_label) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!object_ids || !spectra_labels || !values) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required array parameter is null");
                return;
            }
            if (!object_data_query_label || !primitive_data_radprop_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required label parameter is null");
                return;
            }
            if (spectra_count != value_count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Spectra count must match values count");
                return;
            }

            // Convert arrays to vectors
            std::vector<uint> object_vec(object_ids, object_ids + object_count);

            std::vector<std::string> spectra_vec;
            spectra_vec.reserve(spectra_count);
            for (size_t i = 0; i < spectra_count; i++) {
                if (spectra_labels[i]) {
                    spectra_vec.push_back(std::string(spectra_labels[i]));
                }
            }

            std::vector<float> values_vec(values, values + value_count);

            radiation_model->interpolateSpectrumFromObjectData(object_vec, spectra_vec, values_vec,
                                                              std::string(object_data_query_label),
                                                              std::string(primitive_data_radprop_label));

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::interpolateSpectrumFromObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::interpolateSpectrumFromObjectData): Unknown error interpolating spectrum.");
        }
    }

    //=========================================================================
    // Spectral Manipulation Functions
    //=========================================================================

    PYHELIOS_API void scaleSpectrumToNew(RadiationModel* radiation_model, const char* existing_label,
                                         const char* new_label, float scale_factor) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!existing_label || !new_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }

            radiation_model->scaleSpectrum(std::string(existing_label), std::string(new_label), scale_factor);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::scaleSpectrum): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::scaleSpectrum): Unknown error scaling spectrum.");
        }
    }

    PYHELIOS_API void scaleSpectrumInPlace(RadiationModel* radiation_model, const char* label,
                                           float scale_factor) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }

            radiation_model->scaleSpectrum(std::string(label), scale_factor);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::scaleSpectrum): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::scaleSpectrum): Unknown error scaling spectrum in-place.");
        }
    }

    PYHELIOS_API void scaleSpectrumRandomly(RadiationModel* radiation_model, const char* existing_label,
                                            const char* new_label, float min_scale, float max_scale) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!existing_label || !new_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }

            radiation_model->scaleSpectrumRandomly(std::string(existing_label), std::string(new_label),
                                                  min_scale, max_scale);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::scaleSpectrumRandomly): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::scaleSpectrumRandomly): Unknown error scaling spectrum randomly.");
        }
    }

    PYHELIOS_API void blendSpectra(RadiationModel* radiation_model, const char* new_label,
                                   const char** spectrum_labels, size_t label_count,
                                   const float* weights) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!new_label || !spectrum_labels || !weights) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required parameter is null");
                return;
            }

            // Convert arrays to vectors
            std::vector<std::string> label_vec;
            label_vec.reserve(label_count);
            for (size_t i = 0; i < label_count; i++) {
                if (spectrum_labels[i]) {
                    label_vec.push_back(std::string(spectrum_labels[i]));
                }
            }

            std::vector<float> weight_vec(weights, weights + label_count);

            radiation_model->blendSpectra(std::string(new_label), label_vec, weight_vec);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::blendSpectra): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::blendSpectra): Unknown error blending spectra.");
        }
    }

    PYHELIOS_API void blendSpectraRandomly(RadiationModel* radiation_model, const char* new_label,
                                           const char** spectrum_labels, size_t label_count) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!new_label || !spectrum_labels) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required parameter is null");
                return;
            }

            // Convert array to vector
            std::vector<std::string> label_vec;
            label_vec.reserve(label_count);
            for (size_t i = 0; i < label_count; i++) {
                if (spectrum_labels[i]) {
                    label_vec.push_back(std::string(spectrum_labels[i]));
                }
            }

            radiation_model->blendSpectraRandomly(std::string(new_label), label_vec);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::blendSpectraRandomly): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::blendSpectraRandomly): Unknown error blending spectra randomly.");
        }
    }

    //=========================================================================
    // Advanced Simulation Functions
    //=========================================================================

    PYHELIOS_API float getSkyEnergy(RadiationModel* radiation_model) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return 0.0f;
            }

            return radiation_model->getSkyEnergy();

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::getSkyEnergy): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::getSkyEnergy): Unknown error getting sky energy.");
            return 0.0f;
        }
    }

    PYHELIOS_API float calculateGtheta(RadiationModel* radiation_model, helios::Context* context,
                                       float view_x, float view_y, float view_z) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return 0.0f;
            }
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0.0f;
            }

            helios::vec3 view_direction(view_x, view_y, view_z);
            return radiation_model->calculateGtheta(context, view_direction);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::calculateGtheta): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::calculateGtheta): Unknown error calculating G-function.");
            return 0.0f;
        }
    }

    PYHELIOS_API void radiationOptionalOutputPrimitiveData(RadiationModel* radiation_model, const char* label) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }

            radiation_model->optionalOutputPrimitiveData(label);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::optionalOutputPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::optionalOutputPrimitiveData): Unknown error enabling optional output.");
        }
    }

    PYHELIOS_API void enforcePeriodicBoundary(RadiationModel* radiation_model, const char* boundary) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!boundary) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Boundary specification is null");
                return;
            }

            radiation_model->enforcePeriodicBoundary(std::string(boundary));

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::enforcePeriodicBoundary): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::enforcePeriodicBoundary): Unknown error enforcing periodic boundary.");
        }
    }

    //=========================================================================
    // Camera and Image Functions (v1.3.47)
    //=========================================================================
    
    // Thread-local storage for string returns
    static thread_local std::string camera_image_filename;
    
    PYHELIOS_API const char* writeCameraImage(RadiationModel* radiation_model, const char* camera, 
                                 const char** bands, size_t band_count,
                                 const char* imagefile_base, const char* image_path, 
                                 int frame, float flux_to_pixel_conversion) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return "";
            }
            if (!camera || !bands || !imagefile_base) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required parameters are null");
                return "";
            }
            
            // Convert C array to vector
            std::vector<std::string> band_vector;
            for (size_t i = 0; i < band_count; i++) {
                if (bands[i]) {
                    band_vector.push_back(std::string(bands[i]));
                }
            }
            
            std::string path = image_path ? std::string(image_path) : "./";
            
            camera_image_filename = radiation_model->writeCameraImage(
                std::string(camera), band_vector, std::string(imagefile_base), 
                path, frame, flux_to_pixel_conversion);
            
            return camera_image_filename.c_str();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::writeCameraImage): ") + e.what());
            return "";
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::writeCameraImage): Unknown error writing camera image.");
            return "";
        }
    }
    
    PYHELIOS_API const char* writeNormCameraImage(RadiationModel* radiation_model, const char* camera, 
                                     const char** bands, size_t band_count,
                                     const char* imagefile_base, const char* image_path, int frame) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return "";
            }
            if (!camera || !bands || !imagefile_base) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required parameters are null");
                return "";
            }
            
            // Convert C array to vector
            std::vector<std::string> band_vector;
            for (size_t i = 0; i < band_count; i++) {
                if (bands[i]) {
                    band_vector.push_back(std::string(bands[i]));
                }
            }
            
            std::string path = image_path ? std::string(image_path) : "./";
            
            camera_image_filename = radiation_model->writeNormCameraImage(
                std::string(camera), band_vector, std::string(imagefile_base), path, frame);
            
            return camera_image_filename.c_str();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::writeNormCameraImage): ") + e.what());
            return "";
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::writeNormCameraImage): Unknown error writing normalized camera image.");
            return "";
        }
    }
    
    PYHELIOS_API void writeCameraImageData(RadiationModel* radiation_model, const char* camera, const char* band,
                              const char* imagefile_base, const char* image_path, int frame) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera || !band || !imagefile_base) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required parameters are null");
                return;
            }
            
            std::string path = image_path ? std::string(image_path) : "./";
            
            radiation_model->writeCameraImageData(std::string(camera), std::string(band), 
                                                  std::string(imagefile_base), path, frame);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::writeCameraImageData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::writeCameraImageData): Unknown error writing camera image data.");
        }
    }

    // Bounding box functions - single primitive data label
    PYHELIOS_API void writeImageBoundingBoxes(RadiationModel* radiation_model, const char* camera_label,
                                 const char* primitive_data_label, unsigned int object_class_id,
                                 const char* image_file, const char* classes_txt_file, const char* image_path) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label || !primitive_data_label || !image_file) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required parameters are null");
                return;
            }
            
            std::string classes_file = classes_txt_file ? std::string(classes_txt_file) : "classes.txt";
            std::string path = image_path ? std::string(image_path) : "./";
            
            radiation_model->writeImageBoundingBoxes(std::string(camera_label), std::string(primitive_data_label),
                                                     object_class_id, std::string(image_file), classes_file, path);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::writeImageBoundingBoxes): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::writeImageBoundingBoxes): Unknown error writing bounding boxes.");
        }
    }

    // Bounding box functions - vector primitive data labels
    PYHELIOS_API void writeImageBoundingBoxesVector(RadiationModel* radiation_model, const char* camera_label,
                                       const char** primitive_data_labels, size_t label_count,
                                       unsigned int* object_class_ids, const char* image_file,
                                       const char* classes_txt_file, const char* image_path) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label || !primitive_data_labels || !object_class_ids || !image_file) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required parameters are null");
                return;
            }
            
            // Convert C arrays to vectors
            std::vector<std::string> label_vector;
            std::vector<unsigned int> class_id_vector;
            for (size_t i = 0; i < label_count; i++) {
                if (primitive_data_labels[i]) {
                    label_vector.push_back(std::string(primitive_data_labels[i]));
                    class_id_vector.push_back(object_class_ids[i]);
                }
            }
            
            std::string classes_file = classes_txt_file ? std::string(classes_txt_file) : "classes.txt";
            std::string path = image_path ? std::string(image_path) : "./";
            
            radiation_model->writeImageBoundingBoxes(std::string(camera_label), label_vector,
                                                     class_id_vector, std::string(image_file), classes_file, path);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::writeImageBoundingBoxesVector): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::writeImageBoundingBoxesVector): Unknown error writing vector bounding boxes.");
        }
    }

    // Bounding box functions - single object data label
    PYHELIOS_API void writeImageBoundingBoxes_ObjectData(RadiationModel* radiation_model, const char* camera_label,
                                            const char* object_data_label, unsigned int object_class_id,
                                            const char* image_file, const char* classes_txt_file, const char* image_path) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label || !object_data_label || !image_file) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required parameters are null");
                return;
            }
            
            std::string classes_file = classes_txt_file ? std::string(classes_txt_file) : "classes.txt";
            std::string path = image_path ? std::string(image_path) : "./";
            
            radiation_model->writeImageBoundingBoxes_ObjectData(std::string(camera_label), std::string(object_data_label),
                                                                object_class_id, std::string(image_file), classes_file, path);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::writeImageBoundingBoxes_ObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::writeImageBoundingBoxes_ObjectData): Unknown error writing object bounding boxes.");
        }
    }

    // Bounding box functions - vector object data labels
    PYHELIOS_API void writeImageBoundingBoxes_ObjectDataVector(RadiationModel* radiation_model, const char* camera_label,
                                                  const char** object_data_labels, size_t label_count,
                                                  unsigned int* object_class_ids, const char* image_file,
                                                  const char* classes_txt_file, const char* image_path) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label || !object_data_labels || !object_class_ids || !image_file) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required parameters are null");
                return;
            }
            
            // Convert C arrays to vectors
            std::vector<std::string> label_vector;
            std::vector<unsigned int> class_id_vector;
            for (size_t i = 0; i < label_count; i++) {
                if (object_data_labels[i]) {
                    label_vector.push_back(std::string(object_data_labels[i]));
                    class_id_vector.push_back(object_class_ids[i]);
                }
            }
            
            std::string classes_file = classes_txt_file ? std::string(classes_txt_file) : "classes.txt";
            std::string path = image_path ? std::string(image_path) : "./";
            
            radiation_model->writeImageBoundingBoxes_ObjectData(std::string(camera_label), label_vector,
                                                                class_id_vector, std::string(image_file), classes_file, path);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::writeImageBoundingBoxes_ObjectDataVector): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::writeImageBoundingBoxes_ObjectDataVector): Unknown error writing vector object bounding boxes.");
        }
    }

    // Segmentation mask functions - single primitive data label
    PYHELIOS_API void writeImageSegmentationMasks(RadiationModel* radiation_model, const char* camera_label,
                                     const char* primitive_data_label, unsigned int object_class_id,
                                     const char* json_filename, const char* image_file, int append_file) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label || !primitive_data_label || !json_filename || !image_file) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required parameters are null");
                return;
            }
            
            bool append = (append_file != 0);

            radiation_model->writeImageSegmentationMasks(std::string(camera_label), std::string(primitive_data_label),
                                                         object_class_id, std::string(json_filename),
                                                         std::string(image_file), {}, append);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::writeImageSegmentationMasks): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::writeImageSegmentationMasks): Unknown error writing segmentation masks.");
        }
    }

    // Segmentation mask functions - vector primitive data labels
    PYHELIOS_API void writeImageSegmentationMasksVector(RadiationModel* radiation_model, const char* camera_label,
                                           const char** primitive_data_labels, size_t label_count,
                                           unsigned int* object_class_ids, const char* json_filename,
                                           const char* image_file, int append_file) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label || !primitive_data_labels || !object_class_ids || !json_filename || !image_file) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required parameters are null");
                return;
            }
            
            // Convert C arrays to vectors
            std::vector<std::string> label_vector;
            std::vector<unsigned int> class_id_vector;
            for (size_t i = 0; i < label_count; i++) {
                if (primitive_data_labels[i]) {
                    label_vector.push_back(std::string(primitive_data_labels[i]));
                    class_id_vector.push_back(object_class_ids[i]);
                }
            }
            
            bool append = (append_file != 0);

            radiation_model->writeImageSegmentationMasks(std::string(camera_label), label_vector,
                                                         class_id_vector, std::string(json_filename),
                                                         std::string(image_file), {}, append);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::writeImageSegmentationMasksVector): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::writeImageSegmentationMasksVector): Unknown error writing vector segmentation masks.");
        }
    }

    // Segmentation mask functions - single object data label
    PYHELIOS_API void writeImageSegmentationMasks_ObjectData(RadiationModel* radiation_model, const char* camera_label,
                                                 const char* object_data_label, unsigned int object_class_id,
                                                 const char* json_filename, const char* image_file, int append_file) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label || !object_data_label || !json_filename || !image_file) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required parameters are null");
                return;
            }
            
            bool append = (append_file != 0);

            radiation_model->writeImageSegmentationMasks_ObjectData(std::string(camera_label), std::string(object_data_label),
                                                                    object_class_id, std::string(json_filename),
                                                                    std::string(image_file), {}, append);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::writeImageSegmentationMasks_ObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::writeImageSegmentationMasks_ObjectData): Unknown error writing object segmentation masks.");
        }
    }

    // Segmentation mask functions - vector object data labels
    PYHELIOS_API void writeImageSegmentationMasks_ObjectDataVector(RadiationModel* radiation_model, const char* camera_label,
                                                       const char** object_data_labels, size_t label_count,
                                                       unsigned int* object_class_ids, const char* json_filename,
                                                       const char* image_file, int append_file) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label || !object_data_labels || !object_class_ids || !json_filename || !image_file) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required parameters are null");
                return;
            }
            
            // Convert C arrays to vectors
            std::vector<std::string> label_vector;
            std::vector<unsigned int> class_id_vector;
            for (size_t i = 0; i < label_count; i++) {
                if (object_data_labels[i]) {
                    label_vector.push_back(std::string(object_data_labels[i]));
                    class_id_vector.push_back(object_class_ids[i]);
                }
            }
            
            bool append = (append_file != 0);

            radiation_model->writeImageSegmentationMasks_ObjectData(std::string(camera_label), label_vector,
                                                                    class_id_vector, std::string(json_filename),
                                                                    std::string(image_file), {}, append);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::writeImageSegmentationMasks_ObjectDataVector): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::writeImageSegmentationMasks_ObjectDataVector): Unknown error writing vector object segmentation masks.");
        }
    }

    // Auto-calibration function
    PYHELIOS_API const char* autoCalibrateCameraImage(RadiationModel* radiation_model, const char* camera_label,
                                         const char* red_band_label, const char* green_band_label, const char* blue_band_label,
                                         const char* output_file_path, int print_quality_report,
                                         int algorithm, const char* ccm_export_file_path) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return "";
            }
            if (!camera_label || !red_band_label || !green_band_label || !blue_band_label || !output_file_path) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required parameters are null");
                return "";
            }
            
            bool print_report = (print_quality_report != 0);
            
            // Map integer to ColorCorrectionAlgorithm enum
            RadiationModel::ColorCorrectionAlgorithm algo;
            switch (algorithm) {
                case 0: algo = RadiationModel::ColorCorrectionAlgorithm::DIAGONAL_ONLY; break;
                case 1: algo = RadiationModel::ColorCorrectionAlgorithm::MATRIX_3X3_AUTO; break;
                case 2: algo = RadiationModel::ColorCorrectionAlgorithm::MATRIX_3X3_FORCE; break;
                default: 
                    setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Invalid ColorCorrectionAlgorithm value");
                    return "";
            }
            
            std::string ccm_export = ccm_export_file_path ? std::string(ccm_export_file_path) : "";
            
            camera_image_filename = radiation_model->autoCalibrateCameraImage(
                std::string(camera_label), std::string(red_band_label), std::string(green_band_label),
                std::string(blue_band_label), std::string(output_file_path), print_report, algo, ccm_export);
            
            return camera_image_filename.c_str();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::autoCalibrateCameraImage): ") + e.what());
            return "";
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::autoCalibrateCameraImage): Unknown error auto-calibrating camera image.");
            return "";
        }
    }

    // Camera Creation Functions

    PYHELIOS_API void addRadiationCameraVec3(RadiationModel* radiation_model, const char* camera_label,
                                             const char** band_labels, size_t band_count,
                                             float position_x, float position_y, float position_z,
                                             float lookat_x, float lookat_y, float lookat_z,
                                             const float* camera_properties, unsigned int antialiasing_samples) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label || !band_labels || !camera_properties) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required parameters are null");
                return;
            }
            if (band_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "At least one band label is required");
                return;
            }

            // Convert C arrays to vectors
            std::vector<std::string> band_vector;
            for (size_t i = 0; i < band_count; i++) {
                if (band_labels[i]) {
                    band_vector.push_back(std::string(band_labels[i]));
                }
            }

            // Convert position and lookat parameters to vec3
            helios::vec3 position(position_x, position_y, position_z);
            helios::vec3 lookat(lookat_x, lookat_y, lookat_z);

            // Convert camera properties array to CameraProperties struct
            // Format supports both legacy (6 floats) and extended (10 floats) formats
            // Legacy: [resolution_x, resolution_y, focal_distance, lens_diameter, HFOV, FOV_aspect_ratio]
            // Extended v1.3.58: [+ lens_focal_length, sensor_width_mm, shutter_speed]
            // Extended v1.3.60: [+ camera_zoom] - 10 total elements
            CameraProperties props;
            props.camera_resolution = helios::make_int2((int)camera_properties[0], (int)camera_properties[1]);
            props.focal_plane_distance = camera_properties[2];
            props.lens_diameter = camera_properties[3];
            props.HFOV = camera_properties[4];
            props.FOV_aspect_ratio = camera_properties[5];

            // Extended properties (v1.3.58+) - use defaults then override if provided
            props.lens_focal_length = 0.05f;     // 50mm default
            props.sensor_width_mm = 35.0f;        // Full-frame default
            props.model = "generic";
            props.lens_make = "";
            props.lens_model = "";
            props.lens_specification = "";
            props.exposure = "auto";
            props.shutter_speed = 1.0f / 125.0f;  // 1/125s default
            props.white_balance = "auto";
            props.camera_zoom = 1.0f;             // No zoom default (v1.3.60+)

            // Override with extended properties if provided
            // Python's to_array() provides 10 elements
            props.lens_focal_length = camera_properties[6];
            props.sensor_width_mm = camera_properties[7];
            props.shutter_speed = camera_properties[8];
            props.camera_zoom = camera_properties[9];  // camera_zoom (v1.3.60+)

            radiation_model->addRadiationCamera(std::string(camera_label), band_vector, position, lookat, props, antialiasing_samples);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::addRadiationCamera): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::addRadiationCamera): Unknown error adding radiation camera.");
        }
    }

    PYHELIOS_API void addRadiationCameraSpherical(RadiationModel* radiation_model, const char* camera_label,
                                                  const char** band_labels, size_t band_count,
                                                  float position_x, float position_y, float position_z,
                                                  float radius, float elevation, float azimuth,
                                                  const float* camera_properties, unsigned int antialiasing_samples) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label || !band_labels || !camera_properties) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required parameters are null");
                return;
            }
            if (band_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "At least one band label is required");
                return;
            }

            // Convert C arrays to vectors
            std::vector<std::string> band_vector;
            for (size_t i = 0; i < band_count; i++) {
                if (band_labels[i]) {
                    band_vector.push_back(std::string(band_labels[i]));
                }
            }

            // Convert position to vec3 and viewing direction to SphericalCoord
            helios::vec3 position(position_x, position_y, position_z);
            helios::SphericalCoord viewing_direction = helios::make_SphericalCoord(radius, elevation, azimuth);

            // Convert camera properties array to CameraProperties struct
            // Format supports both legacy (6 floats) and extended (10 floats) formats
            // Legacy: [resolution_x, resolution_y, focal_distance, lens_diameter, HFOV, FOV_aspect_ratio]
            // Extended v1.3.58: [+ lens_focal_length, sensor_width_mm, shutter_speed]
            // Extended v1.3.60: [+ camera_zoom] - 10 total elements
            CameraProperties props;
            props.camera_resolution = helios::make_int2((int)camera_properties[0], (int)camera_properties[1]);
            props.focal_plane_distance = camera_properties[2];
            props.lens_diameter = camera_properties[3];
            props.HFOV = camera_properties[4];
            props.FOV_aspect_ratio = camera_properties[5];

            // Extended properties (v1.3.58+) - use defaults then override if provided
            props.lens_focal_length = 0.05f;     // 50mm default
            props.sensor_width_mm = 35.0f;        // Full-frame default
            props.model = "generic";
            props.lens_make = "";
            props.lens_model = "";
            props.lens_specification = "";
            props.exposure = "auto";
            props.shutter_speed = 1.0f / 125.0f;  // 1/125s default
            props.white_balance = "auto";
            props.camera_zoom = 1.0f;             // No zoom default (v1.3.60+)

            // Override with extended properties if provided
            // Python's to_array() provides 10 elements
            props.lens_focal_length = camera_properties[6];
            props.sensor_width_mm = camera_properties[7];
            props.shutter_speed = camera_properties[8];
            props.camera_zoom = camera_properties[9];  // camera_zoom (v1.3.60+)

            radiation_model->addRadiationCamera(std::string(camera_label), band_vector, position, viewing_direction, props, antialiasing_samples);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::addRadiationCamera): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::addRadiationCamera): Unknown error adding radiation camera.");
        }
    }

    //=========================================================================
    // SIF (Solar-Induced Fluorescence) Camera
    //=========================================================================

    PYHELIOS_API void addSIFCameraVec3(RadiationModel* radiation_model, const char* camera_label,
                                       const char** band_labels, size_t band_count,
                                       float position_x, float position_y, float position_z,
                                       float lookat_x, float lookat_y, float lookat_z,
                                       const float* camera_properties,
                                       float excitation_bin_width_nm, unsigned int excitation_scattering_depth,
                                       unsigned int antialiasing_samples) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label || !band_labels || !camera_properties) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required parameters are null");
                return;
            }
            if (band_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "At least one emission band label is required");
                return;
            }
            if (excitation_bin_width_nm <= 0.f) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "excitation_bin_width_nm must be > 0");
                return;
            }

            std::vector<std::string> band_vector;
            for (size_t i = 0; i < band_count; i++) {
                if (band_labels[i]) {
                    band_vector.push_back(std::string(band_labels[i]));
                }
            }

            helios::vec3 position(position_x, position_y, position_z);
            helios::vec3 lookat(lookat_x, lookat_y, lookat_z);

            SIFCameraProperties props = buildSIFCameraProperties(camera_properties,
                                                                 excitation_bin_width_nm,
                                                                 excitation_scattering_depth);

            radiation_model->addSIFCamera(std::string(camera_label), band_vector, position, lookat, props, antialiasing_samples);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::addSIFCamera): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::addSIFCamera): Unknown error adding SIF camera.");
        }
    }

    PYHELIOS_API void addSIFCameraSpherical(RadiationModel* radiation_model, const char* camera_label,
                                            const char** band_labels, size_t band_count,
                                            float position_x, float position_y, float position_z,
                                            float radius, float elevation, float azimuth,
                                            const float* camera_properties,
                                            float excitation_bin_width_nm, unsigned int excitation_scattering_depth,
                                            unsigned int antialiasing_samples) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label || !band_labels || !camera_properties) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required parameters are null");
                return;
            }
            if (band_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "At least one emission band label is required");
                return;
            }
            if (excitation_bin_width_nm <= 0.f) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "excitation_bin_width_nm must be > 0");
                return;
            }

            std::vector<std::string> band_vector;
            for (size_t i = 0; i < band_count; i++) {
                if (band_labels[i]) {
                    band_vector.push_back(std::string(band_labels[i]));
                }
            }

            helios::vec3 position(position_x, position_y, position_z);
            helios::SphericalCoord viewing_direction = helios::make_SphericalCoord(radius, elevation, azimuth);

            SIFCameraProperties props = buildSIFCameraProperties(camera_properties,
                                                                 excitation_bin_width_nm,
                                                                 excitation_scattering_depth);

            radiation_model->addSIFCamera(std::string(camera_label), band_vector, position, viewing_direction, props, antialiasing_samples);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::addSIFCamera): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::addSIFCamera): Unknown error adding SIF camera.");
        }
    }

    PYHELIOS_API int isSIFCamera(RadiationModel* radiation_model, const char* camera_label) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return 0;
            }
            if (!camera_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Camera label is null");
                return 0;
            }
            return radiation_model->isSIFCamera(std::string(camera_label)) ? 1 : 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::isSIFCamera): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::isSIFCamera): Unknown error.");
            return 0;
        }
    }

    //=========================================================================
    // Camera Management Functions
    //=========================================================================

    PYHELIOS_API void setRadiationCameraPosition(RadiationModel* radiation_model, const char* camera_label,
                                        float x, float y, float z) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Camera label is null");
                return;
            }

            helios::vec3 position(x, y, z);
            radiation_model->setCameraPosition(std::string(camera_label), position);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setCameraPosition): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setCameraPosition): Unknown error setting camera position.");
        }
    }

    PYHELIOS_API void getRadiationCameraPosition(RadiationModel* radiation_model, const char* camera_label,
                                        float* position) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Camera label is null");
                return;
            }
            if (!position) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Position array pointer is null");
                return;
            }

            helios::vec3 pos = radiation_model->getCameraPosition(std::string(camera_label));
            position[0] = pos.x;
            position[1] = pos.y;
            position[2] = pos.z;

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::getCameraPosition): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::getCameraPosition): Unknown error getting camera position.");
        }
    }

    PYHELIOS_API void setCameraLookat(RadiationModel* radiation_model, const char* camera_label,
                                      float x, float y, float z) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Camera label is null");
                return;
            }

            helios::vec3 lookat(x, y, z);
            radiation_model->setCameraLookat(std::string(camera_label), lookat);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setCameraLookat): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setCameraLookat): Unknown error setting camera lookat.");
        }
    }

    PYHELIOS_API void getCameraLookat(RadiationModel* radiation_model, const char* camera_label,
                                      float* lookat) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Camera label is null");
                return;
            }
            if (!lookat) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Lookat array pointer is null");
                return;
            }

            helios::vec3 lookat_vec = radiation_model->getCameraLookat(std::string(camera_label));
            lookat[0] = lookat_vec.x;
            lookat[1] = lookat_vec.y;
            lookat[2] = lookat_vec.z;

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::getCameraLookat): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::getCameraLookat): Unknown error getting camera lookat.");
        }
    }

    PYHELIOS_API void setCameraOrientationVec3(RadiationModel* radiation_model, const char* camera_label,
                                               float x, float y, float z) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Camera label is null");
                return;
            }

            helios::vec3 direction(x, y, z);
            radiation_model->setCameraOrientation(std::string(camera_label), direction);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setCameraOrientation): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setCameraOrientation): Unknown error setting camera orientation.");
        }
    }

    PYHELIOS_API void setCameraOrientationSpherical(RadiationModel* radiation_model, const char* camera_label,
                                                    float radius, float elevation, float azimuth) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Camera label is null");
                return;
            }

            helios::SphericalCoord direction = helios::make_SphericalCoord(radius, elevation, azimuth);
            radiation_model->setCameraOrientation(std::string(camera_label), direction);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setCameraOrientation): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setCameraOrientation): Unknown error setting camera orientation.");
        }
    }

    PYHELIOS_API void getCameraOrientation(RadiationModel* radiation_model, const char* camera_label,
                                           float* orientation) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Camera label is null");
                return;
            }
            if (!orientation) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Orientation array pointer is null");
                return;
            }

            helios::SphericalCoord orient = radiation_model->getCameraOrientation(std::string(camera_label));
            orientation[0] = orient.radius;
            orientation[1] = orient.elevation;
            orientation[2] = orient.azimuth;

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::getCameraOrientation): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::getCameraOrientation): Unknown error getting camera orientation.");
        }
    }

    PYHELIOS_API const char** getAllCameraLabels(RadiationModel* radiation_model, size_t* count) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }

            std::vector<std::string> labels = radiation_model->getAllCameraLabels();

            // Convert to static array of C strings for return
            static thread_local std::vector<std::string> static_labels;
            static thread_local std::vector<const char*> static_c_strings;

            static_labels = labels;
            static_c_strings.clear();
            static_c_strings.reserve(static_labels.size());

            for (const auto& label : static_labels) {
                static_c_strings.push_back(label.c_str());
            }

            *count = static_c_strings.size();
            return static_c_strings.data();

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::getAllCameraLabels): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::getAllCameraLabels): Unknown error getting camera labels.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API void setCameraSpectralResponse(RadiationModel* radiation_model, const char* camera_label,
                                                const char* band_label, const char* global_data) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label || !band_label || !global_data) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required parameter is null");
                return;
            }

            radiation_model->setCameraSpectralResponse(std::string(camera_label), std::string(band_label),
                                                      std::string(global_data));

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setCameraSpectralResponse): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setCameraSpectralResponse): Unknown error setting camera spectral response.");
        }
    }

    PYHELIOS_API void setCameraSpectralResponseFromLibrary(RadiationModel* radiation_model, const char* camera_label,
                                                           const char* camera_library_name) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label || !camera_library_name) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required parameter is null");
                return;
            }

            radiation_model->setCameraSpectralResponseFromLibrary(std::string(camera_label),
                                                                 std::string(camera_library_name));

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setCameraSpectralResponseFromLibrary): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setCameraSpectralResponseFromLibrary): Unknown error setting camera response from library.");
        }
    }

    PYHELIOS_API const float* getCameraPixelData(RadiationModel* radiation_model, const char* camera_label,
                                                 const char* band_label, size_t* size) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                if (size) *size = 0;
                return nullptr;
            }
            if (!camera_label || !band_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required parameter is null");
                if (size) *size = 0;
                return nullptr;
            }
            if (!size) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Size pointer is null");
                return nullptr;
            }

            std::vector<float> pixel_data = radiation_model->getCameraPixelData(std::string(camera_label),
                                                                                std::string(band_label));

            // Store in thread-local static buffer
            static thread_local std::vector<float> pixel_buffer;
            pixel_buffer = pixel_data;
            *size = pixel_buffer.size();
            return pixel_buffer.data();

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::getCameraPixelData): ") + e.what());
            if (size) *size = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::getCameraPixelData): Unknown error getting camera pixel data.");
            if (size) *size = 0;
            return nullptr;
        }
    }

    PYHELIOS_API void setCameraPixelData(RadiationModel* radiation_model, const char* camera_label,
                                         const char* band_label, const float* pixel_data, size_t size) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label || !band_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required parameter is null");
                return;
            }
            if (!pixel_data) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Pixel data pointer is null");
                return;
            }

            std::vector<float> pixel_vec(pixel_data, pixel_data + size);
            radiation_model->setCameraPixelData(std::string(camera_label), std::string(band_label), pixel_vec);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setCameraPixelData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setCameraPixelData): Unknown error setting camera pixel data.");
        }
    }

    //=========================================================================
    // Camera Library Functions (v1.3.58+)
    //=========================================================================

    PYHELIOS_API void addRadiationCameraFromLibrary(RadiationModel* radiation_model,
                                                     const char* camera_label,
                                                     const char* library_camera_label,
                                                     float position_x, float position_y, float position_z,
                                                     float lookat_x, float lookat_y, float lookat_z,
                                                     unsigned int antialiasing_samples) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label || !library_camera_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Camera label or library camera label is null");
                return;
            }

            helios::vec3 position(position_x, position_y, position_z);
            helios::vec3 lookat(lookat_x, lookat_y, lookat_z);

            radiation_model->addRadiationCameraFromLibrary(std::string(camera_label),
                                                          std::string(library_camera_label),
                                                          position, lookat, antialiasing_samples);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::addRadiationCameraFromLibrary): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::addRadiationCameraFromLibrary): Unknown error.");
        }
    }

    PYHELIOS_API void addRadiationCameraFromLibraryWithBands(RadiationModel* radiation_model,
                                                               const char* camera_label,
                                                               const char* library_camera_label,
                                                               float position_x, float position_y, float position_z,
                                                               float lookat_x, float lookat_y, float lookat_z,
                                                               unsigned int antialiasing_samples,
                                                               const char** band_labels, size_t band_count) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label || !library_camera_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Camera label or library camera label is null");
                return;
            }
            if (!band_labels && band_count > 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Band labels pointer is null but count is non-zero");
                return;
            }

            helios::vec3 position(position_x, position_y, position_z);
            helios::vec3 lookat(lookat_x, lookat_y, lookat_z);

            // Convert C array to vector
            std::vector<std::string> band_vector;
            for (size_t i = 0; i < band_count; i++) {
                if (band_labels[i]) {
                    band_vector.push_back(std::string(band_labels[i]));
                }
            }

            radiation_model->addRadiationCameraFromLibrary(std::string(camera_label),
                                                          std::string(library_camera_label),
                                                          position, lookat, antialiasing_samples,
                                                          band_vector);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::addRadiationCameraFromLibrary): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::addRadiationCameraFromLibrary): Unknown error.");
        }
    }

    PYHELIOS_API void updateCameraParameters(RadiationModel* radiation_model,
                                             const char* camera_label,
                                             const float* camera_properties) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Camera label is null");
                return;
            }
            if (!camera_properties) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Camera properties pointer is null");
                return;
            }

            // Convert camera properties array to CameraProperties struct
            // Same format as addRadiationCamera: 10 floats (v1.3.60+)
            CameraProperties props;
            props.camera_resolution = helios::make_int2((int)camera_properties[0], (int)camera_properties[1]);
            props.focal_plane_distance = camera_properties[2];
            props.lens_diameter = camera_properties[3];
            props.HFOV = camera_properties[4];
            props.FOV_aspect_ratio = camera_properties[5];
            props.lens_focal_length = camera_properties[6];
            props.sensor_width_mm = camera_properties[7];
            props.shutter_speed = camera_properties[8];
            props.camera_zoom = camera_properties[9];  // camera_zoom (v1.3.60+)

            // String fields use defaults (cannot be updated via this interface)
            props.model = "generic";
            props.lens_make = "";
            props.lens_model = "";
            props.lens_specification = "";
            props.exposure = "auto";
            props.white_balance = "auto";

            radiation_model->updateCameraParameters(std::string(camera_label), props);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::updateCameraParameters): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::updateCameraParameters): Unknown error.");
        }
    }

    PYHELIOS_API void enableCameraMetadata(RadiationModel* radiation_model,
                                           const char* camera_label) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Camera label is null");
                return;
            }

            radiation_model->enableCameraMetadata(std::string(camera_label));

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::enableCameraMetadata): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::enableCameraMetadata): Unknown error.");
        }
    }

    PYHELIOS_API void enableCameraMetadataMultiple(RadiationModel* radiation_model,
                                                    const char** camera_labels, size_t count) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_labels && count > 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Camera labels pointer is null but count is non-zero");
                return;
            }

            // Convert C array to vector
            std::vector<std::string> labels_vector;
            for (size_t i = 0; i < count; i++) {
                if (camera_labels[i]) {
                    labels_vector.push_back(std::string(camera_labels[i]));
                }
            }

            radiation_model->enableCameraMetadata(labels_vector);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::enableCameraMetadata): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::enableCameraMetadata): Unknown error.");
        }
    }


    //=============================================================================
    // EXR Image Export Functions (v1.3.66+)
    //=============================================================================

    PYHELIOS_API void writeCameraImageDataEXR(RadiationModel* radiation_model, const char* camera,
                                              const char* band, const char* imagefile_base,
                                              const char* image_path, int frame) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera || !band || !imagefile_base || !image_path) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required string parameters are null");
                return;
            }

            radiation_model->writeCameraImageDataEXR(std::string(camera), std::string(band),
                                                     std::string(imagefile_base), std::string(image_path), frame);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::writeCameraImageDataEXR): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::writeCameraImageDataEXR): Unknown error.");
        }
    }

    PYHELIOS_API void writeCameraImageDataEXRMultiple(RadiationModel* radiation_model, const char* camera,
                                                       const char** bands, size_t band_count,
                                                       const char* imagefile_base, const char* image_path, int frame) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera || !bands || !imagefile_base || !image_path) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required parameters are null");
                return;
            }

            std::vector<std::string> band_vector;
            band_vector.reserve(band_count);
            for (size_t i = 0; i < band_count; i++) {
                if (bands[i]) {
                    band_vector.push_back(std::string(bands[i]));
                }
            }

            radiation_model->writeCameraImageDataEXR(std::string(camera), band_vector,
                                                     std::string(imagefile_base), std::string(image_path), frame);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::writeCameraImageDataEXRMultiple): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::writeCameraImageDataEXRMultiple): Unknown error.");
        }
    }

    PYHELIOS_API void writeDepthImageData(RadiationModel* radiation_model, const char* camera_label,
                                          const char* imagefile_base, const char* image_path, int frame) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label || !imagefile_base || !image_path) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required string parameters are null");
                return;
            }

            radiation_model->writeDepthImageData(std::string(camera_label), std::string(imagefile_base),
                                                 std::string(image_path), frame);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::writeDepthImageData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::writeDepthImageData): Unknown error.");
        }
    }

    PYHELIOS_API void writeDepthImageDataEXR(RadiationModel* radiation_model, const char* camera_label,
                                             const char* imagefile_base, const char* image_path, int frame) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label || !imagefile_base || !image_path) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required string parameters are null");
                return;
            }

            radiation_model->writeDepthImageDataEXR(std::string(camera_label), std::string(imagefile_base),
                                                    std::string(image_path), frame);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::writeDepthImageDataEXR): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::writeDepthImageDataEXR): Unknown error.");
        }
    }

    PYHELIOS_API void writeNormDepthImage(RadiationModel* radiation_model, const char* camera_label,
                                          const char* imagefile_base, float max_depth,
                                          const char* image_path, int frame) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!camera_label || !imagefile_base || !image_path) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Required string parameters are null");
                return;
            }

            radiation_model->writeNormDepthImage(std::string(camera_label), std::string(imagefile_base),
                                                 max_depth, std::string(image_path), frame);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::writeNormDepthImage): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::writeNormDepthImage): Unknown error.");
        }
    }

    //=============================================================================
    // Backend Query Functions (v1.3.67+)
    //=============================================================================

    PYHELIOS_API const char* getBackendName(RadiationModel* radiation_model) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return nullptr;
            }

            static thread_local std::string static_result;
            static_result = radiation_model->getBackendName();
            return static_result.c_str();

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::getBackendName): ") + e.what());
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::getBackendName): Unknown error.");
            return nullptr;
        }
    }

    PYHELIOS_API int probeAnyGPUBackend() {
        try {
            clearError();
            return helios::probeAnyGPUBackend() ? 1 : 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (probeAnyGPUBackend): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (probeAnyGPUBackend): Unknown error.");
            return 0;
        }
    }

} //extern "C"

#endif //RADIATION_PLUGIN_AVAILABLE
