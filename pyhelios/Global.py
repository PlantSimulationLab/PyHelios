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
