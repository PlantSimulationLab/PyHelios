\page IO File Input/Output

# File Input/Output

\note File paths can be given as absolute paths or relative paths. Helios automatically resolves asset file paths (models, textures, spectra, etc.) so executables can be run from any directory. The resolution system searches for assets relative to the build directory. You can set the HELIOS_BUILD environment variable to specify a custom build directory location if needed.

## XML File Structure {#XMLstructure}

File input and output is handled using .xml files.  See the Wikipedia page for xml for more information on xml files: [en.wikipedia.org/wiki/XML](https://en.wikipedia.org/wiki/XML).

Within Helios, xml files can be used to execute any Context commands that would be issued within a program, for example, adding geometry, adding timeseries, or adding primitive data.

All xml files start with a header indicating the version to be used, and the tag "<helios>...</helios>" should encapsulate the whole file:

```xml
<?xml version="1.0"?>
<helios>

</helios>
```

Comments are given in xml files by:
```xml
<!-- this is a comment -->
```

### Adding Primitives {#PrimXML}

Primitives are added by giving a tag with the primitive type, followed by elements that specify necessary inputs.  The table below gives examples of adding each primitive type in an .xml file.  Note that the parameters used to specify the primitives are the same as when adding them to the Context via 'add[*]' commands (e.g., addPatch()).

| Primitive Type | Code Sample |
|----------------|-------------|
| Patch | <div style="padding:0.5px;line-height:1.2;"><pre><code> &lt;patch&gt;<br>  &lt;center&gt;0 0 0&lt;/center&gt;<br>  &lt;size&gt;1 1&lt;/size&gt;<br>  &lt;rotation&gt;0 0&lt;/rotation&gt; &lt;!-- OPTIONAL --&gt;<br>  &lt;color&gt;1 0 0&lt;/color&gt; &lt;!-- OPTIONAL --&gt;<br>  &lt;texture&gt;"grass.jpg"&lt;/texture&gt; &lt;!-- OPTIONAL --&gt;<br>&lt;/patch&gt;</code></pre></div> |
| Triangle | <div style="padding:0.5px;line-height:1.2;"><pre><code> &lt;triangle&gt;<br>  &lt;vertex&gt;0 0 0&lt;/vertex&gt;<br>  &lt;vertex&gt;1 0 0&lt;/vertex&gt;<br>  &lt;vertex&gt;1 1 0&lt;/vertex&gt;<br>  &lt;color&gt;1 0 0&lt;/color&gt;<br>&lt;/triangle&gt;</code></pre></div> |
| Disk | <div style="padding:0.5px;line-height:1.2;"><pre><code> &lt;disk&gt;<br>  &lt;center&gt;0 0 0&lt;/center&gt;<br>  &lt;size&gt;1 1&lt;/size&gt;<br>  &lt;rotation&gt;0 0&lt;/rotation&gt;<br>  &lt;color&gt;1 0 0&lt;/color&gt;<br>  &lt;texture&gt;"grass.jpg"&lt;/texture&gt;<br>&lt;/disk&gt;</code></pre></div> |
| Voxel | <div style="padding:0.5px;line-height:1.2;"><pre><code> &lt;voxel&gt;<br>  &lt;center&gt;0 0 0&lt;/center&gt;<br>  &lt;size&gt;1 1 1&lt;/size&gt;<br>  &lt;color&gt;1 0 0&lt;/color&gt;<br>&lt;/voxel&gt;</code></pre></div> |

### Adding Timeseries Data {#TimeXML}

Data timeseries are specified by the tag 'timeseries' with the attribute giving the label for the timeseries (e.g., temperature).  The 'datapoint' tag is used to specify data points, with elements specifying the time, date, and value.  The sample below gives an example of creating a timeseries in an xml file.

```xml
<?xml version="1.0"?>
<helios>
 <timeseries label="temperature" >
  <datapoint>
    <date>2 1 2000</date> <!-- 2 Jan. 2000 -->
    <time>13 0 0</time> <!-- 13:00:00 -->
    <value>301.23</value>
  </datapoint>
  <datapoint>
    <date>2 1 2000</date> <!-- 2 Jan. 2000 -->
    <time>13 15 00</time> <!-- 13:15:00 -->
    <value>301.92</value>
  </datapoint>
  <datapoint>
    <date>2 1 2000</date> <!-- 2 Jan. 2000 -->
    <time>13 30 00</time> <!-- 13:30:00 -->
    <value>302.56</value>
  </datapoint>
  <datapoint>
    <date>2 1 2000</date> <!-- 2 Jan. 2000 -->
    <time>13 45 00</time> <!-- 13:45:00 -->
    <value>303.05</value>
  </datapoint>
 </timeseries>
</helios>
```

Note that the date can alternatively be specified as a Julian day of year (1-366) using the \<dateJulian\> tag:

```xml
  <dateJulian>2 2000</dateJulian> <!-- 2 Jan. 2000, Julian Day = 2 -->
```

## Adding Timeseries (Weather) Data from Tabular Text Files {#ASCIItimeseries}

If timeseries/weather data is available in a tabular ASCII text file, this can be read directly into the Context to create a timeseries using the [loadTabularTimeseriesData()](pyhelios.Context.Context.loadTabularTimeseriesData) method. The general format for these files is that each column should correspond to each variable (e.g., time, date, temperature, wind speed) and each row should be a different time point. There should be an equal number of columns on every line.

At a minimum, there should be a column specifying the date, which could either be a date string (e.g., 03/10/2023) or Julian day and the year, as well as columns specifying the hour and at least one corresponding data value. The date string can separate values by the '/' or '-' characters (03/10/2023 or 03-10-2023, respectively), and can have different ordering (e.g., YYYYMMDD) which is specified based on an argument to the [loadTabularTimeseriesData()](pyhelios.Context.Context.loadTabularTimeseriesData) method.

There are two ways of specifying the ordering and labels of columns. The first is to specify them in the file header (first line). The second is to specify them manually as an argument to the [loadTabularTimeseriesData()](pyhelios.Context.Context.loadTabularTimeseriesData) method. This can be useful if you want to customize the names of data values without modifying the actual text file.

There are certain column labels that are keywords used by Helios to specify required values such as the date. These are given in the table below. Any other label not contained in the table below will be treated as a variable, whose label in the timeseries will be the given column label.

| Column Label | Description | Required? |
|--------------|-------------|-----------|
| year | Year (YYYY) | year+DOY -OR- date |
| DOY or Jul | Day of year starting at Jan. 1 (DOY=1) | year+DOY -OR- date |
| date | Date string delimited by '/' or '-' character (default format YYYY-MM-DD) | year+DOY -OR- date |
| hour | Hour of the day. Can be specified either as 13 or 1300 (for 1PM example). | yes |
| minute | Minute of the hour. If 'hour' above is specified with minute included (e.g., 1315), the minute field will be automatically added. | no |
| second | Second of the minute. | no |

Arguments to the [loadTabularTimeseriesData()](pyhelios.Context.Context.loadTabularTimeseriesData) method:

1. A string specifying the file to be loaded, with path relative to the current working directory or as an absolute path.
2. A list of strings specifying labels for the columns in the file. If an empty list is specified (`[]`), the labels given in the first line of the file will be used. Otherwise, the length of the list must match the number of columns in the file.
3. The delimiter character separating values in each row (e.g., ',').
4. (optional) The format of the date string used to specify date values (e.g., 'YYYYMMDD', 'MMDDYYYY'; month and day should always be two values, and year should be four values). This is not used if dates are specified using the year and DOY. The default format is 'YYYYMMDD'.
5. (optional) Number of header lines in the file. By default, headerlines=0.

There is a special shortcut for reading [CIMIS weather station](https://cimis.water.ca.gov) files. To read these files, simply specify the second argument as a list containing the string "CIMIS" (e.g., `["CIMIS"]`), which will automatically set column labels as:
`["", "", "", "date", "hour", "DOY", "ETo", "", "precipitation", "", "net_radiation", "", "vapor_pressure", "", "air_temperature", "", "air_humidity", "", "dew_point", "", "wind_speed", "", "wind_direction", "", "soil_temperature", ""]`. You can specify any delimiter in this case - it will be overridden to be comma delimited.

A code example for generic weather data is given below.

```python
from pyhelios import Context
from pyhelios.types import Date, Time

context = Context()

context.loadTabularTimeseriesData("../input/weatherfile.csv", ["date", "hour", "temperature"], ",", "MMDDYYYY", 1)

date = Date(2020, 1, 2)
time = Time(13, 0, 0)
T = context.queryTimeseriesData("temperature", date, time)
```

The above example would read the comma-delimited file "../input/weatherfile.csv". Timeseries data would be added to the Context for values of "temperature", which could be queried based on this label.

## Reading XML Files {#XMLread}

XML files can be read by the Context via the function [loadXML()](pyhelios.Context.Context.loadXML).  This function parses the XML file and adds all specified structures (see above) to the Context. Below is an example of how to load an XML file into the Context.

```python
from pyhelios import Context

context = Context()

context.loadXML("file.xml")
```

## Reading Standard Polygon File Formats {#Poly}

### Reading PLY (Stanford Polygon) Files {#PLYread}

The Context can automatically import Stanford .ply files [en.wikipedia.org/wiki/PLY_(file_format)](https://en.wikipedia.org/wiki/PLY_(file_format)).  This is accomplished via the [loadPLY()](pyhelios.Context.Context.loadPLY) command, as illustrated below. There are several overloaded versions of this function, which allow for various modifications to the PLY model.

The `nx`, `ny` and `nz` vertex properties are read as per-vertex normals, and are given the same up-axis permutation as the vertex coordinates.

```python
from pyhelios import Context
from pyhelios.types import vec3, SphericalCoord, RGBcolor, RGBcolor
import math

context = Context()

# location where PLY model will be centered
origin = vec3(0, 0, 0)

# scaling factor to apply to model
scale = 1.0

# rotation to apply to model (optional argument to loadPLY)
rotation = SphericalCoord(0., math.pi)

# default color for model (optional argument to loadPLY)
color = RGBcolor(1, 0, 0)

context.loadPLY("file.ply", origin, scale, rotation, color)
```

There are other forms of the loadPLY function that allow for translation, rotation, and scaling of the entire PLY model.

Different applications may utilize different coordinate axes in .ply files. In computer graphics applications, it is common to define the y-axis as the up direction. Helios uses a z-up coordinate system. By default [loadPLY()](pyhelios.Context.Context.loadPLY) assumes that the coordinate system used when creating the .ply file is y-up. There is an optional argument [loadPLY()](pyhelios.Context.Context.loadPLY) that can allow you to easily define the up-axis.

The Blender software package ([www.blender.org](https://www.blender.org)) can easily modify and convert most polygon file formats to .ply format.

### Reading OBJ (Wavefront) Files {#OBJread}

Helios can read [Wavefront (.obj)](https://en.wikipedia.org/wiki/Wavefront_.obj_file) files and associated material (.mtl) files.  Not all features of .obj files are applicable to Helios, and thus some features are not supported.  Supported features are:

- Geometric vertex coordinates (x,y,z)
- Vertex texture coordinates (u,v)
- Vertex normals (vn)
- All four face vertex reference forms (`v`, `v/vt`, `v//vn`, `v/vt/vn`), including negative (relative) indices
- Texture map image files (.jpg, .png) associated with materials
- Object groups. When the 'o groupname' is added before a set of vertices, primitive data called 'object_label' is written for the resulting set of primitives.

Wavefront files are loaded via the [loadOBJ()](pyhelios.Context.Context.loadOBJ) function, which takes the name of an .obj file.  If the file defines materials and lists an associated material (.mtl) file, the code looks in one of two places for the file.  First, if an absolute or relative path is given for the .mtl file name, the file is simply loaded from that location.  If only a file name is given for the .mtl file, the directory where the original .obj file was found is searched for the .mtl file.

All aspects of material files are not supported. Helios simply searches for the "Kd" texture map, and uses that to color the primitives.

The [loadOBJ()](pyhelios.Context.Context.loadOBJ) function requires inputs that scale the model to achieve a certain size of the model, and apply a rotation to the model. There are multiple overloaded versions of this function (listed below) that allow specification of these aspects differently.

| Function | Description |
|----------|-------------|
| [loadOBJ(filename, origin, height, rotation, default_color, silent=False)](pyhelios.Context.Context.loadOBJ) | Load the model and translate it to the location 'origin', scale to have a height of 'height' (set height=0 to apply no scaling), and apply spherical rotation of 'rotation'. |
| [loadOBJ(filename, origin, height, rotation, default_color, upaxis, silent=False)](pyhelios.Context.Context.loadOBJ) | Same as above, except specify the 'up axis' of the model ('XUP', 'YUP', or 'ZUP'). Some 3D modeling software uses a different default axis corresponding to the up direction (e.g., computer graphics software commonly uses 'y' as the up direction). |
| [loadOBJ(filename, origin, scale, rotation, default_color, upaxis, silent=False)](pyhelios.Context.Context.loadOBJ) | Same as above, except a scaling factor is applied to the model in the x-, y-, and z-directions based on the value of 'scale' (if scale.x=scale.y=scale.z=0, no scaling is applied). |

The last optional argument to the [loadOBJ()](pyhelios.Context.Context.loadOBJ) function allows the user to disable any messages output from the function while loading by setting silent=True.

Example code is given below to load an OBJ model at the origin with no scaling (height=0) or rotation (rotation=`SphericalCoord(1, 0, 0)`) applied. Note that `upaxis` defaults to `'YUP'`; pass `upaxis='ZUP'` explicitly if your model already uses Helios' z-up convention.

```python
from pyhelios import Context
from pyhelios.types import vec3, RGBcolor, SphericalCoord

context = Context()

context.loadOBJ("relative/path/to/someobjfile.obj", origin=vec3(0, 0, 0), height=0,
                rotation=SphericalCoord(1, 0, 0), color=RGBcolor(1, 0, 0))
```

### Writing PLY (Stanford Polygon) Files {#PLYwrite}

The Context has analogous files for writing PLY files based on the geometry currently loaded in the Context. This is accomplished via the [writePLY()](pyhelios.Context.Context.writePLY) command, as illustrated below.

Geometry belonging to a `Polymesh` with retained connectivity (see \ref MeshTopology) is written against the mesh's shared vertices rather than three independent vertices per triangle, and `nx`, `ny` and `nz` vertex properties are emitted when every vertex in the file carries a normal. This is what allows a closed solid to reload as a closed solid whose volume can still be computed. Output for geometry that is not part of such a mesh is unchanged.

```python
from pyhelios import Context

context = Context()

context.addPatch()

context.writePLY("file.ply")
```

### Writing OBJ (Wavefront) Files {#OBJwrite}

Writing Wavefront OBJ files is similar to writing a PLY file, except that it will produce both a .obj file containing the geometry, and a .mtl file defining materials (colors, texture masks). For this reason, only the base file name with no extension is provided to the function.

As with PLY, geometry belonging to a `Polymesh` with retained connectivity is written against the mesh's shared vertices, emitting each vertex once and referencing it by index from every face that uses it. With `write_normals=True` one true per-vertex normal is written per shared vertex, rather than one flattened face normal per primitive, so a smooth mesh survives a load–write–load round trip instead of degrading to a faceted one.

```python
from pyhelios import Context

context = Context()

context.addPatch()

# This will produce two files: "file.obj" and "file.mtl"
context.writeOBJ("file")
```

## Mesh Topology {#MeshTopology}

Triangles read from an OBJ or PLY file are grouped into a `Polymesh` compound object that retains the connectivity of the source file: a deduplicated vertex list, a face table, and optional per-vertex normals and texture coordinates. The vector of UUIDs returned by [loadOBJ()](pyhelios.Context.Context.loadOBJ) and [loadPLY()](pyhelios.Context.Context.loadPLY) is unchanged; the object ID is obtained with [getPrimitiveParentObjectID()](pyhelios.Context.Context.getPrimitiveParentObjectID).

Retained connectivity is what makes a loaded mesh a surface rather than a triangle soup. It is used to compute an enclosed volume, to render the mesh smoothly, and to write it back out against shared vertices so a smooth mesh survives a load–write–load round trip.

| Function | Description |
|----------|-------------|
| [getPolymeshObjectVertices(objID)](pyhelios.Context.Context.getPolymeshObjectVertices) | Shared vertex positions |
| [getPolymeshObjectFaces(objID)](pyhelios.Context.Context.getPolymeshObjectFaces) | Vertex index triples defining each face |
| [getPolymeshObjectVertexNormals(objID)](pyhelios.Context.Context.getPolymeshObjectVertexNormals) | Per-vertex normals, or an empty list if the mesh has none |
| [getPolymeshObjectVertexUV(objID)](pyhelios.Context.Context.getPolymeshObjectVertexUV) | Per-vertex texture coordinates |
| [getPolymeshObjectVertexCount(objID)](pyhelios.Context.Context.getPolymeshObjectVertexCount) | Number of shared vertices |
| [getPolymeshObjectFaceCount(objID)](pyhelios.Context.Context.getPolymeshObjectFaceCount) | Number of faces |
| [doesPolymeshObjectHaveVertexNormals(objID)](pyhelios.Context.Context.doesPolymeshObjectHaveVertexNormals) | Whether the mesh carries vertex normals |
| [getPolymeshObjectVertexNormalSource(objID)](pyhelios.Context.Context.getPolymeshObjectVertexNormalSource) | Where those normals came from |
| [getPolymeshObjectFaceIndexForPrimitive(objID, uuid)](pyhelios.Context.Context.getPolymeshObjectFaceIndexForPrimitive) | Face index of a member primitive |
| [getPolymeshObjectPrimitiveUUIDForFace(objID, face_index)](pyhelios.Context.Context.getPolymeshObjectPrimitiveUUIDForFace) | UUID of the primitive making up a face |
| [setPolymeshObjectTopology(objID, vertices, faces, face_UUIDs, ...)](pyhelios.Context.Context.setPolymeshObjectTopology) | Attach a face set to a mesh built programmatically |

A mesh assembled with [addPolymeshObject()](pyhelios.Context.Context.addPolymeshObject) has no topology until one is attached: its face count is zero, it cannot report a volume, and it is written out as independent per-triangle vertices.

### Vertex Normals {#VertexNormals}

Helios never synthesizes vertex normals implicitly. A mesh has them only if the source file supplied them or [computePolymeshObjectVertexNormals()](pyhelios.Context.Context.computePolymeshObjectVertexNormals) was called explicitly. That function averages face normals weighted by area, and splits vertices across edges whose dihedral angle exceeds `crease_angle_degrees` so that hard edges stay hard.

[getPolymeshObjectVertexNormalSource()](pyhelios.Context.Context.getPolymeshObjectVertexNormalSource) reports the provenance as a `VertexNormalSource`: `NONE`, `AUTHORED` (read from the file) or `COMPUTED`.

```python
from pyhelios import Context
from pyhelios.wrappers.DataTypes import VertexNormalSource

context = Context()
uuids = context.loadOBJ("mesh.obj")
objID = context.getPrimitiveParentObjectID(uuids[0])

if context.getPolymeshObjectVertexNormalSource(objID) == VertexNormalSource.NONE:
    context.computePolymeshObjectVertexNormals(objID, crease_angle_degrees=30)
```

### Topological Queries {#MeshTopoQueries}

| Function | Description |
|----------|-------------|
| [isPolymeshObjectClosed(objID)](pyhelios.Context.Context.isPolymeshObjectClosed) | Whether the mesh is watertight |
| [getPolymeshObjectBoundaryEdges(objID)](pyhelios.Context.Context.getPolymeshObjectBoundaryEdges) | Vertex index pairs for edges referenced by only one face |
| [getPolymeshObjectConnectedComponents(objID)](pyhelios.Context.Context.getPolymeshObjectConnectedComponents) | Face indices grouped into disjoint pieces |
| [getPolymeshObjectSurfaceArea(objID)](pyhelios.Context.Context.getPolymeshObjectSurfaceArea) | Total area of every face |
| [getPolymeshObjectVolume(objID)](pyhelios.Context.Context.getPolymeshObjectVolume) | Enclosed volume; requires a closed mesh |

Only a closed mesh has a well-defined enclosed volume. For a mesh that carries a face table, `getPolymeshObjectVolume()` verifies closure first and raises an error naming the number of boundary edges, rather than returning a meaningless number for an open surface. Use `getPolymeshObjectSurfaceArea()` for an open mesh.

```python
if context.isPolymeshObjectClosed(objID):
    volume = context.getPolymeshObjectVolume(objID)
else:
    print(f"open surface: {len(context.getPolymeshObjectBoundaryEdges(objID))} boundary edges")
```

### Analytic Vertex Normals {#AnalyticNormals}

`Sphere`, `Tube` and `Cone` objects can report the true surface normal of the curved shape they approximate, rather than the flat normal of the triangle that approximates it. [doesObjectHaveAnalyticVertexNormals()](pyhelios.Context.Context.doesObjectHaveAnalyticVertexNormals) reports which object types can, and [getObjectPrimitiveVertexNormals()](pyhelios.Context.Context.getObjectPrimitiveVertexNormals) returns the normals at each vertex of a member primitive. Pass a list of UUIDs instead of one to evaluate many primitives at once, which prepares the per-object quantities only once.

Normals are evaluated from each shape's own definition rather than stored, so they account for taper and remain correct after the object is transformed or its nodes and radii are changed. Object types built from genuinely flat faces, such as a tile or box, report that they have no analytic normals and return an empty list.

## Exporting Project to XML File Format {#Export}

All geometry and global/primitive data loaded into the Context can be written to an XML file using the [writeXML()](pyhelios.Context.Context.writeXML) function, which can be later read back in using the [loadXML()](pyhelios.Context.Context.loadXML). This functionality can be used to save progress during a simulation run, or to ensure that consistent geometry is always used across simulation runs, among other things.

An XML file can be written as follows:

```python
from pyhelios import Context

context = Context()

UUID = context.addPatch()

context.setPrimitiveDataFloat(UUID, "somedata", 10.2)

context.writeXML("file.xml")
```

and later read back into a new simulation:

```python
from pyhelios import Context

context = Context()

# The context will now contain a default patch, with primitive data "somedata" equal to 10.2
context.loadXML("file.xml")
```

To export only a subset of primitives, pass a list of UUIDs to `writeXML()`:

```python
context.writeXML("subset.xml", uuids=[uuid1, uuid2], quiet=True)
```

To export a list of compound objects (and the primitives they contain), use `writeXML_byobject()`:

```python
context.writeXML_byobject("objects.xml", [objID1, objID2], quiet=True)
```

The `quiet` flag (defaults to `False`) suppresses informational console output during export.
