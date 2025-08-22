// PyHelios C Interface
// Provides C-style functions for ctypes integration with Helios library

#include "../include/pyhelios_wrapper.h"
#include "Context.h"
#ifdef VISUALIZER_PLUGIN_AVAILABLE
#include "Visualizer.h"
#endif
#ifdef WEBERPENNTREE_PLUGIN_AVAILABLE
#include "WeberPennTree.h"
#endif
#ifdef RADIATION_PLUGIN_AVAILABLE
#include "RadiationModel.h"
#endif
#include <string>
#include <exception>
#include <cstring>

// Global error state for thread-safe error handling - matches PyHelios error codes
static thread_local std::string last_error_message;
static thread_local int last_error_code = PYHELIOS_SUCCESS;

extern "C" {

    //=============================================================================
    // Error Handling Functions
    //=============================================================================
    
    int getLastErrorCode() {
        return last_error_code;
    }
    
    const char* getLastErrorMessage() {
        return last_error_message.c_str();
    }
    
    void clearError() {
        last_error_code = PYHELIOS_SUCCESS;
        last_error_message.clear();
    }
    
    // Helper function to set error state with PyHelios error codes
    static void setError(int error_code, const std::string& message) {
        last_error_code = error_code;
        last_error_message = message;
    }
    // Context management - core functionality required by PyHelios
    helios::Context* createContext() {
        return new helios::Context();
    }
    
    void destroyContext(helios::Context* context) {
        delete context;
    }
    
    // Context state management
    void markGeometryClean(helios::Context* context) {
        context->markGeometryClean();
    }
    
    void markGeometryDirty(helios::Context* context) {
        context->markGeometryDirty();
    }
    
    bool isGeometryDirty(helios::Context* context) {
        return context->isGeometryDirty();
    }
    
    // Basic primitive creation
    unsigned int addPatch(helios::Context* context) {
        try {
            clearError(); // Clear any previous error
            return context->addPatch();
        } catch (const std::runtime_error& e) {
            // Use error code 7 for runtime errors and preserve exact Helios error message
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return 0; // Return invalid UUID, error will be checked by Python errcheck
        } catch (const std::exception& e) {
            // Use error code 7 for general runtime errors
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addPatch): ") + e.what());
            return 0;
        } catch (...) {
            // Use error code 99 for unknown errors
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addPatch): Unknown error creating patch.");
            return 0;
        }
    }
    
    unsigned int addPatchWithCenterAndSize(helios::Context* context, float* center, float* size) {
        try {
            clearError(); // Clear any previous error
            helios::vec3 center_vec(center[0], center[1], center[2]);
            helios::vec2 size_vec(size[0], size[1]);
            return context->addPatch(center_vec, size_vec);
        } catch (const std::runtime_error& e) {
            // Use error code 7 for runtime errors and preserve exact Helios error message
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return 0; // Return invalid UUID, error will be checked by Python errcheck
        } catch (const std::exception& e) {
            // Use error code 7 for general runtime errors
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addPatch): ") + e.what());
            return 0;
        } catch (...) {
            // Use error code 99 for unknown errors
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addPatch): Unknown error creating patch.");
            return 0;
        }
    }
    
    unsigned int addPatchWithCenterSizeAndRotation(helios::Context* context, float* center, float* size, float* rotation) {
        try {
            clearError(); // Clear any previous error
            helios::vec3 center_vec(center[0], center[1], center[2]);
            helios::vec2 size_vec(size[0], size[1]);
            // rotation array: [radius, elevation, azimuth] - use make_SphericalCoord(radius, elevation, azimuth)
            helios::SphericalCoord rotation_coord = helios::make_SphericalCoord(rotation[0], rotation[1], rotation[2]);
            return context->addPatch(center_vec, size_vec, rotation_coord);
        } catch (const std::runtime_error& e) {
            // Use error code 7 for runtime errors and preserve exact Helios error message
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return 0; // Return invalid UUID, error will be checked by Python errcheck
        } catch (const std::exception& e) {
            // Use error code 7 for general runtime errors
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addPatch): ") + e.what());
            return 0;
        } catch (...) {
            // Use error code 99 for unknown errors
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addPatch): Unknown error creating patch.");
            return 0;
        }
    }
    
    unsigned int addPatchWithCenterSizeRotationAndColor(helios::Context* context, float* center, float* size, float* rotation, float* color) {
        try {
            clearError(); // Clear any previous error
            helios::vec3 center_vec(center[0], center[1], center[2]);
            helios::vec2 size_vec(size[0], size[1]);
            // rotation array: [radius, elevation, azimuth] - use make_SphericalCoord(radius, elevation, azimuth)
            helios::SphericalCoord rotation_coord = helios::make_SphericalCoord(rotation[0], rotation[1], rotation[2]);
            helios::RGBcolor color_rgb(color[0], color[1], color[2]);
            return context->addPatch(center_vec, size_vec, rotation_coord, color_rgb);
        } catch (const std::runtime_error& e) {
            // Use error code 7 for runtime errors and preserve exact Helios error message
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return 0; // Return invalid UUID, error will be checked by Python errcheck
        } catch (const std::exception& e) {
            // Use error code 7 for general runtime errors
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addPatch): ") + e.what());
            return 0;
        } catch (...) {
            // Use error code 99 for unknown errors
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addPatch): Unknown error creating patch.");
            return 0;
        }
    }
    
    unsigned int addPatchWithCenterSizeRotationAndColorRGBA(helios::Context* context, float* center, float* size, float* rotation, float* color) {
        try {
            clearError(); // Clear any previous error
            helios::vec3 center_vec(center[0], center[1], center[2]);
            helios::vec2 size_vec(size[0], size[1]);
            // rotation array: [radius, elevation, azimuth] - use make_SphericalCoord(radius, elevation, azimuth)
            helios::SphericalCoord rotation_coord = helios::make_SphericalCoord(rotation[0], rotation[1], rotation[2]);
            helios::RGBAcolor color_rgba(color[0], color[1], color[2], color[3]);
            return context->addPatch(center_vec, size_vec, rotation_coord, color_rgba);
        } catch (const std::runtime_error& e) {
            // Use error code 7 for runtime errors and preserve exact Helios error message
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return 0; // Return invalid UUID, error will be checked by Python errcheck
        } catch (const std::exception& e) {
            // Use error code 7 for general runtime errors
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addPatch): ") + e.what());
            return 0;
        } catch (...) {
            // Use error code 99 for unknown errors
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addPatch): Unknown error creating patch.");
            return 0;
        }
    }
    
    // Triangle creation functions
    unsigned int addTriangle(helios::Context* context, float* vertex0, float* vertex1, float* vertex2) {
        try {
            clearError(); // Clear any previous error
            helios::vec3 v0(vertex0[0], vertex0[1], vertex0[2]);
            helios::vec3 v1(vertex1[0], vertex1[1], vertex1[2]);
            helios::vec3 v2(vertex2[0], vertex2[1], vertex2[2]);
            return context->addTriangle(v0, v1, v2);
        } catch (const std::runtime_error& e) {
            // Use error code 7 for runtime errors and preserve exact Helios error message
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return 0; // Return invalid UUID, error will be checked by Python errcheck
        } catch (const std::exception& e) {
            // Use error code 7 for general runtime errors
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addTriangle): ") + e.what());
            return 0;
        } catch (...) {
            // Use error code 99 for unknown errors
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addTriangle): Unknown error creating triangle.");
            return 0;
        }
    }
    
    unsigned int addTriangleWithColor(helios::Context* context, float* vertex0, float* vertex1, float* vertex2, float* color) {
        try {
            clearError(); // Clear any previous error
            helios::vec3 v0(vertex0[0], vertex0[1], vertex0[2]);
            helios::vec3 v1(vertex1[0], vertex1[1], vertex1[2]);
            helios::vec3 v2(vertex2[0], vertex2[1], vertex2[2]);
            helios::RGBcolor rgb_color(color[0], color[1], color[2]);
            return context->addTriangle(v0, v1, v2, rgb_color);
        } catch (const std::runtime_error& e) {
            // Use error code 7 for runtime errors and preserve exact Helios error message
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return 0; // Return invalid UUID, error will be checked by Python errcheck
        } catch (const std::exception& e) {
            // Use error code 7 for general runtime errors
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addTriangle): ") + e.what());
            return 0;
        } catch (...) {
            // Use error code 99 for unknown errors
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addTriangle): Unknown error creating triangle with color.");
            return 0;
        }
    }
    
    unsigned int addTriangleWithColorRGBA(helios::Context* context, float* vertex0, float* vertex1, float* vertex2, float* color) {
        try {
            clearError(); // Clear any previous error
            helios::vec3 v0(vertex0[0], vertex0[1], vertex0[2]);
            helios::vec3 v1(vertex1[0], vertex1[1], vertex1[2]);
            helios::vec3 v2(vertex2[0], vertex2[1], vertex2[2]);
            helios::RGBAcolor rgba_color(color[0], color[1], color[2], color[3]);
            return context->addTriangle(v0, v1, v2, rgba_color);
        } catch (const std::runtime_error& e) {
            // Use error code 7 for runtime errors and preserve exact Helios error message
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return 0; // Return invalid UUID, error will be checked by Python errcheck
        } catch (const std::exception& e) {
            // Use error code 7 for general runtime errors
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addTriangle): ") + e.what());
            return 0;
        } catch (...) {
            // Use error code 99 for unknown errors
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addTriangle): Unknown error creating triangle with RGBA color.");
            return 0;
        }
    }
    
    unsigned int addTriangleWithTexture(helios::Context* context, float* vertex0, float* vertex1, float* vertex2, const char* texture_file, float* uv0, float* uv1, float* uv2) {
        try {
            clearError(); // Clear any previous error
            helios::vec3 v0(vertex0[0], vertex0[1], vertex0[2]);
            helios::vec3 v1(vertex1[0], vertex1[1], vertex1[2]);
            helios::vec3 v2(vertex2[0], vertex2[1], vertex2[2]);
            helios::vec2 uv0_vec(uv0[0], uv0[1]);
            helios::vec2 uv1_vec(uv1[0], uv1[1]);
            helios::vec2 uv2_vec(uv2[0], uv2[1]);
            return context->addTriangle(v0, v1, v2, texture_file, uv0_vec, uv1_vec, uv2_vec);
        } catch (const std::runtime_error& e) {
            // Use error code 7 for runtime errors and preserve exact Helios error message
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return 0; // Return invalid UUID, error will be checked by Python errcheck
        } catch (const std::exception& e) {
            // Use error code 7 for general runtime errors
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addTriangle): ") + e.what());
            return 0;
        } catch (...) {
            // Use error code 99 for unknown errors
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addTriangle): Unknown error creating triangle with texture.");
            return 0;
        }
    }
    
    // Compound geometry creation functions - return arrays of UUIDs
    
    // addTile functions
    unsigned int* addTile(helios::Context* context, float* center, float* size, float* rotation, int* subdiv, unsigned int* count) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                *count = 0;
                return nullptr;
            }
            
            helios::vec3 center_vec(center[0], center[1], center[2]);
            helios::vec2 size_vec(size[0], size[1]);
            helios::SphericalCoord rotation_coord = helios::make_SphericalCoord(rotation[0], rotation[1], rotation[2]);
            helios::int2 subdiv_int2(subdiv[0], subdiv[1]);
            
            std::vector<unsigned int> uuids = context->addTile(center_vec, size_vec, rotation_coord, subdiv_int2);
            
            // Convert vector to thread-local static array for return
            static thread_local std::vector<unsigned int> static_result;
            static_result = std::move(uuids);
            *count = static_result.size();
            return static_result.data();
            
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            *count = 0;
            return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addTile): ") + e.what());
            *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addTile): Unknown error creating tile.");
            *count = 0;
            return nullptr;
        }
    }
    
    unsigned int* addTileWithColor(helios::Context* context, float* center, float* size, float* rotation, int* subdiv, float* color, unsigned int* count) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                *count = 0;
                return nullptr;
            }
            
            helios::vec3 center_vec(center[0], center[1], center[2]);
            helios::vec2 size_vec(size[0], size[1]);
            helios::SphericalCoord rotation_coord = helios::make_SphericalCoord(rotation[0], rotation[1], rotation[2]);
            helios::int2 subdiv_int2(subdiv[0], subdiv[1]);
            helios::RGBcolor color_rgb(color[0], color[1], color[2]);
            
            std::vector<unsigned int> uuids = context->addTile(center_vec, size_vec, rotation_coord, subdiv_int2, color_rgb);
            
            // Convert vector to thread-local static array for return
            static thread_local std::vector<unsigned int> static_result;
            static_result = std::move(uuids);
            *count = static_result.size();
            return static_result.data();
            
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            *count = 0;
            return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addTile): ") + e.what());
            *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addTile): Unknown error creating tile with color.");
            *count = 0;
            return nullptr;
        }
    }
    
    // addSphere functions
    unsigned int* addSphere(helios::Context* context, unsigned int ndivs, float* center, float radius, unsigned int* count) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                *count = 0;
                return nullptr;
            }
            
            helios::vec3 center_vec(center[0], center[1], center[2]);
            
            std::vector<unsigned int> uuids = context->addSphere(ndivs, center_vec, radius);
            
            // Convert vector to thread-local static array for return
            static thread_local std::vector<unsigned int> static_result;
            static_result = std::move(uuids);
            *count = static_result.size();
            return static_result.data();
            
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            *count = 0;
            return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addSphere): ") + e.what());
            *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addSphere): Unknown error creating sphere.");
            *count = 0;
            return nullptr;
        }
    }
    
    unsigned int* addSphereWithColor(helios::Context* context, unsigned int ndivs, float* center, float radius, float* color, unsigned int* count) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                *count = 0;
                return nullptr;
            }
            
            helios::vec3 center_vec(center[0], center[1], center[2]);
            helios::RGBcolor color_rgb(color[0], color[1], color[2]);
            
            std::vector<unsigned int> uuids = context->addSphere(ndivs, center_vec, radius, color_rgb);
            
            // Convert vector to thread-local static array for return
            static thread_local std::vector<unsigned int> static_result;
            static_result = std::move(uuids);
            *count = static_result.size();
            return static_result.data();
            
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            *count = 0;
            return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addSphere): ") + e.what());
            *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addSphere): Unknown error creating sphere with color.");
            *count = 0;
            return nullptr;
        }
    }
    
    // addTube functions
    unsigned int* addTube(helios::Context* context, unsigned int ndivs, float* nodes, unsigned int node_count, float* radii, unsigned int* count) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                *count = 0;
                return nullptr;
            }
            
            // Pre-allocate nodes vector with known size
            std::vector<helios::vec3> nodes_vec;
            nodes_vec.reserve(node_count);
            for (unsigned int i = 0; i < node_count; i++) {
                nodes_vec.emplace_back(nodes[i*3], nodes[i*3+1], nodes[i*3+2]);
            }
            
            // Convert radii array to vector with pre-allocation
            std::vector<float> radii_vec;
            radii_vec.reserve(node_count);
            radii_vec.assign(radii, radii + node_count);
            
            std::vector<unsigned int> uuids = context->addTube(ndivs, nodes_vec, radii_vec);
            
            // Convert vector to thread-local static array for return
            static thread_local std::vector<unsigned int> static_result;
            static_result = std::move(uuids);
            *count = static_result.size();
            return static_result.data();
            
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            *count = 0;
            return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addTube): ") + e.what());
            *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addTube): Unknown error creating tube.");
            *count = 0;
            return nullptr;
        }
    }
    
    unsigned int* addTubeWithColor(helios::Context* context, unsigned int ndivs, float* nodes, unsigned int node_count, float* radii, float* colors, unsigned int* count) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                *count = 0;
                return nullptr;
            }
            
            // Pre-allocate nodes vector with known size
            std::vector<helios::vec3> nodes_vec;
            nodes_vec.reserve(node_count);
            for (unsigned int i = 0; i < node_count; i++) {
                nodes_vec.emplace_back(nodes[i*3], nodes[i*3+1], nodes[i*3+2]);
            }
            
            // Convert radii array to vector with pre-allocation
            std::vector<float> radii_vec;
            radii_vec.reserve(node_count);
            radii_vec.assign(radii, radii + node_count);
            
            // Pre-allocate colors vector with known size
            std::vector<helios::RGBcolor> colors_vec;
            colors_vec.reserve(node_count);
            for (unsigned int i = 0; i < node_count; i++) {
                colors_vec.emplace_back(colors[i*3], colors[i*3+1], colors[i*3+2]);
            }
            
            std::vector<unsigned int> uuids = context->addTube(ndivs, nodes_vec, radii_vec, colors_vec);
            
            // Convert vector to thread-local static array for return
            static thread_local std::vector<unsigned int> static_result;
            static_result = std::move(uuids);
            *count = static_result.size();
            return static_result.data();
            
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            *count = 0;
            return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addTube): ") + e.what());
            *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addTube): Unknown error creating tube with color.");
            *count = 0;
            return nullptr;
        }
    }
    
    // addBox functions
    unsigned int* addBox(helios::Context* context, float* center, float* size, int* subdiv, unsigned int* count) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                *count = 0;
                return nullptr;
            }
            
            helios::vec3 center_vec(center[0], center[1], center[2]);
            helios::vec3 size_vec(size[0], size[1], size[2]);
            helios::int3 subdiv_int3(subdiv[0], subdiv[1], subdiv[2]);
            
            std::vector<unsigned int> uuids = context->addBox(center_vec, size_vec, subdiv_int3);
            
            // Convert vector to thread-local static array for return
            static thread_local std::vector<unsigned int> static_result;
            static_result = std::move(uuids);
            *count = static_result.size();
            return static_result.data();
            
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            *count = 0;
            return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addBox): ") + e.what());
            *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addBox): Unknown error creating box.");
            *count = 0;
            return nullptr;
        }
    }
    
    unsigned int* addBoxWithColor(helios::Context* context, float* center, float* size, int* subdiv, float* color, unsigned int* count) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                *count = 0;
                return nullptr;
            }
            
            helios::vec3 center_vec(center[0], center[1], center[2]);
            helios::vec3 size_vec(size[0], size[1], size[2]);
            helios::int3 subdiv_int3(subdiv[0], subdiv[1], subdiv[2]);
            helios::RGBcolor color_rgb(color[0], color[1], color[2]);
            
            std::vector<unsigned int> uuids = context->addBox(center_vec, size_vec, subdiv_int3, color_rgb);
            
            // Convert vector to thread-local static array for return
            static thread_local std::vector<unsigned int> static_result;
            static_result = std::move(uuids);
            *count = static_result.size();
            return static_result.data();
            
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            *count = 0;
            return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addBox): ") + e.what());
            *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addBox): Unknown error creating box with color.");
            *count = 0;
            return nullptr;
        }
    }
    
    // Primitive query functions
    unsigned int getPrimitiveType(helios::Context* context, unsigned int uuid) {
        try {
            clearError(); // Clear any previous error
            return (unsigned int)context->getPrimitiveType(uuid);
        } catch (const std::runtime_error& e) {
            // Use error code 2 for UUID_NOT_FOUND and preserve exact Helios error message
            setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what());
            return 0; // Return invalid type, error will be checked by Python errcheck
        } catch (const std::exception& e) {
            // Use error code 7 for general runtime errors
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return 0;
        } catch (...) {
            // Use error code 99 for unknown errors
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveType): Unknown error accessing primitive with UUID " + std::to_string(uuid) + ".");
            return 0;
        }
    }
    
    float getPrimitiveArea(helios::Context* context, unsigned int uuid) {
        try {
            clearError(); // Clear any previous error
            return context->getPrimitiveArea(uuid);
        } catch (const std::runtime_error& e) {
            // Use error code 2 for UUID_NOT_FOUND and preserve exact Helios error message
            setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what());
            return 0.0f; // Return default value, error will be checked by Python errcheck
        } catch (const std::exception& e) {
            // Use error code 7 for general runtime errors
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return 0.0f;
        } catch (...) {
            // Use error code 99 for unknown errors
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveArea): Unknown error accessing primitive with UUID " + std::to_string(uuid) + ".");
            return 0.0f;
        }
    }
    
    float* getPrimitiveNormal(helios::Context* context, unsigned int uuid) {
        try {
            clearError(); // Clear any previous error
            helios::vec3 normal = context->getPrimitiveNormal(uuid);
            static float result[3];
            result[0] = normal.x;
            result[1] = normal.y;
            result[2] = normal.z;
            return result;
        } catch (const std::runtime_error& e) {
            // Use error code 2 for UUID_NOT_FOUND and preserve exact Helios error message
            setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what());
            static float error_result[3] = {0.0f, 0.0f, 0.0f};
            return error_result; // Return zero vector, error will be checked by Python errcheck
        } catch (const std::exception& e) {
            // Use error code 7 for general runtime errors
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            static float error_result[3] = {0.0f, 0.0f, 0.0f};
            return error_result;
        } catch (...) {
            // Use error code 99 for unknown errors
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveNormal): Unknown error accessing primitive with UUID " + std::to_string(uuid) + ".");
            static float error_result[3] = {0.0f, 0.0f, 0.0f};
            return error_result;
        }
    }
    
    unsigned int getPrimitiveCount(helios::Context* context) {
        return context->getPrimitiveCount();
    }
    
    float* getPrimitiveVertices(helios::Context* context, unsigned int uuid, unsigned int* size) {
        try {
            clearError(); // Clear any previous error
            std::vector<helios::vec3> vertices = context->getPrimitiveVertices(uuid);
            
            // Allocate static buffer for vertex data (3 floats per vertex)
            static std::vector<float> vertex_buffer;
            vertex_buffer.clear();
            vertex_buffer.reserve(vertices.size() * 3);
            
            for (const auto& vertex : vertices) {
                vertex_buffer.push_back(vertex.x);
                vertex_buffer.push_back(vertex.y);
                vertex_buffer.push_back(vertex.z);
            }
            
            // Return total number of floats (3 per vertex)
            *size = vertex_buffer.size();
            return vertex_buffer.data();
        } catch (const std::runtime_error& e) {
            // Use error code 2 for UUID_NOT_FOUND and preserve exact Helios error message
            setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what());
            *size = 0;
            static float error_result[3] = {0.0f, 0.0f, 0.0f};
            return error_result; // Return empty buffer, error will be checked by Python errcheck
        } catch (const std::exception& e) {
            // Use error code 7 for general runtime errors
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            *size = 0;
            static float error_result[3] = {0.0f, 0.0f, 0.0f};
            return error_result;
        } catch (...) {
            // Use error code 99 for unknown errors
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveVertices): Unknown error accessing primitive with UUID " + std::to_string(uuid) + ".");
            *size = 0;
            static float error_result[3] = {0.0f, 0.0f, 0.0f};
            return error_result;
        }
    }
    
    float* getPrimitiveColor(helios::Context* context, unsigned int uuid) {
        try {
            clearError(); // Clear any previous error
            helios::RGBcolor color = context->getPrimitiveColor(uuid);
            static float result[3];
            result[0] = color.r;
            result[1] = color.g;
            result[2] = color.b;
            return result;
        } catch (const std::runtime_error& e) {
            // Use error code 2 for UUID_NOT_FOUND and preserve exact Helios error message
            setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what());
            static float error_result[3] = {0.0f, 0.0f, 0.0f};
            return error_result; // Return black color, error will be checked by Python errcheck
        } catch (const std::exception& e) {
            // Use error code 7 for general runtime errors
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            static float error_result[3] = {0.0f, 0.0f, 0.0f};
            return error_result;
        } catch (...) {
            // Use error code 99 for unknown errors
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveColor): Unknown error accessing primitive with UUID " + std::to_string(uuid) + ".");
            static float error_result[3] = {0.0f, 0.0f, 0.0f};
            return error_result;
        }
    }
    
    float* getPrimitiveColorRGB(helios::Context* context, unsigned int uuid) {
        try {
            clearError(); // Clear any previous error
            helios::RGBcolor color = context->getPrimitiveColorRGB(uuid);
            static float result[3];
            result[0] = color.r;
            result[1] = color.g;
            result[2] = color.b;
            return result;
        } catch (const std::runtime_error& e) {
            // Use error code 2 for UUID_NOT_FOUND and preserve exact Helios error message
            setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what());
            static float error_result[3] = {0.0f, 0.0f, 0.0f};
            return error_result; // Return black color, error will be checked by Python errcheck
        } catch (const std::exception& e) {
            // Use error code 7 for general runtime errors
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            static float error_result[3] = {0.0f, 0.0f, 0.0f};
            return error_result;
        } catch (...) {
            // Use error code 99 for unknown errors
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveColorRGB): Unknown error accessing primitive with UUID " + std::to_string(uuid) + ".");
            static float error_result[3] = {0.0f, 0.0f, 0.0f};
            return error_result;
        }
    }
    
    float* getPrimitiveColorRGBA(helios::Context* context, unsigned int uuid) {
        try {
            clearError(); // Clear any previous error
            helios::RGBAcolor color = context->getPrimitiveColorRGBA(uuid);
            static float result[4];
            result[0] = color.r;
            result[1] = color.g;
            result[2] = color.b;
            result[3] = color.a;
            return result;
        } catch (const std::runtime_error& e) {
            // Use error code 2 for UUID_NOT_FOUND and preserve exact Helios error message
            setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what());
            static float error_result[4] = {0.0f, 0.0f, 0.0f, 1.0f};
            return error_result; // Return black transparent color, error will be checked by Python errcheck
        } catch (const std::exception& e) {
            // Use error code 7 for general runtime errors
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            static float error_result[4] = {0.0f, 0.0f, 0.0f, 1.0f};
            return error_result;
        } catch (...) {
            // Use error code 99 for unknown errors
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveColorRGBA): Unknown error accessing primitive with UUID " + std::to_string(uuid) + ".");
            static float error_result[4] = {0.0f, 0.0f, 0.0f, 1.0f};
            return error_result;
        }
    }
    
    unsigned int* getAllUUIDs(helios::Context* context, unsigned int* size) {
        try {
            clearError(); // Clear any previous error
            std::vector<unsigned int> uuids = context->getAllUUIDs();
            *size = uuids.size();
            
            // Allocate static buffer for UUID data
            static std::vector<unsigned int> uuid_buffer;
            uuid_buffer = uuids;
            
            return uuid_buffer.data();
        } catch (const std::exception& e) {
            // Use error code 7 for general runtime errors
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            *size = 0;
            static unsigned int error_result[1] = {0};
            return error_result; // Return empty buffer, error will be checked by Python errcheck
        } catch (...) {
            // Use error code 99 for unknown errors
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getAllUUIDs): Unknown error retrieving all UUIDs.");
            *size = 0;
            static unsigned int error_result[1] = {0};
            return error_result;
        }
    }
    
    // Object functions
    unsigned int getObjectCount(helios::Context* context) {
        return context->getObjectCount();
    }
    
    unsigned int* getAllObjectIDs(helios::Context* context, unsigned int* size) {
        try {
            clearError(); // Clear any previous error
            std::vector<unsigned int> object_ids = context->getAllObjectIDs();
            *size = object_ids.size();
            
            static std::vector<unsigned int> object_buffer;
            object_buffer = object_ids;
            
            return object_buffer.data();
        } catch (const std::exception& e) {
            // Use error code 7 for general runtime errors
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            *size = 0;
            static unsigned int error_result[1] = {0};
            return error_result; // Return empty buffer, error will be checked by Python errcheck
        } catch (...) {
            // Use error code 99 for unknown errors
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getAllObjectIDs): Unknown error retrieving all object IDs.");
            *size = 0;
            static unsigned int error_result[1] = {0};
            return error_result;
        }
    }
    
    unsigned int* getObjectPrimitiveUUIDs(helios::Context* context, unsigned int object_id, unsigned int* size) {
        try {
            clearError(); // Clear any previous error
            std::vector<unsigned int> uuids = context->getObjectPrimitiveUUIDs(object_id);
            *size = uuids.size();
            
            static std::vector<unsigned int> uuid_buffer;
            uuid_buffer = uuids;
            
            return uuid_buffer.data();
        } catch (const std::runtime_error& e) {
            // Use error code 3 for OBJECT_NOT_FOUND and preserve exact Helios error message
            setError(PYHELIOS_ERROR_FILE_IO, e.what());
            *size = 0;
            static unsigned int error_result[1] = {0};
            return error_result; // Return empty buffer, error will be checked by Python errcheck
        } catch (const std::exception& e) {
            // Use error code 7 for general runtime errors
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            *size = 0;
            static unsigned int error_result[1] = {0};
            return error_result;
        } catch (...) {
            // Use error code 99 for unknown errors
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getObjectPrimitiveUUIDs): Unknown error accessing object with ID " + std::to_string(object_id) + ".");
            *size = 0;
            static unsigned int error_result[1] = {0};
            return error_result;
        }
    }

    unsigned int* loadPLY(helios::Context* context, const char* filename, float* origin, float height, const char* upaxis, unsigned int* size) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                if (size) *size = 0;
                return nullptr;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null");
                if (size) *size = 0;
                return nullptr;
            }
            if (!origin) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Origin is null");
                if (size) *size = 0;
                return nullptr;
            }
            if (!upaxis) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Upaxis is null");
                if (size) *size = 0;
                return nullptr;
            }
            if (!size) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Size pointer is null");
                return nullptr;
            }
            
            helios::vec3 origin_vec(origin[0], origin[1], origin[2]);
            std::string upaxis_str(upaxis);
            
            std::vector<unsigned int> uuids = context->loadPLY(filename, origin_vec, height, upaxis_str, false);
            
            // Allocate static buffer for UUID data
            static std::vector<unsigned int> uuid_buffer;
            uuid_buffer = uuids;
            *size = uuid_buffer.size();
            return uuid_buffer.data();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_FILE_IO, std::string("ERROR (Context::loadPLY): ") + e.what());
            if (size) *size = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::loadPLY): Unknown error loading PLY file.");
            if (size) *size = 0;
            return nullptr;
        }
    }

#ifdef VISUALIZER_PLUGIN_AVAILABLE
    // Visualizer C interface functions
    Visualizer* createVisualizer(unsigned int width, unsigned int height, bool headless) {
        // Enable window decorations by default (true), headless parameter controls window visibility
        return new Visualizer(width, height, 4, true, headless); // 4 antialiasing samples, decorations enabled
    }
    
    Visualizer* createVisualizerWithAntialiasing(unsigned int width, unsigned int height, unsigned int samples, bool headless) {
        // Enable window decorations by default (true), headless parameter controls window visibility  
        return new Visualizer(width, height, samples, true, headless);
    }
    
    void destroyVisualizer(Visualizer* visualizer) {
        delete visualizer;
    }
    
    void buildContextGeometry(Visualizer* visualizer, helios::Context* context) {
        visualizer->buildContextGeometry(context);
    }
    
    void buildContextGeometryUUIDs(Visualizer* visualizer, helios::Context* context, unsigned int* uuids, unsigned int count) {
        std::vector<unsigned int> uuid_vector(uuids, uuids + count);
        visualizer->buildContextGeometry(context, uuid_vector);
    }
    
    void plotInteractive(Visualizer* visualizer) {
        visualizer->plotInteractive();
    }
    
    void plotUpdate(Visualizer* visualizer) {
        visualizer->plotUpdate();
    }
    
    void printWindow(Visualizer* visualizer, const char* filename) {
        visualizer->printWindow(filename);
    }
    
    void closeWindow(Visualizer* visualizer) {
        visualizer->closeWindow();
    }
    
    void setBackgroundColor(Visualizer* visualizer, float* color) {
        helios::RGBcolor bg_color(color[0], color[1], color[2]);
        visualizer->setBackgroundColor(bg_color);
    }
    
    void setLightDirection(Visualizer* visualizer, float* direction) {
        helios::vec3 light_dir(direction[0], direction[1], direction[2]);
        visualizer->setLightDirection(light_dir);
    }
    
    void setCameraPosition(Visualizer* visualizer, float* position, float* lookat) {
        helios::vec3 camera_pos(position[0], position[1], position[2]);
        helios::vec3 look_at(lookat[0], lookat[1], lookat[2]);
        visualizer->setCameraPosition(camera_pos, look_at);
    }
    
    void setCameraPositionSpherical(Visualizer* visualizer, float* position, float* lookat) {
        // Convert to spherical coordinates and call the appropriate method
        helios::vec3 camera_pos(position[0], position[1], position[2]);
        helios::vec3 look_at(lookat[0], lookat[1], lookat[2]);
        // For now, just call the regular setCameraPosition - could be enhanced to use SphericalCoord later
        visualizer->setCameraPosition(camera_pos, look_at);
    }
    
    void setLightingModel(Visualizer* visualizer, unsigned int model) {
        Visualizer::LightingModel lighting_model;
        
        switch (model) {
            case 0:
                lighting_model = Visualizer::LIGHTING_NONE;
                break;
            case 1:
                lighting_model = Visualizer::LIGHTING_PHONG;
                break;
            case 2:
                lighting_model = Visualizer::LIGHTING_PHONG_SHADOWED;
                break;
            default:
                // Default to phong if unknown
                lighting_model = Visualizer::LIGHTING_PHONG;
                break;
        }
        
        visualizer->setLightingModel(lighting_model);
    }
    
    bool validateTextureFile(const char* texture_file) {
        std::string filename(texture_file);
        return ::validateTextureFile(filename);
    }
#endif

#ifdef WEBERPENNTREE_PLUGIN_AVAILABLE
    // WeberPennTree C interface functions
    WeberPennTree* createWeberPennTree(helios::Context* context) {
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
    
    WeberPennTree* createWeberPennTreeWithBuildPluginRootDirectory(helios::Context* context, const char* buildDirectory) {
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
    
    void destroyWeberPennTree(WeberPennTree* wpt) {
        delete wpt;
    }
    
    unsigned int buildTree(WeberPennTree* wpt, const char* treename, float* origin) {
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
    
    unsigned int buildTreeWithScale(WeberPennTree* wpt, const char* treename, float* origin, float scale) {
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
    
    unsigned int* getWeberPennTreeTrunkUUIDs(WeberPennTree* wpt, unsigned int treeID, unsigned int* size) {
        try {
            clearError();
            std::vector<unsigned int> uuids = wpt->getTrunkUUIDs(treeID);
            *size = uuids.size();
            
            static std::vector<unsigned int> uuid_buffer;
            uuid_buffer = uuids;
            
            return uuid_buffer.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (WeberPennTree::getTrunkUUIDs): ") + e.what());
            *size = 0;
            static unsigned int error_result[1] = {0};
            return error_result;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (WeberPennTree::getTrunkUUIDs): Unknown error getting trunk UUIDs.");
            *size = 0;
            static unsigned int error_result[1] = {0};
            return error_result;
        }
    }
    
    unsigned int* getWeberPennTreeBranchUUIDs(WeberPennTree* wpt, unsigned int treeID, unsigned int* size) {
        try {
            clearError();
            std::vector<unsigned int> uuids = wpt->getBranchUUIDs(treeID);
            *size = uuids.size();
            
            static std::vector<unsigned int> uuid_buffer;
            uuid_buffer = uuids;
            
            return uuid_buffer.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (WeberPennTree::getBranchUUIDs): ") + e.what());
            *size = 0;
            static unsigned int error_result[1] = {0};
            return error_result;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (WeberPennTree::getBranchUUIDs): Unknown error getting branch UUIDs.");
            *size = 0;
            static unsigned int error_result[1] = {0};
            return error_result;
        }
    }
    
    unsigned int* getWeberPennTreeLeafUUIDs(WeberPennTree* wpt, unsigned int treeID, unsigned int* size) {
        try {
            clearError();
            std::vector<unsigned int> uuids = wpt->getLeafUUIDs(treeID);
            *size = uuids.size();
            
            static std::vector<unsigned int> uuid_buffer;
            uuid_buffer = uuids;
            
            return uuid_buffer.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (WeberPennTree::getLeafUUIDs): ") + e.what());
            *size = 0;
            static unsigned int error_result[1] = {0};
            return error_result;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (WeberPennTree::getLeafUUIDs): Unknown error getting leaf UUIDs.");
            *size = 0;
            static unsigned int error_result[1] = {0};
            return error_result;
        }
    }
    
    unsigned int* getWeberPennTreeAllUUIDs(WeberPennTree* wpt, unsigned int treeID, unsigned int* size) {
        try {
            clearError();
            std::vector<unsigned int> uuids = wpt->getAllUUIDs(treeID);
            *size = uuids.size();
            
            static std::vector<unsigned int> uuid_buffer;
            uuid_buffer = uuids;
            
            return uuid_buffer.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (WeberPennTree::getAllUUIDs): ") + e.what());
            *size = 0;
            static unsigned int error_result[1] = {0};
            return error_result;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (WeberPennTree::getAllUUIDs): Unknown error getting all UUIDs.");
            *size = 0;
            static unsigned int error_result[1] = {0};
            return error_result;
        }
    }
    
    void setBranchRecursionLevel(WeberPennTree* wpt, unsigned int level) {
        try {
            clearError();
            wpt->setBranchRecursionLevel(level);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (WeberPennTree::setBranchRecursionLevel): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (WeberPennTree::setBranchRecursionLevel): Unknown error setting recursion level.");
        }
    }
    
    void setTrunkSegmentResolution(WeberPennTree* wpt, unsigned int trunk_segs) {
        try {
            clearError();
            wpt->setTrunkSegmentResolution(trunk_segs);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (WeberPennTree::setTrunkSegmentResolution): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (WeberPennTree::setTrunkSegmentResolution): Unknown error setting trunk resolution.");
        }
    }
    
    void setBranchSegmentResolution(WeberPennTree* wpt, unsigned int branch_segs) {
        try {
            clearError();
            wpt->setBranchSegmentResolution(branch_segs);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (WeberPennTree::setBranchSegmentResolution): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (WeberPennTree::setBranchSegmentResolution): Unknown error setting branch resolution.");
        }
    }
    
    void setLeafSubdivisions(WeberPennTree* wpt, unsigned int leaf_segs_x, unsigned int leaf_segs_y) {
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
    
#endif

    //=============================================================================
    // Primitive Data Functions
    //=============================================================================
    
    void setPrimitiveDataFloat(helios::Context* context, unsigned int uuid, const char* label, float value) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            context->setPrimitiveData(uuid, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveData): Unknown error setting primitive data float.");
        }
    }
    
    void setPrimitiveDataInt(helios::Context* context, unsigned int uuid, const char* label, int value) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            context->setPrimitiveData(uuid, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveData): Unknown error setting primitive data int.");
        }
    }
    
    void setPrimitiveDataString(helios::Context* context, unsigned int uuid, const char* label, const char* value) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label || !value) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or value is null");
                return;
            }
            std::string str_value(value);
            context->setPrimitiveData(uuid, label, str_value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveData): Unknown error setting primitive data string.");
        }
    }
    
    float getPrimitiveDataFloat(helios::Context* context, unsigned int uuid, const char* label) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0.0f;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return 0.0f;
            }
            float value;
            context->getPrimitiveData(uuid, label, value);
            return value;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveData): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveData): Unknown error getting primitive data float.");
            return 0.0f;
        }
    }
    
    int getPrimitiveDataInt(helios::Context* context, unsigned int uuid, const char* label) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return 0;
            }
            int value;
            context->getPrimitiveData(uuid, label, value);
            return value;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveData): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveData): Unknown error getting primitive data int.");
            return 0;
        }
    }
    
    int getPrimitiveDataString(helios::Context* context, unsigned int uuid, const char* label, char* buffer, int buffer_size) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0;
            }
            if (!label || !buffer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or buffer is null");
                return 0;
            }
            std::string value;
            context->getPrimitiveData(uuid, label, value);
            
            // Copy string to buffer with null termination
            int copy_length = std::min((int)value.length(), buffer_size - 1);
            std::strncpy(buffer, value.c_str(), copy_length);
            buffer[copy_length] = '\0';
            
            return copy_length;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveData): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveData): Unknown error getting primitive data string.");
            return 0;
        }
    }
    
    bool doesPrimitiveDataExist(helios::Context* context, unsigned int uuid, const char* label) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return false;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return false;
            }
            return context->doesPrimitiveDataExist(uuid, label);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::doesPrimitiveDataExist): ") + e.what());
            return false;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::doesPrimitiveDataExist): Unknown error checking primitive data existence.");
            return false;
        }
    }
    
    void setPrimitiveDataVec3(helios::Context* context, unsigned int uuid, const char* label, float x, float y, float z) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            helios::vec3 vec_value(x, y, z);
            context->setPrimitiveData(uuid, label, vec_value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveData): Unknown error setting primitive data vec3.");
        }
    }
    
    void getPrimitiveDataVec3(helios::Context* context, unsigned int uuid, const char* label, float* x, float* y, float* z) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label || !x || !y || !z) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or coordinate pointers are null");
                return;
            }
            helios::vec3 vec_value;
            context->getPrimitiveData(uuid, label, vec_value);
            *x = vec_value.x;
            *y = vec_value.y;
            *z = vec_value.z;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveData): Unknown error getting primitive data vec3.");
        }
    }
    
    int getPrimitiveDataType(helios::Context* context, unsigned int uuid, const char* label) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return -1;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return -1;
            }
            return (int)context->getPrimitiveDataType(label);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveDataType): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveDataType): Unknown error getting primitive data type.");
            return -1;
        }
    }
    
    int getPrimitiveDataSize(helios::Context* context, unsigned int uuid, const char* label) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return 0;
            }
            return (int)context->getPrimitiveDataSize(uuid, label);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveDataSize): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveDataSize): Unknown error getting primitive data size.");
            return 0;
        }
    }
    
    void setPrimitiveDataUInt(helios::Context* context, unsigned int uuid, const char* label, unsigned int value) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            context->setPrimitiveData(uuid, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveData): Unknown error setting primitive data uint.");
        }
    }
    
    void setPrimitiveDataDouble(helios::Context* context, unsigned int uuid, const char* label, double value) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            context->setPrimitiveData(uuid, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveData): Unknown error setting primitive data double.");
        }
    }
    
    int getPrimitiveDataGeneric(helios::Context* context, unsigned int uuid, const char* label, void* result_buffer, int max_buffer_size) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0;
            }
            if (!label || !result_buffer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or result buffer is null");
                return 0;
            }
            // This is a simplified implementation - in practice you'd need to handle different data types
            setError(PYHELIOS_ERROR_RUNTIME, "getPrimitiveDataGeneric not fully implemented");
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveDataGeneric): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveDataGeneric): Unknown error getting primitive data generically.");
            return 0;
        }
    }
    
    // Extended primitive data functions - Vec2 and Vec4 variants
    void setPrimitiveDataVec2(helios::Context* context, unsigned int uuid, const char* label, float x, float y) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            helios::vec2 vec_value(x, y);
            context->setPrimitiveData(uuid, label, vec_value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveData): Unknown error setting primitive data vec2.");
        }
    }
    
    void setPrimitiveDataVec4(helios::Context* context, unsigned int uuid, const char* label, float x, float y, float z, float w) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            helios::vec4 vec_value(x, y, z, w);
            context->setPrimitiveData(uuid, label, vec_value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveData): Unknown error setting primitive data vec4.");
        }
    }
    
    void getPrimitiveDataVec2(helios::Context* context, unsigned int uuid, const char* label, float* x, float* y) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label || !x || !y) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or coordinate pointers are null");
                return;
            }
            helios::vec2 vec_value;
            context->getPrimitiveData(uuid, label, vec_value);
            *x = vec_value.x;
            *y = vec_value.y;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveData): Unknown error getting primitive data vec2.");
        }
    }
    
    void getPrimitiveDataVec4(helios::Context* context, unsigned int uuid, const char* label, float* x, float* y, float* z, float* w) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label || !x || !y || !z || !w) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or coordinate pointers are null");
                return;
            }
            helios::vec4 vec_value;
            context->getPrimitiveData(uuid, label, vec_value);
            *x = vec_value.x;
            *y = vec_value.y;
            *z = vec_value.z;
            *w = vec_value.w;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveData): Unknown error getting primitive data vec4.");
        }
    }
    
    // Extended primitive data functions - Int2, Int3, Int4 variants
    void setPrimitiveDataInt2(helios::Context* context, unsigned int uuid, const char* label, int x, int y) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            helios::int2 int_value(x, y);
            context->setPrimitiveData(uuid, label, int_value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveData): Unknown error setting primitive data int2.");
        }
    }
    
    void setPrimitiveDataInt3(helios::Context* context, unsigned int uuid, const char* label, int x, int y, int z) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            helios::int3 int_value(x, y, z);
            context->setPrimitiveData(uuid, label, int_value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveData): Unknown error setting primitive data int3.");
        }
    }
    
    void setPrimitiveDataInt4(helios::Context* context, unsigned int uuid, const char* label, int x, int y, int z, int w) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            helios::int4 int_value(x, y, z, w);
            context->setPrimitiveData(uuid, label, int_value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveData): Unknown error setting primitive data int4.");
        }
    }
    
    void getPrimitiveDataInt2(helios::Context* context, unsigned int uuid, const char* label, int* x, int* y) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label || !x || !y) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or coordinate pointers are null");
                return;
            }
            helios::int2 int_value;
            context->getPrimitiveData(uuid, label, int_value);
            *x = int_value.x;
            *y = int_value.y;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveData): Unknown error getting primitive data int2.");
        }
    }
    
    void getPrimitiveDataInt3(helios::Context* context, unsigned int uuid, const char* label, int* x, int* y, int* z) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label || !x || !y || !z) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or coordinate pointers are null");
                return;
            }
            helios::int3 int_value;
            context->getPrimitiveData(uuid, label, int_value);
            *x = int_value.x;
            *y = int_value.y;
            *z = int_value.z;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveData): Unknown error getting primitive data int3.");
        }
    }
    
    void getPrimitiveDataInt4(helios::Context* context, unsigned int uuid, const char* label, int* x, int* y, int* z, int* w) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label || !x || !y || !z || !w) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or coordinate pointers are null");
                return;
            }
            helios::int4 int_value;
            context->getPrimitiveData(uuid, label, int_value);
            *x = int_value.x;
            *y = int_value.y;
            *z = int_value.z;
            *w = int_value.w;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveData): Unknown error getting primitive data int4.");
        }
    }
    
    // Extended primitive data functions - UInt and Double getters
    unsigned int getPrimitiveDataUInt(helios::Context* context, unsigned int uuid, const char* label) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return 0;
            }
            unsigned int value;
            context->getPrimitiveData(uuid, label, value);
            return value;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveData): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveData): Unknown error getting primitive data uint.");
            return 0;
        }
    }
    
    double getPrimitiveDataDouble(helios::Context* context, unsigned int uuid, const char* label) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0.0;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return 0.0;
            }
            double value;
            context->getPrimitiveData(uuid, label, value);
            return value;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveData): ") + e.what());
            return 0.0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveData): Unknown error getting primitive data double.");
            return 0.0;
        }
    }
    
    // Auto-detection primitive data getter - detects type and returns appropriate value
    int getPrimitiveDataAuto(helios::Context* context, unsigned int uuid, const char* label) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return 0;
            }
            
            // Check if the data exists first
            if (!context->doesPrimitiveDataExist(uuid, label)) {
                setError(PYHELIOS_ERROR_RUNTIME, std::string("Primitive data '") + label + "' does not exist for UUID " + std::to_string(uuid));
                return 0;
            }
            
            // Get the data type using the Helios method (without UUID - data types are global per label)
            helios::HeliosDataType data_type = context->getPrimitiveDataType(label);
            
            // Return the data as the appropriate type
            // Note: This simplified implementation only handles basic types
            // For more complex types (vec2, vec3, etc.), the Python layer should use explicit typing
            switch(data_type) {
                case helios::HELIOS_TYPE_INT:
                case helios::HELIOS_TYPE_INT2:
                case helios::HELIOS_TYPE_INT3:
                case helios::HELIOS_TYPE_INT4: {
                    int value;
                    context->getPrimitiveData(uuid, label, value);
                    return value;
                }
                case helios::HELIOS_TYPE_UINT: {
                    unsigned int value;
                    context->getPrimitiveData(uuid, label, value);
                    return (int)value;  // Cast to int for simplicity
                }
                case helios::HELIOS_TYPE_FLOAT:
                case helios::HELIOS_TYPE_VEC2:
                case helios::HELIOS_TYPE_VEC3:
                case helios::HELIOS_TYPE_VEC4: {
                    float value;
                    context->getPrimitiveData(uuid, label, value);
                    return (int)value;  // Cast to int for simplicity
                }
                case helios::HELIOS_TYPE_DOUBLE: {
                    double value;
                    context->getPrimitiveData(uuid, label, value);
                    return (int)value;  // Cast to int for simplicity
                }
                case helios::HELIOS_TYPE_STRING: {
                    // For strings, return the length as an integer
                    std::string value;
                    context->getPrimitiveData(uuid, label, value);
                    return (int)value.length();
                }
                default:
                    setError(PYHELIOS_ERROR_RUNTIME, "Unsupported data type for auto-detection");
                    return 0;
            }
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveDataAuto): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveDataAuto): Unknown error getting primitive data with auto-detection.");
            return 0;
        }
    }

    void colorPrimitiveByDataPseudocolor(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* primitive_data, const char* colormap, unsigned int ncolors) {
        if (context == nullptr) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (colorPrimitiveByDataPseudocolor): Context pointer is null.");
            return;
        }
        if (uuids == nullptr) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (colorPrimitiveByDataPseudocolor): UUIDs array pointer is null.");
            return;
        }
        if (primitive_data == nullptr) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (colorPrimitiveByDataPseudocolor): Primitive data string is null.");
            return;
        }
        if (colormap == nullptr) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (colorPrimitiveByDataPseudocolor): Colormap string is null.");
            return;
        }
        if (num_uuids == 0) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (colorPrimitiveByDataPseudocolor): Number of UUIDs must be greater than 0.");
            return;
        }
        if (ncolors == 0) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (colorPrimitiveByDataPseudocolor): Number of colors must be greater than 0.");
            return;
        }
        
        try {
            // Convert C array to std::vector
            std::vector<uint> uuid_vector(uuids, uuids + num_uuids);
            
            // Call the Helios Context method
            context->colorPrimitiveByDataPseudocolor(uuid_vector, std::string(primitive_data), std::string(colormap), ncolors);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (colorPrimitiveByDataPseudocolor): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (colorPrimitiveByDataPseudocolor): Unknown error applying pseudocolor mapping.");
        }
    }

    void colorPrimitiveByDataPseudocolorWithRange(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* primitive_data, const char* colormap, unsigned int ncolors, float data_min, float data_max) {
        if (context == nullptr) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (colorPrimitiveByDataPseudocolorWithRange): Context pointer is null.");
            return;
        }
        if (uuids == nullptr) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (colorPrimitiveByDataPseudocolorWithRange): UUIDs array pointer is null.");
            return;
        }
        if (primitive_data == nullptr) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (colorPrimitiveByDataPseudocolorWithRange): Primitive data string is null.");
            return;
        }
        if (colormap == nullptr) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (colorPrimitiveByDataPseudocolorWithRange): Colormap string is null.");
            return;
        }
        if (num_uuids == 0) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (colorPrimitiveByDataPseudocolorWithRange): Number of UUIDs must be greater than 0.");
            return;
        }
        if (ncolors == 0) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (colorPrimitiveByDataPseudocolorWithRange): Number of colors must be greater than 0.");
            return;
        }
        if (data_min >= data_max) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (colorPrimitiveByDataPseudocolorWithRange): data_min must be less than data_max.");
            return;
        }
        
        try {
            // Convert C array to std::vector
            std::vector<uint> uuid_vector(uuids, uuids + num_uuids);
            
            // Call the Helios Context method with range
            context->colorPrimitiveByDataPseudocolor(uuid_vector, std::string(primitive_data), std::string(colormap), ncolors, data_min, data_max);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (colorPrimitiveByDataPseudocolorWithRange): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (colorPrimitiveByDataPseudocolorWithRange): Unknown error applying pseudocolor mapping with range.");
        }
    }

#ifdef RADIATION_PLUGIN_AVAILABLE
    // RadiationModel C interface functions
    
    RadiationModel* createRadiationModel(helios::Context* context) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return nullptr;
            }
            return new RadiationModel(context);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::constructor): ") + e.what());
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::constructor): Unknown error creating RadiationModel.");
            return nullptr;
        }
    }
    
    void destroyRadiationModel(RadiationModel* radiation_model) {
        try {
            clearError();
            if (radiation_model != nullptr) {
                delete radiation_model;
            }
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::destructor): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::destructor): Unknown error destroying RadiationModel.");
        }
    }
    
    void disableRadiationMessages(RadiationModel* radiation_model) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            radiation_model->disableMessages();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::disableMessages): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::disableMessages): Unknown error disabling messages.");
        }
    }
    
    void enableRadiationMessages(RadiationModel* radiation_model) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            radiation_model->enableMessages();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::enableMessages): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::enableMessages): Unknown error enabling messages.");
        }
    }
    
    void addRadiationBand(RadiationModel* radiation_model, const char* label) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            radiation_model->addRadiationBand(std::string(label));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::addRadiationBand): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::addRadiationBand): Unknown error adding radiation band.");
        }
    }
    
    void addRadiationBandWithWavelengths(RadiationModel* radiation_model, const char* label, float wavelength_min, float wavelength_max) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            radiation_model->addRadiationBand(std::string(label), wavelength_min, wavelength_max);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::addRadiationBandWithWavelengths): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::addRadiationBandWithWavelengths): Unknown error adding radiation band with wavelengths.");
        }
    }
    
    void copyRadiationBand(RadiationModel* radiation_model, const char* old_label, const char* new_label) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!old_label || !new_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            radiation_model->copyRadiationBand(std::string(old_label), std::string(new_label));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::copyRadiationBand): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::copyRadiationBand): Unknown error copying radiation band.");
        }
    }
    
    unsigned int addCollimatedRadiationSourceDefault(RadiationModel* radiation_model) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return 0;
            }
            return radiation_model->addCollimatedRadiationSource();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::addCollimatedRadiationSource): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::addCollimatedRadiationSource): Unknown error adding collimated radiation source.");
            return 0;
        }
    }
    
    unsigned int addCollimatedRadiationSourceVec3(RadiationModel* radiation_model, float x, float y, float z) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return 0;
            }
            helios::vec3 direction(x, y, z);
            return radiation_model->addCollimatedRadiationSource(direction);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::addCollimatedRadiationSource): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::addCollimatedRadiationSource): Unknown error adding collimated radiation source with vec3.");
            return 0;
        }
    }
    
    unsigned int addCollimatedRadiationSourceSpherical(RadiationModel* radiation_model, float radius, float elevation, float azimuth) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return 0;
            }
            helios::SphericalCoord direction(radius, elevation, azimuth);
            return radiation_model->addCollimatedRadiationSource(direction);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::addCollimatedRadiationSource): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::addCollimatedRadiationSource): Unknown error adding collimated radiation source with spherical coordinates.");
            return 0;
        }
    }
    
    unsigned int addSphereRadiationSource(RadiationModel* radiation_model, float x, float y, float z, float radius) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return 0;
            }
            helios::vec3 position(x, y, z);
            return radiation_model->addSphereRadiationSource(position, radius);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::addSphereRadiationSource): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::addSphereRadiationSource): Unknown error adding sphere radiation source.");
            return 0;
        }
    }
    
    unsigned int addSunSphereRadiationSource(RadiationModel* radiation_model, float radius, float zenith, float azimuth, float position_scaling, float angular_width, float flux_scaling) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return 0;
            }
            helios::SphericalCoord sun_direction(radius, zenith, azimuth);
            return radiation_model->addSunSphereRadiationSource(sun_direction);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::addSunSphereRadiationSource): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::addSunSphereRadiationSource): Unknown error adding sun sphere radiation source.");
            return 0;
        }
    }
    
    void setDirectRayCount(RadiationModel* radiation_model, const char* label, size_t count) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            radiation_model->setDirectRayCount(std::string(label), count);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setDirectRayCount): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setDirectRayCount): Unknown error setting direct ray count.");
        }
    }
    
    void setDiffuseRayCount(RadiationModel* radiation_model, const char* label, size_t count) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            radiation_model->setDiffuseRayCount(std::string(label), count);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setDiffuseRayCount): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setDiffuseRayCount): Unknown error setting diffuse ray count.");
        }
    }
    
    void setDiffuseRadiationFlux(RadiationModel* radiation_model, const char* label, float flux) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            radiation_model->setDiffuseRadiationFlux(std::string(label), flux);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setDiffuseRadiationFlux): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setDiffuseRadiationFlux): Unknown error setting diffuse radiation flux.");
        }
    }
    
    void setSourceFlux(RadiationModel* radiation_model, unsigned int source_id, const char* label, float flux) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            radiation_model->setSourceFlux(source_id, std::string(label), flux);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setSourceFlux): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setSourceFlux): Unknown error setting source flux.");
        }
    }
    
    void setSourceFluxMultiple(RadiationModel* radiation_model, unsigned int* source_ids, size_t count, const char* label, float flux) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!source_ids || !label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameters are null");
                return;
            }
            std::vector<unsigned int> id_vector(source_ids, source_ids + count);
            radiation_model->setSourceFlux(id_vector, std::string(label), flux);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setSourceFlux): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setSourceFlux): Unknown error setting multiple source flux.");
        }
    }
    
    float getSourceFlux(RadiationModel* radiation_model, unsigned int source_id, const char* label) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return 0.0f;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return 0.0f;
            }
            return radiation_model->getSourceFlux(source_id, std::string(label));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::getSourceFlux): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::getSourceFlux): Unknown error getting source flux.");
            return 0.0f;
        }
    }
    
    void setScatteringDepth(RadiationModel* radiation_model, const char* label, unsigned int depth) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            radiation_model->setScatteringDepth(std::string(label), depth);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setScatteringDepth): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setScatteringDepth): Unknown error setting scattering depth.");
        }
    }
    
    void setMinScatterEnergy(RadiationModel* radiation_model, const char* label, float energy) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            radiation_model->setMinScatterEnergy(std::string(label), energy);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::setMinScatterEnergy): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::setMinScatterEnergy): Unknown error setting min scatter energy.");
        }
    }
    
    void disableEmission(RadiationModel* radiation_model, const char* label) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            radiation_model->disableEmission(std::string(label));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::disableEmission): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::disableEmission): Unknown error disabling emission.");
        }
    }
    
    void enableEmission(RadiationModel* radiation_model, const char* label) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            radiation_model->enableEmission(std::string(label));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::enableEmission): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::enableEmission): Unknown error enabling emission.");
        }
    }
    
    void updateRadiationGeometry(RadiationModel* radiation_model) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            radiation_model->updateGeometry();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::updateGeometry): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::updateGeometry): Unknown error updating geometry.");
        }
    }
    
    void updateRadiationGeometryUUIDs(RadiationModel* radiation_model, unsigned int* uuids, size_t count) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null");
                return;
            }
            std::vector<unsigned int> uuid_vector(uuids, uuids + count);
            radiation_model->updateGeometry(uuid_vector);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::updateGeometry): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::updateGeometry): Unknown error updating specific geometry.");
        }
    }
    
    void runRadiationBand(RadiationModel* radiation_model, const char* label) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            radiation_model->runBand(std::string(label));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::runBand): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::runBand): Unknown error running radiation band.");
        }
    }
    
    void runRadiationBandMultiple(RadiationModel* radiation_model, const char** labels, size_t count) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                return;
            }
            if (!labels) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Labels array is null");
                return;
            }
            std::vector<std::string> label_vector;
            for (size_t i = 0; i < count; i++) {
                if (labels[i]) {
                    label_vector.push_back(std::string(labels[i]));
                }
            }
            radiation_model->runBand(label_vector);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::runBand): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::runBand): Unknown error running multiple radiation bands.");
        }
    }
    
    float* getTotalAbsorbedFlux(RadiationModel* radiation_model, size_t* size) {
        try {
            clearError();
            if (!radiation_model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "RadiationModel pointer is null");
                if (size) *size = 0;
                return nullptr;
            }
            if (!size) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Size pointer is null");
                return nullptr;
            }
            
            std::vector<float> flux_data = radiation_model->getTotalAbsorbedFlux();
            
            // Allocate static buffer for flux data
            static std::vector<float> flux_buffer;
            flux_buffer = flux_data;
            *size = flux_buffer.size();
            return flux_buffer.data();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (RadiationModel::getTotalAbsorbedFlux): ") + e.what());
            if (size) *size = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (RadiationModel::getTotalAbsorbedFlux): Unknown error getting absorbed flux.");
            if (size) *size = 0;
            return nullptr;
        }
    }

    //=============================================================================
    // Primitive Data Functions
    //=============================================================================
    
    void setPrimitiveDataFloat(helios::Context* context, unsigned int uuid, const char* label, float value) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            context->setPrimitiveData(uuid, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveData): Unknown error setting primitive data float.");
        }
    }
    
    float getPrimitiveDataFloat(helios::Context* context, unsigned int uuid, const char* label) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0.0f;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return 0.0f;
            }
            float value;
            context->getPrimitiveData(uuid, label, value);
            return value;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveData): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveData): Unknown error getting primitive data float.");
            return 0.0f;
        }
    }
    
    void setPrimitiveDataVec3(helios::Context* context, unsigned int uuid, const char* label, float x, float y, float z) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            helios::vec3 vec_value(x, y, z);
            context->setPrimitiveData(uuid, label, vec_value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveData): Unknown error setting primitive data vec3.");
        }
    }
    
    void getPrimitiveDataVec3(helios::Context* context, unsigned int uuid, const char* label, float* x, float* y, float* z) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label || !x || !y || !z) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or coordinate pointers are null");
                return;
            }
            helios::vec3 vec_value;
            context->getPrimitiveData(uuid, label, vec_value);
            *x = vec_value.x;
            *y = vec_value.y;
            *z = vec_value.z;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveData): Unknown error getting primitive data vec3.");
        }
    }
    
    void setPrimitiveDataInt(helios::Context* context, unsigned int uuid, const char* label, int value) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            context->setPrimitiveData(uuid, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveData): Unknown error setting primitive data int.");
        }
    }
    
    int getPrimitiveDataInt(helios::Context* context, unsigned int uuid, const char* label) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return 0;
            }
            int value;
            context->getPrimitiveData(uuid, label, value);
            return value;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveData): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveData): Unknown error getting primitive data int.");
            return 0;
        }
    }
    
    bool doesPrimitiveDataExist(helios::Context* context, unsigned int uuid, const char* label) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return false;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return false;
            }
            return context->doesPrimitiveDataExist(uuid, label);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::doesPrimitiveDataExist): ") + e.what());
            return false;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::doesPrimitiveDataExist): Unknown error checking primitive data existence.");
            return false;
        }
    }
    
    void setPrimitiveDataString(helios::Context* context, unsigned int uuid, const char* label, const char* value) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label || !value) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or value is null");
                return;
            }
            std::string string_value(value);
            context->setPrimitiveData(uuid, label, string_value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveData): Unknown error setting primitive data string.");
        }
    }
    
    int getPrimitiveDataString(helios::Context* context, unsigned int uuid, const char* label, char* buffer, int buffer_size) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0;
            }
            if (!label || !buffer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or buffer is null");
                return 0;
            }
            std::string string_value;
            context->getPrimitiveData(uuid, label, string_value);
            int length = static_cast<int>(string_value.length());
            if (length < buffer_size) {
                strcpy(buffer, string_value.c_str());
            } else {
                strncpy(buffer, string_value.c_str(), buffer_size - 1);
                buffer[buffer_size - 1] = '\0';
                length = buffer_size - 1;
            }
            return length;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveData): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveData): Unknown error getting primitive data string.");
            return 0;
        }
    }
    
    void setPrimitiveDataUInt(helios::Context* context, unsigned int uuid, const char* label, unsigned int value) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            context->setPrimitiveData(uuid, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveData): Unknown error setting primitive data uint.");
        }
    }
    
    unsigned int getPrimitiveDataUInt(helios::Context* context, unsigned int uuid, const char* label) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return 0;
            }
            unsigned int value;
            context->getPrimitiveData(uuid, label, value);
            return value;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveData): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveData): Unknown error getting primitive data uint.");
            return 0;
        }
    }
    
    void setPrimitiveDataDouble(helios::Context* context, unsigned int uuid, const char* label, double value) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            context->setPrimitiveData(uuid, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveData): Unknown error setting primitive data double.");
        }
    }
    
    double getPrimitiveDataDouble(helios::Context* context, unsigned int uuid, const char* label) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0.0;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return 0.0;
            }
            double value;
            context->getPrimitiveData(uuid, label, value);
            return value;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveData): ") + e.what());
            return 0.0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveData): Unknown error getting primitive data double.");
            return 0.0;
        }
    }
    
    int getPrimitiveDataType(helios::Context* context, unsigned int uuid, const char* label) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return -1;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return -1;
            }
            helios::HeliosDataType data_type = context->getPrimitiveDataType(label);
            return static_cast<int>(data_type);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveDataType): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveDataType): Unknown error getting primitive data type.");
            return -1;
        }
    }
    
    int getPrimitiveDataSize(helios::Context* context, unsigned int uuid, const char* label) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return 0;
            }
            unsigned int size = context->getPrimitiveDataSize(uuid, label);
            return static_cast<int>(size);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveDataSize): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveDataSize): Unknown error getting primitive data size.");
            return 0;
        }
    }
    
    void setPrimitiveDataVec2(helios::Context* context, unsigned int uuid, const char* label, float x, float y) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            helios::vec2 vec_value(x, y);
            context->setPrimitiveData(uuid, label, vec_value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveData): Unknown error setting primitive data vec2.");
        }
    }
    
    void getPrimitiveDataVec2(helios::Context* context, unsigned int uuid, const char* label, float* x, float* y) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label || !x || !y) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or coordinate pointers are null");
                return;
            }
            helios::vec2 vec_value;
            context->getPrimitiveData(uuid, label, vec_value);
            *x = vec_value.x;
            *y = vec_value.y;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveData): Unknown error getting primitive data vec2.");
        }
    }
    
    void setPrimitiveDataVec4(helios::Context* context, unsigned int uuid, const char* label, float x, float y, float z, float w) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            helios::vec4 vec_value(x, y, z, w);
            context->setPrimitiveData(uuid, label, vec_value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveData): Unknown error setting primitive data vec4.");
        }
    }
    
    void getPrimitiveDataVec4(helios::Context* context, unsigned int uuid, const char* label, float* x, float* y, float* z, float* w) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label || !x || !y || !z || !w) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or coordinate pointers are null");
                return;
            }
            helios::vec4 vec_value;
            context->getPrimitiveData(uuid, label, vec_value);
            *x = vec_value.x;
            *y = vec_value.y;
            *z = vec_value.z;
            *w = vec_value.w;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveData): Unknown error getting primitive data vec4.");
        }
    }
    
    void setPrimitiveDataInt2(helios::Context* context, unsigned int uuid, const char* label, int x, int y) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            helios::int2 int_value(x, y);
            context->setPrimitiveData(uuid, label, int_value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveData): Unknown error setting primitive data int2.");
        }
    }
    
    void getPrimitiveDataInt2(helios::Context* context, unsigned int uuid, const char* label, int* x, int* y) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label || !x || !y) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or coordinate pointers are null");
                return;
            }
            helios::int2 int_value;
            context->getPrimitiveData(uuid, label, int_value);
            *x = int_value.x;
            *y = int_value.y;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveData): Unknown error getting primitive data int2.");
        }
    }
    
    void setPrimitiveDataInt3(helios::Context* context, unsigned int uuid, const char* label, int x, int y, int z) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            helios::int3 int_value(x, y, z);
            context->setPrimitiveData(uuid, label, int_value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveData): Unknown error setting primitive data int3.");
        }
    }
    
    void getPrimitiveDataInt3(helios::Context* context, unsigned int uuid, const char* label, int* x, int* y, int* z) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label || !x || !y || !z) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or coordinate pointers are null");
                return;
            }
            helios::int3 int_value;
            context->getPrimitiveData(uuid, label, int_value);
            *x = int_value.x;
            *y = int_value.y;
            *z = int_value.z;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveData): Unknown error getting primitive data int3.");
        }
    }
    
    void setPrimitiveDataInt4(helios::Context* context, unsigned int uuid, const char* label, int x, int y, int z, int w) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            helios::int4 int_value(x, y, z, w);
            context->setPrimitiveData(uuid, label, int_value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveData): Unknown error setting primitive data int4.");
        }
    }
    
    void getPrimitiveDataInt4(helios::Context* context, unsigned int uuid, const char* label, int* x, int* y, int* z, int* w) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!label || !x || !y || !z || !w) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or coordinate pointers are null");
                return;
            }
            helios::int4 int_value;
            context->getPrimitiveData(uuid, label, int_value);
            *x = int_value.x;
            *y = int_value.y;
            *z = int_value.z;
            *w = int_value.w;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveData): Unknown error getting primitive data int4.");
        }
    }
    
    int getPrimitiveDataGeneric(helios::Context* context, unsigned int uuid, const char* label, void* result_buffer, int max_buffer_size) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return -1;
            }
            if (!label || !result_buffer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or result buffer is null");
                return -1;
            }
            
            // Get the data type first
            helios::HeliosDataType data_type = context->getPrimitiveDataType(label);
            int type_int = static_cast<int>(data_type);
            
            // Get the data based on type
            switch (data_type) {
                case helios::HELIOS_TYPE_INT: {
                    if (max_buffer_size < sizeof(int)) {
                        setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Buffer too small for int");
                        return -1;
                    }
                    int value;
                    context->getPrimitiveData(uuid, label, value);
                    *((int*)result_buffer) = value;
                    break;
                }
                case helios::HELIOS_TYPE_UINT: {
                    if (max_buffer_size < sizeof(unsigned int)) {
                        setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Buffer too small for uint");
                        return -1;
                    }
                    unsigned int value;
                    context->getPrimitiveData(uuid, label, value);
                    *((unsigned int*)result_buffer) = value;
                    break;
                }
                case helios::HELIOS_TYPE_FLOAT: {
                    if (max_buffer_size < sizeof(float)) {
                        setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Buffer too small for float");
                        return -1;
                    }
                    float value;
                    context->getPrimitiveData(uuid, label, value);
                    *((float*)result_buffer) = value;
                    break;
                }
                case helios::HELIOS_TYPE_DOUBLE: {
                    if (max_buffer_size < sizeof(double)) {
                        setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Buffer too small for double");
                        return -1;
                    }
                    double value;
                    context->getPrimitiveData(uuid, label, value);
                    *((double*)result_buffer) = value;
                    break;
                }
                case helios::HELIOS_TYPE_VEC2: {
                    if (max_buffer_size < 2 * sizeof(float)) {
                        setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Buffer too small for vec2");
                        return -1;
                    }
                    helios::vec2 value;
                    context->getPrimitiveData(uuid, label, value);
                    float* buffer = (float*)result_buffer;
                    buffer[0] = value.x;
                    buffer[1] = value.y;
                    break;
                }
                case helios::HELIOS_TYPE_VEC3: {
                    if (max_buffer_size < 3 * sizeof(float)) {
                        setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Buffer too small for vec3");
                        return -1;
                    }
                    helios::vec3 value;
                    context->getPrimitiveData(uuid, label, value);
                    float* buffer = (float*)result_buffer;
                    buffer[0] = value.x;
                    buffer[1] = value.y;
                    buffer[2] = value.z;
                    break;
                }
                case helios::HELIOS_TYPE_VEC4: {
                    if (max_buffer_size < 4 * sizeof(float)) {
                        setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Buffer too small for vec4");
                        return -1;
                    }
                    helios::vec4 value;
                    context->getPrimitiveData(uuid, label, value);
                    float* buffer = (float*)result_buffer;
                    buffer[0] = value.x;
                    buffer[1] = value.y;
                    buffer[2] = value.z;
                    buffer[3] = value.w;
                    break;
                }
                case helios::HELIOS_TYPE_INT2: {
                    if (max_buffer_size < 2 * sizeof(int)) {
                        setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Buffer too small for int2");
                        return -1;
                    }
                    helios::int2 value;
                    context->getPrimitiveData(uuid, label, value);
                    int* buffer = (int*)result_buffer;
                    buffer[0] = value.x;
                    buffer[1] = value.y;
                    break;
                }
                case helios::HELIOS_TYPE_INT3: {
                    if (max_buffer_size < 3 * sizeof(int)) {
                        setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Buffer too small for int3");
                        return -1;
                    }
                    helios::int3 value;
                    context->getPrimitiveData(uuid, label, value);
                    int* buffer = (int*)result_buffer;
                    buffer[0] = value.x;
                    buffer[1] = value.y;
                    buffer[2] = value.z;
                    break;
                }
                case helios::HELIOS_TYPE_INT4: {
                    if (max_buffer_size < 4 * sizeof(int)) {
                        setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Buffer too small for int4");
                        return -1;
                    }
                    helios::int4 value;
                    context->getPrimitiveData(uuid, label, value);
                    int* buffer = (int*)result_buffer;
                    buffer[0] = value.x;
                    buffer[1] = value.y;
                    buffer[2] = value.z;
                    buffer[3] = value.w;
                    break;
                }
                case helios::HELIOS_TYPE_STRING: {
                    std::string value;
                    context->getPrimitiveData(uuid, label, value);
                    int length = static_cast<int>(value.length());
                    if (length >= max_buffer_size) {
                        // Truncate to fit in buffer
                        length = max_buffer_size - 1;
                    }
                    strncpy((char*)result_buffer, value.c_str(), length);
                    ((char*)result_buffer)[length] = '\0';
                    break;
                }
                default:
                    setError(PYHELIOS_ERROR_RUNTIME, "Unsupported data type");
                    return -1;
            }
            
            return type_int;
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getPrimitiveDataGeneric): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getPrimitiveDataGeneric): Unknown error getting primitive data.");
            return -1;
        }
    }


#endif
}