# PyHelios Plugin Selection CMake Module
# 
# This module provides functions for dynamic plugin selection and configuration
# based on the generated plugin configuration file from build_helios.py

# Function to include plugin configuration
function(load_plugin_configuration)
    # Check if PyHelios plugin configuration was provided
    if(DEFINED PYHELIOS_PLUGIN_CONFIG)
        if(EXISTS "${PYHELIOS_PLUGIN_CONFIG}")
            message(STATUS "Loading PyHelios plugin configuration: ${PYHELIOS_PLUGIN_CONFIG}")
            include("${PYHELIOS_PLUGIN_CONFIG}")
        else()
            message(WARNING "PyHelios plugin configuration file not found: ${PYHELIOS_PLUGIN_CONFIG}")
            # Fall back to default configuration
            set(PLUGINS "radiation" CACHE STRING "Default plugins for backward compatibility")
            add_compile_definitions(RADIATION_PLUGIN_AVAILABLE)
        endif()
    else()
        # No plugin configuration provided - use default (backward compatibility)
        message(STATUS "No plugin configuration provided - using default (radiation only)")
        set(PLUGINS "radiation" CACHE STRING "Default plugins for backward compatibility")
        add_compile_definitions(RADIATION_PLUGIN_AVAILABLE)
    endif()
    
    # Make PLUGINS available to parent scope
    set(PLUGINS ${PLUGINS} PARENT_SCOPE)
    
    message(STATUS "Selected plugins: ${PLUGINS}")
endfunction()

# Function to validate and resolve plugin dependencies
function(resolve_plugin_dependencies)
    # Get the current plugin list
    set(VALIDATED_PLUGINS)
    
    # Check that all plugins exist in helios-core
    foreach(PLUGIN ${PLUGINS})
        set(PLUGIN_DIR "${CMAKE_CURRENT_SOURCE_DIR}/${BASE_DIRECTORY}/plugins/${PLUGIN}")
        if(EXISTS "${PLUGIN_DIR}")
            list(APPEND VALIDATED_PLUGINS ${PLUGIN})
            message(STATUS "✓ Plugin available: ${PLUGIN}")
        else()
            message(WARNING "✗ Plugin not found: ${PLUGIN} (directory: ${PLUGIN_DIR})")
        endif()
    endforeach()
    
    # Update plugins list with only validated plugins
    set(PLUGINS ${VALIDATED_PLUGINS} PARENT_SCOPE)
    
    if(NOT VALIDATED_PLUGINS)
        message(FATAL_ERROR "No valid plugins found! Check your plugin selection.")
    endif()
    
    message(STATUS "Validated plugins: ${VALIDATED_PLUGINS}")
endfunction()

# Function to generate plugin-specific compile definitions
function(generate_plugin_definitions PLUGINS)
    message(STATUS "Generating compile definitions for plugins: ${PLUGINS}")
    
    foreach(PLUGIN ${PLUGINS})
        # Convert plugin name to uppercase for preprocessor definition
        string(TOUPPER ${PLUGIN} PLUGIN_UPPER)
        add_compile_definitions(${PLUGIN_UPPER}_PLUGIN_AVAILABLE)
        message(STATUS "Added definition: ${PLUGIN_UPPER}_PLUGIN_AVAILABLE")
    endforeach()
    
    # Special handling for radiation plugin
    list(FIND PLUGINS "radiation" RADIATION_INDEX)
    if(RADIATION_INDEX GREATER_EQUAL 0)
        message(STATUS "Radiation plugin enabled - OptiX will be available")
        # OptiX is enabled by default unless explicitly disabled
        # The HELIOS_NO_OPTIX definition can be added in plugin_config.cmake if needed
    else()
        message(STATUS "Radiation plugin not selected - disabling OptiX")
        add_compile_definitions(HELIOS_NO_OPTIX)
    endif()
endfunction()

# Function to filter plugins by platform
function(filter_plugins_by_platform PLUGINS)
    set(FILTERED_PLUGINS)
    
    foreach(PLUGIN ${PLUGINS})
        set(INCLUDE_PLUGIN TRUE)
        
        # Platform-specific filtering
        if(WIN32)
            # Windows supports most plugins
            # No specific filtering needed currently
        elseif(APPLE)
            # macOS has limited support for some GPU plugins
            if(PLUGIN STREQUAL "aeriallidar")
                message(STATUS "⚠️  Plugin ${PLUGIN} has limited macOS support")
                # Include anyway, but warn
            endif()
        elseif(UNIX)
            # Linux supports all plugins
            # No specific filtering needed currently
        endif()
        
        if(INCLUDE_PLUGIN)
            list(APPEND FILTERED_PLUGINS ${PLUGIN})
        else()
            message(STATUS "🚫 Filtered out platform-incompatible plugin: ${PLUGIN}")
        endif()
    endforeach()
    
    set(PLUGINS ${FILTERED_PLUGINS} PARENT_SCOPE)
    message(STATUS "Platform-filtered plugins: ${FILTERED_PLUGINS}")
endfunction()

# Function to add a plugin to the build
function(add_plugin_to_build PLUGIN)
    set(PLUGIN_DIR "${CMAKE_CURRENT_SOURCE_DIR}/${BASE_DIRECTORY}/plugins/${PLUGIN}")
    set(PLUGIN_CMAKE "${PLUGIN_DIR}/CMakeLists.txt")
    
    if(EXISTS "${PLUGIN_CMAKE}")
        message(STATUS "Adding plugin to build: ${PLUGIN}")
        add_subdirectory("${PLUGIN_DIR}" "${CMAKE_CURRENT_BINARY_DIR}/plugins/${PLUGIN}")
        
        # Store plugin for later linking (target doesn't exist yet)
        set_property(GLOBAL APPEND PROPERTY PYHELIOS_PLUGIN_TARGETS ${PLUGIN})
        message(STATUS "Plugin added to build: ${PLUGIN}")
    else()
        message(WARNING "Plugin CMakeLists.txt not found: ${PLUGIN_CMAKE}")
    endif()
endfunction()

# Main function to handle plugin selection workflow
function(setup_plugin_system)
    message(STATUS "=== PyHelios Plugin System Setup ===")
    
    # Step 1: Load plugin configuration
    load_plugin_configuration()
    
    # Step 2: Validate and resolve dependencies
    resolve_plugin_dependencies()
    
    # Step 3: Generate compile definitions
    generate_plugin_definitions("${PLUGINS}")
    
    # Step 4: Filter by platform
    filter_plugins_by_platform("${PLUGINS}")
    
    # Step 5: Plugins will be added by core CMake_project.cmake
    # (Remove custom plugin addition to avoid duplicate subdirectory conflicts)
    
    message(STATUS "=== Plugin System Setup Complete ===")
    message(STATUS "Final plugin list: ${PLUGINS}")
    
    # Make final plugin list available globally AND set PLUGINS for CMake_project.cmake
    set(FINAL_PLUGINS ${PLUGINS} CACHE STRING "Final list of enabled plugins" FORCE)
    set(PLUGINS ${PLUGINS} PARENT_SCOPE)
endfunction()


# Function to link plugins to main target (call after target is created)
function(link_plugins_to_target)
    get_property(PLUGIN_TARGETS GLOBAL PROPERTY PYHELIOS_PLUGIN_TARGETS)
    
    if(PLUGIN_TARGETS)
        message(STATUS "Linking plugins to ${EXECUTABLE_NAME}: ${PLUGIN_TARGETS}")
        foreach(PLUGIN ${PLUGIN_TARGETS})
            if(TARGET ${PLUGIN})
                target_link_libraries(${EXECUTABLE_NAME} PUBLIC ${PLUGIN})
                message(STATUS "✓ Linked plugin library: ${PLUGIN}")
            else()
                message(WARNING "✗ Plugin target not found: ${PLUGIN}")
            endif()
        endforeach()
    else()
        message(STATUS "No plugins to link")
    endif()
endfunction()


# Print plugin information for debugging
function(print_plugin_info)
    message(STATUS "=== Plugin Information ===")
    message(STATUS "Base directory: ${BASE_DIRECTORY}")
    message(STATUS "Executable name: ${EXECUTABLE_NAME}")
    message(STATUS "Selected plugins: ${PLUGINS}")
    message(STATUS "Available plugin directories:")
    
    if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/${BASE_DIRECTORY}/plugins")
        file(GLOB PLUGIN_DIRS "${CMAKE_CURRENT_SOURCE_DIR}/${BASE_DIRECTORY}/plugins/*")
        foreach(PLUGIN_DIR ${PLUGIN_DIRS})
            if(IS_DIRECTORY ${PLUGIN_DIR})
                get_filename_component(PLUGIN_NAME ${PLUGIN_DIR} NAME)
                message(STATUS "  - ${PLUGIN_NAME}")
            endif()
        endforeach()
    else()
        message(STATUS "  No plugins directory found at: ${CMAKE_CURRENT_SOURCE_DIR}/${BASE_DIRECTORY}/plugins")
    endif()
    
    message(STATUS "========================")
endfunction()