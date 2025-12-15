"""
Ctypes wrapper for RadiationModel C++ bindings.

This module provides low-level ctypes bindings to interface with 
the native Helios RadiationModel plugin via the C++ wrapper layer.
"""

import ctypes
from typing import List

from ..plugins import helios_lib
from ..exceptions import check_helios_error

# Define the URadiationModel struct
class URadiationModel(ctypes.Structure):
    pass

# Import UContext from main wrapper to avoid type conflicts
from .UContextWrapper import UContext

# Error checking callback
def _check_error(result, func, args):
    """
    Errcheck callback that automatically checks for Helios errors after each RadiationModel function call.
    This ensures that C++ exceptions are properly converted to Python exceptions.
    """
    check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage)
    return result

# Try to set up RadiationModel function prototypes
try:
    # RadiationModel creation and destruction
    helios_lib.createRadiationModel.argtypes = [ctypes.POINTER(UContext)]
    helios_lib.createRadiationModel.restype = ctypes.POINTER(URadiationModel)

    helios_lib.destroyRadiationModel.argtypes = [ctypes.POINTER(URadiationModel)]
    helios_lib.destroyRadiationModel.restype = None

    # Message control
    helios_lib.disableRadiationMessages.argtypes = [ctypes.POINTER(URadiationModel)]
    helios_lib.disableRadiationMessages.restype = None

    helios_lib.enableRadiationMessages.argtypes = [ctypes.POINTER(URadiationModel)]
    helios_lib.enableRadiationMessages.restype = None

    # Band management
    helios_lib.addRadiationBand.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p]
    helios_lib.addRadiationBand.restype = None

    helios_lib.addRadiationBandWithWavelengths.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p, ctypes.c_float, ctypes.c_float]
    helios_lib.addRadiationBandWithWavelengths.restype = None

    helios_lib.copyRadiationBand.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.copyRadiationBand.restype = None

    helios_lib.copyRadiationBandWithWavelengths.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p, ctypes.c_char_p,
                                                             ctypes.c_float, ctypes.c_float]
    helios_lib.copyRadiationBandWithWavelengths.restype = None

    # Source management  
    helios_lib.addCollimatedRadiationSourceDefault.argtypes = [ctypes.POINTER(URadiationModel)]
    helios_lib.addCollimatedRadiationSourceDefault.restype = ctypes.c_uint

    helios_lib.addCollimatedRadiationSourceVec3.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.addCollimatedRadiationSourceVec3.restype = ctypes.c_uint

    helios_lib.addCollimatedRadiationSourceSpherical.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.addCollimatedRadiationSourceSpherical.restype = ctypes.c_uint

    helios_lib.addSphereRadiationSource.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.addSphereRadiationSource.restype = ctypes.c_uint

    helios_lib.addSunSphereRadiationSource.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.addSunSphereRadiationSource.restype = ctypes.c_uint

    # Ray count configuration
    helios_lib.setDirectRayCount.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p, ctypes.c_size_t]
    helios_lib.setDirectRayCount.restype = None

    helios_lib.setDiffuseRayCount.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p, ctypes.c_size_t]
    helios_lib.setDiffuseRayCount.restype = None

    # Flux configuration
    helios_lib.setDiffuseRadiationFlux.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p, ctypes.c_float]
    helios_lib.setDiffuseRadiationFlux.restype = None

    # Advanced diffuse radiation configuration
    helios_lib.setDiffuseRadiationExtinctionCoeffVec3.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                                                  ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.setDiffuseRadiationExtinctionCoeffVec3.restype = None

    helios_lib.setDiffuseRadiationExtinctionCoeffSpherical.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                                                       ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.setDiffuseRadiationExtinctionCoeffSpherical.restype = None

    helios_lib.getDiffuseFlux.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p]
    helios_lib.getDiffuseFlux.restype = ctypes.c_float

    helios_lib.setDiffuseSpectrum.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.setDiffuseSpectrum.restype = None

    helios_lib.setDiffuseSpectrumMultiple.argtypes = [ctypes.POINTER(URadiationModel),
                                                      ctypes.POINTER(ctypes.c_char_p), ctypes.c_size_t, ctypes.c_char_p]
    helios_lib.setDiffuseSpectrumMultiple.restype = None

    helios_lib.setDiffuseSpectrumIntegralAll.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_float]
    helios_lib.setDiffuseSpectrumIntegralAll.restype = None

    helios_lib.setDiffuseSpectrumIntegralAllRange.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_float,
                                                              ctypes.c_float, ctypes.c_float]
    helios_lib.setDiffuseSpectrumIntegralAllRange.restype = None

    helios_lib.setDiffuseSpectrumIntegralBand.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p, ctypes.c_float]
    helios_lib.setDiffuseSpectrumIntegralBand.restype = None

    helios_lib.setDiffuseSpectrumIntegralBandRange.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                                               ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.setDiffuseSpectrumIntegralBandRange.restype = None

    helios_lib.setSourceFlux.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_uint, ctypes.c_char_p, ctypes.c_float]
    helios_lib.setSourceFlux.restype = None

    helios_lib.setSourceFluxMultiple.argtypes = [ctypes.POINTER(URadiationModel), ctypes.POINTER(ctypes.c_uint), ctypes.c_size_t, ctypes.c_char_p, ctypes.c_float]
    helios_lib.setSourceFluxMultiple.restype = None

    helios_lib.getSourceFlux.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_uint, ctypes.c_char_p]
    helios_lib.getSourceFlux.restype = ctypes.c_float

    # Scattering configuration
    helios_lib.setScatteringDepth.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p, ctypes.c_uint]
    helios_lib.setScatteringDepth.restype = None

    helios_lib.setMinScatterEnergy.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p, ctypes.c_float]
    helios_lib.setMinScatterEnergy.restype = None

    # Emission control
    helios_lib.disableEmission.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p]
    helios_lib.disableEmission.restype = None

    helios_lib.enableEmission.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p]
    helios_lib.enableEmission.restype = None

    # Geometry and simulation
    helios_lib.updateRadiationGeometry.argtypes = [ctypes.POINTER(URadiationModel)]
    helios_lib.updateRadiationGeometry.restype = None

    helios_lib.updateRadiationGeometryUUIDs.argtypes = [ctypes.POINTER(URadiationModel), ctypes.POINTER(ctypes.c_uint), ctypes.c_size_t]
    helios_lib.updateRadiationGeometryUUIDs.restype = None

    helios_lib.runRadiationBand.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p]
    helios_lib.runRadiationBand.restype = None

    helios_lib.runRadiationBandMultiple.argtypes = [ctypes.POINTER(URadiationModel), ctypes.POINTER(ctypes.c_char_p), ctypes.c_size_t]
    helios_lib.runRadiationBandMultiple.restype = None

    # Results and information
    helios_lib.getTotalAbsorbedFlux.argtypes = [ctypes.POINTER(URadiationModel), ctypes.POINTER(ctypes.c_size_t)]
    helios_lib.getTotalAbsorbedFlux.restype = ctypes.POINTER(ctypes.c_float)

    # Band query functions
    helios_lib.doesBandExist.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p]
    helios_lib.doesBandExist.restype = ctypes.c_int

    # Advanced source management
    helios_lib.deleteRadiationSource.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_uint]
    helios_lib.deleteRadiationSource.restype = None

    helios_lib.getSourcePosition.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.getSourcePosition.restype = None

    helios_lib.setSourcePositionVec3.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_uint,
                                                 ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.setSourcePositionVec3.restype = None

    helios_lib.setSourcePositionSpherical.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_uint,
                                                      ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.setSourcePositionSpherical.restype = None

    helios_lib.addRectangleRadiationSource.argtypes = [ctypes.POINTER(URadiationModel),
                                                       ctypes.c_float, ctypes.c_float, ctypes.c_float,
                                                       ctypes.c_float, ctypes.c_float,
                                                       ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.addRectangleRadiationSource.restype = ctypes.c_uint

    helios_lib.addDiskRadiationSource.argtypes = [ctypes.POINTER(URadiationModel),
                                                  ctypes.c_float, ctypes.c_float, ctypes.c_float,
                                                  ctypes.c_float,
                                                  ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.addDiskRadiationSource.restype = ctypes.c_uint

    # Source spectrum management functions
    helios_lib.setSourceSpectrum.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_uint,
                                             ctypes.POINTER(ctypes.c_float), ctypes.c_size_t]
    helios_lib.setSourceSpectrum.restype = None

    helios_lib.setSourceSpectrumMultiple.argtypes = [ctypes.POINTER(URadiationModel),
                                                     ctypes.POINTER(ctypes.c_uint), ctypes.c_size_t,
                                                     ctypes.POINTER(ctypes.c_float), ctypes.c_size_t]
    helios_lib.setSourceSpectrumMultiple.restype = None

    helios_lib.setSourceSpectrumLabel.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_uint, ctypes.c_char_p]
    helios_lib.setSourceSpectrumLabel.restype = None

    helios_lib.setSourceSpectrumLabelMultiple.argtypes = [ctypes.POINTER(URadiationModel),
                                                          ctypes.POINTER(ctypes.c_uint), ctypes.c_size_t,
                                                          ctypes.c_char_p]
    helios_lib.setSourceSpectrumLabelMultiple.restype = None

    helios_lib.setSourceSpectrumIntegral.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_uint, ctypes.c_float]
    helios_lib.setSourceSpectrumIntegral.restype = None

    helios_lib.setSourceSpectrumIntegralRange.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_uint,
                                                          ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.setSourceSpectrumIntegralRange.restype = None

    # Spectrum integration functions
    helios_lib.integrateSpectrum.argtypes = [ctypes.POINTER(URadiationModel),
                                             ctypes.POINTER(ctypes.c_float), ctypes.c_size_t]
    helios_lib.integrateSpectrum.restype = ctypes.c_float

    helios_lib.integrateSpectrumRange.argtypes = [ctypes.POINTER(URadiationModel),
                                                  ctypes.POINTER(ctypes.c_float), ctypes.c_size_t,
                                                  ctypes.c_float, ctypes.c_float]
    helios_lib.integrateSpectrumRange.restype = ctypes.c_float

    helios_lib.integrateSpectrumWithSource.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_uint,
                                                       ctypes.POINTER(ctypes.c_float), ctypes.c_size_t,
                                                       ctypes.c_float, ctypes.c_float]
    helios_lib.integrateSpectrumWithSource.restype = ctypes.c_float

    helios_lib.integrateSpectrumWithCamera.argtypes = [ctypes.POINTER(URadiationModel),
                                                       ctypes.POINTER(ctypes.c_float), ctypes.c_size_t,
                                                       ctypes.POINTER(ctypes.c_float), ctypes.c_size_t]
    helios_lib.integrateSpectrumWithCamera.restype = ctypes.c_float

    helios_lib.integrateSpectrumWithSourceAndCamera.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_uint,
                                                                ctypes.POINTER(ctypes.c_float), ctypes.c_size_t,
                                                                ctypes.POINTER(ctypes.c_float), ctypes.c_size_t]
    helios_lib.integrateSpectrumWithSourceAndCamera.restype = ctypes.c_float

    helios_lib.integrateSourceSpectrum.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_uint,
                                                   ctypes.c_float, ctypes.c_float]
    helios_lib.integrateSourceSpectrum.restype = ctypes.c_float

    # Spectral interpolation functions
    helios_lib.interpolateSpectrumFromPrimitiveData.argtypes = [
        ctypes.POINTER(URadiationModel),
        ctypes.POINTER(ctypes.c_uint), ctypes.c_size_t,  # primitive_uuids, uuid_count
        ctypes.POINTER(ctypes.c_char_p), ctypes.c_size_t,  # spectra_labels, spectra_count
        ctypes.POINTER(ctypes.c_float), ctypes.c_size_t,  # values, value_count
        ctypes.c_char_p, ctypes.c_char_p  # query_label, radprop_label
    ]
    helios_lib.interpolateSpectrumFromPrimitiveData.restype = None

    helios_lib.interpolateSpectrumFromObjectData.argtypes = [
        ctypes.POINTER(URadiationModel),
        ctypes.POINTER(ctypes.c_uint), ctypes.c_size_t,  # object_ids, object_count
        ctypes.POINTER(ctypes.c_char_p), ctypes.c_size_t,  # spectra_labels, spectra_count
        ctypes.POINTER(ctypes.c_float), ctypes.c_size_t,  # values, value_count
        ctypes.c_char_p, ctypes.c_char_p  # query_label, radprop_label
    ]
    helios_lib.interpolateSpectrumFromObjectData.restype = None

    # Spectral manipulation functions
    helios_lib.scaleSpectrumToNew.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                              ctypes.c_char_p, ctypes.c_float]
    helios_lib.scaleSpectrumToNew.restype = None

    helios_lib.scaleSpectrumInPlace.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p, ctypes.c_float]
    helios_lib.scaleSpectrumInPlace.restype = None

    helios_lib.scaleSpectrumRandomly.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                                 ctypes.c_char_p, ctypes.c_float, ctypes.c_float]
    helios_lib.scaleSpectrumRandomly.restype = None

    helios_lib.blendSpectra.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                        ctypes.POINTER(ctypes.c_char_p), ctypes.c_size_t,
                                        ctypes.POINTER(ctypes.c_float)]
    helios_lib.blendSpectra.restype = None

    helios_lib.blendSpectraRandomly.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                                ctypes.POINTER(ctypes.c_char_p), ctypes.c_size_t]
    helios_lib.blendSpectraRandomly.restype = None

    # Advanced simulation functions
    helios_lib.getSkyEnergy.argtypes = [ctypes.POINTER(URadiationModel)]
    helios_lib.getSkyEnergy.restype = ctypes.c_float

    helios_lib.calculateGtheta.argtypes = [ctypes.POINTER(URadiationModel), ctypes.POINTER(UContext),
                                           ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.calculateGtheta.restype = ctypes.c_float

    helios_lib.radiationOptionalOutputPrimitiveData.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p]
    helios_lib.radiationOptionalOutputPrimitiveData.restype = None

    helios_lib.enforcePeriodicBoundary.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p]
    helios_lib.enforcePeriodicBoundary.restype = None

    # Camera and Image Functions (v1.3.47)
    helios_lib.writeCameraImage.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p, 
                                           ctypes.POINTER(ctypes.c_char_p), ctypes.c_size_t,
                                           ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_float]
    helios_lib.writeCameraImage.restype = ctypes.c_char_p

    helios_lib.writeNormCameraImage.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p, 
                                               ctypes.POINTER(ctypes.c_char_p), ctypes.c_size_t,
                                               ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
    helios_lib.writeNormCameraImage.restype = ctypes.c_char_p

    helios_lib.writeCameraImageData.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p, ctypes.c_char_p,
                                               ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
    helios_lib.writeCameraImageData.restype = None

    # Bounding box functions
    helios_lib.writeImageBoundingBoxes.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                                  ctypes.c_char_p, ctypes.c_uint, ctypes.c_char_p,
                                                  ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.writeImageBoundingBoxes.restype = None

    helios_lib.writeImageBoundingBoxesVector.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                                        ctypes.POINTER(ctypes.c_char_p), ctypes.c_size_t,
                                                        ctypes.POINTER(ctypes.c_uint), ctypes.c_char_p,
                                                        ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.writeImageBoundingBoxesVector.restype = None

    helios_lib.writeImageBoundingBoxes_ObjectData.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                                             ctypes.c_char_p, ctypes.c_uint, ctypes.c_char_p,
                                                             ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.writeImageBoundingBoxes_ObjectData.restype = None

    helios_lib.writeImageBoundingBoxes_ObjectDataVector.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                                                   ctypes.POINTER(ctypes.c_char_p), ctypes.c_size_t,
                                                                   ctypes.POINTER(ctypes.c_uint), ctypes.c_char_p,
                                                                   ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.writeImageBoundingBoxes_ObjectDataVector.restype = None

    # Segmentation mask functions
    helios_lib.writeImageSegmentationMasks.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                                       ctypes.c_char_p, ctypes.c_uint, ctypes.c_char_p,
                                                       ctypes.c_char_p, ctypes.c_int]
    helios_lib.writeImageSegmentationMasks.restype = None

    helios_lib.writeImageSegmentationMasksVector.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                                            ctypes.POINTER(ctypes.c_char_p), ctypes.c_size_t,
                                                            ctypes.POINTER(ctypes.c_uint), ctypes.c_char_p,
                                                            ctypes.c_char_p, ctypes.c_int]
    helios_lib.writeImageSegmentationMasksVector.restype = None

    helios_lib.writeImageSegmentationMasks_ObjectData.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                                                 ctypes.c_char_p, ctypes.c_uint, ctypes.c_char_p,
                                                                 ctypes.c_char_p, ctypes.c_int]
    helios_lib.writeImageSegmentationMasks_ObjectData.restype = None

    helios_lib.writeImageSegmentationMasks_ObjectDataVector.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                                                       ctypes.POINTER(ctypes.c_char_p), ctypes.c_size_t,
                                                                       ctypes.POINTER(ctypes.c_uint), ctypes.c_char_p,
                                                                       ctypes.c_char_p, ctypes.c_int]
    helios_lib.writeImageSegmentationMasks_ObjectDataVector.restype = None

    # Auto-calibration function
    helios_lib.autoCalibrateCameraImage.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                                    ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
                                                    ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
    helios_lib.autoCalibrateCameraImage.restype = ctypes.c_char_p

    # Camera creation functions
    helios_lib.addRadiationCameraVec3.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                                  ctypes.POINTER(ctypes.c_char_p), ctypes.c_size_t,
                                                  ctypes.c_float, ctypes.c_float, ctypes.c_float,
                                                  ctypes.c_float, ctypes.c_float, ctypes.c_float,
                                                  ctypes.POINTER(ctypes.c_float), ctypes.c_uint]
    helios_lib.addRadiationCameraVec3.restype = None

    helios_lib.addRadiationCameraSpherical.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                                       ctypes.POINTER(ctypes.c_char_p), ctypes.c_size_t,
                                                       ctypes.c_float, ctypes.c_float, ctypes.c_float,
                                                       ctypes.c_float, ctypes.c_float, ctypes.c_float,
                                                       ctypes.POINTER(ctypes.c_float), ctypes.c_uint]
    helios_lib.addRadiationCameraSpherical.restype = None

    # Camera management functions
    helios_lib.setRadiationCameraPosition.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                             ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.setRadiationCameraPosition.restype = None

    helios_lib.getRadiationCameraPosition.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                             ctypes.POINTER(ctypes.c_float)]
    helios_lib.getRadiationCameraPosition.restype = None

    helios_lib.setCameraLookat.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                           ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.setCameraLookat.restype = None

    helios_lib.getCameraLookat.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                           ctypes.POINTER(ctypes.c_float)]
    helios_lib.getCameraLookat.restype = None

    helios_lib.setCameraOrientationVec3.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                                    ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.setCameraOrientationVec3.restype = None

    helios_lib.setCameraOrientationSpherical.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                                         ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.setCameraOrientationSpherical.restype = None

    helios_lib.getCameraOrientation.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                                ctypes.POINTER(ctypes.c_float)]
    helios_lib.getCameraOrientation.restype = None

    helios_lib.getAllCameraLabels.argtypes = [ctypes.POINTER(URadiationModel), ctypes.POINTER(ctypes.c_size_t)]
    helios_lib.getAllCameraLabels.restype = ctypes.POINTER(ctypes.c_char_p)

    # Advanced camera functions
    helios_lib.setCameraSpectralResponse.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                                     ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.setCameraSpectralResponse.restype = None

    helios_lib.setCameraSpectralResponseFromLibrary.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                                                ctypes.c_char_p]
    helios_lib.setCameraSpectralResponseFromLibrary.restype = None

    helios_lib.getCameraPixelData.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p, ctypes.c_char_p,
                                              ctypes.POINTER(ctypes.c_size_t)]
    helios_lib.getCameraPixelData.restype = ctypes.POINTER(ctypes.c_float)

    helios_lib.setCameraPixelData.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p, ctypes.c_char_p,
                                              ctypes.POINTER(ctypes.c_float), ctypes.c_size_t]
    helios_lib.setCameraPixelData.restype = None

    # Camera Library Functions (v1.3.58+)
    helios_lib.addRadiationCameraFromLibrary.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                                          ctypes.c_char_p, ctypes.c_float, ctypes.c_float,
                                                          ctypes.c_float, ctypes.c_float, ctypes.c_float,
                                                          ctypes.c_float, ctypes.c_uint]
    helios_lib.addRadiationCameraFromLibrary.restype = None

    helios_lib.addRadiationCameraFromLibraryWithBands.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                                                   ctypes.c_char_p, ctypes.c_float, ctypes.c_float,
                                                                   ctypes.c_float, ctypes.c_float, ctypes.c_float,
                                                                   ctypes.c_float, ctypes.c_uint,
                                                                   ctypes.POINTER(ctypes.c_char_p), ctypes.c_size_t]
    helios_lib.addRadiationCameraFromLibraryWithBands.restype = None

    helios_lib.updateCameraParameters.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p,
                                                  ctypes.POINTER(ctypes.c_float)]
    helios_lib.updateCameraParameters.restype = None

    helios_lib.enableCameraMetadata.argtypes = [ctypes.POINTER(URadiationModel), ctypes.c_char_p]
    helios_lib.enableCameraMetadata.restype = None

    helios_lib.enableCameraMetadataMultiple.argtypes = [ctypes.POINTER(URadiationModel),
                                                         ctypes.POINTER(ctypes.c_char_p), ctypes.c_size_t]
    helios_lib.enableCameraMetadataMultiple.restype = None

    # Add automatic error checking to all RadiationModel functions
    helios_lib.createRadiationModel.errcheck = _check_error
    # Note: destroyRadiationModel doesn't need errcheck as it doesn't fail

    # Message control
    helios_lib.disableRadiationMessages.errcheck = _check_error
    helios_lib.enableRadiationMessages.errcheck = _check_error

    # Band management
    helios_lib.addRadiationBand.errcheck = _check_error
    helios_lib.addRadiationBandWithWavelengths.errcheck = _check_error
    helios_lib.copyRadiationBand.errcheck = _check_error
    helios_lib.copyRadiationBandWithWavelengths.errcheck = _check_error

    # Source management
    helios_lib.addCollimatedRadiationSourceDefault.errcheck = _check_error
    helios_lib.addCollimatedRadiationSourceVec3.errcheck = _check_error
    helios_lib.addCollimatedRadiationSourceSpherical.errcheck = _check_error
    helios_lib.addSphereRadiationSource.errcheck = _check_error
    helios_lib.addSunSphereRadiationSource.errcheck = _check_error

    # Ray count configuration
    helios_lib.setDirectRayCount.errcheck = _check_error
    helios_lib.setDiffuseRayCount.errcheck = _check_error

    # Flux configuration
    helios_lib.setDiffuseRadiationFlux.errcheck = _check_error

    # Advanced diffuse radiation
    helios_lib.setDiffuseRadiationExtinctionCoeffVec3.errcheck = _check_error
    helios_lib.setDiffuseRadiationExtinctionCoeffSpherical.errcheck = _check_error
    helios_lib.getDiffuseFlux.errcheck = _check_error
    helios_lib.setDiffuseSpectrum.errcheck = _check_error
    helios_lib.setDiffuseSpectrumMultiple.errcheck = _check_error
    helios_lib.setDiffuseSpectrumIntegralAll.errcheck = _check_error
    helios_lib.setDiffuseSpectrumIntegralAllRange.errcheck = _check_error
    helios_lib.setDiffuseSpectrumIntegralBand.errcheck = _check_error
    helios_lib.setDiffuseSpectrumIntegralBandRange.errcheck = _check_error

    helios_lib.setSourceFlux.errcheck = _check_error
    helios_lib.setSourceFluxMultiple.errcheck = _check_error
    helios_lib.getSourceFlux.errcheck = _check_error

    # Scattering configuration
    helios_lib.setScatteringDepth.errcheck = _check_error
    helios_lib.setMinScatterEnergy.errcheck = _check_error

    # Emission control
    helios_lib.disableEmission.errcheck = _check_error
    helios_lib.enableEmission.errcheck = _check_error

    # Geometry and simulation
    helios_lib.updateRadiationGeometry.errcheck = _check_error
    helios_lib.updateRadiationGeometryUUIDs.errcheck = _check_error
    helios_lib.runRadiationBand.errcheck = _check_error
    helios_lib.runRadiationBandMultiple.errcheck = _check_error

    # Results and information
    helios_lib.getTotalAbsorbedFlux.errcheck = _check_error

    # Band query functions
    helios_lib.doesBandExist.errcheck = _check_error

    # Advanced source management
    helios_lib.deleteRadiationSource.errcheck = _check_error
    helios_lib.getSourcePosition.errcheck = _check_error
    helios_lib.setSourcePositionVec3.errcheck = _check_error
    helios_lib.setSourcePositionSpherical.errcheck = _check_error
    helios_lib.addRectangleRadiationSource.errcheck = _check_error
    helios_lib.addDiskRadiationSource.errcheck = _check_error

    # Source spectrum management
    helios_lib.setSourceSpectrum.errcheck = _check_error
    helios_lib.setSourceSpectrumMultiple.errcheck = _check_error
    helios_lib.setSourceSpectrumLabel.errcheck = _check_error
    helios_lib.setSourceSpectrumLabelMultiple.errcheck = _check_error
    helios_lib.setSourceSpectrumIntegral.errcheck = _check_error
    helios_lib.setSourceSpectrumIntegralRange.errcheck = _check_error

    # Spectrum integration functions
    helios_lib.integrateSpectrum.errcheck = _check_error
    helios_lib.integrateSpectrumRange.errcheck = _check_error
    helios_lib.integrateSpectrumWithSource.errcheck = _check_error
    helios_lib.integrateSpectrumWithCamera.errcheck = _check_error
    helios_lib.integrateSpectrumWithSourceAndCamera.errcheck = _check_error
    helios_lib.integrateSourceSpectrum.errcheck = _check_error

    # Spectral interpolation functions
    helios_lib.interpolateSpectrumFromPrimitiveData.errcheck = _check_error
    helios_lib.interpolateSpectrumFromObjectData.errcheck = _check_error

    # Spectral manipulation functions
    helios_lib.scaleSpectrumToNew.errcheck = _check_error
    helios_lib.scaleSpectrumInPlace.errcheck = _check_error
    helios_lib.scaleSpectrumRandomly.errcheck = _check_error
    helios_lib.blendSpectra.errcheck = _check_error
    helios_lib.blendSpectraRandomly.errcheck = _check_error

    # Advanced simulation functions
    helios_lib.getSkyEnergy.errcheck = _check_error
    helios_lib.calculateGtheta.errcheck = _check_error
    helios_lib.radiationOptionalOutputPrimitiveData.errcheck = _check_error
    helios_lib.enforcePeriodicBoundary.errcheck = _check_error

    # Camera and Image Functions
    helios_lib.writeCameraImage.errcheck = _check_error
    helios_lib.writeNormCameraImage.errcheck = _check_error
    helios_lib.writeCameraImageData.errcheck = _check_error

    # Bounding box functions
    helios_lib.writeImageBoundingBoxes.errcheck = _check_error
    helios_lib.writeImageBoundingBoxesVector.errcheck = _check_error
    helios_lib.writeImageBoundingBoxes_ObjectData.errcheck = _check_error
    helios_lib.writeImageBoundingBoxes_ObjectDataVector.errcheck = _check_error

    # Segmentation mask functions
    helios_lib.writeImageSegmentationMasks.errcheck = _check_error
    helios_lib.writeImageSegmentationMasksVector.errcheck = _check_error
    helios_lib.writeImageSegmentationMasks_ObjectData.errcheck = _check_error
    helios_lib.writeImageSegmentationMasks_ObjectDataVector.errcheck = _check_error

    # Auto-calibration function
    helios_lib.autoCalibrateCameraImage.errcheck = _check_error

    # Camera creation functions
    helios_lib.addRadiationCameraVec3.errcheck = _check_error
    helios_lib.addRadiationCameraSpherical.errcheck = _check_error

    # Camera management functions
    helios_lib.setRadiationCameraPosition.errcheck = _check_error
    helios_lib.getRadiationCameraPosition.errcheck = _check_error
    helios_lib.setCameraLookat.errcheck = _check_error
    helios_lib.getCameraLookat.errcheck = _check_error
    helios_lib.setCameraOrientationVec3.errcheck = _check_error
    helios_lib.setCameraOrientationSpherical.errcheck = _check_error
    helios_lib.getCameraOrientation.errcheck = _check_error
    helios_lib.getAllCameraLabels.errcheck = _check_error

    # Advanced camera functions
    helios_lib.setCameraSpectralResponse.errcheck = _check_error
    helios_lib.setCameraSpectralResponseFromLibrary.errcheck = _check_error
    helios_lib.getCameraPixelData.errcheck = _check_error
    helios_lib.setCameraPixelData.errcheck = _check_error

    # Camera Library Functions (v1.3.58+)
    helios_lib.addRadiationCameraFromLibrary.errcheck = _check_error
    helios_lib.addRadiationCameraFromLibraryWithBands.errcheck = _check_error
    helios_lib.updateCameraParameters.errcheck = _check_error
    helios_lib.enableCameraMetadata.errcheck = _check_error
    helios_lib.enableCameraMetadataMultiple.errcheck = _check_error

    # Mark that RadiationModel functions are available
    _RADIATION_MODEL_FUNCTIONS_AVAILABLE = True

except AttributeError:
    # RadiationModel functions not available in current native library
    _RADIATION_MODEL_FUNCTIONS_AVAILABLE = False

# Python wrapper functions

#=============================================================================
# Spectrum Conversion Helpers
#=============================================================================

def _spectrum_to_flat_array(spectrum):
    """
    Convert Python spectrum to flat float array for ctypes.

    Accepts:
    - List of tuples: [(wavelength1, value1), (wavelength2, value2), ...]
    - List of vec2: [vec2(w1,v1), vec2(w2,v2), ...]
    - List of lists: [[w1,v1], [w2,v2], ...]

    Returns:
    - (ctypes array, size) where array is [w1,v1,w2,v2,...] and size is number of points
    """
    if not spectrum:
        raise ValueError("Spectrum cannot be empty")

    flat_data = []
    for point in spectrum:
        if hasattr(point, 'x') and hasattr(point, 'y'):
            # vec2 object
            flat_data.extend([point.x, point.y])
        elif isinstance(point, (list, tuple)) and len(point) == 2:
            # List or tuple
            flat_data.extend([float(point[0]), float(point[1])])
        else:
            raise ValueError(f"Spectrum points must be vec2, tuple, or list of 2 elements. Got: {type(point)}")

    # Convert to ctypes array
    arr = (ctypes.c_float * len(flat_data))(*flat_data)
    return arr, len(spectrum)

def createRadiationModel(context):
    """Create a new RadiationModel instance"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        return None  # Return None for mock mode
    return helios_lib.createRadiationModel(context)

def destroyRadiationModel(radiation_model):
    """Destroy RadiationModel instance"""
    if radiation_model is None:
        return  # Destroying None is acceptable - no-op
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    helios_lib.destroyRadiationModel(radiation_model)

def disableMessages(radiation_model):
    """Disable RadiationModel status messages"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot disable messages.")
    helios_lib.disableRadiationMessages(radiation_model)

def enableMessages(radiation_model):
    """Enable RadiationModel status messages"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot enable messages.")
    helios_lib.enableRadiationMessages(radiation_model)

def addRadiationBand(radiation_model, label: str):
    """Add radiation band with label"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot add radiation band.")
    label_encoded = label.encode('utf-8')
    helios_lib.addRadiationBand(radiation_model, label_encoded)

def addRadiationBandWithWavelengths(radiation_model, label: str, wavelength_min: float, wavelength_max: float):
    """Add radiation band with wavelength bounds"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot add radiation band.")
    label_encoded = label.encode('utf-8')
    helios_lib.addRadiationBandWithWavelengths(radiation_model, label_encoded, wavelength_min, wavelength_max)

def copyRadiationBand(radiation_model, old_label: str, new_label: str, wavelength_min: float = None, wavelength_max: float = None):
    """Copy existing radiation band to new label, optionally with new wavelength range"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot copy radiation band.")
    old_encoded = old_label.encode('utf-8')
    new_encoded = new_label.encode('utf-8')

    if wavelength_min is not None and wavelength_max is not None:
        helios_lib.copyRadiationBandWithWavelengths(radiation_model, old_encoded, new_encoded,
                                                     wavelength_min, wavelength_max)
    else:
        helios_lib.copyRadiationBand(radiation_model, old_encoded, new_encoded)

def addCollimatedRadiationSourceDefault(radiation_model):
    """Add default collimated radiation source"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot create radiation source.")
    return helios_lib.addCollimatedRadiationSourceDefault(radiation_model)

def addCollimatedRadiationSourceVec3(radiation_model, x: float, y: float, z: float):
    """Add collimated radiation source with vec3 direction"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot create radiation source.")
    return helios_lib.addCollimatedRadiationSourceVec3(radiation_model, x, y, z)

def addCollimatedRadiationSourceSpherical(radiation_model, radius: float, zenith: float, azimuth: float):
    """Add collimated radiation source with spherical direction"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot create radiation source.")
    return helios_lib.addCollimatedRadiationSourceSpherical(radiation_model, radius, zenith, azimuth)

def addSphereRadiationSource(radiation_model, x: float, y: float, z: float, radius: float):
    """Add spherical radiation source"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot create radiation source.")
    return helios_lib.addSphereRadiationSource(radiation_model, x, y, z, radius)

def addSunSphereRadiationSource(radiation_model, radius: float, zenith: float, azimuth: float, 
                               position_scaling: float, angular_width: float, flux_scaling: float):
    """Add sun sphere radiation source"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot create radiation source.")
    return helios_lib.addSunSphereRadiationSource(radiation_model, radius, zenith, azimuth, 
                                                 position_scaling, angular_width, flux_scaling)

def setDirectRayCount(radiation_model, label: str, count: int):
    """Set direct ray count for band"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot set ray count.")
    label_encoded = label.encode('utf-8')
    helios_lib.setDirectRayCount(radiation_model, label_encoded, count)

def setDiffuseRayCount(radiation_model, label: str, count: int):
    """Set diffuse ray count for band"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot set ray count.")
    label_encoded = label.encode('utf-8')
    helios_lib.setDiffuseRayCount(radiation_model, label_encoded, count)

def setDiffuseRadiationFlux(radiation_model, label: str, flux: float):
    """Set diffuse radiation flux for band"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot set radiation flux.")
    label_encoded = label.encode('utf-8')
    helios_lib.setDiffuseRadiationFlux(radiation_model, label_encoded, flux)

#=============================================================================
# Advanced Diffuse Radiation Functions
#=============================================================================

def setDiffuseRadiationExtinctionCoeff(radiation_model, label: str, K: float, peak_direction):
    """Set diffuse radiation extinction coefficient (accepts vec3, SphericalCoord, or list)"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    label_encoded = label.encode('utf-8')

    # Handle different direction types
    if hasattr(peak_direction, 'radius'):  # SphericalCoord
        helios_lib.setDiffuseRadiationExtinctionCoeffSpherical(radiation_model, label_encoded, K,
                                                               peak_direction.radius, peak_direction.elevation,
                                                               peak_direction.azimuth)
    elif hasattr(peak_direction, 'x'):  # vec3
        helios_lib.setDiffuseRadiationExtinctionCoeffVec3(radiation_model, label_encoded, K,
                                                          peak_direction.x, peak_direction.y, peak_direction.z)
    else:  # list/tuple
        if len(peak_direction) == 3:
            helios_lib.setDiffuseRadiationExtinctionCoeffVec3(radiation_model, label_encoded, K,
                                                              peak_direction[0], peak_direction[1], peak_direction[2])
        else:
            raise ValueError("Peak direction must be vec3, SphericalCoord, or 3-element list/tuple")

def getDiffuseFlux(radiation_model, band_label: str) -> float:
    """Get diffuse flux for band"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    band_label_encoded = band_label.encode('utf-8')
    return helios_lib.getDiffuseFlux(radiation_model, band_label_encoded)

def setDiffuseSpectrum(radiation_model, band_label, spectrum_label: str):
    """
    Set diffuse spectrum from global data label.

    Args:
        band_label: Band label (string) or list of band labels
        spectrum_label: Spectrum global data label
    """
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    spectrum_encoded = spectrum_label.encode('utf-8')

    if isinstance(band_label, (list, tuple)):
        # Multiple bands
        label_array = (ctypes.c_char_p * len(band_label))(*[l.encode('utf-8') for l in band_label])
        helios_lib.setDiffuseSpectrumMultiple(radiation_model, label_array, len(band_label), spectrum_encoded)
    else:
        # Single band
        band_encoded = band_label.encode('utf-8')
        helios_lib.setDiffuseSpectrum(radiation_model, band_encoded, spectrum_encoded)

def setDiffuseSpectrumIntegral(radiation_model, spectrum_integral: float, wavelength_min: float = None,
                               wavelength_max: float = None, band_label: str = None):
    """
    Set diffuse spectrum integral (supports all bands or specific band, with optional wavelength range).

    Args:
        spectrum_integral: Integral value
        wavelength_min: Optional minimum wavelength
        wavelength_max: Optional maximum wavelength
        band_label: Optional specific band label (None for all bands)
    """
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    if band_label is not None:
        # Specific band
        band_encoded = band_label.encode('utf-8')
        if wavelength_min is not None and wavelength_max is not None:
            helios_lib.setDiffuseSpectrumIntegralBandRange(radiation_model, band_encoded, spectrum_integral,
                                                           wavelength_min, wavelength_max)
        else:
            helios_lib.setDiffuseSpectrumIntegralBand(radiation_model, band_encoded, spectrum_integral)
    else:
        # All bands
        if wavelength_min is not None and wavelength_max is not None:
            helios_lib.setDiffuseSpectrumIntegralAllRange(radiation_model, spectrum_integral,
                                                          wavelength_min, wavelength_max)
        else:
            helios_lib.setDiffuseSpectrumIntegralAll(radiation_model, spectrum_integral)

def setSourceFlux(radiation_model, source_id: int, label: str, flux: float):
    """Set source flux for single source"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot set source flux.")
    label_encoded = label.encode('utf-8')
    helios_lib.setSourceFlux(radiation_model, source_id, label_encoded, flux)

def setSourceFluxMultiple(radiation_model, source_ids: List[int], label: str, flux: float):
    """Set source flux for multiple sources"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot set source flux.")
    label_encoded = label.encode('utf-8')
    source_array = (ctypes.c_uint * len(source_ids))(*source_ids)
    helios_lib.setSourceFluxMultiple(radiation_model, source_array, len(source_ids), label_encoded, flux)

def getSourceFlux(radiation_model, source_id: int, label: str) -> float:
    """Get source flux for band"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot get source flux.")
    label_encoded = label.encode('utf-8')
    return helios_lib.getSourceFlux(radiation_model, source_id, label_encoded)

def setScatteringDepth(radiation_model, label: str, depth: int):
    """Set scattering depth for band"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot set scattering depth.")
    label_encoded = label.encode('utf-8')
    helios_lib.setScatteringDepth(radiation_model, label_encoded, depth)

def setMinScatterEnergy(radiation_model, label: str, energy: float):
    """Set minimum scatter energy for band"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot set scatter energy.")
    label_encoded = label.encode('utf-8')
    helios_lib.setMinScatterEnergy(radiation_model, label_encoded, energy)

def disableEmission(radiation_model, label: str):
    """Disable emission for band"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot disable emission.")
    label_encoded = label.encode('utf-8')
    helios_lib.disableEmission(radiation_model, label_encoded)

def enableEmission(radiation_model, label: str):
    """Enable emission for band"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot enable emission.")
    label_encoded = label.encode('utf-8')
    helios_lib.enableEmission(radiation_model, label_encoded)

def updateGeometry(radiation_model):
    """Update all geometry in radiation model"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot update geometry.")
    helios_lib.updateRadiationGeometry(radiation_model)

def updateGeometryUUIDs(radiation_model, uuids: List[int]):
    """Update specific geometry UUIDs in radiation model"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot update geometry.")
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.updateRadiationGeometryUUIDs(radiation_model, uuid_array, len(uuids))

def runBand(radiation_model, label: str):
    """Run simulation for single band"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot run simulation.")
    label_encoded = label.encode('utf-8')
    helios_lib.runRadiationBand(radiation_model, label_encoded)

def runBandMultiple(radiation_model, labels: List[str]):
    """Run simulation for multiple bands"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot run simulation.")
    # Convert list of strings to array of c_char_p
    encoded_labels = [label.encode('utf-8') for label in labels]
    label_array = (ctypes.c_char_p * len(encoded_labels))(*encoded_labels)
    helios_lib.runRadiationBandMultiple(radiation_model, label_array, len(encoded_labels))

def getTotalAbsorbedFlux(radiation_model) -> List[float]:
    """Get total absorbed flux for all primitives"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot get absorbed flux.")
    size = ctypes.c_size_t()
    flux_ptr = helios_lib.getTotalAbsorbedFlux(radiation_model, ctypes.byref(size))
    return list(flux_ptr[:size.value])

#=============================================================================
# Band Query Functions
#=============================================================================

def doesBandExist(radiation_model, label: str) -> bool:
    """Check if a radiation band exists"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")
    label_encoded = label.encode('utf-8')
    result = helios_lib.doesBandExist(radiation_model, label_encoded)
    if result == -1:
        raise RuntimeError("Error checking band existence.")
    return result == 1

#=============================================================================
# Advanced Source Management Functions
#=============================================================================

def deleteRadiationSource(radiation_model, source_id: int):
    """Delete a radiation source"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")
    helios_lib.deleteRadiationSource(radiation_model, source_id)

def getSourcePosition(radiation_model, source_id: int):
    """Get position of a radiation source as vec3"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")
    position = (ctypes.c_float * 3)()
    helios_lib.getSourcePosition(radiation_model, source_id, position)
    return [position[0], position[1], position[2]]

#=============================================================================
# Advanced Simulation Functions
#=============================================================================

def getSkyEnergy(radiation_model) -> float:
    """Get total sky energy"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")
    return helios_lib.getSkyEnergy(radiation_model)

def calculateGtheta(radiation_model, context, view_direction) -> float:
    """Calculate G-function (geometry factor) for given view direction"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None or context is None:
        raise ValueError("RadiationModel or Context instance is None.")
    # view_direction can be vec3 or list/tuple
    if hasattr(view_direction, 'x'):
        vx, vy, vz = view_direction.x, view_direction.y, view_direction.z
    else:
        vx, vy, vz = view_direction[0], view_direction[1], view_direction[2]
    return helios_lib.calculateGtheta(radiation_model, context, vx, vy, vz)

def optionalOutputPrimitiveData(radiation_model, label: str):
    """Enable optional primitive data output"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")
    label_encoded = label.encode('utf-8')
    helios_lib.radiationOptionalOutputPrimitiveData(radiation_model, label_encoded)

def enforcePeriodicBoundary(radiation_model, boundary: str):
    """Enforce periodic boundary conditions"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")
    boundary_encoded = boundary.encode('utf-8')
    helios_lib.enforcePeriodicBoundary(radiation_model, boundary_encoded)

def setSourcePosition(radiation_model, source_id: int, position):
    """Set position of a radiation source (accepts vec3, SphericalCoord, or list)"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    # Handle different position types
    if hasattr(position, 'radius'):  # SphericalCoord
        helios_lib.setSourcePositionSpherical(radiation_model, source_id,
                                              position.radius, position.elevation, position.azimuth)
    elif hasattr(position, 'x'):  # vec3
        helios_lib.setSourcePositionVec3(radiation_model, source_id,
                                         position.x, position.y, position.z)
    else:  # list/tuple
        if len(position) == 3:
            helios_lib.setSourcePositionVec3(radiation_model, source_id,
                                             position[0], position[1], position[2])
        else:
            raise ValueError("Position must be vec3, SphericalCoord, or 3-element list/tuple")

def addRectangleRadiationSource(radiation_model, position, size, rotation) -> int:
    """Add a rectangle radiation source"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    # Extract position components
    if hasattr(position, 'x'):
        px, py, pz = position.x, position.y, position.z
    else:
        px, py, pz = position[0], position[1], position[2]

    # Extract size components
    if hasattr(size, 'x'):
        sx, sy = size.x, size.y
    else:
        sx, sy = size[0], size[1]

    # Extract rotation components
    if hasattr(rotation, 'x'):
        rx, ry, rz = rotation.x, rotation.y, rotation.z
    else:
        rx, ry, rz = rotation[0], rotation[1], rotation[2]

    return helios_lib.addRectangleRadiationSource(radiation_model, px, py, pz, sx, sy, rx, ry, rz)

def addDiskRadiationSource(radiation_model, position, radius: float, rotation) -> int:
    """Add a disk radiation source"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    # Extract position components
    if hasattr(position, 'x'):
        px, py, pz = position.x, position.y, position.z
    else:
        px, py, pz = position[0], position[1], position[2]

    # Extract rotation components
    if hasattr(rotation, 'x'):
        rx, ry, rz = rotation.x, rotation.y, rotation.z
    else:
        rx, ry, rz = rotation[0], rotation[1], rotation[2]

    return helios_lib.addDiskRadiationSource(radiation_model, px, py, pz, radius, rx, ry, rz)

#=============================================================================
# Source Spectrum Management Functions
#=============================================================================

def setSourceSpectrum(radiation_model, source_id, spectrum):
    """
    Set source spectrum from spectrum data or label.

    Args:
        source_id: Source ID (int or list of ints)
        spectrum: Either:
            - Spectrum data as list of (wavelength, value) tuples/lists/vec2
            - Global data label string

    Example:
        >>> # Using spectrum data
        >>> spectrum = [(400, 0.1), (500, 0.5), (600, 0.8), (700, 0.3)]
        >>> radiation.setSourceSpectrum(source_id, spectrum)
        >>> # Using global data label
        >>> radiation.setSourceSpectrum(source_id, "D65_illuminant")
    """
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    # Check if spectrum is a string (label) or data
    if isinstance(spectrum, str):
        # Spectrum label case
        spectrum_label = spectrum.encode('utf-8')
        if isinstance(source_id, (list, tuple)):
            # Multiple sources
            source_array = (ctypes.c_uint * len(source_id))(*source_id)
            helios_lib.setSourceSpectrumLabelMultiple(radiation_model, source_array, len(source_id), spectrum_label)
        else:
            # Single source
            helios_lib.setSourceSpectrumLabel(radiation_model, source_id, spectrum_label)
    else:
        # Spectrum data case
        spectrum_array, spectrum_size = _spectrum_to_flat_array(spectrum)
        if isinstance(source_id, (list, tuple)):
            # Multiple sources
            source_array = (ctypes.c_uint * len(source_id))(*source_id)
            helios_lib.setSourceSpectrumMultiple(radiation_model, source_array, len(source_id),
                                                spectrum_array, spectrum_size)
        else:
            # Single source
            helios_lib.setSourceSpectrum(radiation_model, source_id, spectrum_array, spectrum_size)

def setSourceSpectrumIntegral(radiation_model, source_id: int, source_integral: float,
                              wavelength_min: float = None, wavelength_max: float = None):
    """Set source spectrum integral, optionally over wavelength range"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    if wavelength_min is not None and wavelength_max is not None:
        helios_lib.setSourceSpectrumIntegralRange(radiation_model, source_id, source_integral,
                                                   wavelength_min, wavelength_max)
    else:
        helios_lib.setSourceSpectrumIntegral(radiation_model, source_id, source_integral)

#=============================================================================
# Spectrum Integration Functions
#=============================================================================

def integrateSpectrum(radiation_model, object_spectrum, wavelength_min: float = None,
                     wavelength_max: float = None, source_id: int = None,
                     camera_spectrum=None) -> float:
    """
    Integrate spectrum with optional source/camera spectra and wavelength range.

    This is a unified function that handles multiple integration scenarios:
    - Basic integration: integrateSpectrum(model, spectrum)
    - Range integration: integrateSpectrum(model, spectrum, wmin, wmax)
    - With source: integrateSpectrum(model, spectrum, wmin, wmax, source_id=sid)
    - With camera: integrateSpectrum(model, spectrum, camera_spectrum=cam_spec)
    - Full integration: integrateSpectrum(model, spectrum, source_id=sid, camera_spectrum=cam_spec)

    Args:
        object_spectrum: Object spectrum as list of (wavelength, value) tuples/lists/vec2
        wavelength_min: Optional minimum wavelength
        wavelength_max: Optional maximum wavelength
        source_id: Optional source ID for source spectrum integration
        camera_spectrum: Optional camera spectrum for camera integration

    Returns:
        Integrated value

    Example:
        >>> spectrum = [(400, 0.1), (500, 0.5), (600, 0.8)]
        >>> total = radiation.integrateSpectrum(spectrum)
        >>> par = radiation.integrateSpectrum(spectrum, 400, 700)
    """
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    obj_array, obj_size = _spectrum_to_flat_array(object_spectrum)

    # Determine which variant to call based on parameters
    if source_id is not None and camera_spectrum is not None:
        # Source + camera integration
        cam_array, cam_size = _spectrum_to_flat_array(camera_spectrum)
        return helios_lib.integrateSpectrumWithSourceAndCamera(radiation_model, source_id,
                                                               obj_array, obj_size,
                                                               cam_array, cam_size)
    elif camera_spectrum is not None:
        # Camera integration only
        cam_array, cam_size = _spectrum_to_flat_array(camera_spectrum)
        return helios_lib.integrateSpectrumWithCamera(radiation_model, obj_array, obj_size,
                                                      cam_array, cam_size)
    elif source_id is not None:
        # Source integration with range
        if wavelength_min is None or wavelength_max is None:
            raise ValueError("wavelength_min and wavelength_max required when source_id is specified")
        return helios_lib.integrateSpectrumWithSource(radiation_model, source_id, obj_array, obj_size,
                                                      wavelength_min, wavelength_max)
    elif wavelength_min is not None and wavelength_max is not None:
        # Range integration
        return helios_lib.integrateSpectrumRange(radiation_model, obj_array, obj_size,
                                                 wavelength_min, wavelength_max)
    else:
        # Basic integration
        return helios_lib.integrateSpectrum(radiation_model, obj_array, obj_size)

def integrateSourceSpectrum(radiation_model, source_id: int, wavelength_min: float, wavelength_max: float) -> float:
    """Integrate source spectrum over wavelength range"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    return helios_lib.integrateSourceSpectrum(radiation_model, source_id, wavelength_min, wavelength_max)

#=============================================================================
# Spectral Interpolation Functions
#=============================================================================

def interpolateSpectrumFromPrimitiveData(radiation_model, primitive_uuids: List[int],
                                        spectra_labels: List[str], values: List[float],
                                        primitive_data_query_label: str,
                                        primitive_data_radprop_label: str):
    """Interpolate spectrum assignment based on primitive data values"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    if len(spectra_labels) != len(values):
        raise ValueError(f"Number of spectra ({len(spectra_labels)}) must match number of values ({len(values)})")

    # Convert to ctypes arrays
    uuid_array = (ctypes.c_uint * len(primitive_uuids))(*primitive_uuids)
    label_array = (ctypes.c_char_p * len(spectra_labels))(*[l.encode('utf-8') for l in spectra_labels])
    value_array = (ctypes.c_float * len(values))(*values)
    query_encoded = primitive_data_query_label.encode('utf-8')
    radprop_encoded = primitive_data_radprop_label.encode('utf-8')

    helios_lib.interpolateSpectrumFromPrimitiveData(radiation_model,
                                                    uuid_array, len(primitive_uuids),
                                                    label_array, len(spectra_labels),
                                                    value_array, len(values),
                                                    query_encoded, radprop_encoded)

def interpolateSpectrumFromObjectData(radiation_model, object_ids: List[int],
                                     spectra_labels: List[str], values: List[float],
                                     object_data_query_label: str,
                                     primitive_data_radprop_label: str):
    """Interpolate spectrum assignment based on object data values"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    if len(spectra_labels) != len(values):
        raise ValueError(f"Number of spectra ({len(spectra_labels)}) must match number of values ({len(values)})")

    # Convert to ctypes arrays
    id_array = (ctypes.c_uint * len(object_ids))(*object_ids)
    label_array = (ctypes.c_char_p * len(spectra_labels))(*[l.encode('utf-8') for l in spectra_labels])
    value_array = (ctypes.c_float * len(values))(*values)
    query_encoded = object_data_query_label.encode('utf-8')
    radprop_encoded = primitive_data_radprop_label.encode('utf-8')

    helios_lib.interpolateSpectrumFromObjectData(radiation_model,
                                                 id_array, len(object_ids),
                                                 label_array, len(spectra_labels),
                                                 value_array, len(values),
                                                 query_encoded, radprop_encoded)

#=============================================================================
# Spectral Manipulation Functions
#=============================================================================

def scaleSpectrum(radiation_model, existing_label: str, new_label_or_scale, scale_factor: float = None):
    """
    Scale spectrum in-place or to new label.

    Supports two call patterns:
    - scaleSpectrum(model, "label", scale) -> scales in-place
    - scaleSpectrum(model, "existing", "new", scale) -> creates new scaled spectrum

    Args:
        existing_label: Existing global data label
        new_label_or_scale: Either new label string or scale factor
        scale_factor: Scale factor (only if new_label_or_scale is a string)

    Example:
        >>> radiation.scaleSpectrum("leaf_reflectance", 1.2)  # In-place
        >>> radiation.scaleSpectrum("leaf_reflectance", "scaled_leaf", 1.5)  # New label
    """
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    existing_encoded = existing_label.encode('utf-8')

    if scale_factor is None:
        # In-place scaling: scaleSpectrum(label, scale_factor)
        helios_lib.scaleSpectrumInPlace(radiation_model, existing_encoded, new_label_or_scale)
    else:
        # New label scaling: scaleSpectrum(existing, new, scale_factor)
        new_encoded = new_label_or_scale.encode('utf-8')
        helios_lib.scaleSpectrumToNew(radiation_model, existing_encoded, new_encoded, scale_factor)

def scaleSpectrumRandomly(radiation_model, existing_label: str, new_label: str,
                         min_scale: float, max_scale: float):
    """Scale spectrum with random factor and store as new label"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    existing_encoded = existing_label.encode('utf-8')
    new_encoded = new_label.encode('utf-8')
    helios_lib.scaleSpectrumRandomly(radiation_model, existing_encoded, new_encoded, min_scale, max_scale)

def blendSpectra(radiation_model, new_label: str, spectrum_labels: List[str], weights: List[float]):
    """Blend multiple spectra with given weights"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    if len(spectrum_labels) != len(weights):
        raise ValueError(f"Number of labels ({len(spectrum_labels)}) must match number of weights ({len(weights)})")

    new_encoded = new_label.encode('utf-8')
    label_array = (ctypes.c_char_p * len(spectrum_labels))(*[l.encode('utf-8') for l in spectrum_labels])
    weight_array = (ctypes.c_float * len(weights))(*weights)

    helios_lib.blendSpectra(radiation_model, new_encoded, label_array, len(spectrum_labels), weight_array)

def blendSpectraRandomly(radiation_model, new_label: str, spectrum_labels: List[str]):
    """Blend multiple spectra with random weights"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    new_encoded = new_label.encode('utf-8')
    label_array = (ctypes.c_char_p * len(spectrum_labels))(*[l.encode('utf-8') for l in spectrum_labels])

    helios_lib.blendSpectraRandomly(radiation_model, new_encoded, label_array, len(spectrum_labels))

#=============================================================================
# Camera Management Functions
#=============================================================================

def setCameraPosition(radiation_model, camera_label: str, position):
    """Set camera position (accepts vec3 or list)"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    camera_label_encoded = camera_label.encode('utf-8')

    if hasattr(position, 'x'):
        x, y, z = position.x, position.y, position.z
    else:
        x, y, z = position[0], position[1], position[2]

    helios_lib.setRadiationCameraPosition(radiation_model, camera_label_encoded, x, y, z)

def getCameraPosition(radiation_model, camera_label: str):
    """Get camera position as list [x, y, z]"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    camera_label_encoded = camera_label.encode('utf-8')
    position = (ctypes.c_float * 3)()
    helios_lib.getRadiationCameraPosition(radiation_model, camera_label_encoded, position)
    return [position[0], position[1], position[2]]

def setCameraLookat(radiation_model, camera_label: str, lookat):
    """Set camera lookat point (accepts vec3 or list)"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    camera_label_encoded = camera_label.encode('utf-8')

    if hasattr(lookat, 'x'):
        x, y, z = lookat.x, lookat.y, lookat.z
    else:
        x, y, z = lookat[0], lookat[1], lookat[2]

    helios_lib.setCameraLookat(radiation_model, camera_label_encoded, x, y, z)

def getCameraLookat(radiation_model, camera_label: str):
    """Get camera lookat point as list [x, y, z]"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    camera_label_encoded = camera_label.encode('utf-8')
    lookat = (ctypes.c_float * 3)()
    helios_lib.getCameraLookat(radiation_model, camera_label_encoded, lookat)
    return [lookat[0], lookat[1], lookat[2]]

def setCameraOrientation(radiation_model, camera_label: str, direction):
    """Set camera orientation (accepts vec3, SphericalCoord, or list)"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    camera_label_encoded = camera_label.encode('utf-8')

    # Handle different direction types
    if hasattr(direction, 'radius'):  # SphericalCoord
        helios_lib.setCameraOrientationSpherical(radiation_model, camera_label_encoded,
                                                 direction.radius, direction.elevation, direction.azimuth)
    elif hasattr(direction, 'x'):  # vec3
        helios_lib.setCameraOrientationVec3(radiation_model, camera_label_encoded,
                                            direction.x, direction.y, direction.z)
    else:  # list/tuple - assume vec3
        if len(direction) == 3:
            helios_lib.setCameraOrientationVec3(radiation_model, camera_label_encoded,
                                                direction[0], direction[1], direction[2])
        else:
            raise ValueError("Direction must be vec3, SphericalCoord, or 3-element list/tuple")

def getCameraOrientation(radiation_model, camera_label: str):
    """Get camera orientation as list [radius, elevation, azimuth] (spherical coords)"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    camera_label_encoded = camera_label.encode('utf-8')
    orientation = (ctypes.c_float * 3)()
    helios_lib.getCameraOrientation(radiation_model, camera_label_encoded, orientation)
    return [orientation[0], orientation[1], orientation[2]]

def getAllCameraLabels(radiation_model) -> List[str]:
    """Get all camera labels"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    count = ctypes.c_size_t()
    labels_ptr = helios_lib.getAllCameraLabels(radiation_model, ctypes.byref(count))

    if labels_ptr is None or count.value == 0:
        return []

    # Convert array of C strings to Python list of strings
    return [labels_ptr[i].decode('utf-8') for i in range(count.value)]

#=============================================================================
# Advanced Camera Functions
#=============================================================================

def setCameraSpectralResponse(radiation_model, camera_label: str, band_label: str, global_data: str):
    """Set camera spectral response from global data"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    camera_encoded = camera_label.encode('utf-8')
    band_encoded = band_label.encode('utf-8')
    data_encoded = global_data.encode('utf-8')
    helios_lib.setCameraSpectralResponse(radiation_model, camera_encoded, band_encoded, data_encoded)

def setCameraSpectralResponseFromLibrary(radiation_model, camera_label: str, camera_library_name: str):
    """Set camera spectral response from standard camera library"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    camera_encoded = camera_label.encode('utf-8')
    library_encoded = camera_library_name.encode('utf-8')
    helios_lib.setCameraSpectralResponseFromLibrary(radiation_model, camera_encoded, library_encoded)

def getCameraPixelData(radiation_model, camera_label: str, band_label: str) -> List[float]:
    """Get camera pixel data for specific band"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    camera_encoded = camera_label.encode('utf-8')
    band_encoded = band_label.encode('utf-8')
    size = ctypes.c_size_t()
    pixel_ptr = helios_lib.getCameraPixelData(radiation_model, camera_encoded, band_encoded, ctypes.byref(size))

    if pixel_ptr is None or size.value == 0:
        return []

    return list(pixel_ptr[:size.value])

def setCameraPixelData(radiation_model, camera_label: str, band_label: str, pixel_data: List[float]):
    """Set camera pixel data for specific band"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    camera_encoded = camera_label.encode('utf-8')
    band_encoded = band_label.encode('utf-8')
    pixel_array = (ctypes.c_float * len(pixel_data))(*pixel_data)
    helios_lib.setCameraPixelData(radiation_model, camera_encoded, band_encoded, pixel_array, len(pixel_data))

#=============================================================================
# Camera Library Functions (v1.3.58+)
#=============================================================================

def addRadiationCameraFromLibrary(radiation_model, camera_label: str, library_camera_label: str,
                                   position, lookat, antialiasing_samples: int, band_labels: List[str] = None):
    """
    Add radiation camera loading all properties from camera library.

    Loads camera intrinsic parameters (resolution, FOV, sensor size) and spectral
    response data from the camera library XML file. If band_labels is provided, uses
    custom band names; otherwise uses default band names from library.

    Args:
        radiation_model: RadiationModel instance
        camera_label: Label for the camera instance
        library_camera_label: Label of camera in library (e.g., "Canon_20D", "iPhone11", "NikonD700")
        position: Camera position as vec3 or (x, y, z) tuple
        lookat: Lookat point as vec3 or (x, y, z) tuple
        antialiasing_samples: Number of ray samples per pixel (minimum 1)
        band_labels: Optional custom band labels. If None, uses library defaults.

    Raises:
        RuntimeError: If RadiationModel functions not available or operation fails
        ValueError: If parameters are invalid

    Note:
        Available cameras in plugins/radiation/camera_library/camera_library.xml
        include: Canon_20D, Nikon_D700, Nikon_D50, iPhone11, iPhone12ProMAX
    """
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    camera_encoded = camera_label.encode('utf-8')
    library_encoded = library_camera_label.encode('utf-8')

    # Convert position and lookat to floats
    if hasattr(position, 'x'):
        pos_x, pos_y, pos_z = position.x, position.y, position.z
    else:
        pos_x, pos_y, pos_z = position[0], position[1], position[2]

    if hasattr(lookat, 'x'):
        look_x, look_y, look_z = lookat.x, lookat.y, lookat.z
    else:
        look_x, look_y, look_z = lookat[0], lookat[1], lookat[2]

    if band_labels is None:
        # Use basic version without custom bands
        helios_lib.addRadiationCameraFromLibrary(
            radiation_model, camera_encoded, library_encoded,
            ctypes.c_float(pos_x), ctypes.c_float(pos_y), ctypes.c_float(pos_z),
            ctypes.c_float(look_x), ctypes.c_float(look_y), ctypes.c_float(look_z),
            ctypes.c_uint(antialiasing_samples)
        )
    else:
        # Use version with custom band labels
        band_array = (ctypes.c_char_p * len(band_labels))()
        for i, band in enumerate(band_labels):
            band_array[i] = band.encode('utf-8')

        helios_lib.addRadiationCameraFromLibraryWithBands(
            radiation_model, camera_encoded, library_encoded,
            ctypes.c_float(pos_x), ctypes.c_float(pos_y), ctypes.c_float(pos_z),
            ctypes.c_float(look_x), ctypes.c_float(look_y), ctypes.c_float(look_z),
            ctypes.c_uint(antialiasing_samples),
            band_array, len(band_labels)
        )

def updateCameraParameters(radiation_model, camera_label: str, camera_properties):
    """
    Update camera parameters for an existing camera.

    Args:
        radiation_model: RadiationModel instance
        camera_label: Label for the camera to update
        camera_properties: CameraProperties instance or list of 9 floats

    Raises:
        RuntimeError: If RadiationModel functions not available or operation fails
        ValueError: If parameters are invalid

    Note:
        Preserves the camera's position, lookat direction, and spectral band configuration.
        FOV_aspect_ratio is recalculated from resolution.
    """
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    camera_encoded = camera_label.encode('utf-8')

    # Convert CameraProperties to array if needed
    if hasattr(camera_properties, 'to_array'):
        props_array = camera_properties.to_array()
    else:
        props_array = camera_properties

    if len(props_array) != 10:
        raise ValueError(f"Camera properties must have 10 elements, got {len(props_array)}")

    props_c = (ctypes.c_float * 9)(*props_array)
    helios_lib.updateCameraParameters(radiation_model, camera_encoded, props_c)

def enableCameraMetadata(radiation_model, camera_labels):
    """
    Enable automatic JSON metadata file writing for camera(s).

    After calling this method, writeCameraImage() will automatically create a JSON
    metadata file alongside the image containing camera properties, location, acquisition
    settings, and agronomic data.

    Args:
        radiation_model: RadiationModel instance
        camera_labels: Single camera label (str) or list of camera labels (List[str])

    Raises:
        RuntimeError: If RadiationModel functions not available or operation fails
        ValueError: If parameters are invalid

    Note:
        Metadata is automatically populated from camera properties and simulation context.
        Use getCameraMetadata() and setCameraMetadata() to customize metadata.
    """
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None.")

    # Handle both single camera and multiple cameras
    if isinstance(camera_labels, str):
        # Single camera
        camera_encoded = camera_labels.encode('utf-8')
        helios_lib.enableCameraMetadata(radiation_model, camera_encoded)
    elif isinstance(camera_labels, (list, tuple)):
        # Multiple cameras
        if not camera_labels:
            raise ValueError("Camera labels list cannot be empty")

        labels_array = (ctypes.c_char_p * len(camera_labels))()
        for i, label in enumerate(camera_labels):
            labels_array[i] = label.encode('utf-8')

        helios_lib.enableCameraMetadataMultiple(radiation_model, labels_array, len(camera_labels))
    else:
        raise ValueError("camera_labels must be a string or list of strings")

#=============================================================================
# Camera and Image Functions (v1.3.47)
#=============================================================================

def writeCameraImage(radiation_model, camera: str, bands: List[str], imagefile_base: str, 
                     image_path: str = "./", frame: int = -1, flux_to_pixel_conversion: float = 1.0) -> str:
    """Write camera image to file and return output filename"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot write camera image.")
    
    camera_encoded = camera.encode('utf-8')
    imagefile_base_encoded = imagefile_base.encode('utf-8')
    image_path_encoded = image_path.encode('utf-8')
    
    # Convert band list to ctypes array
    band_array = (ctypes.c_char_p * len(bands))()
    for i, band in enumerate(bands):
        band_array[i] = band.encode('utf-8')
    
    result = helios_lib.writeCameraImage(radiation_model, camera_encoded, band_array, len(bands),
                                        imagefile_base_encoded, image_path_encoded, frame, flux_to_pixel_conversion)
    return result.decode('utf-8') if result else ""

def writeNormCameraImage(radiation_model, camera: str, bands: List[str], imagefile_base: str, 
                         image_path: str = "./", frame: int = -1) -> str:
    """Write normalized camera image to file and return output filename"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot write normalized camera image.")
    
    camera_encoded = camera.encode('utf-8')
    imagefile_base_encoded = imagefile_base.encode('utf-8')
    image_path_encoded = image_path.encode('utf-8')
    
    # Convert band list to ctypes array
    band_array = (ctypes.c_char_p * len(bands))()
    for i, band in enumerate(bands):
        band_array[i] = band.encode('utf-8')
    
    result = helios_lib.writeNormCameraImage(radiation_model, camera_encoded, band_array, len(bands),
                                            imagefile_base_encoded, image_path_encoded, frame)
    return result.decode('utf-8') if result else ""

def writeCameraImageData(radiation_model, camera: str, band: str, imagefile_base: str, 
                         image_path: str = "./", frame: int = -1):
    """Write camera image data to file (ASCII format)"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot write camera image data.")
    
    camera_encoded = camera.encode('utf-8')
    band_encoded = band.encode('utf-8')
    imagefile_base_encoded = imagefile_base.encode('utf-8')
    image_path_encoded = image_path.encode('utf-8')
    
    helios_lib.writeCameraImageData(radiation_model, camera_encoded, band_encoded,
                                   imagefile_base_encoded, image_path_encoded, frame)

# Bounding box functions
def writeImageBoundingBoxes(radiation_model, camera_label: str, primitive_data_label: str, 
                           object_class_id: int, image_file: str, classes_txt_file: str = "classes.txt", 
                           image_path: str = "./"):
    """Write image bounding boxes (single primitive data label)"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot write bounding boxes.")
    
    camera_encoded = camera_label.encode('utf-8')
    primitive_encoded = primitive_data_label.encode('utf-8')
    image_file_encoded = image_file.encode('utf-8')
    classes_encoded = classes_txt_file.encode('utf-8')
    image_path_encoded = image_path.encode('utf-8')
    
    helios_lib.writeImageBoundingBoxes(radiation_model, camera_encoded, primitive_encoded, object_class_id,
                                      image_file_encoded, classes_encoded, image_path_encoded)

def writeImageBoundingBoxesVector(radiation_model, camera_label: str, primitive_data_labels: List[str], 
                                  object_class_ids: List[int], image_file: str, 
                                  classes_txt_file: str = "classes.txt", image_path: str = "./"):
    """Write image bounding boxes (vector primitive data labels)"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot write vector bounding boxes.")
    
    if len(primitive_data_labels) != len(object_class_ids):
        raise ValueError("primitive_data_labels and object_class_ids must have the same length")
    
    camera_encoded = camera_label.encode('utf-8')
    image_file_encoded = image_file.encode('utf-8')
    classes_encoded = classes_txt_file.encode('utf-8')
    image_path_encoded = image_path.encode('utf-8')
    
    # Convert lists to ctypes arrays
    label_array = (ctypes.c_char_p * len(primitive_data_labels))()
    for i, label in enumerate(primitive_data_labels):
        label_array[i] = label.encode('utf-8')
    
    id_array = (ctypes.c_uint * len(object_class_ids))(*object_class_ids)
    
    helios_lib.writeImageBoundingBoxesVector(radiation_model, camera_encoded, label_array, len(primitive_data_labels),
                                            id_array, image_file_encoded, classes_encoded, image_path_encoded)

def writeImageBoundingBoxes_ObjectData(radiation_model, camera_label: str, object_data_label: str, 
                                       object_class_id: int, image_file: str, 
                                       classes_txt_file: str = "classes.txt", image_path: str = "./"):
    """Write image bounding boxes with object data (single label)"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot write object bounding boxes.")
    
    camera_encoded = camera_label.encode('utf-8')
    object_encoded = object_data_label.encode('utf-8')
    image_file_encoded = image_file.encode('utf-8')
    classes_encoded = classes_txt_file.encode('utf-8')
    image_path_encoded = image_path.encode('utf-8')
    
    helios_lib.writeImageBoundingBoxes_ObjectData(radiation_model, camera_encoded, object_encoded, object_class_id,
                                                 image_file_encoded, classes_encoded, image_path_encoded)

def writeImageBoundingBoxes_ObjectDataVector(radiation_model, camera_label: str, object_data_labels: List[str], 
                                             object_class_ids: List[int], image_file: str, 
                                             classes_txt_file: str = "classes.txt", image_path: str = "./"):
    """Write image bounding boxes with object data (vector labels)"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot write vector object bounding boxes.")
    
    if len(object_data_labels) != len(object_class_ids):
        raise ValueError("object_data_labels and object_class_ids must have the same length")
    
    camera_encoded = camera_label.encode('utf-8')
    image_file_encoded = image_file.encode('utf-8')
    classes_encoded = classes_txt_file.encode('utf-8')
    image_path_encoded = image_path.encode('utf-8')
    
    # Convert lists to ctypes arrays
    label_array = (ctypes.c_char_p * len(object_data_labels))()
    for i, label in enumerate(object_data_labels):
        label_array[i] = label.encode('utf-8')
    
    id_array = (ctypes.c_uint * len(object_class_ids))(*object_class_ids)
    
    helios_lib.writeImageBoundingBoxes_ObjectDataVector(radiation_model, camera_encoded, label_array, len(object_data_labels),
                                                       id_array, image_file_encoded, classes_encoded, image_path_encoded)

# Segmentation mask functions
def writeImageSegmentationMasks(radiation_model, camera_label: str, primitive_data_label: str, 
                               object_class_id: int, json_filename: str, image_file: str, append_file: bool = False):
    """Write image segmentation masks (single primitive data label)"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot write segmentation masks.")
    
    camera_encoded = camera_label.encode('utf-8')
    primitive_encoded = primitive_data_label.encode('utf-8')
    json_encoded = json_filename.encode('utf-8')
    image_file_encoded = image_file.encode('utf-8')
    
    helios_lib.writeImageSegmentationMasks(radiation_model, camera_encoded, primitive_encoded, object_class_id,
                                          json_encoded, image_file_encoded, int(append_file))

def writeImageSegmentationMasksVector(radiation_model, camera_label: str, primitive_data_labels: List[str], 
                                      object_class_ids: List[int], json_filename: str, image_file: str, 
                                      append_file: bool = False):
    """Write image segmentation masks (vector primitive data labels)"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot write vector segmentation masks.")
    
    if len(primitive_data_labels) != len(object_class_ids):
        raise ValueError("primitive_data_labels and object_class_ids must have the same length")
    
    camera_encoded = camera_label.encode('utf-8')
    json_encoded = json_filename.encode('utf-8')
    image_file_encoded = image_file.encode('utf-8')
    
    # Convert lists to ctypes arrays
    label_array = (ctypes.c_char_p * len(primitive_data_labels))()
    for i, label in enumerate(primitive_data_labels):
        label_array[i] = label.encode('utf-8')
    
    id_array = (ctypes.c_uint * len(object_class_ids))(*object_class_ids)
    
    helios_lib.writeImageSegmentationMasksVector(radiation_model, camera_encoded, label_array, len(primitive_data_labels),
                                                id_array, json_encoded, image_file_encoded, int(append_file))

def writeImageSegmentationMasks_ObjectData(radiation_model, camera_label: str, object_data_label: str, 
                                           object_class_id: int, json_filename: str, image_file: str, 
                                           append_file: bool = False):
    """Write image segmentation masks with object data (single label)"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot write object segmentation masks.")
    
    camera_encoded = camera_label.encode('utf-8')
    object_encoded = object_data_label.encode('utf-8')
    json_encoded = json_filename.encode('utf-8')
    image_file_encoded = image_file.encode('utf-8')
    
    helios_lib.writeImageSegmentationMasks_ObjectData(radiation_model, camera_encoded, object_encoded, object_class_id,
                                                     json_encoded, image_file_encoded, int(append_file))

def writeImageSegmentationMasks_ObjectDataVector(radiation_model, camera_label: str, object_data_labels: List[str], 
                                                 object_class_ids: List[int], json_filename: str, image_file: str, 
                                                 append_file: bool = False):
    """Write image segmentation masks with object data (vector labels)"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot write vector object segmentation masks.")
    
    if len(object_data_labels) != len(object_class_ids):
        raise ValueError("object_data_labels and object_class_ids must have the same length")
    
    camera_encoded = camera_label.encode('utf-8')
    json_encoded = json_filename.encode('utf-8')
    image_file_encoded = image_file.encode('utf-8')
    
    # Convert lists to ctypes arrays
    label_array = (ctypes.c_char_p * len(object_data_labels))()
    for i, label in enumerate(object_data_labels):
        label_array[i] = label.encode('utf-8')
    
    id_array = (ctypes.c_uint * len(object_class_ids))(*object_class_ids)
    
    helios_lib.writeImageSegmentationMasks_ObjectDataVector(radiation_model, camera_encoded, label_array, len(object_data_labels),
                                                           id_array, json_encoded, image_file_encoded, int(append_file))

# Auto-calibration function
def autoCalibrateCameraImage(radiation_model, camera_label: str, red_band_label: str, green_band_label: str, 
                            blue_band_label: str, output_file_path: str, print_quality_report: bool = False, 
                            algorithm: int = 1, ccm_export_file_path: str = "") -> str:
    """Auto-calibrate camera image with color correction and return output filename"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot auto-calibrate camera image.")
    
    camera_encoded = camera_label.encode('utf-8')
    red_encoded = red_band_label.encode('utf-8')
    green_encoded = green_band_label.encode('utf-8')
    blue_encoded = blue_band_label.encode('utf-8')
    output_encoded = output_file_path.encode('utf-8')
    ccm_encoded = ccm_export_file_path.encode('utf-8') if ccm_export_file_path else None
    
    result = helios_lib.autoCalibrateCameraImage(radiation_model, camera_encoded, red_encoded, green_encoded,
                                               blue_encoded, output_encoded, int(print_quality_report),
                                               algorithm, ccm_encoded)
    return result.decode('utf-8') if result else ""

# Camera creation functions
def addRadiationCameraVec3(radiation_model, camera_label: str, band_labels: List[str],
                          position_x: float, position_y: float, position_z: float,
                          lookat_x: float, lookat_y: float, lookat_z: float,
                          camera_properties: List[float], antialiasing_samples: int):
    """Add radiation camera with position and lookat vectors"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot add radiation camera.")

    if not band_labels:
        raise ValueError("At least one band label is required")
    if len(camera_properties) != 10:
        raise ValueError("camera_properties must contain exactly 10 values: [resolution_x, resolution_y, focal_distance, lens_diameter, HFOV, FOV_aspect_ratio, lens_focal_length, sensor_width_mm, shutter_speed, zoom]")

    # Encode camera label
    camera_encoded = camera_label.encode('utf-8')

    # Convert band labels to ctypes array
    band_array = (ctypes.c_char_p * len(band_labels))()
    for i, label in enumerate(band_labels):
        band_array[i] = label.encode('utf-8')

    # Convert camera properties to ctypes array
    props_array = (ctypes.c_float * len(camera_properties))(*camera_properties)

    helios_lib.addRadiationCameraVec3(radiation_model, camera_encoded, band_array, len(band_labels),
                                     ctypes.c_float(position_x), ctypes.c_float(position_y), ctypes.c_float(position_z),
                                     ctypes.c_float(lookat_x), ctypes.c_float(lookat_y), ctypes.c_float(lookat_z),
                                     props_array, ctypes.c_uint(antialiasing_samples))

def addRadiationCameraSpherical(radiation_model, camera_label: str, band_labels: List[str],
                               position_x: float, position_y: float, position_z: float,
                               radius: float, elevation: float, azimuth: float,
                               camera_properties: List[float], antialiasing_samples: int):
    """Add radiation camera with position and spherical viewing direction"""
    if not _RADIATION_MODEL_FUNCTIONS_AVAILABLE:
        raise RuntimeError("RadiationModel functions are not available. Native library missing or radiation plugin not enabled.")
    if radiation_model is None:
        raise ValueError("RadiationModel instance is None. Cannot add radiation camera.")

    if not band_labels:
        raise ValueError("At least one band label is required")
    if len(camera_properties) != 9:
        raise ValueError("camera_properties must contain exactly 9 values: [resolution_x, resolution_y, focal_distance, lens_diameter, HFOV, FOV_aspect_ratio, lens_focal_length, sensor_width_mm, shutter_speed]")

    # Encode camera label
    camera_encoded = camera_label.encode('utf-8')

    # Convert band labels to ctypes array
    band_array = (ctypes.c_char_p * len(band_labels))()
    for i, label in enumerate(band_labels):
        band_array[i] = label.encode('utf-8')

    # Convert camera properties to ctypes array
    props_array = (ctypes.c_float * len(camera_properties))(*camera_properties)

    helios_lib.addRadiationCameraSpherical(radiation_model, camera_encoded, band_array, len(band_labels),
                                          ctypes.c_float(position_x), ctypes.c_float(position_y), ctypes.c_float(position_z),
                                          ctypes.c_float(radius), ctypes.c_float(elevation), ctypes.c_float(azimuth),
                                          props_array, ctypes.c_uint(antialiasing_samples))

