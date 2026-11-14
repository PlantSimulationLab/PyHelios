"""
Tests for the helios-core 1.3.97 Visualizer additions: rectangle read-back of the pixel-to-primitive
map and depth image, getPixelUUIDsAndDepth(), normal-map shading controls, and the stricter
getWindowPixelsRGB() that refuses to read back a frame that is missing or out of date.
"""

import inspect

import numpy as np
import pytest

from pyhelios import Context, Visualizer
from pyhelios.Visualizer import VisualizerError
from pyhelios.wrappers import UVisualizerWrapper as visualizer_wrapper
from pyhelios.wrappers.DataTypes import RGBcolor, vec2, vec3
from tests.test_visualizer import is_headless_environment


REGION_METHODS = ["getPixelUUIDs", "getDepthImage", "getPixelUUIDsAndDepth"]


@pytest.mark.cross_platform
class TestVisualizer1397Validation:
    """Pure-Python checks, run before any native call, so they hold in mock mode too."""

    @pytest.fixture
    def visualizer(self):
        instance = Visualizer.__new__(Visualizer)
        instance.visualizer = object()  # non-None so the init guard passes
        return instance

    @pytest.mark.parametrize("name", REGION_METHODS + ["enableNormalMaps", "disableNormalMaps", "areNormalMapsEnabled"])
    def test_methods_exist(self, name):
        assert callable(getattr(Visualizer, name, None)), f"{name}() is missing"

    @pytest.mark.parametrize("name", REGION_METHODS)
    def test_region_defaults_to_whole_image(self, name):
        assert inspect.signature(getattr(Visualizer, name)).parameters["region"].default is None

    @pytest.mark.parametrize("name", REGION_METHODS)
    @pytest.mark.parametrize("bad", [
        "0,0,4,4", 5, (0, 0, 4), (0, 0, 4, 4, 1), {0, 1, 2, 3},
    ])
    def test_region_must_be_four_values(self, visualizer, name, bad):
        with pytest.raises(TypeError, match="region must be a tuple"):
            getattr(visualizer, name)(bad)

    @pytest.mark.parametrize("name", REGION_METHODS)
    @pytest.mark.parametrize("bad", [
        (0.0, 0, 4, 4), (0, 0, 4.5, 4), (0, "0", 4, 4), (True, 0, 4, 4), (0, 0, 4, None),
    ])
    def test_region_values_must_be_integers(self, visualizer, name, bad):
        # Positionally and by keyword: both must reach the same check.
        with pytest.raises(TypeError, match="must be an integer"):
            getattr(visualizer, name)(bad)
        with pytest.raises(TypeError, match="must be an integer"):
            getattr(visualizer, name)(region=bad)

    @pytest.mark.parametrize("name", REGION_METHODS)
    def test_region_rejects_negative_corner(self, visualizer, name):
        with pytest.raises(ValueError, match="non-negative"):
            getattr(visualizer, name)(region=(-1, 0, 4, 4))
        with pytest.raises(ValueError, match="non-negative"):
            getattr(visualizer, name)((0, -3, 4, 4))

    @pytest.mark.parametrize("name", REGION_METHODS)
    @pytest.mark.parametrize("size", [(0, 4), (4, 0), (-2, 4)])
    def test_region_rejects_empty_size(self, visualizer, name, size):
        with pytest.raises(ValueError, match="at least 1"):
            getattr(visualizer, name)(region=(0, 0) + size)

    @pytest.mark.parametrize("name", REGION_METHODS)
    def test_region_rejects_values_beyond_uint_range(self, visualizer, name):
        # 2**32 would wrap to 0 through ctypes.c_uint; it must be rejected, not truncated.
        with pytest.raises(ValueError, match="far larger"):
            getattr(visualizer, name)(region=(0, 0, 2**32, 4))

    def test_region_accepts_numpy_integers_and_lists(self):
        assert Visualizer._validate_pixel_region([np.int64(1), np.uint32(2), 3, 4]) == (1, 2, 3, 4)
        assert all(type(v) is int for v in Visualizer._validate_pixel_region((np.int32(0), 0, 1, 1)))

    @pytest.mark.parametrize("flag, call", [
        ("_ANNOTATION_1397_FUNCTIONS_AVAILABLE", lambda v: visualizer_wrapper.get_pixel_uuids_region(v, 0, 0, 1, 1)),
        ("_ANNOTATION_1397_FUNCTIONS_AVAILABLE", lambda v: visualizer_wrapper.get_depth_image_region(v, 0, 0, 1, 1)),
        ("_ANNOTATION_1397_FUNCTIONS_AVAILABLE", lambda v: visualizer_wrapper.get_pixel_uuids_and_depth(v)),
        ("_ANNOTATION_1397_FUNCTIONS_AVAILABLE", lambda v: visualizer_wrapper.get_pixel_uuids_and_depth_region(v, 0, 0, 1, 1)),
        ("_NORMAL_MAP_FUNCTIONS_AVAILABLE", lambda v: visualizer_wrapper.enable_normal_maps(v)),
        ("_NORMAL_MAP_FUNCTIONS_AVAILABLE", lambda v: visualizer_wrapper.disable_normal_maps(v)),
        ("_NORMAL_MAP_FUNCTIONS_AVAILABLE", lambda v: visualizer_wrapper.are_normal_maps_enabled(v)),
    ])
    def test_wrappers_raise_rebuild_message_when_symbols_are_missing(self, monkeypatch, flag, call):
        monkeypatch.setattr(visualizer_wrapper, flag, False)
        with pytest.raises(NotImplementedError, match=r"v1\.3\.97.*build_helios"):
            call(object())

    @pytest.mark.parametrize("name", ["enableNormalMaps", "disableNormalMaps", "areNormalMapsEnabled"])
    def test_normal_map_methods_propagate_not_implemented(self, visualizer, monkeypatch, name):
        monkeypatch.setattr(visualizer_wrapper, "_NORMAL_MAP_FUNCTIONS_AVAILABLE", False)
        with pytest.raises(NotImplementedError, match=r"v1\.3\.97"):
            getattr(visualizer, name)()

    def test_get_window_pixels_rgb_documents_plot_update_requirement(self):
        doc = Visualizer.getWindowPixelsRGB.__doc__ or ""
        assert "plotUpdate" in doc and "1.3.97" in doc


@pytest.mark.native_only
@pytest.mark.skipif(is_headless_environment(), reason="Skipping visualizer tests in headless environment")
class TestVisualizer1397Native:
    """Native behavior of the 1.3.97 read-back and shading additions."""

    @pytest.fixture
    def scene(self):
        # Two patches at different depths, off-centre, so a rectangle holds background, both
        # primitives and two depths, and an orientation error would change its contents.
        with Context() as context:
            near = context.addPatch(center=vec3(-0.3, 0.2, 0.5), size=vec2(0.6, 0.5))
            far = context.addPatch(center=vec3(0.35, -0.15, 0.0), size=vec2(0.8, 0.7))
            with Visualizer(200, 150, headless=True) as visualizer:
                visualizer.buildContextGeometry(context)
                visualizer.setCameraPosition(vec3(0, 0, 5), vec3(0, 0, 0))
                yield context, visualizer, (near, far)

    @staticmethod
    def _region(visualizer):
        width, height = visualizer.getFramebufferSize()
        return (width // 4, height // 5, width // 2, (height * 3) // 5)

    def test_pixel_uuids_region_equals_sub_block_of_full_image(self, scene):
        _, visualizer, (near, far) = scene
        full, width, height = visualizer.getPixelUUIDs()
        x0, y0, w, h = self._region(visualizer)

        block, bw, bh = visualizer.getPixelUUIDs(region=(x0, y0, w, h))

        assert (bw, bh) == (w, h)
        assert block.dtype == np.uint32 and block.shape == (w * h,)
        expected = full.reshape(height, width)[y0:y0 + h, x0:x0 + w]
        assert {0, near + 1, far + 1} <= set(np.unique(expected).tolist()), "the rectangle must hold both patches and background"
        np.testing.assert_array_equal(block.reshape(h, w), expected)

    def test_depth_image_region_equals_sub_block_of_full_image(self, scene):
        _, visualizer, _ = scene
        full, width, height = visualizer.getDepthImage()
        x0, y0, w, h = self._region(visualizer)

        block, bw, bh = visualizer.getDepthImage(region=(x0, y0, w, h))

        assert (bw, bh) == (w, h)
        assert block.dtype == np.float32 and block.shape == (w * h,)
        expected = full.reshape(height, width)[y0:y0 + h, x0:x0 + w]
        assert len(np.unique(expected)) >= 3, "the rectangle must hold background and two depths"
        np.testing.assert_array_equal(block.reshape(h, w), expected)

    def test_pixel_uuids_and_depth_match_the_separate_calls(self, scene):
        _, visualizer, _ = scene
        pixels, width, height = visualizer.getPixelUUIDs()
        depth, _, _ = visualizer.getDepthImage()

        both_pixels, both_depth, bw, bh = visualizer.getPixelUUIDsAndDepth()

        assert (bw, bh) == (width, height)
        assert both_pixels.dtype == np.uint32 and both_depth.dtype == np.float32
        np.testing.assert_array_equal(both_pixels, pixels)
        np.testing.assert_array_equal(both_depth, depth)

    def test_pixel_uuids_and_depth_region_equals_sub_blocks(self, scene):
        _, visualizer, _ = scene
        pixels, depth, width, height = visualizer.getPixelUUIDsAndDepth()
        x0, y0, w, h = self._region(visualizer)

        block_pixels, block_depth, bw, bh = visualizer.getPixelUUIDsAndDepth((x0, y0, w, h))

        assert (bw, bh) == (w, h)
        np.testing.assert_array_equal(block_pixels.reshape(h, w), pixels.reshape(height, width)[y0:y0 + h, x0:x0 + w])
        np.testing.assert_array_equal(block_depth.reshape(h, w), depth.reshape(height, width)[y0:y0 + h, x0:x0 + w])

    def test_single_pixel_region_at_the_bottom_right_corner(self, scene):
        _, visualizer, _ = scene
        full, width, height = visualizer.getPixelUUIDs()
        block, bw, bh = visualizer.getPixelUUIDs(region=(width - 1, height - 1, 1, 1))
        assert (bw, bh) == (1, 1)
        assert block[0] == full[-1]

    @pytest.mark.parametrize("name", REGION_METHODS)
    def test_region_outside_framebuffer_raises(self, scene, name):
        _, visualizer, _ = scene
        width, height = visualizer.getFramebufferSize()
        with pytest.raises(VisualizerError, match="does not lie within"):
            getattr(visualizer, name)(region=(width - 4, 0, 5, 1))
        with pytest.raises(VisualizerError, match="does not lie within"):
            getattr(visualizer, name)(region=(0, height, 1, 1))

    def test_normal_maps_toggle_round_trip(self, scene):
        _, visualizer, _ = scene
        assert visualizer.areNormalMapsEnabled() is True, "normal maps are on by default"
        visualizer.disableNormalMaps()
        assert visualizer.areNormalMapsEnabled() is False
        visualizer.enableNormalMaps()
        assert visualizer.areNormalMapsEnabled() is True

    def test_get_window_pixels_rgb_raises_before_any_render(self, scene):
        _, visualizer, _ = scene
        with pytest.raises(VisualizerError, match="plotUpdate"):
            visualizer.getWindowPixelsRGB()

    def test_get_window_pixels_rgb_raises_after_the_view_changes(self, scene):
        _, visualizer, _ = scene
        visualizer.plotUpdate()
        visualizer.getWindowPixelsRGB()
        visualizer.setBackgroundColor(RGBcolor(0.2, 0.3, 0.4))
        with pytest.raises(VisualizerError, match="plotUpdate"):
            visualizer.getWindowPixelsRGB()
        visualizer.plotUpdate()
        pixels, width, height = visualizer.getWindowPixelsRGB()
        assert len(pixels) == 3 * width * height

    def test_get_window_pixels_rgb_reads_the_frame_left_by_print_window(self, scene, tmp_path):
        _, visualizer, _ = scene
        visualizer.printWindow(str(tmp_path / "frame.jpeg"))
        pixels, width, height = visualizer.getWindowPixelsRGB()
        assert len(pixels) == 3 * width * height

    def test_hidden_primitive_reappears_after_show(self, scene):
        context, visualizer, (near, _) = scene
        assert near + 1 in visualizer.getPixelUUIDs()[0]
        context.hidePrimitive(near)
        assert near + 1 not in visualizer.getPixelUUIDs()[0]
        context.showPrimitive(near)
        assert near + 1 in visualizer.getPixelUUIDs()[0]

    def test_read_back_survives_a_second_visualizer(self, scene):
        context, visualizer, (near, far) = scene
        before, _, _ = visualizer.getPixelUUIDs()
        with Visualizer(120, 90, headless=True) as other:
            other.buildContextGeometry(context)
            other.getPixelUUIDs()
        after, _, _ = visualizer.getPixelUUIDs()
        np.testing.assert_array_equal(after, before)
