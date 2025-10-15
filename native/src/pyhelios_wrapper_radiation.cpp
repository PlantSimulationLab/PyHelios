// PyHelios C Interface - Radiation Functions  
// Provides OptiX-accelerated ray tracing and radiation modeling functions

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

extern "C" {
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
            static std::vector<float> flux_buffer;
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
            // Expected format: [resolution_x, resolution_y, focal_distance, lens_diameter, HFOV, FOV_aspect_ratio]
            CameraProperties props;
            props.camera_resolution = helios::make_int2((int)camera_properties[0], (int)camera_properties[1]);
            props.focal_plane_distance = camera_properties[2];
            props.lens_diameter = camera_properties[3];
            props.HFOV = camera_properties[4];
            props.FOV_aspect_ratio = camera_properties[5];

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
            // Expected format: [resolution_x, resolution_y, focal_distance, lens_diameter, HFOV, FOV_aspect_ratio]
            CameraProperties props;
            props.camera_resolution = helios::make_int2((int)camera_properties[0], (int)camera_properties[1]);
            props.focal_plane_distance = camera_properties[2];
            props.lens_diameter = camera_properties[3];
            props.HFOV = camera_properties[4];
            props.FOV_aspect_ratio = camera_properties[5];

            radiation_model->addRadiationCamera(std::string(camera_label), band_vector, position, viewing_direction, props, antialiasing_samples);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::addRadiationCamera): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::addRadiationCamera): Unknown error adding radiation camera.");
        }
    }


} //extern "C"

#endif //RADIATION_PLUGIN_AVAILABLE
