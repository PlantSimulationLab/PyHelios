/**
 * @file pyhelios_wrapper_radiation.h
 * @brief RadiationModel functions for PyHelios C wrapper
 * 
 * This header provides radiation modeling capabilities including
 * radiation bands, light sources, and simulation execution.
 */

#ifndef PYHELIOS_WRAPPER_RADIATION_H
#define PYHELIOS_WRAPPER_RADIATION_H

#include "pyhelios_wrapper_common.h"

// Forward declarations for RadiationModel interface
class RadiationModel;
namespace helios {
    class Context;
}

#ifdef __cplusplus
extern "C" {
#endif

//=============================================================================
// RadiationModel Functions
//=============================================================================

/**
 * @brief Create a new RadiationModel
 * @param context Pointer to the Helios context
 * @return Pointer to the created RadiationModel, or nullptr on error
 */
PYHELIOS_API RadiationModel* createRadiationModel(helios::Context* context);

/**
 * @brief Destroy a RadiationModel
 * @param radiation_model Pointer to the RadiationModel to destroy
 */
PYHELIOS_API void destroyRadiationModel(RadiationModel* radiation_model);

/**
 * @brief Disable RadiationModel status messages
 * @param radiation_model Pointer to the RadiationModel
 */
PYHELIOS_API void disableRadiationMessages(RadiationModel* radiation_model);

/**
 * @brief Enable RadiationModel status messages
 * @param radiation_model Pointer to the RadiationModel
 */
PYHELIOS_API void enableRadiationMessages(RadiationModel* radiation_model);

/**
 * @brief Add a radiation band
 * @param radiation_model Pointer to the RadiationModel
 * @param label Name/label for the radiation band
 */
PYHELIOS_API void addRadiationBand(RadiationModel* radiation_model, const char* label);

/**
 * @brief Add a radiation band with specified wavelength range
 * @param radiation_model Pointer to the RadiationModel
 * @param label Name/label for the radiation band
 * @param wavelength_min Minimum wavelength
 * @param wavelength_max Maximum wavelength
 */
PYHELIOS_API void addRadiationBandWithWavelengths(RadiationModel* radiation_model, const char* label, float wavelength_min, float wavelength_max);

/**
 * @brief Copy a radiation band
 * @param radiation_model Pointer to the RadiationModel
 * @param old_label Label of band to copy
 * @param new_label Label for new band
 */
PYHELIOS_API void copyRadiationBand(RadiationModel* radiation_model, const char* old_label, const char* new_label);

/**
 * @brief Copy a radiation band with new wavelength range
 * @param radiation_model Pointer to the RadiationModel
 * @param old_label Label of band to copy
 * @param new_label Label for new band
 * @param wavelength_min Minimum wavelength for new band
 * @param wavelength_max Maximum wavelength for new band
 */
PYHELIOS_API void copyRadiationBandWithWavelengths(RadiationModel* radiation_model, const char* old_label, const char* new_label,
                                                    float wavelength_min, float wavelength_max);

/**
 * @brief Add a collimated radiation source with default direction
 * @param radiation_model Pointer to the RadiationModel
 * @return Source ID
 */
PYHELIOS_API unsigned int addCollimatedRadiationSourceDefault(RadiationModel* radiation_model);

/**
 * @brief Add a collimated radiation source with vec3 direction
 * @param radiation_model Pointer to the RadiationModel
 * @param x X component of direction vector
 * @param y Y component of direction vector
 * @param z Z component of direction vector
 * @return Source ID
 */
PYHELIOS_API unsigned int addCollimatedRadiationSourceVec3(RadiationModel* radiation_model, float x, float y, float z);

/**
 * @brief Add a collimated radiation source with spherical coordinates
 * @param radiation_model Pointer to the RadiationModel
 * @param elevation Elevation angle in spherical coordinates
 * @param azimuth Azimuth angle in spherical coordinates
 * @param radius Radius in spherical coordinates
 * @return Source ID
 */
PYHELIOS_API unsigned int addCollimatedRadiationSourceSpherical(RadiationModel* radiation_model, float elevation, float azimuth, float radius);

/**
 * @brief Run radiation simulation for a specific band
 * @param radiation_model Pointer to the RadiationModel
 * @param label Name/label of the radiation band to run
 */
PYHELIOS_API void runBand(RadiationModel* radiation_model, const char* label);

//=============================================================================
// Diffuse Radiation Functions
//=============================================================================

/**
 * @brief Set diffuse radiation extinction coefficient (vec3 peak direction)
 * @param radiation_model Pointer to the RadiationModel
 * @param label Band label
 * @param K Extinction coefficient
 * @param peak_dir_x X component of peak direction
 * @param peak_dir_y Y component of peak direction
 * @param peak_dir_z Z component of peak direction
 */
PYHELIOS_API void setDiffuseRadiationExtinctionCoeffVec3(RadiationModel* radiation_model, const char* label,
                                                         float K, float peak_dir_x, float peak_dir_y, float peak_dir_z);

/**
 * @brief Set diffuse radiation extinction coefficient (spherical peak direction)
 * @param radiation_model Pointer to the RadiationModel
 * @param label Band label
 * @param K Extinction coefficient
 * @param radius Spherical radius
 * @param elevation Elevation angle
 * @param azimuth Azimuth angle
 */
PYHELIOS_API void setDiffuseRadiationExtinctionCoeffSpherical(RadiationModel* radiation_model, const char* label,
                                                              float K, float radius, float elevation, float azimuth);

/**
 * @brief Get diffuse flux for band
 * @param radiation_model Pointer to the RadiationModel
 * @param band_label Band label
 * @return Diffuse flux value
 */
PYHELIOS_API float getDiffuseFlux(RadiationModel* radiation_model, const char* band_label);

/**
 * @brief Set diffuse spectrum from global data label (single band)
 * @param radiation_model Pointer to the RadiationModel
 * @param band_label Band label
 * @param spectrum_label Spectrum global data label
 */
PYHELIOS_API void setDiffuseSpectrum(RadiationModel* radiation_model, const char* band_label,
                                     const char* spectrum_label);

/**
 * @brief Set diffuse spectrum from global data label (multiple bands)
 * @param radiation_model Pointer to the RadiationModel
 * @param band_labels Array of band labels
 * @param band_count Number of bands
 * @param spectrum_label Spectrum global data label
 */
PYHELIOS_API void setDiffuseSpectrumMultiple(RadiationModel* radiation_model,
                                             const char** band_labels, size_t band_count,
                                             const char* spectrum_label);

/**
 * @brief Set diffuse spectrum integral (all bands)
 * @param radiation_model Pointer to the RadiationModel
 * @param spectrum_integral Integral value
 */
PYHELIOS_API void setDiffuseSpectrumIntegralAll(RadiationModel* radiation_model, float spectrum_integral);

/**
 * @brief Set diffuse spectrum integral over wavelength range (all bands)
 * @param radiation_model Pointer to the RadiationModel
 * @param spectrum_integral Integral value
 * @param wavelength_min Minimum wavelength
 * @param wavelength_max Maximum wavelength
 */
PYHELIOS_API void setDiffuseSpectrumIntegralAllRange(RadiationModel* radiation_model, float spectrum_integral,
                                                     float wavelength_min, float wavelength_max);

/**
 * @brief Set diffuse spectrum integral for specific band
 * @param radiation_model Pointer to the RadiationModel
 * @param band_label Band label
 * @param spectrum_integral Integral value
 */
PYHELIOS_API void setDiffuseSpectrumIntegralBand(RadiationModel* radiation_model, const char* band_label,
                                                 float spectrum_integral);

/**
 * @brief Set diffuse spectrum integral over wavelength range for specific band
 * @param radiation_model Pointer to the RadiationModel
 * @param band_label Band label
 * @param spectrum_integral Integral value
 * @param wavelength_min Minimum wavelength
 * @param wavelength_max Maximum wavelength
 */
PYHELIOS_API void setDiffuseSpectrumIntegralBandRange(RadiationModel* radiation_model, const char* band_label,
                                                      float spectrum_integral,
                                                      float wavelength_min, float wavelength_max);

//=============================================================================
// Band Query Functions
//=============================================================================

/**
 * @brief Check if a radiation band exists
 * @param radiation_model Pointer to the RadiationModel
 * @param label Name/label of the radiation band to check
 * @return 1 if band exists, 0 if not, -1 on error
 */
PYHELIOS_API int doesBandExist(RadiationModel* radiation_model, const char* label);

//=============================================================================
// Source Management Functions
//=============================================================================

/**
 * @brief Delete a radiation source
 * @param radiation_model Pointer to the RadiationModel
 * @param source_id ID of the source to delete
 */
PYHELIOS_API void deleteRadiationSource(RadiationModel* radiation_model, unsigned int source_id);

//=============================================================================
// Source Spectrum Management Functions
//=============================================================================

/**
 * @brief Set source spectrum from spectrum data
 * @param radiation_model Pointer to the RadiationModel
 * @param source_id Source ID
 * @param spectrum_data Flat array [wavelength1, value1, wavelength2, value2, ...]
 * @param spectrum_size Number of spectrum points
 */
PYHELIOS_API void setSourceSpectrum(RadiationModel* radiation_model, unsigned int source_id,
                                    const float* spectrum_data, size_t spectrum_size);

/**
 * @brief Set source spectrum for multiple sources from spectrum data
 * @param radiation_model Pointer to the RadiationModel
 * @param source_ids Array of source IDs
 * @param source_count Number of sources
 * @param spectrum_data Flat array [wavelength1, value1, wavelength2, value2, ...]
 * @param spectrum_size Number of spectrum points
 */
PYHELIOS_API void setSourceSpectrumMultiple(RadiationModel* radiation_model,
                                            const unsigned int* source_ids, size_t source_count,
                                            const float* spectrum_data, size_t spectrum_size);

/**
 * @brief Set source spectrum from global data label
 * @param radiation_model Pointer to the RadiationModel
 * @param source_id Source ID
 * @param spectrum_label Global data label for spectrum
 */
PYHELIOS_API void setSourceSpectrumLabel(RadiationModel* radiation_model, unsigned int source_id,
                                         const char* spectrum_label);

/**
 * @brief Set source spectrum for multiple sources from global data label
 * @param radiation_model Pointer to the RadiationModel
 * @param source_ids Array of source IDs
 * @param source_count Number of sources
 * @param spectrum_label Global data label for spectrum
 */
PYHELIOS_API void setSourceSpectrumLabelMultiple(RadiationModel* radiation_model,
                                                 const unsigned int* source_ids, size_t source_count,
                                                 const char* spectrum_label);

/**
 * @brief Set source spectrum integral
 * @param radiation_model Pointer to the RadiationModel
 * @param source_id Source ID
 * @param source_integral Integral value
 */
PYHELIOS_API void setSourceSpectrumIntegral(RadiationModel* radiation_model, unsigned int source_id,
                                            float source_integral);

/**
 * @brief Set source spectrum integral over wavelength range
 * @param radiation_model Pointer to the RadiationModel
 * @param source_id Source ID
 * @param source_integral Integral value
 * @param wavelength_min Minimum wavelength
 * @param wavelength_max Maximum wavelength
 */
PYHELIOS_API void setSourceSpectrumIntegralRange(RadiationModel* radiation_model, unsigned int source_id,
                                                 float source_integral, float wavelength_min, float wavelength_max);

//=============================================================================
// Spectrum Integration Functions
//=============================================================================

/**
 * @brief Integrate spectrum over all wavelengths
 * @param radiation_model Pointer to the RadiationModel
 * @param object_spectrum Flat array [wavelength1, value1, wavelength2, value2, ...]
 * @param spectrum_size Number of spectrum points
 * @return Integrated value
 */
PYHELIOS_API float integrateSpectrum(RadiationModel* radiation_model,
                                     const float* object_spectrum, size_t spectrum_size);

/**
 * @brief Integrate spectrum over wavelength range
 * @param radiation_model Pointer to the RadiationModel
 * @param object_spectrum Flat array [wavelength1, value1, wavelength2, value2, ...]
 * @param spectrum_size Number of spectrum points
 * @param wavelength_min Minimum wavelength
 * @param wavelength_max Maximum wavelength
 * @return Integrated value
 */
PYHELIOS_API float integrateSpectrumRange(RadiationModel* radiation_model,
                                          const float* object_spectrum, size_t spectrum_size,
                                          float wavelength_min, float wavelength_max);

/**
 * @brief Integrate spectrum with source spectrum over wavelength range
 * @param radiation_model Pointer to the RadiationModel
 * @param source_id Source ID
 * @param object_spectrum Flat array [wavelength1, value1, wavelength2, value2, ...]
 * @param spectrum_size Number of spectrum points
 * @param wavelength_min Minimum wavelength
 * @param wavelength_max Maximum wavelength
 * @return Integrated value
 */
PYHELIOS_API float integrateSpectrumWithSource(RadiationModel* radiation_model, unsigned int source_id,
                                               const float* object_spectrum, size_t spectrum_size,
                                               float wavelength_min, float wavelength_max);

/**
 * @brief Integrate object spectrum with camera spectrum
 * @param radiation_model Pointer to the RadiationModel
 * @param object_spectrum Flat array [wavelength1, value1, wavelength2, value2, ...]
 * @param object_spectrum_size Number of object spectrum points
 * @param camera_spectrum Flat array [wavelength1, value1, wavelength2, value2, ...]
 * @param camera_spectrum_size Number of camera spectrum points
 * @return Integrated value
 */
PYHELIOS_API float integrateSpectrumWithCamera(RadiationModel* radiation_model,
                                               const float* object_spectrum, size_t object_spectrum_size,
                                               const float* camera_spectrum, size_t camera_spectrum_size);

/**
 * @brief Integrate object spectrum with source and camera spectra
 * @param radiation_model Pointer to the RadiationModel
 * @param source_id Source ID
 * @param object_spectrum Flat array [wavelength1, value1, wavelength2, value2, ...]
 * @param object_spectrum_size Number of object spectrum points
 * @param camera_spectrum Flat array [wavelength1, value1, wavelength2, value2, ...]
 * @param camera_spectrum_size Number of camera spectrum points
 * @return Integrated value
 */
PYHELIOS_API float integrateSpectrumWithSourceAndCamera(RadiationModel* radiation_model, unsigned int source_id,
                                                        const float* object_spectrum, size_t object_spectrum_size,
                                                        const float* camera_spectrum, size_t camera_spectrum_size);

/**
 * @brief Integrate source spectrum over wavelength range
 * @param radiation_model Pointer to the RadiationModel
 * @param source_id Source ID
 * @param wavelength_min Minimum wavelength
 * @param wavelength_max Maximum wavelength
 * @return Integrated value
 */
PYHELIOS_API float integrateSourceSpectrum(RadiationModel* radiation_model, unsigned int source_id,
                                           float wavelength_min, float wavelength_max);

//=============================================================================
// Spectral Interpolation Functions
//=============================================================================

/**
 * @brief Interpolate spectrum from primitive data
 * @param radiation_model Pointer to the RadiationModel
 * @param primitive_uuids Array of primitive UUIDs
 * @param uuid_count Number of UUIDs
 * @param spectra_labels Array of spectrum labels
 * @param spectra_count Number of spectra
 * @param values Array of values corresponding to spectra
 * @param value_count Number of values
 * @param primitive_data_query_label Primitive data label to query
 * @param primitive_data_radprop_label Primitive data label for radiation property
 */
PYHELIOS_API void interpolateSpectrumFromPrimitiveData(RadiationModel* radiation_model,
                                                       const unsigned int* primitive_uuids, size_t uuid_count,
                                                       const char** spectra_labels, size_t spectra_count,
                                                       const float* values, size_t value_count,
                                                       const char* primitive_data_query_label,
                                                       const char* primitive_data_radprop_label);

/**
 * @brief Interpolate spectrum from object data
 * @param radiation_model Pointer to the RadiationModel
 * @param object_ids Array of object IDs
 * @param object_count Number of objects
 * @param spectra_labels Array of spectrum labels
 * @param spectra_count Number of spectra
 * @param values Array of values corresponding to spectra
 * @param value_count Number of values
 * @param object_data_query_label Object data label to query
 * @param primitive_data_radprop_label Primitive data label for radiation property
 */
PYHELIOS_API void interpolateSpectrumFromObjectData(RadiationModel* radiation_model,
                                                    const unsigned int* object_ids, size_t object_count,
                                                    const char** spectra_labels, size_t spectra_count,
                                                    const float* values, size_t value_count,
                                                    const char* object_data_query_label,
                                                    const char* primitive_data_radprop_label);

//=============================================================================
// Spectral Manipulation Functions
//=============================================================================

/**
 * @brief Scale spectrum and store as new global data
 * @param radiation_model Pointer to the RadiationModel
 * @param existing_label Existing global data label
 * @param new_label New global data label for scaled spectrum
 * @param scale_factor Scaling factor
 */
PYHELIOS_API void scaleSpectrumToNew(RadiationModel* radiation_model, const char* existing_label,
                                     const char* new_label, float scale_factor);

/**
 * @brief Scale spectrum in-place
 * @param radiation_model Pointer to the RadiationModel
 * @param label Global data label
 * @param scale_factor Scaling factor
 */
PYHELIOS_API void scaleSpectrumInPlace(RadiationModel* radiation_model, const char* label,
                                       float scale_factor);

/**
 * @brief Scale spectrum randomly and store as new global data
 * @param radiation_model Pointer to the RadiationModel
 * @param existing_label Existing global data label
 * @param new_label New global data label for scaled spectrum
 * @param min_scale Minimum scale factor
 * @param max_scale Maximum scale factor
 */
PYHELIOS_API void scaleSpectrumRandomly(RadiationModel* radiation_model, const char* existing_label,
                                        const char* new_label, float min_scale, float max_scale);

/**
 * @brief Blend multiple spectra with weights
 * @param radiation_model Pointer to the RadiationModel
 * @param new_label New global data label for blended spectrum
 * @param spectrum_labels Array of spectrum labels to blend
 * @param label_count Number of spectrum labels
 * @param weights Array of weights (same size as labels)
 */
PYHELIOS_API void blendSpectra(RadiationModel* radiation_model, const char* new_label,
                               const char** spectrum_labels, size_t label_count,
                               const float* weights);

/**
 * @brief Blend multiple spectra with random weights
 * @param radiation_model Pointer to the RadiationModel
 * @param new_label New global data label for blended spectrum
 * @param spectrum_labels Array of spectrum labels to blend
 * @param label_count Number of spectrum labels
 */
PYHELIOS_API void blendSpectraRandomly(RadiationModel* radiation_model, const char* new_label,
                                       const char** spectrum_labels, size_t label_count);

/**
 * @brief Get position of a radiation source
 * @param radiation_model Pointer to the RadiationModel
 * @param source_id ID of the source
 * @param position Output array [x, y, z] for source position
 */
PYHELIOS_API void getSourcePosition(RadiationModel* radiation_model, unsigned int source_id, float* position);

/**
 * @brief Set position of a radiation source (vec3 variant)
 * @param radiation_model Pointer to the RadiationModel
 * @param source_id ID of the source
 * @param x X component of position
 * @param y Y component of position
 * @param z Z component of position
 */
PYHELIOS_API void setSourcePositionVec3(RadiationModel* radiation_model, unsigned int source_id,
                                        float x, float y, float z);

/**
 * @brief Set position of a radiation source (spherical variant)
 * @param radiation_model Pointer to the RadiationModel
 * @param source_id ID of the source
 * @param radius Spherical radius
 * @param elevation Elevation angle
 * @param azimuth Azimuth angle
 */
PYHELIOS_API void setSourcePositionSpherical(RadiationModel* radiation_model, unsigned int source_id,
                                             float radius, float elevation, float azimuth);

/**
 * @brief Add a rectangle radiation source
 * @param radiation_model Pointer to the RadiationModel
 * @param position_x X coordinate of position
 * @param position_y Y coordinate of position
 * @param position_z Z coordinate of position
 * @param size_x Width of rectangle
 * @param size_y Height of rectangle
 * @param rotation_x X component of rotation vector
 * @param rotation_y Y component of rotation vector
 * @param rotation_z Z component of rotation vector
 * @return Source ID
 */
PYHELIOS_API unsigned int addRectangleRadiationSource(RadiationModel* radiation_model,
                                                      float position_x, float position_y, float position_z,
                                                      float size_x, float size_y,
                                                      float rotation_x, float rotation_y, float rotation_z);

/**
 * @brief Add a disk radiation source
 * @param radiation_model Pointer to the RadiationModel
 * @param position_x X coordinate of position
 * @param position_y Y coordinate of position
 * @param position_z Z coordinate of position
 * @param radius Disk radius
 * @param rotation_x X component of rotation vector
 * @param rotation_y Y component of rotation vector
 * @param rotation_z Z component of rotation vector
 * @return Source ID
 */
PYHELIOS_API unsigned int addDiskRadiationSource(RadiationModel* radiation_model,
                                                 float position_x, float position_y, float position_z,
                                                 float radius,
                                                 float rotation_x, float rotation_y, float rotation_z);

//=============================================================================
// Advanced Simulation Functions
//=============================================================================

/**
 * @brief Get total sky energy
 * @param radiation_model Pointer to the RadiationModel
 * @return Sky energy value
 */
PYHELIOS_API float getSkyEnergy(RadiationModel* radiation_model);

/**
 * @brief Calculate G-function (geometry factor) for given view direction
 * @param radiation_model Pointer to the RadiationModel
 * @param context Pointer to the Helios context
 * @param view_x X component of view direction
 * @param view_y Y component of view direction
 * @param view_z Z component of view direction
 * @return G-function value
 */
PYHELIOS_API float calculateGtheta(RadiationModel* radiation_model, helios::Context* context,
                                   float view_x, float view_y, float view_z);

/**
 * @brief Enable optional primitive data output
 * @param radiation_model Pointer to the RadiationModel
 * @param label Name/label of the primitive data to output
 */
PYHELIOS_API void radiationOptionalOutputPrimitiveData(RadiationModel* radiation_model, const char* label);

/**
 * @brief Enforce periodic boundary conditions
 * @param radiation_model Pointer to the RadiationModel
 * @param boundary Boundary specification string
 */
PYHELIOS_API void enforcePeriodicBoundary(RadiationModel* radiation_model, const char* boundary);

//=============================================================================
// Camera and Image Functions (v1.3.47)
//=============================================================================

/**
 * @brief Write camera image to file (returns output filename)
 * @param radiation_model Pointer to the RadiationModel
 * @param camera Camera label
 * @param bands Array of band labels
 * @param band_count Number of bands
 * @param imagefile_base Base filename for output
 * @param image_path Output directory path
 * @param frame Frame number (-1 for all)
 * @param flux_to_pixel_conversion Conversion factor
 * @return Output filename string
 */
PYHELIOS_API const char* writeCameraImage(RadiationModel* radiation_model, const char* camera, 
                                          const char** bands, size_t band_count,
                                          const char* imagefile_base, const char* image_path, 
                                          int frame, float flux_to_pixel_conversion);

/**
 * @brief Write normalized camera image to file (returns output filename)
 * @param radiation_model Pointer to the RadiationModel
 * @param camera Camera label
 * @param bands Array of band labels
 * @param band_count Number of bands
 * @param imagefile_base Base filename for output
 * @param image_path Output directory path
 * @param frame Frame number (-1 for all)
 * @return Output filename string
 */
PYHELIOS_API const char* writeNormCameraImage(RadiationModel* radiation_model, const char* camera, 
                                              const char** bands, size_t band_count,
                                              const char* imagefile_base, const char* image_path, int frame);

/**
 * @brief Write camera image data to file (ASCII format)
 * @param radiation_model Pointer to the RadiationModel
 * @param camera Camera label
 * @param band Band label
 * @param imagefile_base Base filename for output
 * @param image_path Output directory path
 * @param frame Frame number (-1 for all)
 */
PYHELIOS_API void writeCameraImageData(RadiationModel* radiation_model, const char* camera, const char* band,
                                       const char* imagefile_base, const char* image_path, int frame);

/**
 * @brief Write image bounding boxes (single primitive data label)
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label
 * @param primitive_data_label Primitive data label
 * @param object_class_id Object class ID
 * @param image_file Image filename
 * @param classes_txt_file Classes file
 * @param image_path Image output path
 */
PYHELIOS_API void writeImageBoundingBoxes(RadiationModel* radiation_model, const char* camera_label,
                                          const char* primitive_data_label, unsigned int object_class_id,
                                          const char* image_file, const char* classes_txt_file, const char* image_path);

/**
 * @brief Write image bounding boxes (vector primitive data labels)
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label
 * @param primitive_data_labels Array of primitive data labels
 * @param label_count Number of labels
 * @param object_class_ids Array of class IDs
 * @param image_file Image filename
 * @param classes_txt_file Classes file
 * @param image_path Image output path
 */
PYHELIOS_API void writeImageBoundingBoxesVector(RadiationModel* radiation_model, const char* camera_label,
                                                const char** primitive_data_labels, size_t label_count,
                                                unsigned int* object_class_ids, const char* image_file,
                                                const char* classes_txt_file, const char* image_path);

/**
 * @brief Write image bounding boxes with object data (single label)
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label
 * @param object_data_label Object data label
 * @param object_class_id Object class ID
 * @param image_file Image filename
 * @param classes_txt_file Classes file
 * @param image_path Image output path
 */
PYHELIOS_API void writeImageBoundingBoxes_ObjectData(RadiationModel* radiation_model, const char* camera_label,
                                                     const char* object_data_label, unsigned int object_class_id,
                                                     const char* image_file, const char* classes_txt_file, const char* image_path);

/**
 * @brief Write image bounding boxes with object data (vector labels)
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label
 * @param object_data_labels Array of object data labels
 * @param label_count Number of labels
 * @param object_class_ids Array of class IDs
 * @param image_file Image filename
 * @param classes_txt_file Classes file
 * @param image_path Image output path
 */
PYHELIOS_API void writeImageBoundingBoxes_ObjectDataVector(RadiationModel* radiation_model, const char* camera_label,
                                                           const char** object_data_labels, size_t label_count,
                                                           unsigned int* object_class_ids, const char* image_file,
                                                           const char* classes_txt_file, const char* image_path);

/**
 * @brief Write image segmentation masks (single primitive data label)
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label
 * @param primitive_data_label Primitive data label
 * @param object_class_id Object class ID
 * @param json_filename JSON output filename
 * @param image_file Image filename
 * @param append_file Whether to append to file (1 = true, 0 = false)
 */
PYHELIOS_API void writeImageSegmentationMasks(RadiationModel* radiation_model, const char* camera_label,
                                              const char* primitive_data_label, unsigned int object_class_id,
                                              const char* json_filename, const char* image_file, int append_file);

/**
 * @brief Write image segmentation masks (vector primitive data labels)
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label
 * @param primitive_data_labels Array of primitive data labels
 * @param label_count Number of labels
 * @param object_class_ids Array of class IDs
 * @param json_filename JSON output filename
 * @param image_file Image filename
 * @param append_file Whether to append to file (1 = true, 0 = false)
 */
PYHELIOS_API void writeImageSegmentationMasksVector(RadiationModel* radiation_model, const char* camera_label,
                                                    const char** primitive_data_labels, size_t label_count,
                                                    unsigned int* object_class_ids, const char* json_filename,
                                                    const char* image_file, int append_file);

/**
 * @brief Write image segmentation masks with object data (single label)
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label
 * @param object_data_label Object data label
 * @param object_class_id Object class ID
 * @param json_filename JSON output filename
 * @param image_file Image filename
 * @param append_file Whether to append to file (1 = true, 0 = false)
 */
PYHELIOS_API void writeImageSegmentationMasks_ObjectData(RadiationModel* radiation_model, const char* camera_label,
                                                         const char* object_data_label, unsigned int object_class_id,
                                                         const char* json_filename, const char* image_file, int append_file);

/**
 * @brief Write image segmentation masks with object data (vector labels)
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label
 * @param object_data_labels Array of object data labels
 * @param label_count Number of labels
 * @param object_class_ids Array of class IDs
 * @param json_filename JSON output filename
 * @param image_file Image filename
 * @param append_file Whether to append to file (1 = true, 0 = false)
 */
PYHELIOS_API void writeImageSegmentationMasks_ObjectDataVector(RadiationModel* radiation_model, const char* camera_label,
                                                               const char** object_data_labels, size_t label_count,
                                                               unsigned int* object_class_ids, const char* json_filename,
                                                               const char* image_file, int append_file);

/**
 * @brief Auto-calibrate camera image with color correction
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label
 * @param red_band_label Red band label
 * @param green_band_label Green band label
 * @param blue_band_label Blue band label
 * @param output_file_path Output file path
 * @param print_quality_report Whether to print quality report (1 = true, 0 = false)
 * @param algorithm ColorCorrectionAlgorithm (0=DIAGONAL_ONLY, 1=MATRIX_3X3_AUTO, 2=MATRIX_3X3_FORCE)
 * @param ccm_export_file_path Path to export color correction matrix (optional)
 * @return Output filename string
 */
PYHELIOS_API const char* autoCalibrateCameraImage(RadiationModel* radiation_model, const char* camera_label,
                                                  const char* red_band_label, const char* green_band_label, const char* blue_band_label,
                                                  const char* output_file_path, int print_quality_report,
                                                  int algorithm, const char* ccm_export_file_path);

/**
 * @brief Add radiation camera with position and lookat vectors
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label string
 * @param band_labels Array of band label strings
 * @param band_count Number of band labels
 * @param position_x Camera position X coordinate
 * @param position_y Camera position Y coordinate
 * @param position_z Camera position Z coordinate
 * @param lookat_x Lookat point X coordinate
 * @param lookat_y Lookat point Y coordinate
 * @param lookat_z Lookat point Z coordinate
 * @param camera_properties Camera properties array [resolution_x, resolution_y, focal_distance, lens_diameter, HFOV, FOV_aspect_ratio, lens_focal_length, sensor_width_mm, shutter_speed] (9 floats; v1.3.58+)
 * @param antialiasing_samples Number of antialiasing samples
 */
PYHELIOS_API void addRadiationCameraVec3(RadiationModel* radiation_model, const char* camera_label,
                                         const char** band_labels, size_t band_count,
                                         float position_x, float position_y, float position_z,
                                         float lookat_x, float lookat_y, float lookat_z,
                                         const float* camera_properties, unsigned int antialiasing_samples);

/**
 * @brief Add radiation camera with position and spherical viewing direction
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label string
 * @param band_labels Array of band label strings
 * @param band_count Number of band labels
 * @param position_x Camera position X coordinate
 * @param position_y Camera position Y coordinate
 * @param position_z Camera position Z coordinate
 * @param radius Spherical coordinate radius
 * @param elevation Spherical coordinate elevation
 * @param azimuth Spherical coordinate azimuth
 * @param camera_properties Camera properties array [resolution_x, resolution_y, focal_distance, lens_diameter, HFOV, FOV_aspect_ratio, lens_focal_length, sensor_width_mm, shutter_speed] (9 floats; v1.3.58+)
 * @param antialiasing_samples Number of antialiasing samples
 */
PYHELIOS_API void addRadiationCameraSpherical(RadiationModel* radiation_model, const char* camera_label,
                                              const char** band_labels, size_t band_count,
                                              float position_x, float position_y, float position_z,
                                              float radius, float elevation, float azimuth,
                                              const float* camera_properties, unsigned int antialiasing_samples);

/**
 * @brief Add a solar-induced chlorophyll fluorescence (SIF) camera with vec3 lookat
 *
 * Each emission band must already exist (added via addRadiationBand). The bands are
 * flagged internally as SIF-emitting and use the Fluspect-B leaf-fluorescence kernel
 * for emission instead of Stefan-Boltzmann. Helios auto-creates internal radiation
 * bands covering 400-750 nm at the requested excitation_bin_width_nm.
 *
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label string
 * @param band_labels Array of emission band label strings
 * @param band_count Number of band labels
 * @param position_x Camera position X coordinate
 * @param position_y Camera position Y coordinate
 * @param position_z Camera position Z coordinate
 * @param lookat_x Lookat point X coordinate
 * @param lookat_y Lookat point Y coordinate
 * @param lookat_z Lookat point Z coordinate
 * @param camera_properties Camera properties array of 10 floats (same format as addRadiationCameraVec3)
 * @param excitation_bin_width_nm Excitation wavelength bin width in nm (must be > 0)
 * @param excitation_scattering_depth Scattering depth for excitation bands (0 = no scatter)
 * @param antialiasing_samples Number of antialiasing samples (>= 1)
 */
PYHELIOS_API void addSIFCameraVec3(RadiationModel* radiation_model, const char* camera_label,
                                   const char** band_labels, size_t band_count,
                                   float position_x, float position_y, float position_z,
                                   float lookat_x, float lookat_y, float lookat_z,
                                   const float* camera_properties,
                                   float excitation_bin_width_nm, unsigned int excitation_scattering_depth,
                                   unsigned int antialiasing_samples);

/**
 * @brief Add a solar-induced chlorophyll fluorescence (SIF) camera with spherical viewing direction
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label string
 * @param band_labels Array of emission band label strings
 * @param band_count Number of band labels
 * @param position_x Camera position X coordinate
 * @param position_y Camera position Y coordinate
 * @param position_z Camera position Z coordinate
 * @param radius Spherical viewing radius
 * @param elevation Spherical viewing elevation
 * @param azimuth Spherical viewing azimuth
 * @param camera_properties Camera properties array of 10 floats
 * @param excitation_bin_width_nm Excitation wavelength bin width in nm (must be > 0)
 * @param excitation_scattering_depth Scattering depth for excitation bands (0 = no scatter)
 * @param antialiasing_samples Number of antialiasing samples (>= 1)
 */
PYHELIOS_API void addSIFCameraSpherical(RadiationModel* radiation_model, const char* camera_label,
                                        const char** band_labels, size_t band_count,
                                        float position_x, float position_y, float position_z,
                                        float radius, float elevation, float azimuth,
                                        const float* camera_properties,
                                        float excitation_bin_width_nm, unsigned int excitation_scattering_depth,
                                        unsigned int antialiasing_samples);

/**
 * @brief Check whether a camera was added via addSIFCamera (vs. addRadiationCamera)
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label
 * @return 1 if the camera exists and is a SIF camera, 0 otherwise
 */
PYHELIOS_API int isSIFCamera(RadiationModel* radiation_model, const char* camera_label);

//=============================================================================
// Camera Management Functions
//=============================================================================

/**
 * @brief Set camera position
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label
 * @param x X component of position
 * @param y Y component of position
 * @param z Z component of position
 */
PYHELIOS_API void setRadiationCameraPosition(RadiationModel* radiation_model, const char* camera_label,
                                    float x, float y, float z);

/**
 * @brief Get camera position
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label
 * @param position Output array [x, y, z] for camera position
 */
PYHELIOS_API void getRadiationCameraPosition(RadiationModel* radiation_model, const char* camera_label,
                                    float* position);

/**
 * @brief Set camera lookat point
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label
 * @param x X component of lookat point
 * @param y Y component of lookat point
 * @param z Z component of lookat point
 */
PYHELIOS_API void setCameraLookat(RadiationModel* radiation_model, const char* camera_label,
                                  float x, float y, float z);

/**
 * @brief Get camera lookat point
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label
 * @param lookat Output array [x, y, z] for lookat point
 */
PYHELIOS_API void getCameraLookat(RadiationModel* radiation_model, const char* camera_label,
                                  float* lookat);

/**
 * @brief Set camera orientation (vec3 direction)
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label
 * @param x X component of direction
 * @param y Y component of direction
 * @param z Z component of direction
 */
PYHELIOS_API void setCameraOrientationVec3(RadiationModel* radiation_model, const char* camera_label,
                                           float x, float y, float z);

/**
 * @brief Set camera orientation (spherical coordinates)
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label
 * @param radius Spherical radius
 * @param elevation Elevation angle
 * @param azimuth Azimuth angle
 */
PYHELIOS_API void setCameraOrientationSpherical(RadiationModel* radiation_model, const char* camera_label,
                                                float radius, float elevation, float azimuth);

/**
 * @brief Get camera orientation
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label
 * @param orientation Output array [radius, elevation, azimuth] for spherical orientation
 */
PYHELIOS_API void getCameraOrientation(RadiationModel* radiation_model, const char* camera_label,
                                       float* orientation);

/**
 * @brief Get all camera labels
 * @param radiation_model Pointer to the RadiationModel
 * @param count Output pointer for number of camera labels
 * @return Array of camera label strings (NULL-terminated)
 */
PYHELIOS_API const char** getAllCameraLabels(RadiationModel* radiation_model, size_t* count);

/**
 * @brief Set camera spectral response from global data
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label
 * @param band_label Band label
 * @param global_data Global data label for spectral response
 */
PYHELIOS_API void setCameraSpectralResponse(RadiationModel* radiation_model, const char* camera_label,
                                            const char* band_label, const char* global_data);

/**
 * @brief Set camera spectral response from standard camera library
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label
 * @param camera_library_name Standard camera name (e.g., "iPhone13", "NikonD850")
 */
PYHELIOS_API void setCameraSpectralResponseFromLibrary(RadiationModel* radiation_model, const char* camera_label,
                                                       const char* camera_library_name);

/**
 * @brief Get camera pixel data for specific band
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label
 * @param band_label Band label
 * @param size Output pointer for data size
 * @return Pixel data array
 */
PYHELIOS_API const float* getCameraPixelData(RadiationModel* radiation_model, const char* camera_label,
                                             const char* band_label, size_t* size);

/**
 * @brief Set camera pixel data for specific band
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label
 * @param band_label Band label
 * @param pixel_data Pixel data array
 * @param size Data size
 */
PYHELIOS_API void setCameraPixelData(RadiationModel* radiation_model, const char* camera_label,
                                     const char* band_label, const float* pixel_data, size_t size);

//=========================================================================
// Camera Library Functions (v1.3.58+)
//=========================================================================

/**
 * @brief Add radiation camera loading all properties from camera library
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Label for the camera instance
 * @param library_camera_label Label of camera in library (e.g., "Canon_20D", "iPhone11")
 * @param position_x Camera position X coordinate
 * @param position_y Camera position Y coordinate
 * @param position_z Camera position Z coordinate
 * @param lookat_x Lookat point X coordinate
 * @param lookat_y Lookat point Y coordinate
 * @param lookat_z Lookat point Z coordinate
 * @param antialiasing_samples Number of antialiasing samples
 */
PYHELIOS_API void addRadiationCameraFromLibrary(RadiationModel* radiation_model,
                                                 const char* camera_label,
                                                 const char* library_camera_label,
                                                 float position_x, float position_y, float position_z,
                                                 float lookat_x, float lookat_y, float lookat_z,
                                                 unsigned int antialiasing_samples);

/**
 * @brief Add radiation camera from library with custom band labels
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Label for the camera instance
 * @param library_camera_label Label of camera in library
 * @param position_x Camera position X coordinate
 * @param position_y Camera position Y coordinate
 * @param position_z Camera position Z coordinate
 * @param lookat_x Lookat point X coordinate
 * @param lookat_y Lookat point Y coordinate
 * @param lookat_z Lookat point Z coordinate
 * @param antialiasing_samples Number of antialiasing samples
 * @param band_labels Custom band labels array
 * @param band_count Number of custom band labels
 */
PYHELIOS_API void addRadiationCameraFromLibraryWithBands(RadiationModel* radiation_model,
                                                           const char* camera_label,
                                                           const char* library_camera_label,
                                                           float position_x, float position_y, float position_z,
                                                           float lookat_x, float lookat_y, float lookat_z,
                                                           unsigned int antialiasing_samples,
                                                           const char** band_labels, size_t band_count);

/**
 * @brief Update camera parameters for an existing camera
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Label for the camera to update
 * @param camera_properties Camera properties array (9 floats; v1.3.58+)
 */
PYHELIOS_API void updateCameraParameters(RadiationModel* radiation_model,
                                         const char* camera_label,
                                         const float* camera_properties);

/**
 * @brief Enable automatic JSON metadata file writing for a camera
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Label for the camera to enable metadata for
 */
PYHELIOS_API void enableCameraMetadata(RadiationModel* radiation_model,
                                       const char* camera_label);

/**
 * @brief Enable automatic JSON metadata file writing for multiple cameras
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_labels Array of camera labels
 * @param count Number of camera labels
 */
PYHELIOS_API void enableCameraMetadataMultiple(RadiationModel* radiation_model,
                                                const char** camera_labels, size_t count);

//=============================================================================
// EXR Image Export Functions (v1.3.66+)
//=============================================================================

/**
 * @brief Write single-band camera pixel data to EXR file with lossless float compression
 * @param radiation_model Pointer to the RadiationModel
 * @param camera Camera label
 * @param band Band label
 * @param imagefile_base Base filename for output
 * @param image_path Output directory path
 * @param frame Frame number (-1 to omit)
 */
PYHELIOS_API void writeCameraImageDataEXR(RadiationModel* radiation_model, const char* camera,
                                          const char* band, const char* imagefile_base,
                                          const char* image_path, int frame);

/**
 * @brief Write multi-band camera pixel data to a single EXR file with lossless float compression
 * @param radiation_model Pointer to the RadiationModel
 * @param camera Camera label
 * @param bands Array of band labels
 * @param band_count Number of bands
 * @param imagefile_base Base filename for output
 * @param image_path Output directory path
 * @param frame Frame number (-1 to omit)
 */
PYHELIOS_API void writeCameraImageDataEXRMultiple(RadiationModel* radiation_model, const char* camera,
                                                   const char** bands, size_t band_count,
                                                   const char* imagefile_base, const char* image_path, int frame);

/**
 * @brief Write depth image data to ASCII text file
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label
 * @param imagefile_base Base filename for output
 * @param image_path Output directory path
 * @param frame Frame number (-1 to omit)
 */
PYHELIOS_API void writeDepthImageData(RadiationModel* radiation_model, const char* camera_label,
                                      const char* imagefile_base, const char* image_path, int frame);

/**
 * @brief Write depth image data to EXR file with lossless float compression
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label
 * @param imagefile_base Base filename for output
 * @param image_path Output directory path
 * @param frame Frame number (-1 to omit)
 */
PYHELIOS_API void writeDepthImageDataEXR(RadiationModel* radiation_model, const char* camera_label,
                                         const char* imagefile_base, const char* image_path, int frame);

/**
 * @brief Write normalized depth image (grayscale JPEG)
 * @param radiation_model Pointer to the RadiationModel
 * @param camera_label Camera label
 * @param imagefile_base Base filename for output
 * @param max_depth Maximum depth value for normalization
 * @param image_path Output directory path
 * @param frame Frame number (-1 to omit)
 */
PYHELIOS_API void writeNormDepthImage(RadiationModel* radiation_model, const char* camera_label,
                                      const char* imagefile_base, float max_depth,
                                      const char* image_path, int frame);

//=============================================================================
// Backend Query Functions (v1.3.67+)
//=============================================================================

/**
 * @brief Get the name of the active ray tracing backend
 * @param radiation_model Pointer to the RadiationModel
 * @return Backend name string (e.g., "OptiX 8.1", "Vulkan Compute"), or nullptr on error
 */
PYHELIOS_API const char* getBackendName(RadiationModel* radiation_model);

/**
 * @brief Probe whether any compiled-in GPU backend is available on this system
 * @return 1 if at least one backend is available, 0 if none
 */
PYHELIOS_API int probeAnyGPUBackend();

#ifdef __cplusplus
}
#endif

#endif // PYHELIOS_WRAPPER_RADIATION_H