"""
Regression tests for context-lifetime and silent-failure bugs.

Each test in this module corresponds to a specific defect and MUST fail if its
fix is reverted. See "Regression Tests Must Fail Before the Fix" in CLAUDE.md.

The use-after-free tests run their repro in a subprocess and assert on the exit
code: before the fix these crashed the interpreter with SIGSEGV, which would take
down the test runner rather than report a failure if run in-process.
"""

import os
import signal
import subprocess
import sys
import textwrap

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pyhelios import Context
from pyhelios.plugins.registry import get_plugin_registry
from pyhelios.types import RGBAcolor, RGBcolor, vec2, vec3, vec4
from pyhelios.validation.datatypes import (
    validate_rgb_color,
    validate_vec2,
    validate_vec3,
)
from pyhelios.validation.exceptions import ValidationError

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def run_in_subprocess(source: str) -> subprocess.CompletedProcess:
    """Run a snippet in a fresh interpreter and return the completed process.

    PYTHONPATH is pinned to the repo root: another PyHelios checkout installed on
    this machine can otherwise shadow the working tree and silently test the wrong
    code (it reports plugins as unavailable rather than exercising the fix).
    """
    env = dict(os.environ, PYTHONPATH=REPO_ROOT)
    return subprocess.run(
        [sys.executable, '-c', textwrap.dedent(source)],
        capture_output=True,
        text=True,
        timeout=300,
        cwd=REPO_ROOT,
        env=env,
    )


def assert_did_not_segfault(result: subprocess.CompletedProcess) -> None:
    """Assert the child process was not killed by SIGSEGV."""
    assert result.returncode != -signal.SIGSEGV and result.returncode != 139, (
        "process died with SIGSEGV (use-after-free regression)\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


def plugin_available(name: str) -> bool:
    return get_plugin_registry().is_plugin_available(name)


def graphics_context_unavailable(result: subprocess.CompletedProcess) -> bool:
    """True if the child failed because it could not create a GL context at all.

    plugin_available('visualizer') only reports whether the plugin was compiled
    in; it says nothing about whether the machine can actually open a graphics
    context. CI runners have the plugin but no display, so Visualizer() raises
    before the code under test is ever reached. That is an inapplicable
    environment, not a regression -- but it must be distinguished narrowly, so
    that a genuine render failure still fails the test. Callers must check for
    SIGSEGV first: the use-after-free this guards reproduces as a crash, and a
    crash is a failure in every environment.

    Both spellings are matched: the Python wrapper raises "Failed to create
    Visualizer", while the native error that now propagates through it says
    "Failed to create visualizer: ... Failed to initialize GLFW". Matching only
    one of them makes a headless runner look like a render regression.
    """
    stderr = result.stderr
    return (
        "Failed to create Visualizer" in stderr
        or "Failed to create visualizer" in stderr
        or "Failed to initialize GLFW" in stderr
    )


def radiation_backend_unavailable(result: subprocess.CompletedProcess) -> bool:
    """True if the child failed because no ray tracing backend could initialize.

    The radiation counterpart of graphics_context_unavailable: the plugin can be
    compiled in and still have no usable backend at runtime. The RadiationModel
    constructor then raises before the code under test runs.

    This surfaces differently per platform, so match the constructor's own
    failure message rather than any single cause -- mirroring the predicate in
    test_radiation_model.py::TestCameraExposureSparseSubject._radiation_model:

      - macOS wheels: "No compatible GPU backend found" (MoltenVK reports
        VK_ERROR_EXTENSION_NOT_PRESENT and every backend probe fails).
      - Windows wheels: OSError WinError 0xc06d007e, raised when the radiation
        DLL's OptiX/CUDA dependencies are absent in the wheel test environment.
        This one carries no backend-specific text at all, only the wrapper's
        "Failed to initialize RadiationModel" prefix.

    Callers must check for SIGSEGV first -- see graphics_context_unavailable.
    """
    return ("No compatible GPU backend found" in result.stderr
            or "Failed to initialize RadiationModel" in result.stderr)


@pytest.mark.native_only
@pytest.mark.cross_platform
class TestPluginModelOutlivingContext:
    """Plugin models must not dereference a Context that has been destroyed."""

    @pytest.mark.skipif(not plugin_available('energybalance'),
                        reason="energybalance plugin not built")
    def test_energybalance_after_context_exit_raises_not_segfault(self):
        result = run_in_subprocess("""
            from pyhelios import Context
            from pyhelios.EnergyBalance import EnergyBalanceModel
            from pyhelios.types import vec3
            ctx = Context()
            ctx.addPatch(center=vec3(0, 0, 0))
            eb = EnergyBalanceModel(ctx)
            ctx.__exit__(None, None, None)
            try:
                eb.run()
            except RuntimeError as e:
                print("RAISED_RUNTIMEERROR")
                raise SystemExit(0)
            print("NO_ERROR_RAISED")
            raise SystemExit(2)
        """)
        assert_did_not_segfault(result)
        assert "RAISED_RUNTIMEERROR" in result.stdout, (
            f"expected RuntimeError, got:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    @pytest.mark.skipif(not plugin_available('energybalance'),
                        reason="energybalance plugin not built")
    def test_model_escaping_context_with_block_raises_not_segfault(self):
        """The natural failure mode: model outlives the Context's `with` block."""
        result = run_in_subprocess("""
            from pyhelios import Context
            from pyhelios.EnergyBalance import EnergyBalanceModel
            from pyhelios.types import vec3
            with Context() as ctx:
                ctx.addPatch(center=vec3(0, 0, 0))
                eb = EnergyBalanceModel(ctx)
            try:
                eb.run()
            except RuntimeError:
                print("RAISED_RUNTIMEERROR")
                raise SystemExit(0)
            print("NO_ERROR_RAISED")
            raise SystemExit(2)
        """)
        assert_did_not_segfault(result)
        assert "RAISED_RUNTIMEERROR" in result.stdout, (
            f"expected RuntimeError, got:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    @pytest.mark.skipif(not plugin_available('radiation'),
                        reason="radiation plugin not built")
    def test_radiationmodel_after_context_exit_raises_not_segfault(self):
        result = run_in_subprocess("""
            from pyhelios import Context, RadiationModel
            from pyhelios.types import vec3
            ctx = Context()
            ctx.addPatch(center=vec3(0, 0, 0))
            rad = RadiationModel(ctx)
            rad.addRadiationBand("SW")
            ctx.__exit__(None, None, None)
            try:
                rad.updateGeometry()
            except RuntimeError:
                print("RAISED_RUNTIMEERROR")
                raise SystemExit(0)
            print("NO_ERROR_RAISED")
            raise SystemExit(2)
        """)
        assert_did_not_segfault(result)
        if radiation_backend_unavailable(result):
            pytest.skip("no working radiation backend on this machine")
        assert "RAISED_RUNTIMEERROR" in result.stdout, (
            f"expected RuntimeError, got:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_live_context_is_not_falsely_rejected(self):
        """The liveness guard must not reject a Context that is still alive."""
        from pyhelios.Context import check_context_alive
        with Context() as ctx:
            ctx.addPatch(center=vec3(0, 0, 0))
            check_context_alive(ctx, "TestModel")  # must not raise


@pytest.mark.native_only
@pytest.mark.cross_platform
class TestVisualizerHoldsContextReference:
    """Visualizer must keep the Context alive; it derefs the pointer at render time."""

    @pytest.mark.skipif(not plugin_available('visualizer'),
                        reason="visualizer plugin not built")
    def test_temporary_context_survives_until_render(self):
        """A Context passed as a temporary must not be collected before plotUpdate."""
        result = run_in_subprocess("""
            from pyhelios import Context
            from pyhelios.Visualizer import Visualizer
            from pyhelios.types import vec3

            def make_scene():
                c = Context()
                c.addPatch(center=vec3(0, 0, 0))
                return c

            vis = Visualizer(400, 300, headless=True)
            vis.buildContextGeometry(make_scene())  # refcount would hit 0 here
            vis.plotUpdate()
            print("SURVIVED")
        """)
        assert_did_not_segfault(result)
        if graphics_context_unavailable(result):
            pytest.skip("no graphics context available on this machine")
        assert "SURVIVED" in result.stdout, (
            f"render failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_build_context_geometry_retains_context_reference(self, monkeypatch):
        """The retained reference itself, checked without opening a GL context.

        The subprocess test above is the end-to-end proof, but it can only run
        where a graphics context exists -- which excludes every CI runner and
        most developer machines. This drives buildContextGeometry against a stub
        wrapper so the actual fix (Visualizer._context = context) is covered
        everywhere. Delete that assignment and this fails via the weakref.
        """
        import gc
        import weakref

        from pyhelios.Visualizer import Visualizer
        # 'pyhelios.Visualizer' is the module; the Visualizer name re-exported
        # from the package is the class and would shadow it here.
        visualizer_module = sys.modules['pyhelios.Visualizer']

        monkeypatch.setattr(visualizer_module.visualizer_wrapper,
                            'build_context_geometry',
                            lambda _vis, _ctx: None)

        vis = Visualizer.__new__(Visualizer)
        vis.visualizer = object()

        # The Context is created and dropped inside the helper, so the only
        # reference that can outlive this line is the one buildContextGeometry
        # retained. gc.collect() makes the negative case deterministic rather
        # than relying on refcounting alone.
        collected = weakref.ref(self._load_temporary_scene(vis))
        gc.collect()

        assert getattr(vis, '_context', None) is not None, (
            "buildContextGeometry must retain the Context; the native visualizer "
            "stores a raw Context* and derefs it later at render time"
        )
        assert collected() is not None, (
            "Context was garbage collected while the visualizer still held its "
            "raw pointer -- this is the use-after-free that segfaults at render"
        )

    @staticmethod
    def _load_temporary_scene(vis):
        """Build geometry from a Context that goes out of scope on return."""
        context = Context()
        context.addPatch(center=vec3(0, 0, 0))
        vis.buildContextGeometry(context)
        return context


@pytest.mark.native_only
@pytest.mark.cross_platform
class TestLiDARCollisionDetectionContext:
    """LiDARCloud must retain the Context bound to native collision detection."""

    # NOTE: there is deliberately no "temporary Context survives" crash test here.
    # The native CollisionDetection does store the Context* for its lifetime, but no
    # PyHelios-exposed method dereferences that stored pointer: the GPU toggles only
    # touch the cloud, and every geometry method (syntheticScan, calculateLeafArea,
    # ...) takes a fresh Context per call. A crash test would therefore pass with and
    # without the fix, proving nothing. The retained reference in
    # initializeCollisionDetection is defence against that changing upstream; the
    # reachable defect is the silently-ignored second Context, covered below.

    @pytest.mark.skipif(not plugin_available('lidar'), reason="lidar plugin not built")
    def test_second_different_context_is_rejected(self):
        """C++ ignores a re-init with a new Context; that must not pass silently."""
        from pyhelios.LiDARCloud import LiDARCloud

        first = Context()
        first.addPatch(center=vec3(0, 0, 0))
        second = Context()
        second.addPatch(center=vec3(1, 1, 1))

        cloud = LiDARCloud()
        cloud.initializeCollisionDetection(first)
        with pytest.raises(RuntimeError, match="already initialized with a different Context"):
            cloud.initializeCollisionDetection(second)

    @pytest.mark.skipif(not plugin_available('lidar'), reason="lidar plugin not built")
    def test_reinitializing_with_same_context_is_allowed(self):
        from pyhelios.LiDARCloud import LiDARCloud

        ctx = Context()
        ctx.addPatch(center=vec3(0, 0, 0))
        cloud = LiDARCloud()
        cloud.initializeCollisionDetection(ctx)
        cloud.initializeCollisionDetection(ctx)  # must not raise


@pytest.mark.native_only
@pytest.mark.cross_platform
class TestPlantQuerySentinel:
    """Plant state queries return -1.0f on failure; that must raise, not be returned."""

    @pytest.mark.skipif(not plugin_available('plantarchitecture'),
                        reason="plantarchitecture plugin not built")
    @pytest.mark.parametrize("method", ["getPlantHeight", "getPlantAge", "getPlantLeafArea"])
    def test_invalid_plant_id_raises_instead_of_returning_sentinel(self, method):
        from pyhelios.PlantArchitecture import PlantArchitecture, PlantArchitectureError

        ctx = Context()
        plantarch = PlantArchitecture(ctx)
        with pytest.raises((PlantArchitectureError, RuntimeError)) as excinfo:
            getattr(plantarch, method)(99999)
        # Guard against passing for the wrong reason: the failure must come from
        # the native error state, not e.g. an AttributeError on a renamed method.
        assert "-1" not in str(excinfo.value) or "ERROR" in str(excinfo.value)

    @pytest.mark.skipif(not plugin_available('plantarchitecture'),
                        reason="plantarchitecture plugin not built")
    @pytest.mark.slow
    def test_valid_plant_returns_real_measurements(self):
        """The errcheck must not break the success path."""
        from pyhelios.PlantArchitecture import PlantArchitecture

        ctx = Context()
        plantarch = PlantArchitecture(ctx)
        plantarch.loadPlantModelFromLibrary("bean")
        plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), 10.0)

        assert plantarch.getPlantHeight(plant_id) > 0.0
        assert plantarch.getPlantAge(plant_id) > 0.0
        assert plantarch.getPlantLeafArea(plant_id) > 0.0


@pytest.mark.cross_platform
class TestStrictDatatypeValidation:
    """Validators must check concrete types, not just attribute presence."""

    def test_vec4_rejected_where_vec3_expected(self):
        with pytest.raises(ValidationError):
            validate_vec3(vec4(1, 2, 3, 4), "origin", "test")

    def test_vec3_rejected_where_vec2_expected(self):
        with pytest.raises(ValidationError):
            validate_vec2(vec3(1, 2, 3), "size", "test")

    def test_rgba_rejected_where_rgb_expected(self):
        """RGBAcolor has .r/.g/.b, so a hasattr check would silently drop alpha."""
        with pytest.raises(ValidationError):
            validate_rgb_color(RGBAcolor(1, 0, 0, 0.5), "color", "test")

    def test_correct_types_still_accepted(self):
        validate_vec3(vec3(1, 2, 3), "origin", "test")
        validate_vec2(vec2(1, 2), "size", "test")
        validate_rgb_color(RGBcolor(1, 0, 0), "color", "test")

    @pytest.mark.native_only
    @pytest.mark.skipif(not plugin_available('weberpenntree'),
                        reason="weberpenntree plugin not built")
    def test_weberpenntree_rejects_vec4_origin_consistently(self):
        """Both build paths must reject a vec4 the same way.

        buildTree sized its buffer with len(origin) and silently planted the tree
        at a truncated position; buildTreeWithScale hardcoded 3 and raised
        IndexError. Same input, two different outcomes.
        """
        from pyhelios import WeberPennTree, WPTType

        ctx = Context()
        wpt = WeberPennTree(ctx)
        with pytest.raises(ValidationError):
            wpt.buildTree(WPTType.LEMON, origin=vec4(5, 5, 5, 5))
        with pytest.raises(ValidationError):
            wpt.buildTree(WPTType.LEMON, origin=vec4(5, 5, 5, 5), scale=2.0)


@pytest.mark.native_only
@pytest.mark.cross_platform
class TestPrimitiveInfoDoesNotSwallowFailures:
    """getPrimitiveInfo must not report a native failure as missing data."""

    def test_native_failure_propagates(self):
        ctx = Context()
        uuid = ctx.addPatch(center=vec3(0, 0, 0))

        original = Context.getPrimitiveSolidFraction

        def boom(self, _uuid):
            raise RuntimeError("simulated native failure")

        Context.getPrimitiveSolidFraction = boom
        try:
            with pytest.raises(RuntimeError, match="simulated native failure"):
                ctx.getPrimitiveInfo(uuid)
        finally:
            Context.getPrimitiveSolidFraction = original

    def test_missing_function_in_old_build_is_tolerated(self):
        """NotImplementedError (older library) must still degrade gracefully."""
        ctx = Context()
        uuid = ctx.addPatch(center=vec3(0, 0, 0))

        original = Context.getPrimitiveTextureUV

        def not_built(self, _uuid):
            raise NotImplementedError("texture functions not available")

        Context.getPrimitiveTextureUV = not_built
        try:
            info = ctx.getPrimitiveInfo(uuid)
        finally:
            Context.getPrimitiveTextureUV = original

        assert info.texture_uv is None
        # One unavailable getter must not suppress the others.
        assert info.solid_fraction is not None


@pytest.mark.cross_platform
class TestContextDelDuringInterpreterShutdown:
    """`Context.__del__` must stay silent when it runs during interpreter shutdown.

    At shutdown CPython tears down module globals and the import machinery. A
    Context that is still alive is finalized in that window, so
    `context_wrapper.destroyContext` may already be gone. The original code
    called it unguarded and then ran `import warnings` inside the `except`
    handler -- but importing is no longer possible at that point, so the handler
    itself raised. CPython printed an "Exception ignored in:
    <function Context.__del__>" traceback pointing at the *import* line, hiding
    the original error. See GitHub issue #4.

    This is teardown noise rather than a leak: the OS reclaims the native
    allocation at process exit either way. The bug is the misleading traceback.
    """

    def test_del_during_shutdown_emits_no_traceback(self):
        """Reproduces issue #4's traceback deterministically.

        `atexit` handlers run *before* the final GC pass that finalizes
        surviving objects, so clearing the module global and the `warnings`
        module there puts `__del__` in the same torn-down state it sees during a
        real shutdown. Simulating this by clearing the global at normal runtime
        does NOT reproduce the bug: the `except` handler's `import warnings`
        still succeeds and it degrades to a harmless UserWarning.
        """
        result = run_in_subprocess("""
            import atexit
            import sys
            from pyhelios import Context
            from pyhelios.types import vec2, vec3

            # 'pyhelios.Context' is the module; the `Context` name re-exported
            # from the package is the class and would shadow it here.
            context_module = sys.modules['pyhelios.Context']

            context = Context()
            context.addPatch(center=vec3(0, 0, 0), size=vec2(10, 10))

            def simulate_shutdown_teardown():
                context_module.context_wrapper = None
                sys.modules['warnings'] = None

            atexit.register(simulate_shutdown_teardown)
            print("SCRIPT_COMPLETED")
        """)
        assert_did_not_segfault(result)
        assert "SCRIPT_COMPLETED" in result.stdout, (
            f"script did not run\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert "Exception ignored in" not in result.stderr, (
            "Context.__del__ leaked a traceback during interpreter shutdown:\n"
            f"{result.stderr}"
        )

    def test_del_reports_failures_normally_outside_shutdown(self):
        """The shutdown hardening must not silence genuine runtime failures.

        Outside of shutdown a broken destroyContext should still surface as a
        warning -- a bare `except: pass` would make this test fail.
        """
        result = run_in_subprocess("""
            import sys
            import warnings
            from pyhelios import Context

            context_module = sys.modules['pyhelios.Context']

            class BrokenWrapper:
                def destroyContext(self, ptr):
                    raise RuntimeError("simulated native failure")

            context = Context()
            context_module.context_wrapper = BrokenWrapper()

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                context.__del__()
                if any("simulated native failure" in str(w.message) for w in caught):
                    print("WARNED")
        """)
        assert_did_not_segfault(result)
        assert "WARNED" in result.stdout, (
            "a real __del__ failure was silently swallowed\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
