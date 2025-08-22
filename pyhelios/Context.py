import ctypes
from dataclasses import dataclass
from typing import List, Optional, Union
from enum import Enum

import numpy as np

from .wrappers import UContextWrapper as context_wrapper
from .wrappers.DataTypes import vec2, vec3, vec4, int2, int3, int4, SphericalCoord, RGBcolor, PrimitiveType
from .plugins.loader import LibraryLoadError, validate_library, get_library_info
from .plugins.registry import get_plugin_registry


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
        
        # Check if we're in mock/development mode
        library_info = get_library_info()
        if library_info.get('is_mock', False):
            # In mock mode, don't validate but warn that functionality is limited
            print("Warning: PyHelios running in development mock mode - functionality is limited")
            print("Available plugins: None (mock mode)")
            self.context = None  # Mock context
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
                raise LibraryLoadError(
                    "Failed to create Helios context. Native library may not be functioning correctly."
                )
            
            # Log available plugins after successful context creation
            available_plugins = self._plugin_registry.get_available_plugins()
            if available_plugins:
                print(f"PyHelios Context created with {len(available_plugins)} available plugins: {', '.join(available_plugins[:3])}{'...' if len(available_plugins) > 3 else ''}")
            else:
                print("PyHelios Context created (no plugins detected - check build configuration)")
                
        except Exception as e:
            raise LibraryLoadError(
                f"Failed to create Helios context: {e}. "
                f"Ensure native libraries are built and accessible."
            )
        
    def _check_context_available(self):
        """Helper method to check if context is available (not in mock mode)."""
        if self.context is None:
            raise RuntimeError("Context is in mock mode - native functionality not available. "
                             "Build native libraries with 'python build_scripts/build_helios.py' or set PYHELIOS_DEV_MODE=1 for development.")
    
    def _validate_uuid(self, uuid: int):
        """Validate that a UUID exists in this context.
        
        Args:
            uuid: The UUID to validate
            
        Raises:
            ValueError: If UUID is invalid or doesn't exist in context
        """
        # First check if it's a reasonable UUID value
        if not isinstance(uuid, int) or uuid < 0:
            raise ValueError(f"Invalid UUID: {uuid}. UUIDs must be non-negative integers.")
        
        # Check if UUID exists in context by getting all valid UUIDs
        try:
            valid_uuids = self.getAllUUIDs()
            if uuid not in valid_uuids:
                raise ValueError(f"UUID {uuid} does not exist in context. Valid UUIDs: {valid_uuids[:10]}{'...' if len(valid_uuids) > 10 else ''}")
        except:
            # If we can't get valid UUIDs (e.g., in mock mode), skip validation
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
        
        # Check if file exists
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"File not found: {abs_path}")
        
        # Check if it's actually a file (not a directory)
        if not os.path.isfile(abs_path):
            raise ValueError(f"Path is not a file: {abs_path}")
        
        # Check file extension if specified
        if expected_extensions:
            file_ext = os.path.splitext(abs_path)[1].lower()
            if file_ext not in [ext.lower() for ext in expected_extensions]:
                raise ValueError(f"Invalid file extension '{file_ext}'. Expected one of: {expected_extensions}")
        
        return abs_path

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.context is not None:
            context_wrapper.destroyContext(self.context)
            self.context = None  # Prevent double deletion

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

    def addPatch(self, center: vec3 = vec3(0, 0, 0), size: vec2 = vec2(1, 1), rotation: Optional[SphericalCoord] = None, color: Optional[RGBcolor] = None) -> int:
        self._check_context_available()
        rotation = rotation or SphericalCoord(1, 0, 0)  # radius=1, elevation=0, azimuth=0 (no effective rotation)
        color = color or RGBcolor(1, 1, 1)
        return context_wrapper.addPatchWithCenterSizeRotationAndColor(self.context, center.to_list(), size.to_list(), rotation.to_list(), color.to_list())
        
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

    def getPrimitiveType(self, uuid: int) -> PrimitiveType:
        self._check_context_available()
        primitive_type = context_wrapper.getPrimitiveType(self.context, uuid)
        return PrimitiveType(primitive_type)

    def getPrimitiveArea(self, uuid: int) -> float:
        self._check_context_available()
        return context_wrapper.getPrimitiveArea(self.context, uuid)

    def getPrimitiveNormal(self, uuid: int) -> vec3:
        self._check_context_available()
        normal_ptr = context_wrapper.getPrimitiveNormal(self.context, uuid)
        v = vec3(normal_ptr[0], normal_ptr[1], normal_ptr[2])
        return v

    def getPrimitiveVertices(self, uuid: int) -> List[vec3]:
        self._check_context_available()
        size = ctypes.c_uint()
        vertices_ptr = context_wrapper.getPrimitiveVertices(self.context, uuid, ctypes.byref(size))
        # size.value is the total number of floats (3 per vertex), not the number of vertices
        vertices_list = ctypes.cast(vertices_ptr, ctypes.POINTER(ctypes.c_float * size.value)).contents
        vertices = [vec3(vertices_list[i], vertices_list[i+1], vertices_list[i+2]) for i in range(0, size.value, 3)]
        return vertices

    def getPrimitiveColor(self, uuid: int) -> RGBcolor:
        self._check_context_available()
        color_ptr = context_wrapper.getPrimitiveColor(self.context, uuid)
        return RGBcolor(color_ptr[0], color_ptr[1], color_ptr[2])

    def getPrimitiveCount(self) -> int:
        self._check_context_available()
        return context_wrapper.getPrimitiveCount(self.context)

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
        # Get all physical properties using existing methods
        primitive_type = self.getPrimitiveType(uuid)
        area = self.getPrimitiveArea(uuid)
        normal = self.getPrimitiveNormal(uuid)
        vertices = self.getPrimitiveVertices(uuid)
        color = self.getPrimitiveColor(uuid)
        
        # Create and return PrimitiveInfo object
        return PrimitiveInfo(
            uuid=uuid,
            primitive_type=primitive_type,
            area=area,
            normal=normal,
            vertices=vertices,
            color=color
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
        
        # Parameter validation
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
            return context_wrapper.loadPLYWithOriginHeightRotation(self.context, validated_filename, origin.to_list(), height, rotation.to_list(), upaxis, silent)
        
        elif origin is not None and height is not None and rotation is None and color is not None:
            # Load with origin, height, and color
            return context_wrapper.loadPLYWithOriginHeightColor(self.context, validated_filename, origin.to_list(), height, color.to_list(), upaxis, silent)
        
        elif origin is not None and height is not None and rotation is not None and color is not None:
            # Load with all parameters
            return context_wrapper.loadPLYWithOriginHeightRotationColor(self.context, validated_filename, origin.to_list(), height, rotation.to_list(), color.to_list(), upaxis, silent)
        
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
                                      uv_coords: np.ndarray, texture_file: str) -> List[int]:
        """
        Add textured triangles from NumPy arrays.
        
        Args:
            vertices: NumPy array of shape (N, 3) containing vertex coordinates as float32/float64
            faces: NumPy array of shape (M, 3) containing triangle vertex indices as int32/int64
            uv_coords: NumPy array of shape (N, 2) containing UV texture coordinates as float32/float64
            texture_file: Path to the texture image file
            
        Returns:
            List of UUIDs for the added textured triangles
            
        Raises:
            ValueError: If array dimensions are invalid
        """
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
        
        # Convert arrays to appropriate data types
        vertices_float = vertices.astype(np.float32)
        faces_int = faces.astype(np.int32)
        uv_coords_float = uv_coords.astype(np.float32)
        
        # Add textured triangles
        triangle_uuids = []
        for i in range(faces.shape[0]):
            # Get vertex indices for this triangle
            v0_idx, v1_idx, v2_idx = faces_int[i]
            
            # Get vertex coordinates
            vertex0 = vertices_float[v0_idx].tolist()
            vertex1 = vertices_float[v1_idx].tolist()
            vertex2 = vertices_float[v2_idx].tolist()
            
            # Get UV coordinates
            uv0 = uv_coords_float[v0_idx].tolist()
            uv1 = uv_coords_float[v1_idx].tolist()
            uv2 = uv_coords_float[v2_idx].tolist()
            
            # Add textured triangle
            uuid = context_wrapper.addTriangleWithTexture(self.context, vertex0, vertex1, vertex2, 
                                                         texture_file, uv0, uv1, uv2)
            triangle_uuids.append(uuid)
        
        return triangle_uuids

    # ==================== PRIMITIVE DATA METHODS ====================
    # Primitive data is a flexible key-value store where users can associate 
    # arbitrary data with primitives using string keys
    
    def setPrimitiveDataInt(self, uuid: int, label: str, value: int) -> None:
        """
        Set primitive data as signed 32-bit integer.
        
        Args:
            uuid: UUID of the primitive
            label: String key for the data
            value: Signed integer value
        """
        context_wrapper.setPrimitiveDataInt(self.context, uuid, label, value)
    
    def setPrimitiveDataUInt(self, uuid: int, label: str, value: int) -> None:
        """
        Set primitive data as unsigned 32-bit integer.
        
        Critical for properties like 'twosided_flag' which must be uint in C++.
        
        Args:
            uuid: UUID of the primitive
            label: String key for the data
            value: Unsigned integer value (will be cast to uint32)
        """
        context_wrapper.setPrimitiveDataUInt(self.context, uuid, label, value)
    
    def setPrimitiveDataFloat(self, uuid: int, label: str, value: float) -> None:
        """
        Set primitive data as 32-bit float.
        
        Args:
            uuid: UUID of the primitive
            label: String key for the data
            value: Float value
        """
        context_wrapper.setPrimitiveDataFloat(self.context, uuid, label, value)
    
    def setPrimitiveDataString(self, uuid: int, label: str, value: str) -> None:
        """
        Set primitive data as string.
        
        Args:
            uuid: UUID of the primitive
            label: String key for the data
            value: String value
        """
        context_wrapper.setPrimitiveDataString(self.context, uuid, label, value)
    
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

