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
    current_dir = Path(__file__).parent
    repo_root = current_dir.parent
    build_lib_dir = repo_root / 'pyhelios_build' / 'build' / 'lib'
    working_dir = build_lib_dir.parent
    weberpenntree_assets = working_dir / 'plugins' / 'weberpenntree'
    
    # Validate that build directory and assets exist - fail fast if not
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
        
        # Check if weberpenntree plugin is available
        if not self._plugin_registry.is_plugin_available('weberpenntree'):
            print("Warning: WeberPennTree plugin not detected in current build")
            print("Tree generation functionality may be limited or unavailable")
        
        # Find build directory for asset loading - fail fast if not found
        current_dir = Path(__file__).parent
        repo_root = current_dir.parent
        build_lib_dir = repo_root / 'pyhelios_build' / 'build' / 'lib'
        build_dir = build_lib_dir.parent
        
        if not build_dir.exists():
            raise RuntimeError(
                f"PyHelios build directory not found: {build_dir}. "
                f"WeberPennTree requires native libraries to be built. "
                f"Run: python build_scripts/build_helios.py --plugins weberpenntree"
            )
        
        # Use working directory context manager during WeberPennTree creation
        with _weberpenntree_working_directory():
            self.wpt = wpt_wrapper.createWeberPennTreeWithBuildPluginRootDirectory(
                context.getNativePtr(), str(build_dir)
            )
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        wpt_wrapper.destroyWeberPennTree(self.wpt)

    def getNativePtr(self):
        return self.wpt


    def buildTree(self, wpt_type:WPTType, origin:vec3=vec3(0, 0, 0), scale:float=1) -> int:
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError(
                f"WeberPennTree is not properly initialized. "
                f"This may indicate that the weberpenntree plugin is not available. "
                f"Check plugin status with context.print_plugin_status()"
            )
        
        # Use working directory context manager during tree building to access assets
        with _weberpenntree_working_directory():
            return wpt_wrapper.buildTree(self.wpt, wpt_type.value, origin.to_list())
    
    def getTrunkUUIDs(self, tree_id:int) -> List[int]:
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        return wpt_wrapper.getTrunkUUIDs(self.wpt, tree_id)
    
    def getBranchUUIDs(self, tree_id:int) -> List[int]:
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        return wpt_wrapper.getBranchUUIDs(self.wpt, tree_id)
    
    def getLeafUUIDs(self, tree_id:int) -> List[int]:
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        return wpt_wrapper.getLeafUUIDs(self.wpt, tree_id)
    
    def getAllUUIDs(self, tree_id:int) -> List[int]:
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        return wpt_wrapper.getAllUUIDs(self.wpt, tree_id)
    
    def setBranchRecursionLevel(self, level:int) -> None:
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        wpt_wrapper.setBranchRecursionLevel(self.wpt, level)

    def setTrunkSegmentResolution(self, trunk_segs:int) -> None:
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        wpt_wrapper.setTrunkSegmentResolution(self.wpt, trunk_segs)

    def setBranchSegmentResolution(self, branch_segs:int) -> None:
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        wpt_wrapper.setBranchSegmentResolution(self.wpt, branch_segs)

    def setLeafSubdivisions(self, leaf_segs_x:int, leaf_segs_y:int) -> None:
        if not self.wpt or not isinstance(self.wpt, ctypes._Pointer):
            raise RuntimeError("WeberPennTree is not properly initialized. Check plugin availability.")
        wpt_wrapper.setLeafSubdivisions(self.wpt, leaf_segs_x, leaf_segs_y)

    


        
