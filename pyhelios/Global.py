import os

from .wrappers import UGlobalWrapper as global_wrapper
from .validation.files import validate_directory_path

class Global:

    @staticmethod
    def set_build_plugin_root_directory(directory:str) -> None:
        # Validate directory path
        validated_path = validate_directory_path(
            directory, 
            must_exist=True, 
            create_if_missing=False,
            param_name="directory", 
            function_name="set_build_plugin_root_directory"
        )
        global_wrapper.setBuildPluginRootDirectory(validated_path)

    @staticmethod
    def get_build_plugin_root_directory() -> str:
        return global_wrapper.getBuildPluginRootDirectory()

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

