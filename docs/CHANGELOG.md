# Changelog

# [v0.1.3] 2025-09-22

🚨++ New Plug-in Integrated ++ 🚨
- Initial phase of plant architecture plug-in integrated with PyHelios. This includes basic functionality for building plants from the library.

- Updated Helios native C++ library to v1.3.50

*Improved Error Handling, Build System Optimization, and Testing Infrastructure*
- **Context API**: Enhanced lifecycle state tracking with detailed error messages for better debugging
- **Build System**: Streamlined asset management by removing redundant asset copying code and optimizing build process
- **Testing**: Enhanced cross-platform test coverage with improved mock mode handling and context lifecycle testing
- **Documentation**: Major updates to plugin integration guide with critical implementation patterns and best practices
- **Visualizer**: Enhanced compatibility and error handling for cross-platform visualization workflows

## Build System
- Removed redundant asset copying for visualizer and weberpenntree plugins (using environment variable approach)
- Optimized build process with cleaner CMake integration
- Enhanced cross-platform library validation with fail-fast behavior

# [v0.1.2] 2025-09-18

🎉PyPI package distribution should now be working for all integrated plug-ins 🎉

*Enhanced Build System and GPU Runtime Detection*
- Added robust GPU runtime detection with fail-fast behavior and comprehensive error reporting
- Enhanced wheel building infrastructure with improved GitHub Actions workflows and timeout management
- **Build System**: Improved plugin dependency resolution with explicit user request tracking
- **Context API**: Enhanced error handling with consistent RuntimeError exceptions and better UUID validation
- **RadiationModel**: Expanded camera system integration with comprehensive GPU capability detection
- **Testing**: Added pytest markers for GPU-specific tests and enhanced cross-platform test coverage

# [v0.1.1] 2025-09-14

*PyPI Package Distribution Fixes*
- Fixed wheel building configuration with explicit plugin selection for cross-platform consistency
- **macOS wheels**: Include visualization support while excluding GPU plugins due to cross-compilation constraints
- **Windows/Linux wheels**: Include GPU plugins (radiation, energybalance) in addition to visualization for full feature support
- Improved CI/CD testing with comprehensive plugin validation and better error reporting

*Many documentation error fixes*

## Context
- Enhanced Context with new file export capabilities: `writePLY()`, `writeOBJ()` methods with comprehensive parameter support

# [v0.1.0] 2025-09-06

🎉++ PyPI Package Distribution ++ 🎉
- PyHelios now available on PyPI with `pip install pyhelios3d`

## Package Distribution
- Added comprehensive wheel building infrastructure with GitHub Actions CI/CD
- Cross-platform wheel support for Windows, macOS (x86_64 + ARM64), and Linux
- Automated CUDA toolkit installation and multi-architecture GPU support
- Smart platform detection for optimal plugin selection (macOS excludes GPU, Windows/Linux includes GPU when available)
- Added wheel preparation script for native library packaging
- Added MANIFEST.in for proper PyPI package structure

## Bug Fixes
- Fixed PluginMetadata constructor calls in build_helios.py
- Corrected plugin metadata parameter handling for GPU/visualization exclusions
- Enhanced build system robustness for different plugin configurations

# [v0.0.9] 2025-09-06

🚨++ New Plug-in Integrated ++ 🚨
- Photosynthesis model plug-in integrated with PyHelios

## Stomatal Conductance
- Fixed a few errors in the stomatal conductance model implementation
- Corrected a few errors in the stomatal conductance model documentation

## Radiation Model
- Corrected a few errors in the radiation model documentation

# [v0.0.8] 2025-09-05

🚨++ New Plug-in Integrated ++ 🚨
- Stomatal Conductance plug-in integrated with PyHelios

- Made some updates to testing infrastructure to avoid pytest state contamination

# [v0.0.7] 2025-09-04

- Updated Helios native C++ library to v1.3.47

## Radiation Model
- Finished radiation model integration with PyHelios
- Implemented radiation band management, source configuration, and simulation execution
- Added camera-based radiation modeling with flux data retrieval
- Enhanced with graceful degradation when radiation plugin unavailable

## Documentation
- Updated radiation plugin documentation with API reference and usage examples
- Added troubleshooting guide for OptiX and GPU requirements

# [v0.0.6] 2025-08-27

🚨++ New Plug-in Integrated ++ 🚨
- Solar Position plug-in integrated with PyHelios

## Bug Fixes
- Fixed CMake build system to only compile wrapper sources for selected plugins
- Fixed plugin registry detection for selective builds (`--plugins visualizer`)
- Fixed SolarPosition plugin metadata to correctly reflect optional status
- Fixed WeberPennTree constructor to properly handle unavailable plugin scenarios
- Updated error messages for plugin availability to match build configurations

## Testing
- Enhanced cross-platform tests for selective plugin builds
- Fixed test failures when building with limited plugin sets
- Improved error handling validation in plugin availability tests

# [v0.0.5] 2025-08-27

- Helios native C++ had several bugs that was causing errors in the last version. Merged in patched version of 1.3.46.

## Visualizer
- Fixed some issues that could cause the visualizer tests to crash in headless mode.

# [v0.0.4] 2025-08-25

🚨++ New Plug-in Integrated ++ 🚨
- Energy Balance plug-in integrated with PyHelios

- Updated Helios native C++ library to v1.3.46

## Visualizer
- Added `Visualizer.colorContextPrimitivesByData()`
- Fixed a number of issues where visualizer methods were using lists instead of Helios data types (e.g., vec2, vec3, etc.)

# [v0.0.3] 2025-08-23

## Context
- Added comprehensive file loading support with `Context.loadPLY()`, `Context.loadOBJ()`, and `Context.loadXML()` methods
- Enhanced `Context.loadPLY()` with 5 overloads supporting origin, height, rotation, color, and upaxis transformations
- Enhanced `Context.loadOBJ()` with 4 overloads including scale transformations and upaxis specification
- Added complete `Context.loadXML()` implementation for Helios XML geometry files
- Extended native C++ wrapper with 9 new file loading functions and proper error handling
- Added comprehensive parameter validation and security path checking
- Implemented `Context.addTriangleTextured()`
- Implemented `Context.addTrianglesFromArraysTextured()`

## Examples
- Added example geometry files: `suzanne.ply`, `suzanne.obj`, `suzanne.mtl`, and `leaf_cube.xml`
- Updated `external_geometry_sample.py` and `stanford_bunny_radiation.py` for demonstration

## Documentation
- Major README.md restructuring with simplified installation and quick start guide
- Streamlined documentation structure with consolidated user guide sections
- Updated Doxygen configuration for cleaner documentation generation
- Removed redundant documentation files and consolidated content

## Testing
- Enhanced existing tests with file loading functionality validation
- Added cross-platform API tests that work with and without native library

# [v0.0.2] 2025-08-22

## Context
- Added compound geometry support with `addTile()`, `addSphere()`, `addTube()`, `addBox()`, and `addCone()` methods (with color variants)
- Enhanced native C++ wrapper with thread-safe static vector management
- Fixed memory management issues with proper context cleanup to prevent segmentation faults
- Added comprehensive test coverage for compound geometry functionality

## Examples
- Added `primitive_data_array_example.py` demonstrating numpy array integration
- Enhanced `stanford_bunny_radiation.py` with improved visualization workflow
- Removed deprecated `simple_radiation_test.py`

## Documentation
- Updated plugin integration guide with memory management best practices
- Enhanced README.md with simplified installation instructions

# [v0.0.1] 2025-08-21

## Helios native C++
Fix helios-core submodule to point to correct remote commit  
- Reset submodule to match actual remote state (228a3d389)  
- Remove local divergent commits that don't exist on remote 
- This fixes the git history display showing non-existent commits

## Context
- Add primitive data operations for all types (float, int, string, vec2/3/4, int2/3/4)
- Add primitive data query functions (exists, type, size)
- Add auto-detection getter and pseudo-color visualization support
- Extend Context.py with comprehensive primitive data methods
- Add robust error handling and cross-platform ctypes wrappers
- Include comprehensive test coverage for all primitive data operations
- Added Context::getPrimitiveDataArray() to return a numpy array of primitive data

# [v0.0.0] 2025-08-20

🎉 Initial version! 🎉

## Currently implemented plug-ins
- `visualizer`
- `radiation`
- `weber-penn tree`