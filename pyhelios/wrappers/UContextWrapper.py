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
    helios_lib.doesPrimitiveDataExist.restype = ctypes.c_int
    
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

    # Mark that primitive data functions are available
    _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE = True

except AttributeError:
    # Primitive data functions not available in current native library
    _PRIMITIVE_DATA_FUNCTIONS_AVAILABLE = False

# Try to set up PLY loading function prototypes separately
try:
    # Note: loadPLY function is defined separately outside this try block
    # Only define the specific variant functions here
    
    helios_lib.loadPLYWithOriginHeight.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.POINTER(ctypes.c_float), ctypes.c_float, ctypes.c_char_p, ctypes.c_bool, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.loadPLYWithOriginHeight.restype = ctypes.POINTER(ctypes.c_uint)
    
    helios_lib.loadPLYWithOriginHeightRotation.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.POINTER(ctypes.c_float), ctypes.c_float, ctypes.POINTER(ctypes.c_float), ctypes.c_char_p, ctypes.c_bool, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.loadPLYWithOriginHeightRotation.restype = ctypes.POINTER(ctypes.c_uint)
    
    helios_lib.loadPLYWithOriginHeightColor.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.POINTER(ctypes.c_float), ctypes.c_float, ctypes.POINTER(ctypes.c_float), ctypes.c_char_p, ctypes.c_bool, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.loadPLYWithOriginHeightColor.restype = ctypes.POINTER(ctypes.c_uint)
    
    helios_lib.loadPLYWithOriginHeightRotationColor.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p, ctypes.POINTER(ctypes.c_float), ctypes.c_float, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_char_p, ctypes.c_bool, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.loadPLYWithOriginHeightRotationColor.restype = ctypes.POINTER(ctypes.c_uint)
    
    # Mark that PLY loading functions are available
    _PLY_LOADING_FUNCTIONS_AVAILABLE = True

except AttributeError:
    # PLY loading functions not available in current native library
    _PLY_LOADING_FUNCTIONS_AVAILABLE = False

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

    # Mark that OBJ/XML loading functions are available
    _OBJ_XML_LOADING_FUNCTIONS_AVAILABLE = True

except AttributeError:
    # OBJ/XML loading functions not available in current native library
    _OBJ_XML_LOADING_FUNCTIONS_AVAILABLE = False

# For backward compatibility, set this to True if PLY functions are available  
_FILE_LOADING_FUNCTIONS_AVAILABLE = _PLY_LOADING_FUNCTIONS_AVAILABLE

# Try to set up triangle function prototypes separately
try:
    # addTriangle function prototypes
    helios_lib.addTriangle.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.addTriangle.restype = ctypes.c_uint
    helios_lib.addTriangle.errcheck = _check_error
    
    helios_lib.addTriangleWithColor.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.addTriangleWithColor.restype = ctypes.c_uint
    helios_lib.addTriangleWithColor.errcheck = _check_error
    
    helios_lib.addTriangleWithColorRGBA.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.addTriangleWithColorRGBA.restype = ctypes.c_uint
    helios_lib.addTriangleWithColorRGBA.errcheck = _check_error
    
    helios_lib.addTriangleWithTexture.argtypes = [ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_char_p, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.addTriangleWithTexture.restype = ctypes.c_uint
    helios_lib.addTriangleWithTexture.errcheck = _check_error

    # Mark that triangle functions are available
    _TRIANGLE_FUNCTIONS_AVAILABLE = True

except AttributeError:
    # Triangle functions not available in current native library
    _TRIANGLE_FUNCTIONS_AVAILABLE = False

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
    uuids_ptr = helios_lib.loadPLY(context, filename_encoded, silent, ctypes.byref(size))
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
    if not _TRIANGLE_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("Triangle functions not available in current Helios library. These require updated C++ wrapper implementation.")
    vertex0_ptr = (ctypes.c_float * len(vertex0))(*vertex0)
    vertex1_ptr = (ctypes.c_float * len(vertex1))(*vertex1)
    vertex2_ptr = (ctypes.c_float * len(vertex2))(*vertex2)
    texture_file_encoded = texture_file.encode('utf-8')
    uv0_ptr = (ctypes.c_float * len(uv0))(*uv0)
    uv1_ptr = (ctypes.c_float * len(uv1))(*uv1)
    uv2_ptr = (ctypes.c_float * len(uv2))(*uv2)
    return helios_lib.addTriangleWithTexture(context, vertex0_ptr, vertex1_ptr, vertex2_ptr, texture_file_encoded, uv0_ptr, uv1_ptr, uv2_ptr)

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
    result = helios_lib.doesPrimitiveDataExist(context, uuid, label_encoded)
    return result == 1

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


