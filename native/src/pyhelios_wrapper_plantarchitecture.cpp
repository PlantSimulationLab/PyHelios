// PyHelios C Interface - PlantArchitecture Functions
// Provides procedural plant modeling using plant architecture library

#include "../include/pyhelios_wrapper_common.h"
#include "../include/pyhelios_wrapper_context.h"
#include "Context.h"
#include <string>
#include <vector>
#include <map>
#include <exception>
#include <cstring>

#ifdef PLANTARCHITECTURE_PLUGIN_AVAILABLE
#include "../include/pyhelios_wrapper_plantarchitecture.h"
#include "PlantArchitecture.h"
#include "../../helios-core/plugins/radiation/lib/json/json.hpp"

// Helper functions for JSON serialization (outside extern "C" - internal C++ helpers)
namespace {

nlohmann::json randomParameterFloatToJSON(RandomParameter_float param) {
    nlohmann::json j;
    j["distribution"] = param.distribution;

    if (param.distribution == "constant") {
        // For constant, get the value using val()
        j["parameters"] = std::vector<float>{param.val()};
    } else {
        j["parameters"] = param.distribution_parameters;
    }
    return j;
}

nlohmann::json randomParameterIntToJSON(RandomParameter_int param) {
    nlohmann::json j;
    j["distribution"] = param.distribution;

    if (param.distribution == "constant") {
        // For constant, get the value using val()
        j["parameters"] = std::vector<float>{static_cast<float>(param.val())};
    } else {
        // Convert int distribution_parameters to float for JSON
        std::vector<float> float_params;
        for (int p : param.distribution_parameters) {
            float_params.push_back(static_cast<float>(p));
        }
        j["parameters"] = float_params;
    }
    return j;
}

RandomParameter_float jsonToRandomParameterFloat(const nlohmann::json& j, std::minstd_rand0* generator) {
    RandomParameter_float param;
    param.initialize(generator);
    std::string dist = j["distribution"];

    if (dist == "constant") {
        std::vector<float> params = j["parameters"];
        if (!params.empty()) {
            param = params[0];
        }
    } else if (dist == "uniform") {
        std::vector<float> params = j["parameters"];
        if (params.size() >= 2) {
            param.uniformDistribution(params[0], params[1]);
        }
    } else if (dist == "normal") {
        std::vector<float> params = j["parameters"];
        if (params.size() >= 2) {
            param.normalDistribution(params[0], params[1]);
        }
    } else if (dist == "weibull") {
        std::vector<float> params = j["parameters"];
        if (params.size() >= 2) {
            param.weibullDistribution(params[0], params[1]);
        }
    }

    return param;
}

RandomParameter_int jsonToRandomParameterInt(const nlohmann::json& j, std::minstd_rand0* generator) {
    RandomParameter_int param;
    param.initialize(generator);
    std::string dist = j["distribution"];

    if (dist == "constant") {
        std::vector<float> params = j["parameters"];
        if (!params.empty()) {
            param = static_cast<int>(params[0]);
        }
    } else if (dist == "uniform") {
        std::vector<float> params = j["parameters"];
        if (params.size() >= 2) {
            param.uniformDistribution(static_cast<int>(params[0]), static_cast<int>(params[1]));
        }
    } else if (dist == "discretevalues") {
        std::vector<float> params = j["parameters"];
        std::vector<int> int_params;
        for (float p : params) {
            int_params.push_back(static_cast<int>(p));
        }
        param.discreteValues(int_params);
    }

    return param;
}

nlohmann::json shootParametersToJSON(const ShootParameters& params) {
    nlohmann::json j;

    // Geometric parameters
    j["max_nodes"] = randomParameterIntToJSON(params.max_nodes);
    j["max_nodes_per_season"] = randomParameterIntToJSON(params.max_nodes_per_season);
    j["girth_area_factor"] = randomParameterFloatToJSON(params.girth_area_factor);
    j["insertion_angle_tip"] = randomParameterFloatToJSON(params.insertion_angle_tip);
    j["insertion_angle_decay_rate"] = randomParameterFloatToJSON(params.insertion_angle_decay_rate);
    j["internode_length_max"] = randomParameterFloatToJSON(params.internode_length_max);
    j["internode_length_min"] = randomParameterFloatToJSON(params.internode_length_min);
    j["internode_length_decay_rate"] = randomParameterFloatToJSON(params.internode_length_decay_rate);
    j["base_roll"] = randomParameterFloatToJSON(params.base_roll);
    j["base_yaw"] = randomParameterFloatToJSON(params.base_yaw);
    j["gravitropic_curvature"] = randomParameterFloatToJSON(params.gravitropic_curvature);
    j["tortuosity"] = randomParameterFloatToJSON(params.tortuosity);

    // Growth parameters
    j["phyllochron_min"] = randomParameterFloatToJSON(params.phyllochron_min);
    j["elongation_rate_max"] = randomParameterFloatToJSON(params.elongation_rate_max);
    j["vegetative_bud_break_probability_min"] = randomParameterFloatToJSON(params.vegetative_bud_break_probability_min);
    j["vegetative_bud_break_probability_decay_rate"] = randomParameterFloatToJSON(params.vegetative_bud_break_probability_decay_rate);
    j["max_terminal_floral_buds"] = randomParameterIntToJSON(params.max_terminal_floral_buds);
    j["flower_bud_break_probability"] = randomParameterFloatToJSON(params.flower_bud_break_probability);
    j["fruit_set_probability"] = randomParameterFloatToJSON(params.fruit_set_probability);
    j["vegetative_bud_break_time"] = randomParameterFloatToJSON(params.vegetative_bud_break_time);

    // Boolean flags
    j["flowers_require_dormancy"] = params.flowers_require_dormancy;
    j["growth_requires_dormancy"] = params.growth_requires_dormancy;
    j["determinate_shoot_growth"] = params.determinate_shoot_growth;

    return j;
}

ShootParameters jsonToShootParameters(const nlohmann::json& j, std::minstd_rand0* generator) {
    ShootParameters params(generator);

    // Geometric parameters
    if (j.contains("max_nodes")) params.max_nodes = jsonToRandomParameterInt(j["max_nodes"], generator);
    if (j.contains("max_nodes_per_season")) params.max_nodes_per_season = jsonToRandomParameterInt(j["max_nodes_per_season"], generator);
    if (j.contains("girth_area_factor")) params.girth_area_factor = jsonToRandomParameterFloat(j["girth_area_factor"], generator);
    if (j.contains("insertion_angle_tip")) params.insertion_angle_tip = jsonToRandomParameterFloat(j["insertion_angle_tip"], generator);
    if (j.contains("insertion_angle_decay_rate")) params.insertion_angle_decay_rate = jsonToRandomParameterFloat(j["insertion_angle_decay_rate"], generator);
    if (j.contains("internode_length_max")) params.internode_length_max = jsonToRandomParameterFloat(j["internode_length_max"], generator);
    if (j.contains("internode_length_min")) params.internode_length_min = jsonToRandomParameterFloat(j["internode_length_min"], generator);
    if (j.contains("internode_length_decay_rate")) params.internode_length_decay_rate = jsonToRandomParameterFloat(j["internode_length_decay_rate"], generator);
    if (j.contains("base_roll")) params.base_roll = jsonToRandomParameterFloat(j["base_roll"], generator);
    if (j.contains("base_yaw")) params.base_yaw = jsonToRandomParameterFloat(j["base_yaw"], generator);
    if (j.contains("gravitropic_curvature")) params.gravitropic_curvature = jsonToRandomParameterFloat(j["gravitropic_curvature"], generator);
    if (j.contains("tortuosity")) params.tortuosity = jsonToRandomParameterFloat(j["tortuosity"], generator);

    // Growth parameters
    if (j.contains("phyllochron_min")) params.phyllochron_min = jsonToRandomParameterFloat(j["phyllochron_min"], generator);
    if (j.contains("elongation_rate_max")) params.elongation_rate_max = jsonToRandomParameterFloat(j["elongation_rate_max"], generator);
    if (j.contains("vegetative_bud_break_probability_min")) params.vegetative_bud_break_probability_min = jsonToRandomParameterFloat(j["vegetative_bud_break_probability_min"], generator);
    if (j.contains("vegetative_bud_break_probability_decay_rate")) params.vegetative_bud_break_probability_decay_rate = jsonToRandomParameterFloat(j["vegetative_bud_break_probability_decay_rate"], generator);
    if (j.contains("max_terminal_floral_buds")) params.max_terminal_floral_buds = jsonToRandomParameterInt(j["max_terminal_floral_buds"], generator);
    if (j.contains("flower_bud_break_probability")) params.flower_bud_break_probability = jsonToRandomParameterFloat(j["flower_bud_break_probability"], generator);
    if (j.contains("fruit_set_probability")) params.fruit_set_probability = jsonToRandomParameterFloat(j["fruit_set_probability"], generator);
    if (j.contains("vegetative_bud_break_time")) params.vegetative_bud_break_time = jsonToRandomParameterFloat(j["vegetative_bud_break_time"], generator);

    // Boolean flags
    if (j.contains("flowers_require_dormancy")) params.flowers_require_dormancy = j["flowers_require_dormancy"];
    if (j.contains("growth_requires_dormancy")) params.growth_requires_dormancy = j["growth_requires_dormancy"];
    if (j.contains("determinate_shoot_growth")) params.determinate_shoot_growth = j["determinate_shoot_growth"];

    // Child shoot types
    if (j.contains("child_shoot_types")) {
        std::vector<std::string> labels = j["child_shoot_types"]["labels"];
        std::vector<float> probs = j["child_shoot_types"]["probabilities"];
        params.defineChildShootTypes(labels, probs);
    }

    return params;
}

} // anonymous namespace

extern "C" {

    // PlantArchitecture management functions
    PYHELIOS_API PlantArchitecture* createPlantArchitecture(helios::Context* context) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return nullptr;
            }
            return new PlantArchitecture(context);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::constructor): ") + e.what());
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::constructor): Unknown error creating PlantArchitecture.");
            return nullptr;
        }
    }

    PYHELIOS_API void destroyPlantArchitecture(PlantArchitecture* plantarch) {
        delete plantarch;
    }

    // Plant library functions
    PYHELIOS_API int loadPlantModelFromLibrary(PlantArchitecture* plantarch, const char* plant_label) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!plant_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Plant label is null");
                return -1;
            }

            plantarch->loadPlantModelFromLibrary(std::string(plant_label));
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::loadPlantModelFromLibrary): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::loadPlantModelFromLibrary): Unknown error loading plant model.");
            return -1;
        }
    }

    PYHELIOS_API unsigned int buildPlantInstanceFromLibrary(PlantArchitecture* plantarch, float* base_position, float age, char** param_keys, float* param_values, int param_count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return 0;
            }
            if (!base_position) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Base position array is null");
                return 0;
            }

            helios::vec3 position(base_position[0], base_position[1], base_position[2]);

            // Convert parallel arrays to std::map if parameters provided
            std::map<std::string, float> build_params;
            if (param_keys && param_values && param_count > 0) {
                for (int i = 0; i < param_count; i++) {
                    if (param_keys[i]) {
                        build_params[std::string(param_keys[i])] = param_values[i];
                    }
                }
            }

            return plantarch->buildPlantInstanceFromLibrary(position, age, build_params);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::buildPlantInstanceFromLibrary): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::buildPlantInstanceFromLibrary): Unknown error building plant instance.");
            return 0;
        }
    }

    PYHELIOS_API int buildPlantCanopyFromLibrary(PlantArchitecture* plantarch, float* canopy_center, float* plant_spacing, int* plant_count, float age, float germination_rate, unsigned int** plant_ids, int* num_plants, char** param_keys, float* param_values, int param_count_params) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!canopy_center || !plant_spacing || !plant_count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter arrays are null");
                return -1;
            }

            helios::vec3 center(canopy_center[0], canopy_center[1], canopy_center[2]);
            helios::vec2 spacing(plant_spacing[0], plant_spacing[1]);
            helios::int2 count(plant_count[0], plant_count[1]);

            // Convert parallel arrays to std::map if parameters provided
            std::map<std::string, float> build_params;
            if (param_keys && param_values && param_count_params > 0) {
                for (int i = 0; i < param_count_params; i++) {
                    if (param_keys[i]) {
                        build_params[std::string(param_keys[i])] = param_values[i];
                    }
                }
            }

            std::vector<uint> plantIDs = plantarch->buildPlantCanopyFromLibrary(center, spacing, count, age, germination_rate, build_params);

            // Convert vector to static array for return
            static thread_local std::vector<unsigned int> static_result;
            static_result = plantIDs;
            *plant_ids = static_result.data();
            *num_plants = static_result.size();

            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::buildPlantCanopyFromLibrary): ") + e.what());
            if (num_plants) *num_plants = 0;
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::buildPlantCanopyFromLibrary): Unknown error building plant canopy.");
            if (num_plants) *num_plants = 0;
            return -1;
        }
    }

    PYHELIOS_API int advanceTime(PlantArchitecture* plantarch, float dt) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (dt < 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Time step cannot be negative");
                return -1;
            }

            plantarch->advanceTime(dt);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::advanceTime): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::advanceTime): Unknown error advancing time.");
            return -1;
        }
    }

    // Plant query functions
    PYHELIOS_API int getAvailablePlantModels(PlantArchitecture* plantarch, char*** model_names, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!model_names || !count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output parameters are null");
                return -1;
            }

            std::vector<std::string> models = plantarch->getAvailablePlantModels();
            *count = models.size();

            // Allocate array of string pointers
            *model_names = new char*[models.size()];

            // Copy each string
            for (size_t i = 0; i < models.size(); i++) {
                (*model_names)[i] = new char[models[i].length() + 1];
                strcpy((*model_names)[i], models[i].c_str());
            }

            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getAvailablePlantModels): ") + e.what());
            if (count) *count = 0;
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getAvailablePlantModels): Unknown error getting available plant models.");
            if (count) *count = 0;
            return -1;
        }
    }

    PYHELIOS_API unsigned int* getAllPlantObjectIDs(PlantArchitecture* plantarch, unsigned int plantID, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }

            std::vector<uint> objectIDs = plantarch->getAllPlantObjectIDs(plantID);

            // Convert vector to static array for return
            static thread_local std::vector<unsigned int> static_result;
            static_result = objectIDs;
            *count = static_result.size();

            return static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getAllPlantObjectIDs): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getAllPlantObjectIDs): Unknown error getting plant object IDs.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* getAllPlantUUIDs(PlantArchitecture* plantarch, unsigned int plantID, bool include_hidden, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }

            std::vector<uint> uuids = plantarch->getAllPlantUUIDs(plantID, include_hidden);

            // Convert vector to static array for return
            static thread_local std::vector<unsigned int> static_result;
            static_result = uuids;
            *count = static_result.size();

            return static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getAllPlantUUIDs): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getAllPlantUUIDs): Unknown error getting plant UUIDs.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    // Memory cleanup functions
    PYHELIOS_API void freeStringArray(char** strings, int count) {
        if (strings) {
            for (int i = 0; i < count; i++) {
                delete[] strings[i];
            }
            delete[] strings;
        }
    }

    PYHELIOS_API void freeIntArray(unsigned int* array) {
        // Note: For our implementation, arrays are static thread_local,
        // so no explicit cleanup is needed. This function is provided
        // for API consistency and future compatibility.
    }

    // Collision detection functions
    PYHELIOS_API int enableSoftCollisionAvoidance(PlantArchitecture* plantarch, const unsigned int* target_UUIDs, int uuid_count, const unsigned int* target_IDs, int id_count, bool enable_petiole, bool enable_fruit) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }

            // Convert arrays to vectors
            std::vector<uint> uuid_vector;
            if (target_UUIDs && uuid_count > 0) {
                uuid_vector.assign(target_UUIDs, target_UUIDs + uuid_count);
            }

            std::vector<uint> id_vector;
            if (target_IDs && id_count > 0) {
                id_vector.assign(target_IDs, target_IDs + id_count);
            }

            plantarch->enableSoftCollisionAvoidance(uuid_vector, id_vector, enable_petiole, enable_fruit);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::enableSoftCollisionAvoidance): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::enableSoftCollisionAvoidance): Unknown error enabling collision avoidance.");
            return -1;
        }
    }

    PYHELIOS_API void disableCollisionDetection(PlantArchitecture* plantarch) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return;
            }

            plantarch->disableCollisionDetection();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::disableCollisionDetection): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::disableCollisionDetection): Unknown error disabling collision detection.");
        }
    }

    PYHELIOS_API void setSoftCollisionAvoidanceParameters(PlantArchitecture* plantarch, float view_half_angle_deg, float look_ahead_distance, int sample_count, float inertia_weight) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return;
            }

            plantarch->setSoftCollisionAvoidanceParameters(view_half_angle_deg, look_ahead_distance, sample_count, inertia_weight);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setSoftCollisionAvoidanceParameters): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setSoftCollisionAvoidanceParameters): Unknown error setting collision parameters.");
        }
    }

    PYHELIOS_API void setCollisionRelevantOrgans(PlantArchitecture* plantarch, bool include_internodes, bool include_leaves, bool include_petioles, bool include_flowers, bool include_fruit) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return;
            }

            plantarch->setCollisionRelevantOrgans(include_internodes, include_leaves, include_petioles, include_flowers, include_fruit);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setCollisionRelevantOrgans): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setCollisionRelevantOrgans): Unknown error setting collision-relevant organs.");
        }
    }

    PYHELIOS_API int enableSolidObstacleAvoidance(PlantArchitecture* plantarch, const unsigned int* obstacle_UUIDs, int uuid_count, float avoidance_distance, bool enable_fruit_adjustment, bool enable_obstacle_pruning) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }

            // Convert array to vector
            std::vector<uint> uuid_vector;
            if (obstacle_UUIDs && uuid_count > 0) {
                uuid_vector.assign(obstacle_UUIDs, obstacle_UUIDs + uuid_count);
            }

            plantarch->enableSolidObstacleAvoidance(uuid_vector, avoidance_distance, enable_fruit_adjustment, enable_obstacle_pruning);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::enableSolidObstacleAvoidance): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::enableSolidObstacleAvoidance): Unknown error enabling solid obstacle avoidance.");
            return -1;
        }
    }

    PYHELIOS_API int setStaticObstacles(PlantArchitecture* plantarch, const unsigned int* target_UUIDs, int uuid_count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }

            // Convert array to vector
            std::vector<uint> uuid_vector;
            if (target_UUIDs && uuid_count > 0) {
                uuid_vector.assign(target_UUIDs, target_UUIDs + uuid_count);
            }

            plantarch->setStaticObstacles(uuid_vector);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setStaticObstacles): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setStaticObstacles): Unknown error setting static obstacles.");
            return -1;
        }
    }

    PYHELIOS_API unsigned int* getPlantCollisionRelevantObjectIDs(PlantArchitecture* plantarch, unsigned int plant_id, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }

            std::vector<uint> objectIDs = plantarch->getPlantCollisionRelevantObjectIDs(plant_id);

            // Convert vector to static array for return
            static thread_local std::vector<unsigned int> static_result;
            static_result = objectIDs;
            *count = static_result.size();

            return static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getPlantCollisionRelevantObjectIDs): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getPlantCollisionRelevantObjectIDs): Unknown error getting collision-relevant object IDs.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    // File I/O functions
    PYHELIOS_API int writePlantMeshVertices(PlantArchitecture* plantarch, unsigned int plantID, const char* filename) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null");
                return -1;
            }
            if (std::strlen(filename) == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename cannot be empty");
                return -1;
            }

            plantarch->writePlantMeshVertices(plantID, std::string(filename));
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::writePlantMeshVertices): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::writePlantMeshVertices): Unknown error writing plant mesh vertices.");
            return -1;
        }
    }

    PYHELIOS_API int writePlantStructureXML(PlantArchitecture* plantarch, unsigned int plantID, const char* filename) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null");
                return -1;
            }
            if (std::strlen(filename) == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename cannot be empty");
                return -1;
            }

            plantarch->writePlantStructureXML(plantID, std::string(filename));
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::writePlantStructureXML): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::writePlantStructureXML): Unknown error writing plant structure XML.");
            return -1;
        }
    }

    PYHELIOS_API int writeQSMCylinderFile(PlantArchitecture* plantarch, unsigned int plantID, const char* filename) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null");
                return -1;
            }
            if (std::strlen(filename) == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename cannot be empty");
                return -1;
            }

            plantarch->writeQSMCylinderFile(plantID, std::string(filename));
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::writeQSMCylinderFile): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::writeQSMCylinderFile): Unknown error writing QSM cylinder file.");
            return -1;
        }
    }

    PYHELIOS_API int writePlantStructureUSD(PlantArchitecture* plantarch, unsigned int plantID, const char* filename,
                                             float elastic_modulus, float wood_density, float damping_ratio,
                                             float static_friction, float dynamic_friction, float restitution,
                                             float organ_spring_stiffness, float organ_spring_damping,
                                             float leaf_mass_per_area, float fruit_mass, float flower_mass,
                                             unsigned int solver_position_iterations, float min_segment_length) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!filename || std::strlen(filename) == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename cannot be null or empty");
                return -1;
            }

            USDExportParameters params;
            params.elastic_modulus = elastic_modulus;
            params.wood_density = wood_density;
            params.damping_ratio = damping_ratio;
            params.static_friction = static_friction;
            params.dynamic_friction = dynamic_friction;
            params.restitution = restitution;
            params.organ_spring_stiffness = organ_spring_stiffness;
            params.organ_spring_damping = organ_spring_damping;
            params.leaf_mass_per_area = leaf_mass_per_area;
            params.fruit_mass = fruit_mass;
            params.flower_mass = flower_mass;
            params.solver_position_iterations = solver_position_iterations;
            params.min_segment_length = min_segment_length;

            plantarch->writePlantStructureUSD(plantID, std::string(filename), params);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::writePlantStructureUSD): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::writePlantStructureUSD): Unknown error writing USD file.");
            return -1;
        }
    }

    PYHELIOS_API int registerGrowthFrame(PlantArchitecture* plantarch, unsigned int plantID, float min_segment_length) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            plantarch->registerGrowthFrame(plantID, min_segment_length);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::registerGrowthFrame): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::registerGrowthFrame): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int writePlantGrowthUSD(PlantArchitecture* plantarch, unsigned int plantID, const char* filename, float seconds_per_frame) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!filename || std::strlen(filename) == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename cannot be null or empty");
                return -1;
            }
            plantarch->writePlantGrowthUSD(plantID, std::string(filename), seconds_per_frame);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::writePlantGrowthUSD): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::writePlantGrowthUSD): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int clearGrowthFrames(PlantArchitecture* plantarch, unsigned int plantID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            plantarch->clearGrowthFrames(plantID);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::clearGrowthFrames): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::clearGrowthFrames): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API unsigned int getGrowthFrameCount(PlantArchitecture* plantarch, unsigned int plantID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return 0;
            }
            return plantarch->getGrowthFrameCount(plantID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getGrowthFrameCount): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getGrowthFrameCount): Unknown error.");
            return 0;
        }
    }

    PYHELIOS_API int readPlantStructureXML(PlantArchitecture* plantarch, const char* filename, bool quiet, unsigned int** plant_ids, int* num_plants) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (num_plants) *num_plants = 0;
                return -1;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null");
                if (num_plants) *num_plants = 0;
                return -1;
            }
            if (std::strlen(filename) == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename cannot be empty");
                if (num_plants) *num_plants = 0;
                return -1;
            }
            if (!plant_ids || !num_plants) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output parameters are null");
                if (num_plants) *num_plants = 0;
                return -1;
            }

            std::vector<uint> plantIDs = plantarch->readPlantStructureXML(std::string(filename), quiet);

            // Convert vector to static array for return
            static thread_local std::vector<unsigned int> static_result;
            static_result = plantIDs;
            *plant_ids = static_result.data();
            *num_plants = static_result.size();

            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::readPlantStructureXML): ") + e.what());
            if (num_plants) *num_plants = 0;
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::readPlantStructureXML): Unknown error reading plant structure XML.");
            if (num_plants) *num_plants = 0;
            return -1;
        }
    }

    // Custom plant building functions
    PYHELIOS_API unsigned int addPlantInstance(PlantArchitecture* plantarch, float* base_position, float current_age) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return 0;
            }
            if (!base_position) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Base position array is null");
                return 0;
            }
            if (current_age < 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Current age cannot be negative");
                return 0;
            }

            helios::vec3 position(base_position[0], base_position[1], base_position[2]);
            return plantarch->addPlantInstance(position, current_age);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::addPlantInstance): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::addPlantInstance): Unknown error adding plant instance.");
            return 0;
        }
    }

    PYHELIOS_API int deletePlantInstance(PlantArchitecture* plantarch, unsigned int plantID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }

            plantarch->deletePlantInstance(plantID);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::deletePlantInstance): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::deletePlantInstance): Unknown error deleting plant instance.");
            return -1;
        }
    }

    PYHELIOS_API unsigned int addBaseStemShoot(PlantArchitecture* plantarch, unsigned int plantID, unsigned int current_node_number, float* base_rotation, float internode_radius, float internode_length_max, float internode_length_scale_factor_fraction, float leaf_scale_factor_fraction, float radius_taper, const char* shoot_type_label) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return 0;
            }
            if (!base_rotation) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Base rotation array is null");
                return 0;
            }
            if (!shoot_type_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Shoot type label is null");
                return 0;
            }
            if (std::strlen(shoot_type_label) == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Shoot type label cannot be empty");
                return 0;
            }

            // Convert rotation array to AxisRotation
            AxisRotation rotation(base_rotation[0], base_rotation[1], base_rotation[2]);

            return plantarch->addBaseStemShoot(plantID, current_node_number, rotation, internode_radius, internode_length_max, internode_length_scale_factor_fraction, leaf_scale_factor_fraction, radius_taper, std::string(shoot_type_label));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::addBaseStemShoot): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::addBaseStemShoot): Unknown error adding base stem shoot.");
            return 0;
        }
    }

    PYHELIOS_API unsigned int appendShoot(PlantArchitecture* plantarch, unsigned int plantID, int parent_shoot_ID, unsigned int current_node_number, float* base_rotation, float internode_radius, float internode_length_max, float internode_length_scale_factor_fraction, float leaf_scale_factor_fraction, float radius_taper, const char* shoot_type_label) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return 0;
            }
            if (!base_rotation) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Base rotation array is null");
                return 0;
            }
            if (!shoot_type_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Shoot type label is null");
                return 0;
            }
            if (std::strlen(shoot_type_label) == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Shoot type label cannot be empty");
                return 0;
            }

            // Convert rotation array to AxisRotation
            AxisRotation rotation(base_rotation[0], base_rotation[1], base_rotation[2]);

            return plantarch->appendShoot(plantID, parent_shoot_ID, current_node_number, rotation, internode_radius, internode_length_max, internode_length_scale_factor_fraction, leaf_scale_factor_fraction, radius_taper, std::string(shoot_type_label));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::appendShoot): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::appendShoot): Unknown error appending shoot.");
            return 0;
        }
    }

    PYHELIOS_API unsigned int addChildShoot(PlantArchitecture* plantarch, unsigned int plantID, int parent_shoot_ID, unsigned int parent_node_index, unsigned int current_node_number, float* shoot_base_rotation, float internode_radius, float internode_length_max, float internode_length_scale_factor_fraction, float leaf_scale_factor_fraction, float radius_taper, const char* shoot_type_label, unsigned int petiole_index) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return 0;
            }
            if (!shoot_base_rotation) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Shoot base rotation array is null");
                return 0;
            }
            if (!shoot_type_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Shoot type label is null");
                return 0;
            }
            if (std::strlen(shoot_type_label) == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Shoot type label cannot be empty");
                return 0;
            }

            // Convert rotation array to AxisRotation
            AxisRotation rotation(shoot_base_rotation[0], shoot_base_rotation[1], shoot_base_rotation[2]);

            return plantarch->addChildShoot(plantID, parent_shoot_ID, parent_node_index, current_node_number, rotation, internode_radius, internode_length_max, internode_length_scale_factor_fraction, leaf_scale_factor_fraction, radius_taper, std::string(shoot_type_label), petiole_index);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::addChildShoot): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::addChildShoot): Unknown error adding child shoot.");
            return 0;
        }
    }

    // Get current shoot parameters as JSON
    PYHELIOS_API const char* getCurrentShootParametersJSON(PlantArchitecture* plantarch, const char* shoot_type_label) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return nullptr;
            }
            if (!shoot_type_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Shoot type label is null");
                return nullptr;
            }

            ShootParameters params = plantarch->getCurrentShootParameters(std::string(shoot_type_label));
            nlohmann::json j = shootParametersToJSON(params);

            static thread_local std::string json_string;
            json_string = j.dump();
            return json_string.c_str();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getCurrentShootParameters): ") + e.what());
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getCurrentShootParameters): Unknown error.");
            return nullptr;
        }
    }

    // Phenological control functions
    PYHELIOS_API int setPlantPhenologicalThresholds(
        PlantArchitecture* plantarch,
        unsigned int plantID,
        float time_to_dormancy_break,
        float time_to_flower_initiation,
        float time_to_flower_opening,
        float time_to_fruit_set,
        float time_to_fruit_maturity,
        float time_to_dormancy,
        float max_leaf_lifespan
    ) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }

            plantarch->setPlantPhenologicalThresholds(
                plantID,
                time_to_dormancy_break,
                time_to_flower_initiation,
                time_to_flower_opening,
                time_to_fruit_set,
                time_to_fruit_maturity,
                time_to_dormancy,
                max_leaf_lifespan
            );
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setPlantPhenologicalThresholds): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setPlantPhenologicalThresholds): Unknown error.");
            return -1;
        }
    }

    // Plant state query functions
    PYHELIOS_API float getPlantAge(PlantArchitecture* plantarch, unsigned int plantID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1.0f;
            }
            return plantarch->getPlantAge(plantID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getPlantAge): ") + e.what());
            return -1.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getPlantAge): Unknown error.");
            return -1.0f;
        }
    }

    PYHELIOS_API float getPlantHeight(PlantArchitecture* plantarch, unsigned int plantID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1.0f;
            }
            return plantarch->getPlantHeight(plantID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getPlantHeight): ") + e.what());
            return -1.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getPlantHeight): Unknown error.");
            return -1.0f;
        }
    }

    PYHELIOS_API float sumPlantLeafArea(PlantArchitecture* plantarch, unsigned int plantID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1.0f;
            }
            return plantarch->sumPlantLeafArea(plantID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::sumPlantLeafArea): ") + e.what());
            return -1.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::sumPlantLeafArea): Unknown error.");
            return -1.0f;
        }
    }

    // Define shoot type from JSON
    PYHELIOS_API int defineShootTypeFromJSON(PlantArchitecture* plantarch, helios::Context* context, const char* shoot_type_label, const char* json_params) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return -1;
            }
            if (!shoot_type_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Shoot type label is null");
                return -1;
            }
            if (!json_params) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "JSON parameters are null");
                return -1;
            }

            nlohmann::json j = nlohmann::json::parse(json_params);
            // Use context's random generator
            std::minstd_rand0* generator = context->getRandomGenerator();
            ShootParameters params = jsonToShootParameters(j, generator);
            plantarch->defineShootType(std::string(shoot_type_label), params);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::defineShootType): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::defineShootType): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API void plantarch_setProgressCallback(PlantArchitecture* pa_ptr, void (*callback)(float, const char*)) {
        try {
            clearError();
            if (!pa_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return;
            }
            if (callback) {
                pa_ptr->setProgressCallback([callback](float progress, const std::string& msg) {
                    callback(progress, msg.c_str());
                });
            } else {
                pa_ptr->setProgressCallback(nullptr);
            }
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME,
                     std::string("ERROR (plantarch_setProgressCallback): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN,
                     "ERROR (plantarch_setProgressCallback): Unknown error.");
        }
    }

} // extern "C"

#endif // PLANTARCHITECTURE_PLUGIN_AVAILABLE