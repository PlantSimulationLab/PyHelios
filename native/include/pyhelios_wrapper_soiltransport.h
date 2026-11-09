// PyHelios C Interface - SoilTransport Header
// Provides variably saturated soil water transport (Richards equation) with root water uptake

#ifndef PYHELIOS_WRAPPER_SOILTRANSPORT_H
#define PYHELIOS_WRAPPER_SOILTRANSPORT_H

#ifdef SOILTRANSPORT_PLUGIN_AVAILABLE

#include "pyhelios_wrapper_common.h"
#include "Context.h"
#include "SoilTransportModel.h"

// Plain-data mirrors of the plugin's parameter structs. Field order must match the ctypes
// Structures in pyhelios/wrappers/USoilTransportWrapper.py. Booleans and enums travel as int.

// Mirror of SoilProperties (SoilUtils.h). model is a SoilModel value.
typedef struct {
    float theta_r;
    float theta_s;
    float alpha;
    float n;
    float K_s;
    int model;
    float h_e;
    float kr_spline_start;
} PyHeliosSoilProperties;

// Mirror of SolverParameters (SoilUtils.h), without its deprecated fields.
// K_weighting is a KWeighting value, nonlinear_method a NonlinearMethod value.
typedef struct {
    unsigned int max_picard_iterations;
    int enable_gravity;
    int substep_on_failure;
    float picard_tolerance;
    float dt_min;
    float dt_max;
    unsigned int horizontal_coupling_interval;
    float C_regularization;
    float K_min;
    float picard_omega;
    int K_weighting;
    int anderson_depth;
    int nonlinear_method;
    int num_threads;
    int bdf2;
    int adaptive_dt;
    float dt_target_rel_change;
    float dt_safety;
    float dt_growth_max;
    float dt_reduction_min;
    float dt_failure_factor;
} PyHeliosSoilSolverParameters;

// Mirror of RootDistributionParams (RootSoilCoupling.h).
typedef struct {
    float plant_x;
    float plant_y;
    float plant_z;
    float z_max;
    float r_max;
    float z_star;
    float r_star;
    float pz;
    float pr;
    float total_root_length;
} PyHeliosRootDistributionParams;

// Mirror of WeibullRootParameters (RootSoilCoupling.h).
typedef struct {
    float plant_x;
    float plant_y;
    float z_max;
    float shape_z;
    float scale_z;
    int radial;
    float r_max;
    float shape_r;
    float scale_r;
    float total_root_length;
} PyHeliosWeibullRootParameters;

#ifdef __cplusplus
extern "C" {
#endif

// Model management
PYHELIOS_API SoilTransportModel* createSoilTransportModel(helios::Context* context);
PYHELIOS_API void destroySoilTransportModel(SoilTransportModel* model);

// Domain setup. Vectors are float[3] (x, y, z).
PYHELIOS_API void soilTransportDefineSoilDomain(SoilTransportModel* model, const float* origin, const float* extent);
PYHELIOS_API void soilTransportSetGridResolution(SoilTransportModel* model, unsigned int nx, unsigned int ny, unsigned int nz);
PYHELIOS_API void soilTransportSetColumnResolution(SoilTransportModel* model, unsigned int nz);
PYHELIOS_API void soilTransportSetColumnGrid(SoilTransportModel* model, unsigned int nx, unsigned int ny);
PYHELIOS_API void soilTransportInitializeDomain(SoilTransportModel* model);

// Soil properties
PYHELIOS_API void soilTransportSetSoilProperties(SoilTransportModel* model, const PyHeliosSoilProperties* props);
PYHELIOS_API void soilTransportSetSoilPropertiesColumn(SoilTransportModel* model, unsigned int i, unsigned int j, const PyHeliosSoilProperties* props);
PYHELIOS_API void soilTransportSetSoilPropertiesFromTexture(SoilTransportModel* model, const char* texture);
PYHELIOS_API void soilTransportSetSoilPropertiesFromTextureModel(SoilTransportModel* model, const char* texture, int soil_model, int match_standard_curves);

// Initial and boundary conditions
PYHELIOS_API void soilTransportSetInitialCondition(SoilTransportModel* model, float h_init);
PYHELIOS_API void soilTransportSetInitialConditionHydrostatic(SoilTransportModel* model, float water_table_depth);
PYHELIOS_API void soilTransportSetTopBoundaryFlux(SoilTransportModel* model, float flux);
PYHELIOS_API float soilTransportSetSurfaceEvaporation(SoilTransportModel* model, float potential_rate, float aerodynamic_resistance);
PYHELIOS_API void soilTransportSetTopBoundaryPressure(SoilTransportModel* model, float h);
PYHELIOS_API void soilTransportSetBottomBoundaryFreeDrainage(SoilTransportModel* model);
PYHELIOS_API void soilTransportSetBottomBoundaryPressure(SoilTransportModel* model, float h);
PYHELIOS_API void soilTransportSetBottomBoundaryFlux(SoilTransportModel* model, float flux);
PYHELIOS_API void soilTransportAddSurfaceEmitter(SoilTransportModel* model, float x, float y, float flow_rate, float radius);
PYHELIOS_API void soilTransportClearSurfaceEmitters(SoilTransportModel* model);

// Root coupling
PYHELIOS_API void soilTransportEnableRootUptake(SoilTransportModel* model);
PYHELIOS_API void soilTransportSetRootDistribution(SoilTransportModel* model, unsigned int plant_id, const PyHeliosRootDistributionParams* params);
PYHELIOS_API void soilTransportSetRootDistributionWeibull(SoilTransportModel* model, unsigned int plant_id, const PyHeliosWeibullRootParameters* params);
PYHELIOS_API void soilTransportSetRootRadialConductivity(SoilTransportModel* model, float L_r);
PYHELIOS_API void soilTransportSetRootWaterStressParameters(SoilTransportModel* model, float h_onset, float h_wilting, float omega_c);
PYHELIOS_API void soilTransportSetTranspiration(SoilTransportModel* model, unsigned int plant_id, float transpiration);

// Solver configuration. solver_type is a SolverType value.
PYHELIOS_API void soilTransportSetSolverType(SoilTransportModel* model, int solver_type);
PYHELIOS_API void soilTransportEnableHorizontalCoupling(SoilTransportModel* model, unsigned int interval);
PYHELIOS_API void soilTransportSetSolverParameters(SoilTransportModel* model, const PyHeliosSoilSolverParameters* params);
PYHELIOS_API void soilTransportEnableGPU(SoilTransportModel* model);
PYHELIOS_API void soilTransportDisableGPU(SoilTransportModel* model);
PYHELIOS_API int soilTransportIsGPUEnabled(SoilTransportModel* model);
PYHELIOS_API int soilTransportIsGPUAvailable();

// Run simulation
PYHELIOS_API void runSoilTransportModel(SoilTransportModel* model, float dt);

// Output for coupling
PYHELIOS_API float soilTransportGetSoilWaterPotential(SoilTransportModel* model, unsigned int plant_id);
PYHELIOS_API float soilTransportGetWaterContent(SoilTransportModel* model, const float* position);
PYHELIOS_API float soilTransportGetPressureHead(SoilTransportModel* model, const float* position);

// Point sensors. quantity is a SoilMeasurement value.
PYHELIOS_API unsigned int soilTransportAddSensor(SoilTransportModel* model, const float* position, int quantity);
PYHELIOS_API void soilTransportRecordSensors(SoilTransportModel* model);
PYHELIOS_API unsigned int soilTransportGetSensorCount(SoilTransportModel* model);
PYHELIOS_API float* soilTransportGetSensorData(SoilTransportModel* model, unsigned int sensor_id, unsigned int* count);
PYHELIOS_API float* soilTransportGetSensorTimes(SoilTransportModel* model, unsigned int sensor_id, unsigned int* count);
PYHELIOS_API void soilTransportGetSensorPosition(SoilTransportModel* model, unsigned int sensor_id, float* position);
PYHELIOS_API int soilTransportGetSensorQuantity(SoilTransportModel* model, unsigned int sensor_id);
PYHELIOS_API void soilTransportClearSensorData(SoilTransportModel* model);
PYHELIOS_API void soilTransportWriteSensorData(SoilTransportModel* model, const char* filename);

// Solver diagnostics and mass balance
PYHELIOS_API unsigned int soilTransportGetLastSubstepCount(SoilTransportModel* model);
PYHELIOS_API void soilTransportResetSolverStats(SoilTransportModel* model);
PYHELIOS_API unsigned long long soilTransportSolverPicardOuter(SoilTransportModel* model);
PYHELIOS_API unsigned long long soilTransportSolverNewtonOuter(SoilTransportModel* model);
PYHELIOS_API unsigned long long soilTransportSolverPicardGmres(SoilTransportModel* model);
PYHELIOS_API unsigned long long soilTransportSolverNewtonGmres(SoilTransportModel* model);
PYHELIOS_API float soilTransportGetTimestep(SoilTransportModel* model);
PYHELIOS_API unsigned long long soilTransportGetSolverIterationCount(SoilTransportModel* model);
PYHELIOS_API void soilTransportResetSolverIterationCount(SoilTransportModel* model);
PYHELIOS_API double soilTransportGetTotalWaterStorage(SoilTransportModel* model);
PYHELIOS_API double soilTransportGetCumulativeBoundaryInflux(SoilTransportModel* model);
PYHELIOS_API double soilTransportGetMassBalanceResidual(SoilTransportModel* model);
PYHELIOS_API void soilTransportResetMassBalance(SoilTransportModel* model);
PYHELIOS_API float soilTransportGetCumulativeRootUptake(SoilTransportModel* model, unsigned int plant_id);
PYHELIOS_API float soilTransportGetRootUptakeFlux(SoilTransportModel* model, unsigned int plant_id);

// Visualization. mode is a SoilColorMode value, region a SoilRegion value.
PYHELIOS_API unsigned int* soilTransportAddSoilVisualization(SoilTransportModel* model, int mode, unsigned int* count);
PYHELIOS_API unsigned int* soilTransportAddSoilVisualizationKeepFraction(SoilTransportModel* model, int mode, const float* keep_fraction, unsigned int* count);
PYHELIOS_API unsigned int* soilTransportAddSoilVisualizationRegion(SoilTransportModel* model, int mode, const float* fraction_min, const float* fraction_max, int region, unsigned int* count);
PYHELIOS_API void soilTransportUpdateSoilVisualization(SoilTransportModel* model, const unsigned int* uuids, unsigned int uuid_count, int mode);

// Message control
PYHELIOS_API void soilTransportEnableMessages(SoilTransportModel* model);
PYHELIOS_API void soilTransportDisableMessages(SoilTransportModel* model);

// Soil property library (free functions; no model needed)
PYHELIOS_API void soilTransportGetSoilPropertiesFromTexture(const char* texture, PyHeliosSoilProperties* out);
PYHELIOS_API void soilTransportGetSoilPropertiesFromTextureModel(const char* texture, int soil_model, int match_standard_curves, PyHeliosSoilProperties* out);
PYHELIOS_API void soilTransportToModifiedVanGenuchten(const PyHeliosSoilProperties* vg, float h_e, int match_standard_curves, PyHeliosSoilProperties* out);
// Returns the texture names joined by '\n'; valid until the next call on this thread.
PYHELIOS_API const char* soilTransportGetAvailableSoilTextures();
PYHELIOS_API int soilTransportIsSoilTextureAvailable(const char* texture);

#ifdef __cplusplus
}
#endif

#endif // SOILTRANSPORT_PLUGIN_AVAILABLE

#endif // PYHELIOS_WRAPPER_SOILTRANSPORT_H
