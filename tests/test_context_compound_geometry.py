"""
Tests for PyHelios Context compound geometry methods.

These tests verify the compound geometry creation methods including tiles,
spheres, tubes, and boxes that return lists of primitive UUIDs.
"""

import pytest
from unittest.mock import Mock, patch
import platform
import numpy as np
from typing import List, Union

import pyhelios
from pyhelios import Context
from pyhelios.types import *  # Import all vector types for convenience
from tests.conftest import assert_vec3_equal, assert_vec2_equal, assert_color_equal
from tests.test_utils import GeometryValidator, PlatformHelper


def is_compound_geometry_available():
    """Check if compound geometry functions are available in the current build."""
    try:
        with Context() as context:
            context.addTile()
        return True
    except NotImplementedError:
        return False
    except Exception:
        # Any other exception means the functions exist but failed for other reasons
        return True


compound_geometry_available = pytest.mark.skipif(
    not is_compound_geometry_available(),
    reason="Compound geometry functions not available in current Helios library build"
)


class TestCompoundGeometryValidation:
    """Test validation helpers for compound geometry methods."""
    
    @staticmethod
    def validate_uuid_list(uuids: List[int], expected_min_count: int = 1) -> bool:
        """Validate that a UUID list meets basic requirements."""
        assert isinstance(uuids, list), f"Expected list, got {type(uuids)}"
        assert len(uuids) >= expected_min_count, f"Expected at least {expected_min_count} UUIDs, got {len(uuids)}"
        assert all(isinstance(uuid, int) for uuid in uuids), "All UUIDs must be integers"
        assert all(uuid >= 0 for uuid in uuids), "All UUIDs must be non-negative"
        assert len(set(uuids)) == len(uuids), "All UUIDs must be unique"
        return True
    
    @staticmethod
    def validate_primitive_list(context, uuids: List[int], expected_primitive_type=None):
        """Validate that all UUIDs correspond to valid primitives of expected type."""
        for uuid in uuids:
            # Check UUID exists in context
            assert uuid in context.getAllUUIDs(), f"UUID {uuid} not found in context"
            
            # Check primitive type if specified
            if expected_primitive_type is not None:
                actual_type = context.getPrimitiveType(uuid)
                assert actual_type == expected_primitive_type, \
                    f"Expected {expected_primitive_type}, got {actual_type} for UUID {uuid}"
        return True
    
    @staticmethod
    def calculate_expected_tile_count(subdiv: int2) -> int:
        """Calculate expected number of patches in a tile."""
        return subdiv.x * subdiv.y
    
    @staticmethod
    def calculate_expected_sphere_triangles(ndivs: int) -> int:
        """Calculate expected number of triangles in a sphere."""
        # Sphere tessellation formula: approximately 2 * ndivs^2 triangles
        # This is an approximation - exact formula depends on tessellation algorithm
        return 2 * ndivs * ndivs
    
    @staticmethod
    def calculate_expected_tube_triangles(nodes_count: int, ndivs: int) -> int:
        """Calculate expected number of triangles in a tube."""
        # Tube has ndivs triangles per segment, 2 triangles per radial division
        segments = nodes_count - 1
        return segments * ndivs * 2
    
    @staticmethod
    def calculate_expected_box_patches(subdiv: int3) -> int:
        """Calculate expected number of patches on a box."""
        # Box has 6 faces, each subdivided according to subdiv
        return 2 * (subdiv.x * subdiv.y + subdiv.x * subdiv.z + subdiv.y * subdiv.z)


@pytest.mark.native_only
@compound_geometry_available
class TestTileCreation:
    """Test Context.addTile() method."""
    
    def test_addTile_basic(self, basic_context):
        """Test basic tile creation with default parameters."""
        tile_uuids = basic_context.addTile()
        
        TestCompoundGeometryValidation.validate_uuid_list(tile_uuids, 1)
        TestCompoundGeometryValidation.validate_primitive_list(
            basic_context, tile_uuids, PrimitiveType.Patch
        )
        
        # Default subdiv is (1, 1), so should create 1 patch
        expected_count = TestCompoundGeometryValidation.calculate_expected_tile_count(int2(1, 1))
        assert len(tile_uuids) == expected_count
        
        # Verify context state
        assert basic_context.getPrimitiveCount() == len(tile_uuids)
    
    def test_addTile_with_parameters(self, basic_context):
        """Test tile creation with specified parameters."""
        center = vec3(2, 3, 4)
        size = vec2(3, 2)
        rotation = SphericalCoord(0.5, 0.3, 0)
        subdiv = int2(2, 3)
        color = RGBcolor(0.8, 0.2, 0.1)
        
        tile_uuids = basic_context.addTile(
            center=center, size=size, rotation=rotation, 
            subdiv=subdiv, color=color
        )
        
        TestCompoundGeometryValidation.validate_uuid_list(tile_uuids)
        
        # Should create subdiv.x * subdiv.y patches
        expected_count = TestCompoundGeometryValidation.calculate_expected_tile_count(subdiv)
        assert len(tile_uuids) == expected_count
        
        # Verify all patches have the specified color
        for uuid in tile_uuids:
            actual_color = basic_context.getPrimitiveColor(uuid)
            assert_color_equal(actual_color, color)
    
    def test_addTile_subdivisions(self, basic_context):
        """Test tile creation with various subdivision levels."""
        test_cases = [
            (int2(1, 1), 1),
            (int2(2, 2), 4),
            (int2(3, 4), 12),
            (int2(5, 1), 5),
        ]
        
        for subdiv, expected_count in test_cases:
            # Use the context directly, not as a context manager in a loop
            tile_uuids = basic_context.addTile(subdiv=subdiv)
            
            assert len(tile_uuids) == expected_count, \
                f"Subdivision {subdiv} should create {expected_count} patches, got {len(tile_uuids)}"
            TestCompoundGeometryValidation.validate_uuid_list(tile_uuids, expected_count)
    
    def test_addTile_multiple_tiles(self, basic_context):
        """Test creating multiple tiles in the same context."""
        # Create first tile
        tile1_uuids = basic_context.addTile(
            center=vec3(-2, 0, 0), subdiv=int2(2, 2), color=RGBcolor(1, 0, 0)
        )
        
        # Create second tile
        tile2_uuids = basic_context.addTile(
            center=vec3(2, 0, 0), subdiv=int2(3, 1), color=RGBcolor(0, 1, 0)
        )
        
        # Verify both tiles
        assert len(tile1_uuids) == 4
        assert len(tile2_uuids) == 3
        
        # No overlap in UUIDs
        assert set(tile1_uuids).isdisjoint(set(tile2_uuids))
        
        # Total primitive count should be sum
        assert basic_context.getPrimitiveCount() == len(tile1_uuids) + len(tile2_uuids)
        
        # Verify colors are maintained
        for uuid in tile1_uuids:
            color = basic_context.getPrimitiveColor(uuid)
            assert_color_equal(color, RGBcolor(1, 0, 0))
        
        for uuid in tile2_uuids:
            color = basic_context.getPrimitiveColor(uuid)
            assert_color_equal(color, RGBcolor(0, 1, 0))
    
    def test_addTile_parameter_validation(self, basic_context):
        """Test parameter validation for addTile."""
        # Test invalid subdivision values
        with pytest.raises(ValueError):
            basic_context.addTile(subdiv=int2(0, 1))  # Zero subdivision
        
        with pytest.raises(ValueError):
            basic_context.addTile(subdiv=int2(1, -1))  # Negative subdivision
        
        # Test invalid size values
        with pytest.raises(ValueError):
            basic_context.addTile(size=vec2(0, 1))  # Zero size
        
        with pytest.raises(ValueError):
            basic_context.addTile(size=vec2(1, -1))  # Negative size


@pytest.mark.native_only
@compound_geometry_available
class TestSphereCreation:
    """Test Context.addSphere() method."""
    
    def test_addSphere_basic(self, basic_context):
        """Test basic sphere creation with default parameters."""
        sphere_uuids = basic_context.addSphere()
        
        TestCompoundGeometryValidation.validate_uuid_list(sphere_uuids, 1)
        TestCompoundGeometryValidation.validate_primitive_list(
            basic_context, sphere_uuids, PrimitiveType.Triangle
        )
        
        # Sphere should create multiple triangles
        assert len(sphere_uuids) > 10  # At least some reasonable number of triangles
        
        # Verify context state
        assert basic_context.getPrimitiveCount() == len(sphere_uuids)
    
    def test_addSphere_with_parameters(self, basic_context):
        """Test sphere creation with specified parameters."""
        center = vec3(1, 2, 3)
        radius = 2.5
        ndivs = 15
        color = RGBcolor(0.1, 0.9, 0.3)
        
        sphere_uuids = basic_context.addSphere(
            center=center, radius=radius, ndivs=ndivs, color=color
        )
        
        TestCompoundGeometryValidation.validate_uuid_list(sphere_uuids)
        
        # Verify all triangles have the specified color
        for uuid in sphere_uuids:
            actual_color = basic_context.getPrimitiveColor(uuid)
            assert_color_equal(actual_color, color)
        
        # Verify sphere is roughly the right size by checking vertex distances
        sample_uuid = sphere_uuids[0]
        vertices = basic_context.getPrimitiveVertices(sample_uuid)
        
        # All vertices should be approximately radius distance from center
        for vertex in vertices:
            distance = ((vertex.x - center.x)**2 + 
                       (vertex.y - center.y)**2 + 
                       (vertex.z - center.z)**2)**0.5
            assert distance == pytest.approx(radius, rel=0.1)
    
    def test_addSphere_divisions_scaling(self, basic_context):
        """Test that higher divisions create more triangles."""
        sphere_low = basic_context.addSphere(ndivs=5)
        basic_context.__exit__(None, None, None)  # Reset context
        
        with Context() as new_context:
            sphere_high = new_context.addSphere(ndivs=15)
            
            # Higher divisions should create more triangles
            assert len(sphere_high) > len(sphere_low)
    
    def test_addSphere_parameter_validation(self, basic_context):
        """Test parameter validation for addSphere."""
        # Test invalid radius
        with pytest.raises(ValueError, match="must be positive"):
            basic_context.addSphere(radius=0)
        
        with pytest.raises(ValueError, match="must be positive"):
            basic_context.addSphere(radius=-1.5)
        
        # Test invalid divisions
        with pytest.raises(ValueError, match="must be >= 3"):
            basic_context.addSphere(ndivs=2)
        
        with pytest.raises(ValueError, match="must be >= 3"):
            basic_context.addSphere(ndivs=0)


@pytest.mark.native_only
@compound_geometry_available
class TestTubeCreation:
    """Test Context.addTube() method."""
    
    def test_addTube_basic(self, basic_context):
        """Test basic tube creation with minimal parameters."""
        nodes = [vec3(0, 0, 0), vec3(1, 0, 0)]
        radius = 0.5
        
        tube_uuids = basic_context.addTube(nodes, radius)
        
        TestCompoundGeometryValidation.validate_uuid_list(tube_uuids, 1)
        TestCompoundGeometryValidation.validate_primitive_list(
            basic_context, tube_uuids, PrimitiveType.Triangle
        )
        
        # Tube should create multiple triangles
        assert len(tube_uuids) > 6  # At least some reasonable number for a simple tube
        
        # Verify context state
        assert basic_context.getPrimitiveCount() == len(tube_uuids)
    
    def test_addTube_single_radius(self, basic_context):
        """Test tube creation with single radius for all nodes."""
        nodes = [
            vec3(0, 0, 0),
            vec3(1, 0, 0), 
            vec3(2, 1, 0),
            vec3(3, 1, 1)
        ]
        radius = 0.3
        ndivs = 8
        color = RGBcolor(0.7, 0.2, 0.9)
        
        tube_uuids = basic_context.addTube(nodes, radius, ndivs, color)
        
        TestCompoundGeometryValidation.validate_uuid_list(tube_uuids)
        
        # Verify all triangles have the specified color
        for uuid in tube_uuids:
            actual_color = basic_context.getPrimitiveColor(uuid)
            assert_color_equal(actual_color, color)
    
    def test_addTube_variable_radii(self, basic_context):
        """Test tube creation with different radius at each node."""
        nodes = [
            vec3(0, 0, 0),
            vec3(1, 0, 0),
            vec3(2, 1, 0)
        ]
        radii = [0.1, 0.5, 0.2]  # Variable radii
        
        tube_uuids = basic_context.addTube(nodes, radii)
        
        TestCompoundGeometryValidation.validate_uuid_list(tube_uuids)
        
        # More complex validation could check that the tube actually varies in radius
        # For now, just verify it completes successfully
        assert len(tube_uuids) > 10
    
    def test_addTube_variable_colors(self, basic_context):
        """Test tube creation with different colors at each node."""
        nodes = [
            vec3(0, 0, 0),
            vec3(1, 0, 0),
            vec3(1, 1, 0)
        ]
        radii = 0.2
        colors = [
            RGBcolor(1, 0, 0),  # Red
            RGBcolor(0, 1, 0),  # Green  
            RGBcolor(0, 0, 1)   # Blue
        ]
        
        tube_uuids = basic_context.addTube(nodes, radii, colors=colors)
        
        TestCompoundGeometryValidation.validate_uuid_list(tube_uuids)
        
        # Colors should be interpolated along the tube
        # Exact color verification depends on interpolation implementation
        for uuid in tube_uuids:
            color = basic_context.getPrimitiveColor(uuid)
            assert isinstance(color, RGBcolor)
    
    def test_addTube_single_color_for_all(self, basic_context):
        """Test tube creation with single color applied to all nodes."""
        nodes = [vec3(0, 0, 0), vec3(1, 1, 1), vec3(0, 2, 0)]
        radii = [0.1, 0.2, 0.1]
        color = RGBcolor(0.5, 0.5, 0.5)  # Single color
        
        tube_uuids = basic_context.addTube(nodes, radii, colors=color)
        
        TestCompoundGeometryValidation.validate_uuid_list(tube_uuids)
        
        # All triangles should have the same color (or close to it due to interpolation)
        sample_color = basic_context.getPrimitiveColor(tube_uuids[0])
        assert_color_equal(sample_color, color, tolerance=0.1)
    
    def test_addTube_parameter_validation(self, basic_context):
        """Test parameter validation for addTube."""
        # Test insufficient nodes
        with pytest.raises(ValueError, match="at least 2 nodes"):
            basic_context.addTube([vec3(0, 0, 0)], 0.5)
        
        with pytest.raises(ValueError, match="at least 2 nodes"):
            basic_context.addTube([], 0.5)
        
        # Test invalid divisions
        with pytest.raises(ValueError, match="radial divisions must be at least 3"):
            basic_context.addTube([vec3(0, 0, 0), vec3(1, 0, 0)], 0.5, ndivs=2)
        
        # Test mismatched radii count
        nodes = [vec3(0, 0, 0), vec3(1, 0, 0), vec3(2, 0, 0)]
        radii = [0.1, 0.2]  # Too few radii
        with pytest.raises(ValueError, match="must have same length as nodes"):
            basic_context.addTube(nodes, radii)
        
        # Test mismatched colors count
        colors = [RGBcolor(1, 0, 0), RGBcolor(0, 1, 0)]  # Too few colors
        with pytest.raises(ValueError, match="Number of colors.*must match number of nodes"):
            basic_context.addTube(nodes, 0.5, colors=colors)
        
        # Test invalid radii (negative/zero)
        with pytest.raises(ValueError, match="must be positive"):
            basic_context.addTube([vec3(0, 0, 0), vec3(1, 0, 0)], [0.5, 0])
        
        with pytest.raises(ValueError, match="must be positive"):
            basic_context.addTube([vec3(0, 0, 0), vec3(1, 0, 0)], [-0.1, 0.5])


@pytest.mark.native_only
@compound_geometry_available
class TestBoxCreation:
    """Test Context.addBox() method."""
    
    def test_addBox_basic(self, basic_context):
        """Test basic box creation with default parameters."""
        box_uuids = basic_context.addBox()
        
        TestCompoundGeometryValidation.validate_uuid_list(box_uuids, 6)  # At least 6 faces
        TestCompoundGeometryValidation.validate_primitive_list(
            basic_context, box_uuids, PrimitiveType.Patch
        )
        
        # Default subdiv is (1, 1, 1), so should create 6 patches (one per face)
        expected_count = TestCompoundGeometryValidation.calculate_expected_box_patches(int3(1, 1, 1))
        assert len(box_uuids) == expected_count
        
        # Verify context state
        assert basic_context.getPrimitiveCount() == len(box_uuids)
    
    def test_addBox_with_parameters(self, basic_context):
        """Test box creation with specified parameters."""
        center = vec3(1, 2, 3)
        size = vec3(2, 1, 3)
        subdiv = int3(2, 1, 2)
        color = RGBcolor(0.3, 0.7, 0.1)
        
        box_uuids = basic_context.addBox(
            center=center, size=size, subdiv=subdiv, color=color
        )
        
        TestCompoundGeometryValidation.validate_uuid_list(box_uuids)
        
        # Calculate expected number of patches
        expected_count = TestCompoundGeometryValidation.calculate_expected_box_patches(subdiv)
        assert len(box_uuids) == expected_count
        
        # Verify all patches have the specified color
        for uuid in box_uuids:
            actual_color = basic_context.getPrimitiveColor(uuid)
            assert_color_equal(actual_color, color)
    
    def test_addBox_subdivisions(self, basic_context):
        """Test box creation with various subdivision levels."""
        test_cases = [
            (int3(1, 1, 1), 6),   # Basic cube: 6 faces
            (int3(2, 2, 2), 24),  # 2*2 patches per face * 6 faces = 24
            (int3(1, 2, 3), 22),  # Mixed subdivisions
        ]
        
        for subdiv, expected_count in test_cases:
            with Context() as ctx:  # Fresh context for each test
                box_uuids = ctx.addBox(subdiv=subdiv)
                
                calculated_count = TestCompoundGeometryValidation.calculate_expected_box_patches(subdiv)
                assert calculated_count == expected_count, \
                    f"Test case calculation error for {subdiv}"
                
                assert len(box_uuids) == expected_count, \
                    f"Subdivision {subdiv} should create {expected_count} patches, got {len(box_uuids)}"
    
    def test_addBox_parameter_validation(self, basic_context):
        """Test parameter validation for addBox."""
        # Test invalid size values
        with pytest.raises(ValueError, match="must be positive"):
            basic_context.addBox(size=vec3(0, 1, 1))
        
        with pytest.raises(ValueError, match="must be positive"):
            basic_context.addBox(size=vec3(1, -1, 1))
        
        # Test invalid subdivision values
        with pytest.raises(ValueError, match="All subdivision counts must be at least 1"):
            basic_context.addBox(subdiv=int3(0, 1, 1))
        
        with pytest.raises(ValueError, match="All subdivision counts must be at least 1"):
            basic_context.addBox(subdiv=int3(1, 1, -1))


@pytest.mark.cross_platform  
class TestCompoundGeometryMockMode:
    """Test compound geometry methods in mock mode."""
    
    def test_addTile_mock_mode(self):
        """Test addTile behavior in mock mode or when functions not available."""
        if PlatformHelper.is_native_library_available():
            # If native libraries are available but compound geometry is not
            if not is_compound_geometry_available():
                context = Context()
                # Should raise NotImplementedError indicating functions not available
                with pytest.raises(NotImplementedError) as exc_info:
                    context.addTile()
                
                error_msg = str(exc_info.value)
                assert "Compound geometry functions not available" in error_msg
            else:
                pytest.skip("Compound geometry functions are available - cannot test unavailable scenario")
        else:
            context = Context()
            # Should raise RuntimeError indicating mock mode
            with pytest.raises(RuntimeError) as exc_info:
                context.addTile()
            
            # Error message should indicate mock mode
            error_msg = str(exc_info.value).lower()
            assert any(keyword in error_msg for keyword in 
                      ["mock", "native", "library", "unavailable", "development"])
    
    def test_addSphere_mock_mode(self):
        """Test addSphere behavior in mock mode or when functions not available."""
        if PlatformHelper.is_native_library_available():
            # If native libraries are available but compound geometry is not
            if not is_compound_geometry_available():
                context = Context()
                # Should raise NotImplementedError indicating functions not available
                with pytest.raises(NotImplementedError) as exc_info:
                    context.addSphere()
                
                error_msg = str(exc_info.value)
                assert "Compound geometry functions not available" in error_msg
            else:
                pytest.skip("Compound geometry functions are available - cannot test unavailable scenario")
        else:
            context = Context()
            # Should raise RuntimeError indicating mock mode
            with pytest.raises(RuntimeError) as exc_info:
                context.addSphere()
            
            # Error message should indicate mock mode
            error_msg = str(exc_info.value).lower()
            assert any(keyword in error_msg for keyword in 
                      ["mock", "native", "library", "unavailable", "development"])
    
    def test_addTube_mock_mode(self):
        """Test addTube behavior in mock mode or when functions not available."""
        if PlatformHelper.is_native_library_available():
            # If native libraries are available but compound geometry is not
            if not is_compound_geometry_available():
                context = Context()
                # Should raise NotImplementedError indicating functions not available
                with pytest.raises(NotImplementedError) as exc_info:
                    context.addTube([vec3(0, 0, 0), vec3(1, 0, 0)], 0.5)
                
                error_msg = str(exc_info.value)
                assert "Compound geometry functions not available" in error_msg
            else:
                pytest.skip("Compound geometry functions are available - cannot test unavailable scenario")
        else:
            context = Context()
            # Should raise RuntimeError indicating mock mode
            with pytest.raises(RuntimeError) as exc_info:
                context.addTube([vec3(0, 0, 0), vec3(1, 0, 0)], 0.5)
            
            # Error message should indicate mock mode
            error_msg = str(exc_info.value).lower()
            assert any(keyword in error_msg for keyword in 
                      ["mock", "native", "library", "unavailable", "development"])
    
    def test_addBox_mock_mode(self):
        """Test addBox behavior in mock mode or when functions not available."""
        if PlatformHelper.is_native_library_available():
            # If native libraries are available but compound geometry is not
            if not is_compound_geometry_available():
                context = Context()
                # Should raise NotImplementedError indicating functions not available
                with pytest.raises(NotImplementedError) as exc_info:
                    context.addBox()
                
                error_msg = str(exc_info.value)
                assert "Compound geometry functions not available" in error_msg
            else:
                pytest.skip("Compound geometry functions are available - cannot test unavailable scenario")
        else:
            context = Context()
            # Should raise RuntimeError indicating mock mode
            with pytest.raises(RuntimeError) as exc_info:
                context.addBox()
            
            # Error message should indicate mock mode
            error_msg = str(exc_info.value).lower()
            assert any(keyword in error_msg for keyword in 
                      ["mock", "native", "library", "unavailable", "development"])


@pytest.mark.native_only
@compound_geometry_available
class TestCompoundGeometryIntegration:
    """Test integration of compound geometry methods with existing Context functionality."""
    
    def test_mixed_geometry_creation(self, basic_context):
        """Test creating various compound geometries in the same context."""
        # Create a tile
        tile_uuids = basic_context.addTile(
            center=vec3(-2, 0, 0), subdiv=int2(2, 2), color=RGBcolor(1, 0, 0)
        )
        
        # Create a sphere
        sphere_uuids = basic_context.addSphere(
            center=vec3(0, 0, 0), radius=0.5, ndivs=8, color=RGBcolor(0, 1, 0)
        )
        
        # Create a tube
        tube_nodes = [vec3(2, 0, 0), vec3(2, 1, 0), vec3(2, 1, 1)]
        tube_uuids = basic_context.addTube(
            tube_nodes, 0.1, colors=RGBcolor(0, 0, 1)
        )
        
        # Create a box
        box_uuids = basic_context.addBox(
            center=vec3(0, 2, 0), size=vec3(1, 1, 1), color=RGBcolor(1, 1, 0)
        )
        
        # Verify all geometries are distinct
        all_uuids = tile_uuids + sphere_uuids + tube_uuids + box_uuids
        assert len(set(all_uuids)) == len(all_uuids), "All UUIDs should be unique"
        
        # Verify total count
        expected_total = len(tile_uuids) + len(sphere_uuids) + len(tube_uuids) + len(box_uuids)
        assert basic_context.getPrimitiveCount() == expected_total
        
        # Verify all UUIDs are in context
        context_uuids = basic_context.getAllUUIDs()
        for uuid in all_uuids:
            assert uuid in context_uuids
    
    def test_primitive_data_on_compound_geometry(self, basic_context):
        """Test setting primitive data on compound geometry primitives."""
        # Create a tile
        tile_uuids = basic_context.addTile(subdiv=int2(2, 2))
        
        # Set primitive data on all tile patches
        for i, uuid in enumerate(tile_uuids):
            basic_context.setPrimitiveDataInt(uuid, "tile_index", i)
            basic_context.setPrimitiveDataString(uuid, "geometry_type", "tile_patch")
        
        # Verify data was set correctly
        for i, uuid in enumerate(tile_uuids):
            assert basic_context.getPrimitiveData(uuid, "tile_index", int) == i
            assert basic_context.getPrimitiveData(uuid, "geometry_type", str) == "tile_patch"
        
        # Test bulk data retrieval
        indices_array = basic_context.getPrimitiveDataArray(tile_uuids, "tile_index")
        assert len(indices_array) == len(tile_uuids)
        assert list(indices_array) == list(range(len(tile_uuids)))
    
    def test_compound_geometry_with_existing_primitives(self, basic_context):
        """Test compound geometry creation alongside regular primitives."""
        # Add some regular primitives first
        patch_uuid = basic_context.addPatch(center=vec3(5, 5, 5), color=RGBcolor(0.5, 0.5, 0.5))
        triangle_uuid = basic_context.addTriangle(
            vec3(6, 0, 0), vec3(7, 0, 0), vec3(6.5, 1, 0), RGBcolor(0.8, 0.8, 0.8)
        )
        
        initial_count = basic_context.getPrimitiveCount()
        initial_uuids = set(basic_context.getAllUUIDs())
        
        # Add compound geometry
        sphere_uuids = basic_context.addSphere(center=vec3(10, 10, 10), ndivs=6)
        
        # Verify compound geometry doesn't interfere with existing primitives
        final_count = basic_context.getPrimitiveCount()
        final_uuids = set(basic_context.getAllUUIDs())
        
        assert final_count == initial_count + len(sphere_uuids)
        assert initial_uuids.issubset(final_uuids)
        
        # Verify original primitives still exist and have correct properties
        assert basic_context.getPrimitiveType(patch_uuid) == PrimitiveType.Patch
        assert basic_context.getPrimitiveType(triangle_uuid) == PrimitiveType.Triangle


@pytest.mark.native_only
@pytest.mark.slow
@compound_geometry_available
class TestCompoundGeometryPerformance:
    """Test performance characteristics of compound geometry methods."""
    
    def test_large_tile_creation(self, basic_context):
        """Test performance with large tile subdivisions."""
        # Create a large tile
        large_subdiv = int2(20, 20)  # 400 patches
        
        tile_uuids = basic_context.addTile(subdiv=large_subdiv)
        
        expected_count = TestCompoundGeometryValidation.calculate_expected_tile_count(large_subdiv)
        assert len(tile_uuids) == expected_count
        
        # Verify all patches exist and are valid
        TestCompoundGeometryValidation.validate_primitive_list(
            basic_context, tile_uuids, PrimitiveType.Patch
        )
    
    def test_high_resolution_sphere(self, basic_context):
        """Test performance with high-resolution sphere."""
        # Create a high-resolution sphere
        high_ndivs = 25  # Creates many triangles
        
        sphere_uuids = basic_context.addSphere(ndivs=high_ndivs)
        
        # Should create a substantial number of triangles
        assert len(sphere_uuids) > 100
        
        TestCompoundGeometryValidation.validate_primitive_list(
            basic_context, sphere_uuids, PrimitiveType.Triangle
        )
    
    def test_complex_tube_creation(self, basic_context):
        """Test performance with complex tube geometry."""
        # Create a complex tube with many nodes
        nodes = []
        for i in range(20):  # 20 nodes = 19 segments
            angle = i * 0.3
            x = np.cos(angle) * 2
            y = np.sin(angle) * 2  
            z = i * 0.1
            nodes.append(vec3(x, y, z))
        
        # Variable radii
        radii = [0.1 + 0.05 * np.sin(i * 0.5) for i in range(len(nodes))]
        
        tube_uuids = basic_context.addTube(nodes, radii, ndivs=8)
        
        # Should create substantial geometry
        assert len(tube_uuids) > 50
        
        TestCompoundGeometryValidation.validate_primitive_list(
            basic_context, tube_uuids, PrimitiveType.Triangle
        )
    
    def test_highly_subdivided_box(self, basic_context):
        """Test performance with highly subdivided box."""
        # Create a highly subdivided box
        high_subdiv = int3(10, 8, 6)
        
        box_uuids = basic_context.addBox(subdiv=high_subdiv)
        
        expected_count = TestCompoundGeometryValidation.calculate_expected_box_patches(high_subdiv)
        assert len(box_uuids) == expected_count
        
        TestCompoundGeometryValidation.validate_primitive_list(
            basic_context, box_uuids, PrimitiveType.Patch
        )


@pytest.mark.cross_platform
class TestCompoundGeometryEdgeCases:
    """Test edge cases and error conditions for compound geometry methods."""
    
    @compound_geometry_available
    def test_extreme_parameter_values(self, basic_context):
        """Test compound geometry methods with extreme but valid parameter values."""
        if not PlatformHelper.is_native_library_available():
            pytest.skip("Requires native library for extreme parameter testing")
        
        # Very large coordinates
        large_center = vec3(1e6, 1e6, 1e6)
        
        # Should not crash with large coordinates
        tile_uuids = basic_context.addTile(center=large_center)
        assert len(tile_uuids) > 0
        
        basic_context.__exit__(None, None, None)
        
        # Very small but positive values
        with Context() as small_context:
            small_radius = 1e-6
            sphere_uuids = small_context.addSphere(radius=small_radius)
            assert len(sphere_uuids) > 0
    
    @compound_geometry_available
    def test_boundary_subdivision_values(self, basic_context):
        """Test compound geometry with boundary subdivision values."""
        # Minimum valid subdivisions
        min_tile = basic_context.addTile(subdiv=int2(1, 1))
        assert len(min_tile) == 1
        
        basic_context.__exit__(None, None, None)
        
        with Context() as new_context:
            min_box = new_context.addBox(subdiv=int3(1, 1, 1))
            assert len(min_box) == 6
    
    @compound_geometry_available
    def test_minimal_geometry_requirements(self, basic_context):
        """Test compound geometry with minimal valid parameters."""
        # Minimal sphere
        min_sphere = basic_context.addSphere(ndivs=3)  # Minimum allowed divisions
        assert len(min_sphere) > 0
        
        basic_context.__exit__(None, None, None)
        
        # Minimal tube
        with Context() as new_context:
            minimal_nodes = [vec3(0, 0, 0), vec3(1, 0, 0)]  # Minimum 2 nodes
            min_tube = new_context.addTube(minimal_nodes, 0.1, ndivs=3)  # Minimum divisions
            assert len(min_tube) > 0


@pytest.mark.cross_platform
class TestCompoundGeometryReturnValues:
    """Test return value formats and types for compound geometry methods."""
    
    @compound_geometry_available
    def test_return_value_types(self):
        """Test that all compound geometry methods return List[int]."""
        if not PlatformHelper.is_native_library_available():
            pytest.skip("Requires native library for return value testing")
        
        with Context() as context:
            # Test addTile return type
            tile_result = context.addTile()
            assert isinstance(tile_result, list)
            assert all(isinstance(uuid, int) for uuid in tile_result)
            
            # Test addSphere return type  
            sphere_result = context.addSphere()
            assert isinstance(sphere_result, list)
            assert all(isinstance(uuid, int) for uuid in sphere_result)
            
            # Test addTube return type
            nodes = [vec3(0, 0, 0), vec3(1, 0, 0)]
            tube_result = context.addTube(nodes, 0.5)
            assert isinstance(tube_result, list)
            assert all(isinstance(uuid, int) for uuid in tube_result)
            
            # Test addBox return type
            box_result = context.addBox()
            assert isinstance(box_result, list)
            assert all(isinstance(uuid, int) for uuid in box_result)
    
    @compound_geometry_available
    def test_uuid_uniqueness_across_methods(self):
        """Test that UUIDs are unique across different compound geometry methods."""
        if not PlatformHelper.is_native_library_available():
            pytest.skip("Requires native library for UUID uniqueness testing")
        
        with Context() as context:
            # Create geometry with different methods
            tile_uuids = context.addTile(subdiv=int2(2, 2))
            sphere_uuids = context.addSphere(ndivs=8)
            tube_uuids = context.addTube([vec3(0, 0, 0), vec3(1, 0, 0)], 0.1)
            box_uuids = context.addBox(subdiv=int3(2, 1, 1))
            
            # Collect all UUIDs
            all_compound_uuids = tile_uuids + sphere_uuids + tube_uuids + box_uuids
            
            # Verify all UUIDs are unique
            assert len(set(all_compound_uuids)) == len(all_compound_uuids)
            
            # Verify they match context's UUID list
            context_uuids = context.getAllUUIDs()
            assert set(all_compound_uuids) == set(context_uuids)
    
    @compound_geometry_available
    def test_empty_geometry_handling(self):
        """Test handling of cases that might produce empty geometry.""" 
        if not PlatformHelper.is_native_library_available():
            pytest.skip("Requires native library for empty geometry testing")
        
        with Context() as context:
            # All valid compound geometry methods should produce at least some primitives
            # This test ensures no method returns an empty list for valid parameters
            
            tile_uuids = context.addTile(subdiv=int2(1, 1))
            assert len(tile_uuids) > 0
            
            sphere_uuids = context.addSphere(ndivs=3)  # Minimum divisions
            assert len(sphere_uuids) > 0
            
            tube_uuids = context.addTube([vec3(0, 0, 0), vec3(0.1, 0, 0)], 0.01, ndivs=3)
            assert len(tube_uuids) > 0
            
            box_uuids = context.addBox(subdiv=int3(1, 1, 1))
            assert len(box_uuids) > 0

@pytest.mark.cross_platform
class TestPolymeshTopologyAPI:
    """Signature-level checks for the helios-core 1.3.83 mesh topology API."""

    @pytest.mark.parametrize("name", [
        "setPolymeshObjectTopology",
        "getPolymeshObjectVertices", "getPolymeshObjectFaces",
        "getPolymeshObjectVertexNormals", "getPolymeshObjectVertexUV",
        "doesPolymeshObjectHaveVertexNormals", "getPolymeshObjectVertexNormalSource",
        "getPolymeshObjectVertexCount", "getPolymeshObjectFaceCount",
        "getPolymeshObjectFaceIndexForPrimitive", "getPolymeshObjectPrimitiveUUIDForFace",
        "computePolymeshObjectVertexNormals", "isPolymeshObjectClosed",
        "getPolymeshObjectBoundaryEdges", "getPolymeshObjectConnectedComponents",
        "getPolymeshObjectSurfaceArea",
        "doesObjectHaveAnalyticVertexNormals", "getObjectPrimitiveVertexNormals",
    ])
    def test_topology_methods_exist(self, name):
        assert hasattr(Context, name), f"Context.{name}() is missing"

    def test_topology_wrappers_check_the_flag_that_registers_them(self):
        """
        Each wrapper must guard on the availability flag of the try block that actually
        registered its ctypes prototype.

        The 1.3.83 polymesh prototypes are registered under
        `_CONTEXT_SCALAR_API_AVAILABLE`. Guarding them with `_require_ctx_ext()` instead
        checks an unrelated flag, so against a library missing these symbols the guard
        passes and the call proceeds with no argtypes/restype -- silent stack corruption
        rather than a clean NotImplementedError.
        """
        import inspect
        from pyhelios.wrappers import UContextWrapper as w

        names = [
            "setPolymeshObjectTopologyWrapper", "getPolymeshObjectVerticesWrapper",
            "getPolymeshObjectFacesWrapper", "getPolymeshObjectVertexNormalsWrapper",
            "getPolymeshObjectVertexUVWrapper",
            "doesPolymeshObjectHaveVertexNormalsWrapper",
            "getPolymeshObjectVertexNormalSourceWrapper",
            "getPolymeshObjectVertexCountWrapper", "getPolymeshObjectFaceCountWrapper",
            "getPolymeshObjectFaceIndexForPrimitiveWrapper",
            "getPolymeshObjectPrimitiveUUIDForFaceWrapper",
            "computePolymeshObjectVertexNormalsWrapper", "isPolymeshObjectClosedWrapper",
            "getPolymeshObjectBoundaryEdgesWrapper",
            "getPolymeshObjectConnectedComponentsWrapper",
            "getPolymeshObjectSurfaceAreaWrapper",
            "doesObjectHaveAnalyticVertexNormalsWrapper",
            "getObjectPrimitiveVertexNormalsWrapper",
            "getObjectPrimitiveVertexNormalsBatchWrapper",
        ]
        wrong = []
        for name in names:
            src = inspect.getsource(getattr(w, name))
            if "_require_ctx_scalar_api()" not in src:
                wrong.append(name)
        assert not wrong, f"wrong availability guard on: {wrong}"

    def test_vertex_normal_source_is_publicly_exported(self):
        """The enum is part of the public API, like PrimitiveType."""
        from pyhelios import VertexNormalSource as top_level
        from pyhelios.types import VertexNormalSource as types_level
        from pyhelios.wrappers.DataTypes import VertexNormalSource as wrapper_level
        assert top_level is types_level is wrapper_level

    def test_vertex_normal_source_enum_matches_native(self):
        """Values must match helios::VertexNormalSource, which is cast across the C ABI."""
        from pyhelios.wrappers.DataTypes import VertexNormalSource
        assert int(VertexNormalSource.NONE) == 0
        assert int(VertexNormalSource.AUTHORED) == 1
        assert int(VertexNormalSource.COMPUTED) == 2


@pytest.mark.native_only
class TestPolymeshTopologyNative:
    """helios-core 1.3.83 polymesh mesh topology behavior."""

    @staticmethod
    def _tetrahedron(context):
        """Build a closed unit tetrahedron and attach its topology.

        Returns (objID, vertices, faces, uuids). Volume is exactly 1/6.
        """
        verts = [vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0), vec3(0, 0, 1)]
        faces = [(0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3)]
        uuids = [context.addTriangle(verts[a], verts[b], verts[c]) for a, b, c in faces]
        objID = context.addPolymeshObject(uuids)
        context.setPolymeshObjectTopology(objID, verts, [int3(*f) for f in faces], uuids)
        return objID, verts, faces, uuids

    def test_polymesh_without_topology_reports_no_faces(self):
        """A mesh built with addPolymeshObject alone is a triangle soup until topology is attached."""
        with Context() as context:
            uuids = [context.addTriangle(vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0))]
            objID = context.addPolymeshObject(uuids)
            assert context.getPolymeshObjectFaceCount(objID) == 0
            assert context.getPolymeshObjectVertexCount(objID) == 0

    def test_set_topology_populates_vertex_and_face_counts(self):
        with Context() as context:
            objID, verts, faces, _ = self._tetrahedron(context)
            assert context.getPolymeshObjectVertexCount(objID) == len(verts)
            assert context.getPolymeshObjectFaceCount(objID) == len(faces)
            assert len(context.getPolymeshObjectVertices(objID)) == len(verts)
            assert len(context.getPolymeshObjectFaces(objID)) == len(faces)

    def test_closed_mesh_has_no_boundary_edges(self):
        with Context() as context:
            objID, _, _, _ = self._tetrahedron(context)
            assert context.isPolymeshObjectClosed(objID) is True
            assert context.getPolymeshObjectBoundaryEdges(objID) == []

    def test_open_mesh_reports_boundary_edges(self):
        """A single triangle is an open surface: all three of its edges are boundaries."""
        with Context() as context:
            verts = [vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0)]
            uuid = context.addTriangle(*verts)
            objID = context.addPolymeshObject([uuid])
            context.setPolymeshObjectTopology(objID, verts, [int3(0, 1, 2)], [uuid])

            assert context.isPolymeshObjectClosed(objID) is False
            assert len(context.getPolymeshObjectBoundaryEdges(objID)) == 3

    def test_volume_of_closed_mesh_is_correct(self):
        """The tetrahedron on (0,0,0),(1,0,0),(0,1,0),(0,0,1) encloses exactly 1/6."""
        with Context() as context:
            objID, _, _, _ = self._tetrahedron(context)
            assert context.getPolymeshObjectVolume(objID) == pytest.approx(1.0 / 6.0, rel=1e-5)

    def test_volume_of_open_mesh_raises(self):
        """1.3.83 rejects an open surface rather than returning a meaningless number."""
        with Context() as context:
            verts = [vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0)]
            uuid = context.addTriangle(*verts)
            objID = context.addPolymeshObject([uuid])
            context.setPolymeshObjectTopology(objID, verts, [int3(0, 1, 2)], [uuid])

            from pyhelios.exceptions import HeliosRuntimeError
            with pytest.raises(HeliosRuntimeError, match="not a closed surface"):
                context.getPolymeshObjectVolume(objID)

    def test_surface_area_sums_face_areas(self):
        """Three unit right triangles of area 1/2 plus one equilateral face of area sqrt(3)/2."""
        import math
        with Context() as context:
            objID, _, _, _ = self._tetrahedron(context)
            expected = 3 * 0.5 + math.sqrt(3.0) / 2.0
            assert context.getPolymeshObjectSurfaceArea(objID) == pytest.approx(expected, rel=1e-5)

    def test_connected_components_of_single_mesh(self):
        with Context() as context:
            objID, _, faces, _ = self._tetrahedron(context)
            components = context.getPolymeshObjectConnectedComponents(objID)
            assert len(components) == 1
            assert sorted(components[0]) == list(range(len(faces)))

    def test_face_and_primitive_lookups_are_inverse(self):
        with Context() as context:
            objID, _, _, uuids = self._tetrahedron(context)
            for uuid in uuids:
                face_index = context.getPolymeshObjectFaceIndexForPrimitive(objID, uuid)
                assert context.getPolymeshObjectPrimitiveUUIDForFace(objID, face_index) == uuid

    def test_compute_vertex_normals_marks_them_computed(self):
        """Helios never synthesizes normals implicitly; they appear only after an explicit call."""
        from pyhelios.wrappers.DataTypes import VertexNormalSource
        with Context() as context:
            objID, _, _, _ = self._tetrahedron(context)
            assert context.doesPolymeshObjectHaveVertexNormals(objID) is False
            assert context.getPolymeshObjectVertexNormalSource(objID) == VertexNormalSource.NONE

            context.computePolymeshObjectVertexNormals(objID, crease_angle_degrees=30.0)

            assert context.doesPolymeshObjectHaveVertexNormals(objID) is True
            assert context.getPolymeshObjectVertexNormalSource(objID) == VertexNormalSource.COMPUTED
            assert len(context.getPolymeshObjectVertexNormals(objID)) > 0

    def test_computed_vertex_normals_are_unit_length(self):
        import math
        with Context() as context:
            objID, _, _, _ = self._tetrahedron(context)
            context.computePolymeshObjectVertexNormals(objID, crease_angle_degrees=30.0)
            for n in context.getPolymeshObjectVertexNormals(objID):
                assert math.sqrt(n.x ** 2 + n.y ** 2 + n.z ** 2) == pytest.approx(1.0, abs=1e-4)

    def test_set_topology_rejects_mismatched_face_uuids(self):
        with Context() as context:
            verts = [vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0)]
            uuid = context.addTriangle(*verts)
            objID = context.addPolymeshObject([uuid])
            with pytest.raises(ValueError, match="parallel to faces"):
                context.setPolymeshObjectTopology(
                    objID, verts, [int3(0, 1, 2)], [uuid, uuid]
                )

    def test_set_topology_rejects_wrong_vertex_type(self):
        """Passed positionally, a wrong type must raise rather than be silently accepted."""
        with Context() as context:
            verts = [vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0)]
            uuid = context.addTriangle(*verts)
            objID = context.addPolymeshObject([uuid])
            with pytest.raises(ValueError, match="must be a vec3"):
                context.setPolymeshObjectTopology(
                    objID, [RGBcolor(0, 0, 0)] * 3, [int3(0, 1, 2)], [uuid]
                )
            with pytest.raises(ValueError, match="must be an int3"):
                context.setPolymeshObjectTopology(
                    objID, verts, [vec3(0, 1, 2)], [uuid]
                )

    def test_topology_round_trips_vertex_uv(self):
        with Context() as context:
            verts = [vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0)]
            uv = [vec2(0, 0), vec2(1, 0), vec2(0, 1)]
            uuid = context.addTriangle(*verts)
            objID = context.addPolymeshObject([uuid])
            context.setPolymeshObjectTopology(objID, verts, [int3(0, 1, 2)], [uuid],
                                              vertex_uv=uv)
            got = context.getPolymeshObjectVertexUV(objID)
            assert len(got) == 3
            assert [(p.x, p.y) for p in got] == pytest.approx([(0, 0), (1, 0), (0, 1)])

    def test_authored_normals_keep_their_provenance(self):
        """Normals supplied by the caller are reported as authored, not computed."""
        from pyhelios.wrappers.DataTypes import VertexNormalSource
        with Context() as context:
            verts = [vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0)]
            normals = [vec3(0, 0, 1)] * 3
            uuid = context.addTriangle(*verts)
            objID = context.addPolymeshObject([uuid])
            context.setPolymeshObjectTopology(
                objID, verts, [int3(0, 1, 2)], [uuid],
                vertex_normals=normals,
                normal_source=VertexNormalSource.AUTHORED,
            )
            assert context.doesPolymeshObjectHaveVertexNormals(objID) is True
            assert context.getPolymeshObjectVertexNormalSource(objID) == VertexNormalSource.AUTHORED


@pytest.mark.native_only
class TestV1383BehaviorChanges:
    """Behavioral changes in helios-core 1.3.83 to already-wrapped Context methods."""

    def test_cone_node_radii_follow_object_transform(self):
        """1.3.83 applies the object transform, so a scaled cone reports scaled radii."""
        with Context() as context:
            cone = context.addConeObject(vec3(0, 0, 0), vec3(0, 0, 1), 0.5, 0.25, ndivs=8)
            assert context.getConeObjectNodeRadii(cone) == pytest.approx([0.5, 0.25])

            context.scaleObject(cone, vec3(2, 2, 2))

            assert context.getConeObjectNodeRadii(cone) == pytest.approx([1.0, 0.5])
            assert context.getConeObjectNodeRadius(cone, 0) == pytest.approx(1.0)

    def test_copied_primitive_has_no_parent_object(self):
        """A copy is standalone; it previously claimed a membership the object did not list."""
        with Context() as context:
            uuid = context.addTriangle(vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0))
            objID = context.addPolymeshObject([uuid])
            assert context.getPrimitiveParentObjectID(uuid) == objID

            copy = context.copyPrimitive(uuid)
            assert context.getPrimitiveParentObjectID(copy) == 0

    def test_polymesh_member_primitives_are_deformable(self):
        """Members of a polymesh can be transformed individually; other object types cannot."""
        with Context() as context:
            uuid = context.addTriangle(vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0))
            objID = context.addPolymeshObject([uuid])
            before = context.getPrimitiveVertices(uuid)

            context.translatePrimitive(uuid, vec3(0, 0, 1))

            after = context.getPrimitiveVertices(uuid)
            for b, a in zip(before, after):
                assert a.z == pytest.approx(b.z + 1.0)


@pytest.mark.native_only
class TestAnalyticVertexNormalsNative:
    """helios-core 1.3.83 analytic vertex normals on curved compound objects."""

    def test_curved_objects_report_analytic_normals(self):
        with Context() as context:
            sphere = context.addSphereObject(center=vec3(0, 0, 0), radius=1.0, ndivs=8)
            tube = context.addTubeObject(8, [vec3(0, 0, 0), vec3(0, 0, 1)], [0.1, 0.1])
            assert context.doesObjectHaveAnalyticVertexNormals(sphere) is True
            assert context.doesObjectHaveAnalyticVertexNormals(tube) is True

    def test_flat_faced_objects_report_no_analytic_normals(self):
        """A tile is genuinely flat, so it has no curved shape to evaluate normals from."""
        with Context() as context:
            tile = context.addTileObject(center=vec3(0, 0, 0), size=vec2(1, 1),
                                         rotation=SphericalCoord(1, 0, 0),
                                         subdiv=int2(2, 2))
            assert context.doesObjectHaveAnalyticVertexNormals(tile) is False
            uuid = context.getObjectPrimitiveUUIDs(tile)[0]
            assert context.getObjectPrimitiveVertexNormals(tile, uuid) == []

    def test_sphere_analytic_normals_are_unit_length(self):
        import math
        with Context() as context:
            sphere = context.addSphereObject(center=vec3(0, 0, 0), radius=1.0, ndivs=8)
            uuid = context.getObjectPrimitiveUUIDs(sphere)[0]
            normals = context.getObjectPrimitiveVertexNormals(sphere, uuid)
            assert len(normals) > 0
            for n in normals:
                assert math.sqrt(n.x ** 2 + n.y ** 2 + n.z ** 2) == pytest.approx(1.0, abs=1e-4)

    def test_unit_sphere_normal_points_along_vertex_direction(self):
        """On a unit sphere centered at the origin, the surface normal is the position."""
        import math
        with Context() as context:
            sphere = context.addSphereObject(center=vec3(0, 0, 0), radius=1.0, ndivs=16)
            uuid = context.getObjectPrimitiveUUIDs(sphere)[0]
            normals = context.getObjectPrimitiveVertexNormals(sphere, uuid)
            vertices = context.getPrimitiveVertices(uuid)
            for v, n in zip(vertices, normals):
                length = math.sqrt(v.x ** 2 + v.y ** 2 + v.z ** 2)
                assert n.x == pytest.approx(v.x / length, abs=1e-3)
                assert n.y == pytest.approx(v.y / length, abs=1e-3)
                assert n.z == pytest.approx(v.z / length, abs=1e-3)

    def test_batch_matches_single_primitive_query(self):
        with Context() as context:
            sphere = context.addSphereObject(center=vec3(0, 0, 0), radius=1.0, ndivs=8)
            uuids = context.getObjectPrimitiveUUIDs(sphere)[:4]
            batch = context.getObjectPrimitiveVertexNormals(sphere, uuids)
            assert len(batch) == len(uuids)
            for uuid, group in zip(uuids, batch):
                single = context.getObjectPrimitiveVertexNormals(sphere, uuid)
                assert len(group) == len(single)
                for a, b in zip(group, single):
                    assert (a.x, a.y, a.z) == pytest.approx((b.x, b.y, b.z))
