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

} //extern "C"
