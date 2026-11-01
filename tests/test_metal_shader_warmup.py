"""The Metal shader cache warm-up that keeps forked GPU tests alive on a cold cache."""

import pytest

from tests.conftest import _warm_metal_shader_cache
from tests.test_radiation_model import skip_without_radiation_backend


@pytest.mark.native_only
@pytest.mark.macos_only
class TestMetalShaderWarmup:
    def test_warmup_script_runs_to_completion(self):
        """A warm-up that errors out would leave a cold cache to crash forked GPU tests."""
        skip_without_radiation_backend()
        result = _warm_metal_shader_cache()
        assert result is not None, "warm-up timed out"
        assert result.returncode == 0, result.stderr
