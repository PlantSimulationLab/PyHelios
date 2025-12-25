// PyHelios C Interface - EnergyBalance Functions
// Provides plant energy balance calculations and thermal modeling functions

#include "../include/pyhelios_wrapper_common.h"
#include "../include/pyhelios_wrapper_context.h"
#include "Context.h"
#include <string>
#include <exception>

#ifdef ENERGYBALANCE_PLUGIN_AVAILABLE
#include "../include/pyhelios_wrapper_energybalance.h"
#include "EnergyBalanceModel.h"

extern "C" {
    
    PYHELIOS_API EnergyBalanceModel* createEnergyBalanceModel(helios::Context* context) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return nullptr;
            }
            
            return new EnergyBalanceModel(context);
            
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (createEnergyBalanceModel): ") + e.what());
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (createEnergyBalanceModel): Unknown error creating EnergyBalanceModel.");
            return nullptr;
        }
    }
    
    PYHELIOS_API void destroyEnergyBalanceModel(EnergyBalanceModel* energy_model) {
        if (energy_model) {
            delete energy_model;
        }
    }
    
    PYHELIOS_API void enableEnergyBalanceMessages(EnergyBalanceModel* energy_model) {
        try {
            clearError();
            if (!energy_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "EnergyBalanceModel pointer is null");
                return;
            }
            
            energy_model->enableMessages();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (EnergyBalanceModel::enableMessages): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (EnergyBalanceModel::enableMessages): Unknown error enabling messages.");
        }
    }
    
    PYHELIOS_API void disableEnergyBalanceMessages(EnergyBalanceModel* energy_model) {
        try {
            clearError();
            if (!energy_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "EnergyBalanceModel pointer is null");
                return;
            }
            
            energy_model->disableMessages();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (EnergyBalanceModel::disableMessages): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (EnergyBalanceModel::disableMessages): Unknown error disabling messages.");
        }
    }
    
    PYHELIOS_API void runEnergyBalance(EnergyBalanceModel* energy_model) {
        try {
            clearError();
            if (!energy_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "EnergyBalanceModel pointer is null");
                return;
            }
            
            energy_model->run();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (EnergyBalanceModel::run): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (EnergyBalanceModel::run): Unknown error running energy balance.");
        }
    }
    
    PYHELIOS_API void runEnergyBalanceDynamic(EnergyBalanceModel* energy_model, float dt) {
        try {
            clearError();
            if (!energy_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "EnergyBalanceModel pointer is null");
                return;
            }
            if (dt <= 0.0f) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Time step must be positive");
                return;
            }
            
            energy_model->run(dt);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (EnergyBalanceModel::run): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (EnergyBalanceModel::run): Unknown error running dynamic energy balance.");
        }
    }
    
    PYHELIOS_API void runEnergyBalanceForUUIDs(EnergyBalanceModel* energy_model, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!energy_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "EnergyBalanceModel pointer is null");
                return;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null");
                return;
            }
            if (uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUID count must be greater than 0");
                return;
            }
            
            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            energy_model->run(uuid_vector);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (EnergyBalanceModel::run): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (EnergyBalanceModel::run): Unknown error running energy balance for UUIDs.");
        }
    }
    
    PYHELIOS_API void runEnergyBalanceForUUIDsDynamic(EnergyBalanceModel* energy_model, const unsigned int* uuids, unsigned int uuid_count, float dt) {
        try {
            clearError();
            if (!energy_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "EnergyBalanceModel pointer is null");
                return;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null");
                return;
            }
            if (uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUID count must be greater than 0");
                return;
            }
            if (dt <= 0.0f) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Time step must be positive");
                return;
            }
            
            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            energy_model->run(uuid_vector, dt);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (EnergyBalanceModel::run): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (EnergyBalanceModel::run): Unknown error running dynamic energy balance for UUIDs.");
        }
    }
    
    PYHELIOS_API void addEnergyBalanceRadiationBand(EnergyBalanceModel* energy_model, const char* band) {
        try {
            clearError();
            if (!energy_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "EnergyBalanceModel pointer is null");
                return;
            }
            if (!band) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Band name is null");
                return;
            }
            
            energy_model->addRadiationBand(band);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (EnergyBalanceModel::addRadiationBand): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (EnergyBalanceModel::addRadiationBand): Unknown error adding radiation band.");
        }
    }
    
    PYHELIOS_API void addEnergyBalanceRadiationBands(EnergyBalanceModel* energy_model, const char* const* bands, unsigned int band_count) {
        try {
            clearError();
            if (!energy_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "EnergyBalanceModel pointer is null");
                return;
            }
            if (!bands) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Bands array is null");
                return;
            }
            if (band_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Band count must be greater than 0");
                return;
            }
            
            std::vector<std::string> band_vector;
            for (unsigned int i = 0; i < band_count; i++) {
                if (bands[i]) {
                    band_vector.push_back(std::string(bands[i]));
                }
            }
            energy_model->addRadiationBand(band_vector);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (EnergyBalanceModel::addRadiationBand): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (EnergyBalanceModel::addRadiationBand): Unknown error adding radiation bands.");
        }
    }
    
    PYHELIOS_API void enableAirEnergyBalance(EnergyBalanceModel* energy_model) {
        try {
            clearError();
            if (!energy_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "EnergyBalanceModel pointer is null");
                return;
            }
            
            energy_model->enableAirEnergyBalance();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (EnergyBalanceModel::enableAirEnergyBalance): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (EnergyBalanceModel::enableAirEnergyBalance): Unknown error enabling air energy balance.");
        }
    }
    
    PYHELIOS_API void enableAirEnergyBalanceWithParameters(EnergyBalanceModel* energy_model, float canopy_height_m, float reference_height_m) {
        try {
            clearError();
            if (!energy_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "EnergyBalanceModel pointer is null");
                return;
            }
            if (canopy_height_m <= 0.0f) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Canopy height must be positive");
                return;
            }
            if (reference_height_m <= 0.0f) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Reference height must be positive");
                return;
            }
            
            energy_model->enableAirEnergyBalance(canopy_height_m, reference_height_m);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (EnergyBalanceModel::enableAirEnergyBalance): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (EnergyBalanceModel::enableAirEnergyBalance): Unknown error enabling air energy balance with parameters.");
        }
    }
    
    PYHELIOS_API void evaluateAirEnergyBalance(EnergyBalanceModel* energy_model, float dt_sec, float time_advance_sec) {
        try {
            clearError();
            if (!energy_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "EnergyBalanceModel pointer is null");
                return;
            }
            if (dt_sec <= 0.0f) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Time step must be positive");
                return;
            }
            if (time_advance_sec < dt_sec) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Total time advance must be greater than or equal to time step");
                return;
            }
            
            energy_model->evaluateAirEnergyBalance(dt_sec, time_advance_sec);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (EnergyBalanceModel::evaluateAirEnergyBalance): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (EnergyBalanceModel::evaluateAirEnergyBalance): Unknown error evaluating air energy balance.");
        }
    }
    
    PYHELIOS_API void evaluateAirEnergyBalanceForUUIDs(EnergyBalanceModel* energy_model, const unsigned int* uuids, unsigned int uuid_count, float dt_sec, float time_advance_sec) {
        try {
            clearError();
            if (!energy_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "EnergyBalanceModel pointer is null");
                return;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null");
                return;
            }
            if (uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUID count must be greater than 0");
                return;
            }
            if (dt_sec <= 0.0f) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Time step must be positive");
                return;
            }
            if (time_advance_sec < dt_sec) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Total time advance must be greater than or equal to time step");
                return;
            }
            
            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            energy_model->evaluateAirEnergyBalance(uuid_vector, dt_sec, time_advance_sec);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (EnergyBalanceModel::evaluateAirEnergyBalance): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (EnergyBalanceModel::evaluateAirEnergyBalance): Unknown error evaluating air energy balance for UUIDs.");
        }
    }
    
    PYHELIOS_API void energyBalanceOptionalOutputPrimitiveData(EnergyBalanceModel* energy_model, const char* label) {
        try {
            clearError();
            if (!energy_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "EnergyBalanceModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }

            energy_model->optionalOutputPrimitiveData(label);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (EnergyBalanceModel::optionalOutputPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (EnergyBalanceModel::optionalOutputPrimitiveData): Unknown error adding optional output data.");
        }
    }
    
    PYHELIOS_API void printDefaultValueReport(EnergyBalanceModel* energy_model) {
        try {
            clearError();
            if (!energy_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "EnergyBalanceModel pointer is null");
                return;
            }
            
            energy_model->printDefaultValueReport();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (EnergyBalanceModel::printDefaultValueReport): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (EnergyBalanceModel::printDefaultValueReport): Unknown error printing default value report.");
        }
    }
    
    PYHELIOS_API void printDefaultValueReportForUUIDs(EnergyBalanceModel* energy_model, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!energy_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "EnergyBalanceModel pointer is null");
                return;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null");
                return;
            }
            if (uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUID count must be greater than 0");
                return;
            }
            
            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            energy_model->printDefaultValueReport(uuid_vector);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (EnergyBalanceModel::printDefaultValueReport): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (EnergyBalanceModel::printDefaultValueReport): Unknown error printing default value report for UUIDs.");
        }
    }

    //=============================================================================
    // GPU Acceleration Control (Only available when compiled with CUDA)
    //=============================================================================

    PYHELIOS_API void enableGPUAcceleration(EnergyBalanceModel* energy_model) {
        try {
            clearError();
            if (!energy_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "EnergyBalanceModel pointer is null");
                return;
            }

#ifdef HELIOS_CUDA_AVAILABLE
            energy_model->enableGPUAcceleration();
#else
            setError(PYHELIOS_ERROR_RUNTIME, "GPU acceleration not available - library not compiled with CUDA support");
#endif

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (EnergyBalanceModel::enableGPUAcceleration): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (EnergyBalanceModel::enableGPUAcceleration): Unknown error enabling GPU acceleration.");
        }
    }

    PYHELIOS_API void disableGPUAcceleration(EnergyBalanceModel* energy_model) {
        try {
            clearError();
            if (!energy_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "EnergyBalanceModel pointer is null");
                return;
            }

#ifdef HELIOS_CUDA_AVAILABLE
            energy_model->disableGPUAcceleration();
#else
            // No-op if CUDA not available - already running in CPU mode
#endif

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (EnergyBalanceModel::disableGPUAcceleration): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (EnergyBalanceModel::disableGPUAcceleration): Unknown error disabling GPU acceleration.");
        }
    }

    PYHELIOS_API int isGPUAccelerationEnabled(EnergyBalanceModel* energy_model) {
        try {
            clearError();
            if (!energy_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "EnergyBalanceModel pointer is null");
                return -1;
            }

#ifdef HELIOS_CUDA_AVAILABLE
            return energy_model->isGPUAccelerationEnabled() ? 1 : 0;
#else
            return 0;  // GPU acceleration never enabled without CUDA
#endif

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (EnergyBalanceModel::isGPUAccelerationEnabled): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (EnergyBalanceModel::isGPUAccelerationEnabled): Unknown error checking GPU acceleration status.");
            return -1;
        }
    }

} //extern "C"

#endif //ENERGYBALANCE_PLUGIN_AVAILABLE
