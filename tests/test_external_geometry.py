"""
Tests for PyHelios External Geometry Import functionality.

These tests verify the external geometry import methods including:
1. PLY file loading
2. OBJ file loading  
3. XML file loading
4. NumPy array-based triangle import
"""

import contextlib
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock, patch
import os
import tempfile

from pyhelios import Context, DataTypes
from pyhelios.Context import PrimitiveInfo
from pyhelios.wrappers.DataTypes import PrimitiveType
from tests.conftest import assert_vec3_equal, assert_color_equal


class TestFileLoading:
    """Test file loading functionality (PLY, OBJ, XML)."""
    
    @patch.dict(os.environ, {'PYHELIOS_DEV_MODE': '1'})
    def test_load_ply_simple_mock(self):
        """Test simple PLY loading with mock."""
        # Create a temporary PLY file for testing
        with tempfile.NamedTemporaryFile(suffix='.ply', delete=False) as tmp:
            tmp.write(b"ply\nformat ascii 1.0\nend_header\n")
            tmp_path = tmp.name
        
        try:
            context = Context()
            # In dev mode, PLY loading should either work or raise RuntimeError
            try:
                result = context.loadPLY(tmp_path)
                # If it works, result should be a list (possibly empty for invalid PLY)
                assert isinstance(result, list)
            except RuntimeError as e:
                # If it fails, should contain "not available" message
                assert "not available" in str(e).lower()
        finally:
            os.unlink(tmp_path)
    
    @patch.dict(os.environ, {'PYHELIOS_DEV_MODE': '1'})
    def test_load_ply_with_transformations_mock(self):
        """Test PLY loading with transformations using mock."""
        # Create a temporary PLY file for testing
        with tempfile.NamedTemporaryFile(suffix='.ply', delete=False) as tmp:
            tmp.write(b"ply\nformat ascii 1.0\nend_header\n")
            tmp_path = tmp.name
        
        try:
            context = Context()
            origin = DataTypes.vec3(1.0, 2.0, 3.0)
            rotation = DataTypes.SphericalCoord(1.0, 0.0, 1.57)
            color = DataTypes.RGBcolor(1.0, 0.0, 0.0)
            
            # In dev mode, PLY loading should either work or raise RuntimeError
            try:
                result = context.loadPLY(
                    filename=tmp_path, 
                    origin=origin, 
                    height=2.0,
                    rotation=rotation,
                    color=color,
                    upaxis="YUP",
                    silent=True
                )
                # If it works, result should be a list
                assert isinstance(result, list)
            except RuntimeError as e:
                # If it fails, should contain "not available" message
                assert "not available" in str(e).lower()
        finally:
            os.unlink(tmp_path)
    
    @patch.dict(os.environ, {'PYHELIOS_DEV_MODE': '1'})
    def test_load_obj_simple_mock(self):
        """Test simple OBJ loading with mock."""
        # Create a temporary OBJ file for testing
        with tempfile.NamedTemporaryFile(suffix='.obj', delete=False) as tmp:
            tmp.write(b"# Simple OBJ file\nv 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
            tmp_path = tmp.name
        
        try:
            context = Context()
            # In dev mode, OBJ loading should either work or raise RuntimeError
            try:
                result = context.loadOBJ(tmp_path)
                # If it works, result should be a list
                assert isinstance(result, list)
            except RuntimeError as e:
                # If it fails, should contain "not available" message
                assert "not available" in str(e).lower()
        finally:
            os.unlink(tmp_path)
    
    @patch.dict(os.environ, {'PYHELIOS_DEV_MODE': '1'})
    def test_load_obj_with_transformations_mock(self):
        """Test OBJ loading with transformations using mock."""
        # Create a temporary OBJ file for testing
        with tempfile.NamedTemporaryFile(suffix='.obj', delete=False) as tmp:
            tmp.write(b"# Simple OBJ file\nv 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
            tmp_path = tmp.name
        
        try:
            context = Context()
            origin = DataTypes.vec3(0.0, 0.0, 1.0)
            scale = DataTypes.vec3(2.0, 2.0, 2.0)
            rotation = DataTypes.SphericalCoord(1.0, 0.0, 0.5)
            color = DataTypes.RGBcolor(0.0, 1.0, 0.0)
            
            # In dev mode, OBJ loading should either work or raise RuntimeError
            try:
                result = context.loadOBJ(
                    filename=tmp_path,
                    origin=origin,
                    scale=scale, 
                    rotation=rotation,
                    color=color,
                    upaxis="ZUP"
                )
                # If it works, result should be a list
                assert isinstance(result, list)
            except RuntimeError as e:
                # If it fails, should contain "not available" message
                assert "not available" in str(e).lower()
        finally:
            os.unlink(tmp_path)
    
    @patch.dict(os.environ, {'PYHELIOS_DEV_MODE': '1'})
    def test_load_xml_mock(self):
        """Test XML loading with mock."""
        # Create a temporary XML file for testing
        with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as tmp:
            tmp.write(b"<?xml version='1.0'?><helios></helios>")
            tmp_path = tmp.name
        
        try:
            context = Context()
            # In dev mode, XML loading should either work or raise RuntimeError
            try:
                result = context.loadXML(tmp_path)
                # If it works, result should be a list
                assert isinstance(result, list)
            except RuntimeError as e:
                # If it fails, should contain "not available" message
                assert "not available" in str(e).lower()
        finally:
            os.unlink(tmp_path)
    
    @patch.dict(os.environ, {'PYHELIOS_DEV_MODE': '1'})
    def test_load_ply_invalid_parameter_combinations(self):
        """Test PLY loading with invalid parameter combinations."""
        # Create a temporary PLY file for testing
        with tempfile.NamedTemporaryFile(suffix='.ply', delete=False) as tmp:
            tmp.write(b"ply\nformat ascii 1.0\nend_header\n")
            tmp_path = tmp.name
        
        try:
            context = Context()
            origin = DataTypes.vec3(1.0, 2.0, 3.0)
            
            # Parameter validation happens before mock mode check, so should get ValueError
            with pytest.raises(ValueError) as excinfo:
                context.loadPLY(tmp_path, origin=origin)
            assert "invalid parameter combination" in str(excinfo.value).lower()
        finally:
            os.unlink(tmp_path)
    
    @patch.dict(os.environ, {'PYHELIOS_DEV_MODE': '1'})
    def test_load_obj_invalid_parameter_combinations(self):
        """Test OBJ loading with invalid parameter combinations."""
        # Create a temporary OBJ file for testing
        with tempfile.NamedTemporaryFile(suffix='.obj', delete=False) as tmp:
            tmp.write(b"# Simple OBJ file\nv 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
            tmp_path = tmp.name
        
        try:
            context = Context()
            origin = DataTypes.vec3(1.0, 2.0, 3.0)
            
            # Parameter validation happens before mock mode check, so should get ValueError
            with pytest.raises(ValueError) as excinfo:
                context.loadOBJ(tmp_path, origin=origin)
            assert "invalid parameter combination" in str(excinfo.value).lower()
        finally:
            os.unlink(tmp_path)


@pytest.mark.cross_platform
class TestArrayBasedImport:
    """Test NumPy array-based triangle import."""
    
    def test_add_triangles_from_arrays_basic(self):
        """Test basic triangle import from arrays."""
        with patch('pyhelios.wrappers.UContextWrapper.addTriangle') as mock_add:
            mock_add.side_effect = [100, 101, 102]  # Return different UUIDs for each triangle
            
            context = Context()
            
            # Create simple test data
            vertices = np.array([
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0], 
                [0.0, 1.0, 0.0],
                [1.0, 1.0, 0.0]
            ], dtype=np.float32)
            
            faces = np.array([
                [0, 1, 2],
                [1, 3, 2],
                [0, 2, 3]
            ], dtype=np.int32)
            
            uuids = context.addTrianglesFromArrays(vertices, faces)
            
            assert len(uuids) == 3
            assert uuids == [100, 101, 102]
            assert mock_add.call_count == 3
    
    def test_add_triangles_from_arrays_with_colors(self):
        """Test triangle import with per-vertex colors."""
        with patch('pyhelios.wrappers.UContextWrapper.addTriangleWithColor') as mock_add:
            mock_add.side_effect = [200, 201]
            
            context = Context()
            
            vertices = np.array([
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [1.0, 1.0, 0.0]
            ], dtype=np.float32)
            
            faces = np.array([
                [0, 1, 2],
                [1, 3, 2]
            ], dtype=np.int32)
            
            # Per-vertex colors
            colors = np.array([
                [1.0, 0.0, 0.0],  # red
                [0.0, 1.0, 0.0],  # green
                [0.0, 0.0, 1.0],  # blue
                [1.0, 1.0, 0.0]   # yellow
            ], dtype=np.float32)
            
            uuids = context.addTrianglesFromArrays(vertices, faces, colors)
            
            assert len(uuids) == 2
            assert uuids == [200, 201]
            assert mock_add.call_count == 2
    
    def test_add_triangles_from_arrays_per_triangle_colors(self):
        """Test triangle import with per-triangle colors."""
        with patch('pyhelios.wrappers.UContextWrapper.addTriangleWithColor') as mock_add:
            mock_add.side_effect = [300, 301]
            
            context = Context()
            
            vertices = np.array([
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [1.0, 1.0, 0.0]
            ], dtype=np.float32)
            
            faces = np.array([
                [0, 1, 2],
                [1, 3, 2]
            ], dtype=np.int32)
            
            # Per-triangle colors (2 triangles, 2 colors)
            colors = np.array([
                [1.0, 0.0, 0.0],  # red triangle
                [0.0, 1.0, 0.0]   # green triangle
            ], dtype=np.float32)
            
            uuids = context.addTrianglesFromArrays(vertices, faces, colors)
            
            assert len(uuids) == 2
            assert mock_add.call_count == 2
    
    def test_add_triangles_textured(self):
        """Test textured triangle import."""
        with patch('pyhelios.wrappers.UContextWrapper.addTriangleWithTexture') as mock_add:
            mock_add.side_effect = [400, 401]
            
            context = Context()
            
            vertices = np.array([
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [1.0, 1.0, 0.0],
                [0.0, 1.0, 0.0]
            ], dtype=np.float32)
            
            faces = np.array([
                [0, 1, 2],
                [0, 2, 3]
            ], dtype=np.int32)
            
            uv_coords = np.array([
                [0.0, 0.0],
                [1.0, 0.0],
                [1.0, 1.0],
                [0.0, 1.0]
            ], dtype=np.float32)
            
            from tests.conftest import get_example_file_path
            texture_path = get_example_file_path("Helios_logo.jpeg")
            uuids = context.addTrianglesFromArraysTextured(
                vertices, faces, uv_coords, texture_path
            )
            
            assert len(uuids) == 2
    
    def test_add_triangles_validation_errors(self):
        """Test array validation errors."""
        context = Context()
        
        # Invalid vertices shape
        with pytest.raises(ValueError, match="Vertices array must have shape"):
            vertices = np.array([[0, 0]])  # Wrong shape
            faces = np.array([[0, 1, 2]])
            context.addTrianglesFromArrays(vertices, faces)
        
        # Invalid faces shape
        with pytest.raises(ValueError, match="Faces array must have shape"):
            vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
            faces = np.array([[0, 1]])  # Wrong shape
            context.addTrianglesFromArrays(vertices, faces)
        
        # Invalid face indices
        with pytest.raises(ValueError, match="Face indices reference vertex"):
            vertices = np.array([[0, 0, 0], [1, 0, 0]])  # Only 2 vertices
            faces = np.array([[0, 1, 2]])  # References vertex 2 which doesn't exist
            context.addTrianglesFromArrays(vertices, faces)
        
        # Invalid colors shape
        with pytest.raises(ValueError, match="Colors array must have shape"):
            vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
            faces = np.array([[0, 1, 2]]) 
            colors = np.array([[1, 0]])  # Wrong color shape
            context.addTrianglesFromArrays(vertices, faces, colors)
    
    def test_add_triangles_textured_validation_errors(self):
        """Test textured triangle validation errors."""
        context = Context()
        
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        faces = np.array([[0, 1, 2]])
        
        # Invalid UV coordinates shape
        with pytest.raises(ValueError, match="UV coordinates array must have shape"):
            uv_coords = np.array([[0, 0, 0]])  # Wrong shape (should be 2D)
            context.addTrianglesFromArraysTextured(vertices, faces, uv_coords, "texture.png")
        
        # Mismatched UV coordinates count
        with pytest.raises(ValueError, match="UV coordinates count"):
            uv_coords = np.array([[0, 0]])  # Only 1 UV coord for 3 vertices
            context.addTrianglesFromArraysTextured(vertices, faces, uv_coords, "texture.png")


@pytest.mark.cross_platform
class TestPrimitiveInfo:
    """Test primitive information retrieval."""
    
    def test_get_primitive_info_mock(self):
        """Test getting primitive information with mocked data."""
        with patch.object(Context, 'getPrimitiveType', return_value=DataTypes.PrimitiveType.Triangle), \
             patch.object(Context, 'getPrimitiveArea', return_value=0.5), \
             patch.object(Context, 'getPrimitiveNormal', return_value=DataTypes.vec3(0, 0, 1)), \
             patch.object(Context, 'getPrimitiveVertices', return_value=[
                DataTypes.vec3(0, 0, 0),
                DataTypes.vec3(1, 0, 0), 
                DataTypes.vec3(0, 1, 0)
             ]), \
             patch.object(Context, 'getPrimitiveColor', return_value=DataTypes.RGBcolor(1, 0, 0)), \
             patch.object(Context, 'getPrimitiveTextureFile', return_value=""), \
             patch.object(Context, 'getPrimitiveTextureUV', return_value=[]), \
             patch.object(Context, 'getPrimitiveSolidFraction', return_value=1.0):
            # The texture getters are mocked alongside the others because the UUID
            # under test does not exist natively; getPrimitiveInfo propagates native
            # errors from these rather than silently reporting the fields as None.

            context = Context()
            
            info = context.getPrimitiveInfo(123)
            
            assert info.uuid == 123
            assert info.primitive_type == PrimitiveType.Triangle
            assert info.area == 0.5
            assert_vec3_equal(info.normal, DataTypes.vec3(0, 0, 1))
            assert len(info.vertices) == 3
            assert_vec3_equal(info.vertices[0], DataTypes.vec3(0, 0, 0))
            assert_color_equal(info.color, DataTypes.RGBcolor(1, 0, 0))
            
            # Check centroid calculation
            expected_centroid = DataTypes.vec3(1/3, 1/3, 0)
            assert_vec3_equal(info.centroid, expected_centroid)
    
    @staticmethod
    def _batched_getters(uuids):
        """Patch the list-accepting getters that _batchPrimitiveInfo() uses.

        Each primitive is a triangle, given a distinct area/color so that a
        mis-assembled result (fields paired with the wrong primitive) fails rather
        than passing on identical values.
        """
        n = len(uuids)
        vertices = np.array([[0, 0, 0, 1, 0, 0, 0, 1, 0]] * n, dtype=np.float32).ravel()
        offsets = np.arange(n + 1, dtype=np.uint32) * 9
        return [
            patch.object(Context, 'getPrimitiveType',
                         return_value=np.full(n, int(PrimitiveType.Triangle), dtype=np.uint32)),
            patch.object(Context, 'getPrimitiveArea',
                         return_value=np.array([0.5 * (i + 1) for i in range(n)], dtype=np.float32)),
            patch.object(Context, 'getPrimitiveNormal',
                         return_value=np.array([[0, 0, 1]] * n, dtype=np.float32)),
            patch.object(Context, 'getPrimitiveVertices', return_value=(vertices, offsets)),
            patch.object(Context, 'getPrimitiveColor',
                         return_value=np.array([[1, 0, 0]] * n, dtype=np.float32)),
            patch.object(Context, 'getPrimitiveTextureFile', return_value=[""] * n),
            patch.object(Context, 'getPrimitiveTextureUV',
                         return_value=(np.empty((0,), dtype=np.float32),
                                       np.zeros((n + 1,), dtype=np.uint32))),
            patch.object(Context, 'getPrimitiveSolidFraction',
                         return_value=np.ones(n, dtype=np.float32)),
        ]

    def _assert_assembled(self, infos, uuids):
        assert [i.uuid for i in infos] == uuids, "UUID order not preserved"
        for position, info in enumerate(infos):
            assert info.primitive_type == PrimitiveType.Triangle
            # Area is distinct per primitive, so this catches field/primitive mismatch
            assert info.area == pytest.approx(0.5 * (position + 1))
            assert len(info.vertices) == 3
            assert_vec3_equal(info.vertices[0], DataTypes.vec3(0, 0, 0))
            assert_vec3_equal(info.normal, DataTypes.vec3(0, 0, 1))
            assert_color_equal(info.color, DataTypes.RGBcolor(1, 0, 0))
            assert info.texture_file is None
            assert info.texture_uv is None
            assert info.solid_fraction == pytest.approx(1.0)
            # Derived in __post_init__ from the vertices
            assert_vec3_equal(info.centroid, DataTypes.vec3(1 / 3, 1 / 3, 0))

    def test_get_all_primitive_info_mock(self):
        """getAllPrimitiveInfo covers every UUID, in order, via the batched getters.

        It deliberately does NOT call getPrimitiveInfo() per primitive: that would
        be eight native round-trips each. The assertions are on the assembled
        result rather than on which internal getter was called.
        """
        uuids = [1, 2, 3]
        patches = [patch.object(Context, 'getAllUUIDs', return_value=uuids)]
        patches += self._batched_getters(uuids)

        with contextlib.ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            context = Context()
            all_info = context.getAllPrimitiveInfo()

        assert len(all_info) == 3
        self._assert_assembled(all_info, uuids)

    def test_get_primitives_info_for_object_mock(self):
        """The object variant is batched the same way, over the object's UUIDs."""
        uuids = [10, 20]
        patches = [patch('pyhelios.wrappers.UContextWrapper.getObjectPrimitiveUUIDs',
                         return_value=uuids)]
        patches += self._batched_getters(uuids)

        with contextlib.ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            context = Context()
            object_info = context.getPrimitivesInfoForObject(42)

        assert len(object_info) == 2
        self._assert_assembled(object_info, uuids)


@pytest.mark.unit
class TestPrimitiveDataAPI:
    """Test primitive data API functionality."""
    
    def test_primitive_data_methods_functionality(self):
        """Test that primitive data methods work correctly."""
        context = Context()
        
        # Create a valid primitive
        center = DataTypes.vec3(0, 0, 0)
        size = DataTypes.vec2(1, 1)
        color = DataTypes.RGBcolor(1, 0, 0)
        patch_uuid = context.addPatch(center=center, size=size, color=color)
        
        # Test setting and getting data
        context.setPrimitiveDataInt(patch_uuid, "test_key", 42)
        
        # Test data exists
        assert context.doesPrimitiveDataExist(patch_uuid, "test_key") == True
        assert context.doesPrimitiveDataExist(patch_uuid, "nonexistent_key") == False
        
        # Test getting data
        result = context.getPrimitiveData(patch_uuid, "test_key")
        assert result == 42
        
        # Test getting nonexistent data raises error
        with pytest.raises(Exception):  # Accept any exception type from PyHelios
            context.getPrimitiveData(patch_uuid, "nonexistent_key")


@pytest.mark.integration 
@pytest.mark.native_only
class TestExternalGeometryIntegration:
    """Integration tests requiring native Helios library."""
    
    def test_array_import_integration(self, basic_context):
        """Test array import with real context."""
        # Create simple triangle
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0]
        ], dtype=np.float32)
        
        faces = np.array([[0, 1, 2]], dtype=np.int32)
        
        try:
            uuids = basic_context.addTrianglesFromArrays(vertices, faces)
            
            # Verify triangle was added
            assert len(uuids) == 1
            assert uuids[0] >= 0  # Valid UUID (starts from 0)
            
            # Check primitive count increased
            assert basic_context.getPrimitiveCount() >= 1
            
            # Get info about the triangle
            info = basic_context.getPrimitiveInfo(uuids[0])
            assert info.primitive_type == PrimitiveType.Triangle
            assert info.area > 0
            assert len(info.vertices) == 3
            
        except NotImplementedError as e:
            # If native library doesn't support this yet, that's expected
            if "Triangle functions not available" in str(e):
                pytest.skip("Native triangle addition not yet implemented")
            else:
                raise
    
    def test_primitive_info_integration(self, basic_context):
        """Test primitive info retrieval with real context."""
        # Add a simple patch first
        center = DataTypes.vec3(0, 0, 0)
        size = DataTypes.vec2(1, 1)
        color = DataTypes.RGBcolor(1, 0, 0)
        
        uuid = basic_context.addPatch(center=center, size=size, color=color)
        
        # Get primitive info
        info = basic_context.getPrimitiveInfo(uuid)
        
        assert info.uuid == uuid
        assert info.primitive_type == PrimitiveType.Patch
        assert info.area > 0
        assert len(info.vertices) >= 4  # Patch should have at least 4 vertices (may have padding)
        assert_color_equal(info.color, color)