// PyHelios C Interface - SoilTransport Functions
// Provides variably saturated soil water transport (Richards equation) with root water uptake

#include "../include/pyhelios_wrapper_common.h"
#include "../include/pyhelios_wrapper_context.h"
#include "Context.h"
#include <string>
#include <exception>
#include <stdexcept>
#include <vector>

#ifdef SOILTRANSPORT_PLUGIN_AVAILABLE
#include "../include/pyhelios_wrapper_soiltransport.h"
#include "SoilTransportModel.h"

namespace {

    // Runs body with the PyHelios error protocol: clears the error state, and translates any
    // exception into an error code and message so that no C++ exception crosses into Python.
    // Argument problems detected here throw std::invalid_argument; errors raised by the plugin
    // (helios_runtime_error) are std::runtime_error and already name the C++ method.
    template<typename R, typename F>
    R guarded(const char* function, R failure_value, F&& body) {
        try {
            clearError();
            return body();
        } catch (const std::invalid_argument& e) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, std::string("ERROR (") + function + "): " + e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, std::string("ERROR (") + function + "): Unknown error.");
        }
        return failure_value;
    }

    template<typename F>
    void guardedVoid(const char* function, F&& body) {
        guarded<int>(function, 0, [&]() {
            body();
            return 0;
        });
    }

    SoilTransportModel* requireModel(SoilTransportModel* model) {
        if (!model) {
            throw std::invalid_argument("SoilTransportModel pointer is null");
        }
        return model;
    }

    template<typename T>
    const T* requirePointer(const T* ptr, const char* name) {
        if (!ptr) {
            throw std::invalid_argument(std::string(name) + " pointer is null");
        }
        return ptr;
    }

    helios::vec3 toVec3(const float* v, const char* name) {
        requirePointer(v, name);
        return helios::make_vec3(v[0], v[1], v[2]);
    }

    std::string toString(const char* s, const char* name) {
        requirePointer(s, name);
        return std::string(s);
    }

    int checkEnum(int value, int min_value, int max_value, const char* name) {
        if (value < min_value || value > max_value) {
            throw std::invalid_argument(std::string("invalid ") + name + " value " + std::to_string(value));
        }
        return value;
    }

    SoilModel toSoilModel(int v) {
        return static_cast<SoilModel>(checkEnum(v, static_cast<int>(SoilModel::VAN_GENUCHTEN), static_cast<int>(SoilModel::LINEAR), "SoilModel"));
    }

    SoilColorMode toColorMode(int v) {
        return static_cast<SoilColorMode>(checkEnum(v, static_cast<int>(SoilColorMode::WATER_CONTENT), static_cast<int>(SoilColorMode::TEXTURE), "SoilColorMode"));
    }

    SoilProperties fromC(const PyHeliosSoilProperties* p) {
        requirePointer(p, "SoilProperties");
        SoilProperties props(p->theta_r, p->theta_s, p->alpha, p->n, p->K_s);
        props.model = toSoilModel(p->model);
        props.h_e = p->h_e;
        props.kr_spline_start = p->kr_spline_start;
        return props;
    }

    void toC(const SoilProperties& props, PyHeliosSoilProperties* out) {
        requirePointer(out, "output SoilProperties");
        out->theta_r = props.theta_r;
        out->theta_s = props.theta_s;
        out->alpha = props.alpha;
        out->n = props.n;
        out->K_s = props.K_s;
        out->model = static_cast<int>(props.model);
        out->h_e = props.h_e;
        out->kr_spline_start = props.kr_spline_start;
    }

    SolverParameters fromC(const PyHeliosSoilSolverParameters* p) {
        requirePointer(p, "SolverParameters");
        SolverParameters params; // deprecated fields keep their defaults
        params.max_picard_iterations = p->max_picard_iterations;
        params.enable_gravity = p->enable_gravity != 0;
        params.substep_on_failure = p->substep_on_failure != 0;
        params.picard_tolerance = p->picard_tolerance;
        params.dt_min = p->dt_min;
        params.dt_max = p->dt_max;
        params.horizontal_coupling_interval = p->horizontal_coupling_interval;
        params.C_regularization = p->C_regularization;
        params.K_min = p->K_min;
        params.picard_omega = p->picard_omega;
        params.K_weighting = static_cast<KWeighting>(checkEnum(p->K_weighting, static_cast<int>(KWeighting::DEFAULT), static_cast<int>(KWeighting::UPSTREAM_KR), "KWeighting"));
        params.anderson_depth = p->anderson_depth;
        params.nonlinear_method = static_cast<NonlinearMethod>(checkEnum(p->nonlinear_method, static_cast<int>(NonlinearMethod::PICARD), static_cast<int>(NonlinearMethod::NEWTON_ANALYTIC), "NonlinearMethod"));
        params.num_threads = p->num_threads;
        params.bdf2 = p->bdf2 != 0;
        params.adaptive_dt = p->adaptive_dt != 0;
        params.dt_target_rel_change = p->dt_target_rel_change;
        params.dt_safety = p->dt_safety;
        params.dt_growth_max = p->dt_growth_max;
        params.dt_reduction_min = p->dt_reduction_min;
        params.dt_failure_factor = p->dt_failure_factor;
        return params;
    }

    RootDistributionParams fromC(const PyHeliosRootDistributionParams* p) {
        requirePointer(p, "RootDistributionParams");
        RootDistributionParams params;
        params.plant_x = p->plant_x;
        params.plant_y = p->plant_y;
        params.plant_z = p->plant_z;
        params.z_max = p->z_max;
        params.r_max = p->r_max;
        params.z_star = p->z_star;
        params.r_star = p->r_star;
        params.pz = p->pz;
        params.pr = p->pr;
        params.total_root_length = p->total_root_length;
        return params;
    }

    WeibullRootParameters fromC(const PyHeliosWeibullRootParameters* p) {
        requirePointer(p, "WeibullRootParameters");
        WeibullRootParameters params;
        params.plant_x = p->plant_x;
        params.plant_y = p->plant_y;
        params.z_max = p->z_max;
        params.shape_z = p->shape_z;
        params.scale_z = p->scale_z;
        params.radial = p->radial != 0;
        params.r_max = p->r_max;
        params.shape_r = p->shape_r;
        params.scale_r = p->scale_r;
        params.total_root_length = p->total_root_length;
        return params;
    }

    template<typename T>
    T* returnVector(const std::vector<T>& values, unsigned int* count) {
        static thread_local std::vector<T> static_result;
        static_result = values;
        *count = static_cast<unsigned int>(static_result.size());
        return static_result.empty() ? nullptr : static_result.data();
    }

    unsigned int* requireCount(unsigned int* count) {
        if (!count) {
            throw std::invalid_argument("count pointer is null");
        }
        *count = 0;
        return count;
    }

} // namespace

extern "C" {

    // ---------------------------------------------------------------- model management

    PYHELIOS_API SoilTransportModel* createSoilTransportModel(helios::Context* context) {
        return guarded<SoilTransportModel*>("createSoilTransportModel", nullptr, [&]() -> SoilTransportModel* {
            if (!context) {
                throw std::invalid_argument("Context pointer is null");
            }
            return new SoilTransportModel(context);
        });
    }

    PYHELIOS_API void destroySoilTransportModel(SoilTransportModel* model) {
        if (model) {
            delete model;
        }
    }

    // ---------------------------------------------------------------- domain setup

    PYHELIOS_API void soilTransportDefineSoilDomain(SoilTransportModel* model, const float* origin, const float* extent) {
        guardedVoid("SoilTransportModel::defineSoilDomain", [&]() { requireModel(model)->defineSoilDomain(toVec3(origin, "origin"), toVec3(extent, "extent")); });
    }

    PYHELIOS_API void soilTransportSetGridResolution(SoilTransportModel* model, unsigned int nx, unsigned int ny, unsigned int nz) {
        guardedVoid("SoilTransportModel::setGridResolution", [&]() { requireModel(model)->setGridResolution(nx, ny, nz); });
    }

    PYHELIOS_API void soilTransportSetColumnResolution(SoilTransportModel* model, unsigned int nz) {
        guardedVoid("SoilTransportModel::setColumnResolution", [&]() { requireModel(model)->setColumnResolution(nz); });
    }

    PYHELIOS_API void soilTransportSetColumnGrid(SoilTransportModel* model, unsigned int nx, unsigned int ny) {
        guardedVoid("SoilTransportModel::setColumnGrid", [&]() { requireModel(model)->setColumnGrid(nx, ny); });
    }

    PYHELIOS_API void soilTransportInitializeDomain(SoilTransportModel* model) {
        guardedVoid("SoilTransportModel::initializeDomain", [&]() { requireModel(model)->initializeDomain(); });
    }

    // ---------------------------------------------------------------- soil properties

    PYHELIOS_API void soilTransportSetSoilProperties(SoilTransportModel* model, const PyHeliosSoilProperties* props) {
        guardedVoid("SoilTransportModel::setSoilProperties", [&]() { requireModel(model)->setSoilProperties(fromC(props)); });
    }

    PYHELIOS_API void soilTransportSetSoilPropertiesColumn(SoilTransportModel* model, unsigned int i, unsigned int j, const PyHeliosSoilProperties* props) {
        guardedVoid("SoilTransportModel::setSoilProperties", [&]() { requireModel(model)->setSoilProperties(i, j, fromC(props)); });
    }

    PYHELIOS_API void soilTransportSetSoilPropertiesFromTexture(SoilTransportModel* model, const char* texture) {
        guardedVoid("SoilTransportModel::setSoilPropertiesFromTexture", [&]() { requireModel(model)->setSoilPropertiesFromTexture(toString(texture, "texture")); });
    }

    PYHELIOS_API void soilTransportSetSoilPropertiesFromTextureModel(SoilTransportModel* model, const char* texture, int soil_model, int match_standard_curves) {
        guardedVoid("SoilTransportModel::setSoilPropertiesFromTexture", [&]() { requireModel(model)->setSoilPropertiesFromTexture(toString(texture, "texture"), toSoilModel(soil_model), match_standard_curves != 0); });
    }

    // ---------------------------------------------------------------- initial and boundary conditions

    PYHELIOS_API void soilTransportSetInitialCondition(SoilTransportModel* model, float h_init) {
        guardedVoid("SoilTransportModel::setInitialCondition", [&]() { requireModel(model)->setInitialCondition(h_init); });
    }

    PYHELIOS_API void soilTransportSetInitialConditionHydrostatic(SoilTransportModel* model, float water_table_depth) {
        guardedVoid("SoilTransportModel::setInitialConditionHydrostatic", [&]() { requireModel(model)->setInitialConditionHydrostatic(water_table_depth); });
    }

    PYHELIOS_API void soilTransportSetTopBoundaryFlux(SoilTransportModel* model, float flux) {
        guardedVoid("SoilTransportModel::setTopBoundaryFlux", [&]() { requireModel(model)->setTopBoundaryFlux(flux); });
    }

    PYHELIOS_API float soilTransportSetSurfaceEvaporation(SoilTransportModel* model, float potential_rate, float aerodynamic_resistance) {
        return guarded<float>("SoilTransportModel::setSurfaceEvaporation", 0.f, [&]() { return requireModel(model)->setSurfaceEvaporation(potential_rate, aerodynamic_resistance); });
    }

    PYHELIOS_API void soilTransportSetTopBoundaryPressure(SoilTransportModel* model, float h) {
        guardedVoid("SoilTransportModel::setTopBoundaryPressure", [&]() { requireModel(model)->setTopBoundaryPressure(h); });
    }

    PYHELIOS_API void soilTransportSetBottomBoundaryFreeDrainage(SoilTransportModel* model) {
        guardedVoid("SoilTransportModel::setBottomBoundaryFreeDrainage", [&]() { requireModel(model)->setBottomBoundaryFreeDrainage(); });
    }

    PYHELIOS_API void soilTransportSetBottomBoundaryPressure(SoilTransportModel* model, float h) {
        guardedVoid("SoilTransportModel::setBottomBoundaryPressure", [&]() { requireModel(model)->setBottomBoundaryPressure(h); });
    }

    PYHELIOS_API void soilTransportSetBottomBoundaryFlux(SoilTransportModel* model, float flux) {
        guardedVoid("SoilTransportModel::setBottomBoundaryFlux", [&]() { requireModel(model)->setBottomBoundaryFlux(flux); });
    }

    PYHELIOS_API void soilTransportAddSurfaceEmitter(SoilTransportModel* model, float x, float y, float flow_rate, float radius) {
        guardedVoid("SoilTransportModel::addSurfaceEmitter", [&]() { requireModel(model)->addSurfaceEmitter(x, y, flow_rate, radius); });
    }

    PYHELIOS_API void soilTransportClearSurfaceEmitters(SoilTransportModel* model) {
        guardedVoid("SoilTransportModel::clearSurfaceEmitters", [&]() { requireModel(model)->clearSurfaceEmitters(); });
    }

    // ---------------------------------------------------------------- root coupling

    PYHELIOS_API void soilTransportEnableRootUptake(SoilTransportModel* model) {
        guardedVoid("SoilTransportModel::enableRootUptake", [&]() { requireModel(model)->enableRootUptake(); });
    }

    PYHELIOS_API void soilTransportSetRootDistribution(SoilTransportModel* model, unsigned int plant_id, const PyHeliosRootDistributionParams* params) {
        guardedVoid("SoilTransportModel::setRootDistribution", [&]() { requireModel(model)->setRootDistribution(plant_id, fromC(params)); });
    }

    PYHELIOS_API void soilTransportSetRootDistributionWeibull(SoilTransportModel* model, unsigned int plant_id, const PyHeliosWeibullRootParameters* params) {
        guardedVoid("SoilTransportModel::setRootDistributionWeibull", [&]() { requireModel(model)->setRootDistributionWeibull(plant_id, fromC(params)); });
    }

    PYHELIOS_API void soilTransportSetRootRadialConductivity(SoilTransportModel* model, float L_r) {
        guardedVoid("SoilTransportModel::setRootRadialConductivity", [&]() { requireModel(model)->setRootRadialConductivity(L_r); });
    }

    PYHELIOS_API void soilTransportSetRootWaterStressParameters(SoilTransportModel* model, float h_onset, float h_wilting, float omega_c) {
        guardedVoid("SoilTransportModel::setRootWaterStressParameters", [&]() { requireModel(model)->setRootWaterStressParameters(h_onset, h_wilting, omega_c); });
    }

    PYHELIOS_API void soilTransportSetTranspiration(SoilTransportModel* model, unsigned int plant_id, float transpiration) {
        guardedVoid("SoilTransportModel::setTranspiration", [&]() { requireModel(model)->setTranspiration(plant_id, transpiration); });
    }

    // ---------------------------------------------------------------- solver configuration

    PYHELIOS_API void soilTransportSetSolverType(SoilTransportModel* model, int solver_type) {
        guardedVoid("SoilTransportModel::setSolverType", [&]() {
            SolverType type = static_cast<SolverType>(checkEnum(solver_type, static_cast<int>(SolverType::SOLVER_1D), static_cast<int>(SolverType::SOLVER_3D), "SolverType"));
            requireModel(model)->setSolverType(type);
        });
    }

    PYHELIOS_API void soilTransportEnableHorizontalCoupling(SoilTransportModel* model, unsigned int interval) {
        guardedVoid("SoilTransportModel::enableHorizontalCoupling", [&]() { requireModel(model)->enableHorizontalCoupling(interval); });
    }

    PYHELIOS_API void soilTransportSetSolverParameters(SoilTransportModel* model, const PyHeliosSoilSolverParameters* params) {
        guardedVoid("SoilTransportModel::setSolverParameters", [&]() { requireModel(model)->setSolverParameters(fromC(params)); });
    }

    PYHELIOS_API void soilTransportEnableGPU(SoilTransportModel* model) {
        guardedVoid("SoilTransportModel::enableGPU", [&]() { requireModel(model)->enableGPU(); });
    }

    PYHELIOS_API void soilTransportDisableGPU(SoilTransportModel* model) {
        guardedVoid("SoilTransportModel::disableGPU", [&]() { requireModel(model)->disableGPU(); });
    }

    PYHELIOS_API int soilTransportIsGPUEnabled(SoilTransportModel* model) {
        return guarded<int>("SoilTransportModel::isGPUEnabled", 0, [&]() { return requireModel(model)->isGPUEnabled() ? 1 : 0; });
    }

    PYHELIOS_API int soilTransportIsGPUAvailable() {
        return guarded<int>("SoilTransportModel::isGPUAvailable", 0, []() { return SoilTransportModel::isGPUAvailable() ? 1 : 0; });
    }

    // ---------------------------------------------------------------- run

    PYHELIOS_API void runSoilTransportModel(SoilTransportModel* model, float dt) {
        guardedVoid("SoilTransportModel::run", [&]() { requireModel(model)->run(dt); });
    }

    // ---------------------------------------------------------------- output for coupling

    PYHELIOS_API float soilTransportGetSoilWaterPotential(SoilTransportModel* model, unsigned int plant_id) {
        return guarded<float>("SoilTransportModel::getSoilWaterPotential", 0.f, [&]() { return requireModel(model)->getSoilWaterPotential(plant_id); });
    }

    PYHELIOS_API float soilTransportGetWaterContent(SoilTransportModel* model, const float* position) {
        return guarded<float>("SoilTransportModel::getWaterContent", 0.f, [&]() { return requireModel(model)->getWaterContent(toVec3(position, "position")); });
    }

    PYHELIOS_API float soilTransportGetPressureHead(SoilTransportModel* model, const float* position) {
        return guarded<float>("SoilTransportModel::getPressureHead", 0.f, [&]() { return requireModel(model)->getPressureHead(toVec3(position, "position")); });
    }

    // ---------------------------------------------------------------- point sensors

    PYHELIOS_API unsigned int soilTransportAddSensor(SoilTransportModel* model, const float* position, int quantity) {
        return guarded<unsigned int>("SoilTransportModel::addSensor", 0u, [&]() {
            SoilMeasurement q = static_cast<SoilMeasurement>(checkEnum(quantity, static_cast<int>(SoilMeasurement::WATER_CONTENT), static_cast<int>(SoilMeasurement::PRESSURE_HEAD), "SoilMeasurement"));
            return requireModel(model)->addSensor(toVec3(position, "position"), q);
        });
    }

    PYHELIOS_API void soilTransportRecordSensors(SoilTransportModel* model) {
        guardedVoid("SoilTransportModel::recordSensors", [&]() { requireModel(model)->recordSensors(); });
    }

    PYHELIOS_API unsigned int soilTransportGetSensorCount(SoilTransportModel* model) {
        return guarded<unsigned int>("SoilTransportModel::getSensorCount", 0u, [&]() { return requireModel(model)->getSensorCount(); });
    }

    PYHELIOS_API float* soilTransportGetSensorData(SoilTransportModel* model, unsigned int sensor_id, unsigned int* count) {
        return guarded<float*>("SoilTransportModel::getSensorData", nullptr, [&]() { return returnVector(requireModel(model)->getSensorData(sensor_id), requireCount(count)); });
    }

    PYHELIOS_API float* soilTransportGetSensorTimes(SoilTransportModel* model, unsigned int sensor_id, unsigned int* count) {
        return guarded<float*>("SoilTransportModel::getSensorTimes", nullptr, [&]() { return returnVector(requireModel(model)->getSensorTimes(sensor_id), requireCount(count)); });
    }

    PYHELIOS_API void soilTransportGetSensorPosition(SoilTransportModel* model, unsigned int sensor_id, float* position) {
        guardedVoid("SoilTransportModel::getSensorPosition", [&]() {
            if (!position) {
                throw std::invalid_argument("position pointer is null");
            }
            helios::vec3 p = requireModel(model)->getSensorPosition(sensor_id);
            position[0] = p.x;
            position[1] = p.y;
            position[2] = p.z;
        });
    }

    PYHELIOS_API int soilTransportGetSensorQuantity(SoilTransportModel* model, unsigned int sensor_id) {
        return guarded<int>("SoilTransportModel::getSensorQuantity", -1, [&]() { return static_cast<int>(requireModel(model)->getSensorQuantity(sensor_id)); });
    }

    PYHELIOS_API void soilTransportClearSensorData(SoilTransportModel* model) {
        guardedVoid("SoilTransportModel::clearSensorData", [&]() { requireModel(model)->clearSensorData(); });
    }

    PYHELIOS_API void soilTransportWriteSensorData(SoilTransportModel* model, const char* filename) {
        guardedVoid("SoilTransportModel::writeSensorData", [&]() { requireModel(model)->writeSensorData(toString(filename, "filename")); });
    }

    // ---------------------------------------------------------------- diagnostics and mass balance

    PYHELIOS_API unsigned int soilTransportGetLastSubstepCount(SoilTransportModel* model) {
        return guarded<unsigned int>("SoilTransportModel::getLastSubstepCount", 0u, [&]() { return requireModel(model)->getLastSubstepCount(); });
    }

    PYHELIOS_API void soilTransportResetSolverStats(SoilTransportModel* model) {
        guardedVoid("SoilTransportModel::resetSolverStats", [&]() { requireModel(model)->resetSolverStats(); });
    }

    PYHELIOS_API unsigned long long soilTransportSolverPicardOuter(SoilTransportModel* model) {
        return guarded<unsigned long long>("SoilTransportModel::solverPicardOuter", 0ull, [&]() { return static_cast<unsigned long long>(requireModel(model)->solverPicardOuter()); });
    }

    PYHELIOS_API unsigned long long soilTransportSolverNewtonOuter(SoilTransportModel* model) {
        return guarded<unsigned long long>("SoilTransportModel::solverNewtonOuter", 0ull, [&]() { return static_cast<unsigned long long>(requireModel(model)->solverNewtonOuter()); });
    }

    PYHELIOS_API unsigned long long soilTransportSolverPicardGmres(SoilTransportModel* model) {
        return guarded<unsigned long long>("SoilTransportModel::solverPicardGmres", 0ull, [&]() { return static_cast<unsigned long long>(requireModel(model)->solverPicardGmres()); });
    }

    PYHELIOS_API unsigned long long soilTransportSolverNewtonGmres(SoilTransportModel* model) {
        return guarded<unsigned long long>("SoilTransportModel::solverNewtonGmres", 0ull, [&]() { return static_cast<unsigned long long>(requireModel(model)->solverNewtonGmres()); });
    }

    PYHELIOS_API float soilTransportGetTimestep(SoilTransportModel* model) {
        return guarded<float>("SoilTransportModel::getTimestep", 0.f, [&]() { return requireModel(model)->getTimestep(); });
    }

    PYHELIOS_API unsigned long long soilTransportGetSolverIterationCount(SoilTransportModel* model) {
        return guarded<unsigned long long>("SoilTransportModel::getSolverIterationCount", 0ull, [&]() { return static_cast<unsigned long long>(requireModel(model)->getSolverIterationCount()); });
    }

    PYHELIOS_API void soilTransportResetSolverIterationCount(SoilTransportModel* model) {
        guardedVoid("SoilTransportModel::resetSolverIterationCount", [&]() { requireModel(model)->resetSolverIterationCount(); });
    }

    PYHELIOS_API double soilTransportGetTotalWaterStorage(SoilTransportModel* model) {
        return guarded<double>("SoilTransportModel::getTotalWaterStorage", 0.0, [&]() { return requireModel(model)->getTotalWaterStorage(); });
    }

    PYHELIOS_API double soilTransportGetCumulativeBoundaryInflux(SoilTransportModel* model) {
        return guarded<double>("SoilTransportModel::getCumulativeBoundaryInflux", 0.0, [&]() { return requireModel(model)->getCumulativeBoundaryInflux(); });
    }

    PYHELIOS_API double soilTransportGetMassBalanceResidual(SoilTransportModel* model) {
        return guarded<double>("SoilTransportModel::getMassBalanceResidual", 0.0, [&]() { return requireModel(model)->getMassBalanceResidual(); });
    }

    PYHELIOS_API void soilTransportResetMassBalance(SoilTransportModel* model) {
        guardedVoid("SoilTransportModel::resetMassBalance", [&]() { requireModel(model)->resetMassBalance(); });
    }

    PYHELIOS_API float soilTransportGetCumulativeRootUptake(SoilTransportModel* model, unsigned int plant_id) {
        return guarded<float>("SoilTransportModel::getCumulativeRootUptake", 0.f, [&]() { return requireModel(model)->getCumulativeRootUptake(plant_id); });
    }

    PYHELIOS_API float soilTransportGetRootUptakeFlux(SoilTransportModel* model, unsigned int plant_id) {
        return guarded<float>("SoilTransportModel::getRootUptakeFlux", 0.f, [&]() { return requireModel(model)->getRootUptakeFlux(plant_id); });
    }

    // ---------------------------------------------------------------- visualization

    PYHELIOS_API unsigned int* soilTransportAddSoilVisualization(SoilTransportModel* model, int mode, unsigned int* count) {
        return guarded<unsigned int*>("SoilTransportModel::addSoilVisualization", nullptr, [&]() {
            unsigned int* n = requireCount(count);
            return returnVector(requireModel(model)->addSoilVisualization(toColorMode(mode)), n);
        });
    }

    PYHELIOS_API unsigned int* soilTransportAddSoilVisualizationKeepFraction(SoilTransportModel* model, int mode, const float* keep_fraction, unsigned int* count) {
        return guarded<unsigned int*>("SoilTransportModel::addSoilVisualization", nullptr, [&]() {
            unsigned int* n = requireCount(count);
            return returnVector(requireModel(model)->addSoilVisualization(toColorMode(mode), toVec3(keep_fraction, "keep_fraction")), n);
        });
    }

    PYHELIOS_API unsigned int* soilTransportAddSoilVisualizationRegion(SoilTransportModel* model, int mode, const float* fraction_min, const float* fraction_max, int region, unsigned int* count) {
        return guarded<unsigned int*>("SoilTransportModel::addSoilVisualization", nullptr, [&]() {
            unsigned int* n = requireCount(count);
            SoilRegion r = static_cast<SoilRegion>(checkEnum(region, static_cast<int>(SoilRegion::KEEP), static_cast<int>(SoilRegion::REMOVE), "SoilRegion"));
            return returnVector(requireModel(model)->addSoilVisualization(toColorMode(mode), toVec3(fraction_min, "fraction_min"), toVec3(fraction_max, "fraction_max"), r), n);
        });
    }

    PYHELIOS_API void soilTransportUpdateSoilVisualization(SoilTransportModel* model, const unsigned int* uuids, unsigned int uuid_count, int mode) {
        guardedVoid("SoilTransportModel::updateSoilVisualization", [&]() {
            if (!uuids && uuid_count > 0) {
                throw std::invalid_argument("UUIDs array is null");
            }
            std::vector<uint> uuid_vector;
            if (uuid_count > 0) {
                uuid_vector.assign(uuids, uuids + uuid_count);
            }
            requireModel(model)->updateSoilVisualization(uuid_vector, toColorMode(mode));
        });
    }

    // ---------------------------------------------------------------- messages

    PYHELIOS_API void soilTransportEnableMessages(SoilTransportModel* model) {
        guardedVoid("SoilTransportModel::enableMessages", [&]() { requireModel(model)->enableMessages(); });
    }

    PYHELIOS_API void soilTransportDisableMessages(SoilTransportModel* model) {
        guardedVoid("SoilTransportModel::disableMessages", [&]() { requireModel(model)->disableMessages(); });
    }

    // ---------------------------------------------------------------- soil property library

    PYHELIOS_API void soilTransportGetSoilPropertiesFromTexture(const char* texture, PyHeliosSoilProperties* out) {
        guardedVoid("getSoilPropertiesFromTexture", [&]() { toC(getSoilPropertiesFromTexture(toString(texture, "texture")), out); });
    }

    PYHELIOS_API void soilTransportGetSoilPropertiesFromTextureModel(const char* texture, int soil_model, int match_standard_curves, PyHeliosSoilProperties* out) {
        guardedVoid("getSoilPropertiesFromTexture", [&]() { toC(getSoilPropertiesFromTexture(toString(texture, "texture"), toSoilModel(soil_model), match_standard_curves != 0), out); });
    }

    PYHELIOS_API void soilTransportToModifiedVanGenuchten(const PyHeliosSoilProperties* vg, float h_e, int match_standard_curves, PyHeliosSoilProperties* out) {
        guardedVoid("toModifiedVanGenuchten", [&]() { toC(toModifiedVanGenuchten(fromC(vg), h_e, match_standard_curves != 0), out); });
    }

    PYHELIOS_API const char* soilTransportGetAvailableSoilTextures() {
        return guarded<const char*>("getAvailableSoilTextures", nullptr, []() {
            static thread_local std::string joined;
            joined.clear();
            for (const std::string& name : getAvailableSoilTextures()) {
                if (!joined.empty()) {
                    joined += '\n';
                }
                joined += name;
            }
            return joined.c_str();
        });
    }

    PYHELIOS_API int soilTransportIsSoilTextureAvailable(const char* texture) {
        return guarded<int>("isSoilTextureAvailable", 0, [&]() { return isSoilTextureAvailable(toString(texture, "texture")) ? 1 : 0; });
    }

} // extern "C"

#endif // SOILTRANSPORT_PLUGIN_AVAILABLE
