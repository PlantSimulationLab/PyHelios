"""
SolarPosition - High-level interface for solar position and radiation calculations

This module provides a Python interface to the SolarPosition Helios plugin,
offering comprehensive solar angle calculations, radiation modeling, and
time-dependent solar functions for atmospheric physics and plant modeling.
"""

import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import List, Tuple, Optional, Union
from .wrappers import USolarPositionWrapper as solar_wrapper
from .Context import Context, check_context_alive
from .plugins.registry import get_plugin_registry
from .exceptions import HeliosError
from .assets import get_asset_manager
from .wrappers.DataTypes import Time, Date, vec3, SphericalCoord

logger = logging.getLogger(__name__)


# Runtime data files that the SolarPosition C++ code opens by relative path, given relative to the
# plugin's asset directory ("plugins/solarposition" under the build directory).
_PRAGUE_DATASET = 'lib/prague_sky_model/PragueSkyModelReduced.dat'
_OZONE_CLIMATOLOGY = 'ozone_climatology/sbuv_total_ozone_climatology.txt'
_EXTRATERRESTRIAL_SPECTRUM = 'ssolar_goa/wehrli85.txt'
_ATMOSPHERE_LUT = 'atmosphere_lut/atmosphere_lut.bin'
_THERMAL_ATMOSPHERE_LUT = 'thermal_atmosphere_lut/thermal_atmosphere_lut.bin'

# Files read by the spectral solar irradiance and sensor atmosphere models
_SPECTRAL_MODEL_ASSETS = (_OZONE_CLIMATOLOGY, _EXTRATERRESTRIAL_SPECTRUM, _ATMOSPHERE_LUT)
# Files read by the thermal sensor atmosphere model
_THERMAL_MODEL_ASSETS = (_OZONE_CLIMATOLOGY, _THERMAL_ATMOSPHERE_LUT)


@contextmanager
def _solarposition_working_directory(required_assets: Tuple[str, ...] = (_PRAGUE_DATASET,)):
    """
    Context manager that temporarily changes working directory to where SolarPosition assets are located.

    SolarPosition C++ code opens its data files (the Prague sky model dataset, the ozone climatology,
    the extraterrestrial solar spectrum and the atmospheric look-up tables) through hardcoded relative
    paths such as "plugins/solarposition/lib/prague_sky_model/PragueSkyModelReduced.dat", so they are
    only resolvable when the process is running from the build directory. This manager temporarily
    changes to the build directory where the files actually live.

    Args:
        required_assets: Paths, relative to the "plugins/solarposition" asset directory, of the data
                         files the enclosed call reads.

    Raises:
        RuntimeError: If the build directory or a required data file is not found, indicating a
                      build system error.
    """
    asset_manager = get_asset_manager()
    working_dir = asset_manager._get_helios_build_path()

    if working_dir and working_dir.exists():
        solarposition_assets = working_dir / 'plugins' / 'solarposition'
    else:
        # For wheel installations, check packaged assets
        current_dir = Path(__file__).parent
        packaged_build = current_dir / 'assets' / 'build'

        if packaged_build.exists():
            working_dir = packaged_build
            solarposition_assets = working_dir / 'plugins' / 'solarposition'
        else:
            # Fallback to development paths
            repo_root = current_dir.parent
            build_lib_dir = repo_root / 'pyhelios_build' / 'build' / 'lib'
            working_dir = build_lib_dir.parent
            solarposition_assets = working_dir / 'plugins' / 'solarposition'

            if not build_lib_dir.exists():
                raise RuntimeError(
                    f"PyHelios build directory not found at {build_lib_dir}. "
                    f"Run: build_scripts/build_helios --clean"
                )

    for asset in required_assets:
        asset_path = solarposition_assets / asset
        if not asset_path.exists():
            if asset == _PRAGUE_DATASET:
                raise RuntimeError(
                    f"Prague sky model dataset not found at {asset_path}. "
                    f"This indicates a build system error. The build script should copy the "
                    f"~26 MB dataset to this location. "
                    f"Rebuild with: build_scripts/build_helios --clean"
                )
            raise RuntimeError(
                f"SolarPosition data file not found at {asset_path}. "
                f"This indicates a build system error. The build script should copy the "
                f"solarposition plugin assets to this location. "
                f"Rebuild with: build_scripts/build_helios --clean"
            )

    original_dir = os.getcwd()
    try:
        os.chdir(working_dir)
        logger.debug(f"Changed working directory to {working_dir} for SolarPosition asset access")
        yield working_dir
    finally:
        os.chdir(original_dir)
        logger.debug(f"Restored working directory to {original_dir}")


def _validate_sensor_arguments(label, direction_to_sensor) -> None:
    """Validate the label and sensor direction shared by the sensor atmosphere methods."""
    if not isinstance(label, str):
        raise ValueError(f"Label must be a string, got {type(label).__name__}")
    if not label:
        raise ValueError("Label cannot be empty")
    if not isinstance(direction_to_sensor, vec3):
        raise ValueError(f"direction_to_sensor must be a vec3, got {type(direction_to_sensor).__name__}")
    if direction_to_sensor.x == 0.0 and direction_to_sensor.y == 0.0 and direction_to_sensor.z == 0.0:
        raise ValueError("direction_to_sensor must be a non-zero vector")


class SolarPositionError(HeliosError):
    """Exception raised for SolarPosition-specific errors"""
    pass


class SolarPosition:
    """
    High-level interface for solar position calculations and radiation modeling.
    
    SolarPosition provides comprehensive solar angle calculations, radiation flux
    modeling, sunrise/sunset time calculations, and atmospheric turbidity calibration.
    The plugin automatically uses Context time/date for calculations or can be 
    initialized with explicit coordinates.
    
    This class requires the native Helios library built with SolarPosition support.
    Use context managers for proper resource cleanup.
    
    Examples:
        Basic usage with Context coordinates:
        >>> with Context() as context:
        ...     context.setDate(2023, 6, 21)  # Summer solstice
        ...     context.setTime(12, 0)        # Solar noon
        ...     with SolarPosition(context) as solar:
        ...         elevation = solar.getSunElevation()
        ...         print(f"Sun elevation: {elevation:.1f}°")
        
        Usage with explicit coordinates:
        >>> with Context() as context:
        ...     # Davis, California coordinates
        ...     with SolarPosition(context, utc_offset=-8, latitude=38.5, longitude=-121.7) as solar:
        ...         azimuth = solar.getSunAzimuth()
        ...         flux = solar.getSolarFlux(101325, 288.15, 0.6, 0.1)
        ...         print(f"Solar flux: {flux:.1f} W/m²")
    """
    
    def __init__(self, context: Context, utc_offset: Optional[float] = None, 
                 latitude: Optional[float] = None, longitude: Optional[float] = None):
        """
        Initialize SolarPosition with a Helios context.
        
        Args:
            context: Active Helios Context instance
            utc_offset: UTC time offset in hours (-14 to +12). Helios counts the offset
                       positive moving West, which inverts the real-world UTC-12..UTC+14
                       span, so the range is asymmetric. If provided with
                       latitude/longitude, creates plugin with explicit coordinates.
            latitude: Latitude in degrees (-90 to +90). Required if utc_offset provided.
            longitude: Longitude in degrees (-180 to +180). Required if utc_offset provided.
            
        Raises:
            SolarPositionError: If plugin not available in current build
            ValueError: If coordinate parameters are invalid or incomplete
            RuntimeError: If plugin initialization fails
            
        Note:
            If coordinates are not provided, the plugin uses Context location settings.
            Solar calculations depend on Context time/date - use context.setTime() and
            context.setDate() to set the simulation time before calculations.
        """
        # Check plugin availability
        registry = get_plugin_registry()
        if not registry.is_plugin_available('solarposition'):
            raise SolarPositionError(
                "SolarPosition not available in current Helios library. "
                "SolarPosition plugin availability depends on build configuration.\n"
                "\n"
                "System requirements:\n"
                "  - Platforms: Windows, Linux, macOS\n"
                "  - Dependencies: None\n"
                "  - GPU: Not required\n"
                "\n"
                "If you're seeing this error, the SolarPosition plugin may not be "
                "properly compiled into your Helios library. Please rebuild PyHelios:\n"
                "  build_scripts/build_helios --clean"
            )
        
        # Validate coordinate parameters
        if utc_offset is not None or latitude is not None or longitude is not None:
            # If any coordinate parameter is provided, all must be provided
            if utc_offset is None or latitude is None or longitude is None:
                raise ValueError(
                    "If specifying coordinates, all three parameters must be provided: "
                    "utc_offset, latitude, longitude"
                )
            
            # Validate coordinate ranges
            # Range matches helios::Location::validate(): asymmetric because Helios
            # counts the UTC offset positive moving West, inverting real-world
            # UTC-12..UTC+14 to +12..-14.
            if utc_offset < -14.0 or utc_offset > 12.0:
                raise ValueError(f"UTC offset must be between -14 and +12 hours, got: {utc_offset}")
            if latitude < -90.0 or latitude > 90.0:
                raise ValueError(f"Latitude must be between -90 and +90 degrees, got: {latitude}")
            if longitude < -180.0 or longitude > 180.0:
                raise ValueError(f"Longitude must be between -180 and +180 degrees, got: {longitude}")
            
            # Create with explicit coordinates
            self.context = context
            self._solar_pos = solar_wrapper.createSolarPositionWithCoordinates(
                context.getNativePtr(), utc_offset, latitude, longitude
            )
        else:
            # Create using Context location
            self.context = context
            self._solar_pos = solar_wrapper.createSolarPosition(context.getNativePtr())
        
        if not self._solar_pos:
            raise SolarPositionError("Failed to initialize SolarPosition")
    
    def _check_context_alive(self):
        """Raise if the owning Context has been destroyed (see Context.check_context_alive)."""
        check_context_alive(getattr(self, "context", None), "SolarPosition")

    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources"""
        if hasattr(self, '_solar_pos') and self._solar_pos:
            solar_wrapper.destroySolarPosition(self._solar_pos)
            self._solar_pos = None

    def __del__(self):
        """Destructor to ensure C++ resources freed even without 'with' statement."""
        if hasattr(self, '_solar_pos') and self._solar_pos is not None:
            try:
                solar_wrapper.destroySolarPosition(self._solar_pos)
                self._solar_pos = None
            except Exception as e:
                import warnings
                warnings.warn(f"Error in SolarPosition.__del__: {e}")

    # Atmospheric condition management (modern API)
    def setAtmosphericConditions(self, pressure_Pa: float, temperature_K: float,
                                 humidity_rel: float, turbidity: float) -> None:
        """
        Set atmospheric conditions for subsequent flux calculations (modern API).

        This method sets global atmospheric conditions in the Context that are used
        by parameter-free flux methods (modern API). Once set, you can call getSolarFlux(),
        getSolarFluxPAR(), etc. without passing atmospheric parameters.

        Args:
            pressure_Pa: Atmospheric pressure in Pascals (e.g., 101325 for sea level)
            temperature_K: Temperature in Kelvin (e.g., 288.15 for 15°C)
            humidity_rel: Relative humidity as fraction (0.0-1.0). The spectral solar irradiance,
                sensor atmosphere and thermal atmosphere methods derive the precipitable water
                from it and require a value greater than 0.
            turbidity: Ångström's aerosol turbidity coefficient (β), the aerosol optical depth
                at 1 µm (must be >= 0). The aerosol optical depth at 550 nm is about 2.18 β and
                that at 500 nm about 2.46 β, so an aerosol optical depth measured at 500 nm
                corresponds to β of about 0.41 times that value. This is not Linke turbidity.

        Raises:
            ValueError: If atmospheric parameters are out of valid ranges
            SolarPositionError: If operation fails

        Note:
            This is the modern API pattern. Atmospheric conditions are stored in Context
            global data and reused by all parameter-free flux methods until changed.

        Example:
            >>> # Modern API (set once, use many times)
            >>> with Context() as context:
            ...     with SolarPosition(context) as solar:
            ...         solar.setAtmosphericConditions(101325, 288.15, 0.6, 0.1)
            ...         flux = solar.getSolarFlux()  # No parameters needed
            ...         par = solar.getSolarFluxPAR()  # Uses same conditions
            ...         diffuse = solar.getDiffuseFraction()  # Uses same conditions
        """
        # Validate parameters
        if pressure_Pa < 0.0:
            raise ValueError(f"Atmospheric pressure must be non-negative, got: {pressure_Pa}")
        if temperature_K < 0.0:
            raise ValueError(f"Temperature must be non-negative, got: {temperature_K}")
        if humidity_rel < 0.0 or humidity_rel > 1.0:
            raise ValueError(f"Relative humidity must be between 0 and 1, got: {humidity_rel}")
        if turbidity < 0.0:
            raise ValueError(f"Turbidity must be non-negative, got: {turbidity}")

        self._check_context_alive()
        try:
            solar_wrapper.setAtmosphericConditions(self._solar_pos, pressure_Pa, temperature_K, humidity_rel, turbidity)
        except Exception as e:
            raise SolarPositionError(f"Failed to set atmospheric conditions: {e}")

    def getAtmosphericConditions(self) -> Tuple[float, float, float, float]:
        """
        Get currently set atmospheric conditions from Context.

        Returns:
            Tuple of (pressure_Pa, temperature_K, humidity_rel, turbidity), where turbidity is
            Ångström's aerosol turbidity coefficient (β), the aerosol optical depth at 1 µm

        Raises:
            SolarPositionError: If operation fails

        Note:
            If atmospheric conditions have not been set via setAtmosphericConditions(),
            returns default values: (101325 Pa, 300 K, 0.5, 0.02)

        Example:
            >>> pressure, temp, humidity, turbidity = solar.getAtmosphericConditions()
            >>> print(f"Pressure: {pressure} Pa, Temp: {temp} K")
        """
        self._check_context_alive()
        try:
            return solar_wrapper.getAtmosphericConditions(self._solar_pos)
        except Exception as e:
            raise SolarPositionError(f"Failed to get atmospheric conditions: {e}")

    # Solar angle calculations
    def getSunElevation(self) -> float:
        """
        Get the sun elevation angle in radians.
        
        Returns:
            Sun elevation angle in radians (0 = horizon, pi/2 = zenith)
            
        Raises:
            SolarPositionError: If calculation fails
            
        Example:
            >>> import math
            >>> elevation = solar.getSunElevation()
            >>> print(f"Sun is {math.degrees(elevation):.1f}° above horizon")
        """
        self._check_context_alive()
        try:
            return solar_wrapper.getSunElevation(self._solar_pos)
        except Exception as e:
            raise SolarPositionError(f"Failed to get sun elevation: {e}")
    
    def getSunZenith(self) -> float:
        """
        Get the sun zenith angle in radians.
        
        Returns:
            Sun zenith angle in radians (0 = zenith, pi/2 = horizon)
            
        Raises:
            SolarPositionError: If calculation fails
            
        Example:
            >>> import math
            >>> zenith = solar.getSunZenith()
            >>> print(f"Sun zenith angle: {math.degrees(zenith):.1f}°")
        """
        self._check_context_alive()
        try:
            return solar_wrapper.getSunZenith(self._solar_pos)
        except Exception as e:
            raise SolarPositionError(f"Failed to get sun zenith: {e}")
    
    def getSunAzimuth(self) -> float:
        """
        Get the sun azimuth angle in radians.
        
        Returns:
            Sun azimuth angle in radians (0 = North, pi/2 = East, pi = South,
            3*pi/2 = West)
            
        Raises:
            SolarPositionError: If calculation fails
            
        Example:
            >>> import math
            >>> azimuth = solar.getSunAzimuth()
            >>> print(f"Sun azimuth: {math.degrees(azimuth):.1f}° (compass bearing)")
        """
        self._check_context_alive()
        try:
            return solar_wrapper.getSunAzimuth(self._solar_pos)
        except Exception as e:
            raise SolarPositionError(f"Failed to get sun azimuth: {e}")
    
    # Solar direction vectors
    def getSunDirectionVector(self) -> vec3:
        """
        Get the sun direction as a 3D unit vector.
        
        Returns:
            vec3 representing the sun direction vector (x, y, z)
            
        Raises:
            SolarPositionError: If calculation fails
            
        Example:
            >>> direction = solar.getSunDirectionVector()
            >>> print(f"Sun direction vector: ({direction.x:.3f}, {direction.y:.3f}, {direction.z:.3f})")
        """
        self._check_context_alive()
        try:
            direction_list = solar_wrapper.getSunDirectionVector(self._solar_pos)
            return vec3(direction_list[0], direction_list[1], direction_list[2])
        except Exception as e:
            raise SolarPositionError(f"Failed to get sun direction vector: {e}")
    
    def getSunDirectionSpherical(self) -> SphericalCoord:
        """
        Get the sun direction as spherical coordinates.
        
        Returns:
            SphericalCoord with radius=1, elevation and azimuth in radians
            
        Raises:
            SolarPositionError: If calculation fails
            
        Example:
            >>> spherical = solar.getSunDirectionSpherical()
            >>> print(f"Spherical: r={spherical.radius}, elev={spherical.elevation:.3f}, az={spherical.azimuth:.3f}")
        """
        self._check_context_alive()
        try:
            spherical_list = solar_wrapper.getSunDirectionSpherical(self._solar_pos)
            return SphericalCoord(
                radius=spherical_list[0],
                elevation=spherical_list[1], 
                azimuth=spherical_list[2]
            )
        except Exception as e:
            raise SolarPositionError(f"Failed to get sun direction spherical: {e}")

    def setSunDirection(self, sundirection: SphericalCoord):
        """
        Override the computed solar position with a prescribed sun direction.

        By default the sun position is computed from the date, time and location
        set in the Context. Calling this method overrides that calculation, so
        all subsequent sun queries (elevation, zenith, azimuth, direction
        vectors) and flux calculations use the prescribed direction instead.

        Args:
            sundirection: SphericalCoord giving the direction of the sun.
                Elevation and azimuth are in radians.

        Raises:
            ValueError: If sundirection is not a SphericalCoord
            SolarPositionError: If the override fails

        Example:
            >>> from pyhelios.types import SphericalCoord
            >>> import math
            >>> solar.setSunDirection(SphericalCoord(1.0, math.radians(45), math.radians(180)))
            >>> math.degrees(solar.getSunElevation())
            45.0
        """
        if not isinstance(sundirection, SphericalCoord):
            raise ValueError(
                f"Sun direction must be a SphericalCoord, got {type(sundirection).__name__}"
            )

        self._check_context_alive()
        try:
            solar_wrapper.setSunDirection(
                self._solar_pos,
                sundirection.radius,
                sundirection.elevation,
                sundirection.azimuth,
            )
        except Exception as e:
            raise SolarPositionError(f"Failed to set sun direction: {e}")

    # Solar flux calculations
    def getSolarFlux(self, pressure_Pa: Optional[float] = None, temperature_K: Optional[float] = None,
                     humidity_rel: Optional[float] = None, turbidity: Optional[float] = None) -> float:
        """
        Calculate total solar flux (supports legacy and modern APIs).

        This method supports both legacy and modern APIs:
        - **Legacy API**: Pass all 4 atmospheric parameters explicitly
        - **Modern API**: Pass no parameters, uses atmospheric conditions from setAtmosphericConditions()

        Args:
            pressure_Pa: Atmospheric pressure in Pascals (e.g., 101325 for sea level) [optional]
            temperature_K: Temperature in Kelvin (e.g., 288.15 for 15°C) [optional]
            humidity_rel: Relative humidity as fraction (0.0-1.0) [optional]
            turbidity: Ångström's aerosol turbidity coefficient (β), the aerosol optical depth at 1 µm [optional]

        Returns:
            Total solar flux in W/m²

        Raises:
            ValueError: If some parameters provided but not all, or if values are invalid
            SolarPositionError: If calculation fails or atmospheric conditions not set (modern API)

        Note:
            The model uses the total column ozone of getOzoneColumn(). Where the ozone climatology
            has no data (high-latitude winter months, or poleward of 80 degrees) the calculation
            fails until the ozone column is set with setOzoneColumn(). The same applies to
            getSolarFluxPAR(), getSolarFluxNIR() and getDiffuseFraction().

        Examples:
            Legacy API (backward compatible):
            >>> flux = solar.getSolarFlux(101325, 288.15, 0.6, 0.1)

            Modern API (cleaner, reuses atmospheric state):
            >>> solar.setAtmosphericConditions(101325, 288.15, 0.6, 0.1)
            >>> flux = solar.getSolarFlux()  # No parameters needed
        """
        # Determine which API pattern is being used
        params_provided = [pressure_Pa is not None, temperature_K is not None,
                          humidity_rel is not None, turbidity is not None]

        if all(params_provided):
            # Legacy API: All parameters provided
            self._check_context_alive()
            try:
                with _solarposition_working_directory((_OZONE_CLIMATOLOGY,)):
                    return solar_wrapper.getSolarFlux(self._solar_pos, pressure_Pa, temperature_K, humidity_rel, turbidity)
            except Exception as e:
                raise SolarPositionError(f"Failed to calculate solar flux: {e}")

        elif not any(params_provided):
            # Modern API: No parameters, use atmospheric conditions from Context
            self._check_context_alive()
            try:
                with _solarposition_working_directory((_OZONE_CLIMATOLOGY,)):
                    return solar_wrapper.getSolarFluxFromState(self._solar_pos)
            except Exception as e:
                raise SolarPositionError(
                    f"Failed to calculate solar flux from atmospheric state: {e}\n"
                    "Hint: Call setAtmosphericConditions() first to use parameter-free API, "
                    "or provide all 4 atmospheric parameters for legacy API."
                )

        else:
            # Error: Partial parameters provided
            raise ValueError(
                "Either provide all atmospheric parameters (pressure_Pa, temperature_K, humidity_rel, turbidity) "
                "or provide none to use atmospheric conditions from setAtmosphericConditions(). "
                "Partial parameter sets are not supported."
            )
    
    def getSolarFluxPAR(self, pressure_Pa: Optional[float] = None, temperature_K: Optional[float] = None,
                        humidity_rel: Optional[float] = None, turbidity: Optional[float] = None) -> float:
        """
        Calculate PAR (Photosynthetically Active Radiation) solar flux.

        Supports both legacy (parameter-based) and modern (state-based) APIs.

        Args:
            pressure_Pa: Atmospheric pressure in Pascals [optional]
            temperature_K: Temperature in Kelvin [optional]
            humidity_rel: Relative humidity as fraction (0.0-1.0) [optional]
            turbidity: Ångström's aerosol turbidity coefficient (β), the aerosol optical depth at 1 µm [optional]

        Returns:
            PAR solar flux in W/m² (wavelength range ~400-700 nm)

        Raises:
            ValueError: If some parameters provided but not all
            SolarPositionError: If calculation fails

        Examples:
            Legacy: par_flux = solar.getSolarFluxPAR(101325, 288.15, 0.6, 0.1)
            Modern: solar.setAtmosphericConditions(101325, 288.15, 0.6, 0.1)
                    par_flux = solar.getSolarFluxPAR()
        """
        params_provided = [pressure_Pa is not None, temperature_K is not None,
                          humidity_rel is not None, turbidity is not None]

        if all(params_provided):
            self._check_context_alive()
            try:
                with _solarposition_working_directory((_OZONE_CLIMATOLOGY,)):
                    return solar_wrapper.getSolarFluxPAR(self._solar_pos, pressure_Pa, temperature_K, humidity_rel, turbidity)
            except Exception as e:
                raise SolarPositionError(f"Failed to calculate PAR flux: {e}")
        elif not any(params_provided):
            self._check_context_alive()
            try:
                with _solarposition_working_directory((_OZONE_CLIMATOLOGY,)):
                    return solar_wrapper.getSolarFluxPARFromState(self._solar_pos)
            except Exception as e:
                raise SolarPositionError(
                    f"Failed to calculate PAR flux from atmospheric state: {e}\n"
                    "Hint: Call setAtmosphericConditions() first."
                )
        else:
            raise ValueError("Provide all atmospheric parameters or none (use setAtmosphericConditions()).")
    
    def getSolarFluxNIR(self, pressure_Pa: Optional[float] = None, temperature_K: Optional[float] = None,
                        humidity_rel: Optional[float] = None, turbidity: Optional[float] = None) -> float:
        """
        Calculate NIR (Near-Infrared) solar flux.

        Supports both legacy (parameter-based) and modern (state-based) APIs.

        Args:
            pressure_Pa: Atmospheric pressure in Pascals [optional]
            temperature_K: Temperature in Kelvin [optional]
            humidity_rel: Relative humidity as fraction (0.0-1.0) [optional]
            turbidity: Ångström's aerosol turbidity coefficient (β), the aerosol optical depth at 1 µm [optional]

        Returns:
            NIR solar flux in W/m² (wavelength range >700 nm)

        Raises:
            ValueError: If some parameters provided but not all
            SolarPositionError: If calculation fails

        Examples:
            Legacy: nir_flux = solar.getSolarFluxNIR(101325, 288.15, 0.6, 0.1)
            Modern: solar.setAtmosphericConditions(101325, 288.15, 0.6, 0.1)
                    nir_flux = solar.getSolarFluxNIR()
        """
        params_provided = [pressure_Pa is not None, temperature_K is not None,
                          humidity_rel is not None, turbidity is not None]

        if all(params_provided):
            self._check_context_alive()
            try:
                with _solarposition_working_directory((_OZONE_CLIMATOLOGY,)):
                    return solar_wrapper.getSolarFluxNIR(self._solar_pos, pressure_Pa, temperature_K, humidity_rel, turbidity)
            except Exception as e:
                raise SolarPositionError(f"Failed to calculate NIR flux: {e}")
        elif not any(params_provided):
            self._check_context_alive()
            try:
                with _solarposition_working_directory((_OZONE_CLIMATOLOGY,)):
                    return solar_wrapper.getSolarFluxNIRFromState(self._solar_pos)
            except Exception as e:
                raise SolarPositionError(
                    f"Failed to calculate NIR flux from atmospheric state: {e}\n"
                    "Hint: Call setAtmosphericConditions() first."
                )
        else:
            raise ValueError("Provide all atmospheric parameters or none (use setAtmosphericConditions()).")
    
    def getDiffuseFraction(self, pressure_Pa: Optional[float] = None, temperature_K: Optional[float] = None,
                           humidity_rel: Optional[float] = None, turbidity: Optional[float] = None) -> float:
        """
        Calculate the diffuse fraction of solar radiation.

        Supports both legacy (parameter-based) and modern (state-based) APIs.

        Args:
            pressure_Pa: Atmospheric pressure in Pascals [optional]
            temperature_K: Temperature in Kelvin [optional]
            humidity_rel: Relative humidity as fraction (0.0-1.0) [optional]
            turbidity: Ångström's aerosol turbidity coefficient (β), the aerosol optical depth at 1 µm [optional]

        Returns:
            Diffuse fraction as ratio (0.0-1.0) where:
            - 0.0 = all direct radiation
            - 1.0 = all diffuse radiation

        Raises:
            ValueError: If some parameters provided but not all
            SolarPositionError: If calculation fails

        Examples:
            Legacy: diffuse = solar.getDiffuseFraction(101325, 288.15, 0.6, 0.1)
            Modern: solar.setAtmosphericConditions(101325, 288.15, 0.6, 0.1)
                    diffuse = solar.getDiffuseFraction()
        """
        params_provided = [pressure_Pa is not None, temperature_K is not None,
                          humidity_rel is not None, turbidity is not None]

        if all(params_provided):
            self._check_context_alive()
            try:
                with _solarposition_working_directory((_OZONE_CLIMATOLOGY,)):
                    return solar_wrapper.getDiffuseFraction(self._solar_pos, pressure_Pa, temperature_K, humidity_rel, turbidity)
            except Exception as e:
                raise SolarPositionError(f"Failed to calculate diffuse fraction: {e}")
        elif not any(params_provided):
            self._check_context_alive()
            try:
                with _solarposition_working_directory((_OZONE_CLIMATOLOGY,)):
                    return solar_wrapper.getDiffuseFractionFromState(self._solar_pos)
            except Exception as e:
                raise SolarPositionError(
                    f"Failed to calculate diffuse fraction from atmospheric state: {e}\n"
                    "Hint: Call setAtmosphericConditions() first."
                )
        else:
            raise ValueError("Provide all atmospheric parameters or none (use setAtmosphericConditions()).")

    def getAmbientLongwaveFlux(self, temperature_K: Optional[float] = None,
                               humidity_rel: Optional[float] = None) -> float:
        """
        Calculate the ambient (sky) longwave radiation flux.

        This method supports both legacy and modern APIs:
        - **Legacy API**: Pass temperature and humidity explicitly
        - **Modern API**: Pass no parameters, uses atmospheric conditions from setAtmosphericConditions()

        Args:
            temperature_K: Temperature in Kelvin [optional]
            humidity_rel: Relative humidity as fraction (0.0-1.0) [optional]

        Returns:
            Ambient longwave flux in W/m²

        Raises:
            ValueError: If one parameter provided but not the other
            SolarPositionError: If calculation fails

        Note:
            The longwave flux model is based on Prata (1996).
            Returns downwelling longwave radiation flux on a horizontal surface, integrated over
            all longwave wavelengths. It is the diffuse flux to give an emission band without
            wavelength bounds. For the sky flux within a thermal band with wavelength bounds,
            use getThermalSkyFlux().

        Examples:
            Legacy API:
            >>> lw_flux = solar.getAmbientLongwaveFlux(288.15, 0.6)

            Modern API (uses temperature and humidity from setAtmosphericConditions):
            >>> solar.setAtmosphericConditions(101325, 288.15, 0.6, 0.1)
            >>> lw_flux = solar.getAmbientLongwaveFlux()
        """
        params_provided = [temperature_K is not None, humidity_rel is not None]

        if all(params_provided):
            # Legacy API: Both parameters provided
            # C++ has deprecated 2-parameter version, but we emulate it
            # by setting atmospheric conditions temporarily
            self._check_context_alive()
            try:
                # Get current conditions to restore later
                saved_conditions = solar_wrapper.getAtmosphericConditions(self._solar_pos)

                # Set temporary conditions with provided temperature and humidity
                # Use current values for pressure and turbidity
                solar_wrapper.setAtmosphericConditions(self._solar_pos,
                                                       saved_conditions[0],  # pressure (unchanged)
                                                       temperature_K,         # temperature (provided)
                                                       humidity_rel,          # humidity (provided)
                                                       saved_conditions[3])   # turbidity (unchanged)

                # Call parameter-free version
                result = solar_wrapper.getAmbientLongwaveFluxFromState(self._solar_pos)

                # Restore original conditions
                solar_wrapper.setAtmosphericConditions(self._solar_pos, *saved_conditions)

                return result

            except Exception as e:
                raise SolarPositionError(f"Failed to calculate ambient longwave flux: {e}")

        elif not any(params_provided):
            # Modern API: No parameters, use atmospheric conditions from Context
            self._check_context_alive()
            try:
                return solar_wrapper.getAmbientLongwaveFluxFromState(self._solar_pos)
            except Exception as e:
                raise SolarPositionError(
                    f"Failed to calculate ambient longwave flux from atmospheric state: {e}\n"
                    "Hint: Call setAtmosphericConditions() first to use parameter-free API, "
                    "or provide temperature_K and humidity_rel for legacy API."
                )

        else:
            # Error: Only one parameter provided
            raise ValueError(
                "Either provide both temperature_K and humidity_rel, "
                "or provide neither to use atmospheric conditions from setAtmosphericConditions()."
            )

    # Time calculations
    def getSunriseTime(self) -> Time:
        """
        Calculate sunrise time for the current date and location.
        
        Returns:
            Time object with sunrise time (hour, minute, second)
            
        Raises:
            SolarPositionError: If calculation fails
            
        Example:
            >>> sunrise = solar.getSunriseTime()
            >>> print(f"Sunrise: {sunrise}")  # Prints as HH:MM:SS
        """
        self._check_context_alive()
        try:
            hour, minute, second = solar_wrapper.getSunriseTime(self._solar_pos)
            return Time(hour, minute, second)
        except Exception as e:
            raise SolarPositionError(f"Failed to calculate sunrise time: {e}")
    
    def getSunsetTime(self) -> Time:
        """
        Calculate sunset time for the current date and location.
        
        Returns:
            Time object with sunset time (hour, minute, second)
            
        Raises:
            SolarPositionError: If calculation fails
            
        Example:
            >>> sunset = solar.getSunsetTime()
            >>> print(f"Sunset: {sunset}")  # Prints as HH:MM:SS
        """
        self._check_context_alive()
        try:
            hour, minute, second = solar_wrapper.getSunsetTime(self._solar_pos)
            return Time(hour, minute, second)
        except Exception as e:
            raise SolarPositionError(f"Failed to calculate sunset time: {e}")
    
    # Calibration functions
    def calibrateTurbidityFromTimeseries(self, timeseries_label: str) -> float:
        """
        Calibrate atmospheric turbidity using timeseries data.

        Args:
            timeseries_label: Label of timeseries data in Context. The data should
                be global shortwave radiation flux on a horizontal plane in W/m^2,
                and should contain at least one day of clear-sky conditions.

        Returns:
            The calibrated turbidity value

        Raises:
            ValueError: If timeseries label is invalid
            SolarPositionError: If calibration fails

        Note:
            This method does not itself apply the calibrated value. Pass the
            returned turbidity to setAtmosphericConditions() to use it.

        Example:
            >>> turbidity = solar.calibrateTurbidityFromTimeseries("solar_irradiance")
            >>> solar.setAtmosphericConditions(101325, 293.15, 0.5, turbidity)
        """
        if not timeseries_label:
            raise ValueError("Timeseries label cannot be empty")
        
        self._check_context_alive()
        try:
            with _solarposition_working_directory((_OZONE_CLIMATOLOGY,)):
                return solar_wrapper.calibrateTurbidityFromTimeseries(self._solar_pos, timeseries_label)
        except Exception as e:
            raise SolarPositionError(f"Failed to calibrate turbidity: {e}")
    
    def enableCloudCalibration(self, timeseries_label: str):
        """
        Enable cloud calibration using timeseries data.
        
        Args:
            timeseries_label: Label of cloud timeseries data in Context
            
        Raises:
            ValueError: If timeseries label is invalid
            SolarPositionError: If calibration setup fails
            
        Example:
            >>> solar.enableCloudCalibration("cloud_cover")
        """
        if not timeseries_label:
            raise ValueError("Timeseries label cannot be empty")
        
        self._check_context_alive()
        try:
            solar_wrapper.enableCloudCalibration(self._solar_pos, timeseries_label)
        except Exception as e:
            raise SolarPositionError(f"Failed to enable cloud calibration: {e}")
    
    def disableCloudCalibration(self):
        """
        Disable cloud calibration.

        Raises:
            SolarPositionError: If operation fails

        Example:
            >>> solar.disableCloudCalibration()
        """
        self._check_context_alive()
        try:
            solar_wrapper.disableCloudCalibration(self._solar_pos)
        except Exception as e:
            raise SolarPositionError(f"Failed to disable cloud calibration: {e}")

    # Prague Sky Model Methods (v1.3.59+)
    def enablePragueSkyModel(self):
        """
        Enable Prague Sky Model for physically-based sky radiance calculations.

        The Prague Sky Model provides high-quality spectral and angular sky radiance
        distribution for accurate diffuse radiation modeling. It accounts for Rayleigh
        and Mie scattering to produce realistic sky radiance patterns across the
        360-1480 nm spectral range.

        Raises:
            SolarPositionError: If operation fails

        Note:
            After enabling, call updatePragueSkyModel() to compute and store spectral-angular
            parameters in Context global data. Requires ~27 MB data file:
            plugins/solarposition/lib/prague_sky_model/PragueSkyModelReduced.dat

        Example:
            >>> with Context() as context:
            ...     with SolarPosition(context) as solar:
            ...         solar.enablePragueSkyModel()
            ...         solar.updatePragueSkyModel()
        """
        self._check_context_alive()
        try:
            with _solarposition_working_directory():
                solar_wrapper.enablePragueSkyModel(self._solar_pos)
        except Exception as e:
            raise SolarPositionError(f"Failed to enable Prague Sky Model: {e}")

    def isPragueSkyModelEnabled(self) -> bool:
        """
        Check if Prague Sky Model is currently enabled.

        Returns:
            True if Prague Sky Model has been enabled via enablePragueSkyModel(), False otherwise

        Raises:
            SolarPositionError: If operation fails

        Example:
            >>> if solar.isPragueSkyModelEnabled():
            ...     print("Prague Sky Model is active")
        """
        self._check_context_alive()
        try:
            return solar_wrapper.isPragueSkyModelEnabled(self._solar_pos)
        except Exception as e:
            raise SolarPositionError(f"Failed to check Prague Sky Model status: {e}")

    def updatePragueSkyModel(self, ground_albedo: float = 0.33):
        """
        Update Prague Sky Model and store spectral-angular parameters in Context.

        This is a computationally intensive operation (~1100 model queries with OpenMP
        parallelization) that computes sky radiance distribution for current atmospheric
        and solar conditions. Use pragueSkyModelNeedsUpdate() for lazy evaluation to
        avoid unnecessary updates.

        Args:
            ground_albedo: Ground surface albedo (default: 0.33 for typical soil/vegetation)

        Raises:
            SolarPositionError: If update fails

        Note:
            Reads turbidity (Ångström's β, the aerosol optical depth at 1 µm) from Context
            atmospheric conditions and converts the aerosol optical depth at 550 nm to the
            visibility that parameterizes the Prague model, limited to its range of
            20-131.8 km: turbidities below about 0.029 (including the default of 0.02) use the
            cleanest Prague atmosphere and those above about 0.21 the haziest. Stores results in Context
            global data as "prague_sky_spectral_params" (1350 floats: 225 wavelengths × 6 params),
            "prague_sky_sun_direction", "prague_sky_visibility_km", "prague_sky_ground_albedo",
            and "prague_sky_valid" flag.

        Example:
            >>> solar.setAtmosphericConditions(101325, 288.15, 0.6, 0.1)
            >>> solar.updatePragueSkyModel(ground_albedo=0.25)
        """
        self._check_context_alive()
        try:
            with _solarposition_working_directory():
                solar_wrapper.updatePragueSkyModel(self._solar_pos, ground_albedo)
        except Exception as e:
            raise SolarPositionError(f"Failed to update Prague Sky Model: {e}")

    def pragueSkyModelNeedsUpdate(self, ground_albedo: float = 0.33,
                                   sun_tolerance: float = 0.01,
                                   turbidity_tolerance: float = 0.02,
                                   albedo_tolerance: float = 0.05) -> bool:
        """
        Check if Prague Sky Model needs updating based on changed conditions.

        Enables lazy evaluation to avoid expensive Prague updates when conditions haven't
        changed significantly. Compares current state against cached values.

        Args:
            ground_albedo: Current ground albedo (default: 0.33)
            sun_tolerance: Threshold for sun direction changes (default: 0.01 ≈ 0.57°)
            turbidity_tolerance: Relative threshold for turbidity (default: 0.02 = 2%)
            albedo_tolerance: Threshold for albedo changes (default: 0.05 = 5%)

        Returns:
            True if updatePragueSkyModel() should be called, False if cached data is valid

        Raises:
            SolarPositionError: If check fails

        Note:
            Reads turbidity from Context atmospheric conditions for comparison.

        Example:
            >>> if solar.pragueSkyModelNeedsUpdate():
            ...     solar.updatePragueSkyModel()
        """
        self._check_context_alive()
        try:
            return solar_wrapper.pragueSkyModelNeedsUpdate(self._solar_pos, ground_albedo,
                                                           sun_tolerance, turbidity_tolerance,
                                                           albedo_tolerance)
        except Exception as e:
            raise SolarPositionError(f"Failed to check Prague Sky Model update status: {e}")

    # SSolar-GOA Spectral Solar Model Methods
    def calculateDirectSolarSpectrum(self, label: str, resolution_nm: float = 1.0):
        """
        Calculate direct beam solar spectrum.

        Computes the spectral irradiance of the direct solar beam on a surface normal to
        the sun direction from 300 to 2600 nm, with a spectral model that follows SSolar-GOA
        (Cachorro et al. 2022). Results are stored in Context global data as a vector of
        (wavelength, irradiance) pairs.

        Args:
            label: Label to store the spectrum data in Context global data
            resolution_nm: Wavelength resolution in nanometers (1.0-2300.0).
                          Lower values give finer spectral resolution but require
                          more computation. Default is 1.0 nm.

        Raises:
            ValueError: If label is empty or resolution is out of valid range
            SolarPositionError: If calculation fails

        Note:
            - Requires Context time/date to be set for accurate solar position
            - Atmospheric conditions are taken from setAtmosphericConditions(), the ozone column
              from getOzoneColumn() and the ground albedo from setGroundAlbedo(); cloud
              calibration is applied if enabled with enableCloudCalibration()
            - The spectrum is referred to by its label, e.g. in RadiationModel.setSourceSpectrum()
              or RadiationModel.setDiffuseSpectrum(); context.getGlobalDataSize(label) gives its
              number of wavelengths
            - Fails if the sun is at or below the horizon, if the relative humidity is not
              greater than zero, or if no ozone column was set and the climatology has no data
              for the location and date (see getOzoneColumn())

        Example:
            >>> with Context() as context:
            ...     context.setDate(2023, 6, 21)
            ...     context.setTime(12, 0)
            ...     with SolarPosition(context) as solar:
            ...         solar.calculateDirectSolarSpectrum("direct_spectrum", resolution_nm=5.0)
            ...         n_wavelengths = context.getGlobalDataSize("direct_spectrum")  # 461
        """
        if not label:
            raise ValueError("Label cannot be empty")
        if resolution_nm < 1.0 or resolution_nm > 2300.0:
            raise ValueError(f"Wavelength resolution must be between 1 and 2300 nm, got: {resolution_nm}")

        self._check_context_alive()
        try:
            with _solarposition_working_directory(_SPECTRAL_MODEL_ASSETS):
                solar_wrapper.calculateDirectSolarSpectrum(self._solar_pos, label, resolution_nm)
        except Exception as e:
            raise SolarPositionError(f"Failed to calculate direct solar spectrum: {e}")

    def calculateDiffuseSolarSpectrum(self, label: str, resolution_nm: float = 1.0):
        """
        Calculate diffuse solar spectrum.

        Computes the diffuse (sky) spectral irradiance on a horizontal surface from 300 to
        2600 nm, including light reflected by the ground and scattered back down by the
        atmosphere, with a spectral model that follows SSolar-GOA (Cachorro et al. 2022).
        Results are stored in Context global data as a vector of (wavelength, irradiance) pairs.

        Args:
            label: Label to store the spectrum data in Context global data
            resolution_nm: Wavelength resolution in nanometers (1.0-2300.0).
                          Lower values give finer spectral resolution but require
                          more computation. Default is 1.0 nm.

        Raises:
            ValueError: If label is empty or resolution is out of valid range
            SolarPositionError: If calculation fails

        Note:
            - Requires Context time/date to be set for accurate solar position
            - Atmospheric conditions are taken from setAtmosphericConditions(), the ozone column
              from getOzoneColumn() and the ground albedo from setGroundAlbedo(); cloud
              calibration is applied if enabled with enableCloudCalibration()
            - The spectrum is referred to by its label, e.g. in RadiationModel.setSourceSpectrum()
              or RadiationModel.setDiffuseSpectrum(); context.getGlobalDataSize(label) gives its
              number of wavelengths
            - Fails if the sun is at or below the horizon, if the relative humidity is not
              greater than zero, or if no ozone column was set and the climatology has no data
              for the location and date (see getOzoneColumn())
            - Diffuse radiation results from atmospheric scattering (Rayleigh, aerosol)

        Example:
            >>> with Context() as context:
            ...     context.setDate(2023, 6, 21)
            ...     context.setTime(12, 0)
            ...     with SolarPosition(context) as solar:
            ...         solar.calculateDiffuseSolarSpectrum("diffuse_spectrum", resolution_nm=5.0)
            ...         n_wavelengths = context.getGlobalDataSize("diffuse_spectrum")  # 461
        """
        if not label:
            raise ValueError("Label cannot be empty")
        if resolution_nm < 1.0 or resolution_nm > 2300.0:
            raise ValueError(f"Wavelength resolution must be between 1 and 2300 nm, got: {resolution_nm}")

        self._check_context_alive()
        try:
            with _solarposition_working_directory(_SPECTRAL_MODEL_ASSETS):
                solar_wrapper.calculateDiffuseSolarSpectrum(self._solar_pos, label, resolution_nm)
        except Exception as e:
            raise SolarPositionError(f"Failed to calculate diffuse solar spectrum: {e}")

    def calculateGlobalSolarSpectrum(self, label: str, resolution_nm: float = 1.0):
        """
        Calculate global (total) solar spectrum.

        Computes the global (direct plus diffuse) spectral irradiance on a horizontal surface
        from 300 to 2600 nm, with a spectral model that follows SSolar-GOA (Cachorro et al. 2022).
        Results are stored in Context global data as a vector of (wavelength, irradiance) pairs.

        Args:
            label: Label to store the spectrum data in Context global data
            resolution_nm: Wavelength resolution in nanometers (1.0-2300.0).
                          Lower values give finer spectral resolution but require
                          more computation. Default is 1.0 nm.

        Raises:
            ValueError: If label is empty or resolution is out of valid range
            SolarPositionError: If calculation fails

        Note:
            - Requires Context time/date to be set for accurate solar position
            - Atmospheric conditions are taken from setAtmosphericConditions(), the ozone column
              from getOzoneColumn() and the ground albedo from setGroundAlbedo(); cloud
              calibration is applied if enabled with enableCloudCalibration()
            - The spectrum is referred to by its label, e.g. in RadiationModel.setSourceSpectrum()
              or RadiationModel.setDiffuseSpectrum(); context.getGlobalDataSize(label) gives its
              number of wavelengths
            - Fails if the sun is at or below the horizon, if the relative humidity is not
              greater than zero, or if no ozone column was set and the climatology has no data
              for the location and date (see getOzoneColumn())
            - Global spectrum = direct beam + diffuse (sky) radiation
            - Most useful for plant canopy modeling and photosynthesis calculations

        Example:
            >>> with Context() as context:
            ...     context.setDate(2023, 6, 21)
            ...     context.setTime(12, 0)
            ...     with SolarPosition(context) as solar:
            ...         solar.calculateGlobalSolarSpectrum("global_spectrum", resolution_nm=10.0)
            ...         n_wavelengths = context.getGlobalDataSize("global_spectrum")  # 231
        """
        if not label:
            raise ValueError("Label cannot be empty")
        if resolution_nm < 1.0 or resolution_nm > 2300.0:
            raise ValueError(f"Wavelength resolution must be between 1 and 2300 nm, got: {resolution_nm}")

        self._check_context_alive()
        try:
            with _solarposition_working_directory(_SPECTRAL_MODEL_ASSETS):
                solar_wrapper.calculateGlobalSolarSpectrum(self._solar_pos, label, resolution_nm)
        except Exception as e:
            raise SolarPositionError(f"Failed to calculate global solar spectrum: {e}")

    # Ozone column and ground albedo (v1.3.90+)
    def setOzoneColumn(self, ozone_DU: float) -> None:
        """
        Set the total column ozone, overriding the climatological value.

        The ozone column is used by the broadband solar flux model (getSolarFlux() family), the
        spectral solar irradiance model and the sensor atmosphere models. It is stored in Context
        global data as "atmosphere_ozone_DU".

        Args:
            ozone_DU: Total column ozone in Dobson units (must be > 0)

        Raises:
            ValueError: If ozone_DU is not a positive number
            SolarPositionError: If operation fails

        Example:
            >>> solar.setOzoneColumn(310.0)  # e.g., from a local measurement
        """
        if isinstance(ozone_DU, bool) or not isinstance(ozone_DU, (int, float)):
            raise ValueError(f"Ozone column must be a number, got {type(ozone_DU).__name__}")
        if not ozone_DU > 0.0:
            raise ValueError(f"Ozone column must be positive, got: {ozone_DU}")

        self._check_context_alive()
        try:
            solar_wrapper.setOzoneColumn(self._solar_pos, ozone_DU)
        except Exception as e:
            raise SolarPositionError(f"Failed to set ozone column: {e}")

    def getOzoneColumn(self) -> float:
        """
        Get the total column ozone used by the solar radiation models.

        Returns the ozone column set with setOzoneColumn(), if any. Otherwise returns the monthly
        zonal-mean climatology of the NASA SBUV Merged Ozone Data Set averaged over 2005-2024,
        interpolated linearly in latitude between the centers of its 5-degree latitude bands and in
        the day of the year between the middles of the months.

        Returns:
            Total column ozone in Dobson units

        Raises:
            SolarPositionError: If no ozone column was set and the climatology has no data for the
                location and date. The climatology has no data in high-latitude winter months or
                poleward of 80 degrees; set the ozone column with setOzoneColumn() there.

        Note:
            Next to a latitude band or month without data, the value of the band or month containing
            the location or date is used rather than interpolating toward the missing one.

        Example:
            >>> ozone_DU = solar.getOzoneColumn()
        """
        self._check_context_alive()
        try:
            with _solarposition_working_directory((_OZONE_CLIMATOLOGY,)):
                return solar_wrapper.getOzoneColumn(self._solar_pos)
        except Exception as e:
            raise SolarPositionError(f"Failed to get ozone column: {e}")

    def setGroundAlbedo(self, albedo: float) -> None:
        """
        Set the albedo of the ground surrounding the scene.

        The ground albedo sets how much light is reflected back and forth between the ground and
        the atmosphere, which increases the global and diffuse irradiance, most strongly at short
        wavelengths. It is stored in Context global data as "atmosphere_ground_albedo".

        Args:
            albedo: Broadband ground albedo (must be between 0 and 1)

        Raises:
            ValueError: If albedo is not a number between 0 and 1
            SolarPositionError: If operation fails

        Note:
            The ground albedo affects the global and diffuse spectra of calculateGlobalSolarSpectrum()
            and calculateDiffuseSolarSpectrum(), and the ground irradiance and adjacency radiance of
            calculateSensorAtmosphereSpectra(); without cloud calibration it does not affect the direct
            beam. It does not affect the broadband getSolarFlux() family of methods, and the Prague sky
            model takes its ground albedo as an argument of updatePragueSkyModel().

        Example:
            >>> solar.setGroundAlbedo(0.8)  # e.g., fresh snow
        """
        if isinstance(albedo, bool) or not isinstance(albedo, (int, float)):
            raise ValueError(f"Ground albedo must be a number, got {type(albedo).__name__}")
        if not 0.0 <= albedo <= 1.0:
            raise ValueError(f"Ground albedo must be between 0 and 1, got: {albedo}")

        self._check_context_alive()
        try:
            solar_wrapper.setGroundAlbedo(self._solar_pos, albedo)
        except Exception as e:
            raise SolarPositionError(f"Failed to set ground albedo: {e}")

    def getGroundAlbedo(self) -> float:
        """
        Get the albedo of the ground surrounding the scene.

        Returns:
            Ground albedo set by setGroundAlbedo(), or 0.2 if it has not been set

        Raises:
            SolarPositionError: If operation fails

        Example:
            >>> albedo = solar.getGroundAlbedo()
        """
        self._check_context_alive()
        try:
            return solar_wrapper.getGroundAlbedo(self._solar_pos)
        except Exception as e:
            raise SolarPositionError(f"Failed to get ground albedo: {e}")

    # Sensor atmosphere methods (v1.3.90+)
    def calculateSensorAtmosphereSpectra(self, label: str, direction_to_sensor: vec3,
                                         resolution_nm: float = 1.0) -> None:
        """
        Calculate the spectral atmospheric quantities needed to simulate imagery from a sensor
        above the atmosphere (e.g., a satellite).

        Radiance reaching the sensor is modeled as L_sensor = L_path + T_dir_up * L_surface + L_adj,
        where L_surface is the radiance leaving the scene. The atmosphere is described by a look-up
        table computed with the 6S radiative transfer code (continental aerosol), which gives both
        the upward path to the sensor and the downward solar illumination of the scene. For the two
        to be consistent, illuminate the scene with the "_direct_irradiance" and
        "_diffuse_irradiance" spectra stored by this method rather than those of
        calculateDirectSolarSpectrum() and calculateDiffuseSolarSpectrum().

        The following spectra are stored in Context global data as vectors of vec2
        (wavelength_nm, value), each labeled with the given label followed by a suffix:

        - "_path_radiance": radiance scattered by the atmosphere into the sensor without reaching
          the ground (W/m²/sr/nm)
        - "_adjacency_radiance": radiance reflected by the surrounding ground (albedo from
          setGroundAlbedo()) and scattered by the atmosphere into the sensor (W/m²/sr/nm)
        - "_upward_direct_transmittance": transmittance of the surface-leaving radiance straight to
          the sensor, including gas absorption
        - "_upward_diffuse_transmittance": transmittance of surface-leaving radiance scattered into
          the sensor direction, including gas absorption
        - "_spherical_albedo": spherical albedo of the atmosphere
        - "_direct_irradiance": direct solar irradiance at the ground, normal to the sun direction
          (W/m²/nm)
        - "_diffuse_irradiance": diffuse solar irradiance at the ground on a horizontal surface
          (W/m²/nm)
        - "_global_irradiance": global solar irradiance at the ground on a horizontal surface
          (W/m²/nm)

        The unit vector toward the sensor is also stored, as vec3 global data with the suffix
        "_direction_to_sensor".

        Args:
            label: Prefix of the labels under which the spectra are stored in Context global data
            direction_to_sensor: Vector pointing from the scene toward the sensor (need not be
                normalized). Its zenith angle must not exceed 60 degrees.
            resolution_nm: Wavelength resolution in nanometers (1.0-2300.0). Default is 1.0 nm.

        Raises:
            ValueError: If label is empty, direction_to_sensor is not a non-zero vec3, or
                resolution is out of valid range
            SolarPositionError: If calculation fails, including for conditions outside the range of
                the look-up table

        Note:
            - Atmospheric conditions are taken from setAtmosphericConditions(), the ozone column
              from getOzoneColumn() and the ground albedo from setGroundAlbedo(). The turbidity is
              converted to aerosol optical depth at 550 nm with an Ångström exponent of 1.3.
            - The look-up table covers solar zenith angles up to 70 degrees, view zenith angles up
              to 60 degrees, aerosol optical depths at 550 nm up to 1.2 (turbidity up to about 0.55)
              and surface pressures from 701.2 to 1013 hPa (ground elevations up to about 3 km);
              pressures up to 1050 hPa are extrapolated linearly. Its gas tables cover water vapor
              paths up to 320 g/cm². Conditions outside these ranges, and a sun below the horizon,
              raise an error.
            - The sensor is taken to be above the atmosphere. The model assumes clear sky and
              cannot be used with cloud calibration enabled.
            - RadiationModel.enableCameraAtmosphere() applies these spectra to a camera's images.

        Example:
            >>> solar.setAtmosphericConditions(101325, 298, 0.5, 0.1)
            >>> solar.setGroundAlbedo(0.15)
            >>> solar.calculateSensorAtmosphereSpectra("satellite", vec3(0, 0, 1))  # sensor at nadir
            >>> radiation.setSourceSpectrum(sun_source, "satellite_direct_irradiance")
            >>> radiation.setDiffuseSpectrum("red", "satellite_diffuse_irradiance")
        """
        _validate_sensor_arguments(label, direction_to_sensor)
        if isinstance(resolution_nm, bool) or not isinstance(resolution_nm, (int, float)):
            raise ValueError(f"Wavelength resolution must be a number, got {type(resolution_nm).__name__}")
        if resolution_nm < 1.0 or resolution_nm > 2300.0:
            raise ValueError(f"Wavelength resolution must be between 1 and 2300 nm, got: {resolution_nm}")

        self._check_context_alive()
        try:
            with _solarposition_working_directory(_SPECTRAL_MODEL_ASSETS):
                solar_wrapper.calculateSensorAtmosphereSpectra(self._solar_pos, label,
                                                               direction_to_sensor.to_list(), resolution_nm)
        except Exception as e:
            raise SolarPositionError(f"Failed to calculate sensor atmosphere spectra: {e}")

    def calculateSensorThermalAtmosphere(self, label: str, direction_to_sensor: vec3) -> None:
        """
        Calculate the thermal infrared atmospheric quantities needed to simulate thermal imagery
        from a sensor above the atmosphere (e.g., a satellite).

        Radiance reaching the sensor at a thermal wavelength is modeled as
        L_sensor = tau * L_surface + L_up, where L_surface is the radiance leaving the scene
        (emitted plus reflected sky radiance), tau the atmospheric transmittance and L_up the
        radiance emitted upward by the atmosphere. These are interpolated from a look-up table
        computed with the libRadtran radiative transfer code (clear sky without aerosol).

        The following spectra are stored in Context global data as vectors of vec2
        (wavelength of the bin center in nm, value), with 234 points from 5502 to 15326 nm, each
        labeled with the given label followed by a suffix:

        - "_thermal_transmittance": atmospheric transmittance from the ground to the sensor
        - "_thermal_upwelling_radiance": radiance emitted by the atmosphere toward the sensor
          (W/m²/sr/nm)
        - "_thermal_downwelling_radiance": sky irradiance on a horizontal surface at the ground
          divided by pi (W/m²/sr/nm), independent of the view direction

        The column water vapor (float, g/cm²) is stored with the suffix "_thermal_water_vapor_cm",
        and the unit vector toward the sensor, as vec3, with the suffix "_direction_to_sensor".

        Args:
            label: Prefix of the labels under which the results are stored in Context global data
            direction_to_sensor: Vector pointing from the scene toward the sensor (need not be
                normalized). Its zenith angle must not exceed 60 degrees.

        Raises:
            ValueError: If label is empty or direction_to_sensor is not a non-zero vec3
            SolarPositionError: If calculation fails, including for conditions outside the range of
                the look-up table

        Note:
            - The atmospheric profile is built from the surface air temperature, humidity and
              pressure set with setAtmosphericConditions() and the ozone column of
              getOzoneColumn(). The column water vapor, derived from the temperature and humidity,
              must lie within 0.1-7.5 g/cm², the pressure within 701.2-1050 hPa (pressures above
              1013 hPa are extrapolated) and the ozone column within 150-450 DU. The supported air
              temperatures depend on the pressure: 246.2-321.7 K at 1013 hPa.
            - The model assumes clear sky and does not depend on the position of the sun, so
              night-time imagery can be simulated. Reflected sunlight, which is significant below
              about 5 µm, is not included.

        Example:
            >>> solar.setAtmosphericConditions(101325, 298, 0.5, 0.1)
            >>> solar.calculateSensorThermalAtmosphere("satellite", vec3(0, 0, 1))  # sensor at nadir
            >>> context.getGlobalDataSize("satellite_thermal_transmittance")
            234
        """
        _validate_sensor_arguments(label, direction_to_sensor)

        self._check_context_alive()
        try:
            with _solarposition_working_directory(_THERMAL_MODEL_ASSETS):
                solar_wrapper.calculateSensorThermalAtmosphere(self._solar_pos, label,
                                                               direction_to_sensor.to_list())
        except Exception as e:
            raise SolarPositionError(f"Failed to calculate sensor thermal atmosphere: {e}")

    def getThermalSkyFlux(self, wavelength_min_nm: float, wavelength_max_nm: float) -> float:
        """
        Calculate the sky longwave irradiance on a horizontal surface within a thermal band.

        This is the band-specific counterpart of getAmbientLongwaveFlux(): the downward irradiance
        emitted by a clear-sky atmosphere between two wavelengths, integrated from the downwelling
        radiance of the thermal atmosphere look-up table (see calculateSensorThermalAtmosphere()).
        It is the diffuse flux to give an emission band with the same wavelength bounds
        (RadiationModel.setDiffuseRadiationFlux()), so that the sky radiance the scene reflects is
        consistent with the thermal sensor atmosphere.

        Args:
            wavelength_min_nm: Lower wavelength bound of the band in nm
            wavelength_max_nm: Upper wavelength bound of the band in nm

        Returns:
            Sky longwave irradiance within the band on a horizontal surface, in W/m²

        Raises:
            ValueError: If the bounds are not numbers satisfying 0 < wavelength_min_nm < wavelength_max_nm
            SolarPositionError: If calculation fails, including for bounds outside 5502-15326 nm or
                atmospheric conditions outside the ranges given for calculateSensorThermalAtmosphere()

        Example:
            >>> radiation.addRadiationBand("TIR", 10600, 11190)  # e.g., Landsat 8 TIRS band 10
            >>> radiation.setDiffuseRadiationFlux("TIR", solar.getThermalSkyFlux(10600, 11190))
        """
        for name, value in (("wavelength_min_nm", wavelength_min_nm), ("wavelength_max_nm", wavelength_max_nm)):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{name} must be a number, got {type(value).__name__}")
        if wavelength_min_nm <= 0.0 or wavelength_max_nm <= wavelength_min_nm:
            raise ValueError(
                f"Wavelength bounds must satisfy 0 < wavelength_min_nm < wavelength_max_nm, "
                f"got: ({wavelength_min_nm}, {wavelength_max_nm})")

        self._check_context_alive()
        try:
            with _solarposition_working_directory(_THERMAL_MODEL_ASSETS):
                return solar_wrapper.getThermalSkyFlux(self._solar_pos, wavelength_min_nm, wavelength_max_nm)
        except Exception as e:
            raise SolarPositionError(f"Failed to calculate thermal sky flux: {e}")

    def is_available(self) -> bool:
        """
        Check if SolarPosition is available in current build.
        
        Returns:
            True if plugin is available, False otherwise
        """
        registry = get_plugin_registry()
        return registry.is_plugin_available('solarposition')


# Convenience function
def create_solar_position(context: Context, utc_offset: Optional[float] = None,
                         latitude: Optional[float] = None, longitude: Optional[float] = None) -> SolarPosition:
    """
    Create SolarPosition instance with context and optional coordinates.
    
    Args:
        context: Helios Context
        utc_offset: UTC time offset in hours (optional)
        latitude: Latitude in degrees (optional)  
        longitude: Longitude in degrees (optional)
        
    Returns:
        SolarPosition instance
        
    Example:
        >>> solar = create_solar_position(context, utc_offset=-8, latitude=38.5, longitude=-121.7)
    """
    return SolarPosition(context, utc_offset, latitude, longitude)