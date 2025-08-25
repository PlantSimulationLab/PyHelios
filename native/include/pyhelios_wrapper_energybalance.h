/**
 * @file pyhelios_wrapper_energybalance.h
 * @brief EnergyBalanceModel functions for PyHelios C wrapper
 * 
 * This header provides energy balance modeling capabilities including
 * surface temperature calculations, air energy balance, and thermal modeling.
 */

#ifndef PYHELIOS_WRAPPER_ENERGYBALANCE_H
#define PYHELIOS_WRAPPER_ENERGYBALANCE_H

#include "pyhelios_wrapper_common.h"

// Forward declarations for EnergyBalanceModel interface
class EnergyBalanceModel;
namespace helios {
    class Context;
}

#ifdef __cplusplus
extern "C" {
#endif

//=============================================================================
// EnergyBalanceModel Functions
//=============================================================================

/**
 * @brief Create a new EnergyBalanceModel
 * @param context Pointer to the Helios context
 * @return Pointer to the created EnergyBalanceModel, or nullptr on error
 */
PYHELIOS_API EnergyBalanceModel* createEnergyBalanceModel(helios::Context* context);

/**
 * @brief Destroy an EnergyBalanceModel
 * @param energy_model Pointer to the EnergyBalanceModel to destroy
 */
PYHELIOS_API void destroyEnergyBalanceModel(EnergyBalanceModel* energy_model);

/**
 * @brief Enable EnergyBalanceModel status messages
 * @param energy_model Pointer to the EnergyBalanceModel
 */
PYHELIOS_API void enableEnergyBalanceMessages(EnergyBalanceModel* energy_model);

/**
 * @brief Disable EnergyBalanceModel status messages
 * @param energy_model Pointer to the EnergyBalanceModel
 */
PYHELIOS_API void disableEnergyBalanceMessages(EnergyBalanceModel* energy_model);

/**
 * @brief Run energy balance model for all primitives (steady state)
 * @param energy_model Pointer to the EnergyBalanceModel
 */
PYHELIOS_API void runEnergyBalance(EnergyBalanceModel* energy_model);

/**
 * @brief Run energy balance model for all primitives (dynamic with timestep)
 * @param energy_model Pointer to the EnergyBalanceModel
 * @param dt Time step in seconds
 */
PYHELIOS_API void runEnergyBalanceDynamic(EnergyBalanceModel* energy_model, float dt);

/**
 * @brief Run energy balance model for specific primitives (steady state)
 * @param energy_model Pointer to the EnergyBalanceModel
 * @param uuids Array of primitive UUIDs
 * @param uuid_count Number of UUIDs in the array
 */
PYHELIOS_API void runEnergyBalanceForUUIDs(EnergyBalanceModel* energy_model, const unsigned int* uuids, unsigned int uuid_count);

/**
 * @brief Run energy balance model for specific primitives (dynamic with timestep)
 * @param energy_model Pointer to the EnergyBalanceModel
 * @param uuids Array of primitive UUIDs
 * @param uuid_count Number of UUIDs in the array
 * @param dt Time step in seconds
 */
PYHELIOS_API void runEnergyBalanceForUUIDsDynamic(EnergyBalanceModel* energy_model, const unsigned int* uuids, unsigned int uuid_count, float dt);

/**
 * @brief Add a radiation band for absorbed flux calculations
 * @param energy_model Pointer to the EnergyBalanceModel
 * @param band Name of the radiation band (e.g., "SW", "PAR", "NIR")
 */
PYHELIOS_API void addEnergyBalanceRadiationBand(EnergyBalanceModel* energy_model, const char* band);

/**
 * @brief Add multiple radiation bands for absorbed flux calculations
 * @param energy_model Pointer to the EnergyBalanceModel
 * @param bands Array of radiation band names
 * @param band_count Number of bands in the array
 */
PYHELIOS_API void addEnergyBalanceRadiationBands(EnergyBalanceModel* energy_model, const char* const* bands, unsigned int band_count);

/**
 * @brief Enable air energy balance with automatic canopy height detection
 * @param energy_model Pointer to the EnergyBalanceModel
 */
PYHELIOS_API void enableAirEnergyBalance(EnergyBalanceModel* energy_model);

/**
 * @brief Enable air energy balance with specified parameters
 * @param energy_model Pointer to the EnergyBalanceModel
 * @param canopy_height_m Height of the canopy in meters
 * @param reference_height_m Height at which ambient conditions are measured in meters
 */
PYHELIOS_API void enableAirEnergyBalanceWithParameters(EnergyBalanceModel* energy_model, float canopy_height_m, float reference_height_m);

/**
 * @brief Advance air energy balance over time for all primitives
 * @param energy_model Pointer to the EnergyBalanceModel
 * @param dt_sec Time step in seconds
 * @param time_advance_sec Total time to advance the model in seconds
 */
PYHELIOS_API void evaluateAirEnergyBalance(EnergyBalanceModel* energy_model, float dt_sec, float time_advance_sec);

/**
 * @brief Advance air energy balance over time for specific primitives
 * @param energy_model Pointer to the EnergyBalanceModel
 * @param uuids Array of primitive UUIDs
 * @param uuid_count Number of UUIDs in the array
 * @param dt_sec Time step in seconds
 * @param time_advance_sec Total time to advance the model in seconds
 */
PYHELIOS_API void evaluateAirEnergyBalanceForUUIDs(EnergyBalanceModel* energy_model, const unsigned int* uuids, unsigned int uuid_count, float dt_sec, float time_advance_sec);

/**
 * @brief Add optional output primitive data
 * @param energy_model Pointer to the EnergyBalanceModel
 * @param label Name of the primitive data to add (e.g., "vapor_pressure_deficit")
 */
PYHELIOS_API void optionalOutputPrimitiveData(EnergyBalanceModel* energy_model, const char* label);

/**
 * @brief Print default value report for all primitives
 * @param energy_model Pointer to the EnergyBalanceModel
 */
PYHELIOS_API void printDefaultValueReport(EnergyBalanceModel* energy_model);

/**
 * @brief Print default value report for specific primitives
 * @param energy_model Pointer to the EnergyBalanceModel
 * @param uuids Array of primitive UUIDs
 * @param uuid_count Number of UUIDs in the array
 */
PYHELIOS_API void printDefaultValueReportForUUIDs(EnergyBalanceModel* energy_model, const unsigned int* uuids, unsigned int uuid_count);

#ifdef __cplusplus
}
#endif

#endif // PYHELIOS_WRAPPER_ENERGYBALANCE_H