// PyHelios C Interface - SolarPosition Plugin Implementation
// Provides solar angle calculations, radiation modeling, and time-dependent solar functions

#include "../include/pyhelios_wrapper_common.h"
#include "../include/pyhelios_wrapper_solarposition.h"

#ifdef SOLARPOSITION_PLUGIN_AVAILABLE
#include "SolarPosition.h"
#include "Context.h"
#include <string>
#include <exception>
#include <thread>
#include <cstring>

extern "C" {

// Plugin creation and destruction
HeliosSolarPosition* createSolarPosition(void* context_ptr) {
    try {
        clearError();
        if (!context_ptr) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
            return nullptr;
        }
        
        helios::Context* context = static_cast<helios::Context*>(context_ptr);
        SolarPosition* solar_pos = new SolarPosition(context);
        return reinterpret_cast<HeliosSolarPosition*>(solar_pos);
        
    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
        return nullptr;
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (createSolarPosition): ") + e.what());
        return nullptr;
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (createSolarPosition): Unknown error");
        return nullptr;
    }
}

HeliosSolarPosition* createSolarPositionWithCoordinates(void* context_ptr, float UTC_hours, float latitude_deg, float longitude_deg) {
    try {
        clearError();
        if (!context_ptr) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
            return nullptr;
        }
        
        // Validate parameters
        if (latitude_deg < -90.0f || latitude_deg > 90.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Latitude must be between -90 and +90 degrees");
            return nullptr;
        }
        if (longitude_deg < -180.0f || longitude_deg > 180.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Longitude must be between -180 and +180 degrees");
            return nullptr;
        }
        if (UTC_hours < -12.0f || UTC_hours > 12.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UTC offset must be between -12 and +12 hours");
            return nullptr;
        }
        
        helios::Context* context = static_cast<helios::Context*>(context_ptr);
        SolarPosition* solar_pos = new SolarPosition(UTC_hours, latitude_deg, longitude_deg, context);
        return reinterpret_cast<HeliosSolarPosition*>(solar_pos);
        
    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
        return nullptr;
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (createSolarPositionWithCoordinates): ") + e.what());
        return nullptr;
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (createSolarPositionWithCoordinates): Unknown error");
        return nullptr;
    }
}

void destroySolarPosition(HeliosSolarPosition* solar_pos) {
    if (solar_pos) {
        delete reinterpret_cast<SolarPosition*>(solar_pos);
    }
}

// Solar angle calculations - basic angles in degrees
float getSunElevation(HeliosSolarPosition* solar_pos) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return 0.0f;
        }
        
        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        return sp->getSunElevation();
        
    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
        return 0.0f;
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getSunElevation): ") + e.what());
        return 0.0f;
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getSunElevation): Unknown error");
        return 0.0f;
    }
}

float getSunZenith(HeliosSolarPosition* solar_pos) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return 0.0f;
        }
        
        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        return sp->getSunZenith();
        
    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
        return 0.0f;
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getSunZenith): ") + e.what());
        return 0.0f;
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getSunZenith): Unknown error");
        return 0.0f;
    }
}

float getSunAzimuth(HeliosSolarPosition* solar_pos) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return 0.0f;
        }
        
        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        return sp->getSunAzimuth();
        
    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
        return 0.0f;
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getSunAzimuth): ") + e.what());
        return 0.0f;
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getSunAzimuth): Unknown error");
        return 0.0f;
    }
}

// Solar direction vectors
float* getSunDirectionVector(HeliosSolarPosition* solar_pos) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return nullptr;
        }
        
        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        helios::vec3 direction = sp->getSunDirectionVector();
        
        // Use thread-local static to return array safely
        static thread_local std::vector<float> static_result(3);
        static_result[0] = direction.x;
        static_result[1] = direction.y;
        static_result[2] = direction.z;
        
        return static_result.data();
        
    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
        return nullptr;
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getSunDirectionVector): ") + e.what());
        return nullptr;
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getSunDirectionVector): Unknown error");
        return nullptr;
    }
}

float* getSunDirectionSpherical(HeliosSolarPosition* solar_pos) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return nullptr;
        }
        
        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        helios::SphericalCoord spherical = sp->getSunDirectionSpherical();
        
        // Use thread-local static to return array safely - 3 elements (radius, elevation, azimuth)
        static thread_local std::vector<float> static_result(3);
        static_result[0] = spherical.radius;
        static_result[1] = spherical.elevation;
        static_result[2] = spherical.azimuth;
        
        return static_result.data();
        
    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
        return nullptr;
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getSunDirectionSpherical): ") + e.what());
        return nullptr;
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getSunDirectionSpherical): Unknown error");
        return nullptr;
    }
}

// Solar flux calculations - all take atmospheric parameters
float getSolarFlux(HeliosSolarPosition* solar_pos, float pressure_Pa, float temperature_K, float humidity_rel, float turbidity) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return 0.0f;
        }
        
        // Validate atmospheric parameters
        if (pressure_Pa < 0.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Atmospheric pressure must be non-negative");
            return 0.0f;
        }
        if (temperature_K < 0.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Temperature must be non-negative");
            return 0.0f;
        }
        if (humidity_rel < 0.0f || humidity_rel > 1.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Relative humidity must be between 0 and 1");
            return 0.0f;
        }
        if (turbidity < 0.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Turbidity must be non-negative");
            return 0.0f;
        }
        
        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        sp->setAtmosphericConditions(pressure_Pa, temperature_K, humidity_rel, turbidity);
        return sp->getSolarFlux();
        
    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
        return 0.0f;
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getSolarFlux): ") + e.what());
        return 0.0f;
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getSolarFlux): Unknown error");
        return 0.0f;
    }
}

float getSolarFluxPAR(HeliosSolarPosition* solar_pos, float pressure_Pa, float temperature_K, float humidity_rel, float turbidity) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return 0.0f;
        }
        
        // Validate atmospheric parameters
        if (pressure_Pa < 0.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Atmospheric pressure must be non-negative");
            return 0.0f;
        }
        if (temperature_K < 0.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Temperature must be non-negative");
            return 0.0f;
        }
        if (humidity_rel < 0.0f || humidity_rel > 1.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Relative humidity must be between 0 and 1");
            return 0.0f;
        }
        if (turbidity < 0.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Turbidity must be non-negative");
            return 0.0f;
        }
        
        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        sp->setAtmosphericConditions(pressure_Pa, temperature_K, humidity_rel, turbidity);
        return sp->getSolarFluxPAR();
        
    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
        return 0.0f;
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getSolarFluxPAR): ") + e.what());
        return 0.0f;
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getSolarFluxPAR): Unknown error");
        return 0.0f;
    }
}

float getSolarFluxNIR(HeliosSolarPosition* solar_pos, float pressure_Pa, float temperature_K, float humidity_rel, float turbidity) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return 0.0f;
        }
        
        // Validate atmospheric parameters
        if (pressure_Pa < 0.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Atmospheric pressure must be non-negative");
            return 0.0f;
        }
        if (temperature_K < 0.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Temperature must be non-negative");
            return 0.0f;
        }
        if (humidity_rel < 0.0f || humidity_rel > 1.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Relative humidity must be between 0 and 1");
            return 0.0f;
        }
        if (turbidity < 0.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Turbidity must be non-negative");
            return 0.0f;
        }
        
        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        sp->setAtmosphericConditions(pressure_Pa, temperature_K, humidity_rel, turbidity);
        return sp->getSolarFluxNIR();
        
    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
        return 0.0f;
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getSolarFluxNIR): ") + e.what());
        return 0.0f;
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getSolarFluxNIR): Unknown error");
        return 0.0f;
    }
}

float getDiffuseFraction(HeliosSolarPosition* solar_pos, float pressure_Pa, float temperature_K, float humidity_rel, float turbidity) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return 0.0f;
        }
        
        // Validate atmospheric parameters
        if (pressure_Pa < 0.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Atmospheric pressure must be non-negative");
            return 0.0f;
        }
        if (temperature_K < 0.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Temperature must be non-negative");
            return 0.0f;
        }
        if (humidity_rel < 0.0f || humidity_rel > 1.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Relative humidity must be between 0 and 1");
            return 0.0f;
        }
        if (turbidity < 0.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Turbidity must be non-negative");
            return 0.0f;
        }
        
        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        sp->setAtmosphericConditions(pressure_Pa, temperature_K, humidity_rel, turbidity);
        return sp->getDiffuseFraction();
        
    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
        return 0.0f;
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getDiffuseFraction): ") + e.what());
        return 0.0f;
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getDiffuseFraction): Unknown error");
        return 0.0f;
    }
}

// Atmospheric condition management (modern API)
void setAtmosphericConditions(HeliosSolarPosition* solar_pos, float pressure_Pa, float temperature_K, float humidity_rel, float turbidity) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return;
        }

        // Validate parameters
        if (pressure_Pa < 0.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Atmospheric pressure must be non-negative");
            return;
        }
        if (temperature_K < 0.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Temperature must be non-negative");
            return;
        }
        if (humidity_rel < 0.0f || humidity_rel > 1.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Relative humidity must be between 0 and 1");
            return;
        }
        if (turbidity < 0.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Turbidity must be non-negative");
            return;
        }

        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        sp->setAtmosphericConditions(pressure_Pa, temperature_K, humidity_rel, turbidity);

    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setAtmosphericConditions): ") + e.what());
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setAtmosphericConditions): Unknown error");
    }
}

void getAtmosphericConditions(HeliosSolarPosition* solar_pos, float* pressure_Pa, float* temperature_K, float* humidity_rel, float* turbidity) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return;
        }
        if (!pressure_Pa || !temperature_K || !humidity_rel || !turbidity) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output parameters cannot be null");
            return;
        }

        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        sp->getAtmosphericConditions(*pressure_Pa, *temperature_K, *humidity_rel, *turbidity);

    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getAtmosphericConditions): ") + e.what());
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getAtmosphericConditions): Unknown error");
    }
}

// Modern parameter-free flux methods (use atmospheric conditions from Context)
float getSolarFluxFromState(HeliosSolarPosition* solar_pos) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return 0.0f;
        }

        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        return sp->getSolarFlux();

    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
        return 0.0f;
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getSolarFluxFromState): ") + e.what());
        return 0.0f;
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getSolarFluxFromState): Unknown error");
        return 0.0f;
    }
}

float getSolarFluxPARFromState(HeliosSolarPosition* solar_pos) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return 0.0f;
        }

        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        return sp->getSolarFluxPAR();

    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
        return 0.0f;
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getSolarFluxPARFromState): ") + e.what());
        return 0.0f;
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getSolarFluxPARFromState): Unknown error");
        return 0.0f;
    }
}

float getSolarFluxNIRFromState(HeliosSolarPosition* solar_pos) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return 0.0f;
        }

        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        return sp->getSolarFluxNIR();

    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
        return 0.0f;
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getSolarFluxNIRFromState): ") + e.what());
        return 0.0f;
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getSolarFluxNIRFromState): Unknown error");
        return 0.0f;
    }
}

float getDiffuseFractionFromState(HeliosSolarPosition* solar_pos) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return 0.0f;
        }

        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        return sp->getDiffuseFraction();

    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
        return 0.0f;
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getDiffuseFractionFromState): ") + e.what());
        return 0.0f;
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getDiffuseFractionFromState): Unknown error");
        return 0.0f;
    }
}

float getAmbientLongwaveFluxFromState(HeliosSolarPosition* solar_pos) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return 0.0f;
        }

        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        return sp->getAmbientLongwaveFlux();

    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
        return 0.0f;
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getAmbientLongwaveFluxFromState): ") + e.what());
        return 0.0f;
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getAmbientLongwaveFluxFromState): Unknown error");
        return 0.0f;
    }
}

// Time calculations - returns Time structure components
void getSunriseTime(HeliosSolarPosition* solar_pos, int* hour, int* minute, int* second) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return;
        }
        if (!hour || !minute || !second) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output parameters cannot be null");
            return;
        }
        
        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        helios::Time sunrise = sp->getSunriseTime();
        
        *hour = sunrise.hour;
        *minute = sunrise.minute;
        *second = sunrise.second;
        
    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getSunriseTime): ") + e.what());
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getSunriseTime): Unknown error");
    }
}

void getSunsetTime(HeliosSolarPosition* solar_pos, int* hour, int* minute, int* second) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return;
        }
        if (!hour || !minute || !second) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output parameters cannot be null");
            return;
        }
        
        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        helios::Time sunset = sp->getSunsetTime();
        
        *hour = sunset.hour;
        *minute = sunset.minute;
        *second = sunset.second;
        
    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getSunsetTime): ") + e.what());
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getSunsetTime): Unknown error");
    }
}

// Calibration functions
float calibrateTurbidityFromTimeseries(HeliosSolarPosition* solar_pos, const char* timeseries_label) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return 0.0f;
        }
        if (!timeseries_label) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Timeseries label cannot be null");
            return 0.0f;
        }
        
        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        std::string label(timeseries_label);
        float result = sp->calibrateTurbidityFromTimeseries(label);
        return result;
        
    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
        return 0.0f;
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (calibrateTurbidityFromTimeseries): ") + e.what());
        return 0.0f;
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (calibrateTurbidityFromTimeseries): Unknown error");
        return 0.0f;
    }
}

void enableCloudCalibration(HeliosSolarPosition* solar_pos, const char* timeseries_label) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return;
        }
        if (!timeseries_label) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Timeseries label cannot be null");
            return;
        }
        
        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        std::string label(timeseries_label);
        sp->enableCloudCalibration(label);
        
    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (enableCloudCalibration): ") + e.what());
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (enableCloudCalibration): Unknown error");
    }
}

void disableCloudCalibration(HeliosSolarPosition* solar_pos) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return;
        }
        
        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        sp->disableCloudCalibration();
        
    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (disableCloudCalibration): ") + e.what());
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (disableCloudCalibration): Unknown error");
    }
}

// SSolar-GOA Spectral Solar Model Methods

void calculateDirectSolarSpectrum(HeliosSolarPosition* solar_pos, const char* label, float resolution_nm) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return;
        }
        if (!label) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label pointer is null");
            return;
        }

        // Validate resolution parameter
        if (resolution_nm < 1.0f || resolution_nm > 2300.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Wavelength resolution must be between 1 and 2300 nm");
            return;
        }

        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        sp->calculateDirectSolarSpectrum(std::string(label), resolution_nm);

    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (calculateDirectSolarSpectrum): ") + e.what());
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (calculateDirectSolarSpectrum): Unknown error");
    }
}

void calculateDiffuseSolarSpectrum(HeliosSolarPosition* solar_pos, const char* label, float resolution_nm) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return;
        }
        if (!label) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label pointer is null");
            return;
        }

        // Validate resolution parameter
        if (resolution_nm < 1.0f || resolution_nm > 2300.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Wavelength resolution must be between 1 and 2300 nm");
            return;
        }

        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        sp->calculateDiffuseSolarSpectrum(std::string(label), resolution_nm);

    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (calculateDiffuseSolarSpectrum): ") + e.what());
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (calculateDiffuseSolarSpectrum): Unknown error");
    }
}

void calculateGlobalSolarSpectrum(HeliosSolarPosition* solar_pos, const char* label, float resolution_nm) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return;
        }
        if (!label) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label pointer is null");
            return;
        }

        // Validate resolution parameter
        if (resolution_nm < 1.0f || resolution_nm > 2300.0f) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Wavelength resolution must be between 1 and 2300 nm");
            return;
        }

        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        sp->calculateGlobalSolarSpectrum(std::string(label), resolution_nm);

    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (calculateGlobalSolarSpectrum): ") + e.what());
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (calculateGlobalSolarSpectrum): Unknown error");
    }
}

// Prague Sky Model Functions

void enablePragueSkyModel(HeliosSolarPosition* solar_pos) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return;
        }

        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        sp->enablePragueSkyModel();

    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (enablePragueSkyModel): ") + e.what());
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (enablePragueSkyModel): Unknown error");
    }
}

bool isPragueSkyModelEnabled(HeliosSolarPosition* solar_pos) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return false;
        }

        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        return sp->isPragueSkyModelEnabled();

    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
        return false;
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (isPragueSkyModelEnabled): ") + e.what());
        return false;
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (isPragueSkyModelEnabled): Unknown error");
        return false;
    }
}

void updatePragueSkyModel(HeliosSolarPosition* solar_pos, float ground_albedo) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return;
        }

        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        sp->updatePragueSkyModel(ground_albedo);

    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (updatePragueSkyModel): ") + e.what());
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (updatePragueSkyModel): Unknown error");
    }
}

bool pragueSkyModelNeedsUpdate(HeliosSolarPosition* solar_pos, float ground_albedo,
                                float sun_tolerance, float turbidity_tolerance, float albedo_tolerance) {
    try {
        clearError();
        if (!solar_pos) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "SolarPosition pointer is null");
            return false;
        }

        SolarPosition* sp = reinterpret_cast<SolarPosition*>(solar_pos);
        return sp->pragueSkyModelNeedsUpdate(ground_albedo, sun_tolerance, turbidity_tolerance, albedo_tolerance);

    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
        return false;
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (pragueSkyModelNeedsUpdate): ") + e.what());
        return false;
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (pragueSkyModelNeedsUpdate): Unknown error");
        return false;
    }
}

// Note: Additional utility functions can be added here as needed

} // extern "C"

#endif // SOLARPOSITION_PLUGIN_AVAILABLE