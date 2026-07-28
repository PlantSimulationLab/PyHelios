# Changelog

# [v0.1.26] 2026-07-28

- Updated helios-core to v1.3.78

## Core
- Fixed use-after-free crashes when a plugin model outlives its Context. Every plugin model (`RadiationModel`, `EnergyBalanceModel`, `PhotosynthesisModel`, `StomatalConductanceModel`, `BoundaryLayerConductanceModel`, `LeafOptics`, `SolarPosition`, `PlantArchitecture`, `WeberPennTree`, `Visualizer`, and `LiDARCloud`'s collision detection) passes the raw native `Context*` to a C++ constructor that stores it for the model's lifetime. Destroying the Context first — by leaving its `with` block, or by letting a temporary Context (e.g. `visualizer.buildContextGeometry(make_scene())`) be garbage collected — freed that memory while the model still held the pointer, so the next call segfaulted the interpreter. Models now retain a Python reference to the owning Context and check liveness before every native call, raising an actionable `RuntimeError` instead of crashing. `LiDARCloud` additionally rejects `enableCollisionDetection()` with a second, different Context, which the native side silently ignored (it keeps whichever Context it was first given).
- Vector and color validators now check the concrete type rather than relying on attribute presence. A `vec4` satisfied a `vec3` attribute check and reached C++ as a wrong-length buffer (`to_list()` returns 4 elements), and an `RGBAcolor` satisfied an `RGBcolor` check with its alpha channel silently discarded. Both now raise `ValidationError`.
- `Context.getPrimitiveInfo()` no longer swallows every exception from the texture and solid-fraction getters. Only `NotImplementedError` (the getter absent from an older library build) leaves those fields as `None`; genuine native errors propagate, and each getter is attempted independently so one failure cannot suppress the others.
- **Behavior change inherited from helios-core 1.3.78:** `Context.rotateObject(objID, angle, "z")` now rotates in the opposite direction than it did previously. The native `CompoundObject::rotate()` "z" string-axis branch alone negated the rotation angle, disagreeing with `rotatePrimitive()` and with the `vec3`-axis `rotateObject()` overload; the negation is removed so all three rotation paths share one handedness. PyHelios passes the angle through unchanged at every layer, so this lands directly in the Python API. Any code that compensated for the old flipped azimuth by negating its angle is now rotating the wrong way and must drop the compensation.
- Added coverage for `getObjectBoundingBox()` returning a degenerate box for a single-primitive object. The native implementation seeds the box from the first primitive's first vertex and then `continue`s to the next primitive, so the remaining vertices of that primitive are never compared against the seed. An object made of one primitive — a `1x1` tile, for example — therefore reports `min == max == ` its first vertex, and any object list whose *first* object holds a unique extreme loses that extreme. `getObjectBoundingBox([])` likewise returns a plausible-looking `(0,0,0)`–`(0,0,0)` box rather than failing, because the Python wrapper zero-initializes its output buffers; once fixed, a request covering no primitives raises instead. **The fix belongs to the Helios repository, not to PyHelios** (PyHelios must never patch the vendored `helios-core` submodule); it is applied there in `core/src/Context.cpp` with three accompanying core self-tests, and lands in PyHelios when the submodule pointer advances past v1.3.78. The new PyHelios tests assert the fixed behavior and are marked `xfail` until then. The pre-existing bounding-box tests — in both repos — passed only because they used a box object, whose six faces cover each other's extremes, masking the skipped face.
- Added test coverage for `rotatePrimitive()` and `rotateObject()`, which previously had none across their 14 wrapped entry points — the reason the z-axis handedness change above would have passed the suite unnoticed. The new tests pin the rotation convention (a +90° z-rotation maps (x,y) → (y,−x)) and assert that the string-axis, `vec3`-axis, primitive, and object paths all agree, so a future divergence in any one of them fails loudly. Verified by re-introducing the old negation and confirming only the `z` case goes red.
- Corrected the documented meaning of `about_origin=True` on `rotateObject()` and `scaleObject()`. Both docstrings claimed the operation was about the **global** origin (0,0,0); the native `rotateObjectAboutOrigin()`/`scaleObjectAboutOrigin()` actually use the object's own stored `object_origin`, so an object built away from the world origin spins or scales in place rather than orbiting (0,0,0). Only the documentation was wrong — no behavior changed. To rotate about a specific point, pass it as `origin`.
- Two latent bugs reachable from the PyHelios API are fixed upstream with no PyHelios change: multi-ring colored `addDisk()`/`addDiskObject()` (`ndivs=int2(nr, ntheta)` with `ntheta >= 2`) no longer leaves the first triangle of each outer ring stranded at the world origin, and `getDomainBoundingBox(uuids=[...])` no longer returns an under-sized upper bound when the same vertex also set a new lower bound on that axis.
- Fixed `Context.__del__` printing a spurious traceback at interpreter exit. A `Context` still alive when the interpreter shuts down is finalized after module globals and the import machinery have been torn down, so `context_wrapper.destroyContext` could already be gone. The destructor called it unguarded and then ran `import warnings` inside its `except` handler — but importing is no longer possible at that point, so the handler itself raised and CPython printed `Exception ignored in: <function Context.__del__>` with a traceback pointing at the *import* line, hiding the original error. `warnings` is now imported at module scope and the handler cannot raise. This was cosmetic teardown noise rather than a leak (the OS reclaims the allocation at process exit either way), but it produced an alarming and misleading traceback. Reported as GitHub issue #4.

## Radiation
- Fixed `writeCameraImage()` reporting `invalid map<K, T> key` for an unrendered camera. Camera pixel data is populated only by `runBand()`, and only for the bands passed to that call and for cameras that already existed when it ran. Writing an image for a camera/band outside that set reached `std::map::at` in the native library and surfaced as a bare STL message with no indication of the cause. `writeCameraImage()` and `writeNormCameraImage()` now check the precondition first and raise a `RadiationModelError` naming the camera, the band, and the missing `runBand()` call. The underlying library guard lands in helios-core v1.3.79; this check remains useful for earlier cores. Reported as GitHub issue #4.
- Documented the camera rendering order that this implies (add camera → `updateGeometry()` → `runBand()` → write) and corrected two examples in `plugin_radiation.md` that would fail if copied: the time-series capture loop never called `runBand()`, and the complete-pipeline example wrote images from two cameras it never created.
- Fixed `addSunSphereRadiationSource()` placing the sun in the wrong position. The Python API documents `zenith`/`azimuth` in degrees, but the C interface passed them unconverted into `SphericalCoord(radius, elevation_radians, azimuth_radians)` — wrong units *and* wrong angle convention. An overhead sun (`zenith=0`) yielded 0 W/m² absorbed instead of the source flux. Degrees are now converted to radians and zenith to elevation; absorbed flux follows the cosine law.
- Corrected the documented units of the `wavelength_min`/`wavelength_max` arguments to `addRadiationBand()` and `copyRadiationBand()`: nanometers, not micrometers (the values were always passed through unscaled, so no behavior changed).
- Documented that `getTotalAbsorbedFlux()` returns flux **density** in W/m² per primitive, not power in watts — so `sum()` over the result is not physically meaningful; weight by `getPrimitiveArea()` to obtain watts.
- Documented the new `emission_enabled_<band>` global data that helios-core 1.3.78's `runBand()` writes for every band (`uint`, 1/0). It records which band governs longwave emission, which the energy balance model reads to select the emitting band's emissivity. It needs no new wrapper — the existing `Context.getGlobalData()` uint path returns it.

## Energy Balance
- Documented the `emissivity_[*]` input primitive data, which was missing from the PyHelios input-data table entirely. helios-core 1.3.78 also defined which emissivity is used when the energy balance runs over multiple bands: the emissivity of the single band for which emission is enabled, falling back to the first emission-enabled band (with a warning) if several emit, and to the first band that defines an emissivity when no emission information is available — the case a script hits when it sets radiation fluxes manually without running the `RadiationModel`.

## LiDAR
- Added terrain-following voxel grids mirroring helios-core 1.3.78: `addGrid()` accepts an optional `column_z_offsets` argument that shifts each vertical column of voxels in z by a per-column amount, so a grid can track an external terrain surface such as a DEM. The offsets are row-major as `[j*ndiv[0] + i]`, one value per (x,y) column, and are validated to have length `ndiv[0]*ndiv[1]`. Omitting the argument (or passing all zeros) builds the axis-regular grid exactly as before.
- Added `getCellRotation()`, which reports a grid cell's azimuthal rotation about the z-axis in **degrees**. This getter was previously unwrapped in PyHelios; helios-core 1.3.78 also changed its native units from radians to degrees, so it now matches the units expected by `addGrid()`.
- `getCellCenter()` now returns the **true world-space center** of a grid cell. For a grid built with a non-zero `rotation`, the native library previously returned the raw un-rotated lattice center, which did not lie in the same frame as the hit points, scan origins, or grid bounding box; it is now rotated about the grid anchor to match. Un-rotated grids are unaffected. Code that consumed `getCellCenter()` for a rotated grid and compensated for the missing rotation must drop that compensation.
- Corrected the documented units of the `addGrid()` `rotation` argument: **degrees**, not radians. The native `addGrid()` converts degrees internally, so a caller who followed the previous documentation and passed radians got a grid rotated by roughly 1/57th of the intended angle. No behavior changed — the value was always passed through unscaled — but the documentation was wrong. Note that `addGridCell()` genuinely does take radians (it stores the angle directly), so the two entry points differ; this asymmetry is inherited from the native API and is now documented on both methods.

## Plant Architecture
- `getPlantAge()`, `getPlantHeight()`, and `sumPlantLeafArea()` now raise on failure instead of returning `-1.0`, which was indistinguishable from a real measurement.

## Solar Position
- Fixed SolarPosition's SSolar-GOA spectral tables (`wehrli.dat`, `abscoef.dat`) being omitted from wheels, which made `calculateSpectralIrradiance()` fail on installed packages. The assets are now packaged, with the source path `assets/ssolar_goa` flattened to the `plugins/solarposition/ssolar_goa` location the C++ runtime opens.

# [v0.1.25] 2026-06-25

- Updated helios-core to v1.3.77

## Context
- `setTileObjectSubdivisionByAreaRatio()` now validates that `area_ratio >= 1` (raising `ValueError` otherwise) and its documentation is corrected: `area_ratio` is the ratio of the whole tile's area to an individual sub-patch's area (i.e. the approximate sub-patch count), not the sub-patch-to-tile fraction.

## LiDAR
- Added rotating-Risley-prism (Livox-style rosette) scans mirroring helios-core 1.3.77: `addScanRisley()` registers a non-repetitive rosette scan from a stack of rotating wedge prisms (the new `RisleyPrism` type — `wedge_angle`, `refractive_index`, `rotor_rate`, `phase`), a refractive index of air, a pulse repetition rate, and a 6-DOF trajectory (quaternion or Euler). The per-pulse beam direction is computed by full Snell's-law refraction through the prisms; the scan is stored as a single-row table with `ScanMode.RISLEY_PRISM` / `ScanPattern.RISLEY_PRISM` (new enum values). Query it with `getScanRisleyPrisms()` and `getScanRisleyRefractiveIndexAir()`.
- Added GPU-capability introspection: `isGPUAvailable()` (compiled with CUDA, a device present, and `HELIOS_NO_GPU` unset) and `isGPUAccelerationEnabled()` (whether GPU acceleration is currently toggled on).
- Added per-scan progress reporting for `syntheticScan()`: `setSyntheticScanProgressPointer(ctypes.c_int)` writes the 0-based index of the scan currently being ray-traced (set to `getScanCount()` when finished), and `setProgressCallback(fn)` invokes a Python callback with `(progress_fraction, message)` during the scan.
- Added `setSyntheticScanMemoryBudget(bytes)` to cap the transient ray-tracing scratch buffers `syntheticScan()` allocates when fanning each pulse into sub-rays, so a high-resolution scan is traced in chunks sized to the budget instead of one OOM-prone batch, plus `getSyntheticScanMemoryBudget()` to read it back (0 = automatic, path-dependent: 8 GiB on a GPU build, 4 GiB otherwise). The budget bounds only the live trace buffers, not the output cloud.
- Added `getHitDataColumnIndex(label)` to resolve a hit-data label to its internal column slot (−1 if never set), for repeated bulk access without re-resolving the label by string.
- The synthetic-scan return detection threshold now defaults to a realistic ~5% noise floor (helios-core 1.3.77), pairing with the recommended ~40 rays/pulse to suppress single-sub-ray phantom returns; set it per scan with `setScanDetectionThreshold()` (0 disables suppression, reproducing the previous "report every return" behavior).

## Plant Architecture
- Added `optionalOutputObjectData(labels)` to enable additional per-object output fields to be written onto the Context's compound objects after building (e.g. `age`, `rank`, `plantID`, `plant_height`, `phenology_stage`, `leafID`, `fruitID`, `carbohydrate_concentration`, or `"all"`); accepts a single label or a list.
- Consolidated the random-parameter helpers onto the typed model: `RandomParameter` (now an alias for `RandomParameterFloat`) and `RandomParameterInt` are the typed classes from `pyhelios.plant_architecture_params` and now return `RandomParameterFloat`/`RandomParameterInt` objects (round-trippable via `to_dict()`) rather than the previous plain dicts, with their factory methods (`constant`/`uniform`/`normal`/`weibull` and `constant`/`uniform`/`discrete`) now validating their arguments. `defineShootType()` accepts these objects embedded directly in a raw parameter dict.

# [v0.1.24] 2026-06-21

- Updated helios-core to v1.3.76

## LiDAR
- Added physical-parameter spinning and moving-platform raster scans mirroring helios-core 1.3.76: `addScanSpinning()` registers a continuously-rotating multibeam sensor (Velodyne/Ouster/Hesai) from per-channel **elevation** angles, an azimuth resolution, a pulse repetition rate (PRF), and a 6-DOF trajectory — deriving the azimuth grid, rotation rate, and revolution count internally — and `addScanMovingRaster()` sweeps a fixed angular fan along a quaternion trajectory. Both set a self-describing acquisition mode.
- **Removed `addScanMultibeam()` (breaking change).** In helios-core 1.3.76 a spinning scan must be created through the physical-parameter path; the legacy grid constructor that `addScanMultibeam()` wrapped produces a non-self-describing `STATIC_RASTER`-mode scan that no longer round-trips through XML as a spinning scan. Use `addScanSpinning()` instead (pass per-channel **elevation** angles, an `azimuth_step`, a `pulse_rate_hz`, and a trajectory in place of zenith angles, `Nphi`, and `phi_range`).
- Added scan acquisition-mode introspection: `getScanMode()` (new `ScanMode` enum: `STATIC_RASTER`/`MOVING_RASTER`/`SPINNING`), `getScanStepsPerRev()`, `getScanRotationRate()`, and `getScanRevolutions()`.
- Added analytic-waveform N-return configuration: `setScanReturnMode()`/`getScanReturnMode()` (new `ReturnMode` enum: `MULTI`/`SINGLE`), `setScanSingleReturnSelection()`/`getScanSingleReturnSelection()` (new `SingleReturnSelection` enum: `STRONGEST`/`FIRST`/`LAST`/`STRONGEST_PLUS_LAST`), `setScanMaxReturns()`/`getScanMaxReturns()`, `setScanPulseWidth()`/`getScanPulseWidth()`, `setScanDetectionThreshold()`/`getScanDetectionThreshold()`, and a `return_mode` argument on `syntheticScan()` that overrides the stored mode for one call. The new `echo_width` per-hit data field (return range spread) is now available.
- Added the columnar fast-path bulk reads `getHitDataColumn(label)` / `getHitDataColumnArray(label)`, which use the native cache-linear column storage and return full float64 precision (with an `absent_value` placeholder), versus the float32 of `getHitDataAll`/`getHitDataArray`.
- Added `setExternalTriangulation(vertices, scan_ids)` to drive leaf-area inversion from an externally-supplied mesh (a re-used Helios triangulation or a per-scan open3d Ball-Pivot mesh) instead of the internal Delaunay triangulation, accepting the `(T,9)`/`(T,3,3)`/flat layouts `getTriangleVerticesAll()` exports plus a per-triangle source scan ID (required for the G(theta) ray direction); `calculateLeafArea()` then runs unchanged.
- `syntheticScan()` gained a `cancel_flag` argument (a caller-owned `ctypes.c_int`) that aborts a long scan between pulses when set non-zero from another thread, returning whatever was scanned so far.

## Plant Architecture
- Added a typed, discoverable parameter model (`pyhelios.plant_architecture_params`) mirroring the nested C++ `ShootParameters`/`PhytomerParameters`/`LeafPrototype` structures (plus flat `CarbohydrateParameters`/`NitrogenParameters`), with `RandomParameterFloat`/`RandomParameterInt` distribution specs and `from_dict()`/`to_dict()` round-tripping to the plain-dict JSON transport. `getCurrentShootParameters()` gained a `return_typed` keyword to return a `ShootParameters` object, and `defineShootType()` now accepts either a nested dict or a `ShootParameters`. `getCurrentShootParameters()` now also surfaces the full `phytomer_parameters` sub-structure (internode/petiole/leaf/peduncle/inflorescence and the leaf prototype).
- Added carbohydrate- and nitrogen-model parameter access: `getDefaultCarbohydrateParameters()`/`setPlantCarbohydrateParameters()` and `getDefaultNitrogenParameters()`/`setPlantNitrogenParameters()`. The native API has no per-plant getter for these, so the get methods return the C++ default-constructed template (flat dict or typed object via `return_typed`) to modify and apply to a plant instance.
- `setPlantPhenologicalThresholds()` gained an `is_evergreen` keyword (default `False`) that retains leaves through dormancy instead of shedding them at senescence, matching the helios-core 1.3.76 signature.
- Added `setCancelFlag(cancel_flag)` to register a caller-owned `ctypes.c_int` that, when set non-zero from another thread, stops the canopy-build and `advanceTime()` growth loops between plants/timesteps (returning whatever was built so far) — so a long generation can be aborted mid-build.

# [v0.1.23] 2026-06-16

- Updated helios-core to v1.3.75

## Radiation
- Camera exposure mode is now plumbed through to the native camera: `addRadiationCamera()` and `updateCameraParameters()` read the `exposure` field (`"auto"`/`"manual"`/`"ISOXXX"`) from `CameraProperties` and pass it to helios-core, rather than always forcing `"auto"`.
- Added per-pixel data label map export: `writePrimitiveDataLabelMap()` and `writeObjectDataLabelMap()` write a camera's per-pixel primitive/object data values (float/double/uint/int) to a row-major ASCII text file (background pixels get a configurable `padvalue`, default NaN), plus `getPrimitiveDataLabelMap()`/`getObjectDataLabelMap()` convenience wrappers that return the map directly as a 2D `(height, width)` NumPy array (written to a temp file and loaded, no file left on disk).
- `calculateGtheta()` now calls `updateGeometry()` automatically (with a warning) if the scene geometry hasn't been pushed to the radiation model yet, and raises an explicit `RuntimeError` when the G-function is undefined (no geometry / zero leaf area) instead of silently returning NaN.

## LiDAR
- Added bulk NumPy exports that pull a whole hit cloud across a single FFI call instead of per-hit getters (which dominated synthetic-scan extraction time for million-point clouds): `getHitsXYZRGBArrays()` (returns `(N,3)` float32 coordinates and colors), `getHitDataArray(label)` (`(N,)` float32, NaN where the label is absent), `getHitScanIDArray()` (`(N,)` int32), and `getHitMissArray()` (`(N,)` int32, 1 = miss).
- Added moving-platform (mobile/airborne) raster scans: `addScanMoving()` registers a scan driven by a timestamped 6-DOF pose trajectory (per-sample position plus orientation as quaternions or roll/pitch/yaw Euler angles), a sensor lever arm and boresight misalignment, and a pulse rate. The synthetic-scan generator emits a per-pulse origin and direction interpolated along the trajectory; every hit/miss records its own origin, timestamp, and firing index.
- Added `getHitOrigin(index)` returning the per-pulse beam-emission origin of a hit (the moving-platform origin, or the static scan origin as a fallback).
- Added a global scanner azimuth (heading) offset for synthetic scans: `addScan()`/`addScanMultibeam()` gained a `scan_azimuth_offset` keyword (radians; default 0 = no offset), queryable via `getScanAzimuthOffset()`. It applies a right-hand rotation about the world +z axis on top of the azimuth sweep.
- `calculateLeafArea()` gained an optional `Gtheta` argument: when supplied (with `min_voxel_hits` and `element_width`), leaf area is computed via a triangulation-free, beam-origin-aware inversion using the caller-supplied G(theta). This is the supported leaf-area path for moving-platform scans, whose pulses cannot be triangulated.

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