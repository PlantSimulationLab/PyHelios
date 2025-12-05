/**
 * @file pyhelios_wrapper_weberpenntree.h
 * @brief WeberPennTree functions for PyHelios C wrapper
 * 
 * This header provides procedural tree generation capabilities using
 * Weber-Penn algorithms for realistic tree modeling and simulation.
 */

#ifndef PYHELIOS_WRAPPER_WEBERPENNTREE_H
#define PYHELIOS_WRAPPER_WEBERPENNTREE_H

#include "pyhelios_wrapper_common.h"

// Forward declarations for WeberPennTree interface
class WeberPennTree;
namespace helios {
    class Context;
}

#ifdef __cplusplus
extern "C" {
#endif

//=============================================================================
// WeberPennTree Functions
//=============================================================================

/**
 * @brief Create a WeberPennTree instance
 * @param context Pointer to the Helios Context
 * @return Pointer to the created WeberPennTree
 */
PYHELIOS_API WeberPennTree* createWeberPennTree(helios::Context* context);

/**
 * @brief Create a WeberPennTree instance with build directory
 * @param context Pointer to the Helios Context
 * @param buildDirectory Path to the build directory
 * @return Pointer to the created WeberPennTree
 */
PYHELIOS_API WeberPennTree* createWeberPennTreeWithBuildPluginRootDirectory(helios::Context* context, const char* buildDirectory);

/**
 * @brief Destroy a WeberPennTree instance
 * @param wpt Pointer to the WeberPennTree to destroy
 */
PYHELIOS_API void destroyWeberPennTree(WeberPennTree* wpt);

/**
 * @brief Build a tree with specified name and origin
 * @param wpt Pointer to the WeberPennTree
 * @param treename Name of the tree type to build
 * @param origin Array of 3 floats [x, y, z] for tree origin
 * @return Tree ID
 */
PYHELIOS_API unsigned int buildTree(WeberPennTree* wpt, const char* treename, float* origin);

/**
 * @brief Build a tree with specified name, origin, and scale
 * @param wpt Pointer to the WeberPennTree
 * @param treename Name of the tree type to build
 * @param origin Array of 3 floats [x, y, z] for tree origin
 * @param scale Scale factor for the tree
 * @return Tree ID
 */
PYHELIOS_API unsigned int buildTreeWithScale(WeberPennTree* wpt, const char* treename, float* origin, float scale);

/**
 * @brief Get UUIDs of trunk primitives for a tree
 * @param wpt Pointer to the WeberPennTree
 * @param treeID ID of the tree
 * @param size Pointer to store the number of UUIDs returned
 * @return Pointer to array of UUIDs
 */
PYHELIOS_API unsigned int* getWeberPennTreeTrunkUUIDs(WeberPennTree* wpt, unsigned int treeID, unsigned int* size);

/**
 * @brief Get UUIDs of branch primitives for a tree
 * @param wpt Pointer to the WeberPennTree
 * @param treeID ID of the tree
 * @param size Pointer to store the number of UUIDs returned
 * @return Pointer to array of UUIDs
 */
PYHELIOS_API unsigned int* getWeberPennTreeBranchUUIDs(WeberPennTree* wpt, unsigned int treeID, unsigned int* size);

/**
 * @brief Get UUIDs of leaf primitives for a tree
 * @param wpt Pointer to the WeberPennTree
 * @param treeID ID of the tree
 * @param size Pointer to store the number of UUIDs returned
 * @return Pointer to array of UUIDs
 */
PYHELIOS_API unsigned int* getWeberPennTreeLeafUUIDs(WeberPennTree* wpt, unsigned int treeID, unsigned int* size);

/**
 * @brief Get UUIDs of all primitives for a tree
 * @param wpt Pointer to the WeberPennTree
 * @param treeID ID of the tree
 * @param size Pointer to store the number of UUIDs returned
 * @return Pointer to array of UUIDs
 */
PYHELIOS_API unsigned int* getWeberPennTreeAllUUIDs(WeberPennTree* wpt, unsigned int treeID, unsigned int* size);

/**
 * @brief Set branch recursion level
 * @param wpt Pointer to the WeberPennTree
 * @param level Recursion level for branches
 */
PYHELIOS_API void setBranchRecursionLevel(WeberPennTree* wpt, unsigned int level);

/**
 * @brief Set trunk segment resolution
 * @param wpt Pointer to the WeberPennTree
 * @param trunk_segs Number of segments for trunk
 */
PYHELIOS_API void setTrunkSegmentResolution(WeberPennTree* wpt, unsigned int trunk_segs);

/**
 * @brief Set branch segment resolution
 * @param wpt Pointer to the WeberPennTree
 * @param branch_segs Number of segments for branches
 */
PYHELIOS_API void setBranchSegmentResolution(WeberPennTree* wpt, unsigned int branch_segs);

/**
 * @brief Set leaf subdivisions
 * @param wpt Pointer to the WeberPennTree
 * @param leaf_segs_x Number of subdivisions in x direction
 * @param leaf_segs_y Number of subdivisions in y direction
 */
PYHELIOS_API void setLeafSubdivisions(WeberPennTree* wpt, unsigned int leaf_segs_x, unsigned int leaf_segs_y);

/**
 * @brief Load custom tree species from XML file
 * @param wpt Pointer to the WeberPennTree
 * @param filename Path to XML file containing tree definitions
 * @param silent If true, suppress console output during loading
 */
PYHELIOS_API void loadXMLWeberPennTree(WeberPennTree* wpt, const char* filename, bool silent);

#ifdef __cplusplus
}
#endif

#endif // PYHELIOS_WRAPPER_WEBERPENNTREE_H