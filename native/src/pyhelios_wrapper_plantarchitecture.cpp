// PyHelios C Interface - PlantArchitecture Functions
// Provides procedural plant modeling using plant architecture library

#include "../include/pyhelios_wrapper_common.h"
#include "../include/pyhelios_wrapper_context.h"
#include "Context.h"
#include <string>
#include <vector>
#include <exception>
#include <cstring>

#ifdef PLANTARCHITECTURE_PLUGIN_AVAILABLE
#include "../include/pyhelios_wrapper_plantarchitecture.h"
#include "PlantArchitecture.h"

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

    PYHELIOS_API unsigned int buildPlantInstanceFromLibrary(PlantArchitecture* plantarch, float* base_position, float age) {
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
            return plantarch->buildPlantInstanceFromLibrary(position, age);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::buildPlantInstanceFromLibrary): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::buildPlantInstanceFromLibrary): Unknown error building plant instance.");
            return 0;
        }
    }

    PYHELIOS_API int buildPlantCanopyFromLibrary(PlantArchitecture* plantarch, float* canopy_center, float* plant_spacing, int* plant_count, float age, unsigned int** plant_ids, int* num_plants) {
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

            std::vector<uint> plantIDs = plantarch->buildPlantCanopyFromLibrary(center, spacing, count, age);

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

    PYHELIOS_API unsigned int* getAllPlantUUIDs(PlantArchitecture* plantarch, unsigned int plantID, int* count) {
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

            std::vector<uint> uuids = plantarch->getAllPlantUUIDs(plantID);

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

} // extern "C"

#endif // PLANTARCHITECTURE_PLUGIN_AVAILABLE