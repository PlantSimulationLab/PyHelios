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

} // extern "C"

#endif // PLANTARCHITECTURE_PLUGIN_AVAILABLE