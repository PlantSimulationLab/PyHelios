"""
Tests for SoilTransportModel integration
"""

import math
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from pyhelios import (
    Context,
    HeliosError,
    SoilTransportModel,
    SoilTransportModelError,
    SoilProperties,
    SolverParameters,
    RootDistributionParams,
    WeibullRootParameters,
    SoilModel,
    KWeighting,
    NonlinearMethod,
    SolverType,
    SoilColorMode,
    SoilMeasurement,
    SoilRegion,
    getSoilPropertiesFromTexture,
    toModifiedVanGenuchten,
    getAvailableSoilTextures,
    isSoilTextureAvailable,
)
from pyhelios.types import vec3, RGBcolor

REPO_ROOT = Path(__file__).resolve().parent.parent

# Carsel & Parrish (1988) class averages for loam, as stored in the native texture library
LOAM = dict(theta_r=0.078, theta_s=0.43, alpha=3.6, n=1.56, K_s=2.89e-6)

USDA_TEXTURES = {"sand", "loamy_sand", "sandy_loam", "loam", "silt", "silt_loam", "sandy_clay_loam",
                 "clay_loam", "silty_clay_loam", "sandy_clay", "silty_clay", "clay"}


def vg_theta(h, p):
    """Standard van Genuchten water content, computed independently of the plugin."""
    if h >= 0:
        return p["theta_s"]
    m = 1.0 - 1.0 / p["n"]
    se = (1.0 + abs(p["alpha"] * h) ** p["n"]) ** (-m)
    return p["theta_r"] + (p["theta_s"] - p["theta_r"]) * se


def vg_K(h, p):
    """Standard van Genuchten-Mualem conductivity, computed independently of the plugin."""
    m = 1.0 - 1.0 / p["n"]
    se = (1.0 + abs(p["alpha"] * h) ** p["n"]) ** (-m)
    return p["K_s"] * math.sqrt(se) * (1.0 - (1.0 - se ** (1.0 / m)) ** m) ** 2


# ----------------------------------------------------------------------------------------------
# Tests that need no native library
# ----------------------------------------------------------------------------------------------

@pytest.mark.cross_platform
class TestSoilTransportMetadata:
    """Test plugin metadata and registration"""

    def test_plugin_metadata_exists(self):
        from pyhelios.config.plugin_metadata import get_plugin_metadata

        metadata = get_plugin_metadata('soiltransport')
        assert metadata is not None
        assert metadata.name == 'soiltransport'
        assert metadata.description
        assert 'createSoilTransportModel' in metadata.test_symbols
        assert metadata.gpu_required is False
        assert set(metadata.platforms) == {'windows', 'linux', 'macos'}

    def test_plugin_in_registry(self):
        from pyhelios.config.plugin_metadata import PLUGIN_METADATA
        assert 'soiltransport' in PLUGIN_METADATA

    def test_plugin_in_integrated_list(self):
        """Plugin is part of the default build."""
        build_script = REPO_ROOT / 'build_scripts' / 'build_helios.py'
        if not build_script.exists():
            # Wheel test environments copy only tests/ into an isolated directory
            pytest.skip("Build script not available in wheel testing environment "
                        "(build_scripts/build_helios.py not found)")
        integrated = build_script.read_text().split('INTEGRATED_PLUGINS = [')[1].split(']')[0]
        assert 'soiltransport' in integrated


@pytest.mark.cross_platform
class TestSoilTransportInterface:
    """Test the Python interface without requiring the native library"""

    def test_class_structure(self):
        for method in [
            'defineSoilDomain', 'setGridResolution', 'setColumnResolution', 'setColumnGrid', 'initializeDomain',
            'setSoilProperties', 'setSoilPropertiesFromTexture', 'setInitialCondition',
            'setInitialConditionHydrostatic', 'setTopBoundaryFlux', 'setSurfaceEvaporation',
            'setTopBoundaryPressure', 'setBottomBoundaryFreeDrainage', 'setBottomBoundaryPressure',
            'setBottomBoundaryFlux', 'addSurfaceEmitter', 'clearSurfaceEmitters', 'enableRootUptake',
            'setRootDistribution', 'setRootDistributionWeibull', 'setRootRadialConductivity',
            'setRootWaterStressParameters', 'setTranspiration', 'setSolverType', 'enableHorizontalCoupling',
            'setSolverParameters', 'enableGPU', 'disableGPU', 'isGPUEnabled', 'isGPUAvailable', 'run',
            'getSoilWaterPotential', 'getWaterContent', 'getPressureHead', 'addSensor', 'recordSensors',
            'getSensorCount', 'getSensorData', 'getSensorTimes', 'getSensorPosition', 'getSensorQuantity',
            'clearSensorData', 'writeSensorData', 'getLastSubstepCount', 'resetSolverStats', 'solverPicardOuter',
            'solverNewtonOuter', 'solverPicardGmres', 'solverNewtonGmres', 'getTimestep',
            'getSolverIterationCount', 'resetSolverIterationCount', 'getTotalWaterStorage',
            'getCumulativeBoundaryInflux', 'getMassBalanceResidual', 'resetMassBalance',
            'getCumulativeRootUptake', 'getRootUptakeFlux', 'addSoilVisualization', 'updateSoilVisualization',
            'enableMessages', 'disableMessages', '__enter__', '__exit__', '__del__',
        ]:
            assert hasattr(SoilTransportModel, method), method

    def test_error_class(self):
        assert issubclass(SoilTransportModelError, HeliosError)

    def test_requires_context(self):
        with pytest.raises(TypeError, match="Context"):
            SoilTransportModel("not a context")

    def test_enum_values_match_cpp(self):
        """Enum values are passed to C++ as integers, so they must match SoilUtils.h."""
        assert [int(v) for v in SoilModel] == [0, 1, 2, 3]
        assert int(KWeighting.DEFAULT) == -1
        assert int(KWeighting.HARMONIC) == 3 and int(KWeighting.UPSTREAM_KR) == 4
        assert int(NonlinearMethod.PICARD) == 0 and int(NonlinearMethod.NEWTON_ANALYTIC) == 5
        assert [int(v) for v in SolverType] == [0, 1, 2]
        assert [int(v) for v in SoilColorMode] == [0, 1, 2]
        assert [int(v) for v in SoilMeasurement] == [0, 1]
        assert [int(v) for v in SoilRegion] == [0, 1]

    def test_struct_defaults_match_cpp(self):
        p = SoilProperties()
        assert (p.theta_r, p.theta_s, p.alpha, p.n, p.K_s) == (0.045, 0.43, 14.5, 2.68, 8.25e-5)
        assert p.model == SoilModel.VAN_GENUCHTEN and p.h_e == 0.0 and p.kr_spline_start == 1.0

        s = SolverParameters()
        assert s.max_picard_iterations == 20 and s.picard_tolerance == 1e-5
        assert s.dt_min == 0.01 and s.dt_max == 3600.0 and s.horizontal_coupling_interval == 1
        assert s.nonlinear_method == NonlinearMethod.NEWTON_ANALYTIC and s.K_weighting == KWeighting.DEFAULT
        assert s.enable_gravity and s.substep_on_failure and not s.adaptive_dt and not s.bdf2
        assert s.dt_target_rel_change == 0.03 and s.picard_omega == 1.0 and s.num_threads == 0

        r = RootDistributionParams()
        assert (r.z_max, r.r_max, r.z_star, r.r_star, r.pz, r.pr, r.total_root_length) == \
               (1.5, 1.0, 0.3, 0.0, 1.0, 1.0, 1000.0)

        w = WeibullRootParameters()
        assert (w.z_max, w.shape_z, w.scale_z, w.radial, w.r_max, w.shape_r, w.scale_r) == \
               (1.5, 1.5, 0.3, False, 1.0, 1.0, 0.5)

    def test_named_constructors(self):
        p = SoilProperties.modifiedVanGenuchten(0.05, 0.4, 3.0, 1.5, 1e-6, -0.02)
        assert p.model == SoilModel.MODIFIED_VAN_GENUCHTEN and p.h_e == -0.02
        g = SoilProperties.gardner(0.05, 0.4, 3.0, 1e-6)
        assert g.model == SoilModel.GARDNER and g.n == 2.0
        lin = SoilProperties.linear(0.05, 0.4, 3.0, 1e-6)
        assert lin.model == SoilModel.LINEAR
        assert SoilProperties.vanGenuchten(0.05, 0.4, 3.0, 2.0, 1e-6).m() == pytest.approx(0.5)

    @pytest.mark.parametrize("struct, field, bad", [
        (SoilProperties, "theta_s", "0.4"),
        (SoilProperties, "alpha", float("nan")),
        (SoilProperties, "model", 2),
        (SolverParameters, "adaptive_dt", 1),
        (SolverParameters, "max_picard_iterations", -1),
        (SolverParameters, "max_picard_iterations", 2.5),
        (SolverParameters, "nonlinear_method", 5),
        (SolverParameters, "dt_max", float("inf")),
        (RootDistributionParams, "z_max", None),
        (WeibullRootParameters, "radial", 1),
    ])
    def test_struct_validation_rejects_bad_fields(self, struct, field, bad):
        obj = struct()
        setattr(obj, field, bad)
        with pytest.raises(ValueError, match=field):
            obj.validate("test")

    @pytest.mark.parametrize("model", [SoilModel.GARDNER, SoilModel.LINEAR])
    def test_texture_library_rejects_models_without_a_library(self, model):
        # The native call silently returns van Genuchten properties for LINEAR, so Python must reject it.
        with pytest.raises(ValueError, match=model.name):
            getSoilPropertiesFromTexture("loam", model)

    def test_ctypes_structs_match_c_header(self):
        """Field names, order and types of the ctypes mirrors match native/include/pyhelios_wrapper_soiltransport.h."""
        import ctypes
        from pyhelios.wrappers import USoilTransportWrapper as w
        header = REPO_ROOT / "native" / "include" / "pyhelios_wrapper_soiltransport.h"
        if not header.exists():
            pytest.skip("native/include not available in this test environment")
        c_types = {"float": ctypes.c_float, "int": ctypes.c_int, "unsigned int": ctypes.c_uint}
        structs = {}
        for body, name in re.findall(r"typedef struct \{(.*?)\} (\w+);", header.read_text(), flags=re.S):
            fields = []
            for line in body.splitlines():
                m = re.match(r"\s*(unsigned int|float|int)\s+(\w+);", line)
                if m:
                    fields.append((m.group(2), c_types[m.group(1)]))
            structs[name] = fields
        for c_name, mirror in [("PyHeliosSoilProperties", w.CSoilProperties),
                               ("PyHeliosSoilSolverParameters", w.CSolverParameters),
                               ("PyHeliosRootDistributionParams", w.CRootDistributionParams),
                               ("PyHeliosWeibullRootParameters", w.CWeibullRootParameters)]:
            assert structs[c_name] == list(mirror._fields_), c_name

    def test_dataclass_fields_match_ctypes_mirrors(self):
        """The dataclass -> ctypes conversions rely on matching field names (and order for the root structs)."""
        from pyhelios.wrappers import USoilTransportWrapper as w
        from dataclasses import fields as dc_fields
        for dataclass_type, mirror in [(SoilProperties, w.CSoilProperties), (SolverParameters, w.CSolverParameters),
                                       (RootDistributionParams, w.CRootDistributionParams),
                                       (WeibullRootParameters, w.CWeibullRootParameters)]:
            assert [f.name for f in dc_fields(dataclass_type)] == [f[0] for f in mirror._fields_], dataclass_type.__name__

    def test_solver_parameters_to_c_round_trip(self):
        values = SolverParameters(max_picard_iterations=7, enable_gravity=False, substep_on_failure=False,
                                  picard_tolerance=2e-4, dt_min=0.5, dt_max=99.0, horizontal_coupling_interval=3,
                                  C_regularization=3e-9, K_min=4e-10, picard_omega=0.6,
                                  K_weighting=KWeighting.UPSTREAM_KR, anderson_depth=2,
                                  nonlinear_method=NonlinearMethod.NGS_FAS, num_threads=5, bdf2=True,
                                  adaptive_dt=True, dt_target_rel_change=0.05, dt_safety=0.8, dt_growth_max=1.5,
                                  dt_reduction_min=0.2, dt_failure_factor=0.4)
        c = values._to_c()
        for name, _ in c._fields_:
            assert getattr(c, name) == pytest.approx(float(getattr(values, name)), rel=1e-6), name


# ----------------------------------------------------------------------------------------------
# Native tests
# ----------------------------------------------------------------------------------------------

@pytest.fixture
def context(check_native_library):
    context = Context()
    yield context
    context.__exit__(None, None, None)


@pytest.fixture
def soil(context):
    model = SoilTransportModel(context)
    model.disableMessages()
    yield model
    model.__exit__(None, None, None)


def column(soil, nz=20, depth=1.0):
    """A single 1 m x 1 m column of the given depth (SOLVER_1D)."""
    soil.defineSoilDomain(vec3(0, 0, 0), vec3(1, 1, depth))
    soil.setColumnResolution(nz)


def block3d(soil, n=(6, 6, 12), extent=(1.0, 1.0, 1.0)):
    """A small full-3D block with its origin at (0, 0, 0)."""
    soil.defineSoilDomain(vec3(0, 0, 0), vec3(*extent))
    soil.setGridResolution(*n)
    soil.setSolverType(SolverType.SOLVER_3D)


@pytest.mark.native_only
class TestSoilLibrary:
    """Soil property library (free functions)"""

    def test_available_textures(self):
        assert set(getAvailableSoilTextures()) == USDA_TEXTURES

    def test_is_texture_available(self):
        assert isSoilTextureAvailable("loam")
        assert not isSoilTextureAvailable("peat")

    def test_loam_values(self):
        p = getSoilPropertiesFromTexture("loam")
        for name, value in LOAM.items():
            assert getattr(p, name) == pytest.approx(value, rel=1e-6), name
        assert p.model == SoilModel.VAN_GENUCHTEN

    def test_unknown_texture_raises(self):
        with pytest.raises(SoilTransportModelError, match="peat"):
            getSoilPropertiesFromTexture("peat")

    def test_modified_model_truncates_standard_curves(self):
        """theta_s and K_s become the standard theta and K at h_e (-2 cm by default)."""
        p = getSoilPropertiesFromTexture("loam", SoilModel.MODIFIED_VAN_GENUCHTEN)
        assert p.model == SoilModel.MODIFIED_VAN_GENUCHTEN
        assert p.h_e == pytest.approx(-0.02)
        assert p.theta_r == pytest.approx(LOAM["theta_r"]) and p.n == pytest.approx(LOAM["n"])
        assert p.theta_s == pytest.approx(vg_theta(-0.02, LOAM), rel=1e-5)
        assert p.K_s == pytest.approx(vg_K(-0.02, LOAM), rel=1e-4)

    def test_modified_model_keep_saturated_values(self):
        p = getSoilPropertiesFromTexture("loam", SoilModel.MODIFIED_VAN_GENUCHTEN, match_standard_curves=False)
        assert p.theta_s == pytest.approx(LOAM["theta_s"]) and p.K_s == pytest.approx(LOAM["K_s"])

    def test_to_modified_van_genuchten(self):
        p = toModifiedVanGenuchten(SoilProperties.vanGenuchten(**LOAM), -0.05)
        assert p.model == SoilModel.MODIFIED_VAN_GENUCHTEN and p.h_e == pytest.approx(-0.05)
        assert p.theta_s == pytest.approx(vg_theta(-0.05, LOAM), rel=1e-5)
        assert p.K_s == pytest.approx(vg_K(-0.05, LOAM), rel=1e-4)

    def test_library_argument_types(self):
        with pytest.raises(ValueError):
            getSoilPropertiesFromTexture("loam", 2)
        with pytest.raises(ValueError):
            toModifiedVanGenuchten("loam")

    def test_gpu_unavailable_when_hidden(self, monkeypatch):
        monkeypatch.setenv("HELIOS_NO_GPU", "1")
        assert SoilTransportModel.isGPUAvailable() is False


@pytest.mark.native_only
class TestSoilTransportFunctionality:
    """Plugin behavior with the native library"""

    def test_create_and_destroy(self, context):
        model = SoilTransportModel(context)
        assert model.getNativePtr() is not None
        model.__exit__(None, None, None)
        assert model.getNativePtr() is None

    def test_default_soil_is_loam(self, soil):
        column(soil)
        soil.setInitialCondition(-1.0)
        assert soil.getWaterContent(vec3(0.5, 0.5, -0.5)) == pytest.approx(vg_theta(-1.0, LOAM), rel=1e-4)

    def test_uniform_initial_condition(self, soil):
        column(soil)
        soil.setSoilPropertiesFromTexture("sand")
        soil.setInitialCondition(-0.5)
        assert soil.getPressureHead(vec3(0.5, 0.5, -0.3)) == pytest.approx(-0.5)
        sand = getSoilPropertiesFromTexture("sand")
        expected = vg_theta(-0.5, {k: getattr(sand, k) for k in LOAM})
        assert soil.getWaterContent(vec3(0.5, 0.5, -0.3)) == pytest.approx(expected, rel=1e-4)

    def test_hydrostatic_initial_condition(self, soil):
        column(soil, nz=20, depth=2.0)
        soil.setInitialConditionHydrostatic(1.0)
        # head = height below the water table (positive) or above it (negative), at cell centres
        assert soil.getPressureHead(vec3(0.5, 0.5, -0.25)) == pytest.approx(-0.75, abs=0.051)
        assert soil.getPressureHead(vec3(0.5, 0.5, -1.55)) == pytest.approx(0.55, abs=0.051)

    def test_custom_soil_properties(self, soil):
        column(soil)
        props = SoilProperties.vanGenuchten(0.05, 0.35, 2.0, 1.8, 1e-5)
        soil.setSoilProperties(props)
        soil.setInitialCondition(0.0)
        assert soil.getWaterContent(vec3(0.5, 0.5, -0.5)) == pytest.approx(0.35, rel=1e-5)

    def test_column_soil_properties(self, soil):
        soil.defineSoilDomain(vec3(0, 0, 0), vec3(2, 1, 1))
        soil.setGridResolution(2, 1, 10)
        soil.setSoilProperties(1, 0, SoilProperties.vanGenuchten(0.05, 0.30, 2.0, 1.8, 1e-5))
        soil.setInitialCondition(0.0)
        assert soil.getWaterContent(vec3(0.5, 0.5, -0.5)) == pytest.approx(LOAM["theta_s"], rel=1e-5)
        assert soil.getWaterContent(vec3(1.5, 0.5, -0.5)) == pytest.approx(0.30, rel=1e-5)

    def test_column_soil_properties_by_keyword(self, soil):
        soil.defineSoilDomain(vec3(0, 0, 0), vec3(2, 2, 1))
        soil.setColumnGrid(2, 2)
        soil.setColumnResolution(10)
        soil.setSoilProperties(i=1, j=1, props=SoilProperties.vanGenuchten(0.05, 0.30, 2.0, 1.8, 1e-5))
        soil.setInitialCondition(0.0)
        assert soil.getWaterContent(vec3(1.5, 1.5, -0.5)) == pytest.approx(0.30, rel=1e-5)
        assert soil.getWaterContent(vec3(0.5, 1.5, -0.5)) == pytest.approx(LOAM["theta_s"], rel=1e-5)

    def test_uniform_soil_properties_by_keyword(self, soil):
        column(soil)
        soil.setSoilProperties(props=SoilProperties.vanGenuchten(0.05, 0.33, 2.0, 1.8, 1e-5))
        soil.setInitialCondition(0.0)
        assert soil.getWaterContent(vec3(0.5, 0.5, -0.5)) == pytest.approx(0.33, rel=1e-5)

    def test_air_entry_head_reaches_native(self, soil):
        """With the modified model the soil is saturated between h_e and 0, unlike the standard model."""
        column(soil)
        soil.setSoilProperties(SoilProperties.modifiedVanGenuchten(**LOAM, h_e=-0.1))
        soil.setInitialCondition(-0.05)
        assert soil.getWaterContent(vec3(0.5, 0.5, -0.5)) == pytest.approx(LOAM["theta_s"], rel=1e-5)

    def test_non_physical_properties_rejected(self, soil):
        column(soil)
        with pytest.raises(SoilTransportModelError):
            soil.setSoilProperties(SoilProperties.vanGenuchten(0.5, 0.4, 3.0, 1.5, 1e-6))  # theta_r > theta_s

    @pytest.mark.parametrize("model", [SoilModel.GARDNER, SoilModel.LINEAR])
    def test_texture_on_model_rejects_models_without_a_library(self, soil, model):
        with pytest.raises(ValueError, match=model.name):
            soil.setSoilPropertiesFromTexture("loam", model)

    def test_modified_texture_on_model(self, soil):
        column(soil)
        soil.setSoilPropertiesFromTexture("loam", SoilModel.MODIFIED_VAN_GENUCHTEN)
        soil.setInitialCondition(-0.01)  # above h_e = -2 cm: saturated at the truncated theta_s
        assert soil.getWaterContent(vec3(0.5, 0.5, -0.5)) == pytest.approx(vg_theta(-0.02, LOAM), rel=1e-5)

    def test_grid_cell_count_overflow_rejected(self, soil):
        with pytest.raises(ValueError, match="cells"):
            soil.setGridResolution(65536, 65536, 2)
        soil.setColumnResolution(2)
        with pytest.raises(ValueError, match="cells"):
            soil.setColumnGrid(65536, 65536)
        soil.setColumnGrid(65536, 16384)  # 2^31 cells with nz = 2
        with pytest.raises(ValueError, match="cells"):
            soil.setColumnResolution(4)  # 2^32 cells

    def test_column_soil_properties_outside_grid_raises(self, soil):
        column(soil)
        with pytest.raises(SoilTransportModelError, match="outside"):
            soil.setSoilProperties(3, 0, SoilProperties())

    def test_infiltration_conserves_water_1d(self, soil):
        column(soil, nz=40)
        soil.setInitialCondition(-1.0)
        soil.setTopBoundaryFlux(2e-6)
        soil.setBottomBoundaryFlux(0.0)
        storage0 = soil.getTotalWaterStorage()
        for _ in range(6):
            soil.run(600.0)
        assert soil.getTotalWaterStorage() - storage0 == pytest.approx(2e-6 * 3600.0, rel=1e-3)
        # the wetting front has raised the near-surface water content
        assert soil.getWaterContent(vec3(0.5, 0.5, -0.0125)) > vg_theta(-1.0, LOAM) + 0.01

    def test_bottom_flux_drains_column(self, soil):
        column(soil)
        soil.setInitialCondition(-0.2)
        soil.setTopBoundaryFlux(0.0)
        soil.setBottomBoundaryFlux(1e-7)  # positive = out of the domain
        storage0 = soil.getTotalWaterStorage()
        soil.run(3600.0)
        assert storage0 - soil.getTotalWaterStorage() == pytest.approx(1e-7 * 3600.0, rel=1e-3)

    def test_pressure_boundaries_wet_the_ends(self, soil):
        column(soil)
        soil.setInitialCondition(-2.0)
        soil.setTopBoundaryPressure(0.0)
        soil.setBottomBoundaryPressure(0.0)
        for _ in range(12):
            soil.run(3600.0)
        dry = vg_theta(-2.0, LOAM)
        assert soil.getWaterContent(vec3(0.5, 0.5, -0.025)) > dry + 0.05
        assert soil.getWaterContent(vec3(0.5, 0.5, -0.975)) > dry + 0.05

    def test_free_drainage_loses_water(self, soil):
        column(soil)
        soil.setInitialCondition(-0.1)
        soil.setTopBoundaryFlux(0.0)
        soil.setBottomBoundaryFreeDrainage()
        storage0 = soil.getTotalWaterStorage()
        soil.run(3600.0)
        assert soil.getTotalWaterStorage() < storage0

    def test_3d_mass_balance(self, soil):
        block3d(soil)
        soil.setInitialCondition(-1.0)
        soil.setTopBoundaryFlux(2e-6)
        soil.setBottomBoundaryFreeDrainage()
        storage0 = soil.getTotalWaterStorage()
        for _ in range(10):
            soil.run(60.0)
        influx = soil.getCumulativeBoundaryInflux()
        assert soil.getTotalWaterStorage() - storage0 == pytest.approx(influx, rel=1e-6)
        assert abs(soil.getMassBalanceResidual()) < 1e-9
        soil.resetMassBalance()
        assert soil.getCumulativeBoundaryInflux() == 0.0

    def test_mass_balance_needs_3d(self, soil):
        column(soil)
        soil.setInitialCondition(-1.0)
        with pytest.raises(SoilTransportModelError, match="3D"):
            soil.getCumulativeBoundaryInflux()
        with pytest.raises(SoilTransportModelError, match="3D"):
            soil.getMassBalanceResidual()

    def test_emitter_adds_its_discharge(self, soil):
        block3d(soil)
        soil.setInitialCondition(-1.0)
        soil.setTopBoundaryFlux(0.0)
        soil.setBottomBoundaryFlux(0.0)
        soil.addSurfaceEmitter(0.5, 0.5, 1e-7, 0.2)
        storage0 = soil.getTotalWaterStorage()
        soil.run(1800.0)
        assert soil.getTotalWaterStorage() - storage0 == pytest.approx(1e-7 * 1800.0, rel=1e-4)
        assert soil.getWaterContent(vec3(0.5, 0.5, -0.04)) > soil.getWaterContent(vec3(0.05, 0.05, -0.04))

        soil.clearSurfaceEmitters()
        storage1 = soil.getTotalWaterStorage()
        soil.run(1800.0)
        assert soil.getTotalWaterStorage() == pytest.approx(storage1, rel=1e-6)

    def test_emitter_outside_domain_raises(self, soil):
        block3d(soil)
        with pytest.raises(SoilTransportModelError, match="outside"):
            soil.addSurfaceEmitter(5.0, 0.5, 1e-7)

    def test_point_query_outside_domain_raises(self, soil):
        column(soil)
        soil.setInitialCondition(-1.0)
        with pytest.raises(SoilTransportModelError):
            soil.getWaterContent(vec3(0.5, 0.5, 0.5))

    def test_quasi_3d_spreads_laterally(self, context):
        """An emitter wets the neighboring column only when horizontal coupling is on."""
        results = {}
        for solver in (SolverType.SOLVER_1D, SolverType.SOLVER_QUASI_3D):
            with SoilTransportModel(context) as soil:
                soil.disableMessages()
                soil.defineSoilDomain(vec3(0, 0, 0), vec3(0.6, 0.2, 0.5))
                soil.setGridResolution(3, 1, 20)
                soil.setSolverType(solver)
                if solver == SolverType.SOLVER_QUASI_3D:
                    soil.enableHorizontalCoupling(1)
                soil.setInitialCondition(-1.0)
                soil.setTopBoundaryFlux(0.0)
                soil.setBottomBoundaryFlux(0.0)
                soil.addSurfaceEmitter(0.1, 0.1, 2e-8)
                for _ in range(6):
                    soil.run(600.0)
                results[solver] = soil.getWaterContent(vec3(0.3, 0.1, -0.0125))
        assert results[SolverType.SOLVER_QUASI_3D] > results[SolverType.SOLVER_1D] + 1e-4

    def test_surface_evaporation(self, soil):
        block3d(soil)
        soil.setInitialCondition(-0.1)
        soil.setTopBoundaryFlux(0.0)
        evaporation = soil.setSurfaceEvaporation(1e-7)
        # wet soil evaporates near, but not above, the potential rate over the 1 m² surface
        assert 0.0 < evaporation <= 1e-7 * 1.0 * (1 + 1e-6)
        storage0 = soil.getTotalWaterStorage()
        soil.run(600.0)
        assert soil.getTotalWaterStorage() < storage0

    def test_surface_evaporation_needs_3d(self, soil):
        column(soil)
        with pytest.raises(SoilTransportModelError, match="3D"):
            soil.setSurfaceEvaporation(1e-7)

    def test_grid_change_after_setup_raises(self, soil):
        column(soil)
        soil.setInitialCondition(-1.0)
        with pytest.raises(SoilTransportModelError, match="already been set up"):
            soil.setColumnResolution(30)
        with pytest.raises(SoilTransportModelError, match="already been set up"):
            soil.setSolverType(SolverType.SOLVER_3D)

    def test_column_solver_needs_two_layers(self, soil):
        column(soil, nz=1)
        with pytest.raises(SoilTransportModelError, match="2 layers"):
            soil.initializeDomain()

    def test_run_rejects_nonpositive_dt(self, soil):
        column(soil)
        with pytest.raises(SoilTransportModelError, match="positive"):
            soil.run(0.0)

    def test_adaptive_diagnostics(self, soil):
        block3d(soil)
        soil.setSolverParameters(SolverParameters(adaptive_dt=True, nonlinear_method=NonlinearMethod.PICARD))
        soil.setInitialCondition(-2.0)
        soil.setTopBoundaryFlux(5e-6)
        soil.resetSolverIterationCount()
        soil.run(600.0)
        assert soil.getLastSubstepCount() >= 1
        assert 0.0 < soil.getTimestep() <= 3600.0
        assert soil.getSolverIterationCount() > 0
        soil.resetSolverIterationCount()
        assert soil.getSolverIterationCount() == 0
        # GPU instrumentation counters are 0 on the CPU
        soil.resetSolverStats()
        assert (soil.solverPicardOuter(), soil.solverNewtonOuter(), soil.solverPicardGmres(),
                soil.solverNewtonGmres()) == (0, 0, 0, 0)

    def test_solver_parameters_rejected(self, soil):
        with pytest.raises(SoilTransportModelError, match="dt_min"):
            soil.setSolverParameters(SolverParameters(dt_min=0.0))
        soil.setSolverType(SolverType.SOLVER_3D)
        with pytest.raises(SoilTransportModelError, match="enable_gravity"):
            soil.setSolverParameters(SolverParameters(enable_gravity=False))

    def test_gpu_choice_on_cpu(self, soil):
        if SoilTransportModel.isGPUAvailable():
            pytest.skip("a usable CUDA device is present")
        block3d(soil)
        assert soil.isGPUEnabled() is False
        with pytest.raises(SoilTransportModelError, match="enableGPU"):
            soil.enableGPU()
        soil.disableGPU()
        assert soil.isGPUEnabled() is False

    def test_messages(self, context, capfd):
        with SoilTransportModel(context) as soil:
            column(soil)
            soil.initializeDomain()
        enabled_output = capfd.readouterr().out
        if enabled_output == "" and sys.platform == "win32":
            # In the Windows wheel the native library's stdout does not reach pytest's fd capture, so there is no
            # signal to tell messages on from off. Limited to Windows so a plugin that went silent still fails elsewhere.
            pytest.skip("native stdout is not captured by capfd in this Windows build")
        assert "Initialized domain" in enabled_output
        with SoilTransportModel(context) as soil:
            soil.disableMessages()
            column(soil)
            soil.initializeDomain()
        assert "Initialized domain" not in capfd.readouterr().out


@pytest.mark.native_only
class TestSoilTransportRoots:
    """Root water uptake"""

    def test_uptake_meets_demand_in_wet_soil(self, soil):
        column(soil, nz=30, depth=1.5)
        soil.setInitialCondition(-0.5)
        soil.setTopBoundaryFlux(0.0)
        soil.setBottomBoundaryFlux(0.0)
        soil.setRootDistribution(1, RootDistributionParams(plant_x=0.5, plant_y=0.5))
        assert soil.getRootUptakeFlux(1) == 0.0
        soil.setTranspiration(1, 1e-7)
        assert soil.getRootUptakeFlux(1) == pytest.approx(1e-7, rel=1e-6)
        storage0 = soil.getTotalWaterStorage()
        soil.run(3600.0)
        assert storage0 - soil.getTotalWaterStorage() == pytest.approx(1e-7 * 3600.0, rel=1e-3)
        assert soil.getCumulativeRootUptake(1) == pytest.approx(1e-7 * 3600.0, rel=1e-3)
        assert soil.getSoilWaterPotential(1) == pytest.approx(-0.5, abs=0.01)

    def test_weibull_distribution(self, soil):
        column(soil, nz=30, depth=1.5)
        soil.setInitialCondition(-0.5)
        soil.setRootDistributionWeibull(2, WeibullRootParameters())
        soil.setTranspiration(2, 2e-7)
        assert soil.getRootUptakeFlux(2) == pytest.approx(2e-7, rel=1e-6)

    def test_water_stress_parameters(self, soil):
        """Uniform head h: uptake = T * min(1, alpha(h) / omega_c) with Feddes alpha."""
        column(soil, nz=30, depth=1.5)
        soil.setInitialCondition(-200.0)
        soil.setRootDistribution(1, RootDistributionParams())
        soil.setTranspiration(1, 1e-7)
        assert soil.getRootUptakeFlux(1) == 0.0  # default wilting head -150 m
        soil.setRootWaterStressParameters(-4.0, -300.0, 0.5)
        soil.setTranspiration(1, 1e-7)
        alpha = (-200.0 + 300.0) / (-4.0 + 300.0)
        assert soil.getRootUptakeFlux(1) == pytest.approx(1e-7 * alpha / 0.5, rel=1e-5)

    def test_invalid_stress_parameters_raise(self, soil):
        column(soil)
        with pytest.raises(SoilTransportModelError):
            soil.setRootWaterStressParameters(-150.0, -4.0, 0.5)

    def test_plant_without_roots_raises(self, soil):
        column(soil)
        soil.setInitialCondition(-1.0)
        with pytest.raises(SoilTransportModelError):
            soil.getSoilWaterPotential(7)
        with pytest.raises(SoilTransportModelError):
            soil.setTranspiration(7, 1e-7)
        with pytest.raises(SoilTransportModelError):
            soil.getRootUptakeFlux(7)
        with pytest.raises(SoilTransportModelError):
            soil.getCumulativeRootUptake(7)

    def test_root_flags_do_not_change_uptake(self, soil):
        """enableRootUptake() and setRootRadialConductivity() are accepted; neither changes the uptake."""
        column(soil, nz=30, depth=1.5)
        soil.setInitialCondition(-0.5)
        soil.enableRootUptake()
        soil.setRootRadialConductivity(2e-9)
        soil.setRootDistribution(1, RootDistributionParams())
        soil.setTranspiration(1, 1e-7)
        assert soil.getRootUptakeFlux(1) == pytest.approx(1e-7, rel=1e-6)


@pytest.mark.native_only
class TestSoilTransportSensors:
    """Point sensors"""

    def test_sensor_time_series(self, soil, tmp_path):
        column(soil)
        soil.setInitialCondition(-1.0)
        soil.setTopBoundaryFlux(2e-6)
        theta = soil.addSensor(vec3(0.5, 0.5, -0.1), SoilMeasurement.WATER_CONTENT)
        head = soil.addSensor(vec3(0.5, 0.5, -0.5), SoilMeasurement.PRESSURE_HEAD)
        assert (theta, head) == (0, 1)
        assert soil.getSensorCount() == 2
        assert soil.getSensorQuantity(head) == SoilMeasurement.PRESSURE_HEAD
        position = soil.getSensorPosition(theta)
        assert (position.x, position.y, position.z) == pytest.approx((0.5, 0.5, -0.1))

        for _ in range(3):
            soil.run(600.0)
            soil.recordSensors()
        assert soil.getSensorTimes(theta) == pytest.approx([600.0, 1200.0, 1800.0])
        assert soil.getSensorData(theta)[-1] == pytest.approx(soil.getWaterContent(vec3(0.5, 0.5, -0.1)))
        assert soil.getSensorData(head)[-1] == pytest.approx(soil.getPressureHead(vec3(0.5, 0.5, -0.5)))

        csv = tmp_path / "sensors.csv"
        soil.writeSensorData(str(csv))
        lines = csv.read_text().strip().splitlines()
        assert lines[0].startswith("time_s,") and len(lines) == 4

        soil.clearSensorData()
        assert soil.getSensorData(theta) == [] and soil.getSensorCount() == 2

    def test_sensor_outside_domain_raises(self, soil):
        column(soil)
        with pytest.raises(SoilTransportModelError):
            soil.addSensor(vec3(0.5, 0.5, 1.0), SoilMeasurement.WATER_CONTENT)

    def test_bad_sensor_id_raises(self, soil):
        with pytest.raises(SoilTransportModelError, match="out of range"):
            soil.getSensorData(3)


@pytest.mark.native_only
class TestSoilTransportVisualization:
    """Soil geometry added to the Context"""

    def test_field_visualization(self, context, soil):
        column(soil)
        soil.setInitialCondition(-1.0)
        uuids = soil.addSoilVisualization(SoilColorMode.WATER_CONTENT)
        assert len(uuids) > 0
        assert context.getPrimitiveData(uuids[0], "water_content", float) == pytest.approx(vg_theta(-1.0, LOAM), rel=1e-4)
        assert all(context.getPrimitiveData(u, "soil_cut_face", int) == 0 for u in uuids)

        soil.setTopBoundaryFlux(2e-6)
        soil.run(3600.0)
        soil.updateSoilVisualization(uuids, SoilColorMode.WATER_CONTENT)
        values = [context.getPrimitiveData(u, "water_content", float) for u in uuids]
        assert max(values) > vg_theta(-1.0, LOAM) + 0.01

    def test_cut_faces(self, context, soil):
        block3d(soil)
        soil.setInitialCondition(-1.0)
        keep = soil.addSoilVisualization(SoilColorMode.PRESSURE_HEAD, vec3(1, 1, 0.5))
        assert any(context.getPrimitiveData(u, "soil_cut_face", int) == 1 for u in keep)
        assert context.getPrimitiveData(keep[0], "pressure_head", float) == pytest.approx(-1.0)
        cutaway = soil.addSoilVisualization(SoilColorMode.WATER_CONTENT, vec3(0.5, 0.5, 0), vec3(1, 1, 0.5),
                                            region=SoilRegion.REMOVE)
        assert any(context.getPrimitiveData(u, "soil_cut_face", int) == 1 for u in cutaway)

    def test_texture_mode_from_another_directory(self, context, soil, tmp_path, monkeypatch):
        """The dirt texture resolves through HELIOS_BUILD, not the working directory."""
        monkeypatch.chdir(tmp_path)
        column(soil)
        soil.initializeDomain()
        uuids = soil.addSoilVisualization(SoilColorMode.TEXTURE)
        assert len(uuids) > 0
        assert context.getPrimitiveTextureFile(uuids[0]).endswith("dirt.jpg")

    def test_sub_box_keep_and_keywords(self, context, soil):
        block3d(soil)
        soil.setInitialCondition(-1.0)
        positional = soil.addSoilVisualization(SoilColorMode.WATER_CONTENT, vec3(0, 0, 0), vec3(0.5, 0.5, 0.5))
        keyword = soil.addSoilVisualization(SoilColorMode.WATER_CONTENT, fraction_min=vec3(0, 0, 0),
                                            fraction_max=vec3(0.5, 0.5, 0.5), region=SoilRegion.KEEP)
        assert len(positional) == len(keyword) > 0
        keep = soil.addSoilVisualization(SoilColorMode.WATER_CONTENT, keep_fraction=vec3(1, 1, 0.5))
        assert any(context.getPrimitiveData(u, "soil_cut_face", int) == 1 for u in keep)
        with pytest.raises(TypeError):
            soil.addSoilVisualization(SoilColorMode.WATER_CONTENT, vec3(1, 1, 1), keep_fraction=vec3(1, 1, 1))
        with pytest.raises(TypeError):
            soil.addSoilVisualization(SoilColorMode.WATER_CONTENT, fraction_min=vec3(0, 0, 0))
        with pytest.raises(ValueError, match="vec3"):
            soil.addSoilVisualization(SoilColorMode.WATER_CONTENT, keep_fraction=(1, 1, 0.5))

    def test_region_argument_rules(self, soil):
        with pytest.raises(ValueError, match="region"):
            soil.addSoilVisualization(SoilColorMode.WATER_CONTENT, vec3(1, 1, 0.5), region=SoilRegion.REMOVE)
        with pytest.raises(TypeError):
            soil.addSoilVisualization(SoilColorMode.WATER_CONTENT, vec3(0, 0, 0), vec3(1, 1, 1), vec3(1, 1, 1))


@pytest.mark.native_only
class TestSoilTransportArgumentValidation:
    """Argument types are checked before any native call, positionally and by keyword"""

    def test_vec3_arguments(self, soil):
        with pytest.raises(ValueError, match="vec3"):
            soil.defineSoilDomain(RGBcolor(0, 0, 0), vec3(1, 1, 1))
        with pytest.raises(ValueError, match="vec3"):
            soil.defineSoilDomain(origin=vec3(0, 0, 0), extent=[1, 1, 1])
        with pytest.raises(ValueError, match="vec3"):
            soil.getWaterContent((0.5, 0.5, -0.1))
        with pytest.raises(ValueError, match="vec3"):
            soil.getPressureHead(position=RGBcolor(0.5, 0.5, 0.1))
        with pytest.raises(ValueError, match="vec3"):
            soil.addSensor(RGBcolor(0.5, 0.5, 0.1), SoilMeasurement.WATER_CONTENT)

    def test_enum_arguments(self, soil):
        with pytest.raises(ValueError, match="SolverType"):
            soil.setSolverType(2)
        with pytest.raises(ValueError, match="SoilMeasurement"):
            soil.addSensor(vec3(0, 0, 0), quantity=SoilColorMode.WATER_CONTENT)
        with pytest.raises(ValueError, match="SoilColorMode"):
            soil.addSoilVisualization(SoilMeasurement.WATER_CONTENT)

    def test_struct_and_numeric_arguments(self, soil):
        with pytest.raises(ValueError, match="SoilProperties"):
            soil.setSoilProperties(LOAM)
        with pytest.raises(TypeError):
            soil.setSoilProperties(0, SoilProperties())
        with pytest.raises(ValueError, match="RootDistributionParams"):
            soil.setRootDistribution(1, WeibullRootParameters())
        with pytest.raises(ValueError, match="plant_id"):
            soil.setTranspiration(-1, 1e-7)
        with pytest.raises(ValueError, match="nz"):
            soil.setColumnResolution(10.5)
        with pytest.raises(ValueError, match="finite"):
            soil.setTopBoundaryFlux(float("nan"))
        with pytest.raises(ValueError, match="32-bit"):
            soil.setInitialCondition(-1e39)

    def test_use_after_exit_raises(self, context):
        soil = SoilTransportModel(context)
        soil.__exit__(None, None, None)
        with pytest.raises((ValueError, SoilTransportModelError)):
            soil.setInitialCondition(-1.0)


@pytest.mark.native_only
@pytest.mark.requires_gpu
class TestSoilTransportGPU:
    """CUDA backend of the full 3D solver"""

    def test_enable_gpu(self, soil):
        if not SoilTransportModel.isGPUAvailable():
            pytest.skip("no usable CUDA device for the soil solver")
        block3d(soil)
        soil.enableGPU()
        assert soil.isGPUEnabled() is True
        soil.setInitialCondition(-1.0)
        soil.setTopBoundaryFlux(2e-6)
        storage0 = soil.getTotalWaterStorage()
        soil.run(600.0)
        assert soil.getTotalWaterStorage() - storage0 == pytest.approx(soil.getCumulativeBoundaryInflux(), rel=1e-6)


# ----------------------------------------------------------------------------------------------
# Documentation examples
# ----------------------------------------------------------------------------------------------

DOC_PAGE = REPO_ROOT / "docs" / "plugin_soiltransport.md"
EXAMPLE_SCRIPT = REPO_ROOT / "docs" / "examples" / "soiltransport_sample.py"


def doc_code_blocks():
    if not DOC_PAGE.exists():
        return []
    return re.findall(r"```python\n(.*?)```", DOC_PAGE.read_text(), flags=re.S)


def run_python(source: str, cwd: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run([sys.executable, "-c", source], cwd=cwd, env=env, capture_output=True, text=True,
                          timeout=600)


@pytest.mark.native_only
@pytest.mark.slow
class TestSoilTransportDocumentation:
    """Every Python code block on the plugin page, and the example script, must run as written"""

    def test_page_has_examples(self):
        if not DOC_PAGE.exists():
            pytest.skip("docs/ not available in this test environment")
        assert len(doc_code_blocks()) >= 3

    @pytest.mark.parametrize("index", range(len(doc_code_blocks())))
    def test_doc_code_block_runs(self, index, tmp_path, check_native_library):
        block = doc_code_blocks()[index]
        if "Visualizer" in block:
            from pyhelios.plugins.registry import get_plugin_registry
            if not get_plugin_registry().is_plugin_available("visualizer"):
                pytest.skip("visualizer plugin not available")
            if os.environ.get("CI"):
                pytest.skip("headless OpenGL rendering is not reliable on CI runners")
        result = run_python(block, tmp_path)
        assert result.returncode == 0, f"block {index} failed:\n{result.stdout}\n{result.stderr}"

    def test_example_script_runs(self, tmp_path, check_native_library):
        if not EXAMPLE_SCRIPT.exists():
            pytest.skip("docs/examples not available in this test environment")
        result = run_python(EXAMPLE_SCRIPT.read_text(), tmp_path)
        assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
        assert "Near-surface water content" in result.stdout
