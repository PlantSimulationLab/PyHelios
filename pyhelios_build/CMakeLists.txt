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

#-------- DO NOT MODIFY ---------#
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
add_library(pyhelios_interface STATIC ../native/src/pyhelios_wrapper.cpp)

# Add include directories for plugin headers
target_include_directories(pyhelios_interface PRIVATE
    ${BASE_DIRECTORY}/core/include
    ../native/include
)

# Add plugin-specific include directories only if plugins are selected
if("visualizer" IN_LIST PLUGINS)
    target_include_directories(pyhelios_interface PRIVATE
        ${BASE_DIRECTORY}/plugins/visualizer/include
        ${BASE_DIRECTORY}/plugins/visualizer/lib/glfw-3.3.2/include
        ${BASE_DIRECTORY}/plugins/visualizer/lib/glm
    )
endif()

if("weberpenntree" IN_LIST PLUGINS)
    target_include_directories(pyhelios_interface PRIVATE
        ${BASE_DIRECTORY}/plugins/weberpenntree/include
    )
endif()

if("radiation" IN_LIST PLUGINS)
    target_include_directories(pyhelios_interface PRIVATE
        ${BASE_DIRECTORY}/plugins/radiation/include
        ${BASE_DIRECTORY}/plugins/radiation/lib/json
    )
endif()

if("energybalance" IN_LIST PLUGINS)
    target_include_directories(pyhelios_interface PRIVATE
        ${BASE_DIRECTORY}/plugins/energybalance/include
    )
endif()

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

# Add CUDA include directories if CUDA toolkit was found and radiation plugin is selected
if("radiation" IN_LIST PLUGINS AND CUDAToolkit_FOUND)
    target_include_directories(pyhelios_interface PRIVATE ${CUDAToolkit_INCLUDE_DIRS})
endif()

# Link interface to helios library
target_link_libraries(pyhelios_interface PUBLIC helios)

# Set output directory to lib so it's found by build script
set_target_properties(pyhelios_interface PROPERTIES
    ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
    ARCHIVE_OUTPUT_NAME "pyhelios_interface"
)

#-------- PYHELIOS SHARED LIBRARY ---------#
# Create the PyHelios shared library for Python ctypes interface
add_library(pyhelios_shared SHARED ../native/src/pyhelios_wrapper.cpp)

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

# Link to helios library and all selected plugins
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
    target_link_libraries(pyhelios_shared PRIVATE
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

