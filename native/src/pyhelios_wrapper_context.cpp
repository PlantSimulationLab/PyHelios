// PyHelios C Interface - Context Functions
// Provides Context creation, geometry management, primitive operations, and data functions

#include "../include/pyhelios_wrapper_common.h"
#include "../include/pyhelios_wrapper_context.h"
#include "Context.h"
#include <string>
#include <exception>
#include <cstring>

extern "C" {
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

    // Missing loadPLY overloads
    unsigned int* loadPLYBasic(helios::Context* context, const char* filename, bool silent, unsigned int* size) {
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

    unsigned int* loadPLYWithOriginHeightRotation(helios::Context* context, const char* filename, float* origin, float height, float* rotation, const char* upaxis, bool silent, unsigned int* size) {
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

    unsigned int* loadPLYWithOriginHeightColor(helios::Context* context, const char* filename, float* origin, float height, float* color, const char* upaxis, bool silent, unsigned int* size) {
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

    unsigned int* loadPLYWithOriginHeightRotationColor(helios::Context* context, const char* filename, float* origin, float height, float* rotation, float* color, const char* upaxis, bool silent, unsigned int* size) {
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
    unsigned int* loadOBJ(helios::Context* context, const char* filename, bool silent, unsigned int* size) {
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

    unsigned int* loadOBJWithOriginHeightRotationColor(helios::Context* context, const char* filename, float* origin, float height, float* rotation, float* color, bool silent, unsigned int* size) {
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

    unsigned int* loadOBJWithOriginHeightRotationColorUpaxis(helios::Context* context, const char* filename, float* origin, float height, float* rotation, float* color, const char* upaxis, bool silent, unsigned int* size) {
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

    unsigned int* loadOBJWithOriginScaleRotationColorUpaxis(helios::Context* context, const char* filename, float* origin, float* scale, float* rotation, float* color, const char* upaxis, bool silent, unsigned int* size) {
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
    unsigned int* loadXML(helios::Context* context, const char* filename, bool quiet, unsigned int* size) {
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

    // Context time/date management functions for solar position integration
    void setTime_HourMinute(helios::Context* context, int hour, int minute) {
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
    
    void setTime_HourMinuteSecond(helios::Context* context, int hour, int minute, int second) {
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
    
    void setDate_DayMonthYear(helios::Context* context, int day, int month, int year) {
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
    
    void setDate_JulianDay(helios::Context* context, int julian_day, int year) {
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
    
    void getTime(helios::Context* context, int* hour, int* minute, int* second) {
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
    
    void getDate(helios::Context* context, int* day, int* month, int* year) {
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

    void writePLY(helios::Context* context, const char* filename) {
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

    void writePLYWithUUIDs(helios::Context* context, const char* filename, unsigned int* uuids, unsigned int count) {
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

    void writeOBJ(helios::Context* context, const char* filename, bool write_normals, bool silent) {
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

    void writeOBJWithUUIDs(helios::Context* context, const char* filename, unsigned int* uuids, unsigned int count, bool write_normals, bool silent) {
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

    void writeOBJWithPrimitiveData(helios::Context* context, const char* filename, unsigned int* uuids, unsigned int count, const char** data_fields, unsigned int field_count, bool write_normals, bool silent) {
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


} //extern "C"
