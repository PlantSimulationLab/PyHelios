"""Regression tests pinning the marshalling cost of hot-path APIs.

These assert on *mechanism* (how many times an expensive helper runs, whether a
bulk buffer is converted element-by-element) rather than on wall-clock time,
which would be flaky in CI. A timing assertion would pass or fail based on the
load of the machine; a call-count assertion fails only if the optimization is
actually reverted.
"""

import ctypes
import inspect
import numpy as np
import pytest

from pyhelios.validation.core import validate_input


@pytest.mark.cross_platform
class TestValidationSignatureCaching:
    """The @validate_* decorators must not rebuild inspect.signature per call.

    inspect.signature() is not cached by CPython -- it reconstructs the
    Signature and every Parameter on each call, measured at ~7us. The signature
    of a decorated function is fixed at decoration time, so recomputing it per
    call is pure overhead on the primitive-creation APIs (addPatch, addTriangle,
    addSphere, addTube, addBox), which users call in loops.
    """

    def test_signature_not_recomputed_per_call(self, monkeypatch):
        calls = []
        real_signature = inspect.signature

        def counting_signature(*args, **kwargs):
            calls.append(args[0] if args else None)
            return real_signature(*args, **kwargs)

        monkeypatch.setattr(
            "pyhelios.validation.core.inspect.signature", counting_signature
        )

        @validate_input(param_validators={"x": lambda v, **kw: None})
        def target(x, y=2):
            return x

        # Signature work belongs at decoration time; calls must add none.
        calls.clear()
        for _ in range(10):
            target(1)

        assert calls == [], (
            f"inspect.signature was called {len(calls)} times across 10 "
            f"invocations ({len(calls) / 10:.1f} per call); it must be computed "
            "once at decoration time and cached in the decorator closure."
        )

    def test_validation_still_rejects_and_coerces(self):
        """Caching the signature must not weaken validation or coercion."""

        def reject_negative(value, param_name=None, function_name=None):
            if value < 0:
                raise ValueError("negative")

        @validate_input(
            param_validators={"x": reject_negative},
            type_coercions={"y": lambda v, **kw: int(v)},
        )
        def target(x, y=0):
            return x, y

        # Positional and keyword binding must both still validate. This is the
        # repo's argument-type policy: positional args must not slip through.
        with pytest.raises(Exception):
            target(-1)
        with pytest.raises(Exception):
            target(x=-1)

        # Coercion must still rewrite the value, positionally and by keyword.
        assert target(1, "5") == (1, 5)
        assert target(1, y="5") == (1, 5)

        # Defaults for unprovided params must not be validated into existence.
        assert target(1) == (1, 0)


@pytest.mark.cross_platform
class TestBulkBufferReadback:
    """Bulk native buffers must be converted with numpy, not a list comp.

    getPrimitiveDataFloatArray returns a pointer into a contiguous float32
    buffer. Unboxing it with [float(ptr[i]) for i in range(n)] costs one Python
    float object per element and measured ~385x slower than np.frombuffer at
    1e6 elements -- discarding the entire point of the single-call bulk path.
    """

    def test_float_array_returns_without_per_element_boxing(self):
        from pyhelios.wrappers import UContextWrapper

        source = inspect.getsource(UContextWrapper.getPrimitiveDataFloatArray)
        assert "for i in range(" not in source, (
            "getPrimitiveDataFloatArray converts its result buffer with a "
            "per-element Python loop. Use np.ctypeslib.as_array(...).copy() / "
            "np.frombuffer(...), as ULiDARWrapper.py already does."
        )
        # A .tolist() here would undo the win by re-boxing every element, which
        # is what the removed getPrimitiveDataFloatArrayNumpy split existed for.
        assert ".tolist()" not in source, (
            "getPrimitiveDataFloatArray re-boxes its numpy result into a list; "
            "return the array and let callers vectorize."
        )

    def test_numpy_readback_matches_elementwise(self):
        """The numpy conversion must produce identical values to the loop."""
        n = 256
        buf = (ctypes.c_float * n)()
        for i in range(n):
            buf[i] = i * 0.5
        ptr = ctypes.cast(buf, ctypes.POINTER(ctypes.c_float))

        elementwise = [float(ptr[i]) for i in range(n)]
        vectorized = np.ctypeslib.as_array(ptr, shape=(n,)).copy()

        assert np.array_equal(np.asarray(elementwise, dtype=np.float32), vectorized)

    def test_offsets_returned_without_list_boxing(self):
        """Batch getters must not roundtrip their offset array through list()."""
        from pyhelios.wrappers import UContextWrapper

        for name in (
            "getBatchPrimitiveVertices",
            "getBatchPrimitiveTextureUV",
            "getBatchPrimitiveTextureFiles",
            "getBatchPrimitiveMaterialLabels",
        ):
            source = inspect.getsource(getattr(UContextWrapper, name))
            assert "list(offsets)" not in source, (
                f"{name} boxes its offset array via list(offsets); the caller "
                "immediately rebuilds it with np.array. Return a numpy array."
            )


@pytest.mark.native_only
class TestPositionalTypeRejection:
    """The argument-type policy must hold for POSITIONAL args on real methods.

    CLAUDE.md names this as the trap: context.addPatch(RGBcolor(1,0,0)) binds the
    color to `center` and would place a patch at (1,0,0) rather than raising.
    Caching the signature at decoration time changed the binding step, so the
    contract is pinned here against the actual decorated methods.

    These assert ValidationError specifically, not bare Exception: with the
    decorator removed the call still fails, but with an incidental AttributeError
    from deeper in the chain, which a broad `pytest.raises(Exception)` would
    accept and so would pass for the wrong reason.

    Note on what these actually pin: for a wrong *type* the type_coercions step
    (coerce_to_vec3/vec2) rejects the value before param_validators ever runs, so
    these go red when coercion is removed, not when the validators are. They pin
    the decorator's binding-and-coercion chain -- which is what the signature
    caching changed -- rather than the individual validator functions.
    """

    @pytest.fixture
    def ctx(self):
        from pyhelios import Context
        with Context() as c:
            yield c

    def test_addPatch_rejects_wrong_positional_type(self, ctx):
        from pyhelios.types import RGBcolor, vec3
        from pyhelios.validation.exceptions import ValidationError
        with pytest.raises(ValidationError):
            ctx.addPatch(RGBcolor(1, 0, 0))
        with pytest.raises(ValidationError):
            ctx.addPatch(center=RGBcolor(1, 0, 0))
        with pytest.raises(ValidationError):
            ctx.addPatch(vec3(0, 0, 0), vec3(1, 1, 1))

    def test_addTriangle_rejects_wrong_positional_type(self, ctx):
        from pyhelios.types import RGBcolor, vec3
        from pyhelios.validation.exceptions import ValidationError
        with pytest.raises(ValidationError):
            ctx.addTriangle(RGBcolor(1, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0))

    def test_addSphere_rejects_wrong_positional_type(self, ctx):
        from pyhelios.types import RGBcolor
        from pyhelios.validation.exceptions import ValidationError
        with pytest.raises(ValidationError):
            ctx.addSphere(RGBcolor(1, 0, 0), 1.0)

    def test_addBox_rejects_wrong_positional_type(self, ctx):
        from pyhelios.types import RGBcolor, vec3
        from pyhelios.validation.exceptions import ValidationError
        with pytest.raises(ValidationError):
            ctx.addBox(RGBcolor(1, 0, 0), vec3(1, 1, 1))

    def test_valid_positional_calls_still_succeed(self, ctx):
        """The rejection must not be so broad that correct calls break."""
        from pyhelios.types import vec2, vec3
        uuid = ctx.addPatch(vec3(0, 0, 0), vec2(1, 1))
        assert isinstance(uuid, int)
        uuid2 = ctx.addPatch([1, 2, 3], [1, 1])
        assert isinstance(uuid2, int)
