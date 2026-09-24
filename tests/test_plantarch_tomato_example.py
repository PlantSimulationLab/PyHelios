"""
Runs docs/examples/plantarch_tomato_calibrated_sample.py, the Python port of a calibrated C++
tomato simulation, and checks the plant it grows.

The expected structure -- which leaves are detected on which day, with how many leaflets -- is
what the C++ program writes for the same parameters with plant-to-plant variation switched off.
Organ sizes depend on the random stream, which the dict-defined shoot types consume differently
from the C++ program, so they are checked for plausibility only.
"""

import importlib.util
import os

import pytest

from pyhelios.plugins.registry import get_plugin_registry

EXAMPLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "examples",
                       "plantarch_tomato_calibrated_sample.py")

# The fitted parameters, with the plant-to-plant spreads the port does not model set to zero.
THETA = {
    "phyllochron_min": 3.24206, "elongation_rate_max": 0.0599854, "internode_length_max": 0.0395302,
    "phyllotactic_angle_mean": 145, "phyllotactic_angle_sd": 33.7103, "petiole_pitch": 55.0863,
    "emergence_offset_days": -2.46803, "petiole_pitch_sd": 20.9338, "leaf_pitch_sd": 10.0132,
    "leaf_aspect_ratio": 0.507566, "leaf_aspect_ratio_sd": 0.0872268, "leaf_curvature": -0.260107,
    "leaf_curvature_sd": 0.0757306, "unique_prototypes": 8, "leaf_flexibility": 0.149887,
    "leaf_flexibility_aging": 11, "leaf_flexibility_aging_max": 6.77965, "leaf_flexibility_taper": 150,
    "petiole_flexibility": 0.143147, "petiole_flexibility_aging": 4.5131, "girth_area_factor": 5.00236,
    "internode_radius_initial": 0.0002, "petiole_radius": 0.00117515, "internode_length_max_sd": 0,
    "phyllochron_sd": 0, "emergence_offset_days_sd": 0, "hypocotyl_length": 0.021164,
    "cotyledon_prototype_scale": 0.0320833, "cotyledon_petiole_length": 0.0241521, "cotyledon_petiole_pitch": 60,
    "cotyledon_internode_length": 0.0202119, "phyllotactic_angle_node1": 154, "phyllotactic_angle_node2": 108,
    "internode_scale_late": 1, "internode_scale_age_days": 7.94909, "leaf_expansion_rate_max": 0.114731,
    "base_tilt_deg": 0, "base_tilt_sd": 0, "tortuosity": 12.9256, "leaves_per_petiole": 9,
    "leaflet_scale": 0.796273, "intercalary_leaflet_scale": 0.346864, "leaflet_offset": 0.19,
    "petiole_curvature": 0, "petiole_length": 0.133802, "prototype_scale": 0.0697297, "leaf_scale_node0": 0.85,
    "leaf_scale_nodes": 1.0,
}

# (day, track, leaflets) the C++ program records through day 11. Tracks 0 and 1 are the two
# cotyledons on shoot 0; tracks 100, 102, 104 are the first true leaves on the main stem (shoot 1).
EXPECTED_STRUCTURE = [
    (5, 0, 1), (5, 1, 1), (5, 100, 9),
    (7, 0, 1), (7, 1, 1), (7, 100, 9),
    (9, 0, 1), (9, 1, 1), (9, 100, 9), (9, 102, 9),
    (11, 0, 1), (11, 1, 1), (11, 100, 9), (11, 102, 9), (11, 104, 9),
]


def _load_example():
    if not os.path.exists(EXAMPLE):
        pytest.skip("Example script not available in wheel environment: plantarch_tomato_calibrated_sample.py")
    spec = importlib.util.spec_from_file_location("plantarch_tomato_calibrated_sample", EXAMPLE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.native_only
class TestCalibratedTomatoExample:

    def test_grows_the_same_leaves_as_the_cpp_program(self):
        if not get_plugin_registry().is_plugin_available('plantarchitecture'):
            pytest.skip("PlantArchitecture plugin not available")
        example = _load_example()
        columns = example.LEAF_COLUMNS
        rows = []
        # The library texture stands in for the C++ program's blade crop, which is not shipped with PyHelios.
        for _, _, day_rows in example.simulate(THETA, "TomatoLeaf_centered.png", seed=1, days=[1, 3, 5, 7, 9, 11]):
            rows.extend(dict(zip(columns, r)) for r in day_rows)

        assert [(r["day"], r["track"], r["leaflets"]) for r in rows] == EXPECTED_STRUCTURE
        for r in rows:
            assert float(r["area_cm2"]) > 0.0
            assert float(r["terminal_length_mm"]) >= 1000 * example.DETECTION_TERMINAL_LENGTH
            assert 0.0 < float(r["axis_length_mm"]) < 200.0
            assert 0.0 < float(r["insertion_pitch_deg"]) < 180.0
        cotyledon_height = float(rows[0]["attachment_height_mm"])
        assert cotyledon_height == pytest.approx(1000 * THETA["hypocotyl_length"], abs=0.05), (
            "the cotyledon node sits on a hypocotyl of the prescribed length")

    def test_rejects_plant_to_plant_variation(self):
        example = _load_example()
        with pytest.raises(ValueError, match="internode_length_max_sd"):
            next(example.simulate(dict(THETA, internode_length_max_sd=0.001), "TomatoLeaf_centered.png"))
