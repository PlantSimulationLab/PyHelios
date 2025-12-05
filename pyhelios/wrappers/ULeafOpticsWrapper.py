"""
Ctypes wrapper for LeafOptics C++ bindings.

This module provides low-level ctypes bindings to interface with
the native Helios LeafOptics plugin (PROSPECT model) via the C++ wrapper layer.
"""

import ctypes
from typing import List, Tuple

from ..plugins import helios_lib
from ..exceptions import check_helios_error

# Define the ULeafOptics struct
class ULeafOptics(ctypes.Structure):
    """Opaque structure for LeafOptics C++ class"""
    pass

# Import UContext from main wrapper to avoid type conflicts
from .UContextWrapper import UContext

# Number of properties in LeafOpticsProperties struct
LEAF_OPTICS_PROPERTIES_COUNT = 9

# Number of spectral points (400-2500 nm at 1nm resolution)
LEAF_OPTICS_SPECTRAL_POINTS = 2101

# Error checking callback
def _check_error(result, func, args):
    """Automatic error checking for all leaf optics functions"""
    check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage)
    return result

# Try to set up LeafOptics function prototypes
try:
    # LeafOptics creation and destruction
    helios_lib.createLeafOptics.argtypes = [ctypes.POINTER(UContext)]
    helios_lib.createLeafOptics.restype = ctypes.POINTER(ULeafOptics)
    helios_lib.createLeafOptics.errcheck = _check_error

    helios_lib.destroyLeafOptics.argtypes = [ctypes.POINTER(ULeafOptics)]
    helios_lib.destroyLeafOptics.restype = None

    # Model execution
    helios_lib.leafOpticsRun.argtypes = [
        ctypes.POINTER(ULeafOptics),
        ctypes.POINTER(ctypes.c_uint),
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_char_p
    ]
    helios_lib.leafOpticsRun.restype = None
    helios_lib.leafOpticsRun.errcheck = _check_error

    helios_lib.leafOpticsRunNoUUIDs.argtypes = [
        ctypes.POINTER(ULeafOptics),
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_char_p
    ]
    helios_lib.leafOpticsRunNoUUIDs.restype = None
    helios_lib.leafOpticsRunNoUUIDs.errcheck = _check_error

    # Spectral data retrieval
    helios_lib.leafOpticsGetLeafSpectra.argtypes = [
        ctypes.POINTER(ULeafOptics),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_uint)
    ]
    helios_lib.leafOpticsGetLeafSpectra.restype = None
    helios_lib.leafOpticsGetLeafSpectra.errcheck = _check_error

    # Property management
    helios_lib.leafOpticsSetProperties.argtypes = [
        ctypes.POINTER(ULeafOptics),
        ctypes.POINTER(ctypes.c_uint),
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_float)
    ]
    helios_lib.leafOpticsSetProperties.restype = None
    helios_lib.leafOpticsSetProperties.errcheck = _check_error

    helios_lib.leafOpticsGetPropertiesFromSpectrum.argtypes = [
        ctypes.POINTER(ULeafOptics),
        ctypes.POINTER(ctypes.c_uint),
        ctypes.c_uint
    ]
    helios_lib.leafOpticsGetPropertiesFromSpectrum.restype = None
    helios_lib.leafOpticsGetPropertiesFromSpectrum.errcheck = _check_error

    helios_lib.leafOpticsGetPropertiesFromSpectrumSingle.argtypes = [
        ctypes.POINTER(ULeafOptics),
        ctypes.c_uint
    ]
    helios_lib.leafOpticsGetPropertiesFromSpectrumSingle.restype = None
    helios_lib.leafOpticsGetPropertiesFromSpectrumSingle.errcheck = _check_error

    # Species library
    helios_lib.leafOpticsGetPropertiesFromLibrary.argtypes = [
        ctypes.POINTER(ULeafOptics),
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_float)
    ]
    helios_lib.leafOpticsGetPropertiesFromLibrary.restype = None
    helios_lib.leafOpticsGetPropertiesFromLibrary.errcheck = _check_error

    # Message control
    helios_lib.leafOpticsDisableMessages.argtypes = [ctypes.POINTER(ULeafOptics)]
    helios_lib.leafOpticsDisableMessages.restype = None
    helios_lib.leafOpticsDisableMessages.errcheck = _check_error

    helios_lib.leafOpticsEnableMessages.argtypes = [ctypes.POINTER(ULeafOptics)]
    helios_lib.leafOpticsEnableMessages.restype = None
    helios_lib.leafOpticsEnableMessages.errcheck = _check_error

    # Optional output primitive data (v1.3.59)
    helios_lib.leafOpticsOptionalOutputPrimitiveData.argtypes = [ctypes.POINTER(ULeafOptics), ctypes.c_char_p]
    helios_lib.leafOpticsOptionalOutputPrimitiveData.restype = None
    helios_lib.leafOpticsOptionalOutputPrimitiveData.errcheck = _check_error

    _LEAFOPTICS_FUNCTIONS_AVAILABLE = True

except AttributeError:
    _LEAFOPTICS_FUNCTIONS_AVAILABLE = False


# Wrapper functions

def createLeafOptics(context: ctypes.POINTER(UContext)) -> ctypes.POINTER(ULeafOptics):
    """Create LeafOptics instance

    Args:
        context: Pointer to the Helios Context

    Returns:
        Pointer to the created LeafOptics instance

    Raises:
        NotImplementedError: If LeafOptics functions not available
        ValueError: If context is None
    """
    if not _LEAFOPTICS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "LeafOptics functions not available in current Helios library. "
            "Rebuild PyHelios with 'leafoptics' enabled:\n"
            "  build_scripts/build_helios --plugins leafoptics"
        )

    if not context:
        raise ValueError("Context instance is None.")

    return helios_lib.createLeafOptics(context)


def destroyLeafOptics(leafoptics: ctypes.POINTER(ULeafOptics)) -> None:
    """Destroy LeafOptics instance"""
    if leafoptics and _LEAFOPTICS_FUNCTIONS_AVAILABLE:
        helios_lib.destroyLeafOptics(leafoptics)


def leafOpticsRun(leafoptics: ctypes.POINTER(ULeafOptics),
                  uuids: List[int],
                  properties: List[float],
                  label: str) -> None:
    """Run LeafOptics model and assign spectra to primitives

    Args:
        leafoptics: Pointer to LeafOptics instance
        uuids: List of primitive UUIDs
        properties: List of 9 floats [numberlayers, brownpigments, chlorophyllcontent,
                    carotenoidcontent, anthocyancontent, watermass, drymass, protein, carbonconstituents]
        label: Label for the spectra (appended to "leaf_reflectivity_" and "leaf_transmissivity_")
    """
    if not _LEAFOPTICS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LeafOptics functions not available. Rebuild with leafoptics enabled.")
    if not leafoptics:
        raise ValueError("LeafOptics instance is None.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")
    if len(properties) != LEAF_OPTICS_PROPERTIES_COUNT:
        raise ValueError(f"Properties must have exactly {LEAF_OPTICS_PROPERTIES_COUNT} elements.")
    if not label:
        raise ValueError("Label cannot be empty.")

    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    properties_array = (ctypes.c_float * LEAF_OPTICS_PROPERTIES_COUNT)(*properties)
    label_bytes = label.encode('utf-8')

    helios_lib.leafOpticsRun(leafoptics, uuid_array, len(uuids), properties_array, label_bytes)


def leafOpticsRunNoUUIDs(leafoptics: ctypes.POINTER(ULeafOptics),
                         properties: List[float],
                         label: str) -> None:
    """Run LeafOptics model without assigning to primitives

    Args:
        leafoptics: Pointer to LeafOptics instance
        properties: List of 9 floats [numberlayers, brownpigments, chlorophyllcontent,
                    carotenoidcontent, anthocyancontent, watermass, drymass, protein, carbonconstituents]
        label: Label for the spectra
    """
    if not _LEAFOPTICS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LeafOptics functions not available. Rebuild with leafoptics enabled.")
    if not leafoptics:
        raise ValueError("LeafOptics instance is None.")
    if len(properties) != LEAF_OPTICS_PROPERTIES_COUNT:
        raise ValueError(f"Properties must have exactly {LEAF_OPTICS_PROPERTIES_COUNT} elements.")
    if not label:
        raise ValueError("Label cannot be empty.")

    properties_array = (ctypes.c_float * LEAF_OPTICS_PROPERTIES_COUNT)(*properties)
    label_bytes = label.encode('utf-8')

    helios_lib.leafOpticsRunNoUUIDs(leafoptics, properties_array, label_bytes)


def leafOpticsGetLeafSpectra(leafoptics: ctypes.POINTER(ULeafOptics),
                              properties: List[float]) -> Tuple[List[float], List[float], List[float]]:
    """Get leaf reflectance and transmittance spectra

    Args:
        leafoptics: Pointer to LeafOptics instance
        properties: List of 9 floats [numberlayers, brownpigments, chlorophyllcontent,
                    carotenoidcontent, anthocyancontent, watermass, drymass, protein, carbonconstituents]

    Returns:
        Tuple of (wavelengths, reflectivities, transmissivities) as lists of floats
        - wavelengths: 400-2500 nm at 1nm resolution (2101 points)
        - reflectivities: reflectance values at each wavelength
        - transmissivities: transmittance values at each wavelength
    """
    if not _LEAFOPTICS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LeafOptics functions not available. Rebuild with leafoptics enabled.")
    if not leafoptics:
        raise ValueError("LeafOptics instance is None.")
    if len(properties) != LEAF_OPTICS_PROPERTIES_COUNT:
        raise ValueError(f"Properties must have exactly {LEAF_OPTICS_PROPERTIES_COUNT} elements.")

    properties_array = (ctypes.c_float * LEAF_OPTICS_PROPERTIES_COUNT)(*properties)
    reflectivities = (ctypes.c_float * LEAF_OPTICS_SPECTRAL_POINTS)()
    transmissivities = (ctypes.c_float * LEAF_OPTICS_SPECTRAL_POINTS)()
    wavelengths = (ctypes.c_float * LEAF_OPTICS_SPECTRAL_POINTS)()
    size = ctypes.c_uint()

    helios_lib.leafOpticsGetLeafSpectra(
        leafoptics, properties_array, reflectivities, transmissivities, wavelengths, ctypes.byref(size)
    )

    # Convert to Python lists
    n = size.value
    return (
        list(wavelengths[:n]),
        list(reflectivities[:n]),
        list(transmissivities[:n])
    )


def leafOpticsSetProperties(leafoptics: ctypes.POINTER(ULeafOptics),
                            uuids: List[int],
                            properties: List[float]) -> None:
    """Set leaf optical properties for primitives

    Args:
        leafoptics: Pointer to LeafOptics instance
        uuids: List of primitive UUIDs
        properties: List of 9 floats [numberlayers, brownpigments, chlorophyllcontent,
                    carotenoidcontent, anthocyancontent, watermass, drymass, protein, carbonconstituents]
    """
    if not _LEAFOPTICS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LeafOptics functions not available. Rebuild with leafoptics enabled.")
    if not leafoptics:
        raise ValueError("LeafOptics instance is None.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")
    if len(properties) != LEAF_OPTICS_PROPERTIES_COUNT:
        raise ValueError(f"Properties must have exactly {LEAF_OPTICS_PROPERTIES_COUNT} elements.")

    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    properties_array = (ctypes.c_float * LEAF_OPTICS_PROPERTIES_COUNT)(*properties)

    helios_lib.leafOpticsSetProperties(leafoptics, uuid_array, len(uuids), properties_array)


def leafOpticsGetPropertiesFromSpectrum(leafoptics: ctypes.POINTER(ULeafOptics),
                                         uuids: List[int]) -> None:
    """Get PROSPECT parameters from reflectivity spectrum for primitives

    Args:
        leafoptics: Pointer to LeafOptics instance
        uuids: List of primitive UUIDs to query

    Note:
        Primitives without matching spectra are silently skipped
    """
    if not _LEAFOPTICS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LeafOptics functions not available. Rebuild with leafoptics enabled.")
    if not leafoptics:
        raise ValueError("LeafOptics instance is None.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty.")

    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)

    helios_lib.leafOpticsGetPropertiesFromSpectrum(leafoptics, uuid_array, len(uuids))


def leafOpticsGetPropertiesFromSpectrumSingle(leafoptics: ctypes.POINTER(ULeafOptics),
                                               uuid: int) -> None:
    """Get PROSPECT parameters from reflectivity spectrum for a single primitive

    Args:
        leafoptics: Pointer to LeafOptics instance
        uuid: Single primitive UUID to query

    Note:
        If no matching spectrum is found, the primitive is silently skipped
    """
    if not _LEAFOPTICS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LeafOptics functions not available. Rebuild with leafoptics enabled.")
    if not leafoptics:
        raise ValueError("LeafOptics instance is None.")
    if uuid < 0:
        raise ValueError("UUID must be non-negative.")

    helios_lib.leafOpticsGetPropertiesFromSpectrumSingle(leafoptics, ctypes.c_uint(uuid))


def leafOpticsGetPropertiesFromLibrary(leafoptics: ctypes.POINTER(ULeafOptics),
                                        species: str) -> List[float]:
    """Get leaf optical properties from the built-in species library

    Args:
        leafoptics: Pointer to LeafOptics instance
        species: Name of the species (case-insensitive). Available species:
                 "default", "garden_lettuce", "alfalfa", "corn", "sunflower",
                 "english_walnut", "rice", "soybean", "wine_grape", "tomato",
                 "common_bean", "cowpea"

    Returns:
        List of 9 floats [numberlayers, brownpigments, chlorophyllcontent,
                         carotenoidcontent, anthocyancontent, watermass, drymass, protein, carbonconstituents]

    Note:
        If species is not found, default properties are used and a warning is issued
    """
    if not _LEAFOPTICS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LeafOptics functions not available. Rebuild with leafoptics enabled.")
    if not leafoptics:
        raise ValueError("LeafOptics instance is None.")
    if not species:
        raise ValueError("Species name cannot be empty.")

    properties_array = (ctypes.c_float * LEAF_OPTICS_PROPERTIES_COUNT)()
    species_bytes = species.encode('utf-8')

    helios_lib.leafOpticsGetPropertiesFromLibrary(leafoptics, species_bytes, properties_array)

    return list(properties_array)


def leafOpticsDisableMessages(leafoptics: ctypes.POINTER(ULeafOptics)) -> None:
    """Disable command-line output messages from LeafOptics"""
    if not _LEAFOPTICS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LeafOptics functions not available. Rebuild with leafoptics enabled.")
    if not leafoptics:
        raise ValueError("LeafOptics instance is None.")

    helios_lib.leafOpticsDisableMessages(leafoptics)


def leafOpticsEnableMessages(leafoptics: ctypes.POINTER(ULeafOptics)) -> None:
    """Enable command-line output messages from LeafOptics"""
    if not _LEAFOPTICS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LeafOptics functions not available. Rebuild with leafoptics enabled.")
    if not leafoptics:
        raise ValueError("LeafOptics instance is None.")

    helios_lib.leafOpticsEnableMessages(leafoptics)


def leafOpticsOptionalOutputPrimitiveData(leafoptics: ctypes.POINTER(ULeafOptics), label: str) -> None:
    """Selectively output primitive data for specific biochemical properties

    By default, all biochemical properties are written as primitive data. Use this method
    to select only needed properties for better performance.

    Args:
        leafoptics: LeafOptics instance pointer
        label: Property label - one of: "chlorophyll", "carotenoid", "anthocyanin",
               "brown", "water", "drymass", "protein", "cellulose"

    Note:
        Added in helios-core v1.3.59
    """
    if not _LEAFOPTICS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("LeafOptics functions not available. Rebuild with leafoptics enabled.")
    if not leafoptics:
        raise ValueError("LeafOptics instance is None.")
    if not label:
        raise ValueError("Label cannot be empty.")

    label_encoded = label.encode('utf-8')
    helios_lib.leafOpticsOptionalOutputPrimitiveData(leafoptics, label_encoded)


def is_leafoptics_available() -> bool:
    """Check if LeafOptics functions are available in the current library"""
    return _LEAFOPTICS_FUNCTIONS_AVAILABLE


# Mock mode functions
if not _LEAFOPTICS_FUNCTIONS_AVAILABLE:
    def mock_create(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: LeafOptics not available. "
            "This would create a plugin instance with native library."
        )

    def mock_method(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: LeafOptics method not available. "
            "This would execute plugin computation with native library."
        )

    # Replace functions with mocks for development
    createLeafOptics = mock_create
    leafOpticsRun = mock_method
    leafOpticsRunNoUUIDs = mock_method
    leafOpticsGetLeafSpectra = mock_method
    leafOpticsSetProperties = mock_method
    leafOpticsGetPropertiesFromSpectrum = mock_method
    leafOpticsGetPropertiesFromSpectrumSingle = mock_method
    leafOpticsGetPropertiesFromLibrary = mock_method
