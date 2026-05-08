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

helios_lib.seedRandomGenerator.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
helios_lib.seedRandomGenerator.restype = None

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

# Textured patch function prototypes (may not be available in older builds)
_AVAILABLE_PATCH_TEXTURE_FUNCTIONS = []
try:
    helios_lib.addPatchWithTexture.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_char_p]
    helios_lib.addPatchWithTexture.restype = ctypes.c_uint
    helios_lib.addPatchWithTexture.errcheck = _check_error
    _AVAILABLE_PATCH_TEXTURE_FUNCTIONS.append('addPatchWithTexture')
except AttributeError:
    pass

try:
    helios_lib.addPatchWithTextureAndUV.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_char_p, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.addPatchWithTextureAndUV.restype = ctypes.c_uint
    helios_lib.addPatchWithTextureAndUV.errcheck = _check_error
    _AVAILABLE_PATCH_TEXTURE_FUNCTIONS.append('addPatchWithTextureAndUV')
except AttributeError:
    pass

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

helios_lib.doesPrimitiveExist.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
helios_lib.doesPrimitiveExist.restype = ctypes.c_bool

helios_lib.doesPrimitiveExistBatch.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint]
helios_lib.doesPrimitiveExistBatch.restype = ctypes.c_bool

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

def addPatchWithTexture(context, center:List[float], size:List[float], rotation:List[float], texture_file:str):
    if 'addPatchWithTexture' not in _AVAILABLE_PATCH_TEXTURE_FUNCTIONS:
        raise NotImplementedError(
            "addPatchWithTexture function not available in current Helios library. "
            "Rebuild PyHelios with updated C++ wrapper: build_scripts/build_helios"
        )
    center_ptr = (ctypes.c_float * len(center))(*center)
    size_ptr = (ctypes.c_float * len(size))(*size)
    rotation_ptr = (ctypes.c_float * len(rotation))(*rotation)
    texture_file_encoded = texture_file.encode('utf-8')
    return helios_lib.addPatchWithTexture(context, center_ptr, size_ptr, rotation_ptr, texture_file_encoded)

def addPatchWithTextureAndUV(context, center:List[float], size:List[float], rotation:List[float], texture_file:str, uv_center:List[float], uv_size:List[float]):
    if 'addPatchWithTextureAndUV' not in _AVAILABLE_PATCH_TEXTURE_FUNCTIONS:
        raise NotImplementedError(
            "addPatchWithTextureAndUV function not available in current Helios library. "
            "Rebuild PyHelios with updated C++ wrapper: build_scripts/build_helios"
        )
    center_ptr = (ctypes.c_float * len(center))(*center)
    size_ptr = (ctypes.c_float * len(size))(*size)
    rotation_ptr = (ctypes.c_float * len(rotation))(*rotation)
    texture_file_encoded = texture_file.encode('utf-8')
    uv_center_ptr = (ctypes.c_float * len(uv_center))(*uv_center)
    uv_size_ptr = (ctypes.c_float * len(uv_size))(*uv_size)
    return helios_lib.addPatchWithTextureAndUV(context, center_ptr, size_ptr, rotation_ptr, texture_file_encoded, uv_center_ptr, uv_size_ptr)

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

def doesPrimitiveExist(context, uuid):
    return helios_lib.doesPrimitiveExist(context, uuid)

def doesPrimitiveExistBatch(context, uuids, count):
    return helios_lib.doesPrimitiveExistBatch(context, uuids, count)

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
# Timeseries Functions
# ============================================================================

_TIMESERIES_FUNCTIONS_AVAILABLE = False

try:
    helios_lib.addTimeseriesData.argtypes = [
        ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_float,
        ctypes.c_int, ctypes.c_int, ctypes.c_int,
        ctypes.c_int, ctypes.c_int, ctypes.c_int
    ]
    helios_lib.addTimeseriesData.restype = None

    helios_lib.setCurrentTimeseriesPoint.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_uint]
    helios_lib.setCurrentTimeseriesPoint.restype = None

    helios_lib.queryTimeseriesData_DateTime.argtypes = [
        ctypes.POINTER(UContext), ctypes.c_char_p,
        ctypes.c_int, ctypes.c_int, ctypes.c_int,
        ctypes.c_int, ctypes.c_int, ctypes.c_int
    ]
    helios_lib.queryTimeseriesData_DateTime.restype = ctypes.c_float

    helios_lib.queryTimeseriesData_Current.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p]
    helios_lib.queryTimeseriesData_Current.restype = ctypes.c_float

    helios_lib.queryTimeseriesData_Index.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_uint]
    helios_lib.queryTimeseriesData_Index.restype = ctypes.c_float

    helios_lib.queryTimeseriesTime.argtypes = [
        ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_uint,
        ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)
    ]
    helios_lib.queryTimeseriesTime.restype = None

    helios_lib.queryTimeseriesDate.argtypes = [
        ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_uint,
        ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)
    ]
    helios_lib.queryTimeseriesDate.restype = None

    helios_lib.getTimeseriesLength.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p]
    helios_lib.getTimeseriesLength.restype = ctypes.c_uint

    helios_lib.doesTimeseriesVariableExist.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p]
    helios_lib.doesTimeseriesVariableExist.restype = ctypes.c_bool

    helios_lib.listTimeseriesVariables.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.listTimeseriesVariables.restype = ctypes.POINTER(ctypes.c_char_p)

    helios_lib.loadTabularTimeseriesData.argtypes = [
        ctypes.POINTER(UContext), ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_char_p), ctypes.c_uint,
        ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint
    ]
    helios_lib.loadTabularTimeseriesData.restype = None

    helios_lib.clearTimeseriesData.argtypes = [ctypes.POINTER(UContext)]
    helios_lib.clearTimeseriesData.restype = None

    _TIMESERIES_FUNCTIONS_AVAILABLE = True

except AttributeError:
    _TIMESERIES_FUNCTIONS_AVAILABLE = False

def _check_error_timeseries(result, func, args):
    """Automatic error checking for timeseries functions"""
    check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage)
    return result

if _TIMESERIES_FUNCTIONS_AVAILABLE:
    for fname in ['addTimeseriesData', 'setCurrentTimeseriesPoint',
                  'queryTimeseriesData_DateTime', 'queryTimeseriesData_Current',
                  'queryTimeseriesData_Index', 'queryTimeseriesTime',
                  'queryTimeseriesDate', 'getTimeseriesLength',
                  'doesTimeseriesVariableExist', 'listTimeseriesVariables',
                  'loadTabularTimeseriesData', 'clearTimeseriesData']:
        getattr(helios_lib, fname).errcheck = _check_error_timeseries

# deleteTimeseriesVariable was added in helios-core v1.3.72. Probe separately so wheels
# built against older libraries keep the rest of the timeseries API working.
_TIMESERIES_DELETE_AVAILABLE = False
try:
    helios_lib.deleteTimeseriesVariable.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p]
    helios_lib.deleteTimeseriesVariable.restype = None
    helios_lib.deleteTimeseriesVariable.errcheck = _check_error_timeseries
    _TIMESERIES_DELETE_AVAILABLE = True
except AttributeError:
    _TIMESERIES_DELETE_AVAILABLE = False

# updateTimeseriesData was added in helios-core v1.3.71. Probe separately so that
# wheels built against older libraries keep the rest of the timeseries API working.
_TIMESERIES_UPDATE_AVAILABLE = False
try:
    helios_lib.updateTimeseriesData.argtypes = [
        ctypes.POINTER(UContext), ctypes.c_char_p,
        ctypes.c_int, ctypes.c_int, ctypes.c_int,
        ctypes.c_int, ctypes.c_int, ctypes.c_int,
        ctypes.c_float
    ]
    helios_lib.updateTimeseriesData.restype = None
    _TIMESERIES_UPDATE_AVAILABLE = True
except AttributeError:
    _TIMESERIES_UPDATE_AVAILABLE = False

if _TIMESERIES_UPDATE_AVAILABLE:
    helios_lib.updateTimeseriesData.errcheck = _check_error_timeseries


_NOT_AVAILABLE_MSG = ("Timeseries functions not available in current Helios library. "
                      "Rebuild PyHelios with updated C++ wrapper implementation.")


def addTimeseriesData(context, label: str, value: float, day: int, month: int, year: int,
                      hour: int, minute: int, second: int):
    """Add a data point to a timeseries variable"""
    if not _TIMESERIES_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_MSG)
    helios_lib.addTimeseriesData(context, label.encode('utf-8'), value,
                                 day, month, year, hour, minute, second)


def updateTimeseriesData(context, label: str, day: int, month: int, year: int,
                         hour: int, minute: int, second: int, new_value: float):
    """Update the value of an existing timeseries data point at the given (date, time).

    Note: parameter order intentionally differs from addTimeseriesData() — value
    follows date/time here to match the underlying C++ signature
    `updateTimeseriesData(label, Date, Time, new_value)`.
    """
    if not _TIMESERIES_UPDATE_AVAILABLE:
        raise NotImplementedError(
            "updateTimeseriesData is not available in the current Helios library. "
            "It requires helios-core v1.3.71 or later. Rebuild PyHelios."
        )
    helios_lib.updateTimeseriesData(context, label.encode('utf-8'),
                                    day, month, year, hour, minute, second, new_value)


def setCurrentTimeseriesPoint(context, label: str, index: int):
    """Set the Context date and time from a timeseries data point index"""
    if not _TIMESERIES_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_MSG)
    helios_lib.setCurrentTimeseriesPoint(context, label.encode('utf-8'), index)


def queryTimeseriesDataDateTime(context, label: str, day: int, month: int, year: int,
                                hour: int, minute: int, second: int) -> float:
    """Query a timeseries value at a specific date and time (with interpolation)"""
    if not _TIMESERIES_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_MSG)
    return helios_lib.queryTimeseriesData_DateTime(context, label.encode('utf-8'),
                                                    day, month, year, hour, minute, second)


def queryTimeseriesDataCurrent(context, label: str) -> float:
    """Query a timeseries value at the current Context date/time"""
    if not _TIMESERIES_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_MSG)
    return helios_lib.queryTimeseriesData_Current(context, label.encode('utf-8'))


def queryTimeseriesDataIndex(context, label: str, index: int) -> float:
    """Query a timeseries value by index"""
    if not _TIMESERIES_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_MSG)
    return helios_lib.queryTimeseriesData_Index(context, label.encode('utf-8'), index)


def queryTimeseriesTime(context, label: str, index: int):
    """Get the Time at a timeseries data point. Returns (hour, minute, second)."""
    if not _TIMESERIES_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_MSG)

    hour = ctypes.c_int()
    minute = ctypes.c_int()
    second = ctypes.c_int()
    helios_lib.queryTimeseriesTime(context, label.encode('utf-8'), index,
                                    ctypes.byref(hour), ctypes.byref(minute), ctypes.byref(second))
    return (hour.value, minute.value, second.value)


def queryTimeseriesDate(context, label: str, index: int):
    """Get the Date at a timeseries data point. Returns (year, month, day)."""
    if not _TIMESERIES_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_MSG)

    day = ctypes.c_int()
    month = ctypes.c_int()
    year = ctypes.c_int()
    helios_lib.queryTimeseriesDate(context, label.encode('utf-8'), index,
                                    ctypes.byref(day), ctypes.byref(month), ctypes.byref(year))
    return (year.value, month.value, day.value)


def getTimeseriesLength(context, label: str) -> int:
    """Get the number of data points in a timeseries variable"""
    if not _TIMESERIES_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_MSG)
    return helios_lib.getTimeseriesLength(context, label.encode('utf-8'))


def doesTimeseriesVariableExist(context, label: str) -> bool:
    """Check whether a timeseries variable exists"""
    if not _TIMESERIES_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_MSG)
    return helios_lib.doesTimeseriesVariableExist(context, label.encode('utf-8'))


def listTimeseriesVariables(context):
    """List all existing timeseries variables. Returns List[str]."""
    if not _TIMESERIES_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_MSG)

    count = ctypes.c_uint()
    result_ptr = helios_lib.listTimeseriesVariables(context, ctypes.byref(count))

    if count.value == 0 or not result_ptr:
        return []

    return [result_ptr[i].decode('utf-8') for i in range(count.value)]


def loadTabularTimeseriesData(context, data_file: str, column_labels, delimiter: str,
                              date_string_format: str, headerlines: int):
    """Load tabular timeseries data from a text file"""
    if not _TIMESERIES_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_MSG)

    encoded_labels = [label.encode('utf-8') for label in column_labels]
    labels_array = (ctypes.c_char_p * len(encoded_labels))(*encoded_labels)

    helios_lib.loadTabularTimeseriesData(
        context, data_file.encode('utf-8'),
        labels_array, len(encoded_labels),
        delimiter.encode('utf-8'), date_string_format.encode('utf-8'),
        headerlines
    )


def clearTimeseriesData(context):
    """Clear all timeseries data from the Context"""
    if not _TIMESERIES_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_MSG)
    helios_lib.clearTimeseriesData(context)


def deleteTimeseriesVariable(context, label: str):
    """Delete a single timeseries variable and all of its data points.

    Requires helios-core v1.3.72 or newer.
    """
    if not _TIMESERIES_DELETE_AVAILABLE:
        raise NotImplementedError(
            "deleteTimeseriesVariable requires helios-core v1.3.72 or newer. "
            "Please rebuild PyHelios with `build_scripts/build_helios --clean`."
        )
    helios_lib.deleteTimeseriesVariable(context, label.encode('utf-8'))


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


# =============================================================================
# Texture Functions
# =============================================================================

_TEXTURE_FUNCTIONS_AVAILABLE = False
try:
    helios_lib.getPrimitiveTextureFile.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    helios_lib.getPrimitiveTextureFile.restype = ctypes.c_char_p
    helios_lib.getPrimitiveTextureFile.errcheck = _check_error

    helios_lib.setPrimitiveTextureFile.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_char_p]
    helios_lib.setPrimitiveTextureFile.restype = None
    helios_lib.setPrimitiveTextureFile.errcheck = _check_error

    helios_lib.getPrimitiveTextureSize.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    helios_lib.getPrimitiveTextureSize.restype = None
    helios_lib.getPrimitiveTextureSize.errcheck = _check_error

    helios_lib.getPrimitiveTextureUV.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getPrimitiveTextureUV.restype = ctypes.POINTER(ctypes.c_float)
    helios_lib.getPrimitiveTextureUV.errcheck = _check_error

    helios_lib.primitiveTextureHasTransparencyChannel.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    helios_lib.primitiveTextureHasTransparencyChannel.restype = ctypes.c_bool
    helios_lib.primitiveTextureHasTransparencyChannel.errcheck = _check_error

    helios_lib.getPrimitiveSolidFraction.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    helios_lib.getPrimitiveSolidFraction.restype = ctypes.c_float
    helios_lib.getPrimitiveSolidFraction.errcheck = _check_error

    helios_lib.overridePrimitiveTextureColor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    helios_lib.overridePrimitiveTextureColor.restype = None
    helios_lib.overridePrimitiveTextureColor.errcheck = _check_error

    helios_lib.usePrimitiveTextureColor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    helios_lib.usePrimitiveTextureColor.restype = None
    helios_lib.usePrimitiveTextureColor.errcheck = _check_error

    helios_lib.isPrimitiveTextureColorOverridden.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    helios_lib.isPrimitiveTextureColorOverridden.restype = ctypes.c_bool
    helios_lib.isPrimitiveTextureColorOverridden.errcheck = _check_error

    _TEXTURE_FUNCTIONS_AVAILABLE = True
except AttributeError:
    _TEXTURE_FUNCTIONS_AVAILABLE = False


def getPrimitiveTextureFile(context, uuid: int) -> str:
    """Get the texture file path of a primitive."""
    if not _TEXTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Texture functions not available. Rebuild with updated C++ wrapper.")
    result = helios_lib.getPrimitiveTextureFile(context, ctypes.c_uint(uuid))
    return result.decode('utf-8') if result else ""

def setPrimitiveTextureFile(context, uuid: int, texture_file: str) -> None:
    """Set the texture file path of a primitive."""
    if not _TEXTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Texture functions not available. Rebuild with updated C++ wrapper.")
    helios_lib.setPrimitiveTextureFile(context, ctypes.c_uint(uuid), texture_file.encode('utf-8'))

def getPrimitiveTextureSize(context, uuid: int):
    """Get the texture size of a primitive. Returns (width, height) tuple."""
    if not _TEXTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Texture functions not available. Rebuild with updated C++ wrapper.")
    width = ctypes.c_int()
    height = ctypes.c_int()
    helios_lib.getPrimitiveTextureSize(context, ctypes.c_uint(uuid), ctypes.byref(width), ctypes.byref(height))
    return (width.value, height.value)

def getPrimitiveTextureUV(context, uuid: int):
    """Get the texture UV coordinates of a primitive. Returns list of (u, v) float pairs."""
    if not _TEXTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Texture functions not available. Rebuild with updated C++ wrapper.")
    size = ctypes.c_uint()
    uv_ptr = helios_lib.getPrimitiveTextureUV(context, ctypes.c_uint(uuid), ctypes.byref(size))
    if size.value == 0 or not uv_ptr:
        return []
    uv_list = ctypes.cast(uv_ptr, ctypes.POINTER(ctypes.c_float * size.value)).contents
    return [(uv_list[i], uv_list[i+1]) for i in range(0, size.value, 2)]

def primitiveTextureHasTransparencyChannel(context, uuid: int) -> bool:
    """Check if primitive texture has a transparency channel."""
    if not _TEXTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Texture functions not available. Rebuild with updated C++ wrapper.")
    return helios_lib.primitiveTextureHasTransparencyChannel(context, ctypes.c_uint(uuid))

def getPrimitiveSolidFraction(context, uuid: int) -> float:
    """Get the solid fraction of a primitive."""
    if not _TEXTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Texture functions not available. Rebuild with updated C++ wrapper.")
    return helios_lib.getPrimitiveSolidFraction(context, ctypes.c_uint(uuid))

def overridePrimitiveTextureColor(context, uuid: int) -> None:
    """Override texture color with constant RGB color for a primitive."""
    if not _TEXTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Texture functions not available. Rebuild with updated C++ wrapper.")
    helios_lib.overridePrimitiveTextureColor(context, ctypes.c_uint(uuid))

def usePrimitiveTextureColor(context, uuid: int) -> None:
    """Use texture map color instead of constant RGB color for a primitive."""
    if not _TEXTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Texture functions not available. Rebuild with updated C++ wrapper.")
    helios_lib.usePrimitiveTextureColor(context, ctypes.c_uint(uuid))

def isPrimitiveTextureColorOverridden(context, uuid: int) -> bool:
    """Check if primitive texture color is overridden."""
    if not _TEXTURE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Texture functions not available. Rebuild with updated C++ wrapper.")
    return helios_lib.isPrimitiveTextureColorOverridden(context, ctypes.c_uint(uuid))


# =============================================================================
# Batch Getter Functions
# =============================================================================

_BATCH_FUNCTIONS_AVAILABLE = False
try:
    helios_lib.getBatchPrimitiveNormals.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getBatchPrimitiveNormals.restype = ctypes.POINTER(ctypes.c_float)
    helios_lib.getBatchPrimitiveNormals.errcheck = _check_error

    helios_lib.getBatchPrimitiveColors.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getBatchPrimitiveColors.restype = ctypes.POINTER(ctypes.c_float)
    helios_lib.getBatchPrimitiveColors.errcheck = _check_error

    helios_lib.getBatchPrimitiveAreas.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getBatchPrimitiveAreas.restype = ctypes.POINTER(ctypes.c_float)
    helios_lib.getBatchPrimitiveAreas.errcheck = _check_error

    helios_lib.getBatchPrimitiveTypes.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getBatchPrimitiveTypes.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.getBatchPrimitiveTypes.errcheck = _check_error

    helios_lib.getBatchPrimitiveSolidFractions.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getBatchPrimitiveSolidFractions.restype = ctypes.POINTER(ctypes.c_float)
    helios_lib.getBatchPrimitiveSolidFractions.errcheck = _check_error

    helios_lib.getBatchPrimitiveVertices.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getBatchPrimitiveVertices.restype = ctypes.POINTER(ctypes.c_float)
    helios_lib.getBatchPrimitiveVertices.errcheck = _check_error

    helios_lib.getBatchPrimitiveTextureUV.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getBatchPrimitiveTextureUV.restype = ctypes.POINTER(ctypes.c_float)
    helios_lib.getBatchPrimitiveTextureUV.errcheck = _check_error

    helios_lib.getBatchPrimitiveTextureFiles.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getBatchPrimitiveTextureFiles.restype = ctypes.c_char_p
    helios_lib.getBatchPrimitiveTextureFiles.errcheck = _check_error

    helios_lib.getBatchPrimitiveMaterialLabels.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getBatchPrimitiveMaterialLabels.restype = ctypes.c_char_p
    helios_lib.getBatchPrimitiveMaterialLabels.errcheck = _check_error

    helios_lib.resolveMaterialTextures.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_uint),
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_uint),
        ctypes.POINTER(ctypes.c_uint),
    ]
    helios_lib.resolveMaterialTextures.restype = ctypes.c_char_p
    helios_lib.resolveMaterialTextures.errcheck = _check_error

    helios_lib.packGPUBuffers.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_uint),
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_uint),
    ]
    helios_lib.packGPUBuffers.restype = ctypes.POINTER(ctypes.c_ubyte)
    helios_lib.packGPUBuffers.errcheck = _check_error

    _BATCH_FUNCTIONS_AVAILABLE = True
except AttributeError:
    _BATCH_FUNCTIONS_AVAILABLE = False


def _make_uuid_array(uuids: List[int]):
    """Create a ctypes uint array from a list of UUIDs."""
    return (ctypes.c_uint * len(uuids))(*uuids)

def getBatchPrimitiveNormals(context, uuids: List[int]):
    """Get normals for multiple primitives. Returns (float_ptr, count)."""
    if not _BATCH_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Batch functions not available. Rebuild with updated C++ wrapper.")
    uuids_array = _make_uuid_array(uuids)
    result_size = ctypes.c_uint()
    ptr = helios_lib.getBatchPrimitiveNormals(context, uuids_array, len(uuids), ctypes.byref(result_size))
    return (ptr, result_size.value)

def getBatchPrimitiveColors(context, uuids: List[int]):
    """Get colors for multiple primitives. Returns (float_ptr, count)."""
    if not _BATCH_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Batch functions not available. Rebuild with updated C++ wrapper.")
    uuids_array = _make_uuid_array(uuids)
    result_size = ctypes.c_uint()
    ptr = helios_lib.getBatchPrimitiveColors(context, uuids_array, len(uuids), ctypes.byref(result_size))
    return (ptr, result_size.value)

def getBatchPrimitiveAreas(context, uuids: List[int]):
    """Get areas for multiple primitives. Returns (float_ptr, count)."""
    if not _BATCH_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Batch functions not available. Rebuild with updated C++ wrapper.")
    uuids_array = _make_uuid_array(uuids)
    result_size = ctypes.c_uint()
    ptr = helios_lib.getBatchPrimitiveAreas(context, uuids_array, len(uuids), ctypes.byref(result_size))
    return (ptr, result_size.value)

def getBatchPrimitiveTypes(context, uuids: List[int]):
    """Get types for multiple primitives. Returns (uint_ptr, count)."""
    if not _BATCH_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Batch functions not available. Rebuild with updated C++ wrapper.")
    uuids_array = _make_uuid_array(uuids)
    result_size = ctypes.c_uint()
    ptr = helios_lib.getBatchPrimitiveTypes(context, uuids_array, len(uuids), ctypes.byref(result_size))
    return (ptr, result_size.value)

def getBatchPrimitiveSolidFractions(context, uuids: List[int]):
    """Get solid fractions for multiple primitives. Returns (float_ptr, count)."""
    if not _BATCH_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Batch functions not available. Rebuild with updated C++ wrapper.")
    uuids_array = _make_uuid_array(uuids)
    result_size = ctypes.c_uint()
    ptr = helios_lib.getBatchPrimitiveSolidFractions(context, uuids_array, len(uuids), ctypes.byref(result_size))
    return (ptr, result_size.value)

def getBatchPrimitiveVertices(context, uuids: List[int]):
    """Get vertices for multiple primitives. Returns (float_ptr, offsets_array, total_floats)."""
    if not _BATCH_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Batch functions not available. Rebuild with updated C++ wrapper.")
    count = len(uuids)
    uuids_array = _make_uuid_array(uuids)
    offsets = (ctypes.c_uint * (count + 1))()
    total_floats = ctypes.c_uint()
    ptr = helios_lib.getBatchPrimitiveVertices(context, uuids_array, count, offsets, ctypes.byref(total_floats))
    return (ptr, list(offsets), total_floats.value)

def getBatchPrimitiveTextureUV(context, uuids: List[int]):
    """Get texture UVs for multiple primitives. Returns (float_ptr, offsets_array, total_floats)."""
    if not _BATCH_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Batch functions not available. Rebuild with updated C++ wrapper.")
    count = len(uuids)
    uuids_array = _make_uuid_array(uuids)
    offsets = (ctypes.c_uint * (count + 1))()
    total_floats = ctypes.c_uint()
    ptr = helios_lib.getBatchPrimitiveTextureUV(context, uuids_array, count, offsets, ctypes.byref(total_floats))
    return (ptr, list(offsets), total_floats.value)

def getBatchPrimitiveTextureFiles(context, uuids: List[int]):
    """Get texture files for multiple primitives. Returns (char_ptr, offsets_array, total_chars)."""
    if not _BATCH_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Batch functions not available. Rebuild with updated C++ wrapper.")
    count = len(uuids)
    uuids_array = _make_uuid_array(uuids)
    offsets = (ctypes.c_uint * (count + 1))()
    total_chars = ctypes.c_uint()
    ptr = helios_lib.getBatchPrimitiveTextureFiles(context, uuids_array, count, offsets, ctypes.byref(total_chars))
    return (ptr, list(offsets), total_chars.value)

def getBatchPrimitiveMaterialLabels(context, uuids: List[int]):
    """Get material labels for multiple primitives. Returns (char_ptr, offsets_array, total_chars)."""
    if not _BATCH_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Batch functions not available. Rebuild with updated C++ wrapper.")
    count = len(uuids)
    uuids_array = _make_uuid_array(uuids)
    offsets = (ctypes.c_uint * (count + 1))()
    total_chars = ctypes.c_uint()
    ptr = helios_lib.getBatchPrimitiveMaterialLabels(context, uuids_array, count, offsets, ctypes.byref(total_chars))
    return (ptr, list(offsets), total_chars.value)


def resolveMaterialTextures(context, uuids: List[int], colors_np):
    """Resolve material texture suppression in C++.

    Args:
        context: Context pointer
        uuids: List of primitive UUIDs
        colors_np: numpy float32 array of shape (N, 3), modified IN-PLACE

    Returns:
        List[str] of resolved texture file paths
    """
    if not _BATCH_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Batch functions not available. Rebuild with updated C++ wrapper.")
    count = len(uuids)
    if count == 0:
        return []
    uuids_array = _make_uuid_array(uuids)
    offsets = (ctypes.c_uint * (count + 1))()
    total_chars = ctypes.c_uint()
    colors_ptr = colors_np.ctypes.data_as(ctypes.POINTER(ctypes.c_float))

    ptr = helios_lib.resolveMaterialTextures(
        context, uuids_array, count, colors_ptr, offsets, ctypes.byref(total_chars))

    if total_chars.value == 0 or not ptr:
        return ["" for _ in uuids]
    full_str = ptr.decode('utf-8') if isinstance(ptr, bytes) else ptr
    return [full_str[offsets[i]:offsets[i+1]] for i in range(count)]


def packGPUBuffers(context, uuids: List[int]) -> bytes:
    """Pack GPU-ready geometry buffers for a set of primitives in a single C++ pass.

    Returns the raw binary blob containing header, group descriptors, and
    contiguous typed arrays (positions, colors, uvs, indices, faceToUuid)
    that can be served directly to the frontend for zero-copy BufferGeometry loading.
    """
    if not _BATCH_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Batch functions not available. Rebuild with updated C++ wrapper.")
    count = len(uuids)
    if count == 0:
        return b''
    uuids_array = _make_uuid_array(uuids)
    out_size = ctypes.c_uint()
    ptr = helios_lib.packGPUBuffers(context, uuids_array, count, ctypes.byref(out_size))
    if not ptr or out_size.value == 0:
        return b''
    return bytes(ctypes.cast(ptr, ctypes.POINTER(ctypes.c_ubyte * out_size.value)).contents)


# ==================== Visibility Functions ====================

_VISIBILITY_FUNCTIONS_AVAILABLE = False
try:
    helios_lib.hidePrimitive.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.hidePrimitive.restype = None
    helios_lib.hidePrimitive.errcheck = _check_error

    helios_lib.hidePrimitives.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint]
    helios_lib.hidePrimitives.restype = None
    helios_lib.hidePrimitives.errcheck = _check_error

    helios_lib.showPrimitive.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.showPrimitive.restype = None
    helios_lib.showPrimitive.errcheck = _check_error

    helios_lib.showPrimitives.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint]
    helios_lib.showPrimitives.restype = None
    helios_lib.showPrimitives.errcheck = _check_error

    helios_lib.isPrimitiveHidden.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.isPrimitiveHidden.restype = ctypes.c_bool
    helios_lib.isPrimitiveHidden.errcheck = _check_error

    helios_lib.hideObject.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.hideObject.restype = None
    helios_lib.hideObject.errcheck = _check_error

    helios_lib.hideObjects.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint]
    helios_lib.hideObjects.restype = None
    helios_lib.hideObjects.errcheck = _check_error

    helios_lib.showObject.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.showObject.restype = None
    helios_lib.showObject.errcheck = _check_error

    helios_lib.showObjects.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint]
    helios_lib.showObjects.restype = None
    helios_lib.showObjects.errcheck = _check_error

    helios_lib.isObjectHidden.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.isObjectHidden.restype = ctypes.c_bool
    helios_lib.isObjectHidden.errcheck = _check_error

    _VISIBILITY_FUNCTIONS_AVAILABLE = True
except AttributeError:
    _VISIBILITY_FUNCTIONS_AVAILABLE = False

_NOT_AVAILABLE_VISIBILITY_MSG = (
    "Visibility functions not available in current Helios library. "
    "Rebuild PyHelios with updated C++ wrapper implementation."
)


def hidePrimitiveWrapper(context, uuid: int) -> None:
    if not _VISIBILITY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_VISIBILITY_MSG)
    helios_lib.hidePrimitive(context, uuid)


def hidePrimitivesWrapper(context, uuids: List[int]) -> None:
    if not _VISIBILITY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_VISIBILITY_MSG)
    if not uuids:
        return
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.hidePrimitives(context, uuids_array, len(uuids))


def showPrimitiveWrapper(context, uuid: int) -> None:
    if not _VISIBILITY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_VISIBILITY_MSG)
    helios_lib.showPrimitive(context, uuid)


def showPrimitivesWrapper(context, uuids: List[int]) -> None:
    if not _VISIBILITY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_VISIBILITY_MSG)
    if not uuids:
        return
    uuids_array = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.showPrimitives(context, uuids_array, len(uuids))


def isPrimitiveHiddenWrapper(context, uuid: int) -> bool:
    if not _VISIBILITY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_VISIBILITY_MSG)
    return helios_lib.isPrimitiveHidden(context, uuid)


def hideObjectWrapper(context, objID: int) -> None:
    if not _VISIBILITY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_VISIBILITY_MSG)
    helios_lib.hideObject(context, objID)


def hideObjectsWrapper(context, objIDs: List[int]) -> None:
    if not _VISIBILITY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_VISIBILITY_MSG)
    if not objIDs:
        return
    ids_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    helios_lib.hideObjects(context, ids_array, len(objIDs))


def showObjectWrapper(context, objID: int) -> None:
    if not _VISIBILITY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_VISIBILITY_MSG)
    helios_lib.showObject(context, objID)


def showObjectsWrapper(context, objIDs: List[int]) -> None:
    if not _VISIBILITY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_VISIBILITY_MSG)
    if not objIDs:
        return
    ids_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    helios_lib.showObjects(context, ids_array, len(objIDs))


def isObjectHiddenWrapper(context, objID: int) -> bool:
    if not _VISIBILITY_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_VISIBILITY_MSG)
    return helios_lib.isObjectHidden(context, objID)


# ==================== Object Data Functions ====================

_OBJECT_DATA_FUNCTIONS_AVAILABLE = False
try:
    # Setters (single)
    for _t, _ct in [('Int', ctypes.c_int), ('UInt', ctypes.c_uint), ('Float', ctypes.c_float), ('Double', ctypes.c_double)]:
        _fn = getattr(helios_lib, f'setObjectData{_t}')
        _fn.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, _ct]
        _fn.restype = None
        _fn.errcheck = _check_error

    helios_lib.setObjectDataString.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.setObjectDataString.restype = None
    helios_lib.setObjectDataString.errcheck = _check_error

    helios_lib.setObjectDataVec2.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_float, ctypes.c_float]
    helios_lib.setObjectDataVec2.restype = None
    helios_lib.setObjectDataVec2.errcheck = _check_error
    helios_lib.setObjectDataVec3.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.setObjectDataVec3.restype = None
    helios_lib.setObjectDataVec3.errcheck = _check_error
    helios_lib.setObjectDataVec4.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.setObjectDataVec4.restype = None
    helios_lib.setObjectDataVec4.errcheck = _check_error

    helios_lib.setObjectDataInt2.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
    helios_lib.setObjectDataInt2.restype = None
    helios_lib.setObjectDataInt2.errcheck = _check_error
    helios_lib.setObjectDataInt3.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    helios_lib.setObjectDataInt3.restype = None
    helios_lib.setObjectDataInt3.errcheck = _check_error
    helios_lib.setObjectDataInt4.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    helios_lib.setObjectDataInt4.restype = None
    helios_lib.setObjectDataInt4.errcheck = _check_error

    # Getters
    for _t, _ct in [('Int', ctypes.c_int), ('UInt', ctypes.c_uint), ('Float', ctypes.c_float), ('Double', ctypes.c_double)]:
        _fn = getattr(helios_lib, f'getObjectData{_t}')
        _fn.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p]
        _fn.restype = _ct
        _fn.errcheck = _check_error

    helios_lib.getObjectDataString.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
    helios_lib.getObjectDataString.restype = ctypes.c_int
    helios_lib.getObjectDataString.errcheck = _check_error

    for _n, _ct, _count in [('Vec2', ctypes.c_float, 2), ('Vec3', ctypes.c_float, 3), ('Vec4', ctypes.c_float, 4),
                             ('Int2', ctypes.c_int, 2), ('Int3', ctypes.c_int, 3), ('Int4', ctypes.c_int, 4)]:
        _fn = getattr(helios_lib, f'getObjectData{_n}')
        _fn.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p] + [ctypes.POINTER(_ct)] * _count
        _fn.restype = None
        _fn.errcheck = _check_error

    # Utilities
    helios_lib.getObjectDataType.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p]
    helios_lib.getObjectDataType.restype = ctypes.c_int
    helios_lib.getObjectDataType.errcheck = _check_error

    helios_lib.getObjectDataSize.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p]
    helios_lib.getObjectDataSize.restype = ctypes.c_int
    helios_lib.getObjectDataSize.errcheck = _check_error

    helios_lib.doesObjectDataExist.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p]
    helios_lib.doesObjectDataExist.restype = ctypes.c_bool
    helios_lib.doesObjectDataExist.errcheck = _check_error

    helios_lib.clearObjectData.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p]
    helios_lib.clearObjectData.restype = None
    helios_lib.clearObjectData.errcheck = _check_error

    helios_lib.clearObjectDataBatch.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.c_char_p]
    helios_lib.clearObjectDataBatch.restype = None
    helios_lib.clearObjectDataBatch.errcheck = _check_error

    helios_lib.listObjectData.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.listObjectData.restype = ctypes.POINTER(ctypes.c_char_p)
    helios_lib.listObjectData.errcheck = _check_error

    helios_lib.listAllObjectDataLabels.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.listAllObjectDataLabels.restype = ctypes.POINTER(ctypes.c_char_p)
    helios_lib.listAllObjectDataLabels.errcheck = _check_error

    helios_lib.duplicateObjectData.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.duplicateObjectData.restype = None
    helios_lib.duplicateObjectData.errcheck = _check_error

    helios_lib.renameObjectData.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.renameObjectData.restype = None
    helios_lib.renameObjectData.errcheck = _check_error

    # Filters
    for _t, _ct in [('Float', ctypes.c_float), ('Double', ctypes.c_double), ('Int', ctypes.c_int), ('UInt', ctypes.c_uint)]:
        _fn = getattr(helios_lib, f'filterObjectsByData{_t}')
        _fn.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.c_char_p, _ct, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint)]
        _fn.restype = ctypes.POINTER(ctypes.c_uint)
        _fn.errcheck = _check_error

    helios_lib.filterObjectsByDataString.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.filterObjectsByDataString.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.filterObjectsByDataString.errcheck = _check_error

    _OBJECT_DATA_FUNCTIONS_AVAILABLE = True
except AttributeError:
    _OBJECT_DATA_FUNCTIONS_AVAILABLE = False

_BROADCAST_OBJECT_DATA_AVAILABLE = False
try:
    for _t, _ct in [('Int', ctypes.c_int), ('UInt', ctypes.c_uint), ('Float', ctypes.c_float), ('Double', ctypes.c_double)]:
        _fn = getattr(helios_lib, f'setBroadcastObjectData{_t}')
        _fn.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_size_t, ctypes.c_char_p, _ct]
        _fn.restype = None
        _fn.errcheck = _check_error

    helios_lib.setBroadcastObjectDataString.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_size_t, ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.setBroadcastObjectDataString.restype = None
    helios_lib.setBroadcastObjectDataString.errcheck = _check_error

    for _n, _cts in [('Vec2', [ctypes.c_float]*2), ('Vec3', [ctypes.c_float]*3), ('Vec4', [ctypes.c_float]*4),
                     ('Int2', [ctypes.c_int]*2), ('Int3', [ctypes.c_int]*3), ('Int4', [ctypes.c_int]*4)]:
        _fn = getattr(helios_lib, f'setBroadcastObjectData{_n}')
        _fn.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_size_t, ctypes.c_char_p] + _cts
        _fn.restype = None
        _fn.errcheck = _check_error

    _BROADCAST_OBJECT_DATA_AVAILABLE = True
except AttributeError:
    _BROADCAST_OBJECT_DATA_AVAILABLE = False

_NOT_AVAILABLE_OBJDATA_MSG = (
    "Object data functions not available in current Helios library. "
    "Rebuild PyHelios with updated C++ wrapper implementation."
)
_NOT_AVAILABLE_BROADCAST_OBJDATA_MSG = (
    "Broadcast object data functions not available. "
    "Rebuild native library with updated version."
)


# --- Object data wrapper functions ---

def setObjectDataInt(context, objID: int, label: str, value: int):
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    helios_lib.setObjectDataInt(context, objID, label.encode('utf-8'), value)

def setObjectDataUInt(context, objID: int, label: str, value: int):
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    helios_lib.setObjectDataUInt(context, objID, label.encode('utf-8'), value)

def setObjectDataFloat(context, objID: int, label: str, value: float):
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    helios_lib.setObjectDataFloat(context, objID, label.encode('utf-8'), value)

def setObjectDataDouble(context, objID: int, label: str, value: float):
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    helios_lib.setObjectDataDouble(context, objID, label.encode('utf-8'), value)

def setObjectDataString(context, objID: int, label: str, value: str):
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    helios_lib.setObjectDataString(context, objID, label.encode('utf-8'), value.encode('utf-8'))

def setObjectDataVec2(context, objID: int, label: str, x: float, y: float):
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    helios_lib.setObjectDataVec2(context, objID, label.encode('utf-8'), x, y)

def setObjectDataVec3(context, objID: int, label: str, x: float, y: float, z: float):
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    helios_lib.setObjectDataVec3(context, objID, label.encode('utf-8'), x, y, z)

def setObjectDataVec4(context, objID: int, label: str, x: float, y: float, z: float, w: float):
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    helios_lib.setObjectDataVec4(context, objID, label.encode('utf-8'), x, y, z, w)

def setObjectDataInt2(context, objID: int, label: str, x: int, y: int):
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    helios_lib.setObjectDataInt2(context, objID, label.encode('utf-8'), x, y)

def setObjectDataInt3(context, objID: int, label: str, x: int, y: int, z: int):
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    helios_lib.setObjectDataInt3(context, objID, label.encode('utf-8'), x, y, z)

def setObjectDataInt4(context, objID: int, label: str, x: int, y: int, z: int, w: int):
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    helios_lib.setObjectDataInt4(context, objID, label.encode('utf-8'), x, y, z, w)

# Getters

def getObjectDataInt(context, objID: int, label: str) -> int:
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    return helios_lib.getObjectDataInt(context, objID, label.encode('utf-8'))

def getObjectDataUInt(context, objID: int, label: str) -> int:
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    return helios_lib.getObjectDataUInt(context, objID, label.encode('utf-8'))

def getObjectDataFloat(context, objID: int, label: str) -> float:
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    return helios_lib.getObjectDataFloat(context, objID, label.encode('utf-8'))

def getObjectDataDouble(context, objID: int, label: str) -> float:
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    return helios_lib.getObjectDataDouble(context, objID, label.encode('utf-8'))

def getObjectDataString(context, objID: int, label: str) -> str:
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    buffer = ctypes.create_string_buffer(1024)
    helios_lib.getObjectDataString(context, objID, label.encode('utf-8'), buffer, 1024)
    return buffer.value.decode('utf-8')

def getObjectDataVec2(context, objID: int, label: str) -> List[float]:
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    x, y = ctypes.c_float(), ctypes.c_float()
    helios_lib.getObjectDataVec2(context, objID, label.encode('utf-8'), ctypes.byref(x), ctypes.byref(y))
    return [x.value, y.value]

def getObjectDataVec3(context, objID: int, label: str) -> List[float]:
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    x, y, z = ctypes.c_float(), ctypes.c_float(), ctypes.c_float()
    helios_lib.getObjectDataVec3(context, objID, label.encode('utf-8'), ctypes.byref(x), ctypes.byref(y), ctypes.byref(z))
    return [x.value, y.value, z.value]

def getObjectDataVec4(context, objID: int, label: str) -> List[float]:
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    x, y, z, w = ctypes.c_float(), ctypes.c_float(), ctypes.c_float(), ctypes.c_float()
    helios_lib.getObjectDataVec4(context, objID, label.encode('utf-8'), ctypes.byref(x), ctypes.byref(y), ctypes.byref(z), ctypes.byref(w))
    return [x.value, y.value, z.value, w.value]

def getObjectDataInt2(context, objID: int, label: str) -> List[int]:
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    x, y = ctypes.c_int(), ctypes.c_int()
    helios_lib.getObjectDataInt2(context, objID, label.encode('utf-8'), ctypes.byref(x), ctypes.byref(y))
    return [x.value, y.value]

def getObjectDataInt3(context, objID: int, label: str) -> List[int]:
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    x, y, z = ctypes.c_int(), ctypes.c_int(), ctypes.c_int()
    helios_lib.getObjectDataInt3(context, objID, label.encode('utf-8'), ctypes.byref(x), ctypes.byref(y), ctypes.byref(z))
    return [x.value, y.value, z.value]

def getObjectDataInt4(context, objID: int, label: str) -> List[int]:
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    x, y, z, w = ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int()
    helios_lib.getObjectDataInt4(context, objID, label.encode('utf-8'), ctypes.byref(x), ctypes.byref(y), ctypes.byref(z), ctypes.byref(w))
    return [x.value, y.value, z.value, w.value]

# Utilities

def getObjectDataTypeWrapper(context, objID: int, label: str) -> int:
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    return helios_lib.getObjectDataType(context, objID, label.encode('utf-8'))

def getObjectDataSizeWrapper(context, objID: int, label: str) -> int:
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    return helios_lib.getObjectDataSize(context, objID, label.encode('utf-8'))

def doesObjectDataExistWrapper(context, objID: int, label: str) -> bool:
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    return helios_lib.doesObjectDataExist(context, objID, label.encode('utf-8'))

def clearObjectDataWrapper(context, objID: int, label: str):
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    helios_lib.clearObjectData(context, objID, label.encode('utf-8'))

def clearObjectDataBatchWrapper(context, objIDs: List[int], label: str):
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    if not objIDs:
        return
    ids_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    helios_lib.clearObjectDataBatch(context, ids_array, len(objIDs), label.encode('utf-8'))

def listObjectDataWrapper(context, objID: int) -> List[str]:
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    count = ctypes.c_uint()
    result_ptr = helios_lib.listObjectData(context, objID, ctypes.byref(count))
    if count.value == 0 or not result_ptr:
        return []
    return [result_ptr[i].decode('utf-8') for i in range(count.value)]

def listAllObjectDataLabelsWrapper(context) -> List[str]:
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    count = ctypes.c_uint()
    result_ptr = helios_lib.listAllObjectDataLabels(context, ctypes.byref(count))
    if count.value == 0 or not result_ptr:
        return []
    return [result_ptr[i].decode('utf-8') for i in range(count.value)]

def duplicateObjectDataWrapper(context, objID: int, old_label: str, new_label: str):
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    helios_lib.duplicateObjectData(context, objID, old_label.encode('utf-8'), new_label.encode('utf-8'))

def renameObjectDataWrapper(context, objID: int, old_label: str, new_label: str):
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    helios_lib.renameObjectData(context, objID, old_label.encode('utf-8'), new_label.encode('utf-8'))

# Broadcast setters

def setBroadcastObjectDataInt(context, objIDs: List[int], label: str, value: int):
    if not _BROADCAST_OBJECT_DATA_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_BROADCAST_OBJDATA_MSG)
    if not objIDs:
        raise ValueError("Object IDs list cannot be empty")
    ids_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    helios_lib.setBroadcastObjectDataInt(context, ids_array, len(objIDs), label.encode('utf-8'), value)

def setBroadcastObjectDataUInt(context, objIDs: List[int], label: str, value: int):
    if not _BROADCAST_OBJECT_DATA_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_BROADCAST_OBJDATA_MSG)
    if not objIDs:
        raise ValueError("Object IDs list cannot be empty")
    ids_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    helios_lib.setBroadcastObjectDataUInt(context, ids_array, len(objIDs), label.encode('utf-8'), value)

def setBroadcastObjectDataFloat(context, objIDs: List[int], label: str, value: float):
    if not _BROADCAST_OBJECT_DATA_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_BROADCAST_OBJDATA_MSG)
    if not objIDs:
        raise ValueError("Object IDs list cannot be empty")
    ids_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    helios_lib.setBroadcastObjectDataFloat(context, ids_array, len(objIDs), label.encode('utf-8'), value)

def setBroadcastObjectDataDouble(context, objIDs: List[int], label: str, value: float):
    if not _BROADCAST_OBJECT_DATA_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_BROADCAST_OBJDATA_MSG)
    if not objIDs:
        raise ValueError("Object IDs list cannot be empty")
    ids_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    helios_lib.setBroadcastObjectDataDouble(context, ids_array, len(objIDs), label.encode('utf-8'), value)

def setBroadcastObjectDataString(context, objIDs: List[int], label: str, value: str):
    if not _BROADCAST_OBJECT_DATA_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_BROADCAST_OBJDATA_MSG)
    if not objIDs:
        raise ValueError("Object IDs list cannot be empty")
    ids_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    helios_lib.setBroadcastObjectDataString(context, ids_array, len(objIDs), label.encode('utf-8'), value.encode('utf-8'))

def setBroadcastObjectDataVec2(context, objIDs: List[int], label: str, x: float, y: float):
    if not _BROADCAST_OBJECT_DATA_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_BROADCAST_OBJDATA_MSG)
    if not objIDs:
        raise ValueError("Object IDs list cannot be empty")
    ids_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    helios_lib.setBroadcastObjectDataVec2(context, ids_array, len(objIDs), label.encode('utf-8'), x, y)

def setBroadcastObjectDataVec3(context, objIDs: List[int], label: str, x: float, y: float, z: float):
    if not _BROADCAST_OBJECT_DATA_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_BROADCAST_OBJDATA_MSG)
    if not objIDs:
        raise ValueError("Object IDs list cannot be empty")
    ids_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    helios_lib.setBroadcastObjectDataVec3(context, ids_array, len(objIDs), label.encode('utf-8'), x, y, z)

def setBroadcastObjectDataVec4(context, objIDs: List[int], label: str, x: float, y: float, z: float, w: float):
    if not _BROADCAST_OBJECT_DATA_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_BROADCAST_OBJDATA_MSG)
    if not objIDs:
        raise ValueError("Object IDs list cannot be empty")
    ids_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    helios_lib.setBroadcastObjectDataVec4(context, ids_array, len(objIDs), label.encode('utf-8'), x, y, z, w)

def setBroadcastObjectDataInt2(context, objIDs: List[int], label: str, x: int, y: int):
    if not _BROADCAST_OBJECT_DATA_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_BROADCAST_OBJDATA_MSG)
    if not objIDs:
        raise ValueError("Object IDs list cannot be empty")
    ids_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    helios_lib.setBroadcastObjectDataInt2(context, ids_array, len(objIDs), label.encode('utf-8'), x, y)

def setBroadcastObjectDataInt3(context, objIDs: List[int], label: str, x: int, y: int, z: int):
    if not _BROADCAST_OBJECT_DATA_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_BROADCAST_OBJDATA_MSG)
    if not objIDs:
        raise ValueError("Object IDs list cannot be empty")
    ids_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    helios_lib.setBroadcastObjectDataInt3(context, ids_array, len(objIDs), label.encode('utf-8'), x, y, z)

def setBroadcastObjectDataInt4(context, objIDs: List[int], label: str, x: int, y: int, z: int, w: int):
    if not _BROADCAST_OBJECT_DATA_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_BROADCAST_OBJDATA_MSG)
    if not objIDs:
        raise ValueError("Object IDs list cannot be empty")
    ids_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    helios_lib.setBroadcastObjectDataInt4(context, ids_array, len(objIDs), label.encode('utf-8'), x, y, z, w)

# Filters

def filterObjectsByDataFloatWrapper(context, objIDs: List[int], label: str, value: float, comparator: str) -> List[int]:
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    ids_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    result_count = ctypes.c_uint()
    result_ptr = helios_lib.filterObjectsByDataFloat(context, ids_array, len(objIDs), label.encode('utf-8'), value, comparator.encode('utf-8'), ctypes.byref(result_count))
    if result_count.value == 0 or not result_ptr:
        return []
    return [result_ptr[i] for i in range(result_count.value)]

def filterObjectsByDataDoubleWrapper(context, objIDs: List[int], label: str, value: float, comparator: str) -> List[int]:
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    ids_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    result_count = ctypes.c_uint()
    result_ptr = helios_lib.filterObjectsByDataDouble(context, ids_array, len(objIDs), label.encode('utf-8'), value, comparator.encode('utf-8'), ctypes.byref(result_count))
    if result_count.value == 0 or not result_ptr:
        return []
    return [result_ptr[i] for i in range(result_count.value)]

def filterObjectsByDataIntWrapper(context, objIDs: List[int], label: str, value: int, comparator: str) -> List[int]:
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    ids_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    result_count = ctypes.c_uint()
    result_ptr = helios_lib.filterObjectsByDataInt(context, ids_array, len(objIDs), label.encode('utf-8'), value, comparator.encode('utf-8'), ctypes.byref(result_count))
    if result_count.value == 0 or not result_ptr:
        return []
    return [result_ptr[i] for i in range(result_count.value)]

def filterObjectsByDataUIntWrapper(context, objIDs: List[int], label: str, value: int, comparator: str) -> List[int]:
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    ids_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    result_count = ctypes.c_uint()
    result_ptr = helios_lib.filterObjectsByDataUInt(context, ids_array, len(objIDs), label.encode('utf-8'), value, comparator.encode('utf-8'), ctypes.byref(result_count))
    if result_count.value == 0 or not result_ptr:
        return []
    return [result_ptr[i] for i in range(result_count.value)]

def filterObjectsByDataStringWrapper(context, objIDs: List[int], label: str, value: str) -> List[int]:
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    ids_array = (ctypes.c_uint * len(objIDs))(*objIDs)
    result_count = ctypes.c_uint()
    result_ptr = helios_lib.filterObjectsByDataString(context, ids_array, len(objIDs), label.encode('utf-8'), value.encode('utf-8'), ctypes.byref(result_count))
    if result_count.value == 0 or not result_ptr:
        return []
    return [result_ptr[i] for i in range(result_count.value)]

# Auto-detecting getter (mirrors getPrimitiveDataAuto pattern)

def getObjectDataAuto(context, objID: int, label: str):
    if not _OBJECT_DATA_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_OBJDATA_MSG)
    dtype = getObjectDataTypeWrapper(context, objID, label)
    # HeliosDataType enum: 0=INT, 1=UINT, 2=FLOAT, 3=DOUBLE, 4=VEC2, 5=VEC3, 6=VEC4,
    #                      7=INT2, 8=INT3, 9=INT4, 10=STRING
    if dtype == 0:
        return getObjectDataInt(context, objID, label)
    elif dtype == 1:
        return getObjectDataUInt(context, objID, label)
    elif dtype == 2:
        return getObjectDataFloat(context, objID, label)
    elif dtype == 3:
        return getObjectDataDouble(context, objID, label)
    elif dtype == 4:
        return getObjectDataVec2(context, objID, label)
    elif dtype == 5:
        return getObjectDataVec3(context, objID, label)
    elif dtype == 6:
        return getObjectDataVec4(context, objID, label)
    elif dtype == 7:
        return getObjectDataInt2(context, objID, label)
    elif dtype == 8:
        return getObjectDataInt3(context, objID, label)
    elif dtype == 9:
        return getObjectDataInt4(context, objID, label)
    elif dtype == 10:
        return getObjectDataString(context, objID, label)
    else:
        raise ValueError(f"Unknown object data type code: {dtype}")


# ==================== Global Data Functions ====================

_GLOBAL_DATA_FUNCTIONS_AVAILABLE = False
try:
    for _t, _ct in [('Int', ctypes.c_int), ('UInt', ctypes.c_uint), ('Float', ctypes.c_float), ('Double', ctypes.c_double)]:
        _fn = getattr(helios_lib, f'setGlobalData{_t}')
        _fn.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, _ct]
        _fn.restype = None
        _fn.errcheck = _check_error

    helios_lib.setGlobalDataString.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.setGlobalDataString.restype = None
    helios_lib.setGlobalDataString.errcheck = _check_error

    helios_lib.setGlobalDataVec2.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_float, ctypes.c_float]
    helios_lib.setGlobalDataVec2.restype = None
    helios_lib.setGlobalDataVec2.errcheck = _check_error
    helios_lib.setGlobalDataVec3.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.setGlobalDataVec3.restype = None
    helios_lib.setGlobalDataVec3.errcheck = _check_error
    helios_lib.setGlobalDataVec4.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.setGlobalDataVec4.restype = None
    helios_lib.setGlobalDataVec4.errcheck = _check_error
    helios_lib.setGlobalDataInt2.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
    helios_lib.setGlobalDataInt2.restype = None
    helios_lib.setGlobalDataInt2.errcheck = _check_error
    helios_lib.setGlobalDataInt3.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    helios_lib.setGlobalDataInt3.restype = None
    helios_lib.setGlobalDataInt3.errcheck = _check_error
    helios_lib.setGlobalDataInt4.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    helios_lib.setGlobalDataInt4.restype = None
    helios_lib.setGlobalDataInt4.errcheck = _check_error

    for _t, _ct in [('Int', ctypes.c_int), ('UInt', ctypes.c_uint), ('Float', ctypes.c_float), ('Double', ctypes.c_double)]:
        _fn = getattr(helios_lib, f'getGlobalData{_t}')
        _fn.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p]
        _fn.restype = _ct
        _fn.errcheck = _check_error

    helios_lib.getGlobalDataString.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
    helios_lib.getGlobalDataString.restype = ctypes.c_int
    helios_lib.getGlobalDataString.errcheck = _check_error

    for _n, _ct, _count in [('Vec2', ctypes.c_float, 2), ('Vec3', ctypes.c_float, 3), ('Vec4', ctypes.c_float, 4),
                             ('Int2', ctypes.c_int, 2), ('Int3', ctypes.c_int, 3), ('Int4', ctypes.c_int, 4)]:
        _fn = getattr(helios_lib, f'getGlobalData{_n}')
        _fn.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p] + [ctypes.POINTER(_ct)] * _count
        _fn.restype = None
        _fn.errcheck = _check_error

    helios_lib.getGlobalDataType.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p]
    helios_lib.getGlobalDataType.restype = ctypes.c_int
    helios_lib.getGlobalDataType.errcheck = _check_error
    helios_lib.getGlobalDataSize.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p]
    helios_lib.getGlobalDataSize.restype = ctypes.c_int
    helios_lib.getGlobalDataSize.errcheck = _check_error
    helios_lib.doesGlobalDataExist.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p]
    helios_lib.doesGlobalDataExist.restype = ctypes.c_bool
    helios_lib.doesGlobalDataExist.errcheck = _check_error
    helios_lib.clearGlobalData.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p]
    helios_lib.clearGlobalData.restype = None
    helios_lib.clearGlobalData.errcheck = _check_error
    helios_lib.renameGlobalData.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.renameGlobalData.restype = None
    helios_lib.renameGlobalData.errcheck = _check_error
    helios_lib.duplicateGlobalData.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.duplicateGlobalData.restype = None
    helios_lib.duplicateGlobalData.errcheck = _check_error
    helios_lib.listGlobalData.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.listGlobalData.restype = ctypes.POINTER(ctypes.c_char_p)
    helios_lib.listGlobalData.errcheck = _check_error

    for _t, _ct in [('Int', ctypes.c_int), ('UInt', ctypes.c_uint), ('Float', ctypes.c_float), ('Double', ctypes.c_double)]:
        _fn = getattr(helios_lib, f'incrementGlobalData{_t}')
        _fn.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, _ct]
        _fn.restype = None
        _fn.errcheck = _check_error

    _GLOBAL_DATA_FUNCTIONS_AVAILABLE = True
except AttributeError:
    _GLOBAL_DATA_FUNCTIONS_AVAILABLE = False

_NOT_AVAILABLE_GLOBALDATA_MSG = (
    "Global data functions not available in current Helios library. "
    "Rebuild PyHelios with updated C++ wrapper implementation."
)


def setGlobalDataInt(context, label: str, value: int):
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    helios_lib.setGlobalDataInt(context, label.encode('utf-8'), value)

def setGlobalDataUInt(context, label: str, value: int):
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    helios_lib.setGlobalDataUInt(context, label.encode('utf-8'), value)

def setGlobalDataFloat(context, label: str, value: float):
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    helios_lib.setGlobalDataFloat(context, label.encode('utf-8'), value)

def setGlobalDataDouble(context, label: str, value: float):
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    helios_lib.setGlobalDataDouble(context, label.encode('utf-8'), value)

def setGlobalDataString(context, label: str, value: str):
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    helios_lib.setGlobalDataString(context, label.encode('utf-8'), value.encode('utf-8'))

def setGlobalDataVec2(context, label: str, x: float, y: float):
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    helios_lib.setGlobalDataVec2(context, label.encode('utf-8'), x, y)

def setGlobalDataVec3(context, label: str, x: float, y: float, z: float):
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    helios_lib.setGlobalDataVec3(context, label.encode('utf-8'), x, y, z)

def setGlobalDataVec4(context, label: str, x: float, y: float, z: float, w: float):
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    helios_lib.setGlobalDataVec4(context, label.encode('utf-8'), x, y, z, w)

def setGlobalDataInt2(context, label: str, x: int, y: int):
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    helios_lib.setGlobalDataInt2(context, label.encode('utf-8'), x, y)

def setGlobalDataInt3(context, label: str, x: int, y: int, z: int):
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    helios_lib.setGlobalDataInt3(context, label.encode('utf-8'), x, y, z)

def setGlobalDataInt4(context, label: str, x: int, y: int, z: int, w: int):
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    helios_lib.setGlobalDataInt4(context, label.encode('utf-8'), x, y, z, w)

def getGlobalDataInt(context, label: str) -> int:
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    return helios_lib.getGlobalDataInt(context, label.encode('utf-8'))

def getGlobalDataUInt(context, label: str) -> int:
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    return helios_lib.getGlobalDataUInt(context, label.encode('utf-8'))

def getGlobalDataFloat(context, label: str) -> float:
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    return helios_lib.getGlobalDataFloat(context, label.encode('utf-8'))

def getGlobalDataDouble(context, label: str) -> float:
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    return helios_lib.getGlobalDataDouble(context, label.encode('utf-8'))

def getGlobalDataString(context, label: str) -> str:
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    buffer = ctypes.create_string_buffer(1024)
    helios_lib.getGlobalDataString(context, label.encode('utf-8'), buffer, 1024)
    return buffer.value.decode('utf-8')

def getGlobalDataVec2(context, label: str) -> List[float]:
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    x, y = ctypes.c_float(), ctypes.c_float()
    helios_lib.getGlobalDataVec2(context, label.encode('utf-8'), ctypes.byref(x), ctypes.byref(y))
    return [x.value, y.value]

def getGlobalDataVec3(context, label: str) -> List[float]:
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    x, y, z = ctypes.c_float(), ctypes.c_float(), ctypes.c_float()
    helios_lib.getGlobalDataVec3(context, label.encode('utf-8'), ctypes.byref(x), ctypes.byref(y), ctypes.byref(z))
    return [x.value, y.value, z.value]

def getGlobalDataVec4(context, label: str) -> List[float]:
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    x, y, z, w = ctypes.c_float(), ctypes.c_float(), ctypes.c_float(), ctypes.c_float()
    helios_lib.getGlobalDataVec4(context, label.encode('utf-8'), ctypes.byref(x), ctypes.byref(y), ctypes.byref(z), ctypes.byref(w))
    return [x.value, y.value, z.value, w.value]

def getGlobalDataInt2(context, label: str) -> List[int]:
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    x, y = ctypes.c_int(), ctypes.c_int()
    helios_lib.getGlobalDataInt2(context, label.encode('utf-8'), ctypes.byref(x), ctypes.byref(y))
    return [x.value, y.value]

def getGlobalDataInt3(context, label: str) -> List[int]:
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    x, y, z = ctypes.c_int(), ctypes.c_int(), ctypes.c_int()
    helios_lib.getGlobalDataInt3(context, label.encode('utf-8'), ctypes.byref(x), ctypes.byref(y), ctypes.byref(z))
    return [x.value, y.value, z.value]

def getGlobalDataInt4(context, label: str) -> List[int]:
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    x, y, z, w = ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int()
    helios_lib.getGlobalDataInt4(context, label.encode('utf-8'), ctypes.byref(x), ctypes.byref(y), ctypes.byref(z), ctypes.byref(w))
    return [x.value, y.value, z.value, w.value]

def getGlobalDataTypeWrapper(context, label: str) -> int:
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    return helios_lib.getGlobalDataType(context, label.encode('utf-8'))

def getGlobalDataSizeWrapper(context, label: str) -> int:
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    return helios_lib.getGlobalDataSize(context, label.encode('utf-8'))

def doesGlobalDataExistWrapper(context, label: str) -> bool:
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    return helios_lib.doesGlobalDataExist(context, label.encode('utf-8'))

def clearGlobalDataWrapper(context, label: str):
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    helios_lib.clearGlobalData(context, label.encode('utf-8'))

def renameGlobalDataWrapper(context, old_label: str, new_label: str):
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    helios_lib.renameGlobalData(context, old_label.encode('utf-8'), new_label.encode('utf-8'))

def duplicateGlobalDataWrapper(context, old_label: str, new_label: str):
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    helios_lib.duplicateGlobalData(context, old_label.encode('utf-8'), new_label.encode('utf-8'))

def listGlobalDataWrapper(context) -> List[str]:
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    count = ctypes.c_uint()
    result_ptr = helios_lib.listGlobalData(context, ctypes.byref(count))
    if count.value == 0 or not result_ptr:
        return []
    return [result_ptr[i].decode('utf-8') for i in range(count.value)]

def incrementGlobalDataIntWrapper(context, label: str, increment: int):
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    helios_lib.incrementGlobalDataInt(context, label.encode('utf-8'), increment)

def incrementGlobalDataUIntWrapper(context, label: str, increment: int):
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    helios_lib.incrementGlobalDataUInt(context, label.encode('utf-8'), increment)

def incrementGlobalDataFloatWrapper(context, label: str, increment: float):
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    helios_lib.incrementGlobalDataFloat(context, label.encode('utf-8'), increment)

def incrementGlobalDataDoubleWrapper(context, label: str, increment: float):
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    helios_lib.incrementGlobalDataDouble(context, label.encode('utf-8'), increment)

def getGlobalDataAuto(context, label: str):
    if not _GLOBAL_DATA_FUNCTIONS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_GLOBALDATA_MSG)
    dtype = getGlobalDataTypeWrapper(context, label)
    _dispatch = {0: getGlobalDataInt, 1: getGlobalDataUInt, 2: getGlobalDataFloat, 3: getGlobalDataDouble,
                 4: getGlobalDataVec2, 5: getGlobalDataVec3, 6: getGlobalDataVec4,
                 7: getGlobalDataInt2, 8: getGlobalDataInt3, 9: getGlobalDataInt4, 10: getGlobalDataString}
    if dtype in _dispatch:
        return _dispatch[dtype](context, label)
    raise ValueError(f"Unknown global data type code: {dtype}")


# ==================== Primitive Data Statistics & Filtering ====================

_PRIMITIVE_DATA_STATS_AVAILABLE = False
try:
    _uuid_arr_label = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.c_char_p]

    helios_lib.calculatePrimitiveDataMeanFloat.argtypes = _uuid_arr_label
    helios_lib.calculatePrimitiveDataMeanFloat.restype = ctypes.c_float
    helios_lib.calculatePrimitiveDataMeanFloat.errcheck = _check_error
    helios_lib.calculatePrimitiveDataMeanDouble.argtypes = _uuid_arr_label
    helios_lib.calculatePrimitiveDataMeanDouble.restype = ctypes.c_double
    helios_lib.calculatePrimitiveDataMeanDouble.errcheck = _check_error
    helios_lib.calculatePrimitiveDataMeanVec2.argtypes = _uuid_arr_label + [ctypes.POINTER(ctypes.c_float)]*2
    helios_lib.calculatePrimitiveDataMeanVec2.restype = None
    helios_lib.calculatePrimitiveDataMeanVec2.errcheck = _check_error
    helios_lib.calculatePrimitiveDataMeanVec3.argtypes = _uuid_arr_label + [ctypes.POINTER(ctypes.c_float)]*3
    helios_lib.calculatePrimitiveDataMeanVec3.restype = None
    helios_lib.calculatePrimitiveDataMeanVec3.errcheck = _check_error
    helios_lib.calculatePrimitiveDataMeanVec4.argtypes = _uuid_arr_label + [ctypes.POINTER(ctypes.c_float)]*4
    helios_lib.calculatePrimitiveDataMeanVec4.restype = None
    helios_lib.calculatePrimitiveDataMeanVec4.errcheck = _check_error

    helios_lib.calculatePrimitiveDataAreaWeightedMeanFloat.argtypes = _uuid_arr_label
    helios_lib.calculatePrimitiveDataAreaWeightedMeanFloat.restype = ctypes.c_float
    helios_lib.calculatePrimitiveDataAreaWeightedMeanFloat.errcheck = _check_error
    helios_lib.calculatePrimitiveDataAreaWeightedMeanDouble.argtypes = _uuid_arr_label
    helios_lib.calculatePrimitiveDataAreaWeightedMeanDouble.restype = ctypes.c_double
    helios_lib.calculatePrimitiveDataAreaWeightedMeanDouble.errcheck = _check_error

    helios_lib.calculatePrimitiveDataSumFloat.argtypes = _uuid_arr_label
    helios_lib.calculatePrimitiveDataSumFloat.restype = ctypes.c_float
    helios_lib.calculatePrimitiveDataSumFloat.errcheck = _check_error
    helios_lib.calculatePrimitiveDataSumDouble.argtypes = _uuid_arr_label
    helios_lib.calculatePrimitiveDataSumDouble.restype = ctypes.c_double
    helios_lib.calculatePrimitiveDataSumDouble.errcheck = _check_error

    helios_lib.calculatePrimitiveDataAreaWeightedSumFloat.argtypes = _uuid_arr_label
    helios_lib.calculatePrimitiveDataAreaWeightedSumFloat.restype = ctypes.c_float
    helios_lib.calculatePrimitiveDataAreaWeightedSumFloat.errcheck = _check_error
    helios_lib.calculatePrimitiveDataAreaWeightedSumDouble.argtypes = _uuid_arr_label
    helios_lib.calculatePrimitiveDataAreaWeightedSumDouble.restype = ctypes.c_double
    helios_lib.calculatePrimitiveDataAreaWeightedSumDouble.errcheck = _check_error

    helios_lib.scalePrimitiveDataWithUUIDs.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.c_char_p, ctypes.c_float]
    helios_lib.scalePrimitiveDataWithUUIDs.restype = None
    helios_lib.scalePrimitiveDataWithUUIDs.errcheck = _check_error
    helios_lib.scalePrimitiveDataAll.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_float]
    helios_lib.scalePrimitiveDataAll.restype = None
    helios_lib.scalePrimitiveDataAll.errcheck = _check_error

    helios_lib.incrementPrimitiveDataInt.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.c_char_p, ctypes.c_int]
    helios_lib.incrementPrimitiveDataInt.restype = None
    helios_lib.incrementPrimitiveDataInt.errcheck = _check_error
    helios_lib.incrementPrimitiveDataFloat.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.c_char_p, ctypes.c_float]
    helios_lib.incrementPrimitiveDataFloat.restype = None
    helios_lib.incrementPrimitiveDataFloat.errcheck = _check_error

    helios_lib.aggregatePrimitiveDataSum.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_char_p), ctypes.c_uint, ctypes.c_char_p]
    helios_lib.aggregatePrimitiveDataSum.restype = None
    helios_lib.aggregatePrimitiveDataSum.errcheck = _check_error
    helios_lib.aggregatePrimitiveDataProduct.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_char_p), ctypes.c_uint, ctypes.c_char_p]
    helios_lib.aggregatePrimitiveDataProduct.restype = None
    helios_lib.aggregatePrimitiveDataProduct.errcheck = _check_error

    helios_lib.sumPrimitiveSurfaceArea.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint]
    helios_lib.sumPrimitiveSurfaceArea.restype = ctypes.c_float
    helios_lib.sumPrimitiveSurfaceArea.errcheck = _check_error

    helios_lib.filterPrimitivesByDataFloat.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.c_char_p, ctypes.c_float, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.filterPrimitivesByDataFloat.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.filterPrimitivesByDataFloat.errcheck = _check_error
    helios_lib.filterPrimitivesByDataInt.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.filterPrimitivesByDataInt.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.filterPrimitivesByDataInt.errcheck = _check_error
    helios_lib.filterPrimitivesByDataString.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.filterPrimitivesByDataString.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.filterPrimitivesByDataString.errcheck = _check_error

    _PRIMITIVE_DATA_STATS_AVAILABLE = True
except AttributeError:
    _PRIMITIVE_DATA_STATS_AVAILABLE = False

_NOT_AVAILABLE_STATS_MSG = (
    "Primitive data statistics functions not available in current Helios library. "
    "Rebuild PyHelios with updated C++ wrapper implementation."
)


def _make_uuid_array(uuids):
    return (ctypes.c_uint * len(uuids))(*uuids) if not isinstance(uuids, ctypes.Array) else uuids


def calculatePrimitiveDataMeanFloatWrapper(context, uuids: List[int], label: str) -> float:
    if not _PRIMITIVE_DATA_STATS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_STATS_MSG)
    arr = (ctypes.c_uint * len(uuids))(*uuids)
    return helios_lib.calculatePrimitiveDataMeanFloat(context, arr, len(uuids), label.encode('utf-8'))

def calculatePrimitiveDataMeanDoubleWrapper(context, uuids: List[int], label: str) -> float:
    if not _PRIMITIVE_DATA_STATS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_STATS_MSG)
    arr = (ctypes.c_uint * len(uuids))(*uuids)
    return helios_lib.calculatePrimitiveDataMeanDouble(context, arr, len(uuids), label.encode('utf-8'))

def calculatePrimitiveDataMeanVec3Wrapper(context, uuids: List[int], label: str) -> List[float]:
    if not _PRIMITIVE_DATA_STATS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_STATS_MSG)
    arr = (ctypes.c_uint * len(uuids))(*uuids)
    x, y, z = ctypes.c_float(), ctypes.c_float(), ctypes.c_float()
    helios_lib.calculatePrimitiveDataMeanVec3(context, arr, len(uuids), label.encode('utf-8'), ctypes.byref(x), ctypes.byref(y), ctypes.byref(z))
    return [x.value, y.value, z.value]

def calculatePrimitiveDataAreaWeightedMeanFloatWrapper(context, uuids: List[int], label: str) -> float:
    if not _PRIMITIVE_DATA_STATS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_STATS_MSG)
    arr = (ctypes.c_uint * len(uuids))(*uuids)
    return helios_lib.calculatePrimitiveDataAreaWeightedMeanFloat(context, arr, len(uuids), label.encode('utf-8'))

def calculatePrimitiveDataSumFloatWrapper(context, uuids: List[int], label: str) -> float:
    if not _PRIMITIVE_DATA_STATS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_STATS_MSG)
    arr = (ctypes.c_uint * len(uuids))(*uuids)
    return helios_lib.calculatePrimitiveDataSumFloat(context, arr, len(uuids), label.encode('utf-8'))

def calculatePrimitiveDataSumDoubleWrapper(context, uuids: List[int], label: str) -> float:
    if not _PRIMITIVE_DATA_STATS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_STATS_MSG)
    arr = (ctypes.c_uint * len(uuids))(*uuids)
    return helios_lib.calculatePrimitiveDataSumDouble(context, arr, len(uuids), label.encode('utf-8'))

def calculatePrimitiveDataAreaWeightedSumFloatWrapper(context, uuids: List[int], label: str) -> float:
    if not _PRIMITIVE_DATA_STATS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_STATS_MSG)
    arr = (ctypes.c_uint * len(uuids))(*uuids)
    return helios_lib.calculatePrimitiveDataAreaWeightedSumFloat(context, arr, len(uuids), label.encode('utf-8'))

def scalePrimitiveDataWithUUIDsWrapper(context, uuids: List[int], label: str, factor: float):
    if not _PRIMITIVE_DATA_STATS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_STATS_MSG)
    arr = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.scalePrimitiveDataWithUUIDs(context, arr, len(uuids), label.encode('utf-8'), factor)

def scalePrimitiveDataAllWrapper(context, label: str, factor: float):
    if not _PRIMITIVE_DATA_STATS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_STATS_MSG)
    helios_lib.scalePrimitiveDataAll(context, label.encode('utf-8'), factor)

def incrementPrimitiveDataIntWrapper(context, uuids: List[int], label: str, increment: int):
    if not _PRIMITIVE_DATA_STATS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_STATS_MSG)
    arr = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.incrementPrimitiveDataInt(context, arr, len(uuids), label.encode('utf-8'), increment)

def incrementPrimitiveDataFloatWrapper(context, uuids: List[int], label: str, increment: float):
    if not _PRIMITIVE_DATA_STATS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_STATS_MSG)
    arr = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.incrementPrimitiveDataFloat(context, arr, len(uuids), label.encode('utf-8'), increment)

def aggregatePrimitiveDataSumWrapper(context, uuids: List[int], labels: List[str], result_label: str):
    if not _PRIMITIVE_DATA_STATS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_STATS_MSG)
    arr = (ctypes.c_uint * len(uuids))(*uuids)
    encoded_labels = [l.encode('utf-8') for l in labels]
    labels_arr = (ctypes.c_char_p * len(labels))(*encoded_labels)
    helios_lib.aggregatePrimitiveDataSum(context, arr, len(uuids), labels_arr, len(labels), result_label.encode('utf-8'))

def aggregatePrimitiveDataProductWrapper(context, uuids: List[int], labels: List[str], result_label: str):
    if not _PRIMITIVE_DATA_STATS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_STATS_MSG)
    arr = (ctypes.c_uint * len(uuids))(*uuids)
    encoded_labels = [l.encode('utf-8') for l in labels]
    labels_arr = (ctypes.c_char_p * len(labels))(*encoded_labels)
    helios_lib.aggregatePrimitiveDataProduct(context, arr, len(uuids), labels_arr, len(labels), result_label.encode('utf-8'))

def sumPrimitiveSurfaceAreaWrapper(context, uuids: List[int]) -> float:
    if not _PRIMITIVE_DATA_STATS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_STATS_MSG)
    arr = (ctypes.c_uint * len(uuids))(*uuids)
    return helios_lib.sumPrimitiveSurfaceArea(context, arr, len(uuids))

def filterPrimitivesByDataFloatWrapper(context, uuids: List[int], label: str, value: float, comparator: str) -> List[int]:
    if not _PRIMITIVE_DATA_STATS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_STATS_MSG)
    arr = (ctypes.c_uint * len(uuids))(*uuids)
    result_count = ctypes.c_uint()
    ptr = helios_lib.filterPrimitivesByDataFloat(context, arr, len(uuids), label.encode('utf-8'), value, comparator.encode('utf-8'), ctypes.byref(result_count))
    if result_count.value == 0 or not ptr: return []
    return [ptr[i] for i in range(result_count.value)]

def filterPrimitivesByDataIntWrapper(context, uuids: List[int], label: str, value: int, comparator: str) -> List[int]:
    if not _PRIMITIVE_DATA_STATS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_STATS_MSG)
    arr = (ctypes.c_uint * len(uuids))(*uuids)
    result_count = ctypes.c_uint()
    ptr = helios_lib.filterPrimitivesByDataInt(context, arr, len(uuids), label.encode('utf-8'), value, comparator.encode('utf-8'), ctypes.byref(result_count))
    if result_count.value == 0 or not ptr: return []
    return [ptr[i] for i in range(result_count.value)]

def filterPrimitivesByDataStringWrapper(context, uuids: List[int], label: str, value: str) -> List[int]:
    if not _PRIMITIVE_DATA_STATS_AVAILABLE: raise NotImplementedError(_NOT_AVAILABLE_STATS_MSG)
    arr = (ctypes.c_uint * len(uuids))(*uuids)
    result_count = ctypes.c_uint()
    ptr = helios_lib.filterPrimitivesByDataString(context, arr, len(uuids), label.encode('utf-8'), value.encode('utf-8'), ctypes.byref(result_count))
    if result_count.value == 0 or not ptr: return []
    return [ptr[i] for i in range(result_count.value)]

# ==================== Object / Primitive Geometry Queries, Color Mutation, Crop Domain ====================
# These wrappers were added together; availability of the whole group is controlled by a single flag
# since all require a single fresh native build.
_CONTEXT_GEOMETRY_EXTENSIONS_AVAILABLE = True
_NOT_AVAILABLE_CTX_EXT_MSG = (
    "PyHelios extended Context geometry queries are not available in the loaded native library. "
    "Rebuild with: build_scripts/build_helios --clean"
)

try:
    # Object geometry
    helios_lib.getObjectType.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.getObjectType.restype = ctypes.c_uint
    helios_lib.getObjectType.errcheck = _check_error

    helios_lib.getObjectCenter.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.getObjectCenter.restype = ctypes.POINTER(ctypes.c_float)
    helios_lib.getObjectCenter.errcheck = _check_error

    helios_lib.getObjectBoundingBox.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.getObjectBoundingBox.restype = None
    helios_lib.getObjectBoundingBox.errcheck = _check_error

    helios_lib.getObjectBoundingBox_batch.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.getObjectBoundingBox_batch.restype = None
    helios_lib.getObjectBoundingBox_batch.errcheck = _check_error

    helios_lib.getObjectPrimitiveUUIDs_batch.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getObjectPrimitiveUUIDs_batch.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.getObjectPrimitiveUUIDs_batch.errcheck = _check_error

    helios_lib.getObjectPrimitiveUUIDs_nested.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getObjectPrimitiveUUIDs_nested.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.getObjectPrimitiveUUIDs_nested.errcheck = _check_error

    # Tile
    helios_lib.getTileObjectAreaRatio.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.getTileObjectAreaRatio.restype = ctypes.c_float
    helios_lib.getTileObjectAreaRatio.errcheck = _check_error

    helios_lib.getTileObjectAreaRatio_batch.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getTileObjectAreaRatio_batch.restype = ctypes.POINTER(ctypes.c_float)
    helios_lib.getTileObjectAreaRatio_batch.errcheck = _check_error

    for _fn in ("getTileObjectCenter", "getTileObjectSize", "getTileObjectNormal"):
        getattr(helios_lib, _fn).argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
        getattr(helios_lib, _fn).restype = ctypes.POINTER(ctypes.c_float)
        getattr(helios_lib, _fn).errcheck = _check_error

    helios_lib.getTileObjectSubdivisionCount.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.getTileObjectSubdivisionCount.restype = ctypes.POINTER(ctypes.c_int)
    helios_lib.getTileObjectSubdivisionCount.errcheck = _check_error

    for _fn in ("getTileObjectTextureUV", "getTileObjectVertices"):
        getattr(helios_lib, _fn).argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
        getattr(helios_lib, _fn).restype = ctypes.POINTER(ctypes.c_float)
        getattr(helios_lib, _fn).errcheck = _check_error

    # Sphere
    for _fn in ("getSphereObjectCenter", "getSphereObjectRadius"):
        getattr(helios_lib, _fn).argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
        getattr(helios_lib, _fn).restype = ctypes.POINTER(ctypes.c_float)
        getattr(helios_lib, _fn).errcheck = _check_error

    helios_lib.getSphereObjectSubdivisionCount.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.getSphereObjectSubdivisionCount.restype = ctypes.c_uint
    helios_lib.getSphereObjectSubdivisionCount.errcheck = _check_error

    helios_lib.getSphereObjectVolume.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.getSphereObjectVolume.restype = ctypes.c_float
    helios_lib.getSphereObjectVolume.errcheck = _check_error

    # Box
    for _fn in ("getBoxObjectCenter", "getBoxObjectSize"):
        getattr(helios_lib, _fn).argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
        getattr(helios_lib, _fn).restype = ctypes.POINTER(ctypes.c_float)
        getattr(helios_lib, _fn).errcheck = _check_error

    helios_lib.getBoxObjectSubdivisionCount.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.getBoxObjectSubdivisionCount.restype = ctypes.POINTER(ctypes.c_int)
    helios_lib.getBoxObjectSubdivisionCount.errcheck = _check_error

    helios_lib.getBoxObjectVolume.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.getBoxObjectVolume.restype = ctypes.c_float
    helios_lib.getBoxObjectVolume.errcheck = _check_error

    # Disk
    for _fn in ("getDiskObjectCenter", "getDiskObjectSize"):
        getattr(helios_lib, _fn).argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
        getattr(helios_lib, _fn).restype = ctypes.POINTER(ctypes.c_float)
        getattr(helios_lib, _fn).errcheck = _check_error

    helios_lib.getDiskObjectSubdivisionCount.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.getDiskObjectSubdivisionCount.restype = ctypes.c_uint
    helios_lib.getDiskObjectSubdivisionCount.errcheck = _check_error

    # Tube
    for _fn in ("getTubeObjectSubdivisionCount", "getTubeObjectNodeCount"):
        getattr(helios_lib, _fn).argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
        getattr(helios_lib, _fn).restype = ctypes.c_uint
        getattr(helios_lib, _fn).errcheck = _check_error

    for _fn in ("getTubeObjectNodes", "getTubeObjectNodeRadii", "getTubeObjectNodeColors"):
        getattr(helios_lib, _fn).argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
        getattr(helios_lib, _fn).restype = ctypes.POINTER(ctypes.c_float)
        getattr(helios_lib, _fn).errcheck = _check_error

    helios_lib.getTubeObjectVolume.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.getTubeObjectVolume.restype = ctypes.c_float
    helios_lib.getTubeObjectVolume.errcheck = _check_error

    helios_lib.getTubeObjectSegmentVolume.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_uint]
    helios_lib.getTubeObjectSegmentVolume.restype = ctypes.c_float
    helios_lib.getTubeObjectSegmentVolume.errcheck = _check_error

    # Cone
    helios_lib.getConeObjectSubdivisionCount.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.getConeObjectSubdivisionCount.restype = ctypes.c_uint
    helios_lib.getConeObjectSubdivisionCount.errcheck = _check_error

    for _fn in ("getConeObjectNodes", "getConeObjectNodeRadii"):
        getattr(helios_lib, _fn).argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
        getattr(helios_lib, _fn).restype = ctypes.POINTER(ctypes.c_float)
        getattr(helios_lib, _fn).errcheck = _check_error

    helios_lib.getConeObjectNode.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_int]
    helios_lib.getConeObjectNode.restype = ctypes.POINTER(ctypes.c_float)
    helios_lib.getConeObjectNode.errcheck = _check_error

    helios_lib.getConeObjectNodeRadius.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_int]
    helios_lib.getConeObjectNodeRadius.restype = ctypes.c_float
    helios_lib.getConeObjectNodeRadius.errcheck = _check_error

    helios_lib.getConeObjectAxisUnitVector.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.getConeObjectAxisUnitVector.restype = ctypes.POINTER(ctypes.c_float)
    helios_lib.getConeObjectAxisUnitVector.errcheck = _check_error

    for _fn in ("getConeObjectLength", "getConeObjectVolume"):
        getattr(helios_lib, _fn).argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
        getattr(helios_lib, _fn).restype = ctypes.c_float
        getattr(helios_lib, _fn).errcheck = _check_error

    # Primitive geometry
    for _fn in ("getPatchCenter", "getVoxelCenter", "getVoxelSize"):
        getattr(helios_lib, _fn).argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
        getattr(helios_lib, _fn).restype = ctypes.POINTER(ctypes.c_float)
        getattr(helios_lib, _fn).errcheck = _check_error

    helios_lib.getPatchSize.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.getPatchSize.restype = ctypes.POINTER(ctypes.c_float)
    helios_lib.getPatchSize.errcheck = _check_error

    helios_lib.getTriangleVertex.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_uint]
    helios_lib.getTriangleVertex.restype = ctypes.POINTER(ctypes.c_float)
    helios_lib.getTriangleVertex.errcheck = _check_error

    for _fn in ("getPatchCount", "getTriangleCount"):
        getattr(helios_lib, _fn).argtypes = [ctypes.POINTER(UContext), ctypes.c_bool]
        getattr(helios_lib, _fn).restype = ctypes.c_uint
        getattr(helios_lib, _fn).errcheck = _check_error

    helios_lib.getPrimitiveBoundingBox.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.getPrimitiveBoundingBox.restype = None
    helios_lib.getPrimitiveBoundingBox.errcheck = _check_error

    helios_lib.getPrimitiveBoundingBox_batch.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.getPrimitiveBoundingBox_batch.restype = None
    helios_lib.getPrimitiveBoundingBox_batch.errcheck = _check_error

    # setPrimitiveColor
    helios_lib.setPrimitiveColor.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.setPrimitiveColor.restype = None
    helios_lib.setPrimitiveColor.errcheck = _check_error

    helios_lib.setPrimitiveColor_batch.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.setPrimitiveColor_batch.restype = None
    helios_lib.setPrimitiveColor_batch.errcheck = _check_error

    helios_lib.setPrimitiveColorRGBA.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.setPrimitiveColorRGBA.restype = None
    helios_lib.setPrimitiveColorRGBA.errcheck = _check_error

    helios_lib.setPrimitiveColorRGBA_batch.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.setPrimitiveColorRGBA_batch.restype = None
    helios_lib.setPrimitiveColorRGBA_batch.errcheck = _check_error

    # Primitive data introspection
    helios_lib.clearPrimitiveDataByLabel.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p]
    helios_lib.clearPrimitiveDataByLabel.restype = None
    helios_lib.clearPrimitiveDataByLabel.errcheck = _check_error

    helios_lib.clearPrimitiveDataByLabel_batch.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.c_char_p]
    helios_lib.clearPrimitiveDataByLabel_batch.restype = None
    helios_lib.clearPrimitiveDataByLabel_batch.errcheck = _check_error

    helios_lib.listPrimitiveData.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.listPrimitiveData.restype = ctypes.POINTER(ctypes.c_char_p)
    helios_lib.listPrimitiveData.errcheck = _check_error

    # Crop domain
    for _fn in ("cropDomainX", "cropDomainY", "cropDomainZ"):
        getattr(helios_lib, _fn).argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float)]
        getattr(helios_lib, _fn).restype = None
        getattr(helios_lib, _fn).errcheck = _check_error

    helios_lib.cropDomainXYZ.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.cropDomainXYZ.restype = None
    helios_lib.cropDomainXYZ.errcheck = _check_error

    helios_lib.cropDomainByUUIDs.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.cropDomainByUUIDs.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.cropDomainByUUIDs.errcheck = _check_error

except AttributeError:
    _CONTEXT_GEOMETRY_EXTENSIONS_AVAILABLE = False


def _require_ctx_ext():
    if not _CONTEXT_GEOMETRY_EXTENSIONS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_CTX_EXT_MSG)


def _float3_from_ptr(ptr):
    return (float(ptr[0]), float(ptr[1]), float(ptr[2]))


def _float2_from_ptr(ptr):
    return (float(ptr[0]), float(ptr[1]))


def _int3_from_ptr(ptr):
    return (int(ptr[0]), int(ptr[1]), int(ptr[2]))


def _int2_from_ptr(ptr):
    return (int(ptr[0]), int(ptr[1]))


def getObjectTypeWrapper(context, objID: int) -> int:
    _require_ctx_ext()
    return int(helios_lib.getObjectType(context, objID))


def getObjectCenterWrapper(context, objID: int):
    _require_ctx_ext()
    ptr = helios_lib.getObjectCenter(context, objID)
    return _float3_from_ptr(ptr)


def getObjectBoundingBoxWrapper(context, objID: int):
    _require_ctx_ext()
    mn = (ctypes.c_float * 3)()
    mx = (ctypes.c_float * 3)()
    helios_lib.getObjectBoundingBox(context, objID, mn, mx)
    return ((mn[0], mn[1], mn[2]), (mx[0], mx[1], mx[2]))


def getObjectBoundingBoxBatchWrapper(context, objIDs: List[int]):
    _require_ctx_ext()
    arr = (ctypes.c_uint * len(objIDs))(*objIDs)
    mn = (ctypes.c_float * 3)()
    mx = (ctypes.c_float * 3)()
    helios_lib.getObjectBoundingBox_batch(context, arr, len(objIDs), mn, mx)
    return ((mn[0], mn[1], mn[2]), (mx[0], mx[1], mx[2]))


def getObjectPrimitiveUUIDsBatchWrapper(context, objIDs: List[int]) -> List[int]:
    _require_ctx_ext()
    arr = (ctypes.c_uint * len(objIDs))(*objIDs)
    size = ctypes.c_uint()
    ptr = helios_lib.getObjectPrimitiveUUIDs_batch(context, arr, len(objIDs), ctypes.byref(size))
    if size.value == 0 or not ptr:
        return []
    return [int(ptr[i]) for i in range(size.value)]


def getObjectPrimitiveUUIDsNestedWrapper(context, nested: List[List[int]]) -> List[int]:
    _require_ctx_ext()
    flat = [u for inner in nested for u in inner]
    inner_counts = [len(inner) for inner in nested]
    flat_arr = (ctypes.c_uint * max(len(flat), 1))(*flat)
    counts_arr = (ctypes.c_uint * max(len(inner_counts), 1))(*inner_counts)
    size = ctypes.c_uint()
    ptr = helios_lib.getObjectPrimitiveUUIDs_nested(context, flat_arr, counts_arr, len(inner_counts), ctypes.byref(size))
    if size.value == 0 or not ptr:
        return []
    return [int(ptr[i]) for i in range(size.value)]


# Tile
def getTileObjectAreaRatioWrapper(context, objID: int) -> float:
    _require_ctx_ext()
    return float(helios_lib.getTileObjectAreaRatio(context, objID))


def getTileObjectAreaRatioBatchWrapper(context, objIDs: List[int]) -> List[float]:
    _require_ctx_ext()
    arr = (ctypes.c_uint * len(objIDs))(*objIDs)
    size = ctypes.c_uint()
    ptr = helios_lib.getTileObjectAreaRatio_batch(context, arr, len(objIDs), ctypes.byref(size))
    if size.value == 0 or not ptr:
        return []
    return [float(ptr[i]) for i in range(size.value)]


def getTileObjectCenterWrapper(context, objID: int):
    _require_ctx_ext()
    return _float3_from_ptr(helios_lib.getTileObjectCenter(context, objID))


def getTileObjectSizeWrapper(context, objID: int):
    _require_ctx_ext()
    return _float2_from_ptr(helios_lib.getTileObjectSize(context, objID))


def getTileObjectSubdivisionCountWrapper(context, objID: int):
    _require_ctx_ext()
    return _int2_from_ptr(helios_lib.getTileObjectSubdivisionCount(context, objID))


def getTileObjectNormalWrapper(context, objID: int):
    _require_ctx_ext()
    return _float3_from_ptr(helios_lib.getTileObjectNormal(context, objID))


def _pull_float_array(ptr, size):
    if size == 0 or not ptr:
        return []
    arr = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_float * size)).contents
    return [float(x) for x in arr]


def getTileObjectTextureUVWrapper(context, objID: int):
    _require_ctx_ext()
    size = ctypes.c_uint()
    ptr = helios_lib.getTileObjectTextureUV(context, objID, ctypes.byref(size))
    vals = _pull_float_array(ptr, size.value)
    return [(vals[i], vals[i+1]) for i in range(0, len(vals), 2)]


def getTileObjectVerticesWrapper(context, objID: int):
    _require_ctx_ext()
    size = ctypes.c_uint()
    ptr = helios_lib.getTileObjectVertices(context, objID, ctypes.byref(size))
    vals = _pull_float_array(ptr, size.value)
    return [(vals[i], vals[i+1], vals[i+2]) for i in range(0, len(vals), 3)]


# Sphere
def getSphereObjectCenterWrapper(context, objID: int):
    _require_ctx_ext()
    return _float3_from_ptr(helios_lib.getSphereObjectCenter(context, objID))


def getSphereObjectRadiusWrapper(context, objID: int):
    _require_ctx_ext()
    return _float3_from_ptr(helios_lib.getSphereObjectRadius(context, objID))


def getSphereObjectSubdivisionCountWrapper(context, objID: int) -> int:
    _require_ctx_ext()
    return int(helios_lib.getSphereObjectSubdivisionCount(context, objID))


def getSphereObjectVolumeWrapper(context, objID: int) -> float:
    _require_ctx_ext()
    return float(helios_lib.getSphereObjectVolume(context, objID))


# Box
def getBoxObjectCenterWrapper(context, objID: int):
    _require_ctx_ext()
    return _float3_from_ptr(helios_lib.getBoxObjectCenter(context, objID))


def getBoxObjectSizeWrapper(context, objID: int):
    _require_ctx_ext()
    return _float3_from_ptr(helios_lib.getBoxObjectSize(context, objID))


def getBoxObjectSubdivisionCountWrapper(context, objID: int):
    _require_ctx_ext()
    return _int3_from_ptr(helios_lib.getBoxObjectSubdivisionCount(context, objID))


def getBoxObjectVolumeWrapper(context, objID: int) -> float:
    _require_ctx_ext()
    return float(helios_lib.getBoxObjectVolume(context, objID))


# Disk
def getDiskObjectCenterWrapper(context, objID: int):
    _require_ctx_ext()
    return _float3_from_ptr(helios_lib.getDiskObjectCenter(context, objID))


def getDiskObjectSizeWrapper(context, objID: int):
    _require_ctx_ext()
    return _float2_from_ptr(helios_lib.getDiskObjectSize(context, objID))


def getDiskObjectSubdivisionCountWrapper(context, objID: int) -> int:
    _require_ctx_ext()
    return int(helios_lib.getDiskObjectSubdivisionCount(context, objID))


# Tube
def getTubeObjectSubdivisionCountWrapper(context, objID: int) -> int:
    _require_ctx_ext()
    return int(helios_lib.getTubeObjectSubdivisionCount(context, objID))


def getTubeObjectNodeCountWrapper(context, objID: int) -> int:
    _require_ctx_ext()
    return int(helios_lib.getTubeObjectNodeCount(context, objID))


def getTubeObjectNodesWrapper(context, objID: int):
    _require_ctx_ext()
    size = ctypes.c_uint()
    ptr = helios_lib.getTubeObjectNodes(context, objID, ctypes.byref(size))
    vals = _pull_float_array(ptr, size.value)
    return [(vals[i], vals[i+1], vals[i+2]) for i in range(0, len(vals), 3)]


def getTubeObjectNodeRadiiWrapper(context, objID: int) -> List[float]:
    _require_ctx_ext()
    size = ctypes.c_uint()
    ptr = helios_lib.getTubeObjectNodeRadii(context, objID, ctypes.byref(size))
    return _pull_float_array(ptr, size.value)


def getTubeObjectNodeColorsWrapper(context, objID: int):
    _require_ctx_ext()
    size = ctypes.c_uint()
    ptr = helios_lib.getTubeObjectNodeColors(context, objID, ctypes.byref(size))
    vals = _pull_float_array(ptr, size.value)
    return [(vals[i], vals[i+1], vals[i+2]) for i in range(0, len(vals), 3)]


def getTubeObjectVolumeWrapper(context, objID: int) -> float:
    _require_ctx_ext()
    return float(helios_lib.getTubeObjectVolume(context, objID))


def getTubeObjectSegmentVolumeWrapper(context, objID: int, segment_index: int) -> float:
    _require_ctx_ext()
    return float(helios_lib.getTubeObjectSegmentVolume(context, objID, segment_index))


# Cone
def getConeObjectSubdivisionCountWrapper(context, objID: int) -> int:
    _require_ctx_ext()
    return int(helios_lib.getConeObjectSubdivisionCount(context, objID))


def getConeObjectNodesWrapper(context, objID: int):
    _require_ctx_ext()
    size = ctypes.c_uint()
    ptr = helios_lib.getConeObjectNodes(context, objID, ctypes.byref(size))
    vals = _pull_float_array(ptr, size.value)
    return [(vals[i], vals[i+1], vals[i+2]) for i in range(0, len(vals), 3)]


def getConeObjectNodeRadiiWrapper(context, objID: int) -> List[float]:
    _require_ctx_ext()
    size = ctypes.c_uint()
    ptr = helios_lib.getConeObjectNodeRadii(context, objID, ctypes.byref(size))
    return _pull_float_array(ptr, size.value)


def getConeObjectNodeWrapper(context, objID: int, number: int):
    _require_ctx_ext()
    return _float3_from_ptr(helios_lib.getConeObjectNode(context, objID, number))


def getConeObjectNodeRadiusWrapper(context, objID: int, number: int) -> float:
    _require_ctx_ext()
    return float(helios_lib.getConeObjectNodeRadius(context, objID, number))


def getConeObjectAxisUnitVectorWrapper(context, objID: int):
    _require_ctx_ext()
    return _float3_from_ptr(helios_lib.getConeObjectAxisUnitVector(context, objID))


def getConeObjectLengthWrapper(context, objID: int) -> float:
    _require_ctx_ext()
    return float(helios_lib.getConeObjectLength(context, objID))


def getConeObjectVolumeWrapper(context, objID: int) -> float:
    _require_ctx_ext()
    return float(helios_lib.getConeObjectVolume(context, objID))


# Primitive geometry
def getPatchCenterWrapper(context, uuid: int):
    _require_ctx_ext()
    return _float3_from_ptr(helios_lib.getPatchCenter(context, uuid))


def getPatchSizeWrapper(context, uuid: int):
    _require_ctx_ext()
    return _float2_from_ptr(helios_lib.getPatchSize(context, uuid))


def getTriangleVertexWrapper(context, uuid: int, number: int):
    _require_ctx_ext()
    return _float3_from_ptr(helios_lib.getTriangleVertex(context, uuid, number))


def getVoxelCenterWrapper(context, uuid: int):
    _require_ctx_ext()
    return _float3_from_ptr(helios_lib.getVoxelCenter(context, uuid))


def getVoxelSizeWrapper(context, uuid: int):
    _require_ctx_ext()
    return _float3_from_ptr(helios_lib.getVoxelSize(context, uuid))


def getPatchCountWrapper(context, include_hidden: bool = True) -> int:
    _require_ctx_ext()
    return int(helios_lib.getPatchCount(context, bool(include_hidden)))


def getTriangleCountWrapper(context, include_hidden: bool = True) -> int:
    _require_ctx_ext()
    return int(helios_lib.getTriangleCount(context, bool(include_hidden)))


def getPrimitiveBoundingBoxWrapper(context, uuid: int):
    _require_ctx_ext()
    mn = (ctypes.c_float * 3)()
    mx = (ctypes.c_float * 3)()
    helios_lib.getPrimitiveBoundingBox(context, uuid, mn, mx)
    return ((mn[0], mn[1], mn[2]), (mx[0], mx[1], mx[2]))


def getPrimitiveBoundingBoxBatchWrapper(context, uuids: List[int]):
    _require_ctx_ext()
    arr = (ctypes.c_uint * len(uuids))(*uuids)
    mn = (ctypes.c_float * 3)()
    mx = (ctypes.c_float * 3)()
    helios_lib.getPrimitiveBoundingBox_batch(context, arr, len(uuids), mn, mx)
    return ((mn[0], mn[1], mn[2]), (mx[0], mx[1], mx[2]))


# setPrimitiveColor
def setPrimitiveColorWrapper(context, uuid: int, color_rgb: List[float]):
    _require_ctx_ext()
    arr = (ctypes.c_float * 3)(color_rgb[0], color_rgb[1], color_rgb[2])
    helios_lib.setPrimitiveColor(context, uuid, arr)


def setPrimitiveColorBatchWrapper(context, uuids: List[int], color_rgb: List[float]):
    _require_ctx_ext()
    arr = (ctypes.c_uint * len(uuids))(*uuids)
    color_arr = (ctypes.c_float * 3)(color_rgb[0], color_rgb[1], color_rgb[2])
    helios_lib.setPrimitiveColor_batch(context, arr, len(uuids), color_arr)


def setPrimitiveColorRGBAWrapper(context, uuid: int, color_rgba: List[float]):
    _require_ctx_ext()
    arr = (ctypes.c_float * 4)(color_rgba[0], color_rgba[1], color_rgba[2], color_rgba[3])
    helios_lib.setPrimitiveColorRGBA(context, uuid, arr)


def setPrimitiveColorRGBABatchWrapper(context, uuids: List[int], color_rgba: List[float]):
    _require_ctx_ext()
    arr = (ctypes.c_uint * len(uuids))(*uuids)
    color_arr = (ctypes.c_float * 4)(color_rgba[0], color_rgba[1], color_rgba[2], color_rgba[3])
    helios_lib.setPrimitiveColorRGBA_batch(context, arr, len(uuids), color_arr)


# Primitive data introspection
def clearPrimitiveDataByLabelWrapper(context, uuid: int, label: str):
    _require_ctx_ext()
    helios_lib.clearPrimitiveDataByLabel(context, uuid, label.encode('utf-8'))


def clearPrimitiveDataByLabelBatchWrapper(context, uuids: List[int], label: str):
    _require_ctx_ext()
    arr = (ctypes.c_uint * len(uuids))(*uuids)
    helios_lib.clearPrimitiveDataByLabel_batch(context, arr, len(uuids), label.encode('utf-8'))


def listPrimitiveDataWrapper(context, uuid: int) -> List[str]:
    _require_ctx_ext()
    count = ctypes.c_uint()
    ptr = helios_lib.listPrimitiveData(context, uuid, ctypes.byref(count))
    if count.value == 0 or not ptr:
        return []
    return [ptr[i].decode('utf-8') for i in range(count.value)]


# Crop domain
def cropDomainXWrapper(context, xbounds):
    _require_ctx_ext()
    arr = (ctypes.c_float * 2)(float(xbounds[0]), float(xbounds[1]))
    helios_lib.cropDomainX(context, arr)


def cropDomainYWrapper(context, ybounds):
    _require_ctx_ext()
    arr = (ctypes.c_float * 2)(float(ybounds[0]), float(ybounds[1]))
    helios_lib.cropDomainY(context, arr)


def cropDomainZWrapper(context, zbounds):
    _require_ctx_ext()
    arr = (ctypes.c_float * 2)(float(zbounds[0]), float(zbounds[1]))
    helios_lib.cropDomainZ(context, arr)


def cropDomainXYZWrapper(context, xbounds, ybounds, zbounds):
    _require_ctx_ext()
    x_arr = (ctypes.c_float * 2)(float(xbounds[0]), float(xbounds[1]))
    y_arr = (ctypes.c_float * 2)(float(ybounds[0]), float(ybounds[1]))
    z_arr = (ctypes.c_float * 2)(float(zbounds[0]), float(zbounds[1]))
    helios_lib.cropDomainXYZ(context, x_arr, y_arr, z_arr)


def cropDomainByUUIDsWrapper(context, uuids: List[int], xbounds, ybounds, zbounds) -> List[int]:
    _require_ctx_ext()
    uuid_arr = (ctypes.c_uint * max(len(uuids), 1))(*uuids)
    x_arr = (ctypes.c_float * 2)(float(xbounds[0]), float(xbounds[1]))
    y_arr = (ctypes.c_float * 2)(float(ybounds[0]), float(ybounds[1]))
    z_arr = (ctypes.c_float * 2)(float(zbounds[0]), float(zbounds[1]))
    out_size = ctypes.c_uint()
    ptr = helios_lib.cropDomainByUUIDs(context, uuid_arr, len(uuids), x_arr, y_arr, z_arr, ctypes.byref(out_size))
    if out_size.value == 0 or not ptr:
        return []
    return [int(ptr[i]) for i in range(out_size.value)]


# =============================================================================
# Scalar Getters / Setters & List-of-String Getters
# =============================================================================

_CONTEXT_SCALAR_API_AVAILABLE = True
_NOT_AVAILABLE_SCALAR_API_MSG = (
    "PyHelios scalar Context wrappers are not available in the loaded native library. "
    "Rebuild with: build_scripts/build_helios --clean"
)

try:
    # ---- Bool getters ----
    helios_lib.doesObjectExist.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.doesObjectExist.restype = ctypes.c_bool
    helios_lib.doesObjectExist.errcheck = _check_error

    helios_lib.doesObjectContainPrimitive.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_uint]
    helios_lib.doesObjectContainPrimitive.restype = ctypes.c_bool
    helios_lib.doesObjectContainPrimitive.errcheck = _check_error

    helios_lib.doesMaterialDataExist.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.doesMaterialDataExist.restype = ctypes.c_bool
    helios_lib.doesMaterialDataExist.errcheck = _check_error

    helios_lib.objectHasTexture.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.objectHasTexture.restype = ctypes.c_bool
    helios_lib.objectHasTexture.errcheck = _check_error

    helios_lib.isPrimitiveDirty.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.isPrimitiveDirty.restype = ctypes.c_bool
    helios_lib.isPrimitiveDirty.errcheck = _check_error

    helios_lib.isObjectDataValueCachingEnabled.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p]
    helios_lib.isObjectDataValueCachingEnabled.restype = ctypes.c_bool
    helios_lib.isObjectDataValueCachingEnabled.errcheck = _check_error

    helios_lib.isPrimitiveDataValueCachingEnabled.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p]
    helios_lib.isPrimitiveDataValueCachingEnabled.restype = ctypes.c_bool
    helios_lib.isPrimitiveDataValueCachingEnabled.errcheck = _check_error

    helios_lib.areObjectPrimitivesComplete.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.areObjectPrimitivesComplete.restype = ctypes.c_bool
    helios_lib.areObjectPrimitivesComplete.errcheck = _check_error

    # ---- Numeric scalar getters ----
    helios_lib.getJulianDate.argtypes = [ctypes.POINTER(UContext)]
    helios_lib.getJulianDate.restype = ctypes.c_int
    helios_lib.getJulianDate.errcheck = _check_error

    helios_lib.getMaterialCount.argtypes = [ctypes.POINTER(UContext)]
    helios_lib.getMaterialCount.restype = ctypes.c_uint
    helios_lib.getMaterialCount.errcheck = _check_error

    helios_lib.getObjectArea.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.getObjectArea.restype = ctypes.c_float
    helios_lib.getObjectArea.errcheck = _check_error

    helios_lib.getObjectPrimitiveCount.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.getObjectPrimitiveCount.restype = ctypes.c_uint
    helios_lib.getObjectPrimitiveCount.errcheck = _check_error

    helios_lib.getPolymeshObjectVolume.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.getPolymeshObjectVolume.restype = ctypes.c_float
    helios_lib.getPolymeshObjectVolume.errcheck = _check_error

    helios_lib.getMaterialIDFromLabel.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p]
    helios_lib.getMaterialIDFromLabel.restype = ctypes.c_uint
    helios_lib.getMaterialIDFromLabel.errcheck = _check_error

    helios_lib.getPrimitiveMaterialID.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.getPrimitiveMaterialID.restype = ctypes.c_uint
    helios_lib.getPrimitiveMaterialID.errcheck = _check_error

    helios_lib.getGlobalDataVersion.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p]
    helios_lib.getGlobalDataVersion.restype = ctypes.c_uint64
    helios_lib.getGlobalDataVersion.errcheck = _check_error

    helios_lib.getPrimitiveParentObjectID.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.getPrimitiveParentObjectID.restype = ctypes.c_uint
    helios_lib.getPrimitiveParentObjectID.errcheck = _check_error

    # ---- String returns (buffer pattern) ----
    helios_lib.getObjectTextureFile.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_int]
    helios_lib.getObjectTextureFile.restype = ctypes.c_int
    helios_lib.getObjectTextureFile.errcheck = _check_error

    # ---- List-of-string returns (count + index getter) ----
    helios_lib.listAllPrimitiveDataLabelsCount.argtypes = [ctypes.POINTER(UContext)]
    helios_lib.listAllPrimitiveDataLabelsCount.restype = ctypes.c_uint
    helios_lib.listAllPrimitiveDataLabelsCount.errcheck = _check_error

    helios_lib.listAllPrimitiveDataLabel.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_int]
    helios_lib.listAllPrimitiveDataLabel.restype = ctypes.c_int
    helios_lib.listAllPrimitiveDataLabel.errcheck = _check_error

    helios_lib.getLoadedXMLFileCount.argtypes = [ctypes.POINTER(UContext)]
    helios_lib.getLoadedXMLFileCount.restype = ctypes.c_uint
    helios_lib.getLoadedXMLFileCount.errcheck = _check_error

    helios_lib.getLoadedXMLFile.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_int]
    helios_lib.getLoadedXMLFile.restype = ctypes.c_int
    helios_lib.getLoadedXMLFile.errcheck = _check_error

    # ---- Simple actions ----
    helios_lib.printObjectInfo.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.printObjectInfo.restype = None
    helios_lib.printObjectInfo.errcheck = _check_error

    helios_lib.printPrimitiveInfo.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.printPrimitiveInfo.restype = None
    helios_lib.printPrimitiveInfo.errcheck = _check_error

    helios_lib.enablePrimitiveDataValueCaching.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p]
    helios_lib.enablePrimitiveDataValueCaching.restype = None
    helios_lib.enablePrimitiveDataValueCaching.errcheck = _check_error

    helios_lib.disablePrimitiveDataValueCaching.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p]
    helios_lib.disablePrimitiveDataValueCaching.restype = None
    helios_lib.disablePrimitiveDataValueCaching.errcheck = _check_error

    helios_lib.enableObjectDataValueCaching.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p]
    helios_lib.enableObjectDataValueCaching.restype = None
    helios_lib.enableObjectDataValueCaching.errcheck = _check_error

    helios_lib.disableObjectDataValueCaching.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p]
    helios_lib.disableObjectDataValueCaching.restype = None
    helios_lib.disableObjectDataValueCaching.errcheck = _check_error

    helios_lib.setObjectDataFromPrimitiveDataMean.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p]
    helios_lib.setObjectDataFromPrimitiveDataMean.restype = None
    helios_lib.setObjectDataFromPrimitiveDataMean.errcheck = _check_error

    helios_lib.renameMaterial.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.renameMaterial.restype = None
    helios_lib.renameMaterial.errcheck = _check_error

    helios_lib.renamePrimitiveData.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.renamePrimitiveData.restype = None
    helios_lib.renamePrimitiveData.errcheck = _check_error

    helios_lib.clearMaterialData.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.clearMaterialData.restype = None
    helios_lib.clearMaterialData.errcheck = _check_error

except AttributeError:
    _CONTEXT_SCALAR_API_AVAILABLE = False


def _require_ctx_scalar_api():
    if not _CONTEXT_SCALAR_API_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_SCALAR_API_MSG)


def _read_string_buffer(call_fn, *args, initial_size: int = 256) -> str:
    """Helper: call a C function that fills a char buffer; grow buffer if truncated.

    The C function is expected to take (..., char* buffer, int buffer_size) trailing
    parameters and return the number of bytes copied (excluding null terminator).
    """
    size = initial_size
    while True:
        buf = ctypes.create_string_buffer(size)
        copied = int(call_fn(*args, buf, size))
        # If copied == size - 1 the value may have been truncated; retry with a larger
        # buffer to be safe. Otherwise we have the full string.
        if copied < size - 1:
            return buf.value.decode('utf-8', errors='replace')
        size *= 2
        if size > 1 << 20:  # 1 MiB safety cap
            return buf.value.decode('utf-8', errors='replace')


# ---- Bool getters ----

def doesObjectExistWrapper(context, objID: int) -> bool:
    _require_ctx_scalar_api()
    return bool(helios_lib.doesObjectExist(context, int(objID)))


def doesObjectContainPrimitiveWrapper(context, objID: int, uuid: int) -> bool:
    _require_ctx_scalar_api()
    return bool(helios_lib.doesObjectContainPrimitive(context, int(objID), int(uuid)))


def doesMaterialDataExistWrapper(context, material_label: str, data_label: str) -> bool:
    _require_ctx_scalar_api()
    return bool(helios_lib.doesMaterialDataExist(context, material_label.encode('utf-8'), data_label.encode('utf-8')))


def objectHasTextureWrapper(context, objID: int) -> bool:
    _require_ctx_scalar_api()
    return bool(helios_lib.objectHasTexture(context, int(objID)))


def isPrimitiveDirtyWrapper(context, uuid: int) -> bool:
    _require_ctx_scalar_api()
    return bool(helios_lib.isPrimitiveDirty(context, int(uuid)))


def isObjectDataValueCachingEnabledWrapper(context, label: str) -> bool:
    _require_ctx_scalar_api()
    return bool(helios_lib.isObjectDataValueCachingEnabled(context, label.encode('utf-8')))


def isPrimitiveDataValueCachingEnabledWrapper(context, label: str) -> bool:
    _require_ctx_scalar_api()
    return bool(helios_lib.isPrimitiveDataValueCachingEnabled(context, label.encode('utf-8')))


def areObjectPrimitivesCompleteWrapper(context, objID: int) -> bool:
    _require_ctx_scalar_api()
    return bool(helios_lib.areObjectPrimitivesComplete(context, int(objID)))


# ---- Numeric scalar getters ----

def getJulianDateWrapper(context) -> int:
    _require_ctx_scalar_api()
    return int(helios_lib.getJulianDate(context))


def getMaterialCountWrapper(context) -> int:
    _require_ctx_scalar_api()
    return int(helios_lib.getMaterialCount(context))


def getObjectAreaWrapper(context, objID: int) -> float:
    _require_ctx_scalar_api()
    return float(helios_lib.getObjectArea(context, int(objID)))


def getObjectPrimitiveCountWrapper(context, objID: int) -> int:
    _require_ctx_scalar_api()
    return int(helios_lib.getObjectPrimitiveCount(context, int(objID)))


def getPolymeshObjectVolumeWrapper(context, objID: int) -> float:
    _require_ctx_scalar_api()
    return float(helios_lib.getPolymeshObjectVolume(context, int(objID)))


def getMaterialIDFromLabelWrapper(context, material_label: str) -> int:
    _require_ctx_scalar_api()
    return int(helios_lib.getMaterialIDFromLabel(context, material_label.encode('utf-8')))


def getPrimitiveMaterialIDWrapper(context, uuid: int) -> int:
    _require_ctx_scalar_api()
    return int(helios_lib.getPrimitiveMaterialID(context, int(uuid)))


def getGlobalDataVersionWrapper(context, label: str) -> int:
    _require_ctx_scalar_api()
    return int(helios_lib.getGlobalDataVersion(context, label.encode('utf-8')))


def getPrimitiveParentObjectIDWrapper(context, uuid: int) -> int:
    _require_ctx_scalar_api()
    return int(helios_lib.getPrimitiveParentObjectID(context, int(uuid)))


# ---- String returns ----

def getObjectTextureFileWrapper(context, objID: int) -> str:
    _require_ctx_scalar_api()
    return _read_string_buffer(helios_lib.getObjectTextureFile, context, int(objID))


# ---- List-of-string returns ----

def listAllPrimitiveDataLabelsWrapper(context) -> List[str]:
    # The C side caches the snapshot in a thread-local std::vector populated by the
    # *Count call; the per-index getter then reads from that cache. We materialize the
    # full list here in one call so callers never observe the intermediate cache.
    _require_ctx_scalar_api()
    count = int(helios_lib.listAllPrimitiveDataLabelsCount(context))
    return [
        _read_string_buffer(helios_lib.listAllPrimitiveDataLabel, context, i)
        for i in range(count)
    ]


def getLoadedXMLFilesWrapper(context) -> List[str]:
    # Same count+index pattern as listAllPrimitiveDataLabelsWrapper — see comment there.
    _require_ctx_scalar_api()
    count = int(helios_lib.getLoadedXMLFileCount(context))
    return [
        _read_string_buffer(helios_lib.getLoadedXMLFile, context, i)
        for i in range(count)
    ]


# ---- Simple actions ----

def printObjectInfoWrapper(context, objID: int) -> None:
    _require_ctx_scalar_api()
    helios_lib.printObjectInfo(context, int(objID))


def printPrimitiveInfoWrapper(context, uuid: int) -> None:
    _require_ctx_scalar_api()
    helios_lib.printPrimitiveInfo(context, int(uuid))


def enablePrimitiveDataValueCachingWrapper(context, label: str) -> None:
    _require_ctx_scalar_api()
    helios_lib.enablePrimitiveDataValueCaching(context, label.encode('utf-8'))


def disablePrimitiveDataValueCachingWrapper(context, label: str) -> None:
    _require_ctx_scalar_api()
    helios_lib.disablePrimitiveDataValueCaching(context, label.encode('utf-8'))


def enableObjectDataValueCachingWrapper(context, label: str) -> None:
    _require_ctx_scalar_api()
    helios_lib.enableObjectDataValueCaching(context, label.encode('utf-8'))


def disableObjectDataValueCachingWrapper(context, label: str) -> None:
    _require_ctx_scalar_api()
    helios_lib.disableObjectDataValueCaching(context, label.encode('utf-8'))


def setObjectDataFromPrimitiveDataMeanWrapper(context, objID: int, label: str) -> None:
    _require_ctx_scalar_api()
    helios_lib.setObjectDataFromPrimitiveDataMean(context, int(objID), label.encode('utf-8'))


def renameMaterialWrapper(context, old_label: str, new_label: str) -> None:
    _require_ctx_scalar_api()
    helios_lib.renameMaterial(context, old_label.encode('utf-8'), new_label.encode('utf-8'))


def renamePrimitiveDataWrapper(context, uuid: int, old_label: str, new_label: str) -> None:
    _require_ctx_scalar_api()
    helios_lib.renamePrimitiveData(context, int(uuid), old_label.encode('utf-8'), new_label.encode('utf-8'))


def clearMaterialDataWrapper(context, material_label: str, data_label: str) -> None:
    _require_ctx_scalar_api()
    helios_lib.clearMaterialData(context, material_label.encode('utf-8'), data_label.encode('utf-8'))


# =============================================================================
# Vector-return getters & geometry mutators
# =============================================================================

_CONTEXT_GEOMETRY_MUTATORS_AVAILABLE = True
_NOT_AVAILABLE_GEOMETRY_MUTATORS_MSG = (
    "PyHelios geometry-mutator Context wrappers (vector returns + geometry setters) are not "
    "available in the loaded native library. Rebuild with: build_scripts/build_helios --clean"
)

try:
    # ---- Vector<uint> returns ----
    helios_lib.getDeletedUUIDs.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getDeletedUUIDs.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.getDeletedUUIDs.errcheck = _check_error

    helios_lib.getDirtyUUIDs.argtypes = [ctypes.POINTER(UContext), ctypes.c_bool, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getDirtyUUIDs.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.getDirtyUUIDs.errcheck = _check_error

    helios_lib.getUniquePrimitiveParentObjectIDs.argtypes = [
        ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint,
        ctypes.c_bool, ctypes.POINTER(ctypes.c_uint)
    ]
    helios_lib.getUniquePrimitiveParentObjectIDs.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.getUniquePrimitiveParentObjectIDs.errcheck = _check_error

    # ---- Object normal / origin queries & setters ----
    helios_lib.getObjectAverageNormal.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.getObjectAverageNormal.restype = ctypes.POINTER(ctypes.c_float)
    helios_lib.getObjectAverageNormal.errcheck = _check_error

    helios_lib.setObjectAverageNormal.argtypes = [
        ctypes.POINTER(UContext), ctypes.c_uint,
        ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)
    ]
    helios_lib.setObjectAverageNormal.restype = None
    helios_lib.setObjectAverageNormal.errcheck = _check_error

    helios_lib.setObjectOrigin.argtypes = [
        ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)
    ]
    helios_lib.setObjectOrigin.restype = None
    helios_lib.setObjectOrigin.errcheck = _check_error

    # ---- Primitive azimuth / elevation setters ----
    helios_lib.setPrimitiveAzimuth.argtypes = [
        ctypes.POINTER(UContext), ctypes.c_uint,
        ctypes.POINTER(ctypes.c_float), ctypes.c_float
    ]
    helios_lib.setPrimitiveAzimuth.restype = None
    helios_lib.setPrimitiveAzimuth.errcheck = _check_error

    helios_lib.setPrimitiveElevation.argtypes = [
        ctypes.POINTER(UContext), ctypes.c_uint,
        ctypes.POINTER(ctypes.c_float), ctypes.c_float
    ]
    helios_lib.setPrimitiveElevation.restype = None
    helios_lib.setPrimitiveElevation.errcheck = _check_error

    # ---- Geometry mutators ----
    helios_lib.setTriangleVertices.argtypes = [
        ctypes.POINTER(UContext), ctypes.c_uint,
        ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)
    ]
    helios_lib.setTriangleVertices.restype = None
    helios_lib.setTriangleVertices.errcheck = _check_error

    helios_lib.setPrimitiveNormal.argtypes = [
        ctypes.POINTER(UContext), ctypes.c_uint,
        ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)
    ]
    helios_lib.setPrimitiveNormal.restype = None
    helios_lib.setPrimitiveNormal.errcheck = _check_error

    helios_lib.setPrimitiveNormalBatch.argtypes = [
        ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint,
        ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)
    ]
    helios_lib.setPrimitiveNormalBatch.restype = None
    helios_lib.setPrimitiveNormalBatch.errcheck = _check_error

    helios_lib.setPrimitiveParentObjectID.argtypes = [
        ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_uint
    ]
    helios_lib.setPrimitiveParentObjectID.restype = None
    helios_lib.setPrimitiveParentObjectID.errcheck = _check_error

    helios_lib.setPrimitiveParentObjectIDBatch.argtypes = [
        ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.c_uint
    ]
    helios_lib.setPrimitiveParentObjectIDBatch.restype = None
    helios_lib.setPrimitiveParentObjectIDBatch.errcheck = _check_error

except AttributeError:
    _CONTEXT_GEOMETRY_MUTATORS_AVAILABLE = False


def _require_ctx_geometry_mutators():
    if not _CONTEXT_GEOMETRY_MUTATORS_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_GEOMETRY_MUTATORS_MSG)


# ---- Vector<uint> returns ----

def getDeletedUUIDsWrapper(context) -> List[int]:
    _require_ctx_geometry_mutators()
    count = ctypes.c_uint()
    ptr = helios_lib.getDeletedUUIDs(context, ctypes.byref(count))
    if count.value == 0 or not ptr:
        return []
    return [int(ptr[i]) for i in range(count.value)]


def getDirtyUUIDsWrapper(context, include_deleted: bool = True) -> List[int]:
    _require_ctx_geometry_mutators()
    count = ctypes.c_uint()
    ptr = helios_lib.getDirtyUUIDs(context, bool(include_deleted), ctypes.byref(count))
    if count.value == 0 or not ptr:
        return []
    return [int(ptr[i]) for i in range(count.value)]


def getUniquePrimitiveParentObjectIDsWrapper(context, uuids: List[int], include_zero: bool = True) -> List[int]:
    _require_ctx_geometry_mutators()
    n = len(uuids)
    arr = (ctypes.c_uint * max(n, 1))(*uuids) if n > 0 else (ctypes.c_uint * 1)()
    out_count = ctypes.c_uint()
    ptr = helios_lib.getUniquePrimitiveParentObjectIDs(
        context, arr, n, bool(include_zero), ctypes.byref(out_count)
    )
    if out_count.value == 0 or not ptr:
        return []
    return [int(ptr[i]) for i in range(out_count.value)]


# ---- Object normal / origin ----

def getObjectAverageNormalWrapper(context, objID: int):
    _require_ctx_geometry_mutators()
    ptr = helios_lib.getObjectAverageNormal(context, int(objID))
    return (float(ptr[0]), float(ptr[1]), float(ptr[2]))


def setObjectAverageNormalWrapper(context, objID: int, origin, new_normal) -> None:
    _require_ctx_geometry_mutators()
    o = (ctypes.c_float * 3)(float(origin[0]), float(origin[1]), float(origin[2]))
    n = (ctypes.c_float * 3)(float(new_normal[0]), float(new_normal[1]), float(new_normal[2]))
    helios_lib.setObjectAverageNormal(context, int(objID), o, n)


def setObjectOriginWrapper(context, objID: int, origin) -> None:
    _require_ctx_geometry_mutators()
    o = (ctypes.c_float * 3)(float(origin[0]), float(origin[1]), float(origin[2]))
    helios_lib.setObjectOrigin(context, int(objID), o)


# ---- Primitive azimuth / elevation ----

def setPrimitiveAzimuthWrapper(context, uuid: int, origin, new_azimuth: float) -> None:
    _require_ctx_geometry_mutators()
    o = (ctypes.c_float * 3)(float(origin[0]), float(origin[1]), float(origin[2]))
    helios_lib.setPrimitiveAzimuth(context, int(uuid), o, float(new_azimuth))


def setPrimitiveElevationWrapper(context, uuid: int, origin, new_elevation: float) -> None:
    _require_ctx_geometry_mutators()
    o = (ctypes.c_float * 3)(float(origin[0]), float(origin[1]), float(origin[2]))
    helios_lib.setPrimitiveElevation(context, int(uuid), o, float(new_elevation))


# ---- Geometry mutators ----

def setTriangleVerticesWrapper(context, uuid: int, v0, v1, v2) -> None:
    _require_ctx_geometry_mutators()
    a0 = (ctypes.c_float * 3)(float(v0[0]), float(v0[1]), float(v0[2]))
    a1 = (ctypes.c_float * 3)(float(v1[0]), float(v1[1]), float(v1[2]))
    a2 = (ctypes.c_float * 3)(float(v2[0]), float(v2[1]), float(v2[2]))
    helios_lib.setTriangleVertices(context, int(uuid), a0, a1, a2)


def setPrimitiveNormalWrapper(context, uuid: int, origin, new_normal) -> None:
    _require_ctx_geometry_mutators()
    o = (ctypes.c_float * 3)(float(origin[0]), float(origin[1]), float(origin[2]))
    n = (ctypes.c_float * 3)(float(new_normal[0]), float(new_normal[1]), float(new_normal[2]))
    helios_lib.setPrimitiveNormal(context, int(uuid), o, n)


def setPrimitiveNormalBatchWrapper(context, uuids: List[int], origin, new_normal) -> None:
    _require_ctx_geometry_mutators()
    n_uuids = len(uuids)
    if n_uuids == 0:
        return
    arr = (ctypes.c_uint * n_uuids)(*uuids)
    o = (ctypes.c_float * 3)(float(origin[0]), float(origin[1]), float(origin[2]))
    n = (ctypes.c_float * 3)(float(new_normal[0]), float(new_normal[1]), float(new_normal[2]))
    helios_lib.setPrimitiveNormalBatch(context, arr, n_uuids, o, n)


def setPrimitiveParentObjectIDWrapper(context, uuid: int, objID: int) -> None:
    _require_ctx_geometry_mutators()
    helios_lib.setPrimitiveParentObjectID(context, int(uuid), int(objID))


def setPrimitiveParentObjectIDBatchWrapper(context, uuids: List[int], objID: int) -> None:
    _require_ctx_geometry_mutators()
    n_uuids = len(uuids)
    if n_uuids == 0:
        return
    arr = (ctypes.c_uint * n_uuids)(*uuids)
    helios_lib.setPrimitiveParentObjectIDBatch(context, arr, n_uuids, int(objID))


# =============================================================================
# Material data API + unique data values
# =============================================================================

_CONTEXT_MATERIAL_DATA_AVAILABLE = True
_NOT_AVAILABLE_MATERIAL_DATA_MSG = (
    "PyHelios material-data Context wrappers (material data API + unique data values) are "
    "not available in the loaded native library. Rebuild with: build_scripts/build_helios --clean"
)

try:
    # ---- setMaterialData<T> ----
    helios_lib.setMaterialDataInt.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
    helios_lib.setMaterialDataInt.restype = None
    helios_lib.setMaterialDataInt.errcheck = _check_error

    helios_lib.setMaterialDataUInt.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
    helios_lib.setMaterialDataUInt.restype = None
    helios_lib.setMaterialDataUInt.errcheck = _check_error

    helios_lib.setMaterialDataFloat.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p, ctypes.c_float]
    helios_lib.setMaterialDataFloat.restype = None
    helios_lib.setMaterialDataFloat.errcheck = _check_error

    helios_lib.setMaterialDataDouble.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p, ctypes.c_double]
    helios_lib.setMaterialDataDouble.restype = None
    helios_lib.setMaterialDataDouble.errcheck = _check_error

    helios_lib.setMaterialDataString.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.setMaterialDataString.restype = None
    helios_lib.setMaterialDataString.errcheck = _check_error

    helios_lib.setMaterialDataVec2.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p, ctypes.c_float, ctypes.c_float]
    helios_lib.setMaterialDataVec2.restype = None
    helios_lib.setMaterialDataVec2.errcheck = _check_error

    helios_lib.setMaterialDataVec3.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.setMaterialDataVec3.restype = None
    helios_lib.setMaterialDataVec3.errcheck = _check_error

    helios_lib.setMaterialDataVec4.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.setMaterialDataVec4.restype = None
    helios_lib.setMaterialDataVec4.errcheck = _check_error

    helios_lib.setMaterialDataInt2.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
    helios_lib.setMaterialDataInt2.restype = None
    helios_lib.setMaterialDataInt2.errcheck = _check_error

    helios_lib.setMaterialDataInt3.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    helios_lib.setMaterialDataInt3.restype = None
    helios_lib.setMaterialDataInt3.errcheck = _check_error

    helios_lib.setMaterialDataInt4.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    helios_lib.setMaterialDataInt4.restype = None
    helios_lib.setMaterialDataInt4.errcheck = _check_error

    # ---- getMaterialData<T> ----
    helios_lib.getMaterialDataInt.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.getMaterialDataInt.restype = ctypes.c_int
    helios_lib.getMaterialDataInt.errcheck = _check_error

    helios_lib.getMaterialDataUInt.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.getMaterialDataUInt.restype = ctypes.c_uint
    helios_lib.getMaterialDataUInt.errcheck = _check_error

    helios_lib.getMaterialDataFloat.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.getMaterialDataFloat.restype = ctypes.c_float
    helios_lib.getMaterialDataFloat.errcheck = _check_error

    helios_lib.getMaterialDataDouble.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.getMaterialDataDouble.restype = ctypes.c_double
    helios_lib.getMaterialDataDouble.errcheck = _check_error

    helios_lib.getMaterialDataString.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
    helios_lib.getMaterialDataString.restype = ctypes.c_int
    helios_lib.getMaterialDataString.errcheck = _check_error

    helios_lib.getMaterialDataVec2.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.getMaterialDataVec2.restype = None
    helios_lib.getMaterialDataVec2.errcheck = _check_error

    helios_lib.getMaterialDataVec3.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.getMaterialDataVec3.restype = None
    helios_lib.getMaterialDataVec3.errcheck = _check_error

    helios_lib.getMaterialDataVec4.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.getMaterialDataVec4.restype = None
    helios_lib.getMaterialDataVec4.errcheck = _check_error

    helios_lib.getMaterialDataInt2.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    helios_lib.getMaterialDataInt2.restype = None
    helios_lib.getMaterialDataInt2.errcheck = _check_error

    helios_lib.getMaterialDataInt3.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    helios_lib.getMaterialDataInt3.restype = None
    helios_lib.getMaterialDataInt3.errcheck = _check_error

    helios_lib.getMaterialDataInt4.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    helios_lib.getMaterialDataInt4.restype = None
    helios_lib.getMaterialDataInt4.errcheck = _check_error

    # ---- Material data type query ----
    helios_lib.getMaterialDataType.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.getMaterialDataType.restype = ctypes.c_int
    helios_lib.getMaterialDataType.errcheck = _check_error

    # ---- Unique data values ----
    helios_lib.getUniquePrimitiveDataValuesInt.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getUniquePrimitiveDataValuesInt.restype = ctypes.POINTER(ctypes.c_int)
    helios_lib.getUniquePrimitiveDataValuesInt.errcheck = _check_error

    helios_lib.getUniquePrimitiveDataValuesUInt.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getUniquePrimitiveDataValuesUInt.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.getUniquePrimitiveDataValuesUInt.errcheck = _check_error

    helios_lib.getUniquePrimitiveDataValuesStringCount.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p]
    helios_lib.getUniquePrimitiveDataValuesStringCount.restype = ctypes.c_uint
    helios_lib.getUniquePrimitiveDataValuesStringCount.errcheck = _check_error

    helios_lib.getUniquePrimitiveDataValuesString.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_uint, ctypes.c_char_p, ctypes.c_int]
    helios_lib.getUniquePrimitiveDataValuesString.restype = ctypes.c_int
    helios_lib.getUniquePrimitiveDataValuesString.errcheck = _check_error

    helios_lib.getUniqueObjectDataValuesInt.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getUniqueObjectDataValuesInt.restype = ctypes.POINTER(ctypes.c_int)
    helios_lib.getUniqueObjectDataValuesInt.errcheck = _check_error

    helios_lib.getUniqueObjectDataValuesUInt.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getUniqueObjectDataValuesUInt.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.getUniqueObjectDataValuesUInt.errcheck = _check_error

    helios_lib.getUniqueObjectDataValuesStringCount.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p]
    helios_lib.getUniqueObjectDataValuesStringCount.restype = ctypes.c_uint
    helios_lib.getUniqueObjectDataValuesStringCount.errcheck = _check_error

    helios_lib.getUniqueObjectDataValuesString.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_uint, ctypes.c_char_p, ctypes.c_int]
    helios_lib.getUniqueObjectDataValuesString.restype = ctypes.c_int
    helios_lib.getUniqueObjectDataValuesString.errcheck = _check_error

except AttributeError:
    _CONTEXT_MATERIAL_DATA_AVAILABLE = False


def _require_ctx_material_data():
    if not _CONTEXT_MATERIAL_DATA_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_MATERIAL_DATA_MSG)


def _enc(s: str) -> bytes:
    return s.encode('utf-8')


# ---- setMaterialData<T> Python wrappers ----

def setMaterialDataIntWrapper(context, material_label: str, data_label: str, value: int) -> None:
    _require_ctx_material_data()
    helios_lib.setMaterialDataInt(context, _enc(material_label), _enc(data_label), int(value))


def setMaterialDataUIntWrapper(context, material_label: str, data_label: str, value: int) -> None:
    _require_ctx_material_data()
    helios_lib.setMaterialDataUInt(context, _enc(material_label), _enc(data_label), int(value))


def setMaterialDataFloatWrapper(context, material_label: str, data_label: str, value: float) -> None:
    _require_ctx_material_data()
    helios_lib.setMaterialDataFloat(context, _enc(material_label), _enc(data_label), float(value))


def setMaterialDataDoubleWrapper(context, material_label: str, data_label: str, value: float) -> None:
    _require_ctx_material_data()
    helios_lib.setMaterialDataDouble(context, _enc(material_label), _enc(data_label), float(value))


def setMaterialDataStringWrapper(context, material_label: str, data_label: str, value: str) -> None:
    _require_ctx_material_data()
    helios_lib.setMaterialDataString(context, _enc(material_label), _enc(data_label), _enc(value))


def setMaterialDataVec2Wrapper(context, material_label: str, data_label: str, x: float, y: float) -> None:
    _require_ctx_material_data()
    helios_lib.setMaterialDataVec2(context, _enc(material_label), _enc(data_label), float(x), float(y))


def setMaterialDataVec3Wrapper(context, material_label: str, data_label: str, x: float, y: float, z: float) -> None:
    _require_ctx_material_data()
    helios_lib.setMaterialDataVec3(context, _enc(material_label), _enc(data_label), float(x), float(y), float(z))


def setMaterialDataVec4Wrapper(context, material_label: str, data_label: str, x: float, y: float, z: float, w: float) -> None:
    _require_ctx_material_data()
    helios_lib.setMaterialDataVec4(context, _enc(material_label), _enc(data_label), float(x), float(y), float(z), float(w))


def setMaterialDataInt2Wrapper(context, material_label: str, data_label: str, x: int, y: int) -> None:
    _require_ctx_material_data()
    helios_lib.setMaterialDataInt2(context, _enc(material_label), _enc(data_label), int(x), int(y))


def setMaterialDataInt3Wrapper(context, material_label: str, data_label: str, x: int, y: int, z: int) -> None:
    _require_ctx_material_data()
    helios_lib.setMaterialDataInt3(context, _enc(material_label), _enc(data_label), int(x), int(y), int(z))


def setMaterialDataInt4Wrapper(context, material_label: str, data_label: str, x: int, y: int, z: int, w: int) -> None:
    _require_ctx_material_data()
    helios_lib.setMaterialDataInt4(context, _enc(material_label), _enc(data_label), int(x), int(y), int(z), int(w))


# ---- getMaterialData<T> Python wrappers ----

def getMaterialDataIntWrapper(context, material_label: str, data_label: str) -> int:
    _require_ctx_material_data()
    return int(helios_lib.getMaterialDataInt(context, _enc(material_label), _enc(data_label)))


def getMaterialDataUIntWrapper(context, material_label: str, data_label: str) -> int:
    _require_ctx_material_data()
    return int(helios_lib.getMaterialDataUInt(context, _enc(material_label), _enc(data_label)))


def getMaterialDataFloatWrapper(context, material_label: str, data_label: str) -> float:
    _require_ctx_material_data()
    return float(helios_lib.getMaterialDataFloat(context, _enc(material_label), _enc(data_label)))


def getMaterialDataDoubleWrapper(context, material_label: str, data_label: str) -> float:
    _require_ctx_material_data()
    return float(helios_lib.getMaterialDataDouble(context, _enc(material_label), _enc(data_label)))


def getMaterialDataStringWrapper(context, material_label: str, data_label: str) -> str:
    _require_ctx_material_data()
    return _read_string_buffer(helios_lib.getMaterialDataString, context, _enc(material_label), _enc(data_label))


def getMaterialDataVec2Wrapper(context, material_label: str, data_label: str):
    _require_ctx_material_data()
    x, y = ctypes.c_float(), ctypes.c_float()
    helios_lib.getMaterialDataVec2(context, _enc(material_label), _enc(data_label), ctypes.byref(x), ctypes.byref(y))
    return (float(x.value), float(y.value))


def getMaterialDataVec3Wrapper(context, material_label: str, data_label: str):
    _require_ctx_material_data()
    x, y, z = ctypes.c_float(), ctypes.c_float(), ctypes.c_float()
    helios_lib.getMaterialDataVec3(context, _enc(material_label), _enc(data_label), ctypes.byref(x), ctypes.byref(y), ctypes.byref(z))
    return (float(x.value), float(y.value), float(z.value))


def getMaterialDataVec4Wrapper(context, material_label: str, data_label: str):
    _require_ctx_material_data()
    x, y, z, w = ctypes.c_float(), ctypes.c_float(), ctypes.c_float(), ctypes.c_float()
    helios_lib.getMaterialDataVec4(context, _enc(material_label), _enc(data_label), ctypes.byref(x), ctypes.byref(y), ctypes.byref(z), ctypes.byref(w))
    return (float(x.value), float(y.value), float(z.value), float(w.value))


def getMaterialDataInt2Wrapper(context, material_label: str, data_label: str):
    _require_ctx_material_data()
    x, y = ctypes.c_int(), ctypes.c_int()
    helios_lib.getMaterialDataInt2(context, _enc(material_label), _enc(data_label), ctypes.byref(x), ctypes.byref(y))
    return (int(x.value), int(y.value))


def getMaterialDataInt3Wrapper(context, material_label: str, data_label: str):
    _require_ctx_material_data()
    x, y, z = ctypes.c_int(), ctypes.c_int(), ctypes.c_int()
    helios_lib.getMaterialDataInt3(context, _enc(material_label), _enc(data_label), ctypes.byref(x), ctypes.byref(y), ctypes.byref(z))
    return (int(x.value), int(y.value), int(z.value))


def getMaterialDataInt4Wrapper(context, material_label: str, data_label: str):
    _require_ctx_material_data()
    x, y, z, w = ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int()
    helios_lib.getMaterialDataInt4(context, _enc(material_label), _enc(data_label), ctypes.byref(x), ctypes.byref(y), ctypes.byref(z), ctypes.byref(w))
    return (int(x.value), int(y.value), int(z.value), int(w.value))


def getMaterialDataTypeWrapper(context, material_label: str, data_label: str) -> int:
    _require_ctx_material_data()
    return int(helios_lib.getMaterialDataType(context, _enc(material_label), _enc(data_label)))


# ---- Unique data values ----

def getUniquePrimitiveDataValuesIntWrapper(context, label: str) -> List[int]:
    _require_ctx_material_data()
    count = ctypes.c_uint()
    ptr = helios_lib.getUniquePrimitiveDataValuesInt(context, _enc(label), ctypes.byref(count))
    if count.value == 0 or not ptr:
        return []
    return [int(ptr[i]) for i in range(count.value)]


def getUniquePrimitiveDataValuesUIntWrapper(context, label: str) -> List[int]:
    _require_ctx_material_data()
    count = ctypes.c_uint()
    ptr = helios_lib.getUniquePrimitiveDataValuesUInt(context, _enc(label), ctypes.byref(count))
    if count.value == 0 or not ptr:
        return []
    return [int(ptr[i]) for i in range(count.value)]


def getUniquePrimitiveDataValuesStringWrapper(context, label: str) -> List[str]:
    # Same count+index pattern as listAllPrimitiveDataLabelsWrapper —
    # the C side caches the snapshot in a thread-local std::vector<std::string>.
    _require_ctx_material_data()
    label_b = _enc(label)
    count = int(helios_lib.getUniquePrimitiveDataValuesStringCount(context, label_b))
    return [
        _read_string_buffer(helios_lib.getUniquePrimitiveDataValuesString, context, label_b, i)
        for i in range(count)
    ]


def getUniqueObjectDataValuesIntWrapper(context, label: str) -> List[int]:
    _require_ctx_material_data()
    count = ctypes.c_uint()
    ptr = helios_lib.getUniqueObjectDataValuesInt(context, _enc(label), ctypes.byref(count))
    if count.value == 0 or not ptr:
        return []
    return [int(ptr[i]) for i in range(count.value)]


def getUniqueObjectDataValuesUIntWrapper(context, label: str) -> List[int]:
    _require_ctx_material_data()
    count = ctypes.c_uint()
    ptr = helios_lib.getUniqueObjectDataValuesUInt(context, _enc(label), ctypes.byref(count))
    if count.value == 0 or not ptr:
        return []
    return [int(ptr[i]) for i in range(count.value)]


def getUniqueObjectDataValuesStringWrapper(context, label: str) -> List[str]:
    _require_ctx_material_data()
    label_b = _enc(label)
    count = int(helios_lib.getUniqueObjectDataValuesStringCount(context, label_b))
    return [
        _read_string_buffer(helios_lib.getUniqueObjectDataValuesString, context, label_b, i)
        for i in range(count)
    ]


# =============================================================================
# 4x4 transformation matrices + domain bounds
# =============================================================================

_CONTEXT_TRANSFORM_MATRIX_AVAILABLE = True
_NOT_AVAILABLE_TRANSFORM_MATRIX_MSG = (
    "PyHelios transform-matrix Context wrappers (4x4 transforms + domain bounds) are not "
    "available in the loaded native library. Rebuild with: build_scripts/build_helios --clean"
)

try:
    # ---- 4x4 transformation matrices ----
    helios_lib.getObjectTransformationMatrix.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.getObjectTransformationMatrix.restype = None
    helios_lib.getObjectTransformationMatrix.errcheck = _check_error

    helios_lib.setObjectTransformationMatrix.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.setObjectTransformationMatrix.restype = None
    helios_lib.setObjectTransformationMatrix.errcheck = _check_error

    helios_lib.setObjectTransformationMatrixBatch.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.setObjectTransformationMatrixBatch.restype = None
    helios_lib.setObjectTransformationMatrixBatch.errcheck = _check_error

    helios_lib.getPrimitiveTransformationMatrix.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.getPrimitiveTransformationMatrix.restype = None
    helios_lib.getPrimitiveTransformationMatrix.errcheck = _check_error

    helios_lib.setPrimitiveTransformationMatrix.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.setPrimitiveTransformationMatrix.restype = None
    helios_lib.setPrimitiveTransformationMatrix.errcheck = _check_error

    helios_lib.setPrimitiveTransformationMatrixBatch.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.setPrimitiveTransformationMatrixBatch.restype = None
    helios_lib.setPrimitiveTransformationMatrixBatch.errcheck = _check_error

    # ---- Domain bounds ----
    helios_lib.getDomainBoundingBox.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float)]
    helios_lib.getDomainBoundingBox.restype = None
    helios_lib.getDomainBoundingBox.errcheck = _check_error

    helios_lib.getDomainBoundingBoxFiltered.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.getDomainBoundingBoxFiltered.restype = None
    helios_lib.getDomainBoundingBoxFiltered.errcheck = _check_error

    helios_lib.getDomainBoundingSphere.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.getDomainBoundingSphere.restype = None
    helios_lib.getDomainBoundingSphere.errcheck = _check_error

    helios_lib.getDomainBoundingSphereFiltered.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.getDomainBoundingSphereFiltered.restype = None
    helios_lib.getDomainBoundingSphereFiltered.errcheck = _check_error

except AttributeError:
    _CONTEXT_TRANSFORM_MATRIX_AVAILABLE = False


def _require_ctx_transform_matrix():
    if not _CONTEXT_TRANSFORM_MATRIX_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_TRANSFORM_MATRIX_MSG)


def _alloc_mat4_buffer():
    """Allocate a (ctypes.c_float * 16) buffer for transformation matrix I/O."""
    return (ctypes.c_float * 16)()


# ---- Transformation matrices ----

def getObjectTransformationMatrixWrapper(context, objID: int) -> List[float]:
    """Return the 16 floats of the object's transformation matrix in row-major order."""
    _require_ctx_transform_matrix()
    buf = _alloc_mat4_buffer()
    helios_lib.getObjectTransformationMatrix(context, int(objID), buf)
    return [float(buf[i]) for i in range(16)]


def setObjectTransformationMatrixWrapper(context, objID: int, T_flat: List[float]) -> None:
    _require_ctx_transform_matrix()
    if len(T_flat) != 16:
        raise ValueError(f"Matrix must have 16 elements, got {len(T_flat)}")
    buf = (ctypes.c_float * 16)(*[float(v) for v in T_flat])
    helios_lib.setObjectTransformationMatrix(context, int(objID), buf)


def setObjectTransformationMatrixBatchWrapper(context, objIDs: List[int], T_flat: List[float]) -> None:
    _require_ctx_transform_matrix()
    if len(T_flat) != 16:
        raise ValueError(f"Matrix must have 16 elements, got {len(T_flat)}")
    n = len(objIDs)
    if n == 0:
        return
    arr = (ctypes.c_uint * n)(*objIDs)
    buf = (ctypes.c_float * 16)(*[float(v) for v in T_flat])
    helios_lib.setObjectTransformationMatrixBatch(context, arr, n, buf)


def getPrimitiveTransformationMatrixWrapper(context, uuid: int) -> List[float]:
    _require_ctx_transform_matrix()
    buf = _alloc_mat4_buffer()
    helios_lib.getPrimitiveTransformationMatrix(context, int(uuid), buf)
    return [float(buf[i]) for i in range(16)]


def setPrimitiveTransformationMatrixWrapper(context, uuid: int, T_flat: List[float]) -> None:
    _require_ctx_transform_matrix()
    if len(T_flat) != 16:
        raise ValueError(f"Matrix must have 16 elements, got {len(T_flat)}")
    buf = (ctypes.c_float * 16)(*[float(v) for v in T_flat])
    helios_lib.setPrimitiveTransformationMatrix(context, int(uuid), buf)


def setPrimitiveTransformationMatrixBatchWrapper(context, uuids: List[int], T_flat: List[float]) -> None:
    _require_ctx_transform_matrix()
    if len(T_flat) != 16:
        raise ValueError(f"Matrix must have 16 elements, got {len(T_flat)}")
    n = len(uuids)
    if n == 0:
        return
    arr = (ctypes.c_uint * n)(*uuids)
    buf = (ctypes.c_float * 16)(*[float(v) for v in T_flat])
    helios_lib.setPrimitiveTransformationMatrixBatch(context, arr, n, buf)


# ---- Domain bounds ----

def getDomainBoundingBoxWrapper(context):
    """Return ((xmin, xmax), (ymin, ymax), (zmin, zmax))."""
    _require_ctx_transform_matrix()
    buf = (ctypes.c_float * 6)()
    helios_lib.getDomainBoundingBox(context, buf)
    return ((float(buf[0]), float(buf[1])),
            (float(buf[2]), float(buf[3])),
            (float(buf[4]), float(buf[5])))


def getDomainBoundingBoxFilteredWrapper(context, uuids: List[int]):
    _require_ctx_transform_matrix()
    n = len(uuids)
    arr = (ctypes.c_uint * max(n, 1))(*uuids) if n > 0 else (ctypes.c_uint * 1)()
    buf = (ctypes.c_float * 6)()
    helios_lib.getDomainBoundingBoxFiltered(context, arr, n, buf)
    return ((float(buf[0]), float(buf[1])),
            (float(buf[2]), float(buf[3])),
            (float(buf[4]), float(buf[5])))


def getDomainBoundingSphereWrapper(context):
    """Return ((cx, cy, cz), radius)."""
    _require_ctx_transform_matrix()
    center = (ctypes.c_float * 3)()
    radius = ctypes.c_float()
    helios_lib.getDomainBoundingSphere(context, center, ctypes.byref(radius))
    return ((float(center[0]), float(center[1]), float(center[2])), float(radius.value))


def getDomainBoundingSphereFilteredWrapper(context, uuids: List[int]):
    _require_ctx_transform_matrix()
    n = len(uuids)
    arr = (ctypes.c_uint * max(n, 1))(*uuids) if n > 0 else (ctypes.c_uint * 1)()
    center = (ctypes.c_float * 3)()
    radius = ctypes.c_float()
    helios_lib.getDomainBoundingSphereFiltered(context, arr, n, center, ctypes.byref(radius))
    return ((float(center[0]), float(center[1]), float(center[2])), float(radius.value))


# =============================================================================
# Tube/polymesh + object color/dirty/tile mutators
# =============================================================================

_CONTEXT_TUBE_OBJECT_AVAILABLE = True
_NOT_AVAILABLE_TUBE_OBJECT_MSG = (
    "PyHelios tube-object Context wrappers (tube/polymesh + object color/dirty/tile mutators) "
    "are not available in the loaded native library. Rebuild with: build_scripts/build_helios --clean"
)

try:
    # Tube object mutators
    helios_lib.setTubeNodes.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.c_uint]
    helios_lib.setTubeNodes.restype = None
    helios_lib.setTubeNodes.errcheck = _check_error

    helios_lib.setTubeRadii.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.c_uint]
    helios_lib.setTubeRadii.restype = None
    helios_lib.setTubeRadii.errcheck = _check_error

    helios_lib.scaleTubeGirth.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_float]
    helios_lib.scaleTubeGirth.restype = None
    helios_lib.scaleTubeGirth.errcheck = _check_error

    helios_lib.scaleTubeLength.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_float]
    helios_lib.scaleTubeLength.restype = None
    helios_lib.scaleTubeLength.errcheck = _check_error

    helios_lib.pruneTubeNodes.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_uint]
    helios_lib.pruneTubeNodes.restype = None
    helios_lib.pruneTubeNodes.errcheck = _check_error

    helios_lib.appendTubeSegmentColor.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
    helios_lib.appendTubeSegmentColor.restype = None
    helios_lib.appendTubeSegmentColor.errcheck = _check_error

    helios_lib.appendTubeSegmentTexture.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.c_float, ctypes.c_char_p, ctypes.POINTER(ctypes.c_float)]
    helios_lib.appendTubeSegmentTexture.restype = None
    helios_lib.appendTubeSegmentTexture.errcheck = _check_error

    helios_lib.addPolymeshObject.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint]
    helios_lib.addPolymeshObject.restype = ctypes.c_uint
    helios_lib.addPolymeshObject.errcheck = _check_error

    # Object color
    helios_lib.setObjectColorRGB.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.setObjectColorRGB.restype = None
    helios_lib.setObjectColorRGB.errcheck = _check_error

    helios_lib.setObjectColorRGBBatch.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.setObjectColorRGBBatch.restype = None
    helios_lib.setObjectColorRGBBatch.errcheck = _check_error

    helios_lib.setObjectColorRGBA.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.setObjectColorRGBA.restype = None
    helios_lib.setObjectColorRGBA.errcheck = _check_error

    helios_lib.setObjectColorRGBABatch.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_float)]
    helios_lib.setObjectColorRGBABatch.restype = None
    helios_lib.setObjectColorRGBABatch.errcheck = _check_error

    helios_lib.overrideObjectTextureColor.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.overrideObjectTextureColor.restype = None
    helios_lib.overrideObjectTextureColor.errcheck = _check_error

    helios_lib.overrideObjectTextureColorBatch.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint]
    helios_lib.overrideObjectTextureColorBatch.restype = None
    helios_lib.overrideObjectTextureColorBatch.errcheck = _check_error

    helios_lib.useObjectTextureColor.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.useObjectTextureColor.restype = None
    helios_lib.useObjectTextureColor.errcheck = _check_error

    helios_lib.useObjectTextureColorBatch.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint]
    helios_lib.useObjectTextureColorBatch.restype = None
    helios_lib.useObjectTextureColorBatch.errcheck = _check_error

    # Mark dirty/clean
    helios_lib.markPrimitiveDirty.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.markPrimitiveDirty.restype = None
    helios_lib.markPrimitiveDirty.errcheck = _check_error

    helios_lib.markPrimitiveDirtyBatch.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint]
    helios_lib.markPrimitiveDirtyBatch.restype = None
    helios_lib.markPrimitiveDirtyBatch.errcheck = _check_error

    helios_lib.markPrimitiveClean.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.markPrimitiveClean.restype = None
    helios_lib.markPrimitiveClean.errcheck = _check_error

    helios_lib.markPrimitiveCleanBatch.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint]
    helios_lib.markPrimitiveCleanBatch.restype = None
    helios_lib.markPrimitiveCleanBatch.errcheck = _check_error

    # Tile subdivision
    helios_lib.setTileObjectSubdivisionCount.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.c_int, ctypes.c_int]
    helios_lib.setTileObjectSubdivisionCount.restype = None
    helios_lib.setTileObjectSubdivisionCount.errcheck = _check_error

    helios_lib.setTileObjectSubdivisionByAreaRatio.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.c_float]
    helios_lib.setTileObjectSubdivisionByAreaRatio.restype = None
    helios_lib.setTileObjectSubdivisionByAreaRatio.errcheck = _check_error

except AttributeError:
    _CONTEXT_TUBE_OBJECT_AVAILABLE = False


def _require_ctx_tube_object():
    if not _CONTEXT_TUBE_OBJECT_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_TUBE_OBJECT_MSG)


# ---- Tube object mutators ----

def setTubeNodesWrapper(context, objID: int, nodes_xyz_flat: List[float]) -> None:
    _require_ctx_tube_object()
    if len(nodes_xyz_flat) % 3 != 0:
        raise ValueError(f"nodes_xyz_flat length must be a multiple of 3, got {len(nodes_xyz_flat)}")
    n = len(nodes_xyz_flat) // 3
    if n == 0:
        return
    buf = (ctypes.c_float * len(nodes_xyz_flat))(*[float(v) for v in nodes_xyz_flat])
    helios_lib.setTubeNodes(context, int(objID), buf, n)


def setTubeRadiiWrapper(context, objID: int, radii: List[float]) -> None:
    _require_ctx_tube_object()
    n = len(radii)
    if n == 0:
        return
    buf = (ctypes.c_float * n)(*[float(v) for v in radii])
    helios_lib.setTubeRadii(context, int(objID), buf, n)


def scaleTubeGirthWrapper(context, objID: int, scale_factor: float) -> None:
    _require_ctx_tube_object()
    helios_lib.scaleTubeGirth(context, int(objID), float(scale_factor))


def scaleTubeLengthWrapper(context, objID: int, scale_factor: float) -> None:
    _require_ctx_tube_object()
    helios_lib.scaleTubeLength(context, int(objID), float(scale_factor))


def pruneTubeNodesWrapper(context, objID: int, node_index: int) -> None:
    _require_ctx_tube_object()
    helios_lib.pruneTubeNodes(context, int(objID), int(node_index))


def appendTubeSegmentColorWrapper(context, objID: int, node_position, node_radius: float, color_rgb) -> None:
    _require_ctx_tube_object()
    pos = (ctypes.c_float * 3)(float(node_position[0]), float(node_position[1]), float(node_position[2]))
    col = (ctypes.c_float * 3)(float(color_rgb[0]), float(color_rgb[1]), float(color_rgb[2]))
    helios_lib.appendTubeSegmentColor(context, int(objID), pos, float(node_radius), col)


def appendTubeSegmentTextureWrapper(context, objID: int, node_position, node_radius: float, texture_file: str, uv) -> None:
    _require_ctx_tube_object()
    pos = (ctypes.c_float * 3)(float(node_position[0]), float(node_position[1]), float(node_position[2]))
    uv_buf = (ctypes.c_float * 2)(float(uv[0]), float(uv[1]))
    helios_lib.appendTubeSegmentTexture(context, int(objID), pos, float(node_radius), texture_file.encode('utf-8'), uv_buf)


def addPolymeshObjectWrapper(context, uuids: List[int]) -> int:
    _require_ctx_tube_object()
    n = len(uuids)
    if n == 0:
        raise ValueError("addPolymeshObject requires at least one UUID")
    arr = (ctypes.c_uint * n)(*uuids)
    return int(helios_lib.addPolymeshObject(context, arr, n))


# ---- Object color ----

def setObjectColorRGBWrapper(context, objID: int, color_rgb) -> None:
    _require_ctx_tube_object()
    col = (ctypes.c_float * 3)(float(color_rgb[0]), float(color_rgb[1]), float(color_rgb[2]))
    helios_lib.setObjectColorRGB(context, int(objID), col)


def setObjectColorRGBBatchWrapper(context, objIDs: List[int], color_rgb) -> None:
    _require_ctx_tube_object()
    n = len(objIDs)
    if n == 0:
        return
    arr = (ctypes.c_uint * n)(*objIDs)
    col = (ctypes.c_float * 3)(float(color_rgb[0]), float(color_rgb[1]), float(color_rgb[2]))
    helios_lib.setObjectColorRGBBatch(context, arr, n, col)


def setObjectColorRGBAWrapper(context, objID: int, color_rgba) -> None:
    _require_ctx_tube_object()
    col = (ctypes.c_float * 4)(float(color_rgba[0]), float(color_rgba[1]), float(color_rgba[2]), float(color_rgba[3]))
    helios_lib.setObjectColorRGBA(context, int(objID), col)


def setObjectColorRGBABatchWrapper(context, objIDs: List[int], color_rgba) -> None:
    _require_ctx_tube_object()
    n = len(objIDs)
    if n == 0:
        return
    arr = (ctypes.c_uint * n)(*objIDs)
    col = (ctypes.c_float * 4)(float(color_rgba[0]), float(color_rgba[1]), float(color_rgba[2]), float(color_rgba[3]))
    helios_lib.setObjectColorRGBABatch(context, arr, n, col)


def overrideObjectTextureColorWrapper(context, objID: int) -> None:
    _require_ctx_tube_object()
    helios_lib.overrideObjectTextureColor(context, int(objID))


def overrideObjectTextureColorBatchWrapper(context, objIDs: List[int]) -> None:
    _require_ctx_tube_object()
    n = len(objIDs)
    if n == 0:
        return
    arr = (ctypes.c_uint * n)(*objIDs)
    helios_lib.overrideObjectTextureColorBatch(context, arr, n)


def useObjectTextureColorWrapper(context, objID: int) -> None:
    _require_ctx_tube_object()
    helios_lib.useObjectTextureColor(context, int(objID))


def useObjectTextureColorBatchWrapper(context, objIDs: List[int]) -> None:
    _require_ctx_tube_object()
    n = len(objIDs)
    if n == 0:
        return
    arr = (ctypes.c_uint * n)(*objIDs)
    helios_lib.useObjectTextureColorBatch(context, arr, n)


# ---- Mark dirty/clean ----

def markPrimitiveDirtyWrapper(context, uuid: int) -> None:
    _require_ctx_tube_object()
    helios_lib.markPrimitiveDirty(context, int(uuid))


def markPrimitiveDirtyBatchWrapper(context, uuids: List[int]) -> None:
    _require_ctx_tube_object()
    n = len(uuids)
    if n == 0:
        return
    arr = (ctypes.c_uint * n)(*uuids)
    helios_lib.markPrimitiveDirtyBatch(context, arr, n)


def markPrimitiveCleanWrapper(context, uuid: int) -> None:
    _require_ctx_tube_object()
    helios_lib.markPrimitiveClean(context, int(uuid))


def markPrimitiveCleanBatchWrapper(context, uuids: List[int]) -> None:
    _require_ctx_tube_object()
    n = len(uuids)
    if n == 0:
        return
    arr = (ctypes.c_uint * n)(*uuids)
    helios_lib.markPrimitiveCleanBatch(context, arr, n)


# ---- Tile subdivision ----

def setTileObjectSubdivisionCountWrapper(context, objIDs: List[int], subdiv_x: int, subdiv_y: int) -> None:
    _require_ctx_tube_object()
    n = len(objIDs)
    if n == 0:
        return
    arr = (ctypes.c_uint * n)(*objIDs)
    helios_lib.setTileObjectSubdivisionCount(context, arr, n, int(subdiv_x), int(subdiv_y))


def setTileObjectSubdivisionByAreaRatioWrapper(context, objIDs: List[int], area_ratio: float) -> None:
    _require_ctx_tube_object()
    n = len(objIDs)
    if n == 0:
        return
    arr = (ctypes.c_uint * n)(*objIDs)
    helios_lib.setTileObjectSubdivisionByAreaRatio(context, arr, n, float(area_ratio))


# =============================================================================
# Cleanup, XML write, RNG, Location
# =============================================================================

_CONTEXT_XML_RNG_LOC_AVAILABLE = True
_NOT_AVAILABLE_XML_RNG_LOC_MSG = (
    "PyHelios cleanup/XML/RNG/Location Context wrappers are not available "
    "in the loaded native library. Rebuild with: build_scripts/build_helios --clean"
)

try:
    helios_lib.cleanDeletedUUIDs.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.cleanDeletedUUIDs.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.cleanDeletedUUIDs.errcheck = _check_error

    helios_lib.cleanDeletedObjectIDs.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.cleanDeletedObjectIDs.restype = ctypes.POINTER(ctypes.c_uint)
    helios_lib.cleanDeletedObjectIDs.errcheck = _check_error

    helios_lib.writeXML.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_bool]
    helios_lib.writeXML.restype = None
    helios_lib.writeXML.errcheck = _check_error

    helios_lib.writeXMLFiltered.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.c_bool]
    helios_lib.writeXMLFiltered.restype = None
    helios_lib.writeXMLFiltered.errcheck = _check_error

    helios_lib.writeXML_byobject.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.c_bool]
    helios_lib.writeXML_byobject.restype = None
    helios_lib.writeXML_byobject.errcheck = _check_error

    helios_lib.randu_basic.argtypes = [ctypes.POINTER(UContext)]
    helios_lib.randu_basic.restype = ctypes.c_float
    helios_lib.randu_basic.errcheck = _check_error

    helios_lib.randu_range.argtypes = [ctypes.POINTER(UContext), ctypes.c_float, ctypes.c_float]
    helios_lib.randu_range.restype = ctypes.c_float
    helios_lib.randu_range.errcheck = _check_error

    helios_lib.randu_int_range.argtypes = [ctypes.POINTER(UContext), ctypes.c_int, ctypes.c_int]
    helios_lib.randu_int_range.restype = ctypes.c_int
    helios_lib.randu_int_range.errcheck = _check_error

    helios_lib.randn_basic.argtypes = [ctypes.POINTER(UContext)]
    helios_lib.randn_basic.restype = ctypes.c_float
    helios_lib.randn_basic.errcheck = _check_error

    helios_lib.randn_params.argtypes = [ctypes.POINTER(UContext), ctypes.c_float, ctypes.c_float]
    helios_lib.randn_params.restype = ctypes.c_float
    helios_lib.randn_params.errcheck = _check_error

    helios_lib.setLocation.argtypes = [ctypes.POINTER(UContext), ctypes.c_float, ctypes.c_float, ctypes.c_float]
    helios_lib.setLocation.restype = None
    helios_lib.setLocation.errcheck = _check_error

    helios_lib.getLocation.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.getLocation.restype = None
    helios_lib.getLocation.errcheck = _check_error

except AttributeError:
    _CONTEXT_XML_RNG_LOC_AVAILABLE = False


def _require_ctx_xml_rng_loc():
    if not _CONTEXT_XML_RNG_LOC_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_XML_RNG_LOC_MSG)


# ---- Cleanup ----

def cleanDeletedUUIDsWrapper(context, uuids: List[int]) -> List[int]:
    """Return a new list with deleted UUIDs removed; does NOT mutate the input."""
    _require_ctx_xml_rng_loc()
    n = len(uuids)
    arr_in = (ctypes.c_uint * max(n, 1))(*uuids) if n > 0 else (ctypes.c_uint * 1)()
    count_out = ctypes.c_uint()
    ptr = helios_lib.cleanDeletedUUIDs(context, arr_in, n, ctypes.byref(count_out))
    if count_out.value == 0 or not ptr:
        return []
    return [int(ptr[i]) for i in range(count_out.value)]


def cleanDeletedObjectIDsWrapper(context, objIDs: List[int]) -> List[int]:
    _require_ctx_xml_rng_loc()
    n = len(objIDs)
    arr_in = (ctypes.c_uint * max(n, 1))(*objIDs) if n > 0 else (ctypes.c_uint * 1)()
    count_out = ctypes.c_uint()
    ptr = helios_lib.cleanDeletedObjectIDs(context, arr_in, n, ctypes.byref(count_out))
    if count_out.value == 0 or not ptr:
        return []
    return [int(ptr[i]) for i in range(count_out.value)]


# ---- XML write ----

def writeXMLWrapper(context, filename: str, quiet: bool = False) -> None:
    _require_ctx_xml_rng_loc()
    helios_lib.writeXML(context, filename.encode('utf-8'), bool(quiet))


def writeXMLFilteredWrapper(context, filename: str, uuids: List[int], quiet: bool = False) -> None:
    _require_ctx_xml_rng_loc()
    n = len(uuids)
    arr = (ctypes.c_uint * max(n, 1))(*uuids) if n > 0 else (ctypes.c_uint * 1)()
    helios_lib.writeXMLFiltered(context, filename.encode('utf-8'), arr, n, bool(quiet))


def writeXMLByObjectWrapper(context, filename: str, objIDs: List[int], quiet: bool = False) -> None:
    _require_ctx_xml_rng_loc()
    n = len(objIDs)
    arr = (ctypes.c_uint * max(n, 1))(*objIDs) if n > 0 else (ctypes.c_uint * 1)()
    helios_lib.writeXML_byobject(context, filename.encode('utf-8'), arr, n, bool(quiet))


# ---- RNG ----

def randuBasicWrapper(context) -> float:
    _require_ctx_xml_rng_loc()
    return float(helios_lib.randu_basic(context))


def randuRangeWrapper(context, low: float, high: float) -> float:
    _require_ctx_xml_rng_loc()
    return float(helios_lib.randu_range(context, float(low), float(high)))


def randuIntRangeWrapper(context, low: int, high: int) -> int:
    _require_ctx_xml_rng_loc()
    return int(helios_lib.randu_int_range(context, int(low), int(high)))


def randnBasicWrapper(context) -> float:
    _require_ctx_xml_rng_loc()
    return float(helios_lib.randn_basic(context))


def randnParamsWrapper(context, mean: float, stddev: float) -> float:
    _require_ctx_xml_rng_loc()
    return float(helios_lib.randn_params(context, float(mean), float(stddev)))


# ---- Location ----

def setLocationWrapper(context, latitude: float, longitude: float, utc_offset: float) -> None:
    _require_ctx_xml_rng_loc()
    helios_lib.setLocation(context, float(latitude), float(longitude), float(utc_offset))


def getLocationWrapper(context):
    """Return (latitude, longitude, utc_offset) as a 3-tuple of floats."""
    _require_ctx_xml_rng_loc()
    lat = ctypes.c_float()
    lon = ctypes.c_float()
    utc = ctypes.c_float()
    helios_lib.getLocation(context, ctypes.byref(lat), ctypes.byref(lon), ctypes.byref(utc))
    return (float(lat.value), float(lon.value), float(utc.value))


# =============================================================================
# Colormap helpers + texture transparency
# =============================================================================

_CONTEXT_COLORMAP_AVAILABLE = True
_NOT_AVAILABLE_COLORMAP_MSG = (
    "PyHelios colormap Context wrappers (colormap + texture transparency) are not "
    "available in the loaded native library. Rebuild with: build_scripts/build_helios --clean"
)

try:
    helios_lib.generateColormapNamed.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.generateColormapNamed.restype = ctypes.POINTER(ctypes.c_float)
    helios_lib.generateColormapNamed.errcheck = _check_error

    helios_lib.generateTexturesFromColormapCount.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.POINTER(ctypes.c_float), ctypes.c_uint]
    helios_lib.generateTexturesFromColormapCount.restype = ctypes.c_uint
    helios_lib.generateTexturesFromColormapCount.errcheck = _check_error

    helios_lib.generateTexturesFromColormapPath.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.c_char_p, ctypes.c_int]
    helios_lib.generateTexturesFromColormapPath.restype = ctypes.c_int
    helios_lib.generateTexturesFromColormapPath.errcheck = _check_error

    helios_lib.getPrimitiveTextureTransparencyDataInfo.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getPrimitiveTextureTransparencyDataInfo.restype = ctypes.c_int
    helios_lib.getPrimitiveTextureTransparencyDataInfo.errcheck = _check_error

    helios_lib.getPrimitiveTextureTransparencyDataBuffer.argtypes = [ctypes.POINTER(UContext), ctypes.c_uint]
    helios_lib.getPrimitiveTextureTransparencyDataBuffer.restype = ctypes.POINTER(ctypes.c_ubyte)
    # No errcheck on this getter; the Info call already does the heavy lifting.

except AttributeError:
    _CONTEXT_COLORMAP_AVAILABLE = False


def _require_ctx_colormap():
    if not _CONTEXT_COLORMAP_AVAILABLE:
        raise NotImplementedError(_NOT_AVAILABLE_COLORMAP_MSG)


def generateColormapNamedWrapper(context, name: str, n_colors: int):
    """Return a flat list of (n_colors * 3) RGB floats."""
    _require_ctx_colormap()
    count = ctypes.c_uint()
    ptr = helios_lib.generateColormapNamed(context, name.encode('utf-8'), int(n_colors), ctypes.byref(count))
    n = count.value
    if n == 0 or not ptr:
        return []
    return [float(ptr[i]) for i in range(n * 3)]


def generateTexturesFromColormapWrapper(context, texture_file: str, colormap_rgb_flat: List[float]) -> List[str]:
    """Generate textures from a colormap; return the list of generated file paths."""
    _require_ctx_colormap()
    if len(colormap_rgb_flat) % 3 != 0:
        raise ValueError(f"colormap_rgb_flat length must be a multiple of 3, got {len(colormap_rgb_flat)}")
    n_colors = len(colormap_rgb_flat) // 3
    arr = (ctypes.c_float * len(colormap_rgb_flat))(*[float(v) for v in colormap_rgb_flat]) if n_colors > 0 else (ctypes.c_float * 1)()
    count = int(helios_lib.generateTexturesFromColormapCount(context, texture_file.encode('utf-8'), arr, n_colors))
    return [
        _read_string_buffer(helios_lib.generateTexturesFromColormapPath, context, i)
        for i in range(count)
    ]


def getPrimitiveTextureTransparencyDataWrapper(context, uuid: int):
    """Return (width, height, flat_byte_list) or None if no transparency channel."""
    _require_ctx_colormap()
    width = ctypes.c_uint()
    height = ctypes.c_uint()
    has_data = int(helios_lib.getPrimitiveTextureTransparencyDataInfo(
        context, int(uuid), ctypes.byref(width), ctypes.byref(height)
    ))
    if has_data == 0 or width.value == 0 or height.value == 0:
        return None
    ptr = helios_lib.getPrimitiveTextureTransparencyDataBuffer(context, int(uuid))
    if not ptr:
        return None
    n = width.value * height.value
    flat = [int(ptr[i]) for i in range(n)]
    return (int(width.value), int(height.value), flat)
