// PyHelios C Interface - PlantHydraulics Header
// Provides plant hydraulics modeling of soil, root, stem and leaf water potentials

#ifndef PYHELIOS_WRAPPER_PLANTHYDRAULICS_H
#define PYHELIOS_WRAPPER_PLANTHYDRAULICS_H

#ifdef PLANTHYDRAULICS_PLUGIN_AVAILABLE

#include "pyhelios_wrapper_common.h"
#include "Context.h"
#include "PlantHydraulicsModel.h"

// Number of floats in a hydraulic conductance block: [saturated_conductance, potential_at_half_saturated, sensitivity, temperature_dependence]
#define PYHELIOS_PLANTHYDRAULICS_CONDUCTANCE_SIZE 4
// Number of floats in a full hydraulic capacitance block: [osmotic_potential_at_full_turgor, relative_water_content_at_turgor_loss, cell_wall_elasticity_exponent, saturated_specific_water_content, fixed_constant_capacitance]
#define PYHELIOS_PLANTHYDRAULICS_CAPACITANCE_SIZE 5
// Number of floats in a model coefficient array:
//   [0-3]   leaf conductance block
//   [4-7]   stem conductance block
//   [8-11]  root conductance block
//   [12-16] leaf capacitance block
//   [17-20] stem capacitance [osmotic_potential_at_full_turgor, relative_water_content_at_turgor_loss, cell_wall_elasticity_exponent, fixed_constant_capacitance]
//   [21-24] root capacitance (same layout as stem)
// A fixed_constant_capacitance greater than zero selects a constant capacitance in place of the pressure-volume curve parameters.
#define PYHELIOS_PLANTHYDRAULICS_COEFFICIENT_SIZE 25

#ifdef __cplusplus
extern "C" {
#endif

// Core model management
PYHELIOS_API PlantHydraulicsModel* createPlantHydraulicsModel(helios::Context* context);
PYHELIOS_API void destroyPlantHydraulicsModel(PlantHydraulicsModel* model);

// Model coefficients. A non-empty leaf_capacitance_species takes the leaf capacitance from the species library in place of the values in the array.
PYHELIOS_API void setPlantHydraulicsModelCoefficients(PlantHydraulicsModel* model, const float* coefficients, unsigned int coeff_count, const char* leaf_capacitance_species);
PYHELIOS_API void setPlantHydraulicsModelCoefficientsForUUIDs(PlantHydraulicsModel* model, const float* coefficients, unsigned int coeff_count, const char* leaf_capacitance_species, const unsigned int* uuids, unsigned int uuid_count);
PYHELIOS_API void setPlantHydraulicsModelCoefficientsFromLibrary(PlantHydraulicsModel* model, const char* species);
PYHELIOS_API void setPlantHydraulicsModelCoefficientsFromLibraryForUUIDs(PlantHydraulicsModel* model, const char* species, const unsigned int* uuids, unsigned int uuid_count);
// Getters fill a caller-allocated array of PYHELIOS_PLANTHYDRAULICS_COEFFICIENT_SIZE floats. Library leaf capacitance is returned as its parameter values.
PYHELIOS_API void getPlantHydraulicsModelCoefficients(PlantHydraulicsModel* model, unsigned int uuid, float* coefficients, unsigned int coeff_count);
PYHELIOS_API void getPlantHydraulicsModelCoefficientsFromLibrary(PlantHydraulicsModel* model, const char* species, float* coefficients, unsigned int coeff_count);

// Core execution methods
PYHELIOS_API void runPlantHydraulicsModel(PlantHydraulicsModel* model, int timespan, int timestep);
PYHELIOS_API void runPlantHydraulicsModelForUUIDs(PlantHydraulicsModel* model, const unsigned int* uuids, unsigned int uuid_count, int timespan, int timestep);

// Optional output primitive data
PYHELIOS_API void setPlantHydraulicsOutputConductancePrimitiveData(PlantHydraulicsModel* model, bool toggle);
PYHELIOS_API void setPlantHydraulicsOutputCapacitancePrimitiveData(PlantHydraulicsModel* model, bool toggle);

// Plant grouping
PYHELIOS_API void groupPlantHydraulicsPrimitivesIntoPlantObject(PlantHydraulicsModel* model, const unsigned int* uuids, unsigned int uuid_count);
PYHELIOS_API int getPlantHydraulicsPlantID(PlantHydraulicsModel* model, unsigned int uuid);
PYHELIOS_API int getPlantHydraulicsPlantIDForUUIDs(PlantHydraulicsModel* model, const unsigned int* uuids, unsigned int uuid_count);
PYHELIOS_API int* getPlantHydraulicsUniquePlantIDs(PlantHydraulicsModel* model, const unsigned int* uuids, unsigned int uuid_count, unsigned int* count);
PYHELIOS_API unsigned int* getPlantHydraulicsPrimitivesByPlantID(PlantHydraulicsModel* model, int plantID, unsigned int* count);
PYHELIOS_API unsigned int* getPlantHydraulicsPrimitivesWithoutPlantID(PlantHydraulicsModel* model, const unsigned int* uuids, unsigned int uuid_count, unsigned int* count);

// Water potentials (MPa)
PYHELIOS_API float getPlantHydraulicsStemWaterPotential(PlantHydraulicsModel* model, unsigned int uuid);
PYHELIOS_API float getPlantHydraulicsStemWaterPotentialForUUIDs(PlantHydraulicsModel* model, const unsigned int* uuids, unsigned int uuid_count);
PYHELIOS_API float getPlantHydraulicsStemWaterPotentialOfPlant(PlantHydraulicsModel* model, unsigned int plantID);
PYHELIOS_API float getPlantHydraulicsRootWaterPotential(PlantHydraulicsModel* model, unsigned int uuid);
PYHELIOS_API float getPlantHydraulicsRootWaterPotentialForUUIDs(PlantHydraulicsModel* model, const unsigned int* uuids, unsigned int uuid_count);
PYHELIOS_API float getPlantHydraulicsRootWaterPotentialOfPlant(PlantHydraulicsModel* model, unsigned int plantID);
PYHELIOS_API float getPlantHydraulicsSoilWaterPotential(PlantHydraulicsModel* model, unsigned int uuid);
PYHELIOS_API float getPlantHydraulicsSoilWaterPotentialForUUIDs(PlantHydraulicsModel* model, const unsigned int* uuids, unsigned int uuid_count);
PYHELIOS_API float getPlantHydraulicsSoilWaterPotentialOfPlant(PlantHydraulicsModel* model, unsigned int plantID);
PYHELIOS_API void setPlantHydraulicsSoilWaterPotentialOfPlant(PlantHydraulicsModel* model, unsigned int plantID, float soil_water_potential);

// Pressure-volume and vulnerability curve functions. Capacitance arrays hold PYHELIOS_PLANTHYDRAULICS_CAPACITANCE_SIZE floats, conductance arrays PYHELIOS_PLANTHYDRAULICS_CONDUCTANCE_SIZE.
PYHELIOS_API float computePlantHydraulicsOsmoticPotential(const float* capacitance, float relative_water_content);
PYHELIOS_API float computePlantHydraulicsTurgorPressure(const float* capacitance, float relative_water_content);
PYHELIOS_API float computePlantHydraulicsWaterPotential(const float* capacitance, float relative_water_content);
PYHELIOS_API float computePlantHydraulicsConductance(const float* conductance, float water_potential, float temperature);
PYHELIOS_API float computePlantHydraulicsCapacitance(const float* capacitance, float relative_water_content);

#ifdef __cplusplus
}
#endif

#endif // PLANTHYDRAULICS_PLUGIN_AVAILABLE

#endif // PYHELIOS_WRAPPER_PLANTHYDRAULICS_H
