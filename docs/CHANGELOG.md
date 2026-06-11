# Changelog

# [v0.1.22] 2026-06-10

- Updated helios-core to v1.3.74

## Context
- `setPrimitiveData*()`/`setObjectData*()` now accept a *list* of values (one per UUID/objID) to assign a distinct value to each element in a single bulk call, complementing the existing scalar-broadcast behavior (a scalar still applies the same value to every ID). Covers all 11 data types (`int`, `uint`, `float`, `double`, `string`, `vec2`, `vec3`, `vec4`, `int2`, `int3`, `int4`).
- `overridePrimitiveTextureColor()` and `usePrimitiveTextureColor()` now accept a list of UUIDs, applying the override/restore to all of them in one bulk call (previously single-UUID only).
- `incrementPrimitiveData()` gained an optional `data_type` keyword (`'int'`/`'uint'`/`'float'`/`'double'`) to target a specific field type, and now supports unsigned-int and double fields in addition to the existing int/float overloads.

## LiDAR
- Added `LiDARCloud.addHitPointsWithData()` for bulk in-memory hit ingestion carrying a per-hit data map: like `addHitPoints()` but populates each hit's named-scalar data map (the in-memory equivalent of what the ASCII loader does for non-standard columns), so values like `timestamp`/`target_index`/`target_count` land in the map for multi-return grouping. Uses the full `SphericalCoord` (radius retained for Beer's-law path length).
- Added `LiDARCloud.getTriangleVerticesAll()` to bulk-export every triangulated triangle's three vertices (and source scan ID) in a single call as flat numpy arrays, reading directly off the LiDARcloud and bypassing the Context round-trip and per-triangle vertex loop.
- Added `LiDARCloud.getTriangulationStats()` returning the filter diagnostics from the most recent `triangulateHitPoints()` call as a dict (`candidates`, `dropped_lmax`, `dropped_aspect`, `dropped_degenerate`); each dropped triangle is attributed to one primary reason so `candidates == getTriangleCount() + dropped_lmax + dropped_aspect + dropped_degenerate`, distinguishing a data-limited mesh (few candidates) from a filter-limited one (many candidates dropped by Lmax/aspect).
- **Leaf-area inversion now requires misses (behavior change from helios-core 1.3.74).** `calculateLeafArea()` fails fast with an explicit error if the point cloud contains no misses (fired pulses that returned nothing), rather than silently producing biased leaf area density. `LiDARCloud.syntheticScan()` now records misses by default for **discrete-return** scans as well as full-waveform (the discrete path is routed through a new miss-aware native overload honoring `scan_grid_only`/`record_misses`); import workflows can synthesize misses with `gapfillMisses()`. Added `hasMisses()`, `isHitMiss(index)`, and the static `getMissDistance()` (the `LIDAR_MISS_DISTANCE` constant) to inspect misses.
- Added a global scanner-tilt option for synthetic scans: `addScan()` gained `scan_tilt_roll`/`scan_tilt_pitch` keyword arguments (radians; default 0 = level), queryable via `getScanTiltRoll()`/`getScanTiltPitch()`. Models the residual tilt of the scanner spin axis away from plumb.
- Added a spinning multibeam scan pattern (e.g. Velodyne/Ouster/Hesai): `addScanMultibeam()` registers a rotating multi-channel scan from a list of per-channel zenith angles, and `getScanPattern()` (returning the new `ScanPattern` enum: `RASTER`/`SPINNING_MULTIBEAM`) and `getScanBeamZenithAngles()` query the pattern.
- Added per-voxel leaf-area sampling uncertainty (Pimont et al. 2018): `calculateLeafArea()` gained an optional `element_width` argument that, alongside the leaf-area estimate, computes the sampling variance, exposed through `getCellLADVariance()`, `getCellBeamCount()`, `getCellRelativeDensityIndex()`, `getCellMeanPathLength()`, single-voxel `getCellLeafAreaConfidenceInterval()`, group-scale `getGroupLADConfidenceInterval()` (recommended), and the `exportLeafAreaUncertainty()` file export.
- `exportPointCloud()` gained a `write_header` argument (default True): exports now prepend a `#`-prefixed column-name header line (CloudCompare convention) that round-trips through `loadXML()`.

## Plant Architecture
- Added read-only shoot-topology inspection mirroring helios-core 1.3.74's `getAllShootIDs()`/`getPlantShoot()`: `PlantArchitecture.getAllShootIDs()` returns the contiguous 0-based shoot IDs for a plant (shoot 0 is the base stem), `getShoot()` returns a shoot's topology dict (`rank`, `parent_shoot_id` (-1 for the base stem), `parent_node_index`, `node_count`), `getShootChildIDs()` returns its child shoot IDs, and `getShootInternodeVertices()`/`getShootInternodeRadii()` return its woody internode polyline geometry.

# [v0.1.21] 2026-06-07

- Updated helios-core to v1.3.73

## Context
- Added `clearAllPrimitiveData(label)` and `clearAllObjectData(label)` to remove a named data field from *every* primitive/compound object in the Context (including hidden ones) and release the registered data type for that label, complementing the existing per-UUID/per-objID `clearPrimitiveData()`/`clearObjectData()`.
- Added `deleteTimeseriesDataPoint(date, time, label=None)` to delete a single timeseries data point at a given date/time — for one variable when `label` is given, or across all variables when `label` is `None`.
- `Location` gained an `altitude` field (meters above sea level, default 0.0); `setLocation()` accepts an optional `altitude` in its float form, `getLocation()` now returns it, and `make_Location()` accepts an optional 4th argument. Existing 3-argument usage is unchanged. Note Helios's non-standard longitude convention (+W / −E), which is auto-flipped to the standard +E convention when written into camera EXIF metadata.

## Radiation
- `CameraProperties` gained a `manufacturer` field (helios-core v1.3.73 maps it to the EXIF camera *Make* tag; empty ⇒ "Helios"). Like the other `CameraProperties` string fields, it is exposed on the Python class for forward compatibility but is not yet plumbed through to the native camera. Camera images written via `writeCameraImage()` embed EXIF/XMP metadata (camera intrinsics, orientation, and GPS derived from the Context `Location`) automatically on the native side.

## LiDAR
- `LiDARCloud.addScan()` gained optional `range_noise_stddev` (meters) and `angle_noise_stddev` (radians) arguments that drive realistic anisotropic positional error during `syntheticScan()` (along-beam range noise and across-beam beam-pointing jitter). Both default to 0.0 (disabled), preserving prior behavior. Query them with `getScanRangeNoiseStdDev(scanID)` / `getScanAngleNoiseStdDev(scanID)`.
- Added `exportScans(filename)` to write all scans as an XML metadata file plus one ASCII data file per scan (auto-named `<base>_<scanID>.xyz`), re-loadable with `loadXML()`.

# [v0.1.20] 2026-05-08

- Updated helios-core to v1.3.72

## Context
- Added scalar existence and metadata queries: `doesObjectExist()`, `doesObjectContainPrimitive()`, `doesMaterialDataExist()`, `objectHasTexture()`, `isPrimitiveDirty()`, `areObjectPrimitivesComplete()`, `getJulianDate()`, `getMaterialCount()`, `getObjectArea()`, `getObjectPrimitiveCount()`, `getPolymeshObjectVolume()`, `getMaterialIDFromLabel()`, `getPrimitiveMaterialID()`, `getGlobalDataVersion()`, `getPrimitiveParentObjectID()`, `getObjectTextureFile()`, `listAllPrimitiveDataLabels()`, `getLoadedXMLFiles()`, `printObjectInfo()`, `printPrimitiveInfo()`, `setObjectDataFromPrimitiveDataMean()`, `renameMaterial()`, `renamePrimitiveData()`, `clearMaterialData()`, plus `enable/disablePrimitiveDataValueCaching()` and `enable/disableObjectDataValueCaching()`
- Added vector-return queries and geometry mutators: `getDeletedUUIDs()`, `getDirtyUUIDs()`, `getUniquePrimitiveParentObjectIDs()`, `getObjectAverageNormal()`, plus `setObjectAverageNormal()`, `setObjectOrigin()`, `setPrimitiveAzimuth()`, `setPrimitiveElevation()`, `setTriangleVertices()`, `setPrimitiveNormal()` (single/batch), and `setPrimitiveParentObjectID()` (single/batch)
- Added a complete material-data API spanning all 11 Helios data types (`int`, `uint`, `float`, `double`, `string`, `vec2`, `vec3`, `vec4`, `int2`, `int3`, `int4`): per-type explicit `setMaterialData<Type>()` and `getMaterialData<Type>()` methods, a unified `setMaterialData()`/`getMaterialData()` dispatcher with auto-detection via `getMaterialDataType()`, and `getUniquePrimitiveDataValues()`/`getUniqueObjectDataValues()` (`int`/`uint`/`str`)
- Added 4×4 transformation matrix accessors as numpy `(4,4) float32` ndarrays (also accepting nested lists or flat 16-float lists): `get/setObjectTransformationMatrix()` and `get/setPrimitiveTransformationMatrix()` with single/batch dispatch, plus domain-level `getDomainBoundingBox()` and `getDomainBoundingSphere()` with optional UUID filtering
- Added tube/polymesh/object mutators: `setTubeNodes()`, `setTubeRadii()`, `scaleTubeGirth()`, `scaleTubeLength()`, `pruneTubeNodes()`, `appendTubeSegment()` (color or texture+uv kwargs), `addPolymeshObject()`, `setObjectColor()` (RGB/RGBA, single/batch), `overrideObjectTextureColor()`/`useObjectTextureColor()`, `markPrimitiveDirty()`/`markPrimitiveClean()`, `setTileObjectSubdivisionCount()`, and `setTileObjectSubdivisionByAreaRatio()`
- Added `cleanDeletedUUIDs()` and `cleanDeletedObjectIDs()` (returning new lists, not mutating input), `writeXML()`/`writeXML_byobject()` for XML export with optional UUID filtering, `randu()`/`randn()` random-number draws (uniform with optional float or int range; normal with optional mean/stddev), and geographic `setLocation()`/`getLocation()` returning the new `Location` dataclass (latitude, longitude, UTC offset)
- Added colormap and texture-transparency helpers: `generateColormap(name, n_colors)` returning an `RGBcolor` list, `generateTexturesFromColormap()` returning generated file paths, and `getPrimitiveTextureTransparencyData()` returning an `Optional[np.ndarray]` 2D bool mask
- Added `deleteTimeseriesVariable(label)` to remove a single timeseries variable and all of its data points (complements the existing `clearTimeseriesData()` and `updateTimeseriesData()`).

## LeafOptics
- Extended `LeafOpticsProperties` with two optional Fluspect-B SIF parameters: `V2Z` (violaxanthin↔zeaxanthin de-epoxidation state, default 0.0) and `fqe` (intrinsic fluorescence quantum-efficiency scalar, default 1.0). They are ignored by the pure PROSPECT reflectance/transmittance calculation; the radiation plugin's SIF pipeline reads them when active. The flat float-array layout grew from 9 to 11 entries; `LeafOpticsProperties.from_list()` still accepts both lengths for backward compatibility with serialized data.

## Photosynthesis
- Added `setModelTypeC4()` and the von Caemmerer (2021) steady-state C4 model — `setC4CoefficientsFromLibrary()` / `getC4CoefficientsFromLibrary()` (species: `SetariaViridis_vC2021`, `GenericC4_vC2000`, `Maize_Massad2007`), `setC4ModelCoefficients()` / `getC4ModelCoefficients()` over a 43-float coefficient array (5 temperature-responsive rates × 4 floats: Vpmax/Vcmax/Jmax/Rd/gm; 5 K-25 + 5 dH kinetic constants; 13 user-tunable scalars), and `setCm()` for direct mesophyll CO₂ prescription (testing/validation). Both `setC4CoefficientsFromLibrary()` and `setC4ModelCoefficients()` accept a `material_label` keyword to apply coefficients per-material rather than per-UUID.
- Added `setFarquharMesophyllConductance()` to configure C3 mesophyll conductance `gm` (mol CO₂ / m² / s / bar) with optional temperature response. Default behaviour unchanged: `gm = +∞` reduces `Cc` to `Ci` (legacy Farquhar).
- `FarquharModelCoefficients` flat array round-trip (`to_array()` / `from_array()` and the corresponding `getFarquharModelCoefficients` / `setFarquharModelCoefficients` C wrappers) grew from 18 to 22 floats: slots 18–21 carry `(gm_at_25C, dHa, Topt_C, dHd)` for the gm temperature response. `from_array` still accepts the legacy 18-float layout for back-compat (gm defaults to `+∞`); the C wrapper still accepts 18-float buffers and only consumes the gm slots when the buffer is at least 22 elements.
- C4 `limitation_state` uses the convention `1 = enzyme-limited`, `2 = electron-transport-limited` (vs. C3's `0/1`). New optional output primitive data labels for the C4 model: `Cm` (mesophyll cytosolic CO₂) and `Vp` (PEP carboxylation rate).

## Radiation
- Added `addSIFCamera()` (vec3 lookat and SphericalCoord overloads) plus the new `SIFCameraProperties` (extends `CameraProperties` with `excitation_bin_width_nm` and `excitation_scattering_depth`) and the `isSIFCamera()` query. SIF cameras source per-band emission from the Fluspect-B kernel rather than Stefan-Boltzmann; Helios auto-creates internal excitation bands covering 400–750 nm at the requested bin width.

## LiDAR
- Exposed per-hit scalar data and metadata that `syntheticScan()` already computes: `LiDARCloud.getHitData(index, label)`, `doesHitDataExist(index, label)`, and `getHitScanID(index)`, reaching `intensity`, `distance`, `timestamp`, `target_index`, `target_count`, `deviation`, `nRaysHit`, and any column-format fields. Added bulk single-call exports `getHitDataAll(label)` and `getHitsXYZRGB()` for large clouds.
- Generalized the synthetic scan's primitive-data → hit-data transfer to be driven by the scan's column format: any non-standard label in a scan's `column_format` is now sampled from the struck primitive (FLOAT/DOUBLE/INT/UINT) onto each hit, replacing the previously hardcoded `object_label`/`reflectivity_lidar` pair (`reflectivity_lidar` retains its intensity-modulation behavior). `LiDARCloud.addScan()` gained an optional `column_format` argument (default keeps prior behavior); the previously auto-copied `object_label` must now be listed in `column_format` to transfer.

# [v0.1.19] 2026-04-16

- Updated helios-core to v1.3.71

## Plant Architecture
- Added `writePlantStructureUSD()` to export a plant as a USD articulated rigid body for NVIDIA IsaacSim physics (capsule links, spherical joints with E*I/L spring/damper drives, organ mass bodies)
- Added growth animation export via `registerGrowthFrame()`, `writePlantGrowthUSD()`, `clearGrowthFrames()`, and `getGrowthFrameCount()` for time-sampled USD animations importable into Blender

## Context
- Added `updateTimeseriesData()` method to replace the value of an existing timeseries data point at a specified (date, time)
- Added compound-object geometry queries: `getObjectType()`, `getObjectCenter()`, `getObjectBoundingBox()`, `getObjectPrimitiveUUIDs()` (single/list/nested), plus per-type getters for tile, sphere, box, disk, tube, and cone objects (center, size, subdivision count, normal, vertices, radius, node/radius data, axis, length, volume)
- Added primitive geometry queries: `getPatchCenter()`, `getPatchSize()`, `getTriangleVertex()`, `getVoxelCenter()`, `getVoxelSize()`, `getPatchCount()`, `getTriangleCount()`, `getPrimitiveBoundingBox()` (single UUID or list)
- Added `setPrimitiveColor()` for mutating the color of one primitive or a list of primitives, accepting either `RGBcolor` or `RGBAcolor`
- Added `clearPrimitiveData()` and `listPrimitiveData()` for removing and inspecting per-primitive data fields
- Added domain cropping: `cropDomainX()`, `cropDomainY()`, `cropDomainZ()`, and `cropDomain()` to restrict all primitives (or a supplied UUID list) to given XYZ bounds

# [v0.1.18] 2026-03-18

- Updated helios-core to v1.3.70

## Plant Architecture
- Added optional `include_hidden` parameter to `getAllPlantUUIDs()` to allow querying hidden prototype primitives
- `deletePlantInstance()` now automatically cleans up hidden prototype primitives when all plant instances have been deleted

## Context
- Added `doesPrimitiveExist()` method to check whether primitives exist by single UUID or list of UUIDs
- Added `resolveMaterialTextures()` method for material-based texture suppression resolution (modifies colors in-place, returns resolved texture paths)
- Added `packGPUBuffers()` method to pack GPU-ready geometry buffers into a single binary blob for zero-copy Three.js BufferGeometry loading

# [v0.1.17] 2026-03-15

- Updated helios-core to v1.3.68

## Context
- Added `addPatchTextured()` method for creating textured patches with optional UV coordinates
- Added `clearTimeseriesData()` method to remove all timeseries variables and their associated date/time values from the Context

## Plant Architecture
- Added `germination_rate` parameter to `buildPlantCanopyFromLibrary()` to control the fraction of grid positions occupied by plants
- Added `setProgressCallback()` for receiving `(progress, message)` updates during long-running operations like `advanceTime()`

# [v0.1.16] 2026-03-12

- Updated helios-core to v1.3.67

## Context
- Added primitive texture management methods: `getPrimitiveTextureFile()`, `setPrimitiveTextureFile()`, `getPrimitiveTextureSize()`, `getPrimitiveTextureUV()`, `primitiveTextureHasTransparencyChannel()`, `getPrimitiveSolidFraction()`, `overridePrimitiveTextureColor()`, `usePrimitiveTextureColor()`, `isPrimitiveTextureColorOverridden()`
- Primitive getters now accept a list of UUIDs for efficient batch queries returning NumPy arrays (e.g., `getPrimitiveNormal([uuid1, uuid2])` returns an ndarray of shape (N, 3))
- Added `getAll*` convenience methods that query all primitives in the context (e.g., `getAllPrimitiveNormals()`)
- Extended `PrimitiveInfo` with `texture_file`, `texture_uv`, and `solid_fraction` fields
- Added timeseries data management: `addTimeseriesData()`, `setCurrentTimeseriesPoint()`, `queryTimeseriesData()`, `queryTimeseriesDate()`, `queryTimeseriesTime()`, `getTimeseriesLength()`, `doesTimeseriesVariableExist()`, `listTimeseriesVariables()`, `loadTabularTimeseriesData()`

## Radiation Model
- Added EXR image export methods: `writeCameraImageDataEXR()`, `writeDepthImageData()`, `writeDepthImageDataEXR()`, `writeNormDepthImage()`
- Added `getBackendName()` and `probeAnyGPUBackend()` for runtime GPU backend detection
- Updated error messages to reflect runtime backend auto-detection (OptiX 8 -> OptiX 6 -> Vulkan)

## Validation
- Added `isinstance()`-based type validation to PlantArchitecture and RadiationModel methods per argument type validation policy
- Added `validate_position_like()`, `validate_direction_like()`, and `validate_size_like()` validators for flexible parameter types

# [v0.1.15] 2026-03-06

- Updated helios-core to v1.3.65

## Radiation Model
- Added Vulkan compute backend, enabling GPU ray tracing on AMD, Intel, and Apple Silicon GPUs without CUDA/OptiX
- Radiation plugin now supported on macOS via Vulkan (MoltenVK)
- Build system updated to compile and package SPIR-V shaders alongside PTX files
- Wheel builds on macOS now include radiation and energybalance plugins with bundled MoltenVK runtime

## Build & Packaging
- Dropped Python 3.8 support; added Python 3.12 and 3.13
- CI Vulkan SDK installation step added for macOS wheel builds
- Library loader auto-configures `VK_ICD_FILENAMES` for bundled MoltenVK on macOS

## Testing
- Excluded `tests/manual/` directory from automatic pytest collection
- Fixed visualizer headless detection on macOS (skip unless `PYHELIOS_TEST_VISUALIZER` is set)

# [v0.1.14] 2026-01-30

🚨++ New Plug-in Integrated ++ 🚨
- Terrestrial LiDAR plug-in integrated

- Updated helios-core to v1.3.63

## Core
- Added `Context.seedRandomGenerator()` for reproducible stochastic simulations

## LiDAR
- Removed CollisionDetection as explicit Python API dependency (handled at C++ level)

## Energy Balance
- Energy balance tests now work without radiation plugin by setting radiation flux data manually

# [v0.1.13] 2025-12-25

- Updated helios-core to v1.3.61

## Energy Balance
- **CUDA is now optional**: Plugin uses three-tier execution - GPU (CUDA), OpenMP (parallel CPU), or serial CPU fallback
- Added GPU acceleration control methods: `enableGPUAcceleration()`, `disableGPUAcceleration()`, `isGPUAccelerationEnabled()`, and `isGPUAccelerationAvailable()`
- OpenMP CPU mode is recommended for most workloads without GPU

## Plant Architecture
- Added capability to modify parameters for library plants or build custom plants

# [v0.1.12] 2025-12-15

- Many updates to documentation, transitioning toward consistency with c++ docs
- `pytest-forked` was missing from standard pyhelios dependencies
- Updated helios-core to v1.3.60

## Radiation Model
- Added camera zoom parameter

# [v0.1.11] 2025-12-05

- Updated helios-core to v1.3.59

## Core
- Added `magnitude()` and `normalize()` methods to vec2 and vec3
- Added `scale()` method to RGBcolor and RGBAcolor for color intensity adjustment
- Added `JulianDay()`, `incrementDay()`, and `isLeapYear()` methods to Date
- Added `scaleConeObjectLength()` and `scaleConeObjectGirth()` methods for cone object manipulation

## Solar Position
- Added modern state-based API with `setAtmosphericConditions()`, `getAtmosphericConditions()`, and parameter-free flux methods
- Added `getAmbientLongwaveFlux()` for ambient longwave radiation calculation
- Added Prague Sky Model support with `enablePragueSkyModel()`, `updatePragueSkyModel()`, `isPragueSkyModelEnabled()`, and `pragueSkyModelNeedsUpdate()`

## Leaf Optics
- Added `optionalOutputPrimitiveData()` for selective biochemical property output (chlorophyll, carotenoid, water, etc.)
- CRITICAL BUG: leaf optics was not being built with default build

## WeberPennTree
- Added `loadXML()` method for loading custom tree species from XML files
- Extended `buildTree()` to accept custom species names (strings) in addition to `WPTType` enum

# [v0.1.10] 2025-12-02

🚨++ New Plug-in Integrated ++ 🚨
- Leaf Optics plug-in integrated

- Updated helios-core to v1.3.58

## Context
- Added complete materials system with `addMaterial()`, `setMaterialColor()`, `setMaterialTexture()`, and material assignment methods
- Materials enable efficient memory usage by sharing visual properties across multiple primitives

## Radiation Model
- Extended camera properties with lens focal length, sensor dimensions, shutter speed, and metadata fields
- Added camera library support with `addRadiationCameraFromLibrary()` for preconfigured camera models
- Added `updateCameraParameters()` and `enableCameraMetadata()` for camera management
- Camera properties array expanded from 6 to 9 floats (added lens_focal_length, sensor_width_mm, shutter_speed)

## Solar Position
- Integrated SSolar-GOA spectral solar model with `calculateDirectSolarSpectrum()`, `calculateDiffuseSolarSpectrum()`, and `calculateGlobalSolarSpectrum()`
- Added SolarPosition plugin asset management for SSolar-GOA data files

# [v0.1.9] 2025-11-27

- Updated helios-core to v1.3.57
- There was a memory leak issue in the core and all plug-ins due to missing `__del__` methods, which should be fixed now.

## Core
- Added overloaded `Context.setPrimitiveData[*]()` to accept a list of UUIDs
- Added `Context.deletePrimitive()` and `Context.deleteObject()` methods
- Added `Context.writePrimitiveData()` method to write primitive data to a file

## Radiation Model
- Added new radiation source types: `addRectangleRadiationSource()`, `addDiskRadiationSource()`
- Added source management: `setSourcePosition()`, `getSourcePosition()`, `deleteRadiationSource()`
- Added spectrum manipulation: `setSourceSpectrum()`, `integrateSpectrum()`, `scaleSpectrum()`, `blendSpectra()`
- Added diffuse radiation support: `setDiffuseRadiationExtinctionCoeff()`, `setDiffuseSpectrum()`, `getDiffuseFlux()`
- Added camera system: position, lookat, orientation, spectral response, and pixel data methods
- Added utility methods: `doesBandExist()`, `getSkyEnergy()`, `calculateGtheta()`, `enforcePeriodicBoundary()`
- Extended `copyRadiationBand()` to support optional wavelength range parameters

# [v0.1.8] 2025-10-15

- Updated helios-core to v1.3.55

## PlantArchitecture
- Added custom plant building API with `addPlantInstance()`, `addBaseStemShoot()`, and `addChildShoot()`
- Added collision detection support with `plantDoesCollide()`
- Added `AxisRotation` data type for shoot rotation control
- Expanded plant library to 28 models (added apple_fruitingwall, asparagus, tomato)
- Added `plantarch_custom_building_sample.py`, `plantarch_collision_sample.py`, `plantarch_file_io_sample.py`

# [v0.1.7] 2025-10-11

- Updated helios-core to v1.3.53, which includes a number of upgrades to the visualizer

# [v0.1.6] 2025-10-06

- Reconfigured wheel builds to keep all generated files in `pyhelios_build` directory
- Fixed README.md badge so wheel builds will show 'passing'
- Added missing files in `pyhelios/runtime/` directory to git control

# [v0.1.5] 2025-10-06

🚨++ New Plug-in Integrated ++ 🚨
- Boundary-layer conductance plug-in integrated

- Updated helios-core to v1.3.52

- Removed pre-built wheels for Intel Macs. Free-tier Intel MacOS runners are no longer available on GitHub. Intel Mac users will need to build from source.

# [v0.1.4] 2025-09-25

- Updated helios-core to v1.3.51

## Visualizer
- Fixed issue where font assets were not being copied to the build directory

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