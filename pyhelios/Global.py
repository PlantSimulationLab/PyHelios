import os
from typing import Optional

from .wrappers import UGlobalWrapper as global_wrapper

class Global:
    """Process-wide helios-core functions that belong to no Context or plug-in model.

    The plug-in build root used to locate runtime assets is not settable here: it is a
    per-model construction argument (see ``WeberPennTree(context, build_directory)``),
    and helios-core exposes no global setter for it.
    """

    # =========================================================================
    # GPU Environment (helios-core v1.3.79+)
    # =========================================================================

    @staticmethod
    def gpuRequiredByEnvironment() -> bool:
        """Check whether a GPU is required by the ``HELIOS_REQUIRE_GPU`` environment variable.

        True when ``HELIOS_REQUIRE_GPU`` is set to any value other than ``"0"``.
        This is the counterpart to the ``HELIOS_NO_GPU`` veto: rather than changing
        what hardware probes report, it changes what a test does when no GPU is
        found, so a CI runner dedicated to GPU coverage cannot report success after
        silently skipping every GPU test.

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

        For gating PyHelios's own tests prefer the ``skip_or_fail_without_gpu``
        helper in ``conftest.py``, which reports a skip or failure to pytest directly
        and works in mock mode where no native library is loaded. It also reads the
        environment from Python, so unlike this function it works on Windows when
        the variable was set after the interpreter started — see
        :meth:`gpuRequiredByEnvironment` for why that difference exists.

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
