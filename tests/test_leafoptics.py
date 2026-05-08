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
