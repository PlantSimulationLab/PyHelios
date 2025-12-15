// PyHelios C Interface - Visualizer Functions
// Provides OpenGL-based 3D visualization and rendering functions

#include "../include/pyhelios_wrapper_common.h"
#include "../include/pyhelios_wrapper_context.h"
#include "Context.h"
#include <string>
#include <exception>

#ifdef VISUALIZER_PLUGIN_AVAILABLE
#include "../include/pyhelios_wrapper_visualizer.h"
#include "Visualizer.h"

extern "C" {
    
    //=============================================================================
    // Visualizer Functions
    //=============================================================================

    PYHELIOS_API Visualizer* createVisualizer(unsigned int width, unsigned int height, bool headless) {
        try {
            clearError();
            // Enable window decorations by default (true), headless parameter controls window visibility
            return new Visualizer(width, height, 4, true, headless); // 4 antialiasing samples, decorations enabled
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (createVisualizer): Failed to create visualizer: ") + e.what());
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (createVisualizer): Unknown error creating visualizer. This may indicate OpenGL/graphics initialization problems in headless environments.");
            return nullptr;
        }
    }
    
    PYHELIOS_API Visualizer* createVisualizerWithAntialiasing(unsigned int width, unsigned int height, unsigned int samples, bool headless) {
        try {
            clearError();
            // Enable window decorations by default (true), headless parameter controls window visibility  
            return new Visualizer(width, height, samples, true, headless);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (createVisualizerWithAntialiasing): Failed to create visualizer: ") + e.what());
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (createVisualizerWithAntialiasing): Unknown error creating visualizer. This may indicate OpenGL/graphics initialization problems in headless environments.");
            return nullptr;
        }
    }
    
    PYHELIOS_API void destroyVisualizer(Visualizer* visualizer) {
        delete visualizer;
    }
    
    PYHELIOS_API void buildContextGeometry(Visualizer* visualizer, helios::Context* context) {
        visualizer->buildContextGeometry(context);
    }
    
    PYHELIOS_API void buildContextGeometryUUIDs(Visualizer* visualizer, helios::Context* context, unsigned int* uuids, unsigned int count) {
        std::vector<unsigned int> uuid_vector(uuids, uuids + count);
        visualizer->buildContextGeometry(context, uuid_vector);
    }
    
    PYHELIOS_API void plotInteractive(Visualizer* visualizer) {
        visualizer->plotInteractive();
    }
    
    PYHELIOS_API void plotUpdate(Visualizer* visualizer) {
        visualizer->plotUpdate();
    }
    
    PYHELIOS_API void printWindow(Visualizer* visualizer, const char* filename) {
        visualizer->printWindow(filename);
    }
    
    PYHELIOS_API void closeWindow(Visualizer* visualizer) {
        visualizer->closeWindow();
    }
    
    PYHELIOS_API void setBackgroundColor(Visualizer* visualizer, float* color) {
        helios::RGBcolor bg_color(color[0], color[1], color[2]);
        visualizer->setBackgroundColor(bg_color);
    }
    
    PYHELIOS_API void setLightDirection(Visualizer* visualizer, float* direction) {
        helios::vec3 light_dir(direction[0], direction[1], direction[2]);
        visualizer->setLightDirection(light_dir);
    }
    
    PYHELIOS_API void setCameraPosition(Visualizer* visualizer, float* position, float* lookat) {
        helios::vec3 camera_pos(position[0], position[1], position[2]);
        helios::vec3 look_at(lookat[0], lookat[1], lookat[2]);
        visualizer->setCameraPosition(camera_pos, look_at);
    }
    
    PYHELIOS_API void setCameraPositionSpherical(Visualizer* visualizer, float* angle, float* lookat) {
        // angle array: [radius, elevation, azimuth] - create SphericalCoord properly
        helios::SphericalCoord camera_angle = helios::make_SphericalCoord(angle[0], angle[1], angle[2]);
        helios::vec3 look_at(lookat[0], lookat[1], lookat[2]);
        visualizer->setCameraPosition(camera_angle, look_at);
    }
    
    PYHELIOS_API void setLightingModel(Visualizer* visualizer, unsigned int model) {
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
    
    PYHELIOS_API bool validateTextureFile(const char* texture_file) {
        std::string filename(texture_file);
        return ::validateTextureFile(filename);
    }
    
    PYHELIOS_API void colorContextPrimitivesByData(Visualizer* visualizer, const char* data_name) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (!data_name) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Data name is null");
                return;
            }
            
            visualizer->colorContextPrimitivesByData(data_name);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Visualizer::colorContextPrimitivesByData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Visualizer::colorContextPrimitivesByData): Unknown error coloring primitives by data.");
        }
    }
    
    PYHELIOS_API void colorContextPrimitivesByDataUUIDs(Visualizer* visualizer, const char* data_name, unsigned int* uuids, unsigned int count) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (!data_name) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Data name is null");
                return;
            }
            if (!uuids && count > 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUID array is null but count > 0");
                return;
            }
            
            std::vector<unsigned int> uuid_vector(uuids, uuids + count);
            visualizer->colorContextPrimitivesByData(data_name, uuid_vector);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (Visualizer::colorContextPrimitivesByData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (Visualizer::colorContextPrimitivesByData): Unknown error coloring primitives by data with UUIDs.");
        }
    }

    // Camera Control Functions
    PYHELIOS_API void setCameraFieldOfView(Visualizer* visualizer, float angle_FOV) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            visualizer->setCameraFieldOfView(angle_FOV);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setCameraFieldOfView): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setCameraFieldOfView): Unknown error");
        }
    }

    PYHELIOS_API void getCameraPosition(Visualizer* visualizer, float* camera_position, float* look_at_point) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (!camera_position || !look_at_point) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output arrays cannot be null");
                return;
            }
            
            std::vector<helios::vec3> positions = visualizer->getCameraPosition();
            if (positions.size() >= 2) {
                // positions[0] is look-at center, positions[1] is camera eye location
                look_at_point[0] = positions[0].x;
                look_at_point[1] = positions[0].y;
                look_at_point[2] = positions[0].z;
                
                camera_position[0] = positions[1].x;
                camera_position[1] = positions[1].y;
                camera_position[2] = positions[1].z;
            }
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getCameraPosition): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getCameraPosition): Unknown error");
        }
    }

    PYHELIOS_API void getBackgroundColor(Visualizer* visualizer, float* color) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (!color) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Color output array cannot be null");
                return;
            }
            
            helios::RGBcolor bg_color = visualizer->getBackgroundColor();
            color[0] = bg_color.r;
            color[1] = bg_color.g;
            color[2] = bg_color.b;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getBackgroundColor): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getBackgroundColor): Unknown error");
        }
    }

    // Lighting Control Functions
    PYHELIOS_API void setLightIntensityFactor(Visualizer* visualizer, float intensity_factor) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            visualizer->setLightIntensityFactor(intensity_factor);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setLightIntensityFactor): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setLightIntensityFactor): Unknown error");
        }
    }

    // Window and Display Functions
    PYHELIOS_API void getWindowSize(Visualizer* visualizer, unsigned int* width, unsigned int* height) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (!width || !height) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Width and height output pointers cannot be null");
                return;
            }
            
            uint w, h;
            visualizer->getWindowSize(w, h);
            *width = w;
            *height = h;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getWindowSize): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getWindowSize): Unknown error");
        }
    }

    PYHELIOS_API void getFramebufferSize(Visualizer* visualizer, unsigned int* width, unsigned int* height) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (!width || !height) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Width and height output pointers cannot be null");
                return;
            }
            
            uint w, h;
            visualizer->getFramebufferSize(w, h);
            *width = w;
            *height = h;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getFramebufferSize): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getFramebufferSize): Unknown error");
        }
    }

    PYHELIOS_API void printWindowDefault(Visualizer* visualizer) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            visualizer->printWindow();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (printWindowDefault): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (printWindowDefault): Unknown error");
        }
    }

    PYHELIOS_API void displayImageFromPixels(Visualizer* visualizer, unsigned char* pixel_data, unsigned int width_pixels, unsigned int height_pixels) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (!pixel_data) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Pixel data array cannot be null");
                return;
            }
            if (width_pixels == 0 || height_pixels == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Width and height must be positive");
                return;
            }
            
            // Convert raw array to vector
            size_t data_size = width_pixels * height_pixels * 4; // RGBA format
            std::vector<unsigned char> pixel_vector(pixel_data, pixel_data + data_size);
            
            visualizer->displayImage(pixel_vector, width_pixels, height_pixels);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (displayImageFromPixels): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (displayImageFromPixels): Unknown error");
        }
    }

    PYHELIOS_API void displayImageFromFile(Visualizer* visualizer, const char* file_name) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (!file_name) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "File name cannot be null");
                return;
            }
            
            std::string filename_str(file_name);
            visualizer->displayImage(filename_str);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (displayImageFromFile): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (displayImageFromFile): Unknown error");
        }
    }

    // Window Data Access Functions
    PYHELIOS_API void getWindowPixelsRGB(Visualizer* visualizer, unsigned int* buffer) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (!buffer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Buffer pointer cannot be null");
                return;
            }
            
            visualizer->getWindowPixelsRGB(buffer);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getWindowPixelsRGB): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getWindowPixelsRGB): Unknown error");
        }
    }

    PYHELIOS_API void getDepthMap(Visualizer* visualizer, float** depth_pixels, unsigned int* width_pixels, unsigned int* height_pixels, unsigned int* buffer_size) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (!depth_pixels || !width_pixels || !height_pixels || !buffer_size) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output pointers cannot be null");
                return;
            }
            
            // Use static storage for return data
            static thread_local std::vector<float> static_depth_data;
            uint w, h;
            
            visualizer->getDepthMap(static_depth_data, w, h);
            
            *width_pixels = w;
            *height_pixels = h;
            *buffer_size = static_depth_data.size();
            *depth_pixels = static_depth_data.data();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getDepthMap): ") + e.what());
            if (depth_pixels) *depth_pixels = nullptr;
            if (width_pixels) *width_pixels = 0;
            if (height_pixels) *height_pixels = 0;
            if (buffer_size) *buffer_size = 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getDepthMap): Unknown error");
            if (depth_pixels) *depth_pixels = nullptr;
            if (width_pixels) *width_pixels = 0;
            if (height_pixels) *height_pixels = 0;
            if (buffer_size) *buffer_size = 0;
        }
    }

    PYHELIOS_API void plotDepthMap(Visualizer* visualizer) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            visualizer->plotDepthMap();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (plotDepthMap): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (plotDepthMap): Unknown error");
        }
    }

    // Geometry Management Functions
    PYHELIOS_API void clearGeometry(Visualizer* visualizer) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            visualizer->clearGeometry();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (clearGeometry): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (clearGeometry): Unknown error");
        }
    }

    PYHELIOS_API void clearContextGeometry(Visualizer* visualizer) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            visualizer->clearContextGeometry();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (clearContextGeometry): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (clearContextGeometry): Unknown error");
        }
    }

    PYHELIOS_API void deleteGeometry(Visualizer* visualizer, unsigned int geometry_id) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            visualizer->deleteGeometry(static_cast<size_t>(geometry_id));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (deleteGeometry): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (deleteGeometry): Unknown error");
        }
    }

    PYHELIOS_API void updateContextPrimitiveColors(Visualizer* visualizer) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            visualizer->updateContextPrimitiveColors();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (updateContextPrimitiveColors): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (updateContextPrimitiveColors): Unknown error");
        }
    }

    // Coordinate Axes and Grid Functions
    PYHELIOS_API void addCoordinateAxes(Visualizer* visualizer) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            visualizer->addCoordinateAxes();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (addCoordinateAxes): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (addCoordinateAxes): Unknown error");
        }
    }

    PYHELIOS_API void addCoordinateAxesCustom(Visualizer* visualizer, float* origin, float* length, const char* sign_string) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (!origin || !length || !sign_string) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameters cannot be null");
                return;
            }
            
            helios::vec3 origin_vec(origin[0], origin[1], origin[2]);
            helios::vec3 length_vec(length[0], length[1], length[2]);
            std::string sign_str(sign_string);
            
            visualizer->addCoordinateAxes(origin_vec, length_vec, sign_str);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (addCoordinateAxesCustom): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (addCoordinateAxesCustom): Unknown error");
        }
    }

    PYHELIOS_API void disableCoordinateAxes(Visualizer* visualizer) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            visualizer->disableCoordinateAxes();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (disableCoordinateAxes): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (disableCoordinateAxes): Unknown error");
        }
    }

    PYHELIOS_API void addGridWireFrame(Visualizer* visualizer, float* center, float* size, int* subdivisions) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (!center || !size || !subdivisions) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameters cannot be null");
                return;
            }
            
            helios::vec3 center_vec(center[0], center[1], center[2]);
            helios::vec3 size_vec(size[0], size[1], size[2]);
            helios::int3 subdiv_int3(subdivisions[0], subdivisions[1], subdivisions[2]);
            
            visualizer->addGridWireFrame(center_vec, size_vec, subdiv_int3);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (addGridWireFrame): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (addGridWireFrame): Unknown error");
        }
    }

    // Colorbar Control Functions
    PYHELIOS_API void enableColorbar(Visualizer* visualizer) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            visualizer->enableColorbar();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (enableColorbar): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (enableColorbar): Unknown error");
        }
    }

    PYHELIOS_API void disableColorbar(Visualizer* visualizer) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            visualizer->disableColorbar();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (disableColorbar): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (disableColorbar): Unknown error");
        }
    }

    PYHELIOS_API void setColorbarPosition(Visualizer* visualizer, float* position) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (!position) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Position array cannot be null");
                return;
            }
            
            helios::vec3 pos_vec(position[0], position[1], position[2]);
            visualizer->setColorbarPosition(pos_vec);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setColorbarPosition): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setColorbarPosition): Unknown error");
        }
    }

    PYHELIOS_API void setColorbarSize(Visualizer* visualizer, float* size) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (!size) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Size array cannot be null");
                return;
            }
            
            helios::vec2 size_vec(size[0], size[1]);
            visualizer->setColorbarSize(size_vec);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setColorbarSize): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setColorbarSize): Unknown error");
        }
    }

    PYHELIOS_API void setColorbarRange(Visualizer* visualizer, float min_val, float max_val) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            visualizer->setColorbarRange(min_val, max_val);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setColorbarRange): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setColorbarRange): Unknown error");
        }
    }

    PYHELIOS_API void setColorbarTicks(Visualizer* visualizer, float* ticks, unsigned int count) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (!ticks && count > 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Ticks array is null but count > 0");
                return;
            }
            
            std::vector<float> ticks_vector;
            if (count > 0) {
                ticks_vector.assign(ticks, ticks + count);
            }
            visualizer->setColorbarTicks(ticks_vector);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setColorbarTicks): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setColorbarTicks): Unknown error");
        }
    }

    PYHELIOS_API void setColorbarTitle(Visualizer* visualizer, const char* title) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (!title) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Title cannot be null");
                return;
            }
            
            visualizer->setColorbarTitle(title);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setColorbarTitle): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setColorbarTitle): Unknown error");
        }
    }

    PYHELIOS_API void setColorbarFontColor(Visualizer* visualizer, float* color) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (!color) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Color array cannot be null");
                return;
            }
            
            helios::RGBcolor font_color(color[0], color[1], color[2]);
            visualizer->setColorbarFontColor(font_color);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setColorbarFontColor): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setColorbarFontColor): Unknown error");
        }
    }

    PYHELIOS_API void setColorbarFontSize(Visualizer* visualizer, unsigned int font_size) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            visualizer->setColorbarFontSize(font_size);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setColorbarFontSize): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setColorbarFontSize): Unknown error");
        }
    }

    // Colormap Functions
    PYHELIOS_API void setColormap(Visualizer* visualizer, unsigned int colormap_id) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            
            Visualizer::Ctable colormap;
            switch (colormap_id) {
                case 0: colormap = Visualizer::COLORMAP_HOT; break;
                case 1: colormap = Visualizer::COLORMAP_COOL; break;
                case 2: colormap = Visualizer::COLORMAP_RAINBOW; break;
                case 3: colormap = Visualizer::COLORMAP_LAVA; break;
                case 4: colormap = Visualizer::COLORMAP_PARULA; break;
                case 5: colormap = Visualizer::COLORMAP_GRAY; break;
                default:
                    setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Invalid colormap ID (must be 0-5)");
                    return;
            }
            
            visualizer->setColormap(colormap);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setColormap): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setColormap): Unknown error");
        }
    }

    PYHELIOS_API void setCustomColormap(Visualizer* visualizer, float* colors, float* divisions, unsigned int count) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (!colors || !divisions) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Colors and divisions arrays cannot be null");
                return;
            }
            if (count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count must be greater than 0");
                return;
            }
            
            std::vector<helios::RGBcolor> color_vector;
            std::vector<float> divisions_vector;
            
            color_vector.reserve(count);
            divisions_vector.reserve(count);
            
            for (unsigned int i = 0; i < count; i++) {
                color_vector.emplace_back(colors[i*3], colors[i*3+1], colors[i*3+2]);
                divisions_vector.push_back(divisions[i]);
            }
            
            visualizer->setColormap(color_vector, divisions_vector);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setCustomColormap): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setCustomColormap): Unknown error");
        }
    }

    // Object/Primitive Coloring Functions
    PYHELIOS_API void colorContextPrimitivesByObjectData(Visualizer* visualizer, const char* data_name) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (!data_name) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Data name cannot be null");
                return;
            }
            
            visualizer->colorContextPrimitivesByObjectData(data_name);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (colorContextPrimitivesByObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (colorContextPrimitivesByObjectData): Unknown error");
        }
    }

    PYHELIOS_API void colorContextPrimitivesByObjectDataIDs(Visualizer* visualizer, const char* data_name, unsigned int* obj_ids, unsigned int count) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (!data_name) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Data name cannot be null");
                return;
            }
            if (!obj_ids && count > 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Object IDs array is null but count > 0");
                return;
            }
            
            std::vector<unsigned int> obj_ids_vector;
            if (count > 0) {
                obj_ids_vector.assign(obj_ids, obj_ids + count);
            }
            visualizer->colorContextPrimitivesByObjectData(data_name, obj_ids_vector);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (colorContextPrimitivesByObjectDataIDs): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (colorContextPrimitivesByObjectDataIDs): Unknown error");
        }
    }

    PYHELIOS_API void colorContextPrimitivesRandomly(Visualizer* visualizer, unsigned int* uuids, unsigned int count) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            
            if (count == 0) {
                // Color all primitives randomly
                visualizer->colorContextPrimitivesRandomly();
            } else {
                if (!uuids) {
                    setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUID array is null but count > 0");
                    return;
                }
                std::vector<unsigned int> uuid_vector(uuids, uuids + count);
                visualizer->colorContextPrimitivesRandomly(uuid_vector);
            }
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (colorContextPrimitivesRandomly): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (colorContextPrimitivesRandomly): Unknown error");
        }
    }

    PYHELIOS_API void colorContextObjectsRandomly(Visualizer* visualizer, unsigned int* obj_ids, unsigned int count) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            
            if (count == 0) {
                // Color all objects randomly
                visualizer->colorContextObjectsRandomly();
            } else {
                if (!obj_ids) {
                    setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Object IDs array is null but count > 0");
                    return;
                }
                std::vector<unsigned int> obj_ids_vector(obj_ids, obj_ids + count);
                visualizer->colorContextObjectsRandomly(obj_ids_vector);
            }
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (colorContextObjectsRandomly): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (colorContextObjectsRandomly): Unknown error");
        }
    }

    PYHELIOS_API void clearColor(Visualizer* visualizer) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            visualizer->clearColor();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (clearColor): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (clearColor): Unknown error");
        }
    }

    // Watermark Control Functions
    PYHELIOS_API void hideWatermark(Visualizer* visualizer) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            visualizer->hideWatermark();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (hideWatermark): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (hideWatermark): Unknown error");
        }
    }

    PYHELIOS_API void showWatermark(Visualizer* visualizer) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            visualizer->showWatermark();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (showWatermark): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (showWatermark): Unknown error");
        }
    }

    PYHELIOS_API void updateWatermark(Visualizer* visualizer) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            visualizer->updateWatermark();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (updateWatermark): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (updateWatermark): Unknown error");
        }
    }

    // Performance and Utility Functions
    PYHELIOS_API void enableMessages(Visualizer* visualizer) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            visualizer->enableMessages();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (enableMessages): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (enableMessages): Unknown error");
        }
    }

    PYHELIOS_API void disableMessages(Visualizer* visualizer) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            visualizer->disableMessages();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (disableMessages): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (disableMessages): Unknown error");
        }
    }

    PYHELIOS_API void plotOnce(Visualizer* visualizer, bool get_keystrokes) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            visualizer->plotOnce(get_keystrokes);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (plotOnce): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (plotOnce): Unknown error");
        }
    }

    PYHELIOS_API void plotUpdateWithVisibility(Visualizer* visualizer, bool hide_window) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            visualizer->plotUpdate(hide_window);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (plotUpdateWithVisibility): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (plotUpdateWithVisibility): Unknown error");
        }
    }

    // v1.3.53 Background Control Functions
    PYHELIOS_API void setBackgroundTransparent(Visualizer* visualizer) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            visualizer->setBackgroundTransparent();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setBackgroundTransparent): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setBackgroundTransparent): Unknown error");
        }
    }

    PYHELIOS_API void setBackgroundImage(Visualizer* visualizer, const char* texture_file) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (!texture_file) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Texture file path cannot be null");
                return;
            }
            visualizer->setBackgroundImage(texture_file);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setBackgroundImage): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setBackgroundImage): Unknown error");
        }
    }

    PYHELIOS_API void setBackgroundSkyTexture(Visualizer* visualizer, const char* texture_file, unsigned int divisions) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }

            if (texture_file) {
                visualizer->setBackgroundSkyTexture(texture_file, divisions);
            } else {
                visualizer->setBackgroundSkyTexture("", divisions);
            }
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setBackgroundSkyTexture): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setBackgroundSkyTexture): Unknown error");
        }
    }

    // v1.3.53 Navigation Gizmo Functions
    PYHELIOS_API void hideNavigationGizmo(Visualizer* visualizer) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            visualizer->hideNavigationGizmo();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (hideNavigationGizmo): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (hideNavigationGizmo): Unknown error");
        }
    }

    PYHELIOS_API void showNavigationGizmo(Visualizer* visualizer) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            visualizer->showNavigationGizmo();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (showNavigationGizmo): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (showNavigationGizmo): Unknown error");
        }
    }

    // v1.3.53 Geometry Vertex Manipulation Functions
    PYHELIOS_API void getGeometryVertices(Visualizer* visualizer, size_t geometry_id, float** vertices, size_t* vertex_count) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (!vertices || !vertex_count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output pointers cannot be null");
                return;
            }

            static thread_local std::vector<float> static_vertex_data;
            std::vector<helios::vec3> vertex_vec = visualizer->getGeometryVertices(geometry_id);

            // Flatten vec3 array to float array
            static_vertex_data.clear();
            static_vertex_data.reserve(vertex_vec.size() * 3);
            for (const auto& v : vertex_vec) {
                static_vertex_data.push_back(v.x);
                static_vertex_data.push_back(v.y);
                static_vertex_data.push_back(v.z);
            }

            *vertices = static_vertex_data.data();
            *vertex_count = vertex_vec.size();

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getGeometryVertices): ") + e.what());
            if (vertices) *vertices = nullptr;
            if (vertex_count) *vertex_count = 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getGeometryVertices): Unknown error");
            if (vertices) *vertices = nullptr;
            if (vertex_count) *vertex_count = 0;
        }
    }

    PYHELIOS_API void setGeometryVertices(Visualizer* visualizer, size_t geometry_id, float* vertices, size_t vertex_count) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (!vertices && vertex_count > 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Vertices array is null but count > 0");
                return;
            }

            // Convert flat float array to vec3 vector
            std::vector<helios::vec3> vertex_vec;
            vertex_vec.reserve(vertex_count);
            for (size_t i = 0; i < vertex_count; i++) {
                vertex_vec.emplace_back(vertices[i*3], vertices[i*3+1], vertices[i*3+2]);
            }

            visualizer->setGeometryVertices(geometry_id, vertex_vec);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setGeometryVertices): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setGeometryVertices): Unknown error");
        }
    }

    // v1.3.53 Enhanced printWindow with format support
    PYHELIOS_API void printWindowWithFormat(Visualizer* visualizer, const char* filename, const char* format) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename cannot be null");
                return;
            }
            if (!format) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Format cannot be null");
                return;
            }

            visualizer->printWindow(filename, format);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (printWindowWithFormat): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (printWindowWithFormat): Unknown error");
        }
    }

    //=============================================================================
    // v1.3.54 Point Culling and LOD Functions
    //=============================================================================

    PYHELIOS_API void setPointCullingEnabled(Visualizer* visualizer, bool enabled) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }

            visualizer->setPointCullingEnabled(enabled);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setPointCullingEnabled): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setPointCullingEnabled): Unknown error");
        }
    }

    PYHELIOS_API void setPointCullingThreshold(Visualizer* visualizer, size_t threshold) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }

            visualizer->setPointCullingThreshold(threshold);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setPointCullingThreshold): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setPointCullingThreshold): Unknown error");
        }
    }

    PYHELIOS_API void setPointMaxRenderDistance(Visualizer* visualizer, float distance) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (distance < 0.0f) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Point max render distance cannot be negative");
                return;
            }

            visualizer->setPointMaxRenderDistance(distance);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setPointMaxRenderDistance): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setPointMaxRenderDistance): Unknown error");
        }
    }

    PYHELIOS_API void setPointLODFactor(Visualizer* visualizer, float factor) {
        try {
            clearError();
            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (factor <= 0.0f) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Point LOD factor must be positive");
                return;
            }

            visualizer->setPointLODFactor(factor);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setPointLODFactor): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setPointLODFactor): Unknown error");
        }
    }

    PYHELIOS_API void getPointRenderingMetrics(const Visualizer* visualizer,
                                                size_t* total_points,
                                                size_t* rendered_points,
                                                float* culling_time_ms) {
        try {
            clearError();

            // Nullify output parameters first
            if (total_points) *total_points = 0;
            if (rendered_points) *rendered_points = 0;
            if (culling_time_ms) *culling_time_ms = 0.0f;

            if (!visualizer) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Visualizer pointer is null");
                return;
            }
            if (!total_points || !rendered_points || !culling_time_ms) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output parameter pointers cannot be null");
                return;
            }

            visualizer->getPointRenderingMetrics(*total_points, *rendered_points, *culling_time_ms);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (getPointRenderingMetrics): ") + e.what());
            // Re-nullify on error
            if (total_points) *total_points = 0;
            if (rendered_points) *rendered_points = 0;
            if (culling_time_ms) *culling_time_ms = 0.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (getPointRenderingMetrics): Unknown error");
            if (total_points) *total_points = 0;
            if (rendered_points) *rendered_points = 0;
            if (culling_time_ms) *culling_time_ms = 0.0f;
        }
    }

} //extern "C"

#endif //VISUALIZER_PLUGIN_AVAILABLE
