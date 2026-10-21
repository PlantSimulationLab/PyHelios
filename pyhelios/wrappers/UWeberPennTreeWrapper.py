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
    check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage, helios_lib.clearError)
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

# Flat-array layout used to exchange WeberPennTreeParameters with the native library.
# The order must match native/include/pyhelios_wrapper_weberpenntree.h.
WPT_PARAM_FLOAT_FIELDS = (
    'BaseSize', 'BaseSizeV', 'BaseSplitSize', 'BaseSplitSizeV', 'Scale', 'ScaleV', 'ZScale', 'ZScaleV',
    'Ratio', 'RatioPower', 'LobeDepth', 'Flare', 'LeafScale', 'LeafScaleX',
)  # followed by WoodColor.r, WoodColor.g, WoodColor.b
WPT_PARAM_NUM_FLOATS = len(WPT_PARAM_FLOAT_FIELDS) + 3
WPT_PARAM_INT_FIELDS = ('Shape', 'BaseSplits', 'BaseSplitsV', 'Lobes', 'Levels', 'Leaves', 'LeafShape')
WPT_PARAM_FLOAT_VECTOR_FIELDS = (
    'nSegSplits', 'nSplitAngle', 'nSplitAngleV', 'nCurve', 'nCurveV', 'nCurveBack', 'nLength', 'nLengthV',
    'nTaper', 'nDownAngle', 'nDownAngleV', 'nRotate', 'nRotateV', 'leafAngleCDF',
)
WPT_PARAM_INT_VECTOR_FIELDS = ('nCurveRes', 'nBranches')
WPT_PARAM_STRING_FIELDS = ('label', 'LeafFile', 'WoodFile')

try:
    helios_lib.getWeberPennTreeParameters.argtypes = [
        ctypes.POINTER(UWeberPennTree), ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int64),
        ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.POINTER(ctypes.c_float)),
        ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.POINTER(ctypes.c_int)),
        ctypes.POINTER(ctypes.c_char_p),
    ]
    helios_lib.getWeberPennTreeParameters.restype = None
    helios_lib.getWeberPennTreeParameters.errcheck = _check_error_wpt

    helios_lib.setWeberPennTreeParameters.argtypes = [
        ctypes.POINTER(UWeberPennTree), ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int64),
        ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_int),
        ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
    ]
    helios_lib.setWeberPennTreeParameters.restype = None
    helios_lib.setWeberPennTreeParameters.errcheck = _check_error_wpt

    helios_lib.seedWeberPennTreeRandomGenerator.argtypes = [ctypes.POINTER(UWeberPennTree), ctypes.c_uint]
    helios_lib.seedWeberPennTreeRandomGenerator.restype = None
    helios_lib.seedWeberPennTreeRandomGenerator.errcheck = _check_error_wpt

    _WPT_PARAMETER_FUNCTIONS_AVAILABLE = True
except AttributeError:
    _WPT_PARAMETER_FUNCTIONS_AVAILABLE = False

_WPT_PARAMETER_UNAVAILABLE_MSG = (
    "WeberPennTree parameter/seed functions are not available in the current Helios library. "
    "Rebuild PyHelios with the weberpenntree plugin: build_scripts/build_helios"
)

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

def getTreeParameters(uweberPennTree, treename: str) -> dict:
    """Return the raw parameter fields of a tree as a dict keyed by C++ field name.

    WoodColor is returned as a list [r, g, b]; vectors as lists.
    """
    if not _WPT_PARAMETER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_WPT_PARAMETER_UNAVAILABLE_MSG)
    scalars = (ctypes.c_float * WPT_PARAM_NUM_FLOATS)()
    ints = (ctypes.c_int64 * len(WPT_PARAM_INT_FIELDS))()
    fvec_lengths = (ctypes.c_uint * len(WPT_PARAM_FLOAT_VECTOR_FIELDS))()
    fvec_data = ctypes.POINTER(ctypes.c_float)()
    ivec_lengths = (ctypes.c_uint * len(WPT_PARAM_INT_VECTOR_FIELDS))()
    ivec_data = ctypes.POINTER(ctypes.c_int)()
    strings = (ctypes.c_char_p * len(WPT_PARAM_STRING_FIELDS))()

    helios_lib.getWeberPennTreeParameters(
        uweberPennTree, treename.encode('utf-8'), scalars, ints,
        fvec_lengths, ctypes.byref(fvec_data), ivec_lengths, ctypes.byref(ivec_data), strings)

    result = {}
    for i, name in enumerate(WPT_PARAM_FLOAT_FIELDS):
        result[name] = scalars[i]
    n = len(WPT_PARAM_FLOAT_FIELDS)
    result['WoodColor'] = [scalars[n], scalars[n + 1], scalars[n + 2]]
    for i, name in enumerate(WPT_PARAM_INT_FIELDS):
        result[name] = int(ints[i])
    offset = 0
    for i, name in enumerate(WPT_PARAM_FLOAT_VECTOR_FIELDS):
        length = fvec_lengths[i]
        result[name] = [fvec_data[offset + j] for j in range(length)]
        offset += length
    offset = 0
    for i, name in enumerate(WPT_PARAM_INT_VECTOR_FIELDS):
        length = ivec_lengths[i]
        result[name] = [int(ivec_data[offset + j]) for j in range(length)]
        offset += length
    for i, name in enumerate(WPT_PARAM_STRING_FIELDS):
        value = strings[i]
        result[name] = value.decode('utf-8') if value is not None else ''
    return result


def setTreeParameters(uweberPennTree, treename: str, fields: dict) -> None:
    """Set a tree's parameters from a dict keyed by C++ field name (same layout as getTreeParameters)."""
    if not _WPT_PARAMETER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_WPT_PARAMETER_UNAVAILABLE_MSG)
    scalar_values = [fields[name] for name in WPT_PARAM_FLOAT_FIELDS] + list(fields['WoodColor'])
    scalars = (ctypes.c_float * WPT_PARAM_NUM_FLOATS)(*scalar_values)
    ints = (ctypes.c_int64 * len(WPT_PARAM_INT_FIELDS))(*[fields[name] for name in WPT_PARAM_INT_FIELDS])

    fvecs = [list(fields[name]) for name in WPT_PARAM_FLOAT_VECTOR_FIELDS]
    fvec_lengths = (ctypes.c_uint * len(fvecs))(*[len(v) for v in fvecs])
    flat_f = [x for v in fvecs for x in v]
    fvec_data = (ctypes.c_float * max(len(flat_f), 1))(*flat_f)

    ivecs = [list(fields[name]) for name in WPT_PARAM_INT_VECTOR_FIELDS]
    ivec_lengths = (ctypes.c_uint * len(ivecs))(*[len(v) for v in ivecs])
    flat_i = [x for v in ivecs for x in v]
    ivec_data = (ctypes.c_int * max(len(flat_i), 1))(*flat_i)

    helios_lib.setWeberPennTreeParameters(
        uweberPennTree, treename.encode('utf-8'), scalars, ints,
        fvec_lengths, fvec_data, ivec_lengths, ivec_data,
        fields['label'].encode('utf-8'), fields['LeafFile'].encode('utf-8'), fields['WoodFile'].encode('utf-8'))


def seedRandomGenerator(uweberPennTree, seed: int) -> None:
    if not _WPT_PARAMETER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(_WPT_PARAMETER_UNAVAILABLE_MSG)
    helios_lib.seedWeberPennTreeRandomGenerator(uweberPennTree, seed)
