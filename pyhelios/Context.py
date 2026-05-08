import ctypes
from dataclasses import dataclass
from typing import List, Optional, Union
from enum import Enum

import numpy as np

from .wrappers import UContextWrapper as context_wrapper
from .wrappers.DataTypes import vec2, vec3, vec4, int2, int3, int4, SphericalCoord, RGBcolor, RGBAcolor, PrimitiveType, Date, Time, Location
from .plugins.loader import LibraryLoadError, validate_library, get_library_info
from .plugins.registry import get_plugin_registry
from .validation.geometry import (
    validate_patch_params, validate_triangle_params, validate_sphere_params,
    validate_tube_params, validate_box_params
)


@dataclass
class PrimitiveInfo:
    """
    Physical properties and geometry information for a primitive.
    This is separate from primitive data (user-defined key-value pairs).
    """
    uuid: int
    primitive_type: PrimitiveType
    area: float
    normal: vec3
    vertices: List[vec3]
    color: RGBcolor
    centroid: Optional[vec3] = None
    texture_file: Optional[str] = None
    texture_uv: Optional[List[vec2]] = None
    solid_fraction: Optional[float] = None

    def __post_init__(self):
        """Calculate centroid from vertices if not provided."""
        if self.centroid is None and self.vertices:
            # Calculate centroid as average of vertices
            total_x = sum(v.x for v in self.vertices)
            total_y = sum(v.y for v in self.vertices)
            total_z = sum(v.z for v in self.vertices)
            count = len(self.vertices)
            self.centroid = vec3(total_x / count, total_y / count, total_z / count)


class Context:
    """
    Central simulation environment for PyHelios that manages 3D primitives and their data.
    
    The Context class provides methods for:
    - Creating geometric primitives (patches, triangles)
    - Creating compound geometry (tiles, spheres, tubes, boxes)
    - Loading 3D models from files (PLY, OBJ, XML)
    - Managing primitive data (flexible key-value storage)
    - Querying primitive properties and collections
    - Batch operations on multiple primitives
    
    Key features:
    - UUID-based primitive tracking
    - Comprehensive primitive data system with auto-type detection
    - Efficient array-based data retrieval via getPrimitiveDataArray()
    - Cross-platform compatibility with mock mode support
    - Context manager protocol for resource cleanup
    
    Example:
        >>> with Context() as context:
        ...     # Create primitives
        ...     patch_uuid = context.addPatch(center=vec3(0, 0, 0))
        ...     triangle_uuid = context.addTriangle(vec3(0,0,0), vec3(1,0,0), vec3(0.5,1,0))
        ...     
        ...     # Set primitive data
        ...     context.setPrimitiveDataFloat(patch_uuid, "temperature", 25.5)
        ...     context.setPrimitiveDataFloat(triangle_uuid, "temperature", 30.2)
        ...     
        ...     # Get data efficiently as NumPy array
        ...     temps = context.getPrimitiveDataArray([patch_uuid, triangle_uuid], "temperature")
        ...     print(temps)  # [25.5 30.2]
    """

    def __init__(self):
        # Initialize plugin registry for availability checking
        self._plugin_registry = get_plugin_registry()

        # Track Context lifecycle state for better error messages
        self._lifecycle_state = 'initializing'

        # Check if we're in mock/development mode
        library_info = get_library_info()
        if library_info.get('is_mock', False):
            # In mock mode, don't validate but warn that functionality is limited
            print("Warning: PyHelios running in development mock mode - functionality is limited")
            print("Available plugins: None (mock mode)")
            self.context = None  # Mock context
            self._lifecycle_state = 'mock_mode'
            return
        
        # Validate native library is properly loaded before creating context
        try:
            if not validate_library():
                raise LibraryLoadError(
                    "Native Helios library validation failed. Some required functions are missing. "
                    "Try rebuilding the native library: build_scripts/build_helios"
                )
        except LibraryLoadError:
            raise
        except Exception as e:
            raise LibraryLoadError(
                f"Failed to validate native Helios library: {e}. "
                f"To enable development mode without native libraries, set PYHELIOS_DEV_MODE=1"
            )
        
        # Create the context - this will fail if library isn't properly loaded
        try:
            self.context = context_wrapper.createContext()
            if self.context is None:
                self._lifecycle_state = 'creation_failed'
                raise LibraryLoadError(
                    "Failed to create Helios context. Native library may not be functioning correctly."
                )

            self._lifecycle_state = 'active'

        except Exception as e:
            self._lifecycle_state = 'creation_failed'
            raise LibraryLoadError(
                f"Failed to create Helios context: {e}. "
                f"Ensure native libraries are built and accessible."
            )
        
    def _check_context_available(self):
        """Helper method to check if context is available with detailed error messages."""
        if self.context is None:
            # Provide specific error message based on lifecycle state
            if self._lifecycle_state == 'mock_mode':
                raise RuntimeError(
                    "Context is in mock mode - native functionality not available.\n"
                    "Build native libraries with 'python build_scripts/build_helios.py' or set PYHELIOS_DEV_MODE=1 for development."
                )
            elif self._lifecycle_state == 'cleaned_up':
                raise RuntimeError(
                    "Context has been cleaned up and is no longer usable.\n"
                    "This usually means you're trying to use a Context outside its 'with' statement scope.\n"
                    "\n"
                    "Fix: Ensure all Context usage is inside the 'with Context() as context:' block:\n"
                    "  with Context() as context:\n"
                    "      # All context operations must be here\n"
                    "      with SomePlugin(context) as plugin:\n"
                    "          plugin.do_something()\n"
                    "      with Visualizer() as vis:\n"
                    "          vis.buildContextGeometry(context)  # Still inside Context scope\n"
                    "  # Context is cleaned up here - cannot use context after this point"
                )
            elif self._lifecycle_state == 'creation_failed':
                raise RuntimeError(
                    "Context creation failed - native functionality not available.\n"
                    "Build native libraries with 'python build_scripts/build_helios.py'"
                )
            else:
                # Fallback for unknown states
                raise RuntimeError(
                    f"Context is not available (state: {self._lifecycle_state}).\n"
                    "Build native libraries with 'python build_scripts/build_helios.py' or set PYHELIOS_DEV_MODE=1 for development."
                )
    
    def _validate_uuid(self, uuid: int):
        """Validate that a UUID exists in this context.

        Args:
            uuid: The UUID to validate

        Raises:
            RuntimeError: If UUID is invalid or doesn't exist in context
        """
        # First check if it's a reasonable UUID value
        if not isinstance(uuid, int) or uuid < 0:
            raise RuntimeError(f"Invalid UUID: {uuid}. UUIDs must be non-negative integers.")

        # Check if UUID exists in context by getting all valid UUIDs
        try:
            valid_uuids = self.getAllUUIDs()
            if uuid not in valid_uuids:
                raise RuntimeError(f"UUID {uuid} does not exist in context. Valid UUIDs: {valid_uuids[:10]}{'...' if len(valid_uuids) > 10 else ''}")
        except RuntimeError:
            # Re-raise RuntimeError (validation failed)
            raise
        except Exception:
            # If we can't get valid UUIDs due to other issues (e.g., mock mode), skip validation
            # The _check_context_available() call will have already caught mock mode
            pass
        
    
    def _validate_file_path(self, filename: str, expected_extensions: List[str] = None) -> str:
        """Validate and normalize file path for security.
        
        Args:
            filename: File path to validate
            expected_extensions: List of allowed file extensions (e.g., ['.ply', '.obj'])
            
        Returns:
            Normalized absolute path
            
            
        Raises:
            ValueError: If path is invalid or potentially dangerous
            FileNotFoundError: If file does not exist
        """
        import os.path
        
        # Convert to absolute path and normalize
        abs_path = os.path.abspath(filename)
        
        # Check for path traversal attempts by verifying the resolved path is safe
        # Allow relative paths with .. as long as they resolve to valid absolute paths
        normalized_path = os.path.normpath(abs_path)
        if abs_path != normalized_path:
            raise ValueError(f"Invalid file path (potential path traversal): {filename}")
        
        # Check file extension first (before checking existence) - better UX
        if expected_extensions:
            file_ext = os.path.splitext(abs_path)[1].lower()
            if file_ext not in [ext.lower() for ext in expected_extensions]:
                raise ValueError(f"Invalid file extension '{file_ext}'. Expected one of: {expected_extensions}")
        
        # Check if file exists
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"File not found: {abs_path}")
        
        # Check if it's actually a file (not a directory)
        if not os.path.isfile(abs_path):
            raise ValueError(f"Path is not a file: {abs_path}")
        
        return abs_path

    def _validate_output_file_path(self, filename: str, expected_extensions: List[str] = None) -> str:
        """Validate and normalize output file path for security.

        Args:
            filename: Output file path to validate
            expected_extensions: List of allowed file extensions (e.g., ['.ply', '.obj'])

        Returns:
            Normalized absolute path

        Raises:
            ValueError: If path is invalid or potentially dangerous
            PermissionError: If output directory is not writable
        """
        import os.path

        # Check for empty filename
        if not filename or not filename.strip():
            raise ValueError("Filename cannot be empty")

        # Convert to absolute path and normalize
        abs_path = os.path.abspath(filename)

        # Check for path traversal attempts
        normalized_path = os.path.normpath(abs_path)
        if abs_path != normalized_path:
            raise ValueError(f"Invalid file path (potential path traversal): {filename}")

        # Check file extension
        if expected_extensions:
            file_ext = os.path.splitext(abs_path)[1].lower()
            if file_ext not in [ext.lower() for ext in expected_extensions]:
                raise ValueError(f"Invalid file extension '{file_ext}'. Expected one of: {expected_extensions}")

        # Check if output directory exists and is writable
        output_dir = os.path.dirname(abs_path)
        if not os.path.exists(output_dir):
            raise ValueError(f"Output directory does not exist: {output_dir}")
        if not os.access(output_dir, os.W_OK):
            raise PermissionError(f"Output directory is not writable: {output_dir}")

        return abs_path

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.context is not None:
            context_wrapper.destroyContext(self.context)
            self.context = None  # Prevent double deletion
            self._lifecycle_state = 'cleaned_up'

    def __del__(self):
        """Destructor to ensure C++ resources freed even without 'with' statement."""
        if hasattr(self, 'context') and self.context is not None:
            try:
                context_wrapper.destroyContext(self.context)
                self.context = None
                self._lifecycle_state = 'cleaned_up'
            except Exception as e:
                import warnings
                warnings.warn(f"Error in Context.__del__: {e}")

    def getNativePtr(self):
        self._check_context_available()
        return self.context
    
    def markGeometryClean(self):
        self._check_context_available()
        context_wrapper.markGeometryClean(self.context)
        
    def markGeometryDirty(self):
        self._check_context_available()
        context_wrapper.markGeometryDirty(self.context)
        

    def isGeometryDirty(self) -> bool:
        self._check_context_available()
        return context_wrapper.isGeometryDirty(self.context)

    def seedRandomGenerator(self, seed: int):
        """
        Seed the random number generator for reproducible stochastic results.

        Args:
            seed: Integer seed value for random number generation

        Note:
            This is critical for reproducible results in stochastic simulations
            (e.g., LiDAR scans with beam divergence, random perturbations).
        """
        self._check_context_available()
        context_wrapper.helios_lib.seedRandomGenerator(self.context, seed)

    @validate_patch_params
    def addPatch(self, center: vec3 = vec3(0, 0, 0), size: vec2 = vec2(1, 1), rotation: Optional[SphericalCoord] = None, color: Optional[RGBcolor] = None) -> int:
        self._check_context_available()
        rotation = rotation or SphericalCoord(1, 0, 0)  # radius=1, elevation=0, azimuth=0 (no effective rotation)
        color = color or RGBcolor(1, 1, 1)
        # C++ interface expects [radius, elevation, azimuth] (3 values), not [radius, elevation, zenith, azimuth] (4 values)
        rotation_list = [rotation.radius, rotation.elevation, rotation.azimuth]
        return context_wrapper.addPatchWithCenterSizeRotationAndColor(self.context, center.to_list(), size.to_list(), rotation_list, color.to_list())

    def addPatchTextured(self, center: vec3, size: vec2, texture_file: str,
                         rotation: Optional[SphericalCoord] = None,
                         uv_center: Optional[vec2] = None,
                         uv_size: Optional[vec2] = None) -> int:
        """Add a textured patch primitive to the context.

        Creates a rectangular patch with a texture image mapped to its surface.

        Args:
            center: 3D position of the patch center
            size: Width and height of the patch
            texture_file: Path to texture image file (supports PNG, JPG, JPEG, TGA, BMP)
            rotation: Optional spherical rotation (defaults to no rotation)
            uv_center: Optional UV center of texture map (required if uv_size is provided)
            uv_size: Optional UV size of texture map (required if uv_center is provided)

        Returns:
            UUID of the created textured patch primitive

        Raises:
            ValueError: If arguments have wrong types or UV params are partially specified
            FileNotFoundError: If texture file doesn't exist
            RuntimeError: If context is in mock mode

        Example:
            >>> context = Context()
            >>> uuid = context.addPatchTextured(
            ...     center=vec3(0, 0, 0),
            ...     size=vec2(2, 2),
            ...     texture_file="texture.png"
            ... )
        """
        self._check_context_available()

        if not isinstance(center, vec3):
            raise ValueError(f"center must be a vec3, got {type(center).__name__}")
        if not isinstance(size, vec2):
            raise ValueError(f"size must be a vec2, got {type(size).__name__}")
        if not isinstance(texture_file, str):
            raise ValueError(f"texture_file must be a str, got {type(texture_file).__name__}")
        if rotation is not None and not isinstance(rotation, SphericalCoord):
            raise ValueError(f"rotation must be a SphericalCoord, got {type(rotation).__name__}")

        if (uv_center is None) != (uv_size is None):
            raise ValueError("uv_center and uv_size must both be provided or both omitted")
        if uv_center is not None and not isinstance(uv_center, vec2):
            raise ValueError(f"uv_center must be a vec2, got {type(uv_center).__name__}")
        if uv_size is not None and not isinstance(uv_size, vec2):
            raise ValueError(f"uv_size must be a vec2, got {type(uv_size).__name__}")

        validated_texture_file = self._validate_file_path(texture_file,
                                                          ['.png', '.jpg', '.jpeg', '.tga', '.bmp'])

        rotation = rotation or SphericalCoord(1, 0, 0)
        rotation_list = [rotation.radius, rotation.elevation, rotation.azimuth]

        if uv_center is not None:
            return context_wrapper.addPatchWithTextureAndUV(
                self.context, center.to_list(), size.to_list(), rotation_list,
                validated_texture_file, uv_center.to_list(), uv_size.to_list()
            )
        else:
            return context_wrapper.addPatchWithTexture(
                self.context, center.to_list(), size.to_list(), rotation_list,
                validated_texture_file
            )

    @validate_triangle_params
    def addTriangle(self, vertex0: vec3, vertex1: vec3, vertex2: vec3, color: Optional[RGBcolor] = None) -> int:
        """Add a triangle primitive to the context
        
        Args:
            vertex0: First vertex of the triangle
            vertex1: Second vertex of the triangle  
            vertex2: Third vertex of the triangle
            color: Optional triangle color (defaults to white)
            
        Returns:
            UUID of the created triangle primitive
        """
        self._check_context_available()
        if color is None:
            return context_wrapper.addTriangle(self.context, vertex0.to_list(), vertex1.to_list(), vertex2.to_list())
        else:
            return context_wrapper.addTriangleWithColor(self.context, vertex0.to_list(), vertex1.to_list(), vertex2.to_list(), color.to_list())

    def addTriangleTextured(self, vertex0: vec3, vertex1: vec3, vertex2: vec3, 
                           texture_file: str, uv0: vec2, uv1: vec2, uv2: vec2) -> int:
        """Add a textured triangle primitive to the context
        
        Creates a triangle with texture mapping. The texture image is mapped to the triangle
        surface using UV coordinates, where (0,0) represents the top-left corner of the image
        and (1,1) represents the bottom-right corner.
        
        Args:
            vertex0: First vertex of the triangle
            vertex1: Second vertex of the triangle
            vertex2: Third vertex of the triangle
            texture_file: Path to texture image file (supports PNG, JPG, JPEG, TGA, BMP)
            uv0: UV texture coordinates for first vertex
            uv1: UV texture coordinates for second vertex
            uv2: UV texture coordinates for third vertex
            
        Returns:
            UUID of the created textured triangle primitive
            
        Raises:
            ValueError: If texture file path is invalid
            FileNotFoundError: If texture file doesn't exist
            RuntimeError: If context is in mock mode
            
        Example:
            >>> context = Context()
            >>> # Create a textured triangle
            >>> vertex0 = vec3(0, 0, 0)
            >>> vertex1 = vec3(1, 0, 0) 
            >>> vertex2 = vec3(0.5, 1, 0)
            >>> uv0 = vec2(0, 0)     # Bottom-left of texture
            >>> uv1 = vec2(1, 0)     # Bottom-right of texture
            >>> uv2 = vec2(0.5, 1)   # Top-center of texture
            >>> uuid = context.addTriangleTextured(vertex0, vertex1, vertex2, 
            ...                                    "texture.png", uv0, uv1, uv2)
        """
        self._check_context_available()

        # Parameter type validation
        for name, val in [("vertex0", vertex0), ("vertex1", vertex1), ("vertex2", vertex2)]:
            if not isinstance(val, vec3):
                raise ValueError(f"{name} must be a vec3, got {type(val).__name__}")
        for name, val in [("uv0", uv0), ("uv1", uv1), ("uv2", uv2)]:
            if not isinstance(val, vec2):
                raise ValueError(f"{name} must be a vec2, got {type(val).__name__}")

        # Validate texture file path
        validated_texture_file = self._validate_file_path(texture_file,
                                                          ['.png', '.jpg', '.jpeg', '.tga', '.bmp'])

        # Call the wrapper function
        return context_wrapper.addTriangleWithTexture(
            self.context,
            vertex0.to_list(), vertex1.to_list(), vertex2.to_list(),
            validated_texture_file,
            uv0.to_list(), uv1.to_list(), uv2.to_list()
        )

    def getPrimitiveType(self, uuid):
        """Get the type of a primitive or multiple primitives.

        Args:
            uuid: Single UUID (int) or list of UUIDs

        Returns:
            PrimitiveType for single UUID, or np.ndarray of shape (N,) uint32 for list
        """
        self._check_context_available()
        if isinstance(uuid, (list, tuple)):
            if not uuid:
                return np.empty((0,), dtype=np.uint32)
            ptr, size = context_wrapper.getBatchPrimitiveTypes(self.context, uuid)
            if size == 0 or not ptr:
                return np.empty((0,), dtype=np.uint32)
            return np.ctypeslib.as_array(ptr, shape=(size,)).copy()
        primitive_type = context_wrapper.getPrimitiveType(self.context, uuid)
        return PrimitiveType(primitive_type)

    def getPrimitiveArea(self, uuid):
        """Get the area of a primitive or multiple primitives.

        Args:
            uuid: Single UUID (int) or list of UUIDs

        Returns:
            float for single UUID, or np.ndarray of shape (N,) for list
        """
        self._check_context_available()
        if isinstance(uuid, (list, tuple)):
            if not uuid:
                return np.empty((0,), dtype=np.float32)
            ptr, size = context_wrapper.getBatchPrimitiveAreas(self.context, uuid)
            if size == 0 or not ptr:
                return np.empty((0,), dtype=np.float32)
            return np.ctypeslib.as_array(ptr, shape=(size,)).copy()
        return context_wrapper.getPrimitiveArea(self.context, uuid)

    def getPrimitiveNormal(self, uuid):
        """Get the normal vector of a primitive or multiple primitives.

        Args:
            uuid: Single UUID (int) or list of UUIDs

        Returns:
            vec3 for single UUID, or np.ndarray of shape (N, 3) for list
        """
        self._check_context_available()
        if isinstance(uuid, (list, tuple)):
            if not uuid:
                return np.empty((0, 3), dtype=np.float32)
            ptr, size = context_wrapper.getBatchPrimitiveNormals(self.context, uuid)
            if size == 0 or not ptr:
                return np.empty((0, 3), dtype=np.float32)
            return np.ctypeslib.as_array(ptr, shape=(size,)).copy().reshape(-1, 3)
        normal_ptr = context_wrapper.getPrimitiveNormal(self.context, uuid)
        return vec3(normal_ptr[0], normal_ptr[1], normal_ptr[2])

    def getPrimitiveVertices(self, uuid):
        """Get vertices of a primitive or multiple primitives.

        Args:
            uuid: Single UUID (int) or list of UUIDs

        Returns:
            List[vec3] for single UUID, or tuple of (flat_data, offsets) for list
            where flat_data is a float32 ndarray and offsets is a uint32 ndarray
            of length N+1. Vertices for primitive i are at
            flat_data[offsets[i]:offsets[i+1]].
        """
        self._check_context_available()
        if isinstance(uuid, (list, tuple)):
            if not uuid:
                return (np.empty((0,), dtype=np.float32), np.zeros((1,), dtype=np.uint32))
            ptr, offsets, total = context_wrapper.getBatchPrimitiveVertices(self.context, uuid)
            offsets_arr = np.array(offsets, dtype=np.uint32)
            if total == 0 or not ptr:
                return (np.empty((0,), dtype=np.float32), offsets_arr)
            data = np.ctypeslib.as_array(ptr, shape=(total,)).copy()
            return (data, offsets_arr)
        size = ctypes.c_uint()
        vertices_ptr = context_wrapper.getPrimitiveVertices(self.context, uuid, ctypes.byref(size))
        # size.value is the total number of floats (3 per vertex), not the number of vertices
        vertices_list = ctypes.cast(vertices_ptr, ctypes.POINTER(ctypes.c_float * size.value)).contents
        vertices = [vec3(vertices_list[i], vertices_list[i+1], vertices_list[i+2]) for i in range(0, size.value, 3)]
        return vertices

    def getPrimitiveColor(self, uuid):
        """Get the color of a primitive or multiple primitives.

        Args:
            uuid: Single UUID (int) or list of UUIDs

        Returns:
            RGBcolor for single UUID, or np.ndarray of shape (N, 3) for list
        """
        self._check_context_available()
        if isinstance(uuid, (list, tuple)):
            if not uuid:
                return np.empty((0, 3), dtype=np.float32)
            ptr, size = context_wrapper.getBatchPrimitiveColors(self.context, uuid)
            if size == 0 or not ptr:
                return np.empty((0, 3), dtype=np.float32)
            return np.ctypeslib.as_array(ptr, shape=(size,)).copy().reshape(-1, 3)
        color_ptr = context_wrapper.getPrimitiveColor(self.context, uuid)
        return RGBcolor(color_ptr[0], color_ptr[1], color_ptr[2])

    def getPrimitiveCount(self) -> int:
        self._check_context_available()
        return context_wrapper.getPrimitiveCount(self.context)

    def doesPrimitiveExist(self, uuid) -> bool:
        """Check if a primitive exists for a given UUID or list of UUIDs.

        Args:
            uuid: A single UUID (int) or a list of UUIDs.

        Returns:
            True if the primitive(s) exist, False otherwise.
            For a list, returns True only if ALL primitives exist.
        """
        self._check_context_available()
        if isinstance(uuid, (list, tuple)):
            arr = (ctypes.c_uint * len(uuid))(*uuid)
            return context_wrapper.doesPrimitiveExistBatch(self.context, arr, len(uuid))
        return context_wrapper.doesPrimitiveExist(self.context, uuid)

    def getAllUUIDs(self) -> List[int]:
        self._check_context_available()
        size = ctypes.c_uint()
        uuids_ptr = context_wrapper.getAllUUIDs(self.context, ctypes.byref(size))
        return list(uuids_ptr[:size.value])

    def getObjectCount(self) -> int:
        self._check_context_available()
        return context_wrapper.getObjectCount(self.context)

    def getAllObjectIDs(self) -> List[int]:
        self._check_context_available()
        size = ctypes.c_uint()
        objectids_ptr = context_wrapper.getAllObjectIDs(self.context, ctypes.byref(size))
        return list(objectids_ptr[:size.value])

    def getPrimitiveInfo(self, uuid: int) -> PrimitiveInfo:
        """
        Get physical properties and geometry information for a single primitive.

        Args:
            uuid: UUID of the primitive

        Returns:
            PrimitiveInfo object containing physical properties and geometry
        """
        primitive_type = self.getPrimitiveType(uuid)
        area = self.getPrimitiveArea(uuid)
        normal = self.getPrimitiveNormal(uuid)
        vertices = self.getPrimitiveVertices(uuid)
        color = self.getPrimitiveColor(uuid)

        texture_file = None
        texture_uv = None
        solid_fraction = None
        try:
            tf = self.getPrimitiveTextureFile(uuid)
            if tf:
                texture_file = tf
            texture_uv = self.getPrimitiveTextureUV(uuid)
            if not texture_uv:
                texture_uv = None
            solid_fraction = self.getPrimitiveSolidFraction(uuid)
        except Exception:
            pass

        return PrimitiveInfo(
            uuid=uuid,
            primitive_type=primitive_type,
            area=area,
            normal=normal,
            vertices=vertices,
            color=color,
            texture_file=texture_file,
            texture_uv=texture_uv,
            solid_fraction=solid_fraction,
        )

    def getAllPrimitiveInfo(self) -> List[PrimitiveInfo]:
        """
        Get physical properties and geometry information for all primitives in the context.
        
        Returns:
            List of PrimitiveInfo objects for all primitives
        """
        all_uuids = self.getAllUUIDs()
        return [self.getPrimitiveInfo(uuid) for uuid in all_uuids]

    def getPrimitivesInfoForObject(self, object_id: int) -> List[PrimitiveInfo]:
        """
        Get physical properties and geometry information for all primitives belonging to a specific object.
        
        Args:
            object_id: ID of the object
            
        Returns:
            List of PrimitiveInfo objects for primitives in the object
        """
        object_uuids = context_wrapper.getObjectPrimitiveUUIDs(self.context, object_id)
        return [self.getPrimitiveInfo(uuid) for uuid in object_uuids]

    # Compound geometry methods
    def addTile(self, center: vec3 = vec3(0, 0, 0), size: vec2 = vec2(1, 1), 
                rotation: Optional[SphericalCoord] = None, subdiv: int2 = int2(1, 1), 
                color: Optional[RGBcolor] = None) -> List[int]:
        """
        Add a subdivided patch (tile) to the context.
        
        A tile is a patch subdivided into a regular grid of smaller patches,
        useful for creating detailed surfaces or terrain.
        
        Args:
            center: 3D coordinates of tile center (default: origin)
            size: Width and height of the tile (default: 1x1)
            rotation: Orientation of the tile (default: no rotation)
            subdiv: Number of subdivisions in x and y directions (default: 1x1)
            color: Color of the tile (default: white)
            
        Returns:
            List of UUIDs for all patches created in the tile
            
        Example:
            >>> context = Context()
            >>> # Create a 2x2 meter tile subdivided into 4x4 patches
            >>> tile_uuids = context.addTile(
            ...     center=vec3(0, 0, 1),
            ...     size=vec2(2, 2), 
            ...     subdiv=int2(4, 4),
            ...     color=RGBcolor(0.5, 0.8, 0.2)
            ... )
            >>> print(f"Created {len(tile_uuids)} patches")
        """
        self._check_context_available()

        # Parameter type validation
        if not isinstance(center, vec3):
            raise ValueError(f"Center must be a vec3, got {type(center).__name__}")
        if not isinstance(size, vec2):
            raise ValueError(f"Size must be a vec2, got {type(size).__name__}")
        if rotation is not None and not isinstance(rotation, SphericalCoord):
            raise ValueError(f"Rotation must be a SphericalCoord or None, got {type(rotation).__name__}")
        if not isinstance(subdiv, int2):
            raise ValueError(f"Subdiv must be an int2, got {type(subdiv).__name__}")
        if color is not None and not isinstance(color, RGBcolor):
            raise ValueError(f"Color must be an RGBcolor or None, got {type(color).__name__}")

        # Parameter value validation
        if any(s <= 0 for s in size.to_list()):
            raise ValueError("All size dimensions must be positive")
        if any(s <= 0 for s in subdiv.to_list()):
            raise ValueError("All subdivision counts must be positive")
            
        rotation = rotation or SphericalCoord(1, 0, 0)
        color = color or RGBcolor(1, 1, 1)
        
        # Extract only radius, elevation, azimuth for C++ interface
        rotation_list = [rotation.radius, rotation.elevation, rotation.azimuth]
        
        if color and not (color.r == 1.0 and color.g == 1.0 and color.b == 1.0):
            return context_wrapper.addTileWithColor(
                self.context, center.to_list(), size.to_list(), 
                rotation_list, subdiv.to_list(), color.to_list()
            )
        else:
            return context_wrapper.addTile(
                self.context, center.to_list(), size.to_list(), 
                rotation_list, subdiv.to_list()
            )

    @validate_sphere_params
    def addSphere(self, center: vec3 = vec3(0, 0, 0), radius: float = 1.0, 
                  ndivs: int = 10, color: Optional[RGBcolor] = None) -> List[int]:
        """
        Add a sphere to the context.
        
        The sphere is tessellated into triangular faces based on the specified
        number of divisions.
        
        Args:
            center: 3D coordinates of sphere center (default: origin)
            radius: Radius of the sphere (default: 1.0)
            ndivs: Number of divisions for tessellation (default: 10)
                  Higher values create smoother spheres but more triangles
            color: Color of the sphere (default: white)
            
        Returns:
            List of UUIDs for all triangles created in the sphere
            
        Example:
            >>> context = Context()
            >>> # Create a red sphere at (1, 2, 3) with radius 0.5
            >>> sphere_uuids = context.addSphere(
            ...     center=vec3(1, 2, 3),
            ...     radius=0.5,
            ...     ndivs=20,
            ...     color=RGBcolor(1, 0, 0)
            ... )
            >>> print(f"Created sphere with {len(sphere_uuids)} triangles")
        """
        self._check_context_available()

        # Parameter type validation
        if not isinstance(center, vec3):
            raise ValueError(f"Center must be a vec3, got {type(center).__name__}")
        if not isinstance(radius, (int, float)):
            raise ValueError(f"Radius must be a number, got {type(radius).__name__}")
        if not isinstance(ndivs, int):
            raise ValueError(f"Ndivs must be an integer, got {type(ndivs).__name__}")
        if color is not None and not isinstance(color, RGBcolor):
            raise ValueError(f"Color must be an RGBcolor or None, got {type(color).__name__}")

        # Parameter value validation
        if radius <= 0:
            raise ValueError("Sphere radius must be positive")
        if ndivs < 3:
            raise ValueError("Number of divisions must be at least 3")
        
        if color:
            return context_wrapper.addSphereWithColor(
                self.context, ndivs, center.to_list(), radius, color.to_list()
            )
        else:
            return context_wrapper.addSphere(
                self.context, ndivs, center.to_list(), radius
            )

    @validate_tube_params
    def addTube(self, nodes: List[vec3], radii: Union[float, List[float]], 
                ndivs: int = 6, colors: Optional[Union[RGBcolor, List[RGBcolor]]] = None) -> List[int]:
        """
        Add a tube (pipe/cylinder) to the context.
        
        The tube is defined by a series of nodes (path) with radius at each node.
        It's tessellated into triangular faces based on the number of radial divisions.
        
        Args:
            nodes: List of 3D points defining the tube path (at least 2 nodes)
            radii: Radius at each node. Can be:
                  - Single float: constant radius for all nodes
                  - List of floats: radius for each node (must match nodes length)
            ndivs: Number of radial divisions (default: 6)
                  Higher values create smoother tubes but more triangles
            colors: Colors at each node. Can be:
                   - None: white tube
                   - Single RGBcolor: constant color for all nodes
                   - List of RGBcolor: color for each node (must match nodes length)
                   
        Returns:
            List of UUIDs for all triangles created in the tube
            
        Example:
            >>> context = Context()
            >>> # Create a curved tube with varying radius
            >>> nodes = [vec3(0, 0, 0), vec3(1, 0, 0), vec3(2, 1, 0)]
            >>> radii = [0.1, 0.2, 0.1]
            >>> colors = [RGBcolor(1, 0, 0), RGBcolor(0, 1, 0), RGBcolor(0, 0, 1)]
            >>> tube_uuids = context.addTube(nodes, radii, ndivs=8, colors=colors)
            >>> print(f"Created tube with {len(tube_uuids)} triangles")
        """
        self._check_context_available()

        # Parameter type validation
        if not isinstance(nodes, (list, tuple)):
            raise ValueError(f"Nodes must be a list or tuple, got {type(nodes).__name__}")
        if not isinstance(ndivs, int):
            raise ValueError(f"Ndivs must be an integer, got {type(ndivs).__name__}")
        if colors is not None and not isinstance(colors, (RGBcolor, list, tuple)):
            raise ValueError(f"Colors must be RGBcolor, list, tuple, or None, got {type(colors).__name__}")

        # Parameter value validation
        if len(nodes) < 2:
            raise ValueError("Tube requires at least 2 nodes")
        if ndivs < 3:
            raise ValueError("Number of radial divisions must be at least 3")
        
        # Handle radius parameter
        if isinstance(radii, (int, float)):
            radii_list = [float(radii)] * len(nodes)
        else:
            radii_list = [float(r) for r in radii]
            if len(radii_list) != len(nodes):
                raise ValueError(f"Number of radii ({len(radii_list)}) must match number of nodes ({len(nodes)})")
        
        # Validate radii
        if any(r <= 0 for r in radii_list):
            raise ValueError("All radii must be positive")
        
        # Convert nodes to flat list
        nodes_flat = []
        for node in nodes:
            nodes_flat.extend(node.to_list())
        
        # Handle colors parameter
        if colors is None:
            return context_wrapper.addTube(self.context, ndivs, nodes_flat, radii_list)
        elif isinstance(colors, RGBcolor):
            # Single color for all nodes
            colors_flat = colors.to_list() * len(nodes)
        else:
            # List of colors
            if len(colors) != len(nodes):
                raise ValueError(f"Number of colors ({len(colors)}) must match number of nodes ({len(nodes)})")
            colors_flat = []
            for color in colors:
                colors_flat.extend(color.to_list())
        
        return context_wrapper.addTubeWithColor(self.context, ndivs, nodes_flat, radii_list, colors_flat)

    @validate_box_params
    def addBox(self, center: vec3 = vec3(0, 0, 0), size: vec3 = vec3(1, 1, 1), 
               subdiv: int3 = int3(1, 1, 1), color: Optional[RGBcolor] = None) -> List[int]:
        """
        Add a rectangular box to the context.
        
        The box is subdivided into patches on each face based on the specified
        subdivisions.
        
        Args:
            center: 3D coordinates of box center (default: origin)
            size: Width, height, and depth of the box (default: 1x1x1)
            subdiv: Number of subdivisions in x, y, and z directions (default: 1x1x1)
                   Higher values create more detailed surfaces
            color: Color of the box (default: white)
            
        Returns:
            List of UUIDs for all patches created on the box faces
            
        Example:
            >>> context = Context()
            >>> # Create a blue box subdivided for detail
            >>> box_uuids = context.addBox(
            ...     center=vec3(0, 0, 2),
            ...     size=vec3(2, 1, 0.5),
            ...     subdiv=int3(4, 2, 1),
            ...     color=RGBcolor(0, 0, 1)
            ... )
            >>> print(f"Created box with {len(box_uuids)} patches")
        """
        self._check_context_available()

        # Parameter type validation
        if not isinstance(center, vec3):
            raise ValueError(f"Center must be a vec3, got {type(center).__name__}")
        if not isinstance(size, vec3):
            raise ValueError(f"Size must be a vec3, got {type(size).__name__}")
        if not isinstance(subdiv, int3):
            raise ValueError(f"Subdiv must be an int3, got {type(subdiv).__name__}")
        if color is not None and not isinstance(color, RGBcolor):
            raise ValueError(f"Color must be an RGBcolor or None, got {type(color).__name__}")

        # Parameter value validation
        if any(s <= 0 for s in size.to_list()):
            raise ValueError("All box dimensions must be positive")
        if any(s < 1 for s in subdiv.to_list()):
            raise ValueError("All subdivision counts must be at least 1")
        
        if color:
            return context_wrapper.addBoxWithColor(
                self.context, center.to_list(), size.to_list(), 
                subdiv.to_list(), color.to_list()
            )
        else:
            return context_wrapper.addBox(
                self.context, center.to_list(), size.to_list(), subdiv.to_list()
            )

    def addDisk(self, center: vec3 = vec3(0, 0, 0), size: vec2 = vec2(1, 1),
                ndivs: Union[int, int2] = 20, rotation: Optional[SphericalCoord] = None,
                color: Optional[Union[RGBcolor, RGBAcolor]] = None) -> List[int]:
        """
        Add a disk (circular or elliptical surface) to the context.

        A disk is a flat circular or elliptical surface tessellated into
        triangular faces. Supports both uniform radial subdivisions and
        separate radial/azimuthal subdivisions for finer control.

        Args:
            center: 3D coordinates of disk center (default: origin)
            size: Semi-major and semi-minor radii of the disk (default: 1x1 circle)
            ndivs: Number of radial divisions (int) or [radial, azimuthal] divisions (int2)
                   (default: 20). Higher values create smoother circles but more triangles.
            rotation: Orientation of the disk (default: horizontal, normal = +z)
            color: Color of the disk (default: white). Can be RGBcolor or RGBAcolor for transparency.

        Returns:
            List of UUIDs for all triangles created in the disk

        Example:
            >>> context = Context()
            >>> # Create a red disk at (0, 0, 1) with radius 0.5
            >>> disk_uuids = context.addDisk(
            ...     center=vec3(0, 0, 1),
            ...     size=vec2(0.5, 0.5),
            ...     ndivs=30,
            ...     color=RGBcolor(1, 0, 0)
            ... )
            >>> print(f"Created disk with {len(disk_uuids)} triangles")
            >>>
            >>> # Create a semi-transparent blue elliptical disk
            >>> disk_uuids = context.addDisk(
            ...     center=vec3(0, 0, 2),
            ...     size=vec2(1.0, 0.5),
            ...     ndivs=40,
            ...     rotation=SphericalCoord(1, 0.5, 0),
            ...     color=RGBAcolor(0, 0, 1, 0.5)
            ... )
            >>>
            >>> # Create disk with polar/radial subdivisions for finer control
            >>> disk_uuids = context.addDisk(
            ...     center=vec3(0, 0, 3),
            ...     size=vec2(1, 1),
            ...     ndivs=int2(10, 20),  # 10 radial, 20 azimuthal divisions
            ...     color=RGBcolor(0, 1, 0)
            ... )
        """
        self._check_context_available()

        # Parameter type validation
        if not isinstance(center, vec3):
            raise ValueError(f"Center must be a vec3, got {type(center).__name__}")
        if not isinstance(size, vec2):
            raise ValueError(f"Size must be a vec2, got {type(size).__name__}")
        if not isinstance(ndivs, (int, int2)):
            raise ValueError(f"Ndivs must be an int or int2, got {type(ndivs).__name__}")
        if rotation is not None and not isinstance(rotation, SphericalCoord):
            raise ValueError(f"Rotation must be a SphericalCoord or None, got {type(rotation).__name__}")
        if color is not None and not isinstance(color, (RGBcolor, RGBAcolor)):
            raise ValueError(f"Color must be an RGBcolor, RGBAcolor, or None, got {type(color).__name__}")

        # Parameter value validation
        if any(s <= 0 for s in size.to_list()):
            raise ValueError("Disk size must be positive")

        # Validate subdivisions based on type
        if isinstance(ndivs, int):
            if ndivs < 3:
                raise ValueError("Number of divisions must be at least 3")
        else:  # int2
            if any(n < 1 for n in ndivs.to_list()):
                raise ValueError("Radial and angular divisions must be at least 1")

        # Default rotation (horizontal disk, normal pointing +z)
        if rotation is None:
            rotation = SphericalCoord(1, 0, 0)

        # CRITICAL: Extract only radius, elevation, azimuth for C++ interface
        # (rotation.to_list() returns 4 values, but C++ expects 3)
        rotation_list = [rotation.radius, rotation.elevation, rotation.azimuth]

        # Dispatch based on ndivs and color types
        if isinstance(ndivs, int2):
            # Polar subdivisions variant (supports RGB and RGBA color)
            if color:
                if isinstance(color, RGBAcolor):
                    return context_wrapper.addDiskPolarSubdivisionsRGBA(
                        self.context, ndivs.to_list(), center.to_list(), size.to_list(),
                        rotation_list, color.to_list()
                    )
                else:
                    # RGB color
                    return context_wrapper.addDiskPolarSubdivisions(
                        self.context, ndivs.to_list(), center.to_list(), size.to_list(),
                        rotation_list, color.to_list()
                    )
            else:
                # No color - use default white
                color_list = [1.0, 1.0, 1.0]
                return context_wrapper.addDiskPolarSubdivisions(
                    self.context, ndivs.to_list(), center.to_list(), size.to_list(),
                    rotation_list, color_list
                )
        else:
            # Uniform radial subdivisions
            if color:
                if isinstance(color, RGBAcolor):
                    # RGBA color variant
                    return context_wrapper.addDiskWithRGBAColor(
                        self.context, ndivs, center.to_list(), size.to_list(),
                        rotation_list, color.to_list()
                    )
                else:
                    # RGB color variant
                    return context_wrapper.addDiskWithColor(
                        self.context, ndivs, center.to_list(), size.to_list(),
                        rotation_list, color.to_list()
                    )
            else:
                # No color - use rotation variant
                return context_wrapper.addDiskWithRotation(
                    self.context, ndivs, center.to_list(), size.to_list(),
                    rotation_list
                )

    def addCone(self, node0: vec3, node1: vec3, radius0: float, radius1: float,
                ndivs: int = 20, color: Optional[RGBcolor] = None) -> List[int]:
        """
        Add a cone (or cylinder/frustum) to the context.

        A cone is a 3D shape connecting two circular cross-sections with
        potentially different radii. When radii are equal, creates a cylinder.
        When one radius is zero, creates a true cone.

        Args:
            node0: 3D coordinates of the base center
            node1: 3D coordinates of the apex center
            radius0: Radius at base (node0). Use 0 for pointed end.
            radius1: Radius at apex (node1). Use 0 for pointed end.
            ndivs: Number of radial divisions for tessellation (default: 20)
            color: Color of the cone (default: white)

        Returns:
            List of UUIDs for all triangles created in the cone

        Example:
            >>> context = Context()
            >>> # Create a cylinder (equal radii)
            >>> cylinder_uuids = context.addCone(
            ...     node0=vec3(0, 0, 0),
            ...     node1=vec3(0, 0, 2),
            ...     radius0=0.5,
            ...     radius1=0.5,
            ...     ndivs=20
            ... )
            >>>
            >>> # Create a true cone (one radius = 0)
            >>> cone_uuids = context.addCone(
            ...     node0=vec3(1, 0, 0),
            ...     node1=vec3(1, 0, 1.5),
            ...     radius0=0.5,
            ...     radius1=0.0,
            ...     ndivs=24,
            ...     color=RGBcolor(1, 0, 0)
            ... )
            >>>
            >>> # Create a frustum (different radii)
            >>> frustum_uuids = context.addCone(
            ...     node0=vec3(2, 0, 0),
            ...     node1=vec3(2, 0, 1),
            ...     radius0=0.8,
            ...     radius1=0.4,
            ...     ndivs=16
            ... )
        """
        self._check_context_available()

        # Parameter type validation
        if not isinstance(node0, vec3):
            raise ValueError(f"node0 must be a vec3, got {type(node0).__name__}")
        if not isinstance(node1, vec3):
            raise ValueError(f"node1 must be a vec3, got {type(node1).__name__}")
        if not isinstance(ndivs, int):
            raise ValueError(f"ndivs must be an int, got {type(ndivs).__name__}")
        if color is not None and not isinstance(color, RGBcolor):
            raise ValueError(f"Color must be an RGBcolor or None, got {type(color).__name__}")

        # Parameter value validation
        if radius0 < 0 or radius1 < 0:
            raise ValueError("Radii must be non-negative")
        if ndivs < 3:
            raise ValueError("Number of radial divisions must be at least 3")

        # Dispatch based on color
        if color:
            return context_wrapper.addConeWithColor(
                self.context, ndivs, node0.to_list(), node1.to_list(),
                radius0, radius1, color.to_list()
            )
        else:
            return context_wrapper.addCone(
                self.context, ndivs, node0.to_list(), node1.to_list(),
                radius0, radius1
            )

    def addSphereObject(self, center: vec3 = vec3(0, 0, 0),
                       radius: Union[float, vec3] = 1.0, ndivs: int = 20,
                       color: Optional[RGBcolor] = None,
                       texturefile: Optional[str] = None) -> int:
        """
        Add a spherical or ellipsoidal compound object to the context.

        Creates a sphere or ellipsoid as a compound object with a trackable object ID.
        Primitives within the object are registered as children of the object.

        Args:
            center: Center position of sphere/ellipsoid (default: origin)
            radius: Radius as float (sphere) or vec3 (ellipsoid) (default: 1.0)
            ndivs: Number of tessellation divisions (default: 20)
            color: Optional RGB color
            texturefile: Optional texture image file path

        Returns:
            Object ID of the created compound object

        Raises:
            ValueError: If parameters are invalid
            NotImplementedError: If object-returning functions unavailable

        Examples:
            >>> # Create a basic sphere at origin
            >>> obj_id = ctx.addSphereObject()

            >>> # Create a colored sphere
            >>> obj_id = ctx.addSphereObject(
            ...     center=vec3(0, 0, 5),
            ...     radius=2.0,
            ...     color=RGBcolor(1, 0, 0)
            ... )

            >>> # Create an ellipsoid (stretched sphere)
            >>> obj_id = ctx.addSphereObject(
            ...     center=vec3(10, 0, 0),
            ...     radius=vec3(2, 1, 1),  # Elongated in x-direction
            ...     ndivs=30
            ... )
        """
        self._check_context_available()

        # Parameter type validation
        if not isinstance(center, vec3):
            raise ValueError(f"Center must be a vec3, got {type(center).__name__}")
        if not isinstance(radius, (int, float, vec3)):
            raise ValueError(f"Radius must be a number or vec3, got {type(radius).__name__}")
        if color is not None and not isinstance(color, RGBcolor):
            raise ValueError(f"Color must be an RGBcolor or None, got {type(color).__name__}")

        # Validate parameters
        if ndivs < 3:
            raise ValueError("Number of divisions must be at least 3")

        # Check if radius is scalar (sphere) or vector (ellipsoid)
        is_ellipsoid = isinstance(radius, vec3)

        # Dispatch based on parameters
        if is_ellipsoid:
            # Ellipsoid variants
            if texturefile:
                return context_wrapper.addSphereObject_ellipsoid_texture(
                    self.context, ndivs, center.to_list(), radius.to_list(), texturefile
                )
            elif color:
                return context_wrapper.addSphereObject_ellipsoid_color(
                    self.context, ndivs, center.to_list(), radius.to_list(), color.to_list()
                )
            else:
                return context_wrapper.addSphereObject_ellipsoid(
                    self.context, ndivs, center.to_list(), radius.to_list()
                )
        else:
            # Sphere variants (radius is float)
            if texturefile:
                return context_wrapper.addSphereObject_texture(
                    self.context, ndivs, center.to_list(), radius, texturefile
                )
            elif color:
                return context_wrapper.addSphereObject_color(
                    self.context, ndivs, center.to_list(), radius, color.to_list()
                )
            else:
                return context_wrapper.addSphereObject_basic(
                    self.context, ndivs, center.to_list(), radius
                )

    def addTileObject(self, center: vec3 = vec3(0, 0, 0), size: vec2 = vec2(1, 1),
                     rotation: SphericalCoord = SphericalCoord(1, 0, 0),
                     subdiv: int2 = int2(1, 1),
                     color: Optional[RGBcolor] = None,
                     texturefile: Optional[str] = None,
                     texture_repeat: Optional[int2] = None) -> int:
        """
        Add a tiled patch (subdivided patch) as a compound object to the context.

        Creates a rectangular patch subdivided into a grid of smaller patches,
        registered as a compound object with a trackable object ID.

        Args:
            center: Center position of tile (default: origin)
            size: Size in x and y directions (default: 1x1)
            rotation: Spherical rotation (default: no rotation)
            subdiv: Number of subdivisions in x and y (default: 1x1)
            color: Optional RGB color
            texturefile: Optional texture image file path
            texture_repeat: Optional texture repetitions in x and y

        Returns:
            Object ID of the created compound object

        Raises:
            ValueError: If parameters are invalid
            NotImplementedError: If object-returning functions unavailable

        Examples:
            >>> # Create a basic 2x2 tile
            >>> obj_id = ctx.addTileObject(
            ...     center=vec3(0, 0, 0),
            ...     size=vec2(10, 10),
            ...     subdiv=int2(2, 2)
            ... )

            >>> # Create a colored tile with rotation
            >>> obj_id = ctx.addTileObject(
            ...     center=vec3(5, 0, 0),
            ...     size=vec2(10, 5),
            ...     rotation=SphericalCoord(1, 0, 45),
            ...     subdiv=int2(4, 2),
            ...     color=RGBcolor(0, 1, 0)
            ... )
        """
        self._check_context_available()

        # Parameter type validation
        if not isinstance(center, vec3):
            raise ValueError(f"Center must be a vec3, got {type(center).__name__}")
        if not isinstance(size, vec2):
            raise ValueError(f"Size must be a vec2, got {type(size).__name__}")
        if not isinstance(rotation, SphericalCoord):
            raise ValueError(f"Rotation must be a SphericalCoord, got {type(rotation).__name__}")
        if not isinstance(subdiv, int2):
            raise ValueError(f"Subdiv must be an int2, got {type(subdiv).__name__}")
        if color is not None and not isinstance(color, RGBcolor):
            raise ValueError(f"Color must be an RGBcolor or None, got {type(color).__name__}")
        if texture_repeat is not None and not isinstance(texture_repeat, int2):
            raise ValueError(f"texture_repeat must be an int2 or None, got {type(texture_repeat).__name__}")

        # Extract rotation as 3 values (radius, elevation, azimuth)
        rotation_list = [rotation.radius, rotation.elevation, rotation.azimuth]

        # Dispatch based on parameters
        if texture_repeat is not None:
            if texturefile is None:
                raise ValueError("texture_repeat requires texturefile")
            return context_wrapper.addTileObject_texture_repeat(
                self.context, center.to_list(), size.to_list(), rotation_list,
                subdiv.to_list(), texturefile, texture_repeat.to_list()
            )
        elif texturefile:
            return context_wrapper.addTileObject_texture(
                self.context, center.to_list(), size.to_list(), rotation_list,
                subdiv.to_list(), texturefile
            )
        elif color:
            return context_wrapper.addTileObject_color(
                self.context, center.to_list(), size.to_list(), rotation_list,
                subdiv.to_list(), color.to_list()
            )
        else:
            return context_wrapper.addTileObject_basic(
                self.context, center.to_list(), size.to_list(), rotation_list,
                subdiv.to_list()
            )

    def addBoxObject(self, center: vec3 = vec3(0, 0, 0), size: vec3 = vec3(1, 1, 1),
                    subdiv: int3 = int3(1, 1, 1), color: Optional[RGBcolor] = None,
                    texturefile: Optional[str] = None, reverse_normals: bool = False) -> int:
        """
        Add a rectangular box (prism) as a compound object to the context.

        Args:
            center: Center position (default: origin)
            size: Size in x, y, z directions (default: 1x1x1)
            subdiv: Subdivisions in x, y, z (default: 1x1x1)
            color: Optional RGB color
            texturefile: Optional texture file path
            reverse_normals: Reverse normal directions (default: False)

        Returns:
            Object ID of the created compound object
        """
        self._check_context_available()

        # Parameter type validation
        if not isinstance(center, vec3):
            raise ValueError(f"Center must be a vec3, got {type(center).__name__}")
        if not isinstance(size, vec3):
            raise ValueError(f"Size must be a vec3, got {type(size).__name__}")
        if not isinstance(subdiv, int3):
            raise ValueError(f"Subdiv must be an int3, got {type(subdiv).__name__}")
        if color is not None and not isinstance(color, RGBcolor):
            raise ValueError(f"Color must be an RGBcolor or None, got {type(color).__name__}")

        if reverse_normals:
            if texturefile:
                return context_wrapper.addBoxObject_texture_reverse(self.context, center.to_list(), size.to_list(), subdiv.to_list(), texturefile, reverse_normals)
            elif color:
                return context_wrapper.addBoxObject_color_reverse(self.context, center.to_list(), size.to_list(), subdiv.to_list(), color.to_list(), reverse_normals)
            else:
                raise ValueError("reverse_normals requires either color or texturefile")
        elif texturefile:
            return context_wrapper.addBoxObject_texture(self.context, center.to_list(), size.to_list(), subdiv.to_list(), texturefile)
        elif color:
            return context_wrapper.addBoxObject_color(self.context, center.to_list(), size.to_list(), subdiv.to_list(), color.to_list())
        else:
            return context_wrapper.addBoxObject_basic(self.context, center.to_list(), size.to_list(), subdiv.to_list())

    def addConeObject(self, node0: vec3, node1: vec3, radius0: float, radius1: float,
                     ndivs: int = 20, color: Optional[RGBcolor] = None,
                     texturefile: Optional[str] = None) -> int:
        """
        Add a cone/cylinder/frustum as a compound object to the context.

        Args:
            node0: Base position
            node1: Top position
            radius0: Radius at base
            radius1: Radius at top
            ndivs: Number of radial divisions (default: 20)
            color: Optional RGB color
            texturefile: Optional texture file path

        Returns:
            Object ID of the created compound object
        """
        self._check_context_available()

        # Parameter type validation
        if not isinstance(node0, vec3):
            raise ValueError(f"node0 must be a vec3, got {type(node0).__name__}")
        if not isinstance(node1, vec3):
            raise ValueError(f"node1 must be a vec3, got {type(node1).__name__}")
        if not isinstance(radius0, (int, float)):
            raise ValueError(f"radius0 must be a number, got {type(radius0).__name__}")
        if not isinstance(radius1, (int, float)):
            raise ValueError(f"radius1 must be a number, got {type(radius1).__name__}")
        if color is not None and not isinstance(color, RGBcolor):
            raise ValueError(f"Color must be an RGBcolor or None, got {type(color).__name__}")

        if texturefile:
            return context_wrapper.addConeObject_texture(self.context, ndivs, node0.to_list(), node1.to_list(), radius0, radius1, texturefile)
        elif color:
            return context_wrapper.addConeObject_color(self.context, ndivs, node0.to_list(), node1.to_list(), radius0, radius1, color.to_list())
        else:
            return context_wrapper.addConeObject_basic(self.context, ndivs, node0.to_list(), node1.to_list(), radius0, radius1)

    def addDiskObject(self, center: vec3 = vec3(0, 0, 0), size: vec2 = vec2(1, 1),
                     ndivs: Union[int, int2] = 20, rotation: Optional[SphericalCoord] = None,
                     color: Optional[Union[RGBcolor, RGBAcolor]] = None,
                     texturefile: Optional[str] = None) -> int:
        """
        Add a disk as a compound object to the context.

        Args:
            center: Center position (default: origin)
            size: Semi-major and semi-minor radii (default: 1x1)
            ndivs: int (uniform) or int2 (polar/radial subdivisions) (default: 20)
            rotation: Optional spherical rotation
            color: Optional RGB or RGBA color
            texturefile: Optional texture file path

        Returns:
            Object ID of the created compound object
        """
        self._check_context_available()

        rotation_list = [rotation.radius, rotation.elevation, rotation.azimuth] if rotation else [1, 0, 0]
        is_polar = isinstance(ndivs, int2)

        if is_polar:
            if texturefile:
                return context_wrapper.addDiskObject_polar_texture(self.context, ndivs.to_list(), center.to_list(), size.to_list(), rotation_list, texturefile)
            elif color:
                if isinstance(color, RGBAcolor):
                    return context_wrapper.addDiskObject_polar_rgba(self.context, ndivs.to_list(), center.to_list(), size.to_list(), rotation_list, color.to_list())
                else:
                    return context_wrapper.addDiskObject_polar_color(self.context, ndivs.to_list(), center.to_list(), size.to_list(), rotation_list, color.to_list())
            else:
                return context_wrapper.addDiskObject_polar_color(self.context, ndivs.to_list(), center.to_list(), size.to_list(), rotation_list, RGBcolor(0.5, 0.5, 0.5).to_list())
        else:
            if texturefile:
                return context_wrapper.addDiskObject_texture(self.context, ndivs, center.to_list(), size.to_list(), rotation_list, texturefile)
            elif color:
                if isinstance(color, RGBAcolor):
                    return context_wrapper.addDiskObject_rgba(self.context, ndivs, center.to_list(), size.to_list(), rotation_list, color.to_list())
                else:
                    return context_wrapper.addDiskObject_color(self.context, ndivs, center.to_list(), size.to_list(), rotation_list, color.to_list())
            elif rotation:
                return context_wrapper.addDiskObject_rotation(self.context, ndivs, center.to_list(), size.to_list(), rotation_list)
            else:
                return context_wrapper.addDiskObject_basic(self.context, ndivs, center.to_list(), size.to_list())

    def addTubeObject(self, ndivs: int, nodes: List[vec3], radii: List[float],
                     colors: Optional[List[RGBcolor]] = None,
                     texturefile: Optional[str] = None,
                     texture_uv: Optional[List[float]] = None) -> int:
        """
        Add a tube as a compound object to the context.

        Args:
            ndivs: Number of radial subdivisions
            nodes: List of vec3 positions defining tube segments
            radii: List of radii at each node
            colors: Optional list of RGB colors for each segment
            texturefile: Optional texture file path
            texture_uv: Optional UV coordinates for texture mapping

        Returns:
            Object ID of the created compound object
        """
        self._check_context_available()

        # Parameter type validation
        if not isinstance(nodes, (list, tuple)):
            raise ValueError(f"Nodes must be a list, got {type(nodes).__name__}")
        for i, node in enumerate(nodes):
            if not isinstance(node, vec3):
                raise ValueError(f"nodes[{i}] must be a vec3, got {type(node).__name__}")
        if not isinstance(radii, (list, tuple)):
            raise ValueError(f"Radii must be a list, got {type(radii).__name__}")
        if colors is not None:
            if not isinstance(colors, (list, tuple)):
                raise ValueError(f"Colors must be a list or None, got {type(colors).__name__}")
            for i, c in enumerate(colors):
                if not isinstance(c, RGBcolor):
                    raise ValueError(f"colors[{i}] must be an RGBcolor, got {type(c).__name__}")

        if len(nodes) < 2:
            raise ValueError("Tube requires at least 2 nodes")
        if len(radii) != len(nodes):
            raise ValueError("Number of radii must match number of nodes")

        nodes_flat = [coord for node in nodes for coord in node.to_list()]

        if texture_uv is not None:
            if texturefile is None:
                raise ValueError("texture_uv requires texturefile")
            return context_wrapper.addTubeObject_texture_uv(self.context, ndivs, nodes_flat, radii, texturefile, texture_uv)
        elif texturefile:
            return context_wrapper.addTubeObject_texture(self.context, ndivs, nodes_flat, radii, texturefile)
        elif colors:
            if len(colors) != len(nodes):
                raise ValueError("Number of colors must match number of nodes")
            colors_flat = [c for color in colors for c in color.to_list()]
            return context_wrapper.addTubeObject_color(self.context, ndivs, nodes_flat, radii, colors_flat)
        else:
            return context_wrapper.addTubeObject_basic(self.context, ndivs, nodes_flat, radii)

    def copyPrimitive(self, UUID: Union[int, List[int]]) -> Union[int, List[int]]:
        """
        Copy one or more primitives.

        Creates a duplicate of the specified primitive(s) with all associated data.
        The copy is placed at the same location as the original.

        Args:
            UUID: Single primitive UUID or list of UUIDs to copy

        Returns:
            Single UUID of copied primitive (if UUID is int) or
            List of UUIDs of copied primitives (if UUID is list)

        Example:
            >>> context = Context()
            >>> original_uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
            >>> # Copy single primitive
            >>> copied_uuid = context.copyPrimitive(original_uuid)
            >>> # Copy multiple primitives
            >>> copied_uuids = context.copyPrimitive([uuid1, uuid2, uuid3])
        """
        self._check_context_available()

        if isinstance(UUID, int):
            return context_wrapper.copyPrimitive(self.context, UUID)
        elif isinstance(UUID, list):
            return context_wrapper.copyPrimitives(self.context, UUID)
        else:
            raise ValueError(f"UUID must be int or List[int], got {type(UUID).__name__}")

    def copyPrimitiveData(self, sourceUUID: int, destinationUUID: int) -> None:
        """
        Copy all primitive data from source to destination primitive.

        Copies all associated data (primitive data fields) from the source
        primitive to the destination primitive. Both primitives must already exist.

        Args:
            sourceUUID: UUID of the source primitive
            destinationUUID: UUID of the destination primitive

        Example:
            >>> context = Context()
            >>> source_uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
            >>> dest_uuid = context.addPatch(center=vec3(1, 0, 0), size=vec2(1, 1))
            >>> context.setPrimitiveData(source_uuid, "temperature", 25.5)
            >>> context.copyPrimitiveData(source_uuid, dest_uuid)
            >>> # dest_uuid now has temperature data
        """
        self._check_context_available()

        if not isinstance(sourceUUID, int):
            raise ValueError(f"sourceUUID must be int, got {type(sourceUUID).__name__}")
        if not isinstance(destinationUUID, int):
            raise ValueError(f"destinationUUID must be int, got {type(destinationUUID).__name__}")

        context_wrapper.copyPrimitiveData(self.context, sourceUUID, destinationUUID)

    def copyObject(self, ObjID: Union[int, List[int]]) -> Union[int, List[int]]:
        """
        Copy one or more compound objects.

        Creates a duplicate of the specified compound object(s) with all
        associated primitives and data. The copy is placed at the same location
        as the original.

        Args:
            ObjID: Single object ID or list of object IDs to copy

        Returns:
            Single object ID of copied object (if ObjID is int) or
            List of object IDs of copied objects (if ObjID is list)

        Example:
            >>> context = Context()
            >>> original_obj = context.addTile(center=vec3(0, 0, 0), size=vec2(2, 2))
            >>> # Copy single object
            >>> copied_obj = context.copyObject(original_obj)
            >>> # Copy multiple objects
            >>> copied_objs = context.copyObject([obj1, obj2, obj3])
        """
        self._check_context_available()

        if isinstance(ObjID, int):
            return context_wrapper.copyObject(self.context, ObjID)
        elif isinstance(ObjID, list):
            return context_wrapper.copyObjects(self.context, ObjID)
        else:
            raise ValueError(f"ObjID must be int or List[int], got {type(ObjID).__name__}")

    def copyObjectData(self, source_objID: int, destination_objID: int) -> None:
        """
        Copy all object data from source to destination compound object.

        Copies all associated data (object data fields) from the source
        compound object to the destination object. Both objects must already exist.

        Args:
            source_objID: Object ID of the source compound object
            destination_objID: Object ID of the destination compound object

        Example:
            >>> context = Context()
            >>> source_obj = context.addTile(center=vec3(0, 0, 0), size=vec2(2, 2))
            >>> dest_obj = context.addTile(center=vec3(2, 0, 0), size=vec2(2, 2))
            >>> context.setObjectData(source_obj, "material", "wood")
            >>> context.copyObjectData(source_obj, dest_obj)
            >>> # dest_obj now has material data
        """
        self._check_context_available()

        if not isinstance(source_objID, int):
            raise ValueError(f"source_objID must be int, got {type(source_objID).__name__}")
        if not isinstance(destination_objID, int):
            raise ValueError(f"destination_objID must be int, got {type(destination_objID).__name__}")

        context_wrapper.copyObjectData(self.context, source_objID, destination_objID)

    def translatePrimitive(self, UUID: Union[int, List[int]], shift: vec3) -> None:
        """
        Translate one or more primitives by a shift vector.

        Moves the specified primitive(s) by the given shift vector without
        changing their orientation or size.

        Args:
            UUID: Single primitive UUID or list of UUIDs to translate
            shift: 3D vector representing the translation [x, y, z]

        Example:
            >>> context = Context()
            >>> patch_uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
            >>> # Translate single primitive
            >>> context.translatePrimitive(patch_uuid, vec3(1, 0, 0))  # Move 1 unit in x
            >>> # Translate multiple primitives
            >>> context.translatePrimitive([uuid1, uuid2, uuid3], vec3(0, 0, 1))  # Move 1 unit in z
        """
        self._check_context_available()

        # Type validation
        if not isinstance(shift, vec3):
            raise ValueError(f"shift must be a vec3, got {type(shift).__name__}")

        if isinstance(UUID, int):
            context_wrapper.translatePrimitive(self.context, UUID, shift.to_list())
        elif isinstance(UUID, list):
            context_wrapper.translatePrimitives(self.context, UUID, shift.to_list())
        else:
            raise ValueError(f"UUID must be int or List[int], got {type(UUID).__name__}")

    def translateObject(self, ObjID: Union[int, List[int]], shift: vec3) -> None:
        """
        Translate one or more compound objects by a shift vector.

        Moves the specified compound object(s) and all their constituent
        primitives by the given shift vector without changing orientation or size.

        Args:
            ObjID: Single object ID or list of object IDs to translate
            shift: 3D vector representing the translation [x, y, z]

        Example:
            >>> context = Context()
            >>> tile_uuids = context.addTile(center=vec3(0, 0, 0), size=vec2(2, 2))
            >>> obj_id = context.getPrimitiveParentObjectID(tile_uuids[0])  # Get object ID
            >>> # Translate single object
            >>> context.translateObject(obj_id, vec3(5, 0, 0))  # Move 5 units in x
            >>> # Translate multiple objects
            >>> context.translateObject([obj1, obj2, obj3], vec3(0, 2, 0))  # Move 2 units in y
        """
        self._check_context_available()

        # Type validation
        if not isinstance(shift, vec3):
            raise ValueError(f"shift must be a vec3, got {type(shift).__name__}")

        if isinstance(ObjID, int):
            context_wrapper.translateObject(self.context, ObjID, shift.to_list())
        elif isinstance(ObjID, list):
            context_wrapper.translateObjects(self.context, ObjID, shift.to_list())
        else:
            raise ValueError(f"ObjID must be int or List[int], got {type(ObjID).__name__}")

    def rotatePrimitive(self, UUID: Union[int, List[int]], angle: float,
                       axis: Union[str, vec3], origin: Optional[vec3] = None) -> None:
        """
        Rotate one or more primitives.

        Args:
            UUID: Single UUID or list of UUIDs to rotate
            angle: Rotation angle in radians
            axis: Rotation axis - either 'x', 'y', 'z' or a vec3 direction vector
            origin: Optional rotation origin point. If None, rotates about primitive center.
                   If provided with string axis, raises ValueError.

        Raises:
            ValueError: If axis is invalid or if origin is provided with string axis
        """
        self._check_context_available()

        # Validate axis parameter
        if isinstance(axis, str):
            if axis not in ('x', 'y', 'z'):
                raise ValueError("axis must be 'x', 'y', or 'z'")
            if origin is not None:
                raise ValueError("origin parameter cannot be used with string axis")

            # Use string axis variant
            if isinstance(UUID, int):
                context_wrapper.rotatePrimitive_axisString(self.context, UUID, angle, axis)
            elif isinstance(UUID, list):
                context_wrapper.rotatePrimitives_axisString(self.context, UUID, angle, axis)
            else:
                raise ValueError(f"UUID must be int or List[int], got {type(UUID).__name__}")

        elif isinstance(axis, vec3):
            axis_list = axis.to_list()

            # Check for zero-length axis
            if all(abs(v) < 1e-10 for v in axis_list):
                raise ValueError("axis vector cannot be zero")

            if origin is None:
                # Rotate about primitive center (axis vector variant)
                if isinstance(UUID, int):
                    context_wrapper.rotatePrimitive_axisVector(self.context, UUID, angle, axis_list)
                elif isinstance(UUID, list):
                    context_wrapper.rotatePrimitives_axisVector(self.context, UUID, angle, axis_list)
                else:
                    raise ValueError(f"UUID must be int or List[int], got {type(UUID).__name__}")
            else:
                # Rotate about specified origin point
                if not isinstance(origin, vec3):
                    raise ValueError(f"origin must be a vec3, got {type(origin).__name__}")

                origin_list = origin.to_list()
                if isinstance(UUID, int):
                    context_wrapper.rotatePrimitive_originAxisVector(self.context, UUID, angle, origin_list, axis_list)
                elif isinstance(UUID, list):
                    context_wrapper.rotatePrimitives_originAxisVector(self.context, UUID, angle, origin_list, axis_list)
                else:
                    raise ValueError(f"UUID must be int or List[int], got {type(UUID).__name__}")
        else:
            raise ValueError(f"axis must be str or vec3, got {type(axis).__name__}")

    def rotateObject(self, ObjID: Union[int, List[int]], angle: float,
                    axis: Union[str, vec3], origin: Optional[vec3] = None,
                    about_origin: bool = False) -> None:
        """
        Rotate one or more objects.

        Args:
            ObjID: Single object ID or list of object IDs to rotate
            angle: Rotation angle in radians
            axis: Rotation axis - either 'x', 'y', 'z' or a vec3 direction vector
            origin: Optional rotation origin point. If None, rotates about object center.
                   If provided with string axis, raises ValueError.
            about_origin: If True, rotate about global origin (0,0,0). Cannot be used with origin parameter.

        Raises:
            ValueError: If axis is invalid or if origin and about_origin are both specified
        """
        self._check_context_available()

        # Validate parameter combinations
        if origin is not None and about_origin:
            raise ValueError("Cannot specify both origin and about_origin")

        # Validate axis parameter
        if isinstance(axis, str):
            if axis not in ('x', 'y', 'z'):
                raise ValueError("axis must be 'x', 'y', or 'z'")
            if origin is not None:
                raise ValueError("origin parameter cannot be used with string axis")
            if about_origin:
                raise ValueError("about_origin parameter cannot be used with string axis")

            # Use string axis variant
            if isinstance(ObjID, int):
                context_wrapper.rotateObject_axisString(self.context, ObjID, angle, axis)
            elif isinstance(ObjID, list):
                context_wrapper.rotateObjects_axisString(self.context, ObjID, angle, axis)
            else:
                raise ValueError(f"ObjID must be int or List[int], got {type(ObjID).__name__}")

        elif isinstance(axis, vec3):
            axis_list = axis.to_list()

            # Check for zero-length axis
            if all(abs(v) < 1e-10 for v in axis_list):
                raise ValueError("axis vector cannot be zero")

            if about_origin:
                # Rotate about global origin
                if isinstance(ObjID, int):
                    context_wrapper.rotateObjectAboutOrigin_axisVector(self.context, ObjID, angle, axis_list)
                elif isinstance(ObjID, list):
                    context_wrapper.rotateObjectsAboutOrigin_axisVector(self.context, ObjID, angle, axis_list)
                else:
                    raise ValueError(f"ObjID must be int or List[int], got {type(ObjID).__name__}")
            elif origin is None:
                # Rotate about object center
                if isinstance(ObjID, int):
                    context_wrapper.rotateObject_axisVector(self.context, ObjID, angle, axis_list)
                elif isinstance(ObjID, list):
                    context_wrapper.rotateObjects_axisVector(self.context, ObjID, angle, axis_list)
                else:
                    raise ValueError(f"ObjID must be int or List[int], got {type(ObjID).__name__}")
            else:
                # Rotate about specified origin point
                if not isinstance(origin, vec3):
                    raise ValueError(f"origin must be a vec3, got {type(origin).__name__}")

                origin_list = origin.to_list()
                if isinstance(ObjID, int):
                    context_wrapper.rotateObject_originAxisVector(self.context, ObjID, angle, origin_list, axis_list)
                elif isinstance(ObjID, list):
                    context_wrapper.rotateObjects_originAxisVector(self.context, ObjID, angle, origin_list, axis_list)
                else:
                    raise ValueError(f"ObjID must be int or List[int], got {type(ObjID).__name__}")
        else:
            raise ValueError(f"axis must be str or vec3, got {type(axis).__name__}")

    def scalePrimitive(self, UUID: Union[int, List[int]], scale: vec3, point: Optional[vec3] = None) -> None:
        """
        Scale one or more primitives.

        Args:
            UUID: Single UUID or list of UUIDs to scale
            scale: Scale factors as vec3(x, y, z)
            point: Optional point to scale about. If None, scales about primitive center.

        Raises:
            ValueError: If scale or point parameters are invalid
        """
        self._check_context_available()

        if not isinstance(scale, vec3):
            raise ValueError(f"scale must be a vec3, got {type(scale).__name__}")

        scale_list = scale.to_list()

        if point is None:
            # Scale about primitive center
            if isinstance(UUID, int):
                context_wrapper.scalePrimitive(self.context, UUID, scale_list)
            elif isinstance(UUID, list):
                context_wrapper.scalePrimitives(self.context, UUID, scale_list)
            else:
                raise ValueError(f"UUID must be int or List[int], got {type(UUID).__name__}")
        else:
            # Scale about specified point
            if not isinstance(point, vec3):
                raise ValueError(f"point must be a vec3, got {type(point).__name__}")

            point_list = point.to_list()
            if isinstance(UUID, int):
                context_wrapper.scalePrimitiveAboutPoint(self.context, UUID, scale_list, point_list)
            elif isinstance(UUID, list):
                context_wrapper.scalePrimitivesAboutPoint(self.context, UUID, scale_list, point_list)
            else:
                raise ValueError(f"UUID must be int or List[int], got {type(UUID).__name__}")

    def scaleObject(self, ObjID: Union[int, List[int]], scale: vec3,
                   point: Optional[vec3] = None, about_center: bool = False,
                   about_origin: bool = False) -> None:
        """
        Scale one or more objects.

        Args:
            ObjID: Single object ID or list of object IDs to scale
            scale: Scale factors as vec3(x, y, z)
            point: Optional point to scale about
            about_center: If True, scale about object center (default behavior)
            about_origin: If True, scale about global origin (0,0,0)

        Raises:
            ValueError: If parameters are invalid or conflicting options specified
        """
        self._check_context_available()

        # Validate parameter combinations
        options_count = sum([point is not None, about_center, about_origin])
        if options_count > 1:
            raise ValueError("Cannot specify multiple scaling options (point, about_center, about_origin)")

        if not isinstance(scale, vec3):
            raise ValueError(f"scale must be a vec3, got {type(scale).__name__}")

        scale_list = scale.to_list()

        if about_origin:
            # Scale about global origin
            if isinstance(ObjID, int):
                context_wrapper.scaleObjectAboutOrigin(self.context, ObjID, scale_list)
            elif isinstance(ObjID, list):
                context_wrapper.scaleObjectsAboutOrigin(self.context, ObjID, scale_list)
            else:
                raise ValueError(f"ObjID must be int or List[int], got {type(ObjID).__name__}")
        elif about_center:
            # Scale about object center
            if isinstance(ObjID, int):
                context_wrapper.scaleObjectAboutCenter(self.context, ObjID, scale_list)
            elif isinstance(ObjID, list):
                context_wrapper.scaleObjectsAboutCenter(self.context, ObjID, scale_list)
            else:
                raise ValueError(f"ObjID must be int or List[int], got {type(ObjID).__name__}")
        elif point is not None:
            # Scale about specified point
            if not isinstance(point, vec3):
                raise ValueError(f"point must be a vec3, got {type(point).__name__}")

            point_list = point.to_list()
            if isinstance(ObjID, int):
                context_wrapper.scaleObjectAboutPoint(self.context, ObjID, scale_list, point_list)
            elif isinstance(ObjID, list):
                context_wrapper.scaleObjectsAboutPoint(self.context, ObjID, scale_list, point_list)
            else:
                raise ValueError(f"ObjID must be int or List[int], got {type(ObjID).__name__}")
        else:
            # Default: scale object (standard behavior)
            if isinstance(ObjID, int):
                context_wrapper.scaleObject(self.context, ObjID, scale_list)
            elif isinstance(ObjID, list):
                context_wrapper.scaleObjects(self.context, ObjID, scale_list)
            else:
                raise ValueError(f"ObjID must be int or List[int], got {type(ObjID).__name__}")

    def scaleConeObjectLength(self, ObjID: int, scale_factor: float) -> None:
        """
        Scale the length of a Cone object by scaling the distance between its two nodes.

        Args:
            ObjID: Object ID of the Cone to scale
            scale_factor: Factor by which to scale the cone length (e.g., 2.0 doubles length)

        Raises:
            ValueError: If ObjID is not an integer or scale_factor is invalid
            HeliosRuntimeError: If operation fails (e.g., ObjID is not a Cone object)

        Note:
            Added in helios-core v1.3.59 as a replacement for the removed getConeObjectPointer()
            method, enforcing better encapsulation.

        Example:
            >>> cone_id = context.addConeObject(10, [0,0,0], [0,0,1], 0.1, 0.05)
            >>> context.scaleConeObjectLength(cone_id, 1.5)  # Make cone 50% longer
        """
        if not isinstance(ObjID, int):
            raise ValueError(f"ObjID must be an integer, got {type(ObjID).__name__}")
        if not isinstance(scale_factor, (int, float)):
            raise ValueError(f"scale_factor must be numeric, got {type(scale_factor).__name__}")
        if scale_factor <= 0:
            raise ValueError(f"scale_factor must be positive, got {scale_factor}")

        context_wrapper.scaleConeObjectLength(self.context, ObjID, float(scale_factor))

    def scaleConeObjectGirth(self, ObjID: int, scale_factor: float) -> None:
        """
        Scale the girth of a Cone object by scaling the radii at both nodes.

        Args:
            ObjID: Object ID of the Cone to scale
            scale_factor: Factor by which to scale the cone girth (e.g., 2.0 doubles girth)

        Raises:
            ValueError: If ObjID is not an integer or scale_factor is invalid
            HeliosRuntimeError: If operation fails (e.g., ObjID is not a Cone object)

        Note:
            Added in helios-core v1.3.59 as a replacement for the removed getConeObjectPointer()
            method, enforcing better encapsulation.

        Example:
            >>> cone_id = context.addConeObject(10, [0,0,0], [0,0,1], 0.1, 0.05)
            >>> context.scaleConeObjectGirth(cone_id, 2.0)  # Double the cone girth
        """
        if not isinstance(ObjID, int):
            raise ValueError(f"ObjID must be an integer, got {type(ObjID).__name__}")
        if not isinstance(scale_factor, (int, float)):
            raise ValueError(f"scale_factor must be numeric, got {type(scale_factor).__name__}")
        if scale_factor <= 0:
            raise ValueError(f"scale_factor must be positive, got {scale_factor}")

        context_wrapper.scaleConeObjectGirth(self.context, ObjID, float(scale_factor))

    def loadPLY(self, filename: str, origin: Optional[vec3] = None, height: Optional[float] = None, 
                rotation: Optional[SphericalCoord] = None, color: Optional[RGBcolor] = None, 
                upaxis: str = "YUP", silent: bool = False) -> List[int]:
        """
        Load geometry from a PLY (Stanford Polygon) file.
        
        Args:
            filename: Path to the PLY file to load
            origin: Origin point for positioning the geometry (optional)
            height: Height scaling factor (optional)
            rotation: Rotation to apply to the geometry (optional)
            color: Default color for geometry without color data (optional)
            upaxis: Up axis orientation ("YUP" or "ZUP")
            silent: If True, suppress loading output messages
            
        Returns:
            List of UUIDs for the loaded primitives
        """
        self._check_context_available()

        # Parameter type validation
        if origin is not None and not isinstance(origin, vec3):
            raise ValueError(f"Origin must be a vec3 or None, got {type(origin).__name__}")
        if rotation is not None and not isinstance(rotation, SphericalCoord):
            raise ValueError(f"Rotation must be a SphericalCoord or None, got {type(rotation).__name__}")
        if color is not None and not isinstance(color, RGBcolor):
            raise ValueError(f"Color must be an RGBcolor or None, got {type(color).__name__}")

        # Validate file path for security
        validated_filename = self._validate_file_path(filename, ['.ply'])

        if origin is None and height is None and rotation is None and color is None:
            # Simple load with no transformations
            return context_wrapper.loadPLY(self.context, validated_filename, silent)
        
        elif origin is not None and height is not None and rotation is None and color is None:
            # Load with origin and height
            return context_wrapper.loadPLYWithOriginHeight(self.context, validated_filename, origin.to_list(), height, upaxis, silent)
        
        elif origin is not None and height is not None and rotation is not None and color is None:
            # Load with origin, height, and rotation
            rotation_list = [rotation.radius, rotation.elevation, rotation.azimuth]
            return context_wrapper.loadPLYWithOriginHeightRotation(self.context, validated_filename, origin.to_list(), height, rotation_list, upaxis, silent)
        
        elif origin is not None and height is not None and rotation is None and color is not None:
            # Load with origin, height, and color
            return context_wrapper.loadPLYWithOriginHeightColor(self.context, validated_filename, origin.to_list(), height, color.to_list(), upaxis, silent)
        
        elif origin is not None and height is not None and rotation is not None and color is not None:
            # Load with all parameters
            rotation_list = [rotation.radius, rotation.elevation, rotation.azimuth]
            return context_wrapper.loadPLYWithOriginHeightRotationColor(self.context, validated_filename, origin.to_list(), height, rotation_list, color.to_list(), upaxis, silent)
        
        else:
            raise ValueError("Invalid parameter combination. When using transformations, both origin and height are required.")

    def loadOBJ(self, filename: str, origin: Optional[vec3] = None, height: Optional[float] = None,
                scale: Optional[vec3] = None, rotation: Optional[SphericalCoord] = None, 
                color: Optional[RGBcolor] = None, upaxis: str = "YUP", silent: bool = False) -> List[int]:
        """
        Load geometry from an OBJ (Wavefront) file.
        
        Args:
            filename: Path to the OBJ file to load
            origin: Origin point for positioning the geometry (optional)
            height: Height scaling factor (optional, alternative to scale)
            scale: Scale factor for all dimensions (optional, alternative to height)
            rotation: Rotation to apply to the geometry (optional)
            color: Default color for geometry without color data (optional)
            upaxis: Up axis orientation ("YUP" or "ZUP")
            silent: If True, suppress loading output messages
            
        Returns:
            List of UUIDs for the loaded primitives
        """
        self._check_context_available()

        # Parameter type validation
        if origin is not None and not isinstance(origin, vec3):
            raise ValueError(f"Origin must be a vec3 or None, got {type(origin).__name__}")
        if scale is not None and not isinstance(scale, vec3):
            raise ValueError(f"Scale must be a vec3 or None, got {type(scale).__name__}")
        if rotation is not None and not isinstance(rotation, SphericalCoord):
            raise ValueError(f"Rotation must be a SphericalCoord or None, got {type(rotation).__name__}")
        if color is not None and not isinstance(color, RGBcolor):
            raise ValueError(f"Color must be an RGBcolor or None, got {type(color).__name__}")

        # Validate file path for security
        validated_filename = self._validate_file_path(filename, ['.obj'])

        if origin is None and height is None and scale is None and rotation is None and color is None:
            # Simple load with no transformations
            return context_wrapper.loadOBJ(self.context, validated_filename, silent)
        
        elif origin is not None and height is not None and scale is None and rotation is not None and color is not None:
            # Load with origin, height, rotation, and color (no upaxis)
            return context_wrapper.loadOBJWithOriginHeightRotationColor(self.context, validated_filename, origin.to_list(), height, rotation.to_list(), color.to_list(), silent)
        
        elif origin is not None and height is not None and scale is None and rotation is not None and color is not None and upaxis != "YUP":
            # Load with origin, height, rotation, color, and upaxis
            return context_wrapper.loadOBJWithOriginHeightRotationColorUpaxis(self.context, validated_filename, origin.to_list(), height, rotation.to_list(), color.to_list(), upaxis, silent)
        
        elif origin is not None and scale is not None and rotation is not None and color is not None:
            # Load with origin, scale, rotation, color, and upaxis
            return context_wrapper.loadOBJWithOriginScaleRotationColorUpaxis(self.context, validated_filename, origin.to_list(), scale.to_list(), rotation.to_list(), color.to_list(), upaxis, silent)
        
        else:
            raise ValueError("Invalid parameter combination. For OBJ loading, you must provide either: " +
                           "1) No parameters (simple load), " +
                           "2) origin + height + rotation + color, " +
                           "3) origin + height + rotation + color + upaxis, or " +
                           "4) origin + scale + rotation + color + upaxis")

    def loadXML(self, filename: str, quiet: bool = False) -> List[int]:
        """
        Load geometry from a Helios XML file.
        
        Args:
            filename: Path to the XML file to load
            quiet: If True, suppress loading output messages
            
        Returns:
            List of UUIDs for the loaded primitives
        """
        self._check_context_available()
        # Validate file path for security
        validated_filename = self._validate_file_path(filename, ['.xml'])
        
        return context_wrapper.loadXML(self.context, validated_filename, quiet)

    def writePLY(self, filename: str, UUIDs: Optional[List[int]] = None) -> None:
        """
        Write geometry to a PLY (Stanford Polygon) file.

        Args:
            filename: Path to the output PLY file
            UUIDs: Optional list of primitive UUIDs to export. If None, exports all primitives

        Raises:
            ValueError: If filename is invalid or UUIDs are invalid
            PermissionError: If output directory is not writable
            FileNotFoundError: If UUIDs do not exist in context
            RuntimeError: If Context is in mock mode

        Example:
            >>> context.writePLY("output.ply")  # Export all primitives
            >>> context.writePLY("subset.ply", [uuid1, uuid2])  # Export specific primitives
        """
        self._check_context_available()

        # Validate output file path for security
        validated_filename = self._validate_output_file_path(filename, ['.ply'])

        if UUIDs is None:
            # Export all primitives
            context_wrapper.writePLY(self.context, validated_filename)
        else:
            # Validate UUIDs exist in context
            if not UUIDs:
                raise ValueError("UUIDs list cannot be empty. Use UUIDs=None to export all primitives")

            # Validate each UUID exists
            for uuid in UUIDs:
                self._validate_uuid(uuid)

            # Export specified UUIDs
            context_wrapper.writePLYWithUUIDs(self.context, validated_filename, UUIDs)

    def writeOBJ(self, filename: str, UUIDs: Optional[List[int]] = None,
                 primitive_data_fields: Optional[List[str]] = None,
                 write_normals: bool = False, silent: bool = False) -> None:
        """
        Write geometry to an OBJ (Wavefront) file.

        Args:
            filename: Path to the output OBJ file
            UUIDs: Optional list of primitive UUIDs to export. If None, exports all primitives
            primitive_data_fields: Optional list of primitive data field names to export
            write_normals: Whether to include vertex normals in the output
            silent: Whether to suppress output messages during export

        Raises:
            ValueError: If filename is invalid, UUIDs are invalid, or data fields don't exist
            PermissionError: If output directory is not writable
            FileNotFoundError: If UUIDs do not exist in context
            RuntimeError: If Context is in mock mode

        Example:
            >>> context.writeOBJ("output.obj")  # Export all primitives
            >>> context.writeOBJ("subset.obj", [uuid1, uuid2])  # Export specific primitives
            >>> context.writeOBJ("with_data.obj", [uuid1], ["temperature", "area"])  # Export with data
        """
        self._check_context_available()

        # Validate output file path for security
        validated_filename = self._validate_output_file_path(filename, ['.obj'])

        if UUIDs is None:
            # Export all primitives
            context_wrapper.writeOBJ(self.context, validated_filename, write_normals, silent)
        elif primitive_data_fields is None:
            # Export specified UUIDs without data fields
            if not UUIDs:
                raise ValueError("UUIDs list cannot be empty. Use UUIDs=None to export all primitives")

            # Validate each UUID exists
            for uuid in UUIDs:
                self._validate_uuid(uuid)

            context_wrapper.writeOBJWithUUIDs(self.context, validated_filename, UUIDs, write_normals, silent)
        else:
            # Export specified UUIDs with primitive data fields
            if not UUIDs:
                raise ValueError("UUIDs list cannot be empty when exporting primitive data")
            if not primitive_data_fields:
                raise ValueError("primitive_data_fields list cannot be empty")

            # Validate each UUID exists
            for uuid in UUIDs:
                self._validate_uuid(uuid)

            # Note: Primitive data field validation is handled by the native library
            # which will raise appropriate errors if fields don't exist for the specified primitives

            context_wrapper.writeOBJWithPrimitiveData(self.context, validated_filename, UUIDs, primitive_data_fields, write_normals, silent)

    def writePrimitiveData(self, filename: str, column_labels: List[str],
                           UUIDs: Optional[List[int]] = None,
                           print_header: bool = False) -> None:
        """
        Write primitive data to an ASCII text file.

        Outputs a space-separated text file where each row corresponds to a primitive
        and each column corresponds to a primitive data label.

        Args:
            filename: Path to the output file
            column_labels: List of primitive data labels to include as columns.
                          Use "UUID" to include primitive UUIDs as a column.
                          The order determines the column order in the output file.
            UUIDs: Optional list of primitive UUIDs to include. If None, includes all primitives.
            print_header: If True, writes column labels as the first line of the file

        Raises:
            ValueError: If filename is invalid, column_labels is empty, or UUIDs list is empty when provided
            HeliosFileIOError: If file cannot be written
            HeliosRuntimeError: If a column label doesn't exist for any primitive

        Example:
            >>> # Write temperature and area for all primitives
            >>> context.writePrimitiveData("output.txt", ["UUID", "temperature", "area"])

            >>> # Write with header row
            >>> context.writePrimitiveData("output.txt", ["UUID", "radiation_flux"], print_header=True)

            >>> # Write only for selected primitives
            >>> context.writePrimitiveData("subset.txt", ["temperature"], UUIDs=[uuid1, uuid2])
        """
        self._check_context_available()

        # Validate column_labels
        if not column_labels:
            raise ValueError("column_labels list cannot be empty")

        # Validate output file path (allow any extension for text files)
        validated_filename = self._validate_output_file_path(filename)

        if UUIDs is None:
            # Export all primitives
            context_wrapper.writePrimitiveData(self.context, validated_filename, column_labels, print_header)
        else:
            # Export specified UUIDs
            if not UUIDs:
                raise ValueError("UUIDs list cannot be empty when provided. Use UUIDs=None to include all primitives")

            # Validate each UUID exists
            for uuid in UUIDs:
                self._validate_uuid(uuid)

            context_wrapper.writePrimitiveDataWithUUIDs(self.context, validated_filename, column_labels, UUIDs, print_header)

    def addTrianglesFromArrays(self, vertices: np.ndarray, faces: np.ndarray, 
                              colors: Optional[np.ndarray] = None) -> List[int]:
        """
        Add triangles from NumPy arrays (compatible with trimesh, Open3D format).
        
        Args:
            vertices: NumPy array of shape (N, 3) containing vertex coordinates as float32/float64
            faces: NumPy array of shape (M, 3) containing triangle vertex indices as int32/int64
            colors: Optional NumPy array of shape (N, 3) or (M, 3) containing RGB colors as float32/float64
                   If shape (N, 3): per-vertex colors
                   If shape (M, 3): per-triangle colors
            
        Returns:
            List of UUIDs for the added triangles
            
        Raises:
            ValueError: If array dimensions are invalid
        """
        # Validate input arrays
        if vertices.ndim != 2 or vertices.shape[1] != 3:
            raise ValueError(f"Vertices array must have shape (N, 3), got {vertices.shape}")
        if faces.ndim != 2 or faces.shape[1] != 3:
            raise ValueError(f"Faces array must have shape (M, 3), got {faces.shape}")
        
        # Check vertex indices are valid
        max_vertex_index = np.max(faces)
        if max_vertex_index >= vertices.shape[0]:
            raise ValueError(f"Face indices reference vertex {max_vertex_index}, but only {vertices.shape[0]} vertices provided")
        
        # Validate colors array if provided
        per_vertex_colors = False
        per_triangle_colors = False
        if colors is not None:
            if colors.ndim != 2 or colors.shape[1] != 3:
                raise ValueError(f"Colors array must have shape (N, 3) or (M, 3), got {colors.shape}")
            if colors.shape[0] == vertices.shape[0]:
                per_vertex_colors = True
            elif colors.shape[0] == faces.shape[0]:
                per_triangle_colors = True
            else:
                raise ValueError(f"Colors array shape {colors.shape} doesn't match vertices ({vertices.shape[0]},) or faces ({faces.shape[0]},)")
        
        # Convert arrays to appropriate data types
        vertices_float = vertices.astype(np.float32)
        faces_int = faces.astype(np.int32)
        if colors is not None:
            colors_float = colors.astype(np.float32)
        
        # Add triangles
        triangle_uuids = []
        for i in range(faces.shape[0]):
            # Get vertex indices for this triangle
            v0_idx, v1_idx, v2_idx = faces_int[i]
            
            # Get vertex coordinates
            vertex0 = vertices_float[v0_idx].tolist()
            vertex1 = vertices_float[v1_idx].tolist()
            vertex2 = vertices_float[v2_idx].tolist()
            
            # Add triangle with or without color
            if colors is None:
                # No color specified
                uuid = context_wrapper.addTriangle(self.context, vertex0, vertex1, vertex2)
            elif per_triangle_colors:
                # Use per-triangle color
                color = colors_float[i].tolist()
                uuid = context_wrapper.addTriangleWithColor(self.context, vertex0, vertex1, vertex2, color)
            elif per_vertex_colors:
                # Average the per-vertex colors for the triangle
                color = np.mean([colors_float[v0_idx], colors_float[v1_idx], colors_float[v2_idx]], axis=0).tolist()
                uuid = context_wrapper.addTriangleWithColor(self.context, vertex0, vertex1, vertex2, color)
            
            triangle_uuids.append(uuid)
        
        return triangle_uuids

    def addTrianglesFromArraysTextured(self, vertices: np.ndarray, faces: np.ndarray,
                                      uv_coords: np.ndarray, texture_files: Union[str, List[str]], 
                                      material_ids: Optional[np.ndarray] = None) -> List[int]:
        """
        Add textured triangles from NumPy arrays with support for multiple textures.
        
        This method supports both single-texture and multi-texture workflows:
        - Single texture: Pass a single texture file string, all faces use the same texture
        - Multiple textures: Pass a list of texture files and material_ids array specifying which texture each face uses
        
        Args:
            vertices: NumPy array of shape (N, 3) containing vertex coordinates as float32/float64
            faces: NumPy array of shape (M, 3) containing triangle vertex indices as int32/int64
            uv_coords: NumPy array of shape (N, 2) containing UV texture coordinates as float32/float64
            texture_files: Single texture file path (str) or list of texture file paths (List[str])
            material_ids: Optional NumPy array of shape (M,) containing material ID for each face.
                         If None and texture_files is a list, all faces use texture 0.
                         If None and texture_files is a string, this parameter is ignored.
            
        Returns:
            List of UUIDs for the added textured triangles
            
        Raises:
            ValueError: If array dimensions are invalid or material IDs are out of range
            
        Example:
            # Single texture usage (backward compatible)
            >>> uuids = context.addTrianglesFromArraysTextured(vertices, faces, uvs, "texture.png")
            
            # Multi-texture usage (Open3D style)
            >>> texture_files = ["wood.png", "metal.png", "glass.png"]
            >>> material_ids = np.array([0, 0, 1, 1, 2, 2])  # 6 faces using different textures
            >>> uuids = context.addTrianglesFromArraysTextured(vertices, faces, uvs, texture_files, material_ids)
        """
        self._check_context_available()
        
        # Validate input arrays
        if vertices.ndim != 2 or vertices.shape[1] != 3:
            raise ValueError(f"Vertices array must have shape (N, 3), got {vertices.shape}")
        if faces.ndim != 2 or faces.shape[1] != 3:
            raise ValueError(f"Faces array must have shape (M, 3), got {faces.shape}")
        if uv_coords.ndim != 2 or uv_coords.shape[1] != 2:
            raise ValueError(f"UV coordinates array must have shape (N, 2), got {uv_coords.shape}")
        
        # Check array consistency
        if uv_coords.shape[0] != vertices.shape[0]:
            raise ValueError(f"UV coordinates count ({uv_coords.shape[0]}) must match vertices count ({vertices.shape[0]})")
        
        # Check vertex indices are valid
        max_vertex_index = np.max(faces)
        if max_vertex_index >= vertices.shape[0]:
            raise ValueError(f"Face indices reference vertex {max_vertex_index}, but only {vertices.shape[0]} vertices provided")
        
        # Handle texture files parameter (single string or list)
        if isinstance(texture_files, str):
            # Single texture case - use original implementation for efficiency
            texture_file_list = [texture_files]
            if material_ids is None:
                material_ids = np.zeros(faces.shape[0], dtype=np.uint32)
            else:
                # Validate that all material IDs are 0 for single texture
                if not np.all(material_ids == 0):
                    raise ValueError("When using single texture file, all material IDs must be 0")
        else:
            # Multiple textures case
            texture_file_list = list(texture_files)
            if len(texture_file_list) == 0:
                raise ValueError("Texture files list cannot be empty")
            
            if material_ids is None:
                # Default: all faces use first texture
                material_ids = np.zeros(faces.shape[0], dtype=np.uint32)
            else:
                # Validate material IDs array
                if material_ids.ndim != 1 or material_ids.shape[0] != faces.shape[0]:
                    raise ValueError(f"Material IDs must have shape ({faces.shape[0]},), got {material_ids.shape}")
                
                # Check material ID range
                max_material_id = np.max(material_ids)
                if max_material_id >= len(texture_file_list):
                    raise ValueError(f"Material ID {max_material_id} exceeds texture count {len(texture_file_list)}")
        
        # Validate all texture files exist
        for i, texture_file in enumerate(texture_file_list):
            try:
                self._validate_file_path(texture_file)
            except (FileNotFoundError, ValueError) as e:
                raise ValueError(f"Texture file {i} ({texture_file}): {e}")
        
        # Use efficient multi-texture C++ implementation if available, otherwise triangle-by-triangle
        if 'addTrianglesFromArraysMultiTextured' in context_wrapper._AVAILABLE_TRIANGLE_FUNCTIONS:
            return context_wrapper.addTrianglesFromArraysMultiTextured(
                self.context, vertices, faces, uv_coords, texture_file_list, material_ids
            )
        else:
            # Use triangle-by-triangle approach with addTriangleTextured
            from .wrappers.DataTypes import vec3, vec2
            
            vertices_float = vertices.astype(np.float32)
            faces_int = faces.astype(np.int32)
            uv_coords_float = uv_coords.astype(np.float32)
            
            triangle_uuids = []
            for i in range(faces.shape[0]):
                # Get vertex indices for this triangle
                v0_idx, v1_idx, v2_idx = faces_int[i]
                
                # Get vertex coordinates as vec3 objects
                vertex0 = vec3(vertices_float[v0_idx][0], vertices_float[v0_idx][1], vertices_float[v0_idx][2])
                vertex1 = vec3(vertices_float[v1_idx][0], vertices_float[v1_idx][1], vertices_float[v1_idx][2])
                vertex2 = vec3(vertices_float[v2_idx][0], vertices_float[v2_idx][1], vertices_float[v2_idx][2])
                
                # Get UV coordinates as vec2 objects
                uv0 = vec2(uv_coords_float[v0_idx][0], uv_coords_float[v0_idx][1])
                uv1 = vec2(uv_coords_float[v1_idx][0], uv_coords_float[v1_idx][1])
                uv2 = vec2(uv_coords_float[v2_idx][0], uv_coords_float[v2_idx][1])
                
                # Use texture file based on material ID for this triangle
                material_id = material_ids[i]
                texture_file = texture_file_list[material_id]
                
                # Add textured triangle using the new addTriangleTextured method
                uuid = self.addTriangleTextured(vertex0, vertex1, vertex2, texture_file, uv0, uv1, uv2)
                triangle_uuids.append(uuid)
            
            return triangle_uuids

    # ==================== PRIMITIVE DATA METHODS ====================
    # Primitive data is a flexible key-value store where users can associate 
    # arbitrary data with primitives using string keys
    
    def setPrimitiveDataInt(self, uuids_or_uuid, label: str, value: int) -> None:
        """
        Set primitive data as signed 32-bit integer for one or multiple primitives.

        Args:
            uuids_or_uuid: Single UUID (int) or list of UUIDs to set data for
            label: String key for the data
            value: Signed integer value (broadcast to all UUIDs if list provided)
        """
        if isinstance(uuids_or_uuid, (list, tuple)):
            context_wrapper.setBroadcastPrimitiveDataInt(self.context, uuids_or_uuid, label, value)
        else:
            context_wrapper.setPrimitiveDataInt(self.context, uuids_or_uuid, label, value)

    def setPrimitiveDataUInt(self, uuids_or_uuid, label: str, value: int) -> None:
        """
        Set primitive data as unsigned 32-bit integer for one or multiple primitives.

        Critical for properties like 'twosided_flag' which must be uint in C++.

        Args:
            uuids_or_uuid: Single UUID (int) or list of UUIDs to set data for
            label: String key for the data
            value: Unsigned integer value (broadcast to all UUIDs if list provided)
        """
        if isinstance(uuids_or_uuid, (list, tuple)):
            context_wrapper.setBroadcastPrimitiveDataUInt(self.context, uuids_or_uuid, label, value)
        else:
            context_wrapper.setPrimitiveDataUInt(self.context, uuids_or_uuid, label, value)

    def setPrimitiveDataFloat(self, uuids_or_uuid, label: str, value: float) -> None:
        """
        Set primitive data as 32-bit float for one or multiple primitives.

        Args:
            uuids_or_uuid: Single UUID (int) or list of UUIDs to set data for
            label: String key for the data
            value: Float value (broadcast to all UUIDs if list provided)
        """
        if isinstance(uuids_or_uuid, (list, tuple)):
            context_wrapper.setBroadcastPrimitiveDataFloat(self.context, uuids_or_uuid, label, value)
        else:
            context_wrapper.setPrimitiveDataFloat(self.context, uuids_or_uuid, label, value)

    def setPrimitiveDataDouble(self, uuids_or_uuid, label: str, value: float) -> None:
        """
        Set primitive data as 64-bit double for one or multiple primitives.

        Args:
            uuids_or_uuid: Single UUID (int) or list of UUIDs to set data for
            label: String key for the data
            value: Double value (broadcast to all UUIDs if list provided)
        """
        if isinstance(uuids_or_uuid, (list, tuple)):
            context_wrapper.setBroadcastPrimitiveDataDouble(self.context, uuids_or_uuid, label, value)
        else:
            context_wrapper.setPrimitiveDataDouble(self.context, uuids_or_uuid, label, value)

    def setPrimitiveDataString(self, uuids_or_uuid, label: str, value: str) -> None:
        """
        Set primitive data as string for one or multiple primitives.

        Args:
            uuids_or_uuid: Single UUID (int) or list of UUIDs to set data for
            label: String key for the data
            value: String value (broadcast to all UUIDs if list provided)
        """
        if isinstance(uuids_or_uuid, (list, tuple)):
            context_wrapper.setBroadcastPrimitiveDataString(self.context, uuids_or_uuid, label, value)
        else:
            context_wrapper.setPrimitiveDataString(self.context, uuids_or_uuid, label, value)

    def setPrimitiveDataVec2(self, uuids_or_uuid, label: str, x_or_vec, y: float = None) -> None:
        """
        Set primitive data as vec2 for one or multiple primitives.

        Args:
            uuids_or_uuid: Single UUID (int) or list of UUIDs to set data for
            label: String key for the data
            x_or_vec: Either x component (float) or vec2 object
            y: Y component (if x_or_vec is float)
        """
        if hasattr(x_or_vec, 'x'):
            x, y = x_or_vec.x, x_or_vec.y
        else:
            x = x_or_vec
        if isinstance(uuids_or_uuid, (list, tuple)):
            context_wrapper.setBroadcastPrimitiveDataVec2(self.context, uuids_or_uuid, label, x, y)
        else:
            context_wrapper.setPrimitiveDataVec2(self.context, uuids_or_uuid, label, x, y)

    def setPrimitiveDataVec3(self, uuids_or_uuid, label: str, x_or_vec, y: float = None, z: float = None) -> None:
        """
        Set primitive data as vec3 for one or multiple primitives.

        Args:
            uuids_or_uuid: Single UUID (int) or list of UUIDs to set data for
            label: String key for the data
            x_or_vec: Either x component (float) or vec3 object
            y: Y component (if x_or_vec is float)
            z: Z component (if x_or_vec is float)
        """
        if hasattr(x_or_vec, 'x'):
            x, y, z = x_or_vec.x, x_or_vec.y, x_or_vec.z
        else:
            x = x_or_vec
        if isinstance(uuids_or_uuid, (list, tuple)):
            context_wrapper.setBroadcastPrimitiveDataVec3(self.context, uuids_or_uuid, label, x, y, z)
        else:
            context_wrapper.setPrimitiveDataVec3(self.context, uuids_or_uuid, label, x, y, z)

    def setPrimitiveDataVec4(self, uuids_or_uuid, label: str, x_or_vec, y: float = None, z: float = None, w: float = None) -> None:
        """
        Set primitive data as vec4 for one or multiple primitives.

        Args:
            uuids_or_uuid: Single UUID (int) or list of UUIDs to set data for
            label: String key for the data
            x_or_vec: Either x component (float) or vec4 object
            y: Y component (if x_or_vec is float)
            z: Z component (if x_or_vec is float)
            w: W component (if x_or_vec is float)
        """
        if hasattr(x_or_vec, 'x'):
            x, y, z, w = x_or_vec.x, x_or_vec.y, x_or_vec.z, x_or_vec.w
        else:
            x = x_or_vec
        if isinstance(uuids_or_uuid, (list, tuple)):
            context_wrapper.setBroadcastPrimitiveDataVec4(self.context, uuids_or_uuid, label, x, y, z, w)
        else:
            context_wrapper.setPrimitiveDataVec4(self.context, uuids_or_uuid, label, x, y, z, w)

    def setPrimitiveDataInt2(self, uuids_or_uuid, label: str, x_or_vec, y: int = None) -> None:
        """
        Set primitive data as int2 for one or multiple primitives.

        Args:
            uuids_or_uuid: Single UUID (int) or list of UUIDs to set data for
            label: String key for the data
            x_or_vec: Either x component (int) or int2 object
            y: Y component (if x_or_vec is int)
        """
        if hasattr(x_or_vec, 'x'):
            x, y = x_or_vec.x, x_or_vec.y
        else:
            x = x_or_vec
        if isinstance(uuids_or_uuid, (list, tuple)):
            context_wrapper.setBroadcastPrimitiveDataInt2(self.context, uuids_or_uuid, label, x, y)
        else:
            context_wrapper.setPrimitiveDataInt2(self.context, uuids_or_uuid, label, x, y)

    def setPrimitiveDataInt3(self, uuids_or_uuid, label: str, x_or_vec, y: int = None, z: int = None) -> None:
        """
        Set primitive data as int3 for one or multiple primitives.

        Args:
            uuids_or_uuid: Single UUID (int) or list of UUIDs to set data for
            label: String key for the data
            x_or_vec: Either x component (int) or int3 object
            y: Y component (if x_or_vec is int)
            z: Z component (if x_or_vec is int)
        """
        if hasattr(x_or_vec, 'x'):
            x, y, z = x_or_vec.x, x_or_vec.y, x_or_vec.z
        else:
            x = x_or_vec
        if isinstance(uuids_or_uuid, (list, tuple)):
            context_wrapper.setBroadcastPrimitiveDataInt3(self.context, uuids_or_uuid, label, x, y, z)
        else:
            context_wrapper.setPrimitiveDataInt3(self.context, uuids_or_uuid, label, x, y, z)

    def setPrimitiveDataInt4(self, uuids_or_uuid, label: str, x_or_vec, y: int = None, z: int = None, w: int = None) -> None:
        """
        Set primitive data as int4 for one or multiple primitives.

        Args:
            uuids_or_uuid: Single UUID (int) or list of UUIDs to set data for
            label: String key for the data
            x_or_vec: Either x component (int) or int4 object
            y: Y component (if x_or_vec is int)
            z: Z component (if x_or_vec is int)
            w: W component (if x_or_vec is int)
        """
        if hasattr(x_or_vec, 'x'):
            x, y, z, w = x_or_vec.x, x_or_vec.y, x_or_vec.z, x_or_vec.w
        else:
            x = x_or_vec
        if isinstance(uuids_or_uuid, (list, tuple)):
            context_wrapper.setBroadcastPrimitiveDataInt4(self.context, uuids_or_uuid, label, x, y, z, w)
        else:
            context_wrapper.setPrimitiveDataInt4(self.context, uuids_or_uuid, label, x, y, z, w)
    
    def getPrimitiveData(self, uuid: int, label: str, data_type: type = None):
        """
        Get primitive data for a specific primitive. If data_type is provided, it works like before.
        If data_type is None, it automatically detects the type and returns the appropriate value.
        
        Args:
            uuid: UUID of the primitive  
            label: String key for the data
            data_type: Optional. Python type to retrieve (int, uint, float, double, bool, str, vec2, vec3, vec4, int2, int3, int4, etc.)
                      If None, auto-detects the type using C++ getPrimitiveDataType().
            
        Returns:
            The stored value of the specified or auto-detected type
        """
        # If no type specified, use auto-detection
        if data_type is None:
            return context_wrapper.getPrimitiveDataAuto(self.context, uuid, label)
        
        # Handle basic types (original behavior when type is specified)
        if data_type == int:
            return context_wrapper.getPrimitiveDataInt(self.context, uuid, label)
        elif data_type == float:
            return context_wrapper.getPrimitiveDataFloat(self.context, uuid, label)
        elif data_type == bool:
            # Bool is not supported by Helios core - get as int and convert
            int_value = context_wrapper.getPrimitiveDataInt(self.context, uuid, label)
            return int_value != 0
        elif data_type == str:
            return context_wrapper.getPrimitiveDataString(self.context, uuid, label)
        
        # Handle Helios vector types
        elif data_type == vec2:
            coords = context_wrapper.getPrimitiveDataVec2(self.context, uuid, label)
            return vec2(coords[0], coords[1])
        elif data_type == vec3:
            coords = context_wrapper.getPrimitiveDataVec3(self.context, uuid, label)
            return vec3(coords[0], coords[1], coords[2])
        elif data_type == vec4:
            coords = context_wrapper.getPrimitiveDataVec4(self.context, uuid, label)
            return vec4(coords[0], coords[1], coords[2], coords[3])
        elif data_type == int2:
            coords = context_wrapper.getPrimitiveDataInt2(self.context, uuid, label)
            return int2(coords[0], coords[1])
        elif data_type == int3:
            coords = context_wrapper.getPrimitiveDataInt3(self.context, uuid, label)
            return int3(coords[0], coords[1], coords[2])
        elif data_type == int4:
            coords = context_wrapper.getPrimitiveDataInt4(self.context, uuid, label)
            return int4(coords[0], coords[1], coords[2], coords[3])
        
        # Handle extended numeric types (require explicit specification since Python doesn't have these as distinct types)
        elif data_type == "uint":
            return context_wrapper.getPrimitiveDataUInt(self.context, uuid, label)
        elif data_type == "double":
            return context_wrapper.getPrimitiveDataDouble(self.context, uuid, label)
        
        # Handle list return types (for convenience)
        elif data_type == list:
            # Default to vec3 as list for backward compatibility
            return context_wrapper.getPrimitiveDataVec3(self.context, uuid, label)
        elif data_type == "list_vec2":
            return context_wrapper.getPrimitiveDataVec2(self.context, uuid, label)
        elif data_type == "list_vec4":
            return context_wrapper.getPrimitiveDataVec4(self.context, uuid, label)
        elif data_type == "list_int2":
            return context_wrapper.getPrimitiveDataInt2(self.context, uuid, label)
        elif data_type == "list_int3":
            return context_wrapper.getPrimitiveDataInt3(self.context, uuid, label)
        elif data_type == "list_int4":
            return context_wrapper.getPrimitiveDataInt4(self.context, uuid, label)
        
        else:
            raise ValueError(f"Unsupported primitive data type: {data_type}. "
                           f"Supported types: int, float, bool, str, vec2, vec3, vec4, int2, int3, int4, "
                           f"'uint', 'double', list (for vec3), 'list_vec2', 'list_vec4', 'list_int2', 'list_int3', 'list_int4'")
    
    def doesPrimitiveDataExist(self, uuid: int, label: str) -> bool:
        """
        Check if primitive data exists for a specific primitive and label.
        
        Args:
            uuid: UUID of the primitive
            label: String key for the data
            
        Returns:
            True if the data exists, False otherwise
        """
        return context_wrapper.doesPrimitiveDataExistWrapper(self.context, uuid, label)
    
    def getPrimitiveDataFloat(self, uuid: int, label: str) -> float:
        """
        Convenience method to get float primitive data.
        
        Args:
            uuid: UUID of the primitive
            label: String key for the data
            
        Returns:
            Float value stored for the primitive
        """
        return self.getPrimitiveData(uuid, label, float)
    
    def getPrimitiveDataType(self, uuid: int, label: str) -> int:
        """
        Get the Helios data type of primitive data.
        
        Args:
            uuid: UUID of the primitive
            label: String key for the data
            
        Returns:
            HeliosDataType enum value as integer
        """
        return context_wrapper.getPrimitiveDataTypeWrapper(self.context, uuid, label)
    
    def getPrimitiveDataSize(self, uuid: int, label: str) -> int:
        """
        Get the size/length of primitive data (for vector data).
        
        Args:
            uuid: UUID of the primitive
            label: String key for the data
            
        Returns:
            Size of data array, or 1 for scalar data
        """
        return context_wrapper.getPrimitiveDataSizeWrapper(self.context, uuid, label)
    
    def getPrimitiveDataArray(self, uuids: List[int], label: str) -> np.ndarray:
        """
        Get primitive data values for multiple primitives as a NumPy array.
        
        This method retrieves primitive data for a list of UUIDs and returns the values
        as a NumPy array. The output array has the same length as the input UUID list,
        with each index corresponding to the primitive data value for that UUID.
        
        Args:
            uuids: List of primitive UUIDs to get data for
            label: String key for the primitive data to retrieve
            
        Returns:
            NumPy array of primitive data values corresponding to each UUID.
            The array type depends on the data type:
            - int data: int32 array
            - uint data: uint32 array  
            - float data: float32 array
            - double data: float64 array
            - vector data: float32 array with shape (N, vector_size)
            - string data: object array of strings
            
        Raises:
            ValueError: If UUID list is empty or UUIDs don't exist
            RuntimeError: If context is in mock mode or data doesn't exist for some UUIDs
        """
        self._check_context_available()
        
        if not uuids:
            raise ValueError("UUID list cannot be empty")
        
        # First validate that all UUIDs exist
        for uuid in uuids:
            self._validate_uuid(uuid)
        
        # Then check that all UUIDs have the specified data
        for uuid in uuids:
            if not self.doesPrimitiveDataExist(uuid, label):
                raise ValueError(f"Primitive data '{label}' does not exist for UUID {uuid}")
        
        # Get data type from the first UUID to determine array type
        first_uuid = uuids[0]
        data_type = self.getPrimitiveDataType(first_uuid, label)
        
        # Map Helios data types to NumPy array creation
        # Based on HeliosDataType enum from Helios core
        if data_type == 0:  # HELIOS_TYPE_INT
            result = np.empty(len(uuids), dtype=np.int32)
            for i, uuid in enumerate(uuids):
                result[i] = self.getPrimitiveData(uuid, label, int)
                
        elif data_type == 1:  # HELIOS_TYPE_UINT
            result = np.empty(len(uuids), dtype=np.uint32)
            for i, uuid in enumerate(uuids):
                result[i] = self.getPrimitiveData(uuid, label, "uint")
                
        elif data_type == 2:  # HELIOS_TYPE_FLOAT
            result = np.empty(len(uuids), dtype=np.float32)
            for i, uuid in enumerate(uuids):
                result[i] = self.getPrimitiveData(uuid, label, float)
                
        elif data_type == 3:  # HELIOS_TYPE_DOUBLE
            result = np.empty(len(uuids), dtype=np.float64)
            for i, uuid in enumerate(uuids):
                result[i] = self.getPrimitiveData(uuid, label, "double")
                
        elif data_type == 4:  # HELIOS_TYPE_VEC2
            result = np.empty((len(uuids), 2), dtype=np.float32)
            for i, uuid in enumerate(uuids):
                vec_data = self.getPrimitiveData(uuid, label, vec2)
                result[i] = [vec_data.x, vec_data.y]
                
        elif data_type == 5:  # HELIOS_TYPE_VEC3
            result = np.empty((len(uuids), 3), dtype=np.float32)
            for i, uuid in enumerate(uuids):
                vec_data = self.getPrimitiveData(uuid, label, vec3)
                result[i] = [vec_data.x, vec_data.y, vec_data.z]
                
        elif data_type == 6:  # HELIOS_TYPE_VEC4
            result = np.empty((len(uuids), 4), dtype=np.float32)
            for i, uuid in enumerate(uuids):
                vec_data = self.getPrimitiveData(uuid, label, vec4)
                result[i] = [vec_data.x, vec_data.y, vec_data.z, vec_data.w]
                
        elif data_type == 7:  # HELIOS_TYPE_INT2
            result = np.empty((len(uuids), 2), dtype=np.int32)
            for i, uuid in enumerate(uuids):
                int_data = self.getPrimitiveData(uuid, label, int2)
                result[i] = [int_data.x, int_data.y]
                
        elif data_type == 8:  # HELIOS_TYPE_INT3
            result = np.empty((len(uuids), 3), dtype=np.int32)
            for i, uuid in enumerate(uuids):
                int_data = self.getPrimitiveData(uuid, label, int3)
                result[i] = [int_data.x, int_data.y, int_data.z]
                
        elif data_type == 9:  # HELIOS_TYPE_INT4
            result = np.empty((len(uuids), 4), dtype=np.int32)
            for i, uuid in enumerate(uuids):
                int_data = self.getPrimitiveData(uuid, label, int4)
                result[i] = [int_data.x, int_data.y, int_data.z, int_data.w]
                
        elif data_type == 10:  # HELIOS_TYPE_STRING
            result = np.empty(len(uuids), dtype=object)
            for i, uuid in enumerate(uuids):
                result[i] = self.getPrimitiveData(uuid, label, str)
                
        else:
            raise ValueError(f"Unsupported primitive data type: {data_type}")
        
        return result
    
    
    def colorPrimitiveByDataPseudocolor(self, uuids: List[int], primitive_data: str, 
                                       colormap: str = "hot", ncolors: int = 10, 
                                       max_val: Optional[float] = None, min_val: Optional[float] = None):
        """
        Color primitives based on primitive data values using pseudocolor mapping.
        
        This method applies a pseudocolor mapping to primitives based on the values
        of specified primitive data. The primitive colors are updated to reflect the
        data values using a color map.
        
        Args:
            uuids: List of primitive UUIDs to color
            primitive_data: Name of primitive data to use for coloring (e.g., "radiation_flux_SW")
            colormap: Color map name - options include "hot", "cool", "parula", "rainbow", "gray", "lava"
            ncolors: Number of discrete colors in color map (default: 10)
            max_val: Maximum value for color scale (auto-determined if None)
            min_val: Minimum value for color scale (auto-determined if None)
        """
        if max_val is not None and min_val is not None:
            context_wrapper.colorPrimitiveByDataPseudocolorWithRange(
                self.context, uuids, primitive_data, colormap, ncolors, max_val, min_val)
        else:
            context_wrapper.colorPrimitiveByDataPseudocolor(
                self.context, uuids, primitive_data, colormap, ncolors)
    
    # Context time/date methods for solar position integration
    def setTime(self, hour: int, minute: int = 0, second: int = 0):
        """
        Set the simulation time.
        
        Args:
            hour: Hour (0-23)
            minute: Minute (0-59), defaults to 0
            second: Second (0-59), defaults to 0
            
        Raises:
            ValueError: If time values are out of range
            NotImplementedError: If time/date functions not available in current library build
            
        Example:
            >>> context.setTime(14, 30)  # Set to 2:30 PM
            >>> context.setTime(9, 15, 30)  # Set to 9:15:30 AM
        """
        context_wrapper.setTime(self.context, hour, minute, second)
    
    def setDate(self, year: int, month: int, day: int):
        """
        Set the simulation date.
        
        Args:
            year: Year (1900-3000)
            month: Month (1-12)
            day: Day (1-31)
            
        Raises:
            ValueError: If date values are out of range
            NotImplementedError: If time/date functions not available in current library build
            
        Example:
            >>> context.setDate(2023, 6, 21)  # Set to June 21, 2023
        """
        context_wrapper.setDate(self.context, year, month, day)
    
    def setDateJulian(self, julian_day: int, year: int):
        """
        Set the simulation date using Julian day number.
        
        Args:
            julian_day: Julian day (1-366)
            year: Year (1900-3000)
            
        Raises:
            ValueError: If values are out of range
            NotImplementedError: If time/date functions not available in current library build
            
        Example:
            >>> context.setDateJulian(172, 2023)  # Set to day 172 of 2023 (June 21)
        """
        context_wrapper.setDateJulian(self.context, julian_day, year)
    
    def getTime(self):
        """
        Get the current simulation time.
        
        Returns:
            Tuple of (hour, minute, second) as integers
            
        Raises:
            NotImplementedError: If time/date functions not available in current library build
            
        Example:
            >>> hour, minute, second = context.getTime()
            >>> print(f"Current time: {hour:02d}:{minute:02d}:{second:02d}")
        """
        return context_wrapper.getTime(self.context)
    
    def getDate(self):
        """
        Get the current simulation date.
        
        Returns:
            Tuple of (year, month, day) as integers
            
        Raises:
            NotImplementedError: If time/date functions not available in current library build
            
        Example:
            >>> year, month, day = context.getDate()
            >>> print(f"Current date: {year}-{month:02d}-{day:02d}")
        """
        return context_wrapper.getDate(self.context)

    # ==========================================================================
    # Timeseries Methods
    # ==========================================================================

    def addTimeseriesData(self, label: str, value: float, date: 'Date', time: 'Time'):
        """
        Add a data point to a timeseries variable.

        Args:
            label: Name of the timeseries variable (e.g., "temperature")
            value: Value of the data point
            date: Date of the data point
            time: Time of the data point

        Raises:
            ValueError: If label is empty, or date/time are wrong types
            NotImplementedError: If timeseries functions not available

        Example:
            >>> from pyhelios.types import Date, Time
            >>> context.addTimeseriesData("temperature", 25.3, Date(2024, 6, 15), Time(12, 0, 0))
        """
        self._check_context_available()
        if not isinstance(label, str) or not label:
            raise ValueError("Label must be a non-empty string")
        if not isinstance(date, Date):
            raise ValueError(f"date must be a Date instance, got {type(date).__name__}")
        if not isinstance(time, Time):
            raise ValueError(f"time must be a Time instance, got {type(time).__name__}")

        context_wrapper.addTimeseriesData(
            self.context, label, float(value),
            date.day, date.month, date.year,
            time.hour, time.minute, time.second
        )

    def updateTimeseriesData(self, label: str, date: 'Date', time: 'Time', new_value: float):
        """
        Update the value of an existing timeseries data point.

        Args:
            label: Name of the timeseries variable (must already exist)
            date: Date of the existing point (must match exactly)
            time: Time of the existing point (must match exactly)
            new_value: Replacement value

        Raises:
            ValueError: If label is empty, or date/time are wrong types
            HeliosRuntimeError: If the variable does not exist or no point matches the (date, time)
            NotImplementedError: If timeseries functions not available

        Example:
            >>> from pyhelios.types import Date, Time
            >>> context.addTimeseriesData("temperature", 25.3, Date(2024, 6, 15), Time(12, 0, 0))
            >>> context.updateTimeseriesData("temperature", Date(2024, 6, 15), Time(12, 0, 0), 26.5)
        """
        self._check_context_available()
        if not isinstance(label, str) or not label:
            raise ValueError("Label must be a non-empty string")
        if not isinstance(date, Date):
            raise ValueError(f"date must be a Date instance, got {type(date).__name__}")
        if not isinstance(time, Time):
            raise ValueError(f"time must be a Time instance, got {type(time).__name__}")

        context_wrapper.updateTimeseriesData(
            self.context, label,
            date.day, date.month, date.year,
            time.hour, time.minute, time.second,
            float(new_value)
        )

    def setCurrentTimeseriesPoint(self, label: str, index: int):
        """
        Set the Context date and time from a timeseries data point index.

        Args:
            label: Name of the timeseries variable
            index: Index of the data point (0 = earliest, chronologically ordered)

        Raises:
            ValueError: If label is empty or index is negative
            NotImplementedError: If timeseries functions not available

        Example:
            >>> context.setCurrentTimeseriesPoint("temperature", 0)
        """
        self._check_context_available()
        if not isinstance(label, str) or not label:
            raise ValueError("Label must be a non-empty string")
        if not isinstance(index, int) or index < 0:
            raise ValueError(f"Index must be a non-negative integer, got {index}")

        context_wrapper.setCurrentTimeseriesPoint(self.context, label, index)

    def queryTimeseriesData(self, label: str, date: 'Date' = None, time: 'Time' = None,
                            index: int = None) -> float:
        """
        Query a timeseries data value.

        Three modes of operation:
        - With date and time: returns interpolated value at the specified date/time
        - With index: returns value at the specified data point index
        - With neither: returns value at the current Context date/time

        Args:
            label: Name of the timeseries variable
            date: Date to query at (requires time as well)
            time: Time to query at (requires date as well)
            index: Index of the data point (0 = earliest)

        Returns:
            The timeseries value as a float

        Raises:
            ValueError: If both date/time and index are provided, or if date without time
            NotImplementedError: If timeseries functions not available

        Example:
            >>> # Query at specific date/time
            >>> val = context.queryTimeseriesData("temperature", date=Date(2024, 6, 15), time=Time(12, 0, 0))
            >>> # Query by index
            >>> val = context.queryTimeseriesData("temperature", index=0)
            >>> # Query at current context time
            >>> val = context.queryTimeseriesData("temperature")
        """
        self._check_context_available()
        if not isinstance(label, str) or not label:
            raise ValueError("Label must be a non-empty string")

        has_datetime = date is not None or time is not None
        has_index = index is not None

        if has_datetime and has_index:
            raise ValueError("Cannot specify both date/time and index. Use one or the other.")

        if has_datetime:
            if date is None or time is None:
                raise ValueError("Both date and time must be provided together")
            if not isinstance(date, Date):
                raise ValueError(f"date must be a Date instance, got {type(date).__name__}")
            if not isinstance(time, Time):
                raise ValueError(f"time must be a Time instance, got {type(time).__name__}")
            return context_wrapper.queryTimeseriesDataDateTime(
                self.context, label,
                date.day, date.month, date.year,
                time.hour, time.minute, time.second
            )

        if has_index:
            if not isinstance(index, int) or index < 0:
                raise ValueError(f"Index must be a non-negative integer, got {index}")
            return context_wrapper.queryTimeseriesDataIndex(self.context, label, index)

        return context_wrapper.queryTimeseriesDataCurrent(self.context, label)

    def queryTimeseriesTime(self, label: str, index: int) -> 'Time':
        """
        Get the Time associated with a timeseries data point.

        Args:
            label: Name of the timeseries variable
            index: Index of the data point (0 = earliest)

        Returns:
            Time object for the data point

        Raises:
            ValueError: If label is empty or index is negative
            NotImplementedError: If timeseries functions not available

        Example:
            >>> t = context.queryTimeseriesTime("temperature", 0)
            >>> print(f"{t.hour:02d}:{t.minute:02d}:{t.second:02d}")
        """
        self._check_context_available()
        if not isinstance(label, str) or not label:
            raise ValueError("Label must be a non-empty string")
        if not isinstance(index, int) or index < 0:
            raise ValueError(f"Index must be a non-negative integer, got {index}")

        hour, minute, second = context_wrapper.queryTimeseriesTime(self.context, label, index)
        return Time(hour=hour, minute=minute, second=second)

    def queryTimeseriesDate(self, label: str, index: int) -> 'Date':
        """
        Get the Date associated with a timeseries data point.

        Args:
            label: Name of the timeseries variable
            index: Index of the data point (0 = earliest)

        Returns:
            Date object for the data point

        Raises:
            ValueError: If label is empty or index is negative
            NotImplementedError: If timeseries functions not available

        Example:
            >>> d = context.queryTimeseriesDate("temperature", 0)
            >>> print(f"{d.year}-{d.month:02d}-{d.day:02d}")
        """
        self._check_context_available()
        if not isinstance(label, str) or not label:
            raise ValueError("Label must be a non-empty string")
        if not isinstance(index, int) or index < 0:
            raise ValueError(f"Index must be a non-negative integer, got {index}")

        year, month, day = context_wrapper.queryTimeseriesDate(self.context, label, index)
        return Date(year=year, month=month, day=day)

    def getTimeseriesLength(self, label: str) -> int:
        """
        Get the number of data points in a timeseries variable.

        Args:
            label: Name of the timeseries variable

        Returns:
            Number of data points

        Raises:
            ValueError: If label is empty
            NotImplementedError: If timeseries functions not available

        Example:
            >>> n = context.getTimeseriesLength("temperature")
            >>> print(f"Timeseries has {n} data points")
        """
        self._check_context_available()
        if not isinstance(label, str) or not label:
            raise ValueError("Label must be a non-empty string")

        return context_wrapper.getTimeseriesLength(self.context, label)

    def doesTimeseriesVariableExist(self, label: str) -> bool:
        """
        Check whether a timeseries variable exists.

        Args:
            label: Name of the timeseries variable

        Returns:
            True if the variable exists, False otherwise

        Raises:
            ValueError: If label is empty
            NotImplementedError: If timeseries functions not available

        Example:
            >>> if context.doesTimeseriesVariableExist("temperature"):
            ...     print("Temperature data loaded")
        """
        self._check_context_available()
        if not isinstance(label, str) or not label:
            raise ValueError("Label must be a non-empty string")

        return context_wrapper.doesTimeseriesVariableExist(self.context, label)

    def listTimeseriesVariables(self) -> List[str]:
        """
        List all existing timeseries variables.

        Returns:
            List of timeseries variable names

        Raises:
            NotImplementedError: If timeseries functions not available

        Example:
            >>> variables = context.listTimeseriesVariables()
            >>> for var in variables:
            ...     print(f"  {var}: {context.getTimeseriesLength(var)} points")
        """
        self._check_context_available()

        return context_wrapper.listTimeseriesVariables(self.context)

    def clearTimeseriesData(self):
        """Clear all timeseries data from the Context.

        Removes all timeseries variables and their associated date/time values.

        Raises:
            NotImplementedError: If timeseries functions not available

        Example:
            >>> context.clearTimeseriesData()
            >>> context.listTimeseriesVariables()
            []
        """
        self._check_context_available()
        context_wrapper.clearTimeseriesData(self.context)

    def deleteTimeseriesVariable(self, label: str):
        """Delete a single timeseries variable and all of its data points.

        Complements :meth:`clearTimeseriesData` (which removes all variables) and
        :meth:`updateTimeseriesData` (which modifies a single point).

        Args:
            label: Name of the timeseries variable to delete.

        Raises:
            ValueError: If ``label`` is empty.
            NotImplementedError: If running against helios-core older than v1.3.72.

        Note:
            If the variable does not exist, the underlying Helios API issues a
            non-fatal warning to stderr and the call is otherwise a no-op.

        Example:
            >>> context.addTimeseriesData("temperature", 25.3, Date(2024, 6, 15), Time(12, 0, 0))
            >>> context.deleteTimeseriesVariable("temperature")
            >>> context.doesTimeseriesVariableExist("temperature")
            False
        """
        self._check_context_available()
        if not isinstance(label, str) or not label:
            raise ValueError("Label must be a non-empty string")
        context_wrapper.deleteTimeseriesVariable(self.context, label)

    def loadTabularTimeseriesData(self, data_file: str, column_labels: List[str],
                                  delimiter: str = ",", date_string_format: str = "YYYYMMDD",
                                  headerlines: int = 0):
        """
        Load tabular timeseries data from a text file.

        The file should contain columns of data with dates/times and measured values.
        Column labels specify how each column should be interpreted. Special labels
        include "year", "DOY", "date", "datetime", "hour", "minute", "second", "time".
        Other labels become timeseries variable names.

        Args:
            data_file: Path to the text file containing tabular data
            column_labels: List of column label strings specifying what each column contains
            delimiter: Column delimiter string (default: ",")
            date_string_format: Format of date strings in the file. Supported formats:
                "YYYYMMDD", "YYYYMMDDHH", "YYYYMMDDHHMM", "DD/MM/YYYY",
                "MM/DD/YYYY", "DDMMYYYY", "YYYY-MM-DD", "DD/MM/YYYY HH:MM",
                "MM/DD/YYYY HH:MM", "ISO8601" (default: "YYYYMMDD")
            headerlines: Number of header lines to skip (default: 0)

        Raises:
            ValueError: If data_file is empty, column_labels is empty, or delimiter is empty
            RuntimeError: If the file cannot be read or parsed
            NotImplementedError: If timeseries functions not available

        Example:
            >>> context.loadTabularTimeseriesData(
            ...     "weather_data.csv",
            ...     column_labels=["date", "hour", "temperature", "humidity"],
            ...     delimiter=",",
            ...     headerlines=1
            ... )
            >>> temp = context.queryTimeseriesData("temperature", index=0)
        """
        self._check_context_available()
        if not isinstance(data_file, str) or not data_file:
            raise ValueError("data_file must be a non-empty string")
        if not isinstance(column_labels, list) or not column_labels:
            raise ValueError("column_labels must be a non-empty list of strings")
        for i, label in enumerate(column_labels):
            if not isinstance(label, str):
                raise ValueError(f"column_labels[{i}] must be a string, got {type(label).__name__}")
        if not isinstance(delimiter, str) or not delimiter:
            raise ValueError("delimiter must be a non-empty string")

        context_wrapper.loadTabularTimeseriesData(
            self.context, data_file, column_labels, delimiter,
            date_string_format, headerlines
        )

    # ==========================================================================
    # Primitive and Object Deletion Methods
    # ==========================================================================

    def deletePrimitive(self, uuids_or_uuid: Union[int, List[int]]) -> None:
        """
        Delete one or more primitives from the context.

        This removes the primitive(s) entirely from the context. If a primitive
        belongs to a compound object, it will be removed from that object. If the
        object becomes empty after removal, it is automatically deleted.

        Args:
            uuids_or_uuid: Single UUID (int) or list of UUIDs to delete

        Raises:
            RuntimeError: If any UUID doesn't exist in the context
            ValueError: If UUID is invalid (negative)
            NotImplementedError: If delete functions not available in current library build

        Example:
            >>> context = Context()
            >>> patch_id = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
            >>> context.deletePrimitive(patch_id)  # Single deletion
            >>>
            >>> # Multiple deletion
            >>> ids = [context.addPatch() for _ in range(5)]
            >>> context.deletePrimitive(ids)  # Delete all at once
        """
        self._check_context_available()

        if isinstance(uuids_or_uuid, (list, tuple)):
            for uuid in uuids_or_uuid:
                if uuid < 0:
                    raise ValueError(f"UUID must be non-negative, got {uuid}")
            context_wrapper.deletePrimitives(self.context, list(uuids_or_uuid))
        else:
            if uuids_or_uuid < 0:
                raise ValueError(f"UUID must be non-negative, got {uuids_or_uuid}")
            context_wrapper.deletePrimitive(self.context, uuids_or_uuid)

    def deleteObject(self, objIDs_or_objID: Union[int, List[int]]) -> None:
        """
        Delete one or more compound objects from the context.

        This removes the compound object(s) AND all their child primitives.
        Use this when you want to delete an entire object hierarchy at once.

        Args:
            objIDs_or_objID: Single object ID (int) or list of object IDs to delete

        Raises:
            RuntimeError: If any object ID doesn't exist in the context
            ValueError: If object ID is invalid (negative)
            NotImplementedError: If delete functions not available in current library build

        Example:
            >>> context = Context()
            >>> # Create a compound object (e.g., a tile with multiple patches)
            >>> patch_ids = context.addTile(center=vec3(0, 0, 0), size=vec2(2, 2),
            ...                            tile_divisions=int2(2, 2))
            >>> obj_id = context.getPrimitiveParentObjectID(patch_ids[0])
            >>> context.deleteObject(obj_id)  # Deletes tile and all its patches
        """
        self._check_context_available()

        if isinstance(objIDs_or_objID, (list, tuple)):
            for objID in objIDs_or_objID:
                if objID < 0:
                    raise ValueError(f"Object ID must be non-negative, got {objID}")
            context_wrapper.deleteObjects(self.context, list(objIDs_or_objID))
        else:
            if objIDs_or_objID < 0:
                raise ValueError(f"Object ID must be non-negative, got {objIDs_or_objID}")
            context_wrapper.deleteObject(self.context, objIDs_or_objID)

    # Plugin-related methods
    def get_available_plugins(self) -> List[str]:
        """
        Get list of available plugins for this PyHelios instance.
        
        Returns:
            List of available plugin names
        """
        return self._plugin_registry.get_available_plugins()
    
    def is_plugin_available(self, plugin_name: str) -> bool:
        """
        Check if a specific plugin is available.
        
        Args:
            plugin_name: Name of the plugin to check
            
        Returns:
            True if plugin is available, False otherwise
        """
        return self._plugin_registry.is_plugin_available(plugin_name)
    
    def get_plugin_capabilities(self) -> dict:
        """
        Get detailed information about available plugin capabilities.
        
        Returns:
            Dictionary mapping plugin names to capability information
        """
        return self._plugin_registry.get_plugin_capabilities()
    
    def print_plugin_status(self):
        """Print detailed plugin status information."""
        self._plugin_registry.print_status()
    
    def get_missing_plugins(self, requested_plugins: List[str]) -> List[str]:
        """
        Get list of requested plugins that are not available.
        
        Args:
            requested_plugins: List of plugin names to check
            
        Returns:
            List of missing plugin names
        """
        return self._plugin_registry.get_missing_plugins(requested_plugins)

    # =========================================================================
    # Materials System (v1.3.58+)
    # =========================================================================

    def addMaterial(self, material_label: str):
        """
        Create a new material for sharing visual properties across primitives.

        Materials enable efficient memory usage by allowing multiple primitives to
        share rendering properties. Changes to a material affect all primitives using it.

        Args:
            material_label: Unique label for the material

        Raises:
            RuntimeError: If material label already exists

        Example:
            >>> context.addMaterial("wood_oak")
            >>> context.setMaterialColor("wood_oak", (0.6, 0.4, 0.2, 1.0))
            >>> context.assignMaterialToPrimitive(uuid, "wood_oak")
        """
        context_wrapper.addMaterial(self.context, material_label)

    def doesMaterialExist(self, material_label: str) -> bool:
        """Check if a material with the given label exists."""
        return context_wrapper.doesMaterialExist(self.context, material_label)

    def listMaterials(self) -> List[str]:
        """Get list of all material labels in the context."""
        return context_wrapper.listMaterials(self.context)

    def deleteMaterial(self, material_label: str):
        """
        Delete a material from the context.

        Primitives using this material will be reassigned to the default material.

        Args:
            material_label: Label of the material to delete

        Raises:
            RuntimeError: If material doesn't exist
        """
        context_wrapper.deleteMaterial(self.context, material_label)

    def getMaterialColor(self, material_label: str):
        """
        Get the RGBA color of a material.

        Args:
            material_label: Label of the material

        Returns:
            RGBAcolor object

        Raises:
            RuntimeError: If material doesn't exist
        """
        from .wrappers.DataTypes import RGBAcolor
        color_list = context_wrapper.getMaterialColor(self.context, material_label)
        return RGBAcolor(color_list[0], color_list[1], color_list[2], color_list[3])

    def setMaterialColor(self, material_label: str, color):
        """
        Set the RGBA color of a material.

        This affects all primitives that reference this material.

        Args:
            material_label: Label of the material
            color: RGBAcolor object or tuple/list of (r, g, b, a) values

        Raises:
            RuntimeError: If material doesn't exist

        Example:
            >>> from pyhelios.types import RGBAcolor
            >>> context.setMaterialColor("wood", RGBAcolor(0.6, 0.4, 0.2, 1.0))
            >>> context.setMaterialColor("wood", (0.6, 0.4, 0.2, 1.0))
        """
        if isinstance(color, RGBAcolor):
            r, g, b, a = color.r, color.g, color.b, color.a
        elif isinstance(color, (list, tuple)) and len(color) == 4:
            r, g, b, a = color[0], color[1], color[2], color[3]
        else:
            raise ValueError(f"Color must be an RGBAcolor or a 4-element list/tuple, got {type(color).__name__}")
        context_wrapper.setMaterialColor(self.context, material_label, r, g, b, a)

    def getMaterialTexture(self, material_label: str) -> str:
        """
        Get the texture file path for a material.

        Args:
            material_label: Label of the material

        Returns:
            Texture file path, or empty string if no texture

        Raises:
            RuntimeError: If material doesn't exist
        """
        return context_wrapper.getMaterialTexture(self.context, material_label)

    def setMaterialTexture(self, material_label: str, texture_file: str):
        """
        Set the texture file for a material.

        This affects all primitives that reference this material.

        Args:
            material_label: Label of the material
            texture_file: Path to texture image file

        Raises:
            RuntimeError: If material doesn't exist or texture file not found
        """
        context_wrapper.setMaterialTexture(self.context, material_label, texture_file)

    def isMaterialTextureColorOverridden(self, material_label: str) -> bool:
        """Check if material texture color is overridden by material color."""
        return context_wrapper.isMaterialTextureColorOverridden(self.context, material_label)

    def setMaterialTextureColorOverride(self, material_label: str, override: bool):
        """Set whether material color overrides texture color."""
        context_wrapper.setMaterialTextureColorOverride(self.context, material_label, override)

    def getMaterialTwosidedFlag(self, material_label: str) -> int:
        """Get the two-sided rendering flag for a material (0 = one-sided, 1 = two-sided)."""
        return context_wrapper.getMaterialTwosidedFlag(self.context, material_label)

    def setMaterialTwosidedFlag(self, material_label: str, twosided_flag: int):
        """Set the two-sided rendering flag for a material (0 = one-sided, 1 = two-sided)."""
        context_wrapper.setMaterialTwosidedFlag(self.context, material_label, twosided_flag)

    def assignMaterialToPrimitive(self, uuid, material_label: str):
        """
        Assign a material to primitive(s).

        Args:
            uuid: Single UUID (int) or list of UUIDs (List[int])
            material_label: Label of the material to assign

        Raises:
            RuntimeError: If primitive or material doesn't exist

        Example:
            >>> context.assignMaterialToPrimitive(uuid, "wood_oak")
            >>> context.assignMaterialToPrimitive([uuid1, uuid2, uuid3], "wood_oak")
        """
        if isinstance(uuid, (list, tuple)):
            context_wrapper.assignMaterialToPrimitives(self.context, uuid, material_label)
        else:
            context_wrapper.assignMaterialToPrimitive(self.context, uuid, material_label)

    def assignMaterialToObject(self, objID, material_label: str):
        """
        Assign a material to all primitives in compound object(s).

        Args:
            objID: Single object ID (int) or list of object IDs (List[int])
            material_label: Label of the material to assign

        Raises:
            RuntimeError: If object or material doesn't exist

        Example:
            >>> tree_id = wpt.buildTree(WPTType.LEMON)
            >>> context.assignMaterialToObject(tree_id, "tree_bark")
            >>> context.assignMaterialToObject([id1, id2], "grass")
        """
        if isinstance(objID, (list, tuple)):
            context_wrapper.assignMaterialToObjects(self.context, objID, material_label)
        else:
            context_wrapper.assignMaterialToObject(self.context, objID, material_label)

    def getPrimitiveMaterialLabel(self, uuid):
        """Get the material label assigned to a primitive or multiple primitives.

        Args:
            uuid: Single UUID (int) or list of UUIDs

        Returns:
            str for single UUID, or List[str] for list

        Raises:
            RuntimeError: If primitive doesn't exist
        """
        if isinstance(uuid, (list, tuple)):
            self._check_context_available()
            if not uuid:
                return []
            ptr, offsets, total = context_wrapper.getBatchPrimitiveMaterialLabels(self.context, uuid)
            if total == 0 or not ptr:
                return ["" for _ in uuid]
            full_str = ptr.decode('utf-8') if isinstance(ptr, bytes) else ptr
            return [full_str[offsets[i]:offsets[i+1]] for i in range(len(uuid))]
        return context_wrapper.getPrimitiveMaterialLabel(self.context, uuid)

    def getPrimitiveTwosidedFlag(self, uuid: int, default_value: int = 1) -> int:
        """
        Get two-sided rendering flag for a primitive.

        Checks material first, then primitive data if no material assigned.

        Args:
            uuid: UUID of the primitive
            default_value: Default value if no material/data (default 1 = two-sided)

        Returns:
            Two-sided flag (0 = one-sided, 1 = two-sided)
        """
        return context_wrapper.getPrimitiveTwosidedFlag(self.context, uuid, default_value)

    def getPrimitivesUsingMaterial(self, material_label: str) -> List[int]:
        """
        Get all primitive UUIDs that use a specific material.

        Args:
            material_label: Label of the material

        Returns:
            List of primitive UUIDs using the material

        Raises:
            RuntimeError: If material doesn't exist
        """
        return context_wrapper.getPrimitivesUsingMaterial(self.context, material_label)

    # =========================================================================
    # Texture Methods
    # =========================================================================

    def getPrimitiveTextureFile(self, uuid):
        """Get the texture file path of a primitive or multiple primitives.

        Args:
            uuid: Single UUID (int) or list of UUIDs

        Returns:
            str for single UUID, or List[str] for list
        """
        self._check_context_available()
        if isinstance(uuid, (list, tuple)):
            if not uuid:
                return []
            ptr, offsets, total = context_wrapper.getBatchPrimitiveTextureFiles(self.context, uuid)
            if total == 0 or not ptr:
                return ["" for _ in uuid]
            full_str = ptr.decode('utf-8') if isinstance(ptr, bytes) else ptr
            return [full_str[offsets[i]:offsets[i+1]] for i in range(len(uuid))]
        return context_wrapper.getPrimitiveTextureFile(self.context, uuid)

    def resolveMaterialTextures(self, uuids, colors_np):
        """Resolve material texture suppression for export.

        For each primitive, applies material-based texture suppression rules:
        1. If primitive has texture but material has no texture -> suppress texture, use material color
        2. If both have texture and textureColorOverride -> prefix "mask:", use material color
        3. Otherwise -> leave unchanged

        Args:
            uuids: List of primitive UUIDs
            colors_np: numpy float32 array of shape (N, 3), modified IN-PLACE

        Returns:
            List[str] of resolved texture file paths
        """
        self._check_context_available()
        if not uuids:
            return []
        return context_wrapper.resolveMaterialTextures(self.context, uuids, colors_np)

    def packGPUBuffers(self, uuids):
        """Pack GPU-ready geometry buffers for a set of primitives in a single C++ pass.

        Produces a binary blob containing contiguous typed arrays (positions,
        colors, uvs, indices, faceToUuid) grouped by texture, ready for
        zero-copy loading into Three.js BufferGeometry attributes.

        Args:
            uuids: List of primitive UUIDs

        Returns:
            bytes: Raw binary blob (see wire format v2 spec)
        """
        self._check_context_available()
        if not uuids:
            return b''
        return context_wrapper.packGPUBuffers(self.context, uuids)

    def setPrimitiveTextureFile(self, uuid: int, texture_file: str) -> None:
        """Set the texture file path of a primitive.

        Args:
            uuid: UUID of the primitive
            texture_file: Path to the texture file
        """
        self._check_context_available()
        context_wrapper.setPrimitiveTextureFile(self.context, uuid, texture_file)

    def getPrimitiveTextureSize(self, uuid: int) -> int2:
        """Get the texture size (width, height) of a primitive.

        Args:
            uuid: UUID of the primitive

        Returns:
            int2 with width and height of the texture
        """
        self._check_context_available()
        w, h = context_wrapper.getPrimitiveTextureSize(self.context, uuid)
        return int2(w, h)

    def getPrimitiveTextureUV(self, uuid):
        """Get the texture UV coordinates of a primitive or multiple primitives.

        Args:
            uuid: Single UUID (int) or list of UUIDs

        Returns:
            List[vec2] for single UUID, or tuple of (flat_data, offsets) for list
        """
        self._check_context_available()
        if isinstance(uuid, (list, tuple)):
            if not uuid:
                return (np.empty((0,), dtype=np.float32), np.zeros((1,), dtype=np.uint32))
            ptr, offsets, total = context_wrapper.getBatchPrimitiveTextureUV(self.context, uuid)
            offsets_arr = np.array(offsets, dtype=np.uint32)
            if total == 0 or not ptr:
                return (np.empty((0,), dtype=np.float32), offsets_arr)
            data = np.ctypeslib.as_array(ptr, shape=(total,)).copy()
            return (data, offsets_arr)
        uv_pairs = context_wrapper.getPrimitiveTextureUV(self.context, uuid)
        return [vec2(u, v) for u, v in uv_pairs]

    def primitiveTextureHasTransparencyChannel(self, uuid: int) -> bool:
        """Check if primitive texture has a transparency channel.

        Args:
            uuid: UUID of the primitive

        Returns:
            True if texture has transparency channel
        """
        self._check_context_available()
        return context_wrapper.primitiveTextureHasTransparencyChannel(self.context, uuid)

    def getPrimitiveSolidFraction(self, uuid):
        """Get the solid fraction of a primitive or multiple primitives.

        Args:
            uuid: Single UUID (int) or list of UUIDs

        Returns:
            float for single UUID, or np.ndarray of shape (N,) for list
        """
        self._check_context_available()
        if isinstance(uuid, (list, tuple)):
            if not uuid:
                return np.empty((0,), dtype=np.float32)
            ptr, size = context_wrapper.getBatchPrimitiveSolidFractions(self.context, uuid)
            if size == 0 or not ptr:
                return np.empty((0,), dtype=np.float32)
            return np.ctypeslib.as_array(ptr, shape=(size,)).copy()
        return context_wrapper.getPrimitiveSolidFraction(self.context, uuid)

    def overridePrimitiveTextureColor(self, uuid: int) -> None:
        """Override texture color with constant RGB color for a primitive.

        Args:
            uuid: UUID of the primitive
        """
        self._check_context_available()
        context_wrapper.overridePrimitiveTextureColor(self.context, uuid)

    def usePrimitiveTextureColor(self, uuid: int) -> None:
        """Use texture map color instead of constant RGB for a primitive.

        Args:
            uuid: UUID of the primitive
        """
        self._check_context_available()
        context_wrapper.usePrimitiveTextureColor(self.context, uuid)

    def isPrimitiveTextureColorOverridden(self, uuid: int) -> bool:
        """Check if primitive texture color is overridden.

        Args:
            uuid: UUID of the primitive

        Returns:
            True if texture color is overridden with constant RGB
        """
        self._check_context_available()
        return context_wrapper.isPrimitiveTextureColorOverridden(self.context, uuid)

    # =========================================================================
    # Convenience Methods (getAll*)
    # =========================================================================

    def getAllPrimitiveNormals(self) -> 'np.ndarray':
        """Get normals for all primitives. Returns ndarray of shape (N, 3)."""
        return self.getPrimitiveNormal(self.getAllUUIDs())

    def getAllPrimitiveColors(self) -> 'np.ndarray':
        """Get colors for all primitives. Returns ndarray of shape (N, 3)."""
        return self.getPrimitiveColor(self.getAllUUIDs())

    def getAllPrimitiveAreas(self) -> 'np.ndarray':
        """Get areas for all primitives. Returns ndarray of shape (N,)."""
        return self.getPrimitiveArea(self.getAllUUIDs())

    def getAllPrimitiveTypes(self) -> 'np.ndarray':
        """Get types for all primitives. Returns ndarray of shape (N,) uint32."""
        return self.getPrimitiveType(self.getAllUUIDs())

    def getAllPrimitiveSolidFractions(self) -> 'np.ndarray':
        """Get solid fractions for all primitives. Returns ndarray of shape (N,)."""
        return self.getPrimitiveSolidFraction(self.getAllUUIDs())

    def getAllPrimitiveVertices(self):
        """Get vertices for all primitives. Returns (flat_data, offsets) tuple."""
        return self.getPrimitiveVertices(self.getAllUUIDs())

    def getAllPrimitiveTextureFiles(self) -> List[str]:
        """Get texture files for all primitives. Returns list of strings."""
        return self.getPrimitiveTextureFile(self.getAllUUIDs())

    def getAllPrimitiveMaterialLabels(self) -> List[str]:
        """Get material labels for all primitives. Returns list of strings."""
        return self.getPrimitiveMaterialLabel(self.getAllUUIDs())

    # ==================== Visibility Methods ====================

    def hidePrimitive(self, uuids_or_uuid) -> None:
        """Hide one or more primitives. Hidden primitives are excluded from getAllUUIDs().

        Args:
            uuids_or_uuid: Single UUID (int) or list of UUIDs to hide.
        """
        if isinstance(uuids_or_uuid, (list, tuple)):
            context_wrapper.hidePrimitivesWrapper(self.context, list(uuids_or_uuid))
        else:
            context_wrapper.hidePrimitiveWrapper(self.context, uuids_or_uuid)

    def showPrimitive(self, uuids_or_uuid) -> None:
        """Show one or more previously hidden primitives.

        Args:
            uuids_or_uuid: Single UUID (int) or list of UUIDs to show.
        """
        if isinstance(uuids_or_uuid, (list, tuple)):
            context_wrapper.showPrimitivesWrapper(self.context, list(uuids_or_uuid))
        else:
            context_wrapper.showPrimitiveWrapper(self.context, uuids_or_uuid)

    def isPrimitiveHidden(self, uuid: int) -> bool:
        """Check if a primitive is hidden.

        Args:
            uuid: UUID of the primitive.

        Returns:
            True if the primitive is hidden.
        """
        return context_wrapper.isPrimitiveHiddenWrapper(self.context, uuid)

    def hideObject(self, objids_or_objid) -> None:
        """Hide one or more compound objects (and all their primitives).

        Args:
            objids_or_objid: Single object ID (int) or list of object IDs to hide.
        """
        if isinstance(objids_or_objid, (list, tuple)):
            context_wrapper.hideObjectsWrapper(self.context, list(objids_or_objid))
        else:
            context_wrapper.hideObjectWrapper(self.context, objids_or_objid)

    def showObject(self, objids_or_objid) -> None:
        """Show one or more previously hidden compound objects.

        Args:
            objids_or_objid: Single object ID (int) or list of object IDs to show.
        """
        if isinstance(objids_or_objid, (list, tuple)):
            context_wrapper.showObjectsWrapper(self.context, list(objids_or_objid))
        else:
            context_wrapper.showObjectWrapper(self.context, objids_or_objid)

    def isObjectHidden(self, objID: int) -> bool:
        """Check if a compound object is hidden.

        Args:
            objID: Object ID.

        Returns:
            True if the object is hidden.
        """
        return context_wrapper.isObjectHiddenWrapper(self.context, objID)

    # ==================== Object Data Methods ====================

    def setObjectDataInt(self, objids_or_objid, label: str, value: int) -> None:
        """Set object data as signed 32-bit integer for one or multiple objects."""
        if isinstance(objids_or_objid, (list, tuple)):
            context_wrapper.setBroadcastObjectDataInt(self.context, objids_or_objid, label, value)
        else:
            context_wrapper.setObjectDataInt(self.context, objids_or_objid, label, value)

    def setObjectDataUInt(self, objids_or_objid, label: str, value: int) -> None:
        """Set object data as unsigned 32-bit integer for one or multiple objects."""
        if isinstance(objids_or_objid, (list, tuple)):
            context_wrapper.setBroadcastObjectDataUInt(self.context, objids_or_objid, label, value)
        else:
            context_wrapper.setObjectDataUInt(self.context, objids_or_objid, label, value)

    def setObjectDataFloat(self, objids_or_objid, label: str, value: float) -> None:
        """Set object data as 32-bit float for one or multiple objects."""
        if isinstance(objids_or_objid, (list, tuple)):
            context_wrapper.setBroadcastObjectDataFloat(self.context, objids_or_objid, label, value)
        else:
            context_wrapper.setObjectDataFloat(self.context, objids_or_objid, label, value)

    def setObjectDataDouble(self, objids_or_objid, label: str, value: float) -> None:
        """Set object data as 64-bit double for one or multiple objects."""
        if isinstance(objids_or_objid, (list, tuple)):
            context_wrapper.setBroadcastObjectDataDouble(self.context, objids_or_objid, label, value)
        else:
            context_wrapper.setObjectDataDouble(self.context, objids_or_objid, label, value)

    def setObjectDataString(self, objids_or_objid, label: str, value: str) -> None:
        """Set object data as string for one or multiple objects."""
        if isinstance(objids_or_objid, (list, tuple)):
            context_wrapper.setBroadcastObjectDataString(self.context, objids_or_objid, label, value)
        else:
            context_wrapper.setObjectDataString(self.context, objids_or_objid, label, value)

    def setObjectDataVec2(self, objids_or_objid, label: str, x_or_vec, y: float = None) -> None:
        """Set object data as vec2. Accepts vec2 object or x,y components."""
        if hasattr(x_or_vec, 'x') and y is None:
            x, y = x_or_vec.x, x_or_vec.y
        else:
            x = x_or_vec
        if isinstance(objids_or_objid, (list, tuple)):
            context_wrapper.setBroadcastObjectDataVec2(self.context, objids_or_objid, label, x, y)
        else:
            context_wrapper.setObjectDataVec2(self.context, objids_or_objid, label, x, y)

    def setObjectDataVec3(self, objids_or_objid, label: str, x_or_vec, y: float = None, z: float = None) -> None:
        """Set object data as vec3. Accepts vec3 object or x,y,z components."""
        if hasattr(x_or_vec, 'x') and y is None:
            x, y, z = x_or_vec.x, x_or_vec.y, x_or_vec.z
        else:
            x = x_or_vec
        if isinstance(objids_or_objid, (list, tuple)):
            context_wrapper.setBroadcastObjectDataVec3(self.context, objids_or_objid, label, x, y, z)
        else:
            context_wrapper.setObjectDataVec3(self.context, objids_or_objid, label, x, y, z)

    def setObjectDataVec4(self, objids_or_objid, label: str, x_or_vec, y: float = None, z: float = None, w: float = None) -> None:
        """Set object data as vec4. Accepts vec4 object or x,y,z,w components."""
        if hasattr(x_or_vec, 'x') and y is None:
            x, y, z, w = x_or_vec.x, x_or_vec.y, x_or_vec.z, x_or_vec.w
        else:
            x = x_or_vec
        if isinstance(objids_or_objid, (list, tuple)):
            context_wrapper.setBroadcastObjectDataVec4(self.context, objids_or_objid, label, x, y, z, w)
        else:
            context_wrapper.setObjectDataVec4(self.context, objids_or_objid, label, x, y, z, w)

    def setObjectDataInt2(self, objids_or_objid, label: str, x_or_vec, y: int = None) -> None:
        """Set object data as int2. Accepts int2 object or x,y components."""
        if hasattr(x_or_vec, 'x') and y is None:
            x, y = x_or_vec.x, x_or_vec.y
        else:
            x = x_or_vec
        if isinstance(objids_or_objid, (list, tuple)):
            context_wrapper.setBroadcastObjectDataInt2(self.context, objids_or_objid, label, x, y)
        else:
            context_wrapper.setObjectDataInt2(self.context, objids_or_objid, label, x, y)

    def setObjectDataInt3(self, objids_or_objid, label: str, x_or_vec, y: int = None, z: int = None) -> None:
        """Set object data as int3. Accepts int3 object or x,y,z components."""
        if hasattr(x_or_vec, 'x') and y is None:
            x, y, z = x_or_vec.x, x_or_vec.y, x_or_vec.z
        else:
            x = x_or_vec
        if isinstance(objids_or_objid, (list, tuple)):
            context_wrapper.setBroadcastObjectDataInt3(self.context, objids_or_objid, label, x, y, z)
        else:
            context_wrapper.setObjectDataInt3(self.context, objids_or_objid, label, x, y, z)

    def setObjectDataInt4(self, objids_or_objid, label: str, x_or_vec, y: int = None, z: int = None, w: int = None) -> None:
        """Set object data as int4. Accepts int4 object or x,y,z,w components."""
        if hasattr(x_or_vec, 'x') and y is None:
            x, y, z, w = x_or_vec.x, x_or_vec.y, x_or_vec.z, x_or_vec.w
        else:
            x = x_or_vec
        if isinstance(objids_or_objid, (list, tuple)):
            context_wrapper.setBroadcastObjectDataInt4(self.context, objids_or_objid, label, x, y, z, w)
        else:
            context_wrapper.setObjectDataInt4(self.context, objids_or_objid, label, x, y, z, w)

    def getObjectData(self, objID: int, label: str, data_type: type = None):
        """Get object data with optional type specification. Auto-detects type if not specified."""
        if data_type is None:
            return context_wrapper.getObjectDataAuto(self.context, objID, label)
        if data_type == int:
            return context_wrapper.getObjectDataInt(self.context, objID, label)
        elif data_type == float:
            return context_wrapper.getObjectDataFloat(self.context, objID, label)
        elif data_type == str:
            return context_wrapper.getObjectDataString(self.context, objID, label)
        elif data_type == vec3:
            coords = context_wrapper.getObjectDataVec3(self.context, objID, label)
            return vec3(coords[0], coords[1], coords[2])
        elif data_type == vec2:
            coords = context_wrapper.getObjectDataVec2(self.context, objID, label)
            return vec2(coords[0], coords[1])
        elif data_type == vec4:
            coords = context_wrapper.getObjectDataVec4(self.context, objID, label)
            return vec4(coords[0], coords[1], coords[2], coords[3])
        elif data_type == int2:
            coords = context_wrapper.getObjectDataInt2(self.context, objID, label)
            return int2(coords[0], coords[1])
        elif data_type == int3:
            coords = context_wrapper.getObjectDataInt3(self.context, objID, label)
            return int3(coords[0], coords[1], coords[2])
        elif data_type == int4:
            coords = context_wrapper.getObjectDataInt4(self.context, objID, label)
            return int4(coords[0], coords[1], coords[2], coords[3])
        elif data_type == "uint":
            return context_wrapper.getObjectDataUInt(self.context, objID, label)
        elif data_type == "double":
            return context_wrapper.getObjectDataDouble(self.context, objID, label)
        else:
            raise ValueError(f"Unsupported object data type: {data_type}")

    def getObjectDataFloat(self, objID: int, label: str) -> float:
        """Get float object data."""
        return context_wrapper.getObjectDataFloat(self.context, objID, label)

    def getObjectDataInt(self, objID: int, label: str) -> int:
        """Get int object data."""
        return context_wrapper.getObjectDataInt(self.context, objID, label)

    def getObjectDataString(self, objID: int, label: str) -> str:
        """Get string object data."""
        return context_wrapper.getObjectDataString(self.context, objID, label)

    def getObjectDataType(self, objID: int, label: str) -> int:
        """Get the HeliosDataType enum for object data."""
        return context_wrapper.getObjectDataTypeWrapper(self.context, objID, label)

    def getObjectDataSize(self, objID: int, label: str) -> int:
        """Get the size of object data array."""
        return context_wrapper.getObjectDataSizeWrapper(self.context, objID, label)

    def doesObjectDataExist(self, objID: int, label: str) -> bool:
        """Check if object data exists."""
        return context_wrapper.doesObjectDataExistWrapper(self.context, objID, label)

    def clearObjectData(self, objids_or_objid, label: str) -> None:
        """Clear object data. Accepts single ID or list."""
        if isinstance(objids_or_objid, (list, tuple)):
            context_wrapper.clearObjectDataBatchWrapper(self.context, objids_or_objid, label)
        else:
            context_wrapper.clearObjectDataWrapper(self.context, objids_or_objid, label)

    def listObjectData(self, objID: int) -> List[str]:
        """List all data labels on a specific object."""
        return context_wrapper.listObjectDataWrapper(self.context, objID)

    def listAllObjectDataLabels(self) -> List[str]:
        """List all object data labels in context."""
        return context_wrapper.listAllObjectDataLabelsWrapper(self.context)

    def duplicateObjectData(self, objID: int, old_label: str, new_label: str) -> None:
        """Copy object data to a new label."""
        context_wrapper.duplicateObjectDataWrapper(self.context, objID, old_label, new_label)

    def renameObjectData(self, objID: int, old_label: str, new_label: str) -> None:
        """Rename an object data label."""
        context_wrapper.renameObjectDataWrapper(self.context, objID, old_label, new_label)

    def filterObjectsByData(self, objIDs: List[int], label: str, value, comparator: str = "=") -> List[int]:
        """Filter objects by data value. Auto-dispatches based on value type."""
        if isinstance(value, str):
            return context_wrapper.filterObjectsByDataStringWrapper(self.context, objIDs, label, value)
        elif isinstance(value, float):
            return context_wrapper.filterObjectsByDataFloatWrapper(self.context, objIDs, label, value, comparator)
        elif isinstance(value, int):
            return context_wrapper.filterObjectsByDataIntWrapper(self.context, objIDs, label, value, comparator)
        else:
            raise ValueError(f"Unsupported filter value type: {type(value).__name__}")

    # ==================== Global Data Methods ====================

    def setGlobalDataInt(self, label: str, value: int) -> None:
        """Set global data as signed 32-bit integer."""
        context_wrapper.setGlobalDataInt(self.context, label, value)

    def setGlobalDataUInt(self, label: str, value: int) -> None:
        """Set global data as unsigned 32-bit integer."""
        context_wrapper.setGlobalDataUInt(self.context, label, value)

    def setGlobalDataFloat(self, label: str, value: float) -> None:
        """Set global data as 32-bit float."""
        context_wrapper.setGlobalDataFloat(self.context, label, value)

    def setGlobalDataDouble(self, label: str, value: float) -> None:
        """Set global data as 64-bit double."""
        context_wrapper.setGlobalDataDouble(self.context, label, value)

    def setGlobalDataString(self, label: str, value: str) -> None:
        """Set global data as string."""
        context_wrapper.setGlobalDataString(self.context, label, value)

    def setGlobalDataVec2(self, label: str, x_or_vec, y: float = None) -> None:
        """Set global data as vec2."""
        if hasattr(x_or_vec, 'x') and y is None:
            x, y = x_or_vec.x, x_or_vec.y
        else:
            x = x_or_vec
        context_wrapper.setGlobalDataVec2(self.context, label, x, y)

    def setGlobalDataVec3(self, label: str, x_or_vec, y: float = None, z: float = None) -> None:
        """Set global data as vec3."""
        if hasattr(x_or_vec, 'x') and y is None:
            x, y, z = x_or_vec.x, x_or_vec.y, x_or_vec.z
        else:
            x = x_or_vec
        context_wrapper.setGlobalDataVec3(self.context, label, x, y, z)

    def setGlobalDataVec4(self, label: str, x_or_vec, y: float = None, z: float = None, w: float = None) -> None:
        """Set global data as vec4."""
        if hasattr(x_or_vec, 'x') and y is None:
            x, y, z, w = x_or_vec.x, x_or_vec.y, x_or_vec.z, x_or_vec.w
        else:
            x = x_or_vec
        context_wrapper.setGlobalDataVec4(self.context, label, x, y, z, w)

    def setGlobalDataInt2(self, label: str, x_or_vec, y: int = None) -> None:
        """Set global data as int2."""
        if hasattr(x_or_vec, 'x') and y is None:
            x, y = x_or_vec.x, x_or_vec.y
        else:
            x = x_or_vec
        context_wrapper.setGlobalDataInt2(self.context, label, x, y)

    def setGlobalDataInt3(self, label: str, x_or_vec, y: int = None, z: int = None) -> None:
        """Set global data as int3."""
        if hasattr(x_or_vec, 'x') and y is None:
            x, y, z = x_or_vec.x, x_or_vec.y, x_or_vec.z
        else:
            x = x_or_vec
        context_wrapper.setGlobalDataInt3(self.context, label, x, y, z)

    def setGlobalDataInt4(self, label: str, x_or_vec, y: int = None, z: int = None, w: int = None) -> None:
        """Set global data as int4."""
        if hasattr(x_or_vec, 'x') and y is None:
            x, y, z, w = x_or_vec.x, x_or_vec.y, x_or_vec.z, x_or_vec.w
        else:
            x = x_or_vec
        context_wrapper.setGlobalDataInt4(self.context, label, x, y, z, w)

    def getGlobalData(self, label: str, data_type: type = None):
        """Get global data with optional type specification. Auto-detects type if not specified."""
        if data_type is None:
            return context_wrapper.getGlobalDataAuto(self.context, label)
        if data_type == int:
            return context_wrapper.getGlobalDataInt(self.context, label)
        elif data_type == float:
            return context_wrapper.getGlobalDataFloat(self.context, label)
        elif data_type == str:
            return context_wrapper.getGlobalDataString(self.context, label)
        elif data_type == vec3:
            coords = context_wrapper.getGlobalDataVec3(self.context, label)
            return vec3(coords[0], coords[1], coords[2])
        elif data_type == vec2:
            coords = context_wrapper.getGlobalDataVec2(self.context, label)
            return vec2(coords[0], coords[1])
        elif data_type == vec4:
            coords = context_wrapper.getGlobalDataVec4(self.context, label)
            return vec4(coords[0], coords[1], coords[2], coords[3])
        elif data_type == int2:
            coords = context_wrapper.getGlobalDataInt2(self.context, label)
            return int2(coords[0], coords[1])
        elif data_type == int3:
            coords = context_wrapper.getGlobalDataInt3(self.context, label)
            return int3(coords[0], coords[1], coords[2])
        elif data_type == int4:
            coords = context_wrapper.getGlobalDataInt4(self.context, label)
            return int4(coords[0], coords[1], coords[2], coords[3])
        elif data_type == "uint":
            return context_wrapper.getGlobalDataUInt(self.context, label)
        elif data_type == "double":
            return context_wrapper.getGlobalDataDouble(self.context, label)
        else:
            raise ValueError(f"Unsupported global data type: {data_type}")

    def getGlobalDataFloat(self, label: str) -> float:
        """Get float global data."""
        return context_wrapper.getGlobalDataFloat(self.context, label)

    def getGlobalDataInt(self, label: str) -> int:
        """Get int global data."""
        return context_wrapper.getGlobalDataInt(self.context, label)

    def getGlobalDataString(self, label: str) -> str:
        """Get string global data."""
        return context_wrapper.getGlobalDataString(self.context, label)

    def getGlobalDataType(self, label: str) -> int:
        """Get the HeliosDataType enum for global data."""
        return context_wrapper.getGlobalDataTypeWrapper(self.context, label)

    def getGlobalDataSize(self, label: str) -> int:
        """Get the size of global data array."""
        return context_wrapper.getGlobalDataSizeWrapper(self.context, label)

    def doesGlobalDataExist(self, label: str) -> bool:
        """Check if global data exists."""
        return context_wrapper.doesGlobalDataExistWrapper(self.context, label)

    def clearGlobalData(self, label: str) -> None:
        """Clear global data."""
        context_wrapper.clearGlobalDataWrapper(self.context, label)

    def renameGlobalData(self, old_label: str, new_label: str) -> None:
        """Rename a global data label."""
        context_wrapper.renameGlobalDataWrapper(self.context, old_label, new_label)

    def duplicateGlobalData(self, old_label: str, new_label: str) -> None:
        """Duplicate global data to a new label."""
        context_wrapper.duplicateGlobalDataWrapper(self.context, old_label, new_label)

    def listGlobalData(self) -> List[str]:
        """List all global data labels."""
        return context_wrapper.listGlobalDataWrapper(self.context)

    def incrementGlobalData(self, label: str, increment) -> None:
        """Increment global data. Auto-dispatches based on increment type."""
        if isinstance(increment, float):
            context_wrapper.incrementGlobalDataFloatWrapper(self.context, label, increment)
        elif isinstance(increment, int):
            context_wrapper.incrementGlobalDataIntWrapper(self.context, label, increment)
        else:
            raise ValueError(f"Unsupported increment type: {type(increment).__name__}")

    # ==================== Primitive Data Statistics & Filtering ====================

    def calculatePrimitiveDataMean(self, uuids: List[int], label: str, return_type: type = float):
        """Calculate arithmetic mean of primitive data across UUIDs.

        Args:
            uuids: List of primitive UUIDs.
            label: Data label.
            return_type: float (default), "double", or vec3.
        """
        if return_type == float:
            return context_wrapper.calculatePrimitiveDataMeanFloatWrapper(self.context, uuids, label)
        elif return_type == "double":
            return context_wrapper.calculatePrimitiveDataMeanDoubleWrapper(self.context, uuids, label)
        elif return_type == vec3:
            coords = context_wrapper.calculatePrimitiveDataMeanVec3Wrapper(self.context, uuids, label)
            return vec3(coords[0], coords[1], coords[2])
        else:
            raise ValueError(f"Unsupported return type: {return_type}")

    def calculatePrimitiveDataAreaWeightedMean(self, uuids: List[int], label: str, return_type: type = float):
        """Calculate area-weighted mean of primitive data."""
        if return_type == float:
            return context_wrapper.calculatePrimitiveDataAreaWeightedMeanFloatWrapper(self.context, uuids, label)
        else:
            raise ValueError(f"Unsupported return type: {return_type}")

    def calculatePrimitiveDataSum(self, uuids: List[int], label: str, return_type: type = float):
        """Calculate sum of primitive data across UUIDs."""
        if return_type == float:
            return context_wrapper.calculatePrimitiveDataSumFloatWrapper(self.context, uuids, label)
        elif return_type == "double":
            return context_wrapper.calculatePrimitiveDataSumDoubleWrapper(self.context, uuids, label)
        else:
            raise ValueError(f"Unsupported return type: {return_type}")

    def calculatePrimitiveDataAreaWeightedSum(self, uuids: List[int], label: str, return_type: type = float):
        """Calculate area-weighted sum of primitive data."""
        if return_type == float:
            return context_wrapper.calculatePrimitiveDataAreaWeightedSumFloatWrapper(self.context, uuids, label)
        else:
            raise ValueError(f"Unsupported return type: {return_type}")

    def scalePrimitiveData(self, uuids_or_label, label_or_factor, factor=None) -> None:
        """Scale primitive data by a factor.

        Overloads:
            scalePrimitiveData(uuids, label, factor) - scale for specific UUIDs
            scalePrimitiveData(label, factor) - scale for ALL primitives
        """
        if isinstance(uuids_or_label, str):
            context_wrapper.scalePrimitiveDataAllWrapper(self.context, uuids_or_label, label_or_factor)
        else:
            context_wrapper.scalePrimitiveDataWithUUIDsWrapper(self.context, uuids_or_label, label_or_factor, factor)

    def incrementPrimitiveData(self, uuids: List[int], label: str, increment) -> None:
        """Increment primitive data. Auto-dispatches based on increment type."""
        if isinstance(increment, float):
            context_wrapper.incrementPrimitiveDataFloatWrapper(self.context, uuids, label, increment)
        elif isinstance(increment, int):
            context_wrapper.incrementPrimitiveDataIntWrapper(self.context, uuids, label, increment)
        else:
            raise ValueError(f"Unsupported increment type: {type(increment).__name__}")

    def aggregatePrimitiveDataSum(self, uuids: List[int], labels: List[str], result_label: str) -> None:
        """Sum multiple primitive data fields into a new field."""
        context_wrapper.aggregatePrimitiveDataSumWrapper(self.context, uuids, labels, result_label)

    def aggregatePrimitiveDataProduct(self, uuids: List[int], labels: List[str], result_label: str) -> None:
        """Multiply multiple primitive data fields into a new field."""
        context_wrapper.aggregatePrimitiveDataProductWrapper(self.context, uuids, labels, result_label)

    def sumPrimitiveSurfaceArea(self, uuids: List[int]) -> float:
        """Calculate total one-sided surface area for a set of primitives."""
        return context_wrapper.sumPrimitiveSurfaceAreaWrapper(self.context, uuids)

    def filterPrimitivesByData(self, uuids: List[int], label: str, value, comparator: str = "=") -> List[int]:
        """Filter primitives by data value. Auto-dispatches based on value type.

        Args:
            uuids: UUIDs to filter.
            label: Data label to compare.
            value: Filter value (float, int, or str).
            comparator: Comparison operator ("=", "<", ">", "<=", ">="). Not used for strings.
        """
        if isinstance(value, str):
            return context_wrapper.filterPrimitivesByDataStringWrapper(self.context, uuids, label, value)
        elif isinstance(value, float):
            return context_wrapper.filterPrimitivesByDataFloatWrapper(self.context, uuids, label, value, comparator)
        elif isinstance(value, int):
            return context_wrapper.filterPrimitivesByDataIntWrapper(self.context, uuids, label, value, comparator)
        else:
            raise ValueError(f"Unsupported filter value type: {type(value).__name__}")

    # ==================== Object Geometry Queries ====================

    def getObjectType(self, objID: int) -> int:
        """Return the integer-coded `helios::ObjectType` of a compound object.

        Values follow the C++ `helios::ObjectType` enum
        (0=tile, 1=sphere, 2=tube, 3=box, 4=disk, 5=polymesh, 6=cone).
        """
        self._check_context_available()
        return context_wrapper.getObjectTypeWrapper(self.context, objID)

    def getObjectCenter(self, objID: int) -> vec3:
        self._check_context_available()
        x, y, z = context_wrapper.getObjectCenterWrapper(self.context, objID)
        return vec3(x, y, z)

    def getObjectBoundingBox(self, objIDs):
        """Get axis-aligned bounding box for one object or a list of objects.

        Args:
            objIDs: Single object ID (int) or list of object IDs.

        Returns:
            Tuple of (min_corner: vec3, max_corner: vec3).
        """
        self._check_context_available()
        if isinstance(objIDs, (list, tuple)):
            mn, mx = context_wrapper.getObjectBoundingBoxBatchWrapper(self.context, list(objIDs))
        else:
            mn, mx = context_wrapper.getObjectBoundingBoxWrapper(self.context, objIDs)
        return (vec3(mn[0], mn[1], mn[2]), vec3(mx[0], mx[1], mx[2]))

    def getObjectPrimitiveUUIDs(self, objIDs) -> List[int]:
        """Get flattened primitive UUIDs for one object, a list of objects, or a list-of-lists.

        Args:
            objIDs: int, List[int], or List[List[int]].

        Returns:
            Flat list of primitive UUIDs (union across all objects).
        """
        self._check_context_available()
        if isinstance(objIDs, (list, tuple)) and objIDs and isinstance(objIDs[0], (list, tuple)):
            return context_wrapper.getObjectPrimitiveUUIDsNestedWrapper(self.context, [list(x) for x in objIDs])
        if isinstance(objIDs, (list, tuple)):
            return context_wrapper.getObjectPrimitiveUUIDsBatchWrapper(self.context, list(objIDs))
        return context_wrapper.getObjectPrimitiveUUIDs(self.context, int(objIDs))

    # Tile
    def getTileObjectAreaRatio(self, objIDs):
        """Get tile-object area ratio for one or multiple tile objects."""
        self._check_context_available()
        if isinstance(objIDs, (list, tuple)):
            return context_wrapper.getTileObjectAreaRatioBatchWrapper(self.context, list(objIDs))
        return context_wrapper.getTileObjectAreaRatioWrapper(self.context, objIDs)

    def getTileObjectCenter(self, objID: int) -> vec3:
        self._check_context_available()
        x, y, z = context_wrapper.getTileObjectCenterWrapper(self.context, objID)
        return vec3(x, y, z)

    def getTileObjectSize(self, objID: int) -> vec2:
        self._check_context_available()
        x, y = context_wrapper.getTileObjectSizeWrapper(self.context, objID)
        return vec2(x, y)

    def getTileObjectSubdivisionCount(self, objID: int) -> int2:
        self._check_context_available()
        x, y = context_wrapper.getTileObjectSubdivisionCountWrapper(self.context, objID)
        return int2(x, y)

    def getTileObjectNormal(self, objID: int) -> vec3:
        self._check_context_available()
        x, y, z = context_wrapper.getTileObjectNormalWrapper(self.context, objID)
        return vec3(x, y, z)

    def getTileObjectTextureUV(self, objID: int) -> List[vec2]:
        self._check_context_available()
        pairs = context_wrapper.getTileObjectTextureUVWrapper(self.context, objID)
        return [vec2(u, v) for u, v in pairs]

    def getTileObjectVertices(self, objID: int) -> List[vec3]:
        self._check_context_available()
        triples = context_wrapper.getTileObjectVerticesWrapper(self.context, objID)
        return [vec3(x, y, z) for x, y, z in triples]

    # Sphere
    def getSphereObjectCenter(self, objID: int) -> vec3:
        self._check_context_available()
        x, y, z = context_wrapper.getSphereObjectCenterWrapper(self.context, objID)
        return vec3(x, y, z)

    def getSphereObjectRadius(self, objID: int) -> vec3:
        """Get per-axis radii of a sphere object.

        Note: Helios spheres are spheroids with three independent radii (rx, ry, rz).
        Returns a vec3 (not a scalar).
        """
        self._check_context_available()
        x, y, z = context_wrapper.getSphereObjectRadiusWrapper(self.context, objID)
        return vec3(x, y, z)

    def getSphereObjectSubdivisionCount(self, objID: int) -> int:
        self._check_context_available()
        return context_wrapper.getSphereObjectSubdivisionCountWrapper(self.context, objID)

    def getSphereObjectVolume(self, objID: int) -> float:
        self._check_context_available()
        return context_wrapper.getSphereObjectVolumeWrapper(self.context, objID)

    # Box
    def getBoxObjectCenter(self, objID: int) -> vec3:
        self._check_context_available()
        x, y, z = context_wrapper.getBoxObjectCenterWrapper(self.context, objID)
        return vec3(x, y, z)

    def getBoxObjectSize(self, objID: int) -> vec3:
        self._check_context_available()
        x, y, z = context_wrapper.getBoxObjectSizeWrapper(self.context, objID)
        return vec3(x, y, z)

    def getBoxObjectSubdivisionCount(self, objID: int) -> int3:
        self._check_context_available()
        x, y, z = context_wrapper.getBoxObjectSubdivisionCountWrapper(self.context, objID)
        return int3(x, y, z)

    def getBoxObjectVolume(self, objID: int) -> float:
        self._check_context_available()
        return context_wrapper.getBoxObjectVolumeWrapper(self.context, objID)

    # Disk
    def getDiskObjectCenter(self, objID: int) -> vec3:
        self._check_context_available()
        x, y, z = context_wrapper.getDiskObjectCenterWrapper(self.context, objID)
        return vec3(x, y, z)

    def getDiskObjectSize(self, objID: int) -> vec2:
        self._check_context_available()
        x, y = context_wrapper.getDiskObjectSizeWrapper(self.context, objID)
        return vec2(x, y)

    def getDiskObjectSubdivisionCount(self, objID: int) -> int:
        self._check_context_available()
        return context_wrapper.getDiskObjectSubdivisionCountWrapper(self.context, objID)

    # Tube
    def getTubeObjectSubdivisionCount(self, objID: int) -> int:
        self._check_context_available()
        return context_wrapper.getTubeObjectSubdivisionCountWrapper(self.context, objID)

    def getTubeObjectNodeCount(self, objID: int) -> int:
        self._check_context_available()
        return context_wrapper.getTubeObjectNodeCountWrapper(self.context, objID)

    def getTubeObjectNodes(self, objID: int) -> List[vec3]:
        self._check_context_available()
        triples = context_wrapper.getTubeObjectNodesWrapper(self.context, objID)
        return [vec3(x, y, z) for x, y, z in triples]

    def getTubeObjectNodeRadii(self, objID: int) -> List[float]:
        self._check_context_available()
        return context_wrapper.getTubeObjectNodeRadiiWrapper(self.context, objID)

    def getTubeObjectNodeColors(self, objID: int) -> List[RGBcolor]:
        self._check_context_available()
        triples = context_wrapper.getTubeObjectNodeColorsWrapper(self.context, objID)
        return [RGBcolor(r, g, b) for r, g, b in triples]

    def getTubeObjectVolume(self, objID: int) -> float:
        self._check_context_available()
        return context_wrapper.getTubeObjectVolumeWrapper(self.context, objID)

    def getTubeObjectSegmentVolume(self, objID: int, segment_index: int) -> float:
        self._check_context_available()
        return context_wrapper.getTubeObjectSegmentVolumeWrapper(self.context, objID, segment_index)

    # Cone
    def getConeObjectSubdivisionCount(self, objID: int) -> int:
        self._check_context_available()
        return context_wrapper.getConeObjectSubdivisionCountWrapper(self.context, objID)

    def getConeObjectNodes(self, objID: int) -> List[vec3]:
        self._check_context_available()
        triples = context_wrapper.getConeObjectNodesWrapper(self.context, objID)
        return [vec3(x, y, z) for x, y, z in triples]

    def getConeObjectNodeRadii(self, objID: int) -> List[float]:
        self._check_context_available()
        return context_wrapper.getConeObjectNodeRadiiWrapper(self.context, objID)

    def getConeObjectNode(self, objID: int, number: int) -> vec3:
        self._check_context_available()
        x, y, z = context_wrapper.getConeObjectNodeWrapper(self.context, objID, number)
        return vec3(x, y, z)

    def getConeObjectNodeRadius(self, objID: int, number: int) -> float:
        self._check_context_available()
        return context_wrapper.getConeObjectNodeRadiusWrapper(self.context, objID, number)

    def getConeObjectAxisUnitVector(self, objID: int) -> vec3:
        self._check_context_available()
        x, y, z = context_wrapper.getConeObjectAxisUnitVectorWrapper(self.context, objID)
        return vec3(x, y, z)

    def getConeObjectLength(self, objID: int) -> float:
        self._check_context_available()
        return context_wrapper.getConeObjectLengthWrapper(self.context, objID)

    def getConeObjectVolume(self, objID: int) -> float:
        self._check_context_available()
        return context_wrapper.getConeObjectVolumeWrapper(self.context, objID)

    # ==================== Primitive Geometry Queries ====================

    def getPatchCenter(self, uuid: int) -> vec3:
        self._check_context_available()
        x, y, z = context_wrapper.getPatchCenterWrapper(self.context, uuid)
        return vec3(x, y, z)

    def getPatchSize(self, uuid: int) -> vec2:
        self._check_context_available()
        x, y = context_wrapper.getPatchSizeWrapper(self.context, uuid)
        return vec2(x, y)

    def getTriangleVertex(self, uuid: int, number: int) -> vec3:
        self._check_context_available()
        x, y, z = context_wrapper.getTriangleVertexWrapper(self.context, uuid, number)
        return vec3(x, y, z)

    def getVoxelCenter(self, uuid: int) -> vec3:
        self._check_context_available()
        x, y, z = context_wrapper.getVoxelCenterWrapper(self.context, uuid)
        return vec3(x, y, z)

    def getVoxelSize(self, uuid: int) -> vec3:
        self._check_context_available()
        x, y, z = context_wrapper.getVoxelSizeWrapper(self.context, uuid)
        return vec3(x, y, z)

    def getPatchCount(self, include_hidden: bool = True) -> int:
        self._check_context_available()
        return context_wrapper.getPatchCountWrapper(self.context, include_hidden)

    def getTriangleCount(self, include_hidden: bool = True) -> int:
        self._check_context_available()
        return context_wrapper.getTriangleCountWrapper(self.context, include_hidden)

    def getPrimitiveBoundingBox(self, uuids):
        """Get axis-aligned bounding box for one primitive or a list of primitives.

        Args:
            uuids: Single UUID (int) or list of UUIDs.

        Returns:
            Tuple of (min_corner: vec3, max_corner: vec3).
        """
        self._check_context_available()
        if isinstance(uuids, (list, tuple)):
            mn, mx = context_wrapper.getPrimitiveBoundingBoxBatchWrapper(self.context, list(uuids))
        else:
            mn, mx = context_wrapper.getPrimitiveBoundingBoxWrapper(self.context, uuids)
        return (vec3(mn[0], mn[1], mn[2]), vec3(mx[0], mx[1], mx[2]))

    # ==================== Primitive Color Mutation ====================

    def setPrimitiveColor(self, uuids, color) -> None:
        """Set the RGB or RGBA color of one primitive or a list of primitives.

        Args:
            uuids: Single UUID (int) or list of UUIDs.
            color: RGBcolor or RGBAcolor.
        """
        self._check_context_available()
        if isinstance(color, RGBAcolor):
            rgba = [color.r, color.g, color.b, color.a]
            if isinstance(uuids, (list, tuple)):
                context_wrapper.setPrimitiveColorRGBABatchWrapper(self.context, list(uuids), rgba)
            else:
                context_wrapper.setPrimitiveColorRGBAWrapper(self.context, uuids, rgba)
        elif isinstance(color, RGBcolor):
            rgb = [color.r, color.g, color.b]
            if isinstance(uuids, (list, tuple)):
                context_wrapper.setPrimitiveColorBatchWrapper(self.context, list(uuids), rgb)
            else:
                context_wrapper.setPrimitiveColorWrapper(self.context, uuids, rgb)
        else:
            raise ValueError(f"color must be RGBcolor or RGBAcolor, got {type(color).__name__}")

    # ==================== Primitive Data Introspection / Cleanup ====================

    def clearPrimitiveData(self, uuids, label: str) -> None:
        """Remove a named data field from one primitive or a list of primitives."""
        self._check_context_available()
        if isinstance(uuids, (list, tuple)):
            context_wrapper.clearPrimitiveDataByLabelBatchWrapper(self.context, list(uuids), label)
        else:
            context_wrapper.clearPrimitiveDataByLabelWrapper(self.context, uuids, label)

    def listPrimitiveData(self, uuid: int) -> List[str]:
        """List all data labels attached to a primitive."""
        self._check_context_available()
        return context_wrapper.listPrimitiveDataWrapper(self.context, uuid)

    # ==================== Domain Cropping ====================

    def cropDomainX(self, xbounds: vec2) -> None:
        self._check_context_available()
        if not isinstance(xbounds, vec2):
            raise ValueError(f"xbounds must be a vec2, got {type(xbounds).__name__}")
        context_wrapper.cropDomainXWrapper(self.context, xbounds.to_list())

    def cropDomainY(self, ybounds: vec2) -> None:
        self._check_context_available()
        if not isinstance(ybounds, vec2):
            raise ValueError(f"ybounds must be a vec2, got {type(ybounds).__name__}")
        context_wrapper.cropDomainYWrapper(self.context, ybounds.to_list())

    def cropDomainZ(self, zbounds: vec2) -> None:
        self._check_context_available()
        if not isinstance(zbounds, vec2):
            raise ValueError(f"zbounds must be a vec2, got {type(zbounds).__name__}")
        context_wrapper.cropDomainZWrapper(self.context, zbounds.to_list())

    def cropDomain(self, *args) -> Optional[List[int]]:
        """Crop the context domain to the given XYZ bounds.

        Two call forms:
            cropDomain(xbounds: vec2, ybounds: vec2, zbounds: vec2)
                -> crop ALL primitives; returns None.
            cropDomain(uuids: List[int], xbounds: vec2, ybounds: vec2, zbounds: vec2)
                -> crop only the given primitives; returns the list of primitives
                   that survived (in-bounds UUIDs). The input list is NOT mutated.
        """
        self._check_context_available()
        if len(args) == 3:
            xb, yb, zb = args
            for name, b in (("xbounds", xb), ("ybounds", yb), ("zbounds", zb)):
                if not isinstance(b, vec2):
                    raise ValueError(f"{name} must be a vec2, got {type(b).__name__}")
            context_wrapper.cropDomainXYZWrapper(self.context, xb.to_list(), yb.to_list(), zb.to_list())
            return None
        if len(args) == 4:
            uuids, xb, yb, zb = args
            if not isinstance(uuids, (list, tuple)):
                raise ValueError(f"uuids must be a list or tuple, got {type(uuids).__name__}")
            for name, b in (("xbounds", xb), ("ybounds", yb), ("zbounds", zb)):
                if not isinstance(b, vec2):
                    raise ValueError(f"{name} must be a vec2, got {type(b).__name__}")
            return context_wrapper.cropDomainByUUIDsWrapper(self.context, list(uuids), xb.to_list(), yb.to_list(), zb.to_list())
        raise TypeError(f"cropDomain() takes 3 or 4 positional arguments, got {len(args)}")

    # =========================================================================
    # Scalar Getters / Setters & List-of-String Getters
    # =========================================================================

    # ---- Existence / state queries ----

    def doesObjectExist(self, objID: int) -> bool:
        """Return True if a compound object with the given ID exists."""
        self._check_context_available()
        return context_wrapper.doesObjectExistWrapper(self.context, objID)

    def doesObjectContainPrimitive(self, objID: int, uuid: int) -> bool:
        """Return True if the given primitive UUID belongs to the given object."""
        self._check_context_available()
        return context_wrapper.doesObjectContainPrimitiveWrapper(self.context, objID, uuid)

    def doesMaterialDataExist(self, material_label: str, data_label: str) -> bool:
        """Return True if the named material has data stored under data_label."""
        self._check_context_available()
        return context_wrapper.doesMaterialDataExistWrapper(self.context, material_label, data_label)

    def objectHasTexture(self, objID: int) -> bool:
        """Return True if the compound object has a texture assigned."""
        self._check_context_available()
        return context_wrapper.objectHasTextureWrapper(self.context, objID)

    def isPrimitiveDirty(self, uuid: int) -> bool:
        """Return True if the primitive's geometry has been modified since the last clean mark."""
        self._check_context_available()
        return context_wrapper.isPrimitiveDirtyWrapper(self.context, uuid)

    def isObjectDataValueCachingEnabled(self, label: str) -> bool:
        """Return True if value caching is enabled for the given object-data label."""
        self._check_context_available()
        return context_wrapper.isObjectDataValueCachingEnabledWrapper(self.context, label)

    def isPrimitiveDataValueCachingEnabled(self, label: str) -> bool:
        """Return True if value caching is enabled for the given primitive-data label."""
        self._check_context_available()
        return context_wrapper.isPrimitiveDataValueCachingEnabledWrapper(self.context, label)

    def areObjectPrimitivesComplete(self, objID: int) -> bool:
        """Return True if all primitives originally belonging to this object still exist
        (i.e., none have been deleted)."""
        self._check_context_available()
        return context_wrapper.areObjectPrimitivesCompleteWrapper(self.context, objID)

    # ---- Numeric scalar getters ----

    def getJulianDate(self) -> int:
        """Get the current simulation date as Julian day (1-366)."""
        self._check_context_available()
        return context_wrapper.getJulianDateWrapper(self.context)

    def getMaterialCount(self) -> int:
        """Return the total number of materials registered in the context."""
        self._check_context_available()
        return context_wrapper.getMaterialCountWrapper(self.context)

    def getObjectArea(self, objID: int) -> float:
        """Return the total surface area (one-sided) of all primitives in the object."""
        self._check_context_available()
        return context_wrapper.getObjectAreaWrapper(self.context, objID)

    def getObjectPrimitiveCount(self, objID: int) -> int:
        """Return the number of primitives currently belonging to the object."""
        self._check_context_available()
        return context_wrapper.getObjectPrimitiveCountWrapper(self.context, objID)

    def getPolymeshObjectVolume(self, objID: int) -> float:
        """Return the enclosed volume of a polymesh object."""
        self._check_context_available()
        return context_wrapper.getPolymeshObjectVolumeWrapper(self.context, objID)

    def getMaterialIDFromLabel(self, material_label: str) -> int:
        """Look up a material ID from its human-readable label."""
        self._check_context_available()
        return context_wrapper.getMaterialIDFromLabelWrapper(self.context, material_label)

    def getPrimitiveMaterialID(self, uuid: int) -> int:
        """Return the material ID assigned to the given primitive."""
        self._check_context_available()
        return context_wrapper.getPrimitiveMaterialIDWrapper(self.context, uuid)

    def getGlobalDataVersion(self, label: str) -> int:
        """Return the version counter for a global data entry. Increments on each update;
        useful for cache invalidation."""
        self._check_context_available()
        return context_wrapper.getGlobalDataVersionWrapper(self.context, label)

    def getPrimitiveParentObjectID(self, uuid: int) -> int:
        """Return the ID of the compound object the primitive belongs to.

        Returns 0 if the primitive is not part of any compound object (the documented
        "no parent" sentinel). Raises ``HeliosRuntimeError`` if ``uuid`` does not exist.
        """
        self._check_context_available()
        return context_wrapper.getPrimitiveParentObjectIDWrapper(self.context, uuid)

    # ---- String / list-of-string getters ----

    def getObjectTextureFile(self, objID: int) -> str:
        """Return the filesystem path of the texture assigned to the object, or an
        empty string if no texture is assigned."""
        self._check_context_available()
        return context_wrapper.getObjectTextureFileWrapper(self.context, objID)

    def listAllPrimitiveDataLabels(self) -> List[str]:
        """Return the union of all primitive-data labels used across every primitive
        in the context."""
        self._check_context_available()
        return context_wrapper.listAllPrimitiveDataLabelsWrapper(self.context)

    def getLoadedXMLFiles(self) -> List[str]:
        """Return the list of XML file paths that have been loaded into this context."""
        self._check_context_available()
        return context_wrapper.getLoadedXMLFilesWrapper(self.context)

    # ---- Simple actions ----

    def printObjectInfo(self, objID: int) -> None:
        """Print summary info for the object to stdout (for debugging)."""
        self._check_context_available()
        context_wrapper.printObjectInfoWrapper(self.context, objID)

    def printPrimitiveInfo(self, uuid: int) -> None:
        """Print summary info for the primitive to stdout (for debugging)."""
        self._check_context_available()
        context_wrapper.printPrimitiveInfoWrapper(self.context, uuid)

    def enablePrimitiveDataValueCaching(self, label: str) -> None:
        """Enable value caching for the given primitive-data label. Required before
        using getUniquePrimitiveDataValues for that label."""
        self._check_context_available()
        context_wrapper.enablePrimitiveDataValueCachingWrapper(self.context, label)

    def disablePrimitiveDataValueCaching(self, label: str) -> None:
        """Disable value caching for the given primitive-data label."""
        self._check_context_available()
        context_wrapper.disablePrimitiveDataValueCachingWrapper(self.context, label)

    def enableObjectDataValueCaching(self, label: str) -> None:
        """Enable value caching for the given object-data label. Required before
        using getUniqueObjectDataValues for that label."""
        self._check_context_available()
        context_wrapper.enableObjectDataValueCachingWrapper(self.context, label)

    def disableObjectDataValueCaching(self, label: str) -> None:
        """Disable value caching for the given object-data label."""
        self._check_context_available()
        context_wrapper.disableObjectDataValueCachingWrapper(self.context, label)

    def setObjectDataFromPrimitiveDataMean(self, objID: int, label: str) -> None:
        """Compute the mean of the given primitive-data label across the object's
        primitives and store it as object data on the object itself under the
        same label."""
        self._check_context_available()
        context_wrapper.setObjectDataFromPrimitiveDataMeanWrapper(self.context, objID, label)

    def renameMaterial(self, old_label: str, new_label: str) -> None:
        """Rename an existing material."""
        self._check_context_available()
        context_wrapper.renameMaterialWrapper(self.context, old_label, new_label)

    def renamePrimitiveData(self, uuid: int, old_label: str, new_label: str) -> None:
        """Rename a primitive-data label on a single primitive."""
        self._check_context_available()
        context_wrapper.renamePrimitiveDataWrapper(self.context, uuid, old_label, new_label)

    def clearMaterialData(self, material_label: str, data_label: str) -> None:
        """Clear the named data entry on the given material."""
        self._check_context_available()
        context_wrapper.clearMaterialDataWrapper(self.context, material_label, data_label)

    # =========================================================================
    # Vector-return getters & geometry mutators
    # =========================================================================

    # ---- Vector<uint> queries ----

    def getDeletedUUIDs(self) -> List[int]:
        """Return the list of UUIDs that have been deleted from the context.

        These UUIDs are tombstoned and will not appear in getAllUUIDs(), but their
        IDs are tracked so they can be excluded from external references.
        """
        self._check_context_available()
        return context_wrapper.getDeletedUUIDsWrapper(self.context)

    def getDirtyUUIDs(self, include_deleted: bool = True) -> List[int]:
        """Return the list of UUIDs whose geometry has been modified since the last
        markGeometryClean call.

        Args:
            include_deleted: If True (default), include UUIDs that were deleted while
                dirty. If False, only return UUIDs that still exist.
        """
        self._check_context_available()
        return context_wrapper.getDirtyUUIDsWrapper(self.context, include_deleted)

    def getUniquePrimitiveParentObjectIDs(self, uuids: List[int],
                                          include_zero: bool = True) -> List[int]:
        """Return the unique set of compound-object IDs that the given primitives
        belong to.

        Args:
            uuids: List of primitive UUIDs to inspect.
            include_zero: If True (default), include the sentinel object ID 0
                (i.e., primitives with no parent object). If False, only return
                IDs of real compound objects.
        """
        self._check_context_available()
        if not isinstance(uuids, (list, tuple)):
            raise ValueError(f"uuids must be a list or tuple, got {type(uuids).__name__}")
        return context_wrapper.getUniquePrimitiveParentObjectIDsWrapper(
            self.context, list(uuids), include_zero
        )

    # ---- Object normal / origin ----

    def getObjectAverageNormal(self, objID: int) -> vec3:
        """Return the area-weighted average normal of all primitives in the object."""
        self._check_context_available()
        x, y, z = context_wrapper.getObjectAverageNormalWrapper(self.context, objID)
        return vec3(x, y, z)

    def setObjectAverageNormal(self, objID: int, origin: vec3, new_normal: vec3) -> None:
        """Rotate the object so its area-weighted average normal aligns with
        new_normal. The rotation is applied about the given origin point."""
        self._check_context_available()
        if not isinstance(origin, vec3):
            raise ValueError(f"origin must be a vec3, got {type(origin).__name__}")
        if not isinstance(new_normal, vec3):
            raise ValueError(f"new_normal must be a vec3, got {type(new_normal).__name__}")
        context_wrapper.setObjectAverageNormalWrapper(
            self.context, objID, origin.to_list(), new_normal.to_list()
        )

    def setObjectOrigin(self, objID: int, origin: vec3) -> None:
        """Translate the object so its origin is moved to the given point."""
        self._check_context_available()
        if not isinstance(origin, vec3):
            raise ValueError(f"origin must be a vec3, got {type(origin).__name__}")
        context_wrapper.setObjectOriginWrapper(self.context, objID, origin.to_list())

    # ---- Primitive azimuth / elevation ----

    def setPrimitiveAzimuth(self, uuid: int, origin: vec3, new_azimuth: float) -> None:
        """Rotate a single primitive about the given origin so its azimuth
        equals new_azimuth (radians)."""
        self._check_context_available()
        if not isinstance(origin, vec3):
            raise ValueError(f"origin must be a vec3, got {type(origin).__name__}")
        context_wrapper.setPrimitiveAzimuthWrapper(
            self.context, uuid, origin.to_list(), float(new_azimuth)
        )

    def setPrimitiveElevation(self, uuid: int, origin: vec3, new_elevation: float) -> None:
        """Rotate a single primitive about the given origin so its elevation
        equals new_elevation (radians)."""
        self._check_context_available()
        if not isinstance(origin, vec3):
            raise ValueError(f"origin must be a vec3, got {type(origin).__name__}")
        context_wrapper.setPrimitiveElevationWrapper(
            self.context, uuid, origin.to_list(), float(new_elevation)
        )

    # ---- Geometry mutators ----

    def setTriangleVertices(self, uuid: int, vertex0: vec3, vertex1: vec3, vertex2: vec3) -> None:
        """Replace the three vertices of an existing triangle primitive."""
        self._check_context_available()
        for name, v in (("vertex0", vertex0), ("vertex1", vertex1), ("vertex2", vertex2)):
            if not isinstance(v, vec3):
                raise ValueError(f"{name} must be a vec3, got {type(v).__name__}")
        context_wrapper.setTriangleVerticesWrapper(
            self.context, uuid, vertex0.to_list(), vertex1.to_list(), vertex2.to_list()
        )

    def setPrimitiveNormal(self, uuids_or_uuid, origin: vec3, new_normal: vec3) -> None:
        """Rotate one or more primitives so their normals align with new_normal.

        Accepts either a single UUID (int) or a list/tuple of UUIDs.
        The rotation is applied about the given origin point.
        """
        self._check_context_available()
        if not isinstance(origin, vec3):
            raise ValueError(f"origin must be a vec3, got {type(origin).__name__}")
        if not isinstance(new_normal, vec3):
            raise ValueError(f"new_normal must be a vec3, got {type(new_normal).__name__}")
        if isinstance(uuids_or_uuid, (list, tuple)):
            context_wrapper.setPrimitiveNormalBatchWrapper(
                self.context, list(uuids_or_uuid), origin.to_list(), new_normal.to_list()
            )
        else:
            context_wrapper.setPrimitiveNormalWrapper(
                self.context, uuids_or_uuid, origin.to_list(), new_normal.to_list()
            )

    def setPrimitiveParentObjectID(self, uuids_or_uuid, objID: int) -> None:
        """Reassign one or more primitives to belong to the given compound object.

        Accepts either a single UUID (int) or a list/tuple of UUIDs. Pass objID=0
        to detach primitive(s) from any object.
        """
        self._check_context_available()
        if isinstance(uuids_or_uuid, (list, tuple)):
            context_wrapper.setPrimitiveParentObjectIDBatchWrapper(
                self.context, list(uuids_or_uuid), int(objID)
            )
        else:
            context_wrapper.setPrimitiveParentObjectIDWrapper(
                self.context, int(uuids_or_uuid), int(objID)
            )

    # =========================================================================
    # Material data API + unique data values
    # =========================================================================

    # ---- Per-type explicit setMaterialData* methods ----
    # These mirror the existing setPrimitiveData<Type> family for parity.

    def setMaterialDataInt(self, material_label: str, data_label: str, value: int) -> None:
        """Set int data on a material. Affects all primitives that reference it."""
        self._check_context_available()
        context_wrapper.setMaterialDataIntWrapper(self.context, material_label, data_label, int(value))

    def setMaterialDataUInt(self, material_label: str, data_label: str, value: int) -> None:
        """Set unsigned int data on a material."""
        self._check_context_available()
        context_wrapper.setMaterialDataUIntWrapper(self.context, material_label, data_label, int(value))

    def setMaterialDataFloat(self, material_label: str, data_label: str, value: float) -> None:
        """Set float data on a material."""
        self._check_context_available()
        context_wrapper.setMaterialDataFloatWrapper(self.context, material_label, data_label, float(value))

    def setMaterialDataDouble(self, material_label: str, data_label: str, value: float) -> None:
        """Set double-precision float data on a material."""
        self._check_context_available()
        context_wrapper.setMaterialDataDoubleWrapper(self.context, material_label, data_label, float(value))

    def setMaterialDataString(self, material_label: str, data_label: str, value: str) -> None:
        """Set string data on a material."""
        self._check_context_available()
        context_wrapper.setMaterialDataStringWrapper(self.context, material_label, data_label, str(value))

    def setMaterialDataVec2(self, material_label: str, data_label: str, value: vec2) -> None:
        """Set vec2 data on a material."""
        self._check_context_available()
        if not isinstance(value, vec2):
            raise ValueError(f"value must be a vec2, got {type(value).__name__}")
        context_wrapper.setMaterialDataVec2Wrapper(self.context, material_label, data_label, value.x, value.y)

    def setMaterialDataVec3(self, material_label: str, data_label: str, value: vec3) -> None:
        """Set vec3 data on a material."""
        self._check_context_available()
        if not isinstance(value, vec3):
            raise ValueError(f"value must be a vec3, got {type(value).__name__}")
        context_wrapper.setMaterialDataVec3Wrapper(self.context, material_label, data_label, value.x, value.y, value.z)

    def setMaterialDataVec4(self, material_label: str, data_label: str, value: vec4) -> None:
        """Set vec4 data on a material."""
        self._check_context_available()
        if not isinstance(value, vec4):
            raise ValueError(f"value must be a vec4, got {type(value).__name__}")
        context_wrapper.setMaterialDataVec4Wrapper(self.context, material_label, data_label, value.x, value.y, value.z, value.w)

    def setMaterialDataInt2(self, material_label: str, data_label: str, value: int2) -> None:
        """Set int2 data on a material."""
        self._check_context_available()
        if not isinstance(value, int2):
            raise ValueError(f"value must be an int2, got {type(value).__name__}")
        context_wrapper.setMaterialDataInt2Wrapper(self.context, material_label, data_label, value.x, value.y)

    def setMaterialDataInt3(self, material_label: str, data_label: str, value: int3) -> None:
        """Set int3 data on a material."""
        self._check_context_available()
        if not isinstance(value, int3):
            raise ValueError(f"value must be an int3, got {type(value).__name__}")
        context_wrapper.setMaterialDataInt3Wrapper(self.context, material_label, data_label, value.x, value.y, value.z)

    def setMaterialDataInt4(self, material_label: str, data_label: str, value: int4) -> None:
        """Set int4 data on a material."""
        self._check_context_available()
        if not isinstance(value, int4):
            raise ValueError(f"value must be an int4, got {type(value).__name__}")
        context_wrapper.setMaterialDataInt4Wrapper(self.context, material_label, data_label, value.x, value.y, value.z, value.w)

    # ---- Per-type explicit getMaterialData* methods ----

    def getMaterialDataInt(self, material_label: str, data_label: str) -> int:
        self._check_context_available()
        return context_wrapper.getMaterialDataIntWrapper(self.context, material_label, data_label)

    def getMaterialDataUInt(self, material_label: str, data_label: str) -> int:
        self._check_context_available()
        return context_wrapper.getMaterialDataUIntWrapper(self.context, material_label, data_label)

    def getMaterialDataFloat(self, material_label: str, data_label: str) -> float:
        self._check_context_available()
        return context_wrapper.getMaterialDataFloatWrapper(self.context, material_label, data_label)

    def getMaterialDataDouble(self, material_label: str, data_label: str) -> float:
        self._check_context_available()
        return context_wrapper.getMaterialDataDoubleWrapper(self.context, material_label, data_label)

    def getMaterialDataString(self, material_label: str, data_label: str) -> str:
        self._check_context_available()
        return context_wrapper.getMaterialDataStringWrapper(self.context, material_label, data_label)

    def getMaterialDataVec2(self, material_label: str, data_label: str) -> vec2:
        self._check_context_available()
        x, y = context_wrapper.getMaterialDataVec2Wrapper(self.context, material_label, data_label)
        return vec2(x, y)

    def getMaterialDataVec3(self, material_label: str, data_label: str) -> vec3:
        self._check_context_available()
        x, y, z = context_wrapper.getMaterialDataVec3Wrapper(self.context, material_label, data_label)
        return vec3(x, y, z)

    def getMaterialDataVec4(self, material_label: str, data_label: str) -> vec4:
        self._check_context_available()
        x, y, z, w = context_wrapper.getMaterialDataVec4Wrapper(self.context, material_label, data_label)
        return vec4(x, y, z, w)

    def getMaterialDataInt2(self, material_label: str, data_label: str) -> int2:
        self._check_context_available()
        x, y = context_wrapper.getMaterialDataInt2Wrapper(self.context, material_label, data_label)
        return int2(x, y)

    def getMaterialDataInt3(self, material_label: str, data_label: str) -> int3:
        self._check_context_available()
        x, y, z = context_wrapper.getMaterialDataInt3Wrapper(self.context, material_label, data_label)
        return int3(x, y, z)

    def getMaterialDataInt4(self, material_label: str, data_label: str) -> int4:
        self._check_context_available()
        x, y, z, w = context_wrapper.getMaterialDataInt4Wrapper(self.context, material_label, data_label)
        return int4(x, y, z, w)

    def getMaterialDataType(self, material_label: str, data_label: str) -> int:
        """Return the HeliosDataType enum value for the given material data entry.

        Encoding (from Helios core): 0=INT, 1=UINT, 2=FLOAT, 3=DOUBLE,
        4=VEC2, 5=VEC3, 6=VEC4, 7=INT2, 8=INT3, 9=INT4, 10=STRING.
        """
        self._check_context_available()
        return context_wrapper.getMaterialDataTypeWrapper(self.context, material_label, data_label)

    # ---- Unified dispatch setMaterialData / getMaterialData ----

    def setMaterialData(self, material_label: str, data_label: str, value) -> None:
        """Set material data with type detection from the Python value.

        Dispatches to the correct typed setter based on ``isinstance`` of ``value``.
        For unambiguous numeric width control (e.g., uint vs int), call the
        per-type method directly (``setMaterialDataUInt``, etc.).
        """
        self._check_context_available()
        if isinstance(value, bool):
            # bool is a subclass of int in Python; route to int explicitly.
            context_wrapper.setMaterialDataIntWrapper(self.context, material_label, data_label, int(value))
        elif isinstance(value, int):
            context_wrapper.setMaterialDataIntWrapper(self.context, material_label, data_label, int(value))
        elif isinstance(value, float):
            context_wrapper.setMaterialDataFloatWrapper(self.context, material_label, data_label, float(value))
        elif isinstance(value, str):
            context_wrapper.setMaterialDataStringWrapper(self.context, material_label, data_label, value)
        elif isinstance(value, vec2):
            context_wrapper.setMaterialDataVec2Wrapper(self.context, material_label, data_label, value.x, value.y)
        elif isinstance(value, vec3):
            context_wrapper.setMaterialDataVec3Wrapper(self.context, material_label, data_label, value.x, value.y, value.z)
        elif isinstance(value, vec4):
            context_wrapper.setMaterialDataVec4Wrapper(self.context, material_label, data_label, value.x, value.y, value.z, value.w)
        elif isinstance(value, int2):
            context_wrapper.setMaterialDataInt2Wrapper(self.context, material_label, data_label, value.x, value.y)
        elif isinstance(value, int3):
            context_wrapper.setMaterialDataInt3Wrapper(self.context, material_label, data_label, value.x, value.y, value.z)
        elif isinstance(value, int4):
            context_wrapper.setMaterialDataInt4Wrapper(self.context, material_label, data_label, value.x, value.y, value.z, value.w)
        else:
            raise ValueError(
                f"Unsupported value type for setMaterialData: {type(value).__name__}. "
                f"Supported: int, float, str, vec2, vec3, vec4, int2, int3, int4. "
                f"For uint/double, call setMaterialDataUInt/Double directly."
            )

    def getMaterialData(self, material_label: str, data_label: str, data_type: type = None):
        """Get material data, auto-detecting the type from Helios storage if not specified.

        Args:
            material_label: Name of the material.
            data_label: Data entry label.
            data_type: Optional Python type (int, float, str, vec2, vec3, vec4, int2,
                int3, int4) or string ('uint', 'double'). If ``None``, the type is
                queried via getMaterialDataType and dispatched automatically.
        """
        self._check_context_available()
        if data_type is None:
            t = context_wrapper.getMaterialDataTypeWrapper(self.context, material_label, data_label)
            # Map HeliosDataType enum → typed call
            if t == 0:
                return context_wrapper.getMaterialDataIntWrapper(self.context, material_label, data_label)
            if t == 1:
                return context_wrapper.getMaterialDataUIntWrapper(self.context, material_label, data_label)
            if t == 2:
                return context_wrapper.getMaterialDataFloatWrapper(self.context, material_label, data_label)
            if t == 3:
                return context_wrapper.getMaterialDataDoubleWrapper(self.context, material_label, data_label)
            if t == 4:
                x, y = context_wrapper.getMaterialDataVec2Wrapper(self.context, material_label, data_label)
                return vec2(x, y)
            if t == 5:
                x, y, z = context_wrapper.getMaterialDataVec3Wrapper(self.context, material_label, data_label)
                return vec3(x, y, z)
            if t == 6:
                x, y, z, w = context_wrapper.getMaterialDataVec4Wrapper(self.context, material_label, data_label)
                return vec4(x, y, z, w)
            if t == 7:
                x, y = context_wrapper.getMaterialDataInt2Wrapper(self.context, material_label, data_label)
                return int2(x, y)
            if t == 8:
                x, y, z = context_wrapper.getMaterialDataInt3Wrapper(self.context, material_label, data_label)
                return int3(x, y, z)
            if t == 9:
                x, y, z, w = context_wrapper.getMaterialDataInt4Wrapper(self.context, material_label, data_label)
                return int4(x, y, z, w)
            if t == 10:
                return context_wrapper.getMaterialDataStringWrapper(self.context, material_label, data_label)
            raise ValueError(f"Unknown HeliosDataType code: {t}")

        # Explicit type dispatch
        if data_type == int:
            return self.getMaterialDataInt(material_label, data_label)
        if data_type == float:
            return self.getMaterialDataFloat(material_label, data_label)
        if data_type == str:
            return self.getMaterialDataString(material_label, data_label)
        if data_type == "uint":
            return self.getMaterialDataUInt(material_label, data_label)
        if data_type == "double":
            return self.getMaterialDataDouble(material_label, data_label)
        if data_type == vec2:
            return self.getMaterialDataVec2(material_label, data_label)
        if data_type == vec3:
            return self.getMaterialDataVec3(material_label, data_label)
        if data_type == vec4:
            return self.getMaterialDataVec4(material_label, data_label)
        if data_type == int2:
            return self.getMaterialDataInt2(material_label, data_label)
        if data_type == int3:
            return self.getMaterialDataInt3(material_label, data_label)
        if data_type == int4:
            return self.getMaterialDataInt4(material_label, data_label)
        raise ValueError(
            f"Unsupported material data type: {data_type}. Supported: int, float, str, "
            f"vec2, vec3, vec4, int2, int3, int4, 'uint', 'double'."
        )

    # ---- Unique data values ----

    def getUniquePrimitiveDataValues(self, label: str, dtype: type) -> List:
        """Return the unique values stored under ``label`` across all primitives.

        Requires value caching to be enabled for ``label`` first via
        ``enablePrimitiveDataValueCaching(label)``. Supported ``dtype`` values:
        ``int``, ``str``, or the string ``'uint'``.
        """
        self._check_context_available()
        if dtype == int:
            return context_wrapper.getUniquePrimitiveDataValuesIntWrapper(self.context, label)
        if dtype == "uint":
            return context_wrapper.getUniquePrimitiveDataValuesUIntWrapper(self.context, label)
        if dtype == str:
            return context_wrapper.getUniquePrimitiveDataValuesStringWrapper(self.context, label)
        raise ValueError(
            f"Unsupported dtype for getUniquePrimitiveDataValues: {dtype}. "
            f"Supported: int, str, 'uint'."
        )

    def getUniqueObjectDataValues(self, label: str, dtype: type) -> List:
        """Return the unique values stored under ``label`` across all compound objects.

        Requires value caching to be enabled for ``label`` first via
        ``enableObjectDataValueCaching(label)``. Supported ``dtype`` values:
        ``int``, ``str``, or the string ``'uint'``.
        """
        self._check_context_available()
        if dtype == int:
            return context_wrapper.getUniqueObjectDataValuesIntWrapper(self.context, label)
        if dtype == "uint":
            return context_wrapper.getUniqueObjectDataValuesUIntWrapper(self.context, label)
        if dtype == str:
            return context_wrapper.getUniqueObjectDataValuesStringWrapper(self.context, label)
        raise ValueError(
            f"Unsupported dtype for getUniqueObjectDataValues: {dtype}. "
            f"Supported: int, str, 'uint'."
        )

    # =========================================================================
    # 4x4 transformation matrices + domain bounds
    # =========================================================================

    @staticmethod
    def _marshal_mat4(value) -> List[float]:
        """Coerce a 4x4 transformation matrix input into a flat list of 16 floats.

        Accepts: numpy.ndarray of shape (4,4) or (16,), list/tuple of 16 floats,
        or nested list/tuple of shape (4,4). Helios stores transformation matrices
        in **row-major** order: T[i*4 + j] = element (i, j). A numpy ndarray of
        shape (4,4) maps directly via .ravel() since numpy is row-major by default.
        """
        # numpy ndarray fast path
        if isinstance(value, np.ndarray):
            if value.shape == (4, 4):
                return [float(v) for v in value.ravel().tolist()]
            if value.shape == (16,):
                return [float(v) for v in value.tolist()]
            raise ValueError(
                f"Matrix ndarray must have shape (4,4) or (16,), got {value.shape}"
            )
        # Nested list/tuple of shape (4,4)
        if isinstance(value, (list, tuple)) and len(value) == 4 and \
                all(isinstance(row, (list, tuple)) and len(row) == 4 for row in value):
            flat = []
            for row in value:
                flat.extend(float(v) for v in row)
            return flat
        # Flat list/tuple of 16 floats
        if isinstance(value, (list, tuple)) and len(value) == 16:
            return [float(v) for v in value]
        raise ValueError(
            f"Matrix must be a (4,4) ndarray, (16,) ndarray, list of 16 floats, "
            f"or nested 4x4 list. Got: {type(value).__name__}"
        )

    @staticmethod
    def _mat4_to_ndarray(flat: List[float]) -> 'np.ndarray':
        """Convert a flat list of 16 floats (row-major) to a (4,4) numpy ndarray."""
        return np.array(flat, dtype=np.float32).reshape((4, 4))

    # ---- Transformation matrices ----

    def getObjectTransformationMatrix(self, objID: int) -> 'np.ndarray':
        """Return the object's 4x4 transformation matrix as a (4,4) float32 ndarray.

        Helios stores matrices in row-major order, so element (i, j) is at
        position [i, j] of the returned ndarray. The translation column is at
        positions [0, 3], [1, 3], [2, 3].
        """
        self._check_context_available()
        flat = context_wrapper.getObjectTransformationMatrixWrapper(self.context, int(objID))
        return self._mat4_to_ndarray(flat)

    def setObjectTransformationMatrix(self, objIDs_or_objID, T) -> None:
        """Set the 4x4 transformation matrix on one or more compound objects.

        Args:
            objIDs_or_objID: A single object ID (int) or a list/tuple of object IDs.
            T: A 4x4 matrix as numpy.ndarray((4,4) | (16,) float), list of 16 floats,
                or a nested 4x4 list. Row-major; T[i, j] is element (i, j).
        """
        self._check_context_available()
        flat = self._marshal_mat4(T)
        if isinstance(objIDs_or_objID, (list, tuple)):
            context_wrapper.setObjectTransformationMatrixBatchWrapper(
                self.context, list(objIDs_or_objID), flat
            )
        else:
            context_wrapper.setObjectTransformationMatrixWrapper(
                self.context, int(objIDs_or_objID), flat
            )

    def getPrimitiveTransformationMatrix(self, uuid: int) -> 'np.ndarray':
        """Return the primitive's 4x4 transformation matrix as a (4,4) float32 ndarray
        (row-major; see getObjectTransformationMatrix for layout details)."""
        self._check_context_available()
        flat = context_wrapper.getPrimitiveTransformationMatrixWrapper(self.context, int(uuid))
        return self._mat4_to_ndarray(flat)

    def setPrimitiveTransformationMatrix(self, uuids_or_uuid, T) -> None:
        """Set the 4x4 transformation matrix on one or more primitives.

        Args:
            uuids_or_uuid: A single UUID (int) or a list/tuple of UUIDs.
            T: A 4x4 matrix; see setObjectTransformationMatrix for accepted formats.
        """
        self._check_context_available()
        flat = self._marshal_mat4(T)
        if isinstance(uuids_or_uuid, (list, tuple)):
            context_wrapper.setPrimitiveTransformationMatrixBatchWrapper(
                self.context, list(uuids_or_uuid), flat
            )
        else:
            context_wrapper.setPrimitiveTransformationMatrixWrapper(
                self.context, int(uuids_or_uuid), flat
            )

    # ---- Domain bounds ----

    def getDomainBoundingBox(self, uuids: Optional[List[int]] = None):
        """Return the axis-aligned bounding box of the domain (or a UUID subset).

        Args:
            uuids: Optional list of primitive UUIDs to restrict the computation to.
                If None (default), uses every primitive in the context.

        Returns:
            ``(xbounds, ybounds, zbounds)`` where each element is a ``vec2(min, max)``.
        """
        self._check_context_available()
        if uuids is None:
            xb, yb, zb = context_wrapper.getDomainBoundingBoxWrapper(self.context)
        else:
            if not isinstance(uuids, (list, tuple)):
                raise ValueError(f"uuids must be a list or tuple, got {type(uuids).__name__}")
            xb, yb, zb = context_wrapper.getDomainBoundingBoxFilteredWrapper(self.context, list(uuids))
        return (vec2(xb[0], xb[1]), vec2(yb[0], yb[1]), vec2(zb[0], zb[1]))

    def getDomainBoundingSphere(self, uuids: Optional[List[int]] = None):
        """Return the bounding sphere of the domain (or a UUID subset).

        Returns:
            ``(center, radius)`` where ``center`` is a ``vec3`` and ``radius`` is a float.
        """
        self._check_context_available()
        if uuids is None:
            center, radius = context_wrapper.getDomainBoundingSphereWrapper(self.context)
        else:
            if not isinstance(uuids, (list, tuple)):
                raise ValueError(f"uuids must be a list or tuple, got {type(uuids).__name__}")
            center, radius = context_wrapper.getDomainBoundingSphereFilteredWrapper(self.context, list(uuids))
        return (vec3(center[0], center[1], center[2]), float(radius))

    # =========================================================================
    # Tube/polymesh + object color/dirty/tile mutators
    # =========================================================================

    # ---- Tube object mutators ----

    def setTubeNodes(self, objID: int, nodes: List[vec3]) -> None:
        """Replace the node positions of an existing tube object."""
        self._check_context_available()
        if not isinstance(nodes, (list, tuple)):
            raise ValueError(f"nodes must be a list or tuple, got {type(nodes).__name__}")
        flat = []
        for i, n in enumerate(nodes):
            if not isinstance(n, vec3):
                raise ValueError(f"nodes[{i}] must be a vec3, got {type(n).__name__}")
            flat.extend([n.x, n.y, n.z])
        context_wrapper.setTubeNodesWrapper(self.context, int(objID), flat)

    def setTubeRadii(self, objID: int, radii: List[float]) -> None:
        """Replace the per-node radii of an existing tube object."""
        self._check_context_available()
        if not isinstance(radii, (list, tuple)):
            raise ValueError(f"radii must be a list or tuple, got {type(radii).__name__}")
        context_wrapper.setTubeRadiiWrapper(self.context, int(objID), [float(r) for r in radii])

    def scaleTubeGirth(self, objID: int, scale_factor: float) -> None:
        """Scale the radii of an existing tube object by ``scale_factor``."""
        self._check_context_available()
        context_wrapper.scaleTubeGirthWrapper(self.context, int(objID), float(scale_factor))

    def scaleTubeLength(self, objID: int, scale_factor: float) -> None:
        """Scale the lengths between tube nodes by ``scale_factor``."""
        self._check_context_available()
        context_wrapper.scaleTubeLengthWrapper(self.context, int(objID), float(scale_factor))

    def pruneTubeNodes(self, objID: int, node_index: int) -> None:
        """Remove all tube nodes from index ``node_index`` to the end."""
        self._check_context_available()
        context_wrapper.pruneTubeNodesWrapper(self.context, int(objID), int(node_index))

    def appendTubeSegment(self, objID: int, node_position: vec3, radius: float, *,
                          color: Optional[RGBcolor] = None,
                          texture_file: Optional[str] = None,
                          uv: Optional[vec2] = None) -> None:
        """Append a new segment to an existing tube object.

        Pass exactly one of ``color`` (an RGBcolor) or both ``texture_file`` and
        ``uv`` (a vec2 of texture u-fractions) to specify how the new segment
        should be shaded.
        """
        self._check_context_available()
        if not isinstance(node_position, vec3):
            raise ValueError(f"node_position must be a vec3, got {type(node_position).__name__}")
        has_color = color is not None
        has_texture = texture_file is not None or uv is not None
        if has_color == has_texture:
            raise ValueError(
                "appendTubeSegment requires exactly one of (color) or "
                "(texture_file and uv); cannot mix or omit both."
            )
        if has_color:
            if not isinstance(color, RGBcolor):
                raise ValueError(f"color must be an RGBcolor, got {type(color).__name__}")
            context_wrapper.appendTubeSegmentColorWrapper(
                self.context, int(objID), node_position.to_list(), float(radius),
                [color.r, color.g, color.b]
            )
        else:
            if texture_file is None or uv is None:
                raise ValueError(
                    "appendTubeSegment with texture requires both texture_file and uv."
                )
            if not isinstance(uv, vec2):
                raise ValueError(f"uv must be a vec2, got {type(uv).__name__}")
            tex_path = self._validate_file_path(
                texture_file, ['.png', '.jpg', '.jpeg', '.tga', '.bmp']
            )
            context_wrapper.appendTubeSegmentTextureWrapper(
                self.context, int(objID), node_position.to_list(), float(radius),
                tex_path, [uv.x, uv.y]
            )

    # ---- Polymesh object ----

    def addPolymeshObject(self, uuids: List[int]) -> int:
        """Group the given primitives into a new polymesh compound object and return its ID."""
        self._check_context_available()
        if not isinstance(uuids, (list, tuple)):
            raise ValueError(f"uuids must be a list or tuple, got {type(uuids).__name__}")
        if len(uuids) == 0:
            raise ValueError("addPolymeshObject requires at least one UUID")
        return context_wrapper.addPolymeshObjectWrapper(self.context, list(uuids))

    # ---- Object color ----

    def setObjectColor(self, objIDs_or_objID, color) -> None:
        """Set the color of one or more compound objects.

        Accepts a single object ID or list/tuple of IDs. ``color`` must be an
        ``RGBcolor`` or ``RGBAcolor``.
        """
        self._check_context_available()
        if isinstance(color, RGBAcolor):
            comps = [color.r, color.g, color.b, color.a]
            if isinstance(objIDs_or_objID, (list, tuple)):
                context_wrapper.setObjectColorRGBABatchWrapper(self.context, list(objIDs_or_objID), comps)
            else:
                context_wrapper.setObjectColorRGBAWrapper(self.context, int(objIDs_or_objID), comps)
        elif isinstance(color, RGBcolor):
            comps = [color.r, color.g, color.b]
            if isinstance(objIDs_or_objID, (list, tuple)):
                context_wrapper.setObjectColorRGBBatchWrapper(self.context, list(objIDs_or_objID), comps)
            else:
                context_wrapper.setObjectColorRGBWrapper(self.context, int(objIDs_or_objID), comps)
        else:
            raise ValueError(
                f"color must be an RGBcolor or RGBAcolor, got {type(color).__name__}"
            )

    def overrideObjectTextureColor(self, objIDs_or_objID) -> None:
        """Override the texture mapping with the object's vertex color."""
        self._check_context_available()
        if isinstance(objIDs_or_objID, (list, tuple)):
            context_wrapper.overrideObjectTextureColorBatchWrapper(self.context, list(objIDs_or_objID))
        else:
            context_wrapper.overrideObjectTextureColorWrapper(self.context, int(objIDs_or_objID))

    def useObjectTextureColor(self, objIDs_or_objID) -> None:
        """Restore use of the texture color (undoes overrideObjectTextureColor)."""
        self._check_context_available()
        if isinstance(objIDs_or_objID, (list, tuple)):
            context_wrapper.useObjectTextureColorBatchWrapper(self.context, list(objIDs_or_objID))
        else:
            context_wrapper.useObjectTextureColorWrapper(self.context, int(objIDs_or_objID))

    # ---- Mark dirty/clean ----

    def markPrimitiveDirty(self, uuids_or_uuid) -> None:
        """Mark one or more primitives as dirty (geometry has been modified)."""
        self._check_context_available()
        if isinstance(uuids_or_uuid, (list, tuple)):
            context_wrapper.markPrimitiveDirtyBatchWrapper(self.context, list(uuids_or_uuid))
        else:
            context_wrapper.markPrimitiveDirtyWrapper(self.context, int(uuids_or_uuid))

    def markPrimitiveClean(self, uuids_or_uuid) -> None:
        """Mark one or more primitives as clean (cancels dirty state)."""
        self._check_context_available()
        if isinstance(uuids_or_uuid, (list, tuple)):
            context_wrapper.markPrimitiveCleanBatchWrapper(self.context, list(uuids_or_uuid))
        else:
            context_wrapper.markPrimitiveCleanWrapper(self.context, int(uuids_or_uuid))

    # ---- Tile subdivision ----

    def setTileObjectSubdivisionCount(self, objIDs_or_objID, subdiv: int2) -> None:
        """Set the (Nx, Ny) subdivision count of one or more tile objects.

        The Helios C++ API is batch-only; a single objID is wrapped as a
        single-element list.
        """
        self._check_context_available()
        if not isinstance(subdiv, int2):
            raise ValueError(f"subdiv must be an int2, got {type(subdiv).__name__}")
        if isinstance(objIDs_or_objID, (list, tuple)):
            ids = list(objIDs_or_objID)
        else:
            ids = [int(objIDs_or_objID)]
        context_wrapper.setTileObjectSubdivisionCountWrapper(
            self.context, ids, int(subdiv.x), int(subdiv.y)
        )

    def setTileObjectSubdivisionByAreaRatio(self, objIDs_or_objID, area_ratio: float) -> None:
        """Set tile object subdivision dynamically based on a target area ratio.

        Each tile is subdivided so that its sub-tile area is approximately
        ``area_ratio`` times the tile's full area.
        """
        self._check_context_available()
        if isinstance(objIDs_or_objID, (list, tuple)):
            ids = list(objIDs_or_objID)
        else:
            ids = [int(objIDs_or_objID)]
        context_wrapper.setTileObjectSubdivisionByAreaRatioWrapper(
            self.context, ids, float(area_ratio)
        )

    # =========================================================================
    # Cleanup, XML write, RNG, Location
    # =========================================================================

    # ---- Cleanup ----

    def cleanDeletedUUIDs(self, uuids: List[int]) -> List[int]:
        """Return a new list with deleted UUIDs removed; the input list is not mutated.

        This mirrors the convention used by ``cropDomain``, which returns the
        survivors rather than mutating in place.
        """
        self._check_context_available()
        if not isinstance(uuids, (list, tuple)):
            raise ValueError(f"uuids must be a list or tuple, got {type(uuids).__name__}")
        return context_wrapper.cleanDeletedUUIDsWrapper(self.context, list(uuids))

    def cleanDeletedObjectIDs(self, objIDs: List[int]) -> List[int]:
        """Return a new list with deleted object IDs removed; input is not mutated."""
        self._check_context_available()
        if not isinstance(objIDs, (list, tuple)):
            raise ValueError(f"objIDs must be a list or tuple, got {type(objIDs).__name__}")
        return context_wrapper.cleanDeletedObjectIDsWrapper(self.context, list(objIDs))

    # ---- XML write ----

    def writeXML(self, filename: str, uuids: Optional[List[int]] = None, quiet: bool = False) -> None:
        """Write the context (or a UUID subset) to an XML file.

        Args:
            filename: Output file path. Must end in .xml.
            uuids: Optional list of primitive UUIDs to restrict the export. If
                None (default), all primitives are written.
            quiet: Suppress informational console output.
        """
        self._check_context_available()
        path = self._validate_output_file_path(filename, ['.xml'])
        if uuids is None:
            context_wrapper.writeXMLWrapper(self.context, path, bool(quiet))
        else:
            if not isinstance(uuids, (list, tuple)):
                raise ValueError(f"uuids must be a list or tuple, got {type(uuids).__name__}")
            context_wrapper.writeXMLFilteredWrapper(self.context, path, list(uuids), bool(quiet))

    def writeXML_byobject(self, filename: str, objIDs: List[int], quiet: bool = False) -> None:
        """Write a subset of compound objects to an XML file."""
        self._check_context_available()
        path = self._validate_output_file_path(filename, ['.xml'])
        if not isinstance(objIDs, (list, tuple)):
            raise ValueError(f"objIDs must be a list or tuple, got {type(objIDs).__name__}")
        context_wrapper.writeXMLByObjectWrapper(self.context, path, list(objIDs), bool(quiet))

    # ---- RNG ----

    def randu(self, low=None, high=None):
        """Draw a uniform random number using the Context's RNG.

        Three forms:
            ``randu()`` -> float in [0, 1)
            ``randu(low: float, high: float)`` -> float in [low, high)
            ``randu(low: int, high: int)`` -> int in [low, high]

        Whether the integer or float overload is invoked is determined by
        ``isinstance(low, int)``; pass ``low/high`` as Python ints for the
        integer range form.
        """
        self._check_context_available()
        if low is None and high is None:
            return context_wrapper.randuBasicWrapper(self.context)
        if low is None or high is None:
            raise ValueError("randu requires both low and high, or neither.")
        if isinstance(low, bool) or isinstance(high, bool):
            raise ValueError("randu bounds cannot be bool.")
        # Treat the call as integer-range only when BOTH bounds are Python ints
        # (and not bools, handled above). Otherwise use the float form.
        if isinstance(low, int) and isinstance(high, int):
            return context_wrapper.randuIntRangeWrapper(self.context, low, high)
        return context_wrapper.randuRangeWrapper(self.context, float(low), float(high))

    def randn(self, mean=None, stddev=None) -> float:
        """Draw a normal random number using the Context's RNG.

        Two forms:
            ``randn()`` -> standard normal (mean 0, stddev 1)
            ``randn(mean: float, stddev: float)`` -> N(mean, stddev**2)
        """
        self._check_context_available()
        if mean is None and stddev is None:
            return context_wrapper.randnBasicWrapper(self.context)
        if mean is None or stddev is None:
            raise ValueError("randn requires both mean and stddev, or neither.")
        return context_wrapper.randnParamsWrapper(self.context, float(mean), float(stddev))

    # ---- Location ----

    def setLocation(self, location_or_lat, longitude=None, utc_offset=None) -> None:
        """Set the geographic location used by solar/radiation calculations.

        Two call forms:
            ``setLocation(loc: Location)``
            ``setLocation(latitude_deg: float, longitude_deg: float, utc_offset: float)``
        """
        self._check_context_available()
        if isinstance(location_or_lat, Location):
            if longitude is not None or utc_offset is not None:
                raise ValueError("When passing a Location, do not also pass longitude/utc_offset.")
            loc = location_or_lat
        else:
            if longitude is None or utc_offset is None:
                raise ValueError(
                    "setLocation requires either a Location object or "
                    "(latitude_deg, longitude_deg, utc_offset) as 3 floats."
                )
            loc = Location(float(location_or_lat), float(longitude), float(utc_offset))
        context_wrapper.setLocationWrapper(self.context, loc.latitude, loc.longitude, loc.utc_offset)

    def getLocation(self) -> Location:
        """Return the Context's currently-configured geographic location."""
        self._check_context_available()
        lat, lon, utc = context_wrapper.getLocationWrapper(self.context)
        return Location(lat, lon, utc)

    # =========================================================================
    # Colormap helpers + texture transparency
    # =========================================================================

    def generateColormap(self, name: str, n_colors: int) -> List[RGBcolor]:
        """Generate a colormap with ``n_colors`` entries from a named colormap.

        Args:
            name: Helios colormap name (e.g., "hot", "cool", "lava", "rainbow").
            n_colors: Number of colors in the returned ramp.

        Returns:
            A list of ``RGBcolor`` instances of length ``n_colors``.
        """
        self._check_context_available()
        flat = context_wrapper.generateColormapNamedWrapper(self.context, name, int(n_colors))
        return [RGBcolor(flat[i*3 + 0], flat[i*3 + 1], flat[i*3 + 2]) for i in range(int(n_colors))]

    def generateTexturesFromColormap(self, texture_file: str, colormap: List[RGBcolor]) -> List[str]:
        """Generate one texture file per color in ``colormap`` derived from
        ``texture_file``. Returns the list of generated file paths.
        """
        self._check_context_available()
        if not isinstance(colormap, (list, tuple)):
            raise ValueError(f"colormap must be a list or tuple, got {type(colormap).__name__}")
        flat = []
        for i, c in enumerate(colormap):
            if not isinstance(c, RGBcolor):
                raise ValueError(f"colormap[{i}] must be an RGBcolor, got {type(c).__name__}")
            flat.extend([c.r, c.g, c.b])
        # Validate the input texture exists and looks like an image.
        validated_path = self._validate_file_path(
            texture_file, ['.png', '.jpg', '.jpeg', '.tga', '.bmp']
        )
        return context_wrapper.generateTexturesFromColormapWrapper(
            self.context, validated_path, flat
        )

    def getPrimitiveTextureTransparencyData(self, uuid: int) -> Optional['np.ndarray']:
        """Return the primitive's texture transparency mask as a 2D bool ndarray.

        Returns None if the primitive has no associated transparency channel
        (e.g., it is untextured or its texture has no alpha). The returned
        ndarray has shape (height, width) and dtype ``bool``.
        """
        self._check_context_available()
        result = context_wrapper.getPrimitiveTextureTransparencyDataWrapper(self.context, int(uuid))
        if result is None:
            return None
        width, height, flat = result
        return np.array(flat, dtype=bool).reshape((height, width))


