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
// Advance a single plant, a subset of plants, or all plants by whole years plus days.
PYHELIOS_API int advanceTimeForPlant(PlantArchitecture* plantarch, unsigned int plantID, float dt);
PYHELIOS_API int advanceTimeForPlants(PlantArchitecture* plantarch, unsigned int* plantIDs, int count, float dt);
PYHELIOS_API int advanceTimeYears(PlantArchitecture* plantarch, int time_step_years, float time_step_days);

// Attraction points steer shoot growth toward targets. plantID < 0 selects the global form.
// Points are a flat array of 3*point_count floats (x,y,z per point).
PYHELIOS_API int enableAttractionPoints(PlantArchitecture* plantarch, int plantID, float* points, int point_count, float view_half_angle_deg, float look_ahead_distance, float attraction_weight);
PYHELIOS_API int disableAttractionPoints(PlantArchitecture* plantarch, int plantID);
PYHELIOS_API int updateAttractionPoints(PlantArchitecture* plantarch, int plantID, float* points, int point_count);
PYHELIOS_API int appendAttractionPoints(PlantArchitecture* plantarch, int plantID, float* points, int point_count);
PYHELIOS_API int setAttractionParameters(PlantArchitecture* plantarch, int plantID, float view_half_angle_deg, float look_ahead_distance, float attraction_weight, float obstacle_reduction_factor);

// Custom plant building functions
PYHELIOS_API unsigned int addPlantInstance(PlantArchitecture* plantarch, float* base_position, float current_age);
PYHELIOS_API int deletePlantInstance(PlantArchitecture* plantarch, unsigned int plantID);
PYHELIOS_API unsigned int addBaseStemShoot(PlantArchitecture* plantarch, unsigned int plantID, unsigned int current_node_number, float* base_rotation, float internode_radius, float internode_length_max, float internode_length_scale_factor_fraction, float leaf_scale_factor_fraction, float radius_taper, const char* shoot_type_label);
PYHELIOS_API unsigned int appendShoot(PlantArchitecture* plantarch, unsigned int plantID, int parent_shoot_ID, unsigned int current_node_number, float* base_rotation, float internode_radius, float internode_length_max, float internode_length_scale_factor_fraction, float leaf_scale_factor_fraction, float radius_taper, const char* shoot_type_label);
PYHELIOS_API unsigned int addChildShoot(PlantArchitecture* plantarch, unsigned int plantID, int parent_shoot_ID, unsigned int parent_node_index, unsigned int current_node_number, float* shoot_base_rotation, float internode_radius, float internode_length_max, float internode_length_scale_factor_fraction, float leaf_scale_factor_fraction, float radius_taper, const char* shoot_type_label, unsigned int petiole_index);

// Plant query functions
PYHELIOS_API int getAvailablePlantModels(PlantArchitecture* plantarch, char*** model_names, int* count);
// Shoot type labels. Pass plant_model_name = nullptr and plantID = -1 for the currently loaded
// model, a model name to query one without loading it, or plantID >= 0 for a plant instance.
// Caller frees the result with freeStringArray().
PYHELIOS_API int listShootTypeLabels(PlantArchitecture* plantarch, const char* plant_model_name, int plantID, char*** labels, int* count);
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

// Scene-wide organ queries across every plant. Thread-local static storage; do NOT free.
PYHELIOS_API unsigned int* plantArchitectureGetAllUUIDs(PlantArchitecture* plantarch, int* count);
PYHELIOS_API unsigned int* getAllLeafUUIDs(PlantArchitecture* plantarch, int* count);
PYHELIOS_API unsigned int* getAllInternodeUUIDs(PlantArchitecture* plantarch, int* count);
PYHELIOS_API unsigned int* getAllPetioleUUIDs(PlantArchitecture* plantarch, int* count);
PYHELIOS_API unsigned int* getAllPeduncleUUIDs(PlantArchitecture* plantarch, int* count);
PYHELIOS_API unsigned int* getAllFlowerUUIDs(PlantArchitecture* plantarch, int* count);
PYHELIOS_API unsigned int* getAllFruitUUIDs(PlantArchitecture* plantarch, int* count);
PYHELIOS_API unsigned int* plantArchitectureGetAllObjectIDs(PlantArchitecture* plantarch, int* count);
PYHELIOS_API unsigned int* getAllPlantIDs(PlantArchitecture* plantarch, int* count);

// Shoot topology inspection (read-only). All return thread-local static storage; do NOT free.
PYHELIOS_API unsigned int* getAllPlantShootIDs(PlantArchitecture* plantarch, unsigned int plantID, int* count);
PYHELIOS_API void getPlantShootTopology(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, int* out);
PYHELIOS_API int* getPlantShootChildIDs(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, int* count);
// *count is set to the number of VERTICES; the returned buffer holds 3*count floats (x,y,z per vertex).
PYHELIOS_API float* getPlantShootInternodeVertices(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, int* count);
// *count is set to the number of radius values (one per vertex, i.e. equal to the vertex count).
PYHELIOS_API float* getPlantShootInternodeRadii(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, int* count);

// Shoot hierarchy accessors (helios-core 1.3.82). Array returns use thread-local static
// storage; do NOT free. Scalar returns use an out-param and report failure via getLastErrorCode().
// Returns the ID of the shoot this shoot grew from, or -1 for the base stem shoot.
PYHELIOS_API int getParentShootID(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID);
// Branching order: base stem is 0, a branch off it is 1. Axis continuations from appendShoot()
// keep the parent's rank, so this is not the same as getShootDepth().
PYHELIOS_API unsigned int getShootRank(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID);
// Number of steps through the shoot tree to the base stem shoot, counting axis continuations.
PYHELIOS_API unsigned int getShootDepth(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID);
// Shoot IDs from the given shoot to the base stem shoot inclusive.
PYHELIOS_API unsigned int* getPathToRoot(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, int* count);
// Direct children of a shoot, ordered by the node they attach to. Excludes pruned shoots.
PYHELIOS_API unsigned int* getChildShootIDs(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, int* count);
// All descendants depth-first, excluding the shoot itself and any pruned shoots.
PYHELIOS_API unsigned int* getAllDescendantShootIDs(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, int* count);
// Shoot IDs grouped by rank. Returned flat, with *group_count groups whose lengths are written
// to *group_sizes (also thread-local static, do NOT free). Group i holds the shoots of rank i, and
// a rank with no live shoots is an empty group, so the group index always equals the rank.
PYHELIOS_API unsigned int* getShootIDsByRank(PlantArchitecture* plantarch, unsigned int plantID, int** group_sizes, int* group_count, int* total_count);
// Parent-to-children map. Parent IDs are written to *parent_ids and the child IDs of parent i are
// the next (*group_sizes)[i] entries of the returned flat child buffer. Only shoots that have
// children appear. All three buffers are thread-local static; do NOT free.
PYHELIOS_API unsigned int* getShootHierarchyMap(PlantArchitecture* plantarch, unsigned int plantID, unsigned int** parent_ids, int** group_sizes, int* parent_count, int* total_children);
// Shoots with no children. Excludes pruned shoots.
PYHELIOS_API unsigned int* getTerminalShootIDs(PlantArchitecture* plantarch, unsigned int plantID, int* count);
// 1 if the shoot was pruned away entirely, 0 if it is live, -1 on error.
PYHELIOS_API int isShootPruned(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID);

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

// Dormancy control functions
PYHELIOS_API int makePlantDormant(PlantArchitecture* plantarch, unsigned int plantID);
PYHELIOS_API int breakPlantDormancy(PlantArchitecture* plantarch, unsigned int plantID);
// Returns 1 if dormant, 0 if not, -1 on error (check the error code to disambiguate).
PYHELIOS_API int isPlantDormant(PlantArchitecture* plantarch, unsigned int plantID);

// Pruning and organ removal functions
// pruneBranch removes the phytomer at node_index and everything distal to it,
// recursing into every child shoot of the pruned nodes.
PYHELIOS_API int pruneBranch(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index);
// harvestPlant removes flowers and fruit only; leaves are left in place.
PYHELIOS_API int harvestPlant(PlantArchitecture* plantarch, unsigned int plantID);
PYHELIOS_API int removeShootLeaves(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID);
PYHELIOS_API int removeShootVegetativeBuds(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID);
PYHELIOS_API int removeShootFloralBuds(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID);
PYHELIOS_API int removePlantLeaves(PlantArchitecture* plantarch, unsigned int plantID);

// Plant state query functions
PYHELIOS_API float getPlantAge(PlantArchitecture* plantarch, unsigned int plantID);
// Maximum age in days beyond which the plant stops growing (helios-core 1.3.82).
PYHELIOS_API float getPlantMaxAge(PlantArchitecture* plantarch, unsigned int plantID);
PYHELIOS_API int setPlantMaxAge(PlantArchitecture* plantarch, unsigned int plantID, float max_age);
PYHELIOS_API float getPlantHeight(PlantArchitecture* plantarch, unsigned int plantID);
PYHELIOS_API float sumPlantLeafArea(PlantArchitecture* plantarch, unsigned int plantID);

// ---- Reconstruction from measured geometry (helios-core 1.3.85) ----
// Build a shoot whose internode path follows caller-supplied node positions (a QSM, a digitized
// skeleton, photogrammetry) instead of being generated from the shoot type's curvature/tortuosity.
// node_positions is a flat array of 3*node_count floats (x,y,z per node, base first); node_radii has
// node_count entries. N+1 nodes define N phytomers. parent_shoot_ID = -1 creates a base stem shoot.
// growth_shoot_type_label selects the two-type overload: NULL or "" grows the shoot with the build type,
// otherwise the named type governs node caps, apical curvature and the type of shoots its buds produce.
// Returns the new shoot ID, or 0 with an error set (check getLastErrorCode()).
PYHELIOS_API unsigned int addShootFromNodePositions(PlantArchitecture* plantarch, unsigned int plantID, int parent_shoot_ID, unsigned int parent_node_index, const float* node_positions, const float* node_radii, int node_count, const char* shoot_type_label, const char* growth_shoot_type_label, unsigned int petiole_index);
// Prescribe the centerline of one petiole from measured node positions (flat 3*node_count floats, base
// first) and radii (node_count entries). The first position is snapped onto the parent internode tip.
// Returns 0 on success, -1 on error.
PYHELIOS_API int setPetioleNodePositions(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index, const float* node_positions, const float* node_radii, int node_count);
// Prescribe the base position, orientation and size of every leaf on one petiole. leaf_bases is a flat
// array of 3*leaf_count floats; leaf_rotations is a flat array of 3*leaf_count floats holding
// (pitch, yaw, roll) in RADIANS in the petiole/internode frame (AxisRotation field order); leaf_sizes has
// leaf_count entries. leaf_count must equal the number of leaves already on the petiole. Returns 0 on
// success, -1 on error.
PYHELIOS_API int setPetioleLeafGeometry(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index, const float* leaf_bases, const float* leaf_rotations, const float* leaf_sizes, int leaf_count);
// 1 if the shoot was built by addShootFromNodePositions(), 0 if its geometry was generated, -1 on error.
PYHELIOS_API int isShootGeometryPrescribed(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID);

// ---- helios-core 1.3.86 additions ----
// Change the number of leaves (leaflets) on one petiole of an existing phytomer, rebuilding them
// procedurally. Call before setPetioleLeafGeometry() for the same petiole. leaf_count must be >= 1.
// Returns 0 on success, -1 on error.
PYHELIOS_API int setPetioleLeafCount(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index, unsigned int leaf_count);
// Set the target length of internodes grown at the apex of an existing shoot. A shoot built by
// addShootFromNodePositions() otherwise grows toward the mean of its prescribed internode lengths.
// NOTE: this value is NOT saved by writePlantStructureXML(), so it must be set again after
// readPlantStructureXML(). internode_length_max must be > 0. Returns 0 on success, -1 on error.
PYHELIOS_API int setShootInternodeLengthMax(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, float internode_length_max);

// ---- Built-geometry organ queries (helios-core 1.3.85) ----
// Measured from the geometry actually built, one entry per organ, visited shoot by shoot and then
// phytomer by phytomer. All return thread-local static storage; do NOT free.
// One-sided area (m^2) of each leaf at its present size; leaves without geometry are omitted.
PYHELIOS_API float* getPlantLeafAreas(PlantArchitecture* plantarch, unsigned int plantID, int* count);
// Length (m) of each internode measured along its built node positions; one entry per phytomer.
PYHELIOS_API float* getPlantInternodeLengths(PlantArchitecture* plantarch, unsigned int plantID, int* count);
// Inclination (degrees, 0 = horizontal, folded to [0,90]) of each leaf from its area-weighted normal.
PYHELIOS_API float* getPlantLeafInclinations(PlantArchitecture* plantarch, unsigned int plantID, int* count);

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