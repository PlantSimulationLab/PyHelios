"""
Test suite for PhotosynthesisModel plugin.

Comprehensive tests covering all photosynthesis modeling functionality,
parameter validation, species library, and cross-platform compatibility.
"""

import pytest
from pyhelios import Context
from pyhelios.PhotosynthesisModel import PhotosynthesisModel, PhotosynthesisModelError
from pyhelios.types.photosynthesis import (
    PhotosyntheticTemperatureResponseParameters,
    EmpiricalModelCoefficients,
    FarquharModelCoefficients,
    PHOTOSYNTHESIS_SPECIES,
    validate_species_name,
    get_available_species,
    get_species_aliases
)
from pyhelios.validation.exceptions import ValidationError


class TestPhotosynthesisSpeciesLibrary:
    """Test the photosynthesis species library functionality."""
    
    def test_photosynthesis_species_constants(self):
        """Test that PHOTOSYNTHESIS_SPECIES contains expected species."""
        assert "Almond" in PHOTOSYNTHESIS_SPECIES
        assert "Apple" in PHOTOSYNTHESIS_SPECIES
        assert "Grape" in PHOTOSYNTHESIS_SPECIES
        assert len(PHOTOSYNTHESIS_SPECIES) >= 15  # Should have at least 15 species
        
    def test_get_available_species(self):
        """Test getting available species list."""
        species = get_available_species()
        assert isinstance(species, list)
        assert len(species) >= 15
        assert "Almond" in species
        assert "Apple" in species
        
    def test_get_species_aliases(self):
        """Test getting species aliases mapping."""
        aliases = get_species_aliases()
        assert isinstance(aliases, dict)
        # Test some expected aliases
        if "apple" in aliases:
            assert aliases["apple"] == "Apple"
        if "grape" in aliases:
            assert aliases["grape"] == "Grape"
            
    def test_validate_species_name_valid(self):
        """Test species name validation with valid names."""
        # Test canonical names
        assert validate_species_name("Apple") == "Apple"
        assert validate_species_name("Almond") == "Almond"
        
        # Test case insensitive
        assert validate_species_name("apple") == "Apple"
        assert validate_species_name("APPLE") == "Apple"
        
    def test_validate_species_name_invalid(self):
        """Test species name validation with invalid names."""
        with pytest.raises(ValueError):
            validate_species_name("INVALID_SPECIES")
            
        with pytest.raises(ValueError):
            validate_species_name("")


class TestPhotosynthesisParameterStructures:
    """Test the photosynthesis parameter structure dataclasses."""
    
    def test_temperature_response_parameters_creation(self):
        """Test PhotosyntheticTemperatureResponseParameters creation."""
        params = PhotosyntheticTemperatureResponseParameters()
        assert params.value_at_25C == 100.0
        assert params.dHa == 60.0
        assert params.dHd == 600.0
        assert params.Topt == 10000.0
        
        # Test custom values
        params = PhotosyntheticTemperatureResponseParameters(
            value_at_25C=25.0,
            dHa=65000.0,
            dHd=200000.0,
            Topt=25.0
        )
        assert params.value_at_25C == 25.0
        assert params.dHa == 65000.0
        assert params.dHd == 200000.0
        assert params.Topt == 25.0
        
    def test_empirical_model_coefficients_creation(self):
        """Test EmpiricalModelCoefficients creation."""
        coeffs = EmpiricalModelCoefficients()
        assert coeffs.Tref == 298.0
        assert coeffs.Ci_ref == 290.0
        assert coeffs.Asat == 18.18
        
        # Test to_array method
        arr = coeffs.to_array()
        assert isinstance(arr, list)
        assert len(arr) == 10
        assert arr[0] == 298.0  # Tref
        
        # Test from_array method
        coeffs2 = EmpiricalModelCoefficients.from_array(arr)
        assert coeffs2.Tref == coeffs.Tref
        assert coeffs2.Ci_ref == coeffs.Ci_ref
        
    def test_farquhar_model_coefficients_creation(self):
        """Test FarquharModelCoefficients creation."""
        coeffs = FarquharModelCoefficients()
        assert coeffs.Vcmax == -1.0  # Uninitialized
        assert coeffs.Jmax == -1.0   # Uninitialized
        assert coeffs.O == 213.5     # Ambient oxygen
        
        # Test custom values  
        coeffs = FarquharModelCoefficients(Vcmax=100.0, Jmax=180.0)
        assert coeffs.Vcmax == 100.0
        assert coeffs.Jmax == 180.0


@pytest.mark.cross_platform
class TestPhotosynthesisModelMockMode:
    """Test PhotosynthesisModel in mock mode (cross-platform)."""
    
    def test_photosynthesis_model_static_methods(self):
        """Test static methods work without native libraries."""
        species = PhotosynthesisModel.get_available_species()
        assert isinstance(species, list)
        assert len(species) >= 15
        
        aliases = PhotosynthesisModel.get_species_aliases()
        assert isinstance(aliases, dict)
        
    def test_photosynthesis_model_mock_initialization_error(self):
        """Test PhotosynthesisModel initialization when plugin is available."""
        context = Context()
        
        # Since photosynthesis plugin is now built and available,
        # this should succeed rather than raise an error
        try:
            with PhotosynthesisModel(context) as photosynthesis:
                assert photosynthesis is not None
                assert photosynthesis.get_native_ptr() is not None
        except PhotosynthesisModelError:
            # If this fails, it means the plugin is not available
            # In that case, we expect a clear error message
            pass
        
    def test_photosynthesis_model_invalid_context(self):
        """Test initialization with invalid context."""
        with pytest.raises(PhotosynthesisModelError) as exc_info:
            PhotosynthesisModel("not a context")
            
        assert "Context parameter must be a Context instance" in str(exc_info.value)


@pytest.mark.native_only
class TestPhotosynthesisModelNative:
    """Test PhotosynthesisModel with native libraries."""
    
    def test_photosynthesis_model_initialization(self):
        """Test PhotosynthesisModel initialization with native libraries."""
        context = Context()
        
        with PhotosynthesisModel(context) as photosynthesis:
            assert photosynthesis is not None
            assert photosynthesis.get_native_ptr() is not None
            
    def test_photosynthesis_model_context_manager(self):
        """Test context manager functionality."""
        context = Context()
        
        with PhotosynthesisModel(context) as photosynthesis:
            ptr_before = photosynthesis.get_native_ptr()
            assert ptr_before is not None
            
        # After context manager, should be cleaned up
        assert photosynthesis.get_native_ptr() is None
        
    def test_model_type_configuration(self):
        """The selected model must actually drive the calculation.

        There is no getModelType() accessor, so the model type is observable only through the
        assimilation rate it produces: the empirical and Farquhar models give measurably
        different answers for identical inputs.
        """
        from pyhelios.types import vec3, vec2

        rates = {}
        for label, select in (("empirical", "setModelTypeEmpirical"),
                              ("farquhar", "setModelTypeFarquhar")):
            context = Context()
            uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
            context.setPrimitiveDataFloat(uuid, "radiation_flux_PAR", 500.0)
            context.setPrimitiveDataFloat(uuid, "temperature", 300.0)

            with PhotosynthesisModel(context) as photosynthesis:
                getattr(photosynthesis, select)()
                photosynthesis.run()

            rates[label] = context.getPrimitiveDataFloat(uuid, "net_photosynthesis")

        for label, rate in rates.items():
            assert rate > 0, f"{label} model produced no assimilation"
        assert rates["empirical"] != pytest.approx(rates["farquhar"], rel=1e-3), (
            "both model types produced the same rate, so the selection had no effect"
        )
            
    def test_species_configuration(self):
        """Test species coefficient configuration."""
        context = Context()
        
        with PhotosynthesisModel(context) as photosynthesis:
            photosynthesis.setSpeciesCoefficients("Apple")
            canonical = photosynthesis.getSpeciesCoefficients("Apple")

            # The lookup is case insensitive: the alias must resolve to the same coefficients.
            photosynthesis.setSpeciesCoefficients("apple")
            assert photosynthesis.getSpeciesCoefficients("apple") == canonical

            # And a real species must differ from the default, or the call did nothing.
            assert canonical != photosynthesis.getSpeciesCoefficients("Almond")
            
    def test_species_coefficients_retrieval(self):
        """Test getting species coefficients."""
        context = Context()
        
        with PhotosynthesisModel(context) as photosynthesis:
            coeffs = photosynthesis.getSpeciesCoefficients("Apple")
            assert isinstance(coeffs, list)
            assert len(coeffs) > 0
            
    def test_empirical_model_configuration(self):
        """The coefficients set globally must reach each primitive."""
        from pyhelios.types import vec3, vec2

        context = Context()
        uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))

        with PhotosynthesisModel(context) as photosynthesis:
            coeffs = EmpiricalModelCoefficients()
            coeffs.Asat = 25.0
            photosynthesis.setEmpiricalModelCoefficients(coeffs)

            # Slot 2 of the empirical layout is Asat; see EmpiricalModelCoefficients.to_array().
            assert photosynthesis.getEmpiricalModelCoefficients(uuid)[2] == pytest.approx(25.0)
            
    def test_farquhar_model_configuration(self):
        """The coefficients set globally must reach each primitive."""
        from pyhelios.types import vec3, vec2

        context = Context()
        uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))

        with PhotosynthesisModel(context) as photosynthesis:
            coeffs = FarquharModelCoefficients(Vcmax=100.0, Jmax=180.0)
            photosynthesis.setFarquharModelCoefficients(coeffs)

            stored = FarquharModelCoefficients.from_array(
                photosynthesis.getFarquharModelCoefficients(uuid))
            assert stored.getVcmaxTempResponse().value_at_25C == pytest.approx(100.0, abs=1e-4)
            assert stored.getJmaxTempResponse().value_at_25C == pytest.approx(180.0, abs=1e-4)
            
    @pytest.mark.native_only
    def test_individual_farquhar_parameters(self):
        """Test setting individual Farquhar parameters."""
        context = Context()
        
        # Add test primitive
        from pyhelios.types import vec3, vec2, RGBcolor
        center = vec3(0, 0, 0)
        size = vec2(1, 1)
        color = RGBcolor(0.5, 0.8, 0.3)
        uuid1 = context.addPatch(center=center, size=size, color=color)
        
        with PhotosynthesisModel(context) as photosynthesis:
            # Set initial coefficients so individual setters have something to work with
            from pyhelios.types import FarquharModelCoefficients
            initial_coeffs = FarquharModelCoefficients(
                Vcmax=80.0, Jmax=160.0, alpha=0.75, Rd=1.2
            )
            photosynthesis.setFarquharModelCoefficients(initial_coeffs, [uuid1])
            
            # Test basic parameter setting (now requires UUIDs)
            photosynthesis.setVcmax(100.0, [uuid1])
            photosynthesis.setJmax(180.0, [uuid1])
            photosynthesis.setDarkRespiration(2.0, [uuid1])
            photosynthesis.setQuantumEfficiency(0.85, [uuid1])
            photosynthesis.setLightResponseCurvature(0.7, [uuid1])
            
            # Each setter must actually store its value, not merely avoid raising.
            coeffs = FarquharModelCoefficients.from_array(
                photosynthesis.getFarquharModelCoefficients(uuid1))
            assert coeffs.getVcmaxTempResponse().value_at_25C == pytest.approx(100.0, abs=1e-4)
            assert coeffs.getJmaxTempResponse().value_at_25C == pytest.approx(180.0, abs=1e-4)
            assert coeffs.getRdTempResponse().value_at_25C == pytest.approx(2.0, abs=1e-4)
            assert coeffs.getQuantumEfficiencyTempResponse().value_at_25C == pytest.approx(0.85, abs=1e-4)
            assert photosynthesis.getLightResponseCurvature(uuid1) == pytest.approx(0.7, abs=1e-4)

            # Test with temperature response parameters
            photosynthesis.setVcmax(100.0, [uuid1], dha=65000.0, topt=25.0, dhd=200000.0)
            photosynthesis.setJmax(180.0, [uuid1], dha=43000.0, topt=25.0, dhd=200000.0)

            vcmax = FarquharModelCoefficients.from_array(
                photosynthesis.getFarquharModelCoefficients(uuid1)).getVcmaxTempResponse()
            assert vcmax.dHa == pytest.approx(65000.0, rel=1e-4)
            assert vcmax.dHd == pytest.approx(200000.0, rel=1e-4)
    
    @pytest.mark.native_only
    def test_parameter_persistence_critical(self):
        """
        CRITICAL: Test that individual parameter setters preserve other parameters.
        
        This test verifies the fix for the critical bug where individual parameter
        setters were overwriting all other parameters with defaults.
        """
        context = Context()
        
        # Add test primitive
        from pyhelios.types import vec3, vec2, RGBcolor
        center = vec3(0, 0, 0)
        size = vec2(1, 1)
        color = RGBcolor(0.5, 0.8, 0.3)
        uuid1 = context.addPatch(center=center, size=size, color=color)
        
        with PhotosynthesisModel(context) as photosynthesis:
            # Set explicit Farquhar coefficients first to establish known baseline
            from pyhelios.types import FarquharModelCoefficients
            initial_coeffs = FarquharModelCoefficients(
                Vcmax=120.0,   # μmol m⁻² s⁻¹
                Jmax=200.0,    # μmol m⁻² s⁻¹  
                alpha=0.8,     # mol electrons/mol photons
                Rd=1.5         # μmol m⁻² s⁻¹
            )
            photosynthesis.setFarquharModelCoefficients(initial_coeffs, [uuid1])
            
            # Get baseline coefficients for verification
            baseline_coeffs = photosynthesis.getFarquharModelCoefficients(uuid1)
            assert len(baseline_coeffs) >= 18, "Should have at least 18 Farquhar coefficients"
            
            # Store original values for verification
            original_vcmax = baseline_coeffs[0]   # Vcmax
            original_jmax = baseline_coeffs[1]    # Jmax  
            original_alpha = baseline_coeffs[2]   # alpha
            original_rd = baseline_coeffs[3]      # Rd
            
            # Verify we have the expected initial values
            assert abs(original_vcmax - 120.0) < 0.01, f"Initial Vcmax should be 120.0, got {original_vcmax}"
            assert abs(original_jmax - 200.0) < 0.01, f"Initial Jmax should be 200.0, got {original_jmax}"
            assert abs(original_alpha - 0.8) < 0.01, f"Initial alpha should be 0.8, got {original_alpha}"
            assert abs(original_rd - 1.5) < 0.01, f"Initial Rd should be 1.5, got {original_rd}"
            
            # TEST 1: Modify Vcmax, verify other parameters preserved
            new_vcmax = 150.0
            photosynthesis.setVcmax(new_vcmax, [uuid1])
            
            coeffs_after_vcmax = photosynthesis.getFarquharModelCoefficients(uuid1)
            assert abs(coeffs_after_vcmax[0] - new_vcmax) < 0.01, f"Vcmax not set correctly: {coeffs_after_vcmax[0]} != {new_vcmax}"
            assert abs(coeffs_after_vcmax[1] - original_jmax) < 0.01, f"Jmax was overwritten! {coeffs_after_vcmax[1]} != {original_jmax}"
            assert abs(coeffs_after_vcmax[2] - original_alpha) < 0.01, f"Alpha was overwritten! {coeffs_after_vcmax[2]} != {original_alpha}"
            assert abs(coeffs_after_vcmax[3] - original_rd) < 0.01, f"Rd was overwritten! {coeffs_after_vcmax[3]} != {original_rd}"
            
            # TEST 2: Modify Jmax, verify Vcmax and others preserved  
            new_jmax = 250.0
            photosynthesis.setJmax(new_jmax, [uuid1])
            
            coeffs_after_jmax = photosynthesis.getFarquharModelCoefficients(uuid1)
            assert abs(coeffs_after_jmax[0] - new_vcmax) < 0.01, f"Vcmax was overwritten! {coeffs_after_jmax[0]} != {new_vcmax}"
            assert abs(coeffs_after_jmax[1] - new_jmax) < 0.01, f"Jmax not set correctly: {coeffs_after_jmax[1]} != {new_jmax}"
            assert abs(coeffs_after_jmax[2] - original_alpha) < 0.01, f"Alpha was overwritten! {coeffs_after_jmax[2]} != {original_alpha}"
            assert abs(coeffs_after_jmax[3] - original_rd) < 0.01, f"Rd was overwritten! {coeffs_after_jmax[3]} != {original_rd}"
            
            # TEST 3: Modify Rd, verify Vcmax, Jmax, and alpha preserved
            new_rd = 5.0
            photosynthesis.setDarkRespiration(new_rd, [uuid1])
            
            coeffs_after_rd = photosynthesis.getFarquharModelCoefficients(uuid1)
            assert abs(coeffs_after_rd[0] - new_vcmax) < 0.01, f"Vcmax was overwritten! {coeffs_after_rd[0]} != {new_vcmax}"
            assert abs(coeffs_after_rd[1] - new_jmax) < 0.01, f"Jmax was overwritten! {coeffs_after_rd[1]} != {new_jmax}"
            assert abs(coeffs_after_rd[2] - original_alpha) < 0.01, f"Alpha was overwritten! {coeffs_after_rd[2]} != {original_alpha}"
            assert abs(coeffs_after_rd[3] - new_rd) < 0.01, f"Rd not set correctly: {coeffs_after_rd[3]} != {new_rd}"
            
            # TEST 4: Modify alpha, verify all previous changes preserved
            new_alpha = 0.95
            photosynthesis.setQuantumEfficiency(new_alpha, [uuid1])
            
            coeffs_after_alpha = photosynthesis.getFarquharModelCoefficients(uuid1)
            assert abs(coeffs_after_alpha[0] - new_vcmax) < 0.01, f"Vcmax was overwritten! {coeffs_after_alpha[0]} != {new_vcmax}"
            assert abs(coeffs_after_alpha[1] - new_jmax) < 0.01, f"Jmax was overwritten! {coeffs_after_alpha[1]} != {new_jmax}"
            assert abs(coeffs_after_alpha[2] - new_alpha) < 0.01, f"Alpha not set correctly: {coeffs_after_alpha[2]} != {new_alpha}"
            assert abs(coeffs_after_alpha[3] - new_rd) < 0.01, f"Rd was overwritten! {coeffs_after_alpha[3]} != {new_rd}"
            
            print("✓ CRITICAL TEST PASSED: Individual parameter setters preserve existing parameters!")
            
    def test_model_execution(self):
        """Test model execution methods."""
        from pyhelios.types import vec3, vec2

        context = Context()
        uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))

        with PhotosynthesisModel(context) as photosynthesis:
            # Configure model first
            coeffs = EmpiricalModelCoefficients()
            photosynthesis.setEmpiricalModelCoefficients(coeffs)
            
            # Run model
            photosynthesis.run()

        # run() must write its default output for every primitive.
        assert context.doesPrimitiveDataExist(uuid, "net_photosynthesis")
            
    def test_primitive_specific_operations(self):
        """Test operations with specific primitives."""
        context = Context()
        
        # Add some primitives to context
        from pyhelios.types import vec3, vec2, RGBcolor
        center = vec3(0, 0, 0)
        size = vec2(1, 1)
        color = RGBcolor(0.5, 0.8, 0.3)
        
        uuid1 = context.addPatch(center=center, size=size, color=color)
        uuid2 = context.addPatch(center=vec3(1, 1, 1), size=size, color=color)
        
        with PhotosynthesisModel(context) as photosynthesis:
            # Configure coefficients for specific primitives
            coeffs = EmpiricalModelCoefficients()
            photosynthesis.setEmpiricalModelCoefficients(coeffs, uuids=[uuid1, uuid2])
            
            # Run for specific primitives
            photosynthesis.runForPrimitives([uuid1, uuid2])
            photosynthesis.runForPrimitives(uuid1)  # Single primitive

        for uuid in (uuid1, uuid2):
            assert context.doesPrimitiveDataExist(uuid, "net_photosynthesis")
            
    def test_coefficient_retrieval(self):
        """Test getting coefficients for primitives."""
        context = Context()
        
        # Add a primitive
        from pyhelios.types import vec3, vec2, RGBcolor
        center = vec3(0, 0, 0)
        size = vec2(1, 1)
        color = RGBcolor(0.5, 0.8, 0.3)
        
        uuid = context.addPatch(center=center, size=size, color=color)
        
        with PhotosynthesisModel(context) as photosynthesis:
            # Set coefficients
            empirical_coeffs = EmpiricalModelCoefficients()
            photosynthesis.setEmpiricalModelCoefficients(empirical_coeffs)
            
            farquhar_coeffs = FarquharModelCoefficients(Vcmax=100.0, Jmax=180.0)
            photosynthesis.setFarquharModelCoefficients(farquhar_coeffs)
            
            # Get coefficients
            retrieved_empirical = photosynthesis.getEmpiricalModelCoefficients(uuid)
            retrieved_farquhar = photosynthesis.getFarquharModelCoefficients(uuid)
            
            assert isinstance(retrieved_empirical, list)
            assert isinstance(retrieved_farquhar, list)
            assert len(retrieved_empirical) > 0
            assert len(retrieved_farquhar) > 0
            
    def test_model_utilities(self):
        """Test model utility methods."""
        from pyhelios.types import vec3, vec2

        context = Context()
        uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))

        with PhotosynthesisModel(context) as photosynthesis:
            # Test message control
            photosynthesis.enableMessages()
            photosynthesis.disableMessages()
            
            # Test reporting
            photosynthesis.printModelReport()
            
            # Test export
            photosynthesis.exportResults("test_data")
            
            # Test validation
            is_valid = photosynthesis.validateConfiguration()
            assert isinstance(is_valid, bool)
            assert is_valid  # Should have valid pointer
            
            # resetModel() must restore the library defaults, not merely avoid raising.
            photosynthesis.setFarquharModelCoefficients(
                FarquharModelCoefficients(Vcmax=123.0, Jmax=180.0))
            assert photosynthesis.getFarquharModelCoefficients(uuid)[0] == pytest.approx(123.0)

            photosynthesis.resetModel()
            assert photosynthesis.getFarquharModelCoefficients(uuid)[0] != pytest.approx(123.0)


@pytest.mark.cross_platform
class TestPhotosynthesisValidationDecorators:
    """Test validation decorators work properly."""
    
    def test_species_validation_decorator(self):
        """Test species validation decorator."""
        from pyhelios.validation.plugin_decorators import validate_photosynthesis_species_params
        
        @validate_photosynthesis_species_params
        def dummy_method(self, species):
            return species
            
        # Valid species
        result = dummy_method(None, "Apple")
        assert result == "Apple"
        
        # Invalid species should raise ValidationError
        with pytest.raises(ValidationError):
            dummy_method(None, "INVALID_SPECIES")
            
    def test_uuid_validation_decorator(self):
        """Test UUID validation decorator."""
        from pyhelios.validation.plugin_decorators import validate_photosynthesis_uuid_params
        
        @validate_photosynthesis_uuid_params  
        def dummy_method(self, uuids):
            return uuids
            
        # Valid single UUID
        result = dummy_method(None, 123)
        assert result == 123
        
        # Valid UUID list
        result = dummy_method(None, [123, 456, 789])
        assert result == [123, 456, 789]
        
        # Invalid UUID should raise ValidationError
        with pytest.raises(ValidationError):
            dummy_method(None, "not_an_int")


@pytest.mark.cross_platform
class TestPhotosynthesisParameterValidation:
    """Test all parameter validation functions work correctly."""
    
    def test_species_validation_ranges(self):
        """Test species name validation with various values."""
        # Valid species
        assert validate_species_name("Apple") == "Apple"
        assert validate_species_name("apple") == "Apple"  # Case insensitive
        assert validate_species_name("Grape") == "Grape"
        
        # Invalid species
        with pytest.raises(ValueError):
            validate_species_name("INVALID_SPECIES")
            
        with pytest.raises(ValueError):
            validate_species_name("")
            
    def test_empirical_coefficients_structure(self):
        """Test empirical model coefficients structure."""
        # Valid coefficients
        coeffs = EmpiricalModelCoefficients()
        assert hasattr(coeffs, 'Tref')
        assert hasattr(coeffs, 'Asat')
        assert hasattr(coeffs, 'to_array')
        
        # Test array conversion
        arr = coeffs.to_array()
        assert isinstance(arr, list)
        assert len(arr) == 10
        
    def test_farquhar_coefficients_structure(self):
        """Test Farquhar model coefficients structure."""
        # Valid coefficients
        coeffs = FarquharModelCoefficients()
        assert hasattr(coeffs, 'Vcmax')
        assert hasattr(coeffs, 'Jmax')
        assert coeffs.Vcmax == -1.0  # Uninitialized default

    def test_peaked_response_rejects_dhd_not_exceeding_dha(self):
        """dHd <= dHa is undefined for the peaked Arrhenius form and must be rejected.

        Mirrors validateDeactivationEnergy added in helios-core 1.3.80. Before it, the
        response returned NaN and propagated it into net_photosynthesis with no diagnostic.
        """
        with pytest.raises(ValueError, match="strictly greater"):
            PhotosyntheticTemperatureResponseParameters(100.0, dHa=60.0, dHd=60.0, Topt=310.0)

        with pytest.raises(ValueError, match="strictly greater"):
            PhotosyntheticTemperatureResponseParameters(100.0, dHa=60.0, dHd=30.0, Topt=310.0)

        # dHa <= 0 applies no Arrhenius term, so dHd is unused and must not be rejected.
        PhotosyntheticTemperatureResponseParameters(100.0, dHa=0.0, dHd=0.0, Topt=310.0)
        # The default 10*dHa relationship stays valid.
        PhotosyntheticTemperatureResponseParameters(100.0, dHa=60.0, dHd=600.0, Topt=310.0)

    def test_empirical_coefficients_reject_degenerate_temperature_response(self):
        """Coefficient sets that make the f_T reference denominator zero must be rejected.

        helios-core 1.3.80 made the Tmin/Topt/Tref/q coefficients live (previously inert).
        These two combinations give an infinite or NaN assimilation rate.
        """
        # Tref <= Tmin
        with pytest.raises(ValueError, match="must be greater than the minimum"):
            EmpiricalModelCoefficients(Tref=290.0, Tmin=290.0, Topt=303.0)

        # (1+q)*Topt - Tmin - q*Tref == 0, chosen so Tmin < Topt still holds.
        # With q=1: 2*Topt - Tmin - Tref == 0 -> Tref = 2*Topt - Tmin.
        with pytest.raises(ValueError, match="degenerate"):
            EmpiricalModelCoefficients(Tmin=290.0, Topt=303.0, q=1.0, Tref=316.0)

        # The defaults must remain valid.
        EmpiricalModelCoefficients()


# ============================================================================
# C4 Photosynthesis Bindings (helios-core v1.3.72+)
# ============================================================================


@pytest.mark.cross_platform
class TestC4ConstantsAndImports:
    """Cross-platform sanity checks that the C4 + gm bindings are exposed."""

    def test_c4_species_constant_exposed(self):
        from pyhelios import AVAILABLE_C4_SPECIES
        assert AVAILABLE_C4_SPECIES == [
            "SetariaViridis_vC2021",
            "GenericC4_vC2000",
            "Maize_Massad2007",
        ]

    def test_c4_methods_present_on_class(self):
        # The high-level methods should be visible on PhotosynthesisModel even when
        # the native library is mocked, so callers see a NotImplementedError rather
        # than AttributeError.
        for name in (
            "setModelTypeC4",
            "setC4CoefficientsFromLibrary",
            "getC4CoefficientsFromLibrary",
            "setC4ModelCoefficients",
            "getC4ModelCoefficients",
            "setCm",
            "setFarquharMesophyllConductance",
        ):
            assert hasattr(PhotosynthesisModel, name), f"Missing PhotosynthesisModel.{name}"


@pytest.mark.native_only
class TestC4PhotosynthesisNative:
    """End-to-end checks for the C4 + Farquhar gm bindings (require native build)."""

    C4_COEFF_LEN = 43

    def test_get_c4_library_returns_43_floats(self):
        context = Context()
        with PhotosynthesisModel(context) as photo:
            coeffs = photo.getC4CoefficientsFromLibrary("SetariaViridis_vC2021")
            assert isinstance(coeffs, list)
            assert len(coeffs) == self.C4_COEFF_LEN
            # Vpmax_at_25C (index 0) must be positive for Setaria — paper Table 1: 200.
            assert coeffs[0] > 0.0
            # Vcmax_at_25C (index 4): paper value 40
            assert coeffs[4] > 0.0
            # gm_at_25C (index 16): paper value 1
            assert coeffs[16] > 0.0
            # Kc_25 (index 20): 1210 ubar
            assert coeffs[20] > 100.0

    def test_set_model_type_c4_then_run(self):
        from pyhelios.types import vec3, vec2, RGBcolor

        context = Context()
        uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1),
                                 color=RGBcolor(0.3, 0.7, 0.2))
        # Required inputs for the C4 solver (matching the existing FvCB tests):
        context.setPrimitiveDataFloat(uuid, "radiation_flux_PAR", 1.5e-3)  # W/m^2
        context.setPrimitiveDataFloat(uuid, "air_temperature", 298.0)
        context.setPrimitiveDataFloat(uuid, "air_CO2", 400.0)
        context.setPrimitiveDataFloat(uuid, "moisture_conductance", 0.4)

        with PhotosynthesisModel(context) as photo:
            photo.setModelTypeC4()
            photo.setC4CoefficientsFromLibrary("Maize_Massad2007")
            photo.run()
            # net_photosynthesis is a default output; just confirm it was written.
            assert context.doesPrimitiveDataExist(uuid, "net_photosynthesis")

    def test_round_trip_c4_coefficients_via_array(self):
        from pyhelios.types import vec3, vec2, RGBcolor

        context = Context()
        uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1),
                                 color=RGBcolor(0.3, 0.7, 0.2))

        with PhotosynthesisModel(context) as photo:
            photo.setModelTypeC4()
            library_coeffs = photo.getC4CoefficientsFromLibrary("SetariaViridis_vC2021")
            photo.setC4ModelCoefficients(library_coeffs, [uuid])
            roundtrip = photo.getC4ModelCoefficients(uuid)
            assert len(roundtrip) == self.C4_COEFF_LEN
            # Per-rate value_at_25C must round-trip exactly (slots 0, 4, 8, 12, 16).
            for idx in (0, 4, 8, 12, 16):
                assert roundtrip[idx] == pytest.approx(library_coeffs[idx], rel=1e-5)

    def test_set_cm_bypasses_iteration(self):
        from pyhelios.types import vec3, vec2, RGBcolor

        context = Context()
        uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1),
                                 color=RGBcolor(0.3, 0.7, 0.2))
        context.setPrimitiveDataFloat(uuid, "radiation_flux_PAR", 1.5e-3)
        context.setPrimitiveDataFloat(uuid, "air_temperature", 298.0)
        context.setPrimitiveDataFloat(uuid, "air_CO2", 400.0)
        context.setPrimitiveDataFloat(uuid, "moisture_conductance", 0.4)

        with PhotosynthesisModel(context) as photo:
            photo.setModelTypeC4()
            photo.setC4CoefficientsFromLibrary("SetariaViridis_vC2021")
            photo.setCm(150.0, [uuid])
            # Should run without raising.
            photo.run()

    def test_set_c4_coefficients_by_material(self):
        """Verify the per-material C4 setter (helios-core 1.3.72)."""
        from pyhelios.types import vec3, vec2, RGBcolor

        context = Context()
        uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1),
                                 color=RGBcolor(0.3, 0.7, 0.2))
        # Tag the primitive with a material label so the per-material setter has a target.
        material = "leaf_c4"
        context.addMaterial(material)
        context.assignMaterialToPrimitive(uuid, material)

        with PhotosynthesisModel(context) as photo:
            photo.setModelTypeC4()
            photo.setC4CoefficientsFromLibrary("Maize_Massad2007", material_label=material)

            # Mutually exclusive: passing both uuids and material_label must raise.
            with pytest.raises(ValueError):
                photo.setC4CoefficientsFromLibrary("Maize_Massad2007",
                                                    uuids=[uuid], material_label=material)

            # Round-trip via the array API also accepts material_label.
            arr = photo.getC4CoefficientsFromLibrary("SetariaViridis_vC2021")
            photo.setC4ModelCoefficients(arr, material_label=material)

    def test_set_farquhar_mesophyll_conductance(self):
        from pyhelios.types import vec3, vec2, RGBcolor

        context = Context()
        uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1),
                                 color=RGBcolor(0.3, 0.7, 0.2))
        context.setPrimitiveDataFloat(uuid, "radiation_flux_PAR", 1.5e-3)
        context.setPrimitiveDataFloat(uuid, "air_temperature", 298.0)
        context.setPrimitiveDataFloat(uuid, "air_CO2", 400.0)
        context.setPrimitiveDataFloat(uuid, "moisture_conductance", 0.4)

        with PhotosynthesisModel(context) as photo:
            photo.setModelTypeFarquhar()
            photo.setFarquharCoefficientsFromLibrary("APPLE", uuids=[uuid])
            # gm only (no temperature response).
            photo.setFarquharMesophyllConductance(0.4, uuids=[uuid])
            photo.run()

    def test_farquhar_gm_roundtrip_through_array(self):
        """Verify the 22-float array round-trip preserves the mesophyll-conductance gm.

        Regression test: prior to v0.1.21 the flat array was 18 floats and silently
        dropped gm on round-trip, resetting it to +infinity each time
        ``setFarquharModelCoefficients`` was called with a buffer fetched via
        ``getFarquharModelCoefficients``.
        """
        from pyhelios.types import vec3, vec2, RGBcolor

        context = Context()
        uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1),
                                 color=RGBcolor(0.3, 0.7, 0.2))

        with PhotosynthesisModel(context) as photo:
            photo.setModelTypeFarquhar()
            photo.setFarquharCoefficientsFromLibrary("APPLE", uuids=[uuid])
            # Set a finite gm with a small dHa so it travels through the array layout.
            photo.setFarquharMesophyllConductance(0.4, dha=49.6, uuids=[uuid])

            # 42-element layout: slots 18..21 are (gm_at_25C, dHa, Topt_C, dHd); slots
            # 38..41 carry the light response curvature theta.
            arr = photo.getFarquharModelCoefficients(uuid)
            assert len(arr) == 42
            assert arr[18] == pytest.approx(0.4, abs=1e-4)
            assert arr[19] == pytest.approx(49.6, abs=1e-4)
            # Topt was not set, so it must round-trip as the "no optimum" sentinel (-1).
            assert arr[20] < 0.0

    def test_species_library_returns_real_rates_not_sentinels(self):
        """Library species must report their actual Vcmax/Jmax/alpha/Rd, not -1 sentinels.

        Regression test for helios-core 1.3.80: every entry in the C++ species library is
        populated via ``setVcmax()``/``setJmax()``/``setRd()``/``setQuantumEfficiency_alpha()``,
        and as of 1.3.80 those setters stamp the deprecated scalar fields
        (``FarquharModelCoefficients::Vcmax`` etc.) to the -1 sentinel so that the
        temperature-response object is unambiguously authoritative. The PyHelios wrapper read
        slots 0..3 straight from those deprecated fields, so after the bump every species
        reported Vcmax = Jmax = alpha = Rd = -1.
        """
        with PhotosynthesisModel(Context()) as photo:
            for species in ("almond", "apple", "walnut"):
                coeffs = photo.getSpeciesCoefficients(species)
                assert coeffs[0] > 0.0, f"{species}: Vcmax is {coeffs[0]}, expected a positive rate"
                assert coeffs[1] > 0.0, f"{species}: Jmax is {coeffs[1]}, expected a positive rate"
                assert coeffs[2] > 0.0, f"{species}: alpha is {coeffs[2]}, expected a positive value"
                assert coeffs[3] > 0.0, f"{species}: Rd is {coeffs[3]}, expected a positive rate"

    def test_peaked_temperature_response_survives_library_roundtrip(self):
        """A peaked (4-parameter) temperature response must survive get/set through the array.

        Regression test for helios-core 1.3.80: Almond, Walnut and PistachioFemale were
        re-fitted to use the peaked Arrhenius form with TPU limitation. Slots 0..3 of the flat
        array carried only the rate value, so reading a peaked species and writing it back
        collapsed it to a bare constant — silently discarding dHa/Topt/dHd. The extended
        layout carries the full (value, dHa, Topt_C, dHd) block for each rate.
        """
        from pyhelios.types import vec3, vec2, RGBcolor

        context = Context()
        uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1),
                                color=RGBcolor(0.3, 0.7, 0.2))

        with PhotosynthesisModel(context) as photo:
            photo.setModelTypeFarquhar()
            photo.setFarquharCoefficientsFromLibrary("almond", uuids=[uuid])

            before = photo.getFarquharModelCoefficients(uuid)
            # Slots 22..25 are the Vcmax response block (value, dHa, Topt_C, dHd).
            # Almond is peaked: Vcmax(72.6, dHa=27.3, Topt=42.15 C, dHd=478.4).
            assert before[0] == pytest.approx(72.6, abs=0.5)
            assert before[22] == pytest.approx(72.6, abs=0.5), "Vcmax value lost"
            assert before[23] == pytest.approx(27.3, abs=0.5), "Vcmax dHa lost"
            assert before[24] == pytest.approx(42.15, abs=0.5), "Vcmax Topt lost"
            assert before[25] == pytest.approx(478.4, abs=1.0), "Vcmax dHd lost"

            # Round-trip unchanged: read, write back, read again.
            photo.setFarquharModelCoefficients(
                FarquharModelCoefficients.from_array(before), [uuid])
            after = photo.getFarquharModelCoefficients(uuid)

            for slot, name in ((0, "Vcmax"), (23, "Vcmax dHa"),
                               (24, "Vcmax Topt"), (25, "Vcmax dHd")):
                assert after[slot] == pytest.approx(before[slot], abs=1e-3), \
                    f"{name} changed across round-trip: {before[slot]} -> {after[slot]}"

    def test_rate_response_blocks_are_not_transposed(self):
        """Each rate's temperature-response block must land in its own slots.

        Slots 22..37 are four 4-float blocks in the order Vcmax, Jmax, Rd, alpha. An
        off-by-four in either the pack or the unpack would silently swap two rates — most
        likely Rd and alpha, which are adjacent and both small — while every length and
        finiteness check still passed. Distinct sentinel values per rate make a swap visible.
        """
        from pyhelios.types import vec3, vec2, RGBcolor

        context = Context()
        uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1),
                                color=RGBcolor(0.3, 0.7, 0.2))

        with PhotosynthesisModel(context) as photo:
            photo.setModelTypeFarquhar()
            photo.setFarquharCoefficientsFromLibrary("apple", uuids=[uuid])

            # Deliberately distinct per rate so a transposition cannot coincide.
            photo.setVcmax(111.0, [uuid], dha=61.0, topt=41.0, dhd=611.0)
            photo.setJmax(222.0, [uuid], dha=62.0, topt=42.0, dhd=622.0)
            photo.setDarkRespiration(3.3, [uuid], dha=63.0, topt=43.0, dhd=633.0)
            photo.setQuantumEfficiency(0.44, [uuid], dha=64.0, topt=44.0, dhd=644.0)

            arr = photo.getFarquharModelCoefficients(uuid)
            expected = {
                "Vcmax": (22, 111.0, 61.0, 41.0, 611.0),
                "Jmax": (26, 222.0, 62.0, 42.0, 622.0),
                "Rd": (30, 3.3, 63.0, 43.0, 633.0),
                "alpha": (34, 0.44, 64.0, 44.0, 644.0),
            }
            for name, (base, value, dha, topt, dhd) in expected.items():
                assert arr[base] == pytest.approx(value, abs=1e-2), f"{name} value in wrong slot"
                assert arr[base + 1] == pytest.approx(dha, abs=1e-2), f"{name} dHa in wrong slot"
                assert arr[base + 2] == pytest.approx(topt, abs=1e-2), f"{name} Topt in wrong slot"
                assert arr[base + 3] == pytest.approx(dhd, abs=1e-2), f"{name} dHd in wrong slot"



@pytest.mark.native_only
class TestLightResponseCurvatureIsApplied:
    """setLightResponseCurvature() must actually write theta.

    The method used to read each primitive's coefficients and write them straight back with the
    curvature line commented out, so it silently did nothing: no error, and every subsequent run
    used the default theta. A wrong theta changes the shape of the A-Q curve at intermediate
    light without making the output look obviously wrong.
    """

    @staticmethod
    def _make_primitive():
        from pyhelios.types import vec3, vec2
        context = Context()
        uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        return context, uuid

    def test_curvature_round_trips(self):
        """The value set must be the value read back."""
        context, uuid = self._make_primitive()
        with PhotosynthesisModel(context) as model:
            model.setFarquharCoefficientsFromLibrary('Almond', [uuid])

            default_theta = model.getLightResponseCurvature(uuid)
            model.setLightResponseCurvature(0.42, [uuid])
            assert model.getLightResponseCurvature(uuid) == pytest.approx(0.42, abs=1e-5), (
                "setLightResponseCurvature() did not change the stored theta"
            )
            assert default_theta != pytest.approx(0.42, abs=1e-5), (
                "test is vacuous: the library default already equals the value under test"
            )

    def test_curvature_temperature_response_round_trips(self):
        """dha/topt/dhd select the peaked overload and must not be dropped."""
        context, uuid = self._make_primitive()
        with PhotosynthesisModel(context) as model:
            model.setFarquharCoefficientsFromLibrary('Almond', [uuid])

            model.setLightResponseCurvature(0.55, [uuid], dha=45000.0, topt=28.0, dhd=200000.0)

            response = model.getLightResponseCurvatureTempResponse(uuid)
            assert response.value_at_25C == pytest.approx(0.55, abs=1e-5)
            assert response.dHa == pytest.approx(45000.0, rel=1e-4)
            assert response.dHd == pytest.approx(200000.0, rel=1e-4)

    def test_curvature_applies_to_only_the_listed_primitives(self):
        """A UUID left out of the list keeps its original theta."""
        from pyhelios.types import vec3, vec2
        context = Context()
        target = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        untouched = context.addPatch(center=vec3(2, 0, 0), size=vec2(1, 1))

        with PhotosynthesisModel(context) as model:
            model.setFarquharCoefficientsFromLibrary('Almond', [target, untouched])
            original = model.getLightResponseCurvature(untouched)

            model.setLightResponseCurvature(0.31, [target])

            assert model.getLightResponseCurvature(target) == pytest.approx(0.31, abs=1e-5)
            assert model.getLightResponseCurvature(untouched) == pytest.approx(original, abs=1e-5)


if __name__ == "__main__":
    pytest.main([__file__])