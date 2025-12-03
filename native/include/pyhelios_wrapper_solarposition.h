// PyHelios C Interface - SolarPosition Plugin Functions
// Provides solar angle calculations, radiation modeling, and time-dependent solar functions

#ifndef PYHELIOS_WRAPPER_SOLARPOSITION_H
#define PYHELIOS_WRAPPER_SOLARPOSITION_H

#include "pyhelios_wrapper_common.h"

#ifdef __cplusplus
extern "C" {
#endif

#ifdef SOLARPOSITION_PLUGIN_AVAILABLE

// Forward declaration for SolarPosition plugin
struct HeliosSolarPosition;

// Plugin creation and destruction
PYHELIOS_API HeliosSolarPosition* createSolarPosition(void* context_ptr);
PYHELIOS_API HeliosSolarPosition* createSolarPositionWithCoordinates(void* context_ptr, float UTC_hours, float latitude_deg, float longitude_deg);
PYHELIOS_API void destroySolarPosition(HeliosSolarPosition* solar_pos);

// Solar angle calculations - basic angles in degrees
PYHELIOS_API float getSunElevation(HeliosSolarPosition* solar_pos);
PYHELIOS_API float getSunZenith(HeliosSolarPosition* solar_pos);
PYHELIOS_API float getSunAzimuth(HeliosSolarPosition* solar_pos);

// Solar direction vectors
PYHELIOS_API float* getSunDirectionVector(HeliosSolarPosition* solar_pos);
PYHELIOS_API float* getSunDirectionSpherical(HeliosSolarPosition* solar_pos);

// Solar flux calculations - all take atmospheric parameters
PYHELIOS_API float getSolarFlux(HeliosSolarPosition* solar_pos, float pressure_Pa, float temperature_K, float humidity_rel, float turbidity);
PYHELIOS_API float getSolarFluxPAR(HeliosSolarPosition* solar_pos, float pressure_Pa, float temperature_K, float humidity_rel, float turbidity);
PYHELIOS_API float getSolarFluxNIR(HeliosSolarPosition* solar_pos, float pressure_Pa, float temperature_K, float humidity_rel, float turbidity);
PYHELIOS_API float getDiffuseFraction(HeliosSolarPosition* solar_pos, float pressure_Pa, float temperature_K, float humidity_rel, float turbidity);

// Time calculations - returns Time structure components
PYHELIOS_API void getSunriseTime(HeliosSolarPosition* solar_pos, int* hour, int* minute, int* second);
PYHELIOS_API void getSunsetTime(HeliosSolarPosition* solar_pos, int* hour, int* minute, int* second);

// Calibration functions
PYHELIOS_API float calibrateTurbidityFromTimeseries(HeliosSolarPosition* solar_pos, const char* timeseries_label);
PYHELIOS_API void enableCloudCalibration(HeliosSolarPosition* solar_pos, const char* timeseries_label);
PYHELIOS_API void disableCloudCalibration(HeliosSolarPosition* solar_pos);

// SSolar-GOA Spectral Solar Model Methods
PYHELIOS_API void calculateDirectSolarSpectrum(HeliosSolarPosition* solar_pos, const char* label, float resolution_nm);
PYHELIOS_API void calculateDiffuseSolarSpectrum(HeliosSolarPosition* solar_pos, const char* label, float resolution_nm);
PYHELIOS_API void calculateGlobalSolarSpectrum(HeliosSolarPosition* solar_pos, const char* label, float resolution_nm);

// Note: Additional utility functions can be added here as needed

#endif // SOLARPOSITION_PLUGIN_AVAILABLE

#ifdef __cplusplus
}
#endif

#endif // PYHELIOS_WRAPPER_SOLARPOSITION_H