import os
from typing import Optional

from .wrappers import UGlobalWrapper as global_wrapper

class Global:
    """Process-wide helios-core functions that belong to no Context or plug-in model."""

    # =========================================================================
    # GPU Environment (helios-core v1.3.79+)
    # =========================================================================

    @staticmethod
    def gpuRequiredByEnvironment() -> bool:
        """Check whether a GPU is required by the ``HELIOS_REQUIRE_GPU`` environment variable.

        True when ``HELIOS_REQUIRE_GPU`` is set to any value other than ``"0"``.
        This is the counterpart to the ``HELIOS_NO_GPU`` veto: rather than changing
        what hardware probes report, it makes the absence of a GPU an error.

        The environment is read on every call rather than cached, so a change made
        via ``os.environ`` is observed immediately — **except on Windows**, where it
        is never observed at all. ``libhelios.dll`` links the MSVC C runtime
        statically, so it holds a private copy of the environment snapshotted when
        the DLL was loaded, while ``os.environ`` writes go through Python's own
        runtime. On Windows ``HELIOS_REQUIRE_GPU`` must therefore be set before the
        interpreter starts (``set HELIOS_REQUIRE_GPU=1`` in the shell, or the ``env:``
        block of a CI job); setting it from Python has no effect on this function.
        The same applies to ``HELIOS_NO_GPU``.

        Returns:
            True if a usable GPU is mandatory for this process

        Example:
            >>> from pyhelios import Global
            >>> Global.gpuRequiredByEnvironment()
            False
        """
        return global_wrapper.gpuRequiredByEnvironment()

    @staticmethod
    def requireGPUOrFail(context_message: str) -> None:
        """Raise if ``HELIOS_REQUIRE_GPU`` is set but no usable GPU was found.

        Call at the point code would otherwise skip for lack of a GPU. Does nothing
        unless ``HELIOS_REQUIRE_GPU`` is set. Setting both ``HELIOS_REQUIRE_GPU`` and
        ``HELIOS_NO_GPU`` is contradictory and is reported as such rather than letting
        one silently win.

        This function does not itself probe for hardware: reaching it is taken as
        proof the caller already determined no GPU was usable, so when
        ``HELIOS_REQUIRE_GPU`` is set it always raises.

        Args:
            context_message: Description of what was about to be skipped, included in
                the error message

        Raises:
            HeliosError: If a GPU is required by the environment but none was found

        Example:
            >>> from pyhelios import Global, RadiationModel
            >>> if not RadiationModel.probeAnyGPUBackend():
            ...     Global.requireGPUOrFail("radiation ray tracing")
        """
        global_wrapper.requireGPUOrFail(context_message)

    # =========================================================================
    # Process-wide random number generator (helios-core v1.3.85+)
    # =========================================================================

    @staticmethod
    def seedRandomGenerator(seed: int) -> None:
        """Seed the process-wide random number generator so a run can be reproduced.

        helios-core has two generators. Each ``Context`` owns one, seeded with
        :meth:`Context.seedRandomGenerator`, and it drives everything drawn through
        the Context: primitive placement helpers, ``Context.randu()``, LiDAR
        synthetic-scan noise, and the plant-architecture library's parameter
        sampling. The other is a single process-wide generator behind the free
        function ``helios::randu()``, which plug-in code uses where no Context is at
        hand: the LiDAR leaf-group and triangle index draws in
        ``calculateLeafArea()``, and the placement of berries within a grape
        cluster in PlantArchitecture. This method seeds that second generator.

        By default it is seeded from ``std::random_device`` and every run differs.
        Seeding it from Python makes those draws repeatable; seed the Context too
        if the rest of the simulation must repeat as well.

        The generator is shared by all threads and access to it is synchronized, so
        a seed set from any thread applies to every subsequent draw. Seeding fixes
        the sequence of values drawn, not which thread draws which value, so a
        parallel region that draws from it is still scheduling-dependent.

        Args:
            seed: Value used to seed the generator (unsigned 32-bit)

        Raises:
            ValueError: If ``seed`` is not an int in ``[0, 2**32 - 1]``
            RuntimeError: If the native library predates helios-core v1.3.85

        Example:
            >>> from pyhelios import Global
            >>> Global.seedRandomGenerator(42)
            >>> a = [Global.randu() for _ in range(3)]
            >>> Global.seedRandomGenerator(42)
            >>> assert a == [Global.randu() for _ in range(3)]
        """
        global_wrapper.seedGlobalRandomGenerator(seed)

    @staticmethod
    def randu(imin: Optional[int] = None, imax: Optional[int] = None):
        """Draw from the process-wide random number generator.

        With no arguments, returns a uniform float in ``[0, 1)``. With ``imin`` and
        ``imax``, returns a uniform integer over the **inclusive** range
        ``[imin, imax]``; every value, endpoints included, is equally likely, and if
        ``imin >= imax`` then ``imin`` is returned.

        This draws from the same generator that :meth:`seedRandomGenerator` seeds,
        not from any Context's generator; use :meth:`Context.randu` for that one.

        Args:
            imin: Lower bound of the integer range (inclusive). Must be given with ``imax``.
            imax: Upper bound of the integer range (inclusive). Must be given with ``imin``.

        Returns:
            A float in ``[0, 1)`` when called without arguments, otherwise an int in
            ``[imin, imax]``.

        Raises:
            ValueError: If exactly one of ``imin``/``imax`` is given, or either is not an int
            RuntimeError: If the native library predates helios-core v1.3.85
        """
        if imin is None and imax is None:
            return global_wrapper.globalRandu()
        if imin is None or imax is None:
            raise ValueError("randu() takes either no arguments or both imin and imax")
        return global_wrapper.globalRanduInt(imin, imax)

    @staticmethod
    def evaluateBetaDistributionCDF(theta: float, mu: float, nu: float) -> float:
        """Cumulative probability that a Beta-distributed leaf inclination is at most ``theta``.

        This is the CDF of the same Beta leaf-inclination distribution that
        PlantArchitecture's leaf angle distribution methods sample, in the same
        parameterization: ``nu`` is the first shape parameter of the underlying Beta
        variate and ``mu`` the second, so the mean inclination is
        ``(pi/2) * nu / (mu + nu)``.

        ``theta`` is measured from vertical and saturates outside ``[0, pi/2]``: a
        negative angle gives 0 and an angle at or above ``pi/2`` gives 1.

        Args:
            theta: Leaf inclination angle (radians)
            mu: First parameter of the Beta distribution; must be positive
            nu: Second parameter of the Beta distribution; must be positive

        Returns:
            Cumulative probability in ``[0, 1]``

        Raises:
            HeliosError: If ``mu`` or ``nu`` is not positive
            RuntimeError: If the native library predates helios-core v1.3.87

        Example:
            >>> from pyhelios import Global
            >>> import math
            >>> Global.evaluateBetaDistributionCDF(math.pi / 2, 1.0, 1.0)
            1.0
        """
        return global_wrapper.evaluateBetaDistributionCDF(theta, mu, nu)

    @staticmethod
    def invertBetaDistributionCDF(probability: float, mu: float, nu: float) -> float:
        """Leaf inclination angle at a given cumulative probability of the Beta distribution.

        The inverse of :meth:`evaluateBetaDistributionCDF`, useful for laying out a
        prescribed inclination distribution over a known number of leaves.

        Args:
            probability: Cumulative probability; must be in ``[0, 1]``
            mu: First parameter of the Beta distribution; must be positive
            nu: Second parameter of the Beta distribution; must be positive

        Returns:
            Leaf inclination angle (radians) in ``[0, pi/2]``

        Raises:
            HeliosError: If ``probability`` is outside ``[0, 1]``, or ``mu``/``nu`` is not positive
            RuntimeError: If the native library predates helios-core v1.3.87
        """
        return global_wrapper.invertBetaDistributionCDF(probability, mu, nu)

    @staticmethod
    def evaluateEllipsoidalAzimuthCDF(phi: float, e: float, phi0_degrees: float) -> float:
        """Cumulative probability that an ellipsoidally distributed leaf azimuth is at most ``phi``.

        The probability is measured from the ellipse rotation ``phi0_degrees``, and
        ``phi`` is wrapped into ``[0, 2*pi)``.

        Args:
            phi: Azimuth angle (radians)
            e: Eccentricity of the ellipsoidal distribution; must be in ``[0, 1]``
            phi0_degrees: Azimuthal rotation of the ellipse (degrees)

        Returns:
            Cumulative probability in ``[0, 1]``

        Raises:
            HeliosError: If ``e`` is outside ``[0, 1]``
            RuntimeError: If the native library predates helios-core v1.3.87
        """
        return global_wrapper.evaluateEllipsoidalAzimuthCDF(phi, e, phi0_degrees)

    @staticmethod
    def invertEllipsoidalAzimuthCDF(probability: float, e: float, phi0_degrees: float) -> float:
        """Leaf azimuth angle at a given cumulative probability of the ellipsoidal distribution.

        The inverse of :meth:`evaluateEllipsoidalAzimuthCDF`.

        Args:
            probability: Cumulative probability; must be in ``[0, 1]``
            e: Eccentricity of the ellipsoidal distribution; must be in ``[0, 1]``
            phi0_degrees: Azimuthal rotation of the ellipse (degrees)

        Returns:
            Azimuth angle (radians) in ``[0, 2*pi)``

        Raises:
            HeliosError: If ``probability`` or ``e`` is outside ``[0, 1]``
            RuntimeError: If the native library predates helios-core v1.3.87
        """
        return global_wrapper.invertEllipsoidalAzimuthCDF(probability, e, phi0_degrees)

    # =========================================================================
    # Blackbody Radiation (helios-core v1.3.90+)
    # =========================================================================

    @staticmethod
    def blackbodyBandFraction(wavelength_min_nm: float, wavelength_max_nm: float, temperature_K: float) -> float:
        """Fraction of a blackbody's total emissive power emitted between two wavelengths.

        This is the integral of Planck's law between the two wavelengths divided by its
        integral over all wavelengths (``sigma * T**4``). Multiplying the result by
        ``emissivity * sigma * T**4`` gives the in-band emitted flux of a gray surface,
        which is what a RadiationModel emission band added with wavelength bounds emits.

        Args:
            wavelength_min_nm: Lower wavelength bound (nm); must be >= 0
            wavelength_max_nm: Upper wavelength bound (nm); must be greater than ``wavelength_min_nm``
            temperature_K: Blackbody temperature (K); must be > 0

        Returns:
            Fraction of blackbody emissive power in the band, in ``[0, 1]``

        Raises:
            ValueError: If an argument is not a number
            HeliosError: If the bounds or the temperature are out of range
            RuntimeError: If the native library predates helios-core v1.3.90

        Example:
            >>> from pyhelios import Global
            >>> fraction = Global.blackbodyBandFraction(8000, 14000, 300.0)  # 8-14 um at 300 K
            >>> in_band_flux = 0.98 * 5.670374e-8 * 300.0**4 * fraction      # W/m^2
        """
        return global_wrapper.blackbodyBandFraction(wavelength_min_nm, wavelength_max_nm, temperature_K)

    @staticmethod
    def blackbodySpectralRadiance(wavelength_nm: float, temperature_K: float) -> float:
        """Spectral radiance of a blackbody (Planck's law).

        Its integral over all wavelengths is ``sigma * T**4 / pi``.

        Args:
            wavelength_nm: Wavelength (nm); must be > 0
            temperature_K: Blackbody temperature (K); must be > 0

        Returns:
            Spectral radiance in W/m^2/sr/nm

        Raises:
            ValueError: If an argument is not a number
            HeliosError: If the wavelength or the temperature is not positive
            RuntimeError: If the native library predates helios-core v1.3.90
        """
        return global_wrapper.blackbodySpectralRadiance(wavelength_nm, temperature_K)

    # =========================================================================
    # Single-channel PNG images (helios-core v1.3.95+)
    # =========================================================================

    @staticmethod
    def readPNGSingleChannel(filename: str):
        """Read a single-channel (grayscale) PNG image whose pixel values are integers, such as a class map.

        The values are returned exactly as stored, without scaling to ``[0, 1]``, so that
        each pixel can be used as an index (for example the class of a spectral texture,
        see :meth:`pyhelios.Context.setPrimitiveSpectralTexture`). The image must be 8-bit
        or 16-bit grayscale without transparency: color, indexed-color and
        grayscale-with-alpha images are rejected rather than converted, since converting
        them would change the values.

        Args:
            filename: Path to the PNG image

        Returns:
            A ``numpy.uint16`` array of shape ``(height, width)``, indexed ``[row, column]``
            with row 0 at the top of the image.

        Raises:
            ValueError: If ``filename`` is not a non-empty string
            HeliosError: If the file cannot be read or is not a single-channel 8- or 16-bit PNG
            RuntimeError: If the native library predates helios-core v1.3.95

        Example:
            >>> from pyhelios import Global
            >>> classes = Global.readPNGSingleChannel("leaf_classes.png")
            >>> height, width = classes.shape
        """
        if not isinstance(filename, (str, os.PathLike)) or not str(filename).strip():
            raise ValueError(f"filename must be a non-empty string, got {filename!r}")
        values, _, _ = global_wrapper.readPNGSingleChannel(os.fspath(filename))
        return values

    @staticmethod
    def writePNGSingleChannel(filename: str, width: int, height: int, pixel_values, bit_depth: int = 8) -> None:
        """Write a single-channel (grayscale) PNG image whose pixel values are integers, such as a class map.

        Args:
            filename: Path of the PNG image to write
            width: Image width in pixels
            height: Image height in pixels
            pixel_values: Value of each pixel, row-major with row 0 at the top of the image: a
                flat sequence of ``width * height`` integers or an array of shape
                ``(height, width)``. Values must be in ``[0, 65535]``.
            bit_depth: 8 (default) or 16. Every value must fit, so values above 255 need a
                bit depth of 16.

        Raises:
            ValueError: If an argument has the wrong type, ``pixel_values`` does not hold
                ``width * height`` integers in ``[0, 65535]``, or ``bit_depth`` is not 8 or 16
            HeliosError: If the file cannot be written, or a value does not fit in ``bit_depth``
            RuntimeError: If the native library predates helios-core v1.3.95

        Example:
            >>> import numpy as np
            >>> from pyhelios import Global
            >>> classes = np.ones((32, 64), dtype=np.uint16)
            >>> classes[:, 32:] = 2
            >>> Global.writePNGSingleChannel("leaf_classes.png", 64, 32, classes, 8)
        """
        import numpy as np
        if not isinstance(filename, (str, os.PathLike)) or not str(filename).strip():
            raise ValueError(f"filename must be a non-empty string, got {filename!r}")
        for name, v in (("width", width), ("height", height)):
            if isinstance(v, bool) or not isinstance(v, (int, np.integer)) or v <= 0:
                raise ValueError(f"{name} must be a positive int, got {v!r}")
        if isinstance(bit_depth, bool) or not isinstance(bit_depth, (int, np.integer)) or int(bit_depth) not in (8, 16):
            raise ValueError(f"bit_depth must be 8 or 16, got {bit_depth!r}")
        if isinstance(pixel_values, (str, bytes)):
            raise ValueError("pixel_values must be a sequence or array of integers")
        arr = np.asarray(pixel_values)
        if arr.size > 0 and arr.dtype.kind not in "iu":
            raise ValueError(f"pixel_values must hold integers, got dtype {arr.dtype}")
        if arr.size != int(width) * int(height):
            raise ValueError(f"pixel_values has {arr.size} values, but a {width} x {height} image needs "
                             f"{int(width) * int(height)}")
        if arr.size > 0 and (arr.min() < 0 or arr.max() > 0xFFFF):
            raise ValueError("pixel_values must be in [0, 65535]")
        global_wrapper.writePNGSingleChannel(os.fspath(filename), int(width), int(height), arr, int(bit_depth))

    # =========================================================================
    # Class map area fractions (helios-core v1.3.96+)
    # =========================================================================

    @staticmethod
    def classMapAreaFractions(classes, resolution, uv):
        """Fraction of a primitive's (u,v) polygon in each class of a class map, leaving out class 0.

        Class 0 marks transparent texels, so it is not reported. The texel convention is that of
        the radiation model and of texture masks: texture coordinate ``(u, v)`` falls in column
        ``floor((W-1) u)`` and row ``floor((H-1) (1-v))`` from the top, clamped to the image, so
        column ``i`` covers ``i/(W-1) <= u < (i+1)/(W-1)`` and the last column only ``u >= 1``
        (likewise for rows). Each texel's cell is clipped against the polygon, so a texel
        touching the polygon only along an edge or at a corner covers none of it.

        Args:
            classes: Class of each texel, as returned by :meth:`readPNGSingleChannel` or
                :meth:`pyhelios.Context.getSpectralTextureClassMap`: an integer array of shape
                ``(height, width)`` with row 0 at the top of the image, or a flat sequence of
                ``width * height`` integers in the same order. Values must be in ``[0, 65535]``.
            resolution: Width and height of the class map, as an ``int2``
            uv: ``(u, v)`` coordinates of the polygon's corners, in order, as a list of ``vec2``
                (three for a triangle, four for a patch)

        Returns:
            List of ``(class, fraction)`` tuples, one for each class with a nonzero area, in
            increasing order of class; empty if the polygon covers no texel of a class above 0.

        Raises:
            ValueError: If an argument has the wrong type, or ``classes`` does not hold
                ``width * height`` integers in ``[0, 65535]``
            HeliosError: If the native function rejects the arguments
            RuntimeError: If the native library predates helios-core v1.3.96

        Example:
            >>> import numpy as np
            >>> from pyhelios import Global
            >>> from pyhelios.types import int2, vec2
            >>> classes = np.ones((3, 3), dtype=np.uint16)
            >>> classes[:, 1:] = 2
            >>> Global.classMapAreaFractions(classes, int2(3, 3),
            ...     [vec2(0, 0), vec2(1, 0), vec2(1, 1), vec2(0, 1)])
            [(1, 0.5), (2, 0.5)]
        """
        import numpy as np
        from .wrappers.DataTypes import int2, vec2
        if not isinstance(resolution, int2):
            raise ValueError(f"resolution must be an int2, got {type(resolution).__name__}")
        width, height = int(resolution.x), int(resolution.y)
        if width <= 0 or height <= 0:
            raise ValueError(f"resolution must be positive in both dimensions, got ({width}, {height})")
        if isinstance(uv, (str, bytes)) or not hasattr(uv, "__iter__"):
            raise ValueError(f"uv must be a list of vec2, got {type(uv).__name__}")
        uv = list(uv)
        for i, corner in enumerate(uv):
            if not isinstance(corner, vec2):
                raise ValueError(f"uv[{i}] must be a vec2, got {type(corner).__name__}")
        if isinstance(classes, (str, bytes)):
            raise ValueError("classes must be a sequence or array of integers")
        arr = np.asarray(classes)
        if arr.size > 0 and arr.dtype.kind not in "iu":
            raise ValueError(f"classes must hold integers, got dtype {arr.dtype}")
        if arr.ndim == 2 and arr.shape != (height, width):
            raise ValueError(f"classes has shape {arr.shape}, but resolution ({width}, {height}) needs "
                             f"shape ({height}, {width})")
        if arr.size != width * height:
            raise ValueError(f"classes has {arr.size} values, but a {width} x {height} class map needs "
                             f"{width * height}")
        if arr.size > 0 and (arr.min() < 0 or arr.max() > 0xFFFF):
            raise ValueError("classes must be in [0, 65535]")
        uv_arr = np.array([[c.x, c.y] for c in uv], dtype=np.float32).reshape(-1, 2)
        return global_wrapper.classMapAreaFractions(arr, width, height, uv_arr)

    # =========================================================================
    # Normal and bump maps (helios-core v1.3.97+)
    # =========================================================================

    @staticmethod
    def decodeNormalMapImage(file: str, kind, strength: float = 1.0, flip_green: bool = False):
        """Decode a normal map or bump map image into unit tangent-space normals.

        A tangent-space normal map (``NORMAL_MAP_TANGENT_SPACE``) is read from an RGB(A) PNG
        (16-bit images are reduced to 8 bits) or a JPEG. Each channel c in [0,1] is decoded as
        2c-1 without sRGB decoding, z is clamped to be non-negative, the result is normalized,
        and its xy components are then scaled by ``strength`` before normalizing again (1 keeps
        the map as authored). With ``flip_green`` the y component is negated, for maps made in
        the DirectX convention. A grayscale image is rejected, since it is almost certainly a
        height map.

        A bump map (``NORMAL_MAP_BUMP``) is read from an 8- or 16-bit grayscale PNG at full
        precision, or from an RGB(A) PNG or JPEG as the luminance 0.2126R + 0.7152G + 0.0722B.
        Its values h in [0,1] are heights, and ``strength`` is the displacement, in texels, of
        the full range from 0 to 1. The gradient is taken with a normalized Scharr kernel with
        the edge texels repeated beyond the border, and the normal is
        normalize(-strength*dh/dcolumn, -strength*dh/drow_up, 1). ``flip_green`` is not allowed
        for bump maps.

        Unlike :meth:`Context.getNormalMapTexels`, the result is not cached.

        Args:
            file: Path to the image (PNG or JPEG)
            kind: ``NormalMapKind.NORMAL_MAP_TANGENT_SPACE`` or ``NormalMapKind.NORMAL_MAP_BUMP``
            strength: Finite value greater than zero (see above)
            flip_green: Negate the y component of a tangent-space normal map

        Returns:
            A :class:`NormalMapTexels`

        Raises:
            ValueError: If an argument has the wrong type
            HeliosError: If the image cannot be read or decoded with these arguments
            NotImplementedError: If the native library predates helios-core v1.3.97
        """
        from .normal_map import NormalMapTexels
        from .wrappers.DataTypes import NormalMapKind
        from .wrappers import UContextWrapper as context_wrapper
        if not isinstance(file, (str, os.PathLike)) or not os.fspath(file).strip():
            raise ValueError(f"file must be a non-empty path, got {file!r}")
        if isinstance(kind, bool) or not isinstance(kind, (int, NormalMapKind)):
            raise ValueError(f"kind must be a NormalMapKind, got {type(kind).__name__}")
        import numpy as np
        if isinstance(strength, (bool, np.bool_)) or not isinstance(strength, (int, float, np.integer, np.floating)):
            raise ValueError(f"strength must be a number, got {type(strength).__name__}")
        if not isinstance(flip_green, (bool, np.bool_)):
            raise ValueError(f"flip_green must be a bool, got {type(flip_green).__name__}")
        handle = context_wrapper.decodeNormalMapImageWrapper(os.fspath(file), int(kind), float(strength), bool(flip_green))
        return NormalMapTexels(handle)

    @staticmethod
    def classifyBumpImage(file: str):
        """Classify an image named in an OBJ material's bump line as a bump map or a normal map.

        Many exporters write tangent-space normal maps into ``map_Bump``. A grayscale image (a
        gray PNG, or red, green and blue equal in at least 99.5% of texels) is a bump map;
        otherwise the image is a normal map if its decoded normals point mostly along +z (mean z
        above 0.5 with mean x and y within 0.25 of zero). Any other image raises an error.

        Args:
            file: Path to the image (PNG or JPEG)

        Returns:
            ``NormalMapKind.NORMAL_MAP_BUMP`` or ``NormalMapKind.NORMAL_MAP_TANGENT_SPACE``

        Raises:
            HeliosError: If the image cannot be read or classified
            NotImplementedError: If the native library predates helios-core v1.3.97
        """
        from .wrappers.DataTypes import NormalMapKind
        from .wrappers import UContextWrapper as context_wrapper
        if not isinstance(file, (str, os.PathLike)) or not os.fspath(file).strip():
            raise ValueError(f"file must be a non-empty path, got {file!r}")
        return NormalMapKind(context_wrapper.classifyBumpImageWrapper(os.fspath(file)))

    @staticmethod
    def computeTangentFrame(p0, p1, p2, uv0, uv1, uv2):
        """Derivatives of position with respect to the texture coordinates over a triangle.

        For a triangle (or the first three corners of a patch) with corners p0, p1, p2 and
        texture coordinates uv0, uv1, uv2, computes dP/du and dP/dv, the directions in which the
        tangent-space +x and +y axes of a normal map point on the surface. Mirrored texture
        coordinates give a dP/dv on the other side of dP/du, as they should.

        Args:
            p0, p1, p2: Corners (vec3)
            uv0, uv1, uv2: Texture coordinates of the corners (vec2)

        Returns:
            ``(dPdu, dPdv)`` as vec3s, or None if the texture coordinates are degenerate
            (collinear) so that no frame exists

        Raises:
            ValueError: If an argument is not a vec3 / vec2
            NotImplementedError: If the native library predates helios-core v1.3.97
        """
        from .wrappers.DataTypes import vec2, vec3
        from .wrappers import UContextWrapper as context_wrapper
        for name, value in (("p0", p0), ("p1", p1), ("p2", p2)):
            if not isinstance(value, vec3):
                raise ValueError(f"{name} must be a vec3, got {type(value).__name__}")
        for name, value in (("uv0", uv0), ("uv1", uv1), ("uv2", uv2)):
            if not isinstance(value, vec2):
                raise ValueError(f"{name} must be a vec2, got {type(value).__name__}")
        result = context_wrapper.computeTangentFrameWrapper(
            [p0.x, p0.y, p0.z], [p1.x, p1.y, p1.z], [p2.x, p2.y, p2.z],
            [uv0.x, uv0.y], [uv1.x, uv1.y], [uv2.x, uv2.y])
        if result is None:
            return None
        return vec3(*result[0]), vec3(*result[1])

    @staticmethod
    def applyTangentSpaceNormal(tangent_normal, dPdu, dPdv, normal):
        """Transform a tangent-space normal into a surface direction.

        Builds an orthonormal frame as MikkTSpace (glTF, Blender) does: T is ``dPdu`` made
        perpendicular to ``normal`` and normalized, and B = +/- cross(normal, T), on the side of
        ``dPdv``. Returns normalize(n.x*T + n.y*B + n.z*normal). ``normal`` is the primitive's
        own unit normal (or a smoothed one), not one turned toward a viewer; the opposite face
        of a thin surface uses the negated result.

        Args:
            tangent_normal: Tangent-space normal (vec3), e.g. from :meth:`NormalMapTexels.sampleNearest`
            dPdu: Derivative of position with respect to u (vec3, see :meth:`computeTangentFrame`)
            dPdv: Derivative of position with respect to v (vec3)
            normal: Unit surface normal (vec3)

        Returns:
            Unit shading normal (vec3), or ``normal`` if dPdu is parallel to it or dPdv lies along T

        Raises:
            ValueError: If an argument is not a vec3
            NotImplementedError: If the native library predates helios-core v1.3.97
        """
        from .wrappers.DataTypes import vec3
        from .wrappers import UContextWrapper as context_wrapper
        for name, value in (("tangent_normal", tangent_normal), ("dPdu", dPdu), ("dPdv", dPdv), ("normal", normal)):
            if not isinstance(value, vec3):
                raise ValueError(f"{name} must be a vec3, got {type(value).__name__}")
        out = context_wrapper.applyTangentSpaceNormalWrapper(
            [tangent_normal.x, tangent_normal.y, tangent_normal.z], [dPdu.x, dPdu.y, dPdu.z],
            [dPdv.x, dPdv.y, dPdv.z], [normal.x, normal.y, normal.z])
        return vec3(*out)
