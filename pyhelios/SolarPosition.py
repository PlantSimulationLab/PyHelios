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
            humidity_rel: Relative humidity as fraction (0.0-1.0)
            turbidity: Atmospheric turbidity coefficient (typically 0.02-0.5)

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

        try:
            solar_wrapper.setAtmosphericConditions(self._solar_pos, pressure_Pa, temperature_K, humidity_rel, turbidity)
        except Exception as e:
            raise SolarPositionError(f"Failed to set atmospheric conditions: {e}")

    def getAtmosphericConditions(self) -> Tuple[float, float, float, float]:
        """
        Get currently set atmospheric conditions from Context.

        Returns:
            Tuple of (pressure_Pa, temperature_K, humidity_rel, turbidity)

        Raises:
            SolarPositionError: If operation fails

        Note:
            If atmospheric conditions have not been set via setAtmosphericConditions(),
            returns default values: (101325 Pa, 300 K, 0.5, 0.02)

        Example:
            >>> pressure, temp, humidity, turbidity = solar.getAtmosphericConditions()
            >>> print(f"Pressure: {pressure} Pa, Temp: {temp} K")
        """
        try:
            return solar_wrapper.getAtmosphericConditions(self._solar_pos)
        except Exception as e:
            raise SolarPositionError(f"Failed to get atmospheric conditions: {e}")

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
            turbidity: Atmospheric turbidity coefficient (typically 0.02-0.5) [optional]

        Returns:
            Total solar flux in W/m²

        Raises:
            ValueError: If some parameters provided but not all, or if values are invalid
            SolarPositionError: If calculation fails or atmospheric conditions not set (modern API)

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
            try:
                return solar_wrapper.getSolarFlux(self._solar_pos, pressure_Pa, temperature_K, humidity_rel, turbidity)
            except Exception as e:
                raise SolarPositionError(f"Failed to calculate solar flux: {e}")

        elif not any(params_provided):
            # Modern API: No parameters, use atmospheric conditions from Context
            try:
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
            turbidity: Atmospheric turbidity coefficient [optional]

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
            try:
                return solar_wrapper.getSolarFluxPAR(self._solar_pos, pressure_Pa, temperature_K, humidity_rel, turbidity)
            except Exception as e:
                raise SolarPositionError(f"Failed to calculate PAR flux: {e}")
        elif not any(params_provided):
            try:
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
            turbidity: Atmospheric turbidity coefficient [optional]

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
            try:
                return solar_wrapper.getSolarFluxNIR(self._solar_pos, pressure_Pa, temperature_K, humidity_rel, turbidity)
            except Exception as e:
                raise SolarPositionError(f"Failed to calculate NIR flux: {e}")
        elif not any(params_provided):
            try:
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
            turbidity: Atmospheric turbidity coefficient [optional]

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
            try:
                return solar_wrapper.getDiffuseFraction(self._solar_pos, pressure_Pa, temperature_K, humidity_rel, turbidity)
            except Exception as e:
                raise SolarPositionError(f"Failed to calculate diffuse fraction: {e}")
        elif not any(params_provided):
            try:
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
            Returns downwelling longwave radiation flux on a horizontal surface.

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
        try:
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
            Reads turbidity from Context atmospheric conditions. Stores results in Context
            global data as "prague_sky_spectral_params" (1350 floats: 225 wavelengths × 6 params),
            "prague_sky_sun_direction", "prague_sky_visibility_km", "prague_sky_ground_albedo",
            and "prague_sky_valid" flag.

        Example:
            >>> solar.setAtmosphericConditions(101325, 288.15, 0.6, 0.1)
            >>> solar.updatePragueSkyModel(ground_albedo=0.25)
        """
        try:
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
        try:
            return solar_wrapper.pragueSkyModelNeedsUpdate(self._solar_pos, ground_albedo,
                                                           sun_tolerance, turbidity_tolerance,
                                                           albedo_tolerance)
        except Exception as e:
            raise SolarPositionError(f"Failed to check Prague Sky Model update status: {e}")

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