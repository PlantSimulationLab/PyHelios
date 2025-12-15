"""
Ctypes wrapper for Visualizer C++ bindings.

This module provides low-level ctypes bindings to interface with 
the native Helios Visualizer plugin via the C++ wrapper layer.
"""

import ctypes
from typing import List, Optional

from ..plugins import helios_lib
from ..exceptions import check_helios_error

# Define the UVisualizer struct
class UVisualizer(ctypes.Structure):
    pass

# Import UContext from main wrapper to avoid type conflicts
from .UContextWrapper import UContext

# Try to set up Visualizer function prototypes
try:
    # Visualizer creation and destruction
    helios_lib.createVisualizer.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_bool]
    helios_lib.createVisualizer.restype = ctypes.POINTER(UVisualizer)
    
    # Add errcheck to automatically handle errors and nulls
    def _check_visualizer_creation(result, func, args):
        if _ERROR_MANAGEMENT_AVAILABLE:
            check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage)
        if not result:
            raise RuntimeError(
                "Failed to create Visualizer. This may indicate:\n"
                "1. OpenGL/graphics initialization problems in headless environments\n"
                "2. Missing graphics drivers or display support\n" 
                "3. Insufficient system resources for graphics context creation\n"
                "4. XQuartz or display server configuration issues on macOS/Linux"
            )
        return result
    
    helios_lib.createVisualizer.errcheck = _check_visualizer_creation

    helios_lib.createVisualizerWithAntialiasing.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_bool]
    helios_lib.createVisualizerWithAntialiasing.restype = ctypes.POINTER(UVisualizer)
    helios_lib.createVisualizerWithAntialiasing.errcheck = _check_visualizer_creation

    helios_lib.destroyVisualizer.argtypes = [ctypes.POINTER(UVisualizer)]
    helios_lib.destroyVisualizer.restype = None

    # Context geometry building
    helios_lib.buildContextGeometry.argtypes = [ctypes.POINTER(UVisualizer), ctypes.POINTER(UContext)]
    helios_lib.buildContextGeometry.restype = None

    helios_lib.buildContextGeometryUUIDs.argtypes = [ctypes.POINTER(UVisualizer), ctypes.POINTER(UContext), ctypes.POINTER(ctypes.c_uint32), ctypes.c_size_t]
    helios_lib.buildContextGeometryUUIDs.restype = None

    # Visualization functions
    helios_lib.plotInteractive.argtypes = [ctypes.POINTER(UVisualizer)]
    helios_lib.plotInteractive.restype = None

    helios_lib.plotUpdate.argtypes = [ctypes.POINTER(UVisualizer)]
    helios_lib.plotUpdate.restype = None

    helios_lib.printWindow.argtypes = [ctypes.POINTER(UVisualizer), ctypes.c_char_p]
    helios_lib.printWindow.restype = None

    helios_lib.closeWindow.argtypes = [ctypes.POINTER(UVisualizer)]
    helios_lib.closeWindow.restype = None

    # Camera control
    helios_lib.setCameraPosition.argtypes = [ctypes.POINTER(UVisualizer), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.setCameraPosition.restype = None

    helios_lib.setCameraPositionSpherical.argtypes = [ctypes.POINTER(UVisualizer), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.setCameraPositionSpherical.restype = None

    # Scene configuration
    helios_lib.setBackgroundColor.argtypes = [ctypes.POINTER(UVisualizer), ctypes.POINTER(ctypes.c_float)]
    helios_lib.setBackgroundColor.restype = None

    helios_lib.setLightDirection.argtypes = [ctypes.POINTER(UVisualizer), ctypes.POINTER(ctypes.c_float)]
    helios_lib.setLightDirection.restype = None

    helios_lib.setLightingModel.argtypes = [ctypes.POINTER(UVisualizer), ctypes.c_uint32]
    helios_lib.setLightingModel.restype = None

    # Primitive coloring functions
    helios_lib.colorContextPrimitivesByData.argtypes = [ctypes.POINTER(UVisualizer), ctypes.c_char_p]
    helios_lib.colorContextPrimitivesByData.restype = None
    
    helios_lib.colorContextPrimitivesByDataUUIDs.argtypes = [ctypes.POINTER(UVisualizer), ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]
    helios_lib.colorContextPrimitivesByDataUUIDs.restype = None

    # Camera Control Functions
    helios_lib.setCameraFieldOfView.argtypes = [ctypes.POINTER(UVisualizer), ctypes.c_float]
    helios_lib.setCameraFieldOfView.restype = None

    helios_lib.getCameraPosition.argtypes = [ctypes.POINTER(UVisualizer), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    helios_lib.getCameraPosition.restype = None

    helios_lib.getBackgroundColor.argtypes = [ctypes.POINTER(UVisualizer), ctypes.POINTER(ctypes.c_float)]
    helios_lib.getBackgroundColor.restype = None

    # Lighting Control Functions
    helios_lib.setLightIntensityFactor.argtypes = [ctypes.POINTER(UVisualizer), ctypes.c_float]
    helios_lib.setLightIntensityFactor.restype = None

    # Window and Display Functions
    helios_lib.getWindowSize.argtypes = [ctypes.POINTER(UVisualizer), ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getWindowSize.restype = None

    helios_lib.getFramebufferSize.argtypes = [ctypes.POINTER(UVisualizer), ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getFramebufferSize.restype = None

    helios_lib.printWindowDefault.argtypes = [ctypes.POINTER(UVisualizer)]
    helios_lib.printWindowDefault.restype = None

    helios_lib.displayImageFromPixels.argtypes = [ctypes.POINTER(UVisualizer), ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint, ctypes.c_uint]
    helios_lib.displayImageFromPixels.restype = None

    helios_lib.displayImageFromFile.argtypes = [ctypes.POINTER(UVisualizer), ctypes.c_char_p]
    helios_lib.displayImageFromFile.restype = None

    # Window Data Access Functions
    helios_lib.getWindowPixelsRGB.argtypes = [ctypes.POINTER(UVisualizer), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getWindowPixelsRGB.restype = None

    helios_lib.getDepthMap.argtypes = [ctypes.POINTER(UVisualizer), ctypes.POINTER(ctypes.POINTER(ctypes.c_float)), ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint)]
    helios_lib.getDepthMap.restype = None

    helios_lib.plotDepthMap.argtypes = [ctypes.POINTER(UVisualizer)]
    helios_lib.plotDepthMap.restype = None

    # Geometry Management Functions
    helios_lib.clearGeometry.argtypes = [ctypes.POINTER(UVisualizer)]
    helios_lib.clearGeometry.restype = None

    helios_lib.clearContextGeometry.argtypes = [ctypes.POINTER(UVisualizer)]
    helios_lib.clearContextGeometry.restype = None

    helios_lib.deleteGeometry.argtypes = [ctypes.POINTER(UVisualizer), ctypes.c_uint]
    helios_lib.deleteGeometry.restype = None

    helios_lib.updateContextPrimitiveColors.argtypes = [ctypes.POINTER(UVisualizer)]
    helios_lib.updateContextPrimitiveColors.restype = None

    # Coordinate Axes and Grid Functions
    helios_lib.addCoordinateAxes.argtypes = [ctypes.POINTER(UVisualizer)]
    helios_lib.addCoordinateAxes.restype = None

    helios_lib.addCoordinateAxesCustom.argtypes = [ctypes.POINTER(UVisualizer), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_char_p]
    helios_lib.addCoordinateAxesCustom.restype = None

    helios_lib.disableCoordinateAxes.argtypes = [ctypes.POINTER(UVisualizer)]
    helios_lib.disableCoordinateAxes.restype = None

    helios_lib.addGridWireFrame.argtypes = [ctypes.POINTER(UVisualizer), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int)]
    helios_lib.addGridWireFrame.restype = None

    # Colorbar Control Functions
    helios_lib.enableColorbar.argtypes = [ctypes.POINTER(UVisualizer)]
    helios_lib.enableColorbar.restype = None

    helios_lib.disableColorbar.argtypes = [ctypes.POINTER(UVisualizer)]
    helios_lib.disableColorbar.restype = None

    helios_lib.setColorbarPosition.argtypes = [ctypes.POINTER(UVisualizer), ctypes.POINTER(ctypes.c_float)]
    helios_lib.setColorbarPosition.restype = None

    helios_lib.setColorbarSize.argtypes = [ctypes.POINTER(UVisualizer), ctypes.POINTER(ctypes.c_float)]
    helios_lib.setColorbarSize.restype = None

    helios_lib.setColorbarRange.argtypes = [ctypes.POINTER(UVisualizer), ctypes.c_float, ctypes.c_float]
    helios_lib.setColorbarRange.restype = None

    helios_lib.setColorbarTicks.argtypes = [ctypes.POINTER(UVisualizer), ctypes.POINTER(ctypes.c_float), ctypes.c_uint]
    helios_lib.setColorbarTicks.restype = None

    helios_lib.setColorbarTitle.argtypes = [ctypes.POINTER(UVisualizer), ctypes.c_char_p]
    helios_lib.setColorbarTitle.restype = None

    helios_lib.setColorbarFontColor.argtypes = [ctypes.POINTER(UVisualizer), ctypes.POINTER(ctypes.c_float)]
    helios_lib.setColorbarFontColor.restype = None

    helios_lib.setColorbarFontSize.argtypes = [ctypes.POINTER(UVisualizer), ctypes.c_uint]
    helios_lib.setColorbarFontSize.restype = None

    # Colormap Functions
    helios_lib.setColormap.argtypes = [ctypes.POINTER(UVisualizer), ctypes.c_uint]
    helios_lib.setColormap.restype = None

    helios_lib.setCustomColormap.argtypes = [ctypes.POINTER(UVisualizer), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_uint]
    helios_lib.setCustomColormap.restype = None

    # Object/Primitive Coloring Functions
    helios_lib.colorContextPrimitivesByObjectData.argtypes = [ctypes.POINTER(UVisualizer), ctypes.c_char_p]
    helios_lib.colorContextPrimitivesByObjectData.restype = None

    helios_lib.colorContextPrimitivesByObjectDataIDs.argtypes = [ctypes.POINTER(UVisualizer), ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint), ctypes.c_uint]
    helios_lib.colorContextPrimitivesByObjectDataIDs.restype = None

    helios_lib.colorContextPrimitivesRandomly.argtypes = [ctypes.POINTER(UVisualizer), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint]
    helios_lib.colorContextPrimitivesRandomly.restype = None

    helios_lib.colorContextObjectsRandomly.argtypes = [ctypes.POINTER(UVisualizer), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint]
    helios_lib.colorContextObjectsRandomly.restype = None

    helios_lib.clearColor.argtypes = [ctypes.POINTER(UVisualizer)]
    helios_lib.clearColor.restype = None

    # Watermark Control Functions
    helios_lib.hideWatermark.argtypes = [ctypes.POINTER(UVisualizer)]
    helios_lib.hideWatermark.restype = None

    helios_lib.showWatermark.argtypes = [ctypes.POINTER(UVisualizer)]
    helios_lib.showWatermark.restype = None

    helios_lib.updateWatermark.argtypes = [ctypes.POINTER(UVisualizer)]
    helios_lib.updateWatermark.restype = None

    # Performance and Utility Functions
    helios_lib.enableMessages.argtypes = [ctypes.POINTER(UVisualizer)]
    helios_lib.enableMessages.restype = None

    helios_lib.disableMessages.argtypes = [ctypes.POINTER(UVisualizer)]
    helios_lib.disableMessages.restype = None

    helios_lib.plotOnce.argtypes = [ctypes.POINTER(UVisualizer), ctypes.c_bool]
    helios_lib.plotOnce.restype = None

    helios_lib.plotUpdateWithVisibility.argtypes = [ctypes.POINTER(UVisualizer), ctypes.c_bool]
    helios_lib.plotUpdateWithVisibility.restype = None

    # v1.3.53 Background Control Functions
    helios_lib.setBackgroundTransparent.argtypes = [ctypes.POINTER(UVisualizer)]
    helios_lib.setBackgroundTransparent.restype = None

    helios_lib.setBackgroundImage.argtypes = [ctypes.POINTER(UVisualizer), ctypes.c_char_p]
    helios_lib.setBackgroundImage.restype = None

    helios_lib.setBackgroundSkyTexture.argtypes = [ctypes.POINTER(UVisualizer), ctypes.c_char_p, ctypes.c_uint]
    helios_lib.setBackgroundSkyTexture.restype = None

    # v1.3.53 Navigation Gizmo Functions
    helios_lib.hideNavigationGizmo.argtypes = [ctypes.POINTER(UVisualizer)]
    helios_lib.hideNavigationGizmo.restype = None

    helios_lib.showNavigationGizmo.argtypes = [ctypes.POINTER(UVisualizer)]
    helios_lib.showNavigationGizmo.restype = None

    # v1.3.53 Geometry Vertex Manipulation Functions
    helios_lib.getGeometryVertices.argtypes = [ctypes.POINTER(UVisualizer), ctypes.c_size_t, ctypes.POINTER(ctypes.POINTER(ctypes.c_float)), ctypes.POINTER(ctypes.c_size_t)]
    helios_lib.getGeometryVertices.restype = None

    helios_lib.setGeometryVertices.argtypes = [ctypes.POINTER(UVisualizer), ctypes.c_size_t, ctypes.POINTER(ctypes.c_float), ctypes.c_size_t]
    helios_lib.setGeometryVertices.restype = None

    # v1.3.53 Enhanced printWindow with format support
    helios_lib.printWindowWithFormat.argtypes = [ctypes.POINTER(UVisualizer), ctypes.c_char_p, ctypes.c_char_p]
    helios_lib.printWindowWithFormat.restype = None

    # v1.3.54 Point Culling and LOD Functions
    helios_lib.setPointCullingEnabled.argtypes = [ctypes.POINTER(UVisualizer), ctypes.c_bool]
    helios_lib.setPointCullingEnabled.restype = None

    helios_lib.setPointCullingThreshold.argtypes = [ctypes.POINTER(UVisualizer), ctypes.c_size_t]
    helios_lib.setPointCullingThreshold.restype = None

    helios_lib.setPointMaxRenderDistance.argtypes = [ctypes.POINTER(UVisualizer), ctypes.c_float]
    helios_lib.setPointMaxRenderDistance.restype = None

    helios_lib.setPointLODFactor.argtypes = [ctypes.POINTER(UVisualizer), ctypes.c_float]
    helios_lib.setPointLODFactor.restype = None

    helios_lib.getPointRenderingMetrics.argtypes = [
        ctypes.POINTER(UVisualizer),
        ctypes.POINTER(ctypes.c_size_t),
        ctypes.POINTER(ctypes.c_size_t),
        ctypes.POINTER(ctypes.c_float)
    ]
    helios_lib.getPointRenderingMetrics.restype = None

    # Error management functions availability check
    try:
        helios_lib.getLastErrorCode.restype = ctypes.c_int
        helios_lib.getLastErrorMessage.restype = ctypes.c_char_p
        helios_lib.clearLastError.restype = None
        _ERROR_MANAGEMENT_AVAILABLE = True
    except AttributeError:
        _ERROR_MANAGEMENT_AVAILABLE = False

    _VISUALIZER_FUNCTIONS_AVAILABLE = True
except AttributeError:
    _VISUALIZER_FUNCTIONS_AVAILABLE = False
    _ERROR_MANAGEMENT_AVAILABLE = False

def _check_for_helios_error():
    """Check for and raise Helios errors if error management is available."""
    if _ERROR_MANAGEMENT_AVAILABLE:
        check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage)

# Wrapper functions

def create_visualizer(width: int, height: int, headless: bool = False) -> Optional[ctypes.POINTER(UVisualizer)]:
    """
    Create a new Visualizer instance.
    
    Args:
        width: Window width in pixels
        height: Window height in pixels
        headless: Enable headless mode (no window display)
        
    Returns:
        Pointer to UVisualizer or None if not available
        
    Raises:
        NotImplementedError: If visualizer functions not available
        RuntimeError: If visualizer creation fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )
    
    try:
        # The errcheck callback will handle error checking and null pointer validation
        visualizer = helios_lib.createVisualizer(
            ctypes.c_uint32(width),
            ctypes.c_uint32(height), 
            ctypes.c_bool(headless)
        )
        return visualizer
    except OSError as e:
        # Handle low-level system errors (e.g., graphics context failures)
        raise RuntimeError(
            f"Visualizer plugin failed to initialize due to system error: {e}. "
            "This may indicate missing graphics drivers, OpenGL issues, or "
            "incompatible system configuration. Try building with different options "
            "or check system requirements."
        )

def create_visualizer_with_antialiasing(width: int, height: int, antialiasing_samples: int, headless: bool = False) -> Optional[ctypes.POINTER(UVisualizer)]:
    """
    Create a new Visualizer instance with antialiasing.
    
    Args:
        width: Window width in pixels
        height: Window height in pixels
        antialiasing_samples: Number of antialiasing samples
        headless: Enable headless mode (no window display)
        
    Returns:
        Pointer to UVisualizer or None if not available
        
    Raises:
        NotImplementedError: If visualizer functions not available
        RuntimeError: If visualizer creation fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )
    
    try:
        # The errcheck callback will handle error checking and null pointer validation
        visualizer = helios_lib.createVisualizerWithAntialiasing(
            ctypes.c_uint32(width),
            ctypes.c_uint32(height),
            ctypes.c_uint32(antialiasing_samples),
            ctypes.c_bool(headless)
        )
        return visualizer
    except OSError as e:
        # Handle low-level system errors (e.g., graphics context failures)
        raise RuntimeError(
            f"Visualizer plugin failed to initialize due to system error: {e}. "
            "This may indicate missing graphics drivers, OpenGL issues, or "
            "incompatible system configuration. Try building with different options "
            "or check system requirements."
        )

def destroy_visualizer(visualizer: ctypes.POINTER(UVisualizer)) -> None:
    """
    Destroy a Visualizer instance.
    
    Args:
        visualizer: Pointer to UVisualizer to destroy
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        return  # Silent no-op for cleanup
    
    if visualizer:
        helios_lib.destroyVisualizer(visualizer)
        _check_for_helios_error()

def build_context_geometry(visualizer: ctypes.POINTER(UVisualizer), context: ctypes.POINTER(UContext)) -> None:
    """
    Build Context geometry in the visualizer.
    
    Args:
        visualizer: Pointer to UVisualizer
        context: Pointer to UContext
        
    Raises:
        NotImplementedError: If visualizer functions not available
        RuntimeError: If geometry building fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )
    
    if not visualizer:
        raise ValueError("Visualizer pointer is null")
    if not context:
        raise ValueError("Context pointer is null")
    
    helios_lib.buildContextGeometry(visualizer, context)
    _check_for_helios_error()

def build_context_geometry_uuids(visualizer: ctypes.POINTER(UVisualizer), context: ctypes.POINTER(UContext), uuids: List[int]) -> None:
    """
    Build specific Context geometry UUIDs in the visualizer.
    
    Args:
        visualizer: Pointer to UVisualizer
        context: Pointer to UContext
        uuids: List of primitive UUIDs to visualize
        
    Raises:
        NotImplementedError: If visualizer functions not available
        RuntimeError: If geometry building fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )
    
    if not visualizer:
        raise ValueError("Visualizer pointer is null")
    if not context:
        raise ValueError("Context pointer is null")
    if not uuids:
        raise ValueError("UUIDs list cannot be empty")
    
    # Convert Python list to ctypes array
    uuid_array = (ctypes.c_uint32 * len(uuids))(*uuids)
    
    helios_lib.buildContextGeometryUUIDs(visualizer, context, uuid_array, ctypes.c_size_t(len(uuids)))
    _check_for_helios_error()

def plot_interactive(visualizer: ctypes.POINTER(UVisualizer)) -> None:
    """
    Open interactive visualization window.
    
    Args:
        visualizer: Pointer to UVisualizer
        
    Raises:
        NotImplementedError: If visualizer functions not available
        RuntimeError: If visualization fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )
    
    if not visualizer:
        raise ValueError("Visualizer pointer is null")
    
    helios_lib.plotInteractive(visualizer)
    _check_for_helios_error()

def plot_update(visualizer: ctypes.POINTER(UVisualizer), hide_window: bool = False) -> None:
    """
    Update visualization (non-interactive).

    Args:
        visualizer: Pointer to UVisualizer
        hide_window: Whether to hide the window during update (use True for headless mode)

    Raises:
        NotImplementedError: If visualizer functions not available
        RuntimeError: If visualization update fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )

    if not visualizer:
        raise ValueError("Visualizer pointer is null")

    # Use plotUpdateWithVisibility to properly handle headless mode
    helios_lib.plotUpdateWithVisibility(visualizer, ctypes.c_bool(hide_window))
    _check_for_helios_error()

def print_window(visualizer: ctypes.POINTER(UVisualizer), filename: str) -> None:
    """
    Save current visualization to image file.
    
    Args:
        visualizer: Pointer to UVisualizer
        filename: Output filename for image
        
    Raises:
        NotImplementedError: If visualizer functions not available
        RuntimeError: If image saving fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )
    
    if not visualizer:
        raise ValueError("Visualizer pointer is null")
    if not filename:
        raise ValueError("Filename cannot be empty")
    
    filename_encoded = filename.encode('utf-8')
    helios_lib.printWindow(visualizer, filename_encoded)
    _check_for_helios_error()

def close_window(visualizer: ctypes.POINTER(UVisualizer)) -> None:
    """
    Close visualization window.
    
    Args:
        visualizer: Pointer to UVisualizer
        
    Raises:
        NotImplementedError: If visualizer functions not available
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )
    
    if not visualizer:
        raise ValueError("Visualizer pointer is null")
    
    helios_lib.closeWindow(visualizer)
    _check_for_helios_error()

def set_camera_position(visualizer: ctypes.POINTER(UVisualizer), position: List[float], look_at: List[float]) -> None:
    """
    Set camera position using Cartesian coordinates.
    
    Args:
        visualizer: Pointer to UVisualizer
        position: Camera position [x, y, z]
        look_at: Camera look-at point [x, y, z]
        
    Raises:
        NotImplementedError: If visualizer functions not available
        ValueError: If parameters are invalid
        RuntimeError: If camera positioning fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )
    
    if not visualizer:
        raise ValueError("Visualizer pointer is null")
    
    # Check if objects have the required methods instead of isinstance
    if not (hasattr(position, 'to_list') and hasattr(position, 'x') and hasattr(position, 'y') and hasattr(position, 'z')):
        raise ValueError(f"Position must be a vec3 object, got {type(position).__name__}")
    if not (hasattr(look_at, 'to_list') and hasattr(look_at, 'x') and hasattr(look_at, 'y') and hasattr(look_at, 'z')):
        raise ValueError(f"Look-at must be a vec3 object, got {type(look_at).__name__}")
    
    # Convert vec3 objects to ctypes arrays
    pos_array = (ctypes.c_float * 3)(*position.to_list())
    look_array = (ctypes.c_float * 3)(*look_at.to_list())
    
    helios_lib.setCameraPosition(visualizer, pos_array, look_array)
    _check_for_helios_error()

def set_camera_position_spherical(visualizer: ctypes.POINTER(UVisualizer), angle: List[float], look_at: List[float]) -> None:
    """
    Set camera position using spherical coordinates.
    
    Args:
        visualizer: Pointer to UVisualizer
        angle: Camera position [radius, zenith, azimuth]
        look_at: Camera look-at point [x, y, z]
        
    Raises:
        NotImplementedError: If visualizer functions not available
        ValueError: If parameters are invalid
        RuntimeError: If camera positioning fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )
    
    if not visualizer:
        raise ValueError("Visualizer pointer is null")
    
    # Check if objects have the required methods instead of isinstance
    if not (hasattr(angle, 'to_list') and hasattr(angle, 'radius') and hasattr(angle, 'elevation') and hasattr(angle, 'azimuth')):
        raise ValueError(f"Angle must be a SphericalCoord object, got {type(angle).__name__}")
    if not (hasattr(look_at, 'to_list') and hasattr(look_at, 'x') and hasattr(look_at, 'y') and hasattr(look_at, 'z')):
        raise ValueError(f"Look-at must be a vec3 object, got {type(look_at).__name__}")
    
    # Convert SphericalCoord and vec3 objects to ctypes arrays
    # SphericalCoord.to_list() returns [radius, elevation, zenith, azimuth] but we need [radius, elevation, azimuth]
    angle_list = [angle.radius, angle.elevation, angle.azimuth]
    angle_array = (ctypes.c_float * 3)(*angle_list)
    look_array = (ctypes.c_float * 3)(*look_at.to_list())
    
    helios_lib.setCameraPositionSpherical(visualizer, angle_array, look_array)
    _check_for_helios_error()

def set_background_color(visualizer: ctypes.POINTER(UVisualizer), color: List[float]) -> None:
    """
    Set background color.
    
    Args:
        visualizer: Pointer to UVisualizer
        color: Background color [r, g, b]
        
    Raises:
        NotImplementedError: If visualizer functions not available
        ValueError: If parameters are invalid
        RuntimeError: If color setting fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )
    
    if not visualizer:
        raise ValueError("Visualizer pointer is null")
    
    # Check if object has the required methods instead of isinstance
    if not (hasattr(color, 'to_list') and hasattr(color, 'r') and hasattr(color, 'g') and hasattr(color, 'b')):
        raise ValueError(f"Color must be an RGBcolor object, got {type(color).__name__}")
    
    # Convert RGBcolor object to ctypes array
    color_array = (ctypes.c_float * 3)(*color.to_list())
    
    helios_lib.setBackgroundColor(visualizer, color_array)
    _check_for_helios_error()

def set_light_direction(visualizer: ctypes.POINTER(UVisualizer), direction) -> None:
    """
    Set light direction.
    
    Args:
        visualizer: Pointer to UVisualizer
        direction: Light direction vector as vec3
        
    Raises:
        NotImplementedError: If visualizer functions not available
        ValueError: If parameters are invalid
        RuntimeError: If light direction setting fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )
    
    if not visualizer:
        raise ValueError("Visualizer pointer is null")
    
    # Check if object has the required methods instead of isinstance
    if not (hasattr(direction, 'to_list') and hasattr(direction, 'x') and hasattr(direction, 'y') and hasattr(direction, 'z')):
        raise ValueError(f"Direction must be a vec3 object, got {type(direction).__name__}")
    
    # Convert vec3 object to ctypes array
    dir_array = (ctypes.c_float * 3)(*direction.to_list())
    
    helios_lib.setLightDirection(visualizer, dir_array)
    _check_for_helios_error()

def set_lighting_model(visualizer: ctypes.POINTER(UVisualizer), lighting_model: int) -> None:
    """
    Set lighting model.
    
    Args:
        visualizer: Pointer to UVisualizer
        lighting_model: Lighting model (0=NONE, 1=PHONG, 2=PHONG_SHADOWED)
        
    Raises:
        NotImplementedError: If visualizer functions not available
        ValueError: If parameters are invalid
        RuntimeError: If lighting model setting fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )
    
    if not visualizer:
        raise ValueError("Visualizer pointer is null")
    if lighting_model not in [0, 1, 2]:
        raise ValueError("Lighting model must be 0 (NONE), 1 (PHONG), or 2 (PHONG_SHADOWED)")
    
    helios_lib.setLightingModel(visualizer, ctypes.c_uint32(lighting_model))
    _check_for_helios_error()

def color_context_primitives_by_data(visualizer: ctypes.POINTER(UVisualizer), data_name: str) -> None:
    """
    Color context primitives based on primitive data values.
    
    Args:
        visualizer: Pointer to UVisualizer
        data_name: Name of primitive data to use for coloring
        
    Raises:
        NotImplementedError: If visualizer functions not available
        ValueError: If parameters are invalid
        RuntimeError: If coloring fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )
    
    if not visualizer:
        raise ValueError("Visualizer pointer is null")
    if not data_name:
        raise ValueError("Data name cannot be empty")
    
    data_name_bytes = data_name.encode('utf-8')
    helios_lib.colorContextPrimitivesByData(visualizer, data_name_bytes)
    _check_for_helios_error()

def color_context_primitives_by_data_uuids(visualizer: ctypes.POINTER(UVisualizer), data_name: str, uuids: List[int]) -> None:
    """
    Color specific context primitives based on primitive data values.
    
    Args:
        visualizer: Pointer to UVisualizer
        data_name: Name of primitive data to use for coloring
        uuids: List of primitive UUIDs to color
        
    Raises:
        NotImplementedError: If visualizer functions not available
        ValueError: If parameters are invalid
        RuntimeError: If coloring fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )
    
    if not visualizer:
        raise ValueError("Visualizer pointer is null")
    if not data_name:
        raise ValueError("Data name cannot be empty")
    if not uuids:
        raise ValueError("UUID list cannot be empty")
    
    data_name_bytes = data_name.encode('utf-8')
    uuid_array = (ctypes.c_uint32 * len(uuids))(*uuids)
    helios_lib.colorContextPrimitivesByDataUUIDs(visualizer, data_name_bytes, uuid_array, len(uuids))
    _check_for_helios_error()

def set_background_transparent(visualizer: ctypes.POINTER(UVisualizer)) -> None:
    """
    Enable transparent background mode.

    Args:
        visualizer: Pointer to UVisualizer

    Raises:
        NotImplementedError: If visualizer functions not available
        RuntimeError: If background setting fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )

    if not visualizer:
        raise ValueError("Visualizer pointer is null")

    helios_lib.setBackgroundTransparent(visualizer)
    _check_for_helios_error()

def set_background_image(visualizer: ctypes.POINTER(UVisualizer), texture_file: str) -> None:
    """
    Set custom background image.

    Args:
        visualizer: Pointer to UVisualizer
        texture_file: Path to texture image file

    Raises:
        NotImplementedError: If visualizer functions not available
        ValueError: If parameters are invalid
        RuntimeError: If background setting fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )

    if not visualizer:
        raise ValueError("Visualizer pointer is null")
    if not texture_file:
        raise ValueError("Texture file path cannot be empty")

    texture_file_bytes = texture_file.encode('utf-8')
    helios_lib.setBackgroundImage(visualizer, texture_file_bytes)
    _check_for_helios_error()

def set_background_sky_texture(visualizer: ctypes.POINTER(UVisualizer), texture_file: Optional[str] = None, divisions: int = 50) -> None:
    """
    Set sky sphere texture background with automatic scaling.

    Args:
        visualizer: Pointer to UVisualizer
        texture_file: Path to spherical/equirectangular texture (None for default)
        divisions: Number of divisions for sphere tessellation

    Raises:
        NotImplementedError: If visualizer functions not available
        ValueError: If parameters are invalid
        RuntimeError: If background setting fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )

    if not visualizer:
        raise ValueError("Visualizer pointer is null")
    if divisions <= 0:
        raise ValueError("Divisions must be positive")

    # Use nullptr for default texture, encoded path otherwise
    if texture_file:
        texture_bytes = texture_file.encode('utf-8')
    else:
        texture_bytes = None

    helios_lib.setBackgroundSkyTexture(visualizer, texture_bytes, ctypes.c_uint(divisions))
    _check_for_helios_error()

def hide_navigation_gizmo(visualizer: ctypes.POINTER(UVisualizer)) -> None:
    """
    Hide navigation gizmo (coordinate axes indicator).

    Args:
        visualizer: Pointer to UVisualizer

    Raises:
        NotImplementedError: If visualizer functions not available
        RuntimeError: If operation fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )

    if not visualizer:
        raise ValueError("Visualizer pointer is null")

    helios_lib.hideNavigationGizmo(visualizer)
    _check_for_helios_error()

def show_navigation_gizmo(visualizer: ctypes.POINTER(UVisualizer)) -> None:
    """
    Show navigation gizmo (coordinate axes indicator).

    Args:
        visualizer: Pointer to UVisualizer

    Raises:
        NotImplementedError: If visualizer functions not available
        RuntimeError: If operation fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )

    if not visualizer:
        raise ValueError("Visualizer pointer is null")

    helios_lib.showNavigationGizmo(visualizer)
    _check_for_helios_error()

def get_geometry_vertices(visualizer: ctypes.POINTER(UVisualizer), geometry_id: int) -> List[List[float]]:
    """
    Get vertices of a geometry primitive.

    Args:
        visualizer: Pointer to UVisualizer
        geometry_id: Unique identifier of the geometry

    Returns:
        List of vertices as [[x,y,z], [x,y,z], ...]

    Raises:
        NotImplementedError: If visualizer functions not available
        ValueError: If parameters are invalid
        RuntimeError: If operation fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )

    if not visualizer:
        raise ValueError("Visualizer pointer is null")
    if geometry_id < 0:
        raise ValueError("Geometry ID must be non-negative")

    # Prepare output parameters
    vertices_ptr = ctypes.POINTER(ctypes.c_float)()
    vertex_count = ctypes.c_size_t()

    helios_lib.getGeometryVertices(
        visualizer,
        ctypes.c_size_t(geometry_id),
        ctypes.byref(vertices_ptr),
        ctypes.byref(vertex_count)
    )
    _check_for_helios_error()

    # Convert flat array to list of [x,y,z] vectors
    if not vertices_ptr or vertex_count.value == 0:
        return []

    vertices = []
    for i in range(0, vertex_count.value, 3):
        vertices.append([vertices_ptr[i], vertices_ptr[i+1], vertices_ptr[i+2]])

    return vertices

def set_geometry_vertices(visualizer: ctypes.POINTER(UVisualizer), geometry_id: int, vertices: List[List[float]]) -> None:
    """
    Set vertices of a geometry primitive.

    Args:
        visualizer: Pointer to UVisualizer
        geometry_id: Unique identifier of the geometry
        vertices: List of vertices as [[x,y,z], [x,y,z], ...] or list of vec3 objects

    Raises:
        NotImplementedError: If visualizer functions not available
        ValueError: If parameters are invalid
        RuntimeError: If operation fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )

    if not visualizer:
        raise ValueError("Visualizer pointer is null")
    if geometry_id < 0:
        raise ValueError("Geometry ID must be non-negative")
    if not vertices:
        raise ValueError("Vertices list cannot be empty")

    # Flatten vertices to single array
    flattened = []
    for vertex in vertices:
        # Handle both vec3 objects and [x,y,z] lists
        if hasattr(vertex, 'to_list'):
            flattened.extend(vertex.to_list())
        elif isinstance(vertex, (list, tuple)) and len(vertex) == 3:
            flattened.extend(vertex)
        else:
            raise ValueError("Each vertex must be a vec3 object or [x,y,z] list")

    # Convert to ctypes array
    vertices_array = (ctypes.c_float * len(flattened))(*flattened)

    helios_lib.setGeometryVertices(
        visualizer,
        ctypes.c_size_t(geometry_id),
        vertices_array,
        ctypes.c_size_t(len(flattened))
    )
    _check_for_helios_error()

def print_window_with_format(visualizer: ctypes.POINTER(UVisualizer), filename: str, image_format: str) -> None:
    """
    Save current visualization to image file with specified format.

    Args:
        visualizer: Pointer to UVisualizer
        filename: Output filename for image
        image_format: Image format ("jpeg" or "png")

    Raises:
        NotImplementedError: If visualizer functions not available
        ValueError: If parameters are invalid
        RuntimeError: If image saving fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )

    if not visualizer:
        raise ValueError("Visualizer pointer is null")
    if not filename:
        raise ValueError("Filename cannot be empty")
    if image_format.lower() not in ['jpeg', 'png']:
        raise ValueError("Image format must be 'jpeg' or 'png'")

    filename_bytes = filename.encode('utf-8')
    format_bytes = image_format.lower().encode('utf-8')

    helios_lib.printWindowWithFormat(visualizer, filename_bytes, format_bytes)
    _check_for_helios_error()

def set_point_culling_enabled(visualizer: ctypes.POINTER(UVisualizer), enabled: bool) -> None:
    """
    Enable or disable point cloud culling optimization.

    Args:
        visualizer: Pointer to UVisualizer
        enabled: True to enable culling, false to disable

    Raises:
        NotImplementedError: If visualizer functions not available
        ValueError: If visualizer pointer is null
        RuntimeError: If operation fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )

    if not visualizer:
        raise ValueError("Visualizer pointer is null")

    helios_lib.setPointCullingEnabled(visualizer, ctypes.c_bool(enabled))
    _check_for_helios_error()

def set_point_culling_threshold(visualizer: ctypes.POINTER(UVisualizer), threshold: int) -> None:
    """
    Set the minimum number of points required to trigger culling.

    Args:
        visualizer: Pointer to UVisualizer
        threshold: Point count threshold for enabling culling

    Raises:
        NotImplementedError: If visualizer functions not available
        ValueError: If visualizer pointer is null or threshold is invalid
        RuntimeError: If operation fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )

    if not visualizer:
        raise ValueError("Visualizer pointer is null")
    if threshold < 0:
        raise ValueError("Point culling threshold must be non-negative")

    helios_lib.setPointCullingThreshold(visualizer, ctypes.c_size_t(threshold))
    _check_for_helios_error()

def set_point_max_render_distance(visualizer: ctypes.POINTER(UVisualizer), distance: float) -> None:
    """
    Set the maximum rendering distance for points.

    Args:
        visualizer: Pointer to UVisualizer
        distance: Maximum distance in world units (0 = auto-calculate based on scene size)

    Raises:
        NotImplementedError: If visualizer functions not available
        ValueError: If visualizer pointer is null or distance is invalid
        RuntimeError: If operation fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )

    if not visualizer:
        raise ValueError("Visualizer pointer is null")
    if distance < 0.0:
        raise ValueError("Point max render distance cannot be negative")

    helios_lib.setPointMaxRenderDistance(visualizer, ctypes.c_float(distance))
    _check_for_helios_error()

def set_point_lod_factor(visualizer: ctypes.POINTER(UVisualizer), factor: float) -> None:
    """
    Set the level-of-detail factor for distance-based culling.

    Args:
        visualizer: Pointer to UVisualizer
        factor: LOD factor (higher values = more aggressive culling)

    Raises:
        NotImplementedError: If visualizer functions not available
        ValueError: If visualizer pointer is null or factor is invalid
        RuntimeError: If operation fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )

    if not visualizer:
        raise ValueError("Visualizer pointer is null")
    if factor <= 0.0:
        raise ValueError("Point LOD factor must be positive")

    helios_lib.setPointLODFactor(visualizer, ctypes.c_float(factor))
    _check_for_helios_error()

def get_point_rendering_metrics(visualizer: ctypes.POINTER(UVisualizer)) -> dict:
    """
    Get point cloud rendering performance metrics.

    Args:
        visualizer: Pointer to UVisualizer

    Returns:
        Dictionary with keys:
            - 'total_points': Total point count in scene
            - 'rendered_points': Number of points actually rendered after culling
            - 'culling_time_ms': Time spent on culling in milliseconds

    Raises:
        NotImplementedError: If visualizer functions not available
        ValueError: If visualizer pointer is null
        RuntimeError: If operation fails
    """
    if not _VISUALIZER_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "Visualizer functions not available in current Helios library. "
            "Rebuild with visualizer plugin enabled."
        )

    if not visualizer:
        raise ValueError("Visualizer pointer is null")

    # Prepare output parameters
    total_points = ctypes.c_size_t()
    rendered_points = ctypes.c_size_t()
    culling_time_ms = ctypes.c_float()

    helios_lib.getPointRenderingMetrics(
        visualizer,
        ctypes.byref(total_points),
        ctypes.byref(rendered_points),
        ctypes.byref(culling_time_ms)
    )
    _check_for_helios_error()

    return {
        'total_points': total_points.value,
        'rendered_points': rendered_points.value,
        'culling_time_ms': culling_time_ms.value
    }

# Mock implementations when visualizer is not available
if not _VISUALIZER_FUNCTIONS_AVAILABLE:
    def _mock_function(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: Visualizer plugin not available. "
            "This would perform visualization with native Helios library. "
            "To enable visualizer functionality:\n"
            "1. Build PyHelios with visualizer plugin: build_scripts/build_helios --plugins visualizer\n"
            "2. Ensure OpenGL, GLFW, and graphics dependencies are available\n"
            "3. Rebuild PyHelios with graphics system support"
        )
    
    # Replace all wrapper functions with mock
    create_visualizer = _mock_function
    create_visualizer_with_antialiasing = _mock_function
    build_context_geometry = _mock_function
    build_context_geometry_uuids = _mock_function
    plot_interactive = _mock_function
    plot_update = _mock_function
    print_window = _mock_function
    close_window = _mock_function
    set_camera_position = _mock_function
    set_camera_position_spherical = _mock_function
    set_background_color = _mock_function
    set_light_direction = _mock_function
    set_lighting_model = _mock_function
    color_context_primitives_by_data = _mock_function
    color_context_primitives_by_data_uuids = _mock_function