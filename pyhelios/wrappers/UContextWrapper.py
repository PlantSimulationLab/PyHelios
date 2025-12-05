import ctypes
from typing import List

from ..plugins import helios_lib
from ..exceptions import check_helios_error

# Define the UContext struct
class UContext(ctypes.Structure):
    pass

# Error handling function prototypes
helios_lib.getLastErrorCode.restype = ctypes.c_int
helios_lib.getLastErrorMessage.restype = ctypes.c_char_p
helios_lib.clearError.argtypes = []

# Automatic error checking callback
def _check_error(result, func, args):
    """
    Errcheck callback that automatically checks for Helios errors after each function call.
    This ensures that C++ exceptions are properly converted to Python exceptions.
    """
    check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage)
    return result

# Function prototypes
helios_lib.createContext.restype = ctypes.POINTER(UContext)

helios_lib.destroyContext.argtypes = [ctypes.POINTER(UContext)]

helios_lib.markGeometryClean.argtypes = [ctypes.POINTER(UContext)]

helios_lib.markGeometryDirty.argtypes = [ctypes.POINTER(UContext)]

helios_lib.isGeometryDirty.argtypes = [ctypes.POINTER(UContext)]
helios_lib.isGeometryDirty.restype = ctypes.c_bool

helios_lib.addPatch.argtypes = [ctypes.POINTER(UContext)]
helios_lib.addPatch.restype = ctypes.c_uint
helios_lib.addPatch.errcheck = _check_error

helios_lib.addPatchWithCenterAndSize.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
helios_lib.addPatchWithCenterAndSize.restype = ctypes.c_uint
helios_lib.addPatchWithCenterAndSize.errcheck = _check_error

helios_lib.addPatchWithCenterSizeAndRotation.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
helios_lib.addPatchWithCenterSizeAndRotation.restype = ctypes.c_uint
helios_lib.addPatchWithCenterSizeAndRotation.errcheck = _check_error

helios_lib.addPatchWithCenterSizeRotationAndColor.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
helios_lib.addPatchWithCenterSizeRotationAndColor.restype = ctypes.c_uint
helios_lib.addPatchWithCenterSizeRotationAndColor.errcheck = _check_error

helios_lib.addPatchWithCenterSizeRotationAndColorRGBA.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
helios_lib.addPatchWithCenterSizeRotationAndColorRGBA.restype = ctypes.c_uint
helios_lib.addPatchWithCenterSizeRotationAndColorRGBA.errcheck = _check_error

helios_lib.getPrimitiveType.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
helios_lib.getPrimitiveType.restype = ctypes.c_uint
helios_lib.getPrimitiveType.errcheck = _check_error

helios_lib.getPrimitiveArea.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
helios_lib.getPrimitiveArea.restype = ctypes.c_float
helios_lib.getPrimitiveArea.errcheck = _check_error

helios_lib.getPrimitiveNormal.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
helios_lib.getPrimitiveNormal.restype = ctypes.POINTER(ctypes.c_float)
helios_lib.getPrimitiveNormal.errcheck = _check_error

helios_lib.getPrimitiveVertices.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
helios_lib.getPrimitiveVertices.restype = ctypes.POINTER(ctypes.c_float)
helios_lib.getPrimitiveVertices.errcheck = _check_error

helios_lib.getPrimitiveColor.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
helios_lib.getPrimitiveColor.restype = ctypes.POINTER(ctypes.c_float)
helios_lib.getPrimitiveColor.errcheck = _check_error

helios_lib.getPrimitiveColorRGB.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
helios_lib.getPrimitiveColorRGB.restype = ctypes.POINTER(ctypes.c_float)
helios_lib.getPrimitiveColorRGB.errcheck = _check_error

helios_lib.getPrimitiveColorRGBA.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
helios_lib.getPrimitiveColorRGBA.restype = ctypes.POINTER(ctypes.c_float)
helios_lib.getPrimitiveColorRGBA.errcheck = _check_error

helios_lib.getPrimitiveCount.argtypes = [ctypes.POINTER(UContext)]
helios_lib.getPrimitiveCount.restype = ctypes.c_uint

helios_lib.getAllUUIDs.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint)]
helios_lib.getAllUUIDs.restype = ctypes.POINTER(ctypes.c_uint)
helios_lib.getAllUUIDs.errcheck = _check_error

helios_lib.getObjectCount.argtypes = [ctypes.POINTER(UContext)]
helios_lib.getObjectCount.restype = ctypes.c_uint

helios_lib.getAllObjectIDs.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint)]
helios_lib.getAllObjectIDs.restype = ctypes.POINTER(ctypes.c_uint)
helios_lib.getAllObjectIDs.errcheck = _check_error

helios_lib.getObjectPrimitiveUUIDs.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
helios_lib.getObjectPrimitiveUUIDs.restype = ctypes.POINTER(ctypes.c_uint)
helios_lib.getObjectPrimitiveUUIDs.errcheck = _check_error

helios_lib.loadPLY.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.POINTER(ctypes.c_float), ctypes.c_float, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint)]
helios_lib.loadPLY.restype = ctypes.POINTER(ctypes.c_uint)
helios_lib.loadPLY.errcheck = _check_error

# Try to set up basic loadPLY function prototype
try:
    helios_lib.loadPLYBasic.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_bool, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.loadPLYBasic.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.loadPLYBasic.errcheck = _check_error
    _BASIC_PLY_AVAILABLE = True
except AttributeError:
    _BASIC_PLY_AVAILABLE = False

# Try to set up primitive data function prototypes specifically
try:
    # Primitive data function prototypes - scalar setters
    helios_lib.setPrimitiveDataInt.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_int]
    helios_lib.setPrimitiveDataInt.restype = None
    
    helios_lib.setPrimitiveDataFloat.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_float]
    helios_lib.setPrimitiveDataFloat.restype = None
    
    helios_lib.setPrimitiveDataString.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.setPrimitiveDataString.restype = None
    
    helios_lib.setPrimitiveDataVec3.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.setPrimitiveDataVec3.restype = None
    
    # Primitive data function prototypes - scalar getters
    helios_lib.getPrimitiveDataInt.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p]
    helios_lib.getPrimitiveDataInt.restype = ctypes.c_int
    
    helios_lib.getPrimitiveDataFloat.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p]
    helios_lib.getPrimitiveDataFloat.restype = ctypes.c_float
    
    helios_lib.getPrimitiveDataString.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
    helios_lib.getPrimitiveDataString.restype = ctypes.c_int
    
    helios_lib.getPrimitiveDataVec3.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.getPrimitiveDataVec3.restype = None
    
    # Primitive data utility functions
    helios_lib.doesPrimitiveDataExist.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p]
    helios_lib.doesPrimitiveDataExist.restype = ctypes.c_bool
    
    helios_lib.getPrimitiveDataType.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p]
    helios_lib.getPrimitiveDataType.restype = ctypes.c_int
    
    helios_lib.getPrimitiveDataSize.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p]
    helios_lib.getPrimitiveDataSize.restype = ctypes.c_int
    
    # Extended primitive data function prototypes - scalar setters
    helios_lib.setPrimitiveDataUInt.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_uint]
    helios_lib.setPrimitiveDataUInt.restype = None
    
    helios_lib.setPrimitiveDataDouble.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_double]
    helios_lib.setPrimitiveDataDouble.restype = None
    
    helios_lib.setPrimitiveDataVec2.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_float, ctypes.c_float]
    helios_lib.setPrimitiveDataVec2.restype = None
    
    helios_lib.setPrimitiveDataVec4.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.setPrimitiveDataVec4.restype = None
    
    helios_lib.setPrimitiveDataInt2.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
    helios_lib.setPrimitiveDataInt2.restype = None
    
    helios_lib.setPrimitiveDataInt3.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    helios_lib.setPrimitiveDataInt3.restype = None
    
    helios_lib.setPrimitiveDataInt4.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    helios_lib.setPrimitiveDataInt4.restype = None
    
    # Extended primitive data function prototypes - scalar getters
    helios_lib.getPrimitiveDataUInt.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p]
    helios_lib.getPrimitiveDataUInt.restype = ctypes.c_uint
    
    helios_lib.getPrimitiveDataDouble.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p]
    helios_lib.getPrimitiveDataDouble.restype = ctypes.c_double
    
    helios_lib.getPrimitiveDataVec2.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.getPrimitiveDataVec2.restype = None
    
    helios_lib.getPrimitiveDataVec4.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.getPrimitiveDataVec4.restype = None
    
    helios_lib.getPrimitiveDataInt2.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    helios_lib.getPrimitiveDataInt2.restype = None
    
    helios_lib.getPrimitiveDataInt3.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    helios_lib.getPrimitiveDataInt3.restype = None
    
    helios_lib.getPrimitiveDataInt4.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    helios_lib.getPrimitiveDataInt4.restype = None
    
    # Generic primitive data getter
    helios_lib.getPrimitiveDataGeneric.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_int]
    helios_lib.getPrimitiveDataGeneric.restype = ctypes.c_int

    # Note: getPrimitiveDataAuto is implemented in Python using type detection

    # Add error checking for all primitive data functions
    helios_lib.setPrimitiveDataInt.errcheck = _check_error
    helios_lib.setPrimitiveDataFloat.errcheck = _check_error
    helios_lib.setPrimitiveDataString.errcheck = _check_error
    helios_lib.setPrimitiveDataVec3.errcheck = _check_error
    helios_lib.getPrimitiveDataInt.errcheck = _check_error
    helios_lib.getPrimitiveDataFloat.errcheck = _check_error
    helios_lib.getPrimitiveDataString.errcheck = _check_error
    helios_lib.getPrimitiveDataVec3.errcheck = _check_error
    helios_lib.doesPrimitiveDataExist.errcheck = _check_error
    helios_lib.getPrimitiveDataType.errcheck = _check_error
    helios_lib.getPrimitiveDataSize.errcheck = _check_error
    helios_lib.setPrimitiveDataUInt.errcheck = _check_error
    helios_lib.setPrimitiveDataDouble.errcheck = _check_error
    helios_lib.setPrimitiveDataVec2.errcheck = _check_error
    helios_lib.setPrimitiveDataVec4.errcheck = _check_error
    helios_lib.setPrimitiveDataInt2.errcheck = _check_error
    helios_lib.setPrimitiveDataInt3.errcheck = _check_error
    helios_lib.setPrimitiveDataInt4.errcheck = _check_error
    helios_lib.getPrimitiveDataUInt.errcheck = _check_error
    helios_lib.getPrimitiveDataDouble.errcheck = _check_error
    helios_lib.getPrimitiveDataVec2.errcheck = _check_error
    helios_lib.getPrimitiveDataVec4.errcheck = _check_error
    helios_lib.getPrimitiveDataInt2.errcheck = _check_error
    helios_lib.getPrimitiveDataInt3.errcheck = _check_error
    helios_lib.getPrimitiveDataInt4.errcheck = _check_error
    helios_lib.getPrimitiveDataGeneric.errcheck = _check_error

    # Mark that primitive data functions are available
    _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE = True

except AttributeError:
    # Primitive data functions not available in current native library
    _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE = False

# Try to set up broadcast primitive data function prototypes
_BROADCAST_PRIMITIVE_DATA_AVAILABLE = False
try:
    # Broadcast setPrimitiveData function prototypes - same value to all UUIDs
    helios_lib.setBroadcastPrimitiveDataInt.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_size_t, ctypes.c_char_p, ctypes.c_int]
    helios_lib.setBroadcastPrimitiveDataInt.restype = None
    helios_lib.setBroadcastPrimitiveDataInt.errcheck = _check_error

    helios_lib.setBroadcastPrimitiveDataUInt.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_size_t, ctypes.c_char_p, ctypes.c_uint]
    helios_lib.setBroadcastPrimitiveDataUInt.restype = None
    helios_lib.setBroadcastPrimitiveDataUInt.errcheck = _check_error

    helios_lib.setBroadcastPrimitiveDataFloat.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_size_t, ctypes.c_char_p, ctypes.c_float]
    helios_lib.setBroadcastPrimitiveDataFloat.restype = None
    helios_lib.setBroadcastPrimitiveDataFloat.errcheck = _check_error

    helios_lib.setBroadcastPrimitiveDataDouble.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_size_t, ctypes.c_char_p, ctypes.c_double]
    helios_lib.setBroadcastPrimitiveDataDouble.restype = None
    helios_lib.setBroadcastPrimitiveDataDouble.errcheck = _check_error

    helios_lib.setBroadcastPrimitiveDataString.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_size_t, ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.setBroadcastPrimitiveDataString.restype = None
    helios_lib.setBroadcastPrimitiveDataString.errcheck = _check_error

    helios_lib.setBroadcastPrimitiveDataVec2.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_size_t, ctypes.c_char_p, ctypes.c_float, ctypes.c_float]
    helios_lib.setBroadcastPrimitiveDataVec2.restype = None
    helios_lib.setBroadcastPrimitiveDataVec2.errcheck = _check_error

    helios_lib.setBroadcastPrimitiveDataVec3.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_size_t, ctypes.c_char_p, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.setBroadcastPrimitiveDataVec3.restype = None
    helios_lib.setBroadcastPrimitiveDataVec3.errcheck = _check_error

    helios_lib.setBroadcastPrimitiveDataVec4.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_size_t, ctypes.c_char_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.setBroadcastPrimitiveDataVec4.restype = None
    helios_lib.setBroadcastPrimitiveDataVec4.errcheck = _check_error

    helios_lib.setBroadcastPrimitiveDataInt2.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_size_t, ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
    helios_lib.setBroadcastPrimitiveDataInt2.restype = None
    helios_lib.setBroadcastPrimitiveDataInt2.errcheck = _check_error

    helios_lib.setBroadcastPrimitiveDataInt3.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_size_t, ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    helios_lib.setBroadcastPrimitiveDataInt3.restype = None
    helios_lib.setBroadcastPrimitiveDataInt3.errcheck = _check_error

    helios_lib.setBroadcastPrimitiveDataInt4.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_size_t, ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    helios_lib.setBroadcastPrimitiveDataInt4.restype = None
    helios_lib.setBroadcastPrimitiveDataInt4.errcheck = _check_error

    _BROADCAST_PRIMITIVE_DATA_AVAILABLE = True

except AttributeError:
    # Broadcast primitive data functions not available
    _BROADCAST_PRIMITIVE_DATA_AVAILABLE = False

# Try to set up PLY loading function prototypes separately
# Note: Some PLY functions may not be available in the native library, so we set them up individually

_PLY_LOADING_FUNCTIONS_AVAILABLE = False
_AVAILABLE_PLY_FUNCTIONS = []

# Try each PLY function individually
try:
    helios_lib.loadPLYWithOriginHeight.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.POINTER(ctypes.c_float), ctypes.c_float, ctypes.c_char_p, ctypes.c_bool, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.loadPLYWithOriginHeight.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.loadPLYWithOriginHeight.errcheck = _check_error
    _AVAILABLE_PLY_FUNCTIONS.append('loadPLYWithOriginHeight')
except AttributeError:
    pass

try:
    helios_lib.loadPLYWithOriginHeightRotation.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.POINTER(ctypes.c_float), ctypes.c_float, ctypes.POINTER(ctypes.c_float), ctypes.c_char_p, ctypes.c_bool, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.loadPLYWithOriginHeightRotation.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.loadPLYWithOriginHeightRotation.errcheck = _check_error
    _AVAILABLE_PLY_FUNCTIONS.append('loadPLYWithOriginHeightRotation')
except AttributeError:
    pass

try:
    helios_lib.loadPLYWithOriginHeightColor.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.POINTER(ctypes.c_float), ctypes.c_float, ctypes.POINTER(ctypes.c_float), ctypes.c_char_p, ctypes.c_bool, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.loadPLYWithOriginHeightColor.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.loadPLYWithOriginHeightColor.errcheck = _check_error
    _AVAILABLE_PLY_FUNCTIONS.append('loadPLYWithOriginHeightColor')
except AttributeError:
    pass

try:
    helios_lib.loadPLYWithOriginHeightRotationColor.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.POINTER(ctypes.c_float), ctypes.c_float, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_char_p, ctypes.c_bool, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.loadPLYWithOriginHeightRotationColor.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.loadPLYWithOriginHeightRotationColor.errcheck = _check_error
    _AVAILABLE_PLY_FUNCTIONS.append('loadPLYWithOriginHeightRotationColor')
except AttributeError:
    pass

# Mark PLY functions as available if we found any
if _AVAILABLE_PLY_FUNCTIONS:
    _PLY_LOADING_FUNCTIONS_AVAILABLE = True

# Try to set up OBJ and XML loading function prototypes separately  
try:
    # loadOBJ function prototypes
    helios_lib.loadOBJ.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_bool, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.loadOBJ.restype = ctypes.POINTER(ctypes.c_uint)
    
    helios_lib.loadOBJWithOriginHeightRotationColor.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.POINTER(ctypes.c_float), ctypes.c_float, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_bool, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.loadOBJWithOriginHeightRotationColor.restype = ctypes.POINTER(ctypes.c_uint)
    
    helios_lib.loadOBJWithOriginHeightRotationColorUpaxis.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.POINTER(ctypes.c_float), ctypes.c_float, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_char_p, ctypes.c_bool, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.loadOBJWithOriginHeightRotationColorUpaxis.restype = ctypes.POINTER(ctypes.c_uint)
    
    helios_lib.loadOBJWithOriginScaleRotationColorUpaxis.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_char_p, ctypes.c_bool, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.loadOBJWithOriginScaleRotationColorUpaxis.restype = ctypes.POINTER(ctypes.c_uint)
    
    # loadXML function prototype
    helios_lib.loadXML.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_bool, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.loadXML.restype = ctypes.POINTER(ctypes.c_uint)

    # Add error checking for OBJ and XML loading functions
    helios_lib.loadOBJ.errcheck = _check_error
    helios_lib.loadOBJWithOriginHeightRotationColor.errcheck = _check_error
    helios_lib.loadOBJWithOriginHeightRotationColorUpaxis.errcheck = _check_error
    helios_lib.loadOBJWithOriginScaleRotationColorUpaxis.errcheck = _check_error
    helios_lib.loadXML.errcheck = _check_error

    # Mark that OBJ/XML loading functions are available
    _OBJ_XML_LOADING_FUNCTIONS_AVAILABLE = True

except AttributeError:
    # OBJ/XML loading functions not available in current native library
    _OBJ_XML_LOADING_FUNCTIONS_AVAILABLE = False

# Check if basic file loading functions are available
_BASIC_FILE_LOADING_AVAILABLE = _BASIC_PLY_AVAILABLE

# For backward compatibility, set this to True if any file loading functions are available
_FILE_LOADING_FUNCTIONS_AVAILABLE = _PLY_LOADING_FUNCTIONS_AVAILABLE or _OBJ_XML_LOADING_FUNCTIONS_AVAILABLE or _BASIC_FILE_LOADING_AVAILABLE

# Try to set up file export function prototypes individually
_AVAILABLE_EXPORT_FUNCTIONS = []
_FILE_EXPORT_FUNCTIONS_AVAILABLE = False

# writePLY functions
try:
    helios_lib.writePLY.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p]
    helios_lib.writePLY.restype = None
    helios_lib.writePLY.errcheck = _check_error
    _AVAILABLE_EXPORT_FUNCTIONS.append('writePLY')
except AttributeError:
    pass

try:
    helios_lib.writePLYWithUUIDs.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint), ctypes.c_uint]
    helios_lib.writePLYWithUUIDs.restype = None
    helios_lib.writePLYWithUUIDs.errcheck = _check_error
    _AVAILABLE_EXPORT_FUNCTIONS.append('writePLYWithUUIDs')
except AttributeError:
    pass

# writeOBJ functions
try:
    helios_lib.writeOBJ.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_bool, ctypes.c_bool]
    helios_lib.writeOBJ.restype = None
    helios_lib.writeOBJ.errcheck = _check_error
    _AVAILABLE_EXPORT_FUNCTIONS.append('writeOBJ')
except AttributeError:
    pass

try:
    helios_lib.writeOBJWithUUIDs.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.c_bool, ctypes.c_bool]
    helios_lib.writeOBJWithUUIDs.restype = None
    helios_lib.writeOBJWithUUIDs.errcheck = _check_error
    _AVAILABLE_EXPORT_FUNCTIONS.append('writeOBJWithUUIDs')
except AttributeError:
    pass

try:
    helios_lib.writeOBJWithPrimitiveData.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_char_p), ctypes.c_uint, ctypes.c_bool, ctypes.c_bool]
    helios_lib.writeOBJWithPrimitiveData.restype = None
    helios_lib.writeOBJWithPrimitiveData.errcheck = _check_error
    _AVAILABLE_EXPORT_FUNCTIONS.append('writeOBJWithPrimitiveData')
except AttributeError:
    pass

# writePrimitiveData - write primitive data to ASCII file (all primitives)
try:
    helios_lib.writePrimitiveData.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.POINTER(ctypes.c_char_p), ctypes.c_uint, ctypes.c_bool]
    helios_lib.writePrimitiveData.restype = None
    helios_lib.writePrimitiveData.errcheck = _check_error
    _AVAILABLE_EXPORT_FUNCTIONS.append('writePrimitiveData')
except AttributeError:
    pass

# writePrimitiveDataWithUUIDs - write primitive data to ASCII file (selected primitives)
try:
    helios_lib.writePrimitiveDataWithUUIDs.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.POINTER(ctypes.c_char_p), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.c_bool]
    helios_lib.writePrimitiveDataWithUUIDs.restype = None
    helios_lib.writePrimitiveDataWithUUIDs.errcheck = _check_error
    _AVAILABLE_EXPORT_FUNCTIONS.append('writePrimitiveDataWithUUIDs')
except AttributeError:
    pass

# Mark export functions as available if we found any
if _AVAILABLE_EXPORT_FUNCTIONS:
    _FILE_EXPORT_FUNCTIONS_AVAILABLE = True

# Try to set up triangle function prototypes individually (critical pattern from plugin integration guide)
_AVAILABLE_TRIANGLE_FUNCTIONS = []

# Basic triangle function
try:
    helios_lib.addTriangle.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.addTriangle.restype = ctypes.c_uint
    helios_lib.addTriangle.errcheck = _check_error
    _AVAILABLE_TRIANGLE_FUNCTIONS.append('addTriangle')
except AttributeError:
    pass

# Triangle with color function
try:
    helios_lib.addTriangleWithColor.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.addTriangleWithColor.restype = ctypes.c_uint
    helios_lib.addTriangleWithColor.errcheck = _check_error
    _AVAILABLE_TRIANGLE_FUNCTIONS.append('addTriangleWithColor')
except AttributeError:
    pass

# Triangle with RGBA color function
try:
    helios_lib.addTriangleWithColorRGBA.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.addTriangleWithColorRGBA.restype = ctypes.c_uint
    helios_lib.addTriangleWithColorRGBA.errcheck = _check_error
    _AVAILABLE_TRIANGLE_FUNCTIONS.append('addTriangleWithColorRGBA')
except AttributeError:
    pass

# Triangle with texture function
try:
    helios_lib.addTriangleWithTexture.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_char_p, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.addTriangleWithTexture.restype = ctypes.c_uint
    helios_lib.addTriangleWithTexture.errcheck = _check_error
    _AVAILABLE_TRIANGLE_FUNCTIONS.append('addTriangleWithTexture')
except AttributeError:
    pass

# Multi-texture triangle function (may not be available in all builds)
try:
    helios_lib.addTrianglesFromArraysMultiTextured.argtypes = [
        ctypes.POINTER(UContext),                    # context
        ctypes.POINTER(ctypes.c_float),             # vertices
        ctypes.c_uint,                              # vertex_count
        ctypes.POINTER(ctypes.c_uint),              # faces
        ctypes.c_uint,                              # face_count
        ctypes.POINTER(ctypes.c_float),             # uv_coords
        ctypes.POINTER(ctypes.c_char_p),            # texture_files
        ctypes.c_uint,                              # texture_count
        ctypes.POINTER(ctypes.c_uint),              # material_ids
        ctypes.POINTER(ctypes.c_uint)               # result_count
    ]
    helios_lib.addTrianglesFromArraysMultiTextured.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.addTrianglesFromArraysMultiTextured.errcheck = _check_error
    _AVAILABLE_TRIANGLE_FUNCTIONS.append('addTrianglesFromArraysMultiTextured')
except AttributeError:
    pass

# Mark triangle functions as available if we found any basic functions
_TRIANGLE_FUNCTIONS_AVAILABLE = len(_AVAILABLE_TRIANGLE_FUNCTIONS) > 0

# Compound geometry function prototypes - return arrays of UUIDs
try:
    # addTile functions
    helios_lib.addTile.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.addTile.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.addTile.errcheck = _check_error

    helios_lib.addTileWithColor.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.addTileWithColor.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.addTileWithColor.errcheck = _check_error

    # addSphere functions
    helios_lib.addSphere.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.c_float, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.addSphere.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.addSphere.errcheck = _check_error

    helios_lib.addSphereWithColor.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.c_float, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.addSphereWithColor.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.addSphereWithColor.errcheck = _check_error

    # addTube functions
    helios_lib.addTube.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.addTube.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.addTube.errcheck = _check_error

    helios_lib.addTubeWithColor.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.addTubeWithColor.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.addTubeWithColor.errcheck = _check_error

    # addBox functions
    helios_lib.addBox.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.addBox.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.addBox.errcheck = _check_error

    helios_lib.addBoxWithColor.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.addBoxWithColor.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.addBoxWithColor.errcheck = _check_error

    # addDisk functions
    helios_lib.addDisk.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.addDisk.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.addDisk.errcheck = _check_error

    helios_lib.addDiskWithRotation.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.addDiskWithRotation.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.addDiskWithRotation.errcheck = _check_error

    helios_lib.addDiskWithColor.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.addDiskWithColor.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.addDiskWithColor.errcheck = _check_error

    helios_lib.addDiskWithRGBAColor.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.addDiskWithRGBAColor.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.addDiskWithRGBAColor.errcheck = _check_error

    helios_lib.addDiskPolarSubdivisions.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.addDiskPolarSubdivisions.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.addDiskPolarSubdivisions.errcheck = _check_error

    # addDiskPolarSubdivisionsRGBA function
    helios_lib.addDiskPolarSubdivisionsRGBA.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.addDiskPolarSubdivisionsRGBA.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.addDiskPolarSubdivisionsRGBA.errcheck = _check_error

    # addCone functions
    helios_lib.addCone.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.addCone.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.addCone.errcheck = _check_error

    helios_lib.addConeWithColor.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.addConeWithColor.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.addConeWithColor.errcheck = _check_error

    # Copy operation functions
    helios_lib.copyPrimitive.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.copyPrimitive.restype = ctypes.c_uint
    helios_lib.copyPrimitive.errcheck = _check_error

    helios_lib.copyPrimitives.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.copyPrimitives.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.copyPrimitives.errcheck = _check_error

    helios_lib.copyPrimitiveData.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_uint]
    helios_lib.copyPrimitiveData.restype = None
    helios_lib.copyPrimitiveData.errcheck = _check_error

    helios_lib.copyObject.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.copyObject.restype = ctypes.c_uint
    helios_lib.copyObject.errcheck = _check_error

    helios_lib.copyObjects.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.copyObjects.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.copyObjects.errcheck = _check_error

    helios_lib.copyObjectData.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_uint]
    helios_lib.copyObjectData.restype = None
    helios_lib.copyObjectData.errcheck = _check_error

    # Translation operation functions
    helios_lib.translatePrimitive.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.translatePrimitive.restype = None
    helios_lib.translatePrimitive.errcheck = _check_error

    helios_lib.translatePrimitives.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.translatePrimitives.restype = None
    helios_lib.translatePrimitives.errcheck = _check_error

    helios_lib.translateObject.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.translateObject.restype = None
    helios_lib.translateObject.errcheck = _check_error

    helios_lib.translateObjects.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.translateObjects.restype = None
    helios_lib.translateObjects.errcheck = _check_error

    # Rotation function prototypes
    helios_lib.rotatePrimitive_axisString.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_float, ctypes.c_char_p]
    helios_lib.rotatePrimitive_axisString.restype = None
    helios_lib.rotatePrimitive_axisString.errcheck = _check_error

    helios_lib.rotatePrimitives_axisString.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.c_float, ctypes.c_char_p]
    helios_lib.rotatePrimitives_axisString.restype = None
    helios_lib.rotatePrimitives_axisString.errcheck = _check_error

    helios_lib.rotatePrimitive_axisVector.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
    helios_lib.rotatePrimitive_axisVector.restype = None
    helios_lib.rotatePrimitive_axisVector.errcheck = _check_error

    helios_lib.rotatePrimitives_axisVector.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
    helios_lib.rotatePrimitives_axisVector.restype = None
    helios_lib.rotatePrimitives_axisVector.errcheck = _check_error

    helios_lib.rotatePrimitive_originAxisVector.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_float, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.rotatePrimitive_originAxisVector.restype = None
    helios_lib.rotatePrimitive_originAxisVector.errcheck = _check_error

    helios_lib.rotatePrimitives_originAxisVector.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.c_float, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.rotatePrimitives_originAxisVector.restype = None
    helios_lib.rotatePrimitives_originAxisVector.errcheck = _check_error

    helios_lib.rotateObject_axisString.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_float, ctypes.c_char_p]
    helios_lib.rotateObject_axisString.restype = None
    helios_lib.rotateObject_axisString.errcheck = _check_error

    helios_lib.rotateObjects_axisString.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.c_float, ctypes.c_char_p]
    helios_lib.rotateObjects_axisString.restype = None
    helios_lib.rotateObjects_axisString.errcheck = _check_error

    helios_lib.rotateObject_axisVector.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
    helios_lib.rotateObject_axisVector.restype = None
    helios_lib.rotateObject_axisVector.errcheck = _check_error

    helios_lib.rotateObjects_axisVector.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
    helios_lib.rotateObjects_axisVector.restype = None
    helios_lib.rotateObjects_axisVector.errcheck = _check_error

    helios_lib.rotateObject_originAxisVector.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_float, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.rotateObject_originAxisVector.restype = None
    helios_lib.rotateObject_originAxisVector.errcheck = _check_error

    helios_lib.rotateObjects_originAxisVector.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.c_float, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.rotateObjects_originAxisVector.restype = None
    helios_lib.rotateObjects_originAxisVector.errcheck = _check_error

    helios_lib.rotateObjectAboutOrigin_axisVector.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
    helios_lib.rotateObjectAboutOrigin_axisVector.restype = None
    helios_lib.rotateObjectAboutOrigin_axisVector.errcheck = _check_error

    helios_lib.rotateObjectsAboutOrigin_axisVector.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
    helios_lib.rotateObjectsAboutOrigin_axisVector.restype = None
    helios_lib.rotateObjectsAboutOrigin_axisVector.errcheck = _check_error

    # Scaling function prototypes
    helios_lib.scalePrimitive.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.scalePrimitive.restype = None
    helios_lib.scalePrimitive.errcheck = _check_error

    helios_lib.scalePrimitives.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.scalePrimitives.restype = None
    helios_lib.scalePrimitives.errcheck = _check_error

    helios_lib.scalePrimitiveAboutPoint.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.scalePrimitiveAboutPoint.restype = None
    helios_lib.scalePrimitiveAboutPoint.errcheck = _check_error

    helios_lib.scalePrimitivesAboutPoint.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.scalePrimitivesAboutPoint.restype = None
    helios_lib.scalePrimitivesAboutPoint.errcheck = _check_error

    helios_lib.scaleObject.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.scaleObject.restype = None
    helios_lib.scaleObject.errcheck = _check_error

    helios_lib.scaleObjects.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.scaleObjects.restype = None
    helios_lib.scaleObjects.errcheck = _check_error

    helios_lib.scaleObjectAboutCenter.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.scaleObjectAboutCenter.restype = None
    helios_lib.scaleObjectAboutCenter.errcheck = _check_error

    helios_lib.scaleObjectsAboutCenter.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.scaleObjectsAboutCenter.restype = None
    helios_lib.scaleObjectsAboutCenter.errcheck = _check_error

    helios_lib.scaleObjectAboutPoint.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.scaleObjectAboutPoint.restype = None
    helios_lib.scaleObjectAboutPoint.errcheck = _check_error

    helios_lib.scaleObjectsAboutPoint.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.scaleObjectsAboutPoint.restype = None
    helios_lib.scaleObjectsAboutPoint.errcheck = _check_error

    helios_lib.scaleObjectAboutOrigin.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.scaleObjectAboutOrigin.restype = None
    helios_lib.scaleObjectAboutOrigin.errcheck = _check_error

    helios_lib.scaleObjectsAboutOrigin.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.scaleObjectsAboutOrigin.restype = None
    helios_lib.scaleObjectsAboutOrigin.errcheck = _check_error

    # Cone object scaling methods (v1.3.59)
    helios_lib.scaleConeObjectLength.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_float]
    helios_lib.scaleConeObjectLength.restype = None
    helios_lib.scaleConeObjectLength.errcheck = _check_error

    helios_lib.scaleConeObjectGirth.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_float]
    helios_lib.scaleConeObjectGirth.restype = None
    helios_lib.scaleConeObjectGirth.errcheck = _check_error

    # Object-returning compound geometry prototypes
    helios_lib.addSphereObject_basic.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.c_float]
    helios_lib.addSphereObject_basic.restype = ctypes.c_uint
    helios_lib.addSphereObject_basic.errcheck = _check_error

    helios_lib.addSphereObject_color.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
    helios_lib.addSphereObject_color.restype = ctypes.c_uint
    helios_lib.addSphereObject_color.errcheck = _check_error

    helios_lib.addSphereObject_texture.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.c_float, ctypes.c_char_p]
    helios_lib.addSphereObject_texture.restype = ctypes.c_uint
    helios_lib.addSphereObject_texture.errcheck = _check_error

    helios_lib.addSphereObject_ellipsoid.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.addSphereObject_ellipsoid.restype = ctypes.c_uint
    helios_lib.addSphereObject_ellipsoid.errcheck = _check_error

    helios_lib.addSphereObject_ellipsoid_color.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.addSphereObject_ellipsoid_color.restype = ctypes.c_uint
    helios_lib.addSphereObject_ellipsoid_color.errcheck = _check_error

    helios_lib.addSphereObject_ellipsoid_texture.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_char_p]
    helios_lib.addSphereObject_ellipsoid_texture.restype = ctypes.c_uint
    helios_lib.addSphereObject_ellipsoid_texture.errcheck = _check_error

    # addTileObject prototypes
    helios_lib.addTileObject_basic.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int)]
    helios_lib.addTileObject_basic.restype = ctypes.c_uint
    helios_lib.addTileObject_basic.errcheck = _check_error

    helios_lib.addTileObject_color.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_float)]
    helios_lib.addTileObject_color.restype = ctypes.c_uint
    helios_lib.addTileObject_color.errcheck = _check_error

    helios_lib.addTileObject_texture.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int), ctypes.c_char_p]
    helios_lib.addTileObject_texture.restype = ctypes.c_uint
    helios_lib.addTileObject_texture.errcheck = _check_error

    helios_lib.addTileObject_texture_repeat.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int), ctypes.c_char_p, ctypes.POINTER(ctypes.c_int)]
    helios_lib.addTileObject_texture_repeat.restype = ctypes.c_uint
    helios_lib.addTileObject_texture_repeat.errcheck = _check_error

    # addBoxObject prototypes
    helios_lib.addBoxObject_basic.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int)]
    helios_lib.addBoxObject_basic.restype = ctypes.c_uint
    helios_lib.addBoxObject_basic.errcheck = _check_error
    helios_lib.addBoxObject_color.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_float)]
    helios_lib.addBoxObject_color.restype = ctypes.c_uint
    helios_lib.addBoxObject_color.errcheck = _check_error
    helios_lib.addBoxObject_texture.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int), ctypes.c_char_p]
    helios_lib.addBoxObject_texture.restype = ctypes.c_uint
    helios_lib.addBoxObject_texture.errcheck = _check_error
    helios_lib.addBoxObject_color_reverse.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_float), ctypes.c_bool]
    helios_lib.addBoxObject_color_reverse.restype = ctypes.c_uint
    helios_lib.addBoxObject_color_reverse.errcheck = _check_error
    helios_lib.addBoxObject_texture_reverse.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int), ctypes.c_char_p, ctypes.c_bool]
    helios_lib.addBoxObject_texture_reverse.restype = ctypes.c_uint
    helios_lib.addBoxObject_texture_reverse.errcheck = _check_error

    # addConeObject prototypes
    helios_lib.addConeObject_basic.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_float, ctypes.c_float]
    helios_lib.addConeObject_basic.restype = ctypes.c_uint
    helios_lib.addConeObject_basic.errcheck = _check_error
    helios_lib.addConeObject_color.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
    helios_lib.addConeObject_color.restype = ctypes.c_uint
    helios_lib.addConeObject_color.errcheck = _check_error
    helios_lib.addConeObject_texture.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_float, ctypes.c_float, ctypes.c_char_p]
    helios_lib.addConeObject_texture.restype = ctypes.c_uint
    helios_lib.addConeObject_texture.errcheck = _check_error

    # addDiskObject prototypes
    helios_lib.addDiskObject_basic.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.addDiskObject_basic.restype = ctypes.c_uint
    helios_lib.addDiskObject_basic.errcheck = _check_error
    helios_lib.addDiskObject_rotation.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.addDiskObject_rotation.restype = ctypes.c_uint
    helios_lib.addDiskObject_rotation.errcheck = _check_error
    helios_lib.addDiskObject_color.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.addDiskObject_color.restype = ctypes.c_uint
    helios_lib.addDiskObject_color.errcheck = _check_error
    helios_lib.addDiskObject_rgba.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.addDiskObject_rgba.restype = ctypes.c_uint
    helios_lib.addDiskObject_rgba.errcheck = _check_error
    helios_lib.addDiskObject_texture.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_char_p]
    helios_lib.addDiskObject_texture.restype = ctypes.c_uint
    helios_lib.addDiskObject_texture.errcheck = _check_error
    helios_lib.addDiskObject_polar_color.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.addDiskObject_polar_color.restype = ctypes.c_uint
    helios_lib.addDiskObject_polar_color.errcheck = _check_error
    helios_lib.addDiskObject_polar_rgba.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.addDiskObject_polar_rgba.restype = ctypes.c_uint
    helios_lib.addDiskObject_polar_rgba.errcheck = _check_error
    helios_lib.addDiskObject_polar_texture.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_char_p]
    helios_lib.addDiskObject_polar_texture.restype = ctypes.c_uint
    helios_lib.addDiskObject_polar_texture.errcheck = _check_error

    # addTubeObject prototypes
    helios_lib.addTubeObject_basic.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.c_uint]
    helios_lib.addTubeObject_basic.restype = ctypes.c_uint
    helios_lib.addTubeObject_basic.errcheck = _check_error
    helios_lib.addTubeObject_color.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.c_uint]
    helios_lib.addTubeObject_color.restype = ctypes.c_uint
    helios_lib.addTubeObject_color.errcheck = _check_error
    helios_lib.addTubeObject_texture.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.c_uint, ctypes.c_char_p]
    helios_lib.addTubeObject_texture.restype = ctypes.c_uint
    helios_lib.addTubeObject_texture.errcheck = _check_error
    helios_lib.addTubeObject_texture_uv.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.c_uint, ctypes.c_char_p, ctypes.POINTER(ctypes.c_float), ctypes.c_uint]
    helios_lib.addTubeObject_texture_uv.restype = ctypes.c_uint
    helios_lib.addTubeObject_texture_uv.errcheck = _check_error

    # Mark that compound geometry functions are available
    _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE = True
    
except AttributeError:
    # Functions not available in current library build
    _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE = False

# Legacy compatibility: set _NEW_FUNCTIONS_AVAILABLE based on primitive data availability
_NEW_FUNCTIONS_AVAILABLE = _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE

# Define Python wrappers for the UContext class methods
def createContext():
    return helios_lib.createContext()

def destroyContext(context):
    helios_lib.destroyContext(context)

def markGeometryClean(context):
    helios_lib.markGeometryClean(context)

def markGeometryDirty(context):
    helios_lib.markGeometryDirty(context)

def isGeometryDirty(context):
    return helios_lib.isGeometryDirty(context)

def addPatch(context):
    result = helios_lib.addPatch(context)
    return result

def addPatchWithCenterAndSize(context, center:List[float], size:List[float]):
    center_ptr = (ctypes.c_float * len(center))(*center)
    size_ptr = (ctypes.c_float * len(size))(*size)
    result = helios_lib.addPatchWithCenterAndSize(context, center_ptr, size_ptr)
    return result

def addPatchWithCenterSizeAndRotation(context, center:List[float], size:List[float], rotation:List[float]):
    center_ptr = (ctypes.c_float * len(center))(*center)
    size_ptr = (ctypes.c_float * len(size))(*size)
    rotation_ptr = (ctypes.c_float * len(rotation))(*rotation)
    return helios_lib.addPatchWithCenterSizeAndRotation(context, center_ptr, size_ptr, rotation_ptr)

def addPatchWithCenterSizeRotationAndColor(context, center:List[float], size:List[float], rotation:List[float], color:List[float]):
    center_ptr = (ctypes.c_float * len(center))(*center)
    size_ptr = (ctypes.c_float * len(size))(*size)
    rotation_ptr = (ctypes.c_float * len(rotation))(*rotation)
    color_ptr = (ctypes.c_float * len(color))(*color)
    return helios_lib.addPatchWithCenterSizeRotationAndColor(context, center_ptr, size_ptr, rotation_ptr, color_ptr)

def addPatchWithCenterSizeRotationAndColorRGBA(context, center:List[float], size:List[float], rotation:List[float], color:List[float]):
    center_ptr = (ctypes.c_float * len(center))(*center)
    size_ptr = (ctypes.c_float * len(size))(*size)
    rotation_ptr = (ctypes.c_float * len(rotation))(*rotation)
    color_ptr = (ctypes.c_float * len(color))(*color)
    return helios_lib.addPatchWithCenterSizeRotationAndColorRGBA(context, center_ptr, size_ptr, rotation_ptr, color_ptr)

def getPrimitiveType(context, uuid):
    # Error checking is handled automatically by errcheck
    return helios_lib.getPrimitiveType(context, uuid)

def getPrimitiveArea(context, uuid):
    # Error checking is handled automatically by errcheck
    return helios_lib.getPrimitiveArea(context, uuid)

def getPrimitiveNormal(context, uuid):
    # Error checking is handled automatically by errcheck
    return helios_lib.getPrimitiveNormal(context, uuid)

def getPrimitiveVertices(context, uuid, size):
    # Error checking is handled automatically by errcheck
    return helios_lib.getPrimitiveVertices(context, uuid, size)

def getPrimitiveColor(context, uuid):
    # Error checking is handled automatically by errcheck
    return helios_lib.getPrimitiveColor(context, uuid)

def getPrimitiveColorRGB(context, uuid):
    # Error checking is handled automatically by errcheck
    return helios_lib.getPrimitiveColorRGB(context, uuid)

def getPrimitiveColorRGBA(context, uuid):
    # Error checking is handled automatically by errcheck
    return helios_lib.getPrimitiveColorRGBA(context, uuid)

def getPrimitiveCount(context):
    return helios_lib.getPrimitiveCount(context)

def getAllUUIDs(context, size):
    # Error checking is handled automatically by errcheck
    return helios_lib.getAllUUIDs(context, size)

def getObjectCount(context):
    return helios_lib.getObjectCount(context)

def getAllObjectIDs(context, size):
    # Error checking is handled automatically by errcheck
    return helios_lib.getAllObjectIDs(context, size)

def getObjectPrimitiveUUIDs(context, object_id:int):
    # Error checking is handled automatically by errcheck
    size = ctypes.c_uint()
    uuids_ptr = helios_lib.getObjectPrimitiveUUIDs(context, object_id, ctypes.byref(size))
    return list(uuids_ptr[:size.value])

# Python wrappers for loadPLY functions
def loadPLY(context, filename:str, silent:bool=False):
    if not _FILE_LOADING_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("File loading functions not available in current Helios library. These require updated C++ wrapper implementation.")
    size = ctypes.c_uint()
    filename_encoded = filename.encode('utf-8')
    
    # Try to use the new loadPLYBasic function if available, otherwise fall back to mock
    if _BASIC_PLY_AVAILABLE:
        uuids_ptr = helios_lib.loadPLYBasic(context, filename_encoded, silent, ctypes.byref(size))
    else:
        # Fall back for development - this will likely fail but provide better error messages
        raise RuntimeError("loadPLY basic functionality not available. The native library needs to be rebuilt with the new loadPLY functions. Run: build_scripts/build_helios")
    
    if uuids_ptr is None:
        return []
    return list(uuids_ptr[:size.value])

def loadPLYWithOriginHeight(context, filename:str, origin:List[float], height:float, upaxis:str="YUP", silent:bool=False):
    size = ctypes.c_uint()
    filename_encoded = filename.encode('utf-8')
    upaxis_encoded = upaxis.encode('utf-8')
    origin_ptr = (ctypes.c_float * len(origin))(*origin)
    uuids_ptr = helios_lib.loadPLY(context, filename_encoded, origin_ptr, height, upaxis_encoded, ctypes.byref(size))
    return list(uuids_ptr[:size.value])

def loadPLYWithOriginHeightRotation(context, filename:str, origin:List[float], height:float, rotation:List[float], upaxis:str="YUP", silent:bool=False):
    if not _FILE_LOADING_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("File loading functions not available in current Helios library. These require updated C++ wrapper implementation.")
    size = ctypes.c_uint()
    filename_encoded = filename.encode('utf-8')
    upaxis_encoded = upaxis.encode('utf-8')
    origin_ptr = (ctypes.c_float * len(origin))(*origin)
    rotation_ptr = (ctypes.c_float * len(rotation))(*rotation)
    uuids_ptr = helios_lib.loadPLYWithOriginHeightRotation(context, filename_encoded, origin_ptr, height, rotation_ptr, upaxis_encoded, silent, ctypes.byref(size))
    return list(uuids_ptr[:size.value])

def loadPLYWithOriginHeightColor(context, filename:str, origin:List[float], height:float, color:List[float], upaxis:str="YUP", silent:bool=False):
    if not _FILE_LOADING_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("File loading functions not available in current Helios library. These require updated C++ wrapper implementation.")
    size = ctypes.c_uint()
    filename_encoded = filename.encode('utf-8')
    upaxis_encoded = upaxis.encode('utf-8')
    origin_ptr = (ctypes.c_float * len(origin))(*origin)
    color_ptr = (ctypes.c_float * len(color))(*color)
    uuids_ptr = helios_lib.loadPLYWithOriginHeightColor(context, filename_encoded, origin_ptr, height, color_ptr, upaxis_encoded, silent, ctypes.byref(size))
    return list(uuids_ptr[:size.value])

def loadPLYWithOriginHeightRotationColor(context, filename:str, origin:List[float], height:float, rotation:List[float], color:List[float], upaxis:str="YUP", silent:bool=False):
    if not _FILE_LOADING_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("File loading functions not available in current Helios library. These require updated C++ wrapper implementation.")
    size = ctypes.c_uint()
    filename_encoded = filename.encode('utf-8')
    upaxis_encoded = upaxis.encode('utf-8')
    origin_ptr = (ctypes.c_float * len(origin))(*origin)
    rotation_ptr = (ctypes.c_float * len(rotation))(*rotation)
    color_ptr = (ctypes.c_float * len(color))(*color)
    uuids_ptr = helios_lib.loadPLYWithOriginHeightRotationColor(context, filename_encoded, origin_ptr, height, rotation_ptr, color_ptr, upaxis_encoded, silent, ctypes.byref(size))
    return list(uuids_ptr[:size.value])

# Python wrappers for loadOBJ functions
def loadOBJ(context, filename:str, silent:bool=False):
    if not _FILE_LOADING_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("File loading functions not available in current Helios library. These require updated C++ wrapper implementation.")
    size = ctypes.c_uint()
    filename_encoded = filename.encode('utf-8')
    uuids_ptr = helios_lib.loadOBJ(context, filename_encoded, silent, ctypes.byref(size))
    return list(uuids_ptr[:size.value])

def loadOBJWithOriginHeightRotationColor(context, filename:str, origin:List[float], height:float, rotation:List[float], color:List[float], silent:bool=False):
    if not _FILE_LOADING_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("File loading functions not available in current Helios library. These require updated C++ wrapper implementation.")
    size = ctypes.c_uint()
    filename_encoded = filename.encode('utf-8')
    origin_ptr = (ctypes.c_float * len(origin))(*origin)
    rotation_ptr = (ctypes.c_float * len(rotation))(*rotation)
    color_ptr = (ctypes.c_float * len(color))(*color)
    uuids_ptr = helios_lib.loadOBJWithOriginHeightRotationColor(context, filename_encoded, origin_ptr, height, rotation_ptr, color_ptr, silent, ctypes.byref(size))
    return list(uuids_ptr[:size.value])

def loadOBJWithOriginHeightRotationColorUpaxis(context, filename:str, origin:List[float], height:float, rotation:List[float], color:List[float], upaxis:str="YUP", silent:bool=False):
    if not _FILE_LOADING_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("File loading functions not available in current Helios library. These require updated C++ wrapper implementation.")
    size = ctypes.c_uint()
    filename_encoded = filename.encode('utf-8')
    upaxis_encoded = upaxis.encode('utf-8')
    origin_ptr = (ctypes.c_float * len(origin))(*origin)
    rotation_ptr = (ctypes.c_float * len(rotation))(*rotation)
    color_ptr = (ctypes.c_float * len(color))(*color)
    uuids_ptr = helios_lib.loadOBJWithOriginHeightRotationColorUpaxis(context, filename_encoded, origin_ptr, height, rotation_ptr, color_ptr, upaxis_encoded, silent, ctypes.byref(size))
    return list(uuids_ptr[:size.value])

def loadOBJWithOriginScaleRotationColorUpaxis(context, filename:str, origin:List[float], scale:List[float], rotation:List[float], color:List[float], upaxis:str="YUP", silent:bool=False):
    if not _FILE_LOADING_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("File loading functions not available in current Helios library. These require updated C++ wrapper implementation.")
    size = ctypes.c_uint()
    filename_encoded = filename.encode('utf-8')
    upaxis_encoded = upaxis.encode('utf-8')
    origin_ptr = (ctypes.c_float * len(origin))(*origin)
    scale_ptr = (ctypes.c_float * len(scale))(*scale)
    rotation_ptr = (ctypes.c_float * len(rotation))(*rotation)
    color_ptr = (ctypes.c_float * len(color))(*color)
    uuids_ptr = helios_lib.loadOBJWithOriginScaleRotationColorUpaxis(context, filename_encoded, origin_ptr, scale_ptr, rotation_ptr, color_ptr, upaxis_encoded, silent, ctypes.byref(size))
    return list(uuids_ptr[:size.value])

# Python wrapper for loadXML function
def loadXML(context, filename:str, quiet:bool=False):
    if not _FILE_LOADING_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("File loading functions not available in current Helios library. These require updated C++ wrapper implementation.")
    size = ctypes.c_uint()
    filename_encoded = filename.encode('utf-8')
    uuids_ptr = helios_lib.loadXML(context, filename_encoded, quiet, ctypes.byref(size))
    return list(uuids_ptr[:size.value])

# Python wrappers for file export functions
def writePLY(context, filename: str) -> None:
    """Write all geometry to PLY file"""
    if not _FILE_EXPORT_FUNCTIONS_AVAILABLE or 'writePLY' not in _AVAILABLE_EXPORT_FUNCTIONS:
        raise NotImplementedError(
            "writePLY function not available in current Helios library. "
            "Rebuild PyHelios with updated native interface:\n"
            "  build_scripts/build_helios --clean"
        )

    # Validate inputs
    if not filename:
        raise ValueError("Filename cannot be empty")

    filename_encoded = filename.encode('utf-8')
    # errcheck handles automatic error checking
    helios_lib.writePLY(context, filename_encoded)

def writePLYWithUUIDs(context, filename: str, uuids: List[int]) -> None:
    """Write subset of geometry to PLY file"""
    if not _FILE_EXPORT_FUNCTIONS_AVAILABLE or 'writePLYWithUUIDs' not in _AVAILABLE_EXPORT_FUNCTIONS:
        raise NotImplementedError(
            "writePLYWithUUIDs function not available in current Helios library. "
            "Rebuild PyHelios with updated native interface:\n"
            "  build_scripts/build_helios --clean"
        )

    # Validate inputs
    if not filename:
        raise ValueError("Filename cannot be empty")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty")

    filename_encoded = filename.encode('utf-8')
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.writePLYWithUUIDs(context, filename_encoded, uuids_array, len(uuids))

def writeOBJ(context, filename: str, write_normals: bool = False, silent: bool = False) -> None:
    """Write all geometry to OBJ file"""
    if not _FILE_EXPORT_FUNCTIONS_AVAILABLE or 'writeOBJ' not in _AVAILABLE_EXPORT_FUNCTIONS:
        raise NotImplementedError(
            "writeOBJ function not available in current Helios library. "
            "Rebuild PyHelios with updated native interface:\n"
            "  build_scripts/build_helios --clean"
        )

    # Validate inputs
    if not filename:
        raise ValueError("Filename cannot be empty")

    filename_encoded = filename.encode('utf-8')
    helios_lib.writeOBJ(context, filename_encoded, write_normals, silent)

def writeOBJWithUUIDs(context, filename: str, uuids: List[int], write_normals: bool = False, silent: bool = False) -> None:
    """Write subset of geometry to OBJ file"""
    if not _FILE_EXPORT_FUNCTIONS_AVAILABLE or 'writeOBJWithUUIDs' not in _AVAILABLE_EXPORT_FUNCTIONS:
        raise NotImplementedError(
            "writeOBJWithUUIDs function not available in current Helios library. "
            "Rebuild PyHelios with updated native interface:\n"
            "  build_scripts/build_helios --clean"
        )

    # Validate inputs
    if not filename:
        raise ValueError("Filename cannot be empty")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty")

    filename_encoded = filename.encode('utf-8')
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.writeOBJWithUUIDs(context, filename_encoded, uuids_array, len(uuids), write_normals, silent)

def writeOBJWithPrimitiveData(context, filename: str, uuids: List[int], data_fields: List[str], write_normals: bool = False, silent: bool = False) -> None:
    """Write geometry to OBJ file with primitive data fields"""
    if not _FILE_EXPORT_FUNCTIONS_AVAILABLE or 'writeOBJWithPrimitiveData' not in _AVAILABLE_EXPORT_FUNCTIONS:
        raise NotImplementedError(
            "writeOBJWithPrimitiveData function not available in current Helios library. "
            "Rebuild PyHelios with updated native interface:\n"
            "  build_scripts/build_helios --clean"
        )

    # Validate inputs
    if not filename:
        raise ValueError("Filename cannot be empty")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty")
    if not data_fields:
        raise ValueError("Data fields list cannot be empty")

    filename_encoded = filename.encode('utf-8')
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)

    # Create array of c_char_p for string array
    data_fields_encoded = [field.encode('utf-8') for field in data_fields]
    data_fields_array = (ctypes.c_char_p * len(data_fields_encoded))(*data_fields_encoded)

    helios_lib.writeOBJWithPrimitiveData(context, filename_encoded, uuids_array, len(uuids), data_fields_array, len(data_fields), write_normals, silent)

def writePrimitiveData(context, filename: str, column_labels: List[str], print_header: bool = False) -> None:
    """Write primitive data to ASCII file (all primitives)"""
    if not _FILE_EXPORT_FUNCTIONS_AVAILABLE or 'writePrimitiveData' not in _AVAILABLE_EXPORT_FUNCTIONS:
        raise NotImplementedError(
            "writePrimitiveData function not available in current Helios library. "
            "Rebuild PyHelios with updated native interface:\n"
            "  build_scripts/build_helios --clean"
        )

    # Validate inputs
    if not column_labels:
        raise ValueError("column_labels list cannot be empty")

    filename_encoded = filename.encode('utf-8')

    # Create array of c_char_p for string array
    labels_encoded = [label.encode('utf-8') for label in column_labels]
    labels_array = (ctypes.c_char_p * len(labels_encoded))(*labels_encoded)

    helios_lib.writePrimitiveData(context, filename_encoded, labels_array, len(column_labels), print_header)

def writePrimitiveDataWithUUIDs(context, filename: str, column_labels: List[str], uuids: List[int], print_header: bool = False) -> None:
    """Write primitive data to ASCII file (selected primitives)"""
    if not _FILE_EXPORT_FUNCTIONS_AVAILABLE or 'writePrimitiveDataWithUUIDs' not in _AVAILABLE_EXPORT_FUNCTIONS:
        raise NotImplementedError(
            "writePrimitiveDataWithUUIDs function not available in current Helios library. "
            "Rebuild PyHelios with updated native interface:\n"
            "  build_scripts/build_helios --clean"
        )

    # Validate inputs
    if not column_labels:
        raise ValueError("column_labels list cannot be empty")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty")

    filename_encoded = filename.encode('utf-8')
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)

    # Create array of c_char_p for string array
    labels_encoded = [label.encode('utf-8') for label in column_labels]
    labels_array = (ctypes.c_char_p * len(labels_encoded))(*labels_encoded)

    helios_lib.writePrimitiveDataWithUUIDs(context, filename_encoded, labels_array, len(column_labels), uuids_array, len(uuids), print_header)

# Mock mode functions for development when export functions are unavailable
if not _FILE_EXPORT_FUNCTIONS_AVAILABLE:
    def mock_writePLY(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: writePLY not available. "
            "This would export geometry to PLY format with native library."
        )

    def mock_writeOBJ(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: writeOBJ not available. "
            "This would export geometry to OBJ format with native library."
        )

    def mock_writePrimitiveData(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: writePrimitiveData not available. "
            "This would write primitive data to ASCII file with native library."
        )

    # Replace functions with mocks for development
    writePLY = mock_writePLY
    writePLYWithUUIDs = mock_writePLY
    writeOBJ = mock_writeOBJ
    writeOBJWithUUIDs = mock_writeOBJ
    writeOBJWithPrimitiveData = mock_writeOBJ
    writePrimitiveData = mock_writePrimitiveData
    writePrimitiveDataWithUUIDs = mock_writePrimitiveData

# Python wrappers for addTriangle functions
def addTriangle(context, vertex0:List[float], vertex1:List[float], vertex2:List[float]):
    if not _TRIANGLE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Triangle functions not available in current Helios library. These require updated C++ wrapper implementation.")
    vertex0_ptr = (ctypes.c_float * len(vertex0))(*vertex0)
    vertex1_ptr = (ctypes.c_float * len(vertex1))(*vertex1)
    vertex2_ptr = (ctypes.c_float * len(vertex2))(*vertex2)
    return helios_lib.addTriangle(context, vertex0_ptr, vertex1_ptr, vertex2_ptr)

def addTriangleWithColor(context, vertex0:List[float], vertex1:List[float], vertex2:List[float], color:List[float]):
    if not _TRIANGLE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Triangle functions not available in current Helios library. These require updated C++ wrapper implementation.")
    vertex0_ptr = (ctypes.c_float * len(vertex0))(*vertex0)
    vertex1_ptr = (ctypes.c_float * len(vertex1))(*vertex1)
    vertex2_ptr = (ctypes.c_float * len(vertex2))(*vertex2)
    color_ptr = (ctypes.c_float * len(color))(*color)
    return helios_lib.addTriangleWithColor(context, vertex0_ptr, vertex1_ptr, vertex2_ptr, color_ptr)

def addTriangleWithColorRGBA(context, vertex0:List[float], vertex1:List[float], vertex2:List[float], color:List[float]):
    if not _TRIANGLE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Triangle functions not available in current Helios library. These require updated C++ wrapper implementation.")
    vertex0_ptr = (ctypes.c_float * len(vertex0))(*vertex0)
    vertex1_ptr = (ctypes.c_float * len(vertex1))(*vertex1)
    vertex2_ptr = (ctypes.c_float * len(vertex2))(*vertex2)
    color_ptr = (ctypes.c_float * len(color))(*color)
    return helios_lib.addTriangleWithColorRGBA(context, vertex0_ptr, vertex1_ptr, vertex2_ptr, color_ptr)

def addTriangleWithTexture(context, vertex0:List[float], vertex1:List[float], vertex2:List[float], texture_file:str, uv0:List[float], uv1:List[float], uv2:List[float]):
    if 'addTriangleWithTexture' not in _AVAILABLE_TRIANGLE_FUNCTIONS:
        raise NotImplementedError(
            "addTriangleWithTexture function not available in current Helios library. "
            f"Available triangle functions: {', '.join(_AVAILABLE_TRIANGLE_FUNCTIONS)}. "
            "Rebuild PyHelios with updated C++ wrapper: build_scripts/build_helios"
        )
    vertex0_ptr = (ctypes.c_float * len(vertex0))(*vertex0)
    vertex1_ptr = (ctypes.c_float * len(vertex1))(*vertex1)
    vertex2_ptr = (ctypes.c_float * len(vertex2))(*vertex2)
    texture_file_encoded = texture_file.encode('utf-8')
    uv0_ptr = (ctypes.c_float * len(uv0))(*uv0)
    uv1_ptr = (ctypes.c_float * len(uv1))(*uv1)
    uv2_ptr = (ctypes.c_float * len(uv2))(*uv2)
    return helios_lib.addTriangleWithTexture(context, vertex0_ptr, vertex1_ptr, vertex2_ptr, texture_file_encoded, uv0_ptr, uv1_ptr, uv2_ptr)

def addTrianglesFromArraysMultiTextured(context, vertices, faces, 
                                       uv_coords, texture_files: List[str], 
                                       material_ids) -> List[int]:
    """
    Add textured triangles with multiple textures using material IDs.
    
    Args:
        context: Helios context
        vertices: NumPy array of shape (N, 3) containing vertex coordinates
        faces: NumPy array of shape (M, 3) containing triangle vertex indices  
        uv_coords: NumPy array of shape (N, 2) containing UV texture coordinates
        texture_files: List of texture file paths
        material_ids: NumPy array of shape (M,) containing material ID for each face
        
    Returns:
        List of UUIDs for the added textured triangles
    """
    if not _TRIANGLE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Triangle functions not available in current Helios library. These require updated C++ wrapper implementation.")
    
    # Import numpy here to avoid circular imports
    import numpy as np
    
    # Validate input arrays
    if vertices.ndim != 2 or vertices.shape[1] != 3:
        raise ValueError(f"Vertices array must have shape (N, 3), got {vertices.shape}")
    if faces.ndim != 2 or faces.shape[1] != 3:
        raise ValueError(f"Faces array must have shape (M, 3), got {faces.shape}")
    if uv_coords.ndim != 2 or uv_coords.shape[1] != 2:
        raise ValueError(f"UV coordinates array must have shape (N, 2), got {uv_coords.shape}")
    if material_ids.ndim != 1 or material_ids.shape[0] != faces.shape[0]:
        raise ValueError(f"Material IDs array must have shape (M,) where M={faces.shape[0]}, got {material_ids.shape}")
    
    # Check array consistency
    if uv_coords.shape[0] != vertices.shape[0]:
        raise ValueError(f"UV coordinates count ({uv_coords.shape[0]}) must match vertices count ({vertices.shape[0]})")
    
    # Validate material IDs
    max_material_id = np.max(material_ids)
    if max_material_id >= len(texture_files):
        raise ValueError(f"Material ID {max_material_id} exceeds texture count {len(texture_files)}")
    
    # Convert arrays to appropriate data types and flatten for C interface
    vertices_flat = vertices.astype(np.float32).flatten()
    faces_flat = faces.astype(np.uint32).flatten()
    uv_coords_flat = uv_coords.astype(np.float32).flatten()
    material_ids_array = material_ids.astype(np.uint32)
    
    vertex_count = vertices.shape[0]
    face_count = faces.shape[0]
    texture_count = len(texture_files)
    
    # Convert Python arrays to ctypes arrays
    vertices_ptr = (ctypes.c_float * len(vertices_flat))(*vertices_flat)
    faces_ptr = (ctypes.c_uint * len(faces_flat))(*faces_flat)
    uv_coords_ptr = (ctypes.c_float * len(uv_coords_flat))(*uv_coords_flat)
    material_ids_ptr = (ctypes.c_uint * len(material_ids_array))(*material_ids_array)
    
    # Encode texture file strings
    texture_files_encoded = [f.encode('utf-8') for f in texture_files]
    texture_files_ptr = (ctypes.c_char_p * len(texture_files_encoded))(*texture_files_encoded)
    
    # Result count parameter
    result_count = ctypes.c_uint()
    
    # Call C++ function
    uuids_ptr = helios_lib.addTrianglesFromArraysMultiTextured(
        context, vertices_ptr, vertex_count, faces_ptr, face_count,
        uv_coords_ptr, texture_files_ptr, texture_count, material_ids_ptr,
        ctypes.byref(result_count)
    )
    
    # Convert result to Python list
    if uuids_ptr and result_count.value > 0:
        return list(uuids_ptr[:result_count.value])
    else:
        return []

# Python wrappers for compound geometry functions
def addTile(context, center: List[float], size: List[float], rotation: List[float], subdiv: List[int]) -> List[int]:
    """Add a tile (subdivided patch) to the context"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )
    
    # Validate parameters
    if len(center) != 3:
        raise ValueError("center must have exactly 3 elements [x, y, z]")
    if len(size) != 2:
        raise ValueError("size must have exactly 2 elements [width, height]")
    if len(rotation) != 3:
        raise ValueError("rotation must have exactly 3 elements [radius, elevation, azimuth]")
    if len(subdiv) != 2:
        raise ValueError("subdiv must have exactly 2 elements [x_subdivisions, y_subdivisions]")
    
    # Convert to ctypes arrays
    center_ptr = (ctypes.c_float * 3)(*center)
    size_ptr = (ctypes.c_float * 2)(*size)
    rotation_ptr = (ctypes.c_float * 3)(*rotation)
    subdiv_ptr = (ctypes.c_int * 2)(*subdiv)
    count = ctypes.c_uint()
    
    # Call C function
    uuids_ptr = helios_lib.addTile(context, center_ptr, size_ptr, rotation_ptr, subdiv_ptr, ctypes.byref(count))
    
    # Convert result to Python list
    if uuids_ptr and count.value > 0:
        return list(uuids_ptr[:count.value])
    else:
        return []

def addTileWithColor(context, center: List[float], size: List[float], rotation: List[float], subdiv: List[int], color: List[float]) -> List[int]:
    """Add a tile (subdivided patch) with color to the context"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )
    
    # Validate parameters
    if len(center) != 3:
        raise ValueError("center must have exactly 3 elements [x, y, z]")
    if len(size) != 2:
        raise ValueError("size must have exactly 2 elements [width, height]")
    if len(rotation) != 3:
        raise ValueError("rotation must have exactly 3 elements [radius, elevation, azimuth]")
    if len(subdiv) != 2:
        raise ValueError("subdiv must have exactly 2 elements [x_subdivisions, y_subdivisions]")
    if len(color) != 3:
        raise ValueError("color must have exactly 3 elements [r, g, b]")
    
    # Convert to ctypes arrays
    center_ptr = (ctypes.c_float * 3)(*center)
    size_ptr = (ctypes.c_float * 2)(*size)
    rotation_ptr = (ctypes.c_float * 3)(*rotation)
    subdiv_ptr = (ctypes.c_int * 2)(*subdiv)
    color_ptr = (ctypes.c_float * 3)(*color)
    count = ctypes.c_uint()
    
    # Call C function
    uuids_ptr = helios_lib.addTileWithColor(context, center_ptr, size_ptr, rotation_ptr, subdiv_ptr, color_ptr, ctypes.byref(count))
    
    # Convert result to Python list
    if uuids_ptr and count.value > 0:
        return list(uuids_ptr[:count.value])
    else:
        return []

def addSphere(context, ndivs: int, center: List[float], radius: float) -> List[int]:
    """Add a sphere to the context"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )
    
    # Validate parameters
    if len(center) != 3:
        raise ValueError("center must have exactly 3 elements [x, y, z]")
    if ndivs < 3:
        raise ValueError("ndivs must be at least 3")
    if radius <= 0:
        raise ValueError("radius must be positive")
    
    # Convert to ctypes arrays
    center_ptr = (ctypes.c_float * 3)(*center)
    count = ctypes.c_uint()
    
    # Call C function
    uuids_ptr = helios_lib.addSphere(context, ndivs, center_ptr, radius, ctypes.byref(count))
    
    # Convert result to Python list
    if uuids_ptr and count.value > 0:
        return list(uuids_ptr[:count.value])
    else:
        return []

def addSphereWithColor(context, ndivs: int, center: List[float], radius: float, color: List[float]) -> List[int]:
    """Add a sphere with color to the context"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )
    
    # Validate parameters
    if len(center) != 3:
        raise ValueError("center must have exactly 3 elements [x, y, z]")
    if len(color) != 3:
        raise ValueError("color must have exactly 3 elements [r, g, b]")
    if ndivs < 3:
        raise ValueError("ndivs must be at least 3")
    if radius <= 0:
        raise ValueError("radius must be positive")
    
    # Convert to ctypes arrays
    center_ptr = (ctypes.c_float * 3)(*center)
    color_ptr = (ctypes.c_float * 3)(*color)
    count = ctypes.c_uint()
    
    # Call C function
    uuids_ptr = helios_lib.addSphereWithColor(context, ndivs, center_ptr, radius, color_ptr, ctypes.byref(count))
    
    # Convert result to Python list
    if uuids_ptr and count.value > 0:
        return list(uuids_ptr[:count.value])
    else:
        return []

def addTube(context, ndivs: int, nodes: List[float], radii: List[float]) -> List[int]:
    """Add a tube to the context"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )
    
    # Validate parameters
    if len(nodes) % 3 != 0:
        raise ValueError("nodes array length must be a multiple of 3 (x,y,z coordinates)")
    node_count = len(nodes) // 3
    if len(radii) != node_count:
        raise ValueError(f"radii array length ({len(radii)}) must match number of nodes ({node_count})")
    if ndivs < 3:
        raise ValueError("ndivs must be at least 3")
    if node_count < 2:
        raise ValueError("Must have at least 2 nodes to create a tube")
    
    # Convert to ctypes arrays
    nodes_ptr = (ctypes.c_float * len(nodes))(*nodes)
    radii_ptr = (ctypes.c_float * len(radii))(*radii)
    count = ctypes.c_uint()
    
    # Call C function
    uuids_ptr = helios_lib.addTube(context, ndivs, nodes_ptr, node_count, radii_ptr, ctypes.byref(count))
    
    # Convert result to Python list
    if uuids_ptr and count.value > 0:
        return list(uuids_ptr[:count.value])
    else:
        return []

def addTubeWithColor(context, ndivs: int, nodes: List[float], radii: List[float], colors: List[float]) -> List[int]:
    """Add a tube with colors to the context"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )
    
    # Validate parameters
    if len(nodes) % 3 != 0:
        raise ValueError("nodes array length must be a multiple of 3 (x,y,z coordinates)")
    node_count = len(nodes) // 3
    if len(radii) != node_count:
        raise ValueError(f"radii array length ({len(radii)}) must match number of nodes ({node_count})")
    if len(colors) != node_count * 3:
        raise ValueError(f"colors array length ({len(colors)}) must be 3 times the number of nodes ({node_count * 3})")
    if ndivs < 3:
        raise ValueError("ndivs must be at least 3")
    if node_count < 2:
        raise ValueError("Must have at least 2 nodes to create a tube")
    
    # Convert to ctypes arrays
    nodes_ptr = (ctypes.c_float * len(nodes))(*nodes)
    radii_ptr = (ctypes.c_float * len(radii))(*radii)
    colors_ptr = (ctypes.c_float * len(colors))(*colors)
    count = ctypes.c_uint()
    
    # Call C function
    uuids_ptr = helios_lib.addTubeWithColor(context, ndivs, nodes_ptr, node_count, radii_ptr, colors_ptr, ctypes.byref(count))
    
    # Convert result to Python list
    if uuids_ptr and count.value > 0:
        return list(uuids_ptr[:count.value])
    else:
        return []

def addBox(context, center: List[float], size: List[float], subdiv: List[int]) -> List[int]:
    """Add a box to the context"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )
    
    # Validate parameters
    if len(center) != 3:
        raise ValueError("center must have exactly 3 elements [x, y, z]")
    if len(size) != 3:
        raise ValueError("size must have exactly 3 elements [width, height, depth]")
    if len(subdiv) != 3:
        raise ValueError("subdiv must have exactly 3 elements [x_subdivisions, y_subdivisions, z_subdivisions]")
    
    # Convert to ctypes arrays
    center_ptr = (ctypes.c_float * 3)(*center)
    size_ptr = (ctypes.c_float * 3)(*size)
    subdiv_ptr = (ctypes.c_int * 3)(*subdiv)
    count = ctypes.c_uint()
    
    # Call C function
    uuids_ptr = helios_lib.addBox(context, center_ptr, size_ptr, subdiv_ptr, ctypes.byref(count))
    
    # Convert result to Python list
    if uuids_ptr and count.value > 0:
        return list(uuids_ptr[:count.value])
    else:
        return []

def addBoxWithColor(context, center: List[float], size: List[float], subdiv: List[int], color: List[float]) -> List[int]:
    """Add a box with color to the context"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )
    
    # Validate parameters
    if len(center) != 3:
        raise ValueError("center must have exactly 3 elements [x, y, z]")
    if len(size) != 3:
        raise ValueError("size must have exactly 3 elements [width, height, depth]")
    if len(subdiv) != 3:
        raise ValueError("subdiv must have exactly 3 elements [x_subdivisions, y_subdivisions, z_subdivisions]")
    if len(color) != 3:
        raise ValueError("color must have exactly 3 elements [r, g, b]")
    
    # Convert to ctypes arrays
    center_ptr = (ctypes.c_float * 3)(*center)
    size_ptr = (ctypes.c_float * 3)(*size)
    subdiv_ptr = (ctypes.c_int * 3)(*subdiv)
    color_ptr = (ctypes.c_float * 3)(*color)
    count = ctypes.c_uint()
    
    # Call C function
    uuids_ptr = helios_lib.addBoxWithColor(context, center_ptr, size_ptr, subdiv_ptr, color_ptr, ctypes.byref(count))
    
    # Convert result to Python list
    if uuids_ptr and count.value > 0:
        return list(uuids_ptr[:count.value])
    else:
        return []

def addDisk(context, ndivs: int, center: List[float], size: List[float]) -> List[int]:
    """Add a disk to the context"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Validate parameters
    if len(center) != 3:
        raise ValueError("center must have exactly 3 elements [x, y, z]")
    if len(size) != 2:
        raise ValueError("size must have exactly 2 elements [semi_major, semi_minor]")
    if ndivs < 3:
        raise ValueError("ndivs must be at least 3")

    # Convert to ctypes arrays
    center_ptr = (ctypes.c_float * 3)(*center)
    size_ptr = (ctypes.c_float * 2)(*size)
    count = ctypes.c_uint()

    # Call C function
    uuids_ptr = helios_lib.addDisk(context, ndivs, center_ptr, size_ptr, ctypes.byref(count))

    # Convert result to Python list
    if uuids_ptr and count.value > 0:
        return list(uuids_ptr[:count.value])
    else:
        return []

def addDiskWithRotation(context, ndivs: int, center: List[float], size: List[float], rotation: List[float]) -> List[int]:
    """Add a disk with rotation to the context"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Validate parameters
    if len(center) != 3:
        raise ValueError("center must have exactly 3 elements [x, y, z]")
    if len(size) != 2:
        raise ValueError("size must have exactly 2 elements [semi_major, semi_minor]")
    if len(rotation) != 3:
        raise ValueError("rotation must have exactly 3 elements [radius, elevation, azimuth]")
    if ndivs < 3:
        raise ValueError("ndivs must be at least 3")

    # Convert to ctypes arrays
    center_ptr = (ctypes.c_float * 3)(*center)
    size_ptr = (ctypes.c_float * 2)(*size)
    rotation_ptr = (ctypes.c_float * 3)(*rotation)
    count = ctypes.c_uint()

    # Call C function
    uuids_ptr = helios_lib.addDiskWithRotation(context, ndivs, center_ptr, size_ptr, rotation_ptr, ctypes.byref(count))

    # Convert result to Python list
    if uuids_ptr and count.value > 0:
        return list(uuids_ptr[:count.value])
    else:
        return []

def addDiskWithColor(context, ndivs: int, center: List[float], size: List[float], rotation: List[float], color: List[float]) -> List[int]:
    """Add a disk with color to the context"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Validate parameters
    if len(center) != 3:
        raise ValueError("center must have exactly 3 elements [x, y, z]")
    if len(size) != 2:
        raise ValueError("size must have exactly 2 elements [semi_major, semi_minor]")
    if len(rotation) != 3:
        raise ValueError("rotation must have exactly 3 elements [radius, elevation, azimuth]")
    if len(color) != 3:
        raise ValueError("color must have exactly 3 elements [r, g, b]")
    if ndivs < 3:
        raise ValueError("ndivs must be at least 3")

    # Convert to ctypes arrays
    center_ptr = (ctypes.c_float * 3)(*center)
    size_ptr = (ctypes.c_float * 2)(*size)
    rotation_ptr = (ctypes.c_float * 3)(*rotation)
    color_ptr = (ctypes.c_float * 3)(*color)
    count = ctypes.c_uint()

    # Call C function
    uuids_ptr = helios_lib.addDiskWithColor(context, ndivs, center_ptr, size_ptr, rotation_ptr, color_ptr, ctypes.byref(count))

    # Convert result to Python list
    if uuids_ptr and count.value > 0:
        return list(uuids_ptr[:count.value])
    else:
        return []

def addDiskWithRGBAColor(context, ndivs: int, center: List[float], size: List[float], rotation: List[float], color: List[float]) -> List[int]:
    """Add a disk with RGBA color to the context"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Validate parameters
    if len(center) != 3:
        raise ValueError("center must have exactly 3 elements [x, y, z]")
    if len(size) != 2:
        raise ValueError("size must have exactly 2 elements [semi_major, semi_minor]")
    if len(rotation) != 3:
        raise ValueError("rotation must have exactly 3 elements [radius, elevation, azimuth]")
    if len(color) != 4:
        raise ValueError("color must have exactly 4 elements [r, g, b, a]")
    if ndivs < 3:
        raise ValueError("ndivs must be at least 3")

    # Convert to ctypes arrays
    center_ptr = (ctypes.c_float * 3)(*center)
    size_ptr = (ctypes.c_float * 2)(*size)
    rotation_ptr = (ctypes.c_float * 3)(*rotation)
    color_ptr = (ctypes.c_float * 4)(*color)
    count = ctypes.c_uint()

    # Call C function
    uuids_ptr = helios_lib.addDiskWithRGBAColor(context, ndivs, center_ptr, size_ptr, rotation_ptr, color_ptr, ctypes.byref(count))

    # Convert result to Python list
    if uuids_ptr and count.value > 0:
        return list(uuids_ptr[:count.value])
    else:
        return []

def addDiskPolarSubdivisions(context, ndivs: List[int], center: List[float], size: List[float], rotation: List[float], color: List[float]) -> List[int]:
    """Add a disk with polar/radial subdivisions to the context"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Validate parameters
    if len(ndivs) != 2:
        raise ValueError("ndivs must have exactly 2 elements [radial_divisions, azimuthal_divisions]")
    if len(center) != 3:
        raise ValueError("center must have exactly 3 elements [x, y, z]")
    if len(size) != 2:
        raise ValueError("size must have exactly 2 elements [semi_major, semi_minor]")
    if len(rotation) != 3:
        raise ValueError("rotation must have exactly 3 elements [radius, elevation, azimuth]")
    if len(color) != 3:
        raise ValueError("color must have exactly 3 elements [r, g, b]")
    if any(n < 3 for n in ndivs):
        raise ValueError("All subdivision counts must be at least 3")

    # Convert to ctypes arrays
    ndivs_ptr = (ctypes.c_int * 2)(*ndivs)
    center_ptr = (ctypes.c_float * 3)(*center)
    size_ptr = (ctypes.c_float * 2)(*size)
    rotation_ptr = (ctypes.c_float * 3)(*rotation)
    color_ptr = (ctypes.c_float * 3)(*color)
    count = ctypes.c_uint()

    # Call C function
    uuids_ptr = helios_lib.addDiskPolarSubdivisions(context, ndivs_ptr, center_ptr, size_ptr, rotation_ptr, color_ptr, ctypes.byref(count))

    # Convert result to Python list
    if uuids_ptr and count.value > 0:
        return list(uuids_ptr[:count.value])
    else:
        return []

def addDiskPolarSubdivisionsRGBA(context, ndivs: List[int], center: List[float], size: List[float], rotation: List[float], color: List[float]) -> List[int]:
    """Add a disk with polar/radial subdivisions and RGBA color to the context"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Validate parameters
    if len(ndivs) != 2:
        raise ValueError("ndivs must have exactly 2 elements [radial_divisions, azimuthal_divisions]")
    if len(center) != 3:
        raise ValueError("center must have exactly 3 elements [x, y, z]")
    if len(size) != 2:
        raise ValueError("size must have exactly 2 elements [semi_major, semi_minor]")
    if len(rotation) != 3:
        raise ValueError("rotation must have exactly 3 elements [radius, elevation, azimuth]")
    if len(color) != 4:
        raise ValueError("color must have exactly 4 elements [r, g, b, a]")
    if any(n < 3 for n in ndivs):
        raise ValueError("All subdivision counts must be at least 3")

    # Convert to ctypes arrays
    ndivs_ptr = (ctypes.c_int * 2)(*ndivs)
    center_ptr = (ctypes.c_float * 3)(*center)
    size_ptr = (ctypes.c_float * 2)(*size)
    rotation_ptr = (ctypes.c_float * 3)(*rotation)
    color_ptr = (ctypes.c_float * 4)(*color)
    count = ctypes.c_uint()

    # Call C function
    uuids_ptr = helios_lib.addDiskPolarSubdivisionsRGBA(context, ndivs_ptr, center_ptr, size_ptr, rotation_ptr, color_ptr, ctypes.byref(count))

    # Convert result to Python list
    if uuids_ptr and count.value > 0:
        return list(uuids_ptr[:count.value])
    else:
        return []

def addCone(context, ndivs: int, node0: List[float], node1: List[float], radius0: float, radius1: float) -> List[int]:
    """Add a cone to the context"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Validate parameters
    if len(node0) != 3:
        raise ValueError("node0 must have exactly 3 elements [x, y, z]")
    if len(node1) != 3:
        raise ValueError("node1 must have exactly 3 elements [x, y, z]")
    if ndivs < 3:
        raise ValueError("Number of radial divisions must be at least 3")
    if radius0 < 0 or radius1 < 0:
        raise ValueError("Radii must be non-negative")

    # Convert to ctypes arrays
    node0_ptr = (ctypes.c_float * 3)(*node0)
    node1_ptr = (ctypes.c_float * 3)(*node1)
    count = ctypes.c_uint()

    # Call C function
    uuids_ptr = helios_lib.addCone(context, ndivs, node0_ptr, node1_ptr, radius0, radius1, ctypes.byref(count))

    # Convert result to Python list
    if uuids_ptr and count.value > 0:
        return list(uuids_ptr[:count.value])
    else:
        return []

def addConeWithColor(context, ndivs: int, node0: List[float], node1: List[float], radius0: float, radius1: float, color: List[float]) -> List[int]:
    """Add a cone with color to the context"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Validate parameters
    if len(node0) != 3:
        raise ValueError("node0 must have exactly 3 elements [x, y, z]")
    if len(node1) != 3:
        raise ValueError("node1 must have exactly 3 elements [x, y, z]")
    if len(color) != 3:
        raise ValueError("color must have exactly 3 elements [r, g, b]")
    if ndivs < 3:
        raise ValueError("Number of radial divisions must be at least 3")
    if radius0 < 0 or radius1 < 0:
        raise ValueError("Radii must be non-negative")

    # Convert to ctypes arrays
    node0_ptr = (ctypes.c_float * 3)(*node0)
    node1_ptr = (ctypes.c_float * 3)(*node1)
    color_ptr = (ctypes.c_float * 3)(*color)
    count = ctypes.c_uint()

    # Call C function
    uuids_ptr = helios_lib.addConeWithColor(context, ndivs, node0_ptr, node1_ptr, radius0, radius1, color_ptr, ctypes.byref(count))

    # Convert result to Python list
    if uuids_ptr and count.value > 0:
        return list(uuids_ptr[:count.value])
    else:
        return []

# ============================================================================
# Object-Returning Compound Geometry Wrappers
# ============================================================================

def addSphereObject_basic(context, ndivs: int, center: List[float], radius: float) -> int:
    """Add a spherical compound object (returns object ID)"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Object-returning compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if len(center) != 3:
        raise ValueError("center must have 3 elements [x, y, z]")

    center_ptr = (ctypes.c_float * 3)(*center)
    return helios_lib.addSphereObject_basic(context, ndivs, center_ptr, radius)

def addSphereObject_color(context, ndivs: int, center: List[float], radius: float, color: List[float]) -> int:
    """Add a spherical compound object with color (returns object ID)"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Object-returning compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if len(center) != 3:
        raise ValueError("center must have 3 elements [x, y, z]")
    if len(color) != 3:
        raise ValueError("color must have 3 elements [r, g, b]")

    center_ptr = (ctypes.c_float * 3)(*center)
    color_ptr = (ctypes.c_float * 3)(*color)
    return helios_lib.addSphereObject_color(context, ndivs, center_ptr, radius, color_ptr)

def addSphereObject_texture(context, ndivs: int, center: List[float], radius: float, texturefile: str) -> int:
    """Add a spherical compound object with texture (returns object ID)"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Object-returning compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if len(center) != 3:
        raise ValueError("center must have 3 elements [x, y, z]")

    center_ptr = (ctypes.c_float * 3)(*center)
    texturefile_bytes = texturefile.encode('utf-8')
    return helios_lib.addSphereObject_texture(context, ndivs, center_ptr, radius, texturefile_bytes)

def addSphereObject_ellipsoid(context, ndivs: int, center: List[float], radius: List[float]) -> int:
    """Add an ellipsoidal compound object (returns object ID)"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Object-returning compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if len(center) != 3:
        raise ValueError("center must have 3 elements [x, y, z]")
    if len(radius) != 3:
        raise ValueError("radius must have 3 elements [rx, ry, rz]")

    center_ptr = (ctypes.c_float * 3)(*center)
    radius_ptr = (ctypes.c_float * 3)(*radius)
    return helios_lib.addSphereObject_ellipsoid(context, ndivs, center_ptr, radius_ptr)

def addSphereObject_ellipsoid_color(context, ndivs: int, center: List[float], radius: List[float], color: List[float]) -> int:
    """Add an ellipsoidal compound object with color (returns object ID)"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Object-returning compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if len(center) != 3:
        raise ValueError("center must have 3 elements [x, y, z]")
    if len(radius) != 3:
        raise ValueError("radius must have 3 elements [rx, ry, rz]")
    if len(color) != 3:
        raise ValueError("color must have 3 elements [r, g, b]")

    center_ptr = (ctypes.c_float * 3)(*center)
    radius_ptr = (ctypes.c_float * 3)(*radius)
    color_ptr = (ctypes.c_float * 3)(*color)
    return helios_lib.addSphereObject_ellipsoid_color(context, ndivs, center_ptr, radius_ptr, color_ptr)

def addSphereObject_ellipsoid_texture(context, ndivs: int, center: List[float], radius: List[float], texturefile: str) -> int:
    """Add an ellipsoidal compound object with texture (returns object ID)"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Object-returning compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if len(center) != 3:
        raise ValueError("center must have 3 elements [x, y, z]")
    if len(radius) != 3:
        raise ValueError("radius must have 3 elements [rx, ry, rz]")

    center_ptr = (ctypes.c_float * 3)(*center)
    radius_ptr = (ctypes.c_float * 3)(*radius)
    texturefile_bytes = texturefile.encode('utf-8')
    return helios_lib.addSphereObject_ellipsoid_texture(context, ndivs, center_ptr, radius_ptr, texturefile_bytes)

def addTileObject_basic(context, center: List[float], size: List[float], rotation: List[float], subdiv: List[int]) -> int:
    """Add a tiled patch object (returns object ID)"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Object-returning compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if len(center) != 3:
        raise ValueError("center must have 3 elements [x, y, z]")
    if len(size) != 2:
        raise ValueError("size must have 2 elements [x, y]")
    if len(rotation) != 3:
        raise ValueError("rotation must have 3 elements [radius, elevation, azimuth]")
    if len(subdiv) != 2:
        raise ValueError("subdiv must have 2 elements [x, y]")

    center_ptr = (ctypes.c_float * 3)(*center)
    size_ptr = (ctypes.c_float * 2)(*size)
    rotation_ptr = (ctypes.c_float * 3)(*rotation)
    subdiv_ptr = (ctypes.c_int * 2)(*subdiv)
    return helios_lib.addTileObject_basic(context, center_ptr, size_ptr, rotation_ptr, subdiv_ptr)

def addTileObject_color(context, center: List[float], size: List[float], rotation: List[float], subdiv: List[int], color: List[float]) -> int:
    """Add a tiled patch object with color (returns object ID)"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Object-returning compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if len(center) != 3:
        raise ValueError("center must have 3 elements [x, y, z]")
    if len(size) != 2:
        raise ValueError("size must have 2 elements [x, y]")
    if len(rotation) != 3:
        raise ValueError("rotation must have 3 elements [radius, elevation, azimuth]")
    if len(subdiv) != 2:
        raise ValueError("subdiv must have 2 elements [x, y]")
    if len(color) != 3:
        raise ValueError("color must have 3 elements [r, g, b]")

    center_ptr = (ctypes.c_float * 3)(*center)
    size_ptr = (ctypes.c_float * 2)(*size)
    rotation_ptr = (ctypes.c_float * 3)(*rotation)
    subdiv_ptr = (ctypes.c_int * 2)(*subdiv)
    color_ptr = (ctypes.c_float * 3)(*color)
    return helios_lib.addTileObject_color(context, center_ptr, size_ptr, rotation_ptr, subdiv_ptr, color_ptr)

def addTileObject_texture(context, center: List[float], size: List[float], rotation: List[float], subdiv: List[int], texturefile: str) -> int:
    """Add a tiled patch object with texture (returns object ID)"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Object-returning compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if len(center) != 3:
        raise ValueError("center must have 3 elements [x, y, z]")
    if len(size) != 2:
        raise ValueError("size must have 2 elements [x, y]")
    if len(rotation) != 3:
        raise ValueError("rotation must have 3 elements [radius, elevation, azimuth]")
    if len(subdiv) != 2:
        raise ValueError("subdiv must have 2 elements [x, y]")

    center_ptr = (ctypes.c_float * 3)(*center)
    size_ptr = (ctypes.c_float * 2)(*size)
    rotation_ptr = (ctypes.c_float * 3)(*rotation)
    subdiv_ptr = (ctypes.c_int * 2)(*subdiv)
    texturefile_bytes = texturefile.encode('utf-8')
    return helios_lib.addTileObject_texture(context, center_ptr, size_ptr, rotation_ptr, subdiv_ptr, texturefile_bytes)

def addTileObject_texture_repeat(context, center: List[float], size: List[float], rotation: List[float], subdiv: List[int], texturefile: str, texture_repeat: List[int]) -> int:
    """Add a tiled patch object with texture and repeat (returns object ID)"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Object-returning compound geometry functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if len(center) != 3:
        raise ValueError("center must have 3 elements [x, y, z]")
    if len(size) != 2:
        raise ValueError("size must have 2 elements [x, y]")
    if len(rotation) != 3:
        raise ValueError("rotation must have 3 elements [radius, elevation, azimuth]")
    if len(subdiv) != 2:
        raise ValueError("subdiv must have 2 elements [x, y]")
    if len(texture_repeat) != 2:
        raise ValueError("texture_repeat must have 2 elements [x, y]")

    center_ptr = (ctypes.c_float * 3)(*center)
    size_ptr = (ctypes.c_float * 2)(*size)
    rotation_ptr = (ctypes.c_float * 3)(*rotation)
    subdiv_ptr = (ctypes.c_int * 2)(*subdiv)
    texture_repeat_ptr = (ctypes.c_int * 2)(*texture_repeat)
    texturefile_bytes = texturefile.encode('utf-8')
    return helios_lib.addTileObject_texture_repeat(context, center_ptr, size_ptr, rotation_ptr, subdiv_ptr, texturefile_bytes, texture_repeat_ptr)

def addBoxObject_basic(context, center: List[float], size: List[float], subdiv: List[int]) -> int:
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Object-returning compound geometry functions not available.")
    if len(center) != 3 or len(size) != 3 or len(subdiv) != 3:
        raise ValueError("center, size, and subdiv must have 3 elements")
    return helios_lib.addBoxObject_basic(context, (ctypes.c_float * 3)(*center), (ctypes.c_float * 3)(*size), (ctypes.c_int * 3)(*subdiv))

def addBoxObject_color(context, center: List[float], size: List[float], subdiv: List[int], color: List[float]) -> int:
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Object-returning compound geometry functions not available.")
    if len(center) != 3 or len(size) != 3 or len(subdiv) != 3 or len(color) != 3:
        raise ValueError("center, size, subdiv, and color must have 3 elements")
    return helios_lib.addBoxObject_color(context, (ctypes.c_float * 3)(*center), (ctypes.c_float * 3)(*size), (ctypes.c_int * 3)(*subdiv), (ctypes.c_float * 3)(*color))

def addBoxObject_texture(context, center: List[float], size: List[float], subdiv: List[int], texturefile: str) -> int:
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Object-returning compound geometry functions not available.")
    if len(center) != 3 or len(size) != 3 or len(subdiv) != 3:
        raise ValueError("center, size, and subdiv must have 3 elements")
    return helios_lib.addBoxObject_texture(context, (ctypes.c_float * 3)(*center), (ctypes.c_float * 3)(*size), (ctypes.c_int * 3)(*subdiv), texturefile.encode('utf-8'))

def addBoxObject_color_reverse(context, center: List[float], size: List[float], subdiv: List[int], color: List[float], reverse_normals: bool) -> int:
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Object-returning compound geometry functions not available.")
    if len(center) != 3 or len(size) != 3 or len(subdiv) != 3 or len(color) != 3:
        raise ValueError("center, size, subdiv, and color must have 3 elements")
    return helios_lib.addBoxObject_color_reverse(context, (ctypes.c_float * 3)(*center), (ctypes.c_float * 3)(*size), (ctypes.c_int * 3)(*subdiv), (ctypes.c_float * 3)(*color), reverse_normals)

def addBoxObject_texture_reverse(context, center: List[float], size: List[float], subdiv: List[int], texturefile: str, reverse_normals: bool) -> int:
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Object-returning compound geometry functions not available.")
    if len(center) != 3 or len(size) != 3 or len(subdiv) != 3:
        raise ValueError("center, size, and subdiv must have 3 elements")
    return helios_lib.addBoxObject_texture_reverse(context, (ctypes.c_float * 3)(*center), (ctypes.c_float * 3)(*size), (ctypes.c_int * 3)(*subdiv), texturefile.encode('utf-8'), reverse_normals)

def addConeObject_basic(context, ndivs: int, node0: List[float], node1: List[float], radius0: float, radius1: float) -> int:
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Object-returning compound geometry functions not available.")
    if len(node0) != 3 or len(node1) != 3:
        raise ValueError("node0 and node1 must have 3 elements")
    return helios_lib.addConeObject_basic(context, ndivs, (ctypes.c_float * 3)(*node0), (ctypes.c_float * 3)(*node1), radius0, radius1)

def addConeObject_color(context, ndivs: int, node0: List[float], node1: List[float], radius0: float, radius1: float, color: List[float]) -> int:
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Object-returning compound geometry functions not available.")
    if len(node0) != 3 or len(node1) != 3 or len(color) != 3:
        raise ValueError("node0, node1, and color must have 3 elements")
    return helios_lib.addConeObject_color(context, ndivs, (ctypes.c_float * 3)(*node0), (ctypes.c_float * 3)(*node1), radius0, radius1, (ctypes.c_float * 3)(*color))

def addConeObject_texture(context, ndivs: int, node0: List[float], node1: List[float], radius0: float, radius1: float, texturefile: str) -> int:
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Object-returning compound geometry functions not available.")
    if len(node0) != 3 or len(node1) != 3:
        raise ValueError("node0 and node1 must have 3 elements")
    return helios_lib.addConeObject_texture(context, ndivs, (ctypes.c_float * 3)(*node0), (ctypes.c_float * 3)(*node1), radius0, radius1, texturefile.encode('utf-8'))

def addDiskObject_basic(context, ndivs: int, center: List[float], size: List[float]) -> int:
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Object-returning compound geometry functions not available.")
    if len(center) != 3 or len(size) != 2:
        raise ValueError("center must have 3 elements, size must have 2")
    return helios_lib.addDiskObject_basic(context, ndivs, (ctypes.c_float * 3)(*center), (ctypes.c_float * 2)(*size))

def addDiskObject_rotation(context, ndivs: int, center: List[float], size: List[float], rotation: List[float]) -> int:
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Object-returning compound geometry functions not available.")
    if len(center) != 3 or len(size) != 2 or len(rotation) != 3:
        raise ValueError("Incorrect parameter dimensions")
    return helios_lib.addDiskObject_rotation(context, ndivs, (ctypes.c_float * 3)(*center), (ctypes.c_float * 2)(*size), (ctypes.c_float * 3)(*rotation))

def addDiskObject_color(context, ndivs: int, center: List[float], size: List[float], rotation: List[float], color: List[float]) -> int:
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Object-returning compound geometry functions not available.")
    if len(center) != 3 or len(size) != 2 or len(rotation) != 3 or len(color) != 3:
        raise ValueError("Incorrect parameter dimensions")
    return helios_lib.addDiskObject_color(context, ndivs, (ctypes.c_float * 3)(*center), (ctypes.c_float * 2)(*size), (ctypes.c_float * 3)(*rotation), (ctypes.c_float * 3)(*color))

def addDiskObject_rgba(context, ndivs: int, center: List[float], size: List[float], rotation: List[float], color: List[float]) -> int:
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Object-returning compound geometry functions not available.")
    if len(center) != 3 or len(size) != 2 or len(rotation) != 3 or len(color) != 4:
        raise ValueError("Incorrect parameter dimensions (color needs 4 for RGBA)")
    return helios_lib.addDiskObject_rgba(context, ndivs, (ctypes.c_float * 3)(*center), (ctypes.c_float * 2)(*size), (ctypes.c_float * 3)(*rotation), (ctypes.c_float * 4)(*color))

def addDiskObject_texture(context, ndivs: int, center: List[float], size: List[float], rotation: List[float], texturefile: str) -> int:
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Object-returning compound geometry functions not available.")
    if len(center) != 3 or len(size) != 2 or len(rotation) != 3:
        raise ValueError("Incorrect parameter dimensions")
    return helios_lib.addDiskObject_texture(context, ndivs, (ctypes.c_float * 3)(*center), (ctypes.c_float * 2)(*size), (ctypes.c_float * 3)(*rotation), texturefile.encode('utf-8'))

def addDiskObject_polar_color(context, ndivs: List[int], center: List[float], size: List[float], rotation: List[float], color: List[float]) -> int:
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Object-returning compound geometry functions not available.")
    if len(ndivs) != 2 or len(center) != 3 or len(size) != 2 or len(rotation) != 3 or len(color) != 3:
        raise ValueError("Incorrect parameter dimensions")
    return helios_lib.addDiskObject_polar_color(context, (ctypes.c_int * 2)(*ndivs), (ctypes.c_float * 3)(*center), (ctypes.c_float * 2)(*size), (ctypes.c_float * 3)(*rotation), (ctypes.c_float * 3)(*color))

def addDiskObject_polar_rgba(context, ndivs: List[int], center: List[float], size: List[float], rotation: List[float], color: List[float]) -> int:
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Object-returning compound geometry functions not available.")
    if len(ndivs) != 2 or len(center) != 3 or len(size) != 2 or len(rotation) != 3 or len(color) != 4:
        raise ValueError("Incorrect parameter dimensions (color needs 4 for RGBA)")
    return helios_lib.addDiskObject_polar_rgba(context, (ctypes.c_int * 2)(*ndivs), (ctypes.c_float * 3)(*center), (ctypes.c_float * 2)(*size), (ctypes.c_float * 3)(*rotation), (ctypes.c_float * 4)(*color))

def addDiskObject_polar_texture(context, ndivs: List[int], center: List[float], size: List[float], rotation: List[float], texturefile: str) -> int:
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Object-returning compound geometry functions not available.")
    if len(ndivs) != 2 or len(center) != 3 or len(size) != 2 or len(rotation) != 3:
        raise ValueError("Incorrect parameter dimensions")
    return helios_lib.addDiskObject_polar_texture(context, (ctypes.c_int * 2)(*ndivs), (ctypes.c_float * 3)(*center), (ctypes.c_float * 2)(*size), (ctypes.c_float * 3)(*rotation), texturefile.encode('utf-8'))

def addTubeObject_basic(context, radial_subdivisions: int, nodes: List[float], radii: List[float]) -> int:
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Object-returning compound geometry functions not available.")
    if len(nodes) % 3 != 0:
        raise ValueError("nodes must be a multiple of 3 (flattened vec3 array)")
    node_count = len(nodes) // 3
    nodes_ptr = (ctypes.c_float * len(nodes))(*nodes)
    radii_ptr = (ctypes.c_float * len(radii))(*radii)
    return helios_lib.addTubeObject_basic(context, radial_subdivisions, nodes_ptr, node_count, radii_ptr, len(radii))

def addTubeObject_color(context, radial_subdivisions: int, nodes: List[float], radii: List[float], colors: List[float]) -> int:
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Object-returning compound geometry functions not available.")
    if len(nodes) % 3 != 0 or len(colors) % 3 != 0:
        raise ValueError("nodes and colors must be multiples of 3")
    node_count = len(nodes) // 3
    color_count = len(colors) // 3
    nodes_ptr = (ctypes.c_float * len(nodes))(*nodes)
    radii_ptr = (ctypes.c_float * len(radii))(*radii)
    colors_ptr = (ctypes.c_float * len(colors))(*colors)
    return helios_lib.addTubeObject_color(context, radial_subdivisions, nodes_ptr, node_count, radii_ptr, len(radii), colors_ptr, color_count)

def addTubeObject_texture(context, radial_subdivisions: int, nodes: List[float], radii: List[float], texturefile: str) -> int:
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Object-returning compound geometry functions not available.")
    if len(nodes) % 3 != 0:
        raise ValueError("nodes must be a multiple of 3")
    node_count = len(nodes) // 3
    nodes_ptr = (ctypes.c_float * len(nodes))(*nodes)
    radii_ptr = (ctypes.c_float * len(radii))(*radii)
    return helios_lib.addTubeObject_texture(context, radial_subdivisions, nodes_ptr, node_count, radii_ptr, len(radii), texturefile.encode('utf-8'))

def addTubeObject_texture_uv(context, radial_subdivisions: int, nodes: List[float], radii: List[float], texturefile: str, textureuv_ufrac: List[float]) -> int:
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Object-returning compound geometry functions not available.")
    if len(nodes) % 3 != 0:
        raise ValueError("nodes must be a multiple of 3")
    node_count = len(nodes) // 3
    nodes_ptr = (ctypes.c_float * len(nodes))(*nodes)
    radii_ptr = (ctypes.c_float * len(radii))(*radii)
    uv_ptr = (ctypes.c_float * len(textureuv_ufrac))(*textureuv_ufrac)
    return helios_lib.addTubeObject_texture_uv(context, radial_subdivisions, nodes_ptr, node_count, radii_ptr, len(radii), texturefile.encode('utf-8'), uv_ptr, len(textureuv_ufrac))

def copyPrimitive(context, uuid: int) -> int:
    """Copy a single primitive"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Copy functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Call C function
    result = helios_lib.copyPrimitive(context, uuid)
    return result

def copyPrimitives(context, uuids: List[int]) -> List[int]:
    """Copy multiple primitives"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Copy functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if not uuids:
        return []

    # Convert to ctypes array
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)
    result_count = ctypes.c_uint()

    # Call C function
    result_ptr = helios_lib.copyPrimitives(context, uuids_array, len(uuids), ctypes.byref(result_count))

    # Convert result to Python list
    if result_ptr and result_count.value > 0:
        return list(result_ptr[:result_count.value])
    else:
        return []

def copyPrimitiveData(context, sourceUUID: int, destinationUUID: int) -> None:
    """Copy all primitive data from source to destination"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Copy functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Call C function
    helios_lib.copyPrimitiveData(context, sourceUUID, destinationUUID)

def copyObject(context, objID: int) -> int:
    """Copy a single object"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Copy functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Call C function
    result = helios_lib.copyObject(context, objID)
    return result

def copyObjects(context, objIDs: List[int]) -> List[int]:
    """Copy multiple objects"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Copy functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if not objIDs:
        return []

    # Convert to ctypes array
    objIDs_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    result_count = ctypes.c_uint()

    # Call C function
    result_ptr = helios_lib.copyObjects(context, objIDs_array, len(objIDs), ctypes.byref(result_count))

    # Convert result to Python list
    if result_ptr and result_count.value > 0:
        return list(result_ptr[:result_count.value])
    else:
        return []

def copyObjectData(context, source_objID: int, destination_objID: int) -> None:
    """Copy all object data from source to destination"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Copy functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Call C function
    helios_lib.copyObjectData(context, source_objID, destination_objID)

def translatePrimitive(context, uuid: int, shift: List[float]) -> None:
    """Translate a single primitive"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Translation functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Validate parameters
    if len(shift) != 3:
        raise ValueError("Shift must have exactly 3 elements [x, y, z]")

    # Convert to ctypes array
    shift_ptr = (ctypes.c_float * 3)(*shift)

    # Call C function
    helios_lib.translatePrimitive(context, uuid, shift_ptr)

def translatePrimitives(context, uuids: List[int], shift: List[float]) -> None:
    """Translate multiple primitives"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Translation functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if not uuids:
        return  # Nothing to translate

    # Validate parameters
    if len(shift) != 3:
        raise ValueError("Shift must have exactly 3 elements [x, y, z]")

    # Convert to ctypes arrays
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)
    shift_ptr = (ctypes.c_float * 3)(*shift)

    # Call C function
    helios_lib.translatePrimitives(context, uuids_array, len(uuids), shift_ptr)

def translateObject(context, objID: int, shift: List[float]) -> None:
    """Translate a single object"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Translation functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Validate parameters
    if len(shift) != 3:
        raise ValueError("Shift must have exactly 3 elements [x, y, z]")

    # Convert to ctypes array
    shift_ptr = (ctypes.c_float * 3)(*shift)

    # Call C function
    helios_lib.translateObject(context, objID, shift_ptr)

def translateObjects(context, objIDs: List[int], shift: List[float]) -> None:
    """Translate multiple objects"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Translation functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if not objIDs:
        return  # Nothing to translate

    # Validate parameters
    if len(shift) != 3:
        raise ValueError("Shift must have exactly 3 elements [x, y, z]")

    # Convert to ctypes arrays
    objIDs_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    shift_ptr = (ctypes.c_float * 3)(*shift)

    # Call C function
    helios_lib.translateObjects(context, objIDs_array, len(objIDs), shift_ptr)

# ==================== Rotation Functions ====================

def rotatePrimitive_axisString(context, uuid: int, rotation_radians: float, axis: str) -> None:
    """Rotate a single primitive around an axis specified by string"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Rotation functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Validate axis parameter
    if axis not in ('x', 'y', 'z'):
        raise ValueError("Axis must be 'x', 'y', or 'z'")

    # Encode axis string to bytes
    axis_bytes = axis.encode('utf-8')

    # Call C function
    helios_lib.rotatePrimitive_axisString(context, uuid, rotation_radians, axis_bytes)

def rotatePrimitives_axisString(context, uuids: List[int], rotation_radians: float, axis: str) -> None:
    """Rotate multiple primitives around an axis specified by string"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Rotation functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if not uuids:
        return  # Nothing to rotate

    # Validate axis parameter
    if axis not in ('x', 'y', 'z'):
        raise ValueError("Axis must be 'x', 'y', or 'z'")

    # Convert to ctypes array
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)
    axis_bytes = axis.encode('utf-8')

    # Call C function
    helios_lib.rotatePrimitives_axisString(context, uuids_array, len(uuids), rotation_radians, axis_bytes)

def rotatePrimitive_axisVector(context, uuid: int, rotation_radians: float, axis: List[float]) -> None:
    """Rotate a single primitive around an axis specified by vector"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Rotation functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Validate parameters
    if len(axis) != 3:
        raise ValueError("Axis must have exactly 3 elements [x, y, z]")

    # Convert to ctypes array
    axis_ptr = (ctypes.c_float * 3)(*axis)

    # Call C function
    helios_lib.rotatePrimitive_axisVector(context, uuid, rotation_radians, axis_ptr)

def rotatePrimitives_axisVector(context, uuids: List[int], rotation_radians: float, axis: List[float]) -> None:
    """Rotate multiple primitives around an axis specified by vector"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Rotation functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if not uuids:
        return  # Nothing to rotate

    # Validate parameters
    if len(axis) != 3:
        raise ValueError("Axis must have exactly 3 elements [x, y, z]")

    # Convert to ctypes arrays
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)
    axis_ptr = (ctypes.c_float * 3)(*axis)

    # Call C function
    helios_lib.rotatePrimitives_axisVector(context, uuids_array, len(uuids), rotation_radians, axis_ptr)

def rotatePrimitive_originAxisVector(context, uuid: int, rotation_radians: float, origin: List[float], axis: List[float]) -> None:
    """Rotate a single primitive around an axis through a specified origin point"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Rotation functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Validate parameters
    if len(origin) != 3:
        raise ValueError("Origin must have exactly 3 elements [x, y, z]")
    if len(axis) != 3:
        raise ValueError("Axis must have exactly 3 elements [x, y, z]")

    # Convert to ctypes arrays
    origin_ptr = (ctypes.c_float * 3)(*origin)
    axis_ptr = (ctypes.c_float * 3)(*axis)

    # Call C function
    helios_lib.rotatePrimitive_originAxisVector(context, uuid, rotation_radians, origin_ptr, axis_ptr)

def rotatePrimitives_originAxisVector(context, uuids: List[int], rotation_radians: float, origin: List[float], axis: List[float]) -> None:
    """Rotate multiple primitives around an axis through a specified origin point"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Rotation functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if not uuids:
        return  # Nothing to rotate

    # Validate parameters
    if len(origin) != 3:
        raise ValueError("Origin must have exactly 3 elements [x, y, z]")
    if len(axis) != 3:
        raise ValueError("Axis must have exactly 3 elements [x, y, z]")

    # Convert to ctypes arrays
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)
    origin_ptr = (ctypes.c_float * 3)(*origin)
    axis_ptr = (ctypes.c_float * 3)(*axis)

    # Call C function
    helios_lib.rotatePrimitives_originAxisVector(context, uuids_array, len(uuids), rotation_radians, origin_ptr, axis_ptr)

def rotateObject_axisString(context, objID: int, rotation_radians: float, axis: str) -> None:
    """Rotate a single object around an axis specified by string"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Rotation functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Validate axis parameter
    if axis not in ('x', 'y', 'z'):
        raise ValueError("Axis must be 'x', 'y', or 'z'")

    # Encode axis string to bytes
    axis_bytes = axis.encode('utf-8')

    # Call C function
    helios_lib.rotateObject_axisString(context, objID, rotation_radians, axis_bytes)

def rotateObjects_axisString(context, objIDs: List[int], rotation_radians: float, axis: str) -> None:
    """Rotate multiple objects around an axis specified by string"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Rotation functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if not objIDs:
        return  # Nothing to rotate

    # Validate axis parameter
    if axis not in ('x', 'y', 'z'):
        raise ValueError("Axis must be 'x', 'y', or 'z'")

    # Convert to ctypes array
    objIDs_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    axis_bytes = axis.encode('utf-8')

    # Call C function
    helios_lib.rotateObjects_axisString(context, objIDs_array, len(objIDs), rotation_radians, axis_bytes)

def rotateObject_axisVector(context, objID: int, rotation_radians: float, axis: List[float]) -> None:
    """Rotate a single object around an axis specified by vector"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Rotation functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Validate parameters
    if len(axis) != 3:
        raise ValueError("Axis must have exactly 3 elements [x, y, z]")

    # Convert to ctypes array
    axis_ptr = (ctypes.c_float * 3)(*axis)

    # Call C function
    helios_lib.rotateObject_axisVector(context, objID, rotation_radians, axis_ptr)

def rotateObjects_axisVector(context, objIDs: List[int], rotation_radians: float, axis: List[float]) -> None:
    """Rotate multiple objects around an axis specified by vector"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Rotation functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if not objIDs:
        return  # Nothing to rotate

    # Validate parameters
    if len(axis) != 3:
        raise ValueError("Axis must have exactly 3 elements [x, y, z]")

    # Convert to ctypes arrays
    objIDs_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    axis_ptr = (ctypes.c_float * 3)(*axis)

    # Call C function
    helios_lib.rotateObjects_axisVector(context, objIDs_array, len(objIDs), rotation_radians, axis_ptr)

def rotateObject_originAxisVector(context, objID: int, rotation_radians: float, origin: List[float], axis: List[float]) -> None:
    """Rotate a single object around an axis through a specified origin point"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Rotation functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Validate parameters
    if len(origin) != 3:
        raise ValueError("Origin must have exactly 3 elements [x, y, z]")
    if len(axis) != 3:
        raise ValueError("Axis must have exactly 3 elements [x, y, z]")

    # Convert to ctypes arrays
    origin_ptr = (ctypes.c_float * 3)(*origin)
    axis_ptr = (ctypes.c_float * 3)(*axis)

    # Call C function
    helios_lib.rotateObject_originAxisVector(context, objID, rotation_radians, origin_ptr, axis_ptr)

def rotateObjects_originAxisVector(context, objIDs: List[int], rotation_radians: float, origin: List[float], axis: List[float]) -> None:
    """Rotate multiple objects around an axis through a specified origin point"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Rotation functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if not objIDs:
        return  # Nothing to rotate

    # Validate parameters
    if len(origin) != 3:
        raise ValueError("Origin must have exactly 3 elements [x, y, z]")
    if len(axis) != 3:
        raise ValueError("Axis must have exactly 3 elements [x, y, z]")

    # Convert to ctypes arrays
    objIDs_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    origin_ptr = (ctypes.c_float * 3)(*origin)
    axis_ptr = (ctypes.c_float * 3)(*axis)

    # Call C function
    helios_lib.rotateObjects_originAxisVector(context, objIDs_array, len(objIDs), rotation_radians, origin_ptr, axis_ptr)

def rotateObjectAboutOrigin_axisVector(context, objID: int, rotation_radians: float, axis: List[float]) -> None:
    """Rotate a single object about the global origin around an axis specified by vector"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Rotation functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Validate parameters
    if len(axis) != 3:
        raise ValueError("Axis must have exactly 3 elements [x, y, z]")

    # Convert to ctypes array
    axis_ptr = (ctypes.c_float * 3)(*axis)

    # Call C function
    helios_lib.rotateObjectAboutOrigin_axisVector(context, objID, rotation_radians, axis_ptr)

def rotateObjectsAboutOrigin_axisVector(context, objIDs: List[int], rotation_radians: float, axis: List[float]) -> None:
    """Rotate multiple objects about the global origin around an axis specified by vector"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Rotation functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if not objIDs:
        return  # Nothing to rotate

    # Validate parameters
    if len(axis) != 3:
        raise ValueError("Axis must have exactly 3 elements [x, y, z]")

    # Convert to ctypes arrays
    objIDs_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    axis_ptr = (ctypes.c_float * 3)(*axis)

    # Call C function
    helios_lib.rotateObjectsAboutOrigin_axisVector(context, objIDs_array, len(objIDs), rotation_radians, axis_ptr)

# ==================== Scaling Functions ====================

def scalePrimitive(context, uuid: int, scale: List[float]) -> None:
    """Scale a single primitive"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Scaling functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Validate parameters
    if len(scale) != 3:
        raise ValueError("Scale must have exactly 3 elements [x, y, z]")

    # Convert to ctypes array
    scale_ptr = (ctypes.c_float * 3)(*scale)

    # Call C function
    helios_lib.scalePrimitive(context, uuid, scale_ptr)

def scalePrimitives(context, uuids: List[int], scale: List[float]) -> None:
    """Scale multiple primitives"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Scaling functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if not uuids:
        return  # Nothing to scale

    # Validate parameters
    if len(scale) != 3:
        raise ValueError("Scale must have exactly 3 elements [x, y, z]")

    # Convert to ctypes arrays
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)
    scale_ptr = (ctypes.c_float * 3)(*scale)

    # Call C function
    helios_lib.scalePrimitives(context, uuids_array, len(uuids), scale_ptr)

def scalePrimitiveAboutPoint(context, uuid: int, scale: List[float], point: List[float]) -> None:
    """Scale a single primitive about a specified point"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Scaling functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Validate parameters
    if len(scale) != 3:
        raise ValueError("Scale must have exactly 3 elements [x, y, z]")
    if len(point) != 3:
        raise ValueError("Point must have exactly 3 elements [x, y, z]")

    # Convert to ctypes arrays
    scale_ptr = (ctypes.c_float * 3)(*scale)
    point_ptr = (ctypes.c_float * 3)(*point)

    # Call C function
    helios_lib.scalePrimitiveAboutPoint(context, uuid, scale_ptr, point_ptr)

def scalePrimitivesAboutPoint(context, uuids: List[int], scale: List[float], point: List[float]) -> None:
    """Scale multiple primitives about a specified point"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Scaling functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if not uuids:
        return  # Nothing to scale

    # Validate parameters
    if len(scale) != 3:
        raise ValueError("Scale must have exactly 3 elements [x, y, z]")
    if len(point) != 3:
        raise ValueError("Point must have exactly 3 elements [x, y, z]")

    # Convert to ctypes arrays
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)
    scale_ptr = (ctypes.c_float * 3)(*scale)
    point_ptr = (ctypes.c_float * 3)(*point)

    # Call C function
    helios_lib.scalePrimitivesAboutPoint(context, uuids_array, len(uuids), scale_ptr, point_ptr)

def scaleObject(context, objID: int, scale: List[float]) -> None:
    """Scale a single object"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Scaling functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Validate parameters
    if len(scale) != 3:
        raise ValueError("Scale must have exactly 3 elements [x, y, z]")

    # Convert to ctypes array
    scale_ptr = (ctypes.c_float * 3)(*scale)

    # Call C function
    helios_lib.scaleObject(context, objID, scale_ptr)

def scaleObjects(context, objIDs: List[int], scale: List[float]) -> None:
    """Scale multiple objects"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Scaling functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if not objIDs:
        return  # Nothing to scale

    # Validate parameters
    if len(scale) != 3:
        raise ValueError("Scale must have exactly 3 elements [x, y, z]")

    # Convert to ctypes arrays
    objIDs_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    scale_ptr = (ctypes.c_float * 3)(*scale)

    # Call C function
    helios_lib.scaleObjects(context, objIDs_array, len(objIDs), scale_ptr)

def scaleObjectAboutCenter(context, objID: int, scale: List[float]) -> None:
    """Scale a single object about its center"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Scaling functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Validate parameters
    if len(scale) != 3:
        raise ValueError("Scale must have exactly 3 elements [x, y, z]")

    # Convert to ctypes array
    scale_ptr = (ctypes.c_float * 3)(*scale)

    # Call C function
    helios_lib.scaleObjectAboutCenter(context, objID, scale_ptr)

def scaleObjectsAboutCenter(context, objIDs: List[int], scale: List[float]) -> None:
    """Scale multiple objects about their centers"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Scaling functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if not objIDs:
        return  # Nothing to scale

    # Validate parameters
    if len(scale) != 3:
        raise ValueError("Scale must have exactly 3 elements [x, y, z]")

    # Convert to ctypes arrays
    objIDs_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    scale_ptr = (ctypes.c_float * 3)(*scale)

    # Call C function
    helios_lib.scaleObjectsAboutCenter(context, objIDs_array, len(objIDs), scale_ptr)

def scaleObjectAboutPoint(context, objID: int, scale: List[float], point: List[float]) -> None:
    """Scale a single object about a specified point"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Scaling functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Validate parameters
    if len(scale) != 3:
        raise ValueError("Scale must have exactly 3 elements [x, y, z]")
    if len(point) != 3:
        raise ValueError("Point must have exactly 3 elements [x, y, z]")

    # Convert to ctypes arrays
    scale_ptr = (ctypes.c_float * 3)(*scale)
    point_ptr = (ctypes.c_float * 3)(*point)

    # Call C function
    helios_lib.scaleObjectAboutPoint(context, objID, scale_ptr, point_ptr)

def scaleObjectsAboutPoint(context, objIDs: List[int], scale: List[float], point: List[float]) -> None:
    """Scale multiple objects about a specified point"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Scaling functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if not objIDs:
        return  # Nothing to scale

    # Validate parameters
    if len(scale) != 3:
        raise ValueError("Scale must have exactly 3 elements [x, y, z]")
    if len(point) != 3:
        raise ValueError("Point must have exactly 3 elements [x, y, z]")

    # Convert to ctypes arrays
    objIDs_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    scale_ptr = (ctypes.c_float * 3)(*scale)
    point_ptr = (ctypes.c_float * 3)(*point)

    # Call C function
    helios_lib.scaleObjectsAboutPoint(context, objIDs_array, len(objIDs), scale_ptr, point_ptr)

def scaleObjectAboutOrigin(context, objID: int, scale: List[float]) -> None:
    """Scale a single object about the global origin"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Scaling functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    # Validate parameters
    if len(scale) != 3:
        raise ValueError("Scale must have exactly 3 elements [x, y, z]")

    # Convert to ctypes array
    scale_ptr = (ctypes.c_float * 3)(*scale)

    # Call C function
    helios_lib.scaleObjectAboutOrigin(context, objID, scale_ptr)

def scaleObjectsAboutOrigin(context, objIDs: List[int], scale: List[float]) -> None:
    """Scale multiple objects about the global origin"""
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Scaling functions not available in current Helios library. "
            "Rebuild PyHelios with updated native interface."
        )

    if not objIDs:
        return  # Nothing to scale

    # Validate parameters
    if len(scale) != 3:
        raise ValueError("Scale must have exactly 3 elements [x, y, z]")

    # Convert to ctypes arrays
    objIDs_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    scale_ptr = (ctypes.c_float * 3)(*scale)

    # Call C function
    helios_lib.scaleObjectsAboutOrigin(context, objIDs_array, len(objIDs), scale_ptr)

def scaleConeObjectLength(context, objID: int, scale_factor: float) -> None:
    """Scale the length of a Cone object by scaling the distance between the two nodes

    Args:
        context: Helios Context pointer
        objID: Object ID of the Cone to scale
        scale_factor: Factor by which to scale the cone length

    Note:
        Added in helios-core v1.3.59 as replacement for removed getConeObjectPointer()
    """
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Cone scaling functions not available in current Helios library. "
            "Rebuild PyHelios with helios-core v1.3.59 or later."
        )

    helios_lib.scaleConeObjectLength(context, objID, scale_factor)

def scaleConeObjectGirth(context, objID: int, scale_factor: float) -> None:
    """Scale the girth of a Cone object by scaling the radii at both nodes

    Args:
        context: Helios Context pointer
        objID: Object ID of the Cone to scale
        scale_factor: Factor by which to scale the cone girth

    Note:
        Added in helios-core v1.3.59 as replacement for removed getConeObjectPointer()
    """
    if not _COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Cone scaling functions not available in current Helios library. "
            "Rebuild PyHelios with helios-core v1.3.59 or later."
        )

    helios_lib.scaleConeObjectGirth(context, objID, scale_factor)

# Python wrappers for primitive data functions - scalar setters
def setPrimitiveDataInt(context, uuid:int, label:str, value:int):
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    label_encoded = label.encode('utf-8')
    helios_lib.setPrimitiveDataInt(context, uuid, label_encoded, value)

def setPrimitiveDataFloat(context, uuid:int, label:str, value:float):
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    label_encoded = label.encode('utf-8')
    helios_lib.setPrimitiveDataFloat(context, uuid, label_encoded, value)

def setPrimitiveDataString(context, uuid:int, label:str, value:str):
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    # Explicitly clear error state to prevent contamination in macOS CI environment
    helios_lib.clearError()
    label_encoded = label.encode('utf-8')
    value_encoded = value.encode('utf-8')
    helios_lib.setPrimitiveDataString(context, uuid, label_encoded, value_encoded)

def setPrimitiveDataVec3(context, uuid:int, label:str, x:float, y:float, z:float):
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    label_encoded = label.encode('utf-8')
    helios_lib.setPrimitiveDataVec3(context, uuid, label_encoded, x, y, z)

# Python wrappers for primitive data functions - scalar getters  
def getPrimitiveDataInt(context, uuid:int, label:str) -> int:
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    label_encoded = label.encode('utf-8')
    return helios_lib.getPrimitiveDataInt(context, uuid, label_encoded)

def getPrimitiveDataFloat(context, uuid:int, label:str) -> float:
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    label_encoded = label.encode('utf-8')
    return helios_lib.getPrimitiveDataFloat(context, uuid, label_encoded)

def getPrimitiveDataString(context, uuid:int, label:str) -> str:
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    label_encoded = label.encode('utf-8')
    # Allocate buffer for string output
    buffer = ctypes.create_string_buffer(1024)
    length = helios_lib.getPrimitiveDataString(context, uuid, label_encoded, buffer, 1024)
    return buffer.value.decode('utf-8')

def getPrimitiveDataVec3(context, uuid:int, label:str) -> List[float]:
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    label_encoded = label.encode('utf-8')
    x = ctypes.c_float()
    y = ctypes.c_float()
    z = ctypes.c_float()
    helios_lib.getPrimitiveDataVec3(context, uuid, label_encoded, ctypes.byref(x), ctypes.byref(y), ctypes.byref(z))
    return [x.value, y.value, z.value]

# Python wrappers for primitive data utility functions
def doesPrimitiveDataExistWrapper(context, uuid:int, label:str) -> bool:
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    label_encoded = label.encode('utf-8')
    return helios_lib.doesPrimitiveDataExist(context, uuid, label_encoded)

def getPrimitiveDataTypeWrapper(context, uuid:int, label:str) -> int:
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    label_encoded = label.encode('utf-8')
    return helios_lib.getPrimitiveDataType(context, uuid, label_encoded)

def getPrimitiveDataSizeWrapper(context, uuid:int, label:str) -> int:
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    label_encoded = label.encode('utf-8')
    return helios_lib.getPrimitiveDataSize(context, uuid, label_encoded)

# Python wrappers for extended primitive data functions - scalar setters
def setPrimitiveDataUInt(context, uuid:int, label:str, value:int):
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    label_encoded = label.encode('utf-8')
    helios_lib.setPrimitiveDataUInt(context, uuid, label_encoded, value)

def setPrimitiveDataDouble(context, uuid:int, label:str, value:float):
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    label_encoded = label.encode('utf-8')
    helios_lib.setPrimitiveDataDouble(context, uuid, label_encoded, value)

def setPrimitiveDataVec2(context, uuid:int, label:str, x:float, y:float):
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    label_encoded = label.encode('utf-8')
    helios_lib.setPrimitiveDataVec2(context, uuid, label_encoded, x, y)

def setPrimitiveDataVec4(context, uuid:int, label:str, x:float, y:float, z:float, w:float):
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    label_encoded = label.encode('utf-8')
    helios_lib.setPrimitiveDataVec4(context, uuid, label_encoded, x, y, z, w)

def setPrimitiveDataInt2(context, uuid:int, label:str, x:int, y:int):
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    label_encoded = label.encode('utf-8')
    helios_lib.setPrimitiveDataInt2(context, uuid, label_encoded, x, y)

def setPrimitiveDataInt3(context, uuid:int, label:str, x:int, y:int, z:int):
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    label_encoded = label.encode('utf-8')
    helios_lib.setPrimitiveDataInt3(context, uuid, label_encoded, x, y, z)

def setPrimitiveDataInt4(context, uuid:int, label:str, x:int, y:int, z:int, w:int):
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    label_encoded = label.encode('utf-8')
    helios_lib.setPrimitiveDataInt4(context, uuid, label_encoded, x, y, z, w)

# Python wrappers for extended primitive data functions - scalar getters
def getPrimitiveDataUInt(context, uuid:int, label:str) -> int:
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    label_encoded = label.encode('utf-8')
    return helios_lib.getPrimitiveDataUInt(context, uuid, label_encoded)

def getPrimitiveDataDouble(context, uuid:int, label:str) -> float:
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    label_encoded = label.encode('utf-8')
    return helios_lib.getPrimitiveDataDouble(context, uuid, label_encoded)

def getPrimitiveDataVec2(context, uuid:int, label:str) -> List[float]:
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    label_encoded = label.encode('utf-8')
    x = ctypes.c_float()
    y = ctypes.c_float()
    helios_lib.getPrimitiveDataVec2(context, uuid, label_encoded, ctypes.byref(x), ctypes.byref(y))
    return [x.value, y.value]

def getPrimitiveDataVec4(context, uuid:int, label:str) -> List[float]:
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    label_encoded = label.encode('utf-8')
    x = ctypes.c_float()
    y = ctypes.c_float()
    z = ctypes.c_float()
    w = ctypes.c_float()
    helios_lib.getPrimitiveDataVec4(context, uuid, label_encoded, ctypes.byref(x), ctypes.byref(y), ctypes.byref(z), ctypes.byref(w))
    return [x.value, y.value, z.value, w.value]

def getPrimitiveDataInt2(context, uuid:int, label:str) -> List[int]:
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    label_encoded = label.encode('utf-8')
    x = ctypes.c_int()
    y = ctypes.c_int()
    helios_lib.getPrimitiveDataInt2(context, uuid, label_encoded, ctypes.byref(x), ctypes.byref(y))
    return [x.value, y.value]

def getPrimitiveDataInt3(context, uuid:int, label:str) -> List[int]:
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    label_encoded = label.encode('utf-8')
    x = ctypes.c_int()
    y = ctypes.c_int()
    z = ctypes.c_int()
    helios_lib.getPrimitiveDataInt3(context, uuid, label_encoded, ctypes.byref(x), ctypes.byref(y), ctypes.byref(z))
    return [x.value, y.value, z.value]

def getPrimitiveDataInt4(context, uuid:int, label:str) -> List[int]:
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    label_encoded = label.encode('utf-8')
    x = ctypes.c_int()
    y = ctypes.c_int()
    z = ctypes.c_int()
    w = ctypes.c_int()
    helios_lib.getPrimitiveDataInt4(context, uuid, label_encoded, ctypes.byref(x), ctypes.byref(y), ctypes.byref(z), ctypes.byref(w))
    return [x.value, y.value, z.value, w.value]

def getPrimitiveDataAuto(context, uuid:int, label:str):
    """
    Generic primitive data getter that automatically detects the type.
    
    Args:
        context: Context pointer
        uuid: UUID of the primitive
        label: String key for the data
        
    Returns:
        The stored value with appropriate Python type
    """
    if not _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Primitive data functions not available in current Helios library. These require updated C++ wrapper implementation.")
    
    # First, get the data type
    data_type = getPrimitiveDataTypeWrapper(context, uuid, label)
    
    # Map data types to appropriate getters
    # These constants match the Helios C++ HeliosDataType enum
    HELIOS_TYPE_INT = 0
    HELIOS_TYPE_UINT = 1  
    HELIOS_TYPE_FLOAT = 2
    HELIOS_TYPE_DOUBLE = 3
    HELIOS_TYPE_VEC2 = 4
    HELIOS_TYPE_VEC3 = 5
    HELIOS_TYPE_VEC4 = 6
    HELIOS_TYPE_INT2 = 7
    HELIOS_TYPE_INT3 = 8
    HELIOS_TYPE_INT4 = 9
    HELIOS_TYPE_STRING = 10
    
    if data_type == HELIOS_TYPE_INT:
        return getPrimitiveDataInt(context, uuid, label)
    elif data_type == HELIOS_TYPE_UINT:
        return getPrimitiveDataUInt(context, uuid, label)
    elif data_type == HELIOS_TYPE_FLOAT:
        return getPrimitiveDataFloat(context, uuid, label)
    elif data_type == HELIOS_TYPE_DOUBLE:
        return getPrimitiveDataDouble(context, uuid, label)
    elif data_type == HELIOS_TYPE_VEC2:
        return getPrimitiveDataVec2(context, uuid, label)
    elif data_type == HELIOS_TYPE_VEC3:
        return getPrimitiveDataVec3(context, uuid, label)
    elif data_type == HELIOS_TYPE_VEC4:
        return getPrimitiveDataVec4(context, uuid, label)
    elif data_type == HELIOS_TYPE_INT2:
        return getPrimitiveDataInt2(context, uuid, label)
    elif data_type == HELIOS_TYPE_INT3:
        return getPrimitiveDataInt3(context, uuid, label)
    elif data_type == HELIOS_TYPE_INT4:
        return getPrimitiveDataInt4(context, uuid, label)
    elif data_type == HELIOS_TYPE_STRING:
        return getPrimitiveDataString(context, uuid, label)
    else:
        raise ValueError(f"Unknown data type {data_type} for primitive {uuid}, label '{label}'")


# Python wrappers for broadcast primitive data functions - same value to all UUIDs
def setBroadcastPrimitiveDataInt(context, uuids: List[int], label: str, value: int):
    """Set integer primitive data for multiple primitives (broadcast same value to all)."""
    if not _BROADCAST_PRIMITIVE_DATA_AVAILABLE:
        raise NotImplementedError("Broadcast primitive data functions not available. Rebuild native library with updated version.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty")
    label_encoded = label.encode('utf-8')
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.setBroadcastPrimitiveDataInt(context, uuids_array, len(uuids), label_encoded, value)

def setBroadcastPrimitiveDataUInt(context, uuids: List[int], label: str, value: int):
    """Set unsigned integer primitive data for multiple primitives (broadcast same value to all)."""
    if not _BROADCAST_PRIMITIVE_DATA_AVAILABLE:
        raise NotImplementedError("Broadcast primitive data functions not available. Rebuild native library with updated version.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty")
    label_encoded = label.encode('utf-8')
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.setBroadcastPrimitiveDataUInt(context, uuids_array, len(uuids), label_encoded, value)

def setBroadcastPrimitiveDataFloat(context, uuids: List[int], label: str, value: float):
    """Set float primitive data for multiple primitives (broadcast same value to all)."""
    if not _BROADCAST_PRIMITIVE_DATA_AVAILABLE:
        raise NotImplementedError("Broadcast primitive data functions not available. Rebuild native library with updated version.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty")
    label_encoded = label.encode('utf-8')
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.setBroadcastPrimitiveDataFloat(context, uuids_array, len(uuids), label_encoded, value)

def setBroadcastPrimitiveDataDouble(context, uuids: List[int], label: str, value: float):
    """Set double primitive data for multiple primitives (broadcast same value to all)."""
    if not _BROADCAST_PRIMITIVE_DATA_AVAILABLE:
        raise NotImplementedError("Broadcast primitive data functions not available. Rebuild native library with updated version.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty")
    label_encoded = label.encode('utf-8')
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.setBroadcastPrimitiveDataDouble(context, uuids_array, len(uuids), label_encoded, value)

def setBroadcastPrimitiveDataString(context, uuids: List[int], label: str, value: str):
    """Set string primitive data for multiple primitives (broadcast same value to all)."""
    if not _BROADCAST_PRIMITIVE_DATA_AVAILABLE:
        raise NotImplementedError("Broadcast primitive data functions not available. Rebuild native library with updated version.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty")
    label_encoded = label.encode('utf-8')
    value_encoded = value.encode('utf-8')
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.setBroadcastPrimitiveDataString(context, uuids_array, len(uuids), label_encoded, value_encoded)

def setBroadcastPrimitiveDataVec2(context, uuids: List[int], label: str, x: float, y: float):
    """Set vec2 primitive data for multiple primitives (broadcast same value to all)."""
    if not _BROADCAST_PRIMITIVE_DATA_AVAILABLE:
        raise NotImplementedError("Broadcast primitive data functions not available. Rebuild native library with updated version.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty")
    label_encoded = label.encode('utf-8')
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.setBroadcastPrimitiveDataVec2(context, uuids_array, len(uuids), label_encoded, x, y)

def setBroadcastPrimitiveDataVec3(context, uuids: List[int], label: str, x: float, y: float, z: float):
    """Set vec3 primitive data for multiple primitives (broadcast same value to all)."""
    if not _BROADCAST_PRIMITIVE_DATA_AVAILABLE:
        raise NotImplementedError("Broadcast primitive data functions not available. Rebuild native library with updated version.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty")
    label_encoded = label.encode('utf-8')
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.setBroadcastPrimitiveDataVec3(context, uuids_array, len(uuids), label_encoded, x, y, z)

def setBroadcastPrimitiveDataVec4(context, uuids: List[int], label: str, x: float, y: float, z: float, w: float):
    """Set vec4 primitive data for multiple primitives (broadcast same value to all)."""
    if not _BROADCAST_PRIMITIVE_DATA_AVAILABLE:
        raise NotImplementedError("Broadcast primitive data functions not available. Rebuild native library with updated version.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty")
    label_encoded = label.encode('utf-8')
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.setBroadcastPrimitiveDataVec4(context, uuids_array, len(uuids), label_encoded, x, y, z, w)

def setBroadcastPrimitiveDataInt2(context, uuids: List[int], label: str, x: int, y: int):
    """Set int2 primitive data for multiple primitives (broadcast same value to all)."""
    if not _BROADCAST_PRIMITIVE_DATA_AVAILABLE:
        raise NotImplementedError("Broadcast primitive data functions not available. Rebuild native library with updated version.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty")
    label_encoded = label.encode('utf-8')
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.setBroadcastPrimitiveDataInt2(context, uuids_array, len(uuids), label_encoded, x, y)

def setBroadcastPrimitiveDataInt3(context, uuids: List[int], label: str, x: int, y: int, z: int):
    """Set int3 primitive data for multiple primitives (broadcast same value to all)."""
    if not _BROADCAST_PRIMITIVE_DATA_AVAILABLE:
        raise NotImplementedError("Broadcast primitive data functions not available. Rebuild native library with updated version.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty")
    label_encoded = label.encode('utf-8')
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.setBroadcastPrimitiveDataInt3(context, uuids_array, len(uuids), label_encoded, x, y, z)

def setBroadcastPrimitiveDataInt4(context, uuids: List[int], label: str, x: int, y: int, z: int, w: int):
    """Set int4 primitive data for multiple primitives (broadcast same value to all)."""
    if not _BROADCAST_PRIMITIVE_DATA_AVAILABLE:
        raise NotImplementedError("Broadcast primitive data functions not available. Rebuild native library with updated version.")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty")
    label_encoded = label.encode('utf-8')
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.setBroadcastPrimitiveDataInt4(context, uuids_array, len(uuids), label_encoded, x, y, z, w)


# Try to set up pseudocolor function prototypes
try:
    # colorPrimitiveByDataPseudocolor function prototypes
    helios_lib.colorPrimitiveByDataPseudocolor.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_size_t, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
    helios_lib.colorPrimitiveByDataPseudocolor.restype = None
    
    helios_lib.colorPrimitiveByDataPseudocolorWithRange.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_size_t, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint, ctypes.c_float, ctypes.c_float]
    helios_lib.colorPrimitiveByDataPseudocolorWithRange.restype = None
    
    # Mark that pseudocolor functions are available
    _PSEUDOCOLOR_FUNCTIONS_AVAILABLE = True

except AttributeError:
    # Pseudocolor functions not available in current native library
    _PSEUDOCOLOR_FUNCTIONS_AVAILABLE = False


def colorPrimitiveByDataPseudocolor(context, uuids: List[int], primitive_data: str, colormap: str, ncolors: int):
    """Color primitives using pseudocolor mapping based on primitive data"""
    if not _PSEUDOCOLOR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Pseudocolor functions not available in current Helios library. These require updated C++ wrapper implementation.")
    
    primitive_data_encoded = primitive_data.encode('utf-8')
    colormap_encoded = colormap.encode('utf-8')
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.colorPrimitiveByDataPseudocolor(context, uuid_array, len(uuids), primitive_data_encoded, colormap_encoded, ncolors)


def colorPrimitiveByDataPseudocolorWithRange(context, uuids: List[int], primitive_data: str, colormap: str, ncolors: int, max_val: float, min_val: float):
    """Color primitives using pseudocolor mapping based on primitive data with specified value range"""
    if not _PSEUDOCOLOR_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Pseudocolor functions not available in current Helios library. These require updated C++ wrapper implementation.")
    
    primitive_data_encoded = primitive_data.encode('utf-8')
    colormap_encoded = colormap.encode('utf-8')
    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.colorPrimitiveByDataPseudocolorWithRange(context, uuid_array, len(uuids), primitive_data_encoded, colormap_encoded, ncolors, max_val, min_val)


# Try to set up Context time/date function prototypes
try:
    # Context time/date functions
    helios_lib.setTime_HourMinute.argtypes = [ctypes.POINTER(UContext), ctypes.c_int, ctypes.c_int]
    helios_lib.setTime_HourMinute.restype = None
    
    helios_lib.setTime_HourMinuteSecond.argtypes = [ctypes.POINTER(UContext), ctypes.c_int, ctypes.c_int, ctypes.c_int]
    helios_lib.setTime_HourMinuteSecond.restype = None
    
    helios_lib.setDate_DayMonthYear.argtypes = [ctypes.POINTER(UContext), ctypes.c_int, ctypes.c_int, ctypes.c_int]
    helios_lib.setDate_DayMonthYear.restype = None
    
    helios_lib.setDate_JulianDay.argtypes = [ctypes.POINTER(UContext), ctypes.c_int, ctypes.c_int]
    helios_lib.setDate_JulianDay.restype = None
    
    helios_lib.getTime.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    helios_lib.getTime.restype = None
    
    helios_lib.getDate.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    helios_lib.getDate.restype = None
    
    # Mark that time/date functions are available
    _TIME_DATE_FUNCTIONS_AVAILABLE = True

except AttributeError:
    # Time/date functions not available in current native library
    _TIME_DATE_FUNCTIONS_AVAILABLE = False

# Error checking callback for time/date functions
def _check_error_time_date(result, func, args):
    """Automatic error checking for time/date functions"""
    check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage)
    return result

# Set up automatic error checking for time/date functions
if _TIME_DATE_FUNCTIONS_AVAILABLE:
    helios_lib.setTime_HourMinute.errcheck = _check_error_time_date
    helios_lib.setTime_HourMinuteSecond.errcheck = _check_error_time_date
    helios_lib.setDate_DayMonthYear.errcheck = _check_error_time_date
    helios_lib.setDate_JulianDay.errcheck = _check_error_time_date
    helios_lib.getTime.errcheck = _check_error_time_date
    helios_lib.getDate.errcheck = _check_error_time_date

# Context time/date wrapper functions
def setTime(context, hour: int, minute: int = 0, second: int = 0):
    """Set the simulation time"""
    if not _TIME_DATE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Context time/date functions not available in current Helios library. Rebuild PyHelios with updated C++ wrapper implementation.")
    
    if second == 0:
        helios_lib.setTime_HourMinute(context, hour, minute)
    else:
        helios_lib.setTime_HourMinuteSecond(context, hour, minute, second)

def setDate(context, year: int, month: int, day: int):
    """Set the simulation date"""
    if not _TIME_DATE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Context time/date functions not available in current Helios library. Rebuild PyHelios with updated C++ wrapper implementation.")
    
    helios_lib.setDate_DayMonthYear(context, day, month, year)

def setDateJulian(context, julian_day: int, year: int):
    """Set the simulation date using Julian day"""
    if not _TIME_DATE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Context time/date functions not available in current Helios library. Rebuild PyHelios with updated C++ wrapper implementation.")
    
    helios_lib.setDate_JulianDay(context, julian_day, year)

def getTime(context):
    """Get the current simulation time as a tuple (hour, minute, second)"""
    if not _TIME_DATE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Context time/date functions not available in current Helios library. Rebuild PyHelios with updated C++ wrapper implementation.")
    
    hour = ctypes.c_int()
    minute = ctypes.c_int()
    second = ctypes.c_int()
    
    helios_lib.getTime(context, ctypes.byref(hour), ctypes.byref(minute), ctypes.byref(second))
    
    return (hour.value, minute.value, second.value)

def getDate(context):
    """Get the current simulation date as a tuple (year, month, day)"""
    if not _TIME_DATE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Context time/date functions not available in current Helios library. Rebuild PyHelios with updated C++ wrapper implementation.")
    
    day = ctypes.c_int()
    month = ctypes.c_int()
    year = ctypes.c_int()
    
    helios_lib.getDate(context, ctypes.byref(day), ctypes.byref(month), ctypes.byref(year))
    
    return (year.value, month.value, day.value)


# ============================================================================
# Primitive and Object Deletion Functions
# ============================================================================

_DELETE_FUNCTIONS_AVAILABLE = False

try:
    # Single primitive deletion
    helios_lib.deletePrimitive.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.deletePrimitive.restype = None

    # Multiple primitive deletion
    helios_lib.deletePrimitives.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint]
    helios_lib.deletePrimitives.restype = None

    # Single object deletion
    helios_lib.deleteObject.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.deleteObject.restype = None

    # Multiple object deletion
    helios_lib.deleteObjects.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint]
    helios_lib.deleteObjects.restype = None

    # Mark that delete functions are available
    _DELETE_FUNCTIONS_AVAILABLE = True

except AttributeError:
    # Delete functions not available in current native library
    _DELETE_FUNCTIONS_AVAILABLE = False

# Set up automatic error checking for delete functions
if _DELETE_FUNCTIONS_AVAILABLE:
    helios_lib.deletePrimitive.errcheck = _check_error
    helios_lib.deletePrimitives.errcheck = _check_error
    helios_lib.deleteObject.errcheck = _check_error
    helios_lib.deleteObjects.errcheck = _check_error

# ============================================================================
# Materials System Functions (v1.3.58+)
# ============================================================================

_MATERIALS_FUNCTIONS_AVAILABLE = False

try:
    helios_lib.addMaterial.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    helios_lib.addMaterial.restype = None

    helios_lib.doesMaterialExist.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    helios_lib.doesMaterialExist.restype = ctypes.c_bool

    helios_lib.listMaterials.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t)]
    helios_lib.listMaterials.restype = ctypes.POINTER(ctypes.c_char_p)

    helios_lib.deleteMaterial.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    helios_lib.deleteMaterial.restype = None

    helios_lib.getMaterialColor.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_float)]
    helios_lib.getMaterialColor.restype = None

    helios_lib.setMaterialColor.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.setMaterialColor.restype = None

    helios_lib.getMaterialTexture.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    helios_lib.getMaterialTexture.restype = ctypes.c_char_p

    helios_lib.setMaterialTexture.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.setMaterialTexture.restype = None

    helios_lib.isMaterialTextureColorOverridden.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    helios_lib.isMaterialTextureColorOverridden.restype = ctypes.c_bool

    helios_lib.setMaterialTextureColorOverride.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_bool]
    helios_lib.setMaterialTextureColorOverride.restype = None

    helios_lib.getMaterialTwosidedFlag.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    helios_lib.getMaterialTwosidedFlag.restype = ctypes.c_uint

    helios_lib.setMaterialTwosidedFlag.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint]
    helios_lib.setMaterialTwosidedFlag.restype = None

    helios_lib.assignMaterialToPrimitive.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_char_p]
    helios_lib.assignMaterialToPrimitive.restype = None

    helios_lib.assignMaterialToPrimitives.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint), ctypes.c_size_t, ctypes.c_char_p]
    helios_lib.assignMaterialToPrimitives.restype = None

    helios_lib.assignMaterialToObject.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_char_p]
    helios_lib.assignMaterialToObject.restype = None

    helios_lib.assignMaterialToObjects.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint), ctypes.c_size_t, ctypes.c_char_p]
    helios_lib.assignMaterialToObjects.restype = None

    helios_lib.getPrimitiveMaterialLabel.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    helios_lib.getPrimitiveMaterialLabel.restype = ctypes.c_char_p

    helios_lib.getPrimitiveTwosidedFlag.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint]
    helios_lib.getPrimitiveTwosidedFlag.restype = ctypes.c_uint

    helios_lib.getPrimitivesUsingMaterial.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_size_t)]
    helios_lib.getPrimitivesUsingMaterial.restype = ctypes.POINTER(ctypes.c_uint)

    # Set up automatic error checking for materials functions
    helios_lib.addMaterial.errcheck = _check_error
    helios_lib.doesMaterialExist.errcheck = _check_error
    helios_lib.listMaterials.errcheck = _check_error
    helios_lib.deleteMaterial.errcheck = _check_error
    helios_lib.getMaterialColor.errcheck = _check_error
    helios_lib.setMaterialColor.errcheck = _check_error
    helios_lib.getMaterialTexture.errcheck = _check_error
    helios_lib.setMaterialTexture.errcheck = _check_error
    helios_lib.isMaterialTextureColorOverridden.errcheck = _check_error
    helios_lib.setMaterialTextureColorOverride.errcheck = _check_error
    helios_lib.getMaterialTwosidedFlag.errcheck = _check_error
    helios_lib.setMaterialTwosidedFlag.errcheck = _check_error
    helios_lib.assignMaterialToPrimitive.errcheck = _check_error
    helios_lib.assignMaterialToPrimitives.errcheck = _check_error
    helios_lib.assignMaterialToObject.errcheck = _check_error
    helios_lib.assignMaterialToObjects.errcheck = _check_error
    helios_lib.getPrimitiveMaterialLabel.errcheck = _check_error
    helios_lib.getPrimitiveTwosidedFlag.errcheck = _check_error
    helios_lib.getPrimitivesUsingMaterial.errcheck = _check_error

    _MATERIALS_FUNCTIONS_AVAILABLE = True

except AttributeError:
    _MATERIALS_FUNCTIONS_AVAILABLE = False

# Primitive deletion wrapper functions
def deletePrimitive(context, uuid: int) -> None:
    """Delete a single primitive by UUID.

    Args:
        context: The Helios context pointer
        uuid: UUID of the primitive to delete

    Raises:
        RuntimeError: If primitive UUID doesn't exist in context
    """
    if not _DELETE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "deletePrimitive function not available in current Helios library. "
            "Rebuild PyHelios with updated C++ wrapper implementation."
        )
    helios_lib.deletePrimitive(context, ctypes.c_uint(uuid))

def deletePrimitives(context, uuids: List[int]) -> None:
    """Delete multiple primitives by UUID.

    Args:
        context: The Helios context pointer
        uuids: List of UUIDs of primitives to delete

    Raises:
        RuntimeError: If any primitive UUID doesn't exist in context
    """
    if not _DELETE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "deletePrimitives function not available in current Helios library. "
            "Rebuild PyHelios with updated C++ wrapper implementation."
        )
    if not uuids:
        return  # No-op for empty list
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.deletePrimitives(context, uuids_array, len(uuids))

# Object deletion wrapper functions
def deleteObject(context, objID: int) -> None:
    """Delete a single compound object and all its child primitives.

    Args:
        context: The Helios context pointer
        objID: Object ID to delete

    Raises:
        RuntimeError: If object ID doesn't exist in context
    """
    if not _DELETE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "deleteObject function not available in current Helios library. "
            "Rebuild PyHelios with updated C++ wrapper implementation."
        )
    helios_lib.deleteObject(context, ctypes.c_uint(objID))

def deleteObjects(context, objIDs: List[int]) -> None:
    """Delete multiple compound objects and all their child primitives.

    Args:
        context: The Helios context pointer
        objIDs: List of object IDs to delete

    Raises:
        RuntimeError: If any object ID doesn't exist in context
    """
    if not _DELETE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "deleteObjects function not available in current Helios library. "
            "Rebuild PyHelios with updated C++ wrapper implementation."
        )
    if not objIDs:
        return  # No-op for empty list
    objIDs_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    helios_lib.deleteObjects(context, objIDs_array, len(objIDs))

# ============================================================================
# Materials System Wrapper Functions (v1.3.58+)
# ============================================================================

def addMaterial(context, material_label: str) -> None:
    """Create a new material with the given label."""
    if not _MATERIALS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Materials functions not available. Rebuild with updated C++ wrapper.")
    material_label_encoded = material_label.encode('utf-8')
    helios_lib.addMaterial(context, material_label_encoded)

def doesMaterialExist(context, material_label: str) -> bool:
    """Check if a material exists."""
    if not _MATERIALS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Materials functions not available. Rebuild with updated C++ wrapper.")
    material_label_encoded = material_label.encode('utf-8')
    return helios_lib.doesMaterialExist(context, material_label_encoded)

def listMaterials(context) -> List[str]:
    """Get list of all material labels."""
    if not _MATERIALS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Materials functions not available. Rebuild with updated C++ wrapper.")
    count = ctypes.c_size_t()
    materials_ptr = helios_lib.listMaterials(context, ctypes.byref(count))
    if count.value == 0 or not materials_ptr:
        return []
    return [materials_ptr[i].decode('utf-8') for i in range(count.value)]

def deleteMaterial(context, material_label: str) -> None:
    """Delete a material."""
    if not _MATERIALS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Materials functions not available. Rebuild with updated C++ wrapper.")
    material_label_encoded = material_label.encode('utf-8')
    helios_lib.deleteMaterial(context, material_label_encoded)

def getMaterialColor(context, material_label: str) -> List[float]:
    """Get RGBA color of a material."""
    if not _MATERIALS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Materials functions not available. Rebuild with updated C++ wrapper.")
    material_label_encoded = material_label.encode('utf-8')
    color_array = (ctypes.c_float * 4)()
    helios_lib.getMaterialColor(context, material_label_encoded, color_array)
    return list(color_array)

def setMaterialColor(context, material_label: str, r: float, g: float, b: float, a: float = 1.0) -> None:
    """Set RGBA color of a material."""
    if not _MATERIALS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Materials functions not available. Rebuild with updated C++ wrapper.")
    material_label_encoded = material_label.encode('utf-8')
    helios_lib.setMaterialColor(context, material_label_encoded, r, g, b, a)

def getMaterialTexture(context, material_label: str) -> str:
    """Get texture file path for a material."""
    if not _MATERIALS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Materials functions not available. Rebuild with updated C++ wrapper.")
    material_label_encoded = material_label.encode('utf-8')
    texture_ptr = helios_lib.getMaterialTexture(context, material_label_encoded)
    return texture_ptr.decode('utf-8') if texture_ptr else ""

def setMaterialTexture(context, material_label: str, texture_file: str) -> None:
    """Set texture file for a material."""
    if not _MATERIALS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Materials functions not available. Rebuild with updated C++ wrapper.")
    material_label_encoded = material_label.encode('utf-8')
    texture_file_encoded = texture_file.encode('utf-8')
    helios_lib.setMaterialTexture(context, material_label_encoded, texture_file_encoded)

def isMaterialTextureColorOverridden(context, material_label: str) -> bool:
    """Check if material texture color is overridden."""
    if not _MATERIALS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Materials functions not available. Rebuild with updated C++ wrapper.")
    material_label_encoded = material_label.encode('utf-8')
    return helios_lib.isMaterialTextureColorOverridden(context, material_label_encoded)

def setMaterialTextureColorOverride(context, material_label: str, override: bool) -> None:
    """Set texture color override for a material."""
    if not _MATERIALS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Materials functions not available. Rebuild with updated C++ wrapper.")
    material_label_encoded = material_label.encode('utf-8')
    helios_lib.setMaterialTextureColorOverride(context, material_label_encoded, override)

def getMaterialTwosidedFlag(context, material_label: str) -> int:
    """Get two-sided rendering flag for a material."""
    if not _MATERIALS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Materials functions not available. Rebuild with updated C++ wrapper.")
    material_label_encoded = material_label.encode('utf-8')
    return helios_lib.getMaterialTwosidedFlag(context, material_label_encoded)

def setMaterialTwosidedFlag(context, material_label: str, twosided_flag: int) -> None:
    """Set two-sided rendering flag for a material."""
    if not _MATERIALS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Materials functions not available. Rebuild with updated C++ wrapper.")
    material_label_encoded = material_label.encode('utf-8')
    helios_lib.setMaterialTwosidedFlag(context, material_label_encoded, twosided_flag)

def assignMaterialToPrimitive(context, uuid: int, material_label: str) -> None:
    """Assign a material to a single primitive."""
    if not _MATERIALS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Materials functions not available. Rebuild with updated C++ wrapper.")
    material_label_encoded = material_label.encode('utf-8')
    helios_lib.assignMaterialToPrimitive(context, ctypes.c_uint(uuid), material_label_encoded)

def assignMaterialToPrimitives(context, uuids: List[int], material_label: str) -> None:
    """Assign a material to multiple primitives."""
    if not _MATERIALS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Materials functions not available. Rebuild with updated C++ wrapper.")
    if not uuids:
        return
    material_label_encoded = material_label.encode('utf-8')
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.assignMaterialToPrimitives(context, uuids_array, len(uuids), material_label_encoded)

def assignMaterialToObject(context, objID: int, material_label: str) -> None:
    """Assign a material to all primitives in an object."""
    if not _MATERIALS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Materials functions not available. Rebuild with updated C++ wrapper.")
    material_label_encoded = material_label.encode('utf-8')
    helios_lib.assignMaterialToObject(context, ctypes.c_uint(objID), material_label_encoded)

def assignMaterialToObjects(context, objIDs: List[int], material_label: str) -> None:
    """Assign a material to all primitives in multiple objects."""
    if not _MATERIALS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Materials functions not available. Rebuild with updated C++ wrapper.")
    if not objIDs:
        return
    material_label_encoded = material_label.encode('utf-8')
    objIDs_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    helios_lib.assignMaterialToObjects(context, objIDs_array, len(objIDs), material_label_encoded)

def getPrimitiveMaterialLabel(context, uuid: int) -> str:
    """Get the material label assigned to a primitive."""
    if not _MATERIALS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Materials functions not available. Rebuild with updated C++ wrapper.")
    material_ptr = helios_lib.getPrimitiveMaterialLabel(context, ctypes.c_uint(uuid))
    return material_ptr.decode('utf-8') if material_ptr else ""

def getPrimitiveTwosidedFlag(context, uuid: int, default_value: int = 1) -> int:
    """Get two-sided flag for a primitive (checks material first, then primitive data)."""
    if not _MATERIALS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Materials functions not available. Rebuild with updated C++ wrapper.")
    return helios_lib.getPrimitiveTwosidedFlag(context, ctypes.c_uint(uuid), ctypes.c_uint(default_value))

def getPrimitivesUsingMaterial(context, material_label: str) -> List[int]:
    """Get all primitive UUIDs that use a specific material."""
    if not _MATERIALS_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Materials functions not available. Rebuild with updated C++ wrapper.")
    material_label_encoded = material_label.encode('utf-8')
    count = ctypes.c_size_t()
    uuids_ptr = helios_lib.getPrimitivesUsingMaterial(context, material_label_encoded, ctypes.byref(count))
    if count.value == 0 or not uuids_ptr:
        return []
    return list(uuids_ptr[:count.value])

