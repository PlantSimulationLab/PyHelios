// PyHelios C Interface - Context Functions
// Provides Context creation, geometry management, primitive operations, and data functions

#include "../include/pyhelios_wrapper_common.h"
#include "../include/pyhelios_wrapper_context.h"
#include "Context.h"
#include <string>
#include <exception>
#include <cstring>
#include <cstdio>
#include <atomic>
#include <unordered_map>

extern "C" {
    // Context management - core functionality required by PyHelios
    PYHELIOS_API helios::Context* createContext() {
        return new helios::Context();
    }
    
    PYHELIOS_API void destroyContext(helios::Context* context) {
        delete context;
    }
    
    // Context state management
    PYHELIOS_API void markGeometryClean(helios::Context* context) {
        context->markGeometryClean();
    }
    
    PYHELIOS_API void markGeometryDirty(helios::Context* context) {
        context->markGeometryDirty();
    }
    
    PYHELIOS_API bool isGeometryDirty(helios::Context* context) {
        return context->isGeometryDirty();
    }

    // Random number generator seeding
    PYHELIOS_API void seedRandomGenerator(helios::Context* context, unsigned int seed) {
        context->seedRandomGenerator(seed);
    }

    // Basic primitive creation
    PYHELIOS_API unsigned int addPatch(helios::Context* context) {
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
    
    PYHELIOS_API unsigned int addPatchWithCenterAndSize(helios::Context* context, float* center, float* size) {
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
    
    PYHELIOS_API unsigned int addPatchWithCenterSizeAndRotation(helios::Context* context, float* center, float* size, float* rotation) {
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
    
    PYHELIOS_API unsigned int addPatchWithCenterSizeRotationAndColor(helios::Context* context, float* center, float* size, float* rotation, float* color) {
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
    
    PYHELIOS_API unsigned int addPatchWithCenterSizeRotationAndColorRGBA(helios::Context* context, float* center, float* size, float* rotation, float* color) {
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
    
    PYHELIOS_API unsigned int addPatchWithTexture(helios::Context* context, float* center, float* size, float* rotation, const char* texture_file) {
        try {
            clearError();
            helios::vec3 center_vec(center[0], center[1], center[2]);
            helios::vec2 size_vec(size[0], size[1]);
            helios::SphericalCoord rotation_coord = helios::make_SphericalCoord(rotation[0], rotation[1], rotation[2]);
            return context->addPatch(center_vec, size_vec, rotation_coord, texture_file);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addPatch): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addPatch): Unknown error creating textured patch.");
            return 0;
        }
    }

    PYHELIOS_API unsigned int addPatchWithTextureAndUV(helios::Context* context, float* center, float* size, float* rotation, const char* texture_file, float* uv_center, float* uv_size) {
        try {
            clearError();
            helios::vec3 center_vec(center[0], center[1], center[2]);
            helios::vec2 size_vec(size[0], size[1]);
            helios::SphericalCoord rotation_coord = helios::make_SphericalCoord(rotation[0], rotation[1], rotation[2]);
            helios::vec2 uv_center_vec(uv_center[0], uv_center[1]);
            helios::vec2 uv_size_vec(uv_size[0], uv_size[1]);
            return context->addPatch(center_vec, size_vec, rotation_coord, texture_file, uv_center_vec, uv_size_vec);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addPatch): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addPatch): Unknown error creating textured patch with UV.");
            return 0;
        }
    }

    // Triangle creation functions
    PYHELIOS_API unsigned int addTriangle(helios::Context* context, float* vertex0, float* vertex1, float* vertex2) {
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
    
    PYHELIOS_API unsigned int addTriangleWithColor(helios::Context* context, float* vertex0, float* vertex1, float* vertex2, float* color) {
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
    
    PYHELIOS_API unsigned int addTriangleWithColorRGBA(helios::Context* context, float* vertex0, float* vertex1, float* vertex2, float* color) {
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
    
    PYHELIOS_API unsigned int addTriangleWithTexture(helios::Context* context, float* vertex0, float* vertex1, float* vertex2, const char* texture_file, float* uv0, float* uv1, float* uv2) {
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
    
    // Multi-texture triangle function - supports material IDs for texture assignment
    unsigned int* addTrianglesFromArraysMultiTextured(helios::Context* context, 
                                                     float* vertices, unsigned int vertex_count,
                                                     unsigned int* faces, unsigned int face_count,
                                                     float* uv_coords,
                                                     const char** texture_files, unsigned int texture_count,
                                                     unsigned int* material_ids,
                                                     unsigned int* result_count) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                *result_count = 0;
                return nullptr;
            }
            
            // Validate input parameters
            if (!vertices || !faces || !uv_coords || !texture_files || !material_ids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "One or more input arrays is null");
                *result_count = 0;
                return nullptr;
            }
            
            if (vertex_count == 0 || face_count == 0 || texture_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Vertex, face, or texture count is zero");
                *result_count = 0;
                return nullptr;
            }
            
            // Group faces by material ID for efficient processing
            std::map<unsigned int, std::vector<unsigned int>> material_groups;
            for (unsigned int i = 0; i < face_count; i++) {
                unsigned int material_id = material_ids[i];
                if (material_id >= texture_count) {
                    setError(PYHELIOS_ERROR_INVALID_PARAMETER, 
                            "Material ID " + std::to_string(material_id) + " exceeds texture count " + std::to_string(texture_count));
                    *result_count = 0;
                    return nullptr;
                }
                material_groups[material_id].push_back(i);
            }
            
            // Pre-allocate result vector for all triangles
            static thread_local std::vector<unsigned int> triangle_uuids;
            triangle_uuids.clear();
            triangle_uuids.reserve(face_count);
            
            // Process each material group
            for (const auto& group : material_groups) {
                unsigned int material_id = group.first;
                const std::vector<unsigned int>& face_indices = group.second;
                const char* texture_file = texture_files[material_id];
                
                // Add triangles for this material
                for (unsigned int face_idx : face_indices) {
                    // Get vertex indices for this triangle (3 indices per face)
                    unsigned int v0_idx = faces[face_idx * 3];
                    unsigned int v1_idx = faces[face_idx * 3 + 1];
                    unsigned int v2_idx = faces[face_idx * 3 + 2];
                    
                    // Validate vertex indices
                    if (v0_idx >= vertex_count || v1_idx >= vertex_count || v2_idx >= vertex_count) {
                        setError(PYHELIOS_ERROR_INVALID_PARAMETER, 
                                "Face vertex index exceeds vertex count");
                        *result_count = 0;
                        return nullptr;
                    }
                    
                    // Get vertex coordinates (3 floats per vertex)
                    helios::vec3 vertex0(vertices[v0_idx * 3], vertices[v0_idx * 3 + 1], vertices[v0_idx * 3 + 2]);
                    helios::vec3 vertex1(vertices[v1_idx * 3], vertices[v1_idx * 3 + 1], vertices[v1_idx * 3 + 2]);
                    helios::vec3 vertex2(vertices[v2_idx * 3], vertices[v2_idx * 3 + 1], vertices[v2_idx * 3 + 2]);
                    
                    // Get UV coordinates (2 floats per vertex)
                    helios::vec2 uv0(uv_coords[v0_idx * 2], uv_coords[v0_idx * 2 + 1]);
                    helios::vec2 uv1(uv_coords[v1_idx * 2], uv_coords[v1_idx * 2 + 1]);
                    helios::vec2 uv2(uv_coords[v2_idx * 2], uv_coords[v2_idx * 2 + 1]);
                    
                    // Add textured triangle using existing Helios API
                    unsigned int triangle_uuid = context->addTriangle(vertex0, vertex1, vertex2, texture_file, uv0, uv1, uv2);
                    triangle_uuids.push_back(triangle_uuid);
                }
            }
            
            *result_count = triangle_uuids.size();
            return triangle_uuids.data();
            
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            *result_count = 0;
            return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addTrianglesFromArraysMultiTextured): ") + e.what());
            *result_count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addTrianglesFromArraysMultiTextured): Unknown error creating textured triangles.");
            *result_count = 0;
            return nullptr;
        }
    }
    
    // Compound geometry creation functions - return arrays of UUIDs
    
    // addTile functions
    PYHELIOS_API unsigned int* addTile(helios::Context* context, float* center, float* size, float* rotation, int* subdiv, unsigned int* count) {
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
    
    PYHELIOS_API unsigned int* addTileWithColor(helios::Context* context, float* center, float* size, float* rotation, int* subdiv, float* color, unsigned int* count) {
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
    PYHELIOS_API unsigned int* addSphere(helios::Context* context, unsigned int ndivs, float* center, float radius, unsigned int* count) {
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
    
    PYHELIOS_API unsigned int* addSphereWithColor(helios::Context* context, unsigned int ndivs, float* center, float radius, float* color, unsigned int* count) {
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
    PYHELIOS_API unsigned int* addTube(helios::Context* context, unsigned int ndivs, float* nodes, unsigned int node_count, float* radii, unsigned int* count) {
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
    
    PYHELIOS_API unsigned int* addTubeWithColor(helios::Context* context, unsigned int ndivs, float* nodes, unsigned int node_count, float* radii, float* colors, unsigned int* count) {
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
    PYHELIOS_API unsigned int* addBox(helios::Context* context, float* center, float* size, int* subdiv, unsigned int* count) {
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
    
    PYHELIOS_API unsigned int* addBoxWithColor(helios::Context* context, float* center, float* size, int* subdiv, float* color, unsigned int* count) {
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

    // addDisk functions
    PYHELIOS_API unsigned int* addDisk(helios::Context* context, unsigned int ndivs, float* center, float* size, unsigned int* count) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                *count = 0;
                return nullptr;
            }

            helios::vec3 center_vec(center[0], center[1], center[2]);
            helios::vec2 size_vec(size[0], size[1]);

            std::vector<unsigned int> uuids = context->addDisk(ndivs, center_vec, size_vec);

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
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addDisk): ") + e.what());
            *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addDisk): Unknown error creating disk.");
            *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* addDiskWithRotation(helios::Context* context, unsigned int ndivs, float* center, float* size, float* rotation, unsigned int* count) {
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

            std::vector<unsigned int> uuids = context->addDisk(ndivs, center_vec, size_vec, rotation_coord);

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
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addDisk): ") + e.what());
            *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addDisk): Unknown error creating disk with rotation.");
            *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* addDiskWithColor(helios::Context* context, unsigned int ndivs, float* center, float* size, float* rotation, float* color, unsigned int* count) {
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
            helios::RGBcolor color_rgb(color[0], color[1], color[2]);

            std::vector<unsigned int> uuids = context->addDisk(ndivs, center_vec, size_vec, rotation_coord, color_rgb);

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
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addDisk): ") + e.what());
            *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addDisk): Unknown error creating disk with color.");
            *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* addDiskWithRGBAColor(helios::Context* context, unsigned int ndivs, float* center, float* size, float* rotation, float* color, unsigned int* count) {
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
            helios::RGBAcolor color_rgba(color[0], color[1], color[2], color[3]);

            std::vector<unsigned int> uuids = context->addDisk(ndivs, center_vec, size_vec, rotation_coord, color_rgba);

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
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addDisk): ") + e.what());
            *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addDisk): Unknown error creating disk with RGBA color.");
            *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* addDiskPolarSubdivisions(helios::Context* context, int* ndivs, float* center, float* size, float* rotation, float* color, unsigned int* count) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                *count = 0;
                return nullptr;
            }

            helios::int2 ndivs_int2(ndivs[0], ndivs[1]);
            helios::vec3 center_vec(center[0], center[1], center[2]);
            helios::vec2 size_vec(size[0], size[1]);
            helios::SphericalCoord rotation_coord = helios::make_SphericalCoord(rotation[0], rotation[1], rotation[2]);
            helios::RGBcolor color_rgb(color[0], color[1], color[2]);

            std::vector<unsigned int> uuids = context->addDisk(ndivs_int2, center_vec, size_vec, rotation_coord, color_rgb);

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
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addDisk): ") + e.what());
            *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addDisk): Unknown error creating disk with polar subdivisions.");
            *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* addDiskPolarSubdivisionsRGBA(helios::Context* context, int* ndivs, float* center, float* size, float* rotation, float* color, unsigned int* count) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                *count = 0;
                return nullptr;
            }

            helios::int2 ndivs_int2(ndivs[0], ndivs[1]);
            helios::vec3 center_vec(center[0], center[1], center[2]);
            helios::vec2 size_vec(size[0], size[1]);
            helios::SphericalCoord rotation_coord = helios::make_SphericalCoord(rotation[0], rotation[1], rotation[2]);
            helios::RGBAcolor color_rgba(color[0], color[1], color[2], color[3]);

            std::vector<unsigned int> uuids = context->addDisk(ndivs_int2, center_vec, size_vec, rotation_coord, color_rgba);

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
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addDisk): ") + e.what());
            *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addDisk): Unknown error creating disk with polar subdivisions and RGBA color.");
            *count = 0;
            return nullptr;
        }
    }

    // addCone functions
    PYHELIOS_API unsigned int* addCone(helios::Context* context, unsigned int ndivs, float* node0, float* node1, float radius0, float radius1, unsigned int* count) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                *count = 0;
                return nullptr;
            }

            helios::vec3 node0_vec(node0[0], node0[1], node0[2]);
            helios::vec3 node1_vec(node1[0], node1[1], node1[2]);

            std::vector<unsigned int> uuids = context->addCone(ndivs, node0_vec, node1_vec, radius0, radius1);

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
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addCone): ") + e.what());
            *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addCone): Unknown error creating cone.");
            *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* addConeWithColor(helios::Context* context, unsigned int ndivs, float* node0, float* node1, float radius0, float radius1, float* color, unsigned int* count) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                *count = 0;
                return nullptr;
            }

            helios::vec3 node0_vec(node0[0], node0[1], node0[2]);
            helios::vec3 node1_vec(node1[0], node1[1], node1[2]);
            helios::RGBcolor color_rgb(color[0], color[1], color[2]);

            std::vector<unsigned int> uuids = context->addCone(ndivs, node0_vec, node1_vec, radius0, radius1, color_rgb);

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
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addCone): ") + e.what());
            *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addCone): Unknown error creating cone with color.");
            *count = 0;
            return nullptr;
        }
    }

    // Copy operations - Primitives
    PYHELIOS_API unsigned int copyPrimitive(helios::Context* context, unsigned int uuid) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0;
            }

            return context->copyPrimitive(uuid);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::copyPrimitive): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::copyPrimitive): Unknown error copying primitive.");
            return 0;
        }
    }

    PYHELIOS_API unsigned int* copyPrimitives(helios::Context* context, unsigned int* uuids, unsigned int count, unsigned int* result_count) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                *result_count = 0;
                return nullptr;
            }
            if (!uuids || count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null or empty");
                *result_count = 0;
                return nullptr;
            }

            // Convert C array to vector
            std::vector<unsigned int> uuids_vec(uuids, uuids + count);

            std::vector<unsigned int> result = context->copyPrimitive(uuids_vec);

            // Convert vector to thread-local static array for return
            static thread_local std::vector<unsigned int> static_result;
            static_result = std::move(result);
            *result_count = static_result.size();
            return static_result.data();

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            *result_count = 0;
            return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::copyPrimitive): ") + e.what());
            *result_count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::copyPrimitive): Unknown error copying primitives.");
            *result_count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API void copyPrimitiveData(helios::Context* context, unsigned int sourceUUID, unsigned int destinationUUID) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }

            context->copyPrimitiveData(sourceUUID, destinationUUID);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::copyPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::copyPrimitiveData): Unknown error copying primitive data.");
        }
    }

    // Copy operations - Objects
    PYHELIOS_API unsigned int copyObject(helios::Context* context, unsigned int objID) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0;
            }

            return context->copyObject(objID);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::copyObject): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::copyObject): Unknown error copying object.");
            return 0;
        }
    }

    PYHELIOS_API unsigned int* copyObjects(helios::Context* context, unsigned int* objIDs, unsigned int count, unsigned int* result_count) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                *result_count = 0;
                return nullptr;
            }
            if (!objIDs || count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Object IDs array is null or empty");
                *result_count = 0;
                return nullptr;
            }

            // Convert C array to vector
            std::vector<unsigned int> objIDs_vec(objIDs, objIDs + count);

            std::vector<unsigned int> result = context->copyObject(objIDs_vec);

            // Convert vector to thread-local static array for return
            static thread_local std::vector<unsigned int> static_result;
            static_result = std::move(result);
            *result_count = static_result.size();
            return static_result.data();

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            *result_count = 0;
            return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::copyObject): ") + e.what());
            *result_count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::copyObject): Unknown error copying objects.");
            *result_count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API void copyObjectData(helios::Context* context, unsigned int source_objID, unsigned int destination_objID) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }

            context->copyObjectData(source_objID, destination_objID);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::copyObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::copyObjectData): Unknown error copying object data.");
        }
    }

    // Translation operations - Primitives
    PYHELIOS_API void translatePrimitive(helios::Context* context, unsigned int uuid, float* shift) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!shift) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Shift vector is null");
                return;
            }

            helios::vec3 shift_vec(shift[0], shift[1], shift[2]);
            context->translatePrimitive(uuid, shift_vec);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::translatePrimitive): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::translatePrimitive): Unknown error translating primitive.");
        }
    }

    PYHELIOS_API void translatePrimitives(helios::Context* context, unsigned int* uuids, unsigned int count, float* shift) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!uuids || count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null or empty");
                return;
            }
            if (!shift) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Shift vector is null");
                return;
            }

            // Convert C array to vector
            std::vector<unsigned int> uuids_vec(uuids, uuids + count);
            helios::vec3 shift_vec(shift[0], shift[1], shift[2]);

            context->translatePrimitive(uuids_vec, shift_vec);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::translatePrimitive): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::translatePrimitive): Unknown error translating primitives.");
        }
    }

    // Translation operations - Objects
    PYHELIOS_API void translateObject(helios::Context* context, unsigned int objID, float* shift) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!shift) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Shift vector is null");
                return;
            }

            helios::vec3 shift_vec(shift[0], shift[1], shift[2]);
            context->translateObject(objID, shift_vec);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::translateObject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::translateObject): Unknown error translating object.");
        }
    }

    PYHELIOS_API void translateObjects(helios::Context* context, unsigned int* objIDs, unsigned int count, float* shift) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!objIDs || count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Object IDs array is null or empty");
                return;
            }
            if (!shift) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Shift vector is null");
                return;
            }

            // Convert C array to vector
            std::vector<unsigned int> objIDs_vec(objIDs, objIDs + count);
            helios::vec3 shift_vec(shift[0], shift[1], shift[2]);

            context->translateObject(objIDs_vec, shift_vec);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::translateObject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::translateObject): Unknown error translating objects.");
        }
    }

    // ==================== Rotation Operations ====================

    // Rotate primitive with axis string (single)
    PYHELIOS_API void rotatePrimitive_axisString(helios::Context* context, unsigned int uuid, float rotation_radians, const char* axis) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!axis) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Axis string is null");
                return;
            }
            context->rotatePrimitive(uuid, rotation_radians, axis);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::rotatePrimitive): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::rotatePrimitive): Unknown error rotating primitive.");
        }
    }

    // Rotate primitives with axis string (multiple)
    PYHELIOS_API void rotatePrimitives_axisString(helios::Context* context, unsigned int* uuids, unsigned int count, float rotation_radians, const char* axis) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs pointer is null");
                return;
            }
            if (!axis) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Axis string is null");
                return;
            }
            std::vector<unsigned int> uuids_vec(uuids, uuids + count);
            context->rotatePrimitive(uuids_vec, rotation_radians, axis);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::rotatePrimitive): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::rotatePrimitive): Unknown error rotating primitives.");
        }
    }

    // Rotate primitive with axis vector (single)
    PYHELIOS_API void rotatePrimitive_axisVector(helios::Context* context, unsigned int uuid, float rotation_radians, float* axis) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!axis) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Axis vector is null");
                return;
            }
            helios::vec3 axis_vec(axis[0], axis[1], axis[2]);
            context->rotatePrimitive(uuid, rotation_radians, axis_vec);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::rotatePrimitive): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::rotatePrimitive): Unknown error rotating primitive.");
        }
    }

    // Rotate primitives with axis vector (multiple)
    PYHELIOS_API void rotatePrimitives_axisVector(helios::Context* context, unsigned int* uuids, unsigned int count, float rotation_radians, float* axis) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs pointer is null");
                return;
            }
            if (!axis) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Axis vector is null");
                return;
            }
            std::vector<unsigned int> uuids_vec(uuids, uuids + count);
            helios::vec3 axis_vec(axis[0], axis[1], axis[2]);
            context->rotatePrimitive(uuids_vec, rotation_radians, axis_vec);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::rotatePrimitive): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::rotatePrimitive): Unknown error rotating primitives.");
        }
    }

    // Rotate primitive with origin and axis vector (single)
    PYHELIOS_API void rotatePrimitive_originAxisVector(helios::Context* context, unsigned int uuid, float rotation_radians, float* origin, float* axis) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!origin) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Origin vector is null");
                return;
            }
            if (!axis) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Axis vector is null");
                return;
            }
            helios::vec3 origin_vec(origin[0], origin[1], origin[2]);
            helios::vec3 axis_vec(axis[0], axis[1], axis[2]);
            context->rotatePrimitive(uuid, rotation_radians, origin_vec, axis_vec);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::rotatePrimitive): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::rotatePrimitive): Unknown error rotating primitive.");
        }
    }

    // Rotate primitives with origin and axis vector (multiple)
    PYHELIOS_API void rotatePrimitives_originAxisVector(helios::Context* context, unsigned int* uuids, unsigned int count, float rotation_radians, float* origin, float* axis) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs pointer is null");
                return;
            }
            if (!origin) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Origin vector is null");
                return;
            }
            if (!axis) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Axis vector is null");
                return;
            }
            std::vector<unsigned int> uuids_vec(uuids, uuids + count);
            helios::vec3 origin_vec(origin[0], origin[1], origin[2]);
            helios::vec3 axis_vec(axis[0], axis[1], axis[2]);
            context->rotatePrimitive(uuids_vec, rotation_radians, origin_vec, axis_vec);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::rotatePrimitive): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::rotatePrimitive): Unknown error rotating primitives.");
        }
    }

    // Rotate object with axis string (single)
    PYHELIOS_API void rotateObject_axisString(helios::Context* context, unsigned int objID, float rotation_radians, const char* axis) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!axis) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Axis string is null");
                return;
            }
            context->rotateObject(objID, rotation_radians, axis);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::rotateObject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::rotateObject): Unknown error rotating object.");
        }
    }

    // Rotate objects with axis string (multiple)
    PYHELIOS_API void rotateObjects_axisString(helios::Context* context, unsigned int* objIDs, unsigned int count, float rotation_radians, const char* axis) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!objIDs) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Object IDs pointer is null");
                return;
            }
            if (!axis) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Axis string is null");
                return;
            }
            std::vector<unsigned int> objIDs_vec(objIDs, objIDs + count);
            context->rotateObject(objIDs_vec, rotation_radians, axis);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::rotateObject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::rotateObject): Unknown error rotating objects.");
        }
    }

    // Rotate object with axis vector (single)
    PYHELIOS_API void rotateObject_axisVector(helios::Context* context, unsigned int objID, float rotation_radians, float* axis) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!axis) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Axis vector is null");
                return;
            }
            helios::vec3 axis_vec(axis[0], axis[1], axis[2]);
            context->rotateObject(objID, rotation_radians, axis_vec);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::rotateObject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::rotateObject): Unknown error rotating object.");
        }
    }

    // Rotate objects with axis vector (multiple)
    PYHELIOS_API void rotateObjects_axisVector(helios::Context* context, unsigned int* objIDs, unsigned int count, float rotation_radians, float* axis) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!objIDs) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Object IDs pointer is null");
                return;
            }
            if (!axis) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Axis vector is null");
                return;
            }
            std::vector<unsigned int> objIDs_vec(objIDs, objIDs + count);
            helios::vec3 axis_vec(axis[0], axis[1], axis[2]);
            context->rotateObject(objIDs_vec, rotation_radians, axis_vec);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::rotateObject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::rotateObject): Unknown error rotating objects.");
        }
    }

    // Rotate object with origin and axis vector (single)
    PYHELIOS_API void rotateObject_originAxisVector(helios::Context* context, unsigned int objID, float rotation_radians, float* origin, float* axis) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!origin) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Origin vector is null");
                return;
            }
            if (!axis) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Axis vector is null");
                return;
            }
            helios::vec3 origin_vec(origin[0], origin[1], origin[2]);
            helios::vec3 axis_vec(axis[0], axis[1], axis[2]);
            context->rotateObject(objID, rotation_radians, origin_vec, axis_vec);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::rotateObject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::rotateObject): Unknown error rotating object.");
        }
    }

    // Rotate objects with origin and axis vector (multiple)
    PYHELIOS_API void rotateObjects_originAxisVector(helios::Context* context, unsigned int* objIDs, unsigned int count, float rotation_radians, float* origin, float* axis) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!objIDs) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Object IDs pointer is null");
                return;
            }
            if (!origin) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Origin vector is null");
                return;
            }
            if (!axis) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Axis vector is null");
                return;
            }
            std::vector<unsigned int> objIDs_vec(objIDs, objIDs + count);
            helios::vec3 origin_vec(origin[0], origin[1], origin[2]);
            helios::vec3 axis_vec(axis[0], axis[1], axis[2]);
            context->rotateObject(objIDs_vec, rotation_radians, origin_vec, axis_vec);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::rotateObject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::rotateObject): Unknown error rotating objects.");
        }
    }

    // Rotate object about origin with axis vector (single)
    PYHELIOS_API void rotateObjectAboutOrigin_axisVector(helios::Context* context, unsigned int objID, float rotation_radians, float* axis) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!axis) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Axis vector is null");
                return;
            }
            helios::vec3 axis_vec(axis[0], axis[1], axis[2]);
            context->rotateObjectAboutOrigin(objID, rotation_radians, axis_vec);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::rotateObjectAboutOrigin): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::rotateObjectAboutOrigin): Unknown error rotating object.");
        }
    }

    // Rotate objects about origin with axis vector (multiple)
    PYHELIOS_API void rotateObjectsAboutOrigin_axisVector(helios::Context* context, unsigned int* objIDs, unsigned int count, float rotation_radians, float* axis) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!objIDs) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Object IDs pointer is null");
                return;
            }
            if (!axis) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Axis vector is null");
                return;
            }
            std::vector<unsigned int> objIDs_vec(objIDs, objIDs + count);
            helios::vec3 axis_vec(axis[0], axis[1], axis[2]);
            context->rotateObjectAboutOrigin(objIDs_vec, rotation_radians, axis_vec);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::rotateObjectAboutOrigin): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::rotateObjectAboutOrigin): Unknown error rotating objects.");
        }
    }

    // ==================== Scaling Operations ====================

    // Scale primitive (single)
    PYHELIOS_API void scalePrimitive(helios::Context* context, unsigned int uuid, float* scale) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!scale) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Scale vector is null");
                return;
            }
            helios::vec3 scale_vec(scale[0], scale[1], scale[2]);
            context->scalePrimitive(uuid, scale_vec);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::scalePrimitive): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::scalePrimitive): Unknown error scaling primitive.");
        }
    }

    // Scale primitives (multiple)
    PYHELIOS_API void scalePrimitives(helios::Context* context, unsigned int* uuids, unsigned int count, float* scale) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs pointer is null");
                return;
            }
            if (!scale) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Scale vector is null");
                return;
            }
            std::vector<unsigned int> uuids_vec(uuids, uuids + count);
            helios::vec3 scale_vec(scale[0], scale[1], scale[2]);
            context->scalePrimitive(uuids_vec, scale_vec);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::scalePrimitive): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::scalePrimitive): Unknown error scaling primitives.");
        }
    }

    // Scale primitive about point (single)
    PYHELIOS_API void scalePrimitiveAboutPoint(helios::Context* context, unsigned int uuid, float* scale, float* point) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!scale) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Scale vector is null");
                return;
            }
            if (!point) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Point vector is null");
                return;
            }
            helios::vec3 scale_vec(scale[0], scale[1], scale[2]);
            helios::vec3 point_vec(point[0], point[1], point[2]);
            context->scalePrimitiveAboutPoint(uuid, scale_vec, point_vec);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::scalePrimitiveAboutPoint): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::scalePrimitiveAboutPoint): Unknown error scaling primitive.");
        }
    }

    // Scale primitives about point (multiple)
    PYHELIOS_API void scalePrimitivesAboutPoint(helios::Context* context, unsigned int* uuids, unsigned int count, float* scale, float* point) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs pointer is null");
                return;
            }
            if (!scale) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Scale vector is null");
                return;
            }
            if (!point) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Point vector is null");
                return;
            }
            std::vector<unsigned int> uuids_vec(uuids, uuids + count);
            helios::vec3 scale_vec(scale[0], scale[1], scale[2]);
            helios::vec3 point_vec(point[0], point[1], point[2]);
            context->scalePrimitiveAboutPoint(uuids_vec, scale_vec, point_vec);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::scalePrimitiveAboutPoint): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::scalePrimitiveAboutPoint): Unknown error scaling primitives.");
        }
    }

    // Scale object (single)
    PYHELIOS_API void scaleObject(helios::Context* context, unsigned int objID, float* scale) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!scale) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Scale vector is null");
                return;
            }
            helios::vec3 scale_vec(scale[0], scale[1], scale[2]);
            context->scaleObject(objID, scale_vec);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::scaleObject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::scaleObject): Unknown error scaling object.");
        }
    }

    // Scale objects (multiple)
    PYHELIOS_API void scaleObjects(helios::Context* context, unsigned int* objIDs, unsigned int count, float* scale) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!objIDs) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Object IDs pointer is null");
                return;
            }
            if (!scale) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Scale vector is null");
                return;
            }
            std::vector<unsigned int> objIDs_vec(objIDs, objIDs + count);
            helios::vec3 scale_vec(scale[0], scale[1], scale[2]);
            context->scaleObject(objIDs_vec, scale_vec);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::scaleObject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::scaleObject): Unknown error scaling objects.");
        }
    }

    // Scale object about center (single)
    PYHELIOS_API void scaleObjectAboutCenter(helios::Context* context, unsigned int objID, float* scale) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!scale) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Scale vector is null");
                return;
            }
            helios::vec3 scale_vec(scale[0], scale[1], scale[2]);
            context->scaleObjectAboutCenter(objID, scale_vec);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::scaleObjectAboutCenter): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::scaleObjectAboutCenter): Unknown error scaling object.");
        }
    }

    // Scale objects about center (multiple)
    PYHELIOS_API void scaleObjectsAboutCenter(helios::Context* context, unsigned int* objIDs, unsigned int count, float* scale) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!objIDs) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Object IDs pointer is null");
                return;
            }
            if (!scale) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Scale vector is null");
                return;
            }
            std::vector<unsigned int> objIDs_vec(objIDs, objIDs + count);
            helios::vec3 scale_vec(scale[0], scale[1], scale[2]);
            context->scaleObjectAboutCenter(objIDs_vec, scale_vec);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::scaleObjectAboutCenter): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::scaleObjectAboutCenter): Unknown error scaling objects.");
        }
    }

    // Scale object about point (single)
    PYHELIOS_API void scaleObjectAboutPoint(helios::Context* context, unsigned int objID, float* scale, float* point) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!scale) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Scale vector is null");
                return;
            }
            if (!point) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Point vector is null");
                return;
            }
            helios::vec3 scale_vec(scale[0], scale[1], scale[2]);
            helios::vec3 point_vec(point[0], point[1], point[2]);
            context->scaleObjectAboutPoint(objID, scale_vec, point_vec);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::scaleObjectAboutPoint): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::scaleObjectAboutPoint): Unknown error scaling object.");
        }
    }

    // Scale objects about point (multiple)
    PYHELIOS_API void scaleObjectsAboutPoint(helios::Context* context, unsigned int* objIDs, unsigned int count, float* scale, float* point) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!objIDs) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Object IDs pointer is null");
                return;
            }
            if (!scale) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Scale vector is null");
                return;
            }
            if (!point) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Point vector is null");
                return;
            }
            std::vector<unsigned int> objIDs_vec(objIDs, objIDs + count);
            helios::vec3 scale_vec(scale[0], scale[1], scale[2]);
            helios::vec3 point_vec(point[0], point[1], point[2]);
            context->scaleObjectAboutPoint(objIDs_vec, scale_vec, point_vec);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::scaleObjectAboutPoint): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::scaleObjectAboutPoint): Unknown error scaling objects.");
        }
    }

    // Scale object about origin (single)
    PYHELIOS_API void scaleObjectAboutOrigin(helios::Context* context, unsigned int objID, float* scale) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!scale) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Scale vector is null");
                return;
            }
            helios::vec3 scale_vec(scale[0], scale[1], scale[2]);
            context->scaleObjectAboutOrigin(objID, scale_vec);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::scaleObjectAboutOrigin): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::scaleObjectAboutOrigin): Unknown error scaling object.");
        }
    }

    // Scale objects about origin (multiple)
    PYHELIOS_API void scaleObjectsAboutOrigin(helios::Context* context, unsigned int* objIDs, unsigned int count, float* scale) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!objIDs) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Object IDs pointer is null");
                return;
            }
            if (!scale) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Scale vector is null");
                return;
            }
            std::vector<unsigned int> objIDs_vec(objIDs, objIDs + count);
            helios::vec3 scale_vec(scale[0], scale[1], scale[2]);
            context->scaleObjectAboutOrigin(objIDs_vec, scale_vec);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::scaleObjectAboutOrigin): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::scaleObjectAboutOrigin): Unknown error scaling objects.");
        }
    }

    // Scale cone object length
    PYHELIOS_API void scaleConeObjectLength(helios::Context* context, unsigned int objID, float scale_factor) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            context->scaleConeObjectLength(objID, scale_factor);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::scaleConeObjectLength): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::scaleConeObjectLength): Unknown error scaling cone length.");
        }
    }

    // Scale cone object girth
    PYHELIOS_API void scaleConeObjectGirth(helios::Context* context, unsigned int objID, float scale_factor) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            context->scaleConeObjectGirth(objID, scale_factor);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::scaleConeObjectGirth): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::scaleConeObjectGirth): Unknown error scaling cone girth.");
        }
    }

    // ============================================================================
    // Object-Returning Compound Geometry Methods
    // ============================================================================

    // addSphereObject - 6 overloads

    PYHELIOS_API unsigned int addSphereObject_basic(helios::Context* context, unsigned int ndivs, float* center, float radius) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0;
            }
            if (!center) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Center vector is null");
                return 0;
            }
            helios::vec3 center_vec(center[0], center[1], center[2]);
            return context->addSphereObject(ndivs, center_vec, radius);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addSphereObject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addSphereObject): Unknown error adding sphere object.");
        }
        return 0;
    }

    PYHELIOS_API unsigned int addSphereObject_color(helios::Context* context, unsigned int ndivs, float* center, float radius, float* color) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0;
            }
            if (!center) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Center vector is null");
                return 0;
            }
            if (!color) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Color vector is null");
                return 0;
            }
            helios::vec3 center_vec(center[0], center[1], center[2]);
            helios::RGBcolor color_rgb(color[0], color[1], color[2]);
            return context->addSphereObject(ndivs, center_vec, radius, color_rgb);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addSphereObject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addSphereObject): Unknown error adding sphere object.");
        }
        return 0;
    }

    PYHELIOS_API unsigned int addSphereObject_texture(helios::Context* context, unsigned int ndivs, float* center, float radius, const char* texturefile) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0;
            }
            if (!center) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Center vector is null");
                return 0;
            }
            if (!texturefile) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Texture file path is null");
                return 0;
            }
            helios::vec3 center_vec(center[0], center[1], center[2]);
            return context->addSphereObject(ndivs, center_vec, radius, texturefile);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addSphereObject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addSphereObject): Unknown error adding sphere object.");
        }
        return 0;
    }

    PYHELIOS_API unsigned int addSphereObject_ellipsoid(helios::Context* context, unsigned int ndivs, float* center, float* radius) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0;
            }
            if (!center) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Center vector is null");
                return 0;
            }
            if (!radius) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Radius vector is null");
                return 0;
            }
            helios::vec3 center_vec(center[0], center[1], center[2]);
            helios::vec3 radius_vec(radius[0], radius[1], radius[2]);
            return context->addSphereObject(ndivs, center_vec, radius_vec);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addSphereObject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addSphereObject): Unknown error adding sphere object.");
        }
        return 0;
    }

    PYHELIOS_API unsigned int addSphereObject_ellipsoid_color(helios::Context* context, unsigned int ndivs, float* center, float* radius, float* color) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0;
            }
            if (!center) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Center vector is null");
                return 0;
            }
            if (!radius) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Radius vector is null");
                return 0;
            }
            if (!color) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Color vector is null");
                return 0;
            }
            helios::vec3 center_vec(center[0], center[1], center[2]);
            helios::vec3 radius_vec(radius[0], radius[1], radius[2]);
            helios::RGBcolor color_rgb(color[0], color[1], color[2]);
            return context->addSphereObject(ndivs, center_vec, radius_vec, color_rgb);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addSphereObject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addSphereObject): Unknown error adding sphere object.");
        }
        return 0;
    }

    PYHELIOS_API unsigned int addSphereObject_ellipsoid_texture(helios::Context* context, unsigned int ndivs, float* center, float* radius, const char* texturefile) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0;
            }
            if (!center) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Center vector is null");
                return 0;
            }
            if (!radius) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Radius vector is null");
                return 0;
            }
            if (!texturefile) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Texture file path is null");
                return 0;
            }
            helios::vec3 center_vec(center[0], center[1], center[2]);
            helios::vec3 radius_vec(radius[0], radius[1], radius[2]);
            return context->addSphereObject(ndivs, center_vec, radius_vec, texturefile);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addSphereObject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addSphereObject): Unknown error adding sphere object.");
        }
        return 0;
    }

    // addTileObject - 4 overloads

    PYHELIOS_API unsigned int addTileObject_basic(helios::Context* context, float* center, float* size, float* rotation, int* subdiv) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0;
            }
            if (!center || !size || !rotation || !subdiv) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter pointer is null");
                return 0;
            }
            helios::vec3 center_vec(center[0], center[1], center[2]);
            helios::vec2 size_vec(size[0], size[1]);
            helios::SphericalCoord rotation_coord(rotation[0], rotation[1], rotation[2]);
            helios::int2 subdiv_int2(subdiv[0], subdiv[1]);
            return context->addTileObject(center_vec, size_vec, rotation_coord, subdiv_int2);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addTileObject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addTileObject): Unknown error adding tile object.");
        }
        return 0;
    }

    PYHELIOS_API unsigned int addTileObject_color(helios::Context* context, float* center, float* size, float* rotation, int* subdiv, float* color) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0;
            }
            if (!center || !size || !rotation || !subdiv || !color) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter pointer is null");
                return 0;
            }
            helios::vec3 center_vec(center[0], center[1], center[2]);
            helios::vec2 size_vec(size[0], size[1]);
            helios::SphericalCoord rotation_coord(rotation[0], rotation[1], rotation[2]);
            helios::int2 subdiv_int2(subdiv[0], subdiv[1]);
            helios::RGBcolor color_rgb(color[0], color[1], color[2]);
            return context->addTileObject(center_vec, size_vec, rotation_coord, subdiv_int2, color_rgb);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addTileObject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addTileObject): Unknown error adding tile object.");
        }
        return 0;
    }

    PYHELIOS_API unsigned int addTileObject_texture(helios::Context* context, float* center, float* size, float* rotation, int* subdiv, const char* texturefile) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0;
            }
            if (!center || !size || !rotation || !subdiv || !texturefile) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter pointer is null");
                return 0;
            }
            helios::vec3 center_vec(center[0], center[1], center[2]);
            helios::vec2 size_vec(size[0], size[1]);
            helios::SphericalCoord rotation_coord(rotation[0], rotation[1], rotation[2]);
            helios::int2 subdiv_int2(subdiv[0], subdiv[1]);
            return context->addTileObject(center_vec, size_vec, rotation_coord, subdiv_int2, texturefile);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addTileObject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addTileObject): Unknown error adding tile object.");
        }
        return 0;
    }

    PYHELIOS_API unsigned int addTileObject_texture_repeat(helios::Context* context, float* center, float* size, float* rotation, int* subdiv, const char* texturefile, int* texture_repeat) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0;
            }
            if (!center || !size || !rotation || !subdiv || !texturefile || !texture_repeat) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter pointer is null");
                return 0;
            }
            helios::vec3 center_vec(center[0], center[1], center[2]);
            helios::vec2 size_vec(size[0], size[1]);
            helios::SphericalCoord rotation_coord(rotation[0], rotation[1], rotation[2]);
            helios::int2 subdiv_int2(subdiv[0], subdiv[1]);
            helios::int2 texture_repeat_int2(texture_repeat[0], texture_repeat[1]);
            return context->addTileObject(center_vec, size_vec, rotation_coord, subdiv_int2, texturefile, texture_repeat_int2);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addTileObject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addTileObject): Unknown error adding tile object.");
        }
        return 0;
    }

    // addBoxObject - 5 overloads
    PYHELIOS_API unsigned int addBoxObject_basic(helios::Context* context, float* center, float* size, int* subdiv) {
        try {
            clearError();
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!center || !size || !subdiv) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter pointer is null"); return 0; }
            return context->addBoxObject(helios::vec3(center[0], center[1], center[2]), helios::vec3(size[0], size[1], size[2]), helios::int3(subdiv[0], subdiv[1], subdiv[2]));
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addBoxObject): ") + e.what());
        } catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addBoxObject): Unknown error."); }
        return 0;
    }

    PYHELIOS_API unsigned int addBoxObject_color(helios::Context* context, float* center, float* size, int* subdiv, float* color) {
        try {
            clearError();
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!center || !size || !subdiv || !color) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter pointer is null"); return 0; }
            return context->addBoxObject(helios::vec3(center[0], center[1], center[2]), helios::vec3(size[0], size[1], size[2]), helios::int3(subdiv[0], subdiv[1], subdiv[2]), helios::RGBcolor(color[0], color[1], color[2]));
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addBoxObject): ") + e.what());
        } catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addBoxObject): Unknown error."); }
        return 0;
    }

    PYHELIOS_API unsigned int addBoxObject_texture(helios::Context* context, float* center, float* size, int* subdiv, const char* texturefile) {
        try {
            clearError();
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!center || !size || !subdiv || !texturefile) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter pointer is null"); return 0; }
            return context->addBoxObject(helios::vec3(center[0], center[1], center[2]), helios::vec3(size[0], size[1], size[2]), helios::int3(subdiv[0], subdiv[1], subdiv[2]), texturefile);
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addBoxObject): ") + e.what());
        } catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addBoxObject): Unknown error."); }
        return 0;
    }

    PYHELIOS_API unsigned int addBoxObject_color_reverse(helios::Context* context, float* center, float* size, int* subdiv, float* color, bool reverse_normals) {
        try {
            clearError();
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!center || !size || !subdiv || !color) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter pointer is null"); return 0; }
            return context->addBoxObject(helios::vec3(center[0], center[1], center[2]), helios::vec3(size[0], size[1], size[2]), helios::int3(subdiv[0], subdiv[1], subdiv[2]), helios::RGBcolor(color[0], color[1], color[2]), reverse_normals);
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addBoxObject): ") + e.what());
        } catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addBoxObject): Unknown error."); }
        return 0;
    }

    PYHELIOS_API unsigned int addBoxObject_texture_reverse(helios::Context* context, float* center, float* size, int* subdiv, const char* texturefile, bool reverse_normals) {
        try {
            clearError();
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!center || !size || !subdiv || !texturefile) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter pointer is null"); return 0; }
            return context->addBoxObject(helios::vec3(center[0], center[1], center[2]), helios::vec3(size[0], size[1], size[2]), helios::int3(subdiv[0], subdiv[1], subdiv[2]), texturefile, reverse_normals);
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addBoxObject): ") + e.what());
        } catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addBoxObject): Unknown error."); }
        return 0;
    }

    // addConeObject - 3 overloads
    PYHELIOS_API unsigned int addConeObject_basic(helios::Context* context, unsigned int ndivs, float* node0, float* node1, float radius0, float radius1) {
        try {
            clearError();
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!node0 || !node1) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Node pointer is null"); return 0; }
            return context->addConeObject(ndivs, helios::vec3(node0[0], node0[1], node0[2]), helios::vec3(node1[0], node1[1], node1[2]), radius0, radius1);
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addConeObject): ") + e.what());
        } catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addConeObject): Unknown error."); }
        return 0;
    }

    PYHELIOS_API unsigned int addConeObject_color(helios::Context* context, unsigned int ndivs, float* node0, float* node1, float radius0, float radius1, float* color) {
        try {
            clearError();
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!node0 || !node1 || !color) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter pointer is null"); return 0; }
            return context->addConeObject(ndivs, helios::vec3(node0[0], node0[1], node0[2]), helios::vec3(node1[0], node1[1], node1[2]), radius0, radius1, helios::RGBcolor(color[0], color[1], color[2]));
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addConeObject): ") + e.what());
        } catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addConeObject): Unknown error."); }
        return 0;
    }

    PYHELIOS_API unsigned int addConeObject_texture(helios::Context* context, unsigned int ndivs, float* node0, float* node1, float radius0, float radius1, const char* texturefile) {
        try {
            clearError();
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!node0 || !node1 || !texturefile) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter pointer is null"); return 0; }
            return context->addConeObject(ndivs, helios::vec3(node0[0], node0[1], node0[2]), helios::vec3(node1[0], node1[1], node1[2]), radius0, radius1, texturefile);
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addConeObject): ") + e.what());
        } catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addConeObject): Unknown error."); }
        return 0;
    }

    // addDiskObject - 8 overloads
    PYHELIOS_API unsigned int addDiskObject_basic(helios::Context* context, unsigned int ndivs, float* center, float* size) {
        try {
            clearError();
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!center || !size) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter pointer is null"); return 0; }
            return context->addDiskObject(ndivs, helios::vec3(center[0], center[1], center[2]), helios::vec2(size[0], size[1]));
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addDiskObject): ") + e.what());
        } catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addDiskObject): Unknown error."); }
        return 0;
    }

    PYHELIOS_API unsigned int addDiskObject_rotation(helios::Context* context, unsigned int ndivs, float* center, float* size, float* rotation) {
        try {
            clearError();
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!center || !size || !rotation) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter pointer is null"); return 0; }
            return context->addDiskObject(ndivs, helios::vec3(center[0], center[1], center[2]), helios::vec2(size[0], size[1]), helios::SphericalCoord(rotation[0], rotation[1], rotation[2]));
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addDiskObject): ") + e.what());
        } catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addDiskObject): Unknown error."); }
        return 0;
    }

    PYHELIOS_API unsigned int addDiskObject_color(helios::Context* context, unsigned int ndivs, float* center, float* size, float* rotation, float* color) {
        try {
            clearError();
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!center || !size || !rotation || !color) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter pointer is null"); return 0; }
            return context->addDiskObject(ndivs, helios::vec3(center[0], center[1], center[2]), helios::vec2(size[0], size[1]), helios::SphericalCoord(rotation[0], rotation[1], rotation[2]), helios::RGBcolor(color[0], color[1], color[2]));
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addDiskObject): ") + e.what());
        } catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addDiskObject): Unknown error."); }
        return 0;
    }

    PYHELIOS_API unsigned int addDiskObject_rgba(helios::Context* context, unsigned int ndivs, float* center, float* size, float* rotation, float* color) {
        try {
            clearError();
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!center || !size || !rotation || !color) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter pointer is null"); return 0; }
            return context->addDiskObject(ndivs, helios::vec3(center[0], center[1], center[2]), helios::vec2(size[0], size[1]), helios::SphericalCoord(rotation[0], rotation[1], rotation[2]), helios::RGBAcolor(color[0], color[1], color[2], color[3]));
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addDiskObject): ") + e.what());
        } catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addDiskObject): Unknown error."); }
        return 0;
    }

    PYHELIOS_API unsigned int addDiskObject_texture(helios::Context* context, unsigned int ndivs, float* center, float* size, float* rotation, const char* texturefile) {
        try {
            clearError();
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!center || !size || !rotation || !texturefile) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter pointer is null"); return 0; }
            return context->addDiskObject(ndivs, helios::vec3(center[0], center[1], center[2]), helios::vec2(size[0], size[1]), helios::SphericalCoord(rotation[0], rotation[1], rotation[2]), texturefile);
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addDiskObject): ") + e.what());
        } catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addDiskObject): Unknown error."); }
        return 0;
    }

    PYHELIOS_API unsigned int addDiskObject_polar_color(helios::Context* context, int* ndivs, float* center, float* size, float* rotation, float* color) {
        try {
            clearError();
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!ndivs || !center || !size || !rotation || !color) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter pointer is null"); return 0; }
            return context->addDiskObject(helios::int2(ndivs[0], ndivs[1]), helios::vec3(center[0], center[1], center[2]), helios::vec2(size[0], size[1]), helios::SphericalCoord(rotation[0], rotation[1], rotation[2]), helios::RGBcolor(color[0], color[1], color[2]));
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addDiskObject): ") + e.what());
        } catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addDiskObject): Unknown error."); }
        return 0;
    }

    PYHELIOS_API unsigned int addDiskObject_polar_rgba(helios::Context* context, int* ndivs, float* center, float* size, float* rotation, float* color) {
        try {
            clearError();
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!ndivs || !center || !size || !rotation || !color) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter pointer is null"); return 0; }
            return context->addDiskObject(helios::int2(ndivs[0], ndivs[1]), helios::vec3(center[0], center[1], center[2]), helios::vec2(size[0], size[1]), helios::SphericalCoord(rotation[0], rotation[1], rotation[2]), helios::RGBAcolor(color[0], color[1], color[2], color[3]));
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addDiskObject): ") + e.what());
        } catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addDiskObject): Unknown error."); }
        return 0;
    }

    PYHELIOS_API unsigned int addDiskObject_polar_texture(helios::Context* context, int* ndivs, float* center, float* size, float* rotation, const char* texturefile) {
        try {
            clearError();
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!ndivs || !center || !size || !rotation || !texturefile) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter pointer is null"); return 0; }
            return context->addDiskObject(helios::int2(ndivs[0], ndivs[1]), helios::vec3(center[0], center[1], center[2]), helios::vec2(size[0], size[1]), helios::SphericalCoord(rotation[0], rotation[1], rotation[2]), texturefile);
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addDiskObject): ") + e.what());
        } catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addDiskObject): Unknown error."); }
        return 0;
    }

    // addTubeObject - 4 overloads (requires vector construction)
    PYHELIOS_API unsigned int addTubeObject_basic(helios::Context* context, unsigned int radial_subdivisions, float* nodes, unsigned int node_count, float* radii, unsigned int radius_count) {
        try {
            clearError();
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!nodes || !radii) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter pointer is null"); return 0; }
            if (node_count == 0 || radius_count == 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Arrays cannot be empty"); return 0; }
            std::vector<helios::vec3> nodes_vec;
            nodes_vec.reserve(node_count);
            for (unsigned int i = 0; i < node_count; i++) {
                nodes_vec.emplace_back(nodes[i*3], nodes[i*3+1], nodes[i*3+2]);
            }
            std::vector<float> radii_vec(radii, radii + radius_count);
            return context->addTubeObject(radial_subdivisions, nodes_vec, radii_vec);
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addTubeObject): ") + e.what());
        } catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addTubeObject): Unknown error."); }
        return 0;
    }

    PYHELIOS_API unsigned int addTubeObject_color(helios::Context* context, unsigned int radial_subdivisions, float* nodes, unsigned int node_count, float* radii, unsigned int radius_count, float* colors, unsigned int color_count) {
        try {
            clearError();
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!nodes || !radii || !colors) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter pointer is null"); return 0; }
            std::vector<helios::vec3> nodes_vec;
            nodes_vec.reserve(node_count);
            for (unsigned int i = 0; i < node_count; i++) {
                nodes_vec.emplace_back(nodes[i*3], nodes[i*3+1], nodes[i*3+2]);
            }
            std::vector<float> radii_vec(radii, radii + radius_count);
            std::vector<helios::RGBcolor> colors_vec;
            colors_vec.reserve(color_count);
            for (unsigned int i = 0; i < color_count; i++) {
                colors_vec.emplace_back(colors[i*3], colors[i*3+1], colors[i*3+2]);
            }
            return context->addTubeObject(radial_subdivisions, nodes_vec, radii_vec, colors_vec);
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addTubeObject): ") + e.what());
        } catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addTubeObject): Unknown error."); }
        return 0;
    }

    PYHELIOS_API unsigned int addTubeObject_texture(helios::Context* context, unsigned int radial_subdivisions, float* nodes, unsigned int node_count, float* radii, unsigned int radius_count, const char* texturefile) {
        try {
            clearError();
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!nodes || !radii || !texturefile) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter pointer is null"); return 0; }
            std::vector<helios::vec3> nodes_vec;
            nodes_vec.reserve(node_count);
            for (unsigned int i = 0; i < node_count; i++) {
                nodes_vec.emplace_back(nodes[i*3], nodes[i*3+1], nodes[i*3+2]);
            }
            std::vector<float> radii_vec(radii, radii + radius_count);
            return context->addTubeObject(radial_subdivisions, nodes_vec, radii_vec, texturefile);
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addTubeObject): ") + e.what());
        } catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addTubeObject): Unknown error."); }
        return 0;
    }

    PYHELIOS_API unsigned int addTubeObject_texture_uv(helios::Context* context, unsigned int radial_subdivisions, float* nodes, unsigned int node_count, float* radii, unsigned int radius_count, const char* texturefile, float* textureuv_ufrac, unsigned int uv_count) {
        try {
            clearError();
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!nodes || !radii || !texturefile || !textureuv_ufrac) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter pointer is null"); return 0; }
            std::vector<helios::vec3> nodes_vec;
            nodes_vec.reserve(node_count);
            for (unsigned int i = 0; i < node_count; i++) {
                nodes_vec.emplace_back(nodes[i*3], nodes[i*3+1], nodes[i*3+2]);
            }
            std::vector<float> radii_vec(radii, radii + radius_count);
            std::vector<float> uv_vec(textureuv_ufrac, textureuv_ufrac + uv_count);
            return context->addTubeObject(radial_subdivisions, nodes_vec, radii_vec, texturefile, uv_vec);
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addTubeObject): ") + e.what());
        } catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addTubeObject): Unknown error."); }
        return 0;
    }

    // Primitive query functions
    PYHELIOS_API unsigned int getPrimitiveType(helios::Context* context, unsigned int uuid) {
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
    
    PYHELIOS_API float getPrimitiveArea(helios::Context* context, unsigned int uuid) {
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
    
    PYHELIOS_API float* getPrimitiveNormal(helios::Context* context, unsigned int uuid) {
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
    
    PYHELIOS_API unsigned int getPrimitiveCount(helios::Context* context) {
        return context->getPrimitiveCount();
    }

    PYHELIOS_API bool doesPrimitiveExist(helios::Context* context, unsigned int uuid) {
        return context->doesPrimitiveExist(uuid);
    }

    PYHELIOS_API bool doesPrimitiveExistBatch(helios::Context* context, unsigned int* uuids, unsigned int count) {
        std::vector<uint> uuid_vec(uuids, uuids + count);
        return context->doesPrimitiveExist(uuid_vec);
    }

    PYHELIOS_API float* getPrimitiveVertices(helios::Context* context, unsigned int uuid, unsigned int* size) {
        try {
            clearError(); // Clear any previous error
            std::vector<helios::vec3> vertices = context->getPrimitiveVertices(uuid);

            // Allocate static buffer for vertex data (3 floats per vertex)
            static thread_local std::vector<float> vertex_buffer;
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
    
    PYHELIOS_API float* getPrimitiveColor(helios::Context* context, unsigned int uuid) {
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
    
    PYHELIOS_API float* getPrimitiveColorRGB(helios::Context* context, unsigned int uuid) {
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
    
    PYHELIOS_API float* getPrimitiveColorRGBA(helios::Context* context, unsigned int uuid) {
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
    
    PYHELIOS_API unsigned int* getAllUUIDs(helios::Context* context, unsigned int* size) {
        try {
            clearError(); // Clear any previous error
            std::vector<unsigned int> uuids = context->getAllUUIDs();
            *size = uuids.size();

            // Allocate static buffer for UUID data
            static thread_local std::vector<unsigned int> uuid_buffer;
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
    PYHELIOS_API unsigned int getObjectCount(helios::Context* context) {
        return context->getObjectCount();
    }
    
    PYHELIOS_API unsigned int* getAllObjectIDs(helios::Context* context, unsigned int* size) {
        try {
            clearError(); // Clear any previous error
            std::vector<unsigned int> object_ids = context->getAllObjectIDs();
            *size = object_ids.size();

            static thread_local std::vector<unsigned int> object_buffer;
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
    
    PYHELIOS_API unsigned int* getObjectPrimitiveUUIDs(helios::Context* context, unsigned int object_id, unsigned int* size) {
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

    PYHELIOS_API unsigned int* loadPLY(helios::Context* context, const char* filename, float* origin, float height, const char* upaxis, unsigned int* size) {
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

    // Missing loadPLY overloads
    PYHELIOS_API unsigned int* loadPLYBasic(helios::Context* context, const char* filename, bool silent, unsigned int* size) {
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
            if (!size) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Size pointer is null");
                return nullptr;
            }
            
            std::vector<unsigned int> uuids = context->loadPLY(filename, silent);
            
            static thread_local std::vector<unsigned int> uuid_buffer;
            uuid_buffer = std::move(uuids);
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

    PYHELIOS_API unsigned int* loadPLYWithOriginHeightRotation(helios::Context* context, const char* filename, float* origin, float height, float* rotation, const char* upaxis, bool silent, unsigned int* size) {
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
            if (!rotation) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Rotation is null");
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
            helios::SphericalCoord rotation_coord(rotation[0], rotation[1], rotation[2]);
            std::string upaxis_str(upaxis);
            
            std::vector<unsigned int> uuids = context->loadPLY(filename, origin_vec, height, rotation_coord, upaxis_str, silent);
            
            static thread_local std::vector<unsigned int> uuid_buffer;
            uuid_buffer = std::move(uuids);
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

    PYHELIOS_API unsigned int* loadPLYWithOriginHeightColor(helios::Context* context, const char* filename, float* origin, float height, float* color, const char* upaxis, bool silent, unsigned int* size) {
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
            if (!color) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Color is null");
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
            helios::RGBcolor color_rgb(color[0], color[1], color[2]);
            std::string upaxis_str(upaxis);
            
            std::vector<unsigned int> uuids = context->loadPLY(filename, origin_vec, height, color_rgb, upaxis_str, silent);
            
            static thread_local std::vector<unsigned int> uuid_buffer;
            uuid_buffer = std::move(uuids);
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

    PYHELIOS_API unsigned int* loadPLYWithOriginHeightRotationColor(helios::Context* context, const char* filename, float* origin, float height, float* rotation, float* color, const char* upaxis, bool silent, unsigned int* size) {
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
            if (!rotation) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Rotation is null");
                if (size) *size = 0;
                return nullptr;
            }
            if (!color) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Color is null");
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
            helios::SphericalCoord rotation_coord(rotation[0], rotation[1], rotation[2]);
            helios::RGBcolor color_rgb(color[0], color[1], color[2]);
            std::string upaxis_str(upaxis);
            
            std::vector<unsigned int> uuids = context->loadPLY(filename, origin_vec, height, rotation_coord, color_rgb, upaxis_str, silent);
            
            static thread_local std::vector<unsigned int> uuid_buffer;
            uuid_buffer = std::move(uuids);
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

    // loadOBJ functions
    PYHELIOS_API unsigned int* loadOBJ(helios::Context* context, const char* filename, bool silent, unsigned int* size) {
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
            if (!size) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Size pointer is null");
                return nullptr;
            }
            
            std::vector<unsigned int> uuids = context->loadOBJ(filename, silent);
            
            static thread_local std::vector<unsigned int> uuid_buffer;
            uuid_buffer = std::move(uuids);
            *size = uuid_buffer.size();
            return uuid_buffer.data();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_FILE_IO, std::string("ERROR (Context::loadOBJ): ") + e.what());
            if (size) *size = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::loadOBJ): Unknown error loading OBJ file.");
            if (size) *size = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* loadOBJWithOriginHeightRotationColor(helios::Context* context, const char* filename, float* origin, float height, float* rotation, float* color, bool silent, unsigned int* size) {
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
            if (!rotation) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Rotation is null");
                if (size) *size = 0;
                return nullptr;
            }
            if (!color) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Color is null");
                if (size) *size = 0;
                return nullptr;
            }
            if (!size) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Size pointer is null");
                return nullptr;
            }
            
            helios::vec3 origin_vec(origin[0], origin[1], origin[2]);
            helios::SphericalCoord rotation_coord(rotation[0], rotation[1], rotation[2]);
            helios::RGBcolor color_rgb(color[0], color[1], color[2]);
            
            std::vector<unsigned int> uuids = context->loadOBJ(filename, origin_vec, height, rotation_coord, color_rgb, silent);
            
            static thread_local std::vector<unsigned int> uuid_buffer;
            uuid_buffer = std::move(uuids);
            *size = uuid_buffer.size();
            return uuid_buffer.data();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_FILE_IO, std::string("ERROR (Context::loadOBJ): ") + e.what());
            if (size) *size = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::loadOBJ): Unknown error loading OBJ file.");
            if (size) *size = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* loadOBJWithOriginHeightRotationColorUpaxis(helios::Context* context, const char* filename, float* origin, float height, float* rotation, float* color, const char* upaxis, bool silent, unsigned int* size) {
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
            if (!rotation) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Rotation is null");
                if (size) *size = 0;
                return nullptr;
            }
            if (!color) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Color is null");
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
            helios::SphericalCoord rotation_coord(rotation[0], rotation[1], rotation[2]);
            helios::RGBcolor color_rgb(color[0], color[1], color[2]);
            
            std::vector<unsigned int> uuids = context->loadOBJ(filename, origin_vec, height, rotation_coord, color_rgb, upaxis, silent);
            
            static thread_local std::vector<unsigned int> uuid_buffer;
            uuid_buffer = std::move(uuids);
            *size = uuid_buffer.size();
            return uuid_buffer.data();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_FILE_IO, std::string("ERROR (Context::loadOBJ): ") + e.what());
            if (size) *size = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::loadOBJ): Unknown error loading OBJ file.");
            if (size) *size = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* loadOBJWithOriginScaleRotationColorUpaxis(helios::Context* context, const char* filename, float* origin, float* scale, float* rotation, float* color, const char* upaxis, bool silent, unsigned int* size) {
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
            if (!scale) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Scale is null");
                if (size) *size = 0;
                return nullptr;
            }
            if (!rotation) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Rotation is null");
                if (size) *size = 0;
                return nullptr;
            }
            if (!color) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Color is null");
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
            helios::vec3 scale_vec(scale[0], scale[1], scale[2]);
            helios::SphericalCoord rotation_coord(rotation[0], rotation[1], rotation[2]);
            helios::RGBcolor color_rgb(color[0], color[1], color[2]);
            
            std::vector<unsigned int> uuids = context->loadOBJ(filename, origin_vec, scale_vec, rotation_coord, color_rgb, upaxis, silent);
            
            static thread_local std::vector<unsigned int> uuid_buffer;
            uuid_buffer = std::move(uuids);
            *size = uuid_buffer.size();
            return uuid_buffer.data();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_FILE_IO, std::string("ERROR (Context::loadOBJ): ") + e.what());
            if (size) *size = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::loadOBJ): Unknown error loading OBJ file.");
            if (size) *size = 0;
            return nullptr;
        }
    }

    // loadXML function
    PYHELIOS_API unsigned int* loadXML(helios::Context* context, const char* filename, bool quiet, unsigned int* size) {
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
            if (!size) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Size pointer is null");
                return nullptr;
            }
            
            std::vector<unsigned int> uuids = context->loadXML(filename, quiet);
            
            static thread_local std::vector<unsigned int> uuid_buffer;
            uuid_buffer = std::move(uuids);
            *size = uuid_buffer.size();
            return uuid_buffer.data();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_FILE_IO, std::string("ERROR (Context::loadXML): ") + e.what());
            if (size) *size = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::loadXML): Unknown error loading XML file.");
            if (size) *size = 0;
            return nullptr;
        }
    }

        //=============================================================================
    // Primitive Data Functions
    //=============================================================================

    PYHELIOS_API void setPrimitiveDataFloat(helios::Context* context, unsigned int uuid, const char* label, float value) {
        // Clear error state before any operation to prevent contamination from previous calls
        clearError();
        try {
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

    PYHELIOS_API void setPrimitiveDataInt(helios::Context* context, unsigned int uuid, const char* label, int value) {
        clearError();
        try {
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

    PYHELIOS_API void setPrimitiveDataString(helios::Context* context, unsigned int uuid, const char* label, const char* value) {
        // Clear error state before any operation to prevent contamination from previous calls
        clearError();
        try {
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

    PYHELIOS_API float getPrimitiveDataFloat(helios::Context* context, unsigned int uuid, const char* label) {
        // Clear error state before any operation to prevent contamination from previous calls
        clearError();
        try {
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

    PYHELIOS_API int getPrimitiveDataInt(helios::Context* context, unsigned int uuid, const char* label) {
        // Clear error state before any operation to prevent contamination from previous calls
        clearError();
        try {
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

    PYHELIOS_API int getPrimitiveDataString(helios::Context* context, unsigned int uuid, const char* label, char* buffer, int buffer_size) {
        // Clear error state before any operation to prevent contamination from previous calls
        clearError();
        try {
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

    PYHELIOS_API bool doesPrimitiveDataExist(helios::Context* context, unsigned int uuid, const char* label) {
        clearError();
        try {
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

    PYHELIOS_API void setPrimitiveDataVec3(helios::Context* context, unsigned int uuid, const char* label, float x, float y, float z) {
        // Clear error state before any operation to prevent contamination from previous calls
        clearError();
        try {
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

    PYHELIOS_API void getPrimitiveDataVec3(helios::Context* context, unsigned int uuid, const char* label, float* x, float* y, float* z) {
        // Clear error state before any operation to prevent contamination from previous calls
        clearError();
        try {
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

    PYHELIOS_API int getPrimitiveDataType(helios::Context* context, unsigned int uuid, const char* label) {
        // Clear error state before any operation to prevent contamination from previous calls
        clearError();
        try {
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

    PYHELIOS_API int getPrimitiveDataSize(helios::Context* context, unsigned int uuid, const char* label) {
        // Clear error state before any operation to prevent contamination from previous calls
        clearError();
        try {
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

    PYHELIOS_API void setPrimitiveDataUInt(helios::Context* context, unsigned int uuid, const char* label, unsigned int value) {
        // Clear error state before any operation to prevent contamination from previous calls
        clearError();
        try {
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

    PYHELIOS_API void setPrimitiveDataDouble(helios::Context* context, unsigned int uuid, const char* label, double value) {
        // Clear error state before any operation to prevent contamination from previous calls
        clearError();
        try {
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

    PYHELIOS_API int getPrimitiveDataGeneric(helios::Context* context, unsigned int uuid, const char* label, void* result_buffer, int max_buffer_size) {
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
    PYHELIOS_API void setPrimitiveDataVec2(helios::Context* context, unsigned int uuid, const char* label, float x, float y) {
        // Clear error state before any operation to prevent contamination from previous calls
        clearError();
        try {
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

    PYHELIOS_API void setPrimitiveDataVec4(helios::Context* context, unsigned int uuid, const char* label, float x, float y, float z, float w) {
        // Clear error state before any operation to prevent contamination from previous calls
        clearError();
        try {
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

    PYHELIOS_API void getPrimitiveDataVec2(helios::Context* context, unsigned int uuid, const char* label, float* x, float* y) {
        // Clear error state before any operation to prevent contamination from previous calls
        clearError();
        try {
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

    PYHELIOS_API void getPrimitiveDataVec4(helios::Context* context, unsigned int uuid, const char* label, float* x, float* y, float* z, float* w) {
        // Clear error state before any operation to prevent contamination from previous calls
        clearError();
        try {
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
    PYHELIOS_API void setPrimitiveDataInt2(helios::Context* context, unsigned int uuid, const char* label, int x, int y) {
        // Clear error state before any operation to prevent contamination from previous calls
        clearError();
        try {
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

    PYHELIOS_API void setPrimitiveDataInt3(helios::Context* context, unsigned int uuid, const char* label, int x, int y, int z) {
        // Clear error state before any operation to prevent contamination from previous calls
        clearError();
        try {
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

    PYHELIOS_API void setPrimitiveDataInt4(helios::Context* context, unsigned int uuid, const char* label, int x, int y, int z, int w) {
        // Clear error state before any operation to prevent contamination from previous calls
        clearError();
        try {
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

    PYHELIOS_API void getPrimitiveDataInt2(helios::Context* context, unsigned int uuid, const char* label, int* x, int* y) {
        // Clear error state before any operation to prevent contamination from previous calls
        clearError();
        try {
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

    PYHELIOS_API void getPrimitiveDataInt3(helios::Context* context, unsigned int uuid, const char* label, int* x, int* y, int* z) {
        // Clear error state before any operation to prevent contamination from previous calls
        clearError();
        try {
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

    PYHELIOS_API void getPrimitiveDataInt4(helios::Context* context, unsigned int uuid, const char* label, int* x, int* y, int* z, int* w) {
        // Clear error state before any operation to prevent contamination from previous calls
        clearError();
        try {
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
    PYHELIOS_API unsigned int getPrimitiveDataUInt(helios::Context* context, unsigned int uuid, const char* label) {
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

    PYHELIOS_API double getPrimitiveDataDouble(helios::Context* context, unsigned int uuid, const char* label) {
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
    PYHELIOS_API int getPrimitiveDataAuto(helios::Context* context, unsigned int uuid, const char* label) {
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

    PYHELIOS_API void colorPrimitiveByDataPseudocolor(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* primitive_data, const char* colormap, unsigned int ncolors) {
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

    PYHELIOS_API void colorPrimitiveByDataPseudocolorWithRange(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* primitive_data, const char* colormap, unsigned int ncolors, float data_min, float data_max) {
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

    //=============================================================================
    // Batch Primitive Data Functions - Broadcast Pattern (same value to all UUIDs)
    //=============================================================================

    PYHELIOS_API void setBroadcastPrimitiveDataInt(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* label, int value) {
        clearError();
        try {
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataInt): Context pointer is null.");
                return;
            }
            if (!uuids || num_uuids == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataInt): UUIDs array is null or empty.");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataInt): Label is null.");
                return;
            }
            std::vector<uint> uuid_vec(uuids, uuids + num_uuids);
            context->setPrimitiveData(uuid_vec, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setBroadcastPrimitiveDataInt): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setBroadcastPrimitiveDataInt): Unknown error.");
        }
    }

    PYHELIOS_API void setBroadcastPrimitiveDataUInt(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* label, unsigned int value) {
        clearError();
        try {
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataUInt): Context pointer is null.");
                return;
            }
            if (!uuids || num_uuids == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataUInt): UUIDs array is null or empty.");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataUInt): Label is null.");
                return;
            }
            std::vector<uint> uuid_vec(uuids, uuids + num_uuids);
            context->setPrimitiveData(uuid_vec, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setBroadcastPrimitiveDataUInt): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setBroadcastPrimitiveDataUInt): Unknown error.");
        }
    }

    PYHELIOS_API void setBroadcastPrimitiveDataFloat(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* label, float value) {
        clearError();
        try {
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataFloat): Context pointer is null.");
                return;
            }
            if (!uuids || num_uuids == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataFloat): UUIDs array is null or empty.");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataFloat): Label is null.");
                return;
            }
            std::vector<uint> uuid_vec(uuids, uuids + num_uuids);
            context->setPrimitiveData(uuid_vec, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setBroadcastPrimitiveDataFloat): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setBroadcastPrimitiveDataFloat): Unknown error.");
        }
    }

    PYHELIOS_API void setBroadcastPrimitiveDataDouble(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* label, double value) {
        clearError();
        try {
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataDouble): Context pointer is null.");
                return;
            }
            if (!uuids || num_uuids == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataDouble): UUIDs array is null or empty.");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataDouble): Label is null.");
                return;
            }
            std::vector<uint> uuid_vec(uuids, uuids + num_uuids);
            context->setPrimitiveData(uuid_vec, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setBroadcastPrimitiveDataDouble): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setBroadcastPrimitiveDataDouble): Unknown error.");
        }
    }

    PYHELIOS_API void setBroadcastPrimitiveDataString(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* label, const char* value) {
        clearError();
        try {
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataString): Context pointer is null.");
                return;
            }
            if (!uuids || num_uuids == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataString): UUIDs array is null or empty.");
                return;
            }
            if (!label || !value) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataString): Label or value is null.");
                return;
            }
            std::vector<uint> uuid_vec(uuids, uuids + num_uuids);
            std::string str_value(value);
            context->setPrimitiveData(uuid_vec, label, str_value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setBroadcastPrimitiveDataString): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setBroadcastPrimitiveDataString): Unknown error.");
        }
    }

    PYHELIOS_API void setBroadcastPrimitiveDataVec2(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* label, float x, float y) {
        clearError();
        try {
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataVec2): Context pointer is null.");
                return;
            }
            if (!uuids || num_uuids == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataVec2): UUIDs array is null or empty.");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataVec2): Label is null.");
                return;
            }
            std::vector<uint> uuid_vec(uuids, uuids + num_uuids);
            helios::vec2 value(x, y);
            context->setPrimitiveData(uuid_vec, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setBroadcastPrimitiveDataVec2): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setBroadcastPrimitiveDataVec2): Unknown error.");
        }
    }

    PYHELIOS_API void setBroadcastPrimitiveDataVec3(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* label, float x, float y, float z) {
        clearError();
        try {
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataVec3): Context pointer is null.");
                return;
            }
            if (!uuids || num_uuids == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataVec3): UUIDs array is null or empty.");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataVec3): Label is null.");
                return;
            }
            std::vector<uint> uuid_vec(uuids, uuids + num_uuids);
            helios::vec3 value(x, y, z);
            context->setPrimitiveData(uuid_vec, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setBroadcastPrimitiveDataVec3): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setBroadcastPrimitiveDataVec3): Unknown error.");
        }
    }

    PYHELIOS_API void setBroadcastPrimitiveDataVec4(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* label, float x, float y, float z, float w) {
        clearError();
        try {
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataVec4): Context pointer is null.");
                return;
            }
            if (!uuids || num_uuids == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataVec4): UUIDs array is null or empty.");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataVec4): Label is null.");
                return;
            }
            std::vector<uint> uuid_vec(uuids, uuids + num_uuids);
            helios::vec4 value(x, y, z, w);
            context->setPrimitiveData(uuid_vec, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setBroadcastPrimitiveDataVec4): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setBroadcastPrimitiveDataVec4): Unknown error.");
        }
    }

    PYHELIOS_API void setBroadcastPrimitiveDataInt2(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* label, int x, int y) {
        clearError();
        try {
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataInt2): Context pointer is null.");
                return;
            }
            if (!uuids || num_uuids == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataInt2): UUIDs array is null or empty.");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataInt2): Label is null.");
                return;
            }
            std::vector<uint> uuid_vec(uuids, uuids + num_uuids);
            helios::int2 value(x, y);
            context->setPrimitiveData(uuid_vec, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setBroadcastPrimitiveDataInt2): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setBroadcastPrimitiveDataInt2): Unknown error.");
        }
    }

    PYHELIOS_API void setBroadcastPrimitiveDataInt3(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* label, int x, int y, int z) {
        clearError();
        try {
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataInt3): Context pointer is null.");
                return;
            }
            if (!uuids || num_uuids == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataInt3): UUIDs array is null or empty.");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataInt3): Label is null.");
                return;
            }
            std::vector<uint> uuid_vec(uuids, uuids + num_uuids);
            helios::int3 value(x, y, z);
            context->setPrimitiveData(uuid_vec, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setBroadcastPrimitiveDataInt3): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setBroadcastPrimitiveDataInt3): Unknown error.");
        }
    }

    PYHELIOS_API void setBroadcastPrimitiveDataInt4(helios::Context* context, unsigned int* uuids, size_t num_uuids, const char* label, int x, int y, int z, int w) {
        clearError();
        try {
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataInt4): Context pointer is null.");
                return;
            }
            if (!uuids || num_uuids == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataInt4): UUIDs array is null or empty.");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (setBroadcastPrimitiveDataInt4): Label is null.");
                return;
            }
            std::vector<uint> uuid_vec(uuids, uuids + num_uuids);
            helios::int4 value(x, y, z, w);
            context->setPrimitiveData(uuid_vec, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setBroadcastPrimitiveDataInt4): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setBroadcastPrimitiveDataInt4): Unknown error.");
        }
    }

    // Context time/date management functions for solar position integration
    PYHELIOS_API void setTime_HourMinute(helios::Context* context, int hour, int minute) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (hour < 0 || hour > 23) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Hour must be between 0 and 23");
                return;
            }
            if (minute < 0 || minute > 59) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Minute must be between 0 and 59");
                return;
            }
            
            context->setTime(minute, hour);
            
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setTime_HourMinute): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setTime_HourMinute): Unknown error");
        }
    }
    
    PYHELIOS_API void setTime_HourMinuteSecond(helios::Context* context, int hour, int minute, int second) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (hour < 0 || hour > 23) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Hour must be between 0 and 23");
                return;
            }
            if (minute < 0 || minute > 59) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Minute must be between 0 and 59");
                return;
            }
            if (second < 0 || second > 59) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Second must be between 0 and 59");
                return;
            }
            
            context->setTime(second, minute, hour);
            
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setTime_HourMinuteSecond): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setTime_HourMinuteSecond): Unknown error");
        }
    }
    
    PYHELIOS_API void setDate_DayMonthYear(helios::Context* context, int day, int month, int year) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (day < 1 || day > 31) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Day must be between 1 and 31");
                return;
            }
            if (month < 1 || month > 12) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Month must be between 1 and 12");
                return;
            }
            if (year < 1900 || year > 3000) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Year must be between 1900 and 3000");
                return;
            }
            
            context->setDate(day, month, year);
            
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setDate_DayMonthYear): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setDate_DayMonthYear): Unknown error");
        }
    }
    
    PYHELIOS_API void setDate_JulianDay(helios::Context* context, int julian_day, int year) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (julian_day < 1 || julian_day > 366) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Julian day must be between 1 and 366");
                return;
            }
            if (year < 1900 || year > 3000) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Year must be between 1900 and 3000");
                return;
            }
            
            context->setDate(julian_day, year);
            
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setDate_JulianDay): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setDate_JulianDay): Unknown error");
        }
    }
    
    PYHELIOS_API void getTime(helios::Context* context, int* hour, int* minute, int* second) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!hour || !minute || !second) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output parameters cannot be null");
                return;
            }
            
            helios::Time time = context->getTime();
            *hour = time.hour;
            *minute = time.minute;
            *second = time.second;
            
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getTime): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getTime): Unknown error");
        }
    }
    
    PYHELIOS_API void getDate(helios::Context* context, int* day, int* month, int* year) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!day || !month || !year) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output parameters cannot be null");
                return;
            }
            
            helios::Date date = context->getDate();
            *day = date.day;
            *month = date.month;
            *year = date.year;
            
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getDate): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getDate): Unknown error");
        }
    }

    //=============================================================================
    // Timeseries Functions
    //=============================================================================

    PYHELIOS_API void addTimeseriesData(helios::Context* context, const char* label, float value,
                                        int day, int month, int year, int hour, int minute, int second) {
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

            helios::Date date(day, month, year);
            helios::Time time(hour, minute, second);
            context->addTimeseriesData(label, value, date, time);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (addTimeseriesData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (addTimeseriesData): Unknown error");
        }
    }

    PYHELIOS_API void updateTimeseriesData(helios::Context* context, const char* label,
                                           int day, int month, int year, int hour, int minute, int second,
                                           float new_value) {
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

            helios::Date date(day, month, year);
            helios::Time time(hour, minute, second);
            context->updateTimeseriesData(label, date, time, new_value);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (updateTimeseriesData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (updateTimeseriesData): Unknown error");
        }
    }

    PYHELIOS_API void setCurrentTimeseriesPoint(helios::Context* context, const char* label, unsigned int index) {
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

            context->setCurrentTimeseriesPoint(label, index);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setCurrentTimeseriesPoint): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setCurrentTimeseriesPoint): Unknown error");
        }
    }

    PYHELIOS_API float queryTimeseriesData_DateTime(helios::Context* context, const char* label,
                                                     int day, int month, int year, int hour, int minute, int second) {
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

            helios::Date date(day, month, year);
            helios::Time time(hour, minute, second);
            return context->queryTimeseriesData(label, date, time);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return 0.0f;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (queryTimeseriesData_DateTime): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (queryTimeseriesData_DateTime): Unknown error");
            return 0.0f;
        }
    }

    PYHELIOS_API float queryTimeseriesData_Current(helios::Context* context, const char* label) {
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

            return context->queryTimeseriesData(label);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return 0.0f;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (queryTimeseriesData_Current): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (queryTimeseriesData_Current): Unknown error");
            return 0.0f;
        }
    }

    PYHELIOS_API float queryTimeseriesData_Index(helios::Context* context, const char* label, unsigned int index) {
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

            return context->queryTimeseriesData(label, index);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return 0.0f;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (queryTimeseriesData_Index): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (queryTimeseriesData_Index): Unknown error");
            return 0.0f;
        }
    }

    PYHELIOS_API void queryTimeseriesTime(helios::Context* context, const char* label, unsigned int index,
                                           int* hour, int* minute, int* second) {
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
            if (!hour || !minute || !second) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output parameters cannot be null");
                return;
            }

            helios::Time time = context->queryTimeseriesTime(label, index);
            *hour = time.hour;
            *minute = time.minute;
            *second = time.second;

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (queryTimeseriesTime): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (queryTimeseriesTime): Unknown error");
        }
    }

    PYHELIOS_API void queryTimeseriesDate(helios::Context* context, const char* label, unsigned int index,
                                           int* day, int* month, int* year) {
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
            if (!day || !month || !year) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output parameters cannot be null");
                return;
            }

            helios::Date date = context->queryTimeseriesDate(label, index);
            *day = date.day;
            *month = date.month;
            *year = date.year;

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (queryTimeseriesDate): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (queryTimeseriesDate): Unknown error");
        }
    }

    PYHELIOS_API unsigned int getTimeseriesLength(helios::Context* context, const char* label) {
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

            return context->getTimeseriesLength(label);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getTimeseriesLength): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getTimeseriesLength): Unknown error");
            return 0;
        }
    }

    PYHELIOS_API bool doesTimeseriesVariableExist(helios::Context* context, const char* label) {
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

            return context->doesTimeseriesVariableExist(label);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return false;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (doesTimeseriesVariableExist): ") + e.what());
            return false;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (doesTimeseriesVariableExist): Unknown error");
            return false;
        }
    }

    PYHELIOS_API const char** listTimeseriesVariables(helios::Context* context, unsigned int* count) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count output parameter is null");
                return nullptr;
            }

            static thread_local std::vector<std::string> static_strings;
            static thread_local std::vector<const char*> static_ptrs;

            static_strings = context->listTimeseriesVariables();
            static_ptrs.clear();
            static_ptrs.reserve(static_strings.size());
            for (auto& s : static_strings) {
                static_ptrs.push_back(s.c_str());
            }
            *count = static_strings.size();
            return static_ptrs.empty() ? nullptr : static_ptrs.data();

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (listTimeseriesVariables): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (listTimeseriesVariables): Unknown error");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API void loadTabularTimeseriesData(helios::Context* context, const char* data_file,
                                                 const char** column_labels, unsigned int label_count,
                                                 const char* delimiter, const char* date_string_format,
                                                 unsigned int headerlines) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!data_file) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Data file path is null");
                return;
            }
            if (!column_labels && label_count > 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Column labels array is null but label_count > 0");
                return;
            }
            if (!delimiter) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Delimiter is null");
                return;
            }
            if (!date_string_format) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Date string format is null");
                return;
            }

            std::vector<std::string> labels_vec;
            labels_vec.reserve(label_count);
            for (unsigned int i = 0; i < label_count; i++) {
                if (!column_labels[i]) {
                    setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Column label at index " + std::to_string(i) + " is null");
                    return;
                }
                labels_vec.emplace_back(column_labels[i]);
            }

            context->loadTabularTimeseriesData(std::string(data_file), labels_vec, std::string(delimiter),
                                                std::string(date_string_format), headerlines);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (loadTabularTimeseriesData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (loadTabularTimeseriesData): Unknown error");
        }
    }

    PYHELIOS_API void clearTimeseriesData(helios::Context* context) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            context->clearTimeseriesData();
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (clearTimeseriesData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (clearTimeseriesData): Unknown error");
        }
    }

    PYHELIOS_API void deleteTimeseriesVariable(helios::Context* context, const char* label) {
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
            context->deleteTimeseriesVariable(label);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (deleteTimeseriesVariable): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (deleteTimeseriesVariable): Unknown error");
        }
    }

    //=============================================================================
    // File Export Functions
    //=============================================================================

    PYHELIOS_API void writePLY(helios::Context* context, const char* filename) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null");
                return;
            }

            context->writePLY(filename);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_FILE_IO, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_FILE_IO, std::string("ERROR (Context::writePLY): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::writePLY): Unknown error writing PLY file.");
        }
    }

    PYHELIOS_API void writePLYWithUUIDs(helios::Context* context, const char* filename, unsigned int* uuids, unsigned int count) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null");
                return;
            }
            if (!uuids && count > 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null but count > 0");
                return;
            }

            // Convert C array to vector
            std::vector<unsigned int> uuid_vector(uuids, uuids + count);

            context->writePLY(filename, uuid_vector);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_FILE_IO, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_FILE_IO, std::string("ERROR (Context::writePLY): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::writePLY): Unknown error writing PLY file.");
        }
    }

    PYHELIOS_API void writeOBJ(helios::Context* context, const char* filename, bool write_normals, bool silent) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null");
                return;
            }

            context->writeOBJ(filename, write_normals, silent);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_FILE_IO, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_FILE_IO, std::string("ERROR (Context::writeOBJ): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::writeOBJ): Unknown error writing OBJ file.");
        }
    }

    PYHELIOS_API void writeOBJWithUUIDs(helios::Context* context, const char* filename, unsigned int* uuids, unsigned int count, bool write_normals, bool silent) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null");
                return;
            }
            if (!uuids && count > 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null but count > 0");
                return;
            }

            // Convert C array to vector
            std::vector<unsigned int> uuid_vector(uuids, uuids + count);

            context->writeOBJ(filename, uuid_vector, write_normals, silent);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_FILE_IO, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_FILE_IO, std::string("ERROR (Context::writeOBJ): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::writeOBJ): Unknown error writing OBJ file.");
        }
    }

    PYHELIOS_API void writeOBJWithPrimitiveData(helios::Context* context, const char* filename, unsigned int* uuids, unsigned int count, const char** data_fields, unsigned int field_count, bool write_normals, bool silent) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null");
                return;
            }
            if (!uuids && count > 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null but count > 0");
                return;
            }
            if (!data_fields && field_count > 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Data fields array is null but field_count > 0");
                return;
            }

            // Convert C arrays to vectors
            std::vector<unsigned int> uuid_vector(uuids, uuids + count);
            std::vector<std::string> field_vector;

            for (unsigned int i = 0; i < field_count; i++) {
                if (data_fields[i]) {
                    field_vector.push_back(std::string(data_fields[i]));
                }
            }

            context->writeOBJ(filename, uuid_vector, field_vector, write_normals, silent);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_FILE_IO, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_FILE_IO, std::string("ERROR (Context::writeOBJ): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::writeOBJ): Unknown error writing OBJ file.");
        }
    }

    PYHELIOS_API void writePrimitiveData(helios::Context* context, const char* filename, const char** column_labels, unsigned int label_count, bool print_header) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null");
                return;
            }
            if (!column_labels && label_count > 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Column labels array is null but label_count > 0");
                return;
            }
            if (label_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Column labels array is empty");
                return;
            }

            // Convert C string array to vector of strings
            std::vector<std::string> column_format;
            column_format.reserve(label_count);
            for (unsigned int i = 0; i < label_count; i++) {
                if (column_labels[i]) {
                    column_format.push_back(std::string(column_labels[i]));
                }
            }

            // Call Helios method (all primitives version)
            context->writePrimitiveData(filename, column_format, print_header);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_FILE_IO, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_FILE_IO, std::string("ERROR (Context::writePrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::writePrimitiveData): Unknown error writing primitive data file.");
        }
    }

    PYHELIOS_API void writePrimitiveDataWithUUIDs(helios::Context* context, const char* filename, const char** column_labels, unsigned int label_count, unsigned int* uuids, unsigned int uuid_count, bool print_header) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null");
                return;
            }
            if (!column_labels && label_count > 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Column labels array is null but label_count > 0");
                return;
            }
            if (label_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Column labels array is empty");
                return;
            }
            if (!uuids && uuid_count > 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null but uuid_count > 0");
                return;
            }
            if (uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is empty");
                return;
            }

            // Convert C string array to vector of strings
            std::vector<std::string> column_format;
            column_format.reserve(label_count);
            for (unsigned int i = 0; i < label_count; i++) {
                if (column_labels[i]) {
                    column_format.push_back(std::string(column_labels[i]));
                }
            }

            // Convert C array to vector of UUIDs
            std::vector<unsigned int> uuid_vector(uuids, uuids + uuid_count);

            // Call Helios method (selected primitives version)
            context->writePrimitiveData(filename, column_format, uuid_vector, print_header);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_FILE_IO, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_FILE_IO, std::string("ERROR (Context::writePrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::writePrimitiveData): Unknown error writing primitive data file.");
        }
    }


    //=============================================================================
    // Primitive and Object Deletion Functions
    //=============================================================================

    PYHELIOS_API void deletePrimitive(helios::Context* context, unsigned int uuid) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            context->deletePrimitive(uuid);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::deletePrimitive): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::deletePrimitive): Unknown error.");
        }
    }

    PYHELIOS_API void deletePrimitives(helios::Context* context, unsigned int* uuids, unsigned int count) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!uuids && count > 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null but count > 0");
                return;
            }
            if (count == 0) {
                return;  // No-op for empty list
            }
            std::vector<unsigned int> uuid_vector(uuids, uuids + count);
            context->deletePrimitive(uuid_vector);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::deletePrimitives): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::deletePrimitives): Unknown error.");
        }
    }

    PYHELIOS_API void deleteObject(helios::Context* context, unsigned int objID) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            context->deleteObject(objID);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::deleteObject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::deleteObject): Unknown error.");
        }
    }

    PYHELIOS_API void deleteObjects(helios::Context* context, unsigned int* objIDs, unsigned int count) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!objIDs && count > 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Object IDs array is null but count > 0");
                return;
            }
            if (count == 0) {
                return;  // No-op for empty list
            }
            std::vector<unsigned int> objID_vector(objIDs, objIDs + count);
            context->deleteObject(objID_vector);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::deleteObjects): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::deleteObjects): Unknown error.");
        }
    }

    //=========================================================================
    // Materials System (v1.3.58+)
    //=========================================================================

    // Core Material Management

    PYHELIOS_API void addMaterial(void* context_ptr, const char* material_label) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!material_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Material label is null");
                return;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            context->addMaterial(std::string(material_label));
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addMaterial): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addMaterial): Unknown error.");
        }
    }

    PYHELIOS_API bool doesMaterialExist(void* context_ptr, const char* material_label) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return false;
            }
            if (!material_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Material label is null");
                return false;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            return context->doesMaterialExist(std::string(material_label));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::doesMaterialExist): ") + e.what());
            return false;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::doesMaterialExist): Unknown error.");
            return false;
        }
    }

    PYHELIOS_API const char** listMaterials(void* context_ptr, size_t* count) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            std::vector<std::string> materials = context->listMaterials();

            *count = materials.size();
            if (materials.empty()) {
                return nullptr;
            }

            static thread_local std::vector<char*> string_ptrs;
            static thread_local std::vector<std::string> string_storage;

            string_storage = materials;
            string_ptrs.clear();
            string_ptrs.reserve(materials.size());

            for (auto& str : string_storage) {
                string_ptrs.push_back(const_cast<char*>(str.c_str()));
            }

            return const_cast<const char**>(string_ptrs.data());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::listMaterials): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::listMaterials): Unknown error.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API void deleteMaterial(void* context_ptr, const char* material_label) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!material_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Material label is null");
                return;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            context->deleteMaterial(std::string(material_label));
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::deleteMaterial): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::deleteMaterial): Unknown error.");
        }
    }

    // Material Properties

    PYHELIOS_API void getMaterialColor(void* context_ptr, const char* material_label, float* color) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!material_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Material label is null");
                return;
            }
            if (!color) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Color array pointer is null");
                return;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            helios::RGBAcolor mat_color = context->getMaterialColor(std::string(material_label));
            color[0] = mat_color.r;
            color[1] = mat_color.g;
            color[2] = mat_color.b;
            color[3] = mat_color.a;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getMaterialColor): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getMaterialColor): Unknown error.");
        }
    }

    PYHELIOS_API void setMaterialColor(void* context_ptr, const char* material_label, float r, float g, float b, float a) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!material_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Material label is null");
                return;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            context->setMaterialColor(std::string(material_label), helios::make_RGBAcolor(r, g, b, a));
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setMaterialColor): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setMaterialColor): Unknown error.");
        }
    }

    PYHELIOS_API const char* getMaterialTexture(void* context_ptr, const char* material_label) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return "";
            }
            if (!material_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Material label is null");
                return "";
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            static thread_local std::string texture_str;
            texture_str = context->getMaterialTexture(std::string(material_label));
            return texture_str.c_str();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getMaterialTexture): ") + e.what());
            return "";
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getMaterialTexture): Unknown error.");
            return "";
        }
    }

    PYHELIOS_API void setMaterialTexture(void* context_ptr, const char* material_label, const char* texture_file) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!material_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Material label is null");
                return;
            }
            if (!texture_file) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Texture file path is null");
                return;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            context->setMaterialTexture(std::string(material_label), std::string(texture_file));
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setMaterialTexture): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setMaterialTexture): Unknown error.");
        }
    }

    PYHELIOS_API bool isMaterialTextureColorOverridden(void* context_ptr, const char* material_label) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return false;
            }
            if (!material_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Material label is null");
                return false;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            return context->isMaterialTextureColorOverridden(std::string(material_label));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::isMaterialTextureColorOverridden): ") + e.what());
            return false;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::isMaterialTextureColorOverridden): Unknown error.");
            return false;
        }
    }

    PYHELIOS_API void setMaterialTextureColorOverride(void* context_ptr, const char* material_label, bool override) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!material_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Material label is null");
                return;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            context->setMaterialTextureColorOverride(std::string(material_label), override);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setMaterialTextureColorOverride): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setMaterialTextureColorOverride): Unknown error.");
        }
    }

    PYHELIOS_API unsigned int getMaterialTwosidedFlag(void* context_ptr, const char* material_label) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 1;
            }
            if (!material_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Material label is null");
                return 1;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            return context->getMaterialTwosidedFlag(std::string(material_label));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getMaterialTwosidedFlag): ") + e.what());
            return 1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getMaterialTwosidedFlag): Unknown error.");
            return 1;
        }
    }

    PYHELIOS_API void setMaterialTwosidedFlag(void* context_ptr, const char* material_label, unsigned int twosided_flag) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!material_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Material label is null");
                return;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            context->setMaterialTwosidedFlag(std::string(material_label), twosided_flag);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setMaterialTwosidedFlag): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setMaterialTwosidedFlag): Unknown error.");
        }
    }

    // Primitive-Material Assignment

    PYHELIOS_API void assignMaterialToPrimitive(void* context_ptr, unsigned int UUID, const char* material_label) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!material_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Material label is null");
                return;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            context->assignMaterialToPrimitive(UUID, std::string(material_label));
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::assignMaterialToPrimitive): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::assignMaterialToPrimitive): Unknown error.");
        }
    }

    PYHELIOS_API void assignMaterialToPrimitives(void* context_ptr, const unsigned int* UUIDs, size_t count, const char* material_label) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!UUIDs && count > 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null but count > 0");
                return;
            }
            if (!material_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Material label is null");
                return;
            }
            if (count == 0) {
                return;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            std::vector<unsigned int> uuid_vector(UUIDs, UUIDs + count);
            context->assignMaterialToPrimitive(uuid_vector, std::string(material_label));
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::assignMaterialToPrimitives): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::assignMaterialToPrimitives): Unknown error.");
        }
    }

    PYHELIOS_API void assignMaterialToObject(void* context_ptr, unsigned int ObjID, const char* material_label) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!material_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Material label is null");
                return;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            context->assignMaterialToObject(ObjID, std::string(material_label));
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::assignMaterialToObject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::assignMaterialToObject): Unknown error.");
        }
    }

    PYHELIOS_API void assignMaterialToObjects(void* context_ptr, const unsigned int* ObjIDs, size_t count, const char* material_label) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            if (!ObjIDs && count > 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ObjIDs array is null but count > 0");
                return;
            }
            if (!material_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Material label is null");
                return;
            }
            if (count == 0) {
                return;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            std::vector<unsigned int> objID_vector(ObjIDs, ObjIDs + count);
            context->assignMaterialToObject(objID_vector, std::string(material_label));
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::assignMaterialToObjects): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::assignMaterialToObjects): Unknown error.");
        }
    }

    PYHELIOS_API const char* getPrimitiveMaterialLabel(void* context_ptr, unsigned int UUID) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return "";
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            static thread_local std::string material_label;
            material_label = context->getPrimitiveMaterialLabel(UUID);
            return material_label.c_str();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveMaterialLabel): ") + e.what());
            return "";
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveMaterialLabel): Unknown error.");
            return "";
        }
    }

    PYHELIOS_API unsigned int getPrimitiveTwosidedFlag(void* context_ptr, unsigned int UUID, unsigned int default_value) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return default_value;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            return context->getPrimitiveTwosidedFlag(UUID, default_value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveTwosidedFlag): ") + e.what());
            return default_value;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveTwosidedFlag): Unknown error.");
            return default_value;
        }
    }

    PYHELIOS_API const unsigned int* getPrimitivesUsingMaterial(void* context_ptr, const char* material_label, size_t* count) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!material_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Material label is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            static thread_local std::vector<unsigned int> uuids;
            uuids = context->getPrimitivesUsingMaterial(std::string(material_label));
            *count = uuids.size();
            return uuids.empty() ? nullptr : uuids.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitivesUsingMaterial): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitivesUsingMaterial): Unknown error.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    //=============================================================================
    // Texture Functions
    //=============================================================================

    PYHELIOS_API const char* getPrimitiveTextureFile(void* context_ptr, unsigned int uuid) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return "";
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            static thread_local std::string texture_file;
            texture_file = context->getPrimitiveTextureFile(uuid);
            return texture_file.c_str();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveTextureFile): ") + e.what());
            return "";
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveTextureFile): Unknown error.");
            return "";
        }
    }

    PYHELIOS_API void setPrimitiveTextureFile(void* context_ptr, unsigned int uuid, const char* texture_file) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            context->setPrimitiveTextureFile(uuid, std::string(texture_file));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveTextureFile): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveTextureFile): Unknown error.");
        }
    }

    PYHELIOS_API void getPrimitiveTextureSize(void* context_ptr, unsigned int uuid, int* width, int* height) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                if (width) *width = 0;
                if (height) *height = 0;
                return;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            helios::int2 size = context->getPrimitiveTextureSize(uuid);
            if (width) *width = size.x;
            if (height) *height = size.y;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveTextureSize): ") + e.what());
            if (width) *width = 0;
            if (height) *height = 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveTextureSize): Unknown error.");
            if (width) *width = 0;
            if (height) *height = 0;
        }
    }

    PYHELIOS_API float* getPrimitiveTextureUV(void* context_ptr, unsigned int uuid, unsigned int* size) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                if (size) *size = 0;
                return nullptr;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            std::vector<helios::vec2> uvs = context->getPrimitiveTextureUV(uuid);

            static thread_local std::vector<float> uv_buffer;
            uv_buffer.clear();
            uv_buffer.reserve(uvs.size() * 2);
            for (const auto& uv : uvs) {
                uv_buffer.push_back(uv.x);
                uv_buffer.push_back(uv.y);
            }
            if (size) *size = uv_buffer.size();
            return uv_buffer.empty() ? nullptr : uv_buffer.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveTextureUV): ") + e.what());
            if (size) *size = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveTextureUV): Unknown error.");
            if (size) *size = 0;
            return nullptr;
        }
    }

    PYHELIOS_API bool primitiveTextureHasTransparencyChannel(void* context_ptr, unsigned int uuid) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return false;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            return context->primitiveTextureHasTransparencyChannel(uuid);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::primitiveTextureHasTransparencyChannel): ") + e.what());
            return false;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::primitiveTextureHasTransparencyChannel): Unknown error.");
            return false;
        }
    }

    PYHELIOS_API float getPrimitiveSolidFraction(void* context_ptr, unsigned int uuid) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return 0.0f;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            return context->getPrimitiveSolidFraction(uuid);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveSolidFraction): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveSolidFraction): Unknown error.");
            return 0.0f;
        }
    }

    PYHELIOS_API void overridePrimitiveTextureColor(void* context_ptr, unsigned int uuid) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            context->overridePrimitiveTextureColor(uuid);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::overridePrimitiveTextureColor): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::overridePrimitiveTextureColor): Unknown error.");
        }
    }

    PYHELIOS_API void usePrimitiveTextureColor(void* context_ptr, unsigned int uuid) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            context->usePrimitiveTextureColor(uuid);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::usePrimitiveTextureColor): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::usePrimitiveTextureColor): Unknown error.");
        }
    }

    PYHELIOS_API bool isPrimitiveTextureColorOverridden(void* context_ptr, unsigned int uuid) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return false;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            return context->isPrimitiveTextureColorOverridden(uuid);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::isPrimitiveTextureColorOverridden): ") + e.what());
            return false;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::isPrimitiveTextureColorOverridden): Unknown error.");
            return false;
        }
    }

    //=============================================================================
    // Fixed-Size Batch Getters
    //=============================================================================

    PYHELIOS_API float* getBatchPrimitiveNormals(void* context_ptr, unsigned int* uuids, unsigned int count, unsigned int* result_size) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                if (result_size) *result_size = 0;
                return nullptr;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            static thread_local std::vector<float> buffer;
            buffer.clear();
            buffer.reserve(count * 3);
            for (unsigned int i = 0; i < count; i++) {
                helios::vec3 normal = context->getPrimitiveNormal(uuids[i]);
                buffer.push_back(normal.x);
                buffer.push_back(normal.y);
                buffer.push_back(normal.z);
            }
            if (result_size) *result_size = buffer.size();
            return buffer.empty() ? nullptr : buffer.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getBatchPrimitiveNormals): ") + e.what());
            if (result_size) *result_size = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getBatchPrimitiveNormals): Unknown error.");
            if (result_size) *result_size = 0;
            return nullptr;
        }
    }

    PYHELIOS_API float* getBatchPrimitiveColors(void* context_ptr, unsigned int* uuids, unsigned int count, unsigned int* result_size) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                if (result_size) *result_size = 0;
                return nullptr;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            static thread_local std::vector<float> buffer;
            buffer.clear();
            buffer.reserve(count * 3);
            for (unsigned int i = 0; i < count; i++) {
                helios::RGBcolor color = context->getPrimitiveColor(uuids[i]);
                buffer.push_back(color.r);
                buffer.push_back(color.g);
                buffer.push_back(color.b);
            }
            if (result_size) *result_size = buffer.size();
            return buffer.empty() ? nullptr : buffer.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getBatchPrimitiveColors): ") + e.what());
            if (result_size) *result_size = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getBatchPrimitiveColors): Unknown error.");
            if (result_size) *result_size = 0;
            return nullptr;
        }
    }

    PYHELIOS_API float* getBatchPrimitiveAreas(void* context_ptr, unsigned int* uuids, unsigned int count, unsigned int* result_size) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                if (result_size) *result_size = 0;
                return nullptr;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            static thread_local std::vector<float> buffer;
            buffer.clear();
            buffer.reserve(count);
            for (unsigned int i = 0; i < count; i++) {
                buffer.push_back(context->getPrimitiveArea(uuids[i]));
            }
            if (result_size) *result_size = buffer.size();
            return buffer.empty() ? nullptr : buffer.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getBatchPrimitiveAreas): ") + e.what());
            if (result_size) *result_size = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getBatchPrimitiveAreas): Unknown error.");
            if (result_size) *result_size = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* getBatchPrimitiveTypes(void* context_ptr, unsigned int* uuids, unsigned int count, unsigned int* result_size) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                if (result_size) *result_size = 0;
                return nullptr;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            static thread_local std::vector<unsigned int> buffer;
            buffer.clear();
            buffer.reserve(count);
            for (unsigned int i = 0; i < count; i++) {
                buffer.push_back((unsigned int)context->getPrimitiveType(uuids[i]));
            }
            if (result_size) *result_size = buffer.size();
            return buffer.empty() ? nullptr : buffer.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getBatchPrimitiveTypes): ") + e.what());
            if (result_size) *result_size = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getBatchPrimitiveTypes): Unknown error.");
            if (result_size) *result_size = 0;
            return nullptr;
        }
    }

    PYHELIOS_API float* getBatchPrimitiveSolidFractions(void* context_ptr, unsigned int* uuids, unsigned int count, unsigned int* result_size) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                if (result_size) *result_size = 0;
                return nullptr;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            static thread_local std::vector<float> buffer;
            buffer.clear();
            buffer.reserve(count);
            for (unsigned int i = 0; i < count; i++) {
                buffer.push_back(context->getPrimitiveSolidFraction(uuids[i]));
            }
            if (result_size) *result_size = buffer.size();
            return buffer.empty() ? nullptr : buffer.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getBatchPrimitiveSolidFractions): ") + e.what());
            if (result_size) *result_size = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getBatchPrimitiveSolidFractions): Unknown error.");
            if (result_size) *result_size = 0;
            return nullptr;
        }
    }

    //=============================================================================
    // Variable-Size Batch Getters
    //=============================================================================

    PYHELIOS_API float* getBatchPrimitiveVertices(void* context_ptr, unsigned int* uuids, unsigned int count, unsigned int* offsets_out, unsigned int* total_floats) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                if (total_floats) *total_floats = 0;
                return nullptr;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            static thread_local std::vector<float> buffer;
            buffer.clear();

            for (unsigned int i = 0; i < count; i++) {
                if (offsets_out) offsets_out[i] = buffer.size();
                std::vector<helios::vec3> vertices = context->getPrimitiveVertices(uuids[i]);
                for (const auto& v : vertices) {
                    buffer.push_back(v.x);
                    buffer.push_back(v.y);
                    buffer.push_back(v.z);
                }
            }
            if (offsets_out) offsets_out[count] = buffer.size();
            if (total_floats) *total_floats = buffer.size();
            return buffer.empty() ? nullptr : buffer.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getBatchPrimitiveVertices): ") + e.what());
            if (total_floats) *total_floats = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getBatchPrimitiveVertices): Unknown error.");
            if (total_floats) *total_floats = 0;
            return nullptr;
        }
    }

    PYHELIOS_API float* getBatchPrimitiveTextureUV(void* context_ptr, unsigned int* uuids, unsigned int count, unsigned int* offsets_out, unsigned int* total_floats) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                if (total_floats) *total_floats = 0;
                return nullptr;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            static thread_local std::vector<float> buffer;
            buffer.clear();

            for (unsigned int i = 0; i < count; i++) {
                if (offsets_out) offsets_out[i] = buffer.size();
                std::vector<helios::vec2> uvs = context->getPrimitiveTextureUV(uuids[i]);
                for (const auto& uv : uvs) {
                    buffer.push_back(uv.x);
                    buffer.push_back(uv.y);
                }
            }
            if (offsets_out) offsets_out[count] = buffer.size();
            if (total_floats) *total_floats = buffer.size();
            return buffer.empty() ? nullptr : buffer.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getBatchPrimitiveTextureUV): ") + e.what());
            if (total_floats) *total_floats = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getBatchPrimitiveTextureUV): Unknown error.");
            if (total_floats) *total_floats = 0;
            return nullptr;
        }
    }

    PYHELIOS_API const char* getBatchPrimitiveTextureFiles(void* context_ptr, unsigned int* uuids, unsigned int count, unsigned int* offsets_out, unsigned int* total_chars) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                if (total_chars) *total_chars = 0;
                return nullptr;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            static thread_local std::string buffer;
            buffer.clear();

            for (unsigned int i = 0; i < count; i++) {
                if (offsets_out) offsets_out[i] = buffer.size();
                std::string file = context->getPrimitiveTextureFile(uuids[i]);
                buffer.append(file);
            }
            if (offsets_out) offsets_out[count] = buffer.size();
            if (total_chars) *total_chars = buffer.size();
            return buffer.empty() ? "" : buffer.c_str();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getBatchPrimitiveTextureFiles): ") + e.what());
            if (total_chars) *total_chars = 0;
            return "";
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getBatchPrimitiveTextureFiles): Unknown error.");
            if (total_chars) *total_chars = 0;
            return "";
        }
    }

    PYHELIOS_API const char* getBatchPrimitiveMaterialLabels(void* context_ptr, unsigned int* uuids, unsigned int count, unsigned int* offsets_out, unsigned int* total_chars) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                if (total_chars) *total_chars = 0;
                return nullptr;
            }
            helios::Context* context = static_cast<helios::Context*>(context_ptr);
            static thread_local std::string buffer;
            buffer.clear();

            for (unsigned int i = 0; i < count; i++) {
                if (offsets_out) offsets_out[i] = buffer.size();
                std::string label = context->getPrimitiveMaterialLabel(uuids[i]);
                buffer.append(label);
            }
            if (offsets_out) offsets_out[count] = buffer.size();
            if (total_chars) *total_chars = buffer.size();
            return buffer.empty() ? "" : buffer.c_str();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getBatchPrimitiveMaterialLabels): ") + e.what());
            if (total_chars) *total_chars = 0;
            return "";
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getBatchPrimitiveMaterialLabels): Unknown error.");
            if (total_chars) *total_chars = 0;
            return "";
        }
    }

    PYHELIOS_API const char* resolveMaterialTextures(
        void* context_ptr,
        unsigned int* uuids,
        unsigned int count,
        float* colors_inout,
        unsigned int* tex_offsets_out,
        unsigned int* total_chars_out
    ) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                if (total_chars_out) *total_chars_out = 0;
                return nullptr;
            }

            helios::Context* context = static_cast<helios::Context*>(context_ptr);

            // Material info cache keyed by uint materialID (fast hash, ~5-10 entries)
            struct MatInfo {
                bool has_texture;
                bool tex_color_override;
                float r, g, b;
                std::string texture_file;  // stored once per unique material
            };

            std::unordered_map<unsigned int, MatInfo> mat_cache;
            static thread_local std::string buffer;
            buffer.clear();

            for (unsigned int i = 0; i < count; i++) {
                if (tex_offsets_out) tex_offsets_out[i] = buffer.size();

                // Single map lookup: UUID -> Primitive* -> materialID
                unsigned int matID = context->getPrimitiveMaterialID(uuids[i]);

                // Cache miss: look up material once via const Material& (one map lookup)
                auto it = mat_cache.find(matID);
                if (it == mat_cache.end()) {
                    MatInfo info = {false, false, 0.0f, 0.0f, 0.0f, ""};
                    const helios::Material& mat = context->getMaterial(matID);
                    info.texture_file = mat.texture_file;
                    info.has_texture = !mat.texture_file.empty();
                    info.tex_color_override = mat.texture_color_overridden;
                    info.r = mat.color.r;
                    info.g = mat.color.g;
                    info.b = mat.color.b;
                    auto inserted = mat_cache.emplace(matID, std::move(info));
                    it = inserted.first;
                }

                const MatInfo& mat = it->second;

                // The texture file comes from the material (Primitive::getTextureFile()
                // just returns context->materials.at(materialID).texture_file)
                if (mat.has_texture) {
                    if (mat.tex_color_override) {
                        // Rule 2: Mask — material has texture and color override is set
                        buffer.append("mask:");
                        buffer.append(mat.texture_file);
                        colors_inout[i * 3 + 0] = mat.r;
                        colors_inout[i * 3 + 1] = mat.g;
                        colors_inout[i * 3 + 2] = mat.b;
                    } else {
                        // Rule 3: Pass-through — material has texture, no override
                        buffer.append(mat.texture_file);
                    }
                } else {
                    // Rule 1 / pass-through: material has no texture
                    // Texture file is empty, override color with material color
                    colors_inout[i * 3 + 0] = mat.r;
                    colors_inout[i * 3 + 1] = mat.g;
                    colors_inout[i * 3 + 2] = mat.b;
                    // buffer gets nothing appended (empty tex_file)
                }
            }

            if (tex_offsets_out) tex_offsets_out[count] = buffer.size();
            if (total_chars_out) *total_chars_out = buffer.size();
            return buffer.empty() ? "" : buffer.c_str();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::resolveMaterialTextures): ") + e.what());
            if (total_chars_out) *total_chars_out = 0;
            return "";
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::resolveMaterialTextures): Unknown error.");
            if (total_chars_out) *total_chars_out = 0;
            return "";
        }
    }

    PYHELIOS_API unsigned char* packGPUBuffers(
        void* context_ptr,
        unsigned int* uuids,
        unsigned int count,
        unsigned int* out_size
    ) {
        try {
            clearError();
            if (!context_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                if (out_size) *out_size = 0;
                return nullptr;
            }
            if (count == 0) {
                if (out_size) *out_size = 0;
                return nullptr;
            }

            helios::Context* context = static_cast<helios::Context*>(context_ptr);

            // ---- Material cache (same pattern as resolveMaterialTextures) ----
            struct MatInfo {
                bool has_texture;
                bool tex_color_override;
                float r, g, b;
                std::string texture_file;
            };
            std::unordered_map<unsigned int, MatInfo> mat_cache;

            // ---- First pass: gather per-primitive metadata ----
            struct PrimMeta {
                unsigned int uuid;
                unsigned int vert_count;
                unsigned int tri_count;
                std::string group_key;  // "" = untextured, "mask:path" = mask, "path" = textured
                bool has_texture;
                bool mask_mode;
            };

            std::vector<PrimMeta> metas(count);
            unsigned int total_verts = 0;
            unsigned int total_tris = 0;

            for (unsigned int i = 0; i < count; i++) {
                PrimMeta& m = metas[i];
                m.uuid = uuids[i];

                // Get vertex count
                std::vector<helios::vec3> vertices = context->getPrimitiveVertices(m.uuid);
                m.vert_count = vertices.size();
                m.tri_count = (m.vert_count >= 3) ? (m.vert_count - 2) : 0;

                // Material resolution
                unsigned int matID = context->getPrimitiveMaterialID(m.uuid);
                auto it = mat_cache.find(matID);
                if (it == mat_cache.end()) {
                    MatInfo info = {false, false, 0.0f, 0.0f, 0.0f, ""};
                    const helios::Material& mat = context->getMaterial(matID);
                    info.texture_file = mat.texture_file;
                    info.has_texture = !mat.texture_file.empty();
                    info.tex_color_override = mat.texture_color_overridden;
                    info.r = mat.color.r;
                    info.g = mat.color.g;
                    info.b = mat.color.b;
                    auto inserted = mat_cache.emplace(matID, std::move(info));
                    it = inserted.first;
                }
                const MatInfo& mat = it->second;

                if (mat.has_texture) {
                    if (mat.tex_color_override) {
                        m.group_key = "mask:" + mat.texture_file;
                        m.mask_mode = true;
                        m.has_texture = true;
                    } else {
                        m.group_key = mat.texture_file;
                        m.mask_mode = false;
                        m.has_texture = true;
                    }
                } else {
                    m.group_key = "";
                    m.mask_mode = false;
                    m.has_texture = false;
                }

                total_verts += m.vert_count;
                total_tris += m.tri_count;
            }

            // ---- Sort by group key ----
            std::vector<unsigned int> sorted_indices(count);
            for (unsigned int i = 0; i < count; i++) sorted_indices[i] = i;
            std::sort(sorted_indices.begin(), sorted_indices.end(),
                [&metas](unsigned int a, unsigned int b) {
                    return metas[a].group_key < metas[b].group_key;
                });

            // ---- Identify groups ----
            struct GroupDesc {
                std::string group_key;
                std::string texture_path;
                bool mask_mode;
                bool has_uvs;
                bool has_colors;
                unsigned int vertex_start;
                unsigned int vertex_count;
                unsigned int triangle_start;
                unsigned int triangle_count;
            };

            std::vector<GroupDesc> groups;
            {
                unsigned int v_offset = 0;
                unsigned int t_offset = 0;
                unsigned int gi = 0;
                while (gi < count) {
                    const std::string& key = metas[sorted_indices[gi]].group_key;
                    GroupDesc gd;
                    gd.group_key = key;
                    gd.mask_mode = metas[sorted_indices[gi]].mask_mode;
                    gd.has_uvs = !key.empty();  // textured or mask both have UVs
                    gd.has_colors = key.empty() || gd.mask_mode;  // untextured and mask have vertex colors
                    gd.vertex_start = v_offset;
                    gd.triangle_start = t_offset;

                    if (gd.mask_mode) {
                        gd.texture_path = key.substr(5);  // strip "mask:" prefix
                    } else if (!key.empty()) {
                        gd.texture_path = key;
                    }

                    unsigned int group_verts = 0;
                    unsigned int group_tris = 0;
                    while (gi < count && metas[sorted_indices[gi]].group_key == key) {
                        group_verts += metas[sorted_indices[gi]].vert_count;
                        group_tris += metas[sorted_indices[gi]].tri_count;
                        gi++;
                    }
                    gd.vertex_count = group_verts;
                    gd.triangle_count = group_tris;
                    v_offset += group_verts;
                    t_offset += group_tris;
                    groups.push_back(std::move(gd));
                }
            }

            unsigned int group_count = groups.size();

            // ---- Compute buffer layout ----
            // Header: 16 bytes
            unsigned int header_size = 16;

            // Group descriptors: 19 bytes fixed + texture_path_length per group
            unsigned int descriptors_size = 0;
            for (const auto& g : groups) {
                descriptors_size += 19 + g.texture_path.size();
            }

            // Align descriptor end to 4-byte boundary for typed arrays
            unsigned int aligned_desc_end = ((header_size + descriptors_size) + 3) & ~3u;

            // Typed arrays
            unsigned int positions_size = total_verts * 3 * sizeof(float);
            unsigned int colors_size = total_verts * 3 * sizeof(float);
            unsigned int uvs_size = total_verts * 2 * sizeof(float);
            unsigned int indices_size = total_tris * 3 * sizeof(uint32_t);
            unsigned int faceToUuid_size = total_tris * sizeof(uint32_t);

            unsigned int total_size = aligned_desc_end +
                positions_size + colors_size + uvs_size +
                indices_size + faceToUuid_size;

            // ---- Allocate output buffer ----
            static thread_local std::vector<unsigned char> buffer;
            buffer.resize(total_size);
            unsigned char* buf = buffer.data();

            // ---- Write header ----
            buf[0] = 2;  // version
            buf[1] = 0;  // flags
            buf[2] = group_count & 0xFF;
            buf[3] = (group_count >> 8) & 0xFF;
            *reinterpret_cast<uint32_t*>(buf + 4) = total_verts;
            *reinterpret_cast<uint32_t*>(buf + 8) = total_tris;
            *reinterpret_cast<uint32_t*>(buf + 12) = count;

            // ---- Write group descriptors ----
            unsigned int offset = header_size;
            for (const auto& g : groups) {
                *reinterpret_cast<uint32_t*>(buf + offset) = g.vertex_start; offset += 4;
                *reinterpret_cast<uint32_t*>(buf + offset) = g.vertex_count; offset += 4;
                *reinterpret_cast<uint32_t*>(buf + offset) = g.triangle_start; offset += 4;
                *reinterpret_cast<uint32_t*>(buf + offset) = g.triangle_count; offset += 4;
                uint16_t tex_len = g.texture_path.size();
                *reinterpret_cast<uint16_t*>(buf + offset) = tex_len; offset += 2;
                uint8_t flags = 0;
                if (g.mask_mode) flags |= 0x01;
                if (g.has_uvs) flags |= 0x02;
                if (g.has_colors) flags |= 0x04;
                buf[offset] = flags; offset += 1;
                if (tex_len > 0) {
                    memcpy(buf + offset, g.texture_path.c_str(), tex_len);
                    offset += tex_len;
                }
            }

            // ---- Compute array offsets (4-byte aligned) ----
            offset = aligned_desc_end;  // skip any padding bytes
            unsigned int pos_offset = offset;
            unsigned int col_offset = pos_offset + positions_size;
            unsigned int uv_offset = col_offset + colors_size;
            unsigned int idx_offset = uv_offset + uvs_size;
            unsigned int ftu_offset = idx_offset + indices_size;

            float* positions_ptr = reinterpret_cast<float*>(buf + pos_offset);
            float* colors_ptr = reinterpret_cast<float*>(buf + col_offset);
            float* uvs_ptr = reinterpret_cast<float*>(buf + uv_offset);
            uint32_t* indices_ptr = reinterpret_cast<uint32_t*>(buf + idx_offset);
            uint32_t* ftu_ptr = reinterpret_cast<uint32_t*>(buf + ftu_offset);

            // Zero-fill UVs (untextured prims will have 0,0 UVs)
            memset(buf + uv_offset, 0, uvs_size);
            // Zero-fill colors (textured-only prims won't set colors)
            memset(buf + col_offset, 0, colors_size);

            // ---- Second pass: populate arrays ----
            unsigned int v_cursor = 0;  // current vertex write position
            unsigned int t_cursor = 0;  // current triangle write position

            for (unsigned int si = 0; si < count; si++) {
                unsigned int pi = sorted_indices[si];
                const PrimMeta& m = metas[pi];

                // Fetch vertex positions
                std::vector<helios::vec3> vertices = context->getPrimitiveVertices(m.uuid);
                unsigned int nv = vertices.size();

                // Write positions
                for (unsigned int vi = 0; vi < nv; vi++) {
                    positions_ptr[v_cursor * 3 + vi * 3 + 0] = vertices[vi].x;
                    positions_ptr[v_cursor * 3 + vi * 3 + 1] = vertices[vi].y;
                    positions_ptr[v_cursor * 3 + vi * 3 + 2] = vertices[vi].z;
                }

                // Write colors (material-resolved)
                unsigned int matID = context->getPrimitiveMaterialID(m.uuid);
                const MatInfo& mat = mat_cache[matID];
                if (m.group_key.empty() || m.mask_mode) {
                    // Untextured or mask mode: use material color
                    float cr = mat.r, cg = mat.g, cb = mat.b;
                    if (mat.has_texture && !mat.tex_color_override) {
                        // Normal texture, no override — use primitive color
                        helios::RGBcolor pc = context->getPrimitiveColor(m.uuid);
                        cr = pc.r; cg = pc.g; cb = pc.b;
                    }
                    for (unsigned int vi = 0; vi < nv; vi++) {
                        colors_ptr[v_cursor * 3 + vi * 3 + 0] = cr;
                        colors_ptr[v_cursor * 3 + vi * 3 + 1] = cg;
                        colors_ptr[v_cursor * 3 + vi * 3 + 2] = cb;
                    }
                }

                // Write UVs (if textured or mask)
                if (m.has_texture || m.mask_mode) {
                    std::vector<helios::vec2> uvs = context->getPrimitiveTextureUV(m.uuid);
                    for (unsigned int vi = 0; vi < std::min((unsigned int)uvs.size(), nv); vi++) {
                        uvs_ptr[v_cursor * 2 + vi * 2 + 0] = uvs[vi].x;
                        uvs_ptr[v_cursor * 2 + vi * 2 + 1] = 1.0f - uvs[vi].y;  // V-flip for Three.js
                    }
                }

                // Write indices (triangle fan for polygons) and faceToUuid
                if (nv >= 3) {
                    for (unsigned int ti = 0; ti < nv - 2; ti++) {
                        indices_ptr[t_cursor * 3 + 0] = v_cursor;
                        indices_ptr[t_cursor * 3 + 1] = v_cursor + ti + 1;
                        indices_ptr[t_cursor * 3 + 2] = v_cursor + ti + 2;
                        ftu_ptr[t_cursor] = m.uuid;
                        t_cursor++;
                    }
                }

                v_cursor += nv;
            }

            if (out_size) *out_size = total_size;
            return buffer.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (packGPUBuffers): ") + e.what());
            if (out_size) *out_size = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (packGPUBuffers): Unknown error.");
            if (out_size) *out_size = 0;
            return nullptr;
        }
    }

    // ==================== Visibility Functions ====================

    PYHELIOS_API void hidePrimitive(helios::Context* context, unsigned int uuid) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            context->hidePrimitive(uuid);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::hidePrimitive): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::hidePrimitive): Unknown error.");
        }
    }

    PYHELIOS_API void hidePrimitives(helios::Context* context, unsigned int* uuids, unsigned int count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!uuids || count == 0) { return; }
            std::vector<uint> uuids_vec(uuids, uuids + count);
            context->hidePrimitive(uuids_vec);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::hidePrimitive batch): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::hidePrimitive batch): Unknown error.");
        }
    }

    PYHELIOS_API void showPrimitive(helios::Context* context, unsigned int uuid) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            context->showPrimitive(uuid);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::showPrimitive): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::showPrimitive): Unknown error.");
        }
    }

    PYHELIOS_API void showPrimitives(helios::Context* context, unsigned int* uuids, unsigned int count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!uuids || count == 0) { return; }
            std::vector<uint> uuids_vec(uuids, uuids + count);
            context->showPrimitive(uuids_vec);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::showPrimitive batch): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::showPrimitive batch): Unknown error.");
        }
    }

    PYHELIOS_API bool isPrimitiveHidden(helios::Context* context, unsigned int uuid) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return false; }
            return context->isPrimitiveHidden(uuid);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::isPrimitiveHidden): ") + e.what());
            return false;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::isPrimitiveHidden): Unknown error.");
            return false;
        }
    }

    PYHELIOS_API void hideObject(helios::Context* context, unsigned int objID) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            context->hideObject(objID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::hideObject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::hideObject): Unknown error.");
        }
    }

    PYHELIOS_API void hideObjects(helios::Context* context, unsigned int* objIDs, unsigned int count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!objIDs || count == 0) { return; }
            std::vector<uint> ids_vec(objIDs, objIDs + count);
            context->hideObject(ids_vec);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::hideObject batch): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::hideObject batch): Unknown error.");
        }
    }

    PYHELIOS_API void showObject(helios::Context* context, unsigned int objID) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            context->showObject(objID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::showObject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::showObject): Unknown error.");
        }
    }

    PYHELIOS_API void showObjects(helios::Context* context, unsigned int* objIDs, unsigned int count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!objIDs || count == 0) { return; }
            std::vector<uint> ids_vec(objIDs, objIDs + count);
            context->showObject(ids_vec);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::showObject batch): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::showObject batch): Unknown error.");
        }
    }

    PYHELIOS_API bool isObjectHidden(helios::Context* context, unsigned int objID) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return false; }
            return context->isObjectHidden(objID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::isObjectHidden): ") + e.what());
            return false;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::isObjectHidden): Unknown error.");
            return false;
        }
    }

    // ==================== Object Data Functions ====================

    // --- Setters (single) ---

    PYHELIOS_API void setObjectDataInt(helios::Context* context, unsigned int objID, const char* label, int value) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->setObjectData(objID, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void setObjectDataUInt(helios::Context* context, unsigned int objID, const char* label, unsigned int value) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->setObjectData(objID, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void setObjectDataFloat(helios::Context* context, unsigned int objID, const char* label, float value) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->setObjectData(objID, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void setObjectDataDouble(helios::Context* context, unsigned int objID, const char* label, double value) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->setObjectData(objID, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void setObjectDataString(helios::Context* context, unsigned int objID, const char* label, const char* value) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label || !value) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or value is null"); return; }
            std::string str_value(value);
            context->setObjectData(objID, label, str_value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void setObjectDataVec2(helios::Context* context, unsigned int objID, const char* label, float x, float y) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            helios::vec2 v(x, y);
            context->setObjectData(objID, label, v);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void setObjectDataVec3(helios::Context* context, unsigned int objID, const char* label, float x, float y, float z) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            helios::vec3 v(x, y, z);
            context->setObjectData(objID, label, v);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void setObjectDataVec4(helios::Context* context, unsigned int objID, const char* label, float x, float y, float z, float w) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            helios::vec4 v(x, y, z, w);
            context->setObjectData(objID, label, v);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void setObjectDataInt2(helios::Context* context, unsigned int objID, const char* label, int x, int y) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            helios::int2 v(x, y);
            context->setObjectData(objID, label, v);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void setObjectDataInt3(helios::Context* context, unsigned int objID, const char* label, int x, int y, int z) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            helios::int3 v(x, y, z);
            context->setObjectData(objID, label, v);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void setObjectDataInt4(helios::Context* context, unsigned int objID, const char* label, int x, int y, int z, int w) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            helios::int4 v(x, y, z, w);
            context->setObjectData(objID, label, v);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setObjectData): Unknown error.");
        }
    }

    // --- Broadcast setters ---

    PYHELIOS_API void setBroadcastObjectDataInt(helios::Context* context, unsigned int* objIDs, size_t count, const char* label, int value) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!objIDs || count == 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Object IDs array is null or empty"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            std::vector<uint> ids_vec(objIDs, objIDs + count);
            context->setObjectData(ids_vec, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setBroadcastObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setBroadcastObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void setBroadcastObjectDataUInt(helios::Context* context, unsigned int* objIDs, size_t count, const char* label, unsigned int value) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!objIDs || count == 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Object IDs array is null or empty"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            std::vector<uint> ids_vec(objIDs, objIDs + count);
            context->setObjectData(ids_vec, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setBroadcastObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setBroadcastObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void setBroadcastObjectDataFloat(helios::Context* context, unsigned int* objIDs, size_t count, const char* label, float value) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!objIDs || count == 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Object IDs array is null or empty"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            std::vector<uint> ids_vec(objIDs, objIDs + count);
            context->setObjectData(ids_vec, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setBroadcastObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setBroadcastObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void setBroadcastObjectDataDouble(helios::Context* context, unsigned int* objIDs, size_t count, const char* label, double value) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!objIDs || count == 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Object IDs array is null or empty"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            std::vector<uint> ids_vec(objIDs, objIDs + count);
            context->setObjectData(ids_vec, label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setBroadcastObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setBroadcastObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void setBroadcastObjectDataString(helios::Context* context, unsigned int* objIDs, size_t count, const char* label, const char* value) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!objIDs || count == 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Object IDs array is null or empty"); return; }
            if (!label || !value) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or value is null"); return; }
            std::vector<uint> ids_vec(objIDs, objIDs + count);
            std::string str_value(value);
            context->setObjectData(ids_vec, label, str_value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setBroadcastObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setBroadcastObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void setBroadcastObjectDataVec2(helios::Context* context, unsigned int* objIDs, size_t count, const char* label, float x, float y) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!objIDs || count == 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Object IDs array is null or empty"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            std::vector<uint> ids_vec(objIDs, objIDs + count);
            helios::vec2 v(x, y);
            context->setObjectData(ids_vec, label, v);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setBroadcastObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setBroadcastObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void setBroadcastObjectDataVec3(helios::Context* context, unsigned int* objIDs, size_t count, const char* label, float x, float y, float z) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!objIDs || count == 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Object IDs array is null or empty"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            std::vector<uint> ids_vec(objIDs, objIDs + count);
            helios::vec3 v(x, y, z);
            context->setObjectData(ids_vec, label, v);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setBroadcastObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setBroadcastObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void setBroadcastObjectDataVec4(helios::Context* context, unsigned int* objIDs, size_t count, const char* label, float x, float y, float z, float w) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!objIDs || count == 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Object IDs array is null or empty"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            std::vector<uint> ids_vec(objIDs, objIDs + count);
            helios::vec4 v(x, y, z, w);
            context->setObjectData(ids_vec, label, v);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setBroadcastObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setBroadcastObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void setBroadcastObjectDataInt2(helios::Context* context, unsigned int* objIDs, size_t count, const char* label, int x, int y) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!objIDs || count == 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Object IDs array is null or empty"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            std::vector<uint> ids_vec(objIDs, objIDs + count);
            helios::int2 v(x, y);
            context->setObjectData(ids_vec, label, v);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setBroadcastObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setBroadcastObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void setBroadcastObjectDataInt3(helios::Context* context, unsigned int* objIDs, size_t count, const char* label, int x, int y, int z) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!objIDs || count == 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Object IDs array is null or empty"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            std::vector<uint> ids_vec(objIDs, objIDs + count);
            helios::int3 v(x, y, z);
            context->setObjectData(ids_vec, label, v);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setBroadcastObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setBroadcastObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void setBroadcastObjectDataInt4(helios::Context* context, unsigned int* objIDs, size_t count, const char* label, int x, int y, int z, int w) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!objIDs || count == 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Object IDs array is null or empty"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            std::vector<uint> ids_vec(objIDs, objIDs + count);
            helios::int4 v(x, y, z, w);
            context->setObjectData(ids_vec, label, v);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setBroadcastObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setBroadcastObjectData): Unknown error.");
        }
    }

    // --- Getters ---

    PYHELIOS_API int getObjectDataInt(helios::Context* context, unsigned int objID, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return 0; }
            int value;
            context->getObjectData(objID, label, value);
            return value;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getObjectData): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getObjectData): Unknown error.");
            return 0;
        }
    }

    PYHELIOS_API unsigned int getObjectDataUInt(helios::Context* context, unsigned int objID, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return 0; }
            uint value;
            context->getObjectData(objID, label, value);
            return value;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getObjectData): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getObjectData): Unknown error.");
            return 0;
        }
    }

    PYHELIOS_API float getObjectDataFloat(helios::Context* context, unsigned int objID, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0.0f; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return 0.0f; }
            float value;
            context->getObjectData(objID, label, value);
            return value;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getObjectData): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getObjectData): Unknown error.");
            return 0.0f;
        }
    }

    PYHELIOS_API double getObjectDataDouble(helios::Context* context, unsigned int objID, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0.0; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return 0.0; }
            double value;
            context->getObjectData(objID, label, value);
            return value;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getObjectData): ") + e.what());
            return 0.0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getObjectData): Unknown error.");
            return 0.0;
        }
    }

    PYHELIOS_API int getObjectDataString(helios::Context* context, unsigned int objID, const char* label, char* buffer, int buffer_size) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!label || !buffer) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or buffer is null"); return 0; }
            std::string value;
            context->getObjectData(objID, label, value);
            int copy_length = std::min((int)value.length(), buffer_size - 1);
            std::strncpy(buffer, value.c_str(), copy_length);
            buffer[copy_length] = '\0';
            return copy_length;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getObjectData): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getObjectData): Unknown error.");
            return 0;
        }
    }

    PYHELIOS_API void getObjectDataVec2(helios::Context* context, unsigned int objID, const char* label, float* x, float* y) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label || !x || !y) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or output pointers are null"); return; }
            helios::vec2 v;
            context->getObjectData(objID, label, v);
            *x = v.x; *y = v.y;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void getObjectDataVec3(helios::Context* context, unsigned int objID, const char* label, float* x, float* y, float* z) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label || !x || !y || !z) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or output pointers are null"); return; }
            helios::vec3 v;
            context->getObjectData(objID, label, v);
            *x = v.x; *y = v.y; *z = v.z;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void getObjectDataVec4(helios::Context* context, unsigned int objID, const char* label, float* x, float* y, float* z, float* w) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label || !x || !y || !z || !w) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or output pointers are null"); return; }
            helios::vec4 v;
            context->getObjectData(objID, label, v);
            *x = v.x; *y = v.y; *z = v.z; *w = v.w;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void getObjectDataInt2(helios::Context* context, unsigned int objID, const char* label, int* x, int* y) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label || !x || !y) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or output pointers are null"); return; }
            helios::int2 v;
            context->getObjectData(objID, label, v);
            *x = v.x; *y = v.y;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void getObjectDataInt3(helios::Context* context, unsigned int objID, const char* label, int* x, int* y, int* z) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label || !x || !y || !z) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or output pointers are null"); return; }
            helios::int3 v;
            context->getObjectData(objID, label, v);
            *x = v.x; *y = v.y; *z = v.z;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void getObjectDataInt4(helios::Context* context, unsigned int objID, const char* label, int* x, int* y, int* z, int* w) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label || !x || !y || !z || !w) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or output pointers are null"); return; }
            helios::int4 v;
            context->getObjectData(objID, label, v);
            *x = v.x; *y = v.y; *z = v.z; *w = v.w;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getObjectData): Unknown error.");
        }
    }

    // --- Utilities ---

    PYHELIOS_API int getObjectDataType(helios::Context* context, unsigned int objID, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return -1; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return -1; }
            // helios-core 1.3.72+: use the registry-based, label-only overload. The
            // per-object overload is [[deprecated]]; in a well-formed scene the type
            // for a given label is consistent across all objects, so dropping objID
            // gives the same answer without the deprecation warning.
            (void)objID;
            return static_cast<int>(context->getObjectDataType(label));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getObjectDataType): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getObjectDataType): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int getObjectDataSize(helios::Context* context, unsigned int objID, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return 0; }
            return static_cast<int>(context->getObjectDataSize(objID, label));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getObjectDataSize): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getObjectDataSize): Unknown error.");
            return 0;
        }
    }

    PYHELIOS_API bool doesObjectDataExist(helios::Context* context, unsigned int objID, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return false; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return false; }
            return context->doesObjectDataExist(objID, label);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (doesObjectDataExist): ") + e.what());
            return false;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (doesObjectDataExist): Unknown error.");
            return false;
        }
    }

    PYHELIOS_API void clearObjectData(helios::Context* context, unsigned int objID, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->clearObjectData(objID, label);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (clearObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (clearObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void clearObjectDataBatch(helios::Context* context, unsigned int* objIDs, unsigned int count, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!objIDs || count == 0) { return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            std::vector<uint> ids_vec(objIDs, objIDs + count);
            context->clearObjectData(ids_vec, label);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (clearObjectDataBatch): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (clearObjectDataBatch): Unknown error.");
        }
    }

    PYHELIOS_API const char** listObjectData(helios::Context* context, unsigned int objID, unsigned int* count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); if (count) *count = 0; return nullptr; }
            if (!count) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count output parameter is null"); return nullptr; }
            static thread_local std::vector<std::string> static_strings;
            static thread_local std::vector<const char*> static_ptrs;
            static_strings = context->listObjectData(objID);
            static_ptrs.clear();
            static_ptrs.reserve(static_strings.size());
            for (auto& s : static_strings) { static_ptrs.push_back(s.c_str()); }
            *count = static_strings.size();
            return static_ptrs.empty() ? nullptr : static_ptrs.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (listObjectData): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (listObjectData): Unknown error.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API const char** listAllObjectDataLabels(helios::Context* context, unsigned int* count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); if (count) *count = 0; return nullptr; }
            if (!count) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count output parameter is null"); return nullptr; }
            static thread_local std::vector<std::string> static_strings;
            static thread_local std::vector<const char*> static_ptrs;
            static_strings = context->listAllObjectDataLabels();
            static_ptrs.clear();
            static_ptrs.reserve(static_strings.size());
            for (auto& s : static_strings) { static_ptrs.push_back(s.c_str()); }
            *count = static_strings.size();
            return static_ptrs.empty() ? nullptr : static_ptrs.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (listAllObjectDataLabels): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (listAllObjectDataLabels): Unknown error.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API void duplicateObjectData(helios::Context* context, unsigned int objID, const char* old_label, const char* new_label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!old_label || !new_label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->duplicateObjectData(objID, old_label, new_label);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (duplicateObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (duplicateObjectData): Unknown error.");
        }
    }

    PYHELIOS_API void renameObjectData(helios::Context* context, unsigned int objID, const char* old_label, const char* new_label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!old_label || !new_label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->renameObjectData(objID, old_label, new_label);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (renameObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (renameObjectData): Unknown error.");
        }
    }

    // --- Filters ---

    PYHELIOS_API unsigned int* filterObjectsByDataFloat(helios::Context* context, unsigned int* objIDs, unsigned int count, const char* label, float value, const char* comparator, unsigned int* result_count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); if (result_count) *result_count = 0; return nullptr; }
            if (!objIDs || count == 0 || !label || !comparator) { if (result_count) *result_count = 0; return nullptr; }
            std::vector<uint> ids_vec(objIDs, objIDs + count);
            static thread_local std::vector<unsigned int> static_result;
            static_result = context->filterObjectsByData(ids_vec, std::string(label), value, std::string(comparator));
            *result_count = static_result.size();
            return static_result.empty() ? nullptr : static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (filterObjectsByData): ") + e.what());
            if (result_count) *result_count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (filterObjectsByData): Unknown error.");
            if (result_count) *result_count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* filterObjectsByDataDouble(helios::Context* context, unsigned int* objIDs, unsigned int count, const char* label, double value, const char* comparator, unsigned int* result_count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); if (result_count) *result_count = 0; return nullptr; }
            if (!objIDs || count == 0 || !label || !comparator) { if (result_count) *result_count = 0; return nullptr; }
            std::vector<uint> ids_vec(objIDs, objIDs + count);
            static thread_local std::vector<unsigned int> static_result;
            static_result = context->filterObjectsByData(ids_vec, std::string(label), value, std::string(comparator));
            *result_count = static_result.size();
            return static_result.empty() ? nullptr : static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (filterObjectsByData): ") + e.what());
            if (result_count) *result_count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (filterObjectsByData): Unknown error.");
            if (result_count) *result_count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* filterObjectsByDataInt(helios::Context* context, unsigned int* objIDs, unsigned int count, const char* label, int value, const char* comparator, unsigned int* result_count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); if (result_count) *result_count = 0; return nullptr; }
            if (!objIDs || count == 0 || !label || !comparator) { if (result_count) *result_count = 0; return nullptr; }
            std::vector<uint> ids_vec(objIDs, objIDs + count);
            static thread_local std::vector<unsigned int> static_result;
            static_result = context->filterObjectsByData(ids_vec, std::string(label), value, std::string(comparator));
            *result_count = static_result.size();
            return static_result.empty() ? nullptr : static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (filterObjectsByData): ") + e.what());
            if (result_count) *result_count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (filterObjectsByData): Unknown error.");
            if (result_count) *result_count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* filterObjectsByDataUInt(helios::Context* context, unsigned int* objIDs, unsigned int count, const char* label, unsigned int value, const char* comparator, unsigned int* result_count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); if (result_count) *result_count = 0; return nullptr; }
            if (!objIDs || count == 0 || !label || !comparator) { if (result_count) *result_count = 0; return nullptr; }
            std::vector<uint> ids_vec(objIDs, objIDs + count);
            static thread_local std::vector<unsigned int> static_result;
            static_result = context->filterObjectsByData(ids_vec, std::string(label), value, std::string(comparator));
            *result_count = static_result.size();
            return static_result.empty() ? nullptr : static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (filterObjectsByData): ") + e.what());
            if (result_count) *result_count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (filterObjectsByData): Unknown error.");
            if (result_count) *result_count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* filterObjectsByDataString(helios::Context* context, unsigned int* objIDs, unsigned int count, const char* label, const char* value, unsigned int* result_count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); if (result_count) *result_count = 0; return nullptr; }
            if (!objIDs || count == 0 || !label || !value) { if (result_count) *result_count = 0; return nullptr; }
            std::vector<uint> ids_vec(objIDs, objIDs + count);
            static thread_local std::vector<unsigned int> static_result;
            static_result = context->filterObjectsByData(ids_vec, std::string(label), std::string(value));
            *result_count = static_result.size();
            return static_result.empty() ? nullptr : static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (filterObjectsByData): ") + e.what());
            if (result_count) *result_count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (filterObjectsByData): Unknown error.");
            if (result_count) *result_count = 0;
            return nullptr;
        }
    }

    // ==================== Global Data Functions ====================

    // --- Setters ---

    PYHELIOS_API void setGlobalDataInt(helios::Context* context, const char* label, int value) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->setGlobalData(label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setGlobalData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setGlobalData): Unknown error.");
        }
    }

    PYHELIOS_API void setGlobalDataUInt(helios::Context* context, const char* label, unsigned int value) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->setGlobalData(label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setGlobalData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setGlobalData): Unknown error.");
        }
    }

    PYHELIOS_API void setGlobalDataFloat(helios::Context* context, const char* label, float value) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->setGlobalData(label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setGlobalData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setGlobalData): Unknown error.");
        }
    }

    PYHELIOS_API void setGlobalDataDouble(helios::Context* context, const char* label, double value) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->setGlobalData(label, value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setGlobalData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setGlobalData): Unknown error.");
        }
    }

    PYHELIOS_API void setGlobalDataString(helios::Context* context, const char* label, const char* value) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label || !value) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or value is null"); return; }
            std::string str_value(value);
            context->setGlobalData(label, str_value);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setGlobalData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setGlobalData): Unknown error.");
        }
    }

    PYHELIOS_API void setGlobalDataVec2(helios::Context* context, const char* label, float x, float y) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            helios::vec2 v(x, y);
            context->setGlobalData(label, v);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setGlobalData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setGlobalData): Unknown error.");
        }
    }

    PYHELIOS_API void setGlobalDataVec3(helios::Context* context, const char* label, float x, float y, float z) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            helios::vec3 v(x, y, z);
            context->setGlobalData(label, v);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setGlobalData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setGlobalData): Unknown error.");
        }
    }

    PYHELIOS_API void setGlobalDataVec4(helios::Context* context, const char* label, float x, float y, float z, float w) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            helios::vec4 v(x, y, z, w);
            context->setGlobalData(label, v);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setGlobalData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setGlobalData): Unknown error.");
        }
    }

    PYHELIOS_API void setGlobalDataInt2(helios::Context* context, const char* label, int x, int y) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            helios::int2 v(x, y);
            context->setGlobalData(label, v);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setGlobalData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setGlobalData): Unknown error.");
        }
    }

    PYHELIOS_API void setGlobalDataInt3(helios::Context* context, const char* label, int x, int y, int z) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            helios::int3 v(x, y, z);
            context->setGlobalData(label, v);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setGlobalData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setGlobalData): Unknown error.");
        }
    }

    PYHELIOS_API void setGlobalDataInt4(helios::Context* context, const char* label, int x, int y, int z, int w) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            helios::int4 v(x, y, z, w);
            context->setGlobalData(label, v);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setGlobalData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setGlobalData): Unknown error.");
        }
    }

    // --- Getters ---

    PYHELIOS_API int getGlobalDataInt(helios::Context* context, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return 0; }
            int value;
            context->getGlobalData(label, value);
            return value;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getGlobalData): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getGlobalData): Unknown error.");
            return 0;
        }
    }

    PYHELIOS_API unsigned int getGlobalDataUInt(helios::Context* context, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return 0; }
            uint value;
            context->getGlobalData(label, value);
            return value;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getGlobalData): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getGlobalData): Unknown error.");
            return 0;
        }
    }

    PYHELIOS_API float getGlobalDataFloat(helios::Context* context, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0.0f; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return 0.0f; }
            float value;
            context->getGlobalData(label, value);
            return value;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getGlobalData): ") + e.what());
            return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getGlobalData): Unknown error.");
            return 0.0f;
        }
    }

    PYHELIOS_API double getGlobalDataDouble(helios::Context* context, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0.0; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return 0.0; }
            double value;
            context->getGlobalData(label, value);
            return value;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getGlobalData): ") + e.what());
            return 0.0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getGlobalData): Unknown error.");
            return 0.0;
        }
    }

    PYHELIOS_API int getGlobalDataString(helios::Context* context, const char* label, char* buffer, int buffer_size) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!label || !buffer) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or buffer is null"); return 0; }
            std::string value;
            context->getGlobalData(label, value);
            int copy_length = std::min((int)value.length(), buffer_size - 1);
            std::strncpy(buffer, value.c_str(), copy_length);
            buffer[copy_length] = '\0';
            return copy_length;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getGlobalData): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getGlobalData): Unknown error.");
            return 0;
        }
    }

    PYHELIOS_API void getGlobalDataVec2(helios::Context* context, const char* label, float* x, float* y) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label || !x || !y) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or output pointers are null"); return; }
            helios::vec2 v; context->getGlobalData(label, v); *x = v.x; *y = v.y;
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getGlobalData): ") + e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getGlobalData): Unknown error."); }
    }

    PYHELIOS_API void getGlobalDataVec3(helios::Context* context, const char* label, float* x, float* y, float* z) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label || !x || !y || !z) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or output pointers are null"); return; }
            helios::vec3 v; context->getGlobalData(label, v); *x = v.x; *y = v.y; *z = v.z;
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getGlobalData): ") + e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getGlobalData): Unknown error."); }
    }

    PYHELIOS_API void getGlobalDataVec4(helios::Context* context, const char* label, float* x, float* y, float* z, float* w) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label || !x || !y || !z || !w) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or output pointers are null"); return; }
            helios::vec4 v; context->getGlobalData(label, v); *x = v.x; *y = v.y; *z = v.z; *w = v.w;
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getGlobalData): ") + e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getGlobalData): Unknown error."); }
    }

    PYHELIOS_API void getGlobalDataInt2(helios::Context* context, const char* label, int* x, int* y) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label || !x || !y) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or output pointers are null"); return; }
            helios::int2 v; context->getGlobalData(label, v); *x = v.x; *y = v.y;
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getGlobalData): ") + e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getGlobalData): Unknown error."); }
    }

    PYHELIOS_API void getGlobalDataInt3(helios::Context* context, const char* label, int* x, int* y, int* z) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label || !x || !y || !z) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or output pointers are null"); return; }
            helios::int3 v; context->getGlobalData(label, v); *x = v.x; *y = v.y; *z = v.z;
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getGlobalData): ") + e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getGlobalData): Unknown error."); }
    }

    PYHELIOS_API void getGlobalDataInt4(helios::Context* context, const char* label, int* x, int* y, int* z, int* w) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label || !x || !y || !z || !w) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or output pointers are null"); return; }
            helios::int4 v; context->getGlobalData(label, v); *x = v.x; *y = v.y; *z = v.z; *w = v.w;
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getGlobalData): ") + e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getGlobalData): Unknown error."); }
    }

    // --- Utilities ---

    PYHELIOS_API int getGlobalDataType(helios::Context* context, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return -1; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return -1; }
            return static_cast<int>(context->getGlobalDataType(label));
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getGlobalDataType): ") + e.what()); return -1; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getGlobalDataType): Unknown error."); return -1; }
    }

    PYHELIOS_API int getGlobalDataSize(helios::Context* context, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return 0; }
            return static_cast<int>(context->getGlobalDataSize(label));
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getGlobalDataSize): ") + e.what()); return 0; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getGlobalDataSize): Unknown error."); return 0; }
    }

    PYHELIOS_API bool doesGlobalDataExist(helios::Context* context, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return false; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return false; }
            return context->doesGlobalDataExist(label);
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (doesGlobalDataExist): ") + e.what()); return false; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (doesGlobalDataExist): Unknown error."); return false; }
    }

    PYHELIOS_API void clearGlobalData(helios::Context* context, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->clearGlobalData(label);
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (clearGlobalData): ") + e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (clearGlobalData): Unknown error."); }
    }

    PYHELIOS_API void renameGlobalData(helios::Context* context, const char* old_label, const char* new_label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!old_label || !new_label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->renameGlobalData(old_label, new_label);
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (renameGlobalData): ") + e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (renameGlobalData): Unknown error."); }
    }

    PYHELIOS_API void duplicateGlobalData(helios::Context* context, const char* old_label, const char* new_label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!old_label || !new_label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->duplicateGlobalData(old_label, new_label);
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (duplicateGlobalData): ") + e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (duplicateGlobalData): Unknown error."); }
    }

    PYHELIOS_API const char** listGlobalData(helios::Context* context, unsigned int* count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); if (count) *count = 0; return nullptr; }
            if (!count) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count output parameter is null"); return nullptr; }
            static thread_local std::vector<std::string> static_strings;
            static thread_local std::vector<const char*> static_ptrs;
            static_strings = context->listGlobalData();
            static_ptrs.clear();
            static_ptrs.reserve(static_strings.size());
            for (auto& s : static_strings) { static_ptrs.push_back(s.c_str()); }
            *count = static_strings.size();
            return static_ptrs.empty() ? nullptr : static_ptrs.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (listGlobalData): ") + e.what());
            if (count) *count = 0; return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (listGlobalData): Unknown error.");
            if (count) *count = 0; return nullptr;
        }
    }

    // --- Increment ---

    PYHELIOS_API void incrementGlobalDataInt(helios::Context* context, const char* label, int increment) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->incrementGlobalData(label, increment);
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (incrementGlobalData): ") + e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (incrementGlobalData): Unknown error."); }
    }

    PYHELIOS_API void incrementGlobalDataUInt(helios::Context* context, const char* label, unsigned int increment) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->incrementGlobalData(label, increment);
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (incrementGlobalData): ") + e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (incrementGlobalData): Unknown error."); }
    }

    PYHELIOS_API void incrementGlobalDataFloat(helios::Context* context, const char* label, float increment) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->incrementGlobalData(label, increment);
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (incrementGlobalData): ") + e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (incrementGlobalData): Unknown error."); }
    }

    PYHELIOS_API void incrementGlobalDataDouble(helios::Context* context, const char* label, double increment) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->incrementGlobalData(label, increment);
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (incrementGlobalData): ") + e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (incrementGlobalData): Unknown error."); }
    }

    // ==================== Primitive Data Statistics & Filtering ====================

    #define STATS_PREAMBLE \
        clearError(); \
        if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; } \
        if (!uuids || count == 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs null or empty"); return 0; } \
        if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return 0; } \
        std::vector<uint> uuids_vec(uuids, uuids + count);

    PYHELIOS_API float calculatePrimitiveDataMeanFloat(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label) {
        STATS_PREAMBLE
        try { float v; context->calculatePrimitiveDataMean(uuids_vec, std::string(label), v); return v; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR: ") + e.what()); return 0; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "Unknown error"); return 0; }
    }

    PYHELIOS_API double calculatePrimitiveDataMeanDouble(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!uuids || count == 0 || !label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Invalid parameters"); return 0; }
            std::vector<uint> uuids_vec(uuids, uuids + count);
            double v; context->calculatePrimitiveDataMean(uuids_vec, std::string(label), v); return v;
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR: ") + e.what()); return 0; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "Unknown error"); return 0; }
    }

    PYHELIOS_API void calculatePrimitiveDataMeanVec2(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label, float* x, float* y) {
        clearError();
        try {
            if (!context || !uuids || count == 0 || !label || !x || !y) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Invalid parameters"); return; }
            std::vector<uint> uuids_vec(uuids, uuids + count);
            helios::vec2 v; context->calculatePrimitiveDataMean(uuids_vec, std::string(label), v); *x = v.x; *y = v.y;
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR: ") + e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "Unknown error"); }
    }

    PYHELIOS_API void calculatePrimitiveDataMeanVec3(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label, float* x, float* y, float* z) {
        clearError();
        try {
            if (!context || !uuids || count == 0 || !label || !x || !y || !z) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Invalid parameters"); return; }
            std::vector<uint> uuids_vec(uuids, uuids + count);
            helios::vec3 v; context->calculatePrimitiveDataMean(uuids_vec, std::string(label), v); *x = v.x; *y = v.y; *z = v.z;
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR: ") + e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "Unknown error"); }
    }

    PYHELIOS_API void calculatePrimitiveDataMeanVec4(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label, float* x, float* y, float* z, float* w) {
        clearError();
        try {
            if (!context || !uuids || count == 0 || !label || !x || !y || !z || !w) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Invalid parameters"); return; }
            std::vector<uint> uuids_vec(uuids, uuids + count);
            helios::vec4 v; context->calculatePrimitiveDataMean(uuids_vec, std::string(label), v); *x = v.x; *y = v.y; *z = v.z; *w = v.w;
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR: ") + e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "Unknown error"); }
    }

    PYHELIOS_API float calculatePrimitiveDataAreaWeightedMeanFloat(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label) {
        STATS_PREAMBLE
        try { float v; context->calculatePrimitiveDataAreaWeightedMean(uuids_vec, std::string(label), v); return v; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR: ") + e.what()); return 0; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "Unknown error"); return 0; }
    }

    PYHELIOS_API double calculatePrimitiveDataAreaWeightedMeanDouble(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label) {
        clearError();
        try {
            if (!context || !uuids || count == 0 || !label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Invalid parameters"); return 0; }
            std::vector<uint> uuids_vec(uuids, uuids + count);
            double v; context->calculatePrimitiveDataAreaWeightedMean(uuids_vec, std::string(label), v); return v;
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR: ") + e.what()); return 0; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "Unknown error"); return 0; }
    }

    PYHELIOS_API float calculatePrimitiveDataSumFloat(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label) {
        STATS_PREAMBLE
        try { float v; context->calculatePrimitiveDataSum(uuids_vec, std::string(label), v); return v; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR: ") + e.what()); return 0; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "Unknown error"); return 0; }
    }

    PYHELIOS_API double calculatePrimitiveDataSumDouble(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label) {
        clearError();
        try {
            if (!context || !uuids || count == 0 || !label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Invalid parameters"); return 0; }
            std::vector<uint> uuids_vec(uuids, uuids + count);
            double v; context->calculatePrimitiveDataSum(uuids_vec, std::string(label), v); return v;
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR: ") + e.what()); return 0; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "Unknown error"); return 0; }
    }

    PYHELIOS_API float calculatePrimitiveDataAreaWeightedSumFloat(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label) {
        STATS_PREAMBLE
        try { float v; context->calculatePrimitiveDataAreaWeightedSum(uuids_vec, std::string(label), v); return v; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR: ") + e.what()); return 0; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "Unknown error"); return 0; }
    }

    PYHELIOS_API double calculatePrimitiveDataAreaWeightedSumDouble(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label) {
        clearError();
        try {
            if (!context || !uuids || count == 0 || !label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Invalid parameters"); return 0; }
            std::vector<uint> uuids_vec(uuids, uuids + count);
            double v; context->calculatePrimitiveDataAreaWeightedSum(uuids_vec, std::string(label), v); return v;
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR: ") + e.what()); return 0; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "Unknown error"); return 0; }
    }

    #undef STATS_PREAMBLE

    // Scale & Increment

    PYHELIOS_API void scalePrimitiveDataWithUUIDs(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label, float factor) {
        clearError();
        try {
            if (!context || !uuids || count == 0 || !label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Invalid parameters"); return; }
            std::vector<uint> uuids_vec(uuids, uuids + count);
            context->scalePrimitiveData(uuids_vec, std::string(label), factor);
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR: ") + e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "Unknown error"); }
    }

    PYHELIOS_API void scalePrimitiveDataAll(helios::Context* context, const char* label, float factor) {
        clearError();
        try {
            if (!context || !label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Invalid parameters"); return; }
            context->scalePrimitiveData(std::string(label), factor);
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR: ") + e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "Unknown error"); }
    }

    PYHELIOS_API void incrementPrimitiveDataInt(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label, int increment) {
        clearError();
        try {
            if (!context || !uuids || count == 0 || !label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Invalid parameters"); return; }
            std::vector<uint> uuids_vec(uuids, uuids + count);
            context->incrementPrimitiveData(uuids_vec, label, increment);
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR: ") + e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "Unknown error"); }
    }

    PYHELIOS_API void incrementPrimitiveDataFloat(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label, float increment) {
        clearError();
        try {
            if (!context || !uuids || count == 0 || !label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Invalid parameters"); return; }
            std::vector<uint> uuids_vec(uuids, uuids + count);
            context->incrementPrimitiveData(uuids_vec, label, increment);
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR: ") + e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "Unknown error"); }
    }

    // Aggregate

    PYHELIOS_API void aggregatePrimitiveDataSum(helios::Context* context, unsigned int* uuids, unsigned int count, const char** labels, unsigned int label_count, const char* result_label) {
        clearError();
        try {
            if (!context || !uuids || count == 0 || !labels || label_count == 0 || !result_label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Invalid parameters"); return; }
            std::vector<uint> uuids_vec(uuids, uuids + count);
            std::vector<std::string> labels_vec;
            labels_vec.reserve(label_count);
            for (unsigned int i = 0; i < label_count; i++) { labels_vec.emplace_back(labels[i]); }
            context->aggregatePrimitiveDataSum(uuids_vec, labels_vec, std::string(result_label));
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR: ") + e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "Unknown error"); }
    }

    PYHELIOS_API void aggregatePrimitiveDataProduct(helios::Context* context, unsigned int* uuids, unsigned int count, const char** labels, unsigned int label_count, const char* result_label) {
        clearError();
        try {
            if (!context || !uuids || count == 0 || !labels || label_count == 0 || !result_label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Invalid parameters"); return; }
            std::vector<uint> uuids_vec(uuids, uuids + count);
            std::vector<std::string> labels_vec;
            labels_vec.reserve(label_count);
            for (unsigned int i = 0; i < label_count; i++) { labels_vec.emplace_back(labels[i]); }
            context->aggregatePrimitiveDataProduct(uuids_vec, labels_vec, std::string(result_label));
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR: ") + e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "Unknown error"); }
    }

    // Surface area

    PYHELIOS_API float sumPrimitiveSurfaceArea(helios::Context* context, unsigned int* uuids, unsigned int count) {
        clearError();
        try {
            if (!context || !uuids || count == 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Invalid parameters"); return 0; }
            std::vector<uint> uuids_vec(uuids, uuids + count);
            return context->sumPrimitiveSurfaceArea(uuids_vec);
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR: ") + e.what()); return 0; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "Unknown error"); return 0; }
    }

    // Filter

    PYHELIOS_API unsigned int* filterPrimitivesByDataFloat(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label, float value, const char* comparator, unsigned int* result_count) {
        clearError();
        try {
            if (!context || !uuids || count == 0 || !label || !comparator) { if (result_count) *result_count = 0; return nullptr; }
            std::vector<uint> uuids_vec(uuids, uuids + count);
            static thread_local std::vector<unsigned int> static_result;
            static_result = context->filterPrimitivesByData(uuids_vec, std::string(label), value, std::string(comparator));
            *result_count = static_result.size();
            return static_result.empty() ? nullptr : static_result.data();
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR: ") + e.what()); if (result_count) *result_count = 0; return nullptr; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "Unknown error"); if (result_count) *result_count = 0; return nullptr; }
    }

    PYHELIOS_API unsigned int* filterPrimitivesByDataInt(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label, int value, const char* comparator, unsigned int* result_count) {
        clearError();
        try {
            if (!context || !uuids || count == 0 || !label || !comparator) { if (result_count) *result_count = 0; return nullptr; }
            std::vector<uint> uuids_vec(uuids, uuids + count);
            static thread_local std::vector<unsigned int> static_result;
            static_result = context->filterPrimitivesByData(uuids_vec, std::string(label), value, std::string(comparator));
            *result_count = static_result.size();
            return static_result.empty() ? nullptr : static_result.data();
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR: ") + e.what()); if (result_count) *result_count = 0; return nullptr; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "Unknown error"); if (result_count) *result_count = 0; return nullptr; }
    }

    PYHELIOS_API unsigned int* filterPrimitivesByDataString(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label, const char* value, unsigned int* result_count) {
        clearError();
        try {
            if (!context || !uuids || count == 0 || !label || !value) { if (result_count) *result_count = 0; return nullptr; }
            std::vector<uint> uuids_vec(uuids, uuids + count);
            static thread_local std::vector<unsigned int> static_result;
            static_result = context->filterPrimitivesByData(uuids_vec, std::string(label), std::string(value));
            *result_count = static_result.size();
            return static_result.empty() ? nullptr : static_result.data();
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR: ") + e.what()); if (result_count) *result_count = 0; return nullptr; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "Unknown error"); if (result_count) *result_count = 0; return nullptr; }
    }

    // ==================== Object Geometry Queries ====================

    PYHELIOS_API unsigned int getObjectType(helios::Context* context, unsigned int objID) {
        try {
            clearError();
            return static_cast<unsigned int>(context->getObjectType(objID));
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getObjectType): Unknown error."); return 0;
        }
    }

    PYHELIOS_API float* getObjectCenter(helios::Context* context, unsigned int objID) {
        try {
            clearError();
            helios::vec3 c = context->getObjectCenter(objID);
            static float result[3];
            result[0] = c.x; result[1] = c.y; result[2] = c.z;
            return result;
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what());
            static float err[3] = {0.0f, 0.0f, 0.0f}; return err;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            static float err[3] = {0.0f, 0.0f, 0.0f}; return err;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getObjectCenter): Unknown error.");
            static float err[3] = {0.0f, 0.0f, 0.0f}; return err;
        }
    }

    PYHELIOS_API void getObjectBoundingBox(helios::Context* context, unsigned int objID, float* min_corner, float* max_corner) {
        try {
            clearError();
            if (!min_corner || !max_corner) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output corner pointer is null"); return; }
            helios::vec3 mn, mx;
            context->getObjectBoundingBox(objID, mn, mx);
            min_corner[0] = mn.x; min_corner[1] = mn.y; min_corner[2] = mn.z;
            max_corner[0] = mx.x; max_corner[1] = mx.y; max_corner[2] = mx.z;
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getObjectBoundingBox): Unknown error."); }
    }

    PYHELIOS_API void getObjectBoundingBox_batch(helios::Context* context, unsigned int* objIDs, unsigned int count, float* min_corner, float* max_corner) {
        try {
            clearError();
            if (!min_corner || !max_corner) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output corner pointer is null"); return; }
            std::vector<unsigned int> ids(objIDs, objIDs + count);
            helios::vec3 mn, mx;
            context->getObjectBoundingBox(ids, mn, mx);
            min_corner[0] = mn.x; min_corner[1] = mn.y; min_corner[2] = mn.z;
            max_corner[0] = mx.x; max_corner[1] = mx.y; max_corner[2] = mx.z;
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getObjectBoundingBox_batch): Unknown error."); }
    }

    PYHELIOS_API unsigned int* getObjectPrimitiveUUIDs_batch(helios::Context* context, unsigned int* objIDs, unsigned int count, unsigned int* size) {
        try {
            clearError();
            std::vector<unsigned int> ids(objIDs, objIDs + count);
            static thread_local std::vector<unsigned int> buf;
            buf = context->getObjectPrimitiveUUIDs(ids);
            *size = buf.size();
            return buf.empty() ? nullptr : buf.data();
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); if (size) *size = 0; return nullptr; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); if (size) *size = 0; return nullptr; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getObjectPrimitiveUUIDs_batch): Unknown error."); if (size) *size = 0; return nullptr; }
    }

    PYHELIOS_API unsigned int* getObjectPrimitiveUUIDs_nested(helios::Context* context, unsigned int* flat_objIDs, unsigned int* inner_counts, unsigned int outer_count, unsigned int* size) {
        try {
            clearError();
            std::vector<std::vector<unsigned int>> nested;
            nested.reserve(outer_count);
            unsigned int offset = 0;
            for (unsigned int i = 0; i < outer_count; ++i) {
                unsigned int ic = inner_counts[i];
                nested.emplace_back(flat_objIDs + offset, flat_objIDs + offset + ic);
                offset += ic;
            }
            static thread_local std::vector<unsigned int> buf;
            buf = context->getObjectPrimitiveUUIDs(nested);
            *size = buf.size();
            return buf.empty() ? nullptr : buf.data();
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); if (size) *size = 0; return nullptr; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); if (size) *size = 0; return nullptr; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getObjectPrimitiveUUIDs_nested): Unknown error."); if (size) *size = 0; return nullptr; }
    }

    // ---- Tile ----
    PYHELIOS_API float getTileObjectAreaRatio(helios::Context* context, unsigned int objID) {
        try { clearError(); return context->getTileObjectAreaRatio(objID); }
        catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); return 0.0f; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0.0f; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getTileObjectAreaRatio): Unknown error."); return 0.0f; }
    }

    PYHELIOS_API float* getTileObjectAreaRatio_batch(helios::Context* context, unsigned int* objIDs, unsigned int count, unsigned int* size) {
        try {
            clearError();
            std::vector<unsigned int> ids(objIDs, objIDs + count);
            static thread_local std::vector<float> buf;
            buf = context->getTileObjectAreaRatio(ids);
            *size = buf.size();
            return buf.empty() ? nullptr : buf.data();
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); if (size) *size = 0; return nullptr; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); if (size) *size = 0; return nullptr; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getTileObjectAreaRatio_batch): Unknown error."); if (size) *size = 0; return nullptr; }
    }

    PYHELIOS_API float* getTileObjectCenter(helios::Context* context, unsigned int objID) {
        try {
            clearError();
            helios::vec3 v = context->getTileObjectCenter(objID);
            static float r[3]; r[0]=v.x; r[1]=v.y; r[2]=v.z; return r;
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getTileObjectCenter): Unknown error."); static float e_r[3]={0,0,0}; return e_r; }
    }

    PYHELIOS_API float* getTileObjectSize(helios::Context* context, unsigned int objID) {
        try {
            clearError();
            helios::vec2 v = context->getTileObjectSize(objID);
            static float r[2]; r[0]=v.x; r[1]=v.y; return r;
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); static float e_r[2]={0,0}; return e_r; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); static float e_r[2]={0,0}; return e_r; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getTileObjectSize): Unknown error."); static float e_r[2]={0,0}; return e_r; }
    }

    PYHELIOS_API int* getTileObjectSubdivisionCount(helios::Context* context, unsigned int objID) {
        try {
            clearError();
            helios::int2 v = context->getTileObjectSubdivisionCount(objID);
            static int r[2]; r[0]=v.x; r[1]=v.y; return r;
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); static int e_r[2]={0,0}; return e_r; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); static int e_r[2]={0,0}; return e_r; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getTileObjectSubdivisionCount): Unknown error."); static int e_r[2]={0,0}; return e_r; }
    }

    PYHELIOS_API float* getTileObjectNormal(helios::Context* context, unsigned int objID) {
        try {
            clearError();
            helios::vec3 v = context->getTileObjectNormal(objID);
            static float r[3]; r[0]=v.x; r[1]=v.y; r[2]=v.z; return r;
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getTileObjectNormal): Unknown error."); static float e_r[3]={0,0,0}; return e_r; }
    }

    PYHELIOS_API float* getTileObjectTextureUV(helios::Context* context, unsigned int objID, unsigned int* size) {
        try {
            clearError();
            std::vector<helios::vec2> uvs = context->getTileObjectTextureUV(objID);
            static thread_local std::vector<float> buf;
            buf.clear(); buf.reserve(uvs.size()*2);
            for (const auto& u : uvs) { buf.push_back(u.x); buf.push_back(u.y); }
            *size = buf.size();
            return buf.empty() ? nullptr : buf.data();
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); if (size) *size = 0; return nullptr; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); if (size) *size = 0; return nullptr; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getTileObjectTextureUV): Unknown error."); if (size) *size = 0; return nullptr; }
    }

    PYHELIOS_API float* getTileObjectVertices(helios::Context* context, unsigned int objID, unsigned int* size) {
        try {
            clearError();
            std::vector<helios::vec3> vs = context->getTileObjectVertices(objID);
            static thread_local std::vector<float> buf;
            buf.clear(); buf.reserve(vs.size()*3);
            for (const auto& v : vs) { buf.push_back(v.x); buf.push_back(v.y); buf.push_back(v.z); }
            *size = buf.size();
            return buf.empty() ? nullptr : buf.data();
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); if (size) *size = 0; return nullptr; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); if (size) *size = 0; return nullptr; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getTileObjectVertices): Unknown error."); if (size) *size = 0; return nullptr; }
    }

    // ---- Sphere ----
    PYHELIOS_API float* getSphereObjectCenter(helios::Context* context, unsigned int objID) {
        try {
            clearError();
            helios::vec3 v = context->getSphereObjectCenter(objID);
            static float r[3]; r[0]=v.x; r[1]=v.y; r[2]=v.z; return r;
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getSphereObjectCenter): Unknown error."); static float e_r[3]={0,0,0}; return e_r; }
    }

    PYHELIOS_API float* getSphereObjectRadius(helios::Context* context, unsigned int objID) {
        try {
            clearError();
            helios::vec3 v = context->getSphereObjectRadius(objID);
            static float r[3]; r[0]=v.x; r[1]=v.y; r[2]=v.z; return r;
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getSphereObjectRadius): Unknown error."); static float e_r[3]={0,0,0}; return e_r; }
    }

    PYHELIOS_API unsigned int getSphereObjectSubdivisionCount(helios::Context* context, unsigned int objID) {
        try { clearError(); return context->getSphereObjectSubdivisionCount(objID); }
        catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); return 0; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getSphereObjectSubdivisionCount): Unknown error."); return 0; }
    }

    PYHELIOS_API float getSphereObjectVolume(helios::Context* context, unsigned int objID) {
        try { clearError(); return context->getSphereObjectVolume(objID); }
        catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); return 0.0f; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0.0f; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getSphereObjectVolume): Unknown error."); return 0.0f; }
    }

    // ---- Box ----
    PYHELIOS_API float* getBoxObjectCenter(helios::Context* context, unsigned int objID) {
        try {
            clearError();
            helios::vec3 v = context->getBoxObjectCenter(objID);
            static float r[3]; r[0]=v.x; r[1]=v.y; r[2]=v.z; return r;
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getBoxObjectCenter): Unknown error."); static float e_r[3]={0,0,0}; return e_r; }
    }

    PYHELIOS_API float* getBoxObjectSize(helios::Context* context, unsigned int objID) {
        try {
            clearError();
            helios::vec3 v = context->getBoxObjectSize(objID);
            static float r[3]; r[0]=v.x; r[1]=v.y; r[2]=v.z; return r;
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getBoxObjectSize): Unknown error."); static float e_r[3]={0,0,0}; return e_r; }
    }

    PYHELIOS_API int* getBoxObjectSubdivisionCount(helios::Context* context, unsigned int objID) {
        try {
            clearError();
            helios::int3 v = context->getBoxObjectSubdivisionCount(objID);
            static int r[3]; r[0]=v.x; r[1]=v.y; r[2]=v.z; return r;
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); static int e_r[3]={0,0,0}; return e_r; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); static int e_r[3]={0,0,0}; return e_r; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getBoxObjectSubdivisionCount): Unknown error."); static int e_r[3]={0,0,0}; return e_r; }
    }

    PYHELIOS_API float getBoxObjectVolume(helios::Context* context, unsigned int objID) {
        try { clearError(); return context->getBoxObjectVolume(objID); }
        catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); return 0.0f; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0.0f; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getBoxObjectVolume): Unknown error."); return 0.0f; }
    }

    // ---- Disk ----
    PYHELIOS_API float* getDiskObjectCenter(helios::Context* context, unsigned int objID) {
        try {
            clearError();
            helios::vec3 v = context->getDiskObjectCenter(objID);
            static float r[3]; r[0]=v.x; r[1]=v.y; r[2]=v.z; return r;
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getDiskObjectCenter): Unknown error."); static float e_r[3]={0,0,0}; return e_r; }
    }

    PYHELIOS_API float* getDiskObjectSize(helios::Context* context, unsigned int objID) {
        try {
            clearError();
            helios::vec2 v = context->getDiskObjectSize(objID);
            static float r[2]; r[0]=v.x; r[1]=v.y; return r;
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); static float e_r[2]={0,0}; return e_r; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); static float e_r[2]={0,0}; return e_r; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getDiskObjectSize): Unknown error."); static float e_r[2]={0,0}; return e_r; }
    }

    PYHELIOS_API unsigned int getDiskObjectSubdivisionCount(helios::Context* context, unsigned int objID) {
        try { clearError(); return context->getDiskObjectSubdivisionCount(objID); }
        catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); return 0; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getDiskObjectSubdivisionCount): Unknown error."); return 0; }
    }

    // ---- Tube ----
    PYHELIOS_API unsigned int getTubeObjectSubdivisionCount(helios::Context* context, unsigned int objID) {
        try { clearError(); return context->getTubeObjectSubdivisionCount(objID); }
        catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); return 0; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getTubeObjectSubdivisionCount): Unknown error."); return 0; }
    }

    PYHELIOS_API unsigned int getTubeObjectNodeCount(helios::Context* context, unsigned int objID) {
        try { clearError(); return context->getTubeObjectNodeCount(objID); }
        catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); return 0; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getTubeObjectNodeCount): Unknown error."); return 0; }
    }

    PYHELIOS_API float* getTubeObjectNodes(helios::Context* context, unsigned int objID, unsigned int* size) {
        try {
            clearError();
            std::vector<helios::vec3> ns = context->getTubeObjectNodes(objID);
            static thread_local std::vector<float> buf;
            buf.clear(); buf.reserve(ns.size()*3);
            for (const auto& n : ns) { buf.push_back(n.x); buf.push_back(n.y); buf.push_back(n.z); }
            *size = buf.size();
            return buf.empty() ? nullptr : buf.data();
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); if (size) *size = 0; return nullptr; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); if (size) *size = 0; return nullptr; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getTubeObjectNodes): Unknown error."); if (size) *size = 0; return nullptr; }
    }

    PYHELIOS_API float* getTubeObjectNodeRadii(helios::Context* context, unsigned int objID, unsigned int* size) {
        try {
            clearError();
            static thread_local std::vector<float> buf;
            buf = context->getTubeObjectNodeRadii(objID);
            *size = buf.size();
            return buf.empty() ? nullptr : buf.data();
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); if (size) *size = 0; return nullptr; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); if (size) *size = 0; return nullptr; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getTubeObjectNodeRadii): Unknown error."); if (size) *size = 0; return nullptr; }
    }

    PYHELIOS_API float* getTubeObjectNodeColors(helios::Context* context, unsigned int objID, unsigned int* size) {
        try {
            clearError();
            std::vector<helios::RGBcolor> cs = context->getTubeObjectNodeColors(objID);
            static thread_local std::vector<float> buf;
            buf.clear(); buf.reserve(cs.size()*3);
            for (const auto& c : cs) { buf.push_back(c.r); buf.push_back(c.g); buf.push_back(c.b); }
            *size = buf.size();
            return buf.empty() ? nullptr : buf.data();
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); if (size) *size = 0; return nullptr; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); if (size) *size = 0; return nullptr; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getTubeObjectNodeColors): Unknown error."); if (size) *size = 0; return nullptr; }
    }

    PYHELIOS_API float getTubeObjectVolume(helios::Context* context, unsigned int objID) {
        try { clearError(); return context->getTubeObjectVolume(objID); }
        catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); return 0.0f; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0.0f; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getTubeObjectVolume): Unknown error."); return 0.0f; }
    }

    PYHELIOS_API float getTubeObjectSegmentVolume(helios::Context* context, unsigned int objID, unsigned int segment_index) {
        try { clearError(); return context->getTubeObjectSegmentVolume(objID, segment_index); }
        catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); return 0.0f; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0.0f; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getTubeObjectSegmentVolume): Unknown error."); return 0.0f; }
    }

    // ---- Cone ----
    PYHELIOS_API unsigned int getConeObjectSubdivisionCount(helios::Context* context, unsigned int objID) {
        try { clearError(); return context->getConeObjectSubdivisionCount(objID); }
        catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); return 0; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getConeObjectSubdivisionCount): Unknown error."); return 0; }
    }

    PYHELIOS_API float* getConeObjectNodes(helios::Context* context, unsigned int objID, unsigned int* size) {
        try {
            clearError();
            std::vector<helios::vec3> ns = context->getConeObjectNodes(objID);
            static thread_local std::vector<float> buf;
            buf.clear(); buf.reserve(ns.size()*3);
            for (const auto& n : ns) { buf.push_back(n.x); buf.push_back(n.y); buf.push_back(n.z); }
            *size = buf.size();
            return buf.empty() ? nullptr : buf.data();
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); if (size) *size = 0; return nullptr; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); if (size) *size = 0; return nullptr; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getConeObjectNodes): Unknown error."); if (size) *size = 0; return nullptr; }
    }

    PYHELIOS_API float* getConeObjectNodeRadii(helios::Context* context, unsigned int objID, unsigned int* size) {
        try {
            clearError();
            static thread_local std::vector<float> buf;
            buf = context->getConeObjectNodeRadii(objID);
            *size = buf.size();
            return buf.empty() ? nullptr : buf.data();
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); if (size) *size = 0; return nullptr; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); if (size) *size = 0; return nullptr; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getConeObjectNodeRadii): Unknown error."); if (size) *size = 0; return nullptr; }
    }

    PYHELIOS_API float* getConeObjectNode(helios::Context* context, unsigned int objID, int number) {
        try {
            clearError();
            helios::vec3 v = context->getConeObjectNode(objID, number);
            static float r[3]; r[0]=v.x; r[1]=v.y; r[2]=v.z; return r;
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getConeObjectNode): Unknown error."); static float e_r[3]={0,0,0}; return e_r; }
    }

    PYHELIOS_API float getConeObjectNodeRadius(helios::Context* context, unsigned int objID, int number) {
        try { clearError(); return context->getConeObjectNodeRadius(objID, number); }
        catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); return 0.0f; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0.0f; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getConeObjectNodeRadius): Unknown error."); return 0.0f; }
    }

    PYHELIOS_API float* getConeObjectAxisUnitVector(helios::Context* context, unsigned int objID) {
        try {
            clearError();
            helios::vec3 v = context->getConeObjectAxisUnitVector(objID);
            static float r[3]; r[0]=v.x; r[1]=v.y; r[2]=v.z; return r;
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getConeObjectAxisUnitVector): Unknown error."); static float e_r[3]={0,0,0}; return e_r; }
    }

    PYHELIOS_API float getConeObjectLength(helios::Context* context, unsigned int objID) {
        try { clearError(); return context->getConeObjectLength(objID); }
        catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); return 0.0f; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0.0f; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getConeObjectLength): Unknown error."); return 0.0f; }
    }

    PYHELIOS_API float getConeObjectVolume(helios::Context* context, unsigned int objID) {
        try { clearError(); return context->getConeObjectVolume(objID); }
        catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); return 0.0f; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0.0f; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getConeObjectVolume): Unknown error."); return 0.0f; }
    }

    // ==================== Primitive Geometry Queries ====================

    PYHELIOS_API float* getPatchCenter(helios::Context* context, unsigned int uuid) {
        try {
            clearError();
            helios::vec3 v = context->getPatchCenter(uuid);
            static float r[3]; r[0]=v.x; r[1]=v.y; r[2]=v.z; return r;
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPatchCenter): Unknown error."); static float e_r[3]={0,0,0}; return e_r; }
    }

    PYHELIOS_API float* getPatchSize(helios::Context* context, unsigned int uuid) {
        try {
            clearError();
            helios::vec2 v = context->getPatchSize(uuid);
            static float r[2]; r[0]=v.x; r[1]=v.y; return r;
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); static float e_r[2]={0,0}; return e_r; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); static float e_r[2]={0,0}; return e_r; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPatchSize): Unknown error."); static float e_r[2]={0,0}; return e_r; }
    }

    PYHELIOS_API float* getTriangleVertex(helios::Context* context, unsigned int uuid, unsigned int number) {
        try {
            clearError();
            helios::vec3 v = context->getTriangleVertex(uuid, number);
            static float r[3]; r[0]=v.x; r[1]=v.y; r[2]=v.z; return r;
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getTriangleVertex): Unknown error."); static float e_r[3]={0,0,0}; return e_r; }
    }

    PYHELIOS_API float* getVoxelCenter(helios::Context* context, unsigned int uuid) {
        try {
            clearError();
            helios::vec3 v = context->getVoxelCenter(uuid);
            static float r[3]; r[0]=v.x; r[1]=v.y; r[2]=v.z; return r;
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getVoxelCenter): Unknown error."); static float e_r[3]={0,0,0}; return e_r; }
    }

    PYHELIOS_API float* getVoxelSize(helios::Context* context, unsigned int uuid) {
        try {
            clearError();
            helios::vec3 v = context->getVoxelSize(uuid);
            static float r[3]; r[0]=v.x; r[1]=v.y; r[2]=v.z; return r;
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); static float e_r[3]={0,0,0}; return e_r; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getVoxelSize): Unknown error."); static float e_r[3]={0,0,0}; return e_r; }
    }

    PYHELIOS_API unsigned int getPatchCount(helios::Context* context, bool include_hidden) {
        try { clearError(); return static_cast<unsigned int>(context->getPatchCount(include_hidden)); }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPatchCount): Unknown error."); return 0; }
    }

    PYHELIOS_API unsigned int getTriangleCount(helios::Context* context, bool include_hidden) {
        try { clearError(); return static_cast<unsigned int>(context->getTriangleCount(include_hidden)); }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getTriangleCount): Unknown error."); return 0; }
    }

    PYHELIOS_API void getPrimitiveBoundingBox(helios::Context* context, unsigned int uuid, float* min_corner, float* max_corner) {
        try {
            clearError();
            if (!min_corner || !max_corner) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output corner pointer is null"); return; }
            helios::vec3 mn, mx;
            context->getPrimitiveBoundingBox(uuid, mn, mx);
            min_corner[0]=mn.x; min_corner[1]=mn.y; min_corner[2]=mn.z;
            max_corner[0]=mx.x; max_corner[1]=mx.y; max_corner[2]=mx.z;
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveBoundingBox): Unknown error."); }
    }

    PYHELIOS_API void getPrimitiveBoundingBox_batch(helios::Context* context, unsigned int* uuids, unsigned int count, float* min_corner, float* max_corner) {
        try {
            clearError();
            if (!min_corner || !max_corner) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output corner pointer is null"); return; }
            std::vector<unsigned int> v(uuids, uuids + count);
            helios::vec3 mn, mx;
            context->getPrimitiveBoundingBox(v, mn, mx);
            min_corner[0]=mn.x; min_corner[1]=mn.y; min_corner[2]=mn.z;
            max_corner[0]=mx.x; max_corner[1]=mx.y; max_corner[2]=mx.z;
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveBoundingBox_batch): Unknown error."); }
    }

    // ==================== Primitive Color Mutation ====================

    PYHELIOS_API void setPrimitiveColor(helios::Context* context, unsigned int uuid, float* color) {
        try {
            clearError();
            if (!color) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Color pointer is null"); return; }
            helios::RGBcolor c(color[0], color[1], color[2]);
            context->setPrimitiveColor(uuid, c);
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveColor): Unknown error."); }
    }

    PYHELIOS_API void setPrimitiveColor_batch(helios::Context* context, unsigned int* uuids, unsigned int count, float* color) {
        try {
            clearError();
            if (!color) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Color pointer is null"); return; }
            std::vector<unsigned int> v(uuids, uuids + count);
            helios::RGBcolor c(color[0], color[1], color[2]);
            context->setPrimitiveColor(v, c);
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveColor_batch): Unknown error."); }
    }

    PYHELIOS_API void setPrimitiveColorRGBA(helios::Context* context, unsigned int uuid, float* color) {
        try {
            clearError();
            if (!color) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Color pointer is null"); return; }
            helios::RGBAcolor c(color[0], color[1], color[2], color[3]);
            context->setPrimitiveColor(uuid, c);
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveColorRGBA): Unknown error."); }
    }

    PYHELIOS_API void setPrimitiveColorRGBA_batch(helios::Context* context, unsigned int* uuids, unsigned int count, float* color) {
        try {
            clearError();
            if (!color) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Color pointer is null"); return; }
            std::vector<unsigned int> v(uuids, uuids + count);
            helios::RGBAcolor c(color[0], color[1], color[2], color[3]);
            context->setPrimitiveColor(v, c);
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveColorRGBA_batch): Unknown error."); }
    }

    // ==================== Primitive Data Introspection / Cleanup ====================

    PYHELIOS_API void clearPrimitiveDataByLabel(helios::Context* context, unsigned int uuid, const char* label) {
        try {
            clearError();
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->clearPrimitiveData(uuid, label);
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::clearPrimitiveDataByLabel): Unknown error."); }
    }

    PYHELIOS_API void clearPrimitiveDataByLabel_batch(helios::Context* context, unsigned int* uuids, unsigned int count, const char* label) {
        try {
            clearError();
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            std::vector<unsigned int> v(uuids, uuids + count);
            context->clearPrimitiveData(v, label);
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::clearPrimitiveDataByLabel_batch): Unknown error."); }
    }

    PYHELIOS_API const char** listPrimitiveData(helios::Context* context, unsigned int uuid, unsigned int* count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); if (count) *count = 0; return nullptr; }
            if (!count) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count output parameter is null"); return nullptr; }
            static thread_local std::vector<std::string> static_strings;
            static thread_local std::vector<const char*> static_ptrs;
            static_strings = context->listPrimitiveData(uuid);
            static_ptrs.clear();
            static_ptrs.reserve(static_strings.size());
            for (auto& s : static_strings) { static_ptrs.push_back(s.c_str()); }
            *count = static_strings.size();
            return static_ptrs.empty() ? nullptr : static_ptrs.data();
        } catch (const std::runtime_error& e) { setError(PYHELIOS_ERROR_UUID_NOT_FOUND, e.what()); if (count) *count = 0; return nullptr; }
        catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (listPrimitiveData): ") + e.what()); if (count) *count = 0; return nullptr; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (listPrimitiveData): Unknown error."); if (count) *count = 0; return nullptr; }
    }

    // ==================== Domain Cropping ====================

    PYHELIOS_API void cropDomainX(helios::Context* context, float* xbounds) {
        try {
            clearError();
            if (!xbounds) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "xbounds is null"); return; }
            context->cropDomainX(helios::vec2(xbounds[0], xbounds[1]));
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::cropDomainX): Unknown error."); }
    }

    PYHELIOS_API void cropDomainY(helios::Context* context, float* ybounds) {
        try {
            clearError();
            if (!ybounds) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ybounds is null"); return; }
            context->cropDomainY(helios::vec2(ybounds[0], ybounds[1]));
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::cropDomainY): Unknown error."); }
    }

    PYHELIOS_API void cropDomainZ(helios::Context* context, float* zbounds) {
        try {
            clearError();
            if (!zbounds) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "zbounds is null"); return; }
            context->cropDomainZ(helios::vec2(zbounds[0], zbounds[1]));
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::cropDomainZ): Unknown error."); }
    }

    PYHELIOS_API void cropDomainXYZ(helios::Context* context, float* xbounds, float* ybounds, float* zbounds) {
        try {
            clearError();
            if (!xbounds || !ybounds || !zbounds) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Bounds pointer is null"); return; }
            context->cropDomain(helios::vec2(xbounds[0], xbounds[1]),
                                helios::vec2(ybounds[0], ybounds[1]),
                                helios::vec2(zbounds[0], zbounds[1]));
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::cropDomainXYZ): Unknown error."); }
    }

    PYHELIOS_API unsigned int* cropDomainByUUIDs(helios::Context* context, unsigned int* uuids, unsigned int count, float* xbounds, float* ybounds, float* zbounds, unsigned int* out_size) {
        try {
            clearError();
            if (!xbounds || !ybounds || !zbounds) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Bounds pointer is null"); if (out_size) *out_size = 0; return nullptr; }
            std::vector<unsigned int> v(uuids, uuids + count);
            context->cropDomain(v,
                                helios::vec2(xbounds[0], xbounds[1]),
                                helios::vec2(ybounds[0], ybounds[1]),
                                helios::vec2(zbounds[0], zbounds[1]));
            static thread_local std::vector<unsigned int> buf;
            buf = v;
            *out_size = buf.size();
            return buf.empty() ? nullptr : buf.data();
        } catch (const std::exception& e) { setError(PYHELIOS_ERROR_RUNTIME, e.what()); if (out_size) *out_size = 0; return nullptr; }
        catch (...) { setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::cropDomainByUUIDs): Unknown error."); if (out_size) *out_size = 0; return nullptr; }
    }

    //=========================================================================
    // Scalar Getters / Setters & List-of-String Getters
    //=========================================================================

    // ---- Bool getters ----

    PYHELIOS_API bool doesObjectExist(helios::Context* context, unsigned int objID) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return false; }
            return context->doesObjectExist(objID);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return false;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::doesObjectExist): ") + e.what()); return false;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::doesObjectExist): Unknown error."); return false;
        }
    }

    PYHELIOS_API bool doesObjectContainPrimitive(helios::Context* context, unsigned int objID, unsigned int uuid) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return false; }
            return context->doesObjectContainPrimitive(objID, uuid);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return false;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::doesObjectContainPrimitive): ") + e.what()); return false;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::doesObjectContainPrimitive): Unknown error."); return false;
        }
    }

    PYHELIOS_API bool doesMaterialDataExist(helios::Context* context, const char* material_label, const char* data_label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return false; }
            if (!material_label || !data_label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return false; }
            return context->doesMaterialDataExist(std::string(material_label), data_label);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return false;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::doesMaterialDataExist): ") + e.what()); return false;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::doesMaterialDataExist): Unknown error."); return false;
        }
    }

    PYHELIOS_API bool objectHasTexture(helios::Context* context, unsigned int objID) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return false; }
            return context->objectHasTexture(objID);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return false;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::objectHasTexture): ") + e.what()); return false;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::objectHasTexture): Unknown error."); return false;
        }
    }

    PYHELIOS_API bool isPrimitiveDirty(helios::Context* context, unsigned int uuid) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return false; }
            return context->isPrimitiveDirty(uuid);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return false;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::isPrimitiveDirty): ") + e.what()); return false;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::isPrimitiveDirty): Unknown error."); return false;
        }
    }

    PYHELIOS_API bool isObjectDataValueCachingEnabled(helios::Context* context, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return false; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return false; }
            return context->isObjectDataValueCachingEnabled(std::string(label));
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return false;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::isObjectDataValueCachingEnabled): ") + e.what()); return false;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::isObjectDataValueCachingEnabled): Unknown error."); return false;
        }
    }

    PYHELIOS_API bool isPrimitiveDataValueCachingEnabled(helios::Context* context, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return false; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return false; }
            return context->isPrimitiveDataValueCachingEnabled(std::string(label));
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return false;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::isPrimitiveDataValueCachingEnabled): ") + e.what()); return false;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::isPrimitiveDataValueCachingEnabled): Unknown error."); return false;
        }
    }

    PYHELIOS_API bool areObjectPrimitivesComplete(helios::Context* context, unsigned int objID) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return false; }
            return context->areObjectPrimitivesComplete(objID);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return false;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::areObjectPrimitivesComplete): ") + e.what()); return false;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::areObjectPrimitivesComplete): Unknown error."); return false;
        }
    }

    // ---- Numeric scalar getters ----

    PYHELIOS_API int getJulianDate(helios::Context* context) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            return context->getJulianDate();
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getJulianDate): ") + e.what()); return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getJulianDate): Unknown error."); return 0;
        }
    }

    PYHELIOS_API unsigned int getMaterialCount(helios::Context* context) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            return context->getMaterialCount();
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getMaterialCount): ") + e.what()); return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getMaterialCount): Unknown error."); return 0;
        }
    }

    PYHELIOS_API float getObjectArea(helios::Context* context, unsigned int objID) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0.0f; }
            return context->getObjectArea(objID);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0.0f;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getObjectArea): ") + e.what()); return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getObjectArea): Unknown error."); return 0.0f;
        }
    }

    PYHELIOS_API unsigned int getObjectPrimitiveCount(helios::Context* context, unsigned int objID) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            return context->getObjectPrimitiveCount(objID);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getObjectPrimitiveCount): ") + e.what()); return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getObjectPrimitiveCount): Unknown error."); return 0;
        }
    }

    PYHELIOS_API float getPolymeshObjectVolume(helios::Context* context, unsigned int objID) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0.0f; }
            return context->getPolymeshObjectVolume(objID);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0.0f;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPolymeshObjectVolume): ") + e.what()); return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPolymeshObjectVolume): Unknown error."); return 0.0f;
        }
    }

    PYHELIOS_API unsigned int getMaterialIDFromLabel(helios::Context* context, const char* material_label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!material_label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Material label is null"); return 0; }
            return context->getMaterialIDFromLabel(std::string(material_label));
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getMaterialIDFromLabel): ") + e.what()); return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getMaterialIDFromLabel): Unknown error."); return 0;
        }
    }

    PYHELIOS_API unsigned int getPrimitiveMaterialID(helios::Context* context, unsigned int uuid) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            return context->getPrimitiveMaterialID(uuid);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveMaterialID): ") + e.what()); return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveMaterialID): Unknown error."); return 0;
        }
    }

    PYHELIOS_API uint64_t getGlobalDataVersion(helios::Context* context, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return 0; }
            return context->getGlobalDataVersion(label);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getGlobalDataVersion): ") + e.what()); return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getGlobalDataVersion): Unknown error."); return 0;
        }
    }

    PYHELIOS_API unsigned int getPrimitiveParentObjectID(helios::Context* context, unsigned int uuid) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            return context->getPrimitiveParentObjectID(uuid);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveParentObjectID): ") + e.what()); return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveParentObjectID): Unknown error."); return 0;
        }
    }

    // ---- String returns (buffer pattern) ----

    PYHELIOS_API int getObjectTextureFile(helios::Context* context, unsigned int objID, char* buffer, int buffer_size) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!buffer || buffer_size <= 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Buffer is null or has non-positive size"); return 0; }
            std::string value = context->getObjectTextureFile(objID);
            int copy_length = std::min((int)value.length(), buffer_size - 1);
            std::strncpy(buffer, value.c_str(), copy_length);
            buffer[copy_length] = '\0';
            return copy_length;
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getObjectTextureFile): ") + e.what()); return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getObjectTextureFile): Unknown error."); return 0;
        }
    }

    // ---- List-of-string returns (count + index getter, avoids double thread_local) ----

    namespace {
        // Cache the most recent list-of-string snapshot per context+kind so the
        // count and per-index getter see the same data. Thread-local for safety.
        thread_local std::vector<std::string> s_list_primitive_data_labels_cache;
        thread_local std::vector<std::string> s_list_loaded_xml_files_cache;
    }

    PYHELIOS_API unsigned int listAllPrimitiveDataLabelsCount(helios::Context* context) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            s_list_primitive_data_labels_cache = context->listAllPrimitiveDataLabels();
            return (unsigned int)s_list_primitive_data_labels_cache.size();
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::listAllPrimitiveDataLabels): ") + e.what()); return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::listAllPrimitiveDataLabels): Unknown error."); return 0;
        }
    }

    PYHELIOS_API int listAllPrimitiveDataLabel(helios::Context* context, unsigned int index, char* buffer, int buffer_size) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!buffer || buffer_size <= 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Buffer is null or has non-positive size"); return 0; }
            if (index >= s_list_primitive_data_labels_cache.size()) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Index out of range; call listAllPrimitiveDataLabelsCount() first.");
                return 0;
            }
            const std::string& value = s_list_primitive_data_labels_cache[index];
            int copy_length = std::min((int)value.length(), buffer_size - 1);
            std::strncpy(buffer, value.c_str(), copy_length);
            buffer[copy_length] = '\0';
            return copy_length;
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::listAllPrimitiveDataLabel): ") + e.what()); return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::listAllPrimitiveDataLabel): Unknown error."); return 0;
        }
    }

    PYHELIOS_API unsigned int getLoadedXMLFileCount(helios::Context* context) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            s_list_loaded_xml_files_cache = context->getLoadedXMLFiles();
            return (unsigned int)s_list_loaded_xml_files_cache.size();
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getLoadedXMLFiles): ") + e.what()); return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getLoadedXMLFiles): Unknown error."); return 0;
        }
    }

    PYHELIOS_API int getLoadedXMLFile(helios::Context* context, unsigned int index, char* buffer, int buffer_size) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!buffer || buffer_size <= 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Buffer is null or has non-positive size"); return 0; }
            if (index >= s_list_loaded_xml_files_cache.size()) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Index out of range; call getLoadedXMLFileCount() first.");
                return 0;
            }
            const std::string& value = s_list_loaded_xml_files_cache[index];
            int copy_length = std::min((int)value.length(), buffer_size - 1);
            std::strncpy(buffer, value.c_str(), copy_length);
            buffer[copy_length] = '\0';
            return copy_length;
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getLoadedXMLFile): ") + e.what()); return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getLoadedXMLFile): Unknown error."); return 0;
        }
    }

    // ---- Simple actions ----

    PYHELIOS_API void printObjectInfo(helios::Context* context, unsigned int objID) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            context->printObjectInfo(objID);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::printObjectInfo): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::printObjectInfo): Unknown error.");
        }
    }

    PYHELIOS_API void printPrimitiveInfo(helios::Context* context, unsigned int uuid) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            context->printPrimitiveInfo(uuid);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::printPrimitiveInfo): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::printPrimitiveInfo): Unknown error.");
        }
    }

    PYHELIOS_API void enablePrimitiveDataValueCaching(helios::Context* context, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->enablePrimitiveDataValueCaching(std::string(label));
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::enablePrimitiveDataValueCaching): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::enablePrimitiveDataValueCaching): Unknown error.");
        }
    }

    PYHELIOS_API void disablePrimitiveDataValueCaching(helios::Context* context, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->disablePrimitiveDataValueCaching(std::string(label));
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::disablePrimitiveDataValueCaching): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::disablePrimitiveDataValueCaching): Unknown error.");
        }
    }

    PYHELIOS_API void enableObjectDataValueCaching(helios::Context* context, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->enableObjectDataValueCaching(std::string(label));
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::enableObjectDataValueCaching): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::enableObjectDataValueCaching): Unknown error.");
        }
    }

    PYHELIOS_API void disableObjectDataValueCaching(helios::Context* context, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->disableObjectDataValueCaching(std::string(label));
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::disableObjectDataValueCaching): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::disableObjectDataValueCaching): Unknown error.");
        }
    }

    PYHELIOS_API void setObjectDataFromPrimitiveDataMean(helios::Context* context, unsigned int objID, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->setObjectDataFromPrimitiveDataMean(objID, std::string(label));
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setObjectDataFromPrimitiveDataMean): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setObjectDataFromPrimitiveDataMean): Unknown error.");
        }
    }

    PYHELIOS_API void renameMaterial(helios::Context* context, const char* old_label, const char* new_label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!old_label || !new_label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->renameMaterial(std::string(old_label), std::string(new_label));
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::renameMaterial): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::renameMaterial): Unknown error.");
        }
    }

    PYHELIOS_API void renamePrimitiveData(helios::Context* context, unsigned int uuid, const char* old_label, const char* new_label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!old_label || !new_label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->renamePrimitiveData(uuid, old_label, new_label);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::renamePrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::renamePrimitiveData): Unknown error.");
        }
    }

    PYHELIOS_API void clearMaterialData(helios::Context* context, const char* material_label, const char* data_label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!material_label || !data_label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            context->clearMaterialData(std::string(material_label), data_label);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::clearMaterialData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::clearMaterialData): Unknown error.");
        }
    }

    //=========================================================================
    // Vector-return getters & geometry mutators
    //=========================================================================

    // ---- Vector<uint> returns ----

    PYHELIOS_API unsigned int* getDeletedUUIDs(helios::Context* context, unsigned int* count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); if (count) *count = 0; return nullptr; }
            if (!count) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count out-pointer is null"); return nullptr; }
            static thread_local std::vector<unsigned int> buf;
            buf = context->getDeletedUUIDs();
            *count = (unsigned int)buf.size();
            return buf.empty() ? nullptr : buf.data();
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); if (count) *count = 0; return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getDeletedUUIDs): ") + e.what()); if (count) *count = 0; return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getDeletedUUIDs): Unknown error."); if (count) *count = 0; return nullptr;
        }
    }

    PYHELIOS_API unsigned int* getDirtyUUIDs(helios::Context* context, bool include_deleted, unsigned int* count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); if (count) *count = 0; return nullptr; }
            if (!count) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count out-pointer is null"); return nullptr; }
            static thread_local std::vector<unsigned int> buf;
            buf = context->getDirtyUUIDs(include_deleted);
            *count = (unsigned int)buf.size();
            return buf.empty() ? nullptr : buf.data();
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); if (count) *count = 0; return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getDirtyUUIDs): ") + e.what()); if (count) *count = 0; return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getDirtyUUIDs): Unknown error."); if (count) *count = 0; return nullptr;
        }
    }

    PYHELIOS_API unsigned int* getUniquePrimitiveParentObjectIDs(helios::Context* context, unsigned int* uuids, unsigned int count, bool include_zero, unsigned int* out_count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); if (out_count) *out_count = 0; return nullptr; }
            if (!out_count) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Out-count pointer is null"); return nullptr; }
            std::vector<unsigned int> input(uuids ? uuids : nullptr, uuids ? (uuids + count) : nullptr);
            static thread_local std::vector<unsigned int> buf;
            buf = context->getUniquePrimitiveParentObjectIDs(input, include_zero);
            *out_count = (unsigned int)buf.size();
            return buf.empty() ? nullptr : buf.data();
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); if (out_count) *out_count = 0; return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getUniquePrimitiveParentObjectIDs): ") + e.what()); if (out_count) *out_count = 0; return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getUniquePrimitiveParentObjectIDs): Unknown error."); if (out_count) *out_count = 0; return nullptr;
        }
    }

    // ---- Object normal / origin queries & setters ----

    PYHELIOS_API float* getObjectAverageNormal(helios::Context* context, unsigned int objID) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); static float zero[3] = {0,0,0}; return zero; }
            helios::vec3 n = context->getObjectAverageNormal(objID);
            static float result[3];
            result[0] = n.x; result[1] = n.y; result[2] = n.z;
            return result;
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); static float zero[3] = {0,0,0}; return zero;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getObjectAverageNormal): ") + e.what()); static float zero[3] = {0,0,0}; return zero;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getObjectAverageNormal): Unknown error."); static float zero[3] = {0,0,0}; return zero;
        }
    }

    PYHELIOS_API void setObjectAverageNormal(helios::Context* context, unsigned int objID, float* origin, float* new_normal) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!origin || !new_normal) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Origin or normal pointer is null"); return; }
            helios::vec3 o(origin[0], origin[1], origin[2]);
            helios::vec3 n(new_normal[0], new_normal[1], new_normal[2]);
            context->setObjectAverageNormal(objID, o, n);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setObjectAverageNormal): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setObjectAverageNormal): Unknown error.");
        }
    }

    PYHELIOS_API void setObjectOrigin(helios::Context* context, unsigned int objID, float* origin) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!origin) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Origin pointer is null"); return; }
            helios::vec3 o(origin[0], origin[1], origin[2]);
            context->setObjectOrigin(objID, o);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setObjectOrigin): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setObjectOrigin): Unknown error.");
        }
    }

    // ---- Primitive azimuth / elevation setters ----

    PYHELIOS_API void setPrimitiveAzimuth(helios::Context* context, unsigned int uuid, float* origin, float new_azimuth) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!origin) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Origin pointer is null"); return; }
            helios::vec3 o(origin[0], origin[1], origin[2]);
            context->setPrimitiveAzimuth(uuid, o, new_azimuth);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveAzimuth): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveAzimuth): Unknown error.");
        }
    }

    PYHELIOS_API void setPrimitiveElevation(helios::Context* context, unsigned int uuid, float* origin, float new_elevation) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!origin) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Origin pointer is null"); return; }
            helios::vec3 o(origin[0], origin[1], origin[2]);
            context->setPrimitiveElevation(uuid, o, new_elevation);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveElevation): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveElevation): Unknown error.");
        }
    }

    // ---- Geometry mutators ----

    PYHELIOS_API void setTriangleVertices(helios::Context* context, unsigned int uuid, float* vertex0, float* vertex1, float* vertex2) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!vertex0 || !vertex1 || !vertex2) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Vertex pointer is null"); return; }
            helios::vec3 v0(vertex0[0], vertex0[1], vertex0[2]);
            helios::vec3 v1(vertex1[0], vertex1[1], vertex1[2]);
            helios::vec3 v2(vertex2[0], vertex2[1], vertex2[2]);
            context->setTriangleVertices(uuid, v0, v1, v2);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setTriangleVertices): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setTriangleVertices): Unknown error.");
        }
    }

    PYHELIOS_API void setPrimitiveNormal(helios::Context* context, unsigned int uuid, float* origin, float* new_normal) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!origin || !new_normal) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Origin or normal pointer is null"); return; }
            helios::vec3 o(origin[0], origin[1], origin[2]);
            helios::vec3 n(new_normal[0], new_normal[1], new_normal[2]);
            context->setPrimitiveNormal(uuid, o, n);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveNormal): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveNormal): Unknown error.");
        }
    }

    PYHELIOS_API void setPrimitiveNormalBatch(helios::Context* context, unsigned int* uuids, unsigned int count, float* origin, float* new_normal) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!uuids && count > 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs pointer is null"); return; }
            if (!origin || !new_normal) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Origin or normal pointer is null"); return; }
            std::vector<unsigned int> v(uuids, uuids + count);
            helios::vec3 o(origin[0], origin[1], origin[2]);
            helios::vec3 n(new_normal[0], new_normal[1], new_normal[2]);
            context->setPrimitiveNormal(v, o, n);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveNormal): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveNormal): Unknown error.");
        }
    }

    PYHELIOS_API void setPrimitiveParentObjectID(helios::Context* context, unsigned int uuid, unsigned int objID) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            context->setPrimitiveParentObjectID(uuid, objID);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveParentObjectID): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveParentObjectID): Unknown error.");
        }
    }

    PYHELIOS_API void setPrimitiveParentObjectIDBatch(helios::Context* context, unsigned int* uuids, unsigned int count, unsigned int objID) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!uuids && count > 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs pointer is null"); return; }
            std::vector<unsigned int> v(uuids, uuids + count);
            context->setPrimitiveParentObjectID(v, objID);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveParentObjectID): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveParentObjectID): Unknown error.");
        }
    }

    //=========================================================================
    // Material data API + unique data values
    //=========================================================================

    // Internal helper macro: validate pointers, call body, catch.
    // Each setMaterialData specialization does the same null checks then the typed call.
    #define MATDATA_PROLOGUE(fname) \
        clearError(); \
        try { \
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; } \
            if (!material_label || !data_label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }

    #define MATDATA_EPILOGUE(fname) \
        } catch (const std::runtime_error& e) { \
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); \
        } catch (const std::exception& e) { \
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::" fname "): ") + e.what()); \
        } catch (...) { \
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::" fname "): Unknown error."); \
        }

    // ---- setMaterialData<T> ----

    PYHELIOS_API void setMaterialDataInt(helios::Context* context, const char* material_label, const char* data_label, int value) {
        MATDATA_PROLOGUE("setMaterialData")
        context->setMaterialData(std::string(material_label), data_label, value);
        MATDATA_EPILOGUE("setMaterialData")
    }

    PYHELIOS_API void setMaterialDataUInt(helios::Context* context, const char* material_label, const char* data_label, unsigned int value) {
        MATDATA_PROLOGUE("setMaterialData")
        context->setMaterialData(std::string(material_label), data_label, value);
        MATDATA_EPILOGUE("setMaterialData")
    }

    PYHELIOS_API void setMaterialDataFloat(helios::Context* context, const char* material_label, const char* data_label, float value) {
        MATDATA_PROLOGUE("setMaterialData")
        context->setMaterialData(std::string(material_label), data_label, value);
        MATDATA_EPILOGUE("setMaterialData")
    }

    PYHELIOS_API void setMaterialDataDouble(helios::Context* context, const char* material_label, const char* data_label, double value) {
        MATDATA_PROLOGUE("setMaterialData")
        context->setMaterialData(std::string(material_label), data_label, value);
        MATDATA_EPILOGUE("setMaterialData")
    }

    PYHELIOS_API void setMaterialDataString(helios::Context* context, const char* material_label, const char* data_label, const char* value) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!material_label || !data_label || !value) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label or value is null"); return; }
            context->setMaterialData(std::string(material_label), data_label, std::string(value));
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setMaterialData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setMaterialData): Unknown error.");
        }
    }

    PYHELIOS_API void setMaterialDataVec2(helios::Context* context, const char* material_label, const char* data_label, float x, float y) {
        MATDATA_PROLOGUE("setMaterialData")
        context->setMaterialData(std::string(material_label), data_label, helios::vec2(x, y));
        MATDATA_EPILOGUE("setMaterialData")
    }

    PYHELIOS_API void setMaterialDataVec3(helios::Context* context, const char* material_label, const char* data_label, float x, float y, float z) {
        MATDATA_PROLOGUE("setMaterialData")
        context->setMaterialData(std::string(material_label), data_label, helios::vec3(x, y, z));
        MATDATA_EPILOGUE("setMaterialData")
    }

    PYHELIOS_API void setMaterialDataVec4(helios::Context* context, const char* material_label, const char* data_label, float x, float y, float z, float w) {
        MATDATA_PROLOGUE("setMaterialData")
        context->setMaterialData(std::string(material_label), data_label, helios::vec4(x, y, z, w));
        MATDATA_EPILOGUE("setMaterialData")
    }

    PYHELIOS_API void setMaterialDataInt2(helios::Context* context, const char* material_label, const char* data_label, int x, int y) {
        MATDATA_PROLOGUE("setMaterialData")
        context->setMaterialData(std::string(material_label), data_label, helios::int2(x, y));
        MATDATA_EPILOGUE("setMaterialData")
    }

    PYHELIOS_API void setMaterialDataInt3(helios::Context* context, const char* material_label, const char* data_label, int x, int y, int z) {
        MATDATA_PROLOGUE("setMaterialData")
        context->setMaterialData(std::string(material_label), data_label, helios::int3(x, y, z));
        MATDATA_EPILOGUE("setMaterialData")
    }

    PYHELIOS_API void setMaterialDataInt4(helios::Context* context, const char* material_label, const char* data_label, int x, int y, int z, int w) {
        MATDATA_PROLOGUE("setMaterialData")
        context->setMaterialData(std::string(material_label), data_label, helios::int4(x, y, z, w));
        MATDATA_EPILOGUE("setMaterialData")
    }

    // ---- getMaterialData<T> ----

    PYHELIOS_API int getMaterialDataInt(helios::Context* context, const char* material_label, const char* data_label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!material_label || !data_label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return 0; }
            int value;
            context->getMaterialData(std::string(material_label), data_label, value);
            return value;
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getMaterialData): ") + e.what()); return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getMaterialData): Unknown error."); return 0;
        }
    }

    PYHELIOS_API unsigned int getMaterialDataUInt(helios::Context* context, const char* material_label, const char* data_label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!material_label || !data_label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return 0; }
            unsigned int value;
            context->getMaterialData(std::string(material_label), data_label, value);
            return value;
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getMaterialData): ") + e.what()); return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getMaterialData): Unknown error."); return 0;
        }
    }

    PYHELIOS_API float getMaterialDataFloat(helios::Context* context, const char* material_label, const char* data_label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0.0f; }
            if (!material_label || !data_label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return 0.0f; }
            float value;
            context->getMaterialData(std::string(material_label), data_label, value);
            return value;
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0.0f;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getMaterialData): ") + e.what()); return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getMaterialData): Unknown error."); return 0.0f;
        }
    }

    PYHELIOS_API double getMaterialDataDouble(helios::Context* context, const char* material_label, const char* data_label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0.0; }
            if (!material_label || !data_label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return 0.0; }
            double value;
            context->getMaterialData(std::string(material_label), data_label, value);
            return value;
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0.0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getMaterialData): ") + e.what()); return 0.0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getMaterialData): Unknown error."); return 0.0;
        }
    }

    PYHELIOS_API int getMaterialDataString(helios::Context* context, const char* material_label, const char* data_label, char* buffer, int buffer_size) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!material_label || !data_label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return 0; }
            if (!buffer || buffer_size <= 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Buffer is null or has non-positive size"); return 0; }
            std::string value;
            context->getMaterialData(std::string(material_label), data_label, value);
            int copy_length = std::min((int)value.length(), buffer_size - 1);
            std::strncpy(buffer, value.c_str(), copy_length);
            buffer[copy_length] = '\0';
            return copy_length;
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getMaterialData): ") + e.what()); return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getMaterialData): Unknown error."); return 0;
        }
    }

    PYHELIOS_API void getMaterialDataVec2(helios::Context* context, const char* material_label, const char* data_label, float* x, float* y) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!material_label || !data_label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            if (!x || !y) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output pointer is null"); return; }
            helios::vec2 value;
            context->getMaterialData(std::string(material_label), data_label, value);
            *x = value.x; *y = value.y;
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getMaterialData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getMaterialData): Unknown error.");
        }
    }

    PYHELIOS_API void getMaterialDataVec3(helios::Context* context, const char* material_label, const char* data_label, float* x, float* y, float* z) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!material_label || !data_label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            if (!x || !y || !z) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output pointer is null"); return; }
            helios::vec3 value;
            context->getMaterialData(std::string(material_label), data_label, value);
            *x = value.x; *y = value.y; *z = value.z;
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getMaterialData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getMaterialData): Unknown error.");
        }
    }

    PYHELIOS_API void getMaterialDataVec4(helios::Context* context, const char* material_label, const char* data_label, float* x, float* y, float* z, float* w) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!material_label || !data_label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            if (!x || !y || !z || !w) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output pointer is null"); return; }
            helios::vec4 value;
            context->getMaterialData(std::string(material_label), data_label, value);
            *x = value.x; *y = value.y; *z = value.z; *w = value.w;
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getMaterialData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getMaterialData): Unknown error.");
        }
    }

    PYHELIOS_API void getMaterialDataInt2(helios::Context* context, const char* material_label, const char* data_label, int* x, int* y) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!material_label || !data_label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            if (!x || !y) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output pointer is null"); return; }
            helios::int2 value;
            context->getMaterialData(std::string(material_label), data_label, value);
            *x = value.x; *y = value.y;
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getMaterialData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getMaterialData): Unknown error.");
        }
    }

    PYHELIOS_API void getMaterialDataInt3(helios::Context* context, const char* material_label, const char* data_label, int* x, int* y, int* z) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!material_label || !data_label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            if (!x || !y || !z) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output pointer is null"); return; }
            helios::int3 value;
            context->getMaterialData(std::string(material_label), data_label, value);
            *x = value.x; *y = value.y; *z = value.z;
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getMaterialData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getMaterialData): Unknown error.");
        }
    }

    PYHELIOS_API void getMaterialDataInt4(helios::Context* context, const char* material_label, const char* data_label, int* x, int* y, int* z, int* w) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!material_label || !data_label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return; }
            if (!x || !y || !z || !w) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output pointer is null"); return; }
            helios::int4 value;
            context->getMaterialData(std::string(material_label), data_label, value);
            *x = value.x; *y = value.y; *z = value.z; *w = value.w;
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getMaterialData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getMaterialData): Unknown error.");
        }
    }

    PYHELIOS_API int getMaterialDataType(helios::Context* context, const char* material_label, const char* data_label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return -1; }
            if (!material_label || !data_label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return -1; }
            return (int)context->getMaterialDataType(std::string(material_label), data_label);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return -1;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getMaterialDataType): ") + e.what()); return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getMaterialDataType): Unknown error."); return -1;
        }
    }

    // ---- Unique data values ----
    // String variants use a count+index pair backed by a thread_local cache,
    // mirroring the approach used by listAllPrimitiveDataLabels.

    namespace {
        thread_local std::vector<std::string> s_unique_primitive_string_cache;
        thread_local std::vector<std::string> s_unique_object_string_cache;
    }

    PYHELIOS_API int* getUniquePrimitiveDataValuesInt(helios::Context* context, const char* label, unsigned int* count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); if (count) *count = 0; return nullptr; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); if (count) *count = 0; return nullptr; }
            if (!count) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count out-pointer is null"); return nullptr; }
            static thread_local std::vector<int> buf;
            buf.clear();
            context->getUniquePrimitiveDataValues<int>(std::string(label), buf);
            *count = (unsigned int)buf.size();
            return buf.empty() ? nullptr : buf.data();
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); if (count) *count = 0; return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getUniquePrimitiveDataValues): ") + e.what()); if (count) *count = 0; return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getUniquePrimitiveDataValues): Unknown error."); if (count) *count = 0; return nullptr;
        }
    }

    PYHELIOS_API unsigned int* getUniquePrimitiveDataValuesUInt(helios::Context* context, const char* label, unsigned int* count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); if (count) *count = 0; return nullptr; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); if (count) *count = 0; return nullptr; }
            if (!count) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count out-pointer is null"); return nullptr; }
            static thread_local std::vector<unsigned int> buf;
            buf.clear();
            context->getUniquePrimitiveDataValues<unsigned int>(std::string(label), buf);
            *count = (unsigned int)buf.size();
            return buf.empty() ? nullptr : buf.data();
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); if (count) *count = 0; return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getUniquePrimitiveDataValues): ") + e.what()); if (count) *count = 0; return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getUniquePrimitiveDataValues): Unknown error."); if (count) *count = 0; return nullptr;
        }
    }

    PYHELIOS_API unsigned int getUniquePrimitiveDataValuesStringCount(helios::Context* context, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return 0; }
            s_unique_primitive_string_cache.clear();
            context->getUniquePrimitiveDataValues<std::string>(std::string(label), s_unique_primitive_string_cache);
            return (unsigned int)s_unique_primitive_string_cache.size();
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getUniquePrimitiveDataValues): ") + e.what()); return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getUniquePrimitiveDataValues): Unknown error."); return 0;
        }
    }

    // Pure cache reader: must be preceded by getUniquePrimitiveDataValuesStringCount,
    // which populates s_unique_primitive_string_cache. The context/label parameters
    // are accepted for API symmetry but ignored - the Python wrapper fuses both calls.
    PYHELIOS_API int getUniquePrimitiveDataValuesString(helios::Context* /*context*/, const char* /*label*/, unsigned int index, char* buffer, int buffer_size) {
        clearError();
        try {
            if (!buffer || buffer_size <= 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Buffer is null or has non-positive size"); return 0; }
            if (index >= s_unique_primitive_string_cache.size()) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Index out of range; call getUniquePrimitiveDataValuesStringCount() first.");
                return 0;
            }
            const std::string& value = s_unique_primitive_string_cache[index];
            int copy_length = std::min((int)value.length(), buffer_size - 1);
            std::strncpy(buffer, value.c_str(), copy_length);
            buffer[copy_length] = '\0';
            return copy_length;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getUniquePrimitiveDataValuesString): ") + e.what()); return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getUniquePrimitiveDataValuesString): Unknown error."); return 0;
        }
    }

    PYHELIOS_API int* getUniqueObjectDataValuesInt(helios::Context* context, const char* label, unsigned int* count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); if (count) *count = 0; return nullptr; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); if (count) *count = 0; return nullptr; }
            if (!count) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count out-pointer is null"); return nullptr; }
            static thread_local std::vector<int> buf;
            buf.clear();
            context->getUniqueObjectDataValues<int>(std::string(label), buf);
            *count = (unsigned int)buf.size();
            return buf.empty() ? nullptr : buf.data();
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); if (count) *count = 0; return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getUniqueObjectDataValues): ") + e.what()); if (count) *count = 0; return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getUniqueObjectDataValues): Unknown error."); if (count) *count = 0; return nullptr;
        }
    }

    PYHELIOS_API unsigned int* getUniqueObjectDataValuesUInt(helios::Context* context, const char* label, unsigned int* count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); if (count) *count = 0; return nullptr; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); if (count) *count = 0; return nullptr; }
            if (!count) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count out-pointer is null"); return nullptr; }
            static thread_local std::vector<unsigned int> buf;
            buf.clear();
            context->getUniqueObjectDataValues<unsigned int>(std::string(label), buf);
            *count = (unsigned int)buf.size();
            return buf.empty() ? nullptr : buf.data();
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); if (count) *count = 0; return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getUniqueObjectDataValues): ") + e.what()); if (count) *count = 0; return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getUniqueObjectDataValues): Unknown error."); if (count) *count = 0; return nullptr;
        }
    }

    PYHELIOS_API unsigned int getUniqueObjectDataValuesStringCount(helios::Context* context, const char* label) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!label) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null"); return 0; }
            s_unique_object_string_cache.clear();
            context->getUniqueObjectDataValues<std::string>(std::string(label), s_unique_object_string_cache);
            return (unsigned int)s_unique_object_string_cache.size();
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getUniqueObjectDataValues): ") + e.what()); return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getUniqueObjectDataValues): Unknown error."); return 0;
        }
    }

    // Same count+index protocol as getUniquePrimitiveDataValuesString - see comment there.
    PYHELIOS_API int getUniqueObjectDataValuesString(helios::Context* /*context*/, const char* /*label*/, unsigned int index, char* buffer, int buffer_size) {
        clearError();
        try {
            if (!buffer || buffer_size <= 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Buffer is null or has non-positive size"); return 0; }
            if (index >= s_unique_object_string_cache.size()) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Index out of range; call getUniqueObjectDataValuesStringCount() first.");
                return 0;
            }
            const std::string& value = s_unique_object_string_cache[index];
            int copy_length = std::min((int)value.length(), buffer_size - 1);
            std::strncpy(buffer, value.c_str(), copy_length);
            buffer[copy_length] = '\0';
            return copy_length;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getUniqueObjectDataValuesString): ") + e.what()); return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getUniqueObjectDataValuesString): Unknown error."); return 0;
        }
    }

    #undef MATDATA_PROLOGUE
    #undef MATDATA_EPILOGUE

    //=========================================================================
    // 4x4 transformation matrices + domain bounds
    //=========================================================================

    // ---- 4x4 transformation matrices ----
    // helios::Context methods take `float (&T)[16]` - a reference to a fixed array.
    // We accept `float*` from ctypes and convert via reinterpret_cast.

    PYHELIOS_API void getObjectTransformationMatrix(helios::Context* context, unsigned int objID, float* T_out) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!T_out) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output buffer is null"); return; }
            float (&T_ref)[16] = *reinterpret_cast<float (*)[16]>(T_out);
            context->getObjectTransformationMatrix(objID, T_ref);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getObjectTransformationMatrix): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getObjectTransformationMatrix): Unknown error.");
        }
    }

    PYHELIOS_API void setObjectTransformationMatrix(helios::Context* context, unsigned int objID, float* T_in) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!T_in) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Matrix buffer is null"); return; }
            float (&T_ref)[16] = *reinterpret_cast<float (*)[16]>(T_in);
            context->setObjectTransformationMatrix(objID, T_ref);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setObjectTransformationMatrix): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setObjectTransformationMatrix): Unknown error.");
        }
    }

    PYHELIOS_API void setObjectTransformationMatrixBatch(helios::Context* context, unsigned int* objIDs, unsigned int count, float* T_in) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!objIDs && count > 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ObjIDs pointer is null"); return; }
            if (!T_in) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Matrix buffer is null"); return; }
            std::vector<unsigned int> v(objIDs, objIDs + count);
            float (&T_ref)[16] = *reinterpret_cast<float (*)[16]>(T_in);
            context->setObjectTransformationMatrix(v, T_ref);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setObjectTransformationMatrix): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setObjectTransformationMatrix): Unknown error.");
        }
    }

    PYHELIOS_API void getPrimitiveTransformationMatrix(helios::Context* context, unsigned int uuid, float* T_out) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!T_out) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output buffer is null"); return; }
            float (&T_ref)[16] = *reinterpret_cast<float (*)[16]>(T_out);
            context->getPrimitiveTransformationMatrix(uuid, T_ref);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveTransformationMatrix): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveTransformationMatrix): Unknown error.");
        }
    }

    PYHELIOS_API void setPrimitiveTransformationMatrix(helios::Context* context, unsigned int uuid, float* T_in) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!T_in) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Matrix buffer is null"); return; }
            float (&T_ref)[16] = *reinterpret_cast<float (*)[16]>(T_in);
            context->setPrimitiveTransformationMatrix(uuid, T_ref);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveTransformationMatrix): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveTransformationMatrix): Unknown error.");
        }
    }

    PYHELIOS_API void setPrimitiveTransformationMatrixBatch(helios::Context* context, unsigned int* uuids, unsigned int count, float* T_in) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!uuids && count > 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs pointer is null"); return; }
            if (!T_in) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Matrix buffer is null"); return; }
            std::vector<unsigned int> v(uuids, uuids + count);
            float (&T_ref)[16] = *reinterpret_cast<float (*)[16]>(T_in);
            context->setPrimitiveTransformationMatrix(v, T_ref);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setPrimitiveTransformationMatrix): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setPrimitiveTransformationMatrix): Unknown error.");
        }
    }

    // ---- Domain bounding box / sphere ----

    PYHELIOS_API void getDomainBoundingBox(helios::Context* context, float* bounds_out) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!bounds_out) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output buffer is null"); return; }
            helios::vec2 xb, yb, zb;
            context->getDomainBoundingBox(xb, yb, zb);
            bounds_out[0] = xb.x; bounds_out[1] = xb.y;
            bounds_out[2] = yb.x; bounds_out[3] = yb.y;
            bounds_out[4] = zb.x; bounds_out[5] = zb.y;
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getDomainBoundingBox): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getDomainBoundingBox): Unknown error.");
        }
    }

    PYHELIOS_API void getDomainBoundingBoxFiltered(helios::Context* context, unsigned int* uuids, unsigned int count, float* bounds_out) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!uuids && count > 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs pointer is null"); return; }
            if (!bounds_out) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output buffer is null"); return; }
            std::vector<unsigned int> v(uuids, uuids + count);
            helios::vec2 xb, yb, zb;
            context->getDomainBoundingBox(v, xb, yb, zb);
            bounds_out[0] = xb.x; bounds_out[1] = xb.y;
            bounds_out[2] = yb.x; bounds_out[3] = yb.y;
            bounds_out[4] = zb.x; bounds_out[5] = zb.y;
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getDomainBoundingBox): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getDomainBoundingBox): Unknown error.");
        }
    }

    PYHELIOS_API void getDomainBoundingSphere(helios::Context* context, float* center_out, float* radius_out) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!center_out || !radius_out) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output pointer is null"); return; }
            helios::vec3 c;
            float r;
            context->getDomainBoundingSphere(c, r);
            center_out[0] = c.x; center_out[1] = c.y; center_out[2] = c.z;
            *radius_out = r;
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getDomainBoundingSphere): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getDomainBoundingSphere): Unknown error.");
        }
    }

    PYHELIOS_API void getDomainBoundingSphereFiltered(helios::Context* context, unsigned int* uuids, unsigned int count, float* center_out, float* radius_out) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!uuids && count > 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs pointer is null"); return; }
            if (!center_out || !radius_out) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output pointer is null"); return; }
            std::vector<unsigned int> v(uuids, uuids + count);
            helios::vec3 c;
            float r;
            context->getDomainBoundingSphere(v, c, r);
            center_out[0] = c.x; center_out[1] = c.y; center_out[2] = c.z;
            *radius_out = r;
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getDomainBoundingSphere): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getDomainBoundingSphere): Unknown error.");
        }
    }

    //=========================================================================
    // Tube/polymesh + object color/dirty/tile mutators
    //=========================================================================

    // ---- Tube object mutators ----

    PYHELIOS_API void setTubeNodes(helios::Context* context, unsigned int objID, float* node_xyz_flat, unsigned int count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!node_xyz_flat && count > 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Node positions pointer is null"); return; }
            std::vector<helios::vec3> nodes;
            nodes.reserve(count);
            for (unsigned int i = 0; i < count; ++i) {
                nodes.emplace_back(node_xyz_flat[i*3 + 0], node_xyz_flat[i*3 + 1], node_xyz_flat[i*3 + 2]);
            }
            context->setTubeNodes(objID, nodes);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setTubeNodes): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setTubeNodes): Unknown error.");
        }
    }

    PYHELIOS_API void setTubeRadii(helios::Context* context, unsigned int objID, float* node_radii, unsigned int count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!node_radii && count > 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Radii pointer is null"); return; }
            std::vector<float> radii(node_radii, node_radii + count);
            context->setTubeRadii(objID, radii);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setTubeRadii): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setTubeRadii): Unknown error.");
        }
    }

    PYHELIOS_API void scaleTubeGirth(helios::Context* context, unsigned int objID, float scale_factor) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            context->scaleTubeGirth(objID, scale_factor);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::scaleTubeGirth): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::scaleTubeGirth): Unknown error.");
        }
    }

    PYHELIOS_API void scaleTubeLength(helios::Context* context, unsigned int objID, float scale_factor) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            context->scaleTubeLength(objID, scale_factor);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::scaleTubeLength): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::scaleTubeLength): Unknown error.");
        }
    }

    PYHELIOS_API void pruneTubeNodes(helios::Context* context, unsigned int objID, unsigned int node_index) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            context->pruneTubeNodes(objID, node_index);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::pruneTubeNodes): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::pruneTubeNodes): Unknown error.");
        }
    }

    PYHELIOS_API void appendTubeSegmentColor(helios::Context* context, unsigned int objID, float* node_position, float node_radius, float* color_rgb) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!node_position || !color_rgb) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Node position or color pointer is null"); return; }
            helios::vec3 pos(node_position[0], node_position[1], node_position[2]);
            helios::RGBcolor c(color_rgb[0], color_rgb[1], color_rgb[2]);
            context->appendTubeSegment(objID, pos, node_radius, c);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::appendTubeSegment): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::appendTubeSegment): Unknown error.");
        }
    }

    PYHELIOS_API void appendTubeSegmentTexture(helios::Context* context, unsigned int objID, float* node_position, float node_radius, const char* texturefile, float* textureuv_ufrac) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!node_position || !textureuv_ufrac || !texturefile) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Node, UV, or texture file pointer is null"); return; }
            helios::vec3 pos(node_position[0], node_position[1], node_position[2]);
            helios::vec2 uv(textureuv_ufrac[0], textureuv_ufrac[1]);
            context->appendTubeSegment(objID, pos, node_radius, texturefile, uv);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::appendTubeSegment): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::appendTubeSegment): Unknown error.");
        }
    }

    // ---- Polymesh object creation ----

    PYHELIOS_API unsigned int addPolymeshObject(helios::Context* context, unsigned int* uuids, unsigned int count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!uuids && count > 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs pointer is null"); return 0; }
            std::vector<unsigned int> v(uuids, uuids + count);
            return context->addPolymeshObject(v);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::addPolymeshObject): ") + e.what()); return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::addPolymeshObject): Unknown error."); return 0;
        }
    }

    // ---- Object color / texture override ----

    PYHELIOS_API void setObjectColorRGB(helios::Context* context, unsigned int objID, float* color_rgb) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!color_rgb) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Color pointer is null"); return; }
            context->setObjectColor(objID, helios::RGBcolor(color_rgb[0], color_rgb[1], color_rgb[2]));
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setObjectColor): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setObjectColor): Unknown error.");
        }
    }

    PYHELIOS_API void setObjectColorRGBBatch(helios::Context* context, unsigned int* objIDs, unsigned int count, float* color_rgb) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!objIDs && count > 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ObjIDs pointer is null"); return; }
            if (!color_rgb) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Color pointer is null"); return; }
            std::vector<unsigned int> v(objIDs, objIDs + count);
            context->setObjectColor(v, helios::RGBcolor(color_rgb[0], color_rgb[1], color_rgb[2]));
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setObjectColor): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setObjectColor): Unknown error.");
        }
    }

    PYHELIOS_API void setObjectColorRGBA(helios::Context* context, unsigned int objID, float* color_rgba) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!color_rgba) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Color pointer is null"); return; }
            context->setObjectColor(objID, helios::RGBAcolor(color_rgba[0], color_rgba[1], color_rgba[2], color_rgba[3]));
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setObjectColor): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setObjectColor): Unknown error.");
        }
    }

    PYHELIOS_API void setObjectColorRGBABatch(helios::Context* context, unsigned int* objIDs, unsigned int count, float* color_rgba) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!objIDs && count > 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ObjIDs pointer is null"); return; }
            if (!color_rgba) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Color pointer is null"); return; }
            std::vector<unsigned int> v(objIDs, objIDs + count);
            context->setObjectColor(v, helios::RGBAcolor(color_rgba[0], color_rgba[1], color_rgba[2], color_rgba[3]));
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setObjectColor): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setObjectColor): Unknown error.");
        }
    }

    PYHELIOS_API void overrideObjectTextureColor(helios::Context* context, unsigned int objID) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            context->overrideObjectTextureColor(objID);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::overrideObjectTextureColor): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::overrideObjectTextureColor): Unknown error.");
        }
    }

    PYHELIOS_API void overrideObjectTextureColorBatch(helios::Context* context, unsigned int* objIDs, unsigned int count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!objIDs && count > 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ObjIDs pointer is null"); return; }
            std::vector<unsigned int> v(objIDs, objIDs + count);
            context->overrideObjectTextureColor(v);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::overrideObjectTextureColor): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::overrideObjectTextureColor): Unknown error.");
        }
    }

    PYHELIOS_API void useObjectTextureColor(helios::Context* context, unsigned int objID) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            context->useObjectTextureColor(objID);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::useObjectTextureColor): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::useObjectTextureColor): Unknown error.");
        }
    }

    PYHELIOS_API void useObjectTextureColorBatch(helios::Context* context, unsigned int* objIDs, unsigned int count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!objIDs && count > 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ObjIDs pointer is null"); return; }
            std::vector<unsigned int> v(objIDs, objIDs + count);
            context->useObjectTextureColor(v);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::useObjectTextureColor): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::useObjectTextureColor): Unknown error.");
        }
    }

    // ---- Mark primitive dirty/clean ----

    PYHELIOS_API void markPrimitiveDirty(helios::Context* context, unsigned int uuid) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            context->markPrimitiveDirty(uuid);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::markPrimitiveDirty): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::markPrimitiveDirty): Unknown error.");
        }
    }

    PYHELIOS_API void markPrimitiveDirtyBatch(helios::Context* context, unsigned int* uuids, unsigned int count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!uuids && count > 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs pointer is null"); return; }
            std::vector<unsigned int> v(uuids, uuids + count);
            context->markPrimitiveDirty(v);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::markPrimitiveDirty): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::markPrimitiveDirty): Unknown error.");
        }
    }

    PYHELIOS_API void markPrimitiveClean(helios::Context* context, unsigned int uuid) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            context->markPrimitiveClean(uuid);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::markPrimitiveClean): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::markPrimitiveClean): Unknown error.");
        }
    }

    PYHELIOS_API void markPrimitiveCleanBatch(helios::Context* context, unsigned int* uuids, unsigned int count) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!uuids && count > 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs pointer is null"); return; }
            std::vector<unsigned int> v(uuids, uuids + count);
            context->markPrimitiveClean(v);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::markPrimitiveClean): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::markPrimitiveClean): Unknown error.");
        }
    }

    // ---- Tile subdivision ----

    PYHELIOS_API void setTileObjectSubdivisionCount(helios::Context* context, unsigned int* objIDs, unsigned int count, int subdiv_x, int subdiv_y) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!objIDs && count > 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ObjIDs pointer is null"); return; }
            std::vector<unsigned int> v(objIDs, objIDs + count);
            context->setTileObjectSubdivisionCount(v, helios::int2(subdiv_x, subdiv_y));
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setTileObjectSubdivisionCount): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setTileObjectSubdivisionCount): Unknown error.");
        }
    }

    PYHELIOS_API void setTileObjectSubdivisionByAreaRatio(helios::Context* context, unsigned int* objIDs, unsigned int count, float area_ratio) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!objIDs && count > 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ObjIDs pointer is null"); return; }
            std::vector<unsigned int> v(objIDs, objIDs + count);
            context->setTileObjectSubdivisionCount(v, area_ratio);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setTileObjectSubdivisionByAreaRatio): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setTileObjectSubdivisionByAreaRatio): Unknown error.");
        }
    }

    //=========================================================================
    // Cleanup, XML write, RNG, Location
    //=========================================================================

    // ---- Cleanup helpers ----
    // The C++ method mutates a vector<uint> in-place. We accept input via uuids_in,
    // copy into a thread_local buffer, mutate, then return its data() so the Python
    // wrapper can copy out before any subsequent call invalidates the buffer.

    PYHELIOS_API unsigned int* cleanDeletedUUIDs(helios::Context* context, unsigned int* uuids_in, unsigned int count_in, unsigned int* count_out) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); if (count_out) *count_out = 0; return nullptr; }
            if (!count_out) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count out-pointer is null"); return nullptr; }
            if (!uuids_in && count_in > 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs pointer is null"); *count_out = 0; return nullptr; }
            static thread_local std::vector<unsigned int> buf;
            buf.assign(uuids_in, uuids_in + count_in);
            context->cleanDeletedUUIDs(buf);
            *count_out = (unsigned int)buf.size();
            return buf.empty() ? nullptr : buf.data();
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); if (count_out) *count_out = 0; return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::cleanDeletedUUIDs): ") + e.what()); if (count_out) *count_out = 0; return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::cleanDeletedUUIDs): Unknown error."); if (count_out) *count_out = 0; return nullptr;
        }
    }

    PYHELIOS_API unsigned int* cleanDeletedObjectIDs(helios::Context* context, unsigned int* objIDs_in, unsigned int count_in, unsigned int* count_out) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); if (count_out) *count_out = 0; return nullptr; }
            if (!count_out) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count out-pointer is null"); return nullptr; }
            if (!objIDs_in && count_in > 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ObjIDs pointer is null"); *count_out = 0; return nullptr; }
            static thread_local std::vector<unsigned int> buf;
            buf.assign(objIDs_in, objIDs_in + count_in);
            context->cleanDeletedObjectIDs(buf);
            *count_out = (unsigned int)buf.size();
            return buf.empty() ? nullptr : buf.data();
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); if (count_out) *count_out = 0; return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::cleanDeletedObjectIDs): ") + e.what()); if (count_out) *count_out = 0; return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::cleanDeletedObjectIDs): Unknown error."); if (count_out) *count_out = 0; return nullptr;
        }
    }

    // ---- XML write ----

    PYHELIOS_API void writeXML(helios::Context* context, const char* filename, bool quiet) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!filename) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null"); return; }
            context->writeXML(filename, quiet);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::writeXML): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::writeXML): Unknown error.");
        }
    }

    PYHELIOS_API void writeXMLFiltered(helios::Context* context, const char* filename, unsigned int* uuids, unsigned int count, bool quiet) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!filename) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null"); return; }
            if (!uuids && count > 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs pointer is null"); return; }
            std::vector<unsigned int> v(uuids, uuids + count);
            context->writeXML(filename, v, quiet);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::writeXML): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::writeXML): Unknown error.");
        }
    }

    PYHELIOS_API void writeXML_byobject(helios::Context* context, const char* filename, unsigned int* objIDs, unsigned int count, bool quiet) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!filename) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null"); return; }
            if (!objIDs && count > 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ObjIDs pointer is null"); return; }
            std::vector<unsigned int> v(objIDs, objIDs + count);
            context->writeXML_byobject(filename, v, quiet);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::writeXML_byobject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::writeXML_byobject): Unknown error.");
        }
    }

    // ---- RNG ----

    PYHELIOS_API float randu_basic(helios::Context* context) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0.0f; }
            return context->randu();
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0.0f;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::randu): ") + e.what()); return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::randu): Unknown error."); return 0.0f;
        }
    }

    PYHELIOS_API float randu_range(helios::Context* context, float min, float max) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0.0f; }
            return context->randu(min, max);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0.0f;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::randu): ") + e.what()); return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::randu): Unknown error."); return 0.0f;
        }
    }

    PYHELIOS_API int randu_int_range(helios::Context* context, int min, int max) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            return context->randu(min, max);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::randu): ") + e.what()); return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::randu): Unknown error."); return 0;
        }
    }

    PYHELIOS_API float randn_basic(helios::Context* context) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0.0f; }
            return context->randn();
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0.0f;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::randn): ") + e.what()); return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::randn): Unknown error."); return 0.0f;
        }
    }

    PYHELIOS_API float randn_params(helios::Context* context, float mean, float stddev) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0.0f; }
            return context->randn(mean, stddev);
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0.0f;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::randn): ") + e.what()); return 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::randn): Unknown error."); return 0.0f;
        }
    }

    // ---- Location ----

    PYHELIOS_API void setLocation(helios::Context* context, float latitude_deg, float longitude_deg, float utc_offset) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            context->setLocation(helios::Location(latitude_deg, longitude_deg, utc_offset));
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::setLocation): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::setLocation): Unknown error.");
        }
    }

    PYHELIOS_API void getLocation(helios::Context* context, float* latitude_deg_out, float* longitude_deg_out, float* utc_offset_out) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return; }
            if (!latitude_deg_out || !longitude_deg_out || !utc_offset_out) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output pointer is null");
                return;
            }
            helios::Location loc = context->getLocation();
            *latitude_deg_out = loc.latitude_deg;
            *longitude_deg_out = loc.longitude_deg;
            *utc_offset_out = loc.UTC_offset;
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getLocation): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getLocation): Unknown error.");
        }
    }

    //=========================================================================
    // Colormap helpers + texture transparency
    //=========================================================================

    namespace {
        // Thread-local caches for variable-length returns.
        thread_local std::vector<float> s_colormap_rgb_cache;
        thread_local std::vector<std::string> s_colormap_texture_paths_cache;
        thread_local std::vector<unsigned char> s_transparency_buffer_cache;
    }

    PYHELIOS_API float* generateColormapNamed(helios::Context* context, const char* colormap_name, unsigned int n_colors, unsigned int* count_out) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); if (count_out) *count_out = 0; return nullptr; }
            if (!colormap_name) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Colormap name is null"); if (count_out) *count_out = 0; return nullptr; }
            if (!count_out) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count out-pointer is null"); return nullptr; }
            auto rgb_vec = context->generateColormap(std::string(colormap_name), n_colors);
            s_colormap_rgb_cache.clear();
            s_colormap_rgb_cache.reserve(rgb_vec.size() * 3);
            for (const auto& c : rgb_vec) {
                s_colormap_rgb_cache.push_back(c.r);
                s_colormap_rgb_cache.push_back(c.g);
                s_colormap_rgb_cache.push_back(c.b);
            }
            *count_out = (unsigned int)rgb_vec.size();
            return s_colormap_rgb_cache.empty() ? nullptr : s_colormap_rgb_cache.data();
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); if (count_out) *count_out = 0; return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::generateColormap): ") + e.what()); if (count_out) *count_out = 0; return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::generateColormap): Unknown error."); if (count_out) *count_out = 0; return nullptr;
        }
    }

    PYHELIOS_API unsigned int generateTexturesFromColormapCount(helios::Context* context, const char* texture_file, float* colormap_rgb_flat, unsigned int n_colors) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!texture_file) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Texture file is null"); return 0; }
            if (!colormap_rgb_flat && n_colors > 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Colormap RGB pointer is null"); return 0; }
            std::vector<helios::RGBcolor> colormap;
            colormap.reserve(n_colors);
            for (unsigned int i = 0; i < n_colors; ++i) {
                colormap.emplace_back(colormap_rgb_flat[i*3 + 0], colormap_rgb_flat[i*3 + 1], colormap_rgb_flat[i*3 + 2]);
            }
            s_colormap_texture_paths_cache = context->generateTexturesFromColormap(std::string(texture_file), colormap);
            return (unsigned int)s_colormap_texture_paths_cache.size();
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::generateTexturesFromColormap): ") + e.what()); return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::generateTexturesFromColormap): Unknown error."); return 0;
        }
    }

    // Pure cache reader: must be preceded by generateTexturesFromColormapCount, which
    // populates s_colormap_texture_paths_cache. context/label are intentionally ignored.
    PYHELIOS_API int generateTexturesFromColormapPath(helios::Context* /*context*/, unsigned int index, char* buffer, int buffer_size) {
        clearError();
        try {
            if (!buffer || buffer_size <= 0) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Buffer is null or has non-positive size"); return 0; }
            if (index >= s_colormap_texture_paths_cache.size()) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Index out of range; call generateTexturesFromColormapCount() first.");
                return 0;
            }
            const std::string& value = s_colormap_texture_paths_cache[index];
            int copy_length = std::min((int)value.length(), buffer_size - 1);
            std::strncpy(buffer, value.c_str(), copy_length);
            buffer[copy_length] = '\0';
            return copy_length;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::generateTexturesFromColormapPath): ") + e.what()); return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::generateTexturesFromColormapPath): Unknown error."); return 0;
        }
    }

    PYHELIOS_API int getPrimitiveTextureTransparencyDataInfo(helios::Context* context, unsigned int uuid, unsigned int* width_out, unsigned int* height_out) {
        clearError();
        try {
            if (!context) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null"); return 0; }
            if (!width_out || !height_out) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output pointer is null"); return 0; }
            // Probe for transparency channel first; the Helios C++ getter throws
            // runtime_error if absent, but our Python contract is to return None.
            if (!context->primitiveTextureHasTransparencyChannel(uuid)) {
                *width_out = 0; *height_out = 0;
                s_transparency_buffer_cache.clear();
                return 0;
            }
            const std::vector<std::vector<bool>>* data = context->getPrimitiveTextureTransparencyData(uuid);
            if (!data || data->empty()) {
                *width_out = 0; *height_out = 0;
                s_transparency_buffer_cache.clear();
                return 0;
            }
            unsigned int height = (unsigned int)data->size();
            unsigned int width = (unsigned int)((*data)[0].size());
            // Flatten into a thread_local byte buffer; `bool` -> `unsigned char` cast for ctypes safety.
            s_transparency_buffer_cache.clear();
            s_transparency_buffer_cache.reserve((size_t)width * height);
            for (unsigned int row = 0; row < height; ++row) {
                const auto& row_vec = (*data)[row];
                for (unsigned int col = 0; col < width; ++col) {
                    s_transparency_buffer_cache.push_back(row_vec[col] ? 1 : 0);
                }
            }
            *width_out = width;
            *height_out = height;
            return 1;
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what()); if (width_out) *width_out = 0; if (height_out) *height_out = 0; return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Context::getPrimitiveTextureTransparencyData): ") + e.what()); if (width_out) *width_out = 0; if (height_out) *height_out = 0; return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Context::getPrimitiveTextureTransparencyData): Unknown error."); if (width_out) *width_out = 0; if (height_out) *height_out = 0; return 0;
        }
    }

    // Returns the buffer populated by the most recent
    // getPrimitiveTextureTransparencyDataInfo call on this thread. Callers must invoke
    // Info first; the context/uuid arguments are intentionally ignored. The Python
    // wrapper getPrimitiveTextureTransparencyDataWrapper fuses both calls so users
    // never observe the intermediate state.
    PYHELIOS_API unsigned char* getPrimitiveTextureTransparencyDataBuffer(helios::Context* /*context*/, unsigned int /*uuid*/) {
        return s_transparency_buffer_cache.empty() ? nullptr : s_transparency_buffer_cache.data();
    }

} //extern "C"
