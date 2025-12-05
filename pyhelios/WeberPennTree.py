# import ctypes
# from pyhelios import Context
# from wrappers import UWeberPennTreeWrapper as wpt_wrapper
# from enum import Enum
# from typing import List
# from wrappers import Vec3

import ctypes
import os
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import List

from .wrappers import UWeberPennTreeWrapper as wpt_wrapper
from .wrappers.DataTypes import vec3
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

from .Context import Context

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
                return wpt_wrapper.buildTreeWithScale(self.wpt, tree_name, origin.to_list(), scale)
            else:
                return wpt_wrapper.buildTree(self.wpt, tree_name, origin.to_list())
    
    @validate_tree_uuid_params
    def getTrunkUUIDs(self, tree_id:int) -> List[int]:
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        return wpt_wrapper.getTrunkUUIDs(self.wpt, tree_id)
    
    @validate_tree_uuid_params
    def getBranchUUIDs(self, tree_id:int) -> List[int]:
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        return wpt_wrapper.getBranchUUIDs(self.wpt, tree_id)
    
    @validate_tree_uuid_params
    def getLeafUUIDs(self, tree_id:int) -> List[int]:
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        return wpt_wrapper.getLeafUUIDs(self.wpt, tree_id)
    
    @validate_tree_uuid_params
    def getAllUUIDs(self, tree_id:int) -> List[int]:
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        return wpt_wrapper.getAllUUIDs(self.wpt, tree_id)
    
    @validate_recursion_params
    def setBranchRecursionLevel(self, level:int) -> None:
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        wpt_wrapper.setBranchRecursionLevel(self.wpt, level)

    @validate_trunk_segment_params
    def setTrunkSegmentResolution(self, trunk_segs:int) -> None:
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        wpt_wrapper.setTrunkSegmentResolution(self.wpt, trunk_segs)

    @validate_branch_segment_params
    def setBranchSegmentResolution(self, branch_segs:int) -> None:
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        wpt_wrapper.setBranchSegmentResolution(self.wpt, branch_segs)

    @validate_leaf_subdivisions_params
    def setLeafSubdivisions(self, leaf_segs_x:int, leaf_segs_y:int) -> None:
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
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
            wpt_wrapper.loadXML(self.wpt, str(xml_path), silent)
