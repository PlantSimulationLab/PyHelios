"""
LiDARCloud - High-level interface for LiDAR simulation and point cloud processing

Provides Python interface to Helios LiDAR plugin for:
- Synthetic LiDAR scanning
- Point cloud management and filtering
- Triangulation and mesh generation
- Leaf area density calculations
"""

from typing import List, Tuple, Optional, Union
from .wrappers import ULiDARWrapper as lidar_wrapper
from .Context import Context
from .plugins.registry import get_plugin_registry
from .exceptions import HeliosError
from .wrappers.DataTypes import vec3, RGBcolor, SphericalCoord
from .validation.datatypes import validate_vec3
from .validation.core import validate_positive_value


class LiDARError(HeliosError):
    """Exception raised for LiDAR-specific errors"""
    pass


class LiDARCloud:
    """
    High-level interface for LiDAR point cloud operations.

    Supports synthetic scanning, point cloud filtering, triangulation,
    and leaf area density calculations.

    Example:
        >>> from pyhelios import LiDARCloud
        >>> from pyhelios.types import vec3
        >>>
        >>> with LiDARCloud() as lidar:
        ...     # Add a scan
        ...     scan_id = lidar.addScan(
        ...         origin=vec3(0, 0, 1),
        ...         Ntheta=100, theta_range=(0, 1.57),
        ...         Nphi=100, phi_range=(-3.14, 3.14),
        ...         exit_diameter=0.01, beam_divergence=0.001
        ...     )
        ...
        ...     # Add hit points
        ...     lidar.addHitPoint(scan_id, vec3(1, 0, 0), vec3(1, 0, 0))
        ...
        ...     # Export point cloud
        ...     lidar.exportPointCloud("output.xyz")
    """

    def __init__(self):
        """
        Initialize LiDARCloud.

        Raises:
            LiDARError: If plugin not available in current build
            RuntimeError: If cloud initialization fails
        """
        # Check plugin availability
        registry = get_plugin_registry()
        if not registry.is_plugin_available('lidar'):
            raise LiDARError(
                "LiDAR plugin not available. Rebuild PyHelios with LiDAR:\n"
                "  build_scripts/build_helios --plugins lidar\n"
                "\n"
                "System requirements:\n"
                "  - Platforms: Windows, Linux, macOS\n"
                "  - GPU: Optional (enables GPU acceleration)"
            )

        self._cloud_ptr = lidar_wrapper.createLiDARcloud()
        if not self._cloud_ptr:
            raise LiDARError("Failed to create LiDAR cloud")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources"""
        if hasattr(self, '_cloud_ptr') and self._cloud_ptr:
            lidar_wrapper.destroyLiDARcloud(self._cloud_ptr)
            self._cloud_ptr = None

    def __del__(self):
        """Fallback destructor for cleanup without context manager"""
        if hasattr(self, '_cloud_ptr') and self._cloud_ptr is not None:
            try:
                lidar_wrapper.destroyLiDARcloud(self._cloud_ptr)
                self._cloud_ptr = None
            except Exception as e:
                import warnings
                warnings.warn(f"Error in LiDARCloud.__del__: {e}")

    def addScan(self, origin: Union[vec3, List[float], Tuple[float, float, float]],
                Ntheta: int, theta_range: Tuple[float, float],
                Nphi: int, phi_range: Tuple[float, float],
                exit_diameter: float, beam_divergence: float) -> int:
        """
        Add a LiDAR scan to the point cloud.

        Args:
            origin: Scanner position (vec3 or 3-element list/tuple)
            Ntheta: Number of scan points in zenith direction
            theta_range: Zenith angle range (min, max) in radians
            Nphi: Number of scan points in azimuthal direction
            phi_range: Azimuthal angle range (min, max) in radians
            exit_diameter: Laser beam exit diameter (meters)
            beam_divergence: Beam divergence angle (radians)

        Returns:
            Scan ID for referencing this scan

        Example:
            >>> scan_id = lidar.addScan(
            ...     origin=vec3(0, 0, 1),
            ...     Ntheta=100, theta_range=(0, 1.57),
            ...     Nphi=100, phi_range=(-3.14, 3.14),
            ...     exit_diameter=0.01, beam_divergence=0.001
            ... )
        """
        # Convert origin to vec3 if needed
        if isinstance(origin, (list, tuple)):
            if len(origin) != 3:
                raise ValueError("Origin must have 3 elements [x, y, z]")
            origin = vec3(*origin)
        elif not hasattr(origin, 'x'):
            raise ValueError("Origin must be vec3 or 3-element list/tuple")

        origin_list = [origin.x, origin.y, origin.z]

        # Validate scan parameters
        validate_positive_value(Ntheta, 'Ntheta', 'addScan')
        validate_positive_value(Nphi, 'Nphi', 'addScan')

        if not isinstance(theta_range, (list, tuple)) or len(theta_range) != 2:
            raise ValueError("theta_range must be a tuple (min, max)")
        if not isinstance(phi_range, (list, tuple)) or len(phi_range) != 2:
            raise ValueError("phi_range must be a tuple (min, max)")

        return lidar_wrapper.addLiDARScan(
            self._cloud_ptr, origin_list, Ntheta, theta_range,
            Nphi, phi_range, exit_diameter, beam_divergence
        )

    def getScanCount(self) -> int:
        """Get total number of scans in the cloud"""
        return lidar_wrapper.getLiDARScanCount(self._cloud_ptr)

    def getScanOrigin(self, scanID: int) -> vec3:
        """Get origin of a specific scan"""
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        origin_list = lidar_wrapper.getLiDARScanOrigin(self._cloud_ptr, scanID)
        return vec3(*origin_list)

    def getScanSizeTheta(self, scanID: int) -> int:
        """Get number of zenith scan points for a scan"""
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        return lidar_wrapper.getLiDARScanSizeTheta(self._cloud_ptr, scanID)

    def getScanSizePhi(self, scanID: int) -> int:
        """Get number of azimuthal scan points for a scan"""
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        return lidar_wrapper.getLiDARScanSizePhi(self._cloud_ptr, scanID)

    def addHitPoint(self, scanID: int,
                    xyz: Union[vec3, List[float], Tuple[float, float, float]],
                    direction: Union[vec3, SphericalCoord, List[float], Tuple[float, float]],
                    color: Optional[Union[RGBcolor, List[float], Tuple[float, float, float]]] = None):
        """
        Add a hit point to the point cloud.

        Args:
            scanID: Scan ID this hit belongs to
            xyz: Hit point coordinates (vec3 or 3-element list)
            direction: Ray direction (vec3/SphericalCoord or 2-3 element list)
            color: Optional RGB color (RGBcolor or 3-element list)
        """
        # Convert xyz to list
        if isinstance(xyz, (list, tuple)):
            if len(xyz) != 3:
                raise ValueError("XYZ must have 3 elements")
            xyz_list = list(xyz)
        elif hasattr(xyz, 'x'):
            xyz_list = [xyz.x, xyz.y, xyz.z]
        else:
            raise ValueError("XYZ must be vec3 or 3-element list/tuple")

        # Convert direction to list
        if isinstance(direction, (list, tuple)):
            if len(direction) < 2:
                raise ValueError("Direction must have at least 2 elements [radius, elevation]")
            direction_list = list(direction)
        elif hasattr(direction, 'radius'):  # SphericalCoord
            direction_list = [direction.radius, direction.elevation, direction.azimuth]
        elif hasattr(direction, 'x'):  # vec3
            direction_list = [direction.x, direction.y, direction.z]
        else:
            raise ValueError("Direction must be vec3/SphericalCoord or 2-3 element list")

        # Add with or without color
        if color is not None:
            if isinstance(color, (list, tuple)):
                if len(color) != 3:
                    raise ValueError("Color must have 3 elements [r, g, b]")
                color_list = list(color)
            elif hasattr(color, 'r'):
                color_list = [color.r, color.g, color.b]
            else:
                raise ValueError("Color must be RGBcolor or 3-element list")

            lidar_wrapper.addLiDARHitPointRGB(self._cloud_ptr, scanID, xyz_list, direction_list, color_list)
        else:
            lidar_wrapper.addLiDARHitPoint(self._cloud_ptr, scanID, xyz_list, direction_list)

    def getHitCount(self) -> int:
        """Get total number of hit points in cloud"""
        return lidar_wrapper.getLiDARHitCount(self._cloud_ptr)

    def getHitXYZ(self, index: int) -> vec3:
        """Get coordinates of a hit point"""
        if index < 0:
            raise ValueError("Index must be non-negative")
        xyz_list = lidar_wrapper.getLiDARHitXYZ(self._cloud_ptr, index)
        return vec3(*xyz_list)

    def getHitRaydir(self, index: int) -> SphericalCoord:
        """Get ray direction of a hit point"""
        if index < 0:
            raise ValueError("Index must be non-negative")
        direction_list = lidar_wrapper.getLiDARHitRaydir(self._cloud_ptr, index)
        return SphericalCoord(direction_list[0], direction_list[1])

    def getHitColor(self, index: int) -> RGBcolor:
        """Get color of a hit point"""
        if index < 0:
            raise ValueError("Index must be non-negative")
        color_list = lidar_wrapper.getLiDARHitColor(self._cloud_ptr, index)
        return RGBcolor(*color_list)

    def deleteHitPoint(self, index: int):
        """Delete a hit point from the cloud"""
        if index < 0:
            raise ValueError("Index must be non-negative")
        lidar_wrapper.deleteLiDARHitPoint(self._cloud_ptr, index)

    def coordinateShift(self, shift: Union[vec3, List[float], Tuple[float, float, float]]):
        """
        Translate all hit points by a shift vector.

        Args:
            shift: Translation vector (vec3 or 3-element list)
        """
        if isinstance(shift, (list, tuple)):
            if len(shift) != 3:
                raise ValueError("Shift must have 3 elements [x, y, z]")
            shift_list = list(shift)
        elif hasattr(shift, 'x'):
            shift_list = [shift.x, shift.y, shift.z]
        else:
            raise ValueError("Shift must be vec3 or 3-element list/tuple")

        lidar_wrapper.lidarCoordinateShift(self._cloud_ptr, shift_list)

    def coordinateRotation(self, rotation: Union[SphericalCoord, List[float], Tuple[float, float]]):
        """
        Rotate all hit points by spherical rotation angles.

        Args:
            rotation: Rotation angles (SphericalCoord or 2-3 element list)
        """
        if isinstance(rotation, (list, tuple)):
            if len(rotation) < 2:
                raise ValueError("Rotation must have at least 2 elements [radius, elevation]")
            rotation_list = list(rotation)
        elif hasattr(rotation, 'radius'):
            rotation_list = [rotation.radius, rotation.elevation, rotation.azimuth]
        else:
            raise ValueError("Rotation must be SphericalCoord or 2-3 element list")

        lidar_wrapper.lidarCoordinateRotation(self._cloud_ptr, rotation_list)

    def triangulateHitPoints(self, Lmax: float, max_aspect_ratio: float = 4.0):
        """
        Generate triangle mesh from hit points using Delaunay triangulation.

        Args:
            Lmax: Maximum triangle edge length
            max_aspect_ratio: Maximum triangle aspect ratio (default 4.0)
        """
        validate_positive_value(Lmax, 'Lmax', 'triangulateHitPoints')
        validate_positive_value(max_aspect_ratio, 'max_aspect_ratio', 'triangulateHitPoints')
        lidar_wrapper.lidarTriangulateHitPoints(self._cloud_ptr, Lmax, max_aspect_ratio)

    def getTriangleCount(self) -> int:
        """Get number of triangles in the mesh"""
        return lidar_wrapper.getLiDARTriangleCount(self._cloud_ptr)

    def distanceFilter(self, maxdistance: float):
        """Filter hit points by maximum distance from scanner"""
        validate_positive_value(maxdistance, 'maxdistance', 'distanceFilter')
        lidar_wrapper.lidarDistanceFilter(self._cloud_ptr, maxdistance)

    def reflectanceFilter(self, minreflectance: float):
        """Filter hit points by minimum reflectance value"""
        lidar_wrapper.lidarReflectanceFilter(self._cloud_ptr, minreflectance)

    def firstHitFilter(self):
        """Keep only first return hit points"""
        lidar_wrapper.lidarFirstHitFilter(self._cloud_ptr)

    def lastHitFilter(self):
        """Keep only last return hit points"""
        lidar_wrapper.lidarLastHitFilter(self._cloud_ptr)

    def exportPointCloud(self, filename: str):
        """Export point cloud to ASCII file"""
        if not filename:
            raise ValueError("Filename cannot be empty")
        lidar_wrapper.exportLiDARPointCloud(self._cloud_ptr, filename)

    def loadXML(self, filename: str):
        """Load scan metadata from XML file"""
        if not filename:
            raise ValueError("Filename cannot be empty")
        lidar_wrapper.loadLiDARXML(self._cloud_ptr, filename)

    def disableMessages(self):
        """Disable console output messages"""
        lidar_wrapper.lidarDisableMessages(self._cloud_ptr)

    def enableMessages(self):
        """Enable console output messages"""
        lidar_wrapper.lidarEnableMessages(self._cloud_ptr)

    def addGrid(self, center: Union[vec3, List[float], Tuple[float, float, float]],
                size: Union[vec3, List[float], Tuple[float, float, float]],
                ndiv: Union[List[int], Tuple[int, int, int]],
                rotation: float = 0.0):
        """
        Add a rectangular grid of voxel cells.

        Args:
            center: Grid center position (vec3 or 3-element list)
            size: Grid dimensions [x, y, z] (vec3 or 3-element list)
            ndiv: Number of divisions [nx, ny, nz] (3-element list)
            rotation: Azimuthal rotation angle (radians, default 0.0)

        Example:
            >>> lidar.addGrid(
            ...     center=vec3(0, 0, 0.5),
            ...     size=vec3(10, 10, 1),
            ...     ndiv=[10, 10, 5],
            ...     rotation=0.0
            ... )
        """
        # Convert center to list
        if isinstance(center, (list, tuple)):
            if len(center) != 3:
                raise ValueError("Center must have 3 elements [x, y, z]")
            center_list = list(center)
        elif hasattr(center, 'x'):
            center_list = [center.x, center.y, center.z]
        else:
            raise ValueError("Center must be vec3 or 3-element list/tuple")

        # Convert size to list
        if isinstance(size, (list, tuple)):
            if len(size) != 3:
                raise ValueError("Size must have 3 elements [x, y, z]")
            size_list = list(size)
        elif hasattr(size, 'x'):
            size_list = [size.x, size.y, size.z]
        else:
            raise ValueError("Size must be vec3 or 3-element list/tuple")

        # Validate ndiv
        if not isinstance(ndiv, (list, tuple)) or len(ndiv) != 3:
            raise ValueError("Ndiv must be a 3-element list [nx, ny, nz]")

        lidar_wrapper.addLiDARGrid(self._cloud_ptr, center_list, size_list, list(ndiv), rotation)

    def addGridCell(self, center: Union[vec3, List[float], Tuple[float, float, float]],
                    size: Union[vec3, List[float], Tuple[float, float, float]],
                    rotation: float = 0.0):
        """
        Add a single grid cell.

        Args:
            center: Cell center position (vec3 or 3-element list)
            size: Cell dimensions [x, y, z] (vec3 or 3-element list)
            rotation: Azimuthal rotation angle (radians, default 0.0)
        """
        # Convert center to list
        if isinstance(center, (list, tuple)):
            if len(center) != 3:
                raise ValueError("Center must have 3 elements [x, y, z]")
            center_list = list(center)
        elif hasattr(center, 'x'):
            center_list = [center.x, center.y, center.z]
        else:
            raise ValueError("Center must be vec3 or 3-element list/tuple")

        # Convert size to list
        if isinstance(size, (list, tuple)):
            if len(size) != 3:
                raise ValueError("Size must have 3 elements [x, y, z]")
            size_list = list(size)
        elif hasattr(size, 'x'):
            size_list = [size.x, size.y, size.z]
        else:
            raise ValueError("Size must be vec3 or 3-element list/tuple")

        lidar_wrapper.addLiDARGridCell(self._cloud_ptr, center_list, size_list, rotation)

    def getGridCellCount(self) -> int:
        """Get total number of grid cells"""
        return lidar_wrapper.getLiDARGridCellCount(self._cloud_ptr)

    def getCellCenter(self, index: int) -> vec3:
        """Get center position of a grid cell"""
        if index < 0:
            raise ValueError("Index must be non-negative")
        center_list = lidar_wrapper.getLiDARCellCenter(self._cloud_ptr, index)
        return vec3(*center_list)

    def getCellSize(self, index: int) -> vec3:
        """Get size of a grid cell"""
        if index < 0:
            raise ValueError("Index must be non-negative")
        size_list = lidar_wrapper.getLiDARCellSize(self._cloud_ptr, index)
        return vec3(*size_list)

    def getCellLeafArea(self, index: int) -> float:
        """Get leaf area of a grid cell (m²)"""
        if index < 0:
            raise ValueError("Index must be non-negative")
        return lidar_wrapper.getLiDARCellLeafArea(self._cloud_ptr, index)

    def getCellLeafAreaDensity(self, index: int) -> float:
        """Get leaf area density of a grid cell (m²/m³)"""
        if index < 0:
            raise ValueError("Index must be non-negative")
        return lidar_wrapper.getLiDARCellLeafAreaDensity(self._cloud_ptr, index)

    def getCellGtheta(self, index: int) -> float:
        """Get G(theta) value for a grid cell"""
        if index < 0:
            raise ValueError("Index must be non-negative")
        return lidar_wrapper.getLiDARCellGtheta(self._cloud_ptr, index)

    def setCellGtheta(self, Gtheta: float, index: int):
        """Set G(theta) value for a grid cell"""
        if index < 0:
            raise ValueError("Index must be non-negative")
        lidar_wrapper.setLiDARCellGtheta(self._cloud_ptr, Gtheta, index)

    def calculateHitGridCell(self):
        """Calculate hit point grid cell assignments"""
        lidar_wrapper.calculateLiDARHitGridCell(self._cloud_ptr)

    def gapfillMisses(self):
        """
        Gapfill sky/miss points where rays didn't hit geometry.

        Important for accurate leaf area calculations with real LiDAR data.
        Should be called before triangulation when processing real data.
        """
        lidar_wrapper.gapfillLiDARMisses(self._cloud_ptr)

    def syntheticScan(self, context: Context,
                     rays_per_pulse: Optional[int] = None,
                     pulse_distance_threshold: Optional[float] = None,
                     scan_grid_only: bool = False,
                     record_misses: bool = True,
                     append: bool = False):
        """
        Perform synthetic LiDAR scan of geometry in Context.

        Requires scan metadata to be defined first via addScan() or loadXML().
        Uses ray tracing to simulate LiDAR instrument measurements.

        Args:
            context: Helios Context containing geometry to scan
            rays_per_pulse: Number of rays per pulse (None=discrete-return, typical: 100)
            pulse_distance_threshold: Distance threshold for aggregating hits (meters, required for waveform)
            scan_grid_only: If True, only scan within defined grid cells
            record_misses: If True, record miss/sky points where rays don't hit geometry
            append: If True, append to existing hits; if False, clear existing hits

        Example (Discrete-return):
            >>> from pyhelios import Context, LiDARCloud
            >>> from pyhelios.types import vec3
            >>> with Context() as context:
            ...     # Add geometry
            ...     context.addPatch(center=vec3(0, 0, 0.5), size=vec2(1, 1))
            ...
            ...     with LiDARCloud() as lidar:
            ...         # Define scan parameters
            ...         scan_id = lidar.addScan(
            ...             origin=vec3(0, 0, 2),
            ...             Ntheta=100, theta_range=(0, 1.57),
            ...             Nphi=100, phi_range=(0, 6.28),
            ...             exit_diameter=0, beam_divergence=0
            ...         )
            ...
            ...         # Perform discrete-return scan
            ...         lidar.syntheticScan(context)

        Example (Full-waveform):
            >>> lidar.syntheticScan(
            ...     context,
            ...     rays_per_pulse=100,
            ...     pulse_distance_threshold=0.02,
            ...     record_misses=True
            ... )
        """
        if not isinstance(context, Context):
            raise TypeError("context must be a Context instance")

        context_ptr = context.getNativePtr()

        # Discrete-return mode (single ray per pulse)
        if rays_per_pulse is None:
            # Use append-aware version to ensure explicit control
            lidar_wrapper.syntheticLiDARScanAppend(self._cloud_ptr, context_ptr, append)
        else:
            # Full-waveform mode (multiple rays per pulse)
            if pulse_distance_threshold is None:
                raise ValueError("pulse_distance_threshold required for full-waveform scanning")

            validate_positive_value(rays_per_pulse, 'rays_per_pulse', 'syntheticScan')
            validate_positive_value(pulse_distance_threshold, 'pulse_distance_threshold', 'syntheticScan')

            lidar_wrapper.syntheticLiDARScanFull(
                self._cloud_ptr, context_ptr,
                rays_per_pulse, pulse_distance_threshold,
                scan_grid_only, record_misses, append
            )

    def calculateLeafArea(self, context: Context, min_voxel_hits: Optional[int] = None):
        """
        Calculate leaf area for each grid cell.

        Requires triangulation to have been performed first.

        Args:
            context: Helios Context instance
            min_voxel_hits: Optional minimum number of hits required per voxel

        Example:
            >>> from pyhelios import Context, LiDARCloud
            >>> with Context() as context:
            ...     with LiDARCloud() as lidar:
            ...         # ... load data, add grid, triangulate ...
            ...         lidar.calculateLeafArea(context)
        """
        if not isinstance(context, Context):
            raise TypeError("context must be a Context instance")

        context_ptr = context.getNativePtr()
        if min_voxel_hits is None:
            lidar_wrapper.calculateLiDARLeafArea(self._cloud_ptr, context_ptr)
        else:
            lidar_wrapper.calculateLiDARLeafAreaMinHits(self._cloud_ptr, context_ptr, min_voxel_hits)

    def calculateSyntheticLeafArea(self, context: Context):
        """
        Calculate synthetic leaf area (for validation of synthetic scans).

        Uses exact primitive geometry to calculate leaf area, useful for
        validating synthetic scan accuracy.

        Args:
            context: Helios Context instance containing primitive geometry
        """
        if not isinstance(context, Context):
            raise TypeError("context must be a Context instance")
        context_ptr = context.getNativePtr()
        lidar_wrapper.calculateSyntheticLiDARLeafArea(self._cloud_ptr, context_ptr)

    def calculateSyntheticGtheta(self, context: Context):
        """
        Calculate synthetic G(theta) (for validation of synthetic scans).

        Uses exact primitive geometry to calculate G(theta), useful for
        validating synthetic scan accuracy.

        Args:
            context: Helios Context instance containing primitive geometry
        """
        if not isinstance(context, Context):
            raise TypeError("context must be a Context instance")
        context_ptr = context.getNativePtr()
        lidar_wrapper.calculateSyntheticLiDARGtheta(self._cloud_ptr, context_ptr)

    def exportTriangleNormals(self, filename: str):
        """Export triangle normal vectors to file"""
        if not filename:
            raise ValueError("Filename cannot be empty")
        lidar_wrapper.exportLiDARTriangleNormals(self._cloud_ptr, filename)

    def exportTriangleAreas(self, filename: str):
        """Export triangle areas to file"""
        if not filename:
            raise ValueError("Filename cannot be empty")
        lidar_wrapper.exportLiDARTriangleAreas(self._cloud_ptr, filename)

    def exportLeafAreas(self, filename: str):
        """Export leaf areas for each grid cell to file"""
        if not filename:
            raise ValueError("Filename cannot be empty")
        lidar_wrapper.exportLiDARLeafAreas(self._cloud_ptr, filename)

    def exportLeafAreaDensities(self, filename: str):
        """Export leaf area densities for each grid cell to file"""
        if not filename:
            raise ValueError("Filename cannot be empty")
        lidar_wrapper.exportLiDARLeafAreaDensities(self._cloud_ptr, filename)

    def exportGtheta(self, filename: str):
        """Export G(theta) values for each grid cell to file"""
        if not filename:
            raise ValueError("Filename cannot be empty")
        lidar_wrapper.exportLiDARGtheta(self._cloud_ptr, filename)

    def addTrianglesToContext(self, context: Context):
        """
        Add triangulated mesh to Context as triangle primitives.

        Converts the triangulated point cloud mesh into Context triangle
        primitives that can be used for further analysis or visualization.

        Args:
            context: Helios Context instance

        Example:
            >>> with Context() as context:
            ...     with LiDARCloud() as lidar:
            ...         lidar.loadXML("scan.xml")
            ...         lidar.triangulateHitPoints(Lmax=0.5, max_aspect_ratio=5)
            ...         lidar.addTrianglesToContext(context)
            ...         print(f"Added {context.getPrimitiveCount()} triangles to context")
        """
        if not isinstance(context, Context):
            raise TypeError("context must be a Context instance")
        lidar_wrapper.addLiDARTrianglesToContext(self._cloud_ptr, context.getNativePtr())

    def initializeCollisionDetection(self, context: Context):
        """
        Initialize CollisionDetection plugin for ray tracing.

        Required before performing synthetic scans.

        Args:
            context: Helios Context instance containing geometry
        """
        if not isinstance(context, Context):
            raise TypeError("context must be a Context instance")
        lidar_wrapper.initializeLiDARCollisionDetection(self._cloud_ptr, context.getNativePtr())

    def enableCDGPUAcceleration(self):
        """Enable GPU acceleration for collision detection ray tracing"""
        lidar_wrapper.enableLiDARCDGPUAcceleration(self._cloud_ptr)

    def disableCDGPUAcceleration(self):
        """Disable GPU acceleration (use CPU ray tracing)"""
        lidar_wrapper.disableLiDARCDGPUAcceleration(self._cloud_ptr)

    def is_available(self) -> bool:
        """
        Check if LiDAR is available in current build.

        Returns:
            True if plugin is available, False otherwise
        """
        registry = get_plugin_registry()
        return registry.is_plugin_available('lidar')


# Convenience function
def create_lidar_cloud() -> LiDARCloud:
    """
    Create LiDARCloud instance.

    Returns:
        LiDARCloud instance
    """
    return LiDARCloud()
