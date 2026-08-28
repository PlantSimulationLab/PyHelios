"""
Tests for SolarPosition plugin integration

This test file covers both cross-platform testing (with mock mode) and
native library testing following PyHelios testing standards.
"""

import pytest
import math
from pyhelios import Context, SolarPosition, SolarPositionError
from pyhelios.plugins.registry import get_plugin_registry
# Import HeliosError from pyhelios main module to ensure consistency
from pyhelios import HeliosError
from pyhelios.wrappers.DataTypes import Time, Date, vec3, SphericalCoord


class TestSolarPositionMetadata:
    """Test plugin metadata and registration"""
    
    @pytest.mark.cross_platform
    def test_plugin_metadata_exists(self):
        """Test that plugin metadata is correctly defined"""
        from pyhelios.config.plugin_metadata import get_plugin_metadata
        
        metadata = get_plugin_metadata('solarposition')
        assert metadata is not None
        assert metadata.name == 'solarposition'
        assert metadata.description
        assert metadata.test_symbols
        assert isinstance(metadata.platforms, list)
        assert len(metadata.platforms) > 0
        assert metadata.gpu_required == False
        assert metadata.optional == True  # Optional plugin - depends on build configuration
    
    @pytest.mark.cross_platform
    def test_plugin_registry_includes_solarposition(self):
        """Test that plugin is included in registry"""
        from pyhelios.config.plugin_metadata import PLUGIN_METADATA
        
        # Should be in plugin metadata
        assert 'solarposition' in PLUGIN_METADATA
        
        # Verify metadata structure
        sp_metadata = PLUGIN_METADATA['solarposition']
        assert sp_metadata.name == 'solarposition'
        assert 'solar position' in sp_metadata.description.lower()
        assert 'windows' in sp_metadata.platforms
        assert 'linux' in sp_metadata.platforms
        assert 'macos' in sp_metadata.platforms


class TestSolarPositionAvailability:
    """Test plugin availability detection"""
    
    @pytest.mark.cross_platform
    def test_plugin_registry_awareness(self):
        """Test that plugin registry handles SolarPosition correctly"""
        registry = get_plugin_registry()
        
        # In mock mode or without native libraries, plugin won't be available
        # but should be handled gracefully
        available_plugins = registry.get_available_plugins()
        
        # Test that we can check plugin availability without crashing
        is_available = registry.is_plugin_available('solarposition')
        assert isinstance(is_available, bool)
        
        # solarposition availability depends on build configuration
        # Only assert it's available if it's actually in the available plugins
        if is_available:
            assert 'solarposition' in available_plugins
        else:
            assert 'solarposition' not in available_plugins
    
    @pytest.mark.cross_platform 
    def test_graceful_unavailable_handling(self):
        """Test graceful handling when plugin unavailable in mock mode"""
        registry = get_plugin_registry()
        
        with Context() as context:
            if not registry.is_plugin_available('solarposition'):
                # Should raise informative error with rebuild instructions
                with pytest.raises(SolarPositionError) as exc_info:
                    SolarPosition(context)
                
                error_msg = str(exc_info.value).lower()
                # Error should mention SolarPosition availability  
                assert 'solarposition' in error_msg or 'solar position' in error_msg
                # Should mention plugin availability
                assert 'not available' in error_msg


class TestSolarPositionInterface:
    """Test plugin interface without requiring native library"""
    
    @pytest.mark.cross_platform
    def test_solarposition_class_structure(self):
        """Test that SolarPosition class has expected structure"""
        # Test class attributes and methods exist
        assert hasattr(SolarPosition, '__init__')
        assert hasattr(SolarPosition, '__enter__')
        assert hasattr(SolarPosition, '__exit__')
        
        # Solar angle methods
        assert hasattr(SolarPosition, 'getSunElevation')
        assert hasattr(SolarPosition, 'getSunZenith')
        assert hasattr(SolarPosition, 'getSunAzimuth')
        
        # Direction methods
        assert hasattr(SolarPosition, 'getSunDirectionVector')
        assert hasattr(SolarPosition, 'getSunDirectionSpherical')
        
        # Solar flux methods
        assert hasattr(SolarPosition, 'getSolarFlux')
        assert hasattr(SolarPosition, 'getSolarFluxPAR')
        assert hasattr(SolarPosition, 'getSolarFluxNIR')
        assert hasattr(SolarPosition, 'getDiffuseFraction')
        
        # Time methods
        assert hasattr(SolarPosition, 'getSunriseTime')
        assert hasattr(SolarPosition, 'getSunsetTime')
        
        # Calibration methods
        assert hasattr(SolarPosition, 'calibrateTurbidityFromTimeseries')
        assert hasattr(SolarPosition, 'enableCloudCalibration')
        assert hasattr(SolarPosition, 'disableCloudCalibration')
        
        # Utility methods
# Note: calculateSunElevationAngle and calculateBeamRadiation not available in base SolarPosition plugin
        assert hasattr(SolarPosition, 'is_available')
    
    @pytest.mark.cross_platform
    def test_error_types_available(self):
        """Test that error types are properly defined"""
        assert issubclass(SolarPositionError, HeliosError)
    
    @pytest.mark.cross_platform
    def test_constructor_parameter_validation(self):
        """Test constructor parameter validation"""
        from pyhelios.plugins.registry import get_plugin_registry
        registry = get_plugin_registry()
        
        with Context() as context:
            if registry.is_plugin_available('solarposition'):
                # Plugin is available - constructor should succeed
                try:
                    with SolarPosition(context, utc_offset=-8, latitude=38.5, longitude=-121.7):
                        pass  # Plugin available, constructor should succeed
                except Exception as e:
                    pytest.fail(f"Constructor should succeed with valid parameters when plugin is available: {e}")
            else:
                # Plugin not available - should get proper error
                with pytest.raises(SolarPositionError) as exc_info:
                    SolarPosition(context, utc_offset=-8, latitude=38.5, longitude=-121.7)
                assert "not available" in str(exc_info.value)


@pytest.mark.native_only
class TestSolarPositionFunctionality:
    """Test actual plugin functionality with native library"""
    
    def test_plugin_creation_destruction(self):
        """Test plugin can be created and destroyed"""
        with Context() as context:
            # Test creation with Context location
            with SolarPosition(context) as solar:
                assert solar is not None
                assert isinstance(solar, SolarPosition)
    
    def test_plugin_creation_with_coordinates(self):
        """Test plugin creation with explicit coordinates"""
        with Context() as context:
            # Test creation with Davis, California coordinates
            with SolarPosition(context, utc_offset=-8, latitude=38.5, longitude=-121.7) as solar:
                assert solar is not None
                assert isinstance(solar, SolarPosition)
    
    def test_coordinate_parameter_validation(self):
        """Test coordinate parameter validation"""
        with Context() as context:
            # Test invalid UTC offset
            with pytest.raises(ValueError, match="UTC offset must be between"):
                SolarPosition(context, utc_offset=15, latitude=38.5, longitude=-121.7)
            
            # Test invalid latitude
            with pytest.raises(ValueError, match="Latitude must be between"):
                SolarPosition(context, utc_offset=-8, latitude=95, longitude=-121.7)
            
            # Test invalid longitude
            with pytest.raises(ValueError, match="Longitude must be between"):
                SolarPosition(context, utc_offset=-8, latitude=38.5, longitude=200)

    def test_utc_offset_accepts_minus_14(self):
        """UTC offset range is -14..+12, matching helios::Location::validate().

        Helios counts the offset positive moving West, so real-world UTC+13/UTC+14
        (Kiribati) map to -13/-14. A symmetric -12..+12 bound wrongly rejects them.
        """
        with Context() as context:
            for utc_offset in (-13.0, -14.0):
                with SolarPosition(context, utc_offset=utc_offset,
                                   latitude=38.5, longitude=-121.7) as solar:
                    assert solar is not None

    def test_utc_offset_rejects_beyond_asymmetric_bounds(self):
        """+13 is out of range even though -13 is in range."""
        with Context() as context:
            with pytest.raises(ValueError, match="UTC offset must be between"):
                SolarPosition(context, utc_offset=13.0, latitude=38.5, longitude=-121.7)
            with pytest.raises(ValueError, match="UTC offset must be between"):
                SolarPosition(context, utc_offset=-15.0, latitude=38.5, longitude=-121.7)
    
    def test_solar_angle_calculations(self):
        """Test solar angle calculation methods"""
        with Context() as context:
            # Set known date and time for predictable results
            context.setDate(2023, 6, 21)  # Summer solstice
            context.setTime(12, 0)        # Solar noon
            
            with SolarPosition(context, utc_offset=0, latitude=0, longitude=0) as solar:
                # Test basic angle calculations
                elevation = solar.getSunElevation()
                zenith = solar.getSunZenith()
                azimuth = solar.getSunAzimuth()
                
                # Basic sanity checks
                assert isinstance(elevation, float)
                assert isinstance(zenith, float)
                assert isinstance(azimuth, float)
                
                # Zenith and elevation may not be exactly complementary due to different conventions
                # Just check they're reasonable values
                assert -90 <= elevation <= 90
                assert 0 <= zenith <= 180
                
                # Sun should be above horizon during midday in summer
                assert elevation > 0  # Should be positive during day
                assert 0 <= azimuth <= 360
    
    def test_sun_direction_vectors(self):
        """Test sun direction vector calculations"""
        with Context() as context:
            context.setDate(2023, 6, 21)
            context.setTime(12, 0)
            
            with SolarPosition(context, utc_offset=0, latitude=0, longitude=0) as solar:
                # Test 3D vector
                direction = solar.getSunDirectionVector()
                assert isinstance(direction, vec3)
                
                # Should be unit vector (approximately)
                magnitude = math.sqrt(direction.x**2 + direction.y**2 + direction.z**2)
                assert abs(magnitude - 1.0) < 0.001
                
                # Test spherical coordinates
                spherical = solar.getSunDirectionSpherical()
                assert isinstance(spherical, SphericalCoord)
                assert spherical.radius == pytest.approx(1.0, abs=0.001)
    
    def test_solar_flux_calculations(self):
        """Test solar flux calculation methods"""
        with Context() as context:
            context.setDate(2023, 6, 21)  # Summer solstice
            context.setTime(12, 0)        # Solar noon
            
            with SolarPosition(context, utc_offset=0, latitude=0, longitude=0) as solar:
                # Standard atmospheric conditions
                pressure = 101325.0  # Pa (sea level)
                temperature = 288.15  # K (15°C)
                humidity = 0.6       # 60% relative humidity
                turbidity = 0.1      # Clear sky
                
                # Test total solar flux
                total_flux = solar.getSolarFlux(pressure, temperature, humidity, turbidity)
                assert isinstance(total_flux, float)
                assert total_flux > 0  # Should have positive flux at noon
                assert total_flux < 2000  # Reasonable upper bound
                
                # Test PAR flux
                par_flux = solar.getSolarFluxPAR(pressure, temperature, humidity, turbidity)
                assert isinstance(par_flux, float)
                assert par_flux > 0
                assert par_flux < total_flux  # PAR should be subset of total
                
                # Test NIR flux
                nir_flux = solar.getSolarFluxNIR(pressure, temperature, humidity, turbidity)
                assert isinstance(nir_flux, float)
                assert nir_flux > 0
                assert nir_flux < total_flux  # NIR should be subset of total
                
                # Test diffuse fraction
                diffuse = solar.getDiffuseFraction(pressure, temperature, humidity, turbidity)
                assert isinstance(diffuse, float)
                assert 0.0 <= diffuse <= 1.0  # Should be a fraction
    
    def test_atmospheric_parameter_validation(self):
        """Test atmospheric parameter validation in flux calculations"""
        with Context() as context:
            context.setDate(2023, 6, 21)
            context.setTime(12, 0)
            
            with SolarPosition(context, utc_offset=0, latitude=0, longitude=0) as solar:
                # Test invalid atmospheric parameters - C++ handles validation
                with pytest.raises(SolarPositionError, match="Failed to calculate solar flux"):
                    solar.getSolarFlux(-1000, 288.15, 0.6, 0.1)
                
                with pytest.raises(SolarPositionError, match="Failed to calculate solar flux"):
                    solar.getSolarFlux(101325, -100, 0.6, 0.1)
                
                with pytest.raises(SolarPositionError, match="Failed to calculate solar flux"):
                    solar.getSolarFlux(101325, 288.15, 1.5, 0.1)
                
                with pytest.raises(SolarPositionError, match="Failed to calculate solar flux"):
                    solar.getSolarFlux(101325, 288.15, 0.6, -0.1)
    
    def test_sunrise_sunset_calculations(self):
        """Test sunrise and sunset time calculations"""
        with Context() as context:
            context.setDate(2023, 6, 21)  # Summer solstice
            
            # Use mid-latitude location for reasonable sunrise/sunset
            with SolarPosition(context, utc_offset=-8, latitude=38.5, longitude=-121.7) as solar:
                sunrise = solar.getSunriseTime()
                sunset = solar.getSunsetTime()
                
                assert isinstance(sunrise, Time)
                assert isinstance(sunset, Time)
                
                # Basic sanity checks
                assert 0 <= sunrise.hour <= 23
                assert 0 <= sunset.hour <= 23
                assert 0 <= sunrise.minute <= 59
                assert 0 <= sunset.minute <= 59
                
                # Sunset should be after sunrise
                sunrise_minutes = sunrise.hour * 60 + sunrise.minute
                sunset_minutes = sunset.hour * 60 + sunset.minute
                assert sunset_minutes > sunrise_minutes
                
                # On summer solstice, day should be quite long at mid-latitudes
                day_length_hours = (sunset_minutes - sunrise_minutes) / 60.0
                assert day_length_hours > 12  # Longer than 12 hours
    
    def test_calibration_functions(self):
        """Test turbidity and cloud calibration functions"""
        with Context() as context:
            with SolarPosition(context) as solar:
                # Test calibration methods don't crash
                # Note: These may raise errors if timeseries don't exist, which is expected
                try:
                    solar.calibrateTurbidityFromTimeseries("test_series")
                except (SolarPositionError, HeliosError):
                    pass  # Expected if no timeseries data
                
                try:
                    solar.enableCloudCalibration("cloud_series")
                except (SolarPositionError, HeliosError):
                    pass  # Expected if no cloud data
                
                # Disable should work
                solar.disableCloudCalibration()
    
    def test_utility_functions(self):
        """Test basic solar position functionality (replaces non-existent utility methods)"""
        with Context() as context:
            context.setDate(2023, 6, 21)  # Summer solstice
            context.setTime(12, 0)  # Solar noon
            
            with SolarPosition(context, utc_offset=-8, latitude=38.5, longitude=-121.7) as solar:
                # Test that basic solar calculations work 
                elevation = solar.getSunElevation()
                assert isinstance(elevation, float)
                assert -90 <= elevation <= 90  # Valid elevation range
                
                # Test flux calculation with standard atmosphere
                flux = solar.getSolarFlux(101325, 288.15, 0.6, 0.1)
                assert isinstance(flux, float)
                assert flux > 0  # Should be positive during day
    
    def test_date_time_parameter_validation(self):
        """Test date/time parameter validation in context methods"""
        with Context() as context:
            # Test invalid date/time parameters through context - these should work
            # since Context validates parameters
            
            # Valid parameters should not raise
            context.setDate(2023, 6, 21)  
            context.setTime(12, 30, 45)
            
            with SolarPosition(context) as solar:
                # Basic functionality test
                elevation = solar.getSunElevation()
                assert isinstance(elevation, float)


@pytest.mark.native_only
class TestSolarPositionIntegration:
    """Test plugin integration with other PyHelios components"""
    
    def test_context_time_date_integration(self):
        """Test plugin works with Context time/date functionality"""
        with Context() as context:
            # Test Context time/date methods work with SolarPosition
            context.setDate(2023, 6, 21)
            context.setTime(12, 0, 0)
            
            # Verify Context methods work
            year, month, day = context.getDate()
            hour, minute, second = context.getTime()
            
            assert year == 2023
            assert month == 6
            assert day == 21
            assert hour == 12
            assert minute == 0
            assert second == 0
            
            # Test SolarPosition uses Context time/date
            with SolarPosition(context, utc_offset=0, latitude=0, longitude=0) as solar:
                # Should calculate based on Context time/date
                elevation = solar.getSunElevation()
                assert isinstance(elevation, float)
    
    def test_context_date_time_validation(self):
        """Test Context time/date parameter validation"""
        with Context() as context:
            # Test invalid time parameters
            with pytest.raises((ValueError, HeliosError), match=r"(Hour|hour)"):
                context.setTime(25, 0)
            
            with pytest.raises((ValueError, HeliosError), match=r"(Minute|minute)"):
                context.setTime(12, 65)
            
            with pytest.raises((ValueError, HeliosError), match=r"(Second|second)"):
                context.setTime(12, 30, 65)
            
            # Test invalid date parameters
            with pytest.raises((ValueError, HeliosError), match=r"(Day|day)"):
                context.setDate(2023, 6, 35)
            
            with pytest.raises((ValueError, HeliosError), match=r"(Month|month)"):
                context.setDate(2023, 15, 21)
    
    def test_multiple_plugin_instances(self):
        """Test multiple SolarPosition instances"""
        with Context() as context:
            context.setDate(2023, 6, 21)
            context.setTime(12, 0)
            
            # Create multiple instances with different coordinates
            with SolarPosition(context, utc_offset=0, latitude=0, longitude=0) as solar1:
                with SolarPosition(context, utc_offset=-8, latitude=38.5, longitude=-121.7) as solar2:
                    # Both should work independently
                    elev1 = solar1.getSunElevation()
                    elev2 = solar2.getSunElevation()
                    
                    assert isinstance(elev1, float)
                    assert isinstance(elev2, float)
                    
                    # Different locations should give different results
                    # (though this depends on the exact implementation)
    
    def test_error_handling_integration(self):
        """Test that C++ exceptions become proper Python exceptions"""
        with Context() as context:
            with SolarPosition(context) as solar:
                # Test operations that should cause specific errors
                try:
                    # Invalid timeseries should raise SolarPositionError
                    solar.calibrateTurbidityFromTimeseries("")
                    assert False, "Should have raised an exception for empty string"
                except (ValueError, SolarPositionError):
                    # Either type is acceptable for parameter validation
                    pass


@pytest.mark.slow
class TestSolarPositionPerformance:
    """Performance tests for plugin operations"""
    
    @pytest.mark.native_only
    def test_solar_calculation_performance(self):
        """Test solar calculations don't have performance regressions"""
        import time
        
        with Context() as context:
            context.setDate(2023, 6, 21)
            context.setTime(12, 0)
            
            with SolarPosition(context, utc_offset=0, latitude=0, longitude=0) as solar:
                # Time multiple calculations
                start_time = time.time()
                
                for _ in range(100):  # 100 calculations
                    elevation = solar.getSunElevation()
                    azimuth = solar.getSunAzimuth()
                    flux = solar.getSolarFlux(101325, 288.15, 0.6, 0.1)
                
                elapsed = time.time() - start_time
                
                # Should complete 100 calculations in reasonable time
                assert elapsed < 1.0, f"Solar calculations too slow: {elapsed:.3f}s for 100 calculations"
    
    @pytest.mark.native_only
    def test_plugin_creation_performance(self):
        """Test plugin creation/destruction performance"""
        import time
        
        with Context() as context:
            start_time = time.time()
            
            # Create and destroy multiple instances
            for _ in range(10):
                with SolarPosition(context) as solar:
                    _ = solar.getSunElevation()  # Do one calculation
            
            elapsed = time.time() - start_time

            # Should be able to create/destroy instances quickly
            assert elapsed < 1.0, f"Plugin creation too slow: {elapsed:.3f}s for 10 instances"


@pytest.mark.native_only
class TestSolarPositionModernAPI:
    """Test modern stateful API with setAtmosphericConditions"""

    def test_set_and_get_atmospheric_conditions(self):
        """Test setAtmosphericConditions and getAtmosphericConditions"""
        with Context() as context:
            with SolarPosition(context) as solar:
                # Set known conditions
                pressure = 101325.0
                temperature = 288.15
                humidity = 0.6
                turbidity = 0.1

                solar.setAtmosphericConditions(pressure, temperature, humidity, turbidity)

                # Retrieve and verify
                p, t, h, turb = solar.getAtmosphericConditions()

                assert p == pytest.approx(pressure, abs=0.1)
                assert t == pytest.approx(temperature, abs=0.1)
                assert h == pytest.approx(humidity, abs=0.001)
                assert turb == pytest.approx(turbidity, abs=0.001)

    def test_parameter_free_flux_methods(self):
        """Test parameter-free flux methods (modern API)"""
        with Context() as context:
            context.setDate(2023, 6, 21)  # Summer solstice
            context.setTime(12, 0)  # Solar noon

            with SolarPosition(context, utc_offset=0, latitude=0, longitude=0) as solar:
                # Set atmospheric conditions once
                solar.setAtmosphericConditions(101325, 288.15, 0.6, 0.1)

                # Call parameter-free flux methods
                total_flux = solar.getSolarFlux()
                par_flux = solar.getSolarFluxPAR()
                nir_flux = solar.getSolarFluxNIR()
                diffuse = solar.getDiffuseFraction()

                # All should return valid values
                assert isinstance(total_flux, float)
                assert total_flux > 0
                assert total_flux < 2000

                assert isinstance(par_flux, float)
                assert par_flux > 0
                assert par_flux < total_flux

                assert isinstance(nir_flux, float)
                assert nir_flux > 0
                assert nir_flux < total_flux

                assert isinstance(diffuse, float)
                assert 0.0 <= diffuse <= 1.0

    def test_legacy_and_modern_api_equivalence(self):
        """Test that legacy and modern APIs produce identical results"""
        with Context() as context:
            context.setDate(2023, 6, 21)
            context.setTime(12, 0)

            with SolarPosition(context, utc_offset=0, latitude=0, longitude=0) as solar:
                # Test conditions
                pressure = 101325.0
                temperature = 288.15
                humidity = 0.6
                turbidity = 0.1

                # Legacy API
                legacy_flux = solar.getSolarFlux(pressure, temperature, humidity, turbidity)
                legacy_par = solar.getSolarFluxPAR(pressure, temperature, humidity, turbidity)
                legacy_nir = solar.getSolarFluxNIR(pressure, temperature, humidity, turbidity)
                legacy_diffuse = solar.getDiffuseFraction(pressure, temperature, humidity, turbidity)

                # Modern API
                solar.setAtmosphericConditions(pressure, temperature, humidity, turbidity)
                modern_flux = solar.getSolarFlux()
                modern_par = solar.getSolarFluxPAR()
                modern_nir = solar.getSolarFluxNIR()
                modern_diffuse = solar.getDiffuseFraction()

                # Should produce identical results
                assert legacy_flux == pytest.approx(modern_flux, rel=1e-6)
                assert legacy_par == pytest.approx(modern_par, rel=1e-6)
                assert legacy_nir == pytest.approx(modern_nir, rel=1e-6)
                assert legacy_diffuse == pytest.approx(modern_diffuse, rel=1e-6)

    def test_parameter_validation_setAtmosphericConditions(self):
        """Test parameter validation in setAtmosphericConditions"""
        with Context() as context:
            with SolarPosition(context) as solar:
                # Test invalid pressure
                with pytest.raises(ValueError, match="pressure must be non-negative"):
                    solar.setAtmosphericConditions(-1000, 288.15, 0.6, 0.1)

                # Test invalid temperature
                with pytest.raises(ValueError, match="[Tt]emperature must be non-negative"):
                    solar.setAtmosphericConditions(101325, -100, 0.6, 0.1)

                # Test invalid humidity
                with pytest.raises(ValueError, match="humidity must be between"):
                    solar.setAtmosphericConditions(101325, 288.15, 1.5, 0.1)

                # Test invalid turbidity
                with pytest.raises(ValueError, match="[Tt]urbidity must be non-negative"):
                    solar.setAtmosphericConditions(101325, 288.15, 0.6, -0.1)

    def test_partial_parameters_error(self):
        """Test that providing partial parameters raises ValueError"""
        with Context() as context:
            context.setDate(2023, 6, 21)
            context.setTime(12, 0)

            with SolarPosition(context) as solar:
                # Provide only some parameters - should raise ValueError
                with pytest.raises(ValueError, match="all atmospheric parameters"):
                    solar.getSolarFlux(pressure_Pa=101325)  # Missing others

                with pytest.raises(ValueError, match="all atmospheric parameters"):
                    solar.getSolarFlux(pressure_Pa=101325, temperature_K=288.15)  # Still missing humidity, turbidity

                with pytest.raises(ValueError, match="all atmospheric parameters"):
                    solar.getSolarFluxPAR(humidity_rel=0.6)  # Only one param

                with pytest.raises(ValueError, match="all atmospheric parameters"):
                    solar.getDiffuseFraction(turbidity=0.1)  # Only one param

    def test_getAmbientLongwaveFlux_legacy_api(self):
        """Test getAmbientLongwaveFlux with legacy API (2 parameters)"""
        with Context() as context:
            with SolarPosition(context) as solar:
                # Test legacy API (2 parameters)
                lw_flux_legacy = solar.getAmbientLongwaveFlux(288.15, 0.6)
                assert isinstance(lw_flux_legacy, float)
                assert lw_flux_legacy > 0
                assert lw_flux_legacy < 500  # Reasonable upper bound for longwave flux

    def test_getAmbientLongwaveFlux_modern_api(self):
        """Test getAmbientLongwaveFlux with modern API (no parameters)"""
        with Context() as context:
            with SolarPosition(context) as solar:
                # Set atmospheric conditions
                solar.setAtmosphericConditions(101325, 288.15, 0.6, 0.1)

                # Test modern API (no parameters)
                lw_flux_modern = solar.getAmbientLongwaveFlux()
                assert isinstance(lw_flux_modern, float)
                assert lw_flux_modern > 0
                assert lw_flux_modern < 500

    def test_getAmbientLongwaveFlux_partial_params(self):
        """Test getAmbientLongwaveFlux rejects partial parameters"""
        with Context() as context:
            with SolarPosition(context) as solar:
                # Only temperature provided
                with pytest.raises(ValueError, match="both temperature_K and humidity_rel"):
                    solar.getAmbientLongwaveFlux(temperature_K=288.15)

                # Only humidity provided
                with pytest.raises(ValueError, match="both temperature_K and humidity_rel"):
                    solar.getAmbientLongwaveFlux(humidity_rel=0.6)

    def test_modern_api_reuses_conditions(self):
        """Test that modern API efficiently reuses atmospheric conditions"""
        with Context() as context:
            context.setDate(2023, 6, 21)
            context.setTime(12, 0)

            with SolarPosition(context, utc_offset=0, latitude=0, longitude=0) as solar:
                # Set conditions once
                solar.setAtmosphericConditions(101325, 288.15, 0.6, 0.1)

                # Make multiple calls without repeating parameters
                flux1 = solar.getSolarFlux()
                flux2 = solar.getSolarFlux()
                par = solar.getSolarFluxPAR()
                nir = solar.getSolarFluxNIR()
                diffuse = solar.getDiffuseFraction()
                longwave = solar.getAmbientLongwaveFlux()

                # Flux should be consistent
                assert flux1 == pytest.approx(flux2)

                # All should return valid values
                assert flux1 > 0
                assert par > 0
                assert nir > 0
                assert 0.0 <= diffuse <= 1.0
                assert longwave > 0

    def test_mixed_api_usage(self):
        """Test that legacy and modern APIs can be mixed in same session"""
        with Context() as context:
            context.setDate(2023, 6, 21)
            context.setTime(12, 0)

            with SolarPosition(context, utc_offset=0, latitude=0, longitude=0) as solar:
                # Use modern API
                solar.setAtmosphericConditions(101325, 288.15, 0.6, 0.1)
                modern_flux = solar.getSolarFlux()

                # Use legacy API with different conditions
                legacy_flux = solar.getSolarFlux(101000, 300, 0.5, 0.05)

                # Both should work and return different values (different conditions)
                assert modern_flux > 0
                assert legacy_flux > 0
                assert modern_flux != pytest.approx(legacy_flux)  # Different conditions should give different results

    def test_error_message_quality(self):
        """Test that error messages provide helpful guidance"""
        with Context() as context:
            context.setDate(2023, 6, 21)
            context.setTime(12, 0)

            with SolarPosition(context) as solar:
                # Try to use modern API without setting conditions
                try:
                    solar.getSolarFlux()
                    # If no error, that's OK (C++ uses defaults)
                except SolarPositionError as e:
                    # Error should mention atmospheric conditions
                    error_msg = str(e).lower()
                    assert "atmospheric" in error_msg or "condition" in error_msg or "setAtmosphericConditions" in str(e)

class TestPragueSkyModelAssetPaths:
    """Prague sky model dataset must be found regardless of working directory.

    The Helios C++ code opens the dataset through a hardcoded relative path
    ("plugins/solarposition/lib/prague_sky_model/PragueSkyModelReduced.dat"),
    so it is only resolvable from the build directory. SolarPosition must
    manage the working directory internally the way RadiationModel and
    PlantArchitecture do -- otherwise the sky model silently fails to enable
    for any user whose CWD is not the build directory (i.e. everyone), and
    camera renders come out with a black sky.
    """

    @pytest.mark.native_only
    def test_enable_prague_sky_model_from_arbitrary_directory(self, tmp_path, monkeypatch):
        """enablePragueSkyModel must work when CWD is not the build directory."""
        registry = get_plugin_registry()
        if not registry.is_plugin_available('solarposition'):
            pytest.skip("solarposition plugin not available")

        # A directory with no Helios assets under it at all.
        monkeypatch.chdir(tmp_path)

        with Context() as context:
            context.setDate(2023, 6, 21)
            context.setTime(12, 0)
            with SolarPosition(context) as solar:
                solar.setAtmosphericConditions(101325.0, 293.15, 0.5, 0.05)
                solar.enablePragueSkyModel()
                assert solar.isPragueSkyModelEnabled()

    @pytest.mark.native_only
    def test_update_prague_sky_model_from_arbitrary_directory(self, tmp_path, monkeypatch):
        """updatePragueSkyModel must populate sky data from any working directory."""
        registry = get_plugin_registry()
        if not registry.is_plugin_available('solarposition'):
            pytest.skip("solarposition plugin not available")

        monkeypatch.chdir(tmp_path)

        with Context() as context:
            context.setDate(2023, 6, 21)
            context.setTime(12, 0)
            with SolarPosition(context) as solar:
                solar.setAtmosphericConditions(101325.0, 293.15, 0.5, 0.05)
                solar.enablePragueSkyModel()
                solar.updatePragueSkyModel(ground_albedo=0.25)

                # The valid flag is what RadiationModel checks before using
                # atmospheric sky radiance for camera rendering.
                assert context.doesGlobalDataExist("prague_sky_valid")

    @pytest.mark.native_only
    def test_working_directory_is_restored(self, tmp_path, monkeypatch):
        """The CWD must be restored after the sky model calls."""
        registry = get_plugin_registry()
        if not registry.is_plugin_available('solarposition'):
            pytest.skip("solarposition plugin not available")

        monkeypatch.chdir(tmp_path)
        import os
        expected = os.getcwd()

        with Context() as context:
            context.setDate(2023, 6, 21)
            context.setTime(12, 0)
            with SolarPosition(context) as solar:
                solar.setAtmosphericConditions(101325.0, 293.15, 0.5, 0.05)
                solar.enablePragueSkyModel()
                solar.updatePragueSkyModel(ground_albedo=0.25)

        assert os.getcwd() == expected


@pytest.mark.native_only
class TestSetSunDirection:
    """Test prescribed sun direction override (SolarPosition::setSunDirection)"""

    def _skip_if_unavailable(self):
        registry = get_plugin_registry()
        if not registry.is_plugin_available('solarposition'):
            pytest.skip("solarposition plugin not available")

    def test_set_sun_direction_overrides_computed_position(self):
        """setSunDirection must override the time-based solar position."""
        self._skip_if_unavailable()

        with Context() as context:
            context.setDate(2023, 6, 21)
            context.setTime(12, 0)
            with SolarPosition(context, 8, 38.55, -121.76) as solar:
                computed_elevation = solar.getSunElevation()

                # Prescribe a sun position clearly different from the computed one.
                prescribed_elevation = 0.25
                prescribed_azimuth = 1.5
                solar.setSunDirection(
                    SphericalCoord(1.0, prescribed_elevation, prescribed_azimuth)
                )

                assert solar.getSunElevation() == pytest.approx(prescribed_elevation, abs=1e-4)
                assert solar.getSunAzimuth() == pytest.approx(prescribed_azimuth, abs=1e-4)
                assert solar.getSunElevation() != pytest.approx(computed_elevation, abs=1e-3)

    def test_set_sun_direction_propagates_to_zenith_and_vector(self):
        """The override must be reflected by every downstream sun getter."""
        self._skip_if_unavailable()

        with Context() as context:
            context.setDate(2023, 6, 21)
            context.setTime(12, 0)
            with SolarPosition(context, 8, 38.55, -121.76) as solar:
                elevation = 0.4
                azimuth = 0.9
                solar.setSunDirection(SphericalCoord(1.0, elevation, azimuth))

                # zenith is the complement of elevation
                assert solar.getSunZenith() == pytest.approx(math.pi / 2 - elevation, abs=1e-4)

                # Unit direction vector must match the prescribed spherical angles.
                direction = solar.getSunDirectionVector()
                assert math.sqrt(
                    direction.x ** 2 + direction.y ** 2 + direction.z ** 2
                ) == pytest.approx(1.0, abs=1e-4)
                assert direction.z == pytest.approx(math.sin(elevation), abs=1e-4)

                spherical = solar.getSunDirectionSpherical()
                assert spherical.elevation == pytest.approx(elevation, abs=1e-4)
                assert spherical.azimuth == pytest.approx(azimuth, abs=1e-4)

    def test_set_sun_direction_rejects_wrong_type(self):
        """Wrong argument types must raise ValueError, positionally and by keyword."""
        self._skip_if_unavailable()

        with Context() as context:
            with SolarPosition(context) as solar:
                with pytest.raises(ValueError, match="SphericalCoord"):
                    solar.setSunDirection(vec3(1, 0, 0))
                with pytest.raises(ValueError, match="SphericalCoord"):
                    solar.setSunDirection(sundirection=vec3(1, 0, 0))
                with pytest.raises(ValueError, match="SphericalCoord"):
                    solar.setSunDirection([1.0, 0.0, 0.0])


@pytest.mark.native_only
class TestCalibrateTurbidityReturnValue:
    """calibrateTurbidityFromTimeseries must return the calibrated turbidity"""

    def _skip_if_unavailable(self):
        registry = get_plugin_registry()
        if not registry.is_plugin_available('solarposition'):
            pytest.skip("solarposition plugin not available")

    def test_calibrate_turbidity_returns_float(self):
        """The C++ method returns the calibrated value; it must not be discarded.

        The method is const in C++ and does not store its result, so the return
        value is the only way for a caller to obtain the calibrated turbidity.
        """
        self._skip_if_unavailable()

        with Context() as context:
            context.setDate(2023, 6, 21)

            # Build a clear-sky-like timeseries of global horizontal shortwave flux.
            label = "shortwave_flux"
            for hour in range(5, 20):
                context.addTimeseriesData(
                    label,
                    _clear_sky_flux_Wm2(hour),
                    Date(2023, 6, 21),
                    Time(hour, 0, 0),
                )

            with SolarPosition(context, 8, 38.55, -121.76) as solar:
                result = solar.calibrateTurbidityFromTimeseries(label)

                assert result is not None, (
                    "calibrateTurbidityFromTimeseries discarded the native return value"
                )
                assert isinstance(result, float)
                assert result >= 0.0

    def test_wrapper_layer_returns_turbidity(self):
        """The ctypes wrapper layer must also propagate the value."""
        self._skip_if_unavailable()

        from pyhelios.wrappers import USolarPositionWrapper as solar_wrapper

        with Context() as context:
            context.setDate(2023, 6, 21)
            label = "shortwave_flux"
            for hour in range(5, 20):
                context.addTimeseriesData(
                    label,
                    _clear_sky_flux_Wm2(hour),
                    Date(2023, 6, 21),
                    Time(hour, 0, 0),
                )

            with SolarPosition(context, 8, 38.55, -121.76) as solar:
                value = solar_wrapper.calibrateTurbidityFromTimeseries(
                    solar._solar_pos, label
                )
                assert value is not None
                assert isinstance(value, float)


def _clear_sky_flux_Wm2(hour):
    """Approximate clear-sky global horizontal flux for a summer day."""
    # Simple sinusoid peaking at solar noon; zero outside daylight.
    fraction = (hour - 5.0) / 14.0
    if fraction <= 0.0 or fraction >= 1.0:
        return 0.0
    return 950.0 * math.sin(math.pi * fraction)


@pytest.mark.native_only
class TestCloudCalibrationV1383:
    """helios-core 1.3.83 cloud-calibration fixes to the band partitioning."""

    ATMOSPHERE = (101000.0, 300.0, 0.5, 0.05)

    @staticmethod
    def _noon_context():
        context = Context()
        context.setDate(2023, 6, 21)
        context.setTime(12, 0)
        for hour in range(6, 19):
            context.addTimeseriesData("R_meas", 500.0, Date(2023, 6, 21), Time(hour, 0, 0))
        return context

    def test_calibrated_par_and_nir_are_not_identical(self):
        """Each band previously derived attenuation from itself, collapsing both to the same value."""
        with self._noon_context() as context:
            with SolarPosition(context, utc_offset=-8, latitude=38.5, longitude=-121.7) as solar:
                solar.enableCloudCalibration("R_meas")
                par = solar.getSolarFluxPAR(*self.ATMOSPHERE)
                nir = solar.getSolarFluxNIR(*self.ATMOSPHERE)

                assert par > 0 and nir > 0
                assert abs(par - nir) > 1e-3, "PAR and NIR collapsed to the same value"

    def test_calibrated_par_plus_nir_equals_total(self):
        """They previously each inflated to the broadband flux and summed to twice it."""
        with self._noon_context() as context:
            with SolarPosition(context, utc_offset=-8, latitude=38.5, longitude=-121.7) as solar:
                solar.enableCloudCalibration("R_meas")
                total = solar.getSolarFlux(*self.ATMOSPHERE)
                par = solar.getSolarFluxPAR(*self.ATMOSPHERE)
                nir = solar.getSolarFluxNIR(*self.ATMOSPHERE)

                assert total > 0
                assert par + nir == pytest.approx(total, rel=1e-3)

    def test_cloud_calibration_preserves_clear_sky_band_ratio(self):
        """The attenuation factor is computed once from all-wave flux and applied to both bands."""
        with self._noon_context() as context:
            with SolarPosition(context, utc_offset=-8, latitude=38.5, longitude=-121.7) as solar:
                clear_par = solar.getSolarFluxPAR(*self.ATMOSPHERE)
                clear_nir = solar.getSolarFluxNIR(*self.ATMOSPHERE)
                clear_ratio = clear_par / (clear_par + clear_nir)

                solar.enableCloudCalibration("R_meas")
                par = solar.getSolarFluxPAR(*self.ATMOSPHERE)
                nir = solar.getSolarFluxNIR(*self.ATMOSPHERE)

                assert par / (par + nir) == pytest.approx(clear_ratio, rel=1e-3)

    def test_calibrated_diffuse_fraction_is_not_saturated(self):
        """The old expression clamped to a fully-diffuse sky for every real cloud condition."""
        with self._noon_context() as context:
            with SolarPosition(context, utc_offset=-8, latitude=38.5, longitude=-121.7) as solar:
                solar.enableCloudCalibration("R_meas")
                fdiff = solar.getDiffuseFraction(*self.ATMOSPHERE)

                assert 0.0 <= fdiff <= 1.0
                assert fdiff < 1.0, "diffuse fraction saturated at fully-diffuse"
