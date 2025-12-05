import ctypes
from typing import List

from .UContextWrapper import UContext
from ..plugins import helios_lib
from ..exceptions import check_helios_error


# Define the UWeberPennTree struct
class UWeberPennTree(ctypes.Structure):
    pass

# Automatic error checking callback
def _check_error_wpt(result, func, args):
    """
    Errcheck callback that automatically checks for Helios errors after each WeberPennTree function call.
    This ensures that C++ exceptions are properly converted to Python exceptions.
    """
    check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage)
    return result

# Try to set up WeberPennTree function prototypes
try:
    helios_lib.createWeberPennTree.argtypes = [ctypes.POINTER(UContext)]
    helios_lib.createWeberPennTree.restype = ctypes.POINTER(UWeberPennTree)

    helios_lib.createWeberPennTreeWithBuildPluginRootDirectory.argtypes = [ctypes.POINTER(UContext), ctypes.c_char_p]
    helios_lib.createWeberPennTreeWithBuildPluginRootDirectory.restype = ctypes.POINTER(UWeberPennTree)

    helios_lib.destroyWeberPennTree.argtypes = [ctypes.POINTER(UWeberPennTree)]

    helios_lib.buildTree.argtypes = [ctypes.POINTER(UWeberPennTree), ctypes.c_char_p, ctypes.POINTER(ctypes.c_float)]
    helios_lib.buildTree.restype = ctypes.c_uint
    
    helios_lib.buildTreeWithScale.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_float), ctypes.c_float]
    helios_lib.buildTreeWithScale.restype = ctypes.c_uint

    helios_lib.getWeberPennTreeTrunkUUIDs.argtypes = [ctypes.POINTER(UWeberPennTree), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getWeberPennTreeTrunkUUIDs.restype = ctypes.POINTER(ctypes.c_uint)

    helios_lib.getWeberPennTreeBranchUUIDs.argtypes = [ctypes.POINTER(UWeberPennTree), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getWeberPennTreeBranchUUIDs.restype = ctypes.POINTER(ctypes.c_uint)

    helios_lib.getWeberPennTreeLeafUUIDs.argtypes = [ctypes.POINTER(UWeberPennTree), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getWeberPennTreeLeafUUIDs.restype = ctypes.POINTER(ctypes.c_uint)

    helios_lib.getWeberPennTreeAllUUIDs.argtypes = [ctypes.POINTER(UWeberPennTree), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getWeberPennTreeAllUUIDs.restype = ctypes.POINTER(ctypes.c_uint)

    helios_lib.setBranchRecursionLevel.argtypes = [ctypes.POINTER(UWeberPennTree), ctypes.c_uint]
    helios_lib.setTrunkSegmentResolution.argtypes = [ctypes.POINTER(UWeberPennTree), ctypes.c_uint]
    helios_lib.setBranchSegmentResolution.argtypes = [ctypes.POINTER(UWeberPennTree), ctypes.c_uint]
    helios_lib.setLeafSubdivisions.argtypes = [ctypes.POINTER(UWeberPennTree), ctypes.c_uint, ctypes.c_uint]

    helios_lib.loadXMLWeberPennTree.argtypes = [ctypes.POINTER(UWeberPennTree), ctypes.c_char_p, ctypes.c_bool]
    helios_lib.loadXMLWeberPennTree.restype = None

    # Add automatic error checking to all WeberPennTree functions
    helios_lib.createWeberPennTree.errcheck = _check_error_wpt
    helios_lib.createWeberPennTreeWithBuildPluginRootDirectory.errcheck = _check_error_wpt
    helios_lib.buildTree.errcheck = _check_error_wpt
    helios_lib.buildTreeWithScale.errcheck = _check_error_wpt
    helios_lib.getWeberPennTreeTrunkUUIDs.errcheck = _check_error_wpt
    helios_lib.getWeberPennTreeBranchUUIDs.errcheck = _check_error_wpt
    helios_lib.getWeberPennTreeLeafUUIDs.errcheck = _check_error_wpt
    helios_lib.getWeberPennTreeAllUUIDs.errcheck = _check_error_wpt
    helios_lib.setBranchRecursionLevel.errcheck = _check_error_wpt
    helios_lib.setTrunkSegmentResolution.errcheck = _check_error_wpt
    helios_lib.setBranchSegmentResolution.errcheck = _check_error_wpt
    helios_lib.setLeafSubdivisions.errcheck = _check_error_wpt
    helios_lib.loadXMLWeberPennTree.errcheck = _check_error_wpt

    _WPT_FUNCTIONS_AVAILABLE = True
except AttributeError:
    _WPT_FUNCTIONS_AVAILABLE = False

# Function definitions
def createWeberPennTree(context : UContext):
    if not _WPT_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("WeberPennTree functions not available in current Helios library.")
    return helios_lib.createWeberPennTree(context)

def createWeberPennTreeWithBuildPluginRootDirectory(context : UContext , buildDirectory:str):
    if not _WPT_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("WeberPennTree functions not available in current Helios library.")
    buildDirectory_bytes = buildDirectory.encode("utf-8")
    return helios_lib.createWeberPennTreeWithBuildPluginRootDirectory(context, buildDirectory_bytes)

def destroyWeberPennTree(uweberPennTree):
    if not _WPT_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("WeberPennTree functions not available in current Helios library.")
    helios_lib.destroyWeberPennTree(uweberPennTree)

def buildTree(uweberPennTree, treename: str, origin: List[float]):
    if not _WPT_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("WeberPennTree functions not available in current Helios library.")
    return helios_lib.buildTree(uweberPennTree, treename.encode('utf-8'), (ctypes.c_float * len(origin))(*origin))

def buildTreeWithScale(uweberPennTree, treename, origin, scale):
    if not _WPT_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("WeberPennTree functions not available in current Helios library.")
    treename_bytes = treename.encode("utf-8")
    origin_ptr = (ctypes.c_float * 3)(*origin)
    return helios_lib.buildTreeWithScale(uweberPennTree, treename_bytes, origin_ptr, scale)

def getTrunkUUIDs(uweberPennTree, treeID: int):
    if not _WPT_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("WeberPennTree functions not available in current Helios library.")
    size = ctypes.c_uint()
    uuids_ptr = helios_lib.getWeberPennTreeTrunkUUIDs(uweberPennTree, treeID, ctypes.byref(size))
    uuids = [uuids_ptr[i] for i in range(size.value)]
    return uuids

def getBranchUUIDs(uweberPennTree, treeID: int):
    if not _WPT_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("WeberPennTree functions not available in current Helios library.")
    size = ctypes.c_uint()
    uuids_ptr = helios_lib.getWeberPennTreeBranchUUIDs(uweberPennTree, treeID, ctypes.byref(size))
    uuids = [uuids_ptr[i] for i in range(size.value)]
    return uuids

def getLeafUUIDs(uweberPennTree, treeID: int):
    if not _WPT_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("WeberPennTree functions not available in current Helios library.")
    size = ctypes.c_uint()
    uuids_ptr = helios_lib.getWeberPennTreeLeafUUIDs(uweberPennTree, treeID, ctypes.byref(size))
    uuids = [uuids_ptr[i] for i in range(size.value)]
    return uuids

def getAllUUIDs(uweberPennTree, treeID: int):
    if not _WPT_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("WeberPennTree functions not available in current Helios library.")
    size = ctypes.c_uint()
    uuids_ptr = helios_lib.getWeberPennTreeAllUUIDs(uweberPennTree, treeID, ctypes.byref(size))
    uuids = [uuids_ptr[i] for i in range(size.value)]
    return uuids

def setBranchRecursionLevel(uweberPennTree, level: int):
    if not _WPT_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("WeberPennTree functions not available in current Helios library.")
    helios_lib.setBranchRecursionLevel(uweberPennTree, level)

def setTrunkSegmentResolution(uweberPennTree, trunk_segs: int):
    if not _WPT_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("WeberPennTree functions not available in current Helios library.")
    helios_lib.setTrunkSegmentResolution(uweberPennTree, trunk_segs)

def setBranchSegmentResolution(uweberPennTree, branch_segs: int):
    if not _WPT_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("WeberPennTree functions not available in current Helios library.")
    helios_lib.setBranchSegmentResolution(uweberPennTree, branch_segs)

def setLeafSubdivisions(uweberPennTree, leaf_segs_x: int, leaf_segs_y: int):
    if not _WPT_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("WeberPennTree functions not available in current Helios library.")
    helios_lib.setLeafSubdivisions(uweberPennTree, leaf_segs_x, leaf_segs_y)

def loadXML(uweberPennTree, filename: str, silent: bool = False):
    if not _WPT_FUNCTIONS_AVAILABLE:
        raise NotImplementedError("WeberPennTree functions not available in current Helios library.")
    filename_bytes = filename.encode('utf-8')
    helios_lib.loadXMLWeberPennTree(uweberPennTree, filename_bytes, silent)