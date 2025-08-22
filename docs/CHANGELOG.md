# Changelog

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