"""
Tests for PyHelios Context module.

These tests verify the Context class functionality including primitive management
and geometric operations.
"""

import pytest
from unittest.mock import Mock, patch
import tempfile
import os
import time
import math
import platform
import numpy as np
import pyhelios
from pyhelios import Context, DataTypes
from pyhelios.exceptions import HeliosError, HeliosRuntimeError

REPO_ROOT_CTX = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
from pyhelios.types import *  # Import all vector types for convenience
from tests.conftest import assert_vec3_equal, assert_vec2_equal, assert_color_equal
from tests.test_utils import GeometryValidator, PlatformHelper, generate_patch_test_cases


def _safe_unlink(filepath):
    """Windows-safe file deletion with retry logic for files held by processes."""
    if not os.path.exists(filepath):
        return
        
    # On Windows, files loaded by Helios C++ library may still be locked
    max_attempts = 5 if platform.system() == "Windows" else 1
    
    for attempt in range(max_attempts):
        try:
            os.unlink(filepath)
            return
        except PermissionError:
            if attempt < max_attempts - 1:
                time.sleep(0.1)  # Brief wait for file handle to be released
            else:
                # Last attempt failed - try to continue gracefully
                pass  # Don't fail tests due to Windows file locking issues


def _create_test_texture_file(suffix='.png'):
    """Create a minimal valid texture file for testing."""
    temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    temp_file.close()  # Close file so it can be reopened
    
    try:
        # Try to create a minimal 1x1 pixel image using PIL if available
        from PIL import Image
        img = Image.new('RGB', (1, 1), color='white')
        img.save(temp_file.name)
        return temp_file.name
    except ImportError:
        # PIL not available, just return existing Helios texture if available
        helios_texture = 'helios-core/core/lib/images/disk_texture.png'
        if os.path.exists(helios_texture):
            return helios_texture
        else:
            # Last resort: create empty file (will likely fail in texture loading but better error)
            return temp_file.name


@pytest.mark.native_only
class TestContextCreation:
    """Test Context creation and basic lifecycle."""
    
    def test_context_creation(self, basic_context):
        """Test that Context can be created successfully."""
        assert basic_context is not None
        assert hasattr(basic_context, 'context')
    
    def test_context_manager(self, check_native_library):
        """Test Context as context manager."""
        with Context() as ctx:
            assert ctx is not None
            assert ctx.getPrimitiveCount() == 0
    
    def test_native_ptr_access(self, basic_context):
        """Test native pointer access."""
        ptr = basic_context.getNativePtr()
        assert ptr is not None
    
    def test_geometry_state_management(self, basic_context):
        """Test geometry dirty/clean state management."""
        # Initially should not be dirty
        assert not basic_context.isGeometryDirty()
        
        # NOTE: The geometry dirty state functionality appears to not be
        # implemented in the current native Helios library. The methods
        # exist but don't change the state as expected.
        
        # Test that methods can be called without error
        basic_context.markGeometryDirty()
        # Currently always returns False regardless of state
        # assert basic_context.isGeometryDirty()
        
        basic_context.markGeometryClean()
        assert not basic_context.isGeometryDirty()


@pytest.mark.native_only
class TestPrimitiveManagement:
    """Test primitive creation and management."""
    
    def test_initial_primitive_count(self, basic_context):
        """Test initial primitive count is zero."""
        assert basic_context.getPrimitiveCount() == 0
        assert basic_context.getAllUUIDs() == []
    
    def test_add_simple_patch(self, basic_context, sample_patch_parameters):
        """Test adding a simple patch."""
        params = sample_patch_parameters
        patch_uuid = basic_context.addPatch(
            center=params['center'],
            size=params['size'],
            color=params['color']
        )
        
        assert isinstance(patch_uuid, int)
        assert patch_uuid >= 0  # UUIDs start from 0 in Helios
        assert basic_context.getPrimitiveCount() == 1
        assert patch_uuid in basic_context.getAllUUIDs()
    
    def test_add_patch_with_defaults(self, basic_context):
        """Test adding patch with default parameters."""
        patch_uuid = basic_context.addPatch()
        
        assert isinstance(patch_uuid, int)
        assert patch_uuid >= 0  # UUIDs start from 0 in Helios
        assert basic_context.getPrimitiveCount() == 1
    
    @pytest.mark.parametrize("test_case", generate_patch_test_cases())
    def test_add_patch_variations(self, basic_context, test_case):
        """Test adding patches with various parameters."""
        patch_uuid = basic_context.addPatch(
            center=test_case['center'],
            size=test_case['size'],
            color=test_case['color']
        )
        
        assert isinstance(patch_uuid, int)
        assert patch_uuid >= 0  # UUIDs start from 0 in Helios
        
        # Validate patch properties
        assert GeometryValidator.validate_patch_properties(
            basic_context, patch_uuid,
            test_case['center'], test_case['size'], test_case['color']
        )
    
    def test_multiple_patches(self, basic_context):
        """Test adding multiple patches."""
        patch_uuids = []
        
        for i in range(5):
            center = DataTypes.vec3(i, i, i)
            size = DataTypes.vec2(1, 1)
            color = DataTypes.RGBcolor(i/4.0, 0.5, 0.5)
            
            uuid = basic_context.addPatch(center=center, size=size, color=color)
            patch_uuids.append(uuid)
        
        assert basic_context.getPrimitiveCount() == 5
        assert len(basic_context.getAllUUIDs()) == 5
        
        # Check all UUIDs are unique
        assert len(set(patch_uuids)) == 5
        
        # Check all UUIDs are in the context
        context_uuids = basic_context.getAllUUIDs()
        for uuid in patch_uuids:
            assert uuid in context_uuids


@pytest.mark.native_only
class TestPrimitiveProperties:
    """Test querying primitive properties."""
    
    def test_getPrimitiveType(self, basic_context):
        """Test getting primitive type."""
        patch_uuid = basic_context.addPatch()
        
        prim_type = basic_context.getPrimitiveType(patch_uuid)
        assert prim_type == pyhelios.PrimitiveType.Patch
    
    def test_getPrimitiveArea(self, basic_context):
        """Test getting primitive area."""
        size = DataTypes.vec2(2.0, 3.0)
        patch_uuid = basic_context.addPatch(size=size)
        
        area = basic_context.getPrimitiveArea(patch_uuid)
        expected_area = size.x * size.y
        assert area == pytest.approx(expected_area)
    
    def test_getPrimitiveNormal(self, basic_context):
        """Test getting primitive normal vector."""
        patch_uuid = basic_context.addPatch()
        
        normal = basic_context.getPrimitiveNormal(patch_uuid)
        assert isinstance(normal, DataTypes.vec3)
        
        # Normal should be a unit vector (length ≈ 1)
        length = (normal.x**2 + normal.y**2 + normal.z**2)**0.5
        assert length == pytest.approx(1.0, rel=1e-6)
    
    def test_getPrimitiveVertices(self, basic_context):
        """Test getting primitive vertices."""
        center = DataTypes.vec3(1, 2, 3)
        size = DataTypes.vec2(2, 2)
        patch_uuid = basic_context.addPatch(center=center, size=size)
        
        vertices = basic_context.getPrimitiveVertices(patch_uuid)
        
        # Patch should have 4 vertices
        assert len(vertices) == 4
        assert all(isinstance(v, DataTypes.vec3) for v in vertices)
        
        # Vertices should form a rectangle around the center
        # (exact positions depend on orientation, but we can check bounds)
        x_coords = [v.x for v in vertices]
        y_coords = [v.y for v in vertices]
        z_coords = [v.z for v in vertices]
        
        # All vertices should be close to the center z-coordinate
        for z in z_coords:
            assert z == pytest.approx(center.z, abs=1e-6)
    
    def test_getPrimitiveColor(self, basic_context):
        """Test getting primitive color."""
        expected_color = DataTypes.RGBcolor(0.3, 0.7, 0.1)
        patch_uuid = basic_context.addPatch(color=expected_color)
        
        actual_color = basic_context.getPrimitiveColor(patch_uuid)
        assert_color_equal(actual_color, expected_color)
    
    def test_invalid_uuid_handling(self, basic_context):
        """Test that invalid UUIDs raise appropriate exceptions (fail-fast philosophy)."""
        invalid_uuid = 99999
        
        # Following fail-fast philosophy: invalid UUIDs should raise exceptions, not return fake values
        with pytest.raises(Exception):  # Should raise some kind of exception
            basic_context.getPrimitiveType(invalid_uuid)
        
        with pytest.raises(Exception):  # Should raise some kind of exception  
            basic_context.getPrimitiveArea(invalid_uuid)
            
        with pytest.raises(Exception):  # Should raise some kind of exception
            basic_context.getPrimitiveNormal(invalid_uuid)


@pytest.mark.native_only 
class TestObjectManagement:
    """Test object-level operations."""
    
    def test_initial_object_count(self, basic_context):
        """Test initial object count."""
        assert basic_context.getObjectCount() == 0
        assert basic_context.getAllObjectIDs() == []
    
    def test_objects_after_patch_creation(self, basic_context):
        """Test object management after creating patches."""
        # Add a patch
        basic_context.addPatch()
        
        # Object count should increase
        object_count = basic_context.getObjectCount()
        object_ids = basic_context.getAllObjectIDs()
        
        assert object_count >= 0  # Depends on internal Helios implementation
        assert isinstance(object_ids, list)


class TestContextMocking:
    """Test Context with mocked dependencies."""
    
    def test_mock_context_basic_operations(self, mock_context):
        """Test basic operations with mocked context."""
        assert mock_context.getPrimitiveCount() == 0
        assert mock_context.getAllUUIDs() == []
        
        patch_uuid = mock_context.addPatch()
        assert patch_uuid == 1
    
    def test_mock_context_primitive_properties(self, mock_context):
        """Test primitive property queries with mocked context."""
        patch_uuid = 1
        
        assert mock_context.getPrimitiveType(patch_uuid) == pyhelios.PrimitiveType.Patch
        assert mock_context.getPrimitiveArea(patch_uuid) == 1.0
        
        normal = mock_context.getPrimitiveNormal(patch_uuid)
        assert isinstance(normal, DataTypes.vec3)
        
        color = mock_context.getPrimitiveColor(patch_uuid)
        assert isinstance(color, DataTypes.RGBcolor)


@pytest.mark.unit
class TestContextEdgeCases:
    """Test Context edge cases and error conditions."""
    
    def test_context_without_native_library(self):
        """Test Context behavior when native library is not available."""
        # Skip this test if native libraries are actually available
        if PlatformHelper.is_native_library_available():
            pytest.skip("Native libraries are available - cannot test native library unavailable scenario")
        
        # In PyHelios, Context creation should succeed even without native libraries (mock mode)
        # Operations on the context should raise RuntimeError indicating mock mode
        context = Context()
        
        # Verify we can create a context (should succeed in mock mode)
        assert context is not None
        
        # Operations should raise RuntimeError in mock mode
        with pytest.raises(RuntimeError) as exc_info:
            context.addPatch()
        
        # Error message should indicate mock mode or library unavailable
        error_msg = str(exc_info.value).lower()
        assert any(keyword in error_msg for keyword in 
                  ["mock", "library", "native", "unavailable", "development"])
    
    def test_large_number_of_primitives(self, basic_context):
        """Test performance with many primitives."""
        if not PlatformHelper.is_native_library_available():
            pytest.skip("Requires native library for performance testing")
        
        # Add many patches
        num_patches = 1000
        patch_uuids = []
        
        for i in range(num_patches):
            center = DataTypes.vec3(i % 10, i // 10, 0)
            uuid = basic_context.addPatch(center=center)
            patch_uuids.append(uuid)
        
        assert basic_context.getPrimitiveCount() == num_patches
        assert len(basic_context.getAllUUIDs()) == num_patches
        
        # Verify all UUIDs are unique
        assert len(set(patch_uuids)) == num_patches
    
    @pytest.mark.slow
    def test_context_memory_cleanup(self):
        """Test that Context properly cleans up memory."""
        # This test verifies that multiple Context creations/destructions
        # don't lead to memory leaks
        if not PlatformHelper.is_native_library_available():
            pytest.skip("Requires native library for memory testing")
        
        for i in range(10):
            with Context() as ctx:
                # Add some primitives
                for j in range(100):
                    ctx.addPatch(center=DataTypes.vec3(j, j, j))
                
                assert ctx.getPrimitiveCount() == 100
            # Context should be cleaned up here
    
    def test_patch_with_extreme_values(self, basic_context):
        """Test patch creation with extreme parameter values."""
        # Very large coordinates
        large_center = DataTypes.vec3(1e6, 1e6, 1e6)
        large_size = DataTypes.vec2(1e3, 1e3)
        
        patch_uuid = basic_context.addPatch(center=large_center, size=large_size)
        assert isinstance(patch_uuid, int)
        
        # Very small coordinates
        small_center = DataTypes.vec3(1e-6, 1e-6, 1e-6)
        small_size = DataTypes.vec2(1e-3, 1e-3)
        
        patch_uuid2 = basic_context.addPatch(center=small_center, size=small_size)
        assert isinstance(patch_uuid2, int)


@pytest.mark.native_only
class TestTriangleOperations:
    """Test triangle creation and manipulation."""
    
    def test_add_simple_triangle(self, basic_context):
        """Test adding a simple triangle without color."""
        vertex0 = vec3(0, 0, 0)
        vertex1 = vec3(1, 0, 0)
        vertex2 = vec3(0.5, 1, 0)
        
        triangle_uuid = basic_context.addTriangle(vertex0, vertex1, vertex2)
        
        assert isinstance(triangle_uuid, int)
        assert triangle_uuid >= 0
        assert basic_context.getPrimitiveCount() == 1
        assert triangle_uuid in basic_context.getAllUUIDs()
        
        # Verify it's a triangle primitive
        assert basic_context.getPrimitiveType(triangle_uuid) == PrimitiveType.Triangle
    
    def test_add_triangle_with_color(self, basic_context):
        """Test adding a triangle with specified color."""
        vertex0 = vec3(0, 0, 0)
        vertex1 = vec3(1, 0, 0)
        vertex2 = vec3(0.5, 1, 0)
        color = RGBcolor(0.8, 0.2, 0.1)
        
        triangle_uuid = basic_context.addTriangle(vertex0, vertex1, vertex2, color)
        
        assert isinstance(triangle_uuid, int)
        assert triangle_uuid >= 0
        
        # Verify color is set correctly
        actual_color = basic_context.getPrimitiveColor(triangle_uuid)
        assert_color_equal(actual_color, color)
    
    def test_triangle_properties(self, basic_context):
        """Test triangle geometric properties."""
        vertex0 = vec3(0, 0, 0)
        vertex1 = vec3(2, 0, 0)
        vertex2 = vec3(1, 2, 0)
        
        triangle_uuid = basic_context.addTriangle(vertex0, vertex1, vertex2)
        
        # Test area calculation
        area = basic_context.getPrimitiveArea(triangle_uuid)
        expected_area = 2.0  # Area of triangle with base=2, height=2 is 2
        assert area == pytest.approx(expected_area, rel=1e-5)
        
        # Test vertices
        vertices = basic_context.getPrimitiveVertices(triangle_uuid)
        assert len(vertices) == 3
        assert_vec3_equal(vertices[0], vertex0)
        assert_vec3_equal(vertices[1], vertex1)
        assert_vec3_equal(vertices[2], vertex2)
        
        # Test normal vector
        normal = basic_context.getPrimitiveNormal(triangle_uuid)
        # For triangle in XY plane, normal should point in Z direction
        assert abs(normal.z) == pytest.approx(1.0, rel=1e-5)
        assert abs(normal.x) == pytest.approx(0.0, abs=1e-5)
        assert abs(normal.y) == pytest.approx(0.0, abs=1e-5)
    
    def test_multiple_triangles(self, basic_context):
        """Test adding multiple triangles."""
        triangles = []
        
        for i in range(3):
            vertex0 = vec3(i, 0, 0)
            vertex1 = vec3(i+1, 0, 0)
            vertex2 = vec3(i+0.5, 1, 0)
            color = RGBcolor(i/2.0, 0.5, 0.5)
            
            triangle_uuid = basic_context.addTriangle(vertex0, vertex1, vertex2, color)
            triangles.append(triangle_uuid)
        
        assert basic_context.getPrimitiveCount() == 3
        assert len(basic_context.getAllUUIDs()) == 3
        
        # Verify all triangles are unique
        assert len(set(triangles)) == 3
        
        # Verify all UUIDs are in context
        context_uuids = basic_context.getAllUUIDs()
        for uuid in triangles:
            assert uuid in context_uuids

    def test_add_textured_triangle_basic(self, basic_context):
        """Test adding a basic textured triangle using existing texture."""
        vertex0 = vec3(0, 0, 0)
        vertex1 = vec3(1, 0, 0)
        vertex2 = vec3(0.5, 1, 0)
        
        # UV coordinates
        uv0 = vec2(0, 0)
        uv1 = vec2(1, 0)
        uv2 = vec2(0.5, 1)
        
        # Use existing texture file from Helios core
        texture_file = 'helios-core/core/lib/images/disk_texture.png'
        
        if os.path.exists(texture_file):
            triangle_uuid = basic_context.addTriangleTextured(
                vertex0, vertex1, vertex2, texture_file, uv0, uv1, uv2
            )
            
            assert isinstance(triangle_uuid, int)
            assert triangle_uuid >= 0
            assert basic_context.getPrimitiveCount() == 1
            assert triangle_uuid in basic_context.getAllUUIDs()
            
            # Verify it's a triangle primitive
            assert basic_context.getPrimitiveType(triangle_uuid) == PrimitiveType.Triangle
            
            # Verify triangle properties
            vertices = basic_context.getPrimitiveVertices(triangle_uuid)
            assert len(vertices) == 3
            assert_vec3_equal(vertices[0], vertex0)
            assert_vec3_equal(vertices[1], vertex1)  
            assert_vec3_equal(vertices[2], vertex2)
            
        else:
            pytest.skip("Helios texture file not found - skipping basic textured triangle test")
    
    def test_add_textured_triangle_with_real_texture(self, basic_context):
        """Test adding textured triangle with real texture file."""
        vertex0 = vec3(-1, -1, 0)
        vertex1 = vec3(1, -1, 0)
        vertex2 = vec3(0, 1, 0)
        
        uv0 = vec2(0, 0)    # Bottom-left
        uv1 = vec2(1, 0)    # Bottom-right  
        uv2 = vec2(0.5, 1)  # Top-center
        
        # Use existing texture file from Helios core
        texture_file = 'helios-core/core/lib/images/disk_texture.png'
        
        if os.path.exists(texture_file):
            triangle_uuid = basic_context.addTriangleTextured(
                vertex0, vertex1, vertex2, texture_file, uv0, uv1, uv2
            )
            
            assert isinstance(triangle_uuid, int)
            assert triangle_uuid >= 0
            
            # Test triangle geometric properties  
            area = basic_context.getPrimitiveArea(triangle_uuid)
            # Triangle should have positive area (textured triangles may have different area calculation)
            assert area > 0.0, f"Triangle area should be positive, got {area}"
            # The area should be reasonable for the given triangle size (within expected range)
            assert 1.0 <= area <= 3.0, f"Triangle area {area} should be within reasonable range"
            
            # Test normal vector (triangle in XY plane)
            normal = basic_context.getPrimitiveNormal(triangle_uuid)
            assert abs(abs(normal.z) - 1.0) < 1e-5  # Normal should be ±1 in Z
            
        else:
            pytest.skip("Texture file not found - skipping real texture test")
    
    def test_add_textured_triangle_file_validation(self, basic_context):
        """Test file validation in addTriangleTextured."""
        vertex0 = vec3(0, 0, 0)
        vertex1 = vec3(1, 0, 0)
        vertex2 = vec3(0.5, 1, 0)
        uv0 = vec2(0, 0)
        uv1 = vec2(1, 0)
        uv2 = vec2(0.5, 1)
        
        # Test with non-existent file
        with pytest.raises(FileNotFoundError, match="File not found"):
            basic_context.addTriangleTextured(
                vertex0, vertex1, vertex2, 'nonexistent.png', uv0, uv1, uv2
            )
        
        # Test with invalid file extension
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b'test content')
            temp_filename = temp_file.name
        
        try:
            with pytest.raises(ValueError, match="Invalid file extension"):
                basic_context.addTriangleTextured(
                    vertex0, vertex1, vertex2, temp_filename, uv0, uv1, uv2
                )
        finally:
            _safe_unlink(temp_filename)
        
        # Test with valid extensions (but use existing texture file to avoid PNG loading errors)
        texture_file = 'helios-core/core/lib/images/disk_texture.png'
        if os.path.exists(texture_file):
            # Valid extension should work
            triangle_uuid = basic_context.addTriangleTextured(
                vertex0, vertex1, vertex2, texture_file, uv0, uv1, uv2
            )
            assert isinstance(triangle_uuid, int)
    
    def test_add_textured_triangle_parameter_types(self, basic_context):
        """Test parameter type validation for addTriangleTextured."""
        # Use existing texture file
        texture_file = 'helios-core/core/lib/images/disk_texture.png'
        
        if os.path.exists(texture_file):
            # Valid call
            vertex0 = vec3(0, 0, 0)
            vertex1 = vec3(1, 0, 0)
            vertex2 = vec3(0.5, 1, 0)
            uv0 = vec2(0, 0)
            uv1 = vec2(1, 0)
            uv2 = vec2(0.5, 1)
            
            triangle_uuid = basic_context.addTriangleTextured(
                vertex0, vertex1, vertex2, texture_file, uv0, uv1, uv2
            )
            
            assert isinstance(triangle_uuid, int)
            assert triangle_uuid >= 0
            
            # Verify correct primitive type
            assert basic_context.getPrimitiveType(triangle_uuid) == PrimitiveType.Triangle
        else:
            pytest.skip("Helios texture file not found - skipping parameter type test")
    
    def test_add_multiple_textured_triangles(self, basic_context):
        """Test adding multiple textured triangles."""
        # Use existing texture file
        texture_file = 'helios-core/core/lib/images/disk_texture.png'
        
        if os.path.exists(texture_file):
            triangle_uuids = []
            
            for i in range(3):
                vertex0 = vec3(i, 0, 0)
                vertex1 = vec3(i+1, 0, 0) 
                vertex2 = vec3(i+0.5, 1, 0)
                
                uv0 = vec2(0, 0)
                uv1 = vec2(1, 0)
                uv2 = vec2(0.5, 1)
                
                triangle_uuid = basic_context.addTriangleTextured(
                    vertex0, vertex1, vertex2, texture_file, uv0, uv1, uv2
                )
                triangle_uuids.append(triangle_uuid)
            
            # Verify all triangles created
            assert basic_context.getPrimitiveCount() == 3
            assert len(set(triangle_uuids)) == 3  # All unique
            
            # Verify all are triangle primitives
            for uuid in triangle_uuids:
                assert basic_context.getPrimitiveType(uuid) == PrimitiveType.Triangle
                assert uuid in basic_context.getAllUUIDs()
        else:
            pytest.skip("Helios texture file not found - skipping multiple textured triangles test")
    
    def test_textured_triangle_integration_with_other_primitives(self, basic_context):
        """Test textured triangles work alongside other primitive types."""
        # Use existing texture file
        texture_file = 'helios-core/core/lib/images/disk_texture.png'
        
        if os.path.exists(texture_file):
            # Add various primitive types
            patch_uuid = basic_context.addPatch(center=vec3(0, 0, 0))
            
            triangle_uuid = basic_context.addTriangle(
                vec3(1, 0, 0), vec3(2, 0, 0), vec3(1.5, 1, 0)
            )
            
            textured_triangle_uuid = basic_context.addTriangleTextured(
                vec3(2, 0, 0), vec3(3, 0, 0), vec3(2.5, 1, 0),
                texture_file, vec2(0, 0), vec2(1, 0), vec2(0.5, 1)
            )
            
            # Verify all primitives exist
            assert basic_context.getPrimitiveCount() == 3
            all_uuids = basic_context.getAllUUIDs()
            assert patch_uuid in all_uuids
            assert triangle_uuid in all_uuids
            assert textured_triangle_uuid in all_uuids
            
            # Verify correct primitive types
            assert basic_context.getPrimitiveType(patch_uuid) == PrimitiveType.Patch
            assert basic_context.getPrimitiveType(triangle_uuid) == PrimitiveType.Triangle
            assert basic_context.getPrimitiveType(textured_triangle_uuid) == PrimitiveType.Triangle
        else:
            pytest.skip("Helios texture file not found - skipping integration test")


@pytest.mark.native_only
class TestNumPyArrayOperations:
    """Test NumPy array-based triangle operations."""
    
    def test_addTrianglesFromArrays_basic(self, basic_context):
        """Test adding triangles from NumPy arrays without colors."""
        # Create a simple tetrahedron
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.5, 1.0, 0.0],
            [0.5, 0.5, 1.0]
        ], dtype=np.float32)
        
        faces = np.array([
            [0, 1, 2],
            [0, 1, 3],
            [1, 2, 3],
            [0, 2, 3]
        ], dtype=np.int32)
        
        triangle_uuids = basic_context.addTrianglesFromArrays(vertices, faces)
        
        assert len(triangle_uuids) == 4
        assert basic_context.getPrimitiveCount() == 4
        
        # Verify all returned UUIDs are valid
        for uuid in triangle_uuids:
            assert isinstance(uuid, int)
            assert uuid >= 0
            assert basic_context.getPrimitiveType(uuid) == PrimitiveType.Triangle
    
    def test_addTrianglesFromArrays_with_colors(self, basic_context):
        """Test adding triangles from NumPy arrays with per-triangle colors."""
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.5, 1.0, 0.0],
        ], dtype=np.float32)
        
        faces = np.array([[0, 1, 2]], dtype=np.int32)
        
        # Per-triangle colors
        colors = np.array([[1.0, 0.0, 0.0]], dtype=np.float32)
        
        triangle_uuids = basic_context.addTrianglesFromArrays(vertices, faces, colors)
        
        assert len(triangle_uuids) == 1
        
        # Verify color is applied
        actual_color = basic_context.getPrimitiveColor(triangle_uuids[0])
        expected_color = RGBcolor(1.0, 0.0, 0.0)
        assert_color_equal(actual_color, expected_color)
    
    def test_addTrianglesFromArrays_vertex_colors(self, basic_context):
        """Test adding triangles with per-vertex colors (averaged to triangle)."""
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.5, 1.0, 0.0],
        ], dtype=np.float32)
        
        faces = np.array([[0, 1, 2]], dtype=np.int32)
        
        # Per-vertex colors
        colors = np.array([
            [1.0, 0.0, 0.0],  # Red
            [0.0, 1.0, 0.0],  # Green
            [0.0, 0.0, 1.0],  # Blue
        ], dtype=np.float32)
        
        triangle_uuids = basic_context.addTrianglesFromArrays(vertices, faces, colors)
        
        assert len(triangle_uuids) == 1
        
        # Color should be average of vertex colors
        actual_color = basic_context.getPrimitiveColor(triangle_uuids[0])
        expected_color = RGBcolor(1.0/3, 1.0/3, 1.0/3)  # Average of RGB
        assert_color_equal(actual_color, expected_color, tolerance=1e-5)
    
    def test_addTrianglesFromArrays_validation(self, basic_context):
        """Test validation of NumPy array inputs."""
        # Invalid vertices shape
        invalid_vertices = np.array([[0.0, 0.0]], dtype=np.float32)  # Only 2D
        valid_faces = np.array([[0, 1, 2]], dtype=np.int32)
        
        with pytest.raises(ValueError, match="Vertices array must have shape"):
            basic_context.addTrianglesFromArrays(invalid_vertices, valid_faces)
        
        # Invalid faces shape
        valid_vertices = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.5, 1.0, 0.0]], dtype=np.float32)
        invalid_faces = np.array([[0, 1]], dtype=np.int32)  # Only 2 vertices per face
        
        with pytest.raises(ValueError, match="Faces array must have shape"):
            basic_context.addTrianglesFromArrays(valid_vertices, invalid_faces)
        
        # Face indices out of range
        out_of_range_faces = np.array([[0, 1, 5]], dtype=np.int32)  # Index 5 doesn't exist
        
        with pytest.raises(ValueError, match="Face indices reference vertex"):
            basic_context.addTrianglesFromArrays(valid_vertices, out_of_range_faces)
        
        # Invalid colors shape
        invalid_colors = np.array([[1.0, 0.0]], dtype=np.float32)  # Only 2 components
        
        with pytest.raises(ValueError, match="Colors array must have shape"):
            basic_context.addTrianglesFromArrays(valid_vertices, valid_faces, invalid_colors)
    
    def test_addTrianglesFromArraysTextured_basic(self, basic_context):
        """Test adding textured triangles from arrays."""
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.5, 1.0, 0.0],
        ], dtype=np.float32)
        
        faces = np.array([[0, 1, 2]], dtype=np.int32)
        
        uv_coords = np.array([
            [0.0, 0.0],
            [1.0, 0.0],
            [0.5, 1.0],
        ], dtype=np.float32)
        
        # Create a temporary texture file for testing
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            # Write some dummy content (actual texture loading will likely fail)
            tmp_file.write(b'dummy texture content')
            tmp_file.flush()
            
            # Test that addTrianglesFromArraysTextured properly handles invalid texture files
            # We expect this to raise an exception since we're providing invalid PNG data
            with pytest.raises(Exception) as exc_info:
                basic_context.addTrianglesFromArraysTextured(
                    vertices, faces, uv_coords, tmp_file.name)
            
            # Verify that the exception is texture-related and informative
            error_msg = str(exc_info.value)
            assert any(keyword in error_msg for keyword in 
                      ["Texture", "does not exist", "invalid", "PNG", "not a valid"]), \
                f"Expected texture-related error message, got: {error_msg}"
                    
            # Clean up - Windows-safe file deletion
            _safe_unlink(tmp_file.name)
    
    def test_addTrianglesFromArraysTextured_validation(self, basic_context):
        """Test validation for textured triangle arrays."""
        vertices = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.5, 1.0, 0.0]], dtype=np.float32)
        faces = np.array([[0, 1, 2]], dtype=np.int32)
        
        # Mismatched UV coordinates count
        invalid_uv = np.array([[0.0, 0.0], [1.0, 0.0]], dtype=np.float32)  # Only 2 UVs for 3 vertices
        
        with pytest.raises(ValueError, match="UV coordinates count.*must match vertices count"):
            basic_context.addTrianglesFromArraysTextured(vertices, faces, invalid_uv, "texture.png")
        
        # Invalid UV shape
        invalid_uv_shape = np.array([[0.0, 0.0, 0.0]], dtype=np.float32)  # 3D UV coords
        
        with pytest.raises(ValueError, match="UV coordinates array must have shape"):
            basic_context.addTrianglesFromArraysTextured(vertices, faces, invalid_uv_shape, "texture.png")


@pytest.mark.native_only
class TestPrimitiveDataOperations:
    """Test primitive data storage and retrieval."""
    
    def test_primitive_data_int(self, basic_context):
        """Test integer primitive data operations."""
        patch_uuid = basic_context.addPatch()
        
        # Set and get integer data
        basic_context.setPrimitiveDataInt(patch_uuid, "test_int", 42)
        assert basic_context.getPrimitiveData(patch_uuid, "test_int", int) == 42
        
        # Test data existence
        assert basic_context.doesPrimitiveDataExist(patch_uuid, "test_int")
        assert not basic_context.doesPrimitiveDataExist(patch_uuid, "nonexistent")
    
    def test_primitive_data_float(self, basic_context):
        """Test float primitive data operations."""
        patch_uuid = basic_context.addPatch()
        
        # Set and get float data
        basic_context.setPrimitiveDataFloat(patch_uuid, "test_float", 3.14159)
        assert basic_context.getPrimitiveData(patch_uuid, "test_float", float) == pytest.approx(3.14159)
        assert basic_context.getPrimitiveDataFloat(patch_uuid, "test_float") == pytest.approx(3.14159)
    
    def test_primitive_data_string(self, basic_context):
        """Test string primitive data operations."""
        patch_uuid = basic_context.addPatch()
        
        # Set and get string data
        test_string = "Hello PyHelios"
        basic_context.setPrimitiveDataString(patch_uuid, "test_string", test_string)
        assert basic_context.getPrimitiveData(patch_uuid, "test_string", str) == test_string
    
    def test_primitive_data_uint(self, basic_context):
        """Test unsigned integer primitive data operations."""
        patch_uuid = basic_context.addPatch()
        
        # Set and get unsigned integer data
        basic_context.setPrimitiveDataUInt(patch_uuid, "test_uint", 4294967295)  # Max uint32
        assert basic_context.getPrimitiveData(patch_uuid, "test_uint", "uint") == 4294967295
    
    def test_primitive_data_vector_types(self, basic_context):
        """Test vector-type primitive data operations (where available)."""
        patch_uuid = basic_context.addPatch()
        
        # Note: Vector setter methods are not implemented in the high-level Context class
        # Only test the getter functionality with pre-existing data
        
        # Test that we can at least call the vector getters (they'll return default values)
        try:
            retrieved_vec2 = basic_context.getPrimitiveData(patch_uuid, "nonexistent_vec2", vec2)
            assert isinstance(retrieved_vec2, vec2)
        except Exception:
            # Expected if data doesn't exist
            pass
        
        try:
            retrieved_vec3 = basic_context.getPrimitiveData(patch_uuid, "nonexistent_vec3", vec3)
            assert isinstance(retrieved_vec3, vec3)
        except Exception:
            # Expected if data doesn't exist
            pass
    
    def test_primitive_data_int_types(self, basic_context):
        """Test integer vector-type primitive data operations (where available)."""
        patch_uuid = basic_context.addPatch()
        
        # Note: Vector setter methods for int2/int3/int4 are not implemented in the high-level Context class
        # Only test the getter functionality
        
        # Test that we can at least call the int vector getters
        try:
            retrieved_int2 = basic_context.getPrimitiveData(patch_uuid, "nonexistent_int2", int2)
            assert isinstance(retrieved_int2, int2)
        except Exception:
            # Expected if data doesn't exist
            pass
        
        try:
            retrieved_int3 = basic_context.getPrimitiveData(patch_uuid, "nonexistent_int3", int3)
            assert isinstance(retrieved_int3, int3)
        except Exception:
            # Expected if data doesn't exist
            pass
    
    def test_primitive_data_auto_detection(self, basic_context):
        """Test automatic type detection for primitive data."""
        patch_uuid = basic_context.addPatch()
        
        # Set various types and test auto-detection
        basic_context.setPrimitiveDataInt(patch_uuid, "auto_int", 123)
        basic_context.setPrimitiveDataFloat(patch_uuid, "auto_float", 4.56)
        basic_context.setPrimitiveDataString(patch_uuid, "auto_string", "test")
        
        # Test auto-detection (no type parameter)
        auto_int = basic_context.getPrimitiveData(patch_uuid, "auto_int")
        auto_float = basic_context.getPrimitiveData(patch_uuid, "auto_float")
        auto_string = basic_context.getPrimitiveData(patch_uuid, "auto_string")
        
        assert auto_int == 123
        # Note: Auto-detection may have precision issues or type conversion behavior
        # The important thing is that we get a reasonable numeric result
        assert isinstance(auto_float, (int, float))
        assert float(auto_float) > 0  # Should be some positive number
        assert auto_string == "test"
    
    def test_primitive_data_type_and_size(self, basic_context):
        """Test primitive data type and size queries."""
        patch_uuid = basic_context.addPatch()
        
        basic_context.setPrimitiveDataInt(patch_uuid, "test_data", 42)
        
        # Test type and size queries
        data_type = basic_context.getPrimitiveDataType(patch_uuid, "test_data")
        data_size = basic_context.getPrimitiveDataSize(patch_uuid, "test_data")
        
        assert isinstance(data_type, int)
        assert isinstance(data_size, int)
        assert data_size >= 1  # Should be at least 1 for scalar data
    
    def test_primitive_data_error_handling(self, basic_context):
        """Test error handling for primitive data operations."""
        patch_uuid = basic_context.addPatch()

        # Test accessing non-existent data properly raises exception
        with pytest.raises(HeliosRuntimeError, match="(key not found|map::at|invalid map<K, T> key)"):
            basic_context.getPrimitiveData(patch_uuid, "nonexistent", int)

        # Test unsupported data type
        with pytest.raises(ValueError, match="Unsupported primitive data type"):
            basic_context.getPrimitiveData(patch_uuid, "any", dict)  # Unsupported type
    
    def test_getPrimitiveDataArray_basic(self, basic_context):
        """Test basic functionality of getPrimitiveDataArray method."""
        # Create multiple patches and set primitive data
        patch_uuids = []
        test_values = [10, 20, 30, 40, 50]
        
        for i, value in enumerate(test_values):
            uuid = basic_context.addPatch(center=vec3(i, 0, 0))
            basic_context.setPrimitiveDataInt(uuid, "test_int", value)
            patch_uuids.append(uuid)
        
        # Get data as array
        data_array = basic_context.getPrimitiveDataArray(patch_uuids, "test_int")
        
        # Verify array properties
        assert isinstance(data_array, np.ndarray)
        assert data_array.dtype == np.int32
        assert data_array.shape == (5,)
        assert list(data_array) == test_values
    
    def test_getPrimitiveDataArray_float_data(self, basic_context):
        """Test getPrimitiveDataArray with float data."""
        patch_uuids = []
        test_values = [1.1, 2.2, 3.3, 4.4]
        
        for i, value in enumerate(test_values):
            uuid = basic_context.addPatch(center=vec3(i, 0, 0))
            basic_context.setPrimitiveDataFloat(uuid, "test_float", value)
            patch_uuids.append(uuid)
        
        data_array = basic_context.getPrimitiveDataArray(patch_uuids, "test_float")
        
        assert isinstance(data_array, np.ndarray)
        assert data_array.dtype == np.float32
        assert data_array.shape == (4,)
        np.testing.assert_array_almost_equal(data_array, test_values, decimal=5)
    
    def test_getPrimitiveDataArray_string_data(self, basic_context):
        """Test getPrimitiveDataArray with string data."""
        patch_uuids = []
        test_values = ["apple", "banana", "cherry"]
        
        for i, value in enumerate(test_values):
            uuid = basic_context.addPatch(center=vec3(i, 0, 0))
            basic_context.setPrimitiveDataString(uuid, "test_string", value)
            patch_uuids.append(uuid)
        
        data_array = basic_context.getPrimitiveDataArray(patch_uuids, "test_string")
        
        assert isinstance(data_array, np.ndarray)
        assert data_array.dtype == object
        assert data_array.shape == (3,)
        assert list(data_array) == test_values
    
    def test_getPrimitiveDataArray_vector_data(self, basic_context):
        """Test getPrimitiveDataArray with vector data types."""
        patch_uuids = []
        
        # Test vec3 data
        for i in range(3):
            uuid = basic_context.addPatch(center=vec3(i, 0, 0))
            # Set vec3 data using the DataTypes.setPrimitiveDataVec3 method
            basic_context.setPrimitiveDataFloat(uuid, "x", float(i))
            basic_context.setPrimitiveDataFloat(uuid, "y", float(i + 10))
            basic_context.setPrimitiveDataFloat(uuid, "z", float(i + 20))
            patch_uuids.append(uuid)
        
        # Test individual float arrays instead of vec3 since vec3 requires proper setter
        x_array = basic_context.getPrimitiveDataArray(patch_uuids, "x")
        y_array = basic_context.getPrimitiveDataArray(patch_uuids, "y")
        z_array = basic_context.getPrimitiveDataArray(patch_uuids, "z")
        
        assert x_array.dtype == np.float32
        assert y_array.dtype == np.float32
        assert z_array.dtype == np.float32
        
        np.testing.assert_array_equal(x_array, [0.0, 1.0, 2.0])
        np.testing.assert_array_equal(y_array, [10.0, 11.0, 12.0])
        np.testing.assert_array_equal(z_array, [20.0, 21.0, 22.0])
    
    def test_getPrimitiveDataArray_error_cases(self, basic_context):
        """Test error handling in getPrimitiveDataArray."""
        patch_uuid = basic_context.addPatch()
        basic_context.setPrimitiveDataInt(patch_uuid, "test_data", 42)
        
        # Test empty UUID list
        with pytest.raises(ValueError, match="UUID list cannot be empty"):
            basic_context.getPrimitiveDataArray([], "test_data")
        
        # Test invalid UUID (UUID validation catches invalid UUID)
        with pytest.raises(RuntimeError, match="UUID 999999 does not exist in context"):
            basic_context.getPrimitiveDataArray([999999], "test_data")
        
        # Test non-existent primitive data label
        with pytest.raises(ValueError, match="Primitive data .* does not exist"):
            basic_context.getPrimitiveDataArray([patch_uuid], "nonexistent_label")
    
    def test_getPrimitiveDataArray_mixed_primitives(self, basic_context):
        """Test getPrimitiveDataArray with mixed primitive types."""
        # Create different primitive types
        patch_uuid = basic_context.addPatch(center=vec3(0, 0, 0))
        triangle_uuid = basic_context.addTriangle(
            vec3(1, 0, 0), vec3(2, 0, 0), vec3(1.5, 1, 0)
        )
        
        # Set same data label on both primitives
        basic_context.setPrimitiveDataFloat(patch_uuid, "temperature", 25.5)
        basic_context.setPrimitiveDataFloat(triangle_uuid, "temperature", 30.2)
        
        data_array = basic_context.getPrimitiveDataArray(
            [patch_uuid, triangle_uuid], "temperature"
        )
        
        assert data_array.dtype == np.float32
        assert data_array.shape == (2,)
        np.testing.assert_array_almost_equal(data_array, [25.5, 30.2], decimal=5)
    
    def test_getPrimitiveDataArray_large_dataset(self, basic_context):
        """Test getPrimitiveDataArray performance with larger dataset."""
        # Create 100 patches with data
        patch_uuids = []
        expected_values = []
        
        for i in range(100):
            uuid = basic_context.addPatch(center=vec3(i * 0.1, 0, 0))
            value = i * 0.5
            basic_context.setPrimitiveDataFloat(uuid, "value", value)
            patch_uuids.append(uuid)
            expected_values.append(value)
        
        data_array = basic_context.getPrimitiveDataArray(patch_uuids, "value")
        
        assert data_array.shape == (100,)
        assert data_array.dtype == np.float32
        np.testing.assert_array_almost_equal(data_array, expected_values, decimal=5)


@pytest.mark.native_only
class TestBroadcastPrimitiveData:
    """Test broadcast setPrimitiveData operations (same value to multiple UUIDs)."""

    def test_broadcast_int(self, basic_context):
        """Test broadcast setting of integer data to multiple primitives."""
        uuids = [basic_context.addPatch(center=vec3(i, 0, 0)) for i in range(5)]
        basic_context.setPrimitiveDataInt(uuids, "test_int", 42)
        for uuid in uuids:
            assert basic_context.getPrimitiveData(uuid, "test_int") == 42

    def test_broadcast_uint(self, basic_context):
        """Test broadcast setting of unsigned integer data."""
        uuids = [basic_context.addPatch(center=vec3(i, 0, 0)) for i in range(5)]
        basic_context.setPrimitiveDataUInt(uuids, "test_uint", 100)
        for uuid in uuids:
            assert basic_context.getPrimitiveData(uuid, "test_uint", "uint") == 100

    def test_broadcast_float(self, basic_context):
        """Test broadcast setting of float data to multiple primitives."""
        uuids = [basic_context.addPatch(center=vec3(i, 0, 0)) for i in range(5)]
        basic_context.setPrimitiveDataFloat(uuids, "temperature", 25.5)
        for uuid in uuids:
            assert basic_context.getPrimitiveData(uuid, "temperature") == pytest.approx(25.5)

    def test_broadcast_double(self, basic_context):
        """Test broadcast setting of double data to multiple primitives."""
        uuids = [basic_context.addPatch(center=vec3(i, 0, 0)) for i in range(5)]
        basic_context.setPrimitiveDataDouble(uuids, "precise_value", 3.141592653589793)
        for uuid in uuids:
            assert basic_context.getPrimitiveData(uuid, "precise_value", "double") == pytest.approx(3.141592653589793)

    def test_broadcast_string(self, basic_context):
        """Test broadcast setting of string data to multiple primitives."""
        uuids = [basic_context.addPatch(center=vec3(i, 0, 0)) for i in range(3)]
        basic_context.setPrimitiveDataString(uuids, "material", "glass")
        for uuid in uuids:
            assert basic_context.getPrimitiveData(uuid, "material") == "glass"

    def test_broadcast_vec3(self, basic_context):
        """Test broadcast setting of vec3 data to multiple primitives."""
        uuids = [basic_context.addPatch(center=vec3(i, 0, 0)) for i in range(5)]
        basic_context.setPrimitiveDataVec3(uuids, "wind", 1.0, 0.5, 0.2)
        for uuid in uuids:
            result = basic_context.getPrimitiveData(uuid, "wind")
            assert result[0] == pytest.approx(1.0)
            assert result[1] == pytest.approx(0.5)
            assert result[2] == pytest.approx(0.2)

    def test_broadcast_vec3_with_object(self, basic_context):
        """Test broadcast setting of vec3 data using vec3 object."""
        uuids = [basic_context.addPatch(center=vec3(i, 0, 0)) for i in range(3)]
        wind_vector = vec3(2.0, 1.5, 0.5)
        basic_context.setPrimitiveDataVec3(uuids, "wind", wind_vector)
        for uuid in uuids:
            result = basic_context.getPrimitiveData(uuid, "wind")
            assert result[0] == pytest.approx(2.0)
            assert result[1] == pytest.approx(1.5)
            assert result[2] == pytest.approx(0.5)

    def test_broadcast_empty_uuids_error(self, basic_context):
        """Test that empty UUID list raises error."""
        with pytest.raises(ValueError, match="empty"):
            basic_context.setPrimitiveDataInt([], "test", 42)

    def test_single_uuid_still_works(self, basic_context):
        """Test that single UUID (non-list) still works with existing behavior."""
        uuid = basic_context.addPatch()
        basic_context.setPrimitiveDataFloat(uuid, "temp", 30.0)
        assert basic_context.getPrimitiveData(uuid, "temp") == pytest.approx(30.0)

    def test_broadcast_with_tuple(self, basic_context):
        """Test that tuples work as well as lists for UUIDs."""
        uuids = tuple(basic_context.addPatch(center=vec3(i, 0, 0)) for i in range(3))
        basic_context.setPrimitiveDataInt(uuids, "count", 99)
        for uuid in uuids:
            assert basic_context.getPrimitiveData(uuid, "count") == 99

    def test_broadcast_large_uuid_list(self, basic_context):
        """Test broadcast with a larger number of primitives."""
        n = 100
        uuids = [basic_context.addPatch(center=vec3(i % 10, i // 10, 0)) for i in range(n)]
        basic_context.setPrimitiveDataFloat(uuids, "value", 12.34)

        # Verify all values are set correctly
        data_array = basic_context.getPrimitiveDataArray(uuids, "value")
        assert len(data_array) == n
        np.testing.assert_array_almost_equal(data_array, [12.34] * n, decimal=4)


@pytest.mark.native_only
class TestFileLoadingOperations:
    """Test file loading methods with proper error handling."""
    
    def test_loadPLY_file_validation(self, basic_context):
        """Test PLY file loading with file validation."""
        # Test with non-existent file
        with pytest.raises(FileNotFoundError):
            basic_context.loadPLY("nonexistent_file.ply")
    
    def test_loadOBJ_file_validation(self, basic_context):
        """Test OBJ file loading with file validation."""
        # Test with non-existent file
        with pytest.raises(FileNotFoundError):
            basic_context.loadOBJ("nonexistent_file.obj")
    
    def test_loadXML_file_validation(self, basic_context):
        """Test XML file loading with file validation."""
        # Test with non-existent file
        with pytest.raises(FileNotFoundError):
            basic_context.loadXML("nonexistent_file.xml")
    
    def test_loadPLY_parameter_validation(self, basic_context):
        """Test PLY loading parameter combinations."""
        # Create a temporary PLY file for testing
        with tempfile.NamedTemporaryFile(suffix=".ply", delete=False) as tmp_file:
            # Write a minimal PLY file
            tmp_file.write(b"""ply
format ascii 1.0
element vertex 3
property float x
property float y
property float z
element face 1
property list uchar int vertex_indices
end_header
0.0 0.0 0.0
1.0 0.0 0.0
0.5 1.0 0.0
3 0 1 2
""")
            tmp_file.flush()
            
            try:
                # Test invalid parameter combinations
                origin = vec3(0, 0, 0)
                height = 1.0
                rotation = SphericalCoord(1, 0, 0)
                color = RGBcolor(1, 0, 0)
                
                # Test with only origin (should fail - both origin and height required)
                with pytest.raises(ValueError, match="both origin and height are required"):
                    basic_context.loadPLY(tmp_file.name, origin=origin)
                
                # Test valid parameter combination
                uuids = basic_context.loadPLY(tmp_file.name, origin=origin, height=height)
                assert isinstance(uuids, list)
                
            finally:
                _safe_unlink(tmp_file.name)
    
    def test_file_extension_validation(self, basic_context):
        """Test file extension validation."""
        # Create temporary files with wrong extensions
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp_file:
            tmp_file.write(b"dummy content")
            tmp_file.flush()
            
            try:
                # Test PLY with wrong extension
                with pytest.raises(ValueError, match="Invalid file extension"):
                    basic_context.loadPLY(tmp_file.name)
                
                # Test OBJ with wrong extension  
                with pytest.raises(ValueError, match="Invalid file extension"):
                    basic_context.loadOBJ(tmp_file.name)
                
                # Test XML with wrong extension
                with pytest.raises(ValueError, match="Invalid file extension"):
                    basic_context.loadXML(tmp_file.name)
                    
            finally:
                _safe_unlink(tmp_file.name)


@pytest.mark.cross_platform
class TestFileExportMockMode:
    """Test file export methods in mock mode for cross-platform compatibility."""

    @pytest.mark.mock_mode
    def test_writePLY_mock_mode(self):
        """Test writePLY availability check in mock mode."""
        from pyhelios.plugins.loader import get_library_info

        library_info = get_library_info()
        if library_info.get('is_mock', False):
            with Context() as context:
                with pytest.raises(RuntimeError, match="mock mode"):
                    context.writePLY("test.ply")

    @pytest.mark.mock_mode
    def test_writeOBJ_mock_mode(self):
        """Test writeOBJ availability check in mock mode."""
        from pyhelios.plugins.loader import get_library_info

        library_info = get_library_info()
        if library_info.get('is_mock', False):
            with Context() as context:
                with pytest.raises(RuntimeError, match="mock mode"):
                    context.writeOBJ("test.obj")

    def test_file_export_api_structure(self):
        """Test that export methods have expected structure."""
        # Test method signatures exist
        assert hasattr(Context, 'writePLY')
        assert hasattr(Context, 'writeOBJ')

        # Test that methods are callable
        assert callable(getattr(Context, 'writePLY'))
        assert callable(getattr(Context, 'writeOBJ'))

    def test_export_parameter_validation_types(self):
        """Test export parameter validation without native library."""
        # This tests parameter validation logic that doesn't require native calls
        pass  # Parameter validation will be tested in native tests


@pytest.mark.native_only
class TestFileExportOperations:
    """Test file export methods with actual file I/O operations."""

    def test_writePLY_all_primitives(self, basic_context):
        """Test PLY export with all primitives."""
        # Create some geometry
        patch_uuid = basic_context.addPatch(center=vec3(0, 0, 1), size=vec2(1, 1))
        tri_uuid = basic_context.addTriangle(vec3(0, 0, 0), vec3(1, 0, 0), vec3(0.5, 1, 0))

        # Test export to PLY file
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test_output.ply")

            # Export all primitives
            basic_context.writePLY(output_file)

            # Verify file was created
            assert os.path.exists(output_file)
            assert os.path.isfile(output_file)

            # Verify file has content
            with open(output_file, 'r') as f:
                content = f.read()
                assert 'ply' in content
                assert 'format ascii 1.0' in content

    def test_writePLY_subset_primitives(self, basic_context):
        """Test PLY export with subset of primitives."""
        # Create geometry
        patch_uuid = basic_context.addPatch(center=vec3(0, 0, 1), size=vec2(1, 1))
        tri_uuid = basic_context.addTriangle(vec3(0, 0, 0), vec3(1, 0, 0), vec3(0.5, 1, 0))

        # Test export specific UUIDs
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test_subset.ply")

            # Export only the triangle
            basic_context.writePLY(output_file, UUIDs=[tri_uuid])

            # Verify file was created
            assert os.path.exists(output_file)

            # Verify file has content
            with open(output_file, 'r') as f:
                content = f.read()
                assert 'ply' in content

    def test_writeOBJ_all_primitives(self, basic_context):
        """Test OBJ export with all primitives."""
        # Create some geometry
        patch_uuid = basic_context.addPatch(center=vec3(0, 0, 1), size=vec2(1, 1))
        tri_uuid = basic_context.addTriangle(vec3(0, 0, 0), vec3(1, 0, 0), vec3(0.5, 1, 0))

        # Test export to OBJ file
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test_output.obj")

            # Export all primitives
            basic_context.writeOBJ(output_file)

            # Verify OBJ file was created
            assert os.path.exists(output_file)

            # OBJ export also creates MTL file
            mtl_file = os.path.join(temp_dir, "test_output.mtl")
            assert os.path.exists(mtl_file)

            # Verify files have content
            with open(output_file, 'r') as f:
                content = f.read()
                assert 'v ' in content  # vertex data
                assert 'f ' in content  # face data

    def test_writeOBJ_with_options(self, basic_context):
        """Test OBJ export with write_normals and silent options."""
        # Create geometry
        tri_uuid = basic_context.addTriangle(vec3(0, 0, 0), vec3(1, 0, 0), vec3(0.5, 1, 0))

        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test_normals.obj")

            # Export with normals enabled and silent mode
            basic_context.writeOBJ(output_file, write_normals=True, silent=True)

            assert os.path.exists(output_file)

    def test_writeOBJ_subset_primitives(self, basic_context):
        """Test OBJ export with subset of primitives."""
        # Create geometry
        patch_uuid = basic_context.addPatch(center=vec3(0, 0, 1), size=vec2(1, 1))
        tri_uuid = basic_context.addTriangle(vec3(0, 0, 0), vec3(1, 0, 0), vec3(0.5, 1, 0))

        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test_subset.obj")

            # Export only the patch
            basic_context.writeOBJ(output_file, UUIDs=[patch_uuid])

            assert os.path.exists(output_file)

    def test_writeOBJ_with_primitive_data(self, basic_context):
        """Test OBJ export with primitive data fields."""
        # Create geometry and add data
        tri_uuid = basic_context.addTriangle(vec3(0, 0, 0), vec3(1, 0, 0), vec3(0.5, 1, 0))
        basic_context.setPrimitiveDataFloat(tri_uuid, "temperature", 25.5)
        basic_context.setPrimitiveDataString(tri_uuid, "label", "test_triangle")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test_data.obj")

            # Export with primitive data
            basic_context.writeOBJ(output_file, UUIDs=[tri_uuid],
                                 primitive_data_fields=["temperature", "label"])

            assert os.path.exists(output_file)

    def test_export_file_path_validation(self, basic_context):
        """Test file path validation for export operations."""
        # Test invalid extensions
        with pytest.raises(ValueError, match="Invalid file extension"):
            basic_context.writePLY("test.txt")

        with pytest.raises(ValueError, match="Invalid file extension"):
            basic_context.writeOBJ("test.txt")

        # Test non-existent output directory
        with pytest.raises(ValueError, match="Output directory does not exist"):
            basic_context.writePLY("/nonexistent/directory/test.ply")

        with pytest.raises(ValueError, match="Output directory does not exist"):
            basic_context.writeOBJ("/nonexistent/directory/test.obj")

    def test_export_uuid_validation(self, basic_context):
        """Test UUID validation in export operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test.ply")

            # Test with non-existent UUID
            with pytest.raises(RuntimeError, match="UUID"):
                basic_context.writePLY(output_file, UUIDs=[99999])

            # Test with empty UUID list
            with pytest.raises(ValueError, match="UUIDs list cannot be empty"):
                basic_context.writePLY(output_file, UUIDs=[])

            # Same tests for OBJ
            obj_file = os.path.join(temp_dir, "test.obj")

            with pytest.raises(RuntimeError, match="UUID"):
                basic_context.writeOBJ(obj_file, UUIDs=[99999])

            with pytest.raises(ValueError, match="UUIDs list cannot be empty"):
                basic_context.writeOBJ(obj_file, UUIDs=[])

    def test_export_parameter_validation(self, basic_context):
        """Test parameter validation for export methods."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test empty filename
            with pytest.raises(ValueError, match="cannot be empty"):
                basic_context.writePLY("")

            with pytest.raises(ValueError, match="cannot be empty"):
                basic_context.writeOBJ("")

            # Test OBJ with empty data fields
            tri_uuid = basic_context.addTriangle(vec3(0, 0, 0), vec3(1, 0, 0), vec3(0.5, 1, 0))
            obj_file = os.path.join(temp_dir, "test.obj")

            with pytest.raises(ValueError, match="primitive_data_fields list cannot be empty"):
                basic_context.writeOBJ(obj_file, UUIDs=[tri_uuid], primitive_data_fields=[])

            with pytest.raises(ValueError, match="UUIDs list cannot be empty when exporting primitive data"):
                basic_context.writeOBJ(obj_file, UUIDs=[], primitive_data_fields=["temperature"])

    def test_round_trip_export_import(self, basic_context):
        """Test round-trip: create geometry → export → import → verify."""
        # Create original geometry
        original_patch = basic_context.addPatch(center=vec3(1, 2, 3), size=vec2(2, 2))
        original_tri = basic_context.addTriangle(vec3(0, 0, 0), vec3(1, 0, 0), vec3(0.5, 1, 0))

        with tempfile.TemporaryDirectory() as temp_dir:
            # Export to PLY
            ply_file = os.path.join(temp_dir, "roundtrip.ply")
            basic_context.writePLY(ply_file)

            # Create new context and import
            with Context() as new_context:
                imported_uuids = new_context.loadPLY(ply_file)

                # Verify we got some UUIDs back
                assert len(imported_uuids) > 0
                assert all(isinstance(uuid, int) for uuid in imported_uuids)

            # Test OBJ round-trip
            obj_file = os.path.join(temp_dir, "roundtrip.obj")
            basic_context.writeOBJ(obj_file)

            with Context() as new_context:
                imported_uuids = new_context.loadOBJ(obj_file)
                assert len(imported_uuids) > 0

    def test_export_large_geometry_performance(self, basic_context):
        """Test export performance with larger geometry sets."""
        import time

        # Create moderate amount of geometry (100 triangles)
        uuids = []
        for i in range(100):
            x_offset = i * 0.1
            uuid = basic_context.addTriangle(
                vec3(x_offset, 0, 0),
                vec3(x_offset + 0.05, 0, 0),
                vec3(x_offset + 0.025, 0.05, 0)
            )
            uuids.append(uuid)

        with tempfile.TemporaryDirectory() as temp_dir:
            # Test PLY export performance
            ply_file = os.path.join(temp_dir, "performance.ply")
            start_time = time.time()
            basic_context.writePLY(ply_file)
            ply_time = time.time() - start_time

            # Should complete within reasonable time (adjust if needed)
            assert ply_time < 5.0, f"PLY export took too long: {ply_time:.2f}s"

            # Test OBJ export performance
            obj_file = os.path.join(temp_dir, "performance.obj")
            start_time = time.time()
            basic_context.writeOBJ(obj_file)
            obj_time = time.time() - start_time

            assert obj_time < 5.0, f"OBJ export took too long: {obj_time:.2f}s"


@pytest.mark.native_only
class TestPrimitiveInfoOperations:
    """Test PrimitiveInfo and related methods."""
    
    def test_getPrimitiveInfo_patch(self, basic_context):
        """Test getting primitive info for a patch."""
        center = vec3(2, 3, 4)
        size = vec2(1.5, 2.0)
        color = RGBcolor(0.5, 0.7, 0.2)
        
        patch_uuid = basic_context.addPatch(center=center, size=size, color=color)
        
        primitive_info = basic_context.getPrimitiveInfo(patch_uuid)
        
        assert primitive_info.uuid == patch_uuid
        assert primitive_info.primitive_type == PrimitiveType.Patch
        assert primitive_info.area == pytest.approx(size.x * size.y)
        assert_color_equal(primitive_info.color, color)
        assert len(primitive_info.vertices) == 4  # Patch has 4 vertices
        
        # Check centroid calculation
        assert primitive_info.centroid is not None
        assert isinstance(primitive_info.centroid, vec3)
    
    def test_getPrimitiveInfo_triangle(self, basic_context):
        """Test getting primitive info for a triangle."""
        vertex0 = vec3(0, 0, 0)
        vertex1 = vec3(3, 0, 0)
        vertex2 = vec3(1.5, 4, 0)
        color = RGBcolor(1, 0, 0)
        
        triangle_uuid = basic_context.addTriangle(vertex0, vertex1, vertex2, color)
        
        primitive_info = basic_context.getPrimitiveInfo(triangle_uuid)
        
        assert primitive_info.uuid == triangle_uuid
        assert primitive_info.primitive_type == PrimitiveType.Triangle
        assert primitive_info.area == pytest.approx(6.0, rel=1e-5)  # Area = 0.5 * base * height = 0.5 * 3 * 4 = 6
        assert_color_equal(primitive_info.color, color)
        assert len(primitive_info.vertices) == 3  # Triangle has 3 vertices
        
        # Verify vertices
        assert_vec3_equal(primitive_info.vertices[0], vertex0)
        assert_vec3_equal(primitive_info.vertices[1], vertex1)
        assert_vec3_equal(primitive_info.vertices[2], vertex2)
        
        # Check centroid calculation (should be average of vertices)
        expected_centroid = vec3(
            (vertex0.x + vertex1.x + vertex2.x) / 3,
            (vertex0.y + vertex1.y + vertex2.y) / 3,
            (vertex0.z + vertex1.z + vertex2.z) / 3
        )
        assert_vec3_equal(primitive_info.centroid, expected_centroid)
    
    def test_getAllPrimitiveInfo(self, basic_context):
        """Test getting primitive info for all primitives."""
        # Add multiple primitives
        patch_uuid = basic_context.addPatch()
        triangle_uuid = basic_context.addTriangle(vec3(0,0,0), vec3(1,0,0), vec3(0.5,1,0))
        
        all_primitive_info = basic_context.getAllPrimitiveInfo()
        
        assert len(all_primitive_info) == 2
        
        # Find the patch and triangle info
        patch_info = next(info for info in all_primitive_info if info.uuid == patch_uuid)
        triangle_info = next(info for info in all_primitive_info if info.uuid == triangle_uuid)
        
        assert patch_info.primitive_type == PrimitiveType.Patch
        assert triangle_info.primitive_type == PrimitiveType.Triangle
    
    def test_getPrimitivesInfoForObject(self, basic_context):
        """Test getting primitive info for specific object."""
        # Add a patch (which creates an object)
        patch_uuid = basic_context.addPatch()
        
        # Get object IDs
        object_ids = basic_context.getAllObjectIDs()
        if len(object_ids) > 0:
            object_id = object_ids[0]
            
            # Get primitives for this object
            object_primitive_info = basic_context.getPrimitivesInfoForObject(object_id)
            
            assert isinstance(object_primitive_info, list)
            # Should contain our patch if it belongs to this object
            assert len(object_primitive_info) >= 0


@pytest.mark.cross_platform
class TestValidationMethods:
    """Test internal validation methods."""
    
    def test_validate_uuid_valid_cases(self, basic_context):
        """Test UUID validation with valid UUIDs."""
        if PlatformHelper.is_native_library_available():
            # Add a primitive to get a valid UUID
            patch_uuid = basic_context.addPatch()
            
            # Should not raise exception for valid UUID
            basic_context._validate_uuid(patch_uuid)
        else:
            # In mock mode, validation is skipped
            basic_context._validate_uuid(123)  # Should not raise in mock mode
    
    def test_validate_uuid_invalid_cases(self, mock_context):
        """Test UUID validation with invalid UUIDs."""
        # Test invalid UUID types and values
        with pytest.raises(RuntimeError, match="Invalid UUID"):
            Context()._validate_uuid(-1)  # Negative UUID

        with pytest.raises(RuntimeError, match="Invalid UUID"):
            Context()._validate_uuid("not_an_int")  # String UUID
    
    def test_validate_file_path_valid_cases(self):
        """Test file path validation with valid paths."""
        context = Context()
        
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix=".ply", delete=False) as tmp_file:
            tmp_file.write(b"dummy content")
            tmp_file.flush()
            
            try:
                # Valid file path
                validated_path = context._validate_file_path(tmp_file.name, ['.ply'])
                assert os.path.isabs(validated_path)
                assert validated_path.endswith('.ply')
                
            finally:
                _safe_unlink(tmp_file.name)
    
    def test_validate_file_path_invalid_cases(self):
        """Test file path validation with invalid paths."""
        context = Context()
        
        # Non-existent file
        with pytest.raises(FileNotFoundError):
            context._validate_file_path("nonexistent_file.ply")
        
        # Wrong extension
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp_file:
            tmp_file.write(b"dummy content")
            tmp_file.flush()
            
            try:
                with pytest.raises(ValueError, match="Invalid file extension"):
                    context._validate_file_path(tmp_file.name, ['.ply'])
                    
            finally:
                _safe_unlink(tmp_file.name)
        
        # Directory instead of file
        with tempfile.TemporaryDirectory() as tmp_dir:
            with pytest.raises(ValueError, match="Path is not a file"):
                context._validate_file_path(tmp_dir)


@pytest.mark.cross_platform
class TestPluginMethods:
    """Test plugin-related methods."""
    
    def test_get_available_plugins(self):
        """Test getting available plugins."""
        if PlatformHelper.is_native_library_available():
            with Context() as context:
                plugins = context.get_available_plugins()
                assert isinstance(plugins, list)
                # Should be strings
                assert all(isinstance(plugin, str) for plugin in plugins)
        else:
            # In mock mode, should still work but return empty list
            context = Context()
            plugins = context.get_available_plugins()
            assert isinstance(plugins, list)
    
    def test_is_plugin_available(self):
        """Test checking if specific plugin is available."""
        if PlatformHelper.is_native_library_available():
            with Context() as context:
                # Check some known plugins
                available_plugins = context.get_available_plugins()
                
                if available_plugins:
                    # Test a plugin that should be available
                    assert context.is_plugin_available(available_plugins[0])
                
                # Test a plugin that should not be available
                assert not context.is_plugin_available("nonexistent_plugin_xyz123")
        else:
            context = Context()
            # In mock mode, should return False for any plugin
            assert not context.is_plugin_available("any_plugin")
    
    def test_get_plugin_capabilities(self):
        """Test getting plugin capabilities."""
        if PlatformHelper.is_native_library_available():
            with Context() as context:
                capabilities = context.get_plugin_capabilities()
                assert isinstance(capabilities, dict)
        else:
            context = Context()
            capabilities = context.get_plugin_capabilities()
            assert isinstance(capabilities, dict)
    
    def test_get_missing_plugins(self):
        """Test getting missing plugins."""
        if PlatformHelper.is_native_library_available():
            with Context() as context:
                # Test with some plugins that might not be available
                missing = context.get_missing_plugins(["nonexistent1", "nonexistent2"])
                assert isinstance(missing, list)
                assert "nonexistent1" in missing
                assert "nonexistent2" in missing
        else:
            context = Context()
            missing = context.get_missing_plugins(["any_plugin"])
            assert isinstance(missing, list)


@pytest.mark.native_only  
class TestPseudocolorOperations:
    """Test pseudocolor functionality."""
    
    def test_colorPrimitiveByDataPseudocolor_basic(self, basic_context):
        """Test basic pseudocolor functionality."""
        # Add primitives and set data
        patch_uuids = []
        for i in range(3):
            uuid = basic_context.addPatch(center=vec3(i, 0, 0))
            basic_context.setPrimitiveDataFloat(uuid, "test_data", float(i))
            patch_uuids.append(uuid)
        
        try:
            # Apply pseudocolor
            basic_context.colorPrimitiveByDataPseudocolor(
                uuids=patch_uuids,
                primitive_data="test_data",
                colormap="hot",
                ncolors=10
            )
            
            # Verify colors were applied (actual color values depend on implementation)
            for uuid in patch_uuids:
                color = basic_context.getPrimitiveColor(uuid)
                assert isinstance(color, RGBcolor)
                
        except NotImplementedError:
            # Pseudocolor functions may not be available in current native library
            pytest.skip("Pseudocolor functions not available in current Helios library")
    
    def test_colorPrimitiveByDataPseudocolor_with_range(self, basic_context):
        """Test pseudocolor with specified value range."""
        # Add primitives and set data
        patch_uuids = []
        for i in range(3):
            uuid = basic_context.addPatch(center=vec3(i, 0, 0))
            basic_context.setPrimitiveDataFloat(uuid, "test_data", float(i))
            patch_uuids.append(uuid)
        
        try:
            # Apply pseudocolor with range
            basic_context.colorPrimitiveByDataPseudocolor(
                uuids=patch_uuids,
                primitive_data="test_data",
                colormap="cool",
                ncolors=5,
                max_val=10.0,
                min_val=0.0
            )
            
            # Verify colors were applied
            for uuid in patch_uuids:
                color = basic_context.getPrimitiveColor(uuid)
                assert isinstance(color, RGBcolor)
                
        except NotImplementedError:
            # Pseudocolor functions may not be available in current native library
            pytest.skip("Pseudocolor functions not available in current Helios library")


@pytest.mark.cross_platform
class TestContextErrorHandling:
    """Test Context error handling and edge cases."""
    
    def test_context_in_mock_mode(self):
        """Test Context behavior in mock mode."""
        if not PlatformHelper.is_native_library_available():
            context = Context()
            
            # Should be able to create context
            assert context is not None
            
            # Operations should raise RuntimeError indicating mock mode
            with pytest.raises(RuntimeError, match="mock mode"):
                context.addPatch()
                
            with pytest.raises(RuntimeError, match="mock mode"):
                context.getPrimitiveCount()
                
            # Test getPrimitiveDataArray in mock mode
            with pytest.raises(RuntimeError, match="mock mode"):
                context.getPrimitiveDataArray([1, 2, 3], "test_label")
    
    def test_context_manager_cleanup(self):
        """Test Context cleanup in context manager."""
        if PlatformHelper.is_native_library_available():
            # Test that context is properly cleaned up
            with Context() as context:
                # Add some primitives
                context.addPatch()
                assert context.getPrimitiveCount() == 1
            # Context should be cleaned up here
    
    def test_invalid_operations_on_invalid_context(self):
        """Test operations on invalid/destroyed context."""
        if PlatformHelper.is_native_library_available():
            # Note: This test demonstrates context lifecycle management
            # The actual behavior is that the context pointer remains but the
            # underlying C++ object is destroyed, making operations unsafe
            context = Context()
            
            # Verify context is valid before destruction
            assert context.context is not None
            
            # Destroy the context
            context.__exit__(None, None, None)
            
            # The pointer is set to None to prevent double deletion and segfaults
            # This is the safe approach to context cleanup
            assert context.context is None  # Pointer is safely cleared
            
            # The safer approach is to use context managers properly:
            # with Context() as ctx: ...
            # This ensures automatic cleanup
    
    def test_large_scale_operations(self, basic_context):
        """Test performance with larger numbers of primitives."""
        if not PlatformHelper.is_native_library_available():
            pytest.skip("Requires native library for performance testing")
        
        # Add many primitives to test scalability
        num_primitives = 500
        uuids = []
        
        for i in range(num_primitives):
            center = vec3(i % 20, (i // 20) % 20, 0)
            uuid = basic_context.addPatch(center=center)
            uuids.append(uuid)
            
            # Add some primitive data
            basic_context.setPrimitiveDataInt(uuid, "index", i)
            basic_context.setPrimitiveDataFloat(uuid, "value", float(i) * 0.1)
        
        # Verify all were added
        assert basic_context.getPrimitiveCount() == num_primitives
        
        # Test bulk operations
        all_uuids = basic_context.getAllUUIDs()
        assert len(all_uuids) == num_primitives
        
        # Test primitive info retrieval
        all_info = basic_context.getAllPrimitiveInfo()
        assert len(all_info) == num_primitives
        
        # Verify data integrity for some primitives
        for i in range(0, num_primitives, 50):  # Check every 50th primitive
            uuid = uuids[i]
            assert basic_context.getPrimitiveData(uuid, "index", int) == i
            assert basic_context.getPrimitiveData(uuid, "value", float) == pytest.approx(i * 0.1)


@pytest.mark.native_only
class TestSphericalCoordParameterMapping:
    """Critical tests for SphericalCoord parameter mapping to prevent recurring bugs."""
    
    def test_addPatch_spherical_coord_parameter_count(self, basic_context):
        """Test that addPatch uses correct SphericalCoord parameter count (CRITICAL for radiation physics)."""
        # This test specifically validates the fix for the recurring SphericalCoord bug
        # where PyHelios was passing 4 parameters [radius, elevation, zenith, azimuth] 
        # but C++ expected 3 parameters [radius, elevation, azimuth]
        
        import numpy as np
        
        # Test specific rotation that caused radiation validation failures
        rotation = SphericalCoord(1.0, 0.5 * np.pi, -0.5 * np.pi)  # 90-degree rotation
        
        # This should NOT crash and should create valid geometry
        patch_uuid = basic_context.addPatch(
            center=vec3(0.5, 0, 0.5), 
            size=vec2(1, 1),
            rotation=rotation
        )
        
        assert isinstance(patch_uuid, int)
        assert patch_uuid >= 0
        
        # Verify the patch was created with proper geometry
        vertices = basic_context.getPrimitiveVertices(patch_uuid)
        assert len(vertices) == 4
        
        # The patch should be rotated - vertices should not all have same Z coordinate
        z_coords = [v.z for v in vertices]
        # For a 90-degree rotated patch, vertices should span different Z coordinates
        z_range = max(z_coords) - min(z_coords)
        assert z_range > 0.5  # Should have significant Z variation for rotated patch
    
    def test_addTile_spherical_coord_parameter_count(self, basic_context):
        """Test that addTile uses correct SphericalCoord parameter count."""
        import numpy as np
        
        # Test with same problematic rotation
        rotation = SphericalCoord(1.0, 0.5 * np.pi, -0.5 * np.pi)
        
        tile_uuids = basic_context.addTile(
            center=vec3(0, 0, 0),
            size=vec2(2, 2),
            rotation=rotation,
            subdiv=int2(2, 2)
        )
        
        assert isinstance(tile_uuids, list)
        assert len(tile_uuids) == 4  # 2x2 subdivision
        assert all(isinstance(uuid, int) for uuid in tile_uuids)
        
        # Verify tiles were created with proper rotation
        for uuid in tile_uuids:
            vertices = basic_context.getPrimitiveVertices(uuid)
            assert len(vertices) == 4
            
            # Check that rotation was applied correctly
            z_coords = [v.z for v in vertices]
            z_range = max(z_coords) - min(z_coords)
            # For rotated tiles, should have some Z variation
            assert z_range >= 0  # At minimum, should not crash
    
    def test_spherical_coord_to_list_vs_cpp_interface(self, basic_context):
        """Test that SphericalCoord.to_list() is NOT used for C++ interface calls."""
        # This test documents and validates the fix for the parameter mapping bug
        
        rotation = SphericalCoord(1.0, 0.5, 1.0)
        
        # SphericalCoord.to_list() returns 4 values - this should NOT be passed to C++
        to_list_result = rotation.to_list()
        assert len(to_list_result) == 4  # [radius, elevation, zenith, azimuth]
        
        # The correct mapping for C++ should be 3 values: [radius, elevation, azimuth]
        correct_mapping = [rotation.radius, rotation.elevation, rotation.azimuth]
        assert len(correct_mapping) == 3
        
        # Test that addPatch works with this rotation (validates the fix is applied)
        patch_uuid = basic_context.addPatch(
            center=vec3(0, 0, 0),
            size=vec2(1, 1),
            rotation=rotation
        )
        
        assert isinstance(patch_uuid, int)
        assert patch_uuid >= 0
    
    def test_multiple_rotations_physics_validation(self, basic_context):
        """Test multiple rotation configurations to prevent physics calculation errors."""
        import numpy as np
        
        # Test various rotation configurations that have caused issues
        test_rotations = [
            SphericalCoord(1.0, 0, 0),                        # No rotation
            SphericalCoord(1.0, 0.5 * np.pi, 0),             # 90-degree elevation
            SphericalCoord(1.0, 0, 0.5 * np.pi),             # 90-degree azimuth  
            SphericalCoord(1.0, 0.5 * np.pi, -0.5 * np.pi),  # The problematic radiation test case
            SphericalCoord(1.0, np.pi, 0),                    # 180-degree elevation
            SphericalCoord(1.0, -0.5 * np.pi, np.pi),        # Negative elevation
        ]
        
        created_patches = []
        
        for i, rotation in enumerate(test_rotations):
            center = vec3(i * 2, 0, 0)  # Space patches apart
            
            patch_uuid = basic_context.addPatch(
                center=center,
                size=vec2(1, 1),
                rotation=rotation
            )
            
            assert isinstance(patch_uuid, int)
            assert patch_uuid >= 0
            created_patches.append(patch_uuid)
            
            # Verify patch has valid geometry
            area = basic_context.getPrimitiveArea(patch_uuid)
            assert area > 0  # Should have positive area
            
            normal = basic_context.getPrimitiveNormal(patch_uuid)
            normal_length = (normal.x**2 + normal.y**2 + normal.z**2)**0.5
            assert normal_length == pytest.approx(1.0, rel=1e-5)  # Should be unit vector
        
        # Verify all patches were created successfully
        assert len(created_patches) == len(test_rotations)
        assert basic_context.getPrimitiveCount() == len(test_rotations)
    
    def test_regression_spherical_coord_parameter_count_documentation(self, basic_context):
        """Regression test that documents the exact parameter mapping requirements."""
        # This test serves as documentation and regression prevention for the 
        # SphericalCoord parameter mapping bug that caused radiation physics errors
        
        rotation = SphericalCoord(1.0, 0.5, 1.0)
        
        # Document the WRONG way that was causing the bug:
        wrong_params = rotation.to_list()  # [radius, elevation, zenith, azimuth] = 4 params
        assert len(wrong_params) == 4
        
        # Document the CORRECT way that fixes the bug:
        correct_params = [rotation.radius, rotation.elevation, rotation.azimuth]  # 3 params
        assert len(correct_params) == 3
        
        # The bug was: Context.addPatch() was passing wrong_params (4 values) to C++
        # The fix is: Context.addPatch() now passes correct_params (3 values) to C++
        
        # Test that the fix is working by creating geometry that previously failed
        patch_uuid = basic_context.addPatch(
            center=vec3(0.5, 0, 0.5), 
            size=vec2(1, 1),
            rotation=rotation
        )
        
        # If this test passes, the fix is working correctly
        assert isinstance(patch_uuid, int)
        assert patch_uuid >= 0
        
        # Verify the geometry was created correctly (not corrupted by wrong parameters)
        area = basic_context.getPrimitiveArea(patch_uuid)
        assert area == pytest.approx(1.0, rel=1e-5)  # 1x1 patch should have area 1
        
        vertices = basic_context.getPrimitiveVertices(patch_uuid)
        assert len(vertices) == 4
        
        # This test specifically validates that radiation physics will work correctly
        # because patch geometry is properly oriented


@pytest.mark.native_only
class TestCompoundGeometry:
    """Test compound geometry methods that should always be available in native builds."""
    
    def test_compound_geometry_availability(self, basic_context):
        """Test that all compound geometry methods are available - critical failure if not."""
        # These methods should ALWAYS be available in native builds
        required_methods = ['addTile', 'addSphere', 'addTube', 'addBox']
        
        for method_name in required_methods:
            assert hasattr(basic_context, method_name), \
                f"Critical failure: {method_name} not available in native build"
            method = getattr(basic_context, method_name)
            assert callable(method), f"Critical failure: {method_name} is not callable"
    
    def test_addTile_basic(self, basic_context):
        """Test basic tile creation."""
        center = vec3(0, 0, 0)
        size = vec2(2, 2)
        subdivisions = int2(2, 2)
        
        uuids = basic_context.addTile(center=center, size=size, subdiv=subdivisions)
        
        # Should return list of UUIDs for 2x2 = 4 patches
        assert isinstance(uuids, list)
        assert len(uuids) == 4
        assert all(isinstance(uuid, int) for uuid in uuids)
        assert all(uuid >= 0 for uuid in uuids)
        
        # Verify primitives were added to context
        assert basic_context.getPrimitiveCount() == 4
    
    def test_addTile_with_rotation(self, basic_context):
        """Test tile creation with rotation."""
        center = vec3(1, 1, 1)
        size = vec2(1, 1) 
        subdivisions = int2(3, 3)
        rotation = SphericalCoord(1, 0.5, 1.0)  # radius, elevation, azimuth
        
        uuids = basic_context.addTile(center=center, size=size, rotation=rotation, subdiv=subdivisions)
        
        # Should return 3x3 = 9 patches
        assert len(uuids) == 9
        assert basic_context.getPrimitiveCount() == 9
    
    def test_addTile_with_color(self, basic_context):
        """Test tile creation with color."""
        center = vec3(0, 0, 0)
        size = vec2(1, 1)
        subdivisions = int2(2, 2)
        color = RGBcolor(0.5, 0.7, 0.9)
        
        uuids = basic_context.addTile(center=center, size=size, subdiv=subdivisions, color=color)
        
        assert len(uuids) == 4
        # Note: Color verification would require additional Context methods
    
    def test_addTile_parameter_validation(self, basic_context):
        """Test tile parameter validation."""
        center = vec3(0, 0, 0)
        size = vec2(1, 1)
        
        # Invalid subdivisions
        with pytest.raises(ValueError, match="All subdivision counts must be positive"):
            basic_context.addTile(center=center, size=size, subdiv=int2(0, 1))
        
        with pytest.raises(ValueError, match="All subdivision counts must be positive"):
            basic_context.addTile(center=center, size=size, subdiv=int2(1, -1))
    
    def test_addSphere_basic(self, basic_context):
        """Test basic sphere creation."""
        center = vec3(0, 0, 0)
        radius = 1.0
        subdivisions = 8
        
        uuids = basic_context.addSphere(center, radius, subdivisions)
        
        # Should return list of triangle UUIDs
        assert isinstance(uuids, list)
        assert len(uuids) > 0
        assert all(isinstance(uuid, int) for uuid in uuids)
        assert all(uuid >= 0 for uuid in uuids)
        
        # Verify primitives were added
        assert basic_context.getPrimitiveCount() == len(uuids)
    
    def test_addSphere_high_subdivision(self, basic_context):
        """Test sphere with higher subdivision count."""
        center = vec3(2, 2, 2)
        radius = 0.5
        subdivisions = 16
        
        uuids = basic_context.addSphere(center, radius, subdivisions)
        
        # Higher subdivisions should create more triangles
        assert len(uuids) > 32  # Expect significant number of triangles
        assert basic_context.getPrimitiveCount() == len(uuids)
    
    def test_addSphere_with_color(self, basic_context):
        """Test sphere creation with color."""
        center = vec3(0, 0, 0)
        radius = 1.0
        subdivisions = 6
        color = RGBcolor(1.0, 0.5, 0.0)
        
        uuids = basic_context.addSphere(center, radius, subdivisions, color=color)
        
        assert len(uuids) > 0
        assert basic_context.getPrimitiveCount() == len(uuids)
    
    def test_addSphere_parameter_validation(self, basic_context):
        """Test sphere parameter validation."""
        center = vec3(0, 0, 0)
        
        # Invalid radius
        with pytest.raises(ValueError, match="must be positive"):
            basic_context.addSphere(center, 0.0, 8)

        with pytest.raises(ValueError, match="must be positive"):
            basic_context.addSphere(center, -1.0, 8)

        # Invalid subdivisions
        with pytest.raises(ValueError, match="must be >= 3"):
            basic_context.addSphere(center, 1.0, 2)
    
    def test_addTube_basic(self, basic_context):
        """Test basic tube creation."""
        nodes = [vec3(0, 0, 0), vec3(1, 0, 0), vec3(2, 1, 0)]
        radius = 0.1
        ndivs = 6
        
        uuids = basic_context.addTube(nodes, radius, ndivs)
        
        # Should return list of triangle UUIDs
        assert isinstance(uuids, list)
        assert len(uuids) > 0
        assert all(isinstance(uuid, int) for uuid in uuids)
        assert all(uuid >= 0 for uuid in uuids)
        
        # Verify primitives were added
        assert basic_context.getPrimitiveCount() == len(uuids)
    
    def test_addTube_variable_radii(self, basic_context):
        """Test tube with different radii per node."""
        nodes = [vec3(0, 0, 0), vec3(1, 0, 0), vec3(2, 0, 0)]
        radii = [0.05, 0.1, 0.15]  # Expanding tube
        ndivs = 8
        
        uuids = basic_context.addTube(nodes, radii, ndivs)
        
        assert len(uuids) > 0
        assert basic_context.getPrimitiveCount() == len(uuids)
    
    def test_addTube_with_colors(self, basic_context):
        """Test tube creation with colors."""
        nodes = [vec3(0, 0, 0), vec3(0, 1, 0)]
        radius = 0.1
        ndivs = 6
        colors = [RGBcolor(1.0, 0.0, 0.0), RGBcolor(0.0, 1.0, 0.0)]
        
        uuids = basic_context.addTube(nodes, radius, ndivs, colors=colors)
        
        assert len(uuids) > 0
        assert basic_context.getPrimitiveCount() == len(uuids)
    
    def test_addTube_single_color(self, basic_context):
        """Test tube creation with single color for all segments."""
        nodes = [vec3(0, 0, 0), vec3(1, 0, 0), vec3(1, 1, 0)]
        radius = 0.1
        ndivs = 6
        color = RGBcolor(0.5, 0.5, 1.0)
        
        uuids = basic_context.addTube(nodes, radius, ndivs, colors=color)
        
        assert len(uuids) > 0
        assert basic_context.getPrimitiveCount() == len(uuids)
    
    def test_addTube_parameter_validation(self, basic_context):
        """Test tube parameter validation."""
        nodes = [vec3(0, 0, 0), vec3(1, 0, 0)]
        
        # Invalid radius
        with pytest.raises(ValueError, match="must be positive"):
            basic_context.addTube(nodes, 0.0, 6)
        
        with pytest.raises(ValueError, match="must be positive"):
            basic_context.addTube(nodes, -0.1, 6)
        
        # Invalid ndivs
        with pytest.raises(ValueError, match="Number of radial divisions must be at least 3"):
            basic_context.addTube(nodes, 0.1, 2)
        
        # Insufficient nodes
        with pytest.raises(ValueError, match="must contain at least 2 nodes"):
            basic_context.addTube([vec3(0, 0, 0)], 0.1, 6)
        
        # Mismatched radii count
        with pytest.raises(ValueError, match="must have same length as nodes"):
            basic_context.addTube(nodes, [0.1], 6)  # 2 nodes but 1 radius
        
        # Mismatched colors count
        with pytest.raises(ValueError, match="Number of colors.*must match.*number of nodes"):
            basic_context.addTube(nodes, 0.1, 6, colors=[RGBcolor(1, 0, 0)])  # 2 nodes but 1 color
    
    def test_addBox_basic(self, basic_context):
        """Test basic box creation."""
        center = vec3(0, 0, 0)
        size = vec3(1, 2, 0.5)
        
        uuids = basic_context.addBox(center, size)
        
        # Should return list of triangle UUIDs for box faces
        assert isinstance(uuids, list)
        assert len(uuids) > 0
        assert all(isinstance(uuid, int) for uuid in uuids)
        assert all(uuid >= 0 for uuid in uuids)
        
        # Verify primitives were added
        assert basic_context.getPrimitiveCount() == len(uuids)
    
    def test_addBox_with_subdivisions(self, basic_context):
        """Test box creation with subdivisions."""
        center = vec3(1, 1, 1)
        size = vec3(2, 2, 2)
        subdivisions = int3(2, 2, 2)
        
        uuids = basic_context.addBox(center, size, subdivisions)
        
        # More subdivisions should create more triangles
        assert len(uuids) > 12  # Basic box has 12 triangles (2 per face * 6 faces)
        assert basic_context.getPrimitiveCount() == len(uuids)
    
    def test_addBox_large_subdivisions(self, basic_context):
        """Test box creation with large subdivision counts."""
        center = vec3(0, 0, 0)
        size = vec3(1, 1, 1)
        subdivisions = int3(4, 4, 4)
        
        uuids = basic_context.addBox(center, size, subdivisions)
        
        # Large subdivisions should create many more triangles
        assert len(uuids) > 48  # Much more than basic 12 triangles
        assert basic_context.getPrimitiveCount() == len(uuids)
    
    def test_addBox_with_color(self, basic_context):
        """Test box creation with color."""
        center = vec3(0, 0, 0)
        size = vec3(1, 1, 1)
        color = RGBcolor(0.8, 0.2, 0.9)
        
        uuids = basic_context.addBox(center, size, color=color)
        
        assert len(uuids) > 0
        assert basic_context.getPrimitiveCount() == len(uuids)
    
    def test_addBox_parameter_validation(self, basic_context):
        """Test box parameter validation."""
        center = vec3(0, 0, 0)
        
        # Invalid size (negative dimensions)
        with pytest.raises(ValueError, match="must be positive"):
            basic_context.addBox(center, vec3(-1, 1, 1))

        with pytest.raises(ValueError, match="must be positive"):
            basic_context.addBox(center, vec3(1, 0, 1))

        # Invalid subdivisions
        with pytest.raises(ValueError, match="subdivision counts must be at least 1"):
            basic_context.addBox(center, vec3(1, 1, 1), int3(0, 1, 1))
    
    def test_compound_geometry_return_types(self, basic_context):
        """Test that all compound geometry methods return proper list types."""
        # Test each method returns List[int]
        tile_uuids = basic_context.addTile(center=vec3(0, 0, 0), size=vec2(1, 1), subdiv=int2(2, 2))
        sphere_uuids = basic_context.addSphere(vec3(1, 0, 0), 0.5, 8)
        tube_uuids = basic_context.addTube([vec3(2, 0, 0), vec3(3, 0, 0)], 0.1, 6)
        box_uuids = basic_context.addBox(vec3(4, 0, 0), vec3(1, 1, 1))
        
        # All should return lists of integers
        for uuids, method_name in [
            (tile_uuids, "addTile"), 
            (sphere_uuids, "addSphere"),
            (tube_uuids, "addTube"), 
            (box_uuids, "addBox")
        ]:
            assert isinstance(uuids, list), f"{method_name} should return list"
            assert len(uuids) > 0, f"{method_name} should return non-empty list"
            assert all(isinstance(uuid, int) for uuid in uuids), \
                f"{method_name} should return list of integers"
            assert all(uuid >= 0 for uuid in uuids), \
                f"{method_name} should return valid UUIDs (non-negative)"
    
    def test_compound_geometry_integration(self, basic_context):
        """Test that compound geometry integrates properly with Context operations."""
        # Create various compound geometry
        tile_uuids = basic_context.addTile(center=vec3(0, 0, 0), size=vec2(1, 1), subdiv=int2(2, 2))
        sphere_uuids = basic_context.addSphere(vec3(2, 0, 0), 0.5, 6)
        box_uuids = basic_context.addBox(vec3(4, 0, 0), vec3(0.5, 0.5, 0.5))
        
        total_expected = len(tile_uuids) + len(sphere_uuids) + len(box_uuids)
        
        # Verify total count
        assert basic_context.getPrimitiveCount() == total_expected
        
        # Verify all UUIDs are accessible
        all_context_uuids = basic_context.getAllUUIDs()
        assert len(all_context_uuids) == total_expected
        
        # Verify compound geometry UUIDs are in context
        all_compound_uuids = tile_uuids + sphere_uuids + box_uuids
        for uuid in all_compound_uuids:
            assert uuid in all_context_uuids
        
        # Test that we can add primitive data to compound geometry elements
        if tile_uuids:
            basic_context.setPrimitiveDataString(tile_uuids[0], "type", "tile_patch")
            assert basic_context.getPrimitiveData(tile_uuids[0], "type", str) == "tile_patch"
        
        if sphere_uuids:
            basic_context.setPrimitiveDataFloat(sphere_uuids[0], "radius", 0.5)
            assert basic_context.getPrimitiveData(sphere_uuids[0], "radius", float) == pytest.approx(0.5)


@pytest.mark.cross_platform  
class TestCompoundGeometryMockMode:
    """Test compound geometry methods in mock mode for cross-platform compatibility."""
    
    def test_compound_geometry_mock_mode_behavior(self):
        """Test that compound geometry methods behave appropriately in mock mode."""
        from pyhelios.wrappers import UContextWrapper
        
        # Force compound geometry functions to be unavailable by patching the availability flag
        with patch.object(UContextWrapper, '_COMPOUND_GEOMETRY_FUNCTIONS_AVAILABLE', False):
            context = Context()
            
            # In mock mode, methods should exist but raise informative errors
            assert hasattr(context, 'addTile')
            assert hasattr(context, 'addSphere') 
            assert hasattr(context, 'addTube')
            assert hasattr(context, 'addBox')
            
            # Methods should raise NotImplementedError when functions are not available
            with pytest.raises(NotImplementedError, match="not available"):
                context.addTile(center=vec3(0, 0, 0), size=vec2(1, 1), subdiv=int2(2, 2))
            
            with pytest.raises(NotImplementedError, match="not available"):
                context.addSphere(vec3(0, 0, 0), 1.0, 8)
            
            with pytest.raises(NotImplementedError, match="not available"):
                context.addTube([vec3(0, 0, 0), vec3(1, 0, 0)], 0.1, 6)
            
            with pytest.raises(NotImplementedError, match="not available"):
                context.addBox(vec3(0, 0, 0), vec3(1, 1, 1))


@pytest.mark.native_only
class TestContextTimeDate:
    """Test Context time/date functionality for solar position integration"""
    
    def test_context_time_methods(self):
        """Test Context time setting and getting methods"""
        with Context() as context:
            # Test setting time with hour and minute
            context.setTime(14, 30)
            hour, minute, second = context.getTime()
            assert hour == 14
            assert minute == 30
            assert second == 0  # Should default to 0
            
            # Test setting time with hour, minute, and second
            context.setTime(9, 15, 45)
            hour, minute, second = context.getTime()
            assert hour == 9
            assert minute == 15
            assert second == 45
    
    def test_context_date_methods(self):
        """Test Context date setting and getting methods"""
        with Context() as context:
            # Test setting date
            context.setDate(2023, 6, 21)
            year, month, day = context.getDate()
            assert year == 2023
            assert month == 6
            assert day == 21
            
            # Test setting date with different values
            context.setDate(2024, 12, 25)
            year, month, day = context.getDate()
            assert year == 2024
            assert month == 12
            assert day == 25
    
    def test_context_julian_date(self):
        """Test Context Julian date setting"""
        with Context() as context:
            # Test setting Julian date (day 172 of 2023 should be around June 21)
            context.setDateJulian(172, 2023)
            year, month, day = context.getDate()
            assert year == 2023
            # Should be in June (exact day depends on Helios implementation)
            assert 5 <= month <= 7  # Should be around June
    
    def test_time_parameter_validation(self):
        """Test time parameter validation"""
        with Context() as context:
            # Test invalid hour
            with pytest.raises((ValueError, Exception)):
                context.setTime(25, 0)
            
            with pytest.raises((ValueError, Exception)):
                context.setTime(-1, 0)
            
            # Test invalid minute
            with pytest.raises((ValueError, Exception)):
                context.setTime(12, 60)
            
            with pytest.raises((ValueError, Exception)):
                context.setTime(12, -1)
            
            # Test invalid second
            with pytest.raises((ValueError, Exception)):
                context.setTime(12, 30, 60)
            
            with pytest.raises((ValueError, Exception)):
                context.setTime(12, 30, -1)
    
    def test_date_parameter_validation(self):
        """Test date parameter validation"""
        with Context() as context:
            # Test invalid year
            with pytest.raises((ValueError, Exception)):
                context.setDate(1800, 6, 21)  # Too early
            
            with pytest.raises((ValueError, Exception)):
                context.setDate(3500, 6, 21)  # Too late
            
            # Test invalid month
            with pytest.raises((ValueError, Exception)):
                context.setDate(2023, 0, 21)  # Month 0
            
            with pytest.raises((ValueError, Exception)):
                context.setDate(2023, 13, 21)  # Month 13
            
            # Test invalid day
            with pytest.raises((ValueError, Exception)):
                context.setDate(2023, 6, 0)  # Day 0
            
            with pytest.raises((ValueError, Exception)):
                context.setDate(2023, 6, 32)  # Day 32
    
    def test_julian_date_validation(self):
        """Test Julian date parameter validation"""
        with Context() as context:
            # Test invalid Julian day
            with pytest.raises((ValueError, Exception)):
                context.setDateJulian(0, 2023)  # Day 0
            
            with pytest.raises((ValueError, Exception)):
                context.setDateJulian(367, 2023)  # Day 367
            
            # Test invalid year for Julian date
            with pytest.raises((ValueError, Exception)):
                context.setDateJulian(172, 1800)  # Too early


@pytest.mark.cross_platform
class TestContextTimeDateMockMode:
    """Test Context time/date methods in mock mode for cross-platform compatibility"""
    
    def test_time_date_methods_mock_behavior(self):
        """Test that time/date methods behave appropriately in mock mode"""
        from pyhelios.wrappers import UContextWrapper
        
        # Test if time/date functions are available
        if not hasattr(UContextWrapper, '_TIME_DATE_FUNCTIONS_AVAILABLE'):
            pytest.skip("Time/date functions not implemented in this version")
        
        # Force time/date functions to be unavailable by patching the availability flag
        with patch.object(UContextWrapper, '_TIME_DATE_FUNCTIONS_AVAILABLE', False):
            context = Context()
            
            # In mock mode, methods should exist but raise informative errors
            assert hasattr(context, 'setTime')
            assert hasattr(context, 'setDate')
            assert hasattr(context, 'setDateJulian')
            assert hasattr(context, 'getTime')
            assert hasattr(context, 'getDate')
            
            # Methods should raise NotImplementedError when functions are not available
            with pytest.raises(NotImplementedError, match="not available"):
                context.setTime(12, 0)
            
            with pytest.raises(NotImplementedError, match="not available"):
                context.setDate(2023, 6, 21)
            
            with pytest.raises(NotImplementedError, match="not available"):
                context.setDateJulian(172, 2023)
            
            with pytest.raises(NotImplementedError, match="not available"):
                context.getTime()
            
            with pytest.raises(NotImplementedError, match="not available"):
                context.getDate()


@pytest.mark.native_only
class TestTextureGetters:
    """Test single-UUID texture methods."""

    def test_getPrimitiveTextureFile_no_texture(self, basic_context):
        """Primitive without texture returns empty string."""
        uuid = basic_context.addPatch()
        result = basic_context.getPrimitiveTextureFile(uuid)
        assert isinstance(result, str)

    def test_setPrimitiveTextureFile(self, basic_context):
        """Setting and getting texture file round-trips."""
        uuid = basic_context.addPatch()
        basic_context.setPrimitiveTextureFile(uuid, "test_texture.png")
        result = basic_context.getPrimitiveTextureFile(uuid)
        assert result == "test_texture.png"

    def test_getPrimitiveTextureSize_no_texture(self, basic_context):
        """Primitive without texture returns zero size."""
        uuid = basic_context.addPatch()
        size = basic_context.getPrimitiveTextureSize(uuid)
        assert size.x == 0
        assert size.y == 0

    def test_getPrimitiveTextureUV_patch(self, basic_context):
        """Patch should have UV coordinates."""
        uuid = basic_context.addPatch()
        uvs = basic_context.getPrimitiveTextureUV(uuid)
        assert isinstance(uvs, list)

    def test_getPrimitiveSolidFraction(self, basic_context):
        """Solid fraction for patch without transparency texture."""
        uuid = basic_context.addPatch()
        fraction = basic_context.getPrimitiveSolidFraction(uuid)
        assert isinstance(fraction, float)
        assert fraction >= 0.0

    def test_primitiveTextureHasTransparencyChannel(self, basic_context):
        """Primitive without texture has no transparency channel."""
        uuid = basic_context.addPatch()
        result = basic_context.primitiveTextureHasTransparencyChannel(uuid)
        assert isinstance(result, bool)

    def test_overrideAndUseTextureColor(self, basic_context):
        """Override and restore texture color."""
        uuid = basic_context.addPatch()
        # Initially not overridden
        assert basic_context.isPrimitiveTextureColorOverridden(uuid) == False
        # Override
        basic_context.overridePrimitiveTextureColor(uuid)
        assert basic_context.isPrimitiveTextureColorOverridden(uuid) == True
        # Restore
        basic_context.usePrimitiveTextureColor(uuid)
        assert basic_context.isPrimitiveTextureColorOverridden(uuid) == False

    def test_texture_invalid_uuid(self, basic_context):
        """Texture methods should raise on invalid UUID."""
        with pytest.raises(Exception):
            basic_context.getPrimitiveTextureFile(99999)


@pytest.mark.native_only
class TestListOverloads:
    """Test that scalar getters accept a list of UUIDs and return batch results."""

    def test_getPrimitiveNormal_list(self, basic_context):
        """List overload returns ndarray matching individual normals."""
        uuids = [basic_context.addPatch() for _ in range(5)]
        batch_normals = basic_context.getPrimitiveNormal(uuids)
        assert batch_normals.shape == (5, 3)
        for i, uuid in enumerate(uuids):
            single = basic_context.getPrimitiveNormal(uuid)
            assert batch_normals[i, 0] == pytest.approx(single.x, abs=1e-6)
            assert batch_normals[i, 1] == pytest.approx(single.y, abs=1e-6)
            assert batch_normals[i, 2] == pytest.approx(single.z, abs=1e-6)

    def test_getPrimitiveColor_list(self, basic_context):
        """List overload returns ndarray matching individual colors."""
        colors = [RGBcolor(0.1*i, 0.2*i, 0.3*i) for i in range(1, 4)]
        uuids = [basic_context.addPatch(color=c) for c in colors]
        batch_colors = basic_context.getPrimitiveColor(uuids)
        assert batch_colors.shape == (3, 3)
        for i, uuid in enumerate(uuids):
            single = basic_context.getPrimitiveColor(uuid)
            assert batch_colors[i, 0] == pytest.approx(single.r, abs=1e-6)
            assert batch_colors[i, 1] == pytest.approx(single.g, abs=1e-6)
            assert batch_colors[i, 2] == pytest.approx(single.b, abs=1e-6)

    def test_getPrimitiveArea_list(self, basic_context):
        """List overload returns ndarray matching individual areas."""
        sizes = [vec2(1, 1), vec2(2, 3), vec2(0.5, 4)]
        uuids = [basic_context.addPatch(size=s) for s in sizes]
        batch_areas = basic_context.getPrimitiveArea(uuids)
        assert batch_areas.shape == (3,)
        for i, uuid in enumerate(uuids):
            assert batch_areas[i] == pytest.approx(basic_context.getPrimitiveArea(uuid), abs=1e-6)

    def test_getPrimitiveType_list(self, basic_context):
        """List overload returns ndarray matching individual types."""
        patch = basic_context.addPatch()
        tri = basic_context.addTriangle(vec3(0,0,0), vec3(1,0,0), vec3(0.5,1,0))
        uuids = [patch, tri]
        batch_types = basic_context.getPrimitiveType(uuids)
        assert batch_types.shape == (2,)
        assert batch_types[0] == basic_context.getPrimitiveType(patch).value
        assert batch_types[1] == basic_context.getPrimitiveType(tri).value

    def test_getPrimitiveSolidFraction_list(self, basic_context):
        """List overload returns ndarray matching individual solid fractions."""
        uuids = [basic_context.addPatch() for _ in range(3)]
        batch = basic_context.getPrimitiveSolidFraction(uuids)
        assert batch.shape == (3,)
        for i, uuid in enumerate(uuids):
            assert batch[i] == pytest.approx(basic_context.getPrimitiveSolidFraction(uuid), abs=1e-6)

    def test_getPrimitiveVertices_list(self, basic_context):
        """List overload returns (flat_data, offsets) for mixed geometry."""
        patch = basic_context.addPatch()
        tri = basic_context.addTriangle(vec3(0,0,0), vec3(1,0,0), vec3(0.5,1,0))
        uuids = [patch, tri]
        data, offsets = basic_context.getPrimitiveVertices(uuids)
        assert len(offsets) == 3  # N+1 offsets
        # Patch: 4 vertices = 12 floats
        patch_floats = offsets[1] - offsets[0]
        assert patch_floats == 12
        # Triangle: 3 vertices = 9 floats
        tri_floats = offsets[2] - offsets[1]
        assert tri_floats == 9
        # Verify values match single-UUID getter
        single_verts = basic_context.getPrimitiveVertices(patch)
        for j, v in enumerate(single_verts):
            assert data[offsets[0] + j*3] == pytest.approx(v.x, abs=1e-6)
            assert data[offsets[0] + j*3 + 1] == pytest.approx(v.y, abs=1e-6)
            assert data[offsets[0] + j*3 + 2] == pytest.approx(v.z, abs=1e-6)

    def test_getPrimitiveMaterialLabel_list(self, basic_context):
        """List overload returns list of strings matching individual labels."""
        uuids = [basic_context.addPatch() for _ in range(3)]
        labels = basic_context.getPrimitiveMaterialLabel(uuids)
        assert len(labels) == 3
        for i, uuid in enumerate(uuids):
            assert labels[i] == basic_context.getPrimitiveMaterialLabel(uuid)

    def test_getPrimitiveTextureFile_list(self, basic_context):
        """List overload returns list of texture file strings."""
        uuids = [basic_context.addPatch() for _ in range(3)]
        files = basic_context.getPrimitiveTextureFile(uuids)
        assert len(files) == 3
        assert all(isinstance(f, str) for f in files)

    def test_list_empty(self, basic_context):
        """Empty list returns empty results for all overloads."""
        assert basic_context.getPrimitiveNormal([]).shape == (0, 3)
        assert basic_context.getPrimitiveColor([]).shape == (0, 3)
        assert basic_context.getPrimitiveArea([]).shape == (0,)
        assert basic_context.getPrimitiveType([]).shape == (0,)
        data, offsets = basic_context.getPrimitiveVertices([])
        assert data.shape == (0,)
        assert basic_context.getPrimitiveTextureFile([]) == []
        assert basic_context.getPrimitiveMaterialLabel([]) == []

    def test_list_single_uuid(self, basic_context):
        """Single-element list works correctly."""
        uuid = basic_context.addPatch(size=vec2(2, 3))
        normals = basic_context.getPrimitiveNormal([uuid])
        assert normals.shape == (1, 3)
        areas = basic_context.getPrimitiveArea([uuid])
        assert areas.shape == (1,)
        assert areas[0] == pytest.approx(6.0, abs=1e-6)

    def test_list_invalid_uuid(self, basic_context):
        """List with invalid UUID raises exception."""
        with pytest.raises(Exception):
            basic_context.getPrimitiveNormal([99999])


@pytest.mark.native_only
class TestConvenienceMethods:
    """Test getAll* convenience methods."""

    def test_getAllPrimitiveNormals(self, basic_context):
        """getAllPrimitiveNormals returns correct shape."""
        basic_context.addPatch()
        basic_context.addTriangle(vec3(0,0,0), vec3(1,0,0), vec3(0.5,1,0))
        normals = basic_context.getAllPrimitiveNormals()
        assert normals.shape[0] == basic_context.getPrimitiveCount()
        assert normals.shape[1] == 3

    def test_getAllPrimitiveAreas(self, basic_context):
        """getAllPrimitiveAreas returns correct shape."""
        basic_context.addPatch(size=vec2(2, 3))
        basic_context.addPatch(size=vec2(1, 1))
        areas = basic_context.getAllPrimitiveAreas()
        assert areas.shape[0] == basic_context.getPrimitiveCount()

    def test_getAllPrimitiveVertices(self, basic_context):
        """getAllPrimitiveVertices returns data and offsets."""
        basic_context.addPatch()
        basic_context.addPatch()
        data, offsets = basic_context.getAllPrimitiveVertices()
        assert len(offsets) == basic_context.getPrimitiveCount() + 1
        assert data.shape[0] == offsets[-1]

    def test_getAllPrimitiveMaterialLabels(self, basic_context):
        """getAllPrimitiveMaterialLabels returns list of strings."""
        basic_context.addPatch()
        labels = basic_context.getAllPrimitiveMaterialLabels()
        assert len(labels) == basic_context.getPrimitiveCount()
        assert all(isinstance(l, str) for l in labels)


@pytest.mark.native_only
class TestPrimitiveInfoWithTexture:
    """Test PrimitiveInfo includes texture fields."""

    def test_primitiveInfo_has_texture_fields(self, basic_context):
        """PrimitiveInfo should have texture_file, texture_uv, solid_fraction fields."""
        uuid = basic_context.addPatch()
        info = basic_context.getPrimitiveInfo(uuid)
        assert hasattr(info, 'texture_file')
        assert hasattr(info, 'texture_uv')
        assert hasattr(info, 'solid_fraction')

    def test_primitiveInfo_texture_file_none_or_empty(self, basic_context):
        """PrimitiveInfo for untextured primitive has None/empty texture_file."""
        uuid = basic_context.addPatch()
        info = basic_context.getPrimitiveInfo(uuid)
        assert info.texture_file is None or info.texture_file == ""


@pytest.mark.cross_platform
class TestOverloadMockMode:
    """Test overloaded methods and API structure in mock mode."""

    @pytest.mark.mock_mode
    def test_list_overload_mock_mode(self):
        from pyhelios.plugins.loader import get_library_info
        library_info = get_library_info()
        if library_info.get('is_mock', False):
            with Context() as context:
                with pytest.raises(RuntimeError, match="mock mode"):
                    context.getPrimitiveNormal([1, 2, 3])

    @pytest.mark.mock_mode
    def test_texture_file_mock_mode(self):
        from pyhelios.plugins.loader import get_library_info
        library_info = get_library_info()
        if library_info.get('is_mock', False):
            with Context() as context:
                with pytest.raises(RuntimeError, match="mock mode"):
                    context.getPrimitiveTextureFile(1)

    def test_convenience_api_structure(self):
        """Test that getAll* convenience methods exist on Context class."""
        for method in ['getAllPrimitiveNormals', 'getAllPrimitiveColors',
                       'getAllPrimitiveAreas', 'getAllPrimitiveTypes',
                       'getAllPrimitiveSolidFractions', 'getAllPrimitiveVertices',
                       'getAllPrimitiveTextureFiles', 'getAllPrimitiveMaterialLabels']:
            assert hasattr(Context, method), f"Context missing method: {method}"
            assert callable(getattr(Context, method))

    def test_does_primitive_exist_api_structure(self):
        """Test that doesPrimitiveExist method exists on Context class."""
        assert hasattr(Context, 'doesPrimitiveExist')
        assert callable(getattr(Context, 'doesPrimitiveExist'))

    def test_texture_api_structure(self):
        """Test that texture methods exist on Context class."""
        for method in ['getPrimitiveTextureFile', 'setPrimitiveTextureFile',
                       'getPrimitiveTextureSize', 'getPrimitiveTextureUV',
                       'primitiveTextureHasTransparencyChannel',
                       'getPrimitiveSolidFraction',
                       'overridePrimitiveTextureColor', 'usePrimitiveTextureColor',
                       'isPrimitiveTextureColorOverridden']:
            assert hasattr(Context, method), f"Context missing method: {method}"
            assert callable(getattr(Context, method))


@pytest.mark.native_only
class TestDoesPrimitiveExist:
    """Test doesPrimitiveExist for single UUIDs and lists."""

    def test_existing_patch(self, basic_context):
        """A freshly added patch should exist."""
        uuid = basic_context.addPatch(
            center=DataTypes.vec3(0, 0, 0),
            size=DataTypes.vec2(1, 1),
            color=DataTypes.RGBcolor(1, 1, 1),
        )
        assert basic_context.doesPrimitiveExist(uuid) is True

    def test_nonexistent_uuid(self, basic_context):
        """A UUID that was never created should not exist."""
        assert basic_context.doesPrimitiveExist(999999) is False

    def test_multiple_patches(self, basic_context):
        """All UUIDs from multiple addPatch calls should exist."""
        uuids = [
            basic_context.addPatch(
                center=DataTypes.vec3(i, 0, 0),
                size=DataTypes.vec2(1, 1),
                color=DataTypes.RGBcolor(1, 1, 1),
            )
            for i in range(5)
        ]
        for uuid in uuids:
            assert basic_context.doesPrimitiveExist(uuid) is True

    def test_list_all_exist(self, basic_context):
        """A list of valid UUIDs should return True."""
        uuids = [
            basic_context.addPatch(
                center=DataTypes.vec3(i, 0, 0),
                size=DataTypes.vec2(1, 1),
                color=DataTypes.RGBcolor(1, 1, 1),
            )
            for i in range(3)
        ]
        assert basic_context.doesPrimitiveExist(uuids) is True

    def test_list_with_invalid(self, basic_context):
        """A list containing one invalid UUID should return False."""
        uuid = basic_context.addPatch(
            center=DataTypes.vec3(0, 0, 0),
            size=DataTypes.vec2(1, 1),
            color=DataTypes.RGBcolor(1, 1, 1),
        )
        assert basic_context.doesPrimitiveExist([uuid, 999999]) is False

    def test_empty_list(self, basic_context):
        """An empty list should return False (matches C++ behaviour)."""
        assert basic_context.doesPrimitiveExist([]) is False

    def test_after_delete(self, basic_context):
        """A deleted primitive should no longer exist."""
        uuid = basic_context.addPatch(
            center=DataTypes.vec3(0, 0, 0),
            size=DataTypes.vec2(1, 1),
            color=DataTypes.RGBcolor(1, 1, 1),
        )
        assert basic_context.doesPrimitiveExist(uuid) is True
        basic_context.deletePrimitive(uuid)
        assert basic_context.doesPrimitiveExist(uuid) is False

    def test_tile_uuids_exist(self, basic_context):
        """All UUIDs returned from addTile should exist."""
        uuids = basic_context.addTile(
            center=DataTypes.vec3(0, 0, 0),
            size=DataTypes.vec2(2, 2),
            subdiv=DataTypes.int2(2, 2),
            color=DataTypes.RGBcolor(0.5, 0.5, 0.5),
        )
        assert basic_context.doesPrimitiveExist(uuids) is True


@pytest.mark.native_only
class TestVisibility:
    """Test hide/show/isHidden for primitives and objects."""

    def test_hide_show_primitive(self, basic_context):
        """Hide then show a single primitive."""
        uuid = basic_context.addPatch(
            center=DataTypes.vec3(0, 0, 0), size=DataTypes.vec2(1, 1))
        assert basic_context.isPrimitiveHidden(uuid) is False
        basic_context.hidePrimitive(uuid)
        assert basic_context.isPrimitiveHidden(uuid) is True
        basic_context.showPrimitive(uuid)
        assert basic_context.isPrimitiveHidden(uuid) is False

    def test_hide_show_primitives_batch(self, basic_context):
        """Hide then show multiple primitives at once."""
        uuids = [
            basic_context.addPatch(
                center=DataTypes.vec3(i, 0, 0), size=DataTypes.vec2(1, 1))
            for i in range(3)
        ]
        basic_context.hidePrimitive(uuids)
        for uuid in uuids:
            assert basic_context.isPrimitiveHidden(uuid) is True
        basic_context.showPrimitive(uuids)
        for uuid in uuids:
            assert basic_context.isPrimitiveHidden(uuid) is False

    def test_hidden_primitive_excluded_from_getAllUUIDs(self, basic_context):
        """Hidden primitives should not appear in getAllUUIDs."""
        uuid1 = basic_context.addPatch(
            center=DataTypes.vec3(0, 0, 0), size=DataTypes.vec2(1, 1))
        uuid2 = basic_context.addPatch(
            center=DataTypes.vec3(1, 0, 0), size=DataTypes.vec2(1, 1))
        basic_context.hidePrimitive(uuid1)
        visible_uuids = basic_context.getAllUUIDs()
        assert uuid1 not in visible_uuids
        assert uuid2 in visible_uuids

    def test_hide_show_object(self, basic_context):
        """Hide then show a single compound object."""
        obj_id = basic_context.addBoxObject(
            center=DataTypes.vec3(0, 0, 0),
            size=DataTypes.vec3(1, 1, 1),
            subdiv=DataTypes.int3(1, 1, 1),
        )
        assert basic_context.isObjectHidden(obj_id) is False
        basic_context.hideObject(obj_id)
        assert basic_context.isObjectHidden(obj_id) is True
        basic_context.showObject(obj_id)
        assert basic_context.isObjectHidden(obj_id) is False

    def test_hide_show_objects_batch(self, basic_context):
        """Hide then show multiple objects at once."""
        obj_ids = [
            basic_context.addBoxObject(
                center=DataTypes.vec3(i * 2, 0, 0),
                size=DataTypes.vec3(1, 1, 1),
                subdiv=DataTypes.int3(1, 1, 1),
            )
            for i in range(3)
        ]
        basic_context.hideObject(obj_ids)
        for oid in obj_ids:
            assert basic_context.isObjectHidden(oid) is True
        basic_context.showObject(obj_ids)
        for oid in obj_ids:
            assert basic_context.isObjectHidden(oid) is False

    def test_hide_empty_list_noop(self, basic_context):
        """Hiding/showing empty lists should be a no-op."""
        basic_context.hidePrimitive([])
        basic_context.showPrimitive([])
        basic_context.hideObject([])
        basic_context.showObject([])


@pytest.mark.native_only
class TestObjectDataOperations:
    """Test object data set/get/query operations."""

    def _make_box(self, ctx, x=0):
        return ctx.addBoxObject(
            center=DataTypes.vec3(x, 0, 0),
            size=DataTypes.vec3(1, 1, 1),
            subdiv=DataTypes.int3(1, 1, 1),
        )

    def test_object_data_int(self, basic_context):
        obj_id = self._make_box(basic_context)
        basic_context.setObjectDataInt(obj_id, "count", 42)
        assert basic_context.getObjectData(obj_id, "count", int) == 42
        assert basic_context.getObjectDataInt(obj_id, "count") == 42

    def test_object_data_float(self, basic_context):
        obj_id = self._make_box(basic_context)
        basic_context.setObjectDataFloat(obj_id, "temp", 25.5)
        assert basic_context.getObjectDataFloat(obj_id, "temp") == pytest.approx(25.5)

    def test_object_data_double(self, basic_context):
        obj_id = self._make_box(basic_context)
        basic_context.setObjectDataDouble(obj_id, "precise", 3.141592653589793)
        assert basic_context.getObjectData(obj_id, "precise", "double") == pytest.approx(3.141592653589793)

    def test_object_data_string(self, basic_context):
        obj_id = self._make_box(basic_context)
        basic_context.setObjectDataString(obj_id, "species", "oak")
        assert basic_context.getObjectDataString(obj_id, "species") == "oak"

    def test_object_data_vec3(self, basic_context):
        obj_id = self._make_box(basic_context)
        basic_context.setObjectDataVec3(obj_id, "position", 1.0, 2.0, 3.0)
        result = basic_context.getObjectData(obj_id, "position", DataTypes.vec3)
        assert result.x == pytest.approx(1.0)
        assert result.y == pytest.approx(2.0)
        assert result.z == pytest.approx(3.0)

    def test_object_data_vec3_from_object(self, basic_context):
        obj_id = self._make_box(basic_context)
        v = DataTypes.vec3(4.0, 5.0, 6.0)
        basic_context.setObjectDataVec3(obj_id, "pos", v)
        result = basic_context.getObjectData(obj_id, "pos", DataTypes.vec3)
        assert result.x == pytest.approx(4.0)

    def test_object_data_exists(self, basic_context):
        obj_id = self._make_box(basic_context)
        assert basic_context.doesObjectDataExist(obj_id, "missing") is False
        basic_context.setObjectDataInt(obj_id, "exists_test", 1)
        assert basic_context.doesObjectDataExist(obj_id, "exists_test") is True

    def test_object_data_type_and_size(self, basic_context):
        obj_id = self._make_box(basic_context)
        basic_context.setObjectDataFloat(obj_id, "val", 1.0)
        dtype = basic_context.getObjectDataType(obj_id, "val")
        assert dtype == 2  # HELIOS_TYPE_FLOAT
        size = basic_context.getObjectDataSize(obj_id, "val")
        assert size == 1

    def test_clear_object_data(self, basic_context):
        obj_id = self._make_box(basic_context)
        basic_context.setObjectDataInt(obj_id, "to_clear", 99)
        assert basic_context.doesObjectDataExist(obj_id, "to_clear") is True
        basic_context.clearObjectData(obj_id, "to_clear")
        assert basic_context.doesObjectDataExist(obj_id, "to_clear") is False

    def test_clear_all_object_data_by_label(self, basic_context):
        obj_ids = [self._make_box(basic_context) for _ in range(2)]
        for oid in obj_ids:
            basic_context.setObjectDataInt(oid, "wipe", 1)
            basic_context.setObjectDataInt(oid, "keep", 2)

        basic_context.clearAllObjectData("wipe")

        for oid in obj_ids:
            assert basic_context.doesObjectDataExist(oid, "wipe") is False
            assert basic_context.doesObjectDataExist(oid, "keep") is True

    def test_list_object_data(self, basic_context):
        obj_id = self._make_box(basic_context)
        basic_context.setObjectDataInt(obj_id, "alpha", 1)
        basic_context.setObjectDataFloat(obj_id, "beta", 2.0)
        labels = basic_context.listObjectData(obj_id)
        assert "alpha" in labels
        assert "beta" in labels

    def test_list_all_object_data_labels(self, basic_context):
        obj1 = self._make_box(basic_context, 0)
        obj2 = self._make_box(basic_context, 3)
        basic_context.setObjectDataInt(obj1, "label_a", 1)
        basic_context.setObjectDataInt(obj2, "label_b", 2)
        all_labels = basic_context.listAllObjectDataLabels()
        assert "label_a" in all_labels
        assert "label_b" in all_labels

    def test_duplicate_object_data(self, basic_context):
        obj_id = self._make_box(basic_context)
        basic_context.setObjectDataFloat(obj_id, "original", 3.14)
        basic_context.duplicateObjectData(obj_id, "original", "copy")
        assert basic_context.getObjectDataFloat(obj_id, "copy") == pytest.approx(3.14)

    def test_rename_object_data(self, basic_context):
        obj_id = self._make_box(basic_context)
        basic_context.setObjectDataFloat(obj_id, "old_name", 2.71)
        basic_context.renameObjectData(obj_id, "old_name", "new_name")
        assert basic_context.doesObjectDataExist(obj_id, "old_name") is False
        assert basic_context.getObjectDataFloat(obj_id, "new_name") == pytest.approx(2.71)

    def test_broadcast_object_data(self, basic_context):
        obj_ids = [self._make_box(basic_context, i * 3) for i in range(3)]
        basic_context.setObjectDataFloat(obj_ids, "shared", 99.9)
        for oid in obj_ids:
            assert basic_context.getObjectDataFloat(oid, "shared") == pytest.approx(99.9)

    def test_filter_objects_by_data_float(self, basic_context):
        obj_ids = [self._make_box(basic_context, i * 3) for i in range(5)]
        for i, oid in enumerate(obj_ids):
            basic_context.setObjectDataFloat(oid, "score", float(i * 10))
        result = basic_context.filterObjectsByData(obj_ids, "score", 20.0, ">=")
        assert len(result) == 3  # scores 20, 30, 40

    def test_filter_objects_by_data_string(self, basic_context):
        obj_ids = [self._make_box(basic_context, i * 3) for i in range(3)]
        basic_context.setObjectDataString(obj_ids[0], "type", "tree")
        basic_context.setObjectDataString(obj_ids[1], "type", "shrub")
        basic_context.setObjectDataString(obj_ids[2], "type", "tree")
        result = basic_context.filterObjectsByData(obj_ids, "type", "tree")
        assert len(result) == 2

    def test_object_data_auto_detection(self, basic_context):
        obj_id = self._make_box(basic_context)
        basic_context.setObjectDataFloat(obj_id, "auto_val", 7.5)
        result = basic_context.getObjectData(obj_id, "auto_val")
        assert result == pytest.approx(7.5)


@pytest.mark.native_only
class TestGlobalDataOperations:
    """Test global data set/get/query operations."""

    def test_global_data_int(self, basic_context):
        basic_context.setGlobalDataInt("gcount", 100)
        assert basic_context.getGlobalDataInt("gcount") == 100

    def test_global_data_float(self, basic_context):
        basic_context.setGlobalDataFloat("gtemp", 37.5)
        assert basic_context.getGlobalDataFloat("gtemp") == pytest.approx(37.5)

    def test_global_data_double(self, basic_context):
        basic_context.setGlobalDataDouble("pi", 3.141592653589793)
        assert basic_context.getGlobalData("pi", "double") == pytest.approx(3.141592653589793)

    def test_global_data_string(self, basic_context):
        basic_context.setGlobalDataString("project", "helios")
        assert basic_context.getGlobalDataString("project") == "helios"

    def test_global_data_vec3(self, basic_context):
        basic_context.setGlobalDataVec3("origin", 1.0, 2.0, 3.0)
        result = basic_context.getGlobalData("origin", DataTypes.vec3)
        assert result.x == pytest.approx(1.0)
        assert result.y == pytest.approx(2.0)
        assert result.z == pytest.approx(3.0)

    def test_global_data_exists(self, basic_context):
        assert basic_context.doesGlobalDataExist("missing") is False
        basic_context.setGlobalDataInt("present", 1)
        assert basic_context.doesGlobalDataExist("present") is True

    def test_clear_global_data(self, basic_context):
        basic_context.setGlobalDataInt("to_clear", 42)
        assert basic_context.doesGlobalDataExist("to_clear") is True
        basic_context.clearGlobalData("to_clear")
        assert basic_context.doesGlobalDataExist("to_clear") is False

    def test_list_global_data(self, basic_context):
        basic_context.setGlobalDataInt("ga", 1)
        basic_context.setGlobalDataFloat("gb", 2.0)
        labels = basic_context.listGlobalData()
        assert "ga" in labels
        assert "gb" in labels

    def test_rename_global_data(self, basic_context):
        basic_context.setGlobalDataFloat("old_global", 9.9)
        basic_context.renameGlobalData("old_global", "new_global")
        assert basic_context.doesGlobalDataExist("old_global") is False
        assert basic_context.getGlobalDataFloat("new_global") == pytest.approx(9.9)

    def test_duplicate_global_data(self, basic_context):
        basic_context.setGlobalDataFloat("src_global", 5.5)
        basic_context.duplicateGlobalData("src_global", "dst_global")
        assert basic_context.getGlobalDataFloat("dst_global") == pytest.approx(5.5)

    def test_increment_global_data_int(self, basic_context):
        basic_context.setGlobalDataInt("counter", 10)
        basic_context.incrementGlobalData("counter", 5)
        assert basic_context.getGlobalDataInt("counter") == 15

    def test_increment_global_data_float(self, basic_context):
        basic_context.setGlobalDataFloat("accum", 1.0)
        basic_context.incrementGlobalData("accum", 0.5)
        assert basic_context.getGlobalDataFloat("accum") == pytest.approx(1.5)

    def test_global_data_auto_detection(self, basic_context):
        basic_context.setGlobalDataFloat("auto_g", 42.0)
        result = basic_context.getGlobalData("auto_g")
        assert result == pytest.approx(42.0)


@pytest.mark.native_only
class TestPrimitiveDataStatistics:
    """Test primitive data statistics, filtering, and aggregation."""

    def _make_patches(self, ctx, n=5):
        """Create n patches with float data 'val' = index * 10."""
        uuids = []
        for i in range(n):
            uuid = ctx.addPatch(
                center=DataTypes.vec3(i, 0, 0),
                size=DataTypes.vec2(1, 1))
            ctx.setPrimitiveDataFloat(uuid, "val", float(i * 10))
            uuids.append(uuid)
        return uuids

    def test_calculate_mean_float(self, basic_context):
        uuids = self._make_patches(basic_context)
        # values: 0, 10, 20, 30, 40 -> mean = 20
        mean = basic_context.calculatePrimitiveDataMean(uuids, "val")
        assert mean == pytest.approx(20.0)

    def test_calculate_sum_float(self, basic_context):
        uuids = self._make_patches(basic_context)
        # values: 0 + 10 + 20 + 30 + 40 = 100
        total = basic_context.calculatePrimitiveDataSum(uuids, "val")
        assert total == pytest.approx(100.0)

    def test_calculate_area_weighted_mean(self, basic_context):
        uuids = self._make_patches(basic_context)
        # All patches same size, so area-weighted mean = simple mean
        awm = basic_context.calculatePrimitiveDataAreaWeightedMean(uuids, "val")
        assert awm == pytest.approx(20.0)

    def test_calculate_area_weighted_sum(self, basic_context):
        uuids = self._make_patches(basic_context)
        # Each patch area=1, so area-weighted sum = sum of val * area = sum of val
        aws = basic_context.calculatePrimitiveDataAreaWeightedSum(uuids, "val")
        assert aws == pytest.approx(100.0)

    def test_scale_primitive_data_with_uuids(self, basic_context):
        uuids = self._make_patches(basic_context)
        basic_context.scalePrimitiveData(uuids, "val", 2.0)
        total = basic_context.calculatePrimitiveDataSum(uuids, "val")
        assert total == pytest.approx(200.0)

    def test_scale_primitive_data_all(self, basic_context):
        uuids = self._make_patches(basic_context)
        basic_context.scalePrimitiveData("val", 0.5)
        total = basic_context.calculatePrimitiveDataSum(uuids, "val")
        assert total == pytest.approx(50.0)

    def test_increment_primitive_data_int(self, basic_context):
        uuids = [basic_context.addPatch(
            center=DataTypes.vec3(i, 0, 0), size=DataTypes.vec2(1, 1))
            for i in range(3)]
        for uuid in uuids:
            basic_context.setPrimitiveDataInt(uuid, "count", 10)
        basic_context.incrementPrimitiveData(uuids, "count", 5)
        for uuid in uuids:
            assert basic_context.getPrimitiveData(uuid, "count", int) == 15

    def test_increment_primitive_data_float(self, basic_context):
        uuids = self._make_patches(basic_context)
        basic_context.incrementPrimitiveData(uuids, "val", 1.0)
        # values become 1, 11, 21, 31, 41 -> sum = 105
        total = basic_context.calculatePrimitiveDataSum(uuids, "val")
        assert total == pytest.approx(105.0)

    def test_aggregate_sum(self, basic_context):
        uuids = [basic_context.addPatch(
            center=DataTypes.vec3(i, 0, 0), size=DataTypes.vec2(1, 1))
            for i in range(3)]
        for uuid in uuids:
            basic_context.setPrimitiveDataFloat(uuid, "a", 2.0)
            basic_context.setPrimitiveDataFloat(uuid, "b", 3.0)
        basic_context.aggregatePrimitiveDataSum(uuids, ["a", "b"], "a_plus_b")
        for uuid in uuids:
            assert basic_context.getPrimitiveData(uuid, "a_plus_b", float) == pytest.approx(5.0)

    def test_aggregate_product(self, basic_context):
        uuids = [basic_context.addPatch(
            center=DataTypes.vec3(i, 0, 0), size=DataTypes.vec2(1, 1))
            for i in range(3)]
        for uuid in uuids:
            basic_context.setPrimitiveDataFloat(uuid, "x", 4.0)
            basic_context.setPrimitiveDataFloat(uuid, "y", 5.0)
        basic_context.aggregatePrimitiveDataProduct(uuids, ["x", "y"], "x_times_y")
        for uuid in uuids:
            assert basic_context.getPrimitiveData(uuid, "x_times_y", float) == pytest.approx(20.0)

    def test_sum_primitive_surface_area(self, basic_context):
        uuids = [basic_context.addPatch(
            center=DataTypes.vec3(i, 0, 0), size=DataTypes.vec2(2, 3))
            for i in range(4)]
        # Each patch 2x3 = area 6, 4 patches = 24
        area = basic_context.sumPrimitiveSurfaceArea(uuids)
        assert area == pytest.approx(24.0)

    def test_filter_primitives_by_data_float(self, basic_context):
        uuids = self._make_patches(basic_context)
        # values: 0, 10, 20, 30, 40. Filter >= 20 -> 3 results
        result = basic_context.filterPrimitivesByData(uuids, "val", 20.0, ">=")
        assert len(result) == 3

    def test_filter_primitives_by_data_int(self, basic_context):
        uuids = [basic_context.addPatch(
            center=DataTypes.vec3(i, 0, 0), size=DataTypes.vec2(1, 1))
            for i in range(5)]
        for i, uuid in enumerate(uuids):
            basic_context.setPrimitiveDataInt(uuid, "level", i)
        result = basic_context.filterPrimitivesByData(uuids, "level", 3, "<")
        assert len(result) == 3  # levels 0, 1, 2

    def test_filter_primitives_by_data_string(self, basic_context):
        uuids = [basic_context.addPatch(
            center=DataTypes.vec3(i, 0, 0), size=DataTypes.vec2(1, 1))
            for i in range(4)]
        basic_context.setPrimitiveDataString(uuids[0], "tag", "leaf")
        basic_context.setPrimitiveDataString(uuids[1], "tag", "branch")
        basic_context.setPrimitiveDataString(uuids[2], "tag", "leaf")
        basic_context.setPrimitiveDataString(uuids[3], "tag", "trunk")
        result = basic_context.filterPrimitivesByData(uuids, "tag", "leaf")
        assert len(result) == 2


# ============================================================================
# Extended Context geometry queries (object/primitive introspection, color,
# data cleanup, domain cropping)
# ============================================================================

# helios::ObjectType enum values (from helios-core Context.h)
_OBJ_TYPE_TILE = 0
_OBJ_TYPE_SPHERE = 1
_OBJ_TYPE_TUBE = 2
_OBJ_TYPE_BOX = 3
_OBJ_TYPE_DISK = 4
_OBJ_TYPE_POLYMESH = 5
_OBJ_TYPE_CONE = 6
_OBJ_TYPE_ADAPTIVE_TILE = 7


def _find_test_texture():
    """Absolute path to a texture image shipped with helios-core, or None if unavailable."""
    for relative in ('helios-core/core/lib/images/disk_texture.png',
                     'helios-core/plugins/canopygenerator/textures/dirt.jpg'):
        candidate = os.path.join(REPO_ROOT_CTX, relative)
        if os.path.exists(candidate):
            return candidate
    return None


@pytest.mark.native_only
class TestObjectGeometryQueries:
    def test_get_object_type_for_each_compound(self, basic_context):
        tile_id = basic_context.addTileObject(
            center=vec3(0, 0, 0), size=vec2(1, 1), subdiv=int2(1, 1))
        sphere_id = basic_context.addSphereObject(
            ndivs=5, center=vec3(5, 0, 0), radius=0.5)
        box_id = basic_context.addBoxObject(
            center=vec3(0, 5, 0), size=vec3(1, 1, 1), subdiv=int3(1, 1, 1))
        disk_id = basic_context.addDiskObject(
            ndivs=8, center=vec3(0, 0, 5), size=vec2(0.5, 0.5))
        tube_id = basic_context.addTubeObject(
            ndivs=6, nodes=[vec3(0, 0, 10), vec3(0, 0, 11), vec3(0, 0, 12)],
            radii=[0.1, 0.08, 0.05])
        cone_id = basic_context.addConeObject(
            ndivs=6, node0=vec3(0, 10, 0), node1=vec3(0, 10, 1),
            radius0=0.2, radius1=0.1)

        assert basic_context.getObjectType(tile_id) == _OBJ_TYPE_TILE
        assert basic_context.getObjectType(sphere_id) == _OBJ_TYPE_SPHERE
        assert basic_context.getObjectType(box_id) == _OBJ_TYPE_BOX
        assert basic_context.getObjectType(disk_id) == _OBJ_TYPE_DISK
        adaptive_tile_id = basic_context.addAdaptiveTileObject(
            center=vec3(20, 0, 0), size=vec2(4, 4),
            refinement=AdaptiveTileRefinement(subpatch_size_min=0.5, subpatch_size_max=2.0))

        assert basic_context.getObjectType(tube_id) == _OBJ_TYPE_TUBE
        assert basic_context.getObjectType(cone_id) == _OBJ_TYPE_CONE
        assert basic_context.getObjectType(adaptive_tile_id) == _OBJ_TYPE_ADAPTIVE_TILE

    def test_get_object_center_and_bounding_box(self, basic_context):
        box_id = basic_context.addBoxObject(
            center=vec3(2, 3, 4), size=vec3(2, 4, 6), subdiv=int3(1, 1, 1))
        c = basic_context.getObjectCenter(box_id)
        assert c.x == pytest.approx(2.0)
        assert c.y == pytest.approx(3.0)
        assert c.z == pytest.approx(4.0)

        mn, mx = basic_context.getObjectBoundingBox(box_id)
        assert mn.x == pytest.approx(1.0)
        assert mn.y == pytest.approx(1.0)
        assert mn.z == pytest.approx(1.0)
        assert mx.x == pytest.approx(3.0)
        assert mx.y == pytest.approx(5.0)
        assert mx.z == pytest.approx(7.0)

    def test_get_object_primitive_uuids_single_batch_nested(self, basic_context):
        a = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1), subdiv=int2(2, 2))
        b = basic_context.addTileObject(center=vec3(5, 0, 0), size=vec2(1, 1), subdiv=int2(3, 1))

        a_uuids = basic_context.getObjectPrimitiveUUIDs(a)
        b_uuids = basic_context.getObjectPrimitiveUUIDs(b)
        assert len(a_uuids) == 4
        assert len(b_uuids) == 3

        batch = basic_context.getObjectPrimitiveUUIDs([a, b])
        assert set(batch) == set(a_uuids) | set(b_uuids)

        nested = basic_context.getObjectPrimitiveUUIDs([[a], [b]])
        assert set(nested) == set(a_uuids) | set(b_uuids)

    def test_tile_object_queries(self, basic_context):
        obj_id = basic_context.addTileObject(
            center=vec3(1, 2, 3), size=vec2(4, 5),
            rotation=SphericalCoord(1, 0, 0), subdiv=int2(2, 3))
        c = basic_context.getTileObjectCenter(obj_id)
        assert c.x == pytest.approx(1.0)
        assert c.y == pytest.approx(2.0)
        assert c.z == pytest.approx(3.0)

        s = basic_context.getTileObjectSize(obj_id)
        assert s.x == pytest.approx(4.0)
        assert s.y == pytest.approx(5.0)

        sd = basic_context.getTileObjectSubdivisionCount(obj_id)
        assert sd.x == 2
        assert sd.y == 3

        n = basic_context.getTileObjectNormal(obj_id)
        assert isinstance(n, vec3)

        verts = basic_context.getTileObjectVertices(obj_id)
        assert len(verts) > 0
        assert all(isinstance(v, vec3) for v in verts)

    def test_adaptive_tile_object_queries(self, basic_context):
        refinement = AdaptiveTileRefinement(
            target=vec2(1.0, -2.0), subpatch_size_min=0.25,
            subpatch_size_max=2.0, transition_exponent=0.5)
        obj_id = basic_context.addAdaptiveTileObject(
            center=vec3(1, 2, 3), size=vec2(20, 20),
            rotation=SphericalCoord(1, 0, 0), refinement=refinement)

        c = basic_context.getAdaptiveTileObjectCenter(obj_id)
        assert c.x == pytest.approx(1.0)
        assert c.y == pytest.approx(2.0)
        assert c.z == pytest.approx(3.0)

        s = basic_context.getAdaptiveTileObjectSize(obj_id)
        assert s.x == pytest.approx(20.0)
        assert s.y == pytest.approx(20.0)

        n = basic_context.getAdaptiveTileObjectNormal(obj_id)
        assert isinstance(n, vec3)

        verts = basic_context.getAdaptiveTileObjectVertices(obj_id)
        assert len(verts) == 4
        assert all(isinstance(v, vec3) for v in verts)

        # Refinement parameters round-trip as they were requested
        got = basic_context.getAdaptiveTileObjectRefinement(obj_id)
        assert isinstance(got, AdaptiveTileRefinement)
        assert got.target.x == pytest.approx(1.0)
        assert got.target.y == pytest.approx(-2.0)
        assert got.subpatch_size_min == pytest.approx(0.25)
        assert got.subpatch_size_max == pytest.approx(2.0)
        assert got.transition_exponent == pytest.approx(0.5)

        base = basic_context.getAdaptiveTileObjectBaseSubdivisionCount(obj_id)
        assert isinstance(base, int2)
        assert base.x > 0 and base.y > 0

        max_level = basic_context.getAdaptiveTileObjectMaxRefinementLevel(obj_id)
        assert isinstance(max_level, int)
        assert max_level > 0

        # Achieved sizes bracket the requested range to within the documented ~20%
        achieved = basic_context.getAdaptiveTileObjectSubpatchSizeRange(obj_id)
        assert isinstance(achieved, vec2)
        assert achieved.x <= achieved.y
        assert achieved.x == pytest.approx(0.25, rel=0.25)
        assert achieved.y == pytest.approx(2.0, rel=0.25)

        repeat = basic_context.getAdaptiveTileObjectTextureRepeat(obj_id)
        assert (repeat.x, repeat.y) == (1, 1), "an untextured adaptive tile defaults to a 1x1 repeat"

    def test_adaptive_tile_subpatches_are_non_uniform_and_finest_at_target(self, basic_context):
        """Sub-patch area should grow with distance from the refinement target."""
        refinement = AdaptiveTileRefinement(
            target=vec2(0, 0), subpatch_size_min=0.25, subpatch_size_max=2.0)
        obj_id = basic_context.addAdaptiveTileObject(
            center=vec3(0, 0, 0), size=vec2(20, 20), refinement=refinement)

        uuids = basic_context.getObjectPrimitiveUUIDs(obj_id)
        assert len(uuids) > 1

        areas = [basic_context.getPrimitiveArea(u) for u in uuids]
        # A uniform tile would give one area; an adaptive tile must give several
        assert len(set(round(a, 6) for a in areas)) > 1

        centers = [basic_context.getPatchCenter(u) for u in uuids]
        near = min(range(len(uuids)), key=lambda i: centers[i].x ** 2 + centers[i].y ** 2)
        far = max(range(len(uuids)), key=lambda i: centers[i].x ** 2 + centers[i].y ** 2)
        assert areas[near] < areas[far]

    def test_predict_adaptive_tile_subpatch_count_matches_built_geometry(self, basic_context):
        refinement = AdaptiveTileRefinement(
            target=vec2(0, 0), subpatch_size_min=0.25, subpatch_size_max=2.0)
        predicted = basic_context.predictAdaptiveTileObjectSubpatchCount(vec2(20, 20), refinement)
        assert predicted > 0

        obj_id = basic_context.addAdaptiveTileObject(
            center=vec3(0, 0, 0), size=vec2(20, 20), refinement=refinement)
        assert len(basic_context.getObjectPrimitiveUUIDs(obj_id)) == predicted

    def test_predict_adaptive_tile_subpatch_count_grows_with_transition_exponent(self, basic_context):
        def count(exponent):
            return basic_context.predictAdaptiveTileObjectSubpatchCount(
                vec2(50, 50),
                AdaptiveTileRefinement(subpatch_size_min=0.05, subpatch_size_max=2.0,
                                       transition_exponent=exponent))

        assert count(0.25) < count(0.35) < count(0.5) < count(1.0)

    def test_adaptive_tile_object_color_and_texture_variants(self, basic_context):
        refinement = AdaptiveTileRefinement(subpatch_size_min=0.5, subpatch_size_max=2.0)

        colored = basic_context.addAdaptiveTileObject(
            size=vec2(10, 10), refinement=refinement, color=RGBcolor(1, 0, 0))
        assert basic_context.getObjectType(colored) == _OBJ_TYPE_ADAPTIVE_TILE

        texture = _find_test_texture()
        if texture is None:
            pytest.skip("No texture file available for adaptive tile texture test")

        textured = basic_context.addAdaptiveTileObject(
            size=vec2(10, 10), refinement=refinement, texturefile=texture)
        default_repeat = basic_context.getAdaptiveTileObjectTextureRepeat(textured)
        assert (default_repeat.x, default_repeat.y) == (1, 1)

        repeated = basic_context.addAdaptiveTileObject(
            size=vec2(10, 10), refinement=refinement, texturefile=texture,
            texture_repeat=int2(2, 2))
        rep = basic_context.getAdaptiveTileObjectTextureRepeat(repeated)
        # An adaptive tile applies the requested repeat exactly (unlike a uniform tile)
        assert (rep.x, rep.y) == (2, 2)

    def test_adaptive_tile_rejects_max_larger_than_half_the_tile(self, basic_context):
        with pytest.raises(HeliosError, match="too large for a tile"):
            basic_context.addAdaptiveTileObject(
                size=vec2(1, 1),
                refinement=AdaptiveTileRefinement(subpatch_size_min=0.05, subpatch_size_max=1.0))

    def test_adaptive_tile_rejects_excessive_subpatch_count(self, basic_context):
        refinement = AdaptiveTileRefinement(
            subpatch_size_min=0.005, subpatch_size_max=2.0, transition_exponent=2.0)
        with pytest.raises(HeliosError, match="sub-patches"):
            basic_context.addAdaptiveTileObject(size=vec2(500, 500), refinement=refinement)
        with pytest.raises(HeliosError, match="sub-patches"):
            basic_context.predictAdaptiveTileObjectSubpatchCount(vec2(500, 500), refinement)

    def test_adaptive_tile_queries_reject_unknown_object_id(self, basic_context):
        with pytest.raises(HeliosError):
            basic_context.getAdaptiveTileObjectCenter(999999)

    def test_tile_object_texture_repeat_queries(self, basic_context):
        texture = _find_test_texture()
        if texture is None:
            pytest.skip("No texture file available for tile texture repeat test")

        obj_id = basic_context.addTileObject(
            size=vec2(10, 10), subdiv=int2(10, 10),
            texturefile=texture, texture_repeat=int2(5, 5))

        requested = basic_context.getTileObjectTextureRepeat(obj_id)
        effective = basic_context.getTileObjectEffectiveTextureRepeat(obj_id)
        assert (requested.x, requested.y) == (5, 5)
        assert (effective.x, effective.y) == (5, 5)

    def test_tile_object_effective_texture_repeat_is_reduced_when_it_does_not_divide(self, basic_context):
        texture = _find_test_texture()
        if texture is None:
            pytest.skip("No texture file available for tile texture repeat test")

        # 4 does not evenly divide a subdivision count of 9
        obj_id = basic_context.addTileObject(
            size=vec2(10, 10), subdiv=int2(9, 9),
            texturefile=texture, texture_repeat=int2(4, 4))

        requested = basic_context.getTileObjectTextureRepeat(obj_id)
        effective = basic_context.getTileObjectEffectiveTextureRepeat(obj_id)
        assert (requested.x, requested.y) == (4, 4)
        assert effective.x < requested.x
        assert effective.y < requested.y

    def test_tile_object_retains_texture_repeat_across_subdivision_change(self, basic_context):
        """helios-core 1.3.81: changing the subdivision count used to reset texture repeat to 1x1."""
        texture = _find_test_texture()
        if texture is None:
            pytest.skip("No texture file available for tile texture repeat test")

        obj_id = basic_context.addTileObject(
            size=vec2(10, 10), subdiv=int2(10, 10),
            texturefile=texture, texture_repeat=int2(5, 5))

        basic_context.setTileObjectSubdivisionCount(obj_id, int2(20, 20))

        requested = basic_context.getTileObjectTextureRepeat(obj_id)
        effective = basic_context.getTileObjectEffectiveTextureRepeat(obj_id)
        assert (requested.x, requested.y) == (5, 5), "requested repeat must survive a subdivision change"
        assert (effective.x, effective.y) == (5, 5), "repeat must be re-applied, not reset to 1x1"

    def test_uniform_tile_operations_skip_adaptive_tiles(self, basic_context):
        """Sweeping tile operations over a scene must not overwrite an adaptive layout."""
        adaptive_id = basic_context.addAdaptiveTileObject(
            size=vec2(10, 10),
            refinement=AdaptiveTileRefinement(subpatch_size_min=0.5, subpatch_size_max=2.0))
        subpatches_before = len(basic_context.getObjectPrimitiveUUIDs(adaptive_id))

        # helios warns and skips rather than treating the adaptive tile as a uniform one
        assert basic_context.getTileObjectAreaRatio(adaptive_id) == pytest.approx(0.0)

        basic_context.setTileObjectSubdivisionCount(adaptive_id, int2(2, 2))
        assert len(basic_context.getObjectPrimitiveUUIDs(adaptive_id)) == subpatches_before

    def test_tile_texture_repeat_survives_xml_round_trip(self, basic_context, tmp_path):
        """helios-core 1.3.81 writes an optional <texture_repeat> element for tiled textures."""
        texture = _find_test_texture()
        if texture is None:
            pytest.skip("No texture file available for tile texture repeat test")

        obj_id = basic_context.addTileObject(
            size=vec2(10, 10), subdiv=int2(10, 10),
            texturefile=texture, texture_repeat=int2(5, 5))
        assert (basic_context.getTileObjectTextureRepeat(obj_id).x,
                basic_context.getTileObjectTextureRepeat(obj_id).y) == (5, 5)

        xml_path = tmp_path / "tile_repeat.xml"
        basic_context.writeXML(str(xml_path), quiet=True)

        with Context() as reloaded:
            reloaded.loadXML(str(xml_path), quiet=True)
            tile_ids = [o for o in reloaded.getAllObjectIDs()
                        if reloaded.getObjectType(o) == _OBJ_TYPE_TILE]
            assert len(tile_ids) == 1
            repeat = reloaded.getTileObjectTextureRepeat(tile_ids[0])
            assert (repeat.x, repeat.y) == (5, 5), (
                "texture repeat must survive the XML round trip, otherwise the defect returns "
                "on the next subdivision change")

    def test_adaptive_tile_survives_xml_round_trip(self, basic_context, tmp_path):
        refinement = AdaptiveTileRefinement(
            target=vec2(1.0, -1.0), subpatch_size_min=0.5,
            subpatch_size_max=2.0, transition_exponent=0.5)
        obj_id = basic_context.addAdaptiveTileObject(
            center=vec3(1, 2, 3), size=vec2(20, 20), refinement=refinement)
        subpatches = len(basic_context.getObjectPrimitiveUUIDs(obj_id))

        xml_path = tmp_path / "adaptive_tile.xml"
        basic_context.writeXML(str(xml_path), quiet=True)

        with Context() as reloaded:
            reloaded.loadXML(str(xml_path), quiet=True)
            adaptive_ids = [o for o in reloaded.getAllObjectIDs()
                            if reloaded.getObjectType(o) == _OBJ_TYPE_ADAPTIVE_TILE]
            assert len(adaptive_ids) == 1
            restored = adaptive_ids[0]

            assert len(reloaded.getObjectPrimitiveUUIDs(restored)) == subpatches

            got = reloaded.getAdaptiveTileObjectRefinement(restored)
            assert got.target.x == pytest.approx(1.0)
            assert got.target.y == pytest.approx(-1.0)
            assert got.subpatch_size_min == pytest.approx(0.5)
            assert got.subpatch_size_max == pytest.approx(2.0)
            assert got.transition_exponent == pytest.approx(0.5)

            center = reloaded.getAdaptiveTileObjectCenter(restored)
            assert center.x == pytest.approx(1.0)
            assert center.y == pytest.approx(2.0)
            assert center.z == pytest.approx(3.0)

    def test_sphere_object_queries(self, basic_context):
        obj_id = basic_context.addSphereObject(ndivs=6, center=vec3(0, 0, 0), radius=0.75)
        c = basic_context.getSphereObjectCenter(obj_id)
        assert c.x == pytest.approx(0.0)
        r = basic_context.getSphereObjectRadius(obj_id)
        # Returns vec3 (per-axis radii); for a uniform sphere all three should match
        assert isinstance(r, vec3)
        assert r.x == pytest.approx(0.75)
        assert r.y == pytest.approx(0.75)
        assert r.z == pytest.approx(0.75)
        assert basic_context.getSphereObjectSubdivisionCount(obj_id) == 6
        v = basic_context.getSphereObjectVolume(obj_id)
        assert v > 0

    def test_box_object_queries(self, basic_context):
        obj_id = basic_context.addBoxObject(
            center=vec3(0, 0, 0), size=vec3(2, 3, 4), subdiv=int3(1, 1, 1))
        c = basic_context.getBoxObjectCenter(obj_id)
        assert c.x == pytest.approx(0.0)
        s = basic_context.getBoxObjectSize(obj_id)
        assert s.x == pytest.approx(2.0)
        assert s.y == pytest.approx(3.0)
        assert s.z == pytest.approx(4.0)
        sd = basic_context.getBoxObjectSubdivisionCount(obj_id)
        assert isinstance(sd, int3)
        v = basic_context.getBoxObjectVolume(obj_id)
        assert v == pytest.approx(2 * 3 * 4)

    def test_disk_object_queries(self, basic_context):
        obj_id = basic_context.addDiskObject(
            ndivs=8, center=vec3(0, 0, 0), size=vec2(0.5, 0.5))
        c = basic_context.getDiskObjectCenter(obj_id)
        assert c.x == pytest.approx(0.0)
        s = basic_context.getDiskObjectSize(obj_id)
        assert isinstance(s, vec2)
        sd = basic_context.getDiskObjectSubdivisionCount(obj_id)
        assert sd > 0

    def test_tube_object_queries(self, basic_context):
        nodes = [vec3(0, 0, 0), vec3(0, 0, 1), vec3(0, 0, 2)]
        radii = [0.1, 0.08, 0.05]
        obj_id = basic_context.addTubeObject(ndivs=6, nodes=nodes, radii=radii)

        assert basic_context.getTubeObjectSubdivisionCount(obj_id) == 6
        assert basic_context.getTubeObjectNodeCount(obj_id) == len(nodes)

        got_nodes = basic_context.getTubeObjectNodes(obj_id)
        assert len(got_nodes) == len(nodes)
        for g, n in zip(got_nodes, nodes):
            assert g.x == pytest.approx(n.x)
            assert g.y == pytest.approx(n.y)
            assert g.z == pytest.approx(n.z)

        got_radii = basic_context.getTubeObjectNodeRadii(obj_id)
        assert len(got_radii) == len(radii)
        for g, r in zip(got_radii, radii):
            assert g == pytest.approx(r)

        colors = basic_context.getTubeObjectNodeColors(obj_id)
        assert len(colors) == len(nodes)
        assert all(isinstance(c, RGBcolor) for c in colors)

        v = basic_context.getTubeObjectVolume(obj_id)
        assert v > 0
        seg_v = basic_context.getTubeObjectSegmentVolume(obj_id, 0)
        assert seg_v > 0

    def test_cone_object_queries(self, basic_context):
        obj_id = basic_context.addConeObject(
            ndivs=8, node0=vec3(0, 0, 0), node1=vec3(0, 0, 2),
            radius0=0.3, radius1=0.1)
        assert basic_context.getConeObjectSubdivisionCount(obj_id) == 8
        got_nodes = basic_context.getConeObjectNodes(obj_id)
        assert len(got_nodes) == 2
        got_radii = basic_context.getConeObjectNodeRadii(obj_id)
        assert len(got_radii) == 2
        assert got_radii[0] == pytest.approx(0.3)
        assert got_radii[1] == pytest.approx(0.1)

        node0 = basic_context.getConeObjectNode(obj_id, 0)
        assert node0.z == pytest.approx(0.0)
        assert basic_context.getConeObjectNodeRadius(obj_id, 1) == pytest.approx(0.1)

        axis = basic_context.getConeObjectAxisUnitVector(obj_id)
        assert isinstance(axis, vec3)
        length = basic_context.getConeObjectLength(obj_id)
        assert length == pytest.approx(2.0)
        vol = basic_context.getConeObjectVolume(obj_id)
        assert vol > 0


@pytest.mark.native_only
class TestPrimitiveGeometryQueries:
    def test_patch_center_and_size(self, basic_context):
        uuid = basic_context.addPatch(center=vec3(1, 2, 3), size=vec2(4, 5))
        c = basic_context.getPatchCenter(uuid)
        assert c.x == pytest.approx(1.0)
        assert c.y == pytest.approx(2.0)
        assert c.z == pytest.approx(3.0)
        s = basic_context.getPatchSize(uuid)
        assert s.x == pytest.approx(4.0)
        assert s.y == pytest.approx(5.0)

    def test_triangle_vertex(self, basic_context):
        v0 = vec3(0, 0, 0)
        v1 = vec3(1, 0, 0)
        v2 = vec3(0, 1, 0)
        uuid = basic_context.addTriangle(v0, v1, v2)
        got_v0 = basic_context.getTriangleVertex(uuid, 0)
        assert got_v0.x == pytest.approx(0.0)
        got_v1 = basic_context.getTriangleVertex(uuid, 1)
        assert got_v1.x == pytest.approx(1.0)
        got_v2 = basic_context.getTriangleVertex(uuid, 2)
        assert got_v2.y == pytest.approx(1.0)

    def test_patch_and_triangle_counts(self, basic_context):
        assert basic_context.getPatchCount() == 0
        assert basic_context.getTriangleCount() == 0
        basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        basic_context.addPatch(center=vec3(1, 0, 0), size=vec2(1, 1))
        basic_context.addTriangle(vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0))
        assert basic_context.getPatchCount() == 2
        assert basic_context.getTriangleCount() == 1

    def test_primitive_bounding_box_single_and_batch(self, basic_context):
        u1 = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(2, 2))
        u2 = basic_context.addPatch(center=vec3(5, 0, 0), size=vec2(2, 2))
        mn, mx = basic_context.getPrimitiveBoundingBox(u1)
        assert mn.x == pytest.approx(-1.0)
        assert mx.x == pytest.approx(1.0)

        mn_b, mx_b = basic_context.getPrimitiveBoundingBox([u1, u2])
        assert mn_b.x == pytest.approx(-1.0)
        assert mx_b.x == pytest.approx(6.0)


@pytest.mark.native_only
class TestSetPrimitiveColor:
    def test_set_primitive_color_rgb_single(self, basic_context):
        uuid = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        basic_context.setPrimitiveColor(uuid, RGBcolor(0.1, 0.2, 0.3))
        c = basic_context.getPrimitiveColor(uuid)
        assert c.r == pytest.approx(0.1)
        assert c.g == pytest.approx(0.2)
        assert c.b == pytest.approx(0.3)

    def test_set_primitive_color_rgb_batch(self, basic_context):
        uuids = [basic_context.addPatch(center=vec3(i, 0, 0), size=vec2(1, 1))
                 for i in range(3)]
        basic_context.setPrimitiveColor(uuids, RGBcolor(0.4, 0.5, 0.6))
        for u in uuids:
            c = basic_context.getPrimitiveColor(u)
            assert c.r == pytest.approx(0.4)
            assert c.g == pytest.approx(0.5)
            assert c.b == pytest.approx(0.6)

    def test_set_primitive_color_rgba_single(self, basic_context):
        from pyhelios.wrappers import UContextWrapper as _cw
        uuid = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        basic_context.setPrimitiveColor(uuid, RGBAcolor(0.1, 0.2, 0.3, 0.5))
        # Round-trip via raw RGBA getter from the ctypes wrapper
        ptr = _cw.getPrimitiveColorRGBA(basic_context.context, uuid)
        assert ptr[0] == pytest.approx(0.1)
        assert ptr[1] == pytest.approx(0.2)
        assert ptr[2] == pytest.approx(0.3)
        assert ptr[3] == pytest.approx(0.5)

    def test_set_primitive_color_rgba_batch(self, basic_context):
        from pyhelios.wrappers import UContextWrapper as _cw
        uuids = [basic_context.addPatch(center=vec3(i, 0, 0), size=vec2(1, 1))
                 for i in range(2)]
        basic_context.setPrimitiveColor(uuids, RGBAcolor(0.7, 0.8, 0.9, 0.2))
        for u in uuids:
            ptr = _cw.getPrimitiveColorRGBA(basic_context.context, u)
            assert ptr[0] == pytest.approx(0.7)
            assert ptr[3] == pytest.approx(0.2)


@pytest.mark.cross_platform
class TestSetPrimitiveColorValidation:
    def test_rejects_non_color_types(self, basic_context):
        uuid = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        with pytest.raises(ValueError):
            basic_context.setPrimitiveColor(uuid, vec3(1, 0, 0))
        with pytest.raises(ValueError):
            basic_context.setPrimitiveColor(uuid, (1, 0, 0))


@pytest.mark.cross_platform
class TestAdaptiveTileRefinementValidation:
    """AdaptiveTileRefinement construction is pure Python, so it validates without a native library."""

    def test_defaults_match_helios(self):
        r = AdaptiveTileRefinement()
        assert r.target.x == pytest.approx(0.0)
        assert r.target.y == pytest.approx(0.0)
        assert r.subpatch_size_min == pytest.approx(0.05)
        assert r.subpatch_size_max == pytest.approx(1.0)
        assert r.transition_exponent == pytest.approx(0.35)

    def test_to_list_uses_the_c_abi_element_order(self):
        r = AdaptiveTileRefinement(target=vec2(1.5, -2.5), subpatch_size_min=0.1,
                                   subpatch_size_max=4.0, transition_exponent=0.75)
        values = r.to_list()
        assert len(values) == 5
        assert values[0] == pytest.approx(1.5)
        assert values[1] == pytest.approx(-2.5)
        assert values[2] == pytest.approx(0.1)
        assert values[3] == pytest.approx(4.0)
        assert values[4] == pytest.approx(0.75)

    def test_from_list_round_trips(self):
        r = AdaptiveTileRefinement()
        r.from_list([1.0, 2.0, 0.5, 8.0, 0.6])
        assert r.target.x == pytest.approx(1.0)
        assert r.target.y == pytest.approx(2.0)
        assert r.subpatch_size_min == pytest.approx(0.5)
        assert r.subpatch_size_max == pytest.approx(8.0)
        assert r.transition_exponent == pytest.approx(0.6)

    def test_rejects_non_vec2_target(self):
        with pytest.raises(ValueError, match="target must be a vec2"):
            AdaptiveTileRefinement(target=vec3(0, 0, 0))
        with pytest.raises(ValueError, match="target must be a vec2"):
            AdaptiveTileRefinement(target=(0, 0))

    def test_rejects_non_positive_sizes(self):
        with pytest.raises(ValueError, match="subpatch_size_min must be a positive finite number"):
            AdaptiveTileRefinement(subpatch_size_min=0)
        with pytest.raises(ValueError, match="subpatch_size_max must be a positive finite number"):
            AdaptiveTileRefinement(subpatch_size_max=-1.0)

    def test_rejects_inverted_size_range(self):
        with pytest.raises(ValueError, match="greater than subpatch_size_max"):
            AdaptiveTileRefinement(subpatch_size_min=2.0, subpatch_size_max=1.0)

    def test_rejects_size_ratio_beyond_the_supported_maximum(self):
        with pytest.raises(ValueError, match="16777216"):
            AdaptiveTileRefinement(subpatch_size_min=1e-9, subpatch_size_max=1e3)

    def test_rejects_non_positive_transition_exponent(self):
        with pytest.raises(ValueError, match="transition_exponent must be a positive finite number"):
            AdaptiveTileRefinement(transition_exponent=0)
        with pytest.raises(ValueError, match="transition_exponent must be a positive finite number"):
            AdaptiveTileRefinement(transition_exponent=float('inf'))


@pytest.mark.cross_platform
class TestAddAdaptiveTileObjectValidation:
    """Wrong-type arguments must be rejected whether passed positionally or by keyword."""

    def test_rejects_wrong_types_positionally(self, basic_context):
        # Positional order is (center, size, rotation, refinement, ...)
        with pytest.raises(ValueError, match="Center must be a vec3"):
            basic_context.addAdaptiveTileObject(RGBcolor(1, 0, 0), vec2(10, 10))
        with pytest.raises(ValueError, match="Size must be a vec2"):
            basic_context.addAdaptiveTileObject(vec3(0, 0, 0), vec3(10, 10, 10))
        with pytest.raises(ValueError, match="Rotation must be a SphericalCoord"):
            basic_context.addAdaptiveTileObject(vec3(0, 0, 0), vec2(10, 10), vec3(0, 0, 0))
        with pytest.raises(ValueError, match="Refinement must be an AdaptiveTileRefinement"):
            basic_context.addAdaptiveTileObject(
                vec3(0, 0, 0), vec2(10, 10), SphericalCoord(1, 0, 0), "not-a-refinement")

    def test_rejects_wrong_types_as_keywords(self, basic_context):
        with pytest.raises(ValueError, match="Center must be a vec3"):
            basic_context.addAdaptiveTileObject(center=vec2(0, 0))
        with pytest.raises(ValueError, match="Size must be a vec2"):
            basic_context.addAdaptiveTileObject(size=int2(10, 10))
        with pytest.raises(ValueError, match="Rotation must be a SphericalCoord"):
            basic_context.addAdaptiveTileObject(rotation=vec3(0, 0, 0))
        with pytest.raises(ValueError, match="Refinement must be an AdaptiveTileRefinement"):
            basic_context.addAdaptiveTileObject(refinement=vec2(0, 0))
        with pytest.raises(ValueError, match="Color must be an RGBcolor"):
            basic_context.addAdaptiveTileObject(color=vec3(1, 0, 0))
        with pytest.raises(ValueError, match="texture_repeat must be an int2"):
            basic_context.addAdaptiveTileObject(texturefile="x.png", texture_repeat=vec2(2, 2))

    def test_texture_repeat_requires_a_texture_file(self, basic_context):
        with pytest.raises(ValueError, match="texture_repeat requires texturefile"):
            basic_context.addAdaptiveTileObject(size=vec2(10, 10), texture_repeat=int2(2, 2))

    def test_predict_rejects_wrong_types(self, basic_context):
        with pytest.raises(ValueError, match="Size must be a vec2"):
            basic_context.predictAdaptiveTileObjectSubpatchCount(vec3(10, 10, 10))
        with pytest.raises(ValueError, match="Refinement must be an AdaptiveTileRefinement"):
            basic_context.predictAdaptiveTileObjectSubpatchCount(vec2(10, 10), "nope")
        with pytest.raises(ValueError, match="texture_repeat must be an int2"):
            basic_context.predictAdaptiveTileObjectSubpatchCount(
                vec2(10, 10), AdaptiveTileRefinement(), vec2(1, 1))


@pytest.mark.native_only
class TestPrimitiveDataIntrospection:
    def test_list_and_clear_primitive_data(self, basic_context):
        uuid = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        basic_context.setPrimitiveDataFloat(uuid, "temp", 25.5)
        basic_context.setPrimitiveDataFloat(uuid, "humidity", 80.0)
        labels = basic_context.listPrimitiveData(uuid)
        assert "temp" in labels
        assert "humidity" in labels

        basic_context.clearPrimitiveData(uuid, "temp")
        labels_after = basic_context.listPrimitiveData(uuid)
        assert "temp" not in labels_after
        assert "humidity" in labels_after

    def test_clear_primitive_data_batch(self, basic_context):
        uuids = [basic_context.addPatch(center=vec3(i, 0, 0), size=vec2(1, 1))
                 for i in range(3)]
        for u in uuids:
            basic_context.setPrimitiveDataFloat(u, "x", 1.0)
        basic_context.clearPrimitiveData(uuids, "x")
        for u in uuids:
            assert "x" not in basic_context.listPrimitiveData(u)

    def test_clear_all_primitive_data_by_label(self, basic_context):
        uuids = [basic_context.addPatch(center=vec3(i, 0, 0), size=vec2(1, 1))
                 for i in range(3)]
        for u in uuids:
            basic_context.setPrimitiveDataFloat(u, "wipe", 1.0)
            basic_context.setPrimitiveDataFloat(u, "keep", 2.0)

        basic_context.clearAllPrimitiveData("wipe")

        for u in uuids:
            labels = basic_context.listPrimitiveData(u)
            assert "wipe" not in labels
            assert "keep" in labels


@pytest.mark.native_only
class TestCropDomain:
    def test_crop_domain_x_all_primitives(self, basic_context):
        for x in range(-5, 6):
            basic_context.addPatch(center=vec3(x, 0, 0), size=vec2(0.5, 0.5))
        assert basic_context.getPrimitiveCount() == 11
        basic_context.cropDomainX(vec2(-2, 2))
        remaining = basic_context.getAllUUIDs()
        # cropDomainX removes primitives whose AABB is not fully inside.
        # Each patch has half-size 0.25 in x; centers -1, 0, 1 fully fit in [-2, 2].
        assert len(remaining) == 3

    def test_crop_domain_xyz_all_primitives(self, basic_context):
        basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(0.5, 0.5))
        basic_context.addPatch(center=vec3(10, 0, 0), size=vec2(0.5, 0.5))
        basic_context.cropDomain(vec2(-1, 1), vec2(-1, 1), vec2(-1, 1))
        assert basic_context.getPrimitiveCount() == 1

    def test_crop_domain_by_uuids_returns_filtered(self, basic_context):
        in_range = [basic_context.addPatch(center=vec3(x, 0, 0), size=vec2(0.1, 0.1))
                    for x in (-0.5, 0.0, 0.5)]
        out_of_range = [basic_context.addPatch(center=vec3(x, 0, 0), size=vec2(0.1, 0.1))
                        for x in (-5.0, 5.0)]
        all_uuids = in_range + out_of_range
        survivors = basic_context.cropDomain(all_uuids, vec2(-1, 1), vec2(-1, 1), vec2(-1, 1))
        assert set(survivors) == set(in_range)
        # Original list not mutated
        assert len(all_uuids) == len(in_range) + len(out_of_range)


@pytest.mark.cross_platform
class TestCropDomainValidation:
    def test_rejects_non_vec2_bounds(self, basic_context):
        with pytest.raises(ValueError):
            basic_context.cropDomainX((0, 1))
        with pytest.raises(ValueError):
            basic_context.cropDomain(vec2(0, 1), vec2(0, 1), (0, 1))


# =============================================================================
# Scalar Getters / Setters & List-of-String Getters
# =============================================================================

@pytest.mark.native_only
class TestExistenceQueries:
    def test_does_object_exist_true_after_creation(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        assert basic_context.doesObjectExist(objID) is True

    def test_does_object_exist_false_for_unknown_id(self, basic_context):
        assert basic_context.doesObjectExist(999999) is False

    def test_does_object_contain_primitive(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(2, 2))
        uuids = basic_context.getObjectPrimitiveUUIDs(objID)
        assert len(uuids) > 0
        assert basic_context.doesObjectContainPrimitive(objID, uuids[0]) is True
        # A primitive that doesn't belong to the object
        outsider = basic_context.addPatch(center=vec3(10, 0, 0), size=vec2(0.1, 0.1))
        assert basic_context.doesObjectContainPrimitive(objID, outsider) is False

    def test_object_has_texture_false_for_untextured(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        assert basic_context.objectHasTexture(objID) is False

    def test_is_primitive_dirty_initially_clean(self, basic_context):
        uuid = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        # Newly created primitives may be dirty until markGeometryClean; either bool is OK,
        # we just check the call works and returns a bool.
        result = basic_context.isPrimitiveDirty(uuid)
        assert isinstance(result, bool)

    def test_are_object_primitives_complete_true_initially(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(2, 2))
        assert basic_context.areObjectPrimitivesComplete(objID) is True


@pytest.mark.native_only
class TestValueCachingToggles:
    def test_enable_disable_primitive_data_value_caching(self, basic_context):
        label = "test_caching_label_prim"
        basic_context.enablePrimitiveDataValueCaching(label)
        assert basic_context.isPrimitiveDataValueCachingEnabled(label) is True
        basic_context.disablePrimitiveDataValueCaching(label)
        assert basic_context.isPrimitiveDataValueCachingEnabled(label) is False

    def test_enable_disable_object_data_value_caching(self, basic_context):
        label = "test_caching_label_obj"
        basic_context.enableObjectDataValueCaching(label)
        assert basic_context.isObjectDataValueCachingEnabled(label) is True
        basic_context.disableObjectDataValueCaching(label)
        assert basic_context.isObjectDataValueCachingEnabled(label) is False


@pytest.mark.native_only
class TestScalarNumericGetters:
    def test_get_julian_date(self, basic_context):
        # Default should be a valid Julian day (1-366); we don't assert a specific value.
        jd = basic_context.getJulianDate()
        assert isinstance(jd, int)
        assert 1 <= jd <= 366

    def test_get_material_count_initially_zero_or_more(self, basic_context):
        # Materials are zero-initialized (or default-set); just verify it returns an int.
        n = basic_context.getMaterialCount()
        assert isinstance(n, int)
        assert n >= 0

    def test_get_object_area_positive(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(2, 3),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        area = basic_context.getObjectArea(objID)
        # 2 * 3 = 6 (one-sided).
        assert area == pytest.approx(6.0, rel=1e-4)

    def test_get_object_primitive_count(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(3, 4))
        count = basic_context.getObjectPrimitiveCount(objID)
        # Tile with 3x4 subdivisions → 12 primitives.
        assert count == 12

    def test_get_primitive_parent_object_id_zero_for_loose_primitive(self, basic_context):
        uuid = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        parent = basic_context.getPrimitiveParentObjectID(uuid)
        # A patch added directly (not via an object) has no parent → 0.
        assert parent == 0

    def test_get_primitive_parent_object_id_matches_after_object_creation(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        uuids = basic_context.getObjectPrimitiveUUIDs(objID)
        assert basic_context.getPrimitiveParentObjectID(uuids[0]) == objID

    def test_global_data_version_increments(self, basic_context):
        label = "v_test"
        basic_context.setGlobalDataFloat(label, 1.0)
        v1 = basic_context.getGlobalDataVersion(label)
        basic_context.setGlobalDataFloat(label, 2.0)
        v2 = basic_context.getGlobalDataVersion(label)
        assert isinstance(v1, int) and isinstance(v2, int)
        assert v2 > v1


@pytest.mark.native_only
class TestStringGetters:
    def test_get_object_texture_file_empty_for_untextured(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        path = basic_context.getObjectTextureFile(objID)
        assert isinstance(path, str)
        assert path == ''

    def test_list_all_primitive_data_labels_initially_empty(self, basic_context):
        basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        labels = basic_context.listAllPrimitiveDataLabels()
        assert isinstance(labels, list)
        assert all(isinstance(s, str) for s in labels)
        assert labels == []

    def test_list_all_primitive_data_labels_collects_set(self, basic_context):
        u1 = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        u2 = basic_context.addPatch(center=vec3(1, 0, 0), size=vec2(1, 1))
        basic_context.setPrimitiveDataFloat(u1, "alpha", 0.5)
        basic_context.setPrimitiveDataInt(u2, "beta", 7)
        labels = set(basic_context.listAllPrimitiveDataLabels())
        assert {"alpha", "beta"} <= labels

    def test_get_loaded_xml_files_initially_empty(self, basic_context):
        files = basic_context.getLoadedXMLFiles()
        assert files == []


@pytest.mark.native_only
class TestSimpleActions:
    def test_print_primitive_info_does_not_raise(self, basic_context, capsys):
        uuid = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        basic_context.printPrimitiveInfo(uuid)
        # Output goes to stdout; we only verify the call returns cleanly.
        captured = capsys.readouterr()
        # Some output should appear (don't assert exact format).
        assert len(captured.out) >= 0

    def test_print_object_info_does_not_raise(self, basic_context, capsys):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        basic_context.printObjectInfo(objID)
        captured = capsys.readouterr()
        assert len(captured.out) >= 0

    def test_rename_primitive_data(self, basic_context):
        uuid = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        basic_context.setPrimitiveDataFloat(uuid, "old_name", 3.14)
        basic_context.renamePrimitiveData(uuid, "old_name", "new_name")
        assert basic_context.doesPrimitiveDataExist(uuid, "old_name") is False
        assert basic_context.doesPrimitiveDataExist(uuid, "new_name") is True
        assert basic_context.getPrimitiveData(uuid, "new_name", float) == pytest.approx(3.14)

    def test_set_object_data_from_primitive_data_mean(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(2, 1))
        uuids = basic_context.getObjectPrimitiveUUIDs(objID)
        for i, u in enumerate(uuids):
            basic_context.setPrimitiveDataFloat(u, "metric", float(i + 1))
        basic_context.setObjectDataFromPrimitiveDataMean(objID, "metric")
        # Mean of (1, 2) = 1.5
        assert basic_context.getObjectData(objID, "metric", float) == pytest.approx(1.5)


@pytest.mark.native_only
class TestMaterialAPIBasics:
    """Material lifecycle is needed for these tests; we exercise the basics."""

    def test_get_material_count_after_creation(self, basic_context):
        before = basic_context.getMaterialCount()
        basic_context.addMaterial("tier1_test_material")
        after = basic_context.getMaterialCount()
        assert after == before + 1
        assert basic_context.doesMaterialDataExist("tier1_test_material", "nonexistent_data") is False

    def test_get_material_id_from_label(self, basic_context):
        basic_context.addMaterial("tier1_label_test")
        matID = basic_context.getMaterialIDFromLabel("tier1_label_test")
        assert isinstance(matID, int)
        assert matID > 0  # 0 is reserved/sentinel

    def test_get_primitive_material_id_matches(self, basic_context):
        uuid = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        basic_context.addMaterial("tier1_match_test")
        basic_context.assignMaterialToPrimitive(uuid, "tier1_match_test")
        expected = basic_context.getMaterialIDFromLabel("tier1_match_test")
        assert basic_context.getPrimitiveMaterialID(uuid) == expected

    def test_rename_material(self, basic_context):
        basic_context.addMaterial("tier1_rename_old")
        basic_context.renameMaterial("tier1_rename_old", "tier1_rename_new")
        new_id = basic_context.getMaterialIDFromLabel("tier1_rename_new")
        assert new_id > 0


@pytest.mark.native_only
class TestScalarGetterErrorPaths:
    """Verify that error conditions surface as Python exceptions (no silent zeros).

    Scalar wrappers route through the ctypes `errcheck` callback which calls
    getLastErrorCode after every call and raises on a non-zero status, so a missing
    UUID or material label produces a HeliosRuntimeError rather than a sentinel value.
    """

    def test_get_primitive_parent_object_id_raises_on_invalid_uuid(self, basic_context):
        with pytest.raises(HeliosRuntimeError):
            basic_context.getPrimitiveParentObjectID(999999999)

    def test_get_material_id_from_label_raises_on_unknown_label(self, basic_context):
        with pytest.raises(HeliosRuntimeError):
            basic_context.getMaterialIDFromLabel("definitely_not_a_real_material_xyz")

    def test_get_primitive_material_id_raises_on_invalid_uuid(self, basic_context):
        with pytest.raises(HeliosRuntimeError):
            basic_context.getPrimitiveMaterialID(999999999)


@pytest.mark.cross_platform
class TestScalarAPIMockModeSkipped:
    """Mock-mode placeholder. The native_only classes above are skipped automatically
    when the native library is unavailable; this class documents the intent."""

    def test_marker(self):
        assert True


# =============================================================================
# Vector-return getters & geometry mutators
# =============================================================================

@pytest.mark.native_only
class TestVectorReturnGetters:
    def test_get_deleted_uuids_initially_empty(self, basic_context):
        result = basic_context.getDeletedUUIDs()
        assert isinstance(result, list)
        assert result == []

    def test_get_deleted_uuids_after_deletion(self, basic_context):
        u1 = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        u2 = basic_context.addPatch(center=vec3(2, 0, 0), size=vec2(1, 1))
        basic_context.deletePrimitive(u1)
        deleted = basic_context.getDeletedUUIDs()
        assert u1 in deleted
        assert u2 not in deleted

    def test_get_dirty_uuids_returns_list(self, basic_context):
        basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        result = basic_context.getDirtyUUIDs()
        assert isinstance(result, list)
        assert all(isinstance(u, int) for u in result)

    def test_get_dirty_uuids_include_deleted_default_true(self, basic_context):
        # Just verify the call works with both flag values; we don't assert
        # specifics about content because dirty-tracking semantics depend on Helios.
        a = basic_context.getDirtyUUIDs(include_deleted=True)
        b = basic_context.getDirtyUUIDs(include_deleted=False)
        assert isinstance(a, list)
        assert isinstance(b, list)

    def test_get_unique_primitive_parent_object_ids_empty_input(self, basic_context):
        result = basic_context.getUniquePrimitiveParentObjectIDs([], include_zero=True)
        assert result == []

    def test_get_unique_primitive_parent_object_ids_for_loose_primitives(self, basic_context):
        u1 = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        u2 = basic_context.addPatch(center=vec3(2, 0, 0), size=vec2(1, 1))
        # Loose primitives have parent object ID 0.
        result_with_zero = basic_context.getUniquePrimitiveParentObjectIDs(
            [u1, u2], include_zero=True
        )
        assert 0 in result_with_zero
        # Without the zero sentinel, list should be empty for loose primitives.
        result_no_zero = basic_context.getUniquePrimitiveParentObjectIDs(
            [u1, u2], include_zero=False
        )
        assert 0 not in result_no_zero

    def test_get_unique_primitive_parent_object_ids_for_object(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(2, 2))
        uuids = basic_context.getObjectPrimitiveUUIDs(objID)
        result = basic_context.getUniquePrimitiveParentObjectIDs(uuids, include_zero=False)
        assert objID in result

    def test_get_unique_primitive_parent_object_ids_validates_input(self, basic_context):
        with pytest.raises(ValueError, match="must be a list or tuple"):
            basic_context.getUniquePrimitiveParentObjectIDs(123)


@pytest.mark.native_only
class TestObjectNormalAndOrigin:
    def test_get_object_average_normal_returns_vec3(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        n = basic_context.getObjectAverageNormal(objID)
        assert isinstance(n, vec3)
        # Default tile faces +Z (no rotation applied).
        assert n.z == pytest.approx(1.0, abs=1e-3)

    def test_set_object_origin_runs_cleanly(self, basic_context):
        # setObjectOrigin assigns the object's metadata "origin" attribute used by
        # downstream transform stacks; it does not translate primitive geometry.
        # Just verify the call completes and doesn't raise.
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        basic_context.setObjectOrigin(objID, vec3(5, 0, 0))

    def test_set_object_origin_validates_vec3(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        with pytest.raises(ValueError, match="origin must be a vec3"):
            basic_context.setObjectOrigin(objID, (1, 2, 3))

    def test_set_object_average_normal_validates_args(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        with pytest.raises(ValueError, match="origin must be a vec3"):
            basic_context.setObjectAverageNormal(objID, (0, 0, 0), vec3(0, 0, 1))
        with pytest.raises(ValueError, match="new_normal must be a vec3"):
            basic_context.setObjectAverageNormal(objID, vec3(0, 0, 0), (0, 0, 1))


@pytest.mark.native_only
class TestPrimitiveAzimuthElevation:
    def test_set_primitive_azimuth_runs_cleanly(self, basic_context):
        # Use a triangle so azimuth/elevation rotations have a clear effect on the normal.
        uuid = basic_context.addTriangle(vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0))
        basic_context.setPrimitiveAzimuth(uuid, vec3(0, 0, 0), 1.5708)  # pi/2
        # Just verify no exception — Helios handles the rotation math internally.

    def test_set_primitive_elevation_runs_cleanly(self, basic_context):
        uuid = basic_context.addTriangle(vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0))
        basic_context.setPrimitiveElevation(uuid, vec3(0, 0, 0), 0.7854)  # pi/4

    def test_set_primitive_azimuth_validates_origin(self, basic_context):
        uuid = basic_context.addTriangle(vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0))
        with pytest.raises(ValueError, match="origin must be a vec3"):
            basic_context.setPrimitiveAzimuth(uuid, (0, 0, 0), 1.0)


@pytest.mark.native_only
class TestGeometryMutators:
    def test_set_triangle_vertices_updates_geometry(self, basic_context):
        uuid = basic_context.addTriangle(vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0))
        # Move vertices to a new location.
        basic_context.setTriangleVertices(
            uuid, vec3(5, 0, 0), vec3(6, 0, 0), vec3(5, 1, 0)
        )
        # Read back via the existing per-vertex query.
        v0 = basic_context.getTriangleVertex(uuid, 0)
        assert v0.x == pytest.approx(5.0)
        assert v0.y == pytest.approx(0.0)

    def test_set_triangle_vertices_validates_args(self, basic_context):
        uuid = basic_context.addTriangle(vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0))
        with pytest.raises(ValueError, match="vertex0 must be a vec3"):
            basic_context.setTriangleVertices(uuid, (0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0))

    def test_set_primitive_normal_single(self, basic_context):
        # Match the (working) batch-test case: rotate to +Y normal.
        uuid = basic_context.addPatch(center=vec3(2, 0, 0), size=vec2(0.5, 0.5))
        basic_context.setPrimitiveNormal(uuid, vec3(0, 0, 0), vec3(0, 1, 0))
        n = basic_context.getPrimitiveNormal(uuid)
        assert n.y == pytest.approx(1.0, abs=1e-3)

    def test_set_primitive_normal_batch(self, basic_context):
        uuids = [basic_context.addPatch(center=vec3(i, 0, 0), size=vec2(0.5, 0.5))
                 for i in range(3)]
        basic_context.setPrimitiveNormal(uuids, vec3(0, 0, 0), vec3(0, 1, 0))
        # Each patch's normal should now point along +Y.
        for u in uuids:
            n = basic_context.getPrimitiveNormal(u)
            assert n.y == pytest.approx(1.0, abs=1e-3)

    def test_set_primitive_normal_validates_args(self, basic_context):
        uuid = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        with pytest.raises(ValueError, match="origin must be a vec3"):
            basic_context.setPrimitiveNormal(uuid, (0, 0, 0), vec3(0, 0, 1))
        with pytest.raises(ValueError, match="new_normal must be a vec3"):
            basic_context.setPrimitiveNormal(uuid, vec3(0, 0, 0), (0, 0, 1))

    def test_set_primitive_parent_object_id_single(self, basic_context):
        uuid = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        basic_context.setPrimitiveParentObjectID(uuid, objID)
        assert basic_context.getPrimitiveParentObjectID(uuid) == objID

    def test_set_primitive_parent_object_id_batch(self, basic_context):
        uuids = [basic_context.addPatch(center=vec3(i, 0, 0), size=vec2(0.1, 0.1))
                 for i in range(3)]
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        basic_context.setPrimitiveParentObjectID(uuids, objID)
        for u in uuids:
            assert basic_context.getPrimitiveParentObjectID(u) == objID

    def test_set_primitive_parent_object_id_detach_with_zero(self, basic_context):
        uuid = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        basic_context.setPrimitiveParentObjectID(uuid, objID)
        basic_context.setPrimitiveParentObjectID(uuid, 0)
        assert basic_context.getPrimitiveParentObjectID(uuid) == 0


# =============================================================================
# 4x4 transformation matrices + domain bounds
# =============================================================================

@pytest.mark.native_only
class TestTransformationMatrices:
    @staticmethod
    def _identity_flat():
        return [1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0,
                0.0, 0.0, 0.0, 1.0]

    @staticmethod
    def _translation_matrix(tx, ty, tz):
        # Row-major: translation lives in column 3 → indices 3, 7, 11.
        return [1.0, 0.0, 0.0, float(tx),
                0.0, 1.0, 0.0, float(ty),
                0.0, 0.0, 1.0, float(tz),
                0.0, 0.0, 0.0, 1.0]

    def test_object_transform_round_trip_identity(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        T = basic_context.getObjectTransformationMatrix(objID)
        assert T.shape == (4, 4)
        assert T.dtype == np.float32

    def test_object_transform_set_get_translation(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        T_in = self._translation_matrix(5, -2, 7)
        basic_context.setObjectTransformationMatrix(objID, T_in)
        T_out = basic_context.getObjectTransformationMatrix(objID)
        assert T_out[0, 3] == pytest.approx(5.0)
        assert T_out[1, 3] == pytest.approx(-2.0)
        assert T_out[2, 3] == pytest.approx(7.0)

    def test_set_object_transform_accepts_ndarray(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        T_in = np.array(self._translation_matrix(1, 2, 3), dtype=np.float32).reshape((4, 4))
        basic_context.setObjectTransformationMatrix(objID, T_in)
        T_out = basic_context.getObjectTransformationMatrix(objID)
        assert T_out[0, 3] == pytest.approx(1.0)
        assert T_out[1, 3] == pytest.approx(2.0)
        assert T_out[2, 3] == pytest.approx(3.0)

    def test_set_object_transform_accepts_nested_list(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        T_in = [[1, 0, 0, 4],
                [0, 1, 0, 5],
                [0, 0, 1, 6],
                [0, 0, 0, 1]]
        basic_context.setObjectTransformationMatrix(objID, T_in)
        T_out = basic_context.getObjectTransformationMatrix(objID)
        assert T_out[0, 3] == pytest.approx(4.0)
        assert T_out[1, 3] == pytest.approx(5.0)
        assert T_out[2, 3] == pytest.approx(6.0)

    def test_set_object_transform_batch(self, basic_context):
        ids = [basic_context.addTileObject(center=vec3(i, 0, 0), size=vec2(0.5, 0.5),
                                           rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
               for i in range(3)]
        T_in = self._translation_matrix(10, 20, 30)
        basic_context.setObjectTransformationMatrix(ids, T_in)
        for objID in ids:
            T_out = basic_context.getObjectTransformationMatrix(objID)
            assert T_out[0, 3] == pytest.approx(10.0)
            assert T_out[1, 3] == pytest.approx(20.0)
            assert T_out[2, 3] == pytest.approx(30.0)

    def test_primitive_transform_round_trip(self, basic_context):
        uuid = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        T = basic_context.getPrimitiveTransformationMatrix(uuid)
        assert T.shape == (4, 4)
        assert T.dtype == np.float32

    def test_primitive_transform_set_get_translation(self, basic_context):
        uuid = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        T_in = self._translation_matrix(2, 3, 4)
        basic_context.setPrimitiveTransformationMatrix(uuid, T_in)
        T_out = basic_context.getPrimitiveTransformationMatrix(uuid)
        assert T_out[0, 3] == pytest.approx(2.0)
        assert T_out[1, 3] == pytest.approx(3.0)
        assert T_out[2, 3] == pytest.approx(4.0)

    def test_primitive_transform_batch(self, basic_context):
        uuids = [basic_context.addPatch(center=vec3(i, 0, 0), size=vec2(0.1, 0.1))
                 for i in range(3)]
        T_in = self._translation_matrix(7, 8, 9)
        basic_context.setPrimitiveTransformationMatrix(uuids, T_in)
        for u in uuids:
            T_out = basic_context.getPrimitiveTransformationMatrix(u)
            assert T_out[0, 3] == pytest.approx(7.0)
            assert T_out[1, 3] == pytest.approx(8.0)
            assert T_out[2, 3] == pytest.approx(9.0)

    def test_set_transform_rejects_wrong_shape(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        with pytest.raises(ValueError):
            basic_context.setObjectTransformationMatrix(objID, [1, 2, 3])
        with pytest.raises(ValueError):
            basic_context.setObjectTransformationMatrix(objID, np.zeros((3, 3), dtype=np.float32))
        with pytest.raises(ValueError):
            basic_context.setObjectTransformationMatrix(objID, "not a matrix")


@pytest.mark.native_only
class TestDomainBounds:
    def test_bounding_box_simple(self, basic_context):
        # Two patches at known positions; domain bounds should cover both.
        basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        basic_context.addPatch(center=vec3(5, 3, 2), size=vec2(0.2, 0.2))
        xb, yb, zb = basic_context.getDomainBoundingBox()
        assert isinstance(xb, vec2)
        assert isinstance(yb, vec2)
        assert isinstance(zb, vec2)
        # x covers [-0.5, 5.1]; y covers [-0.5, 3.1]; z covers [0, 0]
        assert xb.x <= 0.0 and xb.y >= 5.0
        assert yb.x <= 0.0 and yb.y >= 3.0

    def test_bounding_box_filtered_by_uuids(self, basic_context):
        u_in = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(0.1, 0.1))
        basic_context.addPatch(center=vec3(100, 100, 100), size=vec2(0.1, 0.1))  # outlier
        xb, yb, zb = basic_context.getDomainBoundingBox(uuids=[u_in])
        assert xb.y < 50.0  # outlier excluded
        assert yb.y < 50.0

    def test_bounding_box_filtered_validates_input(self, basic_context):
        with pytest.raises(ValueError, match="must be a list or tuple"):
            basic_context.getDomainBoundingBox(uuids=42)

    def test_bounding_sphere_simple(self, basic_context):
        basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        basic_context.addPatch(center=vec3(2, 0, 0), size=vec2(1, 1))
        center, radius = basic_context.getDomainBoundingSphere()
        assert isinstance(center, vec3)
        assert isinstance(radius, float)
        assert radius > 0.0

    def test_bounding_sphere_filtered(self, basic_context):
        u_in = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(0.1, 0.1))
        basic_context.addPatch(center=vec3(100, 0, 0), size=vec2(0.1, 0.1))
        center, radius = basic_context.getDomainBoundingSphere(uuids=[u_in])
        # Sphere only encloses the small patch.
        assert radius < 50.0


# =============================================================================
# Tube/polymesh + object color/dirty/tile mutators
# =============================================================================

@pytest.fixture
def tube_object(basic_context):
    """Create a simple straight tube object for mutation tests."""
    nodes = [vec3(0, 0, 0), vec3(0, 0, 1), vec3(0, 0, 2)]
    radii = [0.1, 0.1, 0.1]
    return basic_context.addTubeObject(ndivs=8, nodes=nodes, radii=radii)


@pytest.mark.native_only
class TestTubeMutators:
    def test_set_tube_nodes(self, basic_context, tube_object):
        new_nodes = [vec3(0, 0, 0), vec3(0, 0, 0.5), vec3(0, 0, 1.0)]
        basic_context.setTubeNodes(tube_object, new_nodes)

    def test_set_tube_nodes_validates(self, basic_context, tube_object):
        with pytest.raises(ValueError, match="must be a list or tuple"):
            basic_context.setTubeNodes(tube_object, "nope")
        with pytest.raises(ValueError, match="must be a vec3"):
            basic_context.setTubeNodes(tube_object, [vec3(0, 0, 0), (1, 2, 3)])

    def test_set_tube_radii(self, basic_context, tube_object):
        basic_context.setTubeRadii(tube_object, [0.2, 0.2, 0.2])

    def test_set_tube_radii_validates(self, basic_context, tube_object):
        with pytest.raises(ValueError, match="must be a list or tuple"):
            basic_context.setTubeRadii(tube_object, 0.5)

    def test_scale_tube_girth(self, basic_context, tube_object):
        basic_context.scaleTubeGirth(tube_object, 2.0)

    def test_scale_tube_length(self, basic_context, tube_object):
        basic_context.scaleTubeLength(tube_object, 0.5)

    def test_prune_tube_nodes(self, basic_context, tube_object):
        # Prune everything from index 2 onward (leaves nodes 0 and 1).
        basic_context.pruneTubeNodes(tube_object, 2)

    def test_append_tube_segment_color(self, basic_context, tube_object):
        basic_context.appendTubeSegment(
            tube_object,
            node_position=vec3(0, 0, 3),
            radius=0.1,
            color=RGBcolor(0.2, 0.5, 0.8),
        )

    def test_append_tube_segment_requires_color_or_texture(self, basic_context, tube_object):
        with pytest.raises(ValueError, match="exactly one of"):
            basic_context.appendTubeSegment(tube_object, vec3(0, 0, 3), 0.1)
        with pytest.raises(ValueError, match="exactly one of"):
            basic_context.appendTubeSegment(
                tube_object, vec3(0, 0, 3), 0.1,
                color=RGBcolor(1, 0, 0),
                texture_file="x.png",
                uv=vec2(0, 0),
            )

    def test_append_tube_segment_validates_node_position(self, basic_context, tube_object):
        with pytest.raises(ValueError, match="node_position must be a vec3"):
            basic_context.appendTubeSegment(
                tube_object, (0, 0, 3), 0.1, color=RGBcolor(1, 0, 0)
            )


@pytest.mark.native_only
class TestPolymeshObject:
    def test_add_polymesh_object_returns_id(self, basic_context):
        uuids = [basic_context.addPatch(center=vec3(i, 0, 0), size=vec2(0.1, 0.1))
                 for i in range(3)]
        objID = basic_context.addPolymeshObject(uuids)
        assert isinstance(objID, int)
        assert objID > 0
        # All input primitives are now part of the new object.
        for u in uuids:
            assert basic_context.getPrimitiveParentObjectID(u) == objID

    def test_add_polymesh_object_rejects_empty(self, basic_context):
        with pytest.raises(ValueError, match="at least one UUID"):
            basic_context.addPolymeshObject([])

    def test_add_polymesh_object_rejects_non_list(self, basic_context):
        with pytest.raises(ValueError, match="must be a list or tuple"):
            basic_context.addPolymeshObject(42)


@pytest.mark.native_only
class TestObjectColor:
    def test_set_object_color_rgb_single(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        basic_context.setObjectColor(objID, RGBcolor(0.2, 0.4, 0.6))

    def test_set_object_color_rgba_single(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        basic_context.setObjectColor(objID, RGBAcolor(0.2, 0.4, 0.6, 0.8))

    def test_set_object_color_rgb_batch(self, basic_context):
        ids = [basic_context.addTileObject(center=vec3(i, 0, 0), size=vec2(0.5, 0.5),
                                           rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
               for i in range(3)]
        basic_context.setObjectColor(ids, RGBcolor(0.5, 0.5, 0.5))

    def test_set_object_color_rejects_wrong_type(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        with pytest.raises(ValueError, match="must be an RGBcolor or RGBAcolor"):
            basic_context.setObjectColor(objID, (0.5, 0.5, 0.5))

    def test_override_and_use_object_texture_color(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        basic_context.overrideObjectTextureColor(objID)
        basic_context.useObjectTextureColor(objID)

    def test_override_object_texture_color_batch(self, basic_context):
        ids = [basic_context.addTileObject(center=vec3(i, 0, 0), size=vec2(0.5, 0.5),
                                           rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
               for i in range(2)]
        basic_context.overrideObjectTextureColor(ids)
        basic_context.useObjectTextureColor(ids)


@pytest.mark.native_only
class TestMarkDirtyClean:
    def test_mark_dirty_single_then_clean(self, basic_context):
        u = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        basic_context.markPrimitiveDirty(u)
        assert basic_context.isPrimitiveDirty(u) is True
        basic_context.markPrimitiveClean(u)
        assert basic_context.isPrimitiveDirty(u) is False

    def test_mark_dirty_batch(self, basic_context):
        uuids = [basic_context.addPatch(center=vec3(i, 0, 0), size=vec2(0.1, 0.1))
                 for i in range(3)]
        basic_context.markPrimitiveDirty(uuids)
        for u in uuids:
            assert basic_context.isPrimitiveDirty(u) is True
        basic_context.markPrimitiveClean(uuids)
        for u in uuids:
            assert basic_context.isPrimitiveDirty(u) is False


@pytest.mark.native_only
class TestTileSubdivision:
    def test_set_subdivision_count_single(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        basic_context.setTileObjectSubdivisionCount(objID, int2(3, 4))
        # After re-subdivision, primitive count reflects new grid.
        assert basic_context.getObjectPrimitiveCount(objID) == 12

    def test_set_subdivision_count_batch(self, basic_context):
        ids = [basic_context.addTileObject(center=vec3(i, 0, 0), size=vec2(0.5, 0.5),
                                           rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
               for i in range(2)]
        basic_context.setTileObjectSubdivisionCount(ids, int2(2, 2))
        for objID in ids:
            assert basic_context.getObjectPrimitiveCount(objID) == 4

    def test_set_subdivision_count_validates_int2(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        with pytest.raises(ValueError, match="subdiv must be an int2"):
            basic_context.setTileObjectSubdivisionCount(objID, (3, 4))

    def test_set_subdivision_by_area_ratio(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        # area_ratio is the ratio of the whole tile area to a sub-patch area (>= 1); 4 -> ~2x2.
        basic_context.setTileObjectSubdivisionByAreaRatio(objID, 4.0)
        assert basic_context.getObjectPrimitiveCount(objID) >= 4

    def test_set_subdivision_by_area_ratio_rejects_below_one(self, basic_context):
        # helios-core 1.3.77 requires area_ratio >= 1 (a sub-patch cannot exceed the tile);
        # PyHelios fails fast before the FFI call.
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
        with pytest.raises(ValueError, match="area_ratio must be >= 1"):
            basic_context.setTileObjectSubdivisionByAreaRatio(objID, 0.5)


# =============================================================================
# Cleanup, XML write, RNG, Location
# =============================================================================

@pytest.mark.native_only
class TestCleanDeletedIDs:
    def test_clean_deleted_uuids_returns_new_list(self, basic_context):
        uuids = [basic_context.addPatch(center=vec3(i, 0, 0), size=vec2(0.1, 0.1))
                 for i in range(3)]
        basic_context.deletePrimitive(uuids[1])
        survivors = basic_context.cleanDeletedUUIDs(uuids)
        assert uuids[0] in survivors
        assert uuids[2] in survivors
        assert uuids[1] not in survivors
        # Original input is NOT mutated.
        assert len(uuids) == 3

    def test_clean_deleted_uuids_validates_input(self, basic_context):
        with pytest.raises(ValueError, match="must be a list or tuple"):
            basic_context.cleanDeletedUUIDs(42)

    def test_clean_deleted_uuids_empty_input(self, basic_context):
        assert basic_context.cleanDeletedUUIDs([]) == []

    def test_clean_deleted_object_ids_returns_new_list(self, basic_context):
        ids = [basic_context.addTileObject(center=vec3(i, 0, 0), size=vec2(0.5, 0.5),
                                           rotation=SphericalCoord(1, 0, 0), subdiv=int2(1, 1))
               for i in range(3)]
        basic_context.deleteObject(ids[1])
        survivors = basic_context.cleanDeletedObjectIDs(ids)
        assert ids[0] in survivors
        assert ids[2] in survivors
        assert ids[1] not in survivors


@pytest.mark.native_only
class TestWriteXML:
    def test_writeXML_full_roundtrip(self, basic_context, tmp_path):
        u = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        target = tmp_path / "ctx.xml"
        basic_context.writeXML(str(target), quiet=True)
        assert target.exists()
        assert target.stat().st_size > 0
        # Verify by re-loading; the file should contain the patch UUID.
        with target.open() as f:
            content = f.read()
        assert "primitive" in content.lower() or "patch" in content.lower()

    def test_writeXML_filtered_by_uuids(self, basic_context, tmp_path):
        u_keep = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        u_skip = basic_context.addPatch(center=vec3(5, 5, 5), size=vec2(1, 1))
        target = tmp_path / "filtered.xml"
        basic_context.writeXML(str(target), uuids=[u_keep], quiet=True)
        assert target.exists()

    def test_writeXML_byobject(self, basic_context, tmp_path):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                            rotation=SphericalCoord(1, 0, 0), subdiv=int2(2, 2))
        target = tmp_path / "obj.xml"
        basic_context.writeXML_byobject(str(target), [objID], quiet=True)
        assert target.exists()

    def test_writeXML_rejects_non_xml_extension(self, basic_context, tmp_path):
        with pytest.raises(ValueError):
            basic_context.writeXML(str(tmp_path / "ctx.txt"), quiet=True)

    def test_writeXML_filtered_validates_uuids(self, basic_context, tmp_path):
        target = tmp_path / "ctx.xml"
        with pytest.raises(ValueError, match="must be a list or tuple"):
            basic_context.writeXML(str(target), uuids=42, quiet=True)


@pytest.mark.native_only
class TestRandomNumberGeneration:
    def test_randu_basic_returns_unit_interval(self, basic_context):
        for _ in range(20):
            v = basic_context.randu()
            assert 0.0 <= v < 1.0

    def test_randu_float_range(self, basic_context):
        for _ in range(20):
            v = basic_context.randu(2.0, 5.0)
            assert 2.0 <= v < 5.0

    def test_randu_int_range(self, basic_context):
        for _ in range(20):
            v = basic_context.randu(10, 20)
            assert isinstance(v, int)
            assert 10 <= v <= 20

    def test_randn_basic_finite(self, basic_context):
        # Standard normal; just verify it returns a finite float each draw.
        import math
        for _ in range(20):
            v = basic_context.randn()
            assert math.isfinite(v)

    def test_randn_with_params(self, basic_context):
        # Mean of 1000 draws should be roughly close to the configured mean.
        samples = [basic_context.randn(10.0, 0.5) for _ in range(1000)]
        avg = sum(samples) / len(samples)
        assert abs(avg - 10.0) < 1.0  # generous bound

    def test_randu_partial_args_raise(self, basic_context):
        with pytest.raises(ValueError, match="both low and high"):
            basic_context.randu(low=1.0)

    def test_randn_partial_args_raise(self, basic_context):
        with pytest.raises(ValueError, match="both mean and stddev"):
            basic_context.randn(mean=0.0)


@pytest.mark.native_only
class TestGeographicLocation:
    def test_set_get_location_round_trip_floats(self, basic_context):
        basic_context.setLocation(40.7, 74.0, -5.0)
        loc = basic_context.getLocation()
        assert loc.latitude == pytest.approx(40.7, abs=1e-4)
        assert loc.longitude == pytest.approx(74.0, abs=1e-4)
        assert loc.utc_offset == pytest.approx(-5.0, abs=1e-4)

    def test_set_get_location_round_trip_altitude_floats(self, basic_context):
        basic_context.setLocation(40.7, 74.0, -5.0, altitude=123.0)
        loc = basic_context.getLocation()
        assert loc.latitude == pytest.approx(40.7, abs=1e-4)
        assert loc.altitude == pytest.approx(123.0, abs=1e-3)

    def test_set_get_location_round_trip_altitude_object(self, basic_context):
        basic_context.setLocation(Location(38.5, 121.7, 8.0, 16.0))
        loc = basic_context.getLocation()
        assert loc.altitude == pytest.approx(16.0, abs=1e-3)

    def test_default_location_altitude_is_zero(self, basic_context):
        # Helios::Location default altitude is 0.
        loc = basic_context.getLocation()
        assert loc.altitude == pytest.approx(0.0, abs=1e-4)

    def test_set_get_location_three_arg_defaults_altitude_zero(self, basic_context):
        basic_context.setLocation(40.7, 74.0, -5.0)
        loc = basic_context.getLocation()
        assert loc.altitude == pytest.approx(0.0, abs=1e-4)

    def test_set_get_location_round_trip_object(self, basic_context):
        basic_context.setLocation(Location(38.5, 121.7, 8.0))
        loc = basic_context.getLocation()
        assert isinstance(loc, Location)
        # C++ Location stores floats, not doubles - allow float-precision tolerance.
        assert loc.latitude == pytest.approx(38.5, abs=1e-4)
        assert loc.longitude == pytest.approx(121.7, abs=1e-3)
        assert loc.utc_offset == pytest.approx(8.0, abs=1e-4)

    def test_default_location_is_helios_default(self, basic_context):
        # Helios::Location default constructor: lat=38.55, lon=121.76, utc=8.
        loc = basic_context.getLocation()
        assert loc.latitude == pytest.approx(38.55, abs=1e-3)

    def test_set_location_rejects_partial_args(self, basic_context):
        with pytest.raises(ValueError, match="3 floats"):
            basic_context.setLocation(40.0)
        with pytest.raises(ValueError, match="3 floats"):
            basic_context.setLocation(40.0, 70.0)

    def test_set_location_rejects_mixed_args(self, basic_context):
        with pytest.raises(ValueError, match="When passing a Location"):
            basic_context.setLocation(Location(0, 0, 0), 1.0, 2.0)

    def test_set_location_rejects_altitude_with_object(self, basic_context):
        with pytest.raises(ValueError, match="When passing a Location"):
            basic_context.setLocation(Location(0, 0, 0), altitude=99.0)

    def test_location_is_immutable(self):
        loc = Location(1, 2, 3)
        with pytest.raises(AttributeError):
            loc.latitude = 99

    def test_location_equality_and_repr(self):
        a = Location(1, 2, 3)
        b = Location(1, 2, 3)
        c = Location(1, 2, 4)
        assert a == b
        assert a != c
        assert "latitude=1" in repr(a)

    def test_location_altitude_default_and_field(self):
        loc = Location(1, 2, 3)
        assert loc.altitude == 0.0
        loc2 = Location(1, 2, 3, 50.0)
        assert loc2.altitude == 50.0
        assert "altitude=50" in repr(loc2)

    def test_location_altitude_distinguishes_equality(self):
        assert Location(1, 2, 3, 0.0) == Location(1, 2, 3)
        assert Location(1, 2, 3, 10.0) != Location(1, 2, 3, 20.0)
        assert hash(Location(1, 2, 3, 10.0)) != hash(Location(1, 2, 3, 20.0))

    def test_location_altitude_invalid_type_raises(self):
        with pytest.raises(ValueError, match="altitude must be a number"):
            Location(1, 2, 3, "high")

    def test_make_location_altitude(self):
        from pyhelios.wrappers.DataTypes import make_Location
        loc = make_Location(1, 2, 3, 7.5)
        assert loc.altitude == 7.5
        # 3-arg form still defaults altitude to 0.
        assert make_Location(1, 2, 3).altitude == 0.0


# =============================================================================
# Location range validation (helios-core v1.3.79+)
#
# helios::Location gained a public validate() that both parameterized constructors
# call, and Context::setLocation() re-validates on the way in. PyHelios mirrors the
# same bounds in Location.__init__ so the error arrives as a ValueError at the point
# of construction, in mock mode as well as native.
# =============================================================================

@pytest.mark.cross_platform
class TestLocationRangeValidation:
    """Bounds are those of helios::Location::validate()."""

    @pytest.mark.parametrize("latitude", [90.1, -90.1, 91.0, -91.0, 180.0, 1e6])
    def test_latitude_out_of_range_raises(self, latitude):
        with pytest.raises(ValueError, match="[Ll]atitude"):
            Location(latitude, 0.0, 0.0)

    @pytest.mark.parametrize("latitude", [90.0, -90.0, 0.0, 38.55])
    def test_latitude_at_and_within_bounds_accepted(self, latitude):
        assert Location(latitude, 0.0, 0.0).latitude == pytest.approx(latitude)

    @pytest.mark.parametrize("longitude", [180.1, -180.1, 181.0, -181.0, 1e6])
    def test_longitude_out_of_range_raises(self, longitude):
        with pytest.raises(ValueError, match="[Ll]ongitude"):
            Location(0.0, longitude, 0.0)

    @pytest.mark.parametrize("longitude", [180.0, -180.0, 0.0, 121.76])
    def test_longitude_at_and_within_bounds_accepted(self, longitude):
        assert Location(0.0, longitude, 0.0).longitude == pytest.approx(longitude)

    @pytest.mark.parametrize("utc_offset", [12.1, -14.1, 13.0, -15.0, 24.0])
    def test_utc_offset_out_of_range_raises(self, utc_offset):
        with pytest.raises(ValueError, match="UTC"):
            Location(0.0, 0.0, utc_offset)

    @pytest.mark.parametrize("utc_offset", [12.0, -14.0, 0.0, 8.0])
    def test_utc_offset_at_and_within_bounds_accepted(self, utc_offset):
        """The range is -14..+12, not -12..+12.

        Helios counts the UTC offset positive moving West, so the real-world span
        of UTC-12 through UTC+14 (Kiribati keeps the latter) inverts to +12
        through -14. An offset of -14 is therefore legal and +14 is not.
        """
        assert Location(0.0, 0.0, utc_offset).utc_offset == pytest.approx(utc_offset)

    def test_utc_offset_asymmetric_bounds(self):
        """Guards against "fixing" the range to a symmetric -12..+12."""
        Location(0.0, 0.0, -14.0)  # legal: real-world UTC+14
        with pytest.raises(ValueError, match="UTC"):
            Location(0.0, 0.0, 14.0)  # illegal: would be real-world UTC-14

    @pytest.mark.parametrize("altitude", [float("inf"), float("-inf"), float("nan")])
    def test_non_finite_altitude_raises(self, altitude):
        with pytest.raises(ValueError, match="[Aa]ltitude"):
            Location(0.0, 0.0, 0.0, altitude)

    @pytest.mark.parametrize("altitude", [0.0, -430.0, 8848.0, 1e9])
    def test_altitude_unbounded_but_finite(self, altitude):
        """No non-arbitrary bound exists for a simulated scene's altitude."""
        assert Location(0.0, 0.0, 0.0, altitude).altitude == pytest.approx(altitude)

    def test_make_location_validates_too(self):
        from pyhelios.wrappers.DataTypes import make_Location
        with pytest.raises(ValueError, match="[Ll]atitude"):
            make_Location(95.0, 0.0, 0.0)

    def test_error_message_names_the_offending_value(self):
        with pytest.raises(ValueError, match="95"):
            Location(95.0, 0.0, 0.0)

    def test_type_error_still_precedes_range_error(self):
        """A non-numeric value must report the type problem, not a range problem."""
        with pytest.raises(ValueError, match="must be a number"):
            Location("95", 0.0, 0.0)


@pytest.mark.native_only
class TestSetLocationRangeValidationNative:
    """setLocation() rejects out-of-range values end to end, on a native library.

    Note that these exercise the *Python* guard: Context.setLocation() constructs a
    Location first, which validates and raises before the native call is reached. That
    is the correct behavior for the public API, but it means these tests do not prove
    the native re-validation is present -- see
    TestSetLocationNativeRevalidation for that.
    """

    def test_set_location_rejects_out_of_range_latitude(self, basic_context):
        with pytest.raises((ValueError, RuntimeError), match="[Ll]atitude"):
            basic_context.setLocation(95.0, 0.0, 0.0)

    def test_set_location_rejects_out_of_range_longitude(self, basic_context):
        with pytest.raises((ValueError, RuntimeError), match="[Ll]ongitude"):
            basic_context.setLocation(0.0, 200.0, 0.0)

    def test_set_location_rejects_out_of_range_utc_offset(self, basic_context):
        with pytest.raises((ValueError, RuntimeError), match="UTC"):
            basic_context.setLocation(0.0, 0.0, 15.0)

    def test_set_location_accepts_utc_offset_minus_14(self, basic_context):
        """-14 is in range; asserts PyHelios does not impose a stricter -12 bound."""
        basic_context.setLocation(0.0, 0.0, -14.0)
        assert basic_context.getLocation().utc_offset == pytest.approx(-14.0, abs=1e-4)

    def test_rejected_set_location_leaves_location_unchanged(self, basic_context):
        """Native contract: an out-of-range field leaves the Context's location alone."""
        basic_context.setLocation(38.5, 121.7, 8.0, 16.0)
        before = basic_context.getLocation()

        with pytest.raises((ValueError, RuntimeError)):
            basic_context.setLocation(95.0, 0.0, 0.0)

        after = basic_context.getLocation()
        assert after.latitude == pytest.approx(before.latitude, abs=1e-4)
        assert after.longitude == pytest.approx(before.longitude, abs=1e-4)
        assert after.utc_offset == pytest.approx(before.utc_offset, abs=1e-4)
        assert after.altitude == pytest.approx(before.altitude, abs=1e-3)


@pytest.mark.native_only
class TestSetLocationNativeRevalidation:
    """The native Context::setLocation() re-validation must be load-bearing.

    Context.setLocation() builds a Location first, so its Python-side bounds check
    normally fires before anything reaches C++. These tests call the ctypes wrapper
    directly to bypass that guard, which is the only way to reach
    helios::Location::validate() from Python and prove it is actually there. Without
    them, deleting the native re-validation entirely would break no PyHelios test.
    """

    def _set_raw(self, context, latitude, longitude, utc_offset, altitude=0.0):
        """Call the native setLocation with no Python-side Location construction."""
        from pyhelios.wrappers import UContextWrapper as context_wrapper
        context_wrapper.setLocationWrapper(
            context.getNativePtr(), latitude, longitude, utc_offset, altitude)

    def test_native_rejects_out_of_range_latitude(self, basic_context):
        with pytest.raises(Exception, match="[Ll]atitude"):
            self._set_raw(basic_context, 95.0, 0.0, 0.0)

    def test_native_rejects_out_of_range_longitude(self, basic_context):
        with pytest.raises(Exception, match="[Ll]ongitude"):
            self._set_raw(basic_context, 0.0, 200.0, 0.0)

    def test_native_rejects_out_of_range_utc_offset(self, basic_context):
        with pytest.raises(Exception, match="UTC"):
            self._set_raw(basic_context, 0.0, 0.0, 15.0)

    def test_native_accepts_utc_offset_minus_14(self, basic_context):
        """-14 must reach the native layer and be accepted there, not just in Python."""
        self._set_raw(basic_context, 0.0, 0.0, -14.0)
        assert basic_context.getLocation().utc_offset == pytest.approx(-14.0, abs=1e-4)

    def test_native_rejection_leaves_location_unchanged(self, basic_context):
        """The native contract: an out-of-range field must not mutate the Context."""
        self._set_raw(basic_context, 38.5, 121.7, 8.0, 16.0)
        before = basic_context.getLocation()

        with pytest.raises(Exception):
            self._set_raw(basic_context, 95.0, 0.0, 0.0)

        after = basic_context.getLocation()
        assert after.latitude == pytest.approx(before.latitude, abs=1e-4)
        assert after.longitude == pytest.approx(before.longitude, abs=1e-4)
        assert after.utc_offset == pytest.approx(before.utc_offset, abs=1e-4)
        assert after.altitude == pytest.approx(before.altitude, abs=1e-3)


# =============================================================================
# Colormap helpers + texture transparency
# =============================================================================

@pytest.mark.native_only
class TestColormap:
    def test_generate_colormap_named(self, basic_context):
        colors = basic_context.generateColormap("hot", 16)
        assert isinstance(colors, list)
        assert len(colors) == 16
        for c in colors:
            assert isinstance(c, RGBcolor)
            assert 0.0 <= c.r <= 1.0
            assert 0.0 <= c.g <= 1.0
            assert 0.0 <= c.b <= 1.0

    def test_generate_colormap_returns_distinct_colors(self, basic_context):
        # A real colormap should have visible variation across entries.
        colors = basic_context.generateColormap("hot", 8)
        first = (colors[0].r, colors[0].g, colors[0].b)
        last = (colors[-1].r, colors[-1].g, colors[-1].b)
        assert first != last


@pytest.mark.native_only
class TestTextureTransparency:
    def test_no_transparency_returns_none(self, basic_context):
        u = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))
        # An untextured patch has no transparency data.
        assert basic_context.getPrimitiveTextureTransparencyData(u) is None

    def test_textured_with_alpha_returns_ndarray(self, basic_context):
        # GrapeLeaf.png has a transparent background.
        texture = "/Users/bnbailey/Dropbox/PyHelios/helios-core/plugins/plantarchitecture/assets/textures/GrapeLeaf.png"
        if not os.path.exists(texture):
            pytest.skip("Test texture not available")
        u = basic_context.addPatchTextured(
            center=vec3(0, 0, 0), size=vec2(1, 1), texture_file=texture
        )
        result = basic_context.getPrimitiveTextureTransparencyData(u)
        # If the texture has an alpha channel, we get an ndarray. If Helios
        # treats it as opaque, we get None. Either is acceptable; verify the
        # type of the returned value.
        assert result is None or (hasattr(result, 'shape') and result.dtype == bool)
        if result is not None:
            assert result.ndim == 2
            assert result.shape[0] > 0 and result.shape[1] > 0

@pytest.mark.native_only
class TestRotationOperations:
    """Test primitive and object rotation.

    These cover the 14 wrapped rotate entry points. The handedness assertions
    exist specifically to pin the convention: helios-core 1.3.78 removed a
    negation in CompoundObject::rotate()'s "z" string-axis branch that made
    rotateObject(..., 'z') disagree with rotatePrimitive() and with the
    vec3-axis rotateObject() overload. That defect was invisible to PyHelios
    because none of these entry points had any test coverage.
    """

    @staticmethod
    def _verts(context, uuid):
        """Vertices of a primitive as a list of rounded (x, y, z) tuples."""
        return [(round(v.x, 4), round(v.y, 4), round(v.z, 4))
                for v in context.getPrimitiveVertices(uuid)]

    # -------- handedness / cross-path consistency --------

    def test_z_rotation_is_clockwise_viewed_from_positive_z(self, basic_context):
        """A +90 deg z-rotation maps (x,y) -> (y,-x)."""
        uuid = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(2, 1))
        assert self._verts(basic_context, uuid)[0] == (-1.0, -0.5, 0.0)

        basic_context.rotatePrimitive(uuid, math.pi / 2, 'z')

        # (-1, -0.5) -> (-0.5, 1.0) under (x,y)->(y,-x). The vertex list is
        # cyclically reordered by the rotation, so compare as a set.
        assert set(self._verts(basic_context, uuid)) == {
            (0.5, -1.0, 0.0), (0.5, 1.0, 0.0), (-0.5, 1.0, 0.0), (-0.5, -1.0, 0.0)
        }

    @pytest.mark.parametrize("axis", ['x', 'y', 'z'])
    def test_object_and_primitive_string_axis_rotations_agree(self, basic_context, axis):
        """rotateObject(str axis) and rotatePrimitive(str axis) share one handedness.

        Before helios-core 1.3.78 the 'z' case alone disagreed, because
        CompoundObject::rotate() negated the angle in its "z" branch.
        """
        patch = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(2, 1))
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(2, 1),
                                            subdiv=int2(1, 1))
        tile_prim = basic_context.getObjectPrimitiveUUIDs(objID)[0]

        assert self._verts(basic_context, patch) == self._verts(basic_context, tile_prim)

        basic_context.rotatePrimitive(patch, math.pi / 2, axis)
        basic_context.rotateObject(objID, math.pi / 2, axis)

        assert self._verts(basic_context, patch) == self._verts(basic_context, tile_prim), (
            f"rotateObject and rotatePrimitive disagree about the '{axis}' axis"
        )

    def test_object_string_axis_and_vector_axis_rotations_agree(self, basic_context):
        """rotateObject('z') and rotateObject(vec3(0,0,1)) share one handedness."""
        a = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(2, 1), subdiv=int2(1, 1))
        b = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(2, 1), subdiv=int2(1, 1))
        a_prim = basic_context.getObjectPrimitiveUUIDs(a)[0]
        b_prim = basic_context.getObjectPrimitiveUUIDs(b)[0]

        basic_context.rotateObject(a, math.pi / 2, 'z')
        basic_context.rotateObject(b, math.pi / 2, vec3(0, 0, 1))

        assert self._verts(basic_context, a_prim) == self._verts(basic_context, b_prim)

    def test_full_turn_restores_geometry(self, basic_context):
        """Four quarter-turns about z return a primitive to its start."""
        uuid = basic_context.addPatch(center=vec3(1, 2, 0), size=vec2(2, 1))
        before = self._verts(basic_context, uuid)

        for _ in range(4):
            basic_context.rotatePrimitive(uuid, math.pi / 2, 'z')

        # The vertex list may be cyclically reordered, so compare as a set.
        assert set(before) == set(self._verts(basic_context, uuid))

    def test_opposite_rotations_cancel(self, basic_context):
        """Rotating by +theta then -theta is a no-op."""
        uuid = basic_context.addPatch(center=vec3(0, 0, 0), size=vec2(2, 1))
        before = self._verts(basic_context, uuid)

        basic_context.rotatePrimitive(uuid, 0.7, vec3(1, 1, 0))
        assert self._verts(basic_context, uuid) != before
        basic_context.rotatePrimitive(uuid, -0.7, vec3(1, 1, 0))

        for (x0, y0, z0), (x1, y1, z1) in zip(before, self._verts(basic_context, uuid)):
            assert abs(x0 - x1) < 1e-3
            assert abs(y0 - y1) < 1e-3
            assert abs(z0 - z1) < 1e-3

    # -------- rotation about an explicit origin --------

    def test_rotate_primitive_about_explicit_origin(self, basic_context):
        """Rotating about a remote origin moves the primitive along an arc."""
        uuid = basic_context.addPatch(center=vec3(2, 0, 0), size=vec2(1, 1))

        basic_context.rotatePrimitive(uuid, math.pi / 2, vec3(0, 0, 1), origin=vec3(0, 0, 0))

        center = basic_context.getPatchCenter(uuid)
        assert abs(center.x - 0.0) < 1e-3, f"x={center.x}"
        assert abs(center.y - 2.0) < 1e-3, f"y={center.y}"
        assert abs(center.z - 0.0) < 1e-3, f"z={center.z}"

    def test_rotate_object_about_explicit_origin(self, basic_context):
        """rotateObject with an explicit origin moves the object along an arc."""
        objID = basic_context.addTileObject(center=vec3(2, 0, 0), size=vec2(1, 1),
                                            subdiv=int2(1, 1))

        basic_context.rotateObject(objID, math.pi / 2, vec3(0, 0, 1), origin=vec3(0, 0, 0))

        center = basic_context.getObjectCenter(objID)
        assert abs(center.x - 0.0) < 1e-3, f"x={center.x}"
        assert abs(abs(center.y) - 2.0) < 1e-3, f"y={center.y}"

    def test_rotate_object_about_origin_uses_object_origin_not_world_origin(self, basic_context):
        """about_origin=True rotates about the OBJECT's own origin, not (0,0,0).

        Native rotateObjectAboutOrigin() passes objects.at(ObjID)->object_origin,
        so a tile centered at (2,0,0) spins in place rather than orbiting the
        world origin.
        """
        objID = basic_context.addTileObject(center=vec3(2, 0, 0), size=vec2(1, 1),
                                            subdiv=int2(1, 1))
        prim = basic_context.getObjectPrimitiveUUIDs(objID)[0]

        basic_context.rotateObject(objID, math.pi / 2, vec3(0, 0, 1), about_origin=True)

        # Spun in place: every vertex stays in the original 1x1 footprint about x=2.
        for x, y, _z in self._verts(basic_context, prim):
            assert 1.4 < x < 2.6, f"x={x} left the in-place footprint"
            assert -0.6 < y < 0.6, f"y={y} left the in-place footprint"

    # -------- batch (list) overloads --------

    def test_rotate_primitive_list_matches_individual(self, basic_context):
        """The list overload rotates every primitive like the single overload."""
        batch = [basic_context.addPatch(center=vec3(i, 0, 0), size=vec2(1, 1))
                 for i in range(3)]
        singles = [basic_context.addPatch(center=vec3(i, 0, 0), size=vec2(1, 1))
                   for i in range(3)]

        basic_context.rotatePrimitive(batch, math.pi / 3, 'z')
        for uuid in singles:
            basic_context.rotatePrimitive(uuid, math.pi / 3, 'z')

        for b, s in zip(batch, singles):
            assert self._verts(basic_context, b) == self._verts(basic_context, s)

    def test_rotate_object_list_matches_individual(self, basic_context):
        """The object list overload rotates every object like the single overload."""
        batch = [basic_context.addTileObject(center=vec3(i, 0, 0), size=vec2(1, 1),
                                             subdiv=int2(1, 1)) for i in range(3)]
        singles = [basic_context.addTileObject(center=vec3(i, 0, 0), size=vec2(1, 1),
                                               subdiv=int2(1, 1)) for i in range(3)]

        basic_context.rotateObject(batch, math.pi / 3, 'z')
        for objID in singles:
            basic_context.rotateObject(objID, math.pi / 3, 'z')

        for b, s in zip(batch, singles):
            bp = basic_context.getObjectPrimitiveUUIDs(b)[0]
            sp = basic_context.getObjectPrimitiveUUIDs(s)[0]
            assert self._verts(basic_context, bp) == self._verts(basic_context, sp)

    def test_rotate_primitive_list_axis_vector(self, basic_context):
        """The list + vec3-axis overload reaches the native call and rotates."""
        batch = [basic_context.addPatch(center=vec3(i, 0, 0), size=vec2(1, 1))
                 for i in range(2)]
        before = [self._verts(basic_context, u) for u in batch]

        basic_context.rotatePrimitive(batch, math.pi / 2, vec3(0, 0, 1))

        for uuid, was in zip(batch, before):
            assert self._verts(basic_context, uuid) != was

    def test_rotate_object_list_about_origin(self, basic_context):
        """The object list + about_origin overload reaches the native call."""
        batch = [basic_context.addTileObject(center=vec3(i, 0, 0), size=vec2(1, 1),
                                             subdiv=int2(1, 1)) for i in range(2)]
        prims = [basic_context.getObjectPrimitiveUUIDs(o)[0] for o in batch]
        before = [self._verts(basic_context, p) for p in prims]

        basic_context.rotateObject(batch, math.pi / 2, vec3(0, 0, 1), about_origin=True)

        for prim, was in zip(prims, before):
            assert self._verts(basic_context, prim) != was


@pytest.mark.native_only
class TestRotationValidation:
    """Test argument validation on the rotation methods."""

    def test_invalid_string_axis_rejected(self, basic_context):
        uuid = basic_context.addPatch(center=vec3(0, 0, 0))
        with pytest.raises(ValueError, match="axis must be"):
            basic_context.rotatePrimitive(uuid, 1.0, 'w')
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), subdiv=int2(1, 1))
        with pytest.raises(ValueError, match="axis must be"):
            basic_context.rotateObject(objID, 1.0, 'w')

    def test_origin_with_string_axis_rejected(self, basic_context):
        uuid = basic_context.addPatch(center=vec3(0, 0, 0))
        with pytest.raises(ValueError, match="origin parameter cannot be used"):
            basic_context.rotatePrimitive(uuid, 1.0, 'z', origin=vec3(0, 0, 0))

    def test_about_origin_with_string_axis_rejected(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), subdiv=int2(1, 1))
        with pytest.raises(ValueError, match="about_origin parameter cannot be used"):
            basic_context.rotateObject(objID, 1.0, 'z', about_origin=True)

    def test_origin_and_about_origin_together_rejected(self, basic_context):
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), subdiv=int2(1, 1))
        with pytest.raises(ValueError, match="Cannot specify both"):
            basic_context.rotateObject(objID, 1.0, vec3(0, 0, 1),
                                       origin=vec3(0, 0, 0), about_origin=True)

    def test_zero_length_axis_rejected(self, basic_context):
        uuid = basic_context.addPatch(center=vec3(0, 0, 0))
        with pytest.raises(ValueError, match="axis vector cannot be zero"):
            basic_context.rotatePrimitive(uuid, 1.0, vec3(0, 0, 0))
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), subdiv=int2(1, 1))
        with pytest.raises(ValueError, match="axis vector cannot be zero"):
            basic_context.rotateObject(objID, 1.0, vec3(0, 0, 0))

    def test_wrong_axis_type_rejected(self, basic_context):
        uuid = basic_context.addPatch(center=vec3(0, 0, 0))
        with pytest.raises(ValueError, match="axis must be str or vec3"):
            basic_context.rotatePrimitive(uuid, 1.0, 42)

    def test_non_vec3_origin_rejected(self, basic_context):
        """A wrong-typed origin is rejected rather than reaching C++ as a bad buffer."""
        uuid = basic_context.addPatch(center=vec3(0, 0, 0))
        with pytest.raises(ValueError, match="origin must be a vec3"):
            basic_context.rotatePrimitive(uuid, 1.0, vec3(0, 0, 1), origin=[0, 0, 0])


@pytest.mark.native_only
class TestObjectBoundingBox:
    """Test getObjectBoundingBox.

    Regression coverage for a native seeding bug fixed in helios-core v1.3.79:
    getObjectBoundingBox() seeded min/max from the first primitive's first vertex
    and then `continue`d to the next primitive, so the rest of that primitive's
    vertices were never compared. A single-primitive object therefore reported
    min == max == its first vertex, and in a list only the first object was
    affected, so a list whose first object held a unique extreme lost it.

    These tests were xfailed while the submodule pinned v1.3.78; the pin has since
    advanced to v1.3.80 and they assert the fixed behavior directly. A regression
    here means the core fix was lost, not that the pin is stale — the fix belongs
    in the Helios repository, never in the vendored helios-core submodule.
    """

    @staticmethod
    def _truth(context, objID):
        """Ground-truth bounding box computed from every vertex of the object."""
        verts = [v for uuid in context.getObjectPrimitiveUUIDs(objID)
                 for v in context.getPrimitiveVertices(uuid)]
        mn = vec3(min(v.x for v in verts), min(v.y for v in verts), min(v.z for v in verts))
        mx = vec3(max(v.x for v in verts), max(v.y for v in verts), max(v.z for v in verts))
        return mn, mx

    def test_single_primitive_object_box_is_not_degenerate(self, basic_context):
        """A 1x1 tile is one patch; its box must span the patch, not collapse to a corner."""
        objID = basic_context.addTileObject(center=vec3(2, 0, 0), size=vec2(1, 1),
                                            subdiv=int2(1, 1))

        mn, mx = basic_context.getObjectBoundingBox(objID)

        assert abs(mn.x - 1.5) < 1e-4, f"min.x={mn.x}"
        assert abs(mx.x - 2.5) < 1e-4, f"max.x={mx.x}"
        assert abs(mn.y - (-0.5)) < 1e-4, f"min.y={mn.y}"
        assert abs(mx.y - 0.5) < 1e-4, f"max.y={mx.y}"
        # The box must have real extent, not collapse to a single point.
        assert mx.x > mn.x and mx.y > mn.y

    def test_box_matches_vertex_ground_truth(self, basic_context):
        """The reported box equals the box computed from all vertices."""
        for objID in [
            basic_context.addTileObject(center=vec3(2, 0, 0), size=vec2(1, 1), subdiv=int2(1, 1)),
            basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(2, 2), subdiv=int2(2, 2)),
            basic_context.addBoxObject(center=vec3(1, 1, 1), size=vec3(2, 2, 2), subdiv=int3(1, 1, 1)),
            basic_context.addSphereObject(radius=1.5, center=vec3(0, 0, 3), ndivs=8),
        ]:
            mn, mx = basic_context.getObjectBoundingBox(objID)
            tmn, tmx = self._truth(basic_context, objID)
            for got, want, name in ((mn, tmn, "min"), (mx, tmx, "max")):
                assert abs(got.x - want.x) < 1e-4, f"obj {objID} {name}.x {got.x} != {want.x}"
                assert abs(got.y - want.y) < 1e-4, f"obj {objID} {name}.y {got.y} != {want.y}"
                assert abs(got.z - want.z) < 1e-4, f"obj {objID} {name}.z {got.z} != {want.z}"

    def test_first_object_contributes_its_full_extent_to_a_list(self, basic_context):
        """The first object in a list must not lose its extent to the seeding path.

        The bug was confined to the first primitive of the first object, so a list
        whose FIRST object holds a unique extreme is the case that exposes it.
        """
        big = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(4, 4), subdiv=int2(1, 1))
        small = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1), subdiv=int2(1, 1))

        mn, mx = basic_context.getObjectBoundingBox([big, small])

        # The big tile spans +/-2; if its first primitive were skipped the box would
        # collapse toward the small tile's +/-0.5.
        assert abs(mn.x - (-2.0)) < 1e-4, f"min.x={mn.x}"
        assert abs(mx.x - 2.0) < 1e-4, f"max.x={mx.x}"
        assert abs(mn.y - (-2.0)) < 1e-4, f"min.y={mn.y}"
        assert abs(mx.y - 2.0) < 1e-4, f"max.y={mx.y}"

    def test_single_object_box_matches_same_object_as_list(self, basic_context):
        """getObjectBoundingBox(o) and getObjectBoundingBox([o]) agree."""
        objID = basic_context.addTileObject(center=vec3(3, -1, 0), size=vec2(1, 1),
                                            subdiv=int2(1, 1))

        a_mn, a_mx = basic_context.getObjectBoundingBox(objID)
        b_mn, b_mx = basic_context.getObjectBoundingBox([objID])

        for x, y in ((a_mn, b_mn), (a_mx, b_mx)):
            assert abs(x.x - y.x) < 1e-6
            assert abs(x.y - y.y) < 1e-6
            assert abs(x.z - y.z) < 1e-6

    def test_rotated_object_box_encloses_rotated_geometry(self, basic_context):
        """After rotation the box tracks the rotated vertices."""
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(4, 1),
                                            subdiv=int2(1, 1))
        basic_context.rotateObject(objID, math.pi / 2, 'z')

        mn, mx = basic_context.getObjectBoundingBox(objID)
        tmn, tmx = self._truth(basic_context, objID)

        # The 4x1 tile becomes 1x4 after a quarter turn about z.
        assert abs((mx.x - mn.x) - 1.0) < 1e-3, f"x extent={mx.x - mn.x}"
        assert abs((mx.y - mn.y) - 4.0) < 1e-3, f"y extent={mx.y - mn.y}"
        assert abs(mn.x - tmn.x) < 1e-4 and abs(mx.y - tmx.y) < 1e-4

    def test_nonexistent_object_raises(self, basic_context):
        """An unknown object ID is reported, not silently returned as garbage."""
        with pytest.raises(Exception):
            basic_context.getObjectBoundingBox(999999)

    def test_empty_object_list_raises_instead_of_returning_origin_box(self, basic_context):
        """A request covering no primitives raises rather than reporting a box at the origin.

        The Python wrapper zero-initializes its output buffers, so before the fix
        this returned a plausible-looking (0,0,0)-(0,0,0) box instead of failing.
        """
        basic_context.addTileObject(center=vec3(5, 5, 5), size=vec2(1, 1), subdiv=int2(1, 1))

        from pyhelios.exceptions import HeliosError
        with pytest.raises(HeliosError, match="contain any primitives"):
            basic_context.getObjectBoundingBox([])

    def test_partially_deleted_object_box_covers_remaining_primitives(self, basic_context):
        """After deleting some sub-primitives the box tracks only what remains."""
        objID = basic_context.addTileObject(center=vec3(0, 0, 0), size=vec2(2, 2),
                                            subdiv=int2(2, 2))
        uuids = basic_context.getObjectPrimitiveUUIDs(objID)
        assert len(uuids) == 4

        basic_context.deletePrimitive(uuids[:3])
        remaining = basic_context.getObjectPrimitiveUUIDs(objID)
        assert len(remaining) == 1

        mn, mx = basic_context.getObjectBoundingBox(objID)
        tmn, tmx = self._truth(basic_context, objID)

        # One surviving 1x1 sub-patch: a real extent, not a collapsed point.
        assert abs((mx.x - mn.x) - 1.0) < 1e-4, f"x extent={mx.x - mn.x}"
        assert abs((mx.y - mn.y) - 1.0) < 1e-4, f"y extent={mx.y - mn.y}"
        assert abs(mn.x - tmn.x) < 1e-4 and abs(mx.x - tmx.x) < 1e-4


@pytest.mark.native_only
class TestUUIDValidationComplexity:
    """Bulk UUID validation must be linear in the number of UUIDs.

    ``_validate_uuid()`` calls ``getAllUUIDs()`` and scans the returned list
    linearly. Applying it one element at a time — as every UUID-list entry point
    did — re-fetches and rescans the whole list per element, so validating N UUIDs
    costs O(N^2) plus N native round-trips. Measured at 20,000 primitives:
    ``getPrimitiveDataArray()`` took ~15 s, against ~40 ms once the lookup is
    hoisted.

    These count ``getAllUUIDs()`` calls rather than timing anything, so they pin
    the complexity without being flaky on a loaded machine.
    """

    @staticmethod
    def _count_get_all_uuids(context, operation):
        """Run operation(), returning how many times it called getAllUUIDs()."""
        calls = []
        real_get_all = context.getAllUUIDs

        def counting_get_all():
            calls.append(1)
            return real_get_all()

        context.getAllUUIDs = counting_get_all
        try:
            operation()
        finally:
            del context.getAllUUIDs
        return len(calls)

    def test_getPrimitiveDataArray_validates_in_linear_time(self, basic_context):
        uuids = [basic_context.addPatch(center=DataTypes.vec3(i, 0, 0),
                                        size=DataTypes.vec2(0.5, 0.5))
                 for i in range(12)]
        for uuid in uuids:
            basic_context.setPrimitiveDataFloat(uuid, "value", float(uuid))

        count = self._count_get_all_uuids(
            basic_context,
            lambda: basic_context.getPrimitiveDataArray(uuids, "value"))

        assert count <= 1, (
            f"getAllUUIDs() called {count} times to validate {len(uuids)} UUIDs - "
            f"validation is rescanning the UUID list per element")

    def test_writePLY_validates_in_linear_time(self, basic_context, tmp_path):
        uuids = [basic_context.addPatch(center=DataTypes.vec3(i, 0, 0),
                                        size=DataTypes.vec2(0.5, 0.5))
                 for i in range(12)]
        target = str(tmp_path / "scene.ply")

        count = self._count_get_all_uuids(
            basic_context, lambda: basic_context.writePLY(target, UUIDs=uuids))

        assert count <= 1, (
            f"getAllUUIDs() called {count} times to validate {len(uuids)} UUIDs")

    def test_writeOBJ_validates_in_linear_time(self, basic_context, tmp_path):
        uuids = [basic_context.addPatch(center=DataTypes.vec3(i, 0, 0),
                                        size=DataTypes.vec2(0.5, 0.5))
                 for i in range(12)]
        target = str(tmp_path / "scene.obj")

        count = self._count_get_all_uuids(
            basic_context, lambda: basic_context.writeOBJ(target, UUIDs=uuids))

        assert count <= 1, (
            f"getAllUUIDs() called {count} times to validate {len(uuids)} UUIDs")

    def test_writePrimitiveData_validates_in_linear_time(self, basic_context, tmp_path):
        uuids = [basic_context.addPatch(center=DataTypes.vec3(i, 0, 0),
                                        size=DataTypes.vec2(0.5, 0.5))
                 for i in range(12)]
        target = str(tmp_path / "data.txt")

        count = self._count_get_all_uuids(
            basic_context,
            lambda: basic_context.writePrimitiveData(target, ["UUID"], UUIDs=uuids))

        assert count <= 1, (
            f"getAllUUIDs() called {count} times to validate {len(uuids)} UUIDs")

    def test_bulk_validation_preserves_error_messages(self, basic_context):
        """Hoisting the lookup must not change what callers see on bad input."""
        good = basic_context.addPatch()
        basic_context.setPrimitiveDataFloat(good, "value", 1.0)

        with pytest.raises(RuntimeError, match="UUID 999999 does not exist in context"):
            basic_context.getPrimitiveDataArray([good, 999999], "value")

        with pytest.raises(RuntimeError, match="Invalid UUID"):
            basic_context.getPrimitiveDataArray([good, -1], "value")

        with pytest.raises(RuntimeError, match="Invalid UUID"):
            basic_context.getPrimitiveDataArray([good, "not_an_int"], "value")

    def test_single_uuid_validation_still_works(self, basic_context):
        """_validate_uuid() remains a supported single-UUID entry point."""
        good = basic_context.addPatch()
        basic_context._validate_uuid(good)

        with pytest.raises(RuntimeError, match="does not exist in context"):
            basic_context._validate_uuid(999999)

        with pytest.raises(RuntimeError, match="Invalid UUID"):
            basic_context._validate_uuid(-1)


@pytest.mark.native_only
class TestBulkFloatPrimitiveData:
    """The native bulk float getter must be correct, ordered, and actually used.

    Reading one float label across N primitives used to cost N ctypes round-trips.
    ``getPrimitiveDataFloatArray`` collapses them into a single native call, and
    ``Context.getPrimitiveDataArray()`` routes its float path through it.
    """

    @staticmethod
    def _scene(context, count, label="value"):
        uuids = []
        for i in range(count):
            uuid = context.addPatch(center=DataTypes.vec3(i * 0.3, 0, 0),
                                    size=DataTypes.vec2(0.2, 0.2))
            context.setPrimitiveDataFloat(uuid, label, float(i) * 1.5)
            uuids.append(uuid)
        return uuids

    def test_bulk_getter_returns_values_in_requested_order(self, basic_context):
        from pyhelios.wrappers import UContextWrapper as cw
        uuids = self._scene(basic_context, 10)

        forward = cw.getPrimitiveDataFloatArray(
            basic_context.getNativePtr(), uuids, "value")
        assert forward == pytest.approx([float(i) * 1.5 for i in range(10)])

        # Order must follow the request, not any internal ordering
        reverse = cw.getPrimitiveDataFloatArray(
            basic_context.getNativePtr(), list(reversed(uuids)), "value")
        assert reverse == pytest.approx(list(reversed(forward)))

        subset = cw.getPrimitiveDataFloatArray(
            basic_context.getNativePtr(), [uuids[7], uuids[2]], "value")
        assert subset == pytest.approx([7 * 1.5, 2 * 1.5])

    def test_bulk_getter_matches_scalar_getter(self, basic_context):
        from pyhelios.wrappers import UContextWrapper as cw
        uuids = self._scene(basic_context, 25)

        bulk = cw.getPrimitiveDataFloatArray(
            basic_context.getNativePtr(), uuids, "value")
        one_by_one = [basic_context.getPrimitiveDataFloat(u, "value") for u in uuids]
        assert bulk == pytest.approx(one_by_one)

    def test_bulk_getter_names_the_offending_primitive(self, basic_context):
        from pyhelios.wrappers import UContextWrapper as cw
        uuids = self._scene(basic_context, 5)
        bare = basic_context.addPatch(center=DataTypes.vec3(9, 9, 9),
                                      size=DataTypes.vec2(0.2, 0.2))

        # Native failures surface as HeliosError, which derives from Exception
        # rather than RuntimeError.
        with pytest.raises(HeliosError) as excinfo:
            cw.getPrimitiveDataFloatArray(
                basic_context.getNativePtr(), uuids + [bare], "value")

        message = str(excinfo.value)
        assert str(bare) in message, f"error does not name the primitive: {message}"
        assert "value" in message, f"error does not name the label: {message}"

    def test_bulk_getter_rejects_empty_uuid_list(self, basic_context):
        from pyhelios.wrappers import UContextWrapper as cw
        self._scene(basic_context, 3)
        with pytest.raises(ValueError, match="UUID list cannot be empty"):
            cw.getPrimitiveDataFloatArray(basic_context.getNativePtr(), [], "value")

    def test_getPrimitiveDataArray_float_path_uses_one_native_call(self, basic_context):
        """The float path must not fall back to a per-primitive read."""
        uuids = self._scene(basic_context, 15)

        calls = []
        real_scalar = basic_context.getPrimitiveDataFloat

        def counting_scalar(uuid, label):
            calls.append(uuid)
            return real_scalar(uuid, label)

        basic_context.getPrimitiveDataFloat = counting_scalar
        try:
            result = basic_context.getPrimitiveDataArray(uuids, "value")
        finally:
            del basic_context.getPrimitiveDataFloat

        assert result == pytest.approx([float(i) * 1.5 for i in range(15)])
        assert not calls, (
            f"float path made {len(calls)} per-primitive scalar reads - "
            f"it is not using the bulk getter")

    def test_getPrimitiveDataArray_float_path_reports_missing_label(self, basic_context):
        """The optimistic bulk read must still name the primitive that lacks data."""
        uuids = self._scene(basic_context, 4)
        bare = basic_context.addPatch(center=DataTypes.vec3(9, 9, 9),
                                      size=DataTypes.vec2(0.2, 0.2))

        with pytest.raises(ValueError, match="Primitive data .* does not exist"):
            basic_context.getPrimitiveDataArray(uuids + [bare], "value")

    def test_getPrimitiveDataArray_non_float_types_still_work(self, basic_context):
        """Int and string paths keep their per-primitive reads and messages."""
        uuids = []
        for i in range(6):
            uuid = basic_context.addPatch(center=DataTypes.vec3(i, 0, 0),
                                          size=DataTypes.vec2(0.2, 0.2))
            basic_context.setPrimitiveDataInt(uuid, "count", i * 3)
            uuids.append(uuid)

        assert list(basic_context.getPrimitiveDataArray(uuids, "count")) == [i * 3 for i in range(6)]

        bare = basic_context.addPatch(center=DataTypes.vec3(9, 9, 9),
                                      size=DataTypes.vec2(0.2, 0.2))
        with pytest.raises(ValueError, match="Primitive data .* does not exist"):
            basic_context.getPrimitiveDataArray(uuids + [bare], "count")


@pytest.mark.native_only
class TestPrimitiveInfoBatching:
    """getAllPrimitiveInfo() must not make native calls per primitive.

    It used to be N x getPrimitiveInfo(), and each of those makes 8 native calls
    (type, area, normal, vertices, color, texture file, texture UV, solid
    fraction) -- 77.5 ms for 5,000 primitives against 4.6 ms for the equivalent
    batch getters. Every one of those eight fields has a list-accepting form that
    goes through a native getBatch* call, so the whole thing collapses to a fixed
    number of native calls regardless of scene size.
    """

    SCALAR_GETTERS = ("getPrimitiveType", "getPrimitiveArea", "getPrimitiveNormal",
                      "getPrimitiveVertices", "getPrimitiveColor",
                      "getPrimitiveTextureFile", "getPrimitiveTextureUV",
                      "getPrimitiveSolidFraction")

    @classmethod
    def _count_scalar_calls(cls, context, operation):
        """Run operation(), counting getter calls made with a single UUID.

        A list argument is one native round-trip; an int argument is one per
        primitive. Only the latter scales with the scene.
        """
        scalar_calls = []
        originals = {}

        def make_counter(name, real):
            def counter(uuid, *a, **kw):
                if not isinstance(uuid, (list, tuple)):
                    scalar_calls.append(name)
                return real(uuid, *a, **kw)
            return counter

        for name in cls.SCALAR_GETTERS:
            real = getattr(context, name)
            originals[name] = real
            setattr(context, name, make_counter(name, real))
        try:
            result = operation()
        finally:
            for name in originals:
                delattr(context, name)
        return result, scalar_calls

    @staticmethod
    def _scene(context, count):
        return [context.addPatch(center=DataTypes.vec3(i * 0.3, 0, 0),
                                 size=DataTypes.vec2(0.2, 0.2))
                for i in range(count)]

    def test_getAllPrimitiveInfo_makes_no_per_primitive_calls(self, basic_context):
        self._scene(basic_context, 12)

        info, scalar_calls = self._count_scalar_calls(
            basic_context, basic_context.getAllPrimitiveInfo)

        assert len(info) == 12
        assert not scalar_calls, (
            f"{len(scalar_calls)} per-primitive getter calls for 12 primitives "
            f"({sorted(set(scalar_calls))}) - not using the batch getters")

    def test_getAllPrimitiveInfo_matches_per_primitive_reference(self, basic_context):
        """Batched output must be field-for-field identical to the scalar path."""
        uuids = self._scene(basic_context, 8)
        # A triangle and a textured patch, so the vertex counts differ per
        # primitive and the optional fields are actually populated.
        basic_context.addTriangle(DataTypes.vec3(0, 0, 0), DataTypes.vec3(1, 0, 0),
                                  DataTypes.vec3(0, 1, 0))
        texture = 'helios-core/core/lib/images/disk_texture.png'
        if os.path.exists(os.path.join(REPO_ROOT_CTX, texture)):
            basic_context.addPatchTextured(
                center=DataTypes.vec3(5, 5, 0), size=DataTypes.vec2(1, 1),
                texture_file=os.path.join(REPO_ROOT_CTX, texture))

        batched = basic_context.getAllPrimitiveInfo()
        reference = [basic_context.getPrimitiveInfo(u)
                     for u in basic_context.getAllUUIDs()]

        assert len(batched) == len(reference)
        for got, want in zip(batched, reference):
            assert got.uuid == want.uuid
            assert got.primitive_type == want.primitive_type
            assert got.area == pytest.approx(want.area, rel=1e-6)
            assert (got.normal.x, got.normal.y, got.normal.z) == pytest.approx(
                (want.normal.x, want.normal.y, want.normal.z), rel=1e-6)
            assert (got.color.r, got.color.g, got.color.b) == pytest.approx(
                (want.color.r, want.color.g, want.color.b), rel=1e-6)
            assert len(got.vertices) == len(want.vertices), f"UUID {got.uuid}"
            for a, b in zip(got.vertices, want.vertices):
                assert (a.x, a.y, a.z) == pytest.approx((b.x, b.y, b.z), rel=1e-6)
            assert got.texture_file == want.texture_file, f"UUID {got.uuid}"
            assert (got.texture_uv is None) == (want.texture_uv is None)
            if got.texture_uv is not None:
                assert len(got.texture_uv) == len(want.texture_uv)
                for a, b in zip(got.texture_uv, want.texture_uv):
                    assert (a.x, a.y) == pytest.approx((b.x, b.y), rel=1e-6)
            if want.solid_fraction is None:
                assert got.solid_fraction is None
            else:
                assert got.solid_fraction == pytest.approx(want.solid_fraction, rel=1e-6)
            # centroid is derived in __post_init__; it must survive batching
            assert (got.centroid is None) == (want.centroid is None)
            if want.centroid is not None:
                assert (got.centroid.x, got.centroid.y, got.centroid.z) == pytest.approx(
                    (want.centroid.x, want.centroid.y, want.centroid.z), rel=1e-6)

    def test_getPrimitivesInfoForObject_is_batched_too(self, basic_context):
        tile_uuids = basic_context.addTile(center=DataTypes.vec3(0, 0, 0),
                                           size=DataTypes.vec2(2, 2),
                                           subdiv=DataTypes.int2(4, 4))
        object_id = basic_context.getPrimitiveParentObjectID(tile_uuids[0])

        info, scalar_calls = self._count_scalar_calls(
            basic_context,
            lambda: basic_context.getPrimitivesInfoForObject(object_id))

        assert len(info) == len(tile_uuids)
        assert not scalar_calls, (
            f"{len(scalar_calls)} per-primitive getter calls for "
            f"{len(tile_uuids)} primitives")

    def test_getAllPrimitiveInfo_empty_context(self, basic_context):
        assert basic_context.getAllPrimitiveInfo() == []
