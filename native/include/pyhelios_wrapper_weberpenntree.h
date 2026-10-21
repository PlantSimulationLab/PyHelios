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
#include <stdint.h>

// Sizes of the flat arrays used to exchange WeberPennTreeParameters with Python.
// Field order is documented on getWeberPennTreeParameters() below and must match
// pyhelios/wrappers/UWeberPennTreeWrapper.py.
#define WPT_PARAM_NUM_FLOATS 17
#define WPT_PARAM_NUM_INTS 7
#define WPT_PARAM_NUM_FLOAT_VECTORS 14
#define WPT_PARAM_NUM_INT_VECTORS 2
#define WPT_PARAM_NUM_STRINGS 3

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

/**
 * @brief Get the architectural parameters of a tree in the library
 *
 * The struct is flattened into fixed-order arrays:
 * - scalars[17]: BaseSize, BaseSizeV, BaseSplitSize, BaseSplitSizeV, Scale, ScaleV, ZScale, ZScaleV, Ratio, RatioPower,
 *   LobeDepth, Flare, LeafScale, LeafScaleX, WoodColor.r, WoodColor.g, WoodColor.b
 * - ints[7]: Shape, BaseSplits, BaseSplitsV, Lobes, Levels, Leaves, LeafShape
 * - float vectors[14] (lengths in fvec_lengths, concatenated in *fvec_data): nSegSplits, nSplitAngle, nSplitAngleV, nCurve,
 *   nCurveV, nCurveBack, nLength, nLengthV, nTaper, nDownAngle, nDownAngleV, nRotate, nRotateV, leafAngleCDF
 * - int vectors[2] (lengths in ivec_lengths, concatenated in *ivec_data): nCurveRes, nBranches
 * - strings[3]: label, LeafFile, WoodFile
 * Returned data pointers refer to thread-local buffers valid until the next call on the same thread.
 */
PYHELIOS_API void getWeberPennTreeParameters(WeberPennTree* wpt, const char* treename, float* scalars, int64_t* ints,
                                             unsigned int* fvec_lengths, float** fvec_data,
                                             unsigned int* ivec_lengths, int** ivec_data,
                                             const char** strings);

/**
 * @brief Set the architectural parameters of a tree, adding it to the library if the name is new
 *
 * Arrays use the same layout as getWeberPennTreeParameters().
 */
PYHELIOS_API void setWeberPennTreeParameters(WeberPennTree* wpt, const char* treename, const float* scalars, const int64_t* ints,
                                             const unsigned int* fvec_lengths, const float* fvec_data,
                                             const unsigned int* ivec_lengths, const int* ivec_data,
                                             const char* label, const char* leaf_file, const char* wood_file);

/**
 * @brief Seed the WeberPennTree random number generator (independent of the Context generator)
 * @param wpt Pointer to the WeberPennTree
 * @param seed Random number seed
 */
PYHELIOS_API void seedWeberPennTreeRandomGenerator(WeberPennTree* wpt, unsigned int seed);

#ifdef __cplusplus
}
#endif

#endif // PYHELIOS_WRAPPER_WEBERPENNTREE_H