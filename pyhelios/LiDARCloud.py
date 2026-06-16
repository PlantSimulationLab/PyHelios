"""
LiDARCloud - High-level interface for LiDAR simulation and point cloud processing

Provides Python interface to Helios LiDAR plugin for:
- Synthetic LiDAR scanning
- Point cloud management and filtering
- Triangulation and mesh generation
- Leaf area density calculations
"""

from enum import IntEnum
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


class ScanPattern(IntEnum):
    """Scan pattern returned by :meth:`LiDARCloud.getScanPattern`.

    RASTER is the uniform-angular-grid pattern produced by :meth:`LiDARCloud.addScan`;
    SPINNING_MULTIBEAM is the rotating multi-channel pattern produced by
    :meth:`LiDARCloud.addScanMultibeam`.
    """
    RASTER = 0
    SPINNING_MULTIBEAM = 1


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
                exit_diameter: float, beam_divergence: float,
                column_format: Optional[List[str]] = None,
                range_noise_stddev: float = 0.0, angle_noise_stddev: float = 0.0,
                scan_tilt_roll: float = 0.0, scan_tilt_pitch: float = 0.0,
                scan_azimuth_offset: float = 0.0) -> int:
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
            column_format: Optional list of column-format labels. Non-standard labels
                (anything other than geometry/standard tokens like x/y/z/r/g/b/raydir)
                cause syntheticScan to sample that named primitive data from the struck
                primitive onto each hit's data map, retrievable via getHitData(). Defaults
                to None (empty format).

                One label is special: "reflectivity_lidar" modulates each hit's "intensity"
                (intensity *= reflectivity) rather than being stored as its own hit-data
                key, so getHitData(i, "reflectivity_lidar") will NOT return it.
            range_noise_stddev: Standard deviation of Gaussian range (along-beam) measurement
                noise in meters. Only affects synthetic-scan generation. Defaults to 0.0
                (noise disabled).
            angle_noise_stddev: Standard deviation of Gaussian angular (beam-pointing) jitter
                in radians. Only affects synthetic-scan generation. Defaults to 0.0 (jitter
                disabled).
            scan_tilt_roll: Global scanner tilt roll angle in radians, modeling residual tilt of
                the scanner spin axis away from plumb (right-hand rotation about the body lateral
                axis). Only affects synthetic-scan generation. Defaults to 0.0 (level).
            scan_tilt_pitch: Global scanner tilt pitch angle in radians (right-hand rotation about
                the body forward/azimuth-zero axis). Only affects synthetic-scan generation.
                Defaults to 0.0 (level).
            scan_azimuth_offset: Global scanner azimuth (heading) offset in radians, a right-hand
                rotation about the world +z axis applied on top of the azimuth sweep. Only affects
                synthetic-scan generation. Defaults to 0.0 (no offset).

        Returns:
            Scan ID for referencing this scan

        Example:
            >>> scan_id = lidar.addScan(
            ...     origin=vec3(0, 0, 1),
            ...     Ntheta=100, theta_range=(0, 1.57),
            ...     Nphi=100, phi_range=(-3.14, 3.14),
            ...     exit_diameter=0.01, beam_divergence=0.001,
            ...     column_format=["my_scalar"]
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

        if column_format is not None:
            if not isinstance(column_format, (list, tuple)) or \
                    not all(isinstance(c, str) for c in column_format):
                raise ValueError("column_format must be a list of strings")
            column_format = list(column_format)

        if range_noise_stddev < 0:
            raise ValueError("range_noise_stddev must be non-negative")
        if angle_noise_stddev < 0:
            raise ValueError("angle_noise_stddev must be non-negative")

        return lidar_wrapper.addLiDARScan(
            self._cloud_ptr, origin_list, Ntheta, theta_range,
            Nphi, phi_range, exit_diameter, beam_divergence, column_format,
            range_noise_stddev, angle_noise_stddev,
            scan_tilt_roll, scan_tilt_pitch, scan_azimuth_offset
        )

    def addScanMultibeam(self, origin: Union[vec3, List[float], Tuple[float, float, float]],
                         beam_zenith_angles: List[float],
                         Nphi: int, phi_range: Tuple[float, float],
                         exit_diameter: float, beam_divergence: float,
                         column_format: Optional[List[str]] = None,
                         range_noise_stddev: float = 0.0, angle_noise_stddev: float = 0.0,
                         scan_tilt_roll: float = 0.0, scan_tilt_pitch: float = 0.0,
                         scan_azimuth_offset: float = 0.0) -> int:
        """
        Add a spinning multibeam LiDAR scan (rotating multi-channel sensor, e.g. Velodyne/Ouster/Hesai).

        Each laser channel is fired at a fixed zenith angle (taken from ``beam_zenith_angles``) as the
        sensor head rotates through ``Nphi`` uniform azimuth steps. The scan is stored as an
        (len(beam_zenith_angles) x Nphi) table, so all downstream processing is shared with raster scans.

        Args:
            origin: Scanner position (vec3 or 3-element list/tuple)
            beam_zenith_angles: Per-channel zenith angles in radians (0 = upward, pi/2 = horizontal,
                pi = downward). Manufacturer spec sheets typically list channel angles as elevation
                above the horizon; zenith = pi/2 - elevation. Its length sets Ntheta (number of channels).
            Nphi: Number of azimuth steps (columns) per rotation
            phi_range: Azimuthal angle range (min, max) in radians
            exit_diameter: Laser beam exit diameter (meters)
            beam_divergence: Beam divergence angle (radians)
            column_format: Optional list of column-format labels (see addScan)
            range_noise_stddev: Std. dev. of Gaussian range noise in meters (default 0)
            angle_noise_stddev: Std. dev. of Gaussian angular jitter in radians (default 0)
            scan_tilt_roll: Global scanner tilt roll angle in radians (default 0, level)
            scan_tilt_pitch: Global scanner tilt pitch angle in radians (default 0, level)
            scan_azimuth_offset: Global scanner azimuth (heading) offset in radians, a right-hand
                rotation about the world +z axis applied on top of the azimuth sweep (default 0, no offset)

        Returns:
            Scan ID for referencing this scan
        """
        if isinstance(origin, (list, tuple)):
            if len(origin) != 3:
                raise ValueError("Origin must have 3 elements [x, y, z]")
            origin = vec3(*origin)
        elif not hasattr(origin, 'x'):
            raise ValueError("Origin must be vec3 or 3-element list/tuple")

        origin_list = [origin.x, origin.y, origin.z]

        if not isinstance(beam_zenith_angles, (list, tuple)) or len(beam_zenith_angles) == 0:
            raise ValueError("beam_zenith_angles must be a non-empty list of per-channel angles")
        if not all(isinstance(a, (int, float)) for a in beam_zenith_angles):
            raise ValueError("beam_zenith_angles must be a list of numbers (radians)")

        validate_positive_value(Nphi, 'Nphi', 'addScanMultibeam')

        if not isinstance(phi_range, (list, tuple)) or len(phi_range) != 2:
            raise ValueError("phi_range must be a tuple (min, max)")

        if column_format is not None:
            if not isinstance(column_format, (list, tuple)) or \
                    not all(isinstance(c, str) for c in column_format):
                raise ValueError("column_format must be a list of strings")
            column_format = list(column_format)

        if range_noise_stddev < 0:
            raise ValueError("range_noise_stddev must be non-negative")
        if angle_noise_stddev < 0:
            raise ValueError("angle_noise_stddev must be non-negative")

        return lidar_wrapper.addLiDARScanMultibeam(
            self._cloud_ptr, origin_list, list(beam_zenith_angles),
            Nphi, phi_range, exit_diameter, beam_divergence, column_format,
            range_noise_stddev, angle_noise_stddev,
            scan_tilt_roll, scan_tilt_pitch, scan_azimuth_offset
        )

    def addScanMoving(self, Ntheta: int, theta_range: Tuple[float, float],
                      Nphi: int, phi_range: Tuple[float, float],
                      exit_diameter: float, beam_divergence: float,
                      traj_t: List[float],
                      traj_pos: List[Union[vec3, List[float], Tuple[float, float, float]]],
                      traj_rot: List[List[float]], pulse_rate_hz: float,
                      rot_is_quaternion: bool = True,
                      lever_arm: Optional[Union[vec3, List[float], Tuple[float, float, float]]] = None,
                      boresight_rpy: Optional[Union[vec3, List[float], Tuple[float, float, float]]] = None,
                      column_format: Optional[List[str]] = None,
                      range_noise_stddev: float = 0.0, angle_noise_stddev: float = 0.0,
                      t0: float = 0.0) -> int:
        """
        Add a moving-platform (mobile/airborne) raster LiDAR scan driven by a 6-DOF pose trajectory.

        Unlike :meth:`addScan`, the scanner pose changes during the sweep. For each pulse the synthetic-scan
        generator computes its acquisition time ``t = t0 + ordinal / pulse_rate_hz``, interpolates the platform
        pose at that time (linear position, SLERP orientation), and emits a per-pulse origin
        ``o = pos + R(q) * lever_arm`` and direction ``d = R(q) * R(boresight) * d_body``. Every resulting hit
        and miss stores its own origin (hit-data "origin_x"/"origin_y"/"origin_z", retrievable via
        :meth:`getHitOrigin`), timestamp ("timestamp"), and firing index ("pulse_id").

        The static tilt roll/pitch/azimuth fields are NOT applied in this mode; attitude comes entirely
        from the trajectory and the boresight misalignment. Because the pulses do not lie on a fixed
        theta-phi grid they cannot be triangulated, so leaf-area inversion must use
        :meth:`calculateLeafArea` with an explicit ``Gtheta``.

        Args:
            Ntheta: Number of scan points in zenith direction (raster grid rows)
            theta_range: Zenith angle range (min, max) in radians
            Nphi: Number of scan points in azimuthal direction (raster grid columns)
            phi_range: Azimuthal angle range (min, max) in radians
            exit_diameter: Laser beam exit diameter (meters)
            beam_divergence: Beam divergence angle (radians)
            traj_t: Monotonically increasing trajectory sample times in seconds (length M)
            traj_pos: Platform positions in world coordinates, one [x, y, z] (or vec3) per traj_t entry
            traj_rot: Platform orientations, one entry per traj_t entry. Each entry is a length-4
                quaternion (qx, qy, qz, qw, Hamilton body->world) when ``rot_is_quaternion`` is True,
                otherwise a length-3 roll/pitch/yaw Euler triple in radians (intrinsic Z-Y-X).
            pulse_rate_hz: Pulse repetition rate in Hz (must be > 0)
            rot_is_quaternion: Whether traj_rot holds quaternions (default True) or Euler angles
            lever_arm: Sensor optical center in the platform body frame [x, y, z] meters (default origin)
            boresight_rpy: Fixed sensor rotational misalignment [roll, pitch, yaw] radians (default 0)
            column_format: Optional list of column-format labels (see addScan)
            range_noise_stddev: Std. dev. of Gaussian range noise in meters (default 0)
            angle_noise_stddev: Std. dev. of Gaussian angular jitter in radians (default 0)
            t0: Time of the first pulse in seconds (relative time; default 0)

        Returns:
            Scan ID for referencing this scan
        """
        validate_positive_value(Ntheta, 'Ntheta', 'addScanMoving')
        validate_positive_value(Nphi, 'Nphi', 'addScanMoving')

        if not isinstance(theta_range, (list, tuple)) or len(theta_range) != 2:
            raise ValueError("theta_range must be a tuple (min, max)")
        if not isinstance(phi_range, (list, tuple)) or len(phi_range) != 2:
            raise ValueError("phi_range must be a tuple (min, max)")

        if not isinstance(traj_t, (list, tuple)) or len(traj_t) == 0:
            raise ValueError("traj_t must be a non-empty list of trajectory sample times")
        M = len(traj_t)
        if len(traj_pos) != M or len(traj_rot) != M:
            raise ValueError("traj_t, traj_pos, and traj_rot must all have length M")
        if pulse_rate_hz <= 0:
            raise ValueError("pulse_rate_hz must be greater than 0")
        # Fail fast on a non-monotonic trajectory rather than deferring to a C++
        # exception inside poseAt() at syntheticScan time.
        if any(traj_t[i] >= traj_t[i + 1] for i in range(M - 1)):
            raise ValueError("traj_t must be strictly monotonically increasing")

        def _to_xyz(v, name):
            if hasattr(v, 'x'):
                return [v.x, v.y, v.z]
            if isinstance(v, (list, tuple)) and len(v) == 3:
                return [float(c) for c in v]
            raise ValueError(f"{name} must be a vec3 or 3-element list/tuple")

        pos_list = [_to_xyz(p, "Each traj_pos entry") for p in traj_pos]

        rot_stride = 4 if rot_is_quaternion else 3
        rot_list = []
        for r in traj_rot:
            if not isinstance(r, (list, tuple)) or len(r) != rot_stride:
                raise ValueError(
                    f"Each traj_rot entry must have {rot_stride} elements "
                    f"({'qx,qy,qz,qw' if rot_is_quaternion else 'roll,pitch,yaw'})"
                )
            rot_list.append([float(c) for c in r])

        lever_list = _to_xyz(lever_arm, "lever_arm") if lever_arm is not None else None
        boresight_list = _to_xyz(boresight_rpy, "boresight_rpy") if boresight_rpy is not None else None

        if column_format is not None:
            if not isinstance(column_format, (list, tuple)) or \
                    not all(isinstance(c, str) for c in column_format):
                raise ValueError("column_format must be a list of strings")
            column_format = list(column_format)

        if range_noise_stddev < 0:
            raise ValueError("range_noise_stddev must be non-negative")
        if angle_noise_stddev < 0:
            raise ValueError("angle_noise_stddev must be non-negative")

        return lidar_wrapper.addLiDARScanMoving(
            self._cloud_ptr, Ntheta, theta_range, Nphi, phi_range,
            exit_diameter, beam_divergence,
            [float(t) for t in traj_t], pos_list, rot_list, bool(rot_is_quaternion),
            float(pulse_rate_hz), lever_list, boresight_list, column_format,
            range_noise_stddev, angle_noise_stddev, float(t0)
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

    def getScanRangeNoiseStdDev(self, scanID: int) -> float:
        """Get the range (along-beam) measurement noise standard deviation for a scan (meters).

        Returns the value supplied to addScan() as ``range_noise_stddev`` (0.0 if disabled).
        """
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        return lidar_wrapper.getLiDARScanRangeNoiseStdDev(self._cloud_ptr, scanID)

    def getScanAngleNoiseStdDev(self, scanID: int) -> float:
        """Get the angular (beam-pointing) jitter standard deviation for a scan (radians).

        Returns the value supplied to addScan() as ``angle_noise_stddev`` (0.0 if disabled).
        """
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        return lidar_wrapper.getLiDARScanAngleNoiseStdDev(self._cloud_ptr, scanID)

    def getScanTiltRoll(self, scanID: int) -> float:
        """Get the global scanner tilt roll angle for a scan (radians; 0.0 if level)."""
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        return lidar_wrapper.getLiDARScanTiltRoll(self._cloud_ptr, scanID)

    def getScanTiltPitch(self, scanID: int) -> float:
        """Get the global scanner tilt pitch angle for a scan (radians; 0.0 if level)."""
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        return lidar_wrapper.getLiDARScanTiltPitch(self._cloud_ptr, scanID)

    def getScanAzimuthOffset(self, scanID: int) -> float:
        """Get the global scanner azimuth (heading) offset for a scan (radians; 0.0 if none)."""
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        return lidar_wrapper.getLiDARScanAzimuthOffset(self._cloud_ptr, scanID)

    def getScanPattern(self, scanID: int) -> int:
        """Get the scan pattern for a scan.

        Returns an integer: 0 = raster (uniform angular grid), 1 = spinning multibeam
        (rotating multi-channel sensor). Compare against ``ScanPattern.RASTER`` /
        ``ScanPattern.SPINNING_MULTIBEAM``.
        """
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        return lidar_wrapper.getLiDARScanPattern(self._cloud_ptr, scanID)

    def getScanBeamZenithAngles(self, scanID: int) -> List[float]:
        """Get the per-channel beam zenith angles (radians) for a multibeam scan.

        Returns an empty list for a raster scan.
        """
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        return lidar_wrapper.getLiDARScanBeamZenithAngles(self._cloud_ptr, scanID)

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

    def addHitPoints(self, scanID: int, xyz_array, direction_array, color_array=None):
        """
        Add many hit points to the point cloud in a single bulk call.

        This skips the per-point Python loop by passing contiguous buffers
        straight to the native library in one FFI call.

        Args:
            scanID: Scan ID these hits belong to
            xyz_array: Hit point coordinates, shape (N, 3) [x, y, z]
            direction_array: Ray directions, shape (N, 3) [radius, elevation, azimuth]
                             (azimuth is currently ignored, matching addHitPoint)
            color_array: Optional RGB colors, shape (N, 3) [r, g, b]
        """
        import numpy as np

        xyz_array = np.ascontiguousarray(xyz_array, dtype=np.float32)
        direction_array = np.ascontiguousarray(direction_array, dtype=np.float32)

        if xyz_array.ndim != 2 or xyz_array.shape[1] != 3:
            raise ValueError("xyz_array must have shape (N, 3)")
        if direction_array.ndim != 2 or direction_array.shape[1] != 3:
            raise ValueError("direction_array must have shape (N, 3)")

        count = xyz_array.shape[0]
        if direction_array.shape[0] != count:
            raise ValueError("xyz_array and direction_array must have the same number of rows")

        if color_array is not None:
            color_array = np.ascontiguousarray(color_array, dtype=np.float32)
            if color_array.ndim != 2 or color_array.shape[1] != 3:
                raise ValueError("color_array must have shape (N, 3)")
            if color_array.shape[0] != count:
                raise ValueError("color_array must have the same number of rows as xyz_array")

        lidar_wrapper.addLiDARHitPoints(self._cloud_ptr, scanID,
                                        xyz_array, direction_array, count, color_array)

    def addHitPointsWithData(self, scanID: int, xyz_array, direction_array,
                             data_labels=None, data_values=None, color_array=None):
        """
        Add many hit points carrying a per-hit data map in a single bulk call.

        Like addHitPoints, but also populates each hit's named-scalar data map —
        the in-memory equivalent of what the ASCII loader does for non-standard
        columns. This is the path multi-return LAD needs (timestamp/target_index/
        target_count land in the map so gapfillMisses() can group beams by pulse).

        Args:
            scanID: Scan ID these hits belong to (the scan must already exist)
            xyz_array: Hit point coordinates, shape (N, 3) [x, y, z]
            direction_array: Ray directions, shape (N, 3) [radius, elevation, azimuth].
                             Pass cart2sphere(xyz - origin) to match loadASCIIFile;
                             the full SphericalCoord (incl. radius) is used.
            data_labels: Optional list of data-map key names (length k)
            data_values: Optional (N, k) values for those keys (float64)
            color_array: Optional RGB colors, shape (N, 3) [r, g, b]
        """
        import numpy as np

        xyz_array = np.ascontiguousarray(xyz_array, dtype=np.float32)
        direction_array = np.ascontiguousarray(direction_array, dtype=np.float32)

        if xyz_array.ndim != 2 or xyz_array.shape[1] != 3:
            raise ValueError("xyz_array must have shape (N, 3)")
        if direction_array.ndim != 2 or direction_array.shape[1] != 3:
            raise ValueError("direction_array must have shape (N, 3)")

        count = xyz_array.shape[0]
        if direction_array.shape[0] != count:
            raise ValueError("xyz_array and direction_array must have the same number of rows")

        labels = list(data_labels or [])
        if labels:
            data_values = np.ascontiguousarray(data_values, dtype=np.float64)
            if data_values.ndim != 2 or data_values.shape != (count, len(labels)):
                raise ValueError("data_values must have shape (N, len(data_labels))")
        else:
            data_values = None

        if color_array is not None:
            color_array = np.ascontiguousarray(color_array, dtype=np.float32)
            if color_array.ndim != 2 or color_array.shape[1] != 3:
                raise ValueError("color_array must have shape (N, 3)")
            if color_array.shape[0] != count:
                raise ValueError("color_array must have the same number of rows as xyz_array")

        lidar_wrapper.addLiDARHitPointsWithData(
            self._cloud_ptr, scanID, xyz_array, direction_array, count,
            color_array, labels, data_values)

    def getHitCount(self) -> int:
        """Get total number of hit points in cloud"""
        return lidar_wrapper.getLiDARHitCount(self._cloud_ptr)

    def getHitXYZ(self, index: int) -> vec3:
        """Get coordinates of a hit point"""
        if index < 0:
            raise ValueError("Index must be non-negative")
        xyz_list = lidar_wrapper.getLiDARHitXYZ(self._cloud_ptr, index)
        return vec3(*xyz_list)

    def getHitOrigin(self, index: int) -> vec3:
        """Get the (x,y,z) beam-emission origin of a hit point.

        For moving-platform scans (see :meth:`addScanMoving`) this is the per-pulse emission origin
        recorded on the hit; for static scans it falls back to the single scan origin of the hit's scan.
        """
        if index < 0:
            raise ValueError("Index must be non-negative")
        xyz_list = lidar_wrapper.getLiDARHitOrigin(self._cloud_ptr, index)
        return vec3(*xyz_list)

    def getHitRaydir(self, index: int) -> SphericalCoord:
        """Get ray direction of a hit point"""
        if index < 0:
            raise ValueError("Index must be non-negative")
        direction_list = lidar_wrapper.getLiDARHitRaydir(self._cloud_ptr, index)
        # direction_list is [radius, elevation, azimuth]; preserve azimuth (was previously dropped).
        return SphericalCoord(direction_list[0], direction_list[1], direction_list[2])

    def getHitColor(self, index: int) -> RGBcolor:
        """Get color of a hit point"""
        if index < 0:
            raise ValueError("Index must be non-negative")
        color_list = lidar_wrapper.getLiDARHitColor(self._cloud_ptr, index)
        return RGBcolor(*color_list)

    def getHitScanID(self, index: int) -> int:
        """Get the scan ID a hit point belongs to"""
        if index < 0:
            raise ValueError("Index must be non-negative")
        return lidar_wrapper.getLiDARHitScanID(self._cloud_ptr, index)

    def doesHitDataExist(self, index: int, label: str) -> bool:
        """Check whether a named scalar data value exists for a hit point.

        Per-hit data computed by syntheticScan includes 'intensity', 'distance',
        'timestamp', 'target_index', 'target_count', 'deviation', 'nRaysHit', plus any
        primitive-data labels listed in the scan's column_format.
        """
        if index < 0:
            raise ValueError("Index must be non-negative")
        return lidar_wrapper.doesLiDARHitDataExist(self._cloud_ptr, index, label)

    def getHitData(self, index: int, label: str) -> float:
        """Get a named scalar data value for a hit point.

        Raises HeliosError if the label does not exist for this hit; guard with
        doesHitDataExist() when unsure.
        """
        if index < 0:
            raise ValueError("Index must be non-negative")
        return lidar_wrapper.getLiDARHitData(self._cloud_ptr, index, label)

    def getHitDataAll(self, label: str) -> List[float]:
        """Bulk-export a named scalar data value for all hits in a single FFI call.

        Returns a list of length getHitCount(); entries are NaN where the label is
        absent for that hit. Much faster than looping getHitData() for large clouds.

        Note: values are returned at float32 precision (vs. getHitData(), which returns
        full float64). Use getHitData() per-hit if full precision is required.
        """
        n = self.getHitCount()
        if n == 0:
            return []
        return lidar_wrapper.getLiDARHitData_all(self._cloud_ptr, label, n)

    def getHitsXYZRGB(self) -> Tuple[List[vec3], List[RGBcolor]]:
        """Bulk-export coordinates and colors for all hits in a single FFI call.

        Returns (positions, colors) where positions is a list of vec3 and colors a list
        of RGBcolor, each of length getHitCount(). Much faster than looping
        getHitXYZ()/getHitColor() for large clouds.
        """
        n = self.getHitCount()
        if n == 0:
            return [], []
        xyz_flat, rgb_flat = lidar_wrapper.getLiDARHitsXYZRGB_all(self._cloud_ptr, n)
        positions = [vec3(xyz_flat[3 * i], xyz_flat[3 * i + 1], xyz_flat[3 * i + 2]) for i in range(n)]
        colors = [RGBcolor(rgb_flat[3 * i], rgb_flat[3 * i + 1], rgb_flat[3 * i + 2]) for i in range(n)]
        return positions, colors

    # ---- Bulk numpy exports (single FFI call each; no per-hit Python loop) ----
    # These power the synthetic-scan fast path: extracting a million-hit cloud via
    # the per-index getters (getHitXYZ/getHitColor/getHitScanID/...) costs tens of
    # millions of FFI crossings, which dominated scan time. The *Array methods pull
    # each quantity in one contiguous copy.

    def getHitsXYZRGBArrays(self):
        """Bulk-export hit coordinates + colors as numpy arrays.

        Returns (xyz, rgb), each (getHitCount(), 3) float32. Empty (0,3) arrays
        when there are no hits.
        """
        import numpy as np
        n = self.getHitCount()
        if n == 0:
            return np.empty((0, 3), np.float32), np.empty((0, 3), np.float32)
        return lidar_wrapper.getLiDARHitsXYZRGB_all_np(self._cloud_ptr, n)

    def getHitDataArray(self, label: str):
        """Bulk-export a named scalar field as an (getHitCount(),) float32 array,
        NaN where the label is absent for a hit."""
        import numpy as np
        n = self.getHitCount()
        if n == 0:
            return np.empty((0,), np.float32)
        return lidar_wrapper.getLiDARHitData_all_np(self._cloud_ptr, label, n)

    def getHitScanIDArray(self):
        """Bulk-export the scan ID of every hit as an (getHitCount(),) int32 array."""
        import numpy as np
        n = self.getHitCount()
        if n == 0:
            return np.empty((0,), np.int32)
        return lidar_wrapper.getLiDARHitScanID_all(self._cloud_ptr, n)

    def getHitMissArray(self):
        """Bulk-export the miss flag of every hit as an (getHitCount(),) int32
        array (1 == sky/miss, 0 == real surface return)."""
        import numpy as np
        n = self.getHitCount()
        if n == 0:
            return np.empty((0,), np.int32)
        return lidar_wrapper.isLiDARHitMiss_all(self._cloud_ptr, n)

    def deleteHitPoint(self, index: int):
        """Delete a hit point from the cloud"""
        if index < 0:
            raise ValueError("Index must be non-negative")
        lidar_wrapper.deleteLiDARHitPoint(self._cloud_ptr, index)

    def isHitMiss(self, index: int) -> bool:
        """Return True if a hit is a "miss" (a fired pulse that returned nothing).

        Misses are the transmitted beams that form the denominator of the per-voxel
        transmission probability used by :meth:`calculateLeafArea`. They are produced by
        ``syntheticScan(..., record_misses=True)`` and by :meth:`gapfillMisses`.
        """
        if index < 0:
            raise ValueError("Index must be non-negative")
        return lidar_wrapper.isLiDARHitMiss(self._cloud_ptr, index)

    def hasMisses(self) -> bool:
        """Return True if the cloud contains at least one miss.

        :meth:`calculateLeafArea` requires misses and fails fast without them.
        """
        return lidar_wrapper.lidarHasMisses(self._cloud_ptr)

    @staticmethod
    def getMissDistance() -> float:
        """Return the LIDAR_MISS_DISTANCE constant (meters): the distance at which a
        miss point is placed along its beam."""
        return lidar_wrapper.getLiDARMissDistance()

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

    def getTriangulationStats(self) -> dict:
        """Filter diagnostics from the most recent triangulateHitPoints() call.

        Returns a dict::

            {"candidates", "dropped_lmax", "dropped_aspect", "dropped_degenerate"}

        Each dropped triangle is attributed to one primary reason (Lmax, then
        aspect, then degenerate), so ``candidates == getTriangleCount() +
        dropped_lmax + dropped_aspect + dropped_degenerate``. All zero if
        triangulation has not been run. Use this to tell whether an empty or
        sparse mesh is data-limited (few candidates) or filter-limited (many
        candidates dropped by Lmax/aspect).
        """
        return lidar_wrapper.getLiDARTriangulationStats(self._cloud_ptr)

    def getTriangleVerticesAll(self):
        """Bulk-export every triangle's vertices and source scan in one call.

        Returns (xyz_flat, scan_ids): xyz_flat is a (T*9,) float32 array laid out
        [v0x,v0y,v0z, v1x,v1y,v1z, v2x,v2y,v2z] per triangle, scan_ids is a (T,)
        int32 array. Avoids the Context round-trip and the per-triangle
        getPrimitiveVertices loop.
        """
        return lidar_wrapper.getLiDARTriangleVertices_all(
            self._cloud_ptr, self.getTriangleCount())

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

    def exportPointCloud(self, filename: str, write_header: bool = True):
        """Export point cloud to ASCII file.

        Args:
            filename: Output file path.
            write_header: If True (default), prepend a ``#``-prefixed comment line listing the
                column field names (CloudCompare convention). The loader skips ``#``-prefixed
                lines, so headered files round-trip through ``loadXML()``. Set False for a
                bare data file.
        """
        if not filename:
            raise ValueError("Filename cannot be empty")
        lidar_wrapper.exportLiDARPointCloud(self._cloud_ptr, filename, write_header)

    def exportLeafAreaUncertainty(self, filename: str):
        """Export per-voxel leaf-area sampling uncertainty to a self-describing ASCII file.

        The file has a ``#``-prefixed header and one row per grid cell:
        ``cell_index leaf_area beam_count I_rdi LAD_std_error ci_valid``. Requires that
        :meth:`calculateLeafArea` has been run with an ``element_width`` (the uncertainty
        overload).
        """
        if not filename:
            raise ValueError("Filename cannot be empty")
        lidar_wrapper.exportLiDARLeafAreaUncertainty(self._cloud_ptr, filename)

    def exportScans(self, filename: str):
        """Export all scans to an XML metadata file plus one ASCII data file per scan.

        Args:
            filename: Path of the XML metadata file to write (e.g. "output/scans.xml").
                One ASCII data file is auto-generated per scan, named by stripping the XML
                extension and appending "_<scanID>.xyz" (e.g. "output/scans_0.xyz"). The
                resulting XML can be re-loaded with loadXML() from the same working directory.
        """
        if not filename:
            raise ValueError("Filename cannot be empty")
        lidar_wrapper.exportLiDARScans(self._cloud_ptr, filename)

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

    def getCellBeamCount(self, index: int) -> int:
        """Get the beam count N that entered a grid cell during the leaf-area inversion.

        Returns -1 if :meth:`calculateLeafArea` has not been run for this cell.
        """
        if index < 0:
            raise ValueError("Index must be non-negative")
        return lidar_wrapper.getLiDARCellBeamCount(self._cloud_ptr, index)

    def getCellRelativeDensityIndex(self, index: int) -> float:
        """Get the relative density index (I_rdi) for a grid cell."""
        if index < 0:
            raise ValueError("Index must be non-negative")
        return lidar_wrapper.getLiDARCellRelativeDensityIndex(self._cloud_ptr, index)

    def getCellMeanPathLength(self, index: int) -> float:
        """Get the mean beam path length (m) through a grid cell."""
        if index < 0:
            raise ValueError("Index must be non-negative")
        return lidar_wrapper.getLiDARCellMeanPathLength(self._cloud_ptr, index)

    def getCellLADVariance(self, index: int) -> float:
        """Get the per-voxel LAD sampling variance for a grid cell.

        Returns -1 if uncertainty has not been computed (call :meth:`calculateLeafArea`
        with an ``element_width``).
        """
        if index < 0:
            raise ValueError("Index must be non-negative")
        return lidar_wrapper.getLiDARCellLADVariance(self._cloud_ptr, index)

    def getCellLeafAreaConfidenceInterval(self, index: int, confidence_level: float = 0.95):
        """Get the leaf-area confidence interval for a single grid cell.

        Returns a ``(valid, lower, upper)`` tuple. ``valid`` is False when the interval is
        gated out by the Pimont validity envelope (single-voxel intervals are often
        untrustworthy; prefer :meth:`getGroupLADConfidenceInterval`). Requires
        :meth:`calculateLeafArea` to have been run with an ``element_width``.
        """
        if index < 0:
            raise ValueError("Index must be non-negative")
        return lidar_wrapper.getLiDARCellLeafAreaConfidenceInterval(
            self._cloud_ptr, index, confidence_level)

    def getGroupLADConfidenceInterval(self, indices: List[int], confidence_level: float = 0.95):
        """Get the group-scale LAD confidence interval over a set of grid cells (recommended).

        Returns a ``(valid, mean_lad, lower, upper)`` tuple (Pimont et al. 2018, Eq. 39,
        assuming voxel independence). Requires :meth:`calculateLeafArea` to have been run
        with an ``element_width``.
        """
        if not indices:
            raise ValueError("indices must contain at least one cell index")
        if any(i < 0 for i in indices):
            raise ValueError("Cell indices must be non-negative")
        return lidar_wrapper.getLiDARGroupLADConfidenceInterval(
            self._cloud_ptr, indices, confidence_level)

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
            # Honor scan_grid_only and record_misses for discrete scans too. record_misses
            # defaults to True so the cloud carries the transmitted beams that
            # calculateLeafArea() requires.
            lidar_wrapper.syntheticLiDARScanDiscrete(
                self._cloud_ptr, context_ptr, scan_grid_only, record_misses, append)
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

    def calculateLeafArea(self, context: Context, min_voxel_hits: Optional[int] = None,
                          element_width: Optional[float] = None, Gtheta: Optional[float] = None):
        """
        Calculate leaf area for each grid cell.

        Requires triangulation to have been performed first, UNLESS a ``Gtheta`` is supplied
        (see below).

        .. note::
            The cloud must contain misses (transmitted beams that returned nothing) — the
            inversion fails fast without them. Misses are produced by
            ``syntheticScan(..., record_misses=True)`` (the default) or by
            :meth:`gapfillMisses`. Use :meth:`hasMisses` to check.

        Args:
            context: Helios Context instance
            min_voxel_hits: Optional minimum number of hits required per voxel
            element_width: Optional characteristic vegetation element width (meters). When
                provided, per-voxel sampling uncertainty (Pimont et al. 2018) is computed
                alongside the leaf-area estimate and becomes available via
                :meth:`getCellLADVariance`, :meth:`getCellLeafAreaConfidenceInterval`, and
                :meth:`getGroupLADConfidenceInterval`. ``element_width <= 0`` yields a
                sampling-only variance.
            Gtheta: Optional caller-supplied mean leaf-projection coefficient G(theta), in (0,1]
                (0.5 = spherical/random leaf-angle distribution). When provided, leaf area is
                computed via a beam-based inversion that uses each hit's per-pulse beam origin and
                does NOT require triangulation — the only supported path for moving-platform scans
                (see :meth:`addScanMoving`). Requires both ``min_voxel_hits`` and ``element_width``
                to also be specified.

        Example:
            >>> from pyhelios import Context, LiDARCloud
            >>> with Context() as context:
            ...     with LiDARCloud() as lidar:
            ...         # ... load data, add grid, triangulate ...
            ...         lidar.calculateLeafArea(context)
        """
        if not isinstance(context, Context):
            raise TypeError("context must be a Context instance")

        # Validate argument combinations before touching native state (fail-fast).
        if Gtheta is not None:
            if min_voxel_hits is None or element_width is None:
                raise ValueError(
                    "Gtheta requires both min_voxel_hits and element_width to also be specified "
                    "(the G(theta) overload takes all three)")
            if Gtheta <= 0:
                # The native overload treats Gtheta <= 0 as the "compute from triangulation"
                # sentinel, which silently disables the supplied-G(theta) path. Reject it here.
                raise ValueError(
                    "Gtheta must be > 0 and in (0, 1] (e.g. 0.5 for a spherical leaf-angle distribution)")
        elif element_width is not None and min_voxel_hits is None:
            raise ValueError(
                "element_width requires min_voxel_hits to also be specified "
                "(the uncertainty overload takes both)")

        context_ptr = context.getNativePtr()
        if Gtheta is not None:
            lidar_wrapper.calculateLiDARLeafAreaGtheta(
                self._cloud_ptr, context_ptr, Gtheta, min_voxel_hits, element_width)
        elif element_width is not None:
            lidar_wrapper.calculateLiDARLeafAreaUncertainty(
                self._cloud_ptr, context_ptr, min_voxel_hits, element_width)
        elif min_voxel_hits is None:
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
