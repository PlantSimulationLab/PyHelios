\page API User/API Guide

# User/API Guide

This section provides detailed API documentation for PyHelios core functionality.

## Vector Types {#VecTypes}

There are several vector types commonly used by the Context and other plugins. These are Python classes with at least two member variables. Helios vector types are available by importing:

```python
from pyhelios.types import *
```

Note that vector types are also available when importing Context.

Available vector types are detailed below.

| Type | Description | Data Fields | Member Functions | Math Operators | Creation |
|------|-------------|-------------|------------------|----------------|----------|
| \ref pyhelios.wrappers.DataTypes.vec2 "vec2" | 2D vector of floats | `x`, `y` | \ref pyhelios.wrappers.DataTypes.vec2::normalize "normalize()", \ref pyhelios.wrappers.DataTypes.vec2::magnitude "magnitude()" | * (dot product), * (mult. by scalar), /, +, -, +=, ==, != | `vec2(x, y)` |
| \ref pyhelios.wrappers.DataTypes.vec3 "vec3" | 3D vector of floats | `x`, `y`, `z` | \ref pyhelios.wrappers.DataTypes.vec3::normalize "normalize()", \ref pyhelios.wrappers.DataTypes.vec3::magnitude "magnitude()" | * (dot product), * (mult. by scalar), /, +, -, +=, ==, != | `vec3(x, y, z)` |
| \ref pyhelios.wrappers.DataTypes.vec4 "vec4" | 4D vector of floats | `x`, `y`, `z`, `w` | none | * (dot product), * (mult. by scalar), /, +, -, +=, ==, != | `vec4(x, y, z, w)` |
| \ref pyhelios.wrappers.DataTypes.int2 "int2" | 2D vector of integers | `x`, `y` | none | +, -, +=, ==, != | `int2(x, y)` |
| \ref pyhelios.wrappers.DataTypes.int3 "int3" | 3D vector of integers | `x`, `y`, `z` | none | +, -, +=, ==, != | `int3(x, y, z)` |
| \ref pyhelios.wrappers.DataTypes.int4 "int4" | 4D vector of integers | `x`, `y`, `z`, `w` | none | +, -, +=, ==, != | `int4(x, y, z, w)` |
| \ref pyhelios.wrappers.DataTypes.SphericalCoord "SphericalCoord" | Spherical coordinate | `radius`, `elevation`, `zenith`, `azimuth` | none | ==, != | `SphericalCoord(radius, elevation, azimuth)` |
| \ref pyhelios.wrappers.DataTypes.RGBcolor "RGBcolor" | red-green-blue color code (values normalized to 1) | `r`, `g`, `b` | \ref pyhelios.wrappers.DataTypes.RGBcolor::scale "scale()" | ==, != | `RGBcolor(r, g, b)` |
| \ref pyhelios.wrappers.DataTypes.RGBAcolor "RGBAcolor" | red-green-blue-alpha color code (values normalized to 1) | `r`, `g`, `b`, `a` | \ref pyhelios.wrappers.DataTypes.RGBAcolor::scale "scale()" | ==, != | `RGBAcolor(r, g, b, a)` |
| \ref pyhelios.wrappers.DataTypes.Time "Time" | Time of day | `hour`, `minute`, `second` | none | ==, != | `Time(hour, minute, second)` |
| \ref pyhelios.wrappers.DataTypes.Date "Date" | Calendar date (YYYY,MM,DD) | `year`, `month`, `day` | \ref pyhelios.wrappers.DataTypes.Date::JulianDay "JulianDay()", \ref pyhelios.wrappers.DataTypes.Date::incrementDay "incrementDay()", \ref pyhelios.wrappers.DataTypes.Date::isLeapYear "isLeapYear()" | ==, != | `Date(year, month, day)` |

Vector types can be initialized directly. For example, `i2 = int2(1, 2)` creates an int2 with members `i2.x = 1` and `i2.y = 2`.

### R-G-B(-A) color vectors

There are several predefined RGB color vectors (see RGBcolor) that can be used, which are tabulated below:

| Color | RGB Values | Color Swatch |
|-------|------------|--------------|
| RGB::black | (0,0,0) | <div style="width:50px;height:30px;background-color:rgb(0,0,0);border:1px solid #ccc;"></div> |
| RGB::white | (1,1,1) | <div style="width:50px;height:30px;background-color:rgb(255,255,255);border:1px solid #ccc;"></div> |
| RGB::red | (1,0,0) | <div style="width:50px;height:30px;background-color:rgb(255,0,0);"></div> |
| RGB::blue | (0,0,1) | <div style="width:50px;height:30px;background-color:rgb(0,0,255);"></div> |
| RGB::green | (0,0.6,0) | <div style="width:50px;height:30px;background-color:rgb(0,153,0);"></div> |
| RGB::cyan | (0,1,1) | <div style="width:50px;height:30px;background-color:rgb(0,255,255);"></div> |
| RGB::magenta | (1,0,1) | <div style="width:50px;height:30px;background-color:rgb(255,0,255);"></div> |
| RGB::yellow | (1,1,0) | <div style="width:50px;height:30px;background-color:rgb(255,255,0);"></div> |
| RGB::orange | (1,0.5,0) | <div style="width:50px;height:30px;background-color:rgb(255,127,0);"></div> |
| RGB::violet | (0.5,0,0.5) | <div style="width:50px;height:30px;background-color:rgb(127,0,127);"></div> |
| RGB::lime | (0,1,0) | <div style="width:50px;height:30px;background-color:rgb(0,255,0);"></div> |
| RGB::silver | (0.75,0.75,0.75) | <div style="width:50px;height:30px;background-color:rgb(191,191,191);"></div> |
| RGB::gray | (0.5,0.5,0.5) | <div style="width:50px;height:30px;background-color:rgb(127,127,127);"></div> |
| RGB::navy | (0,0,0.5) | <div style="width:50px;height:30px;background-color:rgb(0,0,127);"></div> |
| RGB::brown | (0.55,0.27,0.075) | <div style="width:50px;height:30px;background-color:rgb(140,69,19);"></div> |
| RGB::khaki | (0.94,0.92,0.55) | <div style="width:50px;height:30px;background-color:rgb(240,235,140);"></div> |
| RGB::greenyellow | (0.678,1,0.184) | <div style="width:50px;height:30px;background-color:rgb(173,255,47);"></div> |
| RGB::forestgreen | (0.133,0.545,0.133) | <div style="width:50px;height:30px;background-color:rgb(34,139,34);"></div> |
| RGB::yellowgreen | (0.6,0.8,0.2) | <div style="width:50px;height:30px;background-color:rgb(153,204,51);"></div> |
| RGB::goldenrod | (0.855,0.647,0.126) | <div style="width:50px;height:30px;background-color:rgb(218,165,32);"></div> |

Note that the above colors can be directly used with RGBAcolor to specify an alpha (transparency) value:

```python
from pyhelios.types import RGBAcolor, RGBcolorcolor

# Create red color first, then use its components
red = RGBcolor(1, 0, 0)
red_trans = RGBAcolor(red.r, red.g, red.b, 0.5)

# Or directly:
red_trans = RGBAcolor(1.0, 0.0, 0.0, 0.5)
```

## Context {#ContextSect}

The Context is a Python class that manages data and functions associated with the Helios framework. The functions of the Context are:

1. Add and manage geometric objects
2. Manage data associated with geometric objects and models in general
3. Manage inputs and outputs

In simplest terms, the Context stores information associated with geometric objects (primitives) and their corresponding data.

In order to use the Context, it must be imported:

```python
from pyhelios import Context
```

The context is typically created within the main function or script:

```python
from pyhelios import Context

# Basic instantiation
context = Context()

# Recommended: Use context manager for automatic cleanup
with Context() as context:
    # Add geometry, run simulations, etc.
    pass
```

The Context is usually passed to plugins, which gives them access to geometry and data.

### Geographic Location {#Location}

The Context stores a geographic location used by plugins such as SolarPosition and RadiationModel for sun-position calculations. Location is represented by the immutable `Location` dataclass with three fields: `latitude` in degrees (+N / -S), `longitude` in degrees (+W / -E per Helios convention), and `utc_offset` in hours (+ moving West).

```python
from pyhelios import Context
from pyhelios.types import Location

context = Context()

# Set location explicitly
context.setLocation(38.55, 121.76, 8.0)             # latitude, longitude, UTC offset
context.setLocation(Location(38.55, 121.76, 8.0))   # equivalent

# Read it back
loc = context.getLocation()
print(loc.latitude, loc.longitude, loc.utc_offset)
```

Once the Context location is set, downstream plugins can read it instead of taking explicit lat/lon arguments.

## Coordinate System {#Coord}

Helios uses a right-handed Cartesian coordinate system. (x,y,z) coordinates are typically specified using the 'vec3' data structure (see Vector Types).

Rotations are typically specified using spherical angles (see Vector Types). A rotation of the elevation angle θ rotates the object about its y-axis. A rotation of the azimuthal angle φ rotates the object clockwise about its z-axis.

When compass directions are used, +y corresponds to North, and +x corresponds East. The azimuthal angle φ is measured clockwise from North.

![Coordinate System](images/core/CoordinateSystem.jpg)

![Compass Coordinates](images/core/CompassCoord.jpeg)

## Geometry {#Geom}

The Helios framework is centered around geometric objects called 'primitives'. Primitive elements build up the geometry of the domain, and typically store the data that couples models. For example, each primitive may have an associated surface temperature value that is updated or used by several different models.

### Primitive Types {#PrimitiveTypes}

The available geometric primitive types are detailed below. Each primitive type has an enumeration that can be used in the code to reference each primitive type.

| Primitive | Description | Enumeration |
|-----------|-------------|-------------|
| Patch | Rectangular polygon with coplanar vertices. A patch is specified by the (x,y,z) coordinate of its center and by the lengths of its sides in the x- and y-directions. The default orientation of a patch is horizontal (i.e., it's normal is in the +z direction). | PRIMITIVE_TYPE_PATCH |
| Triangle | Triangular polygon specified by its three vertices. | PRIMITIVE_TYPE_TRIANGLE |
| Voxel | Parallelpiped or rectangular prism. A voxel is specified by the (x,y,z) coordinate of its center and by the lengths of its sides in the x-, y-, and z-directions. The default orientation of a voxel is axis-aligned. | PRIMITIVE_TYPE_VOXEL |

### Adding Primitives {#AddingPrims}

Primitives are referenced by their 'universal unique identifier' or UUID. When a function is called to add a primitive to the context, a UUID is returned that can be used later to reference the primitive. Objects can be formed simply by storing a group of UUIDs corresponding to the primitives that make up the object.

Each primitive type has a different function that is used to add it to the Context, which are detailed in the table below.

| Primitive | Adder function |
|-----------|----------------|
| Patch | <ul><li>\ref pyhelios.Context.Context::addPatch "addPatch(center, size)"</li><li>\ref pyhelios.Context.Context::addPatch "addPatch(center, size, rotation)"</li><li>\ref pyhelios.Context.Context::addPatch "addPatch(center, size, rotation, color)"</li></ul> |
| Triangle | <ul><li>\ref pyhelios.Context.Context::addTriangle "addTriangle(vertex0, vertex1, vertex2)"</li><li>\ref pyhelios.Context.Context::addTriangle "addTriangle(vertex0, vertex1, vertex2, color)"</li><li>\ref pyhelios.Context.Context::addTriangleTextured "addTriangleTextured(vertex0, vertex1, vertex2, texture_file, uv0, uv1, uv2)"</li></ul> |
| Voxel | **Not implemented in PyHelios.** Use \ref pyhelios.Context.Context::addBox "addBox()" for box geometry. |

#### Adding Patches {#AddingPatch}

Patches are added by specifying the (x,y,z) coordinate of its center, the lengths of its sides in the x- and y-directions, and optionally its spherical rotation (see Coordinate System) and r-g-b color. The following is an example of using the `addPatch()` function to add a simple patch:

```python
from pyhelios import Context
from pyhelios.types import vec3, vec2

context = Context()

center = vec3(0, 0, 1)
size = vec2(1, 1)

UUID = context.addPatch(center, size)
```

This will add the Patch shown below, with the default orientation of horizontal. (Note that the addition of the checkerboard ground and the 'Visualizer' plugin is needed to replicate this image, which is not shown in the example code.)

![Patch geometric primitive](images/primitives/Patch.png)

The patch can also be rotated by adding the optional SphericalCoord argument:

```python
from pyhelios.types import SphericalCoord
import math

center = vec3(0, 0, 1)
size = vec2(1, 1)
rotation = SphericalCoord(1, 0.25*math.pi, 0.5*math.pi)
context.addPatch(center, size, rotation)
```

This will first rotate the patch by 0.25π rad about the x-axis such that its normal is pointing toward the +y direction, THEN it will apply a clockwise azimuthal rotation of 0.5π rad such that its normal is pointing in the +x direction (which will be its final orientation). Note that in order to have more control over rotations, it is recommended to use the \ref pyhelios.Context.Context::rotatePrimitive "rotatePrimitive()" function (see "Primitive Transformations" section below).

#### Adding Triangles {#AddingTriangle}

Triangles are added by specifying the (x,y,z) coordinates of the triangle's three vertices, and optionally its r-g-b color. The following is an example of using the `addTriangle()` function to add a simple triangle:

```python
from pyhelios import Context
from pyhelios.types import vec3, RGBcolorcolor

context = Context()

v0 = vec3(-0.5, -0.5, 1)
v1 = vec3(0.5, -0.5, 1)
v2 = vec3(0, 0.5, 1)

UUID = context.addTriangle(v0, v1, v2, RGBcolorcolor(1, 0, 0))
```

This will add the Triangle shown below. (Note that the addition of the checkerboard ground and the 'Visualizer' plugin is needed to replicate this image, which is not shown in the example code.)

![Triangle geometric primitive](images/primitives/Triangle.png)

An important note for triangles is that the normal direction of the triangle follows the right-hand rule: use your right hand to connect each of the vertices in the order specified, and your thumb will point in the normal direction. This is illustrated in the figure below.

![Right-hand rule to determine triangle normal direction based on the three vertices 0, 1, and 2.](images/primitives/triangle_right-hand-rule.jpeg)

#### Adding Voxels {#AddingVoxel}

**Note: The `addVoxel()` method is not yet implemented in PyHelios.** Voxel geometry can be created by importing 3D models (PLY, OBJ formats) or using box compound geometry.

For box-shaped geometry, use:

```python
from pyhelios import Context
from pyhelios.types import vec3, int3, RGBcolorcolor

context = Context()

center = vec3(0, 0, 1)
size = vec3(1, 1, 1)
subdivisions = int3(1, 1, 1)

# Use addBox for voxel-like geometry
UUIDs = context.addBox(center, size, subdivisions, RGBcolorcolor(1, 0, 0))
```

![Voxel geometric primitive](images/primitives/Voxel.png)

The voxel representation shown above is from the C++ Helios library. For PyHelios, use box geometry or import 3D models.

### Primitive Transformations {#PrimTransform}

After primitives have been added to the Context, their position, size, and orientation can be further modified through transformations.

The \ref pyhelios.Context.Context::scalePrimitive "scalePrimitive()" function takes a vec3 that denotes a scaling factor to apply in each Cartesian direction (x,y,z). The \ref pyhelios.Context.Context::translatePrimitive "translatePrimitive()" function moves the primitive based on values provided by a vec3 that specifies the distance to translate in the x-, y-, and z-directions.

The \ref pyhelios.Context.Context::rotatePrimitive "rotatePrimitive()" function rotates the primitive about an axis through an angle specified in radians. To rotate about one of the x-, y-, or z-axes, the function can be supplied a string of 'x', 'y', or 'z', respectively. The primitive can also be rotated about an arbitrary axis described by a unit vector argument. By default, the axis passes through the origin, but there is also an option to specify an arbitrary axis of rotation passing through an arbitrary origin point.

It is important to note that the order in which transformations are applied matters. Each transformation is applied based on the primitives current state. Rotating a primitive centered about the origin will cause the primitive to rotate about its own center. However, if a primitive is first translated then rotated, the primitive will be rotated about the origin (0,0,0), which does not necessarily coincide with the primitive's center if it has been translated.

The table below gives a list of primitive transformation functions, each of which take either a single UUID or a vector of UUIDs to apply the same transformation to multiple primitives.

| Transformation | Function |
|----------------|----------|
| Translation | <ul><li>\ref pyhelios.Context.Context::translatePrimitive "translatePrimitive(UUID, shift)"</li><li>\ref pyhelios.Context.Context::translatePrimitive "translatePrimitive(UUIDs, shift)"</li></ul> |
| Rotation | <ul><li>\ref pyhelios.Context.Context::rotatePrimitive "rotatePrimitive(UUID, rotation_radians, axis)"</li><li>\ref pyhelios.Context.Context::rotatePrimitive "rotatePrimitive(UUIDs, rotation_radians, axis)"</li><li>\ref pyhelios.Context.Context::rotatePrimitive "rotatePrimitive(UUID, rotation_radians, axis_vector)"</li><li>\ref pyhelios.Context.Context::rotatePrimitive "rotatePrimitive(UUIDs, rotation_radians, axis_vector)"</li><li>\ref pyhelios.Context.Context::rotatePrimitive "rotatePrimitive(UUID, rotation_radians, axis_vector, origin)"</li><li>\ref pyhelios.Context.Context::rotatePrimitive "rotatePrimitive(UUIDs, rotation_radians, axis_vector, origin)"</li></ul> |
| Scaling | <ul><li>\ref pyhelios.Context.Context::scalePrimitive "scalePrimitive(UUID, scale)"</li><li>\ref pyhelios.Context.Context::scalePrimitive "scalePrimitive(UUIDs, scale)"</li></ul> |

Below is a code example of applying a transformation using a pointer to the primitive:

```python
from pyhelios import Context
from pyhelios.types import vec3, vec2

# Initialize the Context
context = Context()

# Add 'Patch' primitive
center = vec3(0, 0, 1)
size = vec2(1, 1)
UUID = context.addPatch(center, size)

# Apply translation
translation = vec3(1, 0, 0)
context.translatePrimitive(UUID, translation)
```

#### Transformation Matrices (Advanced) {#TransformMatrix}

For applications that need direct access to a primitive's or compound object's full 4×4 affine transformation, PyHelios exposes the transformation matrix as a NumPy `(4, 4)` `float32` ndarray in **row-major** order. Element `T[i, j]` is the entry at row `i`, column `j`; the translation column lives at indices `T[0, 3]`, `T[1, 3]`, `T[2, 3]`.

```python
import numpy as np
from pyhelios import Context
from pyhelios.types import vec3, vec2, int2, SphericalCoord

context = Context()

UUID = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
objID = context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                              rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))

# Read the current transformation matrices (returns (4, 4) float32 ndarrays)
T_prim = context.getPrimitiveTransformationMatrix(UUID)
T_obj = context.getObjectTransformationMatrix(objID)

# Set a translation (5, -2, 7) directly via a 4x4 matrix
T_in = np.eye(4, dtype=np.float32)
T_in[0, 3], T_in[1, 3], T_in[2, 3] = 5.0, -2.0, 7.0
context.setObjectTransformationMatrix(objID, T_in)

# The same matrix can be applied to a list of objects in one call
context.setObjectTransformationMatrix([objID], T_in)
```

Setters also accept a list of 16 floats or a nested 4×4 list when NumPy is not convenient.

### Primitive Properties {#PrimProps}

All primitives have a common set of data that can be accessed by the same set of functions, such as the primitive surface area, the primitive vertices, etc.

The table below gives a list of all available primitive property setter and getter functions. In some case, there is no setter function when it is an intrinsic property of the primitive that is not changeable.

| Property | Setter Function | Getter Function |
|----------|-----------------|-----------------|
| Primitive Type | N/A | \ref pyhelios.Context.Context::getPrimitiveType "getPrimitiveType(UUID)" |
| Surface Area | N/A | \ref pyhelios.Context.Context::getPrimitiveArea "getPrimitiveArea(UUID)" |
| Normal Vector | N/A | \ref pyhelios.Context.Context::getPrimitiveNormal "getPrimitiveNormal(UUID)" |
| Vertex Coordinates (x,y,z) | N/A | \ref pyhelios.Context.Context::getPrimitiveVertices "getPrimitiveVertices(UUID)" |

Some primitives have special functions specific to that type of primitive. For example, one may want to query the length and width of a Patch. These primitive-specific functions are tabulated below. If the type of the primitive corresponding to the UUID passed to the function does not match the primitive type for that function, an error will be thrown (for example passing a Triangle UUID to the function getPatchSize()).

| Primitive Type/Property | Getter Function |
|-------------------------|-----------------|

```python
from pyhelios import Context
from pyhelios.types import vec3, vec2, RGBcolor

# Initialize the Context
context = Context()

# Add 'Patch' primitive
center = vec3(0, 0, 1)
size = vec2(1, 1)
UUID = context.addPatch(center, size, color=RGBcolor(1, 0, 0))

# Get Patch size
SIZE = context.getPatchSize(UUID)
```

### Texture Mapping {#Texture}

Images can be overlaid on patches and triangles through a process called [texture mapping](https://en.wikipedia.org/wiki/Texture_mapping). There are typically two reasons for doing this. One is simply for visualization purposes, as it easily allows for complex coloring of a surface by coloring a surface according to an image. The other is to create a more complex shape by removing a portion of the primitive surface according to the transparency channel of an image. Each of these cases are described in detail below.

#### Coloring Primitives by Texture Map {#TextureColor}

Patches: To color a Patch based on an image, simply pass the path to a PNG or JPEG image to the appropriate argument of the addPatch() command. Note that the path should either be absolute, or relative to the directory where the executable will be run (typically the `build' directory).

```python
from pyhelios.types import SphericalCoord

center = vec3(0, 0, 1)
size = vec2(2.5, 1)
rotation = SphericalCoord(1, 0, 0)
context.addPatch(center, size, rotation, "PSL_logo_white.png")
```

![Patch geometric primitive colored by texture map.](images/primitives/Patch_textured.png)

By default, the image is stretched to fill the entire surface of the patch. Alternatively, custom mapping coordinates can be supplied as illustrated below. Texture mapping coordinates are normalized to the dimensions of the image, such that the point (u,v)=(0,0) is in the lower left of the image, (u,v)=(1,1) is in the upper right of the image and so on.

Patches: For patches, the center and size of the box used to crop the texture are specified in (u,v) coordinates. In this example, the portion of the image inside of the red box would be mapped onto the patch, while the rest would be discarded.

![](images/primitives/GrapeLeaf_uvpatch.jpeg)

Triangles: For triangles, the (u,v) coordinates of the three triangle vertices are specified. For triangles, custom (u,v) coordinates must be specified when texture mapping.

![](images/primitives/GrapeLeaf_uvtriangle.jpeg)

#### Masking Primitives by Image Transparency Channel {#TextureMask}

If the image provided for texture mapping has a transparency channel, the portion of the primitive that is transparent will automatically be removed, and the rest of the non-transparent portion of the primitive will be colored according to the image. Note that only PNG images are supported, since JPEG images do not have transparency. An example is given below.

```python
from pyhelios import Context
from pyhelios.types import vec3, vec2, SphericalCoord

# Initialize the Context
context = Context()

# Add 'Patch' primitive with transparency mask
center = vec3(0, 0, 1)
size = vec2(1, 1)

UUID = context.addPatch(center, size, SphericalCoord(1, 0, 0), "GrapeLeaf.png")
```

![Rectangular patch masked by an image with a transparency channel.](images/primitives/AlphaMask_leaf.png)

**A very important performance note when using texture-masked primitives with transparency:** When a texture-masked primitive with transparency is added to the Context, the solid surface area of the primitive is calculated by determining which fraction of pixels are non-transparent. This is a computationally expensive process when the image is high resolution (e.g., millions of pixels).

If you are adding many identical primitives/objects with transparency, it is better to add it to the Context one time, then copy and translate it as many times as you need. An example of this is given in the code below.

```python
from pyhelios import Context
from pyhelios.types import vec3, vec2, SphericalCoord

# Initialize the Context
context = Context()

# Add 'Patch' primitive with transparency mask
# We will add a patch at the origin and with unit size, and copy it multiple times
center = vec3(0, 0, 0)
size = vec2(1, 1)

UUID = context.addPatch(center, size, SphericalCoord(1, 0, 0), "GrapeLeaf.png")

for i in range(10):
    UUID_copy = context.copyPrimitive(UUID)

    position = vec3(i*3, 0, 0)

    context.translatePrimitive(UUID_copy, position)

# Let's delete the original "template"
context.deletePrimitive(UUID)
```

| Property | Getter Function |
|----------|-----------------|

### Compound Geometry {#Compound}

The Context has functions to rapidly generate various shapes, which consist of many primitives. These functions simply add the primitives needed to make the specified geometry, and return a vector of UUIDs corresponding to each of the primitives. The important distinction between these functions and those to add "Objects" (described below) is that Objects retain information about the overall 3D object such as the radius of the sphere.

Functions for adding compound geometry are listed below.

| Geometry | Description | Adder function(s) | Example |
|----------|-------------|-------------------|---------|
| Tile | Patch subdivided into uniform grid of sub-patches. | <ul><li>\ref pyhelios.Context.Context::addTile "addTile(center, size, rotation, subdiv)"</li><li>\ref pyhelios.Context.Context::addTile "addTile(center, size, rotation, subdiv, color)"</li><li>\ref pyhelios.Context.Context::addTile "addTile(center, size, rotation, subdiv, texturefile)"</li></ul> | ![](images/primitives/Tile.png) |
| Sphere | Spherical object tessellated with Triangle primitives. | <ul><li>\ref pyhelios.Context.Context::addSphere "addSphere(Ndivs, center, radius)"</li><li>\ref pyhelios.Context.Context::addSphere "addSphere(Ndivs, center, radius, color)"</li><li>\ref pyhelios.Context.Context::addSphere "addSphere(Ndivs, center, radius, texturefile)"</li></ul> | ![](images/primitives/Sphere.png) |
| Tube | Cylindrical tube object tessellated with Triangle primitives. Follows a specified path and can change radius along its length. | <ul><li>\ref pyhelios.Context.Context::addTube "addTube(Ndivs, nodes, radius)"</li><li>\ref pyhelios.Context.Context::addTube "addTube(Ndivs, nodes, radius, color)"</li></ul> | ![](images/primitives/Tube.png) |
| Box | Rectangular prism object tessellated with Patch primitives. | <ul><li>\ref pyhelios.Context.Context::addBox "addBox(center, size, subdiv)"</li><li>\ref pyhelios.Context.Context::addBox "addBox(center, size, subdiv, color)"</li><li>\ref pyhelios.Context.Context::addBox "addBox(center, size, subdiv, color, reverse_normals)"</li></ul> | ![](images/primitives/Box.png) |
| Disk | Ellipsoidal disk object tessellated with Triangle primitives. | <ul><li>\ref pyhelios.Context.Context::addDisk "addDisk(Ndiv, center, size)"</li><li>\ref pyhelios.Context.Context::addDisk "addDisk(Ndiv, center, size, rotation)"</li><li>\ref pyhelios.Context.Context::addDisk "addDisk(Ndiv, center, size, rotation, color)"</li><li>\ref pyhelios.Context.Context::addDisk "addDisk(Ndiv, center, size, rotation, color)"</li><li>\ref pyhelios.Context.Context::addDisk "addDisk(Ndiv, center, size, rotation, texture_file)"</li></ul> | ![](images/primitives/Disk.png) |

### Objects {#Objects}

Objects are geometries consisting of many primitive elements. The critical difference between "Objects" and the compound objects described above is that Objects retain information about the overall geometry such as length, radius, etc., and have many sub-functions for manipulating them and assigning data. This is often useful when you want to know information about the overall object or want to manipulate the entire object in unison.

Functions for adding objects return a uint that serves as a unique identifier for the object, which can be used for later reference and manipulation. Functions for adding objects are listed in the table below.

| Object | Description | Adder function(s) | Example |
|--------|-------------|-------------------|---------|
| Tile | Patch subdivided into uniform grid of sub-patches. | <ul><li>\ref pyhelios.Context.Context::addTileObject "addTileObject(center, size, rotation, subdiv)"</li><li>\ref pyhelios.Context.Context::addTileObject "addTileObject(center, size, rotation, subdiv, color)"</li><li>\ref pyhelios.Context.Context::addTileObject "addTileObject(center, size, rotation, subdiv, texturefile)"</li></ul> | ![](images/primitives/Tile.png) |
| Sphere | Spherical object tessellated with Triangle primitives. | <ul><li>\ref pyhelios.Context.Context::addSphereObject "addSphereObject(Ndivs, center, radius)"</li><li>\ref pyhelios.Context.Context::addSphereObject "addSphereObject(Ndivs, center, radius, color)"</li><li>\ref pyhelios.Context.Context::addSphereObject "addSphereObject(Ndivs, center, radius, texturefile)"</li></ul> | ![](images/primitives/Sphere.png) |
| Tube | Cylindrical tube object tessellated with Triangle primitives. Follows a specified path and can change radius along its length. | <ul><li>\ref pyhelios.Context.Context::addTubeObject "addTubeObject(Ndivs, nodes, radius)"</li><li>\ref pyhelios.Context.Context::addTubeObject "addTubeObject(Ndivs, nodes, radius, color)"</li></ul> | ![](images/primitives/Tube.png) |
| Box | Rectangular prism object tessellated with Patch primitives. | <ul><li>\ref pyhelios.Context.Context::addBoxObject "addBoxObject(center, size, subdiv)"</li><li>\ref pyhelios.Context.Context::addBoxObject "addBoxObject(center, size, subdiv, color)"</li><li>\ref pyhelios.Context.Context::addBoxObject "addBoxObject(center, size, subdiv, color, reverse_normals)"</li></ul> | ![](images/primitives/Box.png) |
| Disk | Ellipsoidal disk object tessellated with Triangle primitives. | <ul><li>\ref pyhelios.Context.Context::addDiskObject "addDiskObject(Ndiv, center, size)"</li><li>\ref pyhelios.Context.Context::addDiskObject "addDiskObject(Ndiv, center, size, rotation)"</li><li>\ref pyhelios.Context.Context::addDiskObject "addDiskObject(Ndiv, center, size, rotation, color)"</li><li>\ref pyhelios.Context.Context::addDiskObject "addDiskObject(Ndiv, center, size, rotation, color)"</li><li>\ref pyhelios.Context.Context::addDiskObject "addDiskObject(Ndiv, center, size, rotation, texture_file)"</li></ul> | ![](images/primitives/Disk.png) |
| Cone | Tapered cylinder/cone object tessellated with triangles. | <ul><li>\ref pyhelios.Context.Context::addConeObject "addConeObject(Ndivs, node0, node1, radius0, radius1)"</li><li>\ref pyhelios.Context.Context::addConeObject "addConeObject(Ndivs, node0, node1, radius0, radius1, color)"</li><li>\ref pyhelios.Context.Context::addConeObject "addConeObject(Ndivs, node0, node1, radius0, radius1, texturefile)"</li></ul> | ![](images/primitives/Cone.png) |

**Note:** PyHelios uses a Context-centric design. Objects are manipulated through Context methods:

```python
# Manipulate objects via Context, not object pointers
objID = context.addTileObject(center, size, rotation, subdivisions)
context.translateObject(objID, shift)
context.rotateObject(objID, angle, 'z')
context.scaleObject(objID, factor)
```

#### Domain Bounds {#DomainBounds}

The overall extent of all primitives in the Context (or a filtered subset) can be queried with two helpers. `getDomainBoundingBox()` returns a tuple `(xbounds, ybounds, zbounds)` of three `vec2` values where each `vec2.x` is the minimum and `vec2.y` is the maximum along that axis. `getDomainBoundingSphere()` returns `(center, radius)` as `(vec3, float)`. Both methods accept an optional `uuids` argument to restrict the computation to a subset of primitives.

```python
xb, yb, zb = context.getDomainBoundingBox()
center, radius = context.getDomainBoundingSphere()

# Filtered: bounds of just two primitives
xb, yb, zb = context.getDomainBoundingBox(uuids=[uuid1, uuid2])
```

## Data Structures {#Data}

Data structures that are moved in and out of plugins are managed by the Context.  There are three types of Context data structures that serve different purposes:

- **Primitive Data** - is a piece of data associated with a given primitive. An example of this may be the reflectivity or temperature of a given primitive. Primitive data is flexible in that it can have different data types, variable lengths, and can be different for different primitives.  For example, voxels could have a data value specifying the attenuation coefficient, but the attenuation coefficient would not be relevant for patches so they would not have this piece of data.  A given primitive could have an array of 10 integers as its data.  However, primitive data is limited to one-dimensional arrays, and mapping to multidimensional data is left to the user.
- **Material Data** - is a piece of data associated with a named material rather than an individual primitive. Multiple primitives can share the same material, so writing the data once on the material is reflected on every primitive that references it.
- **Global Data** - is similar to 'primitive data', except that global data is not necessarily associated with any particular primitive. An example of global data might be the solar radiative flux incident on the earth.

Implementation of data structure usage is detailed for each type of structure below.

PyHelios supports primitive, material, and global data of the following types: `int`, `uint`, `float`, `double`, `vec2`, `vec3`, `vec4`, `int2`, `int3`, `int4`, and `str`. Unlike the C++ API which uses type enumeration constants, PyHelios uses type-specific methods (e.g., `setPrimitiveDataFloat()`, `setPrimitiveDataVec3()`) for clearer, more Pythonic code.

## Primitive Data {#PrimData}

### Setting Primitive Data Values {#SetPrimData}

Primitive data values can be scalar or a one-dimensional array of values.


```python
from pyhelios import Context
from pyhelios.types import vec3, vec2, RGBcolorcolor

context = Context()

center = vec3(0, 0, 0)
size = vec2(1, 1)

UUID = context.addPatch(center, size, RGBcolorcolor(1, 0, 0))

eps = 0.9
context.setPrimitiveDataFloat(UUID, "emissivity", eps)
```

For array/vector data, use the appropriate vector type. PyHelios provides type-specific methods for setting primitive data.

```python
from pyhelios import Context
from pyhelios.types import vec3, vec2, RGBcolor

context = Context()

center = vec3(0, 0, 0)
size = vec2(1, 1)

UUID = context.addPatch(center, size)

# For vec2 data, use setPrimitiveDataVec2
context.setPrimitiveDataVec2(UUID, "somedata", vec2(2.3, 9.2))

# Or pass components directly
context.setPrimitiveDataVec2(UUID, "somedata", 2.3, 9.2)
```

### Getting Primitive Data Values {#GetPrimData}

If primitive data is a scalar value, it can be retrieved for a given primitive via the Context using the \ref pyhelios.Context.Context::getPrimitiveData "getPrimitiveData(UUID, label)" function:

```python
from pyhelios import Context

context = Context()

center = vec3(0, 0, 0)
size = vec2(1, 1)

UUID = context.addPatch(center, size)

eps = 0.9
context.setPrimitiveData(UUID, "emissivity", eps)

emissivity = context.getPrimitiveData(UUID, "emissivity")
```

In the above example, the value of 'emissivity' is 0.9.

### Primitive Data Query Functions {#PrimDataHelpers}

It is often necessary to query information about primitive data. The following table lists functions used to query primitive data information.

| Function | Description |
|----------|-------------|
| \ref pyhelios.Context.Context::doesPrimitiveDataExist "doesPrimitiveDataExist(UUID, label)" | Check whether primitive data named 'label' exists for the primitive. |
| \ref pyhelios.Context.Context::getPrimitiveDataType "getPrimitiveDataType(UUID, label)" | Get the HeliosDataType for the primitive. |
| \ref pyhelios.Context.Context::getPrimitiveDataSize "getPrimitiveDataSize(UUID, label)" | Get the length/size of the primitive data named 'label'. |

<p> <br> </p>

```python
from pyhelios import Context

context = Context()

center = vec3(0, 0, 0)
size = vec2(1, 1)

UUID = context.addPatch(center, size)

eps = 0.9
context.setPrimitiveDataFloat(UUID, "emissivity", eps)

if context.doesPrimitiveDataExist(UUID, "emissivity"):
    data_type = context.getPrimitiveDataType(UUID, "emissivity")
    L = context.getPrimitiveDataSize(UUID, "emissivity")
```

## Material Data {#MaterialData}

Material data is similar to primitive data, but is attached to a named *material* rather than a UUID. A material is created with `addMaterial(label)` and can then be assigned to one or more primitives via `assignMaterialToPrimitive(uuid, label)`. Setting a data value on the material is reflected for every primitive that references it, which is useful for storing shared physical properties (e.g., a leaf reflectivity that applies to every leaf).

PyHelios provides per-type setter and getter methods for all 11 supported types: `setMaterialDataInt`, `setMaterialDataUInt`, `setMaterialDataFloat`, `setMaterialDataDouble`, `setMaterialDataString`, `setMaterialDataVec2`, `setMaterialDataVec3`, `setMaterialDataVec4`, `setMaterialDataInt2`, `setMaterialDataInt3`, `setMaterialDataInt4`, and the matching `getMaterialData<Type>` accessors. There is also a unified `setMaterialData(material_label, data_label, value)` that detects the value's type at the call site, and a `getMaterialData(material_label, data_label, dtype=None)` that auto-detects the stored type via `getMaterialDataType()` when `dtype` is omitted.

```python
from pyhelios import Context
from pyhelios.types import vec3

context = Context()
context.addMaterial("leaf")

# Per-type explicit (preferred when the type is known)
context.setMaterialDataFloat("leaf", "reflectivity", 0.12)
r = context.getMaterialDataFloat("leaf", "reflectivity")

# Unified dispatch (handy for generic code)
context.setMaterialData("leaf", "tint", vec3(0.2, 0.7, 0.1))
tint = context.getMaterialData("leaf", "tint")  # auto-detects vec3
```

For an entry whose type is unknown at runtime, `getMaterialDataType(material_label, data_label)` returns the `HeliosDataType` enum value (0=INT, 1=UINT, 2=FLOAT, 3=DOUBLE, 4=VEC2, 5=VEC3, 6=VEC4, 7=INT2, 8=INT3, 9=INT4, 10=STRING). Use `doesMaterialDataExist()` to check for presence and `clearMaterialData()` to remove an entry.

### Unique Data Values {#UniqueValues}

For data labels with bounded sets of values (e.g., a categorical "species" string or a small integer ID), PyHelios can pre-cache the unique values seen on primitives or compound objects. Caching must be **enabled before** the data is written:

```python
context.enablePrimitiveDataValueCaching("species")
# ... set primitive data with that label ...
unique = context.getUniquePrimitiveDataValues("species", str)  # ["maple", "oak", ...]
```

The same pattern applies to objects via `enableObjectDataValueCaching()` and `getUniqueObjectDataValues(label, dtype)`. Supported `dtype` values are `int`, `str`, and the string `"uint"`.

## Global Data {#GlobalData}

Global data is similar to primitive data, except that it does not correspond to any particular primitive, rather it is a single instance of a certain data structure. The functions used to create global data within the Context are essentially the same as those used to create primitive data, except they do not take a primitive UUID as an argument (because they do not correspond to primitives).

## Data Timeseries (Weather Inputs) {#DataTimeseries}

Timeseries - or data points corresponding to discrete points in time - can be managed by the Context.  This typically corresponds to weather data that is measured by a sensor.  Timeseries data points are added to the Context by giving the value of the data point, along with Date and Time vectors.  An example is given below to manually add 15-min timeseries data to the Context.

Data in the timeseries can be accessed either via the queryTimeseriesData() function by giving the index of the data point, or by giving a date and time.  To loop through all data in the timeseries, we can query the length of the timeseries and make a for-loop.

```python
from pyhelios import Context
from pyhelios.types import Date, Time

# Initialize the Context
context = Context()

# Add data to timeseries
# Date constructor: Date(year, month, day)
date = Date(2000, 1, 2)  # 2 Jan. 2000

time = Time(13, 0, 0)  # 13:00:00
context.addTimeseriesData("temperature", 301.23, date, time)  # index #0

time = Time(13, 15, 0)  # 13:15:00
context.addTimeseriesData("temperature", 301.92, date, time)  # index #1

time = Time(13, 30, 0)  # 13:30:00
context.addTimeseriesData("temperature", 302.56, date, time)  # index #2

time = Time(13, 45, 0)  # 13:45:00
context.addTimeseriesData("temperature", 303.05, date, time)  # index #3

T = context.queryTimeseriesData("temperature", 1)  # Here, T = 301.92

time = Time(13, 15, 0)
T = context.queryTimeseriesData("temperature", date, time)  # Also here, T = 301.92

for i in range(context.getTimeseriesLength("temperature")):
    T = context.queryTimeseriesData("temperature", i)
    time = context.getTimeseriesTime("temperature", i)
    print(f"Temperature at time {time.hour:02d}:{time.minute:02d}:{time.second:02d} is {T}")
```

Typically, data is not entered manually, but rather through an XML or text file (see [Reading XML Files](#XMLread) for information).

It is often necessary to get the number of data points in a given timeseries, which can be accomplished with the command:

```python
N = context.getTimeseriesLength("temperature")
```

An entire timeseries variable (with all of its time points) can be removed using `deleteTimeseriesVariable()`. If the variable does not exist a non-fatal warning is issued and the call is otherwise a no-op. To wipe every timeseries variable at once, use `clearTimeseriesData()` instead.

```python
context.deleteTimeseriesVariable("temperature")  # removes the variable and all of its data points
```

---

