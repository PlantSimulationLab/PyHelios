"""
High-level Visualizer interface for PyHelios.

This module provides a user-friendly interface to the 3D visualization
capabilities with graceful plugin handling and informative error messages.
"""

import logging
import os
import ctypes
from pathlib import Path
from contextlib import contextmanager
from typing import List, Optional, Union, Tuple

from .plugins.registry import get_plugin_registry
from .plugins import helios_lib
from .wrappers import UVisualizerWrapper as visualizer_wrapper
from .wrappers.DataTypes import vec3, RGBcolor, SphericalCoord
from .Context import Context
from .validation.plugin_decorators import validate_build_geometry_params, validate_print_window_params
from .assets import get_asset_manager

logger = logging.getLogger(__name__)

# Type references for type checking (avoids doxygen parsing issues)
_INT_TYPE = int
_NUMERIC_TYPES = (int, float)


def _resolve_user_path(path: str) -> str:
    """
    Resolve a user-provided path to an absolute path before working directory changes.

    This ensures that user file paths are interpreted relative to their original
    working directory, not the temporary working directory used for asset discovery.

    Args:
        path: User-provided file path (absolute or relative)

    Returns:
        Absolute path resolved from the user's original working directory
    """
    from pathlib import Path

    path_obj = Path(path)
    if path_obj.is_absolute():
        return str(path_obj)
    else:
        # Resolve relative to the user's current working directory
        return str(Path.cwd().resolve() / path_obj)

@contextmanager
def _visualizer_working_directory():
    """
    Context manager that temporarily changes working directory for visualizer operations.

    The C++ visualizer code expects to find assets at 'plugins/visualizer/' relative
    to the current working directory. This context manager ensures the working directory
    is set correctly during visualizer initialization and operations.

    Note: This is required because the Helios C++ core prioritizes current working
    directory for asset resolution over environment variables.
    """
    # Find the build directory where assets are located
    # Try asset manager first (works for both development and wheel installations)
    asset_manager = get_asset_manager()
    working_dir = asset_manager._get_helios_build_path()
    
    if working_dir and working_dir.exists():
        visualizer_assets = working_dir / 'plugins' / 'visualizer'
    else:
        # For wheel installations, check packaged assets  
        current_dir = Path(__file__).parent
        packaged_build = current_dir / 'assets' / 'build'
        
        if packaged_build.exists():
            working_dir = packaged_build
            visualizer_assets = working_dir / 'plugins' / 'visualizer'
        else:
            # Fallback to development paths
            repo_root = current_dir.parent
            build_lib_dir = repo_root / 'pyhelios_build' / 'build' / 'lib'
            working_dir = build_lib_dir.parent
            visualizer_assets = working_dir / 'plugins' / 'visualizer'
            
            if not build_lib_dir.exists():
                logger.warning(f"Build directory not found: {build_lib_dir}")
                # Fallback to current directory - may not work but don't break
                yield
                return
    
    if not (visualizer_assets / 'shaders').exists():
        # Only warn in development environments, not wheel installations
        asset_mgr = get_asset_manager()
        if not asset_mgr._is_wheel_install():
            logger.warning(f"Visualizer assets not found at: {visualizer_assets}")
        # Continue anyway - may be using source assets or alternative setup
    
    # Change working directory temporarily
    original_cwd = Path.cwd()
    
    try:
        logger.debug(f"Changing working directory from {original_cwd} to {working_dir}")
        os.chdir(working_dir)
        yield
    finally:
        logger.debug(f"Restoring working directory to {original_cwd}")
        os.chdir(original_cwd)


class VisualizerError(Exception):
    """Raised when Visualizer operations fail."""
    pass


class Visualizer:
    """
    High-level interface for 3D visualization and rendering.
    
    This class provides a user-friendly wrapper around the native Helios
    visualizer plugin with automatic plugin availability checking and
    graceful error handling.
    
    The visualizer provides OpenGL-based 3D rendering with interactive controls,
    image export, and comprehensive scene configuration options.
    """
    
    # Lighting model constants
    LIGHTING_NONE = 0
    LIGHTING_PHONG = 1
    LIGHTING_PHONG_SHADOWED = 2
    
    # Colormap constants (matching C++ enum values)
    COLORMAP_HOT = 0
    COLORMAP_COOL = 1
    COLORMAP_RAINBOW = 2
    COLORMAP_LAVA = 3
    COLORMAP_PARULA = 4
    COLORMAP_GRAY = 5
    
    def __init__(self, width: int, height: int, antialiasing_samples: int = 1, headless: bool = False):
        """
        Initialize Visualizer with graceful plugin handling.

        Args:
            width: Window width in pixels
            height: Window height in pixels
            antialiasing_samples: Number of antialiasing samples (default: 1)
            headless: Enable headless mode for offscreen rendering (default: False)

        Raises:
            VisualizerError: If visualizer plugin is not available
            ValueError: If parameters are invalid
        """
        # Validate parameter types first
        if not isinstance(width, _INT_TYPE):
            raise ValueError(f"Width must be an integer, got {type(width).__name__}")
        if not isinstance(height, _INT_TYPE):
            raise ValueError(f"Height must be an integer, got {type(height).__name__}")
        if not isinstance(antialiasing_samples, _INT_TYPE):
            raise ValueError(f"Antialiasing samples must be an integer, got {type(antialiasing_samples).__name__}")
        if not isinstance(headless, bool):
            raise ValueError(f"Headless must be a boolean, got {type(headless).__name__}")

        # Validate parameter values
        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive integers")
        if antialiasing_samples < 1:
            raise ValueError("Antialiasing samples must be at least 1")
        
        self.width = width
        self.height = height
        self.antialiasing_samples = antialiasing_samples
        self.headless = headless
        self.visualizer = None
        
        # Check plugin availability using registry
        registry = get_plugin_registry()
        
        if not registry.is_plugin_available('visualizer'):
            # Get helpful information about the missing plugin
            available_plugins = registry.get_available_plugins()
            
            error_msg = (
                "Visualizer requires the 'visualizer' plugin which is not available.\n\n"
                "The visualizer plugin provides OpenGL-based 3D rendering and visualization.\n"
                "System requirements:\n"
                "- OpenGL 3.3 or higher\n"
                "- GLFW library for window management\n"
                "- FreeType library for text rendering\n"
                "- Display/graphics drivers (X11 on Linux, native on Windows/macOS)\n\n"
                "To enable visualization:\n"
                "1. Build PyHelios with visualizer plugin:\n"
                "   build_scripts/build_helios --plugins visualizer\n"
                f"\nCurrently available plugins: {available_plugins}"
            )
            
            # Add platform-specific installation hints
            import platform
            system = platform.system().lower()
            if 'linux' in system:
                error_msg += (
                    "\n\nLinux installation hints:\n"
                    "- Ubuntu/Debian: sudo apt-get install libx11-dev xorg-dev libgl1-mesa-dev libglu1-mesa-dev\n"
                    "- CentOS/RHEL: sudo yum install libX11-devel mesa-libGL-devel mesa-libGLU-devel"
                )
            elif 'darwin' in system:
                error_msg += (
                    "\n\nmacOS installation hints:\n"
                    "- Install XQuartz: brew install --cask xquartz\n"
                    "- OpenGL should be available by default"
                )
            elif 'windows' in system:
                error_msg += (
                    "\n\nWindows installation hints:\n"
                    "- OpenGL drivers should be provided by graphics card drivers\n"
                    "- Visual Studio runtime may be required"
                )
            
            raise VisualizerError(error_msg)
        
        # Plugin is available - create visualizer with correct working directory
        try:
            with _visualizer_working_directory():
                if antialiasing_samples > 1:
                    self.visualizer = visualizer_wrapper.create_visualizer_with_antialiasing(
                        width, height, antialiasing_samples, headless
                    )
                else:
                    self.visualizer = visualizer_wrapper.create_visualizer(
                        width, height, headless
                    )
                    
                if self.visualizer is None:
                    raise VisualizerError(
                        "Failed to create Visualizer instance. "
                        "This may indicate a problem with graphics drivers or OpenGL initialization."
                    )
                logger.info(f"Visualizer created successfully ({width}x{height}, AA:{antialiasing_samples}, headless:{headless})")
            
        except Exception as e:
            raise VisualizerError(f"Failed to initialize Visualizer: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit with proper cleanup."""
        if self.visualizer is not None:
            try:
                with _visualizer_working_directory():
                    visualizer_wrapper.destroy_visualizer(self.visualizer)
                logger.debug("Visualizer destroyed successfully")
            except Exception as e:
                logger.warning(f"Error destroying Visualizer: {e}")
            finally:
                self.visualizer = None
    
    @validate_build_geometry_params
    def buildContextGeometry(self, context: Context, uuids: Optional[List[int]] = None) -> None:
        """
        Build Context geometry in the visualizer.
        
        This method loads geometry from a Helios Context into the visualizer
        for rendering. If no UUIDs are specified, all geometry is loaded.
        
        Args:
            context: Helios Context instance containing geometry
            uuids: Optional list of primitive UUIDs to visualize (default: all)
            
        Raises:
            VisualizerError: If geometry building fails
            ValueError: If parameters are invalid
        """
        if self.visualizer is None:
            raise VisualizerError("Visualizer has been destroyed")
        if not isinstance(context, Context):
            raise ValueError("context must be a Context instance")
        
        try:
            with _visualizer_working_directory():
                if uuids is None:
                    # Load all geometry
                    visualizer_wrapper.build_context_geometry(self.visualizer, context.getNativePtr())
                    logger.debug("Built all Context geometry in visualizer")
                else:
                    # Load specific UUIDs
                    if not uuids:
                        raise ValueError("UUIDs list cannot be empty")
                    visualizer_wrapper.build_context_geometry_uuids(
                        self.visualizer, context.getNativePtr(), uuids
                    )
                    logger.debug(f"Built {len(uuids)} primitives in visualizer")
                
        except Exception as e:
            raise VisualizerError(f"Failed to build Context geometry: {e}")
    
    def plotInteractive(self) -> None:
        """
        Open interactive visualization window.
        
        This method opens a window with the current scene and allows user
        interaction (camera rotation, zooming, etc.). The program will pause
        until the window is closed by the user.
        
        Interactive controls:
        - Mouse scroll: Zoom in/out
        - Left mouse + drag: Rotate camera
        - Right mouse + drag: Pan camera
        - Arrow keys: Camera movement
        - +/- keys: Zoom in/out
        
        Raises:
            VisualizerError: If visualization fails
        """
        if self.visualizer is None:
            raise VisualizerError("Visualizer has been destroyed")
        
        try:
            with _visualizer_working_directory():
                visualizer_wrapper.plot_interactive(self.visualizer)
                logger.debug("Interactive visualization completed")
        except Exception as e:
            raise VisualizerError(f"Interactive visualization failed: {e}")
    
    def plotUpdate(self) -> None:
        """
        Update visualization (non-interactive).

        This method updates the visualization window without user interaction.
        The program continues immediately after rendering. Useful for batch
        processing or creating image sequences.

        In headless mode, automatically hides the window to prevent graphics driver crashes on some platforms.

        Raises:
            VisualizerError: If visualization update fails
        """
        if self.visualizer is None:
            raise VisualizerError("Visualizer has been destroyed")

        try:
            with _visualizer_working_directory():
                # In headless mode, hide the window to avoid OpenGL/Metal crashes on macOS
                visualizer_wrapper.plot_update(self.visualizer, hide_window=self.headless)
            logger.debug("Visualization updated")
        except Exception as e:
            raise VisualizerError(f"Visualization update failed: {e}")
    
    @validate_print_window_params
    def printWindow(self, filename: str, image_format: Optional[str] = None) -> None:
        """
        Save current visualization to image file.

        This method exports the current visualization to an image file.
        Starting from v1.3.53, supports both JPEG and PNG formats.

        Args:
            filename: Output filename for image
                     Can be absolute or relative to user's current working directory
                     Extension (.jpg, .png) is recommended but not required
            image_format: Image format - "jpeg" or "png" (v1.3.53+).
                         If None, automatically detects from filename extension.
                         Defaults to "jpeg" if not detectable from extension.

        Raises:
            VisualizerError: If image saving fails
            ValueError: If filename or format is invalid

        Note:
            PNG format is required to preserve transparent backgrounds when using
            setBackgroundTransparent(). JPEG format will render transparent areas as black.

        Example:
            >>> visualizer.printWindow("output.jpg")  # Auto-detects JPEG
            >>> visualizer.printWindow("output.png")  # Auto-detects PNG
            >>> visualizer.printWindow("output.img", image_format="png")  # Explicit PNG
        """
        if self.visualizer is None:
            raise VisualizerError("Visualizer has been destroyed")
        if not filename:
            raise ValueError("Filename cannot be empty")

        # Resolve filename relative to user's working directory before chdir
        resolved_filename = _resolve_user_path(filename)

        # Auto-detect format from extension if not specified
        if image_format is None:
            if resolved_filename.lower().endswith('.png'):
                image_format = 'png'
            elif resolved_filename.lower().endswith(('.jpg', '.jpeg')):
                image_format = 'jpeg'
            else:
                # Default to jpeg for backward compatibility
                image_format = 'jpeg'
                logger.debug(f"No format specified and extension not recognized, defaulting to JPEG")

        # Validate format
        if image_format.lower() not in ['jpeg', 'png']:
            raise ValueError(f"Image format must be 'jpeg' or 'png', got '{image_format}'")

        try:
            with _visualizer_working_directory():
                # Try using the new format-aware function (v1.3.53+)
                try:
                    visualizer_wrapper.print_window_with_format(
                        self.visualizer,
                        resolved_filename,
                        image_format
                    )
                    logger.debug(f"Visualization saved to {resolved_filename} ({image_format.upper()} format)")
                except (AttributeError, NotImplementedError):
                    # Fallback to old function for older Helios versions
                    if image_format.lower() != 'jpeg':
                        logger.warning(
                            "PNG format requested but not available in current Helios version. "
                            "Falling back to JPEG format. Update to Helios v1.3.53+ for PNG support."
                        )
                    visualizer_wrapper.print_window(self.visualizer, resolved_filename)
                    logger.debug(f"Visualization saved to {resolved_filename} (JPEG format - legacy mode)")
        except Exception as e:
            raise VisualizerError(f"Failed to save image: {e}")
    
    def closeWindow(self) -> None:
        """
        Close visualization window.
        
        This method closes any open visualization window. It's safe to call
        even if no window is open.
        
        Raises:
            VisualizerError: If window closing fails
        """
        if self.visualizer is None:
            raise VisualizerError("Visualizer has been destroyed")
        
        try:
            visualizer_wrapper.close_window(self.visualizer)
            logger.debug("Visualization window closed")
        except Exception as e:
            raise VisualizerError(f"Failed to close window: {e}")
    
    def setCameraPosition(self, position: vec3, lookAt: vec3) -> None:
        """
        Set camera position using Cartesian coordinates.
        
        Args:
            position: Camera position as vec3 in world coordinates
            lookAt: Camera look-at point as vec3 in world coordinates
            
        Raises:
            VisualizerError: If camera positioning fails
            ValueError: If parameters are invalid
        """
        if self.visualizer is None:
            raise VisualizerError("Visualizer has been destroyed")
        
        # Validate DataType parameters
        if not isinstance(position, vec3):
            raise ValueError(f"Position must be a vec3, got {type(position).__name__}")
        if not isinstance(lookAt, vec3):
            raise ValueError(f"LookAt must be a vec3, got {type(lookAt).__name__}")
        
        try:
            visualizer_wrapper.set_camera_position(self.visualizer, position, lookAt)
            logger.debug(f"Camera position set to ({position.x}, {position.y}, {position.z}), looking at ({lookAt.x}, {lookAt.y}, {lookAt.z})")
        except Exception as e:
            raise VisualizerError(f"Failed to set camera position: {e}")
    
    def setCameraPositionSpherical(self, angle: SphericalCoord, lookAt: vec3) -> None:
        """
        Set camera position using spherical coordinates.
        
        Args:
            angle: Camera position as SphericalCoord (radius, elevation, azimuth)
            lookAt: Camera look-at point as vec3 in world coordinates
            
        Raises:
            VisualizerError: If camera positioning fails
            ValueError: If parameters are invalid
        """
        if self.visualizer is None:
            raise VisualizerError("Visualizer has been destroyed")
        
        # Validate DataType parameters
        if not isinstance(angle, SphericalCoord):
            raise ValueError(f"Angle must be a SphericalCoord, got {type(angle).__name__}")
        if not isinstance(lookAt, vec3):
            raise ValueError(f"LookAt must be a vec3, got {type(lookAt).__name__}")
        
        try:
            visualizer_wrapper.set_camera_position_spherical(self.visualizer, angle, lookAt)
            logger.debug(f"Camera position set to spherical (r={angle.radius}, el={angle.elevation}, az={angle.azimuth}), looking at ({lookAt.x}, {lookAt.y}, {lookAt.z})")
        except Exception as e:
            raise VisualizerError(f"Failed to set camera position (spherical): {e}")
    
    def setBackgroundColor(self, color: RGBcolor) -> None:
        """
        Set background color.
        
        Args:
            color: Background color as RGBcolor with values in range [0, 1]
            
        Raises:
            VisualizerError: If color setting fails
            ValueError: If color values are invalid
        """
        if self.visualizer is None:
            raise VisualizerError("Visualizer has been destroyed")
        
        # Validate DataType parameter
        if not isinstance(color, RGBcolor):
            raise ValueError(f"Color must be an RGBcolor, got {type(color).__name__}")
        
        # Validate color range
        if not (0 <= color.r <= 1 and 0 <= color.g <= 1 and 0 <= color.b <= 1):
            raise ValueError(f"Color components ({color.r}, {color.g}, {color.b}) must be in range [0, 1]")
        
        try:
            visualizer_wrapper.set_background_color(self.visualizer, color)
            logger.debug(f"Background color set to ({color.r}, {color.g}, {color.b})")
        except Exception as e:
            raise VisualizerError(f"Failed to set background color: {e}")

    def setBackgroundTransparent(self) -> None:
        """
        Enable transparent background mode (v1.3.53+).

        Sets the background to transparent with checkerboard pattern display.
        Requires PNG output format to preserve transparency.

        Note: When using transparent background, use printWindow() with PNG
        format to save transparent images.

        Raises:
            VisualizerError: If transparent background setting fails
        """
        if self.visualizer is None:
            raise VisualizerError("Visualizer has been destroyed")

        try:
            visualizer_wrapper.set_background_transparent(self.visualizer)
            logger.debug("Background set to transparent mode")
        except Exception as e:
            raise VisualizerError(f"Failed to set transparent background: {e}")

    def setBackgroundImage(self, texture_file: str) -> None:
        """
        Set custom background image texture (v1.3.53+).

        Args:
            texture_file: Path to background image file
                         Can be absolute or relative to working directory

        Raises:
            VisualizerError: If background image setting fails
            ValueError: If texture file path is invalid
        """
        if self.visualizer is None:
            raise VisualizerError("Visualizer has been destroyed")

        if not texture_file or not isinstance(texture_file, str):
            raise ValueError("Texture file path must be a non-empty string")

        # Resolve texture file path relative to user's working directory
        resolved_path = _resolve_user_path(texture_file)

        try:
            visualizer_wrapper.set_background_image(self.visualizer, resolved_path)
            logger.debug(f"Background image set to {resolved_path}")
        except Exception as e:
            raise VisualizerError(f"Failed to set background image: {e}")

    def setBackgroundSkyTexture(self, texture_file: Optional[str] = None, divisions: int = 50) -> None:
        """
        Set sky sphere texture background with automatic scaling (v1.3.53+).

        Creates a sky sphere that automatically scales with the scene.
        Replaces the deprecated addSkyDomeByCenter() method.

        Args:
            texture_file: Path to spherical/equirectangular texture image
                         If None, uses default gradient sky texture
            divisions: Number of sphere tessellation divisions (default: 50)
                      Higher values create smoother sphere but use more GPU

        Raises:
            VisualizerError: If sky texture setting fails
            ValueError: If parameters are invalid

        Example:
            >>> visualizer.setBackgroundSkyTexture()  # Default gradient sky
            >>> visualizer.setBackgroundSkyTexture("sky_hdri.jpg", divisions=100)
        """
        if self.visualizer is None:
            raise VisualizerError("Visualizer has been destroyed")

        if not isinstance(divisions, _INT_TYPE) or divisions <= 0:
            raise ValueError("Divisions must be a positive integer")

        # Resolve texture file path if provided
        resolved_path = None
        if texture_file:
            if not isinstance(texture_file, str):
                raise ValueError("Texture file must be a string")
            resolved_path = _resolve_user_path(texture_file)

        try:
            visualizer_wrapper.set_background_sky_texture(
                self.visualizer,
                resolved_path,
                divisions
            )
            if resolved_path:
                logger.debug(f"Sky texture background set: {resolved_path}, divisions={divisions}")
            else:
                logger.debug(f"Default sky texture background set with divisions={divisions}")
        except Exception as e:
            raise VisualizerError(f"Failed to set sky texture background: {e}")

    def setLightDirection(self, direction: vec3) -> None:
        """
        Set light direction.
        
        Args:
            direction: Light direction vector as vec3 (will be normalized)
            
        Raises:
            VisualizerError: If light direction setting fails
            ValueError: If direction is invalid
        """
        if self.visualizer is None:
            raise VisualizerError("Visualizer has been destroyed")
        
        # Validate DataType parameter
        if not isinstance(direction, vec3):
            raise ValueError(f"Direction must be a vec3, got {type(direction).__name__}")
        
        # Check for zero vector
        if direction.x == 0 and direction.y == 0 and direction.z == 0:
            raise ValueError("Light direction cannot be zero vector")
        
        try:
            visualizer_wrapper.set_light_direction(self.visualizer, direction)
            logger.debug(f"Light direction set to ({direction.x}, {direction.y}, {direction.z})")
        except Exception as e:
            raise VisualizerError(f"Failed to set light direction: {e}")
    
    def setLightingModel(self, lighting_model: Union[int, str]) -> None:
        """
        Set lighting model.
        
        Args:
            lighting_model: Lighting model, either:
                - 0 or "none": No lighting
                - 1 or "phong": Phong shading
                - 2 or "phong_shadowed": Phong shading with shadows
            
        Raises:
            VisualizerError: If lighting model setting fails
            ValueError: If lighting model is invalid
        """
        if self.visualizer is None:
            raise VisualizerError("Visualizer has been destroyed")
        
        # Convert string to integer if needed
        if isinstance(lighting_model, str):
            lighting_model_lower = lighting_model.lower()
            if lighting_model_lower in ['none', 'no', 'off']:
                lighting_model = self.LIGHTING_NONE
            elif lighting_model_lower in ['phong', 'phong_lighting']:
                lighting_model = self.LIGHTING_PHONG
            elif lighting_model_lower in ['phong_shadowed', 'phong_shadows', 'shadowed']:
                lighting_model = self.LIGHTING_PHONG_SHADOWED
            else:
                raise ValueError(f"Unknown lighting model string: {lighting_model}")
        
        # Validate integer value
        if lighting_model not in [self.LIGHTING_NONE, self.LIGHTING_PHONG, self.LIGHTING_PHONG_SHADOWED]:
            raise ValueError(f"Lighting model must be 0 (NONE), 1 (PHONG), or 2 (PHONG_SHADOWED), got {lighting_model}")
        
        try:
            visualizer_wrapper.set_lighting_model(self.visualizer, lighting_model)
            model_names = {0: "NONE", 1: "PHONG", 2: "PHONG_SHADOWED"}
            logger.debug(f"Lighting model set to {model_names.get(lighting_model, lighting_model)}")
        except Exception as e:
            raise VisualizerError(f"Failed to set lighting model: {e}")
    
    def colorContextPrimitivesByData(self, data_name: str, uuids: Optional[List[int]] = None) -> None:
        """
        Color context primitives based on primitive data values.
        
        This method maps primitive data values to colors using the current colormap.
        The visualization will be updated to show data variations across primitives.
        
        The data must have been previously set on the primitives in the Context using
        context.setPrimitiveDataFloat(UUID, data_name, value) before calling this method.
        
        Args:
            data_name: Name of the primitive data to use for coloring.
                      This should match the data label used with setPrimitiveDataFloat().
            uuids: Optional list of specific primitive UUIDs to color.
                   If None, all primitives in context will be colored.
                   
        Raises:
            VisualizerError: If visualizer is not initialized or operation fails
            ValueError: If data_name is invalid or UUIDs are malformed
            
        Example:
            >>> # Set data on primitives in context
            >>> context.setPrimitiveDataFloat(patch_uuid, "radiation_flux_SW", 450.2)
            >>> context.setPrimitiveDataFloat(triangle_uuid, "radiation_flux_SW", 320.1)
            >>> 
            >>> # Build geometry and color by data
            >>> visualizer.buildContextGeometry(context)
            >>> visualizer.colorContextPrimitivesByData("radiation_flux_SW")
            >>> visualizer.plotInteractive()
            
            >>> # Color only specific primitives
            >>> visualizer.colorContextPrimitivesByData("temperature", [uuid1, uuid2, uuid3])
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        if not data_name or not isinstance(data_name, str):
            raise ValueError("Data name must be a non-empty string")
        
        try:
            if uuids is None:
                # Color all primitives
                visualizer_wrapper.color_context_primitives_by_data(self.visualizer, data_name)
                logger.debug(f"Colored all primitives by data: {data_name}")
            else:
                # Color specific primitives
                if not isinstance(uuids, (list, tuple)) or not uuids:
                    raise ValueError("UUIDs must be a non-empty list or tuple")
                if not all(isinstance(uuid, _INT_TYPE) and uuid >= 0 for uuid in uuids):
                    raise ValueError("All UUIDs must be non-negative integers")
                
                visualizer_wrapper.color_context_primitives_by_data_uuids(self.visualizer, data_name, list(uuids))
                logger.debug(f"Colored {len(uuids)} primitives by data: {data_name}")
        
        except ValueError:
            # Re-raise ValueError as is
            raise
        except Exception as e:
            raise VisualizerError(f"Failed to color primitives by data '{data_name}': {e}")

    # Camera Control Methods

    def setCameraFieldOfView(self, angle_FOV: float) -> None:
        """
        Set camera field of view angle.
        
        Args:
            angle_FOV: Field of view angle in degrees
            
        Raises:
            ValueError: If angle is invalid
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")

        try:
            float(angle_FOV)
        except (TypeError, ValueError):
            raise ValueError("Field of view angle must be numeric")
        if angle_FOV <= 0 or angle_FOV >= 180:
            raise ValueError("Field of view angle must be between 0 and 180 degrees")
        
        try:
            helios_lib.setCameraFieldOfView(self.visualizer, ctypes.c_float(angle_FOV))
        except Exception as e:
            raise VisualizerError(f"Failed to set camera field of view: {e}")

    def getCameraPosition(self) -> Tuple[vec3, vec3]:
        """
        Get current camera position and look-at point.
        
        Returns:
            Tuple of (camera_position, look_at_point) as vec3 objects
            
        Raises:
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        try:
            # Prepare output arrays
            camera_pos = (ctypes.c_float * 3)()
            look_at = (ctypes.c_float * 3)()
            
            helios_lib.getCameraPosition(self.visualizer, camera_pos, look_at)
            
            return (vec3(camera_pos[0], camera_pos[1], camera_pos[2]),
                    vec3(look_at[0], look_at[1], look_at[2]))
        except Exception as e:
            raise VisualizerError(f"Failed to get camera position: {e}")

    def getBackgroundColor(self) -> RGBcolor:
        """
        Get current background color.
        
        Returns:
            Background color as RGBcolor object
            
        Raises:
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        try:
            # Prepare output array
            color = (ctypes.c_float * 3)()
            
            helios_lib.getBackgroundColor(self.visualizer, color)
            
            return RGBcolor(color[0], color[1], color[2])
        except Exception as e:
            raise VisualizerError(f"Failed to get background color: {e}")

    # Lighting Control Methods

    def setLightIntensityFactor(self, intensity_factor: float) -> None:
        """
        Set light intensity scaling factor.
        
        Args:
            intensity_factor: Light intensity scaling factor (typically 0.1 to 10.0)
            
        Raises:
            ValueError: If intensity factor is invalid
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        if not isinstance(intensity_factor, _NUMERIC_TYPES):
            raise ValueError("Light intensity factor must be numeric")
        if intensity_factor <= 0:
            raise ValueError("Light intensity factor must be positive")
        
        try:
            helios_lib.setLightIntensityFactor(self.visualizer, ctypes.c_float(intensity_factor))
        except Exception as e:
            raise VisualizerError(f"Failed to set light intensity factor: {e}")

    # Window and Display Methods

    def getWindowSize(self) -> Tuple[int, int]:
        """
        Get window size in pixels.
        
        Returns:
            Tuple of (width, height) in pixels
            
        Raises:
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        try:
            width = ctypes.c_uint()
            height = ctypes.c_uint()
            
            helios_lib.getWindowSize(self.visualizer, ctypes.byref(width), ctypes.byref(height))
            
            return (width.value, height.value)
        except Exception as e:
            raise VisualizerError(f"Failed to get window size: {e}")

    def getFramebufferSize(self) -> Tuple[int, int]:
        """
        Get framebuffer size in pixels.
        
        Returns:
            Tuple of (width, height) in pixels
            
        Raises:
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        try:
            width = ctypes.c_uint()
            height = ctypes.c_uint()
            
            helios_lib.getFramebufferSize(self.visualizer, ctypes.byref(width), ctypes.byref(height))
            
            return (width.value, height.value)
        except Exception as e:
            raise VisualizerError(f"Failed to get framebuffer size: {e}")

    def printWindowDefault(self) -> None:
        """
        Print window with default filename.
        
        Raises:
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        try:
            helios_lib.printWindowDefault(self.visualizer)
        except Exception as e:
            raise VisualizerError(f"Failed to print window: {e}")

    def displayImageFromPixels(self, pixel_data: List[int], width: int, height: int) -> None:
        """
        Display image from RGBA pixel data.
        
        Args:
            pixel_data: RGBA pixel data as list of integers (0-255)
            width: Image width in pixels
            height: Image height in pixels
            
        Raises:
            ValueError: If parameters are invalid
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        if not isinstance(pixel_data, (list, tuple)):
            raise ValueError("Pixel data must be a list or tuple")
        if not isinstance(width, _INT_TYPE) or width <= 0:
            raise ValueError("Width must be a positive integer")
        if not isinstance(height, _INT_TYPE) or height <= 0:
            raise ValueError("Height must be a positive integer")
        
        expected_size = width * height * 4  # RGBA format
        if len(pixel_data) != expected_size:
            raise ValueError(f"Pixel data size mismatch: expected {expected_size}, got {len(pixel_data)}")
        
        try:
            # Convert to ctypes array
            pixel_array = (ctypes.c_ubyte * len(pixel_data))(*pixel_data)
            helios_lib.displayImageFromPixels(self.visualizer, pixel_array, width, height)
        except Exception as e:
            raise VisualizerError(f"Failed to display image from pixels: {e}")

    def displayImageFromFile(self, filename: str) -> None:
        """
        Display image from file.
        
        Args:
            filename: Path to image file
            
        Raises:
            ValueError: If filename is invalid
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        if not isinstance(filename, str) or not filename.strip():
            raise ValueError("Filename must be a non-empty string")
        
        try:
            helios_lib.displayImageFromFile(self.visualizer, filename.encode('utf-8'))
        except Exception as e:
            raise VisualizerError(f"Failed to display image from file '{filename}': {e}")

    # Window Data Access Methods

    def getWindowPixelsRGB(self, buffer: List[int]) -> None:
        """
        Get RGB pixel data from current window.
        
        Args:
            buffer: Pre-allocated buffer to store pixel data
            
        Raises:
            ValueError: If buffer is invalid
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        if not isinstance(buffer, list):
            raise ValueError("Buffer must be a list")
        
        try:
            # Convert buffer to ctypes array
            buffer_array = (ctypes.c_uint * len(buffer))(*buffer)
            helios_lib.getWindowPixelsRGB(self.visualizer, buffer_array)
            
            # Copy results back to Python list
            for i in range(len(buffer)):
                buffer[i] = buffer_array[i]
        except Exception as e:
            raise VisualizerError(f"Failed to get window pixels: {e}")

    def getDepthMap(self) -> Tuple[List[float], int, int]:
        """
        Get depth map from current window.
        
        Returns:
            Tuple of (depth_pixels, width, height)
            
        Raises:
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        try:
            depth_ptr = ctypes.POINTER(ctypes.c_float)()
            width = ctypes.c_uint()
            height = ctypes.c_uint()
            buffer_size = ctypes.c_uint()
            
            helios_lib.getDepthMap(self.visualizer, ctypes.byref(depth_ptr), 
                                   ctypes.byref(width), ctypes.byref(height), 
                                   ctypes.byref(buffer_size))
            
            # Convert to Python list
            if depth_ptr and buffer_size.value > 0:
                depth_data = [depth_ptr[i] for i in range(buffer_size.value)]
                return (depth_data, width.value, height.value)
            else:
                return ([], 0, 0)
        except Exception as e:
            raise VisualizerError(f"Failed to get depth map: {e}")

    def plotDepthMap(self) -> None:
        """
        Plot depth map visualization.
        
        Raises:
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        try:
            helios_lib.plotDepthMap(self.visualizer)
        except Exception as e:
            raise VisualizerError(f"Failed to plot depth map: {e}")

    # Geometry Management Methods

    def clearGeometry(self) -> None:
        """
        Clear all geometry from visualizer.
        
        Raises:
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        try:
            helios_lib.clearGeometry(self.visualizer)
        except Exception as e:
            raise VisualizerError(f"Failed to clear geometry: {e}")

    def clearContextGeometry(self) -> None:
        """
        Clear context geometry from visualizer.
        
        Raises:
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        try:
            helios_lib.clearContextGeometry(self.visualizer)
        except Exception as e:
            raise VisualizerError(f"Failed to clear context geometry: {e}")

    def deleteGeometry(self, geometry_id: int) -> None:
        """
        Delete specific geometry by ID.
        
        Args:
            geometry_id: ID of geometry to delete
            
        Raises:
            ValueError: If geometry ID is invalid
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        if not isinstance(geometry_id, _INT_TYPE) or geometry_id < 0:
            raise ValueError("Geometry ID must be a non-negative integer")
        
        try:
            helios_lib.deleteGeometry(self.visualizer, geometry_id)
        except Exception as e:
            raise VisualizerError(f"Failed to delete geometry {geometry_id}: {e}")

    def updateContextPrimitiveColors(self) -> None:
        """
        Update context primitive colors.

        Raises:
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")

        try:
            helios_lib.updateContextPrimitiveColors(self.visualizer)
        except Exception as e:
            raise VisualizerError(f"Failed to update context primitive colors: {e}")

    # Geometry Vertex Manipulation Methods (v1.3.53+)

    def getGeometryVertices(self, geometry_id: int) -> List[vec3]:
        """
        Get vertices of a geometry primitive.

        Args:
            geometry_id: Unique identifier of the geometry primitive

        Returns:
            List of vertices as vec3 objects

        Raises:
            ValueError: If geometry ID is invalid
            VisualizerError: If operation fails

        Example:
            >>> # Get vertices of a specific geometry
            >>> vertices = visualizer.getGeometryVertices(geometry_id)
            >>> for vertex in vertices:
            ...     print(f"Vertex: ({vertex.x}, {vertex.y}, {vertex.z})")
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")

        if not isinstance(geometry_id, _INT_TYPE) or geometry_id < 0:
            raise ValueError("Geometry ID must be a non-negative integer")

        try:
            vertices_list = visualizer_wrapper.get_geometry_vertices(self.visualizer, geometry_id)
            # Convert [[x,y,z], ...] to [vec3(), ...]
            return [vec3(v[0], v[1], v[2]) for v in vertices_list]
        except Exception as e:
            raise VisualizerError(f"Failed to get geometry vertices: {e}")

    def setGeometryVertices(self, geometry_id: int, vertices: List[vec3]) -> None:
        """
        Set vertices of a geometry primitive.

        This allows dynamic modification of geometry shapes during visualization.
        Useful for animating geometry or adjusting shapes based on simulation results.

        Args:
            geometry_id: Unique identifier of the geometry primitive
            vertices: List of new vertices as vec3 objects

        Raises:
            ValueError: If parameters are invalid
            VisualizerError: If operation fails

        Example:
            >>> # Modify vertices of an existing geometry
            >>> vertices = visualizer.getGeometryVertices(geometry_id)
            >>> # Scale all vertices by 2x
            >>> scaled_vertices = [vec3(v.x*2, v.y*2, v.z*2) for v in vertices]
            >>> visualizer.setGeometryVertices(geometry_id, scaled_vertices)
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")

        if not isinstance(geometry_id, _INT_TYPE) or geometry_id < 0:
            raise ValueError("Geometry ID must be a non-negative integer")

        if not vertices or not isinstance(vertices, (list, tuple)):
            raise ValueError("Vertices must be a non-empty list")

        if not all(isinstance(v, vec3) for v in vertices):
            raise ValueError("All vertices must be vec3 objects")

        try:
            visualizer_wrapper.set_geometry_vertices(self.visualizer, geometry_id, vertices)
            logger.debug(f"Set {len(vertices)} vertices for geometry {geometry_id}")
        except Exception as e:
            raise VisualizerError(f"Failed to set geometry vertices: {e}")

    # Coordinate Axes and Grid Methods

    def addCoordinateAxes(self) -> None:
        """
        Add coordinate axes at origin with unit length.
        
        Raises:
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        try:
            helios_lib.addCoordinateAxes(self.visualizer)
        except Exception as e:
            raise VisualizerError(f"Failed to add coordinate axes: {e}")

    def addCoordinateAxesCustom(self, origin: vec3, length: vec3, sign: str = "both") -> None:
        """
        Add coordinate axes with custom properties.
        
        Args:
            origin: Axes origin position
            length: Axes length in each direction
            sign: Axis direction ("both" or "positive")
            
        Raises:
            ValueError: If parameters are invalid
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        if not isinstance(origin, vec3):
            raise ValueError("Origin must be a vec3")
        if not isinstance(length, vec3):
            raise ValueError("Length must be a vec3")
        if not isinstance(sign, str) or sign not in ["both", "positive"]:
            raise ValueError("Sign must be 'both' or 'positive'")
        
        try:
            origin_array = (ctypes.c_float * 3)(origin.x, origin.y, origin.z)
            length_array = (ctypes.c_float * 3)(length.x, length.y, length.z)
            helios_lib.addCoordinateAxesCustom(self.visualizer, origin_array, length_array, sign.encode('utf-8'))
        except Exception as e:
            raise VisualizerError(f"Failed to add custom coordinate axes: {e}")

    def disableCoordinateAxes(self) -> None:
        """
        Remove coordinate axes.
        
        Raises:
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        try:
            helios_lib.disableCoordinateAxes(self.visualizer)
        except Exception as e:
            raise VisualizerError(f"Failed to disable coordinate axes: {e}")

    def addGridWireFrame(self, center: vec3, size: vec3, subdivisions: List[int]) -> None:
        """
        Add grid wireframe.
        
        Args:
            center: Grid center position
            size: Grid size in each direction
            subdivisions: Grid subdivisions [x, y, z]
            
        Raises:
            ValueError: If parameters are invalid
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        if not isinstance(center, vec3):
            raise ValueError("Center must be a vec3")
        if not isinstance(size, vec3):
            raise ValueError("Size must be a vec3")
        if not isinstance(subdivisions, (list, tuple)) or len(subdivisions) != 3:
            raise ValueError("Subdivisions must be a list of 3 integers")
        if not all(isinstance(s, _INT_TYPE) and s > 0 for s in subdivisions):
            raise ValueError("All subdivisions must be positive integers")
        
        try:
            center_array = (ctypes.c_float * 3)(center.x, center.y, center.z)
            size_array = (ctypes.c_float * 3)(size.x, size.y, size.z)
            subdiv_array = (ctypes.c_int * 3)(*subdivisions)
            helios_lib.addGridWireFrame(self.visualizer, center_array, size_array, subdiv_array)
        except Exception as e:
            raise VisualizerError(f"Failed to add grid wireframe: {e}")

    # Colorbar Control Methods

    def enableColorbar(self) -> None:
        """
        Enable colorbar.
        
        Raises:
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        try:
            helios_lib.enableColorbar(self.visualizer)
        except Exception as e:
            raise VisualizerError(f"Failed to enable colorbar: {e}")

    def disableColorbar(self) -> None:
        """
        Disable colorbar.
        
        Raises:
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        try:
            helios_lib.disableColorbar(self.visualizer)
        except Exception as e:
            raise VisualizerError(f"Failed to disable colorbar: {e}")

    def setColorbarPosition(self, position: vec3) -> None:
        """
        Set colorbar position.
        
        Args:
            position: Colorbar position
            
        Raises:
            ValueError: If position is invalid
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        if not isinstance(position, vec3):
            raise ValueError("Position must be a vec3")
        
        try:
            pos_array = (ctypes.c_float * 3)(position.x, position.y, position.z)
            helios_lib.setColorbarPosition(self.visualizer, pos_array)
        except Exception as e:
            raise VisualizerError(f"Failed to set colorbar position: {e}")

    def setColorbarSize(self, width: float, height: float) -> None:
        """
        Set colorbar size.
        
        Args:
            width: Colorbar width
            height: Colorbar height
            
        Raises:
            ValueError: If size is invalid
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        if not isinstance(width, _NUMERIC_TYPES) or width <= 0:
            raise ValueError("Width must be a positive number")
        if not isinstance(height, _NUMERIC_TYPES) or height <= 0:
            raise ValueError("Height must be a positive number")
        
        try:
            size_array = (ctypes.c_float * 2)(float(width), float(height))
            helios_lib.setColorbarSize(self.visualizer, size_array)
        except Exception as e:
            raise VisualizerError(f"Failed to set colorbar size: {e}")

    def setColorbarRange(self, min_val: float, max_val: float) -> None:
        """
        Set colorbar range.
        
        Args:
            min_val: Minimum value
            max_val: Maximum value
            
        Raises:
            ValueError: If range is invalid
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        if not isinstance(min_val, _NUMERIC_TYPES):
            raise ValueError("Minimum value must be numeric")
        if not isinstance(max_val, _NUMERIC_TYPES):
            raise ValueError("Maximum value must be numeric")
        if min_val >= max_val:
            raise ValueError("Minimum value must be less than maximum value")
        
        try:
            helios_lib.setColorbarRange(self.visualizer, float(min_val), float(max_val))
        except Exception as e:
            raise VisualizerError(f"Failed to set colorbar range: {e}")

    def setColorbarTicks(self, ticks: List[float]) -> None:
        """
        Set colorbar tick marks.
        
        Args:
            ticks: List of tick values
            
        Raises:
            ValueError: If ticks are invalid
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        if not isinstance(ticks, (list, tuple)):
            raise ValueError("Ticks must be a list or tuple")
        if not all(isinstance(t, _NUMERIC_TYPES) for t in ticks):
            raise ValueError("All tick values must be numeric")
        
        try:
            if ticks:
                ticks_array = (ctypes.c_float * len(ticks))(*ticks)
                helios_lib.setColorbarTicks(self.visualizer, ticks_array, len(ticks))
            else:
                helios_lib.setColorbarTicks(self.visualizer, None, 0)
        except Exception as e:
            raise VisualizerError(f"Failed to set colorbar ticks: {e}")

    def setColorbarTitle(self, title: str) -> None:
        """
        Set colorbar title.
        
        Args:
            title: Colorbar title
            
        Raises:
            ValueError: If title is invalid
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        if not isinstance(title, str):
            raise ValueError("Title must be a string")
        
        try:
            helios_lib.setColorbarTitle(self.visualizer, title.encode('utf-8'))
        except Exception as e:
            raise VisualizerError(f"Failed to set colorbar title: {e}")

    def setColorbarFontColor(self, color: RGBcolor) -> None:
        """
        Set colorbar font color.
        
        Args:
            color: Font color
            
        Raises:
            ValueError: If color is invalid
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        if not isinstance(color, RGBcolor):
            raise ValueError("Color must be an RGBcolor")
        
        try:
            color_array = (ctypes.c_float * 3)(color.r, color.g, color.b)
            helios_lib.setColorbarFontColor(self.visualizer, color_array)
        except Exception as e:
            raise VisualizerError(f"Failed to set colorbar font color: {e}")

    def setColorbarFontSize(self, font_size: int) -> None:
        """
        Set colorbar font size.
        
        Args:
            font_size: Font size
            
        Raises:
            ValueError: If font size is invalid
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        if not isinstance(font_size, _INT_TYPE) or font_size <= 0:
            raise ValueError("Font size must be a positive integer")
        
        try:
            helios_lib.setColorbarFontSize(self.visualizer, font_size)
        except Exception as e:
            raise VisualizerError(f"Failed to set colorbar font size: {e}")

    # Colormap Methods

    def setColormap(self, colormap: Union[int, str]) -> None:
        """
        Set predefined colormap.
        
        Args:
            colormap: Colormap ID (0-5) or name ("HOT", "COOL", "RAINBOW", "LAVA", "PARULA", "GRAY")
            
        Raises:
            ValueError: If colormap is invalid
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        colormap_map = {
            "HOT": 0, "COOL": 1, "RAINBOW": 2, 
            "LAVA": 3, "PARULA": 4, "GRAY": 5
        }
        
        if isinstance(colormap, str):
            if colormap.upper() not in colormap_map:
                raise ValueError(f"Unknown colormap name: {colormap}")
            colormap_id = colormap_map[colormap.upper()]
        elif isinstance(colormap, _INT_TYPE):
            if colormap < 0 or colormap > 5:
                raise ValueError("Colormap ID must be 0-5")
            colormap_id = colormap
        else:
            raise ValueError("Colormap must be integer ID or string name")
        
        try:
            helios_lib.setColormap(self.visualizer, colormap_id)
        except Exception as e:
            raise VisualizerError(f"Failed to set colormap: {e}")

    def setCustomColormap(self, colors: List[RGBcolor], divisions: List[float]) -> None:
        """
        Set custom colormap.
        
        Args:
            colors: List of RGB colors
            divisions: List of division points (same length as colors)
            
        Raises:
            ValueError: If parameters are invalid
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        if not isinstance(colors, (list, tuple)) or not colors:
            raise ValueError("Colors must be a non-empty list")
        if not isinstance(divisions, (list, tuple)) or not divisions:
            raise ValueError("Divisions must be a non-empty list")
        if len(colors) != len(divisions):
            raise ValueError("Colors and divisions must have the same length")
        
        if not all(isinstance(c, RGBcolor) for c in colors):
            raise ValueError("All colors must be RGBcolor objects")
        if not all(isinstance(d, _NUMERIC_TYPES) for d in divisions):
            raise ValueError("All divisions must be numeric")
        
        try:
            # Flatten colors to RGB array
            color_array = (ctypes.c_float * (len(colors) * 3))()
            for i, color in enumerate(colors):
                color_array[i*3] = color.r
                color_array[i*3+1] = color.g
                color_array[i*3+2] = color.b
            
            divisions_array = (ctypes.c_float * len(divisions))(*divisions)
            
            helios_lib.setCustomColormap(self.visualizer, color_array, divisions_array, len(colors))
        except Exception as e:
            raise VisualizerError(f"Failed to set custom colormap: {e}")

    # Advanced Coloring Methods

    def colorContextPrimitivesByObjectData(self, data_name: str, obj_ids: Optional[List[int]] = None) -> None:
        """
        Color context primitives by object data.
        
        Args:
            data_name: Name of object data to use for coloring
            obj_ids: Optional list of object IDs to color (None for all)
            
        Raises:
            ValueError: If parameters are invalid
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        if not isinstance(data_name, str) or not data_name.strip():
            raise ValueError("Data name must be a non-empty string")
        
        try:
            if obj_ids is None:
                helios_lib.colorContextPrimitivesByObjectData(self.visualizer, data_name.encode('utf-8'))
            else:
                if not isinstance(obj_ids, (list, tuple)):
                    raise ValueError("Object IDs must be a list or tuple")
                if not all(isinstance(oid, _INT_TYPE) and oid >= 0 for oid in obj_ids):
                    raise ValueError("All object IDs must be non-negative integers")
                
                if obj_ids:
                    obj_ids_array = (ctypes.c_uint * len(obj_ids))(*obj_ids)
                    helios_lib.colorContextPrimitivesByObjectDataIDs(self.visualizer, data_name.encode('utf-8'), obj_ids_array, len(obj_ids))
                else:
                    helios_lib.colorContextPrimitivesByObjectDataIDs(self.visualizer, data_name.encode('utf-8'), None, 0)
        except Exception as e:
            raise VisualizerError(f"Failed to color primitives by object data '{data_name}': {e}")

    def colorContextPrimitivesRandomly(self, uuids: Optional[List[int]] = None) -> None:
        """
        Color context primitives randomly.
        
        Args:
            uuids: Optional list of primitive UUIDs to color (None for all)
            
        Raises:
            ValueError: If UUIDs are invalid
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        try:
            if uuids is None:
                helios_lib.colorContextPrimitivesRandomly(self.visualizer, None, 0)
            else:
                if not isinstance(uuids, (list, tuple)):
                    raise ValueError("UUIDs must be a list or tuple")
                if not all(isinstance(uuid, _INT_TYPE) and uuid >= 0 for uuid in uuids):
                    raise ValueError("All UUIDs must be non-negative integers")
                
                if uuids:
                    uuid_array = (ctypes.c_uint * len(uuids))(*uuids)
                    helios_lib.colorContextPrimitivesRandomly(self.visualizer, uuid_array, len(uuids))
                else:
                    helios_lib.colorContextPrimitivesRandomly(self.visualizer, None, 0)
        except Exception as e:
            raise VisualizerError(f"Failed to color primitives randomly: {e}")

    def colorContextObjectsRandomly(self, obj_ids: Optional[List[int]] = None) -> None:
        """
        Color context objects randomly.
        
        Args:
            obj_ids: Optional list of object IDs to color (None for all)
            
        Raises:
            ValueError: If object IDs are invalid
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        try:
            if obj_ids is None:
                helios_lib.colorContextObjectsRandomly(self.visualizer, None, 0)
            else:
                if not isinstance(obj_ids, (list, tuple)):
                    raise ValueError("Object IDs must be a list or tuple")
                if not all(isinstance(oid, _INT_TYPE) and oid >= 0 for oid in obj_ids):
                    raise ValueError("All object IDs must be non-negative integers")
                
                if obj_ids:
                    obj_ids_array = (ctypes.c_uint * len(obj_ids))(*obj_ids)
                    helios_lib.colorContextObjectsRandomly(self.visualizer, obj_ids_array, len(obj_ids))
                else:
                    helios_lib.colorContextObjectsRandomly(self.visualizer, None, 0)
        except Exception as e:
            raise VisualizerError(f"Failed to color objects randomly: {e}")

    def clearColor(self) -> None:
        """
        Clear primitive colors from previous coloring operations.
        
        Raises:
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        try:
            helios_lib.clearColor(self.visualizer)
        except Exception as e:
            raise VisualizerError(f"Failed to clear colors: {e}")

    # Watermark Control Methods

    def hideWatermark(self) -> None:
        """
        Hide Helios logo watermark.
        
        Raises:
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        try:
            helios_lib.hideWatermark(self.visualizer)
        except Exception as e:
            raise VisualizerError(f"Failed to hide watermark: {e}")

    def showWatermark(self) -> None:
        """
        Show Helios logo watermark.
        
        Raises:
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        try:
            helios_lib.showWatermark(self.visualizer)
        except Exception as e:
            raise VisualizerError(f"Failed to show watermark: {e}")

    def updateWatermark(self) -> None:
        """
        Update watermark geometry to match current window size.

        Raises:
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")

        try:
            helios_lib.updateWatermark(self.visualizer)
        except Exception as e:
            raise VisualizerError(f"Failed to update watermark: {e}")

    # Navigation Gizmo Methods (v1.3.53+)

    def hideNavigationGizmo(self) -> None:
        """
        Hide navigation gizmo (coordinate axes indicator in corner).

        The navigation gizmo shows XYZ axes orientation and can be clicked
        to snap the camera to standard views (top, front, side, etc.).

        Raises:
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")

        try:
            visualizer_wrapper.hide_navigation_gizmo(self.visualizer)
            logger.debug("Navigation gizmo hidden")
        except Exception as e:
            raise VisualizerError(f"Failed to hide navigation gizmo: {e}")

    def showNavigationGizmo(self) -> None:
        """
        Show navigation gizmo (coordinate axes indicator in corner).

        The navigation gizmo shows XYZ axes orientation and can be clicked
        to snap the camera to standard views (top, front, side, etc.).

        Note: Navigation gizmo is shown by default in v1.3.53+.

        Raises:
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")

        try:
            visualizer_wrapper.show_navigation_gizmo(self.visualizer)
            logger.debug("Navigation gizmo shown")
        except Exception as e:
            raise VisualizerError(f"Failed to show navigation gizmo: {e}")

    # Performance and Utility Methods

    def enableMessages(self) -> None:
        """
        Enable standard output from visualizer plugin.
        
        Raises:
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        try:
            helios_lib.enableMessages(self.visualizer)
        except Exception as e:
            raise VisualizerError(f"Failed to enable messages: {e}")

    def disableMessages(self) -> None:
        """
        Disable standard output from visualizer plugin.
        
        Raises:
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        try:
            helios_lib.disableMessages(self.visualizer)
        except Exception as e:
            raise VisualizerError(f"Failed to disable messages: {e}")

    def plotOnce(self, get_keystrokes: bool = True) -> None:
        """
        Run one rendering loop.
        
        Args:
            get_keystrokes: Whether to process keystrokes
            
        Raises:
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        
        try:
            helios_lib.plotOnce(self.visualizer, get_keystrokes)
        except Exception as e:
            raise VisualizerError(f"Failed to run plot once: {e}")

    def plotUpdateWithVisibility(self, hide_window: bool = False) -> None:
        """
        Update visualization with window visibility control.

        Args:
            hide_window: Whether to hide the window during update

        Raises:
            VisualizerError: If operation fails
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")

        try:
            with _visualizer_working_directory():
                helios_lib.plotUpdateWithVisibility(self.visualizer, hide_window)
        except Exception as e:
            raise VisualizerError(f"Failed to update plot with visibility control: {e}")

    # Point Culling and LOD Methods (v1.3.54+)

    def setPointCullingEnabled(self, enabled: bool) -> None:
        """
        Enable or disable point cloud culling optimization.

        Point culling improves rendering performance for large point clouds by
        selectively rendering only points that are visible based on distance
        and density criteria.

        Args:
            enabled: True to enable culling, False to disable (default: True)

        Raises:
            ValueError: If enabled is not a boolean
            VisualizerError: If operation fails

        Example:
            >>> with Visualizer(800, 600) as vis:
            ...     vis.setPointCullingEnabled(False)  # Disable for highest quality
            ...     vis.setPointCullingEnabled(True)   # Enable for better performance
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        if not isinstance(enabled, bool):
            raise ValueError(f"Enabled must be a boolean, got {type(enabled).__name__}")

        try:
            visualizer_wrapper.set_point_culling_enabled(self.visualizer, enabled)
            logger.debug(f"Point culling {'enabled' if enabled else 'disabled'}")
        except Exception as e:
            raise VisualizerError(f"Failed to set point culling enabled: {e}")

    def setPointCullingThreshold(self, threshold: int) -> None:
        """
        Set the minimum number of points required to trigger culling.

        Culling is only activated when the total point count exceeds this threshold.
        This prevents unnecessary culling overhead for small point clouds.

        Args:
            threshold: Point count threshold (default: 10000). Set to 0 to always enable.

        Raises:
            ValueError: If threshold is not a non-negative integer
            VisualizerError: If operation fails

        Example:
            >>> vis.setPointCullingThreshold(50000)  # Only cull for >50k points
            >>> vis.setPointCullingThreshold(0)      # Always enable culling
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        if not isinstance(threshold, int):
            raise ValueError(f"Threshold must be an integer, got {type(threshold).__name__}")
        if threshold < 0:
            raise ValueError("Point culling threshold must be non-negative")

        try:
            visualizer_wrapper.set_point_culling_threshold(self.visualizer, threshold)
            logger.debug(f"Point culling threshold set to {threshold}")
        except Exception as e:
            raise VisualizerError(f"Failed to set point culling threshold: {e}")

    def setPointMaxRenderDistance(self, distance: float) -> None:
        """
        Set the maximum rendering distance for points.

        Points beyond this distance from the camera are not rendered, improving
        performance for large scenes. The distance is measured in world units.

        Args:
            distance: Maximum distance in world units. Use 0 for auto mode (scene_size * 5.0)

        Raises:
            ValueError: If distance is negative
            VisualizerError: If operation fails

        Example:
            >>> vis.setPointMaxRenderDistance(0.0)    # Auto mode
            >>> vis.setPointMaxRenderDistance(100.0)  # Fixed distance

        Note:
            Setting distance to 0 enables automatic mode, which calculates the
            render distance based on the scene bounding box dimensions.
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        if not isinstance(distance, (int, float)):
            raise ValueError(f"Distance must be numeric, got {type(distance).__name__}")
        if distance < 0.0:
            raise ValueError("Point max render distance cannot be negative")

        try:
            visualizer_wrapper.set_point_max_render_distance(self.visualizer, float(distance))
            if distance == 0.0:
                logger.debug("Point max render distance set to auto mode")
            else:
                logger.debug(f"Point max render distance set to {distance}")
        except Exception as e:
            raise VisualizerError(f"Failed to set point max render distance: {e}")

    def setPointLODFactor(self, factor: float) -> None:
        """
        Set the level-of-detail factor for distance-based culling.

        Controls how aggressively points are culled based on distance from camera.
        Higher values result in more aggressive culling (better performance, lower quality).
        Lower values preserve more points (higher quality, lower performance).

        Args:
            factor: LOD factor (default: 10.0, typical range: 1.0-50.0). Must be positive.

        Raises:
            ValueError: If factor is not positive
            VisualizerError: If operation fails

        Example:
            >>> vis.setPointLODFactor(5.0)   # Conservative culling
            >>> vis.setPointLODFactor(10.0)  # Default culling
            >>> vis.setPointLODFactor(25.0)  # Aggressive culling

        Note:
            The LOD factor determines the rate at which point density decreases
            with distance. Higher factors mean points are culled more quickly
            as distance increases.
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")
        if not isinstance(factor, (int, float)):
            raise ValueError(f"LOD factor must be numeric, got {type(factor).__name__}")
        if factor <= 0.0:
            raise ValueError("Point LOD factor must be positive")

        # Warn about extreme values
        if factor < 1.0:
            logger.warning(f"Point LOD factor {factor} is very low (< 1.0), may cause performance issues")
        elif factor > 100.0:
            logger.warning(f"Point LOD factor {factor} is very high (> 100.0), may over-cull points")

        try:
            visualizer_wrapper.set_point_lod_factor(self.visualizer, float(factor))
            logger.debug(f"Point LOD factor set to {factor}")
        except Exception as e:
            raise VisualizerError(f"Failed to set point LOD factor: {e}")

    def getPointRenderingMetrics(self) -> dict:
        """
        Get point cloud rendering performance metrics.

        Provides detailed statistics about point cloud culling and rendering
        performance, useful for optimizing visualization settings.

        Returns:
            Dictionary with keys:
                - 'total_points' (int): Total number of points in the scene
                - 'rendered_points' (int): Number of points actually rendered after culling
                - 'culling_time_ms' (float): Time spent on culling in milliseconds

        Raises:
            VisualizerError: If operation fails

        Example:
            >>> metrics = vis.getPointRenderingMetrics()
            >>> print(f"Total: {metrics['total_points']}")
            >>> print(f"Rendered: {metrics['rendered_points']}")
            >>> cull_rate = (1 - metrics['rendered_points']/metrics['total_points']) * 100
            >>> print(f"Culling rate: {cull_rate:.1f}%")

        Note:
            Metrics are only meaningful after calling plotUpdate() or plotInteractive().
            The culling_time_ms represents CPU time spent on culling calculations,
            not total frame time.
        """
        if not self.visualizer:
            raise VisualizerError("Visualizer not initialized")

        try:
            metrics = visualizer_wrapper.get_point_rendering_metrics(self.visualizer)
            logger.debug(
                f"Point rendering metrics: {metrics['total_points']} total, "
                f"{metrics['rendered_points']} rendered, "
                f"{metrics['culling_time_ms']:.2f} ms culling time"
            )
            return metrics
        except Exception as e:
            raise VisualizerError(f"Failed to get point rendering metrics: {e}")

    def __del__(self):
        """Destructor to ensure proper cleanup."""
        if hasattr(self, 'visualizer') and self.visualizer is not None:
            try:
                with _visualizer_working_directory():
                    visualizer_wrapper.destroy_visualizer(self.visualizer)
            except Exception:
                pass  # Ignore errors during destruction