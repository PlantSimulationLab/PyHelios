# LiDAR Point Cloud Plugin Documentation {#LiDARDoc}

![LiDAR](images/LiDAR.png)

[TOC]

<table>
<tr><th>Dependencies</th><td>Visualizer plugin<br>CollisionDetection plugin</td></tr>
<tr><th>Python Import</th><td>`from pyhelios import LiDARCloud`</td></tr>
<tr><th>Main Class</th><td>\ref pyhelios.LiDARCloud.LiDARCloud "LiDARCloud"</td></tr>
</table>

## Known Issues {#LiDARissues}

- The LiDAR plugin requires the Visualizer plugin to be loaded for visualization operations
- The current version of leaf area calculations handles both discrete-return and multi-return data automatically

## Introduction {#LiDARintro}

The LiDAR plugin is used to process terrestrial LiDAR data into information that is useful for plant models. For example, this may be to determine leaf area and angle distributions at the voxel scale, or to reconstruct individual leaves and add them to the Context.

## Dependencies {#LiDARdepends}

The LiDAR plugin uses the CollisionDetection plugin for ray tracing. GPU acceleration is optional and controlled through the CollisionDetection plugin:
- For CPU-only operation: No additional dependencies required
- For GPU acceleration: NVIDIA CUDA-capable GPU and CUDA runtime (managed by CollisionDetection plugin)

To enable GPU acceleration for faster processing of large point clouds (requires future wrapper implementation):
```python
# Future API - not yet implemented
lidar.enableCDGPUAcceleration()
```

## Class Constructor {#LiDARConstructor}

<table>
<tr><th>Constructors</th></tr>
<tr><td>\ref pyhelios.LiDARCloud.LiDARCloud "LiDARCloud"</td></tr>
</table>

The \ref pyhelios.LiDARCloud.LiDARCloud "LiDARCloud" class contains point cloud data, and is used to perform processing operations on the data. The class constructor does not take any arguments.

```python
from pyhelios import LiDARCloud

# Initialize the LiDAR point cloud
with LiDARCloud() as pointcloud:
    # Perform operations
    pass
```

## Input Primitive Data {#LiDARInputData}

<table>
  <tr><th>Primitive Data Label</th><th>Symbol</th><th>Units</th><th>Data Type</th><th>Description</th><th>Available Plug-ins</th><th>Default Value</th></tr>
  <tr><td>reflectivity_lidar</td><td>\f$\rho_l\f$</td><td>unitless</td><td>\htmlonly<span style="font-family: Courier, monospace; color: green;">float</span>\endhtmlonly</td><td>Primitive reflectivity in the waveband of the laser. This is used to calculate the return intensity in synthetic scans.</td><td>N/A</td><td>1.0</td></tr>
</table>

## Background Information {#LiDARbg}

### Coordinates and Scan Pattern {#LiDARcoord}

The algorithms associated with the LiDAR plugin work with data obtained from a rectangular scan pattern. In this scan pattern, points are sampled at equally spaced intervals in both the zenithal (\f$\theta\f$) and azimuthal (\f$\varphi\f$) directions. At a given azimuthal angle, some range of zenithal angles are consecutively scanned, which represents a "scan line". Each scan line starts at some zenithal angle \f$\theta\f$<sub>min</sub> and ends at some zenithal angle \f$\theta\f$<sub>max</sub>. After recording a scan line at the first azimuthal angle \f$\varphi\f$<sub>min</sub>, the scanner incrementally moves to the next adjacent azimuthal scan direction and records the next scan line until it reaches the azimuthal angle \f$\varphi\f$<sub>max</sub>.

The number of zenithal points within each scan line is given by \f$\mathrm{N}_{\theta}\f$, and the total number of scan lines (i.e., number of individual azimuthal directions) is given by \f$\mathrm{N}_{\varphi}\f$.

Angles are specified in radians in the Python API (note: C++ API uses degrees). Distance units are arbitrary, but must be used consistently.

![Coordinate System](images/CoordinateSystem.jpeg)
*Scan pattern: the scanner traverses some range of zenithal and azimuthal angles to explore a portion of the spherical space surrounding the scanner.*

![Hit Schematic](images/HitSchematic.jpeg)
*For each scan direction, the scanner records the (x,y,z) Cartesian position of the point of intersection between the ray path and the object's surface. Each Cartesian position corresponds to spherical coordinate (zenith,azimuth) representing the scan direction.*

![Rectangular Scan](images/RectangularScan.png)
*The rectangular scan pattern creates quadrilateral polygons between four neighboring points.*

### Difference Between Discrete-Return and Full-Waveform LiDAR Data {#LiDARreturn}

The laser beam emitted from a LiDAR instrument has some finite diameter, which increases with distance from the scanner. In many cases, the beam diameter may be larger than the width of individual leaves by the time it reaches the canopy. This means that a single laser pulse may intersect multiple objects along its path to the ground.

For a **discrete-return** instrument, only one (or sometimes a few) hit points are recorded per laser pulse. The distance from the scanner recorded for the hit point is an effective average distance to all objects intersected by the beam.

By contrast, **full-waveform** instruments are able to record multiple hit point locations along a single laser pulse by analyzing the return timeseries or "waveform". This class of instruments is able to process the timeseries of pulse returns into separate distances. Full-waveform instruments are preferred because they provide more information, particularly in dense canopies where a discrete-return instrument would rarely record the location of the ground. Technically, full-waveform instruments ultimately output discrete hit points, but for the purposes of this documentation we will consider discrete-return data to have a single hit point per laser pulse, and full-waveform data to have an unlimited number of hit points per laser pulse.

There is sometimes ambiguity or inconsistency in usage of the terms discrete-return and full-waveform LiDAR data in the literature. For the purposes of this documentation, we will call "discrete-return" data as a scan that records only a single hit point per laser pulse, and "full-waveform" data as a scan that can record a large number of hit points per laser pulse.

![Waveform Schematic](images/WaveformSchematic.jpeg)

### Scan Metadata {#ScanMetadata}

Each scan has a set of parameters or "metadata" that must be specified in order to process the data. Some parameters are optional, while some are required. The following metadata is needed to define the overall scan itself, in addition to individual scan hit points.

<table>
<tr><th>Metadata</th><th>XML tag</th><th>Description</th><th>Python Parameter</th><th>Default behavior</th></tr>
<tr><td>Scanner origin</td><td>\<origin></td><td>(x,y,z) coordinate of the scanner. This is the position where the scanner rays are sent from.</td><td>`origin` (vec3)</td><td>None: REQUIRED</td></tr>
<tr><td>Size</td><td>\<size></td><td>Number of scan points in the theta (zenithal) and phi (azimuthal) directions.</td><td>`Ntheta`, `Nphi` (int)</td><td>None: REQUIRED</td></tr>
<tr><td>\f$\theta\f$<sub>min</sub></td><td>\<thetaMin></td><td>Minimum scan theta (zenithal) angle. \f$\theta\f$<sub>min</sub>=0 if the scan starts from upward vertical, \f$\theta\f$<sub>min</sub>=π/2 if the scan starts from horizontal. **Note: Python API uses radians; XML uses degrees.**</td><td>`theta_range[0]` (radians)</td><td>0</td></tr>
<tr><td>\f$\theta\f$<sub>max</sub></td><td>\<thetaMax></td><td>Maximum scan theta (zenithal) angle. \f$\theta\f$<sub>max</sub>=π/2 if the scan ends at horizontal, \f$\theta\f$<sub>max</sub>=π if the scan ends at downward vertical. **Note: Python API uses radians; XML uses degrees.**</td><td>`theta_range[1]` (radians)</td><td>π</td></tr>
<tr><td>\f$\varphi\f$<sub>min</sub></td><td>\<phiMin></td><td>Minimum scan phi (azimuthal) angle. \f$\varphi\f$<sub>min</sub>=0 if the scan starts pointing in the +y direction, \f$\varphi\f$<sub>min</sub>=π/2 if the scan starts pointing in the +x direction. **Note: Python API uses radians; XML uses degrees.**</td><td>`phi_range[0]` (radians)</td><td>0</td></tr>
<tr><td>\f$\varphi\f$<sub>max</sub></td><td>\<phiMax></td><td>Maximum scan phi (azimuthal) angle. \f$\varphi\f$<sub>max</sub>=π/2 if the scan ends pointing in the +x direction, \f$\varphi\f$<sub>max</sub>=π if the scan ends pointing in the -y direction. NOTE: \f$\varphi\f$<sub>max</sub> could be greater than 2π if \f$\varphi\f$<sub>min</sub> > 0 and the scanner makes a full rotation. **Note: Python API uses radians; XML uses degrees.**</td><td>`phi_range[1]` (radians)</td><td>2π</td></tr>
<tr><td>Translation</td><td>\<translation></td><td>Global (x,y,z) translation to be applied to entire scan, including the origin and all hit points.</td><td>Use `coordinateShift()`</td><td>No translation</td></tr>
<tr><td>Rotation</td><td>\<rotation></td><td>Global spherical rotation (theta,phi) to be applied to the entire scan, including the origin and all hit points.</td><td>Use `coordinateRotation()`</td><td>No rotation</td></tr>
<tr><td>Beam exit diameter (meters)</td><td>\<exitDiameter></td><td>Effective diameter of laser beam exiting the instrument. Only used for full-waveform synthetic data generation.</td><td>`exit_diameter`</td><td>0 (discrete return)</td></tr>
<tr><td>Beam divergence angle (rad)</td><td>\<beamDivergence></td><td>Angle of laser beam divergence after exiting the instrument. Only used for full-waveform synthetic data generation.</td><td>`beam_divergence`</td><td>0</td></tr>
<tr><td>ASCII point cloud file</td><td>\<filename></td><td>File containing point cloud data to be read.</td><td>Loaded via `loadXML()`</td><td>No file will be read</td></tr>
<tr><td>ASCII file column format</td><td>\<ASCII_format></td><td>Labels for columns in ASCII point cloud file. See section below for possible values and examples.</td><td>Loaded via `loadXML()`</td><td>x y z</td></tr>
</table>

### Hit Point Data {#AddHits}

In addition to scan metadata, the data collected by the scan itself must also be added to the plugin. This can be achieved by either reading data from an ASCII text file, or performing a synthetic scan. At a minimum, point cloud data consists of the Cartesian (x,y,z) coordinates of each hit in the scan. Additionally, hit points may also have an associated r-g-b color value, or some other scalar data value such as intensity or temperature.

For the processing algorithms to work, the scan direction associated with each hit point must also be known. This can be specified directly as a (\f$\theta\f$,\f$\varphi\f$) spherical coordinate, or using the row (i.e., index in the scanline: 1...\f$\mathrm{N}_\theta\f$) and column (i.e., scanline index: 1...\f$\mathrm{N}_\varphi\f$). Otherwise, it will calculate the scan direction by drawing a line between the scan origin position and the hit point.

For full-waveform data, additional information is needed about the hit points. Specifically, the total number of hit points along the pulse. The index can start at 0 or 1 for the first hit along the pulse, it just should be consistent for all points.

## Loading Scan Data from File {#ScanIO}

Scan metadata is typically specified by loading an XML file containing the relevant metadata for each scan. For real data, the XML file specifies the path to an ASCII text file that contains the data for each scan. For synthetic data, the parameters of the simulated scan are loaded from the XML file and used to perform the scan.

The code below gives a sample XML file for loading multiple scans. As specified in the metadata table above, not all entries are required.

```xml
<helios>
  <scan>
    <filename>/path/to/data/file.xyz</filename>
    <ASCII_format>x y z r255 g255 b255 target_count target_index timestamp</ASCII_format>
    <origin>0 0 0</origin>
    <size>2500 4500</size>
    <thetaMin>30</thetaMin>
    <thetaMax>130</thetaMax>
    <phiMin>0</phiMin>
    <phiMax>360</phiMax>
    <translation>1.2 1.5 -10.2</translation>
    <rotation>20 180</rotation>
    <exitDiameter>0.005</exitDiameter>
    <beamDivergence>0.003</beamDivergence>
  </scan>
</helios>
```

The ASCII text file containing the data is a plain text file, where each row corresponds to a hit point and each column is some data value associated with that hit point. The "ASCII_format" tag defines the column format of the ASCII text file. Each entry in the list specifies the meaning of each column. Possible fields are listed in the table below:

<table>
<tr><th>Label</th><th>Description</th><th>Default behavior</th></tr>
<tr><td>x</td><td>x-component of the (x,y,z) Cartesian coordinate of the hit point.</td><td>None: REQUIRED</td></tr>
<tr><td>y</td><td>y-component of the (x,y,z) Cartesian coordinate of the hit point.</td><td>None: REQUIRED</td></tr>
<tr><td>z</td><td>z-component of the (x,y,z) Cartesian coordinate of the hit point.</td><td>None: REQUIRED</td></tr>
<tr><td>zenith (or zenith_rad)</td><td>Zenithal angle of scan ray direction corresponding to the hit point. If "zenith_rad" is used, theta has units of radians rather than degrees.</td><td>Calculated from scan origin and hit (x,y,z)</td></tr>
<tr><td>azimuth (or azimuth_rad)</td><td>Azimuthal angle of scan ray direction corresponding to the hit point. If "azimuth_rad" is used, phi has units of radians rather than degrees.</td><td>Calculated from scan origin and hit (x,y,z)</td></tr>
<tr><td>r (or r255)</td><td>Red component of (r,g,b) hit color. If "r" tag is used, r is a floating point value between 0 and 1. If "r255" is used, r is an integer between 0 and 255.</td><td>r=1 or r255=255</td></tr>
<tr><td>g (or g255)</td><td>Green component of (r,g,b) hit color. If "g" tag is used, g is a floating point value between 0 and 1. If "g255" is used, g is an integer between 0 and 255.</td><td>g=0 or g255=0</td></tr>
<tr><td>b (or b255)</td><td>Blue component of (r,g,b) hit color. If "b" tag is used, b is a floating point value between 0 and 1. If "b255" is used, b is an integer between 0 and 255.</td><td>b=0 or b255=0</td></tr>
<tr><td>target_count</td><td>Number of hits along scan pulse.</td><td>Assumed to be discrete return data</td></tr>
<tr><td>target_index</td><td>Index of hit along scan pulse.</td><td>Assumed to be discrete return data</td></tr>
<tr><td>timestamp</td><td>Unique timestamp of hit point.</td><td>Assumed to be discrete return data</td></tr>
<tr><td>deviation</td><td>Indication of variability in return within a given hit point. Note: this is never used for real data, but can be output for synthetic data.</td><td>N/A</td></tr>
<tr><td>intensity</td><td>Intensity of return. Note: this is never used for real data, but can be output for synthetic data.</td><td>N/A</td></tr>
<tr><td>(label)</td><td>User-defined floating-point data value. "label" can be any string describing data. For example, "temperature", etc.</td><td>N/A</td></tr>
</table>

The XML file can be automatically loaded into the point cloud using the `loadXML()` method:

```python
from pyhelios import LiDARCloud

with LiDARCloud() as pointcloud:
    pointcloud.loadXML("/path/to/file.xml")
```

## Establishing Grid Cells {#LiDARgrid}

Rectangular grid cells are used as the basis for processing point cloud data. For example, total leaf area (or leaf area density) may be calculated for each grid cell. Grid cells or "voxels" are parallelpiped volumes. The top and bottom faces are always horizontal, but the cells can be rotated in the azimuthal direction.

Grid cells are defined by specifying the (x,y,z) position of its center, and the size of the cell in the x, y, and z directions. Additional optional information can also be provided for grid cells, which are detailed below.

<table>
<tr><th>Tag</th><th>Description</th><th>Default behavior</th></tr>
<tr><td>center</td><td>(x,y,z) Cartesian coordinates of cell center.</td><td>None: REQUIRED</td></tr>
<tr><td>size</td><td>Length of cell sides in x, y, and z directions.</td><td>None: REQUIRED</td></tr>
<tr><td>rotation</td><td>Azimuthal rotation of the cell in radians (Python API uses radians; XML uses degrees).</td><td>0</td></tr>
<tr><td>Nx</td><td>Grid cell subdivisions in the x-direction.</td><td>1</td></tr>
<tr><td>Ny</td><td>Grid cell subdivisions in the y-direction.</td><td>1</td></tr>
<tr><td>Nz</td><td>Grid cell subdivisions in the z-direction.</td><td>1</td></tr>
</table>

The grid cell subdivisions options allow the cells to be easily split up into a grid of smaller cells. For example, Nx=Ny=Nz=3 would create 27 grid cells similar to a "Rubik's cube".

Grid cell options can be specified in an XML file using the tags listed in the table above. Multiple grid cells are added by simply adding more `<grid>...</grid>` groups to the XML file.

```xml
<grid>
  <center>0 0 0.5</center>
  <size>1 1 1</size>
  <rotation>30</rotation>
  <Nx>3</Nx>
  <Ny>3</Ny>
  <Nz>3</Nz>
</grid>
```

One way to figure out the appropriate dimension and position of the voxel grid is using the Visualizer and trial-and-error. Make a guess of the voxel parameters, then visualize the point cloud and voxels together and adjust accordingly.

An often faster way to figure out the dimensions of the voxel grid is to use point cloud visualization software such as [Cloud Compare](https://www.cloudcompare.org). Load the point cloud data into Cloud Compare, then add a Box (file->Primitive Factory). You can translate or rotate the box, then find the resulting box location and dimensions in the Properties pane.

![LiDAR Voxel Grid](images/LiDARvoxelgrid.png)

Grid cells can be added programmatically using the Python API:

```python
from pyhelios import LiDARCloud
from pyhelios.types import vec3

with LiDARCloud() as lidar:
    # Add a rectangular grid with subdivisions
    lidar.addGrid(
        center=vec3(0, 0, 0.5),    # Grid center
        size=vec3(10, 10, 1),       # Grid dimensions
        ndiv=[10, 10, 5],           # 10x10x5 = 500 cells
        rotation=0.0                # No rotation
    )

    # Or add individual grid cells
    lidar.addGridCell(
        center=vec3(5, 5, 0.5),
        size=vec3(1, 1, 0.5),
        rotation=0.0
    )

    # Query grid properties
    cell_count = lidar.getGridCellCount()
    for i in range(cell_count):
        center = lidar.getCellCenter(i)
        size = lidar.getCellSize(i)
        print(f"Cell {i}: center=({center.x}, {center.y}, {center.z}), size=({size.x}, {size.y}, {size.z})")
```

## Processing LiDAR Data {#LiDARprocess}

### Hit Point Triangulation {#LiDARtri}

A triangulation between adjacent points is typically required for any of the available data processing algorithms. In the triangulation, adjacent hit points are connected to form a mesh of triangular solid surfaces. The algorithm for performing this triangulation is described in detail in [Bailey and Mahaffee (2017a)](http://dx.doi.org/doi:10.1016/j.rse.2017.03.011).

There are two possible options to be specified when performing the triangulation. A required option is \f$L_{max}\f$, which is the maximum allowable length of a triangle side. This parameter prevents triangles from connecting adjacent leaves (i.e., we only want triangles to be formed with neighboring points on the same leaf). Typically we want \f$L_{max}\f$ to be much larger than the spacing between adjacent hit points, and much smaller than the characteristic length of a leaf. For example, [Bailey and Mahaffee (2017a)](http://dx.doi.org/doi:10.1016/j.rse.2017.03.011) used 5cm for a cottonwood tree.

Another optional parameter is the maximum allowable aspect ratio of a triangle, which is the ratio of the length of the longest triangle side to the shortest triangle side. This has a similar effect as the \f$L_{max}\f$ parameter, and works better in some cases.

**Note:** For multi-return LiDAR data (detected automatically via target_count field), the triangulation uses an adaptive separation ratio filter instead of the aspect ratio parameter. This filter calculates the ratio of spatial distance to angular separation for each triangle edge and rejects triangles where this ratio is anomalously high (indicating points that are angularly close but spatially distant, characteristic of "sliver" triangles from beam spreading). The threshold is automatically calculated as 4.6 times the 25th percentile of the separation ratio distribution, eliminating the need for manual tuning. This approach is robust across different leaf sizes and scan resolutions.

Example triangulation:

```python
from pyhelios import LiDARCloud

with LiDARCloud() as pointcloud:
    pointcloud.loadXML("/path/to/file.xml")

    # Perform triangulation with Lmax=0.05 and maximum aspect ratio of 5
    pointcloud.triangulateHitPoints(Lmax=0.05, max_aspect_ratio=5)
```

### Calculating Leaf Area for Each Grid Cell {#LiDARleafarea}

Using the triangulation and defined grid cells, the plugin can calculate the leaf area (and leaf area density) for each grid cell. The algorithm for calculating leaf area is described in detail in [Bailey and Mahaffee (2017b)](http://dx.doi.org/doi:10.1088/1361-6501/aa5cfd) (except that in the current implementation, weighting by the sine of the scan zenith direction has been removed).

Performing the calculations is simple and requires no inputs. Note that the leaf area calculation requires that the triangulation has been performed beforehand. If no triangulation is available, the plugin will assume a uniformly distributed leaf angle orientation (\f$G=0.5\f$). The leaf area calculation also requires that at least one grid cell was defined.

When using real LiDAR data, it is recommended to gapfill sky/miss points if this has not already been done by the scanner or in pre-processing. When a laser pulse does not intersect any object and reaches the sky, many scanners do not record any hit points. These miss points are important for accurate determination of leaf area.

Example leaf area calculation:

```python
from pyhelios import Context, LiDARCloud
from pyhelios.types import vec3

with Context() as context:
    # Add geometry to context
    context.addPatch(center=vec3(0, 0, 0.5), size=vec2(0.1, 0.1))

    with LiDARCloud() as lidar:
        lidar.loadXML("/path/to/file.xml")

        # Add grid cells
        lidar.addGrid(
            center=vec3(0, 0, 0.5),
            size=vec3(10, 10, 1),
            ndiv=[5, 5, 2],
            rotation=0.0
        )

        # Triangulate hit points
        lidar.triangulateHitPoints(Lmax=0.05, max_aspect_ratio=5)

        # Assign hit points to grid cells
        lidar.calculateHitGridCell()

        # Calculate leaf area for each grid cell
        lidar.calculateLeafArea(context)

        # Export results
        lidar.exportLeafAreas("leaf_areas.txt")
        lidar.exportLeafAreaDensities("leaf_area_densities.txt")

        # Query individual cell results
        for i in range(lidar.getGridCellCount()):
            leaf_area = lidar.getCellLeafArea(i)
            lad = lidar.getCellLeafAreaDensity(i)
            print(f"Cell {i}: LA={leaf_area:.4f} m², LAD={lad:.4f} m²/m³")
```

**Note:** Gapfilling sky/miss points (`gapfillMisses()`) is not yet wrapped. For this functionality, use the C++ API.

### Plant Reconstruction {#LiDARreconstruction}

A leaf-by-leaf reconstruction can be performed for the plant of interest using the method described in [Bailey and Ochoa (2018)](https://www.sciencedirect.com/science/article/pii/S0034425718300191). The reconstruction utilizes the triangulation and leaf area computations to ensure the correct leaf angle and area distributions on average, and thus requires that these routines have been run before performing the reconstruction.

There are two types of available reconstructions:

1. **Triangular reconstruction**: Directly uses triangles resulting from the triangulation to produce the reconstruction. The advantage is that it does not require any assumption about the shape of the leaf and can give a more direct reconstruction in some cases. However, this reconstruction is typically not recommended as it often results in many small triangle groups that don't necessarily resemble actual leaves.

2. **Alpha Mask reconstruction**: Replaces the triangle groups with a "prototype" leaf (which is an alpha mask). This ensures that all reconstructed leaves are representative of an actual leaf in terms of shape and size.

**Note:** Reconstruction methods are not yet wrapped in the current PyHelios implementation. These will be added in a future release. For now, use the C++ API for reconstruction operations.

## Generating Synthetic (Simulated) LiDAR Data {#LiDARsynthetic}

The LiDAR plugin can simulate the measurements of discrete-return and full-waveform instruments based on the geometry in the Context. Ray-tracing is used to simulate the emission of radiation from the instrument, and based on ray-object intersection tests with primitive geometry in the model domain, the simulated hit points can be determined. Currently, only a rectangular scan pattern is supported.

To simulate discrete-return instruments, each laser pulse is modeled by a single ray emanating from the scanner origin. Rays are launched according to the scan parameters currently specified in the LiDARcloud. After calling the appropriate synthetic scan generation function, the simulated scan data will be added to the LiDARcloud as if it was imported from real LiDAR data. In addition to the (x,y,z) location of the ray intersection, the model also produces estimates of return intensity, deviation, and can return an identifier for the intersected object.

For full-waveform data simulation, multiple rays are cast for a single laser beam pulse. The density of rays is Gaussian, with the peak at the center of the beam. The model will also record the target count, target index, and timestamp associated with each hit point.

Synthetic scanning is fully implemented in PyHelios with support for both discrete-return and full-waveform simulation:

```python
from pyhelios import Context, LiDARCloud
from pyhelios.types import vec3, vec2

with Context() as context:
    # Add geometry to scan
    context.addPatch(center=vec3(0, 0, 0.5), size=vec2(1, 1))

    with LiDARCloud() as lidar:
        # Define scan parameters
        scan_id = lidar.addScan(
            origin=vec3(0, 0, 2),
            Ntheta=100, theta_range=(0, 1.57),
            Nphi=100, phi_range=(0, 6.28),
            exit_diameter=0.0,       # Discrete-return
            beam_divergence=0.0
        )

        # Perform discrete-return synthetic scan
        lidar.syntheticScan(context)

        print(f"Generated {lidar.getHitCount()} hit points")
```

### XML Parameter File for Synthetic Data {#LiDARsynthxml}

To generate synthetic discrete-return LiDAR data, first add all desired model geometry to the Context. Then create a LiDARcloud instance and load an XML file containing the scan parameters. As in the case of importing a real point cloud dataset, the XML file must specify the scan origin and the scan resolution at a minimum. However, for synthetic data generation, you will not specify a filename to read containing point cloud data, as this data will be generated by the simulation. You can optionally specify the ASCII_format tag, which will determine which additional data fields should be recorded for each hit point.

If no ASCII_format tag is provided in the XML file, the default is to record the (x,y,z) position of the hit point.

Note that you can add multiple `<scan></scan>` blocks in a single XML file to perform multiple scans.

### Synthetic Discrete-Return Data {#LiDARsynthdiscrete}

Example XML file for discrete-return synthetic scanning:

```xml
<helios>
  <scan>
    <ASCII_format>x y z r255 g255 b255</ASCII_format>
    <origin>0 0 1.0</origin>
    <size>2500 4500</size>
    <thetaMin>30</thetaMin>
    <thetaMax>130</thetaMax>
    <phiMin>0</phiMin>
    <phiMax>360</phiMax>
  </scan>
</helios>
```

Example Python code for discrete-return synthetic scanning:

```python
from pyhelios import Context, LiDARCloud
from pyhelios.types import vec3, vec2

with Context() as context:
    # Add model geometry
    context.addPatch(center=vec3(0, 0, 0.5), size=vec2(1, 1))

    with LiDARCloud() as lidar:
        # Load scan parameters from XML
        lidar.loadXML("/path/to/file.xml")

        # Generate synthetic data
        lidar.syntheticScan(context)

        # Export results
        lidar.exportPointCloud("/path/to/output.xyz")
```

### Synthetic Waveform Data {#LiDARsynthwaveform}

Generation of synthetic full-waveform data is similar to discrete-return, except that additional information is needed to define the scan and simulation. In the XML file, the user must specify the diameter of the laser beam at the scan origin using the `<exitDiameter></exitDiameter>` tags, as well as the angle of beam divergence in radians using the `<beamDivergence></beamDivergence>` tags. If the exit diameter value is not specified, the default value of 0 is used, which means that the model will revert to discrete-return data generation. If the beam divergence value is not specified, a default beam divergence of 0 will be assumed, which effectively just means that the beam will remain perfectly cylindrical with diameter of exitDiameter.

Example XML file for full-waveform synthetic data:

```xml
<helios>
  <scan>
    <ASCII_format>x y z r255 g255 b255 target_count target_index timestamp</ASCII_format>
    <origin>0 0 1.0</origin>
    <size>2500 4500</size>
    <thetaMin>30</thetaMin>
    <thetaMax>130</thetaMax>
    <phiMin>0</phiMin>
    <phiMax>360</phiMax>
    <exitDiameter>0.005</exitDiameter>
    <beamDivergence>0.003</beamDivergence>
  </scan>
</helios>
```

Running the synthetic data generation function requires the specification of parameters associated with the simulation:

1. **Number of rays per pulse**: Sets the maximum possible number of hits per pulse. Specifying 1 ray/pulse effectively creates a discrete-return simulation. Ideally, you want a large number of rays/pulse because it allows for more hits/pulse if needed and results in more accurate simulations. The drawback is that simulations take longer to run. A value on the order of 100 is usually reasonable.

2. **Distance threshold**: For each simulated laser pulse, the rays/pulse are launched from the scan origin. When some or all of those rays intersect the same surface, they will record a distance from the scanner to the hit point that is slightly different for each ray. Similar distances, which are presumed to lie on the same surface, are aggregated into a single hit point if they are within this distance threshold of each other. Specifying too small of a distance threshold may result in many duplicate hit points on the same surface. Specifying too large of a threshold may result in hit points that lie in between two disconnected surfaces. A threshold value that is smaller than the leaf or branch width is usually reasonable.

Example Python code for full-waveform synthetic scanning:

```python
from pyhelios import Context, LiDARCloud
from pyhelios.types import vec3, vec2

with Context() as context:
    # Add model geometry
    context.addPatch(center=vec3(0, 0, 0.5), size=vec2(1, 1))

    with LiDARCloud() as lidar:
        # Load scan parameters (with exitDiameter and beamDivergence)
        lidar.loadXML("/path/to/file.xml")

        # Generate synthetic full-waveform data
        rays_per_pulse = 100
        pulse_distance_threshold = 0.02

        lidar.syntheticScan(
            context,
            rays_per_pulse=rays_per_pulse,
            pulse_distance_threshold=pulse_distance_threshold
        )

        # Export results
        lidar.exportPointCloud("/path/to/output.xyz")
```

**Advanced Options:**

```python
# Full control over synthetic scanning
lidar.syntheticScan(
    context,
    rays_per_pulse=100,
    pulse_distance_threshold=0.02,
    scan_grid_only=True,      # Only scan within grid cells
    record_misses=True,       # Record sky/miss points
    append=False              # Clear existing hits
)
```

## Visualizing Results {#LiDARvis}

Results can be visualized using the Visualizer plugin for Helios. There are two possible means for doing so. First, is to add the relevant geometry to the Context, then visualize primitives in the Context using the Visualizer. This works for the triangulation and plant reconstructions, but cannot be used to visualize just the point cloud since there is no "point" primitive in the Context.

The second option is to add any geometry directly to the Visualizer. There are several functions built into the LiDAR plugin that can do this automatically:

<table>
<tr><th>Function</th><th>Description</th></tr>
<tr><td>addHitsToVisualizer</td><td>Add all hits in the point cloud to the visualizer.</td></tr>
<tr><td>addGridToVisualizer</td><td>Add all grid cells to the visualizer, which are displayed as translucent voxels.</td></tr>
<tr><td>addTrianglesToVisualizer</td><td>Add all triangles to the visualizer, which are colored by the r-g-b color value.</td></tr>
</table>

**Note:** The Visualizer now includes automatic culling optimization for large point clouds (tens of millions of points), making it suitable for visualizing even very large LiDAR datasets with interactive performance.

**Note:** Visualizer integration methods are not yet wrapped in the current PyHelios implementation. For visualization, export point clouds and use external tools like Cloud Compare, or use the C++ API.

## Writing Results to File {#LiDARoutput}

Results of data processing can be easily written to file for external analysis. The following table lists available export functions. Data is written to an ASCII text file, where each line in the file corresponds to a different data point (e.g., hit point, triangle, etc.).

<table>
<tr><th>Function</th><th>Description</th><th>PyHelios Status</th></tr>
<tr><td>exportPointCloud(filename)</td><td>Write the entire point cloud to ASCII file.</td><td>✅ Available</td></tr>
<tr><td>exportTriangleNormals(filename)</td><td>Write the unit normal vectors [nx ny nz] of all triangles formed from triangulation.</td><td>✅ Available</td></tr>
<tr><td>exportTriangleAreas(filename)</td><td>Write the areas of all triangles formed from triangulation.</td><td>✅ Available</td></tr>
<tr><td>exportLeafAreas(filename)</td><td>Write the leaf area contained within each voxel.</td><td>✅ Available</td></tr>
<tr><td>exportLeafAreaDensities(filename)</td><td>Write the leaf area density of each voxel.</td><td>✅ Available</td></tr>
</table>

Example of writing results to file:

```python
from pyhelios import Context, LiDARCloud
from pyhelios.types import vec3

with Context() as context:
    with LiDARCloud() as pointcloud:
        pointcloud.loadXML("/path/to/file.xml")

        pointcloud.triangulateHitPoints(Lmax=0.05, max_aspect_ratio=5)

        # Calculate hit grid cell assignments
        pointcloud.calculateHitGridCell()

        # Calculate leaf area
        pointcloud.calculateLeafArea(context)

        # Export all available data
        pointcloud.exportPointCloud("../output/pointcloud.xyz")
        pointcloud.exportTriangleNormals("../output/triangle_normals.txt")
        pointcloud.exportTriangleAreas("../output/triangle_areas.txt")
        pointcloud.exportLeafAreas("../output/leaf_areas.txt")
        pointcloud.exportLeafAreaDensities("../output/leaf_area_densities.txt")
```

## Currently Implemented Methods

The following LiDARCloud methods are currently available in PyHelios:

### Core Operations
- `addScan()` - Add a LiDAR scan with metadata
- `getScanCount()` - Get number of scans
- `getScanOrigin()` - Get scanner position for a scan
- `getScanSizeTheta()`, `getScanSizePhi()` - Get scan resolution

### Hit Point Management
- `addHitPoint()` - Add hit point with position, direction, and optional color
- `getHitCount()` - Get total number of hit points
- `getHitXYZ()` - Get hit point coordinates
- `getHitRaydir()` - Get ray direction for a hit
- `getHitColor()` - Get hit point color
- `deleteHitPoint()` - Remove a hit point

### Transformations
- `coordinateShift()` - Translate all hit points
- `coordinateRotation()` - Rotate all hit points

### Triangulation
- `triangulateHitPoints()` - Generate Delaunay triangulation
- `getTriangleCount()` - Get number of triangles

### Filtering
- `distanceFilter()` - Filter by maximum distance
- `reflectanceFilter()` - Filter by minimum reflectance
- `firstHitFilter()` - Keep only first returns
- `lastHitFilter()` - Keep only last returns

### Synthetic Scanning (Ray Tracing Simulation)
- `syntheticScan(context)` - Discrete-return synthetic scan (single ray per pulse)
- `syntheticScan(context, append)` - With append control
- `syntheticScan(context, rays_per_pulse, pulse_distance_threshold)` - Full-waveform scan (multiple rays)
- `syntheticScan(context, rays_per_pulse, pulse_distance_threshold, scan_grid_only, record_misses, append)` - Full control

### Grid Cell Management
- `addGrid()` - Add rectangular grid of voxel cells with subdivisions
- `addGridCell()` - Add a single grid cell
- `getGridCellCount()` - Get total number of grid cells
- `getCellCenter()` - Get center position of a grid cell
- `getCellSize()` - Get dimensions of a grid cell
- `getCellLeafArea()` - Get leaf area for a grid cell (m²)
- `getCellLeafAreaDensity()` - Get leaf area density for a grid cell (m²/m³)
- `calculateHitGridCell()` - Assign hit points to grid cells

### Leaf Area Calculations
- `calculateLeafArea()` - Calculate leaf area for each grid cell
- `calculateLeafArea(context, min_voxel_hits)` - Calculate with minimum hits threshold

### File I/O
- `exportPointCloud()` - Export point cloud to ASCII file
- `exportTriangleNormals()` - Export triangle normal vectors
- `exportTriangleAreas()` - Export triangle areas
- `exportLeafAreas()` - Export leaf areas per grid cell
- `exportLeafAreaDensities()` - Export leaf area densities per grid cell
- `loadXML()` - Load scan metadata from XML

### Utility
- `enableMessages()`, `disableMessages()` - Control console output

## Future Implementation Priorities

The following C++ methods are documented but not yet wrapped in PyHelios. These will be prioritized for future releases based on user demand:

### High Priority (Commonly Used)
- Gapfilling: `gapfillMisses()` for sky/miss point interpolation
- Advanced I/O: `exportPointCloudPTX()`, `loadASCIIFile()` for PTX format and direct ASCII loading
- Advanced scan queries: `getScanRangeTheta()`, `getScanRangePhi()`, `getScanBeamExitDiameter()`, `getScanBeamDivergence()`

### Medium Priority
- Reconstruction: `leafReconstructionAlphaMask()`, `trunkReconstruction()`, `addLeafReconstructionToContext()`
- Triangle distribution exports: `exportTriangleInclinationDistribution()`, `exportTriangleAzimuthDistribution()`
- G(theta) export: `exportGtheta()` for leaf angle distribution function

### Lower Priority (Advanced Features)
- Visualizer integration: `addHitsToVisualizer()`, `addGridToVisualizer()`, `addTrianglesToVisualizer()`
- TreeQSM loading: `loadTreeQSM()` for quantitative structure models
- GPU control: `enableCDGPUAcceleration()`, `disableCDGPUAcceleration()`
- Grid bounding box: `getGridBoundingBox()`
- Advanced grid properties: `setCellGtheta()`, `getCellGtheta()`

## Complete Example

```python
from pyhelios import LiDARCloud
from pyhelios.types import vec3, RGBcolor

# Create LiDAR cloud
with LiDARCloud() as pointcloud:
    # Add a terrestrial scan
    scan_id = pointcloud.addScan(
        origin=vec3(0, 0, 2),
        Ntheta=200, theta_range=(0.52, 2.27),  # 30° to 130° in radians
        Nphi=400, phi_range=(0, 6.28),         # 0° to 360° in radians
        exit_diameter=0.005,
        beam_divergence=0.003
    )

    # Add hit points (typically from file or synthetic scan)
    for i in range(100):
        x = i * 0.1
        y = 0
        z = 0.5
        position = vec3(x, y, z)
        direction = vec3(1, 0, 0)
        color = RGBcolor(0.3, 0.7, 0.2)

        pointcloud.addHitPoint(scan_id, position, direction, color=color)

    print(f"Point cloud has {pointcloud.getHitCount()} points")

    # Apply filters
    pointcloud.distanceFilter(maxdistance=15.0)
    pointcloud.firstHitFilter()  # Keep only first returns

    print(f"After filtering: {pointcloud.getHitCount()} points")

    # Generate triangle mesh
    pointcloud.triangulateHitPoints(Lmax=0.05, max_aspect_ratio=5)
    print(f"Generated {pointcloud.getTriangleCount()} triangles")

    # Export results
    pointcloud.exportPointCloud("processed_scan.xyz")
```

## References

- Bailey, B.N. and Mahaffee, W.F., 2017. Rapid measurement of the three-dimensional distribution of leaf area using terrestrial laser scanning. *Remote Sensing of Environment* 188: 154-167. [doi:10.1016/j.rse.2017.03.011](http://dx.doi.org/doi:10.1016/j.rse.2017.03.011)

- Bailey, B.N. and Mahaffee, W.F., 2017. Rapid, high-resolution measurement of leaf area and leaf orientation using terrestrial LiDAR scanning data. *Measurement Science and Technology* 28(6): 064006. [doi:10.1088/1361-6501/aa5cfd](http://dx.doi.org/doi:10.1088/1361-6501/aa5cfd)

- Bailey, B.N. and Ochoa, M.H., 2018. Semi-direct tree reconstruction using terrestrial LiDAR point cloud data. *Remote Sensing of Environment* 208: 133-144. [doi:10.1016/j.rse.2018.02.013](https://doi.org/10.1016/j.rse.2018.02.013)

## See Also

- [Context](@ref ContextDoc) - 3D primitive management
- [CollisionDetection](@ref CollisionDetectionDoc) - Ray tracing for synthetic scans
- [Visualizer](@ref VisualizerDoc) - 3D visualization of point clouds
- [Complete Helios C++ LiDAR Documentation](https://baileylab.ucdavis.edu/software/helios/documentation/html/_li_d_a_r_doc.html)
