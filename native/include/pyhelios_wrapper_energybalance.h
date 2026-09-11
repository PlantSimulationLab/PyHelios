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
 * @brief Enable the canopy airspace model
 *
 * Resolves within-canopy air temperature and humidity from a vertically layered
 * resistance network instead of holding them at a prescribed value. Mutually
 * exclusive with the air energy balance model, and incompatible with the dynamic
 * forms of run() that take a timestep.
 *
 * @param energy_model Pointer to the EnergyBalanceModel
 * @param canopy_uuids Array of canopy (leaf) primitive UUIDs
 * @param canopy_count Number of canopy UUIDs
 * @param ground_uuids Array of ground primitive UUIDs (may be null when ground_count is 0)
 * @param ground_count Number of ground UUIDs
 * @param canopy_height_m Height of the canopy in meters
 * @param reference_height_m Height at which above-canopy conditions are measured, must exceed canopy height
 * @param leaf_area_index One-sided leaf area index on a ground-area basis
 * @param num_layers Number of vertical airspace layers of equal leaf area index
 */
PYHELIOS_API void enableCanopyAirspaceModel(EnergyBalanceModel* energy_model, const unsigned int* canopy_uuids, unsigned int canopy_count, const unsigned int* ground_uuids, unsigned int ground_count, float canopy_height_m, float reference_height_m, float leaf_area_index, unsigned int num_layers);

/**
 * @brief Disable the canopy airspace model
 * @param energy_model Pointer to the EnergyBalanceModel
 */
PYHELIOS_API void disableCanopyAirspaceModel(EnergyBalanceModel* energy_model);

/**
 * @brief Set convergence criteria for the canopy airspace iteration
 * @param energy_model Pointer to the EnergyBalanceModel
 * @param tolerance_K Temperature convergence tolerance in Kelvin (default 0.01)
 * @param max_iterations Maximum number of coupled iterations (default 50)
 */
PYHELIOS_API void setCanopyAirspaceConvergence(EnergyBalanceModel* energy_model, float tolerance_K, unsigned int max_iterations);

/**
 * @brief Add optional output primitive data
 * @param energy_model Pointer to the EnergyBalanceModel
 * @param label Name of the primitive data to add (e.g., "vapor_pressure_deficit")
 */
PYHELIOS_API void energyBalanceOptionalOutputPrimitiveData(EnergyBalanceModel* energy_model, const char* label);

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

//=============================================================================
// GPU Acceleration Control (Only available when compiled with CUDA)
//=============================================================================

/**
 * @brief Enable GPU acceleration for energy balance calculations
 * @param energy_model Pointer to the EnergyBalanceModel
 * @note Only available when compiled with CUDA support
 */
PYHELIOS_API void enableGPUAcceleration(EnergyBalanceModel* energy_model);

/**
 * @brief Disable GPU acceleration and force CPU mode
 * @param energy_model Pointer to the EnergyBalanceModel
 * @note Only available when compiled with CUDA support
 */
PYHELIOS_API void disableGPUAcceleration(EnergyBalanceModel* energy_model);

/**
 * @brief Check if GPU acceleration is currently enabled
 * @param energy_model Pointer to the EnergyBalanceModel
 * @return 1 if GPU acceleration is enabled, 0 if not, -1 on error
 * @note Only available when compiled with CUDA support
 */
PYHELIOS_API int isGPUAccelerationEnabled(EnergyBalanceModel* energy_model);

#ifdef __cplusplus
}
#endif

#endif // PYHELIOS_WRAPPER_ENERGYBALANCE_H