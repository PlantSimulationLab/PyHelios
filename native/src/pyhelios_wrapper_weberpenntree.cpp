// PyHelios C Interface - WeberPennTree Functions
// Provides procedural tree generation using Weber-Penn algorithms

#include "../include/pyhelios_wrapper_common.h"
#include "../include/pyhelios_wrapper_context.h"
#include "Context.h"
#include <string>
#include <exception>
#include <vector>
#include <cstdio>
#include <cstdint>
#include <fstream>
#include <filesystem>
#include <random>
#include <atomic>

#ifdef WEBERPENNTREE_PLUGIN_AVAILABLE
#include "../include/pyhelios_wrapper_weberpenntree.h"
#include "WeberPennTree.h"

namespace {

    // Field order of the flat parameter arrays exchanged with Python. The order must match
    // WPT_PARAM_FLOAT_FIELDS / WPT_PARAM_INT_FIELDS / WPT_PARAM_FLOAT_VECTOR_FIELDS / WPT_PARAM_INT_VECTOR_FIELDS
    // in pyhelios/wrappers/UWeberPennTreeWrapper.py.

    void packTreeScalars(const WeberPennTreeParameters& p, float* scalars, int64_t* ints) {
        const float s[WPT_PARAM_NUM_FLOATS] = {p.BaseSize, p.BaseSizeV, p.BaseSplitSize, p.BaseSplitSizeV, p.Scale, p.ScaleV, p.ZScale, p.ZScaleV, p.Ratio, p.RatioPower,
                                               p.LobeDepth, p.Flare, p.LeafScale, p.LeafScaleX, p.WoodColor.r, p.WoodColor.g, p.WoodColor.b};
        for (int i = 0; i < WPT_PARAM_NUM_FLOATS; i++) {
            scalars[i] = s[i];
        }
        const int64_t n[WPT_PARAM_NUM_INTS] = {p.Shape, (int64_t) p.BaseSplits, (int64_t) p.BaseSplitsV, p.Lobes, p.Levels, p.Leaves, p.LeafShape};
        for (int i = 0; i < WPT_PARAM_NUM_INTS; i++) {
            ints[i] = n[i];
        }
    }

    std::vector<std::vector<float>*> floatVectorFields(WeberPennTreeParameters& p) {
        return {&p.nSegSplits, &p.nSplitAngle, &p.nSplitAngleV, &p.nCurve, &p.nCurveV, &p.nCurveBack, &p.nLength, &p.nLengthV, &p.nTaper,
                &p.nDownAngle, &p.nDownAngleV, &p.nRotate, &p.nRotateV, &p.leafAngleCDF};
    }

    std::vector<std::vector<int>*> intVectorFields(WeberPennTreeParameters& p) {
        return {&p.nCurveRes, &p.nBranches};
    }

    std::string xmlEscape(const std::string& in) {
        std::string out;
        for (char c : in) {
            switch (c) {
                case '&': out += "&amp;"; break;
                case '<': out += "&lt;"; break;
                case '>': out += "&gt;"; break;
                case '"': out += "&quot;"; break;
                case '\'': out += "&apos;"; break;
                default: out += c;
            }
        }
        return out;
    }

    std::string fmtFloat(float v) {
        char buf[64];
        std::snprintf(buf, sizeof(buf), "%.9g", (double) v);
        return buf;
    }

    // The C++ WeberPennTree API can only overwrite trees that already exist in its library, and the only way to
    // add a new tree is loadXML(). To register a new species name, write a single-tree XML file that carries
    // every value validateTreeParameters() inspects, so that loadXML() accepts it exactly when
    // setTreeParameters() would accept the full parameter set. The caller then overwrites the entry with the
    // exact parameters via setTreeParameters().
    void registerNewTreeName(WeberPennTree* wpt, const std::string& treename, const WeberPennTreeParameters& p) {
        const int levels = p.Levels;
        if (levels < 1 || levels > 3) {
            throw std::runtime_error("Levels for tree " + treename + " is " + std::to_string(levels) + ", but it must be between 1 and 3.");
        }
        const size_t required = (size_t) levels + 1;

        auto floatList = [&](const std::vector<float>& v, const char* name) {
            if (v.size() < required) {
                throw std::runtime_error(std::string(name) + " for tree " + treename + " has " + std::to_string(v.size()) + " entries, but Levels is " + std::to_string(levels) + ", which requires at least " + std::to_string(required) + " entries.");
            }
            std::string s;
            for (size_t i = 0; i < required; i++) {
                s += fmtFloat(v[i]) + " ";
            }
            return s;
        };
        auto intList = [&](const std::vector<int>& v, const char* name) {
            if (v.size() < required) {
                throw std::runtime_error(std::string(name) + " for tree " + treename + " has " + std::to_string(v.size()) + " entries, but Levels is " + std::to_string(levels) + ", which requires at least " + std::to_string(required) + " entries.");
            }
            std::string s;
            for (size_t i = 0; i < required; i++) {
                s += std::to_string(v[i]) + " ";
            }
            return s;
        };

        std::string xml = "<?xml version=\"1.0\"?>\n<helios>\n<WeberPennTree label=\"" + xmlEscape(treename) + "\">\n";
        auto tag = [&](const char* name, const std::string& value) { xml += std::string("  <") + name + ">" + value + "</" + name + ">\n"; };
        tag("Shape", "0");
        tag("BaseSize", fmtFloat(p.BaseSize));
        tag("BaseSplits", "0");
        tag("BaseSplitSize", "0");
        tag("Scale", fmtFloat(p.Scale));
        tag("ScaleV", "0");
        tag("ZScale", "0");
        tag("ZScaleV", "0");
        tag("Ratio", "0");
        tag("RatioPower", "0");
        tag("Lobes", "0");
        tag("LobeDepth", "0");
        tag("Flare", "0");
        tag("Levels", std::to_string(levels));
        tag("nSegSplits", floatList(p.nSegSplits, "nSegSplits"));
        tag("nSplitAngle", floatList(p.nSplitAngle, "nSplitAngle"));
        tag("nSplitAngleV", floatList(p.nSplitAngleV, "nSplitAngleV"));
        tag("nCurveRes", intList(p.nCurveRes, "nCurveRes"));
        tag("nCurve", floatList(p.nCurve, "nCurve"));
        tag("nCurveV", floatList(p.nCurveV, "nCurveV"));
        tag("nCurveBack", floatList(p.nCurveBack, "nCurveBack"));
        tag("nLength", floatList(p.nLength, "nLength"));
        tag("nLengthV", floatList(p.nLengthV, "nLengthV"));
        tag("nTaper", floatList(p.nTaper, "nTaper"));
        tag("nDownAngle", floatList(p.nDownAngle, "nDownAngle"));
        tag("nDownAngleV", floatList(p.nDownAngleV, "nDownAngleV"));
        tag("nRotate", floatList(p.nRotate, "nRotate"));
        tag("nRotateV", floatList(p.nRotateV, "nRotateV"));
        tag("nBranches", intList(p.nBranches, "nBranches"));
        tag("Leaves", "0");
        tag("LeafFile", "placeholder.png");
        tag("LeafScale", fmtFloat(p.LeafScale));
        tag("LeafScaleX", fmtFloat(p.LeafScaleX));
        xml += "</WeberPennTree>\n</helios>\n";

        static std::atomic<unsigned long long> counter{0};
        std::random_device rd;
        const std::filesystem::path path = std::filesystem::temp_directory_path() /
            ("pyhelios_wpt_" + std::to_string(rd()) + "_" + std::to_string(counter++) + ".xml");
        {
            std::ofstream out(path);
            if (!out) {
                throw std::runtime_error("Could not write temporary tree definition file " + path.string() + ".");
            }
            out << xml;
        }
        try {
            wpt->loadXML(path.string().c_str(), true);
        } catch (...) {
            std::error_code ec;
            std::filesystem::remove(path, ec);
            throw;
        }
        std::error_code ec;
        std::filesystem::remove(path, ec);
    }

    bool treeExists(WeberPennTree* wpt, const char* treename) {
        // getTreeParameters() is the only public query for library membership, and reports a missing tree
        // by throwing.
        try {
            (void) wpt->getTreeParameters(treename);
            return true;
        } catch (const std::exception&) {
            return false;
        }
    }

} // namespace

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

    PYHELIOS_API void getWeberPennTreeParameters(WeberPennTree* wpt, const char* treename, float* scalars, int64_t* ints,
                                                 unsigned int* fvec_lengths, float** fvec_data,
                                                 unsigned int* ivec_lengths, int** ivec_data,
                                                 const char** strings) {
        try {
            clearError();
            if (!wpt || !treename || !scalars || !ints || !fvec_lengths || !fvec_data || !ivec_lengths || !ivec_data || !strings) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (WeberPennTree::getTreeParameters): Null pointer argument.");
                return;
            }

            static thread_local WeberPennTreeParameters params_buffer;
            static thread_local std::vector<float> fvec_buffer;
            static thread_local std::vector<int> ivec_buffer;

            params_buffer = wpt->getTreeParameters(treename);

            packTreeScalars(params_buffer, scalars, ints);
            std::vector<std::vector<float>*> fvecs = floatVectorFields(params_buffer);
            std::vector<std::vector<int>*> ivecs = intVectorFields(params_buffer);

            fvec_buffer.clear();
            for (size_t i = 0; i < fvecs.size(); i++) {
                fvec_lengths[i] = (unsigned int) fvecs[i]->size();
                fvec_buffer.insert(fvec_buffer.end(), fvecs[i]->begin(), fvecs[i]->end());
            }
            ivec_buffer.clear();
            for (size_t i = 0; i < ivecs.size(); i++) {
                ivec_lengths[i] = (unsigned int) ivecs[i]->size();
                ivec_buffer.insert(ivec_buffer.end(), ivecs[i]->begin(), ivecs[i]->end());
            }
            *fvec_data = fvec_buffer.data();
            *ivec_data = ivec_buffer.data();

            strings[0] = params_buffer.label.c_str();
            strings[1] = params_buffer.LeafFile.c_str();
            strings[2] = params_buffer.WoodFile.c_str();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (WeberPennTree::getTreeParameters): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (WeberPennTree::getTreeParameters): Unknown error getting tree parameters.");
        }
    }

    PYHELIOS_API void setWeberPennTreeParameters(WeberPennTree* wpt, const char* treename, const float* scalars, const int64_t* ints,
                                                 const unsigned int* fvec_lengths, const float* fvec_data,
                                                 const unsigned int* ivec_lengths, const int* ivec_data,
                                                 const char* label, const char* leaf_file, const char* wood_file) {
        try {
            clearError();
            if (!wpt || !treename || !scalars || !ints || !fvec_lengths || !ivec_lengths || !label || !leaf_file || !wood_file) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (WeberPennTree::setTreeParameters): Null pointer argument.");
                return;
            }

            WeberPennTreeParameters p;
            p.label = label;
            p.LeafFile = leaf_file;
            p.WoodFile = wood_file;

            p.BaseSize = scalars[0];
            p.BaseSizeV = scalars[1];
            p.BaseSplitSize = scalars[2];
            p.BaseSplitSizeV = scalars[3];
            p.Scale = scalars[4];
            p.ScaleV = scalars[5];
            p.ZScale = scalars[6];
            p.ZScaleV = scalars[7];
            p.Ratio = scalars[8];
            p.RatioPower = scalars[9];
            p.LobeDepth = scalars[10];
            p.Flare = scalars[11];
            p.LeafScale = scalars[12];
            p.LeafScaleX = scalars[13];
            p.WoodColor = helios::make_RGBcolor(scalars[14], scalars[15], scalars[16]);

            p.Shape = (int) ints[0];
            p.BaseSplits = (uint) ints[1];
            p.BaseSplitsV = (uint) ints[2];
            p.Lobes = (int) ints[3];
            p.Levels = (int) ints[4];
            p.Leaves = (int) ints[5];
            p.LeafShape = (int) ints[6];

            size_t offset = 0;
            std::vector<std::vector<float>*> fv = floatVectorFields(p);
            for (size_t i = 0; i < fv.size(); i++) {
                if (fvec_lengths[i] > 0 && !fvec_data) {
                    setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (WeberPennTree::setTreeParameters): Null float vector data with non-zero length.");
                    return;
                }
                fv[i]->assign(fvec_data + offset, fvec_data + offset + fvec_lengths[i]);
                offset += fvec_lengths[i];
            }
            offset = 0;
            std::vector<std::vector<int>*> iv = intVectorFields(p);
            for (size_t i = 0; i < iv.size(); i++) {
                if (ivec_lengths[i] > 0 && !ivec_data) {
                    setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (WeberPennTree::setTreeParameters): Null int vector data with non-zero length.");
                    return;
                }
                iv[i]->assign(ivec_data + offset, ivec_data + offset + ivec_lengths[i]);
                offset += ivec_lengths[i];
            }

            if (!treeExists(wpt, treename)) {
                registerNewTreeName(wpt, treename, p);
            }
            wpt->setTreeParameters(treename, p);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (WeberPennTree::setTreeParameters): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (WeberPennTree::setTreeParameters): Unknown error setting tree parameters.");
        }
    }

    PYHELIOS_API void seedWeberPennTreeRandomGenerator(WeberPennTree* wpt, unsigned int seed) {
        try {
            clearError();
            wpt->seedRandomGenerator(seed);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (WeberPennTree::seedRandomGenerator): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (WeberPennTree::seedRandomGenerator): Unknown error seeding random generator.");
        }
    }

} //extern "C"

#endif //WEBERPENNTREE_PLUGIN_AVAILABLE
