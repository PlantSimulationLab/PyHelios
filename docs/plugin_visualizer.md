# Visualizer Plugin Documentation {#VisualizerDoc}

[TOC]

<table>
<tr><th>Dependencies</th><td>X11/xorg (Mac/Linux)</td></tr>
<tr><th>Python Import</th><td>`from pyhelios import Visualizer`</td></tr>
<tr><th>Main Class</th><td>\ref pyhelios.Visualizer.Visualizer "Visualizer"</td></tr>
</table>

## System Requirements

<table>
  <tr>
    <th>Dependencies</th>
    <td>X11/xorg (Mac/Linux), OpenGL 3.3+</td>
  </tr>
  <tr>
    <th>Platforms</th>
    <td>Windows, Linux, macOS</td>
  </tr>
  <tr>
    <th>GPU</th>
    <td>OpenGL 3.3 compatible graphics card required</td>
  </tr>
</table>

## Quick Start

```python
from pyhelios import Context, Visualizer
from pyhelios.types import vec3, vec2, RGBcolor

with Context() as context:
    # Create minimal geometry
    patch_uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))

    # Use Visualizer with context manager (recommended)
    with Visualizer(width=1200, height=800) as vis:
        # Build scene geometry from Context
        vis.buildContextGeometry(context)

        # Configure view
        vis.setCameraPosition(vec3(3, 3, 3), vec3(0, 0, 0))
        vis.setBackgroundColor(RGBcolor(0.5, 0.7, 1.0))

        # Show interactive visualization
        vis.plotInteractive()
```

## Class Constructor {#VisClass}

<table>
<tr><th>Constructors</th></tr>
<tr><td>\ref pyhelios.Visualizer.Visualizer "Visualizer(width, height, antialiasing_samples=1, headless=False)"</td></tr>
</table>

The class associated with the visualization is called Visualizer. The class constructor takes width and height arguments that specify the size of the graphics window in pixels. Additional optional parameters control antialiasing quality and headless rendering mode. Below is an example:

```python
from pyhelios import Visualizer

# Opens a graphics window of 1200x800 pixels
with Visualizer(width=1200, height=800) as vis:
    pass
```

## Dependencies {#VisDepends}

<table>
  <tr>
     <th>Installation Method</th>
     <th>Dependency</th>
     <td>\image html apple-logo.png</td>
     <td>\image html unix-logo.png</td>
     <td>\image html windows-logo.png</td>
  </tr>
  <tr>
     <td rowspan="2">**Runtime**<br>(pip install)</td>
     <td>X11 Server</td>
     <td>Required:<br>`$ brew install --cask xquartz`</td>
     <td>Usually pre-installed</td>
     <td>None</td>
  </tr>
  <tr>
     <td>OpenGL 3.3+</td>
     <td colspan="3">Compatible graphics card and drivers</td>
  </tr>
  <tr style="border-top: 3px double #888">
     <td>**Build from Source**<br>(additional deps)</td>
     <td>Development Libraries</td>
     <td>Same as runtime</td>
     <td>`$ sudo apt-get install libx11-dev xorg-dev libgl1-mesa-dev libglu1-mesa-dev libxrandr-dev`</td>
     <td>Visual Studio</td>
  </tr>
</table>

## Known Issues {#VisIssues}

- **macOS OpenGL Warning in Headless Mode**: When using headless rendering on macOS, you may see a warning like:
  ```
  UNSUPPORTED (log once): POSSIBLE ISSUE: unit 6 GLD_TEXTURE_INDEX_2D is unloadable and bound to sampler type (Float) - using zero texture because texture unloadable
  ```
  This is a harmless driver warning from the macOS OpenGL implementation and does not affect rendering functionality. It appears once per run and can be safely ignored.

- Large point clouds are supported with automatic culling optimization.

## Introduction {#VisIntro}

This plugin facilitates visualization of model geometry and data. It can visualize a number of different geometric shapes, including all of the primitive types supported by the Helios context. Individual geometric objects can be added though API commands, and there is a command to automatically add all geometric primitives from the Helios context.

## Using the Visualizer Plug-in {#UseVis}

### Coordinate Systems {#coord}

The visualizer uses two types of coordinate systems to specify the locations of points in space during visualization:

1. **COORDINATES_WINDOW_NORMALIZED** - Coordinates are normalized to unity and are window-aligned. The point (x,y)=(0,0) is in the bottom left corner of the window, and (x,y)=(1,1) is in the upper right corner of the window. The z-coordinate specifies the depth in the screen-normal direction, with values ranging from -1 to 1. For example, an object at z=0.5 would be behind an object at z=0. This coordinate system is typically used when annotating visualizations with text, adding watermarks, or adding objects to the dashboard.

2. **COORDINATES_CARTESIAN** - Coordinates are specified in a 3D Cartesian system (right-handed), where +z is vertical. This coordinate system is typically used when adding model geometry or 3D objects.

### Visualization Window {#Window}

In order to actually display a window for visualization, we must issue a command to plot the geometry. There are different commands to produce a visualization window depending on the intended output:

- \ref pyhelios.Visualizer.Visualizer::plotInteractive "plotInteractive()" - Open an interactive visualization window that allows for user input control. This type of visualization allows for one to, for example, rotate the view or zoom in/out. This will cause the program to wait until the window is closed by the user to continue.
- \ref pyhelios.Visualizer.Visualizer::plotUpdate "plotUpdate()" - Open a window and update it with the current visualization, then continue the program. This does not allow for any user input, since it continues on without checking for input. This is useful when generating a large number of visualization images for a movie.

If \ref pyhelios.Visualizer.Visualizer::plotUpdate "plotUpdate()" is issued, another command \ref pyhelios.Visualizer.Visualizer::printWindow "printWindow()" can be used to output the current visualization to file (JPEG or PNG files).

The current window can be closed using the \ref pyhelios.Visualizer.Visualizer::closeWindow "closeWindow()" command.

Below is an example of opening a window (blank), exporting its contents to file, then closing the window:

```python
from pyhelios import Visualizer

with Visualizer(width=1200, height=800) as vis:
    vis.plotUpdate()  # we have not added geometry, so window is blank
    vis.printWindow("blank_window.jpg")
    vis.closeWindow()
```

### Headless Rendering {#Headless}

The Visualizer supports headless rendering for server environments or automated workflows where no display is available. Headless mode enables all visualization and image export functionality without requiring a graphics display or user interaction.

**Enabling Headless Mode:**

Headless mode is enabled through the constructor by setting the `headless` parameter to `True`:

```python
from pyhelios import Context, Visualizer
from pyhelios.types import vec3

with Context() as context:
    # Enable headless mode
    with Visualizer(width=1200, height=800, antialiasing_samples=8, headless=True) as vis:
        # All visualization functions work normally
        vis.buildContextGeometry(context)
        vis.setCameraPosition(vec3(0, 0, 5), vec3(0, 0, 0))
        vis.plotUpdate()
        vis.printWindow("headless_output.jpg")
```

**Key Features:**
- Full OpenGL rendering using offscreen framebuffers
- All geometry types and visual effects supported
- Image export via \ref pyhelios.Visualizer.Visualizer::printWindow "printWindow()"
- No display or window manager required
- Identical visual output to windowed mode

**Important Notes:**
- When in headless mode, \ref pyhelios.Visualizer.Visualizer::plotInteractive "plotInteractive()" is not available
- Always use \ref pyhelios.Visualizer.Visualizer::plotUpdate "plotUpdate()" for headless workflows

**Use Cases:**
- Automated visualization pipelines on servers
- Batch processing of simulation results
- Integration with cloud computing environments
- Continuous integration testing of visualization features

### Window Background {#Background}

The Visualizer provides multiple options for customizing the window background:

**Default Gradient Background**

By default, the Visualizer displays a subtle vertical gradient background that transitions from a neutral blue at the bottom to white at the top. This provides a clean, professional appearance without requiring any configuration.

**Solid Color Background**

The window background can be set to a constant color using the \ref pyhelios.Visualizer.Visualizer::setBackgroundColor "setBackgroundColor()" command:

```python
from pyhelios import Visualizer
from pyhelios.types import RGBcolor

with Visualizer(width=1200, height=800) as vis:
    vis.setBackgroundColor(RGBcolor(1.0, 1.0, 1.0))  # Set background to white
```

**Transparent Background**

For creating visualizations with transparent backgrounds (useful for overlaying on other images or presentations), use the \ref pyhelios.Visualizer.Visualizer::setBackgroundTransparent "setBackgroundTransparent()" command. When rendering to the screen, a checkerboard pattern indicates transparency. When exporting to PNG format via \ref pyhelios.Visualizer.Visualizer::printWindow "printWindow()", the background will have true alpha channel transparency:

```python
from pyhelios import Visualizer

with Visualizer(width=1200, height=800) as vis:
    vis.setBackgroundTransparent()
    vis.plotUpdate()
    vis.printWindow("output.png", "png")  # Saves with transparent background
```

Note: Transparent backgrounds only work with PNG output format. JPEG output will have an opaque background.

**Custom Image Background**

You can set a custom texture image as the background using the \ref pyhelios.Visualizer.Visualizer::setBackgroundImage "setBackgroundImage()" command:

```python
from pyhelios import Visualizer

with Visualizer(width=1200, height=800) as vis:
    vis.setBackgroundImage("path/to/custom_background.jpg")
```

The image will be stretched to fill the window while maintaining the aspect ratio to avoid distortion. Both JPEG and PNG formats are supported.

**Sky Texture Background**

For outdoor scenes, a three-dimensional sky background can be added using the \ref pyhelios.Visualizer.Visualizer::setBackgroundSkyTexture "setBackgroundSkyTexture()" command. This creates a dynamically scaling sky sphere that uses shader-based transformations to keep the camera always inside, eliminating the need to manually specify a radius. The sky appears infinitely distant regardless of camera position or zoom level:

```python
from pyhelios import Visualizer

with Visualizer(width=1200, height=800) as vis:
    # Use default sky texture (SkyDome_clouds.jpg)
    vis.setBackgroundSkyTexture()

    # Or specify a custom texture
    # vis.setBackgroundSkyTexture("path/to/custom_sky.jpg")
```

The method automatically uses the default sky texture (`plugins/visualizer/textures/SkyDome_clouds.jpg`) if no texture file is specified. The sky can be toggled on/off like other background modes using \ref pyhelios.Visualizer.Visualizer::setBackgroundColor "setBackgroundColor()", \ref pyhelios.Visualizer.Visualizer::setBackgroundTransparent "setBackgroundTransparent()", or \ref pyhelios.Visualizer.Visualizer::setBackgroundImage "setBackgroundImage()".

### Adding Geometry {#AddGeom}

PyHelios Visualizer supports geometry visualization through two primary methods:

1. **Importing from Context** - Load all geometry primitives (patches, triangles, voxels, etc.) from a Helios Context
2. **Utility Objects** - Add coordinate axes and grid wireframes for reference

**Note:** Direct geometry addition methods (addRectangle, addTriangle, etc.) available in the native C++ Helios library are not yet exposed in PyHelios. Use Context primitives and `buildContextGeometry()` instead.

#### Importing Context Geometry {#ContextGeom}

The visualizer can automatically import some or all geometry from the Context. This is accomplished using the \ref pyhelios.Visualizer.Visualizer::buildContextGeometry "buildContextGeometry()" command. To add all primitives in the Context, the \ref pyhelios.Visualizer.Visualizer::buildContextGeometry "buildContextGeometry()" command would be issued, which is passed the Context. We can add a subset of the Context geometry through an additional argument which takes a list of UUIDs.

<table>
  <tr>
     <th>Command</th>
     <th>Description</th>
  </tr>
  <tr>
     <td>\ref pyhelios.Visualizer.Visualizer::buildContextGeometry "buildContextGeometry(context)"</td>
     <td>Add all primitives in the Context to the Visualizer.</td>
  </tr>
  <tr>
     <td>\ref pyhelios.Visualizer.Visualizer::buildContextGeometry "buildContextGeometry(context, uuids=[...])"</td>
     <td>Add a subset of primitives in the Context to the Visualizer.</td>
  </tr>
</table>

The example below shows how to add all Context geometry to the visualizer.

```python
from pyhelios import Context, Visualizer
from pyhelios.types import vec3, vec2

with Context() as context:
    center = vec3(0, 0, 0)
    size = vec2(1, 1)
    context.addPatch(center=center, size=size)

    with Visualizer(width=1200, height=800) as vis:
        vis.buildContextGeometry(context)
```

#### Utility Objects {#UtilityObjects}

PyHelios Visualizer provides methods to add reference objects:

<table>
  <tr>
     <th>Method</th>
     <th>Description</th>
  </tr>
  <tr>
     <td>addCoordinateAxes()</td>
     <td>Add XYZ coordinate axes at the origin</td>
  </tr>
  <tr>
     <td>addCoordinateAxesCustom(origin, length, sign)</td>
     <td>Add coordinate axes at custom position with custom length</td>
  </tr>
  <tr>
     <td>addGridWireFrame(center, size, subdivisions)</td>
     <td>Add a 3D grid wireframe for spatial reference</td>
  </tr>
</table>

Example:

```python
from pyhelios import Visualizer
from pyhelios.types import vec3

with Visualizer(width=1200, height=800) as vis:
    # Add coordinate axes at origin
    vis.addCoordinateAxes()

    # Add custom grid
    vis.addGridWireFrame(vec3(0, 0, 0), vec3(10, 10, 10), [10, 10, 10])
```

### Point Cloud Performance Optimization {#PointCloudPerf}

For large point clouds (tens of millions of points), the visualizer includes automatic culling optimization to maintain interactive performance. This feature is enabled by default when the number of points exceeds a configurable threshold.

**Note:** Point cloud culling configuration functions are available in the native C++ Helios library but are not yet exposed in PyHelios. The automatic culling optimization is still active at the C++ level.

### Plotting Geometry {#PlotWindow}

To this point, we have not actually plotted anything in the Visualizer window. A final command is needed to display all of the geometry added to the Visualizer in the window we have opened. There are two functions for doing this, which are detailed below.

#### plotInteractive() {#PlotInteractive}

The \ref pyhelios.Visualizer.Visualizer::plotInteractive "plotInteractive()" function can be used to generate an interactive plot of the geometry in the Visualizer. This means that the code will pause to produce the plot/visualization until the window is closed by the user. The user can interact with the plot by issuing keystrokes to, e.g., zoom. An example is given below to generate an interactive plot.

```python
from pyhelios import Context, Visualizer
from pyhelios.types import vec3, vec2

with Context() as context:
    center = vec3(0, 0, 0)
    size = vec2(1, 1)
    context.addPatch(center=center, size=size)

    with Visualizer(width=1200, height=800) as vis:
        vis.buildContextGeometry(context)
        vis.plotInteractive()
```

#### View Controls {#ViewControls}

In an interactive plot, the view can be modified via the mouse or keyboard. Note that for very large scenes, mouse-based controls may be laggy.

Mouse camera controls are given by:

<table>
    <tr>
        <th>Mouse Button</th>
        <th>Action</th>
    </tr>
    <tr>
        <td>scroll wheel</td>
        <td>zoom in/out relative to look-at position</td>
    </tr>
    <tr>
        <td>left mouse button (+drag)</td>
        <td>rotate camera view about look-at position</td>
    </tr>
    <tr>
        <td>right mouse button (+drag)</td>
        <td>move look-at position</td>
    </tr>
</table>

Keyboard camera controls are given by:

<table>
  <tr>
     <th>Key</th>
     <th>Action</th>
  </tr>
  <tr>
     <td>up arrow</td>
     <td>increase the viewing elevation angle</td>
  </tr>
  <tr>
     <td>down arrow</td>
     <td>decrease the viewing elevation angle</td>
  </tr>
  <tr>
     <td>left arrow</td>
     <td>rotate camera left (clockwise)</td>
  </tr>
  <tr>
     <td>right arrow</td>
     <td>rotate camera right (counter-clockwise)</td>
  </tr>
  <tr>
     <td>spacebar+up arrow</td>
     <td>move the camera position upward</td>
  </tr>
  <tr>
     <td>spacebar+down arrow</td>
     <td>move the camera position downward</td>
  </tr>
  <tr>
     <td>+</td>
     <td>zoom in</td>
  </tr>
  <tr>
     <td>-</td>
     <td>zoom out</td>
  </tr>
</table>

#### plotUpdate() {#PlotUpdate}

The \ref pyhelios.Visualizer.Visualizer::plotUpdate "plotUpdate()" function simply updates the plot window based on current geometry, and continues on to the next lines of code. This can be useful if only a still image is to be written to file, as illustrated below.

```python
from pyhelios import Context, Visualizer
from pyhelios.types import vec3, vec2

with Context() as context:
    center = vec3(0, 0, 0)
    size = vec2(1, 1)
    context.addPatch(center=center, size=size)

    with Visualizer(width=1200, height=800) as vis:
        vis.buildContextGeometry(context)
        vis.plotUpdate()
        vis.printWindow("rectangle.jpg")
        vis.closeWindow()
```

### Colors and Shading {#ColorShade}

#### Coloring by r-g-b Code {#ColoringRGB}

The surfaces of primitives are most commonly colored by specifying an r-g-b/r-g-b-a color code when adding the geometry, and thus this is the default behavior.

#### Coloring by Texture Map {#ColoringTexture}

Rectangles and disks have the capability of coloring their surface according to a texture map. A texture map can be specified by providing the path to either a JPEG or PNG image file. The image will be mapped onto the surface of the primitive element.

#### Coloring by Pseudocolor Map {#ColoringPseudo}

Primitives can be colored by mapping associated data values to a color table. Given some range of data values, each value is normalized by this range and used to look up an associated color in the color table. The available predefined color tables are shown below. There is also the capability of defining custom color tables.

<table>
  <tr>
     <th>Colormap Name</th>
     <th>Example</th>
  </tr>
  <tr>
     <td>COLORMAP_HOT</td>
     <td>\image html colormap_hot.png</td>
  </tr>
  <tr>
     <td>COLORMAP_COOL</td>
     <td>\image html colormap_cool.png</td>
  </tr>
  <tr>
     <td>COLORMAP_RAINBOW</td>
     <td>\image html colormap_rainbow.png</td>
  </tr>
  <tr>
     <td>COLORMAP_LAVA</td>
     <td>\image html colormap_lava.png</td>
  </tr>
  <tr>
     <td>COLORMAP_PARULA</td>
     <td>\image html colormap_parula.png</td>
  </tr>
  <tr>
     <td>COLORMAP_GRAY</td>
     <td>\image html colormap_gray.png</td>
  </tr>
  <tr>
     <td>COLORMAP_CUSTOM</td>
     <td>N/A</td>
  </tr>
</table>

To color primitives by data values, use the \ref pyhelios.Visualizer.Visualizer::colorContextPrimitivesByData "colorContextPrimitivesByData()" method:

```python
from pyhelios import Context, Visualizer
from pyhelios.types import vec3, vec2

with Context() as context:
    # Create patches with associated data
    uuid1 = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
    uuid2 = context.addPatch(center=vec3(2, 0, 0), size=vec2(1, 1))

    # Use type-specific setPrimitiveData methods
    context.setPrimitiveDataFloat(uuid1, "temperature", 25.0)
    context.setPrimitiveDataFloat(uuid2, "temperature", 35.0)

    with Visualizer(width=1200, height=800) as vis:
        vis.buildContextGeometry(context)
        vis.colorContextPrimitivesByData("temperature")
        vis.plotInteractive()
```

##### Colorbar {#Cbar}

The colorbar is the legend showing how values are mapped to the color table. The table below gives functions for customizing colorbar behavior, including for example its position, size, and visibility.

<table>
  <tr>
     <th>Function</th>
     <th>Description</th>
  </tr>
  <tr>
     <td>enableColorbar()</td>
     <td>Make the colorbar visible.</td>
  </tr>
  <tr>
     <td>disableColorbar()</td>
     <td>Make the colorbar invisible.</td>
  </tr>
  <tr>
     <td>setColorbarPosition(position)</td>
     <td>Set the position of the colorbar. Note that position.z gives the depth of the colorbar.</td>
  </tr>
  <tr>
     <td>setColorbarSize(size)</td>
     <td>Set the size of the colorbar.</td>
  </tr>
  <tr>
     <td>setColorbarRange(cmin, cmax)</td>
     <td>Set the range of data values for the colorbar/colormap.</td>
  </tr>
  <tr>
     <td>setColorbarTicks(ticks)</td>
     <td>Set locations of data tick along colorbar.</td>
  </tr>
  <tr>
     <td>setColorbarTitle(title)</td>
     <td>Set the title text displayed above the colorbar.</td>
  </tr>
  <tr>
     <td>setColorbarFontColor(color)</td>
     <td>Set the color of text in the colorbar.</td>
  </tr>
  <tr>
     <td>setColorbarFontSize(font_size)</td>
     <td>Set the size of the colorbar text in points.</td>
  </tr>
</table>

###### Automatic Tick Generation {#auto_ticks}

When custom ticks are not specified using setColorbarTicks, the visualizer automatically generates tick positions and labels using Heckbert's "nice numbers" algorithm. This algorithm selects tick values that are "clean" multiples of 1, 2, or 5 times a power of 10, making the colorbar easier to read.

**Adaptive Tick Count:** The number of ticks is automatically determined based on the colorbar size and font size to prevent overcrowding. Smaller colorbars will have fewer ticks to maintain readability.

For example:
- A colorbar ranging from 0 to 1 will generate ticks at 0.0, 0.2, 0.4, 0.6, 0.8, 1.0
- A colorbar ranging from 0 to 600 (with limited space) will generate ticks at 0, 200, 400, 600
- A colorbar ranging from 0 to 20 with integer data will generate ticks at 0, 5, 10, 15, 20

The tick label formatting automatically adapts based on the data type and range:
- **Integer data**: Tick labels are formatted as integers with no decimal places (e.g., 0, 5, 10). For values ≥10,000, scientific notation is used (e.g., 1e+04)
- **Floating-point data**: Tick labels show an appropriate number of decimal places based on the tick spacing (e.g., 0.0, 0.2, 0.4). Scientific notation is used for values ≥10,000 or <0.001
- **Scientific notation**: Automatically used for very large (≥10,000) or very small (<0.001) values to maintain readability

The data type (integer vs. float) is automatically detected when calling \ref pyhelios.Visualizer.Visualizer::colorContextPrimitivesByData "colorContextPrimitivesByData()".

\image html vineyard_PAR_cmap.png

#### Shading {#Shading}

To allow for more realistic visualizations, the Phong shading model can be enabled. The Phong shading model can be enabled with or without shadows. The shading options are detailed in the table below. The appropriate value is passed to the \ref pyhelios.Visualizer.Visualizer::setLightingModel "setLightingModel()" command to enable the specified shading model.

<table>
  <tr>
     <th>Shading Model</th>
     <th>Value</th>
     <th>Description</th>
  </tr>
  <tr>
     <td>No shading</td>
     <td>0 or "none"</td>
     <td>No shading is applied. Objects are colored only according to the r-g-b(-a) color code or texture map.</td>
  </tr>
  <tr>
     <td>Phong shading</td>
     <td>1 or "phong"</td>
     <td>Phong shading model</td>
  </tr>
  <tr>
     <td>Phong with shadows</td>
     <td>2 or "phong_shadowed"</td>
     <td>Phong shading model with shadows.</td>
  </tr>
</table>

If the Phong shading model is used, the position of the light source should be specified. This is accomplished through the \ref pyhelios.Visualizer.Visualizer::setLightDirection "setLightDirection()" command, which takes a unit vector pointing toward the light source. The example below shows how to enable the Phong lighting model with shadows, with the light position set according to the position of the sun.

```python
from pyhelios import Context, Visualizer
from pyhelios.types import vec3, vec2, RGBcolor

with Context() as context:
    # Create geometry
    context.addPatch(center=vec3(0, 0, 0), size=vec2(2, 2), color=RGBcolor(0.8, 0.2, 0.2))

    with Visualizer(width=1200, height=800) as vis:
        vis.buildContextGeometry(context)

        # Set light direction (unit vector pointing toward light source)
        light_direction = vec3(1, 1, 1)

        vis.setLightingModel("phong_shadowed")
        vis.setLightDirection(light_direction)

        vis.plotInteractive()
```

### View Options {#Options}

The default camera position is at an elevation angle of 20 degrees and to the North, with the camera looking toward the origin. The distance of the camera from the origin is automatically adjusted to fit all primitives in view.

There are multiple ways of specifying custom camera views. One method involves specifying the (x,y,z) position of the camera, and the (x,y,z) position that the camera is looking at. This is accomplished using the command \ref pyhelios.Visualizer.Visualizer::setCameraPosition "setCameraPosition(position, lookAt)".

The other method involves specifying the spherical coordinates of the camera with respect to the (x,y,z) position the camera is looking at. This is accomplished using the \ref pyhelios.Visualizer.Visualizer::setCameraPositionSpherical "setCameraPositionSpherical(angle, lookAt)".

```python
from pyhelios import Visualizer
from pyhelios.types import vec3, SphericalCoord

with Visualizer(width=1200, height=800) as vis:
    # Method 1: Cartesian coordinates
    vis.setCameraPosition(vec3(10, 10, 10), vec3(0, 0, 0))

    # Method 2: Spherical coordinates
    vis.setCameraPositionSpherical(SphericalCoord(15, 0.785, 1.57), vec3(0, 0, 0))
```

\image html CameraSchematic.jpeg

## Acknowledgements {#VisAcklowledgements}

This plug-in uses all or parts of the following open-sourced software libraries:

The OpenGL Extension Wrangler Library:
Copyright (C) 2008-2016, Nigel Stewart <nigels[]users sourceforge net>
Copyright (C) 2002-2008, Milan Ikits <milan ikits[]ieee org>
Copyright (C) 2002-2008, Marcelo E. Magallon <mmagallo[]debian org>
Copyright (C) 2002, Lev Povalahev
All rights reserved.

The FreeType Project:
Portions of this software are copyright © 2019 The FreeType
Project (www.freetype.org). All rights reserved.

GLFW:
Copyright © 2002-2006 Marcus Geelnard
Copyright © 2006-2019 Camilla Löwy

OpenGL Mathematics (GLM):
Copyright (c) 2005 - 2014 G-Truc Creation

libjpeg:
This software is copyright (C) 1991-2016, Thomas G. Lane, Guido Vollbeding.
All Rights Reserved except as specified below.

libpng:
Copyright (c) 1995-2019 The PNG Reference Library Authors.
Copyright (c) 2018-2019 Cosmin Truta.
Copyright (c) 2000-2002, 2004, 2006-2018 Glenn Randers-Pehrson.
Copyright (c) 1996-1997 Andreas Dilger.
Copyright (c) 1995-1996 Guy Eric Schalnat, Group 42, Inc.
