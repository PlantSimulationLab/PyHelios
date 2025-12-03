"""
SolarPosition - High-level interface for solar position and radiation calculations

This module provides a Python interface to the SolarPosition Helios plugin,
offering comprehensive solar angle calculations, radiation modeling, and
time-dependent solar functions for atmospheric physics and plant modeling.
"""

from typing import List, Tuple, Optional, Union
from .wrappers import USolarPositionWrapper as solar_wrapper
from .Context import Context
from .plugins.registry import get_plugin_registry
from .exceptions import HeliosError
from .wrappers.DataTypes import Time, Date, vec3, SphericalCoord


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
            utc_offset: UTC time offset in hours (-12 to +12). If provided with 
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
            if utc_offset < -12.0 or utc_offset > 12.0:
                raise ValueError(f"UTC offset must be between -12 and +12 hours, got: {utc_offset}")
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

    # Solar angle calculations
    def getSunElevation(self) -> float:
        """
        Get the sun elevation angle in degrees.
        
        Returns:
            Sun elevation angle in degrees (0° = horizon, 90° = zenith)
            
        Raises:
            SolarPositionError: If calculation fails
            
        Example:
            >>> elevation = solar.getSunElevation()
            >>> print(f"Sun is {elevation:.1f}° above horizon")
        """
        try:
            return solar_wrapper.getSunElevation(self._solar_pos)
        except Exception as e:
            raise SolarPositionError(f"Failed to get sun elevation: {e}")
    
    def getSunZenith(self) -> float:
        """
        Get the sun zenith angle in degrees.
        
        Returns:
            Sun zenith angle in degrees (0° = zenith, 90° = horizon)
            
        Raises:
            SolarPositionError: If calculation fails
            
        Example:
            >>> zenith = solar.getSunZenith()
            >>> print(f"Sun zenith angle: {zenith:.1f}°")
        """
        try:
            return solar_wrapper.getSunZenith(self._solar_pos)
        except Exception as e:
            raise SolarPositionError(f"Failed to get sun zenith: {e}")
    
    def getSunAzimuth(self) -> float:
        """
        Get the sun azimuth angle in degrees.
        
        Returns:
            Sun azimuth angle in degrees (0° = North, 90° = East, 180° = South, 270° = West)
            
        Raises:
            SolarPositionError: If calculation fails
            
        Example:
            >>> azimuth = solar.getSunAzimuth()
            >>> print(f"Sun azimuth: {azimuth:.1f}° (compass bearing)")
        """
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
        try:
            spherical_list = solar_wrapper.getSunDirectionSpherical(self._solar_pos)
            return SphericalCoord(
                radius=spherical_list[0],
                elevation=spherical_list[1], 
                azimuth=spherical_list[2]
            )
        except Exception as e:
            raise SolarPositionError(f"Failed to get sun direction spherical: {e}")
    
    # Solar flux calculations
    def getSolarFlux(self, pressure_Pa: float, temperature_K: float, 
                     humidity_rel: float, turbidity: float) -> float:
        """
        Calculate total solar flux with atmospheric parameters.
        
        Args:
            pressure_Pa: Atmospheric pressure in Pascals (e.g., 101325 for sea level)
            temperature_K: Temperature in Kelvin (e.g., 288.15 for 15°C)
            humidity_rel: Relative humidity as fraction (0.0-1.0)
            turbidity: Atmospheric turbidity coefficient (typically 0.05-0.5)
            
        Returns:
            Total solar flux in W/m²
            
        Raises:
            ValueError: If atmospheric parameters are out of valid ranges
            SolarPositionError: If calculation fails
            
        Example:
            >>> # Standard atmospheric conditions
            >>> flux = solar.getSolarFlux(101325, 288.15, 0.6, 0.1)
            >>> print(f"Total solar flux: {flux:.1f} W/m²")
        """
        try:
            return solar_wrapper.getSolarFlux(self._solar_pos, pressure_Pa, temperature_K, humidity_rel, turbidity)
        except Exception as e:
            raise SolarPositionError(f"Failed to calculate solar flux: {e}")
    
    def getSolarFluxPAR(self, pressure_Pa: float, temperature_K: float,
                        humidity_rel: float, turbidity: float) -> float:
        """
        Calculate PAR (Photosynthetically Active Radiation) solar flux.
        
        Args:
            pressure_Pa: Atmospheric pressure in Pascals
            temperature_K: Temperature in Kelvin
            humidity_rel: Relative humidity as fraction (0.0-1.0)
            turbidity: Atmospheric turbidity coefficient
            
        Returns:
            PAR solar flux in W/m² (wavelength range ~400-700 nm)
            
        Raises:
            ValueError: If atmospheric parameters are invalid
            SolarPositionError: If calculation fails
            
        Example:
            >>> par_flux = solar.getSolarFluxPAR(101325, 288.15, 0.6, 0.1)
            >>> print(f"PAR flux: {par_flux:.1f} W/m²")
        """
        try:
            return solar_wrapper.getSolarFluxPAR(self._solar_pos, pressure_Pa, temperature_K, humidity_rel, turbidity)
        except Exception as e:
            raise SolarPositionError(f"Failed to calculate PAR flux: {e}")
    
    def getSolarFluxNIR(self, pressure_Pa: float, temperature_K: float,
                        humidity_rel: float, turbidity: float) -> float:
        """
        Calculate NIR (Near-Infrared) solar flux.
        
        Args:
            pressure_Pa: Atmospheric pressure in Pascals
            temperature_K: Temperature in Kelvin  
            humidity_rel: Relative humidity as fraction (0.0-1.0)
            turbidity: Atmospheric turbidity coefficient
            
        Returns:
            NIR solar flux in W/m² (wavelength range >700 nm)
            
        Raises:
            ValueError: If atmospheric parameters are invalid
            SolarPositionError: If calculation fails
            
        Example:
            >>> nir_flux = solar.getSolarFluxNIR(101325, 288.15, 0.6, 0.1)
            >>> print(f"NIR flux: {nir_flux:.1f} W/m²")
        """
        try:
            return solar_wrapper.getSolarFluxNIR(self._solar_pos, pressure_Pa, temperature_K, humidity_rel, turbidity)
        except Exception as e:
            raise SolarPositionError(f"Failed to calculate NIR flux: {e}")
    
    def getDiffuseFraction(self, pressure_Pa: float, temperature_K: float,
                           humidity_rel: float, turbidity: float) -> float:
        """
        Calculate the diffuse fraction of solar radiation.
        
        Args:
            pressure_Pa: Atmospheric pressure in Pascals
            temperature_K: Temperature in Kelvin
            humidity_rel: Relative humidity as fraction (0.0-1.0)
            turbidity: Atmospheric turbidity coefficient
            
        Returns:
            Diffuse fraction as ratio (0.0-1.0) where:
            - 0.0 = all direct radiation
            - 1.0 = all diffuse radiation
            
        Raises:
            ValueError: If atmospheric parameters are invalid
            SolarPositionError: If calculation fails
            
        Example:
            >>> diffuse_fraction = solar.getDiffuseFraction(101325, 288.15, 0.6, 0.1)
            >>> print(f"Diffuse fraction: {diffuse_fraction:.3f} ({diffuse_fraction*100:.1f}%)")
        """
        try:
            return solar_wrapper.getDiffuseFraction(self._solar_pos, pressure_Pa, temperature_K, humidity_rel, turbidity)
        except Exception as e:
            raise SolarPositionError(f"Failed to calculate diffuse fraction: {e}")
    
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
        try:
            hour, minute, second = solar_wrapper.getSunsetTime(self._solar_pos)
            return Time(hour, minute, second)
        except Exception as e:
            raise SolarPositionError(f"Failed to calculate sunset time: {e}")
    
    # Calibration functions
    def calibrateTurbidityFromTimeseries(self, timeseries_label: str):
        """
        Calibrate atmospheric turbidity using timeseries data.
        
        Args:
            timeseries_label: Label of timeseries data in Context
            
        Raises:
            ValueError: If timeseries label is invalid
            SolarPositionError: If calibration fails
            
        Example:
            >>> solar.calibrateTurbidityFromTimeseries("solar_irradiance")
        """
        if not timeseries_label:
            raise ValueError("Timeseries label cannot be empty")
        
        try:
            solar_wrapper.calibrateTurbidityFromTimeseries(self._solar_pos, timeseries_label)
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
        try:
            solar_wrapper.disableCloudCalibration(self._solar_pos)
        except Exception as e:
            raise SolarPositionError(f"Failed to disable cloud calibration: {e}")

    # SSolar-GOA Spectral Solar Model Methods
    def calculateDirectSolarSpectrum(self, label: str, resolution_nm: float = 1.0):
        """
        Calculate direct beam solar spectrum using SSolar-GOA model.

        Computes the spectral irradiance of direct beam solar radiation across
        300-2600 nm wavelength range using the SSolar-GOA (Global Ozone and
        Atmospheric) spectral model. Results are stored in Context global data
        as a vector of (wavelength, irradiance) pairs.

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
            - Atmospheric parameters from Context location are used
            - Results accessible via context.getGlobalData(label)
            - SSolar-GOA model accounts for atmospheric absorption and scattering

        Example:
            >>> with Context() as context:
            ...     context.setDate(2023, 6, 21)
            ...     context.setTime(12, 0)
            ...     with SolarPosition(context) as solar:
            ...         solar.calculateDirectSolarSpectrum("direct_spectrum", resolution_nm=5.0)
            ...         spectrum = context.getGlobalData("direct_spectrum")
            ...         # spectrum is list of vec2(wavelength_nm, irradiance_W_m2_nm)
        """
        if not label:
            raise ValueError("Label cannot be empty")
        if resolution_nm < 1.0 or resolution_nm > 2300.0:
            raise ValueError(f"Wavelength resolution must be between 1 and 2300 nm, got: {resolution_nm}")

        try:
            solar_wrapper.calculateDirectSolarSpectrum(self._solar_pos, label, resolution_nm)
        except Exception as e:
            raise SolarPositionError(f"Failed to calculate direct solar spectrum: {e}")

    def calculateDiffuseSolarSpectrum(self, label: str, resolution_nm: float = 1.0):
        """
        Calculate diffuse solar spectrum using SSolar-GOA model.

        Computes the spectral irradiance of diffuse (scattered) solar radiation
        across 300-2600 nm wavelength range using the SSolar-GOA model. Results
        are stored in Context global data as a vector of (wavelength, irradiance) pairs.

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
            - Atmospheric parameters from Context location are used
            - Results accessible via context.getGlobalData(label)
            - Diffuse radiation results from atmospheric scattering (Rayleigh, aerosol)

        Example:
            >>> with Context() as context:
            ...     context.setDate(2023, 6, 21)
            ...     context.setTime(12, 0)
            ...     with SolarPosition(context) as solar:
            ...         solar.calculateDiffuseSolarSpectrum("diffuse_spectrum", resolution_nm=5.0)
            ...         spectrum = context.getGlobalData("diffuse_spectrum")
            ...         # spectrum is list of vec2(wavelength_nm, irradiance_W_m2_nm)
        """
        if not label:
            raise ValueError("Label cannot be empty")
        if resolution_nm < 1.0 or resolution_nm > 2300.0:
            raise ValueError(f"Wavelength resolution must be between 1 and 2300 nm, got: {resolution_nm}")

        try:
            solar_wrapper.calculateDiffuseSolarSpectrum(self._solar_pos, label, resolution_nm)
        except Exception as e:
            raise SolarPositionError(f"Failed to calculate diffuse solar spectrum: {e}")

    def calculateGlobalSolarSpectrum(self, label: str, resolution_nm: float = 1.0):
        """
        Calculate global (total) solar spectrum using SSolar-GOA model.

        Computes the spectral irradiance of total solar radiation (direct + diffuse)
        across 300-2600 nm wavelength range using the SSolar-GOA model. Results
        are stored in Context global data as a vector of (wavelength, irradiance) pairs.

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
            - Atmospheric parameters from Context location are used
            - Results accessible via context.getGlobalData(label)
            - Global spectrum = direct beam + diffuse (sky) radiation
            - Most useful for plant canopy modeling and photosynthesis calculations

        Example:
            >>> with Context() as context:
            ...     context.setDate(2023, 6, 21)
            ...     context.setTime(12, 0)
            ...     with SolarPosition(context) as solar:
            ...         solar.calculateGlobalSolarSpectrum("global_spectrum", resolution_nm=10.0)
            ...         spectrum = context.getGlobalData("global_spectrum")
            ...         # spectrum is list of vec2(wavelength_nm, irradiance_W_m2_nm)
            ...         total_irradiance = sum([s.y for s in spectrum]) * 10.0  # Integrate
        """
        if not label:
            raise ValueError("Label cannot be empty")
        if resolution_nm < 1.0 or resolution_nm > 2300.0:
            raise ValueError(f"Wavelength resolution must be between 1 and 2300 nm, got: {resolution_nm}")

        try:
            solar_wrapper.calculateGlobalSolarSpectrum(self._solar_pos, label, resolution_nm)
        except Exception as e:
            raise SolarPositionError(f"Failed to calculate global solar spectrum: {e}")

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