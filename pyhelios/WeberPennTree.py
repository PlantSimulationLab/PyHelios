# import ctypes
# from pyhelios import Context
# from wrappers import UWeberPennTreeWrapper as wpt_wrapper
# from enum import Enum
# from typing import List
# from wrappers import Vec3

import ctypes
import math
import os
from contextlib import contextmanager
from dataclasses import dataclass, field, fields as dataclass_fields
from enum import Enum
from pathlib import Path
from typing import List, Union

from .wrappers import UWeberPennTreeWrapper as wpt_wrapper
from .wrappers.DataTypes import vec3, RGBcolor
from .plugins.registry import get_plugin_registry, graceful_plugin_fallback
from .validation.plugins import validate_wpt_parameters
from .validation.datatypes import validate_vec3
from .validation.core import validate_positive_value
from .assets import get_asset_manager
from .validation.plugin_decorators import (
    validate_tree_uuid_params, validate_recursion_params, validate_trunk_segment_params,
    validate_branch_segment_params, validate_leaf_subdivisions_params, validate_xml_file_params
)


def is_weberpenntree_available():
    """
    Check if WeberPennTree plugin is available for use.
    
    Returns:
        bool: True if WeberPennTree can be used, False otherwise
    """
    try:
        # Check plugin registry
        plugin_registry = get_plugin_registry()
        if not plugin_registry.is_plugin_available('weberpenntree'):
            return False
        
        # Check if wrapper functions are available
        if not wpt_wrapper._WPT_FUNCTIONS_AVAILABLE:
            return False
            
        return True
    except Exception:
        return False

from .Context import Context, check_context_alive

@contextmanager
def _weberpenntree_working_directory():
    """
    Context manager that temporarily changes working directory to where WeberPennTree assets are located.
    
    WeberPennTree C++ code uses hardcoded relative paths like "plugins/weberpenntree/xml/WeberPennTreeLibrary.xml"
    expecting assets relative to working directory. This manager temporarily changes to the build directory
    where assets are actually located.
    
    Raises:
        RuntimeError: If build directory or WeberPennTree assets are not found, indicating a build system error.
    """
    # Find the build directory containing WeberPennTree assets
    # Try asset manager first (works for both development and wheel installations)
    asset_manager = get_asset_manager()
    working_dir = asset_manager._get_helios_build_path()
    
    if working_dir and working_dir.exists():
        weberpenntree_assets = working_dir / 'plugins' / 'weberpenntree'
    else:
        # For wheel installations, check packaged assets  
        current_dir = Path(__file__).parent
        packaged_build = current_dir / 'assets' / 'build'
        
        if packaged_build.exists():
            working_dir = packaged_build
            weberpenntree_assets = working_dir / 'plugins' / 'weberpenntree'
        else:
            # Fallback to development paths
            repo_root = current_dir.parent
            build_lib_dir = repo_root / 'pyhelios_build' / 'build' / 'lib'
            working_dir = build_lib_dir.parent
            weberpenntree_assets = working_dir / 'plugins' / 'weberpenntree'
            
            if not build_lib_dir.exists():
                raise RuntimeError(
                    f"PyHelios build directory not found: {build_lib_dir}. "
                    f"WeberPennTree requires native libraries to be built. "
                    f"Run: python build_scripts/build_helios.py --plugins weberpenntree"
                )
    
    if not weberpenntree_assets.exists():
        raise RuntimeError(
            f"WeberPennTree assets not found: {weberpenntree_assets}. "
            f"Build system failed to copy WeberPennTree assets. "
            f"Run: python build_scripts/build_helios.py --clean --plugins weberpenntree"
        )
    
    xml_file = weberpenntree_assets / 'xml' / 'WeberPennTreeLibrary.xml'
    if not xml_file.exists():
        raise RuntimeError(
            f"WeberPennTree XML library not found: {xml_file}. "
            f"Critical WeberPennTree asset missing from build. "
            f"Run: python build_scripts/build_helios.py --clean --plugins weberpenntree"
        )
    
    # Change to build directory where assets are located
    original_cwd = Path.cwd()
    try:
        os.chdir(working_dir)
        yield
    finally:
        os.chdir(original_cwd)

class WPTType(Enum):
    ALMOND = 'Almond'
    APPLE = 'Apple'
    AVOCADO = 'Avocado'
    LEMON = 'Lemon'
    OLIVE = 'Olive'
    ORANGE = 'Orange'
    PEACH = 'Peach'
    PISTACHIO = 'Pistachio'
    WALNUT = 'Walnut'

_INT32_MIN, _INT32_MAX = -2**31, 2**31 - 1
_UINT32_MAX = 2**32 - 1
_MAX_LEVELS = 3

# Per-level arrays: indexed by recursion level, so each needs at least Levels+1 entries.
_PER_LEVEL_FLOAT_FIELDS = (
    'nSegSplits', 'nSplitAngle', 'nSplitAngleV', 'nCurve', 'nCurveV', 'nCurveBack', 'nLength', 'nLengthV',
    'nTaper', 'nDownAngle', 'nDownAngleV', 'nRotate', 'nRotateV',
)
_PER_LEVEL_INT_FIELDS = ('nCurveRes', 'nBranches')
_SCALAR_FLOAT_FIELDS = (
    'BaseSize', 'BaseSizeV', 'BaseSplitSize', 'BaseSplitSizeV', 'Scale', 'ScaleV', 'ZScale', 'ZScaleV',
    'Ratio', 'RatioPower', 'LobeDepth', 'Flare', 'LeafScale', 'LeafScaleX',
)
_SCALAR_INT_FIELDS = ('Shape', 'Lobes', 'Levels', 'Leaves', 'LeafShape')
_SCALAR_UINT_FIELDS = ('BaseSplits', 'BaseSplitsV')
_STRING_FIELDS = ('label', 'LeafFile', 'WoodFile')


@dataclass(eq=False)
class WeberPennTreeParameters:
    """
    Architectural parameters of a Weber-Penn tree, mirroring the C++ ``WeberPennTreeParameters`` struct.

    Field names and meanings are identical to the C++ struct and to the tags of the XML tree library
    (see the "Creating Custom XML Files" section of the plugin documentation). Per-level arrays
    (``nSegSplits`` ... ``nBranches``) are indexed by recursion level (0 = trunk) and must hold at least
    ``Levels + 1`` entries. ``leafAngleCDF`` is the cumulative leaf inclination distribution computed from
    the XML ``LeafAngleDist`` tag (empty means uniform). Float values are stored as 32-bit floats natively.

    The usual way to obtain one is :meth:`WeberPennTree.getTreeParameters`, modify it, and pass it to
    :meth:`WeberPennTree.setTreeParameters`.
    """
    label: str = ''
    Shape: int = 0
    BaseSize: float = 0.0
    BaseSizeV: float = 0.0
    BaseSplits: int = 0
    BaseSplitsV: int = 0
    BaseSplitSize: float = 0.0
    BaseSplitSizeV: float = 0.0
    Scale: float = 0.0
    ScaleV: float = 0.0
    ZScale: float = 0.0
    ZScaleV: float = 0.0
    Ratio: float = 0.0
    RatioPower: float = 0.0
    Lobes: int = 0
    LobeDepth: float = 0.0
    Flare: float = 0.0
    Levels: int = 0
    nSegSplits: List[float] = field(default_factory=list)
    nSplitAngle: List[float] = field(default_factory=list)
    nSplitAngleV: List[float] = field(default_factory=list)
    nCurveRes: List[int] = field(default_factory=list)
    nCurve: List[float] = field(default_factory=list)
    nCurveV: List[float] = field(default_factory=list)
    nCurveBack: List[float] = field(default_factory=list)
    nLength: List[float] = field(default_factory=list)
    nLengthV: List[float] = field(default_factory=list)
    nTaper: List[float] = field(default_factory=list)
    nDownAngle: List[float] = field(default_factory=list)
    nDownAngleV: List[float] = field(default_factory=list)
    nRotate: List[float] = field(default_factory=list)
    nRotateV: List[float] = field(default_factory=list)
    nBranches: List[int] = field(default_factory=list)
    LeafFile: str = ''
    Leaves: int = 0
    LeafShape: int = 0
    LeafScale: float = 0.0
    LeafScaleX: float = 0.0
    WoodColor: RGBcolor = field(default_factory=lambda: RGBcolor(0.4, 0.2, 0.05))
    WoodFile: str = 'none'
    leafAngleCDF: List[float] = field(default_factory=list)

    def __eq__(self, other):
        if not isinstance(other, WeberPennTreeParameters):
            return NotImplemented
        for f in dataclass_fields(self):
            a, b = getattr(self, f.name), getattr(other, f.name)
            if f.name == 'WoodColor':
                if not (isinstance(a, RGBcolor) and isinstance(b, RGBcolor)) or a.to_list() != b.to_list():
                    return False
            elif isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
                if list(a) != list(b):
                    return False
            elif a != b:
                return False
        return True

    def _to_wrapper_fields(self) -> dict:
        result = {f.name: getattr(self, f.name) for f in dataclass_fields(self)}
        result['WoodColor'] = self.WoodColor.to_list()
        return result

    @classmethod
    def _from_wrapper_fields(cls, raw: dict) -> 'WeberPennTreeParameters':
        values = dict(raw)
        wood = values['WoodColor']
        color = RGBcolor()
        color.r, color.g, color.b = wood[0], wood[1], wood[2]
        values['WoodColor'] = color
        return cls(**values)

    def validate(self) -> None:
        """
        Check field types, ranges and per-level array lengths.

        Raises:
            ValueError: If any field has the wrong type, is out of range, or a per-level array is too short.
        """
        def is_int(v):
            return isinstance(v, int) and not isinstance(v, bool)

        def is_real(v):
            return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)

        for name in _STRING_FIELDS:
            v = getattr(self, name)
            if not isinstance(v, str):
                raise ValueError(f"WeberPennTreeParameters.{name} must be a str, got {type(v).__name__}")
            if '\x00' in v:
                raise ValueError(f"WeberPennTreeParameters.{name} must not contain NUL characters")
        for name in _SCALAR_FLOAT_FIELDS:
            v = getattr(self, name)
            if not is_real(v):
                raise ValueError(f"WeberPennTreeParameters.{name} must be a finite number, got {type(v).__name__}: {v!r}")
        for name in _SCALAR_INT_FIELDS:
            v = getattr(self, name)
            if not is_int(v) or not (_INT32_MIN <= v <= _INT32_MAX):
                raise ValueError(f"WeberPennTreeParameters.{name} must be a 32-bit int, got {type(v).__name__}: {v!r}")
        for name in _SCALAR_UINT_FIELDS:
            v = getattr(self, name)
            if not is_int(v) or not (0 <= v <= _UINT32_MAX):
                raise ValueError(f"WeberPennTreeParameters.{name} must be a non-negative 32-bit int, got {type(v).__name__}: {v!r}")
        if not isinstance(self.WoodColor, RGBcolor):
            raise ValueError(f"WeberPennTreeParameters.WoodColor must be an RGBcolor, got {type(self.WoodColor).__name__}")
        for name in _PER_LEVEL_FLOAT_FIELDS + ('leafAngleCDF',):
            v = getattr(self, name)
            if not isinstance(v, (list, tuple)) or not all(is_real(x) for x in v):
                raise ValueError(f"WeberPennTreeParameters.{name} must be a list of finite numbers, got {v!r}")
        for name in _PER_LEVEL_INT_FIELDS:
            v = getattr(self, name)
            if not isinstance(v, (list, tuple)) or not all(is_int(x) and _INT32_MIN <= x <= _INT32_MAX for x in v):
                raise ValueError(f"WeberPennTreeParameters.{name} must be a list of 32-bit ints, got {v!r}")

        if not (1 <= self.Levels <= _MAX_LEVELS):
            raise ValueError(
                f"WeberPennTreeParameters.Levels is {self.Levels}, but it must be between 1 and {_MAX_LEVELS} "
                f"(level 0 is the trunk and leaves are placed at level Levels)."
            )
        required = self.Levels + 1
        for name in _PER_LEVEL_FLOAT_FIELDS + _PER_LEVEL_INT_FIELDS:
            n = len(getattr(self, name))
            if n < required:
                raise ValueError(
                    f"WeberPennTreeParameters.{name} has {n} entries, but Levels={self.Levels} requires at least {required}."
                )


class WeberPennTree:
    WPTType = WPTType  # Make WPTType accessible as class attribute
    
    def __init__(self, context:Context):
        self.context = context
        self._plugin_registry = get_plugin_registry()
        
        # Check if weberpenntree functions are available at the wrapper level first
        from .wrappers.UWeberPennTreeWrapper import _WPT_FUNCTIONS_AVAILABLE
        if not _WPT_FUNCTIONS_AVAILABLE:
            raise NotImplementedError("WeberPennTree functions not available in current Helios library.")
        
        # Check if weberpenntree plugin is available in registry
        if not self._plugin_registry.is_plugin_available('weberpenntree'):
            print("Warning: WeberPennTree plugin not detected in current build")
            print("Tree generation functionality may be limited or unavailable")
        
        # Find build directory for asset loading using asset manager
        asset_manager = get_asset_manager()
        build_dir = asset_manager._get_helios_build_path()
        
        if not build_dir or not build_dir.exists():
            # In wheel installations, try packaged assets location
            current_dir = Path(__file__).parent
            packaged_build = current_dir / 'assets' / 'build'
            
            if packaged_build.exists() and (packaged_build / 'plugins' / 'weberpenntree').exists():
                build_dir = packaged_build
            else:
                # Fallback to development build directory  
                repo_root = current_dir.parent
                build_lib_dir = repo_root / 'pyhelios_build' / 'build' / 'lib'
                build_dir = build_lib_dir.parent
                
                if not build_dir.exists():
                    raise RuntimeError(
                        f"PyHelios build directory not found: {build_dir}. "
                        f"WeberPennTree requires native libraries to be built. "
                        f"Run: python build_scripts/build_helios.py --plugins weberpenntree"
                    )
        
        # Use the same build_dir for working directory as we use for C++ interface
        # This ensures consistency between Python working directory and C++ asset paths
        original_cwd = Path.cwd()
        try:
            os.chdir(build_dir)
            self.wpt = wpt_wrapper.createWeberPennTreeWithBuildPluginRootDirectory(
                context.getNativePtr(), str(build_dir)
            )
        finally:
            os.chdir(original_cwd)
    
    def _check_context_alive(self):
        """Raise if the owning Context has been destroyed (see Context.check_context_alive)."""
        check_context_alive(getattr(self, "context", None), "WeberPennTree")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.wpt is not None:
            try:
                wpt_wrapper.destroyWeberPennTree(self.wpt)
            finally:
                self.wpt = None  # Prevent double deletion

    def __del__(self):
        """Destructor to ensure C++ resources freed even without 'with' statement."""
        if hasattr(self, 'wpt') and self.wpt is not None:
            try:
                wpt_wrapper.destroyWeberPennTree(self.wpt)
                self.wpt = None
            except Exception as e:
                import warnings
                warnings.warn(f"Error in WeberPennTree.__del__: {e}")

    def getNativePtr(self):
        return self.wpt


    def buildTree(self, wpt_type, origin:vec3=vec3(0, 0, 0), scale:float=1) -> int:
        """
        Build a tree using either a built-in tree type or custom species name.

        Args:
            wpt_type: Either WPTType enum for built-in types, or string for custom species loaded via loadXML()
            origin: Tree origin position (default: vec3(0, 0, 0))
            scale: Tree scale factor (default: 1.0)

        Returns:
            Tree ID for querying tree components
        """
        # Validate inputs
        validate_vec3(origin, "origin", "buildTree")
        validate_positive_value(scale, "scale", "buildTree")

        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError(
                f"WeberPennTree is not properly initialized. "
                f"This may indicate that the weberpenntree plugin is not available. "
                f"Check plugin status with context.print_plugin_status()"
            )

        # Convert wpt_type to string (handle both WPTType enum and string)
        if isinstance(wpt_type, WPTType):
            tree_name = wpt_type.value
        elif isinstance(wpt_type, str):
            tree_name = wpt_type
        else:
            raise TypeError(f"wpt_type must be WPTType enum or string, got {type(wpt_type).__name__}")

        # Use working directory context manager during tree building to access assets
        with _weberpenntree_working_directory():
            # Use scale-aware function if scale is not 1.0, otherwise use regular function
            if scale != 1.0:
                self._check_context_alive()
                return wpt_wrapper.buildTreeWithScale(self.wpt, tree_name, origin.to_list(), scale)
            else:
                self._check_context_alive()
                return wpt_wrapper.buildTree(self.wpt, tree_name, origin.to_list())
    
    @validate_tree_uuid_params
    def getTrunkUUIDs(self, tree_id:int) -> List[int]:
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        self._check_context_alive()
        return wpt_wrapper.getTrunkUUIDs(self.wpt, tree_id)
    
    @validate_tree_uuid_params
    def getBranchUUIDs(self, tree_id:int) -> List[int]:
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        self._check_context_alive()
        return wpt_wrapper.getBranchUUIDs(self.wpt, tree_id)
    
    @validate_tree_uuid_params
    def getLeafUUIDs(self, tree_id:int) -> List[int]:
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        self._check_context_alive()
        return wpt_wrapper.getLeafUUIDs(self.wpt, tree_id)
    
    @validate_tree_uuid_params
    def getAllUUIDs(self, tree_id:int) -> List[int]:
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        self._check_context_alive()
        return wpt_wrapper.getAllUUIDs(self.wpt, tree_id)
    
    @validate_recursion_params
    def setBranchRecursionLevel(self, level:int) -> None:
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        self._check_context_alive()
        wpt_wrapper.setBranchRecursionLevel(self.wpt, level)

    @validate_trunk_segment_params
    def setTrunkSegmentResolution(self, trunk_segs:int) -> None:
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        self._check_context_alive()
        wpt_wrapper.setTrunkSegmentResolution(self.wpt, trunk_segs)

    @validate_branch_segment_params
    def setBranchSegmentResolution(self, branch_segs:int) -> None:
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        self._check_context_alive()
        wpt_wrapper.setBranchSegmentResolution(self.wpt, branch_segs)

    @validate_leaf_subdivisions_params
    def setLeafSubdivisions(self, leaf_segs_x:int, leaf_segs_y:int) -> None:
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        self._check_context_alive()
        wpt_wrapper.setLeafSubdivisions(self.wpt, leaf_segs_x, leaf_segs_y)

    @validate_xml_file_params
    def loadXML(self, filename: str, silent: bool = False) -> None:
        """
        Load custom tree species from XML file.

        Loads tree species definitions from an XML file into the WeberPennTree library.
        After loading, trees can be built using buildTree() with the custom species names
        defined in the XML file.

        Args:
            filename: Path to XML file containing tree species definitions.
                     Can be absolute or relative to current working directory.
            silent: If True, suppress console output during loading. Default False.

        Raises:
            ValueError: If filename is invalid or empty
            FileNotFoundError: If XML file does not exist
            HeliosRuntimeError: If XML file is malformed or cannot be parsed

        Example:
            >>> wpt = WeberPennTree(context)
            >>> wpt.loadXML("my_custom_trees.xml")
            >>> tree_id = wpt.buildTree("CustomOak")  # Use custom species name

        Note:
            XML file must follow WeberPennTree XML schema. See WeberPennTreeLibrary.xml
            in helios-core/plugins/weberpenntree/xml/ for format examples.
        """
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")

        # Convert relative path to absolute BEFORE changing working directory
        xml_path = Path(filename)
        if not xml_path.is_absolute():
            xml_path = xml_path.resolve()

        # Use working directory context manager for C++ asset access
        with _weberpenntree_working_directory():
            self._check_context_alive()
            wpt_wrapper.loadXML(self.wpt, str(xml_path), silent)

    @staticmethod
    def _tree_name(tree_name: Union[WPTType, str], method: str) -> str:
        if isinstance(tree_name, WPTType):
            return tree_name.value
        if isinstance(tree_name, str):
            if not tree_name.strip():
                raise ValueError(f"{method}: tree_name must be a non-empty string")
            if '\x00' in tree_name:
                raise ValueError(f"{method}: tree_name must not contain NUL characters")
            return tree_name
        raise ValueError(f"{method}: tree_name must be a WPTType or str, got {type(tree_name).__name__}")

    def getTreeParameters(self, tree_name: Union[WPTType, str]) -> WeberPennTreeParameters:
        """
        Get the architectural parameters of a tree in the library.

        Args:
            tree_name: WPTType for a built-in species, or the name of a species loaded with loadXML()
                or defined with setTreeParameters().

        Returns:
            WeberPennTreeParameters with every field of the C++ struct.

        Raises:
            ValueError: If tree_name is not a WPTType or non-empty string.
            HeliosRuntimeError: If no tree with that name exists in the library.
        """
        name = self._tree_name(tree_name, "getTreeParameters")
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        self._check_context_alive()
        return WeberPennTreeParameters._from_wrapper_fields(wpt_wrapper.getTreeParameters(self.wpt, name))

    def setTreeParameters(self, tree_name: Union[WPTType, str], parameters: WeberPennTreeParameters) -> None:
        """
        Set the architectural parameters of a tree in the library.

        If ``tree_name`` is not yet in the library, a new species with that name is added, and
        ``buildTree(tree_name)`` will then build it. Parameters are validated in Python (types, Levels
        range, per-level array lengths) and again natively (e.g. Scale > 0, nCurveRes >= 1,
        0 <= BaseSize < 1); an invalid set leaves the library unchanged.

        Args:
            tree_name: WPTType or species name.
            parameters: WeberPennTreeParameters, typically obtained from getTreeParameters() and modified.

        Raises:
            ValueError: If tree_name or parameters are invalid.
            HeliosRuntimeError: If the native validation rejects the parameters.
        """
        name = self._tree_name(tree_name, "setTreeParameters")
        if not isinstance(parameters, WeberPennTreeParameters):
            raise ValueError(
                f"setTreeParameters: parameters must be a WeberPennTreeParameters, got {type(parameters).__name__}"
            )
        parameters.validate()
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        self._check_context_alive()
        wpt_wrapper.setTreeParameters(self.wpt, name, parameters._to_wrapper_fields())

    def seedRandomGenerator(self, seed: int) -> None:
        """
        Seed the WeberPennTree random number generator to make tree geometry reproducible.

        WeberPennTree has its own generator, independent of Context.seedRandomGenerator(); seeding
        the Context does not make trees repeatable. The generator advances with each buildTree() call,
        so re-seed before each build that should be reproduced.

        Args:
            seed: Non-negative integer below 2**32.

        Raises:
            ValueError: If seed is not an int in [0, 2**32).
        """
        if not isinstance(seed, int) or isinstance(seed, bool) or not (0 <= seed <= _UINT32_MAX):
            raise ValueError(f"seedRandomGenerator: seed must be an int in [0, 2**32), got {seed!r}")
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        self._check_context_alive()
        wpt_wrapper.seedRandomGenerator(self.wpt, seed)
