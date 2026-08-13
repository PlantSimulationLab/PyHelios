// PyHelios C Interface - PlantArchitecture Functions
// Provides procedural plant modeling using plant architecture library

#ifndef PYHELIOS_WRAPPER_PLANTARCHITECTURE_H
#define PYHELIOS_WRAPPER_PLANTARCHITECTURE_H

#include "pyhelios_wrapper_common.h"

#ifdef PLANTARCHITECTURE_PLUGIN_AVAILABLE

#ifdef __cplusplus
extern "C" {
#endif

// Forward declaration
struct PlantArchitecture;

// PlantArchitecture management functions
PYHELIOS_API PlantArchitecture* createPlantArchitecture(helios::Context* context);
PYHELIOS_API void destroyPlantArchitecture(PlantArchitecture* plantarch);

// Plant library functions
PYHELIOS_API int loadPlantModelFromLibrary(PlantArchitecture* plantarch, const char* plant_label);
PYHELIOS_API unsigned int buildPlantInstanceFromLibrary(PlantArchitecture* plantarch, float* base_position, float age, char** param_keys, float* param_values, int param_count);
PYHELIOS_API int buildPlantCanopyFromLibrary(PlantArchitecture* plantarch, float* canopy_center, float* plant_spacing, int* plant_count, float age, float germination_rate, unsigned int** plant_ids, int* num_plants, char** param_keys, float* param_values, int param_count_params);
PYHELIOS_API int advanceTime(PlantArchitecture* plantarch, float dt);

// Custom plant building functions
PYHELIOS_API unsigned int addPlantInstance(PlantArchitecture* plantarch, float* base_position, float current_age);
PYHELIOS_API int deletePlantInstance(PlantArchitecture* plantarch, unsigned int plantID);
PYHELIOS_API unsigned int addBaseStemShoot(PlantArchitecture* plantarch, unsigned int plantID, unsigned int current_node_number, float* base_rotation, float internode_radius, float internode_length_max, float internode_length_scale_factor_fraction, float leaf_scale_factor_fraction, float radius_taper, const char* shoot_type_label);
PYHELIOS_API unsigned int appendShoot(PlantArchitecture* plantarch, unsigned int plantID, int parent_shoot_ID, unsigned int current_node_number, float* base_rotation, float internode_radius, float internode_length_max, float internode_length_scale_factor_fraction, float leaf_scale_factor_fraction, float radius_taper, const char* shoot_type_label);
PYHELIOS_API unsigned int addChildShoot(PlantArchitecture* plantarch, unsigned int plantID, int parent_shoot_ID, unsigned int parent_node_index, unsigned int current_node_number, float* shoot_base_rotation, float internode_radius, float internode_length_max, float internode_length_scale_factor_fraction, float leaf_scale_factor_fraction, float radius_taper, const char* shoot_type_label, unsigned int petiole_index);

// Plant query functions
PYHELIOS_API int getAvailablePlantModels(PlantArchitecture* plantarch, char*** model_names, int* count);
PYHELIOS_API unsigned int* getAllPlantObjectIDs(PlantArchitecture* plantarch, unsigned int plantID, int* count);
PYHELIOS_API unsigned int* getAllPlantUUIDs(PlantArchitecture* plantarch, unsigned int plantID, bool include_hidden, int* count);
// Leaf queries. Both return thread-local static storage; do NOT free.
PYHELIOS_API unsigned int* getPlantLeafObjectIDs(PlantArchitecture* plantarch, unsigned int plantID, int* count);
// *count is set to the number of BASE POSITIONS; the returned buffer holds 3*count floats (x,y,z each).
PYHELIOS_API float* getPlantLeafBases(PlantArchitecture* plantarch, unsigned int plantID, int* count);

// Remaining organ queries. All return thread-local static storage; do NOT free.
// An organ absent at the plant's current growth stage yields *count == 0 and a valid
// (empty) buffer, which is not an error condition -- callers must not treat an empty
// result as a failure. Reproductive organs in particular exist only once the plant
// reaches the corresponding stage.
PYHELIOS_API unsigned int* getPlantPetioleObjectIDs(PlantArchitecture* plantarch, unsigned int plantID, int* count);
PYHELIOS_API unsigned int* getPlantPeduncleObjectIDs(PlantArchitecture* plantarch, unsigned int plantID, int* count);
PYHELIOS_API unsigned int* getPlantFlowerObjectIDs(PlantArchitecture* plantarch, unsigned int plantID, int* count);
PYHELIOS_API unsigned int* getPlantFruitObjectIDs(PlantArchitecture* plantarch, unsigned int plantID, int* count);

// Shoot topology inspection (read-only). All return thread-local static storage; do NOT free.
PYHELIOS_API unsigned int* getAllPlantShootIDs(PlantArchitecture* plantarch, unsigned int plantID, int* count);
PYHELIOS_API void getPlantShootTopology(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, int* out);
PYHELIOS_API int* getPlantShootChildIDs(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, int* count);
// *count is set to the number of VERTICES; the returned buffer holds 3*count floats (x,y,z per vertex).
PYHELIOS_API float* getPlantShootInternodeVertices(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, int* count);
// *count is set to the number of radius values (one per vertex, i.e. equal to the vertex count).
PYHELIOS_API float* getPlantShootInternodeRadii(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, int* count);

// Memory cleanup functions
PYHELIOS_API void freeStringArray(char** strings, int count);
PYHELIOS_API void freeIntArray(unsigned int* array);

// Message control
// Prefixed with "plantArchitecture" because the visualizer wrapper already
// exports plain enableMessages/disableMessages with C linkage.
PYHELIOS_API void plantArchitectureEnableMessages(PlantArchitecture* plantarch);
PYHELIOS_API void plantArchitectureDisableMessages(PlantArchitecture* plantarch);

// Ground clipping
PYHELIOS_API void enableGroundClipping(PlantArchitecture* plantarch, float ground_height);

// Collision detection functions
PYHELIOS_API int enableSoftCollisionAvoidance(PlantArchitecture* plantarch, const unsigned int* target_UUIDs, int uuid_count, const unsigned int* target_IDs, int id_count, bool enable_petiole, bool enable_fruit);
PYHELIOS_API void disableCollisionDetection(PlantArchitecture* plantarch);
PYHELIOS_API void setSoftCollisionAvoidanceParameters(PlantArchitecture* plantarch, float view_half_angle_deg, float look_ahead_distance, int sample_count, float inertia_weight);
PYHELIOS_API void setCollisionRelevantOrgans(PlantArchitecture* plantarch, bool include_internodes, bool include_leaves, bool include_petioles, bool include_flowers, bool include_fruit);
PYHELIOS_API int enableSolidObstacleAvoidance(PlantArchitecture* plantarch, const unsigned int* obstacle_UUIDs, int uuid_count, float avoidance_distance, bool enable_fruit_adjustment, bool enable_obstacle_pruning);
PYHELIOS_API int setStaticObstacles(PlantArchitecture* plantarch, const unsigned int* target_UUIDs, int uuid_count);
PYHELIOS_API unsigned int* getPlantCollisionRelevantObjectIDs(PlantArchitecture* plantarch, unsigned int plant_id, int* count);

// File I/O functions
PYHELIOS_API int writePlantMeshVertices(PlantArchitecture* plantarch, unsigned int plantID, const char* filename);
PYHELIOS_API int writePlantStructureXML(PlantArchitecture* plantarch, unsigned int plantID, const char* filename);
PYHELIOS_API int writeQSMCylinderFile(PlantArchitecture* plantarch, unsigned int plantID, const char* filename);
PYHELIOS_API int writePlantStructureUSD(PlantArchitecture* plantarch, unsigned int plantID, const char* filename,
                                         float elastic_modulus, float wood_density, float damping_ratio,
                                         float static_friction, float dynamic_friction, float restitution,
                                         float organ_spring_stiffness, float organ_spring_damping,
                                         float leaf_mass_per_area, float fruit_mass, float flower_mass,
                                         unsigned int solver_position_iterations, float min_segment_length);
PYHELIOS_API int registerGrowthFrame(PlantArchitecture* plantarch, unsigned int plantID, float min_segment_length);
PYHELIOS_API int writePlantGrowthUSD(PlantArchitecture* plantarch, unsigned int plantID, const char* filename, float seconds_per_frame);
PYHELIOS_API int clearGrowthFrames(PlantArchitecture* plantarch, unsigned int plantID);
PYHELIOS_API unsigned int getGrowthFrameCount(PlantArchitecture* plantarch, unsigned int plantID);
PYHELIOS_API int readPlantStructureXML(PlantArchitecture* plantarch, const char* filename, bool quiet, unsigned int** plant_ids, int* num_plants);

// Parameter management functions
PYHELIOS_API const char* getCurrentShootParametersJSON(PlantArchitecture* plantarch, const char* shoot_type_label);
PYHELIOS_API int defineShootTypeFromJSON(PlantArchitecture* plantarch, helios::Context* context, const char* shoot_type_label, const char* json_params);

// Carbohydrate / nitrogen model parameters (get returns default-constructed template; set applies to a plant)
PYHELIOS_API const char* getDefaultCarbohydrateParametersJSON();
PYHELIOS_API int setPlantCarbohydrateParametersFromJSON(PlantArchitecture* plantarch, unsigned int plantID, const char* json_params);
PYHELIOS_API const char* getDefaultNitrogenParametersJSON();
PYHELIOS_API int setPlantNitrogenParametersFromJSON(PlantArchitecture* plantarch, unsigned int plantID, const char* json_params);

// Phenological control functions
PYHELIOS_API int setPlantPhenologicalThresholds(PlantArchitecture* plantarch, unsigned int plantID, float time_to_dormancy_break, float time_to_flower_initiation, float time_to_flower_opening, float time_to_fruit_set, float time_to_fruit_maturity, float time_to_dormancy, float max_leaf_lifespan, int is_evergreen);
PYHELIOS_API int disablePlantPhenology(PlantArchitecture* plantarch, unsigned int plantID);

// Plant state query functions
PYHELIOS_API float getPlantAge(PlantArchitecture* plantarch, unsigned int plantID);
PYHELIOS_API float getPlantHeight(PlantArchitecture* plantarch, unsigned int plantID);
PYHELIOS_API float sumPlantLeafArea(PlantArchitecture* plantarch, unsigned int plantID);

// Progress callback
PYHELIOS_API void plantarch_setProgressCallback(PlantArchitecture* pa_ptr, void (*callback)(float, const char*));

// Cancellation flag — set before a build/canopy/advanceTime call so a non-zero
// flag (written from another thread) stops the build between plants/timesteps.
PYHELIOS_API void plantarch_setCancelFlag(PlantArchitecture* pa_ptr, volatile int* flag);

#ifdef __cplusplus
}
#endif

#endif // PLANTARCHITECTURE_PLUGIN_AVAILABLE

#endif // PYHELIOS_WRAPPER_PLANTARCHITECTURE_H