// PyHelios C Interface - StomatalConductance Header
// Provides stomatal conductance modeling and gas exchange functions

#ifndef PYHELIOS_WRAPPER_STOMATALCONDUCTANCE_H
#define PYHELIOS_WRAPPER_STOMATALCONDUCTANCE_H

#ifdef STOMATALCONDUCTANCE_PLUGIN_AVAILABLE

#include "pyhelios_wrapper_common.h"
#include "Context.h"
#include "StomatalConductanceModel.h"

#ifdef __cplusplus
extern "C" {
#endif

// Core model management
PYHELIOS_API StomatalConductanceModel* createStomatalConductanceModel(helios::Context* context);
PYHELIOS_API void destroyStomatalConductanceModel(StomatalConductanceModel* model);

// Message control
PYHELIOS_API void enableStomatalConductanceMessages(StomatalConductanceModel* model);
PYHELIOS_API void disableStomatalConductanceMessages(StomatalConductanceModel* model);

// Core execution methods
PYHELIOS_API void runStomatalConductanceModel(StomatalConductanceModel* model);
PYHELIOS_API void runStomatalConductanceModelDynamic(StomatalConductanceModel* model, float dt);
PYHELIOS_API void runStomatalConductanceModelForUUIDs(StomatalConductanceModel* model, const unsigned int* uuids, unsigned int uuid_count);
PYHELIOS_API void runStomatalConductanceModelForUUIDsDynamic(StomatalConductanceModel* model, const unsigned int* uuids, unsigned int uuid_count, float dt);

// BWB Model Coefficient Functions
PYHELIOS_API void setStomatalConductanceBWBCoefficients(StomatalConductanceModel* model, float gs0, float a1);
PYHELIOS_API void setStomatalConductanceBWBCoefficientsForUUIDs(StomatalConductanceModel* model, float gs0, float a1, const unsigned int* uuids, unsigned int uuid_count);

// BBL Model Coefficient Functions
PYHELIOS_API void setStomatalConductanceBBLCoefficients(StomatalConductanceModel* model, float gs0, float a1, float D0);
PYHELIOS_API void setStomatalConductanceBBLCoefficientsForUUIDs(StomatalConductanceModel* model, float gs0, float a1, float D0, const unsigned int* uuids, unsigned int uuid_count);

// MOPT Model Coefficient Functions
PYHELIOS_API void setStomatalConductanceMOPTCoefficients(StomatalConductanceModel* model, float gs0, float g1);
PYHELIOS_API void setStomatalConductanceMOPTCoefficientsForUUIDs(StomatalConductanceModel* model, float gs0, float g1, const unsigned int* uuids, unsigned int uuid_count);

// BMF Model Coefficient Functions
PYHELIOS_API void setStomatalConductanceBMFCoefficients(StomatalConductanceModel* model, float Em, float i0, float k, float b);
PYHELIOS_API void setStomatalConductanceBMFCoefficientsForUUIDs(StomatalConductanceModel* model, float Em, float i0, float k, float b, const unsigned int* uuids, unsigned int uuid_count);

// BB Model Coefficient Functions
PYHELIOS_API void setStomatalConductanceBBCoefficients(StomatalConductanceModel* model, float pi_0, float pi_m, float theta, float sigma, float chi);
PYHELIOS_API void setStomatalConductanceBBCoefficientsForUUIDs(StomatalConductanceModel* model, float pi_0, float pi_m, float theta, float sigma, float chi, const unsigned int* uuids, unsigned int uuid_count);

// Species Library Functions
PYHELIOS_API void setStomatalConductanceBMFCoefficientsFromLibrary(StomatalConductanceModel* model, const char* species);
PYHELIOS_API void setStomatalConductanceBMFCoefficientsFromLibraryForUUIDs(StomatalConductanceModel* model, const char* species, const unsigned int* uuids, unsigned int uuid_count);

// Material-label coefficient assignment (stored as material data; resolved per primitive at run time)
PYHELIOS_API void setStomatalConductanceBWBCoefficientsForMaterial(StomatalConductanceModel* model, const char* material_label, float gs0, float a1);
PYHELIOS_API void setStomatalConductanceBBLCoefficientsForMaterial(StomatalConductanceModel* model, const char* material_label, float gs0, float a1, float D0);
PYHELIOS_API void setStomatalConductanceMOPTCoefficientsForMaterial(StomatalConductanceModel* model, const char* material_label, float gs0, float g1);
PYHELIOS_API void setStomatalConductanceBMFCoefficientsForMaterial(StomatalConductanceModel* model, const char* material_label, float Em, float i0, float k, float b);
PYHELIOS_API void setStomatalConductanceBBCoefficientsForMaterial(StomatalConductanceModel* model, const char* material_label, float pi_0, float pi_m, float theta, float sigma, float chi);
PYHELIOS_API void setStomatalConductanceBMFCoefficientsFromLibraryForMaterial(StomatalConductanceModel* model, const char* species, const char* material_label);

// Per-UUID BMF coefficient sets: coeffs is a flat array of 4*uuid_count floats laid out [Em, i0, k, b] per UUID
PYHELIOS_API void setStomatalConductanceBMFCoefficientsPerUUID(StomatalConductanceModel* model, const float* coeffs, const unsigned int* uuids, unsigned int uuid_count);

// Species library lookup: writes [Em, i0, k, b] into coeffs_out (must hold 4 floats)
PYHELIOS_API void getStomatalConductanceBMFCoefficientsFromLibrary(StomatalConductanceModel* model, const char* species, float* coeffs_out);

// Dynamic Time Constants
PYHELIOS_API void setStomatalConductanceDynamicTimeConstants(StomatalConductanceModel* model, float tau_open, float tau_close);
PYHELIOS_API void setStomatalConductanceDynamicTimeConstantsForUUIDs(StomatalConductanceModel* model, float tau_open, float tau_close, const unsigned int* uuids, unsigned int uuid_count);

// Utility Functions
PYHELIOS_API void addStomatalConductanceOptionalOutput(StomatalConductanceModel* model, const char* label);
PYHELIOS_API void printStomatalConductanceDefaultValueReport(StomatalConductanceModel* model);
PYHELIOS_API void printStomatalConductanceDefaultValueReportForUUIDs(StomatalConductanceModel* model, const unsigned int* uuids, unsigned int uuid_count);

#ifdef __cplusplus
}
#endif

#endif // STOMATALCONDUCTANCE_PLUGIN_AVAILABLE

#endif // PYHELIOS_WRAPPER_STOMATALCONDUCTANCE_H