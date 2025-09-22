# PyHelios build CMakeLists.txt - follows Helios standard format
cmake_minimum_required(VERSION 3.15)
project(helios)

#-------- USER INPUTS ---------#

#provide the path to Helios base directory, either as an absolute path or a path relative to the location of this file
set( BASE_DIRECTORY "../helios-core" )
	
#define the name of the executable to be created (minimal for CMake compatibility)
set( EXECUTABLE_NAME "pyhelios_build" )

#provide name of source file(s) (minimal main.cpp for CMake compatibility)
set( SOURCE_FILES "main.cpp" )

#-------- DYNAMIC PLUGIN SELECTION ---------#
# Include the plugin selection module
include("${CMAKE_CURRENT_SOURCE_DIR}/cmake/PluginSelection.cmake")

# Setup plugin system (replaces hardcoded PLUGINS variable)
setup_plugin_system()

#-------- MANYLINUX COMPATIBILITY FIX ---------#
# Apply z_size_t compatibility fix globally for all dependencies
if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
    if(DEFINED ENV{CIBUILDWHEEL} OR DEFINED ENV{AUDITWHEEL_PLAT} OR "$ENV{AUDITWHEEL_PLAT}" MATCHES "manylinux")
        message(STATUS "PyHelios: Applying manylinux z_size_t compatibility fix globally")
        # Force inclusion of stddef.h for all C/C++ compilations to ensure size_t is available
        set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -include stddef.h")
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -include stddef.h") 
        message(STATUS "PyHelios: Applied global stddef.h inclusion for manylinux compatibility")
    endif()
endif()

#-------- HELIOS INTEGRATION ---------#
# Include Helios core build system
# This will create the executable target ${EXECUTABLE_NAME} automatically
include( "${BASE_DIRECTORY}/core/CMake_project.cmake" )

#-------- CUDA SETUP FOR RADIATION PLUGIN ---------#
# Find CUDA if radiation plugin is enabled
if("radiation" IN_LIST PLUGINS)
    find_package(CUDAToolkit QUIET)
    if(CUDAToolkit_FOUND)
        message(STATUS "Found CUDA toolkit for radiation plugin: ${CUDAToolkit_VERSION}")
    endif()
endif()

#-------- PYHELIOS INTERFACE ---------#
# Create PyHelios interface library after Helios setup

# Start with core wrapper sources
set(PYHELIOS_WRAPPER_SOURCES
    ../native/src/pyhelios_wrapper_common.cpp
    ../native/src/pyhelios_wrapper_context.cpp
)

# Add plugin-specific wrapper sources based on selected plugins
if("visualizer" IN_LIST PLUGINS)
    list(APPEND PYHELIOS_WRAPPER_SOURCES ../native/src/pyhelios_wrapper_visualizer.cpp)
endif()

if("weberpenntree" IN_LIST PLUGINS)
    list(APPEND PYHELIOS_WRAPPER_SOURCES ../native/src/pyhelios_wrapper_weberpenntree.cpp)
endif()

if("radiation" IN_LIST PLUGINS)
    list(APPEND PYHELIOS_WRAPPER_SOURCES ../native/src/pyhelios_wrapper_radiation.cpp)
endif()

if("energybalance" IN_LIST PLUGINS)
    list(APPEND PYHELIOS_WRAPPER_SOURCES ../native/src/pyhelios_wrapper_energybalance.cpp)
endif()

if("photosynthesis" IN_LIST PLUGINS)
    list(APPEND PYHELIOS_WRAPPER_SOURCES ../native/src/pyhelios_wrapper_photosynthesis.cpp)
endif()

if("solarposition" IN_LIST PLUGINS)
    list(APPEND PYHELIOS_WRAPPER_SOURCES ../native/src/pyhelios_wrapper_solarposition.cpp)
endif()

if("stomatalconductance" IN_LIST PLUGINS)
    list(APPEND PYHELIOS_WRAPPER_SOURCES ../native/src/pyhelios_wrapper_stomatalconductance.cpp)
endif()

if("plantarchitecture" IN_LIST PLUGINS)
    list(APPEND PYHELIOS_WRAPPER_SOURCES ../native/src/pyhelios_wrapper_plantarchitecture.cpp)
endif()

# Only build static library if not building for wheels
if(NOT DEFINED ENV{CIBUILDWHEEL})
    add_library(pyhelios_interface STATIC ${PYHELIOS_WRAPPER_SOURCES})

    # Add Windows-specific compile definitions for static library
    if(WIN32)
        target_compile_definitions(pyhelios_interface PRIVATE BUILDING_PYHELIOS_DLL)
    endif()
endif()

if(NOT DEFINED ENV{CIBUILDWHEEL})
    # Add include directories for plugin headers
    target_include_directories(pyhelios_interface PRIVATE
        ${BASE_DIRECTORY}/core/include
        ../native/include
    )
endif()

if(NOT DEFINED ENV{CIBUILDWHEEL})
    # Add plugin-specific include directories only if plugins are selected
    if("visualizer" IN_LIST PLUGINS)
        target_include_directories(pyhelios_interface PRIVATE
            ${BASE_DIRECTORY}/plugins/visualizer/include
            ${BASE_DIRECTORY}/plugins/visualizer/lib/glfw-3.3.2/include
            ${BASE_DIRECTORY}/plugins/visualizer/lib/glm
        )
    endif()
endif()

if(NOT DEFINED ENV{CIBUILDWHEEL})
    if("weberpenntree" IN_LIST PLUGINS)
        target_include_directories(pyhelios_interface PRIVATE
            ${BASE_DIRECTORY}/plugins/weberpenntree/include
        )
    endif()
endif()

if(NOT DEFINED ENV{CIBUILDWHEEL})
    if("radiation" IN_LIST PLUGINS)
        target_include_directories(pyhelios_interface PRIVATE
            ${BASE_DIRECTORY}/plugins/radiation/include
            ${BASE_DIRECTORY}/plugins/radiation/lib/json
        )
    endif()
endif()

if(NOT DEFINED ENV{CIBUILDWHEEL})
    if("energybalance" IN_LIST PLUGINS)
        target_include_directories(pyhelios_interface PRIVATE
            ${BASE_DIRECTORY}/plugins/energybalance/include
        )
    endif()
endif()

if(NOT DEFINED ENV{CIBUILDWHEEL})
    if("photosynthesis" IN_LIST PLUGINS)
        target_include_directories(pyhelios_interface PRIVATE
            ${BASE_DIRECTORY}/plugins/photosynthesis/include
        )
    endif()
endif()

if(NOT DEFINED ENV{CIBUILDWHEEL})
    if("solarposition" IN_LIST PLUGINS)
        target_include_directories(pyhelios_interface PRIVATE
            ${BASE_DIRECTORY}/plugins/solarposition/include
        )
    endif()
endif()

if(NOT DEFINED ENV{CIBUILDWHEEL})
    if("stomatalconductance" IN_LIST PLUGINS)
        target_include_directories(pyhelios_interface PRIVATE
            ${BASE_DIRECTORY}/plugins/stomatalconductance/include
        )
    endif()
endif()

if(NOT DEFINED ENV{CIBUILDWHEEL})
    if("plantarchitecture" IN_LIST PLUGINS)
        target_include_directories(pyhelios_interface PRIVATE
            ${BASE_DIRECTORY}/plugins/plantarchitecture/include
        )
    endif()
endif()

if(NOT DEFINED ENV{CIBUILDWHEEL})
    # Add platform-specific OptiX include directories for radiation plugin
    if("radiation" IN_LIST PLUGINS)
        if(WIN32)
            target_include_directories(pyhelios_interface PRIVATE
                ${BASE_DIRECTORY}/plugins/radiation/lib/OptiX/windows64-6.5.0/include
            )
        else()
            target_include_directories(pyhelios_interface PRIVATE
                ${BASE_DIRECTORY}/plugins/radiation/lib/OptiX/linux64-6.5.0/include
            )
        endif()
    endif()
endif()

if(NOT DEFINED ENV{CIBUILDWHEEL})
    # Add CUDA include directories if CUDA toolkit was found and radiation plugin is selected
    if("radiation" IN_LIST PLUGINS AND CUDAToolkit_FOUND)
        target_include_directories(pyhelios_interface PRIVATE ${CUDAToolkit_INCLUDE_DIRS})
    endif()
endif()

if(NOT DEFINED ENV{CIBUILDWHEEL})
    # Link interface to helios library using keyword signature for compatibility
    # Must match the signature style used in Helios core CMake_project.cmake (PUBLIC)
    target_link_libraries(pyhelios_interface PUBLIC helios)
endif()

if(NOT DEFINED ENV{CIBUILDWHEEL})
    # Set output directory to lib so it's found by build script
    set_target_properties(pyhelios_interface PROPERTIES
        ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
        ARCHIVE_OUTPUT_NAME "pyhelios_interface"
    )
endif()

#-------- PYHELIOS SHARED LIBRARY ---------#
# Create the PyHelios shared library for Python ctypes interface
add_library(pyhelios_shared SHARED ${PYHELIOS_WRAPPER_SOURCES})

# Set C++ standard to match Helios core requirements
set_target_properties(pyhelios_shared PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
)

# Add same include directories
target_include_directories(pyhelios_shared PRIVATE
    ${BASE_DIRECTORY}/core/include
    ${BASE_DIRECTORY}/core/lib/pugixml
    ../native/include
)

# Add plugin-specific include directories only if plugins are selected
if("visualizer" IN_LIST PLUGINS)
    target_include_directories(pyhelios_shared PRIVATE
        ${BASE_DIRECTORY}/plugins/visualizer/include
        ${BASE_DIRECTORY}/plugins/visualizer/lib/glfw-3.3.2/include
        ${BASE_DIRECTORY}/plugins/visualizer/lib/glm
    )
endif()

if("weberpenntree" IN_LIST PLUGINS)
    target_include_directories(pyhelios_shared PRIVATE
        ${BASE_DIRECTORY}/plugins/weberpenntree/include
    )
endif()

if("radiation" IN_LIST PLUGINS)
    target_include_directories(pyhelios_shared PRIVATE
        ${BASE_DIRECTORY}/plugins/radiation/include
        ${BASE_DIRECTORY}/plugins/radiation/lib/json
    )
endif()

if("energybalance" IN_LIST PLUGINS)
    target_include_directories(pyhelios_shared PRIVATE
        ${BASE_DIRECTORY}/plugins/energybalance/include
    )
endif()

if("solarposition" IN_LIST PLUGINS)
    target_include_directories(pyhelios_shared PRIVATE
        ${BASE_DIRECTORY}/plugins/solarposition/include
    )
endif()

if("stomatalconductance" IN_LIST PLUGINS)
    target_include_directories(pyhelios_shared PRIVATE
        ${BASE_DIRECTORY}/plugins/stomatalconductance/include
    )
endif()

if("plantarchitecture" IN_LIST PLUGINS)
    target_include_directories(pyhelios_shared PRIVATE
        ${BASE_DIRECTORY}/plugins/plantarchitecture/include
    )
endif()

# Add platform-specific OptiX include directories for radiation plugin (shared library)
if("radiation" IN_LIST PLUGINS)
    if(WIN32)
        target_include_directories(pyhelios_shared PRIVATE
            ${BASE_DIRECTORY}/plugins/radiation/lib/OptiX/windows64-6.5.0/include
        )
    else()
        target_include_directories(pyhelios_shared PRIVATE
            ${BASE_DIRECTORY}/plugins/radiation/lib/OptiX/linux64-6.5.0/include
        )
    endif()
endif()

# Add CUDA include directories if CUDA toolkit was found and radiation plugin is selected (shared library)
if("radiation" IN_LIST PLUGINS AND CUDAToolkit_FOUND)
    target_include_directories(pyhelios_shared PRIVATE ${CUDAToolkit_INCLUDE_DIRS})
endif()

# Link to helios library and all selected plugins using keyword signature for compatibility
target_link_libraries(pyhelios_shared PUBLIC helios)

# Link to plugins based on plugin configuration
if(DEFINED PLUGINS)
    foreach(PLUGIN IN LISTS PLUGINS)
        if(TARGET ${PLUGIN})
            target_link_libraries(pyhelios_shared PUBLIC ${PLUGIN})
            message(STATUS "Linked pyhelios_shared to plugin: ${PLUGIN}")
        endif()
    endforeach()
endif()

# Set output properties for cross-platform naming
if(WIN32)
    # Define DLL export macro for Windows
    target_compile_definitions(pyhelios_shared PRIVATE BUILDING_PYHELIOS_DLL)
    
    # Ensure static linking of Visual Studio runtime and system libraries
    set_target_properties(pyhelios_shared PROPERTIES
        LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
        RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
        OUTPUT_NAME "libhelios"
        MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>"
    )
    
    # Static link system libraries to avoid missing DLL dependencies
    target_link_libraries(pyhelios_shared PUBLIC
        kernel32 user32 gdi32 winspool shell32 ole32 oleaut32 uuid comdlg32 advapi32
    )
    
    # Force static linking for all targets on Windows to avoid DLL dependencies
    set_property(TARGET pyhelios_shared PROPERTY MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
    
    # Ensure all dependencies are found and linked statically
    # This prevents "module not found" errors with missing DLLs
    target_link_options(pyhelios_shared PRIVATE
        "/NODEFAULTLIB:msvcrt.lib"
        "/NODEFAULTLIB:msvcrtd.lib"
    )
elseif(APPLE)
    set_target_properties(pyhelios_shared PROPERTIES
        LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
        OUTPUT_NAME "helios"
    )
else() # Linux
    set_target_properties(pyhelios_shared PROPERTIES
        LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
        OUTPUT_NAME "helios"
    )
endif()

# Copy OptiX DLL to lib directory for Windows wheel packaging
if("radiation" IN_LIST PLUGINS AND WIN32)
    # Determine OptiX version and DLL name
    if(OPTIX_VERSION_LEGACY)
        set(OPTIX_PATH ${BASE_DIRECTORY}/plugins/radiation/lib/OptiX/windows64-5.1.1/)
        set(OPTIX_DLL "optix.51.dll")
    else()
        set(OPTIX_PATH ${BASE_DIRECTORY}/plugins/radiation/lib/OptiX/windows64-6.5.0/)
        set(OPTIX_DLL "optix.6.5.0.dll")
    endif()

    # Copy OptiX DLL to lib directory for wheel packaging
    # The radiation plugin already copies it to CMAKE_BINARY_DIR, we just move it to lib/
    add_custom_command(TARGET pyhelios_shared POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${CMAKE_BINARY_DIR}/${OPTIX_DLL}"
        "${CMAKE_BINARY_DIR}/lib/${OPTIX_DLL}"
        COMMENT "Moving OptiX DLL to lib directory for wheel packaging"
    )
endif()

