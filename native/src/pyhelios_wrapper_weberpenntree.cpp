// PyHelios C Interface - WeberPennTree Functions
// Provides procedural tree generation using Weber-Penn algorithms

#include "../include/pyhelios_wrapper_common.h"
#include "../include/pyhelios_wrapper_context.h"
#include "Context.h"
#include <string>
#include <exception>

#ifdef WEBERPENNTREE_PLUGIN_AVAILABLE
#include "../include/pyhelios_wrapper_weberpenntree.h"
#include "WeberPennTree.h"

extern "C" {
    // WeberPennTree C interface functions
    PYHELIOS_API WeberPennTree* createWeberPennTree(helios::Context* context) {
        try {
            clearError();
            return new WeberPennTree(context);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (WeberPennTree::constructor): ") + e.what());
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (WeberPennTree::constructor): Unknown error creating WeberPennTree.");
            return nullptr;
        }
    }
    
    PYHELIOS_API WeberPennTree* createWeberPennTreeWithBuildPluginRootDirectory(helios::Context* context, const char* buildDirectory) {
        try {
            clearError();
            WeberPennTree* wpt = new WeberPennTree(context);
            // Load XML from build directory
            std::string xmlPath = std::string(buildDirectory) + "/plugins/weberpenntree/xml/WeberPennTreeLibrary.xml";
            wpt->loadXML(xmlPath.c_str());
            return wpt;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (WeberPennTree::constructor): ") + e.what());
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (WeberPennTree::constructor): Unknown error creating WeberPennTree.");
            return nullptr;
        }
    }
    
    PYHELIOS_API void destroyWeberPennTree(WeberPennTree* wpt) {
        delete wpt;
    }
    
    PYHELIOS_API unsigned int buildTree(WeberPennTree* wpt, const char* treename, float* origin) {
        try {
            clearError();
            helios::vec3 origin_vec(origin[0], origin[1], origin[2]);
            return wpt->buildTree(treename, origin_vec);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (WeberPennTree::buildTree): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (WeberPennTree::buildTree): Unknown error building tree.");
            return 0;
        }
    }
    
    PYHELIOS_API unsigned int buildTreeWithScale(WeberPennTree* wpt, const char* treename, float* origin, float scale) {
        try {
            clearError();
            helios::vec3 origin_vec(origin[0], origin[1], origin[2]);
            return wpt->buildTree(treename, origin_vec, scale);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (WeberPennTree::buildTree): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (WeberPennTree::buildTree): Unknown error building tree.");
            return 0;
        }
    }
    
    PYHELIOS_API unsigned int* getWeberPennTreeTrunkUUIDs(WeberPennTree* wpt, unsigned int treeID, unsigned int* size) {
        try {
            clearError();
            std::vector<unsigned int> uuids = wpt->getTrunkUUIDs(treeID);
            *size = uuids.size();
            
            static thread_local std::vector<unsigned int> uuid_buffer;
            uuid_buffer = uuids;
            
            return uuid_buffer.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (WeberPennTree::getTrunkUUIDs): ") + e.what());
            *size = 0;
            static thread_local unsigned int error_result[1] = {0};
            return error_result;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (WeberPennTree::getTrunkUUIDs): Unknown error getting trunk UUIDs.");
            *size = 0;
            static thread_local unsigned int error_result[1] = {0};
            return error_result;
        }
    }
    
    PYHELIOS_API unsigned int* getWeberPennTreeBranchUUIDs(WeberPennTree* wpt, unsigned int treeID, unsigned int* size) {
        try {
            clearError();
            std::vector<unsigned int> uuids = wpt->getBranchUUIDs(treeID);
            *size = uuids.size();
            
            static thread_local std::vector<unsigned int> uuid_buffer;
            uuid_buffer = uuids;
            
            return uuid_buffer.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (WeberPennTree::getBranchUUIDs): ") + e.what());
            *size = 0;
            static thread_local unsigned int error_result[1] = {0};
            return error_result;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (WeberPennTree::getBranchUUIDs): Unknown error getting branch UUIDs.");
            *size = 0;
            static thread_local unsigned int error_result[1] = {0};
            return error_result;
        }
    }
    
    PYHELIOS_API unsigned int* getWeberPennTreeLeafUUIDs(WeberPennTree* wpt, unsigned int treeID, unsigned int* size) {
        try {
            clearError();
            std::vector<unsigned int> uuids = wpt->getLeafUUIDs(treeID);
            *size = uuids.size();
            
            static thread_local std::vector<unsigned int> uuid_buffer;
            uuid_buffer = uuids;
            
            return uuid_buffer.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (WeberPennTree::getLeafUUIDs): ") + e.what());
            *size = 0;
            static thread_local unsigned int error_result[1] = {0};
            return error_result;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (WeberPennTree::getLeafUUIDs): Unknown error getting leaf UUIDs.");
            *size = 0;
            static thread_local unsigned int error_result[1] = {0};
            return error_result;
        }
    }
    
    PYHELIOS_API unsigned int* getWeberPennTreeAllUUIDs(WeberPennTree* wpt, unsigned int treeID, unsigned int* size) {
        try {
            clearError();
            std::vector<unsigned int> uuids = wpt->getAllUUIDs(treeID);
            *size = uuids.size();
            
            static thread_local std::vector<unsigned int> uuid_buffer;
            uuid_buffer = uuids;
            
            return uuid_buffer.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (WeberPennTree::getAllUUIDs): ") + e.what());
            *size = 0;
            static thread_local unsigned int error_result[1] = {0};
            return error_result;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (WeberPennTree::getAllUUIDs): Unknown error getting all UUIDs.");
            *size = 0;
            static thread_local unsigned int error_result[1] = {0};
            return error_result;
        }
    }
    
    PYHELIOS_API void setBranchRecursionLevel(WeberPennTree* wpt, unsigned int level) {
        try {
            clearError();
            wpt->setBranchRecursionLevel(level);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (WeberPennTree::setBranchRecursionLevel): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (WeberPennTree::setBranchRecursionLevel): Unknown error setting recursion level.");
        }
    }
    
    PYHELIOS_API void setTrunkSegmentResolution(WeberPennTree* wpt, unsigned int trunk_segs) {
        try {
            clearError();
            wpt->setTrunkSegmentResolution(trunk_segs);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (WeberPennTree::setTrunkSegmentResolution): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (WeberPennTree::setTrunkSegmentResolution): Unknown error setting trunk resolution.");
        }
    }
    
    PYHELIOS_API void setBranchSegmentResolution(WeberPennTree* wpt, unsigned int branch_segs) {
        try {
            clearError();
            wpt->setBranchSegmentResolution(branch_segs);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (WeberPennTree::setBranchSegmentResolution): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (WeberPennTree::setBranchSegmentResolution): Unknown error setting branch resolution.");
        }
    }
    
    PYHELIOS_API void setLeafSubdivisions(WeberPennTree* wpt, unsigned int leaf_segs_x, unsigned int leaf_segs_y) {
        try {
            clearError();
            helios::int2 leaf_segs(leaf_segs_x, leaf_segs_y);
            wpt->setLeafSubdivisions(leaf_segs);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (WeberPennTree::setLeafSubdivisions): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (WeberPennTree::setLeafSubdivisions): Unknown error setting leaf subdivisions.");
        }
    }

    PYHELIOS_API void loadXMLWeberPennTree(WeberPennTree* wpt, const char* filename, bool silent) {
        try {
            clearError();
            wpt->loadXML(filename, silent);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (WeberPennTree::loadXML): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (WeberPennTree::loadXML): Unknown error loading XML file.");
        }
    }

} //extern "C"

#endif //WEBERPENNTREE_PLUGIN_AVAILABLE
