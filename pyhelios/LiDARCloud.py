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
from .Context import Context, check_context_alive
from .plugins.registry import get_plugin_registry
from .exceptions import HeliosError
from .wrappers.DataTypes import vec3, RGBcolor, SphericalCoord
from .validation.datatypes import validate_vec3
from .validation.core import validate_positive_value


class LiDARError(HeliosError):
    """Exception raised for LiDAR-specific errors"""
    pass


class ScanPattern(IntEnum):
    """Geometric beam pattern returned by :meth:`LiDARCloud.getScanPattern`.

    RASTER is the uniform-angular-grid pattern produced by :meth:`LiDARCloud.addScan`;
    SPINNING_MULTIBEAM is the rotating multi-channel pattern produced by
    :meth:`LiDARCloud.addScanSpinning` (each row is a laser channel at a fixed zenith angle).

    This is the geometric pattern, orthogonal to :class:`ScanMode` (the acquisition mode). Use
    :meth:`LiDARCloud.getScanBeamZenithAngles` to read a spinning scan's per-channel angles.
    """
    RASTER = 0
    SPINNING_MULTIBEAM = 1
    #: Rotating-Risley-prism rosette (Livox-style), produced by :meth:`LiDARCloud.addScanRisley`.
    #: Stored as a single-row (Ntheta=1) table; the per-pulse direction comes from the prism optics.
    RISLEY_PRISM = 2


class ScanMode(IntEnum):
    """High-level acquisition mode returned by :meth:`LiDARCloud.getScanMode`.

    STATIC_RASTER is a uniform angular grid from a single fixed origin (terrestrial/tripod);
    MOVING_RASTER is a fixed angular fan swept along a trajectory (mobile/airborne raster),
    produced by :meth:`LiDARCloud.addScanMovingRaster`; SPINNING is a continuously-rotating
    multi-channel sensor, produced by :meth:`LiDARCloud.addScanSpinning`.
    """
    STATIC_RASTER = 0
    MOVING_RASTER = 1
    SPINNING = 2
    #: Rotating-Risley-prism rosette sensor (Livox-style; always trajectory-driven), produced by
    #: :meth:`LiDARCloud.addScanRisley`. A stationary capture is two coincident poses separated in time.
    RISLEY_PRISM = 3


class RisleyPrism:
    """A single rotating wedge prism in a Risley-prism beam deflector (see :meth:`LiDARCloud.addScanRisley`).

    A pair of such prisms with different (and generally incommensurate) rotation rates traces the
    characteristic non-repetitive rosette of a Livox sensor. The beam direction is computed by
    non-paraxial ray tracing through the wedges; the field of view is an emergent property of the
    wedge angles and refractive indices, not a directly specified parameter.

    Args:
        wedge_angle: Wedge (inclination) angle of the prism in radians.
        refractive_index: Refractive index of the prism glass.
        rotor_rate: Rotation rate about the optical axis in radians/second (the sign sets the rotation
            direction; a counter-rotating pair traces a rosette).
        phase: Initial clocking angle of the wedge about the optical axis in radians at scan time t=0.
    """

    __slots__ = ("wedge_angle", "refractive_index", "rotor_rate", "phase")

    def __init__(self, wedge_angle: float, refractive_index: float,
                 rotor_rate: float, phase: float = 0.0):
        self.wedge_angle = float(wedge_angle)
        self.refractive_index = float(refractive_index)
        self.rotor_rate = float(rotor_rate)
        self.phase = float(phase)

    def to_list(self) -> List[float]:
        """Return the prism as a 4-element [wedge_angle, refractive_index, rotor_rate, phase] list."""
        return [self.wedge_angle, self.refractive_index, self.rotor_rate, self.phase]

    def __repr__(self) -> str:
        return (f"RisleyPrism(wedge_angle={self.wedge_angle}, refractive_index={self.refractive_index}, "
                f"rotor_rate={self.rotor_rate}, phase={self.phase})")

    def __eq__(self, other) -> bool:
        if not isinstance(other, RisleyPrism):
            return NotImplemented
        return self.to_list() == other.to_list()


class ReturnMode(IntEnum):
    """Return-reporting mode for analytic-waveform synthetic scans (see
    :meth:`LiDARCloud.getScanReturnMode`/:meth:`LiDARCloud.setScanReturnMode`).

    MULTI reports every detected return (discrete multi-return, no limit); SINGLE reports at
    most :meth:`LiDARCloud.getScanMaxReturns` returns per pulse, selected by the scan's
    :class:`SingleReturnSelection` policy.
    """
    MULTI = 0
    SINGLE = 1


class SingleReturnSelection(IntEnum):
    """Which return(s) a limited-return instrument keeps when a pulse resolves more returns
    than the return limit (see :meth:`LiDARCloud.setScanSingleReturnSelection`).

    The kept subset is always reported nearest-first.
    """
    STRONGEST = 0
    FIRST = 1
    LAST = 2
    #: Dual return: keep the strongest return AND the last (farthest) return of the
    #: pulse, deduplicated to one when they are the same return. Models the
    #: "strongest + last" dual-return mode of real discrete-return scanners.
    #: Intrinsically yields 1 or 2 returns and ignores the per-scan maxReturns.
    STRONGEST_PLUS_LAST = 3


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

        # Keeps the ctypes progress-callback bridge alive while native code holds it (see
        # setProgressCallback); ctypes does not retain a reference on its own.
        self._progress_callback_ref = None

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
        if pulse_rate_hz <= 0:
            raise ValueError("pulse_rate_hz must be greater than 0")
        if range_noise_stddev < 0:
            raise ValueError("range_noise_stddev must be non-negative")
        if angle_noise_stddev < 0:
            raise ValueError("angle_noise_stddev must be non-negative")

        rot_stride = 4 if rot_is_quaternion else 3
        _, pos_list, rot_list = self._validate_trajectory(
            traj_t, traj_pos, traj_rot, rot_stride, 'addScanMoving')

        lever_list = ([lever_arm.x, lever_arm.y, lever_arm.z] if hasattr(lever_arm, 'x')
                      else list(lever_arm)) if lever_arm is not None else None
        boresight_list = ([boresight_rpy.x, boresight_rpy.y, boresight_rpy.z] if hasattr(boresight_rpy, 'x')
                          else list(boresight_rpy)) if boresight_rpy is not None else None

        if column_format is not None:
            if not isinstance(column_format, (list, tuple)) or \
                    not all(isinstance(c, str) for c in column_format):
                raise ValueError("column_format must be a list of strings")
            column_format = list(column_format)

        return lidar_wrapper.addLiDARScanMoving(
            self._cloud_ptr, Ntheta, theta_range, Nphi, phi_range,
            exit_diameter, beam_divergence,
            [float(t) for t in traj_t], pos_list, rot_list, bool(rot_is_quaternion),
            float(pulse_rate_hz), lever_list, boresight_list, column_format,
            range_noise_stddev, angle_noise_stddev, float(t0)
        )

    @staticmethod
    def _validate_trajectory(traj_t, traj_pos, traj_rot, rot_stride, method):
        """Shared trajectory validation/marshalling for moving/spinning scans.

        Returns (t_list, pos_list, rot_list) of plain Python floats. rot_stride is 4 for
        quaternions or 3 for Euler triples; pass rot_stride=None to skip rotation validation.
        """
        if not isinstance(traj_t, (list, tuple)) or len(traj_t) == 0:
            raise ValueError("traj_t must be a non-empty list of trajectory sample times")
        M = len(traj_t)
        if len(traj_pos) != M:
            raise ValueError("traj_t and traj_pos must have the same length M")
        if rot_stride is not None and len(traj_rot) != M:
            raise ValueError("traj_t and the trajectory orientation list must have the same length M")
        # Fail fast on a non-monotonic trajectory rather than deferring to a C++ exception.
        if any(traj_t[i] >= traj_t[i + 1] for i in range(M - 1)):
            raise ValueError("traj_t must be strictly monotonically increasing")

        def _to_xyz(v, name):
            if hasattr(v, 'x'):
                return [v.x, v.y, v.z]
            if isinstance(v, (list, tuple)) and len(v) == 3:
                return [float(c) for c in v]
            raise ValueError(f"{name} must be a vec3 or 3-element list/tuple")

        pos_list = [_to_xyz(p, "Each traj_pos entry") for p in traj_pos]

        rot_list = None
        if rot_stride is not None:
            rot_list = []
            for r in traj_rot:
                if not isinstance(r, (list, tuple)) or len(r) != rot_stride:
                    label = 'qx,qy,qz,qw' if rot_stride == 4 else 'roll,pitch,yaw'
                    raise ValueError(
                        f"Each trajectory orientation entry must have {rot_stride} elements ({label})"
                    )
                rot_list.append([float(c) for c in r])
        return [float(t) for t in traj_t], pos_list, rot_list

    def addScanSpinning(self, beam_elevation_angles: List[float],
                        azimuth_step: float, pulse_rate_hz: float,
                        traj_t: List[float],
                        traj_pos: List[Union[vec3, List[float], Tuple[float, float, float]]],
                        traj_rot: List[List[float]],
                        rot_is_quaternion: bool = True,
                        exit_diameter: float = 0.0, beam_divergence: float = 0.0,
                        lever_arm: Optional[Union[vec3, List[float], Tuple[float, float, float]]] = None,
                        boresight_rpy: Optional[Union[vec3, List[float], Tuple[float, float, float]]] = None,
                        column_format: Optional[List[str]] = None,
                        range_noise_stddev: float = 0.0, angle_noise_stddev: float = 0.0,
                        t0: float = 0.0) -> int:
        """
        Add a continuously-spinning multibeam scan from physical instrument parameters.

        High-level entry point for a rotating multi-channel sensor (Velodyne/Ouster/Hesai) on a moving
        (or stationary) platform. The azimuth grid, rotation rate, and revolution count are derived
        internally from the azimuth resolution, PRF, and trajectory duration; you never specify an
        azimuth range or step count. Sets the scan's :class:`ScanMode` to ``SPINNING``. For a stationary
        "spin in place" capture (a tripod), supply two coincident poses (same position and orientation)
        separated in time by the acquisition duration.

        Args:
            beam_elevation_angles: Per-channel beam ELEVATION angles above the horizon, in radians
                (NOT zenith — elevation above the horizon, where zenith = pi/2 - elevation; this matches
                manufacturer spec sheets)
            azimuth_step: Azimuth angular resolution in radians per firing step (must be > 0)
            pulse_rate_hz: Pulse repetition rate (PRF) in Hz (must be > 0)
            traj_t: Monotonically increasing trajectory sample times in seconds (length M)
            traj_pos: Platform positions in world coordinates, one [x, y, z] (or vec3) per traj_t entry
            traj_rot: Platform orientations, one per traj_t entry. Length-4 quaternion (qx, qy, qz, qw,
                Hamilton body->world) when ``rot_is_quaternion`` is True, otherwise length-3 roll/pitch/yaw
                Euler triple in radians (intrinsic Z-Y-X).
            rot_is_quaternion: Whether traj_rot holds quaternions (default True) or Euler angles
            exit_diameter: Laser beam exit diameter (meters, default 0)
            beam_divergence: Beam divergence angle (radians, default 0)
            lever_arm: Sensor optical center in the platform body frame [x, y, z] meters (default origin)
            boresight_rpy: Fixed sensor rotational misalignment [roll, pitch, yaw] radians (default 0)
            column_format: Optional list of column-format labels (default ["x", "y", "z"])
            range_noise_stddev: Std. dev. of Gaussian range noise in meters (default 0)
            angle_noise_stddev: Std. dev. of Gaussian angular jitter in radians (default 0)
            t0: Time of the first pulse in seconds (relative time; default 0)

        Returns:
            Scan ID for referencing this scan
        """
        if not isinstance(beam_elevation_angles, (list, tuple)) or len(beam_elevation_angles) == 0:
            raise ValueError("beam_elevation_angles must be a non-empty list of per-channel angles")
        if azimuth_step <= 0:
            raise ValueError("azimuth_step must be greater than 0")
        if pulse_rate_hz <= 0:
            raise ValueError("pulse_rate_hz must be greater than 0")
        if range_noise_stddev < 0:
            raise ValueError("range_noise_stddev must be non-negative")
        if angle_noise_stddev < 0:
            raise ValueError("angle_noise_stddev must be non-negative")

        rot_stride = 4 if rot_is_quaternion else 3
        t_list, pos_list, rot_list = self._validate_trajectory(
            traj_t, traj_pos, traj_rot, rot_stride, 'addScanSpinning')

        lever_list = ([lever_arm.x, lever_arm.y, lever_arm.z] if hasattr(lever_arm, 'x')
                      else list(lever_arm)) if lever_arm is not None else None
        boresight_list = ([boresight_rpy.x, boresight_rpy.y, boresight_rpy.z] if hasattr(boresight_rpy, 'x')
                          else list(boresight_rpy)) if boresight_rpy is not None else None

        if column_format is not None:
            if not isinstance(column_format, (list, tuple)) or \
                    not all(isinstance(c, str) for c in column_format):
                raise ValueError("column_format must be a list of strings")
            column_format = list(column_format)

        return lidar_wrapper.addLiDARScanSpinning(
            self._cloud_ptr, [float(a) for a in beam_elevation_angles],
            float(azimuth_step), float(pulse_rate_hz),
            t_list, pos_list, rot_list, bool(rot_is_quaternion),
            exit_diameter, beam_divergence,
            lever_list, boresight_list, column_format,
            range_noise_stddev, angle_noise_stddev, float(t0)
        )

    def addScanMovingRaster(self, Ntheta: int, theta_range: Tuple[float, float],
                            Nphi: int, phi_range: Tuple[float, float],
                            pulse_rate_hz: float,
                            traj_t: List[float],
                            traj_pos: List[Union[vec3, List[float], Tuple[float, float, float]]],
                            traj_quat: List[List[float]],
                            exit_diameter: float = 0.0, beam_divergence: float = 0.0,
                            lever_arm: Optional[Union[vec3, List[float], Tuple[float, float, float]]] = None,
                            boresight_rpy: Optional[Union[vec3, List[float], Tuple[float, float, float]]] = None,
                            column_format: Optional[List[str]] = None,
                            range_noise_stddev: float = 0.0, angle_noise_stddev: float = 0.0,
                            t0: float = 0.0) -> int:
        """
        Add a moving-platform raster scan: a fixed angular fan swept along a quaternion trajectory.

        High-level wrapper around :meth:`addScanMoving` for a non-spinning sensor on a moving platform.
        Specify the per-frame angular fan resolution plus the trajectory and PRF; Helios derives the
        per-pulse time sampling along the trajectory. Sets the scan's :class:`ScanMode` to ``MOVING_RASTER``.

        Args:
            Ntheta: Number of zenith samples in the angular fan
            theta_range: Zenith angle range (min, max) in radians
            Nphi: Number of azimuth samples in the angular fan
            phi_range: Azimuthal angle range (min, max) in radians
            pulse_rate_hz: Pulse repetition rate (PRF) in Hz (must be > 0)
            traj_t: Monotonically increasing trajectory sample times in seconds (length M)
            traj_pos: Platform positions in world coordinates, one [x, y, z] (or vec3) per traj_t entry
            traj_quat: Platform orientation quaternions (qx, qy, qz, qw, Hamilton body->world), one per
                traj_t entry
            exit_diameter: Laser beam exit diameter (meters, default 0)
            beam_divergence: Beam divergence angle (radians, default 0)
            lever_arm: Sensor optical center in the platform body frame [x, y, z] meters (default origin)
            boresight_rpy: Fixed sensor rotational misalignment [roll, pitch, yaw] radians (default 0)
            column_format: Optional list of column-format labels (default ["x", "y", "z"])
            range_noise_stddev: Std. dev. of Gaussian range noise in meters (default 0)
            angle_noise_stddev: Std. dev. of Gaussian angular jitter in radians (default 0)
            t0: Time of the first pulse in seconds (relative time; default 0)

        Returns:
            Scan ID for referencing this scan
        """
        validate_positive_value(Ntheta, 'Ntheta', 'addScanMovingRaster')
        validate_positive_value(Nphi, 'Nphi', 'addScanMovingRaster')
        if not isinstance(theta_range, (list, tuple)) or len(theta_range) != 2:
            raise ValueError("theta_range must be a tuple (min, max)")
        if not isinstance(phi_range, (list, tuple)) or len(phi_range) != 2:
            raise ValueError("phi_range must be a tuple (min, max)")
        if pulse_rate_hz <= 0:
            raise ValueError("pulse_rate_hz must be greater than 0")
        if range_noise_stddev < 0:
            raise ValueError("range_noise_stddev must be non-negative")
        if angle_noise_stddev < 0:
            raise ValueError("angle_noise_stddev must be non-negative")

        t_list, pos_list, quat_list = self._validate_trajectory(
            traj_t, traj_pos, traj_quat, 4, 'addScanMovingRaster')

        lever_list = ([lever_arm.x, lever_arm.y, lever_arm.z] if hasattr(lever_arm, 'x')
                      else list(lever_arm)) if lever_arm is not None else None
        boresight_list = ([boresight_rpy.x, boresight_rpy.y, boresight_rpy.z] if hasattr(boresight_rpy, 'x')
                          else list(boresight_rpy)) if boresight_rpy is not None else None

        if column_format is not None:
            if not isinstance(column_format, (list, tuple)) or \
                    not all(isinstance(c, str) for c in column_format):
                raise ValueError("column_format must be a list of strings")
            column_format = list(column_format)

        return lidar_wrapper.addLiDARScanMovingRaster(
            self._cloud_ptr, Ntheta, theta_range, Nphi, phi_range,
            float(pulse_rate_hz),
            t_list, pos_list, quat_list,
            exit_diameter, beam_divergence,
            lever_list, boresight_list, column_format,
            range_noise_stddev, angle_noise_stddev, float(t0)
        )

    def addScanRisley(self, prisms: List[Union['RisleyPrism', List[float], Tuple[float, ...]]],
                      refractive_index_air: float, pulse_rate_hz: float,
                      traj_t: List[float],
                      traj_pos: List[Union[vec3, List[float], Tuple[float, float, float]]],
                      traj_rot: List[List[float]],
                      rot_is_quaternion: bool = True,
                      exit_diameter: float = 0.0, beam_divergence: float = 0.0,
                      lever_arm: Optional[Union[vec3, List[float], Tuple[float, float, float]]] = None,
                      boresight_rpy: Optional[Union[vec3, List[float], Tuple[float, float, float]]] = None,
                      column_format: Optional[List[str]] = None,
                      range_noise_stddev: float = 0.0, angle_noise_stddev: float = 0.0,
                      t0: float = 0.0) -> int:
        """
        Add a rotating-Risley-prism (Livox-style rosette) scan from physical instrument parameters.

        High-level entry point for a Livox rosette-pattern sensor (Mid-40/Mid-70/Avia). A single beam is
        refracted through a stack of continuously rotating wedge prisms, tracing a non-repetitive rosette
        that fills a circular field of view. The scan is stored as an Ntheta=1, Nphi=Npulses table, where
        Npulses = round(pulse_rate_hz * trajectory_duration). Sets the scan's :class:`ScanMode` to
        ``RISLEY_PRISM`` and :class:`ScanPattern` to ``RISLEY_PRISM``. Like a spinning scan it is always
        trajectory-driven; a stationary tripod capture is two coincident poses (same position and
        orientation) separated in time by the acquisition duration.

        Args:
            prisms: Rotating wedge prisms in beam-traversal order (at least one; a Livox sensor uses two
                counter-rotating prisms). Each entry is a :class:`RisleyPrism` or a 4-element
                [wedge_angle, refractive_index, rotor_rate, phase] list/tuple (radians / unitless / rad-per-s / radians).
            refractive_index_air: Refractive index of the medium surrounding the prisms (typically 1.0)
            pulse_rate_hz: Pulse repetition rate (PRF) in Hz (must be > 0)
            traj_t: Monotonically increasing trajectory sample times in seconds (length M)
            traj_pos: Platform positions in world coordinates, one [x, y, z] (or vec3) per traj_t entry
            traj_rot: Platform orientations, one per traj_t entry. Length-4 quaternion (qx, qy, qz, qw,
                Hamilton body->world) when ``rot_is_quaternion`` is True, otherwise length-3 roll/pitch/yaw
                Euler triple in radians (intrinsic Z-Y-X).
            rot_is_quaternion: Whether traj_rot holds quaternions (default True) or Euler angles
            exit_diameter: Laser beam exit diameter (meters, default 0)
            beam_divergence: Beam divergence angle (radians, default 0)
            lever_arm: Sensor optical center in the platform body frame [x, y, z] meters (default origin)
            boresight_rpy: Fixed sensor rotational misalignment [roll, pitch, yaw] radians (default 0)
            column_format: Optional list of column-format labels (default ["x", "y", "z"])
            range_noise_stddev: Std. dev. of Gaussian range noise in meters (default 0)
            angle_noise_stddev: Std. dev. of Gaussian angular jitter in radians (default 0)
            t0: Time of the first pulse in seconds (relative time; default 0)

        Returns:
            Scan ID for referencing this scan
        """
        if not isinstance(prisms, (list, tuple)) or len(prisms) == 0:
            raise ValueError("prisms must be a non-empty list of RisleyPrism or 4-element [wedge_angle, refractive_index, rotor_rate, phase]")
        prism_lists = []
        for p in prisms:
            if isinstance(p, RisleyPrism):
                prism_lists.append(p.to_list())
            elif isinstance(p, (list, tuple)) and len(p) == 4:
                prism_lists.append([float(c) for c in p])
            else:
                raise ValueError("Each prism must be a RisleyPrism or a 4-element [wedge_angle, refractive_index, rotor_rate, phase]")
        if refractive_index_air <= 0:
            raise ValueError("refractive_index_air must be greater than 0")
        if pulse_rate_hz <= 0:
            raise ValueError("pulse_rate_hz must be greater than 0")
        if range_noise_stddev < 0:
            raise ValueError("range_noise_stddev must be non-negative")
        if angle_noise_stddev < 0:
            raise ValueError("angle_noise_stddev must be non-negative")

        rot_stride = 4 if rot_is_quaternion else 3
        t_list, pos_list, rot_list = self._validate_trajectory(
            traj_t, traj_pos, traj_rot, rot_stride, 'addScanRisley')

        lever_list = ([lever_arm.x, lever_arm.y, lever_arm.z] if hasattr(lever_arm, 'x')
                      else list(lever_arm)) if lever_arm is not None else None
        boresight_list = ([boresight_rpy.x, boresight_rpy.y, boresight_rpy.z] if hasattr(boresight_rpy, 'x')
                          else list(boresight_rpy)) if boresight_rpy is not None else None

        if column_format is not None:
            if not isinstance(column_format, (list, tuple)) or \
                    not all(isinstance(c, str) for c in column_format):
                raise ValueError("column_format must be a list of strings")
            column_format = list(column_format)

        return lidar_wrapper.addLiDARScanRisley(
            self._cloud_ptr, prism_lists, float(refractive_index_air), float(pulse_rate_hz),
            t_list, pos_list, rot_list, bool(rot_is_quaternion),
            exit_diameter, beam_divergence,
            lever_list, boresight_list, column_format,
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
        (rotating multi-channel sensor), 2 = Risley-prism (Livox-style rosette). Compare against
        ``ScanPattern.RASTER`` / ``ScanPattern.SPINNING_MULTIBEAM`` / ``ScanPattern.RISLEY_PRISM``.
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

    def getScanMode(self, scanID: int) -> ScanMode:
        """Get the high-level acquisition mode of a scan as a :class:`ScanMode`.

        STATIC_RASTER (fixed-origin grid), MOVING_RASTER (fan swept along a trajectory),
        SPINNING (continuously-rotating multi-channel sensor), or RISLEY_PRISM (Livox-style rosette).
        """
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        return ScanMode(lidar_wrapper.getLiDARScanMode(self._cloud_ptr, scanID))

    def getScanStepsPerRev(self, scanID: int) -> int:
        """Get the number of azimuth firing steps per revolution (spinning scans; 0 otherwise)."""
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        return lidar_wrapper.getLiDARScanStepsPerRev(self._cloud_ptr, scanID)

    def getScanRotationRate(self, scanID: int) -> float:
        """Get the sensor-head rotation rate in revolutions/second (spinning scans; 0 otherwise)."""
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        return lidar_wrapper.getLiDARScanRotationRate(self._cloud_ptr, scanID)

    def getScanRevolutions(self, scanID: int) -> float:
        """Get the number of revolutions the sensor head made (spinning scans; 0 otherwise)."""
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        return lidar_wrapper.getLiDARScanRevolutions(self._cloud_ptr, scanID)

    def getScanRisleyPrisms(self, scanID: int) -> List[RisleyPrism]:
        """Get the rotating wedge prisms of a Risley-prism scan as a list of :class:`RisleyPrism`.

        Returns the prism stack in beam-traversal order (empty for non-Risley scans).
        """
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        raw = lidar_wrapper.getLiDARScanRisleyPrisms(self._cloud_ptr, scanID)
        return [RisleyPrism(p[0], p[1], p[2], p[3]) for p in raw]

    def getScanRisleyRefractiveIndexAir(self, scanID: int) -> float:
        """Get the refractive index of the medium surrounding a Risley scan's prisms (1.0 for non-Risley)."""
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        return lidar_wrapper.getLiDARScanRisleyRefractiveIndexAir(self._cloud_ptr, scanID)

    def getScanReturnMode(self, scanID: int) -> ReturnMode:
        """Get the return-reporting mode of a scan as a :class:`ReturnMode` (MULTI or SINGLE)."""
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        return ReturnMode(lidar_wrapper.getLiDARScanReturnMode(self._cloud_ptr, scanID))

    def setScanReturnMode(self, scanID: int, return_mode: Union[ReturnMode, int]):
        """Set the return-reporting mode of a scan (ReturnMode.MULTI or ReturnMode.SINGLE).

        Only affects analytic-waveform synthetic scans (more than one ray per pulse).
        """
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        lidar_wrapper.setLiDARScanReturnMode(self._cloud_ptr, scanID, int(return_mode))

    def getScanSingleReturnSelection(self, scanID: int) -> SingleReturnSelection:
        """Get the single/limited-return selection policy as a :class:`SingleReturnSelection`."""
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        return SingleReturnSelection(
            lidar_wrapper.getLiDARScanSingleReturnSelection(self._cloud_ptr, scanID))

    def setScanSingleReturnSelection(self, scanID: int, selection: Union[SingleReturnSelection, int]):
        """Set the single/limited-return selection policy (STRONGEST, FIRST, LAST, or STRONGEST_PLUS_LAST).

        Used when the scan's return mode is SINGLE and a pulse resolves more returns than maxReturns.
        STRONGEST_PLUS_LAST is a dual-return mode that intrinsically yields 1 or 2 returns and
        ignores maxReturns.
        """
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        lidar_wrapper.setLiDARScanSingleReturnSelection(self._cloud_ptr, scanID, int(selection))

    def getScanMaxReturns(self, scanID: int) -> int:
        """Get the maximum returns per pulse used in single/limited-return mode (1 = single, N = N-return)."""
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        return lidar_wrapper.getLiDARScanMaxReturns(self._cloud_ptr, scanID)

    def setScanMaxReturns(self, scanID: int, max_returns: int):
        """Set the maximum returns per pulse used in single/limited-return mode (must be >= 1)."""
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        if max_returns < 1:
            raise ValueError("max_returns must be >= 1")
        lidar_wrapper.setLiDARScanMaxReturns(self._cloud_ptr, scanID, int(max_returns))

    def setSyntheticScanMemoryBudget(self, bytes: int):
        """Set the soft memory budget (bytes) for :meth:`syntheticScan`'s transient buffers.

        :meth:`syntheticScan` fans each pulse into ``rays_per_pulse`` sub-rays; for a
        large scan the simultaneously-traced sub-rays can demand many gigabytes if
        traced in one batch. This caps the live trace scratch buffers, so the per-scan
        beam fan-out is processed in chunks sized to stay near this budget regardless of
        scan resolution. It bounds only the transient buffers, not the output cloud.

        If never called, the budget is automatic and path-dependent (8 GiB on a GPU
        build, 4 GiB otherwise). Call this to override that with a fixed cap, typically
        to lower peak memory on a constrained host.

        Args:
            bytes: Soft cap in bytes on the live ray-tracing scratch buffers. Must be > 0.
        """
        if bytes <= 0:
            raise ValueError("memory budget must be greater than zero")
        lidar_wrapper.setLiDARSyntheticScanMemoryBudget(self._cloud_ptr, int(bytes))

    def getSyntheticScanMemoryBudget(self) -> int:
        """Get the soft memory budget (bytes) for :meth:`syntheticScan`'s transient buffers.

        Returns the explicitly configured budget set via :meth:`setSyntheticScanMemoryBudget`, or
        0 if using the automatic path-dependent default (8 GiB on a GPU build, 4 GiB otherwise).
        """
        return lidar_wrapper.getLiDARSyntheticScanMemoryBudget(self._cloud_ptr)

    def getScanPulseWidth(self, scanID: int) -> float:
        """Get the pulse width / range resolution (meters) of a scan (0 = use syntheticScan argument)."""
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        return lidar_wrapper.getLiDARScanPulseWidth(self._cloud_ptr, scanID)

    def setScanPulseWidth(self, scanID: int, pulse_width: float):
        """Set the pulse width / range resolution (meters) of a scan (0 = use syntheticScan argument)."""
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        if pulse_width < 0:
            raise ValueError("pulse_width must be non-negative")
        lidar_wrapper.setLiDARScanPulseWidth(self._cloud_ptr, scanID, float(pulse_width))

    def getScanDetectionThreshold(self, scanID: int) -> float:
        """Get the detection threshold (energy fraction, noise floor) of a scan."""
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        return lidar_wrapper.getLiDARScanDetectionThreshold(self._cloud_ptr, scanID)

    def setScanDetectionThreshold(self, scanID: int, detection_threshold: float):
        """Set the detection threshold (energy fraction, noise floor) of a scan."""
        if scanID < 0:
            raise ValueError("Scan ID must be non-negative")
        if detection_threshold < 0:
            raise ValueError("detection_threshold must be non-negative")
        lidar_wrapper.setLiDARScanDetectionThreshold(self._cloud_ptr, scanID, float(detection_threshold))

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
            direction_array: Ray directions, shape (N, 3) [radius, elevation, azimuth]. Pass cart2sphere(xyz - origin) to match loadASCIIFile; the full SphericalCoord (incl. radius) is used.
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

    def getHitDataColumn(self, label: str, absent_value: float = -9999.0) -> List[float]:
        """Bulk-export a named scalar column via the native cache-linear columnar path.

        Faster than :meth:`getHitDataAll` for whole-field reads (a single cache-linear pass over
        the contiguous native column rather than per-hit tree lookups), and returns full float64
        precision. Entries are ``absent_value`` where the label is absent for a hit. Returns a list
        of length getHitCount().
        """
        n = self.getHitCount()
        if n == 0:
            return []
        return lidar_wrapper.getLiDARHitDataColumn(self._cloud_ptr, label, n, absent_value)

    def getHitDataColumnIndex(self, label: str) -> int:
        """Get the internal column slot index for a hit-data label.

        Per-hit scalar data is stored column-wise; this resolves a label to its column slot for
        repeated bulk access without re-resolving the label by string. Returns -1 if the label has
        never been set on any hit.
        """
        if not isinstance(label, str):
            raise TypeError(f"label must be a str, got {type(label).__name__}")
        return lidar_wrapper.getLiDARHitDataColumnIndex(self._cloud_ptr, label)

    def getHitDataColumnArray(self, label: str, absent_value: float = -9999.0):
        """Bulk-export a named scalar column as an (getHitCount(),) float64 numpy array
        via the columnar path (``absent_value`` where the label is absent for a hit)."""
        import numpy as np
        n = self.getHitCount()
        if n == 0:
            return np.empty((0,), np.float64)
        return lidar_wrapper.getLiDARHitDataColumn_np(self._cloud_ptr, label, n, absent_value)

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

    def setExternalTriangulation(self, vertices, scan_ids):
        """Replace the internal triangulation with an externally-supplied mesh.

        Bypasses the internal Delaunay triangulation so a mesh produced elsewhere
        (a re-used Helios triangulation, or a per-scan open3d Ball-Pivot mesh) can
        drive leaf-area inversion without a recompute. After this call,
        ``calculateLeafArea()`` runs unchanged.

        Args:
            vertices: Triangle vertices in world coordinates, accepted as a
                (T, 9) array laid out [v0x,v0y,v0z, v1x,v1y,v1z, v2x,v2y,v2z] per
                triangle, a (T, 3, 3) array, or a flat (T*9,) array -- the same
                layout :meth:`getTriangleVerticesAll` exports, so a Helios mesh
                round-trips directly.
            scan_ids: Source scan index for each triangle, shape (T,). Required;
                every entry must be a valid scan index (see :meth:`addScan`),
                since the leaf-angle G(theta) term needs each triangle's ray
                direction. A merged mesh with no scan association is not valid.

        A grid must already be defined (see :meth:`addGrid`).
        """
        import numpy as np
        verts = np.ascontiguousarray(vertices, dtype=np.float32).reshape(-1)
        if verts.size % 9 != 0:
            raise ValueError(
                f"vertices has {verts.size} floats, must be a multiple of 9 (9 per triangle)")
        tri_count = verts.size // 9

        scans = np.ascontiguousarray(scan_ids, dtype=np.int32).reshape(-1)
        if scans.size != tri_count:
            raise ValueError(
                f"scan_ids has {scans.size} entries, expected {tri_count} (one per triangle)")

        lidar_wrapper.lidarSetExternalTriangulation(
            self._cloud_ptr, verts, scans, tri_count)

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
                rotation: float = 0.0,
                column_z_offsets: Optional[Union[List[float], Tuple[float, ...]]] = None):
        """
        Add a rectangular grid of voxel cells.

        Args:
            center: Grid center position (vec3 or 3-element list)
            size: Grid dimensions [x, y, z] (vec3 or 3-element list)
            ndiv: Number of divisions [nx, ny, nz] (3-element list)
            rotation: Azimuthal rotation angle (degrees, default 0.0)
            column_z_offsets: Optional per-(x,y)-column vertical offset for terrain
                following, row-major as ``[j*ndiv[0] + i]`` with length
                ``ndiv[0]*ndiv[1]``. Each vertical column of voxels is shifted in z by
                its column's offset so the grid can track an external terrain surface
                (e.g. a DEM). ``None`` (the default) builds an axis-regular grid.

        Note:
            ``rotation`` is in **degrees** here, matching the native ``addGrid()``.
            :meth:`addGridCell` takes its rotation in **radians** — the two native
            entry points genuinely differ, and PyHelios passes each through unchanged.
            :meth:`getCellRotation` reports degrees.

        Example:
            >>> lidar.addGrid(
            ...     center=vec3(0, 0, 0.5),
            ...     size=vec3(10, 10, 1),
            ...     ndiv=[10, 10, 5],
            ...     rotation=0.0
            ... )

            Terrain-following grid over a 2x2 column layout:

            >>> lidar.addGrid(
            ...     center=vec3(0, 0, 0.5),
            ...     size=vec3(10, 10, 1),
            ...     ndiv=[2, 2, 5],
            ...     column_z_offsets=[0.0, 0.1, 0.2, 0.3]
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

        if column_z_offsets is None:
            lidar_wrapper.addLiDARGrid(self._cloud_ptr, center_list, size_list, list(ndiv), rotation)
            return

        if not isinstance(column_z_offsets, (list, tuple)):
            raise ValueError(
                "column_z_offsets must be a list or tuple of floats, got "
                f"{type(column_z_offsets).__name__}"
            )

        expected = ndiv[0] * ndiv[1]
        if len(column_z_offsets) != expected:
            raise ValueError(
                f"column_z_offsets must have length ndiv[0]*ndiv[1] = {expected} "
                f"(one value per grid column), got {len(column_z_offsets)}"
            )

        lidar_wrapper.addLiDARGridTerrainFollowing(
            self._cloud_ptr, center_list, size_list, list(ndiv), rotation,
            [float(z) for z in column_z_offsets]
        )

    def addGridCell(self, center: Union[vec3, List[float], Tuple[float, float, float]],
                    size: Union[vec3, List[float], Tuple[float, float, float]],
                    rotation: float = 0.0):
        """
        Add a single grid cell.

        Args:
            center: Cell center position (vec3 or 3-element list)
            size: Cell dimensions [x, y, z] (vec3 or 3-element list)
            rotation: Azimuthal rotation angle (radians, default 0.0)

        Note:
            ``rotation`` is in **radians** here, whereas :meth:`addGrid` takes
            **degrees**. This asymmetry is inherited from the native API — the native
            ``addGridCell()`` stores the angle directly in the cell's radian field while
            ``addGrid()`` converts from degrees. :meth:`getCellRotation` reports degrees.
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
        """Get the true world-space center position of a grid cell.

        For a grid created with a non-zero azimuthal ``rotation``, this is the lattice
        center rotated about the grid anchor (about +z), so it lies in the same rotated
        world frame as the hit points, scan origins, and grid bounding box. For an
        un-rotated grid it is simply the lattice center.
        """
        if index < 0:
            raise ValueError("Index must be non-negative")
        center_list = lidar_wrapper.getLiDARCellCenter(self._cloud_ptr, index)
        return vec3(*center_list)

    def getCellCenterUnrotated(self, index: int) -> vec3:
        """Get the UNROTATED (axis-aligned lattice) center position of a grid cell.

        Companion to :meth:`getCellCenter`, which applies the grid's azimuthal rotation.
        This returns the center on the axis-aligned lattice instead; for an un-rotated
        grid the two are identical.

        Use this when the caller applies the grid rotation itself (e.g. rotating a whole
        voxel group about the grid center for display) — passing the rotated center to
        such code rotates the lattice twice.
        """
        if index < 0:
            raise ValueError("Index must be non-negative")
        center_list = lidar_wrapper.getLiDARCellCenterUnrotated(self._cloud_ptr, index)
        return vec3(*center_list)

    def getCellSize(self, index: int) -> vec3:
        """Get size of a grid cell"""
        if index < 0:
            raise ValueError("Index must be non-negative")
        size_list = lidar_wrapper.getLiDARCellSize(self._cloud_ptr, index)
        return vec3(*size_list)

    def getCellRotation(self, index: int) -> float:
        """Get the azimuthal rotation of a grid cell about the z-axis, in degrees.

        The units match the ``rotation`` argument of :meth:`addGrid`. Note that
        :meth:`addGridCell` takes its rotation in radians.
        """
        if index < 0:
            raise ValueError("Index must be non-negative")
        return lidar_wrapper.getLiDARCellRotation(self._cloud_ptr, index)

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

        Misses synthesized here are stored in virtualized form -- as a per-cell occupancy
        bit plus a scan-wide angular model rather than as stored points -- so they cost no
        per-point storage. They are counted by :meth:`getHitCount` and readable through
        every accessor regardless. See :meth:`hasVirtualMisses` and
        :meth:`getVirtualMissCount`.

        Note:
            Reading the whole cloud back afterwards should go through the bulk accessors
            (:meth:`getHitsXYZRGB`, :meth:`getHitScanIDArray`, :meth:`getHitDataArray`),
            which read virtualized misses in one pass. A Python loop over the per-index
            getters costs O(Nphi) on each such point.
        """
        lidar_wrapper.gapfillLiDARMisses(self._cloud_ptr)

    def gapfillMissesCount(self, scanID: Optional[int] = None,
                           gapfill_grid_only: bool = False,
                           add_flags: bool = False) -> int:
        """
        Gapfill missing points and return only how many were added.

        Identical to :meth:`gapfillMisses` except that the count is returned instead of the
        filled positions, which for a fine scan grid is a large allocation most callers
        discard.

        Args:
            scanID: Scan to gapfill. ``None`` (the default) gapfills every scan, in which
                case ``gapfill_grid_only`` and ``add_flags`` are not used.
            gapfill_grid_only: Fill only within the voxel grid's bounding box
            add_flags: Add ``gapfillMisses_code`` as hit point data (0=original, 1=gapfilled)

        Returns:
            Number of missing points added

        Raises:
            RuntimeError: If the native library predates helios-core v1.3.84
        """
        if scanID is None:
            return lidar_wrapper.gapfillLiDARMissesCount(self._cloud_ptr)
        return lidar_wrapper.gapfillLiDARMissesCountScan(
            self._cloud_ptr, scanID, gapfill_grid_only, add_flags
        )

    def getVirtualMissCount(self) -> int:
        """
        Number of gap-filled misses currently held in virtualized form.

        A miss synthesized by :meth:`gapfillMisses` is a pure function of its scan-grid
        cell, so it is stored implicitly rather than as an element of the hit array. Such
        points are counted by :meth:`getHitCount` and readable through every accessor, but
        occupy no per-point storage.

        Raises:
            RuntimeError: If the native library predates helios-core v1.3.84
        """
        return lidar_wrapper.getLiDARVirtualMissCount(self._cloud_ptr)

    def hasVirtualMisses(self) -> bool:
        """
        Whether any gap-filled miss is currently held in virtualized form.

        Raises:
            RuntimeError: If the native library predates helios-core v1.3.84
        """
        return lidar_wrapper.hasLiDARVirtualMisses(self._cloud_ptr)

    def materializeMisses(self) -> None:
        """
        Convert every virtualized gap-filled miss into a stored hit point.

        Every observable is unchanged by this call -- it trades the memory saving for real
        storage. It happens automatically before any operation that renumbers the hit index
        space (adding or deleting a hit point, writing hit data or a grid cell), so calling
        it explicitly is only needed to pay that cost at a chosen moment.

        Raises:
            RuntimeError: If the native library predates helios-core v1.3.84
        """
        lidar_wrapper.materializeLiDARMisses(self._cloud_ptr)

    def getScanGridDirection(self, scanID: int, row: int, column: int) -> SphericalCoord:
        """
        Beam direction at a scan-grid cell, from the model fitted during gap-filling.

        Available once :meth:`gapfillMisses` has run on the scan through the row/column
        path. This is the same reconstruction used to place synthesized misses, exposed so
        a caller can check the fitted geometry against known directions.

        Args:
            scanID: Scan index
            row: Scan-grid row (zenith index)
            column: Scan-grid column (azimuth index)

        Returns:
            Unit direction of that cell's beam

        Raises:
            RuntimeError: If the native library predates helios-core v1.3.84
        """
        radius, elevation, azimuth = lidar_wrapper.getLiDARScanGridDirection(
            self._cloud_ptr, scanID, row, column
        )
        return SphericalCoord(radius, elevation, azimuth)

    def getHitXYZColumn(self):
        """
        Read every hit's position in index order in one pass.

        Costs O(1) per hit even for virtualized gap-filled misses, which the per-index
        accessors resolve in O(Nphi). Prefer this to a Python loop over
        :meth:`getHitXYZ` whenever the whole cloud is being read.

        Returns:
            List of (x, y, z) tuples, one per hit

        Raises:
            RuntimeError: If the native library predates helios-core v1.3.84
        """
        return lidar_wrapper.getLiDARHitXYZColumn(self._cloud_ptr, self.getHitCount())

    def getHitScanIDColumn(self):
        """
        Read every hit's scan ID in index order in one pass.

        See :meth:`getHitXYZColumn` for why this is preferred over a per-index loop.

        Returns:
            List of scan indices, one per hit

        Raises:
            RuntimeError: If the native library predates helios-core v1.3.84
        """
        return lidar_wrapper.getLiDARHitScanIDColumn(self._cloud_ptr, self.getHitCount())

    def estimateHitPointMemory(self, hit_count: int) -> int:
        """
        Estimate the resident memory a cloud of ``hit_count`` points will occupy, in bytes.

        Each stored point costs the size of a hit point plus, for every scalar-data label
        the cloud carries, one double of value and one byte of presence -- the columnar
        store is dense, so every label costs on every point. Excludes virtualized misses
        and the transient of growing the arrays; see :meth:`reserveHitPoints` for that.

        Most accurate once at least one point exists, since it reads the labels created
        so far.

        Args:
            hit_count: Number of hit points to estimate for

        Returns:
            Estimated resident bytes

        Raises:
            RuntimeError: If the native library predates helios-core v1.3.84
        """
        return lidar_wrapper.estimateLiDARHitPointMemory(self._cloud_ptr, hit_count)

    def setMaxHitPoints(self, max_hits: int) -> None:
        """
        Set the cap on stored hit points before loading fails with a diagnostic.

        Exceeding the cap raises an error naming the projected point count and the limit,
        rather than throwing from inside the allocator where neither the scan responsible
        nor the size is visible. The default (:meth:`getDefaultMaxHitPoints`) is
        deliberately generous: it guards against a mis-specified scan grid exhausting the
        machine, and is not a statement about machine capacity. Raise it when the machine
        genuinely has the memory.

        Args:
            max_hits: Maximum stored hit points, or 0 to disable the check

        Raises:
            RuntimeError: If the native library predates helios-core v1.3.84
        """
        lidar_wrapper.setLiDARMaxHitPoints(self._cloud_ptr, max_hits)

    def getMaxHitPoints(self) -> int:
        """
        Current cap on stored hit points, or 0 if the check is disabled.

        Raises:
            RuntimeError: If the native library predates helios-core v1.3.84
        """
        return lidar_wrapper.getLiDARMaxHitPoints(self._cloud_ptr)

    @staticmethod
    def getDefaultMaxHitPoints() -> int:
        """
        Default cap on the number of stored hit points in a cloud (100 million).

        Raises:
            RuntimeError: If the native library predates helios-core v1.3.84
        """
        return lidar_wrapper.getLiDARDefaultMaxHitPoints()

    def reserveHitPoints(self, hit_count: int) -> None:
        """
        Reserve capacity for hit points and every scalar-data column at once.

        Growing the hit-point array by repeated insertion reallocates geometrically, and
        during every reallocation the old and new buffers are both live. For a cloud of
        tens of millions of returns that transient is gigabytes on top of the steady-state
        cost, and on Windows it is charged against the system commit limit at allocation
        time -- so a load that would comfortably fit once settled can still fail while
        growing. Reserving the final size once removes the transient entirely.

        This only reserves capacity; it does not create hit points, and
        :meth:`getHitCount` is unchanged. Reserving less than the eventual total is
        harmless, as is reserving more.

        Args:
            hit_count: Expected total number of hit points in the cloud

        Raises:
            RuntimeError: If the native library predates helios-core v1.3.84
        """
        lidar_wrapper.reserveLiDARHitPoints(self._cloud_ptr, hit_count)

    def setExactPathLengths(self, exact: bool) -> None:
        """
        Keep every beam path length exactly, instead of binning them.

        The leaf-area inversion bins per-beam voxel path lengths once a voxel accumulates
        many samples, which bounds memory that would otherwise grow without limit with scan
        size. Binning recovers the extinction coefficient far inside the solver's
        tolerance, so this is an escape hatch for unusual geometry, or for confirming that
        binning is not responsible for a difference between two results.

        Args:
            exact: True to keep every sample; False (the default) to bin above the threshold

        Raises:
            RuntimeError: If the native library predates helios-core v1.3.84
        """
        lidar_wrapper.setLiDARExactPathLengths(self._cloud_ptr, exact)

    def getExactPathLengths(self) -> bool:
        """
        Whether path lengths are accumulated exactly.

        Raises:
            RuntimeError: If the native library predates helios-core v1.3.84
        """
        return lidar_wrapper.getLiDARExactPathLengths(self._cloud_ptr)

    def syntheticScan(self, context: Context,
                     rays_per_pulse: Optional[int] = None,
                     pulse_distance_threshold: Optional[float] = None,
                     scan_grid_only: bool = False,
                     record_misses: bool = True,
                     append: bool = False,
                     return_mode: Optional[Union[ReturnMode, int]] = None,
                     cancel_flag=None):
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
            return_mode: Optional :class:`ReturnMode` (MULTI or SINGLE) for analytic-waveform scans.
                Overrides each scan's stored return mode for this call only. Only valid when
                rays_per_pulse is set (waveform mode); raises ValueError otherwise. In SINGLE mode
                up to each scan's getScanMaxReturns() returns per pulse are reported, selected by the
                scan's single-return selection policy.
            cancel_flag: Optional ``ctypes.c_int`` polled during the ray trace. Setting it non-zero from another thread aborts the scan mid-pass. It is cleared when the call returns, so a later scan on this cloud is not pre-cancelled.

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

        # Register an external cancellation flag (a ctypes.c_int set non-zero from
        # another thread) so a long ray trace can be aborted mid-pass. Cleared in
        # the finally below so a later scan on this cloud isn't pre-cancelled.
        if cancel_flag is not None:
            lidar_wrapper.setLiDARCancelFlag(self._cloud_ptr, cancel_flag)
        try:
            self._dispatch_synthetic_scan(
                context_ptr, rays_per_pulse, pulse_distance_threshold,
                scan_grid_only, record_misses, append, return_mode)
        finally:
            if cancel_flag is not None:
                lidar_wrapper.setLiDARCancelFlag(self._cloud_ptr, None)

    def _dispatch_synthetic_scan(self, context_ptr, rays_per_pulse,
                                 pulse_distance_threshold, scan_grid_only,
                                 record_misses, append, return_mode):
        # Discrete-return mode (single ray per pulse)
        if rays_per_pulse is None:
            if return_mode is not None:
                raise ValueError(
                    "return_mode is only valid for analytic-waveform scans; pass rays_per_pulse (> 1)")
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

            if return_mode is None:
                lidar_wrapper.syntheticLiDARScanFull(
                    self._cloud_ptr, context_ptr,
                    rays_per_pulse, pulse_distance_threshold,
                    scan_grid_only, record_misses, append
                )
            else:
                lidar_wrapper.syntheticLiDARScanReturnMode(
                    self._cloud_ptr, context_ptr,
                    rays_per_pulse, pulse_distance_threshold, int(return_mode),
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
                (0.5 = spherical/random leaf-angle distribution). May be a single scalar (broadcast
                to every voxel) or a sequence of one value per grid cell in grid-cell order — the
                latter supports a spatially-varying (e.g. vertically-varying) leaf-angle
                distribution. When provided, leaf area is computed via a beam-based inversion that
                uses each hit's per-pulse beam origin and does NOT require triangulation — the only
                supported path for moving-platform scans (see :meth:`addScanMoving`). Requires both
                ``min_voxel_hits`` and ``element_width`` to also be specified.

        Example:
            >>> from pyhelios import Context, LiDARCloud
            >>> with Context() as context:
            ...     with LiDARCloud() as lidar:
            ...         # ... load data, add grid, triangulate ...
            ...         lidar.calculateLeafArea(context)
        """
        if not isinstance(context, Context):
            raise TypeError("context must be a Context instance")

        # Gtheta may be a scalar (broadcast to every voxel) or a sequence of one value per grid
        # cell (a spatially-varying leaf-angle distribution). Detect which up front.
        gtheta_is_sequence = Gtheta is not None and not isinstance(Gtheta, (int, float))

        # Validate argument combinations before touching native state (fail-fast).
        if Gtheta is not None:
            if min_voxel_hits is None or element_width is None:
                raise ValueError(
                    "Gtheta requires both min_voxel_hits and element_width to also be specified "
                    "(the G(theta) overload takes all three)")
            if gtheta_is_sequence:
                g_list = [float(v) for v in Gtheta]
                n_cells = self.getGridCellCount()
                if len(g_list) != n_cells:
                    raise ValueError(
                        f"A per-voxel Gtheta sequence must have one value per grid cell "
                        f"({n_cells}), but {len(g_list)} were given")
                if any(not (0.0 < v <= 1.0) for v in g_list):
                    raise ValueError(
                        "Every per-voxel Gtheta value must be in (0, 1] "
                        "(e.g. 0.5 for a spherical leaf-angle distribution)")
            elif Gtheta <= 0:
                # The native overload treats Gtheta <= 0 as the "compute from triangulation"
                # sentinel, which silently disables the supplied-G(theta) path. Reject it here.
                raise ValueError(
                    "Gtheta must be > 0 and in (0, 1] (e.g. 0.5 for a spherical leaf-angle distribution)")
        elif element_width is not None and min_voxel_hits is None:
            raise ValueError(
                "element_width requires min_voxel_hits to also be specified "
                "(the uncertainty overload takes both)")

        context_ptr = context.getNativePtr()
        if gtheta_is_sequence:
            lidar_wrapper.calculateLiDARLeafAreaGthetaPerCell(
                self._cloud_ptr, context_ptr, g_list, min_voxel_hits, element_width)
        elif Gtheta is not None:
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

        # Retain a reference to the Context. The native side constructs a
        # CollisionDetection that stores the raw Context* for its lifetime, so a
        # temporary Context would otherwise be freed while still referenced.
        # Note the C++ side only builds CollisionDetection once (it no-ops if one
        # already exists), so the first Context passed here is the one that stays
        # bound - re-initializing with a different Context has no effect.
        if getattr(self, '_cd_context', None) is not None and self._cd_context is not context:
            raise RuntimeError(
                "LiDARCloud collision detection is already initialized with a different Context.\n"
                "The native CollisionDetection keeps the Context it was first given; "
                "passing another one here would silently have no effect.\n"
                "\n"
                "Fix: create a new LiDARCloud for a different Context, or reuse the "
                "Context this cloud was initialized with."
            )
        self._cd_context = context

        lidar_wrapper.initializeLiDARCollisionDetection(self._cloud_ptr, context.getNativePtr())

    def _check_cd_context_alive(self):
        """Raise if the Context bound to collision detection has been destroyed."""
        if getattr(self, '_cd_context', None) is not None:
            check_context_alive(self._cd_context, "LiDARCloud collision detection")

    def enableCDGPUAcceleration(self):
        """Enable GPU acceleration for collision detection ray tracing"""
        self._check_cd_context_alive()
        lidar_wrapper.enableLiDARCDGPUAcceleration(self._cloud_ptr)

    def disableCDGPUAcceleration(self):
        """Disable GPU acceleration (use CPU ray tracing)"""
        self._check_cd_context_alive()
        lidar_wrapper.disableLiDARCDGPUAcceleration(self._cloud_ptr)

    def isGPUAvailable(self) -> bool:
        """Return True if a CUDA-capable GPU is available for collision-detection ray tracing.

        Reports capability (compiled with CUDA, a device present, and HELIOS_NO_GPU not set); use
        :meth:`isGPUAccelerationEnabled` to query whether GPU acceleration is currently toggled on.
        """
        return lidar_wrapper.isLiDARGPUAvailable(self._cloud_ptr)

    def isGPUAccelerationEnabled(self) -> bool:
        """Return True if GPU acceleration is currently enabled for collision-detection ray tracing."""
        return lidar_wrapper.isLiDARGPUAccelerationEnabled(self._cloud_ptr)

    def setSyntheticScanProgressPointer(self, ptr):
        """Register an external per-scan progress counter polled during :meth:`syntheticScan`.

        ``ptr`` is a ``ctypes.c_int`` into which syntheticScan writes the 0-based index of the scan
        currently being ray-traced (set to :meth:`getScanCount` when the batch finishes), letting a
        host thread poll progress while the blocking scan runs. The counter is owned by the caller and
        must outlive the scan. Pass ``None`` to clear.
        """
        import ctypes
        if ptr is not None and not isinstance(ptr, ctypes.c_int):
            raise TypeError("ptr must be a ctypes.c_int (or None to clear)")
        lidar_wrapper.setLiDARSyntheticScanProgressPointer(self._cloud_ptr, ptr)

    def setProgressCallback(self, callback):
        """Register a progress callback fired with ``(progress_fraction, message)`` during :meth:`syntheticScan`.

        ``progress_fraction`` is a float in [0, 1]; ``message`` is a ``str`` describing the current
        phase. Pass ``None`` to clear the callback. The callback bridge is kept alive on this
        :class:`LiDARCloud` for as long as it is registered.
        """
        if callback is None:
            # Clear the native callback first, then drop our reference, so a failure in the native
            # call cannot leave C++ holding a freed bridge.
            lidar_wrapper.setLiDARProgressCallback(self._cloud_ptr, None)
            self._progress_callback_ref = None
            return

        if not callable(callback):
            raise TypeError("callback must be callable or None")

        def _trampoline(progress, message):
            callback(float(progress), message.decode('utf-8') if message else "")

        # Keep the ctypes callback object alive for as long as native code holds it; ctypes does not.
        self._progress_callback_ref = lidar_wrapper.LiDARProgressCallback(_trampoline)
        lidar_wrapper.setLiDARProgressCallback(self._cloud_ptr, self._progress_callback_ref)

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
