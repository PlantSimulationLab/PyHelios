"""
Tests for LeafOptics integration

This module tests the PROSPECT leaf optical model integration including
metadata, availability detection, spectral computation, and species library.
"""

import pytest
from pyhelios import Context
from pyhelios.plugins.registry import get_plugin_registry
from pyhelios import HeliosError
from pyhelios.types import vec3


class TestLeafOpticsMetadata:
    """Test plugin metadata and registration"""

    @pytest.mark.cross_platform
    def test_plugin_metadata_exists(self):
        """Test that plugin metadata is correctly defined"""
        from pyhelios.config.plugin_metadata import get_plugin_metadata

        metadata = get_plugin_metadata('leafoptics')
        assert metadata is not None
        assert metadata.name == 'leafoptics'
        assert metadata.description
        assert metadata.test_symbols
        assert isinstance(metadata.platforms, list)
        assert len(metadata.platforms) > 0
        assert 'windows' in metadata.platforms
        assert 'linux' in metadata.platforms
        assert 'macos' in metadata.platforms

    @pytest.mark.cross_platform
    def test_plugin_available(self):
        """Test that plugin is available when expected"""
        from pyhelios.config.plugin_metadata import PLUGIN_METADATA

        # Should be in plugin metadata
        assert 'leafoptics' in PLUGIN_METADATA

        # Should not require GPU
        metadata = PLUGIN_METADATA['leafoptics']
        assert not metadata.gpu_required

        # Should have no system dependencies
        assert metadata.system_dependencies == []


class TestLeafOpticsAvailability:
    """Test plugin availability detection"""

    @pytest.mark.cross_platform
    def test_plugin_registry_awareness(self):
        """Test that plugin registry knows about LeafOptics"""
        registry = get_plugin_registry()

        # Plugin should be known (even if not available)
        all_plugins = registry.get_available_plugins()
        # Note: leafoptics will be in all_plugins only if actually built and available

    @pytest.mark.cross_platform
    def test_graceful_unavailable_handling(self):
        """Test graceful handling when plugin unavailable"""
        registry = get_plugin_registry()

        with Context() as context:
            if not registry.is_plugin_available('leafoptics'):
                # Should raise informative error
                try:
                    from pyhelios import LeafOptics
                    if LeafOptics is not None:
                        with pytest.raises(Exception) as exc_info:
                            LeafOptics(context)

                        error_msg = str(exc_info.value).lower()
                        # Error should mention rebuilding or plugin unavailability
                        expected_keywords = ['rebuild', 'build', 'enable', 'compile', 'plugin', 'not available', 'unavailable']
                        found_keywords = [k for k in expected_keywords if k in error_msg]
                        assert len(found_keywords) > 0, f"Error message missing expected keywords. Got: '{str(exc_info.value)}'"
                except ImportError:
                    # LeafOptics not imported when plugin unavailable
                    pass
            else:
                # Plugin is available - nothing to test for graceful unavailable handling
                pass


class TestLeafOpticsInterface:
    """Test plugin interface without requiring native library"""

    @pytest.mark.cross_platform
    def test_plugin_class_structure(self):
        """Test that plugin class has expected structure"""
        try:
            from pyhelios import LeafOptics, LeafOpticsError, LeafOpticsProperties

            # Test class attributes and methods exist
            assert hasattr(LeafOptics, '__init__')
            assert hasattr(LeafOptics, '__enter__')
            assert hasattr(LeafOptics, '__exit__')
            assert hasattr(LeafOptics, 'run')
            assert hasattr(LeafOptics, 'runNoUUIDs')
            assert hasattr(LeafOptics, 'getLeafSpectra')
            assert hasattr(LeafOptics, 'setProperties')
            assert hasattr(LeafOptics, 'getPropertiesFromLibrary')
            assert hasattr(LeafOptics, 'getPropertiesFromSpectrum')
            assert hasattr(LeafOptics, 'enableMessages')
            assert hasattr(LeafOptics, 'disableMessages')
            assert hasattr(LeafOptics, 'getAvailableSpecies')
            assert hasattr(LeafOptics, 'isAvailable')

        except ImportError:
            # Expected when plugin not built
            pass

    @pytest.mark.cross_platform
    def test_error_types_available(self):
        """Test that error types are properly defined"""
        try:
            from pyhelios import LeafOpticsError
            assert issubclass(LeafOpticsError, HeliosError)
        except ImportError:
            # Expected when plugin not built
            pass

    @pytest.mark.cross_platform
    def test_properties_dataclass(self):
        """Test LeafOpticsProperties dataclass structure"""
        try:
            from pyhelios import LeafOpticsProperties

            # Test default values
            props = LeafOpticsProperties()
            assert props.numberlayers == 1.5
            assert props.brownpigments == 0.0
            assert props.chlorophyllcontent == 30.0
            assert props.carotenoidcontent == 7.0
            assert props.anthocyancontent == 1.0
            assert props.watermass == 0.015
            assert props.drymass == 0.09
            assert props.protein == 0.0
            assert props.carbonconstituents == 0.0

            # SIF parameters default to (V2Z=0, fqe=1) — inert for PROSPECT.
            assert props.V2Z == 0.0
            assert props.fqe == 1.0

            # Test to_list conversion (extended to 11 entries in v0.1.21)
            props_list = props.to_list()
            assert len(props_list) == 11
            assert props_list[0] == 1.5  # numberlayers
            assert props_list[2] == 30.0  # chlorophyllcontent
            assert props_list[9] == 0.0  # V2Z
            assert props_list[10] == 1.0  # fqe

            # Test from_list conversion with the 11-element layout
            custom_values = [2.0, 0.1, 40.0, 10.0, 2.0, 0.02, 0.1, 0.001, 0.005, 0.5, 0.8]
            custom_props = LeafOpticsProperties.from_list(custom_values)
            assert custom_props.numberlayers == 2.0
            assert custom_props.chlorophyllcontent == 40.0
            assert custom_props.protein == 0.001
            assert custom_props.V2Z == 0.5
            assert custom_props.fqe == 0.8

            # Backwards-compatible: legacy 9-float arrays still load with SIF defaults,
            # but should emit a DeprecationWarning to nudge callers to the 11-element layout.
            legacy_values = [2.0, 0.1, 40.0, 10.0, 2.0, 0.02, 0.1, 0.001, 0.005]
            with pytest.warns(DeprecationWarning):
                legacy_props = LeafOpticsProperties.from_list(legacy_values)
            assert legacy_props.numberlayers == 2.0
            assert legacy_props.V2Z == 0.0
            assert legacy_props.fqe == 1.0

        except ImportError:
            # Expected when plugin not built
            pass

    @pytest.mark.cross_platform
    def test_available_species_list(self):
        """Test available species list is correct"""
        try:
            from pyhelios.LeafOptics import AVAILABLE_SPECIES

            # Should have 12 species
            assert len(AVAILABLE_SPECIES) == 12

            # Check specific species
            assert 'default' in AVAILABLE_SPECIES
            assert 'sunflower' in AVAILABLE_SPECIES
            assert 'corn' in AVAILABLE_SPECIES
            assert 'rice' in AVAILABLE_SPECIES
            assert 'soybean' in AVAILABLE_SPECIES

        except ImportError:
            # Expected when plugin not built
            pass


@pytest.mark.native_only
class TestLeafOpticsFunctionality:
    """Test actual plugin functionality with native library"""

    def test_plugin_creation(self, basic_context):
        """Test plugin can be created and destroyed"""
        from pyhelios import LeafOptics

        leafoptics = LeafOptics(basic_context)
        assert leafoptics is not None
        assert isinstance(leafoptics, LeafOptics)

        # Test cleanup
        leafoptics.__exit__(None, None, None)

    def test_plugin_context_manager(self, basic_context):
        """Test plugin works as context manager"""
        from pyhelios import LeafOptics

        with LeafOptics(basic_context) as leafoptics:
            assert leafoptics is not None

    def test_get_properties_from_library_default(self, basic_context):
        """Test getting default properties from library"""
        from pyhelios import LeafOptics, LeafOpticsProperties

        with LeafOptics(basic_context) as leafoptics:
            props = leafoptics.getPropertiesFromLibrary("default")
            assert isinstance(props, LeafOpticsProperties)
            # Default should have reasonable values
            assert props.numberlayers > 0
            assert props.chlorophyllcontent > 0

    def test_get_properties_from_library_sunflower(self, basic_context):
        """Test getting sunflower properties from library"""
        from pyhelios import LeafOptics, LeafOpticsProperties

        with LeafOptics(basic_context) as leafoptics:
            props = leafoptics.getPropertiesFromLibrary("sunflower")
            assert isinstance(props, LeafOpticsProperties)
            # Sunflower should have higher chlorophyll than default
            assert props.chlorophyllcontent > 0

    def test_get_properties_from_library_all_species(self, basic_context):
        """Test getting properties for all available species"""
        from pyhelios import LeafOptics, LeafOpticsProperties
        from pyhelios.LeafOptics import AVAILABLE_SPECIES

        with LeafOptics(basic_context) as leafoptics:
            for species in AVAILABLE_SPECIES:
                props = leafoptics.getPropertiesFromLibrary(species)
                assert isinstance(props, LeafOpticsProperties), f"Failed for species: {species}"
                assert props.numberlayers > 0, f"Invalid numberlayers for {species}"

    def test_get_leaf_spectra_default(self, basic_context):
        """Test computing leaf spectra with default properties"""
        from pyhelios import LeafOptics, LeafOpticsProperties

        with LeafOptics(basic_context) as leafoptics:
            props = LeafOpticsProperties()
            wavelengths, reflectance, transmittance = leafoptics.getLeafSpectra(props)

            # Check output sizes (should be 2101 points for 400-2500 nm)
            assert len(wavelengths) == 2101
            assert len(reflectance) == 2101
            assert len(transmittance) == 2101

            # Check wavelength range
            assert wavelengths[0] == pytest.approx(400.0, abs=1.0)
            assert wavelengths[-1] == pytest.approx(2500.0, abs=1.0)

            # Check values are in valid range
            for i in range(len(reflectance)):
                assert 0.0 <= reflectance[i] <= 1.0, f"Invalid reflectance at {wavelengths[i]} nm"
                assert 0.0 <= transmittance[i] <= 1.0, f"Invalid transmittance at {wavelengths[i]} nm"
                # Energy conservation: R + T <= 1
                assert reflectance[i] + transmittance[i] <= 1.01, f"Energy conservation violated at {wavelengths[i]} nm"

    def test_get_leaf_spectra_green_peak(self, basic_context):
        """Test that spectra shows characteristic green peak"""
        from pyhelios import LeafOptics, LeafOpticsProperties

        with LeafOptics(basic_context) as leafoptics:
            props = LeafOpticsProperties(chlorophyllcontent=40.0)
            wavelengths, reflectance, transmittance = leafoptics.getLeafSpectra(props)

            # Find reflectance at different wavelengths
            idx_450 = int(450 - 400)  # Blue
            idx_550 = int(550 - 400)  # Green
            idx_650 = int(650 - 400)  # Red

            # Green peak: reflectance at 550 nm should be higher than at 450 nm and 650 nm
            assert reflectance[idx_550] > reflectance[idx_450], "Green peak not visible vs blue"
            assert reflectance[idx_550] > reflectance[idx_650], "Green peak not visible vs red"

    def test_get_leaf_spectra_nir_plateau(self, basic_context):
        """Test that spectra shows NIR plateau"""
        from pyhelios import LeafOptics, LeafOpticsProperties

        with LeafOptics(basic_context) as leafoptics:
            props = LeafOpticsProperties()
            wavelengths, reflectance, transmittance = leafoptics.getLeafSpectra(props)

            # NIR reflectance should be higher than visible
            idx_red = int(680 - 400)   # Red (low reflectance due to chlorophyll)
            idx_nir = int(800 - 400)   # NIR (high reflectance)

            assert reflectance[idx_nir] > reflectance[idx_red], "NIR plateau not visible"

    def test_run_with_primitives(self, basic_context):
        """Test running LeafOptics model with primitives"""
        from pyhelios import LeafOptics, LeafOpticsProperties

        # Add a leaf patch
        leaf_uuid = basic_context.addPatch(center=vec3(0, 0, 1), size=[0.1, 0.1])

        with LeafOptics(basic_context) as leafoptics:
            props = LeafOpticsProperties(chlorophyllcontent=35.0)
            leafoptics.run([leaf_uuid], props, "test_leaf")

            # Verify global data was created
            # (The exact verification depends on Context capabilities)

    def test_run_no_uuids(self, basic_context):
        """Test running LeafOptics without assigning to primitives"""
        from pyhelios import LeafOptics, LeafOpticsProperties

        with LeafOptics(basic_context) as leafoptics:
            props = LeafOpticsProperties()
            # Should not raise an exception
            leafoptics.runNoUUIDs(props, "test_global_spectra")

    def test_set_properties(self, basic_context):
        """Test setting properties on primitives"""
        from pyhelios import LeafOptics, LeafOpticsProperties

        # Add leaf patches
        leaf1_uuid = basic_context.addPatch(center=vec3(0, 0, 1), size=[0.1, 0.1])
        leaf2_uuid = basic_context.addPatch(center=vec3(0.2, 0, 1), size=[0.1, 0.1])

        with LeafOptics(basic_context) as leafoptics:
            props = LeafOpticsProperties(chlorophyllcontent=45.0, watermass=0.02)
            leafoptics.setProperties([leaf1_uuid, leaf2_uuid], props)

    def test_message_control(self, basic_context):
        """Test message enable/disable"""
        from pyhelios import LeafOptics

        with LeafOptics(basic_context) as leafoptics:
            # Should not raise exceptions
            leafoptics.disableMessages()
            leafoptics.enableMessages()


@pytest.mark.native_only
class TestLeafOpticsErrorHandling:
    """Test error handling for LeafOptics"""

    def test_invalid_context(self):
        """Test error when passing invalid context"""
        from pyhelios import LeafOptics

        with pytest.raises(TypeError):
            LeafOptics(None)

        with pytest.raises(TypeError):
            LeafOptics("not a context")

    def test_run_empty_uuids(self, basic_context):
        """Test error when passing empty UUID list"""
        from pyhelios import LeafOptics, LeafOpticsProperties

        with LeafOptics(basic_context) as leafoptics:
            props = LeafOpticsProperties()
            with pytest.raises(ValueError, match="empty"):
                leafoptics.run([], props, "test")

    def test_run_empty_label(self, basic_context):
        """Test error when passing empty label"""
        from pyhelios import LeafOptics, LeafOpticsProperties

        leaf_uuid = basic_context.addPatch(center=vec3(0, 0, 1), size=[0.1, 0.1])

        with LeafOptics(basic_context) as leafoptics:
            props = LeafOpticsProperties()
            with pytest.raises(ValueError, match="empty"):
                leafoptics.run([leaf_uuid], props, "")

    def test_get_properties_empty_species(self, basic_context):
        """Test error when passing empty species name"""
        from pyhelios import LeafOptics

        with LeafOptics(basic_context) as leafoptics:
            with pytest.raises(ValueError, match="empty"):
                leafoptics.getPropertiesFromLibrary("")

    def test_prospect_pro_spectra_are_finite(self, basic_context):
        """A PROSPECT-PRO leaf with no water must produce finite spectra everywhere.

        Regression test for helios-core 1.3.80: the elementary-layer transmittance returned 0
        instead of 1 when the absorption coefficient k was exactly zero, which made the
        internal transmissivity zero and divided by it in the Stokes solution, producing NaN
        reflectance and transmittance. This is reachable with documented inputs — the protein
        absorption spectrum is identically zero over 400-1432 nm and PROSPECT-PRO forces
        drymass to zero, so such a leaf absorbs nothing at 652 of the 2101 wavelengths. The
        NaN spectra were written to global data and consumed by the radiation plugin with no
        diagnostic.

        Asserting finiteness specifically: the pre-existing range check (0 <= value <= 1)
        would also catch NaN, but no existing test ever drove k to zero because they all kept
        watermass and drymass non-zero.
        """
        import math
        from pyhelios import LeafOptics, LeafOpticsProperties

        with LeafOptics(basic_context) as leafoptics:
            # PROSPECT-PRO mode: protein and carbon constituents instead of bulk dry mass,
            # and no water, so absorption is exactly zero across much of the spectrum.
            props = LeafOpticsProperties(
                numberlayers=1.5,
                chlorophyllcontent=0.0,
                carotenoidcontent=0.0,
                anthocyancontent=0.0,
                brownpigments=0.0,
                watermass=0.0,
                drymass=0.0,
                protein=0.001,
                # Must stay zero: the carbon-constituents absorption spectrum is non-zero
                # everywhere, so any positive value keeps k > 0 and never reaches the bug.
                carbonconstituents=0.0,
            )
            leafoptics.disableMessages()
            wavelengths, reflectance, transmittance = leafoptics.getLeafSpectra(props)

            assert len(reflectance) == 2101 and len(transmittance) == 2101
            for i in range(len(reflectance)):
                assert math.isfinite(reflectance[i]), \
                    f"non-finite reflectance {reflectance[i]} at {wavelengths[i]} nm"
                assert math.isfinite(transmittance[i]), \
                    f"non-finite transmittance {transmittance[i]} at {wavelengths[i]} nm"

    def test_invalid_prospect_inputs_are_rejected(self, basic_context):
        """numberlayers < 1 and negative constituents must raise, not produce garbage.

        helios-core 1.3.80 added input validation: N < 1 makes the Stokes exponent negative,
        which inverts the layer stack and can drive the zero-absorption denominator through
        zero, and N = 0 divides by zero outright. Negative constituent contents would
        contribute negative absorption.
        """
        from pyhelios import LeafOptics, LeafOpticsProperties, HeliosError

        with LeafOptics(basic_context) as leafoptics:
            with pytest.raises(HeliosError):
                leafoptics.getLeafSpectra(LeafOpticsProperties(numberlayers=0.5))

            with pytest.raises(HeliosError):
                leafoptics.getLeafSpectra(LeafOpticsProperties(chlorophyllcontent=-1.0))


@pytest.mark.native_only
class TestLeafOpticsIntegration:
    """Test LeafOptics integration with other PyHelios components"""

    def test_context_integration(self, basic_context):
        """Test LeafOptics works with Context geometry"""
        from pyhelios import LeafOptics, LeafOpticsProperties

        # Add various geometry
        patch_uuid = basic_context.addPatch(center=vec3(0, 0, 1), size=[0.1, 0.1])
        triangle_uuid = basic_context.addTriangle(
            vertex0=vec3(0, 0, 0),
            vertex1=vec3(1, 0, 0),
            vertex2=vec3(0.5, 1, 0)
        )

        with LeafOptics(basic_context) as leafoptics:
            props = leafoptics.getPropertiesFromLibrary("corn")
            # Should work with mixed geometry types
            leafoptics.run([patch_uuid, triangle_uuid], props, "corn_leaves")

    def test_multiple_species_workflow(self, basic_context):
        """Test workflow with multiple species"""
        from pyhelios import LeafOptics, LeafOpticsProperties

        # Add leaves for different species
        sunflower_uuid = basic_context.addPatch(center=vec3(0, 0, 1), size=[0.15, 0.15])
        corn_uuid = basic_context.addPatch(center=vec3(0.3, 0, 1), size=[0.1, 0.05])
        soybean_uuid = basic_context.addPatch(center=vec3(0.6, 0, 1), size=[0.08, 0.08])

        with LeafOptics(basic_context) as leafoptics:
            # Apply different species to different leaves
            sunflower_props = leafoptics.getPropertiesFromLibrary("sunflower")
            leafoptics.run([sunflower_uuid], sunflower_props, "sunflower")

            corn_props = leafoptics.getPropertiesFromLibrary("corn")
            leafoptics.run([corn_uuid], corn_props, "corn")

            soybean_props = leafoptics.getPropertiesFromLibrary("soybean")
            leafoptics.run([soybean_uuid], soybean_props, "soybean")

    def test_custom_properties(self, basic_context):
        """Test using custom leaf properties"""
        from pyhelios import LeafOptics, LeafOpticsProperties

        leaf_uuid = basic_context.addPatch(center=vec3(0, 0, 1), size=[0.1, 0.1])

        # Create custom properties (e.g., stressed leaf with high anthocyanin)
        stressed_props = LeafOpticsProperties(
            numberlayers=2.0,
            brownpigments=0.5,
            chlorophyllcontent=20.0,  # Lower chlorophyll
            carotenoidcontent=10.0,
            anthocyancontent=5.0,     # Higher anthocyanin (stress indicator)
            watermass=0.01,           # Lower water (drought stress)
            drymass=0.08,
            protein=0.0,
            carbonconstituents=0.0
        )

        with LeafOptics(basic_context) as leafoptics:
            leafoptics.run([leaf_uuid], stressed_props, "stressed_leaf")

            # Verify spectra can be computed
            wavelengths, refl, trans = leafoptics.getLeafSpectra(stressed_props)
            assert len(wavelengths) == 2101


@pytest.mark.native_only
class TestLeafOpticsAssets:
    """Test LeafOptics asset management"""

    def test_spectral_data_loaded(self, basic_context):
        """Test that spectral data is properly loaded"""
        from pyhelios import LeafOptics, LeafOpticsProperties

        # If we can create LeafOptics and compute spectra, assets are loaded
        with LeafOptics(basic_context) as leafoptics:
            props = LeafOpticsProperties()
            wavelengths, refl, trans = leafoptics.getLeafSpectra(props)

            # Should have full spectral range
            assert len(wavelengths) == 2101

    def test_static_methods_work_without_instance(self):
        """Test static methods work without creating instance"""
        from pyhelios import LeafOptics

        # getAvailableSpecies should work without instance
        species = LeafOptics.getAvailableSpecies()
        assert len(species) == 12
        assert 'default' in species

        # isAvailable should work without instance
        is_available = LeafOptics.isAvailable()
        assert isinstance(is_available, bool)


# ---------------------------------------------------------------------------
# Nitrogen-based automatic mode (LeafOpticsProperties_Nauto)
# ---------------------------------------------------------------------------

def _import_nauto():
    try:
        from pyhelios.LeafOptics import LeafOpticsProperties_Nauto
    except ImportError:
        pytest.skip("pyhelios.LeafOptics not importable in this environment")
    return LeafOpticsProperties_Nauto


@pytest.mark.cross_platform
class TestLeafOpticsNautoProperties:
    """Pure-Python behavior of LeafOpticsProperties_Nauto and nitrogen-mode argument checks"""

    def test_defaults_mirror_cpp_header(self):
        """Every default must match the LeafOpticsProperties_Nauto struct in LeafOptics.h"""
        import re
        from pathlib import Path
        LeafOpticsProperties_Nauto = _import_nauto()

        header = Path(__file__).resolve().parent.parent / "helios-core" / "plugins" / "leafoptics" / "include" / "LeafOptics.h"
        if not header.exists():
            pytest.skip("helios-core LeafOptics.h not present")
        text = header.read_text()
        body = text[text.index("struct LeafOpticsProperties_Nauto"):]
        body = body[:body.index("};")]
        cpp_defaults = {name: float(value.rstrip("fF"))
                        for name, value in re.findall(r"^\s*(?:float|uint)\s+(\w+)\s*=\s*([0-9.eE+-]+f?)\s*;", body, re.M)}

        props = LeafOpticsProperties_Nauto()
        assert len(cpp_defaults) == 15
        for name, value in cpp_defaults.items():
            assert getattr(props, name) == pytest.approx(value), f"default for {name} differs from C++"

    def test_to_list_order(self):
        LeafOpticsProperties_Nauto = _import_nauto()
        props = LeafOpticsProperties_Nauto(
            f_photosynthetic=0.1, N_to_Cab_coefficient=0.2, Car_to_Cab_ratio=0.3, numberlayers=1.4,
            anthocyancontent=0.5, brownpigments=0.6, watermass=0.7, drymass=0.8, protein=0.9,
            carbonconstituents=1.0, V2Z=0.11, fqe=1.2, num_bins=7, reassignment_threshold=1.3,
            min_reassignment_change=1.4)
        assert props.to_list() == pytest.approx(
            [0.1, 0.2, 0.3, 1.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.11, 1.2, 1.3, 1.4])

    @pytest.mark.parametrize("field,value", [
        ("numberlayers", 0.5),
        ("drymass", -0.001),
        ("f_photosynthetic", 1.5),
        ("V2Z", 2.0),
        ("min_reassignment_change", -0.1),
        ("watermass", float("nan")),
        ("N_to_Cab_coefficient", "0.4"),
        ("num_bins", 0),
        ("num_bins", 2.5),
        ("num_bins", True),
    ])
    def test_validate_rejects_bad_values(self, field, value):
        LeafOpticsProperties_Nauto = _import_nauto()
        props = LeafOpticsProperties_Nauto(**{field: value})
        with pytest.raises(ValueError, match=field):
            props.validate()

    def test_validate_accepts_defaults(self):
        LeafOpticsProperties_Nauto = _import_nauto()
        LeafOpticsProperties_Nauto().validate()

    def test_run_argument_validation_without_native(self):
        """run() rejects bad nitrogen-mode arguments before touching the native layer"""
        LeafOpticsProperties_Nauto = _import_nauto()
        from pyhelios.LeafOptics import LeafOptics

        lo = object.__new__(LeafOptics)  # no native instance; only argument checks are exercised
        lo._leafoptics_ptr = None
        with pytest.raises(ValueError, match="label must not be given"):
            lo.run([1], LeafOpticsProperties_Nauto(), "my_label")
        with pytest.raises(ValueError, match="empty"):
            lo.run([], LeafOpticsProperties_Nauto())
        with pytest.raises(ValueError, match="num_bins"):
            lo.run([1], LeafOpticsProperties_Nauto(num_bins=0))
        with pytest.raises(ValueError, match="LeafOpticsProperties_Nauto"):
            lo.run([1], {"f_photosynthetic": 0.5})

    def test_wrapper_functions_fail_loudly_without_instance(self):
        from pyhelios.wrappers import ULeafOpticsWrapper as w
        params = [0.0] * w.LEAF_OPTICS_NAUTO_FLOAT_COUNT
        with pytest.raises((ValueError, RuntimeError, NotImplementedError)):
            w.leafOpticsRunNitrogen(None, [1], params, 1)
        with pytest.raises((ValueError, RuntimeError, NotImplementedError)):
            w.leafOpticsUpdateNitrogenBasedSpectra(None)


@pytest.mark.native_only
class TestLeafOpticsNitrogenMode:
    """Nitrogen-based automatic leaf optics against the native library"""

    @staticmethod
    def _leaf(context, x, nitrogen):
        from pyhelios.types import vec2, int2
        objID = context.addTileObject(center=vec3(x, 0, 1), size=vec2(0.1, 0.1), subdiv=int2(2, 2))
        if nitrogen is not None:
            context.setObjectDataFloat(objID, "leaf_nitrogen_gN_m2", nitrogen)
        return objID, context.getObjectPrimitiveUUIDs(objID)

    def test_assigns_binned_spectra_per_object(self, basic_context):
        from pyhelios import LeafOptics
        LeafOpticsProperties_Nauto = _import_nauto()

        low_obj, low_uuids = self._leaf(basic_context, 0, 1.0)
        high_obj, high_uuids = self._leaf(basic_context, 1, 3.0)

        with LeafOptics(basic_context) as lo:
            lo.disableMessages()
            lo.run(low_uuids + high_uuids, LeafOpticsProperties_Nauto(num_bins=2))

        for i in range(2):
            assert basic_context.doesGlobalDataExist(f"leaf_reflectivity_Nauto_{i}")
            assert basic_context.doesGlobalDataExist(f"leaf_transmissivity_Nauto_{i}")
            assert basic_context.doesGlobalDataExist(f"fluspect_biochem_Nauto_{i}")
        assert not basic_context.doesGlobalDataExist("leaf_reflectivity_Nauto_2")

        # Every primitive of an object shares that object's bin
        for uuid in low_uuids:
            assert basic_context.getPrimitiveData(uuid, "reflectivity_spectrum") == "leaf_reflectivity_Nauto_0"
            assert basic_context.getPrimitiveData(uuid, "transmissivity_spectrum") == "leaf_transmissivity_Nauto_0"
        for uuid in high_uuids:
            assert basic_context.getPrimitiveData(uuid, "reflectivity_spectrum") == "leaf_reflectivity_Nauto_1"

    def test_chlorophyll_follows_nitrogen(self, basic_context):
        """Cab = N * 100 * f_photosynthetic * N_to_Cab_coefficient, Car = Cab * Car_to_Cab_ratio"""
        from pyhelios import LeafOptics
        LeafOpticsProperties_Nauto = _import_nauto()

        _, low_uuids = self._leaf(basic_context, 0, 1.0)
        _, high_uuids = self._leaf(basic_context, 1, 3.0)

        params = LeafOpticsProperties_Nauto(num_bins=2, Car_to_Cab_ratio=0.2)
        with LeafOptics(basic_context) as lo:
            lo.disableMessages()
            lo.optionalOutputPrimitiveData("chlorophyll")
            lo.optionalOutputPrimitiveData("carotenoid")
            lo.run(low_uuids + high_uuids, params)

        assert basic_context.getPrimitiveDataFloat(low_uuids[0], "chlorophyll") == pytest.approx(20.0, rel=1e-5)
        assert basic_context.getPrimitiveDataFloat(high_uuids[0], "chlorophyll") == pytest.approx(60.0, rel=1e-5)
        assert basic_context.getPrimitiveDataFloat(high_uuids[0], "carotenoid") == pytest.approx(12.0, rel=1e-5)

    def test_chlorophyll_is_clamped(self, basic_context):
        from pyhelios import LeafOptics
        LeafOpticsProperties_Nauto = _import_nauto()

        _, low_uuids = self._leaf(basic_context, 0, 0.0)
        _, high_uuids = self._leaf(basic_context, 1, 10.0)

        with LeafOptics(basic_context) as lo:
            lo.disableMessages()
            lo.optionalOutputPrimitiveData("chlorophyll")
            lo.run(low_uuids + high_uuids, LeafOpticsProperties_Nauto(num_bins=2))

        assert basic_context.getPrimitiveDataFloat(low_uuids[0], "chlorophyll") == pytest.approx(5.0)
        assert basic_context.getPrimitiveDataFloat(high_uuids[0], "chlorophyll") == pytest.approx(80.0)

    def test_spectra_respond_to_nitrogen(self, basic_context):
        """A high-nitrogen leaf is greener: more chlorophyll, lower visible reflectance"""
        from pyhelios import LeafOptics, LeafOpticsProperties
        LeafOpticsProperties_Nauto = _import_nauto()

        _, low_uuids = self._leaf(basic_context, 0, 0.5)
        _, high_uuids = self._leaf(basic_context, 1, 3.0)

        with LeafOptics(basic_context) as lo:
            lo.disableMessages()
            lo.optionalOutputPrimitiveData("chlorophyll")
            lo.optionalOutputPrimitiveData("carotenoid")
            lo.run(low_uuids + high_uuids, LeafOpticsProperties_Nauto(num_bins=2))

            def spectrum_of(uuid):
                props = LeafOpticsProperties(
                    numberlayers=1.5, chlorophyllcontent=basic_context.getPrimitiveDataFloat(uuid, "chlorophyll"),
                    carotenoidcontent=basic_context.getPrimitiveDataFloat(uuid, "carotenoid"),
                    anthocyancontent=1.0, watermass=0.015, drymass=0.006)
                return props.chlorophyllcontent, lo.getLeafSpectra(props)

            cab_low, (wl, refl_low, _) = spectrum_of(low_uuids[0])
            cab_high, (_, refl_high, _) = spectrum_of(high_uuids[0])

        assert cab_low == pytest.approx(10.0, rel=1e-5)
        assert cab_high == pytest.approx(60.0, rel=1e-5)
        i550 = wl.index(550.0)
        assert refl_high[i550] < refl_low[i550]

    def test_missing_nitrogen_data_raises(self, basic_context):
        from pyhelios import LeafOptics
        from pyhelios.LeafOptics import LeafOpticsError
        LeafOpticsProperties_Nauto = _import_nauto()

        _, uuids = self._leaf(basic_context, 0, None)
        with LeafOptics(basic_context) as lo:
            lo.disableMessages()
            with pytest.raises(LeafOpticsError, match="leaf_nitrogen_gN_m2"):
                lo.run(uuids, LeafOpticsProperties_Nauto())

    def test_update_before_run_raises(self, basic_context):
        from pyhelios import LeafOptics
        from pyhelios.LeafOptics import LeafOpticsError

        with LeafOptics(basic_context) as lo:
            with pytest.raises(LeafOpticsError, match="[Nn]itrogen mode is not active"):
                lo.updateNitrogenBasedSpectra()

    def test_update_reassigns_after_nitrogen_change(self, basic_context):
        from pyhelios import LeafOptics
        LeafOpticsProperties_Nauto = _import_nauto()

        low_obj, low_uuids = self._leaf(basic_context, 0, 1.0)
        _, high_uuids = self._leaf(basic_context, 1, 3.0)

        with LeafOptics(basic_context) as lo:
            lo.disableMessages()
            lo.run(low_uuids + high_uuids, LeafOpticsProperties_Nauto(num_bins=2))
            assert basic_context.getPrimitiveData(low_uuids[0], "reflectivity_spectrum") == "leaf_reflectivity_Nauto_0"

            basic_context.setObjectDataFloat(low_obj, "leaf_nitrogen_gN_m2", 3.0)
            lo.updateNitrogenBasedSpectra()

        for uuid in low_uuids:
            assert basic_context.getPrimitiveData(uuid, "reflectivity_spectrum") == "leaf_reflectivity_Nauto_1"

    def test_rerun_rebuilds_bins_when_nitrogen_leaves_range(self, basic_context):
        from pyhelios import LeafOptics
        LeafOpticsProperties_Nauto = _import_nauto()

        obj, uuids = self._leaf(basic_context, 0, 1.0)
        with LeafOptics(basic_context) as lo:
            lo.disableMessages()
            lo.optionalOutputPrimitiveData("chlorophyll")
            lo.run(uuids, LeafOpticsProperties_Nauto())
            assert basic_context.getPrimitiveDataFloat(uuids[0], "chlorophyll") == pytest.approx(20.0, rel=1e-5)

            basic_context.setObjectDataFloat(obj, "leaf_nitrogen_gN_m2", 2.5)
            lo.run(uuids, LeafOpticsProperties_Nauto())

        assert basic_context.getPrimitiveDataFloat(uuids[0], "chlorophyll") == pytest.approx(50.0, rel=1e-5)
